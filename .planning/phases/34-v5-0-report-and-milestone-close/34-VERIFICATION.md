---
phase: 34-v5-0-report-and-milestone-close
verified: 2026-09-29T12:34:39Z
status: passed
score: 3/3 roadmap SC verified; 32/32 plan must-have truths verified
overrides_applied: 0
---

# Phase 34: v5.0 Report and Milestone Close — Verification Report

**Phase Goal:** v5.0 is published as measured — every number rendered from a committed record — and the milestone closes on a green CI run of the developer's push.
**Verified:** 2026-09-29T12:34:39Z against HEAD `4d0ab76`. HEAD is `f3bb983` plus `docs(34): code review`, which touches only 34-REVIEW.md.
**Status:** passed
**Re-verification:** No. This is the initial verification.

Every reading below was taken in this session, inside the 3.11 venv (`.venv/bin/python`, Python 3.11.15).

One false RED during the session: I first ran the targeted tests with the pyenv 3.12 interpreter, which has no torch. `test_fixed_rows_cite_a_commit_and_a_collectable_test` failed because its `sys.executable` collect subprocess could not import torch. I re-ran inside the venv and it passed. It was not a code defect.

## Goal Achievement

### Roadmap Success Criteria

| # | Success criterion | Status | Evidence |
|---|---|---|---|
| SC1 | The v5.0 REPORT section and the README glance are rendered from committed records under the numeral scan, and the frozen v4.0 block re-renders byte-identical (RPT-04) | VERIFIED | `scripts/phase34_report.py check` exit 0. `scripts/phase28_report.py check` exit 0. `git diff --quiet HEAD -- scripts/phase28_report.py` exit 0; the file was last touched at `8a466d8`, before Phase 34. The numeral-scan and byte-identity tests are in the 82-test targeted run below, all passing. Sentinels: `docs/REPORT.md` has PHASE28-REPORT-END at :1609 and PHASE34-REPORT-BEGIN/END at :1611/:1737. `README.md` has PHASE34-GLANCE at :111–:122, directly above PHASE28-GLANCE-BEGIN at :123. The publishing commit `226b489` numstat shows README +12/−0 and REPORT +128/−0. Nothing in `docs/REPORT.md`, `README.md`, `scripts/` or `tests/` changed between `226b489` and HEAD. |
| SC2 | A test proves runtime dependencies identical across every milestone tag, v5.0 included (RPT-05) | VERIFIED | `tests/test_package.py::test_runtime_dependencies_identical_across_every_milestone_tag` derives its tags with the `_SHIPPED` regex over `.planning/MILESTONES.md`: v4.0, v3.0, v2.0 and v1.0 at :3/:98/:164/:189. HEAD stands in for v5.0 until `/gsd-complete-milestone` writes its Shipped heading; the D-11 hand-off is recorded as ledger row `P34-V5-TAG-HANDOFF`, RE-DEFERRED. In a scratch clone at a foreign root the test passed; with `v4.0` deleted it went RED with "shipped milestone tags missing from this clone". The superseded `..._four_milestones` test no longer exists (grep across tests/ is empty). `pyproject.toml` was last changed at `5065bc5`, before Phase 34. |
| SC3 | The milestone closes only on a green CI run of the developer's push, with its run id recorded; Claude never pushes (RPT-06) | VERIFIED | `gh run view 36562323069`: event push, branch main, conclusion success, headSha `dcc91f62380c8daa80613ebb9255ac8c4d7ed9eb`. The run log reads `3243 passed, 72 skipped`. `git merge-base --is-ancestor 226b489 dcc91f6…` exit 0. `results/phase34_ledger.json::close.ci_run` records that id, head sha, url, conclusion and `2026-09-29`. In `e2e540f` the ledger diff is only the `close` block. `ledger_rows_digest` is `372bbbf2ba43276b` with 61 rows at both `226b489` and HEAD. origin/main is `dcc91f6`. I cannot re-check "Claude never pushes" from git; it rests on the 34-02 and 34-06 SUMMARY records. |

**Score:** 3/3 roadmap SC.

### Plan must-haves (32 truths across 6 plans)

