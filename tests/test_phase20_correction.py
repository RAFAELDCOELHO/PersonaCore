"""The ARMED TRIPWIRES for the GATE-06 coverage correction — watched RED, then watched GREEN.

``scripts/phase20_gate_coverage.py`` ships the correction. This file is what makes it enforceable.
A guard nobody has watched fail is a guard nobody has verified: five mitigations were watched
failing and restored byte-identically in this phase (``20-SECURITY.md``'s Watched-RED evidence
table), and the ones below join them.

**Why a continuation and not a fix.** ``scripts/mitigation_gate.py`` is PERMANENTLY FROZEN.
``results/phase20_retention_floor.json`` landed at ``9bb34ad``, and
``tests/test_phase20_prereg.py``'s ancestry guard takes ``adds[-1]`` — the EARLIEST add — so every
later commit touching the pin reddens that guard permanently, and a ``git rm`` plus a re-add at the
same path cannot launder it (proved across five observed states at plan 20-03). There is no
recovery path and no force flag. CR-01, WR-09, WR-08 and T-20-19 are all defects INSIDE that file,
so none of them is fixable by editing it. The sanctioned path is a DATED CONTINUATION
(``scripts/_addendum.py``, D-24) plus a real computation in unpinned code that CALLS the pin —
which is ``scripts/phase20_gate_coverage.py`` — plus this test file, which is the half that makes
the correction bite instead of merely existing.

**What is at stake in the verdicts.** The frozen GATE-06 block at ``mitigation_gate.py:798-812``
decides sweep coverage of the extraction axis on the RAW rate, while condition (a) at ``:755-756``
decides that same axis on ``wilson_upper_bound(k, n)`` against the same ceiling. Since
``rate <= wilson_upper_bound(rate * n, n)`` always, the coverage test is systematically shifted
BELOW the criterion it claims to bracket, and it mislabels in BOTH directions:

  DIRECTION (i) — a spurious INCONCLUSIVE. ``FIXTURE_CLEARING_POINT`` swept at ``(1, 3)`` over 104
  questions genuinely brackets X under the (a) rule, yet the pin reports the axis never crossed. A
  would-be PASS is demoted and ``promote_to_full_fidelity`` is withheld.

  DIRECTION (ii) — a spurious FAIL. ``FIXTURE_DESTROYED_MODEL`` swept at ``(3, 11)`` has ZERO
  points clearing X under the (a) rule, yet the pin judges the axis covered and returns a decisive
  FAIL with no GATE-06 reason at all. "We could not tell" is published as "it did not work".

  A THIRD CASE NO REPORT RECORDS. ``FIXTURE_CLEARING_POINT`` under that same ``(3, 11)`` sweep is a
  ``PASS`` from the pin, off an extraction axis on which nothing cleared. Asserted below with its
  honest limit stated: it does not contradict the verifier's narrower no-spurious-PASS claim, which
  was scoped to self-consistent inputs where the judged point is itself one of the swept points.

**Every audit here is an AST walk or goes through ``scripts/_prose.py::normalized``.** This phase
produced FOUR independent instances of a ``grep -c`` / ``X in source`` audit matching the docstring
that EXPLAINS the pattern rather than the pattern itself (``.planning/REQUIREMENTS.md``'s
``| RPT-02 |`` traceability row). Prose ABOUT a number is not the number, and only a parse can tell
them apart — ``tests/test_phase20_prereg.py:797-802`` argues it at length. No ``grep -c`` and no
``X in source`` substring check appears below.

CPU-only: stdlib plus three sibling scripts and ``git``. No torch, no numpy, no network.
"""

import ast
import inspect
import math
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import erasure_gate  # noqa: E402  (needs the sys.path insert above)
import mitigation_gate  # noqa: E402  (same reason)
import phase20_gate_coverage as coverage  # noqa: E402  (same reason)

CORRECTION_REL = "results/phase20_gate_coverage_correction.md"
PAYLOAD_REL = "results/phase20_gate_coverage_correction.json"
RETENTION_FLOOR_REL = "results/phase20_retention_floor.json"
CORRECTION_PATH = _ROOT / CORRECTION_REL
PAYLOAD_PATH = _ROOT / PAYLOAD_REL
RETENTION_FLOOR_PATH = _ROOT / RETENTION_FLOOR_REL

