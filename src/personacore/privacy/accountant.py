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
