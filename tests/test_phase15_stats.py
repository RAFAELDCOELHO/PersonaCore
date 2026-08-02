"""VIZ-03 / D-09..D-12 — the pre-registered Fisher/Δ correlation rule in ``phase15_stats.py``.

CPU-only, GPU/MPS-free, no torch, no checkpoint I/O, no artifact. Every fixture is synthetic and
inline; nothing here reads ``results/phase15_norms.json`` (which does not exist at the commit
these tests land in — that absence is the pre-registration proof). Pins:
  1. ``test_spearman_known_answers`` — the tie-correct transform. Prevents the exact defect in
     ``continual/fisher.py::_spearman``: ordinal ranks collapse a tie and inflate rho to ``1.0``
     where the correct answer is ``0.9486832980505139``.
  2. ``test_seeded_results_are_reproducible`` — prevents an unseeded (or seed-ignoring) resampler
     making the gate verdict depend on whatever shuffle order a given run happens to draw.
  3. ``test_ci_behavior_on_null_and_signal`` — prevents a CI that cannot distinguish independent
     data from a real monotone signal, which would make D-11's load-bearing half meaningless.
  4. ``test_gate_rule`` — prevents the D-11 gate drifting: a positive rho with a CI spanning zero
     is a MISS, the ``ci_lo == 0.0`` boundary is a FAIL, and the pre-registered literals
     (sign, seed, resample counts, n = 36, projection order) are what the module actually holds.

Scripts-load justification: the pre-registered constants and the gate MUST live in the committed
driver for git history itself to be the pre-registration proof (D-09, the ``finetune_ab.py``
register) — moving them into the package would put the experiment's rules somewhere the driver
could drift from. So this test ``importlib``-loads ``scripts/phase15_stats.py`` rather than
duplicating the rules. ``main()`` is ``__main__``-guarded and every rule is a module-level pure
function or constant, so the load runs nothing: no file read, no artifact, no resampling.
"""

import importlib.util
import pathlib

import numpy as np
import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load_stats():
    spec = importlib.util.spec_from_file_location(
        "phase15_stats", _REPO_ROOT / "scripts" / "phase15_stats.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


st = _load_stats()


def test_spearman_known_answers():
    """The four values from 15-RESEARCH.md's validation table, plus the rank transform itself."""
    # Wikipedia's canonical IQ / hours-of-TV example — an exact documented value.
    iq = [106, 86, 100, 101, 99, 103, 97, 113, 112, 110]
    tv = [7, 0, 27, 50, 28, 29, 20, 12, 6, 17]
    assert abs(st.spearman(iq, tv) - (-0.17575757575757575)) < 1e-15

    # THE tie fixture: continual/fisher.py::_spearman returns 1.0 here because its ordinal
    # double-argsort breaks the tie by input order. The tie-correct answer is 0.9486832980505139
    # (scipy: ...138, 1 ulp away). This assertion is what keeps the two implementations apart.
    assert abs(st.spearman([1, 1, 2, 3], [1, 2, 3, 4]) - 0.9486832980505139) < 1e-12

    # Pitfall 4: perfect monotone returns 0.9999999999999999, NOT exactly 1.0 — float
    # accumulation inside np.corrcoef, not a bug. Never assert `== 1.0`.
    rising = [float(i) for i in range(36)]
    # A strictly monotone but NON-linear map: rho must see the rank order, not the shape.
    curved = [float(i) ** 3 + 1.0 for i in range(36)]
    assert st.spearman(rising, curved) == pytest.approx(1.0, abs=1e-12)
    assert st.spearman(rising, [-x for x in curved]) == pytest.approx(-1.0, abs=1e-12)

    # Pin the tie transform itself, not just its downstream effect on rho.
    assert list(st._rank([1, 1, 2, 3])) == [0.5, 0.5, 2.0, 3.0]


def test_seeded_results_are_reproducible():
    """D-12: the verdict is byte-reproducible from the committed artifact, not shuffle-dependent.

    Small resample counts keep the test inside the fast-feedback budget; the seeding property
    they prove is independent of the count. The different-seed assertions are the meta-guard:
    without them this test would also pass if the functions ignored randomness entirely.
    """
    rng = np.random.default_rng(4242)
    a = rng.normal(size=st.N_CELLS)
    b = 0.6 * a + rng.normal(size=st.N_CELLS)

    assert st.permutation_p(a, b, n_perm=2000, seed=st.SEED) == st.permutation_p(
        a, b, n_perm=2000, seed=st.SEED
    )
    assert st.bootstrap_ci(a, b, n_boot=1000, seed=st.SEED) == st.bootstrap_ci(
        a, b, n_boot=1000, seed=st.SEED
    )

    assert st.permutation_p(a, b, n_perm=2000, seed=st.SEED) != st.permutation_p(
        a, b, n_perm=2000, seed=st.SEED + 1
    )
    assert st.bootstrap_ci(a, b, n_boot=1000, seed=st.SEED) != st.bootstrap_ci(
        a, b, n_boot=1000, seed=st.SEED + 1
    )


def test_ci_behavior_on_null_and_signal():
    """The behavioral proof that the load-bearing half of the D-11 gate can tell the two apart."""
    rng = np.random.default_rng(7)
    null_a = rng.normal(size=st.N_CELLS)
    null_b = rng.normal(size=st.N_CELLS)  # independent draw — no relationship to null_a.
    lo, hi, n_degenerate = st.bootstrap_ci(null_a, null_b, n_boot=2000, seed=st.SEED)
    assert lo < 0 < hi, f"independent data must give a CI spanning zero, got [{lo}, {hi}]"
    assert n_degenerate == 0

    signal_a = np.arange(st.N_CELLS, dtype=np.float64)
    signal_b = signal_a + rng.normal(size=st.N_CELLS)  # strong monotone relationship.
    lo, hi, n_degenerate = st.bootstrap_ci(signal_a, signal_b, n_boot=2000, seed=st.SEED)
    assert lo > 0, f"strong monotone data must give a CI excluding zero, got [{lo}, {hi}]"
    assert n_degenerate == 0


def test_gate_rule():
    """D-11's gate and the pre-registered literals it is defined against."""
    # The exact D-11 provenance case: positive rho, CI spans zero -> MISS.
    assert st.ewc_dodges_high_fisher(0.15, -0.1, 0.4) is False
    # Positive rho, CI excludes zero -> PASS.
    assert st.ewc_dodges_high_fisher(0.45, 0.11, 0.70) is True
    # CI excludes zero but the sign is wrong -> MISS (the sign is the falsifiable claim).
    assert st.ewc_dodges_high_fisher(-0.6, -0.9, -0.2) is False
    # The boundary is a FAIL, matching finetune_ab.py::ewc_mitigates.
    assert st.ewc_dodges_high_fisher(0.30, 0.0, 0.55) is False

    # The pre-registered literals — the test_preregistration_constants register.
    assert st.PREDICTED_SIGN == 1
    assert st.SEED == 1337
    assert st.N_PERM == 100_000
    assert st.N_BOOT == 10_000
    assert st.N_CELLS == 36
    assert st.PROJECTIONS == ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")
