---
phase: 28-report-the-published-null-and-milestone-close
plan: 07
subsystem: docs
tags: [ci, ledger, milestone-close, requirements, phase-28]
requires:
  - "28-06 publishing commit 3b63b7d (frozen REPORT/README blocks, byte-identity guards)"
  - "28-03 ledger results/phase28_ledger.json (69 rows, close.ci_run null)"
provides:
  - "results/phase28_ledger.json::close.ci_run filled with the green run (id, url, head_sha, conclusion, recorded)"
  - "RPT-01 / RPT-03 ticked with SATISFIED traceability rows in .planning/REQUIREMENTS.md"
  - "ROADMAP Phase 28 plan list 7/7 ticked, progress row 7/7 Plans complete — verification pending"
  - "STATE.md position, decisions and session continuity at the Phase 28 close boundary"
  - "scripts/phase28_report.py::ledger_frozen_bytes — provenance bytes column excludes close as the digest does"
affects:
  - "/gsd-verify-work 28 (owns the ROADMAP phase checkbox)"
  - "/gsd-complete-milestone v4.0 (owns PROJECT.md, MILESTONES.md, the v4.0 tag)"
tech-stack:
  added: []
  patterns:
    - "close precondition measured, not assumed: the developer pushes, CI runs on origin/main, the run id lands in the record (D-38)"
    - "planning ledgers edited by hand: snapshot -> Edit -> diff -u; zero gsd-sdk mutation handlers (D-34)"
key-files:
  created:
    - .planning/phases/28-report-the-published-null-and-milestone-close/28-07-SUMMARY.md
  modified:
    - results/phase28_ledger.json
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - scripts/phase28_report.py
    - tests/test_phase28_report.py
decisions:
  - "D-38 measured: CI run 35770563251 at head d2dcbe2 (contains 3b63b7d) concluded success; both pushes and the tag push were the developer's, Claude never ran git push"
  - "The ledger's close block is outside the provenance BYTES column as it is outside the rows digest; the frozen view (close.ci_run = None, byte-stable re-dump) reproduces the published 49057, so the render stays byte-identical to 3b63b7d and no dated continuation was needed"
metrics:
  duration: "2 sessions (Task 1 human checkpoint across two pushes; Task 2 continuation)"
  completed: 2026-09-22
---

# Phase 28 Plan 07: Close — the green CI run into the ledger, RPT ticks and planning files by hand Summary

Phase 28 closes at its named boundary: the developer pushed `main` twice, the second run
(35770563251) on `origin/main` concluded `success` with the publishing commit in its head, the run
landed in `results/phase28_ledger.json::close.ci_run` with `rows` byte-unchanged, and RPT-01 /
RPT-03, the ROADMAP plan list and row, and STATE.md were edited by hand with zero `gsd-sdk`
mutation handlers. Milestone archival, `MILESTONES.md`, `PROJECT.md` and the `v4.0` tag are left to
`/gsd-complete-milestone` (D-34); the ROADMAP `- [ ] **Phase 28` checkbox is left to
`/gsd-verify-work 28`.

## Tasks

| Task | Name | Commit | Notes |
|------|------|--------|-------|
| 1 | The developer pushes main and waits for a green CI run on origin/main (checkpoint:human-action, D-38) | d2dcbe2 (the fix commit between the two pushes) | resolved by the developer; two runs, see below |
| 2 | Run id into the ledger's close block; RPT ticks, ROADMAP row and STATE.md by hand; gates | 89aae4f (renderer fix, deviation) + fd03998 (close) | Task 2 verify block exit 0 |

## Task 1 — the two runs (measured by the orchestrator, 2026-09-22)

**Push 1** — `origin/main` → 6896c31. Actions run **35719377808** concluded `failure` (4 tests).
Three causes were measured against the run and fixed at **d2dcbe2** (`test(28-07): three CI causes
measured against run 35719377808 — tags unpushed, a Phase-28 ROADMAP row, a Phase-27 host-gated
skip`):

1. Tags `v2.0` / `v3.0` had never been pushed — `git ls-remote --tags origin` showed only
   `m1-demo-v1`, `v1.0`; `ci.yml` already had `fetch-depth: 0`. The developer pushed the two tags
   (no file change).
2. `tests/test_phase25_correction.py`: `_PRE_EXISTING_TOTAL` 2 → 3 with the third site — the
   ROADMAP Phase 28 progress row naming the refused correction helper as the D-20 route for the
   frozen REPORT block — pinned by content (lines 431-447), not edited away.
