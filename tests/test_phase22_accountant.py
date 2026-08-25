"""Phase 22 -- the (eps, delta) accountant against the committed 60-dps ground truth (V-01 .. V-09).

Every truth here is a decimal STRING read from ``tests/fixtures/phase22_reference.py``, never a
recomputation: ``mpmath`` produced them once, in the research session, and must never become a test
dependency (RPT-03 -- ``pyproject.toml`` is untouched by this phase).

Two disciplines run through the whole file and neither is decoration:

1. **Every comparison is RELATIVE.** True delta spans 9.99e-1 down to 1.05e-57 on this frontier, so
   ``abs(a - b) < 1e-12`` passes trivially for every row below 1e-12 -- including a
   catastrophically wrong ``0.0``.
2. **A zero is refused before it is compared.** RESEARCH F1 measured that BOTH oracles underflow to
   exactly ``0.0`` past z ~ 38.4, so an agreement test that compares first passes on two wrong
   answers against a true ``1.24028351258e-352``.

CPU-only, GPU-free, no torch, no network.
"""

import ast
import math
import pathlib
import subprocess
import sys

import pytest
from tests.fixtures.phase22_reference import DELTA_FRONTIER, VACUOUS_AGREEMENT_ROW

from personacore.privacy.accountant import (
    ROUND_TRIP_REL_TOL,
    delta_closed,
    delta_quadrature,
    epsilon_for,
    sigma_for,
)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_ACCOUNTANT_PATH = _ROOT / "src" / "personacore" / "privacy" / "accountant.py"

# The pin is read, never imported by `src/`: `scripts/` is not a package and the pre-registration
# import ceiling runs the other way (D-10). A TEST is the sanctioned reader — 22-02's own words,
# "the pin is what a test reads to prove the two agree". Idempotence guard per
# tests/test_phase20_prereg.py's shape.
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_accountant  # noqa: E402  (needs the sys.path insert above)
import mitigation_unit  # noqa: E402  (same reason)

# The implementation's own measured bound against 60-dps ground truth, before the reference
# string's quantization is added on top. RESEARCH reports 7.9e-13; measured here the worst
# deviation on a row whose committed truth carries a full 13 significant digits is 9.03e-13
# (eps=8.0, mu=0.5). 1e-12 is that, rounded up to the next decade.
_CLOSED_FORM_REL_BOUND = 1e-12


def _sig_digits(truth_str):
    """Significant digits actually carried by a committed decimal-string truth.

    ``DELTA_FRONTIER``'s truths are NOT all the same width: nine carry 13 significant digits, one
    carries 12, and ``3.7194507268e-91`` carries 11. A flat tolerance therefore charges the
    implementation for the reference table's own rounding, and at 11 digits that rounding is
    ~5e-11 -- fifty times the implementation bound. Reading the width off the string keeps each
    row's tolerance carrying its own denominator.
    """
    mantissa = truth_str.split("e")[0].replace(".", "").replace("-", "")
    return len(mantissa.lstrip("0"))


def _frontier_rel_tol(truth_str):
    """Implementation bound + the committed string's own half-ulp, per row."""
    return _CLOSED_FORM_REL_BOUND + 0.5 * 10.0 ** (1 - _sig_digits(truth_str))


def _representable_rows():
    """The ``DELTA_FRONTIER`` rows whose true delta survives float64.

    Located by ``float(truth) > 0.0`` rather than by index, so the set cannot rot if the table is
    reordered, and cross-checked against ``VACUOUS_AGREEMENT_ROW`` by the meta-guard in
    ``test_closed_form_frontier``.
    """
    return [(eps, mu, truth) for eps, mu, truth in DELTA_FRONTIER if float(truth) > 0.0]


