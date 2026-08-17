"""A5 settled by measurement: rank-1 ablation is EXACTLY representable in the shipped format.

Research assumption A5 (``19-RESEARCH.md:943``) reads "structurally true (zeroing ``B[:, j]`` and
``A[j, :]`` leaves shapes intact) but **not run**". It decides whether M1 is representable at all —
if an ablated adapter could not be written back as a rank-8 artifact, the mechanism would have to
edit base weights, and every property the pin claims for M1 (the unrelaxed key/shape/scale audits,
the untouched adapter-off bit-identity control) would have to be re-earned by a different design.
So it is settled here, before the mechanism is pinned any further, by running it rather than by
arguing it.

Everything below is CPU-only and GPU-free, on a toy model built through the existing injection path
rather than by loading ``checkpoints/persona_adapter.pt`` — the checkpoints are gitignored, the
suite is CPU-only, and a 13.9M-parameter load has no place in ``make test``'s budget. The toy is
built at ``n_layer=6`` and the PRODUCTION ``LoRAConfig()`` (r=8, alpha=16.0) on purpose: those are
what ``component_index()`` derives its 288 addresses from, so a smaller fixture would prove the
operator on a surface the real artifact does not have.

NON-VACUITY, stated because it is the whole risk in a test like this. ``LoRALinear.lora_B`` starts
at ZERO (the identity gate, ``layer.py:30``), so an un-nudged adapter already has ``dW == 0`` and
already reproduces the base bit-for-bit. Every assertion here would then hold against an operator
that did nothing at all. ``_nudge_lora_b`` is what makes the pre-ablation delta non-zero, and the
pre-ablation inequality is asserted before the post-ablation equality in the bit-identity test —
without that pair the strongest-looking assertion in this file would be measuring the identity gate.
"""

import ast
import dataclasses
import importlib.util
import json
import math
import pathlib

import pytest
import torch
import torch.nn as nn

