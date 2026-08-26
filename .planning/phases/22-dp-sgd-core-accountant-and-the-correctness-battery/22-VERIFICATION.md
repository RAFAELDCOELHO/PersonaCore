---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
verified: 2026-08-26T13:46:14Z
status: gaps_found
score: 4/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5 must-haves verified
  gaps_closed:
    - "missing item 1 — `_log_erfc` carries the second term through the erfc underflow. VERIFIED: `delta_closed(775.7866600701457, 35.35533905932738)` = 8.870303048329635e-06 (was 9.99999999999972e-06, 12.7357% high); two-oracle gap 1.105e-11 against the un-widened 1e-9 budget."
    - "missing item 2 — `mu` finiteness in `epsilon_for`. VERIFIED: `epsilon_for(5e-308, 200, 1e-5)` = `inf` (was `0.0`); sigma=0.0 and the next representable float now AGREE at `inf`, so the discontinuity is removed rather than relocated. Mutation M2 (delete the check) reddens 4 tests."
    - "missing item 3 — `delta_quadrature` upper bound + Simpson `log(4*n)` headroom. VERIFIED: the 4001-cell band rescan (eps=1e-4, mu in [74,78]) returns 0 non-finite and 0 outside (0,1] where 404 `inf` cells stood. Mutation M1 (revert the headroom) reddens `test_quadrature_budgets_the_simpson_sum_not_one_term`."
    - "missing item 4 — a DELTA_FRONTIER row in the `b > 27.2` band. VERIFIED: the 13th row (775.7866600701457, 35.35533905932738) ships and its V-02 leg measures 1.105e-11 against a 1e-9 budget."
    - "missing item 5 — a committed truth replacing `> 700.0`. VERIFIED: `EPSILON_OVERFLOW_REGIME` ships two 60-dps epsilons; mutation M3 (truncate the series to one term) reddens 5 tests including both overflow-regime rows."
    - "WARNING-1 — `loop.py` now REFUSES `dp_fn is None` with `dp_noise_rng` PRESENT (loop.py:766), which is the direction the prior report named as worse in KIND. The opposite direction stays tolerated on a measured argument that names the two committed guards it would redden."
  gaps_remaining:
    - "SC3 / DPSGD-03's two-oracle agreement is STILL falsified — in the `erfc(b)` SUBNORMAL band immediately adjacent to the band 22-12 closed. Same conjunct, same mechanism, one band over."
  regressions: []
