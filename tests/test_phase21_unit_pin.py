"""The frozen privacy-unit pin's guards, sampled at BOTH capacities this milestone runs.

``scripts/mitigation_unit.py`` proves its own invariants at import via five module-level ``_prove``
calls, so a wrong edit aborts before any consumer runs. This file is the SECOND tier, and the two
tiers are not redundant:

  * the module-level guards fail at IMPORT, which is what protects a consumer that never thought to
    check;
  * these tests fail at COLLECTION with a message naming this module and this decision, which is
    what tells a reader WHICH pinned number moved and what it was pinned against.

A module-level ``SystemExit`` inside ``scripts/`` would otherwise surface in CI as an import error
on whichever unrelated test file imported it first.

Every number here is sampled at **n = 8 AND n = 64**. A single-N check could only ever say "the
rejected recipe is wrong at the small capacity", which leaves open the reading that the large arm
rescues it. Both rows together say it is wrong at both capacities the milestone runs — a strictly
stronger record, and the one UNIT-05 actually needs.

CPU-only, GPU-free, no torch, no network.
"""

import ast
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_unit  # noqa: E402  (needs the sys.path insert above)

_PIN_PATH = _ROOT / "scripts" / "mitigation_unit.py"

# THE TWO CAPACITIES, and the arithmetic measured at each. Written as one table shared by every
# parametrized guard below so the n = 64 row cannot be dropped from one check while surviving in
# another — which is exactly how a "both capacities" claim decays into a single-N one.
#
# (n, delta*n for the PINNED literal, delta*n for the REJECTED recipe, that value / the ceiling)
_CAPACITIES = (
    (8, 8e-05, 0.8122523963562354, 81.2),
    (64, 0.00064, 0.6597539553864469, 66.0),
)

# WHY `approx` AND NOT `==` ON THE REJECTED PRODUCTS. `n ** -1.1` is a non-integer power, so it
# routes through the platform's libm `pow`, which is NOT guaranteed bit-identical across CPU
# families. This repository has already been bitten by exactly this class: commit `4554c93`
# ("inv_cdf not bit-reproducible across CPU/libm, arm64 Darwin vs x86_64 Linux CI") is a fix for
# the same failure, and CI runs x86_64 Linux while development runs arm64 Darwin.
#
# `1e-12` is roughly four orders of magnitude looser than the ~1-ulp (~1e-16 relative) disagreement
# a libm difference can produce, and still fourteen orders TIGHTER than the effect being asserted —
# the recipe misses its ceiling by 66x-81x. So the tolerance cannot mask the finding. The
# INEQUALITIES below are left exact for the same reason: with 66x of margin they need no slack.
_LIBM_REL = 1e-12


@pytest.mark.parametrize("n, pinned_product, rejected_product, ratio", _CAPACITIES)
def test_prove_guards_pinned_delta_clears_the_ceiling(n, pinned_product, rejected_product, ratio):
    """UNIT-05: the pinned literal `1e-5` satisfies `delta * N < 0.01` at n = 8 and n = 64."""
    assert mitigation_unit.DELTA == 1e-5
    assert mitigation_unit.DELTA_TIMES_N_CEILING == 0.01
    assert mitigation_unit.DELTA * n == pytest.approx(pinned_product, rel=_LIBM_REL)
    assert mitigation_unit.DELTA * n < mitigation_unit.DELTA_TIMES_N_CEILING, (
        f"the pinned delta {mitigation_unit.DELTA} gives delta * {n} = "
        f"{mitigation_unit.DELTA * n}, which does not clear the "
        f"{mitigation_unit.DELTA_TIMES_N_CEILING} ceiling"
    )


@pytest.mark.parametrize("n, pinned_product, rejected_product, ratio", _CAPACITIES)
def test_prove_guards_rejected_recipe_fails_its_own_ceiling(
    n, pinned_product, rejected_product, ratio
):
    """UNIT-05: `1/N**1.1` FAILS `delta * N < 0.01` — asserted, not described, at BOTH capacities.

    A rejected alternative recorded only in prose is a claim. Recorded as a runnable assertion it
    is a claim anyone can re-run at any N, which is why `rejected_delta` ships as executable code
    inside the frozen module rather than as a number in its docstring.
    """
    product = mitigation_unit.rejected_delta(n) * n
    assert product == pytest.approx(rejected_product, rel=_LIBM_REL)
    assert product >= mitigation_unit.DELTA_TIMES_N_CEILING, (
        f"{mitigation_unit.REJECTED_DELTA_RECIPE} at N = {n} gives delta * N = {product}, which "
        f"CLEARS the {mitigation_unit.DELTA_TIMES_N_CEILING} ceiling. If that is now true, the "
        "recorded reason for rejecting the recipe has stopped being true and UNIT-05 is stale"
    )


