---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
reviewed: 2026-08-25T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - src/personacore/privacy/__init__.py
  - src/personacore/privacy/accountant.py
  - src/personacore/privacy/dpsgd.py
  - src/personacore/training/loop.py
  - src/personacore/checkpoint.py
  - scripts/teach_persona.py
  - scripts/mitigation_accountant.py
  - tests/fixtures/phase22_reference.py
  - tests/test_phase20_prereg.py
  - tests/test_phase22_accountant.py
  - tests/test_phase22_checkpoint.py
  - tests/test_phase22_dpsgd.py
  - tests/test_phase22_dpsgd_ast.py
  - tests/test_phase22_fakes.py
  - tests/test_phase22_reference.py
  - tests/test_phase22_wiring.py
findings:
  critical: 4
  warning: 10
  info: 6
  total: 20
status: issues_found
---

# Phase 22: Code Review Report

**Reviewed:** 2026-08-25
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

The mechanism half (`dpsgd.py`, the `dp_fn=`/`fact_bin=` seams, the CLI wiring) is structurally
sound on the axes the phase set out to protect: the clip is genuinely per-record over a global L2
norm across all 72 LoRA tensors, the accumulator holds the SUM, the noise lands on the sum with the
`/N` last, the generator is dedicated and never re-seeded on the step path, and the legacy
`clip_grad_norm_` really does have exactly one reachable call site inside `if dp_fn is None:`. The
full Phase-22 suite is green (232 passed) and `ruff` is clean on every file in scope. I could not
break the per-record sensitivity argument in `dpsgd.py` itself.

**The accountant is where this falls down, and it falls down in three independent places.** Every
finding below is measured against 60-dps `mpmath` ground truth in the project's own venv, not
argued:

1. `epsilon_for` returns **`0.0` — perfect privacy — for a near-zero σ** (CR-01). The guard that is
   supposed to make this impossible carries a docstring proving its own unreachability, and that
   proof rests on a premise (`mu` is finite) that nothing establishes.
2. `delta_quadrature` — the *independent oracle*, the entire basis of DPSGD-03 — **returns `+inf`
   without refusing**, in a band its own condition-1 message names as the failure it exists to
   catch (CR-02).
3. `delta_closed` **silently drops its second term** where `math.erfc` underflows, producing 12.7%
   relative error at exactly the input its own comment cites as reachable on this project's
   frontier (CR-03). The committed `DELTA_FRONTIER` has no row in that band, so the two-oracle
   cross-check never sees it.

Plus one wiring hole: resuming a DP run from a checkpoint without `dp_noise_rng` **silently
replays the noise stream** (CR-04) — the phase's own FAKE 4, reachable through production, in code
whose comment three lines above names that exact consequence and then declines to refuse it.

The evidence trail in the SUMMARYs is unusually honest and several of its self-reported blind spots
(FAKE 3 at σ=0 and accum=1, the one-sided `C*(1+tol)` check, `rng["mps"]` unexercised) are real and
correctly named. What the summaries do **not** cover is the numerical half: no summary measures
`delta_closed` or `delta_quadrature` against ground truth outside the 12 committed rows, and every
one of the four Critical findings lives outside those rows.

---

## Narrative Findings (AI reviewer)

### Critical Issues

#### CR-01: `epsilon_for` reports ε = 0 (perfect privacy) for a near-zero σ

**File:** `src/personacore/privacy/accountant.py:571-576`, with the root cause at `:437-476`

**Issue:** `mu = math.sqrt(steps) / sigma` overflows to `inf` for any `sigma` below
`sqrt(steps)/1.7977e308`. `_delta_or_below_float64` then catches `delta_closed`'s **first** refusal
(the non-finite-input one, whose meaning is "this input is garbage") with a bare
`except ValueError: return None`, and `epsilon_for` reads `None` as "delta is below float64's
range, therefore below the target" and returns **`0.0`**.

Measured in `.venv`:

```
epsilon_for(5e-308,  200, 1e-5) -> 0.0
epsilon_for(1e-310,  200, 1e-5) -> 0.0
epsilon_for(5e-324,  200, 1e-5) -> 0.0     # the smallest positive float64
_delta_or_below_float64(0.0, inf) -> None
```

This is the maximally unsafe direction: a mechanism whose noise standard deviation is `5e-324 * C`
releases the raw clipped sum, and the accountant labels it ε = 0.

`_delta_or_below_float64`'s docstring asserts this cannot happen:

> *"the first two (a non-finite input; `mu <= 0.0`) are **UNREACHABLE from here**: `eps` is
> re-checked finite below, and **`mu` is a finite strictly-positive number** the caller computed
> before entering the loop."*

