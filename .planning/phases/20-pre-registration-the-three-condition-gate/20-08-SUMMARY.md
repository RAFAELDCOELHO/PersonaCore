---
phase: 20-pre-registration-the-three-condition-gate
plan: 08
subsystem: pre-registration-correction
tags: [gate-06, coverage, wilson, provenance, choke-point, unpinned, supersession]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 09
    provides: "20-CONTEXT.md: D-34, D-35, D-37 recorded as LOCKED decisions — the module docstring cites all three, and a decision ID appearing in a shipped module before its record exists is a citation to nothing"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 05
    provides: "scripts/mitigation_gate.py (CLOSED pin) — extraction_ceiling, mitigation_point_verdict, F_Y, EXTRACTION_FLOOR_MIN_SEEDS and the three committed FIXTURE_* dicts this module calls, imports and is measured against"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 07
    provides: "results/phase20_retention_floor.json — the measured adapter-regime floor 0.008681618994239138 that _prove_retention_floor's refusals name as what the borrowed 0.06893 is refused in favour of"
  - phase: 19-selective-erasure
    plan: 01
    provides: "scripts/erasure_gate.py (v3.0 CLOSED pin, 23a830c) — wilson_upper_bound, MARGIN_K, V20_RETENTION_NOISE_FLOOR and _Z_ONE_SIDED_95, every one imported by object identity"
provides:
  - "scripts/phase20_gate_coverage.py — UNPINNED, 602 lines, the executable half of the D-24 dated continuation"
  - "coverage_verdict(...) -> (covered, truncated_axes, sentence) — the corrected GATE-06 coverage test, criterion-matched per axis, deciding BOTH Y legs (D-35 / WR-09)"
  - "wilson_lower_bound(successes, n, z=erasure_gate._Z_ONE_SIDED_95) — REPORTED never DECIDING, with an analytically-exact successes==0 short-circuit"
  - "_prove_retention_floor(*, retention_noise_floor, retention_floor_provenance) — four refusals; the choke point the frozen retention_cap cannot be given (T-20-19)"
  - "corrected_point_verdict(...) — the one sanctioned route to a v4.0 verdict; 24 keyword-only args, sweep_extraction_rates ABSENT BY CONSTRUCTION"
  - "COVERAGE_STATISTIC_BY_AXIS, RETENTION_FLOOR_PROVENANCE_KEYS, ADAPTER_REGIME, SUPERSEDED_GATE06_BLOCK, SUPERSEDED_SWEEP_SENTINEL — module data 20-10's artifact and 20-11's tripwire read"
