"""Plan 36-06: the v6.0 MPS budget derivation, HALT and cut table, and the fill chain (COST-02).

CPU-only, never MPS. The planted probe records are produced by the REAL producer chain: planted run
sidecars -> ``phase36_probe.emit`` -> ``build_record`` -> ``_write_record`` into tmp, so a
consumer/producer shape drift goes red here. Nothing is written under the real results/ or ledger/.
"""

import ast
import copy
import datetime
import json
import math
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_budget  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)
import phase36_probe as probe  # noqa: E402  (same)

from test_phase29_prereg import _git  # noqa: E402

FRONTS = phase35_prereg.V6_MPS_FRONTS
HEAD = _git("rev-parse", "HEAD")
_UTC = datetime.timezone.utc
# Each front's planted provenance.run span (seconds); P is their sum.
SPANS = {"e5": 60, "e6": 120, "e3": 600, "e2": 900, "e1": 1800}
P = sum(SPANS.values())
# Dyadic stand-ins for the record-priced minutes, so every front's seconds are exact floats.
_PRICED = {
    "results/phase19_collateral_curve.json": (("wall_clock_min",), 7.0),
    "results/phase19_calibration_curve.json": (("wall_clock_min",), 7.0),
    "results/phase19_arm_cal-erased.json": (("config", "wall_clock_min"), 10.5),
}


# =================================================================================================
# Planted records through the REAL producer chain
# =================================================================================================


def _e1_rows(at_cap):
    """Two questions x K = 48 draws of 42 s each (4032 s per run); at-cap draws marked."""
    first = [{"seconds": 42.0, "tokens": 3, "at_cap": False} for _ in range(96)]
    second = [dict(r) for r in first]
    if at_cap:  # run 1: two at-cap draws in question 0 (median 42, max 43); run 2: one of 42
        first[0] = {"seconds": 41.0, "tokens": 4, "at_cap": True}
        first[1] = {"seconds": 43.0, "tokens": 4, "at_cap": True}
        second[48] = {"seconds": 42.0, "tokens": 4, "at_cap": True}
    return first, second


def _planted_stages(e1_totals, at_cap):
    first, second = _e1_rows(at_cap)
    runs = [
        probe._e1_run(total, rows, 2, 48)
        for total, rows in zip(e1_totals, (first, second), strict=True)
    ]
    spread = {"n": 24, "min": 0.0625, "median": 0.125, "max": 0.25}
    return {
        "e1": {
            "configuration": {
                "arm": "erased",
                "k": 78,
                "K": 48,
                "k16": 16,
                "questions": 2,
                "seed": 1337,
                "ordering": "planted",
                "target_slot": "pet_name",
                "adapter_in_sha256": "0" * 64,
                "components_sha256": "0" * 64,
                "e1_targets": 4,
                "e1_teaching_seeds": 2,
            },
            "runs": runs,
        },
        "e2": {
            "configuration": {"arm": "retrain", "n_facts_real": 9, "n_facts_m2": 8, "K": 4},
            "train_reps": [
                {"outer_seconds": 96.0, "loop_seconds": 80.0, "overhead_seconds": 16.0},
                {"outer_seconds": 100.0, "loop_seconds": 82.0, "overhead_seconds": 18.0},
            ],
            "a2_pass": {
                "total_seconds": 2800.0,
                "fixed_seconds": 2778.0,
                "draws": 8,
                "draws_per_question": 4,
                "draw_seconds": [1.0, 2.0, 1.0, 2.0, 4.0, 4.0, 4.0, 4.0],
                "draw_seconds_spread": {"n": 8, "min": 1.0, "median": 3.0, "max": 4.0},
            },
        },
        "e3": {
            "configuration": {"point_key": phase36_prereg.E3_PROBE_POINT_KEY, "batch": 8},
            "t_step_budget": {
                "train_seconds": 208.0,
                "loop_seconds": 200.0,
                "overhead_seconds": 8.0,
                "steps": 200,
                "score_seconds": 1250.0,
                "score_draws": 18,
                "score_draws_per_question": 9,
                "score_fixed_seconds": 1223.0,
                "score_draw_seconds": [1.0] * 9 + [2.0] * 9,
            },
            "t_max_steps": {
                "train_seconds": 916.0,
                "loop_seconds": 900.0,
                "overhead_seconds": 16.0,
                "steps": 800,
            },
        },
        "e5": {
            "configuration": {"slots": 8, "questions_per_slot": 13},
            "clearance": {
                "setup_seconds": 16.0,
                "per_slot_seconds": [12.0] * 7 + [14.0],
                "match_seconds_spread": spread,
                "candidates_matched": 24,
                "total_seconds": 128.0,
            },
            "scoring": {
                "adapters": [
                    {
                        "k": 0,
                        "setup_seconds": 4.0,
                        "per_slot_mean_candidate_seconds": [0.125] * 7 + [0.25],
                        "candidates_per_slot": [10] * 7 + [12],
                        "candidates": 82,
                    },
                    {
                        "k": 78,
                        "setup_seconds": 6.0,
                        "per_slot_mean_candidate_seconds": [0.125] * 8,
                        "candidates_per_slot": [10] * 8,
                        "candidates": 80,
                    },
                ],
                "candidate_seconds_spread": spread,
            },
        },
        "e6": {
            "configuration": {"arm": "erased", "k": 78, "K": 48, "anchor_slots": 8},
            "setup_seconds": 8.0,
            "per_slot_draw_seconds_mean": [0.25] * 7 + [0.5],
            "draws": 384,
            "at_cap_draws": 0,
            "draw_seconds_spread": spread,
            "total_seconds": 200.0,
        },
    }


def _plant(root, *, e1_totals=(4096.0, 4064.0), at_cap=True, device="mps"):
    """Planted sidecars -> the REAL phase36_probe.emit (build_record + _write_record) in tmp."""
    start = datetime.datetime(2026, 10, 2, tzinfo=_UTC)
    records = {}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(probe, "_ROOT", root)
        mp.setattr(probe, "refuse_if_dirty", lambda **kw: "")
        for front, stages in _planted_stages(e1_totals, at_cap).items():
            run = {
                "front": front,
                "run_id": phase36_ledger.run_id(36, "probes", front),
                "run_git_sha": HEAD,
                "device": device,
                "torch_version": "planted",
                "started_utc": start.isoformat(),
                "finished_utc": (start + datetime.timedelta(seconds=SPANS[front])).isoformat(),
                "reused": {front: False},
                "stages": stages,
            }
            sidecar = probe.run_sidecar(front)
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            sidecar.write_text(json.dumps(run), encoding="utf-8")
            probe.sessions_sidecar(front).write_text(
                json.dumps([{"git_sha": HEAD, "started_utc": start.isoformat()}]),
                encoding="utf-8",
            )
        for front in phase36_prereg.PROBE_FRONTS:
            out = root / "emitted" / f"phase36_probe_{front}.json"
            probe.emit(front, out_path=out)
            records[front] = json.loads(out.read_text(encoding="utf-8"))
    return records


@pytest.fixture(scope="module")
def planted(tmp_path_factory):
    return _plant(tmp_path_factory.mktemp("planted"))


