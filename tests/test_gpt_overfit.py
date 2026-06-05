"""RED overfit-one-batch gate: the GPT drops into the Phase-3 loop and learns (MODEL-02 SC#1).

Copies the ``tests/test_overfit_batch.py`` scaffold VERBATIM, swapping ONLY the model
(``BigramLanguageModel`` -> ``GPT(ModelConfig())``). ``train()`` (loop.py), ``TrainConfig``
(config.py), and ``seed_everything`` (seeding.py) are REUSED UNTOUCHED — this is the proof the GPT
plugs into the proven harness with zero changes (D-07). Feed ONE fixed batch every step and drive
CE far below the random-init ceiling ``ln(8192) ~= 9.0``.

RED until Plan 02 implements ``personacore.model.GPT``. CPU-only, GPU-free.
"""

import math

import torch

from personacore.config import ModelConfig, TrainConfig
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.training.loop import train

UNIFORM_BOUND = math.log(8192)  # ~9.0 — the random-init CE ceiling the loop must beat.


def test_gpt_overfits_single_fixed_batch():
    # Determinism first (Pitfall 5), then memorize one fixed batch with the existing harness.
    seed_everything(1337)
    model = GPT(ModelConfig())  # ONLY change from test_overfit_batch.py: the model.

    # One fixed batch reused EVERY step (the loop receives it via a single-batch sampler).
    fixed_idx = torch.randint(0, 8192, (4, 16))
    fixed_targets = torch.randint(0, 8192, (4, 16))

    # TUNED (Plan-03 executor, RESEARCH Open Q1): a 6-layer pre-norm GPT overfits a tiny fixed
    # batch with lr=1e-3 (smaller than the bigram's 1e-1), warmup_steps=0, max_steps=300. Measured
    # final loss ~= 5e-4 (margin ~7.0 under the ln(8192)-2 bound) in ~11s on CPU with the FULL
    # ModelConfig — no reduced block_size needed, so the harness-swap proof holds at the real
    # architecture. The asserted bound below is a band, not a fixed loss; do not loosen it.
    cfg = TrainConfig(lr=1e-3, warmup_steps=0, max_steps=300, batch_size=4, grad_accum_steps=1)
    final_loss = train(
        train_config=cfg,
        model=model,
        fixed_batch=(fixed_idx, fixed_targets),
        return_final_loss=True,
    )

    # Memorizing a single batch must push CE far below the uniform-prediction ceiling.
    assert float(final_loss) < UNIFORM_BOUND - 2.0
