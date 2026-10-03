---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 07
subsystem: mps-cost-probes
tags: [cost-01, probes, mps, ledger, launchagent]
requires: [36-01, 36-02, 36-03, 36-04, 36-05, 36-06]
provides:
  - results/phase36_probe_e1.json
  - results/phase36_probe_e2.json
  - results/phase36_probe_e3.json
  - results/phase36_probe_e5.json
  - results/phase36_probe_e6.json
  - ledger/v6_mps_ledger.jsonl
key-files:
  created:
    - results/phase36_probe_e1.json
    - results/phase36_probe_e2.json
    - results/phase36_probe_e3.json
    - results/phase36_probe_e5.json
    - results/phase36_probe_e6.json
    - ledger/v6_mps_ledger.jsonl
  modified:
    - tests/test_phase36_probe.py
requirements-completed: [COST-01]
completed: 2026-10-02
---

# 36-07 — the M3 probe run, the probe records and the ledger

Executed inline by the orchestrator (no executor). Every number below was read from a committed
file after it existed.

## Task 1 — pre-launch gate

- HEAD at the gate: `b3ab341` (after the review fixes); `git status --porcelain -- scripts src
  results tests ledger artifacts` empty; then the STATE-only commit `877b92b`.
- `launchctl list | grep -i personacore`: four Phase 25 agents loaded, none running (PID `-`,
  status 0); no phase36 agent.
- Full suite at the zero-records state (b3ab341): **3781 passed, 4 skipped, EXIT=0** (41:46).
- `phase36_probe.py preflight`: `PREFLIGHT OK 877b92b7845bda9bbc130dd96387fddfab579be4
  fronts=e5,e6,e3,e2,e1`; porcelain unchanged (only the pre-existing `.claude/scheduled_tasks.lock`).
- `-k main_run`: 2 passed.

## Task 2 — the run (Rafael launched it)

Rafael ran the three launch commands on 2026-10-02 (agent PID 57156, `caffeinate -dims`).
The out log, one line per front:

```
[phase36_probe] e5 131.5 s
[phase36_probe] e6 103.3 s
[phase36_probe] e3 2137.9 s
[phase36_probe] e2 2876.9 s
[phase36_probe] e1 7926.7 s
```

Run span (record `provenance.run`): 2026-10-02T18:48:29Z → 22:28:06Z. The agent exited with
status 0; the err log is empty (0 bytes; corrected after verification). Not yet
unloaded at the time of writing (RunAtLoad/KeepAlive false, so it cannot relaunch).

## Task 3 — checks, emit, records, dry

Checks before emit: five `data/probe36_*_run.json` sidecars, each `reused` False and `device`
`mps`; no `data/probe36_*_rep*_arm.json` (pin draw files deleted, D-18); the log scan
`[0-9]+/[0-9]+ = |per_fact|hits` over `logs/phase36_probe.out` returned nothing;
`git ls-files 'results/phase19_*' 'results/phase37_*'` unchanged (sha e1ff8c7…); `reconcile`
appended nothing (ledger 10 lines before and after).

`emit-all` — six single-path commits, the ledger first (W9):

| commit | path |
|---|---|
| f7b9962 | ledger/v6_mps_ledger.jsonl |
| 893b3c0 | results/phase36_probe_e5.json |
| 987c86f | results/phase36_probe_e6.json |
| d389b53 | results/phase36_probe_e3.json |
| 26b6ab0 | results/phase36_probe_e2.json |
| 0d59b6d | results/phase36_probe_e1.json |

### Record numbers (read from the committed records)

- **E1** run 1: total 3935.18 s, fixed 177.20 s, draw sum 3757.98 s, K = 16 1422.45 s, 10368 draws
  (397 at cap). Run 2: total 3989.45 s, fixed 179.09 s, draw sum 3810.36 s, K = 16 1437.67 s,
  10368 draws (397 at cap). Fixed costs kept separate (D-18).
- **E2** train reps: outer 76.11 s / 75.66 s (loop 33.57 / 33.12, overhead 42.54 / 42.54). A2 pass:
  total 2724.68 s, fixed 172.57 s, 10368 draws, 48 per question.
- **E3** T = 200: train 211.91 s (loop 168.09, overhead 43.82), score 1253.28 s (3312 draws, 9 per
  question). T = 800: train 672.23 s, loop 629.02 s, overhead 43.21 s.
- **E5** clearance total 127.95 s, per-slot max 18.32 s; scoring per-slot mean-candidate max
  0.0467 s (k = 0) and 0.0099 s (k = 78), 56 candidates each.
- **E6** per-slot draw means [0.2405, 0.1646, 0.2303, 0.1919, 0.4431, 0.3483, 0.3488, 0.1629] s,
  384 draws (15 at cap), total 102.90 s.

### 25% comparisons — no gated row exceeds

| id | probe s | historical s | divergence |
|---|---|---|---|
| r1b_e1_k48#1 | 3935.18 | 4115.04 | 4.37% |
| r1b_e1_k48#2 | 3989.45 | 4115.04 | 3.05% |
| e2_a2_pass | 2724.68 | 2797.08 | 2.59% |
| e3_t200_train | 211.91 | 209.06 | 1.36% |
| e3_t200_score | 1253.28 | 1246.87 | 0.51% |
| e3_t800_linearity | 629.02 | 672.36 | 6.45% |
| e5_clearance | 127.95 | 126.0 | 1.55% |
| e2_training_context (ungated) | 76.11 | 80.34 | 5.27% |

No investigation note is owed (D-02/D-04): every gated divergence is below 25%.

### Dry budget at the defaults (proposal, nothing written)

`front_hours` E1 52.78, E2 14.14, E3 12.42, E4 4.81, E5 0.36, E6 7.90, R1b 1.11, probes 3.66;
**total 97.19 h → HALT: 7.189 h over the 90 h ceiling**, with the D-15 cut table (e4_reserve 4.81 h;
e6_anchor_adapters 0.047 h × 7; e2_seeds_to_3 5.66 h; e3_whole 12.42 h; e1_checkpoints 6.39 h × 4;
r1b 1.11 h; e1_core 27.22 h). Ruling alternatives: spread_scaled 85.13 h, at_cap 390.06 h,
probe_scaled 97.15 h. Rafael's ruling and the recomputed table are in 36-08-SUMMARY.

### Suite on the probes-only state

First run (HEAD 0d59b6d): **22 failed, 3759 passed, 4 skipped, EXIT=1** — all 22 in
`tests/test_phase36_probe.py` preflight tests, one cause: `_preflight_env` moved
`phase36_ledger._ROOT` to a tmp tree but left `phase36_caps.tracked_files()` reading the real
index; once the real ledger was tracked, the WR-04 append-only proof looked for its committed blob
in the tmp tree (`ledger/v6_mps_ledger.jsonl has no committed blob at HEAD`). The latent
state-dependent red the plan predicted; fixed in the TEST (`70251d6`, the fixture hides the real
tracked ledger), never in `phase36_ledger.py` (pinned by the probe records). 138/138 probe tests
green after. The full re-run is the 36-08 phase gate (fill + budget state).

## Deviations

1. Executed inline by the orchestrator, not by an executor (small mechanical plan).
2. The 22-red latent test (above) — fixed in the test, commit 70251d6.
3. Rafael typed "done" at launch, not at completion; the orchestrator watched the run read-only
   (heartbeat + logs) until the agent exited.