3. `tests/test_phase25_venue.py`: new named leg `_RELEARN_HOST_ONLY_SKIPS = 1`
   (`tests/test_phase27_prereg.py::test_pinned_adapters_hash_on_host`, `@needs_adapters`,
   gitignored `checkpoints/`) on both ubuntu sums → 72 / 72 (lines 306-343, dated continuation).
   Two hypotheses were refuted and recorded in that continuation: `measure_gate05`'s MPS-absent
   guard as the new leg (already inside the ubuntu 52), and the three Phase-27 files running
   skip-free on the M3 (true and irrelevant — the skip is host-gated, not device-gated).

Local `PERSONACORE_SWEEP_ACTIVE=1` suite before the fix commit: 2876 passed / 39 skipped (only the
two `tests/` clean-tree probes red on the uncommitted files; 25 passed after commit). A no-MPS
pytest plugin run named the skips on the ubuntu-like venue.

**Push 2** — `origin/main` == d2dcbe2bb8ec1dac5db4543e877681db3fd577c5. Actions run
**35770563251**: conclusion `success`, status `completed`, headSha
`d2dcbe2bb8ec1dac5db4543e877681db3fd577c5`,
url https://github.com/RAFAELDCOELHO/PersonaCore/actions/runs/35770563251,
createdAt 2026-09-22T18:56:56Z, updatedAt 2026-09-22T19:20:50Z; test job
`2845 passed, 72 skipped, 9 warnings in 1379.21s (0:22:59)`.
`git merge-base --is-ancestor 3b63b7d d2dcbe2` exits 0 — the publishing commit is in the run head
(T-28-18).

**Claude never ran `git push`**; both pushes and the tag push were the developer's (D-38, T-28-08).

**Task 1 `<automated>` verify block** (re-run at continuation start): exit **0**
(`origin/main..main` = 0; newest run on `main` `success`; its headSha == `git rev-parse origin/main`).

## Task 2 — evidence

### 1. Ledger close (commit fd03998)

`.venv/bin/python -c` load → set `close.ci_run` → assert `json.dumps(rows, sort_keys=True)`
unchanged before/after → re-dump `indent=2, sort_keys=True, ensure_ascii=False` + newline → reload
and re-assert. `rows unchanged, len 69`. `git diff 3b63b7d HEAD -- results/phase28_ledger.json`:
1 file, +7 / −1, only the `close` block:

```diff
   "close": {
-    "ci_run": null
+    "ci_run": {
+      "conclusion": "success",
+      "head_sha": "d2dcbe2bb8ec1dac5db4543e877681db3fd577c5",
+      "id": "35770563251",
+      "recorded": "2026-09-22",
+      "url": "https://github.com/RAFAELDCOELHO/PersonaCore/actions/runs/35770563251"
+    }
   },
```

The rows digest is unchanged (`bb9f82fe290d7578a11e221c349733555e5c2f3d197673e56e39d8c65b00dbd7`
before and after). The byte-identity test went RED anyway — see the deviation below — and is GREEN
on the committed tree: `tests/test_phase28_ledger.py tests/test_phase28_report.py` 39 passed.

### 2. REQUIREMENTS.md — `diff -u` 2 hunks, +4 / −2

- `- [ ] **RPT-01**` → `- [x] **RPT-01**`; `- [ ] **RPT-03**` → `- [x] **RPT-03**`. The
  requirement TEXT lines are byte-identical to the snapshot (only the checkbox character changed
  on the first line of each; the continuation lines are outside every hunk).
- Traceability rows `| RPT-01 | Phase 28 | |` and `| RPT-03 | Phase 28 | |` filled:
  - **RPT-01** — `**SATISFIED (plans 28-04, 28-05, 28-06).**` the v4.0 section between the
    `PHASE28-REPORT` sentinels at publishing commit 3b63b7d (frozen, D-20; correction route a dated
    continuation via `scripts/_addendum.py`), rendered from `phase25_frontier.json`
    (`verdicts.capacity_branch` null-at-both-capacities, `verdicts.arm_existentials` verbatim),
    `phase27_admission.json`, `phase26_canary.json`, the three phase23 records; every numeral a
    binding; `derived.sigma_for_eps4` proves `epsilon_for` before printing 15.289937507119; the
    standing expectation quoted from `.planning/research/SUMMARY.md` at c673b4c and
    `tests/test_phase28_prereg.py` proves c673b4c precedes every `results/phase2[0-8]_*` first-add;
    guards named by node id; README glance bullets by the same mechanism (D-11); developer read and
    approved 2026-09-21.
  - **RPT-03** — `**SATISFIED (plans 28-01, 28-03).**` `[project].dependencies` equal at
    v1.0/v2.0/v3.0/HEAD by `tests/test_package.py::test_runtime_dependencies_identical_across_four_milestones`
    (tomllib; d45eaec); the sha256 pin as a change detector under its true name (dd087f7); SC3's
    sha256 clause recorded false as written (5065bc5, `license = "MIT"`, row `SC3-SHA256-CLAUSE`);
    the ledger (rows 841e7df; close at fd03998) — v3.0 tech-debt / stale-stamp counts by `len()`
    **measured: 16 / 6** (28-03 SUMMARY, equal to the audit's `tech_debt:` block and STATE's
    six-item table); 69 rows; closed domain guarded by `tests/test_phase28_ledger.py`; CI run
    35770563251 green on `origin/main` at d2dcbe2… containing 3b63b7d (D-38, the developer pushed).

