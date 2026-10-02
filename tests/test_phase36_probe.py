"""Plan 36-03: the Phase 36 probe driver core and its E1 front (COST-01, D-01, D-11..D-18).

CPU-only, never MPS. Nothing here writes under the real results/, data/, checkpoints/ or ledger/:
every sidecar, ledger, heartbeat and emitted record lands under a tmp directory, and the git
writers run against a scratch repository.
"""

import ast
import datetime
import hashlib
import inspect
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

import phase25_run  # noqa: E402  (scripts/ is not a package)
import phase36_ledger  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)
import phase36_probe as probe  # noqa: E402  (same)

from test_phase25_driver import (  # noqa: E402
    _git_argv_subcommands,
    _git_surface_failure,
    _scratch_repo,
)
from test_phase36_prereg import _untested_functions  # noqa: E402

MODULE = _SCRIPTS / "phase36_probe.py"


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """The run and emit refuse a dirty tree, and this suite runs on dirty trees, so the guard is
    RECORDED (the tests/test_phase31_probe.py idiom)."""
    calls = []
    monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


def _head():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _pre_fix_sha():
    """The parent of the newest commit touching scripts/phase25_run.py (a pinned module)."""
    newest = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "scripts/phase25_run.py"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return subprocess.run(
        ["git", "rev-parse", newest + "^"], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


# =================================================================================================
# Task 1 — identity, isolation, the reading gate, silencing, the draw timer
# =================================================================================================


def test_isolation_labels():
    assert probe.prove_isolated_label("probe36") == "probe36"
    assert probe.prove_isolated_label("probe36_e1_run.json") == "probe36_e1_run.json"
    for bad in ("phase36_x", "phase41", "phase25_calibration_x", "probe31_x"):
        with pytest.raises(SystemExit):
            probe.prove_isolated_label(bad)


def test_isolation_sidecar_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    paths = [probe.run_sidecar("e1"), probe.sessions_sidecar("e1")]
    paths += [probe.arm_record_path("e1", rep) for rep in (1, 2)]
    assert [p.name for p in paths] == [
        "probe36_e1_run.json",
        "probe36_e1_sessions.json",
        "probe36_e1_rep1_arm.json",
        "probe36_e1_rep2_arm.json",
    ]
    assert all(p.parent == tmp_path / "data" for p in paths)
    for helper in (probe.run_sidecar, probe.sessions_sidecar):
        with pytest.raises(SystemExit):
            helper("e4")
    with pytest.raises(SystemExit):
        probe.arm_record_path("e4", 1)
    assert probe._data_path("probe36_x.json") == tmp_path / "data" / "probe36_x.json"
    with pytest.raises(SystemExit):
        probe._data_path("phase36_x.json")
    assert set(probe.RUN_ORDER) == set(phase36_prereg.PROBE_FRONTS)
    assert probe.RUN_ORDER[0] == "e5" and probe.RUN_ORDER[-1] == "e1"


def test_isolation_committed_input_paths_are_the_pins_own():
    import phase19_erasure
    import phase19_run

    rel = phase19_run.TARGET_CURVE_PATH.relative_to(_ROOT).as_posix()
    assert probe.CURVE_RECORD == rel
    erased = phase19_erasure.arm_record_path("erased").relative_to(_ROOT).as_posix()
    assert probe.ERASED_RECORD == erased


@pytest.mark.parametrize(
    "blob",
    [
        {"per_fact": 1},
        {"stages": {"hits": [1, 2]}},
        {"stages": {"runs": [{"recall_rate": 0.5}]}},
        {"configuration": {"nll": 1.0}},
        {"stages": {"note": "taught ON: 3/4"}},
        {"stages": [["x"]]},
        {"stages": {"draws": b"x"}},
    ],
)
def test_record_gate_refuses_readings_and_free_text(blob):
    with pytest.raises(SystemExit):
        probe.prove_no_reading(blob)


def test_record_gate_accepts_numbers_bools_none_and_allowlisted_strings():
    blob = {
        "front": "e1",
        "probe_key": "v6/36/probes/e1",
        "gates_nothing": True,
        "stages": {"runs": [{"total_seconds": 1.5, "draws": 3, "spread": None}]},
        "configuration": {"ordering": "greedy", "seeds": [1337, 2024]},
        "provenance": {"run": {"device": "cpu"}, "module_sha256": {"scripts/x.py": "ab"}},
        "beside": {"path": "results/x.json", "sha256": "ab"},
    }
    assert probe.prove_no_reading(blob) is blob


def test_record_gate_beside_stage_names_are_the_one_exemption():
    beside = probe.phase31_beside()
    stages = beside[probe.BESIDE_KEY][probe.BESIDE_STAGES_KEY]
    assert "recall" in stages  # the half the exemption exists for
    probe.prove_no_reading(beside)
    # Values must still be numbers.
    bad = json.loads(json.dumps(beside))
    bad[probe.BESIDE_KEY][probe.BESIDE_STAGES_KEY]["recall"] = "1079 s"
    with pytest.raises(SystemExit, match="not a number"):
        probe.prove_no_reading(bad)
    # The same key anywhere else is a reading.
    with pytest.raises(SystemExit, match="names a reading"):
        probe.prove_no_reading({"stage_seconds": {"recall": 1.0}})
    with pytest.raises(SystemExit, match="names a reading"):
        probe.prove_no_reading({"x": {probe.BESIDE_STAGES_KEY: {"recall": 1.0}}})


def test_silenced_swallows_prints(capsys):
    with probe.silenced():
        print("taught ON: 3/4 = 0.75")
    print("after")
    assert capsys.readouterr().out == "after\n"


def test_silenced_restores_stdout_after_an_exception():
    before = sys.stdout
    with pytest.raises(RuntimeError), probe.silenced():
        raise RuntimeError("boom")
    assert sys.stdout is before


def test_draw_timer_restores(monkeypatch):
    import phase14_recall

    def fake(model, prompt_ids, device, forbid, **kw):
        return [1, 2, 3], kw.get("stopped", True)

    monkeypatch.setattr(phase14_recall, "_complete", fake)
    with pytest.raises(RuntimeError), probe.DrawTimer() as timer:
        assert phase14_recall._complete is not fake
        assert phase14_recall._complete(None, [0], "cpu", None) == ([1, 2, 3], True)
        phase14_recall._complete(None, [0], "cpu", None, stopped=False)
        raise RuntimeError("boom")
    assert phase14_recall._complete is fake
    assert [set(row) for row in timer.rows] == [{"seconds", "tokens", "at_cap"}] * 2
    assert [(r["tokens"], r["at_cap"]) for r in timer.rows] == [(3, False), (3, True)]
    assert all(isinstance(r["seconds"], float) and r["seconds"] >= 0 for r in timer.rows)


# =================================================================================================
# Task 1 — run_front, the ledger and the heartbeat (D-11, D-12, B1)
# =================================================================================================


def _fake_stage(state):
    state.update(stage="e5_fake")
    return {"configuration": {"slots": 3}, "total_seconds": 0.5, "reused": {"e5": False}}


def _fake_builder(stages):
    return {"total_seconds": stages["total_seconds"]}, 1


def _planted(tmp_path, monkeypatch, stage=_fake_stage):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    monkeypatch.setitem(probe.STAGES, "e5", stage)
    monkeypatch.setitem(probe.RECORD_BUILDERS, "e5", _fake_builder)
    return {"heartbeat_path": tmp_path / "hb.jsonl", "ledger_path": tmp_path / "ledger.jsonl"}


def _beats(path):
    return [json.loads(t) for t in path.read_text(encoding="utf-8").splitlines()]


def test_run_front_writes_ledger_and_heartbeat(tmp_path, monkeypatch):
    paths = _planted(tmp_path, monkeypatch)
    run = probe.run_front("e5", **paths)
    rid = phase36_ledger.run_id(36, "probes", "e5")
    lines = phase36_ledger.read_ledger(paths["ledger_path"])
    assert [(x["event"], x["run_id"], x["front"]) for x in lines] == [
        ("start", rid, "probes"),
        ("end", rid, "probes"),
    ]
    assert lines[1]["record"] == phase36_prereg.probe_record("e5")
    beats = _beats(paths["heartbeat_path"])
    assert beats and all(b["point"] == rid for b in beats)
    sidecar = json.loads(probe.run_sidecar("e5").read_text(encoding="utf-8"))
    assert sidecar == run
    assert run["reused"] == {"e5": False} and "reused" not in run["stages"]
    assert run["run_id"] == rid and run["device"] == "cpu"
    assert run["run_git_sha"] == _head()
    sessions = json.loads(probe.sessions_sidecar("e5").read_text(encoding="utf-8"))
    assert [s["git_sha"] for s in sessions] == [_head()]
    # A second call skips the finished front: no new ledger line, the same sidecar.
    assert probe.run_front("e5", **paths) == run
    assert len(phase36_ledger.read_ledger(paths["ledger_path"])) == len(lines)


def test_run_front_crash_leaves_an_open_start(tmp_path, monkeypatch):
    def crash(state):
        state.update(stage="e5_fake")
        raise RuntimeError("stage died")

    paths = _planted(tmp_path, monkeypatch, crash)
    with pytest.raises(RuntimeError, match="stage died"):
        probe.run_front("e5", **paths)
    lines = phase36_ledger.read_ledger(paths["ledger_path"])
    assert [x["event"] for x in lines] == ["start"]
    assert not probe.run_sidecar("e5").exists()


def test_run_front_beats_before_the_thread(tmp_path, monkeypatch):
    """B1: the 60-s thread first beats after wait(60); a front dying at once still has a beat."""

    def crash(state):
        raise RuntimeError("died in its first second")

    paths = _planted(tmp_path, monkeypatch, crash)
    with pytest.raises(RuntimeError):
        probe.run_front("e5", **paths)
    rid = phase36_ledger.run_id(36, "probes", "e5")
    (start,) = phase36_ledger.read_ledger(paths["ledger_path"])
    assert paths["heartbeat_path"].exists(), "no beat after the start line"
    beats = _beats(paths["heartbeat_path"])
    assert len(beats) == 1 and beats[0]["point"] == rid
    began = datetime.datetime.fromisoformat(start["utc"])
    assert datetime.datetime.fromisoformat(beats[0]["utc"]) >= began
    (lost,) = phase36_ledger.reconcile(
        ledger_path=paths["ledger_path"], heartbeat_path=paths["heartbeat_path"]
    )
    assert lost["flag"] == phase36_ledger.LOST_FLAG and lost["seconds"] >= 0


def test_run_all_refuses_an_unregistered_front_before_anything(tmp_path, monkeypatch, clean_tree):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "disk_precheck", lambda: pytest.fail("ran past a refusal"))
    with pytest.raises(SystemExit, match="no registered stage"):
        probe.run_all(fronts=("e4",))
    assert clean_tree == []


