---
phase: 34-v5-0-report-and-milestone-close
plan: 03
subsystem: results
tags: [ledger, rpt-04, D-11, D-12, D-13, D-14]
requires: [34-01, 34-02]
provides:
  - results/phase34_ledger.json (v5.0 disposition ledger, close.ci_run null)
  - tests/test_phase34_ledger.py (17 tests; derived census)
affects: [34-04 report render, 34-05 read checkpoint, 34-06 close.ci_run]
tech-stack:
  added: []
  patterns: [census derived at test time from REVIEW headings / staged table / SECURITY ids, by-reference rows carrying file sha256 + rows digest]
key-files:
  created:
    - results/phase34_ledger.json
    - tests/test_phase34_ledger.py
  modified: []
decisions:
  - "Four out-of-domain staged labels mapped: P32-WR-02 BY-REFERENCE->ACCEPTED, P32-WR-03 CLOSED->FIXED, P32-IN-03 DATED-CONTINUATION->RE-DEFERRED (code fix), ACTRL-01 NAMED-LIMITATION (partial exercise)->NAMED-LIMITATION"
  - "P28-P22-WARNING-4/5 re-disposed as NAMED-LIMITATION (DEBT-04 wording), so the v5.0 register holds 7 rows, not 5"
requirements-completed: []
# 34-03 contributes to RPT-04 / RPT-06 only; ticks happen in 34-06 after their evidence exists (D-16).
metrics:
  duration: ~50 min
  completed: 2026-09-28
  tasks: 2
  files: 2
---

# Phase 34 Plan 03: v5.0 disposition ledger Summary

`results/phase34_ledger.json` holds 61 rows. It uses the phase28 schema and closed domain, and RE-DEFERRED rows carry `target`/`prerequisite`. `tests/test_phase34_ledger.py` derives the census from every 29..33 REVIEW heading, every row staged in 33-03-SUMMARY and every AR-/UF- id in SECURITY.md. The phase28 ledger is byte-unchanged.

## Commit

| Task | Commit | Files |
|------|--------|-------|
| 1+2 (one commit, per plan) | 1855ce1 | results/phase34_ledger.json, tests/test_phase34_ledger.py |

## RED (Task 1, ledger absent)

```
FAILED tests/test_phase34_ledger.py::test_a_lowercase_disposition_is_red - Fi...
FAILED tests/test_phase34_ledger.py::test_a_re_deferred_row_without_a_target_is_red
17 failed in 0.44s
```
All 17 failed with `FileNotFoundError: ... results/phase34_ledger.json`. The census grep (`== 10` / `!= 10`, `train_arm(`, `os.replace`) found nothing.

## GREEN

- Before commit: `17 passed in 10.22s`
- On the committed tree: `143 passed in 35.13s` (phase34_ledger, phase28_ledger, phase29_prereg, phase21_sc5, phase28_report, test_resume_from_none_is_inert)
- Plus an earlier gate run: `127 passed in 24.34s` (phase29_prereg, phase21_sc5, test_os_replace_appears_only_in_the_two_phase25_writers, test_resume_from_none_is_inert, phase28_ledger, phase28_report)
- `git diff --quiet HEAD -- results/phase28_ledger.json`: unchanged. `git status --short results/ tests/`: empty. `scripts/phase28_report.py check`: `check_exit=0`. `make lint`: "All checks passed! / 308 files already formatted" (ruff fixed one import-sort before the commit).
- **Full suite: NOT run.** The orchestrator override forbids it. Step 6 of Task 2 is skipped, and no `EXIT=` line exists.

## Counts (len() over rows)

- Total: 61
- By disposition: ACCEPTED 15, FIXED 19, NAMED-LIMITATION 7, RE-DEFERRED 20 (CLOSED-EARLIER 0, FORBIDDEN-BY-GUARD 0)
- By milestone: v3.0 2, v4.0 3, v5.0 56
- NAMED-LIMITATION rows: ACTRL-01, RELRN-06..09, P28-P22-WARNING-4, P28-P22-WARNING-5

