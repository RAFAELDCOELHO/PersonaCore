---
phase: 19-selective-memory-erasure
plan: 03
subsystem: testing
tags: [pre-registration, blind-calibration, floor, wilson, reachability, d2, w1, b4, erase-01, stat-02, stat-05]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-01's open pin (`scripts/phase19_erasure.py`) and its ARMED git-ancestry guard"
  - phase: 19-selective-memory-erasure
    provides: "19-02's `N_TARGET_QUESTIONS = 27` and `BEST_ATTAINABLE_TARGET_BOUND` — the reachability ceiling this plan had to live inside"
  - phase: 14-persona-teaching
    provides: "`THRESHOLD_DISCOUNT = 0.60` / `THRESHOLD_FLOOR = 0.20` and `lock_thresholds` (`d7d7917`), the operator being mirrored"
provides:
  - "ERASURE_FLOOR_RULE (5 clauses) + FLOOR_DISCOUNT / FLOOR_CEILING / FLOOR_GRID / FLOOR_SWEEP_STEPS"
  - "lock_erasure_floor() — the mirrored operator; literal_phase14_floor() — the unmirrored one, for side-by-side publication (D2)"
  - "floor_branch() — which of reachability-min / discount / ceiling bound"
  - "ERASURE_FLOOR_MIN — the reachability clamp, computed by the committed wilson_upper_bound, unrounded"
  - "assert_erasure_floor_reachable() called at MODULE SCOPE — importing the pin runs the proof"
  - "floor_sweep() — the closed-unit-interval grid every floor proof runs over"
  - "a `--floor` self-check mode printing both directions, the branch census and the proved bound"
affects: [19-04, 19-05, 19-06, 19-07, 19-09, 19-12, 19-13]

tech-stack:
  added: []
  patterns:
    - "a reachability proof is a pure function CALLED at module scope, so a dead gate fails at import in milliseconds rather than after the compute it would have wasted"
    - "when a committed guard forbids the plan's prescribed primitive, substitute an equivalent and PROVE the equivalence against an oracle in the test — never amend the guard to fit new code"
    - "a residual a rule cannot eliminate is BOUNDED and recorded in the rule text, never claimed away with a stronger sentence that would be unamendable"

key-files:
  created: []
  modified:
    - scripts/phase19_erasure.py
    - tests/test_phase19_erasure.py

key-decisions:
  - "`int()` replaces the plan's prescribed `math.floor` — 19-02 committed a guard forbidding `import math` in the pin (T-19-08: no sqrt available to re-derive a second Wilson interval). On the proved non-negative domain the two are the same function; measured identical at all 1001 swept rates against a `math.floor` oracle in the test, where math IS allowed"
  - "the rule records `never rounds up by more than one ulp` and NOT `rounds strictly toward the harder side` — the second is false (the division back down by 10000 lands one ulp high at 68 of 1001 rates) and would have been unamendable after 19-07. A test asserts the false sentence is ABSENT"
  - "the unscoped inequality `lock(x) <= x * FLOOR_DISCOUNT` is deliberately NOT asserted; it is red at 161 of 1001 rates for a CORRECT implementation. Measured and decomposed instead — 152 clamp + 9 one-ulp residual, jointly exhaustive"
  - "the crossover prose was corrected from an implied iff to a stated sufficient condition: 0.1518 is the CONTINUOUS crossover, and the four-decimal grid makes the clamp bind a hair beyond it (`floor_branch(0.1518)` is still `reachability-min`)"
  - "the proof's return value is NOT bound to a third module name for the same float — `ERASURE_FLOOR_MIN` is the rule constant, `BEST_ATTAINABLE_TARGET_BOUND` (19-02) its measurement-side twin, and callers that want the priced number call the proof and print what it returns"

patterns-established:
  - "publish BOTH directions of a mirrored operator as runnable output (`--floor`), so a reader sees the choice instead of reconstructing it from prose"
  - "mutate the CONSTANT inside the expression, never wrap the expression's output — a clamp applied to an already-clamped value is a no-op mutation that proves nothing"

requirements-completed: []

duration: 30min
completed: 2026-08-17
---

# Phase 19 Plan 03: The Blind Floor-Derivation Rule And Its Reachability Proof — Summary

