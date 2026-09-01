"""PLAN 25-06 — D-44'S SKIP COUNT STATED IN ADVANCE, AND D-13'S REVERT PROVED COMMITTED.

23-VALIDATION.md's Pitfall 1: *a pass count with no skip count beside it is the warning sign.* A
green suite that silently skipped every MPS leg looks identical to one that ran them all, apart
from a number pytest does not even print when it is zero. So this file states the sweep-active skip
count **before the sweep launches** and makes the suite check itself against it.

THE RE-ENTRANCY BOUND — READ THIS BEFORE ADDING ANY SUBPROCESS CALL HERE
------------------------------------------------------------------------
Two tests below run the whole suite in a child process. ``pyproject.toml`` sets
``testpaths = ["tests"]``, so a bare ``pytest tests/`` child **re-collects this very file** and each
level spawns two more. **MEASURED on a two-file reproduction: with no exclusion the spawner ran at
levels 0, 1, 2, 3, 4, 5 and stopped only at an artificial tripwire; with the exclusion it ran at
level 0 and nothing else.** Unbounded, ``pytest tests/ -q`` never reports anything to parse — and
plan 25-17 runs a full suite **during** the 4.5-6.3 day sweep on this same M3, where a runaway
process tree destroys the wall clock this phase exists to measure.

The bound is **argv only**, funnelled through ONE helper so no call site can forget it:

  * ``_SUITE_TARGETS`` carries ``--ignore=tests/test_phase25_venue.py``
  * ``_run_inner_suite`` is the ONLY function here that spawns ``pytest``

``tests/test_phase25_venue.py::test_every_pytest_subprocess_is_funnelled`` enforces both by AST
walk, because this docstring names ``--ignore`` and ``pytest`` on purpose and a textual gate over
this file would go false-RED on its own prose.

**TWO THINGS THE EXCLUSION IS NOT.**

1. **It is NOT the skip the count test forbids.** ``test_the_sweep_active_skip_count_is_the_number_
   stated_in_advance`` must never be skipped for being slow — that test IS the number. ``--ignore``
   is an argv exclusion applied to the **child**; it skips nothing and contributes 0 to any count.
   (Note also that with no ``addopts`` in ``pyproject.toml`` a ``slow`` marker deselects nothing by
   default, so "mark it slow" would not be a bound on anything either.)
2. **It is NOT a pytest-config change.** ``pyproject.toml`` is asserted ``git diff --exit-code``
   byte-unchanged phase-wide (RPT-03): no ``addopts``, no marker registration, no
   ``[tool.pytest.ini_options]`` edit. The entire bound lives in ``_SUITE_TARGETS``.

**WHY EXCLUSION AND NOT A ``PERSONACORE_INNER_SUITE`` SKIPIF GUARD.** A guard would make the
guarded tests *skip inside the child*, so the child's skip count would exceed the number a human
gets from ``PERSONACORE_SWEEP_ACTIVE=1 pytest tests/ -q``. Plan 25-17 compares that human-facing
number against ``SWEEP_ACTIVE_EXPECTED_SKIPS`` **during the live sweep**, so the literal would be
right for one command and wrong for the other. Exclusion keeps **one** number: none of this file's
own tests are MPS-gated, so the excluded file contributes **0** skips either way and the inner and
outer counts are equal by construction.

**COST, stated so 25-17 is not surprised.** Exactly TWO tests here run a full inner suite, so this
plan's own ``pytest tests/ -q`` costs ~3x the suite, one level deep. **25-17 pays ~1x**: its argv is
``PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest tests/ --ignore=tests/test_phase25_venue.py
-q``, which drops both inner-suite spawners and touches no MPS leg while the sweep holds the device.

CPU-only, GPU-free. Every MPS-touching assertion goes through the register, never the device.
"""

import ast
import os
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase25_venue as venue  # noqa: E402  (needs the sys.path insert; scripts/ is not a package)

from test_phase23_mps_venue import (  # noqa: E402  (tests/ is not a package)
    _MPS_ABSENT_REASON,
    _MPS_PRESENT,
    _SWEEP_ACTIVE_REASON,
)

_THIS_FILE = pathlib.Path(__file__).resolve()
_SOURCE = _THIS_FILE.read_text(encoding="utf-8")

# =================================================================================================
# ===== (a0) THE RE-ENTRANCY BOUND — ONE CONSTANT, ONE HELPER =====
# =================================================================================================

