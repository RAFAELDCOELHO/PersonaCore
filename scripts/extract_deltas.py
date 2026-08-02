"""Phase-15 norms extraction: the ONLY code that reads a checkpoint (VIZ-02 / VIZ-03, D-05..D-08).

Computes the relative Frobenius change ``‖ΔW‖_F/‖W₀‖_F`` on the 6-layer x 6-projection grid for
the persona adapter and for both Phase-13 full-fine-tune arms, aggregates the Fisher diagonal on
the same grid, and writes ``results/phase15_norms.json`` — the D-05/D-07 hand-off boundary. Every
downstream consumer (both figures, the D-09 correlation verdict, the report's per-layer
disclosure) reads that committed JSON and NEVER a checkpoint, which is what makes the figures
provably regenerable from the repo alone.

  6 checkpoints (gitignored, ~914 MB)  ->  results/phase15_norms.json (committed, ~100 scalars)
                                       ->  scripts/plot_phase15.py  (figures)
                                       ->  scripts/phase15_stats.py (the pre-registered verdict)

**The six checkpoints, and which is W₀ for which block** (D-08's "name the actual driver" rule —
CONTEXT D-08 lists five; there are six, and the sixth is the load-bearing one):

  - ``checkpoints/persona_adapter.pt``       — the SHIPPABLE persona adapter; ΔW for the
    ``adapter`` block is ``scale * (lora_B @ lora_A)`` (teach_persona.py:194 names this, not
    ``phase14_real_adapter.pt``, as the shippable path).
  - ``checkpoints/convbase_best.pt``         — **W₀ for the ``adapter`` block.** The adapter's
    ``base_fingerprint`` matches this file exactly (``04e724c6…`` / step 4000 / val_loss
    1.5235939979553224) and does NOT match ``best.pt``. Using ``best.pt`` here would produce a
    wrong-by-construction ratio that still renders and still looks plausible.
  - ``checkpoints/best.pt``                  — **W₀ for the ``naive`` and ``ewc`` blocks**, and the
    anchor whose fingerprint pins the Fisher cache. ``finetune_ab.py:58,208`` runs each A/B arm
    fresh from this file.
  - ``checkpoints/phase13_naive_latest.pt``  — the λ=0 arm's end-of-run weights (``naive`` block).
  - ``checkpoints/phase13_ewc_latest.pt``    — the λ=0.01 EWC arm's end-of-run weights (``ewc``).
  - ``checkpoints/fisher_tinystories.pt``    — the N=2000 mean-normalized Fisher cache estimated
    AT ``best.pt`` (``fisher`` block).

**D-08 — extraction is NOT permanently tested in CI, on purpose.** The six checkpoints are
gitignored (~914 MB) and the suite is CPU-only, so the permanent tests cover the artifact→figure
path only. Re-running extraction against a FUTURE checkpoint requires a fresh MANUAL run producing
a fresh COMMITTED artifact — not a test that silently stays green while checking nothing. The
optional ``skipif``-gated reproduction test in ``tests/test_phase15_plots.py`` re-verifies the
committed JSON byte-for-byte when the checkpoints happen to be present locally.

SECURITY: ``torch.load(weights_only=False)`` here reads ONLY this project's OWN trusted
checkpoints at hardcoded ``_REPO_ROOT``-relative paths — never a foreign file, never a path from
``argv``, never a path from an environment variable. The full resume checkpoints (``best.pt``,
``convbase_best.pt``, ``phase13_naive_latest.pt``, ``phase13_ewc_latest.pt``) carry pickled
optimizer/RNG/numpy objects that torch>=2.6's ``weights_only=True`` default rejects, which is the
same posture ``finetune_ab.py:20-25`` and ``teach_persona.py:32-39`` already record. The adapter
and the Fisher cache go through the ``weights_only=True`` ``load_adapter`` / ``load_fisher`` choke
points instead. The full-resume loader in ``personacore.checkpoint`` is deliberately NOT used
anywhere here: it RESTORES global RNG state as a side effect (``checkpoint.py:138-143``) and this
script wants weights only.

Every proof check below is an explicit ``raise SystemExit`` and never an ``-O``-strippable bare
``assert``, so a failure exits non-zero even under ``PYTHONOPTIMIZE``.

Run: ``python scripts/extract_deltas.py`` (inside the Python 3.11 venv, on the M3).
"""

import json
import pathlib
import time

import numpy as np
import torch

