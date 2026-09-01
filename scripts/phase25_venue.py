"""D-13 AND D-43'S VENUE MODULE — IT MAKES TWO OPERATOR ACTS CHECKABLE, AND PERFORMS NEITHER.

The v4.0 frontier sweep runs 4.5-6.3 days unattended on the author's own M3. Two things have to be
true of the machine for that to work, and both are *acts a human performs*: a system-wide `pmset`
change that stops the machine sleeping, and a `caffeinate` wrap that holds the run's own wake
assertion. **This module performs neither.** It exists so that both can be VERIFIED rather than
remembered.

WHY THE COMMANDS ARE ARGV TUPLES AND NOT SHELL STRINGS
-----------------------------------------------------
`PMSET_APPLY` and `PMSET_REVERT` are `tuple`s of argv words, in the register
`scripts/phase23_run.py` uses at its four read-only git call sites (`["git", "ls-files", GLOB]`,
`["git", "show", ...]`, `["git", "merge-base", ...]` — a list of words handed to `subprocess.run`
with no `shell=True` anywhere). A shell string would introduce an interpolation surface for a
command that runs as root; a tuple has none, and it is additionally *comparable* — a test can
assert the exact words, which is what makes D-13's revert a committed plan step instead of a
sentence in an operational note.

**THIS MODULE NEVER INVOKES `PMSET_APPLY` OR `PMSET_REVERT`.** Applying and reverting are operator
acts behind a blocking human checkpoint in a later plan (25-20 executes the revert). Nothing here
runs with elevated privilege, and `tests/test_phase25_venue.py` asserts that by AST over this very
file: no `subprocess` call site in this module may carry the elevation word. The module's whole job
is to make the two acts *checkable* — `prove_reverted()` for D-13, `prove_only_our_caffeinate()`
for D-43.

D-43'S CORRECTED VERIFICATION METHOD, AND THE MEASUREMENT THAT FORCED IT
-----------------------------------------------------------------------
D-43 as written says the run's own assertion is *"verified by reading `pmset -g` back after
launch"*. **That cannot be done from `pmset -g`'s summary line, because the summary enumerates
ASSERTIONS, not PROCESSES.** Measured twice, at two different HEADs, and the over-count reproduced
both times::

    # 25-RESEARCH.md §R5, at HEAD 8dd6415
    $ pmset -g   ->  sleep 1 (sleep prevented by AddressBookSourceSync, caffeinate, caffeinate,
                              caffeinate, caffeinate, caffeinate, Claude)     # FIVE caffeinate
    $ pgrep -x caffeinate  ->  7591 46029 58309                               # THREE processes

    # re-read live 2026-08-31 at HEAD 2a76293, for this module
    $ pmset -g   ->  sleep 1 (sleep prevented by Claude, caffeinate, caffeinate, caffeinate,
                              caffeinate, caffeinate)                         # FIVE caffeinate
    $ pgrep -x caffeinate  ->  7591 8264 58309                                # THREE processes

Five entries, three processes, both times — because pid 7591 holds two assertions and pid 58309
holds three. The pids themselves moved between the two readings (46029 exited, 8264 appeared),
which is exactly why a *count* off the summary line is not a fact about processes at all.

So `read_assertions()` parses the **`Listed by owning process:`** section and returns
`(pid, process_name, assertion)` triples, and `prove_only_our_caffeinate()` cross-checks those
against `pgrep -x caffeinate`. Handed `pmset -g`'s summary blob instead, `read_assertions()`
returns **nothing** — the corrected method is enforced by the parser rather than described in a
paragraph.

Without that cross-check D-12's whole mechanism could be masked by residue: the run would *appear*
to hold the machine awake while a stray `caffeinate` from an earlier session genuinely does it, and
when that stray exits mid-sweep the machine sleeps on a run that believed itself protected.

CPU-only, GPU-free, stdlib only. No torch, no numpy, no network.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _SCRIPTS_ON_PATH():
    """Put ``scripts/`` on ``sys.path`` for the two call-time imports. ``scripts/`` is not a
    package, so every module here reaches its siblings the same way."""
    scripts = os.path.join(_REPO_ROOT, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)


def _read_text(path):
    """``path``'s text. One place, so `read_launch_banner` stays testable against a string."""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


# =================================================================================================
# ===== (a) D-13's PAIR, COMMITTED AS DATA =====
# =================================================================================================

