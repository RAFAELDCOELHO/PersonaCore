---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 02
subsystem: erasure-prereg
tags: [phase41, prereg, fills, erase-04, erase-07, d-26, ancestry]
requires:
  - scripts/phase35_prereg.py (fill, SLOTS, V6_RESULT_PATHS, e1_stop)
  - results/phase36_budget.json, results/phase40_noise_floor.json, results/phase19_calibration_curve.json
  - 41-01-SUMMARY.md measured premises (c12e7f5) and the 2026-10-08 orchestrator amendment
provides:
  - scripts/phase41_prereg.py fill file 1 (E1_CHECKPOINT_GRID, E1_ALTERNATIVE_ORDERING, E1_CONDITION_B_MARGIN, ENTRIES x34, D26_RULING, record paths, ORDERINGS, VALUE_NLL_SECONDS, D11_REFERENCE_*)
  - tests/test_phase41_prereg.py guards; helpers _strictly_before, _first_add (plan 12) and _typed_target_failures (plan 10)
affects: [41-03, 41-04, 41-05, 41-07, 41-10, 41-12]
tech-stack:
  added: []
  patterns: [phase40_prereg structure copied with the [phase41_prereg] tag; GRID node is the one literal-scan exemption]
key-files:
  created: [scripts/phase41_prereg.py, tests/test_phase41_prereg.py]
  modified: []
decisions:
  - "Per-NLL cost bound is computed in code: VALUE_NLL_SECONDS = unit_prices.e1_ordering_seconds / phase19_erasure.N_COMPONENTS = 1.4498666284812822; D-05 headroom GRADIENT_HEADROOM = e1_ordering_seconds / (len(GRID) x VALUE_NLL_SECONDS) = 57.599999999999994 value NLLs per gradient (forward + backward)"
  - "D-11 reference digest read from results/phase19_calibration_curve.json::adapter_in_sha256 (D11_REFERENCE_RECORD / D11_REFERENCE_KEY / D11_REFERENCE_SHA256), never typed"
requirements-completed: []
# 41-02 contributes to ERASE-03, -04, -05, -06, -07, -09, -10 (fills and written entries); it completes none of them.
metrics:
  duration: ~25 min
  completed: 2026-10-08
---

# Phase 41 Plan 02: phase41_prereg fill file 1 Summary

`scripts/phase41_prereg.py` is committed with its test file. It holds the three Phase 41 fills that
have no in-phase input: the grid (16, 32, 48, 64, 128), the "gradient" alternative ordering and the
(b) margin. It also holds 34 ENTRIES that write down D-01..D-28, with Rafael's D-26 words quoted
verbatim. No `results/phase41_*` file existed at any of these commits.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | d6f12e9 | `scripts/phase41_prereg.py` + `tests/test_phase41_prereg.py`, added in the same commit: header, paths, ORDERINGS, the three fills, the caps check, two provisional entries |
| 2 | 578011f | 34 ENTRIES, D26_RULING, `_DEFAULT`, D11_REFERENCE_* constants, `_K48_CAP`, Task 2 tests |
| 3 | 0f5b6f3 | guard tests (test file only) |

`git log --diff-filter=A` on both files prints `d6f12e9`, so both were added in the same commit.

## RED outputs (tests first)

- Task 1, before the module existed: `ModuleNotFoundError: No module named 'phase41_prereg'` →
  `1 error during collection`.
- Task 2, before the entries existed: `6 failed, 7 passed`. The failures were names/kinds,
  d26, k48, predictions, d11 reference and defaults (e.g. `AttributeError: module 'phase41_prereg'
  has no attribute '_DEFAULT'`). The 7 that passed were the six Task 1 tests plus
  `test_value_nll_bound_is_the_budget_price_over_the_components`. That test was green at RED because
  `value_nll_seconds()` already went in with Task 1, where the alternative-ordering derivation
  quotes it.
- Task 3 is guard tests only (no RED/GREEN pair). On its first run one census test failed for a
  real reason: `_untested_functions` reported `band_record`, `cell_record`, `k16_record` and
  `k48_record` because Task 1's test called them through a local alias `p.`. The tests now call
  them as `phase41_prereg.<fn>(`.

## Acceptance lines (printed by runs at HEAD 0f5b6f3)

Task 1 (`import phase41_prereg as p; print(...)`):
```
(16, 32, 48, 64, 128) 16 48 ('greedy', 'gradient') 0.2962962962962963 results/phase41_cell_pet_name_greedy_seed1337.json v6/41/E1/cell_pet_name_greedy_seed1337
```
Task 2:
```
34 5 1 ['e1_share_hours', 'e1_unit_prices']
```
Here 34 is `len(ENTRIES)`, 5 is `max_per_cell = len(GRID)`, and 1 is `committed_cap`, read from
`results/phase36_budget.json` unit_caps.E1.k48_confirms_per_cell.

- `-k "d26 or k48 or predictions or defaults"`: `4 passed, 9 deselected` (Task 2 run).
- `-k "frozen or first_added or records_at_commit"`: `3 passed, 22 deselected`.
- `git ls-files 'results/phase41_*'` and `find results -maxdepth 1 -name 'phase41_*'`: both empty
  after every task. `git status --porcelain -- scripts tests results`: empty after the Task 3 commit.
