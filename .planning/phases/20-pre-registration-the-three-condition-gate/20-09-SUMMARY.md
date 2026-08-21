---
phase: 20-pre-registration-the-three-condition-gate
plan: 09
subsystem: documentation
tags: [pre-registration, decision-record, traceability, dated-amendment, ast-resolution, bookkeeping]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 07
    provides: "results/phase20_retention_floor.json — the measured adapter-regime floor 0.008681618994239138, cap 3.9085032379884783, borrowed_floor_ratio 7.939763314393305, all four re-read from the artifact rather than transcribed"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 06
    provides: "tests/test_phase20_prereg.py — the eight test_* guards the new traceability notes AST-resolve against"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 05
    provides: "scripts/mitigation_gate.py (CLOSED pin) — the identifiers the notes AST-resolve against and the line spans they cite"
provides:
  - "20-CONTEXT.md: D-34, D-35, D-36 and D-37 recorded as LOCKED decisions in the phase's own decision record, in the wave 20-08 depends on — so no shipped artifact cites an ID before its record exists"
  - "REQUIREMENTS.md: eight filled Phase 20 traceability notes, each naming a mitigation_gate mechanism AND the test_phase20_prereg guard that watches it, both AST-resolved"
  - "REQUIREMENTS.md: D-36's dated, additive, provably-tighter in-place amendment to GATE-02's requirement text, so a grep for 4.029000 lands on the correction"
