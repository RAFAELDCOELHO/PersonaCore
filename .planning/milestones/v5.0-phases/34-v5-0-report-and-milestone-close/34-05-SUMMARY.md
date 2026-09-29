---
phase: 34-v5-0-report-and-milestone-close
plan: 05
subsystem: v5.0 publication (docs/REPORT.md, README.md)
tags: [report, publish, byte-identity, freeze, R-1]
requires: [scripts/phase34_report.py (34-04), results/phase34_ledger.json (34-03), scripts/phase28_report.py (frozen)]
provides: [docs/REPORT.md PHASE34-REPORT block, README.md PHASE34-GLANCE block, install-side tests in tests/test_phase34_report.py, Phase 28 placement guards scoped to the v4.0 block]
affects: [34-06 (milestone close; ticks RPT-04 / plan lines)]
tech-stack:
  added: []
  patterns: [install-inverse stripping, history-based deleted-nothing proof, later-milestone blocks derived from sentinels (never a typed stem)]
key-files:
  created: []
  modified:
    - docs/REPORT.md
    - README.md
    - scripts/phase34_report.py
    - tests/test_phase34_report.py
    - tests/test_phase28_report.py
decisions:
  - "PUBLISHED re-pinned 2026-09-28 -> 2026-09-29 before `write`: the publishing commit landed on 2026-09-29 (carried D-24)"
  - "Developer approved the read on 2026-09-29: OQ2 columns, OQ3 mapping, P31-WR-01 reword, OQ5 by-reference row, executor choices (a)-(d); glance source wrapping left as is"
  - "test_install_deleted_nothing is history-based (oldest commit holding the sentinel vs its parent), so a later sanctioned continuation never reddens it"
requirements-completed: []
# RPT-04 is not ticked here: ticks happen only in 34-06 Task 2 (D-16, carried D-34).
metrics:
  duration: two sessions (Task 1 on 2026-09-28; Task 3 on 2026-09-29, including the 38m36s full suite)
  completed: 2026-09-29
---

# Phase 34 Plan 05: v5.0 published — admission MOOT, per-leg outcomes, frozen

The v5.0 section is now in docs/REPORT.md, appended after `<!-- PHASE28-REPORT-END -->`, and the v5.0 bullet is in README.md, directly above `<!-- PHASE28-GLANCE-BEGIN -->`. Both were installed once with `scripts/phase34_report.py write`. Both are byte-identical to a fresh render, and the install deleted no lines. The frozen v4.0 block still re-renders byte-identical: `phase28_report.py check` gives 0, and `scripts/phase28_report.py` is unchanged. The install turned exactly three Phase 28 placement guards RED, as predicted. Each was then scoped to the v4.0 block with a dated-continuation comment (R-1).

## Commit

| Task | Commit | Files |
|------|--------|-------|
| 1 | none (per plan) | tests/test_phase34_report.py (carried into the publishing commit) |
| 2 | none (human read) | — |
| 3 | `226b489` (publishing commit, author date 2026-09-29) | docs/REPORT.md, README.md, scripts/phase34_report.py, tests/test_phase28_report.py, tests/test_phase34_report.py |

```
 README.md                    |  12 ++++
 docs/REPORT.md               | 128 ++++++++++++++++++++++++++++++++++++
 scripts/phase34_report.py    |   2 +-
 tests/test_phase28_report.py |  63 +++++++++++++++---
 tests/test_phase34_report.py | 151 ++++++++++++++++++++++++++++++++++++++++++-
 5 files changed, 345 insertions(+), 11 deletions(-)
```
`git diff 226b489~1 226b489 -- docs/REPORT.md README.md | grep -c '^-[^-]'` → `0`.

## Task 1: install-side tests, natural RED (2026-09-28)

tests/test_phase34_report.py gained section (8), with 11 test functions and 12 test ids (`test_install_deleted_nothing` runs once per file):
- sentinels occur exactly once (report, glance);
- byte-identical (report, glance);
- the report block follows the v4 block;
- the glance sits directly above the v4 glance;
- `test_install_deleted_nothing`;
- `test_write_refuses_once_installed`;
- `test_write_installs_pre_publish_then_refuses`;
- `test_published_date_is_pinned_not_clocked`;
- `test_install_glance_refuses_without_exactly_one_v4_anchor`.

