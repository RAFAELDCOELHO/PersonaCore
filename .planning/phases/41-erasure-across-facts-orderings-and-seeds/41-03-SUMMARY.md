---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 03
subsystem: erasure-prereg
tags: [phase41, prereg, gate-composition, erase-06, erase-07, erase-09, erase-10, descriptive]
requires:
  - scripts/phase41_prereg.py fill file 1 (41-02: TARGETS, SEEDS, ORDERINGS, GRID, E1_CHECKPOINT_GRID, E1_CONDITION_B_MARGIN, ENTRIES, record paths)
  - scripts/erasure_gate.py (wilson_upper_bound, VERDICTS), scripts/phase40_prereg.py (a2_scope, a2_rows, slot_rows, SEEDS), scripts/phase19_run.py (_pooled_rows), scripts/phase37_routes.py (route_d)
  - results/erasure_kstar_arm_k064.json, results/phase40_a2_{full,m2}_seed*.json, results/phase40_noise_floor.json, results/phase20_retention_floor.json, results/phase19_collateral_curve.json
provides:
  - "gate composition: nontarget_slots, record_rows, k16_slot_counts, k16_target_count, condition_a, condition_b, condition_c, cell_verdict, pair_label, summary_counts, not_reached_sentence, floors_fill_inputs, band_fill_inputs; constants SUCCESS/FAILURE/INCONCLUSIVE (selected from erasure_gate.VERDICTS by equality), NOT_RUN, SEED_OUTCOMES, PAIR_LABELS"
  - "descriptive readings: spearman_rho, d12_rows, retention_floor_record, retention_rows, retention_spread, slot_ranges, varies_labels, nontarget_damage, in_range, m1_m2_rows, d13_ranges, d13_comparison, d21_reading; private _group_range, _anchor_size; labels V4_CAP_LABEL, VARIES_LABEL, INSIDE, OUTSIDE, NO_M2"
