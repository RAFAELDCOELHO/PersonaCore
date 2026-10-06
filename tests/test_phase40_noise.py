"""Plan 40-05: the E2 noise-floor driver (scripts/phase40_noise.py) part 1, tested on CPU only.

The teaching driver, the pinned A2 scorer and the model loads are monkeypatched; everything else is
the driver's own code against tmp roots. Nothing here writes the real results/, ledger/, data/ or
checkpoints/ (the autouse guard below snapshots them around every test), and no test runs the real
dirty check against the repository: `_repo_rig` stubs it and stands every gitignored input in with
a tmp file, so the file runs on CPU CI where checkpoints/ and data/ are empty.
"""

import ast
import inspect
import json
import pathlib
import plistlib
import shutil
import subprocess
import sys
import textwrap

import pytest
import torch

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
import phase18_extraction  # noqa: E402  (same)
import phase19_erasure  # noqa: E402  (same; never aliased)
import phase35_prereg  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)
import phase38_rank  # noqa: E402  (same)
import phase39_ctx  # noqa: E402  (same)
import phase39_prereg  # noqa: E402  (same)
import phase40_noise  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase40_prereg  # noqa: E402  (same; frozen: import only)
import teach_persona  # noqa: E402  (same)

from personacore.checkpoint import ADAPTER_SCHEMA_VERSION  # noqa: E402
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


# =================================================================================================
# (4) The A2 wrapper around the pinned scorer.
# =================================================================================================

_COMMITTED_A2 = phase19_erasure.arm_record_path("retrain")


@pytest.mark.parametrize("group", ["full", "m2"])
def test_score_a2_calls_the_pin_with_the_record_path(monkeypatch, tmp_path, group):
    root = _repo_rig(monkeypatch, tmp_path)
    calls = []

    def fake(arm, device, **kw):
        calls.append((arm, device, kw))
        shutil.copyfile(_COMMITTED_A2, kw["record_path"])

    monkeypatch.setattr(phase19_erasure, "run_erasure_arm", fake)
    adapter = root / "checkpoints" / "an_adapter.pt"
    out = phase40_noise.score_a2(group, 1338, adapter, root=root, device="cpu")
    record = root / phase40_prereg.a2_record(group, 1338)
    assert calls == [
        (phase40_prereg.A2_LABEL, "cpu", {"adapter_path": adapter, "record_path": record})
    ]
    assert out == {
        "group": group,
        "seed": 1338,
        "record": phase40_prereg.a2_record(group, 1338),
        "record_sha256": phase40_noise._sha256(record),
    }
    assert out["record_sha256"] == phase40_noise._sha256(_COMMITTED_A2)
    with pytest.raises(SystemExit, match="exists"):
        phase40_noise.score_a2(group, 1338, adapter, root=root, device="cpu")
    assert len(calls) == 1


# =================================================================================================
# (5) D-07: tensor-wise identity, never the file digest.
# =================================================================================================


def _artifact(**changes):
    artifact = {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "adapter": {
            "blocks.0.attn.lora_A": torch.arange(6, dtype=torch.float32).reshape(2, 3),
            "blocks.0.attn.lora_B": torch.ones(3, 2),
            "blocks.1.mlp.lora_A": torch.full((2, 2), 0.25),
        },
        "lora_config": {"rank": 2, "alpha": 4.0},
        "base_fingerprint": "abc123",
    }
    artifact.update(changes)
    return artifact


def test_adapter_identity_tensor_wise(tmp_path):
    a, b = tmp_path / "phase40_e2_full_seed1337_adapter.pt", tmp_path / "persona_adapter.pt"
    torch.save(_artifact(), a)
    torch.save(_artifact(), b)
    # The stem effect: identical tensors under two file names differ by sha256.
    assert phase40_noise._sha256(a) != phase40_noise._sha256(b)
    same = phase40_noise.adapter_identity(a, b)
    assert same["tensors_identical"] is True and same["metadata_equal"] is True
    assert same["keys_equal"] is True and same["n_equal"] == same["n_tensors"] == 3
    assert set(same["max_abs_diff"].values()) == {0.0}
    assert same["metadata_keys"] == ["base_fingerprint", "lora_config", "schema_version"]
    assert same["criterion"] is False

    ulp = _artifact()
    t = ulp["adapter"]["blocks.0.attn.lora_B"]
    t[0, 0] = torch.nextafter(t[0, 0], torch.tensor(2.0))
    c = tmp_path / "ulp.pt"
    torch.save(ulp, c)
    off = phase40_noise.adapter_identity(c, b)
    assert off["tensors_identical"] is False and off["n_equal"] == 2
    assert off["max_abs_diff"]["blocks.0.attn.lora_B"] > 0
    assert off["metadata_equal"] is True

    d = tmp_path / "config.pt"
    torch.save(_artifact(lora_config={"rank": 2, "alpha": 8.0}), d)
    config = phase40_noise.adapter_identity(d, b)
    assert config["metadata_equal"] is False and config["tensors_identical"] is False
    assert config["n_equal"] == 3

    missing = _artifact()
    del missing["adapter"]["blocks.1.mlp.lora_A"]
    e = tmp_path / "missing.pt"
    torch.save(missing, e)
    gone = phase40_noise.adapter_identity(e, b)
    assert gone["keys_equal"] is False and gone["tensors_identical"] is False


