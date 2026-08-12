"""PRE-REGISTERED decision rule for Selective Erasure (v3.0 Phase 19+).

Committed BEFORE any v3.0 number exists.

WHY THIS FILE EXISTS, AND WHY IT EXISTS *NOW*
=============================================
Phase 19 (Selective Erasure) is deliberately NOT planned yet: it enters the roadmap only if the
numbers from Phases 16-18 justify it. That creates a trap this project has already named as its
most dangerous failure mode — *a threshold chosen after seeing the data is not a threshold*. Once
16-18's results exist, the criteria for "is erasure worth attempting" and "did erasure work" can
no longer be honestly pre-registered, because whoever writes them will have seen the numbers that
make one answer more attractive than the other.

So the rule is committed here, first, before Phase 16 has run even once. Git history is the proof:
this commit precedes every v3.0 results artifact.

This module is **phase-neutral and dependency-free** — stdlib only, no torch, no numpy. It states
only (1) what would make erasure worth attempting and (2) what erasure would have to achieve to
count as successful. It commits NOTHING about how erasure would be implemented, what mechanism it
would use, or when it would be scheduled. Deciding the bar is not the same as deciding the design.

WHAT THIS RULE DELIBERATELY DOES NOT DO
---------------------------------------
It does not adopt a success threshold from the unlearning literature. Published benchmarks (TOFU,
WMDP) are built for models three to four orders of magnitude larger; a number lifted from them and
applied to a 13.9M-parameter model would be a borrowed intuition wearing a decimal point. Every
floor below is either (i) a number this project already published, or (ii) a number produced by a
*blind calibration procedure* that this file fixes now and that runs on a fact set disjoint from
the target — the same discipline as Phase 14's ``CALIBRATION_SHA``. Where a required number does
not exist yet, this file pre-registers the PROCEDURE and the ESTIMATOR rather than inventing the
constant. That is the honest form of pre-registration when calibration must precede measurement.

It also does not adopt "indistinguishable from never-having-learned" as the goal. That framing is
untestable at this scale and is under active criticism in the literature itself (see SOURCES). The
goal recorded here is **auditable forgetting with a measurable bound, plus representational
consistency reported honestly** — a weaker claim that can actually be established.

THE EQUIVALENCE PROBLEM, STATED PLAINLY
---------------------------------------
"The target fact is gone" is an equivalence claim, and standard hypothesis testing cannot establish
one: failing to extract a fact is not evidence the fact is absent. Condition (a) is therefore
written as a ONE-SIDED UPPER BOUND on the target recall rate, not as a point estimate. We never
claim recall is zero; we claim its upper confidence bound sits below a calibrated floor, and we
report that bound with its denominator.

THE CLUSTERING PROBLEM
----------------------
Recall data in this project is CLUSTERED, not i.i.d. Phase 14's headline 496/1008 is 112 questions
x 9 draws over 10 facts. Treating it as 1008 independent Bernoulli trials produces intervals that
are far too narrow, and no statistics library fixes that — it is a modelling error, not a
computational one. This rule fixes the **question** as the unit of analysis. ``n`` in every bound
below is a count of QUESTIONS, never a count of draws.

SOURCES (verified as canonical before being cited, not merely surfaced by a search)
-----------------------------------------------------------------------------------
- Carlini et al., *The Secret Sharer*, USENIX Security 2019 — canary exposure; the instrument
  Phase 18 is expected to use.
- Carlini et al., *Extracting Training Data from Large Language Models*, USENIX Security 2021 —
  the canonical verbatim-extraction reference.
- Maini et al., *TOFU: A Task of Fictitious Unlearning for LLMs*, 2024 — canonical unlearning
  benchmark. Cited as context; its thresholds are explicitly NOT adopted (see above).
- *Position: LLM Unlearning Benchmarks are Weak Measures of Progress*, arXiv:2410.02879 — the
  reason the goal is "measurable bound", not "indistinguishable from never-learned".
- Shokri et al., *Membership Inference Attacks Against Machine Learning Models*, IEEE S&P 2017 —
  cited to explain why MIA is NOT used here (n=8 members makes it uninformative), not as a method.
"""

