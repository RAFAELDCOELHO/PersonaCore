"""D-33 / FRONT-03: the figure guard, RETARGETED onto ``scripts/plot_phase25.py``.

**THREE PARTS ARE PORTED; ONE CLAUSE IS AUTHORED. That distinction is recorded here rather than
left to a reader, so the retarget is never mis-recorded as pure reuse.**

PORTED VERBATIM IN STRUCTURE from ``tests/test_phase15_plots.py::
test_plotting_module_never_opens_a_checkpoint`` (D-07's conversion of a declared invariant into a
checked mechanism, which PROJECT.md records as one of three):
  (a) ``test_plotting_module_never_loads_torch`` — an AST import walk WITH PHASE 15'S META-GUARD.
      The meta-guard is the reason the original is trustworthy: a walk that silently stopped
      working would otherwise pass by finding nothing at all.
  (b) ``test_plotting_module_names_no_checkpoint_literal`` — an AST string-constant walk banning
      any ``.pt`` literal. AST and ``endswith`` rather than a substring search, for the
      ``tests/test_phase14_scoring.py:405-411`` reason: this module's docstring necessarily
      discusses checkpoints and artifacts at length precisely while explaining that it opens
      neither, and a substring check cannot tell a call from a mention.
  (c) ``test_a_fresh_interpreter_importing_the_plotter_has_no_torch`` — a subprocess probe that
      exits 1 if ``torch`` lands in ``sys.modules``. It must run out-of-process because torch is
      already imported by sibling tests by the time this file runs.

AUTHORED HERE, NOT PORTED — **Phase 15's guard has NO artifact allow-list**, only a ``.pt``
prohibition:
  (d) ``test_the_plotter_opens_only_the_frontier_artifact`` — every ``open`` / ``read_text`` /
      ``json.load`` / ``json.loads`` / ``pathlib.Path`` construction has its path operand resolved,
      and every resolvable one must be ``FRONTIER_RECORD``, the ``--outdir`` figure destination or
      the ``argparse`` default. Any other literal path fails NAMING IT AND ITS ``lineno``. A second
      read is what would break FRONT-03's single-source promise silently — the figure would still
      render, and a reader holding the artifact and a clone could no longer reproduce it.

EVERY PLANT LIVES IN ``tmp_path``. The walkers take SOURCE TEXT, not a module, exactly so a
violation can be watched failing on a scratch copy while ``scripts/`` stays byte-clean — asserted
after each plant with ``git status --porcelain scripts/``.

CPU-only, GPU-free, no torch at import. ``plot_phase25.main()`` is ``__main__``-guarded, so loading
the plotting module at import renders nothing; ``matplotlib`` selects ``Agg`` at its own import, so
nothing here can open a window.
"""

import ast
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLOT_SCRIPT = _REPO_ROOT / "scripts" / "plot_phase25.py"

# Calls whose path operand the allow-list clause resolves. `Path` is included because a second read
# is most naturally written `json.loads(pathlib.Path("...").read_text())`, where the only literal
# in the expression is the `Path` construction's argument.
_READ_CALLS = frozenset({"open", "read_text", "read_bytes", "load", "loads", "Path"})