gaps:
  - truth: "The (eps, delta) accountant is stdlib `math` only, exact under q=1 composition, and agrees with two oracles of DIFFERENT mathematics (SC3 / DPSGD-03)"
    status: partial
    reason: >-
      Two of three conjuncts hold, unchanged. The third — the two-oracle agreement that IS this
      requirement's entire mechanism of proof — is STILL falsified by measurement, at a point on
      this project's own frozen frontier (T=200, delta=1e-5). 22-12 closed the band where
      `math.erfc(b)` underflows to exactly 0.0. It did not close the band DIRECTLY BELOW it, where
      `math.erfc(b)` returns a SUBNORMAL and has lost up to 52 of its 53 mantissa bits.
      `_log_erfc`'s fast path is guarded on `erfc(x) > 0.0`, so that whole band takes
      `math.log(math.erfc(x))` — bit-for-bit the arithmetic that already shipped — while the
      asymptotic series sitting nine lines below in the same function is 8.5e11x more accurate
      there and is never reached. Measured, not argued; every figure below is from
      `.venv/bin/python` in this tree, adjudicated at 80 dps.
    artifacts:
      - path: "src/personacore/privacy/accountant.py:196-198"
        issue: >-
          `e = math.erfc(x); if e > 0.0: return math.log(e)` routes the ENTIRE erfc-subnormal band
          x in [26.54325845425098, 27.2) to the fast path. `math.erfc` first returns a subnormal at
          x = 26.54325845425098 and first returns exactly 0.0 at x = 27.2, so the band is 0.657
          wide in x and 100% of it is answered by `math.log` of a float that has already lost its
          low bits. WORST ABSOLUTE ERROR in the returned log across the band: **0.2094**, at
          x = 27.196716292271255. The docstring's own conversion rule ("an absolute error d in the
          log is a relative error d in exp(eps + log)") makes that a **23.3% relative error in
          `delta_closed`'s second term**. The asymptotic series in the same function, measured over
          the identical band, is worst 2.458e-13 — **852,064,491,825x more accurate than the branch
          actually taken**. The docstring states the fast path's inertness is "THE LOAD-BEARING
          PROPERTY OF THIS FUNCTION"; measured, that inertness is exactly what preserves the
          pre-existing error here, because `delta_closed`'s pre-fix `else` branch computed the same
          thing.
      - path: "src/personacore/privacy/accountant.py:313"
        issue: >-
          REACHABLE ON THIS PROJECT'S OWN FRONTIER, at the frozen delta. At T=200, delta=1e-5, the
          solution's `b` crosses the subnormal band for sigma in **[0.4135, 0.4185]** — 0.03 below
          the sigma=0.40 point 22-12 fixed. Worst case sigma=0.414: `delta_closed` returns
          1.0000000000000345e-05 against an 80-dps truth of 9.9808100769648472627e-06 — a
          **1.9227e-03 relative error, ~2.7 correct significant digits**, and it does not refuse.
          `delta_quadrature` returns 9.980810076863458e-06, correct to 1.016e-11. The **TWO-ORACLE
          RELATIVE GAP IS 1.919e-03 against `test_two_oracles_agree`'s 1e-9 budget — 1,919,000x
          over.** Induced epsilon error 2.0125e-05 relative (shipped 728.2043182233367 against a
          60-dps 728.1896631303156). NOT A REGRESSION: `delta_closed` at these points is
          BIT-IDENTICAL to the pre-22-12 code (verified by re-running the old `eb == 0.0` guard
          form), so this is a pre-existing sibling defect the fix did not reach.
      - path: "src/personacore/privacy/accountant.py:148-225"
        issue: >-
          THE DIRECTION IS NOT CONSERVATIVE, and that is a change in KIND from the defect this
          phase already closed. The original error dropped a strictly positive term, so delta and
          therefore epsilon were always OVER-stated. A subnormal's lost bits round both ways.
          MEASURED at T=200/delta=1e-5, the shipped epsilon is BELOW the 60-dps truth — the
          privacy-UNDERSTATING direction — at sigma = 0.4150 (-3.512e-04 absolute, 4.844e-07
          relative), 0.4165 (-4.343e-06), 0.4170 (-7.634e-07) and 0.4175 (-6.830e-08). Small, but
          it is the direction that claims more privacy than the mechanism delivers, and the prior
          report's "no published number is optimistic" no longer covers this band.
      - path: "src/personacore/privacy/accountant.py:125"
        issue: >-
          `ROUND_TRIP_REL_TOL = 1e-12` is violated by **2.07e+07x** inside the same band. The
          module's own documented direction, `sigma_for(epsilon_for(sigma, T, delta), T, delta)`
          against `sigma` at T=200/delta=1e-5, deviates by 2.0703e-05 at sigma=0.414 (returns
          0.4139914289872259), 4.041e-06 at 0.4145, 5.615e-07 at 0.4150 and 1.054e-11 at 0.4185.
          The docstring says "measured worst deviation over 48 (sigma, T) pairs is 8.29e-15".
          `_round_trip_pairs()` sweeps the seven `GOLDEN_EPSILON` sigmas plus {0.5, 0.7, 1.5, 3.0,
          50.0}; its SMALLEST sigma is 0.5, so the guard cannot reach the band either.
      - path: "tests/test_phase22_accountant.py:201-211, 361-393"
        issue: >-
          THE SUITE IS STRUCTURALLY BLIND TO THE BAND, exactly as it was to the previous one.
          Measured over all 22 pinned points (13 `DELTA_FRONTIER` + 7 `GOLDEN_EPSILON` + 2
          `EPSILON_OVERFLOW_REGIME`): **ZERO have a subnormal `erfc(b)`.** Twenty are at b <= 14.2
          with a normal erfc; two are past 27.2 in the series band. `_inert_points()` filters on
          `math.erfc(b) > 0.0` and therefore CLASSIFIES THE ENTIRE DEFECTIVE BAND AS "HEALTHY" —
          the filter encodes the defect. PROVEN BY EXECUTION, not inferred: patching `_log_erfc` to
          `return -12345.0` for every input whose `erfc` is subnormal leaves the FULL SUITE at
          **`1314 passed, 1 skipped`**, byte-identical to the unmutated baseline.
      - path: "tests/fixtures/phase22_reference.py:186"
        issue: >-
          A FALSE FIGURE INHERITED FROM MY OWN PRIOR REPORT, now committed twice. "The error is
          EXACTLY ZERO at sigma >= 0.42, so these two rows are the whole reachable band" (repeated
          in `.planning/REQUIREMENTS.md:350` as "EXACTLY ZERO at σ ≥ 0.42"). That measured the
          FIX's delta — pre-fix versus post-fix SHIPPED values, which are genuinely bit-identical
          for sigma >= 0.4125 — and not the error against truth. Measured against 60 dps, the error
          at sigma >= 0.42 is 1.100e-13 at 0.4200 and 9.631e-12 at 0.4185, and the two rows are NOT
          the whole reachable band: [0.4135, 0.4185] is reachable and uncovered. The gap-closure
          plans transcribed the figure faithfully; the error is mine and is corrected here.
    missing:
      - "Route the erfc-SUBNORMAL band to the asymptotic series: change `_log_erfc`'s fast-path guard from `if e > 0.0` to `if e >= 2.2250738585072014e-308` (float64's smallest normal). MEASURED IN THIS TREE: under that one-line change all 7 GOLDEN_EPSILON are `float.hex()`-BIT-IDENTICAL, the 193 accountant+reference tests pass, and the worst point's two-oracle gap falls from 1.919e-03 to 1.014e-11 — inside the un-widened 1e-9 budget."
      - "A DELTA_FRONTIER row whose `b` is SUBNORMAL (e.g. eps=728.2043182233367, mu=sqrt(200)/0.414, b=27.15112, erfc(b)=1.43e-322) with a 60-dps truth, so `test_two_oracles_agree` sweeps the band instead of stepping over it. Today 0 of 22 pinned points enter it."
      - "Retarget `_inert_points()` and `test_log_erfc_inert_points_are_not_empty` from `math.erfc(b) > 0.0` to the smallest-normal threshold. The current filter calls the defective band 'healthy', so it would keep the new row out of the inertness sweep for the wrong reason."
      - "At least one `_round_trip_pairs()` sigma inside [0.4135, 0.4185] at T=200, so `ROUND_TRIP_REL_TOL` is a bound over a band that includes its own worst case rather than over 48 points that avoid it."
      - "Correct `tests/fixtures/phase22_reference.py:186` and `.planning/REQUIREMENTS.md:350`: 'EXACTLY ZERO at sigma >= 0.42' is false as written. It is the FIX's delta that is zero there, not the error."
