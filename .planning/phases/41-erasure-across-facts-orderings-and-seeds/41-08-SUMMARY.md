---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 08
subsystem: erasure-driver
tags: [phase41, e1, driver, preflight, ledger, d-02, d-05, d-13, d-22, d-24, d-26, erase-04, erase-05, erase-06, erase-09]
requires: [41-07]
provides:
  - "phase41_erasure: run_inputs, adapter_digest_failures (ERASE-05), preflight (stages, refusals, caps without k48), _tracked_and_clean, _launch_pathspec, rerun_units (stub for 41-09)"
  - "phase41_erasure: rehearsal identity (record_rehearsal appends units at equal digests, record_rehearsal_seconds adds cpu_ordering_seconds + cpu_timings once), rehearsal_disclosure per unit"
  - "phase41_erasure: ordering_smoke (variant.json write-once with variant_decided_by), _variant / _variant_record, run_prep_unit, run (stage 1)"
affects: [41-09, 41-10, 41-11, 41-12]
tech-stack:
  added: []
  patterns: [Phase 40's preflight/run skeleton re-keyed per unit, fakes bound to the real signatures (inspect.signature.bind) so the live kwargs are checked]
key-files:
  created: []
  modified: [scripts/phase41_erasure.py, tests/test_phase41_erasure.py]
decisions:
  - "variant_decided_by: 'cpu_rehearsal' on a rehearsal root or when the CPU seconds fail ordering_cost_fits; otherwise 'mps_smoke' (the MPS smoke decided: adaptive when it fits, static when it alone fails)"
  - "the smoke's seconds are gradient_ordering's own wall-clock (ordering['seconds']), not a second timer around the call"
  - "a cell stage is refused before any start line until 41-09 wires run_cell (no stub that would leave an open attempt)"
  - "preflight refuses a second prep unit whose seed's first prep unit is neither whole nor pending (it would digest-check an adapter nobody trained), and refuses stage 2 while any prep unit is dropped and not re-run"
requirements-completed: []
metrics:
  duration: not recorded
  completed: 2026-10-08
---

# Phase 41 Plan 08: preflight and run stage 1 Summary

`requirements-completed: []`: 41-08 writes the launch gate and the stage-1 half of the run. Nothing ran on MPS and no record was written, so no requirement is complete.

The E1 driver now has a preflight that checks ERASE-05's adapter digests first. Run then executes stage 1: one ledger attempt per prep unit, with the D-02/D-05 ordering smoke as the first step of the first attempt. Everything is tested on fakes on CPU, in tmp roots.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | bb0fd9f | run_inputs, adapter_digest_failures, rehearsal identity + disclosure, _launch_pathspec, _tracked_and_clean, stage logic, preflight; 31 new tests |
| 2 | 12c43a7 | ordering_smoke, _variant, run_prep_unit, run (stage 1); 14 new tests (the refusal rows now go through run()) |

## RED (tests first)

- **Task 1:** `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py` gave `31 failed, 40 passed in 6.59s`. The failures were AttributeErrors: `refuse_if_dirty` x27 (the rig patches it), and one each for `run_inputs`, `rehearsal_identity_path`, `_tracked_and_clean` and `_launch_pathspec`.
- **Task 2:** the same command gave `35 failed, 49 passed in 8.40s`. The failures were `ordering_smoke` x27 and `run` x8, all AttributeErrors.

## Acceptance lines as printed

- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py -k "preflight or run_inputs or rehearsal"` gave `29 passed, 42 deselected` at Task 1.
- `-k "adapter_mismatch or caps_never_pass_k48 or stage_logic"` gave `3 passed, 68 deselected`.
- `_skip_failures(...)` over tests/test_phase41_erasure.py printed `[]` (Task 1, and again after Task 2).
- `-k "stage1 or band_record_contract or calibration_record_contract or control_gap_mismatch or no_arguments or ordering_smoke"` gave `11 passed, 74 deselected`.
- Plan verification: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py tests/test_phase41_prereg.py tests/test_phase36_ledger.py` gave `193 passed in 13.20s`.
- `test_stage1_records_fill_the_floors_and_bands` covers the fill check. It feeds the four calibration records and four band records from the fake rig to `phase35_prereg.fill` with `floors_fill_inputs()` / `band_fill_inputs()`. `_REPO_ROOT` is monkeypatched to the tmp root, and the corpus and noise floor are copied byte for byte. The draws come from `results/phase19_arm_cal-erased.json`, and both fills accept them.
- `ruff check .` gave `All checks passed!`, and `ruff format --check .` gave `366 files already formatted`.
- `shasum -a 256 scripts/phase41_prereg.py` gave `11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3`, the frozen digest. Neither the prereg nor its test was edited.
- Census greps:
  - `grep -c "train_arm("` gave 1 in the driver and 0 in its test.
  - There is no `os.replace`, no `ratchet_k`, and no new `== 10` in the diff.
  - The only `inject_lora` hit is the pre-existing 41-06 fixture.
  - No `results/*.json` names phase41_erasure, so no module_sha256 pin is affected.
- `find results data checkpoints -maxdepth 1 -name '*phase41*' | wc -l` gave 0.
- Real-host check, read-only: all four `phase41_adapters` files exist and match their recorded sha256. This was hashed directly before writing preflight; no MPS was used.

## Census runs on the committed tree (HEAD 12c43a7, clean except .claude/scheduled_tasks.lock)

- **Batch 1** (the same 31 files as 41-07) gave `1319 passed in 251.29s`, B1_EXIT=0. That is 1274 + 45, where 45 is the new driver tests (40 -> 85).
- **Batch 2** (test_phase23_resume, 23_budget, 25_record, 25_promotion, 40_noise) gave `226 passed, 3 skipped in 138.57s`, B2_EXIT=0.
- `git status --porcelain` before and after both batches showed only `.claude/scheduled_tasks.lock`.

## What the tests prove

- **ERASE-05.** One flipped byte in a tmp Phase 40 adapter makes `adapter_digest_failures()` name `(path, expected, actual)`. Preflight then refuses with `ERASE-05 ... <path>` before any ledger or heartbeat line. A missing adapter gives `actual None`. The test runs on fake files and is never host-gated.
- **Refusals, through run() with smoke/gap/train recorders.** Each of these refuses with the ledger unchanged and no heartbeat:
  - a missing run input
  - an open attempt
  - a rehearsal on mps
  - a require_launch stop
  - dirt
  - an unknown HEAD
  - units outside pending or out of order
  - a real root on cpu
  - a real root with an explicit ledger
  - a missing identity
  - an identity without smoke seconds
  - a prereg digest drift

  Stale outputs refuse too: the calibration record, the band record, raw cal-erased, and the adapter, checkpoint, bin, mask and moved csv for the seed's first prep unit. The second prep unit never owns the adapter files.
- **D-26.** check_unit_caps receives exactly `cells=16, checkpoints_per_cell=5, calibrations=4`.
- **Stages.**
  - With all prep units pending, preflight is at stage 1.
  - Whole prep units on a rehearsal root give stage 2 with CELL_UNITS. units= must be a subset of pending, in UNITS order.
  - On the real root, whole prep units with FLOORS_FILE untracked give `STAGE 1 DONE` with no start line. `_tracked_and_clean` is asked with exactly FLOORS_FILE plus the 8 stage-1 records; patched to True, it gives stage 2 on mps.
  - A dropped prep unit refuses stage 2. A second prep unit whose first was dropped refuses, while `units=PREP_UNITS[2:]` passes.
- **Rehearsal identity.**
  - It is recorded once. The smoke's seconds and timings are added once and never overwritten.
  - A stage-2 call at equal digests appends units and keeps git_sha, module_sha256, started_utc, cpu_ordering_seconds and cpu_timings byte-identical. It never removes a unit.
  - Different digests refuse ("fresh rehearsal"), and so does one optional key without the other ("malformed").
  - The disclosure names every unit.
- **ordering_smoke.** It writes `{variant, variant_decided_by, cpu_seconds, mps_seconds, d02, timings (with ratio), rehearsal, ordering_bound}` write-once. The test covers three (cpu, mps) cases:

  | cpu | mps | variant / decided by |
  |---|---|---|
  | fits | fits | adaptive / mps_smoke |
  | fails | fits | static / cpu_rehearsal |
  | fits | fails | static / mps_smoke |

  - On a rehearsal root it gives cpu == mps == S, rehearsal True and cpu_rehearsal, recorded into the identity it was given.
  - Passing identity_path on the real root refuses, and a None identity_path on a rehearsal root refuses.
  - A d02 STOP propagates before variant.json exists.
- **Stage-1 order.** The exact log per unit, in PREP_UNITS order:
  1. require_launch
  2. start
  3. the smoke (load, smoke, variant.json), first unit only
  4. gap
  5. band record
  6. train (the seed's first unit only)
  7. d11
  8. load
  9. calibration
  10. cal_erase
  11. calibration record
  12. end

  The ledger has 4 start/end pairs whose end lines name `unit_record`. Heartbeat beats cover every run_id, and the trainer runs once per seed.
- **Record contracts.**
  - The band record carries no `provenance.run`, only `provenance.measurement`.
  - The calibration record carries:
    - family A2, corpus == CALIBRATION_CORPUS, and the faked arm's draws
    - a full 288-address applied_ordering, k, stopped and d06_order
    - variant and variant_decided_by (None for greedy)
    - adapter {path, sha256}, which is equal across a seed's two units
    - d11_identity and cal_erased_record {path, sha256}
    - provenance.run with RUN_PROVENANCE_KEYS
    - no `target` key
- **Recovery paths.**
  - Control-gap stop: a STOP file is written and there is no band record. The attempt stays open and reconcile gives one lost line, so the unit is dropped. A relaunch refuses the seed's second unit; `units=PREP_UNITS[2:]` runs seed 2024 without a second smoke.
  - Changed adapter: if the adapter changes between a seed's two units, the second refuses on sha256.
  - Crash between the calibration record and the end line: preflight then says "NEVER reconcile" and leaves the ledger untouched.
- **No-argument run.** `run()` with no arguments on the real-root rig reaches preflight with root == `_ROOT` and every other argument None. It writes the milestone (rig) ledger and heartbeat, uses mps, reads cpu_seconds 100.0 from the identity, and gives decided_by mps_smoke and rehearsal_disclosure commits []. Every fake is bound to the real function's signature, so a kwarg the live path would pass wrongly fails the test.

## Deviations from Plan

1. **[Signature] `run_prep_unit(unit, *, pf, started_utc, state, smoke, cpu_seconds, identity_path)`.** The plan's signature was `(unit, *, root, device, rehearsal, smoke, cpu_seconds)`. The calibration record needs provenance.run (launch sha, modules, started_utc) and the rehearsal disclosure, and the smoke needs the identity path. All of these come from `pf`; root and device are read from it, and rehearsal is derived from the root.
2. **[Rule 2] Stage-2 cell dispatch refused before the start line** ("plan 41-09's run_cell: not wired yet") rather than a `run_cell` stub called inside the attempt. A stub raising inside the attempt would leave an open ledger line.
3. **[Rule 2] Two extra preflight refusals.**
   - A second prep unit whose seed's first prep unit is neither whole nor pending.
   - Stage 2 while a prep unit is dropped and not re-run.

   Both would otherwise crash mid-attempt, or open the cells without every (ordering, seed) present.
4. **[Rule 2] Phase 40's WR-01 open-attempt branch kept per unit.** An open attempt whose unit record exists refuses with "append its end line by command, NEVER reconcile". This is tested by the crash-before-end test.
5. **Pathspec:** a whole or dropped cell excludes its cell record and its K = 16 / K = 48 records at every grid checkpoint, with no disk read. Excluding a never-written path is harmless, so this equals "listed in the cell record or present on disk". On a tmp root the pathspec stays LAUNCH_PATHSPEC, as in Phase 40.
6. **Smoke seconds:** taken from `gradient_ordering`'s own `seconds`, not a second perf_counter around the call. This keeps the test free of clock patching.
7. **run() returns `{"stage", "whole"}`**, which covers the STAGE 1 DONE return, instead of Phase 40's list.
8. **`_tracked_and_clean(*rels)`:** 41-10 plans `_tracked_and_clean(rel)`, and this variadic version serves that call unchanged.
9. **Both prep records carry `rehearsal_disclosure`** (`{"this_is_the_rehearsal": True}` on a tmp root), as Phase 40's seed records did.
10. **run_inputs has 23 entries with one duplicate path** (teach_persona and phase14_recall share the tokenizer path), as in Phase 40. This is harmless for an existence check.

Not done (out of this plan's scope): `main()` arrives in 41-10. The launch-gate memory snapshot and the caffeinate-child identity (D-25) are 41-12's operations steps.

## Known Stubs

- `rerun_units` returns `frozenset()`. Plan 41-09 implements it with drop_attempt, and its test lands there; the plan text specifies this stub.
- Stage 2 is refused until 41-09 wires `run_cell`.

## Threat Flags

None beyond the plan's register. Each threat has a test:

| Threat | Test |
|---|---|
| T-41-29 | adapter mismatch |
| T-41-30 | variant.json write-once before any gradient calibration |
| T-41-31 | gap stop with no band record |
| T-41-32 | real-root stage 2 gated on tracked + clean |
| T-41-33 | caps recorder |

## Not verified

- Nothing ran on MPS, on the real corpus or on a real checkpoint. Everything is fakes and tmp roots.
- `ordering_smoke` → the real `model_gradient_ordering` → `taylor_scores` on a real adapter. Only the 41-06 tiny-fixture path is tested; the first real run is 41-11's CPU rehearsal.
- `preflight` on the real repository root: it would refuse until the rehearsal identity exists, and it was not run.

## Self-Check: PASSED

- FOUND: scripts/phase41_erasure.py, tests/test_phase41_erasure.py
- FOUND: bb0fd9f, 12c43a7 (`git log --oneline -3`)
