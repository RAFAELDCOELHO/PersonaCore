"""Plan 36-02 Task 2: the v6.0 MPS ledger (scripts/phase36_ledger.py), CPU-only.

What this file proves:
- append writes one sort_keys JSON line per event and refuses every malformed transition; a lost
  line closes its attempt, so a relaunch of the same run_id is accepted (W3);
- read_ledger tolerates a torn LAST line and refuses a torn middle one;
- reconcile closes every open attempt from the last heartbeat SINCE THAT ATTEMPT'S START, or at
  0 s with NO_BEAT_FLAG when there is none, and never raises (B1);
- spent counts record provenance, pending end lines and lost lines, refuses while an in-scope
  attempt is open, and never reads the run log or its wall_clock column (AST gate);
- report lists open attempts without refusing (W7c);
- require_launch refuses a cut front (W1) and pauses at D-13 (a), (b), (c); only a matching ruling
  lifts exactly that stop for exactly that front's next launch (W5);
- require_e4_first_point refuses a D-19 divergence; the real ledger is append-only and names every
  probe record; every function has a CPU test; the module imports without torch.

Every ledger and heartbeat here is under tmp_path.
"""

import ast
import datetime
import json
import math
import pathlib
import subprocess
import sys
import types

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
import phase30_points  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)

from test_phase36_caps import _budget  # noqa: E402
from test_phase36_prereg import _untested_functions  # noqa: E402

LEDGER = "scripts/phase36_ledger.py"
T0 = datetime.datetime(2026, 10, 2, 12, 0, tzinfo=datetime.timezone.utc)
PROBE_E1 = phase36_prereg.probe_record("e1")


def _at(seconds):
    return T0 + datetime.timedelta(seconds=seconds)


@pytest.fixture
def clock(monkeypatch):
    """``phase36_ledger._utc_now`` patched to a settable instant."""
    now = types.SimpleNamespace(value=T0)
    monkeypatch.setattr(phase36_ledger, "_utc_now", lambda: now.value)
    return now


@pytest.fixture
def ledger(tmp_path):
    return tmp_path / "ledger" / "v6_mps_ledger.jsonl"


@pytest.fixture
def beats(tmp_path):
    return tmp_path / "data" / "v6_mps_heartbeat.jsonl"


def _beat(path, point, when):
    """A beat with a planted utc, in the phase25_run.HEARTBEAT_FIELDS shape."""
    line = dict.fromkeys(phase25_run.HEARTBEAT_FIELDS)
    line.update(utc=when.isoformat(), point=point, stage="train")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, sort_keys=True) + "\n")


def _start(front, unit, ledger, phase=36):
    rid = phase36_ledger.run_id(phase, front, unit)
    phase36_ledger.append("start", run_id=rid, phase=phase, front=front, ledger_path=ledger)
    return rid


def _spend(ledger, front, hours, unit=None):
    """One closed attempt on `front` costing `hours` (a lost line with those seconds)."""
    rid = _start(front, unit or f"spend{len(phase36_ledger.read_ledger(ledger))}", ledger)
    phase36_ledger.append(
        "lost",
        run_id=rid,
        phase=36,
        front=front,
        seconds=hours * 3600,
        flag=phase36_ledger.LOST_FLAG,
        ledger_path=ledger,
    )
    return rid


def _plan(front_hours, stop_line=None):
    total = math.fsum(front_hours.values())
    stop = min(1.5 * total, 90) if stop_line is None else stop_line
    return phase36_caps.prove_budget_shape(
        _budget(front_hours=dict(front_hours), total_hours=total, stop_line_hours=stop)
    )


_HOURS = dict(_budget()["front_hours"])  # total 49.0 h, stop line 73.5 h


@pytest.fixture
def planted(monkeypatch):
    """Route committed_budget to a settable planted budget."""
    state = types.SimpleNamespace(budget=_plan(_HOURS))
    monkeypatch.setattr(phase36_caps, "committed_budget", lambda tracked=None: state.budget)
    return state


# =================================================================================================
# (1) THE NAMES AND THE PATHS (Q3).
# =================================================================================================


