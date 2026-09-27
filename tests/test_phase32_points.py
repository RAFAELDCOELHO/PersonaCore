"""Plan 32-02: the v5.0 driver library (AFRONT-01) — D-01 recall, the record, D-03, D-08, D-11.

CPU-only. Nothing here writes under the real results/ or data/: every sidecar and record lands in
a tmp directory or a scratch git repository.
"""

import ast
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
import phase25_points  # noqa: E402  (same)
import phase25_promotion  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)
import phase32_points as p32  # noqa: E402  (same)

from test_phase25_driver import _scratch_repo  # noqa: E402

MODULE = _SCRIPTS / "phase32_points.py"
KEYS = phase29_prereg.POINT_KEYS()


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """The write refuses a dirty tree, and this suite runs on dirty trees, so the guard is
    RECORDED (the tests/test_phase31_probe.py idiom)."""
    calls = []
    monkeypatch.setattr(p32, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


# =================================================================================================
# Task 1 — D-01 recall override, the record, stage seconds, the D-03 clock and the stop line
# =================================================================================================


def test_measure_stage_forces_recall_without_mutating_the_plan(monkeypatch):
    seen = []
    monkeypatch.setattr(
        phase25_points, "measure_stage", lambda plan, training: seen.append(plan) or "blob"
    )
    plan = phase30_points.point_plan(KEYS[1])
    assert plan["is_control"] is False
    assert p32.measure_stage(plan, {"t": 1}) == "blob"
    assert seen[0]["is_control"] is True
    assert plan["is_control"] is False
    assert {k: v for k, v in seen[0].items() if k != "is_control"} == {
        k: v for k, v in plan.items() if k != "is_control"
    }


def _tier(k, n):
    return {"numerator": k, "denominator": n, "rate": k / n, "questions": [], "per_family": {}}


def _inputs(tmp_path, key=KEYS[1], **overrides):
    plan = phase30_points.point_plan(key)
    steps = plan["pinned_mechanism"]["composed_steps"]
    windows = 7
    recipe = {
        "n_facts": plan["n_facts"],
        "replay_windows": windows,
        "seed": plan["seed"],
        "max_steps": steps,
        "min_refusal_scored_tokens": 3,
        "replay_source": ["data/a.bin", "data/a.mask"],
    }
    training = {
        "seconds": 100.0,
        "resumed_from_step": 0,
        "checkpoint_step": steps,
        "csv": "data/x.csv",
        "csv_sha256": "c" * 64,
        "final_train_loss": 1.5,
        "ppl_adapter_on": 3.0,
        "ppl_adapter_off": 3.1,
        "train_config": {"seed": plan["seed"], "max_steps": steps},
        "git_sha": "0" * 40,
        "adapter": "checkpoints/x_adapter.pt",
        "adapter_sha256": "a" * 64,
        "clip_bind_count": 0,
    }
    recall = {
        "taught": _tier(3, 8),
        "heldout": _tier(2, 8),
        "taught_off": _tier(1, 8),
        "heldout_off": _tier(0, 8),
        "per_family_gain": {"f": 0.25},
    }
    measured = {
        "point_key": key,
        "adapter_sha256": "a" * 64,
        "capability": {
            "adapter_on": 2.5,
            "adapter_off": 2.4,
            "retention_ppl": 5.0,
            "n_targets": 100,
            "retention_total_tokens": 1000,
        },
        "exposure": {},
        "gate05_gaps": [],
        "zero_extraction_has_nll": False,
        "recall": recall,
        "measure_seconds": 50.0,
        "scoring_seconds": 400.0,
        "device": "cpu",
    }
    blob = {
        "shapes": {
            f: {"timing": {"minutes": float(i + 1)}}
            for i, f in enumerate(phase25_record.ATTACK_FAMILIES)
        }
    }
    scored = [
        {"tier": phase25_record.GATED_TIER, "family": f, "hits": [i % 2 == 0], "n_draws": 16}
        for i, f in enumerate(phase25_record.ATTACK_FAMILIES)
    ]
    cache = tmp_path / "draws.json"
    cache.write_text("{}", encoding="utf-8")
    kwargs = {
        "recipe": recipe,
        "training": training,
        "measured": measured,
        "replay": {
            "per_step": [windows] * steps,
            "expected_per_step": windows,
            "steps": steps,
            "teaching_windows_per_step": 8,
        },
        "blob": blob,
        "per_question": [{"q": 1}],
        "scored": scored,
        "score_seconds": 5.0,
        "control_gap": 0.125,
        "draws_cache": cache,
        "provenance": {"note": "filled by plan 04"},
    }
    kwargs.update(overrides)
    return plan, kwargs


def test_stage_seconds_schema(tmp_path):
    _, kw = _inputs(tmp_path)
    stages = p32.stage_seconds(kw["training"], kw["measured"], kw["blob"], kw["score_seconds"])
    assert list(stages) == list(p32.STAGES)
    assert all(isinstance(s["seconds"], float) for s in stages.values())
    assert stages["train"]["seconds"] == 100.0
    assert stages["measure"]["seconds"] == 50.0
    assert stages["recall"]["seconds"] == 400.0
    families = len(phase25_record.ATTACK_FAMILIES)
    assert stages["draw"]["seconds"] == 60.0 * sum(range(1, families + 1))
    assert stages["score"]["seconds"] == 5.0


def test_stage_seconds_refuses_unscored_recall(tmp_path):
    _, kw = _inputs(tmp_path)
    measured = dict(kw["measured"], scoring_seconds=None)
    with pytest.raises(SystemExit, match="recall was not scored"):
        p32.stage_seconds(kw["training"], measured, kw["blob"], 1.0)


def test_build_point_record_satisfies_the_consumers(tmp_path):
    plan, kw = _inputs(tmp_path)
    record = p32.build_point_record(plan, **kw)
    assert record["schema"] == "phase32_point/1" and record["requirement"] == "AFRONT-01"
    assert record["point_key"] == plan["point_key"] and record["arm"] == plan["arm"]
    assert record["axis"] == "ratio" and record["q"] is None and record["clip_norm"] is None
    assert record["is_control"] is False and record["control_key"] == plan["control_key"]
    assert record["recipe"] == kw["recipe"]
    assert record["composed_steps"] == kw["recipe"]["max_steps"]
    assert record["training"]["train_config"] == kw["training"]["train_config"]
    assert set(record["training"]) == set(p32.TRAINING_FIELDS)
    for field, source in p32.RECALL_FIELDS.items():
        assert record[field] == kw["measured"]["recall"][source], field
    assert record["condition_c"]["control_gap"] == kw["control_gap"]
    assert record["per_family_counts"] == phase25_points._family_counts(kw["scored"])
    assert record["draws_per_question"] == mitigation_budget.CURVE_K
    assert record["draws_per_question_source"] == "mitigation_budget.CURVE_K"
    assert record["adapter_sha256"] == kw["training"]["adapter_sha256"]
    assert record["replay"]["per_step"] == kw["replay"]["per_step"]
    assert set(record["stages"]) == set(p32.STAGES)
    assert record["raw_draws"]["sha256"]
    json.dumps(record)  # serialisable
    # flat_record (the frontier's reader) runs on it without KeyError.
    path = phase29_prereg.point_record_path(plan["point_key"])
    flat = phase25_promotion.flat_record(plan["point_key"], record, {**record, "source": path})
    assert flat["point_taught_recall"] == 3 / 8
    # own_control's reads, replayed on the record (the reader itself needs a committed record).
    recipe = kw["recipe"]
    assert (record["seed"], record["training"]["train_config"]["seed"]) == (recipe["seed"],) * 2
    assert record["replay"]["per_step"] == [recipe["replay_windows"]] * recipe["max_steps"]


@pytest.mark.parametrize(
    "mutate, match",
    [
        (lambda kw: kw["training"].update(resumed_from_step=5), "Pitfall 10"),
        (lambda kw: kw["replay"]["per_step"].__setitem__(0, 6), "replay per_step"),
        (lambda kw: kw["replay"]["per_step"].pop(), "replay per_step"),
        (lambda kw: kw["recipe"].update(max_steps=kw["recipe"]["max_steps"] + 1), "disagree"),
        (lambda kw: kw["training"]["train_config"].update(max_steps=1), "disagree"),
        (lambda kw: kw["training"]["train_config"].update(seed=-1), "disagree"),
    ],
)
def test_build_point_record_refuses(tmp_path, mutate, match):
    plan, kw = _inputs(tmp_path)
    mutate(kw)
    with pytest.raises(SystemExit, match=match):
        p32.build_point_record(plan, **kw)


def _stages(seconds):
    return {s: {"seconds": float(seconds)} for s in p32.STAGES}


def _commit_file(root, rel, blob):
    path = root / rel
    path.write_text(json.dumps(blob), encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", rel], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", rel], check=True)


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    root = _scratch_repo(tmp_path)
    monkeypatch.setattr(p32, "_GIT_ROOT", root)
    monkeypatch.setattr(p32, "_ROOT", root)
    monkeypatch.setattr(phase30_points, "_ROOT", root)
    return root


