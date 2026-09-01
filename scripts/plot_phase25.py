"""Phase-25 frontier figures: privacy x utility, both arms, both capacities — FRONT-03.

ONE FILE IN, FIGURES OUT. Every number this module draws comes from
``results/phase25_frontier.json`` (:data:`FRONTIER_RECORD`), the artifact plan 25-19 assembles
write-once from the 44 committed per-point records. :data:`ALLOWED_READS` is that promise written
down as a tuple, and it is **enforced by a test** — ``tests/test_phase25_plots.py``'s
``test_the_plotter_opens_only_the_frontier_artifact`` walks this module's AST, resolves the path
operand of every read call and every ``.json`` literal, and fails naming any file outside the
allow-list. The plotter opening a SECOND file would break FRONT-03's single-source promise
silently: a reader with the artifact and a clone could no longer regenerate the figure, and
nothing would turn red.

D-33 — THE PHASE-15 GUARD IS RETARGETED, NOT REINVENTED. Three parts of
``tests/test_phase15_plots.py::test_plotting_module_never_opens_a_checkpoint`` are ported verbatim
in structure onto this module: an AST import walk with its meta-guard (no torch, no numpy), an AST
string-constant walk banning any ``.pt`` literal, and a fresh-interpreter subprocess probe that
exits 1 if ``torch`` lands in ``sys.modules``. The ARTIFACT ALLOW-LIST above is **new** — Phase 15's
guard has no allow-list, only a ``.pt`` prohibition — and was authored in plan 25-09, not ported.

NO RETYPED FIGURE VALUE, ANYWHERE. Every annotated number — the never-taught floor, the pool
ceiling, each point's epsilon, each point's recall — is read from the artifact or derived from it at
call time. A figure carrying a retyped number would be exactly the drift this milestone exists to
prevent: the artifact would say one thing and the published picture another, and only the picture
would travel. Rates are computed from the record's own numerator and denominator at plot time —
counts, never a stored rate.

  DP arm       -> results/phase25_frontier_dp.png          n=8 and n=64: measured epsilon (log x)
                                                           against measured taught recall
  Adversarial  -> results/phase25_frontier_adversarial.png n=8 and n=64: mixture ratio against the
                                                           same utility axis, pool ceiling annotated

THE TWO ARMS DO NOT SHARE AN X-AXIS, AND THAT IS STRUCTURAL RATHER THAN STYLISTIC (D-19, D-23). The
adversarial axis is a mixture ratio, not an epsilon: the arm has no sigma, no delta and no q, which
is the same fact ``accounting: null`` states in the record and the reason
``mitigation_gate.capacity_comparison`` is a DP-only instrument. Its axis terminates at the POOL
CEILING by construction — the largest ratio at which the trained pool is used exactly once — not at
the never-taught floor, so the adversarial panels carry that named structural asymmetry in their
caption rather than leaving a reader to infer a missing curve.

WHAT THIS MODULE REQUIRES OF THE ARTIFACT (the contract plan 25-19's assembly must satisfy):
  ``points``              — mapping of point key -> point record, all four arms present. Each record
                            carries ``arm``, ``axis``, its own axis value under that name
                            (``sigma`` / ``ratio``), ``epsilon`` (``null`` at the sigma=0
                            control and on the whole adversarial arm), ``taught_recall`` as
                            ``{"numerator": int, "denominator": int}``, and D-21's inline
                            ``draws_per_question`` / ``draws_per_question_source``.
  ``never_taught_floor``  — ``results/phase23_never_taught.json``'s ``pooled`` block carried
                            VERBATIM (D-42's own discipline): ``nontarget_successes`` /
                            ``nontarget_questions`` / ``tier``. Both arms are read against this one
                            floor (D-19), so it is drawn as the shared lower-left reference.

Run: ``.venv/bin/python scripts/plot_phase25.py``. Headless (``Agg`` is selected BEFORE ``pyplot``,
so a fresh interpreter can import this module with no display); nothing here opens a window, and
nothing here opens a checkpoint.
"""

import argparse
import json
import pathlib

import matplotlib

# Agg BEFORE pyplot: this module only ever writes files, and the fresh-interpreter probe in
# tests/test_phase25_plots.py imports it with no display attached.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend selection above)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_DIR = _ROOT / "results"

# ROADMAP.md's `results/phase2X_frontier.json` is a PLACEHOLDER, not a filename (D-31). The real
# name is spelled here rather than imported from `phase25_record` so this module's import surface
# stays minimal — and `test_the_plotters_path_matches_the_record_modules` asserts the two constants
# are EQUAL, which is what closes the drift a second spelling would otherwise open.
FRONTIER_RECORD = _ROOT / "results" / "phase25_frontier.json"