Nothing establishes that premise. `epsilon_for` checks `sigma` finite and `> 0`, and `steps >= 1`,
but never checks the **quotient**. The companion guard
`test_delta_closed_still_ships_exactly_four_raises` protects the *raise count* the argument rests
on and is structurally incapable of noticing that the argument's other premise never held.

Note the discontinuity this creates at exactly the boundary D-12 argues hardest about: `σ = 0.0`
returns `inf` from an explicit branch, and σ = the next representable float returns `0.0`.

**Fix:**

```python
    mu = math.sqrt(steps) / sigma
    if not math.isfinite(mu):
        # sqrt(steps)/sigma overflowed: sigma is so small the mechanism is effectively
        # deterministic, and no finite eps satisfies delta <= target. Same answer as sigma == 0.
        return math.inf
```

and narrow the swallow so it can only mean what its contract says:

```python
def _delta_or_below_float64(eps, mu):
    if not math.isfinite(eps) or not math.isfinite(mu) or mu <= 0.0:
        raise ValueError(...)          # the two refusals this helper may NOT read as an ordering
    try:
        return delta_closed(eps, mu)
    except ValueError:
        return None
```

---

#### CR-02: `delta_quadrature` returns `+inf` without refusing — the independent oracle can produce a delta above 1

**File:** `src/personacore/privacy/accountant.py:311-318` (condition 1), `:350-356` (the sum),
`:382-390` (condition 3)

**Issue:** Condition 1's negative-`z` clause bounds a **single** `math.exp` call
(`ez < -_EXP_OVERFLOW_ARG`, i.e. `|z| > 37.677`). The Simpson loop then sums **20 001** such terms
with weights up to `4.0`. In the band between "one term fits" and "the sum fits", `integral`
overflows to `+inf`, condition 2's `trunc > rel_tol * inf` is `False`, and condition 3
(`delta <= 0.0`) is one-sided and cannot see an overflow. There is **no** `delta > 1.0` refusal
anywhere.

Measured band (`eps = 1e-6`, sweeping `mu`):

```
mu = 74.975 .. 75.350   ->  z = -37.4875 .. -37.6750  ->  delta_quadrature returns  inf
mu = 75.375 and beyond  ->  z = -37.6875              ->  refused (condition 1)
```

Confirmed at a randomly sampled point too: `delta_quadrature(0.000440884929509763,
75.3129260813192)` returns `inf` against a true delta of `1.0`.

Condition 1's own message names the failure it is missing: *"the separated integral overflows
(z < 0)"*. It fires 0.19 too late in `z`.

This is the module's second oracle. DPSGD-03's entire argument is that it "cannot share the
implementation's failure modes"; an oracle that can return a non-finite delta is not one that can
be compared to anything.

**Fix:** bound the *sum*, not the term, and refuse the upper end of the range:

```python
    # The Simpson sum accumulates n terms with weights up to 4, so the SUM overflows well before
    # any single term does. Budget for it.
    _sum_headroom = math.log(4.0 * n)
    if ez <= -745.0 or (z < 0.0 and ez < -(_EXP_OVERFLOW_ARG - _sum_headroom)):
        raise ValueError(...)
    ...
    delta = _INV_SQRT_2PI * math.exp(ez) * integral
    if not (0.0 < delta <= 1.0):
        raise ValueError(
            f"delta_quadrature({eps!r}, {mu!r}) computed delta = {delta!r}, which is outside "
            f"(0, 1]. delta is a PROBABILITY: a value above 1 (or a non-finite one) means the "
            f"Simpson accumulation overflowed, which the single-term conditioning check above "
            f"cannot see because it bounds one exp and the loop sums {n}."
        )
```

The existing `if delta <= 0.0` branch collapses into that one check.

---

#### CR-03: `delta_closed` silently drops its second term where `erfc` underflows — 12.7% error at an input the module names as reachable

**File:** `src/personacore/privacy/accountant.py:186`

**Issue:**

```python
second = 0.0 if eb == 0.0 else 0.5 * math.exp(eps + math.log(eb))
```

`eb == 0.0` is treated as "the second term is negligible". It is not — it means `math.erfc(b)`
underflowed (measured: `math.erfc(x)` first returns exactly `0.0` at `x = 27.2`). The true second
term is `exp(eps) * Phi(-mu/2 - eps/mu)`, and `exp(eps)` can be astronomically large precisely
where `erfc(b)` is astronomically small — that is the whole reason the line computes it in log
space in the first place. Dropping it is exactly the failure the log-space form was introduced to
prevent, moved one branch to the left.

