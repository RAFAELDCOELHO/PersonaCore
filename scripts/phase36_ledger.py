"""The v6.0 MPS ledger (D-11..D-13, D-19): one cumulative, append-only record of every MPS run.

Every v6.0 MPS run (Phases 36-43, probes included) writes a ``start`` line before it runs and an
``end`` line naming its result record when it finishes. A run that dies leaves a start with no end:
``reconcile`` closes it with a ``lost`` line, counted to its last heartbeat SINCE THAT ATTEMPT'S
START and flagged "sem registro de resultado" on its front (D-12). Spent hours come from each
record's own ``provenance.run`` UTC fields, never typed and never from the training loop's CSV log,
whose wall-clock column holds the step number.

Before a launch, ``require_launch`` refuses a cut front and pauses at the three D-13 stops. A stop
is lifted only by a ``ruling`` line written by ``rule`` after Rafael's written ruling, for exactly
that stop, that front and that launch, on the numbers he saw.

Paths (Q3): the ledger is COMMITTED at ``ledger/v6_mps_ledger.jsonl``, outside scripts/, src/,
results/ and tests/, so it trips no clean-tree probe; the raw 60-s beats go to the gitignored
``data/v6_mps_heartbeat.jsonl`` (written with ``phase25_run.beat``, ``point`` = the run id).

Torch-free at import.
"""

import argparse
import datetime
import fnmatch
import json
import math
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase30_points  # noqa: E402  (scripts/ is not a package; torch-free)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)

LEDGER_PATH = "ledger/v6_mps_ledger.jsonl"
HEARTBEAT_PATH = _ROOT / "data" / "v6_mps_heartbeat.jsonl"

EVENTS = ("start", "end", "lost", "ruling")
LINE_FIELDS = (
    "utc",
    "event",
    "run_id",
    "phase",
    "front",
    "record",
    "seconds",
    "flag",
    "stop",
    "ruling",
)
STOPS = ("a", "b", "c")
LOST_FLAG = "sem registro de resultado"
NO_BEAT_FLAG = "sem registro de resultado; no heartbeat after its start (0 s counted)"
PENDING_FLAG = "record not yet tracked"
# Every v6.0 MPS record carries provenance.run.started_utc / finished_utc / device.
RECORD_CLOCK = ("provenance", "run")


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase36_ledger] {message}")


def run_id(phase, front, unit):
    """The ledger id of one run: ``v6/<phase>/<front>/<unit>``; heartbeats carry it as ``point``."""
    return f"v6/{phase}/{front}/{unit}"


def _utc_now():
    """The one clock for ledger lines."""
    return datetime.datetime.now(datetime.timezone.utc)


def _write_line(line, ledger_path):
    """Append one sort_keys JSON line. Never rewrites; refuses to append onto a torn tail."""
    _prove(
        set(line) == set(LINE_FIELDS), f"a ledger line carries exactly LINE_FIELDS {LINE_FIELDS}"
    )
    path = pathlib.Path(ledger_path or _ROOT / LEDGER_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        with path.open("rb") as handle:
            handle.seek(-1, 2)
            _prove(
                handle.read(1) == b"\n",
                f"{path} ends in a torn line; it is never rewritten by a script: inspect it before "
                "any further append",
            )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, sort_keys=True) + "\n")
    return line


def read_ledger(path=None):
    """Every line as a dict. A non-JSON LAST line (torn tail) is skipped; an earlier one refuses."""
    path = pathlib.Path(path or _ROOT / LEDGER_PATH)
    if not path.exists():
        return []
    texts = [t for t in path.read_text(encoding="utf-8").splitlines() if t.strip()]
    lines = []
    for number, text in enumerate(texts, start=1):
        try:
            line = json.loads(text)
        except ValueError:
            _prove(number == len(texts), f"{path} line {number} is torn and is not the last line")
            continue
        _prove(
            isinstance(line, dict) and line.get("event") in EVENTS,
            f"{path} line {number} is not a ledger line: {text[:80]!r}",
        )
        lines.append(line)
    return lines


