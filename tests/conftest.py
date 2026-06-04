"""Shared test fixtures — Pascal/P100 device simulation without a real GPU."""

import pytest


@pytest.fixture
def simulate_pascal(monkeypatch):
    """Make torch report an available CUDA device with Pascal compute capability (6, 0).

    Lets the bf16-on-Pascal guard be tested on a CPU-only box (CI, laptop).
    """
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda *a, **k: (6, 0))
    return monkeypatch