Measured against 60-dps ground truth at δ = 1e-5, T = 200 — the frontier `sigma_for` walks while
bisecting downward:

| σ | ε | b | `erfc(b)` | `delta_closed` | truth | rel. error |
|---|---|---|---|---|---|---|
| 0.44 | 652.669 | 25.72 | 9.87e-290 | 1.0000000000e-05 | 1.0e-5 | 1.30e-14 |
| 0.43 | 680.159 | 26.25 | 1.11e-301 | 1.0000000000e-05 | 1.0e-5 | 1.34e-14 |
| **0.42** | 709.558 | 26.81 | 1.85e-314 | 1.0000000000e-05 | 1.0e-5 | **1.04e-11** |
| **0.41** | 741.993 | 27.41 | **0.0** | 1.0000000000e-05 | 8.6905e-6 | **13.06%** |
| **0.40** | 775.787 | 28.02 | **0.0** | 1.0000000000e-05 | 8.87030304833e-6 | **12.74%** |

σ = 0.40 / T = 200 is the exact case the line's own comment cites: *"that eps is REACHABLE on this
project's own frontier, not a pathological input: solving epsilon_for at sigma=0.40, T=200 gives
eps = 775.79, and sigma_for walks there while bisecting sigma downward."* `sigma_for`'s `lo`
halving loop evaluates `epsilon_for` at those σ routinely for any large target ε.

The function's stated contract is measurably false there:

> *"``delta`` in ``(0, 1]``, **carrying at least 12 significant digits** of the 60-dps ground truth
> **everywhere this function does not refuse**... the largest deviation over the eleven
> float64-representable rows is 1.84e-12 relative"*

Zero correct significant digits, no refusal, 11 orders past the stated budget.

**Two aggravating facts:**

- The independent oracle is *right* here — `delta_quadrature(775.786660, 35.3553)` returns
  `8.8703030482e-06`, matching truth to 11 digits. The two-oracle cross-check would have caught
  this; it never runs in that band because **no `DELTA_FRONTIER` row has `b > 27.2` with a healthy
  `a`** (the only row past the erfc cliff is `(2.0, 0.05)`, which both oracles refuse and which
  V-02 excludes as `VACUOUS_AGREEMENT_ROW`).
- `test_epsilon_for_survives_the_overflow_regime` parametrizes over exactly σ ∈ {0.40, 0.30} and
  asserts only `isfinite(got)` and `got > 700.0`. It proves the search *returns a number*; it never
  compares it to anything. The returned ε is 775.786660 against a true 774.842722 — 1.2e-3
  relative, in a module whose two published tolerances are both 1e-12.

**Direction, stated honestly:** `second >= 0` always, so dropping it always **over**-states delta,
which makes `epsilon_for` over-state ε. That is the conservative direction, so this is not a live
privacy break. It is still a wrong number from the module whose outputs are the product, and it
makes `GOLDEN_EPSILON_REL_TOL` / `ROUND_TRIP_REL_TOL` meaningless for any future point below
σ ≈ 0.42.

**Fix:** keep the computation in log space through the underflow, using the standard asymptotic:

```python
def _log_erfc(x):
    """log(erfc(x)), valid past the point where erfc itself underflows to 0.0."""
    e = math.erfc(x)
    if e > 0.0:
        return math.log(e)
    if x <= 0.0:                       # erfc(x) -> 2 for x << 0; it never underflows there
        raise ValueError(f"_log_erfc({x!r}): erfc underflowed at a non-positive argument")
    # erfc(x) ~ exp(-x^2)/(x*sqrt(pi)) * (1 - 1/(2x^2) + ...)  for large x > 0
    return -x * x - math.log(x * math.sqrt(math.pi)) + math.log1p(-0.5 / (x * x))

second = 0.5 * math.exp(eps + _log_erfc(b))
```

Then extend `DELTA_FRONTIER` with at least one row in the `b > 27.2` band (e.g. `eps=775.786660,
mu=35.3553`) so V-02 covers it, and give
`test_epsilon_for_survives_the_overflow_regime` a committed truth to compare against instead of a
`> 700.0` liveness check.

---

#### CR-04: resuming a DP run from a checkpoint without `dp_noise_rng` silently replays the noise stream

**File:** `src/personacore/training/loop.py:735-736`

**Issue:**

```python
        if dp_fn is not None and ckpt.get("dp_noise_rng") is not None:
            dp_fn.load_noise_rng_state(ckpt["dp_noise_rng"])
```