## Measurements (decisive command → output)

- **Phase28 by-reference values, recomputed:** file sha256 `a459cc2296cb7590b46ba3f608c22d84b6258d3ffc9aa4a804042425b991b2a0`, `ledger_rows_digest` `bb9f82fe290d7578a11e221c349733555e5c2f3d197673e56e39d8c65b00dbd7`. There are 5 RE-DEFERRED rows: TD-16-R1, TD-17-SUMMARY-FRONTMATTER, IN-07, P22-WARNING-4 and P22-WARNING-5.
- **Pinned modules:** I walked `module_sha256` over `results/phase3*.json` and compared each to the live sha256. Every pin matches except `scripts/phase30_points.py` in the phase30/31 records, which is covered by the 16f2c6d tripwire. So phase29_prereg (11 records), teach_persona (10), phase31_probe (10), phase31_budget, phase32_points (7), phase32_frontier and phase33_admission (live `2041aecc…` = pin) are all unchanged since their records. That makes every open finding in them still open, with no fix commit.
- **FIXED rows.** Each fix commit passed `git merge-base --is-ancestor <sha> HEAD`, and the node ids were read from the `def test` lines each fix commit added. `_fixed_violations` collected all 19 on the committed tree.
  - P29: CR-01 744165b, WR-01 0f0336f, WR-02 9179cd7, WR-03 79cd4c6, WR-04 a37e9a4, IN-01 49a4e9f
  - P30: CR-01 a7d5c9d, WR-01 8592610, WR-02 3562e52, WR-04 8dd1d30, WR-05 00bc4da, WR-06 28f8658, IN-04 f3785da
  - P32-WR-03: f7c1a83, node `tests/test_phase30_points.py::test_ast_guard_planted_red_per_class` (re-measured at :719), RED at 325aaf0
  - P28: TD-16-R1 b8027b8 (`test_d28_amended_note_reddens`), TD-17 5523d50 (`test_all_eleven_phase17_summaries_are_covered`), IN-07 5e0a1f3 (`test_a_leg_refuses_an_untracked_record_inside_the_repo`)
  - P34: PLIST-HOST-PATH abdb77d (both `test_plist_mirrors_the_canary_agent`), RPT05-DERIVED-TAGS bb50737
- **Still-open re-measurements:**
  - P29-IN-02: `grep 'd28_note('` finds no production caller.
  - P29-IN-03: `tests/test_phase16_driver.py:38` still imports at module scope.
  - P29-IN-04: phase29_prereg:402/406 duplicates phase27_prereg:325/330.
  - P30-WR-03: teach_persona:2059 prints replay_windows only on the DP branch. The point records carry `replay.per_step`: n8 ratio0 has 200 steps, all 32; n64 ratio0 has 200 steps, all 256.
  - P30-IN-01: test_phase23_resume:131, the comment is still misplaced.
  - P30-IN-02: loop.py is not in phase30_calibration's PINNED_MODULES but is pinned by the 7 point records.
  - P31-IN-02: `STAGES[:-1]` at :138.
  - P31-IN-04: the plist is absolute under /Users/juliorcoelho, and :19 still cites "(D-10)".
  - P31-IN-05: `_counting_train(**kwargs)` at :390.
  - P32-IN-06: `_is_tracked` still has 3 references.
  - 31-VERIFICATION:94: 31-VALIDATION now has `wave_0_complete: true` but still `status: draft`.
- **P32-IN-03 continuation:**
  - `git log --diff-filter=A -- results/phase30_calibration.json` → `4339f2b`
  - `--diff-filter=D` → (none)
  - `grep add_commit results/phase32_*.json | uniq -c` → `8 "4339f2b2bc29…"`
- **P33:**
  - record `git_sha` = `head_at_write` = 92fe48b
  - `git log -- results/phase33_admission.json` → f48b738 only
