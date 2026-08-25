"""Phase 22 — 60-dps ground truth for the (eps, delta) accountant, committed as LITERAL DATA.

Every number below was computed ONCE, during the ``22-RESEARCH.md`` session, with ``mpmath`` at
``mp.dps = 60``, and is committed here as data for exactly one reason: **so that no test ever
imports mpmath** (RPT-03 — ``pyproject.toml`` is untouched by this phase and the zero-new-dependency
streak holds). ``tests/test_phase22_reference.py::test_no_phase22_test_imports_mpmath`` makes that a
checked property of the whole ``tests/test_phase22_*.py`` glob rather than a promise in a SUMMARY.

**This module has ZERO imports and ZERO executable logic**, and both halves are pinned by
``test_reference_fixture_imports_nothing`` as an AST property. That is not tidiness: a reference
table that can execute is a reference table that can DERIVE its own answers, and a ground truth
derived from the thing it judges is a photograph of the code rather than a constraint on it (D-13's
stated reason for pinning ``GOLDEN_EPSILON`` to the ORACLE and never to ``accountant.py``).

Consumers:
  - V-01 ``test_closed_form_frontier``   -> ``DELTA_FRONTIER``
  - V-02 ``test_two_oracles_agree``      -> ``DELTA_FRONTIER``, ``VACUOUS_AGREEMENT_ROW``
  - V-04 ``test_low_privacy_corner``     -> ``DELTA_FRONTIER`` row (8.0, 0.5), ``QUADRATURE_PARAMS``
  - V-05 ``test_oracle_refuses``         -> ``ZERO_BOUNDARIES``
  - V-06 ``test_golden_epsilon_from_oracle`` -> ``EPSILON_GOLDEN``, ``GOLDEN_EPSILON_REL_TOL``
"""

# =============================================================================================
# 1. DELTA_FRONTIER — delta(eps, mu) for the analytic Gaussian mechanism (Balle-Wang Thm 8 /
#    Dong-Roth-Su Cor 2.13). The V-01 ground truth, 12 rows.
#
#    PROVENANCE: 60-dps mpmath ground truth, computed once in the 22-RESEARCH session, committed
#    as data so no test imports mpmath (RPT-03).
#
#    `truth` is a DECIMAL STRING rather than a float literal, and that is LOAD-BEARING rather than
#    stylistic. The last row's 1.24028351258e-352 sits BELOW the float64 subnormal floor
#    (~4.94e-324), so a float literal would parse to 0.0 SILENTLY — the row would arrive in the
#    table already destroyed, and a "every truth is positive" meta-guard would then be asserting
#    over data the parser had already thrown away. As strings the digits survive; consumers call
#    float() and get exactly what f64 can hold, which for that row IS 0.0 — and that is the point.
#
#    The last two rows are RESEARCH F1's finding, in the table on purpose: past z ~ 38.47 BOTH
#    delta_closed (erfc underflow) and delta_quadrature return exactly 0.0, so the "two oracles of
#    different mathematics" cross-check degenerates to `0.0 == 0.0` and passes on two wrong
#    answers. Row (2.0, 0.1) is the last row where the cross-check is still meaningful; row
#    (2.0, 0.05) is the first where it is VACUOUS. V-02 must refuse a zero before comparing.
# =============================================================================================
DELTA_FRONTIER = (
    (1.0, 1.0, "0.1269367375066"),
    (0.5, 2.0, "0.5991856185339"),
    (3.0, 0.8, "7.016058166974e-5"),
    (0.1, 4.0, "0.9521780438554"),
    (8.0, 0.5, "1.048659178913e-57"),
    (2.0, 0.707, "0.001258125710375"),
    (3.3, 0.707, "1.047970917991e-6"),
    (0.5, 0.5, "0.05244032328767"),
    (6.0, 1.0, "2.787859763764e-9"),
    (0.01, 8.0, "0.9999363400557"),
    (2.0, 0.1, "3.7194507268e-91"),
    (2.0, 0.05, "1.24028351258e-352"),
)

# The ONE frontier row whose true delta is not representable in float64 (z = 39.975). Named as
# data rather than left implicit so `test_reference_table_is_populated` can assert by HARD
# EQUALITY which row underflows — a table that silently zeroed a second row reddens instead of
# passing as "well, one of them was always zero".
VACUOUS_AGREEMENT_ROW = (2.0, 0.05)

