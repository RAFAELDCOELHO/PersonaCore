"""Phase 26 PRE-REGISTRATION — a DATED CONTINUATION, committed before any Phase-26 number exists.

This module continues two frozen texts BY REFERENCE and never edits either:

  * ``phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]`` — WHICH point Phase 26 audits.
    Resolved against ``results/phase25_frontier.json`` it yields the sigma=0 control
    ``dp_n8_sigma0p000000`` (the pre-registered null: no n=8 point returned PASS). The control
    carries no epsilon claim, so the committed comparison is vacuous by construction; the
    control's reading is the instrument's POWER reading (D-01, D-03) and feeds nothing else.
    ``EXTENSION`` below ADDS all 15 noised ``dp_n8`` points, each against its OWN epsilon.
  * ``phase21_filler.GUESSABILITY_WAIVER`` — its premise "filler is never scored" is false from
    this phase (D-07): the adapter-off arm IS the guessability probe. ``WAIVER_CONTINUATION``
    names why; the original text stays standing, superseded.

Both originals stay BYTE-IDENTICAL and visible (D-01, D-07, D-12). ``phase25_prereg``'s copy of
the reservations travels inside the frontier's ``provenance``, so editing it would make the
artifact disagree with the live module — WR-03's defect, avoided.

ANCESTRY-GUARDED. ``tests/test_phase26_prereg.py``
(``test_phase26_prereg_is_frozen_before_every_phase26_result``) requires EVERY commit touching
this file to be a strict ancestor of the first-add of every tracked
``results/phase26_*`` file. After the first sidecar/artifact lands, a correction to anything here
goes in a FURTHER continuation module — never an edit (``scripts/phase21_unit_continuation.py``'s
precedent: a Python contract is continued by a Python module).

CPU-ONLY AT IMPORT. Stdlib + sibling scripts only: no torch, no ``phase14_*``, no ``teach_persona``,
no ``phase21_filler`` (it imports ``phase14_factset`` at module scope) — the waiver is named by its
dotted string, not imported. Every refusal is ``_prove`` -> ``SystemExit``, never ``assert``.

Threats mitigated: T-26-03 (post-hoc favourable reading — every threshold, scope and formula is
committed data before any sidecar exists); T-26-09 (both Wilson bounds and ``z`` imported, never
re-implemented; counts are ``int`` only).
"""

import math
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import erasure_gate  # noqa: E402  (needs the sys.path insert above)
import mitigation_unit  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)

# The date this file was committed, and the property that date certifies: at this commit
# `git ls-files 'results/phase26_*'` returned NOTHING, so no rule below could have been shaped by
# a sidecar, a reading or a verdict that did not yet exist (phase25_prereg.py:54-55's register).
COMMITTED = "2026-09-10"
SIDECARS_AT_COMMIT = 0

# The two names this file supersedes, machine-readable so the claim is contradicted by module
# DATA and not only by the prose above (phase21_unit_continuation.SUPERSEDES' register).
SUPERSEDES = (
    "phase25_prereg.CANARY_RESERVATIONS['audit_target_rule']",
    "phase21_filler.GUESSABILITY_WAIVER",
)

# The tracked set the ancestry guard reads — a constant the test imports rather than retypes.
ARTIFACT_GLOB = "results/phase26_*"


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase26_prereg] {message}")


# =================================================================================================
# (1) THE RULE, BY REFERENCE (D-12), AND ITS RESOLUTION (D-01).
# =================================================================================================

# BY REFERENCE, never retyped: `tests/test_phase26_prereg.py` asserts identity (`is`), not equality.
RULE = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]

CONTROL_KEY = "dp_n8_sigma0p000000"
AUDITED_ARM_PREFIX = "dp_n8"