from personacore.checkpoint import load_adapter, load_fisher
from personacore.provenance import git_sha

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PERSONA_ADAPTER = _REPO_ROOT / "checkpoints" / "persona_adapter.pt"  # shippable adapter (VIZ-02)
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # W0 for the adapter block ONLY
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # W0 for naive/ewc; the Fisher anchor
NAIVE_LATEST = _REPO_ROOT / "checkpoints" / "phase13_naive_latest.pt"  # lambda=0 arm, step 4000
EWC_LATEST = _REPO_ROOT / "checkpoints" / "phase13_ewc_latest.pt"  # lambda=0.01 arm, step 4000
FISHER_CACHE = _REPO_ROOT / "checkpoints" / "fisher_tinystories.pt"  # N=2000 cache at best.pt
NORMS_JSON = _REPO_ROOT / "results" / "phase15_norms.json"  # the committed D-05 hand-off boundary

# ===== The 36-key allowlist =====
#
# Copied verbatim from src/personacore/lora/config.py:16 (TARGET_PROJECTIONS) so the column order
# matches scripts/phase15_stats.py::PROJECTIONS exactly — that spelling is PINNED by the
# pre-registration commit and cannot be repaired downstream.
PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")
N_LAYER = 6  # src/personacore/config.py:89 — ModelConfig.n_layer
N_CELLS = N_LAYER * len(PROJECTIONS)

# (projection name) -> the attribute path inside a Block (gpt.py:136,138).
_PROJ_PATHS = {
    "q_proj": "attn.q_proj",
    "k_proj": "attn.k_proj",
    "v_proj": "attn.v_proj",
    "c_proj": "attn.c_proj",
    "fc_in": "mlp.fc_in",
    "fc_out": "mlp.fc_out",
}

# Exactly 36 (layer, projection, state_dict_key) triples from an EXPLICIT product — never an
# isinstance scan and never a substring match (inject.py:38's "explicit allowlist — NEVER an
# isinstance scan (P1)"). WEIGHTS ONLY, never biases: LoRA wraps only `.weight`, so including
# `.bias` in the full-fine-tune deltas would break the like-for-like the figure asserts.
KEYS = [
    (layer, projection, f"blocks.{layer}.{_PROJ_PATHS[projection]}.weight")
    for layer in range(N_LAYER)
    for projection in PROJECTIONS
]

# Fisher cells are reduced by MEAN, recorded in the artifact so the choice lives in the data. The
# cache is mean-normalized (fisher.py:14-16 — "mean(F) = 1 … stiffness relative to an average
# parameter"), so a per-cell mean reads directly as "x the importance of an average parameter". A
# SUM would confound importance with tensor size: fc_in/fc_out carry 4x the elements of the
# attention projections.
FISHER_AGGREGATE = "mean"

ADAPTER_PARAMS = 331_776  # 6 layers x (4 x 6144 + 2 x 15360) at r=8 — the LoRA A/B tensors only
FULL_MODEL_PARAMS = 13_891_584  # every parameter of the 6-layer GPT the full fine-tunes moved

_COMPARISON_NOTE = (
    "naive and ewc share a comparison basis (same W0 = checkpoints/best.pt, same 4000-step "
    "budget, same config, one bit apart) and MAY be compared cell-for-cell. The adapter block "
    "MAY NOT be compared against either full-fine-tune block. Three concrete confounds, not "
    "'different regimes': (1) parameter count — 331776 LoRA parameters vs 13891584 full-model "
    "parameters; (2) training budget — the 200-step LoRA teaching run vs the 4000-step full "
    "fine-tune; (3) a smaller absolute delta-W magnitude for the adapter does NOT imply more "
    "conservative or less effective learning — it reflects the adapter's parameter budget, not a "
    "quality comparison."
)


def _rel(path):
    """Repo-relative POSIX path — the artifact must not leak an absolute local path."""
    return path.relative_to(_REPO_ROOT).as_posix()


def _fingerprint(blob):
    """The QA-02 provenance trio a full checkpoint carries (finetune_ab.py:221)."""
    return {"git_sha": blob["git_sha"], "step": blob["step"], "val_loss": blob["val_loss"]}


def _load_model(path):
    """Read one full resume checkpoint's weights, with NO RNG side effects.

    SECURITY: weights_only=False is a TRUSTED-ONLY read of this project's OWN checkpoint at a
    hardcoded path (see the module SECURITY paragraph). ``map_location="cpu"`` is mandatory — it
    removes MPS reduction-order variance and is what makes the byte-for-byte reproduction test
    viable. The package's full-resume loader is NOT used: it restores global RNG state as a side
    effect (checkpoint.py:138-143), and this script wants weights only.
    """
    blob = torch.load(path, map_location="cpu", weights_only=False)
    return blob["model"], _fingerprint(blob)


