"""RED overfit-one-batch sanity gate for the training loop (TRAIN-05 / D-10).

The cheapest "the loop actually learns" proof: feed ONE fixed batch every step and drive the
loss far below the random-init bound ``ln(8192) ~= 9.0``. If a fixed batch can't be memorized,
the optimizer/loss/backward wiring is broken regardless of how the full run looks. Determinism
comes from ``seed_everything`` (Pitfall 5); a DEDICATED small TrainConfig (no warmup, a few
hundred steps, a high lr) makes the memorization fast and reliable.

RED until Plan 02 implements ``personacore.training.loop``. CPU-only, GPU-free. The exact final
threshold is pinned by the Plan-04 executor (A2); here we assert it lands well under ln(8192).
"""

import math

import torch
from personacore.model import BigramLanguageModel
from personacore.training.loop import train

from personacore.config import TrainConfig
from personacore.seeding import seed_everything

UNIFORM_BOUND = math.log(8192)  # ~9.0 — the random-init CE ceiling the loop must beat.


def test_overfits_single_fixed_batch():
    # Determinism first (Pitfall 5), then memorize one fixed batch with an aggressive config.
    seed_everything(1337)
    model = BigramLanguageModel(vocab_size=8192)

    # One fixed batch reused EVERY step (the loop receives it via a single-batch sampler).
    fixed_idx = torch.randint(0, 8192, (4, 16))
    fixed_targets = torch.randint(0, 8192, (4, 16))

    cfg = TrainConfig(lr=1e-1, warmup_steps=0, max_steps=300, batch_size=4, grad_accum_steps=1)
    final_loss = train(
        train_config=cfg,
        model=model,
        fixed_batch=(fixed_idx, fixed_targets),
        return_final_loss=True,
    )

    # Memorizing a single batch must push CE far below the uniform-prediction ceiling.
    assert float(final_loss) < UNIFORM_BOUND - 2.0
