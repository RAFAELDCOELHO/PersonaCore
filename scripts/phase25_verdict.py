"""FRONT-04's verdict pass: CPU-only, assembled by IMPORTING the frozen gate, never by authoring.

Nothing in this file decides anything. X comes from ``mitigation_gate.extraction_ceiling``, its
strength sentence from ``mitigation_gate.tolerance_report``, the capacity branch names from
``mitigation_gate.CAPACITY_BRANCHES`` (never spelled here — a module-scope check in
``tests/test_phase25_verdict.py`` asserts no string constant in this file equals one), the
existential's denominator string from ``mitigation_gate.exists_clearing_point``, and all seven of
the Area-7 keyword arguments from their producers in plans 25-21 and 25-22.

THE ONE GENUINELY NEW THING IS `prove_clip_norm_equality`, AND IT IS LOAD-BEARING (D-25). MEASURED
LIVE at HEAD, reproduced in this phase's test file rather than described:
``capacity_comparison`` with ``small_mechanism`` carrying ``clip_norm: 1.0`` and
``large_mechanism`` carrying ``clip_norm: 999.0``, all four ``MECHANISM_KEYS`` equal, returned the
null branch with the reason *"comparability: STRUCTURAL (D-25) - both points agree exactly on all 4
of ('sigma', 'steps', 'delta', 'q')"*. Both of that function's loops iterate
``for key in MECHANISM_KEYS``; neither iterates the mechanisms, so EXTRA KEYS ARE IGNORED RATHER
THAN REFUSED. Because ``std = sigma * C`` (``src/personacore/privacy/dpsgd.py``), two points at
equal nominal sigma and different ``C`` carry DIFFERENT NOISE SCALE while passing the gate's
equality check. ``clip_norm`` cannot join ``MECHANISM_KEYS``: ``scripts/mitigation_gate.py`` is
ancestry-guarded and any commit to it after ``results/phase20_*`` exists reddens the guard
permanently. So the gap is closed CALLER-SIDE, here, before every comparison.

TWO CORRECTIONS THIS MODULE CARRIES IN PLACE, BOTH MEASURED, NEITHER EDITING THE ORIGINAL.

  1. D-42's TOLERANCE FIGURE. ``25-CONTEXT.md``'s D-42 reads "tolerance = at most 2 successes of
     416". The gate's OWN reporter says ZERO. See `extraction_ceiling_and_tolerance`.

  2. D-48/D-49's RETENTION CAP. ``.planning/STATE.md`` and D-49 record the cap as 4.029, the
     BORROWED reading. The cap that actually governs a v4.0 verdict is
     ``phase20_gate_coverage._GOVERNING_CAP`` = 3.9085032379884783, because
     ``_prove_retention_floor`` raises ``SystemExit`` on the borrowed floor. D-49's conclusion
     holds A FORTIORI under it: the governing cap is TIGHTER, so the squeeze the frontier lives in
     is stricter, never looser. Both readings travel in
     ``phase25_condition_c.RETENTION_LEG_BINDS_AT_ANCHOR``; neither is loosened and neither is
     deleted. See `retention_floor_used`.

THE VERDICT CALL GOES THROUGH THE SANCTIONED ROUTE, NOT THROUGH THE PIN (deviation from 25-02's
Task 1(f), recorded rather than silently taken).
``tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module``
is a COMMITTED REPO-WIDE CENSUS: it walks ``scripts/`` and ``src/`` and goes RED on any call to, or
import of, ``mitigation_point_verdict`` outside ``scripts/phase20_gate_coverage.py``. The plan told
this module to call the pin directly; the repository refuses it, and the census names the route to
take instead. ``phase20_gate_coverage.corrected_point_verdict`` calls the pin ONCE and returns its
``(verdict, reasons, arm)`` unaltered, while adding three corrections a direct caller would not
get: real coverage on the extraction axis (raw-rate space is UNREACHABLE — the parameter that
accepted it does not exist on that route), coverage on the held-out leg (the frozen 21-kwarg
signature has no ``sweep_heldout_recalls`` parameter at all), and a retention-provenance check.
Section R3's staging conclusion is UNCHANGED and in fact strengthened: the sanctioned route takes
FOUR whole-curve sequences where the pin takes two, so a per-point verdict is even less computable
at point time.
"""

