"""From-scratch (eps, delta) accountant for the analytic Gaussian mechanism (DPSGD-03).

Every epsilon this project publishes is a number this module returned. Unlike an RDP accountant
-- an integer-alpha grid, a ``logsumexp`` binomial sum over the subsampled Gaussian, a
grid-truncation guard, and a Balle conversion back to (eps, delta) -- this computes the
(eps, delta) curve **exactly**. At ``q = 1`` (no subsampling; Phase 21 D-07/D-23 froze
``scripts/mitigation_unit.py::SAMPLING_RATE_Q`` at 1.0) the Gaussian mechanism's privacy-loss
random variable is itself exactly Gaussian, so Balle-Wang Theorem 8 (arXiv 1805.06530, eq. 6) is
an **iff** rather than a sufficient condition, and Dong-Roth-Su Corollary 2.13 (arXiv 1905.02383)
reaches the identical expression from trade-off functions. There is no slack left to tighten.

``.planning/research/STACK.md``'s hand-rolled-RDP recommendation is therefore **SUPERSEDED by
q = 1**, not an alternative worth weighing (RESEARCH F5): build no alpha grid, no ``logsumexp``,
and no grid-truncation guard here. At q = 1 the RDP route is strictly looser for strictly more
code.

Invariants (each one pinned by ``tests/test_phase22_accountant.py``):

  - ``sigma`` IS THE NOISE MULTIPLIER ``sigma_noise / clip_norm``, unitless -- never the raw
    standard deviation of the added noise. So ``mu = 1/sigma`` and ``mu_eff = sqrt(T)/sigma``, and
    the clip constant cancels out of the accounting entirely. The basis is a FROZEN artifact
    rather than a preference: ``scripts/mitigation_gate.py::MECHANISM_KEYS`` is
    ``("sigma", "steps", "delta", "q")`` and that module's own comment beside it says there is no
    fifth key. **Adding a ``clip_norm=`` parameter to this module would create that fifth key** --
    a mechanism parameter the frozen gate states does not exist. Consistency with
    ``MECHANISM_KEYS`` is not a style question here (RESEARCH F4).

  - THE ADJACENCY RELATION IS **add/remove one fact**, and its sensitivity multiplier is **1.0**
    (``Delta = 1.0 * C``). Removing one record changes the clipped sum by ``g_i``, whose norm is at
    most ``C`` -- the textbook sensitivity argument, and it is the add/remove-one argument. Under
    replace-one it would be ``2C`` and every published epsilon would be roughly 2x larger. Those
    are the same words as ``scripts/mitigation_accountant.py::NEIGHBOURING`` and
    ``::SENSITIVITY_MULTIPLIER`` on purpose: this docstring is one of the three sites the
    cross-site consistency test
    ``tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent`` reads, and that test
    refuses on disagreement. The pin **cannot be imported here** -- ``src/`` never puts
    ``scripts/`` on the path, and the pre-registration import ceiling runs the other way -- which
    is exactly why agreement is checked by reading sources rather than by an import.

  - THE SILENT-ZERO DOMAIN LIMIT IS SHARED, NOT ISOLATED TO ONE ORACLE. ``math.erfc`` underflows
    to exactly ``0.0`` past x ~ 27.2, so ``delta_closed`` returns ``0.0`` once
    ``z = eps/mu - mu/2`` exceeds 38.466608897 -- and ``delta_quadrature`` returns ``0.0`` once z
    exceeds 38.372164249, because both are governed by that one z. A returned ``0.0`` is
    **provably wrong**: delta is strictly positive for every finite eps and every mu > 0, since
    the Gaussian has full support and the integrand is positive on a set of positive measure. Both
    functions therefore REFUSE in that corner instead of returning a plausible-looking number. Two
    independent implementations buy nothing when both fail on the same underlying quantity
    (RESEARCH F1), so without the refusal the two-oracle cross-check passes on ``0.0 == 0.0``
    against a true ``1.24028351258e-352``.

  - REFUSALS ARE ``raise ValueError`` -- **never** ``assert``, which is stripped under
    ``python -O`` and would turn a loud refusal into a silently wrong published delta
    (``lora/layer.py::LoRALinear.merge``'s docstring records that reason for this repository), and
    **never** ``_prove``, which is a ``scripts/`` convention (measured: 18 ``scripts/`` modules,
    0 ``src/`` modules).

  - THE TOLERANCE REGISTER HAS TWO ENTRIES AND THEY ARE WRITTEN DOWN TOGETHER, because the whole
    risk is that they get conflated:

      * **TWO DIFFERENT CALL SHAPES => a RELATIVE TOLERANCE of 1e-12, never ``==``.** The q = 1
        composition identity ``epsilon_for(sigma, T, delta) == epsilon_for(sigma/sqrt(T), 1,
        delta)`` is EXACT in real arithmetic (Dong-Roth-Su Corollary 3.3 is an exact equality of
        trade-off functions), and it still FAILS BITWISE 19.9% of the time in float64 -- 795 of
        4000 sampled pairs, worst relative gap 1.184e-14 (82 ulp), purely from double-rounding:
        ``sqrt(T)/sigma`` costs two roundings and ``1.0/(sigma/sqrt(T))`` costs three (RESEARCH
        F3). The MATHEMATICS is confirmed exact; only its transcription as ``==`` is wrong.

      * **THE SAME CALL SHAPE ACROSS TWO PROCESSES => exact ``==``.** DPSGD-05's kill->resume
        check compares one call shape run twice, which is deterministic, so equality is the
        correct assertion and a tolerance would only weaken it. That is
        ``lora/inject.py::load_adapter_weights``'s W1 reasoning applied here: the same operation
        on the same operands gives a bit-identical float, and *"a tolerance would only weaken
        this"* is its own recorded wording.

    Neither entry generalises to the other's case.

This module imports ``math`` and nothing else (D-10), so ``pyproject.toml`` stays untouched and
RPT-03's zero-new-dependency streak holds. ``tests/test_phase22_accountant.py``'s V-09 asserts
that as a hard equality, statically and out-of-process.
"""

import math

_SQRT2 = math.sqrt(2.0)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)
_SQRT_PI = math.sqrt(math.pi)

