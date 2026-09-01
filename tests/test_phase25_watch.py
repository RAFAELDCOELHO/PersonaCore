"""PLAN 25-05 — BOTH HALVES OF D-16 WATCHED, BEFORE THE SWEEP SPENDS A DAY.

`scripts/phase25_watch.py` makes two claims. The first — *it detects silence* — is the one anybody
would think to test. The second — *it takes no action* — is the one that matters, because the
sweep's LaunchAgent runs with `KeepAlive` **FALSE** precisely so that nothing re-enters a point
outside the driver's deliberate resume logic (D-10, D-12). A watcher that acquires the ability to
relaunch turns a detector into a supervisor and violates the one-attempt rule on the sweep's behalf.

**THE NEVER-ACT HALF IS THE PROPERTY MOST LIKELY TO ROT**, so it gets the treatment this repo
reserves for those: a structural guard, watched failing. `tests/test_phase22_dpsgd_ast.py` states
the rule the guards below satisfy — *a guard proved correct in a scratch repository and a guard
running against this one must be the SAME code, or the proof is about a different function than the
one CI runs.* `_action_calls` and `_write_targets` therefore take **SOURCE TEXT, never a path**, so
the live check over `scripts/phase25_watch.py` and the RED probe over the planted scratch copy in
`tmp_path` execute byte-identical walkers.

**AND THE GUARD IS AN AST WALK, NEVER A GREP — MEASURED, NOT PREFERRED.**
`test_grep_goes_false_red_on_the_watcher` is that measurement: the watcher's own prose names `kill`
and `launchctl` on purpose (they are what `FORBIDDEN_ACTIONS` is *about*), so a textual gate over
that file reports violations that do not exist while the parse reports none. This is the class
`tests/test_phase24_correction.py`'s mechanic 4 exists to close, and `.planning/REQUIREMENTS.md`'s
RPT-02 row records four independent instances of it in Phase 20 alone.

**THE PLANT GOES INTO `tmp_path`, NEVER INTO `scripts/`**, and the test asserts
`git status --porcelain scripts/` is empty immediately afterwards —
`tests/test_phase25_epsilon.py`'s register, for the same reason: a RED watched by mutating a real
repo file is a RED that can be left behind.

**N IS ASSERTED AGAINST ITS SOURCES, NEVER AGAINST ITSELF.** `test_n_is_derived_from_the_measured_
table` recomputes the 24-prompt gaps and both training legs from the committed records and compares
them to `N_DERIVATION`'s pinned literals under exact `==`. A test that read the constant and
compared it to the constant would be green for a module that made every number up.

CPU-only, GPU-free: stdlib plus `pytest`. No torch, no numpy, no network, no MPS.
"""

import ast
import datetime
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase25_watch  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)

_WATCHER_PATH = _ROOT / "scripts" / "phase25_watch.py"
_WATCHER_SOURCE = _WATCHER_PATH.read_text(encoding="utf-8")

# The two committed records N is derived FROM. Both are tracked: `data/` is gitignored
# (`.gitignore:17`), so `results/phase23_never_taught.json` is the CI-visible mirror of the
# seed-1337 draw timings — see `N_DERIVATION["measured_seed1337"]`.
_COST_RECORD = _ROOT / "results" / "phase23_cost.json"
_NEVER_TAUGHT_RECORD = _ROOT / "results" / "phase23_never_taught.json"

_BASE_UTC = "2026-08-31T00:00:00+00:00"


def _beat(**overrides):
    """One heartbeat line carrying all five `HEARTBEAT_FIELDS`."""
    fields = {
        "utc": _BASE_UTC,
        "point": "dp_n8_sigma0p000000",
        "stage": "draw",
        "shape": "A3",
        "draw_index": 7,
    }
    fields.update(overrides)
    return json.dumps(fields)


def _at(minutes):
    """`now`, INJECTED — the boundary is observed without sleeping through it."""
    base = datetime.datetime.fromisoformat(_BASE_UTC)
    return base + datetime.timedelta(minutes=minutes)


