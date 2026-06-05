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
"""

import math

import pytest
import torch

from personacore.config import ModelConfig, TrainConfig
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.training.loop import train

# Guard the WHOLE module: only the real M3 (MPS) runs it; CPU-only CI SKIPS (not ERRORS).
pytestmark = pytest.mark.skipif(
    not torch.backends.mps.is_available(), reason="MPS not available (CPU-only CI)"
)

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
