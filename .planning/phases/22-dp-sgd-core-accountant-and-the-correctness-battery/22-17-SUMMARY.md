---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 17
subsystem: privacy
tags: [dp-accountant, float64, subnormal, erfc, asymptotic-series, mutation-testing, mpmath]

requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "22-12's `_log_erfc` — the fast path, the asymptotic series, and the inertness argument this plan re-scopes"
provides:
  - "`_log_erfc` routes on float64's smallest NORMAL, so the erfc-SUBNORMAL band takes the asymptotic series instead of `math.log` of a float that has already lost mantissa bits"
  - "`LOG_ERFC_BAND` — 17 committed 60-dps `log(erfc(x))` truths spanning all three `math.erfc` regimes"
  - "A boundary-parametrized guard: it asserts the route ACTUALLY CHOSEN is accurate, and never names the boundary"
  - "A run-time three-regime non-vacuity companion that the module under test cannot fool"
affects: [22-18, 22-19, phase-23-mitigation-budget]

tech-stack:
  added: []
  patterns:
    - "Route on a FORMAT property (`math.ldexp(1.0, -1022)`), never on a platform libm's measured crossover"
    - "Guard the RESULT of a routing decision, not the predicate — no behavioural route detector, no AST detector"
    - "Non-vacuity by RUN-TIME classification against a third function, so the module under test cannot satisfy its own meta-guard"

key-files:
  created: []
  modified:
    - src/personacore/privacy/accountant.py
    - tests/fixtures/phase22_reference.py
    - tests/test_phase22_accountant.py
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/deferred-items.md

key-decisions:
  - "[Phase 22] `_log_erfc`'s fast path is guarded on `math.ldexp(1.0, -1022)` (float64's smallest normal), NOT on the measured 26.70 crossover — the threshold is a FORMAT property and portable, the crossover is a libm property and would need re-measuring per platform; erring toward the numerically stable route costs one ulp and is bounded, erring the other way is not"
  - "[Phase 22] The band guard asserts a property of the RESULT ('whatever route was chosen, it is accurate here') rather than of the predicate, so it reddens on a boundary move without a locator — a bisection locator is UNSOUND here because 211 of the first 400 floats above the crossing have the two routes bit-identical"
  - "[Phase 22] Three-regime non-vacuity is computed at RUN TIME from `math.erfc`, never hardcoded, so the guard survives a libm change and cannot be satisfied by the module it judges"

patterns-established:
  - "Boundary-parametrized guard: commit a band spanning every regime the router can see, assert the chosen route's accuracy, and pin non-vacuity by run-time regime classification"
  - "Measure a grid by MULTIPLICATION, never by accumulation — an accumulated `x += 0.05` grid produced two retracted figures in this plan's own lineage"

requirements-completed: [DPSGD-03]

duration: ~65min
completed: 2026-08-26
---

# Phase 22 Plan 17: Route the erfc-Subnormal Band Summary

**One predicate change — `erfc(x) > 0.0` to `erfc(x) >= math.ldexp(1.0, -1022)` — drops the
two-oracle gap at the project's own frozen δ from 1.9190e-03 to 1.0152e-11 inside an unwidened 1e-9
budget, and a 17-row band guard now reddens on the NEXT boundary move instead of a verifier finding
it.**

## Performance

- **Duration:** ~65 min wall clock, including two full-suite runs at ~230 s each
- **Tasks:** 3 of 3
- **Files modified:** 4 (1 source, 2 test, 1 planning)
- **Commits:** 4

| Commit | Task | Subject |
|--------|------|---------|
| `5578b59` | 1 | `fix(22-17)`: route the erfc-SUBNORMAL band to the asymptotic series |
| `c5d9473` | 2 | `test(22-17)`: sweep the routing boundary with a committed 60-dps band table |
| `d27a1b6` | 3 | `docs(22-17)`: log the two out-of-scope discoveries found while watching M-H |
| `1f289dd` | 3 | `fix(22-17)`: restore the 157 lines of deferred-items my previous commit destroyed |

---

## The Headline, With Its Denominators

`epsilon_for(0.414, 200, 1e-5)` — T=200 at the frozen δ, the worst reachable point
`22-VERIFICATION.md` measured:

