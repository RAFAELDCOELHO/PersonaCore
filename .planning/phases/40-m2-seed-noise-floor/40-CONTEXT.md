# Phase 40: M2 Seed Noise Floor - Context

**Gathered:** 2026-10-05
**Status:** Ready for planning

<domain>
## Phase Boundary

E2 (NOISE-01, NOISE-02). Retrain the full taught adapter and the M2 adapter (the real arm minus
`pet_name`) at the S = 5 seeds of Phase 35's `seed_list()` = (1337, 2024, 1338, 2025, 1339), score
each of the 7 gated non-targets' A2 recall at K = 48 per seed with its denominator, and publish the
training-seed noise floor beside v3.0's sampling floor 0.14814814814814814 WITHOUT amending v3.0's
(b) margin 0.2962962962962963. The phase also publishes `results/phase40_noise_floor.json::
gap_noise_floor` (Phase 35's Phase-40 noise-floor contract), which Phase 41 consumes in its
condition-(c) band, and its seed-1337 and seed-2024 adapters are the ones Phase 41 reuses by SHA-256
(ERASE-05). The floor never gates E1 (b) (Phase 35 D-16).

All decisions below were decided by Rafael in discuss-phase 40 (2026-10-05). Every factual premise
in his reply was measured before it was written here (see `<specifics>`).

</domain>

<decisions>
## Implementation Decisions

### Carried forward (not re-decided)
- S = 5 is READ from `results/phase36_budget.json::e2_seed_count` by the `e2_S` slot; it is never
  typed (35-CONTEXT Addendum to D-15). Unit caps E2: adapters 2, seeds 5. Front hours E2
  7.890925927716101 h = 5 x (e2_train_m2_high 76.11 s + e2_train_full_high 80.84 s + 2 x
  e2_a2_pass_high 2762.26 s).
- Process as in Phases 37-39: a phase-owned prereg + ancestry test committed before any
  `results/phase40_*`; one MPS run under the milestone ledger (`require_launch("E2")`) and the
  committed stop rule; a CPU rehearsal first; result records write-once, committed only after
  Rafael writes "approved"; any automatic per-point commits listed in the plan in advance.

### Recall floor — the `e2_noise_floor_estimator` (NOISE-01, NOISE-02)
- **D-01 (what is measured):** two groups, kept SEPARATE: the full taught adapter (5 seeds) and M2
  (5 seeds). In each adapter, the 7 gated non-targets' A2 recall at K = 48, each with its
  denominator (27 questions = 14 core_taught + 13 core_held_out).
- **D-02 (pair statistic):** for each pair of seeds (i, j) of the SAME group, d(i, j) = the largest
  |recall difference| over the 7 slots. This is the statistic of v3.0's sampling floor (one pair,
  max over slots; `phase19_erasure.nontarget_noise_floor = max`).
- **D-03 (group floor):** the group's floor = the MEAN of d(i, j) over its 10 pairs. The published
  training floor, placed beside 0.148148, = the LARGER of the two group floors. The mean is
  labelled `kind: preference`: it keeps the "one pair" scale of the v3.0 number.
- **D-04 (always beside it):** the max and min of the 10 pairs, every pair's d(i, j), and per slot
  the range and the standard deviation across the 5 seeds.
- **D-05 (declared):** every A2 measurement is itself a sample, so the training floor INCLUDES
  sampling noise. Stated in the prereg entry and the report.

### Train fresh; old adapters only as checks
- **D-06:** train all 10 (full and M2 at each of the 5 seeds) with today's code and recipe. No old
  adapter enters the set.
- **D-07 (determinism check, no MPS cost):** compare the sha256 of the new M2@1337 with the committed
  `22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57`
  (`results/phase19_arm_retrain.json::adapter_sha256`). IF the recipe of Phase 19's dialogue-floor
  adapters (`phase19_erase_dialogue_floor_seed1337/2024`, sha256 `f12ab4c3…` / `3fd5aba4…`) is
  identical to the new full adapter's, compare those too. If not bit-identical, report the
  difference in the A2 counts as "ruído de re-execução com a mesma semente"
  (same-seed re-run noise). Descriptive. (For M2@1337, the A2 counts are already committed in
  `phase19_arm_retrain.json`. The dialogue-floor adapters have NO A2 record, so for them only the
  sha256 comparison is free; anything beyond that is priced under D-14.)
