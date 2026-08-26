---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
verified: 2026-08-26T17:16:59Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5 must-haves verified
  gaps_closed:
    - "SC3 / DPSGD-03's two-oracle agreement in the erfc-SUBNORMAL band. VERIFIED BY INDEPENDENT MEASUREMENT: `_log_erfc` routes on `e >= _SMALLEST_NORMAL` (accountant.py:272), `_SMALLEST_NORMAL = math.ldexp(1.0, -1022)` (:96) which I confirmed `== sys.float_info.min`; the module still imports `math` and nothing else. Over the frozen frontier T=200/delta=1e-5, sigma 0.30->3.00 at step 5e-4 (5401 points): worst two-oracle relative gap 2.3492e-11, ZERO points over the UNWIDENED 1e-9 budget. In the exact band round 2 failed in (sigma 0.4100-0.4250) the worst is 1.0378e-11; at sigma=0.4130 it is 1.0237e-11, reproducing the orchestrator's figure exactly. Round 2 measured 1.9190e-03 there."
    - "missing item 1 (round 2) — route the erfc-SUBNORMAL band to the series. VERIFIED. Dense sweep of `_log_erfc` vs 120-dps truth over x in [0.5, 40.0] at 4001 points: worst ABSOLUTE error 2.8621e-13 (at x=33.917, series route); worst RELATIVE 2.7362e-16. Round 2's band, measured on the same code, was worst 0.2213 ABSOLUTE."
    - "missing item 2 — a DELTA_FRONTIER row whose `b` is SUBNORMAL. VERIFIED: 14 rows ship; classified by `math.erfc` at run time they are 11 normal / 1 SUBNORMAL / 2 ZERO. The subnormal one is (728.2043182233367, 34.159747883408095), b=27.151124, erfc(b)=1.43e-322 — exactly one, exactly where round 2 had none."
    - "missing item 3 — retarget `_inert_points()`. VERIFIED at test_phase22_accountant.py:232,236 (`sys.float_info.min`). Mutation P-E (revert the filter to `> 0.0`) reddens 2 tests, so the retarget and the new row are genuinely coupled as `test_log_erfc_inert_points_are_not_empty` claims."
    - "missing item 4 — a `_round_trip_pairs()` sigma inside the band. VERIFIED: sigma=0.414 is in the sweep; its T=200 leg reads 2.6817e-16 (round 2: 2.0703e-05, 2.07e+07x over `ROUND_TRIP_REL_TOL`). Over 480 pairs OUTSIDE the committed sweep, worst 3.6323e-14 — zero over the 1e-12 budget."
    - "missing item 5 — correct 'EXACTLY ZERO at sigma >= 0.42' in both files. VERIFIED: dated retract-in-place in `.planning/REQUIREMENTS.md` and `tests/fixtures/phase22_reference.py`, originals left standing, attribution to my own prior report explicit. Its replacement figures reproduce: pre-fix eps at sigma=0.42 is 709.5584251988014 against post-fix 709.5584251987232 (delta 7.8216e-11 ABSOLUTE, and the record prints both epsilons so the denominator is unambiguous); the highest sigma at which they still differ is 0.4238 — I measured 0.4238 on the same 1e-4 grid."
    - "ROUND-2's BLINDNESS PROBE IS CLOSED. Patching `_log_erfc` to return -12345.0 for every SUBNORMAL erfc input left the suite byte-identical at `1314 passed, 1 skipped` in round 2. The same mutation now reddens 11 tests."
  gaps_remaining: []
  regressions: []
gaps: []
deferred: []
human_verification: []
---

# Phase 22: DP-SGD Core, Accountant, and the Correctness Battery — Re-Verification Report (Round 3)

**Phase Goal:** A from-scratch DP-SGD that is provably not the cheap fake — built and proven
entirely on CPU before a single second of M3 time is spent.
**Verified:** 2026-08-26T17:16:59Z
**Status:** passed
**Re-verification:** Yes — third pass, after gap-closure round 2 (plans 22-17 … 22-19)

