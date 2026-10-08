# Phase 41: Erasure Across Facts, Orderings and Seeds (E1) - Research

**Researched:** 2026-10-07
**Domain:** pre-registration fill files + an MPS driver around the closed Phase 19 pin (M1 rank-1 ablation, A2 extraction, (a)/(b)/(c) gate), from-scratch PyTorch
**Confidence:** HIGH on contracts and paths (read from code at HEAD 3a96092); MEDIUM on MPS cost/determinism assumptions (CPU-measured only)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (copied verbatim from 41-CONTEXT.md `<decisions>`; includes Claude's Discretion)

## Implementation Decisions

### Carried forward (locked before this discussion — do not re-open)
- Targets by rule from `TARGET_RANKING` (35 D-03), teaching seeds `seed_list()[:2]` = (1337, 2024)
  (35 D-05), condition (b) margin `margin_at_gate` = 0.2962962962962963 = 8/27, sampling noise and
  not training noise (35 D-16). Phase 40's training-seed floor enters only the M1 × M2 comparison.
- `e1_stop` / `NOT_REACHED` semantics, K = CURVE_K 16 read, K = FULL_FIDELITY_K 48 confirmation,
  rank never in the stopping rule, rank recorded at every checkpoint (ERASE-07, coded in
  `phase35_prereg.py:1060-1120`).
- Defect E is routed through `phase37_routes.select_target_prefix` (|R| = 8; the pin
  `phase19_erasure.py` stays byte-unchanged, ERASE-08).
- Adapters reused by SHA-256, never retrained (ERASE-05): `results/phase40_noise_floor.json::phase41_adapters`.
  1337 full is `5240a564…` and M2 `991a522b…`; 2024 full is `1a898c8d…` and M2 `9e04fa73…`. Checked
  with `shasum` on 2026-10-07: all four match.
- Budget (`results/phase36_budget.json`): `front_hours.E1` = 52.779745537787676 h, with unit caps
  of 16 cells, 5 checkpoints per cell, 1 K = 48 confirmation per cell and 4 calibrations. Unit
  prices: ordering 417.56 s per cell, K16 1437.67 s, K48 3989.45 s, calibration 1120.33 s. The
  calibration price already includes one adapter training (`e2_train_m2_high` 76.11 s) plus the
  calibration curve plus the `cal-erased` arm.

### Alternative ordering (`e1_alternative_ordering`, ERASE-04)
- **D-01:** The alternative ordering is a **first-order Taylor (gradient) ordering re-ranked at
  every grid checkpoint**:
  1. At the intact adapter and again at each checkpoint, compute ∂NLL/∂s_j on the adapter as
     ablated so far. Here s_j is a scale on rank-1 component j (only components not yet ablated).
  2. Rank by the predicted rise of the NLL on removal, **−∂NLL/∂s_j at s_j = 1**, largest first.
     Never rank by the absolute value: a component whose removal lowers the target NLL goes to the
     back, as in the current ordering. Ties break by address (layer, projection, j), as in
     `select_ablation_prefix`.
  3. Ablate the leading components up to the next checkpoint.
- **D-02:** The NLL is the one the current ordering uses: same value, same context, same scoring
  function (`phase19_erasure.value_span_nll_mean`). The only differences between the two orderings
  are the estimator and the re-ranking at checkpoints.
- **D-03:** The ordering stays a rule over the fact being erased. A calibration therefore runs it
  on `select_calibration_fact()`, and the (ordering, seed) keying of the floors holds unchanged.
  Verified: `_rule_e1_condition_a_floors` reads only `ordering/seed/family/corpus/draws`, and
  nothing forbids a grid-dependent ordering. Because the grid now defines the alternative ordering
  itself, the grid must be filled before any calibration. The Phase 35 fill-order leg (a) already
  guarantees this: `e1_checkpoint_grid` consumes only `results/phase36_budget.json`, so its fill
  file precedes every `results/phase41_*` record (`tests/test_phase35_prereg.py:2434`).
  - In a calibration (rank stop, k may exceed 128), prefixes past the last checkpoint use the last
    gradient ranking. Phase 19's calibration k was 187.
- **D-04:** The ordering actually applied is **written into every cell and calibration record**.
  MPS backward may not be bitwise deterministic, so reproduction uses the recorded ordering.
- **D-05:** **Price and fallback.** The 417.56 s per-cell line is the whole Phase 19 collateral-curve
  run (`results/phase19_collateral_curve.json` wall_clock_min 6.96). That is 288 single-ablation
  NLLs plus the rank scan to k = 78 plus the curve, so one value NLL costs at most ~1.44 s.
  - The adaptive ordering needs at most 5 gradients per cell (the intact adapter plus each
    checkpoint before the last). That fits unless backward costs more than ~57× a forward pass.
  - The CPU rehearsal measures the backward/forward ratio, and the plan asserts that a cell's
    ordering cost fits in 417.56 s.
  - **Written fallback (no new decision needed):** if that assertion fails in the CPU rehearsal,
    the alternative ordering becomes the **static** gradient ordering (computed once on the intact
    adapter), with the same correlation reading (D-06). The same fallback applies if a calibration
    turned out unable to take a grid-dependent ordering.
- **D-06 (descriptive, declared in advance):** the Spearman rank correlation, on the calibration
  fact and per seed, between the gradient ordering on the intact adapter and the current ordering.
  No verdict.

### Checkpoint grid (`e1_checkpoint_grid`, ERASE-07)
- **D-07:** Grid **(16, 32, 48, 64, 128)**, one grid for all 16 cells. These are also the
  re-ranking points of D-01.
  - Justification to record: powers of 2 from 16 to 128, plus 48, which splits (32, 64]. That is
    the interval where the committed `pet_name` zero lies: k* = 64 in
    `results/erasure_kstar_summary.json` (A2, K = 48, seed 1337, current ordering), and Phase 39's
    committed A2 read 2/27 at k = 32 and 0/27 at k = 64 (`results/phase39_ctx_report.md:151-183`).
  - Using that prior reading to place 48 is declared as a **design input**; no threshold depends
    on it.
- **D-08:** No checkpoint at 288. Fully removing the adapter gives the base model, the same in all
  16 cells and already measured (the adapter_off record, 0/27 for all eight facts). The report cites
  it as the end point without new measurement.
- **D-09:** A cell with no zero confirmed by 128 is `NOT_REACHED`, as Phase 35 defines it. It is
  published with the A2 count and rank at every checkpoint and the sentence "não apagado com 128 de
  288 componentes removidos". It never counts as PASS or as FAIL.

### Calibration keying (`e1_condition_a_floors`, ERASE-06)
- **D-10:** Floors are keyed by **(target, ordering, seed)** with one calibration per (ordering,
  seed), 4 in all. A **fresh calibration adapter is trained at 1337 and at 2024 with the same
  driver** (`phase19_erasure._cmd_cal_train` route, arm `erase_calibration`). That puts calibration
  and target adapters in the same training generation at each seed. Phase 19's
  `checkpoints/phase19_erase_calibration_adapter.pt` is **never** an input of the floors.
- **D-11 (prediction, recorded before the run, Phase 40 D-07 pattern):** the new 1337 calibration
  adapter is identical, tensor for tensor (`torch.equal`; SHA-256 depends on the file name), to
  `checkpoints/phase19_erase_calibration_adapter.pt`. A mismatch is a reported finding, not a
  failure, and the floors still come from the new adapters.
  - Context measured 2026-10-07: Phase 40's full 1337 adapter is tensor-identical to
    `checkpoints/persona_adapter.pt` (72/72 tensors `torch.equal`).
- **D-12 (descriptive):** the calibration rate and the floor (with its branch) of each (ordering,
  seed) are published side by side, to show how far the floor moves between seeds.

### Condition (c) and the PASS reading (`e1_condition_c_band_inputs`, ERASE-09/10)
- **D-13:** `control_gap` is **re-measured** on the intact full adapter in each (seed, ordering)
  run, before any ablation, and written to `results/phase41_band_inputs_*.json`. It must equal
  `results/phase40_noise_floor.json::per_seed[seed].full.dialogue_gap.gap` exactly (1337:
  1.2420966625043919; 2024: 1.2368822143360418; Phase 40 measured pre = post bit for bit on MPS).
  A difference stops the run for Rafael's decision; it is never corrected.
  - The resulting bands, with `gap_noise_floor` 0.08406970366097503: 1337 → [0.6210, 1.4102];
    2024 → [0.6184, 1.4050].
- **D-14:** Condition (c) is **the dialogue band only**, as ERASE-09 states. Retention carries no
  verdict. Reasons to record:
  1. The v4.0 retention cap (3.9085032379884783 = 3.891140 + 2 × 0.008681618994239138,
     `results/phase20_retention_floor.json::cap`) is anchored on adapter-off. Phase 40's intact full
     adapters (4.156–4.332) and its five M2 (4.207–4.433) sit above it (`results/phase40_a2_*_seed*.json::retention_ppl`),
     while v3.0's ablated arm (3.6709, `results/phase19_arm_erased.json`) sits below. The leg would
     fail an erasure that preserves the adapter and pass one that destroys it.
  2. This is the same defect Phase 19's report published for the dialogue leg, which ERASE-09
     corrects with the band anchored on the adapted model.
  3. This is a declared change from the (c) of v3.0 and v4.0, not an omission.
  - **Descriptive, declared in advance:**
    - `retention_ppl` at each cell's stop, beside the intact adapter of the same seed and, for
      `pet_name`, the M2 of the same seed;
    - a column "passaria no teto do v4.0: sim/não";
    - the retention spread across Phase 40's five seeds, beside the two-seed floor 0.00868.
- **D-15:** Each cell (target, ordering, seed) carries its own verdict (SUCCESS / FAILURE /
  INCONCLUSIVE, or NOT_REACHED). It also carries **every condition that failed**, (a), (b) and/or
  (c). For (b), it names each non-target fact beyond the margin.
- **D-16:** Each (target, ordering) pair gets exactly one of three labels:
  - **PASS:** SUCCESS at both seeds.
  - **FAILURE replicada:** FAILURE at both seeds.
  - **Não replicado:** any other combination, published with each seed's verdict in full (e.g.
    "SUCCESS na 1337, NOT_REACHED na 2024"). It never reads as the pair's PASS or FAILURE.
