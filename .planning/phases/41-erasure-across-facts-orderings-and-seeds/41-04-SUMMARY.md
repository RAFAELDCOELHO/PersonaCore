---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 04
subsystem: erasure-prereg
tags: [phase41, prereg, erase-07, d-22, d-23, d-24, d-26, d-05, d-02, d-13, r-3b]
requires:
  - scripts/phase41_prereg.py parts 1-2 (41-02 fills and ENTRIES; 41-03 gate composition and readings)
  - scripts/phase35_prereg.py (e1_stop, NOT_REACHED), scripts/phase36_ledger.py (_attempts, run_id)
  - scripts/phase40_prereg.py:1391-1583 (the R-3 b readers copied per unit)
  - results/phase36_budget.json (front_hours, stop_line_hours, unit_prices.e1_ordering_seconds)
provides:
  - "units and order: prep_unit, cell_unit, PREP_UNITS (4, seed-major), CELL_UNITS (16), UNITS (20), unit_key, unit_record, pair_units"
  - "ERASE-07 stop: stop_readings, driver_stop (equal to phase35_prereg.e1_stop on all 63 complete reads sequences); D-26: CONFIRMATION_KEYS, confirmation_failures, confirmation_hours"
  - "D-05 / D-02 / D-13: VARIANTS (ADAPTIVE, STATIC), ordering_cost_fits, alternative_variant, rerank_points, d02_check, control_gap_check"
  - "D-22 / D-24: unit_outcomes, pending_units, pair_progress; D-23: RESUME_ROOT, RESUME_DECLARATION_KEYS, resume_declaration_name, resume_declaration_failures, e1_pause_due, pause_notice"
  - "R-3 b per unit: DROPPED_ROOT, DROPPED_MANIFEST, DROPPED_MANIFEST_KEYS, RELAUNCH_DECLARATION_KEYS, lost_attempts, dropped_attempt_dir, _text, _approved, dropped_manifest_failures, relaunch_declaration_name, relaunch_declaration_failures, latest_head_failures"
affects: [41-05, 41-07, 41-10]
tech-stack:
  added: []
  patterns: [phase40_prereg R-3 b readers copied with seed -> unit; every new def called as phase41_prereg.<fn>( in the tests]
key-files:
  created: []
  modified: [scripts/phase41_prereg.py, tests/test_phase41_prereg.py]
decisions:
  - "driver_stop returns None (continue) for a strict GRID prefix with no stop and NOT_REACHED only once every GRID checkpoint is read; e1_stop refuses partial readings, so equality is proved on the complete sequences and the partial ones are tested separately"
  - "confirmation_failures takes reads as an optional argument (the behaviour's confirmation_failures([]) has one argument); given reads it also refuses a zero K = 16 read without its confirmation and a k48_zero disagreeing with the read"
  - "e1_pause_due checks each declaration against its own e1_hours_at_pause (keys, cells, approved); matching that value to the pause notice is the driver's resume_declaration_failures call"
requirements-completed: []
# 41-04 contributes to ERASE-04, -07 and -10 (written rules the driver will call). It completes none of them: no record exists yet.
metrics:
  duration: ~10 min (commits 13f7f36 10:09, f7d8439 10:13 -0300; previous HEAD f15703b 10:03)
  completed: 2026-10-08
---

# Phase 41 Plan 04: phase41_prereg part 3 (operational rules) Summary

This plan finishes the pre-registration with the rules the driver will only call:
- the 20 units and their order;
- the per-checkpoint stop, proved equal to `phase35_prereg.e1_stop`;
- D-26's confirmation accounting;
- the D-05 variant, D-02 equality and D-13 control-gap rules;
- the D-23 pause and its resume declaration;
- Phase 40's R-3 b crash readers, re-keyed per unit.

All of them are pure functions appended to `scripts/phase41_prereg.py`. No `results/phase41_*`
file exists.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | 13f7f36 | units and order, stop_readings / driver_stop, D-26 accounting, D-05 / D-02 / D-13 rules, plus their tests |
| 2 | f7d8439 | unit outcomes, pair progress, D-23 pause and resume declaration, R-3 b readers per unit, plus their tests |

## RED outputs (tests first)

- Task 1, tests appended before the code: `6 failed, 45 passed`. Every failure was
  `AttributeError: module 'phase41_prereg' has no attribute ...` (for example `control_gap_check`).
- Task 1, first GREEN run: `1 failed, 50 passed`. The every-function census flagged the private
  helper `_is_seconds`. I added `test_is_seconds_helper`, which made it `52 passed`. ruff then
  flagged two E501 lines in the new code, which I split.
- Task 2, tests appended before the code: `5 failed, 52 passed`, all `AttributeError`.
- Task 2, first GREEN run: `1 failed, 56 passed`. The census flagged `_prove_units`. I added
  `test_prove_units_helper`, which made it `58 passed`. One test line was over 100 characters (E501),
  and I split it.

## Acceptance lines (printed at the working tree of each commit)

Task 1:
```
20 prep_greedy_seed1337 cell_sibling_name_gradient_seed2024 (0, 16, 32, 48, 64) (0,) 48
```
`-k driver_stop_equals_e1_stop`: `1 passed, 51 deselected`. The enumeration has 63 complete
sequences (31 stopped + 32 full-grid with no stop) and 30 partial ones. I printed these counts from
`test_phase41_prereg._read_sequences()`. The test asserts `len(complete) >= 2 ** len(GRID)` (32).
Across those sequences the stops seen are exactly `{16, 32, 48, 64, 128, NOT_REACHED}`.

Task 2:
```
data/phase41_dropped data/phase41_resume ('e1_hours_at_pause', 'cells', 'approved') data/phase41_dropped/v6_41_E1_cell_pet_name_greedy_seed1337_2026-10-09T010203 True False
```
`test_census_every_phase41_prereg_function_has_a_cpu_test` is inside the `58 passed` run.

## Test counts

- `tests/test_phase41_prereg.py`: `58 passed` (45 from 41-02/41-03 + 13 new).
- Gate list (`tests/test_phase41_prereg.py tests/test_phase35_*.py tests/test_phase36_*.py
  tests/test_lora_inject.py tests/test_phase21_sc5.py`): `457 passed in 91.04s`. That is 444 at
  41-03 plus the 13 new tests. The list includes the plan's quick legs (`test_phase35_prereg.py`,
  `test_phase36_caps.py`, `test_phase21_sc5.py`).
