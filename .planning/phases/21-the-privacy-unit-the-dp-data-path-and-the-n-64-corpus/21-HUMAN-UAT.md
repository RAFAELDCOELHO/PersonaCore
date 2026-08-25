---
status: partial
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
source: [21-VERIFICATION.md]
started: 2026-08-24T22:20:00Z
updated: 2026-08-25T01:00:00Z
---

## Current Test

number: 3
name: WR-06 — a bare `assert` strippable by `python -O`
expected: |
  `scripts/phase21_filler.py:262` guards the `== 10` leak-vocabulary wall with a bare
  `assert`. Confirmed live: `.venv/bin/python -O -c 'import phase21_filler'` imports
  cleanly with the assert stripped.

  The module's own comment on the line above says it "joins the `== 10` wall HERE, at the
  one file in the repo that could break it", and its sibling frozen pin
  (`mitigation_unit.py:73-76`) states the exact rule this violates. Every other refusal in
  the same file (`refuse_collisions`, `verify_round_trips`) correctly raises `SystemExit`.

  The repo does not run under `-O` today, so this is a latent robustness gap rather than a
  live failure — unlike WR-04, which turned out to have two present-tense call sites.

  Decide: promote to `raise SystemExit`, or accept the latent gap.
awaiting: user response

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

result: pass
decided: "Annotate in place. Retracted at c05880c."
notes: |
  Executed, not just decided. The user's stated figure (44.7549%) was the SUPERSEDED
  pre-WR-01 value; the committed artifact records 44.755245%, so 44.7552% was written.
  The repo-wide check the user asked for found a second live-source site carrying the
  identical uncorrected claim — tests/test_phase21_replay_volume.py:63 — retracted the
  same way. A third site (phase21_unit_record.py:831) was made stale BY the edit and
  fixed to past tense; its sibling at :929-930 was deliberately left alone because it is
  emitted into the artifact, and both artifact sha256 verified unchanged afterwards.
  Suite 994 passed / 1 skipped, ruff clean.

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

result: pass
decided: "Write the continuation. Landed at 9a407d6 as scripts/phase21_unit_continuation.py."
notes: |
  ESCALATED. The premise "nothing is wrong TODAY, Phase 22 owns it" is FALSE.
  scripts/phase21_unit_record.py:1009 and :1037 already reached the pin, aliased as
  `mu.privacy_n` — invisible to any matcher keyed on the literal string. :1037's n is
  multiplied by DELTA and checked against DELTA_TIMES_N_CEILING, so a zero N there CLEARS
  THE PUBLISHED CEILING rather than mislabelling a row. Both were redirected, not exempted.

  Two of my own premises were corrected: _addendum.py is a markdown append-only writer and
  cannot host code (vehicle moved to the phase20_gate_coverage.py shape the repo already
  built for superseding a frozen pin); and no sys.modules hook, shadow or rename forces the
  import, so enforcement is an AST guard modeled on test_phase20_prereg.py:873-905.

  Exact floats (7.0) refused, justified from teach_persona.py:743-750's existing rule on the
  same quantity rather than from preference. Wider than any document recorded:
  privacy_n(False) -> 0, privacy_n(7.0) -> 7, privacy_n(3.0000000001) -> 3.

  RED/GREEN re-verified by the orchestrator on main: pin still returns 7 / 0 / -3; the
  continuation raises SystemExit on 7.9, 0, -3, True, 7.0, '8' and admits 8. Guard exemption
  is a frozenset of two resolve()d paths, proven against a same-basename decoy under tmp_path.
  Suite 1024 passed / 1 skipped; ruff clean; pin and both artifact digests unchanged.

  TWO GAPS RECORDED, NOT CLOSED (both already named at test_phase20_correction.py:1395-1399):
  getattr(mitigation_unit, "privacy_n") produces no matching AST node, and a driver at the
  repo root or under tools/ is unscanned.

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
passed: 2
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
