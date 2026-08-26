"""PHASE 23'S BLIND RULES, DRIVEN — both D-04 branches, the seed rule's boundaries, the refusals.

``scripts/phase23_prereg.py`` states what the σ=0 diagnostic will decide, how D-03's floor is
reduced, how many seeds it is reduced over, and when the n=64 leg is withdrawn. A rule nobody has
watched fire is a rule nobody has verified, so every branch below is EXECUTED rather than described
— including the HALT, which has a permanent watched-RED control so its failure is observable on
every suite run rather than once by hand.

**THE BOUND IS IMPORTED, NEVER RETYPED.** Every ``choose_n_seeds`` boundary case is computed FROM
``H_PER_POINT_FLOOR_SECONDS``. A retyped bound is a bound free to disagree with the one the rule
enforces, and the disagreement would be invisible — both numbers would look right.

CPU-only, GPU-free, no torch, no network.
"""

import math
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from phase23_prereg import (  # noqa: E402  (needs the sys.path insert above)
    CONTROL_FLOOR_RECORD,
    FLOOR_PROVENANCE_KEYS,
    H_PER_POINT_FLOOR_SECONDS,
    SIGMA_ZERO_RECORD,
    choose_n_seeds,
    n64_leg_is_committable,
    noise_floor,
    sigma_zero_verdict,
)

# SYNTHETIC THROUGHOUT, and labelled so: no Phase-23 arm exists — this module is committed while
# `git ls-files 'results/phase23_*'` is still empty, which is the whole point of it landing in wave
# 1. These are CONSTRUCTED INPUTS chosen to exercise a branch, never a measurement.
_CONTROL_READINGS = (0.40, 0.44, 0.42)

_FLOOR_PROVENANCE = {
    "record": CONTROL_FLOOR_RECORD,
    "record_sha256": "0" * 64,
    "git_sha": "0" * 40,
    "device": "mps",
    "torch_version": "2.7.1",
    "seeds": (1337, 1338, 1339),
    "reduction": "range",
    "governs": SIGMA_ZERO_RECORD,
}


def _breach_case(*, beats):
    """A σ=0 reading OUTSIDE the floor, in the named direction, with everything else honest.

    One constructor for both breach directions so the two cases differ in EXACTLY the direction and
    in nothing else — two hand-built fixtures would be free to differ somewhere the assertion does
    not look.
    """
    floor = noise_floor(_CONTROL_READINGS)
    central = _CONTROL_READINGS[0]
    excess = floor * 10.0
    return {
        "control_readings": _CONTROL_READINGS,
        "sigma_zero_reading": central + excess if beats else central - excess,
        "floor": floor,
        "floor_provenance": _FLOOR_PROVENANCE,
    }


def test_floor_breach_halts_the_sweep():
    """D-04, BOTH branches — and the beats-the-control direction as its own assertion.

    The asymmetry is the reason D-04 exists: every correctness bug in this class *improves* utility,
    so a σ=0 that BEATS the control is the direction a real one produces. A test that only checked
    "σ=0 came out worse" would be green against exactly the failure mode being guarded.
    """
    floor = noise_floor(_CONTROL_READINGS)
    central = _CONTROL_READINGS[0]

    # (i) INSIDE the floor — the string, exactly, and no other truthy value.
    inside = sigma_zero_verdict(
        control_readings=_CONTROL_READINGS,
        sigma_zero_reading=central + floor / 2.0,
        floor=floor,
        floor_provenance=_FLOOR_PROVENANCE,
    )
    assert inside == "proceed", (
        f"a σ=0 reading half a floor from the control returned {inside!r} — D-04's only "
        "non-halting outcome is the string 'proceed'"
    )

    # (ii) OUTSIDE the floor, MISSING the control.
    with pytest.raises(SystemExit) as missed:
        sigma_zero_verdict(**_breach_case(beats=False))
    missed_message = str(missed.value)
    for expected in ("HALT", "zero noised points", _FLOOR_PROVENANCE["record"]):
        assert expected in missed_message, (
            f"the halt message omits {expected!r}. An operator reading it has to learn that the "
            "sweep stopped, that NO noised point ran, and which floor record the verdict was "
            f"taken against.\nmessage: {missed_message}"
        )

    # (iii) OUTSIDE the floor, BEATING the control. ITS OWN ASSERTION, deliberately — this is the
    # case most likely to be forgotten, and "better than expected" is the direction a wiring bug
    # in the DP path produces.
    with pytest.raises(SystemExit) as beat:
        sigma_zero_verdict(**_breach_case(beats=True))
    beat_message = str(beat.value)
    assert "HALT" in beat_message and "zero noised points" in beat_message, (
        "a σ=0 reading that BEATS the control by more than the floor did not halt. That is the "
        "direction a correctness bug in this class actually produces — every one of them improves "
        "utility — so a one-sided check is green against the real failure.\n"
        f"message: {beat_message}"
    )
    assert "BEATS" in beat_message, (
        "the halt fired but the message does not name the direction, so the operator cannot tell a "
        f"suspiciously-good σ=0 from a broken one.\nmessage: {beat_message}"
    )


