"""Plan 36-03: the Phase 36 probe driver core and its E1 front (COST-01, D-01, D-11..D-18).

CPU-only, never MPS. Nothing here writes under the real results/, data/, checkpoints/ or ledger/:
every sidecar, ledger, heartbeat and emitted record lands under a tmp directory, and the git
writers run against a scratch repository.
"""

import ast
import contextlib
import datetime
import hashlib
import inspect
import io
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


def test_run_front_reprobe_is_priced_once_and_refused_once_the_record_exists(tmp_path, monkeypatch):
    """CR-01: the WR-02 re-probe (sidecar deleted, front rerun) writes a second end line naming the
    same record; spent prices it without refusing. Once the record exists (emitted or committed),
    a re-probe is refused BEFORE its start line: the write-once record could not carry its
    seconds, so the last end line would name a record another attempt wrote."""
    paths = _planted(tmp_path, monkeypatch)
    states = {}
    monkeypatch.setattr(probe, "_path_state", lambda rel: states.get(rel, "absent"))
    probe.run_front("e5", **paths)
    probe.run_sidecar("e5").unlink()  # the documented re-probe
    probe.run_front("e5", **paths)
    record = phase36_prereg.probe_record("e5")
    lines = phase36_ledger.read_ledger(paths["ledger_path"])
    assert [x["record"] for x in lines if x["event"] == "end"] == [record, record]
    totals = phase36_ledger.spent([], ledger_path=paths["ledger_path"], fronts=("probes",))
    assert [r["flag"] for r in totals["rows"]] == [
        phase36_ledger.SUPERSEDED_FLAG,
        phase36_ledger.PENDING_FLAG,
    ]
    for state in ("untracked", "committed", "modified"):
        states[record] = state
        probe.run_sidecar("e5").unlink(missing_ok=True)
        with pytest.raises(SystemExit, match="CR-01"):
            probe.run_front("e5", **paths)
        assert phase36_ledger.read_ledger(paths["ledger_path"]) == lines


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


def test_a_crashed_attempts_session_never_poisons_a_clean_rerun(tmp_path, monkeypatch):
    """WR-02: a crashed attempt at a pre-fix sha leaves its session in the sidecar; stages never
    resume, so the clean rerun at HEAD owns every priced second and emits without refusing."""

    def crash(state):
        raise RuntimeError("stage died")

    paths = _planted(tmp_path, monkeypatch, crash)
    with pytest.raises(RuntimeError):
        probe.run_front("e5", **paths)
    crashed = [{"git_sha": _pre_fix_sha(), "started_utc": "2026-10-01T00:00:00+00:00"}]
    probe.sessions_sidecar("e5").write_text(json.dumps(crashed), encoding="utf-8")
    phase36_ledger.reconcile(
        ledger_path=paths["ledger_path"], heartbeat_path=paths["heartbeat_path"]
    )
    monkeypatch.setitem(probe.STAGES, "e5", _fake_stage)
    probe.run_front("e5", **paths)
    out = tmp_path / "out" / "record.json"
    probe.emit("e5", out_path=out)
    assert out.exists()
    sessions = json.loads(probe.sessions_sidecar("e5").read_text(encoding="utf-8"))
    assert [s["git_sha"] for s in sessions] == [_head()]


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
    # e4 is never a probe front (36-01), so it never has a builder; e5 got one in 36-04.
    run = {"front": "e4", "run_id": "x", "stages": {"configuration": {}}, "reused": {}}
    with pytest.raises(SystemExit, match="not 'e6'"):
        probe.build_record("e6", run)
    with pytest.raises(SystemExit, match="no record builder"):
        probe.build_record("e4", run)


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


# =================================================================================================
# Task 2 — stage_e1 and the E1 record (D-03, D-04, D-18), pure and light (no model)
# =================================================================================================


def _rows(questions, k, *, at_cap_every=5):
    return [
        {"seconds": 0.01 * (i + 1), "tokens": 4 + i % 3, "at_cap": i % at_cap_every == 0}
        for i in range(questions * k)
    ]


def test_e1_run_separates_fixed_and_prefix_cost():
    import math

    questions, k = 3, 18  # k above CURVE_K so the K = 16 prefix is a strict prefix
    rows = _rows(questions, k)
    run = probe._e1_run(100.0, rows, questions, k)
    seconds = [r["seconds"] for r in rows]
    assert run["fixed_seconds"] == run["total_seconds"] - run["draw_seconds_sum"]
    assert run["draw_seconds_sum"] == math.fsum(seconds)
    first = [
        s for q in range(questions) for s in seconds[q * k : q * k + probe.phase35_prereg.CURVE_K]
    ]
    assert run["k16_seconds"] == pytest.approx(run["fixed_seconds"] + math.fsum(first), rel=1e-12)
    assert len(run["per_question_k48_seconds"]) == questions
    assert len(run["per_question_k16_seconds"]) == questions
    assert run["draws"] == len(run["draw_seconds"]) == len(run["draw_tokens"]) == questions * k
    assert all(type(s) is float for s in run["draw_seconds"])
    assert all(type(t) is int for t in run["draw_tokens"])
    assert run["at_cap_draws"] == sum(r["at_cap"] for r in rows)
    assert run["at_cap_seconds_spread"]["n"] == run["at_cap_draws"]
    none_at_cap = probe._e1_run(100.0, _rows(1, 2, at_cap_every=99)[1:] * 2, 1, 2)
    assert none_at_cap["at_cap_draws"] == 0 and none_at_cap["at_cap_seconds_spread"] is None
    with pytest.raises(SystemExit, match="draw timer counted"):
        probe._e1_run(100.0, rows[:-1], questions, k)
    with pytest.raises(SystemExit, match="longer than the run"):
        probe._e1_run(0.001, rows, questions, k)


def _planted_e1_run():
    runs = [probe._e1_run(total, _rows(2, 3), 2, 3) for total in (50.0, 61.0)]
    stages = {"configuration": {"arm": "erased", "K": 3, "questions": 2}, "runs": runs}
    return {"front": "e1", "run_id": "v6/36/probes/e1", "stages": stages, "reused": {"e1": False}}


def _keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys(value)


def test_build_record_e1_keeps_the_two_fixed_costs_separate():
    run = _planted_e1_run()
    record = probe.build_record("e1", run, beside=probe.phase31_beside())
    runs = record["stages"]["runs"]
    assert [r["fixed_seconds"] for r in runs] == [r["fixed_seconds"] for r in run["stages"]["runs"]]
    assert runs[0]["fixed_seconds"] != runs[1]["fixed_seconds"]
    assert not [key for key in _keys(record) if "mean" in key or "average" in key]
    assert record["stages"]["r1b_k48_totals"] == [50.0, 61.0]
    assert record["repetitions"] == 2
    beside = record[probe.BESIDE_KEY]
    point = json.loads((_ROOT / probe.PHASE31_POINT_RECORD).read_text(encoding="utf-8"))
    assert beside["path"] == probe.PHASE31_POINT_RECORD
    assert beside["total_seconds"] == point["total_seconds"]
    assert beside["stage_seconds"] == {s: v["seconds"] for s, v in point["stages"].items()}
    assert (
        beside["sha256"]
        == hashlib.sha256((_ROOT / probe.PHASE31_POINT_RECORD).read_bytes()).hexdigest()
    )
    probe.prove_no_reading(record)
    leaky = _planted_e1_run()
    leaky["stages"]["configuration"]["per_fact"] = {"pet_name": 1}
    with pytest.raises(SystemExit, match="names a reading"):
        probe.build_record("e1", leaky)
    one = _planted_e1_run()
    one["stages"]["runs"].pop()
    with pytest.raises(SystemExit, match="not 2"):
        probe.build_record("e1", one)
    assert probe.RECORD_BUILDERS["e1"] is probe._e1_stages and probe.STAGES["e1"] is probe.stage_e1
    stages, repetitions = probe._e1_stages(run["stages"])
    assert stages == record["stages"] and repetitions == 2


def test_e1_shape_reads_the_pins_own_k():
    questions, k = probe.e1_shape()
    assert k == phase36_prereg.phase35_prereg.FULL_FIDELITY_K
    erased = json.loads((_ROOT / probe.ERASED_RECORD).read_text(encoding="utf-8"))["config"]
    assert (
        questions
        == erased["corpus_entries"]
        == len(phase36_prereg.phase35_prereg.a2_corpus_entries())
    )


def test_e1_components_reads_committed_json_and_hashes_nothing(monkeypatch):
    hashed = []
    real = probe._sha256
    monkeypatch.setattr(probe, "_sha256", lambda path: hashed.append(path) or real(path))
    components = probe.e1_components()
    assert hashed == []
    erased = json.loads((_ROOT / probe.ERASED_RECORD).read_text(encoding="utf-8"))["config"]
    assert [list(c) for c in components] == erased["ablated_components"]
    assert all(isinstance(c, tuple) for c in components)


def test_published_adapter_identity(tmp_path, monkeypatch):
    import phase14_recall

    curve = json.loads((_ROOT / probe.CURVE_RECORD).read_text(encoding="utf-8"))
    assert probe.published_adapter_sha256() == curve["adapter_in_sha256"]
    adapter = tmp_path / "fixture_adapter.pt"
    adapter.write_bytes(b"fixture adapter")
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", adapter)
    with pytest.raises(SystemExit, match="adapter_in_sha256"):
        probe.prove_published_adapter()
    sha = hashlib.sha256(b"fixture adapter").hexdigest()
    monkeypatch.setattr(probe, "published_adapter_sha256", lambda: sha)
    probe.prove_published_adapter()
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", tmp_path / "absent.pt")
    with pytest.raises(SystemExit, match="is missing"):
        probe.prove_published_adapter()


def _e1_light(tmp_path, monkeypatch, *, calls=6, on_call=None):
    """stage_e1 with a stand-in pin calling a fake _complete; no model, no gitignored input."""
    import phase14_recall
    import phase19_erasure

    real_components = probe.e1_components()  # before any patch, from the committed JSON alone
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    adapter = tmp_path / "checkpoints" / "fixture_adapter.pt"
    adapter.parent.mkdir(parents=True)
    adapter.write_bytes(b"fixture adapter")
    sha = hashlib.sha256(b"fixture adapter").hexdigest()
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", adapter)
    monkeypatch.setattr(probe, "published_adapter_sha256", lambda: sha)
    monkeypatch.setattr(probe, "e1_shape", lambda: (2, 3))
    monkeypatch.setattr(probe, "e1_components", lambda: real_components)
    monkeypatch.setattr(phase14_recall, "_complete", lambda *a, **kw: ([7, 7], True))
    seen = []

    def stand_in(arm, device, **kwargs):
        seen.append((arm, device, kwargs))
        for _ in range(calls):
            phase14_recall._complete(None, [0], device, None)
        pathlib.Path(kwargs["record_path"]).write_text("completions", encoding="utf-8")
        print("taught ON: 3/4 = 0.75 per_fact hits")
        if on_call is not None:
            on_call(len(seen), adapter)
        return {"per_fact": [1]}

    monkeypatch.setattr(phase19_erasure, "run_erasure_arm", stand_in)
    return seen, real_components


def test_stage_e1_light_times_two_runs_and_discards_the_draws(tmp_path, monkeypatch, capsys):
    seen, components = _e1_light(tmp_path, monkeypatch)
    state = {"point": "x", "stage": "start", "shape": None, "draw_index": None}
    out = probe.stage_e1(state)
    assert capsys.readouterr().out == ""
    assert [s[0] for s in seen] == ["erased", "erased"]
    assert [s[2]["record_path"] for s in seen] == [probe.arm_record_path("e1", r) for r in (1, 2)]
    assert all(s[2]["components"] == components for s in seen)
    assert not any(probe.arm_record_path("e1", r).exists() for r in (1, 2))
    assert out["reused"] == {"e1": False} and len(out["runs"]) == 2
    for run in out["runs"]:
        assert run["draws"] == 6 and len(run["draw_seconds"]) == 6
        assert run["draw_tokens"] == [2] * 6 and run["at_cap_draws"] == 0
    config = out["configuration"]
    assert config["k"] == len(components) and config["K"] == 3 and config["questions"] == 2
    assert config["k16"] == phase36_prereg.phase35_prereg.CURVE_K
    assert config["seed"] == 1337 and state["stage"] == "e1_rep2"
    probe.prove_no_reading({"configuration": config, "stages": {"runs": out["runs"]}})


