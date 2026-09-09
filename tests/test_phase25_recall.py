"""Plan 25-18 Task 0 (D-25-18-RECALL): the recall driver, its agent, and the artifact assembly.

CPU-only. The dry run walks all 44 pinned keys against the committed records and the adapters on
disk; resume/refusal and the emitter run on fixtures under ``tmp_path``. The one AST test pins the
driver's ``score_arm`` call to the exact shape ``phase25_points.measure_stage`` uses for the
controls, so the 42 new readings and the 2 recorded ones come off one instrument.
"""

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

import phase25_recall as recall  # noqa: E402  (scripts/ is not a package)
import phase25_record  # noqa: E402  (same)

_PLIST = _ROOT / "artifacts" / "com.personacore.phase25.recall.plist"
_SWEEP_PLIST = _ROOT / "artifacts" / "com.personacore.phase25.sweep.plist"
_KEYS = tuple(phase25_record.ORDERED_POINT_KEYS())

# 25-REVIEW CR-01: `score_point`'s first `_prove` is `adapter.exists()`, and the 44 adapters live
# under gitignored `checkpoints/` — present only on the sweep host, absent on a clone and on
# ubuntu-latest CI. `plutil` is macOS-only. Same idiom as `test_phase25_close.py`'s `pmset` gate.
# `(_ROOT / "checkpoints").is_dir()` short-circuits the 44 record reads on a clone, where the
# directory is absent and every one of them would answer False anyway.
_ADAPTERS_ON_DISK = (_ROOT / "checkpoints").is_dir() and all(
    (_ROOT / recall.point_record(k)["adapter_path"]).exists() for k in _KEYS
)
needs_adapters = pytest.mark.skipif(
    not _ADAPTERS_ON_DISK,
    reason="the 44 sweep adapters live under gitignored checkpoints/ — sweep host only",
)
needs_plutil = pytest.mark.skipif(shutil.which("plutil") is None, reason="plutil is macOS-only")


def _fake_sidecar(key, *, sha=None):
    record = recall.point_record(key)
    tier = {
        "numerator": 1,
        "denominator": 1008,
        "rate": 1 / 1008,
        "questions": 112,
        "draws_per_question": 9,
        "per_family": {},
    }
    heldout = dict(tier, denominator=648, questions=72)
    return {
        "point_key": key,
        "arm": record["arm"],
        "adapter_path": record["adapter_path"],
        "adapter_sha256": record["adapter_sha256"] if sha is None else sha,
        "taught_recall": tier,
        "heldout_recall": heldout,
        "taught_recall_off": tier,
        "heldout_recall_off": heldout,
        "per_family_gain": {},
        "scoring_seconds": 900.0,
        "instrument": recall.INSTRUMENT,
        "instrument_git_sha": "fixture",
        "device": "fixture",
        "utc": "fixture",
    }


# ===== (a) the dry run covers every structural path without the device =====


@needs_adapters
def test_the_dry_run_walks_all_44_and_scores_none(tmp_path, capsys, monkeypatch):
    """2 controls come from their records, 42 would be scored; nothing is written anywhere.

    ``SIDECAR_DIR`` is isolated: once the scoring leg has run, the real ``data/`` holds 42
    sidecars and the live walk reports ``reused`` — which is the resume path, tested separately."""
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    statuses = {}
    for key in _KEYS:
        status, blob = recall.score_point(key, dry_run=True, heartbeat_path=tmp_path / "hb.jsonl")
        statuses[key] = status
        assert blob is None
    counts = {s: sum(1 for v in statuses.values() if v == s) for s in set(statuses.values())}
    assert counts == {recall.SOURCE_POINT_RECORD: 2, "dry_run": 42}, counts
    assert {k for k, s in statuses.items() if s == recall.SOURCE_POINT_RECORD} == {
        "dp_n8_sigma0p000000",
        "dp_n64_sigma0p000000",
    }
    assert not (tmp_path / "hb.jsonl").exists()
    assert "DRY RUN" in capsys.readouterr().out


