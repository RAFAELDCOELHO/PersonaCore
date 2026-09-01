"""PLAN 25-14 — THE TWO LAUNCHAGENTS, AND THE OPERATIONAL NOTE'S BLOCKS.

D-12 puts an 87.86-149.45 h run behind a user LaunchAgent, and the two flags that make that safe
(`KeepAlive` false, `RunAtLoad` false) are one keystroke from being convenient instead of correct.
Everything here is CPU-only and **invokes no `launchctl`**: the plists are parsed as data and the
note is read as text. The claims that can only be made about a *running* machine — the applied
`pmset`, the cleared strays, the live triple, the watched stall record, the session boundary — are
made at a blocking human checkpoint and transcribed into the note, and §11 of the note is the
register of which ones are still outstanding.

**THE RAW XML IS READ AS WELL AS THE PARSED PLIST, DELIBERATELY.** `plistlib` discards comments, and
the single most important thing in the sweep agent is a comment: the reason `KeepAlive` is false.
A test that only parsed the plist would let that reason be deleted silently, and the flag with no
reason beside it is exactly the flag someone flips during an incident.

**WHY THE ABSOLUTE PATHS ARE CHECKED FOR CONSISTENCY AND NOT FOR EQUALITY.** A LaunchAgent has no
notion of a relative path, so all three plists carry this machine's absolute repo root. Asserting
that string equals `_ROOT` would pass here and fail on ubuntu-latest CI, where the checkout lives
somewhere else. What actually has to hold is that **every repo path in a plist is anchored on that
plist's own `WorkingDirectory`** — that is the property §O1's relative `git add` depends on, and it
is true on any machine.
"""

import ast
import json
import pathlib
import plistlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert; scripts/ is not a package)
import phase25_prereg  # noqa: E402  (same)
import phase25_venue  # noqa: E402  (same)
import phase25_watch  # noqa: E402  (same)

_ARTIFACTS = _ROOT / "artifacts"
_SWEEP_PLIST = _ARTIFACTS / "com.personacore.phase25.sweep.plist"
_WATCH_PLIST = _ARTIFACTS / "com.personacore.phase25.watch.plist"
_REHEARSAL_PLIST = _ARTIFACTS / "com.personacore.phase25.rehearsal.plist"
_ALL_PLISTS = (_SWEEP_PLIST, _WATCH_PLIST, _REHEARSAL_PLIST)

_NOTE = _ROOT / "results" / "phase25_operational_note.md"


def _plist(path):
    with path.open("rb") as handle:
        return plistlib.load(handle)


def _xml(path):
    return path.read_text(encoding="utf-8")


# =================================================================================================
# ===== (a) THE TWO FLAGS THAT KEEP AN UNATTENDED RUN COMPATIBLE WITH D-10 =====
# =================================================================================================


def test_the_sweep_agent_has_keepalive_false_with_its_reason():
    """D-12/D-10: no self-healing agent, and the reason survives beside the flag.

    Two assertions, and the second is the one that rots. `KeepAlive is False` is checked from the
    parsed plist; the reason is checked from the RAW XML, in the text that precedes the key,
    because `plistlib` throws comments away. `is False` and not a truthiness check: a
    `<string>false</string>` would parse to the truthy `"false"` and pass a loose test while
    launchd read it as garbage.
    """
    assert _plist(_SWEEP_PLIST)["KeepAlive"] is False

    xml = _xml(_SWEEP_PLIST)
    before_the_key = xml.split("<key>KeepAlive</key>", 1)[0]
    # The LAST comment before the key, so a reason attached to some earlier key cannot satisfy this.
    preceding_comment = before_the_key.rsplit("<!--", 1)[-1]
    normalized = _prose.normalized(preceding_comment)

    assert "D-10" in normalized, (
        "the comment immediately above KeepAlive must name D-10. Without it the flag reads as a "
        f"tuning knob rather than the one-attempt rule's enforcement. Read:\n{normalized}"
    )
    # Case-folded for these two: the comment writes "ONE attempt" for emphasis, and a guard that
    # broke when someone stopped shouting would be measuring typography rather than the reason.
    for phrase in ("one attempt", "resume logic"):
        assert _prose.normalized(phrase) in normalized.lower(), (
            f"the reason beside KeepAlive must say why: {phrase!r} is missing from\n{normalized}"
        )


