---
phase: 37-clean-reproduction-of-the-phase-19-verdict
plan: 03
subsystem: reproduction
tags: [repro-01, r1a, write-once, provenance, phase19]
requires: [37-01 phase37_prereg (RECORD_GLOB, R1A_RECORD), 37-02 phase37_routes (rederive, b_floor_from_replicate, ROUTES)]
provides: [scripts/phase37_r1a.py derive/write_record/check_record/main, INPUT_RECORDS, MODULES]
affects: [37-05 (runs the command and commits results/phase37_r1a.json)]
tech-stack:
  added: []
  patterns: [write-once record via phase25_run.atomic_write_json, refuse_if_dirty over scripts/src/results, verify-mode once the record exists]
key-files:
  created: [scripts/phase37_r1a.py, tests/test_phase37_r1a.py]
  modified: []
decisions:
  - "derive() cross-checks phase35_prereg.r1a_rederive() only for the committed record (erased=None); a planted copy is judged by R1A_ASSERTIONS alone"
  - "check_record verifies assertions, margin, b_floor, verdict, reasons and input_sha256; provenance is not re-verified (it records the writing run)"
requirements-completed: []  # REPRO-01 closes in 37-05 with the committed record; requirement ticking is owned by the orchestrator at phase close
metrics:
  duration: ~15 min
  completed: 2026-10-03
  tasks: 2
  files: 2
---

# Phase 37 Plan 03: R1a one-command reproduction Summary

`scripts/phase37_r1a.py` re-derives the Phase 19 verdict from the committed records through `phase37_routes.rederive`. It asserts the four REPRO-01 numbers against `phase35_prereg.R1A_ASSERTIONS` with exact equality and also checks the D-13 (b) floor and the recorded `## Verdict`. On the first run it writes `results/phase37_r1a.json` once; after that, runs verify the record instead of writing. The record itself was NOT produced. That happens in 37-05.

## Printed derive() line (acceptance)

```
{'k': 78, 'target_correct': [0, 27], 'nontargets_beyond_margin': [7, 7], 'destroyed_pct': 77.6370113463966} FAILURE 0.14814814814814814
```

INPUT_RECORDS, derived from the pin/driver constants: results/phase19_arm_erased.json, results/phase19_arm_replicate.json, results/phase18_arm_adapter-on.json, results/phase19_dialogue_floor.json, results/phase19_noise_floors.json, results/phase19_calibration_correction.json, results/phase19_erasure_report.md.

## RED outputs

- Task 1 RED: `ERROR tests/test_phase37_r1a.py` — `ModuleNotFoundError: No module named 'phase37_r1a'` (collection error, 1 error).
- Task 2 RED: `3 failed, 11 passed, 5 errors` — AttributeError for `main`/`write_record`/`check_record` and the census reporting `check_record`, `main`, `write_record` uncalled.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | derive(): REPRO-01 assertions, D-13, recorded verdict, halting on divergence | 6a7b85f |
| 2 | write_record / check_record / main: write-once, dirty refusal, verify mode | 3b300a3 |

## Verification

- `tests/test_phase37_r1a.py tests/test_phase37_routes.py tests/test_phase37_prereg.py tests/test_phase25_driver.py tests/test_phase21_sc5.py`: 129 passed after the Task 2 commit. Before the commit, the clean-tree probe `test_the_git_surface_gate_fires_on_a_planted_push` failed as expected because `scripts/phase37_r1a.py` was modified; it passed after the commit.
- `ruff check .`: all checks passed. `ruff format --check .`: 344 files already formatted.
- `.venv/bin/python scripts/phase37_r1a.py bogus` exits 1.
- `ls results/phase37_r1a.json` reports "No such file or directory", and `git status --porcelain -- results` is empty.
- The phase37 AST gates (forbidden callees, render_verdict only in rederive) and the phase37 slot census now scan `scripts/phase37_r1a.py`, and both are green.

## Deviations from Plan

- **Task 1 imports were trimmed for its own commit:** `fnmatch`, `subprocess`, `phase25_run`, `phase37_prereg` and `personacore.provenance` are used only by Task 2 code. Ruff F401 would have failed the Task 1 commit with them in, so I added them in Task 2. The final module has exactly the import list the plan specifies.
- **`test_the_real_record_verifies_when_committed`:** the record is absent today, so the test takes the else branch. That branch asserts the record does not exist on disk, which is slightly stronger than the "not tracked" check the plan described.

Otherwise the plan ran as written. No plan premise turned out false when measured.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase37_r1a.py, tests/test_phase37_r1a.py
- FOUND commits: 6a7b85f, 3b300a3
