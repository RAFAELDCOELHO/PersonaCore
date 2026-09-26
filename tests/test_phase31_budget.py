"""Phase 31 ARCAL-03 — the torch-free v5.0 budget and the Phase 32 stop line (31-03)."""

import ast
import inspect
import json
import pathlib
import statistics
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

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase29_prereg  # noqa: E402  (same)
import phase30_points as pts  # noqa: E402  (same)
import phase31_budget as budget  # noqa: E402  (same)
import phase31_probe as probe  # noqa: E402  (same)

# The module-scoped CPU live-path fixtures, imported by name so each runs ONCE in this module.
from test_phase31_probe import (  # noqa: E402
    _synthetic_relearn_run,
    _synthetic_run,
    _synthetic_table,
    point_probe_run,  # noqa: F401  (a fixture, used by name)
    relearn_probe_run,  # noqa: F401  (same)
)

STAGES = ("train", "measure", "recall", "draw", "score")
# Synthetic recipe: the replay window counts are the TEST's inputs, not the pinned ones.
_RECIPE = {
    "n8": {"replay_windows": 32, "max_steps": 200},
    "n64": {"replay_windows": 256, "max_steps": 200},
}


def _inputs(**point_run):
    return {
        "point": probe.build_point_record(_synthetic_run(**point_run), _synthetic_table()),
        "relearn": probe.build_relearn_record(_synthetic_relearn_run()),
        "table": _synthetic_table(),
        "recipe": _RECIPE,
        "max_steps": 200,
    }


def _derived(**point_run):
    inputs = _inputs(**point_run)
    return inputs, budget.derive(**inputs)


def _rows(table, leg):
    return [table["points"][k] for k in phase29_prereg.leg_keys(leg)]


# =================================================================================================
# Task 1 — derive(): the locked D-07..D-10 formula
# =================================================================================================


def test_derive_n64_point_is_the_probe():
    inputs, out = _derived()
    n64 = out["per_point"]["n64"]
    for stage in STAGES:
        assert n64[stage] == inputs["point"]["stages"][stage]["seconds"]
    assert n64["total"] == sum(n64[s] for s in STAGES)


def test_derive_n8_training_scales_by_replay_windows():
    inputs, out = _derived()
    table, point = inputs["table"]["points"], inputs["point"]
    twin64 = table[phase29_prereg.control_key("n64")]["train"]
    twin8 = table[phase29_prereg.control_key("n8")]["train"]
    per_window = (point["stages"]["train"]["seconds"] - twin64) / (200 * 256)
    assert out["derived"]["per_window_seconds"] == per_window
    assert out["per_point"]["n8"]["train"] == twin8 + 200 * 32 * per_window
    with pytest.raises(SystemExit, match="per_window"):
        _derived(training=dict(_synthetic_run()["training"], seconds=twin64))


def test_derive_n8_non_training_uses_median_matched_ratios():
    inputs, out = _derived()
    n8_rows, n64_rows = _rows(inputs["table"], "n8"), _rows(inputs["table"], "n64")
    assert len(n8_rows) == len(phase29_prereg.RATIO_GRID)
    for stage in ("measure", "recall", "draw"):
        pairs = [a[stage] / b[stage] for a, b in zip(n8_rows, n64_rows)]
        ratio = out["derived"]["ratios"][stage]
        assert ratio["pairs"] == pairs
        assert ratio["median"] == statistics.median(pairs)
        n64 = out["per_point"]["n64"][stage]
        assert out["per_point"]["n8"][stage] == n64 * statistics.median(pairs)
    assert out["per_point"]["n8"]["score"] == out["per_point"]["n64"]["score"]
    assert "no Phase 25" in out["formula"]["n8_score"]


def test_derive_spread_is_phase25_per_stage():
    inputs, out = _derived()
    rows = list(inputs["table"]["points"].values())
    assert len(rows) == len(phase29_prereg.POINT_KEYS())
    for stage in ("train", "measure", "recall", "draw"):
        values = [r[stage] for r in rows]
        med = statistics.median(values)
        assert out["spread"][stage] == [min(values) / med, max(values) / med]
    assert out["spread"]["score"] == [1.0, 1.0]
    assert out["formula"]["score_spread"]
    for leg in phase29_prereg.LEGS:
        p = out["per_point"][leg]
        assert p["low"] == sum(p[s] * out["spread"][s][0] for s in STAGES)
        assert p["high"] == sum(p[s] * out["spread"][s][1] for s in STAGES)


