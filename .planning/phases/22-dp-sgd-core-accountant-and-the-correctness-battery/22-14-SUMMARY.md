---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 14
subsystem: privacy
tags: [differential-privacy, accountant, quadrature-oracle, float64-accumulation, mutation-probes, gap-closure, frozen-pin]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-03's src/personacore/privacy/accountant.py::delta_quadrature — the Simpson oracle whose condition 1 and condition 3 this plan repairs"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-12's thirteenth DELTA_FRONTIER row and its `(0, 1] NOT ENFORCED` Returns block — the contract this plan makes true"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-02's scripts/mitigation_accountant.py::GOLDEN_EPSILON — the FROZEN pre-registration this change is proven inert against, bit for bit"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-11's mutation-probe register (real-module mutation, sha256-verified restore, distinct-RED accounting) — the evidence format Task 2 Step 4 follows"
provides:
  - "a delta_quadrature that returns a probability or refuses — never +inf, never above 1.0: condition 1's negative-z clause budgets for the Simpson SUM via math.log(4.0 * n), closing 404 of 4001 measured `inf` cells"
  - "src/personacore/privacy/accountant.py::_DELTA_ACCUMULATION_SLACK — a refusal boundary MEASURED over 5351 answered cells rather than transcribed from a proposal measurement shows would refuse 4.99% of correct answers"
  - "a saturation branch bounded on BOTH sides, so it cannot launder a non-finite delta into a plausible 1.0"
  - "tests/test_phase22_accountant.py::test_quadrature_budgets_the_simpson_sum_not_one_term and ::test_quadrature_returns_a_probability_or_refuses"
  - "a six-mutation register with distinct-RED counts, sha256-identical restores, and — the load-bearing part — a measured explanation for the two mutations that did NOT redden"
