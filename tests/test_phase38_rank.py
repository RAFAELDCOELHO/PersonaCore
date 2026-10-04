"""Plan 38-06: the E5 rank driver (scripts/phase38_rank.py), part 1, tested on CPU only.

The device work (the device resolve, the adapter digests, the prefix models, the NLL instrument) is
monkeypatched; everything else is the driver's own code against tmp_path roots, ledgers and
heartbeats. What this file proves:
- D-17 / D-23: every refusal runs BEFORE the ledger start line and writes nothing; the committed
  stop is require_launch("E5"), no second rule;
- D-21: the 8 readings are checked against the approval, the committed cap stays 6, and the caps
  call never gets prefixes;
- D-20: the three SHA-256 checks (persona adapter, ordered_prefix components, M2 adapter);
- D-18: the 64 committed ranks gate the run BEFORE any minted value is scored; one mismatch is
  GATE_FAILED and scores nothing minted;
- D-08 / D-31: each maximum set is scored once per reading, one value per NLL call, into a
  write-once sidecar per reading;
- RANK-03: no scripts/phase38_*.py re-implements the rank or the NLL.

No test reads a file under checkpoints/ (gitignored, absent on ubuntu CI): the digests are stubbed
and the gitignored run inputs are tmp stand-ins. Nothing here touches the real ledger, results/ or
data/phase38_rank_*.
"""

import ast
import contextlib
import datetime
import hashlib
import inspect
import json
import pathlib
import re
import subprocess
import sys
import types

import pytest

_REPO = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TESTS = str(_REPO / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase14_factset  # noqa: E402  (scripts/ is not a package)
import phase14_recall  # noqa: E402  (same)
import phase18_extraction  # noqa: E402  (same)
import phase19_erasure  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same; never aliased)
import phase36_probe  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same; never aliased)
import phase38_rank  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase38_sizes_prereg  # noqa: E402  (same)

from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402

READINGS = phase38_prereg.READINGS
SLOTS = phase38_prereg.SLOTS
TAUGHT = {fact.slot: fact.value for fact in phase14_factset.LOCKED_FACTS}


def _real_sidecars():
    # _REPO, not phase38_rank._ROOT: some tests patch _ROOT to a rig root.
    return sorted((_REPO / "data").glob("phase38_rank_*"))


_REAL_IDENTITY = _REPO / "data" / "phase38_rehearsal.json"


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    sidecars = _real_sidecars()
    identity = _REAL_IDENTITY.exists()  # D-34: no test creates or deletes the real identity
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _real_sidecars() == sidecars
    assert _REAL_IDENTITY.exists() == identity


def _read(rel):
    return json.loads((_REPO / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gate_ranks():
    return phase38_prereg.committed_gate_ranks()


@pytest.fixture(scope="module")
def references():
    return {slot: list(phase18_extraction.reference_set_for(slot)) for slot in SLOTS}


@pytest.fixture(scope="module")
def committed_digests():
    return {
        "persona_adapter": _read(phase38_prereg.CURVE_RECORD)["adapter_in_sha256"],
        "m2_adapter": _read(phase38_prereg.RETRAIN_SCORES)["retrain_scores"]["adapter_sha256"],
    }


class FakeModel:
    def __init__(self, reading):
        self.reading = reading


def _offset(reading, value):
    """A deterministic per-(reading, value) offset in (-0.5, 0.5), never exactly 0."""
    digest = hashlib.sha256(f"{reading}|{value}".encode()).hexdigest()
    return (int(digest[:8], 16) / 2**32 - 0.5) or 0.25


def _fake_table(gate_ranks, references):
    """Taught 1.0; the first (committed rank - 1) other references in string order 0.5, the rest
    2.0: rank_in_prefix then reproduces every committed rank exactly."""
    table = {}
    for reading in READINGS:
        for slot in SLOTS:
            members = sorted(r for r in references[slot] if r != TAUGHT[slot])
            rank = gate_ranks[reading][slot]["rank"]
            for i, member in enumerate(members):
                table[(reading, slot, member)] = 0.5 if i < rank - 1 else 2.0
            table[(reading, slot, TAUGHT[slot])] = 1.0
    return table


@pytest.fixture
def rig(tmp_path, monkeypatch, gate_ranks, references, committed_digests):
    """The run fixture: a tmp root, tmp ledger/heartbeat, the device work stubbed."""
    (tmp_path / "results").mkdir()
    (tmp_path / "data").mkdir()
    paths = {"ledger_path": tmp_path / "ledger.jsonl", "heartbeat_path": tmp_path / "hb.jsonl"}
    rig = types.SimpleNamespace(
        root=tmp_path,
        paths=paths,
        dirty=[],
        launches=[],
        models=[],
        log=[],
        crash=None,
        table=_fake_table(gate_ranks, references),
        cpu_table={},
        digests=dict(committed_digests),
    )
    # The GITIGNORED run inputs (absent on ubuntu CI) are tmp stand-ins; tracked ones stay real.
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in ("CONVBASE_SLIM", "ADAPTER_PATH"):
        stand_in = inputs / name
        stand_in.write_bytes(b"stand-in")
        monkeypatch.setattr(phase14_recall, name, stand_in)
    m2 = inputs / "m2_adapter"
    m2.write_bytes(b"stand-in")
    monkeypatch.setattr(phase38_rank, "m2_adapter_path", lambda: m2)
    monkeypatch.setattr(phase38_rank, "_device", lambda: "mps")
    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", lambda **kw: rig.dirty.append(kw))
    monkeypatch.setattr(phase38_rank, "adapter_digests", lambda: dict(rig.digests))

    def require_launch(front, **kw):
        rig.launches.append((front, kw))
        return {"front": front, "spent_seconds": {front: 0.0}, "total_seconds": 0.0, "lifted": ()}

    monkeypatch.setattr(phase36_ledger, "require_launch", require_launch)

    @contextlib.contextmanager
    def reading_model(reading, device):
        rig.models.append((reading, device))
        yield FakeModel(reading), "tok"

    monkeypatch.setattr(phase38_rank, "reading_model", reading_model)

    def nll(model, tok, device, *, slot, value):
        rig.log.append((model.reading, slot, value))
        if rig.crash is not None and rig.crash(model.reading, slot, value):
            raise RuntimeError("scorer died mid-scoring")
        if device == "cpu" and (model.reading, slot, value) in rig.cpu_table:
            return rig.cpu_table[(model.reading, slot, value)]
        return rig.table.get((model.reading, slot, value), 1.0 + _offset(model.reading, value))

    monkeypatch.setattr(phase19_erasure, "value_span_nll_mean", nll)
    return rig


def _lines(rig):
    return phase36_ledger.read_ledger(rig.paths["ledger_path"])


# =================================================================================================
# (1) The module's own helpers: these run unpatched.
# =================================================================================================


def test_prove_sha_now_and_paths(tmp_path):
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] broken$"):
        phase38_rank._prove(False, "broken")
    phase38_rank._prove(True, "never raised")
    blob = tmp_path / "b.bin"
    blob.write_bytes(b"e5")
    assert phase38_rank._sha256(blob) == hashlib.sha256(b"e5").hexdigest()
    assert datetime.datetime.fromisoformat(phase38_rank._now()).tzinfo is not None
    assert phase38_rank.RUN_ID == "v6/38/E5/rank" == phase36_ledger.run_id(38, "E5", "rank")
    assert phase38_rank.FRONT == "E5"
    data = tmp_path / "data"
    assert phase38_rank.run_sidecar(tmp_path) == data / "phase38_rank_run.json"
    assert phase38_rank.gate_sidecar(tmp_path) == data / "phase38_rank_gate.json"
    assert phase38_rank.cpu_sidecar(tmp_path) == data / "phase38_rank_cpu.json"
    assert phase38_rank.nll_sidecar(tmp_path, "M2") == data / "phase38_rank_nll_M2.json"
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\]"):
        phase38_rank.nll_sidecar(tmp_path, "k7")
    outputs = phase38_rank.outputs(tmp_path)
    assert outputs[0] == tmp_path / phase38_prereg.RANK_RECORD
    assert len(outputs) == len(set(outputs)) == 1 + 3 + len(READINGS)
    assert all(phase38_rank.nll_sidecar(tmp_path, r) in outputs for r in READINGS)


def test_module_digests_are_the_repo_bytes():
    digests = phase38_rank.module_sha256()
    assert tuple(digests) == phase38_rank.MODULES
    assert "scripts/phase38_rank.py" in digests and "scripts/phase18_extraction.py" in digests
    for rel, digest in digests.items():
        assert digest == hashlib.sha256((_REPO / rel).read_bytes()).hexdigest(), rel


def test_device_is_the_strict_preflight_device(monkeypatch):
    import personacore.preflight

    seen = []
    monkeypatch.setattr(
        personacore.preflight,
        "preflight_device",
        lambda **kw: seen.append(kw) or {"device": "mps"},
    )
    assert phase38_rank._device() == "mps"
    assert seen == [{"strict": True}]


def test_m2_adapter_path_resolves_from_the_constants():
    path = phase38_rank.m2_adapter_path()
    assert pathlib.Path(path).as_posix().endswith("checkpoints/phase19_erase_reference_adapter.pt")