@needs_adapters
def test_the_dry_run_and_reuse_paths_never_import_torch():
    """ORDER-INDEPENDENT: a fresh interpreter walks the dry run and a sidecar reuse, then reports
    whether torch entered sys.modules. Asserting `"torch" not in sys.modules` in-process is
    vacuous once any earlier test has imported torch (measured: green alone, red in the suite)."""
    script = (
        "import json, pathlib, sys, tempfile\n"
        f"sys.path.insert(0, {str(_SCRIPTS)!r})\n"
        "import phase25_recall as r\n"
        "tmp = pathlib.Path(tempfile.mkdtemp())\n"
        "r.SIDECAR_DIR = tmp\n"
        "key = 'dp_n8_sigma0p500000'\n"
        "rec = r.point_record(key)\n"
        "side = {'adapter_sha256': rec['adapter_sha256'], 'taught_recall': {}}\n"
        "r.sidecar_path(key).write_text(json.dumps(side))\n"
        "assert r.score_point(key, dry_run=False)[0] == 'reused'\n"
        "assert r.score_point('dp_n64_sigma0p500000', dry_run=True)[0] == 'dry_run'\n"
        "assert r.score_point('dp_n8_sigma0p000000', dry_run=True)[0] == 'point_record'\n"
        "print('torch' in sys.modules)\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, cwd=_ROOT
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert completed.stdout.strip().splitlines()[-1] == "False"
    # And by AST: every torch-touching import in the driver is INSIDE a function, never at
    # module scope, so the property is structural rather than a snapshot.
    tree = ast.parse((_SCRIPTS / "phase25_recall.py").read_text(encoding="utf-8"))
    top_level = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    } | {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}
    assert not top_level & {"torch", "teach_persona", "phase14_factset", "phase14_recall"}


@needs_adapters
def test_every_adapter_is_on_disk_and_hashes_to_its_record():
    """The precondition the operator's decision rests on: no retraining is needed."""
    for key in _KEYS:
        record = recall.point_record(key)
        adapter = _ROOT / record["adapter_path"]
        assert adapter.exists(), key
        assert recall._sha256(adapter) == record["adapter_sha256"], key


# ===== (b) resume reuses a matching sidecar and REFUSES a mismatched one =====


@needs_adapters
def test_a_matching_sidecar_is_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    key = "dp_n8_sigma0p500000"
    recall.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")
    status, blob = recall.score_point(key, dry_run=False)
    assert status == "reused"
    assert blob["taught_recall"]["denominator"] == 1008


@needs_adapters
def test_a_sidecar_for_a_different_adapter_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    key = "dp_n8_sigma0p500000"
    recall.sidecar_path(key).write_text(
        json.dumps(_fake_sidecar(key, sha="0" * 64)), encoding="utf-8"
    )
    with pytest.raises(SystemExit) as excinfo:
        recall.score_point(key, dry_run=True)
    assert "REFUSED, not reused" in str(excinfo.value)


@needs_adapters
def test_a_control_is_never_rescored_even_with_no_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    status, _ = recall.score_point("dp_n8_sigma0p000000", dry_run=False)
    assert status == recall.SOURCE_POINT_RECORD


# ===== (c) the emitter: 2 records + 42 sidecars == the pinned 44, or a refusal =====


