---
phase: 37-clean-reproduction-of-the-phase-19-verdict
plan: 07
subsystem: reproduction
tags: [R1b, REPRO-03, publication, single-path-commits]
requires: [37-06]
provides: [results/phase37_r1b.json, results/phase37_r1b_arm.json, ledger R1b lines — all tracked]
requirements-completed: [REPRO-03]
# REPRO-01..03 ticked by the orchestrator by hand at phase close (no gsd-sdk handler).
completed: 2026-10-04
---

# Phase 37 Plan 07: R1b records published beside the v3.0 verdict

**On Rafael's "approved", the one attempt's records went in as three single-path commits (ledger, then arm, then record). The suite is green with every Phase 37 record tracked.**

Executed inline by the orchestrator.

## Approval (Task 1)

The orchestrator showed Rafael the record, read from results/phase37_r1b.json:
- verdict REPLICATED, with all four keys at abs_diff 0 and within tolerance;
- decision: k 78, set_equal, positions_moved 0;
- draws bit-identical, 0 of 10368 completions differing;
- non-target deltas equal to the committed ones in all 7 slots;
- replica_verdict FAILURE, with the Phase 19 reasons;
- provenance: head unmoved at 7831ea9.

Rafael wrote "approved".

## Commits (Task 2)

| Commit | Path (only) |
|---|---|
| 3f87acf | ledger/v6_mps_ledger.jsonl (R1b start + end lines) |
| 57dcd4b | results/phase37_r1b_arm.json |
| 8a289fc | results/phase37_r1b.json |

- `git show --name-only` names exactly one path per commit, and the ledger commit is the oldest.
- After the ledger commit, `tests/test_phase36_ledger.py tests/test_phase36_budget.py` gave 105 passed.
- The step 5 targeted set (phase36 ledger/budget, phase35/37 prereg, phase37 r1b/r1a) gave 289 passed.
- `phase36_ledger.py report`: R1b closed with 4104.256927 s, priced from the tracked record (flag null, so no longer PENDING).
- `git ls-files 'results/phase37_*'` lists phase37_r1a.json, phase37_r1b.json and phase37_r1b_arm.json.
- `git status --porcelain -- 'results/phase19_*' README.md` is empty: the replica is published beside the verdict, not over it.
- Full suite at 8a289fc: `3928 passed, 4 skipped, 83 warnings in 2574.46s (0:42:54)`, `EXIT=0`, zero new skips. No latent red surfaced, so no test fix was needed.

## Deviations

- Run inline by the orchestrator.
- The LaunchAgent com.personacore.phase37.r1b is still loaded with no PID, waiting for Rafael's `launchctl bootout`. It cannot start itself (RunAtLoad false, KeepAlive false).
