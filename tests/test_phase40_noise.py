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
import math
import pathlib
import plistlib
import re
import shutil
import subprocess
import sys
import textwrap
import types

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

import mitigation_gate  # noqa: E402  (scripts/ is not a package)
import phase14_factset  # noqa: E402  (same)
import phase14_recall  # noqa: E402  (same)
import phase18_extraction  # noqa: E402  (same)
import phase19_erasure  # noqa: E402  (same; never aliased)
import phase19_floor  # noqa: E402  (same)
import phase19_run  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same)
import phase37_prereg  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)
import phase38_rank  # noqa: E402  (same)
import phase39_ctx  # noqa: E402  (same)
import phase39_prereg  # noqa: E402  (same)
import phase40_noise  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase40_prereg  # noqa: E402  (same; frozen: import only)
import teach_persona  # noqa: E402  (same)

from personacore.checkpoint import ADAPTER_SCHEMA_VERSION  # noqa: E402
from personacore.provenance import refuse_if_dirty  # noqa: E402
from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase35_prereg import _slot_census_failures  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402

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


@pytest.fixture(autouse=True)
def _tracked_budget_only(monkeypatch):
    """Plan 06 interfaces (4): committed_budget reads the committed budget, and spent() never reads
    a committed seed record's clock for a tmp ledger's end line (the real ledger is untracked
    here, so read_ledger's append-only proof skips it too)."""
    monkeypatch.setattr(phase36_caps, "tracked_files", lambda: [phase36_caps.BUDGET_RECORD])


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


# =================================================================================================
# (8) Plan 06: preflight, the rehearsal identity and its disclosure.
# =================================================================================================


def _tmp_rig(monkeypatch, tmp_path, seeds=(1337, 2024)):
    """A rehearsal (tmp) root on `_repo_rig`: explicit tmp ledger and heartbeat, device cpu, HEAD
    stubbed to "h1"."""
    dirty = []
    root = _repo_rig(monkeypatch, tmp_path, dirty=dirty)
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h1")
    ledger, heartbeat = tmp_path / "ledger.jsonl", tmp_path / "heartbeat.jsonl"
    return types.SimpleNamespace(
        root=root,
        dirty=dirty,
        ledger=ledger,
        heartbeat=heartbeat,
        identity=tmp_path / "identity.json",
        kw={
            "root": root,
            "ledger_path": ledger,
            "heartbeat_path": heartbeat,
            "device": "cpu",
            "seeds": tuple(seeds),
        },
    )


def _real_root_rig(monkeypatch, tmp_path, *, identity=True):
    """The real-root branches against a rig (plan 06 interfaces (3)): phase40_noise._ROOT and the
    milestone ledger / heartbeat point into it; HEAD is the repository's real HEAD (the disclosure
    runs git log in _REPO); run_inputs, the caps and the device are stubbed."""
    dirty = []
    root = _repo_rig(monkeypatch, tmp_path, dirty=dirty)
    monkeypatch.setattr(phase40_noise, "_ROOT", root)
    monkeypatch.setattr(phase36_ledger, "_ROOT", root)
    monkeypatch.setattr(phase36_ledger, "LEDGER_PATH", "ledger/rig_ledger.jsonl")
    heartbeat = root / "data" / "rig_heartbeat.jsonl"
    monkeypatch.setattr(phase36_ledger, "HEARTBEAT_PATH", heartbeat)
    head = _git("rev-parse", "HEAD")
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: head)
    monkeypatch.setattr(phase40_noise, "run_inputs", lambda: ())
    monkeypatch.setattr(phase36_caps, "check_unit_caps", lambda front, **counts: dict(counts))
    monkeypatch.setattr(phase40_noise, "_device", lambda: "mps")
    if identity:
        phase40_noise.record_rehearsal(
            phase40_noise.rehearsal_identity_path(), seeds=phase40_prereg.SEEDS[:2]
        )
    return types.SimpleNamespace(
        root=root,
        dirty=dirty,
        ledger=root / "ledger" / "rig_ledger.jsonl",
        heartbeat=heartbeat,
        head=head,
        kw={},
    )


def _ledger(path, *events):
    """Append ``(event, seed)`` lines for run_id(seed) (an end names seed_record(seed))."""
    for event, seed in events:
        extra = {}
        if event == "end":
            extra["record"] = phase40_prereg.seed_record(seed)
        if event == "lost":
            extra.update(seconds=0.0, flag=phase36_ledger.NO_BEAT_FLAG)
        phase36_ledger.append(
            event,
            run_id=phase40_prereg.run_id(seed),
            phase=40,
            front="E2",
            ledger_path=path,
            **extra,
        )


def _lines(path):
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def _raise(message):
    def planted(*args, **kwargs):
        raise SystemExit(message)

    return planted


