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

import phase14_factset  # noqa: E402  (scripts/ is not a package)
import phase14_recall  # noqa: E402  (same)
import phase18_extraction  # noqa: E402  (same)
import phase19_erasure  # noqa: E402  (same; never aliased)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)
import phase38_rank  # noqa: E402  (same)
import phase39_ctx  # noqa: E402  (same)
import phase39_prereg  # noqa: E402  (same)
import phase40_noise  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase40_prereg  # noqa: E402  (same; frozen: import only)
import teach_persona  # noqa: E402  (same)

from personacore.checkpoint import ADAPTER_SCHEMA_VERSION  # noqa: E402
from personacore.provenance import refuse_if_dirty  # noqa: E402
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


def _launch(rig):
    """The launch every refusal row goes through."""
    return phase40_noise.preflight(**rig.kw)


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
        _launch(rig)
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
        _launch(rig)
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
        _launch(rig)
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