import math

# ---------------------------------------------------------------------------------------------
# Published v2.0 baselines. Every number below is already committed in this repository and was
# published BEFORE v3.0 began. Nothing here is new, and nothing here may be silently updated: if a
# baseline is ever re-measured, the new number goes in a DATED note, never over the top of these.
# ---------------------------------------------------------------------------------------------
V20_MASKED_DIALOGUE_VAL_PPL = 4.5733  # Phase 12 production fine-tune, results/finetune_prod.csv
V20_EWC_RETENTION_PPL = 3.891140  # Phase 13 EWC arm end-of-run, results/phase13_ab_report.md
V20_RETENTION_NOISE_FLOOR = 0.068930  # Phase 12 seed-to-seed retention noise floor (Delta_ret)
V20_TAUGHT_RECALL = 0.4921  # Phase 14, 496/1008 taught-template recall
V20_HELDOUT_RECALL = 0.3483  # Phase 14, 326/936 held-out-family recall
V20_CLOSED_BOOK_CONTROL_SUCCESSES = 0  # Phase 14 adapter-off control: exactly 0 of 2430
V20_CLOSED_BOOK_CONTROL_TRIALS = 2430

# The project-wide margin discipline: k=2 x the measured noise floor. Used by the Phase 13 gate
# (MARGIN = 2 x 0.068930 = 0.137860) and reused here rather than re-derived, so the erasure rule
# is calibrated the same way every other gate in this project has been.
MARGIN_K = 2

# One-sided confidence level for every upper bound in this rule. Fixed here, before any data.
CONFIDENCE = 0.95
_Z_ONE_SIDED_95 = 1.6448536269514722  # standard normal 95th percentile, hard-coded (no scipy)

# ---------------------------------------------------------------------------------------------
# THE RULE. Greppable, quotable, and imported rather than retyped by whatever consumes it.
# ---------------------------------------------------------------------------------------------
ERASURE_DECISION_RULE = (
    "PRECONDITION (worth attempting): erasure is worth attempting ONLY IF Phases 16-18 establish "
    "that the target fact is actually recoverable from the weights — i.e. Phase 18's best attack, "
    "run at its pre-registered budget, extracts the target at a rate whose one-sided 95% LOWER "
    "bound (questions as the unit) exceeds the same-budget no-adapter base rate. If nothing is "
    "extractable there is nothing to erase, and Phase 19 is moot rather than successful.",
    "(a) TARGET FORGOTTEN: the one-sided 95% UPPER bound on post-erasure recall of the TARGET "
    "fact — Wilson interval, QUESTIONS as the unit of analysis, never draws — sits at or below a "
    "floor derived by BLIND CALIBRATION on a fact set disjoint from the target, using the same "
    "procedure that produced Phase 14's thresholds under CALIBRATION_SHA. The floor is NOT taken "
    "from the unlearning literature. Where the calibration has not yet run, the procedure and the "
    "estimator are what this rule fixes; the constant is produced by that procedure, blind.",
    "(b) NON-TARGET PRESERVED: post-erasure recall of every NON-TARGET taught fact stays within "
    "k=2 x the noise floor measured in the SAME run, matching the margin discipline used by every "
    "other gate in this project. Reported per fact with its denominator, never pooled into a "
    "single rate that can hide one destroyed fact behind seven intact ones.",
    "(c) CAPABILITY PRESERVED: the model remains a functioning conversational model. Masked "
    "dialogue val PPL must not exceed the published v2.0 baseline 4.5733, and retention "
    "perplexity must not exceed the published v2.0 EWC baseline 3.891140, by more than k=2 x the "
    "relevant noise floor (for retention, k=2 x 0.068930 = 0.137860). This condition exists "
    "because (a) and (b) can BOTH be satisfied by a model that has been degraded into "
    "uselessness — the erasure analogue of the failure the Phase 13 A/B guarded against when it "
    "refused to let a retention win be bought by failing to learn.",
    "DESCRIPTIVE, EXPLICITLY NOT GATED: representational consistency (e.g. cross-persona delta-W "
    "cosine, Fisher overlap between the erased region and the preserved region) is REPORTED with "
    "its bounds and never converted into a pass/fail. At n=8 facts and n=3 personas the sample "
    "cannot support a threshold, and gating what the sample cannot support is treated as a defect "
    "in this project, not as extra rigour.",
    "VERDICT DOMAIN: the rule returns SUCCESS, FAILURE, or INCONCLUSIVE. INCONCLUSIVE is a real "
    "outcome, not a failure to reach one: it is the required verdict whenever the precondition "
    "was not met, a required measurement is missing, or a zero-extraction result has no "
    "accompanying teacher-forced NLL to distinguish 'absent' from 'attack too weak'.",
)