affects: [23 the frontier sweep and DPSGD-06, whose mitigation_budget.py is the accountant's first production consumer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A refusal boundary DERIVED from the executor's own 4000+ cell measurement rather than transcribed from the verification's literal, with BOTH numbers recorded so the rejected form stays auditable"
    - "A guard-then-transform pair where the transform is bounded by the SAME constant as the guard, so the transform cannot outlive the guard and launder a value it was never measured for"
    - "Mutation forensics that distinguish 'my guard is blind' from 'the mutation is behaviourally inert', by re-running the ORACLE (not the test) under each mutation"

key-files:
  created: []
  modified:
    - src/personacore/privacy/accountant.py
    - tests/test_phase22_accountant.py

key-decisions:
  - "The verification's literal `if not (0.0 < delta <= 1.0): raise` was NOT shipped. Measured, it refuses 267 of 5351 answered cells — 4.99% — whose true delta is within an ulp of 1.0. The shipped boundary is 1.0 + 1e-11, derived from my own measurement, and both numbers are recorded here and beside the constant"
  - "The over-1.0 excess SATURATES at 1.0 rather than being returned. delta <= 1.0 is a theorem, the excess is a measured float64 artifact bounded at 6.550e-14, and anything outside the slack refuses loudly. That is what makes the `(0, 1]` contract literally true rather than approximately true"
  - "The saturation branch is bounded on both sides (`1.0 < delta <= 1.0 + slack`) rather than written as a bare `delta > 1.0`. Measured with the two upstream guards reverted, the bare form returns a perfectly plausible 1.0 at the cited defect point where the bounded form returns an obvious inf"
  - "M-D was applied as TWO hunks, not one. The plan's `revert the probability check to the shipped one-sided form` means the refusal AND the bare `return delta` that shipped with it; reverting only the refusal is behaviourally inert and correctly leaves the suite green"
  - "The above-slack/non-finite half of condition 3 is UNREACHABLE from any valid input, because condition 1's headroom bound (4*n*max_term) over-estimates the true Simpson sum and therefore refuses BEFORE overflow. It is watched by M-C, where the inf does reach it — not by a live input, and this SUMMARY says so rather than implying a guard that fires in normal operation"

patterns-established:
  - "Measure the proposed fix before shipping it: a verification's `missing:` item is a hypothesis, not a specification"
  - "For every mutation that does NOT redden, measure the ORACLE under it — an inert mutation and a blind guard look identical from the pytest summary line and are opposite findings"

requirements-completed: []
requirements-contributed: [DPSGD-03]

# Metrics
duration: 70min
completed: 2026-08-26
---

# Phase 22 Plan 14: A Probability or a Refusal — Summary

`delta_quadrature` — the independent oracle DPSGD-03's whole correctness argument rests on —
returned `+inf` and values above 1.0 for a quantity that is a probability. Condition 1 now budgets
for the Simpson **sum** rather than for one `exp` term, and condition 3 owns the upper end with a
boundary measured over 5351 cells rather than transcribed from a proposal that measurement shows
would refuse 4.99% of correct answers.

**Commits:** `86ecea8` (Task 1), `6ac602d` (Task 2), `c0b5153` (the bounded saturation, Rule 2).

## The Defect, Reproduced

Every figure below is `.venv/bin/python` output in this tree, at the plan's own sweep:
eps=1e-4, mu ∈ [74.0, 78.0] at a step of 1e-3, **4001 cells**.

| | shipped | after |
|---|---|---|
| `delta_quadrature(0.000440884929509763, 75.3129260813192)` | **`inf`** | refuses (`DOMAIN LIMIT`) |
| cells returning `inf` | **404 of 4001** | **0 of 4001** |
| first `inf` | μ = **74.951** | — |
| first refusal | μ = **75.355** — 0.19 too late in z | μ = **74.753** |
| cells above 1.0 | **461** | **0** (369 saturate at exactly 1.0) |
| answered / refused | 1355 / 2646 | 753 / 3248 |

Condition 1 bounded a SINGLE `math.exp` argument while the loop accumulates `n` of them at weights
up to 4.0 — and a float **addition** that leaves float64 returns `inf` silently rather than raising,
so nothing upstream could see it. `math.log(4.0 * 20001)` = **11.28983191240606**, moving the
negative-z boundary from `-709.782712893384` to `-698.4928809809779` (|z| cliff 37.677 → 37.376).
The budget is computed from the **actual `n` argument**, not the default, because `n` is
caller-supplied.

## The Boundary Is Measured, Not Transcribed

`22-VERIFICATION.md` proposes `if not (0.0 < delta <= 1.0): raise ValueError(...)`.
**That literal form is over-broad and shipping it would have been a new defect.**

Measured, seed **20260826**, **6000 draws** (eps log-uniform in [1e-8, 5.0], mu log-uniform in
[0.01, 200.0]), run *after* Task 1 so the denominator reflects the fixed condition 1:

| Quantity | Measured | Denominator |
|---|---|---|
| answered cells | **5351** | of 6000 draws (649 refused, **0 non-finite**) |
| answered cells strictly above 1.0 | **267** | **4.99% of 5351** |
| largest value returned | **1.000000000000051** | excess **5.10702591327572e-14** = **230 ulp** of 1.0 |
| at | eps=1.685897030034883e-08, mu=71.83418496137618 | |
| median excess | 6.883e-15 | over the 267 |
| smallest excess | 2.220e-16 | exactly 1 ulp |
| worst excess measured **anywhere** | **6.550315845288424e-14** | the μ ∈ [74, 78] sweep, at μ=74.01 |

Those are not broken cells. They are true deltas within an ulp of 1.0 — the ε→0 limit of every
mechanism — wearing the Simpson accumulation's own rounding. `delta_closed` never exceeds 1.0.

**Shipped:** `_DELTA_ACCUMULATION_SLACK = 1e-11`, which is 100× the seeded maximum rounded up to a
decade. Margins, with both denominators stated because ratios are where this phase has slipped
before:

- `1e-11 / 5.10702591327572e-14` = **195.8×** over the seeded maximum
- `1e-11 / 6.550315845288424e-14` = **152.7×** over the worst excess measured anywhere

**Divergence from the briefed reference figures — reported, not smoothed.** The brief states the
max excess as **5.507e-14** over "~270 of 5354". My measurement gives **5.107e-14** over **267 of
5351** — and 5.107e-14 reproduces the PLAN's own figure (`maximum 1.000000000000051, i.e. a maximum
relative excess of 5.107e-14`) exactly, digit for digit. The brief's 5.507e-14 appears to be a
transcription slip of the plan's number; the count/denominator differ by 2/3 cells because the
sample is drawn after Task 1 changed which cells are answerable. The conclusion is unaffected: both
figures round to the same decade and give the same slack.

## The Fix, in Three Parts

**1. Condition 1 budgets for the sum.** `sum_headroom = math.log(4.0 * n)`, subtracted from
`_EXP_OVERFLOW_ARG` in the negative-z clause only. The composite-Simpson weights sum to `3*(n-1)`,
so `4*n` bounds the sum's growth over its largest term. The positive-z clause (`ez <= -745.0`) is a
different limit — every loop term there is `exp(<= 0) <= 1` and no accumulation can overflow — and
is unchanged.

**2. Condition 3 owns both ends.** One check, one message, so the three-distinct-messages shape
holds: `not math.isfinite(delta) or delta <= 0.0 or delta > 1.0 + _DELTA_ACCUMULATION_SLACK`. A
result inside the slack saturates at 1.0. The message keeps everything the old one carried (the
NOT-implied-by-condition-2 argument, the band `38.372164249 < z < 38.6005`, the eps=1.92625 /
mu=0.05 example) and adds what it now covers.

**3. The saturation branch is bounded on both sides** — `1.0 < delta <= 1.0 + slack`, not
`delta > 1.0`. See "Rule 2" below; this is the one thing here the plan did not ask for.

## Nothing That Worked Stopped Working

| Check | Result |
|---|---|
| 12 representable `DELTA_FRONTIER` rows, `delta_quadrature` `float.hex()` before vs after | **all 12 BIT-IDENTICAL**; row 12 (eps=2.0, mu=0.05) still `REFUSED` |
| 7 `GOLDEN_EPSILON` rows via `epsilon_for`, `float.hex()` | **all 7 BIT-IDENTICAL** to the values 22-12 recorded |
| `scripts/mitigation_accountant.py` | sha256 `ae360f36…bb24bb2d`, **byte-unchanged** |
| `pyproject.toml`, `requirements.txt`, `scripts/` | `git diff --exit-code` exit 0 |
| `accountant.py` imports | `['math']` — only, statically and out-of-process |
| `delta_quadrature` refusal messages | **3 fired, 3 DISTINCT** — before and after |
| `raise` statements in `delta_quadrature` | **7** — before and after (the two ends merged into one) |
| `WORST_RELATIVE_ERROR` (22-12's re-measured 1.2e-11) | still bounds: measured **1.1091e-11** over 12 rows, unchanged |
| `test_golden_epsilon_from_oracle` (356 oracle calls, max \|z\| 7.5) | passes unmodified |
| `test_oracle_refuses` | passes unmodified |

The frontier rows are far from both boundaries — the largest delta any of them reaches is
**0.99994**.

Raw `float.hex()` capture, before | after (identical):

```
1.0   1.0    0x1.03f7688204073p-3    | 0x1.03f7688204073p-3
0.5   2.0    0x1.32c87517ac692p-1    | 0x1.32c87517ac692p-1
3.0   0.8    0x1.264659d6dfc00p-14   | 0x1.264659d6dfc00p-14
0.1   4.0    0x1.e783e16ca81a1p-1    | 0x1.e783e16ca81a1p-1
8.0   0.5    0x1.a5485753e0254p-190  | 0x1.a5485753e0254p-190
2.0   0.707  0x1.49cf631f0bea4p-10   | 0x1.49cf631f0bea4p-10
3.3   0.707  0x1.1950035bc28ccp-20   | 0x1.1950035bc28ccp-20
0.5   0.5    0x1.ad97543063fb0p-5    | 0x1.ad97543063fb0p-5
6.0   1.0    0x1.7f291862f1244p-29   | 0x1.7f291862f1244p-29
0.01  8.0    0x1.fff7a7ed3e034p-1    | 0x1.fff7a7ed3e034p-1
2.0   0.1    0x1.83ecbb4e659d2p-301  | 0x1.83ecbb4e659d2p-301
2.0   0.05   REFUSED                 | REFUSED
775.7866600701457 35.35533905932738  0x1.29a352afd5bcbp-17 | 0x1.29a352afd5bcbp-17
```

## Mutations Watched — Including the Two That Did Not Redden

Six mutations, each applied one-shot to the **real committed file** and restored.
`sha256` before every probe and after every restore:
`50598e6899d9361cd4d211514469c62645a7ce8ca62a4843f1c33b745f61cffb`, **equal in all six cases**, and
`git diff --exit-code -- src/personacore/privacy/accountant.py` exited 0 after each.

| # | Mutation | Result | Distinct REDs |
|---|---|---|---|
| **M-C** | remove the `log(4.0 * n)` headroom (restore the single-term bound) | **RED** | **1** — `test_quadrature_budgets_the_simpson_sum_not_one_term` |
| **M-D** | revert the probability check to the shipped one-sided form — **both hunks**: the refusal AND the bare `return delta` | **RED** | **1** — `test_quadrature_returns_a_probability_or_refuses` |
| **M-D-partial** | revert ONLY the refusal, leaving saturation | **GREEN** | 0 — *inert, see below* |
| **M-D-sat** | revert ONLY the saturation, leaving the refusal | **RED** | **1** — `test_quadrature_returns_a_probability_or_refuses` |
| **M-E** | unbound the saturation (`if delta > 1.0`) | **GREEN** | 0 — *inert, see below* |
| **M-C + M-D-partial + M-E** | the compound that laundered `inf` into `1.0` | **RED** | **1** — `test_quadrature_budgets_the_simpson_sum_not_one_term` |

Verbatim REDs:

```
M-C:
E  AssertionError: Regex pattern did not match.
E    Expected regex: 'DOMAIN LIMIT'
E    Actual message: 'delta_quadrature(0.000440884929509763, 75.3129260813192) computed
E    delta = inf, which is not a probability and is therefore provably wrong. ...'

M-D and M-D-sat:
E  AssertionError: delta_quadrature(8.764339700059768e-08, 57.52681775021329) returned
E  1.0000000000000107, which is not in (0, 1]. delta is a probability and delta <= 1.0
E  is a THEOREM, not a tolerance.
E  assert 1.0000000000000107 <= 1.0
```

**M-C's RED is more informative than a bare failure and worth reading.** Under M-C the cited defect
point no longer returns `inf` — condition 3's new non-finite clause catches it and refuses. The test
reddens on the *message*, i.e. it detects that the **wrong condition** fired. That is the direct
evidence that the two fixes are independent layers rather than one fix written twice: with the
headroom gone, `inf` still never escapes, it just gets refused a stage later with the wrong
diagnosis. It is also the ONLY place the above-slack/non-finite half of condition 3 is ever
observed firing — see the honesty note below.

### The two GREEN mutations are INERT, not unwatched — and I measured which

A green pytest summary cannot distinguish "my guard is blind" from "the mutation changed nothing".
So I re-ran the **oracle**, not the test, under each, with a 1500-draw seeded probe plus the cited
defect point:

| Variant | cited defect point | 1500-draw sample |
|---|---|---|
| HONEST (as committed) | REFUSED | 1343 answered / 157 refused / **0 outside (0, 1]** |
| M-D-partial | REFUSED | 1343 / 157 / **0** — *identical* |
| M-E | REFUSED | 1343 / 157 / **0** — *identical* |

Both are behaviourally identical to the honest module on every measured input, so their green is
**correct**: with condition 1's headroom intact no `inf` reaches condition 3, and with the refusal
intact the saturation's upper bound is unreachable. There was nothing to catch. Reporting them as
"caught by nothing" without this measurement would have been the wrong finding.

## Deviations from Plan

### [Rule 1 — Bug] M-D as the plan phrases it is TWO hunks, and applying one leaves the suite green

The plan's M-D reads *"revert the probability check to the shipped one-sided `if delta <= 0.0`"*.
Applied literally as a single-line substitution it does **not** redden — 181 passed — because the
shipped form was `if delta <= 0.0: raise ...` followed by a bare `return delta`, and my
implementation splits the probability check into a refusal and a saturation. Reverting only the
refusal leaves the saturation clamping.

Resolved for intent: M-D reverts **both** hunks, which is what "the shipped one-sided form" is, and
it reddens. The single-hunk version is recorded separately as **M-D-partial** with its own inertness
measurement, because "the plan's mutation as literally written does not fire" is exactly the kind of
finding this phase asks for rather than a detail to quietly fix.

### [Rule 2 — Missing correctness] The saturation branch could launder a non-finite delta

Not named by the plan. `if delta > 1.0: return 1.0` clamps **any** over-1.0 value, and `inf > 1.0`
is `True` — so the branch converts a non-finite delta into a perfectly plausible `1.0` the moment
the refusal above it stops covering that case. Measured at the exact point `22-VERIFICATION.md`
cited, with condition 1's headroom **and** the refusal both reverted:

```
bounded    `if 1.0 < delta <= 1.0 + slack`  ->  returns inf   (obviously wrong)
unbounded  `if delta > 1.0`                 ->  returns 1.0   (perfectly plausible)
```

A plausible-looking number where a refusal belongs is the exact failure this module's own docstring
gives as the reason **both** oracles refuse in the underflow corner. Shipped bounded (commit
`c0b5153`); behaviourally inert today (the table above), costs one comparison.

### [Rule 1 — Bug] The plan's own acceptance criterion collided with its action text

The action requires the Task-1 test to *state* that the probability half belongs to Task 2; the
acceptance criterion requires the test to contain no `<= 1.0`. The natural phrasing of the first
("there is deliberately no `0.0 < delta <= 1.0` assertion here") puts the literal in the docstring
and trips a naive grep of the second — the same shape as 22-12's `700.0` collision. Reworded to
"no probability-range assertion … a `(0, 1]` clause"; `grep -c "<= 1.0"` over the test now returns
**0** and no information is lost.

### The 22-12 `Returns:` block is now updated, as briefed

22-12 deliberately recorded `delta_quadrature`'s `(0, 1]` claim as **NOT ENFORCED**, because the
defect was outside its closure. That paragraph is replaced: the range is now stated as **enforced**,
with both closures and their re-measured evidence (0 of 4001 non-finite; 267 of 5351 above 1.0
refused-or-saturated), and the accuracy claim re-measured today at **1.109e-11** over the twelve
representable rows — unchanged, because none of those rows is near either boundary.

### `gsd-sdk` handler behaviour, measured this session — SEVENTH session in a row

All calls used the `--flag` form; `22-14-SUMMARY.md` was written BEFORE
`roadmap.update-plan-progress`; every call was followed by `git diff .planning/`. Three of the four
documented hazards reproduced **identically** to 22-12 and 22-13.

| Handler | Outcome |
|---|---|
| `state.advance-plan` | **CORRUPTED** — advanced 13→14 correctly in frontmatter, then FLATTENED the body `Status:` prose to `Ready to execute`, destroying the gap-closure status line, and left the `(13/16)` counter in the `Phase:` line stale. Hand-repaired. |
| `state.add-decision --summary` | **CORRUPTED** — wrote `- [Phase ?]: ` instead of `- [Phase 22] `, on **all three** calls. Hand-repaired. |
| `roadmap.update-plan-progress --phase 22` | **CORRUPTED** — emitted `\| In Progress\|  \|`: malformed cell padding and an EMPTY date where every sibling row carries one. Counts (14/16) and status correct, and the plan checkbox **did** update (SUMMARY written first). Hand-repaired. |
| `state.update-progress` | **SILENT NO-OP** — `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has one. No repair needed; `record-metric`/`advance-plan` had already left the block correct. |
| `state.record-metric --phase --plan --duration --tasks --files` | **CLEAN** — the `70min` unit survived, and it also bumped `completed_plans` 41→42. |
| `state.record-session --stopped-at --resume-file` | **CLEAN** — `stopped_at` updated to `Completed 22-14-PLAN.md`. |

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | **1305 passed, 1 skipped** in 223.74 s |
| Baseline (measured fresh at plan start) | 1303 passed, 1 skipped |
| Delta accounted for exactly | **+2** = `test_quadrature_budgets_the_simpson_sum_not_one_term` + `test_quadrature_returns_a_probability_or_refuses` |
| Regressions | **zero** |
| `.venv/bin/ruff check . && ruff format --check .` | All checks passed; **203 files** already formatted |
| `tests/test_phase22_accountant.py` | **181 passed** in 1.9 s |
| `git diff --exit-code -- pyproject.toml requirements.txt scripts/` | exit 0 |
| `grep -c "log(4.0 \* n)" …/accountant.py` | **1** |
| New tests' runtime | band test milliseconds (refusals short-circuit before the loop); probability test **0.60 s** for 240 cells |

## Known Stubs

None. No hardcoded empties, placeholders, or unwired data paths were introduced.

## Threat Flags

None. No new network endpoint, auth path, file access pattern, or schema at a trust boundary. The
module's import ceiling (`import math`, asserted statically **and** out-of-process) is unchanged and
`pyproject.toml` was not touched (RPT-03 intact).

## Honesty Note: What Is and Is Not Watched

The **non-finite / above-slack** half of condition 3 is unreachable from any valid input. Condition
1's headroom bounds the Simpson sum by `4*n*max_term`, which over-estimates the true sum (the
integrand decays away from its peak), so condition 1 refuses **before** the accumulation can
overflow rather than after. That half is therefore defense-in-depth, observed firing only under
M-C — where the `inf` does reach it and it does refuse. It is not a guard that fires in normal
operation, and this SUMMARY says so rather than letting the merged check imply otherwise.

