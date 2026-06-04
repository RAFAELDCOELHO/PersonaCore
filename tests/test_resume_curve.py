"""RED resume-trajectory + curve-reproducibility tests for the loop (TRAIN-04 / TRAIN-06).

Modeled on ``test_checkpoint.py::test_resume_identical_trajectory`` (lines 43-80): a killed-and-
resumed run must continue the SAME trajectory as an uninterrupted one — next-step loss AND a
sampled param match within 1e-6 — now on the real ``BigramLanguageModel`` + ``build_scheduler``
instead of the toy Linear. The CSV log must also survive the restart: concatenating the pre-kill
and post-resume rows equals an uninterrupted run's rows, with the header written exactly once
(Pitfall 4 — Kaggle session restarts).

RED until Plan 02 implements ``personacore.training.{loop,schedule,data}``. CPU-only, GPU-free.
"""

import csv
import pathlib

import torch
from personacore.model import BigramLanguageModel
from personacore.training.loop import train

from personacore.config import ModelConfig, TrainConfig
from personacore.seeding import seed_everything

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
EOS_ID = 8184


def _read_rows(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def _build():
    # The real bigram instead of the toy Linear used in test_checkpoint.py:_build.
    model = BigramLanguageModel(vocab_size=ModelConfig().vocab_size)
    return model


def test_resume_identical_trajectory(tmp_path):
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)

    # --- Reference: an uninterrupted run of all max_steps ---
    seed_everything(1234)
    ref_model = _build()
    ref = train(
        train_config=cfg,
        model=ref_model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        return_final_loss=True,
    )
    ref_param = ref_model.token_embedding_table.weight.detach().clone()

    # --- Resumed: run half, checkpoint, KILL, fresh model, resume to the end ---
    seed_everything(1234)
    half_model = _build()
    ckpt_path = tmp_path / "latest.pt"
    train(
        train_config=cfg,
        model=half_model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        max_steps_override=3,
        checkpoint_path=ckpt_path,
    )

    fresh_model = _build()
    resumed = train(
        train_config=cfg,
        model=fresh_model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        resume_from=ckpt_path,
        return_final_loss=True,
    )
    resumed_param = fresh_model.token_embedding_table.weight.detach().clone()

    # Trajectory equality within 1e-6 (the checkpoint restores RNG STATE, not a re-seed).
    assert abs(float(resumed) - float(ref)) < 1e-6
    assert torch.allclose(resumed_param, ref_param, atol=1e-6)


def test_csv_curve_survives_restart(tmp_path):
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)

    # Uninterrupted reference curve.
    seed_everything(1234)
    ref_log = tmp_path / "ref.csv"
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        log_path=ref_log,
    )
    ref_rows = _read_rows(ref_log)

    # Killed-and-resumed run writing to the SAME csv path across the restart.
    seed_everything(1234)
    split_log = tmp_path / "split.csv"
    ckpt_path = tmp_path / "latest.pt"
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        max_steps_override=3,
        checkpoint_path=ckpt_path,
        log_path=split_log,
    )
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        resume_from=ckpt_path,
        log_path=split_log,
    )
    split_rows = _read_rows(split_log)

    # Header appears exactly once across the restart (Pitfall 4), and the concatenated curve
    # equals the uninterrupted one row-for-row.
    header = ref_rows[0]
    assert split_rows.count(header) == 1
    assert split_rows == ref_rows