def resolve_audit_target(frontier):
    """``RULE`` executed as written: n=8 points only, the first PASS in ``point_keys`` order, else
    the first n=8 point in ``point_keys`` order. Lifted from ``tests/test_phase25_close.py:274``
    with ``assert`` converted to ``_prove``. Proves the committed rule yields the control (D-12)."""
    points = frontier["points"]
    n8 = [k for k in frontier["point_keys"] if points[k]["arm"].endswith("n8")]
    _prove(
        all(points[k]["canary_population"]["has_out_of_corpus_canaries"] for k in n8),
        "an n=8 point without out-of-corpus canaries — the canary_population_rule reservation "
        "says every n=8 point has them; the frontier disagrees with its own reservation",
    )
    passing = [k for k in n8 if (points[k].get("verdict") or {}).get("verdict") == "PASS"]
    result = passing[0] if passing else n8[0]
    _prove(
        result == CONTROL_KEY,
        f"the committed audit_target_rule resolves to {result!r}, not {CONTROL_KEY!r}. This "
        "continuation was written against the pre-registered null (no n=8 PASS); a different "
        "resolution means the frontier this module was continued from is not the one on disk",
    )
    return result


EXTENSION = (
    "D-01: the control is audited AS COMMITTED and is the instrument's POWER reading. This dated "
    "continuation ADDS all 15 noised dp_n8 points, in `point_keys` order, EACH compared against "
    "its OWN `epsilon` at delta = 1e-5 (D-02: the per-point claim the artifact publishes via "
    "`personacore.privacy.accountant.epsilon_for(sigma, steps, delta)`). NEVER a subset chosen "
    "after seeing a result. The curve total `epsilon_report.curve_total_epsilon` (2387.30 at "
    "delta = 3e-4) travels beside each comparison as context and is never the comparator: it can "
    "only be looser, so a second comparison against it could never accuse anything the first "
    "does not."
)


def audited_point_keys(frontier):
    """The 16 ``dp_n8`` keys, control first, as the ``point_keys`` subsequence (T-26-06: keys come
    only from here). Proved equal to the ``ORDERED_POINT_KEYS()`` restriction."""
    keys = tuple(k for k in frontier["point_keys"] if k.startswith(AUDITED_ARM_PREFIX))
    pinned = tuple(
        k for k in phase25_record.ORDERED_POINT_KEYS() if k.startswith(AUDITED_ARM_PREFIX)
    )
    _prove(
        keys == pinned,
        f"the frontier's dp_n8 subsequence {keys} != ORDERED_POINT_KEYS()'s {pinned}",
    )
    _prove(len(keys) == 16, f"expected 16 dp_n8 points, found {len(keys)}")
    _prove(keys[0] == CONTROL_KEY, f"the first dp_n8 point is {keys[0]!r}, not the control")
    return keys


def noised_point_keys(frontier):
    """The 15 noised points — everything after the control. The audited extension (D-01)."""
    return audited_point_keys(frontier)[1:]


# =================================================================================================
# (2) THE POWER GATE (D-03, D-04).
# =================================================================================================

POWER_SENTENCE = "The instrument must resolve at least the smallest claim it checks."


def power_threshold(frontier):
    """``min(epsilon)`` over the 15 noised points — derived BY RULE from the artifact and asserted
    equal to the sigma=80 record (D-04: no new number)."""
    points = frontier["points"]
    threshold = min(points[k]["epsilon"] for k in noised_point_keys(frontier))
    _prove(
        threshold == points["dp_n8_sigma80p000000"]["epsilon"],
        f"min epsilon over the noised points is {threshold!r}, not the sigma=80 record's "
        f"{points['dp_n8_sigma80p000000']['epsilon']!r} — the extension's smallest claim moved",
    )
    return threshold


def power_gate(control_epsilon_lower, threshold):
    """D-03: the control's epsilon_lower must reach the smallest claim audited. ``None`` (a
    degenerate control reading) FAILS the gate — an instrument that cannot read is without power."""
    passed = control_epsilon_lower is not None and control_epsilon_lower >= threshold
    return {
        "threshold": threshold,
        "control_epsilon_lower": control_epsilon_lower,
        "passed": passed,
        "sentence": POWER_SENTENCE,
    }


