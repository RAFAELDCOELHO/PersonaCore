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
    rig.real_require_launch = phase36_ledger.require_launch

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


# =================================================================================================
# (2) Task 2: the D-30 copy, the anchor ids and draws, the gate cells, the question scoring.
# =================================================================================================


@pytest.fixture(scope="module")
def tiny_gpt():
    import torch

    from personacore.config import ModelConfig
    from personacore.model.gpt import GPT

    torch.manual_seed(0)
    return GPT(ModelConfig(n_layer=1, n_head=2, n_embd=32)).eval()


def _cases(seed, n=24):
    """Seeded random (context, value) id lists: context 1-60 ids, value 1-8 ids, ids < 8184."""
    import random

    rng = random.Random(seed)
    return [
        (
            [rng.randrange(8184) for _ in range(rng.randint(1, 60))],
            [rng.randrange(8184) for _ in range(rng.randint(1, 8))],
        )
        for _ in range(n)
    ]


@pytest.fixture(params=["fake_lm", "tiny_gpt"])
def cpu_model(request):
    return request.getfixturevalue(request.param)


def test_copy_equality_with_the_pinned_function(cpu_model):
    cases = _cases(39)
    assert len(cases) >= 20
    for context, value in cases:
        pinned = phase18_extraction.span_nll_from_ids(cpu_model, context, value, "cpu")
        copy = phase39_ctx.span_nll_tokens(cpu_model, context, value, "cpu")
        assert copy["nll_sum"].hex() == pinned["nll_sum"].hex()
        assert copy["nll_mean"].hex() == pinned["nll_mean"].hex()
        assert copy["n_scored"] == pinned["n_scored"] == len(value)
        assert phase39_ctx._same_bits(copy["nll_sum"], pinned["nll_sum"])
    assert not phase39_ctx._same_bits(1.0, 1.0 + 2**-52)


def test_per_token_values_are_descriptive_sums(cpu_model):
    import math

    for context, value in _cases(40):
        copy = phase39_ctx.span_nll_tokens(cpu_model, context, value, "cpu")
        per_token = copy["per_token"]
        assert len(per_token) == len(value)
        assert all(math.isfinite(v) and v >= 0 for v in per_token)
        assert math.isclose(math.fsum(per_token), copy["nll_sum"], rel_tol=1e-5)


def test_suffix_sum_is_bitwise_the_pinned_call(cpu_model):
    checked = 0
    for context, value in _cases(41):
        plain = phase39_ctx.span_nll_tokens(cpu_model, context, value, "cpu")
        assert plain["suffix_from"] is None and plain["suffix_nll_sum"] is None
        for r in range(1, len(value)):
            copy = phase39_ctx.span_nll_tokens(cpu_model, context, value, "cpu", suffix_from=r)
            pinned = phase18_extraction.span_nll_from_ids(
                cpu_model, context + value[:r], value[r:], "cpu"
            )
            assert copy["suffix_from"] == r
            assert copy["suffix_nll_sum"].hex() == pinned["nll_sum"].hex()
            assert copy["nll_sum"].hex() == plain["nll_sum"].hex()
            assert copy["nll_mean"].hex() == plain["nll_mean"].hex()
            checked += 1
    assert checked >= 20


