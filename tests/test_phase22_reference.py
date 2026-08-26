"""Phase 22 — the reference table is populated, import-free, and mpmath never enters the suite.

Three assertions, every one of them META-GUARDED. The discipline is
``tests/test_phase15_plots.py:326``'s and ``tests/test_phase20_prereg.py:838-841``'s: a scan that
silently stopped scanning is green while checking nothing, and a table that silently emptied would
make V-01 and V-06 green over no data at all. So each test first proves it is looking at something.

This file is the live half of V-24's RPT-03 obligation, made a checked property NOW rather than
after the fact: ``mpmath`` computed the ground truth once, in the research session, and must never
become a test dependency. ``pyproject.toml`` is untouched by this phase.

CPU-only, GPU-free, no torch, no network.
"""

import ast
import pathlib
import sys

from tests.fixtures.phase22_reference import (
    DELTA_FRONTIER,
    EPSILON_GOLDEN,
    VACUOUS_AGREEMENT_ROW,
)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_FIXTURE_PATH = _ROOT / "tests" / "fixtures" / "phase22_reference.py"

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_unit  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)


def _imported_top_level(tree):
    """The FLAT top-level module names imported anywhere in ``tree``."""
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_reference_table_is_populated():
    """The ground truth is 12 delta rows + 7 epsilon rows, and it is REALLY there.

    The meta-guard discipline applied to DATA. A table that silently emptied — a bad merge, a
    truncated write, a refactor that renamed the constant — would make V-01's frontier sweep and
    V-06's golden pin iterate zero rows and report green, having compared nothing.

    The underflow assertion is HARD EQUALITY against ``VACUOUS_AGREEMENT_ROW`` rather than a
    count, because "one row is zero" is satisfied by a table where a DIFFERENT row silently went
    to zero. RESEARCH F1's finding is that exactly one frontier row is beyond float64's reach; if
    a second one ever is, the two-oracle cross-check has gone vacuous somewhere new and this must
    redden rather than shrug.
    """
    assert len(DELTA_FRONTIER) == 13, (
        f"DELTA_FRONTIER holds {len(DELTA_FRONTIER)} rows, not the 13-point frontier V-01 sweeps "
        "— a table that lost rows makes the frontier test green over less than it claims. The "
        "thirteenth is the b > 27.2 row (eps=775.7866600701457, mu=35.35533905932738), the band "
        "where the closed form silently dropped its second term and no committed row looked"
    )
    assert len(EPSILON_GOLDEN) == 7, (
        f"EPSILON_GOLDEN holds {len(EPSILON_GOLDEN)} rows, not 7 — same failure mode as above, "
        "on the pin D-13 requires be derived from the ORACLE rather than from accountant.py"
    )

    for row in DELTA_FRONTIER:
        assert len(row) == 3, f"DELTA_FRONTIER row {row} is not an (eps, mu, truth) triple"
        eps, mu, truth = row
        assert isinstance(eps, float) and isinstance(mu, float), (
            f"DELTA_FRONTIER row {row} has non-float (eps, mu) — the inputs are exact f64 inputs"
        )
        assert isinstance(truth, str), (
            f"DELTA_FRONTIER row {row} carries its truth as {type(truth).__name__}, not a decimal "
            "STRING. Row (2.0, 0.05)'s 1.24028351258e-352 is below the f64 subnormal floor, so a "
            "float literal parses to 0.0 silently and the digits are gone before any test runs"
        )
        assert float(truth) >= 0.0, f"DELTA_FRONTIER row {row} has a negative delta — impossible"

    underflowed = sorted((eps, mu) for eps, mu, truth in DELTA_FRONTIER if float(truth) == 0.0)
    assert underflowed == [VACUOUS_AGREEMENT_ROW], (
        f"the frontier rows that underflow float64 are {underflowed}, not exactly "
        f"[{VACUOUS_AGREEMENT_ROW}]. Every other row must carry a STRICTLY POSITIVE truth: a "
        "silently-zeroed row is indistinguishable from RESEARCH F1's vacuous-agreement corner, "
        "where both oracles return 0.0 and the cross-check passes on two wrong answers"
    )

    for row in EPSILON_GOLDEN:
        assert len(row) == 3, f"EPSILON_GOLDEN row {row} is not a (sigma, steps, epsilon) triple"
        sigma, steps, eps = row
        assert isinstance(sigma, float) and isinstance(steps, int), (
            f"EPSILON_GOLDEN row {row} has a non-float sigma or non-int steps"
        )
        assert isinstance(eps, float) and eps > 0.0, (
            f"EPSILON_GOLDEN row {row} has a non-positive epsilon — every pinned output is a "
            "finite positive epsilon at the frozen delta"
        )

    # The composition identity (Dong-Roth-Su Cor 3.3) as DATA, not as prose: every row whose
    # mu_eff = sqrt(T)/sigma is exactly 1.0 must carry a BIT-IDENTICAL epsilon. `steps ** 0.5` is
    # an operator, so this needs no import — mitigation_unit.py's own register for the same reason.
    unit_mu_eff = [row for row in EPSILON_GOLDEN if row[1] ** 0.5 == row[0]]
    assert len(unit_mu_eff) == 3, (
        f"expected 3 rows at mu_eff = 1.0, found {unit_mu_eff} — the golden table lost the "
        "composition identity it was chosen to carry"
    )
    assert len({eps for _, _, eps in unit_mu_eff}) == 1, (
        f"the mu_eff = 1.0 rows disagree on epsilon: {unit_mu_eff}. eps(sigma, T, delta) == "
        "eps(sigma/sqrt(T), 1, delta) is an EXACT algebraic identity, so these three literals "
        "must be equal bit for bit or the table was not derived from one oracle"
    )


