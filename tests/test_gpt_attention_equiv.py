"""RED numeric-equivalence gate: manual attention == F.scaled_dot_product_attention (MODEL-02).

Proves the hand-rolled attention math is CORRECT (the portfolio claim) by comparing it to the
allowed PyTorch oracle ``F.scaled_dot_product_attention(is_causal=True)``. Both GPTs SHARE weights
via ``load_state_dict`` so only the attention path differs; the manual path must use the same
``1/sqrt(d_head)`` scale and ``(B, n_head, T, d_head)`` layout sdpa uses internally (RESEARCH
Pitfall 5). ``eval()`` + ``dropout=0.0`` are mandatory or the comparison flakes (Pitfall 4).

RED until Plan 02 implements ``personacore.model.GPT`` with the ``attn_impl`` toggle.
CPU-only, GPU-free (Pascal's flash backend never engages; sdpa falls back to the math backend,
numerically identical to manual).
"""

import torch
from torch.nn.functional import scaled_dot_product_attention  # noqa: F401  (oracle the impl uses)

from personacore.config import ModelConfig
from personacore.model import GPT


def test_manual_attention_matches_sdpa():
    torch.manual_seed(0)
    cfg = ModelConfig(block_size=16)
    m_manual = GPT(cfg, attn_impl="manual").eval()
    m_sdpa = GPT(cfg, attn_impl="sdpa").eval()
    m_sdpa.load_state_dict(m_manual.state_dict())  # SAME weights, only the attn path differs.

    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        la, _ = m_manual(idx)
        lb, _ = m_sdpa(idx)

    assert torch.allclose(la, lb, atol=1e-5)
