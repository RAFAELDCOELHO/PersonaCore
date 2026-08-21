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
import json
import math
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import _addendum  # noqa: E402  (needs the sys.path insert above)
import erasure_gate  # noqa: E402  (same reason)
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


def _git(*args):
    done = subprocess.run(("git", *args), cwd=_ROOT, capture_output=True, check=True)
    return done.stdout.decode("utf-8")


def _payload():
    return json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))


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


def test_a_recall_outside_the_unit_interval_cannot_manufacture_y_coverage():
    """The Y legs' value discipline, as a MEASURED DIFFERENTIAL asserted at the route level.

    This is the tripwire ``20-VERIFICATION.md`` gap 1 item 2 asks for, and it is driven through
    ``corrected_point_verdict`` rather than against ``coverage_verdict`` in isolation because that
    is where the INCONCLUSIVE→PASS flip lives and where a regression is user-visible.

    Both halves live in ONE body, the register the two direction tests above use. The HONEST
    truncated axis reaches a finding; the STRICTLY MORE truncated axis — the same leg with one
    point replaced by a NaN — is REFUSED, where before the guard it was PROMOTED to PASS. Splitting
    a differential across two functions lets one half go stale without the other noticing.

    The fixture's own ``sweep_taught_recalls = (0.45, 0.2)`` legitimately brackets
    ``y_taught = 0.35``, so the held-out leg is the only axis under test in cases 1-3.
    """
    fixture = mitigation_gate.FIXTURE_CLEARING_POINT
    y_heldout = coverage.F_Y * fixture["control_heldout_recall"]

    def route(**overrides):
        return coverage.corrected_point_verdict(
            **_corrected_call(
                "FIXTURE_CLEARING_POINT",
                sweep_extraction_successes=DIRECTION_I_SUCCESSES,
                sweep_extraction_questions=QUESTIONS,
                **overrides,
            )
        )

    # 1. THE HONEST READING. Both points sit at or above Y_heldout, so the axis produced ZERO
    #    failing points and genuinely never crossed. That is a finding, and the guard below must
    #    leave it exactly where it was.
    honest = (0.30, 0.28)
    assert all(point >= y_heldout for point in honest), (
        f"{honest} does not sit entirely at or above Y_heldout = {y_heldout!r}, so this axis is "
        "not truncated and case 1 is measuring something other than the honest reading"
    )
    verdict, reasons, _arm = route(sweep_heldout_recalls=honest)
    named = _names_gate06(reasons)
    assert verdict == "INCONCLUSIVE" and named, (
        f"the honest truncated held-out sweep {honest} against Y_heldout = {y_heldout!r} returns "
        f"{verdict!r} with GATE-06 reasons at {named}, not the INCONCLUSIVE carrying one. The "
        f"per-element range guard must not have moved the honest finding. Reasons: {reasons}"
    )
    assert "heldout_recall" in reasons[named[-1]], (
        f"the GATE-06 reason does not name the heldout_recall axis: {reasons[named[-1]]!r}. Then "
        "the demotion is coming from some other leg and this case proves nothing about WR-09's"
    )

    # 2. THE MECHANISM, ASSERTED RATHER THAN NARRATED. This is why the NaN manufactured the
    #    bracket — it was COUNTED as a failing point, not merely passed through — and it is a
    #    property of the comparison, so it stays true after the guard lands.
    assert not (float("nan") >= y_heldout), (
        f"nan >= {y_heldout!r} is no longer False, so a NaN is no longer counted as a FAILING "
        "point and the manufacturing mechanism this test exists to refuse has changed shape"
    )

    # 3. THE FLIP, REFUSED. The SAME axis, STRICTLY MORE truncated than case 1.
    with pytest.raises(SystemExit) as refused:
        route(sweep_heldout_recalls=(float("nan"), 0.28))
    message = str(refused.value)
    assert "held-out" in message and "[0.0, 1.0]" in message, (
        f"the refusal does not name the leg and its [0.0, 1.0] requirement: {message!r}. MEASURED "
        f"BEFORE THIS GUARD, on this fixture at the {DIRECTION_I_SUCCESSES} / {QUESTIONS} sweep: "
        "(nan, 0.28) returned 'PASS' with NO GATE-06 reason at all and coverage_verdict reported "
        f"(True, ()) — FULLY COVERED — while the strictly LESS truncated {honest} returned "
        "'INCONCLUSIVE'. A guard that raises for some other reason does not close that flip"
    )

    # 4. THE WHOLE OUT-OF-RANGE CLASS, ON BOTH LEGS. The review's original demonstration invites
    #    "that is garbage in, garbage out"; case 3 is what makes the claim a differential, and
    #    these two are what make it cover the class rather than one value.
    for label, override in (
        ("the held-out leg", {"sweep_heldout_recalls": (42.0, -99.0)}),
        ("the taught leg", {"sweep_taught_recalls": (-99.0, 42.0)}),
    ):
        with pytest.raises(SystemExit) as out_of_range:
            route(**override)
        assert "[0.0, 1.0]" in str(out_of_range.value), (
            f"{label} accepted {override} without naming the [0.0, 1.0] requirement: "
            f"{str(out_of_range.value)!r}. 42.0 and -99.0 straddle any floor in (0.0, 1.0], so any "
            "garbage pair would certify coverage on an axis nothing was ever measured on"
        )

    # THE POSITIVE CONTROL, in the register test_the_sanctioned_route_cannot_be_handed_raw_rates
    # uses at :365. An in-range held-out sweep that GENUINELY brackets still reaches a verdict, so
    # the four aborts above are attributable to this guard and not to anything else in the route.
    assert DEFAULT_HELDOUT_SWEEP[0] >= y_heldout > DEFAULT_HELDOUT_SWEEP[1], (
        f"{DEFAULT_HELDOUT_SWEEP} does not bracket Y_heldout = {y_heldout!r}, so the control is "
        "not a covered axis and cannot distinguish 'the guard fires' from 'nothing works'"
    )
    control, _control_reasons, _control_arm = route(sweep_heldout_recalls=DEFAULT_HELDOUT_SWEEP)
    assert control in ("PASS", "FAIL", "INCONCLUSIVE"), control


