---
phase: 40-m2-seed-noise-floor
plan: 07
subsystem: e2-driver
tags: [noise-floor, NOISE-01, NOISE-02, build_record, emit, report, phase41-contract]
requires:
  - "40-06: preflight, run, R-3 b helpers, _launch_pathspec, _real_root_rig"
  - "frozen prereg scripts/phase40_prereg.py (sha256 a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2)"
provides:
  - "build_record(root, *, ledger_path): the noise-floor record through the frozen prereg only"
  - "emit / report: write-once; real-root branches (one refuse_if_dirty, tracked-and-clean record)"
  - "render_report(record): pure markdown, every number read from the record"
  - "main(argv): preflight / run / emit / report, no arguments, cwd _REPO"
affects: [40-08, 40-09, 40-10, 41]
tech-stack:
  added: []
  patterns: [real-records-into-the-consumer test, section-scoped report assertions, json round-trip before render]
key-files:
  created: []
  modified:
    - scripts/phase40_noise.py
    - tests/test_phase40_noise.py
decisions:
  - "build_record proves one device across the whole seeds BEFORE any per-seed dialogue_gap, so a mixed set refuses with its own message rather than an R-1 refusal"
  - "a seed record naming a lost_utc the ledger lacks refuses with its own message, ahead of the list-equality check"
  - "INSUFFICIENT_SEEDS omits recall_floor, gap_noise_floor, gap_noise_floor_detail, m2_gap_descriptive and d12 (all need two whole seeds); D-07/D-08/D-08b, predictions and d13 are computed in both statuses"
  - "predictions.status's observed value is the record status"
  - "render_report json-round-trips its input first, so a build_record dict (int keys) and the written file (str keys) render identically"
requirements-completed: []
metrics:
  duration: "~19 min (HEAD 1b5287b 10:07 -> ee889f2 10:23 -0300, SUMMARY 10:26)"
  completed: 2026-10-06
  tasks: 2
  files: 2
---

# Phase 40 Plan 07: E2 driver part 3 (build_record, emit, report, main) Summary

The driver is now complete. `build_record` sha256-checks every seed record, A2 record and adapter before reading it, and gets every number from the frozen prereg: `recall_floor`, `gap_noise_floor`, `d12_table`, `d07_reading`, `d08b_reading` and `d13_reading`. `emit` and `report` are write-once. `main` dispatches the four commands. The REAL `build_record` was run on the REAL committed `run_erasure_arm` records (retrain copied byte for byte, replicate with only `config.arm` relabelled). The Phase 41 rule `phase35_prereg.fill("e1_condition_c_band_inputs", ...)` accepts the result, both on the MPS-valued records and on a CPU-rehearsal build.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1: build_record and emit, consumer fed a real build | 04451b7 | scripts/phase40_noise.py, tests/test_phase40_noise.py |
| 2: render_report, report, main, chain, censuses | ee889f2 | scripts/phase40_noise.py, tests/test_phase40_noise.py |

## RED evidence