# =================================================================================================
# (3) THE PRE-REGISTERED CONSTANTS — RESEARCH Open Questions 2-3, DECIDED here (D-07, D-10, D-14).
# =================================================================================================

DECIDING_TIER = "taught"
DECIDING_TIER_RATIONALE = (
    "The CONTEXT's arithmetic — n_IN = 112 taught questions, ~14 per fact — IS the taught tier, "
    "so the taught tier decides at the fact unit. The held-out tier is REPORTED beside it at both "
    "units and never decides."
)

EXCLUSION_SCOPE = "either"
EXCLUSION_SCOPE_RATIONALE = (
    "D-07 says ANY adapter-off success excludes: a fact with >= 1 adapter-off answered question "
    "in EITHER tier is excluded from its population — the strictest reading. Counted and "
    "published as `excluded n / 56`; the same rule holds for the 8 IN (trivially: adapter-off is "
    "already 0/1008 at the control)."
)

MEMBERSHIP_RULE = (
    "D-14: a fact is ANSWERED (a member) under adapter-on when >= 1 of its DECIDING_TIER "
    "questions has k > 0 — existential, exactly as the artifact's `per_fact.n_answerable`. A "
    "question is answered when >= 1 of its 9 draws contains the value (`contains_value`). With "
    "D-07 requiring adapter-off = 0, a single adapter-on hit cannot come from the base."
)

# D-10: the FACT decides. By reference to the frozen pin — no second definition of the unit.
UNIT = mitigation_unit.PRIVACY_UNIT
UNIT_RATIONALE = (
    "The canary is the fact (`mitigation_unit.PRIVACY_UNIT`); its ~14 questions are correlated "
    "re-measurements. n_IN = 8, n_OUT <= 56 after D-07. The question unit (n_IN = 112, "
    "n_OUT <= 784) travels beside it in the same record and never decides; draws are never a unit."
)

# =================================================================================================
# (4) THE INSTRUMENT'S ARITHMETIC (D-09, D-11, D-13).
# =================================================================================================

# ONE z, by reference (D-11); delta is the claim's delta, by reference (D-02).
Z = erasure_gate._Z_ONE_SIDED_95
DELTA = mitigation_unit.DELTA
JOINT_COVERAGE = (
    ">= 0.90 (Bonferroni over two one-sided 95% Wilson bounds, z = erasure_gate._Z_ONE_SIDED_95)"
)


def _prove_count(name, value):
    """``prove_reproduction``'s register: an ``int`` that is not a ``bool``, or a refusal."""
    _prove(
        isinstance(value, int) and not isinstance(value, bool),
        f"{name} is {value!r}, which is not an int (bool excluded). This formula takes COUNTS; a "
        "float came out of arithmetic and a bool would compare True against 1",
    )


