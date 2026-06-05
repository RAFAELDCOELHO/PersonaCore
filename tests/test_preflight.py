"""Preflight unit tests (ENV-05): device gate with CUDA-P100 -> MPS -> CPU priority.

All tests run CPU-only by monkeypatching torch.cuda / torch.backends.mps — the live P100
assertion is a manual-only Kaggle check (cell-1). The preflight must FAIL LOUD before any
training tier runs (Pitfall 1: a cu128+ wheel silently lacks Pascal sm_60 kernels).
``strict=True`` is the long-run gate; ``strict=False`` is the laptop/CI summary path.
"""

import pytest
import torch

from personacore.preflight import preflight_device


def test_rejects_non_p100(monkeypatch):
    # A non-P100 GPU (e.g. Kaggle's T4) must raise with a message mentioning P100.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda *a, **k: "Tesla T4")
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda *a, **k: (7, 5))
    with pytest.raises(RuntimeError, match="(?i)p100"):
        preflight_device(strict=True)


def test_p100_ok_when_not_strict(monkeypatch):
    # strict=False is the laptop/CI path: a simulated P100 passes and returns a dict.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda *a, **k: "Tesla P100-PCIE-16GB")
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda *a, **k: (6, 0))
    monkeypatch.setattr(
        torch, "ones", lambda *a, **k: torch.zeros(8)
    )  # avoid a real CUDA alloc on a CPU box
    info = preflight_device(strict=False)
    assert "device" in info and "cc" in info and "torch" in info


def test_mps_ok_when_strict(monkeypatch):
    # No CUDA but MPS available: a usable long-run device under D-01 -> returns mps, no raise.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
    info = preflight_device(strict=True)
    assert info["device"] == "mps"
    assert info["cc"] is None
    assert "torch" in info


def test_cpu_raises_when_strict(monkeypatch):
    # No CUDA + no MPS + strict: no usable accelerator for a long run -> raise.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    with pytest.raises(RuntimeError):
        preflight_device(strict=True)


def test_cpu_ok_when_not_strict(monkeypatch):
    # No CUDA + no MPS + non-strict: degrade to a CPU summary dict without raising
    # (preserves the old require_p100=False intent).
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    info = preflight_device(strict=False)
    assert info["device"] == "cpu"
    assert info["cc"] is None
    assert "torch" in info
