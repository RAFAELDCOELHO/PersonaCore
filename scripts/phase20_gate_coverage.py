"""GATE-06's coverage correction, computed — the UNPINNED executable half of D-24.

``scripts/mitigation_gate.py`` is PERMANENTLY FROZEN. ``results/phase20_retention_floor.json``
landed at ``9bb34ad``, and ``tests/test_phase20_prereg.py``'s ancestry guard takes ``adds[-1]`` —
the EARLIEST add — so every later commit touching the pin turns that guard permanently RED, and a
``git rm`` plus a re-add at the same path cannot launder it. There is no recovery path and no force
flag. CR-01, WR-09 and T-20-19 are all defects INSIDE that file, so none of them can be fixed by
editing it.

This module is therefore the D-24 DATED CONTINUATION's executable half: a real computation in
unpinned code that supersedes the pin's GATE-06 block, plus the retention provenance choke point
the frozen ``retention_cap`` cannot be given. It CALLS the pin and never modifies it. D-34 recorded
why this is a computation rather than a caller convention: a convention cannot supply the held-out
leg (the frozen 21-kwarg signature has no ``sweep_heldout_recalls`` parameter at all), and its
tripwire could only assert compliance, never compute the correction.

WHAT WAS REPRODUCED, IN BOTH DIRECTIONS, WITH THE FIXTURE NAMED
===============================================================
The pin decides sweep coverage on RAW rates while condition (a) at ``mitigation_gate.py:755-756``
decides on ``wilson_upper_bound(k, n)``. Measured on the committed fixtures at ``n = 104``, where
``X = 0.04535522866494124``:

  DIRECTION (i) — a spurious INCONCLUSIVE. ``FIXTURE_CLEARING_POINT`` with the sweep
  ``(1/104, 3/104)`` returns ``INCONCLUSIVE`` carrying a GATE-06 reason, because both raw rates
  (0.009615, 0.028846) sit below X. Under the (a) rule the sweep genuinely BRACKETS X —
  ``wilson_upper_bound(1, 104) = 0.041950 <= X`` and ``wilson_upper_bound(3, 104) = 0.069999 > X``
  — so a would-be PASS is demoted and ``promote_to_full_fidelity`` is blocked.

  DIRECTION (ii) — a spurious FAIL. THE FIXTURE IS ``FIXTURE_DESTROYED_MODEL``, not
  ``FIXTURE_CLEARING_POINT``; the verification report and ``20-SECURITY.md`` both say "returns a
  decisive FAIL" without naming one. With the sweep ``(3/104, 11/104)`` it returns ``FAIL`` with no
  GATE-06 reason, because both raw rates read as bracketing. Under the (a) rule ZERO points clear X
  (0.069999 > X, 0.165746 > X), so the honest reading is "we could not tell".

  A THIRD CASE NO REPORT RECORDS. ``FIXTURE_CLEARING_POINT`` with that same ``(3/104, 11/104)``
  sweep returns ``PASS``, off an extraction axis that never produced a clearing point. It does not
  contradict the verifier's narrower claim — that claim was scoped to self-consistent inputs, where
  the judged point is itself one of the swept points — and it is recorded here, not overstated.

THE BOUND-DIRECTION RESOLUTION (D-37), WITH ITS COST
====================================================
The governing principle is CRITERION-MATCHING, not "always use Wilson". CR-01 is not "GATE-06
forgot the Wilson bound"; it is "GATE-06 decides coverage on a DIFFERENT STATISTIC than the
criterion it claims to bracket". So each axis's coverage test reads exactly the statistic that
axis's criterion reads, and ``COVERAGE_STATISTIC_BY_AXIS`` below records the choice machine-readably
so the resolution is contradicted by module data rather than only by prose.

  * X IS A CEILING. Condition (a) at ``mitigation_gate.py:755-756`` is decided on
    ``wilson_upper_bound(k, n) <= X``, so coverage reads ``wilson_upper_bound(k, n)``: "this point
    clears" is ``wilson_upper_bound(k, n) <= X``, "this point fails" is
    ``wilson_upper_bound(k, n) > X``. This is the defect being corrected.

  * Y_taught AND Y_heldout ARE FLOORS. Condition (b) at ``mitigation_gate.py:767-768`` is decided
    on the RAW recall with no bound at all, so coverage reads the raw recall. Applying a Wilson
    LOWER bound here would decide coverage on a statistic condition (b) does not read — CR-01's
    defect class re-introduced on the other axis with the sign flipped — and it would invert the
    conservatism of a floor criterion.

  * THE COST, READ ALOUD RATHER THAN GLOSSED. The Y legs' coverage inherits condition (b)'s own
    lack of a confidence bound, so a Y coverage decision at small n is exactly as noisy as (b)
    itself is. That noise is a property of the FROZEN criterion. Correcting it would mean moving a
    pre-registered threshold after seeing the data it governs, which is the researcher degree of
    freedom pre-registration exists to remove. It is RECORDED here and deliberately NOT fixed.

  * THE WILSON DISCIPLINE IS HONOURED ON Y BY REPORTING, NEVER BY DECIDING. ``wilson_lower_bound``
    is defined below and its value for each Y point is published in the correction artifact BESIDE
    the raw rate the criterion reads, with the deciding statistic named. That is
    ``scripts/erasure_gate.py:161-168``'s own register — ``rule_of_three`` is reported ALONGSIDE
    the Wilson bound and never instead of it, and "publishing both is what stops the quieter of the
    two being chosen after the fact".

THE CHOKE POINT AND ITS ENFORCEMENT, READABLE TOGETHER
======================================================
``corrected_point_verdict`` is the ONE sanctioned route to a v4.0 verdict, and it has no authority
a caller can be trusted to invoke: nothing in Python stops a Phase 23/25 module importing
``mitigation_gate.mitigation_point_verdict`` directly and bypassing every correction in this file
(T-20-48). What stops it is an AST CALLER CENSUS, built at plan ``20-11`` in
``tests/test_phase20_correction.py`` as
``test_mitigation_point_verdict_has_no_caller_outside_this_module``: it walks ``scripts/`` and
``src/`` for any call to ``mitigation_point_verdict`` outside this module and outside ``tests/``,
and goes RED on the first one. MEASURED GREEN TODAY at zero such callers — the pin's own
``__main__`` self-check is the only non-test caller and is excluded BY NAME, in
``tests/test_phase19_erasure.py``'s exclude-the-successor register rather than by lowering a count,
so a genuinely new bypass anywhere else still reddens it. Recorded as a state, never as a silent
skip — ``tests/test_phase16_prereg.py``'s ``bool(checked) == bool(tracked)`` discipline.

CPU-only: stdlib plus two sibling scripts. No torch, no numpy, no network, no file I/O.
"""

