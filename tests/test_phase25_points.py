"""THE PER-POINT RESOLVER (2026-09-04 launch-checkpoint deviation) — CPU-only, never skips.

Every test here is the smallest thing that fails if the corresponding branch breaks: the D-15
schedule as a proved permutation, one unique prefix per key, the DP and adversarial mechanism
pins, GATE-05's n=64 taught mapping and the reported tier's measured omission, D-50's seed-spread
source, D-47's tracked-control-only `control_gap`, and `build_point_record`'s `extra` merge.
"""

import importlib.util
import inspect
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import mitigation_unit  # noqa: E402  (same)
import phase14_factset as fs  # noqa: E402  (same)
import phase21_filler as pf  # noqa: E402  (same)
import phase25_gate05 as g5  # noqa: E402  (same)
import phase25_points as pts  # noqa: E402  (same)
import phase25_prereg as prereg  # noqa: E402  (same)
import phase25_record as rec  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)

LADDER = mitigation_budget.SIGMA_LADDER
GRID = mitigation_budget.ADVERSARIAL_RATIO_GRID


def test_the_schedule_is_a_permutation_with_the_eight_extremes_first():
    schedule = rec.SWEEP_SCHEDULE()
    keys = rec.ORDERED_POINT_KEYS()
    assert len(schedule) == 44 and sorted(schedule) == sorted(keys)
    head = schedule[:8]
    assert head[:2] == ("dp_n8_sigma0p000000", "dp_n64_sigma0p000000")
    extremes = {
        rec.point_key("dp_n8", LADDER[-1]),
        rec.point_key("dp_n64", LADDER[-1]),
        rec.point_key("adv_n8", GRID[0]),
        rec.point_key("adv_n64", GRID[0]),
        rec.point_key("adv_n8", GRID[-1]),
        rec.point_key("adv_n64", GRID[-1]),
    }
    assert set(head[2:]) == extremes
    arms = [rec.parse_point_key(key)[0] for key in head[2:]]
    assert all(a != b for a, b in zip(arms, arms[1:])), arms  # interleaved, no leg exhausted
    assert list(schedule[8:]) == [key for key in keys if key not in head]  # interior as pinned


def test_the_driver_defaults_to_the_schedule_not_the_pinned_order():
    source = inspect.getsource(phase25_run.main)
    assert "SWEEP_SCHEDULE()" in source and "ORDERED_POINT_KEYS()" not in source


def test_every_key_resolves_to_a_plan_with_a_unique_prefix_without_torch():
    plans = [pts.point_plan(key) for key in rec.ORDERED_POINT_KEYS()]
    prefixes = [plan["prefix"] for plan in plans]
    # `arm_outputs` scopes adapter/checkpoint/csv as `{prefix}_{arm}`, so the (prefix, arm) pair is
    # the path identity: 44 distinct adapters, while dp_n8 and dp_n64 share a prefix at one sigma.
    assert len({(plan["prefix"], plan["arm"]) for plan in plans}) == 44
    assert len(set(prefixes)) == len(LADDER) + len(GRID)
    assert all(prefix.startswith("phase25_") for prefix in prefixes)
    assert not any(prefix.startswith(pts.CALIBRATION_PREFIX_LITERAL) for prefix in prefixes)
    assert sum(plan["is_control"] for plan in plans) == 2
    # The axis value the run consumes is the committed literal, never the six-decimal label.
    assert {plan["axis_value"] for plan in plans if plan["is_dp"]} == set(LADDER)
    assert {plan["axis_value"] for plan in plans if not plan["is_dp"]} == set(GRID)


def test_resolving_all_44_plans_imports_no_torch():
    """In a FRESH interpreter, so a sibling test file's torch import cannot mask a regression."""
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'scripts'); import phase25_points as p, "
            "phase25_record as r; [p.point_plan(k) for k in r.SWEEP_SCHEDULE()]; "
            "print('TORCH' if 'torch' in sys.modules else 'NOTORCH')",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "NOTORCH" in completed.stdout, completed.stdout