def _launch(rig, monkeypatch):
    """The launch every refusal row goes through: run(), whose preflight refuses before the first
    start line; a training or scoring call would mean it did not."""
    calls = []
    monkeypatch.setattr(phase40_noise, "train_adapter", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(phase40_noise, "score_a2", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(phase40_noise, "d13_scores", lambda *a, **k: calls.append(a))
    kw = dict(rig.kw)
    if "root" in kw:
        kw["rehearsal_identity"] = rig.identity
    try:
        return phase40_noise.run(**kw)
    finally:
        assert calls == []


def _plant(path, data=b"planted"):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _row_dirty(rig, mp):
    mp.setattr(phase40_noise, "refuse_if_dirty", _raise("[provenance] REFUSING: planted dirt"))
    return "planted dirt"


def _row_unknown_sha(rig, mp):
    mp.setattr(phase40_noise, "git_sha", lambda: "unknown")
    return "git_sha[(][)] could not read HEAD"


def _row_open_attempt(rig, mp):
    _ledger(rig.ledger, ("start", 1337))
    return re.escape(f"open attempt for {phase40_prereg.run_id(1337)}") + ".*reconcile first"


def _row_require_launch(rig, mp):
    mp.setattr(phase36_ledger, "require_launch", _raise("[phase36_ledger] planted PAUSE"))
    return "planted PAUSE"


def _row_caps(rig, mp):
    mp.setattr(phase36_caps, "check_unit_caps", _raise("[phase36_caps] planted cap"))
    return "planted cap"


def _row_no_ledger_path(rig, mp):
    rig.kw["ledger_path"] = None
    return "explicit ledger_path and heartbeat_path"


def _row_no_heartbeat_path(rig, mp):
    rig.kw["heartbeat_path"] = None
    return "explicit ledger_path and heartbeat_path"


def _row_milestone_ledger(rig, mp):
    rig.kw["ledger_path"] = phase36_ledger._ROOT / phase36_ledger.LEDGER_PATH
    return "never the milestone ones"


def _row_milestone_heartbeat(rig, mp):
    rig.kw["heartbeat_path"] = phase36_ledger.HEARTBEAT_PATH
    return "never the milestone ones"


def _row_tmp_mps(rig, mp):
    rig.kw["device"] = "mps"
    return "a rehearsal runs on CPU"


def _row_tmp_no_seeds(rig, mp):
    rig.kw["seeds"] = None
    return "a rehearsal names its seeds"


def _row_tmp_seeds_out_of_order(rig, mp):
    rig.kw["seeds"] = (2024, 1337)
    return "a rehearsal names its seeds"


def _row_real_cpu(rig, mp):
    mp.setattr(phase40_noise, "_device", lambda: "cpu")
    return "E2 runs on MPS on the real root"


def _row_real_subset(rig, mp):
    rig.kw["seeds"] = (1337,)
    return "the real root runs every seed of SEEDS"


def _row_real_ledger(rig, mp):
    rig.kw["ledger_path"] = rig.root / "ledger" / "other.jsonl"
    return "the real root runs every seed of SEEDS"


def _row_real_no_identity(rig, mp):
    return "rehearsal identity.*is missing"


def _row_real_prereg_drift(rig, mp):
    path = phase40_noise.rehearsal_identity_path()
    identity = json.loads(path.read_text(encoding="utf-8"))
    identity["module_sha256"][phase40_noise.PREREG_FILE] = "0" * 64
    path.write_text(json.dumps(identity), encoding="utf-8")
    return "scripts/phase40_prereg.py changed after the rehearsal"


_TMP_ROWS = (
    _row_dirty,
    _row_unknown_sha,
    _row_open_attempt,
    _row_require_launch,
    _row_caps,
    _row_no_ledger_path,
    _row_no_heartbeat_path,
    _row_milestone_ledger,
    _row_milestone_heartbeat,
    _row_tmp_mps,
    _row_tmp_no_seeds,
    _row_tmp_seeds_out_of_order,
)
_REAL_ROWS = (
    _row_real_cpu,
    _row_real_subset,
    _row_real_ledger,
    _row_real_no_identity,
    _row_real_prereg_drift,
)


@pytest.mark.parametrize(
    "plant", _TMP_ROWS + _REAL_ROWS, ids=[f.__name__[5:] for f in _TMP_ROWS + _REAL_ROWS]
)
def test_preflight_refusals(monkeypatch, tmp_path, plant):
    if plant in _REAL_ROWS:
        rig = _real_root_rig(monkeypatch, tmp_path, identity=plant is not _row_real_no_identity)
    else:
        rig = _tmp_rig(monkeypatch, tmp_path)
    match = plant(rig, monkeypatch)
    ledger_before = _lines(rig.ledger)
    with pytest.raises(SystemExit, match=match):
        _launch(rig, monkeypatch)
    assert _lines(rig.ledger) == ledger_before
    assert not rig.heartbeat.exists()


def _missing_input(rig, mp, owner, name):
    missing = rig.root / "missing" / name
    mp.setattr(owner, name, missing)
    return missing


@pytest.mark.parametrize(
    "which",
    [name for _, name in _RUN_INPUTS] + ["m2_seed1337", "full_seed2024", "dialogue_floor_seed1337"],
)
def test_preflight_refuses_a_missing_run_input(monkeypatch, tmp_path, which):
    rig = _tmp_rig(monkeypatch, tmp_path)
    owners = {name: owner for owner, name in _RUN_INPUTS}
    if which in owners:
        missing = _missing_input(rig, monkeypatch, owners[which], which)
    else:
        missing = phase40_noise.comparators()[which]
        missing.unlink()
    with pytest.raises(SystemExit, match=re.escape(f"{missing} is missing")):
        _launch(rig, monkeypatch)
    assert not rig.ledger.exists() and not rig.heartbeat.exists()


def _pending_outputs(group, seed, root, *, rehearsal):
    """Every output path a pending seed must not have yet, by name."""
    paths = phase40_noise.arm_paths(group, seed, rehearsal=rehearsal)
    arm = phase40_noise.arm_name(group, seed, rehearsal=rehearsal)
    return {
        "seed_record": root / phase40_prereg.seed_record(seed),
        "a2_record": root / phase40_prereg.a2_record(group, seed),
        "adapter": paths["adapter"],
        "checkpoint": paths["checkpoint"],
        "bin": paths["bin"],
        "mask": paths["mask"],
        "csv": paths["csv"],
        "moved_csv": root / "data" / phase40_noise.CSV_DIR / arm / "run.csv",
    }


@pytest.mark.parametrize("group", ["full", "m2"])
@pytest.mark.parametrize(
    "key", ["seed_record", "a2_record", "adapter", "checkpoint", "bin", "mask", "csv", "moved_csv"]
)
def test_preflight_refuses_an_existing_output_of_a_pending_seed(monkeypatch, tmp_path, key, group):
    rig = _tmp_rig(monkeypatch, tmp_path)
    path = _plant(_pending_outputs(group, 2024, rig.root, rehearsal=True)[key])
    with pytest.raises(SystemExit, match=re.escape(f"{path} exists")):
        _launch(rig, monkeypatch)
    assert not rig.ledger.exists() and not rig.heartbeat.exists()


def test_preflight_ok_prints_the_line(monkeypatch, tmp_path, capsys):
    rig = _tmp_rig(monkeypatch, tmp_path)
    pf = phase40_noise.preflight(**rig.kw)
    out = capsys.readouterr().out
    expected = (
        f"PREFLIGHT OK h1 device=cpu pending=1337,2024 d13={phase40_prereg.D13_INCLUDED} "
        f"projection_h={phase40_prereg.E2_PROJECTION_HOURS!r} "
        f"stop_h={phase40_prereg.E2_STOP_HOURS!r} spent_E2_s=0.0"
    )
    assert expected in out.splitlines()
    assert set(pf) == {
        "root",
        "pending",
        "launch_git_sha",
        "launch_modules",
        "device",
        "gate",
        "rehearsal_disclosure",
        "dropped_attempts",
    }
    assert pf["pending"] == (1337, 2024) and isinstance(pf["pending"], tuple)
    assert pf["root"] == rig.root and pf["device"] == "cpu" and pf["launch_git_sha"] == "h1"
    assert pf["launch_modules"] == phase40_noise.module_sha256()
    assert pf["gate"]["front"] == "E2"
    assert pf["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
    assert pf["dropped_attempts"] == {}
    (call,) = rig.dirty
    assert call["pathspec"] == phase40_noise.LAUNCH_PATHSPEC
    assert call["cwd"] == phase40_noise._REPO and call["who"] == "phase40_noise"
    assert not rig.ledger.exists() and not rig.heartbeat.exists()


def test_preflight_pending_after_a_crash(monkeypatch, tmp_path):
    rig = _tmp_rig(monkeypatch, tmp_path, seeds=phase40_prereg.SEEDS)
    _ledger(rig.ledger, ("start", 1337), ("end", 1337), ("start", 2024), ("lost", 2024))
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", False)
    assert phase40_noise.preflight(**rig.kw)["pending"] == phase40_prereg.SEEDS[2:]
    # A whole seed is never pending and its outputs are never checked for absence.
    for path in _pending_outputs("full", 1337, rig.root, rehearsal=True).values():
        if path.name != "run.csv" or "data" in path.parts:
            _plant(path)
    # The declined-rerun branch: a dropped seed without a manifest is not pending and its crashed
    # outputs stay in place.
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", True)
    crashed = _pending_outputs("full", 2024, rig.root, rehearsal=True)
    for key in ("adapter", "checkpoint", "csv", "a2_record"):
        _plant(crashed[key])
    pf = phase40_noise.preflight(**rig.kw)
    assert pf["pending"] == phase40_prereg.SEEDS[2:]
    assert 1337 not in pf["pending"] and 2024 not in pf["pending"]
    assert pf["dropped_attempts"] == {}
    # Nothing left to run refuses.
    only = _tmp_rig(monkeypatch, tmp_path / "only", seeds=(1337,))
    _ledger(only.ledger, ("start", 1337), ("end", 1337))
    with pytest.raises(SystemExit, match="nothing to run"):
        phase40_noise.preflight(**only.kw)


def _expected_pathspec(outcomes):
    excluded = []
    for seed in phase40_prereg.SEEDS:
        if outcomes.get(seed) not in ("whole", "dropped"):
            continue
        excluded.append(phase40_prereg.seed_record(seed))
        excluded += [phase40_prereg.a2_record(g, seed) for g in phase40_prereg.GROUPS]
        if outcomes[seed] == "dropped":
            excluded += [
                phase40_noise.arm_paths(g, seed)["csv"]
                .parent.relative_to(teach_persona._REPO_ROOT)
                .as_posix()
                for g in phase40_prereg.GROUPS
            ]
    return phase40_noise.LAUNCH_PATHSPEC + tuple(":(exclude)" + rel for rel in excluded)


def test_preflight_relaunch_pathspec_excludes_only_the_runs_own_records(monkeypatch, tmp_path):
    rig = _real_root_rig(monkeypatch, tmp_path)
    _ledger(None, ("start", 1337), ("end", 1337), ("start", 2024), ("lost", 2024))
    assert rig.ledger.exists()
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", False)
    _plant(rig.root / phase40_prereg.seed_record(1337))
    for group in phase40_prereg.GROUPS:
        _plant(rig.root / phase40_prereg.a2_record(group, 1337))
    _plant(rig.root / phase40_prereg.a2_record("full", 2024))
    expected = _expected_pathspec({1337: "whole", 2024: "dropped"})
    assert expected[len(phase40_noise.LAUNCH_PATHSPEC) :] == (
        ":(exclude)results/phase40_seed1337.json",
        ":(exclude)results/phase40_a2_full_seed1337.json",
        ":(exclude)results/phase40_a2_m2_seed1337.json",
        ":(exclude)results/phase40_seed2024.json",
        ":(exclude)results/phase40_a2_full_seed2024.json",
        ":(exclude)results/phase40_a2_m2_seed2024.json",
        ":(exclude)results/phase40_e2_full_seed2024",
        ":(exclude)results/phase40_e2_m2_seed2024",
    )
    for rerun in (False, True):  # True with no manifest: the real-root declined-rerun row
        monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", rerun)
        before = len(rig.dirty)
        pf = phase40_noise.preflight()
        assert pf["pending"] == phase40_prereg.SEEDS[2:]
        assert len(rig.dirty) == before + 1
        call = rig.dirty[-1]
        assert call["cwd"] == phase40_noise._REPO
        assert tuple(call["pathspec"]) == expected
    # A tmp root's pathspec is LAUNCH_PATHSPEC alone.
    other = tmp_path / "rehearsal"
    phase40_noise.preflight(
        root=other,
        ledger_path=tmp_path / "rh_ledger.jsonl",
        heartbeat_path=tmp_path / "rh_heartbeat.jsonl",
        device="cpu",
        seeds=(1337,),
    )
    assert tuple(rig.dirty[-1]["pathspec"]) == phase40_noise.LAUNCH_PATHSPEC


def test_preflight_pathspec_on_a_real_git_rig(tmp_path):
    repo = tmp_path / "git"

    def git(*args):
        subprocess.run(("git", *args), cwd=repo, capture_output=True, text=True, check=True)

    _plant(repo / "scripts" / "a.py", b"x = 1\n")
    _plant(repo / "results" / ".keep", b"")
    git("init", "-q")
    git("add", "scripts/a.py", "results/.keep")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "rig")
    outcomes = dict.fromkeys(phase40_prereg.SEEDS, "not_run") | {1337: "whole", 2024: "dropped"}
    pathspec = phase40_noise._launch_pathspec(outcomes)
    assert pathspec == _expected_pathspec(outcomes)

    def check(spec):
        return refuse_if_dirty(who="rig", detail="rig", pathspec=spec, cwd=repo)

    for rel in (
        "results/phase40_seed1337.json",
        "results/phase40_a2_full_seed1337.json",
        "results/phase40_a2_full_seed2024.json",
        "results/phase40_e2_full_seed2024/run.csv",
    ):
        _plant(repo / rel)
    assert check(pathspec) == ""
    for rel, named in (
        ("results/phase40_seed1338.json", "results/phase40_seed1338.json"),
        ("results/phase40_e2_full_seed1337/run.csv", "results/phase40_e2_full_seed1337/"),
        ("scripts/b.py", "scripts/b.py"),
    ):
        planted = _plant(repo / rel)
        with pytest.raises(SystemExit, match=re.escape(named)):
            check(pathspec)
        planted.unlink()
        if planted.parent.name.startswith("phase40_e2"):
            planted.parent.rmdir()
    assert check(pathspec) == ""
    nothing = phase40_noise._launch_pathspec(dict.fromkeys(phase40_prereg.SEEDS, "not_run"))
    assert nothing == phase40_noise.LAUNCH_PATHSPEC
    with pytest.raises(SystemExit, match=re.escape("results/phase40_seed1337.json")):
        check(nothing)


def test_rehearsal_identity_and_disclosure(monkeypatch, tmp_path):
    monkeypatch.setattr(phase40_noise, "_ROOT", tmp_path / "a")
    path = phase40_noise.rehearsal_identity_path()
    assert path == tmp_path / "a" / "data" / "phase40_rehearsal.json"
    monkeypatch.setattr(phase40_noise, "_ROOT", tmp_path)
    path = phase40_noise.rehearsal_identity_path()
    assert path == tmp_path / "data" / "phase40_rehearsal.json"
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h1")
    first = phase40_noise.record_rehearsal(path, seeds=(1337, 2024))
    assert first["status"] == "recorded"
    identity = json.loads(path.read_text(encoding="utf-8"))
    assert set(identity) == {"git_sha", "module_sha256", "seeds", "started_utc"}
    assert identity["git_sha"] == "h1" and identity["seeds"] == [1337, 2024]
    assert identity["module_sha256"] == {
        rel: phase40_noise._sha256(_ROOT / rel) for rel in phase40_noise.DISCLOSED_MODULES
    }
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h2")
    kept = phase40_noise.record_rehearsal(path, seeds=(1337, 2024))
    assert kept == {"status": "kept", **identity}
    assert json.loads(path.read_text(encoding="utf-8")) == identity
    with pytest.raises(SystemExit, match="different seed set"):
        phase40_noise.record_rehearsal(path, seeds=(1337,))
    assert json.loads(path.read_text(encoding="utf-8")) == identity

    # The disclosure: git log stubbed.
    logs = {"log": "", "show": ""}

    def fake_run(args, **kw):
        assert kw["cwd"] == phase40_noise._REPO
        out = logs["log"] if args[1] == "log" else logs["show"]
        if args[1] == "log":
            assert args[3] == "h1..h9" and tuple(args[5:]) == phase40_noise.DISCLOSED_MODULES
        return types.SimpleNamespace(stdout=out)

    monkeypatch.setattr(phase40_noise.subprocess, "run", fake_run)
    launch = dict(identity["module_sha256"])
    empty = phase40_noise.rehearsal_disclosure(
        identity, launch_git_sha="h9", launch_module_sha256=launch
    )
    assert empty["commits"] == [] and "no commit" in empty["statement"]
    assert empty["prereg_changed"] is False and empty["driver_changed"] is False
    assert empty["seeds_read"] == [1337, 2024]
    launch[phase40_noise.DRIVER_FILE] = "f" * 64
    with pytest.raises(SystemExit, match="without a commit"):
        phase40_noise.rehearsal_disclosure(
            identity, launch_git_sha="h9", launch_module_sha256=launch
        )
    logs.update(log="c0ffee\tfix the driver\n", show="scripts/phase40_noise.py\nREADME.md\n")
    moved = phase40_noise.rehearsal_disclosure(
        identity, launch_git_sha="h9", launch_module_sha256=launch
    )
    assert moved["commits"] == [
        {"sha": "c0ffee", "reason": "fix the driver", "modules": [phase40_noise.DRIVER_FILE]}
    ]
    assert moved["changed"] == {phase40_noise.DRIVER_FILE: True, phase40_noise.PREREG_FILE: False}
    assert moved["driver_changed"] is True and moved["prereg_changed"] is False
    assert "fix the driver" not in moved["statement"] and "1 commit" in moved["statement"]


def test_preflight_rehearsal_disclosure_on_the_real_root(monkeypatch, tmp_path):
    rig = _real_root_rig(monkeypatch, tmp_path)
    pf = phase40_noise.preflight()
    identity = json.loads(phase40_noise.rehearsal_identity_path().read_text(encoding="utf-8"))
    assert pf["rehearsal_disclosure"] == phase40_noise.rehearsal_disclosure(
        identity, launch_git_sha=rig.head, launch_module_sha256=phase40_noise.module_sha256()
    )
    assert pf["rehearsal_disclosure"]["commits"] == []
    assert pf["device"] == "mps" and pf["pending"] == phase40_prereg.SEEDS


# =================================================================================================
# (9) Plan 06: R-3 b — partial_outputs, drop_attempt, declare_relaunch, rerun_seeds.
# =================================================================================================


def _plant_crash(root, seed):
    """A crash right after the full A2 pass of ``seed``'s rehearsal arms: the full adapter and
    checkpoint, both bins and masks, the m2 in-process csv, the full moved csv, the full A2
    record. Returns {rel: path} of every planted file."""
    full = phase40_noise.arm_paths("full", seed, rehearsal=True)
    m2 = phase40_noise.arm_paths("m2", seed, rehearsal=True)
    arm = phase40_noise.arm_name("full", seed, rehearsal=True)
    planted = [
        full["adapter"],
        full["checkpoint"],
        full["bin"],
        full["mask"],
        m2["bin"],
        m2["mask"],
        m2["csv"],
        root / "data" / phase40_noise.CSV_DIR / arm / "run.csv",
        root / phase40_prereg.a2_record("full", seed),
    ]
    return {_plant(p, str(p).encode()).relative_to(root).as_posix(): p for p in planted}


def _dropped_rig(monkeypatch, tmp_path, seeds=phase40_prereg.SEEDS):
    rig = _tmp_rig(monkeypatch, tmp_path, seeds=seeds)
    _ledger(rig.ledger, ("start", 1337), ("end", 1337), ("start", 2024), ("lost", 2024))
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", True)
    rig.crash = _plant_crash(rig.root, 2024)
    return rig


def _lost_utc(rig, seed):
    return phase40_prereg.lost_attempts(phase36_ledger.read_ledger(rig.ledger), seed)[-1]


def _drop(rig, seed=2024, **kw):
    args = {
        "cause_note": "x",
        "approved": "approved",
        "head_at_dropped_attempt": "h1",
        "root": rig.root,
        "ledger_path": rig.ledger,
    }
    return phase40_noise.drop_attempt(seed, **{**args, **kw})


def test_crash_drop_attempt_moves_and_lists(monkeypatch, tmp_path, capsys):
    rig = _dropped_rig(monkeypatch, tmp_path)
    listed = phase40_noise.partial_outputs(2024, root=rig.root)
    assert listed == sorted(rig.crash.items())
    dropped_root = rig.root / phase40_prereg.DROPPED_ROOT
    ledger = _lines(rig.ledger)

    def refused(match, seed=2024, ledger_path=None, **kw):
        with pytest.raises(SystemExit, match=match):
            _drop(rig, seed, **({"ledger_path": ledger_path} if ledger_path else {}), **kw)
        assert phase40_noise.partial_outputs(2024, root=rig.root) == listed
        assert not dropped_root.exists()
        assert _lines(rig.ledger) == ledger

    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", False)
    refused("DROPPED_SEED_RERUN")
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", True)
    refused("only a crashed attempt", seed=1337)  # whole: never a completed seed
    refused("only a crashed attempt", seed=1338)  # not_run
    still_open = tmp_path / "open.jsonl"
    _ledger(still_open, ("start", 2024), ("lost", 2024), ("start", 2024))
    refused("reconcile first", ledger_path=still_open)
    later = tmp_path / "later.jsonl"
    _ledger(later, ("start", 1337), ("end", 1337), ("start", 1337), ("lost", 1337))
    refused("a whole seed has a later attempt", seed=1337, ledger_path=later)
    record = _plant(rig.root / phase40_prereg.seed_record(2024))
    refused("crash rule [(]i[)]")
    record.unlink()
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "unknown")
    refused("could not read HEAD")
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h1")
    refused("cause_note is empty", cause_note=" ")
    refused("lacks Rafael's 'approved'", approved="ok")
    refused("lacks Rafael's 'approved'", approved="not approved")
    refused("lacks Rafael's 'approved'", approved="unapproved")
    refused("head_change_declared None: HEAD h0 -> h1", head_at_dropped_attempt="h0")
    # The WR-01 ledger refuses preflight too, with nothing written.
    with pytest.raises(SystemExit, match="a whole seed has a later attempt"):
        phase40_noise.preflight(**{**rig.kw, "ledger_path": later})
    assert not rig.heartbeat.exists()

    utc = _lost_utc(rig, 2024)
    rel_dir = phase40_prereg.dropped_attempt_dir(2024, utc)
    digests = {rel: phase40_noise._sha256(path) for rel, path in listed}
    manifest = _drop(rig)
    assert f"DROPPED 2024 {rel_dir} kept={len(listed)}" in capsys.readouterr().out
    assert tuple(manifest) == phase40_prereg.DROPPED_MANIFEST_KEYS
    assert manifest["relaunch_git_sha"] == "h1" and manifest["lost_utc"] == utc
    assert manifest["head_change_declared"] is None
    assert manifest["kept"] == [
        {"from": rel, "path": f"{rel_dir}/{rel}", "sha256": digests[rel]} for rel, _ in listed
    ]
    for item in manifest["kept"]:
        assert phase40_noise._sha256(rig.root / item["path"]) == item["sha256"]
        assert not (rig.root / item["from"]).exists()
    assert phase40_noise.partial_outputs(2024, root=rig.root) == []
    m2_csv_dir = phase40_noise.arm_paths("m2", 2024, rehearsal=True)["csv"].parent
    full_arm = phase40_noise.arm_name("full", 2024, rehearsal=True)
    assert not m2_csv_dir.exists()
    assert not (rig.root / "data" / phase40_noise.CSV_DIR / full_arm).exists()
    on_disk = json.loads((rig.root / rel_dir / phase40_prereg.DROPPED_MANIFEST).read_text())
    assert on_disk == manifest
    assert phase40_prereg.dropped_manifest_failures(manifest, seed=2024, lost_utc=utc) == []
    with pytest.raises(SystemExit, match="write-once"):
        _drop(rig)
    assert _lines(rig.ledger) == ledger

    # A crash before any output keeps nothing; a declared HEAD change is accepted.
    _ledger(rig.ledger, ("start", 1339), ("lost", 1339))
    early = _drop(rig, 1339, head_at_dropped_attempt="h0", head_change_declared="rebased")
    assert early["kept"] == [] and early["head_at_dropped_attempt"] == "h0"


def test_drop_attempt_declare_relaunch_refusals(monkeypatch, tmp_path):
    rig = _dropped_rig(monkeypatch, tmp_path)
    _drop(rig)
    rel_dir = rig.root / phase40_prereg.dropped_attempt_dir(2024, _lost_utc(rig, 2024))
    args = {
        "head_change_declared": "y",
        "approved": "approved",
        "root": rig.root,
        "ledger_path": rig.ledger,
    }

    def declarations():
        return sorted(p.name for p in rel_dir.glob(phase40_prereg.relaunch_declaration_name("*")))

    with pytest.raises(SystemExit, match="drop-time HEAD"):
        phase40_noise.declare_relaunch(2024, **args)
    assert declarations() == []
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h2")
    for change, match in (
        ({"head_change_declared": " "}, "head_change_declared is empty"),
        ({"approved": "ok"}, "lacks Rafael's 'approved'"),
        ({"approved": "not approved"}, "lacks Rafael's 'approved'"),
    ):
        with pytest.raises(SystemExit, match=match):
            phase40_noise.declare_relaunch(2024, **{**args, **change})
        assert declarations() == []
    with pytest.raises(SystemExit, match="only a crashed attempt"):
        phase40_noise.declare_relaunch(1337, **args)
    _ledger(rig.ledger, ("start", 1339), ("lost", 1339))
    with pytest.raises(SystemExit, match="no manifest"):
        phase40_noise.declare_relaunch(1339, **args)
    declaration = phase40_noise.declare_relaunch(2024, **args)
    assert declaration == {
        "launch_git_sha": "h2",
        "head_change_declared": "y",
        "approved": "approved",
    }
    assert declarations() == [phase40_prereg.relaunch_declaration_name("h2")]
    written = rel_dir / phase40_prereg.relaunch_declaration_name("h2")
    assert json.loads(written.read_text(encoding="utf-8")) == declaration
    with pytest.raises(SystemExit, match="write-once"):
        phase40_noise.declare_relaunch(2024, **args)


def _attempt_entry(root, rel_dir, declarations=()):
    rel = f"{rel_dir}/{phase40_prereg.DROPPED_MANIFEST}"
    manifest = json.loads((root / rel).read_text(encoding="utf-8"))
    listed = []
    for name in declarations:
        d_rel = f"{rel_dir}/{name}"
        d = json.loads((root / d_rel).read_text(encoding="utf-8"))
        listed.append({**d, "path": d_rel, "sha256": phase40_noise._sha256(root / d_rel)})
    return {
        **manifest,
        "manifest": rel,
        "manifest_sha256": phase40_noise._sha256(root / rel),
        "relaunch_declarations": listed,
    }


def test_preflight_rerun_needs_the_dropped_manifest(monkeypatch, tmp_path):
    rig = _dropped_rig(monkeypatch, tmp_path, seeds=(1337, 2024, 1338))
    manifest = _drop(rig)
    rel_dir = phase40_prereg.dropped_attempt_dir(2024, _lost_utc(rig, 2024))
    lines = phase36_ledger.read_ledger(rig.ledger)
    outcomes = phase40_prereg.seed_outcomes(lines, (1337, 2024, 1338))
    assert phase40_noise.rerun_seeds(lines, outcomes, root=rig.root) == frozenset({2024})
    pf = phase40_noise.preflight(**rig.kw)
    assert pf["pending"] == (2024, 1338)
    assert pf["dropped_attempts"] == {2024: [_attempt_entry(rig.root, rel_dir)]}

    # Without the manifest (moved out to evidence) 2024 is not pending: the declined-rerun branch.
    manifest_path = rig.root / rel_dir / phase40_prereg.DROPPED_MANIFEST
    evidence = _plant(tmp_path / "evidence" / "manifest.json", manifest_path.read_bytes())
    manifest_path.unlink()
    assert phase40_noise.preflight(**rig.kw)["pending"] == (1338,)
    shutil.move(str(evidence), str(manifest_path))

    def refused(match):
        with pytest.raises(SystemExit, match=match):
            phase40_noise.preflight(**rig.kw)
        assert not rig.heartbeat.exists()

    kept = rig.root / manifest["kept"][0]["path"]
    original = kept.read_bytes()
    kept.write_bytes(b"changed")
    refused("sha256")
    kept.write_bytes(original)
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h2")
    refused("HEAD moved after drop_attempt [(]h1 -> h2[)]: STOP")
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h1")
    adapter = _plant(phase40_noise.arm_paths("full", 2024, rehearsal=True)["adapter"])
    refused(re.escape(f"{adapter} exists"))
    adapter.unlink()

    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h2")
    phase40_noise.declare_relaunch(
        2024,
        head_change_declared="y",
        approved="approved",
        root=rig.root,
        ledger_path=rig.ledger,
    )
    declared = [phase40_prereg.relaunch_declaration_name("h2")]
    pf = phase40_noise.preflight(**rig.kw)
    assert pf["pending"] == (2024, 1338)
    assert pf["dropped_attempts"] == {2024: [_attempt_entry(rig.root, rel_dir, declared)]}

    # A second crash of 2024, dropped under h3: both attempts listed oldest first; the older one
    # is checked for integrity only.
    _ledger(rig.ledger, ("start", 2024), ("lost", 2024))
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h3")
    _plant_crash(rig.root, 2024)
    _drop(rig, head_at_dropped_attempt="h3")
    rel_dir2 = phase40_prereg.dropped_attempt_dir(2024, _lost_utc(rig, 2024))
    assert rel_dir2 != rel_dir
    pf = phase40_noise.preflight(**rig.kw)
    assert pf["pending"] == (2024, 1338)
    assert pf["dropped_attempts"] == {
        2024: [_attempt_entry(rig.root, rel_dir, declared), _attempt_entry(rig.root, rel_dir2)]
    }
    older = rig.root / rel_dir / phase40_prereg.DROPPED_MANIFEST
    older_bytes = older.read_bytes()
    older.unlink()
    refused("no manifest")
    older.write_bytes(older_bytes)

    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", False)
    lines = phase36_ledger.read_ledger(rig.ledger)
    outcomes = phase40_prereg.seed_outcomes(lines, (1337, 2024, 1338))
    assert phase40_noise.rerun_seeds(lines, outcomes, root=rig.root) == frozenset()
    assert phase40_noise.preflight(**rig.kw)["pending"] == (1338,)


# =================================================================================================
# (10) Plan 06: run — one ledger attempt per seed, whole seeds, stop, crash, relaunch, D-13.
# =================================================================================================


def _measured(**changes):
    """A REAL prereg.d13_block measured block (interfaces item (6))."""
    n = phase19_erasure.N_TARGET_QUESTIONS
    args = {
        "curve": {"8": 0.5},
        "gate_rank": 1,
        "a2_rank": 1,
        "committed_ranks": [1] * n,
        "minted_ranks": [1] * n,
    }
    return phase40_prereg.d13_block(**{**args, **changes})


def _run_fakes(monkeypatch, rig, *, d13=None, fail=None):
    """The real train_adapter / score_a2 over fake teach_persona and A2 pins, wrapped to log the
    call order; d13_scores faked (``d13(seed)`` -> its return, default a measured block); the
    ledger calls, the seed-record write and the heartbeat threads logged too."""
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", True)
    monkeypatch.setattr(phase40_noise, "_release", lambda: None)
    rig.log, rig.threads, rig.trained = [], [], []
    monkeypatch.setattr(teach_persona, "train_arm", _fake_train(rig.trained))

    def fake_a2(arm, device, **kw):
        if fail is not None:
            fail(kw["record_path"])
        shutil.copyfile(_COMMITTED_A2, kw["record_path"])

    monkeypatch.setattr(phase19_erasure, "run_erasure_arm", fake_a2)
    train, score = phase40_noise.train_adapter, phase40_noise.score_a2

    def logged_train(group, seed, **kw):
        rig.log.append(("train", group, seed))
        return train(group, seed, **kw)

    def logged_score(group, seed, adapter_path, **kw):
        rig.log.append(("a2", group, seed))
        return score(group, seed, adapter_path, **kw)

    def fake_d13(adapter_path, a2_record_path, device, state):
        seed = int(pathlib.Path(adapter_path).stem.split("seed")[1].split("_")[0])
        rig.log.append(("d13", pathlib.Path(adapter_path), pathlib.Path(a2_record_path)))
        return (d13 or (lambda s: _measured()))(seed)

    monkeypatch.setattr(phase40_noise, "train_adapter", logged_train)
    monkeypatch.setattr(phase40_noise, "score_a2", logged_score)
    monkeypatch.setattr(phase40_noise, "d13_scores", fake_d13)
    require, append, write = (
        phase36_ledger.require_launch,
        phase36_ledger.append,
        phase40_noise._write_once,
    )
    rig.launches = 0

    def logged_require(front, **kw):
        rig.launches += 1
        if rig.launches > 1:  # preflight's own call is not logged
            rig.log.append(("require_launch",))
        return require(front, **kw)

    def logged_append(event, **kw):
        rig.log.append((event, kw["run_id"]))
        return append(event, **kw)

    def logged_write(path, blob):
        rig.log.append(("record", pathlib.Path(path).name))
        return write(path, blob)

    monkeypatch.setattr(phase36_ledger, "require_launch", logged_require)
    monkeypatch.setattr(phase36_ledger, "append", logged_append)
    monkeypatch.setattr(phase40_noise, "_write_once", logged_write)
    start = phase25_run.start_heartbeat

    def logged_start(path, state):
        pair = start(path, state)
        rig.threads.append(pair)
        return pair

    monkeypatch.setattr(phase25_run, "start_heartbeat", logged_start)
    return rig


def _run_kw(rig):
    return {**rig.kw, "rehearsal_identity": rig.identity}


def _record(rig, seed):
    return json.loads((rig.root / phase40_prereg.seed_record(seed)).read_text(encoding="utf-8"))


def _threads_stopped(rig):
    assert rig.threads and all(s.is_set() and not t.is_alive() for s, t in rig.threads)


def test_run_order_per_seed(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path))
    assert phase40_noise.run(**_run_kw(rig)) == [1337, 2024]
    expected = []
    for seed in (1337, 2024):
        rid = phase40_prereg.run_id(seed)
        m2 = phase40_noise.arm_paths("m2", seed, rehearsal=True)["adapter"]
        expected += [
            ("require_launch",),
            ("start", rid),
            ("train", "full", seed),
            ("train", "m2", seed),
            ("a2", "full", seed),
            ("a2", "m2", seed),
            ("d13", m2, rig.root / phase40_prereg.a2_record("m2", seed)),
            ("record", pathlib.Path(phase40_prereg.seed_record(seed)).name),
            ("end", rid),
        ]
    assert rig.log == expected
    _threads_stopped(rig)
    identity = json.loads(rig.identity.read_text(encoding="utf-8"))
    assert identity["seeds"] == [1337, 2024] and identity["git_sha"] == "h1"