| Quantity | Before (verification) | After (measured here) |
|---|---|---|
| `epsilon_for` | 728.2043182233367 | **728.1896631303155** |
| verifier's independent 60-dps solve | 728.1896631303156 | — (agrees to **1 ulp**) |
| `delta_closed` | 1.0000000000000345e-05 | **1.0000000000000226e-05** |
| `delta_quadrature` | 9.980810076863458e-06 | 9.999999999898711e-06 |
| **two-oracle relative gap** | **1.9190e-03** | **1.0152e-11** |
| budget `test_two_oracles_agree` compares at | 1e-9, **NOT widened** | 1e-9, **NOT widened** |
| margin | 1,919,000x **over** | **98.5x inside** (1e-9 / 1.0152e-11) |

Swept across the whole reachable band σ ∈ [0.4130, 0.4200] step 0.0005 at T=200, every row now has
`erfc(b)` subnormal or exactly zero — i.e. **every row was inside the defective band** — and the
worst two-oracle gap over the 15 rows is **1.0237e-11 at σ=0.4130** (97.7x inside 1e-9). The worst
`delta_closed` error against 80-dps truth over the band is **3.1897e-14**, at σ=0.4135.

**A bonus closure the plan did not ask for.** `22-VERIFICATION.md` filed `ROUND_TRIP_REL_TOL` as a
🛑 Blocker — violated by **2.07e+07x** (2.0703e-05 against 1e-12) at σ=0.414. Measured over the same
15-row sweep after this change: worst **4.0274e-16**, at σ=0.4135. Inside the tolerance by 2483x
(1e-12 / 4.0274e-16). That is a consequence of the fix, not separate work, and it is reported
because the verification named it as an open Blocker.

---

## What Shipped

### Task 1 — the predicate (`5578b59`)

`_SMALLEST_NORMAL = math.ldexp(1.0, -1022)` added beside the module's other measured constants,
verified equal to both `2.2250738585072014e-308` and `sys.float_info.min` in a throwaway
interpreter. `_log_erfc`'s fast path changed from `if e > 0.0:` to `if e >= _SMALLEST_NORMAL:`.
**One behavioural line.** No new import — `grep -n "^import \|^from "` still returns the single
`82:import math`.

Three stale premises corrected, plus a fourth the plan did not list (see Deviations):

1. The opening inertness paragraph — `22-VERIFICATION.md` records it as a 🛑 Blocker-severity
   anti-pattern ("a comment asserts a property as protective that is in fact the failure mode").
   Rewritten to scope inertness to the region where `math.erfc` has lost nothing, with the history
   kept rather than deleted.
2. The `Args:` reachability bound: `x > 27.2` → `x >= 26.54325845425098`, with the bisection.
3. `_delta_or_below_float64`'s fifth-`ValueError` argument: the PREMISE restated against the new
   predicate (`erfc(x) < _SMALLEST_NORMAL`, first at 26.54325845425098) while noting the
   CONCLUSION is unchanged and threshold-independent, since `erfc(x) >= 1.0` for every `x <= 0.0`
   and 1.0 is below no positive threshold.

### Task 2 — the band table and the boundary sweep (`c5d9473`)

`LOG_ERFC_BAND`: 17 `(x, truth_string)` rows, `x` a float literal and the truth 20 significant
decimal digits. Derived by ONE invocation whose output is committed as data, with the invocation
and the `mp.mpf` input form both in the provenance block. Fixture still passes
`test_reference_fixture_imports_nothing` (zero imports, zero executable logic) and
`test_no_phase22_test_imports_mpmath`.

`test_log_erfc_band_routes_accurately` — 17 node ids. Asserts a property of the RESULT
(`_log_erfc(x)` agrees with the committed truth to 1e-15 relative), never of the predicate.
**No boundary locator, by design** — see Deviations for the measurement that kills the obvious one.

`test_log_erfc_band_spans_all_three_erfc_regimes` — 1 node id. Classifies every row by calling
`math.erfc` AT RUN TIME and requires all three regimes non-empty, with the three counts in the
message. The split is **not** hardcoded; on this box it is **4 normal / 9 subnormal / 4
exactly-zero**, summing to the 17 committed rows.

### Task 3 — the mutation watch (`d27a1b6`, `1f289dd`)

Produces evidence, not a code change. See the register below.

---

## Measurements: What Reproduced and What Did Not