def test_the_halt_branch_is_watched_red_under_a_no_op_verdict():
    """The HALT observed FAILING, in-process and on every suite run — not once by hand.

    A guard nobody has seen fail is not evidence. This is a DIFFERENTIAL on ONE identical breach
    fixture: a deliberately weakened verdict — one that returns ``"proceed"`` unconditionally, i.e.
    exactly the "downgrade the halt to a warning" mutation D-04 forbids — is shown NOT to raise,
    while the real rule does. Both run on the same inputs, so this measures the rule and not the
    fixture.
    """

    def weakened_verdict(**_kwargs):
        """The mutation: D-04 with its halt removed. Kept local so it can never be imported."""
        return "proceed"

    breach = _breach_case(beats=True)

    assert weakened_verdict(**breach) == "proceed", (
        "the weakened verdict did not return 'proceed' — the control arm of this differential is "
        "broken, so the comparison below proves nothing"
    )
    with pytest.raises(SystemExit) as halted:
        sigma_zero_verdict(**breach)
    assert "HALT" in str(halted.value), (
        "the real verdict raised, but not the D-04 halt — the differential must observe THAT "
        f"branch firing, not some earlier refusal.\nmessage: {halted.value}"
    )


def test_a_floor_that_does_not_re_derive_is_refused():
    """A floor one ULP off the reduction's output is REFUSED — by construction, not by magnitude.

    This is the defect class Phase 20 closed at GATE-02: a float ``!=`` defeated by a one-ULP nudge,
    buying a bit-identical verdict off a borrowed number. Here the floor is required to be EXACTLY
    ``noise_floor(control_readings)``, so the nudge is refused because it is not the reduction's
    output at all — there is no magnitude for it to hide under.
    """
    honest = noise_floor(_CONTROL_READINGS)
    nudged = math.nextafter(honest, math.inf)
    assert nudged != honest, "math.nextafter returned the same float — this test would be vacuous"

    with pytest.raises(SystemExit) as refused:
        sigma_zero_verdict(
            control_readings=_CONTROL_READINGS,
            sigma_zero_reading=_CONTROL_READINGS[0],
            floor=nudged,
            floor_provenance=_FLOOR_PROVENANCE,
        )
    message = str(refused.value)
    assert repr(nudged) in message and repr(honest) in message, (
        "the refusal does not publish BOTH the floor it was handed and the floor that re-derives, "
        f"so a reader cannot see how far off it was.\nmessage: {message}"
    )

    # The honest floor on the SAME reading is admitted — the refusal is one-sided, not a blanket
    # rejection that would be green for the wrong reason.
    assert (
        sigma_zero_verdict(
            control_readings=_CONTROL_READINGS,
            sigma_zero_reading=_CONTROL_READINGS[0],
            floor=honest,
            floor_provenance=_FLOOR_PROVENANCE,
        )
        == "proceed"
    )


@pytest.mark.parametrize("dropped", FLOOR_PROVENANCE_KEYS)
def test_a_record_missing_a_provenance_key_is_refused(dropped):
    """EVERY required provenance key, one at a time: refused, and the message NAMES what is missing.

    Parametrized over the imported tuple rather than a retyped list, so a key added to the rule
    gains a case here automatically instead of silently going unchecked. A record missing
    provenance is REFUSED, **never defaulted** — `mitigation_gate`'s D-14(a) reasoning: an
    unlabelled number is indistinguishable from a borrowed one.
    """
    incomplete = {k: v for k, v in _FLOOR_PROVENANCE.items() if k != dropped}

    with pytest.raises(SystemExit) as refused:
        sigma_zero_verdict(
            control_readings=_CONTROL_READINGS,
            sigma_zero_reading=_CONTROL_READINGS[0],
            floor=noise_floor(_CONTROL_READINGS),
            floor_provenance=incomplete,
        )
    message = str(refused.value)
    assert dropped in message, (
        f"dropping {dropped!r} was refused, but the message does not name it — the operator is "
        f"told the record is unusable without being told what to add.\nmessage: {message}"
    )