def test_names_and_paths():
    assert phase36_ledger.LEDGER_PATH == "ledger/v6_mps_ledger.jsonl"
    assert phase36_ledger.HEARTBEAT_PATH == _ROOT / "data" / "v6_mps_heartbeat.jsonl"
    assert phase36_ledger.EVENTS == ("start", "end", "lost", "ruling")
    assert phase36_ledger.STOPS == ("a", "b", "c")
    assert phase36_ledger.LOST_FLAG == "sem registro de resultado"
    assert phase36_ledger.NO_BEAT_FLAG.startswith(phase36_ledger.LOST_FLAG)
    assert phase36_ledger.RECORD_CLOCK == ("provenance", "run")
    assert set(phase36_ledger.LINE_FIELDS) >= {"utc", "event", "run_id", "front", "seconds"}
    assert phase36_ledger.run_id(41, "E1", "cell0") == "v6/41/E1/cell0"
    now = phase36_ledger._utc_now()
    assert now.tzinfo is not None and now.utcoffset() == datetime.timedelta(0)
    with pytest.raises(SystemExit, match=r"^\[phase36_ledger\] x$"):
        phase36_ledger._prove(False, "x")
    # The ledger is committed; the raw beats are gitignored (Q3).
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", phase36_ledger.LEDGER_PATH], cwd=_ROOT, check=False
    )
    assert ignored.returncode == 1
    beats = subprocess.run(
        ["git", "check-ignore", "-q", "data/v6_mps_heartbeat.jsonl"], cwd=_ROOT, check=False
    )
    assert beats.returncode == 0


# =================================================================================================
# (2) APPEND AND READ (D-11, W3).
# =================================================================================================


def test_append_writes_sort_keys_lines(clock, ledger):
    rid = _start("probes", "e1", ledger)
    clock.value = _at(60)
    end = phase36_ledger.append(
        "end", run_id=rid, phase=36, front="probes", record=PROBE_E1, ledger_path=ledger
    )
    raw = ledger.read_text(encoding="utf-8").splitlines()
    assert len(raw) == 2
    for text in raw:
        line = json.loads(text)
        assert json.dumps(line, sort_keys=True) == text
        assert set(line) == set(phase36_ledger.LINE_FIELDS)
    assert json.loads(raw[1]) == end
    assert end["utc"] == _at(60).isoformat() and end["record"] == PROBE_E1
    assert [line["event"] for line in phase36_ledger.read_ledger(ledger)] == ["start", "end"]


def test_write_line_appends_only(ledger):
    line = dict.fromkeys(phase36_ledger.LINE_FIELDS)
    line.update(utc=T0.isoformat(), event="ruling", front="E1", stop="a", ruling="r", seconds=0.0)
    phase36_ledger._write_line(line, ledger)
    phase36_ledger._write_line(line, ledger)
    assert phase36_ledger.read_ledger(ledger) == [line, line]
    with pytest.raises(SystemExit, match="LINE_FIELDS"):
        phase36_ledger._write_line({"utc": "x"}, ledger)


@pytest.mark.parametrize(
    ("label", "pattern"),
    [
        ("start twice", "still open"),
        ("end without start", "no open attempt"),
        ("lost without start", "no open attempt"),
        ("unknown front", "V6_MPS_FRONTS"),
        ("unknown record", "V6_RESULT_PATHS"),
        ("ruling via append", "start, end or lost"),
        ("negative lost", "seconds"),
        ("bad flag", "flag"),
        ("front mismatch", "front"),
    ],
)
def test_append_refusals(clock, ledger, label, pattern):
    rid = _start("E1", "cell0", ledger)
    other = phase36_ledger.run_id(36, "E1", "other")
    calls = {
        "start twice": lambda: _start("E1", "cell0", ledger),
        "end without start": lambda: phase36_ledger.append(
            "end", run_id=other, phase=36, front="E1", record=PROBE_E1, ledger_path=ledger
        ),
        "lost without start": lambda: phase36_ledger.append(
            "lost",
            run_id=other,
            phase=36,
            front="E1",
            seconds=1.0,
            flag=phase36_ledger.LOST_FLAG,
            ledger_path=ledger,
        ),
        "unknown front": lambda: _start("E9", "x", ledger),
        "unknown record": lambda: phase36_ledger.append(
            "end", run_id=rid, phase=36, front="E1", record="results/x.json", ledger_path=ledger
        ),
        "ruling via append": lambda: phase36_ledger.append(
            "ruling", run_id=rid, phase=36, front="E1", ledger_path=ledger
        ),
        "negative lost": lambda: phase36_ledger.append(
            "lost",
            run_id=rid,
            phase=36,
            front="E1",
            seconds=-1.0,
            flag=phase36_ledger.LOST_FLAG,
            ledger_path=ledger,
        ),
        "bad flag": lambda: phase36_ledger.append(
            "lost", run_id=rid, phase=36, front="E1", seconds=1.0, flag="x", ledger_path=ledger
        ),
        "front mismatch": lambda: phase36_ledger.append(
            "end", run_id=rid, phase=36, front="E2", record=PROBE_E1, ledger_path=ledger
        ),
    }
    before = ledger.read_bytes()
    with pytest.raises(SystemExit, match=pattern):
        calls[label]()
    assert ledger.read_bytes() == before


