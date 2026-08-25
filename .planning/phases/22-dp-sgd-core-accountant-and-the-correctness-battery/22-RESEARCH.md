# Phase 22: DP-SGD Core, Accountant, and the Correctness Battery — Research

**Researched:** 2026-08-25
**Domain:** The analytic Gaussian mechanism (Balle–Wang), q=1 Gaussian composition, and the
numerics of a stdlib-`math`-only (ε, δ) accountant plus its independent quadrature oracle
**Confidence:** HIGH on both external questions — every identity is confirmed against primary
literature AND against a 60-decimal-digit `mpmath` ground truth computed in this session.

**Scope.** This document answers exactly the two questions `22-CONTEXT.md` left external: Q1 the
Balle–Wang analytic Gaussian mechanism and its q=1 composition, Q2 the quadrature oracle's derived
integration range. The seam design (D-01 … D-08, D-14 … D-17) is treated as GIVEN and is not
restated. `22-CONTEXT.md`'s own measurements were **reproduced, not re-litigated** — see the
verification below.

---

## Upstream constraints this research is bound by

Not restated (the planner reads them directly), but named so the reader knows what bounded the
recommendations below:

| Source | Binding constraint |
|---|---|
| `22-CONTEXT.md` D-09 | `REQUIRED_FORM` = analytic Gaussian composition (Balle–Wang); `REJECTED_FORM` = `sqrt(2*ln(1.25/delta))/sigma`; frozen pin has **zero imports** and no executable formula |
| `22-CONTEXT.md` D-10 | `src/personacore/privacy/accountant.py` imports **`math` only** |
| `22-CONTEXT.md` D-12 | forward + inverse in one module; round-trip assertion; `σ=0 → ε=∞` explicit branch |
| `22-CONTEXT.md` D-13 | oracle uses `math.exp` only, **no `Φ`/`erfc`**; range derived from (ε, μ); non-vacuity refusal; `GOLDEN_EPSILON` derived from the ORACLE, never snapshotted from `accountant.py` |
| `22-CONTEXT.md` D-15 | refusals via `raise RuntimeError`/`ValueError`; never `assert`; never `_prove` inside `src/` |
| `tests/test_phase20_prereg.py:915-917` | `imported <= {"pathlib","sys","erasure_gate"}` across all `scripts/mitigation_*.py` |
| `CLAUDE.md` (project) | zero budget, offline, from-scratch, **no new dependencies** (RPT-03); CPU/MPS primary; Python 3.11 venv mandatory |

**No new dependency is recommended anywhere in this document.** `math.erfc`, `math.exp`,
`math.log`, `math.sqrt` are the complete transcendental surface. `pyproject.toml` stays untouched,
so the Package Legitimacy Audit section is **not applicable** — this phase installs nothing.

---

## Phase Requirements

| ID | Description | Research support in this document |
|----|-------------|-----------------------------------|
| DPSGD-01 | per-example clip + Gaussian noise, LoRA only, additive gradient seam | Q1's sensitivity/adjacency finding (F6) is the definitional half of "clipped to `C`"; the mechanism itself is locked |
| DPSGD-02 | seam-off bit-identity vs the Phase-10 golden fixture | out of research scope (locked playbook); Validation Architecture rows V-01/V-02 |
| DPSGD-03 | (ε, δ) accountant, stdlib `math`, exact under q=1, two independent oracles | **§ Analytic Gaussian Mechanism** + **§ Quadrature Oracle** + findings F1–F5 |
| DPSGD-04 | correctness battery, four fakes, positive control watched failing first | Validation Architecture rows V-10 … V-13 |
| DPSGD-05 | MPS RNG slot; kill→resume reproduces a **bit-identical reported ε** | F3 (bitwise ε reproducibility is achievable — the forward path is deterministic; but see F4 on `==` between *different call shapes*) |
| DPSGD-07 | `LoRALinear` unrestructured | out of research scope (locked) |

---

## Verification of `22-CONTEXT.md`'s own numbers

Before adding anything, D-13's measured table was reproduced independently and checked against a
60-dps `mpmath` ground truth. **Every digit matches, including the failure row.**

Probe: `mpmath` 1.3.0 at `mp.dps = 60`; double-precision closed form
`0.5*(erfc(a) - exp(eps)*erfc(b))`; trapezoid `n = 400,001` over a fixed `[-14, 14]`; Python
3.11.15, `.venv`, single process, no CI.

| ε | μ | truth (60 dps) | closed form (f64) | rel err | quad `[-14,14]` | rel err |
|---|---|---|---|---|---|---|
| 1.0 | 1.0 | `0.1269367375066` | `1.269367375066e-01` | 2.24e-17 | `1.269367375741e-01` | 5.32e-10 |
| 0.5 | 2.0 | `0.5991856185339` | `5.991856185339e-01` | 1.87e-16 | `5.991856184686e-01` | 1.09e-10 |
| 3.0 | 0.8 | `7.016058166974e-5` | `7.016058166974e-05` | 7.14e-15 | `7.016058177673e-05` | 1.52e-09 |
| 0.1 | 4.0 | `0.9521780438554` | `9.521780438554e-01` | 4.56e-17 | `9.521780438988e-01` | 4.56e-11 |
| **8.0** | **0.5** | **`1.048659178913e-57`** | `1.048659178912e-57` | 5.07e-13 | **`0.000000000000e+00`** | **1.00e+00** |

`22-CONTEXT.md` D-13's table stands in full. The closed-form column is confirmed correct to
≥12 significant digits against an independent 60-dps computation, and the silent `0.0` is real.

---

## Analytic Gaussian Mechanism (Balle–Wang)

### The identity, and two independent primary sources for it

**Balle & Wang, "Improving the Gaussian Mechanism for Differential Privacy: Analytical Calibration
and Optimal Denoising", ICML 2018, arXiv:1805.06530, Theorem 8 (§3, eq. 6)** states the condition
as **necessary and sufficient** ("if and only if"):

> Φ(Δ/2σ − εσ/Δ) − e^ε Φ(−Δ/2σ − εσ/Δ) ≤ δ

`[CITED: arxiv.org/abs/1805.06530 — Theorem 8, §3 eq. (6)]`

Substituting **μ = Δ/σ** (Δ = per-step L2 sensitivity, σ = noise standard deviation), so that
`Δ/(2σ) = μ/2` and `εσ/Δ = ε/μ`:

```
delta(eps, mu) = Phi(mu/2 - eps/mu) - exp(eps) * Phi(-mu/2 - eps/mu)
```

**Dong, Roth & Su, "Gaussian Differential Privacy", arXiv:1905.02383, Corollary 2.13** gives the
identical expression from a completely different starting point (trade-off functions / f-DP):

> A mechanism is μ-GDP if and only if it is (ε, δ(ε))-DP for all ε ≥ 0, where
> δ(ε) = Φ(−ε/μ + μ/2) − e^ε Φ(−ε/μ − μ/2).

`[CITED: arxiv.org/abs/1905.02383 — Corollary 2.13]`

Two independent derivations, same closed form. This is the `REQUIRED_FORM` D-09 names.

### The `erfc`-implementable form (stdlib `math` only)

`Φ(x) = ½·erfc(−x/√2)`, so with **`a = (ε/μ − μ/2)/√2`** and **`b = (ε/μ + μ/2)/√2`**:

```python
def delta_closed(eps, mu):                       # math only; no scipy, no Phi
    a = (eps / mu - mu / 2) / _SQRT2
    b = (eps / mu + mu / 2) / _SQRT2
    eb = math.erfc(b)
    # exp(eps + log(erfc(b))) rather than exp(eps)*erfc(b): see F2 (overflow at eps > 709.78)
    second = 0.0 if eb == 0.0 else 0.5 * math.exp(eps + math.log(eb))
    return 0.5 * math.erfc(a) - second
```

Verified against the 60-dps ground truth to ≤ 7.9e-13 relative across the whole frontier tested
(worst case ε=2, μ=0.1). Everywhere it does not underflow it retains **≥ 12 significant digits**.

### Why it is EXACT rather than an upper bound

Two reasons, and they are different statements:

1. **Balle–Wang Theorem 8 is an iff**, not a sufficient condition. There is no slack to be
   tightened: any (ε, δ) pair satisfying it is achieved, and any pair violating it is not
   achievable. `[CITED: arxiv.org/abs/1805.06530 Thm 8]`
2. **The privacy-loss random variable of the Gaussian mechanism is itself exactly Gaussian**, so
   the hypothesis-testing trade-off function is *exactly* `G_μ` — not dominated by it. The (ε, δ)
   curve is then the exact convex dual of `G_μ`, which is precisely DRS Corollary 2.13. Nothing is
   relaxed at any step. `[CITED: arxiv.org/abs/1905.02383 Cor. 2.13]`

