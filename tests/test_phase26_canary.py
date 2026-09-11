"""CPU-only tests for the Phase-26 empirical privacy audit canary."""

import ast
import json
import pathlib
import plistlib
import shutil
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import phase25_record  # noqa: E402
import phase25_run  # noqa: E402, F401
import phase26_canary as canary  # noqa: E402
import phase26_prereg  # noqa: E402

_DRIVER = _SCRIPTS / "phase26_canary.py"
_CANARY_PLIST = _ROOT / "artifacts" / "com.personacore.phase26.canary.plist"
_RECALL_PLIST = _ROOT / "artifacts" / "com.personacore.phase25.recall.plist"
_FRONTIER = json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))
_KEYS = phase26_prereg.audited_point_keys(_FRONTIER)
_ADAPTERS_ON_DISK = (_ROOT / "checkpoints").is_dir() and all(
    (_ROOT / _FRONTIER["points"][key]["adapter_path"]).exists() for key in _KEYS
)


@pytest.fixture(scope="module")
def frontier():
    return _FRONTIER


def _convbase_path():
    import phase14_recall as pr

    return pr.CONVBASE_SLIM


def _adapters_on_disk():
    return _ADAPTERS_ON_DISK and _convbase_path().exists()


needs_adapters = pytest.mark.skipif(
    "not _adapters_on_disk()",
    reason=(
        "the 16 sweep adapters and convbase live under gitignored checkpoints/ — sweep host only"
    ),
)
needs_plutil = pytest.mark.skipif(shutil.which("plutil") is None, reason="plutil is macOS-only")


def _score_shape(prefix, n_facts, n_questions):
    questions_per_fact = n_questions // n_facts
    per_fact = {
        f"{prefix}_fact_{fact_index}": {
            "answered_questions": 0,
            "n_questions": questions_per_fact,
            "k": 0,
            "n": questions_per_fact * 9,
            "member": False,
        }
        for fact_index in range(n_facts)
    }
    per_question = [
        {
            "fact": f"{prefix}_fact_{index // questions_per_fact}",
            "family": "fixture",
            "index": index,
            "k": 0,
            "n": 9,
            "answered": False,
        }
        for index in range(n_questions)
    ]
    return {
        "per_question": per_question,
        "per_fact": per_fact,
        "k": 0,
        "n": n_questions * 9,
        "questions": n_questions,
        "questions_answered": 0,
        "draws_per_question": 9,
        "unit_rationale": "fixture",
    }


def _fake_sidecar(key, *, sha=None):
    record = canary.point_record(key)
    return {
        "point_key": key,
        "arm": record["arm"],
        "sigma": record["sigma"],
        "adapter_path": record["adapter_path"],
        "adapter_sha256": record["adapter_sha256"] if sha is None else sha,
        "epsilon_upper": record["epsilon"],
        "delta": record["delta"],
        "in_taught": _score_shape("in_taught", 8, 112),
        "in_heldout": _score_shape("in_heldout", 8, 72),
        "out_taught": _score_shape("out_taught", 56, 784),
        "out_heldout": _score_shape("out_heldout", 56, 504),
        "scoring_seconds": 0.0,
        "instrument": canary.INSTRUMENT,
        "instrument_git_sha": "fixture",
        "device": "fixture",
        "torch_version": "fixture",
        "utc": "fixture",
    }


def _fake_off_sidecar(*, base_sha):
    base = _convbase_path()
    return {
        "arm": "off",
        "base_path": str(base.relative_to(_ROOT)),
        "base_sha256": base_sha,
        "host_point_key": phase26_prereg.CONTROL_KEY,
        "host_adapter_sha256": _FRONTIER["points"][phase26_prereg.CONTROL_KEY]["adapter_sha256"],
        "in_taught": _score_shape("in_taught", 8, 112),
        "in_heldout": _score_shape("in_heldout", 8, 72),
        "out_taught": _score_shape("out_taught", 56, 784),
        "out_heldout": _score_shape("out_heldout", 56, 504),
        "scoring_seconds": 0.0,
        "instrument": canary.INSTRUMENT,
        "instrument_git_sha": "fixture",
        "device": "fixture",
        "torch_version": "fixture",
        "utc": "fixture",
    }


