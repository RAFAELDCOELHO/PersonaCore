"""Plan 41-06: the E1 erasure driver (scripts/phase41_erasure.py) part 1, tested on CPU only.

The skeleton (Phase 40's shape, E1 constants), the written STOP-for-Rafael path, and the first-order
Taylor gradient ordering (D-01..D-05) on a tiny CPU GPT + LoRA fixture against finite differences.
Nothing here writes the real results/, ledger/ or data/ (the autouse guard below checks it around
every test); every output goes to a tmp root.
"""

import json
import pathlib
import re
import subprocess
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

import phase41_erasure  # noqa: E402  (scripts/ is not a package; never aliased — census by name)
import phase41_prereg  # noqa: E402  (same; frozen: import only)

from test_phase29_prereg import _git  # noqa: E402


def _phase41_outputs():
    return sorted(
        p.relative_to(_ROOT).as_posix()
        for d in ("results", "data", "checkpoints")
        for p in (_ROOT / d).glob("*phase41*")
    )


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    outputs = _phase41_outputs()
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _phase41_outputs() == outputs


# =================================================================================================
# (1) Import surface, constants, write-once, the STOP path.
# =================================================================================================


def test_the_driver_imports_without_torch():
    probe = (
        "import sys; sys.path[:0] = [{s!r}, {r!r}]; import phase41_erasure; "
        "print(phase41_erasure.FRONT, *(m in sys.modules for m in "
        "('torch', 'phase19_erasure', 'phase18_extraction', 'phase41_prereg')))"
    ).format(s=str(_SCRIPTS), r=str(_SRC))
    out = subprocess.run(
        (sys.executable, "-c", probe), capture_output=True, text=True, check=True, cwd=_ROOT
    ).stdout.strip()
    assert out == "E1 False False False False"


def test_module_constants():
    d = phase41_erasure
    assert d.FRONT == "E1"
    assert d.PREREG_FILE == "scripts/phase41_prereg.py"
    assert d.DRIVER_FILE == "scripts/phase41_erasure.py"
    assert d.FLOORS_FILE == "scripts/phase41_floors_prereg.py"
    assert d.FLOORS_FILE not in d.MODULES
    assert d.DISCLOSED_MODULES == (d.DRIVER_FILE, d.PREREG_FILE)
    assert d.MODULES[:2] == d.DISCLOSED_MODULES
    for rel in (
        "scripts/phase19_erasure.py",
        "scripts/phase18_extraction.py",
        "scripts/phase14_recall.py",
        "scripts/teach_persona.py",
        "scripts/phase37_routes.py",
        "scripts/phase40_prereg.py",
        "scripts/phase40_noise.py",
        "scripts/erasure_gate.py",
        "scripts/mitigation_gate.py",
        "scripts/phase35_prereg.py",
    ):
        assert rel in d.MODULES, rel
    assert len(set(d.MODULES)) == len(d.MODULES)
    assert all((_ROOT / rel).is_file() for rel in d.MODULES)
    digests = d.module_sha256()
    assert list(digests) == list(d.MODULES)
    assert digests[d.PREREG_FILE] == d._sha256(_ROOT / d.PREREG_FILE)
    assert (d.ARM_PREFIX, d.REHEARSAL_PREFIX, d.WORK_DIR) == ("phase41", "phase41rh", "phase41_e1")
    assert not d.DRIVER_FILE.endswith("prereg.py")
    assert d.RUN_PROVENANCE_KEYS == (
        "git_sha_at_launch",
        "git_sha_at_end",
        "head_moved_during_run",
        "device",
        "torch_version",
        "started_utc",
        "finished_utc",
    )
    # A rehearsal file never lands under the phase41 record glob.
    assert not pathlib.PurePath(f"results/{d.REHEARSAL_PREFIX}_x.json").match("phase41_*")
    assert d._prereg() is phase41_prereg


def test_module_sha256_reads_the_code_not_a_patched_root(monkeypatch, tmp_path):
    before = phase41_erasure.module_sha256()
    monkeypatch.setattr(phase41_erasure, "_ROOT", tmp_path)
    assert phase41_erasure.module_sha256() == before


def test_write_once_refuses_an_existing_file(tmp_path):
    path = tmp_path / "sub" / "blob.json"
    phase41_erasure._write_once(path, {"a": 1})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure._write_once(path, {"a": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}


def test_is_real_only_inside_the_repository(tmp_path):
    assert phase41_erasure._is_real(_ROOT)
    assert phase41_erasure._is_real(_ROOT / "data")
    assert not phase41_erasure._is_real(tmp_path)


def test_stop_for_rafael_writes_evidence_then_exits(tmp_path, monkeypatch):
    stops = tmp_path / "data" / "phase41_e1" / "stops"
    assert phase41_erasure.STOP_KINDS == (
        "d02_inequality",
        "control_gap_mismatch",
        "phase40_adapter_digest",
    )
    assert "data/phase41_e1/stops/" in phase41_prereg.ENTRIES["stop_for_rafael"]["value"]

    with pytest.raises(SystemExit, match="not one of"):
        phase41_erasure.stop_for_rafael("cell_x", "made_up", {"a": 1}, root=tmp_path)
    assert not stops.exists()

    utc = "2026-10-08T12:34:56.000001+00:00"
    monkeypatch.setattr(phase41_erasure, "_now", lambda: utc)
    evidence = {"grad": 0.5, "nograd": 0.25, "stop": True}
    with pytest.raises(SystemExit) as caught:
        phase41_erasure.stop_for_rafael("cell_x", "d02_inequality", evidence, root=tmp_path)
    assert str(caught.value).startswith("STOP FOR RAFAEL d02_inequality cell_x")
    written = stops / f"cell_x_{utc.replace(':', '')}.json"
    assert [p.name for p in stops.iterdir()] == [written.name]
    blob = json.loads(written.read_text(encoding="utf-8"))
    assert blob == {"unit": "cell_x", "kind": "d02_inequality", "evidence": evidence, "utc": utc}

    # A second call at the same instant never overwrites the first file.
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure.stop_for_rafael("cell_x", "control_gap_mismatch", {}, root=tmp_path)
    assert json.loads(written.read_text(encoding="utf-8")) == blob

    # A unit name that is not a plain file-name stem is refused before anything is written.
    with pytest.raises(SystemExit, match="unit"):
        phase41_erasure.stop_for_rafael("../x", "d02_inequality", {}, root=tmp_path)
    assert [p.name for p in stops.iterdir()] == [written.name]


# =================================================================================================
# (2) The Taylor gradient ordering (D-01..D-05) on a tiny CPU GPT + LoRA fixture.
# =================================================================================================

_SLOT, _VALUE = "hometown", "willow creek"


class _WordTok:
    """A tokenizer stand-in: one fixed id per whitespace-separated word."""

    def encode(self, text):
        return [1 + sum(map(ord, word)) % 997 for word in text.split()]


def _tiny(dtype="float32", r=8):
    """Seeded 1-layer GPT + LoRA (the tests/test_lora_toggle.py fixture), lora_B non-zero."""
    import torch

    from personacore.config import ModelConfig
    from personacore.lora import LoRAConfig, LoRALinear, inject_lora
    from personacore.model import GPT

    torch.manual_seed(1234)
    model = GPT(ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16))
    inject_lora(model, LoRAConfig(r=r))
    model = model.to(getattr(torch, dtype)).eval()
    gen = torch.Generator().manual_seed(0)
    with torch.no_grad():
        for m in model.modules():
            if isinstance(m, LoRALinear):
                m.lora_B.copy_(0.1 * torch.randn(m.lora_B.shape, generator=gen))
    return model


def _layer0(monkeypatch):
    """Point the pin's address space at the 1-layer fixture (layer 0 only); the pin file is
    untouched."""
    import phase19_erasure

    prefixes = {k: v for k, v in phase19_erasure._COMPONENT_PREFIX.items() if k[0] == 0}
    index = [a for a in phase19_erasure.component_index() if a[0] == 0]
    monkeypatch.setattr(phase19_erasure, "_COMPONENT_PREFIX", prefixes)
    monkeypatch.setattr(phase19_erasure, "component_index", lambda: list(index))
    return prefixes, index


def _fixed_ids():
    ids, ctx_len = phase41_erasure.value_ids(_WordTok(), _SLOT, _VALUE)
    return ids, ctx_len


def test_taylor_scores_identity(monkeypatch):
    import phase19_erasure
    import torch

    prefixes, _ = _layer0(monkeypatch)
    model = _tiny("float64")
    modules = phase41_erasure.lora_modules(model, prefixes)
    assert sorted(modules) == sorted(prefixes)
    ids, ctx_len = _fixed_ids()

    def loss_fn():
        return phase41_erasure.value_span_loss(model, ids, ctx_len, "cpu")

    # The state component_gradients must leave as it found it: one lora_B frozen, one with a grad.
    first, second = modules[(0, "q_proj")], modules[(0, "fc_in")]
    first.lora_B.requires_grad_(False)
    sentinel = torch.ones_like(second.lora_B)
    second.lora_B.grad = sentinel
    before = {k: (m.lora_B.requires_grad, m.lora_B.grad) for k, m in modules.items()}

    loss, g = phase41_erasure.component_gradients(loss_fn, modules)

    assert {k: (m.lora_B.requires_grad, m.lora_B.grad) for k, m in modules.items()} == before
    assert second.lora_B.grad is sentinel
    r = first.lora_B.shape[1]
    assert sorted(g) == sorted((layer, proj, j) for layer, proj in modules for j in range(r))
    assert loss == float(loss_fn())

    # (b) the A-side identity: sum_k A[j, k] dLoss/dA[j, k].
    a_params = [modules[k].lora_A for k in sorted(modules)]
    grads_a = torch.autograd.grad(loss_fn(), a_params)
    for k, ga in zip(sorted(modules), grads_a):
        side_a = (ga * modules[k].lora_A.detach()).sum(dim=1)
        for j in range(r):
            assert torch.allclose(
                torch.tensor(g[(*k, j)], dtype=torch.float64), side_a[j], rtol=1e-10, atol=1e-14
            ), (k, j)

    # (a) the central finite difference of an explicit scale s_j on B[:, j] at s = 1.
    eps = 1e-3
    for k, m in modules.items():
        b0 = m.lora_B.detach().clone()
        for j in range(r):
            values = []
            for s in (1 + eps, 1 - eps):
                with torch.no_grad():
                    m.lora_B.copy_(b0)
                    m.lora_B[:, j] *= s
                    values.append(float(loss_fn()))
            with torch.no_grad():
                m.lora_B.copy_(b0)
            fd = (values[0] - values[1]) / (2 * eps)
            assert g[(*k, j)] == pytest.approx(fd, rel=1e-3, abs=1e-9), (k, j)
    # The pin's own address space carries the same keys the fixture's lora modules have.
    assert all(prefixes[k] == phase19_erasure._COMPONENT_PREFIX[k] for k in prefixes)


def test_component_gradients_direction_and_ties():
    a = [(0, "q_proj", 0), (0, "q_proj", 1), (0, "k_proj", 0), (0, "k_proj", 1), (1, "fc_in", 0)]
    scores = {a[0]: 0.5, a[1]: -2.0, a[2]: 0.0, a[3]: 0.0, a[4]: -2.0}
    out = phase41_erasure.gradient_ordering(
        lambda prefix: None, lambda: {"scores": scores}, index=a, rerank_at=(0,)
    )
    # Most negative g (the largest predicted NLL rise -g) first, ties by address, positive last:
    # the mirror of select_ablation_prefix's (-contribution[a], a).
    assert out["ordered"] == (a[1], a[4], a[2], a[3], a[0])
    assert out["ordered"] == tuple(sorted(a, key=lambda x: (-(-scores[x]), x)))
    assert [row[0] for row in out["rankings"][0]["scores"]] == [list(x) for x in out["ordered"]]


def _rerank_rig(index):
    loads = []

    def load(prefix):
        loads.append(tuple(prefix))

    def score():
        n = len(loads[-1])
        return {
            "scores": {a: float((i * 31 + 7 * n) % 97 - 48) for i, a in enumerate(index)},
            "d02": {"stop": False, "n": n},
            "forward_seconds": 0.25,
            "forward_backward_seconds": 1.0,
        }

    return loads, load, score


def test_gradient_ordering_reranks_at_the_points():
    import phase19_erasure

    index = phase19_erasure.component_index()
    for calibration, points in ((False, (0, 16, 32, 48, 64)), (True, (0, 16, 32, 48, 64, 128))):
        rerank_at = phase41_prereg.rerank_points("adaptive", calibration=calibration)
        assert rerank_at == points
        loads, load, score = _rerank_rig(index)
        out = phase41_erasure.gradient_ordering(load, score, index=index, rerank_at=rerank_at)
        ordered = out["ordered"]
        assert sorted(ordered) == sorted(index) and len(ordered) == len(index)
        assert [ranking["at"] for ranking in out["rankings"]] == list(points)
        assert loads == [ordered[:p] for p in points]
        bounds = list(points[1:]) + [len(index)]
        for ranking, start, stop in zip(out["rankings"], points, bounds):
            ranked = [tuple(row[0]) for row in ranking["scores"]]
            assert len(ranked) == len(index) - start
            assert set(ranked).isdisjoint(ordered[:start])
            assert ordered[start:stop] == tuple(ranked[: stop - start])
            values = [(row[1], tuple(row[0])) for row in ranking["scores"]]
            assert values == sorted(values)
        # Positions past the last point come from the last ranking.
        last = [tuple(row[0]) for row in out["rankings"][-1]["scores"]]
        assert ordered[points[-1] :] == tuple(last)
        assert out["seconds"] >= 0

    loads, load, score = _rerank_rig(index)
    static = phase41_erasure.gradient_ordering(
        load,
        score,
        index=index,
        rerank_at=phase41_prereg.rerank_points("static", calibration=False),
    )
    intact = score()["scores"]
    assert loads == [()]
    assert [ranking["at"] for ranking in static["rankings"]] == [0]
    assert static["ordered"] == tuple(sorted(index, key=lambda a: (intact[a], a)))

    for bad in ((16,), (0, 32, 16), (0, 0), (0, len(index))):
        with pytest.raises(SystemExit, match="rerank_at"):
            phase41_erasure.gradient_ordering(load, score, index=index, rerank_at=bad)


def test_ordering_recorded():
    import phase19_erasure

    index = phase19_erasure.component_index()
    _, load, score = _rerank_rig(index)
    rerank_at = phase41_prereg.rerank_points("adaptive", calibration=False)
    out = phase41_erasure.gradient_ordering(load, score, index=index, rerank_at=rerank_at)
    assert set(out) == {"ordered", "rankings", "rerank_at", "seconds"}
    assert isinstance(out["ordered"], tuple) and all(isinstance(a, tuple) for a in out["ordered"])
    assert out["rerank_at"] == rerank_at
    for ranking in out["rankings"]:
        assert set(ranking) == {
            "at",
            "scores",
            "d02",
            "forward_seconds",
            "forward_backward_seconds",
        }
        assert ranking["d02"] == {"stop": False, "n": ranking["at"]}
        assert (ranking["forward_seconds"], ranking["forward_backward_seconds"]) == (0.25, 1.0)
        assert all(isinstance(row, list) and len(row) == 2 for row in ranking["scores"])
    back = json.loads(json.dumps(out))
    assert back["ordered"] == [list(a) for a in out["ordered"]]
    assert back["rankings"] == out["rankings"]
    assert back["rerank_at"] == list(rerank_at) and back["seconds"] == out["seconds"]


def test_taylor_scores_d02_twin_matches_the_pin_forward(monkeypatch, tmp_path):
    import phase14_factset
    import phase18_extraction
    import phase19_erasure
    import torch

    _layer0(monkeypatch)
    tok = _WordTok()
    ids, ctx_len = phase41_erasure.value_ids(tok, _SLOT, _VALUE)
    preamble = phase18_extraction._frame_preamble(
        phase14_factset.SLOT_FORMS[_SLOT], phase18_extraction.ADMISSIBLE_NLL_FRAME
    )
    from personacore.dialogue import ASSISTANT_ID

    assert ids == [ASSISTANT_ID] + tok.encode(preamble) + tok.encode(_VALUE)
    assert ctx_len == 1 + len(tok.encode(preamble)) and preamble

    for dtype in ("float32", "float64"):
        model = _tiny(dtype)
        # The twin, grad enabled, against the pin's own no-grad forward on identical ids:
        # bit-equal, and equal to the pin's value_span_nll_mean.
        twin = phase41_erasure.value_span_loss(model, ids, ctx_len, "cpu")
        assert twin.requires_grad
        nograd = phase18_extraction.span_nll_from_ids(model, ids[:ctx_len], ids[ctx_len:], "cpu")
        assert float(twin) == nograd["nll_mean"]
        pin = phase19_erasure.value_span_nll_mean(model, tok, "cpu", slot=_SLOT, value=_VALUE)
        assert float(twin) == pin

    # taylor_scores' D-02 wiring, against the real pin (equal) and planted differences (stop).
    model = _tiny()
    flags = {n: p.requires_grad for n, p in model.named_parameters()}
    out = phase41_erasure.taylor_scores(
        model, tok, "cpu", slot=_SLOT, value=_VALUE, unit="cell_t", root=tmp_path
    )
    assert out["d02"]["equal"] and not out["d02"]["stop"]
    assert out["d02"]["grad"] == pin_value(model, tok)
    assert set(out) == {"scores", "d02", "forward_seconds", "forward_backward_seconds"}
    assert len(out["scores"]) == 6 * 8
    assert out["forward_seconds"] >= 0 and out["forward_backward_seconds"] >= 0
    assert {n: p.requires_grad for n, p in model.named_parameters()} == flags
    assert all(p.grad is None for p in model.parameters())

    grad_value = out["d02"]["grad"]
    monkeypatch.setattr(phase19_erasure, "value_span_nll_mean", lambda *a, **k: grad_value)
    again = phase41_erasure.taylor_scores(
        model, tok, "cpu", slot=_SLOT, value=_VALUE, unit="cell_t", root=tmp_path
    )
    assert not again["d02"]["stop"] and again["scores"] == out["scores"]
    assert not (tmp_path / "data").exists()

    monkeypatch.setattr(phase19_erasure, "value_span_nll_mean", lambda *a, **k: grad_value + 1e-6)
    with pytest.raises(SystemExit, match="^STOP FOR RAFAEL d02_inequality cell_t"):
        phase41_erasure.taylor_scores(
            model, tok, "cpu", slot=_SLOT, value=_VALUE, unit="cell_t", root=tmp_path
        )
    (stop,) = (tmp_path / "data" / "phase41_e1" / "stops").iterdir()
    blob = json.loads(stop.read_text(encoding="utf-8"))
    assert blob["kind"] == "d02_inequality" and blob["evidence"]["stop"] is True
    assert {n: p.requires_grad for n, p in model.named_parameters()} == flags
    assert torch.is_grad_enabled()


def pin_value(model, tok):
    import phase19_erasure

    return phase19_erasure.value_span_nll_mean(model, tok, "cpu", slot=_SLOT, value=_VALUE)


def test_model_gradient_ordering_on_the_tiny_fixture(monkeypatch, tmp_path):
    import dataclasses

    import phase19_erasure
    import torch

    from personacore.lora import LoRAConfig, lora_state_dict

    _, index = _layer0(monkeypatch)
    tok = _WordTok()
    model = _tiny()
    artifact = {
        "adapter": lora_state_dict(model),
        "lora_config": dataclasses.asdict(LoRAConfig(r=8)),
    }
    intact = {k: v.detach().clone() for k, v in artifact["adapter"].items()}
    out = phase41_erasure.model_gradient_ordering(
        model,
        tok,
        "cpu",
        artifact,
        slot=_SLOT,
        value=_VALUE,
        variant="static",
        calibration=False,
        unit="cell_m",
        root=tmp_path,
    )
    assert out["variant"] == "static" and out["rerank_at"] == (0,)
    assert sorted(out["ordered"]) == sorted(index)
    # The intact ranking is the gradient of the intact adapter, and the model is left intact.
    direct = phase41_erasure.taylor_scores(
        model, tok, "cpu", slot=_SLOT, value=_VALUE, unit="cell_m", root=tmp_path
    )
    assert out["ordered"] == tuple(sorted(index, key=lambda a: (direct["scores"][a], a)))
    assert all(torch.equal(v, intact[k]) for k, v in lora_state_dict(model).items())
    assert all(torch.equal(v, intact[k]) for k, v in artifact["adapter"].items())
    assert out["rankings"][0]["d02"]["equal"]
    assert phase19_erasure.ablate_components(artifact, [])["adapter"].keys() == intact.keys()


# =================================================================================================
# (3) Plan 41-07: the calibration adapter (the ONE training helper), D-11, both calibration
# orderings and cal_erase. teach_persona's arm trainer and the pin's scorers are faked.
# =================================================================================================


def _cal_rig(monkeypatch, tmp_path):
    """A tmp repository root: teach_persona._REPO_ROOT and phase14_recall.ADAPTER_PATH point into
    it, so every arm path and the production adapter are tmp files."""
    import phase14_recall
    import teach_persona

    root = tmp_path / "repo"
    for sub in ("checkpoints", "data", "results"):
        (root / sub).mkdir(parents=True)
    monkeypatch.setattr(teach_persona, "_REPO_ROOT", root)
    production = teach_persona.arm_outputs("real")["adapter"]
    production.write_bytes(b"production adapter stand-in")
    monkeypatch.setattr(phase14_recall, "ADAPTER_PATH", production)
    return root


def _fake_trainer(calls, *, mutate=None):
    """A stand-in for teach_persona's arm trainer: writes its five outputs, returns the fields."""
    import teach_persona

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
            "final_train_loss": 0.5,
            "ppl_adapter_on": 3.0,
            "ppl_adapter_off": 4.0,
            "scored_targets": 123,
        }

    return fake


