"""RED structural gate: the six named ``nn.Linear`` projections per block (MODEL-07).

The M2 LoRA bridge needs every adaptable projection to be a named ``nn.Linear`` module reachable
by name (no fused ``c_attn``, no inlined ``F.linear``). This phase ships NO wrapper and NO rank
params — just the named-module seam (D-03/D-04). Guards against a refactor that fuses QKV or
inlines a projection, which would make M2 LoRA unable to wrap it (RESEARCH line 411).

RED until Plan 02 implements ``personacore.model.GPT``. CPU-only, GPU-free.
"""

import torch.nn as nn

from personacore.config import ModelConfig
from personacore.model import GPT

PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")


def test_every_block_exposes_six_named_linear_projections():
    cfg = ModelConfig()
    model = GPT(cfg)
    linear_names = {n for n, m in model.named_modules() if isinstance(m, nn.Linear)}

    for blk in range(cfg.n_layer):
        for proj in PROJECTIONS:
            assert any(n.endswith(f"{blk}.{proj}") or n.endswith(proj) for n in linear_names), (
                f"block {blk}: missing named nn.Linear '{proj}'"
            )
