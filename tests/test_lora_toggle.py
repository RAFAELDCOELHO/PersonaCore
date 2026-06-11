"""LoRA toggle pins (LORA-05 / D-05 / D-06): enable/disable round-trip, scoped CM, eject.

Pins the runtime on/off semantics layered on the 09-01 wrapper:

  1. Toggle round-trip bit-identity (ROADMAP criterion 1) — ``set_adapter_enabled(model,
     False)`` returns logits EXACTLY (``torch.equal``) to the pre-injection base; re-enabling
     restores the adapter logits exactly (the D-05 flag-gated branch never executes when off).
  2. ``adapter_disabled`` scope — inside the CM the model IS the base model; on exit the
     adapter is back.
  3. Exception safety (D-06) — a raising body still re-enables every module (try/finally).
  4. Per-module state preservation — the CM restores PRIOR values, not blanket True: a module
     disabled before entry stays disabled after exit.
  5. Eject restore (D-05 "Reset = drop adapter = instant forget") — ``eject_adapter`` returns
     every wrapped projection to a plain ``nn.Linear``, vanilla state-dict key parity, and
     logits ``torch.equal`` the pre-injection base.
  6. Eject-while-merged refusal (Pitfall 6) — ejecting a merged module would hand back
     adapter-contaminated base weights; ``eject_adapter`` asserts.

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
    adapter_disabled,
    eject_adapter,
    inject_lora,
    set_adapter_enabled,
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
    """Seeded tiny GPT: base logits captured BEFORE injection, then inject + nudge lora_B.

    Returns ``(model, cfg, idx, base_logits, adapter_logits)`` where ``adapter_logits`` is
    the live (base + nonzero delta) output the toggle must round-trip back to exactly.
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
    adapter_logits = _logits(model, idx)
    return model, cfg, idx, base_logits, adapter_logits


def _wrapped(model) -> list[LoRALinear]:
    return [m for m in model.modules() if isinstance(m, LoRALinear)]


def test_toggle_round_trip_bit_identity():
    """ROADMAP criterion 1: disable == base EXACTLY; re-enable == adapter EXACTLY."""
    model, _, idx, base_logits, adapter_logits = _setup()
    assert not torch.equal(adapter_logits, base_logits)  # the delta actually fires.
    set_adapter_enabled(model, False)
    assert torch.equal(_logits(model, idx), base_logits)
    set_adapter_enabled(model, True)
    assert torch.equal(_logits(model, idx), adapter_logits)  # exact round-trip.


def test_adapter_disabled_scope():
    """Inside the CM the model is the base model; on exit the adapter is back."""
    model, _, idx, base_logits, adapter_logits = _setup()
    with adapter_disabled(model):
        assert torch.equal(_logits(model, idx), base_logits)
    assert torch.equal(_logits(model, idx), adapter_logits)


def test_adapter_disabled_exception_safe():
    """D-06: a raising body still re-enables every module (try/finally)."""
    model, _, _, _, _ = _setup()
    with pytest.raises(RuntimeError):
        with adapter_disabled(model):
            raise RuntimeError("body blew up mid-demo")
    for m in _wrapped(model):
        assert m.enabled is True


def test_adapter_disabled_preserves_prior_state():
    """The CM restores PRIOR per-module values, not blanket True."""
    model, _, _, _, _ = _setup()
    wrapped = _wrapped(model)
    pre_disabled = wrapped[0]
    pre_disabled.enabled = False  # disabled BEFORE entering the CM.
    with adapter_disabled(model):
        assert all(m.enabled is False for m in wrapped)
    assert pre_disabled.enabled is False  # prior value restored — stays disabled.
    for m in wrapped[1:]:
        assert m.enabled is True


def test_eject_restores_vanilla_model():
    """Eject returns plain nn.Linear everywhere: vanilla keys, vanilla logits."""
    model, cfg, idx, base_logits, adapter_logits = _setup()
    assert not torch.equal(adapter_logits, base_logits)  # there was something to forget.
    n = eject_adapter(model)
    assert n == 6 * cfg.n_layer
    found = 0
    for parent in model.modules():
        for name in TARGET_PROJECTIONS:
            child = getattr(parent, name, None)
            if isinstance(child, nn.Module):
                assert isinstance(child, nn.Linear)
                assert not isinstance(child, LoRALinear)
                found += 1
    assert found == 6 * cfg.n_layer
    # Vanilla key-set parity: no .base. infix or lora_ keys survive the eject.
    assert model.state_dict().keys() == GPT(cfg).state_dict().keys()
    assert torch.equal(_logits(model, idx), base_logits)  # instant forget (D-05).


def test_eject_refuses_while_merged():
    """Pitfall 6: ejecting a merged module hands back contaminated base weights."""
    model, _, _, _, _ = _setup()
    # Flag flip only — merge() itself lands in Task 2; the guard contract exists now.
    _wrapped(model)[0].merged = True
    with pytest.raises(AssertionError):
        eject_adapter(model)
