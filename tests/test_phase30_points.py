"""Plan 30-02: the v5.0 driver — schedule, plan, recipe identity, own-control reader (WR-05).

CPU-only. Nothing here writes under results/: every forged record lands under tmp_path, because a
results/phase3* file would start the phase29 ancestry clock.
"""

import ast
import copy
import json
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

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase24_adversarial  # noqa: E402  (same)
import phase25_points  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points as pts  # noqa: E402  (same)

from test_phase29_prereg import (  # noqa: E402
    _grid_retype_failures,
    _numeric_constants,
    _planted,
)

LEGS = phase29_prereg.LEGS
CONTROLS = tuple(phase29_prereg.control_key(leg) for leg in LEGS)
POINTS_MODULE = _SCRIPTS / "phase30_points.py"


def _tp():
    import teach_persona  # torch at import — inside tests only

    return teach_persona


# =================================================================================================
# Task 1: schedule, plan, recipe identity (D-09, D-10, D-13, D-17, D-18)
# =================================================================================================


def test_schedule_runs_both_controls_first():
    schedule = pts.SWEEP_SCHEDULE()
    canonical = phase29_prereg.POINT_KEYS()
    assert len(schedule) == len(canonical)
    assert sorted(schedule) == sorted(canonical)
    assert schedule[: len(LEGS)] == CONTROLS
    assert schedule != canonical  # the roles stay separate: canonical order vs execution order


def test_schedule_refuses_a_non_control_before_a_control():
    canonical = phase29_prereg.POINT_KEYS()
    # NATURAL RED: the canonical arm-major order puts the n8 leg's non-control points before the
    # n64 control.
    assert canonical.index(CONTROLS[1]) > len(LEGS)
    with pytest.raises(SystemExit, match="control"):
        pts.prove_controls_first(canonical)
    good = pts.SWEEP_SCHEDULE()
    with pytest.raises(SystemExit):
        pts.prove_controls_first(good[:-1])  # dropped key
    with pytest.raises(SystemExit):
        pts.prove_controls_first(good[:-1] + good[:1])  # duplicated key, same length
    assert pts.prove_controls_first(good) == good


def test_point_plan_matches_the_v4_plan_shape():
    tp = _tp()
    v4_keys = set(phase25_points.point_plan("adv_n8_ratio0p000000"))
    for key in pts.SWEEP_SCHEDULE():
        plan = pts.point_plan(key)
        leg = pts.leg_of(key)
        assert set(plan) == v4_keys, key
        assert plan["point_key"] == key
        assert plan["is_control"] is (key in CONTROLS)
        assert plan["is_dp"] is False
        assert plan["axis"] == "ratio"
        assert any(plan["adversarial_ratio"] is r for r in phase29_prereg.RATIO_GRID), key
        assert plan["axis_value"] is plan["adversarial_ratio"]
        assert plan["n_facts"] == len(tp.arm_spec(plan["arm"])[0])
        assert plan["arm"] in phase29_prereg.ADVR_ARMS
        assert plan["seed"] == phase25_points.SWEEP_SEED
        assert plan["control_key"] == phase29_prereg.control_key(leg)
        assert not plan["prefix"].startswith(phase25_points.CALIBRATION_PREFIX_LITERAL)
        for field in ("dp_sigma", "dp_clip_norm", "point_epsilon", "accounting"):
            assert plan[field] is None, (key, field)
    prefixes = {(pts.point_plan(k)["prefix"], pts.point_plan(k)["arm"]) for k in CONTROLS}
    assert len(prefixes) == len(CONTROLS)


def test_recipe_identity_imports_every_value():
    tp = _tp()
    for leg in LEGS:
        recipe = pts.recipe_identity(leg)
        n = len(tp.arm_spec(f"advr_{leg}")[0])
        assert set(recipe) == phase29_prereg._RECIPE_FIELDS | {
            "min_refusal_scored_tokens",
            "replay_source",
        }
        assert set(recipe) == pts.RECIPE_FIELDS
        assert recipe["n_facts"] == n
        assert recipe["replay_windows"] == phase29_prereg.replay_windows(n)
        assert recipe["seed"] == phase25_points.SWEEP_SEED == tp.SEED
        assert recipe["max_steps"] == mitigation_budget.STEP_BUDGET == tp.MAX_STEPS
        assert recipe["min_refusal_scored_tokens"] == phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS
        assert recipe["replay_source"] == [
            tp.DIALOG_TRAIN_BIN.relative_to(tp._REPO_ROOT).as_posix(),
            tp.DIALOG_TRAIN_MASK.relative_to(tp._REPO_ROOT).as_posix(),
        ]
        prereg = pts.prereg_recipe(recipe)
        assert set(prereg) == phase29_prereg._RECIPE_FIELDS
        # The refused_record recipe check accepts it (an unlearnable reading so it builds).
        key = phase29_prereg.leg_keys(leg)[-1]
        built = phase29_prereg.refused_record(key, taught=(0, 1), heldout=(0, 1), recipe=prereg)
        assert built["recipe"] == prereg


