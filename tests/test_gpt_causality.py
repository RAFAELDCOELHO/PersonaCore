"""RED causality gate: future tokens cannot leak into past logits (MODEL-06).

The highest-value silent-bug guard in the milestone. A mask-after-softmax bug, an inverted
``tril`` comparison, or a finite (non ``-inf``) mask fill all TRAIN and GENERATE normally — only a
causality-perturbation test catches them (RESEARCH Pitfall 1). Perturbing the token at position
``t`` must leave logits at positions ``< t`` BIT-IDENTICAL while CHANGING the logits at ``t``. The
second assertion is non-vacuous: without it, a model that ignores its input entirely would pass.

RED until Plan 02 implements ``personacore.model.GPT``. CPU-only, GPU-free; ``eval()`` +
``no_grad()`` mandatory (dropout/train-mode flakes the comparison — Pitfall 4).
"""

import torch

from personacore.config import ModelConfig
from personacore.model import GPT


def test_changing_token_t_cannot_change_earlier_logits():
    torch.manual_seed(1337)
    model = GPT(ModelConfig(block_size=16))
    model.eval()

    B, T, V = 1, 8, model.config.vocab_size
    idx = torch.randint(0, V, (B, T))

    with torch.no_grad():
        logits_a, _ = model(idx)
        idx2 = idx.clone()
        t = 5
        idx2[0, t] = (idx2[0, t] + 1) % V  # perturb the token at position t.
        logits_b, _ = model(idx2)

    # Past positions (< t) must be bit-identical: the future cannot influence the past.
    assert torch.allclose(logits_a[:, :t, :], logits_b[:, :t, :], atol=1e-6)
    # Non-vacuous: position t DID change, proving the perturbation was real (not an inert model).
    assert not torch.allclose(logits_a[:, t, :], logits_b[:, t, :], atol=1e-6)