# The child's collection scope. `tests/` because `pyproject.toml`'s `testpaths` would select it
# anyway; the `--ignore` because that same `testpaths` is what makes the child re-collect THIS file.
_SUITE_TARGETS = ["tests/", "--ignore=tests/test_phase25_venue.py"]

# `-p no:cacheprovider` so a child never writes `.pytest_cache` under the parent's run.
_INNER_SUITE_ARGV = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]

# D-44's flag, named once. Consumed here, in `tests/conftest.py`, and directly by the two wave-1
# legs — one variable, three readers, no second mechanism.
_SWEEP_ENV_VAR = "PERSONACORE_SWEEP_ACTIVE"

# pytest's terminal summary line: `1759 passed, 36 skipped, 83 warnings in 243.28s (0:04:03)`.
_TERMINAL_LINE = re.compile(r"\bin \d+\.\d+s")
_COUNT = re.compile(r"(\d+) (passed|failed|skipped|error|errors|xfailed|deselected)")


def _run_inner_suite(*, env_overrides, targets=None):
    """THE ONLY ``pytest``-spawning call site in this file. Recursion is bounded HERE.

    ``targets`` defaults to ``_SUITE_TARGETS``, which carries the ``--ignore`` that severs the
    recursion at depth 1. A test needing a narrower scope passes explicit filenames — never a
    re-spelled argv, and never ``tests/`` without the exclusion.

    ``env_overrides`` maps a variable name to its value, or to ``None`` to **pop** it from the
    child's environment. Popping matters: "unset in the parent" is not the same as "absent in the
    child", and the flag-unset baseline test needs the second.

    ``cwd`` is the repo root resolved from ``__file__`` so the relative ``--ignore`` path resolves
    regardless of where the outer pytest was invoked from.
    """
    env = os.environ.copy()
    for name, value in env_overrides.items():
        if value is None:
            env.pop(name, None)
        else:
            env[name] = value
    return subprocess.run(
        [*_INNER_SUITE_ARGV, *(_SUITE_TARGETS if targets is None else targets)],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _terminal_summary(completed):
    """pytest's own final count line, verbatim. Raises with the tail if there is not exactly one."""
    lines = [line for line in completed.stdout.splitlines() if _TERMINAL_LINE.search(line)]
    assert lines, (
        "the inner suite produced no terminal summary line — it did not finish. This is the shape "
        "an unbounded re-entrancy takes: the child never reports because it is still spawning "
        f"children. exit={completed.returncode}\nstdout tail:\n{completed.stdout[-3000:]}\n"
        f"stderr tail:\n{completed.stderr[-2000:]}"
    )
    return lines[-1]


def _counts(completed):
    """``{"passed": N, "skipped": M, ...}`` parsed off the terminal summary line."""
    return {word: int(number) for number, word in _COUNT.findall(_terminal_summary(completed))}


# =================================================================================================
# ===== (a) THE SKIP COUNT, STATED IN ADVANCE =====
# =================================================================================================

# TWO MACHINES, TWO LITERALS. CI is ubuntu-latest on a CPU-only torch wheel; the sweep venue is
# the M3. A single pair cannot describe both: on the M3 the MPS legs RUN unless the flag is set
# (delta = D-44), and on ubuntu they SKIP because MPS is absent (the flag is a no-op).
#
# M3, measured 2026-08-31 at HEAD fd90055 over the COMPLETE suite:
#
#     $ PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest tests/ -rs -q
#     1759 passed, 36 skipped, 83 warnings in 243.28s (0:04:03)
#
# AN ATTRIBUTED SUM, NOT A BARE TOTAL — so a literal that later drifts by one can be BLAMED on a
# named leg instead of re-measured from scratch. 33 + 2 + 1 = 36:
#
#   33  the seven DEVICE-TOUCHING files, all gated through the single register
#         9  tests/test_phase22_dpsgd.py          (_DEVICES params)
#         8  tests/test_phase23_mps_venue.py      (6 _DEVICES params + 2 bare @_MPS_SKIP)
#         8  tests/test_phase22_fakes.py          (7 _DEVICES params + 1 bare @_MPS_SKIP)
#         3  tests/test_phase22_checkpoint.py     (2 _DEVICES params + 1 bare @_MPS_SKIP)
#         2  tests/test_phase23_resume.py         (2 bare @_MPS_SKIP)
#         2  tests/test_phase23_cal03.py          (a module-scope _DEVICES fixture)
#         1  tests/test_mps_smoke.py              (module-level pytestmark)
#    2  the two WAVE-1 legs, named by node id because a drift of one must be attributable:
#         tests/test_phase25_condition_c.py::test_the_measurement_path_reproduces_phase19_exactly
#         tests/test_phase25_gate05.py::test_measure_gate05_produces_six_finite_nlls_per_locked_fact
#       Both gate on this same env var directly (they are wave 1 and predate `sweep_is_active()`),
#       and both additionally serialise on `tempfile.gettempdir()/personacore-phase25-mps.lock`.
#       That lock is irrelevant to the COUNT; it is why the flag-UNSET run below does not have the
#       two of them contending on the M3.
#    1  PRE-EXISTING and NOT D-44's: `tests/test_train_loop.py:81` — "fp16 AMP smoke needs a CUDA
#       GPU". This is the SAME single skip the flag-unset baseline reports on the M3, so
#       `SWEEP_ACTIVE_EXPECTED_SKIPS - FLAG_UNSET_EXPECTED_SKIPS = 35` is exactly what D-44 buys
#       THERE.
#
# ubuntu-latest (CI, CPU-only wheel, no gitignored artifacts). The flag does not add skips —
# every MPS / wave-1 leg already skips because the device is absent. Measured after the CI-green
# fix (groups 1–4) over the inner suite (`--ignore=tests/test_phase25_venue.py`):
#
#   33  the same seven DEVICE-TOUCHING files as above
#    2  the two WAVE-1 legs (skipif `not _MPS_AVAILABLE`, fires without the flag)
#    1  CUDA AMP smoke (`tests/test_train_loop.py:81`)
#    2  never-taught adapter on-disk hash (tests/test_phase23_ctrl.py; gitignored `*.pt`)
#   14  other artifact / golden-platform skips that a fresh clone always takes
#        (slim/lora/forbid_ids, phase14 demo x2, phase15 plots, phase22 checkpoint
#        old-on-disk + 3 v3 cases, phase23 retained draws, two golden-trajectory
#        platform gates)
#  = 52  flag-set AND flag-unset. Re-measure before bumping; do not derive at import.
#
# DELIBERATELY OUTSIDE the number: the five NAME-ONLY node ids that mention `mps` and touch no
# device (`test_lr_schedule.py`, `test_phase22_accountant.py`, `test_preflight.py` and the two
# `test_config.py` dataclass cases). They are enumerated in the register's exemption comment.
#
# THE LITERAL STAYS A LITERAL. It is stated in advance of the sweep 25-14 launches at wave 7, and
# this plan's wave-2 position exists only so it could be measured over a COMPLETE suite. Do not
# soften it into a computed expression, a lower bound, or a value derived at import from a
# collection pass — the equality assert against a pinned integer IS the mechanism. The platform
# split is two pinned integers, not a formula.
_M3_SWEEP_ACTIVE_EXPECTED_SKIPS = 36
_M3_FLAG_UNSET_EXPECTED_SKIPS = 1
_UBUNTU_SWEEP_ACTIVE_EXPECTED_SKIPS = 52
_UBUNTU_FLAG_UNSET_EXPECTED_SKIPS = 52

SWEEP_ACTIVE_EXPECTED_SKIPS = (
    _M3_SWEEP_ACTIVE_EXPECTED_SKIPS if _MPS_PRESENT else _UBUNTU_SWEEP_ACTIVE_EXPECTED_SKIPS
)
FLAG_UNSET_EXPECTED_SKIPS = (
    _M3_FLAG_UNSET_EXPECTED_SKIPS if _MPS_PRESENT else _UBUNTU_FLAG_UNSET_EXPECTED_SKIPS
)

# The two register files, and what they contribute to the sum above. Used by the cheap companion
# test so a fast signal exists per task commit without paying for a full inner suite.
_REGISTER_FILES = ["tests/test_phase23_mps_venue.py", "tests/test_mps_smoke.py"]
_REGISTER_FILE_SKIPS = 9

_WAVE_ONE_FILES = ["tests/test_phase25_condition_c.py", "tests/test_phase25_gate05.py"]
_WAVE_ONE_NODE_IDS = (
    "tests/test_phase25_condition_c.py::test_the_measurement_path_reproduces_phase19_exactly",
    "tests/test_phase25_gate05.py::test_measure_gate05_produces_six_finite_nlls_per_locked_fact",
)

# `--verbosity=1` OVERRIDES the `-q` in `_INNER_SUITE_ARGV` (argparse takes the last write to
# `dest="verbose"`), which is what makes pytest print NODE IDS beside SKIPPED. `-rs` alone prints
# only `file:lineno`, and a node id is what the attribution above is written in.
_NODE_ID_ARGS = ["-rs", "--verbosity=1"]


# =================================================================================================
# ===== THE RE-ENTRANCY BOUND, PROVED THREE WAYS =====
# =================================================================================================


def test_every_pytest_subprocess_is_funnelled_through_one_helper():
    """AST, not grep: this module's docstring names ``pytest`` and ``--ignore`` on purpose.

    Two properties, and the second is the one that keeps the bound honest as the file grows:
    no ``pytest``-spawning call may live outside ``_run_inner_suite``, and ``_run_inner_suite``
    itself must contain exactly ONE spawn.
    """
    tree = ast.parse(_SOURCE)
    owner = {
        id(node): fn.name
        for fn in ast.walk(tree)
        if isinstance(fn, ast.FunctionDef)
        for node in ast.walk(fn)
    }
    spawns = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("run", "check_output", "Popen", "call")
    ]
    unfunnelled = [
        call.lineno
        for call in spawns
        if owner.get(id(call)) != "_run_inner_suite"
        and (
            {k.value for k in ast.walk(call) if isinstance(k, ast.Constant)} & {"pytest"}
            or {getattr(k, "id", "") for k in ast.walk(call)}
            & {"_INNER_SUITE_ARGV", "_SUITE_TARGETS"}
        )
    ]
    assert not unfunnelled, (
        f"line(s) {unfunnelled} spawn pytest outside `_run_inner_suite`. Every such call site can "
        "re-spell the argv WITHOUT `--ignore=tests/test_phase25_venue.py`, and a child that "
        "collects this file spawns two more at every level — measured reaching level 5"
    )
    funnelled = [c for c in spawns if owner.get(id(c)) == "_run_inner_suite"]
    assert len(funnelled) == 1, (
        f"`_run_inner_suite` holds {len(funnelled)} subprocess call(s), not exactly one. The "
        "funnel is only a bound while it is a single point"
    )


