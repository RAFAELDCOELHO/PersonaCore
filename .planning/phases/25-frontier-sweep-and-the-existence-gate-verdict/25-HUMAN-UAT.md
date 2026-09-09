---
status: partial
phase: 25-frontier-sweep-and-the-existence-gate-verdict
source: [25-VERIFICATION.md]
started: 2026-09-09T21:45:00Z
updated: 2026-09-09T21:45:00Z
---

## Current Test

[awaiting human decision — none of the three is a manual test of built behaviour; all three are
developer decisions the verifier is not entitled to make]

## Tests

### 1. Push `main` so CI measures the ubuntu skip count
expected: A green GitHub Actions run on `ubuntu-latest` whose HEAD contains this phase's wave-10..13
files, and the ubuntu literal in `tests/test_phase25_venue.py:238` replaced by the measured number
if it differs from the derived `52 + 3 + 7 = 62`.
why_human: `main` is 95 commits ahead of `origin/main` (newest there `15dce85`, 2026-09-02), so NO
CI run has ever executed any Phase-25 wave-10..13 code. The file labels its own ubuntu pin
**DERIVED, NOT MEASURED**. Only a push closes it, and pushing is an outward-facing action the
verifier and the orchestrator must not take unasked. The 25-REVIEW CR-01 fix must land first.
result: IN PROGRESS 2026-09-09 — the CR-01 fix landed (`795edb3`) and `main` was pushed to `origin/main` (`15dce85..52e736c`, 99 commits). CI run 34403612853 started at 20:52 UTC; the ubuntu skip count it measures is compared against the derived `52 + 3 + 7 = 62` and the pin is replaced with the measured number if they differ.

### 2. Choose the repair route for `mechanism_pin_disclosure.governs`
expected: Either `results/phase25_frontier.json` is re-assembled through the sanctioned
delete-in-its-own-commit route with the per-arm wording, or the discrepancy is recorded where a
reader of the artifact will meet it (`results/phase25_operational_note.md` + a deferred-items entry).
why_human: 25-REVIEW WR-03, independently confirmed by the verifier. The published sentence says the
lot is re-derived "for all 44 points" as `batch_size x max(1, grad_accum_steps)`; the code applies
that formula only on the adversarial arm. On `dp_n8_sigma0p000000` the sentence gives `8 x 8 = 64`
while `records_per_lot` is `8` (`n_facts`). `lot_rule_by_arm` beside it is correct, so the artifact
contradicts itself inside FRONT-03's single source of truth. **No verdict, count, epsilon or Success
Criterion is affected.** The artifact is write-once and downstream-pinned, so the route is a
decision, not a code fix.
result: RESOLVED 2026-09-09 — operator chose: record it in the note and correct the emitter, no re-emit. Landed in the WR-03 commit (note §13.8, `MECHANISM_PIN_DISCLOSURE_GOVERNS_AS_PUBLISHED` pinning the published bytes, the corrected constant naming both arms, two guard tests, and the module-digest test re-pinned to the bytes at the write because the artifact pins the emitter's own sha256).

### 3. Give the adversarial no-replay recipe an owner, or scope the report around it
expected: Either a replay-bearing adversarial re-run has an owning phase with a success criterion,
or Phase 28's report is scoped to publish the adversarial arm as explicitly recipe-confounded.
why_human: The adversarial arm trains with NO replay (note §12.5c), so condition (c) fails on all 12
adversarial points for the recipe rather than the ratio, and at n=64 the arm's own ratio-0 control
scored held-out 0/648 — which is what the coverage route refused on. `deferred-items.md`
(D-25-18-ADV64-REFUSED) hands this to "a later phase" and names none; Phases 26 (canary), 27
(relearning) and 28 (report) carry no goal or criterion covering it. This is a scope and GPU-budget
call, not a verifier call. Decide before Phase 28 publishes.
result: RESOLVED 2026-09-09 — operator chose BOTH: v4.0 publishes the arm as explicitly recipe-confounded (new Phase 28 Success Criterion 4, naming the no-replay cause, the `7,581 teaching + 0 replay` log line, the six n=64 refusals and the 0/648 control), and the measurement itself is opened as a v5.0 candidate milestone in ROADMAP.md — a replay-bearing adversarial re-run of the 12 points, ~25-30 h of MPS at Phase 25's measured pace.

## Summary

The phase goal is achieved: 7/7 must-haves verified, 8/8 requirements accounted for, and the parts
most likely to have been narrated rather than built were re-derived from bytes by the verifier —
38/38 route-reachable verdicts re-computed live through the imported frozen route with 0 mismatches,
12/12 adversarial adapters re-hashed, 44/44 recall readings re-pinned to their `adapter_sha256`, the
gate and budget module digests recomputed, the ordered-key equality re-checked on the committed
bytes, and the machine state read live. The status is `human_needed` only because of the three items
above.

## Gaps

None. No must-have failed, no artifact is missing or stubbed, no key link is unwired, and no blocker
anti-pattern exists.