def test_run_without_d13(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path, seeds=(1337,)))
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", False)
    phase40_noise.run(**_run_kw(rig))
    assert [e for e in rig.log if e[0] == "d13"] == []
    assert _record(rig, 1337)["d13"] is None


def test_whole_seed_ledger_lines(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path))
    phase40_noise.run(**_run_kw(rig))
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [(x["event"], x["run_id"], x["record"]) for x in lines] == [
        (event, phase40_prereg.run_id(seed), record)
        for seed in (1337, 2024)
        for event, record in (("start", None), ("end", phase40_prereg.seed_record(seed)))
    ]
    assert phase40_prereg.seed_outcomes(lines, (1337, 2024)) == {1337: "whole", 2024: "whole"}
    beats = [json.loads(t)["point"] for t in _lines(rig.heartbeat)]
    assert {phase40_prereg.run_id(s) for s in (1337, 2024)} <= set(beats)


def test_stop_before_a_seed_writes_nothing_for_it(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path))
    require = phase36_ledger.require_launch

    def stop_second(front, **kw):
        if rig.launches == 2:  # preflight, seed 1337, then this: before seed 2024
            raise SystemExit("[phase36_ledger] planted D-13 stop")
        return require(front, **kw)

    monkeypatch.setattr(phase36_ledger, "require_launch", stop_second)
    with pytest.raises(SystemExit, match="planted D-13 stop"):
        phase40_noise.run(**_run_kw(rig))
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [(x["event"], x["run_id"]) for x in lines] == [
        ("start", phase40_prereg.run_id(1337)),
        ("end", phase40_prereg.run_id(1337)),
    ]
    assert phase40_noise.partial_outputs(2024, root=rig.root) == []
    assert not (rig.root / phase40_prereg.seed_record(2024)).exists()
    assert phase40_prereg.seed_outcomes(lines, (1337, 2024)) == {1337: "whole", 2024: "not_run"}