The plan said *"Do not transcribe the figures below; reproduce them"* and *"If any does not
reproduce, report the divergence rather than smoothing it."* Nine reproduced; **seven did not.**

### Reproduced

| Claim | Plan / brief | Measured here |
|---|---|---|
| First x with `erfc` SUBNORMAL | 26.54325845425098 | **26.54325845425098** (prev float's erfc 2.2250738585076065e-308, normal) |
| First x with `erfc` exactly 0.0 | 27.2 | **27.2** |
| Band width | 0.657 | **0.6567415457490178** |
| **SHIPPED** worst chosen-route rel err | 1.2369e-05 at x=27.15 | **1.2369e-05 at x=27.15** |
| **Candidate EQUALS the perfect-routing floor** | equal → no third blind band | **equal** (2.0621e-16 both, at x=26.95) |
| Bit-identical routes, first 400 floats | 211 of 400 | **211 of 400** |
| Large-x tail, series vs 120-dps | 5.812e-17 at x=1e6 | **5.8118e-17 at x=1e6** |
| Band worst under M-H | 1.591e-04 at x=27.19 | **1.5906e-04 at x=27.19** |
| Regime split over 17 rows | 4 / 9 / 4 | **4 / 9 / 4** |

The load-bearing claim — *the candidate equals the theoretical floor for any routing rule, so no
third blind band is opened* — **reproduces**. Over x ∈ [20, 30] step 0.05 at `mp.dps = 120`:

```
SHIPPED   (e > 0.0)        worst chosen-route rel err: 1.2369e-5  at x=27.15
CANDIDATE (e >= DBL_MIN)   worst chosen-route rel err: 2.0621e-16 at x=26.95
PERFECT routing (floor)    worst chosen-route rel err: 2.0621e-16 at x=26.95
candidate == floor? True
```

### Diverged — seven findings

**D-1. The candidate's worst is 2.0621e-16, not 1.7586e-16.** Same x (26.95), different value.
**Cause: the grid.** The planning sweep accumulated `x += 0.05` from 20.0, so its "26.95" was
`26.950000000000102`; mine multiplies (`20.0 + k*0.05`) and lands on 26.95 exactly. This is the
same grid artifact the plan itself retracts for the sliver figures. **The conclusion is unchanged**
— candidate == floor on each grid independently — but the number is grid-dependent at the 1-ulp
level and should not be transcribed between grids.

**D-2. The crossover is 26.70 only under the STRICT definition; it is 26.55 under the non-strict
one, and the plan does not say which it used.** Measured:

```
crossover, S <= L from here on (non-strict): x = 26.55
crossover, S <  L from here on (STRICT)    : x = 26.70
```

The gap is three exact TIES — at x ∈ {26.55, 26.60, 26.65} the two routes return bit-identical
floats, so `rel_S == rel_L` and "overtakes" depends entirely on whether ties count. Per-row:

| x | regime | rel route L | rel route S | better |
|---|---|---|---|---|
| 26.50 | normal | 6.5758e-17 | 9.5249e-17 | L |
| 26.55 | subnormal | 6.2563e-17 | 6.2563e-17 | **tie** |
| 26.60 | subnormal | 1.2195e-17 | 1.2195e-17 | **tie** |
| 26.65 | subnormal | 6.2621e-18 | 6.2621e-18 | **tie** |
| 26.70 | subnormal | 4.5398e-16 | 2.1865e-17 | S |
| 26.90 | subnormal | 1.6702e-11 | 4.5196e-17 | S |
| 27.15 | subnormal | 1.2369e-05 | 7.0867e-17 | S |
| 27.20 | ZERO | n/a | 7.2865e-17 | S |

**D-3. The plan's replacement sliver claim is FALSE, and it contradicts the plan's own Task 2.**
Step 4 states *"`series(x)` and `math.log(math.erfc(x))` are BIT-IDENTICAL at every point in the
sliver — a 1.0x ratio, not 29x."* Measured on three grids:

| Grid | n | bit-identical | max ulp gap where they differ |
|---|---|---|---|
| clean 0.005 steps | 32 | 18 / 32 | 2 |
| 400 consecutive floats from the boundary | 400 | **211 / 400** | 1 |
| 2000 uniform samples | 2000 | 1191 / 2000 | 5 |

So 40–47% of sampled points **differ**. The plan's own Task 2 Step 0 says *"211 of the first 400
floats above the real crossing have `series(x) == math.log(math.erfc(x))` bit-for-bit"* — which
means 189 of 400 do **not**, directly contradicting Step 4. The retraction of the "~29x" figure was
correct; **the replacement figure was also wrong**, in the opposite direction. My committed comment
carries the measured 211/400 and the 1–5 ulp gap, and nothing from Step 4.

**What the sliver actually costs, apples-to-apples on each grid** (chosen route vs perfect routing
`min(err_L, err_S)` over the SAME points):

| Grid | worst chosen (route S) | worst perfect | ratio |
|---|---|---|---|
| clean 0.005 steps | 1.5184e-16 | 1.5184e-16 | **1.00x** |
| 400 consecutive floats | 1.8815e-16 | 8.017e-17 | **2.35x** |
| 2000 uniform samples | 2.3226e-16 | 2.1461e-16 | **1.08x** |

Worst anywhere in the sliver: **2.3226e-16** — about one ulp of the returned log, the same register
as the 2.0621e-16 whole-band floor, and **eleven orders** below the 1.2369e-05 the old predicate
cost at x=27.15. Stated honestly across denominators: 2.3226e-16 is *above* the 2.0621e-16 floor
measured on the coarser 0.05 grid, because it is a different grid; on its own grid the sliver costs
1.08x.

**D-4. The band sweep's worst under the candidate is 1.4413e-16 at x=28.01573320140291, not
1.186e-16 at x=29.0.** (The plan measured over sixteen rows; this table has seventeen.) Margin is
therefore **6.94x** (1e-15 / 1.4413e-16), not 8.4x. The plan's own rule — *"If you measure worse
than 2e-16, say so and take the next decade"* — is not triggered: 1.4413e-16 < 2e-16, so **1e-15
stands** and is the tolerance the neighbouring single-point guard already uses. The docstring
carries my measured figure, not the plan's.

**D-5. Two smaller transcription gaps, both benign.** The plan's post-fix two-oracle gap of
1.0137e-11 measures **1.0152e-11** here; row 26.7's route-L error of 4.54e-16 measures
**4.7584e-16**. Both are same-order and neither changes a verdict; recorded because the committed
docstrings quote mine.

**D-6. The hideable window is (26.7, 26.8], not (26.7, 26.8).** Measured by re-routing every band
row through a hostile boundary at each candidate location and counting reddened rows against 1e-15:

```
boundary 26.75: reddens []                        <- HIDDEN
boundary 26.85: reddens [26.8]
boundary 26.89: reddens [26.8]
boundary 26.95: reddens [26.8, 26.9]
boundary 27.05: reddens [26.8, 26.9, 27.0]
```

At a boundary of exactly 26.8 the row at 26.8 takes the series and does not redden, so the window is
half-open at the top. **26.8 is confirmed load-bearing and must not be pruned:** without it, a
boundary anywhere in (26.7, **26.9**] stays green, because row 26.7 scores 4.7584e-16 and passes.
With it, the window is (26.7, 26.8] and the largest route-L error a hidden boundary can carry is
under 3.0228e-14.

**D-7. `grep -rn "float_info" src/` is no longer empty.** It returns one match —
`accountant.py:90`, a COMMENT written in Task 1 explaining why `sys.float_info.min` is deliberately
*not* used. Prose, not code. The load-bearing ceiling is unchanged and checked three stronger ways
(single `import math`; no `import sys` anywhere under `src/personacore/privacy/`; no non-comment
`float_info` match), and `test_accountant_imports_math_only` passes. Logged as a deferred item so
the next executor running that grep does not read a comment as a violation. Separately, the plan's
note that the brief was wrong about `tests/` **reproduces**: `tests/` has 7 `float_info` matches,
5 pre-existing from 22-15 and 2 added by this plan's own meta-guard.

---

## The Frozen Pin Did Not Move — By Capture, Not By Argument

`float.hex()` of every point the module already answers, captured before and after the edit:
all 7 `scripts/mitigation_accountant.py::GOLDEN_EPSILON` epsilons re-derived through `epsilon_for`,
and every representable `DELTA_FRONTIER` delta through `delta_closed`.

```
$ diff before.txt after.txt
$ echo $?
0
```

**EMPTY DIFF over 19 pinned points** (7 golden + 12 representable frontier; the 20th line is the
non-representable `(2.0, 0.05)` row, correctly skipped by both captures). The before capture:

```
GOLDEN_EPSILON sigma=20.0 T=200               -> 0x1.78bb9acadab46p+1   (2.943225239801367)
GOLDEN_EPSILON sigma=14.142135623730951 T=200 -> 0x1.1823af986dfa6p+2   (4.377178095681222)
GOLDEN_EPSILON sigma=10.0 T=200               -> 0x1.a4ab8aa4dedc6p+2   (6.572970067030331)
GOLDEN_EPSILON sigma=5.0 T=200                -> 0x1.ee98d4187f954p+3   (15.456155822609311)
GOLDEN_EPSILON sigma=2.0 T=200                -> 0x1.b3035b50de166p+5   (54.37663901498563)
GOLDEN_EPSILON sigma=1.0 T=1                  -> 0x1.1823af986dfa6p+2   (4.377178095681222)
GOLDEN_EPSILON sigma=8.0 T=64                 -> 0x1.1823af986dfa6p+2   (4.377178095681222)
DELTA_FRONTIER eps=1.0 mu=1.0                 -> 0x1.03f76882040a2p-3   (0.12693673750664397)
DELTA_FRONTIER eps=0.5 mu=2.0                 -> 0x1.32c87517ac6dbp-1   (0.5991856185339332)
DELTA_FRONTIER eps=3.0 mu=0.8                 -> 0x1.264659d6dfd2cp-14  (7.016058166974388e-05)
DELTA_FRONTIER eps=0.1 mu=4.0                 -> 0x1.e783e16ca81d3p-1   (0.9521780438554351)
DELTA_FRONTIER eps=8.0 mu=0.5                 -> 0x1.a5485753df2a0p-190 (1.0486591789120533e-57)
DELTA_FRONTIER eps=2.0 mu=0.707               -> 0x1.49cf631f0bfa0p-10  (0.0012581257103754032)
DELTA_FRONTIER eps=3.3 mu=0.707               -> 0x1.1950035bc2a9cp-20  (1.0479709179912261e-06)
DELTA_FRONTIER eps=0.5 mu=0.5                 -> 0x1.ad97543064028p-5   (0.05244032328766962)
DELTA_FRONTIER eps=6.0 mu=1.0                 -> 0x1.7f291862f14c8p-29  (2.787859763763659e-09)
DELTA_FRONTIER eps=0.01 mu=8.0                -> 0x1.fff7a7ed3e06ap-1   (0.9999363400556949)
DELTA_FRONTIER eps=2.0 mu=0.1                 -> 0x1.83ecbb4e60e00p-301 (3.719450726793152e-91)
DELTA_FRONTIER eps=2.0 mu=0.05                -> NOT REPRESENTABLE (skipped)
DELTA_FRONTIER eps=775.7866600701457 mu=35.35533905932738 -> 0x1.29a352afe3dcfp-17 (8.870303048329635e-06)
```

The after capture is byte-identical to it. **Why exactly one pinned point could have been at risk
and was not:** of the 19, exactly one has `b >= 26.54325845425098` — the thirteenth `DELTA_FRONTIER`
row at `b = 28.01573320140291`, whose `erfc(b)` is exactly `0.0`. It was already on the series route
under the old predicate, so the new predicate cannot move it. The other 18 have a NORMAL `erfc(b)`
(max `b` = 14.1775) and take `math.log` under both.

`git diff --exit-code -- scripts/mitigation_accountant.py` exits **0**. The file was read and never
written.

---

## Mutations Watched Failing

Applied to the REAL committed module, one shot each. `sha256` before the first probe and after the
restore: **`047b30a6e9dce8c6dcab871ddcd5711eafb3264eb506b0d7c631f58c20bdbd65`**, equal, and
`git diff --exit-code -- src/personacore/privacy/accountant.py` exits **0** afterwards.

### Hunk count, VERIFIED rather than inherited

The plan expected *"one behavioural hunk (the predicate) plus one inert one (the constant's
definition, **which nothing else reads**)"*. Measured, the parenthetical is wrong:

