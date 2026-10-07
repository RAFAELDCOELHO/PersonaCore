# Phase 41: Erasure Across Facts, Orderings and Seeds - Context

**Gathered:** 2026-10-07
**Status:** Ready for planning

<domain>
## Phase Boundary

E1 re-measures erasure on the four facts at 13/13 in Phase 19's `TARGET_RANKING` (`pet_name`,
`cat_name`, `street`, `sibling_name`). It runs two orderings (the current one and the alternative
fixed below) and two teaching seeds (1337, 2024), which makes 16 cells (target × ordering × seed).
Each cell stops at the first zero on the pre-registered checkpoint grid, read with A2 at K = 16
and confirmed at K = 48 (`phase35_prereg.e1_stop`). Each cell gets a verdict under conditions
(a), (b) and (c). No (target, ordering) pair reads PASS without both seeds.

The phase fills only the Phase-41-owned slots of `scripts/phase35_prereg.py` (`e1_alternative_ordering`,
`e1_checkpoint_grid`, `e1_condition_a_floors`, `e1_condition_c_band_inputs`; `e1_condition_b_margin`
is already locked in the core), and produces the descriptive readings declared below. New training
arms beyond the calibration adapters are out of scope (see Deferred).

**Requirements:** ERASE-03..ERASE-10.

**Precondition.** Phase 40 is not formally closed yet: there is no `40-VERIFICATION.md`, and
ROADMAP.md:1444 and REQUIREMENTS NOISE-01/02 still read `[ ]` (the 40-11-SUMMARY leaves the hand
close to the orchestrator). Phase 41 reads `results/phase40_noise_floor.json` (committed fd603cd)
and the four adapters it names. Close Phase 40 before the Phase 41 plans treat it as done.
</domain>

<decisions>
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
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pre-registration and slots
- `scripts/phase35_prereg.py`
  - :37-90: slot registry, the owner fill-file ordering rule, and the Phase 41 band and calibration
    contracts.
  - :371: `e1_teaching_seeds`; :382: `e1_targets`; :434: `e1_condition_b_margin`.
  - :1060-1120: `NOT_REACHED` / `e1_stop`.
  - :1211: `_rule_e1_checkpoint_grid`; :1261: `_rule_e1_condition_a_floors`; :1415:
    `_rule_e1_alternative_ordering`; :1700: `_rule_e1_condition_c_band_inputs`; :1791: `_SLOTS`.
- `tests/test_phase35_prereg.py:2434`: the per-fill-file ordering legs.
- `.planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-CONTEXT.md`: D-01..D-05,
  D-16.
- `.planning/REQUIREMENTS.md:737-744`: ERASE-03..10.
- `.planning/ROADMAP.md:1847-1882`: Phase 41's goal and success criteria.

### Erasure mechanics (v3.0, pin byte-unchanged)
- `scripts/phase19_erasure.py`
  - :604-611: `TARGET_RANKING`; :237-272: the component index (36 keys × rank 8 = 288).
  - :2389: `CURVE_CHECKPOINTS`; :2407: `value_span_nll_mean`.
  - :2443-2510: `select_ablation_prefix`, the current ordering, sorted once by single-ablation NLL
    rise.
  - :2955-3020: M2; :3092: `CALIBRATION_ARM`; :3184: `select_calibration_fact`; :3520-3570:
    `_cmd_cal_train` / `_cmd_cal_erase` / `_selected_components`.
- `scripts/phase37_routes.py:155-186`: `select_target_prefix` (defect E route, |R| = 8).
- `scripts/erasure_gate.py:101-117, 229-255`: (a)/(b)/(c), `VERDICTS`, `MARGIN_K`.
- `scripts/mitigation_gate.py:526-590`: `dialogue_gap_band` (D-01); `:595` `retention_cap`
  (descriptive only here, D-14).

