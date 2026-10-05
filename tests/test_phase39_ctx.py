"""Plan 39-04: the E6 driver (scripts/phase39_ctx.py), part 1, tested on CPU only.

The device work (the device resolve, the adapter digests, the reading models) is monkeypatched;
the NLL copy is proved bitwise against the pinned phase18_extraction.span_nll_from_ids on two CPU
models (conftest's fake_lm and a seeded tiny GPT). What this file proves:
- the driver's constants, sidecars and inputs, torch-free at import;
- D-30 / D-30a: the copy's nll_sum / nll_mean and its suffix sum are bitwise the pinned function's;
- D-04 / D-18: the anchor ids are value_span_nll's context; gate cells compare both functions;
- D-05 / D-06 / D-08 / D-28: the anchor draws go through draw_all after the in-prompt guard;
- D-23 / D-23b: question scoring runs on _guarded_span(entry);
- D-02 / D-03 / D-11 / D-19: every preflight refusal runs before the ledger start line.

No test reads a file under checkpoints/ (gitignored, absent on ubuntu CI): the digests are stubbed
and the gitignored run inputs are tmp stand-ins. Nothing here touches the real ledger, results/ or
data/phase39_ctx_*.
"""

import contextlib
import hashlib
import json
import pathlib
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
import phase36_ledger  # noqa: E402  (same; never aliased)
import phase36_probe  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)
import phase38_rank  # noqa: E402  (same)
import phase39_ctx  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase39_prereg  # noqa: E402  (same; frozen, import only)

from test_phase29_prereg import _git  # noqa: E402

READINGS = phase39_prereg.READINGS
SLOTS = phase39_prereg.SLOTS
TAUGHT = {fact.slot: fact.value for fact in phase14_factset.LOCKED_FACTS}


def _real_sidecars():
    # _REPO, not phase39_ctx._ROOT: some tests patch _ROOT to a rig root.
    return sorted((_REPO / "data").glob("phase39_ctx_*"))


_REAL_IDENTITY = _REPO / "data" / "phase39_rehearsal.json"


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    sidecars = _real_sidecars()
    identity = _REAL_IDENTITY.exists()
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _real_sidecars() == sidecars
    assert _REAL_IDENTITY.exists() == identity


