---
phase: 31-mps-cost-probes-and-budget-commitment
plan: 03
subsystem: cost-budget
tags: [arcal-03, budget, stop-line, torch-free, ancestry, write-once]
requires:
  - 31-01 phase31_probe.build_point_record / phase25_stage_table / calibration_descent / _tracked
  - 31-02 phase31_probe.build_relearn_record and the relearn_probe_run fixture
  - phase30_points._tracked_json / calibration_record (committed blobs only)
provides:
  - scripts/phase31_budget.py: derive(), build_record(tracked), require_no_sweep_point(tracked), emit(), main(), STOP_LINE_FACTOR, BUDGET_RECORD, PINNED_MODULES
  - tests/test_phase31_budget.py: formula recompute, branches, stop line, torch-free subprocess, producer-fed, recompute-from-committed, ARCAL-03 ancestry
affects: [31-05, 31-06, 32]
tech-stack:
  added: []
  patterns: [pure derive + committed-blob build_record + write-once emit, refusal-after-sweep only in emit]
key-files:
  created: [scripts/phase31_budget.py, tests/test_phase31_budget.py]
  modified: []
decisions:
  - Q1 locked: n8 train = Phase 25 n8 ratio-0 twin + STEP_BUDGET x replay_windows(n8) x per_window; other n8 stages = n64 x MEDIAN of the 6 matched ratios
  - Q2 locked: FULL_K re-score priced per admitted point as max over rungs of (draw x FULL_K/k + remainder), inside relearning.conditional, never scheduled
  - derive scales the re-score by the relearn record's own k (proved == CURVE_K in build_record), not by a bare CURVE_K
  - conditional[leg] keys are strings ("1".."5") so the record survives the JSON round trip the recompute test compares
requirements-completed: []
# Contributes to ARCAL-03; the orchestrator decides requirement ticks at phase close.
metrics:
  duration: ~45 min (about 22 min of it waiting on the census run)
  completed: 2026-09-26
---

# Phase 31 Plan 03: Budget derive, emit and ARCAL-03 ancestry Summary

`scripts/phase31_budget.py` is a torch-free emitter. It derives the v5.0 sweep and relearning budget, and the Phase 32 stop line (1.5 x `sweep.scheduled.high`), from the two committed probe records plus the 12 committed Phase 25 adv points, `phase25_recall.json` and the calibration recipe. Every read goes through `phase30_points._tracked_json`, and every source carries its sha256. The emit is write-once and refuses once any `results/phase32_point_*` is tracked. The ancestry guards bind as soon as the records are committed.

## Commits

| Task | Gate | Commit | Subject |
|------|------|--------|---------|
| 1 | RED | eda28bf | test(31-03): add failing tests for the torch-free budget derive |
| 1 | GREEN | 79c2863 | feat(31-03): torch-free budget derive with the locked D-07..D-10 formula |
| 2 | RED | 52f154d | test(31-03): add failing emit, recompute and ARCAL-03 ancestry tests |
| 2 | GREEN | 7217152 | feat(31-03): budget build_record from committed blobs and write-once emit |

## Verification (committed tree at 7217152)

- `tests/test_phase31_budget.py` gives **19 passed**. It takes the honest untracked branches, because there is no budget, no probes and no sweep points yet.
- The VALIDATION quick run gives **181 passed** in 207 s: `tests/test_phase31_budget.py test_phase31_probe test_phase30_points test_phase30_calibration test_phase29_prereg test_phase23_resume`.
- The censuses plus Phase 27 give **93 passed** in 22.1 min: `tests/test_lora_inject.py test_phase21_sc5 test_phase25_venue test_phase25_driver test_phase27_relearn`.
- `ruff check` and `ruff format --check` are clean on both files.
- Census hygiene:
  - No `== 10`, `!= 10`, `train_arm(` or skip appears in the test file.
  - The module contains no `os.replace` and no `dp_n` string. It writes through `phase25_run.atomic_write_json`.
  - The only typed number in the module is `STOP_LINE_FACTOR`. The "10 non-control points" note is computed from `POINT_KEYS()` and `LEGS`.
- A sanity run of derive on the real Phase 25 table reproduces RESEARCH's figures:
  - phase25_sum_hours is 12.563 h without recall and 15.880 h with it;
  - the train spread is 0.974-1.141 and the draw spread 0.755-1.107.

## Deviations from Plan

1. **[Orchestrator override] The full suite was not run.** The plan's Task 2 acceptance asks for a full-suite EXIT=0. The orchestrator's gotchas say not to run it (~25 min). I ran the targeted quick run and the censuses above instead. The orchestrator owns the full-suite gate.
2. **[Plan prose vs code] Provenance helper.** `phase31_probe._write_record(out_path, record, run)` requires a probe `run` blob for `provenance.run`, and the budget has none. `emit()` therefore reuses `phase31_probe.calibration_descent()` for the `calibration` block and builds the `provenance` block itself, in the `phase30_calibration` shape: module_sha256 over PINNED_MODULES, git_sha, head_at_write and written_utc. `build_record` adds neither block, as the plan requires.
3. **[Rule 2] The re-score k comes from the relearn record's own `k`.** The plan's formula names `CURVE_K`. `build_record` proves `relearn["k"] == CURVE_K` and `relearn["rungs"] == RUNGS`, so the two agree on the committed record. The fixture record has k = 8 while `phase29_prereg.CURVE_K` is 16, so scaling by a bare CURVE_K would misprice any record not taken at CURVE_K.
4. **[Shape] Branch detail.** `sweep.per_leg[leg]` holds `{points, learnable, unlearnable}`, and each branch is `{legs: {leg: "learnable"|"unlearnable"}, estimate, low, high, hours}`. `ratios` is keyed by stage directly, with `derived.derived_leg` = "n8", because there is exactly one unprobed leg.
5. **[Test shape] The recompute test's honest branch patches `phase31_budget._sha256`** for the two absent synthetic probe paths. It also asserts that `sources` is exactly {both probes, the 12 Phase 25 records, the recall record, the calibration}.
6. **[Test addition]** `test_budget_path_is_the_preregistered_one`.

## For 31-05 / 31-06

- **Emit command (31-06):** run `.venv/bin/python scripts/phase31_budget.py` with no arguments, from a clean tree (`scripts src results`). Then commit `results/phase31_budget.json` alone.
- Order and preconditions:
  - Both probe records must be committed at HEAD first, in separate commits (point, then relearn).
  - The budget must be a later, separate commit. `_assert_frozen_before` rejects same-commit pairs.
  - No `results/phase32_point_*` may be tracked, or emit refuses.
- After the budget is committed, `test_committed_budget_recomputes_from_committed_files` compares `build_record(tracked)` with the committed record minus `{provenance, calibration}`. Both ancestry tests then go non-vacuous.
- The refusal fires if `recipe[leg].max_steps != STEP_BUDGET`, the relearn k or rungs are not CURVE_K / RUNGS, or `per_window <= 0`. The last one means the MPS probe's train is not longer than the Phase 25 n64 twin's train (~80 s). A probe with 256 replay windows per step should clear that easily.
- Phase 32 reads `results/phase31_budget.json::stop_line.seconds` and never retypes it. Pitfall 5 (the recall producer is needed for the non-control points) is in `notes`.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase31_budget.py, tests/test_phase31_budget.py
- FOUND commits: eda28bf, 79c2863, 52f154d, 7217152