def _plist(path):
    with path.open("rb") as handle:
        return plistlib.load(handle)


def _enclosing_function(tree, node):
    best = None
    for candidate in ast.walk(tree):
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if candidate.lineno <= node.lineno <= candidate.end_lineno:
            if best is None or candidate.lineno > best.lineno:
                best = candidate
    return best.name if best is not None else "<module>"


def _git_argv_subcommands(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            continue
        first = node.elts[0]
        if not (isinstance(first, ast.Constant) and first.value == "git"):
            continue
        for element in node.elts[1:]:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                found.append((element.value, element.lineno, _enclosing_function(tree, element)))
                break
    return found


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


def test_in_items_equal_calibration_items_exactly(frontier):
    import phase14_factset as fs
    import teach_persona as tp

    assert canary._items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS) == tp.calibration_items(
        fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS
    )
    assert canary._items(fs.LOCKED_FACTS, fs.HELDOUT_FAMILY_IDS) == tp.calibration_items(
        fs.LOCKED_FACTS, fs.HELDOUT_FAMILY_IDS
    )
    assert len(canary._items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)) == 112
    assert len(canary._items(fs.LOCKED_FACTS, fs.HELDOUT_FAMILY_IDS)) == 72
    assert frontier["point_keys"]


def test_out_items_render_through_the_filler_grammar():
    import phase14_factset as fs
    import phase14_recall as pr
    import phase21_filler as pf

    in_items = canary._items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)
    heldout_in_items = canary._items(fs.LOCKED_FACTS, fs.HELDOUT_FAMILY_IDS)
    out_items = canary._items(pf.FILLER_FACTS, fs.TAUGHT_FAMILY_IDS, forms=pf.FILLER_SLOT_FORMS)
    heldout_out_items = canary._items(
        pf.FILLER_FACTS, fs.HELDOUT_FAMILY_IDS, forms=pf.FILLER_SLOT_FORMS
    )
    assert len(out_items) == 784
    assert len(heldout_out_items) == 504
    assert all(item[1].tier == "filler" for item in out_items + heldout_out_items)
    assert all(
        not pr.contains_value(question, in_fact.value)
        for _family, _fact, question in out_items + heldout_out_items
        for in_fact in fs.LOCKED_FACTS
    )
    assert all(
        not pr.contains_value(question, out_fact.value)
        for _family, _fact, question in in_items + heldout_in_items
        for out_fact in pf.FILLER_FACTS
    )


def test_the_driver_imports_no_torch_touching_module_at_top_level():
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    top_level = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    } | {node.module for node in tree.body if isinstance(node, ast.ImportFrom) and node.module}
    assert not top_level & {
        "torch",
        "teach_persona",
        "phase14_factset",
        "phase14_recall",
        "phase21_filler",
        "phase18_extraction",
    }


def test_the_driver_never_calls_torch_load_directly():
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "load"
        and isinstance(node.value, ast.Name)
        and node.value.id == "torch"
    ]
    assert calls == []


