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

import re
import subprocess

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


if __name__ == "__main__":  # pragma: no cover — an operator's read-only console check
    print(f"pmset -g            : {read_power_settings()}")
    print(f"revert targets      : {PMSET_REVERT_TARGETS}")
    print(f"revert argv         : {' '.join(PMSET_REVERT)}")
    for row in read_assertions():
        print(f"assertion           : pid {row[0]}({row[1]}) {row[2]}")
    print(f"caffeinate processes: {sorted(read_caffeinate_pids())}")
