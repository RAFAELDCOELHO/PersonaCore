---
phase: 32-replay-bearing-frontier-re-run-and-verdict
plan: 01
subsystem: v5.0 frontier guards (phase30_points own-control reader, WR-05 AST guard, pin tripwire)
tags: [ast-guard, own-control, replay, provenance-pin, dated-continuation]
requires: []
provides:
  - "_wr05_failures exempts \"control_readings\" only as a dict-literal key or subscript string (D-17)"
  - "own_control refuses a control whose replay.per_step != [replay_windows] * max_steps (D-19, WR-04)"
  - "recipe_identity refuses a REPLAY_SOURCE entry whose module is not teach_persona (D-10, IN-04)"
  - "_SUPERSEDED_PINS registers fix SHA f3785da23a6afe2bdf8ae62907bbe34d043eca20"
affects: [32-02, 32-03, 32-04, 32-05, phase 33 own_control consumers]
tech-stack:
  added: []
  patterns: [dated in-place continuation, AST-computed natural RED cases, _SUPERSEDED_PINS tripwire]
key-files:
  created: []
  modified:
    - tests/test_phase30_points.py
    - scripts/phase30_points.py
    - tests/test_phase30_calibration.py
decisions:
  - "The D-19 _SUPERSEDED_PINS inline comment moved to its own line above the SHA (same text): inline it was 110 chars and failed ruff E501"
requirements-completed: []
# This plan contributes to AFRONT-01/02 (the guard, own_control replay proof and pin registration they depend on) but does not complete them.
metrics:
  duration: ~20 min
  completed: 2026-09-27
  tasks: 3
  files: 3
---

# Phase 32 Plan 01: Pre-launch guard, own_control replay check and pin registration Summary

The WR-05 guard now lets the frontier write `verdicts.control_readings`, but only as a JSON key, and every carrier form is still blocked. `own_control` refuses a control that did not draw its recipe's replay on every step. `recipe_identity` refuses a foreign replay module. The fix SHA is registered in the pin tripwire.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 D-17 guard continuation | `b9c84c89dd407adab0f6fe95278465110a977d69` | tests/test_phase30_points.py |
| 2 D-19 WR-04 replay + D-10 IN-04 (fix) | `f3785da23a6afe2bdf8ae62907bbe34d043eca20` | scripts/phase30_points.py, tests/test_phase30_points.py |
| 3 D-19 SHA registration | `e62d1c6b5f957b9b5982e5480c01037db7428568` | tests/test_phase30_calibration.py |

`git log --format=%H 4339f2b..HEAD -- scripts/phase30_points.py` prints exactly the 4 `_SUPERSEDED_PINS` SHAs: CR-01, WR-04, WR-05 and f3785da.

## RED/GREEN evidence

- **D-17 natural RED.** Run against the unedited guard, `test_ast_guard_d17_natural_cases` failed on its first assertion, **`flagged == other_lines`**, and not on the disjointness check. This matches the plan's simulation. For phase29_prereg.py the guard flagged `{395, 423, 489}` while `other_lines` was `{423}`: the subscript at 395 and the dict key at 489 were flagged. After the continuation the test is green on all three scripts.
- `test_ast_guard_d17_allows_control_readings_only_as_a_json_key` was also RED before the edit, because both exempt plants were flagged. It is green after.
- **Plant count added: 3**, namely `getattr(phase25_promotion, "control_readings")`, `phase25_promotion.control_readings` and `{"record_kwargs": 1}`. The `from phase25_promotion import control_readings` import plant already existed as `promotion.py`, so it was not duplicated. All plants were flagged both before and after the edit.
- **D-19/IN-04 RED.** After the fixture gained the replay block and before the fix, 4 tests failed: all 3 `test_wr04_own_control_refuses_a_control_without_replay_counts` cases (no replay key, one step short, one step low) and `test_in04_recipe_identity_refuses_a_foreign_replay_module`. None of them raised SystemExit. All 4 were green after the fix. The existing `_good_control` acceptance tests stayed green.
- **Tripwire natural RED.** At f3785da, `test_the_phase30_points_pin_continuation_is_a_tripwire` failed as the plan expected. It was green after e62d1c6.
- **AST literal check.** The numeric Constants in `own_control` are `[]`, so no 32, 256 or 200 appears. Checked with:
  `python -c "import ast; t=ast.parse(open('scripts/phase30_points.py').read()); f=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='own_control'][0]; print(sorted({n.value for n in ast.walk(f) if isinstance(n,ast.Constant) and type(n.value) in (int,float)}))"`

## Tests run

- Census gate (10 tests): green after Task 1 (10 passed) and after Task 3 (10 passed, 5.3 s). Its tripwire member was RED only between Task 2 and Task 3, as the plan expected.
- Plan end: `tests/test_phase29_prereg.py tests/test_phase30_points.py tests/test_phase30_calibration.py tests/test_phase31_probe.py tests/test_phase31_budget.py` gave **178 passed** in 60 s.
- `tests/test_phase30_points.py` alone gave 39 passed.
- ruff check and ruff format --check are clean on all 3 files.

## Deviations from Plan

- **The inline comment was moved (lint).** The plan's `# Phase 32 D-19 WR-04 replay + D-10 IN-04, 2026-09-27` would have made a 110-char line, which fails ruff E501. The identical text now sits on its own line directly above the SHA.

## Plan-premise falsification / disclosure

- **Stale-pin disclosure, broader than the plan states.** The plan names results/phase31_probe_point.json and results/phase31_budget.json. Measured: **all three** Phase 31 records pin `module_sha256["scripts/phase30_points.py"] = 46c9785f…bfcc5`. The third is results/phase31_probe_relearn.json. That hash equals the pre-fix module (`git show f3785da^:scripts/phase30_points.py | shasum -a 256`), so the D-19 fix makes all three stale. None of them has a tripwire. They are write-once and not re-emitted, and per D-19 only the calibration record is covered by `_SUPERSEDED_PINS`.
- No other pinned module was touched. The only pinned module edited was scripts/phase30_points.py.
- IN-01..03 were not touched and remain carried.

## Known Stubs

None.

## Self-Check: PASSED

- Commits b9c84c8, f3785da and e62d1c6 are present on main.
- The modified files exist. No STATE, ROADMAP or REQUIREMENTS edits were made.