deferred: []
human_verification: []
---

# Phase 22: DP-SGD Core, Accountant, and the Correctness Battery — Re-Verification Report

**Phase Goal:** A from-scratch DP-SGD that is provably not the cheap fake — built and proven
entirely on CPU before a single second of M3 time is spent.
**Verified:** 2026-08-26T13:46:14Z
**Status:** gaps_found
**Re-verification:** Yes — after gap closure (plans 22-12 … 22-16)

**Verdict in one line:** all five `missing:` items are genuinely closed and I verified each one by
independent measurement — but **SC3 is still FAILED, on the same conjunct, by the same mechanism,
one band over.** 22-12 fixed the band where `math.erfc(b)` underflows to exactly `0.0`. The band
directly below it, where `math.erfc(b)` returns a **subnormal**, is untouched, reachable at this
project's own frozen δ, and the full suite stays green with garbage injected across it.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criterion) | Status | Evidence |
|---|-----------------------------------|--------|----------|
| 1 | Per-example clipping + Gaussian noise on the **LoRA gradients only**, base frozen, entering `train()` through a NEW ADDITIVE gradient-side seam (DPSGD-01) | ✓ VERIFIED (regression check) | Unchanged from the initial verification. `tests/test_phase22_dpsgd.py`, `_dpsgd_ast.py`, `_wiring.py`, `_fakes.py`, `_checkpoint.py`: **94 passed**. `git diff` shows the gap closure touched `loop.py` only in the resume block (66 lines, all inside the `resume_from` guard and its comment); `dpsgd.py` is **not in the changed-file set at all**. |
| 2 | With the seam off, the default path is **BIT-IDENTICAL** to the Phase-10 golden-trajectory fixture (DPSGD-02) | ✓ VERIFIED (regression check) | `test_seam_off_bit_identical` **PASSED, not skipped**, on this box after the `loop.py` edit. `test_golden_fixture_is_the_phase10_one` and `test_seam_omitted_equals_seam_none` both PASSED. 22-13's new refusal is inside `if resume_from is not None:` and cannot reach the seam-off replay. |
| 3 | The (ε, δ) accountant is stdlib `math` only, exact under q=1 composition, and **agrees with two oracles of DIFFERENT mathematics** (DPSGD-03) | ✗ **FAILED** | (a) stdlib-only: VERIFIED, `import math` still the only import. (b) q=1 exactness: VERIFIED. (c) **two-oracle agreement: STILL FALSIFIED** — 1.919e-03 relative gap at σ=0.414/T=200/δ=1e-5 against a 1e-9 budget, in the erfc-SUBNORMAL band. See below. |
| 4 | Each known silent-non-privacy failure is caught with its positive control **WATCHED FAILING FIRST** (DPSGD-04) | ✓ VERIFIED (regression check) | All four probes still pass; `dpsgd.py` unchanged by the gap closure. 22-13's refusal *adds* to this: the `dp_fn is None` + slot-PRESENT direction — the one the initial report named as "worse in KIND" — now raises at `loop.py:766` with a message that states the consequence. |
| 5 | `checkpoint.py` carries an MPS RNG slot with backward-compatible load; kill→resume reproduces a **BIT-IDENTICAL reported ε**; `LoRALinear` not restructured; `persona_adapter.pt` + every v3.0 checkpoint still load (DPSGD-05, DPSGD-07) | ✓ VERIFIED (regression check) | `test_resume_epsilon_bit_identical[1.0]` and `[0.0]` both PASSED after the `loop.py` edit, as did `test_dp_noise_rng_round_trips_through_a_kill_and_resume` (whose back-compat leg is one of the two guards 22-13 cites as the reason the *other* direction stays tolerated). `git diff --exit-code -- src/personacore/lora/` exits 0; last commit `0a26702`, 2026-08-14, predates Phase 22. |