@pytest.mark.parametrize("path", _ALL_PLISTS, ids=lambda p: p.stem)
def test_both_agents_disable_run_at_load(path):
    """Loading is not starting. Neither agent may begin 87.86-149.45 h of GPU work at login."""
    assert _plist(path)["RunAtLoad"] is False


@pytest.mark.parametrize("path", _ALL_PLISTS, ids=lambda p: p.stem)
def test_no_agent_keeps_itself_alive(path):
    """The watcher and the rehearsal need it false for their own reasons — see each plist's own
    comment — but the shared one is D-10: nothing in this system may relaunch anything."""
    assert _plist(path)["KeepAlive"] is False


# =================================================================================================
# ===== (b) D-12's WRAPPER, AND THE REHEARSAL THAT CANNOT SPEND AN ATTEMPT =====
# =================================================================================================


def test_the_driver_is_wrapped_in_its_own_caffeinate():
    """D-12: the run holds its OWN assertions rather than borrowing a stray one."""
    argv = _plist(_SWEEP_PLIST)["ProgramArguments"]
    assert argv[0].endswith("caffeinate"), argv
    assert "-dims" in argv, argv
    assert any("phase25_run.py" in word for word in argv), argv
    # The wrapper is the FIRST word, not merely present: `caffeinate` anywhere else in the argv
    # would be an argument to something rather than the parent of everything.
    assert tuple(argv[:2]) == (argv[0], phase25_venue.CAFFEINATE_WRAP[1])


def test_the_rehearsal_agent_uses_the_identical_wrapper():
    """The rehearsal is only evidence about the sweep if the thing rehearsed is the same."""
    sweep = _plist(_SWEEP_PLIST)["ProgramArguments"]
    rehearsal = _plist(_REHEARSAL_PLIST)["ProgramArguments"]
    assert rehearsal[:2] == sweep[:2]


def test_the_rehearsal_agent_cannot_run_a_sweep_point():
    """THE HAZARD THIS FILE EXISTS AGAINST, ASSERTED.

    The alternative to a committed rehearsal plist is asking an operator to derive one by editing
    the installed sweep agent. A substitution that silently fails to match leaves them kickstarting
    the REAL 44-point sweep: 4.5-6.3 days of GPU work and, under D-10, an attempt spent. There must
    be no edit-free path from kickstarting the rehearsal to running a point.
    """
    argv = _plist(_REHEARSAL_PLIST)["ProgramArguments"]
    assert not any("phase25_run.py" in word for word in argv), argv
    assert any("phase25_venue.py" in word for word in argv), argv
    assert "--rehearse-heartbeat" in argv, argv


def test_the_rehearsal_runs_the_production_heartbeat(tmp_path):
    """`rehearse_heartbeat` beats through `phase25_run.start_heartbeat`, not a copy of it.

    Watched producing REAL beats rather than asserted structurally: the period is passed down the
    production `seconds=` parameter so the test observes the shipped code path at a cadence it can
    afford, instead of waiting 60 s per beat or editing the constant the driver reads.
    """
    heartbeat = tmp_path / "beat.jsonl"
    phase25_venue.rehearse_heartbeat(heartbeat, seconds=0.3, beat_seconds=0.05)

    beats = [
        json.loads(line) for line in heartbeat.read_text(encoding="utf-8").splitlines() if line
    ]
    assert len(beats) >= 2, beats
    for written in beats:
        assert set(written) == set(phase25_watch.HEARTBEAT_FIELDS), written


# =================================================================================================
# ===== (c) THE WATCHER'S OWN CADENCE, AND THE FILE THE TWO AGENTS SHARE =====
# =================================================================================================


def test_the_watcher_samples_at_or_below_its_own_threshold():
    """A watcher that sampled more slowly than the window it defines could sleep through it."""
    interval = _plist(_WATCH_PLIST)["StartInterval"]
    assert interval <= phase25_watch.STALL_THRESHOLD_MINUTES * 60, (
        f"StartInterval {interval}s exceeds STALL_THRESHOLD_MINUTES "
        f"({phase25_watch.STALL_THRESHOLD_MINUTES} min = "
        f"{phase25_watch.STALL_THRESHOLD_MINUTES * 60}s)"
    )