def test_run_all_checks_the_tree_then_the_disk_then_runs(tmp_path, monkeypatch, clean_tree):
    paths = _planted(tmp_path, monkeypatch)
    order = []
    monkeypatch.setattr(phase25_run, "disk_precheck", lambda: order.append("disk"))
    real = probe.run_front
    monkeypatch.setattr(
        probe, "run_front", lambda front, **kw: order.append(front) or real(front, **kw)
    )
    probe.run_all(fronts=("e5",), **paths)
    (call,) = clean_tree
    assert call["pathspec"] == ("scripts", "src", "results") and call["cwd"] == probe._GIT_ROOT
    assert order == ["disk", "e5"]


# =================================================================================================
# Task 1 — the write-once emit and WR-02
# =================================================================================================


def test_record_session_appends(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    first = probe.record_session("e1")
    second = probe.record_session("e1")
    assert len(first) == 1 and len(second) == 2 and second[0] == first[0]
    assert {s["git_sha"] for s in second} == {_head()}
    on_disk = json.loads(probe.sessions_sidecar("e1").read_text(encoding="utf-8"))
    assert on_disk == second


def test_wr02_pinned_unchanged_passes_for_head():
    probe.prove_pinned_unchanged([_head(), _head()])


def test_wr02_natural_red_on_the_pre_fix_commit():
    with pytest.raises(SystemExit, match="WR-02") as refused:
        probe.prove_pinned_unchanged([_head(), _pre_fix_sha()])
    assert "scripts/phase25_run.py" in str(refused.value)


def test_wr02_unknown_sha_refuses():
    with pytest.raises(SystemExit, match="unknown sha"):
        probe.prove_pinned_unchanged(["f" * 40])


def test_emit_refuses_overwrite_then_dirty_then_wr02(tmp_path, monkeypatch):
    paths = _planted(tmp_path, monkeypatch)
    probe.run_front("e5", **paths)
    calls = []

    def dirty(**kwargs):
        calls.append(kwargs)
        raise SystemExit("[probe] stopped at the dirty check")

    monkeypatch.setattr(probe, "refuse_if_dirty", dirty)
    # (1) overwrite FIRST: the dirty check is never reached.
    existing = tmp_path / "existing.json"
    existing.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        probe.emit("e5", out_path=existing)
    assert calls == [] and existing.read_text(encoding="utf-8") == "{}"
    # (2) dirty SECOND, with the record excluded from its own pathspec.
    rel = "results/phase36_never_written_e5.json"
    with pytest.raises(SystemExit, match="stopped at the dirty check"):
        probe.emit("e5", out_path=probe._GIT_ROOT / rel)
    (call,) = calls
    assert call["pathspec"] == ("scripts", "src", "results", f":(exclude){rel}")
    assert call["cwd"] == probe._GIT_ROOT
    assert not (probe._GIT_ROOT / rel).exists()
    # (3) WR-02 THIRD: a session on a commit whose pinned modules differ from HEAD.
    monkeypatch.setattr(probe, "refuse_if_dirty", lambda **kw: "")
    sessions = probe.sessions_sidecar("e5")
    sessions.write_text(json.dumps([{"git_sha": _pre_fix_sha()}]), encoding="utf-8")
    out = tmp_path / "out" / "record.json"
    with pytest.raises(SystemExit, match="WR-02"):
        probe.emit("e5", out_path=out)
    assert not out.exists()


def test_emit_writes_through_write_record_to_out_path(tmp_path, monkeypatch):
    paths = _planted(tmp_path, monkeypatch)
    run = probe.run_front("e5", **paths)
    monkeypatch.setattr(
        phase36_prereg, "probe_record", lambda front: pytest.fail("touched probe_record")
    )
    seen = []
    real = probe._write_record
    monkeypatch.setattr(probe, "_write_record", lambda *a: seen.append(a[0]) or real(*a))
    out = tmp_path / "emitted" / "phase36_probe_e5.json"
    record = probe.emit("e5", out_path=out)
    assert seen == [out]
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(record))
    assert on_disk["provenance"]["run"]["started_utc"] == run["started_utc"]
    assert set(on_disk["provenance"]["module_sha256"]) == set(probe.PINNED_MODULES)
    assert on_disk["gates_nothing"] is True and on_disk["sweep_point"] is False
    assert on_disk["stages"] == {"total_seconds": 0.5} and on_disk["repetitions"] == 1
    probe.prove_no_reading(on_disk)