def test_copy_refuses(fake_lm):
    for context, value, kwargs, reason in (
        ([], [5], {}, "empty context"),
        ([5], [], {}, "zero value tokens"),
        ([5], [6, 7], {"suffix_from": 0}, "suffix_from"),
        ([5], [6, 7], {"suffix_from": 2}, "suffix_from"),
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*" + reason):
            phase39_ctx.span_nll_tokens(fake_lm, context, value, "cpu", **kwargs)


def test_anchor_ids_are_the_value_span_nll_context(monkeypatch, tok):
    seen = []

    def record(model, context_ids, value_ids, device):
        seen.append(list(context_ids))
        return {"n_scored": len(value_ids), "nll_sum": 0.0, "nll_mean": 0.0}

    monkeypatch.setattr(phase18_extraction, "span_nll_from_ids", record)
    for slot in SLOTS:
        phase18_extraction.value_span_nll(
            None, tok, "cpu", slot=slot, value=TAUGHT[slot], frame="ans1"
        )
        assert seen[-1] == phase39_ctx.anchor_ids(tok, slot), slot
    assert len(seen) == len(SLOTS) == 8
    assert phase18_extraction.ADMISSIBLE_NLL_FRAME == "ans1"


@pytest.fixture
def anchor_rig(monkeypatch, tok):
    import phase16_persistence
    import phase19_erasure

    rig = types.SimpleNamespace(draws=[], guards=[], digest=phase19_erasure.FORBID_IDS_SHA256)
    real_guard = phase14_recall.assert_no_value_in_prompt

    def guard(tok_, question, values, *, prompt_ids=None):
        rig.guards.append((question, list(values), prompt_ids))
        real_guard(tok_, question, values, prompt_ids=prompt_ids)

    def draw_all(model, tok_, prompt_ids, device, forbid, index, **kwargs):
        rig.draws.append((list(prompt_ids), index, kwargs))
        k = kwargs["n_samples"] + 1
        return [f"draw {i}" for i in range(k - 1)] + [TAUGHT[rig.slot]], [True] * k

    monkeypatch.setattr(phase16_persistence, "forbid_digest", lambda forbid: rig.digest)
    monkeypatch.setattr(phase14_recall, "assert_no_value_in_prompt", guard)
    monkeypatch.setattr(phase14_recall, "draw_all", draw_all)
    return rig


def test_anchor_draws_dispatch_the_anchor_ids_at_the_d28_index(anchor_rig, tok):
    K = phase39_prereg.K
    for slot in ("house_number", "person_name"):  # one slot alone keeps its LOCKED_FACTS index
        anchor_rig.slot = slot
        record = phase39_ctx.anchor_draws("model", tok, "cpu", "forbid", slot, "k8")
        ids = phase39_ctx.anchor_ids(tok, slot)
        prompt_ids, index, kwargs = anchor_rig.draws[-1]
        assert prompt_ids == ids
        assert index == phase39_prereg.anchor_seed_index(slot) == SLOTS.index(slot) * K
        assert kwargs == {"n_samples": K - 1}
        assert anchor_rig.guards[-1] == (tok.decode(ids), phase39_ctx._guard_values(), ids)
        assert set(phase18_extraction.DRAW_RECORD_KEYS) | {"stopped"} <= set(record)
        assert record["family"] == "anchor" and record["arm"] == "k8"
        assert record["prefix_text"] is None and record["tier"] is None
        assert record["slot"] == slot and record["seed_index"] == SLOTS.index(slot)
        assert len(record["completions"]) == len(record["stopped"]) == K
        assert record["prompt_ids"] == ids
        fact_id = next(f.id for f in phase14_factset.LOCKED_FACTS if f.slot == slot)
        assert record["fact_id"] == fact_id
        scored = phase18_extraction.score_records([record], {fact_id: TAUGHT[slot]})
        hits = scored[0]["hits"]
        assert len(hits) == K and hits[-1] is True and not any(hits[:-1])
        # Pitfall 5, in the test only: the anchor unit is the question unit of one record.
        tier = phase18_extraction.CORPUS_TIERS[0]
        assert (
            int(any(hits))
            == phase18_extraction.aggregate_questions(
                phase18_extraction.score_records(
                    [{**record, "tier": tier}], {fact_id: TAUGHT[slot]}
                ),
                tier=tier,
            )[fact_id]["n_answerable"]
        )


def test_anchor_draws_guard_runs_before_any_draw(anchor_rig, tok, monkeypatch):
    anchor_rig.slot = "street"

    def leak(*args, **kwargs):
        raise SystemExit("[phase14_recall] leak")

    monkeypatch.setattr(phase14_recall, "assert_no_value_in_prompt", leak)
    with pytest.raises(SystemExit, match="leak"):
        phase39_ctx.anchor_draws("model", tok, "cpu", "forbid", "street", "k0")
    assert anchor_rig.draws == []


def test_anchor_draws_refuse_a_wrong_forbid_mask(anchor_rig, tok):
    anchor_rig.slot = "street"
    anchor_rig.digest = "0" * 64
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*forbid"):
        phase39_ctx.anchor_draws("model", tok, "cpu", "forbid", "street", "k0")
    assert anchor_rig.draws == [] and anchor_rig.guards == []


def test_gate_cells_mark_bitwise_equality(fake_lm, tok, monkeypatch, capsys):
    import math

    for slot in ("pet_name", "birth_year"):
        state = {"draw_index": None}
        cells = phase39_ctx.gate_cells(fake_lm, tok, "cpu", slot, state)
        references = list(phase18_extraction.reference_set_for(slot))
        assert list(cells) == references
        assert state["draw_index"] == len(references) - 1
        for value, cell in cells.items():
            assert cell["equal"] is True, (slot, value)
            assert set(cell["pinned"]) == {"n_scored", "nll_sum", "nll_mean"}
            assert cell["copy"]["nll_sum"] == cell["pinned"]["nll_sum"]
    assert capsys.readouterr().out == ""
    real = phase18_extraction.value_span_nll
    bumped = list(phase18_extraction.reference_set_for("street"))[1]

    def nudged(model, tok_, device, *, slot, value, frame):
        row = real(model, tok_, device, slot=slot, value=value, frame=frame)
        if value == bumped:
            row = {**row, "nll_sum": math.nextafter(row["nll_sum"], math.inf)}
        return row

    monkeypatch.setattr(phase18_extraction, "value_span_nll", nudged)
    cells = phase39_ctx.gate_cells(fake_lm, tok, "cpu", "street", {})
    assert cells[bumped]["equal"] is False
    assert all(cell["equal"] for value, cell in cells.items() if value != bumped)


@pytest.fixture(scope="module")
def entries():
    return phase39_prereg.e6_entries()


def test_question_scoring_uses_the_guarded_span(fake_lm, tok, entries, monkeypatch):
    calls = []
    real = phase39_ctx.span_nll_tokens

    def recorded(model, context_ids, value_ids, device, *, suffix_from=None):
        calls.append((list(context_ids), list(value_ids), suffix_from))
        return real(model, context_ids, value_ids, device, suffix_from=suffix_from)

    monkeypatch.setattr(phase39_ctx, "span_nll_tokens", recorded)
    for index in (0, 100, 215):
        _, entry = entries[index]
        slot = entry["slot"]
        taught = TAUGHT[slot]
        references = list(phase18_extraction.reference_set_for(slot))
        calls.clear()
        state = {"draw_index": None}
        rows = phase39_ctx.score_question(
            fake_lm, tok, "cpu", entry, references, taught=taught, state=state
        )
        context = phase18_extraction._guarded_span(entry)
        assert list(rows) == references and len(calls) == len(references)
        for (ctx, value_ids, suffix_from), candidate in zip(calls, references, strict=True):
            assert ctx == context
            assert value_ids == list(tok.encode(candidate))
            expected = entry["realized_injection"] if candidate == taught else None
            assert suffix_from == expected
        # D-30a on a real entry: the suffix sum is the pinned NLL in A2's exact context.
        pinned = phase18_extraction.span_nll_from_ids(
            fake_lm,
            list(entry["prompt_ids"]),
            list(tok.encode(taught))[entry["realized_injection"] :],
            "cpu",
        )
        assert rows[taught]["suffix_nll_sum"].hex() == pinned["nll_sum"].hex()
        # D-11 (ii): the minted candidates, never the taught value.
        minted = phase39_prereg.minted_members(slot)
        assert taught not in minted
        calls.clear()
        rows = phase39_ctx.score_question(
            fake_lm, tok, "cpu", entry, [taught, *minted], taught=taught, state=state
        )
        assert [c[2] for c in calls] == [entry["realized_injection"]] + [None] * len(minted)


def test_question_scoring_refuses_a_broken_d23b_premise(fake_lm, tok, entries):
    _, entry = entries[0]
    broken = {**entry, "prompt_ids": [*entry["prompt_ids"][:-1], entry["prompt_ids"][-1] + 1]}
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*D-23b"):
        phase39_ctx.score_question(
            fake_lm, tok, "cpu", broken, ["x"], taught=TAUGHT[entry["slot"]], state={}
        )


# =================================================================================================
# (3) Task 3: preflight — every refusal before the ledger start line, gate 2 included.
# =================================================================================================


def test_preflight_alone_writes_nothing(rig, committed_digests, capsys):
    pre = phase39_ctx.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    out = capsys.readouterr().out
    head = _git("rev-parse", "HEAD")
    assert out.startswith(f"PREFLIGHT OK {head} device=mps readings=8 slots=8 entries=216 ")
    assert f" projection_h={phase39_prereg.E6_PROJECTION_HOURS} " in out
    assert f" stop_h={phase39_prereg.E6_STOP_HOURS} " in out
    assert out.rstrip().endswith("spent_E6_s=0.0")
    assert set(pre) == {
        "git_sha",
        "module_sha256",
        "device",
        "gate",
        "reconstruction",
        "readings",
        "slots",
        "gate2",
    }
    assert pre["git_sha"] == head and pre["device"] == "mps"
    assert pre["readings"] == READINGS and pre["slots"] == SLOTS
    assert pre["module_sha256"] == phase39_ctx.module_sha256()
    assert pre["reconstruction"]["persona_adapter"] == committed_digests["persona_adapter"]
    assert pre["gate2"] is rig.gate2 and pre["gate2"]["passed"] is True
    assert rig.launches == [("E6", {"ledger_path": rig.paths["ledger_path"]})]
    assert [d["pathspec"] for d in rig.dirty] == [phase39_ctx.LAUNCH_PATHSPEC]
    assert rig.dirty[0]["cwd"] == phase39_ctx._REPO
    assert not rig.paths["ledger_path"].exists()
    assert not rig.paths["heartbeat_path"].exists()
    assert sorted(p.name for p in rig.root.iterdir()) == ["data", "inputs", "results"]
    assert list((rig.root / "data").iterdir()) == []


def test_preflight_caps_never_get_adapters(rig, monkeypatch):
    import phase36_caps

    seen = []
    real = phase36_caps.check_unit_caps

    def record(front, **kwargs):
        seen.append((front, kwargs))
        return real(front, **kwargs)

    monkeypatch.setattr(phase36_caps, "check_unit_caps", record)
    phase39_ctx.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    assert seen == [
        ("E6", {"entries": 216, "a2_regenerated_entries": 0, "anchor_slots": 8, "max_k": 48})
    ]


def test_preflight_with_the_real_require_launch_on_a_tmp_ledger(rig, monkeypatch, capsys):
    """The committed stops through the REAL require_launch, on an empty tmp ledger."""
    monkeypatch.setattr(phase36_ledger, "require_launch", rig.real_require_launch)
    pre = phase39_ctx.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    assert pre["gate"]["front"] == "E6" and pre["gate"]["lifted"] == ()
    assert capsys.readouterr().out.startswith("PREFLIGHT OK")
    assert not rig.paths["ledger_path"].exists()


def _plant_output(index):
    def plant(rig, monkeypatch):
        path = phase39_ctx.outputs(rig.root)[index]
        path.write_text("{}", encoding="utf-8")

    plant.__name__ = f"output_{index}"
    return plant


def _refuse_dirty(rig, monkeypatch):
    def dirty(**kw):
        raise SystemExit("[phase39_ctx] dirty tree")

    monkeypatch.setattr(phase39_ctx, "refuse_if_dirty", dirty)


def _refuse_unknown_sha(rig, monkeypatch):
    monkeypatch.setattr(phase39_ctx, "git_sha", lambda: "unknown")


def _refuse_untracked_input(rig, monkeypatch):
    real = phase39_ctx.tracked_inputs
    monkeypatch.setattr(phase39_ctx, "tracked_inputs", lambda: (*real(), "results/none.json"))


def _refuse_launch(rig, monkeypatch):
    def cut(front, **kw):
        raise SystemExit("[phase36_ledger] PAUSE")

    monkeypatch.setattr(phase36_ledger, "require_launch", cut)


def _refuse_no_readings(rig, monkeypatch):
    return {"readings": ()}


def _refuse_unknown_reading(rig, monkeypatch):
    return {"readings": ("k0", "k7")}


def _refuse_no_slots(rig, monkeypatch):
    return {"slots": ()}


def _refuse_unknown_slot(rig, monkeypatch):
    return {"slots": ("street", "shoe_size")}


def _refuse_approval(rig, monkeypatch):
    monkeypatch.setattr(phase39_prereg, "APPROVED_E6_ADAPTERS", 7)


def _refuse_adapter_cap(rig, monkeypatch):
    monkeypatch.setattr(phase39_prereg, "COMMITTED_ADAPTER_CAP", 6)


def _refuse_anchor_adapter_cap(rig, monkeypatch):
    monkeypatch.setattr(phase39_prereg, "COMMITTED_ANCHOR_ADAPTER_CAP", 6)


def _refuse_unit_caps(rig, monkeypatch):
    monkeypatch.setattr(phase39_prereg, "K", 49)


def _refuse_cpu_on_the_real_root(rig, monkeypatch):
    monkeypatch.setattr(phase39_ctx, "_ROOT", rig.root)
    monkeypatch.setattr(phase39_ctx, "_device", lambda: "cpu")


def _refuse_missing_gitignored_input(rig, monkeypatch):
    monkeypatch.setattr(phase14_recall, "CONVBASE_SLIM", rig.root / "missing" / "convbase")


def _refuse_missing_m2(rig, monkeypatch):
    monkeypatch.setattr(phase38_rank, "m2_adapter_path", lambda: rig.root / "missing" / "m2")


def _refuse_persona_digest(rig, monkeypatch):
    rig.digests["persona_adapter"] = "0" * 64


def _refuse_m2_digest(rig, monkeypatch):
    rig.digests["m2_adapter"] = "0" * 64


def _refuse_components_digest(rig, monkeypatch):
    monkeypatch.setattr(phase38_prereg, "components_sha256", lambda components: "0" * 64)


def _refuse_a2_record(rig, monkeypatch):
    pins = {r: dict(pin) for r, pin in phase39_prereg.A2_RECORDS.items()}
    pins["k32"]["sha256"] = "0" * 64
    monkeypatch.setattr(phase39_prereg, "A2_RECORDS", pins)


def _refuse_gate2(rig, monkeypatch):
    rows = json.loads(json.dumps(rig.gate2["rows"]))
    rows["k16"]["street"].update(count=rows["k16"]["street"]["count"] + 1, equal=False)
    rig.gate2 = {**rig.gate2, "passed": False, "rows": rows}


_REFUSALS = [
    *((_plant_output(i), r"exists: the E6 scoring has already run") for i in range(12)),
    (_refuse_dirty, r"dirty tree"),
    (_refuse_unknown_sha, r"could not read HEAD"),
    (_refuse_untracked_input, r"results/none\.json is not tracked"),
    (_refuse_launch, r"PAUSE"),
    (_refuse_no_readings, r"no readings"),
    (_refuse_unknown_reading, r"'k7' is not one of"),
    (_refuse_no_slots, r"no slots"),
    (_refuse_unknown_slot, r"'shoe_size' is not one of"),
    (_refuse_approval, r"D-11 approval of 7"),
    (_refuse_adapter_cap, r"committed E6 adapters cap is 7, not 6"),
    (_refuse_anchor_adapter_cap, r"committed E6 anchor_adapters cap is 7, not 6"),
    (_refuse_unit_caps, r"max_k = 49 exceeds the committed cap 48"),
    (_refuse_cpu_on_the_real_root, r"\(D-21\)"),
    (_refuse_missing_gitignored_input, r"convbase is missing"),
    (_refuse_missing_m2, r"m2 is missing"),
    (_refuse_persona_digest, r"persona adapter is not"),
    (_refuse_m2_digest, r"M2 adapter is not"),
    (_refuse_components_digest, r"components are not"),
    (_refuse_a2_record, r"k32: .* is not the committed record"),
    (_refuse_gate2, r"gate 2 \(D-19\): k16/street re-derived \d+, committed \d+"),
]


@pytest.mark.parametrize(("plant", "reason"), _REFUSALS, ids=[p.__name__ for p, _ in _REFUSALS])
def test_preflight_refusals_write_no_ledger_line(rig, monkeypatch, plant, reason):
    kwargs = plant(rig, monkeypatch) or {}
    with pytest.raises(
        SystemExit,
        match=r"^\[(phase39_ctx|phase39_prereg|phase36_ledger|phase36_caps|phase38_rank)\] .*"
        + reason,
    ):
        phase39_ctx.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"], **kwargs)
    assert not rig.paths["ledger_path"].exists()
    assert not rig.paths["heartbeat_path"].exists()


def test_the_refusals_cover_every_output(rig):
    planted = [p for p, _ in _REFUSALS if p.__name__.startswith("output_")]
    assert len(planted) == len(phase39_ctx.outputs(rig.root)) == 12


def test_preflight_refuses_an_open_attempt_and_not_a_closed_one(rig):
    ledger = rig.paths["ledger_path"]
    rid, kw = phase39_ctx.RUN_ID, {"phase": 39, "front": "E6", "ledger_path": ledger}
    phase36_ledger.append("start", run_id=rid, **kw)
    before = ledger.read_bytes()
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*open attempt"):
        phase39_ctx.preflight(root=rig.root, ledger_path=ledger)
    assert ledger.read_bytes() == before
    phase36_ledger.append("end", run_id=rid, record=phase39_prereg.CTX_RECORD, **kw)
    closed = ledger.read_bytes()
    assert phase39_ctx.preflight(root=rig.root, ledger_path=ledger)["device"] == "mps"
    assert ledger.read_bytes() == closed


def test_the_first_io_free_checks_refuse_on_the_real_root(tmp_path):
    """The readings, slots and device checks come first: the real root is safe here whether or
    not the real record exists."""
    ledger = tmp_path / "ledger.jsonl"
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*no readings"):
        phase39_ctx.preflight(ledger_path=ledger, device="mps", readings=())
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*no slots"):
        phase39_ctx.preflight(ledger_path=ledger, device="mps", slots=())
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*D-21"):
        phase39_ctx.preflight(ledger_path=ledger, device="cpu")
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*D-21"):
        phase39_ctx.preflight(root=_REPO / "scratch_inside_repo", ledger_path=ledger, device="cpu")
    assert not ledger.exists()


def test_preflight_on_a_rehearsal_root_accepts_cpu_and_a_slice(rig, monkeypatch):
    monkeypatch.setattr(phase39_ctx, "_device", lambda: "cpu")
    pre = phase39_ctx.preflight(
        root=rig.root,
        ledger_path=rig.paths["ledger_path"],
        readings=("k0", "k78"),
        slots=("pet_name", "street"),
    )
    assert pre["device"] == "cpu"
    assert pre["readings"] == ("k0", "k78") and pre["slots"] == ("pet_name", "street")
    assert not rig.paths["ledger_path"].exists()