def test_the_recursion_bound_is_argv_and_names_this_file():
    """By VALUE: the exclusion is in ``_SUITE_TARGETS`` and it names this exact path."""
    assert _SUITE_TARGETS == ["tests/", "--ignore=tests/test_phase25_venue.py"], _SUITE_TARGETS
    assert f"--ignore=tests/{_THIS_FILE.name}" in _SUITE_TARGETS, (
        "the exclusion no longer names this file — a rename left the bound pointing at a path that "
        "does not exist, and pytest does not complain about an --ignore that matches nothing"
    )


def test_the_child_collects_nothing_from_the_spawner():
    """BEHAVIOURAL: the child's collection contains zero node ids from this file."""
    completed = _run_inner_suite(
        env_overrides={_SWEEP_ENV_VAR: "1"}, targets=_SUITE_TARGETS + ["--collect-only"]
    )
    collected = [
        line
        for line in completed.stdout.splitlines()
        if line.startswith(f"tests/{_THIS_FILE.name}")
    ]
    assert not collected, (
        f"the child collected {len(collected)} node id(s) from the spawner: {collected[:5]}. "
        "Recursion is not bounded — each of those spawns two more children"
    )


def test_the_flag_does_not_make_a_leg_vanish():
    """A SKIP IS COUNTABLE; AN ABSENCE IS NOT (T-25-27, 23-VALIDATION Pitfall 1).

    The cheap companion to the full-suite count test, so a fast signal exists per task commit.
    Collection is compared flag-set against flag-unset: ``pytest.param(..., marks=skipif)`` keeps
    the leg in the collection either way, and a future edit that "optimised" the register into a
    shrinking ``["cpu"] + (["mps"] if available else [])`` list would make 33 legs DISAPPEAR while
    every pass count stayed green.
    """
    with_flag = _run_inner_suite(
        env_overrides={_SWEEP_ENV_VAR: "1"}, targets=_SUITE_TARGETS + ["--collect-only"]
    )
    without_flag = _run_inner_suite(
        env_overrides={_SWEEP_ENV_VAR: None}, targets=_SUITE_TARGETS + ["--collect-only"]
    )
    assert _counts(with_flag) == _counts(without_flag), (
        f"collection differs with the flag ({_terminal_summary(with_flag)}) and without it "
        f"({_terminal_summary(without_flag)}). D-44 must SKIP legs, never remove them: an absent "
        "parametrization cannot be counted, and the whole skip audit rests on counting"
    )

    register = _run_inner_suite(env_overrides={_SWEEP_ENV_VAR: "1"}, targets=_REGISTER_FILES)
    assert _counts(register).get("skipped") == _REGISTER_FILE_SKIPS, (
        f"the two register files report {_terminal_summary(register)!r}, not "
        f"{_REGISTER_FILE_SKIPS} skipped. The attribution behind SWEEP_ACTIVE_EXPECTED_SKIPS is "
        "wrong at its largest single contributor"
    )