import inspect
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import erasure_gate  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)
import mitigation_gate  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (plan 25-21 — six of the seven Area-7 kwargs)
import phase25_gate05  # noqa: E402  (plan 25-22 — the seventh)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``mitigation_gate._prove``'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof. It derives from
    ``BaseException``, so a test asserting one of these refusals must name ``SystemExit`` —
    ``pytest.raises(Exception)`` does NOT catch it.
    """
    if not condition:
        raise SystemExit(f"[phase25_verdict] {message}")


# =============================================================================================
# ===== D-42's OBJECT IDENTITY, MADE A RUNTIME PROPERTY RATHER THAN A COMMENT =====
# =============================================================================================

_prove(
    mitigation_gate.wilson_upper_bound is erasure_gate.wilson_upper_bound,
    "mitigation_gate.wilson_upper_bound is not erasure_gate.wilson_upper_bound. D-42 requires X to "
    "be computed by THE one-definition-per-statistic bound this repository already ships, not by a "
    "second copy free to drift from it. Object identity is the only form of that requirement that "
    "cannot go stale: a value comparison would pass against a re-implementation that happens to "
    "agree today",
)
_prove(
    mitigation_gate.MARGIN_K is erasure_gate.MARGIN_K,
    "mitigation_gate.MARGIN_K is not erasure_gate.MARGIN_K. X is "
    "wilson_upper_bound(k, n) + MARGIN_K * extraction_noise_floor, so a second copy of k would "
    "move the published ceiling while every name in the expression still read correctly",
)


# =============================================================================================
# ===== THE FROZEN CONSTANTS, RESOLVED AND NEVER RETYPED =====
# =============================================================================================

NEVER_TAUGHT_RECORD = _ROOT / "results" / "phase23_never_taught.json"

# CAL-03 / D-08. `epsilon_independent_of_n` is a MEASURED verdict, not a caller preference: this
# record reports epsilon_n8 == epsilon_n64 == 24.38161088311366 at T == 4 on both sides, and its
# `verdict` field is what plan 23-13 read. `fallback_epsilon_tolerance` stays None because D-26
# DELIBERATELY DID NOT SET IT — on this route the fallback is never taken, so the third chosen
# constant this project refused to pick stays unpicked rather than defaulted.
CAL03_RECORD = _ROOT / "results" / "phase23_cal03_wiring.json"

# `teach_persona` and `phase18_extraction` both put torch in `sys.modules` on import (measured by
# plan 25-22), and this module is CPU-only and torch-free by contract. Their module-level literals
# are read from source through the mechanism 25-22 shipped and validated — never imported, and
# never retyped either, because a retyped copy is free to stop agreeing.
DP_ARMS = tuple(phase25_gate05._committed_literal("teach_persona", "DP_ARMS"))
ADV_ARMS = tuple(phase25_gate05._committed_literal("teach_persona", "ADV_ARMS"))
GATED_TIER = phase25_gate05._committed_literal("phase18_extraction", "GATED_TIER")
REPORTED_TIER = phase25_gate05._committed_literal("phase18_extraction", "REPORTED_TIER")

_prove(
    all(leg.startswith(mitigation_gate.ARMS[0]) for leg in DP_ARMS)
    and not any(leg.startswith(mitigation_gate.ARMS[0]) for leg in ADV_ARMS),
    f"the committed leg tuples {DP_ARMS} / {ADV_ARMS} no longer pair with the gate's closed arm "
    f"set {mitigation_gate.ARMS} by name. ARM_LEGS below zips them, and a zip whose order is "
    "assumed rather than checked would route an adversarial leg into the DP-only capacity "
    "instrument — the exact confusion D-23 exists to refuse",
)

# The gate's closed arm names -> the committed training-leg names that carry them. Two namespaces,
# deliberately: `mitigation_point_verdict`'s `arm` is 'dp'/'adversarial' (a CLAIM class), while a
# point's own `arm` is 'dp_n8'/'adv_n64' (a RUN). Conflating them is how an adversarial point ends
# up inside a DP-only instrument.
ARM_LEGS = dict(zip(mitigation_gate.ARMS, (DP_ARMS, ADV_ARMS)))

# ---------------------------------------------------------------------------------------------
# THE SEVEN AREA-7 KEYWORD ARGUMENTS, SOURCED FROM THEIR PRODUCERS (D-45..D-51, T-25-11b).
#
# These are the seven of `mitigation_point_verdict`'s twenty-one that had ZERO PRODUCERS across the
# original 20-plan set — six of them condition (c). D-35's epsilon-scoping claim is UNCHANGED and
# still correct; what D-51 supersedes is only its closing "Nothing to fix". The producers are plans
# 25-21 (`phase25_condition_c`) and 25-22 (`phase25_gate05`), and the dated continuation is plan
# 25-07's D35-CONDITION-C. NONE of the seven is fabricated here.
#
# The seventh name is taken from the producing FUNCTION'S OWN `__name__` rather than spelled, so a
# rename in `phase25_gate05` fails here at import instead of silently producing a kwarg the gate
# does not take.
# ---------------------------------------------------------------------------------------------

CONDITION_C_KWARGS = tuple(
    phase25_condition_c.CONDITION_C_FIELDS[: phase25_condition_c.CONDITION_C_VERDICT_FIELD_COUNT]
)
GATE05_KWARG = phase25_gate05.zero_extraction_has_nll.__name__
AREA7_KWARGS = CONDITION_C_KWARGS + (GATE05_KWARG,)

_PIN_PARAMS = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
_PIN_KWONLY = frozenset(
    name
    for name, parameter in _PIN_PARAMS.items()
    if parameter.kind is inspect.Parameter.KEYWORD_ONLY
)

_prove(
    frozenset(AREA7_KWARGS) <= _PIN_KWONLY,
    f"the Area-7 names {sorted(frozenset(AREA7_KWARGS) - _PIN_KWONLY)} are not keyword-only "
    "parameters of the frozen mitigation_point_verdict. Resolved through `inspect.signature`, "
    "NEVER by grepping scripts/mitigation_gate.py: that file discusses every one of these names in "
    "its own prose, so a textual check over it measures the documentation and not the signature. A "
    "producer for a kwarg the gate does not take produces nothing, and the verdict stays "
    "uncomputable exactly as it was across the whole 20-plan set",
)
_prove(
    len(AREA7_KWARGS) == len(frozenset(AREA7_KWARGS)) == 7,
    f"the Area-7 set resolved to {AREA7_KWARGS}, which is not seven distinct names. Six condition-"
    "(c) inputs plus the GATE-05 flag is the count measurement produced; a different count means "
    "one of the two producers changed its published surface and the verdict is assembling against "
    "an unknown",
)

# The per-point fields `curve_verdicts` reads off a committed point record. Named as a tuple so a
# missing one fails with the field name rather than as a bare KeyError three frames down.
POINT_RECORD_FIELDS = (
    "point_extraction_successes",
    "point_extraction_questions",
    "point_taught_recall",
    "point_heldout_recall",
    "point_dialogue_ppl_on",
    "point_dialogue_ppl_off",
    "point_retention_ppl",
    GATE05_KWARG,
    "replicated_at_second_seed",
)

# The per-capacity sigma=0 control reading. `adapter_on`/`adapter_off` are `measure_condition_c`'s
# own shape (plan 25-21); the two recall legs are what condition (b) is gated against.
CONTROL_READING_FIELDS = ("adapter_on", "adapter_off", "taught_recall", "heldout_recall")

ADVERSARIAL_CAPACITY_RULE_ABSENT = (
    "THERE IS NO COMMITTED ADVERSARIAL CAPACITY RULE, AND THIS IS NAMED RATHER THAN PATCHED "
    "(D-23). `mitigation_gate.capacity_comparison` is a DP-ONLY instrument: it takes NO `arm` "
    "argument at all -- zero occurrences of the name in its body -- and it `_prove`s that all four "
    "of MECHANISM_KEYS ('sigma', 'steps', 'delta', 'q') are present in BOTH mechanism mappings and "
    "compare exactly equal. The adversarial arm has no sigma, no delta and no q; its sweep axis is "
    "a mixture ratio and its record carries `accounting: null`, which states the same fact "
    "structurally. So GATE-10 CANNOT RUN ON THE ADVERSARIAL ARM, and inventing a capacity rule for "
    "it here would be a threshold authored after the phase that spends the compute had already "
    "started -- the one ordering this project's pre-registration discipline exists to forbid. The "
    "absence is published beside the DP capacity verdict so a reader does not read it as an "
    "omission, and `capacity_verdict` refuses an adversarial point BEFORE the gate is reached."
)


# =============================================================================================
# ===== (a) THE NEVER-TAUGHT ANCHORS, WITH THE LEDGER-9 CORRECTION APPLIED =====
# =============================================================================================


def never_taught_anchors():
    """Condition (a)'s four anchors from ``results/phase23_never_taught.json``. Exactly four keys.

    SECTION-LEDGER ROW 9, CORRECTED IN PLACE. That row reads "the pooled block is passed VERBATIM".
    Measured: ``extraction_ceiling(**blob["pooled"])`` raises

        TypeError: extraction_ceiling() got an unexpected keyword argument 'draws_per_question'

    because the pooled block carries NINE keys (``draws_per_question``, ``nontarget_questions``,
    ``nontarget_successes``, ``pooling_rule``, ``rate``, ``seed``, ``tier``, ``total_draws``,
    ``unit``) and ``extraction_ceiling`` takes four. "Verbatim" therefore means TWO fields lifted
    out of ``pooled`` -- ``nontarget_successes`` and ``nontarget_questions`` -- PLUS TWO read from
    the record's TOP LEVEL, ``extraction_noise_floor`` and ``extraction_floor_provenance``. Never a
    splat.

    THESE COUNTS ARE THE NEVER-TAUGHT ARM'S, NOT THE SIGMA=0 CONTROL'S, and the distinction is
    enforced rather than remembered: ``extraction_ceiling`` ``_prove``s
    ``extraction_floor_provenance["arm"] == NEVER_TAUGHT_ARM`` at ITS OWN choke point, so a
    control's counts handed in here abort loudly. The two ``_prove`` calls below duplicate nothing
    the gate does not already check -- they fail at ASSEMBLY time, where the record is still in
    view, rather than four frames deeper.
    """
    blob = json.loads(NEVER_TAUGHT_RECORD.read_text(encoding="utf-8"))
    pooled = blob["pooled"]
    provenance = blob["extraction_floor_provenance"]

    _prove(
        provenance["arm"] == mitigation_gate.NEVER_TAUGHT_ARM,
        f"the committed floor names arm {provenance['arm']!r}, not "
        f"{mitigation_gate.NEVER_TAUGHT_ARM!r}. X is not computable from a floor whose arm is "
        "wrong: D-12 refuses one such borrowing BY NAME, and the gate's own provenance check is "
        "the choke point this assertion front-runs so the failure names the record",
    )
    _prove(
        len(set(provenance["seeds"])) == mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS + 3,
        f"the committed floor reports {len(set(provenance['seeds']))} distinct seed(s) "
        f"{provenance['seeds']!r}; the never-taught protocol is the five-seed SEED_LADDER. The "
        f"frozen gate only requires {mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS}, so this is the "
        "STRICTER check and it is asserted here rather than assumed from the gate passing",
    )
    _prove(
        pooled["tier"] == GATED_TIER,
        f"the pooled block is the {pooled['tier']!r} tier, not the gated {GATED_TIER!r}. Only "
        f"core_held_out feeds the gate (D-05); {REPORTED_TIER!r} is dispatched and reported and "
        "never enters a verdict, and reducing the wrong tier into X would move the ceiling",
    )

    return {
        "control_extraction_successes": pooled["nontarget_successes"],
        "control_extraction_questions": pooled["nontarget_questions"],
        "extraction_noise_floor": blob["extraction_noise_floor"],
        "extraction_floor_provenance": provenance,
    }


# =============================================================================================
# ===== (b) X AND ITS PUBLISHED SENTENCE -- D-42's FIGURE CORRECTED BY THE GATE'S OWN REPORTER =====
# =============================================================================================


def extraction_ceiling_and_tolerance():
    """``(X, tolerated, fraction, sentence)`` -- both from the frozen gate, neither re-derived.

    D-42's PUBLISHED FIGURE IS SUPERSEDED BY A MEASUREMENT, AND THE ORIGINAL IS LEFT STANDING.
    ``25-CONTEXT.md``'s D-42 states the tolerance as "at most 2 successes of 416". The gate's own
    ``tolerance_report`` returns ``(0, 0.0, "... ZERO TOLERANCE ...")``. THE ARITHMETIC, because a
    correction without its arithmetic is just a second assertion: condition (a) compares a WILSON
    BOUND to a WILSON BOUND (``mitigation_gate.py``, ``upper = wilson_upper_bound(point_successes,
    point_questions)`` then ``a_ok = upper <= ceiling``), NOT a raw count to a ceiling. With a
    measured ``extraction_noise_floor`` of exactly 0.0 the ``MARGIN_K * floor`` term vanishes, so

        X                        = 0.006461685297443485
        wilson_upper_bound(0,416) = 0.006461685297443485   <= X, by identity
        wilson_upper_bound(1,416) = 0.01070184962521955    >  X

    ONE leaked question of 416 already exceeds the ceiling. Two cannot be tolerated because one
    cannot.

    THE FIVE-SEED POOLING IS REJECTED FOR A STRONGER REASON THAN D-42 GAVE, AND THE STRONGER ONE IS
    WHAT MUST BE PRE-REGISTERED. D-42 rejects it as too tight. It is not merely tight: pooling the
    five seeds into 2080 questions gives a ceiling of 0.001299052313275338, and
    ``tolerance_report`` RAISES ``ValueError`` on it --

        "ceiling 0.001299052313275338 sits below wilson_upper_bound(0, 416) =
         0.006461685297443485 - no outcome clears it, not even a perfect one, so there is no
         tolerance to report. This is NOT the zero-tolerance regime and must not be published as
         one."

    STRUCTURAL UNSATISFIABILITY, not tightness: no outcome whatsoever clears the pooled ceiling,
    including a perfect one. The committed record's own ``pooling_rule`` gives the independent
    reason -- the five seeds re-ask the SAME questions of five different adapters, so a pooled
    denominator counts correlated re-measurements as independent questions.
    """
    anchors = never_taught_anchors()
    # THE SECOND HALF OF LEDGER ROW 9, and the reason `**anchors` is NOT written here either.
    # `never_taught_anchors` returns the VERDICT's four parameter names; `extraction_ceiling` takes
    # `nontarget_successes` / `nontarget_questions`. The two counts are the same measurement under
    # two names -- "control" at the gate, "nontarget" at the ceiling -- so this is a rename, and a
    # splat is wrong at BOTH ends of the record.
    ceiling = mitigation_gate.extraction_ceiling(
        nontarget_successes=anchors["control_extraction_successes"],
        nontarget_questions=anchors["control_extraction_questions"],
        extraction_noise_floor=anchors["extraction_noise_floor"],
        extraction_floor_provenance=anchors["extraction_floor_provenance"],
    )
    tolerated, fraction, sentence = mitigation_gate.tolerance_report(
        ceiling=ceiling, n_questions=anchors["control_extraction_questions"]
    )
    return ceiling, tolerated, fraction, sentence


# =============================================================================================
# ===== (c) THE CALLER-SIDE clip_norm PROVE -- THE ONE HOLE THE FROZEN GATE IGNORES (D-25) =====
# =============================================================================================


def prove_clip_norm_equality(small_mechanism, large_mechanism, *, point_pair):
    """Refuse a capacity comparison whose ``clip_norm`` is absent or diverges. Returns ``None``.

    ``point_pair`` is the two points' identities, carried into the message so a refusal names WHICH
    comparison it refused. Its whole output is the refusal.

    WHY THIS EXISTS CALLER-SIDE AND CANNOT EXIST IN THE GATE. ``scripts/mitigation_gate.py`` is
    ancestry-guarded: any commit to it after ``results/phase20_*`` exists reddens the guard
    permanently, and ``git rm`` plus a re-add at the same path cannot launder it because the guard
    takes ``adds[-1]``, the EARLIEST add. So ``clip_norm`` cannot join ``MECHANISM_KEYS``, and it
    does not need to.
    """
    for name, mechanism in (("small", small_mechanism), ("large", large_mechanism)):
        _prove(
            "clip_norm" in mechanism,
            f"the {name} mechanism of {point_pair!r} carries no 'clip_norm'. THE MEASURED HOLE, "
            "reproduced verbatim so this refusal is not taken on trust: "
            "`capacity_comparison`'s presence loop and its exact-equality loop BOTH iterate "
            "`for key in MECHANISM_KEYS`, and neither iterates the mechanism mappings -- so a key "
            "outside those four is not checked, not reported, and not refused. A live call with "
            "clip_norm 1.0 against 999.0 and all four MECHANISM_KEYS equal returned a branch, with "
            "a reason reading 'both points agree exactly on all 4 of (sigma, steps, delta, q)'. "
            "Since std = sigma * C, an ABSENT clip_norm is an unpinned noise scale, which is the "
            "same defect as a divergent one with the evidence missing as well",
        )
    small_clip = small_mechanism["clip_norm"]
    large_clip = large_mechanism["clip_norm"]
    _prove(
        small_clip == large_clip,
        f"the two points of {point_pair!r} carry clip_norm {small_clip!r} vs {large_clip!r}. "
        "THE GATE WOULD HAVE ACCEPTED THIS: `capacity_comparison`'s presence loop and its "
        "exact-equality loop BOTH iterate `for key in MECHANISM_KEYS`, so extra keys are IGNORED "
        "rather than refused, and a live call with clip_norm 1.0 against 999.0 -- a 999x "
        "divergence -- returned a branch whose reason reads 'both points agree exactly on all 4 "
        "of (sigma, steps, delta, q)'. Because std = sigma * C, two points at EQUAL NOMINAL SIGMA "
        "and DIFFERENT C carry different noise scale while passing the gate's equality check, so "
        "the comparison would read the mechanism instead of capacity -- exactly what D-25's zero "
        "tolerance constant exists to prevent. clip_norm cannot join MECHANISM_KEYS (the gate is "
        "ancestry-guarded and frozen), so the equality is proved HERE, before every call",
    )


# =============================================================================================
# ===== (d) DP-ONLY SCOPING -- THE ADVERSARIAL ARM REFUSED BEFORE THE GATE (D-23) =====
# =============================================================================================


def capacity_verdict(small_point, large_point, *, small_cleared, large_cleared):
    """GATE-10 for ONE DP capacity pair. Returns ``capacity_comparison``'s ``(branch, reasons)``.

    A point is a mapping carrying ``arm`` (a committed leg name such as the first member of
    ``DP_ARMS``), ``capacity`` and ``mechanism``. THE ONLY CALL TO ``capacity_comparison`` ANYWHERE
    IN THIS MODULE IS THE ONE BELOW, which is what makes the arm refusal structural rather than
    conventional -- an AST walk in this phase's test file asserts that every such call is lexically
    inside this function.

    TWO REFUSALS, BOTH BEFORE THE GATE, AND THE ORDER IS DELIBERATE (deviation from 25-02's Task
    1(d), recorded rather than silently taken). The plan ordered the ``clip_norm`` proof FIRST. It
    is second, because an ADVERSARIAL point has no mechanism at all -- no sigma, no delta, no q and
    no C -- so asking about its ``clip_norm`` first is a category error that reports a MISSING
    NOISE SCALE where the real defect is a DP-ONLY INSTRUMENT HANDED A NON-DP POINT. That is the
    misattribution class ``phase20_gate_coverage``'s own extraction-floor sign check documents
    ("the caller is told the ceiling is out of range rather than that their floor is negative"), and
    it would also make 25-02's own ``test_an_adversarial_point_is_refused_before_the_gate``
    unwritable, since that test asserts the arm message. Both refusals still precede the gate, and
    the ``clip_norm`` proof still runs before EVERY ``capacity_comparison`` call, which is the
    property D-25 needs.

    ``epsilon_independent_of_n`` IS READ FROM CAL-03's COMMITTED RECORD, NEVER CHOSEN HERE, and
    ``fallback_epsilon_tolerance`` STAYS ``None`` -- D-26's third chosen constant, deliberately
    unset in Phase 20 and not smuggled in here. On the measured route the fallback is unreachable,
    so leaving it unset costs nothing and defaulting it would cost the refusal.
    """
    for name, point in (("small", small_point), ("large", large_point)):
        _prove(
            point["arm"] in DP_ARMS,
            f"the {name} point names arm {point['arm']!r}, which is not one of the committed DP "
            f"legs {DP_ARMS}. {ADVERSARIAL_CAPACITY_RULE_ABSENT}",
        )

    point_pair = (small_point["arm"], large_point["arm"])
    prove_clip_norm_equality(
        small_point["mechanism"], large_point["mechanism"], point_pair=point_pair
    )

    cal03 = json.loads(CAL03_RECORD.read_text(encoding="utf-8"))
    _prove(
        cal03["epsilon_n8"] == cal03["epsilon_n64"],
        f"CAL-03's committed record reports epsilon_n8 {cal03['epsilon_n8']!r} against "
        f"epsilon_n64 {cal03['epsilon_n64']!r}. Its `verdict` field is what selects the primary "
        "route below, and a verdict that no longer agrees with the two readings it was derived "
        "from is a halt, not a preference",
    )

    return mitigation_gate.capacity_comparison(
        small_capacity=small_point["capacity"],
        large_capacity=large_point["capacity"],
        small_cleared=small_cleared,
        large_cleared=large_cleared,
        small_mechanism=small_point["mechanism"],
        large_mechanism=large_point["mechanism"],
        epsilon_independent_of_n=cal03["verdict"],
        fallback_epsilon_tolerance=None,
    )


# =============================================================================================
# ===== (e) THE ARM EXISTENTIALS -- FRONT-04 MET BY IMPORTING (D-32) =====
# =============================================================================================


def arm_existential(points, arm):
    """``exists_clearing_point``'s own ``(exists, claim)``, returned UNMODIFIED.

    ``points`` is a sequence of the 3-tuples the verdict route returns. The claim string is the
    gate's, verbatim -- no reformatting, no rounding, no re-wording. When nothing cleared it CARRIES
    ITS OWN DENOMINATOR ("0 of N point(s) examined returned PASS"), because an existential's
    strength is the size of the set it searched, and "no point cleared" and "no point was scored"
    are different findings.

    NOTHING IS AUTHORED HERE FOR THE NULL RESULT. ``null-at-both-capacities`` is already a member of
    ``CAPACITY_BRANCHES`` and ``_CAPACITY_DISPATCH[(False, False)]`` is already dispatch-total at
    module scope in the frozen gate, proved there rather than here. The pre-registered null is a
    NAMED BRANCH reached through a real call -- never an absence of output.
    """
    _prove(
        arm in mitigation_gate.ARMS,
        f"arm {arm!r} is not in the gate's closed set {mitigation_gate.ARMS}. The existential is "
        "computed PER ARM: a DP clear carries a FORMAL (epsilon, delta) guarantee and an "
        "adversarial clear carries evidence about the attacks actually run, so unioning them "
        "publishes the stronger claim on the weaker evidence (GATE-07 / D-28)",
    )
    return mitigation_gate.exists_clearing_point(points=points, arm=arm)


# =============================================================================================
# ===== (f) + (g) THE WHOLE-CURVE VERDICT STAGE, WITH THE SEVEN KWARGS FROM THEIR PRODUCERS =====
# =============================================================================================


def retention_floor_used():
    """(c)'s retention floor, PROVED admissible by ``phase20_gate_coverage._prove_retention_floor``.

    Returns 0.008681618994239138, ``phase20_gate_coverage._ADAPTER_REGIME_RETENTION_FLOOR``, through
    ``phase25_condition_c.retention_floor_for_verdict()`` -- which runs the five refusals a
    retention floor must survive BEFORE returning it.

    D-48's NAMED FLOOR NEVER REACHES A VERDICT, AND THAT IS MEASURED RATHER THAN ASSERTED. D-48
    named ``erasure_gate.V20_RETENTION_NOISE_FLOOR`` = 0.06893 as the floor to import "as-is".
    ``_prove_retention_floor`` RAISES ``SystemExit`` on it -- the Phase 12 full-fine-tune seed pair
    cannot govern an adapter-regime verdict. HONOURING THE REFUSAL BUYS NO EASIER PASS, which is the
    half that matters: see the comment above `_GOVERNING_CAP` below.
    """
    return phase25_condition_c.retention_floor_for_verdict()


# THE GOVERNING CAP IS 3.9085032379884783, derived LIVE from `mitigation_gate.retention_cap` on the
# adapter-regime floor -- NOT the 4.029 that `.planning/STATE.md` and CONTEXT's D-49 record, which
# is `retention_cap` on the BORROWED floor. D-49's conclusion holds A FORTIORI under the governing
# reading, because the governing cap is TIGHTER: at the Phase-19 anchor taught reading the headroom
# is -0.3112566543480071 against the borrowed -0.1907598923364855, so the squeeze the frontier lives
# in is STRICTER, never looser. Both readings travel in
# `phase25_condition_c.RETENTION_LEG_BINDS_AT_ANCHOR`; both are published and neither is loosened.
_GOVERNING_CAP = phase20_gate_coverage._GOVERNING_CAP


def curve_verdicts(records, arm, capacity, *, control_readings_by_arm):
    """One LEG's verdicts. Returns ``[(verdict, reasons, arm)]``, one 3-tuple per record, in order.

    SECTION R3 -- WHY THIS IS A DISTINCT CPU-ONLY STAGE THAT RUNS AFTER A LEG COMPLETES, AND WHY A
    PER-POINT VERDICT IS NOT COMPUTABLE AT POINT TIME. The verdict route takes WHOLE-CURVE inputs:
    the frozen pin reads ``sweep_extraction_rates`` and ``sweep_taught_recalls`` in its GATE-06
    did-the-curve-cross block, and the sanctioned route takes FOUR such sequences
    (``sweep_extraction_successes``, ``sweep_extraction_questions``, ``sweep_taught_recalls``,
    ``sweep_heldout_recalls``). Computing a verdict while the leg is still running would read a
    TRUNCATED curve and could report GATE-06 INCONCLUSIVE for a curve that crosses two points later
    -- a budget artifact published as a finding. So the curve is assembled first and judged second.
    The stage is cheap: no torch, no model load, arithmetic over committed numbers.

    THE SEVEN AREA-7 KWARGS ARE SOURCED, NEVER FABRICATED (T-25-11b). Three are per point and come
    off the record (``point_dialogue_ppl_on``, ``point_dialogue_ppl_off``, ``point_retention_ppl``).
    ``control_gap`` is PER CAPACITY (D-47), taken from THAT capacity's own sigma=0 control through
    ``phase25_condition_c.control_gap_for_capacity`` and routed through
    ``prove_control_gap_not_borrowed`` first -- it sets BOTH edges of (c)'s dialogue band, so a
    borrowed one silently moves the admissible band in both directions at once at the capacity that
    did not produce it. ``gap_noise_floor`` and ``retention_noise_floor`` come from
    ``phase25_condition_c``; ``zero_extraction_has_nll`` from ``phase25_gate05``, whose
    ``prove_flag_is_a_bool`` refuses the ``(False, reason)`` PAIR that would silently DISARM the
    GATE-05 branch on exactly the run that needed it -- ``not (False, '...')`` is ``False``.

    ``control_readings_by_arm`` IS THE WHOLE MAPPING, NOT THIS LEG'S READING (deviation from
    25-02's three-positional signature, recorded rather than silently taken). ``control_gap``,
    ``control_taught_recall`` and ``control_heldout_recall`` have no per-point source, and
    ``prove_control_gap_not_borrowed``'s refusal is PAIRWISE ACROSS ARMS -- handed one reading its
    loop is vacuous and proves nothing. Taking the mapping is what keeps that refusal live.
    """
    _prove(
        arm in ARM_LEGS,
        f"arm {arm!r} is not one of the gate's closed claim classes {tuple(ARM_LEGS)}. This is the "
        "CLAIM class ('dp'/'adversarial'), not the run's leg name -- conflating the two is how an "
        "adversarial clear gets published as a formal guarantee",
    )
    legs = [leg for leg in ARM_LEGS[arm] if leg.endswith(f"n{capacity}")]
    _prove(
        len(legs) == 1,
        f"capacity {capacity!r} matches {legs} of the committed {arm!r} legs {ARM_LEGS[arm]}. "
        "Exactly one leg carries a capacity; zero means the capacity was never committed and two "
        "means the leg names stopped being distinguishable by it",
    )
    leg_arm = legs[0]

    _prove(
        bool(records),
        f"no point records were supplied for leg {leg_arm!r}. A verdict pass over an empty leg "
        "would report a MISSING MEASUREMENT as a curve, and GATE-06's coverage check would then be "
        "taken over nothing at all",
    )
    for index, record in enumerate(records):
        missing = tuple(field for field in POINT_RECORD_FIELDS if field not in record)
        _prove(
            not missing,
            f"point record {index} of leg {leg_arm!r} is missing {missing} of the required "
            f"{POINT_RECORD_FIELDS}. Every one of these is a REQUIRED keyword argument of the "
            "verdict route with no default, which is the protection the twenty-one-argument "
            "signature was bought for: a caller must not be able to omit an anchor and still get a "
            "verdict",
        )

    # D-47's refusal, run over the WHOLE mapping so the pairwise loop is non-vacuous.
    phase25_condition_c.prove_control_gap_not_borrowed(control_readings_by_arm)
    _prove(
        leg_arm in control_readings_by_arm,
        f"leg {leg_arm!r} has no sigma=0 control reading among {sorted(control_readings_by_arm)}. "
        "D-47 makes control_gap PER CAPACITY; without this leg's own control there is no "
        "admissible band for it, and borrowing the other capacity's is the exact substitution "
        "prove_control_gap_not_borrowed refuses",
    )
    control = control_readings_by_arm[leg_arm]
    missing = tuple(field for field in CONTROL_READING_FIELDS if field not in control)
    _prove(
        not missing,
        f"the {leg_arm!r} control reading is missing {missing} of {CONTROL_READING_FIELDS}. Y is "
        "gated at F_Y times the point's OWN v4.0 retrained control on each leg (GATE-04 / D-16), "
        "never derived from v2.0's published recall pair, so a missing control leg has no "
        "substitute that is not a borrowed run-to-run variance",
    )

    anchors = never_taught_anchors()
    control_gap = phase25_condition_c.control_gap_for_capacity(control)
    gap_floor, _gap_recipe = phase25_condition_c.gap_noise_floor()
    retention_floor = retention_floor_used()
    retention_provenance = {
        "regime": phase20_gate_coverage.ADAPTER_REGIME,
        "seeds": phase25_condition_c.RETENTION_FLOOR_DISCLOSURE["seeds"],
    }

    # THE WHOLE CURVE, ASSEMBLED BEFORE ANY POINT IS JUDGED. Raw-rate space is unreachable on this
    # route by construction: the parameter that accepted it does not exist there.
    sweep_extraction_successes = [record["point_extraction_successes"] for record in records]
    sweep_extraction_questions = [record["point_extraction_questions"] for record in records]
    sweep_taught_recalls = [record["point_taught_recall"] for record in records]
    sweep_heldout_recalls = [record["point_heldout_recall"] for record in records]

    verdicts = []
    for index, record in enumerate(records):
        flag = phase25_gate05.prove_flag_is_a_bool(
            record[GATE05_KWARG], point_key=f"{leg_arm}[{index}]"
        )
        verdicts.append(
            phase20_gate_coverage.corrected_point_verdict(
                arm=arm,
                point_extraction_successes=record["point_extraction_successes"],
                point_extraction_questions=record["point_extraction_questions"],
                zero_extraction_has_nll=flag,
                point_taught_recall=record["point_taught_recall"],
                point_heldout_recall=record["point_heldout_recall"],
                control_taught_recall=control["taught_recall"],
                control_heldout_recall=control["heldout_recall"],
                point_dialogue_ppl_on=record["point_dialogue_ppl_on"],
                point_dialogue_ppl_off=record["point_dialogue_ppl_off"],
                control_gap=control_gap,
                gap_noise_floor=gap_floor,
                point_retention_ppl=record["point_retention_ppl"],
                retention_noise_floor=retention_floor,
                retention_floor_provenance=retention_provenance,
                sweep_extraction_successes=sweep_extraction_successes,
                sweep_extraction_questions=sweep_extraction_questions,
                sweep_taught_recalls=sweep_taught_recalls,
                sweep_heldout_recalls=sweep_heldout_recalls,
                replicated_at_second_seed=record["replicated_at_second_seed"],
                **anchors,
            )
        )
    return verdicts
