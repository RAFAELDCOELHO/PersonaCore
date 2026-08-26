---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 12
subsystem: privacy
tags: [differential-privacy, accountant, erfc-underflow, asymptotic-series, mutation-probes, gap-closure, frozen-pin]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-03's src/personacore/privacy/accountant.py::delta_closed — the Balle-Wang Thm 8 closed form whose second term this plan repairs"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-05's epsilon_for/sigma_for — the bisection whose overflow-regime walk is now compared against a committed truth instead of a liveness assertion"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-02's scripts/mitigation_accountant.py::GOLDEN_EPSILON — the FROZEN pre-registration this change is proven inert against, bit for bit"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-11's mutation-probe register (real-module mutation, unmutated control, sha256-verified restore, distinct-RED accounting) — the evidence format Task 3 follows"
provides:
  - "src/personacore/privacy/accountant.py::_log_erfc — log(erfc(x)) carried through the erfc underflow, with an unconditional fast path that makes the change a PROVABLE no-op on every already-answered point"
  - "a delta_closed whose second term survives the erfc cliff: 12.7357% wrong -> 1.795e-14 at the frontier point the module's own comment cited as reachable"
  - "tests/fixtures/phase22_reference.py's thirteenth DELTA_FRONTIER row — the first committed row in the b > 27.2 band, so V-01 and V-02 sweep where they were structurally unable to look"
  - "tests/fixtures/phase22_reference.py::EPSILON_OVERFLOW_REGIME — committed 60-dps epsilons replacing `assert got > 700.0`"
  - "three watched mutations (M-A, M-B, M-G) with distinct-RED counts, verbatim messages and sha256-identical restores"
