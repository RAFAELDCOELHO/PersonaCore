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
checkpoint is W0 for which block, which 36 keys, which aggregate) belong in the committed script,
so the reproduction test ``importlib``-loads it rather than duplicating them. The load happens
INSIDE the gated test, so no torch import reaches a CI collection.
"""

import importlib.util
import json
import math
import pathlib
import re

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NORMS_JSON = _REPO_ROOT / "results" / "phase15_norms.json"
EXTRACT_SCRIPT = _REPO_ROOT / "scripts" / "extract_deltas.py"

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
