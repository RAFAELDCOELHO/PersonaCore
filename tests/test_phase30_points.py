"""Plan 30-02: the v5.0 driver — schedule, plan, recipe identity, own-control reader (WR-05).

CPU-only. Nothing here writes under results/: every forged record lands under tmp_path, because a
results/phase3* file would start the phase29 ancestry clock.
"""

import ast
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
