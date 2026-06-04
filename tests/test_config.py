"""Config-layer unit tests (ENV-03): fp32 default, AMP-off-on-CPU, bf16-raises-on-Pascal.

All tests are CPU-only and GPU-free so CI runs them.
"""

import pytest

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig


def test_fp32_default():
    # fp32 is the default precision: amp must be False without any opt-in.
    cfg = RuntimeConfig(device="cpu")
    assert cfg.amp is False


def test_amp_off_on_cpu():
    # Requesting AMP on a CPU device is silently disabled in __post_init__.
    cfg = RuntimeConfig(device="cpu", amp=True)
    assert cfg.amp is False


def test_bf16_raises_on_pascal(simulate_pascal):
    # bf16 on a Pascal/P100 device (capability major < 7) must RAISE, not warn.
    with pytest.raises(ValueError, match="(?i)pascal|p100|7.0"):
        RuntimeConfig(device="cuda", amp_dtype="bfloat16")


def test_fp16_ok_on_pascal(simulate_pascal):
    # fp16 AMP is fine on Pascal — only bf16 is guarded.
    cfg = RuntimeConfig(device="cuda", amp_dtype="float16", amp=True)
    assert cfg.amp is True
    assert cfg.amp_dtype == "float16"


def test_configs_are_dataclasses():
    model = ModelConfig()
    train = TrainConfig()
    # ModelConfig carries model-sizing hyperparameters.
    assert hasattr(model, "vocab_size")
    assert hasattr(model, "block_size")
    # TrainConfig carries training hyperparameters.
    assert hasattr(train, "lr")
    assert hasattr(train, "grad_accum_steps")
    assert hasattr(train, "seed")


def test_vocab_size_and_eos_locked():
    # Phase 2 locks the load-bearing deliverable: vocab_size=8192 (D-01) and eos_id=8184 (D-03).
    model = ModelConfig()
    assert model.vocab_size == 8192
    assert model.eos_id == 8184