- Task 1 (13 tests written before the functions existed; Task 1's `-k` selector):
  ```
  11 E       AttributeError: module 'phase40_noise' has no attribute 'build_record'
   2 E       AttributeError: module 'phase40_noise' has no attribute 'emit'
  13 failed, 102 deselected in 2.58s
  ```
  The first GREEN run had 12 passed and 1 failed. `test_consumer_accepts_a_cpu_rehearsal_build` hit a `FileNotFoundError` on `<tmp>/consumer/results/phase19_noise_floors.json`: `_consumer_fill` had left `phase35_prereg._REPO_ROOT` patched, so the next `build_record` read `e1_condition_b_margin` from the consumer root. I scoped the patch with `monkeypatch.context()`, and the selector then gave `13 passed`.
  The natural-RED leg of ruling b is in the test itself. An unmodified byte copy of `results/phase19_arm_replicate.json` (config.arm `'replicate'`) as full@1337, with its seed record naming that file's sha256, raises `config\.arm 'replicate'`.
- Task 2 (`-k "report or main or census or skips or chain or os_replace or slot_name"`):
  ```
  15 failed, 3 passed, 115 deselected in 3.99s
  AttributeError: no attribute 'main' (6), 'render_report' (2), 'report' (2), '_tracked_and_clean' (2), '_table' (1)
  assert 0 != 0   (scripts/phase40_noise.py bogus exited 0: no __main__ yet)
  census: {'_tracked_and_clean', 'render_report', 'report', 'main'} not in defs
  ```
  The 3 tests that passed are the pure censuses over the existing driver (no skips, no os.replace / inject_lora, slot census). The first GREEN run had 2 failures. The predictions table followed sorted key order rather than the ENTRIES order, so I fixed it to iterate over `ENTRIES["predictions"]["value"]`. The every-function census found 4 untested helpers (`_counts_table`, `_draws_text`, `_identity_text`, `_seeds_text`), and I added direct calls for them. After that the whole file gave `133 passed`.

## Verify / acceptance outputs

Task 1:
- `pytest tests/test_phase40_noise.py -k "consumer or beside or margin or d08 or d07 or insufficient or emit or dropped_attempts or without_seed or from_real_committed or a2_sha_mismatch"` -> `13 passed, 102 deselected in 13.95s`
- `pytest tests/test_phase35_prereg.py tests/test_phase36_ledger.py` -> `133 passed in 32.66s`
- whole file -> `115 passed in 21.89s`; `ruff check scripts/phase40_noise.py tests/test_phase40_noise.py` -> `All checks passed!`
- `-k consumer` -> `2 passed, 113 deselected` (both call the REAL build_record; no stub of it)
- AST `refuse_if_dirty` call count -> `2`

Task 2 (after commit ee889f2, on the committed tree):
- `pytest tests/test_phase40_noise.py tests/test_phase40_prereg.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase23_resume.py tests/test_phase35_prereg.py tests/test_phase36_ledger.py tests/test_phase36_caps.py` -> `403 passed in 177.26s (0:02:57)`, `EXIT=0`. This covers the plan's seven files plus the 36_ledger and 36_caps censuses.
- `ruff check .` -> `All checks passed!`; `ruff format --check .` -> `362 files already formatted`
- `.venv/bin/python scripts/phase40_noise.py bogus; echo $?` -> `bogus exit=1`
- `test_census_every_phase40_noise_function_has_a_cpu_test` passes with no exclusion (private helpers included)
- `git status --porcelain -- scripts tests results ledger` -> empty
- Census grep over both files: no `== 10` / `!= 10`. The only `train_arm(` is the registered one (`scripts/phase40_noise.py:287`). `os.replace` / `inject_lora` appear only as string literals in the test file's AST gate, with no AST call.
- Prereg digest after both commits: `a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2  scripts/phase40_prereg.py` (unchanged)
- `git diff --quiet 1b5287b HEAD -- .planning/STATE.md .planning/ROADMAP.md` -> unchanged

### The consumer test's band values, as printed by a run

`pytest tests/test_phase40_noise.py -k consumer -s` on the build from the committed records (full@1337 = relabelled replicate, full@2024 = retrain):
```
CONSUMER gap_noise_floor=0.1924750156505528
CONSUMER band (1337, 'greedy') = (0.625, 1.6349500313011056)
CONSUMER band (2024, 'greedy') = (0.875, 2.1349500313011056)
2 passed, 131 deselected in 2.53s
```
The control gaps 1.25 / 1.75 are synthetic band-input records planted by the test. Each band asserts equal to `mitigation_gate.dialogue_gap_band(control_gap=..., gap_noise_floor=<the record's value>)`. The gap floor is a fixture value: it is |gap(replicate) − gap(retrain)| of two committed v3.0 records, not a Phase 40 measurement.

The full suite was not run because the plan does not ask for it.

## Deviations from Plan

1. **[Rule 2] build_record refuses a listed lost_utc that the ledger lacks, with its own message**, before checking that the lists are equal. The plan's single equality check would give that case the same message as an omitted attempt, and the behaviour asks for "each with its own message".
2. **The one-device proof runs before the per-seed loop.** Running it after `dialogue_gap` would let a mixed cpu/mps set reach an R-1 refusal (or none at all) first. With the proof first, the mixed set refuses with "one device across every whole seed".
3. **Extra tests beyond the listed set:** the adapter re-hash refusal (`adapter_sha256`) inside `test_a2_sha_mismatch_refuses`, and `test_census_helpers_called_directly`, which calls the 13 helpers plan 06 listed plus the new private ones by name. The full chain also asserts `len(rig.dirty) == 3`: preflight, run's preflight and emit each made one dirty check.
4. **D-08b's NO_RESIDUAL branch is not reached by a build test.** None of the committed no-component records reproduces the Phase 18 run_arm counts. The test asserts that the record equals `prereg.d08b_reading(...)` for both identity flags, and observes V3_LIMITATION and NOT_SEPARABLE. NO_RESIDUAL is the prereg's own branch, covered in tests/test_phase40_prereg.py.
5. **The plan's "full@2024 to the dialogue-floor seed-2024 adapter" comparator** is read through `comparators()`, which is monkeypatched to tiny tmp adapters in every build test. `adapter_identity` is a recorder around the real tensor-wise function, so no gitignored file is read.

## For plan 08 / 09 (not acted on here)

- `emit` on the real root reads the ledger with `ledger_path=None` (the milestone ledger). Unlike preflight, it does not refuse an explicit ledger on the real root.
- In `render_report`, the double blank line after an attempt's kept-files table is cosmetic (`_table` ends with `""` and `_attempt_lines` appends another).

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-40-24: every A2 record and adapter is re-hashed against its seed record (test_a2_sha_mismatch_refuses). T-40-25: the real build_record is fed to the real Phase 35 rule. T-40-26: `margin_amended` is False and the `git diff --quiet f2cc033^ HEAD -- results/phase19_noise_floors.json scripts/phase19_floor.py` test passes. T-40-27: no top-level `provenance.run`. T-40-28: emit and report are write-once.

## Self-Check: PASSED

- FOUND: scripts/phase40_noise.py, tests/test_phase40_noise.py (modified)
- FOUND commits: 04451b7, ee889f2
