---
status: partial
phase: 13-ewc-a-b-no-forgetting-experiment
source: [13-VERIFICATION.md]
started: 2026-08-01T21:05:00Z
updated: 2026-08-01T21:05:00Z
---

## Current Test

[awaiting the SC1 wording decision]

## Tests

### 1. Confirm or amend the ROADMAP SC1 wording supersession (λ* = None)

expected: `ROADMAP.md:164` states success criterion 1 as "differing ONLY in the penalty (λ=0 vs λ\*)". Phase 12 §8 recorded λ\* = None — calibration did not yield one — so Phase 13 ran λ=0 vs a **pre-chosen λ=0.01** per D-02/D-09. The substance of SC1 is fully verified (arms differ only in the penalty; confirmed by adversarial RNG tracing and by the EWC arm's step-250 `train_loss`/`ewc_penalty` being bit-identical to production). Only the roadmap's phrasing is superseded, and that supersession is recorded in `results/phase13_ab_report.md:303-305` (`## Reconciliation`) rather than silently absorbed into the roadmap text. Decide: accept the report-side record as sufficient, or amend `ROADMAP.md:164` to read "λ=0 vs a pre-chosen λ=0.01 (λ\* calibration returned None in Phase 12)".
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
