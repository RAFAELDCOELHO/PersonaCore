"""Figure 1 of the erasure paper, generated from committed records. Standard library only.

    python scripts/erasure_kstar_figure.py > paper/figure1_three_instruments.svg

Three panels share one log-scaled axis, the number of rank-1 adapter components ablated:
A. teacher-forced NLL of each taught value (committed Phase 19 curve, eight checkpoints);
B. exposure rank of each taught value among its same-slot candidates;
C. generation recall in questions answered (the k* extension at its four checkpoints, and Phase 19's
   committed record at the rank-based stop, for the target only).
The shaded band is the bracket in which the target's generation recall first reaches zero; the
dashed lines are the rank-based stops, one per candidate-set size, from the committed resweep.

Nothing is typed: every value comes from `results/phase19_collateral_curve.json`,
`results/erasure_kstar_summary.json` and `results/phase19_reference_set_resweep.json`. The output
is deterministic, so a committed test can require the committed figure to equal what the records
render. It adds no rule and no measurement, and never writes to `results/`.
"""

import json
import math
import pathlib
import sys
from xml.sax.saxutils import escape

_ROOT = pathlib.Path(__file__).resolve().parent.parent
CURVE_PATH = _ROOT / "results" / "phase19_collateral_curve.json"
SUMMARY_PATH = _ROOT / "results" / "erasure_kstar_summary.json"
RESWEEP_PATH = _ROOT / "results" / "phase19_reference_set_resweep.json"

TARGET_COLOR = "#c0392b"
NONTARGET_COLOR = "#8c8c8c"
BAND_COLOR = "#f0b429"
STOP_COLOR = "#2c3e50"
GRID_COLOR = "#e4e4e4"
INK = "#222222"
FONT = "Helvetica, Arial, sans-serif"

WIDTH, LEFT, RIGHT = 880, 78, 150
PLOT_W = WIDTH - LEFT - RIGHT
TOP, PANEL_H, GAP = 92, 176, 56
HEIGHT = TOP + 3 * PANEL_H + 2 * GAP + 58


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[erasure_kstar_figure] {message}")


def _f(value):
    return f"{value:.2f}"


def _curve_rank(row, slot):
    entry = row["slots"][slot]
    for key in ("rank", "exposure_rank"):
        if key in entry:
            return entry[key]
    return None


def collect(curve, summary, resweep):
    """Everything the figure plots, read from the three records."""
    rows = sorted(curve["checkpoints"], key=lambda r: r["prefix"])
    target = curve["slot"]
    slots = sorted(rows[0]["slots"])
    _prove(target in slots, f"the target slot {target!r} is not among the curve's slots")
    nontargets = [s for s in slots if s != target]

    measured = sorted(int(k) for k in summary["checkpoints"])
    sequence = [int(k) for k, _ in summary["decision"]["sequence"]]
    _prove(measured == sequence, f"summary checkpoints {measured} != the decision's {sequence}")
    blocks = {k: summary["checkpoints"][str(k)] for k in measured}
    for k, block in blocks.items():
        _prove(sorted(block["nontarget"]) == nontargets, f"k = {k}: non-target slots differ")

    _prove(resweep["ordering_is_reference_set_invariant"] is True, "resweep ordering not invariant")
    stops = sorted((run["k"], run["reference_set_size"]) for run in resweep["runs"].values())
    _prove(curve["k"] in [k for k, _ in stops], "the curve's stop is not one of the resweep's")
    _prove(not set(measured) & {k for k, _ in stops}, "a measured checkpoint sits on a stop")

    per_slot_rank = {
        slot: [(r["prefix"], _curve_rank(r, slot)) for r in rows] for slot in nontargets
    }
    if all(rank is not None for series in per_slot_rank.values() for _, rank in series):
        rank_source, nontarget_rank = "curve", per_slot_rank
    else:
        rank_source = "extension"
        nontarget_rank = {
            slot: [(k, blocks[k]["nontarget"][slot]["exposure_rank_this_run"]) for k in measured]
            for slot in nontargets
        }

    committed = summary["committed_k78_read_not_recomputed"]
    n_questions = blocks[measured[0]]["target"]["n_questions"]
    return {
        "target": target,
        "nontargets": nontargets,
        "nll": {s: [(r["prefix"], r["slots"][s]["ans1_mean_nll"]) for r in rows] for s in slots},
        "target_rank": [(r["prefix"], r["target_rank"]) for r in rows],
        "nontarget_rank": nontarget_rank,
        "rank_source": rank_source,
        "measured": measured,
        "curve_stop": curve["k"],
        "target_recall": [(k, blocks[k]["target"]["successes"]) for k in measured]
        + [(curve["k"], committed["target_successes"])],
        "nontarget_recall": {
            s: [(k, blocks[k]["nontarget"][s]["post_answerable"]) for k in measured]
            for s in nontargets
        },
        "n_questions": n_questions,
        "bracket": summary["decision"]["bracket"],
        "stops": stops,
    }


