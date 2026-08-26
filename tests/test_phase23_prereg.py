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

import fnmatch
import json
import math
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

from phase23_prereg import (  # noqa: E402  (needs the sys.path insert above)
    CONTROL_FLOOR_RECORD,
    FLOOR_PROVENANCE_KEYS,
    H_PER_POINT_FLOOR_SECONDS,
    NOISED_RECORD_GLOB,
    SIGMA_ZERO_RECORD,
    choose_n_seeds,
    n64_leg_is_committable,
    noise_floor,
    noised_record_path,
    sigma_zero_verdict,
)

# IMPORTED AND CALLED, NEVER COPIED. `_assert_ordering_holds` is the body Phase 20, 21 and 22's
# live guards run; a lookalike copy here would prove something about a DIFFERENT function than the
# one CI executes, and would decay silently the moment the real helper changed. `tests/` is not a
# package, so the sys.path insert above is what makes this reachable —
# `tests/test_phase22_fakes.py:44-50` already does cross-file imports exactly this way.
from test_phase20_prereg import _assert_ordering_holds, _git  # noqa: E402  (same reason)

_PREREG_MODULE = "scripts/phase23_prereg.py"
_PHASE23_ARTIFACT_GLOB = "results/phase23_*"

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


# =================================================================================================
# ===== THE THREE ANCESTRY GUARDS — vacuous-safe today, hard from the first artifact =====
#
# `globs=(artifact_glob,)` is passed DELIBERATELY, and not `V4_ARTIFACT_GLOBS`. That tuple already
# carries `results/phase23_*` for the ACCOUNTANT's guard
# (`test_phase22_prereg_is_frozen_before_every_phase23_result`), and Phase 21 D-20 measured that
# `globs` is read in exactly ONE place inside `_assert_ordering_holds` — its
# `assert artifact_glob in globs` consistency check — while the ordering loop runs on the SINGULAR
# `artifact_glob`. So widening that tuple would buy nothing here, and these three guards are about
# a different pair of ENDPOINTS entirely: not "the accountant pin before a Phase-23 number" but
# "this phase's own rule, control record and σ=0 record before what each of them pins". Passing the
# singleton satisfies the consistency check without touching a constant three other guards share.
# =================================================================================================


def _ordering_guard(*, prereg_artifact, artifact_glob):
    """`_assert_ordering_holds`, wrapped in the Phase-18 vacuity shape. Returns the pairs checked.

    GREEN WHILE NOTHING IS TRACKED, HARD FROM THE FIRST ARTIFACT. The wrapper is required rather
    than cosmetic: two of the three guards below name a `prereg_artifact` that does not exist yet
    (`CONTROL_FLOOR_RECORD` and `SIGMA_ZERO_RECORD` are written in 23-08 and 23-10), and the helper
    asserts `prereg_commits` non-empty — so calling it unconditionally today would be RED from this
    commit until an artifact lands, inverting the very ordering this discipline exists to
    establish. That is Phase 16's shape and `tests/test_phase20_prereg.py:283-287` records why it
    is wrong.

    The closing `bool(checked) == bool(tracked)` is what stops the vacuity SURVIVING the artifacts'
    arrival: it ties what was compared to whether anything was tracked at all, so the first
    committed artifact makes a still-empty comparison RED instead of quietly green.

    A missing pre-registration WITH artifacts present is its own named red, not folded into the
    equivalence — "the pin does not exist" and "the ordering is violated" are different findings.
    """
    tracked = _git("ls-files", artifact_glob).split()
    prereg_commits = _git("log", "--format=%H", "--", prereg_artifact).split()

    checked = 0
    if tracked:
        assert prereg_commits, (
            f"{len(tracked)} artifact(s) match `git ls-files {artifact_glob}` while "
            f"{prereg_artifact} has NO commits. The thing being pinned exists and the pin does "
            "not, which is the one ordering this guard can never repair: `adds[-1]` takes the "
            "EARLIEST add, so committing the pin now would not make it an ancestor"
        )
        _assert_ordering_holds(
            root=_ROOT,
            prereg_artifact=prereg_artifact,
            artifact_glob=artifact_glob,
            globs=(artifact_glob,),
        )
        checked = len(prereg_commits) * len(tracked)

    assert bool(checked) == bool(tracked), (
        f"checked {checked} pair(s) against {len(tracked)} tracked artifact(s) matching "
        f"`git ls-files {artifact_glob}` — those disagree, so either committed Phase 23 results "
        "went unchecked or the ordering loop ran on paths the match set does not contain. A guard "
        "that checks zero artifacts once results exist is green and blind."
    )
    return checked