The strict `_span`, `_markers`, `_git` and `_unified` are imported from test_phase28_report. `test_write_refuses_once_installed` first asserts that both spans exist, so before the install it cannot pass vacuously.

```
FAILED tests/test_phase34_report.py::test_report_sentinels_occur_exactly_once
FAILED tests/test_phase34_report.py::test_glance_sentinels_occur_exactly_once
FAILED tests/test_phase34_report.py::test_report_block_is_byte_identical - As...
FAILED tests/test_phase34_report.py::test_glance_block_is_byte_identical - As...
FAILED tests/test_phase34_report.py::test_placement_report_block_follows_the_v4_block
FAILED tests/test_phase34_report.py::test_placement_glance_sits_directly_above_the_v4_glance
FAILED tests/test_phase34_report.py::test_install_deleted_nothing[docs/REPORT.md-PHASE34-REPORT]
FAILED tests/test_phase34_report.py::test_install_deleted_nothing[README.md-PHASE34-GLANCE]
FAILED tests/test_phase34_report.py::test_write_refuses_once_installed - Asse...
FAILED tests/test_phase34_report.py::test_write_installs_pre_publish_then_refuses
10 failed, 21 deselected in 1.21s
```
Every failure message has the form `<file>: <!-- PHASE34-{REPORT,GLANCE}-BEGIN --> occurs 0 time(s)`.

I also rehearsed Task 3 in a fresh clone of 1862e7f, away from the main tree:
- `write`, then the phase34 tests: 31 passed;
- 0 deletions in REPORT and README;
- both `check` commands: 0;
- phase28: 3 failed, 23 passed, and the three failures were exactly the R-1 set.

Pre-install gates:
- `phase28_report.py check` → 0;
- `test_phase28_report.py`, `test_phase18_docs.py` and `test_phase15_docs.py` → 41 passed.

The scratch render for the read contained `phase34_report.md` (126 lines), `phase34_glance.md` (11 lines) and `ledger.txt`. The ledger had 61 rows: ACCEPTED 15, FIXED 19, NAMED-LIMITATION 7, RE-DEFERRED 20. Five rows are carried by reference: three v4.0 and two v3.0.

## Task 2: developer read

**approved 2026-09-29** (message: "approved"). The developer accepted every item as shown and asked for no template or ledger edits:
- **OQ2:** the comparison table columns, v4 `label` + `quoted_reasons` beside v5 `state` + `verdict` + `cleared_c`, with `notes` quoted verbatim, are accepted.
- **OQ3:** the mapping is accepted:
  - P32-WR-02 → ACCEPTED;
  - P32-WR-03 → FIXED;
  - P32-IN-03 → RE-DEFERRED (code fix);
  - ACTRL-01 → NAMED-LIMITATION.
- **P31-WR-01 reword:** "is not reached on the MOOT branch" is accepted.
- **OQ5:** the by-reference row P34-RPT05-SUPERSEDED-NODE (ACCEPTED) is accepted.
- **Executor choices (a)-(d):** all accepted:
  - (a) P28-P22-WARNING-4 and -5 are NAMED-LIMITATION;
  - (b) the ACCEPTED dispositions (not RE-DEFERRED) for P29-IN-02..04, P30-WR-03, P30-IN-01..03, P31-WR-02, P31-IN-01/03/04 and P32-AR-01;
  - (c) the added row P31-VERIFICATION-VALIDATION-FRONTMATTER;
  - (d) the by-reference count of 5 (3 v4.0 + 2 v3.0).
- **Glance source wrapping:** the mid-phrase line breaks in the bullet's raw source stay as they are, since rendered Markdown shows one line.

## Task 3: publish (2026-09-29)

**PUBLISHED re-pin.** Task 1 left `PUBLISHED = "2026-09-28"`. The approval and the publishing commit fell on 2026-09-29 (`date +%F`), so I set `PUBLISHED = "2026-09-29"` before `write`, following Task 1 step 4 and carried D-24. First I grepped for pins: no `results/*.json` mentions `phase34_report`, so no record's `module_sha256` pins the renderer. After the edit, the non-install tests passed: `38 passed, 10 deselected`. The rendered title now ends "(recorded 2026-09-29)", matching the publishing commit's author date.

