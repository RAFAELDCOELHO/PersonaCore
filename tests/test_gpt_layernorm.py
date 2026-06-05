"""RED oracle gate: hand-rolled LayerNorm == nn.LayerNorm (MODEL-02).

The from-scratch normalization narrative ships a hand-rolled ``LayerNorm`` (exported from
``personacore.model.gpt``); ``nn.LayerNorm`` is the trusted oracle (D-09). The load-bearing
subtlety (RESEARCH Pitfall 6): the hand-rolled impl must use POPULATION variance
(``unbiased=False``) with ``eps=1e-5`` to match ``nn.LayerNorm``'s defaults — a ``unbiased=True``
bug diverges at ~1e-3 and only this oracle catches it. Fresh weight=1/bias=0 init means no param
copy is needed.

RED until Plan 02 implements ``personacore.model.gpt.LayerNorm``. CPU-only, GPU-free.
"""

import torch
import torch.nn as nn
from personacore.model.gpt import LayerNorm


def test_hand_rolled_layernorm_matches_nn_layernorm():
    torch.manual_seed(0)
    C = 384
    custom = LayerNorm(C)
    ref = nn.LayerNorm(C)  # default eps=1e-5, population variance, weight=1/bias=0.

    x = torch.randn(2, 8, C)  # fp32; oracle divergence grows as the last dim shrinks.
    assert torch.allclose(custom(x), ref(x), atol=1e-6)