@pytest.mark.parametrize(("eps", "mu", "truth_str"), _representable_rows())
def test_closed_form_frontier(eps, mu, truth_str):
    """V-01 -- ``delta_closed`` reproduces Balle-Wang Theorem 8 on the whole representable frontier.

    RELATIVE, never absolute (see the module docstring). The per-row tolerance is the
    implementation's measured 1e-12 bound PLUS the committed truth string's own half-ulp, because
    charging the implementation for the reference table's quantization would make the eps=2.0,
    mu=0.1 row (11 digits) red on a correct answer.
    """
    truth = float(truth_str)
    tol = _frontier_rel_tol(truth_str)
    # Meta-guard: the digit-width rule must never widen the tolerance into vacuity.
    assert 1e-12 < tol <= 1e-10, (
        f"per-row tolerance {tol!r} for truth {truth_str!r} is outside the sane band -- "
        f"_sig_digits returned {_sig_digits(truth_str)}, so the rule is broken, not the accountant"
    )
    got = delta_closed(eps, mu)
    assert got != 0.0, (
        f"delta_closed({eps}, {mu}) returned exactly 0.0 on a representable row (true delta "
        f"{truth_str}). RESEARCH F1: a returned 0.0 is provably wrong and must be a refusal."
    )
    assert abs(got - truth) <= tol * truth, (
        f"delta_closed({eps}, {mu}) = {got!r}, 60-dps truth {truth_str} -- relative deviation "
        f"{abs(got - truth) / truth:.3e} exceeds {tol:.3e}"
    )


def test_closed_form_frontier_parametrization_is_not_empty():
    """Meta-guard: V-01 sweeps eleven rows, and it is really sweeping them.

    A parametrization that silently emptied -- a renamed fixture constant, a truncated table, a
    locator that stopped matching -- makes V-01 green having compared nothing at all. Hard equality
    against ``VACUOUS_AGREEMENT_ROW`` additionally pins WHICH row is excluded: "one row is not
    representable" is satisfied by a table where a DIFFERENT row silently went to zero.
    """
    rows = _representable_rows()
    assert len(rows) == 11, (
        f"V-01 is parametrized over {len(rows)} rows, not the 11 representable frontier rows"
    )
    kept = {r[:2] for r in rows}
    excluded = [(eps, mu) for eps, mu, _ in DELTA_FRONTIER if (eps, mu) not in kept]
    assert excluded == [VACUOUS_AGREEMENT_ROW], (
        f"the rows float64 cannot hold are {excluded}, not exactly [{VACUOUS_AGREEMENT_ROW}] -- "
        f"the two-oracle cross-check has gone vacuous somewhere new"
    )


@pytest.mark.parametrize(
    ("eps", "mu"),
    [
        (2.0, 0.05),  # DELTA_FRONTIER's twelfth row; z = 39.975, true delta 1.24028351258e-352
        (1.0, 0.02),  # RESEARCH F1 table; z = 49.990, true delta 7.12037376927e-549
        (5.0, 0.05),  # RESEARCH F1 table; z = 99.975, true delta 8.18353277275e-2177
    ],
)
def test_closed_form_refuses_when_not_representable(eps, mu):
    """V-05 (closed half) -- past z ~ 38.47 the closed form refuses rather than returning ``0.0``.

    RESEARCH F1: ``math.erfc`` underflows to exactly ``0.0``, so WITHOUT this refusal the closed
    form returns ``0.0``, the quadrature oracle returns ``0.0``, and the two-oracle cross-check
    that DPSGD-03 rests on passes on two wrong answers against a true ``1.24028351258e-352``.
    """
    with pytest.raises(ValueError, match="DOMAIN LIMIT"):
        delta_closed(eps, mu)


def test_closed_form_survives_high_epsilon():
    """RESEARCH F2 -- eps = 775.79 is reachable, and the log-space second term survives it.

    ``epsilon_for(sigma=0.40, T=200)`` at the frozen delta solves to eps = 775.7867 with
    mu_eff = sqrt(200)/0.40 = 35.355, and ``sigma_for`` walks through exactly that point while
    bisecting sigma downward. The naive ``exp(eps) * erfc(b)`` form raises
    ``OverflowError: math range error`` there (bisected boundary 709.782712893384), aborting a
    legitimate inverse solve -- a loud failure, but still a failure.
    """
    with pytest.raises(OverflowError):
        math.exp(775.7867)  # the naive form's first operation, watched failing

    got = delta_closed(775.7867, 35.355)
    assert math.isfinite(got) and got > 0.0, f"delta_closed at eps=775.79 returned {got!r}"


@pytest.mark.parametrize("mu", [0.0, -1.0, float("nan"), float("inf")])
def test_closed_form_domain_refusals_on_mu(mu):
    """Degenerate mu is a ``ValueError``, never a ``ZeroDivisionError``.

    ``mu = 0.0`` is ``sigma = inf`` and belongs to the inverse solver's boundary, so ``eps / mu``
    must never be reached: an uncaught ``ZeroDivisionError`` is an accident wearing a refusal's
    clothes, and a caller cannot tell it apart from a bug.
    """
    with pytest.raises(ValueError):
        delta_closed(1.0, mu)