@pytest.mark.parametrize("rerun", [False, True])
def test_crash_mid_seed_is_dropped_after_reconcile(monkeypatch, tmp_path, rerun):
    seeds = (1337, 2024, 1338)
    crash = {"on": True}

    def fail(record_path):
        if (
            crash["on"]
            and record_path.name == pathlib.Path(phase40_prereg.a2_record("m2", 2024)).name
        ):
            raise RuntimeError("planted crash in the m2 A2 pass")

    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path, seeds=seeds), fail=fail)
    with pytest.raises(RuntimeError, match="planted crash"):
        phase40_noise.run(**_run_kw(rig))
    _threads_stopped(rig)
    rid = phase40_prereg.run_id(2024)
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert (lines[-1]["event"], lines[-1]["run_id"]) == ("start", rid)
    assert set(phase36_ledger.open_runs(lines)) == {rid}
    (lost,) = phase36_ledger.reconcile(ledger_path=rig.ledger, heartbeat_path=rig.heartbeat)
    assert (lost["event"], lost["run_id"]) == ("lost", rid)
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert phase40_prereg.seed_outcomes(lines, seeds) == {
        1337: "whole",
        2024: "dropped",
        1338: "not_run",
    }
    crash["on"] = False
    crashed = phase40_noise.partial_outputs(2024, root=rig.root)
    assert crashed and not (rig.root / phase40_prereg.a2_record("m2", 2024)).exists()

    # The relaunch runs only the not_run seed; 2024's partial outputs stay in place.
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", rerun)
    rig.log.clear()
    assert phase40_noise.run(**_run_kw(rig)) == [1338]
    assert {e[2] for e in rig.log if e[0] == "train"} == {1338}
    assert phase40_noise.partial_outputs(2024, root=rig.root) == crashed
    if not rerun:
        with pytest.raises(SystemExit, match="DROPPED_SEED_RERUN"):
            _drop(rig, cause_note="planted crash")
        return

    manifest = _drop(rig, cause_note="planted crash in the m2 A2 pass")
    rel_dir = phase40_prereg.dropped_attempt_dir(2024, _lost_utc(rig, 2024))
    assert phase40_noise.partial_outputs(2024, root=rig.root) == []
    assert len(manifest["kept"]) == len(crashed)
    arm = phase40_noise.arm_name("full", 2024, rehearsal=True)
    replants = (
        phase40_noise.arm_paths("full", 2024, rehearsal=True)["adapter"],
        rig.root / phase40_prereg.a2_record("full", 2024),
        phase40_noise.arm_paths("full", 2024, rehearsal=True)["csv"],
        rig.root / "data" / phase40_noise.CSV_DIR / arm / "run.csv",
    )
    for path in replants:
        _plant(path)
        rig.log.clear()
        with pytest.raises(SystemExit, match=re.escape(f"{path} exists")):
            phase40_noise.run(**_run_kw(rig))
        assert rig.log == []
        path.unlink()
        if path.name == "run.csv":
            path.parent.rmdir()
    assert phase40_noise.run(**_run_kw(rig)) == [2024]
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [x["event"] for x in lines if x["run_id"] == rid] == ["start", "lost", "start", "end"]
    assert phase40_prereg.seed_outcomes(lines, seeds) == dict.fromkeys(seeds, "whole")
    assert _record(rig, 2024)["dropped_attempts"] == [_attempt_entry(rig.root, rel_dir)]


def test_run_with_no_arguments_resolves_the_real_defaults(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _real_root_rig(monkeypatch, tmp_path))
    assert phase40_noise.run() == list(phase40_prereg.SEEDS)
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [(x["event"], x["run_id"]) for x in lines] == [
        (event, phase40_prereg.run_id(seed))
        for seed in phase40_prereg.SEEDS
        for event in ("start", "end")
    ]
    beats = {json.loads(t)["point"] for t in _lines(rig.heartbeat)}
    assert {phase40_prereg.run_id(s) for s in phase40_prereg.SEEDS} <= beats
    for seed in phase40_prereg.SEEDS:
        record = _record(rig, seed)
        assert record["provenance"]["run"]["device"] == "mps"
        assert record["rehearsal"] is False
        assert record["rehearsal_disclosure"]["commits"] == []
        assert record["groups"]["full"]["arm"] == phase40_noise.arm_name("full", seed)


def test_seed_record_schema(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path, seeds=(1337,)))
    phase40_noise.run(**_run_kw(rig))
    record = _record(rig, 1337)
    run = record["provenance"]["run"]
    assert set(run) == set(phase40_noise.RUN_PROVENANCE_KEYS)  # sort_keys on disk
    assert run["device"] == "cpu" and run["torch_version"] == torch.__version__
    assert run["git_sha_at_launch"] == run["git_sha_at_end"] == "h1"
    assert run["head_moved_during_run"] is False
    started, finished = (
        phase40_noise.datetime.datetime.fromisoformat(run[k])
        for k in ("started_utc", "finished_utc")
    )
    assert started <= finished
    assert record["provenance"]["module_sha256_at_launch"] == phase40_noise.module_sha256()
    for group in phase40_prereg.GROUPS:
        block = record["groups"][group]
        adapter = phase40_noise.arm_paths(group, 1337, rehearsal=True)["adapter"]
        assert block["adapter_sha256"] == phase40_noise._sha256(adapter)
        assert block["a2"]["record"] == phase40_prereg.a2_record(group, 1337)
        assert block["a2"]["record_sha256"] == phase40_noise._sha256(
            rig.root / phase40_prereg.a2_record(group, 1337)
        )
        assert {"csv", "csv_sha256", "train", "checkpoint"} <= set(block)
    assert record["approval"] == phase40_prereg.approval_block()
    assert record["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
    assert record["dropped_attempts"] == []
    assert record["d13"] == _measured()
    assert (record["seed"], record["run_id"]) == (1337, phase40_prereg.run_id(1337))
    assert (record["front"], record["phase"], record["rehearsal"]) == ("E2", 40, True)
    with pytest.raises(SystemExit, match="write-once"):
        phase40_noise._write_once(rig.root / phase40_prereg.seed_record(1337), record)


def _d13_raise_runtime(seed):
    raise RuntimeError("planted")


def _d13_raise_systemexit(seed):
    raise SystemExit("[phase40_prereg] planted")


@pytest.mark.parametrize(
    ("fake", "kind", "expected"),
    [
        (_d13_raise_runtime, "exception", "RuntimeError: planted"),
        (_d13_raise_systemexit, "exception", "SystemExit: [phase40_prereg] planted"),
        (lambda s: _measured(gate_rank=2), "gate_mismatch", None),
        (lambda s: _measured(committed_ranks=[1, 1, 1]), "malformed_reading", None),
        (lambda s: {"faked": True}, "malformed_reading", "measured"),
        (lambda s: {**_measured(), "anchor_curve": object()}, "malformed_reading", "JSON"),
    ],
    ids=["runtime", "systemexit", "gate_mismatch", "malformed_block", "no_measured", "non_json"],
)
def test_d13_failure_is_not_a_crash_the_seed_stays_whole(
    monkeypatch, tmp_path, capsys, fake, kind, expected
):
    rig = _tmp_rig(monkeypatch, tmp_path)
    rig = _run_fakes(monkeypatch, rig, d13=lambda s: _measured() if s == 1337 else fake(s))
    assert phase40_noise.run(**_run_kw(rig)) == [1337, 2024]
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [x["event"] for x in lines] == ["start", "end", "start", "end"]
    assert phase40_prereg.seed_outcomes(lines, (1337, 2024)) == {1337: "whole", 2024: "whole"}
    assert _record(rig, 1337)["d13"] == _measured()
    d13 = _record(rig, 2024)["d13"]
    assert d13["measured"] is False and d13["failure_kind"] == kind
    if kind == "exception":
        assert d13 == phase40_prereg.d13_not_measured("exception", expected)
    elif expected is None:
        assert d13 == fake(2024)
    else:
        assert expected in d13["reason"]
        assert d13 == phase40_prereg.d13_not_measured("malformed_reading", d13["reason"])
    assert f"D13 NOT_MEASURED 2024 {kind}" in capsys.readouterr().out


def test_d13_keyboard_interrupt_is_still_a_crash(monkeypatch, tmp_path):
    def interrupt(seed):
        if seed == 2024:
            raise KeyboardInterrupt
        return _measured()

    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path), d13=interrupt)
    with pytest.raises(KeyboardInterrupt):
        phase40_noise.run(**_run_kw(rig))
    _threads_stopped(rig)
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert set(phase36_ledger.open_runs(lines)) == {phase40_prereg.run_id(2024)}
    assert not (rig.root / phase40_prereg.seed_record(2024)).exists()


def test_head_moving_mid_run_is_recorded(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path))
    first = rig.root / phase40_prereg.seed_record(1337)
    monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h2" if first.exists() else "h1")
    phase40_noise.run(**_run_kw(rig))
    early, late = _record(rig, 1337)["provenance"]["run"], _record(rig, 2024)["provenance"]["run"]
    assert (early["git_sha_at_end"], early["head_moved_during_run"]) == ("h1", False)
    assert (late["git_sha_at_launch"], late["git_sha_at_end"]) == ("h1", "h2")
    assert late["head_moved_during_run"] is True


def _ledger_uses(source):
    calls, reads = set(), set()
    tree = ast.parse(source)
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            func = node.func
            if isinstance(func.value, ast.Name) and func.value.id == "phase36_ledger":
                calls.add(func.attr)
                called.add(id(func))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "phase36_ledger"
            and id(node) not in called
        ):
            reads.add(node.attr)
    return calls, reads


def test_ast_ledger_calls_are_the_allowed_set():
    allowed = {"run_id", "read_ledger", "open_runs", "require_launch", "append"}
    source = (_SCRIPTS / "phase40_noise.py").read_text(encoding="utf-8")
    calls, reads = _ledger_uses(source)
    assert calls and calls <= allowed
    assert {"require_launch", "append", "read_ledger", "open_runs"} <= calls
    assert reads <= {"HEARTBEAT_PATH", "LEDGER_PATH", "_ROOT"}
    planted = (
        source
        + "\n\ndef planted():\n    phase36_ledger.reconcile()\n    phase36_ledger.rule('E2')\n"
    )
    assert _ledger_uses(planted)[0] - allowed == {"reconcile", "rule"}


# =================================================================================================
# (11) Plan 07 Task 1: build_record and emit, fed REAL committed run_erasure_arm records, end to
# end into the Phase 41 consumer.
# =================================================================================================

# B1: the CPU adapter-off measured with MPS hidden (the committed records carry the MPS value).
_CPU_OFF = 4.573348505014267
# The two committed no-component records (pre_erasure.dialogue_ppl == dialogue_ppl).
_RETRAIN = phase19_erasure.arm_record_path("retrain")
_REPLICATE = phase19_erasure.arm_record_path("replicate")
# (full, m2) A2 fixture per seed: the replicate relabelled to A2_LABEL, the retrain byte for byte.
_A2_KINDS = {
    1337: ("relabel", "retrain"),
    2024: ("retrain", "relabel"),
    1338: ("relabel", "retrain"),
}


def _a2_payload(kind, transform=None):
    """The A2 record a seed gets: bytes (a byte copy) or a dict (written by atomic_write_json).
    ``relabel``: the interfaces' relabel rule, config.arm the ONLY edit."""
    source = _REPLICATE if kind in ("replicate", "relabel") else _RETRAIN
    if kind != "relabel" and transform is None:
        return source.read_bytes()
    record = json.loads(source.read_text(encoding="utf-8"))
    if kind == "relabel":
        record["config"]["arm"] = phase40_prereg.A2_LABEL
    return record if transform is None else transform(record)


def _on_device(device, *, off=None, pre_off=None):
    """config.device and config.preflight.device set as run_erasure_arm writes them; the pre and
    post adapter-off set to ``off`` and the pre alone to ``pre_off`` when given."""

    def transform(record):
        record["config"]["device"] = device
        record["config"]["preflight"]["device"] = device
        if off is not None:
            record["dialogue_ppl"]["adapter_off"] = off
            record["pre_erasure"]["dialogue_ppl"]["adapter_off"] = off
        if pre_off is not None:
            record["pre_erasure"]["dialogue_ppl"]["adapter_off"] = pre_off
        return record

    return transform