def test_the_watcher_passes_both_paths_explicitly():
    """No defaults: a path resolved independently in two processes is a drift surface."""
    argv = _plist(_WATCH_PLIST)["ProgramArguments"]
    assert "--heartbeat" in argv and "--stall-record" in argv, argv


def test_all_three_agents_name_the_same_heartbeat_file():
    """The sweep writes it, the rehearsal writes it, the watcher reads it. One literal, asserted
    equal across three files — which is a stronger guarantee than three defaults that happen to
    agree today."""
    beats = set()
    for path in _ALL_PLISTS:
        argv = _plist(path)["ProgramArguments"]
        beats.add(argv[argv.index("--heartbeat") + 1])
    assert len(beats) == 1, beats


# =================================================================================================
# ===== (d) THE SWEEP-ACTIVE FLAG AND THE WORKING DIRECTORY §O1 DEPENDS ON =====
# =================================================================================================


def test_the_sweep_agent_sets_the_sweep_active_flag():
    """D-44: a `pytest` run started during the sweep skips the MPS legs LOUDLY instead of
    contending for the device the sweep is saturating."""
    assert _plist(_SWEEP_PLIST)["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"


@pytest.mark.parametrize("path", _ALL_PLISTS, ids=lambda p: p.stem)
def test_the_working_directory_is_the_repo_root(path):
    """§O1's `git add` of a RELATIVE `results/...` path only resolves if the process starts here.

    Consistency, not equality — see this module's docstring. Every absolute path the plist names,
    other than the system `caffeinate`, must live under that plist's own `WorkingDirectory`, and
    that directory must be a checkout of this repository by name.
    """
    parsed = _plist(path)
    workdir = parsed["WorkingDirectory"]
    assert pathlib.Path(workdir).name == _ROOT.name, (workdir, _ROOT.name)

    named = [
        *parsed["ProgramArguments"],
        parsed["StandardOutPath"],
        parsed["StandardErrorPath"],
    ]
    for word in named:
        if not word.startswith("/") or word.startswith("/usr/"):
            continue
        assert word == workdir or word.startswith(workdir + "/"), (
            f"{word!r} is an absolute path outside this plist's WorkingDirectory {workdir!r}. "
            "A path anchored elsewhere resolves against a different checkout than the one §O1's "
            "point-record commit writes into"
        )


@pytest.mark.parametrize("path", _ALL_PLISTS, ids=lambda p: p.stem)
def test_every_agent_logs_to_a_file(path):
    """D-12: stdout/stderr to file. An agent whose output goes nowhere makes a six-day kill a
    zero-traceback mystery, which is the exact failure the heartbeat also exists against."""
    parsed = _plist(path)
    for key in ("StandardOutPath", "StandardErrorPath"):
        assert parsed[key].endswith((".out", ".err")), parsed[key]
    assert parsed["StandardOutPath"] != parsed["StandardErrorPath"]


def test_the_two_running_agents_do_not_share_a_log():
    """A watcher writing 8,640 'alive' lines into the sweep's log would bury the traceback the
    sweep's log exists to preserve."""
    logs = [_plist(path)["StandardOutPath"] for path in _ALL_PLISTS]
    assert len(set(logs)) == len(logs), logs


# =================================================================================================
# ===== (e) THE LAUNCH IDENTITY — 23-20's DISCIPLINE, RELOCATED AND SAID SO =====
# =================================================================================================


def test_the_driver_emits_its_own_launch_banner():
    """Only the process itself knows its own pid, so only it may report one.

    AST over the driver rather than by running it: `main()` runs sweep points, and a test that
    called it to observe a `print` would be a test that starts the sweep.
    """
    tree = ast.parse((_ROOT / "scripts" / "phase25_run.py").read_text(encoding="utf-8"))
    main = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    called = {
        node.func.attr
        for node in ast.walk(main)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "launch_banner" in called, sorted(called)


def test_the_banner_round_trips_through_the_log(tmp_path):
    """One producer, one consumer. The four numbers a process states about itself survive the
    log."""
    import os

    banner = phase25_venue.launch_banner()
    assert banner.startswith(phase25_venue.LAUNCH_BANNER_PREFIX)

    log = tmp_path / "agent.out"
    log.write_text(banner + "\n", encoding="utf-8")
    assert phase25_venue.read_launch_banner(log) == {
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "pgid": os.getpgrp(),
        "sid": os.getsid(0),
    }


def test_the_last_banner_wins(tmp_path):
    """A log accumulates across launches; the identity being verified is the one running now."""
    log = tmp_path / "agent.out"
    log.write_text(
        f"{phase25_venue.LAUNCH_BANNER_PREFIX} pid=11 ppid=12 pgid=13 sid=14\n"
        "some driver output\n"
        f"{phase25_venue.LAUNCH_BANNER_PREFIX} pid=21 ppid=22 pgid=23 sid=24\n",
        encoding="utf-8",
    )
    assert phase25_venue.read_launch_banner(log)["pid"] == 21


def test_a_log_with_no_banner_refuses(tmp_path):
    """No substitute source is acceptable: `$!` names the shell's job and `launchctl print` names
    the caffeinate wrapper, and neither is the driver."""
    log = tmp_path / "agent.out"
    log.write_text("[phase25_run] point started\n", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        phase25_venue.read_launch_banner(log)
    assert "no-banner" in str(excinfo.value)


def test_a_dead_pid_refuses_rather_than_returning_a_triple(tmp_path):
    """The triple is quoted BEFORE any GPU second, against a live process. Read afterwards it is
    archaeology, and a function that returned it anyway would let a dead run be reported as
    protected."""
    log = tmp_path / "agent.out"
    # PID 0 is never a normal user process; `os.getpgid(0)` means "the caller", so a real
    # not-running pid is needed. 2**31-1 is above every macOS and Linux pid_max.
    log.write_text(
        f"{phase25_venue.LAUNCH_BANNER_PREFIX} pid=2147483647 ppid=1 pgid=1 sid=1\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as excinfo:
        phase25_venue.launch_identity(log)
    assert "launch-identity" in str(excinfo.value)


def test_a_stale_banner_refuses(tmp_path):
    """The banner is a SELF-REPORT and the live probe is the CHECK. When they disagree the log is
    stale — most often a banner from an earlier launch of the same agent."""
    import os

    log = tmp_path / "agent.out"
    log.write_text(
        f"{phase25_venue.LAUNCH_BANNER_PREFIX} pid={os.getpid()} ppid=1 pgid=999999 sid=999999\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as excinfo:
        phase25_venue.launch_identity(log, assertions=[], caffeinate_pids=set())
    assert "launch-identity" in str(excinfo.value)


def test_the_identity_names_the_wrapper_as_the_assertion_holder(tmp_path):
    """The reading the operational note quotes, against INJECTED assertion reads.

    `assertions=` and `caffeinate_pids=` are passed rather than read from the machine so the test is
    a fact about the function and not about whatever happens to hold an assertion on the runner.
    """
    import os

    pid, ppid = os.getpid(), os.getppid()
    log = tmp_path / "agent.out"
    log.write_text(
        f"{phase25_venue.LAUNCH_BANNER_PREFIX} pid={pid} ppid={ppid} "
        f"pgid={os.getpgid(pid)} sid={os.getsid(pid)}\n",
        encoding="utf-8",
    )
    reading = phase25_venue.launch_identity(
        log,
        assertions=[(ppid, "caffeinate", "PreventUserIdleSystemSleep")],
        caffeinate_pids={ppid},
    )
    assert reading["driver_pid"] == pid
    assert reading["wrapper_pid"] == ppid
    assert reading["wrapper_is_a_caffeinate_process"] is True
    assert reading["wrapper_holds_an_assertion"] is True
    assert reading["same_group_and_session_as_wrapper"] == (
        os.getpgid(pid) == os.getsid(pid) == ppid
    )

    # And the RED half: a wrapper that holds nothing is reported as holding nothing.
    quiet = phase25_venue.launch_identity(log, assertions=[], caffeinate_pids=set())
    assert quiet["wrapper_holds_an_assertion"] is False
    assert quiet["wrapper_is_a_caffeinate_process"] is False


def test_the_provenance_names_the_relocation_of_the_equal_triple():
    """D-12 is an ESCALATION of 23-20, and the cost is that `pid == pgid == sid` stops being a true
    statement about the driver. Presenting the wrapping form as the same recipe would have the
    checkpoint assert a relation that is structurally false under it."""
    provenance = phase25_venue.LAUNCH_IDENTITY_PROVENANCE
    moved = _prose.normalized(provenance["what_moved_and_why"])
    assert "pid == pgid == sid" in moved
    assert _prose.normalized("STRUCTURALLY FALSE") in moved
    assert _prose.normalized("caffeinate -dims") in moved

    unchanged = _prose.normalized(provenance["what_is_unchanged"])
    assert _prose.normalized("FROM THE LOG") in unchanged

    relation = _prose.normalized(provenance["the_relation_that_replaces_it"])
    assert "driver.pgid == driver.sid == wrapper.pid" in relation


# =================================================================================================
# ===== (f) THE DISK PRECHECK, WITH THE OMITTED TERM SHOWN SEPARATELY =====
# =================================================================================================


def test_the_disk_precheck_shows_both_retention_terms():
    """D-37's 59 MB is right about the adapter and 42x wrong about the point. Both terms are
    carried separately so the note can show the correction rather than a total that hides it."""
    reading = phase25_venue.prove_disk_headroom()
    assert reading["required_bytes"] == phase25_prereg.DISK_PRECHECK_BYTES
    assert reading["adapter_term_bytes"] == 1352069 * 44
    assert reading["resume_checkpoint_term_bytes"] == 59691603 * 44
    assert reading["retention_bytes"] == 2685921568
    # The pre-registration's own derivation, re-derived rather than re-typed.
    assert str(reading["retention_bytes"]) in phase25_prereg.CANARY_RESERVATIONS[
        "disk_precheck_derivation"
    ].replace(",", "")
    assert reading["free_bytes"] > reading["required_bytes"]


def test_the_precheck_refuses_a_disk_that_cannot_hold_the_run():
    """Watched failing. A precheck that has never refused is a precheck nobody has tested."""
    with pytest.raises(SystemExit) as excinfo:
        phase25_venue.prove_disk_headroom(required_bytes=2**62)
    assert "venue:disk" in str(excinfo.value)


def test_no_log_rotation_step_exists_and_the_arithmetic_says_why():
    """The bound is three orders of magnitude below anything worth a size-checked rename, and a
    rotation step is not free: it is a second writer against a file a six-day run is appending
    to."""
    rotation = phase25_venue.LOG_ROTATION
    assert _prose.normalized("NO ROTATION STEP") in _prose.normalized(rotation["decision"])
    low, high = rotation["heartbeat_beats_over_envelope"]
    assert low < high
    assert rotation["total_bytes_estimate_ceiling"] < rotation["free_bytes_at_authoring"] / 1000


# =================================================================================================
# ===== (g) THE OPERATIONAL NOTE — ITS BLOCKS, AND ITS REGISTER OF WHAT IS STILL PENDING =====
# =================================================================================================

# Blocks that carry a MEASURED, quoted command output today.
_REQUIRED_BLOCKS = (
    "## 1. The before-state: `pmset -g`",
    "## 2. The assertion owners, by owning process",
    "## 3. Disk headroom against `DISK_PRECHECK_BYTES`",
    "## 5. The stall record, and that no action was taken",
    "## 6. The session boundary",
    "## 7. The revert obligation",
    "## 8. §O1 — the driver's git surface",
    "## 9. The deliberate change from 23-20",
    "## 10. Open risks before the sweep starts",
    "## 11. Pending measurements",
)

# Blocks whose figures can only be produced at the blocking human checkpoint. Each must be PRESENT,
# must say PENDING, and must be registered in §11 — so a half-finished note cannot read as a
# finished one, which is the failure mode an operational note has.
#
# §5 and §6 WERE here and were performed on 2026-09-01, so they moved up into `_REQUIRED_BLOCKS`.
# Their coverage did not evaporate with the move: leaving them here would assert the opposite of
# what the note now says, so `_MEASURED_AT_THE_CHECKPOINT` below replaces "says PENDING" with the
# stronger obligation — carry the figure the measurement produced, and say which way it came out.
_PENDING_BLOCKS = ("## 4. The launch identity, read before any GPU second",)

# A block that leaves §11 must arrive with its evidence. Each entry is (heading, tokens that can
# only be present if the measurement was actually taken and transcribed).
_MEASURED_AT_THE_CHECKPOINT = (
    (
        "## 5. The stall record, and that no action was taken",
        ('action_taken: "none"', "data/phase25_stall.jsonl", "71 of 71"),
    ),
    (
        "## 6. The session boundary",
        ("runs = 0", "last exit code = (never exited)", "kern.boottime", "does not survive"),
    ),
)


@pytest.fixture(scope="module")
def note():
    return _prose.normalized(_NOTE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("heading", _REQUIRED_BLOCKS)
def test_the_operational_note_carries_every_required_block(note, heading):
    assert _prose.normalized(heading) in note, heading


@pytest.mark.parametrize("heading", _PENDING_BLOCKS)
def test_every_unmeasured_block_says_so_and_is_registered(note, heading):
    """A block that moves out of §11 without a quoted command output beside it is a defect in the
    note, not a measurement."""
    assert _prose.normalized(heading) in note, heading
    body = _NOTE.read_text(encoding="utf-8").split(heading, 1)[1].split("\n## ", 1)[0]
    assert "PENDING" in body, heading


@pytest.mark.parametrize("heading,tokens", _MEASURED_AT_THE_CHECKPOINT)
def test_a_block_that_left_the_pending_table_carries_its_evidence(heading, tokens):
    """The note's own rule, enforced instead of stated: a block that moves out of §11 without a
    quoted command output beside it is a defect in the note, not a measurement. These two left the
    table on 2026-09-01, so each must still say PENDING nowhere and carry the reading that let it
    leave."""
    body = _NOTE.read_text(encoding="utf-8").split(heading, 1)[1].split("\n## ", 1)[0]
    assert "PENDING" not in body, heading
    for token in tokens:
        assert token in body, (heading, token)


def test_the_note_records_the_revert_obligation_and_names_its_verifier(note):
    """D-13: the revert is a COMMITTED plan step with a named executor and a named verifier. It
    does not depend on anyone remembering it."""
    for token in ("PMSET_REVERT", "prove_reverted", "25-20"):
        assert token in note, token
    for value in phase25_venue.PMSET_REVERT_TARGETS.values():
        assert str(value) in note
    assert " ".join(phase25_venue.PMSET_REVERT) in note


def test_the_note_uses_the_corrected_assertion_method(note):
    """D-43 CORRECTED: read by owning process, cross-checked against `pgrep`, and never from the
    summary line — with the measurement that forces it, not just the instruction."""
    assert "pmset -g assertions" in note
    assert "pgrep -x caffeinate" in note
    assert _prose.normalized("Listed by owning process") in note
    assert _prose.normalized("summary line was not used") in note
    # The reason, as the two measured disagreements rather than as an adjective. 5-vs-3 is the
    # over-count already reproduced twice; 5-vs-6 is this plan's own reading, and it says the
    # summary line does not even enumerate all ASSERTIONS.
    assert _prose.normalized("5-vs-3 gap") in note
    assert _prose.normalized("5-vs-6 gap") in note


def test_the_note_states_the_before_reading_matched_the_committed_revert_targets(note):
    """The checkpoint's STOP condition — if the machine does not read the committed targets, the
    revert would restore the wrong state — must be recorded as SATISFIED rather than skipped."""
    assert _prose.normalized("PMSET_REVERT_TARGETS") in note
    assert _prose.normalized("satisfied, not waived") in note


def test_the_note_carries_the_untested_draw_loop_as_an_open_risk(note):
    """25-11 found `_draw_one_shape` calling a method that does not exist; it would have raised on
    the first draw of the first point after up to 23 minutes of training. It is fixed, but every
    committed driver test takes the dry-run branch, so NO test reaches the live draw loop. Starting
    an unattended 87.86-149.45 h run with that gap open is the largest operational risk here, and a
    note that omitted it would be the note failing at its only job."""
    assert "_draw_one_shape" in note
    assert _prose.normalized("no test reaches the live draw loop") in note
    assert "6df1eba" in note


def test_the_note_is_tracked():
    """An operational note that lives only on the machine it describes is not a record."""
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "results/phase25_operational_note.md"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert tracked == "results/phase25_operational_note.md", tracked


def test_no_sweep_point_record_exists():
    """This plan changes machine state and builds artifacts. It runs NO point, and D-10 keys on the
    tracked record list, so an accidental point here would spend an attempt permanently."""
    import subprocess

    listed = subprocess.run(
        ["git", "ls-files", phase25_prereg.POINT_RECORD_GLOB],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert listed == [], listed
