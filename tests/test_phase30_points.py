"""Plan 30-02: the v5.0 driver — schedule, plan, recipe identity, own-control reader (WR-05).

CPU-only. Nothing here writes under results/: every forged record lands under tmp_path, because a
results/phase3* file would start the phase29 ancestry clock.
"""

import ast
import copy
import json
import pathlib
import re
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


def _commit(root):
    """Commit everything under ``root`` (a tmp repo): the reader reads committed blobs (CR-01)."""

    def git(*args):
        subprocess.run(
            ("git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false")
            + args,
            cwd=root,
            capture_output=True,
            check=True,
        )

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "--allow-empty", "-m", "fixture")


def _good_control(leg, *, taught=(790, 1008), heldout=(346, 648)):
    """A forged own-control record in the v4.0 field shapes, carrying the v5.0 recipe."""
    recipe = pts.recipe_identity(leg)
    return {
        "point_key": phase29_prereg.control_key(leg),
        "arm": pts._arm_of_leg(leg),
        "axis": "ratio",
        "q": None,
        "clip_norm": None,
        "recipe": recipe,
        # What the control TRAINED with, in the v4.0 record shape (WR-04).
        "seed": phase25_points.SWEEP_SEED,
        "composed_steps": mitigation_budget.STEP_BUDGET,
        "training": {
            "train_config": {
                "seed": phase25_points.SWEEP_SEED,
                "max_steps": mitigation_budget.STEP_BUDGET,
            }
        },
        # Phase 32 D-19: what the control's training drew, counted per step
        "replay": {
            "per_step": [recipe["replay_windows"]] * recipe["max_steps"],
            "expected_per_step": recipe["replay_windows"],
            "steps": recipe["max_steps"],
        },
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
    _commit(tmp_path)
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


@pytest.mark.parametrize(
    "path",
    [
        ("seed",),
        ("composed_steps",),
        ("training", "train_config", "seed"),
        ("training", "train_config", "max_steps"),
    ],
)
def test_wr04_refuses_a_control_that_trained_off_its_recipe(tmp_path, monkeypatch, path):
    """WR-04: a control whose measured training fields disagree with the point's recipe is refused
    even when its declared ``recipe`` is correct."""
    record = copy.deepcopy(_good_control("n8"))
    leaf = record
    for step in path[:-1]:
        leaf = leaf[step]
    leaf[path[-1]] += 1
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": record})
    with pytest.raises(SystemExit, match="WR-04"):
        pts.own_control(_non_control("n8"), tracked, point_recipe=pts.recipe_identity("n8"))


def _no_replay(record):
    del record["replay"]  # the fixture shape before Phase 32 D-19: natural RED


def _one_step_short(record):
    record["replay"]["per_step"].pop()


def _one_step_low(record):
    record["replay"]["per_step"][0] -= 1


@pytest.mark.parametrize("breaks", [_no_replay, _one_step_short, _one_step_low])
def test_wr04_own_control_refuses_a_control_without_replay_counts(tmp_path, monkeypatch, breaks):
    """Phase 32 D-19: a control is refused unless its per-step replay equals its recipe's."""
    record = copy.deepcopy(_good_control("n8"))
    breaks(record)
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": record})
    with pytest.raises(SystemExit, match=r"D-19, WR-04.*replay"):
        pts.own_control(_non_control("n8"), tracked, point_recipe=pts.recipe_identity("n8"))


def test_in04_recipe_identity_refuses_a_foreign_replay_module(monkeypatch):
    """D-10 IN-04: the module part of every REPLAY_SOURCE name must be teach_persona."""
    foreign = "other_module.DIALOG_TRAIN_BIN"
    monkeypatch.setattr(
        phase29_prereg, "REPLAY_SOURCE", (foreign, "teach_persona.DIALOG_TRAIN_MASK")
    )
    with pytest.raises(SystemExit, match="IN-04") as excinfo:
        pts.recipe_identity("n8")
    assert foreign in str(excinfo.value)


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
    _commit(tmp_path)
    with pytest.raises(SystemExit, match="seed"):
        pts.require_calibrated_recipe("n8", pts.recipe_identity("n8"), tracked)


def test_cr01_refuses_a_tracked_record_edited_on_disk(tmp_path, monkeypatch):
    """CR-01: a tracked record edited but not committed is refused; the committed blob is read."""
    tracked = _v5_tree(tmp_path, monkeypatch, controls={"n8": _good_control("n8")})
    recipe = pts.recipe_identity("n8")
    assert pts.own_control(_non_control("n8"), tracked, point_recipe=recipe)
    for rel in (pts.CALIBRATION_PATH, phase29_prereg.point_record_path(CONTROLS[0])):
        committed = (tmp_path / rel).read_bytes()
        (tmp_path / rel).write_bytes(committed.replace(b"}", b', "edited": 1}', 1))
        with pytest.raises(SystemExit, match="differs from its committed blob"):
            pts.own_control(_non_control("n8"), tracked, point_recipe=recipe)
        (tmp_path / rel).write_bytes(committed)
    # Tracked by the caller's list but never committed: refused too.
    rel = phase29_prereg.point_record_path(CONTROLS[1])
    _write(tmp_path, rel, _good_control("n64"))
    with pytest.raises(SystemExit, match="no committed blob"):
        pts.own_control(
            _non_control("n64"), tracked + [rel], point_recipe=pts.recipe_identity("n64")
        )


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
    # An identical re-run writes nothing; a DIFFERENT blob for an existing record is refused.
    assert pts.write_refused_records(records) == []
    changed = copy.deepcopy(records)
    changed[next(iter(changed))]["edited"] = True
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        pts.write_refused_records(changed)
    for key in records:
        assert (tmp_path / phase29_prereg.point_record_path(key)).read_bytes() == before[key]


def _refused_leg(leg):
    recipe = pts.prereg_recipe(pts.recipe_identity(leg))
    return {
        k: phase29_prereg.refused_record(k, taught=(0, 1), heldout=(0, 1), recipe=recipe)
        for k in phase29_prereg.leg_keys(leg)
        if k != phase29_prereg.control_key(leg)
    }


def test_review_wr05_refused_leg_write_is_all_or_resumable(tmp_path, monkeypatch):
    """Review WR-05: a failure part-way never leaves the leg permanently unwritable."""
    monkeypatch.setattr(pts, "_ROOT", tmp_path)
    records = _refused_leg("n8")
    keys = list(records)
    paths = [tmp_path / phase29_prereg.point_record_path(k) for k in keys]

    # An unserialisable blob anywhere fails BEFORE any file lands.
    with pytest.raises(TypeError):
        pts.write_refused_records(dict(records, **{keys[1]: {"bad": object()}}))
    assert not any(path.exists() for path in paths)

    # A write killed after the first file: the retry completes the leg.
    real = pts.phase25_run.atomic_write_json
    calls = []

    def _dies_on_second(path, blob):
        calls.append(path)
        if len(calls) > 1:
            raise KeyboardInterrupt
        return real(path, blob)

    monkeypatch.setattr(pts.phase25_run, "atomic_write_json", _dies_on_second)
    with pytest.raises(KeyboardInterrupt):
        pts.write_refused_records(records)
    monkeypatch.setattr(pts.phase25_run, "atomic_write_json", real)
    assert [path.exists() for path in paths] == [True] + [False] * (len(paths) - 1)
    assert pts.write_refused_records(records) == paths[1:]
    assert all(path.exists() for path in paths)

    # A partial leg or a mixed leg is refused.
    with pytest.raises(SystemExit, match="non-controls"):
        pts.write_refused_records({keys[0]: records[keys[0]]})
    with pytest.raises(SystemExit, match="span legs"):
        pts.write_refused_records(dict(records, **_refused_leg("n64")))


# =================================================================================================
# Task 3: AST guard — no WR-05 carrier or dp control key in any v5.0 module (D-14)
# =================================================================================================

_CARRIERS = frozenset(
    {
        "control_key_for",
        "control_reading",
        "record_kwargs",
        "control_readings",
        "_adversarial_extras",
    }
)
_V4_PARSERS = frozenset({"point_plan", "prefix_for", "n_facts_for", "exact_axis_value"})
_DP_KEY = re.compile(r"dp_n\d+(_sigma\d+p\d+)?")


def _docstring_nodes(tree):
    """The first-statement string Expr of the Module and of every def/class: exempt prose."""
    owners = [tree] + [
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    return {
        id(owner.body[0].value)
        for owner in owners
        if owner.body
        and isinstance(owner.body[0], ast.Expr)
        and isinstance(owner.body[0].value, ast.Constant)
        and isinstance(owner.body[0].value.value, str)
    }


_V4_MODULES = ("phase25_points", "phase25_promotion")


def _wr05_failures(source):
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    # Review WR-06: every name a v4.0 module is bound to, aliases included.
    modules = set(_V4_MODULES) | {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name in _V4_MODULES
    }

    # Dated continuation, 2026-09-27 (Phase 32 D-17): FRONTIER_SCHEMA (phase29_prereg) requires
    # the frontier to carry ``verdicts.control_readings``. That key is data, not a carrier call,
    # so the literal "control_readings" is exempt in exactly two JSON-field positions: a dict
    # literal key and a subscript string. getattr, a bare string, the Name, the Attribute and the
    # import stay flagged, and every OTHER carrier stays flagged even as a dict key.
    # Dated continuation, 2026-09-28 (Phase 32 security gate, T-32-01 / review WR-03): the subscript
    # form is exempt only when its value is a chain of subscripts rooted at a plain Name that is
    # not a v4.0 module binding nor ``sys`` (``frontier["verdicts"]["control_readings"]``). Any
    # Call (``vars(m)``), Attribute (``m.__dict__``, ``sys.modules``) or module Name in the chain
    # can name a module namespace, so it stays flagged. Residual: a namespace first bound to a
    # plain name (``d = vars(m); d["control_readings"]``) needs dataflow and is not caught here.
    def _json_root(value):
        while isinstance(value, ast.Subscript):
            value = value.value
        return isinstance(value, ast.Name) and value.id not in modules | {"sys"}

    json_key_ids = {
        id(k)
        for n in ast.walk(tree)
        if isinstance(n, ast.Dict)
        for k in n.keys
        if isinstance(k, ast.Constant) and k.value == "control_readings"
    } | {
        id(n.slice)
        for n in ast.walk(tree)
        if isinstance(n, ast.Subscript)
        and isinstance(n.slice, ast.Constant)
        and n.slice.value == "control_readings"
        and _json_root(n.value)
    }
    failures = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", "?")
        if isinstance(node, ast.Name) and node.id in _CARRIERS:
            failures.append(f"carrier name {node.id} at line {line}")
        elif isinstance(node, ast.Attribute) and node.attr in _CARRIERS:
            failures.append(f"carrier attribute {node.attr} at line {line}")
        elif (
            isinstance(node, ast.Attribute)
            and node.attr in _V4_PARSERS
            and isinstance(node.value, ast.Name)
            and node.value.id in modules
        ):
            failures.append(f"v4.0 parser {node.value.id}.{node.attr} at line {line}")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in modules
        ):
            failures.append(f"getattr on v4.0 module {node.args[0].id} at line {line}")
        elif isinstance(node, ast.ImportFrom) and node.module in _V4_MODULES:
            failures += [
                f"import {alias.name} from {node.module} at line {line}"
                for alias in node.names
                if alias.name in _CARRIERS | _V4_PARSERS
            ]
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and _DP_KEY.fullmatch(node.value)
        ):
            failures.append(f"dp key constant {node.value!r} at line {line}")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and id(node) not in json_key_ids
            and (node.value in _CARRIERS or node.value.startswith("dp_n"))
        ):
            # getattr / importlib spell a carrier as a string; "dp_n" + ... builds a dp key.
            failures.append(f"carrier or dp-key string {node.value!r} at line {line}")
        elif (
            isinstance(node, ast.JoinedStr)
            and node.values
            and isinstance(node.values[0], ast.Constant)
            and isinstance(node.values[0].value, str)
            and node.values[0].value.startswith("dp_n")
        ):
            failures.append(f"dp key f-string at line {line}")
    return failures