def test_emit_refuses_a_reused_stage_and_a_missing_sidecar(tmp_path, monkeypatch):
    def reused(state):
        return dict(_fake_stage(state), reused={"e5": True})

    paths = _planted(tmp_path, monkeypatch, reused)
    out = tmp_path / "record.json"
    with pytest.raises(SystemExit, match="is missing"):
        probe.emit("e5", out_path=out)
    probe.run_front("e5", **paths)
    with pytest.raises(SystemExit, match="Pitfall 5"):
        probe.emit("e5", out_path=out)
    assert not out.exists()


def test_emit_target_and_write_record_direct(tmp_path, monkeypatch, clean_tree):
    rel = "results/phase36_never_written_x.json"
    assert probe._emit_target(rel) == probe._GIT_ROOT / rel
    assert clean_tree[-1]["pathspec"][-1] == f":(exclude){rel}"
    assert probe._emit_target(tmp_path / "x.json") == tmp_path / "x.json"
    assert clean_tree[-1]["pathspec"] == ("scripts", "src", "results")
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    run = {"front": "e5", "run_git_sha": _head(), "reused": {"e5": False}}
    with pytest.raises(SystemExit, match="WR-02 cannot name"):
        probe._write_record(tmp_path / "out.json", {}, run)
    assert not (tmp_path / "out.json").exists()