# =================================================================================================
# ===== THE COUNT ITSELF, AND THE TWO WAVE-1 LEGS INSIDE IT =====
# =================================================================================================


def test_the_two_wave_one_mps_legs_are_inside_the_count():
    """Both wave-1 legs SKIP under the same single mechanism the register uses.

    **Scoped to those two files by name, never ``tests/``**: a third full-suite runner would
    triple the cost for a fact two files prove. Because the targets are explicit filenames and
    neither is this file, the ``--ignore`` is unnecessary here and its absence is not a hole.

    A leg missing from ``-rs`` is a leg missing from the count, and the literal would then be wrong
    in a way the equality assert alone cannot distinguish from a genuine drift.
    """
    completed = _run_inner_suite(
        env_overrides={_SWEEP_ENV_VAR: "1"}, targets=_WAVE_ONE_FILES + _NODE_ID_ARGS
    )
    skipped_ids = {
        line.split()[0]
        for line in completed.stdout.splitlines()
        if " SKIPPED" in line and line.startswith("tests/")
    }
    for node_id in _WAVE_ONE_NODE_IDS:
        assert node_id in skipped_ids, (
            f"{node_id} is not SKIPPED under {_SWEEP_ENV_VAR}=1 — it either RAN (MPS contention "
            "during a live sweep, which is what D-44 exists to prevent) or vanished from "
            f"collection. Either way it is not inside SWEEP_ACTIVE_EXPECTED_SKIPS.\nSkipped ids "
            f"seen: {sorted(skipped_ids)}"
        )
    assert _counts(completed).get("skipped") == len(_WAVE_ONE_NODE_IDS)