def test_reference_fixture_imports_nothing():
    """The reference table is DATA — it imports nothing, so it can derive nothing.

    Asserted by AST rather than by reading the file: a ground truth that can execute is a ground
    truth that can compute its own answers, and a truth derived from the thing it judges is a
    photograph of the code rather than a constraint on it (D-13). Zero imports also discharges
    RPT-03 structurally — the fixture cannot reach mpmath even by accident.
    """
    tree = ast.parse(_FIXTURE_PATH.read_text(encoding="utf-8"))
    # Meta-guard: a file that failed to parse into anything would have an empty import set and
    # would sail through the assertion below while carrying no data at all.
    assert tree.body, (
        f"{_FIXTURE_PATH.name} parsed to an EMPTY module — an empty file has no imports and would "
        "pass this guard while holding none of the ground truth it exists to carry"
    )

    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert imports == [], (
        f"{_FIXTURE_PATH.name} imports {sorted(_imported_top_level(tree))} — the reference table "
        "must be literal data with no import surface at all (RPT-03: mpmath computed these "
        "numbers once, in the research session, and must never become a test dependency)"
    )


def test_no_phase22_test_imports_mpmath():
    """No Phase-22 test reaches mpmath — V-24's RPT-03 half, live from Wave 0.

    Two properties in one test, deliberately, because they are one obligation: the numbers came
    from mpmath ONCE and were committed, so (a) nothing in this phase may import it, and (b) the
    one number in the fixture that belongs to another module — the frozen delta the REJECTED_FORM
    crossover was measured at — must be RESOLVED from that module rather than re-spelled. This
    test never writes the delta literal; it reads ``mitigation_unit.DELTA`` and asserts the
    fixture's own provenance comment agrees with it.
    """
    phase22_tests = sorted((_ROOT / "tests").glob("test_phase22_*.py"))
    # Collapsed-glob meta-guard (tests/test_phase20_prereg.py:838-841's shape): a glob that stops
    # matching makes this scan green while reading no source at all.
    assert phase22_tests, (
        "the tests/test_phase22_*.py glob collapsed to zero files — a broken glob makes this "
        "guard green while scanning nothing, which is the exact failure it exists to catch"
    )

    imported = set()
    for path in [*phase22_tests, _FIXTURE_PATH]:
        imported |= _imported_top_level(ast.parse(path.read_text(encoding="utf-8")))
    assert imported, "the AST import walk found no imports at all — the walk stopped working"
    assert "mpmath" not in imported, (
        f"a Phase-22 test imports mpmath ({sorted(imported)}). The 60-dps ground truth was "
        "computed once and COMMITTED as tests/fixtures/phase22_reference.py precisely so that "
        "mpmath never becomes a test dependency — RPT-03 keeps pyproject.toml untouched"
    )

    # --- the frozen delta, resolved rather than re-spelled -------------------------------------
    source_lines = _FIXTURE_PATH.read_text(encoding="utf-8").splitlines()
    anchors = [
        i for i, line in enumerate(source_lines) if line.startswith("REJECTED_FORM_CROSSOVER")
    ]
    assert len(anchors) == 1, (
        f"expected exactly one REJECTED_FORM_CROSSOVER assignment in {_FIXTURE_PATH.name}, found "
        f"{len(anchors)} — the provenance block below is located relative to it"
    )
    provenance = []
    index = anchors[0] - 1
    while index >= 0 and source_lines[index].lstrip().startswith("#"):
        provenance.append(source_lines[index])
        index -= 1
    assert provenance, (
        "REJECTED_FORM_CROSSOVER has no comment block above it — its provenance, including the "
        "delta it was measured at, would be unrecorded and this assertion would compare nothing"
    )
    assert repr(mitigation_unit.DELTA) in "\n".join(provenance), (
        f"REJECTED_FORM_CROSSOVER's provenance block does not state the frozen delta "
        f"{mitigation_unit.DELTA!r} pinned at scripts/mitigation_unit.py::DELTA. The crossover "
        "mu = 1.737896746 is only meaningful AT a delta; a crossover recorded without one, or "
        "against a delta that has since moved, is a number with no denominator"
    )