# THE ALLOW-LIST. The only file this module may open. Enforced by
# tests/test_phase25_plots.py::test_the_plotter_opens_only_the_frontier_artifact.
ALLOWED_READS = (FRONTIER_RECORD,)

ARTIFACT_PRODUCER = "plan 25-19's write-once assembly in `scripts/phase25_record.py`"

DP_ARMS = ("dp_n8", "dp_n64")
ADVERSARIAL_ARMS = ("adv_n8", "adv_n64")
ORDERED_ARMS = DP_ARMS + ADVERSARIAL_ARMS

FIGURES = {
    "dp": "phase25_frontier_dp.png",
    "adversarial": "phase25_frontier_adversarial.png",
}

# The floor section, and the two COUNT fields the rate is computed from at plot time.
FLOOR_SECTION = "never_taught_floor"
FLOOR_SUCCESSES = "nontarget_successes"
FLOOR_QUESTIONS = "nontarget_questions"

# Marker STYLES, never marker VALUES: the styles are assigned to the distinct `draws_per_question`
# values the artifact actually carries, smallest k first, so a K=48 promoted point is visually
# distinct from a K=16 curve point (D-21) without this module naming either number.
_MARKER_CYCLE = ("o", "D", "^", "s")
_MARKER_SIZES = (30, 72, 60, 60)

DPI = 150
CAPTION_FONTSIZE = 8
CAPTION_WIDTH = 118


def _fail(message):
    """``SystemExit`` with a readable message — never a traceback. The register `_load_artifact`
    in ``scripts/plot_phase15.py`` uses, so a missing or truncated artifact reads as a sentence."""
    raise SystemExit(f"[plot_phase25] {message}")


def _wrap(text, width=CAPTION_WIDTH):
    """Hard-wrap a caption at ``width`` columns. Kept local so the import surface stays minimal."""
    lines, line = [], ""
    for word in str(text).split():
        candidate = f"{line} {word}".strip()
        if len(candidate) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return "\n".join(lines)


def _sentence_about(text, needle):
    """The first sentence of ``text`` containing ``needle``, else its first sentence.

    The adversarial caption's prose is READ FROM THE ARTIFACT rather than retyped here; the record's
    own reason string runs to a paragraph, so one sentence of it is selected instead of quoting the
    whole block on a figure. Selecting is not rewriting: the words are the artifact's.
    """
    sentences = [part.strip() for part in str(text).split(". ") if part.strip()]
    if not sentences:
        return ""
    for sentence in sentences:
        if needle in sentence:
            return sentence.rstrip(".") + "."
    return sentences[0].rstrip(".") + "."


def load_frontier(path=None):
    """The committed frontier artifact, validated on the way in. The ONLY file this module opens.

    A truncated artifact renders a panel that looks plausible and describes nothing, so every
    failure below names the offending file and the offending key and raises rather than plotting.
    """
    path = pathlib.Path(FRONTIER_RECORD if path is None else path)
    if not path.exists():
        _fail(
            f"{path}: missing. This module reads ONLY that artifact (FRONT-03, D-33) and it is "
            f"assembled write-once by {ARTIFACT_PRODUCER} from the 44 committed per-point records. "
            "Run the sweep and its assembly first, then re-run this script."
        )

    artifact = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict) or not artifact:
        _fail(f"{path}: did not parse to a non-empty object — not a Phase-25 frontier artifact")

    points = artifact.get("points")
    if not isinstance(points, dict) or not points:
        _fail(f"{path}: has no non-empty 'points' mapping — not a Phase-25 frontier artifact")

    for key, point in points.items():
        arm = point.get("arm")
        if arm not in ORDERED_ARMS:
            _fail(f"{path}: point {key!r} names arm {arm!r}, none of {ORDERED_ARMS}")
        axis = point.get("axis")
        if axis is None or axis not in point:
            _fail(
                f"{path}: point {key!r} declares axis {axis!r} but carries no {axis!r} field. The "
                "key is a LABEL and the record's own axis field is authoritative"
            )
        recall = point.get("taught_recall")
        if not isinstance(recall, dict) or not {"numerator", "denominator"} <= set(recall):
            _fail(
                f"{path}: point {key!r} has no 'taught_recall' numerator/denominator pair. The "
                "utility axis is computed from COUNTS at plot time, never from a stored rate"
            )
        if point.get("draws_per_question") is None:
            _fail(
                f"{path}: point {key!r} carries no inline 'draws_per_question'. D-21 puts k beside "
                "every reading precisely because a K=16 and a K=48 reading of one point are "
                "numerically identical and differ only in statistical precision"
            )

    missing_arms = [arm for arm in ORDERED_ARMS if not _points_for(artifact, arm)]
    if missing_arms:
        _fail(
            f"{path}: no points for arm(s) {missing_arms}. All four legs are pinned (D-08) and a "
            "panel with no curve is a figure that describes nothing"
        )

    floor = artifact.get(FLOOR_SECTION)
    if not isinstance(floor, dict) or not {FLOOR_SUCCESSES, FLOOR_QUESTIONS} <= set(floor):
        _fail(
            f"{path}: has no {FLOOR_SECTION!r} block carrying {FLOOR_SUCCESSES!r} and "
            f"{FLOOR_QUESTIONS!r}. Both arms are read against the SAME already-measured "
            f"never-taught floor (D-19); {ARTIFACT_PRODUCER} carries "
            "`results/phase23_never_taught.json`'s `pooled` block verbatim for exactly this reason"
        )
    return artifact


