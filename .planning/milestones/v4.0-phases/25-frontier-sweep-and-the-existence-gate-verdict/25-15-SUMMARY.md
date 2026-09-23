---
phase: 25
plan: 15
subsystem: sweep-controls
tags: [D-01, D-03, D-05, D-07, D-47, D-50, CTRL-02, FRONT-03, control, reproduction]
requires:
  - results/phase23_sigma_zero.json
  - results/phase23_never_taught.json
  - results/phase23_matched_control.json
  - scripts/phase25_points.py
  - scripts/phase25_n64_floor.py
provides:
  - results/phase25_point_dp_n8_sigma0p000000.json
  - results/phase25_point_dp_n64_sigma0p000000.json
  - results/phase25_n64_matched_floor.json
  - tests/test_phase25_control.py
affects: []
tech-stack:
  added: []
  patterns:
    - "the driver lands each control in its own single-path commit; the tests read the artifacts and git history, never a transcript"
decisions:
  - "The n=64 control reads 87/1008 — the DP sigma=0 arm and D-03's seam-off comparator at seed 1337 agree to the count and to the retention perplexity (3.947756), the n=64 form of Phase 23's 790 == 790."
  - "D-01's stated justification ('mitigation_point_verdict requires control_extraction_successes') was false: the gate reads the never-taught arm's 0/416 through extraction_ceiling. The control's extraction is justified by CTRL-02 + FRONT-03 and the record says so."
  - "D-50's seed_spread is the retention spread of D-03's five n=64 adapters (max 0.061495); the floor leg therefore ran before the first point."
metrics:
  duration: "controls landed by the sweep driver: n8 ~1h40m (train 218 s, recall 915 s, measure 88 s, draws 79 min), n64 ~2h20m (train 1383 s, recall 1070 s, measure 88 s, draws 90 min); floor leg 3.33 h"
  completed: 2026-09-05
---

# Phase 25 Plan 15: The Control at Both Capacities Summary

Both sigma=0 controls ran as the first two points of the live sweep, each committed by the driver in
its own single-path commit (`359a6fc`, `e444a95`). **The n=8 control reproduced Phase 23's reading
exactly: taught recall 790 / 1008**, checked under hard `==` by `prove_reproduction` before a single
extraction draw. The n=64 control is the repository's first n=64 reading: **taught recall 87 / 1008**,
identical to D-03's seam-off comparator at the same seed. The control's extraction — never measured
before — was measured at both capacities.

## Task 1 — the two control records

| | n=8 | n=64 |
|---|---|---|
| taught recall (ON) | **790 / 1008** (reproduced Phase 23 exactly) | **87 / 1008** (first measurement) |
| `clip_bind_count` at `C = 1e6` | 0, checked before scoring | 0, checked before scoring |
| mechanism (live == pin) | 200 steps, lot [8], q 1.0 | 200 steps, lot [64], q 1.0 |
| extraction, gated `core_held_out` (416 = 104 × 4) | A1-mild 91, A1-aggressive 22, A2 96, A3 76 of 104 | A1-mild 26, A1-aggressive 0, A2 15, A3 8 of 104 |
| refusal column | 0 / 13,824 | 0 / 13,824 |
| condition (c): dialogue ON / OFF, gap | 4.7084 / 4.5733, 0.1351 | 4.7449 / 4.5733, 0.1716 |
| retention perplexity | 3.7832 | 3.9478 |
| GATE-05 | 8 of 8 measured, `zero_extraction_has_nll: true` | 8 measured + 56 filler omitted with reason |
| `epsilon` | `null` + `epsilon_omitted_reason` | `null` + `epsilon_omitted_reason` |

The adapter-OFF dialogue reading is Phase 19's `4.573349214207799` at both capacities (D-45's free
reproduction check). The control **leaks** under extraction, as Phase 18 measured on v3.0 — the
n=64 control leaks far less because it recalls far less (8 facts among 64 in 200 steps).

**D-01's stated justification was false and the decision was re-justified on CTRL-02 + FRONT-03:**
`mitigation_gate.extraction_ceiling` consumes `(0, 416)` from the never-taught record through
`phase25_verdict.never_taught_anchors()`, never the control's counts; `scoring_justification` in
both records says so, and `test_the_gate_never_reads_the_controls_extraction` demonstrates it.

## Task 2 — D-03's n=64 floor (run first; see 25-14-SUMMARY)

`results/phase25_n64_matched_floor.json` (`f019c9a`): seeds 1337/2024/1338/2025/1339 → 87, 67, 67,
89, 98 of 1008; floor **0.030753968253968256** by the called `phase23_prereg.noise_floor`; n=8
reference 0.0267857142857143 quoted beside it; 3.33 h against the 3.3 h estimate.

## Task 3 — `tests/test_phase25_control.py`

**19 passed, 0 skipped** (flag set). The natural RED on live data, verbatim:

```
[phase25_prereg] ONE ATTEMPT — REFUSED for point 'dp_n8_sigma0p000000'. Its record is ALREADY TRACKED: ['results/phase25_point_dp_n8_sigma0p000000.json']. This phase's rules were pre-registered on 2026-08-31 while `git ls-files results/phase25_point_*.json` returned nothing. A SECOND attempt at one point with the first one's reading on screen is exactly the freedom that pre-registration spends.
```

## Deviations from Plan

- Task 2 ran before Task 1 (D-50's `seed_spread` needed it); the driver, not a separate script,
  produced Task 1's records; a score-stage halt on the first point cost only that stage (25-14 §12.5b).
- The full suite is run with `PERSONACORE_SWEEP_ACTIVE=1` and `--ignore=tests/test_phase25_venue.py`
  while the sweep owns the device (D-44); the flag-unset run is 25-14's.

## Verification

- `.venv/bin/python -m pytest tests/test_phase25_control.py -v`: 19 passed, 0 skipped.
- Task 1's automated verify over both records: exits 0 (`clip_bind_count 0`, `clip_norm 1e6`, 416/448 rows, gate passed).
- `git log --oneline -- results/phase25_n64_matched_floor.json | wc -l` = 1, one path.
- Full suite with `PERSONACORE_SWEEP_ACTIVE=1`, `--ignore=tests/test_phase25_venue.py` (D-44, the sweep owns the device): **2004 passed, 36 skipped, 83 warnings in 290.15s (0:04:50)** — the 36 skips are D-44's MPS legs, by name. Two pre-launch 'no point record exists' assertions became order-in-history invariants first (`c674d22`).
- The five frozen modules and `pyproject.toml`: untouched.

## Commits

`f019c9a` floor · `359a6fc` n8 control (driver) · `e444a95` n64 control (driver) · `93968c0` tests.