affects: [41-04, 41-07, 41-10, 41-12]
tech-stack:
  added: []
  patterns: [verdict strings selected by equality from erasure_gate.VERDICTS; every new def called as phase41_prereg.<fn>( in the tests]
key-files:
  created: []
  modified: [scripts/phase41_prereg.py, tests/test_phase41_prereg.py]
decisions:
  - "cell_verdict always returns the same five keys {verdict, judged, failed, beyond, reason}; reason is None except for INCONCLUSIVE (the plan listed four keys for NOT_REACHED)"
  - "k16_slot_counts refuses draws that do not carry exactly E1_CHECKPOINT_GRID['read_k'] completions, so a K = 48 draw list can never be read as a K = 16 count"
  - "slot_ranges recomputes each group's rate range from its counts and refuses a recorded range that differs"
requirements-completed: []
# 41-03 contributes to ERASE-06, -07, -09 and -10 (written rules and fill arguments). It completes none of them: the records and the fills come later.
metrics:
  duration: ~15 min (commits 44586fd 09:58, f220f4f 10:00 -0300; previous HEAD 1d0b679 09:49)
  completed: 2026-10-08
---

# Phase 41 Plan 03: phase41_prereg part 2 (verdicts, labels, readings) Summary

This plan adds the gate composition and every declared descriptive reading to
`scripts/phase41_prereg.py` as pure functions, before any record exists. Each one is tested on
real committed records. Per target, (a) is a Wilson bound against the floor, (b) checks the 7
other core slots against the same seed's intact full adapter, and (c) checks the dialogue gap
against the band. `erasure_gate.erasure_succeeded` and the pin's pet_name-hardwired (b) helpers
are never called; an AST test enforces this.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | 44586fd | gate composition, pair labels, summary counts, NOT_REACHED sentence, floors/band fill-input builders, plus their tests and the AST guard `test_no_pin_pet_name_helpers` |
| 2 | f220f4f | D-06, D-12, D-14, D-18, D-19/D-28, D-20/D-21 readings and their tests |

## RED outputs (tests first)

- Task 1, tests appended before the code: `11 failed, 26 passed`. Every failure was
  `AttributeError: module 'phase41_prereg' has no attribute ...` (for example
  `floors_fill_inputs`). The 26 passing tests were the 25 from 41-02 plus the new AST guard
  `test_no_pin_pet_name_helpers`, which is green while nothing calls the helpers. Its planted
  calls are what prove it can fail.
- Task 1, first GREEN run: `1 failed, 36 passed`. The failing test was the every-function census:
  `band_fill_inputs`, `cell_verdict`, `floors_fill_inputs`, `pair_label` and `summary_counts` were
  called through the alias `p.`. They are now called as `phase41_prereg.<fn>(`.
- Task 2, tests appended before the code: `7 failed, 37 passed`, all `AttributeError` (for example
  `d13_ranges`).
- Task 2, first GREEN run: `3 failed, 41 passed`.
  - The census flagged `_anchor_size`, `_group_range` and `in_range`. I added
    `test_group_range_and_anchor_size_helpers` and switched to direct calls.
  - My non-vacuity assertion in `test_m1_m2_rows` assumed some M1 slot is inside the M2 range.
    On the k = 64 record every slot reads "fora da faixa". It is now a planted M1 count at the M2
    minimum, which reads "dentro".
  - The off-range plant in the slot_ranges test used `street`. Its recorded range of 0.0 is
    already the range of its counts, so nothing raised. The plant now uses `hometown`.

## Acceptance lines (printed at HEAD f220f4f)

Task 1:
```
0 ['birth_year', 'hometown', 'house_number'] não apagado com 128 de 288 componentes removidos 16 5
```
`-k no_pin_pet_name_helpers`: `1 passed, 36 deselected` (at the Task 1 commit).

Task 2:
```
['birth_year', 'hometown'] full only {'anchor_512': (15, 41), 'r_q_committed': (0, 1), 'r_q_minted': (9, 12)}
```
`test_census_every_phase41_prereg_function_has_a_cpu_test`: `1 passed`.

Values the tests compare against records (computed in the test, or typed only in the test):
- Band 1337: `mitigation_gate.dialogue_gap_band(control_gap=per_seed["1337"].full.dialogue_gap.gap,
  gap_noise_floor=gap_noise_floor)` == `(0.6210483312521959, 1.4102360698263419)`.
- The k = 64 arm's gap, `4.920568428792842 - 4.573349214207799`, falls below that band, so (c)
  does not hold there.
- Retention cap `results/phase20_retention_floor.json::cap` == 3.9085032379884783. The k = 64 stop
  reads "sim" (`retention_ppl[0]` 3.723444660061371) and the intact full 1337 adapter reads "não"
  (4.219759892336485).
- pet_name full counts over phase40_prereg.SEEDS are `(27, 26, 27, 25, 27)`.

## Test counts

- `tests/test_phase41_prereg.py`: `45 passed` (25 from 41-02 + 20 new).
- Gate list (9 files: `tests/test_phase41_prereg.py tests/test_phase35_*.py tests/test_phase36_*.py
  tests/test_lora_inject.py tests/test_phase21_sc5.py`, passed as `$(cat gate.txt)`):
  `444 passed in 89.46s`, exit 0. This list includes the plan's verification subset
  (`test_phase35_prereg.py -k "slot or phase41"`).
- `ruff check .`: All checks passed. `ruff format --check .`: 364 files already formatted.
- `git ls-files 'results/phase41_*'` and `find results -maxdepth 1 -name 'phase41_*'`: both empty
  after each commit.
- The diff contains no `== 10`, `os.replace`, `inject_lora`, `train_arm(` or `ratchet_k`
  (checked with `git diff -U0 | grep`, exit 1).
- `shasum -a 256 scripts/phase41_prereg.py` at f220f4f:
  `bdddad1b96f8a682e8d20411c3d71eceebd456a82a2187c55ea4f4668d0f3c37`. Plan 04 will change it.

## Deviations from Plan

1. **[Rule 2 - correctness] K = read_k is checked in `k16_slot_counts`.** The function refuses
   draws that do not carry exactly `E1_CHECKPOINT_GRID["read_k"]` completions. Without this check,
   a K = 48 draw list would count as a K = 16 read. Tested: the untruncated draws are refused.
2. **cell_verdict has one return shape.** Every branch returns `{verdict, judged, failed, beyond,
   reason}`, with `reason` None outside INCONCLUSIVE. The plan's NOT_REACHED dict had no `reason`
   key. A single shape means plan 07 and the report do not need per-branch key handling.
3. **`pair_label` text.** `text` is "<v1> na 1337, <v2> na 2024" for every label, not only for
   não replicado. The plan fixed the text only for não replicado.
4. **Range cross-check in `slot_ranges`.** Each group's range is recomputed from its counts
   (max - min of n/q, the same arithmetic as `phase40_prereg.per_slot_spread`). A recorded range
   that differs is refused. Tested with a planted `hometown` range.
5. **`spearman_rho` uses an exact `sum` of int squared rank differences instead of `math.fsum`.**
   The input is all ints, so the sum is exact; reversal gives exactly -1.0.
6. **`summary_counts` sub-counts count pairs.** Inside não replicado, a pair counts once under a
   sub-key when either seed carries that outcome, as the action and the summary_line entry state.
   The behaviour list's phrase "per seed-verdict occurrence" was not followed. The test fixes the
   semantics: two INCONCLUSIVE pairs, two NOT_REACHED pairs and one NOT_RUN pair over the 8
   synthetic pairs.
7. **Test-only extras.** The fill-builder test also runs `phase35_prereg._prove_entry`,
   `_prove_keys_value` and `_prove_cells_cover_targets` (the rule's own checks that run before any
   file is read) on the built arguments. It also checks that every input matches a declared
   pattern of the slot and that every declared pattern is consumed. `fill` itself cannot run yet,
   because the records do not exist.

## Known Stubs

None. Every function computes from its arguments or from committed records. The fill builders
return None-valued keys by design, since the floors and bands are computed by the Phase 35 rules
at fill time.

## Threat Flags

None. There is no new network, auth or write surface. The functions read only committed
`results/` JSON (through `_read` or the callers' records). T-41-09, T-41-10, T-41-11 and T-41-12
are covered by `test_condition_b_per_target` (cat_name), `test_no_pin_pet_name_helpers`,
`test_nontarget_damage` ((b) left unchanged) and `test_fill_input_builders` (fresh, equal objects).

## Self-Check: PASSED

- FOUND: scripts/phase41_prereg.py, tests/test_phase41_prereg.py (modified)
- FOUND commits: 44586fd, f220f4f (`git log --oneline -3`)
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched. No gsd-sdk handler was called.
