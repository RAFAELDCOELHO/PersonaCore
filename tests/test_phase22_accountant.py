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

import math
import pathlib

import pytest
from tests.fixtures.phase22_reference import DELTA_FRONTIER, VACUOUS_AGREEMENT_ROW

from personacore.privacy.accountant import delta_closed

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_ACCOUNTANT_PATH = _ROOT / "src" / "personacore" / "privacy" / "accountant.py"

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
