---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 18
subsystem: privacy
tags: [dp-accountant, float64, subnormal, erfc, coverage, meta-guards, mutation-testing, mpmath]

requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "22-17's `_log_erfc` routing fix — this plan is the coverage half that makes it watched by data"
provides:
  - "A fourteenth `DELTA_FRONTIER` row whose `b` has a SUBNORMAL `erfc(b)`, so V-01 and V-02 sweep the band 0 of 22 pinned points previously entered"
  - "`_inert_points()` filtered on `sys.float_info.min` — it no longer certifies the defective band as healthy"
  - "`_round_trip_pairs()` reaching sigma=0.414, whose T=200 leg was measured 2.07e+07x over `ROUND_TRIP_REL_TOL`"
  - "Four count meta-guards moved together, plus a hard-equality pin that 0.414 is present"
affects: [22-19, phase-23-mitigation-budget]

tech-stack:
  added: []
  patterns:
    - "A locator filter must be keyed on the property that makes the answer right (erfc kept its mantissa), never on the property the defect satisfies (erfc is strictly positive)"
    - "Count guards and the filters they count are COUPLED — a new row in a band the filter mis-classifies reddens the count, so neither change can land alone"
    - "A documented bound is scoped to a fixture set; when the set grows the bound is re-measured, not re-asserted"

key-files:
  created: []
  modified:
    - tests/fixtures/phase22_reference.py
    - tests/test_phase22_accountant.py
    - tests/test_phase22_reference.py
    - src/personacore/privacy/accountant.py

key-decisions:
  - "[Phase 22] The fourteenth row is keyed on the PRE-FIX epsilon 728.2043182233367, not the post-fix 728.1896631303155 — a row keyed on the fixed accountant's own output would need re-deriving every time the accountant changed, which is the photograph-of-the-code failure D-13 exists to prevent"
  - "[Phase 22] Task 2's `_inert_points` retarget was FOLDED INTO Task 1's commit because the two are coupled: the row alone leaves the tree RED in two places, and a red commit is a worse artifact than a plan-order deviation"
  - "[Phase 22] `test_round_trip_pairs_is_not_empty` gains a hard-equality pin that 0.414 is present, because both count guards pass a swap that keeps the count at 13"

patterns-established:
  - "When a plan's task split would leave a commit boundary RED, fold the coupled fix forward and record the coupling as evidence rather than committing red"

requirements-completed: [DPSGD-03]

duration: ~20min
completed: 2026-08-26
---

# Phase 22 Plan 18: Make the Suite Able to See the Subnormal Band Summary

**A fourteenth frontier row inside the erfc-SUBNORMAL band, a filter that stops calling that band
healthy, and a round-trip sigma that reaches its own worst case — the three guards that turn 22-17's
one-line fix from a claim into a measurement, watched reddening at 1.923e-03, 1.919e-03 and
2.07e+07x when the fix is reverted.**

## Performance

- **Duration:** ~20 min wall clock (12:57 → 13:17), including one full-suite run at 234 s
- **Tasks:** 3 of 3
- **Files modified:** 4 (1 source, 3 test/fixture)
- **Commits:** 3 (+1 for this SUMMARY and the state update)

| Commit | Task | Subject |
|--------|------|---------|
| `f58883f` | 1 (+2 Step 1-2) | `test(22-18)`: put a frontier row inside the erfc-SUBNORMAL band and stop certifying it |
| `5a929cd` | 2 | `test(22-18)`: reach the round trip's own worst case with sigma=0.414 |
| `a3fc461` | 3 | `docs(22-18)`: re-measure the five bounds this plan's widened sweeps falsify |

---

## Every Figure I Was Asked to Check, Checked

The brief said *"Check, do not re-derive; flag anything that does not reproduce."* **All fourteen
reproduced bit-exactly.** Nothing in the pinned block needed flagging.

