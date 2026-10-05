---
phase: 39-instrument-context-2-2
plan: 03
subsystem: pre-registration review (D-27)
tags: [prereg, review, rulings, freeze]
requirements-completed: []
key-files:
  created:
    - .planning/phases/39-instrument-context-2-2/39-REVIEW.md
    - .planning/phases/39-instrument-context-2-2/39-REVIEW-2.md
  modified:
    - scripts/phase39_prereg.py
    - tests/test_phase39_prereg.py
---

# Plan 39-03 Summary — the prereg reviewed, ruled and frozen

Requirements: this plan contributes to CTX-01 and CTX-03; the orchestrator ticks requirements at phase
close. Executed inline by the orchestrator (review → Rafael's rulings → fixes → "reviewed" → suite).

## Task 1 — review and rulings

- First review (`/gsd-code-review 39`, 39-REVIEW.md, 85b7360): 0 blockers, 5 warnings, 4 info.
- Rafael's rulings recorded verbatim in 39-REVIEW.md "## Resolution (2026-10-05)" (cf51309): fix
  WR-01..05, IN-01, IN-02, IN-04; IN-03 a known limitation; a, b, c, d, e, g, h, i, j confirmed (e
  with a change at step 2: REVERSE_DISAGREEMENT); f changed (k0 a cell in neither event, 48 cells per
  event, baseline table).
- Fix commits (each with the four prereg test files and ruff green):
  2c0c300 WR-01 (k0 target vs the SHA-pinned phase18 report total 105/112 + 92/104 = 197, parsed),
  76eff2e WR-02 + f (one cell door), 5079fed e (REVERSE_DISAGREEMENT), b846fd9 g + IN-01 (M2 apart,
  undecided apart), f078603 WR-03 + j (frozen tie audit, class by both formulas), f4dfd48 IN-02 + IN-04,
  cf47e2d WR-05 (literal-scan seeds), f0e6560 confirmations (dated quotes; `UNCONFIRMED []`).
- Second-pass review of the fixes (39-REVIEW-2.md, 36d7182): 0 blockers, no regression on committed
  data (old vs new loaded side by side; five mutants red).
- Rafael's further ruling "Corrigir a ordem das chaves do _door" (sweep, sort_keys round-trip test, no
  value/status/class change): 9366134 — `_door`, `classify_cell`, `baseline_table` compare key sets;
  natural RED on the old prereg (`SystemExit ... a cell has exactly the fields ...`), green on the new;
  old-vs-new comparison all `True` (cells 48/48, class_counts, tie_audit, statuses, baseline, gate2
  rows, ENTRIES, projections).
- Ruling i, shown to Rafael before "reviewed" (committed R_a x G_q; R_q and G_a not measured until
  E6 runs): collapse disagreement 9 (prefixes 9, M2 0), damage 24 (prefixes 24, M2 0),
  REVERSE_DISAGREEMENT 0, undecided 0; G_q tie audit: flips [], exact tie k8/person_name (INTACT by
  strict >).
- Rafael replied "reviewed" on 2026-10-05 (recorded in a9fa058). The prereg is frozen (D-27).

## Task 2 — full suite on the committed state

- HEAD: a9fa058eb99112ad3e8bd231b6ee759c035e4739
- `shasum -a 256 scripts/phase39_prereg.py`:
  4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297
- `git status --porcelain -- scripts src results tests ledger artifacts`: empty;
  `git ls-files 'results/phase39_*'`: empty.
- Suite: `4171 passed, 4 skipped, 83 warnings in 2932.96s (0:48:52)`, `EXIT=0`. Skips 4 = the last
  green run's 4 (Phase 38 close: 4103 passed / 4 skipped): zero new skips.

## Downstream

The rulings changed the prereg API plans 05-07, 09 and 10 named; dated `<orchestrator_amendment>`
blocks were added to those plans (ce0bd2e, 6e7d7b2): CTX02_READINGS / CELL_READINGS, 48 cells per
event, `cells()` / `classify_cell(cell, values, k0)`, REVERSE_DISAGREEMENT, `class_counts` shape,
`tie_audit` replacing the driver's own audit, `baseline_table` (all slots; None on the 2-slot
rehearsal), and the per-token census callee set.

## Self-Check: PASSED