def epsilon_lower(members, n_in, nonmembers, n_out, *, delta=None):
    """D-09: the MAX of the two hypothesis-testing constraints of (epsilon, delta)-DP, from the
    SAME two imported Wilson bounds::

        direction_1 = ln((TPR_lb - delta) / FPR_ub)
        direction_2 = ln((1 - FPR_ub - delta) / (1 - TPR_lb))

    Degenerate cases are NAMED in ``degenerate``, never clipped: a negative direction stays
    negative, and when both directions are undefined ``epsilon_lower`` is ``None``.
    """
    for name, value in (
        ("members", members),
        ("n_in", n_in),
        ("nonmembers", nonmembers),
        ("n_out", n_out),
    ):
        _prove_count(name, value)
    delta = DELTA if delta is None else delta
    tpr_lb = phase20_gate_coverage.wilson_lower_bound(members, n_in)
    fpr_ub = erasure_gate.wilson_upper_bound(nonmembers, n_out)
    degenerate, d1, d2 = [], None, None
    if tpr_lb - delta <= 0:
        degenerate.append("TPR_lb <= delta: direction 1 undefined")
    else:
        d1 = math.log((tpr_lb - delta) / fpr_ub)
    if 1 - fpr_ub - delta <= 0:
        degenerate.append("FPR_ub >= 1 - delta: direction 2 undefined")
    elif tpr_lb >= 1:
        # Unreachable at z > 0 (a Wilson lower bound never reaches 1); named anyway.
        degenerate.append("TPR_lb == 1: direction 2 undefined")
    else:
        d2 = math.log((1 - fpr_ub - delta) / (1 - tpr_lb))
    finite = [d for d in (d1, d2) if d is not None]
    return {
        "members_answered": members,
        "n_in": n_in,
        "nonmembers_answered": nonmembers,
        "n_out": n_out,
        "tpr_lb": tpr_lb,
        "fpr_ub": fpr_ub,
        "direction_1": d1,
        "direction_2": d2,
        "epsilon_lower": max(finite) if finite else None,
        "degenerate": degenerate,
        "z": Z,
        "delta": delta,
        "joint_coverage": JOINT_COVERAGE,
    }


def auditor_ceiling(n_in, n_out):
    """D-13: the perfect reading — TPR = n_IN/n_IN, FPR = 0/n_OUT — on the REAL n's after D-07
    exclusions. Any epsilon_upper at or above it could not have failed (Pitfall 6: exclusions
    lower n_OUT and therefore the ceiling)."""
    return epsilon_lower(n_in, n_in, 0, n_out)["epsilon_lower"]


# =================================================================================================
# (5) THE VERDICT DOMAIN (D-05, D-13) — erasure_gate.VERDICTS' register, three values, one-sided.
# =================================================================================================

VERDICTS = ("BROKEN", "CONSISTENT", "INCONCLUSIVE")
ONE_SIDED_CLAUSE = "this test can only accuse; CONSISTENT is not 'verified correct'"
CEILING_CLAUSE = "epsilon_upper >= auditor_ceiling: this comparison could not have failed"


def verdict(eps_lower, eps_upper, *, power_passed):
    """BROKEN iff epsilon_lower > epsilon_upper; else CONSISTENT iff the power gate passed; else
    INCONCLUSIVE. ``None`` (both directions degenerate) can never accuse."""
    if eps_lower is not None and eps_lower > eps_upper:
        result = "BROKEN"
    else:
        result = "CONSISTENT" if power_passed else "INCONCLUSIVE"
    _prove(result in VERDICTS, f"verdict {result!r} outside {VERDICTS}")
    return result


def point_verdict(reading, epsilon_upper, *, power, auditor_ceiling):
    """One point's verdict with its ``reasons`` — strings carrying the numbers (D-05). The
    sanctioned epsilon sentence (``phase25_epsilon.report_epsilon``) is attached by the driver
    beside each point; nothing here renders a bare epsilon beyond these numeric reasons."""
    d1, d2 = reading["direction_1"], reading["direction_2"]
    degenerate = reading["degenerate"]
    result = verdict(reading["epsilon_lower"], epsilon_upper, power_passed=power["passed"])
    reasons = [
        f"members answered {reading['members_answered']}/{reading['n_in']} and nonmembers "
        f"answered {reading['nonmembers_answered']}/{reading['n_out']} at the unit {UNIT!r}",
        f"TPR_lb = {reading['tpr_lb']:.4f} (Wilson lower), FPR_ub = {reading['fpr_ub']:.4f} "
        f"(Wilson upper), z = {reading['z']}, delta = {reading['delta']}",
        "direction_1 = " + (f"{d1:.4f}" if d1 is not None else degenerate[0]),
        "direction_2 = " + (f"{d2:.4f}" if d2 is not None else degenerate[-1]),
        f"epsilon_lower = {reading['epsilon_lower']!r} vs epsilon_upper = {epsilon_upper!r}: "
        f"{result} — {ONE_SIDED_CLAUSE}",
        f"joint coverage {JOINT_COVERAGE}",
    ]
    if epsilon_upper >= auditor_ceiling:
        reasons.append(f"{CEILING_CLAUSE} (auditor_ceiling = {auditor_ceiling!r})")
    if not power["passed"]:
        reasons.append(
            f"{POWER_SENTENCE} Power gate FAILED: control epsilon_lower = "
            f"{power['control_epsilon_lower']!r} < threshold {power['threshold']!r}"
        )
    return {"verdict": result, "reasons": reasons}


