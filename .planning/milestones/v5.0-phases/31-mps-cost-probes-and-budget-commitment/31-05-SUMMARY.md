---
phase: 31-mps-cost-probes-and-budget-commitment
plan: 05
subsystem: results / probe records
tags: [arcal-01, arcal-02, write-once, ancestry, mps]
requires: ["31-04"]
provides: ["results/phase31_probe_point.json", "results/phase31_probe_relearn.json"]
affects: ["31-06 budget emit (reads both via _tracked_json at HEAD)"]
tech-stack:
  added: []
  patterns: ["write-once emit from a clean tree, one record per commit, flipped guards after each"]
key-files:
  created:
    - results/phase31_probe_point.json
    - results/phase31_probe_relearn.json
  modified: []
decisions:
  - "Point record committed alone (966f91b) before the relearn emit; relearn committed alone on top (28338cd)"
requirements-completed: []
# The orchestrator decides the ARCAL-01/ARCAL-02 ticks at phase close.
metrics:
  duration: ~10 min
  completed: 2026-09-27
---

# Phase 31 Plan 05: Emit and Commit the Probe Records Summary

The ARCAL-01 point probe record and the ARCAL-02 relearning probe record, both from the 31-04 MPS run, were emitted write-once from a clean tree and committed separately in ancestry order. Every flipped v5.0 guard stayed green after each commit.

## Pre-emit checks

- `git status --porcelain scripts src results` was empty before each emit.
- `run_git_sha` = `61465c1f4285a34e878005da988b9f954c2f5e14` in both `data/probe31_point_run.json` and `data/probe31_relearn_run.json`. `git diff --quiet 61465c1 HEAD -- scripts src` exited 0 for both.

## ARCAL-01: results/phase31_probe_point.json (commit 966f91b, touches only this file)

| Field path | Value |
|---|---|
| stages.train.seconds / outer_seconds | 633.46 / 633.55 (resumed_from_step 0) |
| stages.measure.seconds / outer_seconds | 89.29 / 1168.74 |
| stages.recall.seconds | 1079.44 |
| stages.draw.seconds / outer_seconds | 5620.57 / 5621.82 (draws_per_question 16) |
| stages.score.seconds | 0.099 |
| total_seconds | 7422.87 (2.06 h) |
| replay.steps / expected_per_step / set(per_step) | 200 / 256 / {256} |
| sweep_point | false (sweep_point_false_reason present: "This is the Phase 31 COST PROBE (ARCAL-01), not a sweep point...") |
| readings.gates_nothing | true |
| phase25_twin (v4_key adv_n64_ratio0p000000) | train 80.30, measure 87.77, recall 997.98, draw 3851.56 s |
| phase25_per_point_minutes (n 12) | min 49.34 / median 64.12 / max 70.82; with_recall min 64.24 / median 81.23 / max 88.16 |
| calibration.add_commit / is_ancestor_of_head | 4339f2b2 / true |
| adapter.sha256 | 04929111567abe60067f67ab1d2448a0374cf5de793d58167a61acf500954244 |
| provenance.run.device / git_sha / torch_version | mps / 61465c1 / 2.7.1 |

These values match the 31-04 raw values: train outer 633.5, measure outer 1168.7, draw outer 5621.8 and score 0.1.

## ARCAL-02: results/phase31_probe_relearn.json (commit 28338cd, touches only this file; its parent is 966f91b)

| Field path | Value |
|---|---|
| stages.train.seconds | 210.41 |
| rungs | [50, 100, 150, 200, 250, 300, 350, 400]. This is 8 rungs, equal to len(phase29_prereg.RUNGS). |
| k / relearn_cap | 16 / 400 |
| arm_seconds | 43455.49 (12.07 h), equal to train + the sum of stages.rungs[].seconds (43245.1) |
| start_sha256 | 04929111…0954244, equal to the point record's adapter.sha256 (True) |
| sweep_point | false |
| provenance.run.device / git_sha | mps / 61465c1 |

stages.rungs[] (steps: seconds / draw_seconds / remainder_seconds):
50: 5572.5 / 4647.7 / 924.9 · 100: 5468.6 / 4553.0 / 915.7 · 150: 5439.1 / 4540.1 / 899.0 · 200: 5131.3 / 4235.4 / 895.9 · 250: 5047.0 / 4151.2 / 895.9 · 300: 5356.0 / 4436.5 / 919.4 · 350: 5439.6 / 4515.7 / 923.8 · 400: 5790.9 / 4714.9 / 1076.0

## Verification

- After each commit I ran `.venv/bin/pytest tests/test_phase27_relearn.py tests/test_phase29_prereg.py tests/test_phase30_calibration.py tests/test_phase30_points.py tests/test_phase31_probe.py tests/test_phase31_budget.py -q -p no:cacheprovider`. The result was **209 passed** after the point commit and **209 passed** after the relearn commit. This set includes test_no_probe_or_calibration_path_parses_as_a_point_key, which covers SC4.
- `git ls-files 'results/phase32_*'` printed nothing (SC4).
- The budget emit was not run; 31-06 owns it.

## Deviations from Plan

None. The plan was executed exactly as written: no --force, no code, test or data edits, and no gsd-sdk handlers.

## Self-Check: PASSED

- FOUND: results/phase31_probe_point.json (tracked, 966f91b)
- FOUND: results/phase31_probe_relearn.json (tracked, 28338cd)
