"""DATED CONTINUATION of ``scripts/mitigation_unit.privacy_n`` (2026-08-25, review finding WR-04).

``scripts/mitigation_unit.py`` is PERMANENTLY FROZEN. ``results/phase21_privacy_unit.json`` and
``results/phase21_multiplicity.json`` are committed, and
``tests/test_phase20_prereg.py::test_phase21_prereg_is_frozen_before_every_phase21_result`` requires
EVERY commit touching the pin to be an ancestor of every ``results/phase21_*`` first-add. That guard
takes ``adds[-1]`` — the EARLIEST add — so a ``git rm`` plus a re-add at the same path cannot
launder it, and 21-03 measured that laundering attempt across a real cycle rather than assuming.
There is no recovery path and no force flag. WR-04 is a defect INSIDE that file, so it cannot be
fixed by editing that file. This module is therefore the correction: unpinned code that CALLS the
pin, supersedes exactly one of its names, and never modifies it.

This is the shape ``scripts/phase20_gate_coverage.py`` already established for the Phase 20 pin
(D-24's "executable half"), applied to Phase 21's. ``scripts/_addendum.py`` — which the review
names as the vehicle — is the WRONG one and is left alone: its only public function is
``append_addendum(path, addendum, *, pending, recorded)``, an append-only writer over a MARKDOWN
report whose every caller passes a ``results/*.md`` path. It cannot export a Python function. The
INTENT the review records (a dated continuation beside the frozen text, never an edit) is correct
and is what this module implements; only the vehicle moved.

THE DEFECT, MEASURED RATHER THAN DESCRIBED
==========================================
The pin's ``privacy_n`` is ``return int(n_facts)``, and its docstring claims the cast exists "so a
float ``n_facts`` cannot SILENTLY become a fractional N in a downstream epsilon". ``int()`` does not
refuse a float — it TRUNCATES, which is the same class of silent wrong answer one step over.
Measured on the committed pin at ``c05880c``::

    mitigation_unit.privacy_n(7.9)   ->  7      a record is silently DROPPED from the lot
    mitigation_unit.privacy_n(7.0)   ->  7      an int returned for a float that was never counted
    mitigation_unit.privacy_n(0)     ->  0      then `delta * N == 0` clears any ceiling
    mitigation_unit.privacy_n(-3)    -> -3      a NEGATIVE privacy N
    mitigation_unit.privacy_n('8')   ->  8      a string
    mitigation_unit.privacy_n(True)  ->  1      N = 1, named in no document
    mitigation_unit.privacy_n(False) ->  0      N = 0, by the same route
    mitigation_unit.privacy_n(8)     ->  8      the only correct case

The blast radius is not hypothetical and is not confined to Phase 22. ``delta * N`` against
``DELTA_TIMES_N_CEILING`` is the pin's own published ceiling check, and it is computed per capacity
in ``scripts/phase21_unit_record.py``'s ``delta.capacities`` rows off an ``n`` that came through
``privacy_n``. At ``N = 0`` that product is ``0.0``, which clears a ``< 0.01`` ceiling by
construction — a privacy guarantee that passes because it is about nothing.

WHY AN EXACT FLOAT (``7.0``) IS REFUSED TOO, AND NOT ADMITTED AS HARMLESS
========================================================================
It is refused, and the reason is a measured property rather than a preference.

A count reaches this function from ``len(...)``; nothing that counts facts produces a float. A float
N therefore means the value came out of ARITHMETIC — a division, a ratio, a mean — and that is the
same code path that produces ``7.9``. Admitting ``7.0`` makes this guard's verdict depend on whether
the upstream defect happened to land on a whole number, so one defective caller passes at one
capacity and fails at another. That is precisely the "declared invariant that is true the day it is
written" failure this phase exists to refuse, reintroduced by the guard meant to close it.

"Looks whole" is also not the same property as "is whole": ``repr(3.0000000001)`` is visibly not an
integer, but the class it belongs to is invisible at more digits, and the pin truncates every member
of it to ``3``. ``float.is_integer()`` would be the only cheap admission test and it buys nothing —
refusing the TYPE removes the question instead of answering it per value.

Decisively, the repository already settled this for the SAME quantity.
``scripts/teach_persona.py:743-750`` refuses ``n_facts`` with
``isinstance(n_facts, bool) or not (isinstance(n_facts, int) and n_facts > 0)``, raising
``SystemExit`` and calling it "a COUNT of privacy records". That predicate already refuses an exact
float. This module adopts it byte-for-byte in intent, so the two guards on one quantity cannot
disagree — adopting a LOOSER rule here than the precedent the review cites would be a divergence
with no measured need behind it.

WHY ``bool`` GETS ITS OWN REFUSAL
=================================
``bool`` SUBCLASSES ``int``, so ``isinstance(True, int)`` is ``True`` and a plain int check ADMITS
it. Under the pin, ``privacy_n(True)`` returns ``1`` — a privacy N of one record, produced from a
flag. It is checked first and reported separately so the message says ``bool``, rather than a reader
being told ``True`` is not an int when Python says it is.

WHAT IS NOT SUPERSEDED
======================
ONLY ``privacy_n``. ``PRIVACY_UNIT``, ``PRIVACY_UNIT_ARITHMETIC``, ``SAMPLING_RATE_Q``, ``DELTA``,
``DELTA_TIMES_N_CEILING``, ``REJECTED_DELTA_RECIPE``, ``rejected_delta`` and ``REPLAY_OUTSIDE_N``
are correct and stay imported FROM THE PIN by every consumer. A continuation that re-exported the
whole pin would become a second copy of it, free to drift — the defect this repository names as "a
number appearing in two artifacts is two numbers that can disagree", at module scope.

WHY THIS FILE IS NOT NAMED ``mitigation_*``
===========================================
D-22's ceiling. ``tests/test_phase20_prereg.py:72`` globs ``scripts/mitigation_*.py`` and asserts
the ACCUMULATED import surface of every match is a subset of ``{pathlib, sys, erasure_gate}``
(``:916``). A continuation whose whole job is ``import mitigation_unit`` would put that name into
that set and turn the assertion RED. The naming is a FORCED CONSEQUENCE of that ceiling, not a
style choice, and is recorded so a later reader does not "fix" it by renaming.

NOTHING IN PYTHON FORCES A CALLER HERE
======================================
There is no import hook, no shadowing and no rename that can make
``from mitigation_unit import privacy_n`` fail or redirect without editing the pin — and editing the
pin is the one thing that cannot be done. This is the same state
``scripts/phase20_gate_coverage.py:74-81`` records for ``mitigation_point_verdict``, and the
repository's answer is the same: an AST IMPORT CENSUS over ``scripts/`` and ``src/``, in
``tests/test_phase21_unit_continuation.py::test_privacy_n_has_no_route_through_the_pin_outside_this_module``.
It makes the supersession a fact about the IMPORT GRAPH rather than a paragraph — ``.planning/
ROADMAP.md:139-144``'s own words for the gate/budget split.

CPU-only, no I/O, no network. Imports the pin and nothing else.
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import mitigation_unit  # noqa: E402  (needs the sys.path insert above)

# The one name this file supersedes, machine-readable so the claim is contradicted by module DATA
# and not only by the prose above. `tests/test_phase21_unit_continuation.py` reads it.
SUPERSEDES = "mitigation_unit.privacy_n"

# The capacities this milestone runs, and the ONLY values of N any committed `results/phase21_*`
# artifact publishes. The module-level guards at the bottom prove agreement with the pin at both.
PUBLISHED_CAPACITIES = (8, 64)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/mitigation_unit.py:70``'s register.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    validator that disappears under an optimisation flag is not a validator. The bracketed prefix is
    this module's own name, for the reason the pin records — an abort naming the wrong module sends
    its reader to the wrong file, and this one supersedes a function in a file it is not.
    """
    if not condition:
        raise SystemExit(f"[phase21_unit_continuation] {message}")