def test_driver_imports_without_torch():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path[:0] = ['scripts', 'src']; import phase30_points as p; "
            "p.SWEEP_SCHEDULE(); [p.point_plan(k) for k in p.SWEEP_SCHEDULE()]; "
            "print('torch' in sys.modules)",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "False", completed.stdout


def _literal_failures(source):
    tp = _tp()
    tree = ast.parse(source)
    ints = {
        tp.REPLAY_WINDOWS_PER_FACT,
        phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS,
        mitigation_budget.STEP_BUDGET,
        phase25_points.SWEEP_SEED,
    }
    floats = {phase24_adversarial.MASK_FRACTION_MARGIN, tp.MASK_FRACTION_BAND[0]}
    strings = {
        pts.CALIBRATION_PATH,
        tp.DIALOG_TRAIN_BIN.relative_to(tp._REPO_ROOT).as_posix(),
        tp.DIALOG_TRAIN_MASK.relative_to(tp._REPO_ROOT).as_posix(),
    }
    failures = [
        f"numeric literal {n.value!r} at line {n.lineno}"
        for n in _numeric_constants(tree)
        if (type(n.value) is int and n.value in ints)
        or (type(n.value) is float and n.value in floats)
    ]
    failures += [
        f"string literal {n.value!r} at line {n.lineno}"
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in strings
    ]
    failures += _grid_retype_failures(source, mitigation_budget.ADVERSARIAL_RATIO_GRID)
    return failures


def test_no_phase30_module_retypes_a_constant(tmp_path):
    modules = sorted(_SCRIPTS.glob("phase30_*.py"))
    assert POINTS_MODULE in modules
    for path in modules:
        assert _literal_failures(path.read_text(encoding="utf-8")) == [], path
    source = POINTS_MODULE.read_text(encoding="utf-8")
    grid_end = mitigation_budget.ADVERSARIAL_RATIO_GRID[-1]
    for name, plant in (
        ("tokens.py", f"\n_X = {phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS}\n"),
        ("grid.py", f"\n_X = {grid_end!r}\n"),
        ("calibration.py", f"\n_X = {pts.CALIBRATION_PATH!r}\n"),
    ):
        planted = _planted(tmp_path, source, source + plant, name)
        assert _literal_failures(planted), name
    assert POINTS_MODULE.read_text(encoding="utf-8") == source


# =================================================================================================
# Task 2: own-control reader, calibration-recipe refusal, D-19 guard (D-14..D-16, D-19, SC2)
# =================================================================================================


def _write(root, rel, blob):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(blob), encoding="utf-8")
    return rel


def _good_control(leg, *, taught=(790, 1008), heldout=(346, 648)):
    """A forged own-control record in the v4.0 field shapes, carrying the v5.0 recipe."""
    return {
        "point_key": phase29_prereg.control_key(leg),
        "arm": pts._arm_of_leg(leg),
        "axis": "ratio",
        "q": None,
        "clip_norm": None,
        "recipe": pts.recipe_identity(leg),
        "taught_recall": {"numerator": taught[0], "denominator": taught[1]},
        "heldout_recall": {"numerator": heldout[0], "denominator": heldout[1]},
        "condition_c": {"point_dialogue_ppl_on": 5.5, "point_dialogue_ppl_off": 4.5},
        "adapter_sha256": "ab" * 32,
    }


def _v5_tree(tmp_path, monkeypatch, *, controls=None, calibration=True):
    """tmp_path as _ROOT; the calibration (tracked if asked) and any {leg: record} controls."""
    monkeypatch.setattr(pts, "_ROOT", tmp_path)
    tracked = []
    if calibration:
        blob = {"recipe": {leg: pts.recipe_identity(leg) for leg in LEGS}}
        tracked.append(_write(tmp_path, pts.CALIBRATION_PATH, blob))
    for leg, record in (controls or {}).items():
        rel = phase29_prereg.point_record_path(phase29_prereg.control_key(leg))
        tracked.append(_write(tmp_path, rel, record))
    return tracked


