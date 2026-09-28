---
phase: 33-admission-and-relearning-on-admitted-points
verified: 2026-09-28T21:45:00Z
status: passed
score: 4/4 roadmap success criteria verified (SC3 is the not-taken ADMITTED branch; SC4 is the branch the record selected)
overrides_applied: 0
---

# Phase 33: Admission and Relearning on Admitted Points — Verification Report

**Phase Goal:** Admission is called once on the v5.0 frontier, and every admitted point is attacked by relearning. If none is admitted, the MOOT branch ships as the pre-registered named limitation.
**Verified:** 2026-09-28
**Status:** passed
**Re-verification:** No. This is the first verification.

Everything below was re-derived from the files and from git. No SUMMARY claim was used as evidence unless a command confirmed it.

## Goal Achievement

### Observable Truths (roadmap SC1–SC4)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A continuation module reads the v5.0 frontier with its own expected point count and an arm-keyed `recall_threshold(frontier, leg, arm)`. `phase27_prereg.py` is byte-unchanged and its ancestry guard stays green (ADMIT-01) | VERIFIED | `scripts/phase33_admission.py::admit` calls `phase29_prereg.admission(json.loads(raw))` on `results/phase32_frontier.json`. `phase29_prereg.EXPECTED_POINTS = len(ADVR_ARMS)*len(RATIO_GRID)` = 12, and the frontier has 12 entries. A runtime trace I ran myself (monkeypatching `recall_threshold`) recorded 2 calls, `(frontier,'n8','advr')` and `(frontier,'n64','advr')`, with signature `(frontier, leg, arm)`. `git log -- scripts/phase27_prereg.py` returns one commit (916ad4d), there is no working-tree diff, and its live sha256 `18ed837a…` equals the record's pin. `tests/test_phase27_prereg.py` passes. |
| 2 | Admission is called exactly once, its record is write-once, and a second call refuses (ADMIT-02) | VERIFIED | `git log --format=%H -- results/phase33_admission.json` returns exactly one commit, `f48b7381…`, and `git show --name-only f48b738` lists only `results/phase33_admission.json`. I ran `.venv/bin/python scripts/phase33_admission.py admit` live: it exited 1 with "exists — REFUSING to overwrite it … there is no --force". The code refuses in this order: overwrite, then committed-at-HEAD-but-absent (`git rev-parse --verify -q HEAD:<rel>`), then dirty (`refuse_if_dirty`, with a pathspec that excludes only the record). All three refusals come before any digest. |
| 3 | ADMITTED branch: cost-to-recovery curve, disjoint recovery fixture, budget/seed refusal, published qualification (RELRN-06..09) | NOT TAKEN (correct) | The record reads `verdict: "MOOT"` and `admitted_point_keys: []`. I recomputed `phase29_prereg.admission(frontier)` independently and it equals the committed `admission` block exactly. `relearning_scope` also matches; the only difference is tuple vs JSON list. So this branch was not a decision: the record rules it out. |
| 4 | MOOT branch: RELRN-06..09 are recorded as a named limitation citing PREREG-02 (committed before any point ran), the attack legs refuse on the record, and no relearning number is produced | VERIFIED | (a) REQUIREMENTS.md:678-681 holds four cells reading "NOT SATISFIED — named limitation: admission read MOOT (results/phase33_admission.json, commit f48b738; scope rule PREREG-02, phase29_prereg.SCOPE_RULE)", and RELRN-06..09 stay `[ ]`. (b) PREREG-02's `SCOPE_RULE` landed in e44f045 (2026-09-24), which is an ancestor of the frontier's add commit. The first Phase 32 point record is dated 2026-09-27. (c) I ran all four legs live (calibrate, curve, gate, structural-proof). Each exited 1 with the same stderr, sha256 `0e6654ed…c45b`, which equals the committed-state `e_<leg>_after` captures and the `e_<leg>_before` digests recorded in 33-02-SUMMARY. (d) `results/` holds no phase33 file except the admission record, and `refuse_leg` has no code path that writes anything. The record's `limitation` block is bound from the admission reasons and the frontier's `tallies_by_leg` (advr_n8 0/6/0/0, advr_n64 REFUSED 6). |

