"""CAL-02's STRUCTURAL obligations — the gate/budget split, proved TRANSITIVELY.

WHAT THIS FILE IS, AND WHAT IT DELIBERATELY IS NOT
--------------------------------------------------
The **STATIC** half of CAL-02's guard already exists and already bites. It lives at
``tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only``,
it already names ``mitigation_budget`` by string, and it scans the whole ``scripts/mitigation_*.py``
glob so it admits ``scripts/mitigation_budget.py`` the moment Phase 23 creates it. **It is NOT
duplicated here.** ``tests/test_phase20_prereg.py:153-155`` states the rule this file obeys: a
lookalike copy proves something about a DIFFERENT function than the one CI executes, so a guard
proved correct somewhere else and the guard actually running must be the SAME code.

``scripts/mitigation_gate.py`` is **FROZEN** — every commit touching it must be an ancestor of every
``results/phase20_*`` artifact's earliest add, three of which are committed, and a ``git rm`` plus a
re-add cannot launder that because the guard takes the EARLIEST add. There is no recovery path and
no force flag. Nothing in Phase 23 writes to it; this file only READS it.

THE HOLE THE STATIC HALF CANNOT SEE
-----------------------------------
The static scan walks ``scripts/mitigation_*.py`` and nothing else. But the gate's own import list
(``scripts/mitigation_gate.py:56-63``) is ``pathlib``, ``sys`` and **``erasure_gate``** — and
``scripts/erasure_gate.py`` sits OUTSIDE that glob. So the route

    mitigation_gate  ->  erasure_gate  ->  mitigation_budget

is INVISIBLE to any AST walk over ``mitigation_*.py``, however careful. ``erasure_gate.py`` imports
only ``math`` today (``scripts/erasure_gate.py:68``), so the route is empty in fact — but "empty in
fact" is not "structurally unable to import", and SC3 asks for the second.

``test_gate_does_not_transitively_load_the_budget`` below closes it the way this project already
calls the standard: an **out-of-process** probe that execs the real frozen gate and asks the
interpreter, not the source text, what got loaded. The shape is
``tests/test_phase22_accountant.py::test_accountant_imports_math_only``'s second half, cited by
symbol and copied in structure rather than re-derived. Its docstring records WHY out of process is
mandatory and the reason applies here unchanged: by the time this test runs, ``torch`` is already in
``sys.modules`` from sibling tests, so an in-process check would be vacuous.

CPU-only, GPU-free, no torch, no network.
"""

import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_gate  # noqa: E402  (needs the sys.path insert above)

_MITIGATION_GATE_PATH = _ROOT / "scripts" / "mitigation_gate.py"

# ``mitigation_budget`` is the name CAL-02 is about. The other three are the classic offenders
# ``test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only`` names SEPARATELY from its
# subset assertion, for the reason recorded there: so the failure message says WHICH one. They are
# carried here too because the transitive probe is the only half that can see them arriving through
# ``erasure_gate``.
_FORBIDDEN = ("mitigation_budget", "torch", "numpy", "scipy")

# ============================================================================================
# THE IMPORT CEILING — AN OBSERVATION, MEASURED 2026-08-26 IN THIS WORKING TREE (T-23-10)
# ============================================================================================
# Recorded HERE, in a test file plan 23-09 must read, rather than only in a planning document it
# may not. `test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only` asserts
# `imported <= {"pathlib", "sys", "erasure_gate"}` over the UNION across every
# `scripts/mitigation_*.py`. Measured, by walking the AST of each module in the tree today:
#
#     scripts/mitigation_accountant.py   ->  no imports at all
#     scripts/mitigation_unit.py         ->  no imports at all
#     scripts/mitigation_gate.py         ->  pathlib, sys, erasure_gate   (:49-63)
#
# The union is EXACTLY the allow-set, so the ceiling has **zero headroom**. A new
# `scripts/mitigation_*.py` sibling gets no import budget whatsoever, and this is not a guess —
# it was watched:
#
#   (a) a scratch `mitigation_zzprobe.py` containing `import mitigation_budget` produced
#       `AssertionError: a mitigation_*.py module imports mitigation_budget (imports:
#       ['erasure_gate', 'mitigation_budget', 'pathlib', 'sys'])`
#   (b) a scratch `mitigation_budget.py` containing a single `import json` produced
#       `AssertionError: the mitigation modules import ['json'] beyond the allow-set
#       ['erasure_gate', 'pathlib', 'sys']`
#
# Both scratch modules were deleted and `git status --short scripts/` proved empty afterwards.
#
# CONSEQUENCES FOR `scripts/mitigation_budget.py` (plan 23-09), in priority order:
#
#   1. It must have ZERO imports. Not `json`, not `math`, not `dataclasses`. `scripts/
#      phase19_floor.py` is the shape that satisfies this for free — literal assignments and
#      nothing else, each beside a provenance comment naming the artifact it came from.
#   2. It may not import `mitigation_gate` EITHER. That would add `mitigation_gate` to `imported`
#      and break the subset assertion just as surely as `json` does — and it is the import a
#      reader would most naturally reach for, since the budget's K has to agree with the gate's
#      closed menu.
#   3. So a selected K is RESTATED as a literal carrying a provenance comment naming
#      `scripts/mitigation_gate.py::K_RUNGS`, and 23-09 must ship a TEST asserting the literal and
#      the menu agree. A restated constant with no test agreeing it is a copy waiting to drift;
#      that test is the whole price of the zero-import ceiling and it is not optional.
#
# The alternative — widening `allowed` — is available and is REFUSED: it weakens a committed guard
# to accommodate a module that has not been written yet, which is the wrong way round.
# ============================================================================================