# math.exp raises "OverflowError: math range error" strictly above this argument (bisected). It
# bounds the quadrature oracle's conditioning in the NEGATIVE-z direction, and it is the same
# constant RESEARCH F2 measured for the closed form's rejected `exp(eps) * erfc(b)` product.
_EXP_OVERFLOW_ARG = 709.782712893384

# Both bisections stop at this RELATIVE width of their own variable, or at the iteration cap,
# whichever comes first. 1e-15 is a little over one float64 ulp (2.22e-16), so the cap is a
# backstop against a bracket that cannot narrow rather than the normal exit: a bracket of relative
# width 1 reaches 1e-15 in about 50 halvings.
_BISECT_REL_WIDTH = 1e-15
_MAX_BISECTIONS = 200

# The doubling walk's cap. From a start of 1.0 this reaches 2**200 ~ 1.6e60 before refusing, which
# is finite by construction -- so no non-finite eps ever reaches `delta_closed`, and its
# non-finite-input refusal is therefore UNREACHABLE from the search. That is what makes
# `_delta_or_below_float64` able to read a caught ValueError as the underflow corner and nothing
# else (see its docstring).
_MAX_DOUBLINGS = 200

# The smallest target delta `epsilon_for` will solve for. NOT arbitrary: the search reads a
# `delta_closed` refusal as "delta here is below float64's range, so below the target", and that
# reading needs headroom over float64's subnormal floor to be airtight. MEASURED, at every mu from
# 1e-8 to 1e8, `delta_closed` returns exactly 5e-324 -- the smallest positive float64 -- at the
# last eps before it refuses. Any target at or below that floor would make "below the target"
# ambiguous by less than one subnormal; 1e-300 is 24 decades of margin, and no delta a DP report
# can name comes anywhere near it (this project's frozen delta is 1e-5).
_MIN_TARGET_DELTA = 1e-300

# The round-trip budget for `sigma_for(epsilon_for(sigma, T, delta), T, delta)` against `sigma`.
# MEASURED ACHIEVABLE: 8.29e-15 worst relative deviation over 48 (sigma, T) pairs -- the seven
# GOLDEN_EPSILON sigmas plus 0.5, 0.7, 1.5, 3.0 and 50.0, each at T in {1, 64, 200, 1000}. So this
# carries a little over two orders of margin, and it is deliberately NOT tightened to the
# measurement: the number above is one machine's 48 points, not a bound.
#
# (For scale, the OTHER 1e-12 in this module is a different quantity measured on a different
# thing: `GOLDEN_EPSILON_REL_TOL` covers the gap between the two ORACLES' bisected epsilon, worst
# case 1.07e-14. Same tolerance, unrelated denominators.)
ROUND_TRIP_REL_TOL = 1e-12


def _log_erfc(x):
    """``log(erfc(x))``, carried through the point where ``math.erfc`` itself underflows to 0.0.

    **THE FAST PATH IS UNCONDITIONAL AND FIRST, AND THAT INERTNESS IS THE LOAD-BEARING PROPERTY
    OF THIS FUNCTION -- not a side effect of it.** Wherever ``math.erfc(x) > 0.0`` this returns
    ``math.log(math.erfc(x))`` and computes nothing else, which is bit-for-bit the arithmetic
    ``delta_closed`` already performed on its ``else`` branch. That is what makes adding this
    helper a PROVABLE NO-OP on every point the module already answers -- all seven
    ``scripts/mitigation_accountant.py::GOLDEN_EPSILON`` epsilons and all eleven previously
    representable ``DELTA_FRONTIER`` deltas are BIT-IDENTICAL across this change, asserted by
    ``tests/test_phase22_accountant.py::test_log_erfc_is_inert_where_erfc_is_healthy`` with exact
    ``==`` rather than a tolerance. ``GOLDEN_EPSILON`` is a FROZEN pre-registration with no
    correction path, so a routing change that sent healthy inputs through the series below would
    be unrecoverable rather than merely wrong: measured, deleting this fast path moves six of the
    seven pinned epsilons, four of them to ``0.0``.

    Past ``x ~ 27.2`` ``math.erfc`` underflows to exactly ``0.0`` and ``math.log`` can no longer
    be applied to it, but ``log(erfc(x))`` is still a perfectly ordinary number there
    (``-788.79`` at the x this module actually reaches). The asymptotic expansion for large
    positive x is what recovers it::

        log(erfc(x)) = -x*x - log(x*sqrt(pi)) + log(S),
        S = 1 - 1/(2x**2) + 3/(4x**4) - 15/(8x**6) + ...

    successive terms multiplying by ``-(2n-1)/(2x**2)``. The series is DIVERGENT, so it is summed
    under the standard OPTIMAL-TRUNCATION rule -- stop at the first term that is not strictly
    smaller than its predecessor -- with a relative floor and a hard term cap so no argument can
    loop. MEASURED against mpmath at ``mp.workdps(120)`` over
    ``x in {27.2, 27.20000001, 27.3, 28.0, 29.0, 32.0, 45.0, 80.0, 150.0}`` plus the
    ``x = 28.01573320140291`` this module reaches: worst ABSOLUTE error in the returned log
    **7.64e-13** (at x = 150.0), and **5.96e-14** at that 28.0157. Every one of those is BELOW ONE
    ULP of the returned log (worst 0.881 ulp, at x = 29.0), so what is being measured is float64's
    own resolution rather than truncation error. An absolute error ``d`` in the log is a relative
    error ``d`` in ``exp(eps + log)``, so those numbers ARE the relative error the second term
    inherits.

    Args:
        x: the erfc argument. Any float; the series branch is reached only when ``erfc(x)``
            has underflowed, which requires ``x > 27.2``.

    Returns:
        ``log(erfc(x))``. ``-inf`` at an argument so large that ``-x*x`` overflows (checked:
        ``_log_erfc(1e200)`` is ``-inf``, and ``math.exp(eps + -inf)`` is ``0.0``, which is the
        correct second term there rather than an exception).

    Raises:
        ValueError: when ``erfc(x)`` underflowed at ``x <= 0.0``, which is impossible.
    """
    e = math.erfc(x)
    if e > 0.0:
        return math.log(e)
    if x <= 0.0:
        raise ValueError(
            f"_log_erfc({x!r}): erfc underflowed to exactly 0.0 at a NON-POSITIVE argument, which "
            f"is impossible -- math.erfc is monotonically decreasing with erfc(x) >= 1.0 for every "
            f"x <= 0.0, so this means the argument is not the quantity the caller believes it is. "
            f"UNREACHABLE FROM delta_closed: the series branch requires erfc(x) == 0.0, which "
            f"first happens at x ~ 27.2, and delta_closed's b = (eps/mu + mu/2)/sqrt(2) would "
            f"therefore be > 27.2 > 0. Kept as a domain guard in the same spirit as delta_closed's "
            f"own first two refusals, which are likewise unreachable from the search."
        )

    inv = 1.0 / (2.0 * x * x)
    term = 1.0
    total = 1.0
    for n in range(1, 61):
        nxt = term * (-(2 * n - 1) * inv)
        # OPTIMAL TRUNCATION: an asymptotic series stops helping at its smallest term, so the
        # first term that is not strictly smaller than its predecessor is discarded rather than
        # added. The relative floor exits early once the tail is below float64's resolution, and
        # the range cap bounds a pathological x rather than being the normal exit.
        if not abs(nxt) < abs(term):
            break
        total += nxt
        term = nxt
        if abs(nxt) <= 1e-17 * abs(total):
            break
    return -x * x - math.log(x * _SQRT_PI) + math.log(total)