@pytest.mark.parametrize("eps", [float("nan"), float("inf"), float("-inf")])
def test_closed_form_domain_refusals_on_eps(eps):
    """A non-finite eps refuses rather than returning a nan delta every comparison then passes."""
    with pytest.raises(ValueError):
        delta_closed(eps, 1.0)


@pytest.mark.parametrize(("eps", "mu", "truth_str"), _representable_rows())
def test_two_oracles_agree(eps, mu, truth_str):
    """V-02 -- the two oracles agree relatively, AFTER each is proven non-zero.

    The ordering is the whole test. RESEARCH F1 measured that past z ~ 38.47 ``math.erfc``
    underflows and the closed form returns ``0.0``, while the quadrature's ``phi(z)`` prefactor
    underflows and it returns ``0.0`` too -- so ``abs(a - b) <= 1e-9 * abs(b)`` reads ``0.0 == 0.0``
    and PASSES, against a true delta of ``1.24028351258e-352``. Two independent implementations buy
    nothing when both fail on the same underlying quantity, so the zero must be refused before the
    comparison is even reached, each with its own message.

    Measured worst gap between the two oracles over these eleven rows: **2.84e-12 relative**, at
    eps=2.0, mu=0.1 -- roughly 350x inside the 1e-9 budget.
    """
    a = delta_quadrature(eps, mu)
    b = delta_closed(eps, mu)
    assert a != 0.0, (
        f"delta_quadrature({eps}, {mu}) returned exactly 0.0 (true delta {truth_str}) — "
        f"RESEARCH F1's vacuous half. A zero is a refusal, never an oracle value."
    )
    assert b != 0.0, (
        f"delta_closed({eps}, {mu}) returned exactly 0.0 (true delta {truth_str}) — "
        f"RESEARCH F1's vacuous half. A zero is a refusal, never an oracle value."
    )
    assert abs(a - b) <= 1e-9 * abs(b), (
        f"the two oracles disagree at eps={eps}, mu={mu}: quadrature {a!r} against closed form "
        f"{b!r}, relative {abs(a - b) / abs(b):.3e} over the 1e-9 budget"
    )


def test_low_privacy_corner():
    """V-04 -- the DERIVED range is what fixes eps=8, mu=0.5, and the fixed range is measured wrong.

    Two halves, and the second is the load-bearing one. Without the negative control this test
    proves the oracle is right but not that the derived range is WHAT MADE IT right, so a future
    edit replacing the width rule with a constant could keep it green.

    At eps=8, mu=0.5 the integrand's support starts at ``t > eps/mu + mu/2 = 16.25``, entirely
    outside a fixed ``[-14, 14]``. The literal form over that range therefore integrates zero
    everywhere and returns exactly ``0.0`` -- a perfectly plausible delta, wrong by 57 orders of
    magnitude. The derived rule puts the grid on ``[t_min, t_min + U]`` with ``U = 2.41`` and lands
    within 3.6e-13.
    """
    truth = float("1.048659178913e-57")
    got = delta_quadrature(8.0, 0.5)
    assert abs(got - truth) <= 1e-11 * truth, (
        f"derived-range oracle at eps=8, mu=0.5: {got!r} against {truth!r}, relative "
        f"{abs(got - truth) / truth:.3e}"
    )

    def _fixed_range_trapezoid(eps, mu, lo=-14.0, hi=14.0, n=4001):
        """D-13's original probe: the LITERAL integrand on a fixed range. Test-local on purpose."""
        h = (hi - lo) / (n - 1)
        inv = 1.0 / math.sqrt(2.0 * math.pi)
        total = 0.0
        for i in range(n):
            t = lo + i * h
            loss = mu * t - 0.5 * mu * mu
            value = inv * math.exp(-0.5 * (t - mu) ** 2) * max(0.0, 1.0 - math.exp(eps - loss))
            total += value * (0.5 if i in (0, n - 1) else 1.0)
        return total * h

    fixed = _fixed_range_trapezoid(8.0, 0.5)
    assert abs(fixed - truth) / truth >= 0.99, (
        f"the fixed [-14, 14] negative control returned {fixed!r} at relative error "
        f"{abs(fixed - truth) / truth:.3e} — it was supposed to be catastrophically wrong "
        f"(measured 1.00e+00). If this is now accurate the control has stopped controlling."
    )


