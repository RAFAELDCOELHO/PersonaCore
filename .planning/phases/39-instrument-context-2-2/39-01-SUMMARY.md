---
phase: 39-instrument-context-2-2
plan: 01
subsystem: pre-registration
tags: [prereg, e6, ctx-01, ctx-03, phase35-fill, ancestry]
requires:
  - scripts/phase35_prereg.py (fill, a2_corpus_entries, V6_RESULT_PATHS, FULL_FIDELITY_K)
  - scripts/phase38_prereg.py (READINGS, PREFIXES, SLOTS, MARGIN, relation, record paths)
  - scripts/phase36_prereg.py (front_stop_factor)
  - results/phase36_budget.json (unit_caps.E6, unit_prices, front_hours.E6, cap_rulings)
provides:
  - scripts/phase39_prereg.py: record paths, eight A2 pins, D-11/D-26/D-30 approval arithmetic, approval_block(), NOT_MEASURED, twenty ENTRIES, E6_ENTRY_SUBSET and E6_DECOMPOSITION_RULE fills
  - tests/test_phase39_prereg.py: arithmetic, pins, fills, ancestry trio, verbatim rulings, literal scan, schema, import probe, slot census, zero skips, every function called
affects:
  - tests/test_phase36_caps.py owner scan (now on its live branch, e6_entry_subset = 216 entries)
  - tests/test_phase35_prereg.py slot census and slot ordering (scan scripts/phase39_*prereg.py)
tech-stack:
  added: []
  patterns: [phase38_prereg section skeleton, open-audit-hook import probe replacing the torch-free probe]
key-files:
  created:
    - scripts/phase39_prereg.py
    - tests/test_phase39_prereg.py
  modified: []
decisions:
  - "phase35_prereg.fill accepted the MappingProxyType entries directly; no dict(...) conversion was needed"
  - "hashlib and math are not imported in plan 01 (nothing uses them yet; ruff F401); plan 02 adds them with the functions that use them"
requirements-completed: []
# This plan contributes to CTX-01 and CTX-03; the orchestrator ticks requirements at phase close.
metrics:
  completed: 2026-10-04
  tasks: 3
  files: 2
---

# Phase 39 Plan 01: E6 pre-registration, first half: summary

`scripts/phase39_prereg.py` now holds everything that is fixed before any E6 number exists:
- the record paths
- the eight A2 record pins: seven parsed from the budget's E6 ruling, plus adapter-off typed once and tested against the tracked bytes
- the D-11/D-26/D-30 approval and its projections, computed at import from `results/phase36_budget.json`
- the twenty four-field ENTRIES that write out the whole decomposition rule
- both Phase 35 fills: `E6_ENTRY_SUBSET` (all A2 entries, derived) and `E6_DECOMPOSITION_RULE`

`tests/test_phase39_prereg.py` guards all of it. No `results/phase39_*` file exists, tracked or untracked.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | d05f18c | feat(39-01): phase39 prereg header, record paths, A2 pins and D-11/D-26/D-30 approval arithmetic |
| 2 | 06e3893 | feat(39-01): phase39 prereg ENTRIES (whole written E6 rule) and both Phase 35 fills |
| 3 | 6dd4779 | test(39-01): phase39 prereg guards: ancestry, verbatim rulings, literal scan, schema, import probe, census |

## RED outputs (tests first)

Task 1, before `scripts/phase39_prereg.py` existed:
```
E   ModuleNotFoundError: No module named 'phase39_prereg'
ERROR tests/test_phase39_prereg.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.50s
```
Task 2, before ENTRIES and the fills existed:
```
E       AttributeError: module 'phase39_prereg' has no attribute 'E6_ENTRY_SUBSET'
E       AttributeError: module 'phase39_prereg' has no attribute 'E6_DECOMPOSITION_RULE'
E       AttributeError: module 'phase39_prereg' has no attribute 'ENTRIES'
E       AttributeError: module 'phase39_prereg' has no attribute 'ENTRIES'
4 failed, 10 passed in 1.02s
```
Task 3 adds guard tests over code that was already committed. There is no RED state for them. Each guard instead carries a non-vacuity leg (natural-RED ancestry against `scripts/phase35_prereg.py`, plus planted literal, proposer, phrase, skip and untested-function copies, and four planted opens).