**The (a) floor rule is committed blind with D2's mirror stated and both directions publishable
side by side — at a calibration rate of 1.0 the mirrored operator returns 0.20 where Phase 14's
literal operator returns 0.60 — and the floor it can produce is PROVED clearable at n = 27 against
a named attainable outcome by a pure function called at module scope, watched RED under two
mutations and restored byte-identically.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-08-17T23:05Z (local 2026-08-17 20:05 -0300)
- **Completed:** 2026-08-17T23:29:47Z (local 20:29:47 -0300)
- **Tasks:** 2 of 2 (TDD, RED then GREEN each)
- **Files modified:** 2 (0 created, 2 modified)

## Accomplishments

- `ERASURE_FLOOR_RULE` (5 clauses), `FLOOR_DISCOUNT`, `FLOOR_CEILING`, `FLOOR_GRID`,
  `ERASURE_FLOOR_MIN`, `floor_sweep`, `_discounted_floor`, `lock_erasure_floor`,
  `literal_phase14_floor` and `floor_branch` landed in one commit — the plan's requirement that the
  rule state its mirror in the same commit as the code.
- `assert_erasure_floor_reachable` landed with its module-scope call, so importing the pin at all
  runs the proof over the closed unit interval, endpoints proved included.
- 12 new tests, all CPU-only. Two deliberate mutations watched RED, both restored byte-identically.
- `git ls-files 'results/phase19_*'` is still **EMPTY**. No calibration, no ablation, no erasure and
  no Phase 19 artifact has run or been written.

## Task Commits

1. **Task 1 RED** — `31820b1` (test): seven failing tests for the mirrored operator
2. **Task 1 GREEN** — `6969e47` (feat): the rule, the three constants, the three functions
3. **Task 2 RED** — `b1184a8` (test): four failing tests for the import-time proof
4. **Task 2 GREEN** — `48f8ce1` (feat): the proof, its module-scope call, the docstring consequence

## Files Created/Modified

- `scripts/phase19_erasure.py` (modified, 743 → 1020 lines) — the floor section, plus a `--floor`
  self-check mode. Module docstring updated: the "WHAT THIS FILE HOLDS" section now says 19-03, the
  import-time surface now names **three** pure proofs instead of two, and a new RECORDED
  CONSEQUENCE paragraph states that when the clamp binds, (a) clears ONLY on a perfect erasure.
- `tests/test_phase19_erasure.py` (modified, 793 → 1185 lines) — 12 new tests.

## Evidence

### Both directions, side by side — the D2 publication, from the committed self-check

```
$ .venv/bin/python scripts/phase19_erasure.py --floor
[phase19_erasure] mechanism M1-rank1-component-ablation, 5 rule clauses committed
[phase19_erasure] component index: 36 wrapped projections x rank 8 = 288 addressable rank-1 components
[phase19_erasure] floor rule: max(0.091079, min(0.2, floor(cal_rate x 0.6, 4dp)))
[phase19_erasure] clamp binds below cal_rate 0.1518; ceiling saturates at or above 0.3333
[phase19_erasure] cal_rate | mirrored floor | literal Phase 14 floor | branch
    0.0      0.09107873950450847    0.2        reachability-min
    0.1      0.09107873950450847    0.2        reachability-min
    0.1518   0.09107873950450847    0.2        reachability-min
    0.2506   0.1503                 0.2        discount
    0.3333   0.1999                 0.2        discount
    0.4143   0.2                    0.2486     ceiling
    1.0      0.2                    0.6        ceiling
[phase19_erasure] branch census over 1001 swept rates: {'reachability-min': 152, 'discount': 182, 'ceiling': 667}
[phase19_erasure] reachability PROVED at n = 27: best attainable (0 successes, a perfect erasure) = 0.09107873950450847
```

The two rows that matter for D2: at `cal_rate = 1.0` the mirror returns **0.20** and the literal
Phase 14 operator returns **0.60** — a cap three times looser. At the Phase 14 calibration arm's own
measured rates (0.4143 taught / 0.2506 held-out, the B4 *prior*) the mirror returns 0.20 and 0.1503.
The literal operator is never read by any gate; it exists so this table can be printed.

### The plan's own verification commands

