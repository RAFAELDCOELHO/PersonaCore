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

This module imports ``math`` and nothing else (D-10), so ``pyproject.toml`` stays untouched and
RPT-03's zero-new-dependency streak holds. ``tests/test_phase22_accountant.py``'s V-09 asserts
that as a hard equality, statically and out-of-process.
"""

import math

_SQRT2 = math.sqrt(2.0)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)

# math.exp raises "OverflowError: math range error" strictly above this argument (bisected). It
# bounds the quadrature oracle's conditioning in the NEGATIVE-z direction, and it is the same
# constant RESEARCH F2 measured for the closed form's rejected `exp(eps) * erfc(b)` product.
_EXP_OVERFLOW_ARG = 709.782712893384


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

    eb = math.erfc(b)
    # exp(eps + log(erfc(b))), NEVER exp(eps) * erfc(b). The naive product raises
    # "OverflowError: math range error" for eps > 709.782712893384 (bisected), and that eps is
    # REACHABLE on this project's own frontier, not a pathological input: solving epsilon_for at
    # sigma=0.40, T=200 against the frozen delta gives eps = 775.79, and sigma_for walks there
    # while bisecting sigma downward. Log space keeps the identical product below the line.
    second = 0.0 if eb == 0.0 else 0.5 * math.exp(eps + math.log(eb))

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
