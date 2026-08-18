"""THE THREE MEASURED PHASE 19 CONSTANTS, LOCKED — the `921a6bc` analogue, and nothing else.

`erasure_succeeded` (`scripts/erasure_gate.py`) reads three numbers this project could not know in
advance: the (a) target floor, the (b) non-target recall noise floor and the (c) dialogue-PPL noise
floor. Each is now measured. Each is written here as a literal, beside a provenance comment naming
the artifact it came from and the commit that published that artifact — the register
`scripts/phase14_recall.py:191-197` uses for `CALIBRATION_SHA`, so any reader can re-derive every
number below from committed inputs without trusting this file.

**WHY THIS FILE IS NOT THE PIN, AND WHY THAT IS NOT A LOOPHOLE (P19-3).**

The rule that produces the (a) floor is `phase19_erasure.lock_erasure_floor`, and it was committed
BLIND — before the calibration adapter existed, while `git ls-files 'results/phase19_*'` was still
empty. `tests/test_phase16_prereg.py::test_phase19_prereg_is_frozen_before_every_phase19_result`
enforces that ordering against git's object graph: every commit touching
`scripts/phase19_erasure.py` must be an ancestor of every `results/phase19_*` artifact's earliest
add. The (a) floor is the rule's OUTPUT on a measured calibration rate, so it cannot exist until a
Phase 19 artifact does — writing it into the pin would make the pin a non-ancestor of the very
artifact it was derived from and turn that guard permanently RED, with no recovery: the guard takes
`adds[-1]`, the EARLIEST add, so a delete-and-re-add cycle cannot launder the ordering. Phase 17
established this two-file split for exactly this reason
(`tests/test_phase16_prereg.py:160-171`, `STATE.md:194`); Phase 18 refused it for the opposite one.
Phase 19 has a sanctioned post-artifact write, so it needs Phase 17's shape.

**WHAT MAKES IT HONEST ANYWAY.** Three things, none of them a promise.

  1. `tests/test_phase16_prereg.py::test_phase19_floor_precedes_every_target_artifact` guards THIS
     file the same way the pin is guarded, against every TARGET artifact: from the first target
     number onward these constants cannot move without a visibly red suite.
  2. Every constant below RE-DERIVES on every suite run — through the PINNED function, from the
     COMMITTED artifact — in `tests/test_phase19_erasure.py`
     (`test_floor_lock_re_derives_all_three_constants_from_their_evidence_artifacts`). A
     hand-edited number goes red. The reduction is never read back out of an artifact as a
     pre-reduced scalar, because a reduction chosen in the artifact writer is a reduction chosen
     with the numbers already visible.
  3. This file holds LITERAL ASSIGNMENTS AND NOTHING ELSE — no rule, no estimator, no report text,
     no import, all of which stay in the closed pin where the ancestry guard watches them
     (`test_floor_lock_holds_only_literal_constants_and_nothing_else`). A sanctioned write that
     could carry a rule beside a constant would be the loophole; this one cannot.

**READ THIS BEFORE USING `TARGET_FLOOR`.** `phase19_erasure._calibration_rate()` returns
`0.8846153846153846` and `lock_erasure_floor` of THAT is `0.2` — which is what the pin's own
`_cmd_report` still prints. That is published defect B: the function reads Phase 18's CANDIDATE
rows out of `record["pre_erasure"]["per_fact"]`, not this phase's calibration arm. The floor below
is derived from the arm's OWN draws and is the one every Phase 19 gate, constant and rendered
verdict is read against (`results/phase19_calibration_correction.json`, field `governs`). Both
numbers are published; the pin was not edited, per D3.
"""

# =============================================================================================
# ===== (a) THE TARGET FLOOR =====
# =============================================================================================

