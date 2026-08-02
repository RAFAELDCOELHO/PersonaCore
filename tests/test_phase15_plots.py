"""VIZ-02 / VIZ-03 / D-05 / D-06 / D-07 / D-08 contracts for the Phase-15 norms artifact.

CPU-only, GPU/MPS-free, no torch at import. Pins:
  1. ``test_artifact_schema`` — the committed ``results/phase15_norms.json`` carries four blocks
     x 36 cells with the D-06 confound fields on EVERY block (fisher included), a
     machine-readable ``comparison_basis``, the SC3 Fisher estimator ``variant``, and a
     ``vmax_driver`` that actually equals its block's maximum. Prevents a downstream figure or
     report quoting a driver cell the data does not support (D-02 / D-18), and prevents the
     fisher block being quietly exempted from the non-comparability disclosure.
  2. ``test_extraction_reproduces_the_committed_artifact`` — ``skipif``-gated on the six
     gitignored checkpoints. Re-runs extraction into ``tmp_path`` and compares the result to the
     committed file. Prevents a committed artifact that no longer corresponds to what the
     extraction script produces.
  3. ``test_plot_functions_write_pngs`` — VIZ-02 / VIZ-03 tmp_path smoke: both figures render
     headless and land as non-empty files in the requested output dir (never clobbering
     ``results/``).
  4. ``test_ab_panels_share_one_norm`` — D-01, by object IDENTITY through ``_norms``, not by
     equal bounds. The naive and EWC panels take ONE ``LogNorm``; the Fisher panel's differs, on
     the stated units argument.
  5. ``test_shared_range_is_full_data_range`` — D-02. The shared bounds are the exact data
     extrema across BOTH arms, which a percentile-clipped implementation cannot satisfy.
  6. ``test_vmax_driver_matches_argmax`` — D-02 / D-18. Every block's recorded ``vmax_driver``
     names the cell that really is the maximum OF THE GRID THE FIGURE DRAWS, so the caption and
     the report point at the same coordinate the reader sees.
  7. ``test_plotting_module_never_opens_a_checkpoint`` — D-07, structurally: an AST walk plus a
     fresh-interpreter subprocess import.

**D-08 — why extraction is NOT permanently tested.** Extraction needs six gitignored checkpoints
(~914 MB) and cannot run in the CPU-only CI suite; the permanent suite covers the
artifact->figure path only. Re-running extraction against a FUTURE checkpoint requires
a fresh manual run producing a fresh committed artifact — NOT a test that silently stays green
while checking nothing. Test 2 above therefore SKIPS in CI and runs only on a machine that
happens to hold the checkpoints.

**What this suite CANNOT prove:** that the committed numbers describe the INTENDED checkpoints.
Nothing here can distinguish a correct extraction from one run against a different (but
self-consistent) set of weights. The ``git_sha`` / ``step`` / ``val_loss`` fingerprints recorded
in each block are the audit trail that closes that gap — for a human reader, not for this file.

Scripts-load justification: same as ``tests/test_phase13_plots.py`` — the extraction rules (which
checkpoint is W0 for which block, which 36 keys, which aggregate) and the plotting rules (which
artifact field, which norm, which disclosure) belong in the committed scripts, so the tests
``importlib``-load them rather than duplicating them in the package. ``plot_phase15.main()`` is
``__main__``-guarded, so loading the plotting module at import renders nothing. The EXTRACTION
module's load happens INSIDE the gated test, so no torch import reaches a CI collection.
"""

import ast
import importlib.util
import json
import math
import pathlib
import re
import subprocess
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NORMS_JSON = _REPO_ROOT / "results" / "phase15_norms.json"
EXTRACT_SCRIPT = _REPO_ROOT / "scripts" / "extract_deltas.py"
PLOT_SCRIPT = _REPO_ROOT / "scripts" / "plot_phase15.py"

PROJECTIONS = ["q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out"]
BLOCKS = ("adapter", "ewc", "fisher", "naive")
FISHER_VARIANT = "empirical_diag_fisher/groundtruth_targets/mean_normalized"