def _real_historical():
    """The committed historical records, read straight from the files."""
    out = {}
    for rel in phase36_budget.HISTORICAL_RECORDS:
        text = (_ROOT / rel).read_text(encoding="utf-8")
        out[rel] = text if rel.endswith(".md") else json.loads(text)
    return out


def _historical():
    """The real historical records with the three priced minutes replaced by dyadic stand-ins."""
    out = copy.deepcopy(_real_historical())
    for rel, (key, value) in _PRICED.items():
        node = out[rel]
        for part in key[:-1]:
            node = node[part]
        node[key[-1]] = value
    canary_path, canary_key = phase36_prereg.ENTRIES["e4_canary_scoring_price"]["value"]
    node = out[canary_path]
    for part in canary_key[:-1]:
        node = node[part]
    node[canary_key[-1]] = 5556.25
    return out


def _derive(records, **kw):
    kw.setdefault("probes_spent_seconds", float(P))
    return phase36_budget.derive(copy.deepcopy(records), _historical(), **kw)


# Hand-computed front seconds on the planted records (every term exact in binary floating point).
_E1_K48, _E1_K16 = 4096.0, 64.0 + 2 * 16 * 42.0  # max run total; max fixed + first 16 draws
_EXPECTED_SECONDS = {
    "R1b": _E1_K48,
    # 16 cells x (7 min ordering + 5 x K = 16 + 1 x K = 48) + 4 calibrations x (M2 + 7 + 10.5 min)
    "E1": 16 * (420.0 + 5 * _E1_K16 + 1 * _E1_K48) + 4 * (100.0 + 420.0 + 630.0),
    # 5 seeds x (M2 100 + full 82 + 18 x 9/8 + 2 x (2778 + 2 questions x max block 16))
    "E2": 5 * (100.0 + (82.0 + 18.0 * 9 / 8) + 2 * (2778.0 + 2 * 16.0)),
    # 4 recipes x 3 sigmas x (overhead 16 + 800 x 1.125 s/step + (1223 + 2 x 18))
    "E3": 4 * 3 * (16.0 + 800 * 1.125 + (1223.0 + 2 * 18.0)),
    # 3 points x (16 + 200 x 1.125 + 5556.25 canary)
    "E4": 3 * (16.0 + 200 * 1.125 + 5556.25),
    # setup + 8 x 14 + 8 x 512 x 0.25 match + 6 prefixes x (setup 8 + 8 x 512 x 0.25 NLL)
    "E5": 16.0 + 8 * 14.0 + 8 * 512 * 0.25 + 6 * (8.0 + 8 * 512 * 0.25),
    # 7 x (8 + 2 entries x 2016 x 48/48 + (2 + 8) x 12 x 0.25) + 7 x 8 x 48 x 0.5
    "E6": 7 * (8.0 + 2 * 2016.0 * 48 / 48 + (2 + 8) * 12 * 0.25) + 7 * 8 * 48 * 0.5,
}


# =================================================================================================
# Task 1 — derive: comparisons, prices, front hours, stop line, caps, cut table, cuts, rulings
# =================================================================================================


def test_planted_records_carry_the_producer_shape(planted):
    for front, record in planted.items():
        probe.prove_no_reading(record)
        assert record["front"] == front and record["provenance"]["run"]["device"] == "mps"
    clocks = [
        datetime.datetime.fromisoformat(r["provenance"]["run"]["finished_utc"])
        - datetime.datetime.fromisoformat(r["provenance"]["run"]["started_utc"])
        for r in planted.values()
    ]
    assert math.fsum(c.total_seconds() for c in clocks) == P


@pytest.mark.parametrize("front", [f for f in FRONTS if f != "probes"])
def test_derive_front_hours_match_the_hand_computed_formula(planted, front):
    out = _derive(planted)
    assert out["front_hours"][front] == _EXPECTED_SECONDS[front] / 3600


def test_derive_probes_front_is_the_ledger_seconds_lost_attempts_included(planted):
    """W2: P = the five records' clocks; one lost probe attempt of 120 s is in the front."""
    out = _derive(planted, probes_spent_seconds=float(P + 120))
    assert out["front_hours"]["probes"] == (P + 120) / 3600
    assert out["front_hours"]["probes"] != P / 3600
    assert out["total_hours"] == math.fsum(out["front_hours"].values())
    for bad in (-1.0, math.inf, True, "1"):
        with pytest.raises(SystemExit, match="probes_spent_seconds"):
            _derive(planted, probes_spent_seconds=bad)


def test_derive_fits_with_the_stop_line_and_the_exact_total(planted):
    out = _derive(planted)
    assert out["fits"] is True and out["cut_table"] == [] and out["overflow_hours"] is None
    assert list(out["front_hours"]) == list(FRONTS)
    assert all(type(v) is float for v in out["front_hours"].values())
    assert out["total_hours"] == math.fsum(out["front_hours"].values())
    assert out["stop_line_hours"] == min(1.5 * out["total_hours"], 90)
    assert out["e2_seed_count"] == 5 == out["unit_caps"]["E2"]["seeds"]
    assert out["formula"] is phase36_budget.FORMULA
    assert {"R1b", "E1", "E2", "E3", "E4", "E5", "E6", "probes"} <= set(out["formula"])
    assert "NOT re-measured" in out["formula"]["e4_canary_seconds"]
    assert "NOT re-measured" in out["formula"]["e1_ordering_seconds"]
    assert "46.6" in out["formula"]["R1b"] and "6.959" in out["formula"]["R1b"]
    json.dumps(out)


def test_derive_unit_prices_and_the_e4_point(planted):
    prices = phase36_budget.unit_prices(planted, _historical())
    assert prices["a2_k48_high"] == 4096.0 and prices["a2_k16_high"] == _E1_K16
    assert prices["a2_question_k48_high"] == 2016.0
    assert prices["e2_a2_pass_high"] == 2778.0 + 2 * 16.0  # H2: the max per-question block
    assert prices["e3_score_high"] == 1223.0 + 2 * 18.0
    assert prices["e3_per_step_high"] == 1.125  # H1 over both runs
    assert prices["e4_canary_seconds"] == 5556.25
    assert prices["e4_point_seconds"] == 16.0 + 200 * 1.125 + 5556.25
    assert prices["e1_k48_seconds"] == prices["a2_k48_high"]
    real = phase36_budget.unit_prices(planted, _real_historical())
    canary = _real_historical()["results/phase26_canary_sources.json"]
    key = phase36_prereg.E3_PROBE_POINT_KEY
    assert real["e4_canary_seconds"] == canary["points"][key]["provenance"]["scoring_seconds"]
    assert real["e1_ordering_seconds"] == 60 * 6.959359816710154


def test_derive_prices_e1_and_surfaces_an_e6_record_beside_another_e1(planted, monkeypatch, capsys):
    """WR-01: E6 is emitted (write-once) before E1, so an E1 re-probe after E6 is committed leaves
    E6's copy stale forever. The budget prices the E1 record (authoritative) and surfaces the
    mismatch for Rafael rather than refusing."""
    records = copy.deepcopy(planted)
    records["e6"]["a2_context_from_e1"]["a2_context_question_k48_seconds_high"] = 2015.0
    out = _derive(records)
    assert _derive(planted)["a2_context_mismatch"] is None
    assert out["a2_context_mismatch"] == {"e6_record": 2015.0, "e1_record": 2016.0}
    assert out["unit_prices"]["a2_question_k48_high"] == 2016.0
    assert out["front_hours"] == _derive(planted)["front_hours"]
    _committed_inputs(monkeypatch, records)
    phase36_budget.dry()
    assert '[phase36_budget] a2_context_mismatch: {"e1_record": 2016.0' in capsys.readouterr().out
    del records["e1"]
    with pytest.raises(SystemExit, match="exactly"):
        _derive(records)