| Plan | Truths | Status | Key evidence |
|---|---|---|---|
| 34-01 | 4 | VERIFIED | Both plist tests use `HEARTBEAT_PATH.relative_to(_ROOT)` suffix comparison (test_phase31_probe.py:993, test_phase32_points.py:1047), committed alone in `abdb77d`. They pass in the scratch clone at `.../scratchpad/vclone`. RPT-05 tags are derived (`bb50737`). A missing tag goes RED (reproduced). The shallow-clone refusal is kept (test_package.py:64). `PYPROJECT_SHA256` and `pyproject.toml` are unchanged. |
| 34-02 | 4 | VERIFIED | `gh run view 36500648069`: success at `a948d7d3…`, log `3195 passed, 72 skipped`. The run is recorded in 34-02-SUMMARY:35 only; the ledger contains `36500648069` zero times. Push 1 was green, so the RED-diagnosis truth did not apply. Skips were 72, equal to the baseline. |
| 34-03 | 7 | VERIFIED | `results/phase34_ledger.json` has 61 rows: RE-DEFERRED 20, FIXED 19, ACCEPTED 15, NAMED-LIMITATION 7. `results/phase28_ledger.json` was last changed at `fd03998` (Phase 28). The five P28 rows by reference are TD-16-R1, TD-17-SUMMARY-FRONTMATTER, IN-07, P22-WARNING-4 and -5. P33-WR-01/02 are RE-DEFERRED with the dated-pin prerequisite, and the module-pin test is at test_phase34_ledger.py:205. The named-limitation rows are ACTRL-01, RELRN-06..09 and two P28 rows. No row contains "never exercised". The whole `test_phase34_ledger.py` suite passes, including the derived census, the FIXED-needs-collectable-test check and the by-reference digest check. |
| 34-04 | 8 | VERIFIED | `scripts/phase34_report.py` imports `phase28_report as p28` and uses its engine (`resolve`, `_fmt`, `_Template`, `_table`, `_cell`, `_markers`, `_span`, `_github_anchor`, `install`, `ledger_rows_digest`, `ledger_frozen_bytes`, `_named_limitations`, `_ledger_by_disposition`). It declares `class Bindings(p28.Bindings)` with `raise KeyError` on unknown prefixes (:370, :378). The CONTRACT docstring says "WRITTEN AFTER THE RESULTS. It is not a pre-registration". The tests import `_bare_numerals` from test_phase28_report. The rendered lead lists the per-leg lines (advr_n8 PASS 0 of 6 / INCONCLUSIVE 6 of 6; advr_n64 REFUSED 6 of 6, NOT MEASURED) before `MOOT` and its three quoted reasons. The condition_c_vs_v4 rows table, the by_leg table and the notes are quoted. A grep of the block for "mitigation held", "never exercised" and figure links is empty, and a word-grep for `held` in both templates is empty. |
| 34-05 | 6 | VERIFIED | Placement and sentinels are as in SC1. `226b489` amends exactly the three named Phase 28 guards, each with a "Dated continuation, 2026-09-29 (Phase 34 R-1)" comment. The diff hunks start after `test_glance_block_is_byte_identical`, so the phase28 byte-identity tests are untouched. `PUBLISHED = "2026-09-29"` equals the `226b489` commit date. The developer's approval is recorded in 34-05-SUMMARY:95–97; that is a human act and cannot be re-measured. The local full suite is covered below. |
| 34-06 | 5 | VERIFIED | The close commit and ledger are as in SC3. REQUIREMENTS.md :646–648 have RPT-04..06 ticked with SATISFIED rows at :686–688. ROADMAP:191 leaves the Phase 34 checkbox `[ ]` as intended. STATE.md position is updated. `git diff b622b3c HEAD -- .planning/MILESTONES.md .planning/PROJECT.md` is empty and there is no `v5.0` tag. Both `check` commands exit 0. The census guard `tests/test_phase25_correction.py` passes alongside `tests/test_phase28_ledger.py` (38 passed). |

### Required Artifacts

| Artifact | Status | Details |
|---|---|---|
| `tests/test_package.py` | VERIFIED | Derived-tag test is present, passing, and REDs on a missing tag |
| `tests/test_phase31_probe.py`, `tests/test_phase32_points.py` | VERIFIED | Suffix comparison; pass at a foreign root |
| `results/phase34_ledger.json` | VERIFIED | Closed domain, `close.ci_run` filled, rows digest invariant |
| `tests/test_phase34_ledger.py` | VERIFIED | Contains `test_every_review_finding_has_a_row`; suite green |
| `scripts/phase34_report.py` + 2 templates | VERIFIED | Wired: installed spans equal a fresh render (`check` exit 0) |
| `tests/test_phase34_report.py` | VERIFIED | Contract, numeral, byte-identity, placement and write-refusal tests all pass |
| `docs/REPORT.md`, `README.md` | VERIFIED | PHASE34 spans installed once, additively |
| `.planning/REQUIREMENTS.md` | VERIFIED | `- [x] **RPT-06**` present |

### Key Link Verification