def test_arm_names_never_collide(monkeypatch, tmp_path):
    import phase19_erasure
    import teach_persona

    d = phase41_erasure
    assert d.arm_name(1337) == "e1_calibration_seed1337"
    assert d.arm_name(2024, rehearsal=True) == "e1rh_calibration_seed2024"
    names = {d.arm_name(s, rehearsal=r) for s in phase41_prereg.SEEDS for r in (False, True)}
    assert len(names) == 2 * len(phase41_prereg.SEEDS)
    assert names.isdisjoint({phase19_erasure.CALIBRATION_ARM, *teach_persona.ARMS})
    with pytest.raises(SystemExit, match="seed"):
        d.arm_name(1339)
    root = _cal_rig(monkeypatch, tmp_path)
    for seed in phase41_prereg.SEEDS:
        for rehearsal, prefix in ((False, "phase41"), (True, "phase41rh")):
            paths = d.arm_paths(seed, rehearsal=rehearsal)
            arm = d.arm_name(seed, rehearsal=rehearsal)
            assert paths == teach_persona.arm_outputs(arm, prefix=prefix)
            assert paths["adapter"] == root / "checkpoints" / f"{prefix}_{arm}_adapter.pt"


@pytest.mark.parametrize("rehearsal", [False, True])
def test_train_calibration_adapter_order_and_csv_move(monkeypatch, tmp_path, rehearsal):
    import phase14_factset
    import phase14_recall
    import teach_persona

    root = _cal_rig(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(teach_persona, "train_arm", _fake_trainer(calls))
    production = phase14_recall.ADAPTER_PATH.read_bytes()
    out = phase41_erasure.train_calibration_adapter(2024, root=root, rehearsal=rehearsal)
    (call,) = calls
    prefix = "phase41rh" if rehearsal else "phase41"
    arm = phase41_erasure.arm_name(2024, rehearsal=rehearsal)
    facts, second_person, replay_ratio = teach_persona.arm_spec("cal_first_person_replay")
    assert call["facts"] == list(facts)
    assert (call["second_person"], call["replay_ratio"]) == (second_person, replay_ratio)
    assert call["family_ids"] == phase14_factset.TAUGHT_FAMILY_IDS
    assert (call["arm"], call["seed"], call["prefix"]) == (arm, 2024, prefix)
    assert call["kw"] == {}  # no resume_from, no DP, no adversarial ratio
    paths = teach_persona.arm_outputs(arm, prefix=prefix)
    dst = root / "data" / "phase41_e1" / arm / "run.csv"
    assert dst.read_bytes() == f"{arm}:csv".encode()
    assert not paths["csv"].parent.exists()
    assert phase14_recall.ADAPTER_PATH.read_bytes() == production
    assert out == {
        "seed": 2024,
        "arm": arm,
        "prefix": prefix,
        "adapter": f"checkpoints/{prefix}_{arm}_adapter.pt",
        "adapter_sha256": phase41_erasure._sha256(paths["adapter"]),
        "checkpoint": f"checkpoints/{prefix}_{arm}_latest.pt",
        "csv": f"data/phase41_e1/{arm}/run.csv",
        "csv_sha256": phase41_erasure._sha256(dst),
        "train": {
            "final_train_loss": 0.5,
            "ppl_adapter_on": 3.0,
            "ppl_adapter_off": 4.0,
            "scored_targets": 123,
        },
    }


@pytest.mark.parametrize("key", ["adapter", "checkpoint", "bin", "mask", "csv_destination"])
def test_train_calibration_adapter_refuses_an_existing_output(monkeypatch, tmp_path, key):
    import teach_persona

    root = _cal_rig(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(teach_persona, "train_arm", _fake_trainer(calls))
    arm = phase41_erasure.arm_name(1337)
    path = (
        root / "data" / "phase41_e1" / arm / "run.csv"
        if key == "csv_destination"
        else phase41_erasure.arm_paths(1337)[key]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"stale")
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure.train_calibration_adapter(1337, root=root)
    assert calls == []


def test_train_calibration_adapter_refuses_a_changed_production_adapter(monkeypatch, tmp_path):
    import phase14_recall
    import teach_persona

    root = _cal_rig(monkeypatch, tmp_path)
    calls = []
    fake = _fake_trainer(calls, mutate=lambda: phase14_recall.ADAPTER_PATH.write_bytes(b"x"))
    monkeypatch.setattr(teach_persona, "train_arm", fake)
    with pytest.raises(SystemExit, match="persona_adapter"):
        phase41_erasure.train_calibration_adapter(1337, root=root)
    assert len(calls) == 1


def _adapter_file(path, *, bump=False):
    import torch

    from personacore.checkpoint import export_adapter

    tensors = {
        "blocks.0.attn.q_proj.lora_A": torch.arange(6, dtype=torch.float32).reshape(2, 3),
        "blocks.0.attn.q_proj.lora_B": torch.ones(3, 2),
    }
    if bump:
        t = tensors["blocks.0.attn.q_proj.lora_B"]
        t[0, 0] = torch.nextafter(t[0, 0], torch.tensor(2.0))
    path.parent.mkdir(parents=True, exist_ok=True)
    export_adapter(path, adapter=tensors, lora_config={"r": 2}, base_fingerprint={"git_sha": "x"})
    return path


@pytest.mark.parametrize("record_matches", [True, False])
def test_calibration_identity_uses_tensor_equality(monkeypatch, tmp_path, record_matches):
    import ast
    import inspect
    import textwrap

    import phase19_erasure
    import teach_persona

    _cal_rig(monkeypatch, tmp_path)
    reference = teach_persona.arm_outputs(
        phase19_erasure.CALIBRATION_ARM, prefix=phase19_erasure.RETRAIN_PREFIX
    )["adapter"]
    _adapter_file(reference)
    # D-11 amendment: the reference digest is the prereg's, read from the committed record.
    assert (
        phase41_prereg.D11_REFERENCE_SHA256
        == json.loads((_ROOT / phase41_prereg.D11_REFERENCE_RECORD).read_text(encoding="utf-8"))[
            phase41_prereg.D11_REFERENCE_KEY
        ]
    )
    if record_matches:
        monkeypatch.setattr(
            phase41_prereg, "D11_REFERENCE_SHA256", phase41_erasure._sha256(reference)
        )
    same = _adapter_file(tmp_path / "new" / "e1_calibration_seed1337_adapter.pt")
    other = _adapter_file(tmp_path / "new" / "bumped.pt", bump=True)
    assert phase41_erasure._sha256(same) != phase41_erasure._sha256(reference)  # the stem effect

    out = phase41_erasure.calibration_identity(same)
    assert out["tensors_identical"] is True and out["n_equal"] == out["n_tensors"] == 2
    assert out["reference_sha256"] == phase41_erasure._sha256(reference)
    assert out["reference_sha256_matches_record"] is record_matches
    assert out["reference_record"] == phase41_prereg.D11_REFERENCE_RECORD
    assert out["criterion"] is False
    assert (out["finding"] is None) is record_matches  # a mismatch is a finding, never a refusal
    off = phase41_erasure.calibration_identity(other)
    assert off["tensors_identical"] is False and off["n_equal"] == 1
    assert off["reference_sha256_matches_record"] is record_matches

    # AST: no hashlib in the function; the one digest taken is the reference file's (its original
    # path), never the new adapter's.
    fn = ast.parse(textwrap.dedent(inspect.getsource(phase41_erasure.calibration_identity)))
    names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    assert "hashlib" not in names
    digests = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_sha256"
    ]
    assert [ast.unparse(n.args[0]) for n in digests] == ["reference"]


class _Recorder:
    def __init__(self, result):
        self.calls, self.result = [], result

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


def test_greedy_calibration_passes_the_twin_references(monkeypatch):
    import phase14_factset
    import phase18_extraction
    import phase19_erasure

    index = phase19_erasure.component_index()
    ordered = tuple(reversed(index))
    rec = _Recorder({"k": 7, "stopped": True, "cap": 288, "ordered": ordered, "curve": ("c",)})
    monkeypatch.setattr(phase19_erasure, "select_ablation_prefix", rec)
    dialogue = []
    monkeypatch.setattr(
        phase19_erasure, "dialogue_ppl_pair", lambda *a: dialogue.append(a) or {"d": 1}
    )
    fact = phase19_erasure.select_calibration_fact()
    model, tok, artifact = object(), object(), {"adapter": {}}
    out = phase41_erasure.greedy_calibration(model, tok, "cpu", "forbid", artifact, fact)
    ((args, kw),) = rec.calls
    assert args == (model, tok, "cpu", artifact)
    assert (kw["slot"], kw["value"]) == (fact.slot, fact.value)
    assert kw["references"] == phase19_erasure.reference_set_for_calibration(fact.slot, fact)
    taught = {f.slot: f.value for f in phase14_factset.LOCKED_FACTS}
    assert kw["collateral"] == {
        slot: (taught[slot], phase18_extraction.reference_set_for(slot))
        for slot in phase18_extraction.CORE_SLOTS
    }
    assert kw["dialogue_ppl"]() == {"d": 1} and dialogue == [(model, "cpu", "forbid")]
    assert out == {
        "ordered": ordered,
        "k": 7,
        "stopped": True,
        "applied": ordered[:7],
        "curve": ("c",),
    }


@pytest.mark.parametrize("stop_at", [3, None])
def test_gradient_calibration_rank_stop(monkeypatch, tmp_path, stop_at):
    import dataclasses

    import phase19_erasure
    import torch

    from personacore.lora import LoRAConfig, lora_state_dict

    _, index = _layer0(monkeypatch)
    model = _tiny()
    artifact = {
        "adapter": lora_state_dict(model),
        "lora_config": dataclasses.asdict(LoRAConfig(r=8)),
    }
    intact = {k: v.detach().clone() for k, v in artifact["adapter"].items()}
    ordered = tuple(reversed(index))
    orderings = _Recorder({"ordered": ordered, "rankings": [], "variant": "adaptive"})
    monkeypatch.setattr(phase41_erasure, "model_gradient_ordering", orderings)
    ranks = []

    def fake_rank(m, tok, device, *, slot, value, references):
        ranks.append((slot, value, references))
        return (2 if stop_at is not None and len(ranks) >= stop_at else 1), 0.5

    monkeypatch.setattr(phase19_erasure, "_rank_of", fake_rank)
    fact = phase19_erasure.select_calibration_fact()
    out = phase41_erasure.gradient_calibration(
        model, "tok", "cpu", artifact, fact, variant="adaptive", unit="cal_u", root=tmp_path
    )
    ((args, kw),) = orderings.calls
    assert args == (model, "tok", "cpu", artifact)
    assert kw == {
        "slot": fact.slot,
        "value": fact.value,
        "variant": "adaptive",
        "calibration": True,
        "unit": "cal_u",
        "root": tmp_path,
    }
    twin = phase19_erasure.reference_set_for_calibration(fact.slot, fact)
    assert all(r == (fact.slot, fact.value, twin) for r in ranks)
    k = stop_at if stop_at is not None else len(index)
    assert len(ranks) == k
    assert out["k"] == k and out["stopped"] is (stop_at is not None)
    assert out["applied"] == ordered[:k] and out["ordering"] is orderings.result
    # The model is left with the intact adapter.
    assert all(torch.equal(v, intact[k2]) for k2, v in lora_state_dict(model).items())


def test_cal_erase_writes_under_data_only(monkeypatch, tmp_path):
    import fnmatch

    import phase19_erasure

    calls = []

    def fake(arm, device, **kw):
        calls.append((arm, device, kw))
        kw["record_path"].write_text('{"arm": "cal-erased"}', encoding="utf-8")

    monkeypatch.setattr(phase19_erasure, "run_erasure_arm", fake)
    adapter = tmp_path / "checkpoints" / "cal_adapter.pt"
    components = ((0, "q_proj", 1), (1, "fc_in", 3))
    out = phase41_erasure.cal_erase(
        "gradient", 2024, adapter, components, root=tmp_path, device="cpu"
    )
    record = tmp_path / "data" / "phase41_e1" / "cal_erased_gradient_seed2024.json"
    assert calls == [
        (
            "cal-erased",
            "cpu",
            {
                "corpus_path": phase19_erasure.CALIBRATION_CORPUS_PATH,
                "adapter_path": adapter,
                "components": list(components),
                "record_path": record,
            },
        )
    ]
    assert out == {
        "record": "data/phase41_e1/cal_erased_gradient_seed2024.json",
        "record_sha256": phase41_erasure._sha256(record),
    }
    assert not fnmatch.fnmatch(out["record"], phase41_prereg.RECORD_GLOB)
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure.cal_erase(
            "gradient", 2024, adapter, components, root=tmp_path, device="cpu"
        )
    assert len(calls) == 1
    with pytest.raises(SystemExit, match="ordering"):
        phase41_erasure.cal_erase("random", 2024, adapter, components, root=tmp_path, device="cpu")


# =================================================================================================
# (4) Plan 41-07: the control gap, the cell orderings, the K = 16 reader, the K = 48
# confirmation, the M1 export and the D-13 wrapper. The pin's scorers and loaders are faked.
# =================================================================================================


def _noise_floor():
    return json.loads((_ROOT / phase41_prereg.NOISE_FLOOR_RECORD).read_text(encoding="utf-8"))


def test_phase40_adapter_paths_from_the_record():
    committed = _noise_floor()["phase41_adapters"]
    for seed in phase41_prereg.SEEDS:
        for group in ("full", "m2"):
            assert phase41_erasure.phase40_adapter(seed, group) == committed[str(seed)][group]
    with pytest.raises(SystemExit, match="seed"):
        phase41_erasure.phase40_adapter(1339, "full")
    with pytest.raises(SystemExit, match="group"):
        phase41_erasure.phase40_adapter(1337, "m1")


@pytest.mark.parametrize("device", ["mps", "cpu"])
@pytest.mark.parametrize("equal", [True, False])
def test_measure_control_gap_wiring(monkeypatch, device, equal):
    import phase14_recall
    import phase19_erasure

    seed = phase41_prereg.SEEDS[1]
    committed = _noise_floor()["per_seed"][str(seed)]["full"]["dialogue_gap"]["gap"]
    loads = []
    model, forbid = object(), object()

    def fake_load(dev, adapter_path=None):
        loads.append((dev, adapter_path))
        return model, "cfg", "tok", forbid, "artifact"

    monkeypatch.setattr(phase14_recall, "load_adapted_model", fake_load)
    off = 4.5
    on = off + committed if equal else off + committed + 1e-9
    pair = {"adapter_on": on, "adapter_off": off, "n_targets": 7}
    seen = []
    monkeypatch.setattr(
        phase19_erasure, "dialogue_ppl_pair", lambda *a: seen.append(a) or dict(pair)
    )
    out = phase41_erasure.measure_control_gap(seed, device)
    assert loads == [(device, _ROOT / phase41_erasure.phase40_adapter(seed, "full")["path"])]
    assert seen == [(model, device, forbid)]
    assert out == {
        "dialogue_ppl": pair,
        **phase41_prereg.control_gap_check(on - off, committed, device=device),
    }
    assert out["equal"] is ((on - off) == committed)
    assert out["stop"] is (device == "mps" and not out["equal"])


def test_cell_ordering_greedy_uses_the_defect_e_route(monkeypatch, tmp_path):
    import phase14_factset
    import phase19_erasure
    import phase37_routes

    rec = _Recorder({"k": 9, "stopped": True, "ordered": ("a", "b"), "curve": ("c",), "cap": 2})
    monkeypatch.setattr(phase37_routes, "select_target_prefix", rec)
    seen = []
    monkeypatch.setattr(phase19_erasure, "dialogue_ppl_pair", lambda *a: seen.append(a) or "ppl")
    model, tok, artifact = object(), object(), {"adapter": {}}
    out = phase41_erasure.cell_ordering(
        model,
        tok,
        "cpu",
        "forbid",
        artifact,
        target="street",
        ordering="greedy",
        variant="adaptive",
        unit="cell_u",
        root=tmp_path,
    )
    ((args, kw),) = rec.calls
    assert args == (model, tok, "cpu", artifact)
    (street,) = [f for f in phase14_factset.LOCKED_FACTS if f.slot == "street"]
    assert kw["fact"] == street and set(kw) == {"fact", "dialogue_ppl"}
    assert kw["dialogue_ppl"]() == "ppl" and seen == [(model, "cpu", "forbid")]
    assert out == {"ordered": ("a", "b"), "k": 9, "stopped": True, "curve": ("c",)}

    grad = _Recorder({"ordered": ("x",), "rankings": [], "variant": "static"})
    monkeypatch.setattr(phase41_erasure, "model_gradient_ordering", grad)
    alternative = phase41_prereg.E1_ALTERNATIVE_ORDERING["value"]
    out = phase41_erasure.cell_ordering(
        model,
        tok,
        "cpu",
        "forbid",
        artifact,
        target="street",
        ordering=alternative,
        variant="static",
        unit="cell_u",
        root=tmp_path,
    )
    ((args, kw),) = grad.calls
    assert args == (model, tok, "cpu", artifact)
    assert kw == {
        "slot": "street",
        "value": street.value,
        "variant": "static",
        "calibration": False,
        "unit": "cell_u",
        "root": tmp_path,
    }
    assert out is grad.result
    assert len(rec.calls) == 1
    with pytest.raises(SystemExit, match="ordering"):
        phase41_erasure.cell_ordering(
            model,
            tok,
            "cpu",
            "forbid",
            artifact,
            target="street",
            ordering="random",
            variant="static",
            unit="cell_u",
            root=tmp_path,
        )


class _DecodeTok:
    def decode(self, ids):
        return " ".join(f"t{i}" for i in ids)


def _a2_entry(seed_index, fact_id, slot):
    return {
        "family": "A2",
        "dose": 1,
        "fact_id": fact_id,
        "slot": slot,
        "tier": "reported",
        "seed_index": seed_index,
        "prompt_ids": [5, 6, 7, 8 + seed_index],
        "realized_injection": 1,
        "source_family": "A1",
    }


def test_k16_read_draw_loop(monkeypatch):
    import phase14_factset
    import phase14_recall
    import phase18_extraction
    import phase35_prereg
    import teach_persona

    entries = (_a2_entry(0, "f_a", "street"), _a2_entry(3, "f_b", "pet_name"))
    monkeypatch.setattr(phase35_prereg, "a2_corpus_entries", lambda: entries)
    events = []
    monkeypatch.setattr(teach_persona, "seed_everything", lambda s: events.append(("seed", s)))

    def fake_assert(tok, question, values, *, prompt_ids=None):
        events.append(("assert", question, tuple(values), tuple(prompt_ids)))

    read_k = phase41_prereg.E1_CHECKPOINT_GRID["read_k"]

    def fake_draw(model, tok, prompt_ids, device, forbid, index, *, n_samples):
        events.append(("draw", tuple(prompt_ids), device, forbid, index, n_samples))
        return [f"c{i}" for i in range(n_samples + 1)], [False] * (n_samples + 1)

    monkeypatch.setattr(phase14_recall, "assert_no_value_in_prompt", fake_assert)
    monkeypatch.setattr(phase14_recall, "draw_all", fake_draw)
    exposure = []
    monkeypatch.setattr(
        phase18_extraction,
        "measure_exposure",
        lambda m, t, d, *, slot, taught_value: exposure.append((slot, taught_value)) or {"r": 1},
    )
    tok = _DecodeTok()
    out = phase41_erasure.k16_read("model", tok, "cpu", "forbid", target="street")

    values = tuple(f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS)
    expected = [("seed", phase14_recall.SEED)]
    for entry in entries:
        span = phase18_extraction._guarded_span(entry)
        expected.append(("assert", tok.decode(span), values, tuple(span)))
        expected.append(
            (
                "draw",
                tuple(entry["prompt_ids"]),
                "cpu",
                "forbid",
                entry["seed_index"] * phase18_extraction.K,
                read_k - 1,
            )
        )
    assert events == expected
    (street,) = [f for f in phase14_factset.LOCKED_FACTS if f.slot == "street"]
    assert exposure == [("street", street.value)]
    assert out["k"] == read_k and out["exposure"] == {"r": 1}
    assert [d["fact_id"] for d in out["draws"]] == ["f_a", "f_b"]
    for draw, entry in zip(out["draws"], entries):
        assert set(draw) == {
            "family",
            "dose",
            "fact_id",
            "slot",
            "tier",
            "arm",
            "seed_index",
            "prefix_text",
            "completions",
            "stopped",
        }
        assert draw["arm"] == phase18_extraction.ARMS[0]
        assert len(draw["completions"]) == read_k
        assert draw["prefix_text"] == tok.decode(entry["prompt_ids"][-1:])

    # A short draw set is refused.
    monkeypatch.setattr(
        phase14_recall, "draw_all", lambda *a, n_samples: (["c"] * n_samples, [False] * n_samples)
    )
    with pytest.raises(SystemExit, match="completions"):
        phase41_erasure.k16_read("model", tok, "cpu", "forbid", target="street")


def test_k16_reader_passes_the_draw_all_census():
    from test_phase14_scoring import _call_sites, _function_index

    sites = [s for s in _call_sites("draw_all") if s[0] == "scripts/phase41_erasure.py"]
    assert [s[1] for s in sites] == ["k16_read"]
    asserting, decorated = _function_index()
    assert ("scripts/phase41_erasure.py", "k16_read") in asserting
    assert ("scripts/phase41_erasure.py", "k16_read") not in decorated


@pytest.mark.parametrize("zero", [False, True])
def test_k48_confirm_calls_the_pin_with_the_record_path(monkeypatch, tmp_path, zero):
    import shutil

    import phase19_erasure

    committed = _ROOT / "results" / "phase40_a2_full_seed1337.json"
    calls = []

    def fake(arm, device, **kw):
        calls.append((arm, device, kw))
        shutil.copyfile(committed, kw["record_path"])

    monkeypatch.setattr(phase19_erasure, "run_erasure_arm", fake)
    if zero:
        real = phase41_prereg.record_rows
        monkeypatch.setattr(
            phase41_prereg,
            "record_rows",
            lambda r: {**real(r), "street": {**real(r)["street"], "n_answerable": 0}},
        )
    components = ((0, "q_proj", 1),)
    out = phase41_erasure.k48_confirm(
        "street", "greedy", 1337, 16, components, root=tmp_path, device="cpu"
    )
    rel = phase41_prereg.k48_record("street", "greedy", 1337, 16)
    record = tmp_path / rel
    assert calls == [
        (
            "erased",
            "cpu",
            {
                "adapter_path": _ROOT / phase41_erasure.phase40_adapter(1337, "full")["path"],
                "components": list(components),
                "record_path": record,
            },
        )
    ]
    assert out == {
        "record": rel,
        "record_sha256": phase41_erasure._sha256(record),
        "target_zero": zero,
    }
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure.k48_confirm(
            "street", "greedy", 1337, 16, components, root=tmp_path, device="cpu"
        )
    assert len(calls) == 1


def test_export_m1_and_d13_at_stop(monkeypatch, tmp_path):
    import dataclasses

    import phase19_erasure
    import phase40_noise
    import phase40_prereg
    import torch

    from personacore.checkpoint import load_adapter
    from personacore.lora import LoRAConfig, lora_state_dict

    model = _tiny()
    artifact = {
        "adapter": {k: v.detach().clone() for k, v in lora_state_dict(model).items()},
        "lora_config": dataclasses.asdict(LoRAConfig(r=8)),
        "base_fingerprint": {"git_sha": "abc", "step": 1, "val_loss": 2.0},
    }
    components = ((0, "q_proj", 1), (0, "fc_in", 5))
    path = tmp_path / "data" / "phase41_e1" / "m1" / "cell_k016_adapter.pt"
    out = phase41_erasure.export_m1(artifact, components, path)
    back = load_adapter(path)
    assert out == {"path": path, "sha256": phase41_erasure._sha256(path)}
    assert back["lora_config"] == artifact["lora_config"]
    assert back["base_fingerprint"] == artifact["base_fingerprint"]
    want = phase19_erasure.ablate_components(artifact, list(components))["adapter"]
    assert sorted(back["adapter"]) == sorted(want)
    assert all(torch.equal(back["adapter"][k], want[k]) for k in want)
    for layer, proj, j in components:
        prefix = phase19_erasure._COMPONENT_PREFIX[(layer, proj)]
        assert not back["adapter"][f"{prefix}.lora_A"][j].any()
        assert not back["adapter"][f"{prefix}.lora_B"][:, j].any()
        assert artifact["adapter"][f"{prefix}.lora_B"][:, j].any()  # the input is untouched
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure.export_m1(artifact, components, path)

    seen = []

    def raising(*args):
        seen.append(args)
        raise RuntimeError("boom")

    monkeypatch.setattr(phase40_noise, "d13_scores", raising)
    got = phase41_erasure.d13_at_stop(path, tmp_path / "k48.json", "cpu", {"s": 1})
    assert seen == [(path, tmp_path / "k48.json", "cpu", {"s": 1})]
    assert got == {
        **phase40_prereg.d13_not_measured("exception", "RuntimeError: boom"),
        "n_nlls": None,
    }

    def refusing(*args):
        raise SystemExit("refused")

    monkeypatch.setattr(phase40_noise, "d13_scores", refusing)
    got = phase41_erasure.d13_at_stop(path, tmp_path / "k48.json", "cpu", {})
    assert got["failure_kind"] == "exception" and got["reason"] == "SystemExit: refused"

    monkeypatch.setattr(phase40_noise, "d13_scores", lambda *a: {"measured": "yes"})
    got = phase41_erasure.d13_at_stop(path, tmp_path / "k48.json", "cpu", {})
    assert got["failure_kind"] == "malformed_reading" and got["n_nlls"] is None

    measured = {"measured": True, "n_nlls": 925, "curve": [1]}
    monkeypatch.setattr(phase40_noise, "d13_scores", lambda *a: measured)
    assert phase41_erasure.d13_at_stop(path, tmp_path / "k48.json", "cpu", {}) is measured

    def interrupted(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(phase40_noise, "d13_scores", interrupted)
    with pytest.raises(KeyboardInterrupt):
        phase41_erasure.d13_at_stop(path, tmp_path / "k48.json", "cpu", {})


def _record_path_failures(source):
    import ast

    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and (getattr(node.func, "attr", None) or getattr(node.func, "id", None))
        == "run_erasure_arm"
        and not any(k.arg == "record_path" for k in node.keywords)
    ]


def test_run_erasure_arm_always_has_a_record_path():
    import ast

    files = sorted(_SCRIPTS.glob("phase41_*.py"))
    assert _SCRIPTS / "phase41_erasure.py" in files
    calls = 0
    for path in files:
        source = path.read_text(encoding="utf-8")
        assert _record_path_failures(source) == [], path
        calls += sum(
            1
            for n in ast.walk(ast.parse(source))
            if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "run_erasure_arm"
        )
    assert calls >= 2  # cal_erase and k48_confirm: the census is not blind
    planted = "pin.run_erasure_arm('erased', 'cpu', adapter_path=a)\n"
    assert _record_path_failures(planted) == [1]


# =================================================================================================
# (5) Plan 41-07: the E1 LaunchAgent (D-25), a mirror of the proven E2 agent.
# =================================================================================================


def test_plist_mirrors_the_e2_agent():
    import plistlib

    ours = plistlib.loads((_ROOT / "artifacts" / "com.personacore.phase41.e1.plist").read_bytes())
    e2 = plistlib.loads((_ROOT / "artifacts" / "com.personacore.phase40.e2.plist").read_bytes())
    assert ours["Label"] == "com.personacore.phase41.e1"
    args = e2["ProgramArguments"]
    assert args[3].endswith("scripts/phase40_noise.py")
    assert ours["ProgramArguments"] == [
        *args[:3],
        args[3].replace("scripts/phase40_noise.py", "scripts/phase41_erasure.py"),
        *args[4:],
    ]
    assert ours["ProgramArguments"][:2] == ["/usr/bin/caffeinate", "-dims"]
    assert ours["ProgramArguments"][4:] == ["run"]
    assert ours["RunAtLoad"] is False and ours["KeepAlive"] is False
    assert ours["StandardOutPath"] == e2["StandardOutPath"].replace(
        "logs/phase40_e2.out", "logs/phase41_e1.out"
    )
    assert ours["StandardErrorPath"] == e2["StandardErrorPath"].replace(
        "logs/phase40_e2.err", "logs/phase41_e1.err"
    )
    assert ours["StandardOutPath"].endswith("logs/phase41_e1.out")
    assert ours["StandardErrorPath"].endswith("logs/phase41_e1.err")
    changed = {"Label", "ProgramArguments", "StandardOutPath", "StandardErrorPath"}
    assert set(ours) == set(e2)
    assert {k for k in ours if ours[k] != e2[k]} == changed
    assert {k: v for k, v in ours.items() if k not in changed} == {
        k: v for k, v in e2.items() if k not in changed
    }


# =================================================================================================
# (6) Plan 41-08: preflight (ERASE-05's digests first), the rehearsal identity, the stage logic.
# =================================================================================================


def _plant(path, data=b"planted"):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _lines(path):
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def _raise(message):
    def planted(*args, **kwargs):
        raise SystemExit(message)

    return planted


def _timing(at):
    return {"at": at, "forward_seconds": 0.5, "forward_backward_seconds": 2.0, "ratio": 4.0}


def _e1_rig(monkeypatch, tmp_path, *, real=False, identity=True, seconds=True):
    """A tmp repository root (``_cal_rig``) for preflight and run. The four Phase 40 adapters are
    tmp files and ``_noise_floor`` returns the committed record with phase41_adapters rewritten to
    their paths and digests; run_inputs is empty, refuse_if_dirty records its kwargs, the caps read
    the committed budget only. ``real``: ``_ROOT`` and the milestone ledger / heartbeat point into
    the rig, HEAD is the repository's real HEAD, the device resolves to mps, and the rehearsal
    identity is recorded (with its smoke seconds unless ``seconds`` is False)."""
    import phase36_caps
    import phase36_ledger

    root = _cal_rig(monkeypatch, tmp_path)
    dirty = []
    monkeypatch.setattr(phase41_erasure, "refuse_if_dirty", lambda **kw: dirty.append(kw))
    monkeypatch.setattr(phase41_erasure, "run_inputs", lambda: ())
    monkeypatch.setattr(phase36_caps, "tracked_files", lambda: [phase36_caps.BUDGET_RECORD])
    monkeypatch.setattr(phase41_erasure, "_release", lambda: None)
    record = _noise_floor()
    for seed, groups in record["phase41_adapters"].items():
        for group, entry in groups.items():
            path = _plant(root / entry["path"], f"phase40 {group} {seed}".encode())
            entry.update(path=str(path), sha256=phase41_erasure._sha256(path))
    frozen = json.dumps(record)
    monkeypatch.setattr(phase41_erasure, "_noise_floor", lambda: json.loads(frozen))
    rig = types.SimpleNamespace(root=root, dirty=dirty, adapters=record["phase41_adapters"])
    if real:
        monkeypatch.setattr(phase41_erasure, "_ROOT", root)
        monkeypatch.setattr(phase36_ledger, "_ROOT", root)
        monkeypatch.setattr(phase36_ledger, "LEDGER_PATH", "ledger/rig_ledger.jsonl")
        heartbeat = root / "data" / "rig_heartbeat.jsonl"
        monkeypatch.setattr(phase36_ledger, "HEARTBEAT_PATH", heartbeat)
        head = _git("rev-parse", "HEAD")
        monkeypatch.setattr(phase41_erasure, "git_sha", lambda: head)
        monkeypatch.setattr(phase41_erasure, "_device", lambda: "mps")
        if identity:
            path = phase41_erasure.rehearsal_identity_path()
            phase41_erasure.record_rehearsal(path, units=phase41_prereg.PREP_UNITS)
            if seconds:
                phase41_erasure.record_rehearsal_seconds(path, 100.0, [_timing(0)])
        rig.__dict__.update(
            ledger=root / "ledger" / "rig_ledger.jsonl",
            heartbeat=heartbeat,
            head=head,
            identity=None,
            kw={},
        )
        return rig
    monkeypatch.setattr(phase41_erasure, "git_sha", lambda: "h1")
    rig.__dict__.update(
        ledger=tmp_path / "ledger.jsonl",
        heartbeat=tmp_path / "heartbeat.jsonl",
        head="h1",
        identity=tmp_path / "identity.json",
    )
    rig.kw = {
        "root": root,
        "ledger_path": rig.ledger,
        "heartbeat_path": rig.heartbeat,
        "device": "cpu",
    }
    return rig


def _ledger(path, *events):
    """Append ``(event, unit)`` lines for run_id(unit) (an end names unit_record(unit))."""
    import phase36_ledger

    for event, unit in events:
        extra = {}
        if event == "end":
            extra["record"] = phase41_prereg.unit_record(unit)
        if event == "lost":
            extra.update(seconds=0.0, flag=phase36_ledger.NO_BEAT_FLAG)
        phase36_ledger.append(
            event,
            run_id=phase41_prereg.run_id(unit),
            phase=41,
            front="E1",
            ledger_path=path,
            **extra,
        )


def _whole(path, *units):
    for unit in units:
        _ledger(path, ("start", unit), ("end", unit))


def _launch(rig, monkeypatch, **extra):
    """Every refusal row goes through run(): preflight refuses before the first start line; a
    smoke, gap or training call would mean it did not."""
    calls = []
    for name in ("ordering_smoke", "measure_control_gap", "train_calibration_adapter"):
        monkeypatch.setattr(phase41_erasure, name, lambda *a, _n=name, **k: calls.append(_n))
    kw = {**rig.kw, **extra}
    if rig.identity is not None:
        kw["rehearsal_identity"] = rig.identity
    try:
        return phase41_erasure.run(**kw)
    finally:
        assert calls == []


def test_run_inputs_are_module_constants(monkeypatch):
    import ast

    import phase14_recall
    import phase19_erasure
    import phase40_prereg
    import teach_persona

    adapters = _noise_floor()["phase41_adapters"]
    expected = (
        teach_persona.CONVBASE_BEST,
        teach_persona.TOKENIZER_PATH,
        teach_persona.DIALOG_TRAIN_BIN,
        teach_persona.DIALOG_TRAIN_MASK,
        teach_persona.DIALOG_VAL_BIN,
        teach_persona.DIALOG_VAL_MASK,
        phase14_recall.CONVBASE_SLIM,
        phase14_recall.ADAPTER_PATH,
        phase14_recall.TOKENIZER_PATH,
        phase19_erasure.RETENTION_BIN,
        phase19_erasure.PHASE18_CORPUS_PATH,
        phase19_erasure.PHASE18_ARM_RECORD_PATH,
        phase19_erasure.CALIBRATION_CORPUS_PATH,
        teach_persona.arm_outputs(
            phase19_erasure.CALIBRATION_ARM, prefix=phase19_erasure.RETRAIN_PREFIX
        )["adapter"],
        *(
            _ROOT / adapters[str(s)][g]["path"]
            for s in phase41_prereg.SEEDS
            for g in adapters[str(s)]
        ),
        _ROOT / phase41_prereg.NOISE_FLOOR_RECORD,
        *(
            _ROOT / phase40_prereg.a2_record(g, s)
            for s in phase41_prereg.SEEDS
            for g in adapters[str(s)]
        ),
    )
    assert phase41_erasure.run_inputs() == expected
    tree = ast.parse((_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8"))
    (fn,) = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "run_inputs"]
    typed = [
        n.value
        for n in ast.walk(fn)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and ("/" in n.value or n.value.endswith((".pt", ".json", ".bin")))
    ]
    assert typed == []


def test_preflight_refuses_adapter_mismatch(monkeypatch, tmp_path):
    rig = _e1_rig(monkeypatch, tmp_path)
    assert phase41_erasure.adapter_digest_failures() == []
    entry = rig.adapters["2024"]["m2"]
    path = pathlib.Path(entry["path"])
    data = bytearray(path.read_bytes())
    data[0] ^= 1
    path.write_bytes(bytes(data))
    assert phase41_erasure.adapter_digest_failures() == [
        (entry["path"], entry["sha256"], phase41_erasure._sha256(path))
    ]
    with pytest.raises(SystemExit, match="ERASE-05.*" + re.escape(entry["path"])):
        _launch(rig, monkeypatch)
    assert not rig.ledger.exists() and not rig.heartbeat.exists()
    path.unlink()
    assert phase41_erasure.adapter_digest_failures() == [(entry["path"], entry["sha256"], None)]


def _row_missing_input(rig, mp):
    missing = rig.root / "missing" / "input.bin"
    mp.setattr(phase41_erasure, "run_inputs", lambda: (missing,))
    return re.escape(f"{missing} is missing")


def _row_open_attempt(rig, mp):
    _ledger(rig.ledger, ("start", phase41_prereg.PREP_UNITS[0]))
    return "open attempt.*reconcile first"


def _row_tmp_mps(rig, mp):
    rig.kw["device"] = "mps"
    return "a rehearsal runs on CPU"


def _row_require_launch(rig, mp):
    import phase36_ledger

    mp.setattr(phase36_ledger, "require_launch", _raise("[phase36_ledger] planted PAUSE"))
    return "planted PAUSE"


def _row_dirty(rig, mp):
    mp.setattr(phase41_erasure, "refuse_if_dirty", _raise("[provenance] REFUSING: planted dirt"))
    return "planted dirt"


def _row_unknown_sha(rig, mp):
    mp.setattr(phase41_erasure, "git_sha", lambda: "unknown")
    return "could not read HEAD"


def _row_units_outside_pending(rig, mp):
    rig.kw["units"] = (phase41_prereg.CELL_UNITS[0],)
    return "units"


def _row_units_out_of_order(rig, mp):
    rig.kw["units"] = phase41_prereg.PREP_UNITS[1::-1]
    return "units"


def _row_real_cpu(rig, mp):
    mp.setattr(phase41_erasure, "_device", lambda: "cpu")
    return "E1 runs on MPS on the real root"


def _row_real_ledger(rig, mp):
    rig.kw["ledger_path"] = rig.root / "ledger" / "other.jsonl"
    return "milestone ledger"


def _row_real_no_identity(rig, mp):
    return "rehearsal identity.*is missing"


def _row_real_no_seconds(rig, mp):
    return "cpu_ordering_seconds"


def _row_real_prereg_drift(rig, mp):
    path = phase41_erasure.rehearsal_identity_path()
    identity = json.loads(path.read_text(encoding="utf-8"))
    identity["module_sha256"][phase41_erasure.PREREG_FILE] = "0" * 64
    path.write_text(json.dumps(identity), encoding="utf-8")
    return "scripts/phase41_prereg.py changed after the rehearsal"


_TMP_ROWS = (
    _row_missing_input,
    _row_open_attempt,
    _row_tmp_mps,
    _row_require_launch,
    _row_dirty,
    _row_unknown_sha,
    _row_units_outside_pending,
    _row_units_out_of_order,
)
_REAL_ROWS = (
    _row_real_cpu,
    _row_real_ledger,
    _row_real_no_identity,
    _row_real_no_seconds,
    _row_real_prereg_drift,
)


@pytest.mark.parametrize(
    "plant", _TMP_ROWS + _REAL_ROWS, ids=[f.__name__[5:] for f in _TMP_ROWS + _REAL_ROWS]
)
def test_preflight_refusals(monkeypatch, tmp_path, plant):
    if plant in _REAL_ROWS:
        rig = _e1_rig(
            monkeypatch,
            tmp_path,
            real=True,
            identity=plant is not _row_real_no_identity,
            seconds=plant is not _row_real_no_seconds,
        )
    else:
        rig = _e1_rig(monkeypatch, tmp_path)
    match = plant(rig, monkeypatch)
    before = _lines(rig.ledger)
    with pytest.raises(SystemExit, match=match):
        _launch(rig, monkeypatch)
    assert _lines(rig.ledger) == before
    assert not rig.heartbeat.exists()


def _stale_outputs(rig, unit):
    import teach_persona

    _, ordering, seed = phase41_prereg.unit_key(unit)
    paths = phase41_erasure.arm_paths(seed, rehearsal=True)
    arm = phase41_erasure.arm_name(seed, rehearsal=True)
    work = rig.root / "data" / phase41_erasure.WORK_DIR
    assert paths["adapter"].is_relative_to(teach_persona._REPO_ROOT)
    return {
        "calibration_record": rig.root / phase41_prereg.calibration_record(ordering, seed),
        "band_record": rig.root / phase41_prereg.band_record(seed, ordering),
        "cal_erased": work / f"cal_erased_{ordering}_seed{seed}.json",
        "adapter": paths["adapter"],
        "checkpoint": paths["checkpoint"],
        "bin": paths["bin"],
        "mask": paths["mask"],
        "moved_csv": work / arm / "run.csv",
    }


@pytest.mark.parametrize(
    "key",
    [
        "calibration_record",
        "band_record",
        "cal_erased",
        "adapter",
        "checkpoint",
        "bin",
        "mask",
        "moved_csv",
    ],
)
def test_preflight_refuses_a_stale_output_of_a_pending_unit(monkeypatch, tmp_path, key):
    rig = _e1_rig(monkeypatch, tmp_path)
    unit = phase41_prereg.PREP_UNITS[2]  # the first prep unit of the second seed
    path = _plant(_stale_outputs(rig, unit)[key])
    with pytest.raises(SystemExit, match=re.escape(f"{path} exists")):
        _launch(rig, monkeypatch)
    assert not rig.ledger.exists() and not rig.heartbeat.exists()


def test_preflight_second_prep_unit_never_owns_the_adapter(monkeypatch, tmp_path):
    rig = _e1_rig(monkeypatch, tmp_path)
    first, second = phase41_prereg.PREP_UNITS[:2]
    _whole(rig.ledger, first)
    for key in ("adapter", "checkpoint", "bin", "mask", "moved_csv"):
        _plant(_stale_outputs(rig, second)[key])  # the whole first unit's training outputs
    pf = phase41_erasure.preflight(**rig.kw)
    assert pf["pending"] == phase41_prereg.PREP_UNITS[1:]


def test_preflight_caps_never_pass_k48(monkeypatch, tmp_path):
    import phase36_caps

    rig = _e1_rig(monkeypatch, tmp_path)
    seen = []
    monkeypatch.setattr(
        phase36_caps, "check_unit_caps", lambda front, **counts: seen.append((front, counts))
    )
    phase41_erasure.preflight(**rig.kw)
    assert seen == [
        (
            "E1",
            {
                "cells": len(phase41_prereg.CELL_UNITS),
                "checkpoints_per_cell": len(phase41_prereg.GRID),
                "calibrations": len(phase41_prereg.PREP_UNITS),
            },
        )
    ]
    assert "k48_confirms_per_cell" in phase36_caps.CAP_FIELDS["E1"]  # the cap exists; never passed


def test_preflight_stage_logic(monkeypatch, tmp_path, capsys):
    prep, cells = phase41_prereg.PREP_UNITS, phase41_prereg.CELL_UNITS
    rig = _e1_rig(monkeypatch, tmp_path)
    pf = phase41_erasure.preflight(**rig.kw)
    assert (pf["stage"], pf["pending"]) == (1, prep)
    assert phase41_erasure.preflight(**rig.kw, units=prep[2:])["pending"] == prep[2:]
    # A second prep unit never runs before its seed's first (the first trains the adapter).
    with pytest.raises(SystemExit, match="first prep unit"):
        phase41_erasure.preflight(**rig.kw, units=prep[1:2])
    _whole(rig.ledger, *prep)
    # A rehearsal root goes straight to the cells.
    pf = phase41_erasure.preflight(**rig.kw)
    assert (pf["stage"], pf["pending"]) == (2, cells)
    assert phase41_erasure.preflight(**rig.kw, units=cells[2:3])["pending"] == cells[2:3]
    with pytest.raises(SystemExit, match="units"):
        phase41_erasure.preflight(**rig.kw, units=(cells[1], cells[0]))
    with pytest.raises(SystemExit, match="units"):
        phase41_erasure.preflight(**rig.kw, units=prep[:1])  # whole: not pending

    # A dropped prep unit (no rerun approved) keeps stage 2 closed.
    dropped = _e1_rig(monkeypatch, tmp_path / "dropped")
    _ledger(dropped.ledger, ("start", prep[0]), ("lost", prep[0]))
    _whole(dropped.ledger, *prep[1:])
    with pytest.raises(SystemExit, match="dropped"):
        phase41_erasure.preflight(**dropped.kw)
    after_crash = _e1_rig(monkeypatch, tmp_path / "crash")
    _ledger(after_crash.ledger, ("start", prep[0]), ("lost", prep[0]))
    with pytest.raises(SystemExit, match="first prep unit"):
        phase41_erasure.preflight(**after_crash.kw)
    assert phase41_erasure.preflight(**after_crash.kw, units=prep[2:])["pending"] == prep[2:]

    # The real root: cells only once the floors fill file and the 8 records are tracked + clean.
    real = _e1_rig(monkeypatch, tmp_path / "real", real=True)
    _whole(None, *prep)
    asked = []
    capsys.readouterr()
    assert phase41_erasure.preflight() == {"stage": "STAGE 1 DONE", "pending": ()}
    assert "STAGE 1 DONE" in capsys.readouterr().out.splitlines()
    monkeypatch.setattr(
        phase41_erasure, "_tracked_and_clean", lambda *rels: asked.append(rels) or False
    )
    before = _lines(real.ledger)
    assert phase41_erasure.preflight()["stage"] == "STAGE 1 DONE"
    assert _lines(real.ledger) == before and not real.heartbeat.exists()
    stage1 = tuple(
        rel
        for s in phase41_prereg.SEEDS
        for o in phase41_prereg.ORDERINGS
        for rel in (phase41_prereg.calibration_record(o, s), phase41_prereg.band_record(s, o))
    )
    assert asked == [(phase41_erasure.FLOORS_FILE, *stage1)]
    assert len(stage1) == 2 * len(prep)
    monkeypatch.setattr(phase41_erasure, "_tracked_and_clean", lambda *rels: True)
    pf = phase41_erasure.preflight()
    assert (pf["stage"], pf["pending"], pf["device"]) == (2, cells, "mps")


def test_tracked_and_clean_reads_git():
    assert phase41_erasure._tracked_and_clean(phase41_erasure.PREREG_FILE) is True
    assert phase41_erasure._tracked_and_clean(phase41_erasure.FLOORS_FILE) is False
    assert (
        phase41_erasure._tracked_and_clean(phase41_erasure.PREREG_FILE, "scripts/nope.py") is False
    )


def test_launch_pathspec_excludes_whole_and_dropped_records():
    prep, cells = phase41_prereg.PREP_UNITS, phase41_prereg.CELL_UNITS
    outcomes = dict.fromkeys(phase41_prereg.UNITS, "not_run")
    assert phase41_erasure._launch_pathspec(outcomes) == phase41_erasure.LAUNCH_PATHSPEC
    outcomes.update({prep[0]: "whole", prep[1]: "dropped", cells[0]: "whole"})
    _, t, o, s = phase41_prereg.unit_key(cells[0])
    expected = (
        phase41_prereg.calibration_record("greedy", 1337),
        phase41_prereg.band_record(1337, "greedy"),
        phase41_prereg.calibration_record("gradient", 1337),
        phase41_prereg.band_record(1337, "gradient"),
        phase41_prereg.cell_record(t, o, s),
        *(phase41_prereg.k16_record(t, o, s, c) for c in phase41_prereg.GRID),
        *(phase41_prereg.k48_record(t, o, s, c) for c in phase41_prereg.GRID),
    )
    assert phase41_erasure._launch_pathspec(outcomes) == phase41_erasure.LAUNCH_PATHSPEC + tuple(
        ":(exclude)" + rel for rel in expected
    )


def test_preflight_ok_prints_the_line(monkeypatch, tmp_path, capsys):
    rig = _e1_rig(monkeypatch, tmp_path)
    pf = phase41_erasure.preflight(**rig.kw)
    pending = ",".join(phase41_prereg.PREP_UNITS)
    assert (
        f"PREFLIGHT OK h1 device=cpu stage=1 pending={pending} variant=unset spent_E1_h=0.0000"
        in capsys.readouterr().out.splitlines()
    )
    assert set(pf) == {
        "root",
        "stage",
        "pending",
        "outcomes",
        "launch_git_sha",
        "launch_modules",
        "device",
        "gate",
        "variant",
        "rehearsal_disclosure",
        "dropped_attempts",
    }
    assert pf["dropped_attempts"] == {}
    assert pf["root"] == rig.root and pf["launch_git_sha"] == "h1" and pf["variant"] == "unset"
    assert pf["launch_modules"] == phase41_erasure.module_sha256()
    assert pf["gate"]["front"] == "E1"
    assert pf["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
    (call,) = rig.dirty
    assert call["pathspec"] == phase41_erasure.LAUNCH_PATHSPEC
    assert call["cwd"] == phase41_erasure._REPO and call["who"] == "phase41_erasure"
    _plant(
        rig.root / "data" / phase41_erasure.WORK_DIR / "variant.json",
        json.dumps({"variant": "static"}).encode(),
    )
    assert phase41_erasure.preflight(**rig.kw)["variant"] == "static"
    assert "variant=static" in capsys.readouterr().out
    assert not rig.ledger.exists() and not rig.heartbeat.exists()


def test_preflight_rehearsal_disclosure_on_the_real_root(monkeypatch, tmp_path):
    rig = _e1_rig(monkeypatch, tmp_path, real=True)
    pf = phase41_erasure.preflight()
    identity = json.loads(phase41_erasure.rehearsal_identity_path().read_text(encoding="utf-8"))
    assert pf["rehearsal_disclosure"] == phase41_erasure.rehearsal_disclosure(
        identity, launch_git_sha=rig.head, launch_module_sha256=phase41_erasure.module_sha256()
    )
    assert pf["rehearsal_disclosure"]["commits"] == []
    assert pf["device"] == "mps" and pf["pending"] == phase41_prereg.PREP_UNITS
    (call,) = rig.dirty
    assert call["pathspec"] == phase41_erasure.LAUNCH_PATHSPEC  # nothing whole yet


def test_rehearsal_identity_and_disclosure(monkeypatch, tmp_path):
    d = phase41_erasure
    prep, cells = phase41_prereg.PREP_UNITS, phase41_prereg.CELL_UNITS
    monkeypatch.setattr(d, "_ROOT", tmp_path)
    path = d.rehearsal_identity_path()
    assert path == tmp_path / "data" / "phase41_rehearsal.json"
    monkeypatch.setattr(d, "git_sha", lambda: "h1")
    with pytest.raises(SystemExit, match="missing"):
        d.record_rehearsal_seconds(path, 1.0, [_timing(0)])
    assert d.record_rehearsal(path, units=prep)["status"] == "recorded"
    identity = json.loads(path.read_text(encoding="utf-8"))
    assert set(identity) == {"git_sha", "module_sha256", "units", "started_utc"}
    assert identity["git_sha"] == "h1" and identity["units"] == list(prep)
    assert identity["module_sha256"] == {rel: d._sha256(_ROOT / rel) for rel in d.DISCLOSED_MODULES}
    monkeypatch.setattr(d, "git_sha", lambda: "h2")
    # The smoke's seconds and timings, added once and never overwritten.
    timings = [_timing(0), _timing(16)]
    d.record_rehearsal_seconds(path, 12.5, timings)
    smoked = json.loads(path.read_text(encoding="utf-8"))
    assert set(smoked) == d._IDENTITY_KEYS
    assert (smoked["cpu_ordering_seconds"], smoked["cpu_timings"]) == (12.5, timings)
    d.record_rehearsal_seconds(path, 99.0, [_timing(0)])
    assert json.loads(path.read_text(encoding="utf-8")) == smoked
    # A stage-2 call at the same digests appends its units, keeps everything else byte-identical.
    kept = d.record_rehearsal(path, units=cells[:1])
    assert kept["status"] == "kept"
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["units"] == [*prep, cells[0]]
    for key in ("git_sha", "module_sha256", "started_utc", "cpu_ordering_seconds", "cpu_timings"):
        assert json.dumps(after[key]) == json.dumps(smoked[key]), key
    d.record_rehearsal(path, units=prep[:1])  # never removes one
    assert json.loads(path.read_text(encoding="utf-8")) == after
    # Different digests: a changed driver needs a fresh rehearsal (38-REVIEW DR-02).
    drifted = {**after, "module_sha256": {**after["module_sha256"], d.DRIVER_FILE: "f" * 64}}
    path.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(SystemExit, match="fresh rehearsal"):
        d.record_rehearsal(path, units=cells[1:2])
    # One optional key without the other is malformed.
    lone = {k: v for k, v in after.items() if k != "cpu_timings"}
    path.write_text(json.dumps(lone), encoding="utf-8")
    with pytest.raises(SystemExit, match="malformed"):
        d.record_rehearsal(path, units=cells[1:2])

    # The disclosure: git log stubbed.
    logs = {"log": "", "show": ""}

    def fake_run(args, **kw):
        assert kw["cwd"] == d._REPO
        if args[1] == "log":
            assert args[3] == "h1..h9" and tuple(args[5:]) == d.DISCLOSED_MODULES
        return types.SimpleNamespace(stdout=logs["log"] if args[1] == "log" else logs["show"])

    monkeypatch.setattr(d.subprocess, "run", fake_run)
    launch = dict(after["module_sha256"])
    empty = d.rehearsal_disclosure(after, launch_git_sha="h9", launch_module_sha256=launch)
    assert empty["commits"] == [] and "no commit" in empty["statement"]
    assert empty["units_read"] == after["units"]
    assert all(unit in empty["statement"] for unit in after["units"])
    assert empty["prereg_changed"] is False and empty["driver_changed"] is False
    launch[d.DRIVER_FILE] = "f" * 64
    with pytest.raises(SystemExit, match="without a commit"):
        d.rehearsal_disclosure(after, launch_git_sha="h9", launch_module_sha256=launch)
    logs.update(log="c0ffee\tfix the driver\n", show="scripts/phase41_erasure.py\nREADME.md\n")
    moved = d.rehearsal_disclosure(after, launch_git_sha="h9", launch_module_sha256=launch)
    assert moved["commits"] == [
        {"sha": "c0ffee", "reason": "fix the driver", "modules": [d.DRIVER_FILE]}
    ]
    assert moved["changed"] == {d.DRIVER_FILE: True, d.PREREG_FILE: False}
    assert moved["driver_changed"] is True and "1 commit" in moved["statement"]


# =================================================================================================
# (7) Plan 41-08: run stage 1 — the D-02 / D-05 smoke, one ledger attempt per prep unit, the band
# and calibration records (pin, trainer and orderings faked; the driver's own code runs).
# =================================================================================================

_CAL_ERASED = _ROOT / "results" / "phase19_arm_cal-erased.json"
_SMOKE_SECONDS = 7.0


def _checked(real, fake):
    """``fake`` behind the real function's signature: a call the real one would refuse fails."""
    import inspect

    signature = inspect.signature(real)

    def wrapper(*args, **kwargs):
        signature.bind(*args, **kwargs)
        return fake(*args, **kwargs)

    return wrapper


def _smoke_fakes(monkeypatch, log, *, seconds=_SMOKE_SECONDS, stop=False):
    import phase14_recall

    def load(device, adapter_path=None):
        log.append(("load", pathlib.Path(adapter_path).name))
        return "model", "cfg", "tok", "forbid", "artifact"

    def ordering(model, tok, device, artifact, *, slot, value, variant, calibration, unit, root):
        log.append(("smoke", unit, slot, value, variant, calibration))
        if stop:
            phase41_erasure.stop_for_rafael(unit, "d02_inequality", {"planted": True}, root=root)
        points = phase41_prereg.rerank_points(variant, calibration=calibration)
        return {
            "ordered": (),
            "rankings": [
                {
                    "at": p,
                    "scores": [],
                    "d02": phase41_prereg.d02_check(1.5, 1.5),
                    "forward_seconds": 0.25,
                    "forward_backward_seconds": 1.0,
                }
                for p in points
            ],
            "rerank_at": points,
            "seconds": seconds,
            "variant": variant,
        }

    monkeypatch.setattr(
        phase14_recall, "load_adapted_model", _checked(phase14_recall.load_adapted_model, load)
    )
    monkeypatch.setattr(
        phase41_erasure,
        "model_gradient_ordering",
        _checked(phase41_erasure.model_gradient_ordering, ordering),
    )


def _run_fakes(monkeypatch, rig, *, gap_stop=False):
    """The driver's run / run_prep_unit / ordering_smoke / train_calibration_adapter / cal_erase
    run for real; the model load, the gradient ordering, the gap reading, teach_persona's trainer,
    D-11, both calibration orderings and the pin's arm are faked behind their real signatures.
    Every step, ledger call and write-once record is logged in order."""
    import shutil

    import phase19_erasure
    import phase25_run
    import phase36_ledger
    import teach_persona

    d = phase41_erasure
    log = rig.log = []
    rig.threads, rig.trained, rig.preflights = [], [], []
    index = tuple(phase19_erasure.component_index())
    _smoke_fakes(monkeypatch, log)
    monkeypatch.setattr(teach_persona, "train_arm", _fake_trainer(rig.trained))

    def gap(seed, device):
        log.append(("gap", seed, device))
        committed = _noise_floor()["per_seed"][str(seed)]["full"]["dialogue_gap"]["gap"]
        out = {
            "dialogue_ppl": {"adapter_on": 5.0, "adapter_off": 4.0, "n_targets": 7},
            **phase41_prereg.control_gap_check(committed, committed, device=device),
        }
        return {**out, "equal": False, "stop": True} if gap_stop else out

    def identity(new_adapter):
        log.append(("d11", pathlib.Path(new_adapter).name))
        return {"tensors_identical": False, "planted": "d11"}

    def greedy(model, tok, device, forbid, artifact, fact):
        log.append(("calibration", "greedy", fact.id))
        return {
            "ordered": index,
            "k": 7,
            "stopped": True,
            "applied": index[:7],
            "curve": [{"k": 1, "rank": 1}],
        }

    def gradient(model, tok, device, artifact, fact, *, variant, unit, root):
        log.append(("calibration", "gradient", fact.id, variant))
        ordered = index[::-1]
        ranking = {
            "at": 0,
            "scores": [[list(a), -float(i)] for i, a in enumerate(ordered)],
            "d02": phase41_prereg.d02_check(2.0, 2.0),
            "forward_seconds": 0.25,
            "forward_backward_seconds": 1.0,
        }
        return {
            "ordering": {
                "ordered": ordered,
                "rankings": [ranking],
                "rerank_at": (0,),
                "seconds": 3.0,
                "variant": variant,
            },
            "k": 9,
            "stopped": True,
            "applied": ordered[:9],
        }

    def arm(name, device, **kw):
        log.append(("cal_erase", name, pathlib.Path(kw["record_path"]).name))
        shutil.copyfile(_CAL_ERASED, kw["record_path"])

    for name, fake in (
        ("measure_control_gap", gap),
        ("calibration_identity", identity),
        ("greedy_calibration", greedy),
        ("gradient_calibration", gradient),
    ):
        monkeypatch.setattr(d, name, _checked(getattr(d, name), fake))
    monkeypatch.setattr(
        phase19_erasure, "run_erasure_arm", _checked(phase19_erasure.run_erasure_arm, arm)
    )
    train, preflight, write = d.train_calibration_adapter, d.preflight, d._write_once

    def logged_train(seed, **kw):
        log.append(("train", seed))
        return train(seed, **kw)

    def logged_preflight(**kw):
        rig.preflights.append(kw)
        return preflight(**kw)

    def logged_write(path, blob):
        log.append(("record", pathlib.Path(path).name))
        return write(path, blob)

    monkeypatch.setattr(d, "train_calibration_adapter", _checked(train, logged_train))
    monkeypatch.setattr(d, "preflight", logged_preflight)
    monkeypatch.setattr(d, "_write_once", logged_write)
    require, append = phase36_ledger.require_launch, phase36_ledger.append
    rig.launches = 0

    def logged_require(front, **kw):
        rig.launches += 1
        if rig.launches > 1:  # preflight's own call is not logged
            log.append(("require_launch",))
        return require(front, **kw)

    def logged_append(event, **kw):
        log.append((event, kw["run_id"]))
        return append(event, **kw)

    monkeypatch.setattr(phase36_ledger, "require_launch", logged_require)
    monkeypatch.setattr(phase36_ledger, "append", logged_append)
    start = phase25_run.start_heartbeat

    def logged_start(path, state):
        pair = start(path, state)
        rig.threads.append(pair)
        return pair

    monkeypatch.setattr(phase25_run, "start_heartbeat", logged_start)
    return rig


def _run(rig, **extra):
    kw = {**rig.kw, **extra}
    if rig.identity is not None:
        kw["rehearsal_identity"] = rig.identity
    return phase41_erasure.run(**kw)


def _expected_stage1(rig, units, *, device="cpu", smoke=True):
    import phase19_erasure

    fact = phase19_erasure.select_calibration_fact()
    full = pathlib.Path(rig.adapters[str(phase41_prereg.SEEDS[0])]["full"]["path"]).name
    target = phase41_prereg.TARGETS[0]
    rehearsal = rig.identity is not None
    expected = []
    for unit in units:
        _, o, s = phase41_prereg.unit_key(unit)
        rid = phase41_prereg.run_id(unit)
        adapter = phase41_erasure.arm_paths(s, rehearsal=rehearsal)["adapter"].name
        expected += [("require_launch",), ("start", rid)]
        if smoke and unit == phase41_prereg.PREP_UNITS[0]:
            value = phase41_erasure.target_fact(target).value
            expected += [
                ("load", full),
                ("smoke", unit, target, value, "adaptive", False),
                ("record", "variant.json"),
            ]
        expected += [
            ("gap", s, device),
            ("record", pathlib.Path(phase41_prereg.band_record(s, o)).name),
        ]
        if unit == next(u for u in phase41_prereg.PREP_UNITS if u.endswith(f"seed{s}")):
            expected.append(("train", s))
        expected += [("d11", adapter), ("load", adapter)]
        if o == "greedy":
            expected.append(("calibration", o, fact.id))
        else:
            expected.append(("calibration", o, fact.id, "adaptive"))
        expected += [
            ("cal_erase", "cal-erased", f"cal_erased_{o}_seed{s}.json"),
            ("record", pathlib.Path(phase41_prereg.calibration_record(o, s)).name),
            ("end", rid),
        ]
    return expected


def _threads_stopped(rig):
    assert rig.threads and all(s.is_set() and not t.is_alive() for s, t in rig.threads)


def _json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


_PRICE = phase41_prereg.ENTRIES["e1_unit_prices"]["value"]["e1_ordering_seconds"]


@pytest.mark.parametrize(
    ("cpu", "mps", "variant", "decided_by"),
    [
        (10.0, 20.0, "adaptive", "mps_smoke"),
        (2 * _PRICE, 20.0, "static", "cpu_rehearsal"),
        (10.0, 2 * _PRICE, "static", "mps_smoke"),
    ],
)
def test_ordering_smoke_fixes_the_variant(monkeypatch, tmp_path, cpu, mps, variant, decided_by):
    rig = _e1_rig(monkeypatch, tmp_path, real=True)
    log = []
    _smoke_fakes(monkeypatch, log, seconds=mps)
    unit = phase41_prereg.PREP_UNITS[0]
    kw = {"root": rig.root, "device": "mps", "cpu_seconds": cpu, "unit": unit}
    with pytest.raises(SystemExit, match="real root"):
        phase41_erasure.ordering_smoke(**kw, identity_path=tmp_path / "identity.json")
    blob = phase41_erasure.ordering_smoke(**kw, identity_path=None)
    points = phase41_prereg.rerank_points("adaptive", calibration=False)
    expected = {
        "variant": phase41_prereg.alternative_variant(cpu, mps),
        "variant_decided_by": decided_by,
        "cpu_seconds": cpu,
        "mps_seconds": mps,
        "d02": [phase41_prereg.d02_check(1.5, 1.5)] * len(points),
        "timings": [
            {"at": p, "forward_seconds": 0.25, "forward_backward_seconds": 1.0, "ratio": 4.0}
            for p in points
        ],
        "rehearsal": False,
        "ordering_bound": _PRICE,
    }
    assert expected["variant"] == variant
    path = rig.root / "data" / phase41_erasure.WORK_DIR / "variant.json"
    assert _json(path) == expected == blob
    assert log == [
        ("load", pathlib.Path(rig.adapters["1337"]["full"]["path"]).name),
        (
            "smoke",
            unit,
            phase41_prereg.TARGETS[0],
            phase41_erasure.target_fact(phase41_prereg.TARGETS[0]).value,
            "adaptive",
            False,
        ),
    ]
    with pytest.raises(SystemExit, match="write-once"):
        phase41_erasure.ordering_smoke(**kw, identity_path=None)
    assert phase41_erasure._variant(rig.root) == variant


def test_ordering_smoke_on_a_rehearsal_root(monkeypatch, tmp_path):
    rig = _e1_rig(monkeypatch, tmp_path)
    log = []
    _smoke_fakes(monkeypatch, log, seconds=_PRICE / 2)
    unit = phase41_prereg.PREP_UNITS[0]
    kw = {"root": rig.root, "device": "cpu", "cpu_seconds": None, "unit": unit}
    with pytest.raises(SystemExit, match="identity"):
        phase41_erasure.ordering_smoke(**kw, identity_path=None)
    assert log == []
    phase41_erasure.record_rehearsal(rig.identity, units=phase41_prereg.PREP_UNITS)
    blob = phase41_erasure.ordering_smoke(**kw, identity_path=rig.identity)
    assert blob["rehearsal"] is True and blob["variant_decided_by"] == "cpu_rehearsal"
    assert blob["cpu_seconds"] == blob["mps_seconds"] == _PRICE / 2
    assert blob["variant"] == "adaptive"
    identity = _json(rig.identity)
    assert identity["cpu_ordering_seconds"] == _PRICE / 2
    assert identity["cpu_timings"] == blob["timings"]
    assert phase41_erasure.rehearsal_identity_path() != rig.identity  # never the default path
    assert not phase41_erasure.rehearsal_identity_path().exists() or (
        phase41_erasure.rehearsal_identity_path().resolve() != rig.identity.resolve()
    )


def test_ordering_smoke_d02_stop_writes_no_variant(monkeypatch, tmp_path):
    rig = _e1_rig(monkeypatch, tmp_path, real=True)
    _smoke_fakes(monkeypatch, [], stop=True)
    unit = phase41_prereg.PREP_UNITS[0]
    with pytest.raises(SystemExit, match=f"STOP FOR RAFAEL d02_inequality {unit}"):
        phase41_erasure.ordering_smoke(
            root=rig.root, device="mps", cpu_seconds=1.0, unit=unit, identity_path=None
        )
    assert not (rig.root / "data" / phase41_erasure.WORK_DIR / "variant.json").exists()
    (stop,) = (rig.root / "data" / phase41_erasure.WORK_DIR / "stops").iterdir()
    assert _json(stop)["kind"] == "d02_inequality"
    with pytest.raises(SystemExit, match="variant.json is missing"):
        phase41_erasure._variant(rig.root)


def test_run_stage1_order_and_records(monkeypatch, tmp_path, capsys):
    import phase36_ledger

    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path))
    prep = phase41_prereg.PREP_UNITS
    assert _run(rig) == {"stage": 1, "whole": list(prep)}
    assert rig.log == _expected_stage1(rig, prep)
    _threads_stopped(rig)
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [(x["event"], x["run_id"], x["record"]) for x in lines] == [
        (event, phase41_prereg.run_id(unit), record)
        for unit in prep
        for event, record in (("start", None), ("end", phase41_prereg.unit_record(unit)))
    ]
    assert phase41_prereg.unit_outcomes(lines, prep) == dict.fromkeys(prep, "whole")
    beats = {json.loads(t)["point"] for t in _lines(rig.heartbeat)}
    assert {phase41_prereg.run_id(u) for u in prep} <= beats
    identity = _json(rig.identity)
    assert identity["units"] == list(prep) and identity["git_sha"] == "h1"
    assert identity["cpu_ordering_seconds"] == _SMOKE_SECONDS
    out = capsys.readouterr().out.splitlines()
    assert "STAGE 1 DONE" in out and f"RUN DONE whole={list(prep)}" in out
    # The trainer ran once per seed, never for a seed's second prep unit.
    assert [c["seed"] for c in rig.trained] == list(phase41_prereg.SEEDS)


def test_band_record_contract(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path))
    _run(rig)
    for unit in phase41_prereg.PREP_UNITS:
        _, o, s = phase41_prereg.unit_key(unit)
        band = _json(rig.root / phase41_prereg.band_record(s, o))
        committed = _noise_floor()["per_seed"][str(s)]["full"]["dialogue_gap"]["gap"]
        assert (band["seed"], band["ordering"], band["unit"]) == (s, o, unit)
        assert band["control_gap"] == band["committed_gap"] == committed
        assert band["equal"] is True and band["device"] == "cpu" and band["rehearsal"] is True
        assert band["dialogue_ppl"] == {"adapter_on": 5.0, "adapter_off": 4.0, "n_targets": 7}
        assert band["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
        assert set(band["provenance"]) == {"measurement"}
        assert set(band["provenance"]["measurement"]) == {"utc", "device", "git_sha"}
        assert band["provenance"]["measurement"]["git_sha"] == "h1"
        assert s in phase41_prereg.SEEDS and isinstance(o, str)


def test_calibration_record_contract(monkeypatch, tmp_path):
    import phase19_erasure
    import torch

    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path))
    _run(rig)
    index = [list(a) for a in phase19_erasure.component_index()]
    fact = phase19_erasure.select_calibration_fact()
    draws = _json(_CAL_ERASED)["draws"]
    first = {}
    for unit in phase41_prereg.PREP_UNITS:
        _, o, s = phase41_prereg.unit_key(unit)
        record = _json(rig.root / phase41_prereg.calibration_record(o, s))
        assert "target" not in record
        assert (record["ordering"], record["seed"], record["unit"]) == (o, s, unit)
        assert (record["family"], record["corpus"]) == ("A2", phase41_prereg.CALIBRATION_CORPUS)
        assert record["fact_id"] == fact.id and record["draws"] == draws
        applied = record["applied_ordering"]
        assert len(applied) == len(index) and sorted(applied) == sorted(index)
        if o == "greedy":
            assert applied == index and record["d06_order"] == index
            assert (record["k"], record["stopped"]) == (7, True)
            assert record["variant"] is None and record["variant_decided_by"] is None
        else:
            assert applied == index[::-1] and record["d06_order"] == index[::-1]
            assert (record["k"], record["stopped"]) == (9, True)
            assert record["variant"] == "adaptive"
            assert record["variant_decided_by"] == "cpu_rehearsal"
            assert record["ordering_detail"]["rankings"][0]["at"] == 0
        assert isinstance(record["ordering_seconds"], float) and record["ordering_seconds"] >= 0
        adapter = phase41_erasure.arm_paths(s, rehearsal=True)["adapter"]
        assert record["adapter"] == {
            "path": adapter.relative_to(rig.root).as_posix(),
            "sha256": phase41_erasure._sha256(adapter),
        }
        first.setdefault(s, record["adapter"])
        assert record["adapter"] == first[s]
        assert record["d11_identity"] == {"tensors_identical": False, "planted": "d11"}
        raw = rig.root / "data" / phase41_erasure.WORK_DIR / f"cal_erased_{o}_seed{s}.json"
        assert record["cal_erased_record"] == {
            "path": raw.relative_to(rig.root).as_posix(),
            "sha256": phase41_erasure._sha256(raw),
        }
        run = record["provenance"]["run"]
        assert set(run) == set(phase41_erasure.RUN_PROVENANCE_KEYS)
        assert run["device"] == "cpu" and run["torch_version"] == torch.__version__
        assert run["git_sha_at_launch"] == run["git_sha_at_end"] == "h1"
        assert run["head_moved_during_run"] is False
        assert run["started_utc"] <= run["finished_utc"]
        assert record["provenance"]["module_sha256_at_launch"] == phase41_erasure.module_sha256()
        assert record["rehearsal"] is True
        assert record["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
        with pytest.raises(SystemExit, match="write-once"):
            phase41_erasure._write_once(rig.root / phase41_prereg.calibration_record(o, s), {})


def test_stage1_records_fill_the_floors_and_bands(monkeypatch, tmp_path):
    import shutil

    import phase35_prereg

    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path))
    _run(rig)
    for rel in (phase41_prereg.CALIBRATION_CORPUS, phase41_prereg.NOISE_FLOOR_RECORD):
        (rig.root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_ROOT / rel, rig.root / rel)
    monkeypatch.setattr(phase35_prereg, "_REPO_ROOT", rig.root)
    floors = phase35_prereg.fill("e1_condition_a_floors", **phase41_prereg.floors_fill_inputs())
    assert set(floors) == set(phase41_prereg.floors_fill_inputs()["floors"])
    for row in floors.values():
        assert row["calibration_questions"] > 0
    bands = phase35_prereg.fill("e1_condition_c_band_inputs", **phase41_prereg.band_fill_inputs())
    assert set(bands) == set(phase41_prereg.band_fill_inputs()["band_inputs"])


