"""Plan 37-04: R1b, the MPS replica driver (scripts/phase37_r1b.py), tested on CPU only.

The device work (the sweep, the erased arm, the model load, the adapter hash, the device resolve)
is monkeypatched; everything else is the driver's own code against tmp_path roots, ledgers and
heartbeats. What this file proves:
- D-07's two branches: k == 78 and the same set -> the arm runs on the RE-MEASURED list; k != 78 or
  a different set -> the arm never runs and the record reads NOT_REPLICATED (D-14: the sweep is in
  both);
- D-03: the verdict comes only from phase37_prereg.replicated over phase37_routes.rederive, and the
  consumer is fed the REAL committed erased arm (REPLICATED, 0 differing completions);
- D-04 / D-12: a NOT_REPLICATED arm carries the per-slot non-target context beside the floor;
- D-11 / D-16: every cheap refusal runs before the ledger start line; once the start line exists
  the attempt is THE attempt, and no second line for RUN_ID is ever written;
- the ledger wiring: require_launch before start, start/end lines, end names R1B_RECORD.

Nothing here touches the real ledger, the real results/ or data/phase37_r1b_run.json.
"""

import copy
import datetime
import hashlib
import inspect
import json
import pathlib
import re
import shutil
import sys
import types

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase14_recall  # noqa: E402  (scripts/ is not a package)
import phase19_erasure as pin  # noqa: E402  (same)
import phase19_run as p19run  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same; never aliased)
import phase37_prereg  # noqa: E402  (same; never aliased)
import phase37_r1b  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase37_routes  # noqa: E402  (same; never aliased)
import teach_persona  # noqa: E402  (same)

from personacore.provenance import git_sha  # noqa: E402
from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402

_REAL_SIDECAR = _ROOT / "data" / "phase37_r1b_run.json"

# WR-03: every input file the run reads, as the (module, constant) its reader takes it from.
_RUN_INPUTS = (
    (phase14_recall, "CONVBASE_SLIM"),
    (phase14_recall, "ADAPTER_PATH"),
    (phase14_recall, "TOKENIZER_PATH"),
    (teach_persona, "DIALOG_VAL_BIN"),
    (teach_persona, "DIALOG_VAL_MASK"),
    (pin, "RETENTION_BIN"),
    (pin, "PHASE18_CORPUS_PATH"),
    (pin, "PHASE18_ARM_RECORD_PATH"),
)
# The gitignored ones (absent on CI): the rig stands each in with a tmp file.
_GITIGNORED_INPUTS = (
    "CONVBASE_SLIM",
    "ADAPTER_PATH",
    "DIALOG_VAL_BIN",
    "DIALOG_VAL_MASK",
    "RETENTION_BIN",
)


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    sidecar_before = _REAL_SIDECAR.exists()
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _REAL_SIDECAR.exists() == sidecar_before


