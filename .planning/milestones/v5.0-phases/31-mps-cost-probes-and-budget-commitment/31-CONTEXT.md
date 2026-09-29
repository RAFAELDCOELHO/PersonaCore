# Phase 31: MPS Cost Probes and Budget Commitment - Context

**Gathered:** 2026-09-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Measure on the M3 (MPS) what v5.0 actually costs, and commit the budget from those measurements instead of the unsourced ~25-30 h estimate.

The phase produces three write-once records at the paths already pinned in `scripts/phase29_prereg.py::V5_RESULT_PATHS`:
- `results/phase31_probe_point.json` (ARCAL-01): one replay-bearing adversarial point run end to end (training, condition (c), attack scoring, taught recall), with per-stage wall-clock.
- `results/phase31_probe_relearn.json` (ARCAL-02): one relearning leg on a real trained adapter, with per-leg wall-clock.
- `results/phase31_budget.json` (ARCAL-03): the sweep and relearning cost derived from the two probes, with an ancestry test proving it precedes the first sweep point.

Out of scope: running any sweep point (Phase 32), admission (Phase 33), and fixing the Phase 30 carried item WR-03 (stays carried to Phase 32).

</domain>

<decisions>
## Implementation Decisions

### Probe point (ARCAL-01)
- **D-01:** The probe runs the **`advr_n64` control** (ratio 0), the cost-dominant leg with 256 replay windows per step. Only a control can run before Phase 32, because the Phase 30 D-19 guard refuses a non-control point until its own control record exists.
  - A control has no `control_gap` of its own, so condition (c) runs for timing only. The probe records its readings, but they gate nothing.
  - The n8 cost is not probed. It is derived per stage from n64, as specified under D-09.
- **D-02:** The probe is **discarded and isolated**, following the Phase 23 precedent (`results/phase23_cost.json` has `sweep_point: false`).
  - It writes under its own prefix and its own sidecar and adapter paths, never a `phase32_point_*` key or path (SC4).
  - A guard proves that Phase 32's `train_stage` cannot pick up the probe's sidecar or adapter (`phase25_points.train_stage` silently REUSES an existing `data/phase25_<key>_training.json` and adapter).
  - The probe record carries `sweep_point: false` with a reason.
- **D-03:** The probe **times taught-recall scoring** as its own stage. Phase 25 scored recall separately (~1304.5 s/point, `results/phase25_recall.json`), but v5.0 needs recall for floors and `control_gap`, so the budget prices it from this measurement.

### Relearning probe (ARCAL-02)
- **D-04:** "One leg" is **one arm on the full ladder**: one seed relearning to `RELEARN_CAP` = 400 steps, scored at all 8 `RUNGS` at `CURVE_K`. That is the atomic unit every Phase 27 leg is built from. The budget multiplies it by each sub-mode's arm count (fresh ×5, control, mitigated).
- **D-05:** The adapter is **the probe's own `advr_n64` adapter** from D-01: the replay-bearing recipe v5.0 would relearn on, real rather than a CPU stub, and isolated with the probe. The relearning probe therefore runs after the point probe.
  - The v4.0 `checkpoints/phase25_ratio*_adv_n64_adapter.pt` files are NOT used: they are the no-replay recipe and gitignored.
- **D-06:** The relearning probe is built from `phase27_relearn`'s lower-level pieces (`train_relearn_arm`, `score_rung`). **`scripts/phase27_relearn.py` must not be edited**: `results/phase27_admission.json` pins it strictly in `PINNED_MODULES`, the tripwire in `tests/test_phase27_relearn.py` would go red, and every public leg starts with `_require_admitted` against a MOOT record.
- **D-07:** The relearning term is **priced but not scheduled**.
  - Under D-15 option 2 from Phase 29, v5.0 admission reaches CANDIDATE-UNREPLICATED at best, never ADMITTED, so RELRN-06..09 do not run under the current contract.
  - The budget records the relearning term as 0 h scheduled, alongside the full conditional cost of the relearning legs if a later ruling admits. The probe still runs, because ARCAL-02 requires the measurement.