def test_the_sweep_active_skip_count_is_the_number_stated_in_advance():
    """INNER RUN 1 OF 2. The whole point is the number, so this is never skipped.

    Full execution, never ``--collect-only``, so the count is real. Per the module docstring the
    ``--ignore`` in ``_SUITE_TARGETS`` is not the prohibited skip: it bounds the CHILD and
    contributes 0 skips, so this number is the SAME one a human reads from
    ``PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest tests/
    --ignore=tests/test_phase25_venue.py -q`` — the exact argv plan 25-17 runs during the live
    sweep.
    """
    completed = _run_inner_suite(env_overrides={_SWEEP_ENV_VAR: "1"})
    counts = _counts(completed)
    assert counts.get("skipped") == SWEEP_ACTIVE_EXPECTED_SKIPS, (
        f"the sweep-active suite reports {_terminal_summary(completed)!r}, but the count stated in "
        f"advance is {SWEEP_ACTIVE_EXPECTED_SKIPS}. Read the attributed sum beside the literal and "
        "blame the drift on a named leg before re-measuring: a count that moved silently is the "
        "failure 23-VALIDATION.md calls Pitfall 1, whether it moved up or down. "
        f"(child exit={completed.returncode}, counts={counts})"
    )


def test_with_the_flag_unset_the_baseline_is_unchanged():
    """INNER RUN 2 OF 2. The flag is ADDITIVE — with it absent the skip count is still 1.

    The env var is **popped** from the child's environment, never merely left unset in the parent:
    this test must hold when the whole outer suite is itself running under the flag.

    Only the SKIP count is asserted. The PASS count has legitimately grown past the `8dd6415`
    baseline of 1,647 because 25-21 and 25-22 landed in wave 1, and pinning it would make this test
    fail for the wrong reason. The `--ignore` does not move the skip number either: this file's own
    tests are not MPS-gated, so it contributes 0 skips with the flag off as well as on.
    """
    completed = _run_inner_suite(env_overrides={_SWEEP_ENV_VAR: None})
    counts = _counts(completed)
    assert counts.get("skipped") == FLAG_UNSET_EXPECTED_SKIPS, (
        f"with {_SWEEP_ENV_VAR} absent the suite reports {_terminal_summary(completed)!r}, not "
        f"{FLAG_UNSET_EXPECTED_SKIPS} skipped. A flag that silently changed the DEFAULT would be "
        "worse than no flag: every future run would be quietly missing legs nobody asked it to "
        f"drop. (child exit={completed.returncode}, counts={counts})"
    )


# =================================================================================================
# ===== THE REASON TEXT, ASSERTED RATHER THAN ASSUMED =====
# =================================================================================================