# The Phase 20 GATE-06 marker TRIPLE, declared here rather than imported from the throwaway script
# that ran once. `tests/test_phase19_correction.py:49-59` states the register: both halves of the
# pair travel to the writer together — that pairing is why `scripts/_addendum.py` exists at all —
# and the COMMITTED TEST MODULE is the pair's source of truth, not the driver.
#
# TAKEN FROM THE COMMITTED FILE, NOT FROM `20-10-PLAN.md`. The plan hardcoded `2026-08-20`; the
# continuation was written and its numbers re-derived on `2026-08-21` and is dated accordingly
# (`20-10-SUMMARY.md` deviation 1). A dated continuation whose heading date is not its writing date
# puts a false date on the one artifact whose entire purpose is honest provenance.
PENDING = "**Phase 20 GATE-06 coverage correction: not yet recorded.**"
RECORDED = (
    "**Phase 20 GATE-06 coverage correction: recorded in the dated continuation at the end of "
    "this file.**"
)
ADDENDUM_HEADING = (
    "## Addendum — 2026-08-21 — the coverage statistic, the held-out leg, and the retention "
    "floor's missing tripwire"
)

# The sweep the reproductions are driven at. COUNTS out of QUESTIONS, never rates — the whole
# migration mistake this file also arms a tripwire against.
N = 104
DIRECTION_I_SUCCESSES = (1, 3)
DIRECTION_II_SUCCESSES = (3, 11)
QUESTIONS = (N, N)

# `corrected_point_verdict`'s two arguments the frozen fixtures cannot supply, because the frozen
# 21-keyword signature has no parameter for either. `20-10-SUMMARY.md` records that every `evidence`
# verdict in the published JSON was measured with exactly these, so a different default here would
# make the tripwire disagree with the artifact it exists to protect.
DEFAULT_HELDOUT_SWEEP = (0.30, 0.20)
DEFAULT_RETENTION_PROVENANCE = {"regime": "adapter", "seeds": (1337, 2024)}


def _corrected_call(fixture_name, **overrides):
    """The corrected-route kwargs for a committed fixture, READ OFF the fixture, never retyped.

    Takes ``mitigation_gate.<fixture_name>``, drops ``sweep_extraction_rates`` (which does not
    exist on the corrected route) and supplies the two arguments the frozen signature has no
    parameter for. Hand-copying twenty-one keyword arguments into a test is how a fixture and its
    guard drift apart.

    THE MERGE FORM IS LOAD-BEARING, and MEASURED. The obvious one-expression version —
    ``dict(f, sweep_heldout_recalls=..., retention_floor_provenance=..., **overrides)`` — raises
    ``TypeError: dict() got multiple values for keyword argument`` the moment a caller overrides
    either default. That is every retention-provenance refusal case below and the WR-09 held-out
    truncation case, i.e. exactly the cases that carry the correction's two new axes. Merging the
    overrides INTO the defaults first and splatting once is what keeps them reachable.
    """
    fixture = getattr(mitigation_gate, fixture_name)
    kwargs = {k: v for k, v in fixture.items() if k != "sweep_extraction_rates"}
    base = {
        "sweep_heldout_recalls": DEFAULT_HELDOUT_SWEEP,
        "retention_floor_provenance": dict(DEFAULT_RETENTION_PROVENANCE),
    }
    base.update(overrides)
    return dict(kwargs, **base)


def _pin_call(fixture_name, **overrides):
    """The frozen pin's kwargs for a committed fixture.

    ``dict(fixture, key=value)`` and NEVER ``**fixture, key=value``: the committed fixtures already
    carry all twenty-one keywords, so the double-splat form raises MEASURED ``TypeError:
    mitigation_gate.mitigation_point_verdict() got multiple values for keyword argument
    'sweep_extraction_rates'``. Same collision the merge form above exists for.
    """
    return dict(getattr(mitigation_gate, fixture_name), **overrides)


def _ceiling_for(fixture_name):
    """X, obtained by CALLING ``extraction_ceiling`` on the fixture's own arguments.

    Never a typed constant. A hand-copied X is a second copy of the criterion, free to stop
    matching the one the verdict is actually read against (T-20-53).
    """
    fixture = getattr(mitigation_gate, fixture_name)
    return mitigation_gate.extraction_ceiling(
        nontarget_successes=fixture["control_extraction_successes"],
        nontarget_questions=fixture["control_extraction_questions"],
        extraction_noise_floor=fixture["extraction_noise_floor"],
        extraction_floor_provenance=fixture["extraction_floor_provenance"],
    )