def test_build_record_refuses_a_front_mismatch_and_an_unbuilt_front():
    run = {"front": "e5", "run_id": "x", "stages": {"configuration": {}}, "reused": {}}
    with pytest.raises(SystemExit, match="not 'e6'"):
        probe.build_record("e6", run)
    with pytest.raises(SystemExit, match="no record builder"):
        probe.build_record("e5", run)


# =================================================================================================
# Task 1 — D-16's one-path commits and the resumable emit_all (W4, W9)
# =================================================================================================


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    root = _scratch_repo(tmp_path)
    monkeypatch.setattr(probe, "_GIT_ROOT", root)
    return root


def _git_out(root, *argv):
    return subprocess.run(
        ["git", "-C", str(root), *argv], capture_output=True, text=True, check=True
    ).stdout


def test_commit_path_whitelist(scratch):
    (scratch / "results" / "phase36_budget.json").write_text("{}", encoding="utf-8")
    for bad in ("results/phase36_budget.json", "results/../stray.json", "ledger/other.jsonl"):
        with pytest.raises(SystemExit, match="not a listed probe record"):
            probe.commit_path(bad, "x")
    with pytest.raises(SystemExit, match="does not exist"):
        probe.commit_path(phase36_prereg.probe_record("e1"), "x")


def test_commit_path_commits_exactly_one_path(scratch):
    rel = phase36_prereg.probe_record("e5")
    (scratch / rel).write_text("{}", encoding="utf-8")
    (scratch / "results" / "other.json").write_text("{}", encoding="utf-8")
    _git_out(scratch, "add", "results/other.json")
    assert probe._path_state(rel) == "untracked"
    probe.commit_path(rel, "data(36): probe record e5")
    assert _git_out(scratch, "show", "--name-only", "--format=", "HEAD").split() == [rel]
    assert probe._path_state(rel) == "committed"
    with pytest.raises(SystemExit, match="NO-OP"):
        probe.commit_path(rel, "x")
    (scratch / rel).write_text('{"x": 1}', encoding="utf-8")
    assert probe._path_state(rel) == "modified"
    assert probe._path_state(phase36_prereg.probe_record("e1")) == "absent"
    ledger = scratch / phase36_ledger.LEDGER_PATH
    ledger.parent.mkdir()
    ledger.write_text("", encoding="utf-8")
    _git_out(scratch, "checkout", "-q", "-b", "scratch-branch")
    with pytest.raises(SystemExit, match="not main"):
        probe.commit_path(phase36_ledger.LEDGER_PATH, "x")