## Acceptance lines, as printed in this session

Task 1:
```
0.7293568082878159 0.7285258345864714 0.7424221732238463 ('results/phase39_ctx.json', 'results/phase39_ctx_report.md') 8 8 ('k0', 'k8', 'k16', 'k32', 'k64', 'k78', 'M2') ('k8', 'k16', 'k32', 'k64', 'k78', 'M2')
ls-files:[]
find:[]
```
Task 2:
```
20 216 tuple ['e6_projection_hours', 'e6_projection_hours_actual_gate', 'e6_stop_hours']
```
`tests/test_phase36_caps.py -k owner`: `3 passed, 32 deselected in 1.23s`. After the Task 2 commit, `test_owner_fill_files_respect_the_caps_on_the_real_repo` ran on its live branch: `_owner_values` returned `['e5_set_sizes', 'e6_entry_subset']`, and `e6_entry_subset` had 216 entries. The test printed `1 passed in 1.05s`.

Task 3:
```
171 passed in 30.10s          (test_phase39_prereg, test_phase35_prereg, test_phase36_prereg, test_phase36_caps, test_phase21_sc5)
All checks passed!            (ruff check .)
356 files already formatted   (ruff format --check .)
3 passed, 24 deselected in 1.77s   (-k "frozen or first_added or records_at_commit")
3 passed in 6.21s             (slot_census_is_green_on_the_real_tree, slot_ordering_is_green_on_the_real_repo, owner caps)
ls-files:[]
porcelain:[]
1 file already formatted      (ruff format --check scripts/phase39_prereg.py)
```
Before typing the adapter-off pin, I re-measured `git show HEAD:results/phase18_arm_adapter-off.json` and got sha256 `08fe96fbd9753f8b44a5eb67a69d1a2a0b062a666b5a2d5430c2a7476bb15535`, which matches the plan's interfaces. The budget-ruling regex returned exactly 7 matches with the labels and paths the plan states.

## Deviations from Plan

1. **[Rule 3 - Blocking] `hashlib` and `math` not imported.** The plan says to import "exactly as phase38_prereg.py:24-51". Nothing in plan 01's content uses these two modules, so `ruff check` (a verify command) fails with F401. They are left out instead of added with `noqa`. Plan 02 should import them alongside the functions that need them. Commit d05f18c.
2. **Test placement.** I wrote `test_preferences_are_labelled` in Task 2, keyed by entry name through `_UNCONFIRMED` as Task 3 item 7 specifies, because it is the test for Task 2's fourth behaviour bullet. Task 3 did not duplicate it. The test file does not import `_HEAVY`, because the audit-hook probe replaces the torch-free probe as planned.
3. **Fill input type.** `phase35_prereg.fill` accepted the `MappingProxyType` entries as they are, so no `dict(...)` conversion was needed.

There were no other deviations. No gsd-sdk handler was called, and STATE.md, ROADMAP.md and REQUIREMENTS.md were not touched.

## TDD Gate Compliance

Tasks 1 and 2 each have a RED run, recorded above, followed by GREEN. The plan's action says to commit both files together after green, so each task has one `feat(...)` commit and no separate `test(...)` RED commit. Task 3 is guards only and has one `test(...)` commit.

## Known Stubs

None. The entries describe the rule. Plan 02 adds the pure functions that implement it, and that is planned, not a stub.

## Self-Check: PASSED

- FOUND: scripts/phase39_prereg.py
- FOUND: tests/test_phase39_prereg.py
- FOUND: d05f18c, 06e3893, 6dd4779 (git log f21b1b4..HEAD)