def _records(path):
    """Every stall record written so far, in the order it was appended."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


# =================================================================================================
# ===== (a) THE DETECT HALF, WATCHED AGAINST A DELIBERATELY-STALLED STUB =====
# =================================================================================================


def test_a_stalled_heartbeat_writes_exactly_one_stall_record(tmp_path):
    """One silence, one record — carrying WHERE it died, which is the whole diagnostic value."""
    heartbeat = tmp_path / "heartbeat.jsonl"
    heartbeat.write_text(_beat() + "\n", encoding="utf-8")
    stall = tmp_path / "stall.jsonl"

    record = phase25_watch.check(heartbeat, stall_record_path=stall, now=_at(6))

    assert record is not None
    assert _records(stall) == [record], "exactly one record, and it is the one returned"

    # All five fields VERBATIM — not summarised, not renamed, not dropped.
    assert set(record["last_beat"]) == set(phase25_watch.HEARTBEAT_FIELDS)
    assert record["last_beat"] == json.loads(_beat())

    # WHERE it died. A record that said only "stalled" would be worth nothing after six days.
    assert record["last_beat"]["point"] == "dp_n8_sigma0p000000"
    assert record["last_beat"]["stage"] == "draw"
    assert record["last_beat"]["shape"] == "A3"
    assert record["last_beat"]["draw_index"] == 7

    assert record["silence_minutes"] == 6.0
    assert record["stall_threshold_minutes"] == phase25_watch.STALL_THRESHOLD_MINUTES
    assert record["missed_beats"] == 6.0
    assert record["detected_utc"] == _at(6).isoformat()

    # D-16's literal. Its absence would read as an oversight; its presence is the claim.
    assert record["action_taken"] == "none"
    assert "D-16" in record["action_taken_reason"]
    assert "D-10" in record["action_taken_reason"]


def test_a_live_heartbeat_writes_nothing(tmp_path):
    """Below the threshold the watcher's only output path must not come into existence at all."""
    heartbeat = tmp_path / "heartbeat.jsonl"
    heartbeat.write_text(_beat() + "\n", encoding="utf-8")
    stall = tmp_path / "stall.jsonl"

    assert phase25_watch.check(heartbeat, stall_record_path=stall, now=_at(4)) is None
    assert not stall.exists(), "a live heartbeat must not create the stall record"


@pytest.mark.parametrize(
    ("minutes", "expect_record"),
    [(4.9, False), (5.0, True), (5.1, True)],
)
def test_the_boundary_is_the_measured_threshold(tmp_path, minutes, expect_record):
    """THE COMPARISON DIRECTION IS PINNED, NOT ASSUMED.

    N is a measured quantity (`N_DERIVATION`), so `>=` versus `>` at exactly N is a decision and not
    a detail. Straddling it with 4.9 / 5.0 / 5.1 is what makes it a decision on the record: silence
    EQUAL to the threshold fires.
    """
    heartbeat = tmp_path / "heartbeat.jsonl"
    heartbeat.write_text(_beat() + "\n", encoding="utf-8")
    stall = tmp_path / "stall.jsonl"

    record = phase25_watch.check(heartbeat, stall_record_path=stall, now=_at(minutes))

    assert (record is not None) is expect_record
    assert stall.exists() is expect_record
    # The direction, stated as arithmetic: silence AT the threshold counts as stalled.
    assert (minutes >= phase25_watch.STALL_THRESHOLD_MINUTES) is expect_record


def test_a_truncated_final_line_falls_back_to_the_previous_beat(tmp_path):
    """WHY THE HEARTBEAT IS LINE-ORIENTED AND APPEND-ONLY RATHER THAN A REWRITTEN JSON BLOB.

    The case this whole module exists for is a process killed mid-write, so the very last bytes on
    disk are the ones most likely to be half a line. Append-only lines make a torn tail cost at
    most the newest beat: every earlier beat is still parseable and `read_last_beat` walks back one.
    A rewritten blob would leave a file `json.loads` rejects outright, losing the diagnostic value
    of every beat ever written — the `_never_taught_write_draws` failure mode 25-VALIDATION.md
    calls out, at the one moment the record matters most.
    """
    heartbeat = tmp_path / "heartbeat.jsonl"
    complete = _beat(draw_index=11, shape="A2")
    heartbeat.write_text(complete + "\n" + _beat(draw_index=12)[:37], encoding="utf-8")

    beat = phase25_watch.read_last_beat(heartbeat)

    assert beat == json.loads(complete)
    assert beat["draw_index"] == 11 and beat["shape"] == "A2"