```
$ grep -n "_SMALLEST_NORMAL" src/personacore/privacy/accountant.py
96:_SMALLEST_NORMAL = math.ldexp(1.0, -1022)     <- definition
162,234,253,753,760: prose (docstrings / comments)
261:    if e >= _SMALLEST_NORMAL:                 <- the behavioural site
269:            f"{_SMALLEST_NORMAL!r}, ...       <- the raise message's f-string
```

`git diff 8ba735c..HEAD` over the file is **5 hunks**, of which **2 are code** and 3 are prose. The
constant has **two** readers, not one. So both mutations were run.

### M-H — revert the predicate ALONE to `if e > 0.0:`

One hunk (`git diff | grep -c "^@@"` → `1`). **Full suite: `5 failed, 1327 passed, 1 skipped`
in 236.42 s.**

**1 DISTINCT test function, 5 node ids** — all `test_log_erfc_band_routes_accurately`, at
x ∈ {26.8, 26.9, 27.0, 27.151124073213406, 27.19}. Verbatim:

```
AssertionError: _log_erfc(26.8) = -722.10146176919 against the committed 60-dps log(erfc(x))
  -722.10146176916819577 — relative 3.0228e-14 over the measured-plus-margin 1e-15.
  math.erfc(26.8) is 2.484962157e-314, so the route _log_erfc chose here is NOT accurate here:
  the routing boundary has moved toward the side where math.log is applied to an erfc that has
  already lost mantissa bits (2.1828e-11 ABSOLUTE in the log, ...)

AssertionError: _log_erfc(26.9) = -727.4751810077454 ... relative 1.6702e-11 over ... 1e-15.
  math.erfc(26.9) is 1.1522406e-316 ... (1.2151e-08 ABSOLUTE in the log, ...)

AssertionError: _log_erfc(27.0) = -732.8688869822938 ... relative 6.4731e-10 over ... 1e-15.
  math.erfc(27.0) is 5.23705e-319 ... (4.7440e-07 ABSOLUTE in the log, ...)

AssertionError: _log_erfc(27.151124073213406) = -741.0727760913948 ... relative 1.9941e-05
  over ... 1e-15. math.erfc(27.151124073213406) is 1.43e-322 ... (1.4777e-02 ABSOLUTE ...)

AssertionError: _log_erfc(27.19) = -743.0537775602613 against the committed 60-dps log(erfc(x))
  -743.17198938084895565 — relative 1.5906e-04 over the measured-plus-margin 1e-15.
  math.erfc(27.19) is 2e-323 ... (1.1821e-01 ABSOLUTE in the log, ...)
```

