"""Skipif-guarded MPS sanity gate (PRE-02 / D-01a): finite-loss + overfit-one-batch on device=mps.

This is the ONLY MPS-touching test in the suite. The WHOLE module is guarded by
``pytest.mark.skipif(not torch.backends.mps.is_available())`` so CPU-only CI cleanly SKIPS
(it does NOT error at collection). On the real M3 it RUNS the Task-4 sanity gate: the real
``GPT(ModelConfig())`` drops into the proven Phase-3 ``train()`` loop, lets ``RuntimeConfig()``
auto-resolve to MPS (single-source-of-truth — no manual ``device=`` plumbing), and overfits ONE
fixed batch. Two asserts encode the D-01a gate:

1. ``torch.isfinite(final_loss)`` — the finite-loss gate that catches a silent MPS NaN /
   CPU-fallback poisoning the run (T-05-04).
2. ``final_loss < ln(8192) - 2`` — the overfit-one-batch gate (copied VERBATIM from
   ``test_gpt_overfit.py``) proving loss drives far below the random-init CE ceiling on MPS.

If this NaNs or fails to overfit on the M3 while the CPU overfit gate passes, the calibration
checkpoint (Task 4) falls back to ``device=cpu`` for the long run.

D-44 (2026-08-31): THE AVAILABILITY VALUE IS NO LONGER RE-SPELLED HERE. This module used to carry
its own ``torch.backends.mps.is_available()`` call, which made it a SECOND definition of the device
gate — and a second definition is one the sweep-active flag can miss. It now imports the register's
``_MPS_SKIP`` from ``tests/test_phase23_mps_venue.py``, so there is exactly ONE definition of both
the value and the two-reason text, and this module inherits D-44's sweep-naming reason for free.
"""

import math

import torch

from personacore.config import ModelConfig, TrainConfig
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.training.loop import train
from test_phase23_mps_venue import _MPS_SKIP  # noqa: E402  (tests/ is not a package)

# Guard the WHOLE module: only the real M3 (MPS) runs it; CPU-only CI SKIPS (not ERRORS), and a
# live frontier sweep SKIPS with a reason naming the sweep (D-44). One mark, two reasons, one
# definition — see the register's `_MPS_ABSENT_REASON` / `_SWEEP_ACTIVE_REASON`.
pytestmark = _MPS_SKIP

UNIFORM_BOUND = math.log(8192)  # ~9.0 — the random-init CE ceiling the loop must beat on MPS.


def test_overfit_mps():
    # Determinism first (Pitfall 5), then memorize one fixed batch with the existing harness on MPS.
    seed_everything(1337)
    model = GPT(ModelConfig())  # the real model; RuntimeConfig() auto-resolves to MPS on the M3.

    # One fixed batch reused EVERY step (copied VERBATIM from test_gpt_overfit.py).
    fixed_idx = torch.randint(0, 8192, (4, 16))
    fixed_targets = torch.randint(0, 8192, (4, 16))

    cfg = TrainConfig(lr=1e-3, warmup_steps=0, max_steps=300, batch_size=4, grad_accum_steps=1)
    final_loss = train(
        train_config=cfg,
        model=model,
        fixed_batch=(fixed_idx, fixed_targets),
        return_final_loss=True,
    )

    # D-01a finite-loss gate: a silent MPS NaN / CPU-fallback poisoning must be caught here.
    assert torch.isfinite(torch.tensor(final_loss))
    # Overfit gate: memorizing one batch must push CE far below the uniform-prediction ceiling.
    assert float(final_loss) < UNIFORM_BOUND - 2.0
