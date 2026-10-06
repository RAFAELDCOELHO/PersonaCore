"""Plan 40-05: the E2 noise-floor driver (scripts/phase40_noise.py) part 1, tested on CPU only.

The teaching driver, the pinned A2 scorer and the model loads are monkeypatched; everything else is
the driver's own code against tmp roots. Nothing here writes the real results/, ledger/, data/ or
checkpoints/ (the autouse guard below snapshots them around every test), and no test runs the real
dirty check against the repository: `_repo_rig` stubs it and stands every gitignored input in with
a tmp file, so the file runs on CPU CI where checkpoints/ and data/ are empty.
"""

import pathlib
import subprocess
import sys

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

import phase14_factset  # noqa: E402  (scripts/ is not a package)
import phase14_recall  # noqa: E402  (same)
import phase19_erasure  # noqa: E402  (same; never aliased)
import phase38_prereg  # noqa: E402  (same)
import phase40_noise  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase40_prereg  # noqa: E402  (same; frozen: import only)
import teach_persona  # noqa: E402  (same)

from test_phase29_prereg import _git  # noqa: E402

# Every input file the run reads, as the (module, constant) its reader takes it from.
_RUN_INPUTS = (
    (teach_persona, "CONVBASE_BEST"),
    (teach_persona, "TOKENIZER_PATH"),
    (teach_persona, "DIALOG_TRAIN_BIN"),
    (teach_persona, "DIALOG_TRAIN_MASK"),
    (teach_persona, "DIALOG_VAL_BIN"),
    (teach_persona, "DIALOG_VAL_MASK"),
    (phase14_recall, "CONVBASE_SLIM"),
    (phase14_recall, "ADAPTER_PATH"),
    (phase14_recall, "TOKENIZER_PATH"),
    (phase19_erasure, "RETENTION_BIN"),
    (phase19_erasure, "PHASE18_CORPUS_PATH"),
    (phase19_erasure, "PHASE18_ARM_RECORD_PATH"),
)
# The gitignored ones (absent on CI): the rig stands each in with a tmp file.
_GITIGNORED_INPUTS = (
    "CONVBASE_BEST",
    "DIALOG_TRAIN_BIN",
    "DIALOG_TRAIN_MASK",
    "DIALOG_VAL_BIN",
    "DIALOG_VAL_MASK",
    "CONVBASE_SLIM",
    "RETENTION_BIN",
)


def _phase40_outputs():
    return sorted(
        p.name for d in ("data", "checkpoints") for p in (_ROOT / d).glob("*phase40*")
    ) + sorted(p.name for p in (_ROOT / "checkpoints").glob("*e2_*"))


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    outputs = _phase40_outputs()
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _phase40_outputs() == outputs


def _repo_rig(monkeypatch, tmp_path, dirty=None):
    """A tmp repository root for every test that reaches arm_paths, train_adapter, preflight, run
    or emit (plans 05-07). A plain helper, not a fixture: tests pass their own monkeypatch.

    teach_persona._REPO_ROOT and phase14_recall.ADAPTER_PATH point into it, every gitignored input
    is a tmp stand-in on its owning module attribute, the comparators' adapters exist there, and
    the `refuse_if_dirty` phase40_noise calls records its kwargs into ``dirty``."""
    root = tmp_path / "repo"
    for sub in ("checkpoints", "data", "results"):
        (root / sub).mkdir(parents=True)
    dirty = [] if dirty is None else dirty
    monkeypatch.setattr(teach_persona, "_REPO_ROOT", root)
    production = teach_persona.arm_outputs("real")["adapter"]
    production.write_bytes(b"production adapter stand-in")
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", production)
    for owner, name in _RUN_INPUTS:
        if name in _GITIGNORED_INPUTS:
            stand_in = root / "data" / f"input_{owner.__name__}_{name}"
            stand_in.write_bytes(b"stand-in")
            monkeypatch.setattr(owner, name, stand_in)
    for path in phase40_noise.comparators().values():
        if not path.exists():
            path.write_bytes(b"comparator stand-in")
    monkeypatch.setattr(phase40_noise, "refuse_if_dirty", lambda **kw: dirty.append(kw))
    return root


# =================================================================================================
# (1) Import surface, constants, inputs.
# =================================================================================================


def test_the_driver_imports_without_torch():
    probe = (
        "import sys; sys.path[:0] = [{s!r}, {r!r}]; import phase40_noise; "
        "print(phase40_noise.FRONT, *(m in sys.modules for m in "
        "('torch', 'teach_persona', 'phase19_erasure', 'phase40_prereg')))"
    ).format(s=str(_SCRIPTS), r=str(_SRC))
    out = subprocess.run(
        (sys.executable, "-c", probe), capture_output=True, text=True, check=True, cwd=_ROOT
    ).stdout.strip()
    assert out == "E2 False False False False"