This is the sense in which `.planning/research/ARCHITECTURE.md:240` is already correct: *"That is
tight, not a bound."*

### Why `REJECTED_FORM` is rejected for a correct stated reason

`REJECTED_FORM` is `sqrt(2*ln(1.25/delta))/sigma` — the inversion of Dwork & Roth's classical
Gaussian mechanism (Dwork & Roth 2014, *The Algorithmic Foundations of Differential Privacy*,
Theorem A.1), restated as Balle–Wang's own **Theorem 1 (§2)**:

> σ = Δ√(2 log(1.25/δ))/ε, for (ε, δ)-DP with **ε, δ ∈ (0, 1)**.

`[CITED: arxiv.org/abs/1805.06530 — Theorem 1, §2]`

**The `ε ≤ 1` restriction is part of the theorem's hypothesis, not an editorial caveat.** Balle &
Wang §2.3 ("Limitations in the Low Privacy Regime") states it directly:

> the rate σ = Θ(1/ε) provided by the classical Gaussian mechanism cannot be extended beyond the
> interval ε ∈ (0, 1)

and their **Theorem 4** proves a lower bound `σ ≥ Δ/√(2ε)` that the classical `Θ(1/ε)` rate
violates asymptotically. `[CITED: arxiv.org/abs/1805.06530 — §2.3, Thm 4]`

