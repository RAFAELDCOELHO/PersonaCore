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