def _write(path, payload):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        phase25_run.atomic_write_json(path, payload)
    return path


def _build_rig(monkeypatch, tmp_path, *, real=False):
    """`_repo_rig` (or plan 06's `_real_root_rig` when ``real``) plus tiny tmp comparator adapters
    and adapter_identity wrapped in a recorder (the real tensor-wise comparison on tiny files: no
    gitignored file is read)."""
    if real:
        rig = _real_root_rig(monkeypatch, tmp_path)
        rig.build = {}
    else:
        root = _repo_rig(monkeypatch, tmp_path)
        monkeypatch.setattr(phase40_noise, "git_sha", lambda: "h1")
        ledger = tmp_path / "ledger.jsonl"
        rig = types.SimpleNamespace(root=root, ledger=ledger, build={"ledger_path": ledger})
    comparators = {}
    for key in ("m2_seed1337", "full_seed1337", "full_seed2024", "dialogue_floor_seed1337"):
        comparators[key] = tmp_path / "comparators" / f"{key}.pt"
        comparators[key].parent.mkdir(exist_ok=True)
        torch.save(_artifact(), comparators[key])
    monkeypatch.setattr(phase40_noise, "comparators", lambda: dict(comparators))
    rig.comparators = comparators
    rig.identity_calls = []
    real_identity = phase40_noise.adapter_identity

    def recorder(new_path, committed_path):
        rig.identity_calls.append((pathlib.Path(new_path), pathlib.Path(committed_path)))
        return real_identity(new_path, committed_path)

    monkeypatch.setattr(phase40_noise, "adapter_identity", recorder)
    return rig


def _new_adapter(group, seed):
    return phase40_noise.arm_paths(group, seed, rehearsal=True)["adapter"]


def _seed(rig, seed, *, kinds=None, transform=None, device="mps", d13="measured", attempts=()):
    """One whole seed's outputs under the rig: a tiny adapter per group at its original path, the
    A2 records, and the seed record naming their sha256 (as run() writes it)."""
    root = rig.root
    groups = {}
    for group, kind in zip(phase40_prereg.GROUPS, kinds or _A2_KINDS[seed], strict=True):
        adapter = _new_adapter(group, seed)
        adapter.parent.mkdir(parents=True, exist_ok=True)
        torch.save(_artifact(), adapter)
        rel = phase40_prereg.a2_record(group, seed)
        _write(root / rel, _a2_payload(kind, transform))
        groups[group] = {
            "group": group,
            "seed": seed,
            "adapter": adapter.relative_to(teach_persona._REPO_ROOT).as_posix(),
            "adapter_sha256": phase40_noise._sha256(adapter),
            "train": {"final_train_loss": 0.5, "ppl_adapter_on": 3.0},
            "a2": {
                "group": group,
                "seed": seed,
                "record": rel,
                "record_sha256": phase40_noise._sha256(root / rel),
            },
        }
    blob = {
        "front": "E2",
        "phase": 40,
        "seed": seed,
        "rehearsal": device != "mps",
        "groups": groups,
        "d13": _measured() if d13 == "measured" else d13,
        "approval": phase40_prereg.approval_block(),
        "rehearsal_disclosure": {"this_is_the_rehearsal": True, "seed": seed},
        "dropped_attempts": list(attempts),
        "provenance": {
            "run": {"device": device, "git_sha_at_launch": "h1", "seed": seed},
            "module_sha256_at_launch": phase40_noise.module_sha256(),
        },
    }
    path = root / phase40_prereg.seed_record(seed)
    if path.exists():
        path.unlink()
    _write(path, blob)
    return blob


def _whole(rig, *seeds, **kw):
    for seed in seeds:
        _ledger(rig.ledger, ("start", seed), ("end", seed))
        _seed(rig, seed, **kw)


def _build(rig):
    return phase40_noise.build_record(rig.root, **rig.build)


def _a2(rig, group, seed):
    return json.loads((rig.root / phase40_prereg.a2_record(group, seed)).read_text("utf-8"))


def _rows(record):
    return phase40_prereg.a2_rows(record, *phase40_prereg.a2_scope(record))


def _gap(record):
    return record["dialogue_ppl"]["adapter_on"] - record["dialogue_ppl"]["adapter_off"]


def _consumer_fill(tmp_path, monkeypatch, record):
    """Phase 41's rule on the record: written under a tmp root, one synthetic band-input record
    per e1 teaching seed (ordering "greedy"), phase35_prereg._REPO_ROOT pointed at the tmp root."""
    consumer = tmp_path / "consumer"
    _write(consumer / phase40_prereg.NOISE_FLOOR_RECORD, record)
    teaching = phase35_prereg.e1_teaching_seeds()
    gaps = dict(zip(teaching, (1.25, 1.75), strict=True))
    paths = [phase40_prereg.NOISE_FLOOR_RECORD]
    for i, seed in enumerate(teaching):
        rel = f"results/phase41_band_inputs_{i}.json"
        _write(consumer / rel, {"seed": seed, "ordering": "greedy", "control_gap": gaps[seed]})
        paths.append(rel)
    keys = tuple((seed, "greedy") for seed in teaching)
    with monkeypatch.context() as mp:  # restored on exit: later builds read the real records
        mp.setattr(phase35_prereg, "_REPO_ROOT", consumer)
        bands = phase35_prereg.fill(
            "e1_condition_c_band_inputs",
            band_inputs=dict.fromkeys(keys),
            input_records=tuple(paths),
            derivation={
                "value": keys,
                "derivation": "the Phase 41 contract, fed a real build",
                "kind": "preference",
                "source": " ".join(paths),
            },
        )
    return bands, gaps


def test_build_record_from_real_committed_records(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337, 2024)
    record = _build(rig)
    whole = [1337, 2024]
    rows = {g: {s: _rows(_a2(rig, g, s)) for s in whole} for g in phase40_prereg.GROUPS}
    for seed in whole:
        for group in phase40_prereg.GROUPS:
            reading = record["per_seed"][seed][group]
            assert reading["slots"] == phase40_prereg.slot_rows(rows[group][seed])
            gap = reading["dialogue_gap"]
            assert gap["adapter_off_matches_committed"] is True and gap["rehearsal"] is False
            assert gap["pre"]["adapter_off_matches_committed"] is True
            assert gap["gap"] == _gap(_a2(rig, group, seed))
    assert record["recall_floor"] == phase40_prereg.recall_floor(rows["full"], rows["m2"])
    replicate = json.loads(_REPLICATE.read_text(encoding="utf-8"))
    retrain = json.loads(_RETRAIN.read_text(encoding="utf-8"))
    full_gaps = {s: record["per_seed"][s]["full"]["dialogue_gap"]["gap"] for s in whole}
    expected = phase40_prereg.gap_noise_floor(full_gaps)["value"]
    assert record["gap_noise_floor"] == abs(_gap(replicate) - _gap(retrain)) == expected
    assert record["status"] == "MEASURED" and record["device"] == "mps"
    assert "run" not in record["provenance"]
    assert set(record["provenance"]["seeds"]) == set(whole)
    assert record["rehearsal_disclosure"] == {
        s: {"this_is_the_rehearsal": True, "seed": s} for s in whole
    }
    # Ruling e: how many whole seeds and pairs entered, as the prereg returns them.
    for block in (
        record["recall_floor"]["full"],
        record["recall_floor"]["m2"],
        record["recall_floor"]["published"],
        record["gap_noise_floor_detail"],
    ):
        assert (block["n_seeds"], block["n_pairs"]) == (2, math.comb(2, 2))
    assert record["a2_label"] == {
        "label": phase40_prereg.A2_LABEL,
        "explanation": phase40_prereg.ENTRIES["a2_pass"]["value"],
    }
    v3 = json.loads(phase19_run.NOISE_FLOORS_PATH.read_text(encoding="utf-8"))
    assert record["crn_addendum"]["confirmation_g"] == phase40_prereg.CONFIRMATIONS["g"]
    assert record["crn_addendum"]["v3_sampling_floor"] == v3["nontarget_noise_floor"]["value"]
    assert record["phase41_adapters"] == {
        s: {
            g: {
                "path": _new_adapter(g, s).relative_to(teach_persona._REPO_ROOT).as_posix(),
                "sha256": phase40_noise._sha256(_new_adapter(g, s)),
            }
            for g in phase40_prereg.GROUPS
        }
        for s in whole
    }
    json.dumps(record, sort_keys=True)  # atomic_write_json's options

    # A third whole seed: n_seeds 3, C(3, 2) pairs.
    _whole(rig, 1338)
    third = _build(rig)
    for block in (
        third["recall_floor"]["full"],
        third["recall_floor"]["m2"],
        third["recall_floor"]["published"],
        third["gap_noise_floor_detail"],
    ):
        assert (block["n_seeds"], block["n_pairs"]) == (3, math.comb(3, 2))

    # Natural RED (ruling b): the unmodified replicate (config.arm "replicate") as full@1337, its
    # seed record naming that file's sha256.
    _seed(rig, 1337, kinds=("replicate", "retrain"))
    with pytest.raises(SystemExit, match=r"config\.arm 'replicate'"):
        _build(rig)


def test_consumer_fill_accepts_the_real_record(monkeypatch, tmp_path, capsys):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337, 2024)
    record = _build(rig)
    bands, gaps = _consumer_fill(tmp_path, monkeypatch, record)
    assert set(bands) == {(s, "greedy") for s in gaps}
    for seed, gap in gaps.items():
        assert bands[(seed, "greedy")] == mitigation_gate.dialogue_gap_band(
            control_gap=gap, gap_noise_floor=record["gap_noise_floor"]
        )
    with capsys.disabled():
        print(f"\nCONSUMER gap_noise_floor={record['gap_noise_floor']!r}")
        for key, band in bands.items():
            print(f"CONSUMER band {key} = {band!r}")


def test_consumer_accepts_a_cpu_rehearsal_build(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337, 2024, transform=_on_device("cpu", off=_CPU_OFF), device="cpu")
    record = _build(rig)
    assert record["status"] == "MEASURED" and record["device"] == "cpu"
    for seed in (1337, 2024):
        for group in phase40_prereg.GROUPS:
            gap = record["per_seed"][seed][group]["dialogue_gap"]
            assert gap["adapter_off_matches_committed"] is False and gap["rehearsal"] is True
            assert gap["gap"] == _a2(rig, group, seed)["dialogue_ppl"]["adapter_on"] - _CPU_OFF
    bands, gaps = _consumer_fill(tmp_path, monkeypatch, record)
    for seed, gap in gaps.items():
        assert bands[(seed, "greedy")] == mitigation_gate.dialogue_gap_band(
            control_gap=gap, gap_noise_floor=record["gap_noise_floor"]
        )
    # Under the frozen R-1 mps-equality, the CPU-valued readings relabelled mps refuse ...
    assert phase40_prereg.ADAPTER_OFF_RULE == "mps-equality"
    mps_cpu = {"transform": _on_device("mps", off=_CPU_OFF), "device": "mps"}
    for seed in (1337, 2024):
        _seed(rig, seed, **mps_cpu)
    with pytest.raises(SystemExit, match="R-1 mps-equality"):
        _build(rig)
    # ... and so does an mps reading whose PRE adapter-off alone is the CPU value (IN-02 a).
    for seed in (1337, 2024):
        _seed(rig, seed, transform=_on_device("mps", pre_off=_CPU_OFF))
    with pytest.raises(SystemExit, match="R-1 mps-equality"):
        _build(rig)
    # record-only: the mps-relabelled CPU readings build, the match flag False.
    monkeypatch.setattr(phase40_prereg, "ADAPTER_OFF_RULE", "record-only")
    for seed in (1337, 2024):
        _seed(rig, seed, **mps_cpu)
    relabelled = _build(rig)
    assert relabelled["status"] == "MEASURED"
    assert all(
        relabelled["per_seed"][s][g]["dialogue_gap"]["adapter_off_matches_committed"] is False
        for s in (1337, 2024)
        for g in phase40_prereg.GROUPS
    )
    monkeypatch.undo()
    rig = _build_rig(monkeypatch, tmp_path / "wr03")
    # WR-03: a seed record "mps" over A2 records measured on cpu: build_record's own refusal.
    _whole(rig, 1337, 2024, transform=_on_device("cpu", off=_CPU_OFF), device="mps")
    with pytest.raises(SystemExit, match="WR-03"):
        _build(rig)
    # One device across the whole seeds.
    _seed(rig, 1337, transform=_on_device("cpu", off=_CPU_OFF), device="cpu")
    _seed(rig, 2024)
    with pytest.raises(SystemExit, match="one device"):
        _build(rig)


def _kept_attempt(rig, seed, *, lost_utc):
    """A dropped attempt of ``seed``: a kept tiny full adapter (its ``from`` the seed's full
    adapter path) and a kept full A2 record, with the manifest those make."""
    rel_dir = phase40_prereg.dropped_attempt_dir(seed, lost_utc)
    kept = []
    for rel, payload in (
        (_new_adapter("full", seed).relative_to(teach_persona._REPO_ROOT).as_posix(), None),
        (phase40_prereg.a2_record("full", seed), _RETRAIN.read_bytes()),
    ):
        path = rig.root / rel_dir / rel
        if payload is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(_artifact(), path)
        else:
            _write(path, payload)
        kept.append(
            {"from": rel, "path": f"{rel_dir}/{rel}", "sha256": phase40_noise._sha256(path)}
        )
    manifest = {
        "seed": seed,
        "run_id": phase40_prereg.run_id(seed),
        "lost_utc": lost_utc,
        "cause_note": "a planted crash",
        "approved": "approved",
        "head_at_dropped_attempt": "h1",
        "relaunch_git_sha": "h1",
        "head_change_declared": None,
        "kept": kept,
    }
    assert phase40_prereg.dropped_manifest_failures(manifest, seed=seed, lost_utc=lost_utc) == []
    _write(rig.root / rel_dir / phase40_prereg.DROPPED_MANIFEST, manifest)
    return rel_dir