- **D-17:** A pre-registered summary line, **with no threshold**: of the 8 pairs, how many carry
  each of the three labels. INCONCLUSIVE and NOT_REACHED are counted separately inside "não
  replicado". There is no aggregation across targets or orderings beyond that count, and the full
  4 × 2 × 2 table is published.

### M1 × M2 and non-target damage (ERASE-10, 35 D-16)
- **D-18:** The M1 × M2 comparison runs **only in the 4 `pet_name` cells**, is descriptive and has
  no verdict. For the other three targets the report states "sem M2, comparação não feita".
  - Per non-target fact (denominator 27 each): full intact, M1 at the stop, and M2 of the same seed,
    with M1 − full and M2 − full.
  - Beside them, the min–max range (in /27) across Phase 40's five M2 seeds, read from
    `results/phase40_noise_floor.json::recall_floor.m2.per_slot[slot].counts`, and whether M1's rate
    at the stop falls inside or outside that range. This label is declared in advance and costs
    nothing (a read of a committed record).
  - Declared limit: M1 exists at two seeds and the range comes from five retrains, so "fora da
    faixa" is not a statistical test.
  - Context: at 2024 the retrain itself departs from full by 14/27 on `hometown` (22 → 8). At 1337
    the largest departure is 7/27 on `house_number`.
- **D-19:** A non-target slot gets the label **"varia entre seeds"** when its largest amplitude
  across Phase 40's two groups (full and M2, five seeds each; `recall_floor.{full,m2}.per_slot[slot].range`)
  is ≥ the (b) margin 8/27. This is the same convention as the published floor, which takes the
  larger of the two groups.
  - On the committed record this marks `hometown` (17/27) and `birth_year` (13/27), not
    `house_number` (7/27). The rule computes the list, so nothing is typed.
  - The min–max ranges of both groups are published beside each Δ.
  - **Descriptive, per cell:** how many non-targets went beyond the margin among the labelled slots
    and among the unlabelled ones, and whether (b) would fail on the unlabelled slots alone
    (yes/no).
  - The label never discounts a Δ and never enters a verdict: gate (b) still reads all seven
    non-targets against 8/27.
- **D-20:** The **whole D-13 block** is published at the stop of the 4 `pet_name` cells, using
  Phase 40 D-13's scoring (`phase38_rank` / `phase39_ctx`; 925 NLLs per cell, ~9 s each, ~36 s
  total, inside the slack and with no new budget line).
  - It covers the anchor rank at sizes 8/32/128/512 and R_q n1 on the committed and minted lists.
  - Each reading sits beside the five Phase 40 M2 range (anchor at 512: 15–41; R_q n1: 0–1/27
    committed, 9–12/27 minted; `d13.blocks`) with an "inside/outside" label. Descriptive, no
    verdict.
- **D-21 (prediction, recorded before the run, Phase 40 pattern; a disagreement is a finding, not
  a failure):** at the stop, R_q falls outside the M2 range on both lists and the anchor at 512
  falls inside, in all 4 cells.
  - The (1337, current ordering) cell runs on the adapter of Phase 39 and the k* extension. It
    repeats a known reading only if it stops at 64 (Phase 39 committed R_q n1 11/27 at k = 64); a
    stop at 48 is a new prefix. The other three cells are the test.
  - Declared limits: |R| = 8, four cells, two seeds, a comparison range from five retrains; "fora
    da faixa" is not a statistical test.

### Execution order, pause and operations
- **D-22:** The 4 calibrations and the 4 band-input records run first, because the floors and band
  slots are each filled once and need every (ordering, seed) present. Then **all 8 cells of the
  current ordering run, pair by pair (1337 then 2024 for each target, in `TARGET_RANKING` order),
  before the 8 cells of the alternative ordering**, in the same pair order.
- **D-23:** **E1 pauses at its own share**, `front_hours.E1` = 52.78 h, for Rafael's decision; the
  global 90 h stop line stays above it.
  - The pause is checked **before every cell**.
  - The pause notice gives the hours spent on E1 (including those lost to crashes, as in E2), the
    completed pairs, any half-done pair, and what remains for E3 (6.62 h), E4 (4.81 h) and the
    90 h line.
  - Whether to complete a half-done pair is Rafael's call at that moment.
- **D-24:** **The crash rule is Phase 40's R-3 b, per cell.** A new attempt needs Rafael's
  "approved" and a cause note, and uses the same seed and the same HEAD (or the change is
  declared). Partial outputs are kept and listed. Adapters and orderings are compared between
  attempts (`torch.equal`). The rule covers a crash only (no end line), never redoing a finished
  cell.
- **D-25:** **Operations** (Phase 40 lessons):
  - The waiter follows the driver PID, never the log. Logs append across launches, so a grep can
    fire on an old run.
  - Bootout only after two checks that the process has exited.
  - The plan provides per-block relaunch without changing HEAD (like Phase 40's pending seeds).
  - Each launch gate records the memory state, and the other project's collector (the system
    LaunchDaemon named in 40-09-SUMMARY) stays stopped until the run ends.

### Approvals
- Result records are write-once and committed only after Rafael writes "approved" (ERASE-06/10 SC5).
  The plan lists in advance any automatic per-point commits; outside that list, nothing is
  committed without his "approved".

### Claude's Discretion
- File split of the Phase 41 fill files (`scripts/phase41_*prereg.py`) and the driver, subject to
  the Phase 35 fill-order rules.
- Exact field names of the new descriptive blocks in the records and report.

### Deferred Ideas (OUT OF SCOPE) (copied verbatim from 41-CONTEXT.md `<deferred>`)

## Deferred Ideas

- **M2 for the other three targets** (`cat_name`, `street`, `sibling_name`) × 2 seeds. That is 6
  retrains plus their A2 passes, about 4.7 h MPS (6 × (76.11 s + 2762.26 s)), outside ERASE-05 and
  the Phase 36 budget. Consider it after E1, E3 and E4, only if budget remains.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (REQUIREMENTS.md:737-744) | Research Support |
