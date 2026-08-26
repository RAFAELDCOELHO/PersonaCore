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