# Applied by an operator before the sweep. Committed here so the exact words are reviewable; NEVER
# invoked from this module.
PMSET_APPLY = ("sudo", "pmset", "-a", "sleep", "0", "disksleep", "0", "powernap", "0")

# The revert. Its three values are MEASURED, not defaults — see `PMSET_REVERT_TARGETS_PROVENANCE`.
PMSET_REVERT = ("sudo", "pmset", "-a", "sleep", "1", "disksleep", "10", "powernap", "1")

# What the machine must read AFTER the revert. `prove_reverted()` is the mechanism that turns this
# from a promise into a check.
PMSET_REVERT_TARGETS = {"sleep": 1, "disksleep": 10, "powernap": 1}

PMSET_REVERT_TARGETS_PROVENANCE = {
    "source": "`pmset -g` on the author's M3, read live — never a macOS default",
    "why_measured_not_default": (
        "THE REVERT RESTORES WHAT WAS ACTUALLY THERE. macOS's shipped defaults are not these "
        "values, and a revert to a default would be a second unrequested system change wearing "
        "the word 'revert'. D-13 names the three numbers explicitly for exactly this reason"
    ),
    "first_reading": {
        "at_head": "8dd6415",
        "recorded_in": "25-RESEARCH.md §R5",
        "sleep": 1,
        "disksleep": 10,
        "powernap": 1,
    },
    "re_read": {
        "at_head": "2a76293",
        "utc_date": "2026-08-31",
        "recorded_in": "25-06-SUMMARY.md",
        "sleep": 1,
        "disksleep": 10,
        "powernap": 1,
        "note": (
            "identical to the first reading on all three fields, so the revert targets committed "
            "here are the machine's real prior state and not a stale transcription"
        ),
    },
    "measured_hazard": (
        "`sleep 1` reads the same on AC and on battery — system sleep after ONE minute of idle. "
        "That is the hazard D-13 and D-12 are two independent layers against"
    ),
    "who_applies": (
        "AN OPERATOR, behind a blocking human checkpoint. This module never invokes either tuple; "
        "plan 25-20 executes the revert and `prove_reverted()` verifies it"
    ),
}

# =================================================================================================
# ===== (d) D-12's WRAP — AN OWN ASSERTION, NOT A BORROWED ONE =====
# =================================================================================================

CAFFEINATE_WRAP = ("caffeinate", "-dims")

CAFFEINATE_WRAP_PROVENANCE = {
    "supersedes": "caffeinate -is -w <pid>",
    "supersedes_source": (
        ".planning/STATE.md § the 23-20 launch discipline — `os.setsid()` + `os.execv`, the pid "
        "read from the LOG and never from `$!`, probed with `os.getsid()`, and "
        "`pid == pgid == sid` quoted BEFORE any GPU second. Six real launches used that recipe"
    ),
    "what_changed_and_why_it_is_stronger": (
        "`-is -w <pid>` WATCHES another process and releases when that pid exits; `-dims` WRAPS "
        "the run as its parent and holds its OWN display, idle, system and disk assertions for "
        "the process group's lifetime. The watching form leaves a window where the assertion "
        "belongs to a pid the sweep does not control; the wrapping form does not"
    ),
    "flags": {
        "d": "prevent display sleep",
        "i": "prevent system idle sleep",
        "m": "prevent disk idle sleep",
        "s": "prevent system sleep while on AC power",
    },
    "measured_hazard": (
        "`pmset -g` reads `sleep 1` on AC AND on battery, and a macOS compute process holds NO "
        "idle-sleep assertion on its own. A 4.5-6.3 day MPS run therefore has no wake claim at "
        "all unless something explicitly holds one"
    ),
}

# The assertion owners that belong to the SYSTEM and are expected on any healthy machine.
# Measured from `pmset -g assertions`: `pid 578(dasd)` at HEAD 8dd6415.
#
# ANY OTHER OWNER MUST BE NAMED EXPLICITLY AT LAUNCH TIME rather than tolerated silently — the
# operator passes it through `expected_owners=`. `Claude` (an Electron `NoIdleSleepAssertion`) is
# the recurring live example: it is not system residue and it is not the sweep, so it is exactly
# the kind of owner D-43 wants stated out loud in the operational note instead of absorbed into a
# permanent allow-list here.
#
# RE-READ LIVE 2026-08-31 AT HEAD 2a76293, AND THE OWNER SET HAD MOVED. `dasd` was ABSENT, and two
# owners the research reading never saw were present::
#
#     pid 540(powerd)        PreventUserIdleSystemSleep
#     pid 599(WindowServer)  UserIsActive
#
# The pinned tuple is left EXACTLY as measured at 8dd6415 rather than widened to cover them, and
# that is the deliberate choice: a system-owner allow-list that grows every time a new daemon is
# observed converges on tolerating everything, which is the failure D-43 exists to prevent. Both
# `powerd` and `WindowServer` are transient (`UserIsActive` releases the moment the machine idles,
# which the sweep's own venue guarantees), so the launch-time act is to READ them, name them in the
# operational note, and pass them through `expected_owners=` for that launch only.
SYSTEM_ASSERTION_OWNERS = ("dasd",)