# =============================================================================================
# 2. EPSILON_GOLDEN — (sigma, steps, epsilon) with sigma the NOISE MULTIPLIER (sigma_noise /
#    clip_norm, unitless; RESEARCH F4 and the FROZEN
#    scripts/mitigation_gate.py::MECHANISM_KEYS = ("sigma", "steps", "delta", "q") — there is no
#    fifth key, so epsilon_for takes no clip_norm). Evaluated at the frozen delta.
#
#    PROVENANCE: 60-dps mpmath ground truth, computed once in the 22-RESEARCH session, committed
#    as data so no test imports mpmath (RPT-03).
#
#    The epsilon column is the ORACLE column (exp-quadrature), NEVER the erfc closed form. D-13
#    requires it: GOLDEN_EPSILON is derived from an oracle that cannot share the implementation's
#    failure modes, and a golden table read off the closed form shares them by construction. The
#    two columns differ at ~1e-14 BY DESIGN, which is why GOLDEN_EPSILON_REL_TOL exists at all
#    and why an exact float `==` against this table would be wrong.
#
#    THE COMPOSITION IDENTITY, APPEARING AS DATA. Three rows have mu_eff = sqrt(T)/sigma = 1.0 —
#    (14.142135623730951, 200), (1.0, 1) and (8.0, 64) — and all three carry a BIT-IDENTICAL
#    epsilon 4.377178095681209. That is Dong-Roth-Su Cor 3.3 showing up as equal literals rather
#    than as prose. (22-RESEARCH's own sentence says "the last three rows"; measured, the three
#    mu_eff = 1.0 rows are rows 2, 6 and 7 of its table, which is what is transcribed here.)
# =============================================================================================
EPSILON_GOLDEN = (
    (20.0, 200, 2.943225239801352),
    (14.142135623730951, 200, 4.377178095681209),
    (10.0, 200, 6.572970067030306),
    (5.0, 200, 15.456155822609244),
    (2.0, 200, 54.376639014985045),
    (1.0, 1, 4.377178095681209),
    (8.0, 64, 4.377178095681209),
)

# =============================================================================================
# 3. ZERO_BOUNDARIES — where each transcendental stops carrying information, bisected to the
#    digits shown. These are the DOMAIN LIMITS the non-vacuity refusals (D-13's three conditions,
#    widened to delta_closed by RESEARCH F1) are calibrated against.
#
#    PROVENANCE: 60-dps mpmath ground truth + bisection, computed once in the 22-RESEARCH session,
#    committed as data so no test imports mpmath (RPT-03).
#
#    z = eps/mu - mu/2 is the support boundary in standard deviations, and it is the SAME quantity
#    as sqrt(2)*a in the closed form's first erfc argument. That is not a coincidence, and it is
#    why both oracles die at nearly the same z: they are governed by one number, so two
#    independent implementations buy nothing in this corner (F1).
# =============================================================================================
ZERO_BOUNDARIES = {
    # delta_closed(eps, mu) first returns exactly 0.0 at this z.
    "delta_closed_zero_z": 38.466608897,
    # delta_quadrature (the substituted/scaled form) first returns exactly 0.0 at this z.
    # ~0.09 BELOW the closed form's boundary: the narrow band 38.372 < z < 38.467 is the only
    # place the two genuinely disagree, and it is far too narrow to rely on.
    "delta_quadrature_zero_z": 38.372164249,
    # math.erfc(x) first returns exactly 0.0 at this x. Bisected: erfc(27.00) = 5.237046e-319
    # (a subnormal, still information), erfc(27.50) = 0.0.
    "erfc_zero_x": 27.5,
    # math.exp(eps) raises OverflowError above this eps (F2). Reachable on the real frontier:
    # epsilon_for(sigma=0.40, T=200, delta) solves to eps = 775.79. The fix is one line —
    # exp(eps + log(erfc(b))) guarded on erfc(b) == 0.0 — not a domain restriction.
    "exp_overflow_eps": 709.782712893384,
}