def _points_for(artifact, arm):
    """This arm's point records, ordered by their own axis value. Counts in, order out."""
    rows = [point for point in artifact["points"].values() if point.get("arm") == arm]
    return sorted(rows, key=lambda point: float(point[point["axis"]]))


def _rate(numerator, denominator, what):
    """A rate computed from ITS OWN numerator and denominator, at plot time. Never stored."""
    if not denominator:
        _fail(
            f"{what}: denominator is {denominator!r} — a rate without its denominator is "
            "not a reading"
        )
    return float(numerator) / float(denominator)


def _recall(point):
    return _rate(
        point["taught_recall"]["numerator"],
        point["taught_recall"]["denominator"],
        f"point {point.get('point_key')!r} taught recall",
    )


def _floor_rate(artifact):
    floor = artifact[FLOOR_SECTION]
    return _rate(floor[FLOOR_SUCCESSES], floor[FLOOR_QUESTIONS], "the never-taught floor")


def _floor_label(artifact):
    floor = artifact[FLOOR_SECTION]
    tier = floor.get("tier", "the gated tier")
    return (
        f"never-taught floor: {floor[FLOOR_SUCCESSES]}/{floor[FLOOR_QUESTIONS]} on {tier} "
        "(shared lower-left reference for BOTH arms, D-19)"
    )


def _k_styles(artifact):
    """A marker style per distinct ``draws_per_question`` in the artifact, smallest k first."""
    ks = sorted({int(point["draws_per_question"]) for point in artifact["points"].values()})
    if len(ks) > len(_MARKER_CYCLE):
        _fail(
            f"the artifact carries {len(ks)} distinct k values {ks}; only {len(_MARKER_CYCLE)} "
            "marker styles are defined"
        )
    return {k: (_MARKER_CYCLE[i], _MARKER_SIZES[i]) for i, k in enumerate(ks)}


def _scatter_by_k(ax, rows, xs, styles):
    """One scatter call per k, so the legend states each point's k AND the constant it came from."""
    for k in sorted({int(row["draws_per_question"]) for row in rows}):
        marker, size = styles[int(k)]
        sub = [(x, row) for x, row in zip(xs, rows) if int(row["draws_per_question"]) == k]
        source = sub[0][1].get("draws_per_question_source", "unattributed")
        ax.scatter(
            [x for x, _ in sub],
            [_recall(row) for _, row in sub],
            marker=marker,
            s=size,
            edgecolor="black",
            linewidth=0.5,
            zorder=3,
            label=f"k={k} ({source})",
        )


def _floor_line(ax, artifact):
    ax.axhline(
        _floor_rate(artifact),
        color="0.35",
        linestyle=":",
        linewidth=1.2,
        zorder=1,
        label=_floor_label(artifact),
    )


