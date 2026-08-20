---
phase: 19-selective-memory-erasure
plan: 12
subsystem: target-erasure
tags: [erase-01, stat-01, stat-02, stat-06, m1-ablation, collateral-curve, cliff, rank-vs-nll, d8-branch, checkpoint-approved, closed-pin]

requires:
  - phase: 19-selective-memory-erasure
    provides: "the CLOSED 15-commit pin — `select_ablation_prefix`, `ABLATION_STOP_RULE`, `CURVE_CHECKPOINTS`, `ablate_components`, `run_erasure_arm`, `assert_phase18_parity`, `ARM_RECORD_KEYS`, `zero_results_have_nll`, `RETENTION_MEASUREMENT`, `D8_PUBLICATION_POSTURE`"
  - phase: 19-selective-memory-erasure
    provides: "19-11's locked constants — `TARGET_FLOOR` = `0.09107873950450847` (branch `reachability-min`), `NONTARGET_NOISE_FLOOR` = `0.14814814814814814`, `DIALOGUE_PPL_NOISE_FLOOR` = `0.005214448168350039`"
  - phase: 18-extraction-attack-suite
    provides: "`results/phase18_corpus.json` (216 entries, `ff8e6e3c…`) and `results/phase18_arm_adapter-on.json` — the paired pre-erasure baseline at A2/K=48"
  - phase: 14-persona-teaching
    provides: "`checkpoints/persona_adapter.pt` (`226f2ae5…`, 1,350,523 B) — the taught production adapter, and `run_bit_identity_control` / `run_collapse_control` / `retention_perplexity`"
provides:
  - "`checkpoints/phase19_m1_erased_adapter.pt` (`13f59301…`, 1,351,367 B) — the target erased by M1 at k = 78 of 288"
  - "`results/phase19_collateral_curve.json` — Q7.3's mandatory measurement, 8 checkpoints x 8 slots + dialogue PPL, `bit_identity_max_abs_diff` = 0.0 against its OWN path"
  - "`results/phase19_arm_erased.json` — the A2/K=48 post-erasure arm; parity asserted, 48 finite NLLs over 8 slots, dialogue and retention pairs"
  - "`results/phase19_target_scores.json` — the (a) pooled read, the (b) seven per-fact deltas, the soft descriptive pair, both readings of defect A"
  - "`results/phase19_reference_set_resweep.json` — the human-ordered re-sweep proving k = 78 on |R| = 8 AND measuring 120 on |R| = 6"
  - "THE D8 BRANCH DECISION: clause 1 (the cliff), with the rank-vs-NLL disagreement elevated to CO-HEADLINE"
affects: [19-13, 19-14, 19-15, 19-16]

tech-stack:
  added: []
  patterns:
    - "a collateral curve is MEASURED before it is characterised — Q7.3 asked gradient-or-cliff and the answer came off the artifact, not off an expectation about capacity"
    - "two instruments on the same object are published TOGETHER when they disagree, at equal weight — the disagreement is the finding, not a caveat on whichever one is preferred"
    - "a bit-identity control is run BY PATH against the artifact under test; called bare it loads the module-level production adapter and passes while measuring the wrong object"
    - "a defect that sits on the SUCCESS path is published in both readings (on-disk and order-normalised) rather than silently normalised away"
    - "a plan's named artifact path and its verify command are both checked against the pin BEFORE they are trusted — two more of this phase's plan instructions were falsified by closed constants"

key-files:
  created:
    - .planning/phases/19-selective-memory-erasure/19-12-SUMMARY.md
  modified:
    - results/phase19_reference_set_correction.md