# =============================================================================================
# 4. REJECTED_FORM_CROSSOVER — where the classical Gaussian mechanism
#    sqrt(2*ln(1.25/delta))/sigma (Dwork-Roth Thm A.1 / Balle-Wang Thm 1) stops being merely
#    unsupported and becomes wrong in the UNSAFE direction.
#
#    PROVENANCE: 60-dps mpmath ground truth + 60-iteration bisection, computed once in the
#    22-RESEARCH session, committed as data so no test imports mpmath (RPT-03).
#
#    MEASURED AT THE FROZEN DELTA 1e-05 — the value pinned as
#    scripts/mitigation_unit.py::DELTA (Phase 21 D-07/D-23). It is written here as prose, not as
#    a literal constant, because this module imports nothing and therefore cannot resolve it;
#    tests/test_phase22_reference.py::test_no_phase22_test_imports_mpmath reads DELTA from the
#    frozen pin and asserts it against this very comment, so the two can never drift apart while
#    the test module itself never re-spells the number.
#
#    Both parts of the rejection travel with their numbers:
#      - FORMALLY, Thm A.1's hypothesis is eps in (0, 1). Every sigma < 4.84 at this delta yields
#        eps > 1 and so invokes the theorem outside its own hypothesis; the claim is UNSUPPORTED
#        regardless of whether it happens to be numerically conservative.
#      - NUMERICALLY, past the crossover it under-reports eps, i.e. over-claims privacy: at
#        sigma = 0.3 the true delta at eps_classical is 3.572e-4 against a promised 1e-5.
# =============================================================================================
REJECTED_FORM_CROSSOVER = {
    "mu": 1.737896746,
    "sigma": 0.575408178,
    # true_delta / promised_delta at sigma = 0.3 (mu = 3.333): 3.572e-4 / 1e-5.
    "over_claim_factor_at_sigma_0_3": 35.7,
}

# =============================================================================================
# 5. QUADRATURE_PARAMS — the oracle's two tuning constants, each MEASURED rather than chosen.
#
#    PROVENANCE: relative-error sweeps against the 60-dps mpmath ground truth, computed once in
#    the 22-RESEARCH session, committed as data so no test imports mpmath (RPT-03).
#
#    lam = 40.0 — the range rule is t_max = t_min + U with U = -z + sqrt(z*z + 2*lam), the exact
#      positive root of z*U + U**2/2 == lam. WHY 40 AND NOT 80: lam = 80 is safer on paper and
#      WORSE in practice, because at a fixed node count a wider range means a coarser h. Measured
#      (Simpson, n = 4001), lam = 20 leaves a truncation bound of ~6e-8 relative which DOMINATES
#      the total error; lam = 40 drives it to <= 1.21e-16, at or below double-precision
#      resolution, while keeping the finest h; lam = 80 and 160 buy nothing and cost an order of
#      magnitude in discretisation error. lam = 40 is the measured optimum, and the bound is
#      recomputed and checked at run time so the choice does not have to be trusted.
#
#    n = 20001 — composite Simpson nodes, with u = 0 (the integrand's kink at t_min) forced onto
#      a node. WHY MORE NODES IS NOT MONOTONICALLY BETTER: at n = 100001 the accumulation
#      round-off floor (~6e-14) takes over and three of five measured rows get WORSE. n = 20001
#      sits at the sweet spot; a future edit that "makes it safer" by raising n is making it
#      worse. (Simpson at n = 20001 also beats trapezoid at n = 400001 by 3-4 orders of magnitude
#      with 20x fewer nodes, which is why the rule is Simpson and not trapezoid.)
# =============================================================================================
QUADRATURE_PARAMS = {
    "lam": 40.0,
    "n": 20001,
}

# =============================================================================================
# 6. TOLERANCES — every one of them stated beside the measurement it clears.
#
#    PROVENANCE: 60-dps mpmath ground truth, computed once in the 22-RESEARCH session, committed
#    as data so no test imports mpmath (RPT-03).
# =============================================================================================

# The oracle's worst relative error ANYWHERE it returns a value, across the whole 12-row frontier
# (attained at eps=8, mu=0.5 — the row a fixed [-14, 14] range got wrong by 57 orders of
# magnitude, 1.00e+00 relative). Everything worse than this is REFUSED rather than returned.
WORST_RELATIVE_ERROR = 2.7e-12

# The pin tolerance for EPSILON_GOLDEN. Relative, never absolute: true delta spans 9.99e-1 down to
# 1.05e-57, so any absolute tolerance passes trivially for every row below its own magnitude —
# including a catastrophically wrong 0.0.
GOLDEN_EPSILON_REL_TOL = 1e-12
# ...against this measured worst-case gap between the two oracles' bisected epsilon (at
# sigma=2.0, T=200). ~2 orders of margin over the measurement, and ~2 orders tighter than any
# real implementation error would be.
GOLDEN_EPSILON_MEASURED_WORST_REL_GAP = 1.07e-14
