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
    }
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
    rehearsal = _e1_rig(monkeypatch, tmp_path / "rehearsal")
    _whole(rehearsal.ledger, *prep)
    before = _lines(rehearsal.ledger)
    with pytest.raises(SystemExit, match="41-09"):
        _launch(rehearsal, monkeypatch)
    assert _lines(rehearsal.ledger) == before and not rehearsal.heartbeat.exists()
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