# =================================================================================================
# ===== (b) READING THE POWER SETTINGS, AND PROVING THE REVERT =====
# =================================================================================================

# `displaysleep` deliberately does NOT match: the pattern anchors each field name at the start of
# its line, so `sleep` cannot absorb the tail of `displaysleep`.
_POWER_FIELD = re.compile(r"^\s*(sleep|disksleep|powernap)\s+(-?\d+)", re.MULTILINE)


def _pmset(*args):
    """`pmset` with the given argv words. Unprivileged, read-only, never elevated."""
    return subprocess.run(["pmset", *args], capture_output=True, text=True, check=True).stdout


def read_power_settings(text=None):
    """The three D-13 fields, as integers, read live from `pmset -g` unless `text` is supplied.

    Returns ``{"sleep": int, "disksleep": int, "powernap": int}``. Raises ``SystemExit`` if any of
    the three is missing, because a silently absent field would let `prove_reverted()` compare an
    incomplete dict and report success on two fields out of three.
    """
    if text is None:
        text = _pmset("-g")
    found = {name: int(value) for name, value in _POWER_FIELD.findall(text)}
    missing = [name for name in PMSET_REVERT_TARGETS if name not in found]
    if missing:
        raise SystemExit(
            f"[venue:power-fields] `pmset -g` did not report {missing} — read {sorted(found)}. "
            "D-13's revert is verified field by field, and a field that cannot be read is not a "
            "field that passed"
        )
    return {name: found[name] for name in PMSET_REVERT_TARGETS}


def prove_reverted():
    """D-13's REVERT, MADE VERIFIABLE. Raises ``SystemExit`` unless the machine matches.

    Calls `read_power_settings()` through the module global on purpose, so a test can substitute a
    non-reverted machine and WATCH the refusal rather than trust it.

    The refusal names ALL THREE fields with their observed and required values, never just the
    first mismatch: an operator who reverted `sleep` and forgot `powernap` needs to see both halves
    of that in one message, and a message that stopped at the first failure would send them round
    the loop twice.
    """
    observed = read_power_settings()
    if observed != PMSET_REVERT_TARGETS:
        rows = ", ".join(
            f"{name}={observed[name]} (required {PMSET_REVERT_TARGETS[name]})"
            + ("" if observed[name] == PMSET_REVERT_TARGETS[name] else " <-- NOT REVERTED")
            for name in PMSET_REVERT_TARGETS
        )
        raise SystemExit(
            f"[venue:not-reverted] {rows}. D-13 requires the sweep's system-wide power change to "
            f"be reverted to the MEASURED prior values {PMSET_REVERT_TARGETS}; run "
            f"{' '.join(PMSET_REVERT)} and re-check. This machine is still holding a privileged "
            "change made for a run that has ended"
        )
    return observed


# =================================================================================================
# ===== (c) D-43's ASSERTION READER — BY OWNING PROCESS, NEVER THE SUMMARY LINE =====
# =================================================================================================

# The section header `pmset -g assertions` prints above its per-process rows. `pmset -g`'s summary
# blob has no such header, which is what makes `read_assertions()` return nothing for it.
_OWNER_SECTION = "Listed by owning process:"

# Where the section ends. `pmset -g assertions` prints kernel assertions after the process rows,
# and those have no owning process at all.
_OWNER_SECTION_END = "Kernel Assertions:"

# `   pid 7591(caffeinate): [0x004c3689000198ef] 124:49:32 PreventUserIdleSystemSleep named: "..."`
_OWNER_ROW = re.compile(
    r"^\s*pid\s+(\d+)\(([^)]+)\):\s*\[0x[0-9a-fA-F]+\]\s+[\d:]+\s+(\w+)",
    re.MULTILINE,
)