### THREE guards stayed GREEN under M-H, and ALL THREE ARE CORRECT

Reported as correct rather than "fixed" into reddening, per the plan's explicit instruction.

| Guard | Why green is correct |
|---|---|
| `test_log_erfc_matches_the_committed_underflow_truth` | Its `b = 28.01573320140291` has `erfc(b)` **exactly 0.0**, so it takes the series under BOTH predicates. M-H cannot reach it. |
| `test_log_erfc_is_inert_where_erfc_is_healthy` (18 node ids) | All 18 inert points have a **NORMAL** `erfc(b)` (max `b` = 14.1775), so both predicates route them to `math.log`. It is a **no-move** guard on a frozen pin, not a correctness guard — 22-12 watched it under **M-B**, where deleting the fast path moves 6 of 7 pinned epsilons and drives 4 to `0.0`. |
| `test_log_erfc_band_spans_all_three_erfc_regimes` (this plan's own companion) | It classifies rows by calling `math.erfc` directly and **never calls `_log_erfc`**. A predicate revert provably cannot move it — which is the design: the module under test cannot fool its own non-vacuity meta-guard. |

**This is a blind-guard/inert-mutation distinction, stated because they look identical in a pytest
summary line.** None of the three is blind: each has a watcher elsewhere (M-B for the second, the
band sweep itself for the first and third). M-H is simply *behaviourally out of their reach*.

### M-H-both — additionally delete the constant's definition

Two hunks. **Identical result: the same 5 node ids in the same 1 distinct test** (263-test
accountant-consumer subset: `5 failed, 263 passed`). So the second hunk is **inert to the suite** —
the plan's expectation holds behaviourally.

**But it is NOT inert to lint**, which is the correction to the plan's "nothing else reads it":

```
$ .venv/bin/ruff check src/personacore/privacy/accountant.py
F821 Undefined name `_SMALLEST_NORMAL`
   --> src/personacore/privacy/accountant.py:268:16
```

The raise message's f-string reads it. Deleting the definition alone would be a latent `NameError`
on an unreachable branch, caught by `ruff` rather than by `pytest`. Recorded because 22-14's M-D and
22-15's M-E both hit the opposite version of this trap (a one-hunk mutation against a two-layer fix
leaving the suite green); here the second layer is genuinely inert to tests, and the tool that sees
it is the linter.