def test_control_gap_mismatch_stops(monkeypatch, tmp_path):
    import phase36_ledger

    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), gap_stop=True)
    prep = phase41_prereg.PREP_UNITS
    with pytest.raises(SystemExit, match=f"STOP FOR RAFAEL control_gap_mismatch {prep[0]}"):
        _run(rig)
    _threads_stopped(rig)
    _, o, s = phase41_prereg.unit_key(prep[0])
    assert not (rig.root / phase41_prereg.band_record(s, o)).exists()
    assert ("train", s) not in rig.log
    (stop,) = (rig.root / "data" / phase41_erasure.WORK_DIR / "stops").iterdir()
    assert _json(stop)["kind"] == "control_gap_mismatch"
    assert _json(stop)["evidence"]["stop"] is True
    assert (rig.root / "data" / phase41_erasure.WORK_DIR / "variant.json").exists()
    rid = phase41_prereg.run_id(prep[0])
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [(x["event"], x["run_id"]) for x in lines] == [("start", rid)]
    (lost,) = phase36_ledger.reconcile(ledger_path=rig.ledger, heartbeat_path=rig.heartbeat)
    assert (lost["event"], lost["run_id"]) == ("lost", rid)
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert phase41_prereg.unit_outcomes(lines, prep)[prep[0]] == "dropped"
    # The relaunch: the seed's second prep unit is refused, the other seed runs; no second smoke.
    rig = _run_fakes(monkeypatch, rig)
    with pytest.raises(SystemExit, match="first prep unit"):
        _run(rig)
    assert _run(rig, units=prep[2:]) == {"stage": 1, "whole": list(prep[2:])}
    assert rig.log == _expected_stage1(rig, prep[2:], smoke=False)


