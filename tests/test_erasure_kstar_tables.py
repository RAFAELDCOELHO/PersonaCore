"""Guards for `scripts/erasure_kstar_tables.py`.

Synthetic records with the summary and curve shapes the driver writes test the rendering logic. The
last test renders the COMMITTED records, so a schema mismatch shows up here and not in the paper.
"""

import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import erasure_kstar_tables as tables  # noqa: E402

MEASURED = (8, 16, 32, 64)
STOP = 78
OFF = 4.573349214207799
PRE_ON = 5.815445876712191
ON = {1: 5.8, 2: 5.79, 4: 5.7, 8: 5.51, 16: 5.3, 32: 5.09, 64: 4.92, 78: 4.85}
SUCCESSES = {8: 24, 16: 18, 32: 2, 64: 0}
MARGIN = 8 / 27
# Layer counts of the first k addresses: cumulative, so the fixture prefix can be built in slices.
STEPS = [
    (8, [2, 1, 1, 1, 1, 2]),
    (16, [1, 2, 1, 2, 1, 1]),
    (32, [3, 3, 2, 4, 2, 2]),
    (64, [8, 5, 6, 5, 5, 3]),
    (78, [4, 1, 2, 5, 1, 1]),
]
PROJECTIONS = ["q", "k", "v", "c_proj", "fc_in", "fc_out"]


def _prefix():
    addresses = []
    for _k, per_layer in STEPS:
        for layer, count in enumerate(per_layer):
            for _ in range(count):
                addresses.append([layer, PROJECTIONS[len(addresses) % 6], len(addresses)])
    return addresses


def _curve():
    rows = [
        {
            "prefix": k,
            "target_rank": 2 if k == STOP else 1,
            "target_ans1_mean_nll": 0.13 + k / 20,
            "dialogue_ppl": {"adapter_on": ON[k], "adapter_off": OFF},
            "slots": {
                "pet_name": {"ans1_mean_nll": 0.1 + k / 20},
                "person_name": {"ans1_mean_nll": 0.4 + k / 100},
                "street": {"ans1_mean_nll": 0.3 + k / 100},
            },
        }
        for k in (1, 2, 4, 8, 16, 32, 64, 78)
    ]
    return {
        "k": STOP,
        "slot": "pet_name",
        "stopped": True,
        "ordered_prefix": _prefix(),
        "checkpoints": rows,
    }


def _block(k):
    nontarget = {
        "person_name": {"pre_answerable": 26, "post_answerable": 18, "n_questions": 27},
        "street": {"pre_answerable": 27, "post_answerable": 0, "n_questions": 27},
    }
    for entry in nontarget.values():
        entry["exposure_rank_this_run"] = 1
        entry["value_span_nll_committed_curve"] = 0.5 + k / 100
        entry["delta"] = abs(entry["post_answerable"] - entry["pre_answerable"]) / 27
        entry["over_margin"] = entry["delta"] > MARGIN
    return {
        "target": {
            "successes": SUCCESSES[k],
            "n_questions": 27,
            "wilson_upper_bound": 0.0911 if SUCCESSES[k] == 0 else 0.5,
        },
        "nontarget": nontarget,
        "nontarget_margin": MARGIN,
        "nontarget_over_margin_count": sum(e["over_margin"] for e in nontarget.values()),
        "dialogue": {"pre_this_run": {"adapter_on": PRE_ON, "adapter_off": OFF}},
    }


def _summary():
    return {
        "decision": {
            "kstar": 64,
            "bracket": [32, 64],
            "null_case": False,
            "rebound_after_kstar": False,
            "non_increasing": True,
            "sequence": [[k, SUCCESSES[k]] for k in MEASURED],
        },
        "checkpoints": {str(k): _block(k) for k in MEASURED},
        "committed_k78_read_not_recomputed": {"target_successes": 0, "target_n_questions": 27},
        "curve_agreement_all": True,
        "provenance": {
            str(k): {"git_sha": "abc", "torch": "2.7.1", "device": "mps"} for k in MEASURED
        },
        "prereg_sha256": "p" * 64,
        "curve_sha256": "c" * 64,
    }


def _render(summary=None, curve=None):
    return tables.render(summary or _summary(), curve or _curve(), {"a.json": "x" * 64})


def _row(text, first_cell):
    return next(line for line in text.splitlines() if line.startswith(f"| {first_cell} |"))


def test_unmeasured_checkpoints_print_a_dash_never_an_estimate():
    text = _render()
    for k in (1, 2, 4):
        cells = [c.strip() for c in _row(text, k).split("|")[1:-1]]
        assert cells[3:5] == [tables.DASH, tables.DASH] and cells[6] == tables.DASH


