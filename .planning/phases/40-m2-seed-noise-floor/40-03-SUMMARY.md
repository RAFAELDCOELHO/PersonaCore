---
phase: 40-m2-seed-noise-floor
plan: 03
subsystem: pre-registration
tags: [prereg, noise-01, noise-02, recall-floor, gap-floor, d-02, d-03, d-04, d-07, d-08b, d-09, d-10, d-12, d-13, d-15, r-1, r-2, r-3]
requires:
  - scripts/phase40_prereg.py (plan 02: ENTRIES, fills, SEEDS, rulings)
  - scripts/phase19_run.py (_pooled_rows, NOISE_FLOORS_PATH, RETRAIN_SCORES_PATH)
  - scripts/phase19_erasure.py (nontarget_rows, nontarget_deltas, nontarget_noise_floor)
  - scripts/phase36_ledger.py (_attempts, run_id), scripts/phase39_prereg.py (n1)
provides:
  - scripts/phase40_prereg.py section (7) — the pure estimator functions the driver will call
  - tests/test_phase40_prereg.py section (8) — 19 new CPU tests on committed v3.0 records and truth tables
affects:
  - plan 04 (review with Rafael of these functions before any driver code)
tech-stack:
  added: []
  patterns: [pinned v3.0 reductions called, never re-implemented; ruling globals read at call time and monkeypatched in tests]
key-files:
  created: []
  modified:
    - scripts/phase40_prereg.py
    - tests/test_phase40_prereg.py
decisions:
  - "seed_outcomes pairs starts with their end/lost lines through phase36_ledger._attempts rather than re-implementing the pairing"
  - "d12_table returns {per_slot: {slot: {v3_delta_taught_to_m2, pairs}}, criterion: False}"
requirements-completed: []
completed: 2026-10-05
---

# Phase 40 Plan 03: Pure estimator functions Summary

This plan adds the functions behind plan 02's written rule to `scripts/phase40_prereg.py`. They cover the 27-denominator rows, v3.0's pair statistic, the group floors with their extras, the recall floor, the gap floor, the D-12 table, the D-07/D-08b readings, seed outcomes with the R-3 b manifest checks, and the D-13 reduction. On the committed records they reproduce v3.0's 0.14814814814814814 and 0.2592592592592592.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | d759725 | feat(40-03): phase40 prereg rows, pair statistic, group floors and recall floor |
| 2 | 8e9a912 | feat(40-03): phase40 prereg gap floor, D-12 table, D-07/D-08b readings, seed outcomes, R-3 b checks, D-13 reduction |

## RED outputs

Task 1: the seven tests were written before any function existed. Command: `-k "rows or denominator or pair or floor or extras"`
```
7 failed, 27 deselected in 1.42s
   1 E       AssertionError: meta-guard: 0 defs named pair_d
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'a2_scope'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'group_floor'
   2 E       AttributeError: module 'phase40_prereg' has no attribute 'pair_d'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'per_slot_spread'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'recall_floor'
```
Task 2: the twelve tests were written before any function existed. Command: `-k "gap or d12 or d07 or d08 or seed_outcomes or d13"`. The one test that passed is plan 02's `test_approval_d13_nll_count_is_derived`.
```
12 failed, 1 passed, 33 deselected in 1.53s
   3 E       AttributeError: module 'phase40_prereg' has no attribute 'committed_adapter_off'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'd07_reading'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'D08B_OUTCOMES'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'd13_block'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'dropped_attempt_dir'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'gap_noise_floor'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'lost_attempts'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'relaunch_declaration_name'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'seed_outcomes'
   1 E       AttributeError: module 'phase40_prereg' has no attribute 'v3_delta_taught_to_m2'
```
The first GREEN run of Task 2 failed in two places (`2 failed, 44 passed in 4.18s`):
- The `extra` plant in the manifest truth table: the kept-item failure text `kept[0] keys are not ['from', 'path', 'sha256'] (c)` did not name the planted key. The message now includes the item's actual keys.
- The every-function census: it reported `['_text']`. The manifest test now calls `phase40_prereg._text` directly.

## Verify and acceptance (as printed)

Task 1 verify: `7 passed, 27 deselected in 1.70s`; `ruff check`: All checks passed!
Task 1 acceptance (`a2_scope`/`a2_rows`/`pair_d` on the committed Phase 18, replicate and retrain records):
```
0.14814814814814814 0.2592592592592592
```
The whole file after Task 1 gave `34 passed in 4.93s`. Census tests on that tree (`tests/test_phase35_prereg.py tests/test_phase21_sc5.py tests/test_phase23_resume.py -k "slot_census or slot_ordering or sc5 or ten or inert or train_arm"`) gave `13 passed, 88 deselected in 23.79s`.