There is no `else`. When `dp_fn` is set and the checkpoint lacks the key — a pre-Phase-22
checkpoint, or one written by a `train(dp_fn=None)` run at the same path, i.e. **precisely the
backward-compatibility case the `.get()` exists for** — the restore is skipped silently and
training continues from `ckpt["step"]` with a generator freshly seeded in `DPSGD.__init__`.

The comment eleven lines above states the consequence in the code's own words:

> *"Omitting this restore is not a missing nicety: `DPSGD.__init__` re-seeds its generator from the
> caller's seed, so a resumed run **REPLAYS NOISE IT ALREADY RELEASED** — DPSGD-04/SC4's fourth
> named fake (RNG reused across steps) **reachable through PRODUCTION** rather than by a deliberate
> edit. **D-16 invariant 4 is structurally blind to it** (`_prev_gen_state` is None on a freshly
> constructed object, so the continuity check is vacuous on the first post-resume step), which is
> why this is a WIRING requirement no runtime invariant can cover."*

Every word of that is correct, and the code then permits it without a sound. `DPSGD` cannot cover
it either: `load_noise_rng_state` refuses a *late* restore but nothing anywhere refuses a *missing*
one. Independent noise across the T composed steps is the property the accountant charges for; a
resume that repeats a prefix of the stream means the mechanism that ran is not the one ε describes.

`tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical` exercises only the happy
path, where the key is present.

**Fix:**

```python
        if dp_fn is not None:
            if "dp_noise_rng" not in ckpt:
                raise ValueError(
                    f"{resume_from} carries no 'dp_noise_rng' slot, but this run has a DP seam. "
                    "Resuming would re-seed the dedicated generator from scratch and REPLAY noise "
                    "already released -- FAKE 4 (RNG reused across steps) through production, and "
                    "D-16 invariant 4 is vacuous on the first post-resume step so nothing else "
                    "would notice. Resume a DP run only from a checkpoint a DP run wrote."
                )
            dp_fn.load_noise_rng_state(ckpt["dp_noise_rng"])
```

(`best_val_loss` keeps its `.get()`; the two are not the same kind of key. A missing
`best_val_loss` costs one checkpoint-selection decision; a missing `dp_noise_rng` costs the privacy
claim.)

---

### Warnings

#### WR-01: `begin_step()` re-arms the drain flag without draining, and `absorb_record`'s docstring says it cannot

**File:** `src/personacore/privacy/dpsgd.py:390`, docstring claim at `:413-417`

**Issue:** `absorb_record`'s docstring states:

> *"`_drained` is cleared before anything is read and **set again only by the drain loop at the very
> bottom**, so a refactor that DROPS the drain leaves the flag false and the next record is
> refused."*

`begin_step` also sets it (`self._drained = True`, line 390) without draining anything. Measured on
the real 72-tensor model:

```
p.grad = 0.5 everywhere (stale, from an aborted step)   -> global norm 288.0
dp.begin_step()   -> _drained = True, .grad still present
dp.absorb_record() -> ACCEPTED, records = 1, no refusal
```

In the wired production path `_optimizer_step` calls `optimizer.zero_grad(set_to_none=True)`
immediately before `begin_step()`, so this is currently masked. But D-16's whole framing is
"refuse at the SEAM as a property of the mechanism rather than trusted as a property of one
caller", and here the seam trusts the caller.

**Fix:** make `begin_step` establish the invariant instead of asserting it:

```python
    def begin_step(self):
        for buf in self._accum:
            buf.zero_()
        for p in self._params:
            p.grad = None          # ESTABLISH the drain; do not merely re-assert it
        self._writes = 0
        self._records = 0
        self._drained = True
```

and correct the `absorb_record` docstring sentence.

---

#### WR-02: `sigma * C` can overflow to `inf` with both factors finite — released gradients become `±inf` with no refusal

**File:** `src/personacore/privacy/dpsgd.py:161-194` (the domain pre-pass), `:495` (the draw)

**Issue:** The constructor refuses `clip_norm = inf` with a nine-line argument whose premise is
*"The noise `std` IS `self.sigma * self.C` and cannot be anything else... so an infinite C would
crash the draw at a sigma of zero."* The **product** is never checked. Measured:

```
DPSGD(model, sigma=1e200, clip_norm=1e200)   -> constructs; self.sigma * self.C == inf
finalize(1)                                   -> released .grad is all -inf / +inf
```

`torch.normal(std=inf)` does not raise the way `std=nan` does; it returns `±inf`, which reaches
`optimizer.step()` and poisons every trainable parameter. The refusal that exists for exactly this
class of failure does not cover its own product.

**Fix:** add a fifth domain refusal in pre-pass 1:

