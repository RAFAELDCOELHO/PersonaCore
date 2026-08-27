"""THE MATCHED COMPARATOR'S PIN, DRIVEN — ancestry guard, three live censuses, seven RED watches.

``scripts/phase23_matched_prereg.py`` declares the protocol-matched comparator's rules while
``git ls-files 'results/phase23_matched_*'`` returns nothing. A rule nobody has watched fire is a
rule nobody has verified, so every refusal below is EXECUTED against a constructed defect rather
than described — and the three completeness censuses are run against the REAL ``loop.py`` and
``teach_persona.py`` read off disk, not against a fixture that can drift away from them.

**IMPORTED AND CALLED, NEVER COPIED.** ``_ordering_guard`` and ``_git`` come from the live test
modules, for the reason ``tests/test_phase23_prereg.py:51-56`` already records: a lookalike copy
would prove something about a DIFFERENT function than the one CI executes, and would decay silently
the moment the real helper changed. ``tests/`` is not a package, so the ``sys.path`` insert below is
what makes the cross-file import reachable.

CPU-only, GPU-free, no torch, no network.
"""

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase23_matched_prereg as matched  # noqa: E402  (needs the sys.path insert above)

# IMPORTED AND CALLED, NEVER COPIED — see the module docstring.
from test_phase20_prereg import _git  # noqa: E402  (same reason)
from test_phase23_prereg import _ordering_guard  # noqa: E402  (same reason)

_LOOP = _ROOT / "src" / "personacore" / "training" / "loop.py"
_TEACH = _ROOT / "scripts" / "teach_persona.py"

# SYNTHETIC THROUGHOUT and labelled so: no matched arm exists — this pin is committed while the
# glob it governs is EMPTY, which is the whole point of it landing in wave 9. These are CONSTRUCTED
# inputs chosen to exercise a branch, never a measurement.
_SEVEN_BRANCH_SOURCE = """
def _optimizer_step(dp_fn):
    if dp_fn is not None:
        begin_step()
    x = 1 if dp_fn is not None else 2
    if dp_fn is not None:
        absorb_record()
    if dp_fn is None:
        clip_grad_norm_()

def _dp_extra(dp_fn):
    if dp_fn is None:
        return {}

def train(dp_fn, ckpt):
    if dp_fn is None and ckpt.get("dp_noise_rng") is not None:
        pass
    if dp_fn is not None and ckpt.get("dp_noise_rng") is not None:
        pass
"""

_CLIP_BRANCH = "    if dp_fn is None:\n        clip_grad_norm_()"


def _teach_shaped(*, dp_kwargs_keys, train_keys, splat="dp_kwargs"):
    """A synthetic ``train_arm``-shaped source. CONSTRUCTED, never read from the tree."""
    kwargs = ", ".join(f"{key}={i}" for i, key in enumerate(dp_kwargs_keys))
    named = ", ".join(f"{key}={i}" for i, key in enumerate(train_keys))
    return (
        "def train_arm(is_dp):\n"
        "    dp_accum = dict(grad_accum_steps=8) if is_dp else {}\n"
        f"    dp_kwargs = dict({kwargs}) if is_dp else {{}}\n"
        f"    final = train({named}, **{splat})\n"
    )


_LIVE_DP_KWARGS = tuple(matched.DP_KWARGS_KEYS)
_LIVE_TRAIN_NAMED = tuple(sorted(set(matched.TRAIN_CALL_KEYS) - set(_LIVE_DP_KWARGS)))


# =================================================================================================
# ===== TEST 1 — THE ANCESTRY GUARD — vacuous-safe today, HARD from 23-17's first artifact =====
# =================================================================================================


