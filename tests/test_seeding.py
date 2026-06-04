"""Seeding unit tests (ENV-05): determinism across random/numpy/torch + RNG round-trip.

All tests are CPU-only and GPU-free so CI runs them.
"""

import random

import numpy as np
import torch

from personacore.seeding import seed_everything


def _draw():
    """Pull one sample from each RNG stream (python / numpy / torch)."""
    return (random.random(), float(np.random.rand()), torch.rand(1).item())


def test_determinism():
    # A fixed seed must yield identical draws across two independent seed_everything calls.
    seed_everything(1337)
    first = _draw()
    seed_everything(1337)
    second = _draw()
    assert first == second


def test_determinism_different_seed_differs():
    # Sanity: different seeds should (overwhelmingly) produce different draws.
    seed_everything(1)
    a = _draw()
    seed_everything(2)
    b = _draw()
    assert a != b


def test_rng_roundtrip():
    # Capture state -> draw -> restore state -> draw again: identical draw proves
    # generator-STATE restore (the mechanism load_checkpoint relies on, not a re-seed).
    seed_everything(99)
    py_state = random.getstate()
    np_state = np.random.get_state()
    torch_state = torch.get_rng_state()

    before = _draw()

    random.setstate(py_state)
    np.random.set_state(np_state)
    torch.set_rng_state(torch_state)
    after = _draw()

    assert before == after


def test_cudnn_benchmark_disabled():
    # seed_everything turns off the cuDNN autotuner for reproducibility (Pitfall 3).
    seed_everything(7)
    assert torch.backends.cudnn.benchmark is False
