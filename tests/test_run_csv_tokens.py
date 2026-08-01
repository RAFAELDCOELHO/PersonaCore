"""DEBT-01: the run.csv ``tokens`` column must count TRUE tokens.

Each optimizer step consumes ``batch_size * grad_accum_steps`` windows of ``block_size``
tokens, so the cumulative column at step N is ``N * batch_size * grad_accum_steps *
block_size``. The v1.0 loop omitted the ``* block_size`` factor (telemetry-only ×256
under-count, promoted to DEBT-01) — the Phase 12/13 forgetting-curve x-axes read this
column, so it must be correct before the first v2.0 training step.

CPU-only, synthetic bins, tiny model — no artifacts required.
"""

import csv

import numpy as np

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.training.loop import train

CPU_RUNTIME = RuntimeConfig(device="cpu")


def test_run_csv_tokens_counts_true_tokens(tmp_path):
    block_size = 32
    batch_size = 2
    grad_accum_steps = 2
    max_steps = 3

    rng = np.random.default_rng(0)
    ids = rng.integers(0, 8184, size=512, dtype=np.uint16)
    train_bin = tmp_path / "train.bin"
    val_bin = tmp_path / "val.bin"
    ids.tofile(train_bin)
    ids.tofile(val_bin)

    model_cfg = ModelConfig(block_size=block_size, n_layer=1, n_head=2, n_embd=16)
    train_cfg = TrainConfig(
        lr=1e-3,
        warmup_steps=1,
        max_steps=max_steps,
        batch_size=batch_size,
        grad_accum_steps=grad_accum_steps,
    )
    seed_everything(1234)
    model = GPT(model_cfg)
    log_path = tmp_path / "run.csv"

    train(
        train_config=train_cfg,
        runtime_config=CPU_RUNTIME,
        model=model,
        model_config=model_cfg,
        train_bin=train_bin,
        val_bin=val_bin,
        log_path=log_path,
        eval_interval=1,
    )

    with open(log_path) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == max_steps

    tokens_per_step = batch_size * grad_accum_steps * block_size
    for row in rows:
        step = int(row["step"])
        assert int(row["tokens"]) == step * tokens_per_step, (
            f"step {step}: tokens column {row['tokens']} != {step * tokens_per_step} "
            f"(batch {batch_size} × accum {grad_accum_steps} × block {block_size})"
        )