**Score:** 4/5 truths verified — unchanged from the initial verification.

---

### The Five `missing:` Items — Each Re-Measured Independently

| # | `missing:` item | Status | My own measurement (not the SUMMARY's) |
|---|-----------------|--------|-----------------------------------------|
| 1 | `_log_erfc` in log space through the underflow | ✓ CLOSED | `delta_closed(775.7866600701457, 35.35533905932738)` = **8.870303048329635e-06**. Two-oracle gap **1.1050e-11** vs a 1e-9 budget that was NOT widened. Adjudicated at 80 dps: truth 8.8703030483297955e-06, closed form now correct to 1.81e-14. |
| 2 | `mu` finiteness check in `epsilon_for` | ✓ CLOSED | `epsilon_for(5e-308, 200, 1e-5)` = **`inf`**; `epsilon_for(0.0, …)` = `inf`; `nextafter(0.0, 1.0)` = `inf`. The discontinuity is REMOVED, not relocated. Just above the boundary the doubling walk refuses loudly at all four of T ∈ {1, 64, 200, 1000}, as the comment claims. |
| 3 | `delta_quadrature` upper bound + Simpson `log(4*n)` headroom | ✓ CLOSED | Band rescan (eps=1e-4, mu ∈ [74,78] step 1e-3, 4001 cells): **753 answered, 3248 refused, 0 non-finite, 0 outside (0,1]** — where 404 `inf` cells stood. Coverage cost of the tighter condition 1, measured over an independent 4000-draw sweep: **exactly 1 cell** (2457 → 2456). No interaction defect. |
| 4 | `DELTA_FRONTIER` row in the `b > 27.2` band | ✓ CLOSED | 13th row ships; `b = 28.01573`, `erfc(b) = 0.0` exactly; V-02 gap **1.105e-11** vs 1e-9. |
| 5 | Committed truth replacing `> 700.0` | ✓ CLOSED | `EPSILON_OVERFLOW_REGIME` ships `(0.40, 200, "774.8427215876997…")` and `(0.30, 200, "1311.202790704405…")`. My independent 60-dps solve at σ=0.40 gives 774.8427215876998 — agrees. |

**All five closed.** The gap plans did what they were asked. The criterion is still not met, because
the closure was scoped to the five items rather than to the conjunct they were symptoms of.

---

### Guard Capability — Do the NEW Guards Actually Redden? (brief item 3)

Each mutation applied to the **real committed module**, suite re-run, file restored and sha256
re-checked. All three restores were byte-identical.

| Mutation | Target | Result | Capable? |
|----------|--------|--------|----------|
| M1: `sum_headroom = math.log(4.0*n)` → `0.0` | 22-14's Simpson-sum headroom | **1 RED** — `test_quadrature_budgets_the_simpson_sum_not_one_term`. Notably condition 3 then catches the `inf` and refuses, so the layers are independent. | ✓ YES |
| M2: delete `if not math.isfinite(mu): return math.inf` | 22-15's quotient check | **4 RED** — `test_epsilon_for_answers_inf_in_the_subnormal_sigma_band[1|64|200|1000]` | ✓ YES |
| M3: truncate the asymptotic series to one term | 22-12's `_log_erfc` series | **5 RED** — `test_log_erfc_matches_the_committed_underflow_truth`, `test_closed_form_frontier[13th row]`, `test_two_oracles_agree[13th row]`, both `test_epsilon_for_survives_the_overflow_regime` rows | ✓ YES |
| **P1: `_log_erfc` → `-12345.0` for every SUBNORMAL erfc input** | the band this report is about | **`1314 passed, 1 skipped`** — byte-identical to baseline. **ZERO RED.** | ✗ **NO GUARD EXISTS** |

The three guards the gap plans added are genuinely capable — that is a real improvement over this
phase's central finding. P1 is the point: the guards cover the band the plans measured, and the
suite has no detector at all one band over.

---

### The Remaining Gap, Measured

**Where the fast path is used and should not be.** `math.erfc` enters the subnormal range at
x = 26.54325845425098 and reaches exactly 0.0 at x = 27.2. `_log_erfc` guards its fast path on
`e > 0.0`, so all 0.657 of that band takes `math.log(math.erfc(x))`.

| Quantity, over x ∈ [26.543, 27.2) | Value |
|---|---|
| Worst ABSOLUTE error of `_log_erfc` (branch actually taken) in the returned log | **2.094e-01** at x = 27.196716292271255 |
| Worst ABSOLUTE error of the asymptotic series over the identical band | 2.458e-13 |
| Ratio | **8.52e+11x** |
| Implied worst relative error in `delta_closed`'s second term | **≈ 23.3%** |