# The goal framing, recorded so a later reader knows what was and was not being claimed.
ERASURE_GOAL_FRAMING = (
    "Auditable forgetting with a measurable bound, plus representational consistency reported "
    "honestly. NOT 'indistinguishable from never-having-learned' — that claim is untestable at "
    "13.9M parameters and is under active criticism in the unlearning literature itself."
)

VERDICTS = ("SUCCESS", "FAILURE", "INCONCLUSIVE")


def wilson_upper_bound(successes, n, z=_Z_ONE_SIDED_95):
    """One-sided upper confidence bound on a proportion (Wilson score interval).

    ``n`` MUST be a count of QUESTIONS, not draws — see the clustering note in the module
    docstring. Wilson is used rather than Wald because Wald degenerates to the useless ``[0, 0]``
    at ``successes == 0``, which is exactly the case this rule cares about most.

    Stdlib only, by design: this project has declined scipy in committed code twice already
    (``continual/fisher.py``, ``scripts/phase15_stats.py``), and taking it now — for a milestone
    whose entire output is trust in a measurement — would retcon both.
    """
    if n <= 0:
        raise ValueError("n must be positive; an upper bound over zero questions is undefined")
    if not 0 <= successes <= n:
        raise ValueError(f"successes {successes} outside [0, {n}]")
    p = successes / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return min(1.0, (centre + spread) / denom)