- **D-08 (v3.0 'taught' limitation):** v3.0's taught side of the M1 x M2 comparison is
  `checkpoints/persona_adapter.pt` (sha256 `226f2ae5…`, Phase 18 record), NOT a seed-1337 retrain
  under the Phase 19 recipe. Record in the Phase 40 record, field by field, how its recipe differs
  from the retrain's (steps, data, replay, code). This is a v3.0 limitation and goes to the
  milestone report. Compare persona_adapter.pt with the new full@1337, descriptively.

### `gap_noise_floor` (feeds Phase 41's condition-(c) band, so it is a CRITERION)
- **D-09:** measure the adapter-ON dialogue PPL (`masked_perplexity`, the Phase 19 dialogue-floor
  metric) on the 5 full adapters. Adapter-OFF is the committed value 4.573349214207799
  (`results/phase19_noise_floors.json`, `adapter_off_identical_across_seeds: true`), checked, not
  retyped. gap = on − off.
- **D-10 (estimator):** `gap_noise_floor` = the MEAN of |gap difference| over the 10 pairs, built
  as in D-02/D-03. The max is shown beside it. `kind: preference`, same reason (one-pair scale; v3.0
  and v4.0 used one pair, |dPPL| = 0.005214448168350039).
- **D-11 (not in the E2 budget):** the dialogue-PPL measurement is not priced in the E2 formula.
  Bring its price BEFORE the run, for approval in the D-09 format (the 38-D-21/D-22 pattern: the
  cap/hours approval under 36-D-09 quoted verbatim, with the new projection and total written into
  `scripts/phase40_prereg.py` and into every Phase 40 record). Also bring the price of measuring it
  on the 5 M2 adapters (descriptive).

### M1 x M2 re-reading
- **D-12:** publish the floor beside 0.148148 without touching v3.0's (b) margin, AND re-read v3.0's
  `delta_taught_to_m2` per slot beside the distribution of full x M2 differences with no erasure at
  all (5 x 5 = 25 pairs, the 5 same-seed pairs marked). Descriptive, never a verdict.

### Addition: target rank across the 5 M2 seeds (descriptive, scoring only, CONDITIONAL)
- **D-13:** in each of the 5 M2 adapters:
  - the anchor rank of zorp (`pet_name`) against Phase 38's minted list at the nested sizes
    8, 32, 128, 512 (38-D-08 prefixes);
  - n1 of the target under the question context (Phase 39's R_q), on the committed set and on the
    minted set at |R| = 8.
  Purpose: read the two Phase 38/39 signals (rank 16 at k78 vs 32 for M2 at |R| = 512; n1 5/27 at
  k78 vs 0/27 for M2 at |R| = 8) against the retrain's seed-to-seed variation.
- **D-14:** bring its price and the unit cap it needs. It is NOT included without Rafael's
  "approved".

### Run order and where the estimator text lives (Rafael's follow-up)
- **D-15 (run order):** per seed, in `seed_list()` order (1337, 2024, 1338, 2025, 1339). For each
  seed: train the full adapter, train M2, and run both A2 passes before moving to the next seed.
  If the stop rule fires mid-run, what exists is whole seeds, and the two Phase 41 uses (1337,
  2024) are ready first. A stop in the middle of a seed DROPS that seed from the estimator. This is
  declared in the prereg before any record. (The dialogue-PPL readings of D-09, if approved, and the
  D-13 scoring, if approved, are placed in the per-seed unit by the planner unless that changes the
  "whole seeds" property; state where.)
- **D-16 (estimator home) — PATH 1 HOLDS:** both estimators (recall floor, D-01..D-05, and
  `gap_noise_floor`, D-09..D-10) go in the SAME fill of the `e2_noise_floor_estimator` slot, as one
  four-field entry whose `value` is a mapping holding both, so the gap criterion is frozen by the
  same mechanism. Measured, not inferred: `_rule_e2_noise_floor_estimator` only runs
  `_prove_entry` (exactly the four D-14 fields, kind in KINDS, non-empty derivation/source; the
  value is checked for the forbidden phrase only when it is a str), and a dry `fill()` on CPU (no
  write) accepted a mapping value with both estimators and returned it frozen (mappingproxy). The
  slot's `input_records = ()` with owner 40, so Phase 35's ordering rule (a) already forces its
  fill file before every `results/phase40_*` record. Path 2 (the gap estimator in
  `phase40_prereg.py`) is NOT needed.

### Planning items (Rafael wants to SEE both before approving any training)
- **P-1 (dialogue-PPL price):** no committed unit price for `masked_perplexity` exists:
  `results/phase36_budget.json::unit_prices` has none, and `results/phase19_dialogue_floor.json` has
  no wall-clock field. The plan derives one from a committed record that carries timing or proposes
  a small timing step, and states which.
- **P-2 (recipe identity):** whether the Phase 19 dialogue-floor adapters' recipe (`arm_spec`
  "real", `n_facts` 10, `replay_ratio` 1.0, `second_person` false, prefix `phase19`) is identical to
  the new full adapter's. Research settles it before D-07's comparison is planned.

