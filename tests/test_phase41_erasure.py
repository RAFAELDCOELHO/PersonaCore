"""Plan 41-06: the E1 erasure driver (scripts/phase41_erasure.py) part 1, tested on CPU only.

The skeleton (Phase 40's shape, E1 constants), the written STOP-for-Rafael path, and the first-order
Taylor gradient ordering (D-01..D-05) on a tiny CPU GPT + LoRA fixture against finite differences.
Nothing here writes the real results/, ledger/ or data/ (the autouse guard below checks it around
every test); every output goes to a tmp root.
"""

import json
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