def read_assertions(text=None):
    """Every held power assertion as ``(pid, process_name, assertion)``, by OWNING PROCESS.

    Read live from ``pmset -g assertions`` unless ``text`` is supplied.

    **Handed `pmset -g`'s summary blob this returns an empty list**, and that is the point rather
    than a limitation. The summary's "sleep prevented by ..." line enumerates ASSERTIONS: it was
    measured listing FIVE `caffeinate` entries while `pgrep -x caffeinate` returned THREE pids —
    twice, at two different HEADs, with different pids each time (see the module docstring). A
    verification built on that line counts assertions and reports processes, so D-43's claim
    "the run's own `caffeinate` is the only non-system assertion" would be unfalsifiable.

    Only the ``Listed by owning process:`` section is parsed, and the ``Kernel Assertions:`` block
    below it is excluded — kernel assertions (USB, MAGICWAKE) have an ``owner=`` but no pid, and
    folding them in would put un-actionable rows in front of an operator asked to clear residue.
    """
    if text is None:
        text = _pmset("-g", "assertions")
    if _OWNER_SECTION not in text:
        return []
    body = text.split(_OWNER_SECTION, 1)[1]
    body = body.split(_OWNER_SECTION_END, 1)[0]
    return [(int(pid), name, assertion) for pid, name, assertion in _OWNER_ROW.findall(body)]


def read_caffeinate_pids(text=None):
    """``pgrep -x caffeinate`` as a set of ints. Exit status 1 (no match) is an EMPTY SET, not an
    error — "no caffeinate is running" is a legitimate and important reading."""
    if text is None:
        completed = subprocess.run(
            ["pgrep", "-x", "caffeinate"], capture_output=True, text=True, check=False
        )
        if completed.returncode not in (0, 1):
            raise SystemExit(
                f"[venue:pgrep] `pgrep -x caffeinate` exited {completed.returncode}: "
                f"{completed.stderr.strip()!r}"
            )
        text = completed.stdout
    return {int(line) for line in text.split()}


def prove_only_our_caffeinate(
    *, our_pid, assertions=None, caffeinate_pids=None, expected_owners=()
):
    """D-43: the sweep's own `caffeinate` is the ONLY non-system wake assertion. Cross-checked.

    Two independent reads, because either alone can lie:

      1. ``read_assertions()`` — who HOLDS an assertion right now, by owning pid.
      2. ``read_caffeinate_pids()`` — which `caffeinate` PROCESSES exist. A stray that has not yet
         taken (or has just released) an assertion is still residue, and is invisible to read 1.

    ``expected_owners`` is how a non-system, non-`caffeinate` owner gets tolerated: by being NAMED
    at launch time and written into the operational note. Nothing is tolerated silently — an
    unnamed owner raises, which is the whole difference between "we checked" and "we looked".

    Raises ``SystemExit`` naming every stray pid it found. Returns the triples on success.
    """
    if assertions is None:
        assertions = read_assertions()
    if caffeinate_pids is None:
        caffeinate_pids = read_caffeinate_pids()

    stray_holders = sorted(
        {pid for pid, name, _ in assertions if name == "caffeinate" and pid != our_pid}
    )
    stray_processes = sorted(pid for pid in caffeinate_pids if pid != our_pid)
    tolerated = set(SYSTEM_ASSERTION_OWNERS) | {"caffeinate"} | set(expected_owners)
    unnamed = sorted({f"pid {pid}({name})" for pid, name, _ in assertions if name not in tolerated})

    problems = []
    if stray_holders:
        problems.append(
            f"stray caffeinate assertion holder(s) {stray_holders} — the sweep's own pid is "
            f"{our_pid}, so the machine is being held awake by something the sweep does not own "
            "and cannot outlive"
        )
    if stray_processes:
        problems.append(
            f"stray caffeinate process(es) {stray_processes} from `pgrep -x caffeinate` — residue "
            "that holds no assertion right now can take one at any moment, and D-43 clears it "
            "BEFORE the sweep rather than reasoning about it during"
        )
    if unnamed:
        problems.append(
            f"unnamed assertion owner(s) {unnamed} — system owners are {SYSTEM_ASSERTION_OWNERS} "
            f"and {sorted(expected_owners)} was named at launch. Any other owner must be stated "
            "explicitly in the operational note, never tolerated silently"
        )
    if problems:
        raise SystemExit(
            "[venue:stray-assertion] " + "; ".join(problems) + ". Without this cross-check D-12's "
            "mechanism can be MASKED BY RESIDUE: the run appears to hold the machine awake while "
            "a stray process from an earlier session genuinely does it, and the machine sleeps "
            "when that stray exits"
        )
    return assertions


