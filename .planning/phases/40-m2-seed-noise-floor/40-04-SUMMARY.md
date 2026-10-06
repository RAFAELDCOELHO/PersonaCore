---
phase: 40-m2-seed-noise-floor
plan: 04
subsystem: pre-registration review
tags: [prereg, review, freeze, noise-01, noise-02]
requires:
  - scripts/phase40_prereg.py (plans 02-03)
provides:
  - 40-REVIEW.md (findings, Resolution 2026-10-06, Clarifications c and f)
  - scripts/phase40_prereg.py reviewed and FROZEN at 8cf3b32
key-files:
  modified:
    - scripts/phase40_prereg.py
    - tests/test_phase40_prereg.py
    - .planning/phases/40-m2-seed-noise-floor/40-REVIEW.md
requirements-completed: []
completed: 2026-10-06
---

# Phase 40 Plan 04: Prereg review and freeze — Summary

The code review (standard depth, 535a3f1) found 0 critical, 3 warnings, 7 info; every experiment was re-run by the orchestrator before Rafael saw it. Rafael ruled all fixed (IN-02 option a), confirmed a, b, e, f, g, h, i and changed c and e; clarified c (answer 1) and f (answer 2: three approvals); then replied "reviewed".

## Commits

- 535a3f1 review report
- 75a2ab5 WR-01, f3b50da WR-02, 9f4592a WR-03, 4b12a5d IN-01/IN-02(a), bc21cc3 IN-03, 97a06bf IN-04, 7dc13b6 IN-05, cf49c7e IN-06, 541da56 ruling c + IN-07, 01a33ee ruling e
- 0c80656 confirmations a-c, e-i (2026-10-06, verbatim; quotes byte-equal to his reply, checked by the orchestrator)
- 5fb3b2a 40-REVIEW Resolution
- 391e1c0 clarifications c (answer 1) and f (answer 2: record_layout["approvals"], three steps), 8cf3b32 40-REVIEW clarifications

Rafael's replies were pasted text (proposto pelo Claude (claude.ai), adotado por Rafael).

## Frozen prereg

- HEAD: 8cf3b32124f72359485a9f112fd7e3e0b97d4e31
- `shasum -a 256 scripts/phase40_prereg.py`: a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2
- Rafael: "reviewed" (2026-10-06), after seeing the 5fb3b2a..8cf3b32 diff and this sha256.

## Task 1 verify

```
14
UNCONFIRMED []
53 passed
```

## Task 2: full suite on the committed state

`git status --porcelain -- scripts src results tests ledger artifacts` empty at launch (HEAD 8cf3b32).

```
4353 passed, 4 skipped, 83 warnings in 3182.45s (0:53:02)
EXIT=0
```

Zero new skips against the last green run (4346 passed / 4 skipped at 8e9a912). `git ls-files 'results/phase40_*'` empty. Only `.planning/` commits landed while it ran (8d19450, 11bef70, 5534938: plans 05-11 revised for the 40-04 rulings; checker 1B/5W/5I -> 0B/1W/1I, both fixed by hand).

## Deviations

- Rulings c and e changed the prereg (D-13 failure never drops a seed: D13_FAILURE_KINDS, d13_not_measured, d13_reading; floors carry n_seeds/n_pairs). Plans 05-11 were revised to them before any driver code.
- Two values changed as consequences beyond the item table: d13_addition.anchor_gate text (c) and the estimator's adapter_off text (IN-02); both in the reviewed diff.