def delta_closed(eps, mu):
    """delta(eps, mu) for the analytic Gaussian mechanism -- Balle-Wang Theorem 8, closed form.

    ``Phi(x) = 0.5 * erfc(-x/sqrt(2))`` turns
    ``Phi(mu/2 - eps/mu) - exp(eps) * Phi(-mu/2 - eps/mu)`` into two ``math.erfc`` calls, which is
    the whole reason a stdlib-only accountant is possible at all.

    Args:
        eps: the privacy loss epsilon, finite. Not required to be < 1 -- that restriction belongs
            to the classical Gaussian mechanism this project rejects
            (``scripts/mitigation_accountant.py::REJECTED_FORM``), not to Theorem 8.
        mu: the GDP parameter, strictly positive. For a single step ``mu = 1/sigma``; for T-fold
            composition ``mu = sqrt(T)/sigma`` (Dong-Roth-Su Cor 3.3). ``mu = 0.0`` means
            ``sigma = inf`` and is ``epsilon_for``'s boundary to own, not this function's.

    Returns:
        ``delta`` in ``(0, 1]``, carrying at least 12 significant digits of the 60-dps ground truth
        everywhere this function does not refuse. Measured against the committed
        ``tests/fixtures/phase22_reference.py::DELTA_FRONTIER`` truths, the largest deviation over
        the eleven float64-representable rows is **1.84e-12 relative, at eps=2.0, mu=0.1** -- and
        that row's committed truth carries only 11 significant digits, so ~5e-11 of that budget is
        the reference string's own quantization rather than this function's error. The largest
        deviation on a 13-digit row is **9.03e-13, at eps=8.0, mu=0.5**.

    Raises:
        ValueError: on a non-finite input or ``mu <= 0.0``; when delta is below float64's range
            (a domain limit, reported as a refusal and never as a number); or when the computed
            delta is non-positive, which is provably wrong.
    """
    # --- Refusal 1 of 3: DOMAIN. mu <= 0.0 must be caught BEFORE eps/mu, or mu == 0.0 leaves as a
    # ZeroDivisionError -- an accident rather than a decision. mu == 0.0 means sigma = inf and its
    # answer (delta -> 0, epsilon -> 0) belongs to the inverse solver, not here.
    if not math.isfinite(eps) or not math.isfinite(mu):
        raise ValueError(
            f"delta_closed({eps!r}, {mu!r}): both arguments must be finite. A non-finite input "
            f"reaches erfc as a nan and returns a nan delta, which every downstream comparison "
            f"then passes silently."
        )
    if mu <= 0.0:
        raise ValueError(
            f"delta_closed({eps!r}, {mu!r}): mu must be strictly positive (mu = 1/sigma for one "
            f"step, sqrt(T)/sigma for T-fold composition). mu == 0.0 is sigma = inf, which is the "
            f"inverse solver's boundary to own; mu < 0.0 is not a mechanism."
        )

    # z is the support boundary measured in standard deviations, and `a` is exactly z/sqrt(2).
    # That is NOT a coincidence and it is why both oracles die at nearly the same z: the closed
    # form's first erfc argument and the quadrature's exponent are the same number wearing two
    # hats, so two independent implementations share one failure mode in this corner (F1).
    z = eps / mu - mu / 2.0
    a = z / _SQRT2
    b = (eps / mu + mu / 2.0) / _SQRT2

    # exp(eps + log(erfc(b))), NEVER exp(eps) * erfc(b). The naive product raises
    # "OverflowError: math range error" for eps > 709.782712893384 (bisected), and that eps is
    # REACHABLE on this project's own frontier, not a pathological input: solving epsilon_for at
    # sigma=0.40, T=200 against the frozen delta gives eps = 775.79, and sigma_for walks there
    # while bisecting sigma downward.
    #
    # THE LOG IS `_log_erfc(b)` AND NOT `math.log(math.erfc(b))`, AND IT IS UNCONDITIONAL. The
    # shipped form guarded the log on `math.erfc(b)` being exactly zero and substituted 0.0 for
    # the WHOLE second term there, under a comment claiming log space "keeps the identical product
    # below the line" while citing sigma=0.40/T=200 -- the exact point at which that guard fired
    # and the log-space branch therefore never executed at all. MEASURED at
    # (eps=775.7866600701457, mu=35.35533905932738), i.e. that very point: `math.erfc(b)` is
    # exactly 0.0 while `math.exp(eps)` is ~8.3e336, so the true second term is 1.1297e-06 against
    # a first term of 9.99999999999972e-06. Treating the underflow as a negligible term returned
    # 9.99999999999972e-06 against a 60-dps truth of 8.870303048329795e-06 -- **12.7357% high,
    # ZERO correct significant digits**, and it did not refuse, under a docstring promising at
    # least twelve. Across a delta=1e-5 (sigma, T) grid, 19 of 72 cells disagreed with the
    # quadrature oracle above 1e-9, worst 11.36%.
    #
    # THE DIRECTION, RECORDED HONESTLY: `second >= 0`, so dropping it OVER-states delta and
    # therefore OVER-states epsilon. That is the CONSERVATIVE direction, which is why this was a
    # latent wrong number rather than a live privacy break -- and why it survived a phase.
    second = 0.5 * math.exp(eps + _log_erfc(b))

    # --- Refusal 2 of 3: REPRESENTABILITY. Report the domain limit, never a number.
    ea = math.erfc(a)
    if ea == 0.0:
        raise ValueError(
            f"delta_closed({eps!r}, {mu!r}): delta is below float64's range and this is a DOMAIN "
            f"LIMIT, not a number to return. erfc(z/sqrt(2)) underflowed to exactly 0.0 at "
            f"z = eps/mu - mu/2 = {z!r}; the measured boundary is z = 38.466608897. Returning "
            f"0.0 here is what makes the two-oracle cross-check pass on 0.0 == 0.0 against a true "
            f"delta of order 1e-352 (RESEARCH F1), so this refuses instead."
        )

    delta = 0.5 * ea - second

    # --- Refusal 3 of 3: EXACT ZERO. NOT implied by refusal 2, and the reason is structural.
    # Refusal 2 only proves the FIRST term survived. What is returned is a DIFFERENCE whose two
    # terms have ratio exactly a/b in exact arithmetic, so the subtraction cancels roughly
    # mu**2/eps of the leading digits and can round to <= 0.0 while erfc(a) is still strictly
    # positive. A representability check on one term therefore cannot stand in for a check on the
    # result -- which is the same shape as the quadrature oracle's condition 3, where a
    # truncation-RELATIVE test degenerates to `0.0 > 0.0` = False in exactly the corner it exists
    # to catch.
    if delta <= 0.0:
        raise ValueError(
            f"delta_closed({eps!r}, {mu!r}) computed delta = {delta!r}, which is provably wrong: "
            f"delta is STRICTLY positive for every finite eps and every mu > 0, because the "
            f"Gaussian has full support and the integrand is positive on a set of positive "
            f"measure. This check is NOT implied by the representability refusal above -- that "
            f"one proves erfc(z/sqrt(2)) != 0.0, while this is a difference of two terms whose "
            f"cancellation can reach 0.0 with both terms individually representable."
        )
    return delta