- `ruff check .`: All checks passed. `ruff format --check .`: 364 files already formatted.
- `git ls-files 'results/phase41_*'` and `find results -maxdepth 1 -name 'phase41_*'`: both empty.
- `git diff -U0 | grep -nE "== 10|os\.replace|inject_lora|train_arm\(|ratchet_k"`: exit 1 (no match).
- `shasum -a 256 scripts/phase41_prereg.py` at f7d8439:
  `fd5feb1b965498f7943b9c686087b1eeb7a76b5382688a419dc84ee5bf699cf7`.

## Deviations from Plan

The plan 05 review can rule on each of these.

1. **`driver_stop` on a partial reads sequence returns `None`, not NOT_REACHED.**
   - What the plan says, in two places:
     - must_haves: "driver_stop(reads) returns the first checkpoint whose K = 16 read and K = 48
       confirmation are both zero, else NOT_REACHED".
     - action: "the predicate the driver applies after each checkpoint".
   - These two readings conflict. If the driver applies the predicate after each checkpoint, and
     the predicate returns NOT_REACHED for every unstopped prefix, the cell stops at the first
     non-zero read.
   - `phase35_prereg.e1_stop` itself refuses a prefix: "checkpoint X has no reading before the
     stop". CONTEXT D-09 says NOT_REACHED means "no zero confirmed by the last checkpoint".
   - So `driver_stop` returns NOT_REACHED only once every GRID checkpoint is read, and returns
     None (continue) on a strict prefix.
   - The test checks both sides. Equality with `e1_stop` holds on all 63 complete sequences. On
     all 30 partial sequences, `driver_stop` returns None and `e1_stop` raises.
2. **`confirmation_failures(confirmations, reads=None)`.**
   - The plan gives two arities:
     - action: "`confirmation_failures(confirmations, reads)`".
     - behaviour: "confirmation_failures([]) == []".
   - `reads` is optional, which satisfies both.
   - [Rule 2] Given reads, the function also refuses two things: a zero K = 16 read with no
     confirmation, and a confirmation whose `k48_zero` differs from the read. Without these, a
     dropped or edited confirmation would still pass D-26's accounting.
   - `confirmation_hours` refuses confirmations that fail `confirmation_failures`.
3. **How `e1_pause_due` judges a declaration.**
   - The plan says only declarations "with no failures count", and `resume_declaration_failures`
     needs the notice's `e1_hours_at_pause`. `e1_pause_due` has no notice.
   - So `e1_pause_due` checks each declaration against its own value. That covers keys, cells as
     distinct CELL_UNITS, a finite value and `_approved`.
   - The equality with the notice is the driver's `resume_declaration_failures` call. The
     docstring says so.
   - I added no `>= share` bound. The notice's `e1_hours` is `seconds / 3600`, which can sit one
     ulp below `share`, so that bound would refuse a genuine declaration.
   - The pause threshold compares seconds (`e1_seconds >= share * 3600`), not hours. This makes
     `share * 3600` exactly due.
4. **[Rule 2] More input guards than the plan named.**
   - `pending_units` and `unit_outcomes` refuse units outside UNITS, through `_prove_units`.
   - `lost_attempts` refuses an unknown unit. Phase 40's `lost_attempts` did not check its seed.
   - `pair_progress` refuses outcomes that lack any cell.
   - `pause_notice` refuses a missing or negative front's seconds.
   - `ordering_cost_fits`, `alternative_variant` and `e1_pause_due` take only finite reals >= 0
     (bool excluded), through `_is_seconds`.
   - `d02_check` and `control_gap_check` take only reals.
5. **`pending_units` has no `DROPPED_SEED_RERUN` switch.** It follows the plan ("rerun of a dropped
   unit always allowed under R-3 b with Rafael's manifest — D-24 has no never-rerun branch"). Its
   result is in UNITS order, not in the order of the outcomes mapping.
6. **Two private helpers with tests of their own:** `_is_seconds` and `_prove_units`. Both are
   called directly in the tests, for the every-function census.

## Known Stubs

None. Every function computes from its arguments, ENTRIES or the committed budget.

## Threat Flags

None. There is no new network, auth or write surface. `RESUME_ROOT` and `DROPPED_ROOT` are path
strings under `data/`. Nothing here writes them.
- T-41-13: `test_driver_stop_equals_e1_stop`.
- T-41-14: `test_pause_due_and_notice`. Only an approved declaration listing the cell lifts the
  pause. Negated, missing and planted declarations do not.
- T-41-15: `test_unit_outcomes`. A later attempt after a whole unit is refused, and a rerun of a
  whole or not_run unit is refused.
- T-41-16: `test_d02_check`. One ulp, NaN or inf stops.

## Self-Check: PASSED

- FOUND: scripts/phase41_prereg.py, tests/test_phase41_prereg.py (modified)
- FOUND commits: 13f7f36, f7d8439 (`git log --oneline -3`)
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched. No gsd-sdk handler was called.