def test_the_emitter_asserts_set_equality_against_the_pinned_44(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    for key in _KEYS:
        if not all(f in recall.point_record(key) for f in recall.RECALL_FIELDS):
            recall.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")
    out = tmp_path / "recall.json"
    blob = recall.emit(out)
    assert set(blob["points"]) == set(_KEYS) and len(blob["points"]) == 44
    assert blob["sources"] == {recall.SOURCE_POINT_RECORD: 2, "sidecar": 42}
    assert blob["point_records_byte_unchanged"] is True
    assert blob["denominators"] == {"taught": 1008, "heldout": 648}
    for key in ("dp_n8_sigma0p000000", "dp_n64_sigma0p000000"):
        entry = blob["points"][key]
        record = recall.point_record(key)
        assert entry["source"] == recall.SOURCE_POINT_RECORD
        assert entry["taught_recall"] == record["taught_recall"]
        assert entry["heldout_recall"] == record["heldout_recall"]
        assert entry["adapter_sha256"] == record["adapter_sha256"]
    assert blob["points"]["dp_n8_sigma0p000000"]["taught_recall"]["numerator"] == 790
    assert json.loads(out.read_text(encoding="utf-8"))["points"].keys() == blob["points"].keys()


def test_the_emitter_refuses_a_missing_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    for key in _KEYS[:-1]:
        if not all(f in recall.point_record(key) for f in recall.RECALL_FIELDS):
            recall.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        recall.emit(tmp_path / "recall.json")
    assert "not scored" in str(excinfo.value)
    assert not (tmp_path / "recall.json").exists()


# ===== (d) the agent: does not start itself, same wrapper, same heartbeat, own log =====


def _plist(path):
    with path.open("rb") as handle:
        return plistlib.load(handle)


@needs_plutil
def test_the_recall_agent_does_not_start_itself_and_lints():
    parsed = _plist(_PLIST)
    assert parsed["KeepAlive"] is False
    assert parsed["RunAtLoad"] is False
    assert parsed["Label"] == "com.personacore.phase25.recall"
    assert subprocess.run(["plutil", "-lint", str(_PLIST)], capture_output=True).returncode == 0


def test_the_recall_agent_mirrors_the_sweep_agents_wrapper_and_heartbeat():
    ours, sweep = _plist(_PLIST), _plist(_SWEEP_PLIST)
    assert ours["ProgramArguments"][:3] == sweep["ProgramArguments"][:3]  # caffeinate -dims python
    assert ours["ProgramArguments"][3].endswith("scripts/phase25_recall.py")
    beat = ours["ProgramArguments"][ours["ProgramArguments"].index("--heartbeat") + 1]
    assert beat == sweep["ProgramArguments"][sweep["ProgramArguments"].index("--heartbeat") + 1]
    # A LaunchAgent needs ABSOLUTE paths, so both plists carry the sweep host's repo path.
    # Off that host (CI, a clone) the checkable property is that the two agree and name the
    # same repo; the equality with this checkout's root only means anything where the plists
    # are the ones launchd would load. Measured on ubuntu CI run 34403612853, which failed
    # here asserting "/Users/juliorcoelho/PersonaCore" == "/home/runner/work/PersonaCore/...".
    assert ours["WorkingDirectory"] == sweep["WorkingDirectory"]
    assert pathlib.Path(ours["WorkingDirectory"]).name == _ROOT.name
    if pathlib.Path(ours["WorkingDirectory"]).is_dir():
        assert ours["WorkingDirectory"] == str(_ROOT)
    assert ours["StandardOutPath"] != sweep["StandardOutPath"]
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"


# ===== (e) ONE instrument: the driver's score_arm call has measure_stage's exact shape (AST) =====


def _score_arm_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "score_arm"
    ]


def test_the_driver_calls_score_arm_exactly_as_measure_stage_does():
    ours = _score_arm_calls(_SCRIPTS / "phase25_recall.py")
    theirs = _score_arm_calls(_SCRIPTS / "phase25_points.py")
    assert len(ours) == 1 and len(theirs) == 1, (len(ours), len(theirs))
    shape = lambda call: (  # noqa: E731
        ast.dump(call.func),
        [ast.dump(arg) for arg in call.args],
        [ast.dump(kw) for kw in call.keywords],
    )
    assert shape(ours[0]) == shape(theirs[0])
    assert shape(ours[0])[1] == [
        ast.dump(ast.parse(src, mode="eval").body)
        for src in ("arm", "fs.LOCKED_FACTS", "adapter", "device")
    ]


# ===== 25-REVIEW WR-01: the artifact is write-once =====


def test_emit_refuses_to_overwrite_the_committed_artifact():
    """The refusal fires against the LIVE file, before a sidecar or a record is read.

    `results/phase25_frontier.json` pins these bytes (`provenance.inputs.recall_record.sha256`),
    so a second `--emit` over the committed artifact would republish it under a new
    `emitted_git_sha` the frontier does not name. Host-independent: the guard is `emit`'s first
    statement, so it never reaches `checkpoints/` and carries no `@needs_adapters`.
    """
    assert recall.RECORD.exists()
    before = recall.RECORD.read_bytes()
    with pytest.raises(SystemExit) as excinfo:
        recall.emit()
    assert "REFUSING to overwrite it" in str(excinfo.value)
    assert "--force" in str(excinfo.value)
    assert recall.RECORD.read_bytes() == before