**Score:** 4/4. SC3 is correctly not exercised, because the committed record selects SC4.

### Plan must-haves (merged; beyond the SCs)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Contract imported by reference; the driver defines none of it | VERIFIED | `RECORD_PATH`/`FRONTIER_PATH` are derived from `phase29_prereg.V5_RESULT_PATHS`, and `SCOPE_RULE`, `VERDICTS` and `COMMITTED` are read from the prereg. `test_the_contract_is_imported_by_reference` passes. |
| Legs refuse on MOOT/REFUSED/CANDIDATE-UNREPLICATED/INCONCLUSIVE/absent/uncommitted/forged-ADMITTED and write nothing | VERIFIED | `refuse_leg` ends in an unconditional `SystemExit` even after an ADMITTED verdict passes. Parametrized tests and the forged-ADMITTED tests pass. |
| No `scripts/phase33_*.py` imports `phase32_points` (AR-32-02), with a natural RED | VERIFIED | grep finds only a docstring mention. The AST census plus the natural-RED test on `tests/test_phase32_points.py` passes. |
| Three-state git tests assert non-shallow first | VERIFIED | `_assert_not_shallow()` is called first in each history test (test file, lines 298-347). |
| Suite EXIT=0 on the 33-01 tree before `admit`, with no code change up to the record commit | VERIFIED | `suite_3301.sha` = `3262402…`, and the log tail reads "3261 passed, 4 skipped … EXIT=0". `git diff --stat 3262402 f48b738 -- scripts src tests` is empty. The record's `git_sha`/`head_at_write` = 92fe48b, a docs-only commit on top of 3262402. |
| Full suite green after the record commit | VERIFIED | `suite.sha` = `f48b738…`, and the log tail reads "3261 passed, 4 skipped … EXIT=0". |
| Record pinned both ways to the frontier and the modules | VERIFIED | The frontier sha256 `4a4bcb60…` and 56857 bytes match live. All 7 `module_sha256` entries match the live files, including `phase33_admission.py` `2041aecc…`, which is identical at 92fe48b and HEAD. |
| D-05 developer approval before commit | VERIFIED (by record) | 33-02-SUMMARY:11 quotes the reply "aprooved". The record commit f48b738 (17:34) comes after the admit run and is committed alone. Human authorship is attested only by the SUMMARY quote and commit ordering. |
| 33-03 ledger rows, ticks, hand-edits, report check | VERIFIED | The 33-03-SUMMARY table holds P31-WR-01, P32-CR-01/WR-01..05/IN-03 and ACTRL-01, one disposition each. The cited commits 325aaf0, f7c1a83 and 4339f2b exist. `grep add_commit results/phase32_*.json` shows 8 values, all `4339f2b…`, matching the IN-03 continuation. ADMIT-01/02 are `[x]`, and ACTRL-01 is unticked. STATE.md frontmatter `status`/`progress` are untouched in 6b20c55; only stopped_at, last_updated and Current Position changed. `phase28_report.py check` exits 0. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase33_admission.py` | admit + 4 refusal-only legs | VERIFIED | 265 lines, substantive. It is wired to `phase29_prereg.admission`/`relearning_scope`, `phase25_run.atomic_write_json` and `refuse_if_dirty(pathspec=DIRTY_PATHSPEC, cwd=_GIT_ROOT)`. |
| `tests/test_phase33_admission.py` | once-proofs, provenance, censuses | VERIFIED | 536 lines. Contains `test_the_record_was_committed_exactly_once_alone`, and the file passes. |
| `results/phase33_admission.json` | write-once record | VERIFIED | 2167 bytes, sha256 `ae81eada…6ca973` (matches 33-02-SUMMARY), committed once and alone. |
| `.planning/REQUIREMENTS.md` | ADMIT ticks + RELRN named-limitation cells | VERIFIED | Lines 627-628 and 676-681. |
| `33-03-SUMMARY.md` | Phase 34 ledger rows | VERIFIED | Contains `P31-WR-01`. |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| phase33_admission.py | phase29_prereg.admission / relearning_scope | direct call on frontier bytes | WIRED (runtime-traced) |
| phase33_admission.py | phase25_run.atomic_write_json | the single write in admit | WIRED |
| phase33_admission.py | personacore.provenance.refuse_if_dirty | pathspec=DIRTY_PATHSPEC, cwd=_GIT_ROOT | WIRED |
| results/phase33_admission.json | results/phase32_frontier.json | frontier.sha256/bytes | WIRED (digest recomputed; ancestry test passes) |
| REQUIREMENTS RELRN cells | results/phase33_admission.json | path + commit f48b738 | WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| admission record `admission`/`scope` | verdict, reasons, control readings | `phase29_prereg.admission` on the committed frontier | Yes. The independent recompute is equal. | FLOWING |
| record `limitation` | leg lines | admission reasons + frontier `tallies_by_leg` | Yes (advr_n8 counts; the advr_n64 reason is verbatim) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Each leg refuses on the MOOT record | `.venv/bin/python scripts/phase33_admission.py {calibrate,curve,gate,structural-proof}` | exit 1 ×4, identical stderr sha256 `0e6654ed…` = committed-state captures | PASS |
| Second admit refuses | `.venv/bin/python scripts/phase33_admission.py admit` | exit 1, "exists — REFUSING to overwrite" | PASS |
| Targeted tests | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase33_admission.py tests/test_phase27_prereg.py tests/test_phase29_prereg.py` | 148 passed | PASS |
| Report guard | `.venv/bin/python scripts/phase28_report.py check` | exit 0 | PASS |
| Tree untouched by checks | `git status --short` | only the pre-existing ` D .claude/scheduled_tasks.lock` | PASS |