- **SECURITY files found:** {29, 32, 33}, with no 30-/31-SECURITY.md. The ids are AR-32-01/02/03, UF-32-01/02/03 and AR-33-01/02. 29-SECURITY.md has none. Each id is named in a row's source or evidence.

## Dispositions to flag at the 34-05 read checkpoint

1. **The four mapped staged labels (Open Question 3 recommendation):**
   - P32-WR-02 BY-REFERENCE → ACCEPTED
   - P32-WR-03 CLOSED → FIXED (f7c1a83 + node id)
   - P32-IN-03 DATED-CONTINUATION (2026-09-28) → RE-DEFERRED (code fix). The continuation evidence is in `evidence`.
   - ACTRL-01 NAMED-LIMITATION (partial exercise) → NAMED-LIMITATION
2. **P31-WR-01 reason reword (33 D-08):**
   - Staged: "The MOOT branch writes no relearning artifact, so the unreachable crash-recovery path is never exercised"
   - Ledger: "The MOOT branch writes no relearning artifact, so the crash-recovery path is not reached on the MOOT branch"
3. **P34-RPT05-SUPERSEDED-NODE (Open Question 5 recommendation):** ACCEPTED, by reference to the phase28 row SC3-SHA256-CLAUSE and the phase28 file sha256. That row's evidence still names `test_runtime_dependencies_identical_across_four_milestones`.
4. **Executor judgment: P28-P22-WARNING-4/5 → NAMED-LIMITATION**, following DEBT-04 ("re-recorded as a named limitation", `phase29_prereg.NAMED_LIMITATIONS['P22-WARNING-4/5']`). The v5.0 register and withheld block therefore render 7 NAMED-LIMITATION rows, not only ACTRL-01/RELRN-06..09. If the developer prefers them outside the register, the alternative is FIXED on 63ca8de + `test_named_limitations_record_p22_warning_4_5`.
5. **Executor judgment: ACCEPTED rather than RE-DEFERRED** for:
   - P29-IN-02..04 (developer skip ruling at 1328ec0)
   - P30-WR-03 (the replay count is now in every point record), P30-IN-01..03
   - P31-WR-02 (the residual is P32-CR-01), P31-IN-01/03/04
   - P31-VERIFICATION-VALIDATION-FRONTMATTER
   - P32-AR-01

   P31-IN-02 and P31-IN-05 are RE-DEFERRED (code fixes in pinned modules, targeting the milestone that re-derives or reuses them).
6. **The D-11 hand-off row:** P34-V5-TAG-HANDOFF, target `/gsd-complete-milestone v5.0`, prerequisite `git push origin main v5.0`.
7. **The D-14 rows:** P33-WR-01/02 and P33-IN-01..03 are RE-DEFERRED to "the milestone that reuses `phase33_admission`". The test proves live sha256 == pin.

Push-1 (34-02) found no CI-only causes, so there are no "FIXED per push-1 cause" rows. The push-1 run id is not in the ledger (R-3).

## Deviations from Plan

- **Full suite (Task 2 step 6) not run.** The orchestrator override forbids it (~40 min). The targeted gates above ran instead.
- **STATE.md hand-edit not done.** The orchestrator override says the orchestrator applies STATE. STATE/ROADMAP/REQUIREMENTS are untouched and no gsd-sdk mutation handler was called.
- **Extra row P31-VERIFICATION-VALIDATION-FRONTMATTER.** The plan asked to re-measure 31-VERIFICATION:94, and the item is still half open.
- **`_resolve` imported from test_phase28_ledger** for the record-field binding. This is in addition to the four names the plan lists.

## Self-Check: PASSED

- results/phase34_ledger.json and tests/test_phase34_ledger.py exist and are committed in 1855ce1 (`git show --stat` lists exactly these two files).

## Orchestrator addendum — plan step 6 (full suite)

Run by the orchestrator on the committed, clean tree at 72b7542 (the executor was told not to run it): `3280 passed, 4 skipped, 83 warnings in 2432.73s (0:40:32)`, EXIT=0.