def test_stage_e1_refuses_a_short_draw_count(tmp_path, monkeypatch):
    _e1_light(tmp_path, monkeypatch, calls=5)
    with pytest.raises(SystemExit, match="draw timer counted 5"):
        probe.stage_e1({})
    assert not probe.arm_record_path("e1", 1).exists()


def test_stage_e1_refuses_the_wrong_adapter_before_and_after(tmp_path, monkeypatch):
    seen, _ = _e1_light(tmp_path, monkeypatch)
    monkeypatch.setattr(probe, "published_adapter_sha256", lambda: "0" * 64)
    with pytest.raises(SystemExit, match="adapter_in_sha256"):
        probe.stage_e1({})
    assert seen == []

    def tamper(n, adapter):
        if n == 2:
            adapter.write_bytes(b"changed during the run")

    seen, _ = _e1_light(tmp_path / "after", monkeypatch, on_call=tamper)
    with pytest.raises(SystemExit, match="adapter_in_sha256"):
        probe.stage_e1({})
    assert len(seen) == 2


def test_stage_e1_refuses_other_components_and_a_stale_arm_record(tmp_path, monkeypatch):
    seen, components = _e1_light(tmp_path, monkeypatch)
    monkeypatch.setattr(probe, "e1_components", lambda: components[:-1])
    with pytest.raises(SystemExit, match="ablated_components"):
        probe.stage_e1({})
    monkeypatch.setattr(probe, "e1_components", lambda: components)
    stale = probe.arm_record_path("e1", 1)
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="stale probe output"):
        probe.stage_e1({})
    assert seen == []


def _stage_e1_pin_calls():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    (stage,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stage_e1"]
    parents = {child: node for node in ast.walk(stage) for child in ast.iter_child_nodes(node)}
    calls = [
        n
        for n in ast.walk(stage)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "run_erasure_arm"
    ]
    return calls, parents


def test_e1_pin_payload_is_never_bound():
    calls, parents = _stage_e1_pin_calls()
    assert len(calls) == 1
    (call,) = calls
    assert isinstance(parents[call], ast.Expr)
    assert call.args[0].value == "erased"


def test_e1_pin_call_runs_inside_silenced():
    (call,), parents = _stage_e1_pin_calls()
    node, items = call, []
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.With):
            items += [ast.unparse(item.context_expr) for item in node.items]
    assert "silenced()" in items and "DrawTimer()" in items


# =================================================================================================
# Task 3 — the E1 live path on CPU: main -> run_all -> run_front -> stage_e1 -> emit (W10)
# =================================================================================================

_PROBE36_GLOBS = (
    "data/*probe36*",
    "checkpoints/*probe36*",
    "results/*probe36*",
    "results/phase36_probe_*",
)
# The SHAPE is scaled, not the instrument: 216 x 48 CPU draws would dominate the suite.
LIVE_QUESTIONS, LIVE_K = 3, 4
LIVE_DRAWS = LIVE_QUESTIONS * LIVE_K


def _real_probe36_strays():
    """Every probe36 write target in the REAL tree (the test module's _ROOT, never patched)."""
    return sorted(
        {p.relative_to(_ROOT).as_posix() for pattern in _PROBE36_GLOBS for p in _ROOT.glob(pattern)}
    )


def _e1_live_fixture(root):
    """ONE CPU run of the E1 probe through main(), then the REAL emit. Every patch is undone."""
    import phase14_recall
    import phase16_persistence
    import phase17_persona_gate
    import phase19_erasure

    from personacore.checkpoint import export_slim
    from personacore.config import ModelConfig
    from personacore.tokenizer import from_json
    from test_phase22_wiring import _e2e_env

    strays_before = _real_probe36_strays()
    # B1: from the committed JSON alone, before any patch — never from the gitignored .pt.
    real_components = probe.e1_components()
    pin_signature = inspect.signature(phase19_erasure.run_erasure_arm)
    entries = phase36_prereg.phase35_prereg.a2_corpus_entries()[:LIVE_QUESTIONS]
    spies = {"pin_calls": [], "hashed": []}
    heartbeat = root / "heartbeat.jsonl"
    ledger = root / "ledger" / "v6_mps_ledger.jsonl"
    out = root / "emitted" / "phase36_probe_e1.json"
    buf = io.StringIO()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(phase25_run, "_DEVICE", "cpu")
        _e2e_env(root, mp)
        slim = root / "convbase_slim.pt"
        export_slim(root / "convbase.pt", slim)
        mp.setattr(phase14_recall, "CONVBASE_SLIM", slim)
        mp.setattr(phase17_persona_gate, "CONVBASE_SLIM", slim)
        mp.setattr(phase14_recall, "RECALL_MAX_NEW_TOKENS", 4)
        mp.setattr(probe, "_ROOT", root)
        # W1: this module-scoped fixture runs before the autouse clean_tree patch applies.
        mp.setattr(probe, "refuse_if_dirty", lambda **kw: "")
        mp.setattr(phase25_run, "disk_precheck", lambda target=None: None)
        # Redirects of gitignored inputs (absent on CI; never a skipif — the ubuntu skip pin):
        # checkpoints/persona_adapter.pt -> a fixture adapter, and the published sha -> its sha.
        # checkpoints/convbase_slim.pt -> the fixture slim base above. Nothing reads data/.
        adapter = root / "checkpoints" / "fixture_adapter.pt"
        adapter.write_bytes(b"fixture adapter bytes")
        sha = hashlib.sha256(adapter.read_bytes()).hexdigest()
        mp.setattr(phase14_recall, "ADAPTER_PATH", adapter)
        mp.setattr(probe, "published_adapter_sha256", lambda: sha)
        mp.setattr(probe, "e1_shape", lambda: (LIVE_QUESTIONS, LIVE_K))
        mp.setattr(probe, "e1_components", lambda: real_components)
        real_sha256 = probe._sha256
        mp.setattr(
            probe,
            "_sha256",
            lambda path: spies["hashed"].append(pathlib.Path(path)) or real_sha256(path),
        )

        def stand_in(*args, **kwargs):
            """The pin's signature and call shape; the REAL draw_all, so DrawTimer times real
            _complete calls; a reading written, printed and returned — all of which must vanish."""
            bound = pin_signature.bind(*args, **kwargs)
            arguments = bound.arguments
            assert arguments["arm"] == "erased"
            assert arguments["components"] == real_components
            record_path = pathlib.Path(arguments["record_path"])
            assert record_path.parent == root / "data"
            assert record_path.name.startswith("probe36_e1_rep")
            spies["pin_calls"].append(dict(arguments))
            model, _cfg, _ckpt = phase17_persona_gate.build_unadapted_base("cpu")
            tok = from_json(phase14_recall.TOKENIZER_PATH)
            forbid = phase16_persistence.resolve_forbid(tok, ModelConfig.vocab_size)[0]
            for entry in entries:
                phase14_recall.draw_all(
                    model,
                    tok,
                    entry["prompt_ids"],
                    arguments["device"],
                    forbid,
                    entry["seed_index"] * LIVE_K,
                    n_samples=LIVE_K - 1,
                )
            record_path.write_text(json.dumps({"completions": ["Biscuit"]}), encoding="utf-8")
            print("taught ON: 3/4 = 0.75 per_fact hits")
            return {"per_fact": [{"hits": 3}]}

        mp.setattr(phase19_erasure, "run_erasure_arm", stand_in)
        argv = ["run", "--heartbeat", str(heartbeat), "--ledger", str(ledger), "--front", "e1"]
        with contextlib.redirect_stdout(buf):
            assert probe.main(argv) == 0
        sidecar = json.loads(probe.run_sidecar("e1").read_text(encoding="utf-8"))
        arm_paths = [probe.arm_record_path("e1", rep) for rep in (1, 2)]
        probe.emit("e1", out_path=out)  # the REAL _emit_target -> _write_record (W10)
    return {
        "root": root,
        "sidecar": sidecar,
        "record": json.loads(out.read_text(encoding="utf-8")),
        "spies": spies,
        "strays": (strays_before, _real_probe36_strays()),
        "stdout": buf.getvalue(),
        "ledger": ledger,
        "heartbeat": heartbeat,
        "arm_paths": arm_paths,
    }


@pytest.fixture(scope="module")
def e1_live(tmp_path_factory):
    """ONE CPU live-path E1 run per module (the tests/test_phase31_probe.py:386-389 shape)."""
    return _e1_live_fixture(tmp_path_factory.mktemp("e1_live"))


def test_live_e1_calls_the_pin_twice_and_deletes_its_draws(e1_live):
    calls = e1_live["spies"]["pin_calls"]
    assert len(calls) == 2
    paths = [pathlib.Path(c["record_path"]) for c in calls]
    assert paths == e1_live["arm_paths"] and paths[0] != paths[1]
    assert not any(p.exists() for p in paths)
    assert all(c["device"] == "cpu" for c in calls)


def test_live_e1_sidecar_counts_every_draw_and_keeps_fixed_costs_apart(e1_live):
    runs = e1_live["sidecar"]["stages"]["runs"]
    assert len(runs) == 2
    for run in runs:
        assert run["draws"] == LIVE_DRAWS and len(run["draw_seconds"]) == LIVE_DRAWS
        assert all(type(t) is int and 0 <= t <= 4 for t in run["draw_tokens"])
        assert run["fixed_seconds"] == run["total_seconds"] - run["draw_seconds_sum"]
        assert run["fixed_seconds"] > 0
    assert e1_live["sidecar"]["reused"] == {"e1": False}
    assert e1_live["sidecar"]["device"] == "cpu"


def test_live_e1_stdout_holds_no_reading(e1_live):
    text = e1_live["stdout"]
    assert re.search(r"^\[phase36_probe\] e1 \d+\.\d s$", text, re.MULTILINE), text  # not blind
    assert "per_fact" not in text and "hits" not in text
    assert not re.search(r"\d+/\d+ = ", text), text


def test_live_e1_record_passes_the_gate_with_provenance(e1_live):
    record = e1_live["record"]
    probe.prove_no_reading(record)
    assert record["provenance"]["run"]["device"] == "cpu"
    assert set(record["provenance"]["module_sha256"]) == set(probe.PINNED_MODULES)
    for run in record["stages"]["runs"]:
        assert len(run["draw_seconds"]) == LIVE_DRAWS
        assert all(type(s) is float for s in run["draw_seconds"])
    assert record["stages"]["r1b_k48_totals"] == [
        r["total_seconds"] for r in e1_live["sidecar"]["stages"]["runs"]
    ]
    assert record[probe.BESIDE_KEY]["path"] == probe.PHASE31_POINT_RECORD
    assert record["repetitions"] == 2 and record["gates_nothing"] is True


def test_live_e1_ledger_and_heartbeat(e1_live):
    rid = phase36_ledger.run_id(36, "probes", "e1")
    lines = phase36_ledger.read_ledger(e1_live["ledger"])
    assert [(x["event"], x["run_id"]) for x in lines] == [("start", rid), ("end", rid)]
    assert lines[1]["record"] == "results/phase36_probe_e1.json"
    last = e1_live["heartbeat"].read_text(encoding="utf-8").splitlines()[-1]
    assert json.loads(last)["point"] == rid


def test_live_e1_writes_nothing_in_the_real_tree(e1_live):
    before, after = e1_live["strays"]
    assert before == after
    assert not any((e1_live["root"] / "results").iterdir())


def test_live_e1_never_hashed_the_gitignored_adapter(e1_live):
    hashed = e1_live["spies"]["hashed"]
    assert e1_live["root"] / "checkpoints" / "fixture_adapter.pt" in hashed  # non-vacuous
    assert not [p for p in hashed if p.is_relative_to(probe._GIT_ROOT / "checkpoints")]


# =================================================================================================
# Plan 36-04 Task 1 — adapted_model, stage_e6 and the E6 record (D-07, B2), light (no model)
# =================================================================================================


