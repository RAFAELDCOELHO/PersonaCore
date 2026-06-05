"""RED forward-contract gate for the from-scratch GPT decoder (MODEL-02).

Locks the LOCKED ``forward(idx, targets=None) -> (logits, loss)`` contract the GPT must honor so
it drops into the proven Phase-3 training loop with zero harness changes (D-05). Mirrors the
``tests/test_bigram_model.py`` seed-first / construct-and-assert idiom: logits shaped
``(B, T, vocab_size)``; ``targets is None`` -> ``(logits, None)``; else a scalar CE over the
``B*T`` flatten.

RED until Plan 02 implements ``personacore.model.GPT``. CPU-only, GPU-free, no fixture.
"""

import math

import torch

from personacore.config import ModelConfig
from personacore.model import GPT


def test_forward_contract():
    # forward(idx) -> (logits (B,T,V), None); forward(idx, targets) -> (logits, scalar_loss).
    model = GPT(ModelConfig(block_size=16))
    idx = torch.randint(0, 8192, (2, 8))

    logits, loss = model(idx)
    assert logits.shape == (2, 8, 8192)
    assert loss is None

    targets = torch.randint(0, 8192, (2, 8))
    logits, loss = model(idx, targets)
    assert logits.shape == (2, 8, 8192)
    assert isinstance(loss, torch.Tensor)
    assert loss.ndim == 0  # scalar CE reduced over the flattened B*T view.


def test_random_init_loss_sanity_band():
    # GPT's tied/scaled init only LOOSELY approaches ln(vocab) (RESEARCH A6) -> a GENEROUS band:
    # just guard against a mis-flattened / mis-reduced loss, not a tight uniform-prediction bound.
    torch.manual_seed(1337)
    model = GPT(ModelConfig(block_size=16))
    idx = torch.randint(0, 8192, (2, 8))
    targets = torch.randint(0, 8192, (2, 8))
    _, loss = model(idx, targets)
    expected = math.log(8192)  # ~9.0
    assert 0.0 < loss.item() < expected + 3.0