def test_read_ledger_torn_tail(clock, ledger):
    assert phase36_ledger.read_ledger(ledger) == []
    _start("E1", "a", ledger)
    _start("E1", "b", ledger)
    good = ledger.read_bytes()
    ledger.write_bytes(good + b'{"event": "sta')
    assert len(phase36_ledger.read_ledger(ledger)) == 2
    with pytest.raises(SystemExit, match="torn"):  # appending onto a torn tail is refused
        _start("E1", "c", ledger)
    first, second = good.splitlines(keepends=True)
    ledger.write_bytes(first + b'{"event": "sta\n' + second)
    with pytest.raises(SystemExit, match="line 2"):
        phase36_ledger.read_ledger(ledger)
    ledger.write_bytes(first + b'{"event": "bogus"}\n')
    with pytest.raises(SystemExit, match="bogus"):
        phase36_ledger.read_ledger(ledger)


def test_attempts_and_open_runs(clock, ledger):
    rid = _start("E1", "a", ledger)
    lines = phase36_ledger.read_ledger(ledger)
    assert phase36_ledger._attempts(lines) == [(lines[0], None)]
    assert phase36_ledger.open_runs(lines) == {rid: lines[0]}
    phase36_ledger.append(
        "lost", run_id=rid, phase=36, front="E1", seconds=0.0, flag=phase36_ledger.NO_BEAT_FLAG,
        ledger_path=ledger,
    )  # fmt: skip
    lines = phase36_ledger.read_ledger(ledger)
    assert phase36_ledger._attempts(lines) == [(lines[0], lines[1])]
    assert phase36_ledger.open_runs(lines) == {}
    with pytest.raises(SystemExit, match="no open attempt"):
        phase36_ledger._attempts(lines + [lines[1]])
    with pytest.raises(SystemExit, match="still open"):
        phase36_ledger._attempts([lines[0], lines[0]])


# =================================================================================================
# (3) HEARTBEATS AND RECONCILE (D-12, B1).
# =================================================================================================


def test_last_beat_since(beats):
    rid = phase36_ledger.run_id(36, "E1", "a")
    assert phase36_ledger.last_beat_since(rid, T0, beats) is None  # absent file
    _beat(beats, rid, _at(-50))  # before the attempt: never used
    _beat(beats, rid, _at(30))
    _beat(beats, "v6/36/E2/x", _at(90))  # another run interleaved
    _beat(beats, rid, _at(60))
    # The real writer's beats are read too (phase25_run.beat stamps the real clock).
    before = phase36_ledger._utc_now() - datetime.timedelta(seconds=1)
    phase25_run.beat(beats, point="v6/36/E3/live", stage="train", shape=None, draw_index=None)
    found = phase36_ledger.last_beat_since("v6/36/E3/live", before, beats)
    assert found is not None and found >= before
    with beats.open("a", encoding="utf-8") as handle:
        handle.write('{"utc": "2026')  # torn tail (a beat appended after it would merge into it)
    assert phase36_ledger.last_beat_since(rid, T0, beats) == _at(60)
    assert phase36_ledger.last_beat_since(rid, _at(61), beats) is None


def test_reconcile_no_beat_closes_at_zero(clock, ledger, beats):
    rid = _start("E1", "a", ledger)
    with pytest.raises(SystemExit, match="still open"):
        phase36_ledger.spent([], ledger_path=ledger)
    clock.value = _at(500)
    (lost,) = phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=beats)
    assert lost["event"] == "lost" and lost["run_id"] == rid and lost["front"] == "E1"
    assert lost["seconds"] == 0 and lost["flag"] == phase36_ledger.NO_BEAT_FLAG
    assert phase36_ledger.open_runs(phase36_ledger.read_ledger(ledger)) == {}
    assert phase36_ledger.spent([], ledger_path=ledger)["by_front"]["E1"] == 0
    assert phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=beats) == []