def _names_gate06(reasons):
    return [index for index, reason in enumerate(reasons) if "GATE-06" in reason]


def test_direction_i_spurious_inconclusive_is_red_on_the_pin_and_green_through_the_correction():
    """DIRECTION (i): a would-be PASS demoted to INCONCLUSIVE by a coverage test on the wrong stat.

    RED and GREEN asserted against EACH OTHER in one body, rather than in two files. The claim is
    differential — the same fixture and the same sweep reach different verdicts through the frozen
    block and through the correction — and a differential claim split across two test functions can
    go half-stale without either half noticing.
    """
    pin_verdict, pin_reasons, _arm = mitigation_gate.mitigation_point_verdict(
        **_pin_call(
            "FIXTURE_CLEARING_POINT",
            sweep_extraction_rates=tuple(k / N for k in DIRECTION_I_SUCCESSES),
        )
    )
    assert pin_verdict == "INCONCLUSIVE", (
        f"the frozen pin returns {pin_verdict!r} on FIXTURE_CLEARING_POINT at the "
        f"{DIRECTION_I_SUCCESSES} / {QUESTIONS} sweep, not the INCONCLUSIVE this correction was "
        "written against. If CR-01 is gone the continuation needs re-reading, not deleting"
    )
    assert "GATE-06" in pin_reasons[-1], (
        f"the pin's INCONCLUSIVE is not attributed to GATE-06: {pin_reasons[-1]!r}. Then it is a "
        "different branch and this test is measuring the wrong defect"
    )

    # The sweep GENUINELY brackets X under condition (a)'s own statistic — which is what makes the
    # pin's INCONCLUSIVE spurious rather than merely conservative. X by call, bounds by call.
    ceiling = _ceiling_for("FIXTURE_CLEARING_POINT")
    low = coverage.wilson_upper_bound(DIRECTION_I_SUCCESSES[0], N)
    high = coverage.wilson_upper_bound(DIRECTION_I_SUCCESSES[1], N)
    assert low <= ceiling < high, (
        f"the sweep {DIRECTION_I_SUCCESSES} / {QUESTIONS} does not bracket X = {ceiling!r} under "
        f"condition (a)'s rule (bounds {low!r} and {high!r}), so the pin's INCONCLUSIVE would be "
        "correct and there would be nothing to correct"
    )

    corrected_verdict, corrected_reasons, _corrected_arm = coverage.corrected_point_verdict(
        **_corrected_call(
            "FIXTURE_CLEARING_POINT",
            sweep_extraction_successes=DIRECTION_I_SUCCESSES,
            sweep_extraction_questions=QUESTIONS,
        )
    )
    assert corrected_verdict == "PASS", (
        f"the corrected route returns {corrected_verdict!r} where the frozen block returns "
        f"{pin_verdict!r}. A would-be PASS stays DEMOTED and promote_to_full_fidelity stays "
        f"withheld on a sweep that brackets X = {ceiling!r} under the (a) rule "
        f"({low!r} <= X < {high!r}) — which is CR-01's first direction, live. Reasons: "
        f"{corrected_reasons}"
    )
    assert not _names_gate06(corrected_reasons), (
        f"the corrected route still appends a GATE-06 truncation reason on a covered sweep: "
        f"{corrected_reasons}"
    )


