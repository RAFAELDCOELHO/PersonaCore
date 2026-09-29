---
phase: 29-v5-0-pre-registration-and-carried-debt
plan: 03
subsystem: phase16-persistence-driver
tags: [debt, td-16-r1, pre-registration, verbatim]
requires: ["29-01 (phase29_prereg.NAMED_LIMITATIONS['TD-16-R1-REPORT'])"]
provides: ["phase16_persistence.d28_note()", "_blockquote_after(anchor)", "D28_NOTE_ANCHOR"]
affects: [tests/test_phase16_driver.py]
tech-stack:
  added: []
  patterns: ["one shared markdown-blockquote parser for every verbatim pre-registration read"]
key-files:
  created: []
  modified: [scripts/phase16_persistence.py, tests/test_phase16_driver.py]
decisions:
  - "Published Phase-16 report is not re-rendered; the D-28 kernel's absence is tied to NAMED_LIMITATIONS['TD-16-R1-REPORT'] by a biconditional test"
requirements-completed: []
# DEBT-02 closure is the orchestrator's call.
duration: ~10 min
completed: 2026-09-24
---

# Phase 29 Plan 03: D-28 note read verbatim at runtime (DEBT-02) Summary

`d28_note()` reads the D-28 READING QUALIFICATION from 16-CONTEXT.md through the same parser as `arm_d_qualifier()` (both now delegate to `_blockquote_after(anchor)`). A sha256 pin reddens on any amendment. The report-absence test ties the published report's missing kernel to the TD-16-R1-REPORT named limitation.

## Tasks

| Task | Commit | Files |
|------|--------|-------|
| 1. `_blockquote_after` + `d28_note()` | b8027b8 | scripts/phase16_persistence.py |
| 2. Four d28 tests (digest pin, D-25 parity, report-absence <=> limitation, watched RED on tmp copy) | 85ddf7a | tests/test_phase16_driver.py |

## Measurements

- `d28_note()`: 1402 chars, sha256 `171725c69ff06241882a0d165c02172d80721b3b33d55ddf7c8bef8609ad4210`. This matches the research value, and the pin uses it.
- The D-28 anchor sits at 16-CONTEXT.md:267, as the plan says.
- Source guards: `count('0.125') == 1`. The file contains none of the forbidden predicate substrings (0 hits).
- `git diff` on `results/phase16_persistence_report.md` and on 16-CONTEXT.md is empty.

## Verification

- `tests/test_phase16_driver.py`: 77 passed. The `-k d28` selection gives 4 passed and 0 skipped.
- Census plus readers run: all `test_phase16_*`, test_phase17_{personas,scoring,stats}, test_phase18_{prereg,widenings}, test_phase14_scoring, test_phase23_ctrl, test_phase21_{unit_continuation,sc5}, test_phase20_correction, test_phase25_driver, test_lora_inject, test_phase29_prereg. Result: 445 passed, run on the committed tree.
- ruff check and format --check pass on both touched files.

## Deviations from Plan

- The shared `_prove` "missing file" message is now generic and interpolates `{anchor!r}`. The old text named D-25 and arm D specifically. No test pins that message (grep checked).
- The `== 10` census: `tests/test_phase16_driver.py` already had one occurrence before this plan. This plan adds none.

No plan-vs-code mismatches: every line number, constant and digest the plan cited matched the measurement.

## Self-Check: PASSED
- scripts/phase16_persistence.py contains `def d28_note`: FOUND
- commits b8027b8, 85ddf7a: FOUND