def test_oracle_refuses():
    """V-05 -- all three non-vacuity conditions fire, SEPARATELY, with three distinct messages.

    Three conditions sharing one message are one condition wearing three hats, so the messages are
    asserted pairwise distinct rather than merely present.

      1. ``phi(z)`` underflow at eps=12.0, mu=0.3 (z = 39.85, exp argument -794.0).
      2. Relative truncation at a deliberately narrowed ``lam=1.0``, where the rigorous Mills bound
         on the discarded tail is 2.45e-01 against a captured integral of 2.19e-01.
      3. Exact zero at eps=1.92625, mu=0.05 (z = 38.5) -- and this input is the measurement that
         condition 3 is NOT implied by condition 2. In the band 38.372164249 < z < 38.6005 the
         prefactor is still representable (condition 1 silent) and ``trunc/integral`` is ~3.2e-15
         (condition 2 silent), yet the product underflows to exactly ``0.0``.
    """
    messages = []
    for label, args, kwargs in [
        ("condition 1 (phi(z) underflow)", (12.0, 0.3), {}),
        ("condition 2 (relative truncation)", (1.0, 1.0), {"lam": 1.0}),
        ("condition 3 (exact zero)", (1.92625, 0.05), {}),
    ]:
        with pytest.raises(ValueError) as excinfo:
            delta_quadrature(*args, **kwargs)
        messages.append((label, str(excinfo.value)))

    texts = [text for _, text in messages]
    assert len(set(texts)) == 3, (
        "the three non-vacuity conditions do not carry three distinct messages — they are one "
        "condition wearing three hats:\n"
        + "\n".join(f"  {label}: {text[:120]}" for label, text in messages)
    )


@pytest.mark.parametrize("n", [20000, 4, 2, 1, 0])
def test_quadrature_rejects_bad_grid(n):
    """An even node count or fewer than three nodes is a ``ValueError``, never a silent bad rule.

    Composite Simpson needs an odd node count (an even panel count). An even ``n`` applies the
    4/2 weights across a half panel and degrades the rule to something with no stated order, which
    would then be compared against a tolerance calibrated for Simpson's.
    """
    with pytest.raises(ValueError, match="Simpson"):
        delta_quadrature(1.0, 1.0, n=n)


@pytest.mark.parametrize("steps", [1, 64, 200, 1000])
def test_sigma_zero(steps):
    """V-08 -- ``sigma = 0`` is ``eps = inf``, and it is a RETURN rather than an exception.

    ``mu = sqrt(T)/sigma`` is ``1.0/0.0``, which raises ``ZeroDivisionError`` in CPython rather
    than returning ``inf``, so without the explicit branch Phase 23's first executed run (the
    sigma = 0 DP arm, DPSGD-06) would crash at REPORT time rather than in the mechanism.

    ``inf`` is also the mathematically correct value, not a guard: as ``mu -> inf`` the closed
    form's first term goes to 1 and its second to 0, so ``delta -> 1`` for EVERY finite eps
    (measured at 60 dps: 0.999999059179780138 at mu = 10, exactly 1.0 at mu >= 100). No finite eps
    satisfies a target below 1, so the infimum over admissible eps IS ``+inf``.
    """
    try:
        got = epsilon_for(0.0, steps, mitigation_unit.DELTA)
    except ZeroDivisionError as exc:  # pragma: no cover - the failure this test exists to catch
        pytest.fail(
            f"epsilon_for(0.0, {steps}, delta) raised ZeroDivisionError ({exc}) — the explicit "
            f"sigma = 0 branch is gone and 1.0/0.0 is being reached. inf is the correct RETURN."
        )
    assert math.isinf(got) and got > 0.0, (
        f"epsilon_for(0.0, {steps}, delta) returned {got!r}, not +inf. sigma = 0 releases a "
        f"deterministic function of the data: it is (inf, delta)-DP and nothing better."
    )


