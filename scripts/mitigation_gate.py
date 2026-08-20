"""PRE-REGISTERED decision rule for the v4.0 mitigation sweep — the THREE-CONDITION GATE.

Committed BEFORE any v4.0 number exists — before the Phase 23 cost calibration, not merely before
the Phase 25 sweep. ``scripts/erasure_gate.py`` earned its authority exactly this way, committed at
``23a830c`` before Phase 16 ran; this module is the v4.0 continuation of that discipline and NOT a
copy of its thresholds.

CLOSED AT THE FIRST ARTIFACT, AND THE CLOSURE IS MECHANICAL
===========================================================
The moment any ``results/phase20_*`` artifact is committed, this file is CLOSED. A correction after
that point is a DATED CONTINUATION via ``scripts/_addendum.py`` (D-24), never an edit:
``tests/test_phase20_prereg.py`` requires every commit touching this file to be an ancestor of
every v4.0 artifact's first add, so an edit turns that guard permanently RED. A ``git rm`` plus a
re-add at the same path CANNOT launder it — the guard takes ``adds[-1]``, the EARLIEST add, so the
original ordering survives the deletion. There is no recovery path and no force flag, and that cost
is the entire reason the guard is armed in the phase's FIRST plan rather than retro-fitted once
there is something to miss.

WHAT IS NEVER IMPORTED FROM ``erasure_gate``, AND WHY
-----------------------------------------------------
- ``VERDICTS`` — ``("SUCCESS", "FAILURE", "INCONCLUSIVE")`` is the WRONG DOMAIN for v4.0, which
  returns ``PASS`` / ``FAIL`` / ``INCONCLUSIVE`` (GATE-01). Importing it would put the wrong three
  names in this module's namespace, so the relationship between the two vocabularies is PROVED
  instead, through the module handle — see ``_prove_verdict_domain`` (D-31).
- ``V20_RETENTION_NOISE_FLOOR`` — a Phase 12 FULL-FINE-TUNE seed pair, which would govern an
  adapter-regime verdict. D-06 supersedes it for v4.0; the v4.0 retention floor arrives as a
  required kwarg (D-07), measured in the regime it judges.

Every other ``erasure_gate`` name this module uses is IMPORTED by object identity, never retyped,
and each one lands in the plan whose code first consumes it.

CPU-only: stdlib plus ``erasure_gate``. No torch, no numpy, no network, no I/O.
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import erasure_gate  # noqa: E402  (needs the sys.path insert above)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``_addendum.py:50-53``'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof. The message carries this
    module's own name in brackets — an abort naming the wrong module sends its reader to the wrong
    file.
    """
    if not condition:
        raise SystemExit(f"[mitigation_gate] {message}")


# ---------------------------------------------------------------------------------------------
# THE VERDICT DOMAIN. GATE-01 and ROADMAP SC1 require PASS / FAIL / INCONCLUSIVE, while
# `erasure_gate.py:136` publishes SUCCESS / FAILURE / INCONCLUSIVE. `.planning/REQUIREMENTS.md:27`
# is authoritative over `.planning/ROADMAP.md:172`'s `FAILURE` slip. This is the ONE tuple a phase
# whose whole discipline is "import, never retype" cannot import, so it is declared here and its
# relationship to the v3.0 vocabulary is PROVED at import (D-31).
# ---------------------------------------------------------------------------------------------
V4_VERDICTS = ("PASS", "FAIL", "INCONCLUSIVE")

# The explicit v3.0 -> v4.0 name map. Written out rather than derived, so the correspondence being
# proved below is a stated claim that can be read and contested, not an artefact of zip order.
_VERDICT_RELABEL = {
    "SUCCESS": "PASS",
    "FAILURE": "FAIL",
    "INCONCLUSIVE": "INCONCLUSIVE",
}