def test_derive_branches():
    _, out = _derived()
    per_leg = out["sweep"]["per_leg"]
    for leg in phase29_prereg.LEGS:
        p = out["per_point"][leg]
        n = len(phase29_prereg.leg_keys(leg))
        for bound, key in (("estimate", "total"), ("low", "low"), ("high", "high")):
            assert per_leg[leg]["learnable"][bound] == n * p[key]
            assert per_leg[leg]["unlearnable"][bound] == p[key]
    branches = out["sweep"]["branches"]
    assert len(branches) == 2 ** len(phase29_prereg.LEGS)
    all_learnable = next(b for b in branches if set(b["legs"].values()) == {"learnable"})
    assert out["sweep"]["scheduled"] == all_learnable
    for b in branches:
        assert b["high"] == sum(per_leg[leg][b["legs"][leg]]["high"] for leg in b["legs"])


def test_derive_stop_line():
    _, out = _derived()
    assert budget.STOP_LINE_FACTOR == 1.5
    stop = out["stop_line"]
    assert stop["factor"] == budget.STOP_LINE_FACTOR
    assert stop["seconds"] == budget.STOP_LINE_FACTOR * out["sweep"]["scheduled"]["high"]
    assert stop["hours"] == stop["seconds"] / 3600
    assert "sweep.scheduled.high" in stop["basis"]
    assert "never retype" in stop["consumer"]


def test_derive_relearning_is_priced_not_scheduled():
    inputs, out = _derived()
    relearn = inputs["relearn"]
    rel = out["relearning"]
    assert rel["scheduled_seconds"] == 0
    assert "D-15 option 2" in rel["scheduled_reason"]
    scale = phase29_prereg.FULL_K / relearn["k"]
    rungs = relearn["stages"]["rungs"]
    rescore = max(r["draw_seconds"] * scale + r["remainder_seconds"] for r in rungs)
    fk = rel["full_k_rescore"]
    assert fk["per_point_seconds"]["estimate"] == rescore > 0
    assert "phase27_relearn.run_gate" in fk["basis"] and "promote_at_z" in fk["basis"]
    assert "upper bound" in fk["reason"]
    sp = out["spread"]
    train = relearn["stages"]["train"]["seconds"]
    arm = {
        "estimate": relearn["arm_seconds"],
        **{
            bound: train * sp["train"][i]
            + sum(
                r["draw_seconds"] * sp["draw"][i] + r["remainder_seconds"] * sp["recall"][i]
                for r in rungs
            )
            for i, bound in enumerate(("low", "high"))
        },
    }
    re = {
        "estimate": rescore,
        **{
            bound: max(
                r["draw_seconds"] * scale * sp["draw"][i] + r["remainder_seconds"] * sp["recall"][i]
                for r in rungs
            )
            for i, bound in enumerate(("low", "high"))
        },
    }
    for bound in ("estimate", "low", "high"):
        assert rel["arm_seconds"][bound] == arm[bound]
        assert fk["per_point_seconds"][bound] == re[bound]
    arms = len(phase29_prereg.FRESH_SEEDS) + 1
    for leg in phase29_prereg.LEGS:
        cond = rel["conditional"][leg]
        admitted = range(1, len(phase29_prereg.leg_keys(leg)))
        assert list(cond) == [str(a) for a in admitted]
        for a in admitted:
            for bound in ("estimate", "low", "high"):
                assert cond[str(a)][bound] == (arms + a) * arm[bound] + a * re[bound]
    assert "one arm unit" in rel["arm_unit_note"]


def test_derive_reconciles_the_unsourced_estimate():
    inputs, out = _derived()
    rows = list(inputs["table"]["points"].values())
    no_recall = sum(r["train"] + r["measure"] + r["draw"] for r in rows) / 3600
    with_recall = no_recall + sum(r["recall"] for r in rows) / 3600
    rec = out["reconciliation"]
    assert rec["phase25_sum_hours"]["no_recall"] == no_recall
    assert rec["phase25_sum_hours"]["with_recall"] == with_recall
    assert "25-HUMAN-UAT.md" in rec["unsourced_estimate_origin"]
    assert out["resource_not_outcome"] is True
    assert any("Pitfall 5" in n for n in out["notes"])


