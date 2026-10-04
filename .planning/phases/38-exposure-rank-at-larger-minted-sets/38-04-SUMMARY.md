---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 04
subsystem: e5-minting
tags: [review, minting-record, freeze, RANK-01]
requirements-completed: []  # the orchestrator owns requirement ticks; RANK-01 closes at phase verification
key-files:
  created:
    - results/phase38_minting.json
    - .planning/phases/38-exposure-rank-at-larger-minted-sets/38-REVIEW.md
  modified:
    - scripts/phase38_prereg.py
    - tests/test_phase38_prereg.py
    - .planning/phases/38-exposure-rank-at-larger-minted-sets/38-CONTEXT.md
    - .planning/phases/38-exposure-rank-at-larger-minted-sets/38-07-PLAN.md
commits: [1e4b3e2, d33986c, fe80adc, 7357577, fabe210]
---

# 38-04 — review, real mint, minting record (run inline by the orchestrator)

Plan 04 was executed inline by the orchestrator (checkpoint plan, mechanical steps).

## Task 1 — code review before any candidate existed

- `/gsd-code-review 38` over scripts/phase38_prereg.py, scripts/phase38_mint.py and both tests:
  0 critical / 4 warning / 4 info (1e4b3e2). The reviewer ran the real mint into scratch (no STOP,
  stop_draw 58195) and matched every clause of `e5_minting_rule` against the code.
- WR-01 reproduced by the orchestrator (`0 BEFORE BEFORE`). Rafael's ruling: fix WR-01 with two
  named outcomes; nothing else. Fixed TDD (4 RED, then green) in d33986c: `relation(..., *,
  reachable=True)` returns UNREACHABLE_AT_SIZE (moved with 2 x rank_0 > |R|, via the new
  `moved_reachable`) and ALREADY_AT_K0 (event already true at k = 0); precedence UNREACHABLE,
  ALREADY_AT_K0, then the reference outcomes (orchestrator's choice within the ruling). Targeted:
  171 passed; ruff check / format clean.
- WR-02..04 and IN-01..04: known limitations (resolution table in 38-REVIEW.md, fe80adc).
  Rafael replied "reviewed".

## Task 2 — pre-record gate and the real mint

- `git status --porcelain -- scripts src results tests ledger artifacts`: empty. No
  results/phase38_* tracked or on disk. HEAD before the mint: `fe80adc488adc311a7da10188bf3cf4334417a30`.
- Full suite at fe80adc: `4007 passed, 4 skipped, 83 warnings in 2755.08s (0:45:55)`, EXIT=0
  (4 skipped = the 37-07 count; zero new skips).
- `.venv/bin/python scripts/phase38_mint.py`: `MINTING WRITTEN`, exit 0, 1:14 on CPU.
- From the file: seed 1337, per_slot 2048, max_draws 400000, stop_draw 58195; stream draws 58195,
  token_count 38007, duplicate 2452. provenance.run.git_sha == provenance.head_at_write ==
  fe80adc488adc311a7da10188bf3cf4334417a30. completion_source: phase17_personas_report.md,
  e7cf89d0…cf98, mps, 04e724c, 416. phase17_filter_proof passed, 3796 values. approval: D-21
  ruling verbatim; 0.467956566879681 / 77.83105039182757 / 0.5418565110509128 h.

| slot | n_cleared | max \|R\| | excluded | substring_forbidden | substring_minted | neighbour_d1 removed | clearance removed |
|---|---|---|---|---|---|---|---|
| person_name | 2125 | 512 | 0 | 2 | 136 | 1 | 0 |
| pet_name | 2048 | 512 | 1 | 14 | 393 | 4 | 1 |
| cat_name | 2113 | 512 | 0 | 6 | 143 | 1 | 0 |
| sibling_name | 4951 | 512 | 0 | 15 | 648 | 0 | 0 |
| hometown | 2087 | 512 | 0 | 12 | 468 | 0 | 0 |
| street | 2102 | 512 | 0 | 6 | 459 | 0 | 0 |
| birth_year | 219 | 220 | 7 | 0 | 0 | flagged only: 8→2, 32→11, 128→59, 220→101 | 0 |
| house_number | 8768 | 512 | 13 | 0 | 219 | flagged only: 8→1, 32→2, 128→10, 512→19 | 0 |

over_budget, roundtrip, in_question (and token_count for the numeric slots) removed 0 everywhere.

- Stop decider (measured, not a record field): `derive()` with MAX_DRAWS = 58194 in scratch gave a
  D-26 STOP with pet_name at 2047 and every other name slot >= 2048 — pet_name decided the stop at
  draw 58195.
- Verify mode before the commit: `MINTING VERIFIED`, file sha256 b17b8c01…b519 unchanged.

## Task 3 — Rafael approved

Presented with the HEAD/git_sha/head_at_write triple, the porcelain line, per-slot removals and the
stop decider (as Rafael asked). Reply: "approved", plus a report note recorded as D-36 (fabe210,
before any rank): grammar-syllable candidates vs English-compound-like taught values; the report's
Limitations section says so and tells the reader to read each curve beside adapter-off. No rule or
definition change. Amended into 38-07's report spec together with the WR-01 downstream requirement.

## Task 4 — commit and post-commit suite

- 7357577 commits exactly `results/phase38_minting.json` (scripts/phase38_prereg.py now frozen).
- Verify mode on the committed state: `MINTING VERIFIED`, sha256 unchanged.
- Targeted (prereg, mint, phase35_prereg, phase36_ledger, phase36_caps): 247 passed.
- Full suite at fabe210: `4007 passed, 4 skipped, 83 warnings in 2778.93s (0:46:18)`, EXIT=0 —
  no latent red, no test fix needed.

## Deviations

- Executed inline by the orchestrator rather than by a spawned executor.
- `.claude/scheduled_tasks.lock` shows as deleted in the working tree from before this session; not
  ours, never staged.