def _load_plots():
    spec = importlib.util.spec_from_file_location("plot_phase25", PLOT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plot = _load_plots()


def _source():
    return PLOT_SCRIPT.read_text(encoding="utf-8")


def _scripts_dir_is_clean():
    """``git status --porcelain scripts/`` — the real tree stayed untouched by every plant."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "scripts/"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _plant(tmp_path, addition, *, at_end=True):
    """A scratch copy of the plotter in ``tmp_path``, one line added. NEVER into ``scripts/``."""
    source = _source()
    planted = f"{source}\n{addition}\n" if at_end else f"{addition}\n{source}"
    scratch = tmp_path / "plot_phase25.py"
    scratch.write_text(planted, encoding="utf-8")
    return scratch


# --------------------------------------------------------------------------------------------
# the three walkers, each taking SOURCE TEXT so the real module and a planted copy share one
# implementation — a guard that could only run against the real file could never be watched failing
# --------------------------------------------------------------------------------------------


def _imported_modules(source):
    tree = ast.parse(source)
    return {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }


def _string_constants(source):
    return [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _call_name(node):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _resolve_path(node):
    """The literal path an AST node names, or ``None`` when it is not resolvable statically.

    Handles the three forms this repository writes: a bare string, ``_ROOT / "a" / "b.json"`` and
    ``pathlib.Path("a/b.json")``. A variable operand resolves to ``None`` — unresolvable is not the
    same as forbidden, and the clause judges only what it can actually read.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parts = [_resolve_path(node.left), _resolve_path(node.right)]
        resolved = [part for part in parts if part]
        return "/".join(resolved) if resolved else None
    if isinstance(node, ast.Call) and _call_name(node) == "Path" and node.args:
        return _resolve_path(node.args[0])
    return None


def _read_calls(source):
    """``[(call_name, resolved_path_or_None, lineno)]`` for every read-shaped call in ``source``."""
    calls = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name not in _READ_CALLS:
            continue
        operand = node.args[0] if node.args else None
        calls.append((name, _resolve_path(operand), node.lineno))
    return calls


def _allow_list():
    """Every path the plotter may name: the artifact, the outdir default, the figure filenames."""
    artifact = plot.FRONTIER_RECORD
    return {
        str(artifact),
        str(artifact.relative_to(_REPO_ROOT)),
        artifact.name,
        str(plot.RESULTS_DIR),
        str(plot.RESULTS_DIR.relative_to(_REPO_ROOT)),
        *plot.FIGURES.values(),
    }


def _reads_outside_the_allow_list(source):
    """The authored clause's engine: ``[(path, lineno)]`` for every read of a non-allowed file.

    Two complementary sweeps. The first resolves the path operand of every read-shaped call; the
    second catches any ``.json`` literal anywhere in the module, which is the form a second
    artifact read takes even when its operand is assembled out of the walker's reach.
    ``endswith`` and never ``in``: the module's own prose names other artifacts while explaining
    that it opens none of them, and a substring check over prose is the false-RED class RPT-02
    exists to close.
    """
    allowed = _allow_list()
    offenders = [
        (path, lineno)
        for _, path, lineno in _read_calls(source)
        if path is not None and path not in allowed
    ]
    offenders += [
        (node.value, node.lineno)
        for node in _string_constants(source)
        if node.value.endswith(".json") and node.value not in allowed
    ]
    return sorted(set(offenders))


def _fresh_interpreter_probe(module_path):
    """Import ``module_path`` in a CHILD interpreter; exit 1 if ``torch`` reached ``sys.modules``.

    Out-of-process because torch is already in this process's ``sys.modules`` from sibling tests.
    """
    probe = (
        "import importlib.util, sys;"
        f"spec = importlib.util.spec_from_file_location('p25', {str(module_path)!r});"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "sys.exit(1 if 'torch' in sys.modules else 0)"
    )
    return subprocess.run(
        [sys.executable, "-c", probe],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )


# --------------------------------------------------------------------------------------------
# (a) PORTED — the import walk and its meta-guard
# --------------------------------------------------------------------------------------------


def test_plotting_module_never_loads_torch():
    """Phase 15's part (a), retargeted: no torch, no numpy, meta-guard kept."""
    imported = _imported_modules(_source())
    # Meta-guard FIRST, exactly as Phase 15 has it: a walk that silently stopped working would
    # otherwise pass this test by finding nothing at all.
    assert imported, "the AST import walk found no imports — the walk stopped working"
    assert "torch" not in imported, f"plot_phase25 imports torch — D-33 violated ({imported})"
    assert "numpy" not in imported, f"plot_phase25 imports numpy — D-33 violated ({imported})"


def test_the_torch_guard_fires_on_a_planted_import(tmp_path):
    """The ported import walk, WATCHED FAILING on a scratch copy. The plant lives in tmp_path."""
    scratch = _plant(tmp_path, "import torch  # planted violation", at_end=False)
    imported = _imported_modules(scratch.read_text(encoding="utf-8"))
    assert imported, "the meta-guard itself broke — the planted walk found nothing"
    assert "torch" in imported

    with pytest.raises(AssertionError) as excinfo:
        assert "torch" not in imported, f"plot_phase25 imports torch — D-33 violated ({imported})"
    assert "imports torch" in str(excinfo.value)
    assert _scripts_dir_is_clean() == "", "the plant escaped tmp_path and dirtied scripts/"


# --------------------------------------------------------------------------------------------
# (b) PORTED — the string-constant walk
# --------------------------------------------------------------------------------------------


def test_plotting_module_names_no_checkpoint_literal():
    """Phase 15's part (b), retargeted: no ``.pt`` literal, and no ``checkpoints/`` path."""
    constants = _string_constants(_source())
    assert constants, "the AST string-constant walk found no constants — the walk stopped working"

    serialized = [node.value for node in constants if node.value.endswith(".pt")]
    assert serialized == [], f"plot_phase25 names a checkpoint file: {serialized}"

    gitignored = [node.value for node in constants if "checkpoints/" in node.value]
    assert gitignored == [], f"plot_phase25 names a gitignored checkpoint path: {gitignored}"


def test_the_checkpoint_literal_guard_fires_on_a_planted_pt_literal(tmp_path):
    """The ported constant walk, WATCHED FAILING on a scratch copy carrying a ``.pt`` literal."""
    scratch = _plant(tmp_path, '_PLANTED = "checkpoints/persona_adapter.pt"')
    constants = _string_constants(scratch.read_text(encoding="utf-8"))
    serialized = [node.value for node in constants if node.value.endswith(".pt")]

    with pytest.raises(AssertionError) as excinfo:
        assert serialized == [], f"plot_phase25 names a checkpoint file: {serialized}"
    assert "persona_adapter.pt" in str(excinfo.value)
    assert _scripts_dir_is_clean() == "", "the plant escaped tmp_path and dirtied scripts/"


# --------------------------------------------------------------------------------------------
# (c) PORTED — the fresh-interpreter probe
# --------------------------------------------------------------------------------------------


def test_a_fresh_interpreter_importing_the_plotter_has_no_torch():
    """Phase 15's part (c), retargeted. This is the check that cannot be fooled by a helper."""
    result = _fresh_interpreter_probe(PLOT_SCRIPT)
    assert result.returncode == 0, (
        f"the plotting module transitively imports torch — D-33 violated\n{result.stderr}"
    )


def test_the_fresh_interpreter_probe_fires_on_a_planted_torch_import(tmp_path):
    """The probe, WATCHED FAILING: a scratch copy that imports torch must exit 1, not 0."""
    scratch = _plant(tmp_path, "import torch  # planted violation", at_end=False)
    result = _fresh_interpreter_probe(scratch)
    assert result.returncode == 1, (
        "the fresh-interpreter probe did not fire on a module that imports torch "
        f"(returncode={result.returncode})\n{result.stderr}"
    )
    assert _scripts_dir_is_clean() == "", "the plant escaped tmp_path and dirtied scripts/"


# --------------------------------------------------------------------------------------------
# (d) AUTHORED — the artifact allow-list. Phase 15's guard has no equivalent.
# --------------------------------------------------------------------------------------------


def test_the_plotter_opens_only_the_frontier_artifact():
    """FRONT-03: the ONLY file the plotter opens is ``results/phase25_frontier.json``."""
    source = _source()
    calls = _read_calls(source)
    # Meta-guard on the walker itself: the plotter necessarily reads its artifact, so a walk that
    # found no read-shaped call at all has stopped working rather than proved anything.
    assert calls, "the AST read-call walk found no reads — the walk stopped working"

    offenders = _reads_outside_the_allow_list(source)
    assert offenders == [], (
        f"plot_phase25 reads {offenders} — outside ALLOWED_READS {sorted(_allow_list())}. "
        "FRONT-03 promises every figure is drawn from the frontier artifact and nothing else"
    )


def test_the_allow_list_clause_fires_on_a_planted_second_read(tmp_path):
    """The AUTHORED clause, WATCHED FAILING on a scratch copy that opens a second artifact."""
    scratch = _plant(
        tmp_path,
        '_PLANTED = json.loads(pathlib.Path("results/phase23_cost.json").read_text())',
    )
    offenders = _reads_outside_the_allow_list(scratch.read_text(encoding="utf-8"))

    with pytest.raises(AssertionError) as excinfo:
        assert offenders == [], (
            f"plot_phase25 reads {offenders} — outside ALLOWED_READS {sorted(_allow_list())}. "
            "FRONT-03 promises every figure is drawn from the frontier artifact and nothing else"
        )
    message = str(excinfo.value)
    assert "results/phase23_cost.json" in message
    # The offending node's `lineno` travels with it — the repo register from
    # tests/test_phase22_dpsgd_ast.py, so a failure names WHERE rather than only WHAT.
    assert all(isinstance(lineno, int) and lineno > 0 for _, lineno in offenders)
    assert str(offenders[0][1]) in message
    assert _scripts_dir_is_clean() == "", "the plant escaped tmp_path and dirtied scripts/"


def test_the_plotters_path_matches_the_record_modules():
    """A rename in one module cannot drift from the other: the two constants are ``==``.

    ``phase25_record`` OWNS the artifact path (D-31); the plotter spells it a second time so its
    import surface stays minimal. Two spellings of one path is exactly how a writer and a reader
    diverge after a rename, so the second spelling is admissible only with this assertion beside it.
    """
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    import phase25_record

    assert plot.FRONTIER_RECORD == phase25_record.FRONTIER_RECORD, (
        plot.FRONTIER_RECORD,
        phase25_record.FRONTIER_RECORD,
    )
    assert plot.ALLOWED_READS == (phase25_record.FRONTIER_RECORD,)


# --------------------------------------------------------------------------------------------
# the guard is guarding something that WORKS, not an empty module
# --------------------------------------------------------------------------------------------


def _fixture_point(arm, axis, value, *, epsilon, numerator, denominator, k, k_source):
    """One schema-valid point record, carrying exactly the fields the four panels read."""
    record = {
        "point_key": f"{arm}_{axis}{value:.6f}".replace(".", "p"),
        "arm": arm,
        "axis": axis,
        axis: value,
        "epsilon": epsilon,
        "draws_per_question": k,
        "draws_per_question_source": k_source,
        "taught_recall": {"numerator": numerator, "denominator": denominator},
        "accounting": None if arm in plot.ADVERSARIAL_ARMS else {"sigma": value},
    }
    if arm in plot.ADVERSARIAL_ARMS:
        record["epsilon_omitted_reason"] = (
            "THE ADVERSARIAL ARM MAKES NO FORMAL CLAIM, AND `accounting: null` IS THAT STATEMENT "
            "WRITTEN DOWN RATHER THAN LEFT TO BE INFERRED FROM AN ABSENCE (D-31). The two "
            "adversarial capacities are reported side by side DESCRIPTIVELY, and the absence of a "
            "committed capacity rule for this arm is named here rather than left for a reader to "
            "trip over."
        )
    return record


def _fixture_frontier(tmp_path):
    """A minimal but schema-valid frontier artifact — never the real file, which does not exist."""
    points = {}
    for arm in plot.DP_ARMS:
        for sigma, epsilon, numerator, k, source in (
            (0.0, None, 790, 16, "mitigation_budget.CURVE_K"),
            (0.5, 519.7003, 700, 16, "mitigation_budget.CURVE_K"),
            (8.0, 8.6021, 301, 48, "mitigation_budget.FULL_FIDELITY_K"),
            (20.0, 2.9438, 42, 16, "mitigation_budget.CURVE_K"),
        ):
            record = _fixture_point(
                arm,
                "sigma",
                sigma,
                epsilon=epsilon,
                numerator=numerator,
                denominator=1008,
                k=k,
                k_source=source,
            )
            points[record["point_key"]] = record
    for arm in plot.ADVERSARIAL_ARMS:
        for ratio, numerator in ((0.0, 780), (0.5, 601), (1.0, 418), (1.9090909090909092, 209)):
            record = _fixture_point(
                arm,
                "ratio",
                ratio,
                epsilon=None,
                numerator=numerator,
                denominator=1008,
                k=16,
                k_source="mitigation_budget.CURVE_K",
            )
            points[record["point_key"]] = record

    artifact = {
        "points": points,
        "point_keys": list(points),
        # `results/phase23_never_taught.json`'s `pooled` block, in the shape the assembly carries
        # it verbatim (D-42): counts, with the rate re-derived at plot time rather than read.
        "never_taught_floor": {
            "nontarget_successes": 0,
            "nontarget_questions": 416,
            "tier": "core_held_out",
            "draws_per_question": 16,
            "seed": 1337,
        },
    }
    path = tmp_path / "phase25_frontier.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


def test_the_plotter_renders_from_a_fixture_frontier(tmp_path):
    """Both figures render headless from a fixture artifact into an arbitrary outdir."""
    frontier = _fixture_frontier(tmp_path)
    plot.main(["--frontier", str(frontier), "--outdir", str(tmp_path)])

    produced = [tmp_path / name for name in plot.FIGURES.values()]
    for path in produced:
        assert path.exists(), f"{path} was not produced"
        assert path.stat().st_size > 0, f"{path} is empty"
    # Writing into tmp_path is also the proof the render never clobbers the committed results/.
    assert len(produced) == 2


def test_a_missing_artifact_refuses_readably(tmp_path):
    """No traceback: an absent artifact is a sentence naming the plan that produces it."""
    with pytest.raises(SystemExit) as excinfo:
        plot.load_frontier(tmp_path / "absent.json")
    message = str(excinfo.value)
    assert "25-19" in message and "absent.json" in message


def test_a_truncated_artifact_fails_by_name(tmp_path):
    """A point missing its taught-recall counts fails NAMING the point, never rendering a blank."""
    frontier = json.loads(_fixture_frontier(tmp_path).read_text(encoding="utf-8"))
    victim = next(iter(frontier["points"]))
    del frontier["points"][victim]["taught_recall"]
    path = tmp_path / "truncated.json"
    path.write_text(json.dumps(frontier), encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        plot.load_frontier(path)
    assert victim in str(excinfo.value)