def test_second_prep_unit_reuses_the_seed_adapter(monkeypatch, tmp_path):
    prep = phase41_prereg.PREP_UNITS
    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path))
    assert _run(rig, units=prep[:1])["whole"] == list(prep[:1])
    rig.log.clear()
    assert _run(rig, units=prep[1:2])["whole"] == list(prep[1:2])
    assert not [e for e in rig.log if e[0] == "train"]
    first, second = (_json(rig.root / phase41_prereg.unit_record(u))["adapter"] for u in prep[:2])
    assert first == second
    # A changed adapter between the two prep units of a seed refuses.
    other = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path / "other"))
    _run(other, units=prep[:1])
    adapter = phase41_erasure.arm_paths(1337, rehearsal=True)["adapter"]
    adapter.write_bytes(adapter.read_bytes() + b"x")
    with pytest.raises(SystemExit, match="sha256"):
        _run(other, units=prep[1:2])
    assert not (other.root / phase41_prereg.unit_record(prep[1])).exists()


def test_run_with_no_arguments_resolves_the_real_defaults(monkeypatch, tmp_path, capsys):
    import inspect

    import phase36_ledger

    assert all(
        p.default is None for p in inspect.signature(phase41_erasure.run).parameters.values()
    )
    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path, real=True))
    prep = phase41_prereg.PREP_UNITS
    assert phase41_erasure.run() == {"stage": 1, "whole": list(prep)}
    (call,) = rig.preflights
    assert call == {
        "root": phase41_erasure._ROOT,
        "ledger_path": None,
        "heartbeat_path": None,
        "device": None,
        "units": None,
    }
    assert call["root"] == rig.root
    assert rig.log == _expected_stage1(rig, prep, device="mps")
    lines = phase36_ledger.read_ledger(None)
    assert rig.ledger.exists()
    assert [(x["event"], x["run_id"]) for x in lines] == [
        (event, phase41_prereg.run_id(u)) for u in prep for event in ("start", "end")
    ]
    beats = {json.loads(t)["point"] for t in _lines(rig.heartbeat)}
    assert {phase41_prereg.run_id(u) for u in prep} <= beats
    variant = _json(rig.root / "data" / phase41_erasure.WORK_DIR / "variant.json")
    assert (variant["cpu_seconds"], variant["mps_seconds"]) == (100.0, _SMOKE_SECONDS)
    assert variant["rehearsal"] is False and variant["variant_decided_by"] == "mps_smoke"
    for unit in prep:
        _, o, s = phase41_prereg.unit_key(unit)
        for rel in (phase41_prereg.unit_record(unit), phase41_prereg.band_record(s, o)):
            record = _json(rig.root / rel)
            assert record["rehearsal"] is False
            assert record["rehearsal_disclosure"]["commits"] == []
        record = _json(rig.root / phase41_prereg.unit_record(unit))
        assert record["provenance"]["run"]["device"] == "mps"
        assert record["adapter"]["path"].startswith("checkpoints/phase41_e1_calibration_seed")
    assert "STAGE 1 DONE" in capsys.readouterr().out.splitlines()