def delta_quadrature(eps, mu, *, lam=40.0, n=20001, rel_tol=1e-9):
    """delta(eps, mu) by direct numerical integration of the (eps, delta)-DP DEFINITION (D-13).

    THE SECOND ORACLE, AND IT IS DIFFERENT MATHEMATICS RATHER THAN A SECOND SPELLING. ``math.exp``
    and ``math.sqrt`` only -- no ``Phi``, no ``erfc``, no ``math.log``. With ``t ~ N(mu, 1)`` and
    privacy loss ``L = mu*t - mu**2/2``, delta is ``E[max(0, 1 - exp(eps - L))]``; this evaluates
    that expectation on a grid whose range is DERIVED from (eps, mu) rather than fixed. DPSGD-03
    requires an oracle that cannot share the implementation's failure modes, so it may share no
    transcendental with ``delta_closed`` beyond ``exp`` itself.

    THE SUBSTITUTED FORM, WHICH IS AN EXACT ALGEBRAIC IDENTITY ON THAT INTEGRAL AND NOT A DIFFERENT
    INTEGRAL. ``max(0, .)`` is non-zero exactly when ``L > eps``, i.e. when
    ``t > t_min = eps/mu + mu/2``.
    Since ``mu*t_min - mu**2/2 == eps`` by construction, substituting ``u = t - t_min`` makes the
    exponent ``eps - L`` become exactly ``-mu*u`` and ``t - mu`` become ``u + z``, where
    ``z = t_min - mu = eps/mu - mu/2``::

        delta = phi(z) * integral_0^inf exp(-z*u - u*u/2) * (1 - exp(-mu*u)) du

    It buys three things, each measured rather than argued:
      - ``exp(eps)`` never appears, so RESEARCH F2's overflow at eps > 709.78 cannot reach the
        oracle at all.
      - The ``max(0, .)`` clamp disappears, because the domain IS the support.
      - The non-vacuity test stays NON-DEGENERATE where the literal form's silently dies. Under the
        literal form the truncation bound underflows in exactly the regime delta does, so
        ``trunc > rel_tol * delta`` degenerates to ``0.0 > 0.0`` = False and the guard is inert on
        the very failure it exists to catch. In the scaled form ``trunc/I`` stays a finite ~1e-33
        in every one of RESEARCH F1's rows, because ``I`` never underflows -- only the ``phi(z)``
        prefactor does, and condition 1 catches that cleanly.

    Args:
        eps: the privacy loss epsilon, finite.
        mu: the GDP parameter, strictly positive (``mu = 1/sigma``, or ``sqrt(T)/sigma`` composed).
        lam: the tail-exponent budget setting the integration WIDTH. Measured optimum 40.0 -- see
            the ``U`` comment in the body for why 20 is too narrow and 80 is worse, not safer.
        n: composite-Simpson node count, ODD (an even panel count). Measured optimum 20001 -- see
            the ``h`` comment for why raising it makes the oracle worse, not safer.
        rel_tol: the relative truncation budget condition 2 proves the range met.

    Returns:
        ``delta`` in ``(0, 1]``. Worst relative error ANYWHERE this returns a value, measured over
        the eleven representable ``DELTA_FRONTIER`` rows against 60-dps ground truth, is
        **1.0e-12** -- and that row (eps=2.0, mu=0.1) carries an 11-digit committed truth, so most
        of that budget is the reference string's own quantization. The worst deviation on a 13-digit
        row is **3.6e-13, at eps=8.0, mu=0.5**: the low-privacy corner where a fixed ``[-14, 14]``
        range gives relative error **1.00e+00**, returning a perfectly plausible ``0.0`` against a
        true ``1.048659178913e-57``. Everything worse than this is REFUSED rather than returned.

    Raises:
        ValueError: on a degenerate input or grid, or on any of the three non-vacuity conditions.
    """
    # --- Input refusals, each separately messaged (D-15). mu <= 0.0 must precede eps/mu.
    if not math.isfinite(eps) or not math.isfinite(mu) or not math.isfinite(lam):
        raise ValueError(
            f"delta_quadrature({eps!r}, {mu!r}, lam={lam!r}): eps, mu and lam must all be finite. "
            f"A non-finite input propagates through exp() as a nan and returns a nan delta, which "
            f"every downstream comparison then passes silently."
        )
    if mu <= 0.0:
        raise ValueError(
            f"delta_quadrature({eps!r}, {mu!r}): mu must be strictly positive. mu == 0.0 is "
            f"sigma = inf, which is the inverse solver's boundary to own; mu < 0.0 is not a "
            f"mechanism, and it would also invert the derived integration range."
        )
    if lam <= 0.0:
        raise ValueError(
            f"delta_quadrature(lam={lam!r}): lam must be strictly positive. It is the tail "
            f"exponent U solves for, so lam <= 0.0 yields U <= 0 and a grid that runs backwards "
            f"across zero width."
        )
    if n < 3 or n % 2 == 0:
        raise ValueError(
            f"delta_quadrature(n={n!r}): composite Simpson needs an ODD node count >= 3 (an EVEN "
            f"panel count). An even n silently applies 4/2 weights to a half panel and degrades "
            f"the rule to something with no stated order, which would then be compared against a "
            f"tolerance calibrated for Simpson."
        )

    # z is the support boundary in standard deviations from the sampling density's mean, and it is
    # the SAME number as sqrt(2) * delta_closed's first erfc argument. That is why the two oracles
    # share a failure mode in this corner despite being different mathematics (RESEARCH F1).
    z = eps / mu - mu / 2.0
    ez = -0.5 * z * z

    # --- Condition 1 of 3: phi(z) is not representable. Checked BEFORE the 20,001-node loop, not
    # after: for z beyond this boundary the loop's own exp() would raise a bare OverflowError first
    # and the domain limit would surface as an unrelated arithmetic error instead of as a stated
    # refusal. The second clause is the NEGATIVE-z half of the same conditioning limit -- the
    # scaled form separates a tiny phi(z) prefactor from a huge integral, and for z < -37.677 that
    # integral's own exp overflows (measured: mu=76, eps=0.001 -> z = -38.0 -> OverflowError).
    if ez <= -745.0 or (z < 0.0 and ez < -_EXP_OVERFLOW_ARG):
        raise ValueError(
            f"delta_quadrature({eps!r}, {mu!r}): this is a DOMAIN LIMIT, not a range bug and not a "
            f"number to return. At z = eps/mu - mu/2 = {z!r} the scaled form's phi(z) prefactor "
            f"(exp({ez!r})) leaves float64's representable band, so delta is below float64 range "
            f"(z > 0) or the separated integral overflows (z < 0). Reporting a number here is how "
            f"a true delta of order 1e-352 becomes a published 0.0."
        )

    # THE DERIVED RANGE. U is the exact positive root of z*U + U**2/2 == lam, so the discarded tail
    # sits below exp(-lam)/(U+z) by the Mills bound used in condition 2. Well-defined for ALL real
    # z, including negative (eps=0.1, mu=4 gives z = -1.975, U = 14.78), and U + z =
    # sqrt(z*z + 2*lam) > 0 always, which is exactly what that bound needs.
    #
    # A WIDTH RULE, NOT A CONSTANT, because U must adapt in BOTH directions: at eps=8, mu=0.5 the
    # integrand is dead within U = 4.45 and a wide range would only waste resolution, while at
    # eps=0.01, mu=8 it needs U = 17.26. A fixed [-14, 14] is wrong at the first end by 57 orders
    # of magnitude (D-13's measured 0.0 against a true 1.049e-57).
    #
    # lam = 40.0 IS THE MEASURED OPTIMUM AND 80 IS WORSE, NOT SAFER. At a fixed node count a wider
    # range means a coarser h. Measured (Simpson, n = 4001): lam = 20 leaves a ~6e-8 relative
    # truncation bound that DOMINATES the total error; lam = 40 drives it to <= 1.21e-16, at or
    # below double-precision resolution, while keeping the finest h; lam = 80 and 160 buy nothing
    # and cost an order of magnitude in discretisation error.
    U = -z + math.sqrt(z * z + 2.0 * lam)

    # n = 20001 IS THE MEASURED OPTIMUM AND MORE NODES IS NOT MONOTONICALLY BETTER. At n = 100001
    # the accumulation round-off floor (~6e-14) takes over and three of five measured rows get
    # WORSE. A future edit that "makes this safer" by raising n is making it worse. (Simpson at
    # n = 20001 also beats trapezoid at n = 400001 by 3-4 orders with 20x fewer nodes, which is why
    # the rule is Simpson and not trapezoid.)
    h = U / (n - 1)

    # THE GRID STARTS EXACTLY AT u = 0, i.e. exactly at t_min, and that is a MEASURED REQUIREMENT
    # rather than tidiness. The integrand has a kink there -- identically 0 below, right-derivative
    # phi(t_min - mu)*mu > 0 above -- and putting that kink inside a panel instead of on a node
    # costs up to six orders of magnitude (measured 3.30e-13 on-node against 1.07e-06 offset by
    # half a step). The u = 0 endpoint's own value is exactly 0.0 (1 - exp(0) == 0.0); it is
    # written into the sum anyway so the rule reads as the composite Simpson it is.
    total = math.exp(0.0) * (1.0 - math.exp(0.0))
    for i in range(1, n - 1):
        u = i * h
        w = 4.0 if i % 2 else 2.0
        total += w * math.exp(-z * u - 0.5 * u * u) * (1.0 - math.exp(-mu * u))
    total += math.exp(-z * U - 0.5 * U * U) * (1.0 - math.exp(-mu * U))
    integral = total * h / 3.0

    # --- Condition 2 of 3: the range PROVABLY captured the support. Completing the square,
    # -z*u - u**2/2 == z*z/2 - (u+z)**2/2, so the discarded tail of the scaled integral is at most
    # exp(z*z/2)*sqrt(2*pi)*Qbar(U+z) <= exp(-z*U - U**2/2)/(U+z) == exp(-lam)/(U+z), using
    # Qbar(x) <= phi(x)/x for x > 0 and U + z = sqrt(z*z + 2*lam) > 0. One exp and one divide, and
    # it is a PROOF that the range captured the support rather than an assertion that it did.
    trunc = math.exp(-lam) / (U + z)
    if trunc > rel_tol * integral:
        share = trunc / integral if integral else float("inf")
        raise ValueError(
            f"delta_quadrature({eps!r}, {mu!r}, lam={lam!r}): the derived range did NOT provably "
            f"capture the support. The rigorous Mills bound on the discarded tail is {trunc!r} "
            f"against a captured integral of {integral!r} -- a relative {share!r}, over the "
            f"budget {rel_tol!r}. Widen lam rather than trusting the number."
        )

    delta = _INV_SQRT_2PI * math.exp(ez) * integral

    # --- Condition 3 of 3: EXACT ZERO, and it is NOT implied by condition 2. Measured: in the band
    # 38.372164249 < z < 38.6005 the phi(z) prefactor is still representable (condition 1 silent)
    # and trunc/I stays ~3.2e-15 (condition 2 silent), yet the product underflows to exactly 0.0.
    # Under the LITERAL form the failure is worse still -- the truncation bound underflows in
    # exactly the regime delta does, so the relative test degenerates to `0.0 > 0.0` = False and
    # the guard is inert on the very failure it exists to catch (RESEARCH F1's table: z = 39.850
    # and z = 99.900 both slip through).
    if delta <= 0.0:
        raise ValueError(
            f"delta_quadrature({eps!r}, {mu!r}) computed delta = {delta!r}, which is provably "
            f"wrong: delta is STRICTLY positive for every finite eps and every mu > 0, because the "
            f"Gaussian has full support and the integrand is positive on a set of positive "
            f"measure. This condition is NOT implied by the truncation check above -- that one is "
            f"RELATIVE, and a relative test degenerates to `0.0 > 0.0` = False in exactly the "
            f"corner it exists to catch (here z = {z!r}, phi(z) still representable)."
        )
    return delta


