---
phase: 39-instrument-context-2-2
plan: 02
subsystem: pre-registration
tags: [prereg, e6, ctx-02, ctx-03, gate2, classifier, wr-01]
requires:
  - scripts/phase39_prereg.py (plan 01: READINGS, SLOTS, MARGIN, K, STATUSES, CLASSES, A2_RECORDS, MINTED_SET_SIZE, E6_ENTRY_SUBSET, ENTRIES["e6_decomposition_rule"])
  - scripts/phase38_prereg.py (a2_counts, committed_gate_ranks, rank_in_prefix, RETRAIN_SCORES, MINTING_RECORD)
  - scripts/phase19_run.py (_pooled_rows), scripts/erasure_gate.py, scripts/phase20_gate_coverage.py
provides:
  - "scripts/phase39_prereg.py section 9: _values, verify_a2_records, committed_a2_counts, gate2, draw_rate, predicted_hit_rate, unit_of, anchor_seed_index, e6_entries, minted_members"
  - "scripts/phase39_prereg.py section 10: damage_reachable, rank_status, count_status, _wr01, classify_cell, class_counts, n1, median_rank, rank_of_mean_nll"
  - "tests/test_phase39_prereg.py sections 8-9: gate 2 on the real tracked JSON, tamper and mismatch legs, D-23b premise, the 256-combination truth table, the committed-data oracle"
affects:
  - plan 39-03 review (code vs the written precedence; the M9 12-vs-9 collapse discrepancy)
tech-stack:
  added: []
  patterns: [lazy heavy imports inside functions, _prove SystemExit, statuses by STATUSES index]
key-files:
  created: []
  modified:
    - scripts/phase39_prereg.py
    - tests/test_phase39_prereg.py
decisions:
  - "gate2 returns passed False on a count mismatch (no SystemExit); only a digest mismatch exits"
  - "the D-23b realized_injection check runs on all eight A2 records, not only adapter-on (216/216 in each)"
  - "class_counts shares are keyed by the four sufficiency classes plus the two WR-01 outcomes (the classes a disagreement cell can take)"
requirements-completed: []
# This plan contributes to CTX-02 and CTX-03; the orchestrator ticks requirements at phase close.
metrics:
  completed: 2026-10-04
  tasks: 2
  files: 2
---

# Phase 39 Plan 02: E6 prereg pure definitions: summary

`scripts/phase39_prereg.py` now implements the rule that plan 01 wrote down:
- gate 2 over the eight SHA-verified A2 records
- the committed counts
- the D-07 draw rates
- the D-17 prediction
- the D-28 anchor seed index
- the entry and minted-member doors
- the per-reading statuses
- the four-step classifier
- the class counts with their denominators
- the rank summaries

All of it is tested on synthetic inputs (the full truth table) and on committed data.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 55d57ef | feat(39-02): phase39 prereg gate 2, committed A2 counts, D-07 rates, D-17 prediction, seed index, entry and minted doors |
| 2 | a5906b7 | feat(39-02): phase39 prereg statuses, per-cell classifier, class counts and rank summaries |

## RED outputs (tests first)

Task 1, before section 9 existed (`-k "gate2 or a2_sha or premise or seed or minted or rate or predicted or committed or values"`):
```
E       AttributeError: module 'phase39_prereg' has no attribute '_values'
13 failed, 4 passed, 24 deselected in 1.53s
```
Task 2, before section 10 existed (`-k "classify or lost or reachab or rank_summaries or class_counts"`):
```
12 failed, 41 deselected in 1.33s
```

## Acceptance lines, as printed in this session

Task 1:
```
16 passed, 25 deselected in 2.24s     (-k "gate2 or a2_sha or premise or seed or minted or rate or predicted or committed")
41 passed in 4.40s                    (tests/test_phase39_prereg.py)
True 64                               (gate2(): passed, equal cells)
```
Task 2:
```
11 passed, 43 deselected in 0.98s     (-k "classify or lost or reachab")
181 passed in 29.84s                  (test_phase39_prereg, test_phase35_prereg, test_phase36_caps, test_phase21_sc5)
All checks passed!                    (ruff check .)
356 files already formatted           (ruff format --check .)
ls-files:[]                           (git ls-files 'results/phase39_*')
porcelain:[]                          (git status --porcelain -- scripts tests results)
```
Committed-data oracle, published disagreement (R_a INTACT and G_q LOST), printed by a one-off script:
```
collapse 9
damage 24
```
**Collapse count: measured 9, RESEARCH M9 says 12.** The 9 is pinned in `_COLLAPSE_CELLS`, and the discrepancy goes to the plan-03 review. The committed ranks I printed this session show `k78: {'pet_name': 2}` and `M2: {'pet_name': 2}`, so pet_name at k78 and at M2 has R_a LOST. All other classified readings have rank 1 in every slot.

Other premises I measured this session, all matching the plan's interfaces:
- `repr(MARGIN)` printed `0.2962962962962963`, which equals 8/27.
- The exact eight-question drops at n = 27 where the committed formula decides damage are `[15, 17, 19, 21]`.
- The D-23b premise prints `premise 216 216 [1, 2]`.
- Each of the eight A2 records has 216 A2 rows, and all 216 carry their entry's `realized_injection`.
- The pooled counts per record match the interfaces table row for row, with `n_questions` `{27}`.

## Deviations from Plan

1. **[Rule 1 - Test bug] Rank-summary hand example.** In my first `test_rank_summaries` example the taught mean was 2.0, which ranks 1 among the means {2.45, 2.25}, not 2. I changed member `b` to `[0.5, 3.0]` (mean 1.75), so the taught rank is 2 by construction. The implementation was unchanged. Commit a5906b7.
2. **[Rule 3 - Census] Private helper `_wr01`.** The classifier's "UNREACHABLE_AT_SIZE first" choice lives in one helper, `_wr01`, which is used by steps 1 and 3. The every-function census counts private helpers, so `test_classify_wr01_helper_orders_unreachable_first` calls it directly. Separately, `test_reachability_threshold_is_derived` now calls `phase39_prereg.damage_reachable(` directly instead of through an alias, because the census only counts calls of the form `module.fn(`.
3. **D-23b scope widened.** The realized_injection check runs over all eight A2 records instead of only adapter-on. This is stricter than the behaviour bullet, and it held at 216/216 in each record.
4. **`_values()` only.** This plan's action list does not include a `_fact_slots` helper. I wrote one during Task 1 and removed it before committing. `minted_members` reads the taught value from `LOCKED_FACTS` by slot.

No gsd-sdk handler was called, and STATE.md, ROADMAP.md and REQUIREMENTS.md were not touched. I did not run the full suite.

## TDD Gate Compliance

Each task had a RED run, recorded above, and then GREEN. Following the plan's action ("commit both files"), each task has one `feat(...)` commit and no separate `test(...)` commit.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase39_prereg.py, tests/test_phase39_prereg.py
- FOUND: 55d57ef, a5906b7 (git log 979427c..HEAD)