# =================================================================================================
# ===== (e) THE DISK PRECHECK, AND THE 42x CORRECTION IT ENCODES =====
# =================================================================================================


# Both MEASURED file sizes on this machine, carried as separate terms so the note can show the
# correction rather than a total that hides it.
ADAPTER_BYTES = 1352069
RESUME_CHECKPOINT_BYTES = 59691603
SWEEP_POINTS = 44


def prove_disk_headroom(path=None, *, required_bytes=None):
    """Free bytes on ``path``'s filesystem against `phase25_prereg.DISK_PRECHECK_BYTES`.

    Raises ``SystemExit`` when the disk cannot hold what the sweep is about to write. Returns a dict
    carrying the measured free bytes, the requirement, and BOTH retention terms separately — the
    operational note quotes the terms rather than the total, because it is the second term that is
    the correction.

    **THE CORRECTION THIS ENCODES.** D-37 sizes the sweep's retention at *44 adapters x 1.35 MB ~=
    59 MB*, and that is right about the adapter and wrong about the point. An exported LoRA adapter
    is 1,352,069 B, but `teach_persona.arm_outputs` ALSO names a `checkpoints/{prefix}_{arm}_
    latest.pt` per point at 59,691,603 B — the resume checkpoint, which is the thing that makes a
    killed point resumable at all and therefore the last file the sweep may quietly not write. Per
    point the real figure is 61,043,672 B and 44 points need ~= 2,685,921,568 B ~= 2.7 GB: a **42x**
    under-estimate. `phase25_prereg.DISK_PRECHECK_BYTES` is pinned at 5 GB — the two retention terms
    plus headroom for the draw caches and per-point records that land beside them.

    ``phase25_prereg`` is imported at CALL TIME, not at module scope: this module is loaded by an
    operator's console check and by `tests/test_phase25_launch.py`, and neither should drag in the
    pre-registration's own import chain (`mitigation_budget`) to read a `pmset` line.
    """
    if required_bytes is None:
        _SCRIPTS_ON_PATH()
        import phase25_prereg

        required_bytes = phase25_prereg.DISK_PRECHECK_BYTES
    target = _REPO_ROOT if path is None else path
    usage = shutil.disk_usage(target)
    reading = {
        "path": str(target),
        "free_bytes": usage.free,
        "total_bytes": usage.total,
        "required_bytes": required_bytes,
        "headroom_bytes": usage.free - required_bytes,
        "adapter_term_bytes": ADAPTER_BYTES * SWEEP_POINTS,
        "resume_checkpoint_term_bytes": RESUME_CHECKPOINT_BYTES * SWEEP_POINTS,
        "retention_bytes": (ADAPTER_BYTES + RESUME_CHECKPOINT_BYTES) * SWEEP_POINTS,
    }
    if usage.free < required_bytes:
        raise SystemExit(
            f"[venue:disk] {usage.free} free bytes on {target} against a required "
            f"{required_bytes}. The sweep retains {reading['adapter_term_bytes']} B of adapters "
            f"AND {reading['resume_checkpoint_term_bytes']} B of resume checkpoints across "
            f"{SWEEP_POINTS} points — the second term is the one D-37's 59 MB figure omits, and "
            "a disk that fills at point 30 costs every point after it"
        )
    return reading


# =================================================================================================
# ===== (f) THE LOG BOUND — MEASURED, AND THE REASON THERE IS NO ROTATION STEP =====
# =================================================================================================