def test_ast_guard_no_v5_module_reaches_a_dp_control():
    modules = sorted(p for n in range(30, 35) for p in _SCRIPTS.glob(f"phase{n}_*.py"))
    assert POINTS_MODULE in modules, "the census is blind to scripts/phase30_points.py"
    for path in modules:
        assert _wr05_failures(path.read_text(encoding="utf-8")) == [], path
    # NON-VACUITY (natural RED): the v4.0 resolver defines and calls the carrier and builds dp keys.
    v4 = _wr05_failures((_SCRIPTS / "phase25_points.py").read_text(encoding="utf-8"))
    assert any("control_key_for" in f for f in v4), v4
    assert any("dp key f-string" in f for f in v4), v4


def test_ast_guard_planted_red_per_class(tmp_path):
    source = POINTS_MODULE.read_text(encoding="utf-8")
    dp_key = "dp_n8_sigma0p000000"
    assert _DP_KEY.fullmatch(dp_key)
    for name, plant in (
        ("carrier.py", "\n_X = phase25_points.control_key_for\n"),
        ("parser.py", "\n_X = phase25_points.point_plan\n"),
        ("promotion.py", "\nfrom phase25_promotion import control_readings\n"),
        ("constant.py", f"\n_X = {dp_key!r}\n"),
        ("fstring.py", '\n_X = f"dp_n{8}"\n'),
        # Review WR-06: an aliased import, getattr, and a concatenated dp key.
        ("alias.py", '\nimport phase25_points as p25\n_X = p25.point_plan("adv_n8")\n'),
        ("getattr.py", '\n_X = getattr(phase25_points, "control_key_for")\n'),
        ("getattr_parser.py", '\n_X = getattr(phase25_points, "point_plan")\n'),
        ("concat.py", '\n_X = "dp_n" + "8"\n'),
        # Phase 32 D-17: planted because no scripts/ module spells this form; the other forms use
        # natural occurrences, see test_ast_guard_d17_natural_cases. (The ImportFrom form of
        # control_readings is already planted above as promotion.py.)
        ("d17_getattr.py", '\n_X = getattr(phase25_promotion, "control_readings")\n'),
        ("d17_attribute.py", "\n_X = phase25_promotion.control_readings\n"),
        # Dated continuation, 2026-09-28 (Phase 32 security gate, T-32-01 / review WR-03): the
        # D-17 subscript exemption accepted ANY X["control_readings"], so these four module-
        # namespace reads of the carrier returned []. Each must be flagged.
        ("wr03_vars.py", '\n_X = vars(phase25_promotion)["control_readings"]\n'),
        ("wr03_dunder_dict.py", '\n_X = phase25_promotion.__dict__["control_readings"]\n'),
        (
            "wr03_vars_alias.py",
            '\nimport phase25_promotion as p25p\n_X = vars(p25p)["control_readings"]\n',
        ),
        (
            "wr03_sys_modules.py",
            '\nimport sys\n_X = sys.modules["phase25_promotion"].__dict__["control_readings"]\n',
        ),
        # Only "control_readings" is exempt as a dict key; every other carrier stays flagged there.
        ("d17_other_key.py", '\n_X = {"record_kwargs": 1}\n'),
    ):
        planted = _planted(tmp_path, source, source + plant, name)
        assert _wr05_failures(planted), name
    # The docstring exemption, non-vacuously: the SAME string exempt as a docstring, flagged as a
    # bare expression statement after it.
    doc = _planted(
        tmp_path, source, source + f"\n\ndef _x():\n    {dp_key!r}\n    pass\n", "doc.py"
    )
    assert _wr05_failures(doc) == []
    bare = _planted(
        tmp_path, source, source + f"\n\ndef _x():\n    pass\n    {dp_key!r}\n", "bare.py"
    )
    assert any("dp key constant" in f for f in _wr05_failures(bare))
    assert POINTS_MODULE.read_text(encoding="utf-8") == source