def privacy_n(n_facts):
    """The privacy N, VALIDATED. Supersedes ``mitigation_unit.privacy_n`` (see the header).

    Returns a correct positive ``int`` UNCHANGED — no cast, no clamp, no default. Refuses everything
    else, and refuses by RAISING rather than by repairing: a repaired N is a wrong N that reached an
    epsilon anyway, which is the defect being closed rather than a milder version of it.

    Three refusals with three distinct messages, so a reader debugging one does not have to guess
    which fired — ``tests/test_phase20_prereg.py:870-881``'s stated register.
    """
    _prove(
        not isinstance(n_facts, bool),
        f"privacy_n got the bool {n_facts!r}. `bool` SUBCLASSES `int`, so an `isinstance(n, int)` "
        f"test ADMITS it and the frozen pin's `int()` cast turns it into N = {int(n_facts)} in "
        "silence — a privacy N produced from a flag and named in no document. This is checked "
        "FIRST and reported separately so the message says `bool`, rather than telling a reader "
        "that True is not an int when Python says it is",
    )
    _prove(
        isinstance(n_facts, int),
        f"privacy_n got {n_facts!r} ({type(n_facts).__name__}). N is a COUNT of privacy records "
        "and must arrive as an `int`. This REFUSES rather than casting, because the frozen pin's "
        "`int()` TRUNCATES: measured, `mitigation_unit.privacy_n(7.9)` returns 7, dropping a "
        "record from the lot while the epsilon computed against the result still claims to "
        "protect all of them. An EXACT float such as 7.0 is refused on the same terms — a count "
        "arrives from `len(...)`, so a float N came out of arithmetic, and admitting the whole "
        "ones would make this verdict depend on whether the upstream defect happened to land on a "
        "whole number. `scripts/teach_persona.py:743-750` already refuses this quantity on exactly "
        "this predicate; two guards on one quantity must not disagree",
    )
    _prove(
        n_facts > 0,
        f"privacy_n got {n_facts!r}. N must be STRICTLY positive. At N = 0 the pin's own published "
        f"ceiling check `delta * N < {mitigation_unit.DELTA_TIMES_N_CEILING}` reads `0.0 < "
        f"{mitigation_unit.DELTA_TIMES_N_CEILING}` and passes BY CONSTRUCTION — a privacy "
        "guarantee that clears its ceiling because it is about nothing. A negative N is worse: it "
        "makes the product negative, so every ceiling check passes by a wider margin the more "
        "wrong it gets. The frozen pin admits both (measured: 0 -> 0, -3 -> -3)",
    )
    return n_facts