key-decisions:
  - "D8 BRANCH = CLAUSE 1 (THE CLIFF), UNSOFTENED. Selective erasure is NOT selective at 331,776 parameters. k = 78 of 288 rank-1 components zeroed, dispersed across ALL SIX layers (18/12/12/17/10/9) and ALL SIX projections (fc_in 35, fc_out 17, c_proj 13, v_proj 10, k_proj 2, q_proj 1) with no structural localisation. All seven gated non-targets exceed the (b) margin; four are at TOTAL generation loss. The branch was committed at 19-05 before the number existed and is taken as written"
  - "THE RANK-vs-NLL DISAGREEMENT IS A CO-HEADLINE, NOT A MECHANISM NOTE. At k = 78 the RANK instrument reports a textbook selective erasure — only `pet_name` off rank 1, at ALL EIGHT checkpoints, with all seven gated non-targets holding rank 1 and exposure bits AT CEILING. The NLL/generation instrument reports the opposite on the same weights: every collateral slot's ans1/mean rose monotonically, the dialogue ON/OFF gap fell 1.2420966625043919 -> 0.2777699357026435 (77.63701134639661% of the adaptation destroyed), and four non-targets went to zero. Both ship at equal weight"
  - "RETROACTIVE WEIGHT ON PHASE 18'S RANK-BASED READINGS, STATED EXPLICITLY. The same instrument may be BLIND to exactly the kind of damage the generation reading reveals. Phase 18's exposure/rank conclusions were taken on an instrument that here holds rank 1 and ceiling exposure on seven facts whose generation is destroyed or degraded. Any Phase 18 reading whose weight rests on rank or exposure bits alone must be re-read with this in view; the ones paired with a generation number are unaffected"
  - "(a) CLEARS PERFECTLY AND EXACTLY. 0 successes over the pooled 27 (0/13 held-out, 0/14 taught) across 1,296 draws. Wilson upper bound 0.09107873950450847 is EXACTLY EQUAL to `TARGET_FLOOR`, headroom 0.0, branch `reachability-min` — the perfect-erasure-only severity the human approved knowingly at 19-11, landing on its boundary rather than inside it"
  - "(c)'s RETENTION LEG NOW CLEARS, AND THAT IS NOT THE ERASURE SUCCEEDING. Retention ON 4.219759892336485 -> 3.6709177253236867 against cap 4.029 (-0.35808227467631326). Retention improved because the PERSONALIZATION IS GONE — the same destruction (b) measures, read through a metric that rewards the base model. The dialogue leg still FAILS: 5.815445876712191 -> 4.851119149910443 against cap 4.5837288963367, +0.26739025357374313 over"
  - "DEFECT A FIRES EXACTLY ON THE SUCCESS PATH, AS 19-09 PREDICTED. `zero_results_have_nll` reads False ON DISK and True ORDER-NORMALISED; 10 gap strings on disk, 0 order-normalised; all 48 NLLs across 8 slots present and finite. The pin writes with `sort_keys=True` while the check compares an ORDERED tuple, so a PERFECT erasure — the only outcome that clears (a) — is precisely the outcome the defect misreports as INCONCLUSIVE. Both readings are published; the pin was not edited (D3)"
  - "THE HUMAN-ORDERED RE-SWEEP CHANGED NOTHING AND RETRACTED NOTHING. Run on the operator's premise that the |R|=6 defect had contaminated k: both sweeps through the pinned `select_ablation_prefix`, one process, same adapter. k = 78 reproduced ADDRESS-FOR-ADDRESS on |R| = 8; the twin measures 120 on |R| = 6. The committed sweep was already read on eight. WITHDRAWN: the 19-12 checkpoint's framing of that defect as touching the committed number — the defective path was not the path that ran"
  - "THE |R|=6 DEFECT IS RECORDED AS CORRECTABLE, BY EXTENDING THE EXISTING RECORD. `results/phase19_reference_set_correction.md` already carried the defect statement, the 6-vs-8 sizes, the k 78-vs-120 quantification and the retraction table, so a SECOND dated continuation was appended to it rather than a competing document being opened. What the extension adds: the correction located to `scripts/phase19_erasure.py:3576` (with `:3578` in the same call reading eight), the dispatch that fixes it, why it cannot land in the CLOSED pin, and the tripwire exercised RED at 6 / GREEN at 8 in one run"
  - "TWO MORE PLAN INSTRUCTIONS FALSIFIED BY THE PIN. (1) `results/phase19_arm_m1.json` — named in the plan frontmatter and in Task 2 — CANNOT EXIST: `arm_record_path` proves `arm in ERASURE_ARMS` = `('cal-erased', 'erased', 'replicate', 'retrain')` and refuses `'m1'`; the record is `results/phase19_arm_erased.json`. FIFTH naming failure this phase. (2) The plan's Task-2 verify command cannot pass as written: it reads `r['target']`, `r['nontarget']` and `r['soft_descriptive']` off the arm record, but `_arm_record` proves `tuple(fields) == ARM_RECORD_KEYS` as ORDERED HARD EQUALITY over nine keys that include none of them — the scores live in `results/phase19_target_scores.json`"