def test_reconcile_second_attempt_never_inherits_the_first_beat(clock, ledger, beats):
    rid = _start("E1", "a", ledger)
    _beat(beats, rid, _at(100))
    clock.value = _at(200)
    (first,) = phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=beats)
    assert first["seconds"] == 100 and first["flag"] == phase36_ledger.LOST_FLAG
    assert first["flag"] == "sem registro de resultado"
    clock.value = _at(500)  # t1 > t0 + 100 s
    assert _start("E1", "a", ledger) == rid
    clock.value = _at(900)
    (second,) = phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=beats)
    assert second["seconds"] == 0 and second["flag"] == phase36_ledger.NO_BEAT_FLAG
    lost = [x for x in phase36_ledger.read_ledger(ledger) if x["event"] == "lost"]
    assert len(lost) == 2 and all(x["seconds"] >= 0 for x in lost)


def test_reconcile_second_attempt_with_its_own_beat(clock, ledger, beats):
    rid = _start("E1", "a", ledger)
    _beat(beats, rid, _at(100))
    clock.value = _at(200)
    phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=beats)
    clock.value = _at(500)
    _start("E1", "a", ledger)
    _beat(beats, rid, _at(540))
    clock.value = _at(900)
    (second,) = phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=beats)
    assert second["seconds"] == 40 and second["flag"] == phase36_ledger.LOST_FLAG
    assert all(
        x["seconds"] >= 0 for x in phase36_ledger.read_ledger(ledger) if x["event"] == "lost"
    )


def _provenance(started, finished, device="mps"):
    run = {"started_utc": started.isoformat(), "finished_utc": finished.isoformat()}
    return {"provenance": {"run": {**run, "device": device}}}


def test_relaunch_after_a_lost_attempt(clock, ledger, beats, monkeypatch):
    rid = _start("E1", "a", ledger)
    _beat(beats, rid, _at(100))
    clock.value = _at(200)
    phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=beats)
    clock.value = _at(300)
    _start("E1", "a", ledger)  # W3: the lost line closed attempt 1
    clock.value = _at(900)
    phase36_ledger.append(
        "end", run_id=rid, phase=36, front="E1", record=PROBE_E1, ledger_path=ledger
    )
    record = _provenance(_at(300), _at(850))
    monkeypatch.setattr(phase30_points, "_tracked_json", lambda rel, tracked, what: record)
    totals = phase36_ledger.spent([PROBE_E1], ledger_path=ledger)
    assert totals["by_front"]["E1"] == 650.0  # 100 s lost + 550 s from provenance.run
    assert [row["event"] for row in totals["rows"]] == ["lost", "end"]
    rows = phase36_ledger.report_rows([PROBE_E1], ledger_path=ledger, heartbeat_path=beats)["rows"]
    assert [(r["run_id"], r["status"]) for r in rows] == [(rid, "closed"), (rid, "closed")]


# =================================================================================================
# (4) SPENT AND REPORT (D-11, W2, W7c, T-36-07).
# =================================================================================================


def test_spent_sources(clock, ledger, monkeypatch):
    tracked_rid = _start("probes", "e1", ledger)
    clock.value = _at(1000)
    phase36_ledger.append(
        "end", run_id=tracked_rid, phase=36, front="probes", record=PROBE_E1, ledger_path=ledger
    )
    pending_rid = _start("probes", "e2", ledger)
    clock.value = _at(1300)
    phase36_ledger.append(
        "end",
        run_id=pending_rid,
        phase=36,
        front="probes",
        record=phase36_prereg.probe_record("e2"),
        ledger_path=ledger,
    )
    _spend(ledger, "E5", 0.5)
    record = _provenance(_at(10), _at(910))
    monkeypatch.setattr(phase30_points, "_tracked_json", lambda rel, tracked, what: record)
    totals = phase36_ledger.spent([PROBE_E1], ledger_path=ledger)
    rows = {row["run_id"]: row for row in totals["rows"]}
    assert rows[tracked_rid]["seconds"] == 900.0 and rows[tracked_rid]["flag"] is None
    assert rows[pending_rid]["seconds"] == 300.0
    assert rows[pending_rid]["flag"] == phase36_ledger.PENDING_FLAG
    assert totals["by_front"]["probes"] == 1200.0 and totals["by_front"]["E5"] == 1800.0
    assert totals["total_seconds"] == 3000.0
    assert set(totals["by_front"]) == set(phase35_prereg.V6_MPS_FRONTS)

    # W2: a scoped call counts only its fronts and refuses only on their open attempts.
    _start("E1", "open", ledger)
    with pytest.raises(SystemExit, match="still open"):
        phase36_ledger.spent([PROBE_E1], ledger_path=ledger)
    probes = phase36_ledger.spent([PROBE_E1], ledger_path=ledger, fronts=("probes",))
    assert probes["by_front"] == {"probes": 1200.0} and probes["total_seconds"] == 1200.0
    with pytest.raises(SystemExit, match="V6_MPS_FRONTS"):
        phase36_ledger.spent([], ledger_path=ledger, fronts=("bogus",))