Task 2 verify (`tests/test_phase40_prereg.py tests/test_phase35_prereg.py tests/test_phase21_sc5.py`, then `ruff check .` and `ruff format --check .`):
```
138 passed in 31.32s
All checks passed!
360 files already formatted
```
Task 2 acceptance:
- `-k "gap or d12 or d07 or d08 or seed_outcomes or d13"` gave `13 passed, 33 deselected in 1.11s`.
- `test_census_every_phase40_prereg_function_has_a_cpu_test` passes with no exclusion. The whole file gave `46 passed in 3.74s`.
- `git ls-files 'results/phase40_*'` printed nothing (run after 8e9a912).
- `grep -nE "train_arm\(|os\.replace|inject_lora|== 10"` over both files printed nothing.

Full suite on the committed tree at 8e9a912 (`.venv/bin/pytest -q -p no:cacheprovider`, nohup):
```
4346 passed, 4 skipped, 83 warnings in 3192.66s (0:53:12)
EXIT=0
```

## Values reproduced on committed records (asserted in tests)

- `pair_d(phase18, replicate)`: d 0.14814814814814814, deltas (0.0, 0.0, 0.0, 0.0, 0.03703703703703698, 0.11111111111111105, 0.14814814814814814). This equals `results/phase19_noise_floors.json` nontarget_noise_floor.value.
- `pair_d(phase18, retrain)`: d 0.2592592592592592, deltas (0.0, 0.0, 0.0, 0.0, 0.2592592592592592, 0.0, 0.11111111111111116).
- `slot_rows(a2_rows(retrain))`: every core slot has n_questions 27, with per_tier 14 core_taught and 13 core_held_out. Counts: pet_name 0, house_number 17, hometown 18, birth_year 18, person_name 26, cat_name / sibling_name / street 27.
- `gap_noise_floor` over the committed seed_a/seed_b on - off equals `phase19_floor.DIALOGUE_PPL_NOISE_FLOOR`. Before writing the test, I measured `abs(a-b)` as 0.005214448168350039, equal to it.
- `d12_table`: the same-seed (phase18 vs retrain) m2_minus_full equals `v3_delta_taught_to_m2()` on every slot: house_number -0.2592592592592592, hometown -0.11111111111111116, the other five 0.0.
- `committed_adapter_off()` reads 4.573349214207799. The CPU value 4.573348505014267 appears only in the test, where it drives the R-1 truth table.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's S' = 3 truth-table triple (d = 0, 1/27, 4/27) cannot occur**
- **Found during:** Task 1, while writing test_group_floor_truth_table.
- **Issue:** d is a max over slots of |rate difference|, which is a metric. d(i, j) = 0 means rows i and j are equal, so d(i, k) = d(j, k). No three seeds can give 0, 1/27 and 4/27.
- **Fix:** I used two triples. The first gives (1/27, 4/27, 4/27), which also covers "ties keep both pairs". The second gives (0, 1/27, 1/27), which covers min 0. The floor, max, min and math.comb(3, 2) pair count are asserted on both.
- **Files modified:** tests/test_phase40_prereg.py
- **Commit:** d759725

**2. [Rule 3 - Blocking] The every-function census needed a tested helper**
- **Found during:** Task 2
- **Issue:** I added a private `_text(value)` helper (a str that is non-empty after strip), shared by the manifest and declaration checks. The census flagged it as untested.
- **Fix:** test_seed_outcomes_dropped_manifest_truth_table now calls `phase40_prereg._text` directly. There are no census exclusions.
- **Commit:** 8e9a912

### Notes
- The new prereg section is numbered "(7) THE PURE ESTIMATOR FUNCTIONS", not "(9)" as the plan says, because the file's sections end at (6). The tests are under "(8) PLAN 40-03" because the test file already has (1)-(7).
- `pair_d` makes no direct `max` call. The AST gate checks this, and a planted `max(deltas)` version fails it. `d08b_reading` uses `max` for `max_abs_rate_difference`, as the plan specifies. `per_slot_spread` uses `max` and `min` for the range, and `group_floor` uses them for the extras.
- There is no literal pair count anywhere. Pairs come from `itertools.combinations` through `_pairs`, which refuses with INSUFFICIENT_SEEDS below `phase35_prereg.ENTRIES["e2_min_seeds"]`.
- No `phase37_prereg.draw_identity` call was needed: d07_reading takes the caller's `tensor_identical` flag, per the plan's action text.
- STATE.md, ROADMAP.md and REQUIREMENTS.md were not touched. No gsd-sdk mutation handler was called.

## Known Stubs

None.

## Threat Flags

None. The functions read committed JSON only (NOISE_FLOORS_PATH, RETRAIN_SCORES_PATH). The `DROPPED_ROOT` paths are names only: the prereg writes and deletes nothing.

## Self-Check: PASSED

- scripts/phase40_prereg.py and tests/test_phase40_prereg.py are modified, and both are in d759725 and 8e9a912.
- `git log --oneline` shows d759725 and 8e9a912 on main.