def test_an_empty_heartbeat_is_not_a_stall(tmp_path):
    """The normal state between the LaunchAgent starting and the driver's first beat."""
    heartbeat = tmp_path / "heartbeat.jsonl"
    heartbeat.write_text("", encoding="utf-8")
    stall = tmp_path / "stall.jsonl"

    assert phase25_watch.read_last_beat(heartbeat) is None
    assert phase25_watch.check(heartbeat, stall_record_path=stall, now=_at(600)) is None
    assert not stall.exists()


def test_an_absent_heartbeat_is_not_a_stall_either(tmp_path):
    """THE WINDOW BETWEEN BOOTSTRAPPING THE WATCHER AND THE SWEEP'S FIRST BEAT.

    `artifacts/com.personacore.phase25.watch.plist` runs this module every 60 s from the moment it
    is bootstrapped, and the operator bootstraps it BEFORE kickstarting the sweep — so for that
    whole window `data/phase25_heartbeat.jsonl` does not exist yet. Measured in plan 25-14: without
    the guard this raised `FileNotFoundError` once a minute and filled `logs/phase25_watch.err`
    with tracebacks in the state the module's own docstring calls normal.

    It is the SAME state as the empty file above, one step earlier, and it must read the same: no
    beat, no stall, no record, exit 0.
    """
    heartbeat = tmp_path / "never-written.jsonl"
    stall = tmp_path / "stall.jsonl"
    assert not heartbeat.exists()

    assert phase25_watch.read_last_beat(heartbeat) is None
    assert phase25_watch.check(heartbeat, stall_record_path=stall, now=_at(600)) is None
    assert not stall.exists()
    assert phase25_watch.main(["--heartbeat", str(heartbeat), "--stall-record", str(stall)]) == 0


def test_repeated_checks_append_rather_than_overwrite(tmp_path):
    """A SIX-DAY SILENCE MUST BE A HISTORY, NOT A SINGLE POINT (threat T-25-22).

    An overwriting writer would leave one record whose timestamp says only when the watcher last
    ran. Appending leaves the shape of the silence: when it began and how long nobody noticed.
    """
    heartbeat = tmp_path / "heartbeat.jsonl"
    heartbeat.write_text(_beat() + "\n", encoding="utf-8")
    stall = tmp_path / "stall.jsonl"

    first = phase25_watch.check(heartbeat, stall_record_path=stall, now=_at(6))
    second = phase25_watch.check(heartbeat, stall_record_path=stall, now=_at(11))

    written = _records(stall)
    assert written == [first, second]
    assert [row["silence_minutes"] for row in written] == [6.0, 11.0]
    assert written[0]["last_beat"] == written[1]["last_beat"], "the same beat, still not advancing"


# =================================================================================================
# ===== (b) THE NEVER-ACT HALF — THE PROPERTY MOST LIKELY TO ROT =====
#
# Both walkers take SOURCE TEXT, never a path, so the live check and the planted RED probe below
# execute the SAME code (`tests/test_phase22_dpsgd_ast.py`'s rule).
# =================================================================================================


def _action_calls(source):
    """Every `FORBIDDEN_ACTIONS` identifier reaching a CALL POSITION. Sorted `(lineno, name)`.

    A call position is an `ast.Call`'s callee: a bare `kill(...)`, an attribute
    `subprocess.run(...)` or a chained `Popen(...).terminate()`. Resolved by parse and by EXACT
    membership — never by
    substring and never by grep, both of which go false-RED on this module's own prose.
    """
    tree = ast.parse(source)
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        name = None
        if isinstance(callee, ast.Name):
            name = callee.id
        elif isinstance(callee, ast.Attribute):
            name = callee.attr
        if name in phase25_watch.FORBIDDEN_ACTIONS:
            found.add((callee.lineno, name))
    return sorted(found)