def test_module_constants():
    assert phase40_noise.FRONT == "E2"
    assert set(phase40_noise.DISCLOSED_MODULES) <= set(phase40_noise.MODULES)
    assert phase40_noise.DISCLOSED_MODULES == (
        "scripts/phase40_noise.py",
        phase40_noise.PREREG_FILE,
    )
    assert all((_ROOT / rel).is_file() for rel in phase40_noise.MODULES)
    digests = phase40_noise.module_sha256()
    assert list(digests) == list(phase40_noise.MODULES)
    assert digests[phase40_noise.PREREG_FILE] == phase40_noise._sha256(
        _ROOT / phase40_noise.PREREG_FILE
    )
    # A rehearsal csv never lands under the record glob.
    assert not pathlib.PurePath(f"results/{phase40_noise.REHEARSAL_PREFIX}_x").match(
        phase40_prereg.RECORD_GLOB
    )


def test_module_sha256_reads_the_code_not_a_patched_root(monkeypatch, tmp_path):
    before = phase40_noise.module_sha256()
    monkeypatch.setattr(phase40_noise, "_ROOT", tmp_path)
    assert phase40_noise.module_sha256() == before


def test_write_once_refuses_an_existing_file(tmp_path):
    path = tmp_path / "sub" / "blob.json"
    phase40_noise._write_once(path, {"a": 1})
    assert path.read_text(encoding="utf-8").strip().startswith("{")
    with pytest.raises(SystemExit, match="exists"):
        phase40_noise._write_once(path, {"a": 2})


def test_is_real_only_inside_the_repository(tmp_path):
    assert phase40_noise._is_real(_ROOT)
    assert phase40_noise._is_real(_ROOT / "data")
    assert not phase40_noise._is_real(tmp_path)


def test_run_inputs_are_module_constants(monkeypatch, tmp_path):
    _repo_rig(monkeypatch, tmp_path)
    expected = tuple(getattr(owner, name) for owner, name in _RUN_INPUTS)
    expected += tuple(phase40_noise.comparators().values())
    if phase40_prereg.D13_INCLUDED:
        expected += ((_ROOT / phase38_prereg.MINTING_RECORD).resolve(),)
    assert phase40_noise.run_inputs() == expected


# =================================================================================================
# (2) Arm names: never "real", never a rehearsal name on the real run, never a published adapter.
# =================================================================================================


def test_arm_names_never_collide(monkeypatch, tmp_path):
    assert phase40_noise.arm_name("full", 1337) == "e2_full_seed1337"
    assert phase40_noise.arm_name("m2", 2024, rehearsal=True) == "e2rh_m2_seed2024"
    real = {
        phase40_noise.arm_name(g, s) for g in phase40_prereg.GROUPS for s in phase40_prereg.SEEDS
    }
    rehearsal = {
        phase40_noise.arm_name(g, s, rehearsal=True)
        for g in phase40_prereg.GROUPS
        for s in phase40_prereg.SEEDS
    }
    assert len(real) == len(rehearsal) == len(phase40_prereg.GROUPS) * len(phase40_prereg.SEEDS)
    assert not real & rehearsal and "real" not in real | rehearsal
    with pytest.raises(SystemExit, match="group"):
        phase40_noise.arm_name("m1", 1337)
    root = _repo_rig(monkeypatch, tmp_path)
    shipped = teach_persona.arm_outputs("real")["adapter"]
    for group in phase40_prereg.GROUPS:
        for seed in phase40_prereg.SEEDS:
            for rehearsal, prefix in ((False, "phase40"), (True, "phase40rh")):
                paths = phase40_noise.arm_paths(group, seed, rehearsal=rehearsal)
                arm = phase40_noise.arm_name(group, seed, rehearsal=rehearsal)
                assert paths == teach_persona.arm_outputs(arm, prefix=prefix)
                assert paths["adapter"] != shipped
                assert paths["adapter"].is_relative_to(root)
                assert paths["adapter"] not in phase40_noise.comparators().values()


# =================================================================================================
# (3) The ONE training helper.
# =================================================================================================


def _target():
    return next(f for f in phase14_factset.LOCKED_FACTS if f.slot == phase19_erasure.TARGET_SLOT)


def _fake_train(calls, *, mutate=None):
    """A stand-in for teach_persona's arm trainer: writes its five outputs, returns the fields."""

    def fake(arm, *, facts, family_ids, second_person, replay_ratio, seed, prefix, **kw):
        calls.append(
            {
                "arm": arm,
                "facts": list(facts),
                "family_ids": family_ids,
                "second_person": second_person,
                "replay_ratio": replay_ratio,
                "seed": seed,
                "prefix": prefix,
                "kw": kw,
            }
        )
        paths = teach_persona.arm_outputs(arm, prefix=prefix)
        for key in ("bin", "mask", "csv", "checkpoint", "adapter"):
            paths[key].parent.mkdir(parents=True, exist_ok=True)
            paths[key].write_bytes(f"{arm}:{key}".encode())
        if mutate is not None:
            mutate()
        return {
            "arm": arm,
            "paths": paths,
            "stats": {},
            "final_train_loss": 0.5,
            "ppl_adapter_on": 3.0,
            "ppl_adapter_off": 4.0,
            "scored_targets": 123,
        }

    return fake


