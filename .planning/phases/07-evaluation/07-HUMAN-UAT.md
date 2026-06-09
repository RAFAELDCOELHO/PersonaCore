---
status: partial
phase: 07-evaluation
source: [07-VERIFICATION.md]
started: 2026-06-09T21:02:05Z
updated: 2026-06-09T21:02:05Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Run the architecture-ablation cohort (EVAL-03)
expected: `python scripts/run_ablations.py` on the M3 (≈6.6h manual run) fills the four `_pending M3 cohort run_` held-out-PPL and best-val-loss cells in `results/results.md` and produces `results/abl_*.csv` curves for baseline / no_tie / no_pos / depth_cut at identical seed/data/LR/budget. The committed comparison table then presents a real comparison isolating one design choice per variant.
result: [pending]

### 2. Confirm the headline held-out perplexity (EVAL-01)
expected: `python scripts/evaluate.py` reproduces the recorded headline full-val perplexity ≈ 2.1066 over 12,636,922 scored target tokens against the gitignored `best.pt`, and writes the curated samples to `results/samples.md`.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
