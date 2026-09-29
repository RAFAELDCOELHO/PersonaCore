---
phase: 33-admission-and-relearning-on-admitted-points
plan: 01
subsystem: v5.0 admission driver
tags: [admission, write-once, refusal-surface, provenance, ast-census]
requires:
  - scripts/phase29_prereg.py (admission, relearning_scope, SCOPE_RULE, V5_RESULT_PATHS, VERDICTS, COMMITTED)
  - results/phase32_frontier.json (committed, 1 commit)
  - phase25_run.atomic_write_json, personacore.provenance.refuse_if_dirty / git_sha
provides:
  - scripts/phase33_admission.py (admit + four refusal-only legs; RECORD_PATH, FRONTIER_PATH, DIRTY_PATHSPEC, PINNED_MODULES, LEGS, limitation())
  - tests/test_phase33_admission.py (40 tests)
  - SUITE_SHA 3262402da045f03863d51fdf7120fb9de534ee73 (the 33-02 Task 1 precondition)
affects: [33-02 (runs admit live), 33-03, Phase 34 renderer/ledger]
tech-stack:
  added: []
  patterns: [write-once record with HEAD-based committed check, refusal-only CLI legs, sys.setprofile reach trace]
key-files:
  created:
    - scripts/phase33_admission.py
    - tests/test_phase33_admission.py
  modified: []
decisions:
  - "LEGS: calibrate->RELRN-09, curve->RELRN-06, gate->RELRN-07, structural-proof->RELRN-08 (plan's discretion ruling, carried)"
  - "PINNED_MODULES = this module + phase29_prereg, mitigation_gate, mitigation_budget, phase27_prereg, phase25_record, phase25_prereg (derived from __file__; trace test bounds it)"
  - "_committed() reads HEAD via git rev-parse --verify -q HEAD:<rel>, the only git argv in the module; used by admit (D-13) and the leg guard (D-01)"
  - "_rel() returns the bare file name outside _GIT_ROOT so no absolute tmp path enters a refusal message"
requirements-completed: []  # ADMIT-01/02 are ticked in 33-03 Task 2 after the record commit; RELRN-06..09 are never ticked on the MOOT branch
metrics:
  duration: "about 1h45m (including a 39m40s full suite)"
  completed: 2026-09-28
  tasks: 3
  files: 2
---

# Phase 33 Plan 01: Admission Driver Summary

This plan adds `scripts/phase33_admission.py`, a torch-free driver. Its `admit` sub-command calls the frozen `phase29_prereg.admission()` on the committed frontier and writes the thin record `results/phase33_admission.json` exactly once. It refuses in this order, all before any digest: an existing record, then a record committed at HEAD but missing on disk, then a dirty tree. There is no `--force`. The four RELRN leg sub-commands are a refusal surface only. The plan also adds 40 tests, and the full suite is green on the committed tree with the record absent.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | The driver module and its behaviour tests | 7a91a78 | scripts/phase33_admission.py, tests/test_phase33_admission.py |
| 2 | Once-proofs, provenance, by-reference, AR-32-02 and git-surface censuses | 3262402 | tests/test_phase33_admission.py |
| 3 | Full suite on the committed tree, record absent | (no code commit) | this SUMMARY |

## Full suite (Task 3)

- **SUITE_SHA:** `3262402da045f03863d51fdf7120fb9de534ee73`. The run started from this HEAD, with a clean `git status --porcelain -- scripts src tests results` and no `results/phase33_*`.
- **Result:** `3261 passed, 4 skipped, 83 warnings in 2378.07s (0:39:38)`
- **EXIT=0** (log: `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/phase33/suite_3301.log`)
- `git diff --quiet $SUITE_SHA HEAD -- scripts src tests` exited 0 when this SUMMARY was written.

## Verification

- Quick run: `tests/test_phase33_admission.py` shows 40 passed. The Task 1 `-k` filter gives 30 passed and the Task 2 `-k` filter 10 passed, with 0 skipped.
- Guard set (phase33, phase29_prereg, phase27_prereg, phase30_points, phase25_driver, phase21_sc5): 215 passed.
- `ruff check .` and `ruff format --check .` are clean.
- `admit --help` has no `--force`. `PINNED_MODULES` prints 7 paths.
- There is no `pytest.skip`/`skipif`, and neither `== 10` nor `!= 10` appears in either file.
- No pinned file changed. No file under `results/` exists or changed.
- TDD RED: with the module moved aside, the test file failed at collection (1 error). It went green once the module was restored. Tests and module went into one Task 1 commit, as the plan's per-task commit rule asks, so there is no separate `test(...)` RED commit.

## Deviations from Plan

None that change behaviour. Notes:
- The leg reason match uses `startswith(f"{leg} ")`, with a trailing space. The plan says "starts with that leg key". The space stops a prefix collision between leg keys, such as `advr_n6` against `advr_n64`.
- The rule that every test ends with an unchanged real `results/phase33_*` status is enforced by one autouse fixture, not by an assert repeated in each test.
- `limitation()` returns `{"legs": {...}, "scope_rule", "requirements", "surface"}`. The plan fixed the keys but not how the per-leg lines are grouped.

## Known Stubs

- The four leg sub-commands have no body, by design (D-01). The branch is MOOT, so only the refusal surface exists. A future milestone that admits a point builds the body.
- A D-08 wording gap: `admission()` returns no advr_n8 reason. So the n8 line's connective words (`_LEG_LINE`) and the surface sentence (`_SURFACE_LINE`) are driver text, not gate output. Every number in them is bound. 33-02 Task 2 asks the developer to rule on the wording.

## Self-Check: PASSED

- FOUND: scripts/phase33_admission.py, tests/test_phase33_admission.py
- FOUND commits: 7a91a78, 3262402
- Planning files: I made no edits to STATE.md, ROADMAP.md or REQUIREMENTS.md and ran no gsd-sdk mutation handlers (state override).