def test_derive_refuses_a_record_off_the_probe_device(planted, tmp_path):
    cpu = _plant(tmp_path, device="cpu")
    with pytest.raises(SystemExit, match="ran on 'cpu', not 'mps'"):
        _derive(cpu)
    with pytest.raises(SystemExit, match="keyed by exactly"):
        _derive({f: r for f, r in planted.items() if f != "e5"})
    historical = _historical()
    del historical["results/phase25_recall.json"]
    with pytest.raises(SystemExit, match="historical records missing"):
        phase36_budget.derive(planted, historical, probes_spent_seconds=0.0)


def test_divergence_rows_follow_the_comparator_entry(planted):
    rows = phase36_budget.comparisons(planted, _historical())
    ids = [r["id"] for r in rows]
    entry = phase36_prereg.ENTRIES["divergence_comparators"]["value"]
    expected = []
    for row in entry:
        if row["id"] == "r1b_e1_k48":
            expected += ["r1b_e1_k48#1", "r1b_e1_k48#2"]
        elif row["probe_field"] is not None:
            expected.append(row["id"])
    assert ids == expected
    assert not [i for i in ids if i.startswith("e1_phase31_beside")]
    by = {r["id"]: r for r in rows}
    assert by["r1b_e1_k48#1"]["historical_seconds"] == 60 * 68.58400233189265
    assert by["r1b_e1_k48#2"]["probe_seconds"] == 4064.0
    assert by["e5_clearance"]["historical_seconds"] == 2.1 * 60  # the markdown regex
    assert by["e3_t800_linearity"]["historical_seconds"] == 800 / 200 * 200.0
    assert by["e3_t800_linearity"]["probe_seconds"] == 900.0
    assert by["e2_training_context"]["probe_seconds"] == 100.0
    floor = _historical()["results/phase23_control_floor.json"]["per_seed"]
    assert by["e2_training_context"]["historical_seconds"] == max(
        s["training_seconds"] for s in floor
    )
    assert by["e2_training_context"]["gated"] is False
    for r in rows:
        assert r["divergence"] == phase36_prereg.divergence(
            r["probe_seconds"], r["historical_seconds"]
        )
        assert r["exceeds"] is False  # the planted set sits inside the tolerance


def test_divergence_r1b_thirty_percent_slower_refuses_until_a_finding(tmp_path):
    slow = _plant(tmp_path, e1_totals=(1.3 * 4115.04, 4064.0))
    with pytest.raises(SystemExit, match=r"r1b_e1_k48#1.*D-02/D-04: investigate BEFORE"):
        _derive(slow)
    finding = "R1b: the slower first run includes warm-up (planted finding)"
    out = _derive(slow, divergences_investigated={"r1b_e1_k48": finding})
    assert out["divergences_investigated"] == {"r1b_e1_k48": finding}
    assert next(r for r in out["comparisons"] if r["id"] == "r1b_e1_k48#1")["exceeds"]
    with pytest.raises(SystemExit, match="unknown comparator"):
        _derive(slow, divergences_investigated={"r1b": finding})
    with pytest.raises(SystemExit, match="is empty"):
        _derive(slow, divergences_investigated={"r1b_e1_k48": " "})


def test_divergence_an_ungated_comparator_never_refuses(planted):
    records = copy.deepcopy(planted)
    for rep in records["e2"]["stages"]["train_reps"]:
        rep["outer_seconds"] = 400.0
    out = _derive(records)
    row = next(r for r in out["comparisons"] if r["id"] == "e2_training_context")
    assert row["exceeds"] is True and row["gated"] is False


def test_halt_over_the_ceiling_returns_the_cut_table_in_cut_order(planted):
    out = _derive(planted, probes_spent_seconds=150000.0)
    assert out["fits"] is False and out["stop_line_hours"] is None
    assert out["overflow_hours"] == out["total_hours"] - 90
    order = phase36_prereg.ENTRIES["cut_order"]["value"]
    ids = [r["id"] for r in out["cut_table"]]
    assert ids == list(order) and ids[-2:] == ["r1b", "e1_core"]
    for row in out["cut_table"]:
        assert set(row) == {
            "id",
            "unit",
            "hours_per_unit",
            "max_units",
            "hours_saved_max",
            "question_lost",
        }
        assert row["question_lost"].strip() and row["max_units"] >= 1
        assert row["hours_saved_max"] == row["hours_per_unit"] * row["max_units"]
    rows = {r["id"]: r for r in out["cut_table"]}
    hours = out["front_hours"]
    assert rows["e1_checkpoints"]["max_units"] == 5 - 1
    assert rows["e1_checkpoints"]["hours_per_unit"] == 16 * _E1_K16 / 3600
    assert rows["e4_reserve"]["hours_per_unit"] == hours["E4"]
    assert rows["r1b"]["hours_per_unit"] == hours["R1b"]
    assert rows["e1_core"]["hours_per_unit"] == hours["E1"] - 4 * 16 * _E1_K16 / 3600
    assert "D-14" in rows["e2_seeds_to_3"]["unit"] and "to 3" in rows["e2_seeds_to_3"]["unit"]
    assert "e3_grid_subset" in rows["e3_whole"]["question_lost"]
    assert "e1_checkpoint_grid" in rows["e1_core"]["question_lost"]
    # Nothing is applied: the caps are the proposal's.
    assert out["cuts_applied"] == {}
    assert out["unit_caps"] == phase36_budget.proposed_unit_caps(planted)
    direct = phase36_budget.cut_table(
        out["unit_prices"], out["unit_caps"], out["front_hours"], out["total_hours"]
    )
    assert direct == out["cut_table"]


def test_halt_cut_table_rows_are_a_subsequence_after_rulings(planted):
    out = _derive(
        planted, probes_spent_seconds=200000.0, cuts={"e4_reserve": 1, "e2_seeds_to_3": 1}
    )
    ids = [r["id"] for r in out["cut_table"]]
    order = list(phase36_prereg.ENTRIES["cut_order"]["value"])
    assert ids == [i for i in order if i in ids]
    assert "e4_reserve" not in ids and "e2_seeds_to_3" not in ids  # S already 3: no S < 3 row
    assert out["e2_seed_count"] == 3


@pytest.mark.parametrize(
    ("cuts", "check"),
    [
        ({"e4_reserve": 1}, lambda o: o["front_hours"]["E4"] == 0),
        ({"e3_whole": 1}, lambda o: o["front_hours"]["E3"] == 0),
        ({"e2_seeds_to_3": 1}, lambda o: o["e2_seed_count"] == 3),
        ({"e1_checkpoints": 2}, lambda o: o["unit_caps"]["E1"]["checkpoints_per_cell"] == 3),
        ({"r1b": 1}, lambda o: o["front_hours"]["R1b"] == 0),
        (
            {"e1_core": 1},
            lambda o: (
                o["front_hours"]["E1"] == 0
                and o["unit_caps"]["E1"]["cells"] == 0
                and o["unit_caps"]["E1"]["calibrations"] == 0
            ),
        ),
        ({"e6_anchor_adapters": 7}, lambda o: o["unit_caps"]["E6"]["anchor_adapters"] == 0),
    ],
)
def test_cut_applied_only_by_a_ruling(planted, cuts, check):
    out = _derive(planted, cuts=cuts)
    assert check(out) and out["cuts_applied"] == cuts
    assert out["total_hours"] == math.fsum(out["front_hours"].values())