def test_the_modules_own_rate_space_sentinel_cannot_pass_as_counts():
    """GC-04: the RATE-vs-COUNT guard enforced BY TYPE, driven with this module's own constant.

    ``SUPERSEDED_SWEEP_SENTINEL`` is READ from the module and never retyped, so a later change to
    that constant travels into this guard rather than leaving it asserting a stale pair. The old
    ``isinstance(k, float) and k.is_integer()`` acceptance admitted it: a rate-space constant
    defined in the very file whose docstring claims raw-rate space is unreachable through this
    route.
    """

    def route(**overrides):
        return coverage.corrected_point_verdict(
            **_corrected_call(
                "FIXTURE_CLEARING_POINT",
                sweep_extraction_questions=QUESTIONS,
                **overrides,
            )
        )

    for successes, label in (
        (coverage.SUPERSEDED_SWEEP_SENTINEL, "this module's own rate-space sentinel"),
        ((True, False), "a pair of bools"),
    ):
        with pytest.raises(SystemExit) as refused:
            route(sweep_extraction_successes=successes)
        message = str(refused.value)
        assert "RATE" in message and "COUNT" in message, (
            f"{label} {successes!r} passes as a COUNT of successes without the caller being told "
            f"the UNIT is wrong: {message!r}. MEASURED before the guard was enforced by type: "
            f"{coverage.SUPERSEDED_SWEEP_SENTINEL} was read as 0 and 1 successes out of {N} "
            "questions, both clearing X, the extraction axis reading truncated, and the route "
            "returning a spurious INCONCLUSIVE — a DEMOTION, conservative in direction and silent "
            "in operation, which is exactly what this guard's own message says it exists to "
            "prevent. `isinstance(True, int)` is True, so the bool pair was admitted for the same "
            "reason. Bools stay legitimate on the two RECALL legs, where they are 1.0 and 0.0"
        )

    # THE POSITIVE CONTROL. Genuine integer counts on the same fixture and the same denominators
    # still reach a verdict, so the two aborts above are attributable to the type enforcement.
    verdict, _reasons, _arm = route(sweep_extraction_successes=DIRECTION_I_SUCCESSES)
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