```python
        if not math.isfinite(sigma_value * clip_value):
            raise ValueError(
                f"[dp-refusal:std-domain] sigma * clip_norm is "
                f"{sigma_value * clip_value!r}: both factors are finite but their PRODUCT is not, "
                "and that product IS the noise standard deviation. torch.normal(std=inf) returns "
                "+/-inf rather than raising, so every released gradient would be non-finite."
            )
```

---

#### WR-03: `generator=` is adopted with no type or device validation, defeating the stated full-pre-pass contract

**File:** `src/personacore/privacy/dpsgd.py:309-316`

**Issue:** The class docstring promises *"Construction is a FULL PRE-PASS: every refusal below runs
before a single attribute is assigned, so a refusal leaves no half-built DP state behind."* The
`generator` branch adopts whatever it is given:

```
DPSGD(model, sigma=1.0, clip_norm=1.0, generator="not a generator")  -> constructs successfully
```

The failure surfaces at the first `finalize()`, mid-training. The same gap covers the *measured*
D-14 failure mode: a CPU generator with MPS parameters raises
`RuntimeError: Expected a 'mps' device type for generator but found 'cpu'` at the first draw — a
known, recorded incompatibility that the constructor could reject in one line but does not.

**Fix:**

```python
        if generator is not None:
            if not isinstance(generator, torch.Generator):
                raise TypeError(
                    f"[dp-refusal:generator] generator is a {type(generator).__name__}, not a "
                    "torch.Generator. It is adopted AS-IS and never re-seeded, so a wrong object "
                    "surfaces at the first draw -- mid-run -- instead of here."
                )
            if generator.device.type != params[0].device.type:
                raise ValueError(
                    f"[dp-refusal:generator] generator is on {generator.device} but the trainable "
                    f"parameters are on {params[0].device}. MEASURED: a CPU generator filling an "
                    "MPS tensor raises 'Expected a mps device type for generator but found cpu'."
                )
```

Move it into pre-pass 1 so it runs before any attribute is assigned.

---

#### WR-04: `ROUND_TRIP_REL_TOL = 1e-12` is exceeded at reachable inputs, and the round trip is not total

**File:** `src/personacore/privacy/accountant.py:115-124`; test at
`tests/test_phase22_accountant.py:447-463`

**Issue:** The constant's comment claims *"MEASURED ACHIEVABLE: 8.29e-15 worst relative deviation
over 48 (sigma, T) pairs... So this carries a little over two orders of margin."* That is true of
the 48 hand-picked pairs and false as a general bound. Measured on a wider grid at δ = 1e-5:

| σ | T | round-trip relative deviation |
|---|---|---|
| 1 000 | 64 | 5.59e-14 |
| 5 000 | 1 | 9.99e-13 |
| **30 000** | 8 | **1.06e-12** — over budget |
| **100 000** | 64 | **3.88e-12** — over budget |