### Budget (ARCAL-03)
- **D-08:** The budget is a **resource record plus a pre-committed stop line**, not an outcome threshold (consistent with ROADMAP:171).
  - **Stop line:** Phase 32 pauses at a developer checkpoint when cumulative sweep wall-clock exceeds **1.5 × the upper bound of the budget's measured range** (D-10).
  - The stop line is recorded in `phase31_budget.json`, and Phase 32 must read it from there, never retype it.
- **D-09:** The budget uses a **per-stage × counts** formula: the measured per-stage times (train, condition (c), attack draws/scoring, recall) × the point count per leg.
  - n8 per-stage times are scaled from n64 by measured ratios. The replay-bearing training stage scales with the replay window count (32 vs 256). The non-training stages use Phase 25's measured n8/n64 stage ratios.
  - Both D-12 branches are priced: a leg whose control is unlearnable costs its control only, and the rest get REFUSED records with no training.
  - The formula, every input and its source path go in the record, so the total can be recomputed from committed files.
- **D-10:** The uncertainty is **Phase 25's measured spread**, not an invented multiplier: the point estimate plus a range from Phase 25's measured per-point spread (adv points 49-71 min, ~±20%) applied per stage. The range is empirical, and D-08's stop line hangs off its upper bound.

### Replay evidence and run mode
- **D-11:** The probe shows that replay ran by **counting replay draws through `train()`'s existing `on_draw` hook**, the same mechanism `tests/test_phase30_seam.py` uses.
  - The count is recorded per optimizer step in the probe record and must equal `phase29_prereg.replay_windows(64)` = 256 on every step.
  - **`scripts/teach_persona.py` stays untouched.** WR-03 stays carried to Phase 32 as a named item. Reopening frozen pins to edit a protected production module is not worth it here.
- **D-12:** The probes run **unattended under a LaunchAgent**, reusing Phase 25's pattern (`artifacts/com.personacore.phase25.sweep.plist`: `caffeinate -dims`, heartbeat jsonl, logs under `logs/`). Timings are then not skewed by sleep or interactive load. The developer launches and boots out the agent, as in Phase 25/26.

### Claude's Discretion
- The exact probe prefix and sidecar/adapter naming, provided it cannot collide with any `phase32_point_*` / `phase25_*` path (D-02).
- How condition (c) runs for timing without a `control_gap` on a control (D-01), provided the record makes clear that the readings gate nothing.
- Whether the two probes share one LaunchAgent run in sequence or use two (D-05 already orders them point → relearn).
- The record schemas, provided they carry the per-stage wall-clock, `sweep_point: false`, the on_draw replay counts, the provenance (git_sha, head_at_write, module_sha256) and the descent from the calibration commit `4339f2b`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/ROADMAP.md` §"Phase 31: MPS Cost Probes and Budget Commitment": goal and SC1-SC4. Also :171-176, where the budget is a resource, not an outcome threshold.
- `.planning/REQUIREMENTS.md`: ARCAL-01, ARCAL-02, ARCAL-03 (:605-607).

### Pre-registration and prior decisions
- `scripts/phase29_prereg.py`: `V5_RESULT_PATHS` (:148), `ARTIFACT_PATHSPECS`, `POINT_KEYS`, `replay_windows`, the relearning pins `RUNGS` / `RELEARN_CAP` / `FRESH_SEEDS` / `CURVE_K` / `FULL_K` (:315-335), and the D-15 option-2 note (:299-305).
- `.planning/phases/29-v5-0-pre-registration-and-carried-debt/29-CONTEXT.md`: D-02/D-03 paths, D-12 unlearnable-control branches, D-14 write-once/no retry, D-15.
- `.planning/phases/30-replay-bearing-adversarial-recipe-and-its-own-control/30-CONTEXT.md`: D-17/D-18 controls-first, D-19 own-control guard.
- `.planning/phases/30-replay-bearing-adversarial-recipe-and-its-own-control/30-REVIEW.md`: WR-03 (carried), and IN-02/IN-03.
- `results/phase30_calibration.json`: the recipe (seed 1337, max_steps 200, replay 32/256, min_refusal 15). Every v5.0 result descends from its commit, `4339f2b`.

### Cost baselines
- `results/phase25_point_adv_*.json`: `training.seconds`, `measure_seconds`, `shape_timing[*].minutes` (the no-replay per-stage baseline).
- `results/phase25_point_dp_*sigma0*.json`: the only existing replay-bearing training times (dp_n8 ~3.5 min, dp_n64 ~23 min; confounded by DPSGD).
- `results/phase25_recall.json`: taught-recall ~1304.5 s/point.
- `.planning/phases/25-*/25-17-SUMMARY.md` :70-76: adv points 0.92-1.12 h.
- `.planning/phases/25-*/25-HUMAN-UAT.md` :49: the origin of the "~25-30 h" estimate ("12 points at Phase 25's measured pace", no replay or relearning term).
- `results/phase23_cost.json`: the `sweep_point: false` precedent.

### Run mode
- `artifacts/com.personacore.phase25.sweep.plist`: the LaunchAgent pattern to reuse.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/phase30_points.py`: `point_plan`, `recipe_identity`, `require_calibrated_recipe`, `own_control`, `next_action`. It only plans and never trains. Its `point_plan` prefix is `phase32_…`, so the probe needs its own prefix (D-02).
- `scripts/phase25_points.py`: `train_stage` and `measure_stage` accept the Phase 30 plan dict. `train_stage` reuses existing sidecars and adapters (the D-02 hazard).
- `scripts/phase25_run.py`: `draw_point_shapes` (:458) and `score_point` (:586) are key-agnostic. `run_point` (:633) is NOT reusable: it calls `phase25_prereg.prove_first_attempt` and `phase25_points.point_plan` / `parse_point_key`, which refuse `advr_*`.
- `scripts/phase25_condition_c.py`: `measure_condition_c` (:176). `control_gap_for_capacity` (:646) needs a control reading.
- `scripts/phase27_relearn.py`: `train_relearn_arm` (:526), `score_rung` (:692). Import only; never edit (D-06).
- `src/personacore/training/loop.py`: the `train()` `on_draw` hook (D-11).