def _digest_names(source):
    """Name ids and attribute names in adapter_identity's body (the docstring is a Constant)."""
    (fn,) = [
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.FunctionDef) and n.name == "adapter_identity"
    ]
    names = [n.id for n in ast.walk(fn) if isinstance(n, ast.Name)]
    names += [n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)]
    names += [a.name for n in ast.walk(fn) if isinstance(n, ast.Import) for a in n.names]
    assert names, "meta-guard: the scan collected nothing"
    return [x for x in names if "sha256" in x or "hashlib" in x]


def test_adapter_identity_ast_has_no_file_digest():
    source = textwrap.dedent(inspect.getsource(phase40_noise.adapter_identity))
    assert _digest_names(source) == []
    planted = source + "    hashlib.sha256(b'')\n"
    assert _digest_names(planted) == ["hashlib", "sha256"]


def test_comparators_resolve_from_modules():
    found = phase40_noise.comparators()
    assert tuple(found) == (
        "m2_seed1337",
        "full_seed1337",
        "full_seed2024",
        "dialogue_floor_seed1337",
    )
    floor = [
        teach_persona.arm_outputs(
            f"{phase19_erasure.DIALOGUE_FLOOR_ARM}_seed{s}",
            prefix=phase19_erasure.RETRAIN_PREFIX,
        )["adapter"]
        for s in phase19_erasure.DIALOGUE_NOISE_FLOOR_SEEDS
    ]
    assert found["m2_seed1337"] == phase38_rank.m2_adapter_path()
    assert found["full_seed1337"] == phase14_recall.ADAPTER_PATH
    assert phase19_erasure.DIALOGUE_NOISE_FLOOR_SEEDS == (1337, 2024)
    assert [found["dialogue_floor_seed1337"], found["full_seed2024"]] == floor


# =================================================================================================
# (6) D-13: the conditional scorer, through the imported instruments only.
# =================================================================================================


def _d13_rig(monkeypatch, tmp_path, *, a2_rank):
    """Fakes for the model load and the two scoring instruments; the taught value scores lowest
    everywhere, so every measured rank is 1. Returns the call log and the A2 record path."""
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", True)
    monkeypatch.setattr(
        phase40_prereg, "D13_NLLS_PER_ADAPTER", phase40_prereg.d13_nlls_per_adapter()
    )
    slot = phase19_erasure.TARGET_SLOT
    taught = next(f.value for f in phase14_factset.LOCKED_FACTS if f.slot == slot)
    log = {"loads": [], "values": [], "questions": []}

    def load(device, adapter_path=None):
        log["loads"].append((device, adapter_path))
        return ("model", None, "tok", "forbid", "artifact")

    def score_values(model, tok, device, slot_, values, state):
        log["values"].append((slot_, list(values)))
        return [0.0 if v == taught else 1.0 + i for i, v in enumerate(values)]

    def score_question(model, tok, device, entry, candidates, *, taught, state):
        log["questions"].append((entry, list(candidates)))
        return {c: {"nll_mean": 0.0 if c == taught else 1.0 + i} for i, c in enumerate(candidates)}

    monkeypatch.setattr(phase14_recall, "load_adapted_model", load)
    monkeypatch.setattr(phase38_rank, "score_values", score_values)
    monkeypatch.setattr(phase39_ctx, "score_question", score_question)
    record = json.loads(_COMMITTED_A2.read_text(encoding="utf-8"))
    for row in record["exposure"]:
        if row["slot"] == slot:
            row["rank"] = a2_rank
    path = tmp_path / "a2.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return log, path, slot, taught


