"""Real-weights adapter smoke: best.pt + TinyStories bins -> ~1.3 MB adapter.pt (LORA-02/LORA-05).

The real-weights proof of the frozen-base training discipline: the CPU unit tests
(``tests/test_lora_training.py``) pin the canary on a tiny fixture; THIS script is where the
MPS silent-failure class is actually hunted (PITFALLS P5) — the params-actually-update canary
runs on the REAL 13.9M ``best.pt`` weights, on the real preflight device, after ~50 adapter
steps over the TinyStories memmaps. The script IS the proof: every assert is inline, so any
failure exits non-zero (09-RESEARCH Open Q2).

Mirrors ``scripts/pretrain_tinystories.py`` (thin no-CLI driver, logic lives in the package):
``_REPO_ROOT`` path constants, named tuned constants, ``preflight_device(strict=True)`` gate,
keyword-only ``train()`` call — ``training/loop.py`` is NEVER modified (the v1.0 loop is already
frozen-param safe). All outputs (smoke checkpoint, curve CSV, adapter.pt) land in gitignored
paths — weight-based memory is never committed.

Resume note (Open Q1 resolution): a killed smoke resumes by re-running this script with
``resume_from`` semantics — the script's own ``LORA_CFG`` constant rebuilds the module tree
deterministically (vanilla GPT -> load base -> inject -> freeze), so the checkpoint's optimizer
state re-associates without ``train()`` ever learning about LoRA.

Run: ``python scripts/train_adapter_smoke.py`` (inside the Python 3.11 venv).
"""

import math
import os
import pathlib
from dataclasses import asdict

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.checkpoint import export_adapter  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
from personacore.lora import (  # noqa: E402
    LoRAConfig,
    inject_lora,
    lora_state_dict,
    mark_only_lora_trainable,
    snapshot_params,
)
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.training import train  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted base checkpoint (gitignored)
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"  # LOCAL memmap corpus
VAL_BIN = _REPO_ROOT / "data" / "val.bin"  # LOCAL memmap corpus
SMOKE_CKPT = _REPO_ROOT / "checkpoints" / "adapter_smoke.pt"  # resumable smoke state (gitignored)
ADAPTER_PATH = _REPO_ROOT / "checkpoints" / "adapter.pt"  # the ~1.3 MB persona file (gitignored)
LOG_PATH = _REPO_ROOT / "logs" / "adapter_smoke.csv"  # NEW curve CSV, own file (gitignored)

# --- Tuned constants (smoke-scale: prove the discipline, not train a persona) ---
LORA_CFG = LoRAConfig()  # production defaults r=8/alpha=16.0 — the ~1.3 MB persona-file shape.
LR = 1e-3
WARMUP_STEPS = 5
MAX_STEPS = 50
BATCH_SIZE = 8
# Adapter runs MUST override TrainConfig's 0.1 default: weight decay on A/B fights the
# low-rank update and would also perturb frozen-adjacent dynamics (09-RESEARCH Pattern 3).
WEIGHT_DECAY = 0.0


def main() -> None:
    # Gate on a usable device (CUDA-P100 -> MPS -> CPU raise) BEFORE the run (pretrain precedent).
    summary = preflight_device(strict=True)
    print(f"[train_adapter_smoke] preflight: {summary}")

    if not BEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
        )
    if not TRAIN_BIN.exists() or not VAL_BIN.exists():
        raise FileNotFoundError(
            f"Missing local corpus memmaps: {TRAIN_BIN} / {VAL_BIN}. "
            "Run `python scripts/pretrain_tinystories.py` prerequisites (encode the corpus) first."
        )

    seed_everything(1337)
    runtime = RuntimeConfig()  # resolves the preflighted device (MPS on the M3, fp32, AMP off).

    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy objects.
    # TRUSTED-only read of the project's OWN checkpoint (T-09-11; pretrain post-run precedent) —
    # never a foreign file. The SHAREABLE artifact path stays weights_only=True via export_adapter.
    blob = torch.load(BEST_PATH, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering.

    n_layer = blob["model_config"]["n_layer"]
    n_embd = blob["model_config"]["n_embd"]
    n_wrapped = inject_lora(model, LORA_CFG)
    assert n_wrapped == 6 * n_layer, (
        f"inject_lora wrapped {n_wrapped} projections, expected 6 * n_layer = {6 * n_layer}"
    )
    mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # Closed-form census: 18 * r * n_embd per layer across the six projections (== 331,776 at
    # the production shape r=8 / 6L / 384d — the ~1.3 MB fp32 persona file).
    expected_trainable = LORA_CFG.r * n_layer * 18 * n_embd
    assert trainable == expected_trainable, (
        f"trainable census {trainable} != r*n_layer*18*n_embd = {expected_trainable}"
    )
    print(f"[train_adapter_smoke] injected {n_wrapped} wrappers, {trainable} trainable params")

    # Move BEFORE snapshotting: torch.equal raises on cross-device tensors, so the canary
    # snapshot and the post-run params must share the training device.
    model.to(runtime.device)
    before = snapshot_params(model)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SMOKE_CKPT.parent.mkdir(parents=True, exist_ok=True)

    final = train(
        train_config=TrainConfig(
            lr=LR,
            warmup_steps=WARMUP_STEPS,
            max_steps=MAX_STEPS,
            batch_size=BATCH_SIZE,
            weight_decay=WEIGHT_DECAY,
        ),
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        train_bin=TRAIN_BIN,
        val_bin=VAL_BIN,
        log_path=LOG_PATH,
        checkpoint_path=SMOKE_CKPT,
        return_final_loss=True,
    )
    assert math.isfinite(float(final)), f"non-finite final loss {final!r} (PITFALLS P5)"

    # CANARY on real weights (LORA-02 / LORA-05): every trainable moved, every frozen base
    # param bit-untouched at 13.9M scale. The asserts ARE the proof — non-zero exit on failure.
    for n, p in model.named_parameters():
        if p.requires_grad:
            assert not torch.equal(p, before[n]), (
                f"[canary] trainable {n} did not move — silent training failure (P5)"
            )
        else:
            assert torch.equal(p, before[n]), (
                f"[canary] frozen base param {n} changed — grad isolation broken (LORA-02)"
            )
    print("[train_adapter_smoke] canary passed: all lora_ moved, base bit-untouched")

    # Fingerprint READ from the base checkpoint, never recomputed (provenance trio, D-02).
    export_adapter(
        ADAPTER_PATH,
        adapter=lora_state_dict(model),
        lora_config=asdict(LORA_CFG),
        base_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )

    size_mb = ADAPTER_PATH.stat().st_size / 1e6
    print(f"[train_adapter_smoke] wrote {ADAPTER_PATH} ({size_mb:.2f} MB)")
    print(f"[train_adapter_smoke] final train loss: {float(final):.4f}")


if __name__ == "__main__":
    main()