def _committed_bytes(rel):
    shown = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_ROOT, capture_output=True)
    _prove(shown.returncode == 0, f"{rel} has no committed blob at HEAD")
    return shown.stdout


def prove_append_only(tracked=None, path=None):
    """T-36-05: a tracked ledger's committed bytes are a prefix of the working file's. Returns the
    number of committed bytes verified (0 while the ledger is untracked)."""
    tracked = phase36_caps.tracked_files() if tracked is None else tracked
    if LEDGER_PATH not in tracked:
        return 0
    committed = _committed_bytes(LEDGER_PATH)
    working = pathlib.Path(path or _ROOT / LEDGER_PATH).read_bytes()
    _prove(
        working.startswith(committed),
        f"{LEDGER_PATH}'s committed bytes are not a prefix of the working file: the ledger was "
        "rewritten, not appended to (T-36-05)",
    )
    return len(committed)


def last_beat_since(point, since_utc, heartbeat_path=None):
    """The latest complete beat utc of ``point`` at or after ``since_utc``, else None (B1)."""
    path = pathlib.Path(heartbeat_path or HEARTBEAT_PATH)
    if not path.exists():
        return None
    latest = None
    for text in path.read_text(encoding="utf-8").splitlines():
        try:
            beat = json.loads(text)
        except ValueError:
            continue  # a torn line, as in phase25_watch.read_last_beat
        if not (isinstance(beat, dict) and beat.get("point") == point and "utc" in beat):
            continue
        when = datetime.datetime.fromisoformat(beat["utc"])
        if when >= since_utc and (latest is None or when > latest):
            latest = when
    return latest


def _attempts(lines):
    """``[(start line, end/lost line or None)]`` in ledger order; ruling lines are ignored."""
    attempts, current = [], {}
    for line in lines:
        rid = line["run_id"]
        if line["event"] == "start":
            _prove(rid not in current, f"run {rid} has a start while an attempt is still open")
            current[rid] = len(attempts)
            attempts.append((line, None))
        elif line["event"] in ("end", "lost"):
            _prove(rid in current, f"run {rid} has an {line['event']} line but no open attempt")
            index = current.pop(rid)
            attempts[index] = (attempts[index][0], line)
    return attempts


def open_runs(lines):
    """``{run_id: its open start line}``: a start with no end or lost line after it (W3)."""
    return {start["run_id"]: start for start, close in _attempts(lines) if close is None}


def append(event, *, run_id, phase, front, record=None, seconds=None, flag=None, ledger_path=None):
    """Append one start, end or lost line (ruling lines are written by ``rule``)."""
    _prove(event in ("start", "end", "lost"), f"append writes start, end or lost, not {event!r}")
    fronts = phase35_prereg.V6_MPS_FRONTS
    _prove(front in fronts, f"front {front!r} is not in V6_MPS_FRONTS {fronts}")
    _prove(isinstance(run_id, str) and run_id, f"run_id {run_id!r} is not a non-empty str")
    opened = open_runs(read_ledger(ledger_path))
    if event == "start":
        _prove(run_id not in opened, f"run {run_id} still open: reconcile or end it first")
    else:
        _prove(run_id in opened, f"run {run_id} has no open attempt to {event}")
        _prove(
            opened[run_id]["front"] == front,
            f"run {run_id} started on front {opened[run_id]['front']}, not {front}",
        )
    if event == "end":
        _prove(
            isinstance(record, str)
            and any(fnmatch.fnmatch(record, p) for p in phase35_prereg.V6_RESULT_PATHS),
            f"end record {record!r} matches no V6_RESULT_PATHS pattern",
        )
    if event == "lost":
        _prove(
            isinstance(seconds, (int, float))
            and not isinstance(seconds, bool)
            and math.isfinite(seconds)
            and seconds >= 0,
            f"lost seconds {seconds!r} is not a finite number >= 0",
        )
        _prove(flag in (LOST_FLAG, NO_BEAT_FLAG), f"lost flag {flag!r} is not a lost flag")
    line = dict.fromkeys(LINE_FIELDS)
    line.update(
        utc=_utc_now().isoformat(),
        event=event,
        run_id=run_id,
        phase=phase,
        front=front,
        record=record,
        seconds=seconds,
        flag=flag,
    )
    return _write_line(line, ledger_path)