```
$ .venv/bin/python -m pytest -q tests/test_phase19_erasure.py tests/test_phase16_prereg.py tests/test_package.py
...........................................                              [100%]
43 passed in 8.45s

$ .venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); import phase19_erasure as p; print(p.ERASURE_FLOOR_MIN, p.assert_erasure_floor_reachable(p.N_TARGET_QUESTIONS, p.lock_erasure_floor))"
0.09107873950450847 0.09107873950450847

$ git ls-files 'results/phase19_*'
(empty)
```

The unrounded bound printed twice, as the plan required: the stored clamp and the value the proof
independently returns are the same double.

### Full-suite verification

```
$ .venv/bin/python -m pytest -q
767 passed, 1 skipped, 83 warnings in 141.03s (0:02:21)

$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
166 files already formatted
```

Baseline was 755 passed / 1 skipped at 19-02; +12 tests, same single pre-existing CUDA-only skip.

### W1's residual, measured rather than asserted

The plan's claim that `math.floor(v * 10000) / 10000` can land ABOVE the exact
quarter-ten-thousandth reproduced exactly, and the bound is **tighter than the plan stated**:

```
worst decimal-sweep excess at x=0.691: stored=0.4146 exact=0.41459999999999997
  excess=5.551115123125783e-17  ulp(stored)=5.551115123125783e-17  in ulps = 1.0
  excess in ULPs over all 68 exceeding rates: max 1.0, min 1.0
```

Every one of the 68 exceeding rates is over by **exactly one ulp** — max and min are both 1.0, never
two. The nine that sit on the `discount` branch, where no clamp masks them, are exactly the nine the
plan named: `0.173, 0.174, 0.177, 0.178, 0.182, 0.186, 0.19, 0.195, 0.207`.

What `round` would have cost instead, measured on **attainable** rates (`k/n` for n in 16..27, the
denominators a calibration fact can actually produce):

```
attainable k/n rates for n in 16..27: 217 distinct
  round(x*0.60,4) exceeds the floored value at 84 of 217 attainable rates;
    max gap 0.00010000000000010001 at x=0.9047619047619048
  round() exceeds the EXACT discounted rate by at most 4.7826086956526126e-05, vs the theoretical 5e-05

worked example x=7/27=0.25925925925925924: x*0.60=0.15555555555555553
  round(.,4)=0.1556   int-floor=0.1555   round is looser by 9.999999999998899e-05
```

So the choice is a residual of one ulp against a residual of up to 5e-05 — eleven orders of
magnitude, in the direction D2 forbids, at 84 of 217 attainable rates.

### Two deliberate mutations, both watched RED, both restored byte-identically

