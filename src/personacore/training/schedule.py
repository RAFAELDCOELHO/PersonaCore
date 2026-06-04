"""Hand-rolled warmup + cosine LR schedule (D-08 / TRAIN-01) as a resumable LambdaLR.

The decay math is written by hand (the from-scratch ethos), but it is wrapped in a
``torch.optim.lr_scheduler.LambdaLR`` because that is the LOAD-BEARING contract: ``checkpoint.py``
calls ``scheduler.state_dict()`` on save and ``scheduler.load_state_dict()`` on resume (D-05).
``LambdaLR`` serializes only the step counter (``last_epoch``) — the lambda itself is NOT
pickled (A1) — so the harness in Plan 04 MUST rebuild ``build_scheduler(...)`` identically before
``load_checkpoint`` for the ``last_epoch`` restore to be meaningful.

The multiplier rides on the optimizer's base lr: it ramps 0->1 linearly over ``warmup_steps``,
then cosine-decays 1 -> ``min_ratio`` across the remaining steps, holding ``min_ratio`` as a floor
at/after ``max_steps``. The scheduler advances per OPTIMIZER step, not per micro-batch — so under
grad accumulation the LR at optimizer-step N matches the lambda at N, never at N*grad_accum
(Pitfall 2).
"""

import math

from torch.optim.lr_scheduler import LambdaLR


def build_lr_lambda(warmup_steps: int, max_steps: int, min_ratio: float = 0.1):
    """Return the hand-rolled ``lr_lambda(step)`` multiplier (linear warmup -> cosine decay floor).

    - ``step < warmup_steps``: linear ramp ``(step + 1) / warmup_steps`` (0 -> ~1).
    - ``step >= max_steps``: the ``min_ratio`` floor.
    - otherwise: cosine decay from 1 to ``min_ratio`` over ``(max_steps - warmup_steps)``.
    """

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return (step + 1) / max(1, warmup_steps)
        if step >= max_steps:
            return min_ratio
        progress = (step - warmup_steps) / max(1, max_steps - warmup_steps)
        cosine = 0.5 * (1 + math.cos(math.pi * progress))
        return min_ratio + (1 - min_ratio) * cosine

    return lr_lambda


def build_scheduler(optimizer, train_cfg) -> LambdaLR:
    """Wrap the warmup+cosine lambda in a ``LambdaLR`` (the ``scheduler.state_dict()`` contract).

    Reads ``train_cfg.warmup_steps`` / ``train_cfg.max_steps``. The returned object is what
    ``checkpoint.py`` serializes/restores; rebuild it identically on resume (A1).
    """
    return LambdaLR(
        optimizer,
        build_lr_lambda(train_cfg.warmup_steps, train_cfg.max_steps),
    )