**Reachability at the project's own frozen δ.** T=200, δ=1e-5, ε solved by the shipped
`epsilon_for`, error against a 60-dps mpmath solve:

| σ | b at the solution | erfc(b) | shipped ε | rel ε error | two-oracle δ gap | direction |
|---|---|---|---|---|---|---|
| 0.4130 | 27.20935 | 0.0 (series) | 731.3711040772157 | 3.28e-16 | 1.024e-11 | — |
| **0.4135** | 27.18022 | subnormal | 729.7858930406062 | **1.136e-05** | **1.084e-03** | OVER |
| **0.4140** | 27.15112 | 1.43e-322 | 728.2043182233367 | **2.013e-05** | **1.919e-03** | OVER |
| **0.4145** | 27.12171 | subnormal | 726.6098109263614 | 3.521e-06 | 3.357e-04 | OVER |
| **0.4150** | 27.09257 | subnormal | 725.0299956136157 | 4.844e-07 | 4.614e-05 | **UNDER** |
| **0.4165** | 27.00572 | subnormal | 720.3323963228256 | 6.030e-09 | 5.727e-07 | **UNDER** |
| **0.4175** | 26.94817 | subnormal | 717.2274893324382 | 9.522e-11 | 9.017e-09 | **UNDER** |
| 0.4200 | 26.80549 | subnormal | 709.5584251988014 | 1.100e-13 | 2.019e-11 | OVER |
| 0.4000 | 27.99685 | 0.0 (series) | 774.8427215876998 | 1.43e-16 | — | — |

Worst: **σ = 0.414, ε error 2.0125e-05 relative** (shipped 728.2043182233367 against a 60-dps
728.1896631303156). Adjudicated at 80 dps at that point — `delta_closed` = 1.0000000000000345e-05,
truth = 9.9808100769648473e-06, `delta_quadrature` = 9.980810076863458e-06: **the closed form is
the wrong oracle** (1.923e-03) and the quadrature is right to 1.016e-11.