def test_correction_addendum_is_additive_on_the_published_artifact():
    """The continuation was ADDED beside the published verdict, never written over it.

    ``tests/test_phase20_prereg.py`` and ``tests/test_phase19_docs.py`` prove
    ``scripts/_addendum.py`` appends — at a synthetic tmp location, against bytes the test itself
    wrote. This proves what that writer actually DID to the published artifact, which is a
    different claim: a writer can be append-only and still have been run against a file some other
    hand had already rewritten. Every assertion below therefore runs on the COMMITTED BYTES.

    The pre-append revision is DERIVED from history rather than pinned to a hash, and it is derived
    from ``git log`` rather than ``git ls-files``. MEASURED: ``ls-files`` prints the path for a file
    that is staged and never committed, so it cannot distinguish a committed revision from an index
    entry — precisely the state the two-commit rule forbids.
    """
    assert CORRECTION_PATH.exists(), f"{CORRECTION_REL} is missing — plan 20-10 committed it"
    assert _git("rev-parse", "--is-shallow-repository").strip() == "false", (
        "shallow clone: the pre-append revision is not in the object store, so this guard cannot "
        "distinguish 'the append was additive' from 'the history was never read'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )

    # The newest committed revision still carrying the placeholder is BY DEFINITION the one before
    # the append, and that stays true however many later commits touch the file.
    before = None
    for revision in _git("log", "--format=%H", "--", CORRECTION_REL).split():  # newest first
        blob = _git("show", f"{revision}:{CORRECTION_REL}")
        if PENDING in blob:
            before = blob
            break
    assert before is not None, (
        f"no committed revision of {CORRECTION_REL} carries {PENDING!r}, so there is no "
        "pre-append state to compare against. Either the placeholder never existed (the file is "
        "not this writer's output, i.e. the two-commit rule was not followed) or the history was "
        "rewritten"
    )
    after = CORRECTION_PATH.read_text(encoding="utf-8")

    cut = before.index(PENDING)
    assert after[:cut] == before[:cut], (
        f"the published {CORRECTION_REL} no longer starts with its pre-append bytes. Everything "
        "above the placeholder is the FROZEN PIN's own literal reading — all four verdicts with "
        "the fixture named — and an append may not touch any of it"
    )

    before_lines, after_lines = before.splitlines(), after.splitlines()
    changed = [(old, new) for old, new in zip(before_lines, after_lines) if old != new]
    assert changed == [(PENDING, RECORDED)], (
        "exactly one published line may differ, and it is the placeholder becoming a pointer at "
        f"the appended section: {changed}"
    )
    assert after_lines[: len(before_lines)] == [
        RECORDED if line == PENDING else line for line in before_lines
    ], "a published line was moved, deleted or reordered rather than left in place"
    assert len(after_lines) > len(before_lines), "nothing was appended"
    assert ADDENDUM_HEADING in "\n".join(after_lines[len(before_lines) :]), (
        f"{ADDENDUM_HEADING!r} is not in the appended region, so the section was spliced into the "
        "body rather than added after it. NOTE the date: the continuation is dated 2026-08-21, "
        "the day it was written and its numbers re-derived, not the 2026-08-20 its plan hardcoded"
    )

    recorded_after = _addendum._verdict.recorded_verdict(after)
    assert recorded_after == _addendum._verdict.recorded_verdict(before), (
        "the recorded `## Verdict` section changed across the append. It is the section the "
        "clobber guards anchor on and the one thing a continuation exists to sit BESIDE"
    )
    assert recorded_after is not None, (
        f"{CORRECTION_REL} has no `## Verdict` section at all, so the equality above compared "
        "None with None and `append_addendum`'s own unchanged-verdict guard was vacuous on this "
        "file — it would have permitted any rewrite whatsoever of a document with no such heading"
    )

    # STAT-02 as the LINE-SCOPED rule 20-10 wrote this artifact against: a line carrying a `%`
    # figure must carry an explicit k/n denominator on that same line. A percentage with its
    # denominator on some other line is a percentage a reader meets without one.
    for number, line in enumerate(after_lines, start=1):
        if re.search(r"\d\s*%", line) and not re.search(r"\d\s*/\s*\d", line):
            raise AssertionError(
                f"{CORRECTION_REL}:{number} publishes a percentage with no k/n denominator on the "
                f"same line: {line!r}"
            )


def test_every_published_number_re_derives_from_the_modules():
    """Every float in the correction JSON, obtained by CALLING the modules. A hand edit goes red.

    The artifact was generated by a throwaway script that imported the three modules and called
    them; the script is not committed, so the discipline it enforced has no standing enforcement
    until this test exists (T-20-51). Nothing below is typed as a literal.

    ONE published field is deliberately NOT re-derived: ``zero_successes_short_circuit
    .measured_residue_at_n_104``. Re-deriving it would require writing out the naive mirror's
    ``centre - spread`` in this file, i.e. a second copy of exactly the estimator the module
    short-circuits — the T-20-53 defect, introduced by the test that exists to prevent it. The
    short-circuit's OUTPUT is asserted instead, which is the part any decision could read.
    """
    payload = _payload()
    evidence = payload["evidence"]
    fixture = mitigation_gate.FIXTURE_CLEARING_POINT

    assert evidence["n"] == fixture["control_extraction_questions"]
    assert evidence["X"] == _ceiling_for("FIXTURE_CLEARING_POINT"), (
        f"the payload publishes X = {evidence['X']!r} but extraction_ceiling on the fixture's own "
        f"arguments returns {_ceiling_for('FIXTURE_CLEARING_POINT')!r}"
    )
    assert evidence["y_taught"] == coverage.F_Y * fixture["control_taught_recall"]
    assert evidence["y_heldout"] == coverage.F_Y * fixture["control_heldout_recall"]

    ceiling = evidence["X"]
    for point in evidence["swept_points"]:
        k, n = point["successes"], point["questions"]
        upper = coverage.wilson_upper_bound(k, n)
        assert point["wilson_upper_bound"] == upper, (point, upper)
        assert point["raw_rate"] == k / n, (point, k / n)
        assert point["clears_under_condition_a"] == (upper <= ceiling), point
        assert point["clears_under_the_frozen_block"] == (k / n <= ceiling), point

    # BOTH verdicts per direction, re-measured through the pin and through the route. The fixture
    # is read OUT of the payload rather than assumed, so a payload that renamed its fixture is
    # measured against the fixture it actually names.
    for key, successes in (
        ("direction_i", DIRECTION_I_SUCCESSES),
        ("direction_ii", DIRECTION_II_SUCCESSES),
        ("direction_ii_on_clearing_fixture", DIRECTION_II_SUCCESSES),
    ):
        entry = evidence[key]
        name = entry["fixture"]
        assert tuple(entry["successes"]) == successes, (key, entry["successes"])
        questions = tuple(entry["questions"])
        assert tuple(entry["raw_rates"]) == tuple(k / n for k, n in zip(successes, questions)), (
            entry
        )
        assert tuple(entry["wilson_upper"]) == tuple(
            coverage.wilson_upper_bound(k, n) for k, n in zip(successes, questions)
        ), entry

        pin_verdict, _pin_reasons, _pin_arm = mitigation_gate.mitigation_point_verdict(
            **_pin_call(name, sweep_extraction_rates=tuple(entry["raw_rates"]))
        )
        assert entry["pin_verdict"] == pin_verdict, (
            f"{key}: the payload publishes pin_verdict {entry['pin_verdict']!r} but the frozen pin "
            f"on {name} returns {pin_verdict!r}"
        )
        corrected, _reasons, _arm = coverage.corrected_point_verdict(
            **_corrected_call(
                name,
                sweep_extraction_successes=successes,
                sweep_extraction_questions=questions,
            )
        )
        assert entry["corrected_verdict"] == corrected, (
            f"{key}: the payload publishes corrected_verdict {entry['corrected_verdict']!r} but "
            f"the sanctioned route on {name} returns {corrected!r}"
        )

    # The retention leg's whole evidentiary record — two floors, two caps, the ratio.
    retention = payload["retention_provenance"]
    measured_floor = json.loads(RETENTION_FLOOR_PATH.read_text(encoding="utf-8"))[
        "retention_ppl_noise_floor"
    ]
    assert retention["measured_floor"] == measured_floor
    assert retention["borrowed_floor"] == erasure_gate.V20_RETENTION_NOISE_FLOOR
    assert retention["borrowed_cap"] == mitigation_gate.retention_cap(
        retention_noise_floor=erasure_gate.V20_RETENTION_NOISE_FLOOR
    )
    assert retention["governing_cap"] == mitigation_gate.retention_cap(
        retention_noise_floor=measured_floor
    )
    assert retention["ratio"] == erasure_gate.V20_RETENTION_NOISE_FLOOR / measured_floor
    assert retention["borrowed_floor_is_looser"] is (
        retention["governing_cap"] < retention["borrowed_cap"]
    )

    # The REPORTED lower bounds — priced at the nearest whole count at n = 104, because the fixture
    # Y points are fabricated RATES carrying no count. The count is published beside each bound and
    # is re-derived here rather than taken on trust.
    for entries in payload["bound_direction"]["reported_lower_bounds"].values():
        for entry in entries:
            k, n = entry["successes_priced_at_n_104"], entry["questions"]
            assert k == round(entry["fixture_rate"] * n), entry
            assert entry["wilson_lower_bound"] == coverage.wilson_lower_bound(k, n), entry
            assert entry["wilson_upper_bound"] == coverage.wilson_upper_bound(k, n), entry
    short_circuit = payload["bound_direction"]["zero_successes_short_circuit"]
    assert short_circuit["wilson_lower_bound_at_zero"] == coverage.wilson_lower_bound(0, N)

    # The module data the artifact serialises rather than restates.
    assert payload["supersedes"] == coverage.SUPERSEDED_GATE06_BLOCK
    assert tuple(payload["superseded_sweep_sentinel"]) == coverage.SUPERSEDED_SWEEP_SENTINEL
    assert (
        tuple(
            (entry["axis"], entry["statistic"], entry["criterion_site"])
            for entry in payload["coverage_statistic_by_axis"]
        )
        == coverage.COVERAGE_STATISTIC_BY_AXIS
    )

    # WR-09's held-out leg: the ONE published case that overrides the default sweep, and the case
    # the frozen 21-keyword signature has no parameter to reach at all.
    heldout = payload["heldout_coverage"]
    assert heldout["pin_has_the_parameter"] is (
        "sweep_heldout_recalls"
        in inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    )
    verdict, reasons, _arm = coverage.corrected_point_verdict(
        **_corrected_call(
            "FIXTURE_CLEARING_POINT",
            sweep_extraction_successes=DIRECTION_I_SUCCESSES,
            sweep_extraction_questions=QUESTIONS,
            sweep_heldout_recalls=tuple(heldout["sweep_heldout_recalls"]),
        )
    )
    assert heldout["corrected_route_verdict"] == verdict
    assert heldout["y_heldout"] == coverage.F_Y * fixture["control_heldout_recall"]
    assert heldout["sentence"] in reasons[-1], (
        f"the payload's held-out truncation sentence is not the one the route produces: "
        f"{heldout['sentence']!r} against {reasons[-1]!r}"
    )


def test_the_three_defects_are_still_live_in_the_frozen_pin():
    """Each defect asserted against the CODE, never against the prose that describes it.

    A description that outlives its defect is worse than no description: it teaches a reader to
    distrust an artifact that is now correct (T-20-57). If any assertion here goes green, the
    continuation needs RE-READING, not deleting — and the pin is frozen, so a defect going away is
    itself evidence that something moved that should not have.
    """
    payload = _payload()

    # CR-01 — the coverage statistic. The pin still demotes a would-be PASS on direction (i).
    pin_verdict, _reasons, _arm = mitigation_gate.mitigation_point_verdict(
        **_pin_call(
            "FIXTURE_CLEARING_POINT",
            sweep_extraction_rates=tuple(k / N for k in DIRECTION_I_SUCCESSES),
        )
    )
    assert pin_verdict == "INCONCLUSIVE", (
        f"CR-01 is GONE: the frozen pin now returns {pin_verdict!r} on direction (i). "
        f"{CORRECTION_REL} needs re-reading rather than deleting — and since the pin cannot be "
        "edited, a change in its behaviour means something else moved"
    )

    # WR-09 — the held-out leg has no parameter at all in the frozen 21-keyword signature.
    parameters = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    assert "sweep_heldout_recalls" not in parameters, (
        "WR-09 is GONE: mitigation_point_verdict now carries a sweep_heldout_recalls parameter, so "
        "the held-out leg of the pair-valued Y is no longer uncoverable by the frozen gate. The "
        f"continuation says it is; {CORRECTION_REL} needs re-reading rather than deleting"
    )
    assert len(parameters) == 21, len(parameters)

    # T-20-19 — retention_cap accepts the Phase 12 full-fine-tune floor with NO refusal at all,
    # and returns the LOOSER cap. Asserted against the artifact's own published value rather than
    # against a retyped literal.
    borrowed_cap = mitigation_gate.retention_cap(
        retention_noise_floor=erasure_gate.V20_RETENTION_NOISE_FLOOR
    )
    assert borrowed_cap == payload["retention_provenance"]["borrowed_cap"], (
        f"T-20-19 has MOVED: retention_cap on the borrowed floor now returns {borrowed_cap!r} "
        f"against the published {payload['retention_provenance']['borrowed_cap']!r}"
    )
    assert borrowed_cap > payload["retention_provenance"]["governing_cap"], (
        "T-20-19 is GONE: the borrowed floor no longer buys the looser cap, so the substitution is "
        f"no longer the one an unguarded borrowing profits from. {CORRECTION_REL} needs re-reading"
    )


def test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict():
    """T-20-19 as a REACHABILITY claim — the twin of ``tests/test_phase20_prereg.py:1297-1330``.

    Every case is driven THROUGH ``corrected_point_verdict``, never against
    ``_prove_retention_floor`` in isolation. The claim being proved is that no path to a v4.0
    verdict skips the check; a test calling the helper directly would prove the check exists, which
    is a different and much weaker claim. ``extraction_ceiling``'s three ``_prove`` calls are
    unavoidable for exactly this structural reason — ``mitigation_point_verdict`` CALLS it — and
    the retention leg gets the same shape rather than a promise.

    The last case is not a provenance case at all. It is WR-08, asserted at BOTH magnitudes,
    because a guard's POSITION is part of the guard.
    """
    measured_floor = json.loads(RETENTION_FLOOR_PATH.read_text(encoding="utf-8"))[
        "retention_ppl_noise_floor"
    ]

    def refused(**overrides):
        with pytest.raises(SystemExit) as raised:
            coverage.corrected_point_verdict(
                **_corrected_call(
                    "FIXTURE_CLEARING_POINT",
                    sweep_extraction_successes=DIRECTION_I_SUCCESSES,
                    sweep_extraction_questions=QUESTIONS,
                    **overrides,
                )
            )
        return str(raised.value)

    # The four provenance refusals, each mirroring one of `extraction_ceiling`'s at :417/:425/:436
    # — except the fourth, which has no counterpart on the extraction leg.
    refused(retention_floor_provenance={})
    refused(retention_floor_provenance={"seeds": (1337, 2024)})
    refused(retention_floor_provenance={"regime": "full-finetune", "seeds": (1337, 2024)})
    for seeds in ((1337,), (1337, 1337)):
        message = refused(retention_floor_provenance={"regime": "adapter", "seeds": seeds})
        assert "1 distinct" in message, (
            f"the single-seed refusal does not report the count it counted: {message!r}. A "
            "single-seed floor is not a noise floor, it is ONE DRAW — there is no second reading "
            "for it to vary against — and the refusal has to say so with its number"
        )

    # THE BORROWED VALUE, refused BY IDENTITY even under an otherwise clean adapter provenance, so
    # a caller who states the right regime and the right seeds while passing the Phase 12
    # full-fine-tune number is still caught — by the number itself.
    borrowed = refused(retention_noise_floor=erasure_gate.V20_RETENTION_NOISE_FLOOR)
    published = (
        erasure_gate.V20_RETENTION_NOISE_FLOOR / measured_floor,
        mitigation_gate.retention_cap(retention_noise_floor=erasure_gate.V20_RETENTION_NOISE_FLOOR),
        mitigation_gate.retention_cap(retention_noise_floor=measured_floor),
    )
    for number in published:
        assert repr(number) in borrowed, (
            f"the borrowed-floor refusal does not publish {number!r}: {borrowed!r}. The ratio, the "
            "looser cap it buys and the governing cap it displaces are what make the refusal an "
            "argument rather than an assertion — and all three are DERIVED here through the frozen "
            "retention_cap, never retyped"
        )

    # WR-08 — THE SIGN CHECK, PROVED AT THE MAGNITUDE WHERE ITS ORDERING MATTERS. MEASURED: a floor
    # of -0.01 still yields a POSITIVE ceiling (0.005355228664941234), so a sign check placed AFTER
    # the ceiling computation fires with the right message and -0.01 alone proves nothing about
    # position. -0.05 drives the ceiling to -0.07464477133505877, where the `0.0 < ceiling < 1.0`
    # refusal would pre-empt it and the caller would be told the ceiling is out of range rather
    # than that their floor is negative. Both magnitudes, and asserted on the MESSAGE.
    for magnitude in (-0.01, -0.05):
        message = refused(extraction_noise_floor=magnitude)
        assert "NEGATIVE" in message and "extraction_noise_floor" in message, (
            f"the refusal at extraction_noise_floor={magnitude} does not name the floor's SIGN: "
            f"{message!r}"
        )
        assert "the extraction ceiling came out" not in message, (
            f"at extraction_noise_floor={magnitude} the caller is told the CEILING is out of "
            f"range rather than that their FLOOR is negative: {message!r}. The sign check has "
            "moved below the ceiling computation it protects, and the misattribution it exists to "
            "prevent is back"
        )

    # THE POSITIVE CONTROL. A fixture differing from the eight above in ONLY the refused field
    # still reaches a verdict, which is what makes those aborts attributable to the tripwire rather
    # than to anything else in the route.
    verdict, _reasons, _arm = coverage.corrected_point_verdict(
        **_corrected_call(
            "FIXTURE_CLEARING_POINT",
            sweep_extraction_successes=DIRECTION_I_SUCCESSES,
            sweep_extraction_questions=QUESTIONS,
        )
    )
    assert verdict == "PASS", verdict


def test_v4_retention_cap_reads_the_measured_adapter_regime_floor():
    """WR-02: ``results/phase20_retention_floor.json`` was read by NOTHING in ``tests/``.

    An artifact no test reads is an artifact whose arithmetic can silently rot. CI can never
    RE-MEASURE this one — ``checkpoints/`` and ``data/`` are gitignored (R-20-04), so the two
    perplexity readings are unreproducible here — which makes the artifact's own INTERNAL
    consistency the only check available. It is taken, on both sides.
    """
    artifact = json.loads(RETENTION_FLOOR_PATH.read_text(encoding="utf-8"))
    floor = artifact["retention_ppl_noise_floor"]

    assert floor != erasure_gate.V20_RETENTION_NOISE_FLOOR, (
        f"the measured adapter-regime floor is now {floor!r}, the Phase 12 FULL-FINE-TUNE seed "
        "pair. The borrowed value is back in the artifact the v4.0 cap is read from — which is "
        "T-20-19 realized at its source rather than at a call site"
    )
    assert mitigation_gate.retention_cap(retention_noise_floor=floor) == artifact["cap"], (
        f"the artifact publishes cap {artifact['cap']!r} but retention_cap on its own published "
        f"floor returns {mitigation_gate.retention_cap(retention_noise_floor=floor)!r}. A "
        "hand-edited number goes red here"
    )
    assert artifact["borrowed_cap"] == mitigation_gate.retention_cap(
        retention_noise_floor=erasure_gate.V20_RETENTION_NOISE_FLOOR
    )
    assert artifact["cap"] < artifact["borrowed_cap"], (
        f"the re-measured cap {artifact['cap']!r} is not TIGHTER than the borrowed "
        f"{artifact['borrowed_cap']!r}. D-06's whole claim is that the re-measurement does not buy "
        "an easier pass, and that claim is asserted here rather than narrated"
    )
    assert artifact["borrowed_floor_ratio"] == (erasure_gate.V20_RETENTION_NOISE_FLOOR / floor), (
        artifact["borrowed_floor_ratio"]
    )

    # THE ARTIFACT'S INTERNAL CONSISTENCY: the floor IS the spread between the two seeds' own
    # published readings. Bit-exact — the two deltas are committed, so there is no reason to allow
    # a tolerance over a subtraction of two committed doubles.
    deltas = [
        artifact["retention_ppl"][str(seed)]["delta_on_minus_off"] for seed in artifact["seeds"]
    ]
    assert len(deltas) == 2, deltas
    assert floor == abs(deltas[0] - deltas[1]), (
        f"the published floor {floor!r} is not the spread between the two seeds' published "
        f"delta_on_minus_off readings {deltas} (which differ by {abs(deltas[0] - deltas[1])!r}). "
        "checkpoints/ and data/ are gitignored, so this is the ONLY re-derivation CI can perform "
        "on this number, and it is the one that catches a hand edit"
    )
    for seed in artifact["seeds"]:
        entry = artifact["retention_ppl"][str(seed)]
        assert entry["delta_on_minus_off"] == entry["adapter_on"] - entry["adapter_off"], entry


def test_mitigation_point_verdict_has_no_caller_outside_this_module():
    """The census that ENFORCES the choke point — the name ``phase20_gate_coverage.py`` cites.

    ``corrected_point_verdict`` has no authority a Phase 23/25 caller cannot simply not invoke:
    nothing in Python stops a module importing ``mitigation_gate.mitigation_point_verdict`` and
    bypassing every correction in that file (T-20-48). What stops it is this walk, which goes RED
    on the first such caller.

    MATCHED ON BOTH ``.id`` AND ``.attr``. ``tests/test_phase19_erasure.py:1389`` matches on
    ``getattr(node.func, "id", None)`` alone, which is invisible to
    ``mitigation_gate.mitigation_point_verdict(...)`` — an ``ast.Attribute`` node, and exactly the
    form a Phase 23 driver would write. That is WR-07's latent hole and it is not copied here.

    ``tests/`` IS DELIBERATELY EXCLUDED, and the reason is recorded rather than assumed: the prereg
    suite drives the pin's own branches directly, which is the behavioural twin of the pin and not
    a bypass of the correction. The pin's own definition file is excluded for the same
    exclude-the-successor reason ``tests/test_phase19_erasure.py`` states — by NAME, never by
    lowering a count.
    """
    definition = _SCRIPTS / "mitigation_gate.py"
    sanctioned = _SCRIPTS / "phase20_gate_coverage.py"

    bypassing = []
    inside_sanctioned = 0
    for path in sorted(_SCRIPTS.rglob("*.py")) + sorted((_ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if called != "mitigation_point_verdict":
                continue
            if path == sanctioned:
                inside_sanctioned += 1
            elif path != definition:
                bypassing.append(f"{path.relative_to(_ROOT)}:{node.lineno}")

    assert bypassing == [], (
        f"{len(bypassing)} call site(s) reach a v4.0 verdict through the frozen pin directly, "
        f"bypassing scripts/phase20_gate_coverage.py::corrected_point_verdict: {bypassing}. Such a "
        "caller gets RAW-RATE coverage on the extraction axis (the CR-01 defect, which mislabels "
        "in both directions), NO coverage at all on the held-out leg (WR-09 — the frozen "
        "21-keyword signature has no sweep_heldout_recalls parameter), and NO retention "
        f"provenance check whatsoever (T-20-19). See {PAYLOAD_REL}, whose `governs` field names "
        "corrected_point_verdict as the governing route: a verdict read through "
        "mitigation_point_verdict directly is read through the superseded block and does not govern"
    )

    # NON-VACUITY, as a RECORDED STATE rather than a silent pass — `tests/test_phase16_prereg.py`'s
    # `bool(checked) == bool(tracked)` register. A census that returns empty because its matcher is
    # broken proves nothing, so the matcher is proved to fire where a call certainly exists.
    assert inside_sanctioned >= 1, (
        "the census found ZERO calls to mitigation_point_verdict inside "
        "scripts/phase20_gate_coverage.py, which calls it exactly once at step 6 of "
        "corrected_point_verdict. The matcher is broken or the sanctioned route stopped calling "
        "the pin — either way the empty result above proves nothing"
    )