def test_run_inputs_are_the_readers_constants(rig):
    inputs = phase38_rank.run_inputs()
    gitignored = (
        phase14_recall.CONVBASE_SLIM,
        phase14_recall.ADAPTER_PATH,
        phase14_recall.TOKENIZER_PATH,
        phase38_rank.m2_adapter_path(),
    )
    assert inputs[:4] == gitignored
    tracked = [pathlib.Path(p).relative_to(_REPO).as_posix() for p in inputs[4:]]
    assert tracked[0] == phase38_prereg.MINTING_RECORD
    for rel in (
        phase38_prereg.CURVE_RECORD,
        phase38_prereg.ERASED_RECORD,
        phase38_prereg.KSTAR_SUMMARY,
        phase38_prereg.TARGET_SCORES,
        phase38_prereg.RETRAIN_RECORD,
        phase38_prereg.RETRAIN_SCORES,
        phase38_prereg.ADAPTER_OFF_RECORD,
        phase38_prereg.ADAPTER_ON_RECORD,
        phase38_prereg.PROBE_E1_RECORD,
    ):
        assert rel in tracked
    assert all(_git("ls-files", "--error-unmatch", rel) == rel for rel in tracked)


def test_adapter_digests_hash_the_two_adapter_files(tmp_path, monkeypatch):
    persona, m2 = tmp_path / "persona.bin", tmp_path / "m2.bin"
    persona.write_bytes(b"persona")
    m2.write_bytes(b"m2")
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", persona)
    monkeypatch.setattr(phase38_rank, "m2_adapter_path", lambda: m2)
    assert phase38_rank.adapter_digests() == {
        "persona_adapter": hashlib.sha256(b"persona").hexdigest(),
        "m2_adapter": hashlib.sha256(b"m2").hexdigest(),
    }


def test_reconstruction_checks_prove_the_three_digests(rig, committed_digests):
    checked = phase38_rank.reconstruction_checks()
    assert checked == {
        **committed_digests,
        "components_sha256": _read(phase38_prereg.PROBE_E1_RECORD)["configuration"][
            "components_sha256"
        ],
    }
    assert len(phase36_probe.e1_components()) == 78 == phase38_prereg.PREFIXES[-1]


# =================================================================================================
# (2) The scoring plan, the gate rows, the scorer and the reading models.
# =================================================================================================


def test_scoring_plan_reads_the_committed_minting_record():
    record = _read(phase38_prereg.MINTING_RECORD)
    plan = phase38_rank.scoring_plan()
    assert tuple(plan) == SLOTS
    for slot, row in plan.items():
        size = phase38_sizes_prereg.E5_SET_SIZES[slot]
        assert row["size"] == size
        assert len(row["minted"]) == size - 1
        assert row["minted"] == record["slots"][slot]["cleared"][: size - 1]
        assert row["taught"] == TAUGHT[slot]
        assert row["sizes"] == list(phase38_prereg.nested_sizes(size))
    small = phase38_rank.scoring_plan(slots=("pet_name",), max_size=8)
    assert list(small) == ["pet_name"]
    assert len(small["pet_name"]["minted"]) == 7 and small["pet_name"]["sizes"] == [8]


def test_gate_reading_reproduces_every_committed_rank(rig, references, gate_ranks):
    for reading in READINGS:
        nll_by_slot = {
            slot: {v: rig.table[(reading, slot, v)] for v in references[slot]} for slot in SLOTS
        }
        rows = phase38_rank.gate_reading(reading, nll_by_slot)
        assert set(rows) == set(SLOTS)
        for slot, row in rows.items():
            assert row["equal"] is True, (reading, slot, row)
            assert row["rank"] == row["committed_rank"] == gate_ranks[reading][slot]["rank"]
            assert row["n_references"] == len(references[slot])
            assert row["taught_nll"] == 1.0
            assert row["abs_nll_diff"] == abs(1.0 - gate_ranks[reading][slot]["nll_mean"])
    flipped = {slot: {v: rig.table[("k0", slot, v)] for v in references[slot]} for slot in SLOTS}
    flipped["street"][TAUGHT["street"]] = 3.0
    rows = phase38_rank.gate_reading("k0", flipped)
    assert rows["street"]["equal"] is False
    assert rows["street"]["rank"] == len(references["street"])
    assert all(rows[slot]["equal"] for slot in SLOTS if slot != "street")


def test_score_values_calls_the_instrument_once_per_value(monkeypatch, capsys):
    seen = []

    def nll(model, tok, device, *, slot, value):
        print("the pin's own stdout")
        seen.append((model, tok, device, slot, value))
        return float(len(value))

    monkeypatch.setattr(phase19_erasure, "value_span_nll_mean", nll)
    state = {"point": "p", "stage": "s", "shape": None, "draw_index": None}
    out = phase38_rank.score_values("m", "t", "mps", "pet_name", ["a", "bbb", "cc"], state)
    assert out == [1.0, 3.0, 2.0]
    assert seen == [("m", "t", "mps", "pet_name", v) for v in ("a", "bbb", "cc")]
    assert state["shape"] == "pet_name" and state["draw_index"] == 2
    assert capsys.readouterr().out == ""  # silenced: no reading reaches the log


def test_reading_model_builds_each_reading_from_the_pinned_loaders(monkeypatch):
    import torch

    import personacore.lora

    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    built, disabled = [], []

    def adapted(device, k):
        built.append(("adapted", device, k))
        return FakeModel(f"k{k}"), "tok", "forbid"

    def loaded(device, adapter_path=None):
        built.append(("loaded", device, adapter_path))
        return FakeModel("M2"), "cfg", "tok", "forbid", "artifact"

    @contextlib.contextmanager
    def off(model):
        disabled.append(("in", model.reading))
        yield
        disabled.append(("out", model.reading))

    monkeypatch.setattr(phase36_probe, "adapted_model", adapted)
    monkeypatch.setattr(phase14_recall, "load_adapted_model", loaded)
    monkeypatch.setattr(personacore.lora, "adapter_disabled", off)
    for reading in READINGS:
        with phase38_rank.reading_model(reading, "cpu") as (model, tok):
            assert tok == "tok"
            assert model.reading == ("k0" if reading == "adapter_off" else reading)
            if reading == "adapter_off":
                assert disabled == [("in", "k0")]
        if reading == "adapter_off":
            assert disabled == [("in", "k0"), ("out", "k0")]
    m2 = phase38_rank.m2_adapter_path()
    assert built == [
        *(("adapted", "cpu", k) for k in phase38_prereg.PREFIXES),
        ("loaded", "cpu", m2),
        ("adapted", "cpu", 0),
    ]
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\]"):
        with phase38_rank.reading_model("k7", "cpu"):
            pass


# =================================================================================================
# (3) preflight: every refusal before the ledger start line, nothing written (D-17, D-23).
# =================================================================================================


def test_preflight_alone_writes_nothing_and_reports_the_gate(rig, committed_digests, capsys):
    pre = phase38_rank.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    out = capsys.readouterr().out
    assert out.startswith(f"PREFLIGHT OK {_git('rev-parse', 'HEAD')} device=mps readings=8 ")
    assert f"projection_h={phase38_prereg.E5_PROJECTION_HOURS}" in out
    assert f"stop_h={phase38_prereg.E5_STOP_HOURS}" in out
    assert "spent_E5_s=0.0" in out
    assert pre["device"] == "mps" and pre["readings"] == READINGS
    assert pre["git_sha"] == _git("rev-parse", "HEAD")
    assert pre["module_sha256"] == phase38_rank.module_sha256()
    assert pre["reconstruction"]["persona_adapter"] == committed_digests["persona_adapter"]
    assert rig.launches == [("E5", {"ledger_path": rig.paths["ledger_path"]})]
    assert [d["pathspec"] for d in rig.dirty] == [phase38_rank.LAUNCH_PATHSPEC]
    assert rig.dirty[0]["cwd"] == phase38_rank._REPO
    assert not rig.paths["ledger_path"].exists()
    assert sorted(p.name for p in rig.root.iterdir()) == ["data", "inputs", "results"]
    assert list((rig.root / "data").iterdir()) == []


def test_preflight_with_the_real_require_launch_on_a_tmp_ledger(rig, monkeypatch, capsys):
    """The committed D-13 stops through the REAL require_launch, on an empty tmp ledger."""
    monkeypatch.undo()  # drop every rig stub, then re-apply all but require_launch
    monkeypatch.setattr(phase14_recall, "CONVBASE_SLIM", rig.root / "inputs" / "CONVBASE_SLIM")
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", rig.root / "inputs" / "ADAPTER_PATH")
    monkeypatch.setattr(phase38_rank, "m2_adapter_path", lambda: rig.root / "inputs" / "m2_adapter")
    monkeypatch.setattr(phase38_rank, "_device", lambda: "mps")
    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", lambda **kw: None)
    monkeypatch.setattr(phase38_rank, "adapter_digests", lambda: dict(rig.digests))
    pre = phase38_rank.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    assert pre["gate"]["front"] == "E5" and pre["gate"]["lifted"] == ()
    assert capsys.readouterr().out.startswith("PREFLIGHT OK")
    assert not rig.paths["ledger_path"].exists()


def _plant_output(index):
    def plant(rig, monkeypatch):
        path = phase38_rank.outputs(rig.root)[index]
        path.write_text("{}", encoding="utf-8")

    plant.__name__ = f"output_{index}"
    return plant


def _refuse_dirty(rig, monkeypatch):
    def dirty(**kw):
        raise SystemExit("[phase38_rank] dirty tree")

    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", dirty)


def _refuse_unknown_sha(rig, monkeypatch):
    monkeypatch.setattr(phase38_rank, "git_sha", lambda: "unknown")