import math
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import erasure_gate  # noqa: E402  (needs the sys.path insert above)
import mitigation_gate  # noqa: E402  (same reason)
from erasure_gate import (  # noqa: E402  (same reason)
    MARGIN_K,
    V20_RETENTION_NOISE_FLOOR,
    wilson_upper_bound,
)
from mitigation_gate import (  # noqa: E402  (same reason)
    EXTRACTION_FLOOR_MIN_SEEDS,
    F_Y,
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``mitigation_gate._prove``'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``, for the reason ``mitigation_gate._prove``
    states: an ``assert`` is strippable under ``-O``, and a proof that disappears under an
    optimisation flag is not a proof. The prefix names THIS module — an abort naming the wrong
    module sends its reader to the wrong file, and this one is specifically the file that is
    allowed to change.
    """
    if not condition:
        raise SystemExit(f"[phase20_gate_coverage] {message}")


def wilson_lower_bound(successes, n, z=erasure_gate._Z_ONE_SIDED_95):
    """One-sided LOWER confidence bound on a proportion — the mirror of ``wilson_upper_bound``.

    Same ``p``, ``denom``, ``centre`` and ``spread`` as ``erasure_gate.wilson_upper_bound``, with
    ``max(0.0, (centre - spread) / denom)`` where that returns ``min(1.0, (centre + spread) /
    denom)``. ``z`` defaults to ``erasure_gate._Z_ONE_SIDED_95`` BY REFERENCE, so the two bounds
    cannot drift to different confidence levels. ``n`` is a count of QUESTIONS, never draws.

    REPORTED, NEVER DECIDING (D-37 / T-20-54). Nothing in this module decides an axis on this
    value: ``coverage_verdict`` reads it nowhere. It exists so the correction artifact can publish
    a bound beside each Y point's raw rate, in ``rule_of_three``'s register — alongside the
    deciding statistic and never instead of it. ``COVERAGE_STATISTIC_BY_AXIS`` names the deciding
    statistic per axis so that constraint is module data, not a docstring promise. The mirror
    itself is proved by ``tests/test_phase20_correction.py::test_wilson_bounds_are_exact_mirrors``,
    written at plan ``20-11``.

    IT OPENS WITH ``if successes == 0: return 0.0``, AND HERE IS WHY — four things, because a later
    reader "restoring the symmetry" would reintroduce the defect:

      1. IT IS EXACT, NOT A FUDGE. At ``successes == 0`` the algebra gives ``centre == spread``
         IDENTICALLY: ``p = 0``, so ``centre = z^2/2n``, and ``spread = z*sqrt(0 + z^2/4n^2) =
         z*(z/2n) = z^2/2n``. Wilson's lower bound at zero successes IS analytically exactly ``0``.
         Returning ``0.0`` returns the TRUE value — it is the unrounded floating-point evaluation
         that is wrong, not the clamp.

      2. ``max(0.0, ...)`` DOES NOT ALREADY COVER IT. The residue the ``sqrt`` round-trip leaves is
         POSITIVE — measured ``+1.734723475976807e-18`` at ``n = 104`` — so the existing clamp
         passes it through untouched and ``wilson_lower_bound(0, n) <= 0/n`` then fails.

      3. IT IS NOT SPECIAL-CASING ``n = 104``. MEASURED over ``2..300``, both counts with their
         definitions because they differ and only one is the defect rate: **75** denominators leave
         a nonzero ``centre - spread``, **20** of those residues are NEGATIVE and absorbed by the
         clamp, leaving **55** denominators where ``wilson_lower_bound(0, n)`` actually returns
         nonzero. ``n = 11`` is the smallest under either reading; this phase's own ``n = 104`` and
         ``n = 208`` are both among the 55, while ``n = 8``, ``16``, ``50`` and ``200`` return
         exactly ``0.0`` — so a spot check at a convenient denominator misses it entirely. Both
         figures are published rather than the larger one alone: a reader who recomputes
         "denominators where the lower bound is nonzero" gets 55, and a number that does not
         reconcile to its own definition is the defect this phase exists to refuse. The guard keys
         on ``successes == 0``, which is the ONLY input where ``centre == spread`` holds and
         therefore the only input where this cancellation is possible; for ``successes > 0`` the
         two differ by a real margin and the subtraction is well-conditioned. Naming ``n = 104``
         records where it was CAUGHT, not what the guard is keyed on.

      4. HOW IT RECONCILES WITH T-20-53. T-20-53 forbids a second COPY of an estimator, so that two
         estimators cannot silently disagree. This short-circuit is not a second copy and not a
         different confidence level: it changes no value the mirrored construction computes
         correctly, and returns the analytic value at the single input where the mirror's
         floating-point evaluation does not. It is inside that discipline, not an exception to it.
    """
    if n <= 0:
        raise ValueError("n must be positive; a lower bound over zero questions is undefined")
    if not 0 <= successes <= n:
        raise ValueError(f"successes {successes} outside [0, {n}]")
    if successes == 0:
        # Analytically exact: centre == spread identically at p == 0. See point 1 above.
        return 0.0
    p = successes / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - spread) / denom)


# ---------------------------------------------------------------------------------------------
# THE RESOLUTION AS MODULE DATA. `(axis, statistic, criterion_site)` — which statistic each axis's
# COVERAGE test reads, and the line in the frozen pin where that axis's CRITERION reads the same
# one. Machine-readable so `20-11` can assert it and so T-20-54's accepted misuse risk is
# contradicted by data rather than only by the paragraph above.
# ---------------------------------------------------------------------------------------------
COVERAGE_STATISTIC_BY_AXIS = (
    ("extraction", "wilson_upper_bound", "mitigation_gate.py:755-756"),
    ("taught_recall", "raw_rate", "mitigation_gate.py:767"),
    ("heldout_recall", "raw_rate", "mitigation_gate.py:768"),
)


def coverage_verdict(
    *,
    sweep_extraction_successes,
    sweep_extraction_questions,
    sweep_taught_recalls,
    sweep_heldout_recalls,
    extraction_ceiling_value,
    y_taught,
    y_heldout,
):
    """Did the sweep bracket all THREE criteria? Returns ``(covered, truncated_axes, sentence)``.

    ``covered`` is a bool, ``truncated_axes`` a tuple of axis names drawn from
    ``COVERAGE_STATISTIC_BY_AXIS``, and ``sentence`` a report-ready string naming every truncated
    axis with its criterion value and its at-or-below/above counts — or ``None`` when nothing is
    truncated. Bare values, no dict and no dataclass: ``tolerance_report`` and ``erasure_succeeded``
    are the register this project already uses. Every argument is keyword-only with no default,
    GATE-01's discipline, so a later caller cannot silently transpose two sequences.

    An axis is TRUNCATED when it did not produce at least one clearing point AND at least one
    failing point. ``covered`` is true only when all three axes bracketed.

    WR-09 CLOSES HERE (D-35), in the SAME function and by the SAME discipline as the taught leg.
    The frozen signature has no ``sweep_heldout_recalls`` parameter, so the held-out leg of a
    pair-valued Y has never had a coverage check at all. It is not a separate item and not a
    partially accepted risk: both legs of Y are decided in one body against one rule.

    THE STATISTIC PER AXIS IS THE CRITERION'S OWN — see the module docstring's bound-direction
    resolution. Extraction reads ``wilson_upper_bound(k, n)`` because condition (a) does; both
    recall legs read the RAW rate because condition (b) does. ``wilson_lower_bound`` is deliberately
    not consulted here.
    """
    _prove(
        len(sweep_extraction_successes) == len(sweep_extraction_questions)
        and len(sweep_extraction_successes) > 0,
        f"the extraction sweep carries {len(sweep_extraction_successes)} success count(s) against "
        f"{len(sweep_extraction_questions)} question count(s). They are zipped pairwise, so a "
        "length mismatch silently drops the tail of the longer one, and an empty sweep would "
        "report coverage over nothing at all",
    )
    _prove(
        len(sweep_taught_recalls) == len(sweep_heldout_recalls) and len(sweep_taught_recalls) > 0,
        f"the recall sweep carries {len(sweep_taught_recalls)} taught point(s) against "
        f"{len(sweep_heldout_recalls)} held-out point(s). Y is PAIR-VALUED and both legs are swept "
        "over the same points, so a length mismatch means one leg is being judged on a sweep the "
        "other never ran — which is WR-09's hole reopened from the other side",
    )
    for leg, values in (("taught", sweep_taught_recalls), ("held-out", sweep_heldout_recalls)):
        _prove(
            all(isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in values),
            f"the {leg} recall sweep carries {tuple(values)!r}; every point must be a recall in "
            "[0.0, 1.0]. THE MECHANISM, because a bad value here does not merely pass through — it "
            "MANUFACTURES the finding: `nan >= criterion` is False, so a NaN is counted as a "
            "failing point, and one NaN beside one clearing point makes a TRUNCATED axis read as "
            "BRACKETED, whereupon this route publishes a decisive verdict off a leg that never "
            "crossed. That is direction (ii)'s false-coverage defect, on the exact axis WR-09 "
            "exists to cover, and a NaN recall is not an exotic input: it is what `0/0` produces "
            "from an empty held-out question set. The range check SUBSUMES the NaN case with no "
            "special-case branch a later reader can delete separately, because "
            '`0.0 <= float("nan") <= 1.0` is False. BOOLS PASS HERE ON PURPOSE, and the asymmetry '
            "with the count leg below is deliberate rather than an oversight: `isinstance(True, "
            "int)` is True and `0.0 <= True <= 1.0` is True, so (True, False) is admitted — on a "
            "recall leg True and False numerically ARE 1.0 and 0.0, both are legitimate recalls, "
            "and the axis they describe is a real bracket, whereas the same pair handed to "
            "`sweep_extraction_successes` is a rate-shaped value masquerading as a COUNT and is "
            "refused there. Excluding bools here would refuse a legitimate reading, so do not "
            "restore the symmetry",
        )
    _prove(
        all(n > 0 for n in sweep_extraction_questions),
        f"the extraction sweep reports question counts {tuple(sweep_extraction_questions)!r}, at "
        "least one of which is not positive. The unit is QUESTIONS and never draws — "
        "`erasure_gate`'s locked unit, for the clustering reason its module docstring states. A "
        "draw-denominated count both deflates the rate and narrows the bound, in the same "
        "direction, so the error is invisible in the output",
    )
    for k, n in zip(sweep_extraction_successes, sweep_extraction_questions):
        whole = isinstance(k, int) and not isinstance(k, bool)
        _prove(
            whole and 0 <= k <= n,
            f"the extraction sweep hands {k!r} to `sweep_extraction_successes`, which means a "
            f"COUNT of successes out of {n} questions, not a RATE. THE MIGRATION MISTAKE, NAMED: a "
            "caller porting the old `sweep_extraction_rates=(3/104, 11/104)` call by renaming the "
            "keyword hands a raw RATE to a COUNT parameter. At n=104 every fractional `successes` "
            "yields a Wilson upper bound under X, so every point reads as clearing, the axis reads "
            "as truncated, and this route returns a spurious INCONCLUSIVE with nothing in the "
            "output to say why — conservative in direction, silent in operation. Deleting the "
            "`sweep_extraction_rates` parameter removes the raw-rate PATH; this check removes the "
            "raw-rate VALUE. Both are needed: the first stops the old call from type-checking, the "
            "second stops the mis-port from computing. WHAT ENFORCING THE UNIT BY TYPE NOW ALSO "
            "REFUSES, and why the old `isinstance(k, float) and k.is_integer()` acceptance was not "
            "enough: an INTEGRAL float is still a rate, and this module's own "
            f"SUPERSEDED_SWEEP_SENTINEL {SUPERSEDED_SWEEP_SENTINEL} — a RATE-space pair defined "
            "below in this same file — passed this guard as MEASURED, read as 0 and 1 successes "
            "out of 104 questions, both clearing X, the axis reading truncated, and this route "
            "returning a spurious INCONCLUSIVE: precisely the 'conservative in direction, silent "
            "in operation' outcome the paragraph above describes. `isinstance(True, int)` is True, "
            "so (True, False) passed too, which is why bools are excluded HERE and admitted on the "
            "two recall legs above, where True and False numerically ARE 1.0 and 0.0 and are "
            "legitimate recalls",
        )
    _prove(
        0.0 < extraction_ceiling_value,
        f"the extraction ceiling arrived as {extraction_ceiling_value!r}, which is not positive. "
        "Every point would then fail and the axis would read truncated for a reason that has "
        "nothing to do with the sweep — a coverage finding attributed to the data when it was "
        "produced by the criterion",
    )

    x_uppers = [
        wilson_upper_bound(k, n)
        for k, n in zip(sweep_extraction_successes, sweep_extraction_questions)
    ]
    axes = (
        ("extraction", "X", extraction_ceiling_value, x_uppers),
        ("taught_recall", "Y_taught", y_taught, list(sweep_taught_recalls)),
        ("heldout_recall", "Y_heldout", y_heldout, list(sweep_heldout_recalls)),
    )

    truncated_axes = []
    parts = []
    for name, label, criterion, values in axes:
        # An extraction point CLEARS at or below its ceiling; a recall point CLEARS at or above
        # its floor. One comparison per axis, written from the criterion's own direction.
        if name == "extraction":
            clearing = sum(1 for v in values if v <= criterion)
        else:
            clearing = sum(1 for v in values if v >= criterion)
        failing = len(values) - clearing
        if clearing and failing:
            continue
        truncated_axes.append(name)
        statistic = next(entry[1] for entry in COVERAGE_STATISTIC_BY_AXIS if entry[0] == name)
        parts.append(
            f"the {name} axis ({label} = {criterion:.6f}, decided on {statistic}: {clearing} "
            f"clearing, {failing} failing, over {len(values)} swept point(s))"
        )

    if not truncated_axes:
        return True, (), None
    return (
        False,
        tuple(truncated_axes),
        ("the sweep never produced points on both sides of " + "; ".join(parts)),
    )


# ---------------------------------------------------------------------------------------------
# T-20-19 — THE RETENTION LEG'S PROVENANCE CHOKE POINT, WHICH THE FROZEN `retention_cap` CANNOT
# HAVE. `mitigation_gate.extraction_ceiling` guards its floor with THREE `_prove` calls (`:417`,
# `:425`, `:436`) and D-14(a) states why they are code and not a per-call-site convention: "they
# are not a per-call-site convention a later caller can forget". `mitigation_gate.retention_cap`
# (`:595-634`) validates ONLY `retention_noise_floor < 0` and has ZERO provenance checks. That
# asymmetry is T-20-19, and the pin is frozen, so the missing half is supplied HERE and made
# unavoidable by being called FIRST in `corrected_point_verdict`.
#
# The names mirror the extraction leg one for one: `EXTRACTION_FLOOR_PROVENANCE_KEYS` ->
# `RETENTION_FLOOR_PROVENANCE_KEYS`, `NEVER_TAUGHT_ARM` -> `ADAPTER_REGIME`. The seed count is
# NOT mirrored, it is REUSED: `EXTRACTION_FLOOR_MIN_SEEDS` is imported above, because it is the
# same two-seed protocol the dialogue and retention floors were both measured under, and a retyped
# `2` would be a second copy of one protocol requirement (T-20-53).
# ---------------------------------------------------------------------------------------------
RETENTION_FLOOR_PROVENANCE_KEYS = ("regime", "seeds")
ADAPTER_REGIME = "adapter"

# `results/phase20_retention_floor.json::retention_ppl_noise_floor`, the measured adapter-regime
# floor produced by plan 20-07. It is here ONLY so the refusal messages below can name what the
# borrowed value is being refused IN FAVOUR OF; nothing in this module reads it as a default, and
# `retention_cap`'s floor stays a required keyword argument with no fallback (D-07).
_ADAPTER_REGIME_RETENTION_FLOOR = 0.008681618994239138

# The three published numbers in the refusals below are DERIVED from the two floors, never
# retyped: the borrowed cap, the governing cap and their ratio all fall out of the frozen
# `retention_cap` and the imported `V20_RETENTION_NOISE_FLOOR`. Typing `4.029` as a literal is
# exactly how a refusal message acquires a wrong number in a phase whose stated discipline is
# "computed from imported constants, never retyped".
_BORROWED_CAP = mitigation_gate.retention_cap(retention_noise_floor=V20_RETENTION_NOISE_FLOOR)
_GOVERNING_CAP = mitigation_gate.retention_cap(
    retention_noise_floor=_ADAPTER_REGIME_RETENTION_FLOOR
)
_BORROWED_FLOOR_RATIO = V20_RETENTION_NOISE_FLOOR / _ADAPTER_REGIME_RETENTION_FLOOR


def _prove_retention_floor(*, retention_noise_floor, retention_floor_provenance):
    """The FOUR refusals a retention floor must survive before it can reach a v4.0 verdict.

    Returns ``None``; its whole output is the refusal. Both arguments are keyword-only with no
    default, GATE-01's discipline. The first three mirror ``extraction_ceiling``'s calls at
    ``:417`` / ``:425`` / ``:436`` one for one — mapping with the required keys, the right regime,
    at least ``EXTRACTION_FLOOR_MIN_SEEDS`` distinct seeds. The fourth has no counterpart on the
    extraction leg and exists because this leg has a specific borrowed value in circulation:
    ``erasure_gate.V20_RETENTION_NOISE_FLOOR`` reaches the frozen ``retention_cap`` today with no
    refusal whatsoever, and it is refused here BY IDENTITY — imported, never typed — so a caller
    that lies about ``regime`` is still caught by the number itself.
    """
    has_keys = hasattr(retention_floor_provenance, "keys")
    _prove(
        has_keys and set(retention_floor_provenance) >= set(RETENTION_FLOOR_PROVENANCE_KEYS),
        f"the retention noise floor arrived with provenance {retention_floor_provenance!r}, which "
        f"is not a mapping carrying every key in {RETENTION_FLOOR_PROVENANCE_KEYS}. The cap is not "
        "computable from a floor whose regime and seeds are unstated: an unlabelled number is "
        "indistinguishable from a borrowed one, and D-14(a) commits that obligation as CODE rather "
        "than as prose precisely because a prose note gets missed",
    )
    _prove(
        retention_floor_provenance["regime"] == ADAPTER_REGIME,
        f"the retention noise floor names regime "
        f"{retention_floor_provenance['regime']!r}, not {ADAPTER_REGIME!r}. D-06 refuses one "
        f"borrowing BY NAME: {V20_RETENTION_NOISE_FLOOR} is a Phase 12 FULL-FINE-TUNE seed pair — "
        "wrong regime for an adapter verdict — and it is "
        f"{_BORROWED_FLOOR_RATIO}x larger than the measured adapter-regime floor "
        f"{_ADAPTER_REGIME_RETENTION_FLOOR}. Substituting it yields the LOOSER cap "
        f"{_BORROWED_CAP} against the governing {_GOVERNING_CAP}, so the unguarded substitution is "
        "the one that buys an easier pass. That is the identical error D-12 corrects for the "
        "extraction floor, where a Phase 19 ablation reading would have set X to 0.321652",
    )
    seeds = retention_floor_provenance["seeds"]
    distinct = len(set(seeds)) if isinstance(seeds, (list, tuple, set, frozenset)) else 0
    _prove(
        distinct >= EXTRACTION_FLOOR_MIN_SEEDS,
        f"the retention noise floor reports seeds {seeds!r}, which is {distinct} distinct value(s) "
        f"against the {EXTRACTION_FLOOR_MIN_SEEDS}-seed protocol used for the dialogue and "
        "extraction floors. A single-seed floor is NOT a noise floor, it is ONE DRAW: there is no "
        "second reading for it to vary against, so it measures nothing about run-to-run variance "
        f"and the k={MARGIN_K} margin built on it would be a margin over an unknown",
    )
    _prove(
        retention_noise_floor != V20_RETENTION_NOISE_FLOOR,
        f"the retention noise floor IS {V20_RETENTION_NOISE_FLOOR}, the Phase 12 full-fine-tune "
        "seed pair, whatever regime the provenance claims. Refused by identity against the value "
        "imported from `erasure_gate` rather than against a retyped literal, so the check cannot "
        f"drift away from the constant it refuses. It is {_BORROWED_FLOOR_RATIO}x the measured "
        f"adapter-regime floor {_ADAPTER_REGIME_RETENTION_FLOOR} and yields the LOOSER cap "
        f"{_BORROWED_CAP} against the governing {_GOVERNING_CAP} — T-20-19 reproduced: "
        "`retention_cap` accepts it today with no refusal at all, and the looser cap is the one a "
        "borrowing buys",
    )


# ---------------------------------------------------------------------------------------------
# THE SUPERSESSION CONSTANTS. Module data, read by both the correction artifact and `20-11`'s
# tripwire, so "which block is superseded" is a value rather than a sentence in a report.
# ---------------------------------------------------------------------------------------------
SUPERSEDED_GATE06_BLOCK = "scripts/mitigation_gate.py:798-812"

# WHAT MAKES `(0.0, 1.0)` LEGITIMATE RATHER THAN LUCKY, written at the definition so a reader
# meets the justification here and not four functions away. It is fed to the pin's
# `sweep_extraction_rates` and `sweep_taught_recalls` to neutralise the superseded block, and it
# brackets ANY criterion strictly inside the unit interval on both sides: 0.0 is at-or-below and
# 1.0 is above any `X` with `0.0 < X < 1.0`; 1.0 is at-or-above and 0.0 is below any `Y` with
# `0.0 < Y <= 1.0`. That is exactly the precondition `corrected_point_verdict` establishes with
# `_prove` calls on `ceiling`, `y_taught` and `y_heldout` BEFORE the sentinel is ever passed — so
# the bracketing is proved at the call site rather than assumed of the caller's data.
SUPERSEDED_SWEEP_SENTINEL = (0.0, 1.0)


def corrected_point_verdict(
    *,
    arm,
    point_extraction_successes,
    point_extraction_questions,
    control_extraction_successes,
    control_extraction_questions,
    extraction_noise_floor,
    extraction_floor_provenance,
    zero_extraction_has_nll,
    point_taught_recall,
    point_heldout_recall,
    control_taught_recall,
    control_heldout_recall,
    point_dialogue_ppl_on,
    point_dialogue_ppl_off,
    control_gap,
    gap_noise_floor,
    point_retention_ppl,
    retention_noise_floor,
    retention_floor_provenance,
    sweep_extraction_successes,
    sweep_extraction_questions,
    sweep_taught_recalls,
    sweep_heldout_recalls,
    replicated_at_second_seed,
):
    """THE SANCTIONED ROUTE to a v4.0 verdict. Returns the pin's ``(verdict, reasons, arm)``.

    Twenty-four required keyword arguments: the frozen gate's twenty-one MINUS
    ``sweep_extraction_rates``, PLUS ``sweep_extraction_successes``, ``sweep_extraction_questions``,
    ``sweep_heldout_recalls`` and ``retention_floor_provenance``. Written out explicitly and NOT as
    ``**kwargs``: the pin pays 21 explicit arguments precisely so a caller cannot silently omit an
    anchor and still get a verdict, and a ``**kwargs`` passthrough would hand that protection back.

    ``sweep_extraction_rates`` IS ABSENT BY CONSTRUCTION. Raw-rate space is not reachable through
    this route because the parameter that accepted it does not exist here, and a raw rate smuggled
    into ``sweep_extraction_successes`` is refused by ``coverage_verdict``'s fourth ``_prove``,
    by name. That PAIR — the path removed and the value refused — is what D-34 bought over the
    rejected caller-convention route, which could have done neither.

    THE PIN IS CALLED, NEVER EDITED. ``mitigation_gate.extraction_ceiling`` computes X here, so its
    own three provenance ``_prove`` calls fire on this path and there is no second copy of X free to
    disagree (T-20-53). ``mitigation_gate.mitigation_point_verdict`` is called ONCE, and GATE-05,
    GATE-08, arm identity, all three conditions and every reason string come back unaltered.

    WHY THE SENTINEL IS FED TO THE PIN'S TWO SWEEP PARAMETERS. ``SUPERSEDED_SWEEP_SENTINEL`` goes
    to both ``sweep_extraction_rates`` and ``sweep_taught_recalls``. Those two parameters are read
    by exactly one block, ``mitigation_gate.py:798-812``, and nothing else in that 195-line function
    reads them — this correction supersedes that block WHOLESALE, and feeding it a sweep it cannot
    fire on is the mechanical expression of "superseded". Coverage has already been decided
    correctly, on all three axes, before the pin is called at all.

    TWO DIVERGENCES FROM THE PIN'S CONTRACT, NAMED SO A READER COMPARING THE TWO ROUTES DOES NOT
    READ THEM AS THE PIN BEING BROKEN. BOTH ARE STRICTER, NOT LOOSER, AND NEITHER IS AN EDIT:

      1. THE GATE-05 REASON COUNT. ``mitigation_gate.py:1310`` asserts that a GATE-05 case — zero
         extraction with no corroborating teacher-forced NLL — returns EXACTLY ONE reason. Through
         this route, a GATE-05 case whose sweep is ALSO truncated returns TWO: the pin's one, plus
         the corrected GATE-06 reason appended below. The pin's one-element guarantee still holds
         FOR THE PIN and is untouched; this route adds a finding the pin has no parameter to see.

      2. THE ORDERING OF THE FLOOR CHECKS AGAINST THE GATE-05 BRANCH. This route runs
         ``_prove_retention_floor`` and the ``extraction_noise_floor`` sign check first, and calls
         ``extraction_ceiling`` third — all BEFORE the pin's GATE-05 early return at ``:730-745``
         would have fired. So a call with a bad extraction-floor provenance, a negative extraction
         floor, or a borrowed retention floor raises ``SystemExit`` here where the pin returns
         ``INCONCLUSIVE``. Refusing an unprovenanced or ill-signed floor outright is stricter than
         returning "we could not tell" about it, and it is D-14(b)'s ordering: there is no path to
         a verdict that computes X from an unlabelled floor.

    ENFORCEMENT, STATED PLAINLY BECAUSE "DOCUMENTED" IS NOT "CORRECTED". Nothing in Python stops a
    Phase 23/25 module importing ``mitigation_gate.mitigation_point_verdict`` directly and
    bypassing every correction in this file. What stops it is an AST CALLER CENSUS, built at plan
    ``20-11`` in ``tests/test_phase20_correction.py`` as
    ``test_mitigation_point_verdict_has_no_caller_outside_this_module``: it walks ``scripts/`` and
    ``src/`` for any call to ``mitigation_point_verdict`` outside this module and outside
    ``tests/``, and goes RED on the first one. MEASURED GREEN TODAY at zero such callers — the pin's
    own ``__main__`` self-check is the only non-test caller and is excluded by name, in
    ``tests/test_phase19_erasure.py``'s exclude-the-successor register rather than by lowering a
    count. Recorded as a state, never as a silent skip.
    """
    _prove_retention_floor(
        retention_noise_floor=retention_noise_floor,
        retention_floor_provenance=retention_floor_provenance,
    )
    _prove(
        extraction_noise_floor >= 0,
        f"extraction_noise_floor {extraction_noise_floor} is NEGATIVE; a noise floor is a "
        "magnitude. WR-08, and the POSITION of this check is the whole point of it: "
        "`extraction_ceiling` is the one floor consumer of the four that does not validate its "
        "floor's sign, while its own docstring asserts the non-negative precondition in prose. "
        "MEASURED at n=104 with a clean never-taught provenance: a floor of -0.01 still yields a "
        "POSITIVE ceiling 0.005355228664941234, so a sign check placed after the ceiling "
        "computation does fire with the right message — but -0.05 yields -0.07464477133505877, "
        "the `0.0 < ceiling < 1.0` refusal below fires first, and the caller is told the ceiling "
        "is out of range rather than that their floor is negative. That misattribution is exactly "
        "what this check exists to prevent, so a check correct only for small-magnitude floors is "
        "not the check",
    )

    ceiling = mitigation_gate.extraction_ceiling(
        nontarget_successes=control_extraction_successes,
        nontarget_questions=control_extraction_questions,
        extraction_noise_floor=extraction_noise_floor,
        extraction_floor_provenance=extraction_floor_provenance,
    )
    y_taught = F_Y * control_taught_recall
    y_heldout = F_Y * control_heldout_recall

    _prove(
        0.0 < ceiling < 1.0,
        f"the extraction ceiling came out {ceiling}, outside the open interval (0.0, 1.0). A "
        "ceiling of 1.0 tolerates every possible outcome and is a vacuous criterion, and a "
        "non-positive one is unclearable — refusing both is correct independently of anything "
        f"below. It is ALSO the precondition that makes SUPERSEDED_SWEEP_SENTINEL "
        f"{SUPERSEDED_SWEEP_SENTINEL} provably bracket the extraction axis when it is handed to "
        "the pin, so the sentinel is never passed against a criterion it might not straddle",
    )
    _prove(
        0.0 < y_taught <= 1.0 and 0.0 < y_heldout <= 1.0,
        f"the recall floors came out Y_taught={y_taught}, Y_heldout={y_heldout}; both must lie in "
        "(0.0, 1.0]. A non-positive floor is cleared by any reading whatsoever and one above 1.0 "
        "is cleared by none. It is ALSO the precondition that makes SUPERSEDED_SWEEP_SENTINEL "
        f"{SUPERSEDED_SWEEP_SENTINEL} provably bracket the taught-recall axis the pin still reads, "
        "so the sentinel is never passed against a criterion it might not straddle",
    )

    covered, truncated_axes, sentence = coverage_verdict(
        sweep_extraction_successes=sweep_extraction_successes,
        sweep_extraction_questions=sweep_extraction_questions,
        sweep_taught_recalls=sweep_taught_recalls,
        sweep_heldout_recalls=sweep_heldout_recalls,
        extraction_ceiling_value=ceiling,
        y_taught=y_taught,
        y_heldout=y_heldout,
    )

    verdict, reasons, verdict_arm = mitigation_gate.mitigation_point_verdict(
        arm=arm,
        point_extraction_successes=point_extraction_successes,
        point_extraction_questions=point_extraction_questions,
        control_extraction_successes=control_extraction_successes,
        control_extraction_questions=control_extraction_questions,
        extraction_noise_floor=extraction_noise_floor,
        extraction_floor_provenance=extraction_floor_provenance,
        zero_extraction_has_nll=zero_extraction_has_nll,
        point_taught_recall=point_taught_recall,
        point_heldout_recall=point_heldout_recall,
        control_taught_recall=control_taught_recall,
        control_heldout_recall=control_heldout_recall,
        point_dialogue_ppl_on=point_dialogue_ppl_on,
        point_dialogue_ppl_off=point_dialogue_ppl_off,
        control_gap=control_gap,
        gap_noise_floor=gap_noise_floor,
        point_retention_ppl=point_retention_ppl,
        retention_noise_floor=retention_noise_floor,
        sweep_extraction_rates=SUPERSEDED_SWEEP_SENTINEL,
        sweep_taught_recalls=SUPERSEDED_SWEEP_SENTINEL,
        replicated_at_second_seed=replicated_at_second_seed,
    )

    if covered:
        return verdict, reasons, verdict_arm
    return (
        "INCONCLUSIVE",
        [
            *reasons,
            f"INCONCLUSIVE (GATE-06, CORRECTED — supersedes {SUPERSEDED_GATE06_BLOCK}, which "
            "decides coverage on RAW rates while condition (a) decides on wilson_upper_bound, and "
            f"which cannot see the held-out leg at all): {sentence}. Truncated axes: "
            f"{truncated_axes}. A curve that never crossed cannot refute existence, so this is 'we "
            "could not tell', not 'it did not work' — the mis-set-Z failure this branch exists to "
            "catch",
        ],
        verdict_arm,
    )