def plot_dp_arm(artifact, out_dir):
    """The DP panels: measured epsilon against measured taught recall, at both capacities."""
    fig, axes = plt.subplots(1, len(DP_ARMS), figsize=(13.4, 5.2), dpi=DPI)
    for ax, arm in zip(axes, DP_ARMS):
        rows = _points_for(artifact, arm)
        noised = [row for row in rows if row.get("epsilon") is not None]
        controls = [row for row in rows if row.get("epsilon") is None]

        _scatter_by_k(ax, noised, [float(row["epsilon"]) for row in noised], _k_styles(artifact))
        if noised:
            ordered = sorted(noised, key=lambda row: float(row["epsilon"]))
            ax.plot(
                [float(row["epsilon"]) for row in ordered],
                [_recall(row) for row in ordered],
                color="0.55",
                linewidth=1.0,
                zorder=2,
            )
            ax.set_xscale("log")

        # The sigma=0 CONTROL has no epsilon (`epsilon: None`) and cannot be placed on an epsilon
        # axis at all — it is an adapter trained on the same facts with NO privacy, which is the
        # sigma->0 end of this curve. Drawn as the reconnection reference rather than given a
        # fabricated x coordinate.
        for control in controls:
            ax.axhline(
                _recall(control),
                color="tab:blue",
                linestyle="--",
                linewidth=1.1,
                zorder=1,
                label=(
                    f"sigma=0 control ({control['axis']}={float(control[control['axis']]):g}, "
                    "no epsilon) — the sigma->0 reconnection point"
                ),
            )

        _floor_line(ax, artifact)
        ax.set_xlabel("measured privacy — epsilon at the fact level (log scale; larger = weaker)")
        ax.set_ylabel("measured utility — taught recall (successes / questions)")
        ax.set_title(f"{arm} — {len(rows)} swept point(s)")
        ax.legend(fontsize=7, loc="best")

    fig.suptitle("Phase 25 — DP arm: privacy x utility at both capacities")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.text(
        0.5,
        0.012,
        _wrap(
            "epsilon and recall are read from results/phase25_frontier.json; every rate is "
            "computed from the record's own numerator and denominator at plot time. Marker shape "
            "carries each point's k, inline from the record (D-21): a promoted reading and a curve "
            "reading of one point are numerically identical in epsilon and differ only in "
            "statistical precision."
        ),
        ha="center",
        fontsize=CAPTION_FONTSIZE,
        color="gray",
    )

    out_path = pathlib.Path(out_dir) / FIGURES["dp"]
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_adversarial_arm(artifact, out_dir):
    """The adversarial panels: mixture ratio against the same utility axis, pool ceiling annotated.

    The x-axis is a RATIO and not an epsilon, so this figure is separate from the DP one rather
    than a third and fourth panel beside it: the two arms must not share an x-axis (D-19, D-23).
    """
    fig, axes = plt.subplots(1, len(ADVERSARIAL_ARMS), figsize=(13.4, 5.2), dpi=DPI)
    reason = ""
    for ax, arm in zip(axes, ADVERSARIAL_ARMS):
        rows = _points_for(artifact, arm)
        xs = [float(row[row["axis"]]) for row in rows]
        _scatter_by_k(ax, rows, xs, _k_styles(artifact))
        if rows:
            ax.plot(xs, [_recall(row) for row in rows], color="0.55", linewidth=1.0, zorder=2)
            # THE POOL CEILING, DERIVED FROM THE DATA rather than retyped: the largest swept ratio
            # IS the axis terminus by construction (the largest ratio at which the trained pool is
            # used exactly once). A literal here would be a number the artifact could contradict.
            ceiling = max(xs)
            ax.axvline(
                ceiling,
                color="tab:red",
                linestyle="-.",
                linewidth=1.1,
                zorder=1,
                label=f"pool ceiling {ceiling!r} — the axis TERMINUS, not a floor",
            )
            reason = reason or str(rows[0].get("epsilon_omitted_reason") or "")

        _floor_line(ax, artifact)
        ax.set_xlabel("adversarial mixture ratio — adversarial episodes per clean episode")
        ax.set_ylabel("measured utility — taught recall (successes / questions)")
        ax.set_title(f"{arm} — {len(rows)} swept point(s)")
        ax.legend(fontsize=7, loc="best")

    fig.suptitle("Phase 25 — adversarial arm: mixture ratio x utility at both capacities")
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    fig.text(
        0.5,
        0.012,
        _wrap(
            "NAMED STRUCTURAL ASYMMETRY (D-19, D-23): this axis carries NO epsilon and "
            "terminates at the pool ceiling by construction, not at the never-taught floor — the "
            "missing curve to the floor is a property of the arm, not an omission. "
            + _sentence_about(reason, "capacity rule")
        ),
        ha="center",
        fontsize=CAPTION_FONTSIZE,
        color="gray",
    )

    out_path = pathlib.Path(out_dir) / FIGURES["adversarial"]
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--frontier",
        type=pathlib.Path,
        default=FRONTIER_RECORD,
        help="the frontier artifact — the ONLY file this script reads (FRONT-03)",
    )
    parser.add_argument(
        "--outdir",
        type=pathlib.Path,
        default=RESULTS_DIR,
        help="where the figures are written",
    )
    args = parser.parse_args(argv)

    artifact = load_frontier(args.frontier)
    for out_path in (
        plot_dp_arm(artifact, args.outdir),
        plot_adversarial_arm(artifact, args.outdir),
    ):
        print(f"[plot_phase25] wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