**Verdict in one line:** **SC3 now holds, and I am saying so on my own measurements rather than on
the summaries.** The erfc-SUBNORMAL band is closed; I swept for the third adjacent band the brief
asked about and there is none in `_log_erfc`; the four sequential edits to `accountant.py` interact
cleanly. I did find **two things worth reporting** — a large-μ divergence in `delta_quadrature`
that my own round-2 WARNING-4 mis-scoped, and one docstring sentence that understates the closed
defect by 741x — and neither is a blocker, for reasons measured below rather than asserted.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criterion) | Status | Evidence |
|---|-----------------------------------|--------|----------|
| 1 | Per-example clipping + Gaussian noise on the **LoRA gradients only**, base frozen, entering `train()` through a NEW ADDITIVE gradient-side seam (DPSGD-01) | ✓ VERIFIED (regression) | 94 passed across `test_phase22_{dpsgd,checkpoint,fakes,dpsgd_ast,wiring}.py`. Round 2 touched **4 files only** — `accountant.py`, `test_phase22_accountant.py`, `phase22_reference.py`, `test_phase22_reference.py`. `dpsgd.py`, `loop.py`, `checkpoint.py` are not in the changed set at all, so no regression surface exists. |
| 2 | With the seam off, the default path is **BIT-IDENTICAL** to the Phase-10 golden-trajectory fixture (DPSGD-02) | ✓ VERIFIED (regression) | `test_seam_off_bit_identical` **PASSED, not skipped**; `test_golden_fixture_is_the_phase10_one` and `test_seam_omitted_equals_seam_none` PASSED. Confirmed by name in `-v` output, not by a count. |
| 3 | The (ε, δ) accountant is stdlib `math` only, exact under q=1 composition, and **agrees with two oracles of DIFFERENT mathematics** (DPSGD-03) | ✓ **VERIFIED** | All three conjuncts measured true. See the section below — this is the one that failed twice. |
| 4 | Each known silent-non-privacy failure is caught with its positive control **WATCHED FAILING FIRST** (DPSGD-04) | ✓ VERIFIED (regression) | All four probes pass; `dpsgd.py` untouched by round 2. 22-13's `loop.py:766` refusal (WARNING-1) still stands and still passes. |
| 5 | `checkpoint.py` carries an MPS RNG slot with backward-compatible load; kill→resume reproduces a **BIT-IDENTICAL reported ε**; `LoRALinear` not restructured; `persona_adapter.pt` + every v3.0 checkpoint still load (DPSGD-05, DPSGD-07) | ✓ VERIFIED (regression) | `test_resume_epsilon_bit_identical[1.0]` and `[0.0]` PASSED by name; `test_dp_noise_rng_round_trips_through_a_kill_and_resume` PASSED. `git diff --exit-code 6ee90dc..HEAD -- src/personacore/lora/` exits 0. |

**Score:** 5/5 truths verified (round 1: 4/5, round 2: 4/5).

---

## SC3, Conjunct by Conjunct — Measured, Not Read

### (a) stdlib `math` only

`import math` at `accountant.py:82` is the only import statement in the file. `sys.float_info`
appears exactly once, at `:90`, **inside a comment** explaining why the module may not import `sys`
and derives the same constant as `math.ldexp(1.0, -1022)` instead. I confirmed in-process that
`_SMALLEST_NORMAL == sys.float_info.min` is `True`.
`test_accountant_imports_math_only` passes (static, out-of-process).
**The orchestrator's claim reproduces exactly.**

### (b) Exact under q=1 composition

86 tests under `-k "composition_identity or round_trip"` pass. Independently, over 480 (σ, T) pairs
**outside** the committed `_round_trip_pairs()` sweep, the worst round-trip deviation is
**3.6323e-14** — zero breaches of the 1e-12 budget. Round 2 measured 2.0703e-05 at σ=0.414.

### (c) Two oracles of different mathematics agree — **the conjunct that failed twice**