affects: [20-10, 20-11, 20-12, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A frozen pre-registration is corrected by a REAL COMPUTATION in unpinned code that CALLS the pin, never by an edit and never by a caller convention (D-34)"
    - "Coverage of a criterion is tested on the SAME STATISTIC the criterion is decided on — criterion-matching, not 'always use the tighter bound' (D-37)"
    - "A parameter deleted removes a wrong VALUE SPACE's path; a _prove on the replacement parameter removes the wrong value. Both are needed and neither substitutes for the other"
    - "A guard's POSITION is part of the guard: a sign check placed after the computation it protects is pre-empted by a downstream range message at exactly the magnitudes that make the sign error large"
    - "Refusal messages publish DERIVED numbers, computed from the imported constant through the frozen function, never retyped literals"
    - "Constant reuse is proved by the mechanism that can actually FAIL for that object: `is` for a float (F_Y) or a function (wilson_upper_bound), AST import-vs-assign for a small int CPython interns (EXTRACTION_FLOOR_MIN_SEEDS, MARGIN_K)"
    - "A declared, docstring-justified divergence from an exact mirror is inside the no-second-copy discipline; a silent one is the defect"

key-files:
  created:
    - scripts/phase20_gate_coverage.py
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-08-SUMMARY.md
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "D-37 implemented as CRITERION-MATCHING: wilson_upper_bound on the X ceiling because condition (a) at :755-756 decides on it, RAW recall on both Y floors because condition (b) at :767-768 decides on it. A Wilson lower bound on a floor would be CR-01's own defect class with the sign flipped"
  - "The Y legs inherit condition (b)'s missing confidence bound. RECORDED in the module docstring with its cost and deliberately NOT fixed — correcting it would move a pre-registered threshold after seeing the data it governs"
  - "wilson_lower_bound opens with `if successes == 0: return 0.0` — analytically exact (centre == spread identically at p=0), not a fudge and not a tolerance; the divergence from the mirror is declared in the docstring against T-20-53"
  - "The measured adapter-regime floor is the module's ONE float literal, private, with its artifact named — the three published refusal numbers (ratio, borrowed cap, governing cap) are derived from it and the imported V20_RETENTION_NOISE_FLOOR through the frozen retention_cap"
  - "COVERAGE_STATISTIC_BY_AXIS is a tuple of (axis, statistic, criterion_site) triples, NOT the dict shape the plan's prose attributed to CHOSEN_CONSTANTS (which is `{\"F_Y\": ..., \"F_C\": ...}`) — the plan's own action text and verify block both prescribe the tuple, and the tuple is what a per-axis resolution needs"
  - "requirements.mark-complete NOT run for `requirements: [GATE-06, GATE-02]` — neither is discharged here. GATE-06 belongs to 20-12 and closes only after 20-11's tripwire is watched RED-then-GREEN; GATE-02 was already [x] and amended at 20-09"

patterns-established:
  - "Name the fixture, not just the direction: 'returns a decisive FAIL' with no fixture named was unverifiable prose until DIRECTION (ii) was pinned to FIXTURE_DESTROYED_MODEL and the third, unreported FIXTURE_CLEARING_POINT case was measured beside it"
  - "Publish both counts when a measurement has two defensible definitions (75 nonzero residues vs 55 where the defect actually fires) — a number that does not reconcile to its own definition is the defect this phase exists to refuse"

requirements-completed: []

# Metrics
duration: 13min
completed: 2026-08-21
---

# Phase 20 Plan 08: The GATE-06 Coverage Correction and the Retention Choke Point Summary

**`scripts/phase20_gate_coverage.py` now decides sweep coverage on the same statistic each criterion is decided on — and decides the held-out leg the frozen 21-kwarg signature has no parameter for — while `scripts/mitigation_gate.py` stays byte-identical to HEAD.**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-08-21T14:54Z
- **Completed:** 2026-08-21T15:07Z
- **Tasks:** 3 of 3
- **Files created:** 1 (602 lines, plus this SUMMARY)

## Accomplishments

### Task 1 — the corrected coverage computation and the bound-direction resolution (`eed1667`)

`scripts/phase20_gate_coverage.py` created, UNPINNED. It bootstraps `sys.path` exactly as
`mitigation_gate.py:52-54` does, imports `erasure_gate` and `mitigation_gate` as module handles, and
imports `MARGIN_K`, `V20_RETENTION_NOISE_FLOOR`, `wilson_upper_bound`, `EXTRACTION_FLOOR_MIN_SEEDS`
and `F_Y` by name. Every one is used by object identity and none is retyped — asserted directly:
`phase20_gate_coverage.wilson_upper_bound is mitigation_gate.wilson_upper_bound is
erasure_gate.wilson_upper_bound`.

The module docstring carries the three required blocks. Both reproduced directions are named with
their fixtures — `FIXTURE_CLEARING_POINT` for direction (i)'s spurious `INCONCLUSIVE`,
`FIXTURE_DESTROYED_MODEL` for direction (ii)'s spurious `FAIL` — plus the third case no report
records, `FIXTURE_CLEARING_POINT` under direction (ii)'s sweep, which the pin answers `PASS` off an
extraction axis that never produced a clearing point. That one is recorded and explicitly not
overstated: it does not contradict the verifier's narrower, self-consistent-inputs claim.

**The bound-direction resolution.** The governing principle is written as CRITERION-MATCHING, not
"always use Wilson". CR-01 is not "GATE-06 forgot the Wilson bound"; it is "GATE-06 decides coverage
on a different statistic than the criterion it claims to bracket". So:

| Axis | Coverage statistic | Because the criterion reads it at |
|---|---|---|
| `extraction` | `wilson_upper_bound` | `mitigation_gate.py:755-756` |
| `taught_recall` | `raw_rate` | `mitigation_gate.py:767` |
| `heldout_recall` | `raw_rate` | `mitigation_gate.py:768` |

That table is `COVERAGE_STATISTIC_BY_AXIS`, module data, so T-20-54's accepted misuse risk is
contradicted by a value rather than only by a paragraph. **The cost is read aloud**: the Y legs'
coverage inherits condition (b)'s own lack of a confidence bound, so a Y coverage decision at small
n is exactly as noisy as (b) itself. That noise belongs to the FROZEN criterion; correcting it would
mean moving a pre-registered threshold after seeing the data it governs, so it is recorded and
deliberately not fixed. The Wilson discipline is honoured on Y by REPORTING — `wilson_lower_bound`
is published beside each Y point's raw rate, in `erasure_gate.py:161-168`'s `rule_of_three`
register — and never by DECIDING.

**`wilson_lower_bound` opens with `if successes == 0: return 0.0`**, and the docstring records all
four required points. It is exact, not a fudge: at `p = 0` the algebra gives `centre == spread`
identically (both `z²/2n`), so Wilson's lower bound at zero successes IS analytically `0` and it is
the floating-point evaluation, not the clamp, that is wrong. `max(0.0, ...)` cannot absorb it
because the `sqrt` round-trip residue is POSITIVE. And it is not special-casing `n = 104` — measured
over `2..300`, **75** denominators leave a nonzero `centre - spread`, **20** of those residues are
negative and absorbed by the clamp, leaving **55** where the defect actually fires:

| n | `centre - spread` | naive lower bound |
|---|---|---|
| 11 | `1.3877787807814457e-17` | `1.1138242448922617e-17` |
| 104 | `1.734723475976807e-18` | `1.6907391655729735e-18` |
| 208 | `8.673617379884035e-19` | `8.562244663529347e-19` |
| 8, 16, 50, 200 | `0.0` | `0.0` |

Both counts are published rather than the larger one alone. The guard keys on `successes == 0` —
the only input where `centre == spread` holds — so `n = 104` records where it was CAUGHT, not what
the guard is keyed on. The T-20-53 reconciliation is stated in the docstring so a later reader
"restoring the symmetry" is warned off.

`coverage_verdict` returns the bare 3-tuple `(covered, truncated_axes, sentence)` behind FIVE
`_prove` calls, of which the fourth is **the raw-rate refusal**: every `sweep_extraction_successes`
entry must be a whole number in `[0, n]`, and the message names the migration mistake — a caller
porting `sweep_extraction_rates=(3/104, 11/104)` by renaming the keyword hands a RATE to a COUNT
parameter, and at n=104 every fractional `successes` yields a Wilson upper bound under X, so the
axis reads truncated and the route returns a spurious `INCONCLUSIVE` with nothing in the output to
say why. WR-09 closes in this same function and by the same rule as the taught leg (D-35).

### Task 2 — the retention provenance choke point (`02d6683`)

`_prove_retention_floor(*, retention_noise_floor, retention_floor_provenance)` — four `_prove`
calls. The first three mirror `extraction_ceiling`'s at `:417` / `:425` / `:436` one for one:
the provenance is a mapping carrying every key in `RETENTION_FLOOR_PROVENANCE_KEYS`, the regime is
`ADAPTER_REGIME`, and the seeds are at least `EXTRACTION_FLOOR_MIN_SEEDS` distinct values. The
fourth has no counterpart on the extraction leg and is what makes T-20-19's reproduction go red:
`retention_noise_floor != V20_RETENTION_NOISE_FLOOR`, refused **by identity against the imported
constant** so a caller that lies about `regime` is still caught by the number.

The three numbers those refusals publish are **derived, never typed**:

| Published | Derivation | Value |
|---|---|---|
| governing cap | `mitigation_gate.retention_cap(retention_noise_floor=0.008681618994239138)` | `3.9085032379884783` |
| borrowed cap | `mitigation_gate.retention_cap(retention_noise_floor=V20_RETENTION_NOISE_FLOOR)` | `4.029` |
| ratio | `V20_RETENTION_NOISE_FLOOR / 0.008681618994239138` | `7.939763314393305` |

The measured adapter-regime floor is the module's one float literal, module-private, carrying
`results/phase20_retention_floor.json::retention_ppl_noise_floor` in the comment beside it. Nothing
reads it as a default — `retention_cap`'s floor stays a required keyword argument with no fallback
(D-07).

`EXTRACTION_FLOOR_MIN_SEEDS` is REUSED by import rather than retyped, and the reuse is proved
STRUCTURALLY because an identity check on it would be vacuous: it is the small int `2`, CPython
interns it, and a retyped `EXTRACTION_FLOOR_MIN_SEEDS = 2` satisfies `is` identically. The AST check
in the plan's verify block is what bites — the name must appear in a `from mitigation_gate import`
alias list and in NO module-scope `ast.Assign` target.

`SUPERSEDED_GATE06_BLOCK = "scripts/mitigation_gate.py:798-812"` and
`SUPERSEDED_SWEEP_SENTINEL = (0.0, 1.0)` land here, with the sentinel's bracketing justification
written at its definition rather than four functions away: `0.0` is at-or-below and `1.0` is above
any `X` in `(0, 1)`; `1.0` is at-or-above and `0.0` is below any `Y` in `(0, 1]` — exactly the
preconditions Task 3's `_prove` calls establish before the sentinel is ever passed.

### Task 3 — the sanctioned route (`21387a3`)

`corrected_point_verdict` — 24 keyword-only parameters, zero defaults, zero positional, no
`**kwargs`, and NO `sweep_extraction_rates`. Verified by `inspect.signature`. Body order:

1. `_prove_retention_floor(...)` — first, before any compute.
2. `_prove(extraction_noise_floor >= 0, ...)` — WR-08, **before** `extraction_ceiling` is called.
3. `mitigation_gate.extraction_ceiling(...)` for X (so the pin's own three provenance `_prove`s fire
   on this path and no second copy of X exists), then `y_taught` / `y_heldout` from the imported
   `F_Y`.
4. The two sentinel preconditions on `ceiling` and both `y` legs.
5. `coverage_verdict(...)`.
6. `mitigation_gate.mitigation_point_verdict(...)` ONCE, all 21 forwarded, with
   `SUPERSEDED_SWEEP_SENTINEL` on both sweep parameters.
7. `INCONCLUSIVE` with the corrected GATE-06 reason appended when `covered` is false; otherwise the
   pin's 3-tuple unchanged.

**The step-2 ordering is the check, not an implementation detail.** Measured at n=104 with a clean
`never-taught` provenance: `extraction_noise_floor = -0.01` still yields a POSITIVE ceiling
`0.005355228664941234`, so a sign check placed after step 3 fires with the right message — but
`-0.05` yields `-0.07464477133505877`, step 4's `0.0 < ceiling < 1.0` refusal pre-empts it, and the
caller is told the ceiling is out of range rather than that their floor is negative. Both magnitudes
now raise `SystemExit` naming `extraction_noise_floor` and the word NEGATIVE.

Both divergences from the pin's contract are named in the docstring, each STRICTER and neither an
edit: the GATE-05 two-element reason list (the pin's one-element guarantee at `:1310` still holds
FOR THE PIN), and the pre-GATE-05 floor refusals (D-14(b)'s ordering — no path to a verdict computes
X from an unlabelled floor).

The module docstring names the enforcement so the choke point and its guard read together: the AST
caller census at plan `20-11`, `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module`.
**Measured green today**: the only five non-test call sites of `mitigation_point_verdict` are all
inside `mitigation_gate.py`'s own `__main__` self-check (`:1291`, `:1295`, `:1301`, `:1317`,
`:1326`), excluded BY NAME in `tests/test_phase19_erasure.py`'s exclude-the-successor register
rather than by lowering a count.