def _refuse_launch(rig, monkeypatch):
    def cut(front, **kw):
        raise SystemExit("[phase36_ledger] PAUSE")

    monkeypatch.setattr(phase36_ledger, "require_launch", cut)


def _refuse_approval(rig, monkeypatch):
    monkeypatch.setattr(phase38_prereg, "APPROVED_E5_PREFIXES", 7)


def _refuse_committed_cap(rig, monkeypatch):
    monkeypatch.setattr(phase38_prereg, "COMMITTED_PREFIX_CAP", 8)


def _refuse_cpu_on_the_real_root(rig, monkeypatch):
    monkeypatch.setattr(phase38_rank, "_ROOT", rig.root)
    monkeypatch.setattr(phase38_rank, "_device", lambda: "cpu")


def _refuse_untracked_input(rig, monkeypatch):
    monkeypatch.setattr(
        phase38_rank, "TRACKED_INPUTS", (*phase38_rank.TRACKED_INPUTS, "results/phase38_none.json")
    )


def _refuse_missing_gitignored_input(rig, monkeypatch):
    monkeypatch.setattr(phase14_recall, "CONVBASE_SLIM", rig.root / "missing" / "convbase")


def _refuse_missing_m2(rig, monkeypatch):
    monkeypatch.setattr(phase38_rank, "m2_adapter_path", lambda: rig.root / "missing" / "m2")


def _refuse_missing_tracked_input(rig, monkeypatch):
    monkeypatch.setattr(phase38_prereg, "PROBE_E1_RECORD", "results/phase36_probe_none.json")


def _refuse_persona_digest(rig, monkeypatch):
    rig.digests["persona_adapter"] = "0" * 64


def _refuse_m2_digest(rig, monkeypatch):
    rig.digests["m2_adapter"] = "0" * 64


def _refuse_components_digest(rig, monkeypatch):
    monkeypatch.setattr(phase38_prereg, "components_sha256", lambda components: "0" * 64)


_REFUSALS = [
    *((_plant_output(i), r"exists: the E5 scoring has already run") for i in range(12)),
    (_refuse_dirty, r"dirty tree"),
    (_refuse_unknown_sha, r"could not read HEAD"),
    (_refuse_launch, r"PAUSE"),
    (_refuse_approval, r"D-21 approval"),
    (_refuse_committed_cap, r"committed E5 prefix cap is 6, not 8"),
    (_refuse_cpu_on_the_real_root, r"\(D-17\)"),
    (_refuse_untracked_input, r"phase38_none\.json is not tracked"),
    (_refuse_missing_gitignored_input, r"convbase is missing"),
    (_refuse_missing_m2, r"m2 is missing"),
    (_refuse_missing_tracked_input, r"phase36_probe_none\.json is missing"),
    (_refuse_persona_digest, r"persona adapter is not"),
    (_refuse_m2_digest, r"M2 adapter is not"),
    (_refuse_components_digest, r"components are not"),
]


@pytest.mark.parametrize(("plant", "reason"), _REFUSALS, ids=[p.__name__ for p, _ in _REFUSALS])
def test_preflight_refusals_write_no_ledger_line(rig, monkeypatch, plant, reason):
    plant(rig, monkeypatch)
    with pytest.raises(SystemExit, match=r"^\[(phase38_rank|phase36_ledger)\] .*" + reason):
        phase38_rank.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    assert not rig.paths["ledger_path"].exists()
    assert not rig.paths["heartbeat_path"].exists()


def test_the_refusals_cover_every_output():
    assert len(phase38_rank.outputs(pathlib.Path("x"))) == 12


def test_an_open_attempt_refuses_and_a_closed_one_does_not(rig):
    ledger = rig.paths["ledger_path"]
    rid, kw = phase38_rank.RUN_ID, {"phase": 38, "front": "E5", "ledger_path": ledger}
    phase36_ledger.append("start", run_id=rid, **kw)
    before = ledger.read_bytes()
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*open attempt"):
        phase38_rank.preflight(root=rig.root, ledger_path=ledger)
    assert ledger.read_bytes() == before
    phase36_ledger.append("end", run_id=rid, record=phase38_prereg.RANK_RECORD, **kw)
    closed = ledger.read_bytes()
    assert phase38_rank.preflight(root=rig.root, ledger_path=ledger)["device"] == "mps"
    assert ledger.read_bytes() == closed


def test_the_first_io_free_checks_refuse_on_the_real_root(tmp_path):
    """The D-21 readings check and the D-17 device check come first: the real root is safe here
    whether or not the real record exists."""
    ledger = tmp_path / "ledger.jsonl"
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*D-21"):
        phase38_rank.preflight(ledger_path=ledger, device="mps", readings=("k0", "k5"))
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*D-17"):
        phase38_rank.preflight(ledger_path=ledger, device="cpu")
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*D-17"):
        phase38_rank.preflight(root=_REPO / "scratch_inside_repo", ledger_path=ledger, device="cpu")
    assert not ledger.exists()


def test_a_rehearsal_root_accepts_cpu(rig, monkeypatch):
    monkeypatch.setattr(phase38_rank, "_device", lambda: "cpu")
    pre = phase38_rank.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    assert pre["device"] == "cpu"
    assert not rig.paths["ledger_path"].exists()


