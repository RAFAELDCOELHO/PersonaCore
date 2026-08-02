"""Phase-15 figure generation: VIZ-02 adapter weight-delta heatmap + VIZ-03 Fisher/Δ triptych.

Pure ``json`` + ``numpy`` + ``matplotlib`` — no torch, no checkpoints, no serialized-weight file
of any kind. Every number comes from the COMMITTED ``results/phase15_norms.json``, so both
figures regenerate deterministically from the repo alone. That sentence is not a convention:
D-07 converts it into a test — ``tests/test_phase15_plots.py``'s
``test_plotting_module_never_opens_a_checkpoint`` —
which parses this module's AST (no torch import, no serialized-weight filename literal) and
re-imports it in a FRESH interpreter to prove torch never even transitively enters
``sys.modules``. A future edit that "temporarily" reads a checkpoint to fill one missing field
turns red, because a committed PNG that derives from a gitignored 278 MB checkpoint is not
regenerable from a clone and the regenerability claim would quietly become false.

  VIZ-02 → results/phase15_adapter_delta.png — relative Frobenius change ‖ΔW‖_F/‖W₀‖_F for the
           persona LoRA adapter on the 6-layer x 6-projection grid, log color scale.
  VIZ-03 → results/phase15_fisher_ewc.png — naive Δ, EWC Δ and the Fisher diagonal, same grid.

Constraints honored, all from ``.planning/phases/15-figures-writeup/15-CONTEXT.md``:
  D-01 — the naive and EWC panels take ONE ``LogNorm`` object under ONE colorbar. If that makes
         the EWC panel look flat, the flatness IS the finding and is reported, never rescaled
         away. The Fisher panel gets its own norm on a UNITS argument (squared-gradient
         magnitude is not commensurable with a weight-delta ratio) — a units exemption, not a
         convenience one, and it extends to nothing else.
  D-02 — the shared range is the FULL data range: vmax = the largest cell across both arms,
         vmin = the smallest strictly positive cell across both. No percentile clipping at
         either end; under D-01 compression is data.
  D-04 — terse disclosure on the figure itself, so the PNG cannot be misread when it travels
         alone into a slide; the full reasoning lives in the report. Both read the artifact's
         ``vmax_driver`` field rather than each computing its own, so they can differ in amount
         but never in substance.
  D-07 — artifact in, figure out. Nothing here opens a checkpoint.

Run: ``python scripts/plot_phase15.py`` (inside the Python 3.11 venv). Headless — the figures
are written with ``savefig``; nothing here opens a window.
"""

import json
import pathlib

import matplotlib
import numpy as np

# Agg BEFORE pyplot: this script only ever writes files, so it must not need a GUI backend
# (it runs from a plain venv shell and from the tmp_path smoke test).
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend selection above)
from matplotlib.colors import LogNorm  # noqa: E402  (same reason)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_DIR = _REPO_ROOT / "results"  # git-TRACKED output, alongside the phase-13 figures
NORMS_JSON = RESULTS_DIR / "phase15_norms.json"  # the D-05 artifact — the ONLY input

# Every block the two figures draw. Named explicitly so a truncated artifact fails by name
# rather than rendering three panels and one blank one.
REQUIRED_BLOCKS = ("adapter", "naive", "ewc", "fisher")

QUANTITY_LABEL = "‖ΔW‖_F/‖W₀‖_F  (log scale)"
FISHER_LABEL = "mean Fisher diagonal, x an average parameter  (log scale)"
ARTIFACT_POINTER = "full per-layer table in results/phase15_norms.json"

DPI = 150
DISCLOSURE_FONTSIZE = 8  # the D-04 terse line: readable, never competing with the data
TICK_FONTSIZE = 9


def _load_artifact(path=NORMS_JSON):
    """The committed D-05 artifact, validated on the way in. Never degrades silently.

    A missing block, a short grid or a renamed projection would each render a panel that looks
    plausible and describes nothing — the ``plot_phase13.py:88-97`` hazard in its Phase-15 form.
    An empty panel under a titled axis is a figure that lies, so every failure below names the
    offending file and the offending block/layer and raises rather than plotting.
    """
    if not path.exists():
        raise SystemExit(
            f"{path}: missing. This script reads ONLY that artifact (D-07). Regenerate it with "
            "`python scripts/extract_deltas.py` on a machine holding the frozen checkpoints, "
            "then re-run this script."
        )

    artifact = json.loads(path.read_text(encoding="utf-8"))
    projections = artifact.get("projections")
    n_layer = artifact.get("n_layer")
    if not projections or not isinstance(n_layer, int) or n_layer <= 0:
        raise ValueError(f"{path}: no usable 'projections'/'n_layer' — not a Phase-15 artifact")
    expected_cells = n_layer * len(projections)

    blocks = artifact.get("blocks") or {}
    for name in REQUIRED_BLOCKS:
        block = blocks.get(name)
        if block is None:
            raise ValueError(f"{path}: block {name!r} is absent; blocks are {sorted(blocks)}")

        cells = block.get("cells") or {}
        total = sum(len(row) for row in cells.values())
        if total != expected_cells:
            raise ValueError(
                f"{path}: block {name!r} carries {total} cells, expected {expected_cells} "
                f"({n_layer} layers x {len(projections)} projections)"
            )
        for layer in range(n_layer):
            row = cells.get(str(layer))
            if row is None:
                raise ValueError(f"{path}: block {name!r} has no layer {layer}")
            if sorted(row) != sorted(projections):
                raise ValueError(
                    f"{path}: block {name!r} layer {layer} covers {sorted(row)}, "
                    f"expected {sorted(projections)}"
                )

        # The D-02/D-18 disclosure is READ from here, never recomputed in a caption (D-04).
        if not block.get("vmax_driver"):
            raise ValueError(f"{path}: block {name!r} has no 'vmax_driver' to disclose")

    return artifact


