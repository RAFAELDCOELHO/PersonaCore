"""Paper tables for the k* extension, generated from committed records.

Nothing here is typed: every number is read from `results/erasure_kstar_summary.json` or from the
committed Phase 19 curve `results/phase19_collateral_curve.json`, and the output opens with the
sha256 of both files, so a table in the paper traces to the exact bytes it came from.

    python scripts/erasure_kstar_tables.py > paper/erasure_kstar_tables.md

It adds no rule and no measurement, imports nothing from the pin, and never writes to `results/`.
Cells that no committed record carries print as an em dash, never as an estimate.
"""

import hashlib
import json
import pathlib
import sys
from collections import Counter

_ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMMARY_PATH = _ROOT / "results" / "erasure_kstar_summary.json"
CURVE_PATH = _ROOT / "results" / "phase19_collateral_curve.json"
DASH = "—"
PRE_GAP_TOLERANCE = 1e-6


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[erasure_kstar_tables] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _pct(value):
    return f"{100 * value:.2f}%"


def _gap(dialogue):
    return dialogue["adapter_on"] - dialogue["adapter_off"]


def _measured_ks(summary):
    ks = sorted(int(k) for k in summary["checkpoints"])
    sequence = [int(k) for k, _ in summary["decision"]["sequence"]]
    _prove(ks == sequence, f"summary checkpoints {ks} != the decision's sequence {sequence}")
    return ks


def _pre_gap(summary, ks):
    gaps = [_gap(summary["checkpoints"][str(k)]["dialogue"]["pre_this_run"]) for k in ks]
    _prove(
        max(gaps) - min(gaps) < PRE_GAP_TOLERANCE,
        f"the pre-ablation dialogue gap differs between checkpoint runs: {gaps}",
    )
    return gaps[0]


