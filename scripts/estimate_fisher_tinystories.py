"""Real-weights Fisher run: best.pt + TinyStories train.bin -> fisher_tinystories.pt (EWC-01).

The real-weights half of roadmap success criterion 1: the CPU unit tests (``tests/test_fisher.py``
/ ``tests/test_fisher_checkpoint.py``) pin the math and the persistence contracts on tiny
fixtures; THIS script is where the Fisher is ACTUALLY estimated at the 13.9M ``best.pt`` anchor
over real TinyStories windows — D-04's production budget (``N_EXAMPLES = 2000``), with D-05
convergence evidence (half-split Spearman + relative mean changes) REPORTED, not gated: "N is
enough" is a measured claim. The script IS the proof: every proof check is an explicit
``raise SystemExit`` (never a ``-O``-strippable ``assert``), so any failure exits non-zero even
under ``python -O`` / ``PYTHONOPTIMIZE`` (09-RESEARCH Open Q2 precedent).

Writes the production cache ``checkpoints/fisher_tinystories.pt`` that Phase 12's lambda sweep
and Phase 13's A/B arms BOTH consume — one estimation pass, two arms. The cache meets the
``weights_only=True`` safe-load bar via ``export_fisher`` (tensors + primitives, schema-versioned,
anchor-fingerprinted; NO theta_star — recoverable from ``best.pt``, which the fingerprint pins).
Refuse-to-rerun semantics (RESEARCH Open Q3 resolution): an existing cache makes the script exit
loudly instead of silently re-estimating, keeping cache provenance stable for Phases 12/13 —
delete the cache to re-estimate.

Mirrors ``scripts/train_adapter_smoke.py`` (thin no-CLI driver, logic lives in the package):
``_REPO_ROOT`` path constants, named tuned constants, ``preflight_device(strict=True)`` gate,
trusted ``weights_only=False`` anchor load, ``[estimate_fisher_tinystories]``-prefixed prints.
All outputs land in the gitignored ``checkpoints/`` — weight-derived artifacts are never
committed (T-10-07).

Run: ``python scripts/estimate_fisher_tinystories.py`` (inside the Python 3.11 venv).
"""

import math
import os
import pathlib
import time

import numpy as np

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.checkpoint import export_fisher  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.continual import EWCPenalty, estimate_fisher  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted anchor checkpoint (gitignored)
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"  # LOCAL memmap corpus
FISHER_CACHE = _REPO_ROOT / "checkpoints" / "fisher_tinystories.pt"  # production cache (gitignored)

# --- Tuned constants (production estimation budget — prove the Fisher on real weights) ---
N_EXAMPLES = 2000  # D-04: measured < 1 min on MPS at 18.6 ms/example; convergence reported (D-05).
SEED = 1234  # local np.random.default_rng seed — global RNG streams stay untouched (Pitfall 3).
EWC_LAMBDA = 1.0  # Phase-10 placeholder convention — the real lambda is Phase 12's sweep (EWC-03).