def _non_control(leg):
    return phase29_prereg.leg_keys(leg)[-1]


def _perturbed(recipe, field):
    out = copy.deepcopy(recipe)
    value = out[field]
    out[field] = value + ["x"] if isinstance(value, list) else value + 1
    return out


def test_wr05_own_control_accepts_the_own_record(tmp_path, monkeypatch):
    record = _good_control("n8")
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": record})
    recipe = pts.recipe_identity("n8")
    for key in (CONTROLS[0], _non_control("n8")):
        assert pts.own_control(key, tracked, point_recipe=recipe) == record
        assert pts.control_floors(key, tracked, point_recipe=recipe) == ((790, 1008), (346, 648))
        assert pts.control_dialogue_pair(key, tracked, point_recipe=recipe) == {
            "adapter_on": 5.5,
            "adapter_off": 4.5,
        }
        assert pts.control_baseline(key, tracked, point_recipe=recipe) == {
            "source": phase29_prereg.control_baseline_source("n8"),
            "adapter_sha256": record["adapter_sha256"],
        }


def test_wr05_refuses_a_dp_key(tmp_path, monkeypatch):
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": _good_control("n8")})
    with pytest.raises(SystemExit, match="v5.0 point keys"):
        pts.own_control(
            phase25_record.point_key("dp_n8", 0.0),
            tracked,
            point_recipe=pts.recipe_identity("n8"),
        )


def test_wr05_refuses_a_relabelled_dp_record(tmp_path, monkeypatch):
    real = _ROOT / phase25_prereg.point_record_path(phase25_record.point_key("dp_n8", 0.0))
    record = json.loads(real.read_text(encoding="utf-8"))
    recipe = pts.recipe_identity("n8")
    # The recipe check cannot be what refuses it: its pre-registered values equal advr_n8's.
    assert record["seed"] == recipe["seed"]
    assert record["training"]["train_config"]["max_steps"] == recipe["max_steps"]
    assert record["records_per_lot"] == recipe["n_facts"]
    assert phase29_prereg.replay_windows(record["records_per_lot"]) == recipe["replay_windows"]
    record.update(point_key=CONTROLS[0], arm=pts._arm_of_leg("n8"), recipe=recipe)
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": record})
    with pytest.raises(SystemExit, match="axis") as excinfo:
        pts.own_control(_non_control("n8"), tracked, point_recipe=recipe)
    assert "WR-05" in str(excinfo.value)
    # Each of the three DP signatures refuses on its own.
    for field, value in (("axis", "ratio"), ("q", None), ("clip_norm", None)):
        partial = dict(_good_control("n8"), **{field: record[field]})
        assert partial[field] != value
        tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": partial})
        with pytest.raises(SystemExit, match="WR-05"):
            pts.own_control(_non_control("n8"), tracked, point_recipe=recipe)


@pytest.mark.parametrize(
    "field, value",
    [
        ("point_key", CONTROLS[1]),
        ("arm", "adv_n8"),
        ("axis", "sigma"),
        ("q", 1.0),
        ("clip_norm", 1.0),
    ],
)
def test_wr05_refuses_wrong_provenance(tmp_path, monkeypatch, field, value):
    record = dict(_good_control("n8"), **{field: value})
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": record})
    with pytest.raises(SystemExit):
        pts.own_control(_non_control("n8"), tracked, point_recipe=pts.recipe_identity("n8"))


def test_wr05_refuses_a_good_record_at_a_non_v5_path(tmp_path, monkeypatch):
    tracked = _v5_tree(tmp_path, monkeypatch)
    elsewhere = phase25_prereg.point_record_path(phase25_record.point_key("adv_n8", 0.0))
    tracked.append(_write(tmp_path, elsewhere, _good_control("n8")))
    with pytest.raises(SystemExit, match="not TRACKED"):
        pts.own_control(_non_control("n8"), tracked, point_recipe=pts.recipe_identity("n8"))