def test_the_matched_prereg_precedes_every_matched_artifact():
    """The comparator's protocol was pinned BEFORE its readings, as a fact about git's object graph.

    **GREEN AND VACUOUS TODAY**, deliberately: `MATCHED_ARTIFACT_GLOB` matches nothing, so there is
    no pair to compare and `_ordering_guard` returns 0. It becomes HARD from 23-17's first
    artifact, when every commit touching `scripts/phase23_matched_prereg.py` must be a STRICT
    ancestor of that artifact's EARLIEST add.

    `_ordering_guard`'s closing `bool(checked) == bool(tracked)` is what stops the vacuity SURVIVING
    the artifacts' arrival: it ties what was compared to whether anything was tracked at all, so the
    first committed matched artifact makes a still-empty comparison RED instead of quietly green.

    Both values are RESOLVED FROM THE MODULE and never retyped — a retyped glob is a glob free to
    disagree with the one the rules bind on, and the disagreement would be invisible.
    """
    checked = _ordering_guard(
        prereg_artifact="scripts/phase23_matched_prereg.py",
        artifact_glob=matched.MATCHED_ARTIFACT_GLOB,
    )
    assert checked >= 0


# =================================================================================================
# ===== TESTS 2-4 — THE THREE CENSUSES, AGAINST LIVE SOURCE =====
# =================================================================================================


def test_the_branch_ledger_matches_the_live_loop():
    """The seven-branch `dp_fn` ledger is checked against the REAL `loop.py`, read off disk.

    The named key is `("_optimizer_step", "dp_fn is None")` — the `clip_grad_norm_` branch **23-08
    DID NOT ENUMERATE**. It is asserted by name so a future reader sees the one that was missed is
    the one now watched, rather than trusting a total.
    """
    census = matched.prove_branch_ledger_complete(_LOOP.read_text())

    assert sum(census.values()) == 7, (
        f"the live loop.py census sums to {sum(census.values())}, not 7: {sorted(census.items())}"
    )
    assert census[("_optimizer_step", "dp_fn is None")] == 1, (
        "the `clip_grad_norm_` branch 23-08 missed is not present exactly once in the live "
        f"census: {sorted(census.items())}"
    )
    assert len(matched.DP_FN_BRANCH_DISPOSITIONS) == 7


def test_the_dp_wiring_keys_match_the_live_caller():
    """`dp_accum` / `dp_kwargs` are read by AST from the REAL `teach_persona.py`, never retyped."""
    accum, kwargs = matched.prove_dp_wiring_keys(_TEACH.read_text())

    assert accum == frozenset(matched.DP_TRAIN_KEYS) == frozenset({"grad_accum_steps"})
    assert kwargs == frozenset(matched.DP_KWARGS_KEYS)
    assert kwargs == frozenset(
        {"dp_fn", "fact_bin", "n_facts", "replay_bin", "replay_mask_bin", "replay_windows"}
    )


def test_the_train_call_keys_match_the_live_caller():
    """The production `train(...)` keyword union — the leg the other two censuses cannot see.

    THE GAP THIS CLOSES: the branch census sees `dp_fn`-conditioned branches and the wiring census
    sees the two DP dicts. NEITHER sees the other 15 keywords of the production call, so BOTH would
    stay GREEN while a 16th production keyword silently un-matched the comparator — the 23-08
    failure shape one level up.

    `resume_from` and `dp_fn` are both asserted present because they are exactly the two the
    comparator SUBTRACTS: no resume (which is what makes the two `train` resume branches
    `unreached`) and no DP seam (a non-DP arm that nonetheless reaches the `dp_kwargs` wiring).
    """
    union = matched.prove_train_call_keys(_TEACH.read_text())

    assert len(union) == 21, f"the resolved union has {len(union)} names, not 21: {sorted(union)}"
    assert len(set(matched.TRAIN_CALL_KEYS)) == 21
    assert "resume_from" in union, "the keyword the comparator omits is not in the pinned set"
    assert "dp_fn" in union, "the keyword that IS the point is not in the pinned set"