| Sweep (all mine, `.venv/bin/python`, this tree) | Points | Worst two-oracle relative gap | Over the UNWIDENED 1e-9 budget |
|---|---|---|---|
| **Frozen frontier** T=200, δ=1e-5, σ 0.30→3.00 step 5e-4 | 5401 | **2.3492e-11** (σ=0.30) | **0** |
| **Round 2's own band**, σ 0.4100→0.4250 step 1e-4 | 151 | **1.0378e-11** | **0** |
| The project's 7 pinned `GOLDEN_EPSILON` σ at T=200 | 7 | 1.1077e-11 | 0 |
| The 14 `DELTA_FRONTIER` rows (V-02's parametrization) | 13 answered | 1.1091e-11 | 0 |

At σ=0.4130 the gap is **1.0237e-11** — the orchestrator's figure, reproduced to five digits.
Round 2 measured **1.9190e-03** at σ=0.414 against the same budget. The budget was **not widened**:
`test_two_oracles_agree` still compares at 1e-9.

---

## Brief Item 1 — I Swept for a THIRD Adjacent Band Myself

This is how round 2 was found, so I did not take the "no third blind band" claim on trust.

**Sweep A — `_log_erfc` against 120-dps truth, x ∈ [0.5, 40.0], 4001 uniform points.**

| Quantity | Value |
|---|---|
| Worst **ABSOLUTE** error of the route actually chosen | **2.8621e-13** at x=33.917 (series) |
| Worst **RELATIVE** error | 2.7362e-16 at x=0.648 |
| Round 2's worst on the same function | **2.2133e-01** ABSOLUTE at x=27.196 |

Nine orders of magnitude better than the level at which round 2's defect lived, and the worst point
is now in the middle of the series' own domain rather than at a routing seam — i.e. what is being
measured is float64's resolution, not a routing mistake.

**Sweep B — the new boundary at x = 26.54325845425098, probed on BOTH sides.** I re-bisected the
boundary rather than trusting the committed one: `math.erfc` at the float below returns
2.2250738585076065e-308 (normal), at the boundary 2.225073858507186e-308 (subnormal). Then 600
consecutive floats each side:

| Side | Route taken | Shipped worst ABS | Perfect-routing floor `min(err_L, err_S)` | Ratio |
|---|---|---|---|---|
| 600 floats **below** | L (`math.log(erfc)`) | 5.6870e-14 | 5.6841e-14 | 1.00x |
| 600 floats **at/above** | S (series) | 1.6149e-13 | 5.6793e-14 | **2.84x** |

**There is a residual sliver and it is real** — above the boundary the series is chosen where route
L would be up to 2.84x better. Its cost is **1.6e-13 absolute in the log**, i.e. 1.6e-13 relative in
`delta_closed`'s second term, which at the frontier's `second/δ ≈ 0.13` is ~2e-14 relative in δ —
**five orders inside the 1e-9 budget.** The module pins this sliver explicitly at `accountant.py:245-271`
with its own three-grid measurement and states why the boundary is deliberately not moved up to the
crossover. My independent numbers land in the same register as theirs (their 400-float figure
8.017e-17 relative for the floor; mine 5.68e-14/708.4 = 8.02e-17 — **exact agreement**).

**Conclusion: there is no third blind band in `_log_erfc`.** The claimed property holds.

---

## Brief Item 2 — Did Closing This Open Something Else? Four Edits in Sequence

`accountant.py` was modified by 22-12 → 22-14 → 22-15 → 22-17. I re-ran each earlier fix's own
acceptance measurement against the current HEAD:

| Earlier fix | Its own check, re-run now | Result |
|---|---|---|
| 22-12 (second term through the underflow) | `delta_closed(775.7866600701457, 35.35533905932738)` | `8.870303048329635e-06` — unchanged, still correct |
| 22-14 (quadrature returns a probability) | 4001-cell rescan, eps=1e-4, μ ∈ [74,78] step 1e-3 | 753 answered / 3248 refused / **0 non-finite / 0 outside (0,1]** |
| 22-15 (subnormal-σ quotient) | `epsilon_for` at σ=0, `nextafter(0,1)`, and inside the band, at T ∈ {1,64,200,1000} | `inf` at all twelve — continuous, no relocated discontinuity |
| 22-17 (the routing predicate) | frozen-frontier sweep above | 0 breaches |

**The FROZEN pre-registration did not move.** All 7 `GOLDEN_EPSILON` are `float.hex()`-**BIT-IDENTICAL**
against the pre-round-2 tree (`831b990`), verified by loading both modules side by side in one
process — not by re-reading a SUMMARY. Worst deviation against the pin's own literals is
**1.0715e-14** against its 1e-12 tolerance. `git diff --exit-code 6ee90dc..HEAD -- scripts/mitigation_accountant.py`
exits 0.

**No interaction defect found.** I then probed outside the bands the plans measured — that is where
every defect so far has lived — and found the item below.

### ⚠️ WARNING-5 (NEW) — `delta_quadrature` degrades at large μ, at the frozen δ, and my own WARNING-4 mis-scoped it

Sweeping (σ, T, δ) rather than raw (eps, μ):

| Sweep | Over the 1e-9 budget | Worst |
|---|---|---|
| T ∈ {1,8,64,200,1000,5000} × δ ∈ {1e-3,1e-5,1e-8}, 3474 cells | **70** | **8.8207e-09** at σ=0.20, T=5000, δ=1e-3 |
| **T=200 alone** (the frozen T), σ 0.05→60 log-spaced, 900 cells | **58** | **3.7936e-09** at σ=0.05 (μ=282.84) |
| 40 000 random log-uniform (eps, μ) | 67 | 1.0753e-02 — **all 67 at δ < 1e-12** (this is WARNING-4) |

**Which oracle is wrong: the quadrature.** Adjudicated at 60 dps at σ=0.05/T=200/δ=1e-5 —
`delta_closed` is right to **9.5856e-14**, `delta_quadrature` is off by **3.7935e-09**. Same verdict
at all four T=5000 cells. The mechanism is Simpson discretisation: the integrand's `1 - exp(-μu)`
feature has width ~1/μ, the grid step is `h = U/(n-1)`, and the error grows smoothly and monotonically
with μ — 8.1e-11 at μ=70.7, 8.8e-09 at μ=353.6, 6.9e-08 at μ=707.1. No cliff, no discontinuity.

**Why this is a WARNING and not a blocker — four measured reasons, not four arguments:**

1. **No published number is affected, in any direction.** I traced the call graph by AST:
   `sigma_for` → `epsilon_for` → `_delta_or_below_float64` → `delta_closed` → `_log_erfc`.
   **`delta_quadrature` appears nowhere on it.** Its only callers in the whole tree are
   `tests/test_phase22_accountant.py` and `tests/fixtures/phase22_reference.py`. Rounds 1 and 2
   were the opposite case — there the *publishing* oracle was wrong, and round 2's was wrong in the
   **privacy-understating** direction. Here the publishing oracle is correct to ~1e-13 everywhere I
   could reach, including at the worst point.
2. **The breach regime is not a privacy claim.** At T=200 the budget is first breached at
   **σ ≤ 0.078902 (μ ≥ 179.24), where ε ≥ 16 826.3** (bisected). That is not a weak guarantee; it is
   no guarantee. The project's own smallest pinned σ is 0.30 (ε=1311.2), which measures 2.3492e-11 —
   **42x inside budget**.
3. **It is pre-existing, not an interaction defect.** Monkeypatching the pre-22-17 `e > 0.0`
   predicate back in gives a **bit-identical** gap (8.8207e-09 both ways) — `erfc(b)` is exactly 0.0
   at b=252, so both predicates route identically there. And `git diff 9009561..HEAD` touches no line
   of the Simpson grid or loop: the quadrature's integrand is unchanged since 22-03.
4. **It is not covered by the existing record, and the reason is mine.** `REQUIREMENTS.md`'s
   round-3 statement item (iii) carries WARNING-4 as the one open band and says *"**ZERO of the 46**
   is at a δ above 1e-12, against this project's frozen δ of 1e-5, seven decades away."* That
   sentence is **true of the sweep it describes and false as a scoping of the problem** — my 30 000-draw
   random (eps, μ) sweep under-sampled large μ, so it could not see this. Here are two-oracle
   disagreements at δ = **1e-5 exactly**. Same lesson, fourth time, and the source figure is mine.

**Action:** carry into Phase 23 beside WARNING-3. Phase 23 is the accountant's first consumer; if
`mitigation_budget.py` ever cross-checks at μ ≥ 179, the two oracles will disagree and it will look
like a new defect rather than the quadrature's known resolution limit.

---

## Brief Item 3 — Is the New Band Guard Actually Capable? What It Does NOT Catch

Six mutations applied to the **real committed files**, phase-22 battery re-run each time, files
restored and **sha256-verified identical** afterwards (both files confirmed).

| # | Mutation | RED | Capable? |
|---|---|---|---|
| **P-A** | predicate reverted to the pre-22-17 `if e > 0.0` | **8** — 5 `test_log_erfc_band_routes_accurately` rows (26.8, 26.9, 27.0, 27.151, 27.19) + `test_closed_form_frontier[14th]` + `test_two_oracles_agree[14th]` + `test_round_trip[0.414-200]` | ✓ YES |
| **P-B** | boundary moved UP to `e >= 1e-318` (route L kept to x≈26.99) | **2** band rows | ✓ YES |
| **P-B2** | boundary moved UP to `e >= 1e-309` (route L kept to x≈26.60) | **0** | see below |
| **P-C** | boundary moved DOWN to `e >= 1e-300` (series where erfc is still normal) | **0** | as documented |
| **P-D** | **round 2's blindness probe** — `_log_erfc` → `-12345.0` for every SUBNORMAL erfc input | **11** | ✓ YES (was **0** in round 2) |
| **P-E** | `_inert_points` filter reverted to `erfc(b) > 0.0` | **2** — `test_log_erfc_inert_points_are_not_empty` + the 14th row's inertness leg | ✓ YES |

**What it does NOT catch, stated plainly and with the number.** The guard's detection floor sits
between an erfc threshold of 1e-312 and 1e-315:

| Boundary moved UP to | Route L kept to x = | Worst ABS err route L would then incur | Guard |
|---|---|---|---|
| 1e-309 | 26.6016 | **5.78e-14** | GREEN |
| 1e-312 | 26.7310 | 2.42e-12 | GREEN (edge) |
| 1e-315 | 26.8598 | 2.46e-09 | **RED** |
| 1e-318 | 26.9880 | 2.44e-06 | **RED** |
| 0.0 (P-A) | 27.2000 | 2.09e-01 | **RED** |

**P-B2's green is CORRECT, not a blind spot.** The guard's tolerance is 1e-15 relative, which at
|log| ≈ 711 is **7.12e-13 absolute** — and the worst error route L would incur in the band P-B2
hands it is **5.78e-14**, genuinely under it. The largest *undetected* boundary move costs
~2.4e-12 relative in `delta_closed`'s second term, roughly 3e-13 in δ — three orders inside the
two-oracle budget. **The guard's threshold is calibrated to the point where the error starts to
matter, not to the point where the predicate changes.** That is the right design and I could not
break it.

**What it also does not catch, and the file says so itself** (`test_log_erfc_band_routes_accurately`
docstring, lines 407-415): a boundary moved DOWN leaves it green (P-C confirms), because below the
crossover both routes land within ~2e-16. That direction is owned by
`test_log_erfc_is_inert_where_erfc_is_healthy`, and P-E confirms that guard fires. **Both limits are
documented in the file before I measured them.**

---

## Brief Item 4 — SC1/SC2/SC4/SC5 Regression Check

Round 2 changed **4 files**, all in the accountant/test surface. `git diff --stat 831b990..HEAD`:
`accountant.py` (+193/-), `phase22_reference.py`, `test_phase22_accountant.py`,
`test_phase22_reference.py`. **`dpsgd.py`, `loop.py`, `checkpoint.py` and `src/personacore/lora/`
are not in the changed set**, which bounds the regression surface structurally rather than by test
count. All 94 SC1/2/4/5 tests pass; the named SC2 and SC5 tests RAN (confirmed by `-v`, not skipped).

---

## Brief Item 5 — Is the Record Honest?

**Yes. This is the most disciplined record I have read in three passes, and I checked it rather than
admired it.**

- **Both retractions are dated, in place, originals standing.** Two `RETRACTED IN PLACE` markers in
  each of `.planning/REQUIREMENTS.md` and `tests/fixtures/phase22_reference.py`. The false sentence
  *"the error is EXACTLY ZERO at σ ≥ 0.42"* is left verbatim with a dated correction appended.
- **Attribution is to me, by name and by quote.** *"The verifier retracts it in its own name
  (`22-VERIFICATION.md`, 2026-08-26T13:46:14Z): 'the error is mine'. No executor invented it — and
  it entered this file through a plan, which is recorded rather than obscured."*
- **The correction goes further than my own diagnosis and says so.** Item (iii) records that even
  *"it measured the fix's delta"* fails at σ=0.42: pre-fix `709.5584251988014` vs post-fix
  `709.5584251987232`, **a delta of 7.8216e-11**, and the highest σ at which they still differ is
  **0.4238** on a 1e-4 grid. **I reproduced both**: the two epsilons to all 16 digits, the absolute
  delta 7.8216e-11, and the highest differing σ = **0.4238** on the same grid. The record prints both
  epsilons, so the denominator is unambiguous. *(Note: the orchestrator's brief paraphrased this as
  "19 σ" — that count is not in the committed record, and I measured 220 differing σ on a 1e-4 grid
  over [0.40, 0.44]. The record itself makes no such claim.)*
- **WARNING-1 closed** (`loop.py:766`, by 22-13, explicitly "not deferred"). **WARNING-2** routed to
  Phase 23 beside DPSGD-06 with its reasoning. **WARNING-3** recorded. **WARNING-4 named as
  *"THIS IS THE OPEN ONE"*** with my measurement attributed rather than re-derived, correctly called
  a different mechanism, and explicitly *"NOT CLOSED"* and *"not inflated into a blocker it is not."*
- **The SC3 verdict is withheld, for the second round running:** *"THE VERDICT ON SC3 IS THE
  RE-VERIFICATION'S, NOT THIS ROW'S."*
- **The bar was not lowered.** The five ROADMAP success criteria hash to
  **`73a316f4aaff10371ea2e6a605810af7d3b6990f56c4324413ef7068d0ccd968`** at `6ee90dc` (pre-execution),
  at `831b990`, at HEAD **and** in the worktree — four-way byte-identical. The orchestrator's
  `73a316f4…` reproduces. The only changed lines in the Phase-22 block are plan-checklist rows and
  the `**Plans**:` narrative.
- **Every committed numeric bound I spot-checked reproduces to the digit** (table below).

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/personacore/privacy/accountant.py` | Two δ oracles + `epsilon_for`/`sigma_for`, math-only | ✓ **VERIFIED** | 1081 lines. `_log_erfc` routes on `e >= _SMALLEST_NORMAL` (:272), derived via `math.ldexp(1.0, -1022)` (:96). All four earlier fixes re-verified intact. |
| `tests/fixtures/phase22_reference.py` | 14 frontier rows + `LOG_ERFC_BAND` | ✓ **VERIFIED** | 14 rows: 11 normal / **1 SUBNORMAL** / 2 ZERO. `LOG_ERFC_BAND` = 17 rows spanning 4 normal / 9 subnormal / 4 zero. I re-derived all 17 committed truths at **140 dps**: worst deviation **6.85e-21** — the 20-digit strings' own quantization. |
| `tests/test_phase22_accountant.py` | Boundary-parametrized guard + retargeted filters | ✓ **VERIFIED** | `_inert_points` filters on `sys.float_info.min` (:232, :236). `test_log_erfc_band_routes_accurately` asserts a property of the RESULT, never of the predicate. |
| `src/personacore/privacy/dpsgd.py` | The DP-SGD mechanism | ✓ VERIFIED | Not in round 2's changed-file set. |
| `src/personacore/training/loop.py` | `dp_fn=` seam + 22-13's refusal | ✓ VERIFIED | Not in round 2's changed-file set. |
| `scripts/mitigation_accountant.py` | The FROZEN pin | ✓ **VERIFIED** | `git diff --exit-code 6ee90dc..HEAD` exits 0. All 7 ε `float.hex()`-identical against `831b990`, checked in-process. |
| `.planning/ROADMAP.md` | Five unchanged success criteria | ✓ **VERIFIED** | sha256 four-way identical (above). |
| `.planning/REQUIREMENTS.md` DPSGD-03 | An honest retract-in-place | ✓ VERIFIED | See item 5. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_log_erfc` | the asymptotic series | fast path keyed on float64's smallest **NORMAL** | ✓ **WIRED** | `if e >= _SMALLEST_NORMAL` at :272; `math.ldexp(1.0, -1022)` at :96, confirmed `== sys.float_info.min` in-process. |
| `test_two_oracles_agree` | the erfc-subnormal band | the 14th `DELTA_FRONTIER` row | ✓ **WIRED** (was NOT_WIRED) | Row (728.2043182233367, 34.159747883408095), erfc(b)=1.43e-322. P-A reddens it. |
| `test_log_erfc_band_routes_accurately` | `LOG_ERFC_BAND` | parametrized sweep, runtime-classified | ✓ **WIRED** | 17 rows, all three regimes non-empty, pinned by a hard-equality meta-guard. |
| `_inert_points` | `sys.float_info.min` | a filter that stops calling a lossy erfc healthy | ✓ **WIRED** | P-E reddens 2 tests. |
| `epsilon_for` / `sigma_for` | `delta_quadrature` | — | ℹ️ **NO LINK, BY DESIGN** | AST-traced: the publishing path is `sigma_for → epsilon_for → _delta_or_below_float64 → delta_closed → _log_erfc`. This is what bounds WARNING-5. |
| `accountant.py` | any production consumer | — | ℹ️ **NONE YET** | WARNING-3, unchanged. Phase 23 is first. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|----------|---------------|--------|--------------------|--------|
| `delta_closed` second term | `0.5*exp(eps + _log_erfc(b))` | fast path OR series, routed on the smallest normal | Yes — worst 2.86e-13 absolute in the log over x ∈ [0.5, 40] | ✓ **FLOWING** (was HOLLOW in [26.543, 27.2)) |
| `delta_quadrature` δ | Simpson on the definition | derived range + 3 conditions | Yes at μ ≲ 179; degrades to 3.8e-09 at μ=283 | ⚠️ **FLOWING, resolution-limited at large μ** (WARNING-5) |
| `epsilon_for` published ε | bisection over `delta_closed` | closed form only | Yes — correct to ~1e-13 at every point measured, including WARNING-5's worst | ✓ FLOWING |
| `GOLDEN_EPSILON` | seven pinned ε | frozen pin | Yes — bit-identical across round 2 | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full regression suite | `.venv/bin/python -m pytest -q` | **`1338 passed, 1 skipped`** in 230.88 s | ✓ PASS |
| Phase-22 accountant + reference battery | `pytest tests/test_phase22_{accountant,reference}.py` | `217 passed` | ✓ PASS |
| SC1/2/4/5 batteries | `pytest tests/test_phase22_{dpsgd,checkpoint,fakes,dpsgd_ast,wiring}.py` | `94 passed` | ✓ PASS |
| SC3 (a) math-only | `pytest -k test_accountant_imports_math_only` | 1 passed | ✓ PASS |
| SC3 (b) q=1 + round trip | `pytest -k "composition_identity or round_trip"` | 86 passed | ✓ PASS |
| **Two oracles on the frozen frontier** | 5401-point σ sweep, T=200, δ=1e-5 | worst **2.3492e-11**, **0** over 1e-9 | ✓ **PASS** |
| **Round 2's failing point** | σ=0.4130, T=200, δ=1e-5 | **1.0237e-11** (was 1.9190e-03) | ✓ **PASS** |
| **`_log_erfc` vs 120-dps truth** | x ∈ [0.5, 40], 4001 pts | worst **2.8621e-13** ABS | ✓ **PASS** |
| **Third-band probe, both sides of the new boundary** | 600 consecutive floats each side | shipped 1.61e-13 vs floor 5.68e-14 (2.84x) | ✓ PASS (sliver, bounded) |
| **Round trip outside the committed sweep** | 480 (σ,T) pairs | worst **3.6323e-14**, 0 over 1e-12 | ✓ PASS |
| **`GOLDEN_EPSILON` bit-identity across round 2** | both modules loaded, `float.hex()` | **7/7 identical** | ✓ PASS |
| Frozen pin untouched | `git diff --exit-code 6ee90dc..HEAD -- scripts/mitigation_accountant.py` | exit 0 | ✓ PASS |
| Five SCs byte-unchanged | sha256, 4-way | `73a316f4aaff1037…` identical | ✓ PASS |
| LoRA untouched | `git diff --exit-code 6ee90dc..HEAD -- src/personacore/lora/` | exit 0 | ✓ PASS |
| Lint | `ruff check .` + `ruff format --check .` | `All checks passed!` / `203 files already formatted` | ✓ PASS |
| Debt markers in the 4 changed files | `grep -E "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` | **0** in all four | ✓ PASS |
| **Wide (σ,T,δ) grid** | 3474 cells | 70 over budget, worst 8.8207e-09 | ⚠️ **WARNING-5** |

### Committed Numeric Bounds — Independently Re-Derived

Every one of these reproduces **to the digit**, which is why I trust the file's other figures more
than I did in round 2.

| Claim, and where | My measurement | Match |
|---|---|---|
| `accountant.py:490-499` — quadrature worst 1.1091e-11 / 2nd 1.0174e-11 / 3rd 1.0032e-12 | 1.1091e-11 / 1.0174e-11 / 1.0032e-12 | ✓ exact |
| `accountant.py:333-337` — `delta_closed` worst 1.8410e-12 (2.0, 0.1); 13-digit worst 9.0281e-13 (8.0, 0.5) | 1.8410e-12 / 9.0281e-13 | ✓ exact |
| `accountant.py:127-138` — round trip worst 8.2901e-15 at (14.142135623730951, T=1) over 52 pairs | 8.2901e-15, same point, 52 pairs | ✓ exact |
| `accountant.py:1019-1022` — σ=0.414/T=200 leg reads 2.6817e-16 | 2.6817e-16 | ✓ exact |
| `accountant.py:206` — series worst 5.8118e-17 relative over {30…1e6} | 5.8118e-17 at x=1e6 | ✓ exact |
| `accountant.py:220-223` — series worst ABS 7.64e-13 at x=150; 5.96e-14 at 28.01573; worst 0.881 ulp at x=29 | 7.6366e-13 / 5.9579e-14 / 0.881 ulp | ✓ exact |
| `accountant.py:258` — 400-float perfect-routing floor 8.017e-17 | 8.02e-17 (mine, 600 floats) | ✓ agrees |
| `REQUIREMENTS.md` — pre/post ε at σ=0.42: 709.5584251988014 / 709.5584251987232, Δ 7.8216e-11; highest differing σ 0.4238 | identical to 16 digits; 0.4238 | ✓ exact |
| `LOG_ERFC_BAND` — 17 committed 60-dps truths | re-derived at 140 dps, worst deviation 6.85e-21 | ✓ exact |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| — | — | No `scripts/*/tests/probe-*.sh` exist and no PLAN declares one (`grep` over 22-17/18/19 PLANs returns nothing). The project's runnable-check convention is pytest, executed above, plus six mutation probes against the real committed files with sha256-verified restores. | SKIPPED (N/A) |

### Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
|-------------|----------------|--------|----------|
| DPSGD-01 | 22-04, 22-06, 22-10, 22-11 | ✓ SATISFIED | Truth 1. |
| DPSGD-02 | 22-06, 22-08, 22-11 | ✓ SATISFIED | Truth 2; golden replay RAN. |
| DPSGD-03 | 22-01…22-05, 22-09, 22-10, 22-12, 22-14, 22-15, **22-17, 22-18, 22-19** | ✓ **SATISFIED** (was BLOCKED) | Truth 3, all three conjuncts measured. WARNING-5 recorded against the non-publishing oracle. |
| DPSGD-04 | 22-01, 22-02, 22-04, 22-06, 22-09, 22-11, 22-13 | ✓ SATISFIED | Truth 4. |
| DPSGD-05 | 22-05, 22-06, 22-07, 22-13 | ✓ SATISFIED | Truth 5. |
| DPSGD-07 | 22-07 | ✓ SATISFIED | `src/personacore/lora/` byte-unchanged. |
| DPSGD-06 | — (Phase 23) | ℹ️ DEFERRED, correctly | Unchanged. |

**Orphaned requirements:** none.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| all 4 changed files | — | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | — | **ZERO markers.** Clean. |
| all 203 files | — | `ruff check` / `ruff format --check` | — | Clean. |
| `accountant.py` | **193-195** | **A denominator conflation — this phase's own signature failure class, in the sentence describing the defect just closed** | ⚠️ **Warning** | *"worst **1.2369e-05 relative** in the returned log at x = 27.15, which **by this docstring's own conversion rule** is 1.2369e-05 relative in `delta_closed`'s second term."* The rule at `:224` reads *"An **ABSOLUTE** error `d` in the log is a relative error `d` in `exp(eps + log)`"* — it takes the absolute error, not the relative one. **Measured at x=27.15: relative 1.236923e-05, absolute 9.165561e-03, second-term relative error `expm1(abs)` = 9.2077e-03 = 0.92%.** The sentence therefore **understates the closed defect by exactly 741.0x** — which is `\|log(erfc(27.15))\| = 740.9969`, confirming the mechanism. The band's true worst is 0.2213 absolute → **24.8%**. Harmless to every current computation (it describes history, and it errs toward understating a *fixed* problem), but it is the same class of error the phase has now caught seven times, sitting inside the paragraph that corrects one. |
| `accountant.py` | 203-204 | A universal claim generalized from one grid | ℹ️ Info | *"This predicate **EQUALS that floor**, so no rule can do better and **none can be blind somewhere this one is not**."* Grid-dependent: I reproduce equality at multiplicative steps 1.002 and 1.005, but **not** at 1.001 (shipped 2.1068e-16 vs floor 1.7291e-16, 1.22x), and my 600-float boundary probe measures 2.84x. The comment's own body at `:256-262` already records a 2.35x case with its grid, so the file **contradicts and corrects itself thirteen lines down** and every figure carries its grid. Cost either way is ~1 ulp. Recorded, not escalated. |
| `test_phase22_accountant.py` | 290, 303 | Stale docstring prose describing the OLD predicate as current | ℹ️ Info | Inside `test_log_erfc_is_inert_where_erfc_is_healthy`: *"`if erfc(x) > 0.0: return log(erfc(x))` runs FIRST and UNCONDITIONALLY"* and *"`_inert_points` already filters on `erfc(b) > 0.0`"*. Both describe the pre-22-17 code; the executable filter at `:232`/`:236` is correctly `sys.float_info.min`, and P-E proves it. Prose lag only. |

---

### WARNINGS — Carried Forward

**WARNING-1 — CLOSED** by 22-13 (`loop.py:766`). Re-confirmed: 94 SC1/2/4/5 tests pass and `loop.py`
is not in round 2's changed set.

**WARNING-2 — DEFERRED to Phase 23**, correctly, beside DPSGD-06. `teach_persona.py` still cannot
resume a DP arm; a missing feature, not a defect in what shipped.

**WARNING-3 — STILL OPEN and still load-bearing.** No production code reports an ε. Phase 23's
`mitigation_budget.py` is the accountant's first consumer.

**WARNING-4 — STILL OPEN, correctly recorded, and now known to be MIS-SCOPED (by me).** The
cancellation band near float64's representability floor reproduces: 67 disagreements above 1e-9 in
40 000 draws, worst 1.0753e-02, **all at δ < 1e-12**. That part stands. What does not stand is the
inference the record draws from it — see WARNING-5.

**WARNING-5 — NEW, OPEN.** `delta_quadrature`'s Simpson resolution degrades with μ, breaching the
1e-9 two-oracle budget for **μ ≥ 179.24 (σ ≤ 0.0789 at T=200), at the frozen δ=1e-5**, worst
3.7936e-09 at T=200 and 8.8207e-09 at T=5000. The **closed form is correct to ~1e-13** at every one
of those points and is the only oracle on the publishing path, so **no ε this accountant can produce
is affected**. Pre-existing (integrand untouched since 22-03; bit-identical under the pre-22-17
predicate) and monotone in μ, not a cliff. `test_two_oracles_agree`'s parametrization tops out at
**μ = 35.36**, so the suite is structurally unable to see it — the same shape as rounds 1 and 2, one
axis over. **Route to Phase 23.**

---

### Human Verification Required

**None.** Every truth was resolvable by measurement in this tree: the golden replay and the real
on-disk artifact legs both RAN rather than skipped, six mutations executed against the real committed
files with sha256-verified restores, and every disputed figure was adjudicated by an independent
120- or 140-dps computation. No round-2 PLAN carries a deferred `<verify><human-check>` block
(`grep -c` returns 0 for all three).

---

### Gaps Summary

**None. SC3 holds, and here is the evidence rather than the assertion.**

The conjunct that failed twice — *the accountant agrees with two oracles of different mathematics* —
is now true across the region this project operates in, measured three independent ways. Over 5401
points on the frozen frontier (T=200, δ=1e-5, σ 0.30→3.00) the worst two-oracle gap is **2.3492e-11**
and **nothing breaches the 1e-9 budget, which was not widened**. In the exact band round 2 failed
in, the worst is **1.0378e-11** against the **1.9190e-03** I measured last time — five orders of
improvement, at the same points, on the same budget. The mechanism is one predicate: `_log_erfc`
routes on `e >= _SMALLEST_NORMAL` rather than on strict positivity, and `_SMALLEST_NORMAL` is
derived as `math.ldexp(1.0, -1022)` so the module still imports `math` and nothing else.

**I looked for the third band, because that is exactly how round 2 was found, and it is not there.**
A 4001-point sweep of `_log_erfc` against 120-dps truth over x ∈ [0.5, 40] gives a worst **absolute**
error of **2.8621e-13** — nine orders below round 2's 0.2213 — with the worst point in the middle of
the series' domain rather than at a seam. Probing 600 consecutive floats on each side of the new
boundary found a real residual sliver where the series is chosen and route L would be up to 2.84x
better, and I priced it: **1.6e-13 absolute in the log**, five orders inside the budget, and
`accountant.py:245-271` already pins it with its own three-grid measurement and argues why the
boundary is deliberately left below the crossover. My independent floor figure agrees with theirs to
three digits.

**The suite can now see the band it was blind to.** Round 2's blindness probe — `_log_erfc` returning
`-12345.0` across the whole subnormal range — left the suite byte-identical at `1314 passed, 1 skipped`.
It now reddens **11 tests**. Reverting the predicate reddens **8**. Reverting the `_inert_points`
filter reddens **2**. And the new guard's detection floor is calibrated, not accidental: it goes green
only where the alternative route's error (5.78e-14) is genuinely under its own tolerance (7.12e-13),
and reddens as soon as the error reaches 2.46e-09. I could not find a harmful boundary move it misses.

**Four sequential edits to `accountant.py` did not interact badly.** Each earlier fix's own acceptance
measurement still holds at HEAD, the frozen pre-registration's seven ε are `float.hex()`-bit-identical
against the pre-round-2 tree, the round trip is worst 3.63e-14 over 480 pairs outside its committed
sweep, and the five ROADMAP success criteria hash four-way identical to `73a316f4…` — **the bar was
not lowered to meet the work**.

**Two things I am reporting rather than passing over.** First, `delta_quadrature` degrades at large μ
and breaches the two-oracle budget at the frozen δ for σ ≤ 0.0789 at T=200 — but the closed form is
right to 1e-13 there, `delta_quadrature` is provably not on the publishing path (AST-traced), and the
regime is ε ≥ 16 826, which is not a weak guarantee but no guarantee. It is pre-existing, monotone,
and it is **not** what rounds 1 and 2 were: there the *publishing* oracle was wrong and round 2's was
wrong in the privacy-understating direction. It is a warning for Phase 23, not a blocker, and calling
it one would be manufacturing a gap the evidence does not support. Second, one sentence at
`accountant.py:193-195` misapplies the file's own conversion rule to a relative error instead of an
absolute one and thereby understates the *closed* defect by exactly 741.0x — the magnitude of the log
at that x. It corrupts no computation and errs toward understating a fixed problem, but it is the
seventh instance of this phase's signature failure class and it sits inside the paragraph that
corrects the sixth.

**And one correction that is mine again.** My round-2 WARNING-4 concluded that the residual two-oracle
disagreements were confined to δ below 1e-12, seven decades from the frozen δ. `REQUIREMENTS.md`
faithfully transcribed that scoping into its round-3 statement. The figure is true of the sweep it
describes and false as a scoping of the problem: my 30 000-draw random `(eps, μ)` sweep under-sampled
large μ. Anchoring the sweep on `(σ, T, δ)` instead surfaces disagreements at δ = 1e-5 exactly. *An
oracle cross-check is worth exactly the band its parametrization sweeps* — the lesson this phase wrote
into its own permanent record — applies to a verifier's sweep as much as to a test's, and this is the
second round in which the sentence that hid a band was one of mine.

Nothing in this tree publishes an ε yet. Phase 23 is the first consumer, and it should carry
WARNING-3, WARNING-4 and WARNING-5 forward. **SC3's claim — that the privacy accounting is provably
true and not the cheap fake — is, on this pass, supported by measurement rather than by narrative.**

---

_Verified: 2026-08-26T17:16:59Z_
_Verifier: Claude (gsd-verifier) — third pass, re-verification after gap-closure round 2_