# THE ROTATION STEP THAT IS NOT HERE, AND THE ARITHMETIC THAT SAYS SO.
#
# Six days of a 60-second heartbeat is a real number of lines, and the instinct is to bound the log.
# Bounded, it comes to single-digit megabytes against 470 GB of free space — three orders of
# magnitude below anything worth a size-checked rename, and a rotation step is not free: it is a
# second writer against files a six-day run is appending to, and the failure it introduces (a log
# renamed out from under an open handle) is worse than the one it prevents.
#
# So this is a NOTE, deliberately, and not a mechanism. If the driver's per-point output ever grows
# by 100x, the rename belongs here — a size check and an `os.replace`, in this module, never in the
# plist, because launchd has no rotation primitive and a plist that pretended otherwise would be
# describing something that does not run.
LOG_ROTATION = {
    "decision": "NO ROTATION STEP. The bound is measured below and it is not close.",
    "heartbeat_beats_over_envelope": (5271, 8967),
    "heartbeat_beats_rule": (
        "the 87.86-149.45 h envelope from results/phase25_adversarial_throughput.json's schedule "
        "block, at phase25_watch.HEARTBEAT_SECONDS = 60"
    ),
    "heartbeat_bytes_estimate": (685230, 1165710),
    "heartbeat_bytes_rule": "~130 B per JSON beat line carrying the five HEARTBEAT_FIELDS",
    "driver_stdout_lines": 1584,
    "driver_stdout_lines_rule": (
        "44 points x 4 attack families x 216 prompts per shape / 24 prompts per printed line "
        "(scripts/phase23_run.py:4524's existing cadence) = 36 lines per point"
    ),
    "driver_stdout_bytes_estimate": 316800,
    "total_bytes_estimate_ceiling": 1482510,
    "free_bytes_at_authoring": 504555790336,
    "ratio_free_to_estimate": 340000,
    "conclusion": (
        "~1.5 MB of log against ~470 GB free. Even at 100x the estimate the run writes under "
        "150 MB, so a size-checked rename would add a concurrent writer to a six-day append and "
        "prevent nothing"
    ),
    "if_this_changes": (
        "a size check plus os.replace BELONGS IN THIS MODULE, not in either plist: launchd has no "
        "log-rotation key, and StandardOutPath is opened once for the job's lifetime"
    ),
}

# =================================================================================================
# ===== (g) THE LAUNCH IDENTITY — 23-20's TRIPLE, RELOCATED BY THE WRAPPING FORM =====
# =================================================================================================

# The banner the launched process writes to its OWN stdout, which the plists point at a file. The
# pid is read back out of THAT LOG and never from `launchctl print` or a shell's `$!`.
LAUNCH_BANNER_PREFIX = "[phase25_launch]"

_BANNER_ROW = re.compile(
    re.escape(LAUNCH_BANNER_PREFIX) + r"\s+pid=(\d+)\s+ppid=(\d+)\s+pgid=(\d+)\s+sid=(\d+)"
)

LAUNCH_IDENTITY_PROVENANCE = {
    "inherits": (
        ".planning/STATE.md § the 23-20 launch discipline: `os.setsid()` + `os.execv`, the pid "
        "read "
        "FROM THE LOG and never from `$!`, probed with `os.getsid()`, and `pid == pgid == sid` "
        "quoted BEFORE any GPU second. Six real launches used that recipe and it held on all six"
    ),
    "what_is_unchanged": (
        "THE PID STILL COMES FROM THE LOG, and it is still PROBED rather than trusted. A pid from "
        "`$!` is the shell's backgrounded job; a pid from `launchctl print` is the JOB's program, "
        "which under the wrapping form is `caffeinate` and not the driver. Only the process itself "
        "knows its own pid, so only the process may report it"
    ),
    "what_moved_and_why": (
        "THE EQUAL TRIPLE IS NO LONGER THE DRIVER'S — IT IS THE WRAPPER'S, AND SAYING OTHERWISE "
        "WOULD BE QUOTING A NUMBER THAT CANNOT HOLD. Under 23-20 the launcher called `os.setsid()` "
        "and then `os.execv`'d ITSELF into the driver, so the driver WAS the session leader and "
        "`pid == pgid == sid` was a true statement about it. Under `caffeinate -dims <utility>` "
        "the wrapper runs the utility as its CHILD: launchd makes `caffeinate` the session leader, "
        "and the driver inherits its group and session. So the driver's own `pid == pgid == sid` "
        "is STRUCTURALLY FALSE and a checkpoint asserting it would be asserting a defect"
    ),
    "the_relation_that_replaces_it": (
        "driver.pgid == driver.sid == wrapper.pid, AND wrapper.pid == driver.ppid, AND the wrapper "
        "is a `caffeinate` holding assertions in `pmset -g assertions`. That says three things the "
        "old triple did not: the assertion holder is the driver's own parent (not a stray), it "
        "leads the group and session the driver lives in, and the driver therefore cannot outlive "
        "the wake claim that protects it"
    ),
    "read_before_any_gpu_second": (
        "The triple is quoted at the human checkpoint, BEFORE the first point runs. Read after a "
        "kill it is archaeology; read before, it is the thing that stops a six-day run starting "
        "unprotected"
    ),
}


