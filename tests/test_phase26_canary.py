"""CPU-only tests for the Phase-26 empirical privacy audit canary."""

import ast
import copy
import hashlib
import json
import pathlib
import plistlib
import re
import shutil
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import _prose  # noqa: E402
import phase25_prereg  # noqa: E402
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


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """``emit()`` refuses a dirty tree (26-REVIEW WR-03). This suite runs on dirty trees all day,
    so the guard is RECORDED here, never exercised; the real refusal is tested where it lives
    (``tests/test_phase21_unit_record.py``). Returns the calls so one test can prove the wiring."""
    calls = []
    monkeypatch.setattr(canary, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


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


def _fake_off_sidecar(*, base_sha, base_path=None):
    if base_path is None:
        base_path = str(_convbase_path().relative_to(_ROOT))
    return {
        "arm": "off",
        "base_path": base_path,
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


def _complete_fake_audit(tmp_path, monkeypatch):
    """OFF + all 16 point sidecars under ``tmp_path`` over a fixture base file, so ``emit()`` runs
    on any host: no checkpoint is read (the base is pinned by hash, wherever it is)."""
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    base = tmp_path / "base.pt"
    base.write_bytes(b"fixture base")
    canary.off_sidecar_path().write_text(
        json.dumps(_fake_off_sidecar(base_sha=canary._sha256(base), base_path=str(base))),
        encoding="utf-8",
    )
    for key in _KEYS:
        canary.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")


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


def test_emit_refuses_a_dirty_tree_before_reading_any_sidecar(tmp_path, monkeypatch, clean_tree):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    inside = _ROOT / "results" / "phase26_canary_probe_never_written.json"
    with pytest.raises(SystemExit, match="phase26_operational_note.md"):
        canary.emit(inside)
    assert not inside.exists()
    (call,) = clean_tree
    assert call["who"] == "phase26_canary"
    assert call["cwd"] == _ROOT
    assert call["pathspec"] == (
        "scripts",
        "src",
        "results",
        ":(exclude)results/phase26_canary_probe_never_written.json",
    )

    def refuse(**kw):
        raise SystemExit("[probe] REFUSING: the working tree is dirty")

    monkeypatch.setattr(canary, "refuse_if_dirty", refuse)
    with pytest.raises(SystemExit, match="dirty"):
        canary.emit(tmp_path / "canary.json")


def test_emit_refuses_to_overwrite_the_committed_artifact():
    if canary.RECORD.exists():
        before = canary.RECORD.read_bytes()
        with pytest.raises(SystemExit) as excinfo:
            canary.emit()
        assert "REFUSING to overwrite" in str(excinfo.value)
        assert "--force" in str(excinfo.value)
        assert canary.RECORD.read_bytes() == before
    else:
        pass


def test_pin_sources_hashes_every_sidecar_and_refuses_one_that_does_not_re_derive(
    tmp_path, monkeypatch
):
    _complete_fake_audit(tmp_path, monkeypatch)
    record = tmp_path / "canary.json"
    emitted = canary.emit(record)
    assert emitted["off_sidecar_sha256"] == canary._sha256(canary.off_sidecar_path())
    assert set(emitted["off_sidecar_provenance"]) == set(canary._SOURCE_PROVENANCE_KEYS)
    for key in _KEYS:
        assert emitted["points"][key]["source_sha256"] == canary._sha256(canary.sidecar_path(key))
        assert emitted["points"][key]["source_provenance"]["instrument_git_sha"] == "fixture"

    sources = tmp_path / "sources.json"
    pinned = canary.pin_sources(sources, record_path=record)
    assert json.loads(sources.read_text(encoding="utf-8")) == pinned
    assert pinned["artifact_sha256"] == canary._sha256(record)
    assert pinned["off_sidecar"]["sha256"] == emitted["off_sidecar_sha256"]
    assert {k: v["sha256"] for k, v in pinned["points"].items()} == {
        k: emitted["points"][k]["source_sha256"] for k in _KEYS
    }
    assert set(pinned["points"][_KEYS[0]]["provenance"]) == set(canary._SOURCE_PROVENANCE_KEYS)
    assert "git_sha" not in {k for k in pinned if k != "points"}
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        canary.pin_sources(sources, record_path=record)

    # A re-scored sidecar under the SAME adapter hash is not the file the artifact came from.
    key = _KEYS[-1]
    blob = json.loads(canary.sidecar_path(key).read_text(encoding="utf-8"))
    fact = next(iter(blob["in_taught"]["per_fact"]))
    blob["in_taught"]["per_fact"][fact]["member"] = True
    canary.sidecar_path(key).write_text(json.dumps(blob), encoding="utf-8")
    with pytest.raises(SystemExit, match="does not re-derive"):
        canary.pin_sources(tmp_path / "sources2.json", record_path=record)


def test_emit_refuses_a_sidecar_whose_shape_or_fact_set_is_not_the_off_sidecars(
    tmp_path, monkeypatch
):
    _complete_fake_audit(tmp_path, monkeypatch)
    off = canary.off_sidecar_path()
    intact = off.read_text(encoding="utf-8")

    # A truncated OFF sidecar under the right base hash: one filler fact gone.
    blob = json.loads(intact)
    gone = next(iter(blob["out_taught"]["per_fact"]))
    del blob["out_taught"]["per_fact"][gone]
    off.write_text(json.dumps(blob), encoding="utf-8")
    with pytest.raises(SystemExit, match="per_fact n_questions do not sum"):
        canary.emit(tmp_path / "a.json")

    # The same fact renamed, so counts sum but the population is not the ON sidecars'.
    blob = json.loads(intact)
    blob["out_taught"]["per_fact"]["foreign_fact"] = blob["out_taught"]["per_fact"].pop(gone)
    off.write_text(json.dumps(blob), encoding="utf-8")
    with pytest.raises(SystemExit, match="fact set differs from the OFF sidecar"):
        canary.emit(tmp_path / "b.json")

    # An ON sidecar with the wrong question count under the right adapter hash.
    off.write_text(intact, encoding="utf-8")
    key = _KEYS[3]
    blob = json.loads(canary.sidecar_path(key).read_text(encoding="utf-8"))
    blob["in_taught"]["questions"] = 111
    canary.sidecar_path(key).write_text(json.dumps(blob), encoding="utf-8")
    with pytest.raises(SystemExit, match=f"{key}: in_taught has 111 questions"):
        canary.emit(tmp_path / "c.json")


def test_the_instrument_sha_is_resolved_once_at_import_not_per_write(monkeypatch):
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", canary.INSTRUMENT_GIT_SHA)
    monkeypatch.setattr(canary, "git_sha", lambda default="unknown": "0" * 40)
    provenance = canary._provenance("cpu", 0.0)
    assert provenance["instrument_git_sha"] == canary.INSTRUMENT_GIT_SHA
    assert provenance["head_at_write"] == "0" * 40


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


@needs_adapters
def test_the_live_path_is_wired_end_to_end(tmp_path, monkeypatch, frontier):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    import phase14_recall as pr
    import torch

    def fake_loader(device, adapter_path=None):
        return torch.nn.Module(), None, None, frozenset(), None

    def fake_complete(model, tok, question, device, forbid, *, index):
        return {
            "question": question,
            "prompt_ids": [],
            "completions": [f"answer {index}"] * 9,
            "stopped": [True] * 9,
        }

    monkeypatch.setattr(pr, "load_adapted_model", fake_loader)
    monkeypatch.setattr(pr, "complete_question", fake_complete)
    recorded = []

    def record_reproduction(k, n):
        assert isinstance(k, int) and not isinstance(k, bool)
        assert isinstance(n, int) and not isinstance(n, bool)
        recorded.append((k, n))

    monkeypatch.setattr(phase25_prereg, "prove_reproduction", record_reproduction)
    heartbeat = tmp_path / "hb.jsonl"
    assert (
        canary.main(
            [
                "--points",
                phase26_prereg.CONTROL_KEY,
                "dp_n8_sigma80p000000",
                "--heartbeat",
                str(heartbeat),
            ]
        )
        == 0
    )
    off_blob = json.loads(canary.off_sidecar_path().read_text(encoding="utf-8"))
    control_blob = json.loads(
        canary.sidecar_path(phase26_prereg.CONTROL_KEY).read_text(encoding="utf-8")
    )
    producer = json.loads(canary.sidecar_path("dp_n8_sigma80p000000").read_text(encoding="utf-8"))
    expected = {
        "in_taught": (8, 112),
        "in_heldout": (8, 72),
        "out_taught": (56, 784),
        "out_heldout": (56, 504),
    }
    for blob in (off_blob, control_blob, producer):
        for tier, (n_facts, n_questions) in expected.items():
            assert len(blob[tier]["per_fact"]) == n_facts
            assert len(blob[tier]["per_question"]) == n_questions
            assert blob[tier]["questions"] == n_questions
            assert blob[tier]["draws_per_question"] == 9
    assert recorded == [(0, 1008)]
    assert control_blob["reproduction_gate"]["observed"] == list(recorded[0])

    for key in phase26_prereg.noised_point_keys(frontier):
        if key == "dp_n8_sigma80p000000":
            continue
        clone = copy.deepcopy(producer)
        record = frontier["points"][key]
        clone.update(
            point_key=key,
            adapter_sha256=record["adapter_sha256"],
            adapter_path=record["adapter_path"],
            sigma=record["sigma"],
            epsilon_upper=record["epsilon"],
        )
        canary.sidecar_path(key).write_text(json.dumps(clone), encoding="utf-8")

    emitted = canary.emit(tmp_path / "canary.json")
    assert emitted["audited_point_keys"] == list(_KEYS)
    assert re.fullmatch(r"\d+/15", emitted["reachable_claims"])
    assert isinstance(emitted["auditor_ceiling"], float)
    assert set(emitted["power_gate"]) == {
        "threshold",
        "control_epsilon_lower",
        "passed",
        "sentence",
    }
    assert emitted["power_gate"]["sentence"] == phase26_prereg.POWER_SENTENCE
    assert emitted["exclusions"]["out"]["of"] == 56
    for key in _KEYS:
        point = emitted["points"][key]
        assert point["epsilon_sentence"] == frontier["epsilon_report"]["rendered"][key]
        if key == phase26_prereg.CONTROL_KEY:
            assert point["verdict"] is None
            assert point["comparison"].startswith("VACUOUS BY CONSTRUCTION")
            continue
        assert point["verdict"]["verdict"] in phase26_prereg.VERDICTS
        reasons = point["verdict"]["reasons"]
        assert reasons and all(isinstance(reason, str) for reason in reasons)
        assert any("/" in reason for reason in reasons)
        if point["epsilon_upper"] >= emitted["auditor_ceiling"]:
            assert _prose.normalized(phase26_prereg.CEILING_CLAUSE) in _prose.normalized(
                "\n".join(reasons)
            )
        expected_verdict = phase26_prereg.verdict(
            point["fact_unit"]["epsilon_lower"],
            frontier["points"][key]["epsilon"],
            power_passed=emitted["power_gate"]["passed"],
        )
        assert point["verdict"]["verdict"] == expected_verdict
        assert point["epsilon_upper"] == frontier["points"][key]["epsilon"]
    assert emitted["curve_total_epsilon"] == frontier["epsilon_report"]["curve_total_epsilon"]
    assert sum(emitted["summary"].values()) == 15
    assert (
        emitted["frontier_sha256"]
        == hashlib.sha256(phase25_record.FRONTIER_RECORD.read_bytes()).hexdigest()
    )
    assert (
        emitted["prereg_module_sha256"]
        == hashlib.sha256((_ROOT / "scripts" / "phase26_prereg.py").read_bytes()).hexdigest()
    )
    beats = [json.loads(line) for line in heartbeat.read_text(encoding="utf-8").splitlines()]
    assert len(beats) >= 3
    assert {beat["stage"] for beat in beats} >= {"score", "done"}
    evidence_key = phase26_prereg.noised_point_keys(frontier)[0]
    print(
        "PHASE26_WIRING_EVIDENCE "
        + json.dumps(
            {
                "power_gate": emitted["power_gate"],
                "auditor_ceiling": emitted["auditor_ceiling"],
                "reachable_claims": emitted["reachable_claims"],
                "point_key": evidence_key,
                "verdict_reasons": emitted["points"][evidence_key]["verdict"]["reasons"],
            },
            sort_keys=True,
        )
    )


@needs_adapters
def test_the_control_routes_its_in_taught_sum_through_prove_reproduction(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    import phase14_recall as pr
    import torch

    def fake_loader(device, adapter_path=None):
        return torch.nn.Module(), None, None, frozenset(), None

    def fake_complete(model, tok, question, device, forbid, *, index):
        return {
            "question": question,
            "prompt_ids": [],
            "completions": [f"answer {index}"] * 9,
            "stopped": [True] * 9,
        }

    monkeypatch.setattr(pr, "load_adapted_model", fake_loader)
    monkeypatch.setattr(pr, "complete_question", fake_complete)
    calls = []

    def refuse(k, n):
        calls.append((k, n))
        raise SystemExit("gate")

    monkeypatch.setattr(phase25_prereg, "prove_reproduction", refuse)
    with pytest.raises(SystemExit, match="gate"):
        canary.score_point(phase26_prereg.CONTROL_KEY, heartbeat_path=tmp_path / "refused-hb.jsonl")
    assert not canary.sidecar_path(phase26_prereg.CONTROL_KEY).exists()

    def pass_gate(k, n):
        calls.append((k, n))

    monkeypatch.setattr(phase25_prereg, "prove_reproduction", pass_gate)
    status, blob = canary.score_point(
        phase26_prereg.CONTROL_KEY, heartbeat_path=tmp_path / "passed-hb.jsonl"
    )
    assert status == "scored"
    assert canary.sidecar_path(phase26_prereg.CONTROL_KEY).exists()
    assert calls[-1] == (blob["in_taught"]["k"], blob["in_taught"]["n"])


@needs_adapters
def test_the_power_gate_goes_red_on_a_forged_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    live_record = canary.RECORD.read_bytes() if canary.RECORD.exists() else None
    base = _convbase_path()
    canary.off_sidecar_path().write_text(
        json.dumps(_fake_off_sidecar(base_sha=canary._sha256(base))), encoding="utf-8"
    )
    for key in _KEYS:
        canary.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")
    emitted_path = tmp_path / "emitted.json"
    canary.emit(emitted_path)
    forged_path = tmp_path / "forged.json"
    forged = json.loads(emitted_path.read_text(encoding="utf-8"))
    forged["power_gate"]["passed"] = True
    forged["power_gate"]["control_epsilon_lower"] = 0.1
    forged_path.write_text(json.dumps(forged), encoding="utf-8")

    rederived = phase26_prereg.power_gate(0.1, forged["power_gate"]["threshold"])
    assert rederived["passed"] is False
    for key in phase26_prereg.noised_point_keys(_FRONTIER):
        verdict = phase26_prereg.point_verdict(
            forged["points"][key]["fact_unit"],
            forged["points"][key]["epsilon_upper"],
            power=rederived,
            auditor_ceiling=forged["auditor_ceiling"],
        )["verdict"]
        assert verdict in {"INCONCLUSIVE", "BROKEN"}
    if live_record is not None:
        assert canary.RECORD.read_bytes() == live_record


def test_the_sibling_is_pinned_to_the_frontier_both_ways(frontier):
    tracked = _git("ls-files", "results/phase26_canary.json").splitlines()
    if canary.RECORD.exists():
        blob = json.loads(canary.RECORD.read_text(encoding="utf-8"))
        assert (
            blob["frontier_sha256"]
            == hashlib.sha256(phase25_record.FRONTIER_RECORD.read_bytes()).hexdigest()
        )
        assert blob["frontier_bytes"] == 22311714
        assert all(
            blob["points"][key]["adapter_sha256"] == frontier["points"][key]["adapter_sha256"]
            for key in _KEYS
        )
        assert (
            blob["prereg_module_sha256"]
            == hashlib.sha256((_ROOT / "scripts" / "phase26_prereg.py").read_bytes()).hexdigest()
        )
        assert (
            len(_git("log", "--oneline", "--", "results/phase25_frontier.json").splitlines()) == 1
        )
        added = _git("log", "--diff-filter=A", "--", "results/phase26_canary.json").splitlines()
        assert bool(tracked) == bool(added)
    else:
        assert not tracked


def test_every_point_carries_its_reasons_and_the_ceiling_disclosure(frontier):
    tracked = _git("ls-files", "results/phase26_canary.json").splitlines()
    if not canary.RECORD.exists():
        assert not tracked
        return
    blob = json.loads(canary.RECORD.read_text(encoding="utf-8"))
    reachable = []
    for key in phase26_prereg.noised_point_keys(frontier):
        point = blob["points"][key]
        reasons = point["verdict"]["reasons"]
        assert reasons
        if point["epsilon_upper"] >= blob["auditor_ceiling"]:
            assert _prose.normalized(phase26_prereg.CEILING_CLAUSE) in _prose.normalized(
                "\n".join(reasons)
            )
        else:
            reachable.append(key)
    assert blob["reachable_claims"] == f"{len(reachable)}/15"
    assert sum(blob["summary"].values()) == 15


@pytest.mark.skipif(
    not canary.sidecar_path(phase26_prereg.CONTROL_KEY).exists(),
    reason="control sidecar not yet scored — lands during the 26-04 run",
)
@needs_adapters
def test_the_control_reproduced_the_published_reading():
    blob = json.loads(canary.sidecar_path(phase26_prereg.CONTROL_KEY).read_text(encoding="utf-8"))
    assert (blob["in_taught"]["k"], blob["in_taught"]["n"]) == (790, 1008)
    assert blob["reproduction_gate"]["passed"] is True
    assert blob["device"] == "mps"
    assert blob["torch_version"]


# The operational note — blocks that must be present. Each heading pins a quoted command transcript
# (results/phase26_operational_note.md); the shape copies tests/test_phase25_launch.py's register.
_NOTE_REQUIRED_BLOCKS = (
    "## 1. The pre-registration state",
    "## 2. The assertion owners before launch",
    "## 3. The budget as measured",
    "## 4. The wiring proof",
    "## 5. The launch record",
    "## 6. The early-run gate",
    "## 8. The close",
)


@pytest.fixture(scope="module")
def note():
    return _prose.normalized(canary.OPERATIONAL_NOTE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("heading", _NOTE_REQUIRED_BLOCKS)
def test_the_operational_note_carries_every_required_block(note, heading):
    assert _prose.normalized(heading) in note, heading