- Amendment values printed from the module: `VALUE_NLL_SECONDS` 1.4498666284812822;
  `GRADIENT_HEADROOM` 57.599999999999994; `D11_REFERENCE_SHA256`
  bc616c3667719e677532a5e56c7b8de8e2dc79e15af85ccc14bc1dcce66856da. The digest equals the
  41-01-SUMMARY measurement.
- `shasum -a 256 scripts/phase41_prereg.py` at 578011f (unchanged by 0f5b6f3):
  `5df7258cad9db5f627995d0e05ba6c3a6398fc6149411d85fdb62f6634422fe1`. Plans 03/04 will change it.

## Test counts (before the Task 3 commit, working tree = 0f5b6f3 content)

`.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_prereg.py tests/test_phase35_*.py
tests/test_phase36_*.py tests/test_lora_inject.py tests/test_phase21_sc5.py tests/test_phase23_resume.py`
→ `433 passed in 192.58s (0:03:12)`, exit 0. `tests/test_phase41_prereg.py` alone: `25 passed`.
After Task 1's commit, `test_slot_ordering_is_green_on_the_real_repo` and
`test_owner_fill_files_respect_the_caps_on_the_real_repo` gave `2 passed` with the prereg tracked.
`ruff check .`: All checks passed. `ruff format --check .`: 364 files already formatted.

## What the module holds

- Paths: RECORD_GLOB, CALIBRATION_GLOB and BAND_GLOB are selected from `V6_RESULT_PATHS` by
  equality. BUDGET_RECORD, CALIBRATION_CORPUS and NOISE_FLOOR_RECORD come from `SLOTS[...]["input_records"]`.
  ERASURE_RECORD and REPORT_RECORD are derived from RECORD_GLOB. The helpers `calibration_record`,
  `band_record`, `cell_record`, `k16_record`, `k48_record` and `run_id` prove their arguments are
  members of their sets. Per-cell paths also match neither prep glob.
- Fills are bound to their upper-cased slot names. `ORDERINGS = ("greedy", E1_ALTERNATIVE_ORDERING["value"])`.
  `phase36_caps.check_unit_caps("E1", **counts_for("e1_checkpoint_grid", ...))` runs at import, and
  no `k48_confirms_per_cell` keyword appears anywhere (AST test).
- ENTRIES: the 25 decision entries plus the nine `_DEFAULT`-labelled planner defaults
  (record_layout, alternative_variant, not_run, resume_declaration, d02_equality,
  control_gap_scope, approvals, prep_order, stop_for_rafael). Only e1_share_hours and
  e1_unit_prices are `derived`. Every source names 447747c or 3787b9d.

## Deviations from Plan

1. **[Amendment, applied as directed]** Added `value_nll_seconds()`, `VALUE_NLL_SECONDS`,
   `MAX_GRADIENTS_PER_CELL` and `GRADIENT_HEADROOM`. The alternative-ordering derivation quotes
   them with their formulas. One test checks that the bound equals the budget price divided by
   N_COMPONENTS (amendment item 2). Added `D11_REFERENCE_RECORD`, `D11_REFERENCE_KEY` and
   `D11_REFERENCE_SHA256`, read from the record. They appear in `predictions["d11_calibration_identity"]`
   and the predictions derivation. A test checks that the record is tracked, that it equals
   `phase19_run.CURVE_PATH`, and that its `adapter_in` file name equals
   `teach_persona.arm_outputs(CALIBRATION_ARM, prefix=RETRAIN_PREFIX)["adapter"]` (amendment item 1).
2. **[Rule 2 - census]** Added the private helpers `_prove_path` and `_prove_unit`, shared by the
   path functions, and a test that calls both (`test_prove_count_read_and_path_helpers`). This keeps
   the every-function census green.
3. **Literal-scan shape.** The GRID exemption replaces the GRID assignment's lines with
   `GRID = None` (same line count). A separate check, `_k_literals_outside_grid`, asserts that no
   CURVE_K/FULL_FIDELITY_K int lies outside the GRID node. A meta-guard proves the unexempted
   source does fail. VALUE_NLL_SECONDS and GRADIENT_HEADROOM were added to the float census.
4. **Task 2 test granularity.** `test_d11_reference_digest_is_read_from_the_committed_record` and
   `test_value_nll_bound_is_the_budget_price_over_the_components` are extra tests the amendment
   required.
5. **Wording.** In Task 1's derivation, "Ties by address" became "ties by address (layer,
   projection, j)" in Task 2's commit, to match the plan's literal phrase.

## Observations

- `GRADIENT_HEADROOM` is the same as N_COMPONENTS / len(GRID) = 288/5. The price cancels out. It
  means one gradient (forward + backward) may cost about 57.6 value NLLs. Put as backward/forward,
  backward may cost up to about 56.6 forwards. CONTEXT D-05 said "~57x".
- The entries keep D-26's reading "4 beyond the first" (max_per_cell = len(GRID) = 5). That reading
  comes from 41-DISCUSSION-LOG, not from Rafael's words.

## Known Stubs

None. Plans 03 and 04 append the pure functions, as the plan intends.

## Threat Flags

None. There is no new network, auth or file-write surface. At import the module reads only
results/ JSON records, and the audit-hook test shows no checkpoints/ or data/ open.

## Self-Check: PASSED

- FOUND: scripts/phase41_prereg.py, tests/test_phase41_prereg.py
- FOUND commits: d6f12e9, 578011f, 0f5b6f3 (`git log --oneline -4`)
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched. No gsd-sdk handler was called.