# THE MEASURED (a) FLOOR. `lock_erasure_floor(0/23)` = `max(ERASURE_FLOOR_MIN, min(0.20,
# floor(0.0 x 0.60, 4dp)))` = `ERASURE_FLOOR_MIN` = `wilson_upper_bound(0, 27)`.
#
#   input    : the BLIND calibration rate 0 / 23 questions = 0.0, pooled over both tiers
#              (`core_taught` 0/14 + `core_held_out` 0/9), 1,104 draws, attack family A2 at K = 48,
#              scored by the same adversary at the same budget that will score the target (P19-4)
#   rule     : `phase19_erasure.lock_erasure_floor`, committed BLIND in the closed 15-commit pin
#   bound by : the REACHABILITY CLAMP — the discounted value 0.0 falls under `ERASURE_FLOOR_MIN`,
#              so the outer `max` binds and the floor is exactly the perfect-erasure bound
#   evidence : `results/phase19_arm_cal-erased.json` (the committed draws), re-derived per tier
#              through `phase19_erasure.per_fact_rows`; published with both floors and which
#              governs in `results/phase19_calibration_correction.{md,json}`
#
# WHAT THE BRANCH MEANS, STATED RATHER THAN LEFT TO BE INFERRED. `erasure_succeeded` compares
# `upper <= target_floor` (`scripts/erasure_gate.py:230`) and this floor IS `wilson_upper_bound(0,
# 27)` — the smallest value the gate's own estimator can return at the target's pooled denominator.
# Equality passes, so (a) is still reachable, but it clears ONLY on a PERFECT ERASURE: zero
# successes over all 27 scored target questions. One success anywhere and (a) fails. That severity
# is the rule's own output on a rate of zero, not a number chosen after the fact — the rule's
# clause 4 recorded this consequence before any calibration number existed ("BELOW cal_rate =
# 0.1518 ... (a) then clears ONLY on a PERFECT ERASURE").
TARGET_FLOOR = 0.09107873950450847

# Which of `("reachability-min", "discount", "ceiling")` produced the value above, read off
# `phase19_erasure.floor_branch` rather than inferred from the sentence explaining it.
FLOOR_BRANCH = "reachability-min"

# D2's OTHER DIRECTION, COMMITTED AND NOT MERELY REPORTED. `phase19_erasure.literal_phase14_floor`
# applies Phase 14's operator LITERALLY — `max(FLOOR_CEILING, round(cal_rate x 0.60, 4))`, no
# mirror, no floor-rounding — and at this rate returns 0.20. Against erasure's `<=` cap the SMALLER
# floor is the HARDER one, so the mirror produced the harder criterion (0.0911 < 0.20) and D2's
# "harder, never easier" holds by measurement rather than by argument. Never read by a gate; it is
# here so a reader SEES the choice instead of inferring it, which is what D2 requires.
#
# A COINCIDENCE WORTH NAMING: 0.20 is also what the pin's internal defect-B path computes, by a
# completely different route (rate 0.8846 saturating the `ceiling` branch). Same number, unrelated
# derivations — do not read one as corroborating the other.
LITERAL_PHASE14_FLOOR = 0.2

# The commit that added the arm record the (a) rate was re-derived from — the EVIDENCE, which is
# what a reader needs, and deliberately NOT a verdict commit. The correction naming this floor as
# governing was appended at `dcb1b7c` in a commit whose SHA could not be known while that record
# was being written.
TARGET_FLOOR_EVIDENCE_SHA = "14ab93df61a9399fb815918753b85af27e660447"

# =============================================================================================
# ===== (b) THE NON-TARGET RECALL NOISE FLOOR =====
# =============================================================================================

# THE MEASURED (b) FLOOR. `phase19_erasure.nontarget_noise_floor` — the pinned `max` — over the
# seven per-fact `|delta rate|` values, each over its own denominator of 27 and never pooled.
#
#   input    : `[0.0, 0.0, 0.0, 0.0, 0.03703703703703698, 0.11111111111111105,
#              0.14814814814814814]` in slot order, a SEED-STRIDE REPLICATE of Phase 18's
#              adapter-on arm on the UNERASED production adapter (offset 100000, proved
#              collision-free per question), 9,072 non-target draws, A2 at K = 48
#   rule     : `phase19_erasure.nontarget_noise_floor`, the only committed path to this scalar
#   bound by : `cand_town_brindlemoor` / hometown, 21/27 -> 17/27
#   evidence : `results/phase19_noise_floors.json`, block `nontarget_noise_floor`; raw draws in
#              `results/phase19_arm_replicate.json`
#
# KNOWN SOFTNESS, RECORDED WHERE THE NUMBER IS AND NOT ONLY IN A REPORT. FOUR OF THE SEVEN INPUTS
# TO THE `max` CANNOT CONTRIBUTE TO IT. `cat_name`, `street` and `sibling_name` read 27/27 in BOTH
# readings and `person_name` reads 26/27 in both — a saturated fact has no room to vary upward, so
# its zero delta is a CEILING ARTEFACT and not a measurement of sampling noise. The published floor
# is therefore the noise of the three facts that CAN move, taken over a set where four are pinned.
#
# AND THE NUMBER IS THRESHOLD-SHAPED, SO ITS PERMISSIVENESS IS PART OF IT. `erasure_succeeded`
# multiplies this by `MARGIN_K`, giving a margin of 0.2962962962962963 at the gate:
# 0.2963 x 27 = 8.0, so a non-target fact may lose EIGHT of its twenty-seven questions
# post-erasure and still clear (b).
NONTARGET_NOISE_FLOOR = 0.14814814814814814