def test_the_dp_pin_is_the_committed_literals_and_the_control_has_no_epsilon():
    control = pts.point_plan("dp_n8_sigma0p000000")
    assert control["is_control"] and control["dp_clip_norm"] == mitigation_budget.CONTROL_CLIP_NORM
    assert control["pinned_mechanism"] == {
        "composed_steps": mitigation_budget.STEP_BUDGET,
        "composed_lot_sizes": [8],
        "records_per_lot": 8,
        "q": mitigation_unit.SAMPLING_RATE_Q,
        "clip_norm": mitigation_budget.CONTROL_CLIP_NORM,
    }
    assert control["point_epsilon"] is None and control["accounting"] is None

    noised = pts.point_plan("dp_n64_sigma0p500000")
    assert noised["pinned_mechanism"]["clip_norm"] == mitigation_budget.CLIP_NORM
    assert noised["pinned_mechanism"]["records_per_lot"] == 64
    assert noised["point_epsilon"] == mitigation_budget.EPSILON_LADDER[LADDER.index(0.5)]
    assert noised["accounting"]["delta"] == mitigation_unit.DELTA
    assert noised["prefix"] == "phase25_sigma0p500000"


def test_the_adversarial_pin_carries_null_q_and_null_clip_on_both_sides():
    plan = pts.point_plan("adv_n8_ratio1p909091")
    assert not plan["is_dp"] and plan["dp_sigma"] is None and plan["dp_clip_norm"] is None
    assert plan["adversarial_ratio"] == GRID[-1]
    pin = plan["pinned_mechanism"]
    assert pin["q"] is None and pin["clip_norm"] is None
    assert pin["composed_steps"] == mitigation_budget.STEP_BUDGET
    assert plan["point_epsilon"] is None and plan["accounting"] is None
    assert plan["control_key"] == "dp_n8_sigma0p000000"
    assert pts.point_plan("adv_n64_ratio0p000000")["control_key"] == "dp_n64_sigma0p000000"
    # The DP pin is exactly equal on both sides by construction; the adversarial one resolves its
    # lot at train time but the four static fields must already agree with themselves.
    rec.prove_mechanism_matches_pin(dict(pin), dict(pin), point_key=plan["point_key"])


def test_the_n64_taught_mapping_has_64_keys_and_passes_the_tier_proof():
    taught = pts.taught_mapping(fs.LOCKED_FACTS + pf.FILLER_FACTS)
    assert len(taught) == 64
    gated, reported = g5.gate05_tier_slots(taught, 64)
    assert gated == g5.GATE05_SLOTS and len(reported) == 64
    assert len(pts.taught_mapping(fs.LOCKED_FACTS)) == 8
    # Filler facts are keyed by fact id because seven of them share each filler slot.
    assert sum(key.startswith("filler_") for key in taught) == 56


def test_measure_gate05_records_filler_facts_as_unmeasurable(monkeypatch):
    import phase18_extraction as x18

    calls = []

    def fake_measure_exposure(model, tok, device, *, slot, taught_value):
        calls.append(slot)
        return {"slot": slot, "taught_value": taught_value}

    monkeypatch.setattr(x18, "measure_exposure", fake_measure_exposure)
    taught = pts.taught_mapping(fs.LOCKED_FACTS + pf.FILLER_FACTS)
    out = g5.measure_gate05(None, None, "cpu", taught=taught, n_facts=64)
    assert calls == list(g5.GATE05_SLOTS)  # only the eight core slots ever reach the scorer
    assert out["exposure_measured"] == 8 and out["exposure_omitted"] == 56
    assert len(out["reported"]) == 64 and out["reported_slot_count"] == 64
    omitted = [row for row in out["reported"] if row["slot"] not in g5.GATE05_SLOTS]
    assert len(omitted) == 56
    assert all(row["exposure_omitted_reason"] == g5.FILLER_EXPOSURE_OMITTED for row in omitted)
    assert "reference_set_for" in g5.FILLER_EXPOSURE_OMITTED

    n8 = g5.measure_gate05(None, None, "cpu", taught=pts.taught_mapping(fs.LOCKED_FACTS), n_facts=8)
    assert n8["exposure_omitted"] == 0 and n8["omitted_reason"] is None