def test_closed_row_sources(clock, ledger, monkeypatch):
    rid = _start("E2", "a", ledger)
    clock.value = _at(70)
    phase36_ledger.append(
        "end", run_id=rid, phase=36, front="E2", record=PROBE_E1, ledger_path=ledger
    )
    start, end = phase36_ledger.read_ledger(ledger)
    row = phase36_ledger._closed_row(start, end, [])
    assert row["seconds"] == 70.0 and row["flag"] == phase36_ledger.PENDING_FLAG
    monkeypatch.setattr(
        phase30_points, "_tracked_json", lambda rel, tracked, what: {"provenance": {}}
    )
    with pytest.raises(SystemExit, match="provenance.run"):
        phase36_ledger._closed_row(start, end, [PROBE_E1])


def test_spent_counts_a_superseded_end_line_by_its_own_span(clock, ledger, monkeypatch):
    """CR-01: a re-probe writes a second end line naming the same record. The earlier attempt's
    hours were really spent (D-12): counted once by its own ledger span; only the LAST end line is
    counted by the record's provenance.run clock. Never refused, never double counted."""
    for began, ended in ((0, 1000), (2000, 3000)):
        clock.value = _at(began)
        rid = _start("probes", "e1", ledger)
        clock.value = _at(ended)
        phase36_ledger.append(
            "end", run_id=rid, phase=36, front="probes", record=PROBE_E1, ledger_path=ledger
        )
    record = _provenance(_at(2010), _at(2910))
    monkeypatch.setattr(phase30_points, "_tracked_json", lambda rel, tracked, what: record)
    totals = phase36_ledger.spent([PROBE_E1], ledger_path=ledger, fronts=("probes",))
    assert totals["by_front"]["probes"] == 1000.0 + 900.0
    first, last = totals["rows"]
    assert first["seconds"] == 1000.0 and first["flag"] == phase36_ledger.SUPERSEDED_FLAG
    assert last["seconds"] == 900.0 and last["flag"] is None
    report = phase36_ledger.report_rows([PROBE_E1], ledger_path=ledger, heartbeat_path=ledger)
    assert report["rows"] == totals["rows"] and report["by_front"]["probes"] == 1900.0
    attempts = phase36_ledger._attempts(phase36_ledger.read_ledger(ledger))
    assert phase36_ledger._superseded(attempts) == {0}
    assert phase36_ledger._superseded(attempts[1:]) == set()


def test_report_lists_open_attempts_without_refusing(clock, ledger, beats, monkeypatch, capsys):
    _spend(ledger, "E5", 0.25)
    clock.value = _at(100)
    rid = _start("E1", "live", ledger)
    _beat(beats, rid, _at(160))
    quiet = _start("E2", "quiet", ledger)
    with pytest.raises(SystemExit, match="still open"):
        phase36_ledger.spent([], ledger_path=ledger)
    report = phase36_ledger.report_rows([], ledger_path=ledger, heartbeat_path=beats)
    status = {row["run_id"]: (row["status"], row["seconds"]) for row in report["rows"]}
    assert status[rid] == ("open", 60.0)
    assert status[quiet] == ("open", None)
    assert report["by_front"]["E1"] == 0 and report["by_front"]["E5"] == 900.0

    monkeypatch.setattr(phase36_ledger, "LEDGER_PATH", str(ledger))
    monkeypatch.setattr(phase36_ledger, "HEARTBEAT_PATH", beats)
    assert phase36_ledger.main(["report"]) == 0
    out = capsys.readouterr().out
    assert '"status": "open"' in out and rid in out


# =================================================================================================
# (5) D-13: THE THREE STOPS, THE CUT FRONT, THE RULINGS (W1, W5, T-36-09, T-36-39).
# =================================================================================================


def test_stop_checks_messages():
    budget = _plan(_HOURS)
    assert phase36_ledger.stop_checks(budget, {}) == {"a": None, "b": None, "c": None}
    checks = phase36_ledger.stop_checks(budget, {"E1": 16.0})
    assert checks["a"] and "stop (a)" in checks["a"] and "E1" in checks["a"]
    assert checks["b"] is None and checks["c"] is None
    full = {front: 1.5 * hours for front, hours in _HOURS.items()}
    checks = phase36_ledger.stop_checks(budget, full)
    assert checks["a"] is None and "stop (b)" in checks["b"] and checks["c"] is None
    cut = _plan({**_HOURS, "E6": 0.0})
    assert "E6" in phase36_ledger.stop_checks(cut, {"E6": 1 / 3600})["a"]  # W1: no 0-h exemption