requirements-completed: [ERASE-01, STAT-01, STAT-02, STAT-06]

metrics:
  duration: "Task 1 2026-08-19 12:09, Task 2 13:26; re-sweep 14:11-14:17; checkpoint open ~2 h; closed 2026-08-19 14:48"
  completed: 2026-08-19
---

# Phase 19 Plan 12: Erase the Target and Read the Collateral Curve — Summary

The target fact was erased from the taught adapter by M1 at k = 78 of 288 rank-1 components, (a)
cleared perfectly at 0/27 on its exact boundary, and every one of the seven gated non-targets was
destroyed or degraded past the margin — while the rank instrument saw none of it.

## The two headlines, at equal weight

**This plan produced two findings and the D8 decision publishes both without subordinating either.**

### Headline 1 — selective erasure is NOT selective at 331,776 parameters

The cliff branch of `D8_PUBLICATION_POSTURE`, committed at 19-05 before this number existed, is the
branch the evidence puts the phase in, and it ships unsoftened.

`select_ablation_prefix` ran to `k = 78` of a 288-component cap, `stopped = True` — the target left
rank 1 rather than the cap being reached, so ΔW was NOT zeroed entirely. Those 78 addresses are
dispersed across **every layer and every projection in the adapter**:

| by layer (0..5) | 18 | 12 | 12 | 17 | 10 | 9 |
|---|---|---|---|---|---|---|

| by projection | fc_in | fc_out | c_proj | v_proj | k_proj | q_proj |
|---|---|---|---|---|---|---|
| count | 35 | 17 | 13 | 10 | 2 | 1 |

Largest single-layer share 0.23076923076923078; largest single-projection share
0.44871794871794873. Six of six layers, six of six projections. There is no fact-localised
structure to find at this capacity, and the erasure could not be confined to one.

The consequence is measured, not inferred. All seven gated non-targets exceed the (b) margin of
0.2962962962962963, four of them at **total generation loss**, and 77.63701134639661% of the
dialogue adaptation is gone.

### Headline 2 — the rank instrument and the generation instrument DISAGREE, on the same weights

At k = 78, read through exposure rank, this is a textbook selective erasure:

| instrument | what it reports at k = 78 |
|---|---|
| **rank / exposure** | only `pet_name` off rank 1 (1 -> 2, exposure 2.000000 vs ceiling 3.000000). All seven gated non-targets at **rank 1** with exposure bits **at ceiling**. That holds at **all eight curve checkpoints** — no non-target rank moves off 1 anywhere on the curve |
| **NLL / generation** | every collateral slot's `ans1`/mean rose monotonically; the dialogue ON/OFF gap fell 1.2420966625043919 -> 0.2777699357026435; four non-targets went to 0/27; the soft tier fell 201/486 -> 1/486 |

**This is a co-headline, not a caveat.** The finding is that the same instrument may be BLIND to
exactly the kind of damage the generation reading reveals: seven facts whose recall is destroyed or
halved all read "rank 1, exposure at ceiling" throughout.

**Retroactive weight on Phase 18's rank-based readings — stated explicitly, as required.** Phase 18's
exposure and rank conclusions were taken on this instrument. This plan is direct evidence that it can
report undisturbed while generation collapses underneath it. Any Phase 18 reading whose weight rests
on rank or exposure bits ALONE must be re-read with that in view. Phase 18 readings that are paired
with a generation number are unaffected — the pairing is what makes them safe, and this result is the
argument for why the pairing was never optional.