def test_cut_refusals(planted):
    for cuts, pattern in (
        ({"e1_checkpoints": 5}, "leaves 0 checkpoints"),
        ({"e6_anchor_adapters": 8}, "leaves -1 adapters"),
        ({"e3": 1}, "is not one of cut_order"),
        ({"e4_reserve": 2}, "takes 1 unit"),
        ({"e4_reserve": 0}, "is not an int >= 1"),
        ({"e4_reserve": True}, "is not an int >= 1"),
    ):
        with pytest.raises(SystemExit, match=pattern):
            _derive(planted, cuts=cuts)
    caps = phase36_budget.proposed_unit_caps(planted)
    caps["E2"]["seeds"] = 3
    with pytest.raises(SystemExit, match="S is already 3"):
        _derive(planted, unit_caps=caps, cuts={"e2_seeds_to_3": 1})
    assert _derive(planted, cuts=None) == _derive(planted, cuts={})
    assert _derive(planted)["unit_caps"] == phase36_budget.proposed_unit_caps(planted)


def test_derive_proposed_caps_follow_d09_and_the_records(planted):
    caps = phase36_budget.proposed_unit_caps(planted)
    assert caps == {
        "E1": {
            "cells": 16,
            "checkpoints_per_cell": 5,
            "k48_confirms_per_cell": 1,
            "calibrations": 4,
        },
        "E2": {"adapters": 2, "seeds": 5},
        "E3": {"recipes": 4, "sigmas": 3, "max_steps": 800, "max_batch": 8},
        "E4": {"points": 3},
        "E5": {"sets": 8, "max_set_size": 512, "prefixes": 6},
        "E6": {"adapters": 7, "anchor_adapters": 7, "anchor_slots": 8, "entries": 2, "max_k": 48},
    }
    assert set(phase36_budget.CAP_DERIVATIONS) == {
        f"{front}.{name}"
        for front, names in phase36_budget.phase36_caps.CAP_FIELDS.items()
        for name in names
    }


def test_derive_refuses_caps_off_the_contract(planted):
    def caps_with(front, name, value):
        caps = phase36_budget.proposed_unit_caps(planted)
        caps[front][name] = value
        return caps

    for front, name, value, pattern in (
        ("E2", "seeds", 2, "below cut_table_min_seeds 3"),
        ("E2", "adapters", 3, "E2 adapters must be 2"),
        ("E3", "max_steps", 801, "above e3_max_steps 800"),
        ("E1", "cells", -1, "is not an int >= 0"),
        ("E1", "cells", 1.0, "is not an int >= 0"),
    ):
        with pytest.raises(SystemExit, match=pattern):
            _derive(planted, unit_caps=caps_with(front, name, value))
    caps = phase36_budget.proposed_unit_caps(planted)
    del caps["E4"]
    with pytest.raises(SystemExit, match="keyed by exactly"):
        _derive(planted, unit_caps=caps)
    caps = phase36_budget.proposed_unit_caps(planted)
    caps["E5"]["extra"] = 1
    with pytest.raises(SystemExit, match="must carry exactly"):
        _derive(planted, unit_caps=caps)


def test_derive_cap_ruling_raises_e3_max_batch(planted):
    caps = phase36_budget.proposed_unit_caps(planted)
    caps["E3"]["max_batch"] = 16
    with pytest.raises(SystemExit, match="above the probed batch 8"):
        _derive(planted, unit_caps=caps)
    ruling = {"E3.max_batch": "Rafael: batch 16 approved (planted)"}
    out = _derive(planted, unit_caps=caps, cap_rulings=ruling)
    assert out["unit_prices"]["e3_per_step_high"] == 1.125 * 16 / 8
    assert out["unit_prices"]["e4_point_seconds"] == 16.0 + 200 * 1.125 + 5556.25  # v4.0 batch
    assert out["cap_rulings"] == ruling
    for bad, pattern in (({"E3.max_steps": "x"}, "is not one of"), ({"E3.max_batch": ""}, "empty")):
        with pytest.raises(SystemExit, match=pattern):
            _derive(planted, unit_caps=caps, cap_rulings=bad)


def test_derive_price_rulings_swap_in_each_alternative(planted):
    default = _derive(planted)
    at_cap = _derive(planted, price_rulings={"a2_draw_basis": "at_cap"})
    # The MAX at-cap draw (43 s), never the median (42 s): run 1's fixed cost is the larger.
    spread = planted["e1"]["stages"]["runs"][0]["at_cap_seconds_spread"]
    assert (spread["median"], spread["max"]) == (42.0, 43.0)
    fixed = max(r["fixed_seconds"] for r in planted["e1"]["stages"]["runs"])
    assert fixed == 4096.0 - 4032.0
    k48, k16 = fixed + 2 * 48 * 43.0, fixed + 2 * 16 * 43.0
    assert at_cap["unit_prices"]["e1_k48_seconds"] == k48
    assert at_cap["unit_prices"]["e1_k16_seconds"] == k16
    assert (
        at_cap["front_hours"]["E1"]
        == (16 * (420.0 + 5 * k16 + 1 * k48) + 4 * (100.0 + 420.0 + 630.0)) / 3600
    )
    assert at_cap["front_hours"]["R1b"] == default["front_hours"]["R1b"]  # the k = 78 reading
    assert at_cap["front_hours"]["E6"] == default["front_hours"]["E6"]
    assert at_cap["price_rulings"] == {"a2_draw_basis": "at_cap"}

    ratio = 4096.0 / 4064.0
    scaled = _derive(planted, price_rulings={"single_run_draw_loop": "spread_scaled"})
    assert scaled["unit_prices"]["e2_a2_pass_high"] == 2800.0 * ratio
    assert scaled["unit_prices"]["e3_score_high"] == 1250.0 * ratio

    probe_scaled = _derive(planted, price_rulings={"e1_calibration": "probe_scaled"})
    erased = 60 * 68.58400233189265
    assert probe_scaled["unit_prices"]["e1_calibration_seconds"] == 100.0 + 60 * (7.0 + 10.5) * (
        4096.0 / erased
    )
    defaults = {name: pair[0] for name, pair in phase36_budget.RULING_ALTERNATIVES.items()}
    assert _derive(planted, price_rulings=defaults)["front_hours"] == default["front_hours"]