### Inputs and prior readings
- `results/phase36_budget.json`: E1 hours, unit caps and unit prices.
- `results/phase36_probe_e1.json`: E1 probe configuration.
- `scripts/phase36_budget.py:125-140, 221-224`: how the E1 prices and caps were derived.
- `results/phase40_noise_floor.json`
  - `phase41_adapters`, `gap_noise_floor` 0.08406970366097503;
  - `per_seed.*.full.dialogue_gap`, `recall_floor.{full,m2}.per_slot`, `d13.blocks`.
- `results/phase40_noise_floor_report.md`: :741 (how (b) is read against 0.348 is left to Phase 41;
  answered here by 35 D-16 and D-18) and the seed-2025 section.
- `results/phase40_a2_{full,m2}_seed*.json`: `retention_ppl`, per-fact A2.
- `results/erasure_kstar_summary.json`: k* = 64.
- `results/phase39_ctx_report.md:140-275`: prefix A2 and D-13 readings of `pet_name`.
- `results/phase19_collateral_curve.json`, `results/phase19_calibration_curve.json`,
  `results/phase19_arm_erased.json`, `results/phase19_arm_cal-erased.json`.
- `results/phase20_retention_floor.json`: v4.0 retention cap and floor (descriptive).
- `.planning/phases/40-m2-seed-noise-floor/40-CONTEXT.md`: D-07 predictions, D-13, R-3 b
  (lines 149-157).
- `.planning/phases/40-m2-seed-noise-floor/40-09-SUMMARY.md`: launch gate, memory state, the
  collector.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase19_erasure.select_ablation_prefix` / `value_span_nll_mean` / `ablate_components` /
  `component_index`: the current ordering and the NLL the gradient ordering must reuse (D-02).
- `phase37_routes.select_target_prefix`: the defect-E-corrected target route (ERASE-08).
- `phase19_erasure._cmd_cal_train` / `_cmd_cal_erase` / `per_fact_rows` / `lock_erasure_floor` /
  `floor_branch`: the calibration and floor computation the floors slot already calls.
- `mitigation_gate.dialogue_gap_band` (imported via `phase35_prereg.DIALOGUE_GAP_BAND`).
- `phase38_rank` / `phase39_ctx` scoring: the D-13 block for D-20.
- The Phase 40 driver (`scripts/phase40_noise.py`): ledger attempts, R-3 b crash handling, pause
  and launch-gate patterns for D-23..D-25.

### Established Patterns
- One ancestry-guarded owner fill file per phase (`scripts/phase41_*prereg.py`) that binds
  `<SLOT> = phase35_prereg.fill("<slot>", ...)`; every value carries the four-field entry
  {value, derivation, kind, source}.
- Predictions are recorded before the run as descriptive; a disagreement is a finding (Phase 40
  D-07).
- Write-once records; "approved" before each commit; a CPU rehearsal before any MPS launch.

### Integration Points
- Records: `results/phase41_calibration_*.json` (ERASE-06), `results/phase41_band_inputs_*.json`
  (ERASE-09), `results/phase41_*` (ERASE-03..10).
- The ledger `ledger/v6_mps_ledger.jsonl` under front "E1".
</code_context>

<specifics>
## Specific Ideas

- The NOT_REACHED sentence, verbatim: "não apagado com 128 de 288 componentes removidos".
- The pair labels, verbatim: "PASS", "FAILURE replicada", "não replicado".
- The descriptive labels: "varia entre seeds", "dentro/fora da faixa", "passaria no teto do v4.0:
  sim/não", "sem M2, comparação não feita".
- Rafael's answers are quoted verbatim in `41-DISCUSSION-LOG.md`.
</specifics>

<deferred>
## Deferred Ideas

- **M2 for the other three targets** (`cat_name`, `street`, `sibling_name`) × 2 seeds. That is 6
  retrains plus their A2 passes, about 4.7 h MPS (6 × (76.11 s + 2762.26 s)), outside ERASE-05 and
  the Phase 36 budget. Consider it after E1, E3 and E4, only if budget remains.
</deferred>

---

*Phase: 41-erasure-across-facts-orderings-and-seeds*
*Context gathered: 2026-10-07*