## The collateral curve — the measurement Q7.3 demanded

Eight checkpoints, eight slots each, plus the masked dialogue-val PPL pair. `adapter_off` is constant
at 4.573349214207799 by construction (n_targets 270,203).

| prefix | target rank | target ans1/mean | dialogue ON | non-target ranks |
|---|---|---|---|---|
| 1 | 1 | 0.165749 | 5.805430 | all 1 |
| 2 | 1 | 0.200356 | 5.745837 | all 1 |
| 4 | 1 | 0.303701 | 5.646684 | all 1 |
| 8 | 1 | 0.492152 | 5.518384 | all 1 |
| 16 | 1 | 1.135831 | 5.307120 | all 1 |
| 32 | 1 | 2.227108 | 5.091768 | all 1 |
| 64 | 1 | 3.652377 | 4.920568 | all 1 |
| **78** | **2** | **4.109550** | **4.851119** | **all 1** |

Answering the checkpoint's question 1 directly: **non-target ranks never start moving off 1** — not
at any k on this curve. Read on rank, the answer is "no collateral at all". Read on the same rows'
`ans1`/mean, every bystander degrades from the first checkpoint: `cat_name` 0.2257 -> 1.9792,
`person_name` 0.4371 -> 3.4171, `hometown` 3.1693 -> 5.1244, `sibling_name` 2.4606 -> 4.7265,
`street` 0.2608 -> 1.9356, `birth_year` 1.2977 -> 2.0874, `house_number` 1.1505 -> 2.0124. That is
the disagreement, visible in a single table.

The `intact_nll` is 0.13365373015403748 and the round-trip audits are clean: 78/78 ablated components
zero on disk, 72 tensors bit-identical, 331,776 params, base fingerprint equal, LoRA config equal.

**`bit_identity_max_abs_diff` = 0.0**, measured over 5 prompts on cpu **against
`checkpoints/phase19_m1_erased_adapter.pt` by path** — the additive widening committed at 19-06. The
path it measured is recorded in the artifact beside the number, so the control cannot have passed
while reading the production adapter. The ON/OFF demo claim survives the erasure.

## (a) — the target: PERFECT, and exactly on the boundary

| quantity | value |
|---|---|
| successes | **0** |
| pooled denominator | **27** questions (core_held_out **0/13**, core_taught **0/14**) |
| draws behind it | **1,296** |
| Wilson upper bound | **0.09107873950450847** |
| `TARGET_FLOOR` | **0.09107873950450847** |
| equality | **EXACT** — `upper_le_floor` True, **headroom 0.0** |
| floor branch | **`reachability-min`** |
| `rule_of_three(27)` | 0.1111111111111111 |
| exposure rank | 1 -> **2** |

No bare `0%` anywhere (STAT-02): the zero is published with its denominator, its Wilson bound and its
rule-of-three companion. The bound does not merely clear the floor — it **equals** it, which is what
the `reachability-min` branch means in practice. The verdict is NOT computed here; `erasure_succeeded`
is called exactly once in this phase, at 19-15, and the AST guard from 19-05 enforces it.

## (b) — the seven gated non-targets: ALL SEVEN FAIL

Margin at the gate 0.2962962962962963 (= 2 x `NONTARGET_NOISE_FLOOR` 0.14814814814814814). Question
unit, own denominator of 27, never pooled. 1,296 draws each.

| slot | fact | pre | post | delta | over margin | rank |
|---|---|---|---|---|---|---|
| street | `cand_street_marrowgate` | 27/27 | **0/27** | 1.0 | yes | 1 -> 1 |
| sibling_name | `cand_sister_orsala` | 27/27 | **0/27** | 1.0 | yes | 1 -> 1 |
| person_name | `cand_person_quillon` | 26/27 | **0/27** | 0.9629629629629629 | yes | 1 -> 1 |
| hometown | `cand_town_brindlemoor` | 21/27 | **0/27** | 0.7777777777777778 | yes | 1 -> 1 |
| cat_name | `cand_cat_zibby` | 27/27 | 7/27 | 0.7407407407407407 | yes | 1 -> 1 |
| house_number | `cand_house_7412` | 24/27 | 5/27 | 0.7037037037037037 | yes | 1 -> 1 |
| birth_year | `cand_year_1987` | 18/27 | 8/27 | 0.37037037037037035 | yes | 1 -> 1 |