def main() -> None:
    t0 = time.monotonic()

    # Gate on a usable device (CUDA-P100 -> MPS -> CPU raise) BEFORE the run (pretrain precedent).
    summary = preflight_device(strict=True)
    print(f"[estimate_fisher_tinystories] preflight: {summary}")

    if not BEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
        )
    if not TRAIN_BIN.exists():
        raise FileNotFoundError(
            f"Missing local corpus memmap: {TRAIN_BIN}. "
            "Run `python scripts/pretrain_tinystories.py` prerequisites (encode the corpus) first."
        )

    # Refuse-to-rerun (RESEARCH Open Q3): a fresh estimate would silently change the cache
    # provenance Phases 12/13 share. Re-estimation must be an explicit, visible decision.
    if FISHER_CACHE.exists():
        raise SystemExit(
            f"[estimate_fisher_tinystories] {FISHER_CACHE} already exists — refusing to "
            "overwrite the shared production cache. Delete it to re-estimate."
        )

    runtime = RuntimeConfig()  # resolves the preflighted device (MPS on the M3, fp32, AMP off).

    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy objects.
    # TRUSTED-only read of the project's OWN checkpoint (T-10-05; train_adapter_smoke precedent) —
    # never a foreign file. The SHAREABLE artifact path stays weights_only=True via export_fisher.
    blob = torch.load(BEST_PATH, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])
    model.to(runtime.device)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    print(
        f"[estimate_fisher_tinystories] anchor loaded: step {blob['step']}, "
        f"val_loss {blob['val_loss']}, {n_params / 1e6:.1f}M params on {runtime.device}"
    )

    # theta_star: detached CPU clones snapshot from named_parameters() — the dedup rule
    # (Pattern 3 / Pitfall 1): the tied wte/lm_head storage appears exactly once.
    theta_star = {n: p.detach().clone().cpu() for n, p in model.named_parameters()}

    fisher, meta = estimate_fisher(
        model,
        TRAIN_BIN,
        n_examples=N_EXAMPLES,
        block_size=model_cfg.block_size,
        device=runtime.device,
        seed=SEED,
    )
    print(f"[estimate_fisher_tinystories] estimated Fisher over {N_EXAMPLES} windows")

    # --- PROOF CHECKS: explicit SystemExit, never a -O-strippable assert ---

    # [a] Every Fisher tensor finite and non-negative (EWC-01 / Pitfall 7).
    for name, t in fisher.items():
        if not torch.isfinite(t).all():
            raise SystemExit(f"[proof a] non-finite Fisher entries in {name!r} (Pitfall 7)")
        if not (t >= 0).all():
            raise SystemExit(f"[proof a] negative Fisher entries in {name!r} — g**2 cannot be < 0")

    # [b] Tied-tensor dedup on the REAL model (Pitfall 1): the shared wte/lm_head storage
    # contributes exactly once, under wte.weight — one entry per distinct param storage.
    if "lm_head.weight" in fisher:
        raise SystemExit("[proof b] lm_head.weight in Fisher — tied tensor double-counted (P1)")
    if "wte.weight" not in fisher:
        raise SystemExit("[proof b] wte.weight missing from Fisher — wrong key surface (P1)")
    distinct_storages = len({p.data_ptr() for p in model.parameters()})
    if len(fisher) != distinct_storages:
        raise SystemExit(
            f"[proof b] {len(fisher)} Fisher entries != {distinct_storages} distinct param "
            "storages — dedup broken (Pitfall 1)"
        )

    # [c] Normalization (D-01): global mean of the stored Fisher == 1 within fp32 tolerance,
    # computed in fp64 on CPU (MPS has no fp64 — Pitfall 4); raw normalizer recorded and > 0.
    flat64 = np.concatenate([t.numpy().astype(np.float64).ravel() for t in fisher.values()])
    global_mean = float(flat64.mean())
    if not math.isclose(global_mean, 1.0, rel_tol=0.0, abs_tol=1e-5):
        raise SystemExit(f"[proof c] normalized Fisher global mean {global_mean!r} != 1.0 (D-01)")
    if not meta["normalizer"] > 0.0:
        raise SystemExit(f"[proof c] degenerate raw normalizer {meta['normalizer']!r} (D-01)")

    # [d] Exact zero at the anchor: penalty(theta_star) == 0.0 bitwise, for any lambda/Fisher.
    # Device moves are exact fp32 bit copies, so the CPU model matches the CPU theta_star.
    model.to("cpu")
    penalty = EWCPenalty(fisher, theta_star, EWC_LAMBDA, device="cpu")
    at_anchor = float(penalty(model))
    if at_anchor != 0.0:
        raise SystemExit(f"[proof d] penalty {at_anchor!r} != 0.0 exactly at the anchor (EWC-02)")

    # [e] The penalty sees drift: perturb one parameter slightly -> penalty > 0.
    perturbed = next(model.parameters())
    with torch.no_grad():
        perturbed.add_(1e-3)
    drifted = float(penalty(model))
    with torch.no_grad():
        perturbed.sub_(1e-3)  # restore the anchor weights (hygiene; nothing below uses them).
    if not drifted > 0.0:
        raise SystemExit(f"[proof e] penalty {drifted!r} not > 0 under perturbation (EWC-02)")

    # [f] D-05 convergence evidence — REPORT, do not gate ("N is enough" is a measured claim).
    print(
        f"[estimate_fisher_tinystories] convergence (D-05): "
        f"spearman_half={meta['spearman_half']:.6f}, "
        f"rel_mean_change_a={meta['rel_mean_change_a']:.6f}, "
        f"rel_mean_change_b={meta['rel_mean_change_b']:.6f}"
    )

    # Fingerprint READ from the anchor blob, never recomputed (provenance trio, QA-02).
    export_fisher(
        FISHER_CACHE,
        fisher=fisher,
        fisher_meta=meta,
        anchor_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )

    size_mb = FISHER_CACHE.stat().st_size / 1e6
    wall = time.monotonic() - t0
    print(f"[estimate_fisher_tinystories] wrote {FISHER_CACHE} ({size_mb:.2f} MB)")
    print(
        f"[estimate_fisher_tinystories] normalizer={meta['normalizer']:.6e}, "
        f"spearman_half={meta['spearman_half']:.6f}, "
        f"rel_mean_change_a={meta['rel_mean_change_a']:.6f}, "
        f"rel_mean_change_b={meta['rel_mean_change_b']:.6f}"
    )
    print(f"[estimate_fisher_tinystories] all proof checks passed in {wall:.1f}s wall-clock")


if __name__ == "__main__":
    main()