_C_HOURS = {**_HOURS, "E1": 20.0, "E2": 16.0, "E3": 20.0, "E4": 10.0}  # total 80.0 h, stop 90


def _scenario(letter, planted, ledger):
    """Plant spent hours that trip exactly stop `letter`."""
    if letter == "a":
        _spend(ledger, "E1", 16.0)  # > 1.5 x 10
    elif letter == "b":
        for front, hours in _HOURS.items():
            _spend(ledger, front, 1.5 * hours)  # 73.5 h = the stop line, no front above 1.5x
    else:
        planted.budget = _plan(_C_HOURS)
        _spend(ledger, "E1", 30.0)
        _spend(ledger, "E2", 24.0)  # projection 98 h > 90, spent 54 h < 90
    checks = phase36_ledger.stop_checks(
        planted.budget,
        {f: s / 3600 for f, s in phase36_ledger.spent([], ledger_path=ledger)["by_front"].items()},
    )
    assert [k for k, v in checks.items() if v] == [letter]


def _refused(letter):
    return pytest.raises(SystemExit, match=rf"stop \({letter}\)[\s\S]*PAUSE")


@pytest.mark.parametrize("letter", ["a", "b", "c"])
def test_each_stop_pauses_and_only_its_ruling_lifts_it(clock, ledger, planted, letter):
    assert phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)["lifted"] == ()
    _scenario(letter, planted, ledger)
    with _refused(letter):  # RED: the stop trips
        phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)

    # Wrong front: a ruling for E3 does not lift E5's launch.
    phase36_ledger.rule("E3", letter, "Rafael: E3 may go", tracked=[], ledger_path=ledger)
    with _refused(letter):
        phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)
    # Wrong stop: a ruling line for another letter (planted: rule() refuses an untripped stop).
    other = next(s for s in phase36_ledger.STOPS if s != letter)
    with pytest.raises(SystemExit, match="not tripped"):
        phase36_ledger.rule("E5", other, "pre-authorised", tracked=[], ledger_path=ledger)
    seconds = phase36_ledger.spent([], ledger_path=ledger)["total_seconds"]
    line = dict.fromkeys(phase36_ledger.LINE_FIELDS)
    line.update(utc=T0.isoformat(), event="ruling", front="E5", stop=other, ruling="x")
    line["seconds"] = seconds
    phase36_ledger._write_line(line, ledger)
    with _refused(letter):
        phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)

    # The matching ruling lifts exactly that stop for E5.
    ruling = phase36_ledger.rule("E5", letter, "Rafael: go", tracked=[], ledger_path=ledger)
    assert ruling["ruling"] == "Rafael: go" and ruling["seconds"] == seconds
    lifted = phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)
    assert lifted["lifted"] == (letter,)

    # One ruling, one launch: E5 starts; its attempt is closed (0 s) before the re-check.
    _start("E5", "launched", ledger)
    phase36_ledger.reconcile(ledger_path=ledger, heartbeat_path=ledger.parent / "none.jsonl")
    assert phase36_ledger.spent([], ledger_path=ledger)["total_seconds"] == seconds
    with _refused(letter):
        phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)


def test_a_ruling_stops_lifting_once_the_numbers_move(clock, ledger, planted):
    _scenario("a", planted, ledger)
    phase36_ledger.rule("E5", "a", "Rafael: go", tracked=[], ledger_path=ledger)
    assert phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)["lifted"] == ("a",)
    _spend(ledger, "E3", 1.0)  # another front ran in between
    with _refused("a"):
        phase36_ledger.require_launch("E5", tracked=[], ledger_path=ledger)


def test_state_reads_budget_and_spent(clock, ledger, planted):
    _spend(ledger, "E1", 16.0)
    budget, totals, checks = phase36_ledger._state("E5", [], ledger)
    assert budget is planted.budget and totals["by_front"]["E1"] == 16.0 * 3600
    assert checks["a"] and checks["b"] is None and checks["c"] is None
    with pytest.raises(SystemExit, match="V6_MPS_FRONTS"):
        phase36_ledger._state("E9", [], ledger)


def test_lifted_reads_front_stop_seconds_and_the_last_start():
    start = {"event": "start", "front": "E5"}
    ruling = {"event": "ruling", "front": "E5", "stop": "a", "seconds": 7.0}
    assert phase36_ledger._lifted([ruling], "E5", "a", 7.0) is True
    assert phase36_ledger._lifted([start, ruling], "E5", "a", 7.0) is True
    assert phase36_ledger._lifted([ruling, start], "E5", "a", 7.0) is False
    assert phase36_ledger._lifted([ruling], "E5", "a", 7.5) is False
    assert phase36_ledger._lifted([ruling], "E5", "b", 7.0) is False
    assert phase36_ledger._lifted([ruling], "E3", "a", 7.0) is False