def test_the_prereg_rule_precedes_every_phase23_result():
    """D-03: the blind rules were committed BEFORE any Phase-23 number, as a fact about git.

    Every commit touching `scripts/phase23_prereg.py` must be a STRICT ancestor of every
    `results/phase23_*` artifact's EARLIEST add. That is what makes "committed blind" checkable
    rather than claimed — for `noise_floor` and for `choose_n_seeds` alike, which is the entire
    reason the seed-count rule lives in that module instead of in the driver that measures the
    scoring cost deciding it. That driver is re-edited by 23-08 Tasks 2 and 3, by 23-10, by 23-11
    and by 23-14, so `git log -1` on it returns its most recent commit and no ancestry check could
    bind a rule there to anything.

    **AND THIS IS WHAT MAKES `scripts/phase23_prereg.py` EDIT-ONCE.** From 23-04's commit — the
    first Phase-23 artifact — any commit touching that file turns this test permanently RED with no
    recovery path: the ordering loop takes `adds[-1]`, the EARLIEST add, so a delete-and-re-add
    cannot launder it. A correction goes through `scripts/_addendum.py`'s register, published
    elsewhere and dated, never as an edit here.

    Vacuous TODAY BY CONSTRUCTION — `git ls-files results/phase23_*` matches nothing at this
    commit, which is recorded in `23-03-SUMMARY.md` as the state at commit time.
    """
    _ordering_guard(prereg_artifact=_PREREG_MODULE, artifact_glob=_PHASE23_ARTIFACT_GLOB)


def test_control_precedes_sigma_zero():
    """D-03: the control record's first git add STRICTLY PRECEDES the σ=0 record's.

    **THE ORDERING IS THE GUARANTEE, NOT A PROMISE.** A floor reduced after σ=0's number is visible
    is a floor reduced with that number visible, whatever the intent — and no amount of prose can
    distinguish the two after the fact. Requiring the control record to land first makes the
    question answerable from the object graph: the floor was in the repository before the reading
    it judges existed.

    `adds[-1]` — the EARLIEST add — is what makes this permanent. Deleting the control record and
    re-adding it after σ=0 does not reset the ordering; it produces a second add the guard does not
    look at.

    Both paths are resolved from `scripts/phase23_prereg.py`, never retyped, so this guard cannot
    end up watching a path the writer does not use.
    """
    _ordering_guard(prereg_artifact=CONTROL_FLOOR_RECORD, artifact_glob=SIGMA_ZERO_RECORD)


def test_sigma_zero_precedes_every_noised_point():
    """DPSGD-06: σ=0 is the DP arm's FIRST executed run — no noised record may precede it.

    The σ=0 diagnostic is worth running only if it runs FIRST. A sweep point committed before it
    means the diagnostic was read with sweep results already in hand, which is the peek DPSGD-06
    exists to forbid.

    THE CAL-03 WIRING RECORD IS DELIBERATELY OUTSIDE THIS GLOB, and the reason is stated in
    `scripts/phase23_prereg.py`: it exports no adapter, scores no question and runs a toy
    `ModelConfig` under `max_steps_override`. It is a wiring probe, not a sweep point. Its
    exemption is a property of its CONTENT (`sweep_point: false`) rather than of its name — see
    `test_every_noised_sweep_point_is_under_the_noised_glob`, which closes the converse hole this
    path-glob guard cannot see.
    """
    _ordering_guard(prereg_artifact=SIGMA_ZERO_RECORD, artifact_glob=NOISED_RECORD_GLOB)


# The three endpoint pairs, each with a concrete artifact path that MUST match its glob. The third
# element is produced by `noised_record_path` rather than typed, so the fixture rehearses the same
# derivation 23-11 will call.
_ORDERING_ENDPOINTS = (
    (_PREREG_MODULE, _PHASE23_ARTIFACT_GLOB, "results/phase23_probe.json"),
    (CONTROL_FLOOR_RECORD, SIGMA_ZERO_RECORD, SIGMA_ZERO_RECORD),
    (SIGMA_ZERO_RECORD, NOISED_RECORD_GLOB, noised_record_path("dp_n64", 0.5)),
)


def _init_throwaway(root):
    """A scratch repository with LOCAL identity — writes only to `root/.git/config`.

    Local rather than global config so the fixture is independent of whether the host has a
    `user.email` at all (CI runners generally do not), and so nothing outside `tmp_path` is touched.
    """
    root.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=root)
    _git("config", "user.name", "phase23-fixture", cwd=root)
    _git("config", "user.email", "phase23-fixture@localhost", cwd=root)


def _commit_into(root, relpath, message):
    """Write a shape-only stand-in at `relpath` and commit it. The CONTENT is never the subject."""
    target = root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{"note": "shape only — this repository is a throwaway"}\n')
    _git("add", relpath, cwd=root)
    _git("commit", "-q", "-m", message, cwd=root)


