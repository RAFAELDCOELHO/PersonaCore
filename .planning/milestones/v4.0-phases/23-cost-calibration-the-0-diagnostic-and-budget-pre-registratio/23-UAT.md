---
status: complete
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
source: [23-01-SUMMARY.md, 23-02-SUMMARY.md, 23-03-SUMMARY.md, 23-04-SUMMARY.md, 23-05-SUMMARY.md, 23-06-SUMMARY.md, 23-07-SUMMARY.md, 23-08-SUMMARY.md, 23-09-SUMMARY.md, 23-10-SUMMARY.md, 23-11-SUMMARY.md, 23-12-SUMMARY.md, 23-13-SUMMARY.md, 23-14-SUMMARY.md, 23-15-SUMMARY.md, 23-16-SUMMARY.md, 23-17-SUMMARY.md, 23-18-SUMMARY.md, 23-19-SUMMARY.md, 23-20-SUMMARY.md]
started: 2026-08-29T15:52:45Z
updated: 2026-08-29T16:05:28Z
---

## Current Test

[testing complete]

## Tests

### 1. Suite and lint green from the pinned venv
expected: `.venv/bin/python -m pytest tests/ -q` reports `1591 passed, 1 skipped`; `.venv/bin/ruff check . && .venv/bin/ruff format --check .` reports `All checks passed!` / `219 files already formatted`.
result: pass

### 2. DPSGD-06 — the sigma=0 point was the DP arm's first executed run, and the diagnostic fired
expected: `results/phase23_sigma_zero.json` reads `verdict: HALT`, `reading: 0.7837301587301587`, `clip_norm: 1000000.0`, `clip_bind_count: 0`. `pytest tests/test_phase23_prereg.py -k precedes` returns 6 passed — the git ordering (sigma=0 record before any noised point) is a live guard, not a claim.
result: pass

### 3. The halt is discharged through a byte-unedited rule
expected: `git diff c7de5d4 HEAD -- scripts/phase23_prereg.py` prints nothing — the blind verdict function was never edited. `results/phase23_matched_verdict.json` reads `verdict: proceed`, `deviation: 0.0`, `floor: 0.0267857142857143` — half the original floor. The verdict changed because the comparator got better, not because the criterion got looser.
result: pass

### 4. CAL-01 / CAL-05 — cost measured on the real DP path and the real noised adapter
expected: `results/phase23_cost.json` `training.dp_n64` reads `seconds_total: 1383.276182374917` over `timed_iterations: 200` with `dp_seam_active: true`. `generation.h_per_point_floor: 5.7223403197590965` h and `h_per_point_ceiling: 9.013691285839306` h — BOTH above the previously committed 4.77 h/point, which is the finding.
result: pass

### 5. CAL-02 — Z is pinned literal-only, and the gate cannot import it
expected: `scripts/mitigation_budget.py` carries `SWEEP_POINTS = 16`, `CURVE_K = 16`, `FULL_FIDELITY_K = 48`, `STEP_BUDGET = 200`, `N_CONTROL_SEEDS = 5`, `N64_LEG_WITHDRAWN = False` — all literals, zero import statements in the module — each with a `_PROVENANCE` sibling naming `results/phase23_cost.json` and its sha256. `pytest tests/test_phase23_budget.py tests/test_phase20_prereg.py -q` passes, including the out-of-process probe proving the gate never pulls the budget into `sys.modules`.
result: pass

### 6. CAL-03 — the n=64 premise was confirmed by a run, not assumed
expected: `results/phase23_cal03_wiring.json` reads `verdict: true` with `epsilon_n8 == epsilon_n64 == 24.38161088311366` and `t_n8 == t_n64 == 4` at sigma=0.5 / delta=1e-05. `pytest tests/test_phase23_cal03.py -q` returns 11 passed, including the watched N-leak positive control that proves the probe would redden if n_facts ever leaked into T.
result: pass

### 7. CTRL-03 — the never-taught floor is measured, and it is zero
expected: `results/phase23_never_taught.json` reads `readings: [0.0, 0.0, 0.0, 0.0, 0.0]` over 5 seeds at `curve_k: 16`, `extraction_noise_floor: 0.0`, `consumers: ['frontier lower-left floor', 'relearning reference']`. The five adapters were TRAINED once (23-08) and SCORED once (23-14) — adapter sha256s are identical across `phase23_never_taught_training.json` and `phase23_never_taught.json` at all five seeds.
result: pass

### 8. The never-taught scorer has a STANDING positive control
expected: `pytest tests/test_phase23_ctrl.py -k "registers_a_constructed_success or zero_to_one" -q` passes. Degrade the scorer (`phase14_recall.contains_value` -> `return False`) and both tests go RED with the right assertion; restore and they go green. A silently-broken scorer can no longer produce the same artifact a clean run does.
result: pass

### 9. DPSGD-06's stale record is retracted in place, dated
expected: `.planning/REQUIREMENTS.md:160` carries a `DISCHARGED 2026-08-29` continuation and the traceability row carries the retraction between `23-UAT1-CONTINUATION` sentinels. The two false sentences ("...and is still empty"; "Plans 23-11 through 23-14 are BLOCKED") are retracted, not deleted — the originals still stand, same treatment plan 23-12 gave this file.
result: pass

### 10. The M3/MPS primary path — battery device-widened, and production resume proved
expected: `pytest tests/test_phase23_mps_venue.py tests/test_phase22_dpsgd.py tests/test_phase22_checkpoint.py tests/test_phase22_fakes.py tests/test_phase23_resume.py -q` passes with ZERO MPS skips on the M3. `tests/test_phase23_resume.py` includes the production kill->resume proof through `teach_persona.train_arm(resume_from=)` — the same epsilon after a kill, on MPS, closing WARNING-2.
result: pass

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