| # | Mutation | Result | Restored |
|---|----------|--------|----------|
| A | `ERASURE_FLOOR_MIN = 0.0` (the plan's prescribed mutation) | **import RAISES** — `PROOF FAILED: a calibration rate of 0.0 produces an (a) floor of 0.0, but the best attainable upper bound over 27 questions ... is 0.09107873950450847` | sha256 `e7a56624…` |
| B | `ERASURE_FLOOR_MIN` one ulp down (`0.09107873950450845`) | **the suite cannot even COLLECT** — pytest exits `INTERNALERROR ... SystemExit` while importing the test module, and `no tests ran` | sha256 `e7a56624…` |

Mutation B is the one worth naming. A one-ulp downward move of the clamp does not fail a test — it
makes the entire suite unable to run, because the proof executes at *import*, not at call. That is
the difference between `assert_holm_family_reachable`'s register and a test someone remembers to
write. Restoration verified: sha256 `e7a566248d8d48139f73f7a96e5abd25f97cdca9172becc3d11edfaa6aa44e6f`
before and after, `git diff --stat` and `git status --short` both empty.

## Deviations from Plan

### 1. [Rule 3 — blocking: the prescribed primitive would redden a committed guard] `int()` replaces `math.floor`

- **Found during:** Task 1, before writing any code.
- **Plan text:** *"Use `math.floor(cal_rate * FLOOR_DISCOUNT * 10000) / 10000` instead"*, repeated in
  the `<behavior>` block as the assertion to make.
- **The conflict:** 19-02 committed
  `test_the_wilson_bound_is_the_committed_one_and_is_never_re_derived`, which walks the pin's AST
  and asserts `"math" not in imported`, with the reason recorded on it: *"a second Wilson interval
  needs a sqrt, and the point of importing the committed one is that there is no second
  implementation to disagree with it"* (T-19-08). Verified live before writing anything — the guard
  is green at HEAD.
- **Resolved as:** `int(cal_rate * FLOOR_DISCOUNT * FLOOR_GRID) / FLOOR_GRID`, with a `_prove` that
  `0.0 <= cal_rate <= 1.0`. On a non-negative argument `int()` and `math.floor()` are the same
  function; off it they diverge (truncate-toward-zero vs floor), which is exactly what the domain
  proof forecloses and why it is load-bearing rather than defensive.
- **Proved, not assumed:** the test file imports `math` (tests are not the pre-registration) and
  `_grid_oracle` computes the discount with the real `math.floor`. Measured: **0 disagreements over
  all 1001 swept rates**, and the oracle is what every branch/value assertion compares against.
- **Why not amend the guard:** amending a committed guard to fit new code is the manoeuvre this
  entire phase exists to forbid. The guard is older than this plan and its reason is still true.
- **Commit:** `6969e47`

### 2. [Rule 1 — a pinned sentence that would not survive checking] the crossover is a sufficient condition, not an iff

- **Found during:** Task 2, by running the `--floor` printer rather than by review.
- **What was written first:** *"BELOW cal_rate = 0.1518 the discounted value falls under the
  reachability clamp"* — in both `ERASURE_FLOOR_RULE` clause 4 and the module docstring.
- **What the measurement says:** `floor_branch(0.1518)` is still `reachability-min`. 0.1518 is the
  CONTINUOUS crossover `ERASURE_FLOOR_MIN / FLOOR_DISCOUNT`; because the discount snaps DOWN to the
  four-decimal grid, the clamp keeps binding a hair beyond it. The sentence is true as an
  implication and false as the iff a reader would take it for.
- **Resolved as:** both sites now state it as a sufficient condition, name it as the continuous
  crossover, and point at `floor_branch` as the committed way to read the boundary instead of
  inferring it from prose. This matters because the file is **unamendable after 19-07** — the same
  standard CONTEXT B4 applied to itself when it refused an unqualified *"deterministic"*.
- **Commit:** `48f8ce1`

### 3. [Clarification] `ERASURE_FLOOR_MIN` landed in Task 1's commit, not Task 2's

- The plan assigns the constant to Task 2's action, but Task 1's `<behavior>` requires
  `lock_erasure_floor` never return below it — the operator cannot be written correctly without it.
  The constant landed with the operator; what Task 2 added is the **proof that the clamp is
  sufficient**, which is the part the plan asked be justified there rather than in Task 1.

### 4. [Clarification] the proof's return value is not bound to a third module-level name

- The plan says the proof returns the bound *"so the report prints the number the phase was actually
  priced at rather than a second copy computed beside it"*. Binding that return to a new constant
  would have created a THIRD name for one float (`ERASURE_FLOOR_MIN`, 19-02's
  `BEST_ATTAINABLE_TARGET_BOUND`, and it). The module-scope call discards the return exactly as
  `phase18_extraction.py:289` does; callers that want the priced number call the proof, which is
  what the plan's own verification command does.

## Findings For Downstream Plans

1. **The floor budget is `[0.091079, 0.20]` and the calibration decides where in it you land.**
   `floor_branch` reports which clamp bound. Below `cal_rate = 0.1518` (and marginally above, by the
   grid) the answer is `reachability-min` and **(a) then clears only on a perfect erasure** — 0
   successes over all 27 questions. 19-06's report must print the branch beside the floor; a floor
   without its branch hides how hard the criterion was.
2. **The ceiling saturates at `cal_rate >= 0.3333`** — 667 of 1001 swept rates land there. If the
   calibration fact scores anywhere near Phase 14's arm (0.4143 / 0.2506) the floor is 0.20, the
   permissive end, at 2.196x the reachability minimum. Recorded before the number exists (B4) so it
   cannot later be presented as either a surprise or a design win.
3. **The floor must be fed a RATE measured by the same adversary at the same budget** (A2 at K = 48).
   `ERASURE_FLOOR_RULE` clause 1 states this as the hard commensurability constraint (P19-4). A rate
   from a 9-draw `score_items` sweep is not the same quantity and the gate would mean nothing —
   19-06's calibration arm has to build its own corpus over calibration facts by IMPORT.
4. **Do not write `import math` into the pin.** It is guarded, the guard's reason is still live, and
   `int()` on a `_prove`d non-negative domain is the committed substitute.
5. **`assert_erasure_floor_reachable(n, floor_fn)` takes the floor function as a parameter**, so
   19-06 can prove any candidate floor reachable before spending compute on it. It sweeps the whole
   closed unit interval and does not assume monotonicity.
6. **`--floor` re-prints every derived number in this plan** (`python scripts/phase19_erasure.py
   --floor`). It calls the same functions the tests call, so the printer and the guard cannot drift.

## Known Stubs

None. Every function this plan added is fully implemented and exercised by a committed test.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. This plan reads no artifact
at all — the whole floor section is pure arithmetic over already-committed constants. No checkpoint
is loaded, no `weights_only` choke point is touched, nothing is written to disk.

## Threat Register Disposition

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-19-09 | mitigate | **Done** — the rule is committed while `git ls-files 'results/phase19_*'` is empty (verified 0 at start and at end), and the ARMED ancestry guard makes a later edit not an ancestor of the artifacts it would be laundering. `ERASURE_FLOOR_RULE` clause 5 records the forbidden move and cites Phase 14's `d7d7917` precedent, asserted present by test. |
| T-19-10 | mitigate | **Done** — `lock_erasure_floor(x) <= literal_phase14_floor(x)` proved across all 1001 swept rates, 0 violations. A `max`-clamped twin is run in the test and returns 0.60 at `cal_rate = 1.0` where the mirror returns 0.20, so the direction is demonstrated rather than asserted. |
| T-19-11 | mitigate | **Done** — `assert_erasure_floor_reachable` at module scope over the closed unit interval, endpoints proved included. Watched RED twice; mutation B stops the suite collecting at all. The failure message names the compute the proof buys out. |
| T-19-12 | mitigate | **Done** — `ERASURE_FLOOR_MIN = wilson_upper_bound(0, N_TARGET_QUESTIONS)`, unrounded, asserted equal to 19-02's `BEST_ATTAINABLE_TARGET_BOUND`. An AST scan requires **zero** float literals within 1e-4 of it anywhere in the pin, so a retyped `0.0911` at any precision reddens. The rounding trap has its own test covering BOTH directions. |
| T-19-SC | mitigate | **Holds** — zero packages installed; `tests/test_package.py` green (`pyproject.toml` sha256 pin unmoved). |

## Verification Against Plan Success Criteria

- [x] The floor-derivation rule is committed blind, with the mirrored operator stated and justified —
      `ERASURE_FLOOR_RULE` clause 2, in the same commit as the operator (`6969e47`).
- [x] Both directions' values are computable and will be published side by side — `--floor` prints
      the table; 0.20 vs 0.60 at `cal_rate = 1.0`.
- [x] Reachability is PROVED at import against a named attainable outcome (0 successes over 27
      questions, a perfect erasure), not assumed from two numbers.
- [x] The proof was watched RED and restored byte-identically — twice, sha256 `e7a56624…` both times.

## Known Defect In This Plan's Own Record

The Task 1 GREEN commit message (`6969e47`) is missing two words. Its deviation paragraph reads
*"a guard forbidding  in this pin"* — zsh command-substituted a backticked `import math` in the
`-m` argument before git saw it. The content of the commit is unaffected (code and tests are
byte-correct). The correction was attempted via `git commit --amend -F <file>` and **denied by the
permission system**; the denial was not routed around, per the 17-07 precedent. The full deviation
is recorded above in this SUMMARY, which is itself a committed artifact, so the audit trail is
complete. Every subsequent commit message in this plan was passed via `-F` to remove the failure
mode entirely.

## Self-Check: PASSED

- `scripts/phase19_erasure.py` — FOUND (modified, 1020 lines)
- `tests/test_phase19_erasure.py` — FOUND (modified, 1185 lines)
- commit `31820b1` — FOUND
- commit `6969e47` — FOUND
- commit `b1184a8` — FOUND
- commit `48f8ce1` — FOUND
- `results/phase19_*` tracked files — 0 (guard intact)
- pin sha256 after both mutations — `e7a566248d8d48139f73f7a96e5abd25f97cdca9172becc3d11edfaa6aa44e6f`, `git diff` empty
