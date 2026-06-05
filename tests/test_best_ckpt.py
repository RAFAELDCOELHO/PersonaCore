"""RED best-val-loss tracking + perplexity tests (PRE-03).

Proves the D-08 "ship best-val" contract: when ``best_checkpoint_path`` is set, ``train()`` writes
``best.pt`` at the step with the run's LOWEST validation loss (NOT the final step's), and that
``perplexity = exp(best_val_loss)`` is recoverable from the saved blob (the PRE-03 figure).

To make the assertion deterministic and non-tautological we script a val-loss curve that DIPS
then RISES (monkeypatching ``estimate_loss`` in the loop) and assert ``best.pt`` captured the dip,
not the larger final value. Inspecting the blob uses the same ``torch.load(path,
weights_only=False)`` idiom as ``test_resume_curve.py`` (own trusted file).

CPU-only, GPU/MPS-free. RED until Task 2 adds the ``best_checkpoint_path`` best-val seam to the
eval branch of ``train()``.
"""

import math
import pathlib

import numpy as np
import pytest
import torch

import personacore.training.loop as loop
from personacore.config import ModelConfig, TrainConfig
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.tokenizer import from_json
from personacore.training.loop import train

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "tinystories_fixture.txt"
TOKENIZER_PATH = "artifacts/tokenizer.json"
EOS_ID = 8184


def _build_bins(tmp_path):
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6).
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    ids = tok.encode(text, allowed_special="all")
    docs, cur = [], []
    for t in ids:
        cur.append(t)
        if t == EOS_ID:
            docs.append(cur)
            cur = []
    if cur and tok.decode(cur).strip():
        docs.append(cur)
    train_ids = np.array([t for d in docs[:-1] for t in d], dtype=np.uint16)
    val_ids = np.array([t for d in docs[-1:] for t in d], dtype=np.uint16)
    train_bin = tmp_path / "train.bin"
    val_bin = tmp_path / "val.bin"
    train_ids.tofile(train_bin)
    val_ids.tofile(val_bin)
    return train_bin, val_bin


def test_best_ckpt_tracks_lowest_val_loss(tmp_path, monkeypatch):
    train_bin, val_bin = _build_bins(tmp_path)
    best_path = tmp_path / "best.pt"

    # Script a val-loss curve that DIPS then RISES so the lowest value is NOT the final step's.
    # Six eval points (eval_interval=1, max_steps=6): the minimum is 1.0 at the 4th eval.
    scripted = [4.0, 3.0, 2.0, 1.0, 1.5, 2.5]
    min_observed = min(scripted)
    calls = {"i": 0}

    def fake_estimate_loss(model, val_ids, train_cfg, model_cfg, device, iters=20):
        v = scripted[calls["i"]]
        calls["i"] += 1
        return v

    monkeypatch.setattr(loop, "estimate_loss", fake_estimate_loss)

    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)
    seed_everything(1234)
    model = GPT(ModelConfig())
    train(
        train_config=cfg,
        model=model,
        train_bin=train_bin,
        val_bin=val_bin,
        log_path=tmp_path / "run.csv",  # eval branch fires only when a logger is present
        best_checkpoint_path=best_path,
        eval_interval=1,
    )

    assert calls["i"] == len(scripted), "every step should have produced a scripted val loss"
    assert best_path.exists(), "best.pt must be written when best_checkpoint_path is set"

    # best.pt holds the LOWEST observed val loss (the dip), NOT the final step's larger value.
    blob = torch.load(best_path, weights_only=False)  # own trusted file.
    assert blob["val_loss"] == pytest.approx(min_observed)
    assert blob["val_loss"] != pytest.approx(scripted[-1])

    # perplexity = exp(best_val_loss) is the recoverable PRE-03 figure.
    perplexity = math.exp(blob["val_loss"])
    assert perplexity == pytest.approx(math.exp(min_observed))
