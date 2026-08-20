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
from erasure_gate import MARGIN_K, V20_MASKED_DIALOGUE_VAL_PPL  # noqa: E402  (same reason)


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


# ---------------------------------------------------------------------------------------------
# THE TWO CHOSEN CONSTANTS, AND THERE ARE EXACTLY TWO (D-18). Everything else in this module is
# measured, imported or computed. Where `erasure_gate.py:75-79` cites an ARTIFACT PATH beside each
# baseline, these two cite PREFERENCE: they encode how much personalization the milestone will
# spend to buy privacy, and committing that before any data exists is exactly what a
# pre-registration is for. A reviewer should find these two numbers and argue with them.
# ---------------------------------------------------------------------------------------------

#   input      : nothing measured — this is a MILESTONE PREFERENCE, stated as one (D-15)
#   rule       : `Y_taught >= F_Y x control_taught_recall` AND
#                `Y_heldout >= F_Y x control_heldout_recall` — ONE fraction, applied to BOTH legs,
#                each against its OWN v4.0 retrained-control value (D-16)
#   why not
#   derived    : a k=2-derived Y would read "recall must be statistically indistinguishable from
#                the un-mitigated control" — a demand for a free lunch that makes the gate vacuous
#                in the opposite direction, i.e. a guaranteed FAIL for any real mitigation
#   never      : v2.0's published 0.4921 / 0.3483 pair. GATE-04 forbids deriving Y from it, and
#                applying one fraction to each leg's own control REPRODUCES the generalization
#                ratio for free, with no second constant and no borrowed run-to-run variance
F_Y = 0.7  # PREFERENCE, not a derivation (D-15 / D-16 / D-18)

#   input      : nothing measured — a MILESTONE PREFERENCE, stated as one (D-17)
#   rule       : (c)'s dialogue leg clears iff `F_C x control_gap <= gap <= <derived upper bound>`
#   separate
#   from F_Y   : (c) is a CATASTROPHE DETECTOR, Y is the UTILITY TARGET — the distinction
#                `erasure_gate.py:111-117` states textually ("because (a) and (b) can BOTH be
#                satisfied by a model that has been degraded into uselessness"). Binding them to
#                one number would also assert a coupling Phases 13 and 19 both MEASURED to be
#                absent
#   bound by   : a measured hard non-vacuity floor, `f_C > 0.2237` — M1 retained
#                0.22362988653603388 of the dialogue gap, so any lower value fails to reject the
#                one destruction event this project has actually measured. 0.5 sits 2.24x above
#                that floor: real margin, not glued to it
F_C = 0.5  # PREFERENCE, not a derivation (D-17 / D-18)

# The D-18 audit surface, kept AS DATA (the `phase19_floor.py:167-175` register) so a reviewer and
# a test both find exactly two numbers to argue with without a second hand-maintained list.
CHOSEN_CONSTANTS = {"F_Y": F_Y, "F_C": F_C}


def superseded_dialogue_cap(*, gap_noise_floor):
    """GATE-02's dialogue half in its ORIGINAL one-sided form — kept COMPUTABLE and SUPERSEDED.

    This is exactly the shape ``erasure_gate.py:245-247`` computes as its local ``dialogue_cap``,
    lifted into a named function so the v4.0 pin can NAME the v3.0 criterion it replaces without
    transcribing its value. Both terms are IMPORTED (``V20_MASKED_DIALOGUE_VAL_PPL``,
    ``MARGIN_K``); nothing here is retyped. At the committed ``dialogue_ppl_noise_floor`` from
    ``results/phase19_noise_floors.json`` it returns the cap the D-01 justification compares
    against, so that comparison is a COMPUTATION this module performs rather than a literal a
    reader must trust.

    It is NEVER applied as a v4.0 criterion. A v4.0 verdict reads the gap BAND (D-01); this
    function exists only so the superseded form can be named by its computation. It is NOT a claim
    that ``23a830c`` was wrong and NOT a licence to amend it.
    """
    if gap_noise_floor < 0:
        raise ValueError(
            f"gap_noise_floor {gap_noise_floor} is negative; a noise floor is a magnitude and a "
            "negative one would compute a cap BELOW the published baseline"
        )
    return V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * gap_noise_floor


# CAL-04 sentence 1: the per-point draw-budget MENU, closed and ordered, committed NOW — before any
# v4.0 artifact exists. Phase 23 SELECTS the rung by measured throughput (CAL-05: 4.77 h/point is a
# FLOOR for noised points, not a mean, because it was measured on the un-adapted base where most
# draws terminated on a stop id). RATCHET: a selected rung may only INCREASE, never decrease, which
# structurally eliminates the post-null K reduction `scripts/phase18_extraction.py:84-93` records as
# the ATK-03 / P18-4 weakening — fewer draws is less power to observe extraction, i.e. an easier
# null. Pre-flight is the one moment that pin left open for it; this ratchet closes it for v4.0.
K_RUNGS = (48, 24, 16, 8)