`write` → `[phase34_report] installed both blocks (pre-publish only, carried D-20)`. Diff stat: README.md +12 and docs/REPORT.md +128, with 0 `-` lines in either.

The phase34 install tests are GREEN: `tests/test_phase34_report.py` → `31 passed in 1.63s`. `phase34_report.py check` gives 0 and `phase28_report.py check` gives 0.

**Natural RED (R-1)** over test_phase28_report, _prereg, _ledger, test_phase18_docs, test_phase15_docs and test_phase25_correction:
```
E       AssertionError: ('## v5.0 — admission MOOT: advr n8 PASS 0 of 6, INCONCLUSIVE 6 of 6; advr n64 REFUSED 6 of 6 (recorded 2026-09-29)', '## v4.0 — the published null: `null-at-both-capacities` (recorded 2026-09-21)')
E       assert 12 == (9 + 2)
E           SystemExit: [phase28_report] .../test_write_installs_pre_publis0/README.md: expected a blank line then a bullet after it
FAILED tests/test_phase28_report.py::test_report_section_is_after_every_prior_heading
FAILED tests/test_phase28_report.py::test_glance_deleted_nothing - assert 12 ...
FAILED tests/test_phase28_report.py::test_write_installs_pre_publish_then_refuses
3 failed, 84 passed in 22.35s
```
The failures are exactly the three predicted guards, with no other failures.

**Amendment (R-1).** Only these three guards changed in tests/test_phase28_report.py. Each now has a `# Dated continuation, 2026-09-29 (Phase 34 R-1): …` comment block; the file contains three of them. Three helpers were added next to the guards:
- `_later_stems(text, kind)` derives the stems `PHASE<n>-<kind>` with n > 28 from the text, so no stem is typed;
- `_without_later(text, kind)` removes each later block by the exact inverse of its install;
- `_stripped_text(text, stem)` is `_stripped`'s logic applied to a string.

The changes to the guards themselves:
- (a) headings are computed from `_without_later(whole, "REPORT")`;
- (b) the bullets of later GLANCE spans are subtracted from the section count, and the first-bullet-after-END check is unchanged;
- (c) the tmp inputs are `_stripped_text(_without_later(current, kind), PHASE28 stem)`, and the output is compared against `_without_later(current)`.

`_stripped`, the byte-identity tests and every other test are textually unchanged, and `git diff --quiet HEAD -- scripts/phase28_report.py` passes.

**GREEN after the amendment:** the same command gives `87 passed in 22.47s`. Both `check` commands give 0. `make lint` reports `All checks passed!` and `310 files already formatted`. The census run (34-04's list plus phase34, the ledger and package tests) gives `62 passed`.

## Full suite

Detached run on the committed tree `226b489`: `3311 passed, 4 skipped, 83 warnings in 2317.00s (0:38:36)`, `EXIT=0`. That is 34-04's 3299 plus the 12 new test ids, with 0 failed. Afterwards `phase28_report.py check` gave 0 and `phase34_report.py check` gave 0 again.

## Freeze (carried D-20)

Both PHASE34 blocks are now frozen. Any change to either block must be a dated continuation through `scripts/_addendum.py`. `write` will not be run again, and it refuses anyway once the sentinels are present, which `test_write_refuses_once_installed` pins. A future failure of a Phase 28/34 guard against a published block gets fixed in the test or by a dated continuation, never by a re-render.

## Deviations from Plan

- **PUBLISHED re-pin:** 2026-09-28 → 2026-09-29, done before `write` as Task 1 step 4 requires when the publishing day slips. It is not a post-publish edit.
- **Rehearsal in a scratch clone** (not in the plan) during Task 1, to confirm the R-1 premise before the developer's read. The main tree was untouched.
- **Orchestrator override of the plan's STATE.md hand-edit:** STATE.md, ROADMAP.md and REQUIREMENTS.md were not edited, and no gsd-sdk mutation handler was called.

## Self-Check: PASSED

- `226b489` exists with `--stat` showing exactly five files.
- The sentinels occur once each in docs/REPORT.md and README.md.
- Both `check` commands give 0 on the committed tree.