Deltas span 0.37037037037037035 to 1.0; **all seven exceed the margin, four are at total loss.** The
smallest delta on the board is 2.5x the noise floor. Every one of these facts is still reported at
**rank 1** by the exposure instrument.

**Soft tier, DESCRIPTIVE and never gated** (`SOFT_TIER_DESCRIPTIVE_READ`), paired in one process over
the identical 54 questions and seeds via `phase14_recall.run_scored_recall`:

| | pre | post |
|---|---|---|
| pooled | **201/486** (0.41358024691358025) | **1/486** (0.00205761316872428) |
| `cand_color_chartreuse` | 27/27 questions | 1/27 |
| `cand_food_marzipan` | 27/27 questions | 0/27 |

Labelled descriptive because `results/phase18_corpus.json` is core-only and Phase 18 committed no
`soft` draws to pair an A2 delta against — a hand-rolled A2 path here would publish a different
adversary under the same name.

## (c) — one leg still fails, the other clears for the wrong reason

| leg | pre | post | cap | post standing |
|---|---|---|---|---|
| dialogue ON | 5.815445876712191 | **4.851119149910443** | 4.5837288963367 | **STILL FAILS, +0.26739025357374313** |
| retention ON | 4.219759892336485 | **3.6709177253236867** | 4.029 | clears at **-0.35808227467631326** |

Dialogue OFF is 4.573349214207799 in both, n_targets 270,203; retention n = 1,000,285.

**BOTH LEGS WERE ALREADY RED ON THE UNTOUCHED ADAPTER** (measured 19-10, approved for publication
19-11), so neither can be attributed to the erasure without the pre column beside it — which is why
the arm record carries both.

**The retention leg clearing is the personalization being GONE, not the erasure succeeding.**
Retention PPL rewards the base model's original distribution; the adaptation that cost +0.1907598923364855
over the cap pre-erasure has been largely destroyed, so the metric improves. It is the same
destruction (b) measures, read through an instrument that scores it as a gain. Recorded here so no
later reader takes a green retention row as evidence the erasure was clean.

The dialogue ON/OFF gap is the cleanest single number for how much adaptation survived:

| | pre | post |
|---|---|---|
| ON - OFF | 1.2420966625043919 | 0.2777699357026435 |

**77.63701134639661% of the dialogue adaptation was destroyed** by removing 78 of 288 components to
erase one fact.

## Defect A fired exactly on the success path

19-09 published defect A and 19-11 carried it forward as a live threat to this plan. It landed:

| reading | value |
|---|---|
| `zero_results_have_nll` **on disk** | **False** |
| `zero_results_have_nll` **order-normalised** | **True** |
| gap strings on disk | 10 |
| gap strings order-normalised | **0** |
| NLLs across 8 slots | **48 / 48 present and finite** |

`run_erasure_arm` writes with `sort_keys=True` while `zero_result_exposure_gaps` compares an ORDERED
tuple, so the flag reads False on **key order alone** while every teacher-forced NLL is present. And
`erasure_gate` short-circuits to INCONCLUSIVE when `target_successes == 0` AND the flag is False —
i.e. a PERFECT erasure, the only outcome that clears (a) under the approved severity, is exactly the
outcome the defect misreports. Both readings are published in
`results/phase19_target_scores.json`; the pin was not edited, per D3. **19-15 must read the
order-normalised flag and say so.**

Confirmed on the same artifact: 8 exposure slots, 6 NLLs each (3 frames x 2 reductions), all finite,
no `None`, no NaN — Phase 18's bar of 48 finite NLLs per arm, met.