def test_direction_ii_suppressed_inconclusive_is_red_on_the_pin_and_green_through_the_correction():
    """DIRECTION (ii): a truncated axis judged DECISIVELY, on FIXTURE_DESTROYED_MODEL.

    THE FIXTURE IS NAMED because the fixture is what decides the outcome. ``20-SECURITY.md`` and
    the verification report both describe this direction as "returns a decisive FAIL" without
    naming one, and only ``FIXTURE_DESTROYED_MODEL`` does; ``FIXTURE_CLEARING_POINT`` under the
    identical sweep returns PASS, which is asserted at the bottom of this body as the third case no
    report records.
    """
    sweep_rates = tuple(k / N for k in DIRECTION_II_SUCCESSES)
    pin_verdict, pin_reasons, _arm = mitigation_gate.mitigation_point_verdict(
        **_pin_call("FIXTURE_DESTROYED_MODEL", sweep_extraction_rates=sweep_rates)
    )
    assert pin_verdict == "FAIL", (
        f"the frozen pin returns {pin_verdict!r} on FIXTURE_DESTROYED_MODEL at the "
        f"{DIRECTION_II_SUCCESSES} / {QUESTIONS} sweep, not the FAIL this correction was written "
        "against"
    )
    assert not _names_gate06(pin_reasons), (
        "the pin's FAIL now carries a GATE-06 reason, so the axis is no longer being judged "
        f"decisively and direction (ii) is gone: {pin_reasons}"
    )

    # ZERO points clear X under condition (a)'s statistic — the honest reading is "we could not
    # tell", and the pin published "it did not work".
    ceiling = _ceiling_for("FIXTURE_DESTROYED_MODEL")
    bounds = tuple(coverage.wilson_upper_bound(k, N) for k in DIRECTION_II_SUCCESSES)
    assert all(bound > ceiling for bound in bounds), (
        f"at least one point in {DIRECTION_II_SUCCESSES} / {QUESTIONS} clears X = {ceiling!r} "
        f"under the (a) rule (bounds {bounds}), so the axis is not truncated and the pin's "
        "decisive FAIL would be legitimate"
    )

    corrected_verdict, corrected_reasons, _corrected_arm = coverage.corrected_point_verdict(
        **_corrected_call(
            "FIXTURE_DESTROYED_MODEL",
            sweep_extraction_successes=DIRECTION_II_SUCCESSES,
            sweep_extraction_questions=QUESTIONS,
        )
    )
    assert corrected_verdict == "INCONCLUSIVE", (
        f"the corrected route returns {corrected_verdict!r} on a sweep where ZERO points clear "
        f"X = {ceiling!r} (bounds {bounds}). A curve that never crossed cannot refute existence, "
        f"so collapsing it into {pin_verdict!r} publishes 'it did not work' where the evidence "
        f"only supports 'we could not tell'. Reasons: {corrected_reasons}"
    )
    assert "GATE-06" in corrected_reasons[-1], corrected_reasons[-1]
    assert coverage.SUPERSEDED_GATE06_BLOCK in corrected_reasons[-1], (
        "the corrected GATE-06 reason does not name the block it supersedes "
        f"({coverage.SUPERSEDED_GATE06_BLOCK!r}), so a reader meets a second GATE-06 verdict with "
        f"no way to tell which one governs: {corrected_reasons[-1]!r}"
    )

    # THE THIRD CASE, IN NO PRIOR REPORT: the same sweep on the CLEARING fixture is a pin PASS.
    third_pin, _third_reasons, _third_arm = mitigation_gate.mitigation_point_verdict(
        **_pin_call("FIXTURE_CLEARING_POINT", sweep_extraction_rates=sweep_rates)
    )
    third_corrected, _c_reasons, _c_arm = coverage.corrected_point_verdict(
        **_corrected_call(
            "FIXTURE_CLEARING_POINT",
            sweep_extraction_successes=DIRECTION_II_SUCCESSES,
            sweep_extraction_questions=QUESTIONS,
        )
    )
    clearing_ceiling = _ceiling_for("FIXTURE_CLEARING_POINT")
    assert (third_pin, third_corrected) == ("PASS", "INCONCLUSIVE"), (
        f"FIXTURE_CLEARING_POINT under the {DIRECTION_II_SUCCESSES} / {QUESTIONS} sweep reads "
        f"({third_pin!r}, {third_corrected!r}) rather than ('PASS', 'INCONCLUSIVE'). The pin "
        f"publishes a PASS off an extraction axis on which no swept point clears "
        f"X = {clearing_ceiling!r} under condition (a)'s own statistic. THE HONEST LIMIT, stated "
        "so this is not overstated: it does NOT contradict the verifier's narrower "
        "no-spurious-PASS claim, which was scoped to self-consistent inputs where the judged point "
        "is itself one of the swept points. Here it is not"
    )