## Verification

All three plan-supplied automated checks exited `OK`. The behavioural table, measured through
`corrected_point_verdict` against the committed fixtures:

| Case | Sweep | Pin | This route |
|---|---|---|---|
| `FIXTURE_CLEARING_POINT` — direction (i) | `(1, 3)` / `(104, 104)` | `INCONCLUSIVE` | **`PASS`** |
| `FIXTURE_DESTROYED_MODEL` — direction (ii) | `(3, 11)` / `(104, 104)` | `FAIL` | **`INCONCLUSIVE`** |
| `FIXTURE_CLEARING_POINT` — the third, unreported case | `(3, 11)` / `(104, 104)` | `PASS` | **`INCONCLUSIVE`** |
| `FIXTURE_CLEARING_POINT`, `sweep_heldout_recalls=(0.30, 0.28)` | `(1, 3)` / `(104, 104)` | (no parameter) | **`INCONCLUSIVE`** |

Refusals, all through the route rather than only against the helper:

| Input | Outcome |
|---|---|
| `retention_noise_floor=0.06893` under a valid adapter provenance | `SystemExit`, message carries `7.939763314393305`, `4.029`, `3.9085032379884783` |
| `extraction_noise_floor=-0.01` and `-0.05` | `SystemExit` naming the floor's SIGN, not the ceiling's range |
| `sweep_extraction_successes=(3/104, 11/104)` | `SystemExit` naming both RATE and COUNT |
| provenance `{}` / missing `regime` / `regime="full-finetune"` / `seeds=(1337,)` / `seeds=(1337,1337)` | `SystemExit` each; the valid two-seed adapter call is the positive control and returns |