def test_a_cut_front_never_launches(clock, ledger, planted):
    planted.budget = _plan({**_HOURS, "E6": 0.0})
    with pytest.raises(SystemExit, match="a cut front never launches"):
        phase36_ledger.require_launch("E6", tracked=[], ledger_path=ledger)
    _spend(ledger, "E6", 1 / 3600)  # one second on the cut front trips (a) for every front
    with _refused("a"):
        phase36_ledger.require_launch("E1", tracked=[], ledger_path=ledger)
    with pytest.raises(SystemExit, match="cut front"):
        phase36_ledger.rule("E6", "a", "Rafael: go", tracked=[], ledger_path=ledger)
    phase36_ledger.rule("E1", "a", "Rafael: E1 may go", tracked=[], ledger_path=ledger)
    assert phase36_ledger.require_launch("E1", tracked=[], ledger_path=ledger)["lifted"] == ("a",)
    with pytest.raises(SystemExit, match="a cut front never launches"):
        phase36_ledger.require_launch("E6", tracked=[], ledger_path=ledger)


@pytest.mark.parametrize(
    ("args", "pattern"),
    [
        (("E9", "a", "t"), "V6_MPS_FRONTS"),
        (("E5", "d", "t"), "STOPS"),
        (("E5", "a", "  "), "empty"),
        (("E5", "a", 7), "empty"),
        (("E5", "a", "t"), "not tripped"),
    ],
)
def test_rule_refusals(clock, ledger, planted, args, pattern):
    with pytest.raises(SystemExit, match=pattern):
        phase36_ledger.rule(*args, tracked=[], ledger_path=ledger)
    assert phase36_ledger.read_ledger(ledger) == []


