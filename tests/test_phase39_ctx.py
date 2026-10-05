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

import ast
import contextlib
import hashlib
import inspect
import json
import math
import pathlib
import re
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

from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402

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
        "rehearsal_disclosure",
    }
    assert pre["rehearsal_disclosure"] is None  # a rehearsal root: nothing to disclose yet
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
    *((_plant_output(i), r"exists: the E6 scoring has already run") for i in range(2)),
    # WR-01 (39-REVIEW-3): sidecars with no run sidecar and no record are a crashed attempt's.
    *((_plant_output(i), r"partial sidecars from a crashed attempt") for i in range(2, 12)),
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


# =================================================================================================
# (4) Plan 05 Task 1: run() — the gate pass with the D-30 bitwise STOP, the work pass, the
# sidecars and the ledger lines. All on a fake rig: tmp root, tmp ledger, tmp heartbeat.
# =================================================================================================


class FakeModel:
    def __init__(self, reading):
        self.reading = reading


_FORBID = object()


def _offset(key, value):
    """A deterministic per-(key, value) offset in (-0.5, 0.5), never exactly 0."""
    digest = hashlib.sha256(f"{key}|{value}".encode()).hexdigest()
    return (int(digest[:8], 16) / 2**32 - 0.5) or 0.25


@pytest.fixture(scope="module")
def gate_ranks():
    return phase38_prereg.committed_gate_ranks()


@pytest.fixture(scope="module")
def references():
    return {slot: list(phase18_extraction.reference_set_for(slot)) for slot in SLOTS}


def _fake_table(gate_ranks, references):
    """Taught 1.0; the first (committed rank - 1) other references in string order 0.5, the rest
    2.0: rank_in_prefix then reproduces every committed rank exactly."""
    table = {}
    for reading in READINGS:
        for slot in SLOTS:
            members = sorted(r for r in references[slot] if r != TAUGHT[slot])
            rank = gate_ranks[reading][slot]["rank"]
            for i, member in enumerate(members):
                table[(reading, slot, member)] = 0.5 if i < rank - 1 else 2.0
            table[(reading, slot, TAUGHT[slot])] = 1.0
    return table


_HIT_READINGS = ("k0", "k8", "M2")


@pytest.fixture
def run_rig(rig, monkeypatch, tok, gate_ranks, references):
    """The preflight rig plus the device work: fake models, the pinned scorer from a table, the
    copy, the draws. Every scored item lands in ``rig.log`` in order."""
    import phase16_persistence
    import phase19_erasure

    rig.models, rig.log, rig.crash, rig.ulp = [], [], None, None
    rig.table = _fake_table(gate_ranks, references)
    anchors = {tuple(phase39_ctx.anchor_ids(tok, slot)): slot for slot in SLOTS}
    values = {}
    for slot in SLOTS:
        for value in (*references[slot], *phase39_prereg.minted_members(slot)):
            values[tuple(tok.encode(value))] = value

    @contextlib.contextmanager
    def reading_model(reading, device):
        rig.models.append((reading, device))
        yield FakeModel(reading), tok, _FORBID

    def pinned_row(reading, slot, value):
        n = len(tok.encode(value))
        nll = rig.table[(reading, slot, value)]
        return {"n_scored": n, "nll_sum": nll * n, "nll_mean": nll}

    def value_span_nll(model, tok_, device, *, slot, value, frame):
        rig.log.append(("gate", model.reading, slot, value))
        return {**pinned_row(model.reading, slot, value), "frame": frame}

    def copy(model, context_ids, value_ids, device, *, suffix_from=None):
        value = values[tuple(value_ids)]
        slot = anchors.get(tuple(context_ids))
        if slot is not None:
            rig.log.append(("copy_anchor", model.reading, slot, value))
            row = pinned_row(model.reading, slot, value)
            if rig.ulp == (model.reading, slot, value):
                row["nll_sum"] = math.nextafter(row["nll_sum"], math.inf)
            n = row["n_scored"]
            return {**row, "per_token": [row["nll_mean"]] * n, "suffix_from": None}
        rig.log.append(("question", model.reading, value))
        if rig.crash is not None and rig.crash(model.reading):
            raise RuntimeError("copy died mid-scoring")
        context = hashlib.sha256(repr(list(context_ids)).encode()).hexdigest()
        nll = 1.0 + _offset(f"{model.reading}|{context}", value)
        n = len(value_ids)
        return {
            "n_scored": n,
            "nll_sum": nll * n,
            "nll_mean": nll,
            "per_token": [nll] * n,
            "suffix_from": suffix_from,
            "suffix_nll_sum": None if suffix_from is None else nll * (n - suffix_from),
        }

    def draw_all(model, tok_, prompt_ids, device, forbid, index, **kwargs):
        slot = anchors[tuple(prompt_ids)]
        rig.log.append(("draw", model.reading, slot, index))
        k = kwargs["n_samples"] + 1
        hit = [f"it is {TAUGHT[slot]}"] if model.reading in _HIT_READINGS else ["nothing"]
        return [f"draw {i}" for i in range(k - 1)] + hit, [True] * k

    monkeypatch.setattr(phase39_ctx, "reading_model", reading_model)
    monkeypatch.setattr(
        phase16_persistence,
        "forbid_digest",
        lambda forbid: phase19_erasure.FORBID_IDS_SHA256 if forbid is _FORBID else "0" * 64,
    )
    monkeypatch.setattr(phase18_extraction, "value_span_nll", value_span_nll)
    monkeypatch.setattr(phase39_ctx, "span_nll_tokens", copy)
    monkeypatch.setattr(phase14_recall, "draw_all", draw_all)
    return rig


