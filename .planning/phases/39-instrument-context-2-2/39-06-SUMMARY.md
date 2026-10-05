---
phase: 39-instrument-context-2-2
plan: 06
subsystem: E6 driver part 3 (CTX-02, CTX-03)
tags: [driver, crosscheck, d-20, d-30a, classification, tie-audit, baseline, record, emit]
requirements-completed: []
dependency-graph:
  requires: [39-05 (run, sidecars, rehearsal identity), 39-03 (prereg frozen at 9366134)]
  provides: [rank_rows, crosscheck, _suffix_check, _a2_draws, _a2_question_hits, _rank_block, _generation_block, _descriptive_block, _reading_blocks, _cell_values, _minted_ii, _classified, _decomposition, _hours, _cpu_block, _cost, build_record, emit]
  affects: [39-07 report + rehearsal (consumes the record keys), 39-08 MPS run]
key-files:
  created: []
  modified:
    - scripts/phase39_ctx.py
    - tests/test_phase39_ctx.py
decisions:
  - "Classification goes only through the prereg door: cells(event) filtered to the run's readings and slots, then classify_cell, class_counts per event, tie_audit over the damage cells and baseline_table. The driver has no _cells or _drop_audit (39-06 amendment)."
  - "The record's drop_formula_audit is tie_audit's output (damage only). The baseline is None with the reason 'partial slots: baseline_table needs every slot' on a slice. Each None block carries a sibling *_reason key."
  - "A run that scored k0 but no cell reading gives classification None with the reason 'no cell reading scored' (class_counts refuses an empty list)."
metrics:
  started: 2026-10-05T13:34:31Z
  completed: 2026-10-05T13:52:54Z
  tasks: 3
  files: 2
---

# Phase 39 Plan 06: E6 driver part 3 Summary

This plan turns the sidecars into the E6 record. It has three parts:

- **CPU cross-check** (D-20 / D-30a). Gate cells, R_q and (ii) are re-scored on CPU through the same functions, and every taught suffix sum is compared bitwise with the pinned `span_nll_from_ids`.
- **Readings and classification.** The four readings come out per reading and slot. Collapse and damage are classified through the frozen prereg door (`cells` / `classify_cell` / `class_counts` / `tie_audit` / `baseline_table`). The descriptive blocks hold prediction, per-token values and the minted (ii) ranks beside the committed anchor-side rank.
- **`emit`.** It refuses every unsafe state, then writes `results/phase39_ctx.json` once through `phase25_run.atomic_write_json`.

Requirements: this plan contributes to CTX-02 and CTX-03; the orchestrator ticks requirements at phase close.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 | ba6883c | `rank_rows`, `crosscheck`, `_suffix_check` (D-20, D-30a) |
| 2 | f4c20ed | per-cell blocks, `_decomposition` through the prereg door, descriptive blocks, census leg |
| 3 | 485f5c6 | `_hours`, `_cpu_block`, `_cost`, `build_record`, `emit` with every refusal |

## RED, then GREEN (as printed)

- **Task 1.** RED `-k "crosscheck or rank_rows"`: `5 failed, 80 deselected in 3.06s` (AttributeError). GREEN: `5 passed, 80 deselected in 3.82s`. Whole file: `85 passed in 32.16s`.
- **Task 2.** RED `-k "classify or readings or predicted or minted or drop"`: `7 failed, 1 passed, 84 deselected in 6.49s`. The one pass is a pre-existing test the `-k` filter also matches. GREEN: `8 passed, 84 deselected in 6.45s`. `-k "ast or census"`: `5 passed, 87 deselected in 1.44s`. Whole file: `92 passed in 34.02s`.
- **Task 3.** RED `-k "emit or rehearsal or crosscheck"`: `14 failed, 9 passed, 83 deselected in 23.89s`. First GREEN run: `1 failed, 22 passed`. The failure was a test bug: `_emit_existing`'s `planted` flag was read before the plant ran; fixed before the commit. Then `23 passed, 83 deselected in 28.76s`.

## Acceptance lines (as printed)

