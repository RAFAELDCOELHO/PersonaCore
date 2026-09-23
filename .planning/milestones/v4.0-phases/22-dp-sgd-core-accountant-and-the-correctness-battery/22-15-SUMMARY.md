---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 15
subsystem: privacy
tags: [differential-privacy, accountant, float64-overflow, exception-swallow, mutation-probes, gap-closure, frozen-pin]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-05's src/personacore/privacy/accountant.py::epsilon_for — the bisection whose unchecked quotient this plan closes, and its explicit sigma == 0.0 branch, whose answer this change makes continuous"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-12's _log_erfc — the fifth ValueError in delta_closed's call tree, now covered by _delta_or_below_float64's reachability argument"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-14's condition-1 headroom and _DELTA_ACCUMULATION_SLACK — the refusals this change sits beside, and its M-D/M-D-partial forensics, the evidence format M-E/M-E-both follows"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-02's scripts/mitigation_accountant.py::GOLDEN_EPSILON — the FROZEN pre-registration this change is proven inert against, bit for bit"
provides:
  - "an epsilon_for that answers +inf, never 0.0, for every sigma whose sqrt(steps)/sigma overflows — the privacy-UNDERSTATING direction closed, and closed CONTINUOUSLY with the sigma == 0.0 branch"
  - "a _delta_or_below_float64 whose docstring premise is a POSTCONDITION OF ITS OWN PROLOGUE rather than an assertion about the caller: it refuses a non-finite or non-positive mu before the try"
  - "a reachability argument extended to 22-12's _log_erfc, with its measurement (erfc first underflows at x = 27.2; erfc(x) >= 1.0 for every x <= 0.0)"
  - "tests/test_phase22_accountant.py::test_epsilon_for_answers_inf_in_the_subnormal_sigma_band — boundary DERIVED per step count from sys.float_info.max, never a hardcoded sigma list"
  - "tests/test_phase22_accountant.py::test_delta_or_below_float64_refuses_the_inputs_it_may_not_read_as_ordering"
  - "a three-mutation register (M-E, M-E-both, M-F) with distinct-RED counts, the verbatim 0.0 observation, and sha256-identical restores"