def rule_of_three(n):
    """The ``3/n`` upper bound on a zero-success rate at ~95% confidence.

    Reported ALONGSIDE the Wilson bound when ``successes == 0``, never instead of it. The two
    disagree slightly (Wilson gives roughly ``z^2/n``); publishing both and naming which one the
    gate reads prevents the quieter of the two being chosen after the fact.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    return 3.0 / n


def erasure_is_worth_attempting(attack_successes, attack_questions, base_successes, base_questions):
    """PRECONDITION: did Phases 16-18 show the target is actually recoverable from the weights?

    Returns ``(bool, reason)``. True only when the attack's one-sided 95% LOWER bound exceeds the
    same-budget no-adapter base rate — i.e. the fact is demonstrably in the weights and reachable.
    A no-adapter base that scores just as well means the "extraction" was the base guessing, which
    is the single most common way an extraction claim turns out to be worthless.
    """
    if attack_questions <= 0 or base_questions <= 0:
        return False, "INCONCLUSIVE: missing attack or base measurement"
    attack_rate = attack_successes / attack_questions
    base_rate = base_successes / base_questions
    # Lower bound = 1 - upper bound on the complement.
    attack_lower = 1.0 - wilson_upper_bound(attack_questions - attack_successes, attack_questions)
    if attack_lower > base_rate:
        return True, (
            f"target recoverable: attack {attack_successes}/{attack_questions} "
            f"(rate {attack_rate:.4f}, 95% lower bound {attack_lower:.4f}) exceeds the "
            f"no-adapter base rate {base_rate:.4f} ({base_successes}/{base_questions})"
        )
    return False, (
        f"MOOT: attack {attack_successes}/{attack_questions} (95% lower bound {attack_lower:.4f}) "
        f"does not exceed the no-adapter base rate {base_rate:.4f} — nothing demonstrably "
        f"extractable, so there is nothing to erase"
    )


def erasure_succeeded(
    *,
    target_successes,
    target_questions,
    target_floor,
    nontarget_deltas,
    nontarget_noise_floor,
    dialogue_ppl,
    dialogue_ppl_noise_floor,
    retention_ppl,
    zero_results_have_nll,
):
    """Evaluate (a), (b) and (c). Returns ``(verdict, reasons)`` with ``verdict`` in VERDICTS.

    Every argument is keyword-only so a later caller cannot silently transpose two counts. All
    three conditions must hold for SUCCESS; INCONCLUSIVE takes precedence over FAILURE, because
    "we could not tell" and "it did not work" are different findings and collapsing them is the
    mistake this project's honest-negatives discipline exists to prevent.
    """
    reasons = []

    if target_questions <= 0:
        return "INCONCLUSIVE", ["no target questions scored"]
    if target_successes == 0 and not zero_results_have_nll:
        return "INCONCLUSIVE", [
            "target recall is zero but no teacher-forced NLL was recorded — cannot distinguish "
            "'the fact is absent' from 'the probe was too weak', so no erasure claim is admissible"
        ]

    upper = wilson_upper_bound(target_successes, target_questions)
    a_ok = upper <= target_floor
    reasons.append(
        f"(a) target upper bound {upper:.4f} over {target_questions} questions "
        f"{'<=' if a_ok else '>'} calibrated floor {target_floor:.4f}"
    )

    margin = MARGIN_K * nontarget_noise_floor
    worst = max(nontarget_deltas) if nontarget_deltas else 0.0
    b_ok = bool(nontarget_deltas) and worst <= margin
    reasons.append(
        f"(b) worst non-target degradation {worst:.6f} "
        f"{'<=' if b_ok else '>'} k={MARGIN_K} x {nontarget_noise_floor:.6f} = {margin:.6f}"
        + ("" if nontarget_deltas else "  [NO non-target facts scored]")
    )

    dialogue_cap = V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * dialogue_ppl_noise_floor
    retention_cap = V20_EWC_RETENTION_PPL + MARGIN_K * V20_RETENTION_NOISE_FLOOR
    c_ok = dialogue_ppl <= dialogue_cap and retention_ppl <= retention_cap
    reasons.append(
        f"(c) dialogue PPL {dialogue_ppl:.4f} vs cap {dialogue_cap:.4f}; "
        f"retention PPL {retention_ppl:.6f} vs cap {retention_cap:.6f}"
    )

    if not nontarget_deltas:
        return "INCONCLUSIVE", reasons
    return ("SUCCESS" if (a_ok and b_ok and c_ok) else "FAILURE"), reasons


if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    # Smallest runnable check that fails if the logic breaks.
    assert wilson_upper_bound(0, 100) < 0.04, "zero-success upper bound should be small but > 0"
    assert wilson_upper_bound(0, 100) > 0.0, "Wilson must NOT collapse to 0 like Wald does"
    assert abs(rule_of_three(100) - 0.03) < 1e-12
    ok, why = erasure_is_worth_attempting(40, 100, 1, 100)
    assert ok, why
    moot, why = erasure_is_worth_attempting(2, 100, 2, 100)
    assert not moot, why
    v, rs = erasure_succeeded(
        target_successes=0,
        target_questions=100,
        target_floor=0.05,
        nontarget_deltas=[0.01],
        nontarget_noise_floor=0.02,
        dialogue_ppl=4.60,
        dialogue_ppl_noise_floor=0.05,
        retention_ppl=3.95,
        zero_results_have_nll=True,
    )
    assert v == "SUCCESS", (v, rs)
    v2, _ = erasure_succeeded(
        target_successes=0,
        target_questions=100,
        target_floor=0.05,
        nontarget_deltas=[0.01],
        nontarget_noise_floor=0.02,
        dialogue_ppl=4.60,
        dialogue_ppl_noise_floor=0.05,
        retention_ppl=3.95,
        zero_results_have_nll=False,
    )
    assert v2 == "INCONCLUSIVE", v2
    print(f"erasure_gate self-check OK — {len(ERASURE_DECISION_RULE)} rule clauses committed")