def _refuse_bad_steps_or_delta(where, steps, delta):
    """The (steps, delta) domain, refused once for both public directions.

    ``epsilon_for`` and ``sigma_for`` take the same two arguments and must refuse them the same
    way, so the refusals live in one place and each message names its caller. ``where`` is the
    caller's rendered call, so the four refusals below stay distinguishable per direction rather
    than reading as one anonymous validator.
    """
    if isinstance(steps, bool) or not isinstance(steps, int):
        raise ValueError(
            f"{where}: steps must be an int -- it is a COUNT of composed mechanism invocations, "
            f"not a measurement. Got {steps!r} ({type(steps).__name__}). bool is rejected "
            f"explicitly because it is an int subclass, so True would silently mean one step."
        )
    if steps < 1:
        raise ValueError(
            f"{where}: steps must be >= 1. Got {steps!r}. Zero steps is not a mechanism that "
            f"released anything, and Dong-Roth-Su Corollary 3.3 composes T >= 1 invocations; "
            f"sqrt(0)/sigma = 0.0 would otherwise reach delta_closed as mu = 0.0."
        )
    if not math.isfinite(delta):
        raise ValueError(
            f"{where}: delta must be finite. Got {delta!r}. A non-finite target makes every "
            f"bisection comparison against it silently False, and the search would return its "
            f"bracket rather than a solution."
        )
    if delta <= 0.0 or delta >= 1.0:
        raise ValueError(
            f"{where}: delta must lie strictly inside (0.0, 1.0). Got {delta!r}. delta = 0.0 is "
            f"pure eps-DP, which the Gaussian mechanism cannot deliver at any finite eps (its "
            f"privacy loss is unbounded), and delta >= 1.0 is satisfied by releasing the raw data."
        )
    if delta < _MIN_TARGET_DELTA:
        raise ValueError(
            f"{where}: delta = {delta!r} is below this accountant's smallest solvable target "
            f"{_MIN_TARGET_DELTA!r}. This is a DOMAIN LIMIT of the search, stated rather than "
            f"papered over: the bracketing walk reads a delta_closed refusal as 'delta here is "
            f"below float64's range, therefore below the target', and measured, delta_closed "
            f"returns exactly 5e-324 at the last eps before it refuses. A target within a "
            f"subnormal of that floor would make the comparison ambiguous instead of decisive."
        )


