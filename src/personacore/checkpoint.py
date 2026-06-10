"""Open-dict resumable checkpoints (ENV-04 / QA-02 / M2 EWC seam).

A checkpoint is a plain ``dict`` bundling the FULL training state — model + optimizer +
scheduler + step + complete RNG generator state + embedded config + git SHA + a schema
version — never a bare ``state_dict``. Two properties make it load-bearing:

1. **Exact resume (ENV-04).** ``load_checkpoint`` RESTORES generator state via
   ``set_rng_state`` / ``set_state`` / ``setstate`` (NOT a re-seed — Pitfall 2), so a
   killed run resumes the SAME trajectory it would have followed uninterrupted. This is
   what makes the 30h/week Kaggle quota survivable across ~9h session caps.
2. **Open for extension (M2 EWC seam, TRAIN-06).** ``save_checkpoint`` accepts arbitrary
   ``**extra`` keys, so Milestone 2 can add ``fisher`` / ``theta_star`` with NO format
   change. The embedded config (D-03) makes the checkpoint the single source of truth —
   no sidecar config file.

Security: the resume checkpoint contains pickled optimizer/RNG/python objects, so it loads
with full (non-``weights_only``) pickle. It is therefore TRUSTED-ONLY — load it solely from
your own files. The slim INFERENCE checkpoint (``export_slim`` / ``load_slim``, Phase 8)
uses ``weights_only=True``. Loading always passes ``map_location="cpu"`` so a CUDA-saved
file resumes on a CPU laptop (Pitfall 5).
"""

import random
from dataclasses import asdict

import numpy as np
import torch

CKPT_SCHEMA_VERSION = 1
SLIM_SCHEMA_VERSION = 1  # slim INFERENCE artifact schema (DEMO-02), independent of the full one.


def save_checkpoint(
    path,
    *,
    model,
    optimizer,
    scheduler,
    step,
    model_config,
    train_config,
    git_sha,
    scaler=None,
    val_loss=None,
    **extra,
) -> None:
    """Serialize the full training state to ``path`` as an open dict.

    Captures model/optimizer/scheduler state_dicts, the step counter, the COMPLETE RNG
    generator state (python/numpy/torch/cuda), the embedded configs (D-03 / QA-02), the
    git SHA (provenance), and any ``**extra`` keys (the M2 EWC seam).

    The ``GradScaler`` state (CLAUDE.md's named ``scaler`` checkpoint field) is serialized too:
    on the fp16/P100 path the scale factor + growth tracker EVOLVE during training, so a resume
    that re-creates a fresh default-scale scaler would diverge from an uninterrupted run. On CPU
    (or any fp32 run) the scaler is disabled and ``state_dict()`` is an empty dict — harmless.
    """
    ckpt = {
        "schema_version": CKPT_SCHEMA_VERSION,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler is not None else None,
        "scaler": scaler.state_dict() if scaler is not None else None,
        "step": step,
        "val_loss": val_loss,
        "model_config": asdict(model_config),  # config travels WITH weights (QA-02)
        "train_config": asdict(train_config),
        "git_sha": git_sha,  # provenance (QA-02)
        "rng": {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.get_rng_state(),
            "cuda": (torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None),
        },
        # OPEN DICT: M2 may add "fisher" / "theta_star" here with no format change.
        **extra,
    }
    torch.save(ckpt, path)


def load_checkpoint(
    path, *, model, optimizer=None, scheduler=None, scaler=None, map_location="cpu"
):
    """Restore full training state from ``path`` and return the checkpoint dict.

    Loads model/optimizer/scheduler/scaler state, then RESTORES the captured RNG generator STATE
    (NOT a re-seed — Pitfall 2) so the random stream continues from the saved step. Returns
    the full dict so the caller can read ``step`` / configs / ``git_sha`` / extra keys.

    ``scaler`` restore uses ``ckpt.get("scaler")`` so a pre-fix (scaler-less) checkpoint resumes
    cleanly without it — the open-dict format stays backward compatible.
    """
    # weights_only=False: the resume checkpoint carries pickled optimizer/RNG/numpy
    # objects that the torch>=2.6 weights_only=True default rejects. TRUSTED-only file
    # (own checkpoint); the slim INFERENCE checkpoint (Phase 8) uses weights_only=True.
    ckpt = torch.load(path, map_location=map_location, weights_only=False)
    model.load_state_dict(ckpt["model"])
    if optimizer is not None and ckpt.get("optimizer") is not None:
        optimizer.load_state_dict(ckpt["optimizer"])
    if scheduler is not None and ckpt.get("scheduler") is not None:
        scheduler.load_state_dict(ckpt["scheduler"])
    if scaler is not None and ckpt.get("scaler") is not None:
        scaler.load_state_dict(ckpt["scaler"])

    rng = ckpt["rng"]  # RESTORE state -> continue the same stream (NOT re-seed)
    random.setstate(rng["python"])
    np.random.set_state(rng["numpy"])
    torch.set_rng_state(rng["torch"])
    if rng["cuda"] is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(rng["cuda"])

    return ckpt  # caller reads step / configs / git_sha / extra keys


def export_slim(full_path, slim_path, *, map_location="cpu") -> dict:
    """Export the shippable slim INFERENCE checkpoint from a FULL training checkpoint (DEMO-02).

    Keeps ONLY what inference needs: the model ``state_dict`` plus the QA-02 provenance trio
    (``model_config`` / ``git_sha`` / ``step``) and the recorded ``val_loss``. Dropped on
    purpose: ``optimizer`` / ``scheduler`` / ``scaler`` / ``rng`` / ``train_config`` — the slim
    file is for generation, never resume. With those pickled training objects gone, the result
    round-trips through ``torch.load(..., weights_only=True)`` (see ``load_slim``): tensors and
    primitive containers only, so nothing else can ride along (T-08-03).

    Returns the slim dict it wrote, so callers can print/inspect what shipped.
    """
    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy
    # objects that the torch>=2.6 weights_only=True default rejects. TRUSTED-only read of
    # the project's OWN checkpoint (T-08-02 / T-07-02 lineage) — never a foreign file.
    full = torch.load(full_path, map_location=map_location, weights_only=False)
    slim = {
        "schema_version": SLIM_SCHEMA_VERSION,
        "model": full["model"],
        "model_config": full["model_config"],
        "git_sha": full["git_sha"],  # provenance travels WITH the shipped weights (QA-02).
        "step": full["step"],
        "val_loss": float(full["val_loss"]),
    }
    torch.save(slim, slim_path)
    return slim


def load_slim(path, *, map_location="cpu") -> dict:
    """Load the slim INFERENCE checkpoint under the locked safe-load bar (T-08-01).

    ``weights_only=True`` is the restricted unpickler — tensors + primitive containers only,
    ZERO code execution on load. Every slim consumer (demo, notebook, tests) goes through this
    single choke point; the module docstring reserved exactly this split in Phase 1.
    """
    loaded = torch.load(path, map_location=map_location, weights_only=True)
    if loaded.get("schema_version") != SLIM_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported slim checkpoint schema_version {loaded.get('schema_version')!r} in "
            f"{path} (expected {SLIM_SCHEMA_VERSION}). Re-export with scripts/export_slim.py."
        )
    return loaded