def test_epsilon_for_matches_golden():
    """``epsilon_for`` reproduces the FROZEN pin's seven pre-registered epsilons.

    The pin's epsilons are bisected against the exp-quadrature ORACLE, never snapshotted from this
    module (D-13), so the two routes are different mathematics and differ at ~1e-14 by
    construction. That is why the comparison is ``GOLDEN_EPSILON_REL_TOL`` and not ``==``: an
    exact float pin would redden on correct code.

    delta is READ from ``mitigation_unit.DELTA`` and never re-spelled here — the pin's own
    ``GOLDEN_EPSILON_DELTA_SOURCE`` says a consuming test must resolve it from that module, which
    is the only shape that keeps ONE delta in the repository.
    """
    rows = mitigation_accountant.GOLDEN_EPSILON
    # Meta-guard: a truncated pin would make this sweep green having compared nothing.
    assert len(rows) == 7, (
        f"the pin carries {len(rows)} GOLDEN_EPSILON rows, not 7 — a truncated table makes this "
        f"test green over less than it claims"
    )
    tol = mitigation_accountant.GOLDEN_EPSILON_REL_TOL
    worst = 0.0
    for sigma, steps, pinned in rows:
        got = epsilon_for(sigma, steps, mitigation_unit.DELTA)
        rel = abs(got - pinned) / abs(pinned)
        worst = max(worst, rel)
        assert rel <= tol, (
            f"epsilon_for({sigma!r}, {steps!r}, delta) = {got!r} against the pinned {pinned!r} — "
            f"relative {rel:.3e} over the pin's own budget {tol:.3e}"
        )
    # Non-vacuity in the other direction: a bisection that collapsed to returning the pinned value
    # would show a perfect zero. The two routes are different mathematics and MUST differ a little.
    assert worst > 0.0, (
        "every epsilon_for row matched its pinned value BITWISE. The pin comes from the "
        "exp-quadrature oracle and this function bisects the erfc closed form; a bitwise match on "
        "all seven rows means the table is a photograph of the code, not a constraint on it."
    )


@pytest.mark.parametrize("sigma", [0.40, 0.30])
def test_epsilon_for_survives_the_overflow_regime(sigma):
    """RESEARCH F2 -- the search WALKS INTO eps > 709.78, and must come back with a number.

    Phase 23 would never PUBLISH eps = 776. But ``sigma_for`` bisects sigma downward and
    ``epsilon_for`` doubles its bracket upward, so both enter this domain during an ordinary
    search: at the frozen delta, sigma = 0.40 / T = 200 solves to eps = 775.79 and sigma = 0.30 /
    T = 200 to eps = 1312.16. The naive ``exp(eps) * erfc(b)`` second term raises
    ``OverflowError`` there and would abort a legitimate solve; the log-space form does not.
    """
    got = epsilon_for(sigma, 200, mitigation_unit.DELTA)
    assert math.isfinite(got), f"epsilon_for({sigma}, 200, delta) returned {got!r}"
    assert got > 700.0, (
        f"epsilon_for({sigma}, 200, delta) = {got!r}, which is BELOW the overflow regime this "
        f"test exists to walk through — RESEARCH F2 measures 775.79 and 1312.16 for these two"
    )


@pytest.mark.parametrize(
    ("sigma", "steps", "delta"),
    [
        (1.0, 0, mitigation_unit.DELTA),  # steps below one
        (1.0, 200, 0.0),  # delta at the closed lower end
        (1.0, 200, 1.0),  # delta at the closed upper end
        (-1.0, 200, mitigation_unit.DELTA),  # a negative noise multiplier
        (float("nan"), 200, mitigation_unit.DELTA),  # a non-finite sigma
        (float("inf"), 200, mitigation_unit.DELTA),  # sigma = inf is a limit, not a configuration
        (1.0, 200.0, mitigation_unit.DELTA),  # steps as a float — a count, not a measurement
        (1.0, 200, float("nan")),  # a non-finite delta
        (1.0, 200, 1e-320),  # below the solvable floor
    ],
)
def test_epsilon_for_domain_refusals(sigma, steps, delta):
    """Every degenerate input is a ``ValueError``, never a ``ZeroDivisionError`` and never a number.

    ``steps = 0`` is the one worth naming: ``sqrt(0)/sigma`` is ``0.0``, which would reach
    ``delta_closed`` as ``mu = 0.0`` and surface one call later as a message about mu rather than
    about the step count that produced it.
    """
    with pytest.raises(ValueError):
        epsilon_for(sigma, steps, delta)