def test_the_skip_reason_names_the_sweep():
    """SKIPPED reasons under the flag name the sweep IFF the flag is what produced them.

    On the M3 with MPS present, D-44's skip is the one that fires, and every reason must name
    the sweep and the flag. On ubuntu-latest MPS is absent, so the register files skip with
    ``_MPS_ABSENT_REASON`` even when the flag is set — requiring ``sweep`` there would be a
    false-RED on the reason ``test_the_skip_reason_is_different_when_mps_is_simply_absent``
    exists to keep distinct. Explicit filenames rather than ``tests/``, so this is cheap and
    cannot recurse — but it still goes through ``_run_inner_suite`` like every other spawn here,
    which the AST criterion above enforces.
    """
    completed = _run_inner_suite(
        env_overrides={_SWEEP_ENV_VAR: "1"}, targets=_REGISTER_FILES + ["-rs"]
    )
    reasons = [line for line in completed.stdout.splitlines() if line.startswith("SKIPPED [")]
    assert reasons, f"no SKIPPED reason lines at all:\n{completed.stdout[-2000:]}"
    if _MPS_PRESENT:
        for line in reasons:
            assert "sweep" in line.lower(), (
                f"a skip reason does not name the sweep: {line[:200]!r}. D-44's whole requirement "
                "is that the skip is LOUD — a reason a reader cannot trace back to the sweep is a "
                "leg lost inside a green count"
            )
            assert _SWEEP_ENV_VAR in line, (
                f"a skip reason does not name {_SWEEP_ENV_VAR}: {line[:200]!r}. Naming the flag "
                "is what makes the skip reproducible — without it a reader knows something was "
                "skipped but not how to unskip it"
            )
    else:
        for line in reasons:
            assert "ubuntu-latest" in line, (
                f"a skip reason on CPU-only CI is not the MPS-absent reason: {line[:200]!r}. "
                "The flag cannot produce a sweep-named skip when MPS is not present"
            )
            assert _SWEEP_ENV_VAR not in line, (
                f"a skip reason on CPU-only CI names {_SWEEP_ENV_VAR}: {line[:200]!r}. That is "
                "the sweep reason wearing an MPS-absent skip, which is Trap 2"
            )


def test_the_skip_reason_is_different_when_mps_is_simply_absent():
    """TRAP 2: the two-reason construction PROVED distinct, not declared.

    ``_MPS_SKIP``'s ``reason`` is a fixed string chosen once at import. A conditional that
    collapsed to a single text would satisfy every other assertion in this file, and the CI reader
    on ``ubuntu-latest`` would be told the sweep is holding a device that machine does not have.
    """
    assert _SWEEP_ACTIVE_REASON != _MPS_ABSENT_REASON
    assert "sweep" in _SWEEP_ACTIVE_REASON.lower() and _SWEEP_ENV_VAR in _SWEEP_ACTIVE_REASON
    assert _SWEEP_ENV_VAR not in _MPS_ABSENT_REASON, (
        "the MPS-absent reason names the sweep flag. That reason is what CI prints, and CI is "
        "`ubuntu-latest` on a CPU-only wheel where no sweep is running and no MPS device exists"
    )
    assert "ubuntu-latest" in _MPS_ABSENT_REASON


# =================================================================================================
# ===== (d) D-13'S REVERT, PROVED COMMITTED =====
# =================================================================================================