affects: [20-08, 20-10, 20-11, 20-12, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A verify assertion is SCOPED to the span the task wrote when the asserted string already exists elsewhere in the file — measured first, then scoped: 2026-08-20 occurs 4x in 20-CONTEXT.md and 3.9085032379884783 / 0.008681618994239138 / 0.06893 were already in REQUIREMENTS.md, so a whole-file `in` check on any of them could not fail"
    - "A traceability note's claim of coverage is checked by AST RESOLUTION, not by substring: backticked tokens must resolve into the FunctionDef / module-scope Assign name set of scripts/mitigation_gate.py AND into the test_* set of tests/test_phase20_prereg.py"
    - "The check asserts the VISITED row set equals the expected eight, so a renamed or deleted row reddens instead of being silently skipped"
    - "Ordering between a decision record and the artifact citing it is enforced by the WAVE GRAPH (20-08 depends_on 20-09), never by within-plan task order, which cannot bind a sibling plan"
    - "A pre-registration amendment is admissible only as a conjunction: DATED and IN PLACE and ADDITIVE and provably TIGHTER — the arithmetic showing it moves the threshold against the amender's interest is part of the amendment, not a footnote"

key-files:
  created:
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-09-SUMMARY.md
  modified:
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-CONTEXT.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "D-34 — the GATE-06 correction is a real computation in unpinned code, not a caller convention: a convention cannot supply the held-out leg (no sweep_heldout_recalls parameter exists in the frozen 21-kwarg signature) and its tripwire could only assert compliance, never compute the correction"
  - "D-35 — WR-09's held-out leg closes in the SAME function and by the SAME discipline as the taught leg; coverage_verdict decides both in one body against one rule"
  - "D-36 — GATE-02's pre-registration text is amended IN PLACE, dated and additively, on four grounds that must hold together; precedent is ROADMAP SC1, which already carries this shape for this number"
  - "D-37 — the coverage statistic is criterion-matched per axis (Wilson upper on the X ceiling, raw recall on both Y floors); wilson_lower_bound is defined for REPORTING only, and the Y legs' inherited lack of a confidence bound is recorded and deliberately NOT fixed"
  - "GATE-01/03/04/05/07/08/09/10 checkboxes NOT re-checked — they were checked at 0f265e2 and a second edit would make one discharge look like two (T-20-56)"
  - "The GATE-06 and RPT-02 rows were left byte-identical: GATE-06 belongs to 20-12 and must not be discharged on the strength of a bookkeeping plan"

patterns-established:
  - "Measure-then-scope: `<already_present_strings>` is measured against HEAD before the verify block is written, so a later editor cannot un-scope a check by accident"
  - "A cross-reference clause appended to a traceability row deliberately avoids the amendment's own opener string, so the `count('Amended by D-36') == 1` uniqueness assertion keeps biting"

requirements-completed: []

# Metrics
duration: 10min
completed: 2026-08-21
---

# Phase 20 Plan 09: Gap-Closure Bookkeeping — Decision Record, Traceability Notes, GATE-02 Amendment Summary

**D-34…D-37 are now looked-up-able before `20-08` ships the docstring that cites them, eight silently-discharged Phase 20 requirements name the code and the guard that discharge them, and a `grep` for `4.029000` now lands on a dated amendment naming the `3.9085032379884783` that actually governs.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-08-21T14:35Z
- **Completed:** 2026-08-21T14:46Z
- **Tasks:** 3 of 3
- **Files modified:** 2 (plus this SUMMARY)

## Accomplishments

### Task 1 — D-34, D-35, D-36, D-37 recorded (`b6c20e9`)

A new `### Resolved during gap closure — decisions forced by 20-VERIFICATION.md` subsection was
appended to `## Implementation Decisions` in `20-CONTEXT.md`, positioned immediately before
`### Claude's Discretion` so it sits inside the decisions section, with a dated italic preamble in
D-31…D-33's register. 44 insertions, **0 deletions** — D-01…D-33 are untouched, unrenumbered and
unre-dated.

The ordering claim this plan carries is not a sentence: `20-08` declares `depends_on: [20-09]` and
this plan is the whole of gap-closure wave 1, so the module docstring that cites `D-34`, `D-35` and
`D-37` provably cannot be written before the record exists. Within-plan task order could never have
guaranteed that against a sibling plan in the same wave.

### Task 2 — the eight empty traceability notes filled (`0a24874`)

`GATE-01`, `GATE-03`, `GATE-04`, `GATE-05`, `GATE-07`, `GATE-08`, `GATE-09` and `GATE-10` each
gained a one-to-two-sentence note naming the mechanism in `scripts/mitigation_gate.py` **and** the
guard in `tests/test_phase20_prereg.py` that watches it, sourced from `20-VERIFICATION.md`'s
Evidence column. All twelve Phase 20 rows are now non-empty.

Every cited name was AST-resolved **before** the notes were written, and again by the acceptance
check afterward: backticked tokens must land in the `FunctionDef` / module-scope `Assign` name set
of `scripts/mitigation_gate.py` and in the `test_*` set of `tests/test_phase20_prereg.py`. This is
an AST resolution rather than an `X in source` substring test on purpose — this phase produced four
independent instances of a substring audit matching the prose explaining the pattern (recorded in
the `RPT-02` row), and policing that defect with the defect would have been absurd.

Every line span cited in the notes was re-verified against HEAD rather than copied: `y_taught` /
`y_heldout` at `:765-766`, the GATE-05 early return at `:730-745` (`745` is its closing paren), and
the GATE-08 replication branch at `:822-829` (`829` is its `return`). The five-name
`from erasure_gate import` list and the existence of `V20_TAUGHT_RECALL` / `V20_HELDOUT_RECALL` in
`scripts/erasure_gate.py` were both confirmed before GATE-04's note claimed them.

**Checkboxes untouched.** All eight were `[x]` from `0f265e2`; re-checking them would make one
discharge look like two in the commit record (T-20-56).

### Task 3 — D-36's dated in-place GATE-02 amendment (`e18df43`)

A blockquote opening `> **Amended by D-36 at plan `20-09`, and the amendment is TIGHTER.**` now sits
between the `- [x] **GATE-02**:` and `- [x] **GATE-03**:` bullets, in the same shape ROADMAP SC1
already carries from D-06. Every number in it was re-read from
`results/phase20_retention_floor.json`, not transcribed from a report:

| Field read | Value |
|---|---|
| `retention_ppl_noise_floor` | `0.008681618994239138` |
| `cap` | `3.9085032379884783` |
| `borrowed_floor` | `0.06893` |
| `borrowed_cap` | `4.029` |
| `borrowed_floor_ratio` | `7.939763314393305` |
| `seed_1337_remeasured_vs_published.abs_delta` | `0.0` |

The block states the tension rather than gliding over it — this repo's convention is that
pre-registration requirement text is not edited, which is exactly why the supersession originally
lived only in the traceability row — and resolves it on D-36's four conjoined grounds: DATED
(2026-08-21), IN PLACE, ADDITIVE (the original `4.029000` is byte-identical above it), and provably
TIGHTER (`3.9085032379884783 < 4.029`, from a floor `7.939763314393305x` smaller, so condition (c)
gets **harder** — a self-serving amendment moves a threshold the other way).

It also names the enforcement, so the amendment is a pointer to a mechanism rather than prose:
`_prove_retention_floor` in `scripts/phase20_gate_coverage.py` (plan `20-08`) refuses `0.06893` at
the choke point, and `tests/test_phase20_correction.py` (plan `20-11`) asserts `retention_cap` at
the measured floor equals the artifact's published `cap` bit-exact. Neither exists yet; both are the
next two waves, and the amendment is what makes their absence visible if they never land.

The `| GATE-02 |` traceability row gained one cross-reference clause and kept its
`RESIDUAL — OPEN` paragraph intact for `20-12` to rewrite. The clause deliberately does not repeat
the string `Amended by D-36`, so the `count(...) == 1` uniqueness assertion still bites.

## Verification

All three plan-supplied automated checks exited 0, each **scoped to the span its task wrote**:

| Check | Scope | Result |
|---|---|---|
| Task 1 | `2026-08-20` asserted only between the new heading and the `- **D-34` bullet | `OK` |
| Task 2 | 12 non-empty rows; 8 notes AST-resolved on both sides; visited set `==` expected eight | `OK — 12 non-empty rows, 8 notes AST-resolved on both sides` |
| Task 3 | 9 required strings asserted only between `Amended by D-36` and the `- [x] **GATE-03**` bullet | `OK  4.029000 at 2029  amendment at 2046  block len 2355` |

The scoping is load-bearing, not stylistic (T-20-63). Measured against HEAD before writing:
`2026-08-20` already occurred 4x in `20-CONTEXT.md`, and `3.9085032379884783`,
`0.008681618994239138` and `0.06893` were already in `.planning/REQUIREMENTS.md`. A whole-file
`assert s in text` on any of them could not have failed.

Diffs are additive as required:

- `20-CONTEXT.md` — 44 insertions, 0 deletions.
- `.planning/REQUIREMENTS.md` — 40 insertions, 9 deletions across the two tasks. Every deletion is
  a one-line table row replaced by itself plus content: the eight empty `| GATE-NN | Phase 20 | |`
  rows, and the `| GATE-02 |` row whose note gained the cross-reference clause (a single-line
  append is unrepresentable in a line diff any other way). **Zero deletions inside any
  `- [x] **GATE-NN**:` requirement bullet.**

No code was touched. The six test modules that read `.planning/` documents were run anyway —
`tests/test_phase20_prereg.py`, `test_phase15_docs.py`, `test_phase16_driver.py`,
`test_phase16_stats.py`, `test_phase16_ladder.py`, `test_phase17_stats.py` — **201 passed in 6.62s**.

## Task Commits

| Task | Commit | Files |
|---|---|---|
| 1 — record D-34…D-37 | `b6c20e9` | `20-CONTEXT.md` |
| 2 — fill eight traceability notes | `0a24874` | `.planning/REQUIREMENTS.md` |
| 3 — D-36 GATE-02 amendment | `e18df43` | `.planning/REQUIREMENTS.md` |

## Deviations from Plan

None. The plan executed exactly as written.

Two things worth recording that are *not* deviations:

1. **`requirements.mark-complete` was deliberately NOT run** for the plan's `requirements: [GATE-02]`
   frontmatter. GATE-02 is already `[x]`; the SDK verb would edit the checkbox and the traceability
   table, which is both a no-op at best and — given this repo's five recorded instances of
   `state.*` / `roadmap.*` handlers corrupting planning frontmatter — an unnecessary risk against
   the exact row this plan just rewrote. `STATE.md` and `ROADMAP.md` were hand-edited for the same
   reason.
2. **Line spans in the Task 2 notes were re-derived rather than trusted.** The plan cited
   `:730-745` and `:822-829`; both reproduced exactly against HEAD, so the plan's numbers were kept.
   Had they not, the note would have carried the measured span — a traceability note pointing at the
   wrong line is the T-20-55 defect class with a different surface.

## Threat Model Outcomes

| Threat ID | Disposition | Outcome |
|---|---|---|
| T-20-21 | mitigate | CARRIED FORWARD, open by design. The `| GATE-06 |` row is byte-identical after this plan; `20-12` rewrites it only after `20-11`'s tripwire has been watched RED-then-GREEN. |
| T-20-19 | mitigate | CARRIED FORWARD, open. The record half shipped: the D-36 amendment publishes the governing cap beside the borrowed one and NAMES the enforcement. The mechanism ships at `20-08` and closes at `20-11`. |
| T-20-52 | mitigate | Closed for this plan. The amendment is dated, additive (original byte-identical above it) and carries the arithmetic showing it moves the threshold against the amender's interest. |
| T-20-55 | mitigate | Closed. All eight notes AST-resolve on both sides, and the visited-set assertion means a renamed row reddens rather than being skipped. |
| T-20-56 | accept | Honoured. Zero checkbox edits — `git diff` shows no change to any `- [x] **GATE-NN**` bullet. |
| T-20-63 | mitigate | Closed. All three checks are scoped to spans this plan wrote, with the pre-existing strings measured and recorded in the plan so the scoping cannot be removed by accident. |

## Threat Flags

None. No code, no endpoints, no schema, no trust-boundary surface — two planning documents.

## Known Stubs

None.

## Notes for Future Plans

- **`20-08` is unblocked.** `D-34`, `D-35` and `D-37` are recorded; the module docstring may cite
  them. If `20-08`'s docstring wording diverges from the record, the RECORD is what shipped first
  and the docstring is what should move.
- **`20-11` inherits a published promise.** The GATE-02 amendment states in the pre-registration
  text that `tests/test_phase20_correction.py` asserts `retention_cap(measured floor) == cap`
  bit-exact. That sentence is now a commitment in a requirement, not just in a plan.
- **`20-12` finds what it expects.** The `| GATE-06 |` row and the `| GATE-02 |` row's
  `RESIDUAL — OPEN` paragraph are both intact; only a cross-reference clause was appended to the
  latter.

## Self-Check: PASSED

- `.planning/phases/20-pre-registration-the-three-condition-gate/20-CONTEXT.md` — FOUND
- `.planning/REQUIREMENTS.md` — FOUND
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-09-SUMMARY.md` — FOUND
- commit `b6c20e9` — FOUND
- commit `0a24874` — FOUND
- commit `e18df43` — FOUND