def _prove_verdict_domain():
    """Prove ``V4_VERDICTS`` is a RELABELLING of ``erasure_gate.VERDICTS``, not a second domain.

    The discipline is kept by PROVING the relationship, not by asserting it in a comment a refactor
    can break. Called at MODULE SCOPE so a dead gate fails at import rather than after the compute
    it would waste — the same reason the Phase 19 dispatch table is proved at import.

    Three separate proofs, because they fail for three different reasons and a reader debugging one
    should not have to guess which:

      1. EQUAL LENGTH — a fourth v4.0 verdict, or a dropped one, is a different domain wearing the
         same name. GATE-01 fixes the arity at three.
      2. POSITIONAL CORRESPONDENCE — every v3.0 name maps, through ``_VERDICT_RELABEL``, to the
         v4.0 name at its OWN index. This is what makes ``V4_VERDICTS`` a relabelling rather than a
         coincidentally-three-long tuple.
      3. ``INCONCLUSIVE`` PRESERVED — the one name both vocabularies spell identically, at the same
         index in both. It is the verdict this project's honest-negatives discipline exists to keep
         distinct from FAIL, so a silent respelling of it is the most damaging drift available.
    """
    _prove(
        len(V4_VERDICTS) == len(erasure_gate.VERDICTS),
        f"the v4.0 domain holds {len(V4_VERDICTS)} verdict(s) {V4_VERDICTS} against the v3.0 "
        f"{len(erasure_gate.VERDICTS)} {erasure_gate.VERDICTS} — GATE-01 fixes the arity at "
        "three, so a length mismatch is a different domain wearing the same name",
    )
    for i, v3_name in enumerate(erasure_gate.VERDICTS):
        _prove(
            _VERDICT_RELABEL.get(v3_name) == V4_VERDICTS[i],
            f"position {i}: erasure_gate.VERDICTS[{i}] is {v3_name!r}, which _VERDICT_RELABEL "
            f"sends to {_VERDICT_RELABEL.get(v3_name)!r}, but V4_VERDICTS[{i}] is "
            f"{V4_VERDICTS[i]!r}. The v4.0 domain must be a RELABELLING of the v3.0 one, not a "
            "second independent vocabulary that happens to be three names long",
        )
    shared = "INCONCLUSIVE"
    _prove(
        shared in erasure_gate.VERDICTS
        and shared in V4_VERDICTS
        and erasure_gate.VERDICTS.index(shared) == V4_VERDICTS.index(shared),
        f"{shared!r} must appear in BOTH vocabularies, spelled identically and at the same index: "
        f"erasure_gate.VERDICTS is {erasure_gate.VERDICTS} and V4_VERDICTS is {V4_VERDICTS}. "
        "'we could not tell' and 'it did not work' are different findings, and the name that keeps "
        "them apart is the one name a relabelling must not touch",
    )


_prove_verdict_domain()


# ---------------------------------------------------------------------------------------------
# ARM IDENTITY (GATE-07 / D-28). A closed set, because "there exists a clearing point" over the
# UNION of the two arms conflates a formal guarantee with an empirical one.
# ---------------------------------------------------------------------------------------------
ARMS = ("dp", "adversarial")

ARM_CLAIMS = {
    "dp": (
        "FORMAL GUARANTEE. A clearing DP point carries an (epsilon, delta)-differential-privacy "
        "claim: a mathematical property of the DP-SGD mechanism at the recorded noise multiplier, "
        "step count, sampling rate and delta. It bounds what ANY adversary can learn, including "
        "adversaries nobody in this project thought to run, and it holds whether or not an attack "
        "was attempted."
    ),
    "adversarial": (
        "NOT A FORMAL GUARANTEE, and this is stated rather than left to be inferred. A clearing "
        "adversarial point is an empirical result about the specific attacks that were actually "
        "run, at the specific budget they were run at: evidence that THOSE attacks failed, never "
        "evidence that extraction is impossible. A stronger — or merely different — attack is not "
        "excluded by this arm and never will be."
    ),
}

_prove(
    tuple(ARM_CLAIMS) == ARMS,
    f"the claim table holds {tuple(ARM_CLAIMS)} against the committed {ARMS}. The published set "
    "and the runnable set must be ONE set: a name with no claim string is a name a later plan "
    "would have to add code for, which is a commit to this file — and once any "
    "`results/phase20_*` artifact exists, such a commit turns the ancestry guard permanently red",
)