# The commit that PUBLISHED the (b) block and added the replicate arm record it was derived from.
# `results/phase19_noise_floors.json` was first added one commit earlier with the (c) block alone;
# this SHA points at the evidence for THIS constant, which is what re-deriving it requires.
NONTARGET_NOISE_FLOOR_EVIDENCE_SHA = "8a02b04dc1a43d9554afb2e03aaa561a38d89a70"

# =============================================================================================
# ===== (c) THE DIALOGUE-PERPLEXITY NOISE FLOOR =====
# =============================================================================================

# THE MEASURED (c) FLOOR. `phase19_erasure.dialogue_noise_floor(ppl_seed_a, ppl_seed_b)` — one
# absolute difference over the pinned seed pair, in the ADAPTER REGIME the gate actually reads.
#
#   input    : masked dialogue-val PPL with the adapter ON at seed 1337 = 5.815445876712191 and at
#              seed 2024 = 5.810231428543841, over 270,203 scored targets each; the adapter-OFF
#              readings are IDENTICAL across the two seeds (4.573349214207799), which is what makes
#              the difference above a seed effect on the adaptation rather than instrument drift
#   rule     : `phase19_erasure.dialogue_noise_floor` via `dialogue_floor_from_record`
#   cap      : `dialogue_cap(this)` = 4.5837288963367 (`V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K x`)
#   evidence : `results/phase19_noise_floors.json`, block `dialogue_ppl_noise_floor`; raw record
#              `results/phase19_dialogue_floor.json`
#
# CONDITION (c) IS ALREADY RED, BEFORE ANY ERASURE EXISTS, AND THAT IS RECORDED HERE RATHER THAN
# DISCOVERED LATER. On the UNTOUCHED production taught adapter the dialogue leg reads 5.8154
# against the 4.5837 cap above (+1.2317 over) and the retention leg reads 4.219759892336485
# against its fully determined 4.029000 cap (+0.1908 over). Admitting the pre-erasure model on the
# dialogue leg would need a floor of 0.62105 — roughly 119x the floor actually measured. So (c) as
# written cannot attribute anything to an erasure that has not happened, and a (c) failure that
# PREDATES the erasure is a different finding from one CAUSED by it. Under D3 the literal result
# ships unsoftened with the dated diagnosis beside it; the estimators were not re-chosen and the
# rule was not amended. Whatever post-erasure (c) reading 19-15 renders must be published beside
# these pre-erasure ones or the report will attribute a pre-existing failure to the erasure.
DIALOGUE_PPL_NOISE_FLOOR = 0.005214448168350039

# The commit that added `results/phase19_dialogue_floor.json` and published the (c) block.
DIALOGUE_PPL_NOISE_FLOOR_EVIDENCE_SHA = "c9f5f979c89face353f68ddf13a9824d15702b83"

# =============================================================================================
# ===== THE PROVENANCE MAP =====
# =============================================================================================

# Which committed artifact each constant is re-derived FROM. Kept as data so
# `test_floor_lock_evidence_shas_are_real_commits_that_touched_their_artifacts` can assert every
# `*_EVIDENCE_SHA` above is a real commit that actually touches its artifact, and that the artifact
# is tracked — without a second hand-maintained copy of the pairing living in the test.
EVIDENCE_ARTIFACT = {
    "TARGET_FLOOR": "results/phase19_arm_cal-erased.json",
    "NONTARGET_NOISE_FLOOR": "results/phase19_noise_floors.json",
    "DIALOGUE_PPL_NOISE_FLOOR": "results/phase19_noise_floors.json",
}