def test_derive_price_ruling_refusals(planted, tmp_path):
    for rulings, pattern in (
        ({"draw_basis": "at_cap"}, "is not one of"),
        ({"a2_draw_basis": "median"}, "is neither"),
    ):
        with pytest.raises(SystemExit, match=pattern):
            _derive(planted, price_rulings=rulings)
    no_cap = _plant(tmp_path, at_cap=False)
    assert phase36_budget.price_alternatives(no_cap, _historical())["a2_draw_basis"] == {
        "at_cap": None
    }
    with pytest.raises(SystemExit, match="unavailable: no at-cap draw"):
        _derive(no_cap, price_rulings={"a2_draw_basis": "at_cap"})
    prices = phase36_budget.unit_prices(planted, _historical())
    alternatives = {"e1_calibration": {"probe_scaled": {"not_a_price": 1.0}}}
    with pytest.raises(SystemExit, match="replaces unknown prices"):
        phase36_budget.apply_price_rulings(prices, alternatives, {"e1_calibration": "probe_scaled"})


def test_derive_runs_without_torch(planted, tmp_path):
    blob = tmp_path / "inputs.json"
    blob.write_text(json.dumps({"probes": planted, "historical": _historical()}), encoding="utf-8")
    code = (
        "import sys, json; sys.path[:0] = ['scripts', 'src']; import phase36_budget as b; "
        f"d = json.loads(open({str(blob)!r}).read()); "
        "out = b.derive(d['probes'], d['historical'], probes_spent_seconds=1.0); "
        "print(out['fits'], 'torch' in sys.modules)"
    )
    done = subprocess.run([sys.executable, "-c", code], cwd=_ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["True", "False"], done.stdout


def test_derive_small_helpers():
    assert phase36_budget._is_count(0) and not phase36_budget._is_count(True)
    assert not phase36_budget._is_count(-1) and not phase36_budget._is_count(1.0)
    assert phase36_budget._at({"a": [{"b": 1}, {"b": 2}]}, ("a", "*", "b")) == [1, 2]
    assert phase36_budget._h2(12.0, 4, 2, [1.0, 2.0, 5.0, 1.0]) == 12.0 + 2 * 6.0
    with pytest.raises(SystemExit, match="draw seconds for"):
        phase36_budget._h2(1.0, 3, 2, [1.0, 1.0, 1.0])
    with pytest.raises(SystemExit, match=r"^\[phase36_budget\] boom$"):
        phase36_budget._prove(False, "boom")
    row = {"historical_path": "x.md", "historical_key": r"wall `([0-9.]+)` min", "unit": "min"}
    assert phase36_budget._historical_seconds(row, {"x.md": "wall `2.5` min"}) == 150.0
    with pytest.raises(SystemExit, match="no match"):
        phase36_budget._historical_seconds(row, {"x.md": "nothing"})


def test_derive_private_steps_match_derive(planted):
    caps = phase36_budget.proposed_unit_caps(planted)
    phase36_budget._prove_caps(caps, {}, 8)
    prices = phase36_budget.unit_prices(planted, _historical())
    seconds = phase36_budget._front_seconds(prices, caps, False)
    assert seconds == _EXPECTED_SECONDS
    assert phase36_budget._front_seconds(prices, caps, True)["R1b"] == 0.0
    assert phase36_budget._apply_cuts(caps, {"r1b": 1}) is True
    assert phase36_budget._apply_cuts(caps, {}) is False


# =================================================================================================
# Task 2 — committed inputs, the fill chain, dry, emit, recompute, ancestry
# =================================================================================================

import phase30_points  # noqa: E402  (scripts/ is not a package)

from test_phase29_prereg import _assert_frozen_before  # noqa: E402
from test_phase36_prereg import _untested_functions  # noqa: E402
from test_phase36_probe import _live_run  # noqa: E402

BUDGET = phase36_budget.BUDGET_RECORD
LEDGER = phase36_ledger.LEDGER_PATH
RECORDS = phase36_prereg.PROBE_RECORDS
HALT_MESSAGE = (
    "[phase35_prereg] the fronts do not fit Rafael's MPS ceiling: HALT and take the cut options "
    "to Rafael (COST-02); no front is cut unilaterally"
)


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """emit refuses a dirty tree and this suite runs on dirty trees, so the guard is RECORDED."""
    calls = []
    monkeypatch.setattr(phase36_budget, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


def _tracked():
    return phase36_budget.phase36_caps.tracked_files()


def _phase36_results_state():
    return (
        _git("status", "--porcelain", "--untracked-files=all", "--", "results/phase36_*"),
        sorted(p.name for p in (_ROOT / "results").glob("phase36_*")),
    )


def _committed_inputs(monkeypatch, records, spent=float(P)):
    """The committed-file loaders replaced by the planted records (no probe record exists yet)."""
    monkeypatch.setattr(phase36_budget, "probe_record_paths", lambda tracked=None: RECORDS)
    monkeypatch.setattr(phase36_budget, "load_probes", lambda tracked: copy.deepcopy(records))
    monkeypatch.setattr(phase36_budget, "load_historical", lambda tracked: _historical())
    monkeypatch.setattr(phase36_budget, "ledger_probes_seconds", lambda tracked: spent)


def _clock(record):
    run = record["provenance"]["run"]
    return (
        datetime.datetime.fromisoformat(run["finished_utc"])
        - datetime.datetime.fromisoformat(run["started_utc"])
    ).total_seconds()


def test_load_historical_reads_the_committed_records():
    assert phase36_budget.load_historical(_tracked()) == _real_historical()
    assert "results/phase31_probe_point.json" not in phase36_budget.HISTORICAL_RECORDS


def test_head_blob_reads_head_and_refuses_untracked():
    rel = "results/phase17_personas_report.md"
    assert phase36_budget._head_blob(rel, _tracked()) == (_ROOT / rel).read_bytes()
    with pytest.raises(SystemExit, match="is not TRACKED"):
        phase36_budget._head_blob(rel, [])


def test_ledger_blob_is_the_committed_ledger():
    """Honest in both states: the ledger is committed by the probe run's emit-all (36-07)."""
    tracked = _tracked()
    if LEDGER in tracked:
        assert (
            phase36_budget._ledger_blob(tracked)
            == subprocess.run(
                ["git", "show", f"HEAD:{LEDGER}"], cwd=_ROOT, capture_output=True, check=True
            ).stdout
        )
    else:
        with pytest.raises(SystemExit, match="is not TRACKED"):
            phase36_budget._ledger_blob(tracked)


def test_probe_record_paths_refuses_a_partial_set_naming_the_fronts():
    assert phase36_budget.probe_record_paths(list(RECORDS)) == RECORDS
    with pytest.raises(SystemExit, match=r"fronts \['e3', 'e6'\]"):
        phase36_budget.probe_record_paths([r for r in RECORDS if "_e3" not in r and "_e6" not in r])
    tracked = _tracked()
    if all(r in tracked for r in RECORDS):
        assert phase36_budget.probe_record_paths() == RECORDS
    else:
        with pytest.raises(SystemExit, match="probe records missing for fronts"):
            phase36_budget.probe_record_paths()


def test_load_probes_reads_each_record_through_tracked_json(planted, monkeypatch):
    by_path = {phase36_prereg.probe_record(f): r for f, r in planted.items()}
    seen = []

    def committed(rel, tracked, what):
        seen.append(rel)
        return by_path[rel]

    monkeypatch.setattr(phase30_points, "_tracked_json", committed)
    assert phase36_budget.load_probes(list(RECORDS)) == planted
    assert sorted(seen) == sorted(RECORDS)


def _ledger_text(lines):
    out = []
    for fields in lines:
        line = dict.fromkeys(phase36_ledger.LINE_FIELDS)
        line.update(fields)
        out.append(json.dumps(line, sort_keys=True))
    return ("\n".join(out) + "\n").encode("utf-8")


def test_ledger_probes_seconds_counts_the_lost_attempt(planted, monkeypatch):
    """W2: two probe end lines (their records' clocks) + one lost probe line of 120 s; an OPEN
    line of another front is out of scope and does not refuse."""
    e5, e6 = phase36_prereg.probe_record("e5"), phase36_prereg.probe_record("e6")
    rid = {f: phase36_ledger.run_id(36, "probes", f) for f in ("e5", "e6", "e3")}
    utc = "2026-10-02T00:00:00+00:00"
    blob = _ledger_text(
        [
            {"utc": utc, "event": "start", "run_id": rid["e5"], "phase": 36, "front": "probes"},
            {"utc": utc, "event": "end", "run_id": rid["e5"], "phase": 36, "front": "probes"}
            | {"record": e5},
            {"utc": utc, "event": "start", "run_id": rid["e6"], "phase": 36, "front": "probes"},
            {"utc": utc, "event": "end", "run_id": rid["e6"], "phase": 36, "front": "probes"}
            | {"record": e6},
            {"utc": utc, "event": "start", "run_id": rid["e3"], "phase": 36, "front": "probes"},
            {"utc": utc, "event": "lost", "run_id": rid["e3"], "phase": 36, "front": "probes"}
            | {"seconds": 120.0, "flag": phase36_ledger.LOST_FLAG},
            {"utc": utc, "event": "start", "run_id": "v6/41/E1/x", "phase": 41, "front": "E1"},
        ]
    )
    asked = []
    monkeypatch.setattr(phase36_budget, "_ledger_blob", lambda tracked: asked.append(1) or blob)
    by_path = {e5: planted["e5"], e6: planted["e6"]}
    monkeypatch.setattr(phase30_points, "_tracked_json", lambda rel, tracked, what: by_path[rel])
    seconds = phase36_budget.ledger_probes_seconds([LEDGER, e5, e6])
    assert seconds == SPANS["e5"] + SPANS["e6"] + 120.0
    assert seconds == _clock(planted["e5"]) + _clock(planted["e6"]) + 120.0
    assert asked == [1]
    with pytest.raises(SystemExit, match="is not tracked"):
        phase36_budget.ledger_probes_seconds([e5, e6])
    assert asked == [1]  # refused before any read


def test_committed_derive_and_chosen_on_committed_loaders(planted, monkeypatch):
    _committed_inputs(monkeypatch, planted)
    derived = phase36_budget.committed_derive(RECORDS)
    assert derived == _derive(planted)
    approved = {"approved": "planted"}
    assert phase36_budget.committed_derive(RECORDS, **approved) == derived
    value = phase36_budget.chosen(RECORDS, **approved)
    assert value == {
        "front_hours": derived["front_hours"],
        "stop_line_hours": derived["stop_line_hours"],
        "e2_seed_count": 5,
    }
    assert phase36_budget._fit_value(derived) == value
    with pytest.raises(SystemExit, match="are not the probe records"):
        phase36_budget.committed_derive(RECORDS[:4])


def test_derivation_names_every_input_and_each_override():
    value = {"front_hours": {}, "stop_line_hours": 1.0, "e2_seed_count": 5}
    ruling = {
        "price_rulings": {"a2_draw_basis": "at_cap"},
        "cap_rulings": {"E3.max_batch": "batch 16 approved"},
        "divergences_investigated": {"r1b_e1_k48": "warm-up"},
        "cuts": {"e4_reserve": 1},
        "approved": "approved",
    }
    entry = phase36_budget.derivation(value, RECORDS, **ruling)
    assert set(entry) == set(phase35_prereg.ENTRY_FIELDS) and entry["kind"] == "derived"
    assert entry["value"] is value
    for rel in (*RECORDS, *phase36_budget.HISTORICAL_RECORDS, LEDGER):
        assert rel in entry["source"]
    text = entry["derivation"]
    assert "price ruling a2_draw_basis: at_cap (default k78)" in text
    assert "cap ruling E3.max_batch: batch 16 approved" in text
    assert "finding r1b_e1_k48: warm-up" in text and '"e4_reserve": 1' in text
    assert text.endswith("approved by Rafael: approved")
    assert phase35_prereg.FORBIDDEN_PHRASE not in text + entry["source"]
    assert "the proposal (CAP_DERIVATIONS)" in phase36_budget._describe({})[-2]
    with pytest.raises(SystemExit, match="no approved text"):
        phase36_budget.derivation(value, RECORDS)
    with pytest.raises(SystemExit, match="unknown ruling keys"):
        phase36_budget.derivation(value, RECORDS, approved="x", fill=1)


def test_consumer_fill_chain_on_real_producer_records(tmp_path, monkeypatch):
    """The five records the CPU live run EMITTED through the real phase36_probe.emit ->
    _emit_target -> _write_record (W10) feed derive, the v6.0 fill, the budget record, then
    fill('e2_S') and fill('e1_checkpoint_grid'). DOCUMENTED SUBSTITUTIONS: PROBE_DEVICE = "cpu"
    (CPU fixture runs); probes_spent_seconds = the fsum of the five records' clocks (the no-lost-
    attempt case spent(fronts=('probes',)) returns on a ledger naming exactly these records; the
    lost-attempt case is test_ledger_probes_seconds_counts_the_lost_attempt); a finding for every
    gated comparator (fixture seconds are CPU seconds at fixture scale)."""
    live = _live_run(tmp_path / "live", None)
    repo = tmp_path / "repo"
    (repo / "results").mkdir(parents=True)
    for front, rel in zip(phase36_prereg.PROBE_FRONTS, RECORDS, strict=True):
        emitted = live["root"] / "emitted" / f"phase36_probe_{front}.json"
        (repo / rel).write_bytes(emitted.read_bytes())  # byte for byte
    probes = {
        f: json.loads((repo / rel).read_text(encoding="utf-8"))
        for f, rel in zip(phase36_prereg.PROBE_FRONTS, RECORDS, strict=True)
    }
    assert probes == live["records"]
    monkeypatch.setattr(phase36_budget, "PROBE_DEVICE", "cpu")
    spent = math.fsum(_clock(r) for r in probes.values())
    findings = {
        row["id"]: "fixture: CPU seconds at fixture scale"
        for row in phase36_prereg.ENTRIES["divergence_comparators"]["value"]
        if row["gated"]
    }
    ruling = {"divergences_investigated": findings, "approved": "fixture: CPU live run"}
    historical = phase36_budget.load_historical(_tracked())
    derived = phase36_budget.derive(
        probes, historical, probes_spent_seconds=spent, divergences_investigated=findings
    )
    assert derived["fits"], derived["total_hours"]
    value = phase36_budget._fit_value(derived)

    monkeypatch.setattr(phase35_prereg, "_REPO_ROOT", repo)
    real_fill, filled_slots = phase35_prereg.fill, []
    monkeypatch.setattr(
        phase35_prereg,
        "fill",
        lambda slot, **kw: filled_slots.append(slot) or real_fill(slot, **kw),
    )
    filled = phase35_prereg.fill(
        "v6_budget_and_stop_line",
        **value,
        input_records=RECORDS,
        derivation=phase36_budget.derivation(value, RECORDS, **ruling),
    )
    assert dict(filled["front_hours"]) == derived["front_hours"]
    assert filled["total_hours"] == derived["total_hours"]
    record = phase36_budget.budget_record(filled, derived, ruling)
    assert record["approved"] == ruling["approved"] and "RESOURCE" in record["note"]
    assert record["unit_prices"]["e4_point_seconds"] > 0
    (repo / BUDGET).write_text(json.dumps(record), encoding="utf-8")

    budget_only = (BUDGET,)
    seeds = record["e2_seed_count"]
    s = phase35_prereg.fill(
        "e2_S",
        input_records=budget_only,
        derivation={
            "value": seeds,
            "derivation": "fixture: S read from the budget record",
            "kind": "derived",
            "source": BUDGET,
        },
    )
    assert s == seeds == 5
    checkpoints = tuple(range(1, record["unit_caps"]["E1"]["checkpoints_per_cell"] + 1))
    grid = phase35_prereg.fill(
        "e1_checkpoint_grid",
        checkpoints=checkpoints,
        input_records=budget_only,
        derivation={
            "value": checkpoints,
            "derivation": "fixture: the proposed grid at the cap",
            "kind": "derived",
            "source": BUDGET,
        },
    )
    assert grid["checkpoints"] == checkpoints
    assert filled_slots == ["v6_budget_and_stop_line", "e2_S", "e1_checkpoint_grid"]
    assert phase36_budget.phase36_caps.owner_overruns({"e1_checkpoint_grid": grid}, record) == []


def test_budget_record_refuses_values_off_the_derivation(planted):
    derived = _derive(planted)
    filled = {**phase36_budget._fit_value(derived), "total_hours": derived["total_hours"]}
    filled["e2_seed_count"] = 4
    with pytest.raises(SystemExit, match="is not the derived one"):
        phase36_budget.budget_record(filled, derived, {"approved": "x"})


def test_halt_chain_refuses_and_writes_nothing(planted, monkeypatch):
    before = _phase36_results_state()
    _committed_inputs(monkeypatch, planted, spent=150000.0)
    with pytest.raises(SystemExit, match="HALT: the fronts total") as caught:
        phase36_budget.chosen(RECORDS, approved="x")
    assert "no front is cut unilaterally" in str(caught.value)
    derived = phase36_budget.committed_derive(RECORDS)
    assert derived["fits"] is False and len(derived["cut_table"]) == len(phase36_budget.CUT_ORDER)
    hours = derived["front_hours"]
    with pytest.raises(SystemExit) as caught:
        phase35_prereg.fill(
            "v6_budget_and_stop_line",
            front_hours=hours,
            stop_line_hours=math.fsum(hours.values()),
            e2_seed_count=5,
            input_records=RECORDS,
            derivation={"value": {}, "derivation": "x", "kind": "derived", "source": "x"},
        )
    assert str(caught.value) == HALT_MESSAGE
    assert _phase36_results_state() == before


def _listing():
    return (
        _git("status", "--porcelain", "--untracked-files=all"),
        sorted(p.relative_to(_ROOT).as_posix() for p in (_ROOT / "results").iterdir()),
    )


def test_dry_writes_nothing_and_prints_every_number(planted, monkeypatch, tmp_path, capsys):
    _committed_inputs(monkeypatch, planted)
    before = _listing()
    derived = phase36_budget.dry()
    out = capsys.readouterr().out
    assert derived == _derive(planted)
    assert "[phase36_budget] FITS" in out and "HALT" not in out
    assert out.count("[phase36_budget] comparison:") == len(derived["comparisons"])
    for text in phase36_budget.SURFACED:
        assert json.dumps(text) in out
    for name, (default, alternative) in phase36_budget.RULING_ALTERNATIVES.items():
        assert f"ruling {name}={default}:" in out and f"ruling {name}={alternative}:" in out
    assert "E3 hours at recipes 4:" in out and "E3 hours at recipes 5:" in out
    assert "E3 max_batch:" in out and "front_hours:" in out and "stop_line_hours:" in out
    for name in phase36_budget.CAP_DERIVATIONS:
        assert f"cap {name}:" in out

    ruling = tmp_path / "ruling.json"
    ruling.write_text(
        json.dumps({"price_rulings": {"a2_draw_basis": "at_cap"}, "approved": "x"}),
        encoding="utf-8",
    )
    ruled = phase36_budget.dry(ruling)
    assert ruled["price_rulings"] == {"a2_draw_basis": "at_cap"}
    _committed_inputs(monkeypatch, planted, spent=150000.0)
    halted = phase36_budget.dry()
    out = capsys.readouterr().out
    assert halted["fits"] is False and "HALT:" in out
    assert out.count("[phase36_budget] cut:") == len(phase36_budget.CUT_ORDER)
    assert _listing() == before

    ruling.write_text(json.dumps({"cut": {}}), encoding="utf-8")
    with pytest.raises(SystemExit, match="unknown ruling keys"):
        phase36_budget.dry(ruling)
    with pytest.raises(SystemExit, match="never lives under results/"):
        phase36_budget.dry(_ROOT / "results" / "ruling.json")


def test_dry_prints_the_comparisons_before_a_divergence_refusal(tmp_path, monkeypatch, capsys):
    _committed_inputs(monkeypatch, _plant(tmp_path, e1_totals=(1.3 * 4115.04, 4064.0)))
    with pytest.raises(SystemExit, match="investigate BEFORE"):
        phase36_budget.dry()
    out = capsys.readouterr().out
    assert '"id": "r1b_e1_k48#1"' in out and '"exceeds": true' in out


def test_dry_refuses_naming_the_missing_probe_records_on_the_real_tree():
    if all(r in _tracked() for r in RECORDS):
        return  # the probe records exist: dry runs (36-07)
    before = _listing()
    done = subprocess.run(
        [sys.executable, "scripts/phase36_budget.py", "dry"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 1
    assert "probe records missing for fronts" in done.stderr
    assert _listing() == before


def test_show_and_main_dispatch(monkeypatch, capsys):
    phase36_budget._show("label", {"b": 1, "a": 2})
    assert capsys.readouterr().out == '[phase36_budget] label: {"a": 2, "b": 1}\n'
    calls = []
    monkeypatch.setattr(phase36_budget, "dry", lambda ruling_path=None: calls.append(ruling_path))
    monkeypatch.setattr(phase36_budget, "emit", lambda out_path=BUDGET: calls.append(out_path))
    assert phase36_budget.main(["dry"]) == 0
    assert phase36_budget.main(["dry", "--ruling", "/tmp/r.json"]) == 0
    assert phase36_budget.main(["emit"]) == 0
    assert calls == [None, "/tmp/r.json", BUDGET]
    with pytest.raises(SystemExit):
        phase36_budget.main(["write"])


def test_later_records_reads_phase_37_onwards_end_lines(monkeypatch):
    lines = [
        {"event": "end", "phase": 36, "record": RECORDS[0]},
        {"event": "end", "phase": 37, "record": "results/phase37_replica.json"},
        {"event": "end", "phase": 41, "record": "results/phase41_untracked.json"},
        {"event": "start", "phase": 42, "record": None},
    ]
    monkeypatch.setattr(phase36_ledger, "read_ledger", lambda path=None: lines)
    tracked = [RECORDS[0], "results/phase37_replica.json"]
    assert phase36_budget.later_records(tracked) == ["results/phase37_replica.json"]


def test_emit_refuses_an_existing_output_first(tmp_path, clean_tree):
    out = tmp_path / "budget.json"
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        phase36_budget.emit(out)
    assert out.read_text(encoding="utf-8") == "{}" and clean_tree == []


def test_emit_dirty_pathspec_then_fill_file_refusals(monkeypatch, clean_tree):
    rel = "results/phase36_never_written_budget.json"

    def stop():
        raise SystemExit("[test] stopped after the dirty check")

    monkeypatch.setattr(phase36_budget.phase36_caps, "tracked_files", stop)
    with pytest.raises(SystemExit, match="stopped after the dirty check"):
        phase36_budget.emit(rel)
    (call,) = clean_tree
    assert call["cwd"] == phase36_budget._GIT_ROOT
    assert call["pathspec"] == ("scripts", "src", "results", f":(exclude){rel}")
    assert not (_ROOT / rel).exists()
    monkeypatch.setattr(phase36_budget.phase36_caps, "tracked_files", lambda: list(RECORDS))
    with pytest.raises(SystemExit, match="phase36_budget_prereg.py is not tracked"):
        phase36_budget.emit(rel)


def test_emit_refuses_after_a_phase_37_record(monkeypatch, tmp_path):
    later = "results/phase37_replica.json"
    monkeypatch.setattr(phase36_budget, "FILL_FILE", "scripts/phase36_prereg.py")
    monkeypatch.setattr(
        phase36_budget.phase36_caps,
        "tracked_files",
        lambda: ["scripts/phase36_prereg.py", *RECORDS, later],
    )
    monkeypatch.setattr(
        phase36_ledger,
        "read_ledger",
        lambda path=None: [{"event": "end", "phase": 37, "record": later}],
    )
    monkeypatch.setattr(phase36_budget, "committed_derive", lambda *a, **k: pytest.fail("built"))
    out = tmp_path / "budget.json"
    with pytest.raises(SystemExit, match="precedes every phase-37..43 MPS record"):
        phase36_budget.emit(out)
    assert not out.exists()


def _fill_module(value, total, ruling):
    module = type(sys)("phase36_budget_prereg")
    module.RULING = ruling
    module.V6_BUDGET_AND_STOP_LINE = {**value, "total_hours": total}
    return module


def test_emit_writes_the_rederived_budget(planted, monkeypatch, tmp_path):
    """The fill file is planted (plan 08 writes the real one after Rafael's approved); the
    committed loaders are planted; FILL_FILE points at a tracked, unchanged module."""
    _committed_inputs(monkeypatch, planted)
    monkeypatch.setattr(phase36_budget, "FILL_FILE", "scripts/phase36_prereg.py")
    monkeypatch.setattr(
        phase36_budget.phase36_caps,
        "tracked_files",
        lambda: ["scripts/phase36_prereg.py", *RECORDS, LEDGER],
    )
    monkeypatch.setattr(phase36_ledger, "read_ledger", lambda path=None: [])
    monkeypatch.setattr(phase36_budget, "_head_blob", lambda rel, tracked: rel.encode("utf-8"))
    ruling = {"approved": "planted"}
    derived = _derive(planted)
    value = phase36_budget._fit_value(derived)
    fill = _fill_module(value, derived["total_hours"], ruling)
    monkeypatch.setitem(sys.modules, "phase36_budget_prereg", fill)
    out = tmp_path / "budget.json"
    record = phase36_budget.emit(out)
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == json.loads(json.dumps(record))
    assert written["front_hours"] == derived["front_hours"]
    assert set(written["sources"]) == {*RECORDS, *phase36_budget.HISTORICAL_RECORDS, LEDGER}
    assert set(written["provenance"]["module_sha256"]) == {
        "scripts/phase36_budget.py",
        "scripts/phase36_prereg.py",
        "scripts/phase36_caps.py",
    }
    assert {"git_sha", "head_at_write", "written_utc"} <= set(written["provenance"])

    bad = _fill_module({**value, "e2_seed_count": 4}, derived["total_hours"], ruling)
    monkeypatch.setitem(sys.modules, "phase36_budget_prereg", bad)
    with pytest.raises(SystemExit, match="is not the re-derived budget"):
        phase36_budget.emit(tmp_path / "other.json")
    _committed_inputs(monkeypatch, planted, spent=150000.0)
    with pytest.raises(SystemExit, match="HALT"):
        phase36_budget.emit(tmp_path / "halt.json")
    assert not (tmp_path / "other.json").exists() and not (tmp_path / "halt.json").exists()


def _strip(record):
    return {k: v for k, v in record.items() if k not in ("provenance", "sources")}


def test_recompute_the_committed_budget(planted, monkeypatch):
    tracked = _tracked()
    if BUDGET in tracked:
        import phase36_budget_prereg as fill_file

        committed = json.loads((_ROOT / BUDGET).read_text(encoding="utf-8"))
        derived = phase36_budget.committed_derive(
            phase36_budget.probe_record_paths(tracked), **fill_file.RULING
        )
        rebuilt = phase36_budget.budget_record(
            fill_file.V6_BUDGET_AND_STOP_LINE, derived, fill_file.RULING
        )
        assert _strip(json.loads(json.dumps(rebuilt))) == _strip(committed)
        return
    # Honest branch: no committed budget yet. Two derives on the same records are identical.
    _committed_inputs(monkeypatch, planted)
    first = phase36_budget.committed_derive(RECORDS)
    second = phase36_budget.committed_derive(RECORDS)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_ancestry_probes_fill_file_budget_and_later_records():
    tracked = _tracked()
    later = phase36_budget.later_records(tracked)
    if BUDGET in tracked:
        _assert_frozen_before(phase36_budget.FILL_FILE, [BUDGET])
        for record in RECORDS:
            _assert_frozen_before(record, [phase36_budget.FILL_FILE])
        _assert_frozen_before(BUDGET, later)
    else:
        assert later == [], f"{later} tracked before the v6.0 budget"
    # NON-VACUITY (natural RED): phase35_prereg was added before phase36_prereg existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before("scripts/phase36_prereg.py", ["scripts/phase35_prereg.py"])


def test_every_budget_function_has_a_cpu_test():
    source = (_SCRIPTS / "phase36_budget.py").read_text(encoding="utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert len([n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]) > 1
    assert _untested_functions("phase36_budget", source, test_source) == []


def test_budget_module_never_fills_and_never_names_the_v6_module():
    tree = ast.parse((_SCRIPTS / "phase36_budget.py").read_text(encoding="utf-8"))
    attrs = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute)]
    assert attrs, "meta-guard: the walk saw no attribute"
    owner = [n for n in attrs if isinstance(n.value, ast.Name) and n.value.id == "phase35_prereg"]
    assert owner, "meta-guard: no phase35_prereg access, the walk is blind"
    assert [n.attr for n in owner if n.attr == "fill" or n.attr.startswith("_")] == []
    assert not [
        n for n in ast.walk(tree) if isinstance(n, ast.Constant) and n.value == "phase35_prereg"
    ]
    assert not (_SCRIPTS / "phase36_budget.py").name.endswith("prereg.py")