One rewording during the edit: the RPT-01 row first spelled the refused helper's function name;
`tests/test_phase25_correction.py::test_no_continuation_was_written_by_append_addendum` counts
that name across ROADMAP/REQUIREMENTS/25-CONTEXT (pinned total 3) and went RED on the new
occurrence. The row now says "a dated continuation via `scripts/_addendum.py`" (the planner's own
row template never spelled the name); REQUIREMENTS still has zero occurrences, ROADMAP its pinned
two, and the guard is 23 passed.

### 3. ROADMAP.md — `diff -u` 2 hunks, +2 / −1

- `- [ ] 28-07-PLAN.md` → `- [x]` (seven `- [x] 28-0N-PLAN.md` lines now).
- Progress row `| 6/7 | In Progress | 2026-09-21 — …` → `| 7/7 | Plans complete — verification
  pending | 2026-09-22 — v4.0 published as measured: null-at-both-capacities (docs/REPORT.md,
  publishing commit 3b63b7d), README glance bullets rendered, ledger … (69 rows; v3.0 tech-debt 16 /
  stale-stamp 6 by len()), CI run 35770563251 green on origin/main at head d2dcbe2 (… the first run
  35719377808 at 6896c31 failed on 4 tests, three causes measured and fixed at d2dcbe2 …; Claude never
  ran git push, D-38); close.ci_run recorded, rows byte-unchanged; the frozen block's ledger
  provenance row sized the whole file, so filling close moved 49057 → 49297 — fixed in the renderer
  at 89aae4f …; RPT-01/RPT-03 ticked by hand; zero gsd-sdk mutation handlers. Earlier: wave 5 of 6
  complete: …` — every earlier clause of the "Earlier:" chain kept verbatim.
- The `- [ ] **Phase 28: …` heading checkbox at :158 is UNTICKED (verify-work owns it).

### 4. STATE.md — `diff -u` 5 hunks, +17 / −10