# =================================================================================================
# (6) THE WAIVER CONTINUATION (D-07) AND THE PUBLICATION-OBLIGATION CONTINUATION (D-40, D-18, D-19).
# =================================================================================================

WAIVER_CONTINUATION = {
    "supersedes": "phase21_filler.GUESSABILITY_WAIVER",
    "why": (
        "its premise 'filler is never scored' is false from this phase: the adapter-off arm IS "
        "the guessability probe (D-07); any filler fact with an adapter-off hit in either tier is "
        "excluded, counted and published"
    ),
    "committed": COMMITTED,
}

# WHY A PYTHON CONSTANT AND NOT A `scripts/_addendum.py` APPEND: `_addendum.append_addendum` is a
# markdown writer requiring a `pending` placeholder the Phase-25 note does not carry, and
# `scripts/phase21_unit_continuation.py:14-20` records that a Python contract is continued by a
# Python module. The obligation is DATA a Phase-28 test resolves against the artifact, not prose
# (T-26-03). It EXTENDS `phase25_prereg.PUBLICATION_OBLIGATION` by reference; the original tuple
# is untouched. Same `(field_path, why)` shape; paths address INTO `results/phase26_canary.json`.
SUPERSEDES_OBLIGATION = "phase25_prereg.PUBLICATION_OBLIGATION"

PUBLICATION_OBLIGATION_CONTINUATION = (
    (
        "power_gate.passed",
        "whether the instrument had POWER at the control, published WITH `power_gate.sentence` "
        f"('{POWER_SENTENCE}') and the observed `control_epsilon_lower` vs `threshold`. Without "
        "it, 15 CONSISTENT readings from a blind auditor are indistinguishable from 15 approvals",
    ),
    (
        "auditor_ceiling",
        "the largest epsilon_lower this instrument could have produced on the real n's after "
        "D-07 exclusions. A reader must see it before reading any CONSISTENT: an epsilon_upper "
        "above it could not have failed",
    ),
    (
        "reachable_claims",
        "`k/15` — how many of the 15 published claims sit BELOW the auditor's ceiling and were "
        "therefore actually testable (D-13). Published at the top of the artifact, never inferred",
    ),
    (
        "exclusions.out.n",
        "the count of filler facts EXCLUDED from the OUT population by the D-07 precondition "
        "(any adapter-off hit in either tier), published as `excluded n / 56` — never hidden",
    ),
    (
        "points.<key>.verdict.verdict",
        "a member of `phase26_prereg.VERDICTS`. Phase 28 may quote any epsilon ONLY beside this "
        "verdict and its reasons (D-18); an epsilon quoted without its canary verdict is a claim "
        "detached from the one test that could have accused it",
    ),
    (
        "points.<key>.verdict.reasons",
        "the numbers behind the verdict — counts at the fact unit, both Wilson bounds with z, "
        "both directions or their named degenerate case, epsilon_lower vs epsilon_upper, the "
        "one-sided clause, the joint coverage and the D-13 ceiling clause where it applies",
    ),
    (
        "<artifact absent>",
        "if `results/phase26_canary.json` does not exist, the report must say 'audit not "
        "executed / partial' beside EVERY epsilon it quotes, citing the dated D-19 entry in "
        "results/phase26_operational_note.md",
    ),
)