def test_the_sanctioned_route_cannot_be_handed_raw_rates():
    """The interface half AND the value half. Neither substitutes for the other.

    Deleting ``sweep_extraction_rates`` removes the raw-rate PATH — the old call no longer
    type-checks. It does NOT remove the raw-rate VALUE: a caller porting the old call by RENAMING
    the keyword hands a rate to a count parameter, and at n=104 every fractional ``successes``
    yields a Wilson upper bound under X, so every point reads as clearing, the axis reads as
    truncated, and the route would return a spurious INCONCLUSIVE with nothing in the output to say
    why — conservative in direction, silent in operation. This is the tripwire
    ``20-VERIFICATION.md`` gap 1 item 3 asks for.
    """
    signature = inspect.signature(coverage.corrected_point_verdict)
    assert "sweep_extraction_rates" not in signature.parameters, (
        "`sweep_extraction_rates` is back on the sanctioned route's signature. Its ABSENCE BY "
        "CONSTRUCTION is what makes raw-rate space unreachable through this route"
    )
    assert len(signature.parameters) == 24, (
        f"the sanctioned route takes {len(signature.parameters)} parameters, not 24 — the frozen "
        "gate's 21 minus sweep_extraction_rates plus sweep_extraction_successes, "
        "sweep_extraction_questions, sweep_heldout_recalls and retention_floor_provenance"
    )
    for name, parameter in signature.parameters.items():
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
            f"{name} is {parameter.kind}, not KEYWORD_ONLY. GATE-01's discipline: a positional "
            "parameter is one a later caller can silently transpose with its neighbour"
        )
        assert parameter.default is inspect.Parameter.empty, (
            f"{name} acquired the default {parameter.default!r}. The pin pays 21 explicit "
            "arguments precisely so a caller cannot omit an anchor and still get a verdict"
        )

    # THE ARMED HALF: the direction-(ii) migration mistake, driven through the route.
    with pytest.raises(SystemExit) as migrated:
        coverage.corrected_point_verdict(
            **_corrected_call(
                "FIXTURE_DESTROYED_MODEL",
                sweep_extraction_successes=tuple(k / N for k in DIRECTION_II_SUCCESSES),
                sweep_extraction_questions=QUESTIONS,
            )
        )
    message = str(migrated.value)
    assert "RATE" in message and "COUNT" in message, (
        f"the refusal does not name the confusion it is refusing: {message!r}. A caller who "
        "renamed the keyword needs to be told that the UNIT changed, not merely that something "
        "was invalid"
    )

    for bad, label in (
        ((-1, 3), "a negative success count"),
        ((3, N + 1), "a success count above its denominator"),
    ):
        with pytest.raises(SystemExit):
            coverage.corrected_point_verdict(
                **_corrected_call(
                    "FIXTURE_DESTROYED_MODEL",
                    sweep_extraction_successes=bad,
                    sweep_extraction_questions=QUESTIONS,
                )
            )

    # THE POSITIVE CONTROL. A refusal test with no positive control cannot distinguish "the guard
    # fires" from "nothing works" — the integer form of the very same sweep must reach a verdict.
    verdict, _reasons, _arm = coverage.corrected_point_verdict(
        **_corrected_call(
            "FIXTURE_DESTROYED_MODEL",
            sweep_extraction_successes=DIRECTION_II_SUCCESSES,
            sweep_extraction_questions=QUESTIONS,
        )
    )
    assert verdict in ("PASS", "FAIL", "INCONCLUSIVE"), verdict


def test_the_superseded_sweep_sentinel_cannot_fire_the_frozen_gate06_branch():
    """What makes ``corrected_point_verdict``'s step 6 legitimate rather than lucky.

    The route neutralises the superseded block by handing ``SUPERSEDED_SWEEP_SENTINEL`` to both of
    the pin's sweep parameters. That is only sound if the sentinel provably brackets every
    criterion the block reads — asserted here on all three committed fixtures rather than assumed
    of the construction (T-20-50). If a sentinel could fire the frozen branch, the correction's own
    GATE-06 reason would be competing with a stale one from the block it supersedes.
    """
    for name in ("FIXTURE_CLEARING_POINT", "FIXTURE_DESTROYED_MODEL", "FIXTURE_TRUNCATED_SWEEP"):
        _verdict, reasons, _arm = mitigation_gate.mitigation_point_verdict(
            **_pin_call(
                name,
                sweep_extraction_rates=coverage.SUPERSEDED_SWEEP_SENTINEL,
                sweep_taught_recalls=coverage.SUPERSEDED_SWEEP_SENTINEL,
            )
        )
        assert not _names_gate06(reasons), (
            f"{name} under SUPERSEDED_SWEEP_SENTINEL "
            f"{coverage.SUPERSEDED_SWEEP_SENTINEL} still fires the frozen GATE-06 branch: "
            f"{[reasons[i] for i in _names_gate06(reasons)]}. The sentinel would then be masking "
            "nothing and the corrected route would publish two competing GATE-06 readings"
        )