def require_fingerprint(adapter_art, w0_blob_fingerprint):
    """The single most important check in this script — VIZ-02's W₀ must be the RIGHT base model.

    ``load_adapter`` only WARNS on a fingerprint mismatch (checkpoint.py:252-259) because the base
    evolves mid-milestone and a hard error would brick every adapter at each base re-export. A
    COMMITTED FIGURE cannot afford a warning: a wrong denominator still renders and still looks
    plausible. Explicit ``raise SystemExit``, never a bare ``assert``.
    """
    want = adapter_art["base_fingerprint"]
    if want != w0_blob_fingerprint:
        raise SystemExit(
            f"[extract_deltas] adapter base fingerprint {want!r} does not match "
            f"{CONVBASE_BEST} ({w0_blob_fingerprint!r}). VIZ-02's ‖W₀‖_F denominator would "
            "describe the WRONG base model — the ratio would still render and still look "
            "plausible. load_adapter only WARNS on this (checkpoint.py:252-259, D-02: the base "
            "evolves mid-milestone); a committed figure cannot afford a warning. Do NOT switch "
            "W₀ to checkpoints/best.pt to make this pass."
        )


def _ratio(dw, w0):
    """``‖ΔW‖_F / ‖W₀‖_F`` in fp64 — statistics domain, the continual/fisher.py discipline."""
    return float(torch.linalg.norm(dw) / torch.linalg.norm(w0))


def adapter_cells(adapter, scale, w0_model):
    """ΔW = ``scale * (lora_B @ lora_A)``; ``scale`` is alpha/r READ FROM THE ARTIFACT.

    ``layer.py:27`` names ``self.scale`` the single source of truth for alpha/r and forbids
    recomputing it (PITFALLS P3); ``inject.py:258`` does the same fold. Shape sanity:
    ``(out, r) @ (r, in) == (out, in)`` — identical to ``base.weight`` (layer.py:51).
    """
    out = {}
    for layer, projection, key in KEYS:
        prefix = key[: -len(".weight")]
        a = adapter[f"{prefix}.lora_A"].to(torch.float64)  # (r, in)
        b = adapter[f"{prefix}.lora_B"].to(torch.float64)  # (out, r)
        out[(layer, projection)] = _ratio(scale * (b @ a), w0_model[key].to(torch.float64))
    return out


def full_ft_cells(arm_model, w0_model):
    """ΔW = arm weights minus W₀, per (layer, projection). Weights only, never biases."""
    out = {}
    for layer, projection, key in KEYS:
        w0 = w0_model[key].to(torch.float64)
        out[(layer, projection)] = _ratio(arm_model[key].to(torch.float64) - w0, w0)
    return out


def fisher_cells(fisher):
    """Per-cell MEAN of the mean-normalized Fisher diagonal (see FISHER_AGGREGATE)."""
    out = {}
    for layer, projection, key in KEYS:
        out[(layer, projection)] = float(fisher[key].to(torch.float64).mean())
    return out


def _grid(cells):
    """The (N_LAYER, len(PROJECTIONS)) fp64 array in the PINNED row/column order."""
    return np.array(
        [[cells[(layer, projection)] for projection in PROJECTIONS] for layer in range(N_LAYER)],
        dtype=np.float64,
    )


def _nested(cells):
    """``{"0".."5": {projection: float}}`` — the spelling pinned by phase15_stats.load_pairs."""
    return {
        str(layer): {projection: cells[(layer, projection)] for projection in PROJECTIONS}
        for layer in range(N_LAYER)
    }


def _vmax_driver(cells):
    """D-02/D-18's outlier disclosure, computed ONCE here.

    Deriving it here rather than re-deriving it in the caption (Plan 15-03) and again in the
    report (Plan 15-05) is what closes D-04's "different amounts, never different things"
    STRUCTURALLY instead of by proofreading.
    """
    grid = _grid(cells)
    row, col = np.unravel_index(int(np.argmax(grid)), grid.shape)
    return {"layer": int(row), "projection": PROJECTIONS[col], "value": float(grid[row, col])}


def _nonpositive_cells(cells):
    """Count of cells <= 0.

    ``LogNorm(0.0)`` returns ``masked`` and does NOT raise, so a zero cell would silently vanish
    from the figure. The report states "N non-positive cells" from THIS field rather than letting
    the figure imply it.
    """
    return int(sum(1 for value in cells.values() if value <= 0.0))


