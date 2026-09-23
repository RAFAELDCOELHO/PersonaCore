---
phase: 26-empirical-privacy-audit-canary
plan: 04
subsystem: privacy-audit
tags: [canary, launchagent, mps, sidecar, reproduction-gate, d-44, pytest]

# Dependency graph
requires:
  - phase: 26-03
    provides: CPU-only canary structure, refusal, and live-wiring tests
  - phase: 26-02
    provides: canary scoring driver and LaunchAgent plist
provides:
  - Pre-launch and post-kickstart operational record for the Phase-26 canary
  - Approved early-run gate with real OFF/control sidecars and consumer refusal
  - Sweep-active control-read coverage and the dated D-44 skip-register continuation
affects: [26-05, empirical-privacy-audit]

# Tech tracking
tech-stack:
  added: []
  patterns: [quoted checkpoint evidence, real-record refusal before trust, sidecar-only control read]

key-files:
  created:
    - .planning/phases/26-empirical-privacy-audit-canary/26-04-SUMMARY.md
  modified:
    - results/phase26_operational_note.md
    - tests/test_phase26_canary.py
    - tests/test_phase25_venue.py

key-decisions:
  - "The control reproduction test runs under PERSONACORE_SWEEP_ACTIVE=1 because it reads a completed sidecar and never touches MPS."
  - "The note records the sidecars' actual write-time instrument SHA, a7843b3, because provenance is computed when each sidecar is written rather than at kickstart."
  - "The approved canary remains unattended; plan 26-05 owns the close and final artifact decision."

patterns-established:
  - "Record the early gate from producer sidecars, the consumer refusal, heartbeat, assertion owner, and the read-only control test."
  - "Maintain D-44 skip counts by named leg, including the dated control-sidecar continuation."

requirements-completed: [CANARY-01, CANARY-02]

# Metrics
duration: not measured
completed: 2026-09-11
---

# Phase 26: Empirical Privacy Audit Canary Summary

**The approved 16-point MPS canary passed its 790/1008 control gate, refused partial emission on real records, and left a zero-skip sidecar control read plus D-44 register continuation.**

## Performance

- **Duration:** not measured
- **Started:** not recorded
- **Completed:** 2026-09-11
- **Tasks:** 3
- **Files modified:** 4, including this SUMMARY

## Accomplishments

- **Task 1 (pre-session):** 4c01c43 added the first tracked Phase-26 result with the note's §1–§4 and heading test; a7843b3 added the post-kickstart §5 launch record. The agent was installed and kickstarted under caffeinate -dims.
- **Task 2:** At the checkpoint timestamp 2026-09-11T18:34:58Z, the operator replied "approved" and left the approximately 25-hour run unattended.
- **Task 3 (this session):** §6 was filled from six quoted checkpoint outputs: OFF/control sidecar hashes and timings, the "reproduction_gate" JSON, the real-record emit() refusal naming all 15 missing noised keys, heartbeat progress, assertion ownership, and the passing control-read test. §7 now names only the close.
- The control-read sweep_is_active() skip was removed because the test reads a sidecar only; the D-44 continuation set _CANARY_CONTROL_NOT_YET_SCORED_SKIPS to 0 and records M3 sweep-active 39, M3 flag-unset 4, and ubuntu 70/70.

## Task Commits

Each task was committed atomically or recorded at its human checkpoint:

1. **Task 1: Pre-launch record and launch** - 4c01c43 (COMMIT A, note §1–§4 plus heading test), a7843b3 (COMMIT B, §5 after kickstart)
2. **Task 2: Early-run gate approval** - operator checkpoint "approved" at 2026-09-11T18:34:58Z (no commit)
3. **Task 3: Early-run record and test/register continuation** - b6527ef (test and D-44 changes), 3a21995 (note §6 and §7)

The SUMMARY itself is commit (iii), using the prescribed docs(26-04): complete the launch plan — SUMMARY message.

## Files Created/Modified

- results/phase26_operational_note.md - §6 records the approved early-run gate from quoted real-path outputs; §7 contains only the plan-26-05 close.
- tests/test_phase26_canary.py - removes the sweep-active skip from the sidecar-only control read and removes the stale artifact assertion described below.
- tests/test_phase25_venue.py - adds the dated D-44 continuation and records zero not-yet-scored control skips with M3 39/4 and ubuntu 70/70 counts.
- .planning/phases/26-empirical-privacy-audit-canary/26-04-SUMMARY.md - this execution summary.

## Decisions Made

- Treat the real OFF and control sidecars as the trust boundary: emit() was exercised against them and refused before any partial artifact could be assembled.
- Preserve the approved run and its write-time provenance. Both early sidecars carry instrument_git_sha = a7843b3; the note corrects the earlier assumption that they would carry COMMIT A because _provenance() runs at sidecar-write time.
- Keep the control-read test active under the sweep flag because it performs no model load, draw, or MPS work.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed a stale operational-note assertion**
- **Found during:** Task 3, after Task 1 had created the operational note.
- **Issue:** test_emit_refuses_to_overwrite_the_committed_artifact had an else-branch assertion, assert not canary.OPERATIONAL_NOTE.exists() or "## 7." not in (...), that was written in plan 26-03 before the note existed. It passed vacuously then, but became permanently false once Task 1 intentionally created the note with ## 7. Pending.
- **Fix:** Removed the stale assertion; the branch is now a no-op while the final artifact does not exist. The real write-once refusal invariant remains covered by the if branch and the dedicated tests in the same file. This was in scope under the plan's license to update §6/§7 content assertions.
- **Files modified:** tests/test_phase26_canary.py
- **Verification:** Ruff passed, the sweep-active canary/prereg run passed 42 passed in 3.73s, and the mandatory venue result below passed.
- **Committed in:** b6527ef

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug)
**Impact on plan:** The fix restores the intended write-once test boundary; no production scope or live-run behavior changed.

## Issues Encountered

- The mandatory full-file tests/test_phase25_venue.py run, which spawns the whole repository suite twice, could not complete inside this sandbox: two in-process attempts were killed by real host memory pressure while the live MPS canary (pid 70302, approximately 9–11 GB resident) was running. The orchestrating process ran it directly outside the sandbox, without interfering with the canary, and recorded the clean result: 16 passed in 884.88s (0:14:44). The canary PID remained live and its heartbeat advanced throughout. This is an environmental/infrastructure note, not a code defect; the 14-minute suite was not rerun in this session.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The operator-approved approximately 25-hour MPS run continues unattended toward plan 26-05, the close. Plan 26-05 owns the final sidecars, emit(), machine restoration, and close decision; those are not this plan's job.

---
*Phase: 26-empirical-privacy-audit-canary*
*Completed: 2026-09-11*