# ---------------------------------------------------------------------------------------------
# THE RULE. Greppable, quotable, and imported rather than retyped by whatever consumes it — the
# `erasure_gate.py:95-127` shape. These are module DATA, not comments, so a test can assert them
# and a report can quote them without a second hand-maintained copy.
# ---------------------------------------------------------------------------------------------
MITIGATION_DECISION_RULE = (
    "(c) DIALOGUE LEG — SUPERSEDES THE FORM GATE-02 INHERITS (D-01). Condition (c)'s dialogue half "
    "is a BAND ON THE ON-OFF ADAPTATION GAP (`gap = point_ppl_on - point_ppl_off`), never a "
    "one-sided cap on raw perplexity, and this SUPERSEDES the form GATE-02 and "
    "`.planning/ROADMAP.md:163-167` inherit from `.planning/research/SUMMARY.md` R5. The "
    "superseded criterion is named by its COMPUTATION — `superseded_dialogue_cap("
    "gap_noise_floor=<the committed dialogue_ppl_noise_floor from "
    "results/phase19_noise_floors.json>)` — and NEVER by its value: a pin whose entire discipline "
    "is 'computed from imported constants, never retyped' must not retype the one number it "
    "supersedes. THE MEASURED REASON: against that cap the UNTOUCHED TAUGHT ADAPTER reads "
    "5.815445876712191 and fails by +1.231717 before any mitigation runs, while M1 — which "
    "destroyed 77.637% of the dialogue adaptation — reads 4.851119149910443 and fails by only "
    "+0.267390. Retaining that cap as an upper bound therefore SELECTS FOR DESTRUCTION: the only "
    "readings admitted are adapters flattened back to adapter-off. "
    "`results/phase19_erasure_report.md:446-450` reached exactly this conclusion from the same "
    "number R5 cites toward the opposite one.",
    "THE BOUNDARY, STATED EXPLICITLY SO THE CLAUSE ABOVE CANNOT BE MISREAD. This is NOT a claim "
    "that `23a830c` was wrong to be written the way it was, and NOT a licence to amend it. "
    "`scripts/erasure_gate.py` was committed before Phase 16 ran and before any v3.0 number "
    "existed; that ordering is the entire reason any v3.0 figure is worth anything, and amending "
    "it now to a criterion the data would have cleared is the one move that would void the "
    "milestone. `results/phase19_erasure_report.md:453-457` and `docs/REPORT.md:1215` record this "
    "in the repository's own words. v4.0 supersedes v3.0's FORM for v4.0 verdicts only; v3.0's "
    "published verdicts stand unamended and its pin stays byte-untouched.",
    "(c) LEG ASYMMETRY IS BY DESIGN, AND THE REASON IS RECORDED (D-05). The two legs of (c) are "
    "asymmetric in form: dialogue is a BAND, retention is a ONE-SIDED UPPER CAP. The reason is "
    "measured rather than stylistic — the dialogue gap is SIGN-STABLE (always positive, direction "
    "known), while the retention gap CHANGES SIGN inside the already-measured range (taught "
    "+0.3286199167186572, M1 -0.22022225029414155), which makes a symmetric band geometrically "
    "incoherent for the retention leg specifically. Recorded here so a later 'unify the two legs' "
    "refactor goes RED rather than looking like cleanup.",
    "EXACTLY TWO CHOSEN CONSTANTS EXIST IN THIS PIN (D-15 / D-18): `F_Y` and `F_C`, both labelled "
    "in the source as milestone PREFERENCE rather than derivation, and both re-exported as data in "
    "`CHOSEN_CONSTANTS` so an audit needs no second hand-maintained copy. Everything else here is "
    "measured, imported or computed. Y's fraction CANNOT be derived, and that is named rather than "
    "disguised: a k=2-derived Y would read 'recall must be statistically indistinguishable from "
    "the un-mitigated control', which makes the gate vacuous in the opposite direction — a "
    "guaranteed FAIL for any real mitigation. `F_C` is SEPARATE from `F_Y` because (c) is a "
    "catastrophe detector while Y is the utility target, and its hard non-vacuity floor is "
    "MEASURED at f_C > 0.2237: M1 retained 0.22362988653603388 of the dialogue gap, so any lower "
    "fails to reject the one destruction event this project has actually measured.",
    "ORDERING DISCIPLINE (D-08): `results/phase20_retention_floor.json` — and every other "
    "`results/phase20_*` artifact — lands STRICTLY AFTER this file's first commit, never before "
    "and never in the same commit. That rule is TIGHTER than the mechanism requires: "
    "`git merge-base --is-ancestor` is reflexive, so a gate and an artifact committed together "
    "would pass. It is recorded as a discipline so a later reader treats same-commit as neither a "
    "defect nor a licence.",
    "GLOB SCOPE, WITH ITS COST NAMED RATHER THAN HIDDEN (D-33): `V4_ARTIFACT_GLOBS` in "
    "`tests/test_phase20_prereg.py` carries `results/phase20_*` ONLY. Pre-declaring Phases 21 "
    "through 28 was considered and REJECTED — only `phase20_*` can be proven RED-then-GREEN by "
    "this phase's own fixture, and an advance declaration without demonstration is exactly the "
    "kind of unproven assertion this phase exists to refuse. Each of Phases 21-28 adds its own "
    "prefix at the moment it first writes results. The accepted cost: an `assert` catches an "
    "EMPTY match set, never an INCOMPLETE one, so a future phase that forgets its prefix fails "
    "SILENTLY. That risk is accepted in exchange for never asserting coverage this phase cannot "
    "demonstrate.",
)

# The goal framing, recorded so a later reader knows what is and is not being claimed.
MITIGATION_GOAL_FRAMING = (
    "`erasure_gate`'s rejection of 'indistinguishable from never-having-learned' does NOT transfer "
    "to v4.0, and the reason is recorded here so a reader does not misread the v4.0 X ceiling as "
    "reopening a claim this repository committed against (D-10). That rejection targeted an "
    "UNVERIFIABLE POST-HOC ASSERTION about an already-observed erasure result — a claim about a "
    "model's state that no measurement at 13.9M parameters could establish. v4.0's claim is "
    "categorically different: a MATHEMATICAL GUARANTEE BUILT INTO THE DP-SGD MECHANISM, which "
    "holds by construction at the recorded mechanism parameters rather than being asserted after "
    "the fact. The v3.0 framing stands for v3.0; it is not the v4.0 goal and was never refuted."
)
