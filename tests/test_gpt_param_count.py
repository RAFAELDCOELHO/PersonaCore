"""RED parameter-count gate: tied-weight-aware count in the [10M, 15M] band (MODEL-05).

The model targets ~10-15M params (CLAUDE.md: fits free-tier training + on-device CPU inference).
The count MUST dedup the tied ``wte``/``lm_head`` tensor by storage pointer so it is counted
exactly once (a value-copy "tying" would inflate the count by one vocab x n_embd block ~3.15M and
cross-fail test_gpt_weight_tying). Asserts the BAND, not the exact ~13.9M, so bias-count nuances
don't break it (D-11 / RESEARCH A6).

RED until Plan 02 implements ``personacore.model.GPT``. CPU-only, GPU-free.
"""

from personacore.config import ModelConfig
from personacore.model import GPT


def count_parameters(model) -> int:
    # Dedup by storage pointer: the same tensor (tied wte/lm_head) maps to one key, counted once.
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()
    return sum(seen.values())


def test_param_count_in_target_band():
    n = count_parameters(GPT(ModelConfig()))  # ~13.9M with locked 6/6/384/256 defaults.
    assert 10_000_000 <= n <= 15_000_000