def reconcile(*, ledger_path=None, heartbeat_path=None):
    """D-12, B1: close every open attempt with a lost line, counted from its start to its last
    beat SINCE THAT START (LOST_FLAG), or at 0 s (NO_BEAT_FLAG) when it has none. Never refuses a
    missing beat: an open start would otherwise block spent() and every launch forever. Returns
    the appended lines."""
    appended = []
    for rid, start in open_runs(read_ledger(ledger_path)).items():
        began = datetime.datetime.fromisoformat(start["utc"])
        beat = last_beat_since(rid, began, heartbeat_path)
        if beat is None:
            seconds, flag = 0.0, NO_BEAT_FLAG
        else:
            seconds, flag = (beat - began).total_seconds(), LOST_FLAG
        _prove(seconds >= 0, f"run {rid} reconciled to negative seconds {seconds}")
        appended.append(
            append(
                "lost",
                run_id=rid,
                phase=start["phase"],
                front=start["front"],
                seconds=seconds,
                flag=flag,
                ledger_path=ledger_path,
            )
        )
    return appended


def _closed_row(start, close, tracked):
    """One closed attempt's seconds: a lost line's own; a tracked record's provenance.run span;
    an untracked record's end minus start utc, flagged pending."""
    row = {
        "run_id": start["run_id"],
        "phase": start["phase"],
        "front": start["front"],
        "event": close["event"],
        "record": close["record"],
        "started_utc": start["utc"],
        "status": "closed",
    }
    if close["event"] == "lost":
        return {**row, "seconds": close["seconds"], "flag": close["flag"]}
    if close["record"] in tracked:
        clock = phase30_points._tracked_json(close["record"], tracked, "the run record")
        for key in RECORD_CLOCK:
            clock = clock.get(key) if isinstance(clock, dict) else None
        _prove(
            isinstance(clock, dict) and {"started_utc", "finished_utc"} <= set(clock),
            f"{close['record']} carries no provenance.run started_utc / finished_utc",
        )
        started, finished = clock["started_utc"], clock["finished_utc"]
        flag = None
    else:
        started, finished, flag = start["utc"], close["utc"], PENDING_FLAG
    seconds = (
        datetime.datetime.fromisoformat(finished) - datetime.datetime.fromisoformat(started)
    ).total_seconds()
    _prove(seconds >= 0, f"run {start['run_id']} has a negative span {seconds} s")
    return {**row, "seconds": seconds, "flag": flag}


def spent(tracked=None, *, ledger_path=None, fronts=None):
    """Seconds spent per front over CLOSED attempts; refuses while an in-scope attempt is open."""
    scope = phase35_prereg.V6_MPS_FRONTS if fronts is None else fronts
    _prove(
        set(scope) <= set(phase35_prereg.V6_MPS_FRONTS),
        f"fronts {scope!r} are not in V6_MPS_FRONTS",
    )
    tracked = phase36_caps.tracked_files() if tracked is None else tracked
    attempts = [a for a in _attempts(read_ledger(ledger_path)) if a[0]["front"] in scope]
    still = [start["run_id"] for start, close in attempts if close is None]
    _prove(
        not still,
        f"attempts still open: {still}. Wait for their end lines, or run `phase36_ledger.py "
        "reconcile` once the run is dead; `phase36_ledger.py report` shows progress",
    )
    records = [close["record"] for _, close in attempts if close["event"] == "end"]
    twice = sorted({r for r in records if records.count(r) > 1})
    _prove(not twice, f"records named by two end lines (double count): {twice}")
    rows = [_closed_row(start, close, tracked) for start, close in attempts]
    by_front = {
        front: math.fsum(r["seconds"] for r in rows if r["front"] == front) for front in scope
    }
    return {"by_front": by_front, "total_seconds": math.fsum(by_front.values()), "rows": rows}


