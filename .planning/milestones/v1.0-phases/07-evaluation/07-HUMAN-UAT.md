---
status: complete
phase: 07-evaluation
source: [07-VERIFICATION.md]
started: 2026-06-09T21:02:05Z
updated: 2026-06-10T09:35:00Z
---

## Current Test

[all tests passed]

## Tests

### 1. Run the architecture-ablation cohort (EVAL-03)
expected: `python scripts/run_ablations.py` on the M3 (≈6.6h manual run) fills the four `_pending M3 cohort run_` held-out-PPL and best-val-loss cells in `results/results.md` and produces `results/abl_*.csv` curves for baseline / no_tie / no_pos / depth_cut at identical seed/data/LR/budget. The committed comparison table then presents a real comparison isolating one design choice per variant.
result: passed — cohort ran 2026-06-10 at the D-07-calibrated budget (REDUCED_MAX_STEPS=2500, locked from the 8k baseline curve). All four cells filled and committed: baseline PPL 2.8212 / val 1.0426, no_tie 2.7870 / 1.0312, no_pos 2.9221 / 1.0796, depth_cut 3.0074 / 1.1078 (all over 12,636,922 tokens). `results/abl_{baseline,no_tie,no_pos,depth_cut,calibration}.csv` produced and committed.

### 2. Confirm the headline held-out perplexity (EVAL-01)
expected: `python scripts/evaluate.py` reproduces the recorded headline full-val perplexity ≈ 2.1066 over 12,636,922 scored target tokens against the gitignored `best.pt`, and writes the curated samples to `results/samples.md`.
result: passed — `evaluate.py` on `checkpoints/best.pt` reproduced headline full-val perplexity 2.1066 over 12,636,922 scored target tokens exactly, and regenerated coherent `results/samples.md`. (Distinct from best.pt's recorded random-batch ppl 2.0913, per Pitfall 5.)

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