**Bit-identical to pre-fix.** Re-running the pre-22-12 `second = 0.0 if eb == 0.0 else …` form at
σ=0.414 gives exactly the shipped value. This is a pre-existing sibling defect the fix did not
reach — **not a regression introduced by the gap closure.**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/personacore/privacy/accountant.py` | Two δ oracles + `epsilon_for`/`sigma_for` | ⚠️ **STILL DEFECTIVE** | 988 lines (was 705). Three of the four numerical defects closed and independently confirmed. The fourth — the erfc-subnormal band — remains, is reachable at the frozen δ, and is not conservative. |
| `src/personacore/privacy/dpsgd.py` | The DP-SGD mechanism | ✓ VERIFIED | **Not in the gap closure's changed-file set.** No regression possible. |
| `src/personacore/training/loop.py` | The `dp_fn=` seam + 22-13's refusal | ✓ VERIFIED | +66 lines, all inside the `resume_from` block. The refusal at `:766` fires on `dp_fn is None and ckpt.get("dp_noise_rng") is not None`, with the three-case analysis written out and the two committed guards that pin the tolerated direction named by test id. |
| `scripts/mitigation_accountant.py` | The FROZEN pin | ✓ VERIFIED | `git diff --exit-code 6ee90dc..HEAD` exits **0** — byte-unchanged across all five gap plans. All 7 `GOLDEN_EPSILON` values re-derived through the changed accountant are bit-identical, and remain bit-identical under my candidate fix. |
| `tests/fixtures/phase22_reference.py` | 13 frontier rows + the two new tables | ⚠️ **PARTIAL** | The 13th row lands and covers the series band. **Zero rows cover the subnormal band.** Line 186 carries a false inherited figure. |
| `.planning/ROADMAP.md` | Five unchanged success criteria | ✓ VERIFIED | Goal + SC block diffed against `6ee90dc`: the **only** line that changed is `**Plans**: 11 plans in 6 waves` → `16 plans in 10 waves (…)`, which is bookkeeping, not a criterion. **The bar was not lowered.** |
| `.planning/REQUIREMENTS.md` DPSGD-03 | An honest retract-in-place | ✓ VERIFIED | See "Is the Record Honest?" below. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `train(resume_from=)` | refusal on a seamless DP resume | `dp_fn is None and ckpt.get("dp_noise_rng")` | ✓ **WIRED** (was PARTIAL) | WARNING-1's dangerous half is closed at `loop.py:766`. |
| `train(resume_from=)` | `DPSGD.load_noise_rng_state` | `ckpt.get("dp_noise_rng")` | ✓ WIRED | Unchanged; both committed guards still pass. |
| `teach_persona.py` | `train(resume_from=)` on a DP arm | — | ⚠️ **NOT WIRED** | WARNING-2, deferred to Phase 23 by explicit decision. Recorded, not inherited as done. |
| `accountant.py` | any production consumer | — | ℹ️ **NONE YET** | Unchanged. Phase 23's `mitigation_budget.py` is the first consumer — which is why the residual band should close before it lands. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `delta_closed` second term | `0.5*exp(eps + _log_erfc(b))` | `_log_erfc` fast path OR series | Series band: yes (1.81e-14). **Subnormal band: NO** — up to 23.3% wrong, silently | ⚠️ **HOLLOW IN [26.543, 27.2)** |
| `delta_quadrature` δ | Simpson on the definition | derived range + 3 conditions | Yes — 0 non-finite, 0 outside (0,1] over 4001 cells; right to 1.0e-11 where the closed form is 1.9e-3 wrong | ✓ FLOWING |
| `epsilon_for` at a subnormal σ | `math.inf` | quotient finiteness check | Yes — continuous with the σ=0 branch at all four T | ✓ FLOWING |
| `GOLDEN_EPSILON` | seven pinned ε | frozen pin | Yes — bit-identical through the gap closure AND under the candidate fix | ✓ FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full regression suite | `.venv/bin/python -m pytest -q` | `1314 passed, 1 skipped` in 226.40 s | ✓ PASS |
| Phase-22 accountant battery | `pytest tests/test_phase22_accountant.py tests/test_phase22_reference.py` | `193 passed` | ✓ PASS |
| SC1/2/4/5 files | `pytest tests/test_phase22_{dpsgd,checkpoint,fakes,dpsgd_ast,wiring}.py` | `94 passed` | ✓ PASS |
| SC2 golden replay actually runs | `pytest tests/test_phase22_dpsgd.py -v` | `test_seam_off_bit_identical PASSED` (not skipped) | ✓ PASS |
| SC5 resumed ε | `pytest tests/test_phase22_checkpoint.py -v` | `test_resume_epsilon_bit_identical[1.0]` and `[0.0]` PASSED | ✓ PASS |
| LoRA untouched | `git diff --exit-code -- src/personacore/lora/` | exit 0 | ✓ PASS |
| Frozen pin untouched | `git diff --exit-code 6ee90dc..HEAD -- scripts/mitigation_accountant.py` | exit 0 | ✓ PASS |
| Lint | `ruff check .` + `ruff format --check .` | `All checks passed!` / `203 files already formatted` | ✓ PASS |
| Debt markers in changed files | `grep -E "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` | **0** across all 6 changed files | ✓ PASS |
| `delta_closed` at the 22-12 fix point | `delta_closed(775.7866600701457, 35.35533905932738)` | `8.870303048329635e-06` (was 12.7357% high) | ✓ PASS |
| `epsilon_for` at a subnormal σ | `epsilon_for(5e-308, 200, 1e-5)` | `inf` (was `0.0`) | ✓ PASS |
| δ is a probability (quadrature) | 4001-cell band rescan | 0 non-finite, 0 outside (0,1] | ✓ PASS |
| **Two oracles agree at σ=0.414/T=200/δ=1e-5** | `delta_closed` vs `delta_quadrature` | `1.0000000000000345e-05` vs `9.980810076863458e-06` — **1.919e-03 apart** | ✗ **FAIL** |
| **Independent 80-dps adjudication of that point** | mpmath `mp.dps=80` | truth `9.9808100769648473e-06` — the **closed form** is wrong by 1.9e-3 | ✗ **FAIL** |
| **`sigma_for` round trip in the band** | `sigma_for(epsilon_for(0.414,200,1e-5),200,1e-5)` | `0.4139914289872259` vs `0.414` — **2.07e-05**, 2.07e+07x `ROUND_TRIP_REL_TOL` | ✗ **FAIL** |
| **Any guard for the subnormal band** | `_log_erfc` → `-12345.0` there, full suite | `1314 passed, 1 skipped` — **zero RED** | ✗ **FAIL** |
| Candidate closure preserves the frozen pin | fast-path guard → `e >= 2.2250738585072014e-308` | 7/7 `GOLDEN_EPSILON` `float.hex()`-identical; 193 tests pass; worst gap 1.919e-03 → **1.014e-11** | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| — | — | No `scripts/*/tests/probe-*.sh` exist and no PLAN declares one; the project's runnable-check convention is pytest, executed above, plus the four mutation probes | SKIPPED (N/A) |

---

### Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
|-------------|----------------|--------|----------|
| DPSGD-01 | 22-04, 22-06, 22-10, 22-11 | ✓ SATISFIED | Truth 1. `dpsgd.py` not in the changed-file set; 94 tests pass. |
| DPSGD-02 | 22-06, 22-08, 22-11 | ✓ SATISFIED | Truth 2. Golden replay RAN and passed after the `loop.py` edit. |
| DPSGD-03 | 22-01, 22-02, 22-03, 22-05, 22-09, 22-10, **22-12, 22-14, 22-15** | ✗ **BLOCKED** | Truth 3. Math-only and q=1 exactness hold. Three of four numerical defects closed. The two-oracle agreement is still falsified at a reachable point on the frozen frontier, and no guard can see the band. |
| DPSGD-04 | 22-01, 22-02, 22-04, 22-06, 22-09, 22-11, **22-13** | ✓ SATISFIED | Truth 4, strengthened by 22-13's refusal on the direction the initial report named as worse in kind. |
| DPSGD-05 | 22-05, 22-06, 22-07, **22-13** | ✓ SATISFIED | Truth 5. Both `test_resume_epsilon_bit_identical` legs pass after the edit. |
| DPSGD-07 | 22-07 | ✓ SATISFIED | Truth 5. `src/personacore/lora/` byte-unchanged. |
| DPSGD-06 | — (Phase 23) | ℹ️ DEFERRED, correctly | Unchanged. |

**Orphaned requirements:** none.

---

### Is the Record Honest? (brief item 4)

**Yes, with one inherited error that is mine, not the executors'.**

- **The retract-in-place left the original assertion standing.** `REQUIREMENTS.md:350` keeps the
  full original SATISFIED narrative verbatim and appends *"RETRACTED IN PLACE 2026-08-26 (plan
  22-16)… Everything above is left unamended as the record of what was believed when Phase 22's
  execution closed."* That is the correct shape.
- **It withholds the verdict.** *"THE VERDICT ON SC3 IS THE RE-VERIFICATION'S, NOT THIS ROW'S…
  this row does not pre-empt it."* Confirmed.
- **It does not overclaim.** It records both denominators explicitly (12.7357% against the 60-dps
  truth; 11.297% against the quadrature with the closed form as denominator) — I checked both
  arithmetically and both are right. It records 22-15's **deviation** from my recommendation
  (`+inf` rather than a raise) and argues it rather than hiding it. It records that in two of three
  plans the specified mutation was one hunk where the fix ships as two layers.
- **The ROADMAP's five success criteria are byte-unchanged.** Diffed against `6ee90dc`; the only
  changed line in the block is the plan-count bookkeeping line.
- **The one error:** `tests/fixtures/phase22_reference.py:186` and `REQUIREMENTS.md:350` both carry
  *"EXACTLY ZERO at σ ≥ 0.42"*. That figure came from my own initial report, where I measured the
  difference between the pre-fix and post-fix shipped values rather than the error against truth.
  It is false, and it is precisely the sentence that made the residual band look already covered.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| all 6 changed files | — | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | — | **ZERO markers.** Clean. |
| all 203 files | — | `ruff check` / `ruff format --check` | — | Clean. |
| `accountant.py` | 151-162 | Comment asserts a property as protective that is in fact the failure mode | 🛑 Blocker | *"THE FAST PATH IS UNCONDITIONAL AND FIRST, AND THAT INERTNESS IS THE LOAD-BEARING PROPERTY OF THIS FUNCTION."* Measured, that unconditional inertness is exactly what preserves a 23.3% error across the erfc-subnormal band. |
| `accountant.py` | 244-260 | `Returns:` accuracy claim scoped to a fixture set that avoids the defect | ⚠️ Warning | Honest scoping — a real improvement over the previous universal claim — but the scope is the 12 rows, and 0 of 22 pinned points enter the band. |
| `accountant.py` | 125-129 | `ROUND_TRIP_REL_TOL` documented as 1e-12 with 8.29e-15 measured | 🛑 Blocker | Violated by 2.07e+07x at σ=0.414; the sweep's smallest σ is 0.5. |
| `test_phase22_accountant.py` | 211 | `erfc(b) > 0.0` used as the definition of "healthy" | 🛑 Blocker | The filter classifies the defective band as healthy, so it encodes the defect it should exclude. |

---

### WARNINGS