def test_epsilon_for_refusals_carry_distinct_messages():
    """Nine refusals wearing one message would be one refusal, so distinctness is asserted.

    The same discipline ``test_oracle_refuses`` applies to the quadrature's three non-vacuity
    conditions, applied to the inverse solver's domain.
    """
    cases = [
        (1.0, 0, mitigation_unit.DELTA),
        (1.0, 200, 0.0),
        (1.0, 200, 1.0),
        (-1.0, 200, mitigation_unit.DELTA),
        (float("nan"), 200, mitigation_unit.DELTA),
        (float("inf"), 200, mitigation_unit.DELTA),
        (1.0, 200.0, mitigation_unit.DELTA),
        (1.0, 200, float("nan")),
        (1.0, 200, 1e-320),
    ]
    texts = []
    for sigma, steps, delta in cases:
        with pytest.raises(ValueError) as excinfo:
            epsilon_for(sigma, steps, delta)
        texts.append(str(excinfo.value))
    assert len(set(texts)) == len(cases), (
        "epsilon_for's domain refusals do not carry distinct messages:\n"
        + "\n".join(f"  {case}: {text[:110]}" for case, text in zip(cases, texts))
    )


def _round_trip_pairs():
    """Twelve-plus (sigma, T) pairs spanning the frontier the Phase 23 sweep will visit.

    The seven ``GOLDEN_EPSILON`` sigmas (so the round trip is exercised at exactly the points the
    frozen pin constrains) plus five that are not pinned anywhere — 0.5 and 0.7 at the noisy end,
    1.5 and 3.0 in the middle, 50.0 at the quiet end — each at four step counts.
    """
    sigmas = [row[0] for row in mitigation_accountant.GOLDEN_EPSILON] + [0.5, 0.7, 1.5, 3.0, 50.0]
    return [(sigma, steps) for sigma in sigmas for steps in (1, 64, 200, 1000)]


@pytest.mark.parametrize(("sigma", "steps"), _round_trip_pairs())
def test_round_trip(sigma, steps):
    """V-07 -- ``sigma_for(epsilon_for(sigma, T, d), T, d)`` returns ``sigma``.

    D-12's stated purpose, and it is worth restating because the test looks redundant with the
    golden check: this is FREE, and it catches a divergent inverse — which NO single-direction
    test can see. A forward function that is wrong and an inverse that is wrong in exactly the
    compensating way both pass their own tests and fail this one.

    Measured worst deviation over these 48 pairs: **8.29e-15 relative**, against the
    ``ROUND_TRIP_REL_TOL`` budget of 1e-12.
    """
    epsilon = epsilon_for(sigma, steps, mitigation_unit.DELTA)
    back = sigma_for(epsilon, steps, mitigation_unit.DELTA)
    assert abs(back - sigma) <= ROUND_TRIP_REL_TOL * sigma, (
        f"round trip at sigma={sigma!r}, T={steps} went out at epsilon={epsilon!r} and came back "
        f"as {back!r} — relative {abs(back - sigma) / sigma:.3e} over {ROUND_TRIP_REL_TOL:.3e}"
    )


def test_round_trip_pairs_is_not_empty():
    """Meta-guard: V-07 sweeps 48 pairs, and the locator is really producing them.

    A parametrization built off ``GOLDEN_EPSILON`` inherits that table's failure modes — a
    truncated pin would silently shrink this sweep instead of reddening.
    """
    pairs = _round_trip_pairs()
    assert len(pairs) == 48, (
        f"V-07 is parametrized over {len(pairs)} pairs, not the 48 the sweep claims "
        f"(12 sigmas x 4 step counts) — the pin or the extra sigma list has changed"
    )
    assert len({sigma for sigma, _ in pairs}) == 12, (
        f"the sweep covers {len({s for s, _ in pairs})} distinct sigmas, not 12 — two entries "
        f"have collided and the sweep is narrower than it reads"
    )


@pytest.mark.parametrize("steps", [1, 64, 200, 1000])
def test_round_trip_at_sigma_zero(steps):
    """The sigma = 0 boundary round-trips EXACTLY, and here ``==`` is the correct assertion.

    Both ends are exact boundary values rather than bisected ones: ``epsilon_for`` returns
    ``math.inf`` from an explicit branch and ``sigma_for`` returns ``0.0`` from an explicit branch,
    so no arithmetic runs in either direction. This is the D-06 identity's own input — Phase 23's
    first executed DP run is the sigma = 0 point — which is why closing the round trip there
    matters more than closing it at any interior sigma.
    """
    delta = mitigation_unit.DELTA
    assert sigma_for(epsilon_for(0.0, steps, delta), steps, delta) == 0.0