def test_the_driver_imports_without_torch():
    import subprocess

    probe = (
        "import sys; sys.path[:0] = ['scripts', 'src']; import phase38_rank as r; "
        "print(r.RUN_ID, r.FRONT, 'torch' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_REPO, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["v6/38/E5/rank", "E5", "False"], out.stdout


def test_private_helpers(tmp_path, monkeypatch):
    sidecar = tmp_path / "data" / "once.json"
    phase38_rank._write_once(sidecar, {"b": 1, "a": [2]})
    assert json.loads(sidecar.read_text(encoding="utf-8")) == {"a": [2], "b": 1}
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*write-once"):
        phase38_rank._write_once(sidecar, {})
    assert phase38_rank._json(phase38_prereg.CURVE_RECORD) == _read(phase38_prereg.CURVE_RECORD)
    assert phase38_rank._taught() == TAUGHT
    assert phase38_rank._is_real(phase38_rank._ROOT) is True
    assert phase38_rank._is_real(_REPO / "data" / "scratch") is True  # inside the repo
    assert phase38_rank._is_real(tmp_path) is False
    monkeypatch.setattr(phase38_rank, "_ROOT", tmp_path)
    assert phase38_rank._is_real(tmp_path) is True


# =================================================================================================
# (4) run(): ledger start, the D-18 gate over all 8 readings, the one scoring pass, the sidecars,
# the ledger end. All on the fake rig, tmp root, tmp ledger, tmp heartbeat.
# =================================================================================================


def _sidecar(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _split_log(rig, references):
    """(gate entries, scoring entries): the gate part is every reading's reference scorings."""
    n_gate = sum(len(references[slot]) for slot in SLOTS) * len(READINGS)
    return rig.log[:n_gate], rig.log[n_gate:]


def test_run_scores_the_full_shape_gate_first(rig, references, capsys):
    status = phase38_rank.run(root=rig.root, **rig.paths)
    assert status == "SCORED"
    assert "RUN SCORED" in capsys.readouterr().out
    lines = _lines(rig)
    assert [(x["event"], x["run_id"]) for x in lines] == [
        ("start", phase38_rank.RUN_ID),
        ("end", phase38_rank.RUN_ID),
    ]
    assert lines[1]["record"] == phase38_prereg.RANK_RECORD and lines[1]["front"] == "E5"
    # D-18: the 8 x 8 gate rows, all equal, before any minted value.
    gate = _sidecar(phase38_rank.gate_sidecar(rig.root))
    assert gate["passed"] is True and gate["run_id"] == phase38_rank.RUN_ID
    assert set(gate["rows"]) == set(READINGS)  # atomic_write_json sorts keys
    assert all(set(rows) == set(SLOTS) for rows in gate["rows"].values())
    assert all(row["equal"] for rows in gate["rows"].values() for row in rows.values())
    gate_part, scoring_part = _split_log(rig, references)
    assert gate_part == [
        (reading, slot, value)
        for reading in READINGS
        for slot in SLOTS
        for value in references[slot]
    ]
    # D-08 / D-31: each (reading, slot) scores taught + the minted prefix exactly once, in order.
    plan = phase38_rank.scoring_plan()
    assert scoring_part == [
        (reading, slot, value)
        for reading in READINGS
        for slot in SLOTS
        for value in [plan[slot]["taught"], *plan[slot]["minted"]]
    ]
    assert [r for r, _ in rig.models] == [*READINGS, *READINGS]
    assert {d for _, d in rig.models} == {"mps"}
    for reading in READINGS:
        blob = _sidecar(phase38_rank.nll_sidecar(rig.root, reading))
        assert blob["reading"] == reading and set(blob["slots"]) == set(SLOTS)
        for slot, row in blob["slots"].items():
            size = phase38_sizes_prereg.E5_SET_SIZES[slot]
            assert row["taught"] == TAUGHT[slot] and row["taught_nll"] == 1.0
            assert len(row["minted_nll"]) == size - 1 == len(row["minted"])
            assert row["minted"] == plan[slot]["minted"]
            assert row["minted_nll"] == [
                rig.table.get((reading, slot, v), 1.0 + _offset(reading, v)) for v in row["minted"]
            ]
    run = _sidecar(phase38_rank.run_sidecar(rig.root))
    assert run["status"] == "SCORED"
    assert set(phase38_rank.RUN_PROVENANCE_KEYS) <= set(run)
    assert run["git_sha_at_launch"] == run["git_sha_at_end"] == _git("rev-parse", "HEAD")
    assert run["head_moved_during_run"] is False and run["device"] == "mps"
    assert run["module_sha256_at_launch"] == phase38_rank.module_sha256()
    assert run["reconstruction"] == phase38_rank.reconstruction_checks()
    assert run["sizes"] == {slot: plan[slot]["size"] for slot in SLOTS}
    assert run["gate_sha256"] == phase38_rank._sha256(phase38_rank.gate_sidecar(rig.root))
    assert run["nll_sha256"] == {
        r: phase38_rank._sha256(phase38_rank.nll_sidecar(rig.root, r)) for r in READINGS
    }
    beats = [json.loads(t) for t in rig.paths["heartbeat_path"].read_text().splitlines()]
    assert beats and {b["point"] for b in beats} == {phase38_rank.RUN_ID}
    assert not (rig.root / phase38_prereg.RANK_RECORD).exists()  # emit is plan 38-07's


def test_a_gate_mismatch_is_gate_failed_and_scores_nothing_minted(rig, references):
    rig.table[("k32", "street", TAUGHT["street"])] = 3.0
    assert phase38_rank.run(root=rig.root, **rig.paths) == "GATE_FAILED"
    gate = _sidecar(phase38_rank.gate_sidecar(rig.root))
    assert gate["passed"] is False
    assert [
        (r, s) for r, rows in gate["rows"].items() for s, x in rows.items() if not x["equal"]
    ] == [("k32", "street")]
    assert all(value in references[slot] for _, slot, value in rig.log)  # zero minted values
    assert [r for r, _ in rig.models] == list(READINGS)  # no scoring pass
    assert not any(phase38_rank.nll_sidecar(rig.root, r).exists() for r in READINGS)
    run = _sidecar(phase38_rank.run_sidecar(rig.root))
    assert run["status"] == "GATE_FAILED" and run["nll_sha256"] == {}
    assert [x["event"] for x in _lines(rig)] == ["start", "end"]


def test_the_real_root_refuses_a_partial_shape_before_any_ledger_line(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    for kw in ({"readings": ("k0",)}, {"slots": ("pet_name",)}, {"max_size": 8}):
        with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*full"):
            phase38_rank.run(ledger_path=ledger, heartbeat_path=tmp_path / "hb", **kw)
        with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*full"):
            phase38_rank.run(root=_REPO / "scratch", ledger_path=ledger, **kw)
    assert not ledger.exists() and not (tmp_path / "hb").exists()


def test_a_rehearsal_root_runs_a_partial_shape(rig):
    shape = {"readings": ("k0", "k78"), "slots": ("pet_name",), "max_size": 8}
    assert phase38_rank.run(root=rig.root, **rig.paths, **shape) == "SCORED"
    written = sorted(p.name for p in (rig.root / "data").iterdir())
    assert written == [
        "phase38_rank_gate.json",
        "phase38_rank_nll_k0.json",
        "phase38_rank_nll_k78.json",
        "phase38_rank_run.json",
    ]
    for reading in ("k0", "k78"):
        blob = _sidecar(phase38_rank.nll_sidecar(rig.root, reading))
        assert list(blob["slots"]) == ["pet_name"]
        assert len(blob["slots"]["pet_name"]["minted_nll"]) == 7
    run = _sidecar(phase38_rank.run_sidecar(rig.root))
    assert run["readings"] == ["k0", "k78"] and run["slots"] == ["pet_name"]
    assert run["max_size"] == 8 and run["sizes"] == {"pet_name": 8}


def test_a_commit_landing_mid_run_is_named(rig, monkeypatch):
    heads = iter(["a" * 40, "b" * 40])
    monkeypatch.setattr(phase38_rank, "git_sha", lambda: next(heads))
    phase38_rank.run(root=rig.root, **rig.paths, readings=("k0",), slots=("pet_name",), max_size=8)
    run = _sidecar(phase38_rank.run_sidecar(rig.root))
    assert (run["git_sha_at_launch"], run["git_sha_at_end"]) == ("a" * 40, "b" * 40)
    assert run["head_moved_during_run"] is True


def test_a_crash_mid_scoring_leaves_an_open_start_that_reconcile_closes(rig, references):
    """Rehearsal: the scorer dies at k16's first minted value, after k0 and k8 landed."""
    rig.crash = lambda reading, slot, value: reading == "k16" and value not in references[slot]
    with pytest.raises(RuntimeError, match="scorer died mid-scoring"):
        phase38_rank.run(root=rig.root, **rig.paths)
    landed = {r: phase38_rank.nll_sidecar(rig.root, r) for r in ("k0", "k8")}
    digests = {r: phase38_rank._sha256(p) for r, p in landed.items()}
    assert not phase38_rank.nll_sidecar(rig.root, "k16").exists()
    assert not phase38_rank.run_sidecar(rig.root).exists()
    lines = _lines(rig)
    assert [(x["event"], x["run_id"]) for x in lines] == [("start", phase38_rank.RUN_ID)]
    assert phase38_rank.RUN_ID in phase36_ledger.open_runs(lines)
    phase36_ledger.reconcile(**rig.paths)
    reconciled = _lines(rig)
    assert [x["event"] for x in reconciled] == ["start", "lost"]
    assert reconciled[1]["flag"] == phase36_ledger.LOST_FLAG
    assert phase36_ledger.open_runs(reconciled) == {}
    for reading, path in landed.items():  # intact after the crash and the reconcile
        assert phase38_rank._sha256(path) == digests[reading]
        assert len(_sidecar(path)["slots"]) == len(SLOTS)
    with pytest.raises(SystemExit, match=r"phase38_rank_gate\.json exists"):
        phase38_rank.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    assert _lines(rig) == reconciled


def test_a_refusal_inside_run_writes_no_ledger_line(rig, monkeypatch):
    monkeypatch.setattr(phase38_rank, "git_sha", lambda: "unknown")
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*HEAD"):
        phase38_rank.run(root=rig.root, **rig.paths)
    assert not rig.paths["ledger_path"].exists()
    assert not rig.paths["heartbeat_path"].exists()
    assert rig.log == [] and rig.models == []


# =================================================================================================
# (4b) crosscheck, build_record, emit (plan 38-07 Task 1): the record arithmetic through the
# phase38_prereg definitions, recomputed here from the NLL sidecars.
# =================================================================================================


def _scored(rig, **shape):
    assert phase38_rank.run(root=rig.root, **rig.paths, **shape) == "SCORED"
    phase38_rank.crosscheck(root=rig.root)
    return _sidecar(phase38_rank.run_sidecar(rig.root))


def _recomputed_curve(row, sizes, exclude=()):
    nll = {row["taught"]: row["taught_nll"], **dict(zip(row["minted"], row["minted_nll"]))}
    out = {}
    for size in sizes:
        members = [v for i, v in enumerate(row["minted"][: size - 1]) if i not in exclude]
        rank = phase38_prereg.rank_in_prefix(nll, row["taught"], members)
        n = len(members) + 1
        out[str(size)] = {"size": n, "rank": rank, "bits": phase38_prereg.exposure_bits(rank, n)}
    return out


def _jsonable(blob):
    return json.loads(json.dumps(blob))


def test_curve_for_reads_the_nested_prefixes():
    curve = phase38_rank.curve_for("t", 1.0, ["a", "b", "c"], [0.5, 2.0, 0.7], [2, 4])
    assert curve == {
        "2": {"size": 2, "rank": 2, "bits": 0.0},
        "4": {"size": 4, "rank": 3, "bits": 2 - phase38_prereg.math.log2(3)},
    }
    trimmed = phase38_rank.curve_for(
        "t", 1.0, ["a", "b", "c"], [0.5, 2.0, 0.7], [2, 4], exclude=[0]
    )
    assert trimmed == {
        "2": {"size": 1, "rank": 1, "bits": 0.0},
        "4": {"size": 3, "rank": 2, "bits": phase38_prereg.math.log2(3) - 1},
    }


def test_crosscheck_writes_the_cpu_sidecar_once(rig, capsys):
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*phase38_rank_run\.json is missing"):
        phase38_rank.crosscheck(root=rig.root)
    blob = _scored(rig)
    assert "CROSSCHECK DONE" in capsys.readouterr().out
    cpu = _sidecar(phase38_rank.cpu_sidecar(rig.root))
    assert cpu["device"] == "cpu" and "torch_version" in cpu
    assert [r for r, d in rig.models if d == "cpu"] == list(READINGS)
    gate = _sidecar(phase38_rank.gate_sidecar(rig.root))
    assert cpu["gate"] == {
        r: {s: row["rank"] for s, row in rows.items()} for r, rows in gate["rows"].items()
    }
    for reading in READINGS:
        side = _sidecar(phase38_rank.nll_sidecar(rig.root, reading))["slots"]
        for slot in SLOTS:
            sizes = list(phase38_prereg.nested_sizes(blob["sizes"][slot]))
            curve = _recomputed_curve(side[slot], sizes)
            assert cpu["ranks"][reading][slot] == {s: c["rank"] for s, c in curve.items()}
    before = phase38_rank.cpu_sidecar(rig.root).read_bytes()
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*phase38_rank_cpu\.json exists"):
        phase38_rank.crosscheck(root=rig.root)
    assert phase38_rank.cpu_sidecar(rig.root).read_bytes() == before


def test_emit_writes_the_record_once_through_the_prereg_definitions(rig, capsys):
    # cat_name at k0: every minted value below the taught one, so rank_0 = |R| at every size:
    # "moved" is UNREACHABLE_AT_SIZE and "left the top eighth" is ALREADY_AT_K0 (WR-01).
    cat_minted = phase38_rank.scoring_plan(slots=("cat_name",))["cat_name"]["minted"]
    rig.table.update({("k0", "cat_name", v): 0.1 for v in cat_minted})
    blob = _scored(rig)
    record = phase38_rank.emit(root=rig.root)
    assert f"EMITTED SCORED {rig.root / phase38_prereg.RANK_RECORD}" in capsys.readouterr().out
    on = _sidecar(rig.root / phase38_prereg.RANK_RECORD)
    assert on == _jsonable(record)
    assert (on["front"], on["run_id"], on["status"]) == ("E5", phase38_rank.RUN_ID, "SCORED")
    assert on["approval"] == _jsonable(phase38_prereg.approval_block())
    assert on["minting_record"] == {
        "path": phase38_prereg.MINTING_RECORD,
        "sha256": hashlib.sha256((_REPO / phase38_prereg.MINTING_RECORD).read_bytes()).hexdigest(),
    }
    assert on["set_sizes"] == blob["sizes"] and on["reconstruction"] == blob["reconstruction"]
    gate = _sidecar(phase38_rank.gate_sidecar(rig.root))
    assert on["gate"] == gate and on["committed_reference_sets"] == gate["rows"]
    assert on["descriptive_readings"] == ["M2", "adapter_off"]
    assert set(on["readings"]) == set(READINGS)
    sides = {r: _sidecar(phase38_rank.nll_sidecar(rig.root, r))["slots"] for r in READINGS}
    sizes = {s: list(phase38_prereg.nested_sizes(blob["sizes"][s])) for s in SLOTS}
    for reading in READINGS:
        assert set(on["readings"][reading]) == set(SLOTS)
        for slot in SLOTS:
            cell, side = on["readings"][reading][slot], sides[reading][slot]
            assert cell["curve"] == _recomputed_curve(side, sizes[slot])
            assert (cell["taught_nll"], cell["minted_nll"]) == (
                side["taught_nll"],
                side["minted_nll"],
            )
    a2 = phase38_prereg.a2_counts()
    for slot in SLOTS:
        counts, n = a2[slot]["counts"], a2[slot]["n_questions"]
        collapse = phase38_prereg.first_collapse(counts)
        damage = phase38_prereg.first_damage(counts, n)
        assert on["a2"][slot] == {
            "n_questions": n,
            "counts": {str(k): c for k, c in counts.items()},
            "first_collapse": collapse,
            "first_damage": damage,
            "margin": phase38_prereg.MARGIN,
        }
        assert set(on["events"][slot]) == {str(size) for size in sizes[slot]}
        for size in sizes[slot]:
            ranks = {
                k: on["readings"][f"k{k}"][slot]["curve"][str(size)]["rank"]
                for k in phase38_prereg.PREFIXES
            }
            rank_0 = ranks[0]
            expected = {
                "moved": (
                    {k: phase38_prereg.moved(r, rank_0) for k, r in ranks.items()},
                    phase38_prereg.moved_reachable(rank_0, size),
                ),
                "left_top_eighth": (
                    {k: phase38_prereg.left_top_eighth(r, size) for k, r in ranks.items()},
                    True,
                ),
            }
            events = on["events"][slot][str(size)]
            assert set(events) == set(expected)
            for name, (flags, reachable) in expected.items():
                first = phase38_prereg.first_event(flags)
                assert set(events[name]["flags"]) == {str(k) for k in phase38_prereg.PREFIXES}
                assert not {"M2", "adapter_off", "kM2"} & set(events[name]["flags"])  # D-16
                assert events[name] == {
                    "flags": {str(k): f for k, f in flags.items()},
                    "first": first,
                    "rank_0": rank_0,
                    "reachable": reachable,
                    "vs_collapse": phase38_prereg.relation(first, collapse, reachable=reachable),
                    "vs_damage": phase38_prereg.relation(first, damage, reachable=reachable),
                }
    for size in sizes["cat_name"]:
        cat = on["events"]["cat_name"][str(size)]
        assert cat["moved"]["rank_0"] == size
        assert cat["moved"]["vs_collapse"] == cat["moved"]["vs_damage"] == "UNREACHABLE_AT_SIZE"
        assert cat["left_top_eighth"]["vs_damage"] == "ALREADY_AT_K0"
    relations = {
        e[name][side]
        for by_size in on["events"].values()
        for e in by_size.values()
        for name in e
        for side in ("vs_collapse", "vs_damage")
    }
    assert relations - {"UNREACHABLE_AT_SIZE", "ALREADY_AT_K0"}  # the reachable path is exercised
    # D-27: the numeric slots without their distance-1 neighbours, descriptive.
    minting = _read(phase38_prereg.MINTING_RECORD)["slots"]
    numeric = {s for s in SLOTS if "neighbour_d1" in minting[s]}
    assert numeric == {"birth_year", "house_number"} == set(on["sensitivity_numeric"])
    for slot in numeric:
        excluded = set(minting[slot]["neighbour_d1"])
        sens = on["sensitivity_numeric"][slot]
        assert sens["descriptive"] is True
        for reading in READINGS:
            curve = _recomputed_curve(sides[reading][slot], sizes[slot], excluded)
            assert sens["curves"][reading] == curve
            assert any(c["size"] < int(s) for s, c in curve.items())
    # D-33
    audit = on["drop_formula_audit"]
    assert audit == _jsonable(phase38_prereg.drop_formula_audit(a2))
    assert audit["flips"] == [] and audit["exact_ties"] == [["person_name", 8]]
    # D-19, descriptive
    cpu = on["cpu_crosscheck"]
    assert cpu["criterion"] is False and cpu["device"] == "cpu"
    assert (cpu["differing"], cpu["differing_cells"]) == (0, [])
    assert cpu["cells"] == len(READINGS) * sum(len(v) for v in sizes.values())
    assert (cpu["gate_cells"], cpu["gate_differing"]) == (len(READINGS) * len(SLOTS), 0)
    assert on["cost"]["e5_stop_hours"] == phase38_prereg.E5_STOP_HOURS
    assert on["cost"]["e5_projection_hours"] == phase38_prereg.E5_PROJECTION_HOURS
    assert 0 <= on["cost"]["run_hours"] < 1
    prov = on["provenance"]
    assert prov["run"] == {key: blob[key] for key in phase38_rank.RUN_PROVENANCE_KEYS}
    assert prov["run"]["device"] == blob["device"] == "mps"
    assert prov["module_sha256_at_launch"] == blob["module_sha256_at_launch"]
    assert prov["module_sha256"] == phase38_rank.module_sha256()
    assert prov["modules_changed_since_launch"] == []
    assert prov["sidecar_sha256"]["cpu"] == phase38_rank._sha256(phase38_rank.cpu_sidecar(rig.root))
    # The helpers, called directly: build_record is a pure function of the sidecars.
    rebuilt = _jsonable(phase38_rank.build_record(rig.root))
    for blob_ in (rebuilt, on):
        blob_["provenance"].pop("written_utc")
    assert rebuilt == on
    assert _jsonable(phase38_rank._events(record["readings"], SLOTS, sizes, a2)) == on["events"]
    cpu_side = phase38_rank._load(phase38_rank.cpu_sidecar(rig.root))
    assert cpu_side == _sidecar(phase38_rank.cpu_sidecar(rig.root))
    block = phase38_rank._cpu_block(cpu_side, on["readings"], gate["rows"], SLOTS, sizes)
    assert block == on["cpu_crosscheck"]
    assert on["cost"]["run_hours"] == phase38_rank._hours(blob["started_utc"], blob["finished_utc"])
    assert phase38_rank._hours("2026-10-04T10:00:00+00:00", "2026-10-04T11:30:00+00:00") == 1.5
    before = (rig.root / phase38_prereg.RANK_RECORD).read_bytes()
    with pytest.raises(SystemExit, match=r"REFUSING to overwrite"):
        phase38_rank.emit(root=rig.root)
    assert (rig.root / phase38_prereg.RANK_RECORD).read_bytes() == before


def test_a_perturbed_cpu_nll_is_counted_and_a_subset_has_no_events(rig):
    value = phase38_rank.scoring_plan(slots=("pet_name",), max_size=8)["pet_name"]["minted"][0]
    mps = rig.table.get(("k0", "pet_name", value), 1.0 + _offset("k0", value))
    rig.cpu_table[("k0", "pet_name", value)] = 5.0 if mps < 1.0 else 0.0
    _scored(rig, readings=("k0",), slots=("pet_name",), max_size=8)
    record = phase38_rank.emit(root=rig.root)
    cpu = record["cpu_crosscheck"]
    assert (cpu["cells"], cpu["differing"], cpu["differing_cells"]) == (
        1,
        1,
        [["k0", "pet_name", 8]],
    )
    assert (cpu["gate_cells"], cpu["gate_differing"]) == (1, 0)
    assert record["events"] is None and "k8" in record["events_reason"]
    assert record["set_sizes"] == {"pet_name": 8}
    assert record["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}


def test_a_gate_failed_run_emits_the_gate_rows_only(rig):
    rig.table[("k32", "street", TAUGHT["street"])] = 3.0
    assert phase38_rank.run(root=rig.root, **rig.paths) == "GATE_FAILED"
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*not SCORED"):
        phase38_rank.crosscheck(root=rig.root)
    record = phase38_rank.emit(root=rig.root)  # no CPU sidecar needed
    assert record["status"] == "GATE_FAILED"
    assert record["gate"] == _sidecar(phase38_rank.gate_sidecar(rig.root))
    assert record["gate"]["passed"] is False
    assert not {"readings", "events", "sensitivity_numeric", "cpu_crosscheck", "a2"} & set(record)
    assert record["approval"] == phase38_prereg.approval_block()
    assert record["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
    assert (rig.root / phase38_prereg.RANK_RECORD).exists()


def test_emit_refusals_write_nothing(rig, monkeypatch):
    out = rig.root / phase38_prereg.RANK_RECORD
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*phase38_rank_run\.json is missing"):
        phase38_rank.emit(root=rig.root)
    shape = {"readings": ("k0", "k8"), "slots": ("pet_name",), "max_size": 8}
    assert phase38_rank.run(root=rig.root, **rig.paths, **shape) == "SCORED"
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*phase38_rank_cpu\.json is missing"):
        phase38_rank.emit(root=rig.root)
    phase38_rank.crosscheck(root=rig.root)
    for path in (phase38_rank.gate_sidecar(rig.root), phase38_rank.nll_sidecar(rig.root, "k8")):
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*not the bytes the run wrote"):
            phase38_rank.emit(root=rig.root)
        path.write_bytes(original)

    def dirty(**kw):
        raise SystemExit("[phase38_rank] dirty tree")

    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", dirty)
    with pytest.raises(SystemExit, match=r"dirty tree"):
        phase38_rank.emit(root=rig.root)
    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", lambda **kw: rig.dirty.append(kw))
    monkeypatch.setattr(phase38_rank, "_ROOT", rig.root)  # the real-root branch: full shape only
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*full"):
        phase38_rank.emit(root=rig.root)
    assert not out.exists()
    monkeypatch.undo()
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"REFUSING to overwrite"):
        phase38_rank.emit(root=rig.root)
    assert out.read_text(encoding="utf-8") == "{}"


# =================================================================================================
# (4c) D-34: the rehearsal identity, written by run() before the first score; the disclosure of
# every later commit to a scoring module; the preflight gate on the real root.
# =================================================================================================

_DISCLOSED = ("scripts/phase38_rank.py", "scripts/phase38_sizes_prereg.py")


def _identity(path, **shape):
    shape = {"readings": list(READINGS), "slots": list(SLOTS), "max_size": 8, **shape}
    return phase38_rank.record_rehearsal(path, **shape)


def test_disclosed_modules_and_the_identity_path(tmp_path, monkeypatch):
    assert phase38_rank.DISCLOSED_MODULES == _DISCLOSED
    assert set(_DISCLOSED) <= set(phase38_rank.MODULES)
    assert phase38_rank.rehearsal_identity_path() == _REAL_IDENTITY
    monkeypatch.setattr(phase38_rank, "_ROOT", tmp_path)
    assert phase38_rank.rehearsal_identity_path() == tmp_path / "data" / "phase38_rehearsal.json"


def test_record_rehearsal_keeps_the_first_identity(tmp_path, capsys):
    path = tmp_path / "id.json"
    first = _identity(path, slots=["pet_name", "birth_year"])
    assert f"REHEARSAL RECORDED {_git('rev-parse', 'HEAD')}" in capsys.readouterr().out
    on = _sidecar(path)
    assert first == {"status": "recorded", **on}
    assert on["git_sha"] == _git("rev-parse", "HEAD")
    assert on["module_sha256"] == {
        rel: hashlib.sha256((_REPO / rel).read_bytes()).hexdigest() for rel in _DISCLOSED
    }
    assert (on["readings"], on["slots"], on["max_size"]) == (
        list(READINGS),
        ["pet_name", "birth_year"],
        8,
    )
    assert datetime.datetime.fromisoformat(on["started_utc"]).tzinfo is not None
    before = path.read_bytes()
    again = _identity(path, slots=["street"], max_size=32)
    assert again == {"status": "kept", **on}
    assert path.read_bytes() == before


def test_the_identity_is_written_before_the_first_score(rig, tmp_path, monkeypatch):
    """B-1: a crash on the FIRST scoring call leaves the identity and no sidecar; a preflight
    refusal leaves no identity; a rerun after the crash keeps the first identity."""
    identity = tmp_path / "id.json"
    shape = {"readings": ("k0",), "slots": ("pet_name",), "max_size": 8}

    def dirty(**kw):
        raise SystemExit("[phase38_rank] dirty tree")

    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", dirty)
    with pytest.raises(SystemExit, match=r"dirty tree"):
        phase38_rank.run(root=rig.root, **rig.paths, **shape, rehearsal_identity=identity)
    assert not identity.exists() and not rig.paths["ledger_path"].exists()
    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", lambda **kw: None)
    rig.crash = lambda reading, slot, value: True
    with pytest.raises(RuntimeError, match="scorer died"):
        phase38_rank.run(root=rig.root, **rig.paths, **shape, rehearsal_identity=identity)
    assert len(rig.log) == 1  # the crash came on the very first score
    assert identity.exists()
    assert list((rig.root / "data").iterdir()) == []
    assert [x["event"] for x in _lines(rig)] == ["start"]
    first = identity.read_bytes()
    second = tmp_path / "second"
    (second / "data").mkdir(parents=True)
    rig.crash = None
    paths = {"ledger_path": second / "ledger.jsonl", "heartbeat_path": second / "hb.jsonl"}
    assert phase38_rank.run(root=second, **paths, **shape, rehearsal_identity=identity) == "SCORED"
    assert identity.read_bytes() == first


def test_the_real_root_never_records_a_rehearsal(tmp_path):
    identity, ledger = tmp_path / "id.json", tmp_path / "ledger.jsonl"
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*full"):
        phase38_rank.run(ledger_path=ledger, rehearsal_identity=identity)
    assert not identity.exists() and not ledger.exists()


def _git_lines(*args):
    return [line for line in _git(*args).splitlines() if line]


def test_rehearsal_disclosure_lists_every_commit_to_a_scoring_module():
    first = _git_lines("log", "--reverse", "--format=%H", "--", "tests/test_phase38_rank.py")[0]
    identity = {
        "git_sha": first,
        "module_sha256": {
            rel: hashlib.sha256(_git("show", f"{first}:{rel}").encode() + b"\n").hexdigest()
            for rel in _DISCLOSED
        },
        "readings": list(READINGS),
        "slots": ["pet_name", "birth_year"],
        "max_size": 8,
        "started_utc": "2026-10-04T00:00:00+00:00",
    }
    head = _git("rev-parse", "HEAD")
    launch = phase38_rank.module_sha256()
    disclosure = phase38_rank.rehearsal_disclosure(
        identity, launch_git_sha=head, launch_module_sha256=launch
    )
    commits = disclosure["commits"]
    assert commits and disclosure["driver_changed"] is True
    assert disclosure["changed"]["scripts/phase38_rank.py"] is True
    for commit in commits:
        touched = set(_git_lines("show", "--name-only", "--format=", commit["sha"]))
        assert commit["modules"] == [rel for rel in _DISCLOSED if rel in touched]
        assert commit["modules"], commit
        assert commit["reason"] == _git("log", "-1", "--format=%s", commit["sha"])
    assert _git_lines("log", "--format=%H", f"{first}..{head}", "--", *_DISCLOSED) == [
        c["sha"] for c in commits
    ]
    assert disclosure["slice_read"] == {
        "readings": list(READINGS),
        "slots": ["pet_name", "birth_year"],
        "max_size": 8,
    }
    assert disclosure["statement"] == (
        "The CPU rehearsal (38-07) read pet_name, birth_year at |R| 8 under 8 readings, minted "
        "candidates included, before the driver review and the MPS run (D-34)."
    )
    assert disclosure["launch_module_sha256"] == {rel: launch[rel] for rel in _DISCLOSED}
    assert (disclosure["rehearsal_git_sha"], disclosure["launch_git_sha"]) == (first, head)
    same = {**identity, "git_sha": head, "module_sha256": {r: launch[r] for r in _DISCLOSED}}
    equal = phase38_rank.rehearsal_disclosure(
        same, launch_git_sha=head, launch_module_sha256=launch
    )
    assert equal["commits"] == [] and equal["driver_changed"] is False
    assert equal["changed"] == {rel: False for rel in _DISCLOSED}
    drifted = {**same, "module_sha256": {**same["module_sha256"], _DISCLOSED[1]: "0" * 64}}
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*without a commit"):
        phase38_rank.rehearsal_disclosure(drifted, launch_git_sha=head, launch_module_sha256=launch)


def test_preflight_on_the_real_root_requires_the_identity(rig, monkeypatch):
    monkeypatch.setattr(phase38_rank, "_ROOT", rig.root)
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*D-34"):
        phase38_rank.preflight(ledger_path=rig.paths["ledger_path"])
    assert not rig.paths["ledger_path"].exists() and rig.launches == []
    _identity(phase38_rank.rehearsal_identity_path())
    assert phase38_rank.rehearsal_identity_path() == rig.root / "data" / "phase38_rehearsal.json"
    assert phase38_rank.preflight(ledger_path=rig.paths["ledger_path"])["device"] == "mps"


@pytest.mark.parametrize("gate_fails", [False, True])
def test_the_real_root_record_carries_the_disclosure(rig, monkeypatch, gate_fails):
    monkeypatch.setattr(phase38_rank, "_ROOT", rig.root)
    _identity(phase38_rank.rehearsal_identity_path(), slots=["pet_name", "birth_year"])
    if gate_fails:
        rig.table[("k32", "street", TAUGHT["street"])] = 3.0
    status = phase38_rank.run(**rig.paths)
    assert status == ("GATE_FAILED" if gate_fails else "SCORED")
    if not gate_fails:
        phase38_rank.crosscheck()
    record = phase38_rank.emit()
    disclosure = record["rehearsal_disclosure"]
    head = _git("rev-parse", "HEAD")
    assert (disclosure["rehearsal_git_sha"], disclosure["launch_git_sha"]) == (head, head)
    assert disclosure["commits"] == [] and disclosure["driver_changed"] is False
    assert disclosure["slice_read"]["slots"] == ["pet_name", "birth_year"]
    assert (rig.root / phase38_prereg.RANK_RECORD).exists()


# =================================================================================================
# (4d) render_report, report, main (plan 38-07 Task 3): the report is the record rendered, nothing
# else; the CLI calls each command with no argument from the repository root.
# =================================================================================================

_SECTIONS = [
    "# Phase 38 — E5 exposure rank at larger minted sets",
    "## Status",
    "## Approval and cost (D-21/D-22/D-23)",
    "## Gate: committed reference sets (D-18, D-11a)",
    "## A2 counts, collapse and damage (D-13, D-14)",
    "## Drop formula audit (D-33)",
    "## Rank curves (D-15)",
    "## Did the rank move before generation collapsed? (D-12, D-29, D-30)",
    "## Numeric neighbour sensitivity (D-27, descriptive)",
    "## CPU cross-check (D-19, descriptive)",
    "## Rehearsal disclosure (D-34)",
    "## Limitations (D-36)",
    "## Provenance",
]
_LIMITATION_SENTENCES = (
    "The name/place candidates are grammar syllables while the taught values look like English "
    "compound words, so at the same token count the base model may prefer the taught values.",
    'Read each curve beside the "adapter-off (descriptive)" column of the same slot and size.',
)
_COLUMNS = (*(f"k{k}" for k in phase38_prereg.PREFIXES), "M2", "adapter_off")


def _emitted(rig):
    cat_minted = phase38_rank.scoring_plan(slots=("cat_name",))["cat_name"]["minted"]
    rig.table.update({("k0", "cat_name", v): 0.1 for v in cat_minted})
    _scored(rig)
    phase38_rank.emit(root=rig.root)
    return _sidecar(rig.root / phase38_prereg.RANK_RECORD)


def _headings(text):
    return re.findall(r"^#{1,2} .+$", text, flags=re.M)


def _section(text, heading):
    start = text.index(heading + "\n")
    end = text.find("\n## ", start + len(heading))
    return text[start : end if end != -1 else len(text)]


def _rows(section):
    """Table body rows (header and separator dropped) as lists of cell strings."""
    lines = [line for line in section.splitlines() if line.startswith("|")]
    return [[c.strip() for c in line.strip("|").split("|")] for line in lines[2:]]


def test_render_report_renders_the_scored_record(rig):
    record = _emitted(rig)
    text = phase38_rank.render_report(record)
    assert _headings(text) == _SECTIONS
    assert record["approval"]["ruling"] in text  # D-21, verbatim
    # Curves: parsed back and compared with the record, cell by cell.
    curves = _section(text, "## Rank curves (D-15)")
    header = [line for line in curves.splitlines() if line.startswith("|")][0]
    assert "M2 (descriptive)" in header and "adapter-off (descriptive)" in header
    rows = _rows(curves)
    expected_rows = [
        (slot, str(size))
        for slot in SLOTS
        for size in phase38_prereg.nested_sizes(record["set_sizes"][slot])
    ]
    assert [(r[0], r[1]) for r in rows] == expected_rows
    for row in rows:
        slot, size = row[0], row[1]
        for reading, cell in zip(_COLUMNS, row[2:]):
            rank, bits = re.fullmatch(r"(\d+) \((.+)\)", cell).groups()
            curve = record["readings"][reading][slot]["curve"][size]
            assert (int(rank), float(bits)) == (curve["rank"], curve["bits"])
    # Relations: one row per slot x size x event, WR-01 outcomes by name with rank_0.
    relations = _rows(_section(text, _SECTIONS[7]))
    events = record["events"]
    assert len(relations) == 2 * sum(len(by_size) for by_size in events.values())
    cat = [r for r in relations if r[0] == "cat_name"]
    for r in cat:
        size = r[1]
        if r[2].startswith("moved"):
            assert r[6] == r[8] == f"UNREACHABLE_AT_SIZE (rank_0 = {size})"
        else:
            assert r[6] == r[8] == f"ALREADY_AT_K0 (rank_0 = {size})"
    by_year = [r for r in relations if r[0] == "birth_year"]  # never collapsed (A2 counts)
    assert all(r[5] == "never within the grid" for r in by_year)
    assert any(r[6] == "never collapsed within the grid" for r in by_year)
    # A2 counts and the D-33 audit.
    a2_rows = _rows(_section(text, "## A2 counts, collapse and damage (D-13, D-14)"))
    assert [r[0] for r in a2_rows] == list(SLOTS)
    audit = record["drop_formula_audit"]
    d33 = _section(text, "## Drop formula audit (D-33)")
    assert [(r[0], int(r[1])) for r in _rows(d33)] == [tuple(c) for c in audit["differing"]]
    assert "No damage event changes between the two formulas." in d33
    assert "`person_name` k = 8: exact margin tie decided by D-14's strict >" in d33
    assert "margin tie decided by rounding" not in d33
    sens = _section(text, "## Numeric neighbour sensitivity (D-27, descriptive)")
    assert {r[0] for r in _rows(sens)} == {"birth_year", "house_number"}
    cpu = _section(text, "## CPU cross-check (D-19, descriptive)")
    assert f"{record['cpu_crosscheck']['differing']} of {record['cpu_crosscheck']['cells']}" in cpu
    assert "This record IS the CPU rehearsal" in _section(text, "## Rehearsal disclosure (D-34)")
    limitations = _section(text, "## Limitations (D-36)")
    assert all(sentence in limitations for sentence in _LIMITATION_SENTENCES)
    assert record["provenance"]["run"]["git_sha_at_launch"] in _section(text, "## Provenance")
    # The other branches, chosen from the record's data.
    flipped = json.loads(json.dumps(record))
    flipped["drop_formula_audit"]["flips"] = [["street", 16]]
    first = next(iter(flipped["events"]["pet_name"]))
    flipped["events"]["pet_name"][first]["moved"]["vs_damage"] = "REFERENCE_NEVER_IN_GRID"
    other = phase38_rank.render_report(flipped)
    assert "`street` k = 16: margin tie decided by rounding" in other
    assert "No damage event changes" not in other
    assert "never damaged within the grid" in other
    subset = json.loads(json.dumps(record))
    subset.update(events=None, events_reason="a rehearsal subset without the readings ['k8']")
    assert "a rehearsal subset without the readings ['k8']" in phase38_rank.render_report(subset)


def test_render_helpers():
    assert phase38_rank._table(("a", "b"), [[1, "x"]]) == [
        "| a | b |",
        "|---|---|",
        "| 1 | x |",
        "",
    ]
    event = {"rank_0": 3, "vs_collapse": "REFERENCE_NEVER_IN_GRID", "vs_damage": "ALREADY_AT_K0"}
    assert phase38_rank._relation_text(event, "vs_collapse") == "never collapsed within the grid"
    assert phase38_rank._relation_text(event, "vs_damage") == "ALREADY_AT_K0 (rank_0 = 3)"
    event["vs_damage"] = "UNREACHABLE_AT_SIZE"
    assert phase38_rank._relation_text(event, "vs_damage") == "UNREACHABLE_AT_SIZE (rank_0 = 3)"
    event["vs_damage"] = "BEFORE"
    assert phase38_rank._relation_text(event, "vs_damage") == "BEFORE"
    assert phase38_rank._first_text(None, "never") == "never"
    assert phase38_rank._first_text(16, "never") == "k = 16"
    assert phase38_rank._slots({"street": 1, "pet_name": 2}) == ["pet_name", "street"]
    assert phase38_rank._sizes(["128", "32", "512", "8"]) == ["8", "32", "128", "512"]
    curves = {"k0": {"pet_name": {"32": {"rank": 2, "bits": 4.0}, "8": {"rank": 1, "bits": 3.0}}}}
    assert phase38_rank._curve_rows(curves, ["pet_name"], ["k0", "M2"]) == [
        ["pet_name", "8", "1 (3.0)", "—"],
        ["pet_name", "32", "2 (4.0)", "—"],
    ]
    lines = phase38_rank._disclosure_lines({"this_is_the_rehearsal": True})
    assert lines[0].startswith("This record IS the CPU rehearsal (D-34)")


def test_render_report_renders_the_disclosure_branches(rig):
    record = _emitted(rig)
    disclosure = {
        "statement": "The CPU rehearsal read pet_name at |R| 8 under 8 readings.",
        "slice_read": {"readings": list(READINGS), "slots": ["pet_name"], "max_size": 8},
        "rehearsal_git_sha": "a" * 40,
        "rehearsal_module_sha256": {rel: "1" * 64 for rel in _DISCLOSED},
        "launch_git_sha": "b" * 40,
        "launch_module_sha256": {rel: "1" * 64 for rel in _DISCLOSED},
        "changed": {rel: False for rel in _DISCLOSED},
        "driver_changed": False,
        "commits": [],
    }
    empty = phase38_rank.render_report({**record, "rehearsal_disclosure": disclosure})
    section = _section(empty, "## Rehearsal disclosure (D-34)")
    assert disclosure["statement"] in section and "a" * 40 in section and "b" * 40 in section
    assert (
        "No commit touched scripts/phase38_rank.py or scripts/phase38_sizes_prereg.py between the "
        "rehearsal and the launch." in section
    )
    assert len(_rows(section)) == len(_DISCLOSED)
    commit = {"sha": "c" * 40, "reason": "fix(38-07): why", "modules": [_DISCLOSED[0]]}
    changed = {
        **disclosure,
        "changed": {_DISCLOSED[0]: True, _DISCLOSED[1]: False},
        "driver_changed": True,
        "commits": [commit],
    }
    listed = _section(
        phase38_rank.render_report({**record, "rehearsal_disclosure": changed}),
        "## Rehearsal disclosure (D-34)",
    )
    assert f"`{'c' * 40}` fix(38-07): why (touched: {_DISCLOSED[0]})" in listed
    assert "No commit touched" not in listed


def test_render_report_on_a_gate_failed_record(rig):
    rig.table[("k32", "street", TAUGHT["street"])] = 3.0
    phase38_rank.run(root=rig.root, **rig.paths)
    record = _jsonable(phase38_rank.emit(root=rig.root))
    text = phase38_rank.render_report(record)
    assert _headings(text) == [
        "# Phase 38 — E5 exposure rank at larger minted sets",
        "## Status",
        "## Approval and cost (D-21/D-22/D-23)",
        "## Gate: committed reference sets (D-18, D-11a)",
        "## Rehearsal disclosure (D-34)",
        "## Limitations (D-36)",
        "## Provenance",
    ]
    assert "GATE_FAILED" in _section(text, "## Status")
    gate_rows = _rows(_section(text, "## Gate: committed reference sets (D-18, D-11a)"))
    assert len(gate_rows) == len(READINGS) * len(SLOTS)
    assert [r[:2] for r in gate_rows if r[5] == "False"] == [["k32", "street"]]
    assert all(sentence in text for sentence in _LIMITATION_SENTENCES)


def test_report_writes_once_and_the_real_root_needs_a_committed_record(rig, monkeypatch, capsys):
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*phase38_rank\.json is missing"):
        phase38_rank.report(root=rig.root)
    record = _emitted(rig)
    out = rig.root / phase38_prereg.REPORT_RECORD
    monkeypatch.setattr(phase38_rank, "_ROOT", rig.root)
    monkeypatch.setattr(phase38_rank, "_tracked_and_clean", lambda rel: False)
    with pytest.raises(SystemExit, match=r"^\[phase38_rank\] .*committed and unmodified"):
        phase38_rank.report()
    assert not out.exists()
    monkeypatch.undo()
    assert phase38_rank.report(root=rig.root) == out
    assert f"REPORT {out}" in capsys.readouterr().out
    assert out.read_text(encoding="utf-8") == phase38_rank.render_report(record)
    before = out.read_bytes()
    with pytest.raises(SystemExit, match=r"REFUSING to overwrite"):
        phase38_rank.report(root=rig.root)
    assert out.read_bytes() == before


def test_tracked_and_clean_reads_git():
    assert phase38_rank._tracked_and_clean("scripts/phase38_prereg.py") is True
    assert phase38_rank._tracked_and_clean("results/phase38_never_written.json") is False


def test_the_full_fake_chain_through_the_commands(rig):
    assert phase38_rank.run(root=rig.root, **rig.paths) == "SCORED"
    phase38_rank.crosscheck(root=rig.root)
    phase38_rank.emit(root=rig.root)
    out = phase38_rank.report(root=rig.root)
    artifacts = (
        phase38_rank.run_sidecar(rig.root),
        phase38_rank.cpu_sidecar(rig.root),
        rig.root / phase38_prereg.RANK_RECORD,
        out,
    )
    assert all(path.exists() for path in artifacts)
    record = json.loads((rig.root / phase38_prereg.RANK_RECORD).read_text(encoding="utf-8"))
    assert out.read_text(encoding="utf-8") == phase38_rank.render_report(record)


@pytest.mark.parametrize("command", ["preflight", "run", "crosscheck", "emit", "report"])
def test_main_dispatches_with_no_arguments_from_the_repo(tmp_path, monkeypatch, command):
    real = getattr(phase38_rank, command)
    seen = []

    def recorder(*args, **kwargs):
        inspect.signature(real).bind(*args, **kwargs)
        seen.append((args, kwargs, pathlib.Path.cwd()))

    monkeypatch.setattr(phase38_rank, command, recorder)
    monkeypatch.chdir(tmp_path)
    assert phase38_rank.main([command]) == 0
    assert seen == [((), {}, phase38_rank._REPO)]


@pytest.mark.parametrize("argv", [[], ["bogus"], ["run", "x"]])
def test_main_refuses_anything_else(argv):
    with pytest.raises(SystemExit) as raised:
        phase38_rank.main(argv)
    assert raised.value.code == phase38_rank.__doc__


def test_the_cli_exits_non_zero_on_a_bogus_command():
    done = subprocess.run(
        [sys.executable, "scripts/phase38_rank.py", "bogus"], cwd=_REPO, capture_output=True
    )
    assert done.returncode != 0


# =================================================================================================
# (5) RANK-03: the rank and the NLL are imported and called, never re-implemented.
# =================================================================================================

_OWN_DEFS = {
    "exposure_rank",
    "_rank_of",
    "reference_set_for",
    "value_span_nll",
    "value_span_nll_mean",
}
_NEVER_CALLED = {"exposure_rank", "_rank_of", "inject_lora"}
_PINNED_CALLS = {
    "reference_set_for": "phase18_extraction",
    "value_span_nll_mean": "phase19_erasure",
    "value_span_nll": "phase18_extraction",
}


def _rank03_failures(sources):
    """(failures, pinned calls seen) over ``(relpath, source)`` pairs."""
    failures, seen = [], set()
    for relpath, source in sources:
        for node in ast.walk(ast.parse(source)):
            where = f"{relpath}:{getattr(node, 'lineno', '?')}"
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in _OWN_DEFS:
                failures.append(f"{where}: defines {node.name}")
            if (
                isinstance(node, ast.Attribute)
                and node.attr == "replace"
                and isinstance(node.value, ast.Name)
                and node.value.id == "os"
            ):
                failures.append(f"{where}: os.replace")
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name in _NEVER_CALLED:
                failures.append(f"{where}: calls {name}")
            if name in _PINNED_CALLS:
                owner = _PINNED_CALLS[name]
                if isinstance(func, ast.Attribute) and getattr(func.value, "id", None) == owner:
                    seen.add(name)
                else:
                    failures.append(f"{where}: {name} not called as {owner}.{name}")
    return failures, seen


def _phase38_sources():
    paths = sorted(_SCRIPTS.glob("phase38_*.py"))
    assert paths, "meta-guard: no scripts/phase38_*.py, the gate would be vacuous"
    return [(p.relative_to(_REPO).as_posix(), p.read_text(encoding="utf-8")) for p in paths]


def test_rank03_no_phase38_script_reimplements_the_instrument(tmp_path):
    sources = _phase38_sources()
    failures, seen = _rank03_failures(sources)
    assert failures == []
    assert seen == {"reference_set_for", "value_span_nll_mean"}  # non-vacuity: the pinned calls
    source = (_SCRIPTS / "phase38_rank.py").read_text(encoding="utf-8")
    for name, plant in (
        ("own_def.py", "\n\ndef reference_set_for(slot):\n    return [slot]\n"),
        (
            "exposure.py",
            "\n\ndef planted(nll):\n    return phase18_extraction.exposure_rank(nll)\n",
        ),
        (
            "bare.py",
            "\n\ndef planted(m):\n    return value_span_nll_mean(m, 0, 0, slot=1, value=2)\n",
        ),
        ("inject.py", "\n\ndef planted(m, c):\n    inject_lora(m, c)\n"),
        ("replace.py", "\n\ndef planted(a, b):\n    os.replace(a, b)\n"),
    ):
        planted = _planted(tmp_path, source, source + plant, name)
        assert _rank03_failures([(name, planted)])[0], name


def test_the_instrument_file_is_unchanged():
    """RANK-03: phase18_extraction.py bytes stay what tests/test_phase21_sc5.py pins."""
    assert _git("status", "--porcelain", "--", "scripts/phase18_extraction.py") == ""
    assert _git("diff", "HEAD", "--", "scripts/phase18_extraction.py") == ""


def test_no_in_run_stop_rule_and_no_ruling_writes():
    """D-23: the committed stop is require_launch's; the driver never calls phase36_ledger.rule."""
    tree = ast.parse((_SCRIPTS / "phase38_rank.py").read_text(encoding="utf-8"))
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and getattr(node.func.value, "id", None) == "phase36_ledger"
    }
    assert called == {"run_id", "read_ledger", "open_runs", "require_launch", "append"}
    assert not re.search(r"\bprefixes\s*=", ast.unparse(tree))  # check_unit_caps never gets it


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_every_phase38_rank_function_has_a_cpu_test(tmp_path):
    source = (_SCRIPTS / "phase38_rank.py").read_text(encoding="utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _untested_functions("phase38_rank", source, test_source) == []
    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase38_rank", copied, test_source) == ["planted_untested"]