def test_adapted_model_checks_the_adapter_first_and_ablates_only_when_k_positive(monkeypatch):
    import phase14_recall
    import phase19_erasure

    import personacore.lora

    calls = []
    monkeypatch.setattr(probe, "prove_published_adapter", lambda: calls.append(("identity",)))
    artifact = {"adapter": {}, "lora_config": {}}
    monkeypatch.setattr(
        phase14_recall,
        "load_adapted_model",
        lambda device: (
            calls.append(("load", device)) or ("model", "cfg", "tok", "forbid", artifact)
        ),
    )
    monkeypatch.setattr(
        phase19_erasure,
        "ablate_components",
        lambda art, components: calls.append(("ablate", art, components)) or "ablated",
    )
    monkeypatch.setattr(
        personacore.lora,
        "load_adapter_weights",
        lambda model, art: calls.append(("apply", model, art)),
    )
    assert probe.adapted_model("cpu", 0) == ("model", "tok", "forbid")
    assert calls == [("identity",), ("load", "cpu")]
    calls.clear()
    components = probe.e1_components()
    assert probe.adapted_model("cpu", 3) == ("model", "tok", "forbid")
    assert calls == [
        ("identity",),
        ("load", "cpu"),
        ("ablate", artifact, components[:3]),
        ("apply", "model", "ablated"),
    ]


def _e6_light(monkeypatch):
    """stage_e6 on the REAL tokenizer and the REAL draw_all over a fake _complete; no model."""
    import phase14_recall

    from personacore.tokenizer import from_json

    tok = from_json(phase14_recall.TOKENIZER_PATH)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    monkeypatch.setattr(probe, "adapted_model", lambda device, k: (None, tok, None))
    monkeypatch.setattr(
        phase14_recall, "_complete", lambda *a, **kw: ([5, 5, 5], not kw.get("greedy"))
    )
    log = []
    real_assert, real_draw = phase14_recall.assert_no_value_in_prompt, phase14_recall.draw_all

    def asserted(tok, question, values, *, prompt_ids=None):
        log.append(("assert", list(prompt_ids), tuple(values)))
        return real_assert(tok, question, values, prompt_ids=prompt_ids)

    def drawn(model, tok, prompt_ids, device, forbid, index, **kw):
        log.append(("draw", list(prompt_ids), index, kw["n_samples"]))
        return real_draw(model, tok, prompt_ids, device, forbid, index, **kw)

    monkeypatch.setattr(phase14_recall, "assert_no_value_in_prompt", asserted)
    monkeypatch.setattr(phase14_recall, "draw_all", drawn)
    return log


def test_stage_e6_light_asserts_each_anchor_before_its_draw(monkeypatch, capsys):
    import phase14_factset

    log = _e6_light(monkeypatch)
    state = {"point": "x", "stage": "start", "shape": None, "draw_index": None}
    out = probe.stage_e6(state)
    assert capsys.readouterr().out == ""
    slots = [f.slot for f in phase14_factset.LOCKED_FACTS]
    K = phase36_prereg.phase35_prereg.FULL_FIDELITY_K
    values = tuple(f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS)
    # B2: one assertion per anchor slot, each immediately before that slot's draw, same ids.
    assert [entry[0] for entry in log] == ["assert", "draw"] * len(slots)
    for i in range(len(slots)):
        checked, drew = log[2 * i], log[2 * i + 1]
        assert checked[1] == drew[1] and checked[2] == values
        assert drew[2] == i * K and drew[3] == K - 1
    assert len({tuple(entry[1]) for entry in log}) == len(slots)
    assert out["draws"] == len(slots) * K
    assert out["at_cap_draws"] == len(slots)  # the fake leaves only the greedy draw at the cap
    assert len(out["per_slot_draw_seconds_mean"]) == len(slots)
    assert out["draw_seconds_spread"]["n"] == out["draws"]
    assert out["total_seconds"] >= out["setup_seconds"] >= 0
    config = out["configuration"]
    assert (config["k"], config["K"]) == (len(probe.e1_components()), K)
    assert config["anchor_slots"] == len(slots) and config["seed"] == 1337
    assert out["reused"] == {"e6": False} and state["stage"] == "e6_anchor"


def test_stage_e6_refuses_a_short_draw_count(monkeypatch):
    import phase14_recall

    _e6_light(monkeypatch)
    real = phase14_recall.draw_all
    monkeypatch.setattr(
        phase14_recall, "draw_all", lambda *a, **kw: real(*a, **dict(kw, n_samples=1))
    )
    with pytest.raises(SystemExit, match="draw timer counted"):
        probe.stage_e6({})


def _stage_calls(name, attr):
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    (stage,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    parents = {child: node for node in ast.walk(stage) for child in ast.iter_child_nodes(node)}
    calls = [
        n
        for n in ast.walk(stage)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == attr
    ]
    return calls, parents


def _with_items(node, parents):
    items = []
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.With):
            items += [ast.unparse(item.context_expr) for item in node.items]
    return items


def test_e6_draw_is_unbound_silenced_and_asserted_first():
    (draw,), parents = _stage_calls("stage_e6", "draw_all")
    assert isinstance(parents[draw], ast.Expr)
    assert "silenced()" in _with_items(draw, parents)
    assert "DrawTimer()" in _with_items(draw, parents)
    (check,), check_parents = _stage_calls("stage_e6", "assert_no_value_in_prompt")
    loop = parents[parents[draw]]
    assert isinstance(loop, ast.For)
    assert check_parents[check_parents[check]].lineno == loop.lineno  # the same loop body
    assert check.lineno < draw.lineno
    assert ast.unparse(check.args[2]) == "values"


def _planted_e6_stage(state):
    return {
        "configuration": {"arm": "erased", "K": 4, "anchor_slots": 2},
        "setup_seconds": 1.5,
        "per_slot_draw_seconds_mean": [0.25, 0.5],
        "draws": 8,
        "at_cap_draws": 3,
        "draw_seconds_spread": {"n": 8, "min": 0.1, "median": 0.3, "max": 0.7},
        "total_seconds": 6.0,
        "reused": {"e6": False},
    }


def _planted_e1_sidecar():
    runs = [
        {"per_question_k48_seconds": [2.0, 4.0]},
        {"per_question_k48_seconds": [5.0, 3.0, 4.0]},
    ]
    sidecar = probe.run_sidecar("e1")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps({"front": "e1", "stages": {"runs": runs}}), encoding="utf-8")
    return sidecar


