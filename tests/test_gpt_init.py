"""RED per-tensor init-std gate for the GPT-2 weight init recipe (MODEL-04).

Asserts the canonical GPT-2 init: std 0.02 on embeddings + input projections, and the
residual-scaled ``0.02 / sqrt(2 * n_layer)`` on the projections that WRITE the residual stream.
D-04a is the single most error-prone fact: that scaling applies to BOTH ``c_proj`` (attn output)
AND ``fc_out`` (MLP output). The roadmap phrases it singularly as "residual-scaled c_proj" — a
test that checks only ``c_proj`` would silently pass a model that mis-inits ``fc_out``
(RESEARCH Pitfall 3), so this gate asserts BOTH suffixes explicitly.

RED until Plan 02 implements ``personacore.model.GPT``. CPU-only, GPU-free.
"""

import math

import torch

from personacore.config import ModelConfig
from personacore.model import GPT

# Finite-tensor std is noisy -> loose relative tolerance per suffix (RESEARCH / PATTERNS).
STD_REL_TOL = 0.1


def _assert_std(name: str, std: float, target: float) -> None:
    assert abs(std - target) < target * STD_REL_TOL, f"{name}: std={std:.6f} target={target:.6f}"


def test_per_tensor_init_std():
    torch.manual_seed(0)
    cfg = ModelConfig()
    model = GPT(cfg)

    base_std = 0.02
    residual_std = 0.02 / math.sqrt(2 * cfg.n_layer)  # n_layer=6 -> ~0.005774

    base_suffixes = (
        "wte.weight",
        "wpe.weight",
        "q_proj.weight",
        "k_proj.weight",
        "v_proj.weight",
        "fc_in.weight",
    )
    # The two residual-stream writers — D-04a: BOTH must be residual-scaled.
    residual_suffixes = ("c_proj.weight", "fc_out.weight")

    saw_c_proj = False
    saw_fc_out = False

    for name, p in model.named_parameters():
        std = p.std().item()
        if any(name.endswith(s) for s in residual_suffixes):
            _assert_std(name, std, residual_std)
            if name.endswith("c_proj.weight"):
                saw_c_proj = True
            if name.endswith("fc_out.weight"):
                saw_fc_out = True
        elif any(name.endswith(s) for s in base_suffixes):
            _assert_std(name, std, base_std)
        elif name.endswith(".bias"):
            assert p.abs().max().item() == 0.0, f"{name}: bias must be exactly 0"

    # Both residual-output projections were actually present and asserted (non-vacuous, D-04a).
    assert saw_c_proj, "no c_proj.weight found"
    assert saw_fc_out, "no fc_out.weight found"


def test_layernorm_params_default():
    # Hand-rolled LayerNorm (ln_1/ln_2/ln_f): weight all-ones, bias all-zeros.
    torch.manual_seed(0)
    model = GPT(ModelConfig())
    for name, p in model.named_parameters():
        if (".ln_" in name or name.startswith("ln_")) and name.endswith(".weight"):
            assert torch.allclose(p, torch.ones_like(p)), f"{name}: LayerNorm weight must be ones"
        if (".ln_" in name or name.startswith("ln_")) and name.endswith(".bias"):
            assert p.abs().max().item() == 0.0, f"{name}: LayerNorm bias must be zeros"