The **saturation** half is live: 269 of 5351 answered cells in the seeded sample and 369 of 753 in
the μ ∈ [74, 78] sweep return exactly 1.0 through it. (269 rather than 267 because two cells already
returned exactly 1.0 before saturation.)

## What This Does Not Close

`22-VERIFICATION.md` lists five missing items. With 22-12's three and this plan's one, **four are
closed**. Still open:

- a finiteness check on `mu` in `epsilon_for` after `mu = math.sqrt(steps) / sigma`
  (`epsilon_for(5e-308, 200, 1e-5)` still returns `0.0` — perfect privacy for essentially zero
  noise, the privacy-**understating** direction)

DPSGD-03 is not fully closed until that lands, and `REQUIREMENTS.md`'s `[x] SATISFIED` row for it
is still unsupported. `requirements.mark-complete` was **deliberately not called**, for the same
reason 22-12 gave: re-asserting completion with my own hands while a measured gap remains would put
the false claim back. Frontmatter records `requirements-completed: []` and
`requirements-contributed: [DPSGD-03]`.

## Self-Check: PASSED

All three claimed files exist on disk; all three commit hashes (`86ecea8`, `6ac602d`, `c0b5153`)
resolve in `git log`; and every frontmatter-claimed symbol is present in source —
`_DELTA_ACCUMULATION_SLACK` (6 occurrences), `math.log(4.0 * n)` (1), and both new test functions
in `tests/test_phase22_accountant.py` (2).