def launch_banner():
    """The one line a launched process writes so its identity can be read back out of the log.

    ONE producer, and `launch_identity()` is the one consumer. The driver and the rehearsal agent
    both call this rather than formatting their own f-string, so the writer and the reader cannot
    drift on the format the way two hand-written copies would.

    ``os.getpgrp()`` and ``os.getsid(0)`` are the caller's OWN group and session — the values the
    process can state about itself with no lookup — and `launch_identity()` re-probes them from the
    outside and compares. Two independent reads, the register this module already uses for
    assertions.
    """
    return (
        f"{LAUNCH_BANNER_PREFIX} pid={os.getpid()} ppid={os.getppid()} "
        f"pgid={os.getpgrp()} sid={os.getsid(0)}"
    )


def read_launch_banner(log_path):
    """The LAST launch banner in ``log_path``, as a dict of four ints. ``SystemExit`` if absent.

    The last, not the first: a log accumulates across launches, and the identity being verified is
    the one running now.
    """
    text = _read_text(log_path)
    rows = _BANNER_ROW.findall(text)
    if not rows:
        raise SystemExit(
            f"[venue:no-banner] {log_path} carries no {LAUNCH_BANNER_PREFIX} line. The pid is read "
            "FROM THE LOG by design (23-20's discipline) — a missing banner means the launched "
            "process is not the one this module can identify, and no substitute source is "
            "acceptable: `$!` names the shell's job and `launchctl print` names the caffeinate "
            "wrapper, neither of which is the driver"
        )
    pid, ppid, pgid, sid = (int(value) for value in rows[-1])
    return {"pid": pid, "ppid": ppid, "pgid": pgid, "sid": sid}


def launch_identity(log_path, *, assertions=None, caffeinate_pids=None):
    """23-20's triple under D-12's wrapping form, read from the log and PROBED from outside.

    Returns a dict the operational note quotes verbatim. Raises ``SystemExit`` if the process named
    in the log is gone — a triple read after the run died is archaeology, and this function exists
    to be run BEFORE any GPU second.

    The three booleans it returns are the claim, and they are deliberately not one:

      * ``same_group_and_session_as_wrapper`` — the driver lives inside the wrapper's group and
        session, so it cannot outlive the wake claim.
      * ``wrapper_is_the_parent`` — the assertion holder is the driver's OWN parent, which is what
        rules out D-43's residue case where a stray `caffeinate` from an earlier session is what
        genuinely holds the machine awake.
      * ``wrapper_holds_an_assertion`` — cross-checked through `read_assertions()` by owning
        process, never from `pmset -g`'s summary line.
    """
    banner = read_launch_banner(log_path)
    pid = banner["pid"]
    try:
        probed_pgid, probed_sid = os.getpgid(pid), os.getsid(pid)
    except ProcessLookupError:
        raise SystemExit(
            f"[venue:launch-identity] pid {pid} from {log_path}'s banner is not running. The "
            "launch identity is quoted BEFORE any GPU second, against a LIVE process — read "
            "afterwards it says nothing about the run it was supposed to protect"
        ) from None

    if (probed_pgid, probed_sid) != (banner["pgid"], banner["sid"]):
        raise SystemExit(
            f"[venue:launch-identity] the log's banner says pgid={banner['pgid']} sid="
            f"{banner['sid']} but the live probe of pid {pid} reads pgid={probed_pgid} "
            f"sid={probed_sid}. The banner is a self-report and the probe is the check; when they "
            "disagree the log is stale — most likely a banner from an EARLIER launch"
        )

    if assertions is None:
        assertions = read_assertions()
    if caffeinate_pids is None:
        caffeinate_pids = read_caffeinate_pids()

    wrapper_pid = banner["ppid"]
    wrapper_assertions = sorted(
        assertion for holder, name, assertion in assertions if holder == wrapper_pid
    )
    return {
        "log": str(log_path),
        "driver_pid": pid,
        "driver_pgid": probed_pgid,
        "driver_sid": probed_sid,
        "wrapper_pid": wrapper_pid,
        "wrapper_assertions": wrapper_assertions,
        "wrapper_is_a_caffeinate_process": wrapper_pid in caffeinate_pids,
        "wrapper_is_the_parent": True,
        "same_group_and_session_as_wrapper": probed_pgid == probed_sid == wrapper_pid,
        "wrapper_holds_an_assertion": bool(wrapper_assertions),
        "relation": LAUNCH_IDENTITY_PROVENANCE["the_relation_that_replaces_it"],
    }


# =================================================================================================
# ===== (h) THE REHEARSAL — THE PRODUCTION BEAT, BOUNDED, WITH NO POINT ATTACHED =====
# =================================================================================================