Bound sanity, EXACT comparison with no tolerance anywhere:
`wilson_lower_bound(k, 104) <= k/104 <= wilson_upper_bound(k, 104)` for all 105 outcomes, and
`wilson_lower_bound(0, n) == 0.0` for every `n` in `2..400` — a span containing the measured
cancelling denominators `11`, `104` and `208`.

Plan-level checks:

| Check | Result |
|---|---|
| `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` | exit 0, after every one of the three task commits AND against `321e4a4` (pre-plan HEAD) |
| `.venv/bin/python -m pytest tests/test_phase20_prereg.py -q` | `18 passed in 1.35s` |
| `ruff check .` / `ruff format --check .` | `All checks passed!` / `175 files already formatted` |
| `.venv/bin/python -m pytest -q` | `863 passed, 1 skipped in 197.09s` — the `20-REVIEW.md` baseline exactly |

## Task Commits

| Task | Commit | Files |
|---|---|---|
| 1 — corrected coverage + bound-direction resolution | `eed1667` | `scripts/phase20_gate_coverage.py` |
| 2 — retention choke point + supersession constants | `02d6683` | `scripts/phase20_gate_coverage.py` |
| 3 — `corrected_point_verdict`, the sanctioned route | `21387a3` | `scripts/phase20_gate_coverage.py` |