def _rerun_rig(monkeypatch, tmp_path):
    """1337 whole; 2024 start + lost (utc U), then its whole re-run listing that attempt."""
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337)
    _ledger(rig.ledger, ("start", 2024), ("lost", 2024))
    rig.lost = _lost_utc(rig, 2024)
    rig.rel_dir = _kept_attempt(rig, 2024, lost_utc=rig.lost)
    _ledger(rig.ledger, ("start", 2024), ("end", 2024))
    rig.entry = _attempt_entry(rig.root, rig.rel_dir)
    _seed(rig, 2024, attempts=[rig.entry])
    return rig


def test_build_record_lists_dropped_attempts_and_attempt_identity(monkeypatch, tmp_path):
    rig = _rerun_rig(monkeypatch, tmp_path)
    record = _build(rig)
    new_full = _new_adapter("full", 2024)
    kept_full = rig.root / rig.entry["kept"][0]["path"]
    assert rig.entry["kept"][0]["from"] == _record(rig, 2024)["groups"]["full"]["adapter"]
    expected_identity = phase40_noise.adapter_identity(new_full, kept_full)
    assert record["seeds"]["dropped_attempts"] == {
        2024: [
            {
                **rig.entry,
                "kept_verified": True,
                "adapter_identity": {
                    "full": expected_identity,
                    "m2": "not produced by the dropped attempt",
                },
            }
        ]
    }
    assert (new_full, kept_full) in rig.identity_calls
    assert record["seeds"]["dropped_seed_outputs"] == {}

    # The seed record lists no attempt while the ledger holds the lost line.
    _seed(rig, 2024, attempts=[])
    with pytest.raises(SystemExit, match=r"R-3 b \(c\): every lost attempt of a whole seed"):
        _build(rig)
    # An entry whose lost_utc the ledger lacks.
    _seed(rig, 2024, attempts=[rig.entry, {**rig.entry, "lost_utc": "2000-01-01T00:00:00+00:00"}])
    with pytest.raises(SystemExit, match="a lost attempt the ledger lacks"):
        _build(rig)
    # A kept file whose bytes changed.
    _seed(rig, 2024, attempts=[rig.entry])
    _build(rig)
    with kept_full.open("ab") as f:
        f.write(b"\0")
    with pytest.raises(SystemExit, match="kept file .* sha256 changed"):
        _build(rig)

    # No lost line and every dropped_attempts []: {}.
    clean = _build_rig(monkeypatch, tmp_path / "clean")
    _whole(clean, 1337, 2024)
    assert _build(clean)["seeds"]["dropped_attempts"] == {}


def test_build_record_lists_dropped_attempts_of_a_seed_left_dropped(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337)
    _ledger(rig.ledger, ("start", 2024), ("lost", 2024))
    _plant(_new_adapter("full", 2024), b"crashed full adapter")
    _plant(rig.root / phase40_prereg.a2_record("full", 2024), b"crashed full A2 record")
    record = _build(rig)
    in_place = phase40_noise.partial_outputs(2024, root=rig.root)
    assert len(in_place) == 2
    assert record["seeds"]["dropped_seed_outputs"] == {
        2024: {
            "manifests": [],
            "in_place": [{"from": rel, "sha256": phase40_noise._sha256(p)} for rel, p in in_place],
        }
    }
    manifest = _drop(rig)
    rel_dir = phase40_prereg.dropped_attempt_dir(2024, _lost_utc(rig, 2024))
    rel = f"{rel_dir}/{phase40_prereg.DROPPED_MANIFEST}"
    after = _build(rig)
    assert after["seeds"]["dropped_seed_outputs"] == {
        2024: {
            "manifests": [
                {
                    **manifest,
                    "manifest": rel,
                    "manifest_sha256": phase40_noise._sha256(rig.root / rel),
                    "kept_verified": True,
                }
            ],
            "in_place": [],
        }
    }

    # The re-run case: one byte appended to the kept attempt's manifest refuses.
    rerun = _rerun_rig(monkeypatch, tmp_path / "rerun")
    _build(rerun)
    with (rerun.root / rerun.entry["manifest"]).open("ab") as f:
        f.write(b" ")
    with pytest.raises(SystemExit, match="manifest_sha256"):
        _build(rerun)


def test_build_record_without_seed_1337(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _ledger(rig.ledger, ("start", 1337), ("lost", 1337))
    _whole(rig, 2024, 1338)
    record = _build(rig)
    assert record["status"] == "MEASURED"
    gone = "not whole: seed 1337 is dropped"
    assert record["identity"]["m2_seed1337"] == record["identity"]["full_seed1337"] == gone
    assert record["d07"]["m2_seed1337"] == record["d08b"] == gone
    observed = {k: v["observed"] for k, v in record["predictions"].items()}
    assert observed["tensor_identity"]["m2_seed1337"] == gone
    assert observed["tensor_identity"]["full_seed1337"] == gone
    assert observed["gap_pair"] == observed["m2_counts"] == observed["full_counts"] == gone
    assert record["identity"]["full_seed2024"]["tensors_identical"] is True
    assert observed["tensor_identity"]["full_seed2024"] is True
    assert "persona_vs_dialogue_floor_1337" in record["d08"]
    assert set(record["phase41_adapters"]) == {2024}

    rig = _build_rig(monkeypatch, tmp_path / "no2024")
    _ledger(rig.ledger, ("start", 2024), ("lost", 2024))
    _whole(rig, 1337, 1338)
    record = _build(rig)
    gone = "not whole: seed 2024 is dropped"
    assert record["identity"]["full_seed2024"] == gone
    assert record["predictions"]["gap_pair"]["observed"] == gone
    assert isinstance(record["d08b"], dict) and set(record["phase41_adapters"]) == {1337}

    rig = _build_rig(monkeypatch, tmp_path / "not_run")
    _whole(rig, 2024, 1338)
    record = _build(rig)
    gone = "not whole: seed 1337 is not_run"
    assert record["identity"]["m2_seed1337"] == record["d07"]["m2_seed1337"] == gone
    assert record["seeds"]["not_run"] == [1337, 2025, 1339]


def test_insufficient_seeds_has_no_gap_key(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337)
    _ledger(rig.ledger, ("start", 2024), ("lost", 2024))
    record = _build(rig)
    assert record["status"] == "INSUFFICIENT_SEEDS"
    for key in ("gap_noise_floor", "recall_floor", "gap_noise_floor_detail"):
        assert key not in record
    assert "INSUFFICIENT_SEEDS" in record["stop"] and "stops for Rafael" in record["stop"]
    assert record["seeds"]["dropped"] == [2024] and record["seeds"]["whole"] == [1337]
    with pytest.raises(SystemExit, match="gap_noise_floor"):
        _consumer_fill(tmp_path, monkeypatch, record)


def test_emit_records_the_d13_reading(monkeypatch, tmp_path, capsys):
    rig = _build_rig(monkeypatch, tmp_path)
    assert phase40_prereg.D13_INCLUDED is True
    failed = phase40_prereg.d13_not_measured("exception", "RuntimeError: planted")
    _whole(rig, 1337)
    _whole(rig, 2024, d13=failed)
    record = phase40_noise.emit(root=rig.root, ledger_path=rig.ledger)
    blocks = {1337: _measured(), 2024: failed}
    assert record["d13"] == {"reading": phase40_prereg.d13_reading(blocks), "blocks": blocks}
    assert record["seeds"]["whole"] == [1337, 2024]
    assert record["recall_floor"]["full"]["seeds"] == [1337, 2024]
    assert record["gap_noise_floor_detail"]["seeds"] == [1337, 2024]
    out = rig.root / phase40_prereg.NOISE_FLOOR_RECORD
    assert json.loads(out.read_text(encoding="utf-8"))["status"] == "MEASURED"
    assert "EMIT MEASURED whole=1337,2024" in capsys.readouterr().out

    # D-13 not approved: the seed records carry null and the record's d13 is None.
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", False)
    for seed in (1337, 2024):
        _seed(rig, seed, d13=None)
    assert _build(rig)["d13"] is None
    # A null d13 while D-13 is approved refuses with d13_reading's message.
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", True)
    with pytest.raises(SystemExit, match="neither d13_block nor d13_not_measured"):
        _build(rig)


def test_emit_refuses_an_attempt_after_a_whole_seed(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337)
    _ledger(rig.ledger, ("start", 1337), ("lost", 1337))
    with pytest.raises(SystemExit, match="a whole seed has a later attempt"):
        _build(rig)
    with pytest.raises(SystemExit, match="a whole seed has a later attempt"):
        phase40_noise.emit(root=rig.root, ledger_path=rig.ledger)
    assert not (rig.root / phase40_prereg.NOISE_FLOOR_RECORD).exists()


def test_a2_sha_mismatch_refuses(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337, 2024)
    _build(rig)
    with (rig.root / phase40_prereg.a2_record("m2", 2024)).open("ab") as f:
        f.write(b" ")
    with pytest.raises(SystemExit, match="sha256"):
        _build(rig)
    # The adapter re-hashed at its original path too (Phase 41 reuses it by sha256 there).
    _seed(rig, 2024)
    _build(rig)
    with _new_adapter("m2", 2024).open("ab") as f:
        f.write(b"\0")
    with pytest.raises(SystemExit, match="adapter_sha256"):
        _build(rig)


def test_emit_publishes_floor_beside_v3_and_margin_unamended(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337, 2024)
    record = _build(rig)
    assert record["recall_floor"]["beside"] == {
        "sampling_floor": phase19_floor.NONTARGET_NOISE_FLOOR,
        "margin_at_gate": phase35_prereg.e1_condition_b_margin(),
        "margin_amended": False,
    }
    first = _git(
        "log", "--diff-filter=A", "--format=%H", "--", "scripts/phase40_prereg.py"
    ).split()[-1]
    unchanged = subprocess.run(
        (
            "git",
            "diff",
            "--quiet",
            f"{first}^",
            "HEAD",
            "--",
            "results/phase19_noise_floors.json",
            "scripts/phase19_floor.py",
        ),
        cwd=_ROOT,
    )
    assert unchanged.returncode == 0


def _identity_stub(monkeypatch, rig, identical):
    def stub(new_path, committed_path):
        rig.identity_calls.append((pathlib.Path(new_path), pathlib.Path(committed_path)))
        return {"tensors_identical": identical, "criterion": False}

    monkeypatch.setattr(phase40_noise, "adapter_identity", stub)


def test_emit_d08_block_and_d07_readings(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337, 2024)
    p18 = json.loads(phase19_erasure.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    retrain = json.loads(_RETRAIN.read_text(encoding="utf-8"))
    full, m2 = _a2(rig, "full", 1337), _a2(rig, "m2", 1337)
    outcomes = set()
    for identical in (True, False):
        rig.identity_calls.clear()
        _identity_stub(monkeypatch, rig, identical)
        record = _build(rig)
        d07 = record["d07"]["m2_seed1337"]
        expected = phase40_prereg.d07_reading(
            identical, _rows(m2), phase40_prereg.a2_rows(retrain, *phase40_prereg.a2_scope(m2))
        )
        assert {k: d07[k] for k in expected} == expected
        assert (d07["label"] is None) is identical
        assert d07["draw_identity"] == phase37_prereg.draw_identity(m2["draws"], retrain["draws"])
        family, tiers = phase40_prereg.a2_scope(full)
        d08b = phase40_prereg.d08b_reading(
            identical, phase40_prereg.a2_rows(p18, family, tiers), _rows(full)
        )
        assert {k: record["d08b"][k] for k in d08b} == d08b
        assert record["d08b"]["draw_identity"] == phase37_prereg.draw_identity(
            full["draws"], [d for d in p18["draws"] if d["family"] == family]
        )
        outcomes.add(record["d08b"]["outcome"])
        assert record["d08"] == {
            "statement": phase40_prereg.ENTRIES["d08_correction"]["value"],
            "persona_vs_dialogue_floor_1337": {"tensors_identical": identical, "criterion": False},
        }
        comp = rig.comparators
        assert (comp["full_seed1337"], comp["dialogue_floor_seed1337"]) in rig.identity_calls
        assert (_new_adapter("m2", 1337), comp["m2_seed1337"]) in rig.identity_calls
        assert (_new_adapter("full", 2024), comp["full_seed2024"]) in rig.identity_calls
        assert record["predictions"]["tensor_identity"]["observed"]["m2_seed1337"] is identical
    assert "NOT_SEPARABLE" in outcomes and outcomes <= set(phase40_prereg.D08B_OUTCOMES)
    assert len(outcomes) == 2


def test_emit_is_write_once_and_refuses_a_dirty_tree(monkeypatch, tmp_path, capsys):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337, 2024)
    out = rig.root / phase40_prereg.NOISE_FLOOR_RECORD
    phase40_noise.emit(root=rig.root, ledger_path=rig.ledger)
    before = out.read_bytes()
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        phase40_noise.emit(root=rig.root, ledger_path=rig.ledger)
    assert out.read_bytes() == before
    monkeypatch.undo()

    real = _build_rig(monkeypatch, tmp_path / "real", real=True)
    _whole(real, 1337)
    _ledger(real.ledger, ("start", 2024), ("lost", 2024))
    real_out = real.root / phase40_prereg.NOISE_FLOOR_RECORD
    planted = []

    def dirty(**kw):
        planted.append(kw)
        raise SystemExit("planted: dirty tree")

    monkeypatch.setattr(phase40_noise, "refuse_if_dirty", dirty)
    with pytest.raises(SystemExit, match="dirty"):
        phase40_noise.emit()
    assert not real_out.exists() and len(planted) == 1
    monkeypatch.setattr(phase40_noise, "refuse_if_dirty", lambda **kw: real.dirty.append(kw))
    record = phase40_noise.emit()
    assert real_out.exists() and record["status"] == "INSUFFICIENT_SEEDS"
    outcomes = phase40_prereg.seed_outcomes(_ledger_lines(real.ledger), phase40_prereg.SEEDS)
    assert len(real.dirty) == 1
    assert real.dirty[0]["pathspec"] == phase40_noise._launch_pathspec(outcomes)
    assert planted[0]["pathspec"] == real.dirty[0]["pathspec"]


def _ledger_lines(path):
    return [json.loads(t) for t in _lines(path)]


# =================================================================================================
# (12) Plan 07 Task 2: render_report, report, main, the full fake chain and the censuses.
# =================================================================================================

_HEADINGS = (
    "# Phase 40 — E2 training-seed noise floor",
    "## Status",
    "## Approval and cost (D-11, D-13, D-14)",
    "## Seeds (D-15)",
    "## A2 recall per seed with its denominator (NOISE-01)",
    "## Training-seed floor beside v3.0's sampling floor (NOISE-02, D-01..D-05)",
    "## Every pair (D-02, D-04)",
    "## Per-slot spread (D-04)",
    "## gap_noise_floor (D-09, D-10)",
    "## Full x M2 re-reading (D-12, descriptive)",
    "## Determinism check (D-07, descriptive)",
    "## persona_adapter.pt correction and the Phase 18 residual (D-08, D-08b)",
    "## Target rank across the M2 seeds (D-13, descriptive)",
    "## Predictions recorded before the run",
    "## Provenance",
)
_DISCLOSURE = {
    "statement": "The CPU rehearsal ran seeds [1337, 2024] on this prereg before the MPS run.",
    "rehearsal_git_sha": "r1",
    "launch_git_sha": "l1",
    "changed": {"scripts/phase40_noise.py": True, "scripts/phase40_prereg.py": False},
    "commits": [{"sha": "c1", "reason": "fix | a pipe", "modules": ["scripts/phase40_noise.py"]}],
}


def _sections(report):
    """{heading: the text up to the next heading} (the title included)."""
    out, heading = {}, None
    for line in report.splitlines():
        if line.startswith("#"):
            heading = line
            out[heading] = []
        else:
            out[heading].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def _cells(line):
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)[1:-1]]