def test_ast_guard_d17_allows_control_readings_only_as_a_json_key(tmp_path):
    """Phase 32 D-17: FRONTIER_SCHEMA's ``verdicts.control_readings`` key is writable as data."""
    source = POINTS_MODULE.read_text(encoding="utf-8")
    for name, plant in (
        ("d17_dict_key.py", '\n_X = {"control_readings": 1}\n'),
        ("d17_subscript.py", '\n_Y = {}\n_Y["control_readings"] = 1\n'),
    ):
        assert _wr05_failures(_planted(tmp_path, source, source + plant, name)) == [], name
    assert POINTS_MODULE.read_text(encoding="utf-8") == source


def _control_readings_lines(source):
    """``(json_lines, other_lines)`` of every "control_readings" occurrence, by AST position."""
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    json_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            json_ids |= {id(k) for k in node.keys if k is not None}
        elif isinstance(node, ast.Subscript):
            json_ids.add(id(node.slice))
    json_lines, other_lines = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == "control_readings":
            if id(node) in json_ids:
                json_lines.add(node.lineno)
            elif id(node) not in docstrings:
                other_lines.add(node.lineno)
        elif (isinstance(node, ast.Name) and node.id == "control_readings") or (
            isinstance(node, ast.Attribute) and node.attr == "control_readings"
        ):
            other_lines.add(node.lineno)
    return json_lines, other_lines


def test_ast_guard_d17_natural_cases():
    """Phase 32 D-17, natural RED/GREEN in three unedited scripts: the JSON-key positions are
    exempt, every other spelling of control_readings stays flagged. Lines are computed by AST."""
    for name in ("phase29_prereg.py", "phase23_matched_prereg.py", "phase25_promotion.py"):
        src = (_SCRIPTS / name).read_text(encoding="utf-8")
        json_lines, other_lines = _control_readings_lines(src)
        assert other_lines, name
        if name != "phase23_matched_prereg.py":
            assert json_lines, name
        flagged = {
            int(m)
            for f in _wr05_failures(src)
            if "control_readings" in f
            for m in re.findall(r"at line (\d+)", f)
        }
        assert flagged == other_lines, (name, flagged, other_lines)
        assert not (flagged & json_lines), (name, flagged, json_lines)