def test_d13_scores_counts_and_wiring(monkeypatch, tmp_path):
    log, path, slot, taught = _d13_rig(monkeypatch, tmp_path, a2_rank=1)
    out = phase40_noise.d13_scores("adapter.pt", path, "cpu", {})
    plan = phase38_rank.scoring_plan(slots=(slot,))[slot]
    refs = phase18_extraction.reference_set_for(slot)
    entries = [e for e in phase35_prereg.a2_corpus_entries() if e["slot"] == slot]
    assert log["loads"] == [("cpu", "adapter.pt")]
    assert log["values"] == [(slot, [taught] + plan["minted"]), (slot, list(refs))]
    minted = phase39_prereg.minted_members(slot)
    assert log["questions"] == [q for e in entries for q in ((e, list(refs)), (e, list(minted)))]
    n = len(plan["minted"]) + 1 + len(refs) + len(entries) * (len(refs) + len(minted))
    assert n == phase40_prereg.D13_NLLS_PER_ADAPTER == out["n_nlls"]
    anchor = [0.0] + [2.0 + i for i in range(len(plan["minted"]))]
    expected = phase40_prereg.d13_block(
        curve=phase38_rank.curve_for(taught, 0.0, plan["minted"], anchor[1:], plan["sizes"]),
        gate_rank=1,
        a2_rank=1,
        committed_ranks=[1] * len(entries),
        minted_ranks=[1] * len(entries),
    )
    assert expected["measured"] is True
    assert out == {**expected, "n_nlls": n}


def test_d13_scores_returns_the_gate_mismatch_block(monkeypatch, tmp_path):
    # The committed A2 record's pet_name exposure rank is 2; the fake ranks the taught value 1.
    log, path, slot, _taught = _d13_rig(monkeypatch, tmp_path, a2_rank=2)
    out = phase40_noise.d13_scores("adapter.pt", path, "cpu", {})
    assert out["measured"] is False and out["failure_kind"] == "gate_mismatch"
    assert out["n_nlls"] == phase40_prereg.D13_NLLS_PER_ADAPTER
    assert {k: v for k, v in out.items() if k != "n_nlls"} == phase40_prereg.d13_not_measured(
        "gate_mismatch", out["reason"]
    )


def test_d13_scores_refuses_when_not_approved(monkeypatch, tmp_path):
    log, path, _slot, _taught = _d13_rig(monkeypatch, tmp_path, a2_rank=1)
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", False)
    with pytest.raises(SystemExit, match="D-13"):
        phase40_noise.d13_scores("adapter.pt", path, "cpu", {})
    assert log == {"loads": [], "values": [], "questions": []}


# =================================================================================================
# (7) The LaunchAgent.
# =================================================================================================

_PLIST = _ROOT / "artifacts" / "com.personacore.phase40.e2.plist"
_R1B_PLIST = _ROOT / "artifacts" / "com.personacore.phase37.r1b.plist"


def test_plist_mirrors_the_r1b_agent():
    ours = plistlib.loads(_PLIST.read_bytes())
    r1b = plistlib.loads(_R1B_PLIST.read_bytes())
    assert ours["Label"] == "com.personacore.phase40.e2"
    args = r1b["ProgramArguments"]
    assert ours["ProgramArguments"] == [
        "/usr/bin/caffeinate",
        "-dims",
        args[2],
        args[3].replace("scripts/phase37_r1b.py", "scripts/phase40_noise.py"),
        "run",
    ]
    assert args[2].endswith("/.venv/bin/python") and args[3].endswith("scripts/phase37_r1b.py")
    assert ours["RunAtLoad"] is False and ours["KeepAlive"] is False
    assert ours["StandardOutPath"] == r1b["StandardOutPath"].replace(
        "logs/phase37_r1b.out", "logs/phase40_e2.out"
    )
    assert ours["StandardErrorPath"] == r1b["StandardErrorPath"].replace(
        "logs/phase37_r1b.err", "logs/phase40_e2.err"
    )
    assert ours["StandardOutPath"].endswith("logs/phase40_e2.out")
    assert ours["StandardErrorPath"].endswith("logs/phase40_e2.err")
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"
    assert ours["ProcessType"] == "Interactive"
    changed = {"Label", "ProgramArguments", "StandardOutPath", "StandardErrorPath"}
    assert set(ours) == set(r1b)
    assert {k: v for k, v in ours.items() if k not in changed} == {
        k: v for k, v in r1b.items() if k not in changed
    }