@pytest.mark.parametrize("field", sorted(pts.RECIPE_FIELDS))
def test_wr05_refuses_recipe_divergence(tmp_path, monkeypatch, field):
    recipe = pts.recipe_identity("n8")
    record = dict(_good_control("n8"), recipe=_perturbed(recipe, field))
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": record})
    with pytest.raises(SystemExit, match=field):
        pts.own_control(_non_control("n8"), tracked, point_recipe=recipe)
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": _good_control("n8")})
    with pytest.raises(SystemExit, match=field):
        pts.own_control(_non_control("n8"), tracked, point_recipe=_perturbed(recipe, field))


def test_recipe_mismatch_against_the_calibration_is_refused(tmp_path, monkeypatch):
    tracked = _v5_tree(tmp_path, monkeypatch)
    for leg in LEGS:
        recipe = pts.recipe_identity(leg)
        assert pts.require_calibrated_recipe(leg, recipe, tracked) == recipe
        for field in sorted(pts.RECIPE_FIELDS):
            with pytest.raises(SystemExit, match=field):
                pts.require_calibrated_recipe(leg, _perturbed(recipe, field), tracked)
        with pytest.raises(SystemExit, match="not TRACKED"):
            pts.require_calibrated_recipe(leg, recipe, [])
    # The calibration's own recipe differing from the live identity is refused too.
    drifted = {"recipe": {leg: pts.recipe_identity(leg) for leg in LEGS}}
    drifted["recipe"]["n8"] = _perturbed(drifted["recipe"]["n8"], "seed")
    _write(tmp_path, pts.CALIBRATION_PATH, drifted)
    with pytest.raises(SystemExit, match="seed"):
        pts.require_calibrated_recipe("n8", pts.recipe_identity("n8"), tracked)


def test_guard_refuses_a_point_whose_control_is_untracked(tmp_path, monkeypatch):
    tracked = _v5_tree(tmp_path, monkeypatch)
    with pytest.raises(SystemExit) as excinfo:
        pts.next_action(_non_control("n8"), tracked)
    message = str(excinfo.value)
    assert phase29_prereg.point_record_path(CONTROLS[0]) in message
    assert "not TRACKED" in message
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": _good_control("n8")})
    with pytest.raises(SystemExit) as excinfo:
        pts.next_action(_non_control("n64"), tracked)
    assert phase29_prereg.point_record_path(CONTROLS[1]) in str(excinfo.value)


def test_guard_trains_the_control_first_and_then_its_leg(tmp_path, monkeypatch):
    tracked = _v5_tree(tmp_path, monkeypatch, calibration=False)
    with pytest.raises(SystemExit) as excinfo:
        pts.next_action(CONTROLS[0], tracked)
    assert pts.CALIBRATION_PATH in str(excinfo.value)
    tracked = _v5_tree(tmp_path, monkeypatch)
    assert pts.next_action(CONTROLS[0], tracked) == {
        "action": "train",
        "plan": pts.point_plan(CONTROLS[0]),
    }
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": _good_control("n8")})
    key = _non_control("n8")
    assert pts.next_action(key, tracked) == {"action": "train", "plan": pts.point_plan(key)}


def test_guard_short_circuits_an_unlearnable_leg(tmp_path, monkeypatch):
    def _never(*args, **kwargs):
        raise AssertionError("train_stage reached for an unlearnable leg")

    monkeypatch.setattr(phase25_points, "train_stage", _never)
    taught, heldout = (0, 1008), (0, 648)
    control = _good_control("n8", taught=taught, heldout=heldout)
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": control})
    action = pts.next_action(_non_control("n8"), tracked)
    assert action["action"] == "refuse"
    records = action["records"]
    assert tuple(records) == tuple(k for k in phase29_prereg.leg_keys("n8") if k != CONTROLS[0])
    recipe = pts.prereg_recipe(pts.recipe_identity("n8"))
    for key, blob in records.items():
        assert blob == phase29_prereg.refused_record(
            key, taught=taught, heldout=heldout, recipe=recipe
        )
    written = pts.write_refused_records(records)
    before = {}
    for key in records:
        out = tmp_path / phase29_prereg.point_record_path(key)
        # JSON round-trip: the builder's (k, n) tuples land as lists.
        assert json.loads(out.read_text(encoding="utf-8")) == json.loads(json.dumps(records[key]))
        before[key] = out.read_bytes()
    assert len(written) == len(records)
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        pts.write_refused_records(records)
    for key in records:
        assert (tmp_path / phase29_prereg.point_record_path(key)).read_bytes() == before[key]