Separately, the round trip is not total: `epsilon_for(1e5, 1, 1e-5)` returns `0.0` (the mechanism
already meets the target at ε = 0, a documented return), and feeding that back gives
`ValueError: sigma_for(0.0, 1, 1e-05): target_epsilon must be strictly positive`. D-12's stated
guarantee ("`sigma_for(epsilon_for(σ,T,δ),T,δ) == σ` to tolerance, which is free and catches a
divergent inverse") therefore holds on a sub-domain that no docstring names.

**Fix:** state the constant's domain of validity beside it, and name the ε = 0 boundary in
`epsilon_for`'s and `sigma_for`'s `Returns:` sections:

```python
# Valid over sigma <= ~1e4 (measured 9.99e-13 worst at sigma=5e3). Above that the two bisections'
# independent 1e-15 relative brackets compose past 1e-12 -- measured 3.88e-12 at sigma=1e5, T=64.
# NOT a general bound.
ROUND_TRIP_REL_TOL = 1e-12
```

---

#### WR-05: `ZERO_BOUNDARIES["erfc_zero_x"] = 27.5` is measurably wrong and contradicts its sibling entry

**File:** `tests/fixtures/phase22_reference.py:115-117`

**Issue:** The entry is labelled "`math.erfc(x)` **first** returns exactly `0.0` at this x" with the
comment *"Bisected: erfc(27.00) = 5.237046e-319 (a subnormal, still information), erfc(27.50) =
0.0."* That is a two-point sample, not a bisection. Measured:

```
math.erfc(27.0) = 5.23705e-319
math.erfc(27.2) = 0.0            <- already exactly zero
first-zero x, bisected 200x      = 27.199999999999996
```

The same dict's `delta_closed_zero_z = 38.466608897` is `27.2 * sqrt(2)` to 10 digits, so the two
entries contradict each other, and `accountant.py`'s own module docstring says *"`math.erfc`
underflows to exactly `0.0` past x ~ **27.2**"*. The fixture is the outlier.

This matters beyond tidiness: 27.2 is the exact cliff behind CR-03, and a reference table that
places it at 27.5 will steer the next reader past the failure.

**Fix:** `"erfc_zero_x": 27.2,` with the comment corrected to
`erfc(27.19) = 1e-323 (a subnormal), erfc(27.2) = 0.0 -- bisected to 27.199999999999996`.

---

#### WR-06: four committed reference constants have zero consumers, and the fixture docstring names consumers that do not exist

**File:** `tests/fixtures/phase22_reference.py:15-20, 108-122, 175-178, 190, 199`

**Issue:** The fixture's own consumer register claims:

```
  - V-04 ``test_low_privacy_corner``   -> ``DELTA_FRONTIER`` row (8.0, 0.5), ``QUADRATURE_PARAMS``
  - V-05 ``test_oracle_refuses``       -> ``ZERO_BOUNDARIES``
  - V-06 ``test_golden_epsilon_from_oracle`` -> ``EPSILON_GOLDEN``, ``GOLDEN_EPSILON_REL_TOL``
```

Measured references outside the fixture itself:

| constant | external references |
|---|---|
| `QUADRATURE_PARAMS` | **0** |
| `WORST_RELATIVE_ERROR` | **0** |
| `GOLDEN_EPSILON_MEASURED_WORST_REL_GAP` | **0** |
| `ZERO_BOUNDARIES` | **1**, and it is a docstring mention in a test, not a read |

`tests/test_phase22_accountant.py:27` imports exactly `DELTA_FRONTIER, VACUOUS_AGREEMENT_ROW`.
`test_low_privacy_corner` hard-codes its own truth string and calls `delta_quadrature(8.0, 0.5)`
with the defaults; `test_oracle_refuses` hard-codes its three input pairs; the golden check reads
`GOLDEN_EPSILON_REL_TOL` from the **frozen pin**, not from here.

`QUADRATURE_PARAMS = {"lam": 40.0, "n": 20001}` is the sharpest instance: it duplicates
`delta_quadrature`'s hard-coded signature defaults with nothing tying them together, so a change to
either drifts silently — in a fixture whose entire stated purpose is to be a constraint on the code
rather than a photograph of it.

**Fix:** either wire them (`delta_quadrature(8.0, 0.5, **QUADRATURE_PARAMS)` in V-04, and read
`ZERO_BOUNDARIES` in V-05's parametrization) or delete the four constants and the false consumer
lines. Wiring `QUADRATURE_PARAMS` is the higher-value half.

---

#### WR-07: on the DP path `TrainConfig.grad_clip` becomes silently inert

**File:** `src/personacore/training/loop.py:220-228`

**Issue:** `clip_grad_norm_` is now reached only under `if dp_fn is None:`. On a DP arm the mixed
buffer — private noised mean **plus** an entirely un-clipped public replay term — reaches
`optimizer.step()` with nothing bounding it, and `train_cfg.grad_clip` is read by nothing. The
operator gets no warning, no log line and no refusal that a configured value is ignored.

This is a deliberate design decision (D-03, post-processing) and the reasoning in `finalize`'s
docstring is correct. But that same docstring records:

> *"Measured, it is inert BY ACCIDENT rather than by construction... Whether it binds on the REAL
> corpus at 200 overfit steps is **UNMEASURED**."*

So the change from "clipped, and it happened not to bind on a fixture" to "not clipped at all" is
unmeasured on the corpus the DP arms will actually run, and silent.

**Fix:** one line in the DP branch of `_optimizer_step`, or in `train_arm`'s DP provenance print:

```python
    else:
        # D-03: train_cfg.grad_clip is DELIBERATELY not applied on the DP path (the released
        # magnitude must stay independent of public data, and renormalising erases the
        # wrong-sensitivity control's signal). Say so, so it is not read as an oversight.
        dp_fn.finalize(accum)
```

and add `grad_clip=<value> (NOT APPLIED on the DP path, D-03)` to `teach_persona.py`'s DP
provenance line, which is otherwise the run's only record of its own configuration.

---

#### WR-08: `sensitivity_tolerance = 1e-6` has ~3.6x measured headroom over float32 error at the production shape

**File:** `src/personacore/privacy/dpsgd.py:132` (the default), `:463` (the check)

**Issue:** The parameter is documented only as *"absorbing float32 re-summation error only"*, with
no margin recorded. Measured over 180 binding cases on the real 72-tensor / 331 776-parameter
model, with per-tensor gradient scales spanning 10^-4 .. 10^4:

```
worst |clipped_norm / C - 1| = 2.80e-07     against a tolerance of 1e-6
```

A factor of 3.6. `_global_norm` computes 72 per-tensor float32 norms and then a norm of the stack;
a `LoRAConfig.r` bump, a deeper base or a wider gradient dynamic range moves that number, and the
consequence is a spurious `[dp-invariant:sensitivity]` `RuntimeError` that kills a live run. Note
D-04's census refusal exists precisely because a future `r` change is anticipated — the same change
narrows this margin.

**Fix:** record the measurement at the parameter and widen to a value with an order of headroom:

```python
        sensitivity_tolerance: the relative slack in the runtime ``norm <= C * (1 + tol)`` check,
            absorbing float32 re-summation error only. MEASURED at the production shape (72
            tensors / 331,776 params, per-tensor scales over 10^-4..10^4, 180 binding cases): worst
            ``|clipped_norm/C - 1|`` is 2.80e-07, so 1e-5 carries ~36x and 1e-6 only ~3.6x. A
            spurious refusal here kills a live run.
```

---

#### WR-09: `math.sqrt(steps)` raises `OverflowError`, escaping a function documented to raise only `ValueError`

**File:** `src/personacore/privacy/accountant.py:402-413` (the steps refusals), `:571` (the sqrt)

**Issue:** `_refuse_bad_steps_or_delta` checks that `steps` is a non-`bool` `int >= 1` but not that
it is representable as a float. Measured:

```
epsilon_for(1.0, 10**400, 1e-5)  ->  OverflowError: int too large to convert to float
```

Both public functions document `Raises: ValueError` exclusively, and
`test_epsilon_for_domain_refusals` / `test_sigma_for_domain_refusals` both assert
`pytest.raises(ValueError)` — so a caller writing the documented `except ValueError` handler around
the accountant does not catch this.

**Fix:** add a magnitude bound beside the type check:

```python
    if steps > 2**53:
        raise ValueError(
            f"{where}: steps = {steps!r} exceeds 2**53, past which an int is not exactly "
            "representable as a float64 and math.sqrt(steps) raises OverflowError rather than "
            "returning. T is a step budget; nothing in this project composes 9e15 invocations."
        )
```

---

#### WR-10: the frozen pin's `REQUIRED_FORM` contradicts its own `SIGMA_IS_THE_NOISE_MULTIPLIER`

**File:** `scripts/mitigation_accountant.py:136` vs `:300-319`

**Issue:** `REQUIRED_FORM` writes the mechanism as

> `"delta(eps, mu) = Phi(mu/2 - eps/mu) - exp(eps) * Phi(-mu/2 - eps/mu), with **mu = Delta/sigma**"`

while `SIGMA_IS_THE_NOISE_MULTIPLIER`, 160 lines below in the same file, says

> `"`sigma` **EVERYWHERE IN THIS FILE** IS THE NOISE MULTIPLIER: sigma == sigma_noise / C, UNITLESS
> ... mu = Delta/sigma_noise = C/sigma_noise = **1/sigma**"`

and explicitly labels the other reading as *"Any prose **elsewhere** reading 'mu = C/sigma' is
using sigma for the RAW noise std; it is the outlier phrasing"*. Under the file's own stated
convention, `REQUIRED_FORM`'s `mu = Delta/sigma` is wrong by a factor of `C` — and the outlier is
not elsewhere, it is in the same file, in the constant that names the required form.

The file ships five module-scope `_prove` guards (multiplier, relation-string, two composition
proofs, table shape, rejected != required). None compares `REQUIRED_FORM`'s `mu` definition to
`SIGMA_IS_THE_NOISE_MULTIPLIER`'s, which is the one cross-check the pin's own D-18 argument says
matters ("the only check available is that the places STATING it agree").

Nothing consumes `REQUIRED_FORM` as data, so this is a documentation defect rather than a live
arithmetic one — but it is a documentation defect *in a pre-registration*, whose value is entirely
that a later reader can trust its statement of the form.

**Fix:** this file is FROZEN once any `results/phase23_*` artifact is tracked. Per Phase 20 D-24
the correction is a **dated continuation via `scripts/_addendum.py`**, never an in-place edit —
recording that `REQUIRED_FORM`'s `mu = Delta/sigma` uses `sigma` for the raw noise std and that
`SIGMA_IS_THE_NOISE_MULTIPLIER` is the governing definition (`mu = 1/sigma`,
`mu_eff = T**0.5/sigma`). If `results/phase23_*` is still empty, the cheaper fix is to correct the
string now and add a sixth `_prove` asserting `"1/sigma" in SIGMA_IS_THE_NOISE_MULTIPLIER and
"Delta/sigma," not in REQUIRED_FORM`.

---

### Info

#### IN-01: validated values are discarded and re-derived

**File:** `src/personacore/privacy/dpsgd.py:159-160, 295-296`

`sigma_value = float(sigma)` / `clip_value = float(clip_norm)` are computed and checked, then the
assignments call `float(sigma)` / `float(clip_norm)` a second time. Harmless for plain numbers, but
it means the value that was *validated* is not the value that is *stored*.

**Fix:** `self.sigma = sigma_value` / `self.C = clip_value`.

---

#### IN-02: a non-numeric `sigma`/`clip_norm` produces an untagged bare `ValueError`

**File:** `src/personacore/privacy/dpsgd.py:91-94` (the claim), `:159-160` (the gap)

The module docstring: *"Every refusal message carries a bracketed `[dp-refusal:...]` tag naming
which refusal fired."* Measured: `DPSGD(m, sigma="abc", clip_norm=1.0)` raises
`ValueError: could not convert string to float: 'abc'` — no tag, from `float()` before any refusal
runs.

**Fix:** wrap the two conversions in a `try/except (TypeError, ValueError)` that re-raises with
`[dp-refusal:sigma-domain]` / `[dp-refusal:clip-domain]`.

---

#### IN-03: `checkpoint_extra={"dp_noise_rng": ...}` is a mid-run `TypeError` the save-time guard cannot see

**File:** `src/personacore/training/loop.py:876-877, 899-900, 926-927`;
`src/personacore/checkpoint.py:71-85`

`save_checkpoint(..., **(checkpoint_extra or {}), **_dp_extra())` raises
`TypeError: got multiple values for keyword argument 'dp_noise_rng'` if a caller puts that key in
`checkpoint_extra` alongside a `dp_fn`. `_RESERVED_CKPT_KEYS` deliberately excludes `dp_noise_rng`
(it is an `**extra` key by design), so `save_checkpoint`'s own collision guard cannot report it —
the failure arrives as a bare `TypeError` at the first checkpoint interval, after training work is
done.

**Fix:** merge with an explicit check in `train()` before the first save, or refuse
`dp_noise_rng in checkpoint_extra` up front alongside the other entry validations.

---

#### IN-04: `_noise_std_expression` takes the first `torch.normal` in walk order with no "exactly one" meta-guard

**File:** `tests/test_phase22_dpsgd_ast.py:915-925`

V-25's third assertion reads whichever `normal` call `ast.walk` reaches first. Today there is
exactly one (confirmed by AST), and the helper's sibling guards each carry their own meta-guard,
but this one does not — a second draw site inserted earlier in the tree would shadow the pinned
expression and leave the guard green over the wrong call.

**Fix:** collect all matching calls and assert `len(calls) == 1` before returning the `std=` node.

---

#### IN-05: nothing pins `mean=0.0` on the noise draw

**File:** `src/personacore/privacy/dpsgd.py:492`; guard at `tests/test_phase22_dpsgd_ast.py:1000-1027`

V-25 pins the `std=` argument structurally (two-operand `Mult` over `self.sigma` and `self.C`, no
numeric constant) and the AST guards cover the generator, the clip constant and the noise/divide
order. The `mean=` operand is the one argument of the draw that no guard reads. A non-zero mean is
a data-independent shift and therefore DP-preserving, so this is not a privacy hole — but it is a
gap in a set of guards whose stated claim is that the draw's shape is pinned.

**Fix:** extend the same assertion: `mean_node` must be `ast.Constant(0.0)`.

---

#### IN-06: the single-write counter is incremented inside the loop it bounds

**File:** `src/personacore/privacy/dpsgd.py:549-568`

`self._writes += 1` runs inside the `for buf, p, term in zip(...)` loop, and the check is
`self._writes != len(self._params)`. Since `zip` cannot exceed `len(self._params)`, the only
failures reachable are a short `private` list and a double `finalize` without an intervening
`begin_step` (which 22-04 records deliberately). It cannot observe a write performed anywhere
else. The SUMMARY describes it as turning "a single write" from a described sequence into "a
measured count"; the structural half of that claim is actually carried by
`test_dpsgd_step_reaches_no_forbidden_call`'s hard-equality `.grad`-write allowlist, not by this
counter.

**Fix:** none required — but the docstring at `:542` should credit the AST allowlist rather than
implying the counter proves the write is unique.

---

_Reviewed: 2026-08-25_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