### Addendum (2026-10-05, Rafael, plan-phase 40) — D-07 and D-08 amended
Research measured the D-08 premise false (40-RESEARCH.md Pitfalls 1-2); the orchestrator re-measured
it before asking (`torch.equal` on all 72 tensors + identical non-tensor metadata). Rafael ruled
"Opção 1 (correção)" with three adjustments. These SUPERSEDE the D-07/D-08 text above where they
differ:
- **D-08 (amended):** `persona_adapter.pt` and `phase19_erase_dialogue_floor_seed1337_adapter.pt` are
  the same adapter (72 equal tensors; the file sha256 differs only by the file name `torch.save`
  writes into the zip). The milestone report records this as a CORRECTION of the scout note in
  `<specifics>`, NOT as a v3.0 limitation.
- **D-08b (residual):** the residual difference — v3.0's taught-side A2 counts came from Phase 18's
  `run_arm` draws (`phase19_run.py:1721`, `PHASE18_ARM_RECORD_PATH`), not from `run_erasure_arm` — is
  reported with its MEASURED size against the new full@1337. It is named a v3.0 limitation ONLY if
  the counts differ on identical weights. If the new full@1337 does not reproduce the weights bit for
  bit, the report says the two effects (weights vs scoring path) cannot be separated.
- **D-07 (amended; Rafael's reply labels it "D-02 (checagem de determinismo)" — the determinism check
  is D-07, D-02 is the pair statistic and is unchanged):** every comparison between a new adapter
  and a committed one is made tensor by tensor (`torch.equal` on every tensor, plus the metadata),
  NEVER by the file sha256. Applies to M2@1337 vs `phase19_erase_reference_adapter.pt` and to
  full@1337 vs `persona_adapter.pt`. (Phase 41's ERASE-05 reuse-by-SHA-256 hashes the SAME file at
  its original path, so it is unaffected.)

### Claude's Discretion
- D-04's per-slot standard deviation: sample SD (`statistics.stdev`), population SD shown beside it.
- The A2 arm label for the full adapter: `"retrain"` (keeps the Phase 18 parity assertion); the group
  (full / M2) lives in Phase 40's own fields.
- The ~10 per-arm A2 records are committed after Rafael's "approved", like every result record.
- Record field layout of `results/phase40_noise_floor.json` beyond the contract key
  `gap_noise_floor` (finite >= 0), and how per-seed records (if any) are split; the per-seed records
  must keep the "whole seed" unit of D-15.