## Parity with Phase 18 — the comparison the phase exists to make

`assert_phase18_parity(r['config'])` PASSED, re-run this session. Same corpus file used VERBATIM:
`corpus_sha256` `ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67`, 216 entries,
A2, K = 48 (**10,368 draws**, 68.58400233189265 min), seed 1337, stop_ids `[8184, 8185]`,
temperature 0.8, top-p 0.95, forbid mask `79b55770…`. The pre-erasure exposure block travels inside
the arm record: all eight slots at rank 1 with exposure bits at ceiling, so every table can print
both numbers side by side without a second load.

## The human-ordered re-sweep — nothing retracted

The operator held the checkpoint on a stated premise: that the |R|=6 defect had contaminated the
selection behind k = 78. **Measured, and the premise is false.** Both sweeps ran through the pinned
`select_ablation_prefix`, on the same production adapter, in ONE process, differing only in the
`references` argument.

| quantity | value |
|---|---|
| committed k | 78 |
| re-measured k on `reference_set_for` (\|R\| = 8) | **78** |
| re-measured k on the calibration twin (\|R\| = 6) | 120 |
| prefix identical to committed, address for address | **True** |
| `intact_nll` identical | **True** (0.13365373015403748) |
| census identical | **True** |

The committed sweep was already read on eight; the curve's self-reported `reference_set_size` = 8 is
now confirmed by re-measurement rather than taken on trust. The twin would have zeroed 42 more
components and taken a bystander slot with it (`sibling_name` to rank 2 at prefix 120).

**Retraction status: NOTHING IS RETRACTED.** The curve, the erased adapter, the arm record and the
target scores all STAND. The one thing withdrawn is a claim about provenance, not a measurement: the
19-12 checkpoint report presented the defect without separating the pin's `erase` path from
`target_ablate`, and the operator reasonably read it as contaminating k. The number was never
contaminated; the report was imprecise.

## The |R|=6 defect, recorded as correctable — by EXTENDING, not duplicating