def stop_checks(budget, spent_h):
    """The D-13 stops as ``{letter: message or None}`` (pure)."""
    hours = budget["front_hours"]
    factor = phase36_prereg.ENTRIES["front_stop_factor"]["value"]
    ceiling = phase35_prereg.ENTRIES["mps_ceiling_hours"]["value"]
    over = [
        f"{f} spent {spent_h.get(f, 0):.4f} h, above {factor} x its high bound {hours[f]} h"
        for f in phase35_prereg.V6_MPS_FRONTS
        if spent_h.get(f, 0) > factor * hours[f]
    ]
    total = math.fsum(spent_h.values())
    projection = math.fsum(max(hours[f], spent_h.get(f, 0)) for f in phase35_prereg.V6_MPS_FRONTS)
    return {
        "a": "D-13 stop (a): " + "; ".join(over) if over else None,
        "b": (
            f"D-13 stop (b): cumulative spent {total:.4f} h reached stop_line_hours "
            f"{budget['stop_line_hours']}"
            if total >= budget["stop_line_hours"]
            else None
        ),
        "c": (
            f"D-13 stop (c): projection sum(max(front_hours, spent)) = {projection:.4f} h is "
            f"above mps_ceiling_hours {ceiling}: pause BEFORE launching and bring the cut table"
            if projection > ceiling
            else None
        ),
    }


def _lifted(lines, front, stop, spent_seconds):
    """A ruling for this front and stop after the front's last start, given on these numbers."""
    last_start = max(
        (i for i, x in enumerate(lines) if x["event"] == "start" and x["front"] == front),
        default=-1,
    )
    return any(
        x["event"] == "ruling"
        and x["front"] == front
        and x["stop"] == stop
        and x["seconds"] == spent_seconds
        for x in lines[last_start + 1 :]
    )


def _state(front, tracked, ledger_path):
    """(budget, spent totals, stop checks) for ``front``; refuses an unknown or cut front."""
    fronts = phase35_prereg.V6_MPS_FRONTS
    _prove(front in fronts, f"front {front!r} is not in V6_MPS_FRONTS {fronts}")
    budget = phase36_caps.committed_budget(tracked)
    _prove(
        budget["front_hours"][front] > 0,
        f"front {front} has 0 committed hours: a cut front never launches (W1, D-15); only a new "
        "budget Rafael approves restores it",
    )
    totals = spent(tracked, ledger_path=ledger_path)
    spent_h = {f: s / 3600 for f, s in totals["by_front"].items()}
    return budget, totals, stop_checks(budget, spent_h)


def require_launch(front, *, tracked=None, ledger_path=None):
    """D-13 before every launch: refuse a cut front; pause at each unlifted stop. Writes nothing."""
    tracked = phase36_caps.tracked_files() if tracked is None else tracked
    _, totals, checks = _state(front, tracked, ledger_path)
    lines = read_ledger(ledger_path)
    lifted = []
    for letter in STOPS:
        if checks[letter] is None:
            continue
        if _lifted(lines, front, letter, totals["total_seconds"]):
            lifted.append(letter)
            continue
        _prove(
            False,
            f"{checks[letter]}. PAUSE: take what already ran and the cut table to Rafael (D-13); "
            f"after his written ruling, `phase36_ledger.py rule --front {front} --stop {letter} "
            "--text '<his ruling verbatim>'` lifts this stop for this front's next launch",
        )
    return {
        "front": front,
        "spent_seconds": totals["by_front"],
        "total_seconds": totals["total_seconds"],
        "lifted": tuple(lifted),
    }