@pytest.mark.parametrize(
    ("target_epsilon", "steps", "delta"),
    [
        (0.0, 200, mitigation_unit.DELTA),  # perfect privacy — no finite sigma solves it
        (-1.0, 200, mitigation_unit.DELTA),  # a negative privacy loss is not a mechanism
        (float("nan"), 200, mitigation_unit.DELTA),  # non-finite, and NOT +inf
        (float("-inf"), 200, mitigation_unit.DELTA),  # ditto
        (1.0, 0, mitigation_unit.DELTA),  # steps below one
        (1.0, 200.0, mitigation_unit.DELTA),  # steps as a float
        (1.0, 200, 0.0),  # delta at the closed lower end
        (1.0, 200, 1.0),  # delta at the closed upper end
        (math.inf, 0, mitigation_unit.DELTA),  # the +inf branch must NOT skip the domain check
        (math.inf, 200, 1.0),  # ditto, on delta
    ],
)
def test_sigma_for_domain_refusals(target_epsilon, steps, delta):
    """Degenerate inputs refuse, INCLUDING on the ``+inf`` fast path.

    The last two cases are the ones a naive ordering would miss: returning ``0.0`` for
    ``target_epsilon = inf`` BEFORE validating ``steps`` and ``delta`` would answer a question
    nobody could have asked, so ``_refuse_bad_steps_or_delta`` runs first.
    """
    with pytest.raises(ValueError):
        sigma_for(target_epsilon, steps, delta)


