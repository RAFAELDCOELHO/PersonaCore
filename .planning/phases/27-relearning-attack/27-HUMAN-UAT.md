---
status: partial
phase: 27-relearning-attack
source: [27-VERIFICATION.md]
started: 2026-09-16T22:20:00Z
updated: 2026-09-16T22:20:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Carry ruling for the latent review findings (CR-01, CR-02, WR-02, WR-03, WR-06; inconsequential WR-01, WR-04)
expected: A recorded ruling on how the confirmed-but-latent findings of 27-REVIEW.md (a1dec50), all reproduced by 27-VERIFICATION.md and none falsified, are carried. None has an owning phase today. Verifier's recommendation: named limitations in Phase 28's RPT-03 list, plus the obligation that the first phase to read ADMITTED fixes them in its continuation driver/pre-registration before its first leg — (a) refuse unless both corpus pins hold (CR-01); (b) compare the record's bytes with HEAD, re-derive admitted_point_keys and check frontier_sha256 at leg time (CR-02); (c) require every expected arm reading and refuse on diverging streams (WR-02); (d) route run CSVs under the gitignored out-dir (WR-03); (e) pre-register one gate baseline per leg and refuse to overwrite a gate output (WR-06); (f) rule on WR-05 before any adv_* admission. The alternative is an explicit decision to re-issue the operator-committed record (delete it in its own commit, fix the driver, re-run admit, operator re-commits); MOOT cannot change.
result: [pending]

### 2. WR-05 decision-coverage ruling — which control an adversarial point reads
expected: A dated ruling before any adv_* point can be admitted. Today the driver reads the DP control per leg (dp_n8 taught 790/1008 → threshold 0.5486); the frontier judged adv_n8 points against their own control (879/1008 → 0.6104); no adversarial control adapter is pinned; D-12/D-24/D-28 never considered the arm. Options: a pre-registration continuation keying threshold/pin/Z by (arm, leg); a refusal to admit adv_* points, with its reason; or acceptance of DP-control calibration, with its reason. Latent today: 0 of 12 adversarial points admissible (6 INCONCLUSIVE, 6 REFUSED).
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
