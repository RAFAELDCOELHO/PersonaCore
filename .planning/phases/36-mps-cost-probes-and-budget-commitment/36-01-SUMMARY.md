---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 01
subsystem: pre-registration
tags: [prereg, cost-probes, budget, ancestry]
requires: [scripts/phase35_prereg.py public names, scripts/phase25_record.py]
provides:
  - scripts/phase36_prereg.py (ENTRIES x17, PROBE_GLOB, PROBE_FRONTS, PROBE_RECORDS, probe_record, E3_PROBE_POINT_KEY, E3_PROBE_POINT_RECORD, divergence, exceeds, prove_p22)
  - tests/test_phase36_prereg.py (_untested_functions(module_name, module_source, test_source), reusable by later Phase 36 tests)
affects: [36-02..36-08]
tech-stack:
  added: []
  patterns: [four-field entries, import-time _prove, ancestry guard with natural RED]
key-files:
  created: [scripts/phase36_prereg.py, tests/test_phase36_prereg.py]
  modified: []
key-decisions:
  - "Comparator rows are built by a small _row() helper returning MappingProxyType; it is called by the test so the CPU-test census stays green"
  - "The record-priced stages (e4_canary_scoring_price, e1_ordering_price, e1_calibration_price) are resolved on tracked records in the test too (T-36-04), not only the comparator rows"
requirements-completed: []  # contributes to COST-01/COST-02; the orchestrator/verifier decides ticks (they close in plans 07/08)
metrics:
  completed: 2026-10-02
  tasks: 2
  files: 2
---

# Phase 36 Plan 01: Phase 36 Pre-Registration Summary

Torch-free `scripts/phase36_prereg.py` freezes 17 four-field entries (25% divergence and its 8-row comparator map, T <= 800 with an import-time P22 proof, E4 reserve/pricing/first-point check, E1 ordering/calibration prices, high-bound rules with ruling alternatives, 1.5x stop factors, projection rule, S >= 3 cut-table floor, S = 5 proposal, D-15 cut order) and the five probe record paths, committed before any `results/phase36_*` file, with an ancestry-guarded test file.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 prereg module | 81c75d3 | scripts/phase36_prereg.py |
| 2 tests | 9f75933 | tests/test_phase36_prereg.py |

## Verification (real output)

- Task 1 verify: `17 ('results/phase36_probe_e1.json', 'results/phase36_probe_e2.json', 'results/phase36_probe_e3.json', 'results/phase36_probe_e5.json', 'results/phase36_probe_e6.json') results/phase25_point_dp_n8_sigma0p500000.json False`
- `git log --format=%H -- scripts/phase36_prereg.py | wc -l` -> 1; `git ls-files 'results/phase36_*' | wc -l` -> 0; `git diff --quiet HEAD~1 HEAD -- scripts/phase35_prereg.py` -> exit 0.
- Slot census over the new module before commit: `[]`.
- `pytest -q tests/test_phase36_prereg.py` -> `17 passed in 2.79s` (0 skipped).
- Clean tree after both commits: `pytest -q` over test_phase36_prereg, test_phase35_prereg (whole file, covers -k "census or ordering or frozen"), test_phase21_sc5, test_lora_inject, test_phase29_prereg, test_phase18_prereg, test_phase20_prereg, test_phase25_prereg, test_phase25_record, test_phase25_driver, test_phase23_ctrl, test_phase21_unit_continuation, test_phase30_calibration, test_phase25_epsilon -> `399 passed in 66.01s`.
- ruff check + ruff format --check: green on both files.
- RED legs observed inside the tests: ancestry `CalledProcessError` on scripts/phase35_prereg.py; `prove_p22(20000)` raises SystemExit matching "RECIPE-04" (onset 0.7890371982939541 measured before writing the test; 800 -> 0.15780356992036104); planted proposer/forbidden-phrase/skip/untested-def copies all red.

## Premises measured (all held)