@needs_adapters
def test_the_dry_run_walks_off_and_sixteen_and_never_imports_torch():
    script = (
        "import pathlib, sys, tempfile\n"
        f"sys.path.insert(0, {str(_SCRIPTS)!r})\n"
        "import phase26_canary as canary\n"
        "canary.SIDECAR_DIR = pathlib.Path(tempfile.mkdtemp())\n"
        "canary.main(['--dry-run'])\n"
        "assert 'torch' not in sys.modules\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=_ROOT, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    dry_run_lines = [line for line in completed.stdout.splitlines() if "DRY RUN" in line]
    assert len(dry_run_lines) == 17
    assert dry_run_lines[0].startswith("[phase26_canary] off:")
    for line, key in zip(dry_run_lines[1:], _KEYS):
        assert key in line


@needs_adapters
def test_a_matching_sidecar_is_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    key = "dp_n8_sigma0p500000"
    canary.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")
    status, blob = canary.score_point(key, dry_run=True)
    assert status == "reused"
    assert blob["point_key"] == key

    base = _convbase_path()
    canary.off_sidecar_path().write_text(
        json.dumps(_fake_off_sidecar(base_sha=canary._sha256(base))), encoding="utf-8"
    )
    status, blob = canary.score_off_once(dry_run=True)
    assert status == "reused"
    assert blob["arm"] == "off"


@needs_adapters
def test_a_sidecar_for_a_different_adapter_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    key = "dp_n8_sigma0p500000"
    canary.sidecar_path(key).write_text(
        json.dumps(_fake_sidecar(key, sha="0" * 64)), encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="REFUSED, not reused"):
        canary.score_point(key, dry_run=True)

    canary.off_sidecar_path().write_text(
        json.dumps(_fake_off_sidecar(base_sha="0" * 64)), encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="REFUSED, not reused"):
        canary.score_off_once(dry_run=True)


def test_emit_refuses_a_partial_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    empty_out = tmp_path / "empty.json"
    with pytest.raises(SystemExit, match="phase26_operational_note.md"):
        canary.emit(empty_out)
    assert not empty_out.exists()

    if not _adapters_on_disk():
        pytest.skip("the partial-sidecar sub-case needs the sweep host's convbase")
    base = _convbase_path()
    canary.off_sidecar_path().write_text(
        json.dumps(_fake_off_sidecar(base_sha=canary._sha256(base))), encoding="utf-8"
    )
    for key in _KEYS[:-1]:
        canary.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")
    partial_out = tmp_path / "partial.json"
    with pytest.raises(SystemExit) as excinfo:
        canary.emit(partial_out)
    assert _KEYS[-1] in str(excinfo.value)
    assert not partial_out.exists()


def test_emit_refuses_to_overwrite_the_committed_artifact():
    if canary.RECORD.exists():
        before = canary.RECORD.read_bytes()
        with pytest.raises(SystemExit) as excinfo:
            canary.emit()
        assert "REFUSING to overwrite" in str(excinfo.value)
        assert "--force" in str(excinfo.value)
        assert canary.RECORD.read_bytes() == before
    else:
        assert not canary.OPERATIONAL_NOTE.exists() or "## 7." not in (
            canary.OPERATIONAL_NOTE.read_text(encoding="utf-8")
        )


def test_the_driver_never_commits(tmp_path):
    assert _git_argv_subcommands(_DRIVER) == []
    planted = tmp_path / "phase26_canary_planted.py"
    planted.write_text(
        _DRIVER.read_text(encoding="utf-8") + '\n\ndef _planted():\n    return ["git", "push"]\n',
        encoding="utf-8",
    )
    found = _git_argv_subcommands(planted)
    assert len(found) == 1
    subcommand, _lineno, function = found[0]
    assert subcommand == "push"
    assert function == "_planted"


def test_the_canary_agent_mirrors_the_recall_agent():
    ours, recall = _plist(_CANARY_PLIST), _plist(_RECALL_PLIST)
    assert ours["Label"] == "com.personacore.phase26.canary"
    assert ours["KeepAlive"] is False
    assert ours["RunAtLoad"] is False
    assert ours["ProgramArguments"][:3] == recall["ProgramArguments"][:3]
    assert ours["ProgramArguments"][3].endswith("scripts/phase26_canary.py")
    beat = ours["ProgramArguments"][ours["ProgramArguments"].index("--heartbeat") + 1]
    recall_beat = recall["ProgramArguments"][recall["ProgramArguments"].index("--heartbeat") + 1]
    assert beat == recall_beat
    assert ours["WorkingDirectory"] == recall["WorkingDirectory"]
    assert ours["StandardOutPath"] != recall["StandardOutPath"]
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"


@needs_plutil
def test_the_canary_agent_plist_lints():
    assert (
        subprocess.run(["plutil", "-lint", str(_CANARY_PLIST)], capture_output=True).returncode == 0
    )


def test_sidecar_paths_refuse_a_path_separator():
    with pytest.raises(SystemExit):
        canary.sidecar_path("../x")
    with pytest.raises(SystemExit):
        canary.point_record("dp_n8_sigma0p5")
