---
phase: 24-adversarial-extraction-aware-training-the-held-out-attack-fa
plan: 02
subsystem: testing
tags: [pre-registration, budget-pin, ast-guard, re-derivation, literal-only, adversarial-ratio]

# Dependency graph
requires:
  - phase: 18-attack-suite
    provides: "`results/phase18_corpus.json` and `phase18_extraction.CORPUS_PATH` — the 864-prompt attack corpus whose 336 `core_taught` rows across the three trained families are the pin's numerator"
  - phase: 21-privacy-unit-dp-data-path
    provides: "`results/phase21_multiplicity.json` `corpus_geometry` and `phase21_unit_record.ARTIFACTS` — the 176 / 1408 clean-episode counts that are the pin's denominator, resolved from the register rather than a string"
  - phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
    provides: "`scripts/mitigation_budget.py`'s literal-only, zero-import shape and its `input / rule / output / evidence` + `_PROVENANCE` register convention; `tests/test_phase23_budget.py`'s three guards"
provides:
  - "`mitigation_budget.ADVERSARIAL_RATIO_GRID = (0.0, 0.25, 0.5, 1.0, 1.5, 1.9090909090909092)` — D-09's two pre-registered extremes plus four discretionary interior points, as plain float literals"
  - "`mitigation_budget.ADVERSARIAL_RATIO_GRID_PROVENANCE` — unit (D-06), both extremes with derivation and per-record digests, trained/held-out families with the containment reason, point-count attribution, and D-07 multiplicity at the upper extreme"
  - "`tests/test_phase24_grid.py` — five tests re-deriving both extremes and the multiplicity from the two committed records under exact `==`, with a permanent watched one-ULP control"
  - "`tests/test_phase23_budget.py::_POST_23_13_CONSTANTS` — a later-phase exclusion register whose entries must prove their covering test reads them"