def _read(rel):
    return json.loads((_REPO / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def committed_digests():
    return {
        "persona_adapter": _read(phase38_prereg.CURVE_RECORD)["adapter_in_sha256"],
        "m2_adapter": _read(phase38_prereg.RETRAIN_SCORES)["retrain_scores"]["adapter_sha256"],
    }


@pytest.fixture(scope="module")
def real_gate2():
    """The real gate 2 on the committed A2 records, computed once (~2 s)."""
    return phase39_prereg.gate2()


@pytest.fixture(scope="module")
def tok():
    from personacore.tokenizer import from_json

    return from_json(_REPO / "artifacts" / "tokenizer.json")


@pytest.fixture
def rig(tmp_path, monkeypatch, committed_digests, real_gate2):
    """The preflight fixture: a tmp root, tmp ledger/heartbeat, the device work stubbed."""
    (tmp_path / "results").mkdir()
    (tmp_path / "data").mkdir()
    paths = {"ledger_path": tmp_path / "ledger.jsonl", "heartbeat_path": tmp_path / "hb.jsonl"}
    rig = types.SimpleNamespace(
        root=tmp_path,
        paths=paths,
        dirty=[],
        launches=[],
        digests=dict(committed_digests),
        gate2=real_gate2,
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
    monkeypatch.setattr(phase39_ctx, "_device", lambda: "mps")
    monkeypatch.setattr(phase39_ctx, "refuse_if_dirty", lambda **kw: rig.dirty.append(kw))
    monkeypatch.setattr(phase38_rank, "adapter_digests", lambda: dict(rig.digests))
    monkeypatch.setattr(phase39_prereg, "gate2", lambda **kw: rig.gate2)

    def require_launch(front, **kw):
        rig.launches.append((front, kw))
        return {"front": front, "spent_seconds": {front: 0.0}, "total_seconds": 0.0, "lifted": ()}

    monkeypatch.setattr(phase36_ledger, "require_launch", require_launch)
    return rig


# =================================================================================================
# (1) Task 1: constants, sidecars, inputs, digests, the device and the reading models.
# =================================================================================================


def test_constants_and_paths(tmp_path):
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] broken$"):
        phase39_ctx._prove(False, "broken")
    phase39_ctx._prove(True, "never raised")
    assert phase39_ctx.RUN_ID == "v6/39/E6/ctx" == phase36_ledger.run_id(39, "E6", "ctx")
    assert phase39_ctx.FRONT == "E6"
    assert phase39_ctx.LAUNCH_PATHSPEC == ("scripts", "src", "results", "artifacts")
    assert phase39_ctx.PREREG_FILE == "scripts/phase39_prereg.py"
    data = tmp_path / "data"
    assert phase39_ctx.run_sidecar(tmp_path) == data / "phase39_ctx_run.json"
    assert phase39_ctx.gate_sidecar(tmp_path) == data / "phase39_ctx_gate.json"
    assert phase39_ctx.cpu_sidecar(tmp_path) == data / "phase39_ctx_cpu.json"
    assert phase39_ctx.reading_sidecar(tmp_path, "M2") == data / "phase39_ctx_M2.json"
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\]"):
        phase39_ctx.reading_sidecar(tmp_path, "k7")
    outputs = phase39_ctx.outputs(tmp_path)
    assert outputs == (
        tmp_path / phase39_prereg.CTX_RECORD,
        data / "phase39_ctx_run.json",
        data / "phase39_ctx_gate.json",
        data / "phase39_ctx_cpu.json",
        *(data / f"phase39_ctx_{reading}.json" for reading in READINGS),
    )
    assert len(set(outputs)) == len(outputs) == 4 + 8
    for sidecar in outputs[1:]:
        assert sidecar.parent == data and sidecar.name.startswith("phase39_ctx_")


def test_the_driver_imports_without_torch():
    probe = (
        "import sys; sys.path[:0] = ['scripts', 'src']; import phase39_ctx as c; "
        "print(c.RUN_ID, c.FRONT, 'torch' in sys.modules, 'phase39_prereg' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_REPO, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["v6/39/E6/ctx", "E6", "False", "False"], out.stdout


def test_module_digests_are_the_repo_bytes():
    digests = phase39_ctx.module_sha256()
    assert tuple(digests) == phase39_ctx.MODULES
    for rel in (
        "src/personacore/lora/layer.py",
        "scripts/phase19_floor.py",
        "scripts/erasure_gate.py",
        "scripts/phase20_gate_coverage.py",
        "src/personacore/lora/inject.py",
        "src/personacore/lora/config.py",
        "src/personacore/model/gpt.py",
        "scripts/phase18_extraction.py",
        "scripts/phase39_prereg.py",
        "scripts/phase39_ctx.py",
    ):
        assert rel in digests, rel
    for rel, digest in digests.items():
        assert digest == hashlib.sha256((_REPO / rel).read_bytes()).hexdigest(), rel
        if rel == "scripts/phase39_ctx.py":  # tracked by this task's own commit
            assert (_REPO / rel).exists()
            continue
        assert _git("ls-files", "--error-unmatch", rel) == rel


def test_device_is_the_strict_preflight_device(monkeypatch):
    import personacore.preflight

    seen = []
    monkeypatch.setattr(
        personacore.preflight,
        "preflight_device",
        lambda **kw: seen.append(kw) or {"device": "mps"},
    )
    assert phase39_ctx._device() == "mps"
    assert seen == [{"strict": True}]


def test_reading_model_builds_each_reading_from_the_pinned_loaders(monkeypatch):
    import torch

    import personacore.lora

    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    built, disabled = [], []

    def adapted(device, k):
        built.append(("adapted", device, k))
        return torch.nn.Linear(1, 1), "tok", f"forbid-k{k}"

    def loaded(device, adapter_path=None):
        built.append(("loaded", device, adapter_path))
        return torch.nn.Linear(1, 1), "cfg", "tok", "forbid-M2", "artifact"

    @contextlib.contextmanager
    def off(model):
        disabled.append("in")
        yield
        disabled.append("out")

    monkeypatch.setattr(phase36_probe, "adapted_model", adapted)
    monkeypatch.setattr(phase14_recall, "load_adapted_model", loaded)
    monkeypatch.setattr(personacore.lora, "adapter_disabled", off)
    for reading in READINGS:
        with phase39_ctx.reading_model(reading, "cpu") as (model, tok, forbid):
            assert isinstance(model, torch.nn.Linear) and tok == "tok"
            expected = {"M2": "forbid-M2", "adapter_off": "forbid-k0"}.get(
                reading, f"forbid-{reading}"
            )
            assert forbid == expected
            if reading == "adapter_off":
                assert disabled == ["in"]
        if reading == "adapter_off":
            assert disabled == ["in", "out"]
    m2 = phase38_rank.m2_adapter_path()
    assert built == [
        *(("adapted", "cpu", k) for k in phase39_prereg.PREFIXES),
        ("loaded", "cpu", m2),
        ("adapted", "cpu", 0),
    ]
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\]"):
        with phase39_ctx.reading_model("k7", "cpu"):
            pass


def test_run_inputs_and_tracked_inputs(rig):
    tracked = phase39_ctx.tracked_inputs()
    assert tracked[0] == "scripts/phase39_prereg.py"
    for rel in (
        *(phase39_prereg.A2_RECORDS[r]["path"] for r in READINGS),
        phase38_prereg.MINTING_RECORD,
        phase38_prereg.RANK_RECORD,
        "results/phase18_corpus.json",
        phase39_prereg.BUDGET_RECORD,
        "results/phase36_probe_e1.json",
        "results/phase36_probe_e6.json",
    ):
        assert rel in tracked, rel
    assert len(set(tracked)) == len(tracked)
    assert all(_git("ls-files", "--error-unmatch", rel) == rel for rel in tracked)
    inputs = phase39_ctx.run_inputs()
    assert inputs[:4] == (
        phase14_recall.CONVBASE_SLIM,
        phase14_recall.ADAPTER_PATH,
        phase14_recall.TOKENIZER_PATH,
        phase38_rank.m2_adapter_path(),
    )
    for path in phase38_rank.run_inputs()[4:]:
        assert path in inputs
    for rel in tracked:
        assert _REPO / rel in inputs
    assert len(set(inputs)) == len(inputs)


def test_private_helpers(tmp_path, monkeypatch):
    blob = tmp_path / "b.bin"
    blob.write_bytes(b"e6")
    assert phase39_ctx._sha256(blob) == hashlib.sha256(b"e6").hexdigest()
    assert phase39_ctx._now().endswith("+00:00")
    assert phase39_ctx._json(phase38_prereg.CURVE_RECORD) == _read(phase38_prereg.CURVE_RECORD)
    assert phase39_ctx._load(_REPO / phase38_prereg.CURVE_RECORD) == _read(
        phase38_prereg.CURVE_RECORD
    )
    assert phase39_ctx._prereg() is phase39_prereg
    assert phase39_ctx._taught() == TAUGHT
    values = phase39_ctx._guard_values()
    assert values == [
        f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS
    ]
    sidecar = tmp_path / "data" / "once.json"
    phase39_ctx._write_once(sidecar, {"b": 1, "a": [2]})
    assert json.loads(sidecar.read_text(encoding="utf-8")) == {"a": [2], "b": 1}
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*write-once"):
        phase39_ctx._write_once(sidecar, {})
    assert phase39_ctx._is_real(phase39_ctx._ROOT) is True
    assert phase39_ctx._is_real(_REPO / "data" / "scratch") is True  # inside the repo
    assert phase39_ctx._is_real(tmp_path) is False
    monkeypatch.setattr(phase39_ctx, "_ROOT", tmp_path)
    assert phase39_ctx._is_real(tmp_path) is True