def _delta_or_below_float64(eps, mu):
    """``delta_closed(eps, mu)``, or ``None`` when delta has left float64's range entirely.

    ``None`` IS NOT A NUMBER AND NEVER REACHES A CALLER. It is the ORDERING FACT the refusal
    itself carries, which is a strictly different thing from substituting a value for one:
    ``delta_closed`` refuses precisely because delta is smaller than float64 can hold, and the
    only use made of that here is "smaller than the target", which is the one conclusion the
    refusal's own condition licenses. Turning it into a returned ``0.0`` -- the failure RESEARCH
    F1 exists to prevent -- would instead let it be COMPARED against another oracle's ``0.0``.

    MEASURED, not assumed: at every mu from 1e-8 to 1e8, ``delta_closed`` returns exactly
    ``5e-324`` (float64's smallest positive value) at the last eps before it refuses. Since
    ``_refuse_bad_steps_or_delta`` floors the target at 1e-300, a refusal is 24 decades below the
    target rather than a subnormal away from it.

    WHY THE CAUGHT ``ValueError`` CANNOT BE A DIFFERENT REFUSAL. ``delta_closed`` ships exactly
    four ``raise`` statements, and the first two (a non-finite input; ``mu <= 0.0``) are
    UNREACHABLE from here: ``eps`` is re-checked finite below, and ``mu`` is a finite
    strictly-positive number the caller computed before entering the loop. Only the
    representability and exact-zero refusals -- the two that mean "below float64's range" -- can
    fire. ``tests/test_phase22_accountant.py::test_delta_closed_still_ships_exactly_four_raises``
    reddens if a fifth is ever added, because that argument would then need re-reading rather than
    silently widening.

    Letting the refusal propagate instead is NOT AN OPTION, and this is measured too: the
    doubling walk overshoots into the underflow corner on a normal input (mu = 141.4, reached at
    sigma = 0.5 / T = 5000 in V-03's own sweep), so propagation would abort a legitimate solve
    that has already bracketed its answer.
    """
    if not math.isfinite(eps):
        raise ValueError(
            f"_delta_or_below_float64({eps!r}, {mu!r}): eps must be finite here. A non-finite eps "
            f"would reach delta_closed's FIRST refusal, whose meaning is 'this input is garbage' "
            f"and NOT 'delta is below float64's range' -- reading one as the other is exactly the "
            f"conflation this helper's contract forbids."
        )
    try:
        return delta_closed(eps, mu)
    except ValueError:
        return None


