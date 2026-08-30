---
status: partial
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
source: [24-VERIFICATION.md]
started: 2026-08-30T19:23:45Z
updated: 2026-08-30T20:36:24Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Give ADVT-01 an owning phase in ROADMAP.md  [RESOLVED]
expected: ADVT-01 has a phase that formally claims it. Today REQUIREMENTS.md:476 maps it to
Phase 24; Phase 24's own `**Requirements**` line (ROADMAP.md:718) claims it and its traceability
row correctly declares it unsatisfiable ("no adapter has been trained"). Phase 25 — which actually
does the work, per its SC2 "intensity for adversarial ... swept to the never-taught floor" — does
NOT list it: ROADMAP.md:814 reads `CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04`.
Verified by the orchestrator: `grep -n "ADVT-01" .planning/ROADMAP.md` returns hits only inside
Phase 24's block (718, 723, 785, 807). The requirement is currently unownable by the process.
Suggested fix: append `, ADVT-01` to ROADMAP.md:814.
RESOLVED 2026-08-30 at commit e5a2474 — ROADMAP.md:814 now carries ADVT-01, and the resulting
two-phase span (24 builds, 25 satisfies) is recorded as a dated additive amendment under
REQUIREMENTS.md's Traceability heading rather than by editing the dated 2026-08-20 count.
why_human: Editing the roadmap's requirement mapping is a planning decision. The verifier can
observe the hole but must not silently reassign a requirement.
result: resolved (developer decision 2026-08-30; commit e5a2474)

### 2. Decide ADVT-02's ticked wording vs the actual mechanism
expected: The requirement prose says A2 "is REFUSED at the episode builder, not dropped". The
mechanism is filter-then-refuse: A2 rows are excluded by the list comprehension at
scripts/phase24_adversarial.py:289-292 (`row["family"] in TRAINED_FAMILIES`), and the SystemExit
at :300 is explicitly belt-and-braces behind it — the code's own comment reads "BELT AND BRACES
beside the filter above, not instead of it" — firing only if the filter widens. The operative
property (A2 never trains) holds doubly and is verified. Question is whether the ticked prose
should read "filtered out AND refused behind the filter".
why_human: Editorial call on the wording of an already-ticked requirement.
result: [pending]

### 3. Confirm 24-04's instrumentation is intended for Phase 25 consumption
expected: `contains_refusal` / `score_refusal` / `clean_frame_probe_populations` in
scripts/phase14_recall.py are called by Phase 25's sweep driver. Today they are exercised only by
tests/test_phase24_refusal_rate.py — verified correct in isolation (112 vs 112 distinct,
budget-matched, disjoint, 0 of 10 published values across 224 questions) but consumed by no running
pipeline. No ROADMAP SC required them wired during Phase 24, so this is not a gap against the
contract.
why_human: An unconsumed instrument is how a planned measurement quietly never gets taken.
result: [pending]

## Summary

total: 3
passed: 1
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