def _action_failure_message(findings, label):
    """Names the offending call, its `lineno` and its FILE — 'failed' alone is a dead end.

    `label` is passed rather than hard-coded so the planted RED names the scratch copy it actually
    walked. A message that said `scripts/phase25_watch.py` while walking `tmp_path` would send a
    reader to a clean file.
    """
    return "\n".join(
        f"{label}:{lineno}: forbidden action {name!r} appears in a CALL "
        f"POSITION. D-16 makes this watcher a DETECTOR: an automatic restart, kill or cleanup "
        f"re-enters a sweep point outside the driver's deliberate resume logic and violates "
        f"D-10's one-attempt rule. Remove the call; a stall is corrected by a human."
        for lineno, name in findings
    )


def _imported_modules(source):
    """Top-level module names this source imports."""
    tree = ast.parse(source)
    names = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    names |= {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    return names


def test_the_watcher_takes_no_action():
    """D-16'S DETECT-NEVER-ACT HALF, live over `scripts/phase25_watch.py`."""
    findings = _action_calls(_WATCHER_SOURCE)
    assert findings == [], _action_failure_message(findings, "scripts/phase25_watch.py")

    # Non-vacuous: the tuple the walker checks against must actually be populated, and it must
    # contain the actions that would matter. A guard over an empty tuple passes everything.
    assert phase25_watch.FORBIDDEN_ACTIONS == (
        "kill",
        "terminate",
        "Popen",
        "run",
        "launchctl",
        "unlink",
        "rmtree",
        "remove",
    )

    # The import set is the second lock: `subprocess` is what makes every one of the above
    # reachable in one line, so its absence is asserted rather than inferred (threat T-25-21).
    modules = _imported_modules(_WATCHER_SOURCE)
    assert "subprocess" not in modules
    assert modules <= {"json", "pathlib", "datetime", "argparse", "sys", "os"}, modules


def test_grep_goes_false_red_on_the_watcher():
    """THE MEASUREMENT THAT JUSTIFIES THE PARSE, taken on the real committed file.

    A textual gate over `scripts/phase25_watch.py` reports violations that DO NOT EXIST: the module
    names `kill`, `launchctl`, `terminate` and the rest in its docstrings and in `FORBIDDEN_ACTIONS`
    itself, on purpose, because that tuple is what the module is *about*. Only a parse can tell
    prose about a name from the name.
    """
    textual = sorted({name for name in phase25_watch.FORBIDDEN_ACTIONS if name in _WATCHER_SOURCE})
    assert textual, "the demonstration is vacuous if the tokens are absent from the text"
    assert "kill" in textual and "launchctl" in textual

    assert _action_calls(_WATCHER_SOURCE) == [], (
        f"grep-RED on {textual} / AST-GREEN: {len(textual)} forbidden tokens occur textually and "
        f"NONE of them resolves to a call. A textual gate would be red on a correct file."
    )


def _write_targets(source):
    """Every write in `source`, as `(lineno, receiver-name-or-None)`.

    Collects `write_text` / `write_bytes` calls and any `open(...)` whose mode admits writing. The
    receiver is the path operand: `X.open(...)`'s `X`, or builtin `open(path, ...)`'s first
    argument. `None` means the operand is not a bare name — a literal, a call, an attribute — which
    the caller treats as a violation, because the watcher's only sanctioned target is a parameter.
    """
    tree = ast.parse(source)
    targets = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        attr = callee.attr if isinstance(callee, ast.Attribute) else None
        is_builtin_open = isinstance(callee, ast.Name) and callee.id == "open"

        if attr in ("write_text", "write_bytes"):
            operand = callee.value
        elif attr == "open" or is_builtin_open:
            arguments = list(node.args) + [keyword.value for keyword in node.keywords]
            if is_builtin_open:
                operand = node.args[0] if node.args else None
                arguments = arguments[1:]
            else:
                operand = callee.value
            modes = [
                argument.value
                for argument in arguments
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            ]
            if not any(set(mode) & set("awx+") for mode in modes):
                continue  # read-only `open` is not a write
        else:
            continue

        name = operand.id if isinstance(operand, ast.Name) else None
        targets.append((node.lineno, name))
    return sorted(targets)


def test_the_watcher_writes_only_the_stall_record():
    """EVERY WRITE RESOLVES TO THE `stall_record_path` PARAMETER (threat T-25-24).

    Never to the heartbeat — a watcher that edits the driver's own record destroys the one artifact
    that says where the run died — and never to a literal path, which would put the watcher's
    output somewhere no caller chose.
    """
    targets = _write_targets(_WATCHER_SOURCE)
    assert targets, "no write found at all; the guard would be passing vacuously"
    offenders = [(lineno, name) for lineno, name in targets if name != "stall_record_path"]
    assert offenders == [], (
        f"scripts/phase25_watch.py writes to something other than the stall_record_path "
        f"parameter at {offenders}. The heartbeat is opened READ-ONLY and the stall record is the "
        f"watcher's only output."
    )

    # And the heartbeat side is read-only by construction: the only call reaching it is `read_text`.
    assert "read_text" in _WATCHER_SOURCE


def test_the_never_act_guard_fires_on_a_planted_action(tmp_path):
    """THE GUARD'S OWN RED, on a SCRATCH COPY. The real file is never mutated."""
    planted_path = tmp_path / "phase25_watch_planted.py"
    planted_source = _WATCHER_SOURCE + (
        "\n\nimport subprocess\n\n\n"
        "def _restart_the_sweep():\n"
        '    subprocess.run(["launchctl", "kickstart", "-k", "x"])\n'
    )
    planted_path.write_text(planted_source, encoding="utf-8")

    findings = _action_calls(planted_source)
    assert len(findings) == 1, findings
    lineno, name = findings[0]
    assert name == "run", "the CALL is `run`; `launchctl` is a string argument, not an identifier"
    assert lineno == len(planted_source.splitlines())

    message = _action_failure_message(findings, str(planted_path))
    assert str(planted_path) in message
    assert f":{lineno}" in message and "'run'" in message and "D-10" in message, message

    # The import lock fires on the same plant, independently of the call walker.
    assert "subprocess" in _imported_modules(planted_source)

    # AND THE PLANT IS ONLY IN `tmp_path`. A RED watched by mutating a real repo file is a RED that
    # can be left behind — `tests/test_phase25_epsilon.py`'s register.
    completed = subprocess.run(
        ["git", "status", "--porcelain", "scripts/"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout == "", (
        f"watching the RED must leave no residue in scripts/: {completed.stdout!r}"
    )
    assert _action_calls(_WATCHER_SOURCE) == [], "the real watcher is still clean"


def test_a_detected_stall_is_a_successful_run(tmp_path):
    """A DETECTED STALL EXITS 0, THROUGH A REAL `main()` INVOCATION (threat T-25-25).

    A non-zero exit would make a LaunchAgent-managed watcher look like a crashing job to whatever
    supervises it, and would invite exactly the automatic remediation D-16 forbids. Detecting a
    stall is the watcher working, not the watcher failing.
    """
    heartbeat = tmp_path / "heartbeat.jsonl"
    heartbeat.write_text(_beat() + "\n", encoding="utf-8")
    stall = tmp_path / "stall.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            str(_WATCHER_PATH),
            "--heartbeat",
            str(heartbeat),
            "--stall-record",
            str(stall),
            "--now",
            "2026-08-31T00:06:00+00:00",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, (completed.returncode, completed.stderr)
    assert "STALL" in completed.stdout and "action_taken: 'none'" in completed.stdout
    written = _records(stall)
    assert len(written) == 1 and written[0]["action_taken"] == "none"
    assert written[0]["last_beat"]["draw_index"] == 7


# =================================================================================================
# ===== (c) N IS ASSERTED AGAINST ITS SOURCES, NOT AGAINST ITSELF =====
# =================================================================================================


def test_n_is_derived_from_the_measured_table():
    """RECOMPUTE THE TABLE FROM THE COMMITTED RECORDS AND COMPARE UNDER EXACT `==`.

    A test that read `N_DERIVATION` and compared it to `N_DERIVATION` would be green for a module
    that invented every number. Every literal below comes back out of `results/phase23_cost.json`
    and `results/phase23_never_taught.json` at full stored precision, per that record's own
    `published_figure_rule`: *"A rounding is not a figure this phase publishes."*
    """
    derivation = phase25_watch.N_DERIVATION
    cost = json.loads(_COST_RECORD.read_text(encoding="utf-8"))
    per_shape = {row["shape"]: row for row in cost["generation"]["per_shape"]}

    # --- REGIME 1: the MEASURED gaps, from the tracked seed-1337 mirror -------------------------
    never_taught = json.loads(_NEVER_TAUGHT_RECORD.read_text(encoding="utf-8"))
    seed_block = never_taught["per_seed"][0]
    assert seed_block["draws_per_question"] == derivation["measured_seed1337"]["k"] == 16
    measured = {
        row["shape"]: row["minutes"] * 24 / row["prompts"] for row in seed_block["per_shape"]
    }
    assert derivation["measured_seed1337"]["gap_24_prompt_minutes"] == measured
    worst_measured_shape = max(measured, key=measured.get)
    assert worst_measured_shape == derivation["measured_seed1337"]["worst_shape"] == "A3"
    assert derivation["worst_24_prompt_gap_measured_minutes"] == measured[worst_measured_shape]

    # --- REGIME 2: the no-EOS CEILING gaps ------------------------------------------------------
    ceiling = {shape: 24 * 16 / row["draws_per_min_ceiling"] for shape, row in per_shape.items()}
    assert derivation["ceiling_no_eos"]["gap_24_prompt_minutes"] == ceiling
    worst_ceiling_shape = max(ceiling, key=ceiling.get)
    assert worst_ceiling_shape == derivation["ceiling_no_eos"]["worst_shape"] == "A1-mild"
    worst_ceiling = ceiling[worst_ceiling_shape]
    assert derivation["worst_24_prompt_gap_ceiling_minutes"] == worst_ceiling
    assert round(worst_ceiling, 2) == 5.03

    # --- REGIME 3: D-11's K=48 promotion --------------------------------------------------------
    projection = 24 * 48 / per_shape[worst_ceiling_shape]["draws_per_min_ceiling"]
    assert derivation["full_fidelity_projection"]["worst_24_prompt_gap_minutes"] == projection
    assert round(projection, 1) == 15.1

    # --- THE TRUE WORST CASE: training, which emits no per-shape line at all ---------------------
    n8_seconds = cost["training"]["dp_n8"]["seconds_total"]
    n64_seconds = cost["training"]["dp_n64"]["seconds_total"]
    assert derivation["training_legs"]["dp_n8_seconds"] == n8_seconds
    assert derivation["training_legs"]["dp_n64_seconds"] == n64_seconds
    assert derivation["dp_n8_training_minutes"] == n8_seconds / 60.0
    assert derivation["dp_n64_training_minutes"] == n64_seconds / 60.0
    assert round(n8_seconds, 1) == 205.4

    # THE PROSE'S "23.06 min" IS A ROUNDING OF A ROUNDING, AND THE TEST PINS THE TRUE READING
    # RATHER THAN REPRODUCING IT. 25-CONTEXT.md (D-14), 25-VALIDATION.md and 25-05-PLAN.md all
    # quote "1383.3 s = 23.06 min": the seconds were rounded to 1383.3 first and 23.055 was then
    # rounded up BY HAND. From the record's own full-precision leaf,
    # 1383.276182374917 / 60 = 23.0546 -> 23.05, and even the intermediate 1383.3 / 60 = 23.055
    # rounds to 23.05 under Python's round-half-to-even. `phase23_cost.json` states the governing
    # rule in its own words — *"A rounding is not a figure this phase publishes."* — so the module
    # pins the full float and never quotes a two-decimal 23.06.
    assert round(n64_seconds / 60.0, 2) == 23.05
    assert round(round(n64_seconds, 1) / 60.0, 2) == 23.05
    assert derivation["dp_n64_training_minutes_two_decimal_note"].startswith("23.05, NOT 23.06")

    # --- THE WINDOW THE WALL-CLOCK BEAT EXISTS TO OPEN -------------------------------------------
    # D-16 derives N from the MEASURED worst-case gap. N sits above it and below the training leg.
    threshold = phase25_watch.STALL_THRESHOLD_MINUTES
    assert measured[worst_measured_shape] < threshold < n64_seconds / 60.0
    assert round(measured[worst_measured_shape], 2) == 3.78

    # AND THE HONEST PART, RECORDED RATHER THAN SMOOTHED: N is *below* the ceiling-regime gap and
    # far below the K=48 projection. Under an EVENT-driven beat, N = 5 would false-fire in both.
    # That gap between the regimes is exactly what forces the beat to be a wall-clock timer.
    assert threshold < worst_ceiling < projection
    assert "wall-clock" in derivation["why_the_draw_gaps_do_not_bound_n"]


def test_the_event_driven_alternative_is_computed_from_the_same_records():
    """WHY THE BEAT IS WALL-CLOCK, as arithmetic rather than as an assertion.

    An event-driven beat is silent for a whole training leg and only speaks again 24 prompts later,
    so its worst silence is the leg plus the first gap after it. Recomputed at both K rungs, that
    envelope is what would force N far coarser than the draw loop can itself resolve.
    """
    derivation = phase25_watch.N_DERIVATION
    alternative = derivation["event_driven_alternative"]

    training = derivation["dp_n64_training_minutes"]
    gap_16 = derivation["worst_24_prompt_gap_ceiling_minutes"]
    gap_48 = derivation["full_fidelity_projection"]["worst_24_prompt_gap_minutes"]

    assert alternative["max_silence_at_curve_k_minutes"] == training + gap_16
    assert alternative["max_silence_at_full_fidelity_k_minutes"] == training + gap_48
    assert alternative["minimum_threshold_minutes_envelope"] == (
        training + gap_16,
        training + gap_48,
    )
    assert alternative["coarser_than_ceiling_gap_factor_envelope"] == (
        (training + gap_16) / gap_16,
        (training + gap_48) / gap_16,
    )

    # The round figure a human quotes is INSIDE the measured envelope and is labelled as a round
    # figure, so it is never mistaken for a measurement.
    stated = alternative["stated_round_figure_minutes"]
    low, high = alternative["minimum_threshold_minutes_envelope"]
    assert low < stated < high
    assert round(stated / gap_16) == 7, "the '7x coarser' figure, over the ceiling-gap"

    # D-08's 44 points are 2 x (16 sigma + 6 ratios); half of them carry an n=64 training leg.
    assert alternative["n64_training_legs"] == 22
    assert 2 * (16 + 6) == 44


def test_the_contract_is_pinned_as_data():
    """The beat's rate, its fields and the missed-beat arithmetic are constants, not comments."""
    assert phase25_watch.HEARTBEAT_SECONDS == 60
    assert phase25_watch.HEARTBEAT_FIELDS == ("utc", "point", "stage", "shape", "draw_index")
    assert phase25_watch.STALL_THRESHOLD_MINUTES == 5

    provenance = phase25_watch.HEARTBEAT_SECONDS_PROVENANCE
    assert provenance["missed_beats_at_threshold"] == (
        phase25_watch.STALL_THRESHOLD_MINUTES * 60 // phase25_watch.HEARTBEAT_SECONDS
    )
    assert "OUTER loop" in provenance["emitted_from"]

    # Detection latency, recomputed against the run's own envelope rather than carried over.
    derivation = phase25_watch.N_DERIVATION
    low_hours, high_hours = derivation["run_envelope_hours"]
    assert derivation["detection_latency_fraction_of_run"] == (
        phase25_watch.STALL_THRESHOLD_MINUTES / (low_hours * 60.0)
    )
    assert derivation["detection_latency_percent_envelope"] == (
        phase25_watch.STALL_THRESHOLD_MINUTES / (high_hours * 60.0) * 100,
        phase25_watch.STALL_THRESHOLD_MINUTES / (low_hours * 60.0) * 100,
    )