def _grid(artifact, block):
    """The block's ``(n_layer, n_projection)`` fp64 grid — layer rows, ``projections`` columns.

    The column order is the artifact's own ``projections`` list and the row order is 0..n-1,
    which is exactly the order ``scripts/phase15_stats.py::load_pairs`` flattens: the figure and
    the statistic must describe the same cells or the correlation stops describing the picture.
    """
    cells = artifact["blocks"][block]["cells"]
    return np.array(
        [
            [float(cells[str(layer)][projection]) for projection in artifact["projections"]]
            for layer in range(artifact["n_layer"])
        ],
        dtype=np.float64,
    )


def _own_norm(values, label):
    """A ``LogNorm`` over ``values``' full range — vmin is the smallest STRICTLY POSITIVE cell.

    A log scale needs a positive floor; zero and negative cells are masked by ``LogNorm`` rather
    than raising, which is why ``_cmap`` paints them instead of leaving a hole.
    """
    flat = np.asarray(values, dtype=np.float64).ravel()
    positive = flat[flat > 0.0]
    if positive.size == 0:
        raise ValueError(f"{label}: every cell is non-positive — a log scale has no floor here")
    return LogNorm(vmin=float(positive.min()), vmax=float(flat.max()))


def _shared_norm(naive, ewc):
    """D-01/D-02: ONE norm object spanning BOTH arms, over their full combined data range.

    No percentile clipping at either end. Under D-01 the compression a shared scale produces is
    the result — EWC constraining movement in absolute terms — and clipping it away would edit
    the finding out of the figure.
    """
    return _own_norm(np.concatenate([naive.ravel(), ewc.ravel()]), "naive+ewc")


def _norms(artifact):
    """The three norm objects ``plot_fisher_ewc`` hands to ``imshow``: (naive, ewc, fisher).

    The first two are the SAME object, not two objects with equal bounds — which is why the
    D-01 test can assert ``naive_norm is ewc_norm``. A value comparison would also pass for an
    implementation that built one norm per panel and happened to compute matching limits, and
    that implementation is precisely the one a later "just tweak this panel" edit turns into two
    different scales. ``plot_fisher_ewc`` obtains its norms here and passes them through
    untouched, so this helper cannot drift from what is actually drawn.
    """
    shared = _shared_norm(_grid(artifact, "naive"), _grid(artifact, "ewc"))
    fisher = _own_norm(_grid(artifact, "fisher"), "fisher")
    return shared, shared, fisher


def _cmap(name="magma"):
    """A copy of ``name`` whose masked cells are visible grey rather than a transparent hole.

    ``LogNorm(...)(0.0)`` returns ``masked`` and does NOT raise, so without ``set_bad`` a zero
    cell renders as nothing at all — indistinguishable from missing data. All four blocks
    currently report zero non-positive cells; the report states that from the artifact's count,
    not from the figure appearing to have none.
    """
    cmap = plt.get_cmap(name).copy()
    cmap.set_bad(color="0.85")
    return cmap


def _annotate_axes(ax, projections, n_layer):
    """Layer index rows, projection-name columns — so a reader can find the driver cell by eye."""
    ax.set_xticks(range(len(projections)))
    ax.set_xticklabels(projections, rotation=30, ha="right", fontsize=TICK_FONTSIZE)
    ax.set_yticks(range(n_layer))
    ax.set_yticklabels(range(n_layer), fontsize=TICK_FONTSIZE)
    ax.set_xlabel("projection")
    ax.set_ylabel("transformer block (layer)")


def _driver(block):
    """``"layer N / proj"`` straight from the artifact — caption and report read ONE field."""
    driver = block["vmax_driver"]
    return f"layer {driver['layer']} / {driver['projection']}"


