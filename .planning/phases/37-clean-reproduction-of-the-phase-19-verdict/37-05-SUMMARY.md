---
phase: 37-clean-reproduction-of-the-phase-19-verdict
plan: 05
subsystem: reproduction
tags: [R1a, REPRO-01, write-once-record, prereg-freeze]
requires: [37-03, 37-04]
provides: [results/phase37_r1a.json]
affects: [scripts/phase37_prereg.py (frozen from this commit)]
key-files:
  created: [results/phase37_r1a.json]
requirements-completed: [REPRO-01]
# REPRO-01 is ticked in REQUIREMENTS.md by the orchestrator at phase close (hand edit, no gsd-sdk handler).
duration: ~100 min (two 45-min suites)
completed: 2026-10-03
---

# Phase 37 Plan 05: R1a record published

**One CPU command re-derived the Phase 19 FAILURE verdict exactly; the write-once record was committed alone after Rafael's "approved", freezing the Phase 37 pre-registration.**

Executed inline by the orchestrator (small mechanical plan with a human gate).

## Before the record (Task 1)

- The code review ran before this plan, while the prereg could still change (37-REVIEW.md). It found 0 blockers and 5 warnings, all fixed per Rafael's ruling in 2781bd6, 6dbad06, 9069c5c, 9abab12 and 5896ae3. The review was committed in eeeb804 and the fixes marked in 7e6432c.
- Tree: `git status --porcelain -- scripts src results tests ledger artifacts` was empty. No `results/phase37_*` file existed on disk or in git.
- HEAD at the pre-record gate: `7e6432c7f318c8c63beb565a98223c80ddf3d78e`.
- Pre-record full suite: `3928 passed, 4 skipped, 83 warnings in 2704.08s (0:45:04)`, `EXIT=0`. The 4 skips equal the last green run's (Phase 36: 3782 passed, 4 skipped).
- Command: `.venv/bin/python scripts/phase37_r1a.py`, exit 0, printed `R1a REPRODUCED (record written)`. Afterwards porcelain listed only `?? results/phase37_r1a.json`.

## The record, read from results/phase37_r1a.json

| Field | Value |
|---|---|
| assertions.k | 78 |
| assertions.target_correct | [0, 27] |
| assertions.nontargets_beyond_margin | [7, 7] |
| assertions.destroyed_pct | 77.6370113463966 |
| margin | 0.2962962962962963 |
| b_floor (D-13) | 0.14814814814814814 |
| verdict | FAILURE |

Reasons (equal, in order, to the `## Verdict` lines of results/phase19_erasure_report.md, enforced since WR-04):
- (a) target upper bound 0.0911 over 27 questions <= calibrated floor 0.0911
- (b) worst non-target degradation 1.000000 > k=2 x 0.148148 = 0.296296
- (c) dialogue PPL 4.8511 vs cap 4.5837; retention PPL 3.670918 vs cap 4.029000

input_sha256 (first 16 hex):
- results/phase18_arm_adapter-on.json 71fb062779b6b4c2
- results/phase19_arm_erased.json c10313a75a233cdd
- results/phase19_arm_replicate.json 77474413fa65c1ca
- results/phase19_calibration_correction.json 833631cfc578909f
- results/phase19_dialogue_floor.json 57d648d26bfaa0e3
- results/phase19_erasure_report.md 214667b6036e650b
- results/phase19_noise_floors.json ad2c96dd9e89e433

provenance.run.git_sha = head_at_write = `7e6432c7f318c8c63beb565a98223c80ddf3d78e` (the gate HEAD).
File sha256: `bcae9145dbca029b8c4b5591101c29da63424dfd01d100f768bbe17511941f02`.

## Approval (Task 2)

Rafael re-ran the command himself, which hit verify mode and printed `R1a REPRODUCED (record verified)` with the same values, then wrote "approved".

## Commit and after (Task 3)

- `fe715c5` results(37): R1a record. `git show --name-only` lists only `results/phase37_r1a.json`.
- Verify mode afterwards printed `R1a REPRODUCED (record verified)` and the file's sha256 was unchanged (`bcae9145…1f02`).
- Post-commit full suite at fe715c5: `3928 passed, 4 skipped, 83 warnings in 2714.48s (0:45:14)`, `EXIT=0`, zero new skips. No latent red surfaced, so no test fix was needed. The targeted set in step 5 is contained in that run.
- `scripts/phase37_prereg.py` is frozen from fe715c5 on. Any correction is a dated continuation via scripts/_addendum.py.

## Deviations

- Run inline by the orchestrator instead of an executor, following the repo practice for small checkpoint plans.
- During the post-commit suite, the orchestrator amended 37-06-PLAN.md (e634ee2) for the WR-01/WR-02 driver changes: the crash case "sweep file exists, sidecar absent" means reconcile and keep the file as evidence, and the plan now checks `head_moved_during_run`. That edit does not affect this plan's suite evidence, since no test reads 37-06-PLAN.md (the only Phase 37 planning file a test reads is 37-CONTEXT.md).