- **Task 3 verify** (`tests/test_phase39_ctx.py tests/test_phase39_prereg.py tests/test_phase25_driver.py tests/test_phase21_sc5.py`):
  - Before the Task 3 commit: `1 failed, 201 passed in 75.40s`. The failure was `test_the_git_surface_gate_fires_on_a_planted_push` (`watching the RED must leave no residue in scripts/: ' M scripts/phase39_ctx.py'`), the clean-tree probe reacting to uncommitted work.
  - After commit 485f5c6: `202 passed in 62.47s (0:01:02)`.
- **Lint.** `ruff check .`: `All checks passed!`. `ruff format --check .`: `358 files already formatted`.
- **Orchestrator's targeted set** after the commits (`tests/test_phase39_ctx.py tests/test_phase14_scoring.py tests/test_lora_inject.py tests/test_phase21_sc5.py tests/test_phase25_driver.py tests/test_phase36_ledger.py`): `234 passed in 54.26s`.
- **Clean-tree checks.** `git status --porcelain -- scripts tests results ledger`: empty. `find results -maxdepth 1 -name 'phase39_*'`: nothing. `find data -maxdepth 1 -name 'phase39_*'`: nothing.
- **Prereg unchanged.** `git diff --quiet 9366134 -- scripts/phase39_prereg.py tests/test_phase39_prereg.py`: unchanged. `shasum -a 256 scripts/phase39_prereg.py`: `4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297`.
- **`== 10` / `!= 10` grep** on tests/test_phase39_ctx.py: no match. The full suite was not run (orchestrator override).

## Ruling i, reproduced through the driver (printed this session)

`_decomposition` ran on committed R_a × committed G_q, all 48 cells per event, with R_q and G_a held at their k0 values. Each tuple below is (cells, disagreement, reverse, undecided):

- collapse: `{'combined': (48, 9, 0, 0), 'prefixes': (40, 9, 0, 0), 'M2': (8, 0, 0, 0)}`
- damage: `{'combined': (48, 24, 0, 0), 'prefixes': (40, 24, 0, 0), 'M2': (8, 0, 0, 0)}`
- tie audit: `flips [] exact_ties [['k8', 'person_name', 'G_q']]`

These match the amendment's measurement. The test that pins them is `test_classify_on_the_committed_counts`.

## The fake record's class counts (as printed, `-s`)

These come from the tmp rig's fake SCORED record over `k0, k8, k78, M2, adapter_off` × `person_name, pet_name`. They reflect fake NLLs and fake anchor hits, and only the committed G_q counts are real; they are not measurements.

```
FAKE collapse: cells 6 disagreement 1 reverse 0 undecided 0 by_class {'INSTRUMENT_SUFFICIENT': 1, 'NO_DISAGREEMENT': 5} prefixes 4 M2 2
FAKE damage: cells 6 disagreement 1 reverse 0 undecided 0 by_class {'NO_DISAGREEMENT': 5, 'UNREACHABLE_AT_SIZE': 1} prefixes 4 M2 2
FAKE audit: flips [] exact_ties [['k8', 'person_name', 'G_q']]
```

## What exists now

- **`crosscheck(*, root, device="cpu")`**
  - Requires a SCORED run sidecar and refuses an existing CPU sidecar.
  - Writes `{device, torch_version, started_utc, finished_utc, gate, rq, minted, suffix_equality: {compared, equal, unequal}}` once.
  - Writes no ledger line. Prints `CROSSCHECK DONE <path>`.
- **Record keys, common to every status:** `front, run_id, status, approval, shape, reconstruction, gate {rows, copy_equality, cells}, gate2, rehearsal_disclosure, limitations, not_measured, context_b_instrument, provenance`.
- **Keys SCORED adds:**
  - `readings {reading: {slot: {taught, fact_id, R_a, rank, generation, descriptive, anchor_record}}}`
  - `classification {event: {cells, counts}}` / `classification_reason`
  - `drop_formula_audit` (tie_audit output) / `drop_formula_audit_reason`
  - `baseline` / `baseline_reason`
  - `adapter_off`, `minted_ii`, `cpu_crosscheck`, `cost`