affects: [23 the frontier sweep and DPSGD-06, whose mitigation_budget.py is the accountant's first production consumer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Validate the DERIVED quantity, not only its operands: two individually-valid inputs can produce an invalid quotient, and the check belongs where the quotient is formed"
    - "A docstring premise turned into a checked postcondition of the same function's prologue, so the argument no longer depends on any caller's behaviour"
    - "A boundary DERIVED per parametrization inside the test (sys.float_info.max is available to the test but banned in the module), so an import ceiling on the module is not paid for with a transcribed constant that is wrong at half the parameters"
    - "A test that pins the branch NEXT DOOR by message, so a future edit cannot extend a new branch upward over a band that is already handled loudly"

key-files:
  created: []
  modified:
    - src/personacore/privacy/accountant.py
    - tests/test_phase22_accountant.py

key-decisions:
  - "The answer is a RETURNED math.inf, NOT a raise — a deliberate deviation from 22-VERIFICATION.md's `refusing rather than falling through`. The defect the verifier named IS a discontinuity (sigma=0 gives inf, the next float gives 0.0); returning inf REMOVES it, a raise would only RELOCATE it to sigma=0 -> inf / next float -> ValueError. inf is also what the sigma == 0.0 branch's own 60-dps argument gives as mu -> inf"
  - "The band's sigmas are DERIVED per step count (boundary/2.0, nextafter(boundary, 0.0), 5e-324) and never hardcoded. 5e-308 is a NORMAL float, not subnormal, and is in band at T=200/1000 while OUT of band at T=1/64 — a literal list is unsatisfiable across the four step counts test_sigma_zero covers"
  - "M-E as the plan phrases it does NOT reproduce the measured 0.0. Deleting the quotient check alone leaves the helper's new refusal to propagate as a ValueError. Both hunks are required, recorded as M-E-both, and the single-hunk result is reported separately rather than smoothed"
  - "M-F leaves the band test GREEN and that green is CORRECT, not blind — measured, the band reads inf at all 12 cells under M-F because the quotient check runs first. The direct helper test is what watches it, which is why the plan asks for one"
  - "The test name keeps the plan's `subnormal_sigma_band` wording, which is a MISNOMER, and says so in its own docstring: at T=1000 the boundary (1.759e-307) sits nearly two decades ABOVE float64's smallest normal. The band is defined by the QUOTIENT overflowing, not by the sigma being subnormal"

patterns-established:
  - "For every mutation the plan specifies, check whether it is one hunk or several before claiming a clean watch — the layers a fix ships in are not always the layers the plan describes"

requirements-completed: []
requirements-contributed: [DPSGD-03]

# Metrics
duration: 45min
completed: 2026-08-26
---

# Phase 22 Plan 15: The Quotient, Checked — Summary

`epsilon_for` published **ε = 0.0 — perfect privacy — for essentially zero noise**. The quotient
`math.sqrt(steps) / sigma` was never checked for finiteness, and a garbage-input refusal was being
read as an ordering fact. The quotient is now checked, the answer is `+inf` continuous with the
σ = 0 branch, and the helper that does the reading refuses the two inputs that would make it false.

**This closes the LAST of the five `missing:` items in `22-VERIFICATION.md`.**

**Commits:** `3cfcc14` (Task 1), `7115bd6` (Task 2).

## The Defect, Reproduced Against HEAD

Every figure below is `.venv/bin/python` output in this tree, Python 3.11.15.

```
epsilon_for(5e-308, 200, 1e-5) = 0.0
math.sqrt(200)/5e-308          = inf
epsilon_for(0.0, 200, 1e-5)    = inf
```

The chain, measured: `mu = inf` reaches `_delta_or_below_float64` → `delta_closed` refuses it with
its **non-finite-input** refusal, whose meaning is *"this input is garbage"* → the bare
`except ValueError` swallows that → the ε = 0 shortcut reads the resulting `None` as *"δ here is
below float64's range, therefore below the target"* → `return 0.0`.

`second >= 0` was 22-12's saving grace; there is none here. **This is the privacy-UNDERSTATING
direction** — the one direction `.planning/research/PITFALLS.md` calls unsound.

## The Boundary Is Derived, and the Verification's Figure Was a Sample

The quotient overflows exactly when `sigma < math.sqrt(steps) / sys.float_info.max`. That boundary
is a **function of `steps`**, so the band's width moves with T:

| T | boundary = `sqrt(T) / sys.float_info.max` | is `5e-308` below it? |
|---|---|---|
| 1 | `5.562684646268003e-309` | **No** — μ finite (2.0e+307) |
| 64 | `4.450147717014404e-308` | **No** — μ finite (1.6e+308) |
| 200 | `7.866824069956795e-308` | **Yes** — μ = `inf` → `0.0` |
| 1000 | `1.7590753387454952e-307` | **Yes** — μ = `inf` → `0.0` |

**Correction to `22-VERIFICATION.md`, recorded with its measurement.** The verification's brief
gives *"widest sigma at T=200 is 4.450147717014403e-308"*. That is the widest σ its **sampling
visited** — it is exactly `2 * sys.float_info.min` — not the boundary. The T=200 boundary is
`7.866824069956795e-308`, 1.77× larger. (`4.4501477170144e-308` is, coincidentally, the T=**64**
boundary to within one ulp.) The verification's conclusion is unaffected; only the width is.

**`5e-308` is a NORMAL float, not a subnormal.** float64's smallest normal is
`2.2250738585072014e-308`. The test name inherits the word "subnormal" from the defect's original
framing and its own docstring corrects it: at T=1000 the boundary sits nearly two decades **above**
the subnormal floor. **A hardcoded sigma list is unsatisfiable** across the four step counts
`test_sigma_zero` covers, which is why every in-band sigma is derived from `boundary` at that T.

Measured behaviour at each edge, all four step counts:

| σ | μ | before | after |
|---|---|---|---|
| `boundary / 2.0` | `inf` | **`0.0`** | `inf` |
| `nextafter(boundary, 0.0)` | `inf` | **`0.0`** | `inf` |
| `5e-324` (smallest positive float64) | `inf` | **`0.0`** | `inf` |
| `nextafter(boundary, 1.0)` | finite, ~1.8e308 | `ValueError` (bracket) | `ValueError` (bracket) — **unchanged** |

The `boundary` value **itself** is asserted by neither direction, and that is measured rather than
cautious: `sqrt(T)/boundary` is `inf` at T=1 and **finite** at T=64, 200 and 1000, because the
division re-rounds. Only strictly-below and strictly-above are decidable.

## Returned `+inf`, Not a Raise — the Deviation, Stated

`22-VERIFICATION.md`'s `missing:` item reads *"A finiteness check on `mu` in `epsilon_for` …
**refusing** rather than falling through"*. **This plan returns `math.inf` instead, deliberately.**

The reason is the verifier's own artifact note: the defect it names is a **discontinuity** —
*"σ=0.0 returns `inf`, the next representable float returns `0.0`"*. A refusal would leave
σ=0 → `inf` and the next float → `ValueError`, which **relocates** the discontinuity rather than
removing it. `math.inf` makes the two branches agree and the discontinuity is gone.

`inf` is also the mathematically correct value, by the identical argument the `sigma == 0.0` branch
eighteen lines above already carries: as μ → ∞ the closed form's first term → 1 and its second → 0,
so δ → 1 for **every** finite ε (measured at 60 dps in that branch's own comment: exactly 1.0 at
μ ≥ 100). No finite ε satisfies a target below 1, so the infimum over admissible ε is `+inf`. A σ
whose quotient overflows is a mechanism releasing a deterministic function of the data, and
(∞, δ)-DP is what that earns.

**A reader of the traceability row must learn of this.** `22-16` summarised this plan without the
return-vs-refuse distinction; the row it writes should carry it.

## The Swallow, Narrowed

`_delta_or_below_float64`'s docstring argued its `except ValueError` could only mean one thing, from
the premise *"`mu` is a finite strictly-positive number the caller computed"* — **and nothing
established it.** The helper now refuses a non-finite or non-positive `mu` before the `try`,
alongside the existing `eps` check, so the premise is a **postcondition of its own prologue** and
holds regardless of any caller.

The paragraph is rewritten to argue from those checks, to name what changed, and — because 22-12
added `_log_erfc`, a **fifth** `ValueError` in `delta_closed`'s call tree from **outside**
`delta_closed`'s FunctionDef — to cover it as a reachability argument **with its measurement**:

```
erfc underflow boundary, bisected: erfc(27.199999999999996) = 1e-323, erfc(27.2) = 0.0
erfc(0.0) = 1.0, erfc(-1e300) = 2.0; min over x <= 0 sampled = 1.0
```

`math.erfc` is monotonically decreasing with `erfc(x) >= 1.0` for every `x <= 0.0`, so
`_log_erfc`'s `x <= 0.0` branch requires an underflow that cannot happen there — unreachable from
**any** call. `delta_closed` reaches `_log_erfc` with `b = (eps/mu + mu/2)/sqrt(2)`, so taking the
series branch already implies `b >= 27.2 > 0`.

The docstring also states, rather than implying otherwise, that
`test_delta_closed_still_ships_exactly_four_raises` counts statements in **one** FunctionDef and is
by construction unable to see either fact — which is why they are a check and a measurement, not a
promise left to it.

### Raise statements, counted before and after

| Function | before | after |
|---|---|---|
| `_log_erfc` | 1 | 1 |
| **`delta_closed`** | **4** | **4** — the guarded count, unmoved |
| `delta_quadrature` | 7 | 7 |
| `_refuse_bad_steps_or_delta` | 5 | 5 |
| **`_delta_or_below_float64`** | 1 | **2** |
| `epsilon_for` | 3 | 3 — it returns, it does not raise |
| `sigma_for` | 4 | 4 |
| **module total** | **25** | **26** |

`test_delta_closed_still_ships_exactly_four_raises` passes, run explicitly.

## The Frozen Pin Did Not Move

Captured by loading `git show HEAD:…/accountant.py` and the working file as two separate modules in
one process and comparing `float.hex()` — not by re-reading transcribed strings.

| Set | Rows | Result |
|---|---|---|
| `GOLDEN_EPSILON` via `epsilon_for` | 7 | **all 7 BIT-IDENTICAL** |
| `DELTA_FRONTIER` via `delta_closed` | 13 | **all 12 representable BIT-IDENTICAL**; row 12 (ε=2.0, μ=0.05) still `REFUSED` |
| `DELTA_FRONTIER` via `delta_quadrature` | 13 | **all 12 representable BIT-IDENTICAL**; row 12 still `REFUSED` |
| **total moved** | | **0** |

```
eps(20.0,               200) 0x1.78bb9acadab46p+1   | 0x1.78bb9acadab46p+1   IDENTICAL
eps(14.142135623730951, 200) 0x1.1823af986dfa6p+2   | 0x1.1823af986dfa6p+2   IDENTICAL
eps(10.0,               200) 0x1.a4ab8aa4dedc6p+2   | 0x1.a4ab8aa4dedc6p+2   IDENTICAL
eps(5.0,                200) 0x1.ee98d4187f954p+3   | 0x1.ee98d4187f954p+3   IDENTICAL
eps(2.0,                200) 0x1.b3035b50de166p+5   | 0x1.b3035b50de166p+5   IDENTICAL
eps(1.0,                  1) 0x1.1823af986dfa6p+2   | 0x1.1823af986dfa6p+2   IDENTICAL
eps(8.0,                 64) 0x1.1823af986dfa6p+2   | 0x1.1823af986dfa6p+2   IDENTICAL
```

**Why it is inert by construction, not by luck:** the new `epsilon_for` branch is reachable only
when the quotient is **non-finite**, and every pinned σ produces a finite μ (the smallest pinned σ
is 1.0). The new helper refusal is reachable only from a non-finite or non-positive μ, which no
pinned point produces. Both branches are unreachable from every point the module already answered.

| Artifact | Result |
|---|---|
| `scripts/mitigation_accountant.py` | sha256 `ae360f36…bb24bb2d`, **byte-unchanged** (identical to 22-14's record) |
| `git diff --exit-code -- pyproject.toml requirements.txt scripts/` | **exit 0** |
| `grep -c "float_info" src/personacore/privacy/accountant.py` | **0** |
| `accountant.py` imports | `math` — only, statically **and** out of process |

## Mutations Watched — Including the One the Plan Got Wrong

Each applied one-shot to the **real committed file**, then `git checkout --`. `sha256` before every
probe and after every restore:
`fcc0b1eaf6c817a52079d620d295e74d98f06a28c16a836809aadfd331585769`, **equal in all three cases**,
and `git diff --exit-code -- src/personacore/privacy/accountant.py` exited **0** after each.

| # | Mutation | Result | Distinct REDs | Node IDs |
|---|---|---|---|---|
| **M-E** | delete the `math.isfinite(mu)` check in `epsilon_for` — **alone** | RED | **1** | 4 |
| **M-E-both** | delete the quotient check **AND** the helper's `mu` refusal | RED | **2** | 9 |
| **M-F** | delete the helper's `mu` refusal — **alone** | RED | **1** | 5 |

### M-E as the plan phrases it does NOT restore the measured `0.0`

The plan requires *"the observed value must be `0.0` — capture that verbatim"*. It is **not** `0.0`.
With the quotient check gone but the helper's refusal intact, that refusal **propagates**:

```
T=1     boundary/2       -> ValueError: _delta_or_below_float64(0.0, inf): mu must be finite and strictly positive here.
T=64    nextafter(b,0)   -> ValueError: _delta_or_below_float64(0.0, inf): mu must be finite and strictly positive here.
T=200   5e-324           -> ValueError: _delta_or_below_float64(0.0, inf): mu must be finite and strictly positive here.
T=1000  boundary/2       -> ValueError: _delta_or_below_float64(0.0, inf): mu must be finite and strictly positive here.
(all 12 (T, sigma) cells identical)
4 failed, 186 passed in 1.83s
```

This is 22-14's M-D finding in a new place: **the two fixes are independent layers, and the plan's
single-hunk mutation only removes one.** It is reported rather than smoothed. The finding is also
substantive — it shows the helper's refusal alone converts a **silent** `0.0` into a **loud** (if
mis-diagnosed) refusal, and that the quotient check is what converts it into the correct
*continuous* answer.

### M-E-both — the defect verbatim

Both hunks. `epsilon_for` returns **`0.0` at all 12 (T, σ) cells**, and the RED carries it:

```
E  AssertionError: epsilon_for(3.9334120349783973e-308, 200, 1e-05) returned 0.0, not +inf — at
   boundary / 2.0, where sqrt(steps)/sigma overflows. A returned 0.0 here is PERFECT PRIVACY for
   essentially zero noise: the privacy-UNDERSTATING direction, and the exact defect
   22-VERIFICATION.md measured at sigma=5e-308, T=200.
E  assert (False)
E   +  where False = <built-in function isinf>(0.0)

9 failed, 181 passed in 1.83s
```

**2 distinct tests, 9 node IDs.** `181 passed` is exactly the pre-Task-2 count for this file, which
is the other half of the evidence: nothing outside the two new tests moved.

### M-F — RED on the helper, GREEN on the band, and the green is CORRECT

```
5 failed, 185 passed in 1.82s
E  Failed: DID NOT RAISE <class 'ValueError'>   (×5: inf, -inf, nan, 0.0, -1.0)
```

**1 distinct test, 5 node IDs.** The band test stays green. Following 22-14's rule — a green pytest
line cannot distinguish a *blind guard* from a *behaviourally inert mutation* — I re-ran the
**function**, not the test, under M-F:

| Variant | band behaviour, 12 (T, σ) cells |
|---|---|
| HONEST (as committed) | `inf` × 12 |
| M-F | `inf` × 12 — **identical** |

M-F is **inert on `epsilon_for`** because the quotient check runs first and the helper is never
reached with a non-finite μ. There is nothing for the band test to catch, which is precisely why
the plan asks for a **direct** call on the private helper — and that test does catch it.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | **1314 passed, 1 skipped** in 221.03 s |
| Baseline (measured fresh at plan start, and 22-14's recorded figure) | **1305 passed, 1 skipped** |
| Delta accounted for exactly | **+9** = 4 (`…subnormal_sigma_band` × T ∈ {1, 64, 200, 1000}) + 5 (`…may_not_read_as_ordering` × μ ∈ {inf, -inf, nan, 0.0, -1.0}) |
| Regressions | **zero** |
| `.venv/bin/python -m pytest tests/test_phase22_accountant.py -q` | **190 passed** in 1.84 s (181 before) |
| `-k "golden or round_trip or four_raises or sigma_zero or domain_refusals or imports_math"` | **95 passed, 86 deselected** |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | All checks passed; **203 files** already formatted |
| `git diff --exit-code -- pyproject.toml requirements.txt scripts/` | exit 0 |
| Post-commit deletion check, both commits | no files deleted |
| Untracked files introduced | none (`.gitignore` was already modified at session start, untouched here) |

`make test` and `make lint` were **not** used: `make test` resolves bare `pytest` to the pyenv
3.12.13 first on PATH and produces ~83 `ModuleNotFoundError: torch`; `make lint` exits 0 over a
different file set. Both are the wrong instrument, per the environment brief.

## Deviations from Plan

### [Deliberate, and the plan says so] Return `math.inf` rather than refuse

`22-VERIFICATION.md`'s `missing:` wording is *"refusing rather than falling through"*. Recorded in
full under **"Returned `+inf`, Not a Raise"** above, with its reasoning: a refusal relocates the
discontinuity the verifier measured instead of removing it, and `inf` is what the σ = 0 branch's own
60-dps argument gives as μ → ∞. The plan mandates this deviation and requires it be recorded; it is
recorded here and it is the single most important line for a reader of the traceability row.

### [Rule 1 — Bug] The plan's M-E is one hunk and needs two

Recorded above with both observations. The plan's acceptance criterion (*"the observed value must
be `0.0`"*) is **not satisfiable** by the mutation it names, because the fix ships as two
independent layers and M-E removes one. Both the single-hunk result (`ValueError` propagating) and
the two-hunk result (`0.0` verbatim) are reported separately, following 22-14's M-D precedent.

### [Rule 2 — Missing correctness] The test name's "subnormal" is a misnomer, corrected in place

The plan's acceptance criterion pins the test's **name**
(`test_epsilon_for_answers_inf_in_the_subnormal_sigma_band`), and the name is wrong: the band is
defined by the **quotient** overflowing, not by σ being subnormal, and at T=1000 the boundary
(`1.759e-307`) is nearly two decades above float64's smallest normal. Renaming would break the
plan's stated criterion for no functional gain and would fork the vocabulary three SUMMARYs have
used. The name is kept and the **docstring states the correction**, with the measurement. Recorded
here so the next reader does not inherit the claim.

### Correction to `22-VERIFICATION.md`'s band width

The brief's *"widest sigma at T=200 is 4.450147717014403e-308"* is the widest σ its sampling
**visited** (`2 * sys.float_info.min`), not the boundary. Measured boundary at T=200:
`7.866824069956795e-308`, **1.77×** wider. Recorded above with the full four-T table.

### `gsd-sdk` handler behaviour, measured this session — EIGHTH session in a row

All calls used the `--flag` form; `22-15-SUMMARY.md` was written **before**
`roadmap.update-plan-progress`; every call was followed by `git diff .planning/`.

| Handler | Outcome |
|---|---|
| `state.advance-plan` | **CORRUPTED** — advanced 14→15 in frontmatter, then FLATTENED the body `Status:` prose to `Ready to execute`, destroying the gap-closure status line, and left the `(14/16)` counter in the `Phase:` line stale. Identical to 22-14. Hand-repaired. |
| `state.add-decision --summary` | **CORRUPTED** — wrote `- [Phase ?]: ` instead of `- [Phase 22] `, on every call. Hand-repaired. |
| `roadmap.update-plan-progress --phase 22` | **CORRUPTED** — emitted malformed cell padding and an EMPTY date where every sibling row carries one. Counts and status correct; the plan checkbox did update (SUMMARY written first). Hand-repaired. |
| `state.update-progress` | **SILENT NO-OP** — `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has one. No repair needed. |
| `state.record-metric --phase --plan --duration --tasks --files` | **CLEAN** — the `45min` unit survived. |
| `state.record-session --stopped-at --resume-file` | **CLEAN**. |

`requirements.mark-complete` was **deliberately not called**, for the third consecutive plan and for
a reason that has now changed shape: `REQUIREMENTS.md` already marks DPSGD-03 `[x] SATISFIED` — the
row `22-VERIFICATION.md` measured as unsupported. All five `missing:` items are now closed, but
re-asserting a completion row **with my own hands** is not this plan's call: it belongs to the
re-verification, and to `22-16`, which owns the traceability correction. Frontmatter records
`requirements-completed: []` and `requirements-contributed: [DPSGD-03]`.

## Known Stubs

None. No hardcoded empties, placeholders, or unwired data paths were introduced. The one hardcoded
float in the new test is `5e-324`, float64's smallest positive value — a **property** of the type,
in band at every T, and it sits behind a meta-guard that asserts the quotient really overflows.

## Threat Flags

None. No new network endpoint, auth path, file access pattern, or schema at a trust boundary. The
module's import ceiling (`import math`, asserted statically **and** out of process) is unchanged;
`sys.float_info` is used only in the test module, where `sys` was already imported.

Register dispositions from the plan's `<threat_model>`, all `mitigate`, all discharged:

| Threat ID | Disposition | Evidence |
|---|---|---|
| T-22-31 | mitigated | Quotient check returning `math.inf`; pinned at 4 step counts × 3 in-band σ; watched under M-E-both with `0.0` captured verbatim |
| T-22-32 | mitigated | `_delta_or_below_float64` refuses non-finite / non-positive μ before the `try`; watched under M-F, 5 node IDs |
| T-22-33 | mitigated | The reachability argument extended to `_log_erfc` with its bisected measurement; `test_delta_closed_still_ships_exactly_four_raises` run explicitly and passing at 4 |
| T-22-34 | mitigated | Boundary derived in the TEST; `grep -c float_info` on the module returns **0**; `test_accountant_imports_math_only` passes |
| T-22-SC | accepted | No installs; `pyproject.toml` and `requirements.txt` asserted byte-unchanged |

## What This Closes

`22-VERIFICATION.md` lists five `missing:` items. 22-12 closed three, 22-14 closed the fourth, and
**this plan closes the fifth and last.** The three measured accountant defects — the dropped
`erfc`-underflow term, `delta_quadrature`'s non-probabilities, and `epsilon_for`'s overflowed
quotient — are all closed, each watched failing under its own mutation.

What that does **not** mean: DPSGD-03's `[x] SATISFIED` row is not this plan's to re-assert. The
verdict is the re-verification's, and the traceability correction is `22-16`'s.

## Self-Check: PASSED

- `src/personacore/privacy/accountant.py` — FOUND
- `tests/test_phase22_accountant.py` — FOUND
- `.planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-15-SUMMARY.md` — FOUND
- commit `3cfcc14` — FOUND in `git log`
- commit `7115bd6` — FOUND in `git log`
- `math.isfinite(mu)` in `accountant.py` — FOUND (the frontmatter `contains:` claim).
  `grep -c` returns **4**, of which **2 are new**: the `epsilon_for` quotient check and the
  `_delta_or_below_float64` refusal. The other two predate this plan (`delta_closed`'s refusal 1,
  `delta_quadrature`'s first input refusal) — stated because a bare count of 4 would otherwise read
  as four new occurrences.
- `test_epsilon_for_answers_inf_in_the_subnormal_sigma_band` — FOUND in
  `tests/test_phase22_accountant.py`
- `test_delta_or_below_float64_refuses_the_inputs_it_may_not_read_as_ordering` — FOUND in
  `tests/test_phase22_accountant.py`
