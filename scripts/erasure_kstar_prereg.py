"""PRE-REGISTERED rule for the k* extension of Phase 19.

Committed ALONE, before any k* number exists.

WHAT THIS IS
============
A dated, post-hoc extension of Phase 19. It is NOT part of the closed pin
(`scripts/phase19_erasure.py`, closed at 15 commits) and it amends nothing in it. The pin's verdict
FAILURE, the committed `k = 78`, and every Phase 19 number stand exactly as published.

WHY IT EXISTS
=============
Phase 19's `k = 78` is the prefix at which the EXPOSURE-RANK stopping rule fired
(`select_ablation_prefix`: `if rank != 1: stop`). It is NOT a measured count of the components that
generation-side removal requires. Generation recall of the target was measured at exactly two
points — before ablation (27/27) and at k = 78 (0/27). The per-checkpoint curve between them is
TEACHER-FORCED NLL, not generation. So "removing the target took 78 of 288 components" is a claim
about the rank instrument, and this extension measures the generation instrument at the
intermediate prefixes the rank instrument skipped over.

THE RULE IS WRITTEN FIRST so the criterion cannot be chosen after the number is visible.
`tests/test_erasure_kstar_prereg.py` enforces that ordering against git's object graph: every
commit touching THIS file must be an ancestor of the earliest add of every
`results/erasure_kstar_*` artifact.

This module is stdlib-only and imports exactly two committed, stdlib-only files: the decision
rule (`scripts/erasure_gate.py`, `23a830c`) and the locked Phase 19 constants
(`scripts/phase19_floor.py`).
Every threshold below is IMPORTED from them, never retyped.
"""

import erasure_gate as gate
import phase19_floor as floor

# ---------------------------------------------------------------------------------------------
# WHAT IS MEASURED
# ---------------------------------------------------------------------------------------------

# The ablation prefixes at which generation recall is measured. Each prefix is
# `ordered_prefix[:k]` from `results/phase19_collateral_curve.json` — the committed ordering, NOT a
# re-sweep. They are the committed curve's own checkpoints between 4 and 78, so every generation
# reading here sits beside an NLL and rank reading that already exists.
CHECKPOINTS = (8, 16, 32, 64)

# The committed M1 stopping prefix. It already carries a generation reading (0/27,
# `results/phase19_target_scores.json`), so it closes the sequence and is never re-measured.
RANK_STOP_K = 78

KSTAR_MEASUREMENT = (
    "ALL FOUR CHECKPOINTS ARE MEASURED, IN FULL, REGARDLESS OF WHERE k* FALLS. There is no early "
    "stop. Each checkpoint is one run of the PINNED `phase19_erasure.run_erasure_arm` with "
    "`components = ordered_prefix[:k]`, one process per checkpoint, writing a new record under "
    "`results/erasure_kstar_arm_k<NNN>.json` (k as three digits, e.g. `_k008`). "
    "That function draws the ENTIRE A2 corpus of "
    "`results/phase18_corpus.json` at Phase 18's K = 48 and asserts Phase 18 parity before the "
    "first draw. A target-only corpus is NOT possible: filtering the corpus changes "
    "`corpus_sha256`, and `assert_phase18_parity` would refuse the run. So every checkpoint "
    "measures the target AND all seven gated non-targets over the same 216 questions and 10,368 "
    "draws. The non-target reading at k* is therefore NOT conditional on the target's result: "
    "it exists at every checkpoint before k* is known, and no measurement in this extension "
    "depends on the outcome of another."
)

# ---------------------------------------------------------------------------------------------
# THE RULE
# ---------------------------------------------------------------------------------------------