def test_cumulative_seconds_over_committed_records(scratch):
    path = phase29_prereg.point_record_path
    _commit_file(scratch, path(KEYS[0]), {"stages": _stages(10)})
    _commit_file(scratch, path(KEYS[1]), {"stages": _stages(3.5)})
    _commit_file(scratch, path(KEYS[2]), {"rule": "PREREG-03"})
    (scratch / path(KEYS[3])).write_text(json.dumps({"stages": _stages(99)}), encoding="utf-8")
    tracked = p32.tracked_results()
    assert path(KEYS[3]) not in tracked
    assert p32.cumulative_seconds(tracked) == len(p32.STAGES) * (10 + 3.5)


def test_cumulative_seconds_refuses_a_record_without_stages(scratch):
    _commit_file(scratch, phase29_prereg.point_record_path(KEYS[0]), {"x": 1})
    with pytest.raises(SystemExit, match="neither stages nor rule"):
        p32.cumulative_seconds(p32.tracked_results())


def test_stop_line_is_read_from_the_committed_budget():
    budget = json.loads((_ROOT / p32.BUDGET_PATH).read_text(encoding="utf-8"))
    assert p32.stop_line_seconds(p32.tracked_results()) == budget["stop_line"]["seconds"]
    with pytest.raises(SystemExit, match="not TRACKED"):
        p32.stop_line_seconds([])


