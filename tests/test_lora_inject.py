"""LoRA injection pins (LORA-01 / LORA-05): allowlist, ordering, tied tensor, param census.

Pins the post-load injection machinery on a tiny CPU fixture:

  1. Wrap count — ``inject_lora`` wraps exactly ``6 * n_layer`` projections and nothing else.
  2. Allowlist cross-pin — ``TARGET_PROJECTIONS`` equals the seam test's ``PROJECTIONS``
     tuple (``tests/test_gpt_lora_seam.py:16``); production code never imports from tests/.
  3. Tied-tensor safety (LORA-05) — post-injection ``lm_head.weight`` still IS ``wte.weight``
     (``data_ptr`` identity) and neither head nor embedding is a ``LoRALinear`` (PITFALLS P1).
  4. Load->inject ordering — injection after weights exist leaves logits BIT-identical
     (B=0 + loaded base => identity).
  5. Param-count closed form (LORA-05) — trainable census == r * n_layer * 18 * n_embd
     after ``mark_only_lora_trainable``; only ``lora_`` params are trainable.
  6. ``lora_state_dict`` filter — exactly 2 * 6 * n_layer tensors, no base weights leak.
  7. Key-audited apply — ``load_adapter_weights`` reproduces logits across identically
     injected models; a corrupted dict raises ``ValueError`` BEFORE any weight loads (P4).
  8. ``snapshot_params`` — detached clones immune to later in-place mutation (the canary).

CPU-only, GPU-free.
"""

import pytest
import torch
import torch.nn as nn

from personacore.config import ModelConfig
from personacore.lora import (
    TARGET_PROJECTIONS,
    LoRAConfig,
    LoRALinear,
    inject_lora,
    load_adapter_weights,
    lora_state_dict,
    mark_only_lora_trainable,
    snapshot_params,
)
from personacore.model import GPT

# Canonical allowlist restated from tests/test_gpt_lora_seam.py::PROJECTIONS (line 16) — the
# cross-pin target. Tests may restate the literal; production code never imports from tests/.
PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")


def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184); everything else is shrunk
    # for a cheap CPU fixture (tests/test_slim_checkpoint.py precedent).
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


def _build_injected(r: int = 4):
    """Seeded tiny GPT with LoRA injected — the load->inject->freeze substrate."""
    torch.manual_seed(1234)
    cfg = _tiny_config()
    model = GPT(cfg)
    lora_cfg = LoRAConfig(r=r)
    n = inject_lora(model, lora_cfg)
    return model, cfg, lora_cfg, n


def _nudge_lora_b(model, seed: int) -> None:
    """Make the adapter delta nonzero/distinctive so applies are observable."""
    torch.manual_seed(seed)
    with torch.no_grad():
        for name, p in model.named_parameters():
            if "lora_B" in name:
                nn.init.normal_(p)


def test_wrap_count_and_targets():
    model, cfg, _, n = _build_injected()
    assert n == 6 * cfg.n_layer
    for block in model.blocks:
        for name in ("q_proj", "k_proj", "v_proj", "c_proj"):
            assert isinstance(getattr(block.attn, name), LoRALinear)
        for name in ("fc_in", "fc_out"):
            assert isinstance(getattr(block.mlp, name), LoRALinear)


def test_allowlist_cross_pin():
    # TARGET_PROJECTIONS must equal the structural seam gate's tuple — one canonical allowlist.
    assert TARGET_PROJECTIONS == PROJECTIONS


def test_tied_tensor_never_wrapped():
    model, _, _, _ = _build_injected()
    # data_ptr identity reused verbatim from tests/test_gpt_weight_tying.py (LORA-05).
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
    assert not isinstance(model.lm_head, LoRALinear)
    assert not isinstance(model.wte, LoRALinear)


def test_injection_preserves_logits_bit_identical():
    torch.manual_seed(1234)
    cfg = _tiny_config()
    model = GPT(cfg).eval()
    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        before, _ = model(idx)
    inject_lora(model, LoRAConfig(r=4))
    model.eval()  # fresh LoRALinear children default to train mode.
    with torch.no_grad():
        after, _ = model(idx)
    # B=0 + loaded base => bit-identity (the load->inject ordering pin).
    assert torch.equal(before, after)


def test_trainable_census_formula():
    model, cfg, lora_cfg, _ = _build_injected()
    mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # Closed form verified in 09-RESEARCH.md: r * n_layer * 18 * n_embd (LORA-05).
    assert trainable == lora_cfg.r * cfg.n_layer * 18 * cfg.n_embd
    for name, p in model.named_parameters():
        if p.requires_grad:
            assert "lora_" in name, f"non-LoRA param is trainable: {name}"
        else:
            assert "lora_" not in name, f"LoRA param is frozen: {name}"


