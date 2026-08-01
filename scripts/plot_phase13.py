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
from matplotlib.ticker import StrMethodFormatter  # noqa: E402  (same reason)

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

# The frontier endpoint is a CLAIM the figure title and caption both make ("1250-step sweep
# endpoints"), so the row is selected by step rather than positionally: a CSV that ever stops
# short would otherwise be plotted silently under a title asserting a budget it never reached.
SWEEP_ENDPOINT_STEP = 1250

# Fixed series order + colors (08-UI-SPEC plot contract): matplotlib default cycle only.
ARMS = (
    ("naive (λ=0)", NAIVE_CSV, "C1"),
    ("EWC (λ=0.01)", EWC_CSV, "C0"),
)
DPI = 150

# The 11in curve figure is read at ~7in column width, so anything below ~10pt drops under 6pt
# on the page. Nothing on either figure is smaller than this.
LEGEND_FONTSIZE = 11


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _series(rows, column, source="<rows>"):
    """``(steps, values)`` for the rows carrying a value in ``column``. Never degrades silently.

    The pre-seeded step-0 row leaves the train-only columns blank (``restval=""``), so an
    unconditional ``float(r[col])`` would raise; the eval columns are populated there. The
    blank test is explicit (``not in (None, "")``) rather than truthy: ``DictReader`` yields
    strings, and a legitimate ``"0.0"`` must not be mistaken for a blank.

    An ABSENT column is the twin of the Pitfall-1 hazard ``build_frontier_points`` already
    defends against (``results/ft_lr_9e-5.csv`` carries no ``retention_ppl``): every
    ``DictReader`` row dict holds all fieldnames, so a missing column resolves to ``None`` on
    every row and would plot a valid-looking but EMPTY panel. Raise instead — an empty panel
    under a titled axis is a figure that lies.
    """
    if not rows:
        raise ValueError(f"{source}: no rows at all, cannot plot column {column!r}")
    if column not in rows[0]:
        raise KeyError(f"{source}: no column {column!r}; columns are {sorted(rows[0])}")
    pairs = [
        (int(float(r["step"])), float(r[column])) for r in rows if r.get(column) not in (None, "")
    ]
    if not pairs:
        raise ValueError(f"{source}: column {column!r} is blank in all {len(rows)} rows")
    return [step for step, _ in pairs], [value for _, value in pairs]


def build_frontier_points():
    """The SIX VIZ-04 points as ``(label, dialog_ppl, retention_ppl)``, ordered by λ.

    Five are the ``SWEEP_ENDPOINT_STEP`` rows of the committed sweep CSVs; λ=0 is
    ``LAMBDA0_POINT`` (see the Pitfall-1 note above — its arm CSV has no retention column).
    """
    points = [("λ=0", LAMBDA0_POINT["dialog_ppl"], LAMBDA0_POINT["retention_ppl"])]
    for lam in SWEEP_LAMBDAS:
        path = RESULTS_DIR / f"ft_lam_{lam}.csv"
        rows = _rows(path)
        endpoint = next((r for r in rows if int(float(r["step"])) == SWEEP_ENDPOINT_STEP), None)
        if endpoint is None:
            raise ValueError(
                f"{path}: no step-{SWEEP_ENDPOINT_STEP} row (last is "
                f"{rows[-1]['step'] if rows else 'n/a'}) — the figure title and caption both "
                f"claim {SWEEP_ENDPOINT_STEP}-step sweep endpoints"
            )
        points.append((f"λ={lam}", float(endpoint["dialog_ppl"]), float(endpoint["retention_ppl"])))
    return points


def plot_forgetting_curve(out_dir):
    """VIZ-01: forgetting + acquisition vs step for both 4000-step arms. Returns the path."""
    fig, (ax_ret, ax_dlg) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=DPI)

    for label, path, color in ARMS:
        rows = _rows(path)
        # `path` is threaded in so a missing column names the offending CSV, not just itself.
        for ax, column in ((ax_ret, "retention_ppl"), (ax_dlg, "dialog_ppl")):
            ax.plot(*_series(rows, column, path), color=color, label=label, marker="o", ms=3)

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
    # ...but the DEFAULT log formatter then labels the ticks 4x10^0 / 6x10^0 / 10^1 / 3x10^1.
    # This panel exists to compare perplexities of 31.90 -> 4.19 vs 4.57, so the reader must
    # not have to decode "4x10^0" as 4.0. Plain numbers on BOTH major and minor ticks (in this
    # range 10 is the only major; 4/6/20/30 are all minor, so majors alone would label almost
    # nothing). "{x:g}" over a bare ScalarFormatter so the major reads "10", not "10.0".
    plain = StrMethodFormatter("{x:g}")
    ax_dlg.yaxis.set_major_formatter(plain)
    ax_dlg.yaxis.set_minor_formatter(plain)
    ax_dlg.set_title("Acquisition — masked dialogue PPL")
    ax_dlg.set_ylabel("dialogue PPL (lower = better learned)")

    for ax in (ax_ret, ax_dlg):
        ax.set_xlabel("fine-tuning step")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=LEGEND_FONTSIZE)

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