def _sidecar(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _lines(rig):
    return phase36_ledger.read_ledger(rig.paths["ledger_path"])


def _kinds(rig, kind):
    return [entry[1:] for entry in rig.log if entry[0] == kind]


def test_run_scores_the_full_shape_gate_first(run_rig, references, entries, capsys):
    rig = run_rig
    assert phase39_ctx.run(root=rig.root, **rig.paths) == "SCORED"
    assert "RUN SCORED — next: crosscheck, then emit" in capsys.readouterr().out
    lines = _lines(rig)
    assert [(x["event"], x["run_id"]) for x in lines] == [
        ("start", phase39_ctx.RUN_ID),
        ("end", phase39_ctx.RUN_ID),
    ]
    assert lines[1]["record"] == phase39_prereg.CTX_RECORD and lines[1]["front"] == "E6"
    # D-18 / D-30: every gate cell, through both functions, before any draw or question NLL.
    first_work = min(i for i, e in enumerate(rig.log) if e[0] in ("draw", "question"))
    gate_part = rig.log[:first_work]
    expected = [(r, s, v) for r in READINGS for s in SLOTS for v in references[s]]
    assert [e[1:] for e in gate_part if e[0] == "gate"] == expected
    assert [e[1:] for e in gate_part if e[0] == "copy_anchor"] == expected
    assert {e[0] for e in rig.log[first_work:]} == {"draw", "question"}
    assert [r for r, _ in rig.models] == [*READINGS, *READINGS]
    assert {d for _, d in rig.models} == {"mps"}
    gate = _sidecar(phase39_ctx.gate_sidecar(rig.root))
    assert gate["passed"] is True and gate["run_id"] == phase39_ctx.RUN_ID
    assert gate["copy_equality"] == {"cells_compared": 8 * 56, "cells_equal": 8 * 56, "unequal": []}
    assert all(row["equal"] for rows in gate["rows"].values() for row in rows.values())
    assert set(gate["cells"]) == set(READINGS)
    K = phase39_prereg.K
    for reading in READINGS:
        blob = _sidecar(phase39_ctx.reading_sidecar(rig.root, reading))
        assert blob["reading"] == reading and blob["run_id"] == phase39_ctx.RUN_ID
        assert set(blob["anchor"]) == set(SLOTS)
        for slot, record in blob["anchor"].items():
            assert len(record["completions"]) == len(record["stopped"]) == K
            assert record["slot"] == slot and record["arm"] == reading
        assert set(blob["questions"]) == {str(i) for i, _ in entries}
        assert len(blob["questions"]) == 216
        for i, entry in entries:
            q = blob["questions"][str(i)]
            slot = entry["slot"]
            assert q["index"] == i and q["slot"] == slot and q["fact_id"] == entry["fact_id"]
            assert (q["tier"], q["seed_index"]) == (entry["tier"], entry["seed_index"])
            assert q["realized_injection"] == entry["realized_injection"]
            assert set(q["references"]) == set(references[slot])
            for candidate, row in q["references"].items():
                if candidate == TAUGHT[slot]:
                    assert row["suffix_from"] == entry["realized_injection"]
                    assert row["suffix_nll_sum"] is not None
                else:
                    assert row["suffix_from"] is None and row["suffix_nll_sum"] is None
            # D-26: the minted members only — the taught NLL is shared with R_q.
            assert set(q["minted"]) == set(phase39_prereg.minted_members(slot))
    run = _sidecar(phase39_ctx.run_sidecar(rig.root))
    assert run["status"] == "SCORED" and run["run_id"] == phase39_ctx.RUN_ID
    assert set(phase39_ctx.RUN_PROVENANCE_KEYS) <= set(run)
    assert run["git_sha_at_launch"] == run["git_sha_at_end"] == _git("rev-parse", "HEAD")
    assert run["head_moved_during_run"] is False and run["device"] == "mps"
    assert run["module_sha256_at_launch"] == phase39_ctx.module_sha256()
    assert run["reconstruction"] == phase38_rank.reconstruction_checks()
    assert run["gate2"]["rows"] == rig.gate2["rows"]
    assert (run["readings"], run["slots"]) == (list(READINGS), list(SLOTS))
    assert run["entries"] == [i for i, _ in entries]
    assert run["gate_sha256"] == phase39_ctx._sha256(phase39_ctx.gate_sidecar(rig.root))
    assert run["reading_sha256"] == {
        r: phase39_ctx._sha256(phase39_ctx.reading_sidecar(rig.root, r)) for r in READINGS
    }
    beats = [json.loads(t) for t in rig.paths["heartbeat_path"].read_text().splitlines()]
    assert beats and {b["point"] for b in beats} == {phase39_ctx.RUN_ID}
    assert not (rig.root / phase39_prereg.CTX_RECORD).exists()  # emit is plan 06's


def _assert_gate_failed(rig):
    assert _kinds(rig, "draw") == [] and _kinds(rig, "question") == []
    assert [r for r, _ in rig.models] == list(READINGS)  # no work pass
    assert not any(phase39_ctx.reading_sidecar(rig.root, r).exists() for r in READINGS)
    run = _sidecar(phase39_ctx.run_sidecar(rig.root))
    assert run["status"] == "GATE_FAILED" and run["reading_sha256"] == {}
    assert [x["event"] for x in _lines(rig)] == ["start", "end"]
    return _sidecar(phase39_ctx.gate_sidecar(rig.root))


def test_a_gate_rank_mismatch_is_gate_failed(run_rig):
    rig = run_rig
    rig.table[("k32", "street", TAUGHT["street"])] = 3.0
    assert phase39_ctx.run(root=rig.root, **rig.paths) == "GATE_FAILED"
    gate = _assert_gate_failed(rig)
    assert gate["passed"] is False
    assert [
        (r, s) for r, rows in gate["rows"].items() for s, x in rows.items() if not x["equal"]
    ] == [("k32", "street")]
    assert gate["copy_equality"] == {"cells_compared": 8 * 56, "cells_equal": 8 * 56, "unequal": []}


def test_a_bitwise_inequality_is_gate_failed(run_rig, references):
    rig = run_rig
    bumped = references["street"][1]
    rig.ulp = ("k16", "street", bumped)
    assert phase39_ctx.run(root=rig.root, **rig.paths) == "GATE_FAILED"
    gate = _assert_gate_failed(rig)
    assert gate["passed"] is False
    assert all(row["equal"] for rows in gate["rows"].values() for row in rows.values())
    assert gate["copy_equality"] == {
        "cells_compared": 8 * 56,
        "cells_equal": 8 * 56 - 1,
        "unequal": [["k16", "street", bumped]],
    }
    assert gate["cells"]["k16"]["street"][bumped]["equal"] is False


def test_the_real_root_refuses_a_partial_shape(tmp_path):
    ledger, hb = tmp_path / "ledger.jsonl", tmp_path / "hb.jsonl"
    for kw in (
        {"readings": ("k0",)},
        {"slots": ("pet_name",)},
        {"rehearsal_identity": tmp_path / "id.json"},
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*full"):
            phase39_ctx.run(ledger_path=ledger, heartbeat_path=hb, **kw)
        with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*full"):
            phase39_ctx.run(root=_REPO / "scratch", ledger_path=ledger, heartbeat_path=hb, **kw)
    assert not ledger.exists() and not hb.exists() and not (tmp_path / "id.json").exists()


def test_a_rehearsal_root_needs_its_own_ledger_and_heartbeat(rig):
    milestone_ledger = phase36_ledger._ROOT / phase36_ledger.LEDGER_PATH
    milestone_hb = pathlib.Path(phase36_ledger.HEARTBEAT_PATH)
    ledger, hb = rig.paths["ledger_path"], rig.paths["heartbeat_path"]
    for kw in (
        {"ledger_path": None, "heartbeat_path": hb},
        {"ledger_path": ledger, "heartbeat_path": None},
        {"ledger_path": milestone_ledger, "heartbeat_path": hb},
        {"ledger_path": ledger, "heartbeat_path": milestone_hb},
        {},
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*DR-01"):
            phase39_ctx.run(root=rig.root, **kw)
    assert not ledger.exists() and not hb.exists() and rig.launches == []


def test_a_rehearsal_root_runs_a_partial_shape(run_rig, entries):
    rig = run_rig
    shape = {"readings": ("k0", "k78"), "slots": ("pet_name", "birth_year")}
    assert phase39_ctx.run(root=rig.root, **rig.paths, **shape) == "SCORED"
    written = sorted(p.name for p in (rig.root / "data").iterdir())
    assert written == [
        "phase39_ctx_gate.json",
        "phase39_ctx_k0.json",
        "phase39_ctx_k78.json",
        "phase39_ctx_run.json",
    ]
    K = phase39_prereg.K
    in_shape = [i for i, e in entries if e["slot"] in shape["slots"]]
    assert len(in_shape) == 54
    for reading in shape["readings"]:
        blob = _sidecar(phase39_ctx.reading_sidecar(rig.root, reading))
        assert list(blob["anchor"]) == ["birth_year", "pet_name"]  # sort_keys
        assert sorted(blob["questions"], key=int) == [str(i) for i in in_shape]
    # D-28: each slot keeps its LOCKED_FACTS seed index in a slice.
    assert _kinds(rig, "draw") == [
        (reading, slot, index)
        for reading in shape["readings"]
        for slot, index in (("pet_name", 1 * K), ("birth_year", 6 * K))
    ]
    run = _sidecar(phase39_ctx.run_sidecar(rig.root))
    assert run["readings"] == ["k0", "k78"] and run["slots"] == ["pet_name", "birth_year"]
    assert run["entries"] == in_shape
    assert run["device"] == "mps"


def test_a_commit_landing_mid_run_is_named(run_rig, monkeypatch):
    rig = run_rig
    heads = iter(["a" * 40, "b" * 40])
    monkeypatch.setattr(phase39_ctx, "git_sha", lambda: next(heads))
    phase39_ctx.run(root=rig.root, **rig.paths, readings=("k0",), slots=("pet_name",))
    run = _sidecar(phase39_ctx.run_sidecar(rig.root))
    assert (run["git_sha_at_launch"], run["git_sha_at_end"]) == ("a" * 40, "b" * 40)
    assert run["head_moved_during_run"] is True


def test_a_crash_mid_scoring_leaves_an_open_start_that_reconcile_closes(run_rig):
    """The copy dies at the third reading's first question, after two readings landed."""
    rig = run_rig
    rig.crash = lambda reading: reading == READINGS[2]
    with pytest.raises(RuntimeError, match="copy died mid-scoring"):
        phase39_ctx.run(root=rig.root, **rig.paths)
    landed = {r: phase39_ctx.reading_sidecar(rig.root, r) for r in READINGS[:2]}
    digests = {r: phase39_ctx._sha256(p) for r, p in landed.items()}
    assert not phase39_ctx.reading_sidecar(rig.root, READINGS[2]).exists()
    assert not phase39_ctx.run_sidecar(rig.root).exists()
    lines = _lines(rig)
    assert [(x["event"], x["run_id"]) for x in lines] == [("start", phase39_ctx.RUN_ID)]
    assert phase39_ctx.RUN_ID in phase36_ledger.open_runs(lines)
    phase36_ledger.reconcile(**rig.paths)
    reconciled = _lines(rig)
    assert [x["event"] for x in reconciled] == ["start", "lost"]
    assert reconciled[1]["flag"] == phase36_ledger.LOST_FLAG
    assert phase36_ledger.open_runs(reconciled) == {}
    for reading, path in landed.items():  # intact after the crash and the reconcile
        assert phase39_ctx._sha256(path) == digests[reading]
        assert len(_sidecar(path)["questions"]) == 216
    # WR-01 (39-REVIEW-3): the refusal names every partial sidecar as kept evidence and points at
    # crash rule (ii); it never says the scoring has run.
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] partial sidecars") as refused:
        phase39_ctx.preflight(root=rig.root, ledger_path=rig.paths["ledger_path"])
    message = str(refused.value)
    assert "already run" not in message
    for path in (phase39_ctx.gate_sidecar(rig.root), *landed.values()):
        assert path.name in message
    for words in ("root-cause evidence", "never reused", "crash rule (ii)", "approved"):
        assert words in message, words
    assert _lines(rig) == reconciled


def test_a_refusal_inside_run_writes_no_ledger_line(run_rig, monkeypatch):
    rig = run_rig
    monkeypatch.setattr(phase39_ctx, "git_sha", lambda: "unknown")
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*HEAD"):
        phase39_ctx.run(root=rig.root, **rig.paths)
    assert not rig.paths["ledger_path"].exists()
    assert not rig.paths["heartbeat_path"].exists()
    assert rig.log == [] and rig.models == []


# =================================================================================================
# (5) Plan 05 Task 2: the rehearsal identity (D-21, D-27), written by run() before the first
# score; the disclosure of every later commit to a disclosed module; the real-root preflight.
# =================================================================================================

_DISCLOSED = ("scripts/phase39_ctx.py", "scripts/phase39_prereg.py")


def _identity(path, **shape):
    shape = {"readings": list(READINGS), "slots": list(SLOTS), **shape}
    return phase39_ctx.record_rehearsal(path, **shape)


def test_disclosed_modules_and_the_identity_path(tmp_path, monkeypatch):
    assert phase39_ctx.DISCLOSED_MODULES == _DISCLOSED
    assert set(_DISCLOSED) <= set(phase39_ctx.MODULES)
    assert phase39_ctx.rehearsal_identity_path() == _REAL_IDENTITY
    monkeypatch.setattr(phase39_ctx, "_ROOT", tmp_path)
    assert phase39_ctx.rehearsal_identity_path() == tmp_path / "data" / "phase39_rehearsal.json"


def test_record_rehearsal_keeps_the_first_identity_of_the_same_slice(tmp_path, capsys):
    import datetime

    path = tmp_path / "id.json"
    first = _identity(path, readings=["k0", "k78"], slots=["pet_name", "birth_year"])
    assert f"REHEARSAL RECORDED {_git('rev-parse', 'HEAD')}" in capsys.readouterr().out
    on = _sidecar(path)
    assert first == {"status": "recorded", **on}
    assert set(on) == {"git_sha", "module_sha256", "readings", "slots", "started_utc"}
    assert on["git_sha"] == _git("rev-parse", "HEAD")
    assert on["module_sha256"] == {
        rel: hashlib.sha256((_REPO / rel).read_bytes()).hexdigest() for rel in _DISCLOSED
    }
    assert (on["readings"], on["slots"]) == (["k0", "k78"], ["pet_name", "birth_year"])
    assert datetime.datetime.fromisoformat(on["started_utc"]).tzinfo is not None
    before = path.read_bytes()
    again = _identity(path, readings=("k0", "k78"), slots=("pet_name", "birth_year"))
    assert again == {"status": "kept", **on}
    assert f"REHEARSAL KEPT {on['git_sha']}" in capsys.readouterr().out
    assert path.read_bytes() == before
    # 38-REVIEW DR-02: a wider (or any other) slice would go undisclosed under the kept identity.
    for shape in (
        {"readings": ["k0", "k78"], "slots": list(SLOTS)},
        {"readings": list(READINGS), "slots": ["pet_name", "birth_year"]},
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*different slice.*DR-02"):
            _identity(path, **shape)
    assert path.read_bytes() == before


def test_the_identity_is_written_before_the_first_score(run_rig, tmp_path, monkeypatch):
    """A preflight refusal leaves no identity; a crash on the FIRST gate score leaves the identity
    and no sidecar; a rerun of the same slice keeps it; another slice refuses before the start."""
    rig = run_rig
    identity = tmp_path / "id.json"
    shape = {"readings": ("k0",), "slots": ("pet_name",)}

    def dirty(**kw):
        raise SystemExit("[phase39_ctx] dirty tree")

    monkeypatch.setattr(phase39_ctx, "refuse_if_dirty", dirty)
    with pytest.raises(SystemExit, match=r"dirty tree"):
        phase39_ctx.run(root=rig.root, **rig.paths, **shape, rehearsal_identity=identity)
    assert not identity.exists() and not rig.paths["ledger_path"].exists()
    monkeypatch.setattr(phase39_ctx, "refuse_if_dirty", lambda **kw: None)
    real = phase18_extraction.value_span_nll

    def dies(*args, **kwargs):
        rig.log.append(("died",))
        raise RuntimeError("scorer died")

    monkeypatch.setattr(phase18_extraction, "value_span_nll", dies)
    with pytest.raises(RuntimeError, match="scorer died"):
        phase39_ctx.run(root=rig.root, **rig.paths, **shape, rehearsal_identity=identity)
    assert rig.log == [("died",)]  # the crash came on the very first score
    assert identity.exists()
    assert list((rig.root / "data").iterdir()) == []
    assert [x["event"] for x in _lines(rig)] == ["start"]
    first = identity.read_bytes()
    monkeypatch.setattr(phase18_extraction, "value_span_nll", real)
    for name, kw in (("second", shape), ("third", {**shape, "slots": ("pet_name", "street")})):
        again = tmp_path / name
        (again / "data").mkdir(parents=True)
        paths = {"ledger_path": again / "ledger.jsonl", "heartbeat_path": again / "hb.jsonl"}
        if name == "second":
            assert phase39_ctx.run(root=again, **paths, **kw, rehearsal_identity=identity) == (
                "SCORED"
            )
        else:  # DR-02, refused BEFORE the ledger start line
            with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*DR-02"):
                phase39_ctx.run(root=again, **paths, **kw, rehearsal_identity=identity)
            assert not paths["ledger_path"].exists() and not paths["heartbeat_path"].exists()
        assert identity.read_bytes() == first


def _git_lines(*args):
    return [line for line in _git(*args).splitlines() if line]


def test_rehearsal_disclosure_lists_every_commit_to_a_disclosed_module():
    first = _git_lines("log", "--reverse", "--format=%H", "--", "tests/test_phase39_ctx.py")[0]
    identity = {
        "git_sha": first,
        "module_sha256": {
            rel: hashlib.sha256(_git("show", f"{first}:{rel}").encode() + b"\n").hexdigest()
            for rel in _DISCLOSED
        },
        "readings": list(READINGS),
        "slots": ["pet_name", "birth_year"],
        "started_utc": "2026-10-05T00:00:00+00:00",
    }
    head = _git("rev-parse", "HEAD")
    launch = phase39_ctx.module_sha256()
    disclosure = phase39_ctx.rehearsal_disclosure(
        identity, launch_git_sha=head, launch_module_sha256=launch
    )
    commits = disclosure["commits"]
    assert commits and disclosure["driver_changed"] is True
    assert disclosure["changed"] == {
        "scripts/phase39_ctx.py": True,
        "scripts/phase39_prereg.py": False,  # frozen at 9366134, before the first driver commit
    }
    assert disclosure["prereg_changed"] is False
    for commit in commits:
        touched = set(_git_lines("show", "--name-only", "--format=", commit["sha"]))
        assert commit["modules"] == [rel for rel in _DISCLOSED if rel in touched]
        assert commit["modules"], commit
        assert commit["reason"] == _git("log", "-1", "--format=%s", commit["sha"])
    assert _git_lines("log", "--format=%H", f"{first}..{head}", "--", *_DISCLOSED) == [
        c["sha"] for c in commits
    ]
    assert disclosure["slice_read"] == {
        "readings": list(READINGS),
        "slots": ["pet_name", "birth_year"],
    }
    assert disclosure["statement"] == (
        "The CPU rehearsal (39-07) read pet_name, birth_year under 8 readings, all their A2 "
        "entries, before the driver review and the MPS run (D-21, D-27)."
    )
    assert disclosure["launch_module_sha256"] == {rel: launch[rel] for rel in _DISCLOSED}
    assert (disclosure["rehearsal_git_sha"], disclosure["launch_git_sha"]) == (first, head)
    same = {**identity, "git_sha": head, "module_sha256": {r: launch[r] for r in _DISCLOSED}}
    equal = phase39_ctx.rehearsal_disclosure(same, launch_git_sha=head, launch_module_sha256=launch)
    assert equal["commits"] == [] and equal["driver_changed"] is False
    assert equal["changed"] == {rel: False for rel in _DISCLOSED}
    assert equal["prereg_changed"] is False
    drifted = {**same, "module_sha256": {**same["module_sha256"], _DISCLOSED[0]: "0" * 64}}
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*without a commit"):
        phase39_ctx.rehearsal_disclosure(drifted, launch_git_sha=head, launch_module_sha256=launch)


def test_preflight_on_the_real_root_requires_the_identity_and_no_prereg_drift(rig, monkeypatch):
    monkeypatch.setattr(phase39_ctx, "_ROOT", rig.root)
    path = phase39_ctx.rehearsal_identity_path()
    assert path == rig.root / "data" / "phase39_rehearsal.json"
    ledger = rig.paths["ledger_path"]
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*D-21/D-27: run the 39-07 rehearsal"):
        phase39_ctx.preflight(ledger_path=ledger)
    assert rig.launches == []
    # D-27: the prereg changed after the rehearsal — only Rafael's ruling lifts it.
    _identity(path, slots=["pet_name", "birth_year"])
    kept = _sidecar(path)
    path.unlink()
    drifted = {**kept, "module_sha256": {**kept["module_sha256"], _DISCLOSED[1]: "0" * 64}}
    path.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] D-27: .*Rafael's ruling"):
        phase39_ctx.preflight(ledger_path=ledger)
    # 38-REVIEW DR-03: a malformed identity refuses at preflight, not at emit.
    for malformed in ({}, {**kept, "module_sha256": {}}, [kept]):
        path.write_text(json.dumps(malformed), encoding="utf-8")
        with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*malformed.*DR-03"):
            phase39_ctx.preflight(ledger_path=ledger)
    assert not ledger.exists()
    path.unlink()
    _identity(path, slots=["pet_name", "birth_year"])
    pre = phase39_ctx.preflight(ledger_path=ledger)
    assert pre["device"] == "mps"
    head = _git("rev-parse", "HEAD")
    disclosure = pre["rehearsal_disclosure"]
    assert (disclosure["rehearsal_git_sha"], disclosure["launch_git_sha"]) == (head, head)
    assert disclosure["commits"] == [] and disclosure["driver_changed"] is False
    assert disclosure["slice_read"]["slots"] == ["pet_name", "birth_year"]
    assert not ledger.exists()


# =================================================================================================
# (6) Plan 05 Task 3: AST censuses (never grep — the docstrings discuss these names). The pinned
# instruments are imported and called, never redefined; the copy's per-token values never feed a
# rank or an event (D-30 condition 2); the ledger discipline (D-03).
# =================================================================================================

_OWN_DEFS = {
    "span_nll_from_ids",
    "value_span_nll",
    "value_span_nll_mean",
    "exposure_rank",
    "_rank_of",
    "reference_set_for",
    "score_records",
    "aggregate_questions",
    "_pooled_rows",
    "draw_all",
}
_NEVER_CALLED = {"exposure_rank", "_rank_of", "inject_lora"}
_PINNED_CALLS = {
    "value_span_nll": "phase18_extraction",
    "reference_set_for": "phase18_extraction",
    "_guarded_span": "phase18_extraction",
    "_frame_preamble": "phase18_extraction",
    "score_records": "phase18_extraction",
    "draw_all": "phase14_recall",
    "assert_no_value_in_prompt": "phase14_recall",
    "_pooled_rows": "phase19_run",
}
_MUST_SEE = {
    "value_span_nll",
    "reference_set_for",
    "_guarded_span",
    "draw_all",
    "assert_no_value_in_prompt",
}
# 39-05 orchestrator amendment: every prereg door that decides a rank, a status or a class.
_RANK_CALLEES = {
    "rank_in_prefix",
    "n1",
    "median_rank",
    "rank_of_mean_nll",
    "rank_status",
    "count_status",
    "cell_statuses",
    "classify_cell",
    "disagreement_of",
    "class_counts",
    "tie_audit",
    "drop_audit",
    "baseline_table",
    "gate_reading",
}
_DESCRIPTIVE_KEYS = {"per_token", "suffix_nll_sum"}


def _phase39_sources():
    paths = sorted(_SCRIPTS.glob("phase39_*.py"))
    assert paths, "meta-guard: no scripts/phase39_*.py, the census would be vacuous"
    return [(p.relative_to(_REPO).as_posix(), p.read_text(encoding="utf-8")) for p in paths]


def _callee(call):
    return getattr(call.func, "id", None) or getattr(call.func, "attr", None)


def _calls(sources, name):
    return [
        (relpath, node)
        for relpath, source in sources
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and _callee(node) == name
    ]


def _instrument_failures(sources):
    """(failures, pinned calls seen) over ``(relpath, source)`` pairs."""
    failures, seen = [], set()
    for relpath, source in sources:
        for node in ast.walk(ast.parse(source)):
            where = f"{relpath}:{getattr(node, 'lineno', '?')}"
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in _OWN_DEFS:
                failures.append(f"{where}: defines {node.name}")
            if not isinstance(node, ast.Call):
                continue
            name = _callee(node)
            if name in _NEVER_CALLED:
                failures.append(f"{where}: calls {name}")
            if name in _PINNED_CALLS:
                owner = _PINNED_CALLS[name]
                if isinstance(node.func, ast.Attribute) and getattr(
                    node.func.value, "id", None
                ) == (owner):
                    seen.add(name)
                else:
                    failures.append(f"{where}: {name} not called as {owner}.{name}")
    return failures, seen


def _ctx_source():
    return (_SCRIPTS / "phase39_ctx.py").read_text(encoding="utf-8")


def test_ast_instruments_are_imported_not_redefined(tmp_path):
    failures, seen = _instrument_failures(_phase39_sources())
    assert failures == []
    assert _MUST_SEE <= seen  # non-vacuity: the pinned calls are there
    source = _ctx_source()
    for name, plant in (
        ("own_def.py", "\n\ndef reference_set_for(slot):\n    return [slot]\n"),
        (
            "exposure.py",
            "\n\ndef planted(nll):\n    return phase18_extraction.exposure_rank(nll)\n",
        ),
        ("bare.py", "\n\ndef planted(m):\n    return value_span_nll(m, 0, 0, slot=1, value=2)\n"),
        ("inject.py", "\n\ndef planted(m, c):\n    inject_lora(m, c)\n"),
        ("draw_def.py", "\n\ndef draw_all(*args):\n    return args\n"),
    ):
        planted = _planted(tmp_path, source, source + plant, name)
        assert _instrument_failures([(name, planted)])[0], name


def _sampler_failures(sources):
    failures = []
    for relpath, source in sources:
        for node in ast.walk(ast.parse(source)):
            if (
                isinstance(node, ast.Attribute)
                and node.attr == "replace"
                and getattr(node.value, "id", None) == "os"
            ):
                failures.append(f"{relpath}:{node.lineno}: os.replace")
    for relpath, call in _calls(sources, "draw_all"):
        for kw in call.keywords:
            if kw.arg in ("temperature", "top_p"):
                failures.append(f"{relpath}:{call.lineno}: draw_all({kw.arg}=)")
    return failures


def test_ast_no_os_replace_and_no_sampler_override(tmp_path):
    sources = _phase39_sources()
    assert _sampler_failures(sources) == []
    assert _calls(sources, "draw_all")  # non-vacuity: the draw call is there
    source = _ctx_source()
    for name, plant in (
        (
            "sampler.py",
            "\n\ndef planted(m, t, i, d, f):\n"
            "    phase14_recall.draw_all(m, t, i, d, f, 0, temperature=0.5)\n",
        ),
        (
            "top_p.py",
            "\n\ndef planted(m, t, i, d, f):\n"
            "    phase14_recall.draw_all(m, t, i, d, f, 0, top_p=0.9)\n",
        ),
        ("replace.py", "\n\ndef planted(a, b):\n    os.replace(a, b)\n"),
    ):
        planted = _planted(tmp_path, source, source + plant, name)
        assert _sampler_failures([(name, planted)]), name


def _caps_failures(sources):
    """(failures, check_unit_caps attribute calls): narrowed to that call (a whole-file regex
    reddened on an innocent local name in 38-07)."""
    failures, calls = [], []
    for relpath, call in _calls(sources, "check_unit_caps"):
        if not isinstance(call.func, ast.Attribute):
            continue
        calls.append(f"{relpath}:{call.lineno}")
        for kw in call.keywords:
            if kw.arg in ("adapters", "anchor_adapters"):
                failures.append(f"{relpath}:{call.lineno}: check_unit_caps({kw.arg}=)")
    return failures, calls


def test_ast_caps_never_get_the_raised_counts(tmp_path):
    failures, calls = _caps_failures(_phase39_sources())
    assert failures == []
    assert len(calls) == 1  # non-vacuity: preflight's one call
    source = _ctx_source()
    planted = _planted(
        tmp_path,
        source,
        source + '\n\ndef planted():\n    phase36_caps.check_unit_caps("E6", adapters=8)\n',
        "caps.py",
    )
    assert _caps_failures([("caps.py", planted)])[0]


def _reads_descriptive(node):
    if isinstance(node, ast.Subscript):
        key = node.slice
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
    ):
        key = node.args[0]
    else:
        return False
    return isinstance(key, ast.Constant) and key.value in _DESCRIPTIVE_KEYS


def _per_token_failures(sources):
    """(offending functions, rank-calling functions, per-token readers) over every FunctionDef: a
    function calling a rank / event door may not read "per_token" or "suffix_nll_sum"."""
    offending, rank_callers, readers = set(), set(), set()
    for relpath, source in sources:
        for function in ast.walk(ast.parse(source)):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            nodes = list(ast.walk(function))
            name = f"{relpath}:{function.name}"
            calls_rank = any(isinstance(n, ast.Call) and _callee(n) in _RANK_CALLEES for n in nodes)
            reads = any(_reads_descriptive(n) for n in nodes)
            if calls_rank:
                rank_callers.add(name)
            if reads:
                readers.add(name)
            if calls_rank and reads:
                offending.add(name)
    return offending, rank_callers, readers


def test_ast_per_token_values_never_feed_a_rank_or_event(tmp_path):
    offending, rank_callers, readers = _per_token_failures(_phase39_sources())
    assert offending == set()
    assert "scripts/phase39_ctx.py:run" in rank_callers  # non-vacuity: gate_reading
    assert rank_callers  # and the prereg's doors
    # Plan 06 (W1): the real readers, by name — never among the offenders.
    for reader in ("_descriptive_block", "_suffix_check"):
        assert f"scripts/phase39_ctx.py:{reader}" in readers, reader
        assert f"scripts/phase39_ctx.py:{reader}" not in offending, reader
    for caller in ("rank_rows", "_rank_block", "_classified"):
        assert f"scripts/phase39_ctx.py:{caller}" in rank_callers, caller
    source = _ctx_source()
    for name, plant, reader in (
        (
            "subscript.py",
            "\n\ndef planted(nll, row, taught, others):\n"
            '    return phase38_prereg.rank_in_prefix(row["per_token"], taught, others)\n',
            True,
        ),
        (
            "get.py",
            "\n\ndef planted(cells, row):\n"
            '    return phase38_rank.gate_reading("k0", row.get("suffix_nll_sum"))\n',
            True,
        ),
    ):
        planted = _planted(tmp_path, source, source + plant, name)
        bad, _, _ = _per_token_failures([(name, planted)])
        assert bad == {f"{name}:planted"}, name
    # The reader side, planted at this plan (W1): no committed function subscripts these keys
    # yet (span_nll_tokens binds locals and returns them as dict-literal keys); plan 06 adds the
    # leg asserting the real _descriptive_block is a reader.
    planted = _planted(
        tmp_path,
        source,
        source + '\n\ndef _planted_reader(row):\n    return row["per_token"]\n',
        "reader.py",
    )
    bad, _, readers = _per_token_failures([("reader.py", planted)])
    assert "reader.py:_planted_reader" in readers
    assert "reader.py:_planted_reader" not in bad


def _ledger_calls(source):
    return {
        node.func.attr
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and getattr(node.func.value, "id", None) == "phase36_ledger"
    }


def test_ast_ledger_calls_are_the_allowed_five(tmp_path):
    """D-03: the committed stop is require_launch's; the driver never calls phase36_ledger.rule."""
    allowed = {"run_id", "read_ledger", "open_runs", "require_launch", "append"}
    source = _ctx_source()
    assert _ledger_calls(source) == allowed
    planted = _planted(
        tmp_path,
        source,
        source + '\n\ndef planted():\n    phase36_ledger.rule("E6", seconds=1)\n',
        "rule.py",
    )
    assert _ledger_calls(planted) - allowed == {"rule"}


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


# =================================================================================================
# (7) Plan 06 Task 1: rank_rows and the CPU cross-check (D-20, D-30a) — NLL and rank only,
# descriptive, write-once, no ledger line.
# =================================================================================================

_SHAPE = {"readings": ("k0", "k78"), "slots": ("pet_name", "birth_year")}


def test_rank_rows_reads_nll_mean_only():
    rows = {
        "a": {"nll_mean": 1.0, "nll_sum": 3.0, "per_token": [1.0] * 3, "suffix_nll_sum": 2.0},
        "b": {"nll_mean": 0.5, "nll_sum": 9.0, "per_token": [0.5], "suffix_nll_sum": None},
        "c": {"nll_mean": 2.0, "nll_sum": 0.1, "per_token": [2.0], "suffix_nll_sum": None},
    }
    expected = phase38_prereg.rank_in_prefix({"a": 1.0, "b": 0.5, "c": 2.0}, "a", ["b", "c"])
    assert phase39_ctx.rank_rows(rows, "a") == expected == 2
    moved = {
        "a": {**rows["a"], "per_token": [99.0] * 3, "suffix_nll_sum": 99.0, "nll_sum": 99.0},
        "b": {**rows["b"], "per_token": [0.0], "nll_sum": 0.0},
        "c": {**rows["c"], "per_token": [0.0], "nll_sum": 0.0},
    }
    assert phase39_ctx.rank_rows(moved, "a") == expected
    assert phase39_ctx.rank_rows({**rows, "b": {**rows["b"], "nll_mean": 1.5}}, "a") == 1


def _fake_pinned_suffix(tok):
    """The pinned span_nll_from_ids on the run rig's FakeModel: the taught suffix in A2's exact
    context gets the same expression the rig's copy uses (nll * suffix length)."""
    taught_ids = {slot: list(tok.encode(value)) for slot, value in TAUGHT.items()}

    def span_nll_from_ids(model, context_ids, value_ids, device):
        value_ids, context_ids = list(value_ids), list(context_ids)
        for slot, ids in taught_ids.items():
            cut = len(ids) - len(value_ids)
            if cut >= 1 and ids[cut:] == value_ids and context_ids[-cut:] == ids[:cut]:
                context = hashlib.sha256(repr(context_ids[:-cut]).encode()).hexdigest()
                nll = 1.0 + _offset(f"{model.reading}|{context}", TAUGHT[slot])
                n = len(value_ids)
                return {"n_scored": n, "nll_sum": nll * n, "nll_mean": nll}
        raise AssertionError("not a taught suffix in an A2 context")

    return span_nll_from_ids


@pytest.fixture
def crosscheck_rig(run_rig, tok, monkeypatch):
    monkeypatch.setattr(phase18_extraction, "span_nll_from_ids", _fake_pinned_suffix(tok))
    return run_rig


def _cpu_ranks_from_sidecars(rig, readings):
    """R_q and (ii) ranks recomputed in the test from the reading sidecars, nll_mean only."""
    rq, minted = {}, {}
    for reading in readings:
        blob = _sidecar(phase39_ctx.reading_sidecar(rig.root, reading))
        rq[reading], minted[reading] = {}, {}
        for key, q in blob["questions"].items():
            taught = TAUGHT[q["slot"]]
            nll = {c: row["nll_mean"] for c, row in q["references"].items()}
            rq[reading][key] = phase38_prereg.rank_in_prefix(
                nll, taught, [c for c in nll if c != taught]
            )
            ii = {taught: nll[taught], **{c: row["nll_mean"] for c, row in q["minted"].items()}}
            minted[reading][key] = phase38_prereg.rank_in_prefix(ii, taught, list(q["minted"]))
    return rq, minted


def test_crosscheck_writes_the_cpu_sidecar_once(crosscheck_rig, capsys):
    rig = crosscheck_rig
    assert phase39_ctx.run(root=rig.root, **rig.paths, **_SHAPE) == "SCORED"
    ledger = rig.paths["ledger_path"].read_bytes()
    loaded = len(rig.models)
    out = phase39_ctx.crosscheck(root=rig.root, device="cpu")
    assert out == phase39_ctx.cpu_sidecar(rig.root)
    assert f"CROSSCHECK DONE {out}" in capsys.readouterr().out
    cpu = _sidecar(out)
    assert set(cpu) == {
        "device",
        "torch_version",
        "started_utc",
        "finished_utc",
        "gate",
        "rq",
        "minted",
        "suffix_equality",
    }
    assert cpu["device"] == "cpu"
    assert rig.models[loaded:] == [(r, "cpu") for r in _SHAPE["readings"]]
    gate = _sidecar(phase39_ctx.gate_sidecar(rig.root))
    assert cpu["gate"] == {
        r: {s: gate["rows"][r][s]["rank"] for s in _SHAPE["slots"]} for r in _SHAPE["readings"]
    }
    rq, minted = _cpu_ranks_from_sidecars(rig, _SHAPE["readings"])
    assert (cpu["rq"], cpu["minted"]) == (rq, minted)
    run = _sidecar(phase39_ctx.run_sidecar(rig.root))
    compared = len(run["entries"]) * len(_SHAPE["readings"])
    assert compared == 2 * 54
    assert cpu["suffix_equality"] == {"compared": compared, "equal": compared, "unequal": []}
    assert rig.paths["ledger_path"].read_bytes() == ledger  # D-20: no ledger line
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*write-once"):
        phase39_ctx.crosscheck(root=rig.root, device="cpu")
    assert len(rig.models) == loaded + len(_SHAPE["readings"])


def test_crosscheck_refuses_a_gate_failed_or_missing_run(crosscheck_rig, tmp_path):
    rig = crosscheck_rig
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*no E6 run"):
        phase39_ctx.crosscheck(root=tmp_path, device="cpu")
    rig.table[("k78", "pet_name", TAUGHT["pet_name"])] = 3.0
    assert phase39_ctx.run(root=rig.root, **rig.paths, **_SHAPE) == "GATE_FAILED"
    loaded = len(rig.models)
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*GATE_FAILED, not SCORED"):
        phase39_ctx.crosscheck(root=rig.root, device="cpu")
    assert not phase39_ctx.cpu_sidecar(rig.root).exists()
    assert len(rig.models) == loaded


def test_crosscheck_suffix_check_called_directly(fake_lm, tok, entries):
    for index in (0, 120):
        _, entry = entries[index]
        slot = entry["slot"]
        taught = TAUGHT[slot]
        refs = phase39_ctx.score_question(
            fake_lm,
            tok,
            "cpu",
            entry,
            list(phase18_extraction.reference_set_for(slot)),
            taught=taught,
            state={},
        )
        assert phase39_ctx._suffix_check(fake_lm, tok, "cpu", entry, refs, taught) is True
        bumped = math.nextafter(refs[taught]["suffix_nll_sum"], math.inf)
        off = {**refs, taught: {**refs[taught], "suffix_nll_sum": bumped}}
        assert phase39_ctx._suffix_check(fake_lm, tok, "cpu", entry, off, taught) is False


def test_crosscheck_suffix_equality_on_a_cpu_model(tmp_path, fake_lm, tok, entries, monkeypatch):
    """The real copy and the real pinned function on fake_lm: every compared suffix is equal."""

    @contextlib.contextmanager
    def reading_model(reading, device):
        yield fake_lm, tok, _FORBID

    monkeypatch.setattr(phase39_ctx, "reading_model", reading_model)
    in_slot = [i for i, e in entries if e["slot"] == "pet_name"]
    sidecar = phase39_ctx.run_sidecar(tmp_path)
    sidecar.parent.mkdir(parents=True)
    sidecar.write_text(
        json.dumps(
            {"status": "SCORED", "readings": ["k0"], "slots": ["pet_name"], "entries": in_slot}
        ),
        encoding="utf-8",
    )
    cpu = _sidecar(phase39_ctx.crosscheck(root=tmp_path, device="cpu"))
    assert cpu["suffix_equality"] == {"compared": 27, "equal": 27, "unequal": []}
    assert set(cpu["rq"]["k0"]) == {str(i) for i in in_slot}
    assert set(cpu["gate"]["k0"]) == {"pet_name"}


# =================================================================================================
# (8) Plan 06 Task 2: the per-cell blocks (R_a, R_q, G_a, G_q), the classification through the
# prereg's one cell door (39-06 amendment: cells / classify_cell / class_counts / tie_audit /
# baseline_table), and the descriptive blocks. Every number recomputed here through the prereg.
# =================================================================================================

# k0 (the reference), two prefix cells, M2 and adapter-off; person_name holds the committed k8 G_q
# exact margin tie.
_SCORED_SHAPE = {
    "readings": ("k0", "k8", "k78", "M2", "adapter_off"),
    "slots": ("person_name", "pet_name"),
}


@pytest.fixture
def scored_rig(crosscheck_rig):
    """A SCORED fake run on _SCORED_SHAPE plus its CPU cross-check, on the tmp rig."""
    rig = crosscheck_rig
    assert phase39_ctx.run(root=rig.root, **rig.paths, **_SCORED_SHAPE) == "SCORED"
    phase39_ctx.crosscheck(root=rig.root, device="cpu")
    rig.run = _sidecar(phase39_ctx.run_sidecar(rig.root))
    rig.gate = _sidecar(phase39_ctx.gate_sidecar(rig.root))
    return rig


def _slot_questions(blob, slot):
    return sorted(
        (q for q in blob["questions"].values() if q["slot"] == slot), key=lambda q: q["index"]
    )


def _fact_id(slot):
    return next(f.id for f in phase14_factset.LOCKED_FACTS if f.slot == slot)


def test_readings_block_recomputes_through_the_prereg(scored_rig):
    rig = scored_rig
    K = phase39_prereg.K
    committed = phase38_prereg.committed_gate_ranks()
    blocks = phase39_ctx._reading_blocks(rig.root, rig.run, rig.gate)
    assert list(blocks) == list(_SCORED_SHAPE["readings"])
    values = phase39_ctx._cell_values(blocks)
    for reading in _SCORED_SHAPE["readings"]:
        blob = _sidecar(phase39_ctx.reading_sidecar(rig.root, reading))
        draws = phase39_ctx._a2_draws(reading)
        assert list(blocks[reading]) == list(_SCORED_SHAPE["slots"])
        for slot in _SCORED_SHAPE["slots"]:
            block, taught, fact_id = blocks[reading][slot], TAUGHT[slot], _fact_id(slot)
            assert (block["taught"], block["fact_id"]) == (taught, fact_id)
            assert block["R_a"] == committed[reading][slot]["rank"]
            assert block["R_a"] == rig.gate["rows"][reading][slot]["rank"]
            questions = _slot_questions(blob, slot)
            assert len(questions) == phase39_prereg.N_QUESTIONS
            ranks = [
                phase38_prereg.rank_in_prefix(
                    {c: r["nll_mean"] for c, r in q["references"].items()},
                    taught,
                    [c for c in q["references"] if c != taught],
                )
                for q in questions
            ]
            rank = block["rank"]
            assert rank["indices"] == [q["index"] for q in questions]
            assert rank["ranks"] == ranks
            assert rank["n1"] == phase39_prereg.n1(ranks)
            assert rank["median"] == phase39_prereg.median_rank(ranks)
            nll = {
                c: [q["references"][c]["nll_mean"] for q in questions]
                for c in questions[0]["references"]
            }
            assert rank["rank_of_mean_nll"] == phase39_prereg.rank_of_mean_nll(
                nll, taught, [c for c in nll if c != taught]
            )
            # D-08: G_a re-derived from the anchor record the block carries.
            anchor = blob["anchor"][slot]
            assert block["anchor_record"] == anchor
            hits = phase18_extraction.score_records([anchor], {fact_id: taught})[0]["hits"]
            g_a = block["generation"]["G_a"]
            assert g_a["hits"] == hits and g_a["h"] == sum(hits)
            assert g_a["unit"] == phase39_prereg.unit_of(hits) == int(reading in _HIT_READINGS)
            assert g_a["rate"] == phase39_prereg.draw_rate(sum(hits), K)
            # G_q: the committed A2 draws, the count proved equal to gate 2.
            per_question = phase39_ctx._a2_question_hits(draws, fact_id, taught)
            assert len(per_question) == phase39_prereg.N_QUESTIONS
            g_q = block["generation"]["G_q"]
            assert g_q["per_question"] == per_question
            assert g_q["count"] == rig.run["gate2"]["rows"][reading][slot]["count"]
            assert g_q["count"] == sum(v > 0 for v in per_question.values())
            assert g_q["total"] == sum(per_question.values())
            assert g_q["rate"] == phase39_prereg.draw_rate(g_q["total"], len(per_question) * K)
            assert values[reading][slot] == {
                "R_a": block["R_a"],
                "R_q": rank["n1"],
                "G_a": g_a["unit"],
                "G_q": g_q["count"],
            }


def test_readings_a2_draws_load_once_per_reading(scored_rig, monkeypatch):
    rig = scored_rig
    calls = []
    real = phase39_ctx._a2_draws
    monkeypatch.setattr(
        phase39_ctx, "_a2_draws", lambda reading: calls.append(reading) or real(reading)
    )
    phase39_ctx._reading_blocks(rig.root, rig.run, rig.gate)
    assert calls == list(_SCORED_SHAPE["readings"])  # I2: once per reading, never per slot
    rows = real("k8")
    assert len(rows) == phase39_prereg.N_ENTRIES and {r["family"] for r in rows} == {"A2"}


def _row(nll, **extra):
    return {"nll_mean": nll, "nll_sum": nll * 2, "per_token": [nll, nll], **extra}


def test_readings_helpers_called_directly():
    taught = "T"
    questions = [
        {
            "index": i,
            "references": {"T": _row(t), "a": _row(a), "b": _row(b)},
            "minted": {"m": _row(m)},
        }
        for i, (t, a, b, m) in enumerate(
            ((1.0, 2.0, 3.0, 0.5), (2.5, 2.0, 3.0, 4.0), (1.0, 0.5, 0.7, 9.0))
        )
    ]
    block = phase39_ctx._rank_block(questions, taught)
    ranks = [1, 2, 3]
    assert block["indices"] == [0, 1, 2] and block["ranks"] == ranks
    assert block["n1"] == phase39_prereg.n1(ranks) == 1
    assert block["median"] == phase39_prereg.median_rank(ranks) == 2
    nll = {"T": [1.0, 2.5, 1.0], "a": [2.0, 2.0, 0.5], "b": [3.0, 3.0, 0.7]}
    assert block["rank_of_mean_nll"] == phase39_prereg.rank_of_mean_nll(nll, "T", ["a", "b"])
    assert block["minted"] == {"ranks": [2, 1, 1], "n1": 2, "median": 1}
    K = phase39_prereg.K
    slot, fact_id = "pet_name", _fact_id("pet_name")
    anchor = {
        "family": "anchor",
        "dose": None,
        "fact_id": fact_id,
        "slot": slot,
        "tier": None,
        "arm": "k8",
        "seed_index": 1,
        "prefix_text": None,
        "completions": ["no"] * (K - 2) + [f"it is {TAUGHT[slot]}"] * 2,
        "stopped": [True] * K,
    }
    a2_hits = {"core_taught/0": 3, "core_taught/1": 0, "core_held_out/0": 1}
    generation = phase39_ctx._generation_block(anchor, a2_hits, TAUGHT[slot], fact_id, 2)
    hits = [False] * (K - 2) + [True] * 2
    assert generation["G_a"] == {
        "hits": hits,
        "unit": phase39_prereg.unit_of(hits),
        "h": 2,
        "rate": phase39_prereg.draw_rate(2, K),
    }
    assert generation["G_q"] == {
        "count": 2,
        "per_question": a2_hits,
        "total": 4,
        "rate": phase39_prereg.draw_rate(4, 3 * K),
    }
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*gate 2"):
        phase39_ctx._generation_block(anchor, a2_hits, TAUGHT[slot], fact_id, 3)


def _values(**by_reading):
    return {
        reading: {"pet_name": dict(zip(("R_a", "R_q", "G_a", "G_q"), v))}
        for reading, v in by_reading.items()
    }


def test_classify_helpers_called_directly():
    values = _values(k0=(1, 20, 1, 21), k8=(1, 3, 0, 13))
    out = phase39_ctx._decomposition(values, ("pet_name",))
    assert out["classification_reason"] is None
    for event in phase39_prereg.EVENTS:
        cell = phase39_prereg.cell_spec(event, "k8", "pet_name")
        expected = [
            phase39_prereg.classify_cell(cell, values["k8"]["pet_name"], values["k0"]["pet_name"])
        ]
        assert out["classification"][event]["cells"] == expected
        assert out["classification"][event]["counts"] == phase39_prereg.class_counts(expected)
    damage = out["classification"]["damage"]["cells"]
    assert out["drop_formula_audit"] == phase39_prereg.tie_audit(damage)
    assert out["drop_formula_audit_reason"] is None
    assert out["baseline"] is None
    assert out["baseline_reason"] == "partial slots: baseline_table needs every slot"
    # adapter-off is a reading but never a cell (D-11 i).
    off = phase39_ctx._decomposition({**values, **_values(adapter_off=(5, 0, 0, 0))}, ("pet_name",))
    assert off["classification"] == out["classification"]
    full = {r: {slot: values[r]["pet_name"] for slot in SLOTS} for r in values}
    whole = phase39_ctx._decomposition(full, SLOTS)
    assert whole["baseline"] == phase39_prereg.baseline_table(full["k0"])
    assert whole["baseline_reason"] is None
    assert len(whole["classification"]["collapse"]["cells"]) == len(SLOTS)


def test_classify_needs_k0():
    out = phase39_ctx._decomposition(_values(k8=(1, 3, 0, 13), k78=(2, 0, 0, 0)), ("pet_name",))
    for key in ("classification", "drop_formula_audit", "baseline"):
        assert out[key] is None
        assert out[f"{key}_reason"] == "k0 not scored"
    alone = phase39_ctx._decomposition(_values(k0=(1, 20, 1, 21)), ("pet_name",))
    assert alone["classification"] is None and alone["drop_formula_audit"] is None
    assert alone["classification_reason"].startswith("no cell reading scored")


def test_classify_on_the_committed_counts():
    """Ruling i through the driver: committed R_a x committed G_q over all 48 cells per event (R_q
    and G_a held at their k0 values so they decide nothing): the published disagreement counts
    and the G_q tie audit reported to Rafael before 'reviewed'."""
    ranks = phase38_prereg.committed_gate_ranks()
    counts = phase39_prereg.committed_a2_counts()
    n = phase39_prereg.N_QUESTIONS
    values = {
        reading: {
            slot: {
                "R_a": ranks[reading][slot]["rank"],
                "R_q": n,
                "G_a": 1,
                "G_q": counts[reading][slot],
            }
            for slot in SLOTS
        }
        for reading in phase39_prereg.CTX02_READINGS
    }
    out = phase39_ctx._decomposition(values, SLOTS)
    measured = {}
    for event in phase39_prereg.EVENTS:
        cells = out["classification"][event]["cells"]
        assert [(c["reading"], c["slot"]) for c in cells] == [
            (c["reading"], c["slot"]) for c in phase39_prereg.cells(event)
        ]
        assert len(cells) == 48
        for cell in cells:
            door = {f: cell[f] for f in ("event", "reading", "slot", "n", "reference")}
            assert cell == phase39_prereg.classify_cell(
                door, values[cell["reading"]][cell["slot"]], values["k0"][cell["slot"]]
            )
        counts_ = out["classification"][event]["counts"]
        assert counts_ == phase39_prereg.class_counts(cells)
        measured[event] = tuple(
            counts_[part][key]
            for part in ("combined", "prefixes", "M2")
            for key in ("disagreement_cells", "reverse_disagreement_cells", "undecided_cells")
        )
    assert measured == {
        "collapse": (9, 0, 0, 9, 0, 0, 0, 0, 0),
        "damage": (24, 0, 0, 24, 0, 0, 0, 0, 0),
    }
    audit = out["drop_formula_audit"]
    assert audit == phase39_prereg.tie_audit(out["classification"]["damage"]["cells"])
    assert audit["criterion"] is False
    assert audit["flips"] == []
    assert audit["exact_ties"] == [["k8", "person_name", "G_q"]]


def test_predicted_and_extras_are_descriptive(scored_rig):
    rig = scored_rig
    K = phase39_prereg.K
    blocks = phase39_ctx._reading_blocks(rig.root, rig.run, rig.gate)
    rank_record = _read(phase38_prereg.RANK_RECORD)["readings"]
    minted_ii = phase39_ctx._minted_ii(blocks)
    for reading in _SCORED_SHAPE["readings"]:
        blob = _sidecar(phase39_ctx.reading_sidecar(rig.root, reading))
        for slot in _SCORED_SHAPE["slots"]:
            block, taught = blocks[reading][slot], TAUGHT[slot]
            cells = rig.gate["cells"][reading][slot]
            questions = _slot_questions(blob, slot)
            per_question = block["generation"]["G_q"]["per_question"]
            d = block["descriptive"]
            predicted = d["predicted"]
            assert predicted["a"] == phase39_prereg.predicted_hit_rate(
                cells[taught]["pinned"]["nll_sum"]
            )
            assert predicted["a_observed"] == block["generation"]["G_a"]["h"] / K
            b = [
                {
                    "index": q["index"],
                    "predicted": phase39_prereg.predicted_hit_rate(
                        q["references"][taught]["suffix_nll_sum"]
                    ),
                    "observed": per_question[f"{q['tier']}/{q['seed_index']}"] / K,
                }
                for q in questions
            ]
            assert predicted["b_per_question"] == b
            assert predicted["b_mean_predicted"] == math.fsum(x["predicted"] for x in b) / len(b)
            assert predicted["b_observed"] == sum(per_question.values()) / (len(per_question) * K)
            assert "D-17" in predicted["caveat"] and "temperature, top-p" in predicted["caveat"]
            assert (
                "D-29" in predicted["conditioning"]
                and "prefix_text + completion" in predicted["conditioning"]
            )
            # D-23a: per-token values of every candidate in both contexts.
            assert d["per_token"]["anchor"] == {
                c: cell["copy"]["per_token"] for c, cell in cells.items()
            }
            assert set(d["per_token"]["anchor"]) == set(phase18_extraction.reference_set_for(slot))
            assert d["per_token"]["question"] == {
                str(q["index"]): {
                    c: row["per_token"] for c, row in {**q["references"], **q["minted"]}.items()
                }
                for q in questions
            }
            # D-11 (ii): the minted ranks beside the committed anchor-side rank at |R| = 8.
            size = phase39_prereg.MINTED_SET_SIZE
            assert minted_ii[reading][slot] == {
                **block["rank"]["minted"],
                "size": size,
                "anchor_side_rank": rank_record[reading][slot]["curve"][str(size)]["rank"],
            }
    # D-11 (i): adapter-off carries the four readings and enters no cell.
    assert set(blocks["adapter_off"]["pet_name"]) >= {"R_a", "rank", "generation"}
    out = phase39_ctx._decomposition(phase39_ctx._cell_values(blocks), _SCORED_SHAPE["slots"])
    for event in phase39_prereg.EVENTS:
        readings = {c["reading"] for c in out["classification"][event]["cells"]}
        assert readings == {"k8", "k78", "M2"}


# =================================================================================================
# (9) Plan 06 Task 3: build_record and emit — the write-once record, the cross-check block, the
# cost, provenance and every refusal. Statuses, classes, counts and the audit are recomputed here
# through the prereg's doors from the record as read back (sort_keys JSON).
# =================================================================================================

_COMMON_KEYS = {
    "front",
    "run_id",
    "status",
    "approval",
    "shape",
    "reconstruction",
    "gate",
    "gate2",
    "rehearsal_disclosure",
    "limitations",
    "not_measured",
    "context_b_instrument",
    "provenance",
}
_SCORED_KEYS = {
    "readings",
    "classification",
    "classification_reason",
    "drop_formula_audit",
    "drop_formula_audit_reason",
    "baseline",
    "baseline_reason",
    "adapter_off",
    "minted_ii",
    "cpu_crosscheck",
    "cost",
}
_D20 = "no generation cross-check: generation is seeded per device (D-20)"


def _record_path(rig):
    return rig.root / phase39_prereg.CTX_RECORD


def _record_values(record):
    return {
        reading: {
            slot: {
                "R_a": block["R_a"],
                "R_q": block["rank"]["n1"],
                "G_a": block["generation"]["G_a"]["unit"],
                "G_q": block["generation"]["G_q"]["count"],
            }
            for slot, block in by_slot.items()
        }
        for reading, by_slot in record["readings"].items()
    }


def test_emit_writes_the_record_once_through_the_prereg(scored_rig, monkeypatch, capsys):
    rig = scored_rig
    calls = []
    real = phase39_ctx._a2_draws
    monkeypatch.setattr(phase39_ctx, "_a2_draws", lambda r: calls.append(r) or real(r))
    returned = phase39_ctx.emit(root=rig.root)
    path = _record_path(rig)
    assert f"EMITTED SCORED {path}" in capsys.readouterr().out
    assert calls == list(_SCORED_SHAPE["readings"])  # I2: one load per reading
    record = _sidecar(path)
    assert record == json.loads(json.dumps(returned))
    assert set(record) == _COMMON_KEYS | _SCORED_KEYS
    assert record["status"] == "SCORED" and record["front"] == "E6"
    assert record["run_id"] == phase39_ctx.RUN_ID
    assert record["approval"] == json.loads(json.dumps(phase39_prereg.approval_block()))
    assert {"reference_reading", "cell_readings"} <= set(record["approval"])
    assert record["shape"] == {
        "readings": list(_SCORED_SHAPE["readings"]),
        "slots": list(_SCORED_SHAPE["slots"]),
        "entries": rig.run["entries"],
    }
    assert record["gate"] == {k: rig.gate[k] for k in ("rows", "copy_equality", "cells")}
    some = record["gate"]["cells"]["k0"]["pet_name"][TAUGHT["pet_name"]]
    assert some["copy"]["per_token"]
    assert record["gate2"] == rig.run["gate2"]
    assert record["gate2"]["rows"] == json.loads(json.dumps(phase39_prereg.gate2()["rows"]))
    equality = rig.gate["copy_equality"]
    assert record["context_b_instrument"].endswith(
        f"gate-1 equality: {equality['cells_equal']} of {equality['cells_compared']}"
    )
    assert record["reconstruction"] == rig.run["reconstruction"]
    assert {r: set(s) for r, s in record["readings"].items()} == {
        r: set(_SCORED_SHAPE["slots"]) for r in _SCORED_SHAPE["readings"]
    }
    assert record["baseline"] is None
    assert record["baseline_reason"] == "partial slots: baseline_table needs every slot"
    assert record["classification_reason"] is None
    assert "never classified" in record["adapter_off"]
    size = phase39_prereg.MINTED_SET_SIZE
    rank_record = _read(phase38_prereg.RANK_RECORD)["readings"]
    for reading, by_slot in record["readings"].items():
        for slot, block in by_slot.items():
            assert record["minted_ii"][reading][slot] == {
                **block["rank"]["minted"],
                "size": size,
                "anchor_side_rank": rank_record[reading][slot]["curve"][str(size)]["rank"],
            }
    cpu = _sidecar(phase39_ctx.cpu_sidecar(rig.root))
    check = record["cpu_crosscheck"]
    assert check["criterion"] is False and check["generation"] == _D20
    assert (check["device"], check["torch_version"]) == (cpu["device"], cpu["torch_version"])
    n_questions = len(rig.run["entries"]) * len(_SCORED_SHAPE["readings"])
    assert check["gate_cells"] == len(_SCORED_SHAPE["readings"]) * len(_SCORED_SHAPE["slots"])
    assert check["rq_cells"] == check["minted_cells"] == n_questions
    for key in ("gate", "rq", "minted"):
        assert check[f"{key}_differing"] == 0 and check[f"{key}_differing_cells"] == []
    assert check["suffix_equality"] == cpu["suffix_equality"]
    assert cpu["suffix_equality"]["equal"] == n_questions
    # Cost: every number computed from the budget JSON, none typed (I1).
    budget = _read(phase39_prereg.BUDGET_RECORD)
    n = len(_SCORED_SHAPE["readings"])
    extra = (2 * n - n) * budget["unit_prices"]["adapter_setup_high"] / 3600
    cost = record["cost"]
    assert cost["run_hours"] == phase39_ctx._hours(rig.run["started_utc"], rig.run["finished_utc"])
    assert (cost["setups_priced"], cost["setups_run"]) == (n, 2 * n)
    assert cost["e6_projection_hours"] == phase39_prereg.E6_PROJECTION_HOURS
    assert cost["e6_stop_hours"] == phase39_prereg.E6_STOP_HOURS
    assert cost["extra_setup_hours"] == extra
    assert cost["projection_with_double_load_hours"] == phase39_prereg.E6_PROJECTION_HOURS + extra
    assert cost["within_stop"] is (
        phase39_prereg.E6_PROJECTION_HOURS + extra <= phase39_prereg.E6_STOP_HOURS
    )
    assert "I1" in cost["note"]
    assert record["limitations"] == list(phase39_prereg.ENTRIES["limitations"]["value"])
    assert record["not_measured"] == list(phase39_prereg.NOT_MEASURED)
    assert record["rehearsal_disclosure"] == {
        "this_is_the_rehearsal": True,
        "slice": {
            "readings": list(_SCORED_SHAPE["readings"]),
            "slots": list(_SCORED_SHAPE["slots"]),
        },
    }
    provenance = record["provenance"]
    assert provenance["run"] == {k: rig.run[k] for k in phase39_ctx.RUN_PROVENANCE_KEYS}
    assert provenance["run"]["device"] == rig.run["device"] == "mps"
    assert provenance["module_sha256_at_launch"] == rig.run["module_sha256_at_launch"]
    assert provenance["module_sha256"] == phase39_ctx.module_sha256()
    assert provenance["modules_changed_since_launch"] == []
    assert provenance["head_at_write"] == _git("rev-parse", "HEAD")
    assert provenance["sidecar_sha256"] == {
        "run": phase39_ctx._sha256(phase39_ctx.run_sidecar(rig.root)),
        "gate": rig.run["gate_sha256"],
        "readings": rig.run["reading_sha256"],
        "cpu": phase39_ctx._sha256(phase39_ctx.cpu_sidecar(rig.root)),
    }
    before = path.read_bytes()
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*REFUSING to overwrite"):
        phase39_ctx.emit(root=rig.root)
    assert path.read_bytes() == before


def test_emit_drop_formula_audit_is_recomputed(scored_rig):
    """Statuses, classes, counts and the D-33 audit recomputed through the prereg's doors from the
    record read back; the fake record's class counts are printed for the SUMMARY."""
    rig = scored_rig
    phase39_ctx.emit(root=rig.root)
    record = _sidecar(_record_path(rig))
    values = _record_values(record)
    for event in phase39_prereg.EVENTS:
        cells = record["classification"][event]["cells"]
        expected = [
            (c["reading"], c["slot"])
            for c in phase39_prereg.cells(event)
            if c["reading"] in values and c["slot"] in _SCORED_SHAPE["slots"]
        ]
        assert [(c["reading"], c["slot"]) for c in cells] == expected
        assert {c["reading"] for c in cells} == {"k8", "k78", "M2"}  # no k0, no adapter_off
        for cell in cells:
            door = {f: cell[f] for f in ("event", "reading", "slot", "n", "reference")}
            assert cell == phase39_prereg.classify_cell(
                door, values[cell["reading"]][cell["slot"]], values["k0"][cell["slot"]]
            )
        counts = record["classification"][event]["counts"]
        assert counts == json.loads(json.dumps(phase39_prereg.class_counts(cells)))
        combined = counts["combined"]
        print(
            f"FAKE {event}: cells {combined['cells']} disagreement {combined['disagreement_cells']}"
            f" reverse {combined['reverse_disagreement_cells']} undecided "
            f"{combined['undecided_cells']} by_class "
            f"{ {k: v for k, v in combined['by_class'].items() if v} }"
            f" prefixes {counts['prefixes']['cells']} M2 {counts['M2']['cells']}"
        )
    audit = record["drop_formula_audit"]
    damage = record["classification"]["damage"]["cells"]
    assert audit == json.loads(json.dumps(phase39_prereg.tie_audit(damage)))
    assert audit["criterion"] is False
    assert ["k8", "person_name", "G_q"] in audit["exact_ties"]  # the committed G_q exact tie
    print(f"FAKE audit: flips {audit['flips']} exact_ties {audit['exact_ties']}")


def test_emit_cpu_block_and_hours_called_directly():
    assert phase39_ctx._hours("2026-10-05T00:00:00+00:00", "2026-10-05T01:00:00+00:00") == 1.0
    blocks = {
        "k0": {
            "pet_name": {"rank": {"indices": [5, 9], "ranks": [1, 2], "minted": {"ranks": [1, 1]}}}
        }
    }
    cpu = {
        "device": "cpu",
        "torch_version": "t",
        "gate": {"k0": {"pet_name": 1}},
        "rq": {"k0": {"5": 1, "9": 3}},
        "minted": {"k0": {"5": 1, "9": 1}},
        "suffix_equality": {"compared": 2, "equal": 2, "unequal": []},
    }
    block = phase39_ctx._cpu_block(cpu, blocks, {"k0": {"pet_name": {"rank": 1}}})
    assert block == {
        "criterion": False,
        "device": "cpu",
        "torch_version": "t",
        "gate_cells": 1,
        "gate_differing": 0,
        "gate_differing_cells": [],
        "rq_cells": 2,
        "rq_differing": 1,
        "rq_differing_cells": [["k0", "pet_name", 9]],
        "minted_cells": 2,
        "minted_differing": 0,
        "minted_differing_cells": [],
        "suffix_equality": cpu["suffix_equality"],
        "generation": _D20,
    }


def test_emit_crosscheck_counts_a_differing_cpu_rank(crosscheck_rig, entries, monkeypatch):
    """One CPU NLL perturbed after the run: exactly that R_q cell differs in the record."""
    rig = crosscheck_rig
    shape = {"readings": ("k0",), "slots": ("pet_name",)}
    assert phase39_ctx.run(root=rig.root, **rig.paths, **shape) == "SCORED"
    index, entry = next((i, e) for i, e in entries if e["slot"] == "pet_name")
    taught = TAUGHT["pet_name"]
    blob = _sidecar(phase39_ctx.reading_sidecar(rig.root, "k0"))
    q = blob["questions"][str(index)]
    nll = {c: r["nll_mean"] for c, r in q["references"].items()}
    rank = phase38_prereg.rank_in_prefix(nll, taught, [c for c in nll if c != taught])
    moved = 10.0 if rank == 1 else -1.0
    context = phase18_extraction._guarded_span(entry)
    copy = phase39_ctx.span_nll_tokens

    def perturbed(model, context_ids, value_ids, device, *, suffix_from=None):
        row = copy(model, context_ids, value_ids, device, suffix_from=suffix_from)
        if list(context_ids) == context and suffix_from is not None:
            row = {**row, "nll_mean": moved}
        return row

    monkeypatch.setattr(phase39_ctx, "span_nll_tokens", perturbed)
    phase39_ctx.crosscheck(root=rig.root, device="cpu")
    record = phase39_ctx.emit(root=rig.root)
    check = record["cpu_crosscheck"]
    assert check["rq_differing"] == 1
    assert check["rq_differing_cells"] == [["k0", "pet_name", index]]
    assert check["gate_differing"] == 0
    assert check["suffix_equality"]["equal"] == check["suffix_equality"]["compared"] == 27


def _emit_existing(rig, monkeypatch):
    _record_path(rig).write_text("{}", encoding="utf-8")
    return "REFUSING to overwrite"


def _emit_no_run(rig, monkeypatch):
    phase39_ctx.run_sidecar(rig.root).unlink()
    return "no E6 run to emit"


def _emit_gate_bytes(rig, monkeypatch):
    path = phase39_ctx.gate_sidecar(rig.root)
    path.write_text(json.dumps(_sidecar(path), indent=1), encoding="utf-8")
    return r"phase39_ctx_gate\.json is not the bytes the run wrote"


def _emit_reading_bytes(rig, monkeypatch):
    path = phase39_ctx.reading_sidecar(rig.root, "k8")
    path.write_text(json.dumps(_sidecar(path), indent=1), encoding="utf-8")
    return r"phase39_ctx_k8\.json is not the bytes the run wrote"


def _emit_no_cpu(rig, monkeypatch):
    phase39_ctx.cpu_sidecar(rig.root).unlink()
    return "run crosscheck before emit"


def _emit_dirty(rig, monkeypatch):
    def dirty(**kw):
        raise SystemExit("[phase39_ctx] dirty tree")

    monkeypatch.setattr(phase39_ctx, "refuse_if_dirty", dirty)
    return "dirty tree"


def _emit_partial_on_the_real_root(rig, monkeypatch):
    monkeypatch.setattr(phase39_ctx, "_ROOT", rig.root)
    return "full READINGS x SLOTS"


def _emit_gate2_moved(rig, monkeypatch):
    rows = json.loads(json.dumps(rig.gate2["rows"]))
    rows["k8"]["pet_name"]["count"] += 1
    rig.gate2 = {**rig.gate2, "rows": rows}
    return "changed since launch"


_EMIT_REFUSALS = [
    _emit_existing,
    _emit_no_run,
    _emit_gate_bytes,
    _emit_reading_bytes,
    _emit_no_cpu,
    _emit_dirty,
    _emit_partial_on_the_real_root,
    _emit_gate2_moved,
]


@pytest.mark.parametrize("plant", _EMIT_REFUSALS, ids=[p.__name__ for p in _EMIT_REFUSALS])
def test_emit_refusals_write_nothing(scored_rig, monkeypatch, plant):
    rig = scored_rig
    reason = plant(rig, monkeypatch)
    planted = _record_path(rig).exists()
    before = sorted(p.name for p in (rig.root / "results").iterdir())
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*" + reason):
        phase39_ctx.emit(root=rig.root)
    assert sorted(p.name for p in (rig.root / "results").iterdir()) == before
    assert _record_path(rig).exists() is planted


def test_emit_a_gate_failed_run(crosscheck_rig, capsys):
    rig = crosscheck_rig
    rig.table[("k78", "pet_name", TAUGHT["pet_name"])] = 3.0
    assert phase39_ctx.run(root=rig.root, **rig.paths, **_SHAPE) == "GATE_FAILED"
    assert not phase39_ctx.cpu_sidecar(rig.root).exists()  # none required
    record = phase39_ctx.emit(root=rig.root)
    assert f"EMITTED GATE_FAILED {_record_path(rig)}" in capsys.readouterr().out
    assert set(record) == _COMMON_KEYS
    gate = _sidecar(phase39_ctx.gate_sidecar(rig.root))
    assert record["gate"] == {k: gate[k] for k in ("rows", "copy_equality", "cells")}
    assert record["gate"]["rows"]["k78"]["pet_name"]["equal"] is False
    assert record["gate2"] == _sidecar(phase39_ctx.run_sidecar(rig.root))["gate2"]
    assert set(record["provenance"]["sidecar_sha256"]) == {"run", "gate", "readings"}


def test_the_record_carries_the_rehearsal_disclosure(scored_rig, monkeypatch):
    rig = scored_rig
    monkeypatch.setattr(phase39_ctx, "_ROOT", rig.root)
    identity = phase39_ctx.rehearsal_identity_path()
    assert identity == rig.root / "data" / "phase39_rehearsal.json"
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*rehearsal.*missing|missing.*D-21"):
        phase39_ctx.build_record(rig.root)
    phase39_ctx.record_rehearsal(identity, readings=["k0", "k78"], slots=["pet_name", "birth_year"])
    record = phase39_ctx.build_record(rig.root)
    expected = phase39_ctx.rehearsal_disclosure(
        _sidecar(identity),
        launch_git_sha=rig.run["git_sha_at_launch"],
        launch_module_sha256=rig.run["module_sha256_at_launch"],
    )
    assert record["rehearsal_disclosure"] == expected
    assert record["rehearsal_disclosure"]["slice_read"]["slots"] == ["pet_name", "birth_year"]
    assert not _record_path(rig).exists()  # build_record writes nothing


# =================================================================================================
# (10) Plan 07 Task 1: render_report, report, main — the report is the record rendered, nothing
# else (CTX-03); the CLI calls each command with no argument from the repository root.
# =================================================================================================

_SECTIONS = [
    "# Phase 39 — E6 instrument × context 2×2",
    "## Status",
    "## Approval and cost (D-11, D-26, D-30)",
    "## Gate 1: committed anchor ranks and the copy's equality (D-18, D-30)",
    "## Gate 2: committed A2 counts re-derived (D-19)",
    "## The four readings per slot and adapter (D-13)",
    "## Baseline at k0 (ruling f)",
    "## Decomposition under collapse (D-15, D-16)",
    "## Decomposition under damage (D-15, D-16)",
    "## Instrument share and context share (CTX-03)",
    "## Reverse disagreement and undecided cells (ruling e, IN-01)",
    "## Drop-formula audit (D-33, descriptive)",
    "## Common unit and per-draw rates (D-07, descriptive)",
    "## Predicted vs observed hit rate (D-17, D-23c, D-29, descriptive)",
    "## Adapter-off (D-11 i, descriptive)",
    "## Minted sets under the full question at |R| = 8 (D-11 ii, D-26, descriptive)",
    "## CPU cross-check (D-20, descriptive)",
    "## Rehearsal disclosure (D-21, D-27)",
    "## Not measured (D-12, D-23d)",
    "## Limitations (D-22)",
    "## Provenance",
]
_GATE_FAILED_SECTIONS = [*_SECTIONS[:5], *_SECTIONS[-4:]]
_KEYS = ("R_a", "R_q", "G_a", "G_q")


def _emitted(rig):
    phase39_ctx.emit(root=rig.root)
    return _sidecar(_record_path(rig))


def _headings(text):
    return re.findall(r"^#{1,2} .+$", text, flags=re.M)


def _section(text, heading):
    start = text.index(heading + "\n")
    end = text.find("\n## ", start + len(heading))
    return text[start : end if end != -1 else len(text)]


def _gfm_cells(line):
    return re.split(r"(?<!\\)\|", line.strip())[1:-1]


def _assert_gfm_tables(text):
    """Every table's header, delimiter and body rows have the same cell count, so GFM renders
    them as tables (an unescaped pipe inside a cell, e.g. |R|, adds cells)."""
    lines = text.splitlines()
    tables = 0
    for i, line in enumerate(lines[:-1]):
        if line.startswith("|") and re.fullmatch(r"\|(---\|)+", lines[i + 1]):
            tables += 1
            width = len(_gfm_cells(lines[i + 1]))
            assert len(_gfm_cells(line)) == width, line
            body = lines[i + 2 :]
            end = next((j for j, x in enumerate(body) if not x.startswith("|")), len(body))
            for row in body[:end]:
                assert len(_gfm_cells(row)) == width, row
    assert tables


def _tables(section):
    """Each GFM table of ``section``: its body rows (header and delimiter dropped) as lists of
    stripped cell strings."""
    tables, current = [], None
    for line in section.splitlines():
        if line.startswith("|"):
            if current is None:
                current = []
                tables.append(current)
            current.append([c.strip() for c in _gfm_cells(line)])
        else:
            current = None
    return [table[2:] for table in tables]


def _fraction(cell):
    return tuple(int(x) for x in re.fullmatch(r"(\d+)/(\d+)", cell).groups())


def _count_of(cell):
    return tuple(int(x) for x in re.fullmatch(r"(\d+) of (\d+)", cell).groups())


def test_render_report_renders_the_scored_record(scored_rig):
    record = _emitted(scored_rig)
    text = phase39_ctx.render_report(record)
    assert _headings(text) == _SECTIONS
    _assert_gfm_tables(text)
    assert "\n".join(phase39_ctx._scored_sections(record)) in text
    # Approval and cost: D-11 verbatim, the projection steps, the stop, the cost block.
    approval = _section(text, _SECTIONS[2])
    assert phase39_prereg.D11_RULING in approval
    for step, hours in record["approval"]["projection_steps"].items():
        assert f"- projection step {step}: {hours!r}" in approval
    assert f"- e6_stop_hours: {record['approval']['e6_stop_hours']!r}" in approval
    for key, value in record["cost"].items():
        assert f"- cost {key}: {value!r}" in approval
    # Gate 1: the rows, then the copy sentence with cells compared and equal.
    gate1 = _section(text, _SECTIONS[3])
    (gate_rows,) = _tables(gate1)
    rows = record["gate"]["rows"]
    assert [r[:2] for r in gate_rows] == [
        [reading, slot] for reading in _SCORED_SHAPE["readings"] for slot in _SCORED_SHAPE["slots"]
    ]
    for r in gate_rows:
        row = rows[r[0]][r[1]]
        assert [int(r[2]), int(r[3]), int(r[4]), r[5]] == [
            row["n_references"],
            row["rank"],
            row["committed_rank"],
            str(row["equal"]),
        ]
    equality = record["gate"]["copy_equality"]
    assert (
        f"cells compared {equality['cells_compared']}, cells equal {equality['cells_equal']}"
        in gate1
    )
    assert record["context_b_instrument"] in gate1
    # Gate 2: every committed row, the WR-01 independent flag on the target row.
    (g2_rows,) = _tables(_section(text, _SECTIONS[4]))
    assert len(g2_rows) == len(READINGS) * len(SLOTS)
    for r in g2_rows:
        row = record["gate2"]["rows"][r[0]][r[1]]
        assert [int(r[2]), int(r[3]), int(r[4]), r[5]] == [
            row["count"],
            row["committed"],
            row["n_questions"],
            str(row["equal"]),
        ]
        assert r[6] == str(row.get("independent", "—"))
    # The four readings, parsed back and compared with the record cell by cell.
    (four,) = _tables(_section(text, _SECTIONS[5]))
    assert [(r[0].split(" ")[0], r[1]) for r in four] == [
        (reading, slot)
        for reading in READINGS
        if reading in record["readings"]
        for slot in SLOTS
        if slot in record["readings"][reading]
    ]
    for r in four:
        reading = r[0].split(" ")[0]
        assert (r[0] == f"{reading} (descriptive)") is (reading == "adapter_off")
        block = record["readings"][reading][r[1]]
        rank, ga, gq = block["rank"], block["generation"]["G_a"], block["generation"]["G_q"]
        assert int(r[2]) == block["R_a"]
        assert _fraction(r[3]) == (rank["n1"], len(rank["ranks"]))
        assert (int(r[4]), int(r[5])) == (rank["median"], rank["rank_of_mean_nll"])
        assert int(r[6]) == ga["unit"]
        assert (
            _fraction(r[7])
            == (ga["h"], len(ga["hits"]))
            == (ga["rate"]["successes"], phase39_prereg.K)
        )
        assert _fraction(r[8]) == (gq["count"], len(gq["per_question"]))
        assert _fraction(r[9]) == (gq["total"], gq["rate"]["n"])
    # Baseline: the record's reason on a partial slot set.
    assert f"No baseline table: {record['baseline_reason']}." in _section(text, _SECTIONS[6])
    # Decomposition: one row per door cell, statuses, values, k0 values, class, disagreement.
    for event, heading in zip(phase39_prereg.EVENTS, _SECTIONS[7:9], strict=True):
        (table,) = _tables(_section(text, heading))
        cells = record["classification"][event]["cells"]
        assert len(table) == len(cells)
        for r, cell in zip(table, cells, strict=True):
            assert r[:2] == [cell["reading"], cell["slot"]]
            for key, shown in zip(_KEYS, r[2:6], strict=True):
                status, value = re.fullmatch(r"(\w+) \((\d+)\)", shown).groups()
                assert (status, int(value)) == (cell["statuses"][key], cell["values"][key])
            assert [int(x) for x in r[6:10]] == [cell["k0"][key] for key in _KEYS]
            assert r[10:] == [cell["class"], str(cell["disagreement"])]
    # The shares: every outcome, of its cells and of its disagreement cells, per group and event.
    shares = _section(text, _SECTIONS[9])
    assert record["classification"]["collapse"]["counts"]["m2_label"] in shares
    (share_rows,) = _tables(shares)
    groups = ("prefixes", phase39_prereg.RETRAIN_READING, "combined")
    assert [r[:3] for r in share_rows] == [
        [event, group, name]
        for event in phase39_prereg.EVENTS
        for group in groups
        for name in phase39_prereg.OUTCOMES
    ]
    for r in share_rows:
        tally = record["classification"][r[0]]["counts"][r[1]]
        assert _count_of(r[3]) == (tally["by_class"][r[2]], tally["cells"])
        if r[2] in tally["disagreement_by_class"]:
            assert _count_of(r[4]) == (
                tally["disagreement_by_class"][r[2]],
                tally["disagreement_cells"],
            )
            share = tally["shares"][r[2]]
            assert r[5] == ("—" if share is None else repr(share))
        else:
            assert r[4] == r[5] == "—"
    for event in phase39_prereg.EVENTS:
        tally = record["classification"][event]["counts"]["combined"]
        d = tally["disagreement_cells"]
        (line,) = [x for x in shares.splitlines() if x.startswith(f"- {event}, combined: ")]
        for name, label in (
            ("INSTRUMENT_SUFFICIENT", "instrument share"),
            ("CONTEXT_SUFFICIENT", "context share"),
        ):
            share = tally["shares"][name]
            assert (
                f"{label} ({name}) {tally['disagreement_by_class'][name]} of {d} disagreement "
                f"cells (share {'—' if share is None else repr(share)})" in line
            )
    # Reverse disagreement and undecided cells, apart.
    apart = _section(text, _SECTIONS[10])
    (apart_rows,) = _tables(apart)
    for r in apart_rows:
        tally = record["classification"][r[0]]["counts"][r[1]]
        assert _count_of(r[2]) == (tally["reverse_disagreement_cells"], tally["cells"])
        assert _count_of(r[3]) == (tally["undecided_cells"], tally["cells"])
    assert "No reverse disagreement and no undecided cell under collapse." in apart
    # D-33: the exact tie listed apart from the differing counts, with the class by both formulas.
    audit = record["drop_formula_audit"]
    d33 = _section(text, _SECTIONS[11])
    assert ["k8", "person_name", "G_q"] in audit["exact_ties"]
    tie = next(c for c in audit["cells"] if (c["reading"], c["slot"]) == ("k8", "person_name"))
    assert tie["audits"]["G_q"]["differs"] is False
    assert (
        f"- `k8` `person_name` G_q: exact margin tie decided by strict >; class "
        f"{tie['class_committed']} by the committed formula, {tie['class_exact']} by the exact "
        "formula" in d33
    )
    differing = [r[:3] for table in _tables(d33) for r in table]
    assert ["k8", "person_name", "G_q"] not in differing
    assert differing == [
        [c["reading"], c["slot"], key]
        for c in audit["cells"]
        for key in _KEYS[1:]
        if c["audits"][key]["differs"]
    ]
    assert "Criterion: False" in d33
    assert "No count status changes between the two formulas." in d33
    # Rates, prediction, adapter-off, (ii), CPU cross-check.
    rates = _section(text, _SECTIONS[12])
    assert "1-vs-27" in rates and "clustering ignored" in rates
    (rate_rows,) = _tables(rates)
    for r in rate_rows:
        rate = record["readings"][r[0]][r[1]]["generation"]["G_q"]["rate"]
        assert r[-3:] == [
            repr(rate["rate"]),
            repr(rate["wilson_lower_95"]),
            repr(rate["wilson_upper_95"]),
        ]
    predicted = _section(text, _SECTIONS[13])
    block = record["readings"]["k0"]["pet_name"]["descriptive"]["predicted"]
    assert block["caveat"] in predicted and block["conditioning"] in predicted
    off = _section(text, _SECTIONS[14])
    assert record["adapter_off"] in off
    assert [r[0] for r in _tables(off)[0]] == list(_SCORED_SHAPE["slots"])
    (minted,) = _tables(_section(text, _SECTIONS[15]))
    for r in minted:
        ii = record["minted_ii"][r[0]][r[1]]
        assert (int(r[2]), _fraction(r[3]), int(r[5])) == (
            ii["size"],
            (ii["n1"], len(ii["ranks"])),
            ii["anchor_side_rank"],
        )
    cpu = _section(text, _SECTIONS[16])
    check = record["cpu_crosscheck"]
    assert f"{check['rq_differing']} of {check['rq_cells']}" in cpu
    suffix = check["suffix_equality"]
    assert f"{suffix['equal']} of {suffix['compared']}" in cpu and _D20 in cpu
    assert "This record IS the CPU rehearsal" in _section(text, _SECTIONS[17])
    not_measured = _section(text, _SECTIONS[18])
    assert all(f"- {item}" in not_measured for item in phase39_prereg.NOT_MEASURED)
    limitations = _section(text, _SECTIONS[19])
    assert all(f"- {item}" in limitations for item in record["limitations"])
    assert record["provenance"]["run"]["git_sha_at_launch"] in _section(text, _SECTIONS[20])


def test_render_report_other_branches_from_the_record(scored_rig):
    record = _emitted(scored_rig)
    # A flip, a reverse disagreement and an undecided cell planted in copies of the record.
    planted = json.loads(json.dumps(record))
    audit = planted["drop_formula_audit"]
    audit["flips"] = [["k8", "pet_name", "R_q"]]
    cell = next(c for c in audit["cells"] if (c["reading"], c["slot"]) == ("k8", "pet_name"))
    cells = planted["classification"]["collapse"]["cells"]
    cells[0].update({"class": phase39_prereg.REVERSE_DISAGREEMENT, "disagreement": False})
    cells[1].update({"class": "UNREACHABLE_AT_SIZE", "disagreement": None})
    text = phase39_ctx.render_report(planted)
    d33 = _section(text, "## Drop-formula audit (D-33, descriptive)")
    assert (
        f"- `k8` `pet_name` R_q: margin tie decided by rounding; class {cell['class_committed']} "
        f"by the committed formula, {cell['class_exact']} by the exact formula" in d33
    )
    assert "No count status changes" not in d33
    apart = _section(text, "## Reverse disagreement and undecided cells (ruling e, IN-01)")
    assert f"- collapse `{cells[0]['reading']}` `{cells[0]['slot']}`: REVERSE_DISAGREEMENT" in apart
    assert f"- collapse `{cells[1]['reading']}` `{cells[1]['slot']}`: UNREACHABLE_AT_SIZE" in apart
    assert "under collapse." not in apart
    # The full baseline table (ruling f), every slot and reading key with both events' status.
    full = json.loads(json.dumps(record))
    k0 = {slot: dict(zip(_KEYS, (1, 20, 1, 21))) for slot in SLOTS}
    full["baseline"] = json.loads(json.dumps(phase39_prereg.baseline_table(k0)))
    full["baseline_reason"] = None
    (baseline,) = _tables(_section(phase39_ctx.render_report(full), "## Baseline at k0 (ruling f)"))
    assert len(baseline) == len(SLOTS) * len(_KEYS)
    for r in baseline:
        row = full["baseline"][r[0]][r[1]]
        assert [int(r[2]), r[3], r[4]] == [row["value"], row["collapse"], row["damage"]]
    # Nothing classified: each decomposition section and the audit carry the record's reason.
    empty = json.loads(json.dumps(record))
    for key in ("classification", "drop_formula_audit"):
        empty.update({key: None, f"{key}_reason": "no cell reading scored: test"})
    empty_text = phase39_ctx.render_report(empty)
    assert _headings(empty_text) == _SECTIONS
    for heading in _SECTIONS[7:12]:
        assert "no cell reading scored: test" in _section(empty_text, heading)


def test_render_report_on_a_gate_failed_record(crosscheck_rig):
    rig = crosscheck_rig
    rig.table[("k78", "pet_name", TAUGHT["pet_name"])] = 3.0
    rig.ulp = ("k0", "birth_year", TAUGHT["birth_year"])
    assert phase39_ctx.run(root=rig.root, **rig.paths, **_SHAPE) == "GATE_FAILED"
    record = _emitted(rig)
    text = phase39_ctx.render_report(record)
    assert _headings(text) == _GATE_FAILED_SECTIONS
    _assert_gfm_tables(text)
    assert "GATE_FAILED" in _section(text, "## Status")
    gate1 = _section(text, _SECTIONS[3])
    (rows,) = _tables(gate1)
    assert len(rows) == len(_SHAPE["readings"]) * len(_SHAPE["slots"])
    assert [r[:2] for r in rows if r[5] == "False"] == [["k78", "pet_name"]]
    assert "- rank not reproduced: `k78` `pet_name`" in gate1
    assert f"- unequal cell: `k0` `birth_year` `{TAUGHT['birth_year']}`" in gate1
    assert len(_tables(_section(text, _SECTIONS[4]))[0]) == len(READINGS) * len(SLOTS)
    assert "This record IS the CPU rehearsal" in _section(text, _SECTIONS[17])
    assert "Decomposition" not in text and "Drop-formula audit" not in text


def test_render_report_disclosure_branches(scored_rig):
    record = _emitted(scored_rig)
    disclosure = {
        "statement": "The CPU rehearsal (39-07) read pet_name under 8 readings.",
        "slice_read": {"readings": list(READINGS), "slots": ["pet_name"]},
        "rehearsal_git_sha": "a" * 40,
        "rehearsal_module_sha256": {rel: "1" * 64 for rel in _DISCLOSED},
        "launch_git_sha": "b" * 40,
        "launch_module_sha256": {rel: "1" * 64 for rel in _DISCLOSED},
        "changed": {rel: False for rel in _DISCLOSED},
        "prereg_changed": False,
        "driver_changed": False,
        "commits": [],
    }
    empty = phase39_ctx.render_report({**record, "rehearsal_disclosure": disclosure})
    section = _section(empty, "## Rehearsal disclosure (D-21, D-27)")
    assert disclosure["statement"] in section and "a" * 40 in section and "b" * 40 in section
    assert (
        "No commit touched scripts/phase39_ctx.py or scripts/phase39_prereg.py between the "
        "rehearsal and the launch." in section
    )
    assert "This record IS the CPU rehearsal" not in section
    assert len(_tables(section)[0]) == len(_DISCLOSED)
    commit = {"sha": "c" * 40, "reason": "fix(39-07): why", "modules": [_DISCLOSED[0]]}
    changed = {
        **disclosure,
        "changed": {_DISCLOSED[0]: True, _DISCLOSED[1]: False},
        "driver_changed": True,
        "commits": [commit],
    }
    listed = _section(
        phase39_ctx.render_report({**record, "rehearsal_disclosure": changed}),
        "## Rehearsal disclosure (D-21, D-27)",
    )
    assert f"- `{'c' * 40}` fix(39-07): why (touched: {_DISCLOSED[0]})" in listed
    assert "No commit touched" not in listed
    rehearsal = phase39_ctx._disclosure_lines(record["rehearsal_disclosure"])
    assert rehearsal[0].startswith("This record IS the CPU rehearsal (D-21, D-27)")
    assert "person_name, pet_name" in rehearsal[0]


def test_report_helpers_called_directly():
    assert phase39_ctx._table(("a", "b"), [[1, "x"]]) == ["| a | b |", "|---|---|", "| 1 | x |", ""]
    escaped = phase39_ctx._table(("|R|",), [["a|b"]])
    assert (escaped[0], escaped[2]) == ("| \\|R\\| |", "| a\\|b |")
    assert phase39_ctx._slots({"street": 1, "pet_name": 2}) == ["pet_name", "street"]
    assert phase39_ctx._readings(["k78", "M2", "adapter_off", "k0", "k16"]) == [
        "k0",
        "k16",
        "k78",
        "M2",
        "adapter_off",
    ]


def test_report_writes_once_and_the_real_root_needs_a_committed_record(
    scored_rig, monkeypatch, capsys
):
    rig = scored_rig
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*phase39_ctx\.json is missing"):
        phase39_ctx.report(root=rig.root)
    record = _emitted(rig)
    out = rig.root / phase39_prereg.REPORT_RECORD
    monkeypatch.setattr(phase39_ctx, "_ROOT", rig.root)
    monkeypatch.setattr(phase39_ctx, "_tracked_and_clean", lambda rel: False)
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*committed and unmodified"):
        phase39_ctx.report()
    assert not out.exists()
    monkeypatch.setattr(phase39_ctx, "_tracked_and_clean", lambda rel: True)
    assert phase39_ctx.report() == out  # the real-root branch, on the rig root
    assert out.read_text(encoding="utf-8") == phase39_ctx.render_report(record)
    out.unlink()
    monkeypatch.undo()
    assert phase39_ctx.report(root=rig.root) == out
    assert f"REPORT {out}" in capsys.readouterr().out
    assert out.read_text(encoding="utf-8") == phase39_ctx.render_report(record)
    before = out.read_bytes()
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*REFUSING to overwrite"):
        phase39_ctx.report(root=rig.root)
    assert out.read_bytes() == before


def test_report_tracked_and_clean_reads_git():
    assert phase39_ctx._tracked_and_clean("scripts/phase39_prereg.py") is True
    assert phase39_ctx._tracked_and_clean("results/phase39_never_written.json") is False


def test_the_full_fake_chain_through_the_commands(crosscheck_rig):
    rig = crosscheck_rig
    assert phase39_ctx.run(root=rig.root, **rig.paths, **_SCORED_SHAPE) == "SCORED"
    phase39_ctx.crosscheck(root=rig.root)
    phase39_ctx.emit(root=rig.root)
    out = phase39_ctx.report(root=rig.root)
    assert out == rig.root / phase39_prereg.REPORT_RECORD
    artifacts = (
        phase39_ctx.run_sidecar(rig.root),
        phase39_ctx.gate_sidecar(rig.root),
        phase39_ctx.cpu_sidecar(rig.root),
        _record_path(rig),
        out,
    )
    assert all(path.exists() for path in artifacts)
    record = _sidecar(_record_path(rig))
    assert out.read_text(encoding="utf-8") == phase39_ctx.render_report(record)
    assert [x["event"] for x in _lines(rig)] == ["start", "end"]


@pytest.mark.parametrize("command", ["preflight", "run", "crosscheck", "emit", "report"])
def test_main_dispatches_with_no_arguments_from_the_repo(tmp_path, monkeypatch, command):
    real = getattr(phase39_ctx, command)
    seen = []

    def recorder(*args, **kwargs):
        inspect.signature(real).bind(*args, **kwargs)
        seen.append((args, kwargs, pathlib.Path.cwd()))

    monkeypatch.setattr(phase39_ctx, command, recorder)
    monkeypatch.chdir(tmp_path)
    assert phase39_ctx.main([command]) == 0
    assert seen == [((), {}, phase39_ctx._REPO)]


@pytest.mark.parametrize("argv", [[], ["bogus"], ["run", "x"]])
def test_main_refuses_anything_else(argv):
    with pytest.raises(SystemExit) as raised:
        phase39_ctx.main(argv)
    assert raised.value.code == phase39_ctx.__doc__


def test_main_the_cli_exits_non_zero_on_a_bogus_command():
    done = subprocess.run(
        [sys.executable, "scripts/phase39_ctx.py", "bogus"], cwd=_REPO, capture_output=True
    )
    assert done.returncode != 0


def test_census_helpers_called_directly(tmp_path):
    # _kept_identity: absent, the same slice kept, another slice refused (DR-02).
    path = tmp_path / "id.json"
    shape = {"readings": ["k0"], "slots": ["pet_name"]}
    assert phase39_ctx._kept_identity(path, **shape) is None
    phase39_ctx.record_rehearsal(path, **shape)
    assert phase39_ctx._kept_identity(path, **shape) == _sidecar(path)
    with pytest.raises(SystemExit, match=r"^\[phase39_ctx\] .*different slice"):
        phase39_ctx._kept_identity(path, readings=["k0"], slots=["street"])
    # _classified: the door's cells only (no k0, no adapter-off), against k0.
    values = _values(k0=(1, 20, 1, 21), k8=(1, 3, 0, 13), adapter_off=(5, 0, 0, 0))
    for event in phase39_prereg.EVENTS:
        cell = phase39_prereg.cell_spec(event, "k8", "pet_name")
        assert phase39_ctx._classified(values, event) == [
            phase39_prereg.classify_cell(cell, values["k8"]["pet_name"], values["k0"]["pet_name"])
        ]
    # _cost: every number from the budget record (I1).
    run = {
        "readings": ["k0", "k8"],
        "started_utc": "2026-10-05T00:00:00+00:00",
        "finished_utc": "2026-10-05T00:30:00+00:00",
    }
    setup = _read(phase39_prereg.BUDGET_RECORD)["unit_prices"]["adapter_setup_high"]
    cost = phase39_ctx._cost(run)
    assert cost["run_hours"] == 0.5
    assert (cost["setups_priced"], cost["setups_run"]) == (2, 4)
    assert cost["extra_setup_hours"] == 2 * setup / 3600
    assert cost["projection_with_double_load_hours"] == (
        phase39_prereg.E6_PROJECTION_HOURS + 2 * setup / 3600
    )
    # _descriptive_block: exp(-nll_sum) beside the observed rates; per-token values carried.
    K = phase39_prereg.K
    gate = {
        "T": {"pinned": {"nll_sum": 2.0}, "copy": {"per_token": [1.0, 1.0]}},
        "a": {"pinned": {"nll_sum": 3.0}, "copy": {"per_token": [3.0]}},
    }
    questions = [
        {
            "index": 7,
            "tier": "core_taught",
            "seed_index": 0,
            "references": {"T": {"suffix_nll_sum": 1.0, "per_token": [0.5, 1.0]}},
            "minted": {"m": {"per_token": [4.0]}},
        }
    ]
    block = phase39_ctx._descriptive_block(gate, questions, {"core_taught/0": 3}, "T", 2)
    assert block["predicted"]["a"] == math.exp(-2.0)
    assert block["predicted"]["a_observed"] == 2 / K
    assert block["predicted"]["b_per_question"] == [
        {"index": 7, "predicted": math.exp(-1.0), "observed": 3 / K}
    ]
    assert block["predicted"]["b_mean_predicted"] == math.exp(-1.0)
    assert block["predicted"]["b_observed"] == 3 / K
    assert block["per_token"] == {
        "anchor": {"T": [1.0, 1.0], "a": [3.0]},
        "question": {"7": {"T": [0.5, 1.0], "m": [4.0]}},
    }


def test_census_every_phase39_ctx_function_has_a_cpu_test(tmp_path):
    source = (_SCRIPTS / "phase39_ctx.py").read_text(encoding="utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert {"render_report", "report", "main", "_tracked_and_clean"} <= {n.name for n in defs}
    assert _untested_functions("phase39_ctx", source, test_source) == []
    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase39_ctx", copied, test_source) == ["planted_untested"]