def epsilon_for(sigma, steps, delta):
    """The smallest eps for which the T-fold composed Gaussian mechanism is (eps, delta)-DP.

    THE SIGNATURE IS ``(sigma, steps, delta)`` -- THREE PARAMETERS, AND THERE IS DELIBERATELY NO
    ``clip_norm=``. ``sigma`` is the noise multiplier ``sigma_noise / clip_norm`` (unitless), so
    ``mu_eff = sqrt(steps) / sigma`` and the clip constant cancels out of the accounting entirely.
    A ``clip_norm=`` parameter would create a FIFTH mechanism key beside
    ``scripts/mitigation_gate.py::MECHANISM_KEYS`` -- ``("sigma", "steps", "delta", "q")``, a
    FROZEN artifact whose own comment says there is no fifth key. Consistency with
    ``MECHANISM_KEYS`` is not a preference here (RESEARCH F4).

    Solved by BISECTION on the strictly-decreasing map ``eps -> delta_closed(eps, mu_eff)``, over
    the same closed form ``delta_closed`` implements. ``sigma_for`` then bisects over THIS
    function rather than over a second transcription of the form, so the two directions cannot
    disagree by construction (D-12's one choke point).

    THE FIVE PRECONDITIONS ARE ``scripts/mitigation_accountant.py::REQUIRED_FORM_CONDITIONS``,
    which is the frozen statement of them; two are repeated here because no other artifact in
    ``src/`` states them and both fail SILENTLY:

      2. HOMOGENEOUS ``sigma`` AND ``Delta`` ACROSS ALL T STEPS. The general composition is
         ``sqrt(sum of mu_i squared)``; it collapses to ``mu * sqrt(T)`` only if every step is
         identical. A mid-run sigma change invalidates ``mu * sqrt(T)`` with nothing raising --
         the published number is simply wrong.
      3. T FIXED IN ADVANCE, NOT A DATA-DEPENDENT STOPPING TIME. Early-stopping on a validation
         metric makes T itself a function of the private data, and the composition theorem no
         longer applies to it.

    And the non-obvious half, recorded because a reader is likely to assume it runs the other way:
    ADAPTIVITY IS PERMITTED AT NO COST. Dong-Roth-Su Corollary 3.3 covers mechanisms whose inputs
    depend on earlier outputs, so DP-SGD's step-to-step dependence buys no penalty. An unnecessary
    penalty applied out of caution is still a wrong published number. (Conditions 1 and 5 -- q = 1,
    and Delta being the per-step sensitivity under a fixed adjacency -- are pinned by
    ``scripts/mitigation_unit.py::SAMPLING_RATE_Q`` and by this module's adjacency paragraph.)

    Args:
        sigma: the NOISE MULTIPLIER, ``>= 0.0``. ``0.0`` is the deterministic mechanism and is
            handled explicitly below.
        steps: T, the number of composed invocations. An ``int`` ``>= 1``.
        delta: the target delta, strictly inside ``(0.0, 1.0)`` and at least
            ``_MIN_TARGET_DELTA``.

    Returns:
        The eps solving ``delta_closed(eps, sqrt(steps)/sigma) == delta`` to a relative bracket
        width of 1e-15, or ``math.inf`` at ``sigma == 0.0``, or ``0.0`` when the mechanism already
        meets the target at eps = 0. Cross-checked against
        ``scripts/mitigation_accountant.py::GOLDEN_EPSILON`` at that pin's own
        ``GOLDEN_EPSILON_REL_TOL`` (1e-12) by
        ``tests/test_phase22_accountant.py::test_epsilon_for_matches_golden``; measured worst
        relative deviation over its seven rows is **1.07e-14**, at sigma = 2.0 / T = 200 -- which
        is the gap between the two ORACLES, not this function's error, since the pin's epsilons
        are bisected against the exp-quadrature oracle and this bisects against the erfc closed
        form.

    Raises:
        ValueError: on a negative or non-finite sigma, a non-integer or non-positive steps, a
            delta outside ``(0.0, 1.0)`` or below the solvable floor, or a bracket that failed to
            close within its documented iteration cap.
    """
    where = f"epsilon_for({sigma!r}, {steps!r}, {delta!r})"
    if not math.isfinite(sigma):
        raise ValueError(
            f"{where}: sigma must be finite. Got {sigma!r}. sigma = inf is the infinitely noisy "
            f"mechanism (eps = 0), which is a limit rather than a configuration, and nan would "
            f"make every bisection comparison False and return a bracket endpoint."
        )
    if sigma < 0.0:
        raise ValueError(
            f"{where}: sigma must be >= 0.0. Got {sigma!r}. A negative noise multiplier is not a "
            f"mechanism; it would give mu < 0.0, which delta_closed refuses one call later with a "
            f"message about mu rather than about the sigma that produced it."
        )
    _refuse_bad_steps_or_delta(where, steps, delta)

    # --- sigma = 0: THE EXPLICIT BRANCH, and it sits immediately before the ONLY division in this
    # function so that `sqrt(steps) / sigma` is never reached. `1.0/0.0` raises ZeroDivisionError
    # in CPython (it does NOT return inf), so the branch is operationally required -- but inf is
    # also the MATHEMATICALLY CORRECT return value, not a guard papering over an exception:
    #
    #   sigma -> 0  =>  mu -> inf, and in the closed form
    #     Phi(mu/2 - eps/mu)          -> Phi(+inf) = 1
    #     exp(eps) * Phi(-mu/2 - eps/mu) -> exp(eps) * Phi(-inf) = 0
    #   =>  delta(eps, mu) -> 1 for EVERY finite eps.
    #
    # Measured at 60 dps: delta = 0.999999059179780138 at mu = 10, and exactly 1.0 at mu >= 100
    # for eps in {1, 10, 100}. Since delta = 1 at every finite eps, NO finite eps satisfies
    # delta <= a target below 1, so the infimum over admissible eps is +inf. That agrees with the
    # mechanism-level statement: sigma = 0 releases a deterministic function of the data, which is
    # (inf, delta)-DP for any delta < 1 and nothing better.
    if sigma == 0.0:
        return math.inf

    mu = math.sqrt(steps) / sigma

    # eps = 0 is the left end of the domain (a negative eps is not a privacy loss). If the
    # mechanism already meets the target there, 0.0 IS the infimum and there is nothing to bisect.
    at_zero = _delta_or_below_float64(0.0, mu)
    if at_zero is None or at_zero <= delta:
        return 0.0

    # --- Bracket by DOUBLING the upper bound. Safe past eps = 709.78 because delta_closed
    # computes its second term as exp(eps + log(erfc(b))) rather than exp(eps) * erfc(b): the
    # naive product raises OverflowError there, and the walk REACHES that domain on this project's
    # own frontier (RESEARCH F2 -- sigma = 0.40 / T = 200 solves to eps = 775.79, sigma = 0.30 /
    # T = 200 to eps = 1312.16). The cap is an iteration count rather than a magnitude, so `hi`
    # stays finite and delta_closed's non-finite refusal stays unreachable from here.
    lo, hi = 0.0, 1.0
    for _ in range(_MAX_DOUBLINGS):
        above = _delta_or_below_float64(hi, mu)
        if above is None or above <= delta:
            break
        lo = hi
        hi *= 2.0
    else:
        raise ValueError(
            f"{where}: the upper bracket failed to close in {_MAX_DOUBLINGS} doublings, reaching "
            f"eps = {hi!r} at mu = {mu!r} with delta still above the target. Refusing rather than "
            f"looping: a walk that has not bracketed its root has no answer to return."
        )

    for _ in range(_MAX_BISECTIONS):
        mid = 0.5 * (lo + hi)
        # Stop on the relative width OR on a midpoint that no longer separates the bracket -- at
        # adjacent floats `0.5 * (lo + hi)` returns one of the endpoints and the loop would
        # otherwise spin out its remaining iterations for no refinement.
        if mid <= lo or mid >= hi or hi - lo <= _BISECT_REL_WIDTH * hi:
            break
        middle = _delta_or_below_float64(mid, mu)
        if middle is None or middle <= delta:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def sigma_for(target_epsilon, steps, delta):
    """The smallest noise multiplier reaching ``target_epsilon`` at ``steps`` and ``delta``.

    IT BISECTS OVER ``epsilon_for``, NOT OVER A RE-DERIVED CLOSED FORM. That is D-12's ONE choke
    point, and the reason is not tidiness: the inverse is the forward function inverted, so a
    divergence between the two directions is impossible BY CONSTRUCTION rather than by discipline.
    ``tests/test_phase22_accountant.py::test_sigma_for_uses_the_forward_function`` asserts that
    structurally, by AST -- a second bisection inlined here would redden it -- and
    ``::test_round_trip`` catches a divergence numerically.

    D-12's SECOND PREMISE CORRECTION, recorded because the corrected reason is the load-bearing
    one: *"forward-only would force Phase 23 to improvise bisection outside the frozen module"* is
    FALSE AS STATED, because under D-09 the frozen module (``scripts/mitigation_accountant.py``)
    holds no executable formula at all -- everything executable is already outside it. The real
    risk is improvisation outside the ACCOUNTANT'S SINGLE CHOKE POINT: a bisection written inline
    in ``scripts/mitigation_budget.py`` or in a Phase 23 driver would be untested against
    ``GOLDEN_EPSILON`` and free to disagree with the forward direction while both look right.

    ``epsilon_for`` is strictly DECREASING in sigma, so the bracket is walked in both directions:
    ``hi`` doubles while its epsilon is still above the target, then ``lo`` halves while its
    epsilon is still below it.

    Args:
        target_epsilon: the epsilon to hit. Strictly positive; ``math.inf`` is the sigma = 0 point
            and is answered exactly rather than bisected.
        steps: T, the number of composed invocations. An ``int`` ``>= 1``.
        delta: the target delta, strictly inside ``(0.0, 1.0)``.

    Returns:
        The sigma whose ``epsilon_for`` meets ``target_epsilon``, bisected to a relative width of
        1e-15, or exactly ``0.0`` at ``target_epsilon = math.inf``. Round-tripped against
        ``epsilon_for`` at ``ROUND_TRIP_REL_TOL``; measured worst deviation over 48 (sigma, T)
        pairs is 8.29e-15.

    Raises:
        ValueError: on a non-positive or non-finite (other than ``+inf``) target_epsilon, a bad
            steps or delta, or a bracket that failed to close within its documented cap.
    """
    where = f"sigma_for({target_epsilon!r}, {steps!r}, {delta!r})"
    _refuse_bad_steps_or_delta(where, steps, delta)
    if target_epsilon == math.inf:
        # The exact boundary, closing the round trip at the sigma = 0 point rather than bisecting
        # toward it: no finite sigma gives an infinite epsilon, so this is the answer and not an
        # approximation of one. Both ends of `sigma_for(epsilon_for(0.0, T, d), T, d)` are
        # therefore exact, which is why that round trip is asserted with `==`.
        return 0.0
    if not math.isfinite(target_epsilon):
        raise ValueError(
            f"{where}: target_epsilon must be finite or +inf. Got {target_epsilon!r}. -inf and "
            f"nan are not privacy losses; +inf is the sigma = 0 point and is handled above."
        )
    if target_epsilon <= 0.0:
        raise ValueError(
            f"{where}: target_epsilon must be strictly positive. Got {target_epsilon!r}. "
            f"epsilon = 0.0 is perfect privacy, which the Gaussian mechanism reaches only in the "
            f"sigma -> inf limit, so no finite sigma solves it and there is nothing to bracket."
        )

    hi = 1.0
    for _ in range(_MAX_DOUBLINGS):
        if epsilon_for(hi, steps, delta) <= target_epsilon:
            break
        hi *= 2.0
    else:
        raise ValueError(
            f"{where}: the NOISY end of the bracket failed to close in {_MAX_DOUBLINGS} "
            f"doublings, reaching sigma = {hi!r} with epsilon still above the target. Refusing "
            f"rather than looping: a walk that has not bracketed its root has no answer."
        )

    lo = hi
    for _ in range(_MAX_DOUBLINGS):
        lo *= 0.5
        if epsilon_for(lo, steps, delta) >= target_epsilon:
            break
    else:
        raise ValueError(
            f"{where}: the QUIET end of the bracket failed to close in {_MAX_DOUBLINGS} halvings, "
            f"reaching sigma = {lo!r} with epsilon still below the target against an upper bound "
            f"of {hi!r}. Refusing rather than looping."
        )

    for _ in range(_MAX_BISECTIONS):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi or hi - lo <= _BISECT_REL_WIDTH * hi:
            break
        if epsilon_for(mid, steps, delta) <= target_epsilon:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)
