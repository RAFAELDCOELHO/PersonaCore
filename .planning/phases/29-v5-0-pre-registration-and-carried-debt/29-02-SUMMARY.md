---
phase: 29-v5-0-pre-registration-and-carried-debt
plan: 02
subsystem: testing
tags: [debt, in-07, frontmatter, phase17-archive]
requires: []
provides:
  - "DEBT-01: relearn untracked-record probe runs in a scratch repo (relearn._ROOT monkeypatched)"
  - "DEBT-03: 11 archived Phase-17 SUMMARYs validate as schema summary"
affects: [tests/test_phase27_relearn.py, .planning/milestones/v3.0-phases/17-multi-persona-isolation-matrix]
tech-stack:
  added: []
  patterns: ["scratch git repo + monkeypatched module _ROOT for git-tracked-ness probes"]
key-files:
  created: [tests/test_phase29_debt.py]
  modified:
    - tests/test_phase27_relearn.py
    - .planning/milestones/v3.0-phases/17-multi-persona-isolation-matrix/17-01-SUMMARY.md (through 17-11, 11 files)
key-decisions:
  - "Top-level duration/completed copied verbatim from each file's own metrics: block (D-18 as amended 2026-09-24); metrics: left untouched"
requirements-completed: []
# requirements-completed left empty per orchestrator override: DEBT-01/DEBT-03 closure is decided by the orchestrator.
duration: 8min
completed: 2026-09-24
---

# Phase 29 Plan 02: DEBT-01 and DEBT-03 Summary

The IN-07 relearn probe no longer writes into the real `results/`: it now runs in a scratch git repo with `relearn._ROOT` pointed at it, and a guard checks that the real `results/phase27_*` files are unchanged. All 11 archived Phase-17 SUMMARYs now pass `frontmatter.validate --schema summary`, and a test holds their values in place.

## Tasks

| Task | Commit | Result |
|------|--------|--------|
| 1 DEBT-01 scratch-root probe (D-16) | 5e0a1f3 | `test_a_leg_refuses_an_untracked_record_inside_the_repo` keeps its name, adds `tmp_path`/`monkeypatch`, creates the scratch repo with `git init` under `tmp_path.resolve()`, still asserts `not tracked` + `REFUSING`, then asserts: tracked `results/phase27_*` sha256 unchanged, `_real_tree_strays()` unchanged, porcelain clean, and no real-repo probe path |
| 2 DEBT-03 frontmatter (D-18 amended) + test | 5523d50 | +2/-0 per file (numstat verified on the commit); all 11 validate `valid: true, missing: []`; `tests/test_phase29_debt.py` checks the 6 keys, that top-level equals nested, and that `completed` equals the `git log --follow --diff-filter=A` first-add date |

## Verification

- `tests/test_phase27_relearn.py -k "untracked_record or provenance_digests"`: 2 passed. `scripts/phase27_relearn.py` is unchanged, and `git status --porcelain -- results/` is empty.
- `tests/test_phase29_debt.py`: 12 passed (11 parametrized + 1 count check). Ran on the committed tree.
- Natural RED: `_frontmatter` on the HEAD~1 blob of 17-01 is missing `['duration', 'completed']`.
- Archive readers and census: test_phase17_stats, test_phase16_driver/stats/ladder, test_phase28_ledger and test_phase21_sc5 gave 198 passed.
- ruff check + format --check are green on both test files.

## Deviations from Plan

- I made the frontmatter insertion with a short deterministic Python script instead of the Edit tool. It is still a hand edit: no gsd-sdk mutation handler was used. The script checked that the top-level keys were absent first, and numstat shows exactly +2/-0 per file.
- I added `test_all_eleven_phase17_summaries_are_covered` as a separate test for the "exactly 11" check, so `-k summary_frontmatter` selects exactly 11.
- The plan's verification line runs both files under one `-k` filter, which deselects the whole debt file. I ran the debt file on its own as well.

Plan-vs-code mismatches: none. The nested values and `--follow` dates I measured match the plan's interfaces table exactly (17-01..09 = 2026-08-14, 17-10/11 = 2026-08-15; durations as listed).

## Self-Check: PASSED

- FOUND: tests/test_phase29_debt.py, commits 5e0a1f3 and 5523d50.