def test_e6_record_and_the_a2_context_beside(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    monkeypatch.setitem(probe.STAGES, "e6", _planted_e6_stage)
    paths = {"heartbeat_path": tmp_path / "hb.jsonl", "ledger_path": tmp_path / "ledger.jsonl"}
    probe.run_front("e6", **paths)
    out = tmp_path / "emitted" / "phase36_probe_e6.json"
    # D-07: the A2-context unit comes from the E1 probe, so E6 cannot emit before it.
    with pytest.raises(SystemExit, match="comes from the E1 probe"):
        probe.emit("e6", out_path=out)
    assert not out.exists()
    sidecar = _planted_e1_sidecar()
    beside = probe.e6_a2_context_beside()
    assert beside == {
        "a2_context_from_e1": {
            "a2_context_question_k48_seconds_high": 4.0,  # max(mean(2, 4), mean(5, 3, 4))
            "path": "data/probe36_e1_run.json",
        }
    }
    record = probe.emit("e6", out_path=out)
    assert record["a2_context_from_e1"] == beside["a2_context_from_e1"]
    stages = record["stages"]
    assert set(stages) == {
        "setup_seconds",
        "per_slot_draw_seconds_mean",
        "draws",
        "at_cap_draws",
        "draw_seconds_spread",
        "total_seconds",
    }
    assert record["repetitions"] == 2 and record["configuration"]["anchor_slots"] == 2
    probe.prove_no_reading(json.loads(out.read_text(encoding="utf-8")))
    planted = probe.STAGES["e6"]({})
    planted.pop("reused")  # run_front moves it to the sidecar's top level
    assert probe._e6_stages(planted) == (stages, 2)
    sidecar.write_text(json.dumps({"stages": {"runs": [{}]}}), encoding="utf-8")
    with pytest.raises(SystemExit, match="not 2"):
        probe.e6_a2_context_beside()


# =================================================================================================
# Plan 36-04 Task 2 — stage_e5: the Phase 17 clearance sample + the E5 scoring sample (D-08)
# =================================================================================================

_E5_SENTINEL_TEXT = "SENTINEL completion text"
_E5_SENTINEL_NLL = 987.654321


def _e5_light(monkeypatch):
    """stage_e5 with every model-touching call faked and recorded; the real fixture material,
    tokenizer, forbid mask, held-out questions and reference sets."""
    import phase14_factset
    import phase14_factset_gate
    import phase17_persona_gate
    import phase19_erasure

    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    calls = {"probe": [], "match": [], "adapter": [], "nll": []}
    monkeypatch.setattr(
        phase17_persona_gate, "build_unadapted_base", lambda device: ("base", None, None)
    )

    def guess(model, tok, device, forbid, value, questions, *, start_index=0):
        calls["probe"].append((value, len(questions), start_index))
        probes = [
            {"question": q, "prompt_ids": [1], "completions": [_E5_SENTINEL_TEXT] * 4}
            for q in questions
        ]
        return {"value": value, "probes": probes, "clean": "SENTINEL verdict"}

    monkeypatch.setattr(phase14_factset_gate, "probe_guessability", guess)
    monkeypatch.setattr(
        phase14_factset,
        "exact_match_clean",
        lambda texts, value: calls["match"].append((len(texts), value)) or "SENTINEL verdict",
    )
    monkeypatch.setattr(
        probe, "adapted_model", lambda device, k: calls["adapter"].append(k) or ("m", "tok", None)
    )
    monkeypatch.setattr(
        phase19_erasure,
        "value_span_nll_mean",
        lambda model, tok, device, *, slot, value: (
            calls["nll"].append((model, slot, value)) or _E5_SENTINEL_NLL
        ),
    )
    return calls


def test_stage_e5_light_times_both_samples_and_keeps_no_reading(tmp_path, monkeypatch, capsys):
    import phase17_persona_facts
    import phase17_personas
    import phase18_extraction

    calls = _e5_light(monkeypatch)
    out = probe.stage_e5({"point": "x", "stage": "start", "shape": None, "draw_index": None})
    assert capsys.readouterr().out == ""
    slots = phase17_personas.CORE_SLOTS
    per_slot = phase17_personas.QUESTIONS_PER_SLOT
    # Clearance: one cached probe pass per slot over its 13 fresh questions, anchored on
    # PERSONAS[0]'s value, with disjoint seeding windows (phase17_persona_gate.py:285-299).
    anchors = {
        f.slot: f.value for f in phase17_persona_facts.PERSONA_FACTS[phase17_personas.PERSONAS[0]]
    }
    assert calls["probe"] == [(anchors[s], per_slot, i * per_slot) for i, s in enumerate(slots)]
    published = [f for facts in phase17_persona_facts.PERSONA_FACTS.values() for f in facts]
    assert sorted(value for _n, value in calls["match"]) == sorted(f.value for f in published)
    assert {n for n, _value in calls["match"]} == {per_slot * 4}
    clearance = out["clearance"]
    assert len(clearance["per_slot_seconds"]) == len(slots)
    assert clearance["candidates_matched"] == len(published)
    assert clearance["match_seconds_spread"]["n"] == len(published)
    assert clearance["total_seconds"] >= clearance["setup_seconds"] >= 0
    # Scoring: k = 0 then k = 78, every reference-set candidate of every locked slot.
    k78 = len(probe.e1_components())
    assert calls["adapter"] == [0, k78]
    sizes = [len(phase18_extraction.reference_set_for(s)) for s in slots]
    assert len(calls["nll"]) == 2 * sum(sizes)
    rows = out["scoring"]["adapters"]
    assert [r["k"] for r in rows] == [0, k78]
    for row in rows:
        assert row["candidates_per_slot"] == sizes and row["candidates"] == sum(sizes)
        assert len(row["per_slot_mean_candidate_seconds"]) == len(slots)
    assert out["scoring"]["candidate_seconds_spread"]["n"] == 2 * sum(sizes)
    config = out["configuration"]
    assert config["slots"] == len(slots) and config["published_values"] == len(published)
    assert config["questions_per_slot"] == per_slot
    assert config["scoring_frame"] == phase18_extraction.ADMISSIBLE_NLL_FRAME
    assert "per slot" in config["clearance_unit"] and "per candidate" in config["clearance_unit"]
    # No verdict, completion or NLL reaches the sidecar or the record.
    run = {"front": "e5", "run_id": "v6/36/probes/e5", "reused": out.pop("reused")}
    run["stages"] = out
    blob = json.dumps(run)
    assert "SENTINEL" not in blob and str(_E5_SENTINEL_NLL) not in blob
    record = probe.build_record("e5", run)
    assert record["repetitions"] == len(slots)
    assert set(record["stages"]) == {"clearance", "scoring"}
    assert probe._e5_stages(out) == (record["stages"], len(slots))


def test_stage_e5_refuses_a_short_clearance(monkeypatch):
    import phase17_isolation

    calls = _e5_light(monkeypatch)
    held = phase17_isolation.held_out_by_slot()
    monkeypatch.setattr(
        phase17_isolation, "held_out_by_slot", lambda: {s: v[:-1] for s, v in held.items()}
    )
    with pytest.raises(SystemExit, match="questions probed"):
        probe.stage_e5({})
    assert calls["adapter"] == []  # refused before any scoring adapter loads


def test_e5_readings_are_never_bound_into_the_record():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    (stage,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stage_e5"]
    parents = {child: node for node in ast.walk(stage) for child in ast.iter_child_nodes(node)}
    found = {}
    for node in ast.walk(stage):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            found.setdefault(node.func.attr, []).append(node)
    for name in ("exact_match_clean", "value_span_nll_mean"):
        assert len(found[name]) == 1 and isinstance(parents[found[name][0]], ast.Expr), name
        assert "silenced()" in _with_items(found[name][0], parents), name
    (guess,) = found["probe_guessability"]
    assign = parents[guess]
    assert isinstance(assign, ast.Assign) and [ast.unparse(t) for t in assign.targets] == ["probed"]
    assert "silenced()" in _with_items(guess, parents)
    # `probed` is read only for its completions and then deleted.
    uses = [
        parents[n]
        for n in ast.walk(stage)
        if isinstance(n, ast.Name) and n.id == "probed" and isinstance(n.ctx, ast.Load)
    ]
    assert [ast.unparse(u) for u in uses] == ["probed['probes']"]
    deleted = [
        n for n in ast.walk(stage) if isinstance(n, ast.Delete) and "probed" in ast.unparse(n)
    ]
    assert deleted


# =================================================================================================
# Plan 36-04 Task 3 — E5 and E6 live on CPU: main -> run_all -> run_front -> stage -> real emit
# =================================================================================================


def _e5_e6_live_fixture(root):
    """ONE CPU run of E5 then E6 through main(), then the REAL emit of both. Every patch is undone.

    DOCUMENTED SUBSTITUTION: ``probe.adapted_model`` is a stand-in bound against the real
    signature. It runs the REAL ``prove_published_adapter`` on a fixture adapter and returns the
    fixture base with the real tokenizer and forbid mask, because CI has no persona_adapter.pt and
    the real 78 components address a full-size adapter the fixture base cannot carry; the ablation
    route is exercised by the MPS run and by Phase 19's own tests. Every other call is REAL:
    build_unadapted_base, probe_guessability, exact_match_clean, reference_set_for,
    value_span_nll_mean, assert_no_value_in_prompt and draw_all through DrawTimer.
    """
    import phase14_factset
    import phase14_factset_gate
    import phase14_recall
    import phase16_persistence
    import phase17_persona_gate
    import phase19_erasure

    from personacore.checkpoint import export_slim
    from personacore.config import ModelConfig
    from personacore.tokenizer import from_json
    from test_phase22_wiring import _e2e_env

    strays_before = _real_probe36_strays()
    # B1: from the committed JSON alone, before any patch — never from the gitignored .pt.
    real_components = probe.e1_components()
    adapter_signature = inspect.signature(probe.adapted_model)
    log = []
    spies = {"guess": [], "match": [], "nll": [], "adapter": [], "hashed": []}
    heartbeat = root / "heartbeat.jsonl"
    ledger = root / "ledger" / "v6_mps_ledger.jsonl"
    buf = io.StringIO()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(phase25_run, "_DEVICE", "cpu")
        _e2e_env(root, mp)
        slim = root / "convbase_slim.pt"
        export_slim(root / "convbase.pt", slim)
        mp.setattr(phase14_recall, "CONVBASE_SLIM", slim)
        mp.setattr(phase17_persona_gate, "CONVBASE_SLIM", slim)
        # The SHAPE is scaled, not the instrument: generation budgets cut to 4 tokens.
        mp.setattr(phase14_recall, "RECALL_MAX_NEW_TOKENS", 4)
        mp.setattr(phase14_factset_gate, "PROBE_MAX_NEW_TOKENS", 4)
        mp.setattr(probe, "_ROOT", root)
        # W1: this module-scoped fixture runs before the autouse clean_tree patch applies.
        mp.setattr(probe, "refuse_if_dirty", lambda **kw: "")
        mp.setattr(phase25_run, "disk_precheck", lambda target=None: None)
        # Redirects of gitignored inputs (absent on CI; never a skipif — the ubuntu skip pin):
        # checkpoints/persona_adapter.pt -> a fixture adapter, and the published sha -> its sha;
        # checkpoints/convbase_slim.pt -> the fixture slim base above; data/probe36_e1_run.json
        # (the E1 sidecar E6's beside reads) -> a planted numbers-only sidecar under root.
        adapter = root / "checkpoints" / "fixture_adapter.pt"
        adapter.write_bytes(b"fixture adapter bytes")
        sha = hashlib.sha256(adapter.read_bytes()).hexdigest()
        mp.setattr(phase14_recall, "ADAPTER_PATH", adapter)
        mp.setattr(probe, "published_adapter_sha256", lambda: sha)
        mp.setattr(probe, "e1_components", lambda: real_components)
        real_sha256 = probe._sha256
        mp.setattr(
            probe,
            "_sha256",
            lambda path: spies["hashed"].append(pathlib.Path(path)) or real_sha256(path),
        )

        def stand_in(*args, **kwargs):
            arguments = adapter_signature.bind(*args, **kwargs).arguments
            assert arguments["k"] in (0, len(real_components))
            spies["adapter"].append(arguments["k"])
            probe.prove_published_adapter()  # the real adapted_model's first line
            model, _cfg, _ckpt = phase17_persona_gate.build_unadapted_base(arguments["device"])
            tok = from_json(phase14_recall.TOKENIZER_PATH)
            forbid = phase16_persistence.resolve_forbid(tok, ModelConfig.vocab_size)[0]
            return model, tok, forbid

        mp.setattr(probe, "adapted_model", stand_in)
        # The fixture base has RANDOM weights, so it emits lone UTF-8 continuation-byte tokens
        # that the real instrument's strict tok.decode (phase14_factset_gate._probe) refuses; the
        # real base decoded all 416 published completions. The fixture mask also forbids every id
        # whose standalone decode fails, so any sampled sequence decodes. Fixture-only.
        real_forbid = phase16_persistence.resolve_forbid

        def fixture_forbid(tok, vocab_size):
            mask, digest = real_forbid(tok, vocab_size)
            mask = mask.clone()
            for idx in (~mask[0]).nonzero().flatten().tolist():
                try:
                    tok.decode([idx])
                except UnicodeDecodeError:
                    mask[0, idx] = True
            return mask, digest

        mp.setattr(phase16_persistence, "resolve_forbid", fixture_forbid)

        def forward(module, name, on_call):
            real = getattr(module, name)

            def spy(*args, **kwargs):
                on_call(*args, **kwargs)
                return real(*args, **kwargs)

            mp.setattr(module, name, spy)

        forward(
            phase14_recall,
            "assert_no_value_in_prompt",
            lambda tok, question, values, *, prompt_ids=None: log.append(
                ("assert", list(prompt_ids))
            ),
        )
        forward(
            phase14_recall,
            "draw_all",
            lambda model, tok, prompt_ids, *a, **kw: log.append(("draw", list(prompt_ids))),
        )
        forward(
            phase14_factset_gate, "probe_guessability", lambda *a, **kw: spies["guess"].append(1)
        )
        forward(phase14_factset, "exact_match_clean", lambda t, v: spies["match"].append(v))
        forward(phase19_erasure, "value_span_nll_mean", lambda *a, **kw: spies["nll"].append(1))
        _planted_e1_sidecar()
        argv = ["run", "--heartbeat", str(heartbeat), "--ledger", str(ledger)]
        argv += ["--front", "e5", "e6"]
        with contextlib.redirect_stdout(buf):
            assert probe.main(argv) == 0
        sidecars = {
            f: json.loads(probe.run_sidecar(f).read_text(encoding="utf-8")) for f in ("e5", "e6")
        }
        records = {}
        for front in ("e5", "e6"):
            out = root / "emitted" / f"phase36_probe_{front}.json"
            probe.emit(front, out_path=out)  # the REAL _emit_target -> _write_record (W10)
            records[front] = json.loads(out.read_text(encoding="utf-8"))
    return {
        "root": root,
        "sidecars": sidecars,
        "records": records,
        "log": log,
        "spies": spies,
        "strays": (strays_before, _real_probe36_strays()),
        "stdout": buf.getvalue(),
        "ledger": ledger,
        "components": real_components,
    }


@pytest.fixture(scope="module")
def e5_e6_live(tmp_path_factory):
    return _e5_e6_live_fixture(tmp_path_factory.mktemp("e5_e6_live"))


def test_live_e5_e6_reach_every_instrument(e5_e6_live):
    import phase17_persona_facts
    import phase17_personas
    import phase18_extraction

    spies, slots = e5_e6_live["spies"], phase17_personas.CORE_SLOTS
    k78 = len(e5_e6_live["components"])
    assert spies["adapter"] == [0, k78, k78]  # E5 scoring k = 0 and k = 78, then E6 at k = 78
    assert len(spies["guess"]) == len(slots)
    published = [f.value for facts in phase17_persona_facts.PERSONA_FACTS.values() for f in facts]
    anchors = [f.value for f in phase17_persona_facts.PERSONA_FACTS[phase17_personas.PERSONAS[0]]]
    # probe_guessability calls exact_match_clean once itself per slot, on that slot's anchor.
    assert sorted(spies["match"]) == sorted(published + anchors)
    sizes = [len(phase18_extraction.reference_set_for(s)) for s in slots]
    assert len(spies["nll"]) == 2 * sum(sizes)


def test_live_e6_asserts_each_anchor_before_its_draw(e5_e6_live):
    import phase14_factset

    log, slots = e5_e6_live["log"], phase14_factset.LOCKED_FACTS
    assert [kind for kind, _ids in log] == ["assert", "draw"] * len(slots)
    for i in range(len(slots)):
        assert log[2 * i][1] == log[2 * i + 1][1]
    stages = e5_e6_live["sidecars"]["e6"]["stages"]
    assert stages["draws"] == len(slots) * phase36_prereg.phase35_prereg.FULL_FIDELITY_K
    assert len(stages["per_slot_draw_seconds_mean"]) == len(slots)


def test_live_e5_timed_every_slot_and_every_match(e5_e6_live):
    import phase17_personas

    clearance = e5_e6_live["sidecars"]["e5"]["stages"]["clearance"]
    assert len(clearance["per_slot_seconds"]) == len(phase17_personas.CORE_SLOTS)
    assert clearance["candidates_matched"] == clearance["match_seconds_spread"]["n"]
    assert clearance["candidates_matched"] == 3 * len(phase17_personas.CORE_SLOTS)  # 24 values
    assert all(s > 0 for s in clearance["per_slot_seconds"])
    assert e5_e6_live["sidecars"]["e5"]["reused"] == {"e5": False}


def test_live_e5_e6_records_pass_the_gate_with_provenance(e5_e6_live):
    for front, record in e5_e6_live["records"].items():
        probe.prove_no_reading(record)
        assert record["front"] == front and record["gates_nothing"] is True
        assert record["provenance"]["run"]["device"] == "cpu"
        assert set(record["provenance"]["module_sha256"]) == set(probe.PINNED_MODULES)
    beside = e5_e6_live["records"]["e6"]["a2_context_from_e1"]
    assert beside == {
        "a2_context_question_k48_seconds_high": 4.0,
        "path": "data/probe36_e1_run.json",
    }
    assert e5_e6_live["records"]["e5"]["repetitions"] == e5_e6_live["records"]["e6"]["repetitions"]


def test_live_e5_e6_stdout_holds_no_reading(e5_e6_live):
    text = e5_e6_live["stdout"]
    for front in ("e5", "e6"):  # not blind: run_front's own lines were captured
        assert re.search(rf"^\[phase36_probe\] {front} \d+\.\d s$", text, re.MULTILINE), text
    for word in ("clean", "hits", "per_fact"):
        assert word not in text, text
    assert not re.search(r"\d+/\d+ = ", text), text


def test_live_e5_e6_ledger(e5_e6_live):
    lines = phase36_ledger.read_ledger(e5_e6_live["ledger"])
    expected = []
    for front in ("e5", "e6"):
        rid = phase36_ledger.run_id(36, "probes", front)
        expected += [("start", rid, None), ("end", rid, phase36_prereg.probe_record(front))]
    assert [(x["event"], x["run_id"], x.get("record")) for x in lines] == expected


def test_live_e5_e6_writes_nothing_in_the_real_tree(e5_e6_live):
    before, after = e5_e6_live["strays"]
    assert before == after
    assert not any((e5_e6_live["root"] / "results").iterdir())


def test_live_e5_e6_never_hashed_the_gitignored_adapter(e5_e6_live):
    hashed = e5_e6_live["spies"]["hashed"]
    assert e5_e6_live["root"] / "checkpoints" / "fixture_adapter.pt" in hashed  # non-vacuous
    assert not [p for p in hashed if p.is_relative_to(probe._GIT_ROOT / "checkpoints")]


# =================================================================================================
# Plan 36-04 Task 3 — the unattended LaunchAgent (D-16)
# =================================================================================================


def test_plist_mirrors_the_phase31_probe_agent():
    import plistlib

    ours = plistlib.loads((_ROOT / "artifacts/com.personacore.phase36.probe.plist").read_bytes())
    phase31 = plistlib.loads((_ROOT / "artifacts/com.personacore.phase31.probe.plist").read_bytes())
    assert ours["Label"] == "com.personacore.phase36.probe"
    assert ours["KeepAlive"] is False and ours["RunAtLoad"] is False
    args, phase31_args = ours["ProgramArguments"], phase31["ProgramArguments"]
    assert args[:3] == phase31_args[:3] and args[:2] == ["/usr/bin/caffeinate", "-dims"]
    assert args[2].endswith("/.venv/bin/python")
    assert args[3].endswith("scripts/phase36_probe.py") and args[4] == "run"
    # R-2: a suffix comparison, so the assertion is host-independent (CI's root is elsewhere).
    expected = phase36_ledger.HEARTBEAT_PATH.relative_to(_ROOT).parts
    heartbeat = pathlib.Path(args[args.index("--heartbeat") + 1])
    assert heartbeat.parts[-len(expected) :] == expected
    assert args == [*args[:5], "--heartbeat", str(heartbeat)]  # runs every front in RUN_ORDER
    assert ours["WorkingDirectory"] == phase31["WorkingDirectory"]
    for key in ("StandardOutPath", "StandardErrorPath"):
        assert "/logs/" in ours[key] and ours[key] != phase31[key]
    assert ours["StandardOutPath"].endswith("logs/phase36_probe.out")
    assert ours["StandardErrorPath"].endswith("logs/phase36_probe.err")
    assert ours["EnvironmentVariables"] == phase31["EnvironmentVariables"]
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"
    assert ours["ProcessType"] == phase31["ProcessType"]
    # main() parses exactly these arguments into a run over the default RUN_ORDER.
    parsed = probe.build_parser().parse_args(args[4:])
    assert parsed.mode == "run" and tuple(parsed.front) == probe.RUN_ORDER


# =================================================================================================
# Plan 36-05 Task 1 — E3 (D-05, D-19): the published sigma point at both step counts, light
# =================================================================================================


def test_loop_timer_sums_counts_and_restores():
    import types

    def loop(**kwargs):
        if kwargs.get("boom"):
            raise RuntimeError("loop died")
        return "trained"

    fake = types.SimpleNamespace(train=loop)
    with probe.loop_timer(fake) as box:
        assert fake.train is not loop
        assert fake.train(steps=2) == "trained"
    assert fake.train is loop and box["calls"] == 1 and box["seconds"] >= 0
    with pytest.raises(RuntimeError, match="loop died"), probe.loop_timer(fake) as box:
        fake.train(boom=True)
    assert fake.train is loop and box["calls"] == 1


def test_e3_plan_rekeys_the_published_point():
    import phase25_points

    published = phase25_points.point_plan(phase36_prereg.E3_PROBE_POINT_KEY)
    assert probe.e3_steps() == tuple(phase36_prereg.ENTRIES["e3_probe_steps"]["value"])
    for steps in probe.e3_steps():
        plan = probe.e3_plan(steps)
        assert plan["point_key"] == f"probe36_e3_t{steps}"
        assert plan["prefix"] == f"probe36_t{steps}"
        assert plan["pinned_mechanism"] == dict(published["pinned_mechanism"], composed_steps=steps)
        changed = {"point_key", "prefix", "pinned_mechanism"}
        assert {k: v for k, v in plan.items() if k not in changed} == {
            k: v for k, v in published.items() if k not in changed
        }
        assert plan["arm"] == "dp_n8" and plan["dp_sigma"] == 0.5 and plan["seed"] == 1337
        for label in (plan["point_key"], plan["prefix"]):
            assert probe.prove_isolated_label(label) == label


def _e3_light(tmp_path, monkeypatch, *, crash_on=None, resumed=0, composed_offset=0, draws=None):
    """stage_e3 with train_stage and score_arm faked and recorded; no model, no training."""
    import phase14_recall
    import phase25_points
    import teach_persona as tp

    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(phase25_points, "_ROOT", tmp_path)
    monkeypatch.setattr(tp, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    (tmp_path / "checkpoints").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(tp, "train", lambda **kw: "the fake loop")
    monkeypatch.setattr(phase14_recall, "_complete", lambda *a, **kw: ([3, 3], True))
    per_question = 1 + phase14_recall.N_SEEDED_SAMPLES
    calls = {"train": [], "score": [], "loop": tp.train, "max_steps": tp.MAX_STEPS}

    def train_stage(plan):
        calls["train"].append((plan, tp.MAX_STEPS))
        if crash_on == len(calls["train"]):
            raise RuntimeError("training died")
        tp.train()
        adapter = tp.arm_outputs(plan["arm"], prefix=plan["prefix"])["adapter"]
        adapter.write_bytes(plan["point_key"].encode())
        return {
            "seconds": 2.5,
            "adapter_sha256": hashlib.sha256(adapter.read_bytes()).hexdigest(),
            "resumed_from_step": resumed,
            "live_mechanism": {"composed_steps": tp.MAX_STEPS + composed_offset},
            "final_train_loss": 1.0,
        }

    def score_arm(arm, facts, adapter_path, device):
        calls["score"].append((arm, facts, adapter_path, device))
        for _ in range(2 * per_question if draws is None else draws):
            phase14_recall._complete(None, [0], device, None)
        print("taught ON: 3/4 = 0.75, per-family gain")
        return {"on_taught": {"rate": 0.75}}

    monkeypatch.setattr(phase25_points, "train_stage", train_stage)
    monkeypatch.setattr(tp, "score_arm", score_arm)
    return calls


def test_stage_e3_light_trains_both_runs_and_scores_only_the_step_budget_run(
    tmp_path, monkeypatch, capsys
):
    import phase14_factset
    import phase14_recall
    import teach_persona as tp

    calls = _e3_light(tmp_path, monkeypatch)
    state = {"point": "x", "stage": "start", "shape": None, "draw_index": None}
    out = probe.stage_e3(state)
    assert capsys.readouterr().out == ""
    short, longest = probe.e3_steps()
    assert [(plan["point_key"], seen) for plan, seen in calls["train"]] == [
        (f"probe36_e3_t{short}", short),
        (f"probe36_e3_t{longest}", longest),
    ]
    assert tp.MAX_STEPS == calls["max_steps"] and tp.train is calls["loop"]  # restored
    ((arm, facts, adapter, device),) = calls["score"]
    assert arm == "dp_n8" and facts is phase14_factset.LOCKED_FACTS and device == "cpu"
    assert adapter == tp.arm_outputs("dp_n8", prefix=f"probe36_t{short}")["adapter"]
    per_question = 1 + phase14_recall.N_SEEDED_SAMPLES
    budget, longest_run = out["t_step_budget"], out["t_max_steps"]
    assert budget["steps"] == short and longest_run["steps"] == longest
    assert budget["score_draws"] == 2 * per_question == len(budget["score_draw_seconds"])
    assert budget["score_draws_per_question"] == per_question
    assert all(type(s) is float for s in budget["score_draw_seconds"])
    assert budget["score_fixed_seconds"] == pytest.approx(
        budget["score_seconds"] - sum(budget["score_draw_seconds"])
    )
    for run in (budget, longest_run):
        assert run["train_seconds"] == 2.5
        assert run["overhead_seconds"] == run["train_seconds"] - run["loop_seconds"]
    assert set(longest_run) == {"train_seconds", "loop_seconds", "overhead_seconds", "steps"}
    config = out["configuration"]
    assert config["point_key"] == phase36_prereg.E3_PROBE_POINT_KEY
    assert (config["arm"], config["sigma"], config["lr"], config["seed"]) == (
        "dp_n8",
        0.5,
        3e-4,
        1337,
    )
    assert config["batch"] == tp.BATCH_SIZE and config["steps"] == [short, longest]
    assert out["reused"] == {"e3": False} and state["stage"] == f"e3_t{longest}"
    run = {"front": "e3", "run_id": "v6/36/probes/e3", "reused": out.pop("reused"), "stages": out}
    record = probe.build_record("e3", run)
    assert set(record["stages"]) == {"t_step_budget", "t_max_steps"}
    assert record["repetitions"] == 2
    assert "0.75" not in json.dumps(record)
    assert probe._e3_stages(out) == (record["stages"], 2)
    out["t_max_steps"]["score_seconds"] = 1.0
    with pytest.raises(SystemExit, match="training only"):
        probe._e3_stages(out)


@pytest.mark.parametrize("crash_on", [1, 2])
def test_stage_e3_restores_max_steps_and_train_after_a_crash(tmp_path, monkeypatch, crash_on):
    import teach_persona as tp

    calls = _e3_light(tmp_path, monkeypatch, crash_on=crash_on)
    with pytest.raises(RuntimeError, match="training died"):
        probe.stage_e3({})
    assert len(calls["train"]) == crash_on
    assert tp.MAX_STEPS == calls["max_steps"] and tp.train is calls["loop"]


@pytest.mark.parametrize("which", ["sidecar", "adapter", "checkpoint"])
@pytest.mark.parametrize("run_index", [0, 1])
def test_stage_e3_refuses_a_reused_or_resumable_output(tmp_path, monkeypatch, which, run_index):
    import phase25_points
    import teach_persona as tp

    calls = _e3_light(tmp_path, monkeypatch)
    plan = probe.e3_plan(probe.e3_steps()[run_index])
    outputs = tp.arm_outputs(plan["arm"], prefix=plan["prefix"])
    path = {
        "sidecar": phase25_points.training_sidecar(plan["point_key"]),
        "adapter": outputs["adapter"],
        "checkpoint": outputs["checkpoint"],
    }[which]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="Pitfall 5"):
        probe.stage_e3({})
    assert calls["train"] == []  # refused before any training


def test_stage_e3_refuses_a_resumed_run_and_a_short_composition(tmp_path, monkeypatch):
    _e3_light(tmp_path, monkeypatch, resumed=3)
    with pytest.raises(SystemExit, match="W2"):
        probe.stage_e3({})
    _e3_light(tmp_path / "short", monkeypatch, composed_offset=-1)
    with pytest.raises(SystemExit, match="seam composed"):
        probe.stage_e3({})


def test_stage_e3_refuses_a_score_draw_count_off_the_question_grid(tmp_path, monkeypatch):
    _e3_light(tmp_path, monkeypatch, draws=5)
    with pytest.raises(SystemExit, match="draws per question"):
        probe.stage_e3({})


def test_e3_p22_runs_before_any_training_and_the_score_is_never_bound():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    (stage,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "stage_e3"]
    calls = [n for n in ast.walk(stage) if isinstance(n, ast.Call)]
    first_train = min(n.lineno for n in calls if getattr(n.func, "attr", None) == "train_stage")
    p22 = [n for n in calls if getattr(n.func, "attr", None) == "prove_p22"]
    assert len(p22) == 1 and p22[0].lineno < first_train
    assert "e3_max_steps" in ast.unparse(p22[0])  # the REAL cap, never e3_steps()
    (score,), parents = _stage_calls("stage_e3", "score_arm")
    assert isinstance(parents[score], ast.Expr)
    assert {"silenced()", "DrawTimer()"} <= set(_with_items(score, parents))
    (train,), parents = _stage_calls("stage_e3", "train_stage")
    assert {"silenced()", "loop_timer(tp)"} <= set(_with_items(train, parents))


# =================================================================================================
# Plan 36-05 — the CPU live path of the training fronts: main -> run_all -> run_front -> stage
# =================================================================================================


def _live_env(root, mp, spies):
    """Every patch a CPU live run of ANY front needs, on ``mp`` (a MonkeyPatch.context, W1).

    The SHAPE is scaled, never the instrument: _e2e_env's two-step recipe, 4-token generation, a
    3 x 4 A2 pass, and E3 at (MAX_STEPS, 2 x MAX_STEPS) — a documented substitution for the
    pre-registered (200, 800); prove_p22 still runs on the REAL e3_max_steps (stage_e3 reads the
    entry, not e3_steps). Gitignored inputs are redirected, never skipped (the ubuntu skip pin):
    persona_adapter.pt -> a fixture adapter and its published sha, convbase_slim.pt -> the
    fixture slim base. The two pin entry points the fixture base cannot carry are stand-ins bound
    against the REAL signatures: run_erasure_arm (draws through the REAL draw_all, so DrawTimer
    times real _complete calls) and adapted_model (the 78 real components address a full-size
    adapter; Phase 19's own tests cover the ablation).
    """
    import numpy as np
    import phase14_factset_gate
    import phase14_recall
    import phase16_persistence
    import phase17_persona_gate
    import phase19_erasure
    import phase25_points
    import teach_persona as tp

    from personacore.checkpoint import export_slim
    from personacore.config import ModelConfig
    from personacore.tokenizer import from_json
    from test_phase22_wiring import _e2e_env

    real_components = probe.e1_components()  # B1: the committed JSON, before any patch
    pin_signature = inspect.signature(phase19_erasure.run_erasure_arm)
    adapter_signature = inspect.signature(probe.adapted_model)
    entries = phase36_prereg.phase35_prereg.a2_corpus_entries()[:LIVE_QUESTIONS]
    mp.setattr(phase25_run, "_DEVICE", "cpu")
    _e2e_env(root, mp)
    # The published M2 recipe bakes replay into its bin at the `real` arm's ratio (legacy sizing,
    # teach_persona._prepend_replay): ~9.2k tokens, more than _e2e_env's four windows. Same
    # decodable ids, tiled (the tests/test_phase21_replay_volume.py 20,000-element precedent).
    replay = np.resize(np.fromfile(tp.DIALOG_TRAIN_BIN, dtype=np.uint16), 20_000)
    replay.tofile(tp.DIALOG_TRAIN_BIN)
    np.ones(replay.size, dtype=np.uint8).tofile(tp.DIALOG_TRAIN_MASK)
    slim = root / "convbase_slim.pt"
    export_slim(root / "convbase.pt", slim)
    mp.setattr(phase14_recall, "CONVBASE_SLIM", slim)
    mp.setattr(phase17_persona_gate, "CONVBASE_SLIM", slim)
    mp.setattr(phase14_recall, "RECALL_MAX_NEW_TOKENS", 4)
    mp.setattr(phase14_factset_gate, "PROBE_MAX_NEW_TOKENS", 4)
    mp.setattr(probe, "_ROOT", root)
    mp.setattr(phase25_points, "_ROOT", root)
    mp.setattr(probe, "refuse_if_dirty", lambda **kw: "")
    mp.setattr(phase25_run, "disk_precheck", lambda target=None: None)
    adapter = root / "checkpoints" / "fixture_adapter.pt"
    adapter.write_bytes(b"fixture adapter bytes")
    sha = hashlib.sha256(adapter.read_bytes()).hexdigest()
    mp.setattr(phase14_recall, "ADAPTER_PATH", adapter)
    mp.setattr(probe, "published_adapter_sha256", lambda: sha)
    mp.setattr(probe, "e1_shape", lambda: (LIVE_QUESTIONS, LIVE_K))
    mp.setattr(probe, "e1_components", lambda: real_components)
    fixture_steps = (tp.MAX_STEPS, 2 * tp.MAX_STEPS)
    mp.setattr(probe, "e3_steps", lambda: fixture_steps)
    real_sha256 = probe._sha256
    mp.setattr(
        probe,
        "_sha256",
        lambda path: spies["hashed"].append(pathlib.Path(path)) or real_sha256(path),
    )
    # The random-weight base emits lone continuation bytes the strict decode refuses (36-04).
    real_forbid = phase16_persistence.resolve_forbid

    def fixture_forbid(tok, vocab_size):
        mask, digest = real_forbid(tok, vocab_size)
        mask = mask.clone()
        for idx in (~mask[0]).nonzero().flatten().tolist():
            try:
                tok.decode([idx])
            except UnicodeDecodeError:
                mask[0, idx] = True
        return mask, digest

    mp.setattr(phase16_persistence, "resolve_forbid", fixture_forbid)

    def base(device):
        model, _cfg, _ckpt = phase17_persona_gate.build_unadapted_base(device)
        tok = from_json(phase14_recall.TOKENIZER_PATH)
        return model, tok, phase16_persistence.resolve_forbid(tok, ModelConfig.vocab_size)[0]

    def adapted(*args, **kwargs):
        arguments = adapter_signature.bind(*args, **kwargs).arguments
        assert arguments["k"] in (0, len(real_components))
        probe.prove_published_adapter()  # the real adapted_model's first line
        return base(arguments["device"])

    mp.setattr(probe, "adapted_model", adapted)

    def pin(*args, **kwargs):
        arguments = pin_signature.bind(*args, **kwargs).arguments
        if arguments["arm"] == "erased":
            assert arguments["components"] == real_components
        else:
            assert arguments["arm"] == "retrain"
            m2 = tp.arm_outputs(probe.E2_ARMS[0], prefix=probe.PROBE_PREFIX)["adapter"]
            assert pathlib.Path(arguments["adapter_path"]) == m2 and m2.exists()
        record_path = pathlib.Path(arguments["record_path"])
        assert record_path.parent == root / "data" and record_path.name.startswith("probe36_e")
        spies["pin_calls"].append(dict(arguments))
        model, tok, forbid = base(arguments["device"])
        for entry in entries:
            phase14_recall.draw_all(
                model,
                tok,
                entry["prompt_ids"],
                arguments["device"],
                forbid,
                entry["seed_index"] * LIVE_K,
                n_samples=LIVE_K - 1,
            )
        record_path.write_text(json.dumps({"completions": ["Biscuit"]}), encoding="utf-8")
        print("taught ON: 3/4 = 0.75 per_fact hits")
        return {"per_fact": [{"hits": 3}]}

    mp.setattr(phase19_erasure, "run_erasure_arm", pin)

    def forward(module, name, key):
        real = getattr(module, name)

        def spy(*args, **kwargs):
            out = real(*args, **kwargs)
            spies[key].append((args, kwargs, out))
            return out

        mp.setattr(module, name, spy)

    forward(phase25_points, "train_stage", "train_stage")
    forward(tp, "score_arm", "score_arm")
    forward(phase36_prereg, "prove_p22", "p22")
    return fixture_steps


def _spies():
    keys = ("hashed", "pin_calls", "train_stage", "score_arm", "p22", "stages")
    return {key: [] for key in keys}


def _live_run(root, fronts, *, wrap_stages=False):
    """ONE CPU run of ``fronts`` through main(['run']), then the REAL emit of each (W10)."""
    import teach_persona as tp

    strays_before = _real_probe36_strays()
    spies, buf = _spies(), io.StringIO()
    heartbeat, ledger = root / "heartbeat.jsonl", root / "ledger" / "v6_mps_ledger.jsonl"
    with pytest.MonkeyPatch.context() as mp:
        fixture_steps = _live_env(root, mp, spies)
        fixture_max_steps = tp.MAX_STEPS
        if wrap_stages:  # Pitfall 9: bind (state,) against each REAL stage, then forward to it
            for front in probe.RUN_ORDER:
                real = probe.STAGES[front]

                def recorder(*args, _front=front, _real=real, **kwargs):
                    inspect.signature(_real).bind(*args, **kwargs)
                    spies["stages"].append(_front)
                    return _real(*args, **kwargs)

                mp.setitem(probe.STAGES, front, recorder)
        argv = ["run", "--heartbeat", str(heartbeat), "--ledger", str(ledger)]
        if fronts is not None:
            argv += ["--front", *fronts]
        with contextlib.redirect_stdout(buf):
            assert probe.main(argv) == 0
        ran = probe.RUN_ORDER if fronts is None else tuple(fronts)
        max_steps_after = tp.MAX_STEPS
        sidecars = {f: json.loads(probe.run_sidecar(f).read_text(encoding="utf-8")) for f in ran}
        records = {}
        for front in ran:
            out = root / "emitted" / f"phase36_probe_{front}.json"
            probe.emit(front, out_path=out)  # the REAL _emit_target -> _write_record
            records[front] = json.loads(out.read_text(encoding="utf-8"))
    return {
        "root": root,
        "sidecars": sidecars,
        "records": records,
        "spies": spies,
        "strays": (strays_before, _real_probe36_strays()),
        "stdout": buf.getvalue(),
        "ledger": ledger,
        "fixture_steps": fixture_steps,
        "max_steps": (fixture_max_steps, max_steps_after),
    }


@pytest.fixture(scope="module")
def e3_live(tmp_path_factory):
    return _live_run(tmp_path_factory.mktemp("e3_live"), ("e3",))


def test_live_e3_trains_both_step_counts_through_the_real_train_stage(e3_live):
    blobs = [out for _args, _kw, out in e3_live["spies"]["train_stage"]]
    steps = e3_live["fixture_steps"]
    assert [b["live_mechanism"]["composed_steps"] for b in blobs] == list(steps)
    assert [b["resumed_from_step"] for b in blobs] == [0, 0]
    assert [b["point_key"] for b in blobs] == [f"probe36_e3_t{s}" for s in steps]
    assert len(e3_live["spies"]["score_arm"]) == 1
    ((args, _kw, _out),) = e3_live["spies"]["score_arm"]
    assert (
        args[0] == "dp_n8" and pathlib.Path(args[2]).name == f"probe36_t{steps[0]}_dp_n8_adapter.pt"
    )
    before, after = e3_live["max_steps"]
    assert before == after  # tp.MAX_STEPS restored after both runs
    # RECIPE-04 ran on the REAL cap even though the fixture trains at fixture steps.
    assert [args for args, _kw, _out in e3_live["spies"]["p22"]][0] == (
        phase36_prereg.ENTRIES["e3_max_steps"]["value"],
    )


def test_live_e3_record_shape_and_gate(e3_live):
    record = e3_live["records"]["e3"]
    probe.prove_no_reading(record)
    assert record["provenance"]["run"]["device"] == "cpu" and record["repetitions"] == 2
    budget, longest = record["stages"]["t_step_budget"], record["stages"]["t_max_steps"]
    assert (budget["steps"], longest["steps"]) == e3_live["fixture_steps"]
    assert budget["score_draws"] == len(budget["score_draw_seconds"]) > 0
    assert budget["score_draws"] % budget["score_draws_per_question"] == 0
    assert all(type(s) is float for s in budget["score_draw_seconds"])
    assert set(longest) == {"train_seconds", "loop_seconds", "overhead_seconds", "steps"}
    for run in (budget, longest):
        assert 0 < run["loop_seconds"] < run["train_seconds"]
    assert e3_live["sidecars"]["e3"]["reused"] == {"e3": False}


def test_live_e3_stdout_holds_no_reading(e3_live):
    text = e3_live["stdout"]
    assert re.search(r"^\[phase36_probe\] e3 \d+\.\d s$", text, re.MULTILINE), text
    assert "gain" not in text and not re.search(r"\d+/\d+ = ", text), text


def test_live_e3_writes_nothing_in_the_real_tree(e3_live):
    root = e3_live["root"]
    assert not any((root / "results").iterdir())  # train_stage moved its csv under data/
    before, after = e3_live["strays"]
    assert before == after
    hashed = e3_live["spies"]["hashed"]
    assert hashed and not [p for p in hashed if p.is_relative_to(probe._GIT_ROOT / "checkpoints")]


# =================================================================================================
# Plan 36-05 Task 2 — E2 (D-08): two M2 retrains + one K = 48 A2 pass, light (no model)
# =================================================================================================

_E2_SENTINEL = "SENTINEL taught ON: 3/4 = 0.75"


def _e2_light(tmp_path, monkeypatch, *, draws=6, on_pin=None):
    """stage_e2 with the teaching driver and the pin faked and recorded; no model, no training."""
    import phase14_recall
    import phase19_erasure
    import teach_persona as tp

    monkeypatch.setattr(probe, "_ROOT", tmp_path)
    monkeypatch.setattr(tp, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    adapter = tmp_path / "checkpoints" / "fixture_adapter.pt"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_bytes(b"fixture adapter")
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", adapter)
    monkeypatch.setattr(probe, "e1_shape", lambda: (2, 3))
    monkeypatch.setattr(tp, "train", lambda **kw: "the fake loop")
    monkeypatch.setattr(phase14_recall, "_complete", lambda *a, **kw: ([3, 3], True))
    calls = {"teach": [], "pin": [], "loop": tp.train}

    def fake_teach(arm, **kwargs):
        calls["teach"].append((arm, kwargs))
        tp.train()
        paths = tp.arm_outputs(arm, prefix=kwargs["prefix"])
        for key in ("csv", "checkpoint", "adapter"):
            paths[key].parent.mkdir(parents=True, exist_ok=True)
            paths[key].write_text(arm, encoding="utf-8")
        print(_E2_SENTINEL)
        return {"final_train_loss": 1.0, "ppl_adapter_on": 2.0}

    def pin(arm, device, **kwargs):
        calls["pin"].append((arm, device, kwargs))
        for _ in range(draws):
            phase14_recall._complete(None, [0], device, None)
        pathlib.Path(kwargs["record_path"]).write_text(_E2_SENTINEL, encoding="utf-8")
        if on_pin is not None:
            on_pin(adapter)
        print(_E2_SENTINEL)
        return {"per_fact": [1]}

    monkeypatch.setattr(tp, "train_arm", fake_teach)
    monkeypatch.setattr(phase19_erasure, "run_erasure_arm", pin)
    return calls


@pytest.mark.parametrize(
    "arm", ["real", "erase_reference", "phase19_m2", "probe36", "probe31_m2", "xprobe36_m2"]
)
def test_train_e2_rep_refuses_real_and_foreign_arm_names(tmp_path, monkeypatch, arm):
    calls = _e2_light(tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        probe.train_e2_rep(arm, (), False, 0.0)
    assert calls["teach"] == []


@pytest.mark.parametrize("which", ["adapter", "checkpoint", "csv"])
def test_train_e2_rep_refuses_stale_outputs(tmp_path, monkeypatch, which):
    import teach_persona as tp

    calls = _e2_light(tmp_path, monkeypatch)
    arm = probe.E2_ARMS[0]
    if which == "csv":
        path = tmp_path / "data" / "probe36_e2" / arm / "run.csv"
    else:
        path = tp.arm_outputs(arm, prefix=probe.PROBE_PREFIX)[which]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("stale", encoding="utf-8")
    with pytest.raises(SystemExit, match="stale probe output"):
        probe.train_e2_rep(arm, (), False, 0.0)
    assert calls["teach"] == []


def test_train_e2_rep_moves_the_csv_under_data(tmp_path, monkeypatch, capsys):
    import phase14_factset
    import teach_persona as tp

    calls = _e2_light(tmp_path, monkeypatch)
    arm = probe.E2_ARMS[1]
    rep = probe.train_e2_rep(arm, ("f",), True, 0.25)
    assert capsys.readouterr().out == ""
    ((called, kwargs),) = calls["teach"]
    assert called == arm and kwargs == {
        "facts": ("f",),
        "family_ids": phase14_factset.TAUGHT_FAMILY_IDS,
        "second_person": True,
        "replay_ratio": 0.25,
        "prefix": "probe36",
    }
    assert set(rep) == {"outer_seconds", "loop_seconds", "overhead_seconds"}
    assert rep["overhead_seconds"] == rep["outer_seconds"] - rep["loop_seconds"]
    assert tp.train is calls["loop"]  # restored
    csv = tp.arm_outputs(arm, prefix=probe.PROBE_PREFIX)["csv"]
    assert not csv.parent.exists()  # WR-01: results/<prefix>_<arm>/ is gone
    assert (tmp_path / "data" / "probe36_e2" / arm / "run.csv").read_text(encoding="utf-8") == arm
    assert not list((tmp_path / "checkpoints").glob("phase19_*"))
    assert not (tmp_path / "checkpoints" / "persona_adapter.pt").exists()


def test_stage_e2_light_times_two_reps_and_one_a2_pass(tmp_path, monkeypatch, capsys):
    import phase14_factset
    import phase19_erasure
    import teach_persona as tp

    calls = _e2_light(tmp_path, monkeypatch)
    adapter_before = (tmp_path / "checkpoints" / "fixture_adapter.pt").read_bytes()
    state = {"point": "x", "stage": "start", "shape": None, "draw_index": None}
    out = probe.stage_e2(state)
    assert capsys.readouterr().out == ""
    target = {f.slot: f for f in phase14_factset.LOCKED_FACTS}[phase19_erasure.TARGET_SLOT]
    facts, second_person, replay_ratio = phase19_erasure.retrain_arm_spec(target.id)
    assert [arm for arm, _kw in calls["teach"]] == list(probe.E2_ARMS)
    for _arm, kwargs in calls["teach"]:
        assert kwargs["facts"] == facts and kwargs["second_person"] == second_person
        assert kwargs["replay_ratio"] == replay_ratio
    ((arm, device, kwargs),) = calls["pin"]
    assert arm == "retrain" and device == "cpu"
    assert kwargs["adapter_path"] == tp.arm_outputs("probe36_m2_a", prefix="probe36")["adapter"]
    assert kwargs["record_path"] == probe.arm_record_path("e2", 1)
    assert not probe.arm_record_path("e2", 1).exists()  # the draws are discarded
    assert (tmp_path / "checkpoints" / "fixture_adapter.pt").read_bytes() == adapter_before
    passed = out["a2_pass"]
    assert passed["draws"] == 6 == len(passed["draw_seconds"]) and passed["draws_per_question"] == 3
    assert all(type(s) is float for s in passed["draw_seconds"])
    assert passed["fixed_seconds"] == pytest.approx(
        passed["total_seconds"] - sum(passed["draw_seconds"])
    )
    assert passed["draw_seconds_spread"]["n"] == 6
    assert len(out["train_reps"]) == 2
    config = out["configuration"]
    real_facts = tp.arm_spec("real")[0]
    assert config["n_facts_real"] == len(real_facts) == config["n_facts_m2"] + 1
    assert (config["target_slot"], config["K"], config["questions"]) == (target.slot, 3, 2)
    assert config["steps"] == tp.MAX_STEPS and config["seed"] == 1337
    assert out["reused"] == {"e2": False} and state["stage"] == "e2_a2_pass"
    run = {"front": "e2", "run_id": "v6/36/probes/e2", "reused": out.pop("reused"), "stages": out}
    record = probe.build_record("e2", run)
    assert set(record["stages"]) == {"train_reps", "a2_pass"} and record["repetitions"] == 2
    assert "reading" not in set(_keys(record)) and "SENTINEL" not in json.dumps(record)
    assert probe._e2_stages(out) == (record["stages"], 2)
    out["train_reps"].pop()
    with pytest.raises(SystemExit, match="not 2"):
        probe._e2_stages(out)


def test_stage_e2_refuses_a_short_pass_a_stale_record_and_a_changed_adapter(tmp_path, monkeypatch):
    _e2_light(tmp_path, monkeypatch, draws=5)
    with pytest.raises(SystemExit, match="draw timer counted 5"):
        probe.stage_e2({})
    assert not probe.arm_record_path("e2", 1).exists()
    calls = _e2_light(tmp_path / "stale", monkeypatch)
    stale = probe.arm_record_path("e2", 1)
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="stale probe output"):
        probe.stage_e2({})
    assert calls["teach"] == []  # refused before any training
    _e2_light(tmp_path / "tamper", monkeypatch, on_pin=lambda a: a.write_bytes(b"changed"))
    with pytest.raises(SystemExit, match="T-36-19"):
        probe.stage_e2({})


def test_e2_driver_and_pin_calls_are_unbound_and_silenced():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    driver = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "train_arm"
    ]
    assert len(driver) == 1  # the one registered call site (tests/test_phase23_resume.py)
    (call,), parents = _stage_calls("train_e2_rep", "train_arm")
    assert isinstance(parents[call], ast.Expr) and call.args[0].id == "arm"
    assert {"silenced()", "loop_timer(tp)"} <= set(_with_items(call, parents))
    assert not [k for k in call.keywords if k.arg == "resume_from"]
    (pin,), parents = _stage_calls("stage_e2", "run_erasure_arm")
    assert isinstance(parents[pin], ast.Expr) and pin.args[0].value == "retrain"
    assert {"silenced()", "DrawTimer()"} <= set(_with_items(pin, parents))


@pytest.fixture(scope="module")
def e2_live(tmp_path_factory):
    return _live_run(tmp_path_factory.mktemp("e2_live"), ("e2",))


def test_live_e2_trains_two_reps_and_runs_one_a2_pass(e2_live):
    root = e2_live["root"]
    (call,) = e2_live["spies"]["pin_calls"]
    assert call["arm"] == "retrain" and call["device"] == "cpu"
    assert not pathlib.Path(call["record_path"]).exists()
    for arm in probe.E2_ARMS:
        assert (root / "data" / "probe36_e2" / arm / "run.csv").exists()
        assert (root / "checkpoints" / f"probe36_{arm}_adapter.pt").exists()
    stages = e2_live["records"]["e2"]["stages"]
    assert len(stages["train_reps"]) == 2
    for rep in stages["train_reps"]:
        assert 0 < rep["loop_seconds"] < rep["outer_seconds"]
    assert stages["a2_pass"]["draws"] == LIVE_DRAWS == len(stages["a2_pass"]["draw_seconds"])
    assert stages["a2_pass"]["draws_per_question"] == LIVE_K
    config = e2_live["records"]["e2"]["configuration"]
    assert config["n_facts_m2"] == config["n_facts_real"] - 1


def test_live_e2_record_passes_the_gate_with_provenance(e2_live):
    record = e2_live["records"]["e2"]
    probe.prove_no_reading(record)
    assert record["provenance"]["run"]["device"] == "cpu" and record["repetitions"] == 2
    assert e2_live["sidecars"]["e2"]["reused"] == {"e2": False}
    text = e2_live["stdout"]
    assert re.search(r"^\[phase36_probe\] e2 \d+\.\d s$", text, re.MULTILINE), text
    assert "per_fact" not in text and not re.search(r"\d+/\d+ = ", text), text


def test_live_e2_never_touches_published_adapters(e2_live):
    root = e2_live["root"]
    assert not any((root / "results").iterdir())  # WR-01: both csvs moved under data/
    assert not list((root / "checkpoints").glob("phase19_*"))
    assert not (root / "checkpoints" / "persona_adapter.pt").exists()
    fixture = root / "checkpoints" / "fixture_adapter.pt"
    assert fixture.read_bytes() == b"fixture adapter bytes"
    hashed = e2_live["spies"]["hashed"]
    assert fixture in hashed  # non-vacuous: the before/after identity check ran
    assert not [p for p in hashed if p.is_relative_to(probe._GIT_ROOT / "checkpoints")]
    before, after = e2_live["strays"]
    assert before == after


# =================================================================================================
# Plan 36-05 Task 3 — preflight (T-36-24, W3) and the main(['run']) dispatch (Pitfall 9)
# =================================================================================================


def _preflight_env(tmp_path, monkeypatch):
    """A tmp tree with every input preflight checks; the device string is "mps" (never touched).

    B1: every gitignored input — persona_adapter.pt included — is a tmp fixture file, and the
    published sha is the fixture's; the committed JSON inputs are the real tracked files."""
    import phase14_recall
    import phase19_erasure
    import phase25_points
    import teach_persona as tp

    root = tmp_path / "tree"
    for module in (probe, phase25_points, phase36_ledger):
        monkeypatch.setattr(module, "_ROOT", root)
    monkeypatch.setattr(tp, "_REPO_ROOT", root)
    monkeypatch.setattr(phase25_run, "_DEVICE", "mps")  # a string; nothing here builds a device
    monkeypatch.setattr(phase25_run, "disk_precheck", lambda target=None: None)
    inputs = {
        (phase14_recall, "ADAPTER_PATH"): "persona_adapter.pt",
        (phase14_recall, "CONVBASE_SLIM"): "convbase_slim.pt",
        (phase19_erasure, "RETENTION_BIN"): "retention_val.bin",
        (phase19_erasure, "PHASE18_CORPUS_PATH"): "phase18_corpus.json",
        (phase19_erasure, "PHASE18_ARM_RECORD_PATH"): "phase18_arm_adapter-on.json",
        (tp, "CONVBASE_BEST"): "convbase_best.pt",
        (tp, "FACTSET_REPORT"): "factset.md",
        (tp, "DIALOG_TRAIN_BIN"): "dialog_train.bin",
        (tp, "DIALOG_TRAIN_MASK"): "dialog_train_mask.bin",
        (tp, "DIALOG_VAL_BIN"): "dialog_val.bin",
        (tp, "DIALOG_VAL_MASK"): "dialog_val_mask.bin",
    }
    for (module, name), filename in inputs.items():
        path = tmp_path / "inputs" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(filename.encode())
        monkeypatch.setattr(module, name, path)
    sha = hashlib.sha256(b"persona_adapter.pt").hexdigest()
    monkeypatch.setattr(probe, "published_adapter_sha256", lambda: sha)
    (root / "data").mkdir(parents=True)
    return root, inputs


def _listing(root):
    return sorted((p.relative_to(root).as_posix(), p.stat().st_mtime_ns) for p in root.rglob("*"))


def _plant(root, *relatives):
    for rel in relatives:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")


def test_preflight_passes_on_a_clean_tree_and_writes_nothing(
    tmp_path, monkeypatch, capsys, clean_tree
):
    root, _inputs = _preflight_env(tmp_path, monkeypatch)
    before = _listing(tmp_path)
    probe.preflight()
    assert _listing(tmp_path) == before
    out = capsys.readouterr().out
    assert f"PREFLIGHT OK {_head()} fronts=e5,e6,e3,e2,e1" in out, out
    (call,) = clean_tree
    assert call["pathspec"] == ("scripts", "src", "results") and call["cwd"] == probe._GIT_ROOT


def test_preflight_refuses_a_non_mps_device_and_a_dirty_tree(tmp_path, monkeypatch, clean_tree):
    _preflight_env(tmp_path, monkeypatch)
    monkeypatch.setattr(phase25_run, "_DEVICE", "cpu")
    with pytest.raises(SystemExit, match="not 'mps'"):
        probe.preflight()
    assert clean_tree == []  # refused before the dirty check
    monkeypatch.setattr(phase25_run, "_DEVICE", "mps")

    def dirty(**kwargs):
        raise SystemExit("[provenance] the tree is dirty")

    monkeypatch.setattr(probe, "refuse_if_dirty", dirty)
    with pytest.raises(SystemExit, match="dirty"):
        probe.preflight()


def test_preflight_refuses_an_open_ledger_run_until_reconcile(tmp_path, monkeypatch, capsys):
    root, _inputs = _preflight_env(tmp_path, monkeypatch)
    ledger = root / phase36_ledger.LEDGER_PATH
    rid = phase36_ledger.run_id(36, "probes", "e3")
    phase36_ledger.append("start", run_id=rid, phase=36, front="probes", ledger_path=ledger)
    with pytest.raises(SystemExit, match="phase36_ledger.py reconcile"):
        probe.preflight()
    # W3 / B1: reconcile closes even an attempt with no beat after its start, so it never sticks.
    phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=tmp_path / "hb.jsonl")
    probe.preflight()
    assert "PREFLIGHT OK" in capsys.readouterr().out


@pytest.mark.parametrize("index", range(11))
def test_preflight_refuses_a_missing_input(tmp_path, monkeypatch, index):
    _root, inputs = _preflight_env(tmp_path, monkeypatch)
    module, name = list(inputs)[index]
    monkeypatch.setattr(module, name, tmp_path / "absent" / name)
    with pytest.raises(SystemExit, match="missing"):
        probe.preflight()


def test_preflight_refuses_a_missing_committed_input_and_the_wrong_adapter(tmp_path, monkeypatch):
    _preflight_env(tmp_path, monkeypatch)
    real = probe.CURVE_RECORD
    monkeypatch.setattr(probe, "CURVE_RECORD", "results/phase36_never_written_curve.json")
    with pytest.raises(SystemExit, match="phase36_never_written_curve"):
        probe.preflight()
    monkeypatch.setattr(probe, "CURVE_RECORD", real)
    monkeypatch.setattr(probe, "published_adapter_sha256", lambda: "0" * 64)
    with pytest.raises(SystemExit, match="adapter_in_sha256"):
        probe.preflight()


def test_preflight_refuses_an_unregistered_or_extra_front(tmp_path, monkeypatch):
    _preflight_env(tmp_path, monkeypatch)
    monkeypatch.delitem(probe.STAGES, "e3")
    with pytest.raises(SystemExit, match=r"\['e3'\]"):
        probe.preflight()
    monkeypatch.setitem(probe.STAGES, "e3", probe.stage_e3)
    monkeypatch.setitem(probe.STAGES, "e4", _fake_stage)
    with pytest.raises(SystemExit, match=r"\['e4'\]"):
        probe.preflight()


@pytest.mark.parametrize(
    "stray",
    [
        "data/probe36_e1_rep1_arm.json",
        "data/probe36_e2/probe36_m2_a/run.csv",
        "checkpoints/probe36_t200_dp_n8_latest.pt",
        "data/phase25_probe36_e3_t800_training.json",
        "data/persona_probe36_m2_b_train.bin",
        "results/probe36_probe36_m2_a/run.csv",
    ],
)
def test_preflight_refuses_a_stale_probe_output(tmp_path, monkeypatch, capsys, stray):
    root, _inputs = _preflight_env(tmp_path, monkeypatch)
    _plant(root, *(f"data/probe36_{f}_sessions.json" for f in probe.RUN_ORDER))
    probe.preflight()  # session sidecars alone are never strays
    assert "PREFLIGHT OK" in capsys.readouterr().out
    _plant(root, stray)
    with pytest.raises(SystemExit, match="stale probe output") as refused:
        probe.preflight()
    assert stray.split("/")[1] in str(refused.value)


def _e2_e3_outputs():
    """One file per front-specific output name of E2 and E3, repo-relative, by front."""
    e2 = ["data/probe36_e2/probe36_m2_a/run.csv"]
    for arm in probe.E2_ARMS:
        e2 += [f"data/persona_{arm}_train.bin", f"data/persona_{arm}_train_mask.bin"]
        e2 += [f"checkpoints/probe36_{arm}_adapter.pt", f"checkpoints/probe36_{arm}_latest.pt"]
    e3 = []
    for steps in probe.e3_steps():
        e3 += [f"data/phase25_probe36_e3_t{steps}_training.json"]
        e3 += [f"checkpoints/probe36_t{steps}_dp_n8_{kind}.pt" for kind in ("adapter", "latest")]
    return {"e2": e2, "e3": e3}


def test_front_outputs_attribute_every_stray_glob_match_to_exactly_one_front(tmp_path, monkeypatch):
    root, _inputs = _preflight_env(tmp_path, monkeypatch)
    rels = [f"data/probe36_{f}_{name}" for f in probe.RUN_ORDER for name in ("run.json", "x.json")]
    outputs = _e2_e3_outputs()
    _plant(root, *rels, *outputs["e2"], *outputs["e3"])
    owned = {front: probe.front_outputs(front) for front in probe.RUN_ORDER}
    matched = sorted({p for pattern in probe.STRAY_GLOBS for p in root.glob(pattern)})
    assert len(matched) >= len(rels)  # non-vacuous: every planted name is under a stray glob
    for path in matched:
        owners = [front for front, paths in owned.items() if path in paths]
        assert len(owners) == 1, (path, owners)
    with pytest.raises(SystemExit, match="not a probe front"):
        probe.front_outputs("e4")


def test_preflight_relaunch_keeps_finished_fronts_and_refuses_the_crashed_one(
    tmp_path, monkeypatch, capsys
):
    """W3: e5, e6 and e3 finished; e2 crashed mid-training (its run sidecar never written)."""
    root, _inputs = _preflight_env(tmp_path, monkeypatch)
    finished = [f"data/probe36_{f}_run.json" for f in ("e5", "e6", "e3")]
    e3 = _e2_e3_outputs()["e3"]
    _plant(root, *finished, *e3, *(f"data/probe36_{f}_sessions.json" for f in probe.RUN_ORDER))
    partial = [
        "checkpoints/probe36_probe36_m2_a_adapter.pt",
        "checkpoints/probe36_probe36_m2_a_latest.pt",
        "data/persona_probe36_m2_a_train.bin",
    ]
    _plant(root, *partial, "results/probe36_probe36_m2_a/run.csv")
    with pytest.raises(SystemExit, match="stale probe output") as refused:
        probe.preflight()
    for rel in partial:
        assert rel in str(refused.value)
    assert not [rel for rel in e3 if rel in str(refused.value)]  # e3 finished: its outputs stay
    for rel in partial:
        (root / rel).unlink()
    with pytest.raises(SystemExit, match="results/probe36_probe36_m2_a"):
        probe.preflight()  # results/probe36_* belongs to no front and always refuses
    (root / "results/probe36_probe36_m2_a/run.csv").unlink()
    (root / "results/probe36_probe36_m2_a").rmdir()
    probe.preflight()
    assert "PREFLIGHT OK" in capsys.readouterr().out
    assert all((root / rel).exists() for rel in finished + e3)


def test_main_run_defaults(monkeypatch):
    calls = []
    signature = inspect.signature(probe.run_front)

    def recorder(*args, **kwargs):
        signature.bind(*args, **kwargs)  # run_all's kwargs must fit the REAL run_front
        calls.append((args, kwargs))

    monkeypatch.setattr(probe, "run_front", recorder)
    monkeypatch.setattr(phase25_run, "disk_precheck", lambda target=None: None)
    assert probe.main(["run"]) == 0
    defaults = {
        "heartbeat_path": phase36_ledger.HEARTBEAT_PATH,
        "ledger_path": probe._GIT_ROOT / phase36_ledger.LEDGER_PATH,
    }
    assert calls == [((front,), defaults) for front in probe.RUN_ORDER]


def test_main_run_dispatches_every_front(tmp_path):
    """Pitfall 9: main(['run']) with no --front reaches every REAL stage in RUN_ORDER on CPU —
    each STAGES entry wrapped by a recorder that binds (state,) against the real stage and
    forwards to it — then the REAL emit of all five records."""
    assert all(probe.STAGES[f] is getattr(probe, f"stage_{f}") for f in probe.RUN_ORDER)
    live = _live_run(tmp_path / "all", None, wrap_stages=True)
    assert live["spies"]["stages"] == list(probe.RUN_ORDER)
    assert len(live["sidecars"]) == len(probe.RUN_ORDER)
    lines = phase36_ledger.read_ledger(live["ledger"])
    assert len(lines) == 2 * len(probe.RUN_ORDER)
    assert [x["event"] for x in lines] == ["start", "end"] * len(probe.RUN_ORDER)
    for front in probe.RUN_ORDER:
        assert re.search(rf"^\[phase36_probe\] {front} \d+\.\d s$", live["stdout"], re.MULTILINE)
        record = live["records"][front]
        probe.prove_no_reading(record)
        assert record["reused"] == {front: False}
    # E6's beside is the E1 probe that ran here, not a planted sidecar.
    runs = live["sidecars"]["e1"]["stages"]["runs"]
    high = max(sum(r["per_question_k48_seconds"]) / LIVE_QUESTIONS for r in runs)
    beside = live["records"]["e6"]["a2_context_from_e1"]
    assert beside["a2_context_question_k48_seconds_high"] == pytest.approx(high)
    assert [c["arm"] for c in live["spies"]["pin_calls"]] == ["retrain", "erased", "erased"]
    assert not any((live["root"] / "results").iterdir())
    before, after = live["strays"]
    assert before == after
    hashed = live["spies"]["hashed"]
    assert not [p for p in hashed if p.is_relative_to(probe._GIT_ROOT / "checkpoints")]
