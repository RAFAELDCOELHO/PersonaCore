---
status: partial
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
source: [21-VERIFICATION.md]
started: 2026-08-24T22:20:00Z
updated: 2026-08-24T22:20:00Z
---

## Current Test

[awaiting human decision]

## Tests

### 1. WR-03 — a measured-false number still asserted in live source

expected: `scripts/teach_persona.py:162-163` states "49.90% at n=64, because both sides scale
with `n_facts`. Nothing re-tunes." The phase's own committed artifact records
`documented_n64_claim_holds: false` and `measured_n64_share_at_the_pinned_constant:
0.44755244755244755`. The file is editable and NOT ancestry-pinned, so the project's
retract-in-place rule applies and nothing blocks the edit.

why_human: Whether a measured-false number may stand in live source while its correction lives
only in a `results/` artifact is a project-convention judgement, not a testable property. Both
states are green today.

decision: annotate in place before Phase 22, or accept the divergence.

result: [pending]

### 2. WR-04 — `privacy_n` unvalidated inside the frozen module Phase 22 imports

expected: `mitigation_unit.privacy_n` is frozen and Phase 22's accountant imports it for N.
Measured: `privacy_n(7.9) -> 7` (silently drops a record), `privacy_n("8") -> 8`,
`privacy_n(0) -> 0` (then `δ·N == 0` clears the ceiling), `privacy_n(-3) -> -3`. No Phase 21
addendum exists — grep of `scripts/_addendum.py` for `phase21` / `mitigation_unit` / `privacy_n`
returns nothing.

why_human: This is the wrong-unit defect class one level up, sitting in the module the NEXT phase
consumes — aimed squarely at the phase that exists to prevent it. Phase 21 computes no ε, so
nothing here is currently wrong; whether the continuation is owed by 21 or by 22 is a scope
decision. The pin is FROZEN, so the only route is a dated continuation via `scripts/_addendum.py`
— editing the pin would permanently redden the ancestry guard with no undo.

decision: write the `_addendum.py` continuation exporting a validated `privacy_n` before Phase 22,
or accept the pin's version and let Phase 22 own it.

result: [pending]

### 3. WR-06 — a bare `assert` strippable by `python -O`

expected: `scripts/phase21_filler.py:262` guards the `== 10` wall with a bare `assert`. Confirmed
live: `.venv/bin/python -O -c 'import phase21_filler'` imports cleanly with the assert stripped.
The module's own comment says it "joins the `== 10` wall HERE, at the one file in the repo that
could break it", and its sibling frozen pin (`mitigation_unit.py:73-76`) states the exact rule this
violates. Every other refusal in the file (`refuse_collisions`, `verify_round_trips`) correctly
raises `SystemExit`.

why_human: The repo does not run under `-O` today, so this is a latent robustness gap rather than a
live failure. Whether it is worth a commit is a judgement.

decision: promote to `raise SystemExit`, or accept the latent gap.

result: [pending]

### 4. The phase's own documentation ledger

expected:
- `21-VALIDATION.md` — every row still reads `TBD | TBD | TBD` / `pending`, and row `:81`'s
  selector `-k phase21_glob_red_then_green` collects ZERO tests and exits 0 (measured:
  `22 deselected in 0.01s`, exit 0). A second vacuous selector at `:88-89` was already found by
  21-09 during execution.
- `.planning/REQUIREMENTS.md` — all six UNIT bullets still `- [ ]` and all six traceability Note
  cells EMPTY, against a convention where GATE-01..GATE-10 carry substantial evidence notes.
- `.planning/STATE.md` — the orchestrator has already repaired this during the run
  (`Plan: 11 of 11`, `Status: Awaiting human verification`, `completed_plans: 28`,
  `stopped_at` naming the verification outcome). Only `21-VALIDATION.md` and `REQUIREMENTS.md`
  remain.

why_human: None of this affects code correctness. It affects whether Phase 22 can trust the ledger
it reads. The `gsd-sdk` mutation handlers are known to corrupt this frontmatter — during this run
`state.update-progress` reported `updated: false, reason: "Progress field not found"` while
silently writing four fields, two of which it was never asked about — so the repair route is a
human decision rather than another handler call.

decision: close the ledger before Phase 22, or carry it forward.

result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