@pytest.mark.parametrize("n, pinned_product, rejected_product, ratio", _CAPACITIES)
def test_prove_guards_rejected_ratio_to_ceiling(n, pinned_product, rejected_product, ratio):
    """The MAGNITUDE of the failure, not merely its direction: 81.2x at n = 8, 66.0x at n = 64.

    `rel=1e-2` because the two published figures are quoted to three significant digits (D-23), so
    the assertion is against what the record SAYS rather than against a longer float the record
    does not contain.
    """
    product = mitigation_unit.rejected_delta(n) * n
    assert product / mitigation_unit.DELTA_TIMES_N_CEILING == pytest.approx(ratio, rel=1e-2)


def test_pinned_delta_and_the_rejected_recipe_cannot_both_be_green():
    """NON-VACUITY: the two families of assertion above are mutually exclusive by construction.

    Without this, a future edit setting `DELTA = rejected_delta(N)` would make the pinned-literal
    tests and the rejected-recipe tests describe the SAME number, and both families could go green
    while the record they encode had collapsed into one claim. Three orders of magnitude is the
    smallest separation that cannot be reached by a rounding change; the measured gap is far wider
    (1e-5 against 0.1015 at n = 8, a factor of ~10,153).
    """
    gap = mitigation_unit.rejected_delta(8) / mitigation_unit.DELTA
    assert gap > 1e3, (
        f"the pinned delta {mitigation_unit.DELTA} and the rejected recipe's value at N = 8 "
        f"{mitigation_unit.rejected_delta(8)} differ by only {gap}x. They must stay separated by "
        "more than three orders of magnitude, or the 'pinned literal passes / rejected recipe "
        "fails' record stops being a contrast between two different numbers"
    )


@pytest.mark.parametrize("n", (8, 64))
def test_privacy_n_is_the_fact_count_and_q_is_one(n):
    """UNIT-04 / D-07: replay sits outside N, so q = 1 and N is the fact count unmodified."""
    assert mitigation_unit.privacy_n(n) == n
    assert mitigation_unit.SAMPLING_RATE_Q == 1.0


def test_privacy_unit_is_one_taught_fact():
    """UNIT-01: the unit is a FACT, spelled exactly. The string is what downstream records quote."""
    assert mitigation_unit.PRIVACY_UNIT == "one taught fact"


def test_pin_imports_nothing():
    """D-22's ceiling, asserted DIRECTLY on this module rather than only inherited from the glob.

    `tests/test_phase20_prereg.py:522` already asserts `imported <= {"pathlib", "sys",
    "erasure_gate"}` over an `imported` set ACCUMULATED across every `scripts/mitigation_*.py`
    module (`:498`). That covers this file for free, but it covers it in a set naming all of them —
    so a ceiling widening reports "the mitigation modules import X" without saying which module,
    and a widening that stayed inside the allow-set would not report at all.

    This is the second tier: zero imports, named to this file. Zero rather than "within the
    allow-set" is the actual decision (D-22) — the ceiling permits three names and using none of
    them is what keeps `json` unreachable, which is in turn why the artifact writer lives outside
    the glob in `scripts/phase21_unit_record.py`.
    """
    tree = ast.parse(_PIN_PATH.read_text(encoding="utf-8"))
    imports = [
        ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert imports == [], (
        f"{_PIN_PATH.name} imports {imports}. D-22: joining the `scripts/mitigation_*.py` glob "
        "caps this module's import surface at {pathlib, sys, erasure_gate}, so `json` is "
        "unreachable and this module can do no I/O. The artifact writer lives OUTSIDE the glob in "
        "`scripts/phase21_unit_record.py`; anything here that needs an import belongs there"
    )