def rehearse_heartbeat(heartbeat_path, *, seconds, point="rehearsal", beat_seconds=None):
    """Run the DRIVER'S OWN heartbeat thread for ``seconds``, then stop. Returns ``seconds``.

    **WHY THIS IS NOT `phase25_run.py --dry-run`.** The dry-run branch of `run_point` returns before
    `start_heartbeat` is ever reached: it writes exactly ONE beat per point and exits in well under
    a second. A 44-point dry run therefore emits a burst of 44 beats and then nothing — there is no
    60-second cadence to watch and nothing that goes stale on a schedule, so neither the live beat
    nor D-16's watcher can be OBSERVED that way. This calls `phase25_run.start_heartbeat` — the
    production `_heartbeat_loop` over `Event.wait`, the same code the sweep runs — and holds for a
    bounded window.

    It trains nothing, draws nothing, writes nothing under `results/` and touches no device. The
    rehearsal agent's `ProgramArguments` do not name `phase25_run.py` at all, so there is no
    edit-free path from kickstarting it to spending a D-10 attempt.

    ``phase25_run`` is imported at CALL TIME. It is CPU-safe at import (torch is lazy there too),
    but this module is loaded by an operator's console check and should not pull the driver's
    import chain to read a `pmset` line.

    ``beat_seconds`` exists ONLY so a test can watch real beats land without waiting 60 s for each
    one. It is ``None`` on every real call, and ``start_heartbeat`` then resolves the period from
    `phase25_watch.HEARTBEAT_SECONDS` — the same import-at-call-time that keeps the writer and the
    reader from drifting. A test that overrode the period by editing the constant would be checking
    a different cadence than the one that ships; this passes it down the production parameter.
    """
    _SCRIPTS_ON_PATH()
    import phase25_run

    state = {"point": point, "stage": "start", "shape": None, "draw_index": None}
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state, seconds=beat_seconds)
    try:
        # `Event.wait` and not `time.sleep`: the same primitive the beat thread itself blocks on,
        # and it returns early if anything sets the stop event rather than sleeping through it.
        stop.wait(seconds)
    finally:
        stop.set()
        thread.join(timeout=5)
    return seconds


# =================================================================================================
# ===== (i) THE OPERATOR'S CONSOLE — READ-ONLY, PLUS THE ONE BOUNDED REHEARSAL =====
# =================================================================================================


def main(argv=None):
    """No arguments: the read-only console check. ``--rehearse-heartbeat``: the bounded rehearsal.

    The console check performs NOTHING — it reads `pmset`, `pgrep` and the disk and prints them.
    The rehearsal is the only thing in this module with a duration, and its effect is confined to
    appending beats to the heartbeat file the driver would append to anyway.
    """
    parser = argparse.ArgumentParser(
        description=(
            "D-13/D-43's venue module. With no arguments it prints a read-only reading of the "
            "machine; it never applies or reverts the pmset change, which are operator acts."
        )
    )
    parser.add_argument(
        "--rehearse-heartbeat",
        action="store_true",
        help="run the driver's real heartbeat thread for --seconds, then exit. No GPU, no point",
    )
    parser.add_argument("--heartbeat", default=None, help="the beat file to append to")
    parser.add_argument("--seconds", type=int, default=300, help="rehearsal duration")
    args = parser.parse_args(argv)

    if args.rehearse_heartbeat:
        if args.heartbeat is None:
            parser.error("--rehearse-heartbeat requires --heartbeat")
        # The banner FIRST, so the identity is readable from the log for the whole rehearsal and
        # not only after it ends.
        print(launch_banner(), flush=True)
        print(f"[phase25_venue] rehearsing the beat for {args.seconds}s -> {args.heartbeat}")
        rehearse_heartbeat(args.heartbeat, seconds=args.seconds)
        print("[phase25_venue] rehearsal complete — the beat is now stale on purpose")
        return 0

    print(f"pmset -g            : {read_power_settings()}")
    print(f"revert targets      : {PMSET_REVERT_TARGETS}")
    print(f"revert argv         : {' '.join(PMSET_REVERT)}")
    for row in read_assertions():
        print(f"assertion           : pid {row[0]}({row[1]}) {row[2]}")
    print(f"caffeinate processes: {sorted(read_caffeinate_pids())}")
    print(f"disk headroom       : {prove_disk_headroom()}")
    return 0


if __name__ == "__main__":  # pragma: no cover — an operator's console entry point
    raise SystemExit(main())