def test_the_pmset_revert_is_committed_with_its_measured_targets():
    """The revert is a COMMITTED plan step, not a memory — and the module carrying it is TRACKED."""
    assert venue.PMSET_REVERT_TARGETS == {"sleep": 1, "disksleep": 10, "powernap": 1}
    assert isinstance(venue.PMSET_REVERT, tuple) and isinstance(venue.PMSET_APPLY, tuple), (
        "the pmset commands must be argv TUPLES, so there is no shell string to interpolate into "
        "and the exact words are comparable"
    )
    assert venue.PMSET_REVERT[:3] == ("sudo", "pmset", "-a")

    # The argv and the targets are two spellings of one fact; they must agree word for word.
    words = list(venue.PMSET_REVERT)
    for field, value in venue.PMSET_REVERT_TARGETS.items():
        assert field in words, f"{field!r} is missing from {venue.PMSET_REVERT}"
        assert words[words.index(field) + 1] == str(value), (
            f"`{' '.join(venue.PMSET_REVERT)}` sets {field}="
            f"{words[words.index(field) + 1]} while PMSET_REVERT_TARGETS requires {value}. The "
            "argv an operator runs and the values `prove_reverted()` checks have drifted apart"
        )

    tracked = subprocess.run(
        ["git", "ls-files", "scripts/phase25_venue.py"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert tracked == ["scripts/phase25_venue.py"], (
        f"`git ls-files scripts/phase25_venue.py` returned {tracked!r}. D-13 requires the "
        "revert to be a COMMITTED, verifiable step; an untracked module is a note on one machine"
    )


def test_prove_reverted_refuses_a_non_reverted_machine(monkeypatch):
    """**THE NATURAL RED, WATCHED.** A machine still holding the sweep's own `pmset` change.

    ``{"sleep": 0, "disksleep": 0, "powernap": 0}`` is not a planted value: it is exactly what
    ``PMSET_APPLY`` produces, so this is the file's real intermediate state between the sweep's
    start and D-13's revert — the state plan 25-20 will find the machine in.
    """
    monkeypatch.setattr(
        venue, "read_power_settings", lambda: {"sleep": 0, "disksleep": 0, "powernap": 0}
    )
    with pytest.raises(SystemExit) as caught:
        venue.prove_reverted()
    message = str(caught.value)
    for field in venue.PMSET_REVERT_TARGETS:
        assert field in message, (
            f"the refusal does not name {field!r}: {message!r}. An operator who reverted one field "
            "and forgot another needs both halves in ONE message, not one round trip per field"
        )
    assert "NOT REVERTED" in message and " ".join(venue.PMSET_REVERT) in message

    # And it PASSES on a reverted machine, so the refusal above is discriminating rather than total.
    monkeypatch.setattr(venue, "read_power_settings", lambda: dict(venue.PMSET_REVERT_TARGETS))
    assert venue.prove_reverted() == venue.PMSET_REVERT_TARGETS


# A verbatim `pmset -g assertions` capture, M3, 2026-08-31. Trimmed to the shape the parser reads:
# the by-owning-process section, a `Details:` continuation line, and the kernel block below it.
_ASSERTIONS_FIXTURE = """2026-08-31 19:27:51 -0300
Assertion status system-wide:
   PreventUserIdleSystemSleep     1
Listed by owning process:
   pid 70095(Claude): [0x004fc9e100019192] 59:22:42 NoIdleSleepAssertion named: "Electron"
   pid 7591(caffeinate): [0x004c3689000198ef] 124:49:32 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
\tDetails: caffeinate asserting on behalf of Process ID 7584
   pid 7591(caffeinate): [0x004c3689000798f0] 124:49:32 PreventSystemSleep named: "caffeinate command-line tool"
   pid 578(dasd): [0x004c36890007ffff] 12:00:00 BackgroundTask named: "dasd"
Kernel Assertions: 0x104=USB,MAGICWAKE
   id=700  level=255 0x100=MAGICWAKE creat=08/06/2026, 22:03 description=en0 owner=IOSkywalkNetworkBSDClient
"""  # noqa: E501

# A verbatim `pmset -g` SUMMARY capture, same machine, same minute. FIVE `caffeinate` entries for
# THREE processes — this is the blob D-43's original method would have been read from.
_SUMMARY_FIXTURE = """System-wide power settings:
Currently in use:
 standby              1
 powernap             1
 disksleep            10
 sleep                1 (sleep prevented by Claude, caffeinate, caffeinate, caffeinate, caffeinate, caffeinate)
 displaysleep         10
"""  # noqa: E501


def test_the_assertion_reader_parses_owners_not_the_summary_line():
    """D-43 CORRECTED: owners come from ``pmset -g assertions``; the summary yields NOTHING.

    The second half is the one that enforces the correction rather than describing it. The summary
    line enumerates ASSERTIONS — measured at five `caffeinate` entries against three processes,
    twice, at two HEADs, with different pids each time. A verification built on it counts
    assertions and reports processes, so D-43's claim would be unfalsifiable.
    """
    rows = venue.read_assertions(_ASSERTIONS_FIXTURE)
    assert all(
        len(row) == 3 and isinstance(row[0], int) and isinstance(row[1], str) for row in rows
    ), rows
    assert rows == [
        (70095, "Claude", "NoIdleSleepAssertion"),
        (7591, "caffeinate", "PreventUserIdleSystemSleep"),
        (7591, "caffeinate", "PreventSystemSleep"),
        (578, "dasd", "BackgroundTask"),
    ], rows

    # Two assertions for ONE pid — the exact over-count the summary line cannot distinguish.
    caffeinate = [row for row in rows if row[1] == "caffeinate"]
    assert len(caffeinate) == 2 and len({row[0] for row in caffeinate}) == 1

    # The kernel block below the section is excluded: kernel assertions have an `owner=` but no pid.
    assert not [row for row in rows if row[1] == "IOSkywalkNetworkBSDClient"]

    assert venue.read_assertions(_SUMMARY_FIXTURE) == [], (
        "`read_assertions` returned rows for `pmset -g`'s SUMMARY blob. D-43's original method — "
        "'verified by reading `pmset -g` back after launch' — is exactly what this must refuse: "
        "the summary names five caffeinate entries for three processes, so nothing read from it is "
        "a fact about processes"
    )


def test_prove_only_our_caffeinate_refuses_a_stray():
    """D-43: the sweep's own `caffeinate` is the ONLY non-system wake assertion. Cross-checked."""
    ours = 4242
    clean = [
        (ours, "caffeinate", "PreventUserIdleSystemSleep"),
        (578, "dasd", "BackgroundTask"),
    ]
    assert (
        venue.prove_only_our_caffeinate(our_pid=ours, assertions=clean, caffeinate_pids={ours})
        == clean
    )

    stray = clean + [(9999, "caffeinate", "PreventUserIdleSystemSleep")]
    with pytest.raises(SystemExit) as caught:
        venue.prove_only_our_caffeinate(
            our_pid=ours, assertions=stray, caffeinate_pids={ours, 9999}
        )
    assert "9999" in str(caught.value), str(caught.value)

    # A caffeinate PROCESS holding no assertion yet is still residue, and is invisible to the
    # assertion read alone. This is the half the cross-check against `pgrep -x caffeinate` buys.
    with pytest.raises(SystemExit) as caught:
        venue.prove_only_our_caffeinate(
            our_pid=ours, assertions=clean, caffeinate_pids={ours, 7591}
        )
    assert "7591" in str(caught.value) and "pgrep" in str(caught.value)

    # An unnamed non-system owner raises; the same owner NAMED at launch time passes. An exemption
    # stated is a decision, an exemption inferred from absence is the defect.
    with_claude = clean + [(70095, "Claude", "NoIdleSleepAssertion")]
    with pytest.raises(SystemExit) as caught:
        venue.prove_only_our_caffeinate(
            our_pid=ours, assertions=with_claude, caffeinate_pids={ours}
        )
    assert "Claude" in str(caught.value)
    assert (
        venue.prove_only_our_caffeinate(
            our_pid=ours,
            assertions=with_claude,
            caffeinate_pids={ours},
            expected_owners=("Claude",),
        )
        == with_claude
    )


def test_the_caffeinate_wrap_holds_its_own_assertion():
    """D-12: ``-dims`` WRAPS the run; 23-20's ``-is -w <pid>`` WATCHED another pid's lifetime."""
    assert venue.CAFFEINATE_WRAP == ("caffeinate", "-dims")
    provenance = venue.CAFFEINATE_WRAP_PROVENANCE
    assert provenance["supersedes"] == "caffeinate -is -w <pid>"
    assert set(provenance["flags"]) == set("dims")


def test_this_module_never_invokes_the_privileged_commands():
    """T-25-29: ``scripts/phase25_venue.py`` makes the pmset acts CHECKABLE and performs NEITHER.

    AST over the module's own source, because its docstring necessarily quotes the commands it is
    refusing to run and a textual gate would go false-RED on that paragraph.
    """
    tree = ast.parse(pathlib.Path(venue.__file__).read_text(encoding="utf-8"))
    spawns = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("run", "check_output", "Popen", "call")
    ]
    for call in spawns:
        constants = {k.value for k in ast.walk(call) if isinstance(k, ast.Constant)}
        names = {getattr(k, "id", "") for k in ast.walk(call)}
        assert not (constants & {"sudo"}), f"line {call.lineno} elevates privilege"
        assert not (names & {"PMSET_APPLY", "PMSET_REVERT"}), (
            f"line {call.lineno} invokes a committed pmset tuple. Applying and reverting are "
            "OPERATOR acts behind a blocking human checkpoint; this module's job is to make them "
            "checkable, and a module that runs `sudo` on its own is a different program"
        )


def test_pyproject_is_byte_unchanged():
    """RPT-03: the whole re-entrancy bound is argv. No ``addopts``, no marker registration."""
    completed = subprocess.run(
        ["git", "diff", "--exit-code", "--", "pyproject.toml"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (
        f"pyproject.toml has uncommitted changes:\n{completed.stdout}\nThe bound on re-entrancy "
        "lives entirely in `_SUITE_TARGETS`; a pytest-config change here would break RPT-03's "
        "phase-wide byte-identity assertion"
    )