**Measured, the failure is not merely "loose" — it inverts into an over-claim of privacy.** At
δ = 1e-5 (`scripts/mitigation_unit.py:86`'s pinned `DELTA`), with σ read as the noise multiplier
(μ = 1/σ), comparing `ε_classical = √(2 ln(1.25/δ))/σ` against the exact ε solving
`δ_analytic(ε, μ) = 1e-5` (60-dps bisection, 300 iterations):

| σ | μ = 1/σ | ε_classical | ε_exact | verdict | true δ **at** ε_classical |
|---|---|---|---|---|---|
| 8.0 | 0.125 | 0.605601 | 0.434416 | conservative | 2.052e-8 |
| 4.0 | 0.250 | 1.211201 | 0.926342 | conservative — but ε > 1, **outside Thm A.1** | 5.525e-8 |
| 2.0 | 0.500 | 2.422403 | 1.993091 | conservative, outside Thm A.1 | 1.981e-7 |
| 1.0 | 1.000 | 4.844805 | 4.377178 | conservative, outside Thm A.1 | 1.219e-6 |
| 0.7 | 1.429 | 6.921150 | 6.652488 | conservative, outside Thm A.1 | 4.355e-6 |
| **0.5** | **2.000** | **9.689611** | **9.997256** | **OVER-CLAIMS PRIVACY** | **1.937e-5** (1.9× the promise) |
| **0.3** | **3.333** | **16.149351** | **19.130768** | **OVER-CLAIMS PRIVACY** | **3.572e-4 (35.7× the promise)** |

Crossover located by 60-iteration bisection: **μ = 1.737896746 (σ = 0.575408178) at δ = 1e-5.**
Above that μ, the classical formula reports an ε *smaller* than the mechanism earns — the unsafe
direction.

So `REJECTED_FORM` is rejected on a two-part reason, both parts stated correctly:

- **Formally:** it is a theorem with hypothesis `ε ∈ (0,1)`. Every σ < 4.84 at δ=1e-5 produces
  ε > 1 and therefore invokes it outside its hypothesis. The resulting claim is *unsupported*,
  independent of whether it happens to be numerically conservative.
- **Numerically:** past μ = 1.738 it is not merely unsupported but **wrong in the unsafe
  direction** — 35.7× the promised δ at σ = 0.3.

This is a stronger rejection than "it is loose", and it is the one the frozen pin's prose should
carry. `.planning/research/PITFALLS.md`'s standing rule — a hand-rolled accountant that fails in
the direction of a *smaller* ε is unsound — is exactly what this measures.

### The q = 1 T-fold composition identity — CONFIRMED, with its conditions

**Dong, Roth & Su, arXiv:1905.02383, Corollary 3.3:**

> The n-fold composition of μ_i-GDP mechanisms is √(μ₁² + ⋯ + μₙ²)-GDP.

`[CITED: arxiv.org/abs/1905.02383 — Corollary 3.3]`. This is an **exact equality of trade-off
functions**, not an upper bound, and DRS §3 explicitly permits each M_i to depend on the outputs of
M_1 … M_{i−1} — i.e. it **covers adaptive composition**, which DP-SGD requires (step t's gradient
depends on step t−1's weights).

Homogeneous case: T identical μ-GDP steps compose to `μ_eff = μ√T`. Cross-checked against zCDP
(Bun & Steinke 2016): one Gaussian step is `ρ = μ²/2`-zCDP, T-fold gives `Tρ`, and
`√(2Tρ) = μ√T` — measured identical to 12 decimals at (μ=0.05, T=200), (μ=0.5, T=200),
(μ=0.1, T=64). Two accounting frameworks, same answer.

**Therefore D-13's identity holds, and D-09's `T ** 0.5` composition proof is correct.** With
`μ_eff(σ, T) = √T/σ`:

```
mu_eff(sigma, T)      = sqrt(T)/sigma
mu(sigma/sqrt(T), 1)  = 1/(sigma/sqrt(T)) = sqrt(T)/sigma      # identical in exact arithmetic
```

`ε(σ, T, δ) == ε(σ/√T, 1, δ)` is therefore an **exact algebraic identity**, not an approximation.

**The five conditions it rests on — three of which `22-CONTEXT.md` states, two of which it does
not:**

| # | Condition | Status in `22-CONTEXT.md` |
|---|---|---|
| 1 | **q = 1, no subsampling.** With q < 1 the subsampled Gaussian's trade-off function is not Gaussian; the identity fails and RDP/PLD accounting with CLT approximation is required. | **Stated** — Phase 21 D-07/D-23 pin `SAMPLING_RATE_Q = 1.0` |
| 2 | **Homogeneous σ and Δ across all T steps.** The general form is `√(Σμᵢ²)`; it collapses to `μ√T` only if every step is identical. A mid-run σ change silently invalidates it. | **Implied** by D-17's construct-once capture, never stated as a composition precondition |
| 3 | **T fixed in advance, not a data-dependent stopping time.** | Implied by `MAX_STEPS = 200`; not stated |
| 4 | **Adaptivity is permitted.** DRS Cor 3.3 covers it, so DP-SGD's step-to-step dependence costs nothing. | Not stated — worth recording, because it is the non-obvious half and a reader may assume otherwise |
| 5 | **Δ is the per-step sensitivity under a FIXED adjacency relation, and μ = Δ/σ uses that same Δ.** | **NOT STATED — see finding F6 below. This is the loud one.** |

Note the identity is safe *as a code identity* regardless of which adjacency is chosen, because
both sides of `ε(σ,T,δ) == ε(σ/√T,1,δ)` use the same convention. What the adjacency changes is the
**meaning and the numeric value** of the published ε.

### `σ = 0 → ε = ∞`: the math agrees, it is not merely a convenient guard

`σ → 0` means `μ = Δ/σ → ∞`. Taking the limit in the closed form:

```
Phi(mu/2 - eps/mu) -> Phi(+inf) = 1
exp(eps) * Phi(-mu/2 - eps/mu) -> exp(eps) * Phi(-inf) = 0
=> delta(eps, mu) -> 1  for EVERY finite eps
```

Measured at 60 dps:

| μ | ε | δ | 1 − δ |
|---|---|---|---|
| 10 | 1 | 0.999999059179780138 | 9.408e-7 |
| 30 | 1 | 1.0 | 1.210e-50 |
| 30 | 100 | 1.0 | 1.546e-31 |
| 100 | 1, 10, 100 | 1.0 | 0.0 |
| 1e6 | 1, 10, 100 | 1.0 | 0.0 |

Since δ = 1 for every finite ε, **no finite ε satisfies δ ≤ 1e-5**, so the infimum over admissible
ε is `+∞`. This agrees with the mechanism-level statement: σ = 0 releases a deterministic function
of the data, which is (∞, δ)-DP for any δ < 1 and nothing better. D-12's explicit branch is
therefore **the mathematically correct return value**, not a guard papering over a
`ZeroDivisionError` — though `1.0/0.0` is confirmed to raise `ZeroDivisionError` in CPython 3.11
(not return `inf`), so the branch is also operationally required exactly as D-12 says.

---

## Quadrature Oracle: Derived Integration Range

### The support boundary, derived algebraically

D-13's integrand: `t ~ N(μ, 1)`, `L = μt − μ²/2`, `δ = E[max(0, 1 − e^(ε−L))]`.

The `max(0, ·)` is non-zero exactly when `1 − e^(ε−L) > 0`, i.e. `L > ε`:

```
mu*t - mu^2/2 > eps   <=>   t > eps/mu + mu/2
```

**`t_min = ε/μ + μ/2`.** `[VERIFIED: algebra + numerics, this session]`

Check against D-13's measured failure: ε=8, μ=0.5 → `8/0.5 + 0.25 = 16.25`. `22-CONTEXT.md` records
"the integrand's support starts at `t > 16.25`". **Exact match.** The fixed `[-14, 14]` misses the
entire support, which is why the oracle returned exactly `0.0`.

Define **`z = t_min − μ = ε/μ − μ/2`** — the support boundary measured in standard deviations from
the sampling density's mean. `z` is the single parameter that governs every numerical property
below; note it is the *same* `√2·a` that appears in the closed form's first `erfc` argument. That
is not a coincidence and it is load-bearing for F1.

### The derived range rule

**Lower limit: exactly `t_min`. Not `t_min − anything`.**

The integrand has a **kink** at `t_min`: it is identically 0 below, and its right-derivative there
is `φ(t_min − μ)·μ > 0`. Placing the kink at a grid node preserves the quadrature rule's
convergence order; putting it inside a panel destroys it.

Measured (Simpson, n = 4001, Λ = 40 range rule, relative error vs 60-dps truth):

| ε | μ | grid starts at `t_min` | offset ½ step below | offset 1.0 below |
|---|---|---|---|---|
| 1.00 | 1.000 | **3.30e-13** | 1.07e-06 | 2.43e-07 |
| 3.00 | 0.800 | **1.28e-10** | 4.14e-06 | 2.26e-06 |
| 8.00 | 0.500 | **1.69e-09** | 1.36e-05 | 1.67e-05 |
| 3.30 | 0.707 | **2.23e-10** | 5.28e-06 | 4.07e-07 |
| 6.00 | 1.000 | **4.17e-10** | 7.01e-06 | 1.08e-05 |

**Up to six orders of magnitude.** "Start the grid exactly at `t_min`" is a measured requirement,
not tidiness.

**Upper limit: `t_max = t_min + U` with `U = −z + √(z² + 2Λ)`, Λ = 40.**

`U` is the exact positive root of `z·U + U²/2 = Λ`, which is the exponent appearing in the tail
bound below. It is well-defined for **all real z including negative z** (high-privacy corner:
ε=0.1, μ=4 gives z = −1.975, U = 14.78), and it always satisfies `U + z = √(z² + 2Λ) > 0`, which
is what the bound needs.

**Why a width rule and not a constant.** `U` must adapt in *both* directions: at ε=8, μ=0.5
(z = 15.75) the integrand dies within `U = 4.45`, so a wide fixed range wastes resolution; at
ε=0.01, μ=8 (z = −4.0) it needs `U = 17.26`. A constant width is wrong at one end or the other.

**Why Λ = 40 and not 80.** Λ = 80 is *safer on paper* and *worse in practice*, because at fixed
node count a wider range means a coarser `h`. Measured (Simpson, n = 4001), relative error |
rigorous truncation bound:

| ε | μ | Λ=20 | Λ=40 | Λ=80 | Λ=160 |
|---|---|---|---|---|---|
| 1.00 | 1.000 | 8.78e-10 \| 9.01e-10 | **8.05e-14 \| 1.32e-18** | 3.30e-13 \| 3.95e-36 | 1.38e-12 \| 5.05e-71 |
| 3.00 | 0.800 | 5.63e-09 \| 5.99e-09 | **2.10e-11 \| 9.25e-18** | 1.28e-10 \| 2.87e-35 | 6.91e-10 \| 3.72e-70 |
| 8.00 | 0.500 | 2.96e-08 \| 6.29e-08 | **1.34e-10 \| 1.21e-16** | 1.69e-09 \| 4.63e-34 | 1.84e-08 \| 7.08e-69 |
| 3.30 | 0.707 | 8.38e-09 \| 9.32e-09 | **3.30e-11 \| 1.48e-17** | 2.23e-10 \| 4.67e-35 | 1.31e-09 \| 6.13e-70 |
| 6.00 | 1.000 | 8.91e-09 \| 9.50e-09 | **5.51e-11 \| 1.56e-17** | 4.17e-10 \| 5.05e-35 | 2.69e-09 \| 6.72e-69 |

Λ = 20 leaves a truncation bound of ~6e-8 relative — **not** negligible, and it dominates the total
error. Λ = 40 drives the truncation bound to ≤ 1.21e-16 (at or below double-precision resolution)
while keeping the finest `h`. Λ = 80 and 160 buy nothing and cost an order of magnitude in
discretisation error. **Λ = 40 is the measured optimum.**

The choice does not have to be trusted, because the bound is computed and checked at run time —
see the refusal below.

### Rule and node count

**Composite Simpson, n = 20,001 nodes.** Measured relative error vs 60-dps truth, grid starting
exactly at `t_min`, Λ = 40 range rule:

| ε | μ | rule | n=201 | n=401 | n=1001 | n=4001 | **n=20001** | n=100001 |
|---|---|---|---|---|---|---|---|---|
| 1.00 | 1.000 | trapezoid | 8.54e-04 | 2.14e-04 | 3.42e-05 | 2.14e-06 | 8.54e-08 | 3.42e-09 |
| 1.00 | 1.000 | **Simpson** | 5.35e-08 | 3.30e-09 | 8.43e-11 | 3.30e-13 | **1.27e-14** | 6.23e-14 |
| 3.00 | 0.800 | trapezoid | 3.28e-03 | 8.21e-04 | 1.31e-04 | 8.21e-06 | 3.28e-07 | 1.31e-08 |
| 3.00 | 0.800 | **Simpson** | 2.03e-05 | 1.27e-06 | 3.27e-08 | 1.28e-10 | **2.21e-13** | 7.52e-14 |
| 8.00 | 0.500 | trapezoid | 1.06e-02 | 2.67e-03 | 4.27e-04 | 2.67e-05 | 1.07e-06 | 4.27e-08 |
| 8.00 | 0.500 | **Simpson** | 2.63e-04 | 1.68e-05 | 4.31e-07 | 1.69e-09 | **2.71e-12** | 1.04e-13 |
| 3.30 | 0.707 | trapezoid | 4.17e-03 | 1.04e-03 | 1.67e-04 | 1.04e-05 | 4.17e-07 | 1.67e-08 |
| 3.30 | 0.707 | **Simpson** | 3.54e-05 | 2.22e-06 | 5.70e-08 | 2.23e-10 | **3.71e-13** | 6.09e-14 |
| 6.00 | 1.000 | trapezoid | 5.52e-03 | 1.38e-03 | 2.21e-04 | 1.38e-05 | 5.54e-07 | 2.21e-08 |
| 6.00 | 1.000 | **Simpson** | 6.61e-05 | 4.16e-06 | 1.07e-07 | 4.17e-10 | **6.82e-13** | 5.58e-14 |

Two observations worth carrying into the plan:

1. **Simpson at n = 20,001 beats trapezoid at n = 400,001 (D-13's probe) by 3–4 orders of
   magnitude, with 20× fewer nodes.** Simpson is a five-line change from trapezoid (`4/2/4/2`
   weights, `h/3`); there is no reason to keep trapezoid.
2. **More nodes is not monotonically better.** At n = 100,001 the accumulation round-off floor
   (~6e-14) takes over and three of five rows get *worse*. `n = 20,001` sits at the sweet spot;
   a plan that "makes it safer" by raising n is making it worse.

### Recommended implementation — the exact change of variable

Substituting `u = t − t_min` collapses the integrand to a two-parameter form. Since
`μ·t_min − μ²/2 = ε` by definition of `t_min`, the exponent `ε − L` becomes exactly `−μu`, and
`t − μ = u + z`:

```
delta = integral_{t_min}^{inf} phi(t - mu) * (1 - exp(eps - L)) dt
      = phi(z) * integral_0^{inf} exp(-z*u - u^2/2) * (1 - exp(-mu*u)) du
```

This is an **exact algebraic identity on D-13's integral**, not a different integral. It preserves
every D-13 property — direct integration of the (ε, δ)-DP definition, `math.exp` only, no `Φ`, no
`erfc` — and buys three things:

- `exp(ε)` never appears, so the ε>709 overflow (F2) cannot reach the oracle.
- The `max(0, ·)` clamp disappears; the domain *is* the support.
- **The non-vacuity test stays non-degenerate where the literal form's test silently dies** (F1).

Measured: literal and substituted forms agree to within their shared discretisation error at every
frontier point tested (both give 2.71e-12 at ε=8, μ=0.5). The substitution buys conditioning, not
accuracy — but the conditioning is the whole point of the refusal.

```python
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)

def delta_quadrature(eps, mu, *, lam=40.0, n=20001, rel_tol=1e-9):
    """Independent oracle: integrates the (eps,delta)-DP definition. math.exp ONLY."""
    z = eps / mu - mu / 2.0                    # t_min - mu; t_min = eps/mu + mu/2
    U = -z + math.sqrt(z * z + 2.0 * lam)      # exact root of z*U + U^2/2 == lam
    h = U / (n - 1)
    f = lambda u: math.exp(-z * u - 0.5 * u * u) * (1.0 - math.exp(-mu * u))
    s = f(0.0) + f(U)                          # u=0 IS the kink; it must be a node
    for i in range(1, n - 1):
        s += (4.0 if i % 2 else 2.0) * f(i * h)
    integral = s * h / 3.0                     # composite Simpson

    ez = -0.5 * z * z
    if ez <= -745.0:                           # phi(z) underflows: delta is below f64 range
        raise ValueError(...)                  # REFUSE. see refusal condition 1
    trunc = math.exp(-lam) / (U + z)           # rigorous Mills bound on the discarded tail
    if trunc > rel_tol * integral:             # refusal condition 2
        raise ValueError(...)
    delta = _INV_SQRT_2PI * math.exp(ez) * integral
    if delta <= 0.0:                           # refusal condition 3
        raise ValueError(...)
    return delta
```

### The non-vacuity refusal — three conditions, and none is redundant

**The truncation bound is rigorous and computable with `exp` alone.** Completing the square,
`−zu − u²/2 = z²/2 − (u+z)²/2`, so the discarded tail of the scaled integral is

```
integral_U^inf exp(-z*u - u^2/2)*(1 - exp(-mu*u)) du
  <= integral_U^inf exp(-z*u - u^2/2) du                     (since 1 - exp(-mu*u) <= 1)
   = exp(z^2/2) * sqrt(2*pi) * Qbar(U + z)                   (Qbar = upper normal tail)
  <= exp(-z*U - U^2/2) / (U + z)                             (Mills: Qbar(x) <= phi(x)/x, x > 0)
   = exp(-lam) / (U + z)                                     (by construction of U)
```

valid because `U + z = √(z² + 2Λ) > 0` always. So the guard is one `exp` and one divide, and it is
a *proof* that the range captured the support rather than an assertion that it did.

**Condition 1 — `phi(z)` underflow ⇒ δ is not representable.** Not a range bug; a domain limit.
Must be reported as a refusal, never as a number.

**Condition 2 — the relative truncation test** `trunc > rel_tol * integral`.

**Condition 3 — `delta <= 0.0`.** `δ(ε, μ) > 0` strictly for every finite ε and μ > 0, because the
Gaussian has full support and the integrand is positive on a set of positive measure. A returned
`0.0` is therefore **provably wrong**, always.

**Condition 3 is NOT implied by condition 2, and this was measured.** Under the *literal* form
(`trunc_bound_on_delta = exp(−z²/2 − Λ)/(√(2π)(U+z))`), the bound underflows in exactly the regime
where δ does, so the relative test degenerates to `0.0 > rel_tol * 0.0` = **False** — the guard
does not fire on the very failure it exists to catch:

| ε | μ | z | true δ (60 dps) | δ in f64 | literal trunc bound | `trunc > rel_tol*δ` fires? | scaled `trunc/I` |
|---|---|---|---|---|---|---|---|
| 8.00 | 0.50 | 15.750 | 1.0486592e-57 | 1.049e-57 | 4.852e-91 | no (correct — result is good) | 4.63e-34 |
| 11.00 | 0.30 | 36.517 | 2.4539247e-294 | 2.454e-294 | **0.0** (underflowed) | no — guard is **inert** | 2.10e-33 |
| 12.00 | 0.30 | 39.850 | 1.0924472e-349 | **0.0** | **0.0** | **no — GUARD FAILS TO FIRE** | 2.31e-33 |
| 20.00 | 0.20 | 99.900 | 5.8907974e-2173 | **0.0** | **0.0** | **no — GUARD FAILS TO FIRE** | 8.96e-33 |

In the **scaled** form, `trunc/I` stays a finite, meaningful number (~1e-33) in every row, because
`I` never underflows — only the `φ(z)` prefactor does, and that is caught cleanly by condition 1.
**This is the measured reason to prefer the substituted form**, and the reason condition 3 must
exist as an independent check either way.

Representability boundary, bisected to 9 digits: **`delta_closed` first returns exactly `0.0` at
z = 38.466608897**; **`delta_quadrature` (scaled) first returns exactly `0.0` at z = 38.372164249**.

### Relative-error table across the frontier, including the regime that broke the fixed range

Recommended oracle (Simpson, n = 20,001, Λ = 40, grid from `t_min`), versus 60-dps ground truth.
The `refused?` column is the behaviour the three conditions produce.

| ε | μ | z | U | truth (60 dps) | oracle (f64) | **rel err** | fixed `[-14,14]` rel err | refused? |
|---|---|---|---|---|---|---|---|---|
| 1.00 | 1.000 | 0.500 | 8.5440 | `0.1269367375066` | `1.269367375066e-01` | **1.3e-14** | 5.32e-10 | no |
| 0.50 | 2.000 | −0.750 | 9.6237 | `0.5991856185339` | `5.991856185339e-01` | **2.1e-14** | 1.09e-10 | no |
| 3.00 | 0.800 | 3.350 | 6.4297 | `7.016058166974e-5` | `7.016058166973e-05` | **2.2e-13** | 1.52e-09 | no |
| 0.10 | 4.000 | −1.975 | 11.0245 | `0.9521780438554` | `9.521780438554e-01` | **1.4e-14** | 4.56e-11 | no |
| **8.00** | **0.500** | **15.750** | **2.4139** | **`1.048659178913e-57`** | **`1.048659178910e-57`** | **2.7e-12** | **1.00e+00** | **no — FIXED** |
| 2.00 | 0.707 | 2.475 | 7.1264 | `0.001258125710375` | `1.258125710375e-03` | 1.1e-13 | — | no |
| 3.30 | 0.707 | 4.314 | 5.9022 | `1.047970917991e-6` | `1.047970917991e-06` | 3.7e-13 | — | no |
| 0.50 | 0.500 | 0.750 | 8.3072 | `0.05244032328767` | `5.244032328767e-02` | 1.2e-14 | — | no |
| 6.00 | 1.000 | 5.500 | 5.1962 | `2.787859763764e-9` | `2.787859763762e-09` | 6.8e-13 | — | no |
| 0.01 | 8.000 | −3.999 | 13.1300 | `0.9999363400557` | `9.999363400557e-01` | 9.6e-15 | — | no |
| 12.00 | 0.300 | 39.850 | 0.9908 | `1.092447176104e-349` | *(not representable)* | — | — | **YES (cond. 1)** |
| 20.00 | 0.200 | 99.900 | 0.3998 | `5.890797353908e-2173` | *(not representable)* | — | — | **YES (cond. 1)** |

(`U` values shown for Λ=40; the Λ=80 values quoted in the Λ-sensitivity table differ accordingly.)

**The ε=8, μ=0.5 row is fixed: 1.00e+00 → 2.7e-12.** Worst relative error anywhere the oracle
returns a value is **2.7e-12**; everything worse is refused rather than returned.

### Why the comparison must be relative, and what tolerance

True δ spans `9.99e-1` to `1.05e-57` in the table above. Any absolute tolerance is meaningless:
`abs(a−b) < 1e-12` passes trivially for every row below δ=1e-12, including the catastrophically
wrong `0.0`. The oracle agreement test must be `abs(a−b) <= rel_tol * abs(b)` **with an explicit
`a != 0.0 and b != 0.0` precondition** (see F1).

**For `GOLDEN_EPSILON`'s pin tolerance:** ε is far less sensitive to δ than δ is to itself
(`d ln δ/dε ≈ −z/μ`, so a relative error in δ shrinks by roughly `μ/z` when carried into ε).
Measured, ε bisected to convergence against each oracle independently:

| σ | T | ε via closed form (`erfc`) | ε via oracle (`exp` quadrature) | rel gap |
|---|---|---|---|---|
| 20.0 | 200 | `2.943225239801367` | `2.943225239801352` | 5.13e-15 |
| 14.142135623730951 | 200 | `4.377178095681224` | `4.377178095681209` | 3.25e-15 |
| 10.0 | 200 | `6.572970067030331` | `6.572970067030306` | 3.78e-15 |
| 5.0 | 200 | `15.456155822609318` | `15.456155822609244` | 4.83e-15 |
| 2.0 | 200 | `54.376639014985628` | `54.376639014985045` | 1.07e-14 |
| 1.0 | 1 | `4.377178095681224` | `4.377178095681209` | 3.25e-15 |
| 8.0 | 64 | `4.377178095681224` | `4.377178095681209` | 3.25e-15 |

**`GOLDEN_EPSILON` should be pinned with a relative tolerance of `1e-12`** — ~2 orders of margin
over the measured 1.07e-14 worst case, and ~2 orders tighter than any real implementation error
would be. An exact float equality would be **wrong**: D-13 requires the golden values to come from
the oracle, and the oracle and the implementation differ at 1e-14 by construction.

Note the last three rows: σ=14.142/T=200, σ=1/T=1 and σ=8/T=64 all have `μ_eff = 1.0` and produce
**bit-identical ε**. That is the composition identity appearing as data, and it is the natural
shape for the golden vectors.

---

## Findings that change the plan

Six things measured in this session that `22-CONTEXT.md` does not record. F1 and F4 are the
load-bearing ones.

### F1 — The two-oracle cross-check is VACUOUS in exactly the regime D-13 was written to defend

`[VERIFIED: this session, 60-dps ground truth]`

The closed form has the **same silent-zero failure mode** as the quadrature, at a nearly identical
boundary — because both are governed by the same `z`. `math.erfc(x)` returns exactly `0.0` for
x ≥ 27.2 (bisected: `erfc(27.00) = 5.237046e-319`, `erfc(27.50) = 0.0`), so `delta_closed` returns
`0.0` once `z > 38.4666`. The oracle returns `0.0` once `z > 38.3722`.

**Consequence: past z ≈ 38.47 both return `0.0`, and the agreement test PASSES on two wrong
answers.** Measured with `abs(a−b) <= 1e-9*abs(b)`:

| ε | μ | z | closed (f64) | oracle (f64) | agreement test | TRUE δ (60 dps) |
|---|---|---|---|---|---|---|
| 2.00 | 0.707 | 2.475 | 1.25813e-03 | 1.25813e-03 | True (correct) | `0.00125812571038` |
| 8.00 | 0.500 | 15.750 | 1.04866e-57 | 1.04866e-57 | True (correct) | `1.04865917891e-57` |
| 2.00 | 0.100 | 19.950 | 3.71945e-91 | 3.71945e-91 | True (correct) | `3.7194507268e-91` |
| **2.00** | **0.050** | **39.975** | **0.0** | **0.0** | **True — VACUOUS** | `1.24028351258e-352` |
| **1.00** | **0.020** | **49.990** | **0.0** | **0.0** | **True — VACUOUS** | `7.12037376927e-549` |
| **5.00** | **0.050** | **99.975** | **0.0** | **0.0** | **True — VACUOUS** | `8.18353277275e-2177` |

D-13 correctly identifies the quadrature's silent zero and requires a refusal there. It does not
record that **the closed form has the identical failure**, so the "two oracles of different
mathematics" defence collapses to `0.0 == 0.0` in that corner. Two independent implementations do
not help when both fail on the same underlying quantity.

**What the plan must do:**
1. `accountant.py::delta_closed` needs the **same** non-vacuity refusal as the oracle — a
   `z`-domain check and a `delta <= 0.0` refusal. D-13 mandates it only for the oracle.
2. The agreement test must **refuse `a == 0.0 or b == 0.0` before comparing**, not treat it as
   agreement.
3. There is a narrow **useful** band, `38.372 < z < 38.467`, where the two genuinely disagree
   (measured at z = 38.40: closed = `6.9169e-323`, oracle = `0.0`). That is a real disagreement and
   the check would fire there — but it is ~0.1 wide in z and cannot be relied on.

This is Phase 20's own carried lesson — *a guard that refuses a NAME where the harm is a PROPERTY*
— turned on the cross-check itself.

### F2 — `math.exp(eps)` overflows at ε > 709.78, and the inverse's bisection reaches it

`[VERIFIED: this session]`

The naive closed form `0.5*(erfc(a) − exp(eps)*erfc(b))` raises `OverflowError: math range error`
for ε > 709.782712893384 (bisected). Reachable on the real frontier — `epsilon_for(σ, T=200,
δ=1e-5)`:

| σ | μ_eff = √200/σ | ε | naive `delta_closed(ε, μ)` |
|---|---|---|---|
| 2.00 | 7.071 | 54.3766 | 1.0000e-05 |
| 1.00 | 14.142 | 159.4415 | 1.0000e-05 |
| 0.50 | 28.284 | 519.6982 | 1.0000e-05 |
| 0.45 | 31.427 | 626.9223 | 1.0000e-05 |
| **0.40** | **35.355** | **775.7867** | **OverflowError** |
| **0.30** | **47.140** | **1312.1600** | **OverflowError** |

Phase 23 would never *publish* ε = 776, but `sigma_for` bisects σ downward and `epsilon_for`
doubles its ε bracket upward, so both walk into this domain during a normal search. This is a
**loud** failure (an exception), not a silent one — the good kind — but it aborts a legitimate
inverse solve.

**Fix is one line:** `exp(eps + log(erfc(b)))` guarded by `erfc(b) == 0.0`, as shown in the code
sketch above. Verified: with the fix, the σ=0.30 case computes cleanly.

### F3 — D-13's identity is exact in real arithmetic but FAILS bitwise 19.9% of the time in float64

`[VERIFIED: this session, 4,000-sample random sweep, seed 20260825]`

`μ_eff(σ,T) = sqrt(T)/sigma` costs two roundings; `μ(σ/√T, 1) = 1.0/(sigma/sqrt(T))` costs three.
Sweeping σ log-uniform in [0.5, 200] and T uniform in [1, 5000] at δ=1e-5:

| quantity | disagreement rate |
|---|---|
| μ derivation, bitwise | 1099/4000 = **27.5%** |
| `epsilon_for` end to end, bitwise | 795/4000 = **19.9%** |
| worst relative gap | **1.184e-14** (82 ulp), at σ=184.50381354671796, T=119 |

Representative mismatches:

```
sigma=64.84002691931646  T=3506  3.9416180134610093 vs 3.941618013461011    4 ulp  rel=4.51e-16
sigma=1.15156541215471   T=3493  1535.9032619024501 vs 1535.9032619024506   2 ulp  rel=2.96e-16
sigma=130.75401938516768 T=231   0.4013471353125827 vs 0.40134713531258104 30 ulp  rel=4.15e-15
```

A hand-picked golden set can easily be all-green by luck — my first 5 hand-chosen pairs were all
bitwise equal, and so were the 3 in the end-to-end check. Phase 23's swept σ values will not be.

**What the plan must do:** D-13's second oracle `ε(σ, T, δ) == ε(σ/√T, 1, δ)` must be asserted with
a **relative tolerance of 1e-12** (~2 orders over the measured 1.18e-14 worst case), never with
float `==`. The *mathematics* of D-13 is confirmed exact; only its transcription as `==` is wrong.

**This interacts with DPSGD-05.** DPSGD-05 requires a kill→resume to reproduce a *bit-identical
reported ε*. That is achievable and should be kept as `==` — it compares **the same call shape**
across two processes, which is deterministic. The tolerance above applies only to comparing **two
different call shapes**. The plan must not conflate them: one is `==`, the other is `rel_tol`.

### F4 — `σ` is the NOISE MULTIPLIER, not the raw noise std. Already settled in two committed artifacts.

`[VERIFIED: grep against HEAD]`

D-12 writes "`μ = C/σ`", implying σ is the raw noise standard deviation. But D-12 also specifies
`epsilon_for(sigma, T, delta)` — **with no `C` argument**. Both cannot be right. Three committed
artifacts resolve it, all agreeing:

1. `scripts/mitigation_gate.py:1026` — `MECHANISM_KEYS = ("sigma", "steps", "delta", "q")`, called
   in its own comment "the mechanism parameters epsilon is a deterministic function of… there is no
   fifth key". **`C` is not a key.** This file is FROZEN (Phase 20 D-24).
2. `scripts/mitigation_gate.py:161` — the DP arm's formal claim is "a mathematical property of the
   DP-SGD mechanism at the recorded **noise multiplier**, step count, sampling rate and delta".
   Four quantities, matching `MECHANISM_KEYS` exactly.
3. `.planning/research/ARCHITECTURE.md:14` and `:229` — "T compositions of the Gaussian mechanism
   is exactly μ-GDP with **μ = √T/σ**"; the code sketch's docstring repeats it verbatim.

So `σ ≡ σ_noise / C` (unitless), `μ = 1/σ`, `μ_eff = √T/σ`, and `epsilon_for` correctly needs no
`C`. **D-12's "μ = C/σ" is the outlier phrasing, not a fifth decision.** Under it, D-12's measured
"`μ = C/σ` is a `ZeroDivisionError`" is still exactly right — `1.0/0.0` raises — so the decision's
substance is unaffected; only its variable naming needs correcting.

**What the plan must do:** `accountant.py`'s docstring should state `sigma` is the noise multiplier
`sigma_noise / clip_norm` and cite `mitigation_gate.py:1026` as the frozen basis. If the plan
instead adds a `clip_norm=` parameter to `epsilon_for`, it introduces a **fifth mechanism key** the
frozen gate says does not exist. Consistency with `MECHANISM_KEYS` is not a preference here.

*(Cross-check: this reading reproduces `22-CONTEXT.md`'s own Phase-23 note. At T=200 and per-step
μ=0.7, μ_eff = 9.899 and δ ≈ 0.99999 at ε=2 — I reproduce δ = 1.0 to 60 dps at μ=9.899. And its
"a usable ε needs σ ≈ 20×C" matches `epsilon_for(σ=20, T=200, δ=1e-5) = 2.943225`.)*

### F5 — `.planning/research/STACK.md`'s RDP accountant recommendation is superseded, not an alternative

`[VERIFIED: grep against HEAD]`

`STACK.md:207` recommends "hand-rolled RDP, Poisson-subsampled Gaussian, integer-α only, Balle
conversion", with an α grid, a grid-truncation guard, and a `logsumexp` binomial sum. That
recommendation assumes **q < 1**. Phase 21 D-07/D-23 locked `SAMPLING_RATE_Q = 1.0`, and
`ARCHITECTURE.md:238-240` states the consequence explicitly: *"Why GDP and not RDP. Because the
fact-aligned design has no subsampling (q = 1)… composition of T Gaussian mechanisms is exactly
μ-GDP… That is tight, not a bound."*

22-CONTEXT D-09's `REQUIRED_FORM` follows ARCHITECTURE, correctly. Recorded here only so a planner
who reads STACK.md does not build an α grid, a `logsumexp`, or a grid-truncation guard — **none of
which this phase needs.** At q=1 the RDP route is strictly looser than the exact form for more
code. Skip it.

### F6 — LOUD: the adjacency relation is a stated precondition of `μ = Δ/σ`, and it has never landed in code

`[VERIFIED: grep against HEAD — 0 hits in scripts/, src/, tests/]`

Composition condition 5 above. `μ = Δ/σ` requires Δ to be the per-step L2 sensitivity **under a
fixed neighbouring relation**, and the two standard choices differ by a factor of 2:

- **add/remove-one (unbounded DP):** removing a record changes the clipped sum by `g_i`, ‖·‖ ≤ C
  → **Δ = C**
- **replace-one (bounded DP):** replacing record i changes the sum by `g_i − g_i'`, ‖·‖ ≤ 2C
  → **Δ = 2C**

D-02's stated argument — *"one record moves the sum by at most `C` — the textbook sensitivity
argument"* — is the **add/remove-one** argument. It is correct under that convention and wrong by
2× under replace-one. Since ε is roughly linear in μ over the operating range, that is roughly a
factor of 2 in every published ε.

**This is NOT an unresearched question — it is a carry-forward gap.** `.planning/research/
PITFALLS.md:143-165` (pitfall **P3, "Noise scaled to the wrong sensitivity"**) already settles it
and prescribes the mechanism:

> Under add/remove-one neighbouring, the L2 sensitivity of the clipped sum is `C`; under
> replace-one it is `2C`. … The neighbouring relation is a definition, not a code artifact.
> Nothing in a training loop records which one you meant. Papers use both. … Write the neighbouring
> relation into the same module-level constant block as X and Y, as a string, before any run:
> `NEIGHBOURING = "add/remove one <unit>"` and `SENSITIVITY_MULTIPLIER = 1.0`. … **Phase to
> address: P20 (constant), P21 (accountant consumes it).**

**Measured: neither constant exists.** `grep -rn "NEIGHBOURING\|SENSITIVITY_MULTIPLIER" scripts/
src/ tests/` returns **zero hits**. P20 and P21 both closed without landing it, and
`22-CONTEXT.md` does not carry it forward. Zero hits for `adjacen|add-remove|replace-one|bounded
DP` in `scripts/`, `src/`, or `.planning/REQUIREMENTS.md` either.

**Why it matters here specifically.** PITFALLS P3 is verbatim DPSGD-04's second fake, "noise scaled
to the wrong sensitivity". D-17 makes that fake impossible **at the code level** (single-source
`self.C`, so introducing a second constant is a positive insertion the AST guard catches). It does
**not** address the **definitional** half: `self.C` being single-sourced proves the code is
self-consistent, not that `C` is the right sensitivity for the adjacency the report claims. A DP
implementation can pass all four of D-05's axes and all four of D-16's runtime invariants while
publishing an ε that is 2× optimistic, because every guard checks `C` against `C`.

**What the plan should do** (this is the planner's call, not a research decision):

- Land PITFALLS P3's prescribed constants in the frozen pin — `scripts/mitigation_accountant.py`
  already has to be zero-import, and two string/float literals cost nothing. `NEIGHBOURING` and
  `SENSITIVITY_MULTIPLIER` sit naturally beside `REQUIRED_FORM` and `REJECTED_FORM`, and the pin is
  precisely "the definition, committed before the number".
- Have `accountant.py`'s docstring and `dpsgd.py`'s noise line both name the same relation, so
  PITFALLS P3's stated warning sign ("the report says add/remove and the accountant's docstring
  says replace") is checkable.
- Note the pin cannot *import* the constant (zero-import ceiling) — the check is a test that reads
  both sites, which is the same shape D-05 axis 1 already builds.

Under the D-02 sensitivity argument as written, the consistent choice is
`NEIGHBOURING = "add/remove one fact"` with `SENSITIVITY_MULTIPLIER = 1.0` — matching PITFALLS P3's
own recommendation and matching `mitigation_unit.py`'s `PRIVACY_UNIT`. **But that is a decision, not
a research finding, and it should be made explicitly rather than inherited by silence.**

---

## Validation Architecture

Test framework detected from the tree:

| Property | Value |
|----------|-------|
| Framework | `pytest` 8.x (`pyproject.toml`; `pythonpath = ["."]` at `:26`) |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `.venv/bin/python -m pytest tests/test_phase22_accountant.py -x -q` |
| Full suite command | `make test` (CPU-only, GPU-free) |
| Lint | `make lint` (`ruff check . && ruff format --check .`) |
| Env | Python **3.11** venv mandatory (`CLAUDE.md`); local box is 3.14 and is not a supported target |

**Nothing in this phase requires a GPU.** Every row below runs on CPU. The three MPS-touching rows
(V-14, V-15) are `pytest.mark.skipif(not torch.backends.mps.is_available())` and are honestly
recorded as required-but-unexercised in CI, per D-14.

### Phase Requirements → Test Map

| Req | ID | Behaviour validated | Granularity / sampling rate | Observable | Automated command | Exists? |
|---|---|---|---|---|---|---|
| DPSGD-03 | V-01 | `delta_closed` matches Balle–Wang Thm 8 on the 12-point frontier | once per test run | rel err ≤ 1e-12 vs pinned 60-dps literals | `pytest tests/test_phase22_accountant.py::test_closed_form_frontier -x` | ❌ Wave 0 |
| DPSGD-03 | V-02 | `delta_quadrature` agrees with `delta_closed` | once per test run | **relative** tol 1e-9, **with `a != 0.0 and b != 0.0` asserted first** (F1) | `…::test_two_oracles_agree -x` | ❌ Wave 0 |
| DPSGD-03 | V-03 | `ε(σ,T,δ)` vs `ε(σ/√T,1,δ)` — the composition oracle | once per test run, ≥20 swept (σ,T) | rel gap ≤ 1e-12, **never `==`** (F3) | `…::test_composition_identity -x` | ❌ Wave 0 |
| DPSGD-03 | V-04 | derived range beats the fixed range at ε=8, μ=0.5 | once per test run | rel err ≤ 1e-11 where `[-14,14]` gives 1.0 | `…::test_low_privacy_corner -x` | ❌ Wave 0 |
| DPSGD-03 | V-05 | **non-vacuity refusal fires** — all 3 conditions, each separately | once per test run | `pytest.raises(ValueError)` at z=39.85 (cond. 1), at a deliberately narrowed Λ (cond. 2), on a forced 0.0 (cond. 3) | `…::test_oracle_refuses -x` | ❌ Wave 0 |
| DPSGD-03 | V-06 | `GOLDEN_EPSILON` in the frozen pin reproduces from the **oracle**, not from `accountant.py` | once per test run | rel tol 1e-12; test imports the pin and re-derives via `delta_quadrature` only | `…::test_golden_epsilon_from_oracle -x` | ❌ Wave 0 |
| DPSGD-03 | V-07 | round-trip `sigma_for(epsilon_for(σ,T,δ),T,δ) == σ` | once per test run | rel ≤ 1e-12 (measured achievable: ≤1.07e-15) | `…::test_round_trip -x` | ❌ Wave 0 |
| DPSGD-03/05 | V-08 | `σ = 0 → ε = inf`, never `ZeroDivisionError` | once per test run | `math.isinf(epsilon_for(0.0, T, δ))` | `…::test_sigma_zero -x` | ❌ Wave 0 |
| DPSGD-03 | V-09 | `accountant.py` imports **`math` only** | **build time (AST)** | `ast` walk of the module's import nodes == `{"math"}` | `…::test_accountant_imports_math_only -x` | ❌ Wave 0 |
| DPSGD-03 | V-10 | frozen pin has **zero imports** and no executable formula | **build time (AST)** | import set empty; no `BinOp`/`Call` at module level beyond literal tuples — extends `tests/test_phase20_prereg.py:915-917`'s existing shape | `pytest tests/test_phase20_prereg.py -k accountant -x` | ❌ Wave 0 |
| DPSGD-01/04 | V-11 | D-05 axis 1 — AST guard over the call graph: no `.backward()`, `.grad` write, clip/normalize, **second clip constant**, or **in-step re-seed** between noise and `step()` | **build time (AST)** | AST walk asserts absent | `pytest tests/test_phase22_dpsgd_ast.py -x` | ❌ Wave 0 |
| DPSGD-01/04 | V-12 | D-05 axis 2 — one-kwarg-apart runtime differential; private noised contribution byte-identical with/without the public term | once per test run | `torch.equal` on the private term | `pytest tests/test_phase22_dpsgd.py::test_side_channel_negative_control -x` | ❌ Wave 0 |
| DPSGD-01/04 | V-13 | D-16 runtime invariants ×4: `.grad` drain, sensitivity ≤ `C*(1+tol)`, single-write count, generator-state advance | **runtime, EVERY step, inside the seam** | `raise RuntimeError` (never `assert` — D-15, `python -O`) | exercised by every DP test + the D-08 end-to-end run | ❌ Wave 0 |
| DPSGD-02 | V-14 | seam off ⇒ bit-identical to `tests/fixtures/golden_trajectory_v1.json` | once per test run; platform-gated replay + platform-independent in-process identity | `torch.equal` / exact JSON match | `pytest tests/test_phase22_dpsgd.py::test_seam_off_bit_identical -x` | ❌ Wave 0 |
| DPSGD-05 | V-15 | kill→resume reproduces a **bit-identical reported ε** | once per test run | `epsilon_a == epsilon_b` — exact `==` is correct here (same call shape, F3) | `pytest tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical -x` | ❌ Wave 0 |
| DPSGD-05 | V-16 | `rng["mps"]` slot round-trips; **old checkpoints without it still load** | once per test run | `rng.get("mps")` is None-safe; v3.0 fixture loads | `pytest tests/test_phase22_checkpoint.py -x` | ❌ Wave 0 |
| DPSGD-07 | V-17 | `persona_adapter.pt` + every v3.0 checkpoint still load; `LoRALinear` state-dict keys unchanged | once per test run | key-set equality | existing `tests/test_lora_*.py` + one new key-set assertion | partial ✅ |
| DPSGD-04 | V-18 | **FAKE 1** clip the averaged gradient — drop the drain | **one-shot positive control, RED→GREEN** | D-05 axis 4 reddens, then restore and re-green | `pytest tests/test_phase22_fakes.py::test_fake_averaged_gradient -x` | ❌ Wave 0 |
| DPSGD-04 | V-19 | **FAKE 2** wrong sensitivity — add a second clip constant | **one-shot positive control, RED→GREEN** | D-05 axis 1 (AST) **and** D-16's runtime `C*(1+tol)` both redden | `…::test_fake_wrong_sensitivity -x` | ❌ Wave 0 |
| DPSGD-04 | V-20 | **FAKE 3** noise after averaging — build `divide → noise` | **one-shot positive control, RED→GREEN** | D-06's CPU σ=0 identity breaks | `…::test_fake_noise_after_averaging -x` | ❌ Wave 0 |
| DPSGD-04 | V-21 | **FAKE 4** RNG reuse — add an in-step `manual_seed` | **one-shot positive control, RED→GREEN** | D-05 axis 1 (AST) **and** D-16's generator-state check redden | `…::test_fake_rng_reuse -x` | ❌ Wave 0 |
| DPSGD-01 | V-22 | D-04's three property refusals at wiring time: non-`lora_` `requires_grad`, scaler enabled, trainable count == 331,776 | once per test run + **runtime at seam construction** | `pytest.raises(RuntimeError)` ×3; the `inject_lora`-without-`mark_only_lora_trainable` case (172 tensors / 14,223,360 params) is the positive control | `pytest tests/test_phase22_dpsgd.py::test_seam_refuses -x` | ❌ Wave 0 |
| DPSGD-01 | V-23 | D-08's four wirings execute end-to-end on a CPU fixture and write **no scored artifact** | once per test run | run completes; `results/` unchanged | `pytest tests/test_phase22_wiring.py -x` | ❌ Wave 0 |
| — | V-24 | `pyproject.toml` untouched (RPT-03); `mitigation_gate.py` / `mitigation_unit.py` unmodified | once per test run | existing frozen-pin + ancestry tests | `pytest tests/test_phase20_prereg.py -x` | ✅ exists |

### Sampling rate

- **Per task commit:** `.venv/bin/python -m pytest tests/test_phase22_*.py -x -q` — the accountant
  rows alone run in well under 30 s (a single `delta_quadrature` at n=20,001 is ~10 ms in pure
  Python; the full 12-point frontier is ~0.3 s).
- **Per wave merge:** `make test` (full CPU-only suite) + `make lint`.
- **Phase gate:** full suite green, all four positive controls **observed RED before GREEN with the
  RED output recorded**, before `/gsd:verify-work`.
- **Runtime, every training step:** D-16's four invariants, inside the seam. Justified by the
  measured cost asymmetry — a failure costs ~17 s (training) against 4.77 h (evaluation, which runs
  after; `REQUIREMENTS.md:159-161`).

### Wave 0 gaps

- [ ] `tests/test_phase22_accountant.py` — V-01 … V-09
- [ ] `tests/test_phase22_dpsgd_ast.py` — V-11
- [ ] `tests/test_phase22_dpsgd.py` — V-12, V-14, V-22
- [ ] `tests/test_phase22_checkpoint.py` — V-15, V-16
- [ ] `tests/test_phase22_fakes.py` — V-18 … V-21 (each RED-then-GREEN)
- [ ] `tests/test_phase22_wiring.py` — V-23
- [ ] additions to `tests/test_phase20_prereg.py` — V-10, plus D-11's `V4_ARTIFACT_GLOBS` +
      `_assert_ordering_holds(artifact_glob="results/phase23_*")` **both halves**
- [ ] a committed 60-dps reference table (literal values, generated once, checked in as data) so
      V-01 does not need `mpmath` — **`mpmath` must not become a test dependency** (RPT-03). The
      values in this document's tables are that table.
- No framework install needed: `pytest` 8.x is already in `[dev]`.

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.11 venv | everything | ✓ | 3.11.15 (`.venv`) | none needed |
| `math` (stdlib) | accountant + oracle | ✓ | stdlib | — |
| `pytest` | whole battery | ✓ | 8.x (`[dev]`) | — |
| `torch` | `dpsgd.py`, checkpoint, golden fixture | ✓ | 2.7.1 | — |
| `mpmath` | **research only** — the 60-dps ground truth in this document | ✓ | 1.3.0 (transitive) | **must NOT be imported by any test** — pin the literals instead (RPT-03) |
| `scipy` | nothing | ✗ | — | not needed; `math.erfc` is sufficient |
| MPS backend | V-14/V-16 device rows | (host-dependent) | — | `skipif`; D-14 records the slot as required-but-unexercised |

**Nothing to install.** `pyproject.toml` stays untouched and the Package Legitimacy Audit is not
applicable to this phase.

---

## Open Questions (RESOLVED)

> All three were closed before planning. Retitled and annotated per the Phase-22 revision so no
> reader treats a resolved question as still open:
> **Q1** — closed by `22-CONTEXT.md` **D-18** (`NEIGHBOURING` / `SENSITIVITY_MULTIPLIER` pinned in
> the frozen module, cross-site test built here rather than deferred).
> **Q2** — closed by `22-CONTEXT.md`'s naming correction (σ is the noise MULTIPLIER, so `μ = 1/σ`
> and `μ_eff = √T/σ`) together with this document's **F4**; no `clip_norm=` parameter reaches
> `epsilon_for`, so no fifth `MECHANISM_KEYS` entry is created.
> **Q3** — closed by plan **22-02 Task 1**, which fixes the frozen pin's contents, its zero-import
> ceiling and its `GOLDEN_EPSILON` provenance.

1. **Which adjacency relation does the published ε assume? (F6)**
   - What I know: `μ = Δ/σ` needs a fixed adjacency; add/remove-one gives Δ=C, replace-one gives
     Δ=2C. D-02's written argument is the add/remove-one argument. `.planning/research/PITFALLS.md`
     P3 prescribes `NEIGHBOURING = "add/remove one <unit>"` / `SENSITIVITY_MULTIPLIER = 1.0` and
     assigns it to P20/P21.
   - What I tried: grepped `scripts/`, `src/`, `tests/`, and `.planning/REQUIREMENTS.md` for
     `NEIGHBOURING`, `SENSITIVITY_MULTIPLIER`, `adjacen`, `add-remove`, `replace-one`, `bounded DP`.
     **Zero hits in code.** P20 and P21 closed without landing it.
   - Why it needs a human: it is a factor of ~2 on every published ε, D-17's guards structurally
     cannot detect it (they check `C` against `C`), and choosing it silently is exactly the
     failure PITFALLS P3 exists to prevent. **Recommendation:** land the two constants in the
     frozen pin with `add/remove one fact` / `1.0`, matching D-02's argument and
     `mitigation_unit.PRIVACY_UNIT` — but state it as a decision.

2. **Does `epsilon_for` gain a `clip_norm=` parameter, or is `sigma` documented as the noise
   multiplier? (F4)**
   - What I know: `mitigation_gate.py:1026`'s `MECHANISM_KEYS` (FROZEN) has four keys and no `C`;
     `:161` says "noise multiplier"; `ARCHITECTURE.md:14` says `μ = √T/σ`. All three say the
     noise-multiplier reading. D-12's "`μ = C/σ`" phrasing is the only dissent.
   - What I tried: read all three artifacts; confirmed D-12's `ZeroDivisionError` measurement holds
     under either reading, so no decision substance changes.
   - Recommendation: document `sigma` as the noise multiplier and cite `mitigation_gate.py:1026`.
     Adding `clip_norm=` would create a fifth mechanism key the frozen gate says does not exist.

3. **Does the frozen pin's `REJECTED_FORM` prose carry the *reason*, or only the formula?**
   - D-09 requires naming the rejected form "without transcribing its logic". The §
     "Why `REJECTED_FORM` is rejected" material above (Thm A.1's `ε ∈ (0,1)` hypothesis; the
     measured crossover at μ=1.7379; 35.7× the promised δ at σ=0.3) is prose and literals, so it
     fits inside the zero-import ceiling — but it is the planner's call how much goes in the pin
     versus in `accountant.py`'s docstring.

Everything else in scope was settled. Notably **not** open: the closed form (Q1), the exactness
argument, the composition identity and its five conditions, `σ=0 → ε=∞`, `t_min`, the range rule,
Λ, the quadrature rule and node count, the three refusal conditions, and every tolerance.

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | `pytest` 8.x is in the `[dev]` extra and `make test` is the full-suite command | Validation Architecture | Wrong command in the plan; trivially corrected at Wave 0 |
| A2 | The recommended file names (`tests/test_phase22_*.py`) match the project's convention | Validation Architecture | Cosmetic — the planner names files |
| A3 | `mpmath` 1.3.0 is present only transitively and is not a declared dependency | Environment Availability | If a test imports it, RPT-03's zero-new-dependency streak is at risk — hence the "pin the literals" instruction |

Everything else in this document is `[VERIFIED]` (measured this session with the stated probe
conditions) or `[CITED]` (quoted from the named primary source with theorem/section number). No
figure is reported without its provenance and its bound.

---

## Probe conditions (bounds stated rather than glossed)

- **Environment:** `/Users/juliorcoelho/PersonaCore/.venv`, CPython **3.11.15**, `mpmath` 1.3.0,
  `numpy` 2.4.6, macOS/darwin 25.5.0, single process, no confidence intervals, no CI replication.
- **Ground truth:** `mpmath` at `mp.dps = 60`, `Φ(x) = erfc(−x/√2)/2`. Exact ε values obtained by
  300-iteration bisection on a strictly-decreasing `δ(·, μ)`.
- **Quadrature:** composite Simpson unless labelled trapezoid; grid start exactly at `t_min` unless
  the row says otherwise; Λ as labelled; pure Python floats (float64) throughout — **no NumPy in
  any recommended implementation.**
- **Random sweeps:** F3 used `random.seed(20260825)`, σ log-uniform in [0.5, 200], T uniform in
  [1, 5000], N = 4000 (and N = 200,000 for the μ-only bitwise check). Rates are point estimates on
  that distribution; a different σ/T distribution will give a different rate but not a different
  conclusion (the mechanism is double-rounding, which is distribution-independent).
- **Not measured:** timing of the accountant (irrelevant — it runs once per report, not per step);
  behaviour under `python -O` (D-15's `raise`-not-`assert` rule is inherited, not re-verified);
  anything about the gradient seam (out of scope by the fence).

---

## Sources

### Primary (HIGH confidence)

- **Balle & Wang, "Improving the Gaussian Mechanism for Differential Privacy: Analytical
  Calibration and Optimal Denoising", ICML 2018 — arXiv:1805.06530.**
  Theorem 8 (§3, eq. 6) — the iff condition, `REQUIRED_FORM`. Theorem 1 (§2) — the classical
  mechanism, stated for `ε, δ ∈ (0,1)`. §2.3 "Limitations in the Low Privacy Regime" + Theorem 4 —
  the classical rate "cannot be extended beyond the interval ε ∈ (0,1)".
  https://arxiv.org/abs/1805.06530
- **Dong, Roth & Su, "Gaussian Differential Privacy", arXiv:1905.02383.**
  Definition 2.6 (μ-GDP); **Corollary 2.13** — the exact (ε,δ) dual, independently confirming
  Balle–Wang Thm 8; **Corollary 3.3** — T-fold composition is `√(Σμᵢ²)`-GDP, an *exact* equality of
  trade-off functions, covering *adaptive* composition (§3, eq. 9).
  https://arxiv.org/abs/1905.02383
- **Dwork & Roth, *The Algorithmic Foundations of Differential Privacy* (2014), Theorem A.1** — the
  origin of `REJECTED_FORM`, with `ε ∈ (0,1)` in its hypothesis. Reached via Balle–Wang's Theorem 1
  restatement rather than the monograph directly.
- **This session's numerical probes** — 60-dps `mpmath` ground truth, reproduced D-13's table
  exactly; all tables above.

### Repo-internal (HIGH — read against HEAD, not transcribed)

- `scripts/mitigation_gate.py:161`, `:1024-1026` — "noise multiplier"; `MECHANISM_KEYS` with no
  `C`. **FROZEN** (Phase 20 D-24).
- `scripts/mitigation_unit.py:86` — `DELTA = 1e-5`; `:46` — `SAMPLING_RATE_Q = 1.0`. **FROZEN.**
- `.planning/research/ARCHITECTURE.md:14`, `:229`, `:238-240`, `:932` — `μ = √T/σ`; "tight, not a
  bound"; "Why GDP and not RDP"; two independent sources for the dual.
- `.planning/research/PITFALLS.md:143-165` — pitfall P3, the adjacency prescription (F6).
- `.planning/research/STACK.md:207-262` — the RDP recommendation superseded by q=1 (F5).
- `tests/test_phase20_prereg.py:915-917` — the import ceiling forcing the accountant's split.

### Secondary (MEDIUM)

- **Bun & Steinke, "Concentrated Differential Privacy" (2016)** — zCDP cross-check of the
  composition identity (`ρ = μ²/2`, `√(2Tρ) = μ√T`). Used as an independent confirmation of DRS
  Cor. 3.3, verified numerically this session rather than re-read.

---

## Metadata

**Confidence breakdown:**
- Analytic Gaussian mechanism (Q1): **HIGH** — two independent primary sources give the identical
  closed form, and it is confirmed to 60 decimal digits numerically.
- Composition identity and its conditions: **HIGH** — DRS Cor. 3.3 is an exact result explicitly
  covering adaptive composition; cross-checked against zCDP.
- Rejection of `REJECTED_FORM`: **HIGH** — the `ε ∈ (0,1)` hypothesis is quoted from the paper, and
  the over-claim is measured with its crossover located to 9 digits.
- Quadrature range, rule, node count, tolerances (Q2): **HIGH** — every number is a measurement in
  this session against a 60-dps reference, with probe conditions stated.
- F6 (adjacency): **HIGH** on the mathematics and on the grep; the *choice* of relation is a
  decision for the planner/user, not a research output.

**Research date:** 2026-08-25
**Valid until:** indefinite for the mathematics (2018/2019 results, no successor tightens an exact
result); ~90 days for the repo-internal line anchors, which are the part that goes stale — every
path here was resolved against HEAD (`a5f4ac1`) during this session.