Every historical value in the plan's interfaces block was printed this session and matched: phase19_arm_erased 68.58400233189265, phase19_arm_retrain 46.61799373229345, phase25 point training 209.06438398361206, phase25_recall scoring 1246.8666050434113, phase26 canary scoring 5556.242378950119, collateral curve 6.959359816710154, cal-erased 10.389092532793681, calibration curve 7.0145487507184345, phase23 control-floor per-seed 78.37..80.34, phase31 total 7422.866891449317, phase17 report regex -> ['2.1']. STEP_BUDGET 200, E3_SIGMAS (0.0, 0.5, 1.0), E3_N 8, e2_min_seeds 2, mps_ceiling_hours 90. None of these numbers is typed in the module; only paths and key paths.

## Deviations from Plan

1. **[Rule 2 - Added] `_row()` helper in the module.** The plan specifies MappingProxyType rows but no constructor; a helper keeps the 8 rows uniform. Because the CPU-test census covers every module-level def, the test calls `phase36_prereg._row(...)` directly.
2. **[Rule 2 - Added] Record-priced stages resolved in the test.** Test 7 also resolves `e4_canary_scoring_price`, `e1_ordering_price` and both `e1_calibration_price` sources on tracked records (T-36-04 names "each" record; the plan's test list covered only comparator rows).
3. **Minor plan/pattern line-number drift (no behavioral effect):** 36-PATTERNS cites phase35_prereg `_prove` at :675-678; it is at :136-139 (the :675-678 region is inside `_ENTRIES`). 36-PATTERNS' `_HEAVY` includes `phase26_canary`; the plan's test 11 list omits it, and the plan was followed.
4. **`_insert_at` imported from tests/test_phase35_prereg.py** (alongside `_slot_census_failures`) rather than copied, for the planted-copy AST legs.

## Carry into wave 2 (real names)

- Module: `scripts/phase36_prereg.py`; import as plain `import phase36_prereg`.
- `phase36_prereg.ENTRIES[<name>]["value"]` with names: divergence_tolerance, divergence_comparators, uncompared_stages, e3_max_steps, e3_probe_steps, e4_reserve_points, e4_canary_scoring_price, e4_first_point_check, e1_ordering_price, e1_calibration_price, high_bound_rule, front_stop_factor, stop_line_factor, projection_rule, cut_table_min_seeds, e2_proposed_seed_count, cut_order.
- Comparator row keys: id, front, probe_field, historical_path, historical_key, unit, gated. Row ids: r1b_e1_k48, e2_a2_pass, e3_t200_train, e3_t200_score, e3_t800_linearity, e5_clearance, e2_training_context, e1_phase31_beside (only row with probe_field None; ungated). e5_clearance's historical_key is a regex str over results/phase17_personas_report.md; e3_t800_linearity has historical_path/key None.
- Probe-record field names the comparator rows bind later probe schemas to: `runs[*].total_seconds` (E1), `a2_pass.total_seconds` (E2), `t_step_budget.train_seconds` / `t_step_budget.score_seconds` / `t_step_budget.loop_seconds` / `t_step_budget.steps` / `t_max_steps.loop_seconds` / `t_max_steps.steps` (E3), `clearance.total_seconds` (E5), `train reps outer_seconds` (E2 context, free text).
- `PROBE_GLOB = "results/phase36_probe_*.json"`, `PROBE_FRONTS = ("e1","e2","e3","e5","e6")`, `PROBE_RECORDS`, `probe_record(front)` (refuses e4 and any unknown front).
- `E3_PROBE_POINT_KEY = "dp_n8_sigma0p500000"`, `E3_PROBE_POINT_RECORD = "results/phase25_point_dp_n8_sigma0p500000.json"`.
- `divergence(probe, historical)`, `exceeds(probe, historical)`, `prove_p22(steps)`.
- `high_bound_rule["ruling_alternatives"]`: a2_draw_basis ("k78","at_cap"), single_run_draw_loop ("within_run","spread_scaled"), e1_calibration ("records","probe_scaled").
- Test helper: `from test_phase36_prereg import _untested_functions` with signature `(module_name, module_source, test_source)`.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase36_prereg.py (81c75d3)
- FOUND: tests/test_phase36_prereg.py (9f75933)