def rule(front, stop, text, *, tracked=None, ledger_path=None):
    """Write Rafael's ruling for a stop TRIPPED NOW (W5). Run only on his own written reply."""
    _prove(stop in STOPS, f"stop {stop!r} is not one of STOPS {STOPS}")
    _prove(isinstance(text, str) and text.strip(), "the ruling text is empty")
    tracked = phase36_caps.tracked_files() if tracked is None else tracked
    _, totals, checks = _state(front, tracked, ledger_path)
    _prove(
        checks[stop] is not None,
        f"stop ({stop}) is not tripped now: a ruling is never written ahead of its stop",
    )
    line = dict.fromkeys(LINE_FIELDS)
    line.update(
        utc=_utc_now().isoformat(),
        event="ruling",
        front=front,
        stop=stop,
        ruling=text,
        seconds=totals["total_seconds"],  # a snapshot; spent() never counts a ruling line
    )
    return _write_line(line, ledger_path)


def require_e4_first_point(first_point_seconds, *, tracked=None):
    """D-19: the first E4 point's seconds within divergence_tolerance of the reserve's price.
    Returns the divergence."""
    prices = phase36_caps.committed_budget(tracked).get("unit_prices", {})
    _prove("e4_point_seconds" in prices, "the budget carries no unit_prices e4_point_seconds")
    price = prices["e4_point_seconds"]
    _prove(
        not phase36_prereg.exceeds(first_point_seconds, price),
        f"D-19: the first E4 point took {first_point_seconds} s against the reserve's {price} s "
        "per point, above divergence_tolerance. PAUSE before the rest launch: back to Rafael",
    )
    return phase36_prereg.divergence(first_point_seconds, price)


def report_rows(tracked=None, *, ledger_path=None, heartbeat_path=None):
    """The progress view (W7c): every attempt (open ones with seconds to their last beat since
    their start, None before the first beat), every ruling, and per-front totals of CLOSED
    attempts. Never refuses on an open attempt."""
    tracked = phase36_caps.tracked_files() if tracked is None else tracked
    lines = read_ledger(ledger_path)
    rows = []
    for start, close in _attempts(lines):
        if close is not None:
            rows.append(_closed_row(start, close, tracked))
            continue
        began = datetime.datetime.fromisoformat(start["utc"])
        beat = last_beat_since(start["run_id"], began, heartbeat_path)
        rows.append(
            {
                "run_id": start["run_id"],
                "phase": start["phase"],
                "front": start["front"],
                "event": "start",
                "record": None,
                "started_utc": start["utc"],
                "status": "open",
                "seconds": None if beat is None else (beat - began).total_seconds(),
                "flag": None,
            }
        )
    rows += [{**x, "status": "ruling"} for x in lines if x["event"] == "ruling"]
    by_front = {
        f: math.fsum(r["seconds"] for r in rows if r["status"] == "closed" and r["front"] == f)
        for f in phase35_prereg.V6_MPS_FRONTS
    }
    return {"rows": rows, "by_front": by_front}


def main(argv=None):
    parser = argparse.ArgumentParser(description="The v6.0 MPS ledger (D-11..D-13).")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("report", help="every attempt, open ones included; never refuses")
    commands.add_parser("reconcile", help="close every open attempt of a dead run (D-12)")
    ruling = commands.add_parser("rule", help="Rafael's written ruling on a tripped stop (W5)")
    ruling.add_argument("--front", required=True)
    ruling.add_argument("--stop", required=True, choices=STOPS)
    ruling.add_argument("--text", required=True)
    args = parser.parse_args(argv)
    if args.command == "report":
        report = report_rows()
        for row in report["rows"]:
            print(json.dumps(row, sort_keys=True))
        print(json.dumps({"closed_seconds_by_front": report["by_front"]}, sort_keys=True))
    elif args.command == "reconcile":
        for line in reconcile():
            print(json.dumps(line, sort_keys=True))
    else:
        print(json.dumps(rule(args.front, args.stop, args.text), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