def test_the_rank_stop_row_reads_phase19s_committed_recall_and_marks_kstar():
    text = _render()
    assert "| 78 | 2 |" in text and "| 0/27 | — | " in _row(text, 78)
    assert _row(text, "**64**").split("|")[4].strip() == "0/27"


def test_adaptation_destroyed_is_derived_from_the_gap_not_typed():
    text = _render()
    expected = 1 - (ON[8] - OFF) / (PRE_ON - OFF)
    assert f"{100 * expected:.2f}%" in _row(text, 8)


def test_a_delta_exactly_at_the_margin_is_not_bold_and_is_flagged():
    summary = _summary()
    entry = summary["checkpoints"]["8"]["nontarget"]["person_name"]
    entry.update(pre_answerable=27, post_answerable=19, delta=MARGIN, over_margin=False)
    line = _row(_render(summary), "person_name")
    assert "27→19 (0.296) =" in line and "**27→19" not in line


def test_over_margin_cells_are_bold():
    assert "**27→0 (1.000)**" in _row(_render(), "street")


def test_composition_counts_match_the_fixture_prefix_and_sum_to_k():
    text = _render()
    layers = text.split("### Composition of the ablated prefix, by layer")[1].split("###")[0]
    assert "| 32 | 6 | 6 | 4 | 7 | 4 | 5 | 6 |" in layers
    assert "| 78 | 18 | 12 | 12 | 17 | 10 | 9 | 6 |" in layers
    by_projection = text.split("by projection")[1].split("###")[0]
    for line in by_projection.splitlines():
        if line.startswith("| 64 |"):
            assert sum(int(c) for c in line.split("|")[2:-2]) == 64


def test_the_decision_block_states_the_lag_from_the_records():
    assert "lags the generation zero by at least 14 components" in _render()


def test_a_summary_whose_checkpoints_disagree_with_the_sequence_is_refused():
    summary = _summary()
    del summary["checkpoints"]["16"]
    with pytest.raises(SystemExit, match="sequence"):
        _render(summary)


def test_a_short_prefix_is_refused():
    curve = _curve()
    curve["ordered_prefix"] = curve["ordered_prefix"][:60]
    with pytest.raises(SystemExit, match="fewer than"):
        _render(curve=curve)


def test_pre_ablation_gaps_that_disagree_are_refused():
    summary = _summary()
    summary["checkpoints"]["32"]["dialogue"]["pre_this_run"]["adapter_on"] += 0.01
    with pytest.raises(SystemExit, match="pre-ablation"):
        _render(summary)


def test_the_output_opens_with_the_sha256_of_its_sources():
    assert _render().splitlines()[0].count("sha256") == 1
    assert "a.json sha256 " + "x" * 64 in _render().splitlines()[0]


def test_the_committed_records_render():
    summary_path, curve_path = tables.SUMMARY_PATH, tables.CURVE_PATH
    if not (summary_path.exists() and curve_path.exists()):
        pytest.skip("the committed k* records are not in this tree")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    curve = json.loads(curve_path.read_text(encoding="utf-8"))
    text = tables.render(
        summary, curve, {p.name: tables._sha256(p) for p in (summary_path, curve_path)}
    )
    for k, successes in summary["decision"]["sequence"]:
        assert f"| {successes}/27 |" in _row(text, k) or f"| {successes}/27 |" in _row(
            text, f"**{k}**"
        )


def test_a_counter_that_disagrees_with_its_own_cells_is_refused():
    summary = _summary()
    summary["checkpoints"]["16"]["nontarget_over_margin_count"] += 1
    with pytest.raises(SystemExit, match="its own cells"):
        _render(summary)


def test_the_instrument_table_reads_recall_rank_and_nll_from_the_summary():
    text = _render()
    section = text.split("by instrument")[1].split("###")[0]
    assert "| street | 0/27 · r1 · 0.58 |" in section


def test_nll_decreases_and_off_ceiling_ranks_are_generated_from_the_records():
    assert "adjacent curve checkpoints (unrounded): none" in _render()
    assert "measured k: none" in _render()
    curve = _curve()
    curve["checkpoints"][1]["slots"]["person_name"]["ans1_mean_nll"] = 0.1
    assert "person_name, k 1→2:" in _render(curve=curve)
    summary = _summary()
    summary["checkpoints"]["32"]["nontarget"]["street"]["exposure_rank_this_run"] = 2
    assert "street at k = 32: rank 2" in _render(summary)