def _tables(text):
    """Every GFM table in ``text`` as [header, *rows] of cells; each proved well-formed."""
    tables, block = [], []
    for line in [*text.splitlines(), ""]:
        if line.startswith("|"):
            block.append(line)
            continue
        if block:
            header = _cells(block[0])
            assert block[1] == "|" + "---|" * len(header), block[:2]
            rows = [_cells(row) for row in block[2:]]
            assert all(len(row) == len(header) for row in rows), block
            tables.append([header, *rows])
            block = []
    return tables


def _report_record(monkeypatch, tmp_path):
    """A MEASURED record from the real build: 1337 whole, 2024 re-run after a dropped attempt (its
    D-13 not measured), 1338 left dropped with a partial output in place; 1337's disclosure the
    launch shape, 2024's the rehearsal's. Round-tripped through JSON as the file holds it."""
    rig = _rerun_rig(monkeypatch, tmp_path)
    failed = phase40_prereg.d13_not_measured("exception", "RuntimeError: planted")
    _seed(rig, 2024, attempts=[rig.entry], d13=failed)
    _ledger(rig.ledger, ("start", 1338), ("lost", 1338))
    _plant(_new_adapter("full", 1338), b"crashed full adapter")
    record = _build(rig)
    record["rehearsal_disclosure"][1337] = dict(_DISCLOSURE)
    return json.loads(json.dumps(record, sort_keys=True)), rig


def test_render_report_measured(monkeypatch, tmp_path):
    record, rig = _report_record(monkeypatch, tmp_path)
    report = phase40_noise.render_report(record)
    headings = [line for line in report.splitlines() if line.startswith("#")]
    assert headings == list(_HEADINGS)
    sections = _sections(report)
    for text in sections.values():
        _tables(text)
    assert report == phase40_noise.render_report(record)  # pure

    status = sections["## Status"]
    assert "MEASURED" in status and "1338" in status

    approval, a = sections["## Approval and cost (D-11, D-13, D-14)"], record["approval"]
    for key in ("ruling", "r3_conditions", "record_total_ruling"):
        assert f"> {a[key]}" in approval
    for key in (
        "committed_total_hours",
        "e2_total_hours",
        "e2_e5_e6_total_hours",
        "e2_e5_e6_total_hours_e6_actual_gate",
    ):
        assert [key, repr(a[key])] in _tables(approval)[0]

    seeds = sections["## Seeds (D-15)"]
    attempt = record["seeds"]["dropped_attempts"]["2024"][0]
    for text in (
        attempt["lost_utc"],
        attempt["cause_note"],
        f"Rafael's approved: {attempt['approved']}",
        f"`{attempt['head_at_dropped_attempt']}`",
        f"`{record['provenance']['seeds']['2024']['git_sha_at_launch']}`",
        f"`{attempt['manifest_sha256']}`",
        "not produced by the dropped attempt",
        "tensors_identical True",
    ):
        assert text in seeds, text
    kept = [row for table in _tables(seeds) for row in table[1:]]
    for item in attempt["kept"]:
        assert [item["from"], item["path"], item["sha256"]] in kept
    (in_place,) = record["seeds"]["dropped_seed_outputs"]["1338"]["in_place"]
    assert "Seed 1338 is left dropped" in seeds
    assert [in_place["from"], in_place["sha256"]] in kept

    # NOISE-01: the per-seed table parsed back equals the record cell by cell.
    a2 = sections["## A2 recall per seed with its denominator (NOISE-01)"]
    (table,) = _tables(a2)
    tiers = sorted(record["per_seed"]["1337"]["full"]["slots"]["pet_name"]["per_tier"])
    assert table[0] == ["seed", "group", "slot", "fact", "recall", "rate", *tiers]
    expected = []
    for seed in ("1337", "2024"):
        for group in phase40_prereg.GROUPS:
            slots = record["per_seed"][seed][group]["slots"]
            for slot in (*phase19_erasure.GATED_NONTARGET_SLOTS, phase19_erasure.TARGET_SLOT):
                row = slots[slot]
                expected.append(
                    [
                        seed,
                        group,
                        slot,
                        row["fact_id"],
                        f"{row['n_answerable']}/{row['n_questions']}",
                        repr(row["rate"]),
                        *(
                            f"{row['per_tier'][t]['n_answerable']}/{row['per_tier'][t]['n_questions']}"
                            for t in tiers
                        ),
                    ]
                )
    assert table[1:] == expected
    assert all(r[4].endswith("/27") for r in table[1:])
    assert {r[6].split("/")[1] for r in table[1:]} | {r[7].split("/")[1] for r in table[1:]} == {
        "13",
        "14",
    }
    # Ruling b: the explanation once, in this section, after the config.arm sentence.
    explanation = record["a2_label"]["explanation"]
    assert report.count(explanation) == 1 and a2.count(explanation) == 1
    sentence = (
        "Every A2 record of both groups carries config.arm 'retrain' because it names the "
        "pinned A2 pass, not a group"
    )
    assert a2.index(sentence) < a2.index(explanation)

    floor = sections["## Training-seed floor beside v3.0's sampling floor (NOISE-02, D-01..D-05)"]
    rf = record["recall_floor"]
    published = rf["published"]
    assert f"Published floor: {published['value']!r} (group {published['group']}" in floor
    assert repr(phase19_floor.NONTARGET_NOISE_FLOOR) == "0.14814814814814814"
    assert "0.14814814814814814" in floor
    assert f"{rf['beside']['margin_at_gate']!r}, not amended" in floor
    for block in (rf["full"], rf["m2"], published):
        assert f"{block['n_seeds']} whole seeds, {block['n_pairs']} pairs entered" in floor
    # Addendum g, section-scoped.
    assert floor.count(phase40_prereg.CONFIRMATIONS["g"]) == 1
    v3 = json.loads(phase19_run.NOISE_FLOORS_PATH.read_text(encoding="utf-8"))
    assert repr(v3["nontarget_noise_floor"]["value"]) in floor
    assert "not an upper bound on training plus sampling and may come out below" in floor
    below = "as the addendum allows"
    assert (below in floor) is record["crn_addendum"]["published_below_v3_sampling_floor"]
    flipped = json.loads(json.dumps(record))
    flipped["crn_addendum"]["published_below_v3_sampling_floor"] = True
    assert below in phase40_noise.render_report(flipped)

    pairs = sections["## Every pair (D-02, D-04)"]
    assert [["group", "seeds", "d", "deltas"]] == [t[0] for t in _tables(pairs)]
    spread = sections["## Per-slot spread (D-04)"]
    assert _tables(spread)[0][1][1] == phase19_erasure.GATED_NONTARGET_SLOTS[0]

    gap = sections["## gap_noise_floor (D-09, D-10)"]
    detail = record["gap_noise_floor_detail"]
    assert f"gap_noise_floor = {record['gap_noise_floor']!r}" in gap
    assert f"{detail['n_seeds']} whole seeds, {detail['n_pairs']} pairs entered" in gap
    readings = [t for t in _tables(gap) if t[0][0] == "seed" and "pre adapter_off" in t[0]]
    (readings,) = readings
    header = readings[0]
    for row in readings[1:]:
        reading = record["per_seed"][row[0]][row[1]]["dialogue_gap"]
        cell = dict(zip(header, row, strict=True))
        assert cell["device"] == reading["device"]
        assert cell["adapter_off"] == repr(reading["adapter_off"])
        assert cell["committed adapter_off"] == repr(reading["committed_adapter_off"])
        assert cell["matches"] == str(reading["adapter_off_matches_committed"])
        assert cell["pre adapter_on"] == repr(reading["pre"]["adapter_on"])
        assert cell["pre adapter_off"] == repr(reading["pre"]["adapter_off"])
        assert cell["pre matches"] == str(reading["pre"]["adapter_off_matches_committed"])
        assert cell["rehearsal"] == str(reading["rehearsal"])
        assert cell["pre_post_equal"] == str(reading["pre_post_equal"])
        assert cell["gap"] == repr(reading["gap"])
    assert len(readings) == 1 + 2 * 2

    for heading in (
        "## Full x M2 re-reading (D-12, descriptive)",
        "## Determinism check (D-07, descriptive)",
        "## Target rank across the M2 seeds (D-13, descriptive)",
    ):
        assert "descriptive, never a verdict" in sections[heading], heading
    d13 = sections["## Target rank across the M2 seeds (D-13, descriptive)"]
    assert "Measured seeds: 1337." in d13
    assert "seed 2024: not measured (exception): RuntimeError: planted" in d13
    assert "the seed is kept: ruling c" in d13

    predictions = sections["## Predictions recorded before the run"]
    keys = [row[0] for row in _tables(predictions)[0][1:]]
    assert keys == list(phase40_prereg.ENTRIES["predictions"]["value"])

    provenance = sections["## Provenance"]
    assert "Seed 2024: this is the rehearsal." in provenance
    for text in ("`r1`", "`l1`", "scripts/phase40_noise.py", "`c1` fix | a pipe"):
        assert text in provenance, text


def test_render_report_insufficient_seeds(monkeypatch, tmp_path):
    rig = _build_rig(monkeypatch, tmp_path)
    _whole(rig, 1337)
    _ledger(rig.ledger, ("start", 2024), ("lost", 2024))
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", False)
    _seed(rig, 1337, d13=None)
    record = json.loads(json.dumps(_build(rig), sort_keys=True))
    report = phase40_noise.render_report(record)
    assert [line for line in report.splitlines() if line.startswith("#")] == list(_HEADINGS)
    sections = _sections(report)
    for text in sections.values():
        _tables(text)
    assert "INSUFFICIENT_SEEDS" in sections["## Status"]
    assert record["stop"] in sections["## Status"] and "stops for Rafael" in record["stop"]
    assert "Published floor" not in report and "gap_noise_floor =" not in report
    assert "not published" in sections["## gap_noise_floor (D-09, D-10)"]
    assert ["2024", "dropped"] in _tables(sections["## Seeds (D-15)"])[0]
    assert (
        "D-13 was not approved"
        in sections["## Target rank across the M2 seeds (D-13, descriptive)"]
    )


def test_report_writes_once_and_the_real_root_needs_a_committed_record(
    monkeypatch, tmp_path, capsys
):
    rig = _build_rig(monkeypatch, tmp_path)
    with pytest.raises(SystemExit, match="emit the record first"):
        phase40_noise.report(root=rig.root)
    _whole(rig, 1337, 2024)
    phase40_noise.emit(root=rig.root, ledger_path=rig.ledger)
    record = json.loads((rig.root / phase40_prereg.NOISE_FLOOR_RECORD).read_text("utf-8"))
    out = rig.root / phase40_prereg.REPORT_RECORD
    assert phase40_noise.report(root=rig.root) == out
    assert f"REPORT {out}" in capsys.readouterr().out
    assert out.read_text(encoding="utf-8") == phase40_noise.render_report(record)
    before = out.read_bytes()
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        phase40_noise.report(root=rig.root)
    assert out.read_bytes() == before
    monkeypatch.undo()

    real = _build_rig(monkeypatch, tmp_path / "real", real=True)
    _whole(real, 1337, 2024)
    phase40_noise.emit()
    monkeypatch.setattr(phase40_noise, "_tracked_and_clean", lambda rel: False)
    with pytest.raises(SystemExit, match="committed and unmodified"):
        phase40_noise.report()
    assert not (real.root / phase40_prereg.REPORT_RECORD).exists()
    monkeypatch.setattr(phase40_noise, "_tracked_and_clean", lambda rel: True)
    assert phase40_noise.report() == real.root / phase40_prereg.REPORT_RECORD


