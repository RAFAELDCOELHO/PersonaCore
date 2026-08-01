"""VIZ-01 / VIZ-04 figure-generation contracts for ``scripts/plot_phase13.py``.

CPU-only, GPU/MPS-free, no torch. Pins two things:
  1. ``test_frontier_has_six_points`` — the Pitfall-1 regression. ``results/ft_lr_9e-5.csv``
     (the λ=0 sweep arm) has NO ``retention_ppl`` column, so a naive CSV-only read yields
     FIVE points and silently drops the collapse baseline the whole frontier is measured
     against. The λ=0 point must come from the hardcoded-with-citation constant.
  2. ``test_plot_functions_write_pngs`` — tmp_path smoke: both figures render headless and
     land as non-empty files in the requested output dir (never clobbering ``results/``).

Scripts-load justification: same as ``tests/test_phase13_driver.py`` — the plotting rules
(which CSV, which constant, which baseline) belong in the committed script, so the test
``importlib``-loads it rather than duplicating them in the package. ``main()`` is
``__main__``-guarded, so the load renders nothing.
"""

import importlib.util
import pathlib

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load_plots():
    spec = importlib.util.spec_from_file_location(
        "plot_phase13", _REPO_ROOT / "scripts" / "plot_phase13.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp = _load_plots()


def test_frontier_has_six_points():
    """VIZ-04 spans SIX λ values — the five sweep CSVs PLUS the CSV-less λ=0 baseline."""
    points = pp.build_frontier_points()
    assert len(points) == 6

    labels = [label for label, _dialog, _retention in points]
    assert labels == ["λ=0", "λ=0.01", "λ=0.1", "λ=1", "λ=10", "λ=100"]

    # λ=0 is the hardcoded-with-citation point (Pitfall 1), not a CSV read.
    zero = points[0]
    assert (zero[1], zero[2]) == (4.4453, 5.9553)
    assert pp.LAMBDA0_POINT == {"dialog_ppl": 4.4453, "retention_ppl": 5.9553}

    # Verified sweep endpoints (final rows of results/ft_lam_*.csv), (dialog, retention).
    assert points[1][1:] == (4.7297648435089465, 3.781300975354022)
    assert points[5][1:] == (16.211242472545788, 2.108236650427832)


def test_baseline_is_the_headline_not_the_curve_anchor():
    """Pitfall 3: the dashed VIZ-01 baseline is the v1.0 headline 2.1066 (full-val,
    unmasked) — NEVER the 2.107553076833866 sub-bin anchor the step-0 CSV rows carry."""
    assert pp.HEADLINE_RETENTION == 2.1066


def test_plot_functions_write_pngs(tmp_path):
    """Both figures render headless into an arbitrary out_dir as non-empty PNGs."""
    curve = pp.plot_forgetting_curve(tmp_path)
    frontier = pp.plot_frontier(tmp_path)

    assert curve == tmp_path / "phase13_forgetting_curve.png"
    assert frontier == tmp_path / "phase13_frontier.png"
    for path in (curve, frontier):
        assert path.exists()
        assert path.stat().st_size > 0