def _docstring_ids(tree):
    owners = [tree] + [
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    return {
        id(o.body[0].value)
        for o in owners
        if o.body and isinstance(o.body[0], ast.Expr) and isinstance(o.body[0].value, ast.Constant)
    }


def test_ast_stop_line_paths_and_recipe_values_are_never_typed():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    docs = _docstring_ids(tree)
    constants = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and id(n) not in docs]
    budget = json.loads((_ROOT / p32.BUDGET_PATH).read_text(encoding="utf-8"))
    stop = budget["stop_line"]["seconds"]
    assert [n.lineno for n in constants if type(n.value) is float and n.value == stop] == []
    paths = set(phase29_prereg.V5_RESULT_PATHS)
    assert [n.value for n in constants if isinstance(n.value, str) and n.value in paths] == []
    banned = {32, 256, 1337, 15}
    assert [n.lineno for n in constants if type(n.value) is int and n.value in banned] == []
    # Non-vacuous: the walk sees this module's numeric constants at all.
    assert any(type(n.value) is int for n in constants)


def test_import_is_torch_free():
    code = (
        "import sys; sys.path.insert(0, 'scripts'); import phase32_points; "
        "assert 'torch' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], cwd=_ROOT, check=True)


# =================================================================================================
# Task 2 — D-08 session shas, write-once, D-11 one-path commit, git-surface and census gates
# =================================================================================================

import mitigation_gate  # noqa: E402  (scripts/ is not a package)

from test_phase25_driver import _git_argv_subcommands, _git_surface_failure  # noqa: E402
from test_phase29_prereg import _gate_retype_failures, _planted  # noqa: E402

V5_DRIVER_MODULES = sorted(_SCRIPTS.glob("phase32_*.py"))


def _head():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _pre_fix_sha():
    """The parent of the newest commit touching scripts/phase30_points.py (the 32-01 fix)."""
    newest = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "scripts/phase30_points.py"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return subprocess.run(
        ["git", "rev-parse", newest + "^"], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_record_session_appends(tmp_path, monkeypatch):
    monkeypatch.setattr(p32, "_ROOT", tmp_path)
    first = p32.record_session(KEYS[0])
    second = p32.record_session(KEYS[0])
    assert len(first) == 1 and len(second) == 2 and second[0] == first[0]
    assert {s["git_sha"] for s in second} == {_head()}
    assert all(s["started_utc"] for s in second)
    on_disk = json.loads(p32.sessions_sidecar(KEYS[0]).read_text(encoding="utf-8"))
    assert on_disk == second
    assert p32.sessions_sidecar(KEYS[0]).is_relative_to(tmp_path / "data")
    with pytest.raises(SystemExit):
        p32.sessions_sidecar("not_a_key")


def test_wr02_pinned_unchanged_passes_for_head():
    p32.prove_pinned_unchanged([_head(), _head()])


def test_wr02_natural_red_on_the_pre_fix_commit():
    with pytest.raises(SystemExit, match="D-08") as refused:
        p32.prove_pinned_unchanged([_head(), _pre_fix_sha()])
    assert "scripts/phase30_points.py" in str(refused.value)


def test_wr02_unknown_sha_refuses():
    with pytest.raises(SystemExit, match="unknown sha"):
        p32.prove_pinned_unchanged(["f" * 40])


def _record_for_write():
    return {"point_key": KEYS[0], "training": {"git_sha": _head()}}


def test_write_once_refuses_an_existing_target_before_the_dirty_check(scratch, clean_tree):
    out = scratch / phase29_prereg.point_record_path(KEYS[0])
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        p32.write_point_record(KEYS[0], _record_for_write(), shas=[_head()])
    assert clean_tree == []
    assert out.read_text(encoding="utf-8") == "{}"


def test_write_once_dirty_check_then_d08_then_write(scratch, clean_tree):
    rel = p32.write_point_record(KEYS[0], _record_for_write(), shas=[_head()])
    assert rel == phase29_prereg.point_record_path(KEYS[0])
    assert json.loads((scratch / rel).read_text(encoding="utf-8")) == _record_for_write()
    assert len(clean_tree) == 1
    call = clean_tree[0]
    assert call["pathspec"] == ("scripts", "src", "results", f":(exclude){rel}")
    assert call["cwd"] == p32._CODE_ROOT
    assert call["who"] == "phase32_points" and call["detail"]


def test_write_once_refuses_on_a_stale_session_sha(scratch, clean_tree):
    with pytest.raises(SystemExit, match="D-08"):
        p32.write_point_record(KEYS[0], _record_for_write(), shas=[_pre_fix_sha()])
    assert not (scratch / phase29_prereg.point_record_path(KEYS[0])).exists()
    # The training sidecar's own git_sha is checked even when the session list is clean.
    stale = {"point_key": KEYS[0], "training": {"git_sha": _pre_fix_sha()}}
    with pytest.raises(SystemExit, match="D-08"):
        p32.write_point_record(KEYS[0], stale, shas=[_head()])


def _git_out(root, *argv):
    return subprocess.run(
        ["git", "-C", str(root), *argv], capture_output=True, text=True, check=True
    ).stdout


def test_commit_path_commits_exactly_one_path(scratch):
    rel = phase29_prereg.point_record_path(KEYS[0])
    (scratch / rel).write_text("{}", encoding="utf-8")
    (scratch / "results" / "other.json").write_text("{}", encoding="utf-8")
    _git_out(scratch, "add", "results/other.json")
    p32.commit_path(rel, p32.commit_message(KEYS[0]))
    assert _git_out(scratch, "show", "--name-only", "--format=", "HEAD").split() == [rel]
    assert _git_out(scratch, "log", "-1", "--format=%s").strip() == (
        f"feat(32): record sweep point {KEYS[0]}"
    )
    assert "results/other.json" in _git_out(scratch, "diff", "--cached", "--name-only")
    # No-op: already committed and unchanged.
    with pytest.raises(SystemExit, match="NO-OP"):
        p32.commit_path(rel, "x")


def test_commit_path_refusals(scratch):
    (scratch / "stray.json").write_text("{}", encoding="utf-8")
    for bad in ("stray.json", "results/../stray.json"):
        with pytest.raises(SystemExit, match="not under results/"):
            p32.commit_path(bad, "x")
    with pytest.raises(SystemExit, match="does not exist"):
        p32.commit_path(phase29_prereg.point_record_path(KEYS[1]), "x")
    rel = phase29_prereg.point_record_path(KEYS[2])
    (scratch / rel).write_text("{}", encoding="utf-8")
    _git_out(scratch, "checkout", "-q", "-b", "scratch-branch")
    with pytest.raises(SystemExit, match="not main"):
        p32.commit_path(rel, "x")


def test_commit_untracked_commits_only_the_uncommitted(scratch):
    done, fresh = (phase29_prereg.point_record_path(k) for k in KEYS[:2])
    _commit_file(scratch, done, {"rule": "PREREG-03"})
    (scratch / fresh).write_text("{}", encoding="utf-8")
    committed = p32.commit_untracked([done, fresh], lambda rel: f"feat(32): {rel}")
    assert committed == [fresh]
    assert _git_out(scratch, "show", "--name-only", "--format=", "HEAD").split() == [fresh]
    assert p32.commit_untracked([done, fresh], lambda rel: "x") == []


def test_commit_messages():
    assert p32.commit_message(KEYS[0]) == f"feat(32): record sweep point {KEYS[0]}"
    assert p32.commit_message(KEYS[0], refused=True) == (
        f"feat(32): record PREREG-03 refused point {KEYS[0]}"
    )


def _git_helper_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (getattr(node.func, "id", None) or getattr(node.func, "attr", None)) == "_git"
    ]


def test_git_surface_is_bounded(tmp_path):
    allowed = set(p32.ALLOWED_GIT_ACTIONS) | set(p32.READ_ONLY_GIT_ACTIONS)
    offenders, message = _git_surface_failure(MODULE, allowed)
    assert offenders == [], message
    used = {row[0] for row in _git_argv_subcommands(MODULE)}
    assert {"add", "commit"} <= used  # non-vacuous
    assert V5_DRIVER_MODULES, "no scripts/phase32_*.py found — the census is blind"
    for path in V5_DRIVER_MODULES:
        assert _git_helper_calls(path) == [], path
    # Natural RED: the Phase 31 probe calls its _git helper.
    assert _git_helper_calls(_SCRIPTS / "phase31_probe.py")
    # Planted RED: a push is outside the surface.
    source = MODULE.read_text(encoding="utf-8")
    planted = _planted(tmp_path, source, source + '\n_X = ["git", "push"]\n', "push.py")
    (tmp_path / "push.py").write_text(planted, encoding="utf-8")
    offenders, _ = _git_surface_failure(tmp_path / "push.py", allowed)
    assert [row[0] for row in offenders] == ["push"]


def test_census_gates_over_the_v5_driver():
    needle = "train_arm" + "("
    for path in V5_DRIVER_MODULES:
        source = path.read_text(encoding="utf-8")
        assert _gate_retype_failures(source, mitigation_gate.F_Y) == [], path
        assert needle not in source, path
        replaces = [
            node.lineno
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Attribute)
            and node.attr == "replace"
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        ]
        assert replaces == [], path
    # Natural REDs: the same helper fires on the two modules that define gate functions.
    for name, gate in (
        ("phase27_prereg.py", "cleared_abc"),
        ("phase20_gate_coverage.py", "corrected_point_verdict"),
    ):
        failures = _gate_retype_failures(
            (_SCRIPTS / name).read_text(encoding="utf-8"), mitigation_gate.F_Y
        )
        assert any(gate in f for f in failures), (name, failures)
