"""Thin no-CLI slim-export driver: checkpoints/best.pt -> checkpoints/model_slim.pt (DEMO-02).

Mirrors ``scripts/evaluate.py``: logic lives in ``src/personacore``
(``checkpoint.export_slim``) — this script only wires the trusted ``best.pt`` to the exporter
and prints what shipped. No CLI flag parsing (Phase-1 D-04): all paths are
``_REPO_ROOT``-relative constants. No accelerator preflight gate — the export is a one-shot
local CPU transform, not a training run.

The ``checkpoint.py`` module docstring reserved this split from Phase 1: the slim INFERENCE
checkpoint (Phase 8) uses ``weights_only=True``. ``export_slim`` strips
optimizer/scheduler/scaler/rng/train_config so the shipped file round-trips through the
restricted unpickler with zero code execution on load (T-08-01), while ``model_config`` +
``git_sha`` + ``step`` travel with the weights (QA-02).

SECURITY: the export READS ``best.pt`` with ``torch.load(..., weights_only=False)`` — used
ONLY for the project's OWN trusted checkpoint (T-08-02 / T-07-02 lineage), never a foreign
file. The WRITTEN slim artifact is the one strangers download; it loads safe-by-construction.

Run: ``python scripts/export_slim.py`` (inside the Python 3.11 venv).
"""

import pathlib

from personacore.checkpoint import export_slim

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted shipped checkpoint (gitignored)
SLIM_PATH = _REPO_ROOT / "checkpoints" / "model_slim.pt"  # shippable slim artifact (gitignored)


def main() -> None:
    if not BEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BEST_PATH}. Run `python scripts/pretrain_tinystories.py` first."
        )
    slim = export_slim(BEST_PATH, SLIM_PATH)
    size_mb = SLIM_PATH.stat().st_size / 1e6
    print(f"[export_slim] wrote {SLIM_PATH} ({size_mb:.1f} MB)")
    print(f"[export_slim] keys: {sorted(slim.keys())}")
    print(f"[export_slim] git_sha: {slim['git_sha']}  step: {slim['step']}")


if __name__ == "__main__":
    main()