from personacore.checkpoint import export_adapter, load_adapter
from personacore.config import ModelConfig
from personacore.lora import (
    LoRAConfig,
    LoRALinear,
    adapter_disabled,
    inject_lora,
    load_adapter_weights,
    lora_state_dict,
)
from personacore.model import GPT

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name, relpath):
    """Load a ``scripts/`` driver by path — production code is never importable from tests/."""
    spec = importlib.util.spec_from_file_location(name, _ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


erasure = _load("phase19_erasure", "scripts/phase19_erasure.py")
extract_deltas = _load("extract_deltas", "scripts/extract_deltas.py")


def _tiny_config() -> ModelConfig:
    """A cheap CPU GPT that still carries the REAL wrap surface.

    ``n_layer`` stays at 6 — ``extract_deltas.KEYS`` enumerates ``blocks.0..5``, so a shallower toy
    would leave two thirds of the component index addressing projections the model does not have.
    ``vocab_size``/``eos_id`` stay at the LOCKED defaults; only the widths shrink.
    """
    return ModelConfig(block_size=32, n_layer=6, n_head=2, n_embd=16)


def _nudge_lora_b(model, seed: int) -> None:
    """Make the adapter delta non-zero so ablation is observable (test_lora_inject.py:65)."""
    torch.manual_seed(seed)
    with torch.no_grad():
        for name, p in model.named_parameters():
            if "lora_B" in name:
                nn.init.normal_(p)


def _build_pair(seed: int = 1234):
    """``(base, adapted, lora_cfg)`` — an un-injected base and the SAME weights with an adapter.

    ``run_bit_identity_control``'s construction (``phase14_recall.py:1505-1523``) in miniature:
    model A is never injected at all, model B loads the identical state dict and is injected
    AFTERWARDS (ARCHITECTURE Anti-pattern 1 — injection rewrites every wrapped projection's keys
    with a ``.base.`` infix, so injecting first would break every key).
    """
    torch.manual_seed(seed)
    cfg = _tiny_config()
    base = GPT(cfg)
    weights = {k: v.detach().clone() for k, v in base.state_dict().items()}

    adapted = GPT(cfg)
    adapted.load_state_dict(weights)
    lora_cfg = LoRAConfig()  # PRODUCTION r=8 / alpha=16.0 — the surface component_index() derives.
    n = inject_lora(adapted, lora_cfg)
    assert n == 6 * cfg.n_layer == len(extract_deltas.KEYS), (
        f"injected {n} wrappers but the committed enumeration holds {len(extract_deltas.KEYS)} "
        "projections — the toy does not carry the surface the component index addresses"
    )
    _nudge_lora_b(adapted, seed)
    return base.eval(), adapted.eval(), lora_cfg


def _artifact(model, lora_cfg) -> dict:
    """An ``export_adapter``-shaped artifact for the live model (``checkpoint.py:196``)."""
    return {
        "adapter": lora_state_dict(model),
        "lora_config": dataclasses.asdict(lora_cfg),
        "base_fingerprint": {"git_sha": "toyfixture", "step": 0, "val_loss": 1.0},
    }


def _logits(model, idx):
    with torch.no_grad():
        out, _ = model(idx)
    return out


def _max_abs_diff(a, b) -> float:
    return (a - b).abs().max().item()


def test_component_index_is_derived_and_addresses_only_wrapped_projections():
    """The index is exactly ``len(KEYS) * r`` distinct ``(layer, projection, j)`` addresses."""
    index = erasure.component_index()
    rank = erasure.PRODUCTION_RANK

    assert len(index) == len(extract_deltas.KEYS) * rank
    assert len(set(index)) == len(index), "the index holds a duplicate address"
    assert erasure.N_COMPONENTS == len(index), (
        "the module-scope census disagrees with the function it was derived from"
    )

    wrapped = {(layer, projection) for layer, projection, _key in extract_deltas.KEYS}
    for layer, projection, j in index:
        assert (layer, projection) in wrapped, (
            f"({layer}, {projection}) is not in the committed wrap enumeration"
        )
        assert 0 <= j < rank, f"component index j={j} is outside [0, {rank})"

    # Every wrapped projection contributes exactly r components — no projection is over- or
    # under-represented, which a naive product could hide behind a correct total.
    for cell in wrapped:
        assert sum(1 for layer, projection, _j in index if (layer, projection) == cell) == rank


def test_ablation_leaves_the_artifact_keys_shapes_and_scale_byte_identical():
    """The erased artifact is the same SHAPE of object — that is what makes M1 representable."""
    _base, adapted, lora_cfg = _build_pair()
    art = _artifact(adapted, lora_cfg)
    # An arbitrary, non-trivial subset: every third address, so several projections are partially
    # ablated and several are untouched.
    subset = erasure.component_index()[::3]

    erased = erasure.ablate_components(art, subset)

    assert erased["adapter"].keys() == art["adapter"].keys(), "the key set moved"
    for key, tensor in art["adapter"].items():
        assert erased["adapter"][key].shape == tensor.shape, f"{key} changed shape"
        assert erased["adapter"][key].dtype == tensor.dtype, f"{key} changed dtype"
    # `scale` is alpha/r and is invisible to the key and shape audits (W1, inject.py:113-118), so
    # it is checked on its own terms: the recorded config must be equal AND unmodified.
    assert erased["lora_config"] == art["lora_config"]
    assert erased["lora_config"]["alpha"] == lora_cfg.alpha
    assert erased["lora_config"]["r"] == lora_cfg.r
    assert erased["base_fingerprint"] == art["base_fingerprint"]


def test_ablation_zeroes_both_factors_and_leaves_every_other_component_alone():
    """BOTH ``B[:, j]`` and ``A[j, :]`` — the property the pin's mechanism rule claims.

    This is the assertion that bites the half-ablation. ``dW == 0`` does NOT: the component's
    contribution is ``scale * outer(B[:, j], A[j, :])``, so zeroing EITHER factor already sends
    that outer product to zero and the delta-based tests stay green while ``A[j, :]`` still carries
    live values (measured, see the plan SUMMARY's deliberate-RED record). An operator that cleared
    only one factor would leave the component's absence depending on which half was cleared rather
    than being a property of the file.
    """
    _base, adapted, lora_cfg = _build_pair()
    art = _artifact(adapted, lora_cfg)
    layer, projection, j = erasure.component_index()[0]
    prefix = erasure._COMPONENT_PREFIX[(layer, projection)]

    before_a = art["adapter"][f"{prefix}.lora_A"]
    before_b = art["adapter"][f"{prefix}.lora_B"]
    # Non-vacuity: both slices must carry live values BEFORE, or "it is zero after" proves nothing.
    assert before_a[j, :].abs().max() > 0
    assert before_b[:, j].abs().max() > 0

    erased = erasure.ablate_components(art, [(layer, projection, j)])
    after_a = erased["adapter"][f"{prefix}.lora_A"]
    after_b = erased["adapter"][f"{prefix}.lora_B"]

    assert torch.equal(after_a[j, :], torch.zeros_like(after_a[j, :]))
    assert torch.equal(after_b[:, j], torch.zeros_like(after_b[:, j]))

    # Every OTHER rank-1 component of the same projection survives untouched — an operator that
    # zeroed the whole tensor would also satisfy the two assertions above.
    keep = [i for i in range(lora_cfg.r) if i != j]
    assert torch.equal(after_a[keep, :], before_a[keep, :])
    assert torch.equal(after_b[:, keep], before_b[:, keep])


def test_ablate_components_does_not_mutate_its_input_adapter():
    """The caller's PRE-erasure adapter survives — the (b) condition needs the paired delta."""
    _base, adapted, lora_cfg = _build_pair()
    art = _artifact(adapted, lora_cfg)
    before = {k: v.detach().clone() for k, v in art["adapter"].items()}
    assert any(t.abs().max() > 0 for t in before.values()), "vacuous: the input was already zero"

    erased = erasure.ablate_components(art, erasure.component_index())

    for key, tensor in before.items():
        assert torch.equal(art["adapter"][key], tensor), f"{key} was mutated in place"
    # And the result is genuinely a different object, not the input handed back.
    for key in before:
        assert erased["adapter"][key] is not art["adapter"][key]
    assert all(t.abs().max() == 0 for t in erased["adapter"].values())


def test_fully_ablated_artifact_round_trips_through_export_and_the_load_audits(tmp_path):
    """``export_adapter`` -> ``load_adapter`` -> ``load_adapter_weights``, no audit relaxed.

    All three audits run for real: the key-set audit, the shape/dtype audit, and the SCALE audit
    that reads ``artifact["lora_config"]`` (``inject.py:119-129``). Loading into a SECOND,
    independently injected model is what makes the key audit meaningful — applying an artifact back
    onto the model it came from could not detect a key-set the format does not describe.
    """
    _base, adapted, lora_cfg = _build_pair()
    art = _artifact(adapted, lora_cfg)
    erased = erasure.ablate_components(art, erasure.component_index())

    path = tmp_path / "phase19_toy_erased_adapter.pt"
    written = export_adapter(
        path,
        adapter=erased["adapter"],
        lora_config=erased["lora_config"],
        base_fingerprint=erased["base_fingerprint"],
    )
    assert written["lora_config"] == art["lora_config"]

    # weights_only=True restricted unpickler — the erased artifact must survive the same choke
    # point the shippable persona file goes through.
    loaded = load_adapter(path)
    assert loaded["lora_config"] == art["lora_config"]
    assert loaded["adapter"].keys() == art["adapter"].keys()

    torch.manual_seed(4321)
    fresh = GPT(_tiny_config())
    inject_lora(fresh, LoRAConfig(**loaded["lora_config"]))
    load_adapter_weights(fresh, loaded)  # raises ValueError on any key/shape/scale complaint.

    for _prefix, module in fresh.named_modules():
        if isinstance(module, LoRALinear):
            assert module.scale == lora_cfg.alpha / lora_cfg.r


def test_full_ablation_zeroes_delta_w_in_every_wrapped_projection():
    """``dW = scale * (B @ A)`` is EXACTLY the zero matrix in all 36 cells after full ablation.

    The fold is ``merged_state_dict``'s (``inject.py:282``) and ``adapter_cells``' (``:186``):
    ``scale`` is read from ``LoRALinear.scale``, the single source of truth, and never recomputed
    (PITFALLS P3). ``torch.equal`` against ``zeros_like``, not ``allclose`` — the claim is exact.
    """
    _base, adapted, lora_cfg = _build_pair()
    art = _artifact(adapted, lora_cfg)

    # Non-vacuity: the delta is non-zero in every cell BEFORE ablation.
    nonzero_before = 0
    for _prefix, module in adapted.named_modules():
        if isinstance(module, LoRALinear):
            delta = module.scale * (module.lora_B @ module.lora_A)
            if delta.abs().max() > 0:
                nonzero_before += 1
    assert nonzero_before == len(extract_deltas.KEYS), (
        f"only {nonzero_before} of {len(extract_deltas.KEYS)} cells carried a non-zero delta "
        "before ablation — the fixture, not the operator, would be producing the zeros below"
    )

    erased = erasure.ablate_components(art, erasure.component_index())
    load_adapter_weights(adapted, erased)

    checked = 0
    for prefix, module in adapted.named_modules():
        if not isinstance(module, LoRALinear):
            continue
        delta = module.scale * (module.lora_B @ module.lora_A)
        assert delta.shape == module.base.weight.shape, f"{prefix}: dW is not base-weight shaped"
        assert torch.equal(delta, torch.zeros_like(delta)), (
            f"{prefix}: dW is not exactly zero after ablating all "
            f"{erasure.N_COMPONENTS} components (max |dW| = {delta.abs().max().item():.3e})"
        )
        checked += 1
    assert checked == len(extract_deltas.KEYS)


def test_full_ablation_preserves_the_adapter_off_bit_identity_control():
    """Max abs diff EXACTLY 0.0 against ``adapter_disabled`` and against the un-adapted base.

    The bar ``run_bit_identity_control`` (``phase14_recall.py:1480``) already meets on the real
    weights (``STATE.md:142``), reproduced here on the ablated artifact. M1 stays inside the rank-8
    decomposition specifically so this holds: with the adapter disabled the wrapper's forward is
    literally ``self.base(x)``, so an operator that only rewrites ``lora_A``/``lora_B`` cannot move
    the adapter-off logits at all — and after a full ablation the adapter-ON logits join them.
    """
    base, adapted, lora_cfg = _build_pair()
    art = _artifact(adapted, lora_cfg)
    idx = torch.randint(0, _tiny_config().vocab_size, (2, 12))

    # NON-VACUITY, and it is the load-bearing half of this test: BEFORE ablation the adapter must
    # actually change the logits. Without this the equalities below are satisfied by an adapter
    # that never did anything (lora_B starts at zero — layer.py:30).
    before_on = _logits(adapted, idx)
    base_logits = _logits(base, idx)
    assert not torch.equal(before_on, base_logits), (
        "the un-ablated adapter already reproduces the base — the fixture never nudged lora_B, so "
        "every equality below would be measuring the identity gate rather than the ablation"
    )

    load_adapter_weights(adapted, erasure.ablate_components(art, erasure.component_index()))
    after_on = _logits(adapted, idx)
    with adapter_disabled(adapted):
        after_off = _logits(adapted, idx)

    assert _max_abs_diff(after_on, after_off) == 0.0
    assert torch.equal(after_on, after_off), (
        "the fully ablated adapter-ON logits differ from adapter_disabled — dW is not zero"
    )
    assert _max_abs_diff(after_on, base_logits) == 0.0
    assert torch.equal(after_on, base_logits), (
        "the fully ablated model differs from the un-adapted base — the demo's 'memory off' state "
        "would no longer be the base, which is the entire claim the toggle makes"
    )
    # The adapter-off state is untouched by the operator: disabled logits still equal the base,
    # which is what `run_bit_identity_control` asserts on the real weights.
    assert torch.equal(after_off, base_logits)


def test_ablate_components_refuses_addresses_it_cannot_honour():
    """Every ``_prove`` branch bites — an untested refusal is a refusal nobody has watched."""
    _base, adapted, lora_cfg = _build_pair()
    art = _artifact(adapted, lora_cfg)
    address = erasure.component_index()[0]

    with pytest.raises(SystemExit, match="addressed twice"):
        erasure.ablate_components(art, [address, address])

    layer, projection, _j = address
    with pytest.raises(SystemExit, match="outside"):
        erasure.ablate_components(art, [(layer, projection, lora_cfg.r)])

    with pytest.raises(SystemExit, match="not a wrapped projection"):
        erasure.ablate_components(art, [(layer, "not_a_projection", 0)])

    with pytest.raises(SystemExit, match="export_adapter-shaped"):
        erasure.ablate_components({"adapter": art["adapter"]}, [address])


# =============================================================================================
# ===== PLAN 19-02 / TASK 1 — THE TARGET FACT, ITS RULE AND ITS TIE-BREAKS (D7) =====
# =============================================================================================
#
# The pin publishes `TARGET_RANKING` as a written constant, exactly as `phase14_recall`'s
# `CALIBRATION_SHA` block publishes its calibrated thresholds. What makes that honest rather than
# a transcription is the first test below: it re-runs the committed rule over the committed arm
# record on EVERY run, so a hand-edited constant goes red. The constants are value-free — keyed by
# SLOT, never by `fact_id` — because every core `fact_id` ends in its own locked value
# (`scripts/phase17_personas.py:61`, `scripts/phase17_isolation.py:128`), so a fact-id-keyed
# ranking would embed all eight of them in the pre-registration's source (T-19-07).

_ARM_RECORD = _ROOT / "results" / "phase18_arm_adapter-on.json"


def _committed_values():
    """``{fact_id: value}`` for ``score_records`` — a PARAMETER, never an import (T-19-07)."""
    facts = _load("phase14_factset", "scripts/phase14_factset.py")
    return {fact.id: fact.value for fact in facts.LOCKED_FACTS + facts.SOFT_TIER_FACTS}


@pytest.fixture(scope="module")
def arm_record():
    return json.loads(_ARM_RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def derived_rows(arm_record):
    return erasure.target_rows_from_arm_record(arm_record, _committed_values())


def _synthetic(entries):
    """``(per_fact_rows, exposure)`` over the eight pinned slots with controlled rate and NLL.

    ``entries`` is ``{slot: (fact_id, successes, rate, nll)}`` and must cover every pinned slot —
    the rule refuses anything else, which is itself one of the behaviours under test.
    """
    rows = {
        fact_id: {"slot": slot, "n_answerable": successes, "n_questions": 13, "rate": rate}
        for slot, (fact_id, successes, rate, _nll) in entries.items()
    }
    exposure = [
        {"slot": slot, "admissible": ["ans1", "mean"], "nll": {"ans1": {"mean": nll}}}
        for slot, (_fact_id, _successes, _rate, nll) in entries.items()
    ]
    return rows, exposure


def _flat(rates_and_nlls):
    """Every pinned slot at rate 0.0 / NLL 9.0 except the ones named, which are handed to it."""
    entries = {
        slot: (f"synthetic_{slot}", 0, 0.0, 9.0) for slot in sorted(erasure.CORE_GATED_SLOTS)
    }
    entries.update(rates_and_nlls)
    return _synthetic(entries)


def test_target_ranking_is_re_derived_from_the_committed_arm_record(derived_rows, arm_record):
    """The published ranking IS what the committed rule returns on the committed artifact.

    A hand-edited `TARGET_RANKING` — one rate nudged, one row reordered, the head swapped — fails
    here. That is the whole of T-19-05: the constant carries no authority of its own, it is a
    cached result of a function this test re-runs.
    """
    ranked = erasure.rank_target_candidates(derived_rows, arm_record["exposure"])

    assert ranked == erasure.TARGET_RANKING, (
        "the committed TARGET_RANKING is not what the committed rule returns on "
        f"{_ARM_RECORD.name} — re-derived {ranked}"
    )
    assert erasure.TARGET_SLOT == ranked[0][0]

    fact_id = erasure.select_target_fact(derived_rows, arm_record["exposure"])
    assert derived_rows[fact_id]["slot"] == erasure.TARGET_SLOT, (
        "select_target_fact and rank_target_candidates disagree about the head of the same order"
    )
    # And the selector's return is a real fact of the record, not a fabricated id.
    assert fact_id in derived_rows


def test_the_tie_break_is_load_bearing_on_the_real_record(derived_rows, arm_record):
    """MEASURED, not assumed: the primary criterion does NOT decide this target on its own.

    Several core slots sit at the ceiling on the gated tier, so the highest-rate criterion returns
    a SET and tie-break 1 is what picks the target out of it. Recorded as a checked fact because it
    is the reason D7 required the tie-break in the same commit as the rule: had the tie-break been
    written afterwards, the actual choice would have been made after the ranking was visible.
    """
    ranked = erasure.rank_target_candidates(derived_rows, arm_record["exposure"])
    top_rate = ranked[0][erasure.TARGET_RANKING_FIELDS.index("rate")]
    tied = [row for row in ranked if row[erasure.TARGET_RANKING_FIELDS.index("rate")] == top_rate]

    assert len(tied) > 1, (
        "only one slot holds the top rate, so this run's target was decided by the primary "
        "criterion alone — the claim in the SUMMARY that the tie-break was load-bearing is stale"
    )
    nll_at = erasure.TARGET_RANKING_FIELDS.index("exposure_ans1_mean_nll")
    assert ranked[0][nll_at] == min(row[nll_at] for row in tied), (
        "the head of the ranking is not the lowest-NLL member of the tied set — tie-break 1 says "
        "MOST EXPOSED WINS, and a higher NLL is less exposed"
    )


def test_target_ranking_covers_the_eight_core_gated_slots(derived_rows, arm_record):
    """Eight rows, the canonical slot set, one shared denominator, proved against the draw count."""
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")

    assert {row[0] for row in erasure.TARGET_RANKING} == set(extraction.CORE_SLOTS)
    assert len(erasure.TARGET_RANKING) == len(extraction.CORE_SLOTS) == 8
    assert set(erasure.CORE_GATED_SLOTS) == set(extraction.CORE_SLOTS)
    assert erasure.TARGET_RANKING_FIELDS == (
        "slot",
        "successes",
        "n_questions",
        "rate",
        "exposure_ans1_mean_nll",
    )

    # The denominator is DERIVED from the record, never typed: the cell holds exactly one draw
    # record per question, so the questions must sum to the number of records.
    tier, family = extraction.GATED_TIER, "A2"
    cell = [d for d in arm_record["draws"] if d["family"] == family and d["tier"] == tier]
    denominators = {row[2] for row in erasure.TARGET_RANKING}
    assert len(denominators) == 1, f"the eight facts do not share one denominator: {denominators}"
    assert sum(row[2] for row in erasure.TARGET_RANKING) == len(cell)

    for slot, successes, n_questions, rate, _nll in erasure.TARGET_RANKING:
        assert 0 <= successes <= n_questions
        assert rate == successes / n_questions, f"{slot}: the published rate is not successes/n"

    # And every published row agrees with the live aggregation, field for field.
    by_slot = {row["slot"]: row for row in derived_rows.values()}
    for slot, successes, n_questions, rate, _nll in erasure.TARGET_RANKING:
        assert by_slot[slot]["n_answerable"] == successes
        assert by_slot[slot]["n_questions"] == n_questions
        assert by_slot[slot]["rate"] == rate


def test_rate_ties_resolve_by_the_exposure_tie_break_in_both_directions():
    """Tie-break 1 decides a two-way rate tie, and it decides it by DIRECTION, not by position.

    Running it twice with the two NLLs swapped is what separates "the tie-break fired" from "the
    first-listed slot happened to win" — an implementation that ignored exposure entirely would
    pass the first assertion alone.
    """
    rows, exposure = _flat(
        {
            "hometown": ("synthetic_hometown", 13, 1.0, 0.5),
            "street": ("synthetic_street", 13, 1.0, 0.25),
        }
    )
    assert rows[erasure.select_target_fact(rows, exposure)]["slot"] == "street"

    rows, exposure = _flat(
        {
            "hometown": ("synthetic_hometown", 13, 1.0, 0.25),
            "street": ("synthetic_street", 13, 1.0, 0.5),
        }
    )
    assert rows[erasure.select_target_fact(rows, exposure)]["slot"] == "hometown"


def test_a_tie_on_rate_AND_exposure_resolves_lexicographically_by_fact_id():
    """Tie-break 2. The ids are chosen so the lexical answer is NOT the insertion-order answer."""
    rows, exposure = _flat(
        {
            "hometown": ("zzz_second_alphabetically", 13, 1.0, 0.25),
            "street": ("aaa_first_alphabetically", 13, 1.0, 0.25),
        }
    )
    assert erasure.select_target_fact(rows, exposure) == "aaa_first_alphabetically"

    # Same input, reversed insertion order — a dict-iteration-order dependence would flip here.
    reversed_rows = dict(reversed(list(rows.items())))
    assert erasure.select_target_fact(reversed_rows, exposure) == "aaa_first_alphabetically"


def test_a_three_way_tie_is_still_deterministic():
    """Three slots identical on BOTH criteria — the rule still returns one answer, always."""
    tied = {
        "hometown": ("tie_c", 13, 1.0, 0.25),
        "street": ("tie_a", 13, 1.0, 0.25),
        "cat_name": ("tie_b", 13, 1.0, 0.25),
    }
    rows, exposure = _flat(tied)
    assert erasure.select_target_fact(rows, exposure) == "tie_a"

    ranked = erasure.rank_target_candidates(rows, exposure)
    assert [row[0] for row in ranked[:3]] == ["street", "cat_name", "hometown"]
    for _ in range(3):
        assert erasure.rank_target_candidates(dict(rows), exposure) == ranked


def test_select_target_fact_refuses_a_row_set_that_is_not_the_eight_core_gated_facts():
    """Every refusal bites — an untested refusal is a refusal nobody has watched."""
    rows, exposure = _flat({})

    short = dict(list(rows.items())[:-1])
    with pytest.raises(SystemExit, match="eight core gated"):
        erasure.select_target_fact(short, exposure)

    extra = dict(rows)
    extra["synthetic_ninth"] = {
        "slot": "not_a_core_slot",
        "n_answerable": 0,
        "n_questions": 13,
        "rate": 0.0,
    }
    with pytest.raises(SystemExit, match="eight core gated"):
        erasure.select_target_fact(extra, exposure)

    renamed = {k: dict(v) for k, v in rows.items()}
    renamed["synthetic_hometown"]["slot"] = "not_a_core_slot"
    with pytest.raises(SystemExit, match="core gated slot set"):
        erasure.select_target_fact(renamed, exposure)

    two_facts_one_slot = {k: dict(v) for k, v in rows.items()}
    two_facts_one_slot["synthetic_hometown"]["slot"] = "street"
    with pytest.raises(SystemExit, match="both claim slot"):
        erasure.select_target_fact(two_facts_one_slot, exposure)

    with pytest.raises(SystemExit, match="no exposure entry"):
        erasure.select_target_fact(rows, exposure[:-1])


def test_the_exposure_reduction_is_read_from_the_record_never_chosen_here():
    """``ans1``/``mean`` is the arm record's OWN ``admissible`` pair, not a second choice.

    D-29 published six frame x reduction NLLs and marked exactly one admissible. Re-picking one
    here would be a second selection rule for the same quantity, free to stop agreeing with the
    one Phase 18 committed — so the pin reads the record's declaration and refuses a record that
    declares something else.
    """
    rows, exposure = _flat({})
    relabelled = [dict(entry, admissible=["f3_bare", "sum"]) for entry in exposure]
    with pytest.raises(SystemExit, match="admissible"):
        erasure.select_target_fact(rows, relabelled)


def test_target_selection_rule_states_its_tie_breaks_and_the_forbidden_move(arm_record):
    """D7: the rule and BOTH tie-breaks land in the same commit, and say what is forbidden."""
    text = " ".join(erasure.TARGET_SELECTION_RULE)
    lowered = text.lower()

    assert "tie-break 1" in lowered and "tie-break 2" in lowered
    assert "lexicographically" in lowered
    assert "most exposed wins" in lowered
    assert "forbidden" in lowered
    assert "9a923d6" in text, "the rule does not name the arm record's first-add commit"
    # The budget the rule names is the one the record declares — prose that stops being true is
    # the failure mode a pre-registration cannot survive.
    assert f"K = {arm_record['config']['k']}" in text
    assert erasure.MECHANISM_ID not in text  # the mechanism rule and this one stay separate

    # No fact value may reach the pin's source, and the rule is the longest prose in it.
    facts = _load("phase14_factset", "scripts/phase14_factset.py")
    forbidden = [f.value.lower() for f in facts.LOCKED_FACTS + facts.SOFT_TIER_FACTS]
    assert len(forbidden) == 10
    source = (_ROOT / "scripts" / "phase19_erasure.py").read_text(encoding="utf-8").lower()
    hits = [value for value in forbidden if value in source]
    assert hits == [], (
        f"scripts/phase19_erasure.py embeds fact value(s) {hits} — every core fact_id ends in "
        "its own value, so a fact-id-keyed constant puts the answers into the pin (T-19-07)"
    )


# =============================================================================================
# ===== PLAN 19-02 / TASK 2 — THE (a) DENOMINATOR, DERIVED FROM THE BINDING FIXTURE (D5) =====
# =============================================================================================

_FIXTURE = _ROOT / "results" / "phase16_recall_sample.json"
_PIN_SOURCE = (_ROOT / "scripts" / "phase19_erasure.py").read_text(encoding="utf-8")


def test_target_question_counts_are_re_derived_from_the_committed_fixture(arm_record):
    """n = 27 is what the binding 270-question fixture holds for the target, not what was typed.

    Two independent artifacts have to agree for this to pass: the fixture supplies both per-tier
    counts, and Phase 18's own aggregation of the arm record supplies the held-out one a second
    time (the head of ``TARGET_RANKING``). The pin cross-checks those two at import.
    """
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")
    counts = erasure.derive_target_question_counts(_FIXTURE, _ARM_RECORD)

    assert counts == {**erasure.TARGET_QUESTION_COUNTS, "pooled": erasure.N_TARGET_QUESTIONS}
    assert erasure.N_TARGET_QUESTIONS == 27
    assert erasure.N_TARGET_QUESTIONS == sum(erasure.TARGET_QUESTION_COUNTS.values())
    assert set(erasure.TARGET_QUESTION_COUNTS) == set(extraction.CORPUS_TIERS)

    # The fixture's own published per-core-fact census, read off the artifact rather than retyped.
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    per_core = fixture["counts"]["per_core_fact"]
    assert erasure.TARGET_QUESTION_COUNTS["core_taught"] == per_core["taught"]
    assert erasure.TARGET_QUESTION_COUNTS["core_held_out"] == per_core["held_out"]

    # And the target this counted is the one the ranking selected — not some other fact.
    fact_id = erasure.target_fact_id(arm_record["draws"])
    assert (
        erasure.select_target_fact(
            erasure.target_rows_from_arm_record(arm_record, _committed_values()),
            arm_record["exposure"],
        )
        == fact_id
    )


def test_target_fact_id_resolves_the_pinned_slot_and_refuses_an_ambiguous_record():
    """The ONE committed slot -> fact_id path, so no downstream plan writes the id by hand."""
    records = [
        {"fact_id": "alpha", "slot": erasure.TARGET_SLOT},
        {"fact_id": "alpha", "slot": erasure.TARGET_SLOT},
        {"fact_id": "beta", "slot": "hometown"},
    ]
    assert erasure.target_fact_id(records) == "alpha"

    with pytest.raises(SystemExit, match="carry slot"):
        erasure.target_fact_id(records + [{"fact_id": "gamma", "slot": erasure.TARGET_SLOT}])
    with pytest.raises(SystemExit, match="carry slot"):
        erasure.target_fact_id([{"fact_id": "beta", "slot": "hometown"}])


def test_target_question_counts_refuses_a_duplicated_question():
    """A repeated ``(fact_id, seed_index)`` INFLATES n rather than raising, unless it is caught.

    That is the ugly direction: a silently doubled denominator makes every Wilson bound narrower,
    so the (a) condition would look easier to clear than the fixture supports.
    """
    tiers = ("t_taught", "t_held_out")
    clean = {
        "questions": {
            "t_taught": [{"fact_id": "target", "seed_index": i} for i in range(3)]
            + [{"fact_id": "other", "seed_index": 0}],
            "t_held_out": [{"fact_id": "target", "seed_index": i} for i in range(2)],
        }
    }
    assert erasure.target_question_counts(clean, "target", tiers) == {
        "t_taught": 3,
        "t_held_out": 2,
        "pooled": 5,
    }

    duplicated = {"questions": {k: list(v) for k, v in clean["questions"].items()}}
    duplicated["questions"]["t_taught"].append({"fact_id": "target", "seed_index": 0})
    with pytest.raises(SystemExit, match="twice"):
        erasure.target_question_counts(duplicated, "target", tiers)

    with pytest.raises(SystemExit, match="no questions"):
        erasure.target_question_counts(clean, "a_fact_the_fixture_does_not_hold", tiers)

    with pytest.raises(SystemExit, match="no 'not_a_tier' tier"):
        erasure.target_question_counts(clean, "target", ("not_a_tier",))

    with pytest.raises(SystemExit, match="pooled"):
        erasure.target_question_counts(clean, "target", ("t_taught", "pooled"))


def test_the_pooled_denominator_is_never_typed_anywhere_in_the_pin():
    """P19-5 / T-19-06: 27 is COMPUTED from two counted quantities, never written down.

    An AST walk rather than ``grep -n "27"``: a grep cannot tell an integer literal from the two
    digits inside a float, and the pin publishes eight exposure NLLs.
    """
    literals = [
        node.value
        for node in ast.walk(ast.parse(_PIN_SOURCE))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value == erasure.N_TARGET_QUESTIONS
    ]
    assert literals == [], (
        f"the pin types the pooled denominator {erasure.N_TARGET_QUESTIONS} as an integer literal "
        f"{len(literals)} time(s) — it must be summed from the two counted tiers"
    )


def test_the_wilson_bound_is_the_committed_one_and_is_never_re_derived():
    """STAT-05 / T-19-08: imported from ``erasure_gate`` by IDENTITY, not by matching values."""
    import erasure_gate

    assert erasure.wilson_upper_bound is erasure_gate.wilson_upper_bound

    tree = ast.parse(_PIN_SOURCE)
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "wilson_upper_bound" not in defined
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "math" not in imported, (
        "the pin imports math — a second Wilson interval needs a sqrt, and the point of importing "
        "the committed one is that there is no second implementation to disagree with it"
    )

    # And it is Wilson, not Wald: Wald degenerates to exactly 0 at zero successes, which is the
    # case the (a) condition cares about most (erasure_gate.py:144-149).
    assert erasure.BEST_ATTAINABLE_TARGET_BOUND > 0.0
    assert erasure.BEST_ATTAINABLE_TARGET_BOUND == erasure_gate.wilson_upper_bound(
        0, erasure.N_TARGET_QUESTIONS
    )
    # Pooling is what buys the reachability: the held-out tier alone cannot clear as low a floor.
    assert erasure.BEST_ATTAINABLE_TARGET_BOUND < erasure_gate.wilson_upper_bound(
        0, erasure.TARGET_QUESTION_COUNTS["core_held_out"]
    )


def test_denominator_rule_records_the_departure_the_refusal_and_the_real_arithmetic():
    """Every number the rule quotes is a computed one, and D5's declarations are all made."""
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")
    import erasure_gate

    text = " ".join(erasure.DENOMINATOR_RULE)
    lowered = text.lower()

    held_out = erasure.TARGET_QUESTION_COUNTS["core_held_out"]
    assert f"n = {erasure.N_TARGET_QUESTIONS}" in text
    assert f"{erasure_gate.wilson_upper_bound(0, held_out):.6f}" in text
    assert f"{erasure.BEST_ATTAINABLE_TARGET_BOUND:.6f}" in text

    # The REFUSED inflation is (attack families) x (questions) — 4 is derived, not asserted.
    families = len(extraction.ATTACK_FAMILIES)
    assert families == 4
    assert f"n = {families * held_out}" in text
    assert f"n = {families * erasure.N_TARGET_QUESTIONS}" in text

    # The three declarations D5 required be stated rather than implied.
    assert "departure" in lowered, "the tier pooling is not declared as a departure from Phase 18"
    assert "refused" in lowered
    assert "two calls" in lowered, "the mechanics of pooling under a single-tier _prove are missing"
    assert "aggregate_questions" in text and "2223" in text


# =============================================================================================
# ===== PLAN 19-03 / TASK 1 — THE (a) FLOOR-DERIVATION RULE, MIRRORED AND BOUNDED (D2/W1) =====
# =============================================================================================
#
# ``math`` is imported HERE and never in the pin: `test_the_wilson_bound_is_the_committed_one`
# forbids it there so no sqrt is available to re-derive a second Wilson interval (T-19-08). The
# tests are not the pre-registration, so a `math.floor` ORACLE for the pin's `int()` truncation is
# exactly what belongs on this side of the line.


def _floor_rows():
    """``(cal_rate, mirrored floor, literal Phase 14 floor, branch)`` over the whole domain."""
    return tuple(
        (
            x,
            erasure.lock_erasure_floor(x),
            erasure.literal_phase14_floor(x),
            erasure.floor_branch(x),
        )
        for x in erasure.floor_sweep()
    )


def _grid_oracle(x):
    """The discount branch computed INDEPENDENTLY of the pin, with the stdlib `math.floor`.

    The pin cannot import ``math``, so it truncates with ``int()``. On the non-negative domain the
    two are the same function and this oracle is what proves it rather than asserting it.
    """
    return math.floor(x * erasure.FLOOR_DISCOUNT * erasure.FLOOR_GRID) / erasure.FLOOR_GRID


def test_the_floor_mirror_is_never_looser_than_the_literal_phase14_operator():
    """T-19-10 / D2: the mirror makes (a) HARDER at every rate, and both directions are visible.

    Phase 14 clamped with ``max(FLOOR, ...)`` against a ``>=`` gate — that RAISES the bar. Erasure's
    floor is an upper cap against a ``<=`` gate, so the identical literal operator would RAISE the
    cap and make (a) EASIER. A "mirror" that quietly loosened anywhere on the domain reddens here
    rather than passing review.
    """
    looser = [(x, mirror, literal) for x, mirror, literal, _b in _floor_rows() if mirror > literal]
    assert looser == [], (
        f"the mirrored floor is LOOSER than Phase 14's literal operator at {len(looser)} of "
        f"{len(erasure.floor_sweep())} rates (first: {looser[:3]}) — D2 requires the adjustment "
        "make (a) harder, never easier"
    )

    # BOTH DIRECTIONS' VALUES, side by side at the domain endpoints. D2 asks that a reader SEE the
    # choice rather than infer it, so the gap is asserted here and printed by `--floor`.
    assert erasure.lock_erasure_floor(0.0) == erasure.ERASURE_FLOOR_MIN
    assert erasure.literal_phase14_floor(0.0) == erasure.FLOOR_CEILING
    assert erasure.lock_erasure_floor(1.0) == erasure.FLOOR_CEILING
    assert erasure.literal_phase14_floor(1.0) == round(1.0 * erasure.FLOOR_DISCOUNT, 4)
    # At a perfect calibration rate the literal operator hands (a) a cap three times the mirror's.
    assert erasure.literal_phase14_floor(1.0) > 3 * erasure.lock_erasure_floor(1.0) - 1e-12


def test_the_floor_clamp_is_a_min_not_a_max():
    """The ceiling CAPS. Swapped for a `max` it would admit the rate instead of refusing it."""
    rows = _floor_rows()
    over = [(x, mirror) for x, mirror, _l, _b in rows if mirror > erasure.FLOOR_CEILING]
    assert over == [], (
        f"the floor exceeds FLOOR_CEILING at {len(over)} rates — the clamp is not a min"
    )

    def _swapped(x):
        """The same expression with the inner clamp mirrored back the wrong way."""
        return max(erasure.ERASURE_FLOOR_MIN, max(erasure.FLOOR_CEILING, _grid_oracle(x)))

    assert _swapped(1.0) == round(1.0 * erasure.FLOOR_DISCOUNT, 4)
    assert erasure.lock_erasure_floor(1.0) == erasure.FLOOR_CEILING
    assert _swapped(1.0) > erasure.lock_erasure_floor(1.0), (
        "a `max` clamp does not cap a large calibration rate, it ADMITS it — the returned cap "
        "would rise with the calibration fact's own recall, which is the direction D2 forbids"
    )


def test_the_floor_never_returns_below_the_reachability_minimum_and_reports_its_branch():
    """Every returned floor is inside ``[ERASURE_FLOOR_MIN, FLOOR_CEILING]`` and names its bound.

    The branch reporter is not decoration: when the reachability clamp binds, (a) clears ONLY on a
    perfect erasure, and a report that printed the floor without which bound produced it would
    leave the reader to re-derive the severity of the criterion they are being shown.
    """
    census = {}
    for x, mirror, _literal, branch in _floor_rows():
        assert erasure.ERASURE_FLOOR_MIN <= mirror <= erasure.FLOOR_CEILING, (x, mirror)
        expected = {
            "reachability-min": erasure.ERASURE_FLOOR_MIN,
            "discount": _grid_oracle(x),
            "ceiling": erasure.FLOOR_CEILING,
        }[branch]
        assert mirror == expected, (
            f"floor_branch({x!r}) reports {branch!r} but the returned floor {mirror!r} is not the "
            f"value that branch produces ({expected!r})"
        )
        census[branch] = census.get(branch, 0) + 1

    # All three branches are REACHED on the domain — a branch reporter with a dead arm is a
    # reporter whose dead arm has never been checked against anything.
    assert census == {"reachability-min": 152, "discount": 182, "ceiling": 667}, census
    assert sum(census.values()) == len(erasure.floor_sweep())


def test_the_floor_is_exact_before_the_division_scoped_to_the_branch_it_describes():
    """``floor(v * 10000) <= v * 10000`` — integer vs float, no tolerance, on the discount branch.

    The UNSCOPED form ``lock(x) <= x * FLOOR_DISCOUNT`` is DELIBERATELY NOT asserted. It is red at
    161 of these 1001 rates for a CORRECT implementation, because below the crossover the
    reachability clamp binds by design. Measured here instead of denied: every violation is on the
    ``reachability-min`` branch and nowhere else, which is the whole content of the claim.
    """
    rows = _floor_rows()
    scale = erasure.FLOOR_DISCOUNT * erasure.FLOOR_GRID
    violations = [
        x
        for x, _m, _l, branch in rows
        if branch == "discount" and not math.floor(x * scale) <= x * scale
    ]
    assert violations == [], violations
    assert sum(1 for _x, _m, _l, b in rows if b == "discount") == 182

    unscoped = [x for x, mirror, _l, _b in rows if not mirror <= x * erasure.FLOOR_DISCOUNT]
    assert len(unscoped) == 161, (
        f"{len(unscoped)} rates violate the unscoped form, not the 161 measured when the rule was "
        "committed — a changed FLOOR_DISCOUNT or ERASURE_FLOOR_MIN moves the crossover"
    )
    # The 161 decompose EXACTLY, and into the two effects this plan already characterised
    # separately — there is no third, unexplained way for the unscoped form to go red.
    by_branch = {branch: 0 for branch in ("reachability-min", "discount", "ceiling")}
    for x in unscoped:
        by_branch[erasure.floor_branch(x)] += 1
    assert by_branch == {"reachability-min": 152, "discount": 9, "ceiling": 0}, by_branch

    # 152: the clamp binding, by design. EVERY rate on that branch violates, none is a near miss.
    clamped = [x for x, _m, _l, b in rows if b == "reachability-min"]
    assert len(clamped) == 152
    assert all(x in unscoped for x in clamped)
    # 9: the one-ulp division residual of the NEXT test, not a second phenomenon.
    residual = [x for x in unscoped if erasure.floor_branch(x) == "discount"]
    assert {
        (erasure.lock_erasure_floor(x) - x * erasure.FLOOR_DISCOUNT)
        / math.ulp(erasure.lock_erasure_floor(x))
        for x in residual
    } == {1.0}

    # The crossover itself, named rather than inferred: below it the clamp binds.
    crossover = erasure.ERASURE_FLOOR_MIN / erasure.FLOOR_DISCOUNT
    assert max(clamped) < crossover <= min(x for x, _m, _l, b in rows if b == "discount")
    assert (
        erasure.lock_erasure_floor(0.10)
        == erasure.ERASURE_FLOOR_MIN
        > 0.10 * erasure.FLOOR_DISCOUNT
    )


def test_the_stored_floor_exceeds_the_four_decimal_grid_by_at_most_one_ulp():
    """W1's honest bound: the ``floor`` is exact, the DIVISION back down is not.

    ``floor(v * 10000)`` is exact. ``/ 10000`` re-rounds to the nearest representable double and can
    land one ulp ABOVE the exact quarter-ten-thousandth — a residual D2 exposure the rule RECORDS
    rather than claims away. Measured: it happens, it is always exactly one ulp, and never two.
    """
    exceeding = [
        (x, _grid_oracle(x) - x * erasure.FLOOR_DISCOUNT)
        for x in erasure.floor_sweep()
        if _grid_oracle(x) > x * erasure.FLOOR_DISCOUNT
    ]
    assert len(exceeding) == 68
    ulps = {excess / math.ulp(_grid_oracle(x)) for x, excess in exceeding}
    assert ulps == {1.0}, f"the stored floor exceeds the exact grid value by {ulps} ulps, not one"

    # Nine of the 68 sit on the discount branch, where no clamp masks them. Named, because these
    # are the only rates at which the residual can reach the gate at all.
    unmasked = [x for x, _e in exceeding if erasure.floor_branch(x) == "discount"]
    assert unmasked == [0.173, 0.174, 0.177, 0.178, 0.182, 0.186, 0.19, 0.195, 0.207]

    # And it is int()-vs-math.floor()-identical everywhere: the pin cannot import math, so this is
    # what makes the substitution a measured equivalence instead of an assumed one.
    assert [erasure.lock_erasure_floor(x) for x in unmasked] == [_grid_oracle(x) for x in unmasked]


def test_a_floor_hit_exactly_on_the_bound_still_clears_the_gate():
    """The gate's comparison is ``<=``: a target upper bound exactly ON the floor PASSES.

    This is Phase 14's ``>=`` boundary discipline mirrored (``phase14_recall.py:200-218``, pinned by
    ``tests/test_phase14_scoring.py:115-143``), and it is load-bearing for reachability: run against
    the tightest floor the rule can produce, a PERFECT erasure lands exactly on it. One ulp lower
    and the same perfect erasure FAILS — which is what the clamp exists to prevent.
    """
    import erasure_gate

    tightest = erasure.lock_erasure_floor(0.0)
    kwargs = dict(
        target_successes=0,
        target_questions=erasure.N_TARGET_QUESTIONS,
        nontarget_deltas=[0.0],
        nontarget_noise_floor=0.01,
        dialogue_ppl=erasure_gate.V20_MASKED_DIALOGUE_VAL_PPL,
        dialogue_ppl_noise_floor=0.01,
        retention_ppl=erasure_gate.V20_EWC_RETENTION_PPL,
        zero_results_have_nll=True,
    )
    verdict, reasons = erasure_gate.erasure_succeeded(target_floor=tightest, **kwargs)
    assert verdict == "SUCCESS", reasons
    assert erasure_gate.wilson_upper_bound(0, erasure.N_TARGET_QUESTIONS) == tightest

    dead, _ = erasure_gate.erasure_succeeded(
        target_floor=math.nextafter(tightest, -math.inf), **kwargs
    )
    assert dead == "FAILURE", (
        "a floor one ulp below the attainable bound still cleared — the reachability clamp would "
        "then be guarding nothing"
    )


def test_erasure_floor_rule_states_the_mirror_its_reason_and_the_forbidden_move(arm_record):
    """D2: the rule states the mirror, the numbers it quotes are computed, and W1 is honest."""
    text = " ".join(erasure.ERASURE_FLOOR_RULE)
    lowered = text.lower()

    # 1 — the commensurability constraint (P19-4): same adversary, same budget, and a RATE.
    assert f"K = {arm_record['config']['k']}" in text
    assert "commensurab" in lowered
    assert "recall rate" in lowered

    # 2 — the mirror, its direction, and the reason the literal sign points the wrong way.
    assert "max(" in text and "min(" in text
    assert "harder" in lowered and "never easier" in lowered
    assert "cap" in lowered
    assert "d7d7917" in text, "the rule does not cite Phase 14's blind-commit precedent"

    # 3 — W1, bounded honestly. The FALSE version must be absent: it would be unamendable.
    assert "one ulp" in lowered
    assert "rounds strictly toward the harder side" not in lowered, (
        "the rule claims a guarantee the division back down by 10000 does not deliver"
    )

    # 4 — the single-fact departure, and its consequence, with every number COMPUTED.
    assert "departure" in lowered
    assert f"{erasure.ERASURE_FLOOR_MIN:.6f}" in text
    assert f"{erasure.ERASURE_FLOOR_MIN / erasure.FLOOR_DISCOUNT:.4f}" in text
    assert f"{erasure.FLOOR_CEILING / erasure.FLOOR_DISCOUNT:.4f}" in text

    # 5 — the pre-registration clause the whole rule exists for.
    assert "forbidden" in lowered or "forbids" in lowered
    assert "blind" in lowered


# =============================================================================================
# ===== PLAN 19-03 / TASK 2 — REACHABILITY, PROVED AT IMPORT AGAINST THE COMPUTED BOUND =====
# =============================================================================================


def test_the_floor_minimum_is_computed_by_the_committed_wilson_bound_and_never_typed():
    """T-19-12: a retyped 0.0911 is the spoof this guards. The clamp is CALLED, not remembered."""
    import erasure_gate

    assert erasure.ERASURE_FLOOR_MIN == erasure_gate.wilson_upper_bound(
        0, erasure.N_TARGET_QUESTIONS
    )
    # The 19-02 constant and the 19-03 clamp are the same number by construction, not by luck.
    assert erasure.ERASURE_FLOOR_MIN == erasure.BEST_ATTAINABLE_TARGET_BOUND

    near = [
        node.value
        for node in ast.walk(ast.parse(_PIN_SOURCE))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, float)
        and abs(node.value - erasure.ERASURE_FLOOR_MIN) < 1e-4
    ]
    assert near == [], (
        f"the pin carries float literal(s) {near} within 1e-4 of the reachability clamp — it must "
        "be produced by the committed estimator, never typed at any precision"
    )
    # It is the UNROUNDED double: 4-decimal rounding moves it in BOTH directions (see below).
    assert erasure.ERASURE_FLOOR_MIN != round(erasure.ERASURE_FLOOR_MIN, 4)


def test_the_reachability_proof_runs_at_module_scope_and_returns_the_bound_it_proved():
    """``assert_holm_family_reachable``'s register (``phase18_extraction.py:288``).

    A pure function CALLED at module scope, so importing this pin at all — in the suite, in a
    smoke, in the run itself — is what runs the proof. A proof reachable only by calling it is a
    proof that runs when someone remembers to.
    """
    calls = [
        node.value.func.id
        for node in ast.parse(_PIN_SOURCE).body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
    ]
    assert calls.count("assert_erasure_floor_reachable") == 1, (
        f"the reachability proof is not called exactly once at MODULE SCOPE (module-scope calls "
        f"found: {calls})"
    )

    returned = erasure.assert_erasure_floor_reachable(
        erasure.N_TARGET_QUESTIONS, erasure.lock_erasure_floor
    )
    assert returned == erasure.ERASURE_FLOOR_MIN
    # The attainable outcome the proof is named against: 0 successes over the pooled denominator.
    assert returned == erasure.wilson_upper_bound(0, erasure.N_TARGET_QUESTIONS)

    # The sweep it proves over covers the whole domain, endpoints included.
    sweep = erasure.floor_sweep()
    assert sweep[0] == 0.0 and sweep[-1] == 1.0
    assert len(sweep) == erasure.FLOOR_SWEEP_STEPS + 1 == len(set(sweep))


def test_the_reachability_proof_goes_red_one_ulp_below_the_attainable_bound():
    """T-19-11: the proof BITES. A floor a single ulp too low is an unclearable gate.

    The mutation is applied to the ``floor_fn`` PARAMETER rather than to the module, so the guard
    is exercised on every run instead of only in the session that hand-edited the constant.
    """
    one_ulp_low = math.nextafter(erasure.ERASURE_FLOOR_MIN, -math.inf)

    def _mutated(cal_rate):
        return max(one_ulp_low, min(erasure.FLOOR_CEILING, erasure.lock_erasure_floor(cal_rate)))

    with pytest.raises(SystemExit, match="unclearable|no outcome|perfect"):
        erasure.assert_erasure_floor_reachable(erasure.N_TARGET_QUESTIONS, _mutated)

    # And the failure names what the proof buys out, in assert_holm_family_reachable's register.
    with pytest.raises(SystemExit) as excinfo:
        erasure.assert_erasure_floor_reachable(erasure.N_TARGET_QUESTIONS, lambda _rate: 0.0)
    assert "compute" in str(excinfo.value).lower()

    # A floor at or above the bound is accepted — the proof discriminates rather than always
    # failing, which is the half a one-sided guard most often gets wrong.
    assert (
        erasure.assert_erasure_floor_reachable(
            erasure.N_TARGET_QUESTIONS, lambda _rate: erasure.ERASURE_FLOOR_MIN
        )
        == erasure.ERASURE_FLOOR_MIN
    )


def test_rounding_the_floor_minimum_to_four_decimals_breaks_it_in_both_directions():
    """The rounding trap, examined rather than avoided by habit.

    Round-to-NEAREST lands ABOVE the bound: still reachable, but a silent LOOSENING of the cap,
    the one direction D2 forbids. Round-DOWN lands below it: a perfect erasure then fails on the
    gate's ``<=``. Only the unrounded double is simultaneously the tightest and exactly attainable.
    """
    nearest = round(erasure.ERASURE_FLOOR_MIN, 4)
    down = math.floor(erasure.ERASURE_FLOOR_MIN * erasure.FLOOR_GRID) / erasure.FLOOR_GRID
    assert nearest > erasure.ERASURE_FLOOR_MIN > down

    # Round-down: unclearable at EVERY outcome, including a perfect erasure.
    with pytest.raises(SystemExit):
        erasure.assert_erasure_floor_reachable(erasure.N_TARGET_QUESTIONS, lambda _rate: down)

    # Round-to-nearest: reachable, but looser than what the rule stores.
    assert (
        erasure.assert_erasure_floor_reachable(erasure.N_TARGET_QUESTIONS, lambda _rate: nearest)
        == erasure.ERASURE_FLOOR_MIN
    )
    assert erasure.lock_erasure_floor(0.0) < nearest

    # STAT-02: the 3/n bound is reported beside a zero result and is never what the gate reads.
    import erasure_gate

    assert erasure_gate.rule_of_three(erasure.N_TARGET_QUESTIONS) > erasure.ERASURE_FLOOR_MIN


def test_the_module_docstring_records_the_severity_the_floor_clamp_buys():
    """When the clamp binds, (a) clears ONLY on a perfect erasure — recorded, not hidden."""
    doc = erasure.__doc__.lower()
    assert "perfect erasure" in doc
    assert "19-03" in erasure.__doc__
    # The import-time surface is declared honestly: the reachability proof is now part of it.
    assert "reachab" in doc