### Established Patterns
- Write-once records with a dirty-first refusal and `phase25_run.atomic_write_json`. `os.replace` is allowed only in `phase25_run.py` / `phase25_record.py`.
- The provenance block {module_sha256, git_sha, head_at_write, written_utc}. Pins are live-checked, so a later edit to a pinned module needs a dated `_SUPERSEDED_PINS` continuation.
- The Phase 30 AST guard bans v4.0 control carriers (`control_key_for`, `control_reading`, `_adversarial_extras`, dp-key strings, aliases, `getattr`) in v5.0 modules, and the probe modules fall under it.

### Integration Points and Tripwires
- **`_SUPERSEDED_PINS` registers.** Any commit to `scripts/teach_persona.py` (`tests/test_phase27_relearn.py`, `tests/test_phase24_record.py`) or `scripts/phase30_points.py` (`tests/test_phase30_calibration.py`) must add its SHA there. The Phase 31 plan should avoid both modules or budget the dated extension.
- **Ancestry.** `test_ancestry_calibration_precedes_every_later_v5_result` and `test_phase29_prereg_is_frozen_before_every_v5_result` apply. `phase25_record.py` and `phase20_gate_coverage.py` are frozen once a v5.0 result exists.
- **New ancestry test (ARCAL-03).** `phase31_budget.json` must precede the first `phase32_point_*` record.

</code_context>

<specifics>
## Specific Ideas

- The developer's recurring emphasis: measurement over assumption. The budget exists because the ~25-30 h figure was never measured, so every number in `phase31_budget.json` must trace to a committed record, and the range is empirical rather than a guessed margin.
- Timing reliability matters more than convenience, so runs are unattended (D-12).

</specifics>

<deferred>
## Deferred Ideas

- **WR-03** (advr runs log `replay_ratio=0.0` and no `replay_windows`, the fix edits `teach_persona.py`) stays carried to Phase 32. So does **WR-04's replay-count cross-check**, which depends on it.
- **IN-01..04** from 30-REVIEW.md stay carried to Phase 32.
- **Probing the n8 control directly.** Not done: n8 is derived per stage (D-09). Revisit only if the Phase 32 n8 leg breaches the stop line.

</deferred>

---

*Phase: 31-mps-cost-probes-and-budget-commitment*
*Context gathered: 2026-09-26*