@pytest.mark.parametrize("group", ["full", "m2"])
@pytest.mark.parametrize("rehearsal", [False, True])
def test_train_adapter_order_and_csv_move(monkeypatch, tmp_path, group, rehearsal):
    root = _repo_rig(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(teach_persona, "train_arm", _fake_train(calls))
    production = phase14_recall.ADAPTER_PATH.read_bytes()
    out = phase40_noise.train_adapter(group, 2024, root=root, rehearsal=rehearsal)
    (call,) = calls
    prefix = "phase40rh" if rehearsal else "phase40"
    arm = phase40_noise.arm_name(group, 2024, rehearsal=rehearsal)
    real_facts, real_second, real_replay = teach_persona.arm_spec("real")
    if group == "full":
        expected_facts = list(real_facts)
    else:
        expected_facts = [f for f in real_facts if f.id != _target().id]
        assert len(expected_facts) == len(real_facts) - 1
    assert call["facts"] == expected_facts
    assert (call["second_person"], call["replay_ratio"]) == (real_second, real_replay)
    assert call["family_ids"] == phase14_factset.TAUGHT_FAMILY_IDS
    assert (call["arm"], call["seed"], call["prefix"]) == (arm, 2024, prefix)
    assert call["kw"] == {}  # no resume_from, no DP, no adversarial ratio
    paths = teach_persona.arm_outputs(arm, prefix=prefix)
    dst = root / "data" / "phase40_e2" / arm / "run.csv"
    assert dst.read_bytes() == f"{arm}:csv".encode()
    assert not paths["csv"].parent.exists()
    assert phase14_recall.ADAPTER_PATH.read_bytes() == production
    assert out == {
        "group": group,
        "seed": 2024,
        "arm": arm,
        "prefix": prefix,
        "adapter": f"checkpoints/{prefix}_{arm}_adapter.pt",
        "adapter_sha256": phase40_noise._sha256(paths["adapter"]),
        "checkpoint": f"checkpoints/{prefix}_{arm}_latest.pt",
        "csv": f"data/phase40_e2/{arm}/run.csv",
        "csv_sha256": phase40_noise._sha256(dst),
        "train": {
            "final_train_loss": 0.5,
            "ppl_adapter_on": 3.0,
            "ppl_adapter_off": 4.0,
            "scored_targets": 123,
        },
    }


@pytest.mark.parametrize("key", ["adapter", "checkpoint", "bin", "mask", "csv_destination"])
def test_train_adapter_refuses_an_existing_output(monkeypatch, tmp_path, key):
    root = _repo_rig(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(teach_persona, "train_arm", _fake_train(calls))
    paths = phase40_noise.arm_paths("m2", 1337)
    path = (
        root / "data" / "phase40_e2" / phase40_noise.arm_name("m2", 1337) / "run.csv"
        if key == "csv_destination"
        else paths[key]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"stale")
    with pytest.raises(SystemExit, match="exists"):
        phase40_noise.train_adapter("m2", 1337, root=root)
    assert calls == []


def test_train_adapter_refuses_a_changed_production_adapter(monkeypatch, tmp_path):
    root = _repo_rig(monkeypatch, tmp_path)
    calls = []
    fake = _fake_train(calls, mutate=lambda: phase14_recall.ADAPTER_PATH.write_bytes(b"clobbered"))
    monkeypatch.setattr(teach_persona, "train_arm", fake)
    with pytest.raises(SystemExit, match="persona_adapter"):
        phase40_noise.train_adapter("full", 1337, root=root)
    assert len(calls) == 1


def test_train_adapter_refuses_an_m2_spec_dropping_two_facts(monkeypatch, tmp_path):
    root = _repo_rig(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(teach_persona, "train_arm", _fake_train(calls))
    facts, second, replay = teach_persona.arm_spec("real")
    monkeypatch.setattr(
        phase19_erasure, "retrain_arm_spec", lambda fact_id: (list(facts)[2:], second, replay)
    )
    with pytest.raises(SystemExit, match="dropped"):
        phase40_noise.train_adapter("m2", 1337, root=root)
    assert calls == []


def test_train_adapter_refuses_an_m2_spec_with_changed_settings(monkeypatch, tmp_path):
    root = _repo_rig(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(teach_persona, "train_arm", _fake_train(calls))
    spec = phase19_erasure.retrain_arm_spec(_target().id)
    monkeypatch.setattr(
        phase19_erasure, "retrain_arm_spec", lambda fact_id: (spec[0], not spec[1], spec[2])
    )
    with pytest.raises(SystemExit, match="second_person"):
        phase40_noise.train_adapter("m2", 1337, root=root)
    assert calls == []
