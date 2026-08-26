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
  - ``test_log_erfc_band_routes_accurately`` and its non-vacuity companion -> ``LOG_ERFC_BAND``
"""

# =============================================================================================
# 1. DELTA_FRONTIER — delta(eps, mu) for the analytic Gaussian mechanism (Balle-Wang Thm 8 /
#    Dong-Roth-Su Cor 2.13). The V-01 ground truth, 13 rows.
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
    # ---- THE THIRTEENTH ROW: RESEARCH F1'S TWIN, AND THE ONE NOBODY LOOKED AT ------------------
    # F1's finding is that past z ~ 38.47 the FIRST erfc underflows and BOTH oracles return 0.0.
    # Its twin is what happens EARLIER, in the band between the two cliffs: past b ~ 27.2 the
    # SECOND erfc underflows while the FIRST is still perfectly healthy. Measured here:
    # a = 3.015733201402912 with erfc(a) = 1.999999999999944e-05, and b = 28.01573320140291 with
    # erfc(b) = exactly 0.0. So delta_closed does NOT refuse — it returns a plausible number with
    # the whole second term silently discarded, worth 11.3% of the answer.
    #
    # THE CROSS-CHECK WAS STRUCTURALLY UNABLE TO SEE IT. Every one of the twelve rows above has a
    # healthy erfc(b) (largest b is 11.5, at the (8.0, 0.5) row), so V-01 and V-02 swept the whole
    # committed frontier without ever entering the band. Phase 22 verified `gaps_found` on exactly
    # this: the shipped closed form returned 9.99999999999972e-06 here — 12.7357% high against the
    # truth below, ZERO correct significant digits, under a docstring promising at least twelve.
    # This row exists so that the two-oracle agreement DPSGD-03 rests on is swept where it broke.
    #
    # THE INPUTS' MEANING: sigma = 0.40 / T = 200 at the frozen delta, i.e. mu = sqrt(200)/0.40 =
    # 35.35533905932738 (bit-exact), and eps = 775.7866600701457 — the epsilon the SHIPPED
    # accountant returned for that point, which is why b lands past the cliff. It is the exact
    # input `accountant.py`'s own comment cites as reachable on this project's frontier.
    #
    # PROVENANCE — THREE ROUTES, AGREEING, before the literal was committed:
    #   1. 60-dps mpmath, the truth below. ONE-OFF shell invocation, output committed as data:
    #        .venv/bin/python -c "
    #        from mpmath import mp
    #        mp.dps = 60
    #        eps = mp.mpf(775.7866600701457); mu = mp.mpf(35.35533905932738)
    #        a = (eps/mu - mu/2)/mp.sqrt(2); b = (eps/mu + mu/2)/mp.sqrt(2)
    #        print(mp.nstr(mp.mpf(0.5)*mp.erfc(a) - mp.mpf(0.5)*mp.exp(eps)*mp.erfc(b), 25))"
    #        # -> 8.870303048329795521072e-6
    #      The inputs go through `mp.mpf(<python float>)`, NOT `mp.mpf("<decimal string>")`.
    #      That is recorded because the two differ: measured, the string form gives
    #      8.870303048329874498e-6, a relative 8.90e-15 away. Both round to the SAME 13-digit
    #      literal below, so the artifact is unaffected — but a provenance that does not say which
    #      form was used is not reproducible.
    #   2. `delta_quadrature(775.7866600701457, 35.35533905932738)` — DIFFERENT MATHEMATICS
    #      (Simpson on the (eps,delta)-DP definition, `exp` only, no erfc and no Phi), float64:
    #      8.870303048231617e-06, a relative 1.107e-11 from route 1.
    #   3. `delta_closed` through the erfc asymptotic route, float64: 8.870303048329635e-06, a
    #      relative 1.814e-14 from route 1.
    #   Route 2 is the one that licenses this literal: it shares no transcendental with route 3
    #   beyond `exp`, so it cannot inherit the erfc cliff that produced the defect.
    (775.7866600701457, 35.35533905932738, "8.870303048330e-6"),
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
# 2b. EPSILON_OVERFLOW_REGIME — (sigma, steps, epsilon) at T = 200 for the ONLY two sigmas whose
#     solved epsilon walks past the `math.exp` overflow boundary (709.782712893384). Evaluated at
#     the frozen delta — stated as prose and NOT re-spelled as a literal, exactly as the
#     REJECTED_FORM_CROSSOVER block does; the consuming test resolves
#     `scripts/mitigation_unit.py::DELTA` and passes it in, which keeps ONE delta in the repository.
#
#     WHY IT EXISTS: `test_epsilon_for_survives_the_overflow_regime` parametrized over these two
#     sigmas — the two points where the dropped second term bit hardest — and asserted only that a
#     finite number above 700.0 came back. The test that walked directly into the defect never
#     compared its number to anything. These are the numbers it compares against now.
#
#     PROVENANCE: 60-dps mpmath + bisection to a 4096-wide bracket halved 400 times, ONE-OFF shell
#     invocation, output committed as data:
#       .venv/bin/python -c "
#       from mpmath import mp
#       mp.dps = 60
#       def d(eps, mu):
#           a = (eps/mu - mu/2)/mp.sqrt(2); b = (eps/mu + mu/2)/mp.sqrt(2)
#           return mp.mpf(0.5)*mp.erfc(a) - mp.mpf(0.5)*mp.exp(eps)*mp.erfc(b)
#       target = mp.mpf(1e-5)
#       for mu64 in (35.35533905932738, 47.14045207910317):
#           mu = mp.mpf(mu64); lo, hi = mp.mpf(0), mp.mpf(4096)
#           for _ in range(400):
#               mid = (lo+hi)/2
#               if d(mid, mu) <= target: hi = mid
#               else: lo = mid
#           print(mp.nstr(hi, 25))"
#     `mu` enters as `mp.mpf(<the float64 sqrt(steps)/sigma>)` and the target as `mp.mpf(1e-5)`,
#     i.e. the exact binary64 values `epsilon_for` itself computes and compares — so the deviation
#     measured against these truths is the implementation's own, with no input mismatch folded in.
#     (Recorded honestly: an independent bisection run while planning this row obtained
#     774.8427215876996890674888 and 1311.202790704405527755873 — a relative 6.6e-17 and 6.8e-17
#     from the literals below, i.e. under half a float64 ulp. At 1e-12 the choice between them is
#     four orders of magnitude below anything that can change a verdict; it is recorded rather than
#     silently reconciled because the last digits of a 25-digit literal are at the noise floor and
#     a reader should know it.)
#
#     WHAT THIS CONSTANT DOES **NOT** BUY, stated rather than overclaimed. It is a 60-dps
#     evaluation of the SAME closed form the implementation uses, so it catches float64 error and
#     asymptotic-truncation error and CANNOT catch a formula error — both sides would be wrong
#     together. That is precisely why D-13 has GOLDEN_EPSILON bisected against the QUADRATURE
#     oracle instead. Independence in THIS band is carried by the thirteenth DELTA_FRONTIER row's
#     V-02 leg, which compares the two oracles at exactly this (eps, mu); the coverage exists, but
#     it comes from that row and not from this constant.
#
#     THE SIZE OF WHAT IT NOW CATCHES: before this phase's fix the SHIPPED accountant returned
#     775.7866600701457 and 1312.1599912046381 for these two rows — a relative 1.218e-03 and
#     7.300e-04, in a module whose two published tolerances are both 1e-12. The error is EXACTLY
#     ZERO at sigma >= 0.42, so these two rows are the whole reachable band.
# =============================================================================================
EPSILON_OVERFLOW_REGIME = (
    (0.40, 200, "774.8427215876997401873883"),
    (0.30, 200, "1311.202790704405616448176"),
)

# =============================================================================================
# 2c. LOG_ERFC_BAND — log(erfc(x)) across `_log_erfc`'s ROUTING BOUNDARY, spanning ALL THREE
#     `math.erfc` regimes end to end: erfc still NORMAL, erfc SUBNORMAL, erfc exactly 0.0.
#
#     WHY A BAND AND NOT MORE POINTS. Round 1 pinned the single point where `math.erfc(b)` is
#     exactly 0.0, and the next verifier found the band immediately BELOW it — where `math.erfc`
#     returns a subnormal that has already discarded up to 52 of its 53 mantissa bits, and where
#     `_log_erfc`'s old `if erfc(x) > 0.0` predicate therefore routed everything to `math.log`.
#     A table of fixed points produces round 3. This table's parametrization IS the boundary's own
#     neighbourhood: the consuming sweep asserts that WHATEVER ROUTE `_log_erfc` CHOSE at x, that
#     route is accurate at x, and its companion classifies every row by `math.erfc` AT RUN TIME and
#     requires all three regimes non-empty. Any predicate `_log_erfc` could plausibly use draws its
#     boundary somewhere between "erfc is a healthy normal float" and "erfc is gone entirely", so a
#     band covering all three regimes straddles that boundary WITHOUT NAMING IT.
#
#     `x` is a FLOAT LITERAL — the exact binary64 the implementation evaluates — and the truth is a
#     DECIMAL STRING at 20 significant digits, for the same reason section 1 uses strings.
#
#     THREE ROWS ARE DELIBERATE AND NONE OF THEM IS DECORATION:
#       - 26.54325845425098 is the SUBNORMAL BOUNDARY ITSELF, bisected on this box. `math.erfc` at
#         the float below it is 2.2250738585076065e-308, which is NORMAL; at it, erfc is
#         2.225073858507186e-308, the first value strictly below float64's smallest normal
#         2.2250738585072014e-308. Three consecutive floats apart, and the whole defect lives there.
#       - 27.151124073213406 is `delta_closed`'s `b` at sigma=0.414 / T=200 — the WORST REACHABLE
#         POINT on this project's own frozen frontier, and the `b` plan 22-18's new frontier row
#         will use. Recorded precisely because the number moved when the defect closed: it is `b` at
#         the PRE-FIX epsilon 728.2043182233367 (erfc = 1.43e-322). The post-fix `epsilon_for` at
#         that sigma returns 728.1896631303155, whose `b` is 27.150820712787866 (erfc = 1.5e-322).
#         Both are subnormal and both are in the band; the pre-fix one is pinned because it is the
#         point 22-VERIFICATION.md measured the 1.919e-03 two-oracle gap at.
#       - 26.8 CLOSES A GRANULARITY GAP IN THE UP DIRECTION, and MUST NOT BE PRUNED AS REDUNDANT.
#         Without it the band jumps 26.7 -> 26.9. MEASURED here: row 26.7 scores 4.7584e-16 under
#         route L and PASSES the 1e-15 budget, so a boundary moved up to anywhere in (26.7, 26.9]
#         would leave the sweep GREEN. With 26.8 in the table (3.0228e-14 under route L — reddens)
#         the hideable window shrinks to (26.7, 26.8], and the largest route-L error a boundary
#         hidden in it can carry is under 3.03e-14.
#
#     PROVENANCE — 60-dps mpmath, ONE-OFF shell invocation, its OUTPUT committed here as data
#     (RPT-03; `tests/test_phase22_reference.py::test_no_phase22_test_imports_mpmath` enforces the
#     no-import rule by AST over the whole `test_phase22_*` glob):
#
#       .venv/bin/python -c "from mpmath import mp; mp.dps=60; [print(repr(x),
#       mp.nstr(mp.log(mp.erfc(mp.mpf(x))), 20)) for x in (24.0, 25.0, 26.0, 26.4,
#       26.54325845425098, 26.6, 26.65, 26.7, 26.8, 26.9, 27.0, 27.151124073213406, 27.19, 27.2,
#       27.6, 28.01573320140291, 29.0)]"
#
#     The inputs enter as `mp.mpf(<python float>)`, NOT as `mp.mpf("<decimal string>")`. That is
#     recorded because the two forms DIFFER — 22-12 measured 8.90e-15 between them on the thirteenth
#     frontier row — so a provenance that does not say which was used is not reproducible. Taking
#     the python float means the truth is log(erfc(x)) at the SAME x the code evaluates, with no
#     input mismatch folded into the deviation measured. (Cross-check: the 28.01573320140291 row
#     agrees to every digit with the 25-digit literal
#     `test_log_erfc_matches_the_committed_underflow_truth` already carries.)
#
#     WHAT THIS TABLE DOES **NOT** BUY, stated rather than overclaimed, exactly as
#     EPSILON_OVERFLOW_REGIME's own block does for its narrower case. It is `mpmath`'s own `erfc`
#     at 60 dps, so it catches a ROUTING error and a FLOAT64 error and CANNOT catch an error in the
#     asymptotic expansion's DERIVATION — for that to slip through, mpmath's erfc and this module's
#     hand-rolled series would have to be wrong TOGETHER. They come from different implementations
#     by different authors, which is why this is a real constraint and not a photograph of the code.
# =============================================================================================
LOG_ERFC_BAND = (
    (24.0, "-579.75128495304457696"),
    (25.0, "-628.79203917407168537"),
    (26.0, "-679.83119976319423026"),
    (26.4, "-700.80644507223147169"),
    (26.54325845425098, "-708.39641853226411327"),
    (26.6, "-711.41398156849619185"),
    (26.65, "-714.07835686349255419"),
    (26.7, "-716.74772865324142255"),
    (26.8, "-722.10146176916819577"),
    (26.9, "-727.47518101989586635"),
    (27.0, "-732.86888650789741098"),
    (27.151124073213406, "-741.05799894069437943"),
    (27.19, "-743.17198938084895565"),
    (27.2, "-743.71625659997681358"),
    (27.6, "-765.65083601676106754"),
    (28.01573320140291, "-788.78707403515630585"),
    (29.0, "-844.94025442214730431"),
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

# The oracle's worst relative error ANYWHERE it returns a value, across the whole 13-row frontier.
# RE-MEASURED when the thirteenth row landed, because that row moved it: the worst is now
# **1.107e-11**, at (eps=775.7866600701457, mu=35.35533905932738), where the quadrature integrates
# over a support starting at t_min = 39.62 and the accumulated Simpson round-off is the binding
# term. The previous holder — eps=8, mu=0.5, the row a fixed [-14, 14] range got wrong by 57
# orders of magnitude (1.00e+00 relative) — sits at 3.6e-13. Everything worse than this is REFUSED
# rather than returned.
#
# This is the ORACLE's error, and it is deliberately NOT the budget V-02 compares the two oracles
# at (1e-9, which the new row clears by 90x). A bound recorded over 12 rows and left standing over
# 13 is exactly the stale-denominator failure this table exists to prevent.
WORST_RELATIVE_ERROR = 1.2e-11

# The pin tolerance for EPSILON_GOLDEN. Relative, never absolute: true delta spans 9.99e-1 down to
# 1.05e-57, so any absolute tolerance passes trivially for every row below its own magnitude —
# including a catastrophically wrong 0.0.
GOLDEN_EPSILON_REL_TOL = 1e-12
# ...against this measured worst-case gap between the two oracles' bisected epsilon (at
# sigma=2.0, T=200). ~2 orders of margin over the measurement, and ~2 orders tighter than any
# real implementation error would be.
GOLDEN_EPSILON_MEASURED_WORST_REL_GAP = 1.07e-14