def test_wilson_bounds_are_exact_mirrors():
    """The mirror, proved EXACTLY — and its ONE declared divergence proved general, not tuned.

    ``wilson_lower_bound`` diverges from the algebraic mirror at ``successes == 0``, deliberately
    and with the reason recorded in its own docstring: at ``p = 0`` the algebra gives
    ``centre == spread`` identically, so the analytic lower bound IS exactly ``0`` and it is the
    floating-point evaluation, not the clamp, that is wrong. That case is therefore asserted
    SEPARATELY below rather than folded into the mirror claim — asserting the mirror at zero
    successes would assert the defect.

    No ``math.isclose`` and no tolerance appears on any bracketing assertion. The one tolerance is
    on the symmetry-about-the-centre property, which is a claim about the shared construction and
    not a bracketing guarantee.
    """
    for k in range(0, N + 1):
        low = coverage.wilson_lower_bound(k, N)
        high = coverage.wilson_upper_bound(k, N)
        assert low <= k / N <= high, (
            f"the bounds at {k}/{N} do not bracket the point estimate: [{low!r}, {high!r}] "
            f"against {k / N!r}"
        )

    assert coverage.wilson_lower_bound(0, N) == 0.0
    assert coverage.wilson_upper_bound(N, N) == 1.0

    # THE SHORT-CIRCUIT IS NOT `n = 104` SPECIAL-CASING. This span contains the measured cancelling
    # denominators 11 (the smallest), 104 and 208 — where the naive mirror returns 1.11e-17,
    # 1.69e-18 and 8.56e-19 — and also 8, 16, 50 and 200, where it returns exactly 0.0 anyway. A
    # spot check at one convenient denominator would prove nothing.
    for n in range(2, 401):
        value = coverage.wilson_lower_bound(0, n)
        assert value == 0.0, (
            f"wilson_lower_bound(0, {n}) returned {value!r} rather than exactly 0.0. At zero "
            "successes Wilson's lower bound is analytically 0 (centre == spread identically at "
            "p = 0), so a nonzero return is the sqrt round-trip residue leaking through — and "
            "max(0.0, ...) cannot absorb it because the residue is POSITIVE"
        )

    # SYMMETRY ABOUT THE SHARED WILSON CENTRE, at the same z. The centre only — no spread, no
    # sqrt — so this is a property check of the shared construction rather than a second copy of
    # either bound (T-20-53). This is the ONE place a tolerance belongs.
    z = erasure_gate._Z_ONE_SIDED_95
    for k in range(1, N + 1):
        denom = 1.0 + z * z / N
        centre = (k / N + z * z / (2 * N)) / denom
        midpoint = (coverage.wilson_lower_bound(k, N) + coverage.wilson_upper_bound(k, N)) / 2
        assert math.isclose(midpoint, centre, rel_tol=0.0, abs_tol=1e-12), (
            f"the two bounds at {k}/{N} are not symmetric about the Wilson centre {centre!r}: "
            f"midpoint {midpoint!r}. They have drifted to different z or different denominators"
        )

    # IDENTITY, PROVED PER OBJECT BY THE MECHANISM THAT CAN ACTUALLY FAIL FOR ITS TYPE.
    assert (
        coverage.wilson_upper_bound
        is erasure_gate.wilson_upper_bound
        is mitigation_gate.wilson_upper_bound
    ), "a second copy of the upper bound exists — two estimators, free to stop matching"
    assert coverage.F_Y is mitigation_gate.F_Y, (
        "F_Y is no longer the pin's own object. It is the float 0.7 and a retyped literal is NOT "
        "`is`-identical to it (measured), so this check bites"
    )

    # MARGIN_K and EXTRACTION_FLOOR_MIN_SEEDS are both the small int 2, which CPython INTERNS — a
    # retyped literal passes an `is` check identically (measured), so an `is` assertion on them
    # could not fail and would not be a guard. What T-20-53 actually claims for them is that they
    # are IMPORTED and never assigned, so that is what gets asserted, structurally.
    tree = ast.parse((_SCRIPTS / "phase20_gate_coverage.py").read_text(encoding="utf-8"))
    imported = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assigned = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    for name in ("MARGIN_K", "EXTRACTION_FLOOR_MIN_SEEDS"):
        assert name in imported, (
            f"{name} is not in scripts/phase20_gate_coverage.py's import alias set {imported}. It "
            "must be REUSED from the module that defines it, not restated"
        )
        assert name not in assigned, (
            f"{name} is assigned at module scope in scripts/phase20_gate_coverage.py — a second "
            "copy of a protocol requirement, which is exactly what T-20-53 forbids"
        )