# local-only: extraction reads these six checkpoints and `checkpoints/` is gitignored
# (.gitignore), so the reproduction test below can never run in CI — the multi-artifact
# skipif form from tests/test_phase14_demo.py:128-133.
_REQUIRED_CKPTS = (
    "persona_adapter.pt",
    "convbase_best.pt",
    "best.pt",
    "phase13_naive_latest.pt",
    "phase13_ewc_latest.pt",
    "fisher_tinystories.pt",
)
_HAVE_CKPTS = all((_REPO_ROOT / "checkpoints" / name).exists() for name in _REQUIRED_CKPTS)


def _artifact():
    return json.loads(NORMS_JSON.read_text(encoding="utf-8"))


def _load_plots():
    spec = importlib.util.spec_from_file_location("plot_phase15", PLOT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plot = _load_plots()


def _flat(grid):
    return [float(v) for row in grid.tolist() for v in row]


def test_artifact_schema():
    """The committed D-05 artifact carries everything D-06 and SC3 require, and correctly."""
    artifact = _artifact()
    # Meta-guard (the tests/test_phase14_scoring.py:423-424 habit): a truncated or renamed file
    # must fail LOUDLY here rather than let every assertion below pass vacuously.
    assert isinstance(artifact, dict) and artifact, f"{NORMS_JSON} did not parse to a dict"
    assert "blocks" in artifact, f"{NORMS_JSON} has no 'blocks' object — not a D-05 artifact"

    assert artifact["git_sha"] and artifact["built"]
    assert artifact["n_layer"] == 6
    assert artifact["projections"] == PROJECTIONS
    assert artifact["quantity"]
    assert artifact["fisher_aggregate"]

    basis = artifact["comparison_basis"]
    assert basis["naive_vs_ewc"] is True
    assert basis["adapter_vs_full_finetune"] is False
    # D-06's non-comparability statement must live in the DATA, naming D-03's actual confounds
    # (parameter count, training budget) rather than gesturing at "different regimes".
    assert isinstance(basis["note"], str) and basis["note"]
    assert "331776" in basis["note"]
    assert "training budget" in basis["note"]

    assert tuple(sorted(artifact["blocks"])) == BLOCKS

    for name, block in artifact["blocks"].items():
        # EVERY block, fisher included — asserted in a loop so fisher cannot be exempted (D-06).
        assert block["regime"], f"block {name!r} has an empty regime"
        assert isinstance(block["param_count"], int) and block["param_count"] > 0, name
        assert isinstance(block["training_budget"], str) and block["training_budget"], name

        cells = block["cells"]
        assert sorted(cells) == [str(layer) for layer in range(6)], name
        grid = []
        for layer in range(6):
            row = cells[str(layer)]
            assert sorted(row) == sorted(PROJECTIONS), f"block {name!r} layer {layer}"
            values = [float(row[projection]) for projection in PROJECTIONS]
            assert all(math.isfinite(v) for v in values), f"block {name!r} layer {layer}"
            grid.append(values)
        assert sum(len(row) for row in cells.values()) == 36, name

        flat = [v for row in grid for v in row]
        driver = block["vmax_driver"]
        assert driver["layer"] in range(6), name
        assert driver["projection"] in PROJECTIONS, name
        # The D-02/D-18 disclosure being CORRECT in the data, not merely present: the caption
        # (15-03) and the report (15-05) both read this, so a stale driver would put the same
        # wrong coordinate in two places at once.
        assert driver["value"] == pytest.approx(max(flat), abs=1e-12), name
        assert grid[driver["layer"]][PROJECTIONS.index(driver["projection"])] == pytest.approx(
            max(flat), abs=1e-12
        ), name

        # LogNorm(0.0) returns `masked` and does NOT raise, so a zero cell would silently vanish
        # from the figure — the report states this count from the data, not from the picture.
        assert isinstance(block["nonpositive_cells"], int), name
        assert block["nonpositive_cells"] == sum(1 for v in flat if v <= 0.0), name

    fisher = artifact["blocks"]["fisher"]
    # ROADMAP SC3 names the Fisher variant as a required v2.0 disclosure: the coarse `regime`
    # says which family, `variant` says which estimator, from which targets, under which
    # normalization. An empty or missing variant is a SCHEMA failure, not a proofreading miss.
    assert isinstance(fisher["variant"], str) and fisher["variant"]
    assert fisher["variant"] == FISHER_VARIANT
    assert isinstance(fisher["n_examples"], int)
    assert isinstance(fisher["seed"], int)


# Extraction runs ONLY here; the import of the torch-importing script is deliberately inside the
# gated test so a CI collection never touches torch.
_TOP_LEVEL_PROVENANCE = re.compile(r'^(  "(?:git_sha|built)": ).*$', re.M)


def _normalize_run_provenance(text):
    """Blank the TWO top-level run-provenance fields, and nothing else.

    ``git_sha`` and ``built`` at the top level record WHEN and AT WHICH COMMIT extraction ran —
    they are not something extraction COMPUTES, and they necessarily differ once HEAD moves past
    the commit that produced the committed artifact (it always does: the artifact is committed
    after the script). The two-space indent anchors this to the top level only: the checkpoint
    fingerprints nested inside each block (``base_fingerprint`` / ``fingerprint`` /
    ``anchor_fingerprint`` / ``w0_fingerprint``) sit deeper and are compared byte-for-byte, which
    is the point — they are the audit trail that says which weights the numbers describe.
    """
    return _TOP_LEVEL_PROVENANCE.sub(r"\1<run-provenance>", text)


# local-only: extraction needs the six gitignored checkpoints (~914 MB), so this cannot run in
# CPU-only CI. See the D-08 paragraph in the module docstring — re-running extraction against a
# future checkpoint is a fresh MANUAL run producing a fresh committed artifact, not this test.
@pytest.mark.skipif(not _HAVE_CKPTS, reason="gitignored checkpoints not present (CI)")
def test_extraction_reproduces_the_committed_artifact(tmp_path):
    """Re-running extraction on the frozen checkpoints reproduces the committed JSON."""
    spec = importlib.util.spec_from_file_location("extract_deltas", EXTRACT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    produced = tmp_path / "phase15_norms.json"
    module.main(produced)

    # Bytes, not parsed floats: extraction is pure tensor arithmetic on frozen weights forced
    # onto CPU (map_location="cpu"), so it is deterministic. No float tolerance is added here —
    # a first observed mismatch is information, not a reason to weaken the check.
    fresh = _normalize_run_provenance(produced.read_text(encoding="utf-8"))
    committed = _normalize_run_provenance(NORMS_JSON.read_text(encoding="utf-8"))
    assert fresh == committed


def test_plot_functions_write_pngs(tmp_path):
    """VIZ-02 and VIZ-03 render headless into an arbitrary out_dir as non-empty PNGs."""
    adapter = plot.plot_adapter_delta(tmp_path)
    triptych = plot.plot_fisher_ewc(tmp_path)

    # Writing to tmp_path is also the proof they never clobber the committed results/ copies.
    assert adapter == tmp_path / "phase15_adapter_delta.png"
    assert triptych == tmp_path / "phase15_fisher_ewc.png"
    for path in (adapter, triptych):
        assert path.exists()
        assert path.stat().st_size > 0


def test_ab_panels_share_one_norm(tmp_path):
    """D-01: the naive and EWC panels take ONE norm OBJECT; the Fisher panel's is its own.

    Asserted by ``is``, never by comparing ``(vmin, vmax)``. An implementation that built one
    norm per panel and happened to compute matching bounds would satisfy a value comparison
    while quietly defeating the same-instance contract — and that implementation is exactly the
    one a later "just brighten this panel" edit turns into two different scales, which is the
    thing D-01 exists to prevent.
    """
    artifact = _artifact()
    naive = plot._grid(artifact, "naive")
    ewc = plot._grid(artifact, "ewc")

    shared = plot._shared_norm(naive, ewc)
    stacked = _flat(naive) + _flat(ewc)
    assert shared.vmin == pytest.approx(min(v for v in stacked if v > 0.0), abs=1e-12)
    assert shared.vmax == pytest.approx(max(stacked), abs=1e-12)

    # The units exemption is real and VISIBLE, not an accident of two blocks happening to span
    # the same decades: squared-gradient magnitude is not commensurable with a delta ratio.
    fisher = _flat(plot._grid(artifact, "fisher"))
    assert (min(v for v in fisher if v > 0.0), max(fisher)) != (shared.vmin, shared.vmax)

    naive_norm, ewc_norm, fisher_norm = plot._norms(artifact)
    assert naive_norm is ewc_norm
    assert fisher_norm is not naive_norm

    # ...and the helper cannot drift from what is drawn: the figure that consumes these three
    # norms must still render with them.
    assert plot.plot_fisher_ewc(tmp_path).exists()


def test_shared_range_is_full_data_range():
    """D-02: the shared bounds are the EXACT extrema across both arms — nothing clipped.

    ``vmax`` is the largest cell across both arms and ``vmin`` the smallest strictly positive
    one. A percentile-clipped implementation cannot satisfy that, and the two ``>``/``<``
    assertions below show the equalities have teeth: the true extrema sit strictly outside a
    5%/95% clip, so a clipped norm would produce measurably different numbers rather than
    coincidentally equal ones.
    """
    artifact = _artifact()
    shared = plot._shared_norm(plot._grid(artifact, "naive"), plot._grid(artifact, "ewc"))

    stacked = sorted(_flat(plot._grid(artifact, "naive")) + _flat(plot._grid(artifact, "ewc")))
    positive = [v for v in stacked if v > 0.0]
    assert shared.vmax == pytest.approx(stacked[-1], abs=1e-12)
    assert shared.vmin == pytest.approx(positive[0], abs=1e-12)

    assert shared.vmax > stacked[int(0.95 * len(stacked))]
    assert shared.vmin < positive[int(0.05 * len(positive))]


def test_vmax_driver_matches_argmax():
    """D-02 / D-18: every block's recorded driver cell IS that block's maximum, as drawn.

    The grid comes from the plotting module's own ``_grid`` — the row/column order the figure
    actually renders — so this pins the disclosure the caption and the report both read against
    the picture a reader is looking at, not against a differently-ordered re-derivation.
    """
    artifact = _artifact()
    for name in BLOCKS:
        grid = plot._grid(artifact, name)
        driver = artifact["blocks"][name]["vmax_driver"]
        cell = float(grid[driver["layer"]][PROJECTIONS.index(driver["projection"])])
        assert cell == pytest.approx(max(_flat(grid)), abs=1e-12), name
        assert driver["value"] == pytest.approx(cell, abs=1e-12), name


def test_plotting_module_never_opens_a_checkpoint():
    """D-07: the plotting module has NO code path that opens a serialized checkpoint.

    Nothing in ``scripts/plot_phase15.py`` itself prevents a future edit from adding a two-line
    checkpoint read when one artifact field turns out to be missing. Without this test "reads
    only the artifact" is a convention that edit breaks silently — and D-07's whole point is
    that the regenerability proof holds BY CONSTRUCTION: a committed PNG derived from a
    gitignored 278 MB checkpoint cannot be regenerated from a clone, so the claim would become
    false without anything turning red. This is also a security control — it is what keeps the
    plotting path provably incapable of deserializing anything.

    AST rather than substring matching, for the ``tests/test_phase14_scoring.py:405-411``
    reason: a substring check cannot tell a call from a mention in a docstring, and this
    module's docstring necessarily discusses checkpoints at length precisely while explaining
    that it never opens one.

    Two complementary checks. (a) is the readable statement of intent; (b) is the one that
    cannot be fooled — it catches a transitive import through a helper module (a) cannot see,
    and it must run out-of-process because torch is already in ``sys.modules`` from sibling
    tests by the time this runs.
    """
    tree = ast.parse(PLOT_SCRIPT.read_text(encoding="utf-8"))

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
    # Meta-guard first (the tests/test_phase14_scoring.py:441 habit): a walk that silently
    # stopped working would otherwise pass this test by finding nothing at all.
    assert imported, "the AST import walk found no imports — the walk stopped working"
    assert "torch" not in imported, f"plot_phase15 imports torch — D-07 violated ({imported})"

    serialized = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.endswith(".pt")
    ]
    assert serialized == [], f"plot_phase15 names a checkpoint file: {serialized}"

    probe = (
        "import importlib.util, sys;"
        "spec = importlib.util.spec_from_file_location('p15', 'scripts/plot_phase15.py');"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "sys.exit(1 if 'torch' in sys.modules else 0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"plotting module transitively imports torch — D-07 violated\n{result.stderr}"
    )