def _checkpoint_table(summary, curve, ks, gap_pre):
    stop, kstar = curve["k"], summary["decision"]["kstar"]
    committed = summary["committed_k78_read_not_recomputed"]
    lines = [
        "| k | target exposure rank | target value-span NLL | target generation recall "
        "| Wilson upper bound | dialogue adaptation destroyed | non-targets over margin |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in sorted(curve["checkpoints"], key=lambda r: r["prefix"]):
        k = row["prefix"]
        block = summary["checkpoints"].get(str(k))
        if block is not None:
            target = block["target"]
            recall = f"{target['successes']}/{target['n_questions']}"
            bound = f"{target['wilson_upper_bound']:.4f}"
            flagged = sum(entry["over_margin"] for entry in block["nontarget"].values())
            _prove(
                flagged == block["nontarget_over_margin_count"],
                f"k = {k}: the block counts {block['nontarget_over_margin_count']} non-targets "
                f"over the margin but its own cells flag {flagged}",
            )
            over = f"{flagged}/{len(block['nontarget'])}"
        elif k == stop:
            recall = f"{committed['target_successes']}/{committed['target_n_questions']}"
            bound = over = DASH
        else:
            recall = bound = over = DASH
        destroyed = _pct(1 - _gap(row["dialogue_ppl"]) / gap_pre)
        label = f"**{k}**" if k == kstar else str(k)
        nll = f"{row['target_ans1_mean_nll']:.4f}"
        rank = row["target_rank"]
        lines.append(f"| {label} | {rank} | {nll} | {recall} | {bound} | {destroyed} | {over} |")
    return "\n".join(lines)


def _nontarget_table(summary, ks):
    first = summary["checkpoints"][str(ks[0])]
    margin = first["nontarget_margin"]
    for k in ks:
        _prove(
            summary["checkpoints"][str(k)]["nontarget_margin"] == margin,
            f"the (b) margin differs at k = {k}",
        )
    slots = sorted(first["nontarget"])
    lines = [
        "| non-target fact | " + " | ".join(str(k) for k in ks) + " |",
        "|---|" + "---|" * len(ks),
    ]
    for slot in slots:
        cells = []
        for k in ks:
            entry = summary["checkpoints"][str(k)]["nontarget"][slot]
            text = f"{entry['pre_answerable']}→{entry['post_answerable']} ({entry['delta']:.3f})"
            if entry["over_margin"]:
                text = f"**{text}**"
            elif abs(entry["delta"] - margin) < 1e-12:
                text += " ="
            cells.append(text)
        lines.append(f"| {slot} | " + " | ".join(cells) + " |")
    n = first["nontarget"][slots[0]]["n_questions"]
    note = (
        f"Cells read `pre→post (|Δrate|)` over {n} questions per fact. Bold: strictly above the "
        f"(b) margin {margin:.6f}. `=`: exactly at the margin, which does not count."
    )
    return "\n".join(lines), note


def _composition_tables(curve, ks):
    prefix, stop = curve["ordered_prefix"], curve["k"]
    _prove(len(prefix) >= stop, f"ordered_prefix holds {len(prefix)} addresses, fewer than {stop}")
    every_k = sorted(set(ks) | {stop})
    layers = sorted({a[0] for a in prefix[:stop]})
    projections = sorted({a[1] for a in prefix[:stop]})
    by_layer = [
        "| k | " + " | ".join(f"layer {layer}" for layer in layers) + " | layers touched |",
        "|---|" + "---|" * (len(layers) + 1),
    ]
    by_projection = [
        "| k | " + " | ".join(projections) + " | projections touched |",
        "|---|" + "---|" * (len(projections) + 1),
    ]
    for k in every_k:
        head = prefix[:k]
        _prove(len(head) == k, f"ordered_prefix[:{k}] holds {len(head)} addresses")
        layer_counts = Counter(a[0] for a in head)
        projection_counts = Counter(a[1] for a in head)
        _prove(sum(layer_counts.values()) == k, f"layer counts at k = {k} do not sum to k")
        cells = " | ".join(str(layer_counts.get(layer, 0)) for layer in layers)
        by_layer.append(f"| {k} | {cells} | {len(layer_counts)} |")
        cells = " | ".join(str(projection_counts.get(p, 0)) for p in projections)
        by_projection.append(f"| {k} | {cells} | {len(projection_counts)} |")
    return "\n".join(by_layer), "\n".join(by_projection)


def _decision_block(summary, curve):
    decision, first = summary["decision"], next(iter(summary["provenance"].values()))
    lines = [
        f"- k* = {decision['kstar']}, bracket ({decision['bracket'][0]}, {decision['bracket'][1]}]",
        f"- null case: {decision['null_case']}",
        f"- rebound after k*: {decision['rebound_after_kstar']}",
        f"- non-increasing sequence: {decision['non_increasing']}",
        "- target successes by k: " + ", ".join(f"{k}: {s}" for k, s in decision["sequence"]),
        f"- rank-instrument stop: k = {curve['k']}; it lags the generation zero by at least "
        f"{curve['k'] - decision['kstar']} components",
        f"- curve agreement at every measured k: {summary['curve_agreement_all']}",
        f"- run provenance: git_sha {first['git_sha']}, torch {first['torch']}, "
        f"device {first['device']}",
        f"- rule sha256 (`prereg_sha256`): {summary['prereg_sha256']}",
        f"- curve sha256: {summary['curve_sha256']}",
    ]
    return "\n".join(lines)


def render(summary, curve, sources):
    """The whole Markdown document, from two parsed records and the sha256 of their files."""
    ks = _measured_ks(summary)
    _prove(curve["k"] not in ks, "the rank-instrument stop is one of the measured checkpoints")
    gap_pre = _pre_gap(summary, ks)
    nontarget, nontarget_note = _nontarget_table(summary, ks)
    by_layer, by_projection = _composition_tables(curve, ks)
    stamp = "; ".join(f"{name} sha256 {digest}" for name, digest in sorted(sources.items()))
    parts = [
        f"<!-- generated by scripts/erasure_kstar_tables.py; {stamp} -->",
        "### Two instruments across the checkpoints",
        _checkpoint_table(summary, curve, ks, gap_pre),
        f"Recall, Wilson bound and non-target counts exist only where the k* extension measured "
        f"(k = {', '.join(map(str, ks))}) and, for recall at k = {curve['k']}, in Phase 19's "
        f"committed record; {DASH} marks a checkpoint no generation measurement covers. Rank, NLL "
        f"and dialogue come from the committed curve.",
        "### Collateral damage per non-target fact",
        nontarget,
        nontarget_note,
        "### Composition of the ablated prefix, by layer",
        by_layer,
        "### Composition of the ablated prefix, by projection",
        by_projection,
        "### Decision and provenance",
        _decision_block(summary, curve),
    ]
    return "\n\n".join(parts) + "\n"


def main(argv):
    _prove(not argv, "no arguments: it reads the committed records and writes Markdown to stdout")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    curve = json.loads(CURVE_PATH.read_text(encoding="utf-8"))
    sources = {p.name: _sha256(p) for p in (SUMMARY_PATH, CURVE_PATH)}
    sys.stdout.write(render(summary, curve, sources))


if __name__ == "__main__":
    main(sys.argv[1:])
