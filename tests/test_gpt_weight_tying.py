"""RED weight-tying gate: ``lm_head.weight`` IS ``wte.weight`` (MODEL-03).

GPT-2 ties the output head to the token embedding (saves ~3.15M params at the 8192 vocab). The
ONLY check that proves a TRUE shared tensor (not a ``.clone()`` value copy — RESEARCH Pitfall 2)
is ``data_ptr()`` identity: same storage pointer => one ``nn.Parameter``, coupled gradients, and
the tied tensor counted exactly once by the param-count gate.

RED until Plan 02 implements ``personacore.model.GPT``. CPU-only, GPU-free, no fixture.
"""

from personacore.config import ModelConfig
from personacore.model import GPT


def test_lm_head_shares_storage_with_token_embedding():
    # data_ptr() identity is the load-bearing assert: a copy would differ here AND inflate the
    # param count by one vocab x n_embd block (cross-checks test_gpt_param_count).
    model = GPT(ModelConfig())
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