class _Panel:
    def __init__(self, index, ymin, ymax):
        self.top = TOP + index * (PANEL_H + GAP)
        self.ymin, self.ymax = ymin, ymax

    def y(self, value):
        return self.top + PANEL_H - (value - self.ymin) / (self.ymax - self.ymin) * PANEL_H


def _points(fx, panel, series):
    return " ".join(f"{_f(fx(k))},{_f(panel.y(v))}" for k, v in series)


def _text(x, y, content, size=12, anchor="start", weight="normal", extra=""):
    return (
        f'<text x="{_f(x)}" y="{_f(y)}" font-size="{size}" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="{INK}"{extra}>{escape(content)}</text>'
    )


def render(data):
    """The whole SVG document, from `collect`'s output."""
    stops = data["stops"]
    xmax = 2 ** math.ceil(math.log2(stops[-1][0]))
    span = math.log2(xmax)

    def fx(k):
        return LEFT + math.log2(k) / span * PLOT_W

    max_nll = max(v for series in data["nll"].values() for _, v in series)
    max_rank = max(
        [r for _, r in data["target_rank"]]
        + [r for series in data["nontarget_rank"].values() for _, r in series]
    )
    n = data["n_questions"]
    panels = [
        (
            "panel-a",
            "A",
            "Teacher-forced NLL of the taught value",
            _Panel(0, 0, math.ceil(max_nll)),
        ),
        (
            "panel-b",
            "B",
            "Exposure rank among same-slot candidates (rank 1 = ceiling)",
            _Panel(1, max_rank + 0.5, 0.5),
        ),
        ("panel-c", "C", f"Generation recall (questions answered of {n})", _Panel(2, 0, n)),
    ]
    ticks = {
        "panel-a": [(v, str(v)) for v in range(0, math.ceil(max_nll) + 1)],
        "panel-b": [(r, str(r)) for r in range(1, max_rank + 1)],
        "panel-c": [(round(n * i / 3), str(round(n * i / 3))) for i in range(4)],
    }
    xticks = [2**i for i in range(int(span) + 1)]
    bottom = TOP + 3 * PANEL_H + 2 * GAP

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{FONT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="white"/>',
    ]

    # legend
    ly = 28
    out.append(
        f'<line x1="{LEFT}" y1="{ly}" x2="{LEFT + 30}" y2="{ly}" stroke="{TARGET_COLOR}" '
        f'stroke-width="2.4"/><circle cx="{LEFT + 15}" cy="{ly}" r="3.6" fill="{TARGET_COLOR}"/>'
    )
    out.append(_text(LEFT + 38, ly + 4, f"{data['target']} (erasure target)"))
    lx = LEFT + 260
    out.append(
        f'<line x1="{lx}" y1="{ly}" x2="{lx + 30}" y2="{ly}" stroke="{NONTARGET_COLOR}" '
        f'stroke-width="1.4"/><circle cx="{lx + 15}" cy="{ly}" r="2.4" fill="{NONTARGET_COLOR}"/>'
    )
    out.append(_text(lx + 38, ly + 4, f"{len(data['nontargets'])} non-target facts"))
    hx = lx + 210
    out.append(
        f'<circle cx="{hx}" cy="{ly}" r="3.6" fill="white" stroke="{TARGET_COLOR}" '
        f'stroke-width="1.6"/>'
    )
    out.append(_text(hx + 12, ly + 4, "Phase 19 record (not re-measured)"))

    ly2 = ly + 20
    out.append(
        f'<line x1="{LEFT}" y1="{ly2}" x2="{LEFT + 30}" y2="{ly2}" stroke="{STOP_COLOR}" '
        f'stroke-width="1.2" stroke-dasharray="5 4"/>'
    )
    out.append(_text(LEFT + 38, ly2 + 4, "rank-based stop, one per candidate-set size"))
    bx = LEFT + 340
    out.append(
        f'<rect x="{bx}" y="{ly2 - 6}" width="30" height="12" fill="{BAND_COLOR}" opacity="0.35"/>'
    )
    out.append(_text(bx + 38, ly2 + 4, "bracket of the target's first generation zero"))

    # band and stops, behind the panels' content
    low, high = data["bracket"]
    out.append(
        f'<rect class="bracket" data-low="{low}" data-high="{high}" x="{_f(fx(low))}" '
        f'y="{TOP}" width="{_f(fx(high) - fx(low))}" height="{_f(bottom - TOP)}" '
        f'fill="{BAND_COLOR}" opacity="0.18"/>'
    )
    label_y = TOP - 30
    for index, (k, size) in enumerate(stops):
        out.append(
            f'<line class="rank-stop" data-k="{k}" data-candidates="{size}" x1="{_f(fx(k))}" '
            f'y1="{label_y + 4}" x2="{_f(fx(k))}" y2="{bottom}" stroke="{STOP_COLOR}" '
            f'stroke-width="1.2" stroke-dasharray="5 4"/>'
        )
        left_side = index < len(stops) - 1
        out.append(
            _text(
                fx(k) + (-6 if left_side else 6),
                label_y,
                f"k = {k} ({size} candidates)",
                11,
                "end" if left_side else "start",
            )
        )

    for pid, letter, title, panel in panels:
        out.append(f'<g id="{pid}">')
        out.append(_text(LEFT - 66, panel.top - 14, f"{letter}  {title}", 13, "start", "bold"))
        for value, label in ticks[pid]:
            y = panel.y(value)
            out.append(
                f'<line x1="{LEFT}" y1="{_f(y)}" x2="{LEFT + PLOT_W}" y2="{_f(y)}" '
                f'stroke="{GRID_COLOR}" stroke-width="1"/>'
            )
            out.append(_text(LEFT - 8, y + 4, label, 11, "end"))
        for k in xticks:
            out.append(
                f'<line x1="{_f(fx(k))}" y1="{panel.top}" x2="{_f(fx(k))}" '
                f'y2="{panel.top + PANEL_H}" stroke="{GRID_COLOR}" stroke-width="1"/>'
            )
        out.append(
            f'<rect x="{LEFT}" y="{panel.top}" width="{PLOT_W}" height="{PANEL_H}" fill="none" '
            f'stroke="#999999" stroke-width="1"/>'
        )

        if pid == "panel-a":
            nontarget_series = {s: data["nll"][s] for s in data["nontargets"]}
            target_series = data["nll"][data["target"]]
        elif pid == "panel-b":
            nontarget_series = data["nontarget_rank"]
            target_series = data["target_rank"]
        else:
            nontarget_series = data["nontarget_recall"]
            target_series = data["target_recall"]
        for slot in sorted(nontarget_series):
            series = nontarget_series[slot]
            out.append(
                f'<polyline class="nontarget" data-slot="{escape(slot)}" fill="none" '
                f'stroke="{NONTARGET_COLOR}" stroke-width="1.4" opacity="0.8" '
                f'points="{_points(fx, panel, series)}"/>'
            )
            radius = 6.5 if pid == "panel-b" else 2.4
            opacity = 0.45 if pid == "panel-b" else 0.8
            for k, v in series:
                out.append(
                    f'<circle cx="{_f(fx(k))}" cy="{_f(panel.y(v))}" r="{radius}" '
                    f'fill="{NONTARGET_COLOR}" opacity="{opacity}"/>'
                )
        out.append(
            f'<polyline class="target" fill="none" stroke="{TARGET_COLOR}" stroke-width="2.4" '
            f'points="{_points(fx, panel, target_series)}"/>'
        )
        for k, v in target_series:
            hollow = pid == "panel-c" and k == data["curve_stop"]
            fill = "white" if hollow else TARGET_COLOR
            out.append(
                f'<circle class="target-point" cx="{_f(fx(k))}" cy="{_f(panel.y(v))}" r="3.6" '
                f'fill="{fill}" stroke="{TARGET_COLOR}" stroke-width="1.6"/>'
            )
        if pid == "panel-c":
            out.append(
                _text(
                    fx(high) - 4,
                    panel.top - 14,
                    f"target first reaches 0/{n} in ({low}, {high}]",
                    12,
                    "end",
                )
            )
        if pid == "panel-b":
            all_one = all(r == 1 for series in data["nontarget_rank"].values() for _, r in series)
            note = (
                f"the {len(data['nontargets'])} non-target facts (grey) sit at rank 1 at every "
                f"plotted checkpoint"
                if all_one
                else "non-target facts in grey"
            )
            out.append(_text(LEFT + 10, panel.y(1.5) + 4, note, 12))
        out.append("</g>")

    for k in xticks:
        out.append(_text(fx(k), bottom + 18, str(k), 11, "middle"))
    out.append(
        _text(
            LEFT + PLOT_W / 2,
            bottom + 42,
            "rank-1 adapter components ablated, k (log scale)",
            12,
            "middle",
        )
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main(argv):
    _prove(not argv, "no arguments: it reads the committed records and writes SVG to stdout")
    curve = json.loads(CURVE_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    resweep = json.loads(RESWEEP_PATH.read_text(encoding="utf-8"))
    sys.stdout.write(render(collect(curve, summary, resweep)))


if __name__ == "__main__":
    main(sys.argv[1:])
