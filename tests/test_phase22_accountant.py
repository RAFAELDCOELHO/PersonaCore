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
import random
import subprocess
import sys

import pytest
from tests.fixtures.phase22_reference import (
    DELTA_FRONTIER,
    EPSILON_OVERFLOW_REGIME,
    VACUOUS_AGREEMENT_ROW,
)

from personacore.privacy.accountant import (
    ROUND_TRIP_REL_TOL,
    _log_erfc,
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
    """Meta-guard: V-01 sweeps twelve rows, and it is really sweeping them.

    A parametrization that silently emptied -- a renamed fixture constant, a truncated table, a
    locator that stopped matching -- makes V-01 green having compared nothing at all. Hard equality
    against ``VACUOUS_AGREEMENT_ROW`` additionally pins WHICH row is excluded: "one row is not
    representable" is satisfied by a table where a DIFFERENT row silently went to zero.
    """
    rows = _representable_rows()
    assert len(rows) == 12, (
        f"V-01 is parametrized over {len(rows)} rows, not the 12 representable frontier rows — "
        f"the twelfth is the b > 27.2 row (eps=775.7866600701457, mu=35.35533905932738), whose "
        f"whole purpose is to put V-01 and V-02 inside the band they could not previously reach"
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


def _erfc_b(eps, mu):
    """``delta_closed``'s SECOND erfc argument, ``b = (eps/mu + mu/2)/sqrt(2)``.

    Spelled here rather than imported so the two ``_log_erfc`` guards below derive ``b`` the same
    way the implementation does without reaching into it for the value they are judging.
    """
    return (eps / mu + mu / 2.0) / math.sqrt(2.0)


def _pinned_points():
    """Every ``(label, eps, mu)`` this module answers on a committed or FROZEN row.

    The representable ``DELTA_FRONTIER`` rows, plus the seven FROZEN ``GOLDEN_EPSILON`` rows
    re-expressed as ``(pinned_epsilon, sqrt(steps)/sigma)`` — which is exactly the ``(eps, mu)``
    pair ``epsilon_for``'s bisection converges onto, and therefore the pair whose ``b`` decides
    which branch of ``_log_erfc`` answers it.
    """
    points = [(f"DELTA_FRONTIER({eps}, {mu})", eps, mu) for eps, mu, _ in _representable_rows()]
    points += [
        (f"GOLDEN_EPSILON(sigma={sigma}, T={steps})", pinned, math.sqrt(steps) / sigma)
        for sigma, steps, pinned in mitigation_accountant.GOLDEN_EPSILON
    ]
    return points


def _inert_points():
    """The pinned points whose ``b`` is OUTSIDE the erfc underflow band.

    Located by ``math.erfc(b) > 0.0`` rather than by index or by name, so the set cannot rot if a
    table is reordered — the same locator discipline ``_representable_rows`` uses. The one pinned
    point this excludes is the thirteenth ``DELTA_FRONTIER`` row, which exists precisely BECAUSE
    its ``b`` underflows, and which ``test_log_erfc_matches_the_committed_underflow_truth`` owns
    instead. ``test_log_erfc_inert_points_are_not_empty`` pins both the count and that exclusion by
    hard equality, so this filter cannot silently swallow a row it was never meant to.
    """
    return [point for point in _pinned_points() if math.erfc(_erfc_b(point[1], point[2])) > 0.0]


def test_log_erfc_inert_points_are_not_empty():
    """Meta-guard: the inertness sweep covers 18 pinned points, and excludes exactly the one row.

    ``_inert_points`` filters on ``erfc(b) > 0.0``, so the per-point test below cannot ALSO assert
    that condition without asserting a tautology. The non-vacuity therefore lives here, in this
    file's own established shape (``test_closed_form_frontier_parametrization_is_not_empty``,
    ``test_round_trip_pairs_is_not_empty``): a filter that silently emptied, or that swallowed a
    pinned row along with the intended one, would leave the sweep green over less than it claims —
    and what it claims is that a FROZEN pre-registration cannot move.

    Eighteen: eleven previously-representable ``DELTA_FRONTIER`` rows plus seven ``GOLDEN_EPSILON``
    rows. The exclusion is asserted by HARD EQUALITY rather than by count, because "one row is in
    the band" is equally satisfied by a table where a DIFFERENT row drifted into it — which would
    mean a pinned epsilon had started being answered by the asymptotic series without anything
    reddening.
    """
    points = _inert_points()
    assert len(points) == 18, (
        f"the inertness sweep covers {len(points)} pinned points, not the 18 it claims (11 "
        f"previously-representable DELTA_FRONTIER rows + 7 GOLDEN_EPSILON rows)"
    )
    kept = {label for label, _, _ in points}
    excluded = [(label, eps, mu) for label, eps, mu in _pinned_points() if label not in kept]
    assert [label for label, _, _ in excluded] == [
        "DELTA_FRONTIER(775.7866600701457, 35.35533905932738)"
    ], (
        f"the pinned points inside the erfc underflow band are {[p[0] for p in excluded]}, not "
        f"exactly the thirteenth DELTA_FRONTIER row. Any OTHER row landing in that band means a "
        f"pinned answer is now produced by the asymptotic series instead of by math.log(erfc(b)) — "
        f"and GOLDEN_EPSILON is FROZEN, so such a move would be unrecoverable"
    )


@pytest.mark.parametrize(("label", "eps", "mu"), _inert_points())
def test_log_erfc_is_inert_where_erfc_is_healthy(label, eps, mu):
    """``_log_erfc`` CANNOT MOVE A PINNED ROW — asserted by exact equality, never by tolerance.

    ``scripts/mitigation_accountant.py::GOLDEN_EPSILON`` is a FROZEN pre-registration: a
    correction after the first ``results/phase23_*`` artifact is a dated continuation via
    ``scripts/_addendum.py`` and never an edit, so an accountant change that MOVES a pinned
    epsilon is unrecoverable rather than merely wrong. ``_log_erfc``'s fast path is what makes
    that impossible: ``if erfc(x) > 0.0: return log(erfc(x))`` runs FIRST and UNCONDITIONALLY, so
    every input whose erfc is healthy gets bit-for-bit the arithmetic the shipped code already
    performed, and the asymptotic series is reachable only where the shipped code was returning
    ``0.0`` instead.

    This states that structurally rather than trusting it. The failure it exists to catch is a
    future edit "simplifying" ``_log_erfc`` into using the series everywhere: measured, deleting
    the fast path moves six of the seven pinned epsilons and sends four of them to ``0.0``,
    because the pinned rows sit at ``b`` between 3.19 and 7.94 where the asymptotic expansion is
    worth roughly three digits.

    The non-vacuity half — that this sweep really covers 18 points and excludes exactly the one
    row whose ``b`` underflows — lives in ``test_log_erfc_inert_points_are_not_empty``, because
    ``_inert_points`` already filters on ``erfc(b) > 0.0`` and re-asserting it here would be a
    tautology rather than a guard.
    """
    b = _erfc_b(eps, mu)
    healthy = math.erfc(b)
    assert _log_erfc(b) == math.log(healthy), (
        f"{label}: _log_erfc({b!r}) = {_log_erfc(b)!r} is NOT BIT-IDENTICAL to "
        f"math.log(math.erfc(b)) = {math.log(healthy)!r}. The fast path is gone or reordered, so "
        f"this pinned row is now answered by the asymptotic series — and GOLDEN_EPSILON is a "
        f"FROZEN pre-registration with NO correction path"
    )


def test_log_erfc_matches_the_committed_underflow_truth():
    """``_log_erfc`` is CORRECT past the erfc cliff, against a committed 60-dps truth.

    The inertness guard above proves ``_log_erfc`` changes nothing where erfc is healthy. It says
    nothing about the branch that actually does the new work, and a series that is inert AND wrong
    is exactly as useless as no series at all. This is that branch's own truth.

    ``b = 28.01573320140291`` is ``delta_closed``'s second erfc argument at
    (eps=775.7866600701457, mu=35.35533905932738) — sigma=0.40 / T=200 at the frozen delta, the
    point the shipped comment cited as reachable and the point at which the shipped code silently
    dropped the whole term. ``math.erfc(b)`` there is exactly ``0.0``; ``log(erfc(b))`` is
    ``-788.787``, a perfectly ordinary number.

    PROVENANCE of the literal — mpmath 1.3.0, present in ``.venv`` only as a TRANSITIVE dependency
    of torch (torch -> sympy -> mpmath), declared in neither ``pyproject.toml`` nor
    ``requirements.txt``, and imported by NOTHING in this suite (RPT-03;
    ``tests/test_phase22_reference.py::test_no_phase22_test_imports_mpmath`` enforces that by AST
    over the whole ``test_phase22_*`` glob). It was computed by a ONE-OFF shell invocation whose
    OUTPUT is committed here as data::

        .venv/bin/python -c "
        from mpmath import mp
        mp.dps = 60
        print(mp.nstr(mp.log(mp.erfc(mp.mpf(28.01573320140291))), 25))"
        # -> -788.7870740351563058464846

    ``mp.mpf(28.01573320140291)`` takes the PYTHON FLOAT, i.e. the exact binary64 value the
    implementation passes, rather than ``mp.mpf("28.01573320140291")`` which would re-parse the
    decimal to a different number. That distinction is recorded because it is the denominator:
    the truth below is ``log(erfc(x))`` at the SAME x the code evaluates, so the deviation
    measured is the series' own, with no input mismatch folded in.

    THE TOLERANCE IS MEASURED, NOT CHOSEN. Deviation on this box: **7.55e-17 relative**
    (5.96e-14 ABSOLUTE in the log, which is 0.52 of one ulp of ``-788.787``). 1e-15 is that
    rounded up to the next decade with ~13x of margin. Stated in the units that matter downstream:
    an absolute error ``d`` in the log is a relative error ``d`` in ``exp(eps + log)``, so 1e-15
    relative here is 7.9e-13 relative in the second term — inside the frontier row's own 1.5e-12
    budget. WATCHED: truncating the series to one term (``S = 1 - 1/(2x**2)``) makes the absolute
    error 1.2144e-06, six orders past this bound, and reddens this test.
    """
    b = (775.7866600701457 / 35.35533905932738 + 35.35533905932738 / 2.0) / math.sqrt(2.0)
    # META-GUARD: this test's whole subject is the branch BEYOND the cliff. If erfc(b) were still
    # representable, _log_erfc would return math.log(erfc(b)) from its fast path and this would be
    # a test of math.log rather than of the asymptotic series.
    assert math.erfc(b) == 0.0, (
        f"math.erfc({b!r}) = {math.erfc(b)!r}, not exactly 0.0 — this input is NO LONGER in the "
        f"underflow band, so _log_erfc answers it from the fast path and the series this test "
        f"exists to check is never reached"
    )

    truth = float("-788.7870740351563058464846")
    got = _log_erfc(b)
    rel = abs(got - truth) / abs(truth)
    assert rel <= 1e-15, (
        f"_log_erfc({b!r}) = {got!r} against the committed 60-dps log(erfc(b)) "
        f"-788.7870740351563058464846 — relative {rel:.3e} over the measured-plus-margin 1e-15 "
        f"({abs(got - truth):.3e} ABSOLUTE in the log, which is the same figure as the relative "
        f"error the second term of delta_closed inherits)"
    )


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

    Measured worst gap between the two oracles over these TWELVE rows: **1.105e-11 relative**, at
    the thirteenth frontier row (eps=775.7866600701457, mu=35.35533905932738) -- roughly 90x
    inside the 1e-9 budget. That row is the reason this figure moved: the previous worst was
    2.84e-12 at eps=2.0, mu=0.1, over a sweep that never entered the ``b > 27.2`` band at all.
    Where the shipped closed form silently dropped its second term there, this comparison read
    **12.74% relative** -- the falsification that made Phase 22 verify ``gaps_found``. The budget
    is NOT widened to accommodate it; 1e-9 stands, and the fix is what brought the gap inside it.
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


def test_quadrature_budgets_the_simpson_sum_not_one_term():
    """The measured ``+inf`` band REFUSES — condition 1 budgets for the sum, not for one term.

    ``_EXP_OVERFLOW_ARG`` bounds a SINGLE ``math.exp`` argument, but the Simpson loop accumulates
    ``n`` of them at weights up to 4.0 and a float ADDITION that leaves float64 returns ``inf``
    silently rather than raising. So the running ``total`` overflowed while condition 1 was still
    silent, and the oracle DPSGD-03's whole argument rests on returned ``inf`` for a probability.

    MEASURED IN THIS TREE, before the fix: sweeping eps=1e-4 over mu in [74.0, 78.0] at a step of
    1e-3 gave **404 of 4001 cells non-finite**, first at mu=74.951, while this refusal did not fire
    until mu=75.355 — ~0.19 too late in z. After subtracting ``log(4*n)`` (11.28983191240606 at
    n=20001) from the negative-z budget: **0 non-finite**, and the first refusal moves to
    mu=74.753. That 4001-cell measurement lives in ``22-14-SUMMARY.md``, NOT here: CI gets a dozen
    deterministic points spanning the FORMER hole, which run in milliseconds because a refusal
    short-circuits before the 20,001-node loop.

    SCOPED TO REFUSALS ON PURPOSE. There is deliberately no probability-range assertion in this
    test. Every point below refuses, so a ``(0, 1]`` clause would assert nothing inside the band —
    and read over the wider mu in [74, 78], 368 of the 753 cells this fix leaves ANSWERED return
    1.0000000000000655, which is above 1.0. That half is
    ``test_quadrature_returns_a_probability_or_refuses``'s, and its boundary is MEASURED rather
    than guessed.
    """
    # The exact point 22-VERIFICATION.md reproduced as returning `inf`.
    with pytest.raises(ValueError, match="DOMAIN LIMIT"):
        delta_quadrature(0.000440884929509763, 75.3129260813192)

    lo, hi = 74.951, 75.355  # measured: first shipped `inf` -> first shipped refusal
    band = [lo + k * (hi - lo) / 13 for k in range(14)]
    assert len(band) >= 12, (
        f"the band sweep degenerated to {len(band)} points — a loop over an empty or near-empty "
        f"list passes vacuously, which is the failure this meta-guard exists to catch"
    )

    answered = []
    refused = 0
    for mu in band:
        try:
            answered.append((mu, delta_quadrature(1e-4, mu)))
        except ValueError:
            refused += 1
    assert answered == [], (
        f"the former `inf` hole is answering again at {answered!r}. Condition 1's negative-z "
        f"clause is back to bounding ONE math.exp argument instead of the Simpson SUM, so the "
        f"accumulation leaves float64 silently and this oracle returns a non-probability."
    )
    # Meta-guard: a band that stopped reaching the boundary would leave `answered` empty for the
    # wrong reason only if it also refused nothing, which is impossible here — but a future edit
    # that made every call raise for an UNRELATED reason (a bad grid, say) would still be caught
    # by the `match="DOMAIN LIMIT"` above, and an empty band is caught by the length guard.
    assert refused == len(band), (
        f"only {refused} of {len(band)} band points refused — the sweep is no longer measuring "
        f"the boundary it was pinned to"
    )


def test_quadrature_returns_a_probability_or_refuses():
    """V-05's upper half — the oracle returns a value in ``(0, 1]`` or it raises. Never between.

    ``delta_quadrature`` is the INDEPENDENT ORACLE the whole DPSGD-03 correctness argument rests
    on, and an oracle that can return ``inf`` or 1.0000000000000655 for a PROBABILITY is not one
    that can be compared to anything. The shipped magnitude refusal was one-sided
    (``if delta <= 0.0``), so the upper end was unguarded entirely.

    THE BOUNDARY IS MEASURED, NOT TRANSCRIBED, and that distinction is the point of this test.
    ``22-VERIFICATION.md`` proposed the literal ``if not (0.0 < delta <= 1.0): raise``. Measured
    over 6000 draws at seed 20260826 (eps log-uniform in [1e-8, 5.0], mu log-uniform in
    [0.01, 200.0]), that form would have REFUSED **267 of 5351 answered cells — 4.99%** — whose
    true delta is within an ulp of 1.0 (the eps -> 0 limit of every mechanism), the largest excess
    being 5.107e-14, i.e. 230 ulp. ``delta_closed`` never exceeds 1.0; only the Simpson
    accumulation does, and only by float64 rounding. So the shipped refusal fires above
    ``1.0 + _DELTA_ACCUMULATION_SLACK`` (1e-11, 195.8x the seeded maximum and 152.7x the worst
    excess measured anywhere) and saturates at the mathematical bound below it.

    THE META-GUARDS ARE WHAT KEEP THIS FROM BEING DECORATIVE. A sweep that refused everything, or
    that never reached the boundary at all, would pass a bare ``0 < d <= 1`` loop trivially. So
    the answered and refused counts are BOTH pinned non-empty, and — the one that actually
    matters — so is the SATURATION count: if no cell in this sample lands above 1.0 before
    saturation, reverting the check to the shipped one-sided ``delta <= 0.0`` would leave this
    test green and it would be watching nothing. Measured on this sample: 212 answered, 28
    refused, **14 saturated**, in 0.60 s.
    """
    rng = random.Random(20260826)
    cells = []
    for _ in range(240):
        eps = math.exp(rng.uniform(math.log(1e-8), math.log(5.0)))
        mu = math.exp(rng.uniform(math.log(0.01), math.log(200.0)))
        cells.append((eps, mu))

    answered = refused = saturated = 0
    for eps, mu in cells:
        try:
            delta = delta_quadrature(eps, mu)
        except ValueError:
            refused += 1
            continue
        answered += 1
        assert math.isfinite(delta), (
            f"delta_quadrature({eps!r}, {mu!r}) returned {delta!r} — a non-finite probability. The "
            f"Simpson accumulation left float64 and condition 1 did not see it."
        )
        assert 0.0 < delta <= 1.0, (
            f"delta_quadrature({eps!r}, {mu!r}) returned {delta!r}, which is not in (0, 1]. delta "
            f"is a probability and delta <= 1.0 is a THEOREM, not a tolerance."
        )
        if delta == 1.0:
            saturated += 1

    assert answered >= 1 and refused >= 1, (
        f"the sweep answered {answered} and refused {refused} of {len(cells)} cells — a sweep that "
        f"does one or the other exclusively passes the (0, 1] loop above vacuously"
    )
    assert saturated >= 1, (
        f"no cell in this {len(cells)}-cell sample reached the saturation branch (measured: 14). "
        f"Without one, reverting the magnitude check to the shipped one-sided `delta <= 0.0` "
        f"would leave this test GREEN — it would be watching nothing. Widen the sample."
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


@pytest.mark.parametrize(("sigma", "steps", "truth_str"), EPSILON_OVERFLOW_REGIME)
def test_epsilon_for_survives_the_overflow_regime(sigma, steps, truth_str):
    """RESEARCH F2 -- the search WALKS INTO eps > 709.78, and comes back with the RIGHT number.

    Phase 23 would never PUBLISH eps = 775. But ``sigma_for`` bisects sigma downward and
    ``epsilon_for`` doubles its bracket upward, so both enter this domain during an ordinary
    search. The naive ``exp(eps) * erfc(b)`` second term raises ``OverflowError`` there and would
    abort a legitimate solve; the log-space form does not.

    WHY A LIVENESS ASSERTION WAS NOT ENOUGH, which is this test's own history rather than a
    hypothetical. It shipped parametrized over exactly these two sigmas -- the ONLY two on the
    whole frontier where the closed form's dropped second term bites -- and asserted nothing about
    the value beyond ``math.isfinite(got)`` and ``got > 700.0``. Both held perfectly while
    ``epsilon_for`` returned 775.7866600701457 against a truth of 774.8427215876997, a relative
    **1.218e-03** in a module whose two published tolerances are both 1e-12. The test that walked
    straight into the defect was structurally incapable of seeing it: a number wrong in the fourth
    significant digit is still finite and still above 700. ``test_two_oracles_agree`` could not see
    it either, because no committed frontier row lived in the band -- which is what the thirteenth
    ``DELTA_FRONTIER`` row now fixes.

    THE ``math.isfinite`` LEG IS KEPT rather than subsumed. It states the overflow-survival
    property directly, and it is the assertion that fails with a readable message if a future edit
    reintroduces the naive product: an ``OverflowError`` escaping from inside the bisection is a
    different and less legible failure than a comparison against a committed truth.

    THE TOLERANCE IS MEASURED. Deviation of the fixed ``epsilon_for`` from these committed 60-dps
    truths on this box: **0.0e+00** at sigma=0.40 (the 60-dps root and the float64 root round to
    one double) and **1.734e-16** at sigma=0.30. ``ROUND_TRIP_REL_TOL`` -- this module's existing
    1e-12 register -- therefore carries at least twelve orders of margin here, and no
    "these must differ" non-vacuity leg is asserted, because at sigma=0.40 a bitwise match is the
    CORRECT outcome rather than a suspicious one: the 60-dps root sits 0.45 ulp from the float64
    root, so landing on the same double is what a correct implementation does. The pin that must
    NOT match bitwise is ``GOLDEN_EPSILON``, and its own test carries that control.

    The truths are a 60-dps bisection of the SAME closed form, so they catch float64 and
    truncation error and NOT a formula error -- see ``EPSILON_OVERFLOW_REGIME``'s provenance block,
    which says so, and names the thirteenth frontier row's V-02 leg as where independence in this
    band actually comes from.
    """
    got = epsilon_for(sigma, steps, mitigation_unit.DELTA)
    assert math.isfinite(got), (
        f"epsilon_for({sigma}, {steps}, delta) returned {got!r} — the search did not survive the "
        f"eps > 709.782712893384 regime it walks through to reach this answer"
    )
    truth = float(truth_str)
    rel = abs(got - truth) / truth
    assert rel <= ROUND_TRIP_REL_TOL, (
        f"epsilon_for({sigma}, {steps}, delta) = {got!r} against the committed 60-dps truth "
        f"{truth_str} — relative {rel:.3e} over {ROUND_TRIP_REL_TOL:.3e}. The shipped accountant "
        f"returned 775.7866600701457 and 1312.1599912046381 for these two rows (1.218e-03 and "
        f"7.300e-04 relative) by discarding delta_closed's second term past the erfc cliff"
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


# The composition sweep's RNG seed, stated once and used by every consumer below so the sweep is
# reproducible and its distribution is RESEARCH F3's: sigma log-uniform in [0.5, 200], T uniform
# integer in [1, 5000]. F3 drew 4,000 samples from exactly this and measured a 19.9% bitwise
# disagreement rate end to end.
_COMPOSITION_SEED = 20260825


def _composition_pairs():
    """A deterministic grid plus a seeded sample from RESEARCH F3's own distribution.

    Both halves are needed and they fail differently. The GRID pins the frontier points a reader
    can check by hand and keeps the sweep meaningful if the RNG implementation ever changes; the
    SAMPLE is what actually contains bitwise disagreement, because round sigmas are much more
    likely to agree to the last bit. F3 measured that trap directly — its first five hand-chosen
    pairs were all bitwise equal — which is why ``test_composition_identity`` alone is not enough
    and its negative control below asserts the sample is doing its job.
    """
    grid = [
        (0.5, 1),
        (0.5, 64),
        (0.7, 200),
        (1.0, 1),
        (1.0, 1000),
        (2.0, 200),
        (3.0, 64),
        (5.0, 200),
        (8.0, 64),
        (10.0, 200),
        (14.142135623730951, 200),
        (20.0, 200),
        (50.0, 1),
        (50.0, 5000),
        (100.0, 3000),
        (200.0, 5000),
    ]
    rng = random.Random(_COMPOSITION_SEED)
    sample = [
        (math.exp(rng.uniform(math.log(0.5), math.log(200.0))), rng.randint(1, 5000))
        for _ in range(12)
    ]
    return grid + sample


@pytest.mark.parametrize(("sigma", "steps"), _composition_pairs())
def test_composition_identity(sigma, steps):
    """V-03 -- the SECOND oracle: ``eps(sigma, T, d)`` against ``eps(sigma/sqrt(T), 1, d)``.

    THE IDENTITY IS EXACT IN REAL ARITHMETIC. ``mu_eff(sigma, T) = sqrt(T)/sigma`` and
    ``mu(sigma/sqrt(T), 1) = 1/(sigma/sqrt(T))`` are the same number, and Dong-Roth-Su Corollary
    3.3 is an EXACT EQUALITY of trade-off functions covering adaptive composition — not an upper
    bound. So this is a genuine oracle on ``epsilon_for``, reached by a different call shape.

    AND IT FAILS BITWISE 19.9% OF THE TIME IN FLOAT64. RESEARCH F3, 4,000 samples at seed
    20260825: 795/4000 disagree end to end, worst relative gap **1.184e-14 (82 ulp)** at
    sigma=184.50381354671796, T=119. The cause is double-rounding and nothing else —
    ``sqrt(T)/sigma`` costs two roundings, ``1.0/(sigma/sqrt(T))`` costs three. **The mathematics
    of D-13 is confirmed exact; only its transcription as ``==`` is wrong.**

    1e-12 is therefore the tolerance, ~2 orders over the measured worst case, and NEVER ``==``.
    Measured over this sweep's own pairs: worst relative gap 9.01e-16.
    """
    delta = mitigation_unit.DELTA
    composed = epsilon_for(sigma, steps, delta)
    single = epsilon_for(sigma / math.sqrt(steps), 1, delta)
    assert abs(composed - single) <= 1e-12 * abs(single), (
        f"the composition identity failed at sigma={sigma!r}, T={steps}: "
        f"epsilon_for(sigma, T) = {composed!r} against epsilon_for(sigma/sqrt(T), 1) = {single!r}, "
        f"relative {abs(composed - single) / abs(single):.3e} over the 1e-12 budget"
    )


def test_composition_identity_would_fail_under_exact_equality():
    """The negative control: this sweep really does contain bitwise disagreement.

    Without it ``test_composition_identity`` could be green on a sweep that happens to be
    all-bitwise-equal by luck, proving nothing about the tolerance it uses — and RESEARCH F3
    measured exactly that trap: *"my first 5 hand-chosen pairs were all bitwise equal, and so were
    the 3 in the end-to-end check."* A sweep that agreed everywhere would make ``==`` look correct
    and would silently license writing it, which is the one conclusion F3 forbids.

    So this asserts the sweep is NON-DEGENERATE rather than asserting a rate: fewer bitwise-equal
    pairs than pairs. Measured on this sweep: 3 of 28 disagree (F3's own 19.9% is over 4,000
    random draws; a 16-point round-number grid pulls this sweep's rate down, which is precisely
    why the seeded sample is in it).
    """
    delta = mitigation_unit.DELTA
    pairs = _composition_pairs()
    # Meta-guard: an empty or truncated sweep would make the count assertion below vacuous.
    assert len(pairs) >= 20, (
        f"the composition sweep is {len(pairs)} pairs, fewer than the 20 V-03 requires — a "
        f"shrunken sweep makes both this control and the identity test green over less"
    )
    equal = [
        (sigma, steps)
        for sigma, steps in pairs
        if epsilon_for(sigma, steps, delta) == epsilon_for(sigma / math.sqrt(steps), 1, delta)
    ]
    assert len(equal) < len(pairs), (
        f"all {len(pairs)} swept pairs are BITWISE equal, so test_composition_identity is green "
        f"over a sweep containing no disagreement at all and proves nothing about its tolerance. "
        f"RESEARCH F3 measures 19.9% disagreement over 4,000 random draws — widen the sweep "
        f"(more seeded samples, or a wider sigma/T range) rather than believing this."
    )


def test_tolerance_register_is_documented():
    """Both tolerance registers are written down, ADJACENTLY, so they cannot be conflated.

    V-03 above compares TWO DIFFERENT CALL SHAPES and must use ``rel_tol``. DPSGD-05's kill/resume
    check (plan 22-07) compares THE SAME CALL SHAPE across two processes and must use exact
    ``==``. Both are correct; each is wrong in the other's place, and the failure mode is a reader
    who has seen only one of them. Writing them down next to each other is what prevents it, so
    this asserts they ARE next to each other rather than trusting that they are.

    The ``==`` half cites ``lora/inject.py::load_adapter_weights``'s W1 comment, which argues for
    exact equality on precisely this ground — the same operation on the same operands gives a
    bit-identical float — and says in its own words that *"a tolerance would only weaken this."*
    """
    tree = ast.parse(_ACCOUNTANT_PATH.read_text(encoding="utf-8"))
    docstring = ast.get_docstring(tree)
    # Meta-guard: a missing or emptied module docstring would satisfy nothing below by vacuity,
    # but it would also make every "in" check fail confusingly rather than at the real cause.
    assert docstring and len(docstring) > 500, (
        f"accountant.py's module docstring is {len(docstring or '')} characters — there is no "
        f"register to read, so this guard would be asserting against an empty string"
    )
    required = [
        "TWO DIFFERENT CALL SHAPES",
        "RELATIVE TOLERANCE of 1e-12",
        "THE SAME CALL SHAPE ACROSS TWO PROCESSES",
        "exact ``==``",
        "DPSGD-05",
        "lora/inject.py::load_adapter_weights",
        "a tolerance would only weaken",
        "F3",
    ]
    missing = [text for text in required if text not in docstring]
    assert missing == [], (
        f"accountant.py's module docstring no longer states {missing}. Both halves of RESEARCH "
        f"F3's rule must live in one place: rel_tol=1e-12 for two different call shapes, exact == "
        f"for the same call shape across two processes. A register with one half removed is how "
        f"the two get conflated."
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


# =============================================================================================
# V-06 (plan 22-09). Every pinned golden epsilon RE-DERIVED from the QUADRATURE ORACLE ALONE.
#
# WHY THIS IS NOT A CONTRADICTION OF D-12's SINGLE-CHOKE-POINT RULE. D-12 forbids improvising a
# bisection in PRODUCTION code (`scripts/mitigation_budget.py`, a driver) — a second solver free
# to disagree with `epsilon_for` is exactly what that rule exists to prevent. D-13 REQUIRES a
# re-derivation by an independent route HERE, and the two rules do not collide: this bisection is
# test-local, is never importable by a caller, and its whole purpose is to be a DIFFERENT route.
# A golden table read off the implementation shares the implementation's failure modes BY
# CONSTRUCTION — a PHOTOGRAPH OF THE CODE rather than a CONSTRAINT ON IT, green on the day it was
# taken and green forever after, including every day the code is wrong in the same way.
# =============================================================================================

_THIS_FILE = pathlib.Path(__file__).resolve()

# The bisection's own budget. The measured worst case over the seven rows is 47 halvings and 6
# doublings, so these caps are ~4x and ~10x headroom; they exist so a broken oracle produces a
# named failure instead of an infinite loop.
_ORACLE_BISECT_REL_WIDTH = 1e-14
_ORACLE_BISECT_MAX_STEPS = 200
_ORACLE_BISECT_MAX_DOUBLINGS = 60

# The two callees that would turn V-06 from a constraint into a photograph. Asserted STRUCTURALLY
# over the test's own AST rather than promised in a docstring, because a docstring cannot redden.
_V06_FORBIDDEN_CALLEES = frozenset({"epsilon_for", "delta_closed"})

# MEASURED, on this box, by the bisection below: the worst relative deviation between the
# oracle-derived epsilon and the pinned one across all seven rows is 5.749506e-15 (the sigma = 2.0
# row). Two float64 quadratures of different integrals cannot agree more closely than this, and
# `GOLDEN_EPSILON_REL_TOL = 1e-12` therefore carries ~174x of margin over it.
_V06_MEASURED_ORACLE_GAP = 5.749506e-15

# The negative control's perturbation, and the ceiling that makes it BITE.
#
# DELIBERATELY NOT `10 * GOLDEN_EPSILON_REL_TOL`, which is what plan 22-09 specifies and which is
# STRUCTURALLY INCAPABLE of the job it is given. `abs(p*(1 + 10*t) - p) > t*p` is true for EVERY
# t > 0, so a perturbation defined as a multiple of the tolerance stays green after the tolerance
# is widened to 1e-3 — the exact widening the control exists to detect. Watched: with the
# tolerance at 1e-3 the multiple-of-tolerance form still passes. So the perturbation is a FIXED
# relative amount (1e-9: ~174,000x the measured oracle gap, and the smallest scale a real
# implementation error plausibly reaches) and the tolerance carries its own ceiling.
_V06_PERTURBATION = 1e-9
_GOLDEN_REL_TOL_CEILING = 1e-11


def test_golden_epsilon_from_oracle():
    """V-06 -- all seven ``GOLDEN_EPSILON`` rows re-derived by bisecting ``delta_quadrature``.

    THE ORACLE ONLY. This body calls neither ``epsilon_for`` nor ``delta_closed``, and that is
    asserted over this function's OWN AST below rather than claimed here -- a claim in a docstring
    is exactly what a future edit "simplifying" the test by calling the implementation would leave
    untouched. See the block comment above for why a test-local bisection does not contradict
    D-12's one-choke-point rule.

    WHY AN EXACT FLOAT PIN WOULD BE **WRONG** RATHER THAN MERELY STRICT. The pin's epsilons were
    bisected against the quadrature oracle at 60 decimal places; this bisects the same oracle in
    float64, and two float64 quadratures of different integrals differ at ~1e-14 by construction.
    Measured here, worst case 5.749506e-15 across the seven rows. ``GOLDEN_EPSILON_REL_TOL = 1e-12``
    is ~174x of margin over that and ~1000x TIGHTER than the ceiling the negative control pins, so
    it is loose enough to accept correct code and tight enough to refuse a moved accountant. An
    ``==`` here would pin the pin to one of the two mathematics and redden on correct code.

    delta is strictly DECREASING in eps at fixed mu, so the bracket invariant is
    ``delta(lo) > target >= delta(hi)`` and the returned ``hi`` is the infimum ``REQUIRED_FORM``
    names. A ``delta_quadrature`` refusal is deliberately NOT caught: measured over the 356 oracle
    calls this test makes, the largest ``z = eps/mu - mu/2`` probed is **7.5000** (at eps = 8.0,
    mu = 1.0), against the committed ``ZERO_BOUNDARIES["delta_quadrature_zero_z"] = 38.372164249``
    at which the oracle refuses. The walk therefore never reaches one, and a refusal here would
    mean the bracket had left the representable region and the derivation is not valid -- a loud
    error is the correct outcome, not a substituted ordering fact.
    """
    target_delta = mitigation_unit.DELTA
    rel_tol = mitigation_accountant.GOLDEN_EPSILON_REL_TOL
    rows = mitigation_accountant.GOLDEN_EPSILON

    # META-GUARD 1: a truncated pin cannot make the loop vacuous. Seven is the count the oracle
    # derivation covers; six would silently drop a row and still "pass every row".
    assert len(rows) == 7, (
        f"GOLDEN_EPSILON carries {len(rows)} rows, not the seven the pin's own provenance and its "
        f"module-scope shape guard both name: {rows}. A truncated table makes this loop green over "
        "fewer epsilons than the pin claims to constrain"
    )

    # META-GUARD 2: "derived from the oracle" made STRUCTURAL. Walks this function's own AST and
    # asserts the called-name set contains delta_quadrature and excludes the implementation's two
    # other routes. This is the assertion that reddens if a future edit calls epsilon_for here.
    own_tree = ast.parse(_THIS_FILE.read_text(encoding="utf-8"))
    own_def = next(
        (
            node
            for node in ast.walk(own_tree)
            if isinstance(node, ast.FunctionDef) and node.name == "test_golden_epsilon_from_oracle"
        ),
        None,
    )
    assert own_def is not None, (
        "test_golden_epsilon_from_oracle was not found in this file's own AST -- the meta-guard "
        "would then be green over an empty walk, which is the failure it exists to prevent"
    )
    own_callees = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in ast.walk(own_def)
        if isinstance(node, ast.Call)
    }
    assert "delta_quadrature" in own_callees, (
        f"this test's own body calls {sorted(name for name in own_callees if name)} and NOT "
        "delta_quadrature -- V-06's whole claim is a re-derivation through the oracle, so a body "
        "that never calls it proves nothing regardless of which asserts pass"
    )
    assert not (own_callees & _V06_FORBIDDEN_CALLEES), (
        f"this test's own body calls {sorted(own_callees & _V06_FORBIDDEN_CALLEES)}. D-13: the "
        "golden table must be re-derived by an INDEPENDENT route. A derivation that calls the "
        "implementation shares its failure modes by construction and turns the pin into a "
        "photograph of the code rather than a constraint on it"
    )

    worst = 0.0
    for sigma, steps, pinned in rows:
        mu_eff = math.sqrt(steps) / sigma

        lo, hi, doublings = 0.0, 1.0, 0
        while delta_quadrature(hi, mu_eff) > target_delta:
            lo, hi = hi, hi * 2.0
            doublings += 1
            assert doublings <= _ORACLE_BISECT_MAX_DOUBLINGS, (
                f"the upper bracket walked past eps = {hi!r} at mu_eff = {mu_eff!r} without "
                f"delta falling to {target_delta!r} -- delta is decreasing in eps, so this means "
                "the oracle is not decreasing and the derivation below would be meaningless"
            )

        halvings = 0
        while (hi - lo) > _ORACLE_BISECT_REL_WIDTH * hi and halvings < _ORACLE_BISECT_MAX_STEPS:
            mid = 0.5 * (lo + hi)
            if delta_quadrature(mid, mu_eff) <= target_delta:
                hi = mid
            else:
                lo = mid
            halvings += 1

        # META-GUARD 3: the bisection CONVERGED rather than returning its initial guess. Without
        # this, an iteration cap hit on the first pass would compare `hi = 1.0` against the pin
        # and report a real-looking deviation for a reason that has nothing to do with the pin.
        assert (hi - lo) <= _ORACLE_BISECT_REL_WIDTH * hi, (
            f"the bisection at sigma = {sigma!r}, steps = {steps} stopped after {halvings} "
            f"halvings with a bracket of relative width {(hi - lo) / hi:.3e}, wider than the "
            f"{_ORACLE_BISECT_REL_WIDTH:.0e} this derivation is compared at. Its result is not a "
            "converged epsilon and must not be read as one"
        )

        deviation = abs(hi - pinned) / pinned
        worst = max(worst, deviation)
        assert abs(hi - pinned) <= rel_tol * pinned, (
            f"the quadrature oracle re-derives sigma = {sigma!r}, steps = {steps} as {hi!r}, "
            f"against the pinned {pinned!r} -- relative deviation {deviation:.6e}, over "
            f"GOLDEN_EPSILON_REL_TOL = {rel_tol!r}. Both routes bisect at mu_eff = {mu_eff!r} and "
            "delta = mitigation_unit.DELTA, so a gap this size is a real disagreement between the "
            "pin and this oracle, not float noise"
        )

    # NON-DEGENERACY, in the other direction. Measured, every one of the seven rows deviates
    # (min 1.62e-15, worst 5.75e-15): the pin was derived at 60 decimal places and this route runs
    # in float64, so a BITWISE match on all seven would mean the pin had been regenerated from a
    # float64 route -- the photograph D-13 forbids, arriving through the oracle instead of through
    # the implementation.
    assert worst > 0.0, (
        "every pinned epsilon matched the float64 quadrature bisection BITWISE. The pin's "
        "provenance says 60-decimal-place ground truth, and two different precisions do not agree "
        "to the last bit on seven rows by chance -- check whether GOLDEN_EPSILON was regenerated "
        "from a float64 run"
    )
    assert worst <= _V06_MEASURED_ORACLE_GAP * 10.0, (
        f"the worst oracle-vs-pin deviation is {worst:.6e}, more than 10x the "
        f"{_V06_MEASURED_ORACLE_GAP:.6e} this file records as measured. That is still inside "
        "GOLDEN_EPSILON_REL_TOL, but the "
        "recorded measurement is now stale and the tolerance's stated margin is no longer the "
        "margin that exists"
    )


def test_golden_epsilon_would_catch_a_moved_accountant():
    """The negative control: ``GOLDEN_EPSILON_REL_TOL`` is neither vacuously wide nor too tight.

    Without a control, a tolerance accidentally widened to 1e-3 leaves V-06 green while
    constraining nothing at all -- the pin would still be compared, and would still agree, with an
    accountant that had moved by a part in a thousand.

    THE CONTROL PLAN 22-09 SPECIFIES CANNOT DO THAT JOB, and this is a correction rather than an
    embellishment. It says to perturb by ``10 * GOLDEN_EPSILON_REL_TOL`` relative and assert the
    comparison fails. But ``abs(p * (1 + 10*t) - p) > t * p`` reduces to ``10*t*p > t*p``, which is
    true for EVERY positive t -- so that control is green at t = 1e-12 and equally green at
    t = 1e-3. It is invariant under exactly the mutation it exists to catch.

    So the perturbation here is a FIXED relative amount, and the tolerance carries its own
    ceiling. The two assertions bracket the tolerance from both sides: it must be tight enough to
    refuse a 1e-9 move, and loose enough to accept the measured 5.749506e-15 gap between two
    float64 quadratures of different integrals.
    """
    rel_tol = mitigation_accountant.GOLDEN_EPSILON_REL_TOL
    assert 0.0 < rel_tol <= _GOLDEN_REL_TOL_CEILING, (
        f"GOLDEN_EPSILON_REL_TOL is {rel_tol!r}, outside (0, {_GOLDEN_REL_TOL_CEILING!r}]. Above "
        "that ceiling V-06 stops constraining the accountant: the fixed perturbation below is "
        f"{_V06_PERTURBATION!r} relative, and a tolerance at or past it would accept a moved "
        "accountant as agreement"
    )

    sigma, steps, pinned = mitigation_accountant.GOLDEN_EPSILON[0]
    moved = pinned * (1.0 + _V06_PERTURBATION)
    assert abs(moved - pinned) > rel_tol * pinned, (
        f"an accountant returning {moved!r} for sigma = {sigma!r}, steps = {steps} -- a relative "
        f"move of {_V06_PERTURBATION!r} off the pinned {pinned!r} -- would PASS the comparison "
        f"V-06 performs at GOLDEN_EPSILON_REL_TOL = {rel_tol!r}. The pin is then decorative"
    )

    # The other side, so the tolerance is not merely 'not too wide': it must still accept the
    # honest float64-vs-60-dps gap, or V-06 reddens on correct code.
    assert _V06_MEASURED_ORACLE_GAP <= rel_tol, (
        f"GOLDEN_EPSILON_REL_TOL = {rel_tol!r} is below the measured "
        f"{_V06_MEASURED_ORACLE_GAP:.6e} gap between the pin's 60-dps derivation and this file's "
        "float64 one. A tolerance under the construction gap reddens on a correct accountant"
    )