def test_run_stage_gates(monkeypatch, tmp_path, capsys):
    prep = phase41_prereg.PREP_UNITS
    real = _e1_rig(monkeypatch, tmp_path / "real", real=True)
    _whole(None, *prep)
    before = _lines(real.ledger)
    assert phase41_erasure.run() == {"stage": "STAGE 1 DONE", "whole": []}
    assert "STAGE 1 DONE" in capsys.readouterr().out.splitlines()
    assert _lines(real.ledger) == before and not real.heartbeat.exists()
    # The rehearsal identity rule is checked before the first start line.
    fresh = _e1_rig(monkeypatch, tmp_path / "fresh")
    with pytest.raises(SystemExit, match="rehearsal_identity"):
        phase41_erasure.run(**fresh.kw)
    assert not fresh.ledger.exists()


def test_crash_between_the_record_and_the_end_line_is_never_reconciled(monkeypatch, tmp_path):
    import phase36_ledger

    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path))
    prep = phase41_prereg.PREP_UNITS
    append = phase36_ledger.append

    def crash_at_end(event, **kw):
        if event == "end":
            raise RuntimeError("planted crash before the end line")
        return append(event, **kw)

    monkeypatch.setattr(phase36_ledger, "append", crash_at_end)
    with pytest.raises(RuntimeError, match="planted crash"):
        _run(rig, units=prep[:1])
    _threads_stopped(rig)
    assert (rig.root / phase41_prereg.unit_record(prep[0])).exists()
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert [x["event"] for x in lines] == ["start"]
    monkeypatch.setattr(phase36_ledger, "append", append)
    with pytest.raises(SystemExit, match="NEVER reconcile"):
        phase41_erasure.preflight(**rig.kw)
    assert phase36_ledger.read_ledger(rig.ledger) == lines


# =================================================================================================
# (8) Plan 41-09: run_cell — the grid loop, the K = 16 records, the K = 48 confirmations, the stop
# proved against Phase 35's e1_stop, D-13 at the pet_name stop (D-20), the cell record.
# =================================================================================================

_GRID = phase41_prereg.E1_CHECKPOINT_GRID["checkpoints"]
_READ_K = phase41_prereg.E1_CHECKPOINT_GRID["read_k"]


def _a2_reads():
    """The committed Phase 40 full A2 draws of seed 1337 cut to read_k completions (every target
    answers some of its questions there), loaded once."""
    if not hasattr(_a2_reads, "draws"):
        record = _json(_ROOT / "results" / "phase40_a2_full_seed1337.json")
        _a2_reads.draws = [
            {**d, "completions": d["completions"][:_READ_K], "stopped": d["stopped"][:_READ_K]}
            for d in record["draws"]
        ]
    return _a2_reads.draws


def _k16_draws(target, zero):
    """A K = read_k read; ``zero`` blanks the target's completions so its pooled count is 0."""
    draws = _a2_reads()
    if zero:
        return [{**d, "completions": [""] * _READ_K} if d["slot"] == target else d for d in draws]
    return draws


def _cell_fakes(monkeypatch, rig, script, *, d13=None, crash_at=None):
    """The model load, the pin's ablation, load_adapter_weights, the cell ordering, the K = 16 read,
    the K = 48 confirmation, the M1 export and D-13 faked behind their real signatures. ``script``
    maps each checkpoint to ``(k16_zero, k48_zero or None, rank)``; the read fake asserts the
    ordering file exists and reads the checkpoint from the weights loaded just before it."""
    import phase14_recall
    import phase19_erasure

    from personacore import lora

    d = phase41_erasure
    index = tuple(phase19_erasure.component_index())
    log = rig.cell_log = []
    rig.index = index

    def load(device, adapter_path=None):
        log.append(("load", pathlib.Path(adapter_path).name, device))
        return "model", "cfg", "tok", "forbid", {"ablated": []}

    def ablate(adapter, components):
        return {"ablated": [tuple(c) for c in components]}

    def weights(model, artifact):
        log.append(("weights", tuple(artifact["ablated"])))

    def ordering(model, tok, device, forbid, artifact, *, target, ordering, variant, unit, root):
        assert artifact == {"ablated": []}  # the snapshot, never an ablated adapter
        log.append(("ordering", unit, ordering, variant))
        rig.unit = unit
        if ordering == "greedy":
            return {"ordered": index, "k": 3, "stopped": True, "curve": [{"k": 1, "rank": 1}]}
        return {
            "ordered": index[::-1],
            "rankings": [{"at": 0, "scores": [], "d02": None}],
            "rerank_at": (0,),
            "seconds": 1.0,
            "variant": variant,
        }

    def read(model, tok, device, forbid, *, target):
        assert phase41_erasure._ordering_path(rig.root, rig.unit).exists()
        loaded = next(e[1] for e in reversed(log) if e[0] == "weights")
        c = len(loaded)
        if crash_at == c:
            raise RuntimeError(f"planted crash at checkpoint {c}")
        k16_zero, _k48, rank = script[c]
        log.append(("k16", c))
        return {
            "draws": _k16_draws(target, k16_zero),
            "k": _READ_K,
            "exposure": {"rank": rank, "at": c},
        }

    def confirm(target, ordering, seed, checkpoint, components, *, root, device):
        log.append(("k48", checkpoint, tuple(components)))
        rel = phase41_prereg.k48_record(target, ordering, seed, checkpoint)
        path = _plant(pathlib.Path(root) / rel, f"k48 {checkpoint}".encode())
        return {
            "record": rel,
            "record_sha256": d._sha256(path),
            "target_zero": script[checkpoint][1],
        }

    def export(artifact, components, path):
        log.append(("m1", len(components), pathlib.Path(path).name))
        path = _plant(path, b"m1")
        return {"path": path, "sha256": d._sha256(path)}

    def scored(m1_path, k48_record_path, device, state):
        log.append(("d13", pathlib.Path(m1_path).name, pathlib.Path(k48_record_path).name))
        return d13 if d13 is not None else {"measured": True, "planted": "d13"}

    monkeypatch.setattr(
        phase14_recall, "load_adapted_model", _checked(phase14_recall.load_adapted_model, load)
    )
    monkeypatch.setattr(
        phase19_erasure, "ablate_components", _checked(phase19_erasure.ablate_components, ablate)
    )
    monkeypatch.setattr(lora, "load_adapter_weights", _checked(lora.load_adapter_weights, weights))
    for name, fake in (
        ("cell_ordering", ordering),
        ("k16_read", read),
        ("k48_confirm", confirm),
        ("export_m1", export),
        ("d13_at_stop", scored),
    ):
        monkeypatch.setattr(d, name, _checked(getattr(d, name), fake))
    return rig


def _plant_variant(root, variant="adaptive"):
    _plant(phase41_erasure._variant_path(root), json.dumps({"variant": variant}).encode())


def _cell(rig, unit):
    return phase41_erasure.run_cell(unit, root=rig.root, device="cpu", state={})


def _reads(blob):
    return [(r["checkpoint"], r["k16_zero"], r["k48_zero"]) for r in blob["reads"]]


_NEVER_ZERO = {c: (False, None, 5) for c in _GRID}
_NEVER_CONFIRMED = {c: (True, False, 5) for c in _GRID}


@pytest.mark.parametrize(
    ("script", "stop", "n_reads", "n_confirmations"),
    [
        ({_GRID[0]: (True, True, 5)}, _GRID[0], 1, 1),
        (
            {_GRID[0]: (False, None, 5), _GRID[1]: (True, False, 5), _GRID[2]: (True, True, 5)},
            _GRID[2],
            3,
            2,
        ),
        (_NEVER_CONFIRMED, "NOT_REACHED", len(_GRID), len(_GRID)),
        (_NEVER_ZERO, "NOT_REACHED", len(_GRID), 0),
    ],
    ids=["zero_at_first", "confirmed_after_a_failed_one", "never_confirmed", "never_zero"],
)
def test_cell_loop_matches_e1_stop(monkeypatch, tmp_path, script, stop, n_reads, n_confirmations):
    import phase35_prereg

    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), script)
    unit = phase41_prereg.cell_unit("street", "greedy", 1337)
    blob = _cell(rig, unit)
    reads = _reads(blob)
    assert [c for c, *_ in reads] == list(_GRID[:n_reads])
    assert [e[1] for e in rig.cell_log if e[0] == "k16"] == list(_GRID[:n_reads])
    k48 = [e for e in rig.cell_log if e[0] == "k48"]
    assert len(k48) == len(blob["confirmations"]) == n_confirmations
    # A confirmation runs exactly when the K = read_k target count is 0, at that prefix.
    assert [e[1] for e in k48] == [c for c, zero, _ in reads if zero]
    assert all(e[2] == rig.index[: e[1]] for e in k48)
    assert blob["stop"] == stop == phase41_prereg.driver_stop(reads)
    e1 = phase35_prereg.e1_stop(
        grid=phase41_prereg.E1_CHECKPOINT_GRID, readings=phase41_prereg.stop_readings(reads)
    )
    assert blob["e1_stop"] == dict(e1) and e1["stop"] == stop
    assert blob["judged"] is (stop != phase35_prereg.NOT_REACHED)
    assert phase41_prereg.confirmation_failures(blob["confirmations"], reads) == []
    assert (blob["unit"], blob["target"], blob["ordering"], blob["seed"]) == (
        unit,
        "street",
        "greedy",
        1337,
    )
    assert blob["adapter"] == rig.adapters["1337"]["full"]
    assert blob["variant"] is None
    assert [e for e in rig.cell_log if e[0] == "load"] == [
        ("load", pathlib.Path(rig.adapters["1337"]["full"]["path"]).name, "cpu")
    ]


def test_rank_recorded_at_every_read_checkpoint(monkeypatch, tmp_path):
    ranks = {c: (False, None, i + 1) for i, c in enumerate(_GRID)}
    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), ranks)
    blob = _cell(rig, phase41_prereg.cell_unit("street", "greedy", 1337))
    assert blob["stop"] == "NOT_REACHED"
    assert [r["rank"] for r in blob["reads"]] == [ranks[c][2] for c in _GRID]
    # A rank of 1 at a confirmed zero still stops: the rank never enters the stop.
    rig = _cell_fakes(monkeypatch, rig, {_GRID[0]: (True, True, 1)})
    blob = _cell(rig, phase41_prereg.cell_unit("street", "greedy", 2024))
    assert blob["stop"] == _GRID[0] and blob["reads"][0]["rank"] == 1


def test_not_reached_record(monkeypatch, tmp_path):
    import phase35_prereg

    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), _NEVER_CONFIRMED)
    blob = _cell(rig, phase41_prereg.cell_unit("pet_name", "greedy", 1337))
    assert blob["stop"] == phase35_prereg.NOT_REACHED and blob["judged"] is False
    assert blob["not_reached_sentence"] == phase41_prereg.not_reached_sentence()
    assert [r["checkpoint"] for r in blob["reads"]] == list(_GRID)
    for row in blob["reads"]:
        assert row["target_count"] == [0, 27] and row["k16_zero"] is True
    # Never PASS or FAIL: no M1 export, no D-13 on a NOT_REACHED pet_name cell.
    assert blob["d13"] is None and blob["m1"] is None
    assert not [e for e in rig.cell_log if e[0] in ("m1", "d13")]
    judged = _cell_fakes(monkeypatch, rig, {_GRID[0]: (True, True, 5)})
    assert (
        _cell(judged, phase41_prereg.cell_unit("street", "greedy", 1337))["not_reached_sentence"]
        is None
    )


