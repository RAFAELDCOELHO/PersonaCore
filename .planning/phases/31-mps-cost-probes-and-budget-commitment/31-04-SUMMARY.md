---
phase: 31-mps-cost-probes-and-budget-commitment
plan: 04
subsystem: measurement
tags: [mps, probe, launchagent, arcal]
requires: [31-01, 31-02, 31-03]
provides: [data/probe31_point_run.json, data/probe31_relearn_run.json]
requirements-completed: []  # contributes to ARCAL-01/02; the orchestrator decides ticks at phase close
key-files:
  created: []
  modified: []
duration: 14h08m run (2026-09-26 21:23 UTC -> 2026-09-27 11:31 UTC)
completed: 2026-09-27
---

# Phase 31 Plan 04: Long MPS measurement — Summary

The D-12 LaunchAgent ran point-then-relearn on MPS once, exited 0 with an empty stderr, and was booted out by the developer. No code or tracked file changed.

## Task 1 — pre-launch gates (orchestrator, tree at 0d5be51)

| Gate | Result |
|------|--------|
| (1) `git status --porcelain scripts src results tests artifacts` | 0 lines |
| (2) full suite at 0d5be51 | EXIT=0 — 3127 passed / 4 skipped / 0 failed in 1877 s |
| (3) `test_phase31_probe.py -k "live_path or main_run"` / `test_phase31_budget.py -k producer` | 7 passed / 1 passed |
| (4) `find data checkpoints results logs -name '*probe31*'` | empty |
| (5) `torch.backends.mps.is_available()` | True |
| (6) free disk vs `DISK_PRECHECK_BYTES` | 509,523,566,592 ≥ 5,000,000,000 |
| (7) `plutil -lint` plist | OK |
| (8) `launchctl print …phase31.probe` | exit 113 (not loaded) |

The run launched from HEAD 61465c1 (a STATE.md-only commit on top of 0d5be51); both sidecars record `run_git_sha` 61465c1.

## Task 2 — developer action

The developer reported: state not running, last exit code 0, stderr empty, agent booted out without error.

## Task 3 — post-run verification (raw values)

- The last heartbeat line is `{"point": "probe31", "stage": "done", "utc": "2026-09-27T11:31:01.669742+00:00"}`.
- `logs/phase31_probe.out` ends with `[phase31_probe] relearn probe complete — wrote data/probe31_relearn_run.json`.
- `grep -c Traceback logs/phase31_probe.err` prints 0.
- `git status --porcelain scripts src results` prints 0 lines, and `launchctl print` exits 113, so the agent is booted out.
- Replay: `replay.per_step` has 200 entries with value set {256}, and `recipe.replay_windows` is 256 (D-11 held).
- Relearn `start_sha256` equals the point `training.adapter_sha256` (`04929111…0954244`), and the on-disk adapter hashes to the same value.
- Every `relearn_moves()` source is absent and every destination exists (4/4).
- `tests/test_phase27_relearn.py` on the post-run tree, before any emit: 37 passed.
- The relearn sidecar has `complete: true` and 8 rungs, ladder 50..400, k 16, relearn_cap 400.

### Raw per-stage seconds

| Probe | Stage | Seconds | Source field |
|-------|-------|---------|--------------|
| point | train | 633.5 | `outer_seconds.train` (`training.seconds` 633.46) |
| point | measure | 1168.7 | `outer_seconds.measure` (`measured.measure_seconds` 89.3 + `scoring_seconds` 1079.4) |
| point | draw | 5621.8 | `outer_seconds.draw` |
| point | score | 0.1 | `outer_seconds.score` |
| point | **total** | 7424.1 (2.06 h) | sum of `outer_seconds` |
| relearn | train | 210.4 | `train.seconds` |
| relearn | rung 50 / 100 / 150 / 200 | 5572.5 / 5468.6 / 5439.1 / 5131.3 | `rungs[i].seconds` |
| relearn | rung 250 / 300 / 350 / 400 | 5047.0 / 5356.0 / 5439.6 / 5790.9 | `rungs[i].seconds` |
| relearn | **arm** | 43455.5 (12.07 h) | train + Σ rung seconds |

The point's `shape_minutes` are A1-mild 20.16, A1-aggressive 27.14, A2 17.54 and A3 28.83.

## Deviations

- The point sidecar carries no `complete` key; the relearn sidecar does. Point completion is evidenced by `finished_utc`, the `done` heartbeat and the relearn half starting from its adapter, which only runs after the point half.
- Task 1 gates were run by the orchestrator, not an executor agent.

## Next

31-05: `phase31_probe.py emit point` → commit alone → `emit relearn` → commit alone, running the flipped guards after each.