|----|-------------|------------------|
| ERASE-03 | Targets = the four 13/13 facts of `TARGET_RANKING`, by a committed rule | `phase35_prereg.e1_targets()` (:382) already returns `('pet_name','cat_name','street','sibling_name')` [VERIFIED: ran in .venv]. Never type the names; iterate `e1_targets()`. |
| ERASE-04 | Two pre-registered orderings | Current = `phase37_routes.select_target_prefix` (:154) → `pin.select_ablation_prefix` `ordered`; alternative = Taylor gradient (D-01), filled once via `fill("e1_alternative_ordering", ordering=<entry>)` (:1415). Gradient hook: §Pattern 2. |
| ERASE-05 | Seeds from `seed_list`; Phase 40 pet_name full + M2 adapters reused by SHA-256 | `e1_teaching_seeds()` (:371) = `(1337, 2024)` [VERIFIED]. Paths/digests from `results/phase40_noise_floor.json::phase41_adapters` (`checkpoints/phase40_e2_{full,m2}_seed{1337,2024}_adapter.pt`). Check in driver preflight, not in a host-gated test (§Pitfall 12). |
| ERASE-06 | (a) floor derived before measurement; calibration per (ordering, seed) | `_rule_e1_condition_a_floors` (:1261) computes floors from `results/phase41_calibration_*.json` + `results/phase19_calibration_corpus.json`; 4 calibration records; fill-order §Pattern 1. |
| ERASE-07 | Rank never in stop rule; recorded at every checkpoint; grid read K=16, confirm K=48 | `fill("e1_checkpoint_grid", checkpoints=(16,32,48,64,128), ...)` (:1211) + `phase35_prereg.e1_stop` (:1075). K=16 read = bit-identical prefix of the K=48 run (phase23_run.py:4191-4197 precedent). |
| ERASE-08 | Defect E via wrapper importing the pin; pin byte-unchanged + test | `phase37_routes.select_target_prefix`; existing proof `tests/test_phase37_routes.py:317 test_pin_and_gate_are_byte_unchanged` (anchor `3ba3e2c`, probe digest). Phase 41 adds its own leg. |
| ERASE-09 | (c) = bilateral dialogue band on adapted model, D-01 imported from `mitigation_gate` | `fill("e1_condition_c_band_inputs", ...)` (:1700) → `DIALOGUE_GAP_BAND` (= `mitigation_gate.dialogue_gap_band`, :344 / mitigation_gate.py:526). |
| ERASE-10 | Per-non-target damage with own denominator; no PASS without second seed | Per-target non-target set (NOT the pin's `GATED_NONTARGET_SLOTS`, §Pitfall 4); D-16 pair labels as a pure function in phase41_prereg. |
</phase_requirements>

## Summary

Phase 41 is mostly wiring, not new ML. Every hard part already exists. The slot rules live in `scripts/phase35_prereg.py`. The current ordering is `phase37_routes.select_target_prefix`. The A2 pass is `pin.run_erasure_arm`. The K=16 prefix read follows `phase23_run.py:4491`'s draw loop shape. The band is `mitigation_gate.dialogue_gap_band`, the D-13 block is `phase40_noise.d13_scores`, and the ledger, crash and launch skeleton is `scripts/phase40_noise.py`. The new code is:
- the Taylor gradient ordering;
- a rank-stop scan for the alternative ordering in calibration;
- a K=16 A2 reader;
- the per-cell loop over `e1_stop`;
- a generic per-target (a)/(b)/(c) verdict;
- the pair labels;
- an E1-share pause.

The fill order is non-negotiable and already pinned by a planted green test (`tests/test_phase35_prereg.py:2583-2593`, case `g41`). It runs in this order:
1. `scripts/phase41_prereg.py` fills `e1_checkpoint_grid`, `e1_alternative_ordering` **and `e1_condition_b_margin`**.
2. Then `results/phase41_calibration_*.json`.
3. Then `results/phase41_band_inputs_*.json`.
4. Then `scripts/phase41_floors_prereg.py` fills `e1_condition_a_floors` **and** `e1_condition_c_band_inputs` in ONE file.
5. Then every other `results/phase41_*`.

CONTEXT's "e1_condition_b_margin is already locked in the core" is true of its *value*, but it is still a Phase-41-owned slot. If no Phase 41 file ever calls `fill("e1_condition_b_margin")`, leg (c) goes red the moment a cell record is tracked.

I measured the gradient hook on CPU in this session. The value NLL computed with grad enabled equals `pin.value_span_nll_mean` bit for bit (0.13363315165042877, both paths). The ratio of forward+backward to forward is 4.33×, against D-05's 57× break-even. The Taylor −∂NLL/∂s_j tracks the actual single-ablation rise for the top components (0.0269 vs 0.0321, 0.0228 vs 0.0276) [VERIFIED: scratch probe, persona_adapter.pt, CPU]. `span_nll_from_ids` wraps its forward in `torch.no_grad()` (phase18_extraction.py:1084), so the gradient needs a 10-line grad-enabled twin of that forward. Neither the pin nor phase18 is edited.

**Primary recommendation:** mirror Phase 38's two-fill-file pattern (`phase38_prereg.py` + `phase38_sizes_prereg.py`) and Phase 40's driver skeleton (`phase40_noise.py`). Run two stages under one `run` command: prep (4 calibrations + 4 band inputs), then Rafael's approved, commits and the floors fill file, then the cells. Resolve every path from module constants.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Slot fills (grid, alt ordering, b-margin) + pure functions (gradient-order rule text, verdict combiner, pair labels, D-19 labels, Spearman, pause arithmetic, R-3 b ledger readers) | `scripts/phase41_prereg.py` (fill file 1, frozen before first phase41 record) | tests/test_phase41_prereg.py | Leg (a): every commit of this file precedes every `results/phase41_*`; pure functions must be written before the first calibration record, as Phase 40 did with its estimators (40-03). |
| Floors + band fills | `scripts/phase41_floors_prereg.py` (fill file 2) | — | Both slots consume in-phase inputs; ONE file so its exemption covers both input patterns. |
| MPS work: calibration training, orderings, K16/K48 reads, band re-measure, D-13 | driver `scripts/phase41_erasure.py` (name must NOT end in `prereg.py`) | `phase37_routes`, `phase19_erasure` (pin), `phase40_noise.d13_scores` | One ledger attempt per unit under `require_launch("E1")`. |
| Verdicts, labels, report | CPU `emit` / `report` subcommands of the driver, reading committed records through the fills | `scripts/_addendum.py` for any post-hoc continuation | Phase 40 emit/report pattern. |
| Budget/pause | `phase36_ledger.spent`/`require_launch` + a Phase 41 E1-share check | `phase36_caps.check_unit_caps("E1", ...)` | D-23 pause at 52.78 h is NOT one of the ledger's stops (a/b/c). |

## Standard Stack

No new packages. Python 3.11.15, torch 2.7.1 in `.venv` [VERIFIED: `.venv/bin/python -c ...`]. Stdlib: `statistics`, `json`, `fnmatch`, `hashlib`.

| Reused module | Symbols | Use |
|---|---|---|
| `phase35_prereg` | `fill`, `e1_stop`, `NOT_REACHED`, `e1_targets`, `e1_teaching_seeds`, `e1_condition_b_margin`, `CURVE_K`(16), `FULL_FIDELITY_K`(48), `MARGIN_K`(2), `DIALOGUE_GAP_BAND`, `a2_corpus_entries`, `SLOTS`, `V6_RESULT_PATHS` | slots and stop |
| `phase37_routes` | `select_target_prefix`, `route_a` (zero-result NLL flag), `route_c`-style pooling, `route_d` (retention scalar) | current ordering and defect routes |
| `phase19_erasure` (pin, never edited or monkeypatched) | `select_ablation_prefix`, `value_span_nll_mean`, `ablate_components`, `component_index`, `_COMPONENT_PREFIX`, `_rank_of`, `run_erasure_arm`, `dialogue_ppl_pair`, `select_calibration_fact`, `reference_set_for_calibration`, `per_fact_rows`, `lock_erasure_floor`, `floor_branch`, `CALIBRATION_CORPUS_PATH`, `RETRAIN_PREFIX` | mechanics |
| `phase18_extraction` | `_frame_preamble`, `ASSISTANT_ID`, `ADMISSIBLE_NLL_FRAME`('ans1'), `ADMISSIBLE_NLL_REDUCTION`('mean'), `measure_exposure`, `reference_set_for`, `_guarded_span`, `K` | gradient twin, rank, K16 reader |
| `phase19_run` | `_pooled_rows` | 27-question pooling |
| `phase40_prereg` | `a2_scope`, `a2_rows`, `slot_rows`, `committed_adapter_off`, `d13_block` | intact baselines and D-13 |
| `phase40_noise` | `adapter_identity` (torch.equal), `d13_scores`, the preflight/run/drop_attempt/declare_relaunch shapes | D-11, D-20, skeleton |
| `teach_persona` | `train_arm`, `arm_spec("cal_first_person_replay")`, `arm_outputs` | calibration adapters |
| `erasure_gate` | `wilson_upper_bound`, `VERDICTS` | (a) and verdict domain |
| `phase36_ledger` / `phase36_caps` / `phase25_run` | `require_launch`, `append`, `spent`, `read_ledger`, `open_runs`, `run_id`; `check_unit_caps`; `atomic_write_json`, `beat`, `start_heartbeat` | ops |

**Installation:** none (`pip install -e ".[cpu,dev,demo]"` already in the venv).

## Package Legitimacy Audit

No external package is installed by this phase, so slopcheck was not run. Packages removed: none. Packages flagged: none.

## Architecture Patterns

### System Architecture Diagram

```
Phase 40 committed inputs ──► preflight (sha256 of 4 adapters vs phase40_noise_floor.json::phase41_adapters,
  (noise_floor.json,           refuse_if_dirty, require_launch("E1"), check_unit_caps, E1-share pause)
   a2_{full,m2}_seed*.json)          │
                                     ▼
STAGE 1 (prep, 4 units: ordering x seed)                         [fill file 1 committed; grid + alt-ordering fixed]
  train calibration adapter per seed (teach_persona.train_arm, Phase 41 arm name)  ── D-11 torch.equal vs phase19 cal adapter
  ordering on select_calibration_fact():  greedy -> pin.select_ablation_prefix(twin |R|=6)
                                          gradient -> Taylor ordering re-ranked at grid points + rank-stop scan
  pin.run_erasure_arm("cal-erased", corpus=phase19_calibration_corpus, components=prefix, record_path=data/...)
  band: load intact full adapter -> pin.dialogue_ppl_pair -> control_gap == Phase 40 gap (else STOP)
      ──► results/phase41_calibration_<o>_seed<s>.json , results/phase41_band_inputs_<o>_seed<s>.json
                                     │  Rafael "approved" -> commit records -> commit phase41_floors_prereg.py
                                     ▼
STAGE 2 (16 cells, D-22 order: greedy pairs then gradient pairs; pause check before each cell)
  ordering (full 288, recorded) ─► for c in grid: ablate prefix[:c] ─► K16 A2 read (216 q) + rank
        └─ K16 target==0? ─► K48 pin.run_erasure_arm("erased", components=prefix[:c], record_path=results/phase41_...) 
              └─ K48 target==0 ─► STOP (e1_stop)  else next c ; none by 128 ─► NOT_REACHED
  at stop: (a) wilson(t,27) <= floor[(t,o,s)]; (b) |post-pre| per 7 non-targets <= 8/27, pre = Phase 40 A2 full of same seed;
           (c) lo <= gap <= hi with band[(s,o)]; pet_name cells: export M1 adapter -> d13_scores
      ──► results/phase41_cell_<t>_<o>_seed<s>.json
                                     ▼
CPU emit/report: per-cell verdicts + failed conditions, pair labels (D-16), D-17 counts, D-14/D-18/D-19/D-20 descriptives
```

### Recommended file layout

```
scripts/phase41_prereg.py          # fill file 1: E1_CHECKPOINT_GRID, E1_ALTERNATIVE_ORDERING, E1_CONDITION_B_MARGIN + pure fns + predictions (D-11, D-21)
scripts/phase41_floors_prereg.py   # fill file 2: E1_CONDITION_A_FLOORS, E1_CONDITION_C_BAND_INPUTS (+ check_unit_caps)
scripts/phase41_erasure.py         # driver: preflight / run / emit / report / drop_attempt / declare_relaunch
artifacts/com.personacore.phase41.e1.plist
tests/test_phase41_prereg.py       # FIRST-ADDED before any results/phase41_* (ancestry)
tests/test_phase41_floors_prereg.py
tests/test_phase41_erasure.py
```
Closest analogs: `scripts/phase38_prereg.py` + `scripts/phase38_sizes_prereg.py` with `tests/test_phase38_sizes_prereg.py:163-201` (input precedes file; file frozen before other records; test file first-added before scoring records); `scripts/phase40_prereg.py` + `tests/test_phase40_prereg.py:391-413` (frozen-before-records, this-test-file-first-added, RECORDS_AT_COMMIT at first commit, census of untested functions :889).

### Pattern 1: The fill contracts (exact)

Every fill is `<SLOT_UPPER> = phase35_prereg.fill("<slot>", ...)` at module level, after a plain `import phase35_prereg`. The census is at `tests/test_phase35_prereg.py:2166`: it refuses aliases, `from phase35_prereg import fill`, any `phase35_prereg._*` access, and any other module-level binding of a slot's upper-cased name. A derivation is the four-field entry `{value, derivation, kind ∈ ("derived","preference"), source}` with no `proposer` or `adopted_by` key and without the phrase "selected by THE USER, verbatim" (`_prove_entry`, :160). `_consume_inputs` (:910) requires:
- `input_records` is a non-empty tuple of repo-relative, existing, non-duplicate paths, each matching a declared pattern;
- every declared pattern is consumed;
- **every consumed path appears as a substring of `derivation["source"]`**.

| Slot | Call | Declared inputs (SLOTS :1791) | Derivation `value` must equal | Returns |
|---|---|---|---|---|
| `e1_checkpoint_grid` | `fill(..., checkpoints=(16,32,48,64,128), input_records=("results/phase36_budget.json",), derivation=...)` | `results/phase36_budget.json` | the **tuple** `(16,32,48,64,128)` (`==`; a list fails) | registered grid `{checkpoints, read_k:16, confirm_k:48, not_reached:"NOT_REACHED"}`; `e1_stop` accepts only this object (identity, `_is_filled`) |
| `e1_alternative_ordering` | `fill(..., ordering={value:<non-empty str>, derivation, kind, source})` | none | n/a (the entry IS the value) | deep-frozen entry |
| `e1_condition_b_margin` | `fill("e1_condition_b_margin")` (no kwargs) | `results/phase19_noise_floors.json` (read in the core) | n/a | `0.2962962962962963` |
| `e1_condition_a_floors` | `fill(..., floors={(t,o,s): None for t in e1_targets() for o in ORDERINGS for s in e1_teaching_seeds()}, input_records=(<4 calibration paths>, "results/phase19_calibration_corpus.json"), derivation=...)` | `results/phase41_calibration_*.json`, `results/phase19_calibration_corpus.json` | the keys, any order, each once (`_prove_keys_value`) | `(t,o,s) -> {floor, floor_branch, calibration_rate, calibration_successes, calibration_questions, calibration_record}` |
| `e1_condition_c_band_inputs` | `fill(..., band_inputs={(s,o): None ...}, input_records=("results/phase40_noise_floor.json", <4 band paths>), derivation=...)` | `results/phase40_noise_floor.json`, `results/phase41_band_inputs_*.json` | the keys | `(s,o) -> (lo, hi)` |

Record contracts the rules read:
- **Calibration record** (`results/phase41_calibration_*.json`): carries `ordering` (str), `seed` (1337|2024), `family` = "A2", `corpus` = "results/phase19_calibration_corpus.json" (repo-relative; it must equal a consumed input), and `draws` (THE ARM'S OWN draws). It has **NO `target` key**. There is exactly one record per (ordering, seed). The rule pools `per_fact_rows` over `phase18_extraction.CORPUS_TIERS` for `select_calibration_fact()` = `cal_person_varek` (slot `person_name`, corpus 23 questions = 14 + 9) [VERIFIED], then computes `lock_erasure_floor(rate)` and `floor_branch(rate)`. The questions per tier must equal the corpus's `question_counts`.
- **Band record** (`results/phase41_band_inputs_*.json`): carries `seed`, `ordering`, `control_gap` (finite). There is exactly one per (seed, ordering).
- Extra keys are allowed in both (`_prove_record` checks a superset). Put `provenance.run.{started_utc, finished_utc, device}` in every record that ends a ledger attempt: `phase36_ledger._closed_row` reads the clock from tracked records.

**Fill-order legs** (`tests/test_phase35_prereg.py:2475-2536`). The planted green sequence `g41` at :2583-2593 is the template:
- **(a)** Every commit of a fill file holding any slot without a `results/phase41_*` input (grid, alt ordering, b-margin) strictly precedes every tracked `results/phase41_*`. The floors file (both slots have in-phase inputs) precedes every phase41 record except `calibration_*` and `band_inputs_*`.
- **(b)** Every tracked declared input precedes the first commit of the file consuming it. So all 4 calibration records, all 4 band records, `phase19_calibration_corpus.json` and `phase40_noise_floor.json` are committed before `phase41_floors_prereg.py`.
- **(c)** Once a phase-41 record that is not a declared input is tracked, every Phase-41 slot is filled, b-margin included.
- The red cases `a41` and `b7_41` (:2651-2702) show the two mistakes: an alt ordering after a calibration, and an alt ordering riding in the floors file.
- Splitting floors and band into two files breaks (a). A file holding only floors would have to precede the band records.

### Pattern 2: Taylor gradient ordering without touching the pin (D-01/D-02)

The rank-1 component j of a projection contributes `scale * outer(B[:, j], A[j, :])` (pin :287-291). Scaling it by s_j is the same as replacing B with B·diag(s). Hence ∂NLL/∂s_j at s=1 equals Σ_i B[i,j]·∂NLL/∂B[i,j], which also equals Σ_k A[j,k]·∂NLL/∂A[j,k]. No model edit and no new parameter are needed. Rank by −g_j largest first, which means `sorted(remaining, key=lambda a: (g[a], a))`, the mirror of the pin's `(-contribution[a], a)` at :2487.

```python
# Source: measured in this session (scratch probe); ids built exactly as phase18_extraction.span_nll_from_ids (:1050-1107)
def taylor_scores(model, tok, device, *, slot, value):
    import torch, torch.nn.functional as F
    import phase14_factset as fs, phase18_extraction as x, phase19_erasure as pin
    pre = x._frame_preamble(fs.SLOT_FORMS[slot], x.ADMISSIBLE_NLL_FRAME)
    ctx = [x.ASSISTANT_ID] + list(tok.encode(pre)); ids = ctx + list(tok.encode(value))
    model.requires_grad_(False)
    mods = {lp: model.get_submodule(p) for lp, p in pin._COMPONENT_PREFIX.items()}
    for m in mods.values(): m.lora_B.requires_grad_(True); m.lora_B.grad = None
    xx = torch.tensor([ids[:-1]], device=device); y = torch.tensor([ids[1:]], device=device)
    span = torch.zeros_like(y, dtype=torch.bool); span[:, len(ctx) - 1:] = True
    logits, _ = model(xx)
    loss = F.cross_entropy(logits.view(-1, logits.size(-1)), y.masked_fill(~span, -100).reshape(-1),
                           reduction="mean", ignore_index=-100)  # == ADMISSIBLE_NLL_REDUCTION
    loss.backward()
    g = {(l, p, j): float(v) for (l, p), m in mods.items()
         for j, v in enumerate((m.lora_B.grad * m.lora_B.detach()).sum(dim=0))}
    for m in mods.values(): m.lora_B.grad = None; m.lora_B.requires_grad_(False)
    return float(loss), g   # assert float(loss) == pin.value_span_nll_mean(...) (D-02; CPU: bit-equal, measured)
```
- **Whole ordering computed up front.** Re-ranking at checkpoint c depends only on ablating the first c components of the ordering so far, never on an A2 reading. So the full 288-length ordering is a deterministic function of (adapter, fact, grid) and can be computed and written into the record (D-04) before any K16 read. Gradients are taken at intact, 16, 32, 48 and 64 (5, per D-05). The one at 128 is used only by calibrations, where k may exceed 128 (positions 129-288 then use the 128 ranking, D-03).
- **Hygiene.** Load each prefix through `load_adapter_weights(model, pin.ablate_components(artifact, prefix))`, snapshotting first with `ablate_components(artifact, [])` as the pin does at :2474. Ablated components have B[:,j]=0, so g=0; exclude them anyway (D-01 "only components not yet ablated"). Sampling and perplexity run under `@torch.no_grad()` (generation/core.py:24, perplexity.py:33/83/148), so leftover `requires_grad` cannot leak a graph. Still clear `.grad`.
- **Cost.** At most 5 forward+backward passes per cell. CPU measured forward 5.7 ms, forward+backward 24.8 ms (4.33×) [VERIFIED: CPU]. MPS is unmeasured, so the CPU rehearsal records the ratio and asserts the D-05 budget.

### Pattern 3: Current ordering per cell (ERASE-08)

`phase37_routes.select_target_prefix(model, tok, device, artifact, *, fact, dialogue_ppl)`. The signature is pinned by `tests/test_phase37_routes.py:300`. `fact` is the `phase14_factset.LOCKED_FACTS` member whose `.slot == target`, and `dialogue_ppl=lambda: pin.dialogue_ppl_pair(model, device, forbid)`. Take `out["ordered"]` (288) as the ordering. Record `k`, `stopped` and `curve` descriptively; the rank stop is NOT E1's stop. For (pet_name, greedy, 1337), `ordered[:78]` should equal `results/phase19_collateral_curve.json::ordered_prefix` (the adapter is tensor-identical, Phase 40 D-07), which makes a free descriptive determinism check.

### Pattern 4: The cell loop and `e1_stop`

`e1_stop` (:1075) cannot be called incrementally. It walks the whole grid and refuses a missing reading ("checkpoint X has no reading before the stop") unless a confirmed zero comes first. So:
1. The driver decides with the same predicate after each checkpoint: K16 target count == 0 → run the K48 confirmation; the K48 target count == 0 → stop. Otherwise go to the next checkpoint.
2. Build `readings = {c: {"curve_k_zero": bool, "full_fidelity_k_zero": bool | None}}` for every checkpoint read, with `None` exactly when `curve_k_zero` is False.
3. Call `phase35_prereg.e1_stop(grid=phase41_prereg.E1_CHECKPOINT_GRID, readings=readings)` once at the end. Prove its `stop` equals the driver's.
4. `{"stop": NOT_REACHED, "judged": False}` gets no (b)/(c) verdict.

Use `grid["read_k"]` / `grid["confirm_k"]`, never 16/48 literals. Target zero = pooled 27-question `n_answerable == 0` via `phase19_run._pooled_rows(draws, values, "A2", tiers)`.

### Pattern 5: The K=16 read (no pin edit)

`run_erasure_arm` hard-wires K = Phase 18's `config.k` = 48 (pin :2825, `n_samples=budget - 1` at :2893), so K16 needs its own loop. Copy `phase23_run.py:4491`'s shape:
- `recall.draw_all(model, tok, entry["prompt_ids"], device, forbid, entry["seed_index"] * x18.K, n_samples=CURVE_K - 1)` over `phase35_prereg.a2_corpus_entries()` (216 = 8 facts × 27) [VERIFIED].
- `recall.assert_no_value_in_prompt(...)` on `x18._guarded_span(entry)` **in the same undecorated function**, as the draw_all census at `tests/test_phase14_scoring.py:728` requires.
- `seed_everything(recall.SEED)` as the pin does.
- Draw dicts in the pin's schema, so `per_fact_rows` scores them.
- Rank at each checkpoint: `x18.measure_exposure(model, tok, device, slot=target, taught_value=value)` (|R|=8).

The stride `seed_index * 48` makes K16 the bit-identical prefix of the K48 run (phase23_run.py:4191-4197; phase36_probe "K = 16 by prefix stability").

### Pattern 6: K=48 confirmation and the stop record

`pin.run_erasure_arm("erased", device, adapter_path=<phase40 full adapter of the seed>, components=prefix[:c], record_path=root/"results/phase41_a2_<t>_<o>_seed<s>_k<ccc>.json")`. This is exactly erasure_kstar_run.py:139's shape. `"erased"` is parity-asserted (pin :2552). The Phase 37 AST gate refuses `run_erasure_arm` without `record_path`, so copy that gate. The record supplies post `per_fact` (draws), `exposure` (rank and the zero-NLL flag via `phase37_routes.route_a`), `dialogue_ppl` (the (c) gap), and `retention_ppl` (`route_d`, descriptive D-14).

### Pattern 7: Calibration per (ordering, seed) (D-10, D-03)

- **Train.** `tp.train_arm(<phase41 arm>, facts=..., family_ids=phase14_factset.TAUGHT_FAMILY_IDS, second_person=..., replay_ratio=..., seed=seed, prefix="phase41")` with `(facts, second_person, replay_ratio) = tp.arm_spec("cal_first_person_replay")`. That is `_cmd_cal_train`'s recipe (pin :3521-3536) with `seed=` added. **Never call `pin._cmd_cal_train`.** Its arm `erase_calibration` / prefix `phase19` resolve to `checkpoints/phase19_erase_calibration_adapter.pt` and `data/persona_erase_calibration_train.bin`, both of which exist [VERIFIED], and it takes no seed. Train one adapter per seed (2 trainings serve 4 calibrations). Move the run.csv out of `results/phase41_<arm>/` exactly as `phase40_noise.train_adapter` does (:312-345, move at :340), because that path matches `results/phase41_*`.
- **Greedy calibration.** `pin.select_ablation_prefix(model, tok, device, artifact, slot=fact.slot, value=fact.value, references=pin.reference_set_for_calibration(fact.slot, fact), collateral={...}, dialogue_ppl=...)`. These are `_selected_components`' exact args (:3558-3587); calling it directly keeps the full `ordered` for D-06. The applied prefix is `ordered[:k]` (Phase 19 k = 187).
- **Gradient calibration.** The same twin references; a rank-stop scan over the precomputed gradient ordering, `for p in 1..288: load prefix; rank,_ = pin._rank_of(...twin refs...); if rank != 1: k = p; break` (the pin's clause at :2489-2495). With no stop, k = 288.
- **Erase.** `pin.run_erasure_arm("cal-erased", device, corpus_path=pin.CALIBRATION_CORPUS_PATH, adapter_path=<new cal adapter>, components=prefix, record_path=<data/phase41_e1/...>)`. Then write the calibration record `{ordering, seed, family:"A2", corpus:"results/phase19_calibration_corpus.json", draws: arm["draws"], applied_ordering, k, adapter sha256, d11 identity, provenance}`. The raw arm record must not land under `results/phase41_*` (§Pitfall 2).
- **D-06 Spearman.** Both orderings are permutations of 288, so use the closed form ρ = 1 − 6Σd²/(n(n²−1)). Python 3.11's `statistics.correlation` has no `method=` [VERIFIED: signature `(x, y, /)`].

### Pattern 8: Verdict per cell (D-15) — do not call `erasure_gate.erasure_succeeded`

Its (c) is the v3.0 one-sided cap (erasure_gate.py:245-251), which ERASE-09 replaces, and the pin's (b) helpers are hard-wired to `TARGET_SLOT = "pet_name"` (pin :624, :1174, :1358). Compose in `phase41_prereg`:
- **INCONCLUSIVE** (gate's precedence, erasure_gate.py:219-229): target questions == 0, or target zero and `route_a(record)` False, or no non-target deltas.
- **(a)** `erasure_gate.wilson_upper_bound(n_answerable, 27) <= floors[(t,o,s)]["floor"]`.
- **(b)** For each of the 7 slots ≠ t (`phase18_extraction.CORE_SLOTS`), compare `abs(post_rate - pre_rate) <= margin`, with margin = `E1_CONDITION_B_MARGIN`. **pre = the intact full adapter of the SAME seed**: `results/phase40_a2_full_seed{s}.json` via `phase40_prereg.a2_rows/slot_rows`. Never the K48 record's `pre_erasure.per_fact`: the pin reads that from the Phase 18 record (seed-1337 adapter, pin :2936) and it would be wrong at 2024. At 1337 they coincide (d08b counts equal) [VERIFIED].
- **(c)** `lo <= on - off <= hi` from the K48 record's `dialogue_ppl`, with `(lo, hi) = E1_CONDITION_C_BAND_INPUTS[(s,o)]`.
- **Verdict** = SUCCESS iff (a)∧(b)∧(c), else FAILURE, listing every failed condition and each non-target beyond the margin.

### Anti-patterns
- Calling any `pin._cmd_*` or `phase19_run.report()` (Phase 37 AST gate, test_phase37_routes.py:388-395).
- Binding `E1_CHECKPOINT_GRID = phase41_prereg.E1_CHECKPOINT_GRID` at module level in the driver. The census flags any module-level binding of a slot name (Phase 40 test `test_driver_binds_no_slot_name`, test_phase40_noise.py:2989).
- Typing 16/48/8/27/0.296/band numbers. Read them from the fills and constants (AST gate like `test_no_derived_value_is_typed_in_the_prereg`, test_phase40_prereg.py:548).
- `os.replace` (allowed only in phase25_run/phase25_record, test_phase25_driver.py:340): use `phase25_run.atomic_write_json`.

## Don't Hand-Roll

| Problem | Don't build | Use |
|---|---|---|
| Current ordering / defect E | a 288-sweep | `phase37_routes.select_target_prefix` |
| Ablation | tensor zeroing | `pin.ablate_components` + `load_adapter_weights` (scale audit) |
| A2 K=48 pass | draw loop | `pin.run_erasure_arm(..., record_path=...)` |
| Per-fact counts / 27 pooling | scoring | `pin.per_fact_rows` + `phase19_run._pooled_rows` |
| Zero-NLL flag | key walk | `phase37_routes.route_a` (defect A) |
| Floors | rate→floor math | the `e1_condition_a_floors` fill (`lock_erasure_floor`/`floor_branch` inside) |
| Band | lo/hi | the `e1_condition_c_band_inputs` fill |
| Stop | stop logic of record | `phase35_prereg.e1_stop` |
| Adapter identity | sha256 compare | `phase40_noise.adapter_identity` (torch.save embeds the file name; memory `torch-save-sha-depends-on-filename`) |
| D-13 block | NLL scoring | `phase40_noise.d13_scores(adapter_path, a2_record_path, device, state)` (needs a file: export the M1 adapter with `personacore.checkpoint.export_adapter`) |
| Ledger / crash / heartbeat | new log | `phase36_ledger.append/reconcile/spent/require_launch`, `phase25_run.beat/start_heartbeat`, Phase 40's `drop_attempt`/`declare_relaunch` shapes |
| Atomic write | tmp+rename | `phase25_run.atomic_write_json` |

## Common Pitfalls

1. **Unfilled b-margin reddens leg (c).** It is a Phase-41 slot (SLOTS :1844). Put `E1_CONDITION_B_MARGIN = phase35_prereg.fill("e1_condition_b_margin")` in fill file 1 (as `_P41_FIRST` does).
2. **Intermediate phase41 records before the floors fill deadlock legs (a)/(c).** Calibration raw arm records, K16 scratch, csvs: anything under `results/phase41_*` that is not `calibration_*`/`band_inputs_*` and is committed before `phase41_floors_prereg.py` turns leg (a) red (floors file is not before it) and leg (c) red (floors are unfilled). Keep raw prep outputs under `data/phase41_e1/` (gitignored, `.gitignore:17`) and embed the draws in the calibration record. Rehearsal prefix `phase41rh` (fnmatch `results/phase41_*` does not match `phase41rh_`), like Phase 40's `phase40rh`.
3. **`_cmd_cal_train` collides with Phase 19 outputs and ignores the seed** (see Pattern 7). D-10's "arm `erase_calibration`" must be read as that arm's recipe under a Phase 41 arm name.
4. **Pin (b) helpers are pet_name-only.** `nontarget_rows`/`nontarget_deltas`/`target_fact_id`/`render_verdict` hard-wire `TARGET_SLOT`. For cat_name/street/sibling_name they would drop pet_name and gate the target as a non-target.
5. **Wrong (b) baseline at seed 2024** (Pattern 8). Also route (b) pre and the D-18 "full intact" column through the same Phase 40 A2 full record.
6. **`span_nll_from_ids` is `no_grad`.** A gradient through `value_span_nll_mean` is zero/absent. Use the twin, assert value equality (D-02). The MPS equality is unmeasured (Assumption A1).
7. **Second K=48 confirmation exceeds the committed cap.** `unit_caps.E1.k48_confirms_per_cell = 1`; `e1_stop` allows K16=0 / K48≠0 → continue → a second confirmation. `check_unit_caps("E1", k48_confirms_per_cell=2)` refuses (phase36_caps.py:165-178; "exceeding a Phase 36 cap needs Rafael's approved"). Open Question 1.
8. **D-23 pause is not a ledger stop.** `require_launch` pauses only at 1.5 × 52.78 = 79.17 h (stop a), at 90 h cumulative (stop b), or on projection > 90 (stop c) (phase36_ledger.py:341-367). The 52.78 h check is new code: `spent(fronts=("E1",))["by_front"]["E1"] / 3600 >= budget["front_hours"]["E1"]` before each cell's start line (`spent` refuses while an attempt is open, so check between attempts). Ledger now: total 16.7588 h, E1 0.0 h, E2 11.6465 h (stop a at 11.836 h) [VERIFIED: `phase36_ledger.spent()`]. `rule()` can only lift a/b/c, so a resume after the E1 pause needs its own written-approval artifact (Open Question 4).
9. **The current-ordering price is k-dependent.** 417.56 s = Phase 19's k=78 run. For targets whose rank stays 1 longer, `select_ablation_prefix`'s rank scan runs further (≤288 × |R|=8 NLLs) plus one extra curve row. CPU NLL ≈ 6 ms, so the scan is minor, but MPS per-NLL time is unmeasured (A3). Compare the first cell's wall-clock against 417.56 s.
10. **Leg (a) also freezes fill file 1 against fixes.** After the first calibration record is committed, any edit is red forever. Corrections become dated continuations (`_addendum.py` for markdown; a new continuation module for Python), never edits (memory `pin-corrections-are-dated-continuations`). Run the code review BEFORE the first record commit.
11. **Census registers a new file trips.**
    - `train_arm(` grep census (`tests/test_phase23_resume.py:60`, `_TRAIN_ARM_CALL_SITES`): add one line for the Phase 41 call. It counts text hits in `scripts` and `tests`, so a test file that writes `train_arm(` in prose also counts.
    - draw_all census (Pattern 5).
    - `os.replace` census.
    - ISO-06 (`tests/test_lora_inject.py:261`): avoid `inject_lora` (use `recall.load_adapted_model`).
    - `== 10` literal wall (`tests/test_phase21_sc5.py:170`): no `== 10` in new tests.
    - `mitigation_gate.ratchet_k` K menu `(48,24,16,8)`: fixtures use 8/16 only.
    - Slot census + "every prereg function has a CPU test" (`_untested_functions`, test_phase35_prereg.py:2725).
    - `test_owner_fill_files_respect_the_caps_on_the_real_repo` (tests/test_phase36_caps.py:283) **exec's every tracked fill file**, so both phase41 fill files must import cleanly on a CPU-only clone.
    - Grep acceptance criteria over files whose docstrings discuss a term go false-red. Use AST gates (memory `grep-criteria-measure-prose`).
12. **Host-gated skips move the CI skip pin.** `checkpoints/` is gitignored. Any test that skips when an adapter is absent changes the ubuntu skip total pinned in `tests/test_phase25_venue.py` (memory `execute-phase-gates-in-personacore`). Do the adapter sha256 check in driver preflight and test it with fakes.
13. **Dry-run-only tests hide an unwired live path** (memory `dry-run-tests-hide-an-unwired-driver`). Required tests:
    - `main([cmd])` dispatches to the real function with `inspect.signature(real).bind` (test_phase40_noise.py:2830);
    - `run()` with no arguments resolves the real defaults on a fake rig (:1647);
    - feed `emit` one real committed producer record. Before stage 2, feed the floors/band fills the actual stage-1 records, and the verdict combiner one real K48 arm record: `results/erasure_kstar_arm_k064.json` (A2, k=64, pet_name 0/27) is a committed stand-in with the same schema.
14. **Operations.**
    - The waiter follows the driver PID (`ps -p`, then an empty `pgrep`), never the appended log (memory `appended-log-waiter-kills-relaunch`).
    - The caffeinate child holds the assertions (memory `caffeinate-dims-wrapper-is-the-child`).
    - The collector `/Library/LaunchDaemons/com.polybot.negrisk-books.plist` stays stopped. Record `sysctl vm.swapusage`, `memory_pressure | tail -1`, top RSS and the latest JetsamEvent before each kickstart (40-09-SUMMARY.md:160-166).
    - Kill a running suite's pytest pids before an executor edits `scripts/` (clean-tree probes).

## Code Examples

The fill file 1 skeleton follows the census-conformant shape at `tests/test_phase35_prereg.py:2563` and `scripts/phase38_sizes_prereg.py`:
```python
import phase35_prereg
import phase36_caps
GRID = (16, 32, 48, 64, 128)            # D-07, caller-chosen; derivation value must be this tuple
BUDGET_RECORD = phase35_prereg.SLOTS["e1_checkpoint_grid"]["input_records"][0]   # registry read, allowed
E1_CHECKPOINT_GRID = phase35_prereg.fill("e1_checkpoint_grid", checkpoints=GRID,
    input_records=(BUDGET_RECORD,),
    derivation={"value": GRID, "derivation": "...D-07 text...", "kind": "preference",
                "source": f"41-CONTEXT D-07 (447747c); {BUDGET_RECORD} front_hours.E1, unit_caps.E1"})
E1_ALTERNATIVE_ORDERING = phase35_prereg.fill("e1_alternative_ordering", ordering={
    "value": "gradient", "derivation": "...D-01..D-05 rule incl. written static fallback...",
    "kind": "preference", "source": "41-CONTEXT D-01..D-06 (447747c)"})
E1_CONDITION_B_MARGIN = phase35_prereg.fill("e1_condition_b_margin")
phase36_caps.check_unit_caps("E1", **phase36_caps.counts_for("e1_checkpoint_grid", E1_CHECKPOINT_GRID))
```
Ordering keys: `ORDERINGS = ("greedy", E1_ALTERNATIVE_ORDERING["value"])`. The Phase 40 consumer test already keys the band by `(seed, "greedy")` (test_phase40_noise.py:2066). `fill` needs no extra import beyond `phase35_prereg` (the slot census forbids `from phase35_prereg import fill`).

D-16 pair label (pure, truth-table tested):
```python
def pair_label(v1337, v2024):
    if v1337 == v2024 == "SUCCESS": return "PASS"
    if v1337 == v2024 == "FAILURE": return "FAILURE replicada"
    return "não replicado"          # carries both seeds' verdicts verbatim in the record
```

## State of the Art

| Old | Current | Impact |
|---|---|---|
| v3.0 (c): one-sided caps on dialogue and retention PPL (erasure_gate.py:245-251) | dialogue gap band anchored on the adapted model (ERASE-09; retention descriptive only, D-14) | do not reuse `erasure_succeeded` |
| Phase 19 calibration stop via twin refs, k=187 at seed 1337 on `phase19_erase_calibration_adapter.pt` | per (ordering, seed) on fresh adapters | D-11 compares the new 1337 adapter by `torch.equal` |
| E1 single target pet_name, single seed | 4 targets × 2 orderings × 2 seeds | pin (b) helpers unusable as-is |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | On MPS the grad-enabled forward equals `value_span_nll_mean` bit for bit (true on CPU, measured) | Pattern 2 | A hard assert would crash an MPS cell. Measure in the MPS launch-gate smoke, or record the difference with a pre-declared tolerance. |
| A2 | On MPS, K16 draws equal the first 16 of the K48 draws (prefix stability, the v4.0/Phase 36 premise) | Pattern 5 | Only descriptive; the stop reads each read separately. |
| A3 | MPS per-NLL cost is small enough that `select_target_prefix`'s k-dependent rank scan stays near 417.56 s for every target | Pitfall 9 | E1 overrun is caught by the D-23 pause. |
| A4 | A Phase-41 arm name and prefix do not change training numerics (bins depend only on facts/family_ids/settings/seed), so D-11 can hold | Pattern 7 | D-11 is a prediction; a mismatch is a finding. |
| A5 | A raw `run_erasure_arm` record written under `data/` and folded into the calibration record satisfies "the arm's own draws" | Pattern 7 | If Rafael wants the raw arm record committed, it needs a path outside `results/phase41_*`, or a post-floors commit. |

## Open Questions (bring to Rafael before the prereg freeze)

1. **Second K48 confirmation versus the cap of 1.** The ruling must be written in fill file 1 before any record exists. Options: allow it and count it in E1 hours; or pause for approval mid-cell. Recommendation: pre-register "a further confirmation is allowed; each one is recorded and its hours count against E1's share", or ask Rafael.
2. **K16 read scope.** The price assumes all 216 A2 questions (1437.67 s). Only the target's 27 enter the stop, so 27 would be roughly 8× cheaper. Recommendation: keep 216 (it matches the priced design and gives per-fact damage at every checkpoint, descriptive). This is a design choice; record it in fill file 1.
3. **D-19 label for `pet_name` as a non-target** (in cat_name/street/sibling_name cells). `recall_floor.{full,m2}.per_slot` has no `pet_name` row (M2 drops it; full counts 27,26,27,25,27 → range 2/27 [VERIFIED from phase40_a2_full_seed*.json]). Recommendation: compute pet_name from the full group's A2 records only (range 2/27 → unlabelled) and say so; or mark it "não avaliado".
4. **Resume after the D-23 pause.** It needs a written approval record (path and format). Mirror Phase 40's `relaunch_declaration` (`phase40_prereg.RELAUNCH_DECLARATION_KEYS`) under `data/phase41_*`.
5. **Band records: own ledger attempts or inside the calibration attempts.** One `end` line names one record (`phase36_ledger.append`, :221-226). Recommendation: one attempt per (ordering, seed) prep unit that ends on the calibration record, with the band measured first inside it; or separate short attempts ending on each band record. Both keep the hours on E1.
6. **MPS strictness of the D-02 value equality** (A1).
7. **Precondition: Phase 40 is not closed** (no `40-VERIFICATION.md`; ROADMAP.md:1444 and REQUIREMENTS NOISE-01/02 still `[ ]`; `ls .planning/phases/40-m2-seed-noise-floor/` shows no VERIFICATION) [VERIFIED]. Plan 41-01 should start with a gate task:
   - Phase 40 hand-closed by the orchestrator, or verified;
   - `git ls-files --error-unmatch` on `results/phase40_noise_floor.json` and `results/phase40_a2_{full,m2}_seed{1337,2024}.json`;
   - sha256 of the four adapters equal to `phase41_adapters`.

   Phase 41 reads:
   - `gap_noise_floor` 0.08406970366097503;
   - `per_seed[s].full.dialogue_gap.gap` (1337: 1.2420966625043919, 2024: 1.2368822143360418);
   - `recall_floor.{full,m2}.per_slot[*].{counts,range}`;
   - `d13.blocks`;
   - the A2 full/M2 records of 1337/2024 [VERIFIED values].

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| `.venv` Python 3.11 | everything | ✓ | 3.11.15 | — (never system 3.14) |
| torch + MPS | stage 1/2 | ✓ | 2.7.1 | CPU only for rehearsal |
| Phase 40 adapters (4) | cells | ✓ | sha256 verified in CONTEXT 2026-10-07 | none: blocking if missing |
| `checkpoints/persona_adapter.pt`, convbase, tokenizer, dialog/retention bins, `results/phase18_corpus.json`, `results/phase19_calibration_corpus.json` | pin run inputs | ✓ (pin ran in Phase 40) | — | preflight refuses (Phase 40 `run_inputs` pattern) |
| `gsd-sdk` | planning | ✓ | — | — |
| launchd agent `com.personacore.phase41.e1` | launch | ✗ (to be written) | — | mirror `artifacts/com.personacore.phase40.e2.plist` + its plist test (test_phase40_noise.py:607) |

## Validation Architecture

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest 8 in `.venv`, CPU-only |
| Quick run | `.venv/bin/pytest -q tests/test_phase41_prereg.py tests/test_phase41_floors_prereg.py tests/test_phase41_erasure.py -p no:cacheprovider` |
| Gate legs | `.venv/bin/pytest -q tests/test_phase35_prereg.py -k "slot_ordering or slot_census or frozen" tests/test_phase36_caps.py -k owner tests/test_phase37_routes.py -k byte_unchanged tests/test_phase23_resume.py tests/test_phase14_scoring.py -k draw_all tests/test_phase25_driver.py -k os_replace tests/test_lora_inject.py tests/test_phase21_sc5.py` |
| Full suite | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus an `until grep -q '^EXIT='` waiter. It takes ~53-56 min (4495 passed / 4 skipped at 9a6a5e4, 40-11-SUMMARY.md:45,89), and the Bash tool caps a call at 600 s. |

### Phase Requirements → Test Map
| Req | Behavior | Type | Command / test | Exists? |
|---|---|---|---|---|
| ERASE-03 | targets iterate `e1_targets()`; no typed names (AST) | unit | `tests/test_phase41_prereg.py::test_targets_are_read` | ❌ W0 |
| ERASE-04 | two orderings; alt-ordering entry four fields; gradient = Σ B·∂B (vs explicit-s finite difference, vs Σ A·∂A); tie-break by address; whole ordering recorded | unit (CPU tiny model) | `::test_taylor_scores_identity`, `::test_ordering_recorded` | ❌ |
| ERASE-05 | adapter digests from `phase41_adapters`; preflight refuses a mismatch (fake files) | unit | `tests/test_phase41_erasure.py::test_preflight_refuses_adapter_mismatch` | ❌ |
| ERASE-06 | floors fill on real committed calibration records; leg (a)/(b)/(c) green on real repo; planted reds | unit + git-rig | `tests/test_phase41_floors_prereg.py`; `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` | partial (35 legs exist) |
| ERASE-07 | driver stop == `e1_stop`; rank at every read checkpoint; NOT_REACHED sentence verbatim | unit | `::test_cell_loop_matches_e1_stop` (truth table over readings) | ❌ |
| ERASE-08 | pin byte-unchanged | git | reuse `tests/test_phase37_routes.py::test_pin_and_gate_are_byte_unchanged`, plus a Phase 41 leg asserting the driver never calls `_cmd_*`/`report` (AST) | ✅ / ❌ |
| ERASE-09 | band via `DIALOGUE_GAP_BAND is mitigation_gate.dialogue_gap_band`; control_gap equality refusal | unit | `::test_band_is_imported`, `::test_control_gap_mismatch_stops` | ❌ |
| ERASE-10 | per-target 7 non-targets each /27; pre = Phase 40 A2 full of the same seed; pair labels truth table; D-17 counts | unit | `::test_verdict_per_target`, `::test_pair_labels` | ❌ |
| SC5 | prereg frozen before records; test file first-added before records; RECORDS_AT_COMMIT; write-once | git | Phase 40 analog tests (test_phase40_prereg.py:391-413) | ❌ |

### Sampling Rate
- **Per task commit:** the quick run plus the gate legs touching the edited file.
- **Per wave merge:** the full suite on a COMMITTED tree, run again after each record commit (Phase 36 lesson: new reds appear only once records are tracked).
- **Phase gate:** full suite green, plus a full-shape CPU rehearsal into a tmp root before any MPS launch (`phase41rh` prefix, explicit ledger and heartbeat, `device='cpu'`; Phase 40's 40-08 pattern, ~1.15 h CPU per Phase 40 seed). The rehearsal measures the backward/forward ratio and asserts the D-05 ordering cost. MPS launch gate: a smoke of A1 and A3.

### Wave 0 Gaps
- [ ] `tests/test_phase41_prereg.py`: must be committed in or before the commit that adds `scripts/phase41_prereg.py`, and before any phase41 record.
- [ ] Register line in `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES`.
- [ ] A tiny CPU GPT+LoRA fixture for the gradient identity tests (no checkpoints, so no host-gated skip).

## Security Domain

| ASVS | Applies | Control |
|---|---|---|
| V5 Input validation | yes | every consumed record re-validated by the slot rules (`_prove_record`, `_consume_inputs`); `_prove`, never `assert` |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256` for records and adapters; `torch.equal` for tensors |
| V2/V3/V4 | no | offline, single user |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Edited prereg after seeing results | Tampering | ancestry legs (a)/(b)/(c) and the frozen-before tests; dated continuations only |
| Overwritten evidence | Tampering | write-once (`_write_once`), `run_erasure_arm` clobber refusal, append-only ledger (`prove_append_only`) |
| Pickle code execution in adapters | Elevation | `load_adapter` / `load_adapted_model` (weights_only load, phase14_recall.py docstring) |
| Kaggle token / secrets in records | Info disclosure | none involved; never record env |

## Sources

### Primary (HIGH; read at HEAD 3a96092)
- `scripts/phase35_prereg.py` :37-90, :317-350, :371-450, :769-778, :847-1010, :1060-1120, :1211-1418, :1694-1903
- `tests/test_phase35_prereg.py` :2120-2280, :2430-2702
- `scripts/phase19_erasure.py` :225-345, :604-640, :1291-1375, :2389-2510, :2541-2560, :2704-2940, :3092, :3184-3230, :3521-3590
- `scripts/phase18_extraction.py` :1031-1130, :1361
- `scripts/phase37_routes.py` (whole); `tests/test_phase37_routes.py` :300-420
- `scripts/erasure_gate.py` :95-260; `scripts/mitigation_gate.py` :526-593
- `scripts/phase40_noise.py` :1-1120; `scripts/phase40_prereg.py` :1-140, :1036-1060, :1201-1300, :1391-1597
- `tests/test_phase40_noise.py` :607, :1647, :2062, :2830; `tests/test_phase40_prereg.py` :378-413, :870-905
- `scripts/phase36_ledger.py`, `scripts/phase36_caps.py` :45-210, `scripts/phase36_budget.py` :100-240, `results/phase36_budget.json`
- `scripts/phase23_run.py` :4185-4520; `scripts/phase36_probe.py` :440-575; `scripts/erasure_kstar_run.py` :1-140
- `scripts/phase38_sizes_prereg.py`, `tests/test_phase38_sizes_prereg.py`
- `results/phase40_noise_floor.json`, `results/phase40_a2_full_seed*.json`, `results/phase19_*` records, `ledger/v6_mps_ledger.jsonl`
- CPU scratch probe (this session): grad-path equality, 4.33× ratio, Taylor vs actual deltas

## Metadata
- Standard stack: HIGH, since every symbol was read in the code.
- Architecture and fill order: HIGH. It is pinned by planted tests.
- Pitfalls: HIGH for the code-contract ones; MEDIUM for MPS cost and determinism (A1-A3).
- Valid until: the next commit touching `scripts/phase35_prereg.py` (frozen) or the Phase 40 records; about 30 days otherwise.