def test_confirmations_recorded_with_hours(monkeypatch, tmp_path):
    script = {**_NEVER_CONFIRMED, _GRID[3]: (True, True, 5)}
    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), script)
    unit = phase41_prereg.cell_unit("cat_name", "greedy", 2024)
    blob = _cell(rig, unit)
    assert blob["stop"] == _GRID[3] and len(blob["confirmations"]) == 4
    for item, row in zip(blob["confirmations"], blob["reads"]):
        assert set(item) == set(phase41_prereg.CONFIRMATION_KEYS)
        assert item["checkpoint"] == row["checkpoint"]
        assert (
            item["record"]
            == row["k48_record"]
            == phase41_prereg.k48_record("cat_name", "greedy", 2024, item["checkpoint"])
        )
        assert row["k48_sha256"] == phase41_erasure._sha256(rig.root / item["record"])
        assert item["started_utc"] <= item["finished_utc"]
        assert isinstance(item["seconds"], float) and item["seconds"] >= 0
    assert phase41_prereg.confirmation_failures(blob["confirmations"], _reads(blob)) == []
    assert blob["confirmation_hours"] == phase41_prereg.confirmation_hours(blob["confirmations"])


@pytest.mark.parametrize("ordering", phase41_prereg.ORDERINGS)
def test_ordering_written_before_any_read(monkeypatch, tmp_path, ordering):
    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), _NEVER_ZERO)
    _plant_variant(rig.root, "static")
    unit = phase41_prereg.cell_unit("street", ordering, 1337)
    blob = _cell(rig, unit)  # the read fake asserts the file exists at every read
    written = _json(phase41_erasure._ordering_path(rig.root, unit))
    assert written["ordering"] == blob["applied_ordering"]
    assert written["unit"] == unit and written["variant"] == blob["variant"]
    expected = rig.index if ordering == "greedy" else rig.index[::-1]
    assert blob["applied_ordering"]["ordered"] == [list(a) for a in expected]
    assert blob["variant"] == (None if ordering == "greedy" else "static")
    assert isinstance(blob["ordering_seconds"], float) and blob["ordering_seconds"] >= 0
    assert [e[3] for e in rig.cell_log if e[0] == "ordering"] == [blob["variant"]]
    # Every read loads ordering[:c] of THAT ordering, never another prefix.
    loads = [e[1] for e in rig.cell_log if e[0] == "weights"]
    assert loads == [expected[:c] for c in _GRID]


def test_k16_records_are_write_once_and_named(monkeypatch, tmp_path):
    script = {_GRID[0]: (False, None, 4), _GRID[1]: (True, True, 2)}
    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), script)
    unit = phase41_prereg.cell_unit("sibling_name", "greedy", 1337)
    blob = _cell(rig, unit)
    for c, row in zip(_GRID, blob["reads"]):
        rel = phase41_prereg.k16_record("sibling_name", "greedy", 1337, c)
        record = _json(rig.root / rel)
        assert row["k16_record"] == rel
        assert row["k16_sha256"] == phase41_erasure._sha256(rig.root / rel)
        assert record["unit"] == unit and record["checkpoint"] == c
        assert record["k"] == _READ_K and record["device"] == "cpu"
        assert record["components"] == [list(a) for a in rig.index[:c]]
        assert record["exposure"] == {"rank": script[c][2], "at": c}
        draws = _k16_draws("sibling_name", script[c][0])
        assert record["draws"] == draws
        counts = phase41_prereg.k16_slot_counts(draws)
        assert record["slot_counts"] == counts and len(counts) == 8
        assert record["target_count"] == list(
            phase41_prereg.k16_target_count(draws, "sibling_name")
        )
        assert row["target_count"] == record["target_count"]
        assert all(v["n_questions"] == 27 for v in counts.values())
    assert not (
        rig.root / phase41_prereg.k16_record("sibling_name", "greedy", 1337, _GRID[2])
    ).exists()
    # An existing K = 16 record refuses: write-once.
    other = phase41_prereg.cell_unit("sibling_name", "greedy", 2024)
    _plant(rig.root / phase41_prereg.k16_record("sibling_name", "greedy", 2024, _GRID[0]))
    with pytest.raises(SystemExit, match="write-once"):
        _cell(rig, other)


def test_pet_name_stop_scores_d13_and_keeps_the_cell_whole(monkeypatch, tmp_path):
    import phase40_prereg

    script = {_GRID[0]: (False, None, 3), _GRID[1]: (True, True, 2)}
    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path), script)
    unit = phase41_prereg.cell_unit("pet_name", "greedy", 1337)
    blob = _cell(rig, unit)
    stop = _GRID[1]
    k48 = phase41_prereg.k48_record("pet_name", "greedy", 1337, stop)
    m1 = f"{unit}_k{stop:03d}_adapter.pt"
    assert [e for e in rig.cell_log if e[0] in ("m1", "d13")] == [
        ("m1", stop, m1),
        ("d13", m1, pathlib.Path(k48).name),
    ]
    path = rig.root / "data" / phase41_erasure.WORK_DIR / "m1" / m1
    assert blob["m1"] == {
        "path": path.relative_to(rig.root).as_posix(),
        "sha256": phase41_erasure._sha256(path),
    }
    assert blob["d13"] == {"measured": True, "planted": "d13"}
    # A D-13 not measured is recorded and the cell stays whole.
    missed = {**phase40_prereg.d13_not_measured("exception", "RuntimeError: boom"), "n_nlls": None}
    rig = _cell_fakes(monkeypatch, rig, script, d13=missed)
    blob = _cell(rig, phase41_prereg.cell_unit("pet_name", "greedy", 2024))
    assert blob["stop"] == stop and blob["d13"] == missed and blob["d13"]["measured"] is False
    # A non-pet_name cell never exports M1 nor scores D-13.
    rig = _cell_fakes(monkeypatch, rig, script)
    blob = _cell(rig, phase41_prereg.cell_unit("street", "greedy", 1337))
    assert blob["stop"] == stop and blob["d13"] is None and blob["m1"] is None
    assert not [e for e in rig.cell_log if e[0] in ("m1", "d13")]


def _stage2_rig(monkeypatch, tmp_path, script, *, crash_at=None, **kw):
    """A rig whose four prep units are whole and whose variant is fixed: preflight is at stage 2."""
    rig = _cell_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path, **kw), script, crash_at=crash_at)
    ledger = rig.ledger if rig.identity is not None else None
    _whole(ledger, *phase41_prereg.PREP_UNITS)
    _plant_variant(rig.root)
    return rig


def test_run_stage2_writes_one_cell_record_per_attempt(monkeypatch, tmp_path, capsys):
    import phase36_ledger
    import torch

    rig = _stage2_rig(monkeypatch, tmp_path, {_GRID[0]: (True, True, 5)})
    cells = phase41_prereg.CELL_UNITS[:3]
    before = _lines(rig.ledger)
    assert _run(rig, units=cells) == {"stage": 2, "whole": list(cells)}
    lines = phase36_ledger.read_ledger(rig.ledger)[len(before) :]
    assert [(x["event"], x["run_id"], x["record"]) for x in lines] == [
        (event, phase41_prereg.run_id(unit), record)
        for unit in cells
        for event, record in (("start", None), ("end", phase41_prereg.unit_record(unit)))
    ]
    for unit in cells:
        _, t, o, s = phase41_prereg.unit_key(unit)
        record = _json(rig.root / phase41_prereg.cell_record(t, o, s))
        assert record["front"] == "E1" and record["run_id"] == phase41_prereg.run_id(unit)
        assert (record["unit"], record["stop"], record["judged"]) == (unit, _GRID[0], True)
        assert record["rehearsal"] is True
        assert record["rehearsal_disclosure"] == {"this_is_the_rehearsal": True}
        run = record["provenance"]["run"]
        assert set(run) == set(phase41_erasure.RUN_PROVENANCE_KEYS)
        assert run["device"] == "cpu" and run["torch_version"] == torch.__version__
        assert record["provenance"]["module_sha256_at_launch"] == phase41_erasure.module_sha256()
        assert (record["d13"] is None) is (t != "pet_name")
    assert _json(rig.identity)["units"] == list(cells)
    out = capsys.readouterr().out.splitlines()
    assert f"RUN DONE whole={list(cells)}" in out and "STAGE 1 DONE" not in out


def test_run_stage2_on_the_real_root(monkeypatch, tmp_path):
    rig = _stage2_rig(monkeypatch, tmp_path, {_GRID[0]: (True, True, 5)}, real=True)
    monkeypatch.setattr(phase41_erasure, "_tracked_and_clean", lambda *rels: True)
    cell = phase41_prereg.CELL_UNITS[0]
    assert phase41_erasure.run(units=(cell,)) == {"stage": 2, "whole": [cell]}
    _, t, o, s = phase41_prereg.unit_key(cell)
    record = _json(rig.root / phase41_prereg.cell_record(t, o, s))
    assert record["provenance"]["run"]["device"] == "mps" and record["rehearsal"] is False
    assert record["rehearsal_disclosure"]["commits"] == []
    assert ("load", pathlib.Path(rig.adapters[str(s)]["full"]["path"]).name, "mps") in rig.cell_log


# =================================================================================================
# (9) Plan 41-09: the D-23 pause and resume, R-3 b per unit (drop_attempt, declare_relaunch,
# rerun_units), the crash between a record and its end line, no deletion in the driver.
# =================================================================================================


def _spent(monkeypatch, rig, *, bump):
    """phase36_ledger.spent behind its real signature, asserting no attempt is open at each call
    and counting the calls; ``bump`` adds E1's share to the E1 seconds (the pause is due)."""
    import math

    import phase36_ledger

    real = phase36_ledger.spent
    share = phase41_prereg.ENTRIES["e1_share_hours"]["value"] * 3600 if bump else 0.0
    rig.spent_calls = 0

    def recorded(tracked=None, *, ledger_path=None, fronts=None):
        lines = phase36_ledger.read_ledger(ledger_path)
        assert not phase36_ledger.open_runs(lines), "spent called while an attempt is open"
        rig.spent_calls += 1
        out = real(tracked, ledger_path=ledger_path, fronts=fronts)
        by_front = {**out["by_front"], "E1": out["by_front"]["E1"] + share}
        return {**out, "by_front": by_front, "total_seconds": math.fsum(by_front.values())}

    monkeypatch.setattr(phase36_ledger, "spent", _checked(real, recorded))


def _pauses(rig):
    return sorted((rig.root / "data" / phase41_erasure.WORK_DIR).glob("pause_*.json"))


def test_pause_before_a_cell_writes_no_start_line(monkeypatch, tmp_path, capsys):
    import phase36_ledger

    rig = _stage2_rig(monkeypatch, tmp_path, {_GRID[0]: (True, True, 5)})
    _spent(monkeypatch, rig, bump=True)
    cells = phase41_prereg.CELL_UNITS
    before = _lines(rig.ledger)
    assert _run(rig) == {"stage": 2, "whole": [], "paused": cells[0]}
    assert _lines(rig.ledger) == before and not rig.heartbeat.exists()
    assert not [e for e in rig.cell_log if e[0] == "ordering"]
    (path,) = _pauses(rig)
    totals = phase36_ledger.spent(ledger_path=rig.ledger)
    expected = phase41_prereg.pause_notice(
        by_front_seconds=totals["by_front"],
        total_seconds=totals["total_seconds"],
        outcomes=phase41_prereg.unit_outcomes(
            phase36_ledger.read_ledger(rig.ledger), phase41_prereg.UNITS
        ),
    )
    notice = _json(path)
    assert notice == {**json.loads(json.dumps(expected)), "next_cell": cells[0]}
    out = capsys.readouterr().out.splitlines()
    assert any(
        line.startswith(f"PAUSE e1_h={notice['e1_hours']:.4f} next={cells[0]}") for line in out
    )
    # Rafael's resume declaration naming the next two cells lets exactly those two run.
    phase41_erasure.declare_resume(
        cells[:2], approved="approved", e1_hours_at_pause=notice["e1_hours"], root=rig.root
    )
    assert _run(rig) == {"stage": 2, "whole": list(cells[:2]), "paused": cells[2]}
    assert len(_pauses(rig)) == 2 and _json(_pauses(rig)[-1])["next_cell"] == cells[2]
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert phase41_prereg.unit_outcomes(lines, cells[:3]) == {
        cells[0]: "whole",
        cells[1]: "whole",
        cells[2]: "not_run",
    }


def test_declare_resume_refuses_without_approved(monkeypatch, tmp_path):
    rig = _stage2_rig(monkeypatch, tmp_path, {_GRID[0]: (True, True, 5)})
    cells = phase41_prereg.CELL_UNITS
    resume = rig.root / phase41_prereg.RESUME_ROOT
    with pytest.raises(SystemExit, match="no pause notice"):
        phase41_erasure.declare_resume(
            cells[:1], approved="approved", e1_hours_at_pause=1.0, root=rig.root
        )
    _spent(monkeypatch, rig, bump=True)
    _run(rig)
    hours = _json(_pauses(rig)[-1])["e1_hours"]
    for change, match in (
        ({"approved": "ok"}, "lacks Rafael's 'approved'"),
        ({"approved": "not approved"}, "lacks Rafael's 'approved'"),
        ({"cells": ("prep_greedy_seed1337",)}, "distinct CELL_UNITS"),
        ({"cells": (cells[0], cells[0])}, "distinct CELL_UNITS"),
        ({"e1_hours_at_pause": hours + 1}, "e1_hours_at_pause"),
    ):
        args = {"cells": cells[:1], "approved": "approved", "e1_hours_at_pause": hours, **change}
        with pytest.raises(SystemExit, match=match):
            phase41_erasure.declare_resume(args.pop("cells"), root=rig.root, **args)
        assert not resume.exists()
    first = phase41_erasure.declare_resume(
        cells[:1], approved="approved", e1_hours_at_pause=hours, root=rig.root
    )
    assert first == {"e1_hours_at_pause": hours, "cells": list(cells[:1]), "approved": "approved"}
    assert _json(rig.root / phase41_prereg.resume_declaration_name(1)) == first
    phase41_erasure.declare_resume(
        cells[1:2], approved="approved", e1_hours_at_pause=hours, root=rig.root
    )
    assert sorted(p.name for p in resume.iterdir()) == [
        pathlib.Path(phase41_prereg.resume_declaration_name(n)).name for n in (1, 2)
    ]


def test_pause_checked_between_attempts_only(monkeypatch, tmp_path):
    rig = _stage2_rig(monkeypatch, tmp_path, {_GRID[0]: (True, True, 5)})
    _spent(monkeypatch, rig, bump=False)
    cells = phase41_prereg.CELL_UNITS[:2]
    assert _run(rig, units=cells) == {"stage": 2, "whole": list(cells)}
    # preflight's require_launch, then per cell the pause check and its require_launch.
    assert rig.spent_calls == 1 + 2 * len(cells)
    assert not _pauses(rig)


def _drop(rig, unit, **kw):
    args = {
        "cause_note": "x",
        "approved": "approved",
        "head_at_dropped_attempt": rig.head,
        "root": rig.root,
        "ledger_path": rig.ledger,
    }
    return phase41_erasure.drop_attempt(unit, **{**args, **kw})


def _lost_utc(rig, unit):
    import phase36_ledger

    return phase41_prereg.lost_attempts(phase36_ledger.read_ledger(rig.ledger), unit)[-1]


def _crashed_cell(monkeypatch, tmp_path):
    """A cell attempt crashed after two K = 16 records and one K = 48 record, reconciled lost; an
    M1 export is planted too (a pet_name stop's)."""
    import phase36_ledger

    script = {_GRID[0]: (False, None, 5), _GRID[1]: (True, False, 5)}
    rig = _stage2_rig(monkeypatch, tmp_path, script, crash_at=_GRID[2])
    cell = phase41_prereg.CELL_UNITS[2]
    with pytest.raises(RuntimeError, match="planted crash"):
        _run(rig, units=(cell,))
    (lost,) = phase36_ledger.reconcile(ledger_path=rig.ledger, heartbeat_path=rig.heartbeat)
    assert (lost["event"], lost["run_id"]) == ("lost", phase41_prereg.run_id(cell))
    _plant(phase41_erasure._m1_path(rig.root, cell, _GRID[1]), b"m1")
    return rig, cell


def test_crash_drop_attempt_moves_and_lists_per_unit(monkeypatch, tmp_path, capsys):
    rig, cell = _crashed_cell(monkeypatch, tmp_path)
    _, t, o, s = phase41_prereg.unit_key(cell)
    planted = [
        rig.root / phase41_prereg.k16_record(t, o, s, _GRID[0]),
        rig.root / phase41_prereg.k16_record(t, o, s, _GRID[1]),
        rig.root / phase41_prereg.k48_record(t, o, s, _GRID[1]),
        phase41_erasure._ordering_path(rig.root, cell),
        phase41_erasure._m1_path(rig.root, cell, _GRID[1]),
    ]
    listed = phase41_erasure.partial_outputs(cell, root=rig.root)
    assert listed == sorted((p.relative_to(rig.root).as_posix(), p) for p in planted)
    digests = {rel: phase41_erasure._sha256(path) for rel, path in listed}
    utc = _lost_utc(rig, cell)
    rel_dir = phase41_prereg.dropped_attempt_dir(cell, utc)
    manifest = _drop(rig, cell)
    assert f"DROPPED {cell} {rel_dir} kept={len(listed)}" in capsys.readouterr().out
    assert tuple(manifest) == phase41_prereg.DROPPED_MANIFEST_KEYS
    assert manifest["kept"] == [
        {"from": rel, "path": f"{rel_dir}/{rel}", "sha256": digests[rel]} for rel, _ in listed
    ]
    for item in manifest["kept"]:  # moved, never deleted
        assert phase41_erasure._sha256(rig.root / item["path"]) == item["sha256"]
        assert not (rig.root / item["from"]).exists()
    assert phase41_erasure.partial_outputs(cell, root=rig.root) == []
    assert _json(rig.root / rel_dir / phase41_prereg.DROPPED_MANIFEST) == manifest
    assert phase41_prereg.dropped_manifest_failures(manifest, unit=cell, lost_utc=utc) == []
    with pytest.raises(SystemExit, match="write-once"):
        _drop(rig, cell)

    # The seed's FIRST prep unit (its training unit) owns the calibration adapter outputs.
    rig = _e1_rig(monkeypatch, tmp_path / "prep")
    unit = phase41_prereg.PREP_UNITS[0]
    _, o, s = phase41_prereg.unit_key(unit)
    _ledger(rig.ledger, ("start", unit), ("lost", unit))
    arm = phase41_erasure.arm_paths(s, rehearsal=True)
    work = rig.root / "data" / phase41_erasure.WORK_DIR
    record = rig.root / phase41_prereg.calibration_record(o, s)
    planted = [
        rig.root / phase41_prereg.band_record(s, o),
        work / f"cal_erased_{o}_seed{s}.json",
        *(arm[k] for k in ("adapter", "checkpoint", "bin", "mask", "csv")),
        work / phase41_erasure.arm_name(s, rehearsal=True) / "run.csv",
        record.parent / f".{record.name}.abc123.tmp",
    ]
    for path in planted:
        _plant(path, str(path).encode())
    listed = phase41_erasure.partial_outputs(unit, root=rig.root)
    assert listed == sorted((p.relative_to(rig.root).as_posix(), p) for p in planted)
    manifest = _drop(rig, unit)
    assert sorted(i["from"] for i in manifest["kept"]) == [rel for rel, _ in listed]
    assert all(not p.exists() for p in planted)
    assert all((rig.root / i["path"]).is_file() for i in manifest["kept"])


def test_drop_second_prep_unit_keeps_the_seed_adapter(monkeypatch, tmp_path):
    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path))
    prep = phase41_prereg.PREP_UNITS
    _run(rig, units=prep[:1])
    _ledger(rig.ledger, ("start", prep[1]), ("lost", prep[1]))
    _, o, s = phase41_prereg.unit_key(prep[1])
    work = rig.root / "data" / phase41_erasure.WORK_DIR
    planted = [
        _plant(rig.root / phase41_prereg.band_record(s, o)),
        _plant(work / f"cal_erased_{o}_seed{s}.json"),
    ]
    arm = phase41_erasure.arm_paths(s, rehearsal=True)
    seed_files = [arm[k] for k in ("adapter", "checkpoint", "bin", "mask")]
    seed_files.append(work / phase41_erasure.arm_name(s, rehearsal=True) / "run.csv")
    digests = {p: phase41_erasure._sha256(p) for p in seed_files}
    manifest = _drop(rig, prep[1])
    assert sorted(i["from"] for i in manifest["kept"]) == sorted(
        p.relative_to(rig.root).as_posix() for p in planted
    )
    assert {p: phase41_erasure._sha256(p) for p in seed_files} == digests
    cited = _json(rig.root / phase41_prereg.unit_record(prep[0]))["adapter"]["sha256"]
    assert cited == digests[arm["adapter"]]
    # The re-run digest-checks the same adapter against the first unit's record: no training.
    rig.log.clear()
    rig.trained.clear()
    assert _run(rig, units=prep[1:2])["whole"] == [prep[1]]
    assert not [e for e in rig.log if e[0] == "train"] and rig.trained == []
    record = _json(rig.root / phase41_prereg.unit_record(prep[1]))
    assert record["adapter"]["sha256"] == cited
    (attempt,) = record["dropped_attempts"]
    assert attempt["lost_utc"] == _lost_utc(rig, prep[1])
    assert attempt["adapter_identity"] == phase41_erasure.NOT_PRODUCED