### Restore

```
$ shasum -a 256 src/personacore/privacy/accountant.py
047b30a6e9dce8c6dcab871ddcd5711eafb3264eb506b0d7c631f58c20bdbd65   <- equal to the pre-probe hash
$ git diff --exit-code -- src/personacore/privacy/accountant.py ; echo $?
0
```

---

## Verification

| Check | Command | Result |
|---|---|---|
| Full suite | `.venv/bin/python -m pytest -q` | **`1332 passed, 1 skipped`** in 222.40 s |
| Baseline at `8ba735c` | (given) | `1314 passed, 1 skipped` |
| **Delta, accounted for EXACTLY** | — | **+18 = 17** `test_log_erfc_band_routes_accurately` rows **+ 1** `test_log_erfc_band_spans_all_three_erfc_regimes`. Verified by `--collect-only \| grep -c`: 17 and 1. **Zero regressions.** |
| Phase-22 accountant + reference | `pytest tests/test_phase22_accountant.py tests/test_phase22_reference.py -q` | `211 passed` (was 193) |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | `All checks passed!` / `203 files already formatted` |
| Frozen pin | `git diff --exit-code -- scripts/mitigation_accountant.py` | **exit 0** |
| Dependencies | `git diff --exit-code -- pyproject.toml requirements.txt` | **exit 0** — no installs (T-22-SC) |
| Module import ceiling | `grep -n "^import \|^from " src/personacore/privacy/accountant.py` | `82:import math` — the single line |
| `sys` under `privacy/` | `grep -rn "import sys" src/personacore/privacy/` | (empty) |
| `float_info` executable in `src/` | `grep -rn "float_info" src/ \| grep -v '#'` | (no non-comment match) |
| `float_info` in `scripts/` | `grep -rn "float_info" scripts/` | (empty) |
| Debt markers in changed files | `grep -nE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` | **0 markers** |
| Pinned points | before/after `float.hex()` capture | **EMPTY DIFF**, 19 points |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug, MINE] I destroyed 157 lines of `deferred-items.md` and recovered them**