# THE META-GUARD (T-23-07). A probe whose ``exec_module`` silently failed would load nothing at all
# and then report an empty offender list — green, and proving nothing. So the probe PRINTS a
# sentinel read off the exec'd module and the test asserts it arrived.
# ``test_accountant_imports_math_only`` carries the same idea as its ``assert imported`` meta-guard.
_SENTINEL_PREFIX = "GATE_SENTINEL="
_SENTINEL_ATTR = "NEVER_TAUGHT_ARM"


def _import_probe(module_path):
    """Source for a fresh interpreter that execs ``module_path`` and reports what it dragged in.

    Exits 1 with the offender list on stdout when any ``_FORBIDDEN`` name reached ``sys.modules``,
    0 otherwise. One builder, used by BOTH the real-gate test and the positive control below, so
    the control cannot drift into exercising a different probe than the one that guards the gate.
    """
    return (
        "import importlib.util, sys;"
        f"spec = importlib.util.spec_from_file_location('probe_target', {module_path!r});"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        f"print({_SENTINEL_PREFIX!r} + repr(getattr(m, {_SENTINEL_ATTR!r})));"
        f"bad = [n for n in {_FORBIDDEN!r} if n in sys.modules];"
        "print(bad); sys.exit(1 if bad else 0)"
    )


def _run_probe(module_path):
    return subprocess.run(
        [sys.executable, "-c", _import_probe(module_path)],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )


def test_gate_does_not_transitively_load_the_budget():
    """CAL-02 / SC3 / T-23-06 — the gate is structurally unable to reach the budget, TRANSITIVELY.

    The static scan at ``tests/test_phase20_prereg.py:1171`` proves the gate never NAMES
    ``mitigation_budget``. This proves the stronger thing: exec the real frozen gate in a fresh
    interpreter and ``mitigation_budget`` is not in ``sys.modules`` afterwards — closing the
    ``gate -> erasure_gate -> budget`` route that sits outside the ``mitigation_*.py`` glob the
    static scan walks.
    """
    relative = _MITIGATION_GATE_PATH.relative_to(_ROOT).as_posix()
    result = _run_probe(relative)

    # Meta-guard FIRST, for the same reason the accountant's runs first: a probe that loaded
    # nothing would otherwise pass by finding no offenders in an empty process.
    expected = _SENTINEL_PREFIX + repr(getattr(mitigation_gate, _SENTINEL_ATTR))
    assert expected in result.stdout, (
        f"the probe never printed {expected!r}, so `scripts/mitigation_gate.py` did NOT actually "
        f"load — the walk collapsed and the offender list below proves nothing\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    assert result.returncode == 0, (
        f"`scripts/mitigation_gate.py` TRANSITIVELY loads a forbidden module — CAL-02/SC3 "
        f"violated. The offender list is on stdout. The route the static AST scan cannot see is "
        f"gate -> erasure_gate -> X, because `scripts/erasure_gate.py` is outside the "
        f"`scripts/mitigation_*.py` glob that scan walks.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_the_transitive_probe_detects_a_module_that_does_load_the_budget(tmp_path):
    """POSITIVE CONTROL for the probe above, and it is PERMANENT rather than a one-off.

    A guard nobody has watched fail is not evidence. The two STATIC assertions were watched RED by
    hand against scratch modules in `scripts/` (see the ceiling block above for their literal
    failure text); that observation is transient by construction, because the scratch modules have
    to be deleted afterwards. This one is not: it builds its scratch pair under `tmp_path`, so it
    can live in the suite and re-prove itself on every run. A watched RED that runs every time is
    strictly better evidence than one performed once.

    WHAT IT DOES AND DOES NOT CLAIM. It proves the PROBE detects the route — nothing about the real
    gate, which `test_gate_does_not_transitively_load_the_budget` covers. The two share
    `_import_probe`, so the control cannot pass by exercising a different probe than the one that
    guards the gate.

    The scratch loader stands in for a hypothetical `erasure_gate` that grew an import: it is a
    module the probe execs which reaches `mitigation_budget` INDIRECTLY, through `sys.path` rather
    than by sitting in the `scripts/mitigation_*.py` glob. That is precisely the shape the static
    AST scan cannot see, so the RED here is the RED that matters.
    """
    (tmp_path / "mitigation_budget.py").write_text("Z_SWEEP = ()\n", encoding="utf-8")

    sentinel_value = getattr(mitigation_gate, _SENTINEL_ATTR)
    loader = tmp_path / "scratch_gate.py"
    loader.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(tmp_path)!r})\n"
        "import mitigation_budget  # noqa: F401\n"
        # Cited off the real gate rather than retyped, so the two sentinels cannot drift.
        f"{_SENTINEL_ATTR} = {sentinel_value!r}\n",
        encoding="utf-8",
    )

    result = _run_probe(str(loader))

    # Same meta-guard, same order: prove the scratch module LOADED before reading its verdict. A
    # crash would also exit non-zero, and a control that cannot tell "detected" from "crashed"
    # proves nothing.
    expected = _SENTINEL_PREFIX + repr(sentinel_value)
    assert expected in result.stdout, (
        f"the control's scratch module never printed {expected!r} — it CRASHED rather than being "
        f"caught, so this test is not observing what it claims to observe\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    assert result.returncode == 1, (
        f"the probe stayed GREEN against a module that DOES load mitigation_budget — the probe in "
        f"this file is vacuous and `test_gate_does_not_transitively_load_the_budget` proves "
        f"nothing\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "mitigation_budget" in result.stdout, (
        f"the probe reddened but did not NAME mitigation_budget on stdout, so a real failure would "
        f"not tell its reader which module got in\nstdout: {result.stdout}"
    )