- **Cost block.** It prices the double load per reading (I1). `_a2_draws` loads once per reading (I2), proved by a call-count test.
- **Rehearsal disclosure.** On the real root it is `rehearsal_disclosure(identity, launch sha, launch digests)`, and a missing identity refuses. On a rehearsal root it is `{"this_is_the_rehearsal": True, "slice": {readings, slots}}`.

## Deviations from Plan

### Amendment-driven (39-06 orchestrator_amendment overrides the plan text)

1. **No driver `_cells`, `_classification` or per-cell `rank_status` / `count_status`.**
   - `_classified(values, event)` filters `cells(event)` to the run's readings and slots, then calls `classify_cell(cell, values, k0)`.
   - `_decomposition(values, slots)` returns the classification with `class_counts`, `tie_audit` over the damage cells, and `baseline_table`.
   - k0 is a cell in neither event. adapter_off never reaches the door.
   - `test_classify_helpers_called_directly` and `test_classify_from_the_record`-style checks now recompute through `cell_spec` / `classify_cell` / `class_counts` / `tie_audit` / `baseline_table`. "Collapse cells cover CLASSIFIED_READINGS" is now "cells == `cells(event)` filtered to the run", in `test_emit_drop_formula_audit_is_recomputed`.
2. **No driver `_drop_audit`, and no call to `phase38_prereg.drop_formula_audit`.**
   - The record's `drop_formula_audit` is `tie_audit`'s output: damage only, M2 and G_a n = 1 included, flips and exact ties named `[reading, slot, key]`.
   - `test_drop_audit_names_rounding_ties` and `test_drop_audit_matches_phase38_on_committed_counts` became `test_classify_on_the_committed_counts`, which reproduces ruling i (numbers above).
   - The plan's "9 differing cells (Phase 38's 7 + M2 hometown/house_number)" check was dropped: it described the removed Phase-38-style audit, which the driver no longer builds.
   - `test_emit_drop_formula_audit_is_recomputed` asserts `record["drop_formula_audit"] == tie_audit(record damage cells)` on the record as read back.
3. **New baseline block.** `baseline` / `baseline_reason` were added (ruling f). On a partial-slot run the baseline is None with the amendment's reason.

### Other adjustments

4. **[Rule 2] Reasons and the k0-only case.** Each None block (classification, drop_formula_audit, baseline) carries a sibling `*_reason` key ("k0 not scored", or the partial-slot reason). A run with k0 but no cell reading gets "no cell reading scored: ...". Without it, emit on a `("k0",)` rehearsal would crash in `class_counts([])`.
5. **One test moved from Task 1 to Task 3.** `test_crosscheck_counts_a_differing_cpu_rank` (a Task 1 behaviour) is implemented in Task 3 as `test_emit_crosscheck_counts_a_differing_cpu_rank`, because it asserts on the record. The record names exactly `["k0", "pet_name", <index>]`.
6. **Extra tests:**
   - `test_crosscheck_refuses_a_gate_failed_or_missing_run`
   - `test_readings_a2_draws_load_once_per_reading` (I2)
   - census legs asserting `_suffix_check` as a reader and `rank_rows` / `_rank_block` / `_classified` as rank callers, beside the planned `_descriptive_block` leg
7. **Extra helpers:**
   - `_reading_blocks`, `_cell_values`, `_minted_ii` and `_cost` keep `build_record` free of rank callees and descriptive reads.
   - `_rank_block` adds `indices`, so the CPU block can name differing cells as `[reading, slot, index]`.
8. **The cpu-sidecar refusal lives in two places.** `emit` refuses before `build_record`, as the plan says, and `build_record` proves it too.
9. **Interruption.** The session was interrupted once by an API 529 after Task 1's RED. The working tree was intact; I re-synced from the diff and continued with no work lost.

Prereg untouched. No gsd-sdk mutation handler called. STATE/ROADMAP/REQUIREMENTS/PLAN files not edited. No Obsidian note.

## Known Stubs

None in this plan's scope. The `__main__` dispatcher and `report` are still missing; they arrive in plan 07.

## Self-Check: PASSED

- FOUND: scripts/phase39_ctx.py, tests/test_phase39_ctx.py
- FOUND: ba6883c, f4c20ed, 485f5c6
