"""Guards for `scripts/erasure_kstar_figure.py`.

Synthetic records with the shapes the pipeline writes test the drawing logic; the last test renders
the COMMITTED records and requires the committed figure, if present, to equal that render.
"""

import json
import pathlib
import sys
import xml.etree.ElementTree as ET

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import erasure_kstar_figure as fig  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"
KS = [1, 2, 4, 8, 16, 32, 64, 78]
MEASURED = (8, 16, 32, 64)
TARGET = [24, 18, 2, 0]
SLOTS = ["birth_year", "cat_name", "street"]
RECALL = {"birth_year": [14, 13, 14, 11], "cat_name": [27, 27, 27, 6], "street": [27, 24, 11, 0]}


def _records(curve_ranks=False):
    rows = []
    for i, k in enumerate(KS):
        slots = {s: {"ans1_mean_nll": 0.5 + i / 4 + j / 10} for j, s in enumerate(SLOTS)}
        slots["pet_name"] = {"ans1_mean_nll": 0.2 + i / 2}
        if curve_ranks:
            for entry in slots.values():
                entry["rank"] = 1
        rows.append({"prefix": k, "target_rank": 2 if k == 78 else 1, "slots": slots})
    curve = {"k": 78, "slot": "pet_name", "checkpoints": rows}
    summary = {
        "decision": {"bracket": [32, 64], "sequence": [[k, s] for k, s in zip(MEASURED, TARGET)]},
        "checkpoints": {
            str(k): {
                "target": {"successes": TARGET[i], "n_questions": 27},
                "nontarget": {
                    s: {"post_answerable": RECALL[s][i], "exposure_rank_this_run": 1} for s in SLOTS
                },
            }
            for i, k in enumerate(MEASURED)
        },
        "committed_k78_read_not_recomputed": {"target_successes": 0, "target_n_questions": 27},
    }
    resweep = {
        "ordering_is_reference_set_invariant": True,
        "runs": {
            "reference_set_for": {"k": 78, "reference_set_size": 8},
            "reference_set_for_calibration": {"k": 120, "reference_set_size": 6},
        },
    }
    return curve, summary, resweep


def _root(**kwargs):
    return ET.fromstring(fig.render(fig.collect(*_records(**kwargs))))


def test_the_svg_parses_and_has_three_panels():
    root = _root()
    assert [g.get("id") for g in root.iter(f"{SVG}g")] == ["panel-a", "panel-b", "panel-c"]


def test_panel_c_plots_the_target_at_five_points_and_each_nontarget_at_four():
    root = _root()
    panel_c = next(g for g in root.iter(f"{SVG}g") if g.get("id") == "panel-c")
    target = next(e for e in panel_c if e.get("class") == "target")
    assert len(target.get("points").split()) == 5
    nontargets = [e for e in panel_c if e.get("class") == "nontarget"]
    assert sorted(e.get("data-slot") for e in nontargets) == SLOTS
    assert all(len(e.get("points").split()) == 4 for e in nontargets)


def test_panel_a_plots_every_slot_at_the_eight_curve_checkpoints():
    panel_a = next(g for g in _root().iter(f"{SVG}g") if g.get("id") == "panel-a")
    target = next(e for e in panel_a if e.get("class") == "target")
    assert len(target.get("points").split()) == len(KS)


def test_the_committed_record_point_is_hollow_and_the_measured_ones_are_filled():
    panel_c = next(g for g in _root().iter(f"{SVG}g") if g.get("id") == "panel-c")
    fills = [e.get("fill") for e in panel_c if e.get("class") == "target-point"]
    assert fills == [fig.TARGET_COLOR] * 4 + ["white"]


def test_the_stops_and_the_bracket_come_from_the_records():
    root = _root()
    stops = [
        (int(e.get("data-k")), int(e.get("data-candidates")))
        for e in root.iter(f"{SVG}line")
        if e.get("class") == "rank-stop"
    ]
    assert stops == [(78, 8), (120, 6)]
    band = next(e for e in root.iter(f"{SVG}rect") if e.get("class") == "bracket")
    assert (band.get("data-low"), band.get("data-high")) == ("32", "64")


def test_the_render_is_deterministic():
    assert fig.render(fig.collect(*_records())) == fig.render(fig.collect(*_records()))


def test_nontarget_ranks_come_from_the_curve_when_it_records_them_else_from_the_extension():
    assert fig.collect(*_records())["rank_source"] == "extension"
    assert fig.collect(*_records(curve_ranks=True))["rank_source"] == "curve"


def test_a_summary_that_disagrees_with_its_decision_is_refused():
    curve, summary, resweep = _records()
    del summary["checkpoints"]["16"]
    with pytest.raises(SystemExit, match="decision"):
        fig.collect(curve, summary, resweep)


def test_a_resweep_whose_ordering_is_not_invariant_is_refused():
    curve, summary, resweep = _records()
    resweep["ordering_is_reference_set_invariant"] = False
    with pytest.raises(SystemExit, match="invariant"):
        fig.collect(curve, summary, resweep)


def test_a_measured_checkpoint_on_a_stop_is_refused():
    curve, summary, resweep = _records()
    resweep["runs"]["reference_set_for"]["k"] = 64
    curve["k"] = 64
    with pytest.raises(SystemExit, match="sits on a stop"):
        fig.collect(curve, summary, resweep)


def test_the_committed_figure_equals_what_the_committed_records_render():
    paths = (fig.CURVE_PATH, fig.SUMMARY_PATH, fig.RESWEEP_PATH)
    if not all(p.exists() for p in paths):
        pytest.skip("the committed records are not in this tree")
    records = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    rendered = fig.render(fig.collect(*records))
    committed = _ROOT / "paper" / "figure1_three_instruments.svg"
    if not committed.exists():
        pytest.skip("the figure is not committed yet")
    assert committed.read_text(encoding="utf-8") == rendered, (
        "regenerate it with `python scripts/erasure_kstar_figure.py > "
        "paper/figure1_three_instruments.svg`"
    )
