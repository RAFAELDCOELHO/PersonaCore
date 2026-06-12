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
import warnings
from dataclasses import asdict

import numpy as np
import torch

CKPT_SCHEMA_VERSION = 1
SLIM_SCHEMA_VERSION = 1  # slim INFERENCE artifact schema (DEMO-02), independent of the full one.
ADAPTER_SCHEMA_VERSION = 1  # adapter "persona file" schema (LORA-03 / D-01); independent again.
FISHER_SCHEMA_VERSION = 1  # Fisher cache schema (EWC-01 / Phase 10); independent again.

# Core checkpoint fields that ``save_checkpoint(**extra)`` must never overwrite. Keys that
# shadow NAMED parameters (``model``, ``step``, ...) already raise ``TypeError`` from Python's
# keyword mechanics; ``rng`` and ``schema_version`` are NOT parameters and would otherwise pass
# through ``**extra`` silently — corruption that surfaces only as an opaque error at RESUME
# time, deep inside ``load_checkpoint``'s RNG restore. Guarded fail-loud at SAVE time instead.
_RESERVED_CKPT_KEYS = frozenset(
    {
        "schema_version",
        "model",
        "optimizer",
        "scheduler",
        "scaler",
        "step",
        "val_loss",
        "model_config",
        "train_config",
        "git_sha",
        "rng",
    }
)


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

    ``**extra`` keys colliding with reserved core fields raise ``ValueError`` here, at save
    time — never a silent overwrite that bricks the checkpoint at resume.
    """
    clash = _RESERVED_CKPT_KEYS & extra.keys()
    if clash:
        raise ValueError(
            f"save_checkpoint: extra keys {sorted(clash)} collide with reserved "
            "checkpoint fields — they would silently overwrite core resume state."
        )
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
    # WR-02: save_checkpoint defaults val_loss=None, so the exporter's contract must cover
    # None — float(None) raised an opaque TypeError. None survives weights_only=True (it is
    # a primitive), so the slim safe-load contract is preserved.
    val_loss = full.get("val_loss")
    slim = {
        "schema_version": SLIM_SCHEMA_VERSION,
        "model": full["model"],
        "model_config": full["model_config"],
        "git_sha": full["git_sha"],  # provenance travels WITH the shipped weights (QA-02).
        "step": full["step"],
        "val_loss": float(val_loss) if val_loss is not None else None,
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


def export_adapter(path, *, adapter, lora_config, base_fingerprint) -> dict:
    """Export the adapter "persona file" artifact (LORA-03 / D-01).

    The persona file carries ONLY the LoRA A/B tensors plus primitive metadata — a small,
    swappable, shareable, deletable artifact designed to meet the slim safe-load bar (D-01):
    tensors and primitive containers exclusively, so it round-trips through
    ``torch.load(..., weights_only=True)`` (see ``load_adapter``) with zero code execution.

    The caller supplies plain dicts — ``checkpoint.py`` NEVER imports ``lora/`` (locked
    dependency direction; mirrors how ``export_slim`` takes a path, not a model). Callers
    produce ``adapter`` via ``personacore.lora.lora_state_dict`` (the ``lora_``-key filter
    that keeps base weights out of the shareable file) and ``lora_config`` via
    ``dataclasses.asdict``; ``base_fingerprint`` is the QA-02 provenance trio
    (``git_sha`` / ``step`` / ``val_loss``) of the base the adapter was trained on (D-02).

    Returns the artifact dict it wrote (``export_slim``'s return-what-shipped precedent).
    """
    art = {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "adapter": adapter,
        "lora_config": lora_config,
        "base_fingerprint": base_fingerprint,
    }
    torch.save(art, path)
    return art


def load_adapter(path, *, expected_fingerprint=None, map_location="cpu") -> dict:
    """Load the adapter persona file under the locked safe-load bar (LORA-03 / D-01).

    ``weights_only=True`` is the restricted unpickler — tensors + primitive containers only,
    ZERO code execution on load (T-09-07). Every adapter consumer (demo, Phase 14 persona
    loads, tests) goes through this SINGLE choke point — verbatim ``load_slim`` discipline.

    When ``expected_fingerprint`` is given and differs from the artifact's
    ``base_fingerprint``, a ``UserWarning`` names BOTH fingerprints but the artifact still
    loads — D-02 is locked: warn but load, because the base evolves mid-milestone and a hard
    error would brick every adapter at each base re-export.

    Structural validation: a schema-valid file missing any required key (``adapter`` /
    ``lora_config`` / ``base_fingerprint``) raises a ``ValueError`` naming the gaps HERE —
    the single choke point — instead of a bare ``KeyError`` deep in a downstream consumer.
    """
    loaded = torch.load(path, map_location=map_location, weights_only=True)
    if loaded.get("schema_version") != ADAPTER_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported adapter schema_version {loaded.get('schema_version')!r} in "
            f"{path} (expected {ADAPTER_SCHEMA_VERSION}). Re-export with "
            "personacore.checkpoint.export_adapter."
        )
    missing = {"adapter", "lora_config", "base_fingerprint"} - loaded.keys()
    if missing:
        raise ValueError(
            f"malformed adapter artifact {path}: missing keys {sorted(missing)} "
            "(expected an export_adapter persona file)."
        )
    if expected_fingerprint is not None and loaded["base_fingerprint"] != expected_fingerprint:
        warnings.warn(
            f"adapter base fingerprint mismatch: artifact carries "
            f"{loaded['base_fingerprint']!r} but the loaded base is {expected_fingerprint!r} "
            "— loading anyway (D-02 — base evolves mid-milestone).",
            UserWarning,
            stacklevel=2,
        )
    return loaded


def export_fisher(path, *, fisher, fisher_meta, anchor_fingerprint) -> dict:
    """Export the shareable Fisher cache (EWC-01 / Phase 10).

    The cache carries the normalized diagonal Fisher tensors plus primitive metadata — one
    estimation pass at ``best.pt`` shared by Phase 12/13's A/B arms. Designed to meet the
    slim safe-load bar: tensors and primitive containers exclusively, so it round-trips
    through ``torch.load(..., weights_only=True)`` (see ``load_fisher``) with zero code
    execution on load (T-10-06).

    The caller supplies plain dicts — ``checkpoint.py`` NEVER imports ``continual/`` (the
    locked dependency direction; the ``export_adapter`` precedent). Callers produce ``fisher``
    / ``fisher_meta`` via ``personacore.continual.estimate_fisher`` (``{str: fp32 CPU tensor}``
    + primitives-only meta); ``anchor_fingerprint`` is the QA-02 provenance trio
    (``git_sha`` / ``step`` / ``val_loss``) READ from the anchor checkpoint, never recomputed.

    ``theta_star`` is deliberately NOT in the cache: it is recoverable from ``best.pt``, which
    ``anchor_fingerprint`` pins — the cache is an optimization only, and resume never depends
    on it (resume checkpoints carry Fisher/theta_star by value via ``save_checkpoint(**extra)``;
    ARCHITECTURE anti-pattern 2).

    Returns the cache dict it wrote (``export_slim``'s return-what-shipped precedent).
    """
    art = {
        "schema_version": FISHER_SCHEMA_VERSION,
        "fisher": fisher,
        "fisher_meta": fisher_meta,
        "anchor_fingerprint": anchor_fingerprint,
    }
    torch.save(art, path)
    return art


def load_fisher(path, *, expected_fingerprint=None, map_location="cpu") -> dict:
    """Load the Fisher cache under the locked safe-load bar (EWC-01 / T-10-06).

    ``weights_only=True`` is the restricted unpickler — tensors + primitive containers only,
    ZERO code execution on load. Every cache consumer (Phase 12 lambda sweep, Phase 13 A/B
    arms, tests) goes through this SINGLE choke point — verbatim ``load_adapter`` discipline:
    schema gate FIRST, then structural missing-key validation, then the fingerprint check.

    Fingerprint semantics differ from ``load_adapter`` ON PURPOSE: a Fisher estimated at
    different weights is mathematically WRONG for this anchor (the penalty's importance
    weights would not describe the loaded base), so a mismatching ``expected_fingerprint``
    raises ``ValueError`` instead of warning — re-estimation costs under a minute via
    ``scripts/estimate_fisher_tinystories.py``, so a hard error is cheap and safe.
    """
    loaded = torch.load(path, map_location=map_location, weights_only=True)
    if loaded.get("schema_version") != FISHER_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported fisher schema_version {loaded.get('schema_version')!r} in "
            f"{path} (expected {FISHER_SCHEMA_VERSION}). Re-export with "
            "personacore.checkpoint.export_fisher."
        )
    missing = {"fisher", "fisher_meta", "anchor_fingerprint"} - loaded.keys()
    if missing:
        raise ValueError(
            f"malformed fisher cache {path}: missing keys {sorted(missing)} "
            "(expected an export_fisher cache file)."
        )
    if expected_fingerprint is not None and loaded["anchor_fingerprint"] != expected_fingerprint:
        raise ValueError(
            f"fisher cache anchor fingerprint mismatch: cache carries "
            f"{loaded['anchor_fingerprint']!r} but the loaded anchor is "
            f"{expected_fingerprint!r} — a Fisher estimated at different weights is wrong "
            "for this anchor. Delete the cache and re-run "
            "scripts/estimate_fisher_tinystories.py."
        )
    return loaded