# =================================================================================================
# ===== TESTS 5-8 — THE CENSUS REFUSALS, WATCHED RED. An unwatched guard is not evidence =====
# =================================================================================================


def test_a_planted_dp_fn_branch_is_refused():
    """WATCHED RED: an EIGHTH `dp_fn` branch in the source is refused, and named."""
    planted = _SEVEN_BRANCH_SOURCE.replace(
        _CLIP_BRANCH, _CLIP_BRANCH + "\n    if dp_fn is None:\n        something_new()"
    )
    # The synthetic seven must be ADMITTED first, or this test proves nothing about the eighth.
    matched.prove_branch_ledger_complete(_SEVEN_BRANCH_SOURCE)

    with pytest.raises(SystemExit) as refused:
        matched.prove_branch_ledger_complete(planted)

    message = str(refused.value)
    assert "UNDECLARED" in message, message
    assert "_optimizer_step" in message and "dp_fn is None" in message, (
        f"the refusal does not name the undeclared pair: {message}"
    )


def test_a_removed_dp_fn_branch_is_refused():
    """WATCHED RED, the other direction: a DELETED branch is refused too.

    Both directions matter because this module is EDIT-ONCE — a ledger whose evidence describes
    code that no longer exists cannot be corrected, so it must fail loudly instead.
    """
    removed = _SEVEN_BRANCH_SOURCE.replace(_CLIP_BRANCH + "\n", "")
    assert removed != _SEVEN_BRANCH_SOURCE, "the fixture edit did not apply — this would be vacuous"

    with pytest.raises(SystemExit) as refused:
        matched.prove_branch_ledger_complete(removed)

    message = str(refused.value)
    assert "MISSING" in message, message
    assert "_optimizer_step" in message and "dp_fn is None" in message, (
        f"the refusal does not name the missing pair: {message}"
    )


def test_a_dropped_dp_kwarg_is_refused():
    """WATCHED RED: a `dp_kwargs` dict missing `replay_windows` is refused, and the name printed."""
    short = tuple(key for key in _LIVE_DP_KWARGS if key != "replay_windows")
    source = _teach_shaped(dp_kwargs_keys=short, train_keys=_LIVE_TRAIN_NAMED)

    with pytest.raises(SystemExit) as refused:
        matched.prove_dp_wiring_keys(source)

    message = str(refused.value)
    assert "replay_windows" in message, message
    assert "MISSING" in message, message


def test_an_added_train_call_keyword_is_refused():
    """WATCHED RED: the 23-08 failure shape reproduced deliberately, one level up.

    One extra production keyword (`extra_eval_fns`) un-matches the comparator while the branch
    census and the wiring census both stay GREEN. Asserted here so that blindness is closed by a
    mechanism rather than by a reader noticing.
    """
    source = _teach_shaped(
        dp_kwargs_keys=_LIVE_DP_KWARGS,
        train_keys=_LIVE_TRAIN_NAMED + ("extra_eval_fns",),
    )
    # The other two censuses are GREEN on this very source — that is the point being made.
    matched.prove_dp_wiring_keys(source)

    with pytest.raises(SystemExit) as refused:
        matched.prove_train_call_keys(source)

    message = str(refused.value)
    assert "extra_eval_fns" in message, message
    assert "UNDECLARED" in message, message

    # And the undefected shape is ADMITTED, so the refusal above is about the extra key and not
    # about the fixture being malformed.
    clean = _teach_shaped(dp_kwargs_keys=_LIVE_DP_KWARGS, train_keys=_LIVE_TRAIN_NAMED)
    assert matched.prove_train_call_keys(clean) == set(matched.TRAIN_CALL_KEYS)


# =================================================================================================
# ===== TEST 9 — ONE ATTEMPT — and the HONESTY OF ITS WORDING is itself the deliverable =====
# =================================================================================================


