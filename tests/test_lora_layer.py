"""LoRA layer-level pins: the ``LoRALinear`` composition wrapper (LORA-01 / D-05).

Pins the wrapper's load-bearing correctness properties before any injection machinery exists:

  1. B=0 identity gate — wrapping a seeded ``nn.Linear`` leaves outputs BIT-identical
     (``torch.equal``) to the bare Linear at init. The single highest-value LoRA test: a
     non-zero delta at step 0 poisons every baseline downstream (PITFALLS P2).
  2. ``scale`` single source — computed exactly once in ``__init__``; forward and the
     Plan-03 merge both read the same plain-float attribute (PITFALLS P3).
  3. A-Gaussian / B-zero init with explicit shapes (LORA-01).
  4. A/B contiguity — fresh explicit-shape tensors, never ``weight.T`` views (PITFALLS P5).
  5. Dropout placement — ``nn.Dropout`` on ``x``, LoRA branch only, train-mode gated; the
     base path is untouched and a disabled branch is bit-identical to base (D-05).
  6. State-dict hygiene — ``enabled``/``merged`` are plain attrs, never serialized.
  7. The delta actually fires once ``lora_B`` is nudged nonzero.

CPU-only, GPU-free.
"""

import torch
import torch.nn as nn

from personacore.lora import TARGET_PROJECTIONS, LoRAConfig, LoRALinear


def _seeded_base(in_features: int = 16, out_features: int = 16) -> nn.Linear:
    torch.manual_seed(1234)
    return nn.Linear(in_features, out_features)


def test_b_zero_identity_gate():
    """Wrapped output is BIT-identical to the bare Linear at init (the identity gate, P2)."""
    base = _seeded_base()
    wrapped = LoRALinear(base, r=4, alpha=8.0)
    x = torch.randn(4, 16)
    with torch.no_grad():
        assert torch.equal(wrapped(x), base(x))


def test_scale_single_source():
    """scale is a plain float set once in __init__ — alpha/r at construction (P3)."""
    wrapped = LoRALinear(_seeded_base(), r=8, alpha=16.0)
    assert isinstance(wrapped.scale, float)
    assert wrapped.scale == 2.0


def test_a_gaussian_b_zero_init():
    """lora_B all zeros (identity gate); lora_A Gaussian-init, nonzero, explicit shapes."""
    wrapped = LoRALinear(_seeded_base(in_features=16, out_features=32), r=4, alpha=8.0)
    assert wrapped.lora_A.shape == (4, 16)  # (r, in_features)
    assert wrapped.lora_B.shape == (32, 4)  # (out_features, r)
    assert torch.count_nonzero(wrapped.lora_B) == 0
    assert torch.count_nonzero(wrapped.lora_A) > 0


def test_a_b_contiguous():
    """A/B are fresh contiguous tensors — never weight.T views (PITFALLS P5 / MPS)."""
    wrapped = LoRALinear(_seeded_base(), r=4, alpha=8.0)
    assert wrapped.lora_A.is_contiguous()
    assert wrapped.lora_B.is_contiguous()


def test_dropout_on_lora_branch_only():
    """Dropout hits x on the LoRA branch only, train-mode gated; base path unaffected."""
    base = _seeded_base()
    wrapped = LoRALinear(base, r=4, alpha=8.0, dropout=0.5)
    assert isinstance(wrapped.dropout, nn.Dropout)
    assert wrapped.dropout.p == 0.5
    nn.init.normal_(wrapped.lora_B)  # nudge nonzero so the delta is observable.
    x = torch.randn(8, 16)

    # Train mode: the LoRA branch is stochastic across calls on the same input.
    wrapped.train()
    with torch.no_grad():
        y1 = wrapped(x)
        y2 = wrapped(x)
    assert not torch.equal(y1, y2)

    # Eval mode: deterministic (nn.Dropout owns the train/eval gating).
    wrapped.eval()
    with torch.no_grad():
        e1 = wrapped(x)
        e2 = wrapped(x)
    assert torch.equal(e1, e2)

    # Disabled delta branch == base(x) regardless of dropout/mode (D-05: never executed).
    wrapped.train()
    wrapped.enabled = False
    with torch.no_grad():
        assert torch.equal(wrapped(x), base(x))


def test_state_dict_hygiene():
    """Keys are exactly base.weight/base.bias/lora_A/lora_B; flags never serialize."""
    wrapped = LoRALinear(_seeded_base(), r=4, alpha=8.0)
    keys = set(wrapped.state_dict().keys())
    assert keys == {"base.weight", "base.bias", "lora_A", "lora_B"}
    assert not any("enabled" in k or "merged" in k for k in keys)


def test_delta_fires_when_b_nonzero():
    """Once lora_B is nonzero and enabled, the wrapper diverges from the bare Linear."""
    base = _seeded_base()
    wrapped = LoRALinear(base, r=4, alpha=8.0)
    nn.init.normal_(wrapped.lora_B)
    assert wrapped.enabled is True
    x = torch.randn(4, 16)
    with torch.no_grad():
        assert not torch.equal(wrapped(x), base(x))


def test_lora_config_defaults():
    """LoRAConfig house defaults: r=8/alpha=16.0/dropout=0.0/targets=TARGET_PROJECTIONS."""
    cfg = LoRAConfig()
    assert cfg.r == 8
    assert cfg.alpha == 16.0
    assert cfg.dropout == 0.0
    assert cfg.targets == TARGET_PROJECTIONS
    assert TARGET_PROJECTIONS == ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")
