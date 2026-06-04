"""RED tests for the warmup + cosine LR schedule (TRAIN-01).

``build_lr_lambda(warmup_steps, max_steps, min_ratio=0.1)`` returns the hand-rolled multiplier:
a linear ramp 0->1 over ``warmup_steps`` then a cosine decay toward ``min_ratio``.
``build_scheduler(optimizer, train_cfg)`` wraps it in a ``LambdaLR``. The schedule steps per
OPTIMIZER step, not per micro-batch — so under grad accumulation the LR at optimizer-step N must
match the lambda at N, never at N*grad_accum (Pitfall 2). ``state_dict`` round-trips ``last_epoch``
so a killed run resumes the schedule exactly.

RED until Plan 02 implements ``personacore.training.schedule``. CPU-only, GPU-free; builds a tiny
nn.Linear + AdamW like test_checkpoint.py:_build.
"""

import torch

from personacore.config import TrainConfig
from personacore.training.schedule import build_lr_lambda, build_scheduler


def _build_optimizer(lr=1.0):
    # Base lr=1.0 so the LambdaLR multiplier reads straight off the param-group lr.
    model = torch.nn.Linear(4, 1)
    return torch.optim.AdamW(model.parameters(), lr=lr)


def test_warmup_ramps_from_zero_toward_one():
    fn = build_lr_lambda(warmup_steps=10, max_steps=100, min_ratio=0.1)
    # Step 0 starts near 0; the multiplier rises monotonically across warmup toward ~1 at the top.
    assert fn(0) < fn(5) < fn(9)
    assert fn(0) <= 0.2
    assert fn(10) >= 0.99  # end of warmup is the peak (multiplier ~1).


def test_cosine_decays_toward_min_ratio():
    fn = build_lr_lambda(warmup_steps=10, max_steps=100, min_ratio=0.1)
    # After warmup the cosine decays monotonically; the floor approaches min_ratio at max_steps.
    assert fn(10) > fn(55) > fn(99)
    assert abs(fn(100) - 0.1) < 1e-6


def test_lr_matches_lambda_at_optimizer_step_n():
    # After N optimizer steps the param-group lr equals base_lr * lambda(N) — schedule advances
    # per optimizer step, NOT per micro-batch (Pitfall 2).
    cfg = TrainConfig(lr=1.0, warmup_steps=10, max_steps=100)
    opt = _build_optimizer(lr=cfg.lr)
    sched = build_scheduler(opt, cfg)
    fn = build_lr_lambda(cfg.warmup_steps, cfg.max_steps, min_ratio=0.1)
    n = 5
    for _ in range(n):
        opt.step()
        sched.step()
    assert abs(opt.param_groups[0]["lr"] - cfg.lr * fn(n)) < 1e-6


def test_scheduler_state_dict_round_trips_last_epoch():
    cfg = TrainConfig(lr=1.0, warmup_steps=10, max_steps=100)
    opt = _build_optimizer(lr=cfg.lr)
    sched = build_scheduler(opt, cfg)
    for _ in range(7):
        opt.step()
        sched.step()
    state = sched.state_dict()
    assert state["last_epoch"] == 7

    # A fresh scheduler restores the exact position from the saved state.
    fresh_opt = _build_optimizer(lr=cfg.lr)
    fresh_sched = build_scheduler(fresh_opt, cfg)
    fresh_sched.load_state_dict(state)
    assert fresh_sched.state_dict()["last_epoch"] == 7