def _emit_all_env(monkeypatch, states, *, fail_on_commit=None):
    """emit_all against a dict-backed _path_state, with recorders on emit and commit_path."""
    calls = []
    monkeypatch.setattr(phase36_ledger, "reconcile", lambda: calls.append(("reconcile",)))
    monkeypatch.setattr(probe, "_path_state", lambda rel: states[rel])

    def fake_emit(front, out_path=None):
        calls.append(("emit", front))
        states[phase36_prereg.probe_record(front)] = "untracked"

    def fake_commit(rel, message):
        calls.append(("commit", rel))
        if fail_on_commit is not None and sum(c[0] == "commit" for c in calls) == fail_on_commit:
            raise SystemExit("[probe] git commit failed")
        states[rel] = "committed"

    monkeypatch.setattr(probe, "emit", fake_emit)
    monkeypatch.setattr(probe, "commit_path", fake_commit)
    return calls


def _absent_states():
    states = dict.fromkeys(phase36_prereg.PROBE_RECORDS, "absent")
    states[phase36_ledger.LEDGER_PATH] = "modified"
    return states


def test_emit_all_commits_the_ledger_first(monkeypatch):
    states = _absent_states()
    calls = _emit_all_env(monkeypatch, states)
    probe.emit_all()
    ledger = phase36_ledger.LEDGER_PATH
    expected = [("reconcile",), ("commit", ledger)]
    for front in probe.RUN_ORDER:
        expected += [("emit", front), ("commit", phase36_prereg.probe_record(front))]
    assert calls == expected
    assert set(states.values()) == {"committed"}
    # The signatures the fakes stand in for.
    inspect.signature(probe.emit).bind("e1", out_path=None)
    inspect.signature(probe.commit_path).bind("x", "y")


def test_emit_all_resumes_after_abort(monkeypatch):
    states = _absent_states()
    calls = _emit_all_env(monkeypatch, states, fail_on_commit=3)
    with pytest.raises(SystemExit, match="commit failed"):
        probe.emit_all()
    e5, e6 = (phase36_prereg.probe_record(f) for f in ("e5", "e6"))
    assert states[phase36_ledger.LEDGER_PATH] == "committed" and states[e5] == "committed"
    assert states[e6] == "untracked"
    calls_rerun = _emit_all_env(monkeypatch, states)
    probe.emit_all()
    assert [c[1] for c in calls_rerun if c[0] == "emit"] == ["e3", "e2", "e1"]
    committed = [c[1] for c in calls_rerun if c[0] == "commit"]
    assert committed == [phase36_prereg.probe_record(f) for f in ("e6", "e3", "e2", "e1")]
    every = [c[1] for c in calls + calls_rerun if c[0] == "commit"]
    every.remove(e6)  # the aborted attempt
    assert sorted(every) == sorted([phase36_ledger.LEDGER_PATH, *phase36_prereg.PROBE_RECORDS])
    assert set(states.values()) == {"committed"}
    # Write-once: a committed record changed on disk refuses.
    states[phase36_prereg.probe_record("e3")] = "modified"
    states[phase36_ledger.LEDGER_PATH] = "committed"
    _emit_all_env(monkeypatch, states)
    with pytest.raises(SystemExit, match="write-once"):
        probe.emit_all()