def test_sigma_for_uses_the_forward_function():
    """D-12's ONE choke point, asserted STRUCTURALLY rather than described.

    ``sigma_for`` must bisect over ``epsilon_for`` and over nothing else. A second bisection
    inlined here — over ``delta_closed`` directly, or over the quadrature oracle — would be free
    to disagree with the forward direction while both look right in isolation, which is exactly
    the failure D-12 exists to make impossible. The round trip catches that numerically; this
    catches it in the source, so a future edit reddens before it can be measured.
    """
    tree = ast.parse(_ACCOUNTANT_PATH.read_text(encoding="utf-8"))
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    # Meta-guard: an AST walk that stopped working would make every assertion below vacuous.
    assert "sigma_for" in functions, (
        f"accountant.py has no sigma_for FunctionDef — the walk found {sorted(functions)}"
    )
    called = {
        node.func.id
        for node in ast.walk(functions["sigma_for"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "epsilon_for" in called, (
        f"sigma_for's body calls {sorted(called)} and does NOT call epsilon_for — the inverse has "
        f"stopped bisecting over the forward function and D-12's one choke point is gone"
    )
    forbidden = called & {"delta_closed", "delta_quadrature"}
    assert forbidden == set(), (
        f"sigma_for's body calls {sorted(forbidden)} directly. The inverse must bisect over "
        f"epsilon_for, not over a re-derived closed form: a second bisection here is free to "
        f"disagree with the forward direction, which is the divergence D-12 forbids."
    )


def test_delta_closed_still_ships_exactly_four_raises():
    """``epsilon_for`` reads a caught ``ValueError`` as the underflow corner — this pins that.

    ``_delta_or_below_float64`` maps a ``delta_closed`` refusal to "delta is below float64's
    range, therefore below the target". That is sound because ``delta_closed`` ships exactly FOUR
    ``raise`` statements and the first two — a non-finite input, and ``mu <= 0.0`` — are
    structurally unreachable from the search, which re-checks ``eps`` finite and enters with a
    finite, strictly positive ``mu``. Only the representability and exact-zero refusals can fire,
    and both mean exactly one thing.

    (FOUR ``raise`` statements, THREE numbered refusals: ``delta_closed``'s docstring calls the
    non-finite check and the ``mu <= 0.0`` check "Refusal 1 of 3" jointly, and they are two
    statements. This test counts statements, because a statement is what a new refusal would add.)

    A FIFTH ``raise`` with different semantics would silently widen that reading into something
    the argument no longer covers. This reddens instead, which is the whole point: it forces the
    next author to re-read ``_delta_or_below_float64``'s contract rather than inherit it.
    """
    tree = ast.parse(_ACCOUNTANT_PATH.read_text(encoding="utf-8"))
    bodies = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "delta_closed"
    }
    assert "delta_closed" in bodies, (
        "delta_closed has no FunctionDef in accountant.py — the AST walk found nothing to count"
    )
    raises = [n.lineno for n in ast.walk(bodies["delta_closed"]) if isinstance(n, ast.Raise)]
    assert len(raises) == 4, (
        f"delta_closed now raises at {raises} — {len(raises)} statements, not the four "
        f"epsilon_for's underflow reading is argued against. Re-read "
        f"accountant._delta_or_below_float64's docstring before changing this number."
    )


def test_accountant_imports_math_only():
    """V-09 -- ``accountant.py`` imports ``math`` and nothing else, statically AND transitively.

    Two complementary halves, the ``tests/test_phase15_plots.py`` shape. (a) is the readable
    statement of intent; (b) is the one that cannot be fooled -- it catches an import arriving
    through a helper module the single-file walk cannot see. (b) MUST run out of process: by the
    time this test runs, ``torch`` is already in ``sys.modules`` from sibling tests, so an
    in-process ``"torch" not in sys.modules`` check would be vacuous.

    The static half asserts HARD EQUALITY rather than ``imported <= {"math"}``. A subset form is
    satisfied by the empty set, which is exactly the collapsed-walk failure the meta-guard above it
    exists to catch -- equality makes that structural instead of leaving it to the meta-guard alone.

    SCOPING NOTE (22-PATTERNS.md section 3), recorded because a future reader will otherwise
    believe this guard is broader than it is: it scopes to this ONE file. A ``privacy/__init__.py``
    that re-exported from ``accountant`` would add a relative ``ImportFrom`` (``node.level == 1``)
    to the PACKAGE, not to this module, so it would pass here and that is correct. Plan 22-01
    shipped ``__init__.py`` with no re-exports, so the question is currently moot.
    """
    tree = ast.parse(_ACCOUNTANT_PATH.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    # Meta-guard FIRST: a walk that silently stopped working would otherwise pass by finding
    # nothing at all.
    assert imported, "the AST import walk found no imports — the walk stopped working"
    assert imported == {"math"}, (
        f"accountant.py imports {sorted(imported)}; D-10 permits exactly {{'math'}}. Offenders: "
        f"{sorted(imported - {'math'})}. pyproject.toml must stay untouched (RPT-03)."
    )

    relative = _ACCOUNTANT_PATH.relative_to(_ROOT).as_posix()
    probe = (
        "import importlib.util, sys;"
        f"spec = importlib.util.spec_from_file_location('acct', {relative!r});"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "bad = [n for n in ('torch', 'numpy', 'scipy', 'mpmath') if n in sys.modules];"
        "print(bad); sys.exit(1 if bad else 0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"accountant.py transitively loads a forbidden module — D-10/RPT-03 violated\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_accountant_has_no_assert_and_no_prove():
    """D-15's refusal register, enforced structurally rather than left to convention.

    An ``assert`` is stripped under ``python -O``, which would turn a loud refusal into a silently
    wrong published delta -- ``lora/layer.py::LoRALinear.merge``'s docstring records that exact
    reason for this repository, and Phase 21 WR-06 promoted a wall from ``assert`` to ``SystemExit``
    on the same grounds. ``_prove`` is the ``scripts/`` register (measured: 18 ``scripts/`` modules,
    0 ``src/`` modules); importing that habit here would put two refusal vocabularies in one
    package.

    The ``ast.Raise`` presence check is the load-bearing half: a file that lost every refusal would
    otherwise pass this test by having lost the asserts along with them.
    """
    tree = ast.parse(_ACCOUNTANT_PATH.read_text(encoding="utf-8"))
    raises = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Raise)]
    assert len(raises) >= 6, (
        f"accountant.py contains {len(raises)} raise statements, fewer than the six refusals the "
        f"two oracles ship — this guard is vacuous on a file that has lost its refusals"
    )
    asserts = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    assert asserts == [], (
        f"accountant.py asserts at lines {asserts}; D-15 requires `raise` — an assert is stripped "
        f"under `python -O`, turning a loud refusal into a silently wrong delta"
    )
    proves = [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_prove"
    ]
    assert proves == [], (
        f"accountant.py calls _prove at lines {proves}; that is the scripts/ register (18 "
        f"scripts/ modules, 0 src/ modules), never src/'s"
    )