def test_main_rule_and_reconcile(clock, ledger, planted, monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(phase36_ledger, "LEDGER_PATH", str(ledger))
    monkeypatch.setattr(phase36_ledger, "HEARTBEAT_PATH", tmp_path / "none.jsonl")
    _spend(ledger, "E1", 16.0)
    _start("E2", "dead", ledger)
    assert phase36_ledger.main(["reconcile"]) == 0
    assert phase36_ledger.NO_BEAT_FLAG in capsys.readouterr().out
    assert phase36_ledger.main(["rule", "--front", "E5", "--stop", "a", "--text", "go"]) == 0
    assert '"ruling": "go"' in capsys.readouterr().out


def test_require_e4_first_point(planted):
    price = planted.budget["unit_prices"]["e4_point_seconds"]
    assert phase36_ledger.require_e4_first_point(price * 1.25, tracked=[]) == 0.25
    with pytest.raises(SystemExit, match="D-19"):
        phase36_ledger.require_e4_first_point(price * 1.2501, tracked=[])
    planted.budget = {**planted.budget, "unit_prices": {}}
    with pytest.raises(SystemExit, match="e4_point_seconds"):
        phase36_ledger.require_e4_first_point(price, tracked=[])


# =================================================================================================
# (6) THE REAL LEDGER (T-36-05) AND THE MPS RECORDS IT MUST NAME (D-11).
# =================================================================================================


def test_prove_append_only(tmp_path, monkeypatch):
    rel = "scripts/phase36_prereg.py"
    assert phase36_ledger._committed_bytes(rel) == (_ROOT / rel).read_bytes()
    working = tmp_path / "ledger.jsonl"
    assert phase36_ledger.prove_append_only([], working) == 0  # untracked: nothing to prove
    monkeypatch.setattr(phase36_ledger, "_committed_bytes", lambda rel: b"a\nb\n")
    working.write_bytes(b"a\nb\nc\n")
    assert phase36_ledger.prove_append_only([phase36_ledger.LEDGER_PATH], working) == 4
    working.write_bytes(b"a\nX\nc\n")
    with pytest.raises(SystemExit, match="T-36-05"):
        phase36_ledger.prove_append_only([phase36_ledger.LEDGER_PATH], working)


def test_every_reader_of_the_real_ledger_proves_it_append_only(
    clock, tmp_path, planted, monkeypatch
):
    """WR-04 (T-36-05): a working ledger whose committed bytes are not its prefix (a dropped lost
    line hides hours; a deleted file hides all of them) is refused by every path that reads or
    writes the real ledger, never read silently. A tmp/scratch ledger is not the real one."""
    scratch = tmp_path / "scratch.jsonl"
    _spend(scratch, "E5", 1.0, unit="hidden")
    _spend(scratch, "E1", 2.0, unit="kept")
    committed = scratch.read_bytes()
    real = tmp_path / phase36_ledger.LEDGER_PATH
    real.parent.mkdir(parents=True)
    monkeypatch.setattr(phase36_ledger, "_ROOT", tmp_path)
    monkeypatch.setattr(phase36_caps, "tracked_files", lambda: [phase36_ledger.LEDGER_PATH])
    monkeypatch.setattr(phase36_ledger, "_committed_bytes", lambda rel: committed)
    tracked = [phase36_ledger.LEDGER_PATH]
    calls = (
        lambda: phase36_ledger.spent(tracked),
        lambda: phase36_ledger.require_launch("E5", tracked=tracked),
        lambda: phase36_ledger.rule("E5", "a", "go", tracked=tracked),
        lambda: phase36_ledger.reconcile(),
        lambda: phase36_ledger.report_rows(tracked),
        lambda: _start("E2", "x", None),
    )
    for working in (b"".join(committed.splitlines(keepends=True)[2:]), None):
        if working is None:
            real.unlink()
        else:
            real.write_bytes(working)
        for call in calls:
            with pytest.raises(SystemExit, match="T-36-05"):
                call()
    real.write_bytes(committed)  # appended-to (here: equal) passes
    assert phase36_ledger.spent(tracked)["by_front"]["E5"] == 3600.0
    assert phase36_ledger.spent(tracked, ledger_path=scratch)["by_front"]["E1"] == 7200.0


def _git_ls(*patterns):
    out = subprocess.run(
        ["git", "ls-files", *patterns], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    return out.stdout.split()


def _ended_records():
    if phase36_ledger.LEDGER_PATH not in _git_ls(phase36_ledger.LEDGER_PATH):
        return set()
    return {x["record"] for x in phase36_ledger.read_ledger() if x["event"] == "end"}


def test_real_ledger_is_append_only_and_names_every_probe_record():
    probes = _git_ls(phase36_prereg.PROBE_GLOB)
    if phase36_ledger.LEDGER_PATH in _git_ls(phase36_ledger.LEDGER_PATH):
        assert phase36_ledger.prove_append_only() > 0
        assert set(probes) <= _ended_records()
    else:
        assert probes == []  # today: no ledger, no probe record (W9: the ledger commits first)


def test_every_tracked_v6_mps_record_has_a_launch_line():
    ended = _ended_records()
    unnamed = []
    for path in _git_ls("results/phase3[7-9]_*", "results/phase4[0-3]_*"):
        try:
            record = json.loads((_ROOT / path).read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        run = record.get("provenance", {}).get("run", {}) if isinstance(record, dict) else {}
        if isinstance(run, dict) and run.get("device") == "mps" and path not in ended:
            unnamed.append(path)
    assert unnamed == []  # honest-green at zero MPS records


# =================================================================================================
# (7) NO RUN LOG, NO wall_clock (T-36-07); CPU-ONLY; EVERY FUNCTION HAS A CPU TEST.
# =================================================================================================

_FORBIDDEN = ("run.csv", "wall_clock")


def _clock_source_failures(source):
    """(failures, collected): non-docstring str constants and attribute names in `source`."""
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    collected = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                collected.add(node.value)
        elif isinstance(node, ast.Attribute):
            collected.add(node.attr)
    failures = sorted(text for text in collected if _FORBIDDEN[0] in text or text == _FORBIDDEN[1])
    return failures, collected


def test_ledger_never_reads_run_csv_or_wall_clock():
    source = (_ROOT / LEDGER).read_text(encoding="utf-8")
    failures, collected = _clock_source_failures(source)
    assert collected, "meta-guard: nothing collected, the gate is blind"
    assert "provenance" in collected and "finished_utc" in collected
    assert failures == []
    for planted in ('x = "logs/run.csv"\n', 'y = record["wall_clock"]\n', "z = r.wall_clock\n"):
        assert _clock_source_failures(source + planted)[0], planted


_HEAVY = ("torch", "teach_persona", "phase19_erasure", "phase18_extraction", "phase23_run")


def test_the_ledger_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase36_ledger; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout


def test_every_ledger_function_has_a_cpu_test():
    source = (_ROOT / LEDGER).read_text(encoding="utf-8")
    assert [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _untested_functions("phase36_ledger", source, test_source) == []