## Deviations from Plan

Two recorded, both trivial and neither semantic.

**1. [Rule 2 — recorded, not fixed] `COVERAGE_STATISTIC_BY_AXIS` is a tuple of triples, and the
plan's parenthetical about its shape is wrong.** The plan says "This is the shape
`mitigation_gate.CHOSEN_CONSTANTS` uses"; `CHOSEN_CONSTANTS` is in fact a two-key **dict**
(`{"F_Y": F_Y, "F_C": F_C}`, `mitigation_gate.py:221`). The plan's own action text and its verify
block both prescribe a tuple of `(axis, statistic, criterion_site)` triples, and a per-axis
resolution needs the third field, so the tuple was implemented and the false shape claim was simply
not repeated in the module. Resolved from the code rather than from the prose.

**2. Ruff `F401` is red at the intermediate commits `eed1667` and `02d6683`, green at the plan
boundary.** Task 1's action text prescribes importing all five names up front, but `F_Y` is not
consumed until Task 3 and `MARGIN_K` / `V20_RETENTION_NOISE_FLOOR` / `EXTRACTION_FLOOR_MIN_SEEDS`
not until Task 2. The imports were kept where the plan put them rather than shuffled per task, for
one reason that cannot be worked around: Task 2's own AST verify block REQUIRES `F_Y` to be in the
`from mitigation_gate import ...` alias list at Task 2, one task before its first use — so no task
ordering makes every intermediate commit `F401`-clean. Recorded here rather than hidden.
`ruff check .` passes at `21387a3` and there are no pre-commit hooks, so nothing was bypassed.

Two things worth recording that are *not* deviations:

1. **`requirements.mark-complete` was deliberately NOT run** for the plan's
   `requirements: [GATE-06, GATE-02]`. Neither is discharged by this plan: GATE-06 belongs to
   `20-12` and closes only after `20-11`'s tripwire has been watched RED-then-GREEN, and GATE-02 was
   already `[x]` and amended at `20-09`. `STATE.md` and `ROADMAP.md` were hand-edited for the
   separate reason that this repo has six recorded instances of `state.*` / `roadmap.*` handlers
   corrupting planning frontmatter. Seventh consecutive session treating them as unsafe.
2. **Every measured number in `<measured_ground_truth>` was re-derived before being written into a
   docstring**, not transcribed. All of them reproduced exactly, including the 75 / 20 / 55 residue
   census and `retention_cap(0.06893) == 4.029`.