affects: [23 the frontier sweep and DPSGD-06, whose mitigation_budget.py is the accountant's first production consumer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A repair to a module constrained by a FROZEN pin, made SAFE BY CONSTRUCTION rather than by testing after the fact: the new code path is unreachable from every pinned input because the old arithmetic runs first and unconditionally"
    - "Inertness asserted by exact `==` over an 18-point pinned set, with the vacuity guard moved OUT of the per-point test (where the locator's own filter would make it a tautology) and into a hard-count companion"
    - "mpmath used as a ONE-OFF shell invocation whose OUTPUT is committed as a decimal string, with the exact invocation AND which `mp.mpf` form the inputs took recorded in the provenance comment"
    - "A reference constant whose LIMIT is stated in its own provenance ('a 60-dps read of the same closed form catches float64 error, never a formula error') plus a pointer to where real independence comes from"

key-files:
  created: []
  modified:
    - src/personacore/privacy/accountant.py
    - tests/fixtures/phase22_reference.py
    - tests/test_phase22_accountant.py
    - tests/test_phase22_reference.py

key-decisions:
  - "_log_erfc's fast path is UNCONDITIONAL and FIRST. That ordering is the entire safety argument for touching a module pinned by a frozen pre-registration: every input with a healthy erfc gets bit-for-bit the shipped arithmetic, so all 19 already-answered points are unchanged by construction rather than by luck"
  - "The new DELTA_FRONTIER row must be EXCLUDED from the inertness sweep, because its whole purpose is to take the series branch. _inert_points filters on erfc(b) > 0.0 and the non-vacuity moved to a hard-count companion test — re-asserting the filter inside the per-point test would have been a tautology dressed as a meta-guard"
  - "The 1e-9 two-oracle budget was NOT widened. The measured gap at the new row is 1.105e-11, 90.5x inside it; had it not fit, the fix would have been wrong rather than the tolerance"
  - "delta_quadrature's Returns block records its `(0, 1]` claim as NOT ENFORCED rather than re-asserting it. The +inf / >1.0 defect is real and outside this plan's closure; re-committing a measured-false contract with my own hands was the one thing I would not do"
  - "WORST_RELATIVE_ERROR was re-measured (2.7e-12 -> 1.2e-11). It is consumed by no test, but its comment claimed a bound 'across the whole 12-row frontier' that the thirteenth row falsified"

patterns-established:
  - "Provable-no-op repair under a frozen pin: new branch reachable only where the old code was already wrong"
  - "Both denominators reported for every accuracy claim (full-precision truth AND the committed string the test actually compares to)"

requirements-completed: []
requirements-contributed: [DPSGD-03]

# Metrics
duration: 95min
completed: 2026-08-26
---

# Phase 22 Plan 12: The erfc Cliff, Closed and Watched — Summary

`delta_closed` silently discarded its second term wherever `math.erfc(b)` underflowed; a
module-level `_log_erfc` now carries it in log space, and a thirteenth `DELTA_FRONTIER` row puts
the two-oracle cross-check inside the band it was structurally unable to reach.

## What Shipped

Three of the five gaps `22-VERIFICATION.md` recorded are closed. The two not closed — a finiteness
check on `mu` in `epsilon_for`, and `delta_quadrature`'s missing upper-bound refusal — are
untouched by design; they belong to other plans.

| Gap closed | Where |
|---|---|
| `_log_erfc(x)` staying in log space through the underflow, so `second` is never silently dropped | `accountant.py:128-198` |
| A `DELTA_FRONTIER` row in the `b > 27.2` band with a healthy `a`, so `test_two_oracles_agree` covers it | `phase22_reference.py` row 13 |
| A committed truth for `test_epsilon_for_survives_the_overflow_regime`, replacing `> 700.0` | `phase22_reference.py::EPSILON_OVERFLOW_REGIME` |

**Commits:** `06d9ce9` (Task 1), `6c4322a` (Task 2), `f9fab8c` (Task 3).

## The Defect, and the Direction

At `(eps=775.7866600701457, mu=35.35533905932738)` — σ=0.40 / T=200 / δ=1e-5, the exact input the
shipped line's own comment cited as reachable — `math.erfc(b)` is exactly `0.0` while `math.exp(eps)`
is ~8.3e336, so the true second term is `1.1297e-06` against a first term of `9.99999999999972e-06`.

| | value | relative to the 60-dps truth `8.870303048329795521072e-6` |
|---|---|---|
| shipped `delta_closed` | `9.99999999999972e-06` | **1.2736e-01** — zero correct significant digits, and it did not refuse |
| fixed `delta_closed` | `8.870303048329635e-06` | **1.7952e-14** |

`second >= 0`, so dropping it OVER-states δ and therefore OVER-states ε — the conservative
direction. That is why this was a latent wrong number rather than a live privacy break, and why it
survived a phase.

## The Frozen Pin Did Not Move

This was the single irrecoverable risk. `scripts/mitigation_accountant.py` is a closed
pre-registration with no correction path.

Every one of the **19** points the module already answered was captured by `float.hex()` before the
edit and re-captured after. `diff` of the two captures is **empty** — all 7 `GOLDEN_EPSILON`
epsilons and all 11 representable `DELTA_FRONTIER` deltas BIT-IDENTICAL, and row 12 still `REFUSED`.
Raw before/after, verbatim:

```
delta_closed(1.0, 1.0)    = 0x1.03f76882040a2p-3      delta_closed(2.0, 0.707)  = 0x1.49cf631f0bfa0p-10
delta_closed(0.5, 2.0)    = 0x1.32c87517ac6dbp-1      delta_closed(3.3, 0.707)  = 0x1.1950035bc2a9cp-20
delta_closed(3.0, 0.8)    = 0x1.264659d6dfd2cp-14     delta_closed(0.5, 0.5)    = 0x1.ad97543064028p-5
delta_closed(0.1, 4.0)    = 0x1.e783e16ca81d3p-1      delta_closed(6.0, 1.0)    = 0x1.7f291862f14c8p-29
delta_closed(8.0, 0.5)    = 0x1.a5485753df2a0p-190    delta_closed(0.01, 8.0)   = 0x1.fff7a7ed3e06ap-1
delta_closed(2.0, 0.1)    = 0x1.83ecbb4e60e00p-301    delta_closed(2.0, 0.05)   = REFUSED

epsilon_for(20.0, 200)              = 0x1.78bb9acadab46p+1
epsilon_for(14.142135623730951,200) = 0x1.1823af986dfa6p+2
epsilon_for(10.0, 200)              = 0x1.a4ab8aa4dedc6p+2
epsilon_for(5.0, 200)               = 0x1.ee98d4187f954p+3
epsilon_for(2.0, 200)               = 0x1.b3035b50de166p+5
epsilon_for(1.0, 1)                 = 0x1.1823af986dfa6p+2
epsilon_for(8.0, 64)                = 0x1.1823af986dfa6p+2
```

**Why it is inert by construction, not by luck:** `_log_erfc`'s `if e > 0.0: return math.log(e)` is
unconditional and FIRST, so it is bit-for-bit the arithmetic the shipped `else` branch already
performed. The asymptotic series is reachable only where the shipped code was returning `0.0`.
That property is now committed as `test_log_erfc_is_inert_where_erfc_is_healthy`, asserting exact
`==` over 18 pinned points (11 frontier + 7 golden), with `test_log_erfc_inert_points_are_not_empty`
pinning both the count and — by hard equality — which single row is excluded.

## Measured Numbers, With Their Denominators

`accountant.py`'s own docstring warns about conflating denominators ("same tolerance, unrelated
denominators"), so both are stated.

| Quantity | Measured | Bound | Margin |
|---|---|---|---|
| Series truncation, worst over x ∈ {27.2 … 150} | **7.6366e-13** absolute in the log (at x=150) | plan's STOP threshold 1e-11 | **13.1x** |
| Series truncation at the `b = 28.01573320140291` that matters | **5.9579e-14** | — | 0.52 ulp |
| `_frontier_rel_tol("8.870303048330e-6")` | **1.5e-12** | band `1e-12 < tol ≤ 1e-10` | holds |
| V-01, fixed `delta_closed` vs the **COMMITTED 13-DIGIT STRING** — *the test's denominator* | **4.1061e-14** | 1.5e-12 | **36.5x** |
| V-01, same value vs the **FULL-PRECISION mpmath truth** | **1.8143e-14** | 1.5e-12 | **82.7x** |
| V-02 two-oracle gap at the new row | **1.1050e-11** | 1e-9, **unwidened** | **90.5x** |
| `epsilon_for(0.40, 200)` vs its committed truth | **0.0e+00** | 1e-12 | exact |
| `epsilon_for(0.30, 200)` vs its committed truth | **1.7341e-16** | 1e-12 | ~5,800x |

Every truncation error measured is **below one ulp of the returned log** (worst 0.881 ulp, at
x=29.0), so what is being measured is float64's own resolution and not truncation.

## Mutations Watched Failing

All three applied to the REAL committed file, one shot each, restored byte-identically.
`sha256` before every probe and after every restore: `6e50e175b8c6a150f15bc1f3622b0c693f538f1bd1a40768b64b8a77e4e37072`,
**equal in all three cases**, and `git diff --exit-code -- src/personacore/privacy/accountant.py`
exited 0 after each.

### M-A — restore the dropped term (`delta_closed`'s second-term line only)

**3 DISTINCT tests, 4 node IDs.** Verbatim:

```
delta_closed(775.7866600701457, 35.35533905932738) = 9.99999999999972e-06, 60-dps truth
  8.870303048330e-6 -- relative deviation 1.274e-01 exceeds 1.500e-12
the two oracles disagree at eps=775.7866600701457, mu=35.35533905932738: quadrature
  8.870303048231617e-06 against closed form 9.99999999999972e-06, relative 1.130e-01 over the 1e-9 budget
epsilon_for(0.4, 200, delta) = 775.7866600701457 against the committed 60-dps truth
  774.8427215876997401873883 — relative 1.218e-03 over 1.000e-12
epsilon_for(0.3, 200, delta) = 1312.1599912046381 against the committed 60-dps truth
  1311.202790704405616448176 — relative 7.300e-04 over 1.000e-12
```

`test_log_erfc_matches_the_committed_underflow_truth` stayed **GREEN under M-A, and that is
CORRECT** — M-A reverts `delta_closed`'s line and never touches `_log_erfc`, which that test calls
directly. It was not "fixed" into reddening; M-G below is its watcher.

### M-B — delete `_log_erfc`'s fast path (the pin-moving mutation)

**6 DISTINCT tests, 36 node IDs:** `test_closed_form_frontier`, `test_two_oracles_agree`,
`test_log_erfc_is_inert_where_erfc_is_healthy`, `test_epsilon_for_matches_golden`, `test_round_trip`,
`test_composition_identity_would_fail_under_exact_equality`.

Measured directly on the frozen pin under M-B — **6 of 7 `GOLDEN_EPSILON` rows move, and 4 return
`0.0`**:

| σ | T | honest | under M-B |
|---|---|---|---|
| 20.0 | 200 | 2.943225239801367 | **0.0** |
| 14.142135623730951 | 200 | 4.377178095681222 | **0.0** |
| 10.0 | 200 | 6.572970067030331 | 6.5729696382081375 |
| 5.0 | 200 | 15.456155822609311 | 15.4561558225707 |
| 2.0 | 200 | 54.37663901498563 | 54.37663901498563 (unmoved) |
| 1.0 | 1 | 4.377178095681222 | **0.0** |
| 8.0 | 64 | 4.377178095681222 | **0.0** |

`test_epsilon_for_matches_golden` reddens with `epsilon_for(20.0, 200, delta) = 0.0 against the
pinned 2.943225239801352 — relative 1.000e+00`. That observation — not an assumption — is the whole
evidence that the frozen pin is protected against a future edit to `_log_erfc`.

### M-G — series truncated to one term (`S = 1 - 1/(2x**2)`)

**4 DISTINCT tests, 5 node IDs** — the underflow-truth guard, the new row's V-01 and V-02 legs, and
both overflow-regime epsilon legs. Verbatim on the guard no other mutation reaches:

```
_log_erfc(28.01573320140291) = -788.7870752495246 against the committed 60-dps log(erfc(b))
  -788.7870740351563058464846 — relative 1.540e-09 over the measured-plus-margin 1e-15
  (1.214e-06 ABSOLUTE in the log, which is the same figure as the relative error the second term
  of delta_closed inherits)
```

Without this probe that test would ship unwatched.

**Distinct-RED totals: M-A 3, M-B 6, M-G 4.**

## mpmath Provenance (RPT-03 intact)

mpmath 1.3.0 is present only as a **transitive** dependency of torch (torch → sympy → mpmath),
declared in **neither** `pyproject.toml` **nor** `requirements.txt` — verified, and neither file was
touched. Every truth was produced by a one-off `.venv/bin/python -c` shell invocation whose OUTPUT
is committed as a decimal string; the exact invocation, **including which `mp.mpf` form the inputs
took**, is recorded beside each constant. Nothing imports mpmath: the only matches under `grep` are
inside docstrings and comments, and `test_no_phase22_test_imports_mpmath` (AST) plus
`test_reference_fixture_imports_nothing` both pass.

The `mp.mpf(float)` vs `mp.mpf("string")` distinction is real and recorded: measured **8.90e-15**
apart. Both round to the same committed 13-digit literal, so the artifact is unaffected — but a
provenance that does not say which was used is not reproducible.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | **1302 passed, 1 skipped** in 223.58s |
| Baseline at `9960918` | 1280 passed, 1 skipped |
| Delta accounted for exactly | +22 = 18 (inertness sweep) + 1 (count guard) + 1 (underflow truth) + 2 (new row × V-01, V-02) |
| Regressions | **zero** |
| `.venv/bin/ruff check . && ruff format --check .` | All checks passed; 203 files already formatted |
| `git diff --exit-code -- pyproject.toml requirements.txt scripts/` | exit 0 |
| `grep -n "^import \|^from " …/accountant.py` | `82:import math` — only |
| `test_two_oracles_agree` / `test_closed_form_frontier` | 12 passed each |
| `test_log_erfc_is_inert_where_erfc_is_healthy` | 18 passed |
| `test_delta_closed_still_ships_exactly_four_raises` | passed (`_log_erfc` is module-level, so its `raise` is outside `delta_closed`'s FunctionDef) |

## Deviations from Plan

### [Rule 1 — Bug] The plan's own acceptance criterion collided with its action text (`700.0`)

Task 2's action **requires** the docstring to explain "why a liveness assertion was not enough";
its acceptance criterion requires `grep -n "700.0"` to return nothing inside that test. Quoting the
removed assertion is the natural way to satisfy the first and breaks the second.

Resolved for intent, implementing the stronger outcome: **no live assertion** (verified by AST —
the executable body contains *zero* numeric constants) while the docstring keeps the historical
record. The only surviving `700.0` is prose.

### [Rule 1 — Bug] `_inert_points` would have made the new row fail its own meta-guard

As the plan specifies it, `test_log_erfc_is_inert_where_erfc_is_healthy` sweeps "every representable
`DELTA_FRONTIER` row" and asserts `math.erfc(b) > 0.0`. Once Task 2 adds the thirteenth row — which
is *representable* but whose `b` **underflows by design** — that meta-guard fails on the very row
the plan adds. The plan is internally unsatisfiable across its own two tasks.

Fixed by filtering `_inert_points` on `erfc(b) > 0.0` and moving the non-vacuity into a hard-count
companion (`test_log_erfc_inert_points_are_not_empty`, `len == 18` plus hard equality on the single
exclusion). Re-asserting the filter inside the per-point test would have been a tautology wearing a
meta-guard's clothes — the exact failure shape this phase found five times already.

### [Rule 2 — Missing correctness] Two stale bounds the new row falsified

Neither was named by the plan; both became false the moment the thirteenth row landed.

- `phase22_reference.py::WORST_RELATIVE_ERROR` claimed the oracle's worst error "across the whole
  12-row frontier" was 2.7e-12. Re-measured over 13 rows: **1.109e-11**, at the new row. Updated to
  1.2e-11. (Consumed by no test — which is *why* it would have rotted silently.)
- `delta_quadrature`'s `Returns:` block claimed 1.0e-12 over "the eleven representable rows".
  Re-measured over twelve: **1.109e-11**.

### [Rule 2 — Missing correctness] `delta_quadrature`'s `(0, 1]` recorded as not enforced

`delta_quadrature` returning `+inf` and values >1.0 is gap #3 of five, **outside this plan's
closure**. I did not add the refusal (scope). But the plan has me editing that exact docstring
sentence, and re-committing a contract the verifier measured false would be worse than inheriting
it. The block now records the defect, its measured inputs, and that it is another plan's to close.

### Measurement divergence from a briefed reference figure — reported, not smoothed

The brief states series truncation "worst **1.1369e-13** over x ∈ {27.2 … 150}". **Measured here:
7.6366e-13**, at x=150.0. The plan's own text says 7.637e-13 — my measurement reproduces the PLAN
exactly, and 1.1369e-13 is the **ulp of the returned log at |log| ≈ 788**, not the worst absolute
error (at x=150, |log| ≈ 22505 and one ulp is 3.638e-12). The brief's figure appears to be an
ulp reported as an error.

The **conclusion is unaffected**: every error is sub-ulp, so the quantity measured is float64
resolution rather than truncation, and the STOP rule passes.

**Correction, applied 2026-08-26 by the orchestrator after re-measuring.** This paragraph first
recorded the margin as "~13,000x rather than ~100x". That is wrong by three orders of magnitude:
the margin is `1e-11 / 7.6366e-13` = **13.1x**. The worst-error figure (7.6366e-13 at x=150) is
correct and reproduces the plan's own 7.637e-13; only the ratio was mis-stated. Re-measured over
the plan's exact nine-point band:

```
worst ABSOLUTE error over the plan's band: 7.6366e-13 at x=150.0
margin = 1e-11 / 7.6366e-13 = 13.1x
at the b that matters (28.01573320140291): 5.9579e-14   (plan says 6.454e-14)
_log_erfc(1e200) = -inf                                  (required, confirmed)
```

13.1x is a real pass, not a comfortable one — a future change to the truncation rule has about one
order of magnitude of room, not four. Recorded here so no later plan inherits the larger number.
Note also that the worst error over a WIDER sweep (0.5 steps to x≈157) is 4.3344e-12 at x=139.2,
still ~1.2 ulp; the plan's band caps at x=150 and the STOP rule is defined over that band only.

Similarly, my 60-dps `EPSILON_OVERFLOW_REGIME` bisections differ from the briefed values by
**6.6e-17 / 6.8e-17 relative** — under half a float64 ulp, four orders below anything that can
change a verdict. Both are recorded in the constant's provenance rather than silently reconciled.

### Tooling hazard hit — zsh command substitution in a commit message

The Task 2 commit message used backticks inside a double-quoted `-m` string; zsh executed them as
command substitution (`(eval):1: command not found: got`) and **ate four words** from one bullet
("replaces the ␣ liveness assertion"). Every number and claim in the message survived. `--amend` was
blocked twice by the fact-forcing gate even after presenting the required facts, so the message
stands as-is and the correction is recorded here. **Remaining commits used `-F <file>`.**

### `gsd-sdk` handler behaviour, measured this session

All calls used the `--flag` form and every one was followed by `git diff .planning/`. Mixed result —
two documented hazards reproduced, three did **not**, which is worth recording either way:

| Handler | Outcome |
|---|---|
| `roadmap.update-plan-progress --phase 22` | **CORRUPTED** — emitted `\| In Progress\|  \|`: malformed cell padding and an EMPTY date where every sibling row carries one. Counts (12/16) and status correct. The plan checkbox **did** update this time (SUMMARY written first). Hand-repaired. |
| `state.add-decision --summary …` | **CORRUPTED** — wrote `- [Phase ?]: ` instead of `- [Phase 22] `. Also rejects `--decision`; the flag is `--summary`. Hand-repaired. |
| `state.update-progress` | **SILENT NO-OP** — `{"updated": false, "reason": "Progress field not found in STATE.md"}`, though the field is plainly present. No repair needed: `advance-plan` had already left the block correct. |
| `state.advance-plan` | Reported `advanced: false, reason: last_plan` off a **stale 11/11**, yet rewrote the progress block anyway — and the values it wrote are **correct** (44 total, 40 done, phase 22 reopened so completed_phases 3→2). Left the entire "Current Position" body block stale; hand-repaired. |
| `state.record-metric --phase --plan --duration --tasks --files` | **CLEAN** — the `95min` unit survived (prior sessions recorded it being dropped). |
| `state.record-session --stopped-at --resume-file` | **CLEAN** — `stopped_at` updated correctly (prior sessions recorded it going stale). |

`requirements.mark-complete` was **deliberately not called.** `REQUIREMENTS.md:132/342` already marks
DPSGD-03 `[x] SATISFIED` — the row `22-VERIFICATION.md` explicitly measured as unsupported. This plan
improves it but closes only three of five gaps, so re-asserting completion would put the same false
claim back with my own hands. Frontmatter records `requirements-completed: []` and
`requirements-contributed: [DPSGD-03]`; the row is 22-16's to correct once the gap set is closed.

## Known Stubs

None. No hardcoded empties, placeholders, or unwired data paths were introduced.

## Threat Flags

None. No new network endpoint, auth path, file access pattern, or schema at a trust boundary. The
one new module-level function is pure arithmetic over `math`, and the module's import ceiling
(`import math`, asserted statically **and** out-of-process) is unchanged.

## What This Does Not Close

`22-VERIFICATION.md` lists five missing items; this plan closes three. Still open:

- a finiteness check on `mu` in `epsilon_for` after `mu = math.sqrt(steps) / sigma`
  (`epsilon_for(5e-308, 200, 1e-5)` still returns `0.0` — perfect privacy for essentially zero
  noise, the privacy-**understating** direction)
- `delta_quadrature`'s upper-bound refusal plus a condition-1 headroom budget for the Simpson
  **sum** rather than for one `exp` term

SC3 / DPSGD-03's two-oracle agreement is no longer falsified in the band that falsified it, but the
requirement is not fully closed until those two land.

## Self-Check: PASSED

All five claimed files exist on disk; all three commit hashes (`06d9ce9`, `6c4322a`, `f9fab8c`)
resolve in `git log`; and all four frontmatter-claimed symbols/links are present in source —
`def _log_erfc`, `EPSILON_OVERFLOW_REGIME`, the `_log_erfc(b)` key link in `delta_closed`, and the
`775.7866600701457` parametrization link in `test_phase22_accountant.py`.