def test_report_tracked_and_clean_reads_git():
    assert phase40_noise._tracked_and_clean("scripts/phase40_prereg.py") is True
    assert phase40_noise._tracked_and_clean("results/phase40_never_written.json") is False


def test_the_full_fake_chain_through_the_commands(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    rig = _real_root_rig(monkeypatch, tmp_path, identity=True)
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", True)
    root = rig.root
    trained = []

    def fake_train(group, seed, *, root, rehearsal=False):
        adapter = phase40_noise.arm_paths(group, seed, rehearsal=rehearsal)["adapter"]
        adapter.parent.mkdir(parents=True, exist_ok=True)
        torch.save(_artifact(), adapter)
        trained.append((group, seed))
        return {
            "group": group,
            "seed": seed,
            "arm": phase40_noise.arm_name(group, seed, rehearsal=rehearsal),
            "adapter": adapter.relative_to(teach_persona._REPO_ROOT).as_posix(),
            "adapter_sha256": phase40_noise._sha256(adapter),
            "train": {"final_train_loss": 0.5},
        }

    def fake_score(group, seed, adapter_path, *, root, device):
        index = phase40_prereg.SEEDS.index(seed)
        kinds = ("relabel", "retrain") if index % 2 == 0 else ("retrain", "relabel")
        rel = phase40_prereg.a2_record(group, seed)
        _write(root / rel, _a2_payload(kinds[phase40_prereg.GROUPS.index(group)]))
        return {
            "group": group,
            "seed": seed,
            "record": rel,
            "record_sha256": phase40_noise._sha256(root / rel),
        }

    monkeypatch.setattr(phase40_noise, "train_adapter", fake_train)
    monkeypatch.setattr(phase40_noise, "score_a2", fake_score)
    monkeypatch.setattr(phase40_noise, "d13_scores", lambda *a, **k: _measured())
    comparators = {}
    for key in ("m2_seed1337", "full_seed1337", "full_seed2024", "dialogue_floor_seed1337"):
        comparators[key] = tmp_path / f"{key}.pt"
        torch.save(_artifact(), comparators[key])
    monkeypatch.setattr(phase40_noise, "comparators", lambda: dict(comparators))
    monkeypatch.setattr(phase40_noise, "_tracked_and_clean", lambda rel: True)

    for command in ("preflight", "run", "emit", "report"):
        assert phase40_noise.main([command]) == 0, command
    assert pathlib.Path.cwd() == phase40_noise._REPO
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [(x["event"], x["run_id"]) for x in lines] == [
        (event, phase40_prereg.run_id(seed))
        for seed in phase40_prereg.SEEDS
        for event in ("start", "end")
    ]
    out = root / phase40_prereg.NOISE_FLOOR_RECORD
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["status"] == "MEASURED"
    assert record["seeds"]["whole"] == list(phase40_prereg.SEEDS)
    assert len(trained) == 2 * len(phase40_prereg.SEEDS)
    report = (root / phase40_prereg.REPORT_RECORD).read_text(encoding="utf-8")
    assert report == phase40_noise.render_report(record)
    # preflight, run and emit each made their one dirty check.
    assert len(rig.dirty) == 3


@pytest.mark.parametrize("command", ["preflight", "run", "emit", "report"])
def test_main_dispatches_with_no_arguments_from_the_repo(tmp_path, monkeypatch, command):
    real = getattr(phase40_noise, command)
    seen = []

    def recorder(*args, **kwargs):
        inspect.signature(real).bind(*args, **kwargs)
        seen.append((args, kwargs, pathlib.Path.cwd()))

    monkeypatch.setattr(phase40_noise, command, recorder)
    monkeypatch.chdir(tmp_path)
    assert phase40_noise.main([command]) == 0
    assert seen == [((), {}, phase40_noise._REPO)]


@pytest.mark.parametrize("argv", [[], ["bogus"], ["run", "x"]])
def test_main_refuses_anything_else(argv):
    with pytest.raises(SystemExit) as raised:
        phase40_noise.main(argv)
    assert raised.value.code == phase40_noise.__doc__


def test_main_the_cli_exits_non_zero_on_a_bogus_command():
    done = subprocess.run(
        [sys.executable, "scripts/phase40_noise.py", "bogus"], cwd=_ROOT, capture_output=True
    )
    assert done.returncode != 0


def test_census_helpers_called_directly(monkeypatch, tmp_path):
    """Every helper the paths above reach only indirectly, called by name."""
    assert phase40_noise._prereg() is phase40_prereg
    assert phase40_noise._prove(True, "x") is None
    with pytest.raises(SystemExit, match=r"^\[phase40_noise\] planted$"):
        phase40_noise._prove(False, "planted")
    assert phase40_noise._rel(tmp_path / "a" / "b.json", tmp_path) == "a/b.json"
    assert phase40_noise._now().endswith("+00:00")
    blob = _write(tmp_path / "blob.json", {"k": [1]})
    assert phase40_noise._load(blob) == {"k": [1]}
    assert phase40_noise._kept_identity(tmp_path / "absent.json", seeds=(1337,)) is None
    import personacore.preflight

    monkeypatch.setattr(
        personacore.preflight, "preflight_device", lambda strict: {"device": f"dev:{strict}"}
    )
    assert phase40_noise._device() == "dev:True"
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    assert phase40_noise._release() is None
    assert phase40_noise._target_fact_id() == _target().id
    full, m2 = phase40_noise.arm_spec("full"), phase40_noise.arm_spec("m2")
    assert full == teach_persona.arm_spec("real")
    assert sorted({f.id for f in full[0]} - {f.id for f in m2[0]}) == [_target().id]
    # The R-3 b helpers on the re-run rig.
    rig = _rerun_rig(monkeypatch, tmp_path / "rerun")
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert phase40_noise._dropped_attempts(2024, lines, root=rig.root, launch_git_sha="h1") == [
        rig.entry
    ]
    roots = phase40_noise._output_roots(2024, root=rig.root)
    assert len(roots) == len(phase40_prereg.GROUPS) * 7
    assert (rig.root, rig.root / phase40_prereg.a2_record("m2", 2024)) in roots
    sr = _record(rig, 2024)
    listed = phase40_noise._listed_attempts(sr, 2024, lines, root=rig.root)
    assert [a["lost_utc"] for a in listed] == [rig.lost] and listed[0]["kept_verified"] is True
    phase40_noise._verified_kept(rig.entry, root=rig.root, what="x")
    dropped = _build_rig(monkeypatch, tmp_path / "dropped")
    _ledger(dropped.ledger, ("start", 2024), ("lost", 2024))
    d_lines = phase36_ledger.read_ledger(dropped.ledger)
    assert phase40_noise._left_dropped(2024, d_lines, root=dropped.root) == {
        "manifests": [],
        "in_place": [],
    }
    utc, rel_dir = phase40_noise._latest_dropped_dir(phase40_prereg, d_lines, 2024, what="x")
    assert rel_dir == phase40_prereg.dropped_attempt_dir(2024, utc)
    outcomes = {1337: "whole", 2024: "dropped", 1338: "not_run"}
    assert phase40_noise._not_whole(outcomes, 1337) is None
    assert phase40_noise._not_whole(outcomes, 1337, 2024) == "not whole: seed 2024 is dropped"
    assert phase40_noise._not_whole(outcomes, 1338) == "not whole: seed 1338 is not_run"
    # Report helpers.
    assert phase40_noise._table(("a", "b"), [[1, "x"]]) == [
        "| a | b |",
        "|---|---|",
        "| 1 | x |",
        "",
    ]
    escaped = phase40_noise._table(("|R|",), [["a|b"]])
    assert (escaped[0], escaped[2]) == ("| \\|R\\| |", "| a\\|b |")
    assert phase40_noise._seed_order({"2024": 1, "1337": 2, "1339": 3}) == ["1337", "2024", "1339"]
    assert phase40_noise._slot_order({"pet_name": 1, "street": 2}) == ["street", "pet_name"]
    lines_ = phase40_noise._attempt_lines(rig.entry, "launch-sha")
    assert any("launch-sha" in line for line in lines_)
    assert phase40_noise._seeds_text([]) == "none"
    assert phase40_noise._seeds_text([1337, 2024]) == "1337, 2024"
    assert phase40_noise._identity_text("not whole: seed 1337 is dropped") == (
        "not whole: seed 1337 is dropped"
    )
    assert phase40_noise._identity_text(
        {"tensors_identical": False, "n_equal": 2, "n_tensors": 3}
    ).startswith("tensors_identical False (2/3 tensors equal")
    counts = {"pet_name": {"new": [1, 27], "committed": [2, 27], "delta": -1}}
    assert phase40_noise._counts_table(counts)[2] == "| pet_name | 1/27 | 2/27 | -1 |"
    draws = phase37_prereg.draw_identity([], [])
    assert phase40_noise._draws_text(draws).startswith("draw identity: bit_identical True")
    assert phase40_noise._disclosure_lines("1337", {"this_is_the_rehearsal": True}) == [
        "Seed 1337: this is the rehearsal.",
        "",
    ]


def test_census_every_phase40_noise_function_has_a_cpu_test(tmp_path):
    source = (_SCRIPTS / "phase40_noise.py").read_text(encoding="utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n.name for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert {"build_record", "emit", "render_report", "report", "main", "_tracked_and_clean"} <= set(
        defs
    )
    assert _untested_functions("phase40_noise", source, test_source) == []
    planted = source + '\n\ndef _planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase40_noise", copied, test_source) == ["_planted_untested"]


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def _driver_failures(source):
    """os.replace (only phase25_run / record may) and inject_lora (ISO-06) in the driver."""
    failures = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "replace"
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        ):
            failures.append(f"os.replace at line {node.lineno}")
        name = node.id if isinstance(node, ast.Name) else getattr(node, "attr", None)
        if name == "inject_lora" or (
            isinstance(node, ast.alias) and node.name.split(".")[-1] == "inject_lora"
        ):
            failures.append(f"inject_lora at line {node.lineno}")
    return failures


def test_no_os_replace_and_no_inject_lora(tmp_path):
    source = (_SCRIPTS / "phase40_noise.py").read_text(encoding="utf-8")
    assert _driver_failures(source) == []
    for name, plant in (
        ("replace.py", "\n\ndef planted(a, b):\n    os.replace(a, b)\n"),
        ("inject.py", "\n\ndef planted(m):\n    personacore.lora.inject.inject_lora(m)\n"),
        ("import.py", "\n\nfrom personacore.lora.inject import inject_lora\n"),
    ):
        assert _driver_failures(_planted(tmp_path, source, source + plant, name)), name


def test_driver_binds_no_slot_name(tmp_path):
    source = (_SCRIPTS / "phase40_noise.py").read_text(encoding="utf-8")
    assert _slot_census_failures([("scripts/phase40_noise.py", source)]) == []
    planted = _planted(tmp_path, source, source + "\n\nE2_S = 3\n", "slot.py")
    assert _slot_census_failures([("scripts/phase40_noise.py", planted)])


# =================================================================================================
# (13) Plan 09 Task 1: the review fixes (40-REVIEW-2 WR-01..WR-04, IN-01..IN-06).
# =================================================================================================


def test_wr01_crash_between_seed_record_and_end_line_names_rule_i_never_reconcile(
    monkeypatch, tmp_path
):
    """WR-01 / IN-06: a kill after seed 2024's record and before its end line. preflight names
    crash rule (i) (append the end line by command, NEVER reconcile); the rule-(i) recovery then
    relaunches only the not_run seed and every seed is whole."""
    seeds = (1337, 2024, 1338)
    rig = _run_fakes(monkeypatch, _tmp_rig(monkeypatch, tmp_path, seeds=seeds))
    append = phase36_ledger.append

    def killed(event, **kw):
        if event == "end" and kw["run_id"] == phase40_prereg.run_id(2024):
            raise KeyboardInterrupt("planted kill between the seed record and the end line")
        return append(event, **kw)

    monkeypatch.setattr(phase36_ledger, "append", killed)
    with pytest.raises(KeyboardInterrupt):
        phase40_noise.run(**_run_kw(rig))
    monkeypatch.setattr(phase36_ledger, "append", append)
    _threads_stopped(rig)
    rid = phase40_prereg.run_id(2024)
    assert set(phase36_ledger.open_runs(phase36_ledger.read_ledger(rig.ledger))) == {rid}
    assert (rig.root / phase40_prereg.seed_record(2024)).exists()
    with pytest.raises(SystemExit, match=r"crash rule \(i\).*NEVER reconcile") as refused:
        phase40_noise.preflight(**rig.kw)
    assert "seed2024" in str(refused.value) and "seed1337" not in str(refused.value)
    print(f"\nWR01 preflight refusal: {refused.value}")
    # Rule (i): the end line by command, then the relaunch runs only the not_run seed.
    phase36_ledger.append(
        "end",
        run_id=rid,
        phase=40,
        front="E2",
        record=phase40_prereg.seed_record(2024),
        ledger_path=rig.ledger,
    )
    rig.log.clear()
    assert phase40_noise.run(**_run_kw(rig)) == [1338]
    outcomes = phase40_prereg.seed_outcomes(phase36_ledger.read_ledger(rig.ledger), seeds)
    assert outcomes == dict.fromkeys(seeds, "whole")
    print(f"WR01 after rule (i) and the relaunch: {outcomes}")