def test_budget_derives_without_torch():
    run = _synthetic_run(training=dict(_synthetic_run()["training"], seconds=900.0))
    code = (
        "import sys, json; sys.path[:0] = ['scripts', 'src']; "
        "import phase31_budget as b, phase31_probe as p, phase30_points as pts, "
        "mitigation_budget as mb; "
        f"run = json.loads({json.dumps(run)!r}); "
        f"rrun = json.loads({json.dumps(_synthetic_relearn_run())!r}); "
        "t = p._tracked(); table = p.phase25_stage_table(t); "
        "b.derive(point=p.build_point_record(run, table), relearn=p.build_relearn_record(rrun), "
        "table=table, recipe=pts.calibration_record(t)['recipe'], max_steps=mb.STEP_BUDGET); "
        "print('torch' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=_ROOT, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "False", completed.stdout


def test_budget_consumes_real_producer_records(point_probe_run, relearn_probe_run):  # noqa: F811
    _, point, _ = point_probe_run
    _, relearn, _ = relearn_probe_run
    tracked = probe._tracked()
    table = probe.phase25_stage_table(tracked)
    # DOCUMENTED SUBSTITUTION (this test only): fixture seconds are CPU seconds at 2 steps, not MPS
    # seconds at STEP_BUDGET, so the n64 twin's train is set to half the fixture probe's train to
    # keep per_window > 0. Every other input is the real producer's record or a committed record.
    control = phase29_prereg.control_key("n64")
    table["points"][control] = dict(
        table["points"][control], train=0.5 * point["stages"]["train"]["seconds"]
    )
    available = {
        "point": point,
        "relearn": relearn,
        "table": table,
        "recipe": pts.calibration_record(tracked)["recipe"],
        "max_steps": mitigation_budget.STEP_BUDGET,
    }
    params = inspect.signature(budget.derive).parameters
    assert set(params) <= set(available), set(params) - set(available)
    out = budget.derive(**{name: available[name] for name in params})
    assert out["stop_line"]["seconds"] > 0
    assert out["relearning"]["full_k_rescore"]["per_point_seconds"]["estimate"] > 0
    assert out["per_point"]["n64"]["train"] == point["stages"]["train"]["seconds"]
    json.dumps(out)  # the record is JSON-serialisable end to end


def test_budget_never_calls_torch_touching_helpers():
    tree = ast.parse((_SCRIPTS / "phase31_budget.py").read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert len(calls) > 1, "the walk saw no calls: the guard is blind"
    bad = [
        ast.dump(n)
        for n in calls
        if isinstance(n.func, ast.Attribute) and n.func.attr == "replay_windows"
    ]
    bad += [
        ast.dump(n)
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr == "MAX_STEPS"
    ]
    assert bad == []


# =================================================================================================
# Task 2 — build_record / emit from committed files, and the ARCAL-03 ancestry guards
# =================================================================================================

from test_phase29_prereg import _assert_frozen_before, _git  # noqa: E402

BUDGET = budget.BUDGET_RECORD
POINT, RELEARN = probe.POINT_RECORD, probe.RELEARN_RECORD


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """emit refuses a dirty tree and this suite runs on dirty trees, so the guard is RECORDED."""
    calls = []
    monkeypatch.setattr(budget, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


def _is_tracked(rel):
    return rel in _git("ls-files", rel).split()


def test_budget_path_is_the_preregistered_one():
    assert BUDGET == "results/phase31_budget.json"
    assert BUDGET in phase29_prereg.V5_RESULT_PATHS


def test_emit_budget_is_write_once(tmp_path):
    out = tmp_path / "budget.json"
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        budget.emit(out)
    assert out.read_text(encoding="utf-8") == "{}"
    if _is_tracked(BUDGET):
        path = probe._GIT_ROOT / BUDGET
        before = path.read_bytes()
        with pytest.raises(SystemExit, match="REFUSING to overwrite"):
            budget.emit()
        assert path.read_bytes() == before


def test_emit_budget_refuses_a_dirty_tree_first(monkeypatch, clean_tree):
    def stop():
        raise SystemExit("[probe] stopped after the dirty check")

    monkeypatch.setattr(probe, "_tracked", stop)
    monkeypatch.setattr(
        budget, "build_record", lambda t: pytest.fail("built before the dirty check")
    )
    rel = "results/phase31_never_written_budget.json"
    inside = probe._GIT_ROOT / rel
    with pytest.raises(SystemExit, match="stopped after the dirty check"):
        budget.emit(inside)
    assert not inside.exists()
    (call,) = clean_tree
    assert call["cwd"] == probe._GIT_ROOT
    assert call["pathspec"] == ("scripts", "src", "results", f":(exclude){rel}")


def _forged_point():
    return probe.build_point_record(
        _synthetic_run(training=dict(_synthetic_run()["training"], seconds=900.0)),
        _synthetic_table(),
    )


def test_emit_budget_refuses_untracked_probes(monkeypatch):
    real = probe._tracked()
    with pytest.raises(SystemExit, match=POINT):
        budget.build_record([p for p in real if p != POINT])
    real_json = pts._tracked_json
    forged = _forged_point()
    monkeypatch.setattr(
        pts,
        "_tracked_json",
        lambda rel, tracked, what: forged if rel == POINT else real_json(rel, tracked, what),
    )
    with pytest.raises(SystemExit, match=RELEARN):
        budget.build_record([p for p in real if p != RELEARN])


def test_emit_budget_refuses_after_a_sweep_point(monkeypatch, tmp_path):
    sweep = phase29_prereg.point_record_path(phase29_prereg.control_key("n8"))
    assert sweep.startswith(phase29_prereg.POINT_RECORD_PREFIX)
    with pytest.raises(SystemExit, match=sweep):
        budget.require_no_sweep_point(["results/phase30_calibration.json", sweep])
    assert budget.require_no_sweep_point(["results/phase30_calibration.json"]) is None
    built = []
    monkeypatch.setattr(probe, "_tracked", lambda: ["results/phase30_calibration.json", sweep])
    monkeypatch.setattr(budget, "build_record", lambda t: built.append(t) or pytest.fail("built"))
    out = tmp_path / "budget.json"
    with pytest.raises(SystemExit, match=sweep):
        budget.emit(out)
    assert built == [] and not out.exists()


def _strip(record):
    return {k: v for k, v in record.items() if k not in ("provenance", "calibration")}


def test_committed_budget_recomputes_from_committed_files(monkeypatch):
    if _is_tracked(BUDGET):
        committed = json.loads((probe._GIT_ROOT / BUDGET).read_text(encoding="utf-8"))
        rebuilt = json.loads(json.dumps(budget.build_record(probe._tracked())))
        assert _strip(rebuilt) == _strip(committed)
        return
    # Honest branch: no committed budget yet. build_record over forged-tracked synthetic probes is
    # deterministic and names every source it read.
    forged = {POINT: _forged_point(), RELEARN: probe.build_relearn_record(_synthetic_relearn_run())}
    real_json, real_sha = pts._tracked_json, budget._sha256
    monkeypatch.setattr(
        pts,
        "_tracked_json",
        lambda rel, tracked, what: forged[rel] if rel in forged else real_json(rel, tracked, what),
    )
    monkeypatch.setattr(
        budget, "_sha256", lambda p: real_sha(p) if pathlib.Path(p).exists() else "f" * 64
    )
    tracked = [*probe._tracked(), POINT, RELEARN]
    first, second = budget.build_record(tracked), budget.build_record(tracked)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert "provenance" not in first and "calibration" not in first
    table = probe.phase25_stage_table(probe._tracked())
    expected = {POINT, RELEARN, table["recall_source"], pts.CALIBRATION_PATH}
    expected |= {row["source"] for row in table["points"].values()}
    assert set(first["sources"]) == expected


def test_ancestry_budget_precedes_every_sweep_point():
    points = sorted(_git("ls-files", phase29_prereg.POINT_RECORD_PREFIX + "*.json").split())
    if not _is_tracked(BUDGET):
        assert points == [], f"sweep point(s) {points} committed before the ARCAL-03 budget"
        return
    _assert_frozen_before(BUDGET, points)
    # NON-VACUITY (natural RED): the calibration was added before the budget existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(BUDGET, [pts.CALIBRATION_PATH])


def test_ancestry_probes_precede_the_budget():
    if not _is_tracked(BUDGET):
        later = _git("ls-files", "results/phase32_*").split()
        assert later == [], f"{later} tracked before the ARCAL-03 budget"
        return
    for probe_record in (POINT, RELEARN):
        _assert_frozen_before(probe_record, [BUDGET])
    if _is_tracked(RELEARN):
        _assert_frozen_before(POINT, [RELEARN])
    # NON-VACUITY (natural RED): the point probe was added before the budget existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(BUDGET, [POINT])
