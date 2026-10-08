---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 09
subsystem: erasure-driver
tags: [phase41, e1, driver, run_cell, e1_stop, d-09, d-13, d-20, d-23, d-24, d-26, d-27, erase-07, erase-10, r-3b]
requires: [41-08]
provides:
  - "phase41_erasure: run_cell (the grid loop, K = 16 records, K = 48 confirmations, the stop proved equal to e1_stop, D-13 at the pet_name stop), write_cell, stage 2 wired in run()"
  - "phase41_erasure: the D-23 pause (_pause before every cell's require_launch), declare_resume, _resume_declarations"
  - "phase41_erasure: R-3 b per unit: partial_outputs, drop_attempt, declare_relaunch, rerun_units (replacing the 41-08 stub), _dropped_attempts, _compared_attempts; preflight returns dropped_attempts"
affects: [41-10, 41-11, 41-12, 41-13]
tech-stack:
  added: []
  patterns: [Phase 40's R-3 b re-keyed per unit, fakes bound to the real signatures (inspect.signature.bind) so the live kwargs from run() to every leaf are checked]
key-files:
  created: []
  modified: [scripts/phase41_erasure.py, tests/test_phase41_erasure.py]
decisions:
  - "A confirmation carries exactly CONFIRMATION_KEYS (confirmation_failures refuses any other key); the K = 48 record's sha256 lives in the read row (k48_sha256)"
  - "rerun_units needs the latest manifest present AND passing dropped_manifest_failures; a failing manifest leaves the unit dropped, not pending"
  - "drop_attempt moves files and leaves emptied directories in place: the only directory removal in the driver stays train_calibration_adapter's csv rmdir (AST-guarded)"
  - "declare_resume answers the latest pause notice on disk; e1_pause_due only sees declarations that hold against a written notice's e1_hours"
requirements-completed: []
metrics:
  duration: not recorded
  completed: 2026-10-08
---

# Phase 41 Plan 09: run stage 2 (the cells), the D-23 pause, R-3 b per unit Summary

`requirements-completed: []`: 41-09 writes the cell loop and its operations rules. Nothing ran on MPS and no cell record exists, so no requirement is complete.

Stage 2 of the run is now wired. Each pending cell runs in its own ledger attempt, and `run_cell` reads the pre-registered grid in order. At every checkpoint it takes the K = 16 read, and when the target's pooled count is 0 it takes a K = 48 confirmation. It stops at the first non-None `driver_stop`, and that stop is proved equal to `phase35_prereg.e1_stop` on the same readings. The D-23 pause is checked before every cell. A crashed unit can be dropped (its outputs moved, never deleted) and re-run on Rafael's approved manifest. Everything is tested on fakes, on CPU, in tmp roots.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | 269a930 | run_cell, write_cell, stage 2 in run() (the 41-08 refusal removed); 13 new tests |
| 2 | ed1ca50 | _pause, declare_resume, partial_outputs, drop_attempt, declare_relaunch, rerun_units, _dropped_attempts, _compared_attempts; 9 new tests |

## RED (tests first)

- **Task 1:** `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py` gave `13 failed, 85 passed in 9.90s`. The failures were AttributeErrors on `run_cell` / `_ordering_path`, plus the two stage-2 run tests, which preflight passed before the "41-09: not wired yet" refusal stopped them.
- **Task 2:** the same command gave `8 failed, 99 passed in 15.10s`. The failures were AttributeErrors on `declare_resume`, `partial_outputs`, `drop_attempt` and `rerun_units`, plus the pause run tests. `test_no_file_deletion_in_the_driver` passed at RED because it guards the existing code; its planted `unlink` half shows it is not vacuous.

## Acceptance lines as printed

- `-k "matches_e1_stop or rank_recorded or not_reached_record or confirmations_recorded or written_before or write_once_and_named or d13"` gave `12 passed, 86 deselected`. The `matches_e1_stop` parametrization includes `never_confirmed` (len(GRID) = 5 confirmations, NOT_REACHED) and `confirmed_after_a_failed_one` (2 confirmations, stop at GRID[2]), each with the counts asserted.
- `-k "pause or resume or drop_attempt or drop_second_prep or rerun or between_record"` gave `8 passed, 99 deselected`, with `test_drop_second_prep_unit_keeps_the_seed_adapter` included.
- `-k no_file_deletion` gave `1 passed`.
- Plan verification: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py tests/test_phase41_prereg.py tests/test_phase36_ledger.py` gave `215 passed in 19.32s`.
- `ruff check .` gave `All checks passed!`, and `ruff format --check .` gave `366 files already formatted`.
- `shasum -a 256 scripts/phase41_prereg.py` gave `11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3`, the frozen digest. Neither the prereg nor its test was edited.
- Census greps over the diff: no `== 10`, `os.replace`, `ratchet_k` or `inject_lora` added. `grep -c "train_arm("` still gives 1 in the driver and 0 in its test. No `results/*.json` names phase41_erasure. The driver diff types none of 16/48/27/128/288 outside prose; one error message that said "K = 48" was changed to "K = confirm_k".
- `find results data checkpoints -maxdepth 1 -name '*phase41*' | wc -l` gave 0.

## Census runs on the committed tree (HEAD ed1ca50, clean except .claude/scheduled_tasks.lock)

- **Batch 1** (the same 31 files as 41-07/41-08) gave `1341 passed in 267.20s`, B1_EXIT=0. That is 1319 + 22, where 22 is the new driver tests (85 -> 107).
- **Batch 2** (test_phase23_resume, 23_budget, 25_record, 25_promotion, 40_noise) gave `226 passed, 3 skipped in 139.32s`, B2_EXIT=0.
- `git status --porcelain` before and after both batches was identical (`STATUS_SAME`), showing only `.claude/scheduled_tasks.lock`.

## What the tests prove

- **ERASE-07 / D-26 / D-27, the stop.** The checkpoints are read in GRID order. A K = 48 confirmation runs exactly at the zero K = 16 reads, with `ordering[:c]` as its components. The cell's stop equals `driver_stop(reads)`, `e1_stop(...)["stop"]` and the scripted expectation. `confirmation_failures(confirmations, reads) == []` holds, and `confirmation_hours` is the prereg's. Four sequences are covered:

  | sequence | stop | confirmations |
  |---|---|---|
  | zero confirmed at 16 | 16 | 1 |
  | zero not confirmed at 32, then confirmed at 48 | 48 | 2 |
  | every checkpoint zero, never confirmed | NOT_REACHED | 5 |
  | never zero | NOT_REACHED | 0 |

- **ERASE-10, the rank.** Every read row records the target's exposure rank, NOT_REACHED cells included. A rank of 1 at a confirmed zero still stops.
- **D-09.** A NOT_REACHED cell records judged False, every read, and `not_reached_sentence()` verbatim. It gets no M1 export and no D-13; a judged cell's sentence is None.
- **D-04 / D-24, the ordering.** `orderings/<unit>.json` exists at every read; the fake asserts this. It holds the full ordering, equal to the record's `applied_ordering`. Every read loads exactly that ordering's prefix, for both greedy and gradient (whose variant comes from variant.json).
- **K = 16 records.** Each one is written write-once at `k16_record(t, o, s, c)` with the draws, k, exposure, `target_count == [n, q]`, the 8-slot `k16_slot_counts`, and `components == ordering[:c]`. A planted record refuses with "write-once".
- **D-20.** At a judged pet_name stop, `export_m1(snapshot, ordering[:stop], m1/<unit>_k<stop>_adapter.pt)` runs, then `d13_at_stop(m1, root/k48_record(... stop), device, state)`. A not-measured D-13 is recorded and the cell stays whole. Non-pet_name cells never call either.
- **Stage 2 through run().** There is one start/end pair per cell, and each end names `cell_record(t, o, s)`. The record carries provenance.run (RUN_PROVENANCE_KEYS), module_sha256_at_launch, rehearsal_disclosure and dropped_attempts. The rehearsal identity appends the cell units. On the real root the cell runs on mps with disclosure commits [].
- **D-23.**
  - With E1's spent at its share, run() writes `pause_<utc>.json` equal to `pause_notice(...)` plus `next_cell`, prints `PAUSE e1_h=... next=<cell>`, and appends no ledger line or heartbeat.
  - `declare_resume` naming the next two cells lets exactly those two run, and the run pauses again before the third.
  - `declare_resume` refuses without a pause notice, without "approved" (including "not approved"), on non-CELL_UNITS or repeated cells, and on an e1_hours mismatch. It writes resume_01, then resume_02.
  - `spent` is never called while an attempt is open: it is called exactly 1 + 2 x cells times.
- **R-3 b per unit.**
  - **Crashed cell.** A cell crashed after K = 16 at 16 and 32 and K = 48 at 32, reconciled lost, with an M1 export planted. `drop_attempt` moves those three records, the ordering file and the M1 export under `dropped_attempt_dir(unit, lost_utc)`, with the sha256 of each in the manifest. The originals are gone, the moved files re-hash, and the manifest passes `dropped_manifest_failures`.
  - **Seed's first prep unit.** Its drop moves the band record, the raw cal-erased record, the adapter, checkpoint, bin, mask, in-process csv, moved csv, and the calibration record's atomic-write temp.
  - **Seed's second prep unit.** With the first unit whole, the drop moves only the band record and the raw cal-erased record. The adapter, checkpoint, bin, mask and moved csv keep their sha256 and stay out of the kept list. The re-run does not train, digest-checks the adapter the first record cites, and lists the attempt with `adapter_identity == NOT_PRODUCED`.
  - **Refusals.** Each of these refuses with nothing moved and the ledger unchanged:
    - a whole unit
    - a not-run unit
    - an open attempt
    - a present unit record (crash rule (i))
    - an unknown HEAD
    - an empty cause note
    - "ok", "not approved"
    - an undeclared HEAD change

    `declare_relaunch` refuses when the HEAD did not move, and without approved.
  - **Re-run.** With no manifest the unit is not pending; with a failing manifest it is not re-run. A tampered kept file refuses preflight on sha256. The cell's re-run record lists the attempt (manifest, manifest_sha256, kept re-hashed) with `ordering_equal is True`. A first prep unit that crashed after training retrains on its re-run, and `phase40_noise.adapter_identity(new, kept)` is called with exactly those two paths.
  - **Crash between record and end line.** For a cell, the record exists and the attempt is open. Preflight says "NEVER reconcile", drop refuses "reconcile first", and the ledger is untouched.
- **No deletion.** An AST scan of the driver finds only `train_calibration_adapter`'s rmdir among remove/unlink/rmtree/rmdir/removedirs calls. A planted `unlink` is found.

## Deviations from Plan

1. **[Rule 1 - Bug] Confirmations hold exactly CONFIRMATION_KEYS.** The plan listed `record_sha256` inside each confirmation, but `confirmation_failures` refuses any key outside CONFIRMATION_KEYS. The sha256 is recorded in the read row instead (`k48_record`, `k48_sha256`, next to `k16_record`, `k16_sha256`).
2. **[Structure] `write_cell(unit, *, pf, started_utc, state)`.** It writes the cell record (provenance.run, rehearsal disclosure, dropped_attempts) around `run_cell(unit, *, root, device, state)`, which keeps the plan's signature and returns the blob. run() calls write_cell, mirroring run_prep_unit.
3. **[Record] Extra cell-record keys.** `judged`, `ordering_record` (the orderings/ path), `m1` ({path, sha256} or None), and the read rows' `k16_zero` / `k48_zero`. The stop sequence can be rebuilt from the record alone.
4. **[Rule 2] A cell's stale outputs now include the ordering file and the M1 export path at every grid checkpoint.** Preflight refuses them before a start line, where before they would hit a write-once refusal mid-attempt and leave an open ledger line.
5. **[Rule 2] `rerun_units` requires a passing manifest.** Phase 40 only checked existence. A failing manifest leaves the unit dropped; the plan's "whose latest manifest passes".
6. **drop_attempt leaves emptied directories in place.** Phase 40 rmdir'd them. The plan's AST guard allows only `train_calibration_adapter`'s csv rmdir. Empty directories are invisible to git and to every stale check (those check files).
7. **`_output_roots` excludes the unit record itself.** drop_attempt refuses when it exists, but its atomic-write temp is listed.
8. **One `phase36_ledger.spent(ledger_path=...)` call per pause check** instead of two. `by_front["E1"]` is the same as the `fronts=("E1",)` call's, and pause_notice needs all fronts.
9. **declare_resume binds the declaration to the latest pause notice on disk** and refuses without one. `_resume_declarations` hands `e1_pause_due` only declarations that hold against some written notice's e1_hours (e1_pause_due's docstring assigns that check to the driver).
10. **The pause notice file is `pause_notice(...)` plus `next_cell`.** On a pause, run() returns `{"stage", "whole", "paused"}`.
11. **The calibration record always carries `dropped_attempts`** ([] when none), as Phase 40's seed record did.
12. **Test edits.**
    - `test_run_stage_gates` lost its 41-09 refusal row, as the 41-08 handoff asked.
    - `test_preflight_ok_prints_the_line`'s key set gained `dropped_attempts` (asserted `{}`).
    - `_stage2_rig` gained a `crash_at` passthrough.

## Known Stubs

None. The 41-08 `rerun_units` stub is replaced, and stage 2 is wired.

## Threat Flags

None beyond the plan's register. Each threat has a test:

| Threat | Test |
|---|---|
| T-41-34 | stop == driver_stop == e1_stop on four sequences; the rank recorded but never read |
| T-41-35 | the pause before every cell; approved declarations only |
| T-41-36 | moves with a sha256 manifest; re-run lists the attempts and compares the ordering / adapter |
| T-41-37 | drop refuses a whole unit and a present unit record; unit_outcomes refuses a later attempt |

## Not verified

- Nothing ran on MPS, on a real adapter or on the real corpus. `run_cell` ran only on fakes: the load, the pin's ablation, `load_adapter_weights`, `cell_ordering`, `k16_read`, `k48_confirm`, `export_m1` and `d13_at_stop`. Each fake is bound to its real signature. The K = 16 draws are the committed Phase 40 A2 draws cut to read_k, with the target blanked for a zero. The first real run of the cell loop is 41-11's CPU rehearsal.
- Through this driver, `d13_at_stop` → `phase40_noise.d13_scores` refuses unless Phase 40's `D13_INCLUDED`. That refusal is caught as not measured (41-07's wrapper). Whether D-13 is actually measured at a pet_name stop is not checked here.
- Memory with two models loaded during a K = 48 confirmation (the cell's model plus run_erasure_arm's own) was not measured on MPS.
- The Obsidian vault note: this executor has no Obsidian MCP tool, so the registration is left to the orchestrator.

## Self-Check: PASSED

- FOUND: scripts/phase41_erasure.py, tests/test_phase41_erasure.py
- FOUND: 269a930, ed1ca50 (`git log --oneline -3`)