| From | To | Status |
|---|---|---|
| `_required_tags` | MILESTONES.md Shipped headings | WIRED (regex at test_package.py:31) |
| push-1 record | GH run 36500648069 | WIRED (gh re-read) |
| ledger tests | 29..33 REVIEW/SECURITY/33-03-SUMMARY, plus the `v5.0-phases` fallback | WIRED (`_PHASE_ROOTS` at :40) |
| P28-* rows | phase28 ledger sha256 + `ledger_rows_digest` | WIRED (test passes) |
| `Bindings.__getitem__` | the three records | WIRED (`raise KeyError`) |
| byte-identity test | PHASE34 span | WIRED (`check` exit 0) |
| `close.ci_run.head_sha` | publishing commit `226b489` | WIRED (`merge-base --is-ancestor` exit 0) |

### Data-Flow Trace (Level 4)

| Artifact | Source | Real data | Status |
|---|---|---|---|
| PHASE34 REPORT/GLANCE spans | `results/phase32_frontier.json`, `results/phase33_admission.json`, `results/phase34_ledger.json` via `p28.resolve` | Yes. The rendered values (tallies, control recalls 777/1008, 0/1008, 1/648, the v4 rows) come from record fields; the numeral scan forbids typed numerals | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| v4.0 block frozen | `.venv/bin/python scripts/phase28_report.py check` | exit 0 | PASS |
| v5.0 block equals render | `.venv/bin/python scripts/phase34_report.py check` | exit 0 | PASS |
| Targeted suites | pytest test_package, test_phase34_report, test_phase34_ledger, test_phase28_report, both plist tests | 82 passed | PASS |
| Census + v4 ledger | pytest test_phase25_correction, test_phase28_ledger | 38 passed | PASS |
| Foreign-root clone | plist ×2 + RPT-05 in scratch clone | 3 passed; RED with v4.0 deleted | PASS |
| CI push 2 | `gh run view 36562323069` | success @ dcc91f6, 3243 passed / 72 skipped | PASS |

### Probe Execution

Not applicable. No PLAN declares a `probe-*.sh`, and this is not a migration phase.

### Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| RPT-04 | 34-03, 34-04, 34-05, 34-06 | SATISFIED | SC1 |
| RPT-05 | 34-01, 34-06 | SATISFIED | SC2 |
| RPT-06 | 34-01, 34-02, 34-03, 34-06 | SATISFIED | SC3 |

No requirement is orphaned. REQUIREMENTS.md maps only RPT-04..06 to Phase 34, and every plan ID is accounted for.

### Anti-Patterns Found

The debt-marker scan (TBD/FIXME/XXX/TODO/HACK) over the phase's files found nothing.

The code review `34-REVIEW.md` (`4d0ab76`, landed during this verification) reports 0 critical, 3 warnings and 5 info. They are advisory; none falsifies an SC or a must-have:

| Finding | Severity | Impact on the goal |
|---|---|---|
| WR-01: `write` is not atomic | Warning | Latent. The write already ran once and the blocks are frozen. |
| WR-02: glance binds only some tally categories; "unlearnable" prose is typed | Warning | Latent. The published values match the records today (`check` exit 0), so it only matters for a future renderer. |
| WR-03: the by_leg table shows `k5`/`k6` = `0` for the REFUSED advr_n64 leg and omits the v4 per-leg counts | Warning | These are the record's values, rendered as bound. It is a presentation concern, not a hand-typed number. The same row carries `v5_state refused_prereg03`, and the block says NOT MEASURED. Any correction would be a dated continuation (`scripts/_addendum.py`). This is the developer's call and does not block the goal. |
| IN-01..05 | Info | None |

In `226b489`, the third amended guard (`test_write_installs_pre_publish_then_refuses`) switched from `read_bytes()` to `read_text()` equality. I noted this; it has no effect on the goal.

### Human Verification Required

None. The developer's read of the rendered blocks before the freeze is already recorded (34-05-SUMMARY, approved 2026-09-29).

### Pending for the orchestrator

The local full suite (`.../scratchpad/34-06-suite.log`) was still running at about 36% with no `EXIT=` line when I finished, so its result is not part of this report. CI run 36562323069 covers every code byte at HEAD: since `dcc91f6` only the ledger `close` block and planning files have changed, and the ledger-dependent tests passed locally above.

### Gaps Summary

None. v5.0 is published additively between PHASE34 sentinels, rendered from three committed records under the shared numeral grammar. The v4.0 block still re-renders byte-identical. RPT-05's tag set is derived and REDs on a missing tag. The milestone's close run 36562323069 is green, contains the publishing commit, and is recorded in `close.ci_run` without moving the rows digest.

---

_Verified: 2026-09-29T12:34:39Z_
_Verifier: Claude (gsd-verifier)_