def test_drop_attempt_refusals(monkeypatch, tmp_path):
    rig, cell = _crashed_cell(monkeypatch, tmp_path)
    listed = phase41_erasure.partial_outputs(cell, root=rig.root)
    dropped_root = rig.root / phase41_prereg.DROPPED_ROOT
    ledger = _lines(rig.ledger)

    def refused(match, unit=cell, **kw):
        with pytest.raises(SystemExit, match=match):
            _drop(rig, unit, **kw)
        assert phase41_erasure.partial_outputs(cell, root=rig.root) == listed
        assert not dropped_root.exists()
        assert _lines(rig.ledger) == ledger

    refused("only a crashed attempt", unit=phase41_prereg.PREP_UNITS[0])  # whole
    refused("only a crashed attempt", unit=phase41_prereg.CELL_UNITS[5])  # not run
    still_open = tmp_path / "open.jsonl"
    _ledger(still_open, ("start", cell), ("lost", cell), ("start", cell))
    refused("reconcile first", ledger_path=still_open)
    record = _plant(rig.root / phase41_prereg.unit_record(cell))
    refused("crash rule [(]i[)]")
    record.unlink()
    monkeypatch.setattr(phase41_erasure, "git_sha", lambda: "unknown")
    refused("could not read HEAD")
    monkeypatch.setattr(phase41_erasure, "git_sha", lambda: "h1")
    refused("cause_note is empty", cause_note=" ")
    refused("lacks Rafael's 'approved'", approved="ok")
    refused("lacks Rafael's 'approved'", approved="not approved")
    refused("head_change_declared None: HEAD h0 -> h1", head_at_dropped_attempt="h0")
    _drop(rig, cell)
    rel_dir = rig.root / phase41_prereg.dropped_attempt_dir(cell, _lost_utc(rig, cell))
    args = {
        "head_change_declared": "y",
        "approved": "approved",
        "root": rig.root,
        "ledger_path": rig.ledger,
    }

    def declarations():
        return sorted(p.name for p in rel_dir.glob(phase41_prereg.relaunch_declaration_name("*")))

    with pytest.raises(SystemExit, match="drop-time HEAD"):  # the HEAD did not move
        phase41_erasure.declare_relaunch(cell, **args)
    monkeypatch.setattr(phase41_erasure, "git_sha", lambda: "h2")
    for change in ({"approved": "ok"}, {"approved": "not approved"}):
        with pytest.raises(SystemExit, match="lacks Rafael's 'approved'"):
            phase41_erasure.declare_relaunch(cell, **{**args, **change})
    with pytest.raises(SystemExit, match="only a crashed attempt"):
        phase41_erasure.declare_relaunch(phase41_prereg.PREP_UNITS[0], **args)
    assert declarations() == []
    declaration = phase41_erasure.declare_relaunch(cell, **args)
    assert declaration == {
        "launch_git_sha": "h2",
        "head_change_declared": "y",
        "approved": "approved",
    }
    assert declarations() == [phase41_prereg.relaunch_declaration_name("h2")]


def test_rerun_needs_the_manifest_and_compares_attempts(monkeypatch, tmp_path):
    import phase36_ledger
    import phase40_noise

    rig, cell = _crashed_cell(monkeypatch, tmp_path)

    def rerun():
        lines = phase36_ledger.read_ledger(rig.ledger)
        outcomes = phase41_prereg.unit_outcomes(lines, phase41_prereg.UNITS)
        return phase41_erasure.rerun_units(lines, outcomes, root=rig.root)

    assert rerun() == frozenset()  # no manifest: not re-run, so not pending
    assert cell not in phase41_erasure.preflight(**rig.kw)["pending"]
    manifest = _drop(rig, cell)
    utc = _lost_utc(rig, cell)
    rel_dir = phase41_prereg.dropped_attempt_dir(cell, utc)
    path = rig.root / rel_dir / phase41_prereg.DROPPED_MANIFEST
    assert rerun() == frozenset({cell})
    original = path.read_bytes()
    path.write_text(json.dumps({**manifest, "approved": "ok"}), encoding="utf-8")
    assert rerun() == frozenset()  # a failing manifest is no re-run
    path.write_bytes(original)
    kept = rig.root / manifest["kept"][0]["path"]
    kept_bytes = kept.read_bytes()
    kept.write_bytes(b"changed")
    with pytest.raises(SystemExit, match="sha256"):
        phase41_erasure.preflight(**rig.kw)
    kept.write_bytes(kept_bytes)
    # The re-run of the cell: its record lists the dropped attempt and compares the orderings.
    _cell_fakes(monkeypatch, rig, {_GRID[0]: (True, True, 5)})
    assert _run(rig, units=(cell,)) == {"stage": 2, "whole": [cell]}
    record = _json(rig.root / phase41_prereg.unit_record(cell))
    (attempt,) = record["dropped_attempts"]
    assert attempt["lost_utc"] == utc and attempt["kept"] == manifest["kept"]
    assert attempt["manifest"] == f"{rel_dir}/{phase41_prereg.DROPPED_MANIFEST}"
    assert attempt["manifest_sha256"] == phase41_erasure._sha256(path)
    assert attempt["relaunch_declarations"] == []
    assert attempt["ordering_equal"] is True
    for item in attempt["kept"]:
        assert phase41_erasure._sha256(rig.root / item["path"]) == item["sha256"]

    # A prep unit crashed after training: its re-run trains again and compares the adapters.
    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path / "prep"))
    unit = phase41_prereg.PREP_UNITS[0]
    current = phase41_erasure.calibration_identity
    crash = {"on": True}

    def identity(new_adapter):
        if crash["on"]:
            raise RuntimeError("planted crash after training")
        return current(new_adapter)

    monkeypatch.setattr(phase41_erasure, "calibration_identity", identity)
    with pytest.raises(RuntimeError, match="planted crash"):
        _run(rig, units=(unit,))
    phase36_ledger.reconcile(ledger_path=rig.ledger, heartbeat_path=rig.heartbeat)
    _, o, s = phase41_prereg.unit_key(unit)
    adapter = phase41_erasure.arm_paths(s, rehearsal=True)["adapter"]
    manifest = _drop(rig, unit)
    (item,) = [i for i in manifest["kept"] if i["from"] == adapter.relative_to(rig.root).as_posix()]
    seen = []

    def compared(new_path, committed_path):
        seen.append((pathlib.Path(new_path), pathlib.Path(committed_path)))
        return {"tensors_identical": True, "planted": "identity"}

    monkeypatch.setattr(
        phase40_noise, "adapter_identity", _checked(phase40_noise.adapter_identity, compared)
    )
    crash["on"] = False
    assert _run(rig, units=(unit,))["whole"] == [unit]
    assert [e for e in rig.log if e[0] == "train"]
    assert seen == [(adapter, rig.root / item["path"])]
    (attempt,) = _json(rig.root / phase41_prereg.unit_record(unit))["dropped_attempts"]
    assert attempt["adapter_identity"] == {"tensors_identical": True, "planted": "identity"}


def test_crash_between_record_and_end_line(monkeypatch, tmp_path):
    import phase36_ledger

    rig = _stage2_rig(monkeypatch, tmp_path, {_GRID[0]: (True, True, 5)})
    cell = phase41_prereg.CELL_UNITS[0]
    append = phase36_ledger.append

    def crash_at_end(event, **kw):
        if event == "end":
            raise RuntimeError("planted crash before the end line")
        return append(event, **kw)

    monkeypatch.setattr(phase36_ledger, "append", crash_at_end)
    with pytest.raises(RuntimeError, match="planted crash"):
        _run(rig, units=(cell,))
    assert (rig.root / phase41_prereg.unit_record(cell)).exists()
    lines = phase36_ledger.read_ledger(rig.ledger)
    assert lines[-1]["event"] == "start" and lines[-1]["run_id"] == phase41_prereg.run_id(cell)
    monkeypatch.setattr(phase36_ledger, "append", append)
    with pytest.raises(SystemExit, match="NEVER reconcile"):
        phase41_erasure.preflight(**rig.kw)
    with pytest.raises(SystemExit, match="reconcile first"):
        _drop(rig, cell)
    assert phase36_ledger.read_ledger(rig.ledger) == lines


_DELETERS = ("remove", "unlink", "rmtree", "rmdir", "removedirs")


def _deletion_calls(source):
    """``[(top-level name, call)]`` of every call named like a file deletion."""
    import ast

    found = []
    for top in ast.parse(source).body:
        name = getattr(top, "name", "<module>")
        for node in ast.walk(top):
            if isinstance(node, ast.Call):
                func = node.func
                called = getattr(func, "attr", None) or getattr(func, "id", None)
                if called in _DELETERS:
                    found.append((name, called))
    return found


def test_no_file_deletion_in_the_driver():
    source = (_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8")
    allowed = [("train_calibration_adapter", "rmdir")]  # the emptied csv dir (Phase 40 IN-02)
    assert _deletion_calls(source) == allowed
    planted = source + "\n\ndef planted(path):\n    pathlib.Path(path).unlink()\n"
    assert _deletion_calls(planted) == allowed + [("planted", "unlink")]


# =================================================================================================
# (10) Plan 41-10 Task 1: build_record and emit — verdicts, pair labels, the summary and every
# declared reading from the records the real write paths produce on a tmp root, with ONE real
# committed producer record (results/erasure_kstar_arm_k064.json) as a stop's K = 48 record.
# =================================================================================================

_K064 = _ROOT / "results" / "erasure_kstar_arm_k064.json"
# The checkpoint that record was read at: its own ablated-component count, a GRID checkpoint.
_K064_AT = len(_json(_K064)["config"]["ablated_components"])
assert _K064_AT in _GRID
_CURVE = _ROOT / "results" / "phase19_collateral_curve.json"


def _fills(monkeypatch, root):
    """The two fills, exactly as plan 41-13's floors file will make them, on ``root``'s stage-1
    records: the corpus and the noise floor copied byte for byte, phase35_prereg._REPO_ROOT
    pointed at ``root`` for the two calls only."""
    import shutil

    import phase35_prereg

    for rel in (phase41_prereg.CALIBRATION_CORPUS, phase41_prereg.NOISE_FLOOR_RECORD):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_ROOT / rel, root / rel)
    with monkeypatch.context() as m:
        m.setattr(phase35_prereg, "_REPO_ROOT", root)
        floors = phase35_prereg.fill("e1_condition_a_floors", **phase41_prereg.floors_fill_inputs())
        bands = phase35_prereg.fill(
            "e1_condition_c_band_inputs", **phase41_prereg.band_fill_inputs()
        )
    return floors, bands


def _d13_block(seed):
    """A D-13 block as phase40_noise.d13_scores returns it: the committed Phase 40 one."""
    return _noise_floor()["d13"]["blocks"][str(seed)]


def _producer_rig(monkeypatch, tmp_path, **kw):
    """Stage 1 through run() (the 41-08 write paths, fakes behind the real signatures)."""
    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path, **kw))
    if rig.identity is not None:
        _run(rig)
    else:
        phase41_erasure.run()
    return rig


def _producer_cell(monkeypatch, rig, unit):
    """One judged pet_name cell through run(): the greedy ordering starts with Phase 19's
    ordered_prefix, the K = read_k target count is zero only at _K064_AT, and the REAL k48_confirm
    runs with the pin's arm writing results/erasure_kstar_arm_k064.json's bytes at its
    record_path; D-13 is the committed Phase 40 block."""
    import shutil

    import phase19_erasure

    real_confirm = phase41_erasure.k48_confirm
    _, target, ordering, seed = phase41_prereg.unit_key(unit)
    script = {c: (c == _K064_AT, True if c == _K064_AT else None, 9) for c in _GRID}
    rig = _cell_fakes(monkeypatch, rig, script, d13=_d13_block(seed))
    prefix = [tuple(a) for a in _json(_CURVE)["ordered_prefix"]]
    ordered = tuple(prefix) + tuple(a for a in rig.index if a not in set(prefix))

    def cell_ordering(
        model, tok, device, forbid, artifact, *, target, ordering, variant, unit, root
    ):
        rig.unit = unit
        return {"ordered": ordered, "k": len(prefix), "stopped": True, "curve": []}

    def arm(name, device, **kw):
        assert name == "erased" and len(kw["components"]) == _K064_AT
        shutil.copyfile(_K064, kw["record_path"])

    d = phase41_erasure
    monkeypatch.setattr(d, "cell_ordering", _checked(d.cell_ordering, cell_ordering))
    monkeypatch.setattr(d, "k48_confirm", real_confirm)
    monkeypatch.setattr(
        phase19_erasure, "run_erasure_arm", _checked(phase19_erasure.run_erasure_arm, arm)
    )
    if rig.identity is not None:
        assert _run(rig, units=(unit,))["whole"] == [unit]
    else:
        assert phase41_erasure.run(units=(unit,))["whole"] == [unit]
    k48 = rig.root / phase41_prereg.k48_record(target, ordering, seed, _K064_AT)
    assert k48.read_bytes() == _K064.read_bytes()  # the committed producer record, byte for byte
    return rig


def _roundtrip(value):
    return json.loads(json.dumps(value, default=dict))


def test_emit_fed_a_real_producer_record(monkeypatch, tmp_path):
    import erasure_gate
    import phase37_routes
    import phase40_prereg

    p = phase41_prereg
    rig = _producer_rig(monkeypatch, tmp_path)
    cell = p.cell_unit("pet_name", "greedy", 1337)
    _producer_cell(monkeypatch, rig, cell)
    floors, bands = _fills(monkeypatch, rig.root)
    record = phase41_erasure.emit(root=rig.root, ledger_path=rig.ledger, floors=floors, bands=bands)
    assert record == _json(rig.root / p.ERASURE_RECORD)
    assert record["phase"] == 41 and record["front"] == "E1" and record["status"] == "PARTIAL"
    k064 = _json(_K064)
    rel = p.k48_record("pet_name", "greedy", 1337, _K064_AT)
    assert record["inputs"][rel] == phase41_erasure._sha256(_K064)
    c = record["cells"][cell]
    assert (c["stop"], c["judged"], c["outcome"]) == (_K064_AT, True, "whole")
    post = p.record_rows(k064)
    pre = p.record_rows(_json(_ROOT / phase40_prereg.a2_record("full", 1337)))
    a, b, cc = (c["conditions"][k] for k in ("a", "b", "c"))
    assert a["upper"] == erasure_gate.wilson_upper_bound(0, 27)
    assert a["floor"] == floors[("pet_name", "greedy", 1337)]["floor"] and a["holds"] is True
    assert list(b["slots"]) == list(p.nontarget_slots("pet_name"))
    for slot, row in b["slots"].items():
        assert row["pre"] == [pre[slot]["n_answerable"], 27], slot
        assert row["post"] == [post[slot]["n_answerable"], 27], slot
    assert cc["gap"] == 4.920568428792842 - 4.573349214207799
    assert [cc["lo"], cc["hi"]] == list(bands[(1337, "greedy")])
    expected = p.cell_verdict(
        stop=_K064_AT,
        target_n=0,
        target_q=27,
        zero_results_have_nll=phase37_routes.route_a(k064),
        a=p.condition_a(0, 27, floors[("pet_name", "greedy", 1337)]["floor"]),
        b=p.condition_b(post, pre, "pet_name"),
        c=p.condition_c(k064["dialogue_ppl"], bands[(1337, "greedy")]),
    )
    v = c["verdict"]
    assert v in erasure_gate.VERDICTS and v == expected["verdict"]
    assert (c["failed"], c["beyond"], c["reason"]) == (
        expected["failed"],
        expected["beyond"],
        expected["reason"],
    )
    # Every other cell never started: NOT_RUN.
    others = {u: block["verdict"] for u, block in record["cells"].items() if u != cell}
    assert set(record["cells"]) == set(p.CELL_UNITS)
    assert set(others.values()) == {p.NOT_RUN}
    assert record["table"]["pet_name"]["greedy"] == {"1337": v, "2024": p.NOT_RUN}
    pair = record["pairs"]["pet_name|greedy"]
    assert pair["label"] == "não replicado" and pair["text"] == f"{v} na 1337, NOT_RUN na 2024"
    summary = record["summary"]
    assert summary["n_pairs"] == 8
    assert sum(summary[label] for label in p.PAIR_LABELS) == 8
    assert summary["inside_nao_replicado"] == {f"{v} + NOT_RUN": 1, "NOT_RUN + NOT_RUN": 7}
    # D-27: every checkpoint's K = 16 per-fact counts, read from the K = 16 record it names.
    assert [r["checkpoint"] for r in c["reads"]] == [x for x in _GRID if x <= _K064_AT]
    for read in c["reads"]:
        k16 = _json(rig.root / p.k16_record("pet_name", "greedy", 1337, read["checkpoint"]))
        assert read["slot_counts"] == k16["slot_counts"] and read["rank"] == 9
        assert read["target_count"] == k16["target_count"]
    assert c["confirmation_hours"] == p.confirmation_hours(c["confirmations"])
    # D-18, D-19 / D-28, D-14, D-20.
    noise = _noise_floor()
    m2 = p.record_rows(_json(_ROOT / phase40_prereg.a2_record("m2", 1337)))
    assert c["m1_m2"] == _roundtrip(
        p.m1_m2_rows("pet_name", full_rows=pre, m1_rows=post, m2_rows=m2, noise_floor=noise)
    )
    assert record["labels"]["varies"] == ["birth_year", "hometown"]
    assert c["nontarget_damage"] == _roundtrip(
        p.nontarget_damage(p.condition_b(post, pre, "pet_name"), {"birth_year", "hometown"})
    )
    cap = p.retention_floor_record()[1]["cap"]
    assert c["retention"]["stop"] == k064["retention_ppl"][0] and c["retention"]["cap"] == cap
    assert c["retention"][p.V4_CAP_LABEL] in ("sim", "não")
    assert c["d13"] == _roundtrip(p.d13_comparison(_d13_block(1337), p.d13_ranges(noise)))
    assert record["d21"]["per_cell"]["gradient|1337"] == "not measured"
    assert record["d21"]["prediction_held"] is None
    predictions = record["predictions"]
    assert set(predictions) == set(p.ENTRIES["predictions"]["value"])
    assert predictions["greedy_1337_phase19_prefix"]["held"] is True
    assert record["variant"] == "adaptive" and record["variant_decided_by"] == "cpu_rehearsal"
    assert record["not_reached_sentence"] == p.not_reached_sentence()


def test_not_reached_cell_in_the_record(monkeypatch, tmp_path):
    p = phase41_prereg
    rig = _producer_rig(monkeypatch, tmp_path)
    ranks = {c: (True, False, i + 2) for i, c in enumerate(_GRID)}
    rig = _cell_fakes(monkeypatch, rig, ranks)
    cell = p.cell_unit("street", "greedy", 1337)
    assert _run(rig, units=(cell,))["whole"] == [cell]
    floors, bands = _fills(monkeypatch, rig.root)
    record = phase41_erasure.build_record(
        rig.root, ledger_path=rig.ledger, floors=floors, bands=bands
    )
    c = record["cells"][cell]
    assert (c["verdict"], c["judged"], c["stop"]) == ("NOT_REACHED", False, "NOT_REACHED")
    assert c["conditions"] is None and c["failed"] == [] and c["beyond"] == []
    assert c["not_reached_sentence"] == p.not_reached_sentence()
    assert [r["checkpoint"] for r in c["reads"]] == list(_GRID)
    assert [r["rank"] for r in c["reads"]] == [ranks[x][2] for x in _GRID]
    assert all(r["target_count"] == [0, 27] for r in c["reads"])
    assert all(set(r["slot_counts"]) == set(p.k16_slot_counts(_a2_reads())) for r in c["reads"])
    assert len(c["confirmations"]) == len(_GRID) and c["confirmation_hours"] >= 0
    assert c["m1_m2"] == {"comparison": p.NO_M2} and c["d13"] is None
    assert record["table"]["street"]["greedy"]["1337"] == "NOT_REACHED"
    assert record["pairs"]["street|greedy"]["text"] == "NOT_REACHED na 1337, NOT_RUN na 2024"


def _floors_module(monkeypatch, floors, bands):
    module = types.ModuleType("phase41_floors_prereg")
    module.E1_CONDITION_A_FLOORS, module.E1_CONDITION_C_BAND_INPUTS = floors, bands
    monkeypatch.setitem(sys.modules, "phase41_floors_prereg", module)
    return module


