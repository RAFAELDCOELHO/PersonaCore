---
phase: 28-report-the-published-null-and-milestone-close
plan: 06
subsystem: docs
tags: [report, readme, byte-identity, ledger, freeze, phase-28]
requires:
  - "28-04 renderer (scripts/phase28_report.py, templates) and its committed records"
  - "28-05 guard files (tests/test_phase28_report.py, tests/test_phase28_prereg.py, tests/test_phase28_ledger.py)"
provides:
  - "docs/REPORT.md v4.0 section between PHASE28-REPORT sentinels (published, frozen)"
  - "README.md v3.0 + v4.0 glance bullets between PHASE28-GLANCE sentinels"
  - "byte-identity guards: test_report_block_is_byte_identical, test_glance_block_is_byte_identical"
  - "ledger row TD-XC-README-GLANCE -> FIXED"
affects:
  - "28-07 (milestone close; pushes this commit)"
tech-stack:
  added: []
  patterns:
    - "render-from-records + sentinel-bounded install + `==` byte-identity test as the drift guard"
    - "dated continuation via scripts/_addendum.py::append_addendum as the only post-publish correction route"
key-files:
  created: []
  modified:
    - docs/REPORT.md
    - README.md
    - tests/test_phase28_report.py
    - tests/test_phase25_correction.py
    - scripts/phase28_report.py
    - results/phase28_ledger.json
decisions:
  - "D-20 freeze: from commit 3b63b7d, `scripts/phase28_report.py write` is never run again in this phase; corrections are dated addenda via append_addendum"
  - "Renderer `_adv_points` now emits the condition (c) reasons or the refusal, not reasons[0] (condition (a)'s bare 0.0000% sentence) — STAT-02 guard and prose agreement"
metrics:
  duration: "2 sessions (Task 1 + checkpoint read, then Task 3 continuation)"
  completed: 2026-09-21
---

# Phase 28 Plan 06: Publish v4.0 — null at both capacities, rendered from committed records Summary

The v4.0 section (null result at both capacities) is published in `docs/REPORT.md` and the v3.0/v4.0 glance bullets in `README.md`, both rendered from the committed records by `scripts/phase28_report.py` and pinned by `==` byte-identity tests so the prose cannot drift from the records without going RED. Publishing commit `3b63b7d`; block frozen under D-20.

## Tasks

| Task | Name | Commit | Notes |
|------|------|--------|-------|
| 1 | Byte-identity tests RED→GREEN, register widened, ledger flip, install both blocks | 3b63b7d (folded into the publishing commit by design) | see transcripts below |
| 2 | Developer read of both rendered blocks (checkpoint:human-verify) | — | **"approved"**, 2026-09-21, no wording change |
| 3 | Publishing commit + post-commit `check` | 3b63b7d | `check` exit 0 on the committed tree |

## Task 1 evidence

**RED (before install, sentinels absent):**
```
4 failed  — test_report_block_is_byte_identical, test_glance_block_is_byte_identical (+ the two sentinel-presence guards): PHASE28-REPORT / PHASE28-GLANCE sentinels absent
```

**GREEN (after install):**
```
4 passed  (the same four)
81 passed — tests/test_phase28_report.py tests/test_phase28_prereg.py tests/test_phase28_ledger.py tests/test_phase25_correction.py tests/test_phase18_docs.py tests/test_phase15_docs.py
```

Re-run in this continuation before the commit: `make lint` green (ruff check + format --check, 288 files); the same six files → `81 passed in 17.88s`.

**Diff stats (publishing commit 3b63b7d):**

| File | Change |
|------|--------|
| docs/REPORT.md | +283 / −0, single hunk appended after line 1326, after every existing `## ` heading (D-01) |
| README.md | +19 / −0 at :111–128 inside `## Results at a glance`; `## ` heading count 12, unchanged (D-11) |
| tests/test_phase28_report.py | +136 / −1 — byte-identity tests + sentinel guards |
| tests/test_phase25_correction.py | register widened 2→5 (adds test_phase28_report.py, test_phase28_prereg.py, test_phase28_ledger.py); test renamed `test_the_register_still_routes_through_normalized`; "three files wide"/"THREE GUARD FILES" wording removed (D-22, D-26) |
| results/phase28_ledger.json | 3-line flip: TD-XC-README-GLANCE RE-DEFERRED → FIXED, evidence `1a89294; tests/test_phase28_report.py::test_glance_block_is_byte_identical` |
| scripts/phase28_report.py | `_adv_points` fix (deviation below) + `PUBLISHED = "2026-09-21"` |

## Task 2 — developer read

Checkpoint returned with both rendered blocks in the working tree, uncommitted. Developer response: **"approved"** (2026-09-21), no wording change requested. The publishing commit was made after the read, as D-20 requires.

## Task 3 — publishing commit

```
3b63b7d docs(28-06): publish v4.0 — null-at-both-capacities, rendered from committed records; README glance bullets; byte-identity guards (D-01, D-11, D-17, D-20)
 6 files changed, 466 insertions(+), 15 deletions(-)
```

Staged by explicit path, exactly the six files. Post-commit: `.venv/bin/python scripts/phase28_report.py check` → exit 0 on the committed tree (D-24). Pre-existing ` D .claude/scheduled_tasks.lock` left untouched.

**Full suite:** not run by this executor. The plan's background `make test` step belongs to the orchestrator, which runs it detached after this plan returns (the ~23 min suite does not fit the executor's gate).

## D-20 freeze statement

From commit `3b63b7d`, `scripts/phase28_report.py write` is **never run again in this phase**. The PHASE28-REPORT and PHASE28-GLANCE spans are frozen; the byte-identity tests pin them to the committed records. The only correction route is `scripts/_addendum.py::append_addendum` as a **dated continuation** appended below the block — never an edit of the published span.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Renderer `_adv_points` emitted the wrong reason sentence**
- **Found during:** Task 1, first render
- **Issue:** `_adv_points` emitted `reasons[0]`, which is condition (a)'s `0.0000%` sentence. That tripped STAT-02 `tests/test_phase25_correction.py::test_no_bare_zero_percent_in_docs` and contradicted the surrounding prose (the section argues from condition (c), not (a)).
- **Fix:** `_adv_points` now renders the condition (c) reasons, or the refusal when there are none; the table header reads `reasons (c), or the refusal`.
- **Files modified:** scripts/phase28_report.py (rendered output in docs/REPORT.md)
- **Commit:** 3b63b7d

No other deviations. Nothing pushed (28-07's checkpoint); STATE.md / ROADMAP.md untouched by this executor.

## Known Stubs

None.

## Self-Check: PASSED

- docs/REPORT.md contains `<!-- PHASE28-REPORT-BEGIN -->` — FOUND
- README.md contains `<!-- PHASE28-GLANCE-BEGIN -->` — FOUND
- commit 3b63b7d — FOUND (`git log`)
- `scripts/phase28_report.py check` — exit 0