def test_a_second_attempt_is_refused():
    """WATCHED RED: a tracked matched artifact refuses a second attempt; an empty list does not.

    **AND THE MESSAGE MUST NAME ALL FOUR SCOPE CLAUSES**, because an OVERCLAIMED GUARANTEE IS THE
    DEFECT THIS MODULE EXISTS TO PREVENT and this particular claim has already been overstated
    twice. Clauses (2) and (3) are asserted EXPLICITLY BY NAME, and BOTH HALVES of (3) — the
    auditability AND its non-retroactive start point — because:

      * an auditability claim without its start point is the same overclaim in new clothes; and
      * a test checking only three clauses passes against a message naming three of four, which is
        exactly how the previous overclaim survived a revision.
    """
    assert matched.prove_first_attempt([]) is True, "an EMPTY tracked list must not be refused"

    with pytest.raises(SystemExit) as refused:
        matched.prove_first_attempt([matched.MATCHED_CONTROL_RECORD])
    message = str(refused.value)

    # (1) the uncommitted window
    assert "UNCOMMITTED WINDOW" in message, message
    assert ".gitignore:17" in message and ".gitignore:14" in message, message

    # (2) the full-delete case is PREVENTED BY NOTHING in real time
    assert "PREVENTED BY NOTHING" in message, message
    assert "prior_scored_seeds_at_start" in message, message
    assert "INDISTINGUISHABLE FROM A FIRST" in message, message

    # (3a) that same case IS auditable after the fact
    assert "AUDITABLE AFTER THE FACT" in message, message
    assert "cfa2c87" in message, message
    assert "VISIBLE DIFF" in message, message
    # (3b) ...and its start point — tracking is NOT retroactive, so auditability begins AT the
    # commit, and that commit is a DISCIPLINE, not a mechanism. Asserted separately from (3a):
    # a message carrying only the good half is the overclaim this whole clause exists to refuse.
    assert "NOT RETROACTIVE" in message, message
    assert "AUDITABILITY BEGINS ONLY AT THE COMMIT" in message, message
    assert "DISCIPLINE, NOT A MECHANISM" in message, message

    # (4) one glob only — VISIBLE, not REFUSED
    assert "phase23_rematch_" in message, message
    assert "VISIBLE, NOT REFUSED" in message, message

    # And the words that would signal an overclaim are ABSENT.
    assert "closed" not in message.replace("sound closed", "").replace("not 'closed'", ""), (
        f"the refusal message calls this residual 'closed', which it is not: {message}"
    )


# =================================================================================================
# ===== TESTS 10-11 — THE VISIBILITY DISCLOSURE — a REQUIRED FIELD OF BOTH RECORDS =====
# =================================================================================================


def _complete_verdict_record():
    record = dict.fromkeys(matched.VERDICT_REQUIRED_KEYS)
    record["sigma_zero_was_visible"] = True
    return record


def test_the_verdict_record_must_declare_every_required_key():
    """WATCHED RED three ways — and the third drives the WHOLE tuple, not only the two flags.

    Checking every member is what makes the refusal live in the MODULE rather than only here: this
    file could be deleted by the same commit that drops a key, and `VERDICT_REQUIRED_KEYS` cannot
    be extended later because the module is EDIT-ONCE from 23-17's first artifact.
    """
    assert matched.prove_verdict_record_declares_visibility(_complete_verdict_record()) is True

    # (i) the visibility flag ABSENT
    absent = {k: v for k, v in _complete_verdict_record().items() if k != "sigma_zero_was_visible"}
    with pytest.raises(SystemExit) as refused:
        matched.prove_verdict_record_declares_visibility(absent)
    assert "sigma_zero_was_visible" in str(refused.value)

    # (ii) the visibility flag set to False — the σ=0 reading WAS visible; denying it is refused
    denied = _complete_verdict_record()
    denied["sigma_zero_was_visible"] = False
    with pytest.raises(SystemExit) as refused:
        matched.prove_verdict_record_declares_visibility(denied)
    assert "not True" in str(refused.value), str(refused.value)

    # (iii) EVERY OTHER member, one dropped at a time
    for key in matched.VERDICT_REQUIRED_KEYS:
        short = {k: v for k, v in _complete_verdict_record().items() if k != key}
        with pytest.raises(SystemExit) as refused:
            matched.prove_verdict_record_declares_visibility(short)
        assert key in str(refused.value), (
            f"dropping {key!r} was refused without the message naming it: {refused.value}"
        )