# ---------------------------------------------------------------------------------------------
# THE GUARDS. Module scope, so a wrong edit fails at IMPORT rather than inside a consumer that has
# already spent compute — `scripts/mitigation_unit.py:210-213`'s stated placement reason.
#
# WHAT THEY PROVE, and why it is the load-bearing property rather than a decoration: on the
# ADMITTED domain this function is a strict RESTRICTION of the pin's, never a different answer. That
# is what lets `scripts/phase21_unit_record.py` be routed through here without any committed
# `results/phase21_*` number moving — the artifact publishes N at these two capacities and nowhere
# else. If a future edit made the two disagree at 8 or 64, the published artifact would silently
# stop matching its own emitter, and this abort is what makes that impossible to ship.
# ---------------------------------------------------------------------------------------------
for _n in PUBLISHED_CAPACITIES:
    _prove(
        privacy_n(_n) == mitigation_unit.privacy_n(_n) == _n,
        f"at the published capacity N = {_n} this module returns {privacy_n(_n)!r} while the "
        f"frozen pin returns {mitigation_unit.privacy_n(_n)!r}. The continuation may only NARROW "
        "the pin's domain, never change its answer inside it — a disagreement here means every "
        "committed results/phase21_* row carrying this N was emitted against a different rule "
        "than the one now shipping",
    )
del _n