def test_lora_state_dict_filter():
    model, cfg, _, _ = _build_injected()
    adapter = lora_state_dict(model)
    assert all("lora_" in k for k in adapter)
    assert len(adapter) == 2 * 6 * cfg.n_layer  # one A + one B per wrapped projection.
    # Base weights never leak into the persona file.
    assert not any(".base." in k for k in adapter)


def test_load_adapter_weights_applies_bit_identical():
    model_a, cfg, _, _ = _build_injected()
    model_b, _, _, _ = _build_injected()  # identically seeded -> identical base + lora_A.
    _nudge_lora_b(model_a, seed=7)
    load_adapter_weights(model_b, {"adapter": lora_state_dict(model_a)})
    model_a.eval()
    model_b.eval()
    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        logits_a, _ = model_a(idx)
        logits_b, _ = model_b(idx)
    assert torch.equal(logits_a, logits_b)


def test_load_adapter_weights_raises_before_loading():
    model_a, _, _, _ = _build_injected()
    model_b, _, _, _ = _build_injected()
    _nudge_lora_b(model_a, seed=11)  # adapter values differ from model_b's zeros.
    adapter = lora_state_dict(model_a)
    before = {k: v.clone() for k, v in lora_state_dict(model_b).items()}

    # One key removed -> ValueError (PITFALLS P4: no bare strict=False).
    missing_one = dict(adapter)
    del missing_one[sorted(missing_one)[0]]
    with pytest.raises(ValueError):
        load_adapter_weights(model_b, {"adapter": missing_one})

    # One key renamed -> ValueError.
    renamed_one = dict(adapter)
    renamed_one["blocks.0.attn.q_proj.lora_Z"] = renamed_one.pop(sorted(renamed_one)[0])
    with pytest.raises(ValueError):
        load_adapter_weights(model_b, {"adapter": renamed_one})

    # Correct key set, ONE wrong-shaped tensor -> ValueError BEFORE any tensor copies
    # (CR-02: load_state_dict(strict=False) copies shape-matching tensors first, so a bare
    # strict=False call would half-apply the crafted artifact before raising).
    k0 = sorted(adapter)[0]
    wrong_shape = dict(adapter)
    wrong_shape[k0] = torch.zeros(adapter[k0].shape[0] + 1, adapter[k0].shape[1])
    with pytest.raises(ValueError, match="shape/dtype"):
        load_adapter_weights(model_b, {"adapter": wrong_shape})

    # Correct key set + shapes, ONE wrong-dtype tensor -> same friendly refusal.
    wrong_dtype = dict(adapter)
    wrong_dtype[k0] = adapter[k0].double()
    with pytest.raises(ValueError, match="shape/dtype"):
        load_adapter_weights(model_b, {"adapter": wrong_dtype})

    # The audit fires BEFORE any weight is loaded: model_b's lora tensors are unchanged.
    after = lora_state_dict(model_b)
    for k, v in before.items():
        assert torch.equal(v, after[k]), f"failed audit mutated {k}"


def test_load_adapter_weights_refuses_wrong_rank():
    """CR-02 secondary: an r=8 artifact onto an r=4 injection has IDENTICAL key names but
    different shapes — the audit must raise the friendly ValueError (not torch's opaque
    aggregated size-mismatch RuntimeError) and leave the victim bit-unchanged."""
    model_r4, _, _, _ = _build_injected(r=4)
    model_r8, _, _, _ = _build_injected(r=8)
    _nudge_lora_b(model_r8, seed=13)
    before = {k: v.clone() for k, v in lora_state_dict(model_r4).items()}
    with pytest.raises(ValueError, match="shape/dtype"):
        load_adapter_weights(model_r4, {"adapter": lora_state_dict(model_r8)})
    after = lora_state_dict(model_r4)
    for k, v in before.items():
        assert torch.equal(v, after[k]), f"wrong-rank refusal mutated {k}"


def test_snapshot_params_detached_clones():
    model, _, _, _ = _build_injected()
    snap = snapshot_params(model)
    assert set(snap.keys()) == {n for n, _ in model.named_parameters()}
    name, param = next(iter(model.named_parameters()))
    original = param.detach().clone()
    assert snap[name].requires_grad is False  # detached clone, not a live view.
    with torch.no_grad():
        param.add_(1.0)
    assert torch.equal(snap[name], original)  # snapshot immune to the mutation.
    assert not torch.equal(snap[name], param)