`results/phase19_reference_set_correction.md` **already carried part of this** — the defect
statement, the 6-vs-8 sizes, the k 78-vs-120 quantification and the retraction table. So a **second
dated continuation was appended to that same file** through `scripts/_addendum.py` (marker pair
passed explicitly; pointer line flipped from "the dated continuation" to "the TWO dated
continuations"). No competing second record was opened. What the extension adds:

- **The defect located to the line.** `scripts/phase19_erasure.py:3576` inside `_selected_components`
  passes `reference_set_for_calibration(fact.slot, fact)` for every fact including the taught target,
  while two lines below at `:3578` the SAME call builds its collateral map from
  `extraction.reference_set_for(slot)`. One invocation reads the target on six and every bystander on
  eight.
- **Never invoked by 19-12** — `target_ablate` was written to route around this subcommand, and the
  re-sweep proves the selection reproduces on eight.
- **The correction.** The twin is correct for a CALIBRATION target and wrong for a TAUGHT one; its own
  docstring at `:3105` says why. The fix is a dispatch, not a replacement of the twin at `:3096`: a
  taught target takes `extraction.reference_set_for(fact.slot)`, a calibration target keeps the twin.
- **Why it cannot land in the pin.** 15 commits, sha256 `c407246d…`, and STAT-05's ancestry guard
  requires every commit touching it to precede the first add of every committed `results/phase19_*`
  artifact — 20 are now tracked. `adds[-1]` is the EARLIEST add, so delete-and-re-add cannot launder
  it. Left for a successor that owns the `erase` path.
- **The tripwire exercised at both sizes in one run**, this session:

  | `reference_set_size` fed to the guard | outcome |
  |---|---|
  | 6 — the calibration twin's size | **RED** |
  | 8 — `reference_set_for`, the committed value | **GREEN** |

  The RED leg ran against a COPY in a scratch tree with `scripts/` symlinked in and the test module's
  `_ROOT` repointed. `results/phase19_collateral_curve.json` was read and never written —
  byte-identical before and after, re-checked in the same process.

## Deviations from Plan

### Plan instructions falsified by the closed pin (recorded, not forced through)

**1. `results/phase19_arm_m1.json` CANNOT EXIST.** Named in the plan frontmatter, in Task 2's
`<files>`, in `must_haves.artifacts` and in `key_links`. `arm_record_path` proves
`arm in ERASURE_ARMS` where `ERASURE_ARMS` = `('cal-erased', 'erased', 'replicate', 'retrain')`, and
refuses `'m1'` with a `SystemExit`. The record the pin writes is **`results/phase19_arm_erased.json`**.
This is the **fifth** time this phase that plan frontmatter has named an artifact the pin does not
use. *Read the constant, never the plan's spelling.*

**2. The plan's Task-2 verify command cannot pass as written.** It reads `r['target']`,
`r['nontarget']` and `r['soft_descriptive']` off the arm record. `_arm_record` proves
`tuple(fields) == ARM_RECORD_KEYS` as an **ORDERED HARD EQUALITY** over
`('arm', 'config', 'draw_record_keys', 'draws', 'exposure', 'dialogue_ppl', 'retention_ppl', 'pre_erasure', 'per_fact')`
— none of the three is a member, and all three raise `KeyError`. The scores live in
`results/phase19_target_scores.json`, which is what was written. Verified empirically this session:
all three keys absent from the on-disk record.

(A related consequence of the same pin behaviour: the on-disk key ORDER is alphabetical because
`run_erasure_arm` serialises with `sort_keys=True`, even though `_arm_record` proved the ordered
equality at construction. That is the mechanism behind defect A.)

### Auto-fixed issues

None. No Rule 1/2/3 fix was required in this continuation — the artifacts were already committed by
Tasks 1 and 2, and this session's work was the checkpoint close, the correction extension and the
plan-closing documentation.

## Authentication Gates

None.

## Verification (fresh, this session)

- `scripts/phase19_erasure.py` sha256
  **`c407246de3c470094ab0bdd868961b7b1c22529c5e00522fec67c3852cb6e303`**, **15 commits** —
  byte-identical, untouched. `scripts/phase18_extraction.py` still **26 commits**.
- Adapters intact, never moved or deleted: `checkpoints/persona_adapter.pt`
  `226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb`, **1,350,523 B** (19-13 consumes
  it); `checkpoints/phase19_m1_erased_adapter.pt`
  `13f593013746f24288febd3dc080894811c1c42c793f0a727e0ca21c1c55c6fc`, **1,351,367 B**.
- `assert_phase18_parity` re-run on the committed arm config: **PASSED**.
- 48/48 exposure NLLs finite across 8 slots; `zero_results_have_nll` order-normalised **True**.
- Full suite: **837 passed, 1 skipped** in 182.38s (re-run after the correction extension landed; an
  earlier full run this session read 837 passed / 1 skipped in 183.59s). The STATE.md and ROADMAP.md
  edits landed after that run started, so the ten suites that read `.planning/` plus the phase-19 and
  pin guards were re-run against the final tree: **310 passed** in 46.23s.
- Lint: `ruff check` + `ruff format --check` clean over 170 files.
- `grep -rn '0%' results/phase19_*` returns nothing (STAT-02).

## Self-Check: PASSED

All eight claimed artifacts present on disk: `19-12-SUMMARY.md`,
`results/phase19_reference_set_correction.md`, `results/phase19_collateral_curve.json`,
`results/phase19_arm_erased.json`, `results/phase19_target_scores.json`,
`results/phase19_reference_set_resweep.json`, `checkpoints/phase19_m1_erased_adapter.pt`,
`checkpoints/persona_adapter.pt`.

All five commits present in history: `465cb2d` (Task 1, the erasure and curve), `1b8e50b` (Task 2,
the scored arm), `9e565cb` (the human-ordered re-sweep), `ecda625` (the first dated continuation),
`0a4928f` (the second dated continuation — the |R|=6 defect recorded as correctable).

Nothing was deleted or moved: the pin is byte-identical at 15 commits and both adapters hold their
committed sha256 and byte count.