- Frontmatter: `stopped_at` → "Phase 28 COMPLETE (2026-09-22) — …" with the previous PLANNED
  record kept as "Superseded stop record (28 planned): …"; `last_updated`
  "2026-09-22T20:30:00.000Z"; `last_activity` 2026-09-22; `progress.completed_plans` 114 → 115
  (`completed_phases` 7 and `percent` 78 untouched — the phase-complete step is the orchestrator's).
- `**Current focus:**` prefixed with "PLANS COMPLETE 7/7 (2026-09-22; …). Earlier: EXECUTING …".
- `## Current Position`: Phase line → "PLANS COMPLETE 7/7 2026-09-22 … awaiting /gsd-verify-work
  28"; Plan line → "7 of 7 executed. Wave 6 COMPLETE 2026-09-22 — 28-07: …" prefixed on the
  existing wave chain.
- `Last activity:` prefixed with the 2026-09-22 entry, "Earlier:" chain kept.
- `### Decisions`: seven `[Phase 28]` lines appended after the last `[Phase 27]` line —
  frozen-at-publish (D-20); rows digest excludes `close` + the bytes-column fix; D-27 as a
  one-liner; the 24-UAT stamp ruling; D-38 run id measured; the three CI causes and the two refuted
  hypotheses; planning ledgers by hand (D-34).
- `## Session Continuity`: `Last session` / `Stopped at` updated, the 28-context record kept as
  "Superseded stop record (28 context): …".
- `head -25` frontmatter parses (`---` fences intact).

### 5. Gates

- Task 2 `<automated>` verify block: exit **0** (ledger shape; RPT ticks and SATISFIED rows; phase
  checkbox untouched; `7/7` row; seven plan ticks; `check` exit 0; 39 passed `-x`; PROJECT.md /
  MILESTONES.md clean).
- `make lint`: `All checks passed!` / `288 files already formatted`.
- `.venv/bin/python scripts/phase28_report.py check`: exit 0 on the committed tree.
- `git tag -l v4.0`: empty. `git status --short .planning/PROJECT.md .planning/MILESTONES.md`: empty.
- The full suite is NOT run here — the orchestrator runs it detached after this return (the local
  suite is ~23 min; CI's 2845 / 72 at d2dcbe2 is the measured full run).
- Zero `gsd-sdk` mutation handlers were called (all anchors located by `grep -n`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The frozen block's ledger provenance row sized the whole file, so filling `close` tripped byte-identity while the rows digest stood**
- **Found during:** Task 2 step 1 — `tests/test_phase28_report.py::test_report_block_is_byte_identical`
  RED after the close write: the Provenance table row
  `results/phase28_ledger.json (`rows` only) | bb9f82fe… | 49057 |` re-rendered as `| 49297 |`.
  The digest (rows only, by design — `ledger_rows_digest` docstring: "`close` stays outside so
  28-07 can fill `ci_run`") was unchanged; the plan's remedy ("the rows changed — revert and
  redo") did not apply because the rows had not changed. Editing the published block is forbidden
  (D-20), and a re-render would also have moved the number.
- **Fix:** `scripts/phase28_report.py::ledger_frozen_bytes(ledger)` — re-dump the ledger with
  `close.ci_run = None` (`indent=2, sort_keys=True, ensure_ascii=False` + newline, the byte-stable
  form 28-03 verified) and take its UTF-8 length; the provenance row uses it in place of the raw
  file size. Measured before editing: the frozen view is exactly **49057** bytes ==
  `git show 3b63b7d:results/phase28_ledger.json | wc -c`, so the render is byte-identical to the
  published block and no dated continuation was needed. `tests/test_phase28_report.py::
  test_provenance_digests_recompute_from_bytes` now pins the ledger row's bytes to the frozen view
  (other rows still to `stat().st_size`); new regression test
  `test_ledger_size_column_is_invariant_under_close` (frozen bytes and rows digest equal with
  `ci_run` filled, nulled and as-is). Natural RED recorded above; GREEN: 44 passed across the three
  Phase 28 test files.
- **Files modified:** scripts/phase28_report.py, tests/test_phase28_report.py
- **Commit:** 89aae4f

**2. [Rule 1 - Bug] The new RPT-01 row spelled the refused correction helper's name**
- **Found during:** Task 2 step 2 — `tests/test_phase25_correction.py::test_no_continuation_was_written_by_append_addendum`
  RED (total 5 against the pinned 3 after the RPT-01 row and the ROADMAP note).
- **Fix:** reworded the two new sentences to `scripts/_addendum.py` / "the refused correction
  helper's name"; the pinned pre-existing sites untouched. 23 passed.
- **Files modified:** .planning/REQUIREMENTS.md, .planning/ROADMAP.md (before the close commit)
- **Commit:** fd03998

## Hand-over (D-34)

Milestone archival, `MILESTONES.md`, `PROJECT.md` and the `v4.0` tag are left to
`/gsd-complete-milestone`; the ROADMAP Phase 28 heading checkbox, the frontmatter
`completed_phases` / `percent`, and the progress row's Status cell beyond "Plans complete —
verification pending" are left to `/gsd-verify-work 28` and the orchestrator's phase-complete step.

## Known Stubs

None.

## Threat Flags

None — no new surface; `close.ci_run` is the field the ledger schema reserved for this plan.

## Self-Check: PASSED

- FOUND: results/phase28_ledger.json (`close.ci_run.id` 35770563251)
- FOUND: .planning/REQUIREMENTS.md (`- [x] **RPT-01**`, `- [x] **RPT-03**`, two SATISFIED rows)
- FOUND: .planning/ROADMAP.md (7 × `- [x] 28-0N-PLAN.md`, row `7/7`, `- [ ] **Phase 28` untouched)
- FOUND: .planning/STATE.md (stopped_at names 3b63b7d and 35770563251)
- FOUND commits: d2dcbe2, 89aae4f, fd03998
- NOT CREATED (by design): tag v4.0; NOT MODIFIED: .planning/PROJECT.md, .planning/MILESTONES.md
- NOT RUN (by design): `git push` — never, by Claude