### Probe Execution

Not applicable. No probe scripts are declared by the phase plans, and this is not a migration phase.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| ADMIT-01 | 33-01, 33-03 | SATISFIED | SC1 evidence; ticked `[x]` at REQUIREMENTS.md:627 |
| ADMIT-02 | 33-01, 33-02, 33-03 | SATISFIED | SC2 evidence; ticked `[x]` at REQUIREMENTS.md:628 |
| RELRN-06 | 33-01..03 | NAMED LIMITATION (the D-09 / SC4 success path) | REQUIREMENTS.md:678; the `curve` leg refuses on the record |
| RELRN-07 | 33-01..03 | NAMED LIMITATION (D-09 / SC4) | REQUIREMENTS.md:679; the `gate` leg refuses |
| RELRN-08 | 33-01..03 | NAMED LIMITATION (D-09 / SC4) | REQUIREMENTS.md:680; the `structural-proof` leg refuses |
| RELRN-09 | 33-01..03 | NAMED LIMITATION (D-09 / SC4) | REQUIREMENTS.md:681; the `calibrate` leg refuses |

Every phase ID is accounted for, and REQUIREMENTS.md maps no orphaned ID to Phase 33.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| scripts/phase33_admission.py, tests/test_phase33_admission.py | — | TBD/FIXME/XXX/TODO/HACK | none found | — |
| scripts/phase33_admission.py | `refuse_leg` | The committed-at-HEAD check is skipped for a record path outside `_GIT_ROOT` | Info | No impact. The function still ends in an unconditional refusal, so no path runs a leg body. |
| results/phase33_admission.json | `limitation.requirements` | Order follows `LEGS` (09, 06, 07, 08) rather than numeric order | Info | Cosmetic. The record is write-once and must not be edited. |

### Human Verification Required

None outstanding. The two manual-only items in 33-VALIDATION.md were both completed during 33-02: the live before/after leg captures (I re-verified them against the capture files and a fresh run) and the D-05 developer review (attested by the quoted reply and commit ordering).

### Gaps Summary

None. The committed admission record, independently recomputed from the committed frontier, reads MOOT, so the phase took the SC4 branch as pre-registered. The admission record exists once, alone, and pinned. The attack legs refuse on it with byte-identical output. RELRN-06..09 carry the named-limitation cells, and no relearning number exists anywhere in `results/`.

---

_Verified: 2026-09-28T21:45:00Z_
_Verifier: Claude (gsd-verifier)_
