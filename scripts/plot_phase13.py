"""Phase-13 figure generation: VIZ-01 forgetting curve + VIZ-04 λ frontier.

Pure ``csv`` + ``matplotlib`` — no torch, no training, no checkpoints. Every number comes
from a COMMITTED artifact (the two arm CSVs and the five λ-sweep CSVs) or from a
hardcoded-with-citation constant, so the figures regenerate deterministically from the repo
alone. Thin no-CLI ``main()`` with ``_REPO_ROOT``-relative constants (Phase-1 D-04).

  VIZ-01 → results/phase13_forgetting_curve.png — retention (forgetting) and dialogue
           (acquisition) PPL vs step for BOTH 4000-step A/B arms.
  VIZ-04 → results/phase13_frontier.png — retention vs dialogue trade-off, one point per λ,
           at the 1250-step sweep endpoints.

The two figures describe DIFFERENT training budgets and must never be read as one series
(RESEARCH Pitfall 4): the arms ran 4000 steps, the λ sweep ran 1250. Both captions say so.

Run: ``python scripts/plot_phase13.py`` (inside the Python 3.11 venv). Headless — the
figures are written with ``savefig``; nothing here calls ``show()``.
"""

import csv
import pathlib

import matplotlib

# Agg BEFORE pyplot: this script only ever writes files, so it must not need a GUI backend
# (it runs from a plain venv shell and from the tmp_path smoke test).
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend selection above)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_DIR = _REPO_ROOT / "results"  # git-TRACKED output, next to the A/B report
NAIVE_CSV = RESULTS_DIR / "phase13_naive" / "run.csv"  # committed 4000-step naive arm
EWC_CSV = RESULTS_DIR / "phase13_ewc" / "run.csv"  # committed 4000-step EWC arm

# Pitfall 3 — the dashed VIZ-01 baseline is the v1.0 HEADLINE retention PPL (full-val,
# unmasked; results/retention_anchors.json "headline_unmasked_fullval"). It is DISTINCT from
# the 2.107553076833866 frozen sub-bin anchor that the curves' own step-0 rows already carry.
# Never substitute one for the other.
HEADLINE_RETENTION = 2.1066

# Pitfall 1 — results/ft_lr_9e-5.csv (the λ=0 sweep arm at the headline LR) has NO
# retention_ppl column, so the collapse baseline CANNOT be read from a CSV. Both values are
# transcribed from results/finetune_smoke_report.md Stage 2/3, locked at commit 666d096.
# Hardcode-with-citation register (finetune_dialog.py:75): this code never parses a report
# at runtime. A naive CSV-only frontier silently plots five points and drops λ=0 entirely.
LAMBDA0_POINT = {"dialog_ppl": 4.4453, "retention_ppl": 5.9553}

SWEEP_LAMBDAS = ("0.01", "0.1", "1", "10", "100")  # results/ft_lam_{λ}.csv, 1250 steps each

# Fixed series order + colors (08-UI-SPEC plot contract): matplotlib default cycle only.
ARMS = (
    ("naive (λ=0)", NAIVE_CSV, "C1"),
    ("EWC (λ=0.01)", EWC_CSV, "C0"),
)
DPI = 150


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _series(rows, column):
    """``(steps, values)`` for the rows carrying a value in ``column``.

    The pre-seeded step-0 row leaves the train-only columns blank (``restval=""``), so an
    unconditional ``float(r[col])`` would raise; the eval columns are populated there.
    """
    pairs = [(int(float(r["step"])), float(r[column])) for r in rows if r.get(column)]
    return [step for step, _ in pairs], [value for _, value in pairs]


def build_frontier_points():
    """The SIX VIZ-04 points as ``(label, dialog_ppl, retention_ppl)``, ordered by λ.

    Five are the final rows of the committed 1250-step sweep CSVs; λ=0 is ``LAMBDA0_POINT``
    (see the Pitfall-1 note above — its arm CSV has no retention column).
    """
    points = [("λ=0", LAMBDA0_POINT["dialog_ppl"], LAMBDA0_POINT["retention_ppl"])]
    for lam in SWEEP_LAMBDAS:
        final = _rows(RESULTS_DIR / f"ft_lam_{lam}.csv")[-1]
        points.append((f"λ={lam}", float(final["dialog_ppl"]), float(final["retention_ppl"])))
    return points


def plot_forgetting_curve(out_dir):
    """VIZ-01: forgetting + acquisition vs step for both 4000-step arms. Returns the path."""
    fig, (ax_ret, ax_dlg) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=DPI)

    for label, path, color in ARMS:
        rows = _rows(path)
        ax_ret.plot(*_series(rows, "retention_ppl"), color=color, label=label, marker="o", ms=3)
        ax_dlg.plot(*_series(rows, "dialog_ppl"), color=color, label=label, marker="o", ms=3)

    ax_ret.axhline(
        HEADLINE_RETENTION,
        linestyle="--",
        color="gray",
        label=f"v1.0 headline {HEADLINE_RETENTION} (full-val, unmasked)",
    )
    ax_ret.set_title("Forgetting — TinyStories retention PPL")
    ax_ret.set_ylabel("retention PPL (lower = less forgetting)")

    # Log y: the step-0 anchor is 31.9 and both arms land near 4.2-4.6, so a linear axis
    # collapses the entire post-anchor separation into one pixel band.
    ax_dlg.set_yscale("log")
    ax_dlg.set_title("Acquisition — masked dialogue PPL")
    ax_dlg.set_ylabel("dialogue PPL (lower = better learned)")

    for ax in (ax_ret, ax_dlg):
        ax.set_xlabel("fine-tuning step")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)

    fig.suptitle("EWC vs naive fine-tuning — 4000-step arms, identical config except λ (DEMO-04)")
    fig.tight_layout()

    out_path = pathlib.Path(out_dir) / "phase13_forgetting_curve.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_frontier(out_dir):
    """VIZ-04: retention-vs-acquisition trade-off across λ. Returns the path."""
    points = build_frontier_points()
    dialog = [d for _label, d, _r in points]
    retention = [r for _label, _d, r in points]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=DPI)
    ax.plot(dialog, retention, color="C0", linestyle=":", zorder=1)
    ax.scatter(dialog, retention, color="C0", zorder=2)
    for label, d, r in points:
        ax.annotate(label, (d, r), textcoords="offset points", xytext=(7, 5), fontsize=9)

    ax.set_xlabel("dialogue PPL (acquisition — lower is better)")
    ax.set_ylabel("retention PPL (forgetting — lower is better)")
    ax.set_title("EWC λ frontier — 1250-step sweep endpoints")
    ax.grid(alpha=0.3)
    ax.margins(x=0.13)  # headroom so the right-most (λ=100) annotation is not clipped
    # The budget is stated on the figure itself: these are 1250-step sweep endpoints and are
    # NOT comparable point-for-point with the 4000-step arms in the forgetting curve.
    fig.text(
        0.5,
        0.005,
        "1250-step sweep endpoints (LR 9e-5, unmasked) — not the 4000-step A/B arms",
        ha="center",
        fontsize=8,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))

    out_path = pathlib.Path(out_dir) / "phase13_frontier.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def main() -> None:
    for out_path in (plot_forgetting_curve(RESULTS_DIR), plot_frontier(RESULTS_DIR)):
        print(f"[plot_phase13] wrote {out_path}")


if __name__ == "__main__":
    main()
