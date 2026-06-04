"""RED forward-contract tests for the disposable bigram baseline (MODEL-01 / D-02).

The bigram is the Phase-3 throwaway that proves the harness (loop, checkpoint, sampling)
BEFORE the real GPT (Phase 4) exists. Its locked forward contract (D-02) is the same shape
the transformer will honor: ``forward(idx, targets=None) -> (logits, loss)`` with
``logits.shape == (B, T, vocab_size)`` and the cross-entropy computed on a flattened view.

RED until Plan 02 implements ``personacore.model.BigramLanguageModel``. CPU-only, GPU-free,
no fixture (random ``idx`` via seeded ``torch.randint``).
"""

import math

import torch

from personacore.model import BigramLanguageModel


def test_forward_returns_logits_none_without_targets():
    # forward(idx) -> (logits, None) with logits shaped (B, T, vocab_size) (D-02).
    model = BigramLanguageModel(vocab_size=32)
    idx = torch.randint(0, 32, (2, 5))
    logits, loss = model(idx)
    assert logits.shape == (2, 5, 32)
    assert loss is None


def test_forward_returns_scalar_loss_with_targets():
    # forward(idx, targets) -> (logits, loss) where loss is a 0-dim scalar tensor (D-02).
    model = BigramLanguageModel(vocab_size=32)
    idx = torch.randint(0, 32, (2, 5))
    targets = torch.randint(0, 32, (2, 5))
    logits, loss = model(idx, targets)
    assert logits.shape == (2, 5, 32)
    assert isinstance(loss, torch.Tensor)
    assert loss.ndim == 0  # scalar tensor (CE reduced over the flattened B*T view).


def test_random_init_loss_near_uniform_bound():
    # At random init the CE-flatten loss should sit near -ln(1/vocab_size) = ln(vocab_size):
    # a uniform-prediction sanity bound that catches a mis-flattened or mis-reduced loss.
    torch.manual_seed(1337)
    vocab_size = 32
    model = BigramLanguageModel(vocab_size=vocab_size)
    idx = torch.randint(0, vocab_size, (4, 8))
    targets = torch.randint(0, vocab_size, (4, 8))
    _, loss = model(idx, targets)
    expected = math.log(vocab_size)
    # Generous band: random init won't be exactly uniform, but must be in the right ballpark.
    assert abs(loss.item() - expected) < 1.0