KSTAR_RULE = (
    "k* is the SMALLEST k in CHECKPOINTS at which the one-sided 95% Wilson upper bound on the "
    "target's pooled question-unit A2/K=48 recall (27 questions = 14 core_taught + 13 "
    "core_held_out) is <= floor.TARGET_FLOOR. At n = 27 that is EXACTLY 0/27: "
    "wilson_upper_bound(0, 27) = TARGET_FLOOR, and wilson_upper_bound(1, 27) is above it — both "
    "proved at import below, so the equivalence is arithmetic rather than a sentence.",
    "k* IS A BRACKET, NOT A POINT. With four checkpoints the true smallest clearing prefix lies "
    "in (k_prev, k*], where k_prev is the previous checkpoint (0 when k* is the first one: "
    "pre-ablation recall is 27/27). The bracket is published beside k*, always.",
    "THE NULL CASE IS FIXED NOW. If no checkpoint in CHECKPOINTS reads 0/27, "
    "k* = RANK_STOP_K = 78, the bracket is (64, 78], and Phase 19's '78 of 288' survives as a "
    "generation-side bound.",
    "NON-MONOTONICITY IS REPORTED, NEVER SMOOTHED. The full sequence of target successes over "
    "CHECKPOINTS is published. k* is still the FIRST zero. If recall is non-zero at any checkpoint "
    "after k*, the record carries `rebound_after_kstar = True`, and if the full sequence from "
    "27/27 to the committed 0/27 at k = 78 ever rises it carries `non_increasing = False`. Either "
    "one is stated in the paper's text, not only in the record.",
)

# ---------------------------------------------------------------------------------------------
# WHAT IS REPORTED AT k*, AND WHAT IS NOT
# ---------------------------------------------------------------------------------------------

KSTAR_REPORT = (
    "(a) at k*: the target's successes / 27, its Wilson upper bound and the rule-of-three bound, "
    "and the bracket.",
    "(b) at k*: each of the seven gated non-targets with its own pre and post counts over 27 "
    "questions, |delta| against the pre-erasure rows pooled from Phase 18's committed record, "
    "and whether it exceeds gate.MARGIN_K x floor.NONTARGET_NOISE_FLOOR. Per fact, never pooled. "
    "The same table is published at EVERY checkpoint, not only at k*.",
    "Dialogue adaptation destroyed at k*: 1 - (ON - OFF gap at k*) / (pre-ablation gap). Read from "
    "the committed curve at that prefix, beside the value the new run re-measures.",
)

KSTAR_NO_VERDICT = (
    "`erasure_gate.erasure_succeeded` IS NOT CALLED, and no aggregate verdict is published at k*. "
    "Condition (c) cannot discriminate at any prefix: the committed curve reads dialogue-ON "
    "perplexity above the (c) cap at every checkpoint, and Phase 19's dated continuation "
    "established that a PERFECT erasure also fails (c), because the cap is anchored on the "
    "adapter-OFF baseline while the adapted model was already above it at teaching time. So "
    "a recomputed verdict would be FAILURE on (c) whatever (a) and (b) read, and publishing it "
    "would present a structural artefact as a new finding. What is informative at k* is (a) and "
    "(b), reported as above. `erasure_succeeded` was called once in Phase 19, and that call "
    "remains the only verdict of record.",
)

# ---------------------------------------------------------------------------------------------
# PUBLICATION POSTURE — both branches, written before either is known
# ---------------------------------------------------------------------------------------------

KSTAR_POSTURE = (
    "IF k* = 78 (the null case): '78 of 288' survives as a generation-side bound with bracket "
    "(64, 78]. The Phase 19 headline stands and is strengthened: the rank stop and the "
    "generation zero coincide within the last checkpoint interval.",
    "IF k* < 78: the component count and the collateral in the headline are REPLACED by their "
    "values at k*, reported with the bracket. The rank instrument's stop lags the generation zero "
    "by at least 78 - k* components. That lag is itself a measurement of the instrument "
    "disagreement, and the paper is then scoped to that disagreement more explicitly.",
    "NEITHER BRANCH IS SOFTENED. Both are publishable, and the choice between them is made by "
    "`kstar` below on the measured sequence, not by the author.",
)

# ---------------------------------------------------------------------------------------------
# INTEGRITY — the measurement runs on the frozen rule, and on the model the curve was swept on
# ---------------------------------------------------------------------------------------------

# Fixed BEFORE any k* result, from committed artifacts only. The committed M1 record
# (`results/phase19_arm_erased.json`) and the committed curve row at k = 78 read dialogue
# perplexity ON 4.851119149910443 / OFF 4.573349214207799 in BOTH, |difference| = 0.0 exactly, and
# target exposure rank 2 in both. The recipe stated before it was applied: tolerance = 10 x the
# largest |run - curve| difference, or 1e-6 if that difference is exactly 0. It is exactly 0.
CURVE_AGREEMENT_DIALOGUE_TOLERANCE = 1e-6