def test_the_control_record_must_declare_the_visibility():
    """WATCHED RED: 23-17's CONTROL record carries the disclosure too, and this is not redundant.

    `results/phase23_matched_control.json` is the artifact whose PROTOCOL was designed with
    `0.7837301587301587` on screen. A disclosure that does not travel with the artifact it is about
    is a disclosure a reader of that artifact never sees.
    """
    complete = {
        "sigma_zero_was_visible": True,
        "sigma_zero_visibility_disclosure": matched.SIGMA_ZERO_VISIBILITY_DISCLOSURE,
    }
    assert matched.prove_control_record_declares_visibility(complete) is True

    with pytest.raises(SystemExit) as refused:
        matched.prove_control_record_declares_visibility({"sigma_zero_visibility_disclosure": "x"})
    assert "sigma_zero_was_visible" in str(refused.value)

    denied = dict(complete, sigma_zero_was_visible=False)
    with pytest.raises(SystemExit) as refused:
        matched.prove_control_record_declares_visibility(denied)
    assert "not True" in str(refused.value), str(refused.value)

    # An EMPTY disclosure satisfies a key check and discloses nothing, which is worse than an
    # absent one because it looks answered.
    empty = dict(complete, sigma_zero_visibility_disclosure="   ")
    with pytest.raises(SystemExit) as refused:
        matched.prove_control_record_declares_visibility(empty)
    assert "empty" in str(refused.value), str(refused.value)

    # The pinned disclosure states its four scope clauses and the visibility fact itself.
    disclosure = matched.SIGMA_ZERO_VISIBILITY_DISCLOSURE
    assert "0.7837301587301587" in disclosure
    assert "c7de5d4" in disclosure
    assert "UNCOMMITTED WINDOW" in disclosure
    assert "PREVENTED BY NOTHING IN REAL TIME" in disclosure
    assert "TRACKING IS NOT RETROACTIVE" in disclosure
    assert "DISCIPLINE, NOT A MECHANISM" in disclosure
    assert "ONE GLOB" in disclosure


# =================================================================================================
# ===== TEST 12 — THE THREE CLOSED PRE-REGISTRATIONS ARE BYTE-UNCHANGED =====
# =================================================================================================


def test_the_closed_preregistrations_are_untouched():
    """ "The corrected comparator is an INPUT, not a rule change" — made CHECKABLE rather than said.

    `scripts/phase23_prereg.py` against its BLIND BIRTH COMMIT `c7de5d4`, and the two frozen
    mitigation modules against `HEAD` (the `git diff --exit-code` equivalent: no uncommitted
    change). If any of the three moved, `sigma_zero_verdict`'s blindness would no longer be a fact
    about git and this whole gap-closure wave would be arguing from a rule it had edited.
    """
    assert _git("diff", "--stat", "c7de5d4", "HEAD", "--", "scripts/phase23_prereg.py") == "", (
        "scripts/phase23_prereg.py is NOT byte-identical to its blind birth commit c7de5d4"
    )

    for frozen in (
        "scripts/phase23_prereg.py",
        "scripts/mitigation_gate.py",
        "scripts/mitigation_accountant.py",
        "scripts/mitigation_budget.py",
    ):
        assert _git("diff", "--", frozen) == "", f"{frozen} has an uncommitted modification"
        assert _git("diff", "--cached", "--", frozen) == "", f"{frozen} has a STAGED modification"