def _block(cells, *, regime, param_count, training_budget, source_ckpt, w0_source, **extra):
    """One artifact block. EVERY block — including fisher — carries the D-06 confound fields, so
    a reader parsing any single block in isolation still sees what it can be compared against."""
    return {
        "regime": regime,
        "param_count": param_count,
        "training_budget": training_budget,
        "source_ckpt": source_ckpt,
        "w0_source": w0_source,
        **extra,
        "cells": _nested(cells),
        "vmax_driver": _vmax_driver(cells),
        "nonpositive_cells": _nonpositive_cells(cells),
    }


def build_artifact():
    """Read the six checkpoints and return the complete artifact dict (proofs run in ``main``)."""
    for path in (
        PERSONA_ADAPTER,
        CONVBASE_BEST,
        BEST_PATH,
        NAIVE_LATEST,
        EWC_LATEST,
        FISHER_CACHE,
    ):
        if not path.exists():
            raise SystemExit(
                f"[extract_deltas] missing checkpoint {path} — extraction reads all six frozen "
                "checkpoints and cannot run without it. These files are gitignored (~914 MB); "
                "extraction is a local-only manual run, never a CI step."
            )

    convbase_model, convbase_fp = _load_model(CONVBASE_BEST)
    best_model, best_fp = _load_model(BEST_PATH)
    naive_model, naive_fp = _load_model(NAIVE_LATEST)
    ewc_model, ewc_fp = _load_model(EWC_LATEST)

    # weights_only=True choke point; the fingerprint check below is ours, not load_adapter's.
    adapter_art = load_adapter(PERSONA_ADAPTER)
    require_fingerprint(adapter_art, convbase_fp)
    adapter = adapter_art["adapter"]
    if len(adapter) != 2 * N_CELLS:
        raise SystemExit(
            f"[extract_deltas] {PERSONA_ADAPTER} carries {len(adapter)} adapter tensors, "
            f"expected {2 * N_CELLS} ({N_CELLS} lora_A/lora_B pairs). The artifact does not "
            "describe a 6-layer x 6-projection injection."
        )
    lora_config = adapter_art["lora_config"]
    # scale = alpha/r read FROM THE ARTIFACT and never recomputed elsewhere (layer.py:27, P3).
    scale = lora_config["alpha"] / lora_config["r"]

    # load_fisher RAISES (not warns) on an anchor-fingerprint mismatch — that is the desired
    # behavior: a Fisher estimated at different weights is wrong for this anchor.
    cache = load_fisher(FISHER_CACHE, expected_fingerprint=best_fp)
    fisher, fisher_meta = cache["fisher"], cache["fisher_meta"]

    blocks = {
        "adapter": _block(
            adapter_cells(adapter, scale, convbase_model),
            regime="lora_adapter_teaching_run",
            param_count=ADAPTER_PARAMS,
            training_budget=(
                "200 steps, batch 8 x block 256, LoRA r=8 alpha=16 on the frozen conversational "
                "base (scripts/teach_persona.py real arm)"
            ),
            source_ckpt={"path": _rel(PERSONA_ADAPTER), "base_fingerprint": convbase_fp},
            w0_source=_rel(CONVBASE_BEST),
            lora_r=lora_config["r"],
            lora_alpha=lora_config["alpha"],
            lora_scale=scale,
        ),
        "naive": _block(
            full_ft_cells(naive_model, best_model),
            regime="full_finetune_naive",
            param_count=FULL_MODEL_PARAMS,
            training_budget=(
                "4000 steps, batch 32 x block 256, LR 9e-5, lambda=0 "
                "(scripts/finetune_ab.py naive arm)"
            ),
            source_ckpt={"path": _rel(NAIVE_LATEST), "fingerprint": naive_fp},
            w0_source=_rel(BEST_PATH),
            w0_fingerprint=best_fp,
        ),
        "ewc": _block(
            full_ft_cells(ewc_model, best_model),
            regime="full_finetune_ewc_lambda_0.01",
            param_count=FULL_MODEL_PARAMS,
            training_budget=(
                "4000 steps, batch 32 x block 256, LR 9e-5, lambda=0.01 "
                "(scripts/finetune_ab.py ewc arm)"
            ),
            source_ckpt={"path": _rel(EWC_LATEST), "fingerprint": ewc_fp},
            w0_source=_rel(BEST_PATH),
            w0_fingerprint=best_fp,
        ),
        "fisher": _block(
            fisher_cells(fisher),
            regime="fisher_diagonal_estimate",
            param_count=FULL_MODEL_PARAMS,
            training_budget=(
                "no training — one estimation pass of 2000 examples at checkpoints/best.pt "
                "(scripts/estimate_fisher_tinystories.py)"
            ),
            source_ckpt={"path": _rel(FISHER_CACHE), "anchor_fingerprint": best_fp},
            w0_source=None,
            # SC3's named Fisher variant, carried OUT of the cache and INTO the artifact: the
            # coarse `regime` says which family, `variant` says which estimator, from which
            # targets, under which normalization. That is the claim a reader can check.
            variant=fisher_meta["variant"],
            n_examples=fisher_meta["n_examples"],
            seed=fisher_meta["seed"],
        ),
    }

    return {
        "git_sha": git_sha(),
        "built": time.strftime("%Y-%m-%d", time.gmtime()),
        "n_layer": N_LAYER,
        "projections": list(PROJECTIONS),
        "quantity": "relative_frobenius_change",
        "quantity_note": (
            "Each adapter/naive/ewc cell is ‖ΔW‖_F/‖W₀‖_F for that (layer, projection) `.weight` "
            "tensor, computed in fp64 on CPU. Weights only, never biases — LoRA wraps only "
            "`.weight`, so including `.bias` in the full-fine-tune deltas would break the "
            "like-for-like the figures assert. Fisher cells are a magnitude, not a ratio."
        ),
        "fisher_aggregate": FISHER_AGGREGATE,
        "fisher_aggregate_note": (
            "The Fisher cache is mean-normalized (mean(F) = 1 over all trainable coordinates), so "
            "a per-cell mean reads as 'x the importance of an average parameter'. A sum would "
            "confound importance with tensor size — fc_in/fc_out carry 4x the elements of the "
            "attention projections."
        ),
        "comparison_basis": {
            "naive_vs_ewc": True,
            "adapter_vs_full_finetune": False,
            "note": _COMPARISON_NOTE,
        },
        "blocks": blocks,
    }