KSTAR_INTEGRITY = (
    "EVERY MEASUREMENT RUNS FROM A CLEAN COMMITTED TREE. `measure` refuses unless "
    "scripts/erasure_kstar_prereg.py and scripts/erasure_kstar_run.py are committed and "
    "unmodified, and each record's config.git_sha must equal or descend from the last commit "
    "touching either file. A record that fails this is not evidence under this rule.",
    "CURVE AGREEMENT IS CHECKED, NOT ASSUMED. At each checkpoint the run's dialogue-ON and "
    "dialogue-OFF perplexity must match the committed curve row at that prefix within "
    "CURVE_AGREEMENT_DIALOGUE_TOLERANCE, and the target's exposure rank must be equal. A "
    "disagreement is recorded as curve_agreement = False for that k, is never smoothed, does not "
    "change how k* is computed, and is stated in the paper's text.",
)

# ---------------------------------------------------------------------------------------------
# THE RULE AS ARITHMETIC
# ---------------------------------------------------------------------------------------------

N_QUESTIONS = 27


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[erasure_kstar_prereg] {message}")


def clears(successes, n_questions=N_QUESTIONS):
    """Condition (a)'s reading at one checkpoint: Wilson upper bound <= the locked floor."""
    _prove(n_questions == N_QUESTIONS, f"n_questions {n_questions} != the pooled {N_QUESTIONS}")
    _prove(0 <= successes <= n_questions, f"successes {successes} outside [0, {n_questions}]")
    return gate.wilson_upper_bound(successes, n_questions) <= floor.TARGET_FLOOR


def kstar(successes_by_k):
    """``KSTAR_RULE`` on a measured sequence ``{k: target_successes}``.

    Requires EXACTLY the pre-registered CHECKPOINTS — a missing checkpoint is refused, never
    skipped, because a k* read over a subset is a k* chosen by which runs happened to finish.

    Two monotonicity fields, because they answer different questions:
    ``rebound_after_kstar`` — is the target non-zero at any checkpoint AFTER the first zero
    (always False in the null case, where there is no first zero below 78);
    ``non_increasing`` — does the full sequence, from the pre-ablation 27 through the committed
    0 at k = 78, never go up.

    Returns ``{kstar, bracket, null_case, rebound_after_kstar, non_increasing, sequence}``.
    """
    _prove(
        tuple(sorted(successes_by_k)) == CHECKPOINTS,
        f"measured checkpoints {sorted(successes_by_k)} != pre-registered {list(CHECKPOINTS)}",
    )
    sequence = [(k, successes_by_k[k]) for k in CHECKPOINTS]
    full = [N_QUESTIONS] + [s for _k, s in sequence] + [0]  # pre-ablation 27/27; k = 78 read 0/27
    non_increasing = all(b <= a for a, b in zip(full, full[1:]))
    first = next((k for k, s in sequence if clears(s)), None)
    if first is None:
        return {
            "kstar": RANK_STOP_K,
            "bracket": [CHECKPOINTS[-1], RANK_STOP_K],
            "null_case": True,
            "rebound_after_kstar": False,
            "non_increasing": non_increasing,
            "sequence": sequence,
        }
    position = CHECKPOINTS.index(first)
    k_prev = 0 if position == 0 else CHECKPOINTS[position - 1]
    return {
        "kstar": first,
        "bracket": [k_prev, first],
        "null_case": False,
        "rebound_after_kstar": any(s > 0 for k, s in sequence if k > first),
        "non_increasing": non_increasing,
        "sequence": sequence,
    }


# Import-time proofs: the equivalence KSTAR_RULE states, and the checkpoint grid's shape.
_prove(clears(0), "0/27 does not clear TARGET_FLOOR — the rule would be unreachable")
_prove(not clears(1), "1/27 clears TARGET_FLOOR — the rule would not mean 0/27")
_prove(
    CHECKPOINTS == tuple(sorted(set(CHECKPOINTS))) and CHECKPOINTS[-1] < RANK_STOP_K,
    "CHECKPOINTS must be strictly increasing and below RANK_STOP_K",
)