def plot_adapter_delta(out_dir):
    """VIZ-02: the persona adapter's ‖ΔW‖_F/‖W₀‖_F grid, own log scale. Returns the path."""
    artifact = _load_artifact()
    block = artifact["blocks"]["adapter"]
    grid = _grid(artifact, "adapter")

    fig, ax = plt.subplots(figsize=(7.6, 5.6), dpi=DPI)
    im = ax.imshow(grid, cmap=_cmap(), norm=_own_norm(grid, "adapter"), aspect="auto")
    _annotate_axes(ax, artifact["projections"], artifact["n_layer"])
    ax.set_title("VIZ-02 — persona adapter ‖ΔW‖_F/‖W₀‖_F (LoRA teaching run)")
    fig.colorbar(im, ax=ax, label=QUANTITY_LABEL)

    # D-18 + D-04: terse, on the figure, and every fact in it is READ from the artifact — the
    # driver cell from `vmax_driver`, the parameter budget from `param_count`. The report
    # carries the full three-confound version (D-03); this line only has to stop the
    # figure-travels-alone misreading, which is the adapter-vs-full-fine-tune comparison the
    # shared formula invites and D-03 forbids.
    fig.text(
        0.5,
        0.005,
        f"color range driven by {_driver(block)} — {block['param_count']:,} LoRA parameters over "
        "a different training budget than the full fine-tune,\nso this figure is NOT comparable "
        f"to the VIZ-03 delta panels — {ARTIFACT_POINTER}",
        ha="center",
        fontsize=DISCLOSURE_FONTSIZE,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.09, 1, 1))

    out_path = pathlib.Path(out_dir) / "phase15_adapter_delta.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_fisher_ewc(out_dir):
    """VIZ-03: naive Δ and EWC Δ under ONE shared norm, plus the Fisher diagonal on its own.

    The signed ``naiveΔ − ewcΔ`` reduction is deliberately NOT a panel here: it is the D-10
    statistic's input, it can legitimately be negative where EWC moved further than naive, and a
    log norm would mask exactly those cells. It belongs in the correlation, not on a log axis.
    """
    artifact = _load_artifact()
    naive_norm, ewc_norm, fisher_norm = _norms(artifact)
    naive, ewc, fisher = (_grid(artifact, name) for name in ("naive", "ewc", "fisher"))

    fig, (ax_naive, ax_ewc, ax_fisher) = plt.subplots(1, 3, figsize=(15, 5.0), dpi=DPI)
    # Explicit margins rather than tight_layout: the shared colorbar below spans TWO axes, and
    # a colorbar made from an axes LIST is not something tight_layout can place. The colorbars
    # are created after this call so they steal space from the final axes positions.
    fig.subplots_adjust(left=0.05, right=0.97, bottom=0.27, top=0.86, wspace=0.4)

    delta_cmap = _cmap()
    im_naive = ax_naive.imshow(naive, cmap=delta_cmap, norm=naive_norm, aspect="auto")
    ax_ewc.imshow(ewc, cmap=delta_cmap, norm=ewc_norm, aspect="auto")
    im_fisher = ax_fisher.imshow(fisher, cmap=_cmap("viridis"), norm=fisher_norm, aspect="auto")

    ax_naive.set_title("naive Δ (λ=0)")
    ax_ewc.set_title("EWC Δ (λ=0.01) — same scale")
    ax_fisher.set_title("Fisher diagonal (own scale — different units)")
    for ax in (ax_naive, ax_ewc, ax_fisher):
        _annotate_axes(ax, artifact["projections"], artifact["n_layer"])

    # ONE colorbar across both delta panels: the D-01 shared scale rendered visibly as shared,
    # so a reader never has to check two colorbars to learn they match.
    fig.colorbar(im_naive, ax=[ax_naive, ax_ewc], label=QUANTITY_LABEL)
    fig.colorbar(im_fisher, ax=ax_fisher, label=FISHER_LABEL)

    fig.suptitle(
        "VIZ-03 — where the full fine-tune moved, and where the Fisher diagonal said not to"
    )

    # D-04 terse disclosure. The shared vmax driver is whichever ARM's recorded `vmax_driver`
    # holds the larger value — read from the artifact, not recomputed from the grids, so this
    # caption and the report quote one field. (They are not the same cell: see 15-02-SUMMARY.)
    drivers = [artifact["blocks"][name] for name in ("naive", "ewc")]
    shared_driver = max(drivers, key=lambda block: block["vmax_driver"]["value"])
    fig.text(
        0.5,
        0.03,
        "the naive and EWC panels share ONE log scale and are directly comparable cell-for-cell; "
        "the Fisher panel has its own because its units differ\n"
        f"(squared-gradient magnitude, not a weight-delta ratio) — shared range driven by "
        f"{_driver(shared_driver)}; {ARTIFACT_POINTER}",
        ha="center",
        fontsize=DISCLOSURE_FONTSIZE,
        color="gray",
    )

    out_path = pathlib.Path(out_dir) / "phase15_fisher_ewc.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def main() -> None:
    for out_path in (plot_adapter_delta(RESULTS_DIR), plot_fisher_ewc(RESULTS_DIR)):
        print(f"[plot_phase15] wrote {out_path}")


if __name__ == "__main__":
    main()
