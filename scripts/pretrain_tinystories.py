"""Thin no-CLI entry for the TinyStories long pretrain on local M3/MPS (PRE-02 / PRE-03).

Mirrors ``scripts/train_bigram.py``: logic lives in ``src/personacore/{model,training}`` — this
script only wires configs + LOCAL paths + the new memmap/best seams, then prints decoded samples
and the recorded perplexity. NO argparse (D-04): paths are ``_REPO_ROOT``-relative constants and
the calibrated hyperparameters are config-dataclass overrides.

Run: ``python scripts/pretrain_tinystories.py`` on the M3 (inside the Python 3.11 venv).
``RuntimeConfig()`` auto-resolves to MPS (fp32, AMP auto-off — no scaler path). The run is
kill-survivable: it resumes bit-for-bit from ``checkpoints/latest.pt`` whenever that file already
exists (laptop sleep/interrupt or a manual stop), and ships ``checkpoints/best.pt`` (the LOWEST
val-loss step, D-08) plus ``logs/run.csv`` curves. Outputs land in ``.gitignore``d paths
(``*.pt``, ``logs/``, ``checkpoints/``) so weight-based memory is never committed.

PREFLIGHT: ``preflight_device(strict=True)`` gates the long run on a usable accelerator (MPS on
the M3) and the LOCAL ``data/*.bin`` corpus — it does NOT reference the Kaggle dataset-mount
constant (this is the local primary path, not the Kaggle P100 fallback).

CALIBRATION (Task 4): the LR / batch_size / grad_accum_steps / max_steps / eval_interval /
checkpoint-every-K / sample-every-S constants below are MEASURED on the real M3 by the calibration
smoke (D-01a). The placeholders here are clearly marked TODO(calibration) — they are intentionally
NOT final numbers; the calibration task fills them from measured tokens/sec, the largest stable
batch, and the highest non-diverging LR.
"""

import math
import os
import pathlib

# An uncovered MPS op falls back to CPU rather than crashing the multi-hour run (T-05-04).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402
from personacore.training import sample, train  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"  # LOCAL memmap (not a Kaggle dataset mount)
VAL_BIN = _REPO_ROOT / "data" / "val.bin"  # LOCAL memmap (not a Kaggle dataset mount)
LOG_PATH = _REPO_ROOT / "logs" / "run.csv"  # gitignored (logs/)
CKPT_PATH = _REPO_ROOT / "checkpoints" / "latest.pt"  # gitignored (*.pt / checkpoints/)
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # gitignored — the shipped best-val checkpoint

# --- Calibration constants (Task 4 MEASURES these on the real M3 — do NOT invent final numbers) ---
LR = 3e-4  # TODO(calibration): highest non-diverging LR from the Stage-2 LR sweep.
BATCH_SIZE = 32  # TODO(calibration): largest stable (no-OOM, finite-loss) batch from Stage 1.
GRAD_ACCUM_STEPS = 1  # TODO(calibration): set so the effective batch is healthy.
MAX_STEPS = 50_000  # TODO(calibration): size from measured tokens/sec (quality-first, D-04).
EVAL_INTERVAL = 250  # TODO(calibration): eval/log cadence.
CHECKPOINT_INTERVAL = 250  # K: in-loop latest.pt cadence (a kill loses <= K steps).
SAMPLE_INTERVAL = 1_000  # S: qualitative coherence-check sample cadence (D-06).
SAMPLE_MAX_NEW_TOKENS = 200  # length of each periodic coherence sample.


def main() -> None:
    # Long-run gate: assert a usable accelerator (MPS on the M3) BEFORE training; never references
    # the Kaggle mount — this is the local primary path. Raises on a CPU-only box (strict).
    summary = preflight_device(strict=True)
    print(f"[pretrain] preflight: {summary}")

    # Assert the LOCAL corpus exists (run scripts/encode_corpus.py first — Plan 01).
    if not TRAIN_BIN.exists() or not VAL_BIN.exists():
        raise FileNotFoundError(
            f"Missing local corpus memmaps: {TRAIN_BIN} / {VAL_BIN}. "
            "Run `python scripts/encode_corpus.py` first (Plan 01)."
        )

    seed_everything(TrainConfig().seed)  # FRESH run only — resume restores RNG state instead.
    runtime = RuntimeConfig()  # MPS-aware (D-02); resolves device="mps" on the M3, AMP auto-off.
    model_cfg = ModelConfig()  # LOCKED 6L/6H/384d, block_size=256, vocab 8192, eos 8184.
    model = GPT(model_cfg)  # the REAL model (not BigramLanguageModel).

    cfg = TrainConfig(
        lr=LR,
        batch_size=BATCH_SIZE,
        grad_accum_steps=GRAD_ACCUM_STEPS,
        max_steps=MAX_STEPS,
    )

    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6).

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CKPT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Kill-survivable restart: resume from latest.pt iff it already exists (bit-for-bit, D-04).
    resume_from = CKPT_PATH if CKPT_PATH.exists() else None
    if resume_from is not None:
        print(f"[pretrain] resuming from {CKPT_PATH}")

    train(
        train_config=cfg,
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        train_bin=TRAIN_BIN,
        val_bin=VAL_BIN,
        eos_id=model_cfg.eos_id,
        log_path=LOG_PATH,
        checkpoint_path=CKPT_PATH,
        best_checkpoint_path=BEST_PATH,
        eval_interval=EVAL_INTERVAL,
        checkpoint_interval=CHECKPOINT_INTERVAL,
        sample_interval=SAMPLE_INTERVAL,
        tokenizer=tok,
        sample_max_new_tokens=SAMPLE_MAX_NEW_TOKENS,
        resume_from=resume_from,
    )

    # --- Ship best.pt: load it, record perplexity = exp(best_val_loss), print curated samples. ---
    blob = torch.load(BEST_PATH, weights_only=False)  # own trusted file.
    best_val_loss = blob["val_loss"]
    perplexity = math.exp(best_val_loss)
    model.load_state_dict(blob["model"])
    model.to(runtime.device)

    print(f"[pretrain] best.pt val_loss={best_val_loss:.4f}  perplexity={perplexity:.3f}")
    for i in range(3):
        seed = torch.tensor([[model_cfg.eos_id]], dtype=torch.long, device=runtime.device)
        out = sample(model, seed, max_new_tokens=SAMPLE_MAX_NEW_TOKENS)[0].tolist()
        print(f"[sample {i + 1}] {tok.decode(out)!r}")


if __name__ == "__main__":
    main()