def test_emit_all_refuses_an_absent_ledger(monkeypatch):
    states = _absent_states()
    states[phase36_ledger.LEDGER_PATH] = "absent"
    calls = _emit_all_env(monkeypatch, states)
    with pytest.raises(SystemExit, match="nothing to emit"):
        probe.emit_all()
    assert calls == [("reconcile",)]


def test_git_surface_is_bounded():
    allowed = set(probe.ALLOWED_GIT_ACTIONS) | set(probe.READ_ONLY_GIT_ACTIONS)
    offenders, message = _git_surface_failure(MODULE, allowed)
    assert offenders == [], message
    used = {row[0] for row in _git_argv_subcommands(MODULE)}
    assert {"add", "commit"} <= used  # non-vacuous


# =================================================================================================
# Task 1 — the CLI, torch-free import, and the census
# =================================================================================================


def test_main_dispatch_binds_real_signatures(tmp_path, monkeypatch):
    calls = []
    for name in ("run_all", "emit", "emit_all", "preflight"):
        signature = inspect.signature(getattr(probe, name))

        def recorder(*args, _name=name, _sig=signature, **kwargs):
            _sig.bind(*args, **kwargs)  # the arguments main() passes must fit the REAL function
            calls.append((_name, args, kwargs))

        monkeypatch.setattr(probe, name, recorder)
    hb, ledger = tmp_path / "hb.jsonl", tmp_path / "ledger.jsonl"
    argv = ["run", "--heartbeat", str(hb), "--ledger", str(ledger), "--front", "e1", "e5"]
    assert probe.main(argv) == 0
    assert probe.main(["run"]) == 0
    assert probe.main(["emit", "e1"]) == 0
    assert probe.main(["emit-all"]) == 0
    assert probe.main(["preflight"]) == 0
    assert calls == [
        ("run_all", (), {"heartbeat_path": hb, "ledger_path": ledger, "fronts": ("e1", "e5")}),
        (
            "run_all",
            (),
            {
                "heartbeat_path": phase36_ledger.HEARTBEAT_PATH,
                "ledger_path": None,
                "fronts": probe.RUN_ORDER,
            },
        ),
        ("emit", ("e1",), {}),
        ("emit_all", (), {}),
        ("preflight", (), {}),
    ]
    for bad in (["emit", "e4"], ["run", "--front", "e4"]):
        with pytest.raises(SystemExit) as caught:
            probe.main(bad)
        assert caught.value.code != 0
    assert probe.build_parser().parse_args(["emit", "e6"]).front == "e6"


def test_preflight_refuses_an_unregistered_front(monkeypatch, capsys):
    for front in probe.RUN_ORDER:
        monkeypatch.setitem(probe.STAGES, front, _fake_stage)
    probe.preflight()
    assert "RUN_ORDER e5 e6 e3 e2 e1" in capsys.readouterr().out
    monkeypatch.delitem(probe.STAGES, "e3")
    with pytest.raises(SystemExit, match=r"\['e3'\]"):
        probe.preflight()


def test_small_helpers(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    assert probe._rel(tmp_path / "data" / "x.json") == "data/x.json"
    assert probe._rel("/elsewhere/x.json") == "/elsewhere/x.json"
    assert datetime.datetime.fromisoformat(probe._now()).tzinfo is not None
    assert probe._spread([3.0, 1.0, 2.0]) == {"n": 3, "min": 1.0, "median": 2.0, "max": 3.0}
    (tmp_path / "f").write_bytes(b"abc")
    assert probe._sha256(tmp_path / "f") == hashlib.sha256(b"abc").hexdigest()
    with pytest.raises(SystemExit, match=r"\[phase36_probe\] no"):
        probe._prove(False, "no")
    assert probe._committed_json(probe.CURVE_RECORD)["adapter_in_sha256"]


def test_module_imports_without_torch():
    code = (
        "import sys; sys.path[:0] = ['scripts', 'src']; import phase36_probe; "
        "print('torch' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=_ROOT, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "False", completed.stdout


def test_every_probe_function_has_a_cpu_test():
    source = MODULE.read_text(encoding="utf-8")
    assert [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _untested_functions("probe", source, test_source) == []
