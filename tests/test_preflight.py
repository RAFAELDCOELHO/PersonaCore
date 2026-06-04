"""Preflight unit tests (ENV-05): refuse a long run on a non-P100 / no-CUDA box.

All tests run CPU-only by monkeypatching torch.cuda — the live P100 assertion is a
manual-only Kaggle check (cell-1). The preflight must FAIL LOUD before any training tier
runs (Pitfall 1: a cu128+ wheel silently lacks Pascal sm_60 kernels).
"""

import pytest
import torch

from personacore.preflight import preflight_p100


def test_rejects_non_p100(monkeypatch):
    # A non-P100 GPU (e.g. Kaggle's T4) must raise with a message mentioning P100.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda *a, **k: "Tesla T4")
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda *a, **k: (7, 5))
    with pytest.raises(RuntimeError, match="(?i)p100"):
        preflight_p100()


def test_rejects_no_cuda(monkeypatch):
    # No CUDA at all (accelerator not set) must raise.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError):
        preflight_p100()


def test_cpu_ok_when_not_required(monkeypatch):
    # require_p100=False is the CPU/laptop path: a simulated P100 passes and returns a dict.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda *a, **k: "Tesla P100-PCIE-16GB")
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda *a, **k: (6, 0))
    monkeypatch.setattr(
        torch, "ones", lambda *a, **k: torch.zeros(8)
    )  # avoid a real CUDA alloc on a CPU box
    info = preflight_p100(require_p100=False)
    assert "device" in info and "cc" in info and "torch" in info