- **Found during:** Task 3, immediately after committing `d27a1b6`, whose stat read
  `1 file changed, 54 insertions(+), 157 deletions(-)`.
- **Issue:** I used `Write` on `deferred-items.md` without having Read it, assuming it did not
  exist. It did. The write replaced the entire Phase 22 deferral log — the `test_phase20_prereg.py`
  line-anchor entry, the `delta_quadrature` negative-`z` band with its 22-16 retract-in-place,
  WARNING-2 and WARNING-1 — with my two new entries.
- **Fix:** recovered from `d27a1b6~1`, verified all 157 prior lines byte-identical by
  `git show d27a1b6~1:<path> | diff - <(head -157 <path>)` (empty), and re-appended my entries in
  the file's own heading style. Net effect against `d27a1b6~1` is now `61 insertions(+), 0
  deletions(-)`.
- **Commit:** `1f289dd`. The destructive commit `d27a1b6` is left in history rather than rewritten,
  so the record shows what happened.

**2. [Rule 2 — Missing critical correctness] A FOURTH stale premise the plan did not list**

- **Found during:** Task 1, Step 3.
- **Issue:** `_log_erfc`'s own `raise ValueError` message stated *"the series branch requires
  erfc(x) == 0.0, which first happens at x ~ 27.2, and delta_closed's b ... would therefore be
  > 27.2 > 0."* That is the identical falsehood as premises (ii) and (iii), inside a **shipped
  message a user would read at failure time** — the plan lists three premises and this is a fourth,
  in the very function being changed.
- **Fix:** restated against the new predicate (`erfc(x) < _SMALLEST_NORMAL`, first at
  26.54325845425098, so `b > 26.54 > 0`), with the threshold interpolated from the constant rather
  than re-spelled.
- **Files modified:** `src/personacore/privacy/accountant.py`. **Commit:** `5578b59`.

**3. [Rule 2 — Missing critical functionality] The band's lower edge pinned by HARD EQUALITY**

- **Issue:** "all three regimes non-empty" is satisfied by a table that has drifted off the
  boundary — e.g. one whose lowest subnormal row is 26.9. The counts would be intact and the band
  would no longer straddle the thing it exists to straddle.
- **Fix:** the companion additionally asserts `min(regimes["subnormal"]) == 26.54325845425098`,
  following the same hard-equality-over-count discipline
  `test_log_erfc_inert_points_are_not_empty` already uses for its exclusion. Plus a guard that
  `sys.float_info.min == math.ldexp(1.0, -1022)`, so a non-IEEE box fails loudly instead of
  classifying against the wrong threshold.
- **Commit:** `c5d9473`.

**4. [Rule 2 — Documentation correctness] Fixture Consumers list extended**

`tests/fixtures/phase22_reference.py`'s module docstring lists which test consumes which constant.
`LOG_ERFC_BAND` was added to it, so the contract stays complete. **Commit:** `c5d9473`.

### Deliberately NOT Done

**The false figure at `tests/fixtures/phase22_reference.py:185-187`** — *"The error is EXACTLY ZERO
at sigma >= 0.42, so these two rows are the whole reachable band"* — is still there. It is false
(`22-VERIFICATION.md` retracts it in the verifier's own name; re-confirmed here by measurement),
and it sits in a file this plan edits. **Not fixed**, because the dispatch brief names **plan
22-19** as the plan that exists to undo false figures in committed comments, and
`.planning/REQUIREMENTS.md:350` carries the same sentence — one plan should correct both. Logged in
`deferred-items.md` with the measurement and the owner.

### A plan-internal inconsistency, resolved by measurement

Task 2 Step 1 and the objective both say the band measures **4 / 9 / 4**; Step 3 says *"Do NOT
hardcode the 4/8/4 split."* 4+9+4 = 17 = the row count, so 4/8/4 is a leftover from the 16-row
draft. Measured: **4 / 9 / 4**. Nothing is hardcoded either way, so this changes no code.

### Naming collision, recorded so a register is not misread

This plan's mutation label **M-H collides with 22-13's M-H**. Different mutations of different
files — 22-13's reverts `loop.py`'s DP-resume refusal, this one reverts `_log_erfc`'s predicate.
Both were watched RED. Labels are per-plan, not global.

---

## Authentication Gates

None.

## Known Stubs

None. Every value the new code returns is computed; the committed table is literal 60-dps data with
its derivation recorded; `grep -nE "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER"` over all three changed
source files returns **0 markers**.

## Threat Flags

None. The three artifacts introduce no network endpoint, no auth path, no file access and no schema
change. The plan's register is discharged as written: T-22-39 (fast path keyed on smallest normal,
worst error measured equal to the perfect-routing floor, watched under M-H), T-22-40 (band sweep
asserts the CHOSEN route across all three regimes, sliver comment states why the boundary is not
moved up), T-22-41 (scope limit stated in the sweep's docstring, naming
`test_log_erfc_is_inert_where_erfc_is_healthy` and 22-12's M-B), T-22-42 (run-time three-regime
classification plus a hard-equality boundary-row pin), T-22-43 (`float.hex()` capture, empty diff,
`git diff --exit-code` on the pin at every gate), T-22-44 (constant from `math.ldexp`, import
ceiling asserted three ways), T-22-SC (no installs; `pyproject.toml` and `requirements.txt` exit 0).

---

## Self-Check: PASSED

Files claimed created/modified:

```
FOUND: src/personacore/privacy/accountant.py
FOUND: tests/fixtures/phase22_reference.py
FOUND: tests/test_phase22_accountant.py
FOUND: .planning/phases/22-.../deferred-items.md
```

Commits claimed:

```
FOUND: 5578b59   FOUND: c5d9473   FOUND: d27a1b6   FOUND: 1f289dd
```

Content claims verified in-tree: `_SMALLEST_NORMAL = math.ldexp(1.0, -1022)` at
`accountant.py:96`; `if e >= _SMALLEST_NORMAL:` at `accountant.py:261`; `LOG_ERFC_BAND` with 17
rows in the fixture; `test_log_erfc_band_routes_accurately` collecting 17 node ids and
`test_log_erfc_band_spans_all_three_erfc_regimes` collecting 1; full suite `1332 passed, 1 skipped`;
ruff clean over 203 files.
