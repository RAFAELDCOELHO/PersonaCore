"""RED tests for the training loop's AMP ordering + grad accumulation (TRAIN-01 / TRAIN-02).

The fp16 AMP path has a load-bearing op ORDER (Pitfall 1): per optimizer step the loop must
``scaler.unscale_`` exactly once, THEN ``clip_grad_norm_``, THEN ``scaler.step``, THEN
``scaler.update`` — clipping unscaled grads and stepping/updating in that order. A "loss went
down" check is insufficient; these tests SPY on the call sequence. Grad accumulation over N
micro-batches must be numerically equivalent to one big batch within tolerance. The real fp16
kernel is exercised only behind an inline ``skipif`` (no ``cuda`` marker is registered in
pyproject.toml) so CI stays green on a CPU box.

RED until Plan 02 implements ``personacore.training.loop``. CPU-only except the guarded smoke.
"""

import pytest
import torch

from personacore.config import RuntimeConfig, TrainConfig
from personacore.training.loop import train


class _SpyScaler:
    """Wraps a GradScaler-shaped object, recording the order of AMP calls per optimizer step."""

    def __init__(self, calls):
        self._calls = calls

    def scale(self, loss):
        self._calls.append("scale")
        return loss

    def unscale_(self, optimizer):
        self._calls.append("unscale_")

    def step(self, optimizer):
        self._calls.append("step")
        optimizer.step()

    def update(self):
        self._calls.append("update")


def test_amp_ordering_unscale_clip_step_update(monkeypatch):
    # Record the AMP op sequence and assert unscale_ -> clip -> step -> update with exactly one
    # unscale_ per optimizer step (Pitfall 1). We spy on clip_grad_norm_ via the same call-log.
    calls: list[str] = []
    real_clip = torch.nn.utils.clip_grad_norm_

    def _spy_clip(params, max_norm, *a, **k):
        calls.append("clip")
        return real_clip(params, max_norm, *a, **k)

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", _spy_clip)

    cfg = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=1, grad_clip=1.0)
    runtime = RuntimeConfig(device="cpu")
    # The loop must thread our spy scaler through; train() accepts an injectable scaler so the
    # CPU test can observe the AMP ordering without a real GPU.
    train(train_config=cfg, runtime_config=runtime, scaler=_SpyScaler(calls))

    # Exactly one unscale_ for the single optimizer step, in the locked order.
    assert calls.count("unscale_") == 1
    order = [c for c in calls if c in ("unscale_", "clip", "step", "update")]
    assert order == ["unscale_", "clip", "step", "update"]


def test_grad_accum_equivalent_to_big_batch():
    # N micro-batches with grad_accum_steps=N must match one big batch within tolerance: the
    # accumulated-then-stepped loss equals the single-big-batch loss.
    cfg_accum = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=4, batch_size=4)
    cfg_big = TrainConfig(max_steps=1, warmup_steps=0, grad_accum_steps=1, batch_size=16)
    runtime = RuntimeConfig(device="cpu")

    accum_loss = train(train_config=cfg_accum, runtime_config=runtime, return_final_loss=True)
    big_loss = train(train_config=cfg_big, runtime_config=runtime, return_final_loss=True)
    assert abs(float(accum_loss) - float(big_loss)) < 1e-3


# Inline skipif (no `cuda` marker is registered in pyproject.toml) keeps CI green on CPU:
# the guard is `skipif(not torch.cuda.is_available())`; `reason` is required by pytest so the
# skip is a clean SKIP (not a collection ERROR) on a CPU box.
@pytest.mark.skipif(not torch.cuda.is_available(), reason="fp16 AMP smoke needs a CUDA GPU")
def test_amp_fp16_smoke():
    # Real fp16 path on a CUDA GPU runs without inf/nan in the loss (D-07b). Inline skipif keeps
    # CI green on CPU — no `cuda` marker is registered in pyproject.toml.
    cfg = TrainConfig(max_steps=2, warmup_steps=0)
    runtime = RuntimeConfig(device="cuda", amp=True, amp_dtype="float16")
    final_loss = train(train_config=cfg, runtime_config=runtime, return_final_loss=True)
    assert torch.isfinite(torch.as_tensor(float(final_loss)))