- Driver/rehearsal mechanics, following the Phases 37-39 pattern.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` — NOISE-01, NOISE-02 (v6.0 block); ERASE-05, ERASE-09, ERASE-10
  (Phase 41 consumes this phase's adapters and `gap_noise_floor`)
- `.planning/ROADMAP.md` §"Phase 40: M2 Seed Noise Floor" and the v6.0 ordering/approvals paragraphs

### Pre-registration and budget (closed inputs)
- `scripts/phase35_prereg.py` — `seed_list()`, `e1_teaching_seeds()`, slots `e2_S` and
  `e2_noise_floor_estimator`, the Phase-40 noise-floor contract (module docstring),
  `_rule_e1_condition_c_band_inputs` (how Phase 41 reads `gap_noise_floor`), `ENTRIES["e2_min_seeds"]`
- `.planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-CONTEXT.md` — D-05,
  D-06, D-14, D-15 + Addendum, D-16
- `results/phase36_budget.json` — `e2_seed_count`, `front_hours.E2`, `unit_caps.E2`, `unit_prices`,
  `formula.E2`
- `.planning/phases/36-mps-cost-probes-and-budget-commitment/36-CONTEXT.md` — D-08, D-09, D-11..D-13
  (ledger, stop line), Q6
- `results/phase36_probe_e2.json` — the M2 probe configuration (retrain arm, seed 1337, 200 steps,
  K 48, 216 questions)
- `scripts/phase36_budget.py`, `scripts/phase36_caps.py`, `scripts/phase36_ledger.py` — cap
  enforcement and `require_launch`

### v3.0 floors and the M1 x M2 comparison
- `results/phase19_noise_floors.json` — `nontarget_noise_floor` (0.148148, max over 7 slots,
  `margin_at_gate` 0.296296) and `dialogue_ppl_noise_floor` (0.005214, adapter_off 4.573349)
- `scripts/phase19_erasure.py` — `NONTARGET_NOISE_FLOOR_ESTIMATOR`, `nontarget_noise_floor`,
  `DIALOGUE_NOISE_FLOOR_ESTIMATOR`, `GATED_NONTARGET_SLOTS`, `RETRAIN_ARM`
- `scripts/phase19_run.py` (~1700-1760) — the M1 x M2 comparison (`delta_taught_to_m2`)
- `results/phase19_arm_retrain.json` — M2@1337 A2 record, `adapter_sha256` 22e66552…
- `results/phase19_dialogue_floor.json` — the dialogue-floor recipe and seeds
- `scripts/mitigation_gate.py` — `dialogue_gap_band` (D-01 logic, gap = on − off)
- `scripts/phase25_condition_c.py` — `gap_noise_floor()` and `DIALOGUE_FLOOR_RECIPE_MISMATCH` (v4.0
  imported the v3.0 one-pair floor)

### The D-13 addition and the D-09 approval format
- `.planning/phases/38-exposure-rank-at-larger-minted-sets/38-CONTEXT.md` — D-08 (nested sizes),
  D-21/D-22 (the D-09 approval format)
- `results/phase38_minting.json`, `results/phase38_rank.json`, `results/phase38_rank_report.md`
  (pet_name row: k78 16, M2 32 at |R| 512)
- `scripts/phase38_rank.py`, `scripts/phase39_ctx.py`, `results/phase39_ctx_report.md` (R_q n1:
  k78 5/27, M2 0/27)
- `.planning/phases/39-instrument-context-2-2/39-CONTEXT.md` — process pattern (D-21, D-27)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase35_prereg.fill("e2_S", ...)` and `fill("e2_noise_floor_estimator", estimator=...)`: the two
  Phase-40 slots; the precedent fill files are `scripts/phase38_prereg.py` and
  `scripts/phase39_prereg.py`.
- `phase19_erasure.nontarget_noise_floor` (the v3.0 max reduction), `_pooled_rows` in
  `phase19_run.py` (per-fact rows with per-tier denominators, recovering the 27 = 14 + 13 unit).
- The Phase 36 E2 probe path (`scripts/phase36_probe.py`), which already trains M2 at seed 1337 and
  runs the A2 pass on MPS.
- `phase38_rank.py` / `phase39_ctx.py` scoring functions for D-13.

### Established Patterns
- Phase-owned prereg + ancestry test before any record; write-once records; Rafael's "approved"
  before each result commit; LaunchAgent + heartbeat driver under the ledger; CPU rehearsal first.
- Thresholds as four-field entries {value, derivation, kind, source}; no proposer field.

### Integration Points
- `results/phase40_noise_floor.json::gap_noise_floor` → Phase 41 `e1_condition_c_band_inputs`.
- The seed-1337/2024 full and M2 adapters → Phase 41 (reused by SHA-256, ERASE-05).
- The floor → the v6.0 report (Phase 45), beside 0.148148.

</code_context>

<specifics>
## Specific Ideas

Premises in Rafael's reply, each measured on 2026-10-05 before being written here:
- The v3.0 sampling floor is one pair, max over the 7 slots: `nontarget_noise_floor = max` →
  0.14814814814814814 (= 4/27); `margin_at_gate` = 2 x that. ✓
- C(5,2) = 10 within-group pairs; 5 x 5 = 25 full x M2 pairs. ✓
- adapter-off 4.573349214207799 committed; `adapter_off_identical_across_seeds: true`. ✓
- M2@1337 sha256 22e66552… recorded in `phase19_arm_retrain.json` (and on disk as
  `checkpoints/phase19_erase_reference_adapter.pt`). ✓
- Phase 38 pet_name at |R| 512: k78 rank 16, M2 rank 32; Phase 39 R_q n1 at |R| 8: k78 5/27, M2 0/27;
  nested sizes 8/32/128/512; zorp = `pet_name` (`cand_dog_zorp`). ✓
- "D-09 format" = Phase 38 D-21/D-22. ✓
- Measured during scout: `persona_adapter.pt` (226f2ae5…) ≠ the Phase 19 dialogue-floor seed-1337
  adapter (f12ab4c3…); the dialogue-floor adapters have no A2 record.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (D-13 is an in-phase descriptive addition gated on
Rafael's "approved", not a deferral.)

</deferred>

---

*Phase: 40-m2-seed-noise-floor*
*Context gathered: 2026-10-05*
