---
status: partial
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
source: [23-VERIFICATION.md]
started: 2026-08-29T11:03:56Z
updated: 2026-08-29T11:03:56Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Does the DPSGD-06 record in REQUIREMENTS.md earn a dated retract-in-place continuation?

Decide whether `.planning/REQUIREMENTS.md`'s DPSGD-06 record gets a dated retract-in-place
continuation — the 23-12 treatment — before Phase 24 planning reads it.

Reproduce the staleness with:

```bash
git ls-files 'results/phase23_noised_*' | wc -l   # returns 1; the row says "still empty"
```

and read `.planning/REQUIREMENTS.md:455` ("Plans 23-11 through 23-14 are BLOCKED; zero noised
sweep points may run") against the four executed SUMMARYs.

expected: Either a dated `RETRACTED IN PLACE` / discharge continuation is appended to the
DPSGD-06 inline body (lines 156-160) and traceability row (line 455) — pointing at
`results/phase23_matched_verdict.json` and the human unblock act `746ecf6` — or the developer
rules the ROADMAP + STATE continuations sufficient and records that choice.

why_human: The staleness is programmatically proven, but the remedy is a convention decision.
This project spent an entire plan (23-12) retracting a false claim in this same file under
exactly this convention; whether a second false claim in the same file, in the same phase,
earns the same treatment is the developer's call, not the verifier's.

result: [pending]

### 2. Does the never-taught scoring path get a committed positive control?

Decide whether the never-taught scoring path gets a committed positive control before Phase 25
(frontier lower-left floor) and Phase 27 (relearning reference) consume
`extraction_noise_floor = 0.0` twice.

The verifier ran the missing control and it FIRES — injecting one true fact value into one
completion of the real seed-1337 draw set moves the gated reading `0/416` -> `1/416` through the
unmodified `phase18_extraction.score_records`. The zero is therefore proven honest; this is a
gap in the *standing guard*, not in the measurement.

expected: Either a test lands in `tests/test_phase23_ctrl.py` that watches the scorer register a
constructed success on the retained draws (the same watched-RED discipline CAL-03 already has at
`test_an_n_leak_into_t_is_detected`), or the developer records that the inherited Phase-18
coverage plus this verification's one-off falsification is sufficient.

why_human: The zero is proven honest, so this is not a gap in the measurement. It is a gap in the
standing guard for a number two later phases consume. Whether that guard is owed before those
consumers exist is a scheduling decision.

result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