**WARNING-1 — CLOSED.** `loop.py:766` refuses `dp_fn is None` with `dp_noise_rng` PRESENT. I
traced the reachability argument for the tolerated direction and it holds: all three
`save_checkpoint` sites splat `**_dp_extra()`, and the two guards it names
(`test_dp_noise_rng_round_trips_through_a_kill_and_resume`'s back-compat leg,
`test_resume_epsilon_bit_identical`'s negative control) both drive that case and both pass.

**WARNING-2 — DEFERRED to Phase 23, correctly.** `teach_persona.py` still cannot resume a DP arm.
This is a missing feature rather than a defect in what shipped, and it is routed beside DPSGD-06.

**WARNING-3 — STILL OPEN, and it is now load-bearing.** No production code reports an ε. That is
still correct for this phase's scope, and it is the only reason the residual band has not
mis-published anything. Phase 23's `mitigation_budget.py` is the accountant's first consumer.

**WARNING-4 (new, informational).** Outside the subnormal band, a 30,000-draw log-uniform sweep
found 46 further two-oracle disagreements above 1e-9, worst **6.08e-09** at δ = 6.26e-237 — a
different mechanism (cancellation in `0.5*erfc(a) - second` near the representability floor), 6x
over budget, and **0 of them at a δ above 1e-12**. Not a blocker; recorded so it is not discovered
later as a surprise.

---

### Human Verification Required

None. Every truth was resolvable from the codebase by measurement: the golden replay and the real
on-disk artifact legs both RAN rather than skipped on this box, the four mutation probes executed
against the real committed module with sha256-verified restores, and the disputed oracle was
adjudicated by an 80-dps third computation. No PLAN carried a deferred `<verify><human-check>`
block.

---

### Gaps Summary

**The gap closure did real, verifiable work, and I want that stated before the verdict.** All five
`missing:` items are closed and I confirmed each one myself rather than reading a SUMMARY: the
dropped second term is recovered to 1.81e-14, the `mu` quotient is checked and answers `+inf`
continuously with the σ=0 branch, `delta_quadrature` returns a probability or refuses across the
band where 404 cells returned `inf`, the thirteenth frontier row lands and its V-02 leg measures
1.105e-11 against a budget that was *not* widened, and the `> 700.0` liveness assertion is gone.
Three of those guards redden under mutation of the real module. The frozen pre-registration is
byte-unchanged with all seven ε bit-identical, the ROADMAP's success criteria are byte-unchanged,
and the DPSGD-03 retraction is one of the more honest records I have read — it names both
denominators, records a deliberate deviation from my own recommendation and argues it, reports that
two plan-specified mutations were single hunks against two-layer fixes, and explicitly refuses to
call SC3 itself.

**SC3 is still not true.** The criterion is not "five items were addressed"; it is that the
accountant *agrees with two oracles of different mathematics*. Measured, at σ=0.414 / T=200 /
δ=1e-5 — this project's own frozen δ, 0.03 in σ away from the point that produced the original
failure — the two oracles disagree by **1.919e-03 relative, against a 1e-9 budget**. An 80-dps
third computation says the **closed form** is the wrong one, by 1.9e-3, with roughly 2.7 correct
significant digits; the quadrature is right to 1.0e-11. The induced ε error is 2.01e-05 relative,
and at four measured σ it runs in the **privacy-UNDERSTATING** direction — which the previous
defect never did, so "no published number is optimistic" no longer holds in this band. The module's
own `ROUND_TRIP_REL_TOL` is violated by 2.07e+07x at the same σ.

**The root cause is one line and the shape of it is this phase's own central finding, repeated.**
`_log_erfc` routes on `math.erfc(x) > 0.0`. That predicate is true throughout the subnormal range,
where `math.erfc` has already thrown away up to 52 of its 53 mantissa bits — so the branch whose
inertness the docstring calls "the load-bearing property of this function" faithfully reproduces a
pre-existing 23.3% error, while the asymptotic series nine lines below, which is 8.5e11x more
accurate there, is never reached. `delta_closed` at these points is **bit-identical to the pre-22-12
code**: this is a sibling defect the fix stepped over, not a regression it introduced.

**And the suite cannot see it, for exactly the reason it could not see the last one.** Zero of the
twenty-two pinned points has a subnormal `erfc(b)`. `_round_trip_pairs()`'s smallest σ is 0.5.
`_inert_points()` filters on `erfc(b) > 0.0` and therefore *classifies the defective band as
healthy* — the filter encodes the defect. I proved the blindness by execution rather than
inference: `_log_erfc` returning `-12345.0` for every subnormal input leaves the full suite at
`1314 passed, 1 skipped`, byte-identical to baseline. The lesson 22-16 wrote into the permanent
record — *"an oracle cross-check is worth exactly the band its parametrization sweeps"* — is
correct, and it applies to the closure as much as to the thing closed.

**One sentence of my own to own.** The reason this band looked already covered is a false figure in
my initial report — *"the error is EXACTLY ZERO at σ ≥ 0.42"* — which measured the fix's delta
rather than the error against truth, and which the plans faithfully transcribed into
`phase22_reference.py:186` and `REQUIREMENTS.md:350`. It needs correcting in both places.

**The closure is small and I measured it here.** Changing the fast-path guard to
`if e >= 2.2250738585072014e-308` leaves all seven `GOLDEN_EPSILON` bit-identical, passes the 193
accountant and reference tests, and drops the worst point's two-oracle gap from 1.919e-03 to
**1.014e-11** — inside the un-widened 1e-9 budget. What it needs beside it is a frontier row in the
band, a retargeted `_inert_points` filter, and a round-trip σ inside [0.4135, 0.4185], so the next
verifier is not the detector.

Nothing in this tree publishes an ε yet, so nothing is currently wrong in the world. Phase 23 is the
first consumer. This phase's stated purpose is that the privacy claim must be *provably* true — and
an accountant that is 1.9e-3 wrong where nobody swept, in the understating direction, is not yet
proven.

---

_Verified: 2026-08-26T13:46:14Z_
_Verifier: Claude (gsd-verifier) — re-verification after gap closure_