@pytest.mark.parametrize(("prereg", "artifact_glob", "artifact"), _ORDERING_ENDPOINTS)
def test_the_phase23_ordering_guards_are_red_then_green(tmp_path, prereg, artifact_glob, artifact):
    """Each of the three prefixes OBSERVED biting — RED on a wrong order, GREEN on a right one.

    **Reading a glob pattern and confirming it BITES are different acts.** The three live guards
    above are vacuous today, so none of these patterns has ever been seen matching anything; a
    pattern that reads correctly while matching nothing is green over nothing. The comment block at
    `tests/test_phase20_prereg.py:125-170` records that this mutation-invisibility gets WORSE with
    more prefixes live — and this plan adds three at once, which is exactly the situation it warns
    about. So each pair is driven through a wrong order and a right one in its own throwaway
    repository, and the `ls-files` assertion at each is a POSITIVE OBSERVATION of the glob matching
    rather than an inference from the pattern's text.

    **It runs the SAME `_assert_ordering_holds` the live guards call**, parameterized on `root`.

    Two separate scratch repositories rather than one repaired in place, deliberately: the red is
    NOT repairable by re-committing, which is the property `adds[-1]` buys and the reason the real
    module is edit-once. The real repository's history is never touched — every `_git` call below
    passes `cwd=`, and everything lives under pytest's `tmp_path`.
    """
    wrong = tmp_path / "wrong-order"
    _init_throwaway(wrong)
    _commit_into(wrong, artifact, "the artifact, committed FIRST — the order the guard forbids")
    _commit_into(wrong, prereg, "the pre-registration, committed SECOND")

    assert _git("ls-files", artifact_glob, cwd=wrong).split() == [artifact], (
        f"`git ls-files {artifact_glob}` did not match the committed {artifact}. The ordering "
        "failure below is unreachable unless this match set is non-empty, so without this "
        "observation a guard watching the wrong prefix would pass silently"
    )
    with pytest.raises(subprocess.CalledProcessError) as out_of_order:
        _assert_ordering_holds(
            root=wrong,
            prereg_artifact=prereg,
            artifact_glob=artifact_glob,
            globs=(artifact_glob,),
        )
    # `subprocess.run(check=True)` fails with no explanatory message, so name the failing command:
    # without this, ANY CalledProcessError from ANY git call would satisfy the `raises` above.
    assert tuple(out_of_order.value.cmd[:3]) == ("git", "merge-base", "--is-ancestor"), (
        f"the wrong-order repository failed on {out_of_order.value.cmd} — the expected red is the "
        "ancestry check itself, not an incidental git failure elsewhere in the helper"
    )

    right = tmp_path / "right-order"
    _init_throwaway(right)
    _commit_into(right, prereg, "the pre-registration, committed FIRST")
    _commit_into(right, artifact, "the artifact, committed SECOND — strictly after the pin")

    assert _git("ls-files", artifact_glob, cwd=right).split() == [artifact]
    _assert_ordering_holds(
        root=right,
        prereg_artifact=prereg,
        artifact_glob=artifact_glob,
        globs=(artifact_glob,),
    )


def test_no_phase23_artifact_sits_outside_the_prefix():
    """A Phase-23 artifact named anything else is invisible to EVERY guard in this file.

    `results/phase23_` is not a naming convention, it is the membership test. A file called
    `results/sigma_zero.json` is watched by nothing here and by nothing at
    `tests/test_phase20_prereg.py:332` either — not merely unwatched but structurally invisible,
    which is the worst of the two because it looks like coverage.

    This scans by BASENAME rather than by the prefix, so a file that names the phase and misses the
    prefix is caught. Vacuous today and named as such; hard from the first Phase-23 artifact.
    """
    tracked = _git("ls-files", "results/*").split()
    stray = [
        path
        for path in tracked
        if "phase23" in pathlib.PurePosixPath(path).name and not path.startswith("results/phase23_")
    ]
    assert stray == [], (
        f"{len(stray)} tracked artifact(s) name phase23 but sit outside the `results/phase23_` "
        f"prefix: {stray}. Every ordering guard in this file and the accountant's guard at "
        "tests/test_phase20_prereg.py:332 bind on that prefix, so these are watched by nothing. "
        "Resolve the path from scripts/phase23_prereg.py rather than typing it at the call site"
    )