def test_build_record_real_root_defaults_import_the_floors_file(monkeypatch, tmp_path):
    import ast

    rig = _producer_rig(monkeypatch, tmp_path, real=True)
    floors, bands = _fills(monkeypatch, rig.root)
    _floors_module(monkeypatch, floors, bands)
    record = phase41_erasure.build_record(rig.root)
    assert record["calibrations"]["d12"] == _roundtrip(phase41_prereg.d12_rows(floors))
    assert record["status"] == "PARTIAL"
    assert {b["verdict"] for b in record["cells"].values()} == {phase41_prereg.NOT_RUN}
    # A rehearsal root passes its own fills: the floors file is the real root's.
    tmp = _producer_rig(monkeypatch, tmp_path / "tmp")
    with pytest.raises(SystemExit, match="floors and bands"):
        phase41_erasure.build_record(tmp.root, ledger_path=tmp.ledger)
    # The floors file is imported inside build_record only; no module-level name binds a fill.
    tree = ast.parse((_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8"))
    sites = [
        (top.name if isinstance(top, ast.FunctionDef) else "<module>")
        for top in tree.body
        for node in ast.walk(top)
        if isinstance(node, ast.Import)
        and any(a.name == "phase41_floors_prereg" for a in node.names)
    ]
    assert sites == ["build_record"]
    bound = {
        t.id
        for top in tree.body
        if isinstance(top, ast.Assign)
        for t in top.targets
        if isinstance(t, ast.Name)
    }
    assert not bound & {"E1_CONDITION_A_FLOORS", "E1_CONDITION_C_BAND_INPUTS"}


def test_emit_is_write_once_and_refuses_a_dirty_tree(monkeypatch, tmp_path):
    p = phase41_prereg
    rig = _producer_rig(monkeypatch, tmp_path)
    floors, bands = _fills(monkeypatch, rig.root)
    kw = {"root": rig.root, "ledger_path": rig.ledger, "floors": floors, "bands": bands}
    record = phase41_erasure.emit(**kw)
    assert _json(rig.root / p.ERASURE_RECORD) == record
    with pytest.raises(SystemExit, match="write-once"):
        phase41_erasure.emit(**kw)

    real = _producer_rig(monkeypatch, tmp_path / "real", real=True)
    floors, bands = _fills(monkeypatch, real.root)
    _floors_module(monkeypatch, floors, bands)
    out = real.root / p.ERASURE_RECORD
    monkeypatch.setattr(phase41_erasure, "refuse_if_dirty", _raise("planted dirty tree"))
    with pytest.raises(SystemExit, match="planted dirty tree"):
        phase41_erasure.emit()
    assert not out.exists()
    dirty = []
    monkeypatch.setattr(phase41_erasure, "refuse_if_dirty", lambda **k: dirty.append(k))
    # The stage-1 records are untracked in the repository: refused, nothing written.
    with pytest.raises(SystemExit, match="tracked and clean"):
        phase41_erasure.emit()
    assert not out.exists() and dirty and dirty[-1]["cwd"] == phase41_erasure._REPO
    asked = []

    def tracked(*rels):
        asked.append(rels)
        return True

    monkeypatch.setattr(phase41_erasure, "_tracked_and_clean", tracked)
    record = phase41_erasure.emit()
    assert _json(out) == record
    (rels,) = asked
    assert rels[0] == phase41_erasure.FLOORS_FILE
    assert set(rels[1:]) == set(record["inputs"])
    assert set(phase41_erasure._stage1_records()) <= set(rels)


def test_record_has_no_top_level_run_provenance(monkeypatch, tmp_path):
    rig = _producer_rig(monkeypatch, tmp_path)
    floors, bands = _fills(monkeypatch, rig.root)
    record = phase41_erasure.build_record(
        rig.root, ledger_path=rig.ledger, floors=floors, bands=bands
    )
    assert "run" not in record["provenance"]
    assert set(record["provenance"]) == {"emitted_utc", "git_sha", "module_sha256"}
    assert record["provenance"]["module_sha256"] == phase41_erasure.module_sha256()


# =================================================================================================
# (11) Plan 41-10 Task 2: render_report, report, main; the gates that keep the driver honest (AST,
# ERASE-08's byte-unchanged leg, the every-function census, no skips).
# =================================================================================================


def _producer_record(monkeypatch, tmp_path):
    """The Task 1 record: one judged pet_name cell on the real producer record, the rest NOT_RUN."""
    rig = _producer_rig(monkeypatch, tmp_path)
    _producer_cell(monkeypatch, rig, phase41_prereg.cell_unit("pet_name", "greedy", 1337))
    floors, bands = _fills(monkeypatch, rig.root)
    kw = {"ledger_path": rig.ledger, "floors": floors, "bands": bands}
    return rig, phase41_erasure.emit(root=rig.root, **kw)


def test_render_report_has_every_declared_label(monkeypatch, tmp_path):
    p = phase41_prereg
    _, record = _producer_record(monkeypatch, tmp_path)
    text = phase41_erasure.render_report(record)
    assert text == phase41_erasure.render_report(json.loads(json.dumps(record)))  # pure
    assert "\n\n\n" not in text and text.endswith("\n") and not text.endswith("\n\n")
    summary = record["summary"]
    for label in p.PAIR_LABELS:
        assert f"{label} {summary[label]}" in text, label
    for combination, count in summary["inside_nao_replicado"].items():
        assert f"| {combination} | {count} |" in text, combination
    for t in p.TARGETS:
        for o in p.ORDERINGS:
            row = " | ".join(str(record["table"][t][o][str(s)]) for s in p.SEEDS)
            assert f"| {t} | {o} | {row} |" in text, (t, o)
    for label in (
        p.VARIES_LABEL,
        p.INSIDE,
        p.OUTSIDE,
        p.V4_CAP_LABEL,
        p.NO_M2,
        p.not_reached_sentence(),
        "não é teste estatístico",
        "vazia no ponto de parada julgado",
    ):
        assert label in text, label
    cell = record["cells"][p.cell_unit("pet_name", "greedy", 1337)]
    assert f"Verdict **{cell['verdict']}**" in text
    for name in cell["failed"] + cell["beyond"]:
        assert name in text
    assert repr(cell["confirmation_hours"]) in text
    assert repr(record["e1_hours"]) in text
    assert record["end_point"]["record"] in text and record["end_point"]["sha256"] in text
    assert repr(record["calibrations"]["prep_hours"]) in text
    assert record["variant_decided_by"] in text
    for name, prediction in record["predictions"].items():
        assert f"| {name} | {prediction['held']} |" in text, name


def test_report_writes_once_from_a_tracked_record(monkeypatch, tmp_path):
    p = phase41_prereg
    real = _producer_rig(monkeypatch, tmp_path, real=True)
    floors, bands = _fills(monkeypatch, real.root)
    _floors_module(monkeypatch, floors, bands)
    with pytest.raises(SystemExit, match="emit the record first"):
        phase41_erasure.report()
    with monkeypatch.context() as m:
        m.setattr(phase41_erasure, "_tracked_and_clean", lambda *rels: True)
        record = phase41_erasure.emit()
    # The real root renders only a tracked, unmodified record: this one is untracked.
    with pytest.raises(SystemExit, match="committed and unmodified"):
        phase41_erasure.report()
    out = real.root / p.REPORT_RECORD
    assert not out.exists()
    asked = []
    monkeypatch.setattr(
        phase41_erasure, "_tracked_and_clean", lambda *rels: asked.append(rels) or True
    )
    assert phase41_erasure.report() == out
    assert asked == [(p.ERASURE_RECORD,)]
    assert out.read_text(encoding="utf-8") == phase41_erasure.render_report(record)
    with pytest.raises(SystemExit, match=r"write-once.*scripts/_addendum\.py"):
        phase41_erasure.report()


@pytest.mark.parametrize("command", ["preflight", "run", "emit", "report"])
def test_main_dispatches_with_no_arguments_from_the_repo(tmp_path, monkeypatch, command):
    import inspect

    real = getattr(phase41_erasure, command)
    seen = []

    def recorder(*args, **kwargs):
        inspect.signature(real).bind(*args, **kwargs)
        seen.append((args, kwargs, pathlib.Path.cwd()))

    monkeypatch.setattr(phase41_erasure, command, recorder)
    monkeypatch.chdir(tmp_path)
    assert phase41_erasure.main([command]) == 0
    assert seen == [((), {}, phase41_erasure._REPO)]


@pytest.mark.parametrize("argv", [[], ["bogus"], ["run", "x"]])
def test_main_refuses_anything_else(argv):
    with pytest.raises(SystemExit) as raised:
        phase41_erasure.main(argv)
    assert raised.value.code == phase41_erasure.__doc__


def test_main_the_cli_exits_non_zero_on_a_bogus_command():
    done = subprocess.run(
        [sys.executable, "scripts/phase41_erasure.py", "bogus"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert done.returncode != 0
    assert "phase41_erasure.py emit" in done.stderr


def test_the_full_fake_chain_through_the_commands(monkeypatch, tmp_path):
    import inspect

    p = phase41_prereg
    rig = _cell_fakes(
        monkeypatch, _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path)), _NEVER_ZERO
    )

    def command(name, **kw):
        real = getattr(phase41_erasure, name)
        bound = inspect.signature(real).bind(**kw)
        return real(*bound.args, **bound.kwargs)

    run_kw = {**rig.kw, "rehearsal_identity": rig.identity}
    assert command("preflight", **rig.kw)["stage"] == 1
    assert command("run", **run_kw) == {"stage": 1, "whole": list(p.PREP_UNITS)}
    assert command("preflight", **rig.kw)["pending"] == p.CELL_UNITS
    assert command("run", **run_kw) == {"stage": 2, "whole": list(p.CELL_UNITS)}
    floors, bands = _fills(monkeypatch, rig.root)
    record = command("emit", root=rig.root, ledger_path=rig.ledger, floors=floors, bands=bands)
    out = command("report", root=rig.root)
    assert record["status"] == "COMPLETE"
    assert {c["verdict"] for c in record["cells"].values()} == {"NOT_REACHED"}
    assert record["summary"]["inside_nao_replicado"] == {"NOT_REACHED + NOT_REACHED": 8}
    assert out.read_text(encoding="utf-8") == phase41_erasure.render_report(record)
    assert _json(rig.identity)["units"] == list(p.UNITS)


def test_phase41_call_gate(monkeypatch, tmp_path):
    import test_phase37_routes

    allowed = {"draw_all", "reference_set_for_calibration", "write_text"}
    assert allowed < test_phase37_routes._FORBIDDEN_CALLEES  # non-vacuity: each was forbidden
    monkeypatch.setattr(
        test_phase37_routes,
        "_FORBIDDEN_CALLEES",
        test_phase37_routes._FORBIDDEN_CALLEES - allowed,
    )
    paths = sorted(_SCRIPTS.glob("phase41_*.py"))
    assert _SCRIPTS / "phase41_erasure.py" in paths
    for path in paths:
        assert test_phase37_routes._call_failures(path.read_text(encoding="utf-8")) == [], path
    source = (_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8")
    for plant in (
        "\n\ndef planted(rec):\n    return erasure_gate.erasure_succeeded(rec)\n",
        "\n\ndef planted():\n    import phase19_erasure as pin\n\n    pin._cmd_cal_train()\n",
        "\n\ndef planted():\n    pin.run_erasure_arm('x', 'cpu')\n",
        "\n\ndef planted(path):\n    return open(path)\n",
    ):
        assert test_phase37_routes._call_failures(source + plant), plant


def test_no_os_replace_and_no_inject_lora(tmp_path):
    from test_phase29_prereg import _planted
    from test_phase40_noise import _driver_failures

    source = (_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8")
    assert _driver_failures(source) == []
    for name, plant in (
        ("replace.py", "\n\ndef planted(a, b):\n    os.replace(a, b)\n"),
        ("inject.py", "\n\ndef planted(m):\n    personacore.lora.inject.inject_lora(m)\n"),
        ("import.py", "\n\nfrom personacore.lora.inject import inject_lora\n"),
    ):
        assert _driver_failures(_planted(tmp_path, source, source + plant, name)), name


def test_driver_binds_no_slot_name(tmp_path):
    from test_phase29_prereg import _planted
    from test_phase35_prereg import _slot_census_failures

    source = (_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8")
    assert _slot_census_failures([("scripts/phase41_erasure.py", source)]) == []
    planted = _planted(tmp_path, source, source + "\n\nE1_CONDITION_A_FLOORS = 3\n", "slot.py")
    assert _slot_census_failures([("scripts/phase41_erasure.py", planted)])


def test_no_check_unit_caps_k48_in_the_driver(tmp_path):
    from test_phase29_prereg import _planted
    from test_phase41_prereg import _k48_caps_call_failures

    source = (_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8")
    assert "check_unit_caps(" in source  # meta-guard: the driver does call the caps
    assert _k48_caps_call_failures(source) == []
    plant = '\nphase36_caps.check_unit_caps("E1", k48_confirms_per_cell=2)\n'
    assert _k48_caps_call_failures(_planted(tmp_path, source, source + plant, "k48.py"))


def _driver_census_values():
    """The ints and floats the driver must never type: every one read from its source here."""
    import mitigation_gate
    import phase19_erasure
    import phase20_run
    import phase35_prereg

    p = phase41_prereg
    noise = _noise_floor()
    gnf = noise["gap_noise_floor"]
    gaps = [noise["per_seed"][str(s)]["full"]["dialogue_gap"]["gap"] for s in p.SEEDS]
    bands = [
        edge
        for gap in gaps
        for edge in mitigation_gate.dialogue_gap_band(control_gap=gap, gap_noise_floor=gnf)
    ]
    retention = json.loads(phase20_run.RETENTION_FLOOR_PATH.read_text(encoding="utf-8"))
    ints = {
        p.E1_CHECKPOINT_GRID["read_k"],
        phase35_prereg.FULL_FIDELITY_K,
        phase19_erasure.N_TARGET_QUESTIONS,
        p.GRID[-1],
        phase19_erasure.N_COMPONENTS,
        *p.SEEDS,
    }
    floats = {
        p.E1_CONDITION_B_MARGIN,
        *bands,
        *gaps,
        gnf,
        p.ENTRIES["e1_share_hours"]["value"],
        *p.ENTRIES["e1_unit_prices"]["value"].values(),
        retention["cap"],
        retention["retention_ppl_noise_floor"],
    }
    assert len(ints) == 7 and len(bands) == 2 * len(gaps), "meta-guard: a census value collided"
    assert all(type(f) is float for f in floats), "meta-guard: a census value is not a float"
    return ints, floats


def test_no_derived_value_is_typed_in_the_driver(tmp_path):
    from test_phase29_prereg import _planted
    from test_phase35_prereg import _literal_failures

    ints, floats = _driver_census_values()
    source = (_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8")
    assert _literal_failures(source, ints, floats, set()) == []
    confirm_k = repr(max(i for i in ints if i in phase41_prereg.GRID))
    for name, plant in (
        ("k48.py", f"\nX = {confirm_k}\n"),
        ("margin.py", f"\nX = {phase41_prereg.E1_CONDITION_B_MARGIN!r}\n"),
    ):
        assert _literal_failures(
            _planted(tmp_path, source, source + plant, name), ints, floats, set()
        )


def test_no_target_name_is_typed_in_the_driver(tmp_path):
    from test_phase29_prereg import _planted
    from test_phase41_prereg import _typed_target_failures

    source = (_SCRIPTS / "phase41_erasure.py").read_text(encoding="utf-8")
    assert _typed_target_failures(source) == []
    target = phase41_prereg.TARGETS[1]
    planted = _planted(tmp_path, source, source + f"\nT = {target!r}\n", "typed.py")
    assert _typed_target_failures(planted)


def test_pin_and_gate_are_byte_unchanged_for_phase41():
    import hashlib

    from test_phase37_routes import _GATE_ANCHOR, _PIN_ANCHOR, _git_quiet

    probe = _json(_ROOT / "results" / "phase36_probe_e1.json")
    pinned = probe["provenance"]["module_sha256"]["scripts/phase19_erasure.py"]
    actual = hashlib.sha256((_SCRIPTS / "phase19_erasure.py").read_bytes()).hexdigest()
    assert actual == pinned
    for anchor, rel in (
        (_PIN_ANCHOR, "scripts/phase19_erasure.py"),
        (_GATE_ANCHOR, "scripts/erasure_gate.py"),
    ):
        assert _git_quiet("diff", "--quiet", anchor, "HEAD", "--", rel) == 0, rel
        assert _git("status", "--porcelain", "--", rel) == "", rel
        # Non-vacuity: the anchor commit itself DID change the file.
        assert _git_quiet("diff", "--quiet", f"{anchor}~1", anchor, "--", rel) != 0, rel


def test_census_helpers_called_directly(monkeypatch, tmp_path):
    """Every driver helper the paths above reach only indirectly, called by name."""
    import phase14_factset
    import phase18_extraction
    import phase19_erasure
    import torch

    from personacore import preflight as personacore_preflight

    p = phase41_prereg
    assert phase41_erasure._prove(True, "x") is None
    with pytest.raises(SystemExit, match=r"^\[phase41_erasure\] boom$"):
        phase41_erasure._prove(False, "boom")
    assert phase41_erasure._now().endswith("+00:00")
    assert phase41_erasure._rel(tmp_path / "a" / "b", tmp_path) == "a/b"
    assert phase41_erasure._key("t", "o", 1) == "t|o|1"
    assert phase41_erasure._counts([3, 27]) == "3/27"
    assert phase41_erasure._table(("a", "b"), [["x|y", 1]]) == [
        "| a | b |",
        "|---|---|",
        "| x\\|y | 1 |",
        "",
    ]
    unit = p.CELL_UNITS[-1]
    assert phase41_erasure._cell_section(
        unit, {"verdict": p.NOT_RUN, "outcome": "dropped"}, {}
    ) == [
        f"### {unit}",
        "",
        "Verdict **NOT_RUN** (ledger outcome: dropped).",
        "",
    ]
    assert phase41_erasure._prereg() is p
    assert phase41_erasure._noise_floor() == _noise_floor()
    path = _plant(tmp_path / "x.json", b'{"a": 1}')
    assert phase41_erasure._load(path) == {"a": 1}
    calls = []
    monkeypatch.setattr(
        personacore_preflight,
        "preflight_device",
        lambda **kw: calls.append(kw) or {"device": "cpu"},
    )
    assert phase41_erasure._device() == "cpu" and calls == [{"strict": True}]
    emptied = []
    monkeypatch.setattr(torch.mps, "empty_cache", lambda: emptied.append(1))
    for available in (False, True):
        monkeypatch.setattr(torch.backends.mps, "is_available", lambda a=available: a)
        assert phase41_erasure._release() is None
    assert emptied == [1]
    phase41_erasure._import_modules()
    assert all(
        pathlib.PurePosixPath(rel).stem in sys.modules
        for rel in phase41_erasure.MODULES
        if rel.startswith("scripts/")
    )
    assert phase41_erasure._disclosed_digests() == {
        r: phase41_erasure._sha256(_ROOT / r) for r in phase41_erasure.DISCLOSED_MODULES
    }
    assert phase41_erasure._root_ledger(phase41_erasure._ROOT) is True
    with pytest.raises(SystemExit, match="rehearsal into a tmp root"):
        phase41_erasure._root_ledger(phase41_erasure._ROOT, tmp_path / "l.jsonl")
    with pytest.raises(SystemExit, match="explicit ledger_path"):
        phase41_erasure._root_ledger(tmp_path, None)
    assert phase41_erasure._root_ledger(tmp_path, tmp_path / "l.jsonl") is False
    assert phase41_erasure._seed_first_prep_unit(p.SEEDS[0]) == p.PREP_UNITS[0]
    assert phase41_erasure._stage1_records() == tuple(
        rel
        for u in p.PREP_UNITS
        for rel in (p.calibration_record(*p.unit_key(u)[1:]), p.band_record(*p.unit_key(u)[:0:-1]))
    )
    cell = p.CELL_UNITS[0]
    assert len(phase41_erasure._unit_records(cell)) == 1 + 2 * len(_GRID)
    assert phase41_erasure._unit_records(p.PREP_UNITS[0]) == phase41_erasure._stage1_records()[:2]
    stale = phase41_erasure._stale_outputs(cell, root=tmp_path)
    assert phase41_erasure._ordering_path(tmp_path, cell) in stale
    assert all(phase41_erasure._m1_path(tmp_path, cell, c) in stale for c in _GRID)
    roots = phase41_erasure._output_roots(cell, root=tmp_path)
    assert [path for _, path in roots] == [x for x in stale if x != tmp_path / p.unit_record(cell)]
    assert {phase41_erasure._base(path, tmp_path) for _, path in roots} == {tmp_path}
    fact = phase41_erasure.target_fact(p.TARGETS[0])
    assert phase41_erasure.twin_references(fact) == phase19_erasure.reference_set_for_calibration(
        fact.slot, fact
    )
    taught = {f.slot: f.value for f in phase14_factset.LOCKED_FACTS}
    assert phase41_erasure.collateral() == {
        s: (taught[s], phase18_extraction.reference_set_for(s))
        for s in phase18_extraction.CORE_SLOTS
    }

    rig = _run_fakes(monkeypatch, _e1_rig(monkeypatch, tmp_path / "rig"))
    identity = phase41_erasure.record_rehearsal(rig.identity, units=p.PREP_UNITS)
    assert phase41_erasure._well_formed(
        {k: identity[k] for k in phase41_erasure._REQUIRED_IDENTITY_KEYS}
    )
    assert not phase41_erasure._well_formed({"git_sha": "h1"})
    assert phase41_erasure._kept_identity(rig.identity)["git_sha"] == "h1"
    assert phase41_erasure._kept_identity(tmp_path / "missing.json") is None
    with pytest.raises(SystemExit, match="variant.json is missing"):
        phase41_erasure._variant_record(rig.root)
    pf = phase41_erasure.preflight(**rig.kw)
    run = phase41_erasure._run_provenance(pf, "2026-10-08T00:00:00+00:00")
    assert (
        set(run) == set(phase41_erasure.RUN_PROVENANCE_KEYS)
        and run["head_moved_during_run"] is False
    )
    unit = p.PREP_UNITS[0]
    rel = phase41_erasure.run_prep_unit(
        unit,
        pf=pf,
        started_utc=run["started_utc"],
        state={},
        smoke=True,
        cpu_seconds=None,
        identity_path=rig.identity,
    )
    assert rel == p.unit_record(unit) and (rig.root / rel).is_file()
    assert phase41_erasure._variant_record(rig.root)["variant"] in p.VARIANTS
    lines = []
    assert phase41_erasure._dropped_attempts(unit, lines, root=rig.root, launch_git_sha="h1") == []
    assert phase41_erasure._compared_attempts(unit, [], root=rig.root) == []
    with pytest.raises(SystemExit, match="only a crashed attempt"):
        phase41_erasure._latest_dropped_dir(lines, unit, what="dropped")
    assert (
        phase41_erasure._pause_notices(rig.root) == []
        and phase41_erasure._resume_declarations(rig.root) == []
    )

    rig = _stage2_rig(monkeypatch, tmp_path / "cells", {_GRID[0]: (True, True, 5)})
    assert phase41_erasure._pause(p.CELL_UNITS[0], root=rig.root, ledger_path=rig.ledger) is None
    phase41_erasure.record_rehearsal(rig.identity, units=p.PREP_UNITS)
    pf = phase41_erasure.preflight(**rig.kw)
    rel = phase41_erasure.write_cell(
        p.CELL_UNITS[0], pf=pf, started_utc=phase41_erasure._now(), state={}
    )
    assert rel == p.unit_record(p.CELL_UNITS[0]) and _json(rig.root / rel)["stop"] == _GRID[0]


def test_census_every_phase41_erasure_function_has_a_cpu_test(tmp_path):
    import ast

    from test_phase29_prereg import _planted
    from test_phase36_prereg import _untested_functions

    real = _SCRIPTS / "phase41_erasure.py"
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the driver defines no function, the census would be vacuous"
    assert _untested_functions("phase41_erasure", source, test_source) == []
    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase41_erasure", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before


def test_no_skips_in_this_file(tmp_path):
    from test_phase29_prereg import _planted
    from test_phase36_prereg import _skip_failures

    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))