## Threat Model Outcomes

| Threat ID | Disposition | Outcome |
|---|---|---|
| T-20-21 | mitigate | MECHANISM SHIPPED, threat still OPEN by design. `coverage_verdict` decides extraction on `wilson_upper_bound(k, n)` and decides BOTH Y legs; the raw-rate refusal names the migration mistake. Closure requires `20-11`'s tripwire watched RED-then-GREEN on both directions. |
| T-20-19 | mitigate | MECHANISM SHIPPED, threat still OPEN. `_prove_retention_floor` supplies the choke point the frozen `retention_cap` cannot be given, called FIRST in `corrected_point_verdict` so no path through this module reaches a verdict skipping it. Every refusal case and the positive control were exercised; standing enforcement is `20-11`'s. |
| T-20-48 | mitigate | Enforcement NAMED and measured green — zero non-test callers of `mitigation_point_verdict` outside the pin's own `__main__`. The census that keeps it green is `20-11`'s; today's greenness is a recorded state, not a skip. |
| T-20-50 | mitigate | The sentinel is passed only behind `_prove(0.0 < ceiling < 1.0)` and `_prove(0.0 < y_taught <= 1.0 and 0.0 < y_heldout <= 1.0)`, and coverage is decided BEFORE the pin is called at all, so a truncation returns INCONCLUSIVE regardless of what the pin says. `20-11` asserts the neutralisation on every committed fixture. |
| T-20-53 | mitigate | `wilson_upper_bound` asserted `is`-identical across all three modules. `F_Y`, `MARGIN_K`, `V20_RETENTION_NOISE_FLOOR` and `EXTRACTION_FLOOR_MIN_SEEDS` imported and proved unassigned by AST. X is obtained by CALLING `extraction_ceiling`, never recomputed. `wilson_lower_bound`'s short-circuit is a declared, docstring-justified divergence returning the analytic value — inside the discipline, not an exception. |
| T-20-54 | accept | Honoured as accepted. `wilson_lower_bound` is defined for REPORTING only and is read by nothing in this module; `COVERAGE_STATISTIC_BY_AXIS` names the deciding statistic per axis so a future misuse is contradicted by module data. |

## Threat Flags

None. No network surface, no endpoints, no schema, no file I/O, no trust-boundary change — one
CPU-only stdlib module that reads its inputs from its own keyword arguments.

## Known Stubs

None. Every function this plan promised computes; nothing returns a placeholder.

## Notes for Future Plans

- **`20-10` has its module data.** `SUPERSEDED_GATE06_BLOCK`, `SUPERSEDED_SWEEP_SENTINEL` and
  `COVERAGE_STATISTIC_BY_AXIS` are importable values, so the `governs` / `supersedes` artifact reads
  them rather than retyping them. The four measured verdict rows in this SUMMARY's Verification
  table are the artifact's content.
- **`20-11` inherits TWO named test names it must honour**, because this module's docstrings already
  cite them: `tests/test_phase20_correction.py::test_wilson_bounds_are_exact_mirrors` (cited in
  `wilson_lower_bound.__doc__`) and
  `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module`
  (cited in the module docstring and in `corrected_point_verdict.__doc__`). A shipped module citing
  a test that never gets written is the T-20-55 defect class. If a name must change, the DOCSTRING
  moves — it is the one editable half.
- **The mirror test has a trap.** `test_wilson_bounds_are_exact_mirrors` must NOT assert that
  `wilson_lower_bound` is the algebraic mirror at `successes == 0`; it is not, deliberately, and the
  divergence is documented. Assert the mirror for `successes > 0` and assert the analytic `0.0` at
  `successes == 0` separately, over a denominator span containing `11`, `104` and `208`.
- **`20-12` should not discharge GATE-06 on the strength of this plan.** The mechanism exists;
  nothing has watched it go red. `20-SECURITY.md` stays `threats_open: 2` until `20-11`.

## Self-Check: PASSED

- `scripts/phase20_gate_coverage.py` — FOUND (602 lines)
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-08-SUMMARY.md` — FOUND
- commit `eed1667` — FOUND
- commit `02d6683` — FOUND
- commit `21387a3` — FOUND
- `scripts/mitigation_gate.py`, `scripts/erasure_gate.py` — byte-identical to `321e4a4` (pre-plan HEAD)