| Quantity | Brief | Measured here |
|---|---|---|
| `math.sqrt(200)/0.414` | 34.159747883408095 | **34.159747883408095** (`repr` equality, not eyeball) |
| `a` | 2.9965347012327306 | **2.9965347012327306** |
| `erfc(a)` | 2.257809999067321e-05 | **2.257809999067321e-05**, `>= smallest normal` → HEALTHY |
| `b` | 27.151124073213406 | **27.151124073213406** |
| `erfc(b)` | 1.43e-322 | **1.43e-322**, asserted `0.0 < e < 2.2250738585072014e-308` → **SUBNORMAL** |
| 60-dps truth | 0.000009980810076964806559419972 | **identical**, from the one-off invocation below |
| 13-digit rounding | `9.980810076965e-6` | **`9.980810076965e-6`** (`mp.nstr(r1, 13)`) |
| V-01 | 3.6662e-14 vs 1.5000e-12 | **3.6662e-14 vs 1.5e-12 — 40.9x inside** |
| V-01 tolerance sanity band | `1e-12 < tol <= 1e-10` | **holds**; `_sig_digits` = 13 → `1e-12 + 5e-13` |
| V-02 | 1.0137e-11 vs 1e-9 | **1.0137e-11 vs 1e-9 — 98.6x inside**, budget NOT widened |
| shipped (pre-22-17) V-01 / V-02 | 1.9227e-03 / 1.9190e-03 | **1.923e-03 / 1.919e-03**, watched under M-H |
| round trip sigma=0.414, T=200 | 2.0703e-05 BEFORE → 2.6817e-16 AFTER | **both**, watched under M-H |
| T=1/64/1000 never in band | — | **confirmed by regime**, see the T-dependence table |
| worst over all 52 round-trip pairs | 8.2901e-15 | **8.2901e-15**, at (14.142135623730951, T=1) |

The one-off mpmath invocation, its output committed as a decimal string in the fixture:

```
$ .venv/bin/python -c "
from mpmath import mp
mp.dps = 60
eps = mp.mpf(728.2043182233367); mu = mp.mpf(34.159747883408095)
a = (eps/mu - mu/2)/mp.sqrt(2); b = (eps/mu + mu/2)/mp.sqrt(2)
print(mp.nstr(mp.mpf(0.5)*mp.erfc(a) - mp.mpf(0.5)*mp.exp(eps)*mp.erfc(b), 25))"
0.000009980810076964806559419972
```

**The `mp.mpf` input form is recorded, and it matters.** Inputs enter as `mp.mpf(<python float>)`,
not `mp.mpf("<decimal string>")`. **Measured for THIS row**, the string form gives
`0.00000998081007696484726271054` — a relative **4.078e-15** away. That is a *different* figure from
the **8.90e-15** 22-12 recorded for the thirteenth row, which is exactly why the provenance block
states its own rather than inheriting the sibling's. Both forms round to the same 13-digit literal,
so the artifact is unaffected.

**Three routes, agreeing, before the literal was committed** (relative to route 1):

| Route | Value | vs route 1 |
|---|---|---|
| 1. mpmath, 60 dps | `0.000009980810076964806559419972` | — |
| 2. `delta_quadrature` — different mathematics | `9.980810076863458e-06` | **1.0154e-11** |
| 3. `delta_closed`, post-22-17 | `9.980810076964634e-06` | **1.728e-14** |
| — shipped `delta_closed`, pre-22-17 | `1.0000000000000345e-05` | **1.9227e-03** |

Route 2 licenses the literal: it shares no transcendental with route 3 beyond `exp`. The shipped
value was reconstructed independently (routing `b` through `math.log(math.erfc(b))` by hand) and
came out `1.0000000000000345e-05`, matching `22-VERIFICATION.md` exactly — ~2.7 correct significant
digits (`-log10(1.923e-03)` = 2.72).

---

## The Coupling, Observed Rather Than Predicted

The brief's table said the row landing without the retarget "REDDENS the `== 18` guard". **Measured,
it reddens TWO things, not one**, and the second is stronger evidence than the first. At the exact
intermediate state — row present, filter unretargeted — the tree was:

```
FAILED tests/test_phase22_accountant.py::test_log_erfc_inert_points_are_not_empty
FAILED tests/test_phase22_accountant.py::test_log_erfc_is_inert_where_erfc_is_healthy[
        DELTA_FRONTIER(728.2043182233367, 34.159747883408095)-728.2043182233367-34.159747883408095]
2 failed, 212 passed
```