@pytest.fixture(scope="module")
def curve():
    return json.loads(p19run.TARGET_CURVE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def committed():
    return json.loads(pin.arm_record_path("erased").read_text(encoding="utf-8"))


def _prefix(curve):
    return [tuple(a) for a in curve["ordered_prefix"]]


def _outside(curve):
    inside = set(_prefix(curve))
    return next(tuple(a) for a in pin.component_index() if tuple(a) not in inside)


@pytest.fixture
def rig(tmp_path, monkeypatch, curve):
    """The run fixture: a tmp root, tmp ledger/heartbeat, the device work stubbed."""
    (tmp_path / "results").mkdir()
    (tmp_path / "data").mkdir()
    paths = {"ledger_path": tmp_path / "ledger.jsonl", "heartbeat_path": tmp_path / "hb.jsonl"}
    rig = types.SimpleNamespace(
        root=tmp_path,
        paths=paths,
        dirty=[],
        launches=[],
        arms=[],
        sweep={"k": curve["k"], "ordered": _prefix(curve), "raise": None},
    )
    for owner, name in _RUN_INPUTS:
        if name in _GITIGNORED_INPUTS:
            stand_in = tmp_path / "data" / f"input_{name}"
            stand_in.write_bytes(b"stand-in")
            monkeypatch.setattr(owner, name, stand_in)
    monkeypatch.setattr(phase37_r1b, "_device", lambda: "mps")
    monkeypatch.setattr(phase37_r1b, "adapter_sha256", lambda: curve["adapter_in_sha256"])
    monkeypatch.setattr(phase37_r1b, "refuse_if_dirty", lambda **kw: rig.dirty.append(kw))

    def require_launch(front, **kw):
        rig.launches.append((front, kw, paths["ledger_path"].exists()))
        return {"front": front}

    monkeypatch.setattr(phase36_ledger, "require_launch", require_launch)
    monkeypatch.setattr(
        phase14_recall,
        "load_adapted_model",
        lambda device, adapter_path=None: ("model", None, "tok", "forbid", "artifact"),
    )

    def select(model, tok, device, artifact, *, fact, dialogue_ppl):
        assert fact.slot == pin.TARGET_SLOT and device == "mps" and callable(dialogue_ppl)
        if rig.sweep["raise"] is not None:
            raise rig.sweep["raise"]
        return {
            "k": rig.sweep["k"],
            "stopped": True,
            "cap": curve["cap"],
            "ordered": list(rig.sweep["ordered"]),
            "intact_nll": curve["intact_nll"],
            "curve": curve["checkpoints"],
        }

    monkeypatch.setattr(phase37_routes, "select_target_prefix", select)

    def arm(name, device, *, components=(), record_path=None, **kw):
        rig.arms.append(
            {"arm": name, "device": device, "components": list(components), "path": record_path}
        )
        shutil.copyfile(pin.arm_record_path("erased"), record_path)

    monkeypatch.setattr(pin, "run_erasure_arm", arm)
    return rig


def _lines(rig):
    return phase36_ledger.read_ledger(rig.paths["ledger_path"])


# =================================================================================================
# (1) The module's own helpers (W1): these run unpatched.
# =================================================================================================


def test_prove_sha_now_and_sidecar_helpers(tmp_path):
    with pytest.raises(SystemExit, match=r"^\[phase37_r1b\] broken$"):
        phase37_r1b._prove(False, "broken")
    phase37_r1b._prove(True, "never raised")
    blob = tmp_path / "b.bin"
    blob.write_bytes(b"r1b")
    assert phase37_r1b._sha256(blob) == hashlib.sha256(b"r1b").hexdigest()
    assert datetime.datetime.fromisoformat(phase37_r1b._now()).tzinfo is not None
    assert phase37_r1b.run_sidecar(tmp_path) == tmp_path / "data" / "phase37_r1b_run.json"
    assert phase37_r1b.RUN_ID == "v6/37/R1b/replica" == phase36_ledger.run_id(37, "R1b", "replica")


def test_device_is_the_strict_preflight_device(monkeypatch):
    import personacore.preflight

    seen = []
    monkeypatch.setattr(
        personacore.preflight,
        "preflight_device",
        lambda **kw: seen.append(kw) or {"device": "mps"},
    )
    assert phase37_r1b._device() == "mps"
    assert seen == [{"strict": True}]


def test_adapter_sha256_hashes_the_production_adapter_path(tmp_path, monkeypatch):
    fake = tmp_path / "persona_adapter.pt"
    fake.write_bytes(b"adapter bytes")
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", fake)
    assert phase37_r1b.adapter_sha256() == hashlib.sha256(b"adapter bytes").hexdigest()


def test_curve_is_the_committed_curve(curve):
    assert phase37_r1b._curve() == curve


# =================================================================================================
# (2) run(): D-07's set-equal branch, the ledger, the heartbeat, D-14, provenance.run.
# =================================================================================================


def test_run_on_the_committed_order_replicates(rig, curve, committed):
    record = phase37_r1b.run(root=rig.root, **rig.paths)
    assert record["verdict"] == "REPLICATED"
    assert all(row["abs_diff"] == 0 for row in record["comparison"]["per_key"].values())
    n_completions = sum(len(d["completions"]) for d in committed["draws"])
    assert n_completions == 216 * 48
    identity = record["draw_identity"]
    assert identity["bit_identical"] is True and identity["criterion"] is False
    assert identity["differing_completions"] == 0 and identity["n_completions"] == n_completions
    assert record["decision"]["positions_moved"] == 0 and record["decision"]["run_arm"] is True
    assert rig.arms == [
        {
            "arm": "erased",
            "device": "mps",
            "components": _prefix(curve),
            "path": rig.root / phase37_prereg.R1B_ARM_RECORD,
        }
    ]
    assert rig.launches == [("R1b", {"ledger_path": rig.paths["ledger_path"]}, False)]
    lines = _lines(rig)
    assert [(x["event"], x["run_id"], x["front"], x["phase"]) for x in lines] == [
        ("start", phase37_r1b.RUN_ID, "R1b", 37),
        ("end", phase37_r1b.RUN_ID, "R1b", 37),
    ]
    assert lines[1]["record"] == phase37_prereg.R1B_RECORD
    beats = [json.loads(t) for t in rig.paths["heartbeat_path"].read_text().splitlines()]
    assert beats and all(b["point"] == phase37_r1b.RUN_ID for b in beats)
    run = record["provenance"]["run"]
    assert (
        set(run)
        == set(phase37_r1b.RUN_PROVENANCE_KEYS)
        == {
            "git_sha_at_launch",
            "git_sha_at_end",
            "head_moved_during_run",
            "device",
            "torch_version",
            "started_utc",
            "finished_utc",
        }
    )
    head = _git("rev-parse", "HEAD")
    assert run["git_sha_at_launch"] == run["git_sha_at_end"] == head
    assert run["head_moved_during_run"] is False
    assert record["provenance"]["module_sha256_at_launch"] == phase37_r1b.module_sha256()
    assert record["provenance"]["modules_changed_since_launch"] == []
    assert run["device"] == "mps" and run["started_utc"] <= run["finished_utc"]
    sweep = record["sweep"]
    assert sweep["ordered_prefix"] == curve["ordered_prefix"] and sweep["k"] == curve["k"]
    assert sweep["curve"] == curve["checkpoints"]
    assert sweep["reference_set_size"] == curve["reference_set_size"]
    assert record["arm_record"] == phase37_prereg.R1B_ARM_RECORD
    on_disk = json.loads((rig.root / phase37_prereg.R1B_RECORD).read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(record))
    sidecar = json.loads(phase37_r1b.run_sidecar(rig.root).read_text(encoding="utf-8"))
    assert sidecar["arm_ran"] is True and sidecar["run_id"] == phase37_r1b.RUN_ID
    scope = phase37_prereg.ENTRIES["r1b_scope"]["value"]
    assert record["re_measured"] == list(scope["re_measured"])
    assert record["inherited"] == list(scope["inherited"])
    tolerance = phase37_prereg.R1B_TOLERANCE_AND_REPLICATED["tolerance"]
    assert record["tolerance"] == dict(tolerance)
    exclude = tuple(
        f":(exclude){rel}" for rel in (phase37_prereg.R1B_ARM_RECORD, phase37_prereg.R1B_RECORD)
    )
    assert [kw["pathspec"] for kw in rig.dirty] == [
        phase37_r1b.LAUNCH_PATHSPEC,
        ("scripts", "src", "results", *exclude),
    ]


def test_run_on_a_reordered_set_runs_the_remeasured_list(rig, curve):
    reordered = list(reversed(_prefix(curve)))
    rig.sweep["ordered"] = reordered
    record = phase37_r1b.run(root=rig.root, **rig.paths)
    assert rig.arms[0]["components"] == reordered
    moved = sum(a != b for a, b in zip(reordered, _prefix(curve), strict=True))
    assert moved > 0 and record["decision"]["positions_moved"] == moved
    assert record["decision"]["set_equal"] is True
    assert record["verdict"] == "REPLICATED"


# =================================================================================================
# (3) run(): D-07's divergence branch — the arm never runs, the sweep is still recorded (D-14).
# =================================================================================================


def _diverged(rig):
    record = phase37_r1b.run(root=rig.root, **rig.paths)
    assert rig.arms == []
    assert record["verdict"] == "NOT_REPLICATED"
    assert record["arm_record"] is None and "comparison" not in record
    assert "draw_identity" not in record and "sweep" in record
    assert [x["event"] for x in _lines(rig)] == ["start", "end"]
    assert not (rig.root / phase37_prereg.R1B_ARM_RECORD).exists()
    return record


def test_run_k79_does_not_run_the_arm(rig, curve):
    extra = _outside(curve)
    rig.sweep.update(k=curve["k"] + 1, ordered=[*_prefix(curve), extra])
    record = _diverged(rig)
    assert record["decision"]["k_equal"] is False and record["decision"]["k"] == curve["k"] + 1
    assert record["decision"]["only_in_remeasured"] == [list(extra)]
    assert record["sweep"]["ordered_prefix"] == [list(a) for a in [*_prefix(curve), extra]]


def test_run_k78_with_another_set_does_not_run_the_arm(rig, curve):
    swapped = _prefix(curve)
    dropped, swapped[-1] = swapped[-1], _outside(curve)
    rig.sweep["ordered"] = swapped
    record = _diverged(rig)
    assert record["decision"]["k_equal"] is True and record["decision"]["set_equal"] is False
    assert record["decision"]["only_in_remeasured"] == [list(swapped[-1])]
    assert record["decision"]["only_in_committed"] == [list(dropped)]


# =================================================================================================
# (4) D-11 / D-16: one attempt. Refusals before the start line write nothing.
# =================================================================================================


def test_a_crash_after_the_start_line_is_the_attempt(rig):
    rig.sweep["raise"] = RuntimeError("sweep died")
    with pytest.raises(RuntimeError, match="sweep died"):
        phase37_r1b.run(root=rig.root, **rig.paths)
    lines = _lines(rig)
    assert [x["event"] for x in lines] == ["start"]
    assert phase37_r1b.RUN_ID in phase36_ledger.open_runs(lines)
    assert not phase37_r1b.run_sidecar(rig.root).exists()
    rig.sweep["raise"] = None
    with pytest.raises(SystemExit, match="D-11"):
        phase37_r1b.run(root=rig.root, **rig.paths)
    assert _lines(rig) == lines
    phase36_ledger.reconcile(**rig.paths)
    reconciled = _lines(rig)
    assert [x["event"] for x in reconciled] == ["start", "lost"]
    with pytest.raises(SystemExit, match="D-11"):
        phase37_r1b.run(root=rig.root, **rig.paths)
    assert _lines(rig) == reconciled
    assert rig.arms == []


def _refuse_record(rig, monkeypatch):
    (rig.root / phase37_prereg.R1B_RECORD).write_text("{}", encoding="utf-8")


def _refuse_arm(rig, monkeypatch):
    (rig.root / phase37_prereg.R1B_ARM_RECORD).write_text("{}", encoding="utf-8")


def _refuse_sidecar(rig, monkeypatch):
    phase37_r1b.run_sidecar(rig.root).write_text("{}", encoding="utf-8")


def _refuse_cpu(rig, monkeypatch):
    monkeypatch.setattr(phase37_r1b, "_device", lambda: "cpu")


def _refuse_adapter(rig, monkeypatch):
    monkeypatch.setattr(phase37_r1b, "adapter_sha256", lambda: "0" * 64)


def _refuse_unknown_sha(rig, monkeypatch):
    monkeypatch.setattr(phase37_r1b, "git_sha", lambda: "unknown")


def _refuse_launch(rig, monkeypatch):
    def cut(front, **kw):
        raise SystemExit("[phase36_ledger] PAUSE")

    monkeypatch.setattr(phase36_ledger, "require_launch", cut)


@pytest.mark.parametrize(
    "plant",
    [
        _refuse_record,
        _refuse_arm,
        _refuse_sidecar,
        _refuse_cpu,
        _refuse_adapter,
        _refuse_unknown_sha,
        _refuse_launch,
    ],
)
def test_preflight_refusals_write_no_ledger_line(rig, monkeypatch, plant):
    plant(rig, monkeypatch)
    with pytest.raises(SystemExit):
        phase37_r1b.run(root=rig.root, **rig.paths)
    assert not rig.paths["ledger_path"].exists()
    assert not rig.paths["heartbeat_path"].exists()
    assert rig.arms == []


def test_run_inputs_are_the_readers_constants():
    assert phase37_r1b.run_inputs() == tuple(getattr(owner, name) for owner, name in _RUN_INPUTS)


@pytest.mark.parametrize(("owner", "name"), _RUN_INPUTS, ids=[name for _, name in _RUN_INPUTS])
def test_a_missing_run_input_refuses_before_the_start_line(rig, monkeypatch, owner, name):
    """WR-03 / D-16: a missing input is a preflight refusal, not THE attempt."""
    missing = rig.root / "missing" / name
    monkeypatch.setattr(owner, name, missing)
    with pytest.raises(SystemExit, match=re.escape(f"{missing} is missing")):
        phase37_r1b.run(root=rig.root, **rig.paths)
    assert not rig.paths["ledger_path"].exists()
    assert not rig.paths["heartbeat_path"].exists()
    assert rig.arms == []


def test_preflight_alone_writes_nothing_and_reports_the_gate(rig, curve, capsys):
    pre = phase37_r1b.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    assert pre["device"] == "mps" and pre["curve"] == curve and pre["gate"] == {"front": "R1b"}
    assert pre["git_sha"] == _git("rev-parse", "HEAD")  # WR-01: captured at launch
    assert pre["module_sha256"] == phase37_r1b.module_sha256()
    assert capsys.readouterr().out.startswith("PREFLIGHT OK")
    assert not rig.paths["ledger_path"].exists()
    assert sorted(p.name for p in rig.root.iterdir()) == ["data", "results"]


def test_a_commit_landing_mid_run_is_named_not_hidden(rig, monkeypatch):
    """WR-01: launch HEAD, end HEAD and the change between them are all in the record."""
    heads = iter(["a" * 40, "b" * 40, "c" * 40])  # preflight, sidecar, emit
    monkeypatch.setattr(phase37_r1b, "git_sha", lambda: next(heads))
    real = phase37_r1b.module_sha256
    launch = {rel: "0" * 64 for rel in phase37_r1b.MODULES}
    hashes = iter([launch])  # preflight's read; every later read is the real tree
    monkeypatch.setattr(phase37_r1b, "module_sha256", lambda: next(hashes, None) or real())
    record = phase37_r1b.run(root=rig.root, **rig.paths)
    run = record["provenance"]["run"]
    assert (run["git_sha_at_launch"], run["git_sha_at_end"]) == ("a" * 40, "b" * 40)
    assert run["head_moved_during_run"] is True
    assert record["provenance"]["head_at_write"] == "c" * 40
    assert record["provenance"]["module_sha256_at_launch"] == launch
    assert record["provenance"]["module_sha256"] == real()
    assert record["provenance"]["modules_changed_since_launch"] == sorted(phase37_r1b.MODULES)
    sidecar = json.loads(phase37_r1b.run_sidecar(rig.root).read_text(encoding="utf-8"))
    assert sidecar["module_sha256_at_launch"] == launch


# =================================================================================================
# (5) emit / build_record: the consumer fed the REAL committed erased arm (D-03, D-04, D-12).
# =================================================================================================


def _plant_sidecar(rig, curve, *, arm_ran):
    prefix = _prefix(curve)
    blob = {
        "run_id": phase37_r1b.RUN_ID,
        "git_sha_at_launch": "0" * 40,
        "git_sha_at_end": "0" * 40,
        "head_moved_during_run": False,
        "module_sha256_at_launch": phase37_r1b.module_sha256(),
        "device": "mps",
        "torch_version": "planted",
        "started_utc": "2026-10-03T00:00:00+00:00",
        "finished_utc": "2026-10-03T01:00:00+00:00",
        "sweep": {"k": curve["k"], "ordered_prefix": curve["ordered_prefix"]},
        "decision": phase37_prereg.prefix_decision(curve["k"], prefix, prefix),
        "arm_ran": arm_ran,
    }
    phase37_r1b.run_sidecar(rig.root).write_text(json.dumps(blob), encoding="utf-8")
    return blob


def test_emit_on_the_committed_arm_reads_replicated(rig, curve):
    _plant_sidecar(rig, curve, arm_ran=True)
    shutil.copyfile(pin.arm_record_path("erased"), rig.root / phase37_prereg.R1B_ARM_RECORD)
    record = phase37_r1b.emit(root=rig.root)
    assert record["verdict"] == "REPLICATED" and record["replica_verdict"] == "FAILURE"
    assert record["draw_identity"]["differing_completions"] == 0
    assert record["draw_identity"]["differing_entries"] == 0
    assert record["provenance"]["run"]["torch_version"] == "planted"


def test_emit_on_a_shifted_arm_reads_not_replicated_with_context(rig, curve, committed):
    _plant_sidecar(rig, curve, arm_ran=True)
    shifted = copy.deepcopy(committed)
    shifted["dialogue_ppl"]["adapter_on"] += 0.05
    (rig.root / phase37_prereg.R1B_ARM_RECORD).write_text(
        json.dumps(shifted, sort_keys=True), encoding="utf-8"
    )
    record = phase37_r1b.emit(root=rig.root)
    assert record["verdict"] == "NOT_REPLICATED"
    assert record["comparison"]["per_key"]["destroyed_pct"]["within"] is False
    context = record["nontarget_context"]
    assert context["criterion"] is False
    assert context["noise_floor"] == phase37_prereg.NONTARGET_FLOOR
    assert set(context["slots"]) == set(pin.GATED_NONTARGET_SLOTS)
    assert all(row["abs_diff"] == 0 for row in context["slots"].values())


def test_emit_refuses_an_existing_record_and_a_missing_sidecar(rig, curve):
    with pytest.raises(SystemExit, match="phase37_r1b_run.json"):
        phase37_r1b.emit(root=rig.root)
    _plant_sidecar(rig, curve, arm_ran=False)
    (rig.root / phase37_prereg.R1B_RECORD).write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING"):
        phase37_r1b.emit(root=rig.root)
    assert rig.dirty == []


def test_build_record_without_the_arm(rig, curve):
    blob = _plant_sidecar(rig, curve, arm_ran=False)
    record = phase37_r1b.build_record(blob, root=rig.root)
    assert record["verdict"] == phase37_prereg.ENTRIES["not_replicated_rule"]["value"]
    assert record["arm_record"] is None and record["sweep"] == blob["sweep"]
    assert set(record["provenance"]["module_sha256"]) == set(phase37_r1b.MODULES)
    assert record["provenance"]["run"]["git_sha_at_launch"] == blob["git_sha_at_launch"]
    assert record["provenance"]["modules_changed_since_launch"] == []
    expected = {
        rel: hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest()
        for rel in (phase37_prereg.CURVE_RECORD, phase37_prereg.ERASED_RECORD)
    }
    assert record["committed_comparators"] == expected


# =================================================================================================
# (6) main(): the three subcommands, traced against the real signatures.
# =================================================================================================


@pytest.mark.parametrize("command", ["preflight", "run", "emit"])
def test_main_dispatches_with_signature_valid_kwargs(tmp_path, monkeypatch, command):
    real = getattr(phase37_r1b, command)
    seen = []

    def recorder(*args, **kwargs):
        inspect.signature(real).bind(*args, **kwargs)
        # WR-05: whatever the launch cwd, the command runs at the repo root, so every git_sha()
        # (the driver's and the pin's arm record) names this repository's HEAD.
        seen.append((args, kwargs, pathlib.Path.cwd(), git_sha()))
        return command

    monkeypatch.setattr(phase37_r1b, command, recorder)
    monkeypatch.chdir(tmp_path)
    assert phase37_r1b.main([command]) == command
    assert seen == [((), {}, _ROOT, _git("rev-parse", "HEAD"))]


@pytest.mark.parametrize("argv", [["bogus"], [], ["run", "extra"]])
def test_main_refuses_anything_else(argv):
    with pytest.raises(SystemExit):
        phase37_r1b.main(argv)


# =================================================================================================
# (7) The LaunchAgent (a mirror of the phase36 probe agent), zero skips, every function called.
# =================================================================================================

_PLIST = _ROOT / "artifacts" / "com.personacore.phase37.r1b.plist"
_PROBE_PLIST = _ROOT / "artifacts" / "com.personacore.phase36.probe.plist"


def _plist(path):
    import plistlib

    return plistlib.loads(path.read_bytes())


def test_plist_mirrors_the_phase36_probe_agent():
    ours, probe = _plist(_PLIST), _plist(_PROBE_PLIST)
    assert ours["Label"] == "com.personacore.phase37.r1b"
    assert ours["KeepAlive"] is False and ours["RunAtLoad"] is False
    args = ours["ProgramArguments"]
    assert args[:3] == probe["ProgramArguments"][:3]
    assert args[:2] == ["/usr/bin/caffeinate", "-dims"]
    assert args[2].endswith("/.venv/bin/python")
    assert args[3].endswith("scripts/phase37_r1b.py")
    assert args[4:] == ["run"]
    for key in ("WorkingDirectory", "ProcessType", "EnvironmentVariables"):
        assert ours[key] == probe[key], key
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"
    # Suffix comparisons only, so the assertion holds on CI's root too.
    assert ours["StandardOutPath"].endswith("logs/phase37_r1b.out")
    assert ours["StandardErrorPath"].endswith("logs/phase37_r1b.err")
    for key in ("StandardOutPath", "StandardErrorPath"):
        assert ours[key] != probe[key]


def test_main_parses_the_plist_arguments(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # main chdirs to the repo root; monkeypatch restores the cwd
    seen = []
    monkeypatch.setattr(phase37_r1b, "run", lambda **kw: seen.append(kw))
    phase37_r1b.main(_plist(_PLIST)["ProgramArguments"][4:])
    assert seen == [{}]


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_every_phase37_r1b_function_has_a_cpu_test(tmp_path):
    real = _SCRIPTS / "phase37_r1b.py"
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _untested_functions("phase37_r1b", source, test_source) == []
    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase37_r1b", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before
