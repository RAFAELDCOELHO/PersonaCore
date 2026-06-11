"""LoRA merge pins (LORA-04 / D-07 / D-08): in-place fold, bit-exact unmerge, pure fold.

Pins the merge/unmerge utilities layered on the 09-01 wrapper:

  1. Merged forward equivalence (ROADMAP criterion 4) — after ``merge_lora`` the folded base
     path matches the live (base + adapter) path within ``atol=1e-5`` on CPU; the 09-01
     ``not self.merged`` forward gate is what prevents double-counting end-to-end.
  2. Bit-exact unmerge (D-07) — ``unmerge_lora`` restores every wrapped ``base.weight``
     EXACTLY (``torch.equal``, stored-clone copy-back — float subtraction would NOT
     round-trip) and post-unmerge logits equal the pre-merge live logits bit-for-bit.
  3. State guards — double merge and never-merged unmerge both assert.
  4. Training-mode guard (Pitfall 6) — ``merge_lora`` refuses in train mode: checkpoints must
     never be saved merged; merge is an eval-time utility.
  5. Eject interplay — eject refuses while merged; after unmerge it succeeds and logits
     return EXACTLY to the pre-injection base.
  6. ``merged_state_dict`` purity + parity (D-08) — a PURE fold: zero mutation of the live
     model, vanilla-GPT key-set parity (no ``.base.``/``lora_`` keys survive), and a fresh
     GPT loaded ``strict=True`` reproduces the live logits within 1e-5.
  7. ``_w0`` hygiene — the stored clone is a plain attribute, never a state-dict entry, and
     is deleted on unmerge.

CPU-only, GPU-free.
"""

import pytest
import torch
import torch.nn as nn

from personacore.config import ModelConfig
from personacore.lora import (
    LoRAConfig,
    LoRALinear,
    eject_adapter,
    inject_lora,
    merge_lora,
    merged_state_dict,
    unmerge_lora,
)
from personacore.model import GPT


def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184); everything else is shrunk
    # for a cheap CPU fixture (tests/test_slim_checkpoint.py precedent).
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


def _logits(model, idx):
    with torch.no_grad():
        out, _ = model(idx)
    return out


def _setup(r: int = 4):
    """Seeded tiny GPT in eval mode with a nonzero adapter and captured live logits.

    ``.eval()`` is mandatory: it satisfies the ``merge_lora`` training-mode assert AND turns
    dropout off so the two-path comparison is deterministic (test_gpt_attention_equiv.py
    precedent). ``base_logits`` is captured BEFORE injection for the eject interplay test.
    """
    torch.manual_seed(1234)
    cfg = _tiny_config()
    model = GPT(cfg).eval()
    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    base_logits = _logits(model, idx)
    inject_lora(model, LoRAConfig(r=r))
    model.eval()  # fresh LoRALinear children default to train mode.
    with torch.no_grad():
        for m in model.modules():
            if isinstance(m, LoRALinear):
                nn.init.normal_(m.lora_B, std=0.1)  # nudge nonzero so the delta fires.
    live_logits = _logits(model, idx)
    return model, cfg, idx, base_logits, live_logits


def _wrapped(model) -> list[LoRALinear]:
    return [m for m in model.modules() if isinstance(m, LoRALinear)]


def test_merged_forward_matches_live():
    """ROADMAP criterion 4: folded base path == live (base + adapter) path within 1e-5."""
    model, _, idx, _, live_logits = _setup()
    merge_lora(model)
    assert all(m.merged is True for m in _wrapped(model))
    merged_logits = _logits(model, idx)
    # Double-counting via the forward delta branch would blow this tolerance — the 09-01
    # `not self.merged` gate is what this exercises end-to-end.
    assert torch.allclose(merged_logits, live_logits, atol=1e-5)


def test_unmerge_bit_exact():
    """D-07: stored-clone copy-back restores every base.weight EXACTLY (torch.equal)."""
    model, _, idx, _, live_logits = _setup()
    pre = {
        name: m.base.weight.detach().clone()
        for name, m in model.named_modules()
        if isinstance(m, LoRALinear)
    }
    merge_lora(model)
    unmerge_lora(model)
    for name, m in model.named_modules():
        if isinstance(m, LoRALinear):
            # Bit-identity, NOT allclose: float subtraction would not round-trip.
            assert torch.equal(m.base.weight, pre[name]), f"base.weight drifted: {name}"
    assert torch.equal(_logits(model, idx), live_logits)


def test_merge_unmerge_state_guards():
    """Double merge asserts (per-module `assert not self.merged`); bare unmerge asserts."""
    model, _, _, _, _ = _setup()
    merge_lora(model)
    with pytest.raises(AssertionError):
        merge_lora(model)  # second fold would double-count the delta.

    never_merged, _, _, _, _ = _setup()
    with pytest.raises(AssertionError):
        unmerge_lora(never_merged)


def test_merge_refuses_in_training_mode():
    """Pitfall 6: a merged-state checkpoint double-counts the delta on reload."""
    model, _, _, _, _ = _setup()
    model.train()
    with pytest.raises(AssertionError):
        merge_lora(model)


def test_eject_after_unmerge_interplay():
    """Eject refuses while merged; after unmerge it succeeds and returns to base exactly."""
    model, cfg, idx, base_logits, _ = _setup()
    model.eval()
    merge_lora(model)
    with pytest.raises(AssertionError):
        eject_adapter(model)
    unmerge_lora(model)
    assert eject_adapter(model) == 6 * cfg.n_layer
    assert torch.equal(_logits(model, idx), base_logits)


def test_merged_state_dict_purity_and_parity():
    """D-08: pure fold — zero mutation, vanilla key parity, strict-loadable, 1e-5 logits."""
    model, cfg, idx, _, live_logits = _setup()
    snapshot = {k: v.detach().clone() for k, v in model.state_dict().items()}

    sd = merged_state_dict(model)

    # (a) Zero mutation: every live tensor bit-identical, every module still unmerged.
    after = model.state_dict()
    assert set(after.keys()) == set(snapshot.keys())
    for k, v in snapshot.items():
        assert torch.equal(after[k], v), f"merged_state_dict mutated {k}"
    assert all(m.merged is False for m in _wrapped(model))

    # (b) Vanilla key-set parity: no .base./lora_ keys survive the fold.
    assert set(sd.keys()) == set(GPT(cfg).state_dict().keys())

    # (c) A fresh vanilla GPT loads the fold strict=True and reproduces the live logits.
    fresh = GPT(cfg)
    fresh.load_state_dict(sd, strict=True)
    fresh.eval()
    assert torch.allclose(_logits(fresh, idx), live_logits, atol=1e-5)


def test_w0_hygiene():
    """The stored clone is a plain attr (never in state_dict) and is deleted on unmerge."""
    model, _, _, _, _ = _setup()
    merge_lora(model)
    assert not any("_w0" in k for k in model.state_dict())
    unmerge_lora(model)
    for m in _wrapped(model):
        assert not hasattr(m, "_w0")