```
E  AssertionError: the inertness sweep covers 19 pinned points, not the 18 it claims
E  assert 19 == 18

E  AssertionError: DELTA_FRONTIER(728.2043182233367, 34.159747883408095):
   _log_erfc(27.151124073213406) = -741.0579989406943 is NOT BIT-IDENTICAL to
   math.log(math.erfc(b)) = -741.0727760913948. The fast path is gone or reordered...
```

The second RED is the point stated in one line: **the old filter does not merely miscount, it
generates a parametrized node that demands `_log_erfc` return `math.log` of a float that has already
lost its mantissa.** The guard's message even mis-diagnoses it ("the fast path is gone or
reordered") because that guard was written under the assumption that everything it sweeps is
healthy. That assumption is what the retarget repairs.

The counts, verified by running both filters over both tables rather than taken on the plan's word:

| | OLD filter `erfc(b) > 0.0` | NEW filter `>= sys.float_info.min` |
|---|---|---|
| 13 rows (before this plan) | 18 | 18 |
| 14 rows (after) | **19 → RED** | **18** |

Exclusion list 1 → 2 entries, as specified.

---

## The Four Count Meta-Guards, Enumerated With Before/After

**Every literal was read from the code before it was changed.** The brief's line numbers were stale
for three of the four; the literals themselves were all correct.

| Guard | File | Brief said line | Actual line | Before | After |
|---|---|---|---|---|---|
| `len(DELTA_FRONTIER)` | `test_phase22_reference.py` | 59 | **59** ✓ | 13 | **14** |
| `len(rows)` over `_representable_rows()` | `test_phase22_accountant.py` | 128 | **129** | 12 | **13** |
| `len(pairs)` | `test_phase22_accountant.py` | 907 | **1019** | 48 | **52** |
| distinct sigmas | `test_phase22_accountant.py` | 911 | **1023** | 12 | **13** |

Each assertion's MESSAGE moved with its number, so a future failure still names which row or sigma
the sweep exists to carry. A fifth guard — `len(points) == 18` in
`test_log_erfc_inert_points_are_not_empty` — **deliberately did not move**, and its message now says
what a 19 would mean.

**A guard I added beyond the four (Rule 2).** `test_round_trip_pairs_is_not_empty` now also asserts
`0.414 in {sigma for sigma, _ in pairs}` by hard equality. Both counters pass a swap that replaces
0.414 with any other sigma and keeps the count at 13 — the exact failure mode the exclusion lists
elsewhere in this file use hard equality to close, and the same Rule-2 addition 22-17 made for
`LOG_ERFC_BAND`'s lower edge.

**And the discipline caught me.** My first draft of the two-entry exclusion list spelled the new
row's eps as `728.2043182233407` instead of `728.2043182233367`. The hard-equality assertion reddened
on it immediately:

```
E  At index 1 diff: 'DELTA_FRONTIER(728.2043182233367, ...)' != 'DELTA_FRONTIER(728.2043182233407, ...)'
```

A count-based guard would have passed that transcription error silently. Recorded because it is a
live demonstration of why this file prefers hard equality to counts.

---

## The Round-Trip Sigma, With Its T-Dependence Stated Rather Than Over-Claimed

`0.414` crosses `(1, 64, 200, 1000)` automatically → four new pairs. **The band is a function of T**,
which is `test_epsilon_for_answers_inf_in_the_subnormal_sigma_band`'s finding (22-15) applied here.
Measured at the solved point, post-22-17:

| T | `b` at the solution | `erfc(b)` | regime | round-trip relative |
|---|---|---|---|---|
| 1 | 4.555937 | 1.170825807703566e-10 | NORMAL | 2.6817e-16 |
| 64 | 16.646586 | 1.5222310261915774e-122 | NORMAL | 5.3634e-16 |
| **200** | **27.150821** | **1.5e-322** | **SUBNORMAL** | 2.6817e-16 |
| 1000 | 57.018029 | 0.0 | ZERO | 5.3634e-16 |

**Exactly one leg is in the band**, and the T=1000 leg is past the cliff entirely — it takes the
series under BOTH predicates, so M-H cannot reach it either. All four legs pass, so the sigma is
added unconditionally and **no assertion anywhere requires all four to be in the band**. Confirmed
by the mutation: M-H reddens `test_round_trip[0.414-200]` and only that node id, not all four.

---

## Five Stale Bounds Re-Measured — the Plan Named Four