def prove(artifact):
    """Every structural proof, BEFORE the write (build_retention_bin.py:157-186 ordering).

    Each is an explicit ``raise SystemExit`` naming the specific offender — never a bare
    ``assert``, which ``python -O`` strips.
    """
    blocks = artifact["blocks"]
    for name in ("adapter", "naive", "ewc", "fisher"):
        cells = blocks[name]["cells"]
        total = sum(len(row) for row in cells.values())
        if total != N_CELLS:
            raise SystemExit(
                f"[extract_deltas] block {name!r} carries {total} cells, expected exactly "
                f"{N_CELLS} ({N_LAYER} layers x {len(PROJECTIONS)} projections)."
            )
        for layer in range(N_LAYER):
            row = cells.get(str(layer))
            if row is None or tuple(sorted(row)) != tuple(sorted(PROJECTIONS)):
                raise SystemExit(
                    f"[extract_deltas] block {name!r} layer {layer} has projections "
                    f"{sorted(row) if row else None}, expected {sorted(PROJECTIONS)}."
                )
            for projection, value in row.items():
                if not np.isfinite(value):
                    raise SystemExit(
                        f"[extract_deltas] block {name!r} cell (layer {layer}, {projection}) is "
                        f"{value!r}, not finite — a non-finite cell would poison every "
                        "downstream figure and the correlation."
                    )

    variant = blocks["fisher"].get("variant")
    if not isinstance(variant, str) or not variant:
        raise SystemExit(
            f"[extract_deltas] the fisher block's 'variant' is {variant!r}, not a non-empty "
            "string. ROADMAP SC3 requires the v2.0 narrative to name the exact Fisher estimator "
            "variant, and it must be carried out of the cache's fisher_meta into this artifact."
        )


def main(out_path=None):
    """Build, prove, then write. ``out_path`` lets the reproduction test target ``tmp_path``."""
    out_path = pathlib.Path(out_path) if out_path is not None else NORMS_JSON
    artifact = build_artifact()
    prove(artifact)
    # The writer is PINNED (build_retention_bin.py:180-182): indent=2, NO key re-sorting —
    # insertion order IS the pinned order — plus an explicit trailing newline. Any deviation makes
    # the D-08 byte-for-byte reproduction test untestable.
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(artifact, fh, indent=2)
        fh.write("\n")
    print(f"[extract_deltas] wrote {out_path}")
    return out_path


if __name__ == "__main__":
    main()