def test_seed_spread_comes_only_from_the_n64_floor_record(monkeypatch, tmp_path):
    monkeypatch.setattr(pts, "N64_FLOOR_RECORD", tmp_path / "missing.json")
    with pytest.raises(SystemExit) as excinfo:
        pts.seed_spread()
    assert "phase25_n64_floor" in str(excinfo.value)
    record = tmp_path / "floor.json"
    record.write_text(json.dumps({"retention": {"seed_spread": [0.01, 0.02]}}))
    monkeypatch.setattr(pts, "N64_FLOOR_RECORD", record)
    assert pts.seed_spread() == [0.01, 0.02]


def test_control_gap_is_read_only_from_a_tracked_control_record(monkeypatch, tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        pts.control_reading("adv_n8", tracked=[])
    assert "not TRACKED" in str(excinfo.value)
    relative = prereg.point_record_path("dp_n64_sigma0p000000")
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"condition_c": {"point_dialogue_ppl_on": 5.5, "point_dialogue_ppl_off": 4.5}})
    )
    monkeypatch.setattr(pts, "_ROOT", tmp_path)
    assert pts.control_reading("dp_n64", tracked=[relative]) == {
        "adapter_on": 5.5,
        "adapter_off": 4.5,
    }


def _record_builder():
    spec = importlib.util.spec_from_file_location(
        "test_phase25_record", _ROOT / "tests" / "test_phase25_record.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build


def test_build_point_record_merges_extras_and_refuses_collisions_and_gate_names():
    build = _record_builder()
    record = build(extra={"taught_recall": {"numerator": 790, "denominator": 1008}})
    assert record["taught_recall"] == {"numerator": 790, "denominator": 1008}
    with pytest.raises(SystemExit) as collision:
        build(extra={"arm": "dp_n8"})
    assert "collide" in str(collision.value)
    with pytest.raises(SystemExit):
        build(extra={"point_taught_recall": 0.5})  # a verdict kwarg can never be an extra


def test_the_retention_seed_spread_is_pairwise_sorted_and_nonnegative():
    import phase25_n64_floor as floor

    spread = floor.retention_seed_spread({"1337": 1.0, "2024": 1.5, "1338": 1.2})
    assert spread == sorted(spread) and len(spread) == 3
    assert [round(v, 6) for v in spread] == [0.2, 0.3, 0.5]


def test_score_point_rolls_up_per_family_cell_never_across_families(monkeypatch):
    """MEASURED 2026-09-04 21:49 UTC, on the first sweep point after 79 minutes of draws:
    `aggregate_questions` refuses records pooled across families — the same (fact_id, seed_index)
    appears once per attack family — so the per-fact rollup must be taken per (family, tier) cell,
    exactly as `phase23_run.score_never_taught` takes it. The draws survived in the cache; only
    the score stage was lost."""
    import phase18_extraction as x18

    def fake_score_records(records, values):
        return [
            {
                "family": family,
                "tier": tier,
                "fact_id": "cand_cat_zibby",
                "slot": "cat_name",
                "seed_index": 26,
                "hits": [True, False],
                "n_draws": 2,
            }
            for family in rec.ATTACK_FAMILIES
            for tier in (rec.GATED_TIER, rec.REPORTED_TIER)
        ]

    monkeypatch.setattr(x18, "score_records", fake_score_records)
    blob = {"shapes": {family: {"draws": [{}]} for family in rec.ATTACK_FAMILIES}}
    per_question, per_fact, scored = phase25_run.score_point(blob, {})
    assert len(per_question[rec.GATED_TIER]) == len(rec.ATTACK_FAMILIES)
    assert set(per_fact[rec.GATED_TIER]) == set(rec.ATTACK_FAMILIES)
    assert per_fact[rec.GATED_TIER]["A2"]["cand_cat_zibby"]["n_questions"] == 1