def _prove_noised_record_is_under_the_glob(path, payload):
    """The ONE content-side predicate, run by the live scan AND by the watched-RED cases below.

    Returns True when a real σ>0 sweep point was checked, False when the record is out of scope.

    `sweep_point` is **not** a schema-required key — 23-05's `TRAINING_RECORD_KEYS` and
    `GENERATION_RECORD_KEYS` do not contain it, and across the whole phase only 23-04's wiring
    record declares it. So a record carrying `sigma > 0` and NO `sweep_point` key is a REFUSAL, not
    an exemption: without that line the escape simply moves from "wrong filename" to "missing key",
    and a wrong filename is a choice somebody made while an omission requires no lie at all. Only
    an explicit `sweep_point: false` exempts; silence does not.
    """
    sigma = payload.get("sigma")
    if not isinstance(sigma, (int, float)) or isinstance(sigma, bool) or not sigma > 0:
        return False

    assert "sweep_point" in payload, (
        f"{path} declares sigma={sigma!r} and carries NO `sweep_point` key. Silence is not a "
        "declaration: `sweep_point` is not schema-required, so omitting it would exempt a real "
        "sweep point from the σ=0 ordering with no false statement at all. Declare "
        "`sweep_point: true` and file the record at "
        "phase23_prereg.noised_record_path(arm, sigma), or declare `sweep_point: false` and say "
        "why it is not a sweep point"
    )
    if payload["sweep_point"] is not True:
        return False

    assert fnmatch.fnmatch(path, NOISED_RECORD_GLOB), (
        f"{path} declares sigma={sigma!r} at a real sweep point but does not match "
        f"{NOISED_RECORD_GLOB}. `test_sigma_zero_precedes_every_noised_point` binds on that glob, "
        "so this record would escape the DPSGD-06 ordering BY FILENAME — the guard would never "
        "see it. Produce the path with phase23_prereg.noised_record_path(arm, sigma)"
    )
    return True


def test_every_noised_sweep_point_is_under_the_noised_glob():
    """T-23-81 / T-23-84: a σ>0 sweep point cannot escape the noised glob by name OR by omission.

    Every ordering guard above binds on a PATH GLOB. Nothing in this file otherwise asserts the
    converse — that a record whose CONTENT declares a real sweep point is actually filed under the
    glob. Without it a record can declare σ > 0 at a real sweep point and escape the σ=0 ordering
    simply by being named something else, and the guard would never see it.

    So membership of the noised glob becomes a consequence of what a record says about ITSELF. And
    23-04's `CAL03_WIRING_RECORD` is exempt because it declares `sweep_point: false` — a property
    of its CONTENT, not of its name. That is the whole point, and it is why saying NOTHING must be
    a refusal rather than a third exemption.

    Vacuous-safe by the same shape as the ordering guards: zero tracked records passes having
    checked nothing, hard from the first one onward. The two escape routes are watched FAILING on
    synthetic records in this same body, so the closure is observed rather than assumed.
    """
    tracked = [
        path for path in _git("ls-files", _PHASE23_ARTIFACT_GLOB).split() if path.endswith(".json")
    ]
    scanned = 0
    for path in tracked:
        _prove_noised_record_is_under_the_glob(
            path, json.loads((_ROOT / path).read_text(encoding="utf-8"))
        )
        scanned += 1
    assert bool(scanned) == bool(tracked), (
        f"scanned {scanned} of {len(tracked)} tracked `{_PHASE23_ARTIFACT_GLOB}` json record(s) — "
        "a content guard that reads zero records once records exist is green and blind"
    )

    # WATCHED RED 1 — T-23-81, the FILENAME escape. A real sweep point named outside the glob.
    escaped_name = "results/phase23_dp_run_at_sigma_one.json"
    with pytest.raises(AssertionError) as renamed:
        _prove_noised_record_is_under_the_glob(escaped_name, {"sigma": 1.0, "sweep_point": True})
    assert escaped_name in str(renamed.value)

    # WATCHED RED 2 — T-23-84, the OMISSION escape. The path here IS under the glob, so this
    # isolates the missing key: the refusal must fire on CONTENT alone, independent of the name.
    with pytest.raises(AssertionError) as silent:
        _prove_noised_record_is_under_the_glob(noised_record_path("dp", 1.0), {"sigma": 1.0})
    assert "sweep_point" in str(silent.value)

    # THE TWO ONE-SIDED CONTROLS, so neither refusal above is a blanket rejection: a correctly
    # named sweep point is CHECKED and admitted, and CAL-03's wiring record is EXEMPT by its own
    # explicit `sweep_point: false` while sitting outside the glob.
    assert _prove_noised_record_is_under_the_glob(
        noised_record_path("dp", 1.0), {"sigma": 1.0, "sweep_point": True}
    )
    assert not _prove_noised_record_is_under_the_glob(
        "results/phase23_cal03_wiring.json", {"sigma": 1.0, "sweep_point": False}
    )