22-12 found this failure twice; the plan named four instances; **there was a fifth and a sixth.**

| # | Location | Was | Now | Constant moved? |
|---|---|---|---|---|
| a | `ROUND_TRIP_REL_TOL` comment | "8.29e-15 over 48 (sigma, T) pairs", sigma list of 5 | **8.2901e-15 over 52**, sigma list of 6 incl. 0.414 | **No** — 1e-12 stands, deliberately not tightened |
| b | `sigma_for` `Returns:` | "48 (sigma, T) pairs is 8.29e-15" | **52 pairs, 8.2901e-15 at (14.142135623730951, T=1)** | n/a |
| c | `delta_closed` `Returns:` | "the TWELVE representable rows", 1.84e-12 / 9.03e-13 | **THIRTEEN**, **1.8410e-12** at (2.0, 0.1) and **9.0281e-13** at (8.0, 0.5) | **No** — both figures unchanged |
| d | `WORST_RELATIVE_ERROR` comment | "whole 13-row frontier", 1.107e-11 | **14-row**, **1.1091e-11**; new row is 2nd at **1.0174e-11** | **No** — 1.2e-11 stands |
| e | `delta_quadrature` `Returns:` **(not in the plan)** | "the TWELVE representable rows", 1.109e-11 | **THIRTEEN**, **1.1091e-11** | **No** |
| f | `_log_erfc` docstring **(not in the plan)** | "all twelve representable ... asserted by `test_log_erfc_is_inert_where_erfc_is_healthy`" | **thirteen**, and the attribution corrected: the test covers **18 of those 20**, the two cliff rows being owned elsewhere | n/a |

(f) was doubly wrong: the count was stale *and* the attribution was never accurate — the inertness
test has only ever asserted bit-identity for the healthy subset (11 frontier + 7 golden), not for
every representable row. Adding a second cliff row made a pre-existing imprecision into a plain
falsehood.