def test_a_non_mapping_provenance_is_refused():
    """The `hasattr(..., "keys")` branch, driven — a bare number carries no provenance at all."""
    with pytest.raises(SystemExit) as refused:
        sigma_zero_verdict(
            control_readings=_CONTROL_READINGS,
            sigma_zero_reading=_CONTROL_READINGS[0],
            floor=noise_floor(_CONTROL_READINGS),
            floor_provenance=0.04,
        )
    assert "not a mapping" in str(refused.value)


def test_single_seed_readings_are_refused():
    """`noise_floor([x])` raises, naming the one-draw reasoning `mitigation_gate` already uses."""
    with pytest.raises(SystemExit) as refused:
        noise_floor([0.41])
    message = str(refused.value)
    assert "ONE DRAW" in message, (
        "a single-seed floor was refused, but not for the recorded reason. It is not a noise floor "
        f"at all — there is no second reading for it to vary against.\nmessage: {message}"
    )
    # Two readings ARE admitted, so the refusal is a threshold rather than a blanket rejection.
    assert noise_floor((0.40, 0.44)) > 0.0


@pytest.mark.parametrize("bad", (float("nan"), float("inf"), float("-inf")))
def test_a_non_finite_reading_is_refused(bad):
    """A NaN floor compares False against every deviation — it would turn the HALT into a pass."""
    with pytest.raises(SystemExit) as refused:
        noise_floor((0.40, bad, 0.42))
    assert "finite" in str(refused.value)


@pytest.mark.parametrize(
    ("epsilon_n8", "epsilon_n64", "t_n8", "t_n64", "expected", "why"),
    (
        (1.25, 1.25, 400, 400, True, "both equal — the only committable case"),
        (
            1.25,
            math.nextafter(1.25, math.inf),
            400,
            400,
            False,
            "ε differing in the LAST ULP — the concrete statement that no tolerance exists",
        ),
        (1.25, 1.25, 400, 401, False, "T differing by ONE step — where the leak lives"),
        (1.25, 1.30, 400, 512, False, "both differing — the loud case"),
    ),
)
def test_n64_leg_is_withdrawn_on_any_inequality(
    epsilon_n8, epsilon_n64, t_n8, t_n64, expected, why
):
    """D-06: exact ``==`` on both legs, and the ONE-ULP case is asserted False.

    The ULP case is the load-bearing one. The two arms are the SAME call shape at fixed σ — not two
    independent mathematics — so any relative tolerance would admit exactly the wiring leak the
    check exists to catch. Phase 22 rejected this same reasoning once already in DPSGD-05.
    """
    assert (
        n64_leg_is_committable(
            epsilon_n8=epsilon_n8, epsilon_n64=epsilon_n64, t_n8=t_n8, t_n64=t_n64
        )
        is expected
    ), why


@pytest.mark.parametrize(
    ("divisor", "expected"),
    (
        (5.0, 5),  # 5 * c lands EXACTLY on the bound — the inclusive edge
        (4.5, 4),  # 5 * c overruns, 4 * c fits
        (3.5, 3),  # 4 * c overruns, 3 * c fits
        (2.0, 3),  # even 3 * c overruns — STILL 3, because D-03's floor outranks the bound
    ),
)
def test_choose_n_seeds_is_the_committed_rule(divisor, expected):
    """D-03's four boundaries, every cost DERIVED from the imported bound, plus the three refusals.

    Computing each per-seed cost as ``H_PER_POINT_FLOOR_SECONDS / divisor`` is the point: a retyped
    bound is a bound free to disagree with the one the rule enforces, and both numbers would still
    look right.

    THE LAST CASE IS NOT A BUG. D-03 locks N to 3-5, so when even three seeds overrun the budget
    the rule returns 3 and the CALLER records the overrun. The range is the pre-registered
    commitment; the bound is a budget, and a budget miss is a fact to publish rather than a licence
    to break the range.
    """
    cost = H_PER_POINT_FLOOR_SECONDS / divisor
    chosen = choose_n_seeds(cost)
    assert chosen == expected, (
        f"{cost!r}s/seed chose N={chosen}, expected {expected}: "
        f"{chosen} * {cost!r} = {chosen * cost!r} against a bound of {H_PER_POINT_FLOOR_SECONDS}"
    )

    # THE THREE REFUSALS, asserted in this body so they cannot be deleted without a boundary case
    # noticing. Each is invariant of the parameter above; each message must name the value, because
    # "invalid cost" tells an operator nothing about which measurement produced it.
    for value in (0, -1.0, float("inf")):
        with pytest.raises(SystemExit) as refused:
            choose_n_seeds(value)
        assert repr(value) in str(refused.value), (
            f"choose_n_seeds({value!r}) was refused without the message naming the offending "
            f"value.\nmessage: {refused.value}"
        )