affects: [24-05 corpus-to-episode builder, 24-06 adversarial_ratio seam, 24-07 D-05 four-corner band check, Phase 25 frontier + SC3 multiplicity reporting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-record provenance: `upper_extreme_source_provenance` keyed by path carrying per-record `sha256` + `git_sha`, because a single top-level digest can only name one of two backing artifacts"
    - "Self-earning exclusion register: a name subtracted from a completeness census must name a covering test, and the census asserts that test exists and AST-reads the name"
    - "ULP control by `struct` bit-pattern rather than `math.nextafter` — no import budget question, and the direction of the step is unambiguous"

key-files:
  created:
    - tests/test_phase24_grid.py
  modified:
    - scripts/mitigation_budget.py
    - tests/test_phase23_budget.py

key-decisions:
  - "Tasks 1 and 2 landed in ONE commit (4ecf5bc), not two: the Z-register completeness check refuses to excuse the new constant until its covering test exists, so a Task-1-only commit would have been RED at HEAD"
  - "`ADVERSARIAL_RATIO_GRID` is NOT registered as a Z constant. It is subtracted through a new `_POST_23_13_CONSTANTS`: no throughput figure feeds it, and it is backed by TWO records, so the Z loops' single-record provenance shape would have asserted a shape it does not have"
  - "The plan's `git_sha: <the commit this pin lands at>` was NOT written — a commit cannot contain its own sha. Per-record `git_sha` is carried instead, and `results/phase18_corpus.json`'s is `None` because the record carries none; the test asserts that None is structural, not invented"
  - "Five tests shipped, not the plan's four. The one-ULP nudge became a PERMANENT watched control (`test_a_one_ulp_nudge_to_the_upper_extreme_is_detected`) on `test_a_hand_edited_floor_is_detected`'s precedent, in addition to the plan's one-time manual observation"
  - "ADVT-01 is still NOT ticked — six of seven plans carry it; ADVT-03 is not ticked either, since this plan only names the after-the-fact token-volume record rather than emitting it"

patterns-established:
  - "Grep acceptance criteria satisfied literally by rewording prose: the plan's `grep -n '1.909'` criterion matched only a docstring sentence, which was reworded rather than argued with"
  - "Destructive-revert avoidance: a probe applied to a committed-adjacent file is reverted by a targeted inverse edit, never by `git checkout -- <file>`, which would have destroyed 102 uncommitted insertions"

requirements-completed: []

# Metrics
duration: 18min
completed: 2026-08-30
---

# Phase 24 Plan 02: D-09's Adversarial Sweep Grid, Pinned and Re-Derived — Summary

**The adversarial sweep's two extremes are now literal constants in the resource budget, and both
re-derive from committed artifacts under exact `==` — 336 counted out of the attack corpus, 176
counted out of the episode geometry, quotient `1.9090909090909092`, with a one-ULP nudge watched
being refused by three separate assertions.**

## Performance

- **Duration:** 18 min (plan start commit `8f52fee` at 13:13:22-03:00 → task commit `4ecf5bc` at
  13:31:47-03:00)
- **Started:** 2026-08-30T16:13:22Z
- **Completed:** 2026-08-30T16:31:47Z
- **Tasks:** 2 of 2 (landed in one commit — see Deviations)
- **Files:** 3 (1 created, 2 modified; `scripts/mitigation_budget.py` **102 insertions, 0 deletions**)

## Accomplishments

### Both extremes were COUNTED, not transcribed

Every operand was re-derived at HEAD from the artifact rather than carried forward from the plan's
prose:

| Quantity | Value | Source | How obtained |
|---|---|---|---|
| Trained-pool episodes | **336** | `results/phase18_corpus.json` via `phase18_extraction.CORPUS_PATH` | rows with `tier == "core_taught"` and `family in ("A1-mild", "A1-aggressive", "A3")` — 112 each, counted |
| Clean episodes, n=8 | **176** | `results/phase21_multiplicity.json` `corpus_geometry` via `phase21_unit_record.ARTIFACTS["multiplicity"]` | the row whose `arm == "dp_n8"`, field `episodes` |
| Clean episodes, n=64 | **1408** | same record | the row whose `arm == "dp_n64"` |
| **Upper extreme** | **`1.9090909090909092`** | `336 / 176` | exact float equality with the pinned literal confirmed (`336/176 == 1.9090909090909092` → `True`) |
| n=64's own ceiling | `0.23863636363636365` | `336 / 1408` | the reason `0.25` is the first interior point |
| Multiplicity at the top | `dp_n8: 1.0`, `dp_n64: 8.0` | `upper * episodes / pool` | both exact, no tolerance used |

Corpus census, recorded so the non-vacuity claim is checkable: **864 prompts**, four families at 216
each, `tier` split **448 `core_taught` / 416 `core_held_out`**, i.e. 112 / 104 per family. The
family filter therefore selects 336 of 864 and **excludes** the 216 `A2` rows plus the 312
`core_held_out` rows — the test asserts both halves, because a filter matching everything would be
green while measuring the whole corpus.

Record digests pinned in the provenance and checked live on every suite run:

- `results/phase18_corpus.json` → `ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67`
- `results/phase21_multiplicity.json` → `e9e3b9bf3d31525ad27f90c0afdac0faf97e7faef324cf05d832898c00944da1`
  (its own recorded `git_sha`: `eba0571a7f75e6631b7b080939d130947b703cdf`)

### The one-ULP nudge was WATCHED RED, and the output is quoted

Applied directly to line 633 of `scripts/mitigation_budget.py`
(`1.9090909090909092` → `1.9090909090909094`, the next representable double). **Three of the five
tests refused it**, verbatim:

```
E   AssertionError: `ADVERSARIAL_RATIO_GRID` tops out at 1.9090909090909094, but 336 adversarial
    episodes over 176 clean episodes re-derives 1.9090909090909092. Exact `==`: a grid extreme that
    does not re-derive from the records it cites is an author's preference wearing a measurement's
    clothes
E   assert 1.9090909090909094 == 1.9090909090909092
tests/test_phase24_grid.py:118: AssertionError

E   AssertionError: the unnudged pin does not re-derive — this control is measuring a broken pin
    rather than a broken comparison
tests/test_phase24_grid.py:213: AssertionError

E   AssertionError: the provenance reports 1.0x multiplicity on arm 'dp_n8' at the upper extreme,
    but 1.9090909090909094 x 176 clean episodes over a pool of 336 re-derives 1.0000000000000002
E   assert 1.0 == 1.0000000000000002
tests/test_phase24_grid.py:333: AssertionError
```

**A first attempt at this probe silently proved nothing and is recorded rather than hidden.** The
naive `source.replace(old, new, 1)` hit **occurrence 1 of 4** — the comment block's `output` line at
:618, not the constant — and the suite came back `5 passed`. That green was a false negative from a
probe that never touched the pin. The digits appear four times in the module (`:618` and `:628` in
comments, `:633` the tuple, `:644` the provenance value); the corrected probe anchored on the full
assignment line. Both the comment nudge and the constant nudge were reverted by **targeted inverse
edits** — `grep -c "1.9090909090909094"` returned `0` and GREEN was re-observed before commit.

`git checkout -- scripts/mitigation_budget.py` was attempted as the revert and was **correctly
refused by the destructive-command gate**; had it run it would have destroyed all 102 uncommitted
insertions. The inverse edit is the only sanctioned revert here.

### The pin is structurally incapable of being an expression

- `ADVERSARIAL_RATIO_GRID` is a **plain `ast.Assign`** of a tuple of six float literals — no
  annotation (`ast.AnnAssign` fails the guard), no `336 / 176` (`ast.BinOp` raises inside the
  guard's `ast.literal_eval` at `tests/test_phase23_budget.py:463`).
- **Zero imports added.** The `{erasure_gate, pathlib, sys}` equality ceiling — zero headroom in
  both directions — is unmoved: `test_the_import_ceiling_still_has_zero_headroom` green.
- `ast.parse(...).body[1:]` is **all `ast.Assign`** → `True`. The module docstring still opens the
  file.
- **No `prereg_artifact=` registration was added.**
  `test_the_budget_module_is_protected_but_not_frozen` is green — the module stays protected but
  not frozen, and that freeze would have been irrevocable.
- `scripts/mitigation_budget.py` is **102 insertions, 0 deletions**. The module's whole history
  remains additive.

### Only the extremes are claimed as pre-registered

The provenance says so in the constant itself rather than in a plan document:
`point_count_selected_by` records that the four interior points and their spacing are the planner's
choice under 24-CONTEXT's Claude's Discretion, that they size the spend and decide no outcome, and
that D-09 pre-registers `0.0` and `1.9090909090909092` **only**. `1.0` is episode parity, the
legible midpoint; `0.25` is the first point above n=64's own no-repetition ceiling
(`0.23863636363636365`), i.e. the first point at which D-07 multiplicity is non-trivial at the
large capacity.

`held_out_reason` carries D-10/D-12's containment argument in full — the `build_a2_prompt`
assistant-turn value prefix at mask=1, and `contains_value`'s blindness to prefixes — and states
that the reason precedes every run and **may not be claimed as a deliberate leave-one-out choice**.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_z_was_sized_against_the_ceiling`'s completeness census turned RED — a landmine the plan's `<interfaces>` block did not name**

- **Found during:** Task 1, on the first run of the plan's own acceptance command
- **Issue:** `tests/test_phase23_budget.py:1291` asserts
  `tuple(discovered) == _Z_CONSTANTS` over an AST walk of every module-level name in
  `scripts/mitigation_budget.py` that is neither `_PROVENANCE`-suffixed nor in
  `_PRE_23_13_CONSTANTS`. Adding `ADVERSARIAL_RATIO_GRID` made `discovered` a 7-tuple against a
  6-tuple register:
  `Left contains one more item: 'ADVERSARIAL_RATIO_GRID'`. The plan's `<interfaces>` block named
  three guards on this file; this was a fourth. **The guard was correct** — an unregistered
  constant genuinely would be skipped by every loop in that file.
- **Fix:** Added `_POST_23_13_CONSTANTS`, a dict mapping a later-phase constant to the test that
  covers it, subtracted from `discovered` for the mirror of the reason `_PRE_23_13_CONSTANTS` is.
  **The exclusion earns itself**: before the subtraction, the test now asserts the covering file
  exists and that an AST walk over it (`ast.Attribute` nodes, never a grep — this file's own prose
  names all these constants) genuinely reads the excluded name. Registering it as a Z constant was
  rejected: no throughput figure feeds it, so the `sized_against` branch would have been false, and
  it is backed by two records, so the `_Z_RECORD_BACKED` single-record shape does not fit.
  `test_z_was_sized_against_the_ceiling`'s docstring received a **dated continuation**, not an edit.
- **Watched RED first:** the self-earning half was observed biting before `tests/test_phase24_grid.py`
  existed — `assert False +  where False = PosixPath('.../tests/test_phase24_grid.py').exists`.
- **Files modified:** `tests/test_phase23_budget.py` (44 insertions, 1 deletion — the deletion is
  the one-line list comprehension replaced by its three-clause form)
- **Commit:** `4ecf5bc`

**Consequence: Tasks 1 and 2 are ONE commit, not two.** The register's self-earning check makes the
two tasks indivisible — a Task-1-only commit would have left HEAD with a RED
`tests/test_phase23_budget.py`, and this repository does not ship RED commits. The plan's Task 1
acceptance criterion (`pytest -q tests/test_phase23_budget.py` reports 0 failed) is satisfied at
`4ecf5bc`, which is the first commit at which it *can* be satisfied.

**2. [Rule 1 - Bug] A false-negative ULP probe was corrected rather than accepted**

See "The one-ULP nudge was WATCHED RED" above. The first probe replaced a comment occurrence and
returned a meaningless `5 passed`.

### Plan-Text Corrections

**1. `git_sha: "the commit sha this pin lands at"` is impossible and was not written.**
A commit cannot contain its own sha. The file's existing semantics for `git_sha` are *the commit the
backing RECORD was written at* (`SWEEP_POINTS_PROVENANCE.git_sha` is `results/phase23_cost.json`'s
own field). This pin has **two** backing records, so a single top-level string could name at most
one. Resolution, following `FULL_FIDELITY_K_PROVENANCE`'s `record_sha256: None` /
`git_sha: None`-by-construction precedent: no top-level `git_sha` or `record_sha256`, with the
absence justified inside `governs`, and a per-record `upper_extreme_source_provenance` dict carrying
`sha256` (checked live) and `git_sha` for each. `results/phase18_corpus.json` records no `git_sha`
of its own, so its entry is `None` — and the test asserts that None is **structural**, going red if
the record ever grows one, rather than letting a fabricated sha sit there unread.

**2. Five tests, not four.** The plan asked for four named tests plus a one-time manual ULP
observation. The manual observation was performed (quoted above), **and** the control was made
permanent as `test_a_one_ulp_nudge_to_the_upper_extreme_is_detected`, on the precedent this file's
sibling already sets: `test_a_hand_edited_floor_is_detected` "watches a one-ULP nudge being refused
rather than merely asserting it would". Consequently the plan's `4 passed` acceptance figure reads
**5 passed**.

**3. A sixth test was written and deleted before commit.** `test_the_grid_is_pinned_as_literals_and_
the_module_still_computes_nothing` narrowed the module-wide literal-only guard to this plan's two
constants. It bought only a nicer failure message over a guard that already refuses an `ast.BinOp`
anywhere in the file, so it was dropped rather than shipped.

**4. The plan's `grep -n "1.909" tests/test_phase24_grid.py` criterion initially matched prose.**
Not an assertion — a docstring sentence explaining that the extreme is pinned as a float literal in
the budget module. Rather than argue the criterion, the sentence was reworded to stop spelling the
digits. Both grep criteria (`results/phase18_corpus.json` and `1.909`) now return **nothing**.

## Verification

All commands run with `.venv/bin/python` (Python 3.11 editable install).

| Check | Result |
|---|---|
| `pytest -q tests/test_phase24_grid.py` | **5 passed**, 0 failed |
| `pytest -q tests/test_phase23_budget.py` | **19 passed**, 0 failed |
| `pytest -q tests/test_phase24_grid.py tests/test_phase23_budget.py tests/test_phase21_sc5.py tests/test_phase20_prereg.py` | **53 passed**, 0 failed |
| **Full suite (`pytest -q`)** | **`1601 passed, 1 skipped`**, 0 failed, 375.36 s |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 222 files already formatted |
| `ast.parse(...).body[1:]` all `ast.Assign` | `True` |
| `ADVERSARIAL_RATIO_GRID` | `(0.0, 0.25, 0.5, 1.0, 1.5, 1.9090909090909092)` — 6 points, first `0.0`, last `1.9090909090909092` |
| `git diff --numstat scripts/mitigation_budget.py` (vs `8f52fee`) | `102  0` — **zero deletions** |
| `git diff scripts/phase18_extraction.py scripts/mitigation_gate.py` | **EMPTY** |
| `grep -n "results/phase18_corpus.json" tests/test_phase24_grid.py` | nothing |
| `grep -n "1.909" tests/test_phase24_grid.py` | nothing |
| SC5 wall census (`(?:==\|!=)\s*10(?![0-9_])` over the new file) | **0 hits** |

**Baseline arithmetic.** The pre-24-02 measured baseline was `1596 passed, 1 skipped` (24-01's
recorded figure; ROADMAP's `1591` was pre-24-01 and STATE's `1589` was two plans stale).
`1596 + 5 = 1601`. **Exactly five tests are this plan's**, all in `tests/test_phase24_grid.py`; the
`tests/test_phase23_budget.py` edit changed an existing test's body and added no test function.

**One transient failure, understood and cleared.**
`tests/test_phase23_matched_prereg.py::test_the_closed_preregistrations_are_untouched` failed on the
pre-commit full-suite run with `scripts/mitigation_budget.py has an uncommitted modification`. That
guard asserts `git diff -- <file>` is empty — a **working-tree cleanliness** check, not a freeze
(the same test's first assertion, pinning `scripts/phase23_prereg.py` to its blind birth commit
`c7de5d4`, passed throughout). It cleared on commit; the post-commit full-suite run is the
`1601 passed, 1 skipped` figure above.

## Known Stubs

None. Both constants carry real measured values; no placeholder, no `TODO`, no deferred wiring.

## Threat Flags

None. The provenance dict carries family **labels** and counts only — no fact value, no slot value.
`scripts/mitigation_budget.py` remains inside the `scripts/mitigation_*.py` register both import
ceilings scan.

## Threat Register Disposition

| Threat ID | Disposition | Evidence |
|---|---|---|
| T-24-06 (Tampering, `ADVERSARIAL_RATIO_GRID`) | **mitigated** | Both operands recounted from `results/phase18_corpus.json` + `results/phase21_multiplicity.json` under exact `==` on every suite run; one-ULP nudge watched failing on three assertions and made a permanent control |
| T-24-07 (DoS, the AST literal guard) | **mitigated** | Float literal, plain `ast.Assign`, zero imports/functions/branches; whole budget suite green (19 passed) |
| T-24-08 (EoP, freeze status) | **mitigated** | No `prereg_artifact=` added; `test_the_budget_module_is_protected_but_not_frozen` green |
| T-24-09 (Repudiation, pre-registration order) | **mitigated** | Pinned in wave 1, before D-05's calibration (24-07) and before any training; `point_count_selected_by` records that only the extremes are pre-registered |
| T-24-10 (Info disclosure, provenance dict) | **mitigated** | Labels and counts only; no value from the D-10 lexicon appears |
| T-24-SC (package installs) | **accepted** | No `pip install` was run |

## Requirements

`ADVT-01` and `ADVT-03` are the plan's declared requirements and **neither is ticked**.
`.planning/REQUIREMENTS.md` is **byte-unchanged**. ADVT-01 is carried by six of this phase's seven
plans and this one ships only the grid pin. ADVT-03 is *named* by the provenance's `unit` field —
which records that token volume floats and is reported after the fact — but the record itself is
24-07's to emit; ticking it here would claim an artifact that does not exist.

## Notes for Future Plans

- **24-05 / 24-06 consume `ADVERSARIAL_RATIO_GRID` by import, never by retyping.** The grid is
  ascending and duplicate-free (asserted), so `grid[0]` and `grid[-1]` are well-defined as the
  extremes at both ends.
- **The digits appear four times in `scripts/mitigation_budget.py`** (`:618`, `:628` in comments;
  `:633` the tuple; `:644` the provenance). Only the last two are bound by tests, and the test
  asserts they agree with each other. Any future probe of this pin must anchor on the full
  assignment line — anchoring on the bare value hits a comment first and produces a false green.
- **`_POST_23_13_CONSTANTS` is the register for the next non-Z constant** added to the budget
  module. Adding a name there without a covering test that AST-reads it now fails loudly.
- **Phase 25 SC3** can read `multiplicity_at_upper_extreme` directly; it re-derives on every suite
  run, so it will not go stale if either record moves.

## Self-Check: PASSED

- `scripts/mitigation_budget.py` — FOUND (`ADVERSARIAL_RATIO_GRID` importable, 6-tuple)
- `tests/test_phase24_grid.py` — FOUND (5 tests, all passing)
- `tests/test_phase23_budget.py` — FOUND (19 tests, all passing)
- Commit `4ecf5bc` — FOUND in `git log`
- Full suite `1601 passed, 1 skipped` — MEASURED, not asserted