**A denominator distinction I have to state rather than smooth over.** The plan predicted the
quadrature's error at the new row as **1.0154e-11**; measured, it is **1.0174e-11**. Both are
correct — they have different denominators. 1.0154e-11 is against the **full 60-dps truth** (it is
route 2's provenance gap); 1.0174e-11 is against the **committed 13-digit string**, which is what
the consuming tests compare to. The same split explains a pre-existing 1.107e-11 / 1.109e-11
discrepancy between the fixture comment and the accountant docstring for the *thirteenth* row —
neither was wrong. Both denominators are now named in the fixture comment so the next reader does
not file it as a contradiction.

---

## Mutations Watched Failing

### M-J — a TEST-SIDE mutation: revert `_inert_points()`'s filter to `math.erfc(...) > 0.0`

**It watches the FILTER, not the module.** Applied to the real committed test file.

**Hunk count VERIFIED, not inherited: 1** (`git diff | grep -c "^@@"` → `1`). Checked for a second
layer, because round 1 found twice and 22-17 a third time that a plan's one-hunk mutation was a
two-layer fix: `grep -n smallest_normal` returns **two binding sites in this file** — line 232/236
(`_inert_points`, this mutation's target) and line 453/463 (`test_log_erfc_band_spans_all_three_
erfc_regimes`, a **different function** that classifies `LOG_ERFC_BAND` rows and is not part of
M-J). Reverting the filter as one hunk removes both the local binding and its use, so `ruff` stays
clean at **exit 0** — the opposite of 22-17's M-H-both, where deleting a definition left a reader
behind and tripped `F821`. One hunk is complete here.

**2 DISTINCT tests, 2 node ids**, verbatim above in "The Coupling". Suite under M-J:
`2 failed, 213 passed`.

**Restore:** `943dad8111c87fb36d6aa4bf1aa220ee5224cd52e9ca8948397a6212c00cac01` before and after,
`git diff --exit-code -- tests/test_phase22_accountant.py` → **exit 0**.

### M-H re-applied — this plan's ADDITIONAL REDs only

`_log_erfc`'s predicate reverted to `if e > 0.0:`. **Hunk count VERIFIED: 1**, `ruff` clean. (22-17
established `_SMALLEST_NORMAL` has two readers — the predicate and a raise message's f-string — so a
*delete-the-constant* variant is two hunks; that variant is 22-17's M-H-both and was not needed
here, since the predicate is the behavioural site and this plan's question is only what its own data
adds.)

Under M-H: **8 failed, 209 passed** over the accountant + reference files. **Five are 22-17's**
(`test_log_erfc_band_routes_accurately` at x ∈ {26.8, 26.9, 27.0, 27.151124073213406, 27.19}) and
were recorded there. **THREE ARE THIS PLAN'S**, one per artifact it shipped:

```
E  AssertionError: delta_closed(728.2043182233367, 34.159747883408095) = 1.0000000000000345e-05,
   60-dps truth 9.980810076965e-6 -- relative deviation 1.923e-03 exceeds 1.500e-12

E  AssertionError: the two oracles disagree at eps=728.2043182233367, mu=34.159747883408095:
   quadrature 9.980810076863458e-06 against closed form 1.0000000000000345e-05,
   relative 1.919e-03 over the 1e-9 budget

E  AssertionError: round trip at sigma=0.414, T=200 went out at epsilon=728.2043182233367 and
   came back as 0.4139914289872259 — relative 2.070e-05 over 1.000e-12
```

| This plan's RED | Node id | Measured | Budget | Over by |
|---|---|---|---|---|
| V-01 leg | `test_closed_form_frontier[728.2043182233367-...]` | 1.923e-03 | 1.500e-12 | **1.28e+09x** |
| V-02 leg | `test_two_oracles_agree[728.2043182233367-...]` | 1.919e-03 | 1e-9 | **1.92e+06x** |
| round trip | `test_round_trip[0.414-200]` | 2.070e-05 | 1.000e-12 | **2.07e+07x** |

**Delta contributed by this plan: +3 distinct tests, +3 node ids** (22-17's M-H was 1 distinct test
/ 5 node ids; this tree is 4 / 8). The round-trip message is worth one sentence of its own: it went
out at **exactly `728.2043182233367`**, the epsilon the fourteenth row is keyed on — the row and the
sigma are the same point on the frontier seen from the two directions, which is why one mutation
reddens both.

**Restore:** `27ff55e5826d82a8632ecbb6c46518c1ebb2caf83e753aafaed24ddd702c289b` before and after,
`git diff --exit-code -- src/personacore/privacy/accountant.py` → **exit 0**.

---

## The Frozen Pin and the Pinned Points Did Not Move

This plan changes **no arithmetic** — only test data, a test-side filter, and comments — so any
movement at all would be a defect, not a tolerance question.

```
$ diff <22-17's published 19-point float.hex() capture> <re-captured here>
EMPTY DIFF over 22-17's 19 pinned points
```

Mechanically: 19 hex tokens extracted from `22-17-SUMMARY.md`, 19 re-derived here, sorted, `diff`
empty. All 7 `GOLDEN_EPSILON` and all 12 previously-representable `DELTA_FRONTIER` deltas
bit-identical. The 20th point is the new row itself, at `0x1.4ee68177ef27ep-17`
(`9.980810076964634e-06`), which had no prior capture to move from.

```
$ git diff --exit-code -- scripts/mitigation_accountant.py          ; echo $?   -> 0
$ git diff --exit-code 6ee90dc..HEAD -- scripts/mitigation_accountant.py ; echo $? -> 0
$ git diff --exit-code -- pyproject.toml requirements.txt           ; echo $?   -> 0
```

The frozen pin was **read and never written**, and is byte-unchanged across all six gap plans.

---

## Verification

| Check | Command | Result |
|---|---|---|
| Full suite | `.venv/bin/python -m pytest -q` | **`1338 passed, 1 skipped`** in 234.49 s |
| Baseline (22-17's close) | — | `1332 passed, 1 skipped` |
| **Delta, accounted for EXACTLY** | `--collect-only \| grep -c` | **+6 = 2 + 4**. `grep -c "728.2043182233367"` → **2** (the V-01 and V-02 legs); `grep -c "test_round_trip\[0.414"` → **4**. **Zero regressions, nothing else moved.** |
| Phase-22 accountant + reference | `pytest tests/test_phase22_{accountant,reference}.py -q` | `217 passed` (was 211) |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | `All checks passed!` / `203 files already formatted` |
| Frozen pin | `git diff --exit-code -- scripts/mitigation_accountant.py` | **exit 0** |
| Dependencies | `git diff --exit-code -- pyproject.toml requirements.txt` | **exit 0** — no installs (T-22-SC) |
| mpmath not imported | `pytest ...::test_no_phase22_test_imports_mpmath ...::test_reference_fixture_imports_nothing` | **2 passed** (AST, over the whole `test_phase22_*` glob + the fixture) |
| mpmath textual matches | `grep -rn "import mpmath\|from mpmath" tests/ src/ scripts/` | **2 matches, both PROSE inside docstrings** (`test_phase22_accountant.py:337` quotes the shell invocation; `test_phase22_reference.py:148` is an English sentence). Neither is an import; the AST guard above is the authoritative check. My own new provenance block is inside `#` comments in the fixture, which imports nothing. |
| Module import ceiling | `grep -n "^import \|^from " src/personacore/privacy/accountant.py` | `82:import math` — the single line |
| Debt markers in changed files | `grep -nE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` | **0 markers** across all four |
| Pinned points | `float.hex()` capture vs 22-17's | **EMPTY DIFF**, 19 points |
| Both restores | `shasum -a 256` + `git diff --exit-code` | byte-identical, exit 0, both files |

**Both budgets explicitly NOT widened.** `test_two_oracles_agree` still compares at `1e-9`;
`_frontier_rel_tol`'s sanity band is still `1e-12 < tol <= 1e-10`; `ROUND_TRIP_REL_TOL` is still
`1e-12` and was **not** tightened to the measurement either.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Task 2's Step 1-2 folded into Task 1's commit**

- **Found during:** Task 1, at the commit gate.
- **Issue:** The plan puts the fourteenth row in Task 1 and the `_inert_points` retarget in Task 2,
  but the plan's own coupling table shows the row alone reddens the count guard. Measured, it
  reddens **two** tests. Task 1's `<verify><automated>` is
  `pytest tests/test_phase22_{reference,accountant}.py -q`, which cannot pass at that boundary — so
  the plan's task split requires committing a RED tree.
- **Fix:** captured both REDs verbatim first (they are the strongest evidence in this SUMMARY that
  the retarget is load-bearing rather than cosmetic), then folded the retarget and its
  count-guard/exclusion-list update into the same commit. `f58883f` is green. Task 2's commit
  `5a929cd` carries the round-trip sigma and its two count guards.
- **Files modified:** `tests/test_phase22_accountant.py`. **Commit:** `f58883f`.

**2. [Rule 2 — Missing critical functionality] A hard-equality pin that 0.414 is in the sweep**

- **Issue:** `len(pairs) == 52` and `len(distinct) == 13` both pass a future edit that swaps 0.414
  for any other sigma. The one sigma in the sweep that reaches the erfc-SUBNORMAL band could leave
  silently while both counters stayed green — which is precisely the failure this plan exists to
  close, reintroduced one level up.
- **Fix:** `assert 0.414 in {sigma for sigma, _ in pairs}` with a message naming the 2.07e+07x
  measurement, following this file's established hard-equality-over-count discipline.
- **Commit:** `5a929cd`.

**3. [Rule 2 — Documentation correctness] A FIFTH and SIXTH stale bound the plan did not name**

- **Found during:** Task 3, Step 1, by grepping the scope words rather than the four named sites.
- **Issue:** `delta_quadrature`'s `Returns:` block (e) carries the same "TWELVE representable
  `DELTA_FRONTIER` rows" scope as `delta_closed`'s, and `_log_erfc`'s docstring (f) claimed the
  inertness test asserts bit-identity for "all twelve representable `DELTA_FRONTIER` deltas" — a
  claim that was already imprecise (the test covers only the healthy subset) and that a second
  cliff row turns into a plain falsehood.
- **Fix:** both re-measured and re-scoped; (f)'s attribution corrected to "18 of those 20", naming
  the guards that own the other two.
- **Commit:** `a3fc461`.

**4. [Rule 2 — Documentation correctness] "The last two rows" in the fixture's section-1 header**

- **Issue:** the header said *"The last two rows are RESEARCH F1's finding"*, meaning rows 11 and
  12. That was already positionally false once 22-12 appended a thirteenth row, and this plan's
  fourteenth makes it more so.
- **Fix:** "Rows 11 and 12", which is what it always meant. **Commit:** `f58883f`.

### Divergences From the Plan's Own Figures

**Two, both benign, both stated with their denominators.**

1. **The quadrature's error at the new row is 1.0174e-11, not 1.0154e-11** — different denominators
   (committed 13-digit string vs full 60-dps truth), both correct, explained in full above. The
   fixture comment now names both so the pre-existing 1.107/1.109 pair for the thirteenth row is not
   mis-read as a contradiction either.
2. **The `mp.mpf(str)` vs `mp.mpf(float)` divergence for this row is 4.078e-15, not 22-12's
   8.90e-15** — that figure was measured on the *thirteenth* row and does not transfer. The block
   states its own.

### Line Numbers in the Brief

Three of the four count-guard line numbers were stale (`128`→129, `907`→1019, `911`→1023); the
fourth (`59`) was right. **All four literals were correct.** Read from the code before changing, as
instructed. Recorded because the brief presented them as verified against the code.

### Deliberately NOT Done

**The false figure at the fixture's `EPSILON_OVERFLOW_REGIME` block** — *"The error is EXACTLY ZERO
at sigma >= 0.42, so these two rows are the whole reachable band"* — is still there, in a file this
plan edits. It is false and `22-VERIFICATION.md` retracts it in the verifier's own name. **Not
fixed**, for the same reason 22-17 gave: plan **22-19** exists to undo false figures in committed
comments, and `.planning/REQUIREMENTS.md:350` carries the same sentence — one plan should correct
both places at once. Already logged in `deferred-items.md` by 22-17 with the measurement and the
owner; this plan adds nothing new to that entry.

---

## Authentication Gates

None.

## Known Stubs

None. Every number this plan commits is either measured in this session or a 60-dps literal whose
one-off derivation is recorded beside it, including the `mp.mpf` input form. `grep -nE
"TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER"` over all four changed files returns **0 markers**.

## Threat Flags

None. No network endpoint, no auth path, no file access, no schema change. The plan's register is
discharged as written:

- **T-22-45** (filter certifying the defective band) — retargeted to `sys.float_info.min`, watched
  reddening under M-J at 19-against-18 **plus** a second RED the register did not anticipate.
- **T-22-46** (a cross-check that cannot reach its band) — fourteenth row lands, `erfc(b)` asserted
  strictly between 0.0 and the smallest normal at run time by the test that consumes it; V-01 and
  V-02 both inside UNWIDENED tolerances at 40.9x and 98.6x.
- **T-22-47** (a row or sigma landing uncounted) — all four count guards moved and enumerated with
  before/after, each literal read from the code; a fifth guard deliberately held at 18; a hard
  equality added where the counts alone were insufficient.
- **T-22-48** (`ROUND_TRIP_REL_TOL` over a sweep avoiding its worst case) — 0.414 added, T-dependence
  stated with the per-T regime measured, comment re-measured over 52.
- **T-22-49** (stale bounds surviving a widened sweep) — **six** re-measured, two beyond the plan's
  four.
- **T-22-50** (the 1e-9 budget widened) — unchanged; the row is 98.6x inside it.
- **T-22-SC** (installs) — none; `pyproject.toml` and `requirements.txt` exit 0; mpmath entered only
  as a one-off shell invocation whose output is committed as a decimal string, with the AST no-import
  guard passing.

---

## Self-Check: PASSED

Files claimed modified:

```
FOUND: tests/fixtures/phase22_reference.py
FOUND: tests/test_phase22_accountant.py
FOUND: tests/test_phase22_reference.py
FOUND: src/personacore/privacy/accountant.py
```

Commits claimed:

```
FOUND: f58883f   FOUND: 5a929cd   FOUND: a3fc461
```

Content claims verified in-tree: `DELTA_FRONTIER` holds 14 rows with the fourteenth at
`(728.2043182233367, 34.159747883408095, "9.980810076965e-6")`; `_inert_points` filters on
`sys.float_info.min`; `_round_trip_pairs` contains `0.414` and yields 52 pairs over 13 distinct
sigmas; the four count literals read 14, 13, 52, 13 and the inertness count reads 18 with a
two-entry exclusion list; full suite `1338 passed, 1 skipped`; ruff clean over 203 files; frozen pin
`git diff --exit-code` exit 0.
