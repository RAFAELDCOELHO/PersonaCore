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
import re

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
        """``lock_erasure_floor``'s EXPRESSION with the clamp constant moved down by one ulp.

        Wrapping ``lock_erasure_floor``'s OUTPUT would be a no-op — it is already clamped at the
        unmutated value, so the outer ``max`` would never bind and the mutation would prove
        nothing. The clamp itself has to move, which is why the discount is recomputed here.
        """
        return max(one_ulp_low, min(erasure.FLOOR_CEILING, _grid_oracle(cal_rate)))

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

    # Prose numbers are asserted against the functions that compute them (the 19-02 discipline),
    # so a pinned sentence cannot quote a figure that stopped being true.
    assert f"{erasure.ERASURE_FLOOR_MIN / erasure.FLOOR_DISCOUNT:.4f}" in erasure.__doc__
    assert (
        f"wilson_upper_bound(0, {erasure.N_TARGET_QUESTIONS}) = "
        f"{erasure.ERASURE_FLOOR_MIN:.6f}" in erasure.assert_erasure_floor_reachable.__doc__
    )


# =============================================================================================
# ===== PLAN 19-04 / TASK 1 — THE (c) DIALOGUE NOISE FLOOR AND THE RETENTION MEASUREMENT =====
# =============================================================================================
#
# `erasure_succeeded` is keyword-only and three of its arguments have NO committed default. This
# section covers the two on the (c) side. `dialogue_ppl_noise_floor` (`erasure_gate.py:208`) is
# the one nobody notices is missing: it is threshold-shaped, the only value this repo has ever
# measured for it came off a FULL-FINE-TUNE regime, and a noise floor chosen after seeing whether
# it clears the cap is precisely the failure mode `23a830c` exists to prevent. `retention_ppl` has
# never been measured on an ADAPTED model at all. Both are pinned as estimators, with their seed
# pair and their arm config, BEFORE either number exists.


def _teach_persona():
    """The committed teaching recipe. Loaded HERE and never in the pin, which holds no fact set."""
    return _load("teach_persona", "scripts/teach_persona.py")


def _gate_reason_cap(noise_floor):
    """The dialogue cap as `erasure_succeeded` ITSELF computes it, read out of its own reason.

    The gate computes the cap in a local (`erasure_gate.py:245`) and never returns it, so its
    arithmetic is observable only through the `(c)` reason string. Parsing that string is what
    makes the comparison a check against the gate rather than against a second copy of the
    expression written in the test.
    """
    import erasure_gate

    _verdict, reasons = erasure_gate.erasure_succeeded(
        target_successes=0,
        target_questions=erasure.N_TARGET_QUESTIONS,
        target_floor=erasure.ERASURE_FLOOR_MIN,
        nontarget_deltas=[0.0],
        nontarget_noise_floor=0.01,
        dialogue_ppl=1.0,
        dialogue_ppl_noise_floor=noise_floor,
        retention_ppl=1.0,
        zero_results_have_nll=True,
    )
    (line,) = [r for r in reasons if r.startswith("(c)")]
    return line.split("vs cap ")[1].split(";")[0]


def test_the_dialogue_noise_floor_estimator_pins_its_seed_pair_and_its_arm_config():
    """T-19-13: the estimator, the seeds and every recipe constant, committed before the number.

    A spread measured across two seeds AND a changed recipe measures the recipe. The estimator is
    therefore only meaningful if the seven other knobs are pinned in the same commit as the seeds.
    """
    tp = _teach_persona()
    text = " ".join(erasure.DIALOGUE_NOISE_FLOOR_ESTIMATOR)
    lowered = text.lower()

    # The seed pair, PINNED — and its head is the production seed, re-derived rather than trusted.
    assert erasure.DIALOGUE_NOISE_FLOOR_SEEDS[0] == tp.SEED
    assert len(erasure.DIALOGUE_NOISE_FLOOR_SEEDS) == 2
    assert len(set(erasure.DIALOGUE_NOISE_FLOOR_SEEDS)) == 2, "a 'seed pair' of one seed"
    assert str(erasure.DIALOGUE_NOISE_FLOOR_SEEDS).replace(" ", "") in text.replace(" ", "")

    # The estimator names its instrument and the arm it reads, not merely "dialogue PPL".
    assert "masked_perplexity" in text
    assert "run_collapse_control" in text
    assert "adapter-on" in lowered or "adapter on" in lowered

    # Every recipe constant is named, and each one is checked against the live committed value —
    # a pinned recipe that has quietly stopped matching `teach_persona` pins nothing.
    for rendered, live in (
        ("3e-4", tp.LR),
        ("0.0", tp.WEIGHT_DECAY),
        ("8", tp.BATCH_SIZE),
        ("200", tp.MAX_STEPS),
        ("20", tp.WARMUP_STEPS),
        ("False", tp.REAL_RUN_SECOND_PERSON),
        ("1.0", tp.REAL_RUN_REPLAY_RATIO),
    ):
        # `or` short-circuits, so the boolean never reaches `float()`; the LR is the one knob
        # whose committed repr (0.0003) differs from the rendering the recipe is quoted in.
        assert rendered == str(live) or float(rendered) == float(live), (
            f"the pinned recipe renders {rendered} where the committed value is {live}"
        )
        assert rendered in text, f"the estimator does not pin the recipe constant {rendered}"
    assert "REAL_RUN_SECOND_PERSON" in text and "REAL_RUN_REPLAY_RATIO" in text

    # The adapter-OFF arm is REFUSED, with the measurement that makes it vacuous.
    assert "refus" in lowered
    assert "adapter_disabled" in text or "adapter-off" in lowered
    assert "0.0" in text  # the bit-identity max abs diff — a trivially passing, blind measurement


def test_dialogue_noise_floor_is_an_absolute_difference_and_refuses_a_non_measurement():
    """|ΔPPL| over a seed pair — symmetric, and closed to anything that is not a perplexity.

    `math` is unavailable in the pin (T-19-08), so non-finiteness is detected with `x != x` and a
    comparison against `float("inf")`. The lower guard is `>= 1.0` and not `>= 0.0`: a masked CE is
    a sum of non-negative terms, so `exp(mean CE) >= 1` is arithmetic rather than convention, and
    the realistic mistake this function invites is being handed a DELTA where a PPL belongs.
    """
    assert erasure.dialogue_noise_floor(4.470551, 4.472255) == abs(4.470551 - 4.472255)
    assert erasure.dialogue_noise_floor(4.472255, 4.470551) == erasure.dialogue_noise_floor(
        4.470551, 4.472255
    )
    assert erasure.dialogue_noise_floor(4.5, 4.5) == 0.0

    for bad in (float("nan"), float("inf"), -float("inf"), -1.0, 0.0, 0.001704):
        with pytest.raises(SystemExit, match="perplexity|finite"):
            erasure.dialogue_noise_floor(4.5, bad)
        with pytest.raises(SystemExit, match="perplexity|finite"):
            erasure.dialogue_noise_floor(bad, 4.5)


def test_dialogue_cap_reproduces_the_gates_own_arithmetic_across_a_swept_range():
    """STAT-05: the cap is the GATE's, imported and never retyped — proved over a swept range."""
    import erasure_gate

    assert erasure.V20_MASKED_DIALOGUE_VAL_PPL is erasure_gate.V20_MASKED_DIALOGUE_VAL_PPL
    assert erasure.MARGIN_K is erasure_gate.MARGIN_K

    sweep = [x / 100 for x in range(0, 101)]
    for noise_floor in sweep:
        assert f"{erasure.dialogue_cap(noise_floor):.4f}" == _gate_reason_cap(noise_floor)

    # And at full precision, behaviourally: the gate's `<=` passes AT the cap and fails one ulp
    # above it. A 4-decimal string agreement would survive a cap that was wrong in the 5th.
    def _verdict(dialogue_ppl, noise_floor):
        return erasure_gate.erasure_succeeded(
            target_successes=0,
            target_questions=erasure.N_TARGET_QUESTIONS,
            target_floor=erasure.ERASURE_FLOOR_MIN,
            nontarget_deltas=[0.0],
            nontarget_noise_floor=0.01,
            dialogue_ppl=dialogue_ppl,
            dialogue_ppl_noise_floor=noise_floor,
            retention_ppl=erasure_gate.V20_EWC_RETENTION_PPL
            + erasure_gate.MARGIN_K * erasure_gate.V20_RETENTION_NOISE_FLOOR,
            zero_results_have_nll=True,
        )[0]

    for noise_floor in (0.0, erasure.V20_DIALOGUE_NOISE_FLOOR_FULL_FT, 0.5, 1.0):
        cap = erasure.dialogue_cap(noise_floor)
        assert _verdict(cap, noise_floor) == "SUCCESS"
        assert _verdict(math.nextafter(cap, math.inf), noise_floor) == "FAILURE"


def test_the_pre_erasure_dialogue_excess_is_on_the_record_before_the_erasure():
    """The (c) gap that PREDATES the erasure, pinned with both its published sources.

    A (c) failure that was already there and a (c) failure the erasure caused are different
    findings, and the only thing that separates them is having both numbers on the record before
    the run. Every derived figure here is computed from the imported constants, never typed.
    """
    text = " ".join(erasure.DIALOGUE_NOISE_FLOOR_ESTIMATOR)

    # Both published inputs trace to the reports the estimator cites, checked against the files.
    smoke = (_ROOT / "results" / "finetune_smoke_report.md").read_text(encoding="utf-8")
    recall = (_ROOT / "results" / "phase14_recall_report.md").read_text(encoding="utf-8")
    assert f"{erasure.V20_DIALOGUE_NOISE_FLOOR_FULL_FT:.6f}" in smoke
    assert f"{erasure.V20_TAUGHT_ADAPTER_DIALOGUE_PPL:.4f}" in recall
    assert "finetune_smoke_report.md" in text and "phase14_recall_report.md" in text
    # The seed pair that produced it is the SAME pair the retention half of that table used, and
    # that retention half is what the gate already reads as its noise floor.
    assert "(1337,2024)" in text.replace(" ", "")
    assert f"{erasure.V20_RETENTION_NOISE_FLOOR:.6f}" in text

    cap_at_full_ft = erasure.dialogue_cap(erasure.V20_DIALOGUE_NOISE_FLOOR_FULL_FT)
    excess = erasure.V20_TAUGHT_ADAPTER_DIALOGUE_PPL - cap_at_full_ft
    required = (
        erasure.V20_TAUGHT_ADAPTER_DIALOGUE_PPL - erasure.V20_MASKED_DIALOGUE_VAL_PPL
    ) / erasure.MARGIN_K
    assert f"{cap_at_full_ft:.6f}" in text
    assert f"{excess:+.4f}" in text
    assert f"{required:.5f}" in text
    assert f"{required / erasure.V20_DIALOGUE_NOISE_FLOOR_FULL_FT:.0f}x" in text
    assert excess > 0.0, "the pre-erasure excess is the whole reason this clause exists"
    # The claim about it is UNVERIFIED and says so — the estimator is how it becomes verified.
    assert "unverified" in text.lower()
    assert "publishes" in text.lower() or "published" in text.lower()


def test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent():
    """Q4: `retention_perplexity` has never been called on a LoRA-adapted model. Measured here."""
    from personacore.config import ModelConfig

    text = " ".join(erasure.RETENTION_MEASUREMENT)

    assert "retention_perplexity" in text
    assert "data/retention_val.bin" in text
    assert f"{ModelConfig.block_size}" in text
    assert "pre" in text.lower() and "post" in text.lower()
    assert "same process" in text.lower()

    # The census, MEASURED rather than quoted: every call site, and the fact that none of the
    # modules holding one so much as imports the injection path.
    call_sites = []
    for path in sorted(_ROOT.glob("scripts/*.py")) + sorted((_ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == (
                "retention_perplexity"
            ):
                call_sites.append(path)
    modules = sorted({path.name for path in call_sites})
    assert len(call_sites) == 6 and len(modules) == 4, (
        f"the retention call-site census moved: {len(call_sites)} calls in {modules}"
    )
    for name in modules:
        source = next(p for p in call_sites if p.name == name).read_text(encoding="utf-8")
        assert "inject_lora" not in source and "load_adapter" not in source, (
            f"{name} reaches the injection path — the 'no adapted precedent' claim is stale"
        )
    assert f"{len(call_sites)} call sites" in text and f"{len(modules)} modules" in text

    # (c)'s retention half is FULLY determined; nothing about it is open. Computed, not typed.
    cap = erasure.V20_EWC_RETENTION_PPL + erasure.MARGIN_K * erasure.V20_RETENTION_NOISE_FLOOR
    assert f"{cap:.6f}" in text
    assert f"{erasure.V20_EWC_RETENTION_PPL:.6f}" in text


# =============================================================================================
# ===== PLAN 19-04 / TASK 2 — THE (b) NOISE FLOOR, PER FACT, NEVER POOLED (D4/B5) =====
# =============================================================================================
#
# `erasure_succeeded` reads TWO things on the (b) side: a sequence it takes `max` of, and a scalar
# it multiplies by `MARGIN_K` (`erasure_gate.py:236-237`). The scalar is therefore threshold-shaped
# in exactly the way `dialogue_ppl_noise_floor` is, and the REDUCTION that produces it from seven
# per-fact numbers is a choice that has to be made before the seven numbers exist.


def _rows(**by_slot):
    """`{fact_id: row}` in `target_rows_from_arm_record`'s shape, over the seven non-targets.

    `by_slot` is `{slot: successes}`; every unnamed non-target slot scores 0. Denominators are the
    pooled per-fact question count, which is what the (b) contract requires each row to carry.
    """
    n = erasure.N_TARGET_QUESTIONS
    return {
        f"synthetic_{slot}": {
            "slot": slot,
            "n_answerable": by_slot.get(slot, 0),
            "n_questions": n,
            "rate": by_slot.get(slot, 0) / n,
        }
        for slot in erasure.GATED_NONTARGET_SLOTS
    }


def test_the_nontarget_estimator_pins_the_replicate_its_declined_alternative_and_its_precedent():
    """D4: what the (b) floor is, why the retrain was declined, and what precedent it follows."""
    text = " ".join(erasure.NONTARGET_NOISE_FLOOR_ESTIMATOR)
    lowered = text.lower()

    # The estimator itself: a seed-stride replicate on the UNERASED adapter, same everything else.
    assert "seed-stride" in lowered or "seed stride" in lowered
    assert "unerased" in lowered
    assert "replicate" in lowered

    # The DECLINED alternative, with its reason — a decline recorded as a decline (19-01's D1).
    assert "retrain" in lowered
    assert "declined" in lowered or "decline" in lowered
    assert "confound" in lowered

    # The precedent it follows: two committed descriptive-never-gated seed registers.
    assert "REPLICATION_SEEDS" in text
    assert "taught_replication" in text

    # The cost and the pairing — the pre-erasure rates are already committed, so it is ONE run.
    assert "phase18_arm_adapter-on.json" in text
    assert "10,368" in text or "10368" in text
    assert "172" in text

    # The two traps the rule sets, both of them intended.
    assert "one destroyed fact" in lowered
    assert "inconclusive" in lowered
    assert "stat-06" in lowered or "STAT-06" in text


def test_nontarget_deltas_is_per_fact_over_exactly_the_seven_and_has_no_pooled_path():
    """T-19-14: seven per-fact values with their own denominators, and no way to return one."""
    import inspect

    pre = _rows()
    post = _rows(**{erasure.GATED_NONTARGET_SLOTS[0]: 3})

    deltas = erasure.nontarget_deltas(pre, post)
    assert len(deltas) == len(erasure.GATED_NONTARGET_SLOTS) == 7
    assert deltas[0] == 3 / erasure.N_TARGET_QUESTIONS
    assert list(deltas[1:]) == [0.0] * 6
    # Order is the committed slot order, so a report zips the values against a pinned constant
    # rather than against whatever order a dict happened to be built in.
    assert erasure.nontarget_deltas(post, pre) == deltas, "the delta is ABSOLUTE, not signed"

    # The seven are the eight core gated slots MINUS the target, derived and not enumerated.
    assert erasure.TARGET_SLOT not in erasure.GATED_NONTARGET_SLOTS
    assert set(erasure.GATED_NONTARGET_SLOTS) | {erasure.TARGET_SLOT} == set(
        erasure.CORE_GATED_SLOTS
    )

    # NO POOLED RETURN PATH EXISTS. Two parameters, one return, and nothing that could collapse
    # seven numbers into one — the collapse is a separate, named, pinned function.
    assert list(inspect.signature(erasure.nontarget_deltas).parameters) == ["pre_rows", "post_rows"]
    (fn,) = [
        node
        for node in ast.walk(ast.parse(_PIN_SOURCE))
        if isinstance(node, ast.FunctionDef) and node.name == "nontarget_deltas"
    ]
    assert len([n for n in ast.walk(fn) if isinstance(n, ast.Return)]) == 1
    for banned in ("sum", "mean", "max", "min"):
        assert banned not in {
            n.func.id
            for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }, f"nontarget_deltas reduces with {banned}() — the reduction is a separate pinned function"

    # An EMPTY result is impossible by construction: `erasure_succeeded` turns an empty sequence
    # into INCONCLUSIVE (`erasure_gate.py:253-254`), so the refusal has to happen here.
    with pytest.raises(SystemExit, match="seven|non-target"):
        erasure.nontarget_deltas({}, {})
    with pytest.raises(SystemExit, match="seven|non-target"):
        erasure.nontarget_deltas(
            {
                **pre,
                "the_target": {
                    "slot": erasure.TARGET_SLOT,
                    "n_answerable": 0,
                    "n_questions": erasure.N_TARGET_QUESTIONS,
                    "rate": 0.0,
                },
            },
            post,
        )


def test_nontarget_deltas_refuses_a_draw_rate_and_a_mismatched_denominator():
    """The QUESTION unit, enforced twice — by the denominator and by the rate's own identity."""
    pre, post = _rows(), _rows()

    # A draw-rate row: the same numerator over K x the questions. `erasure_gate`'s clustering note
    # rules that unit out, so it is refused rather than silently narrowing every (b) comparison.
    draw_rate = {k: dict(v) for k, v in post.items()}
    first = erasure.GATED_NONTARGET_SLOTS[0]
    draw_rate[f"synthetic_{first}"]["n_questions"] = erasure.N_TARGET_QUESTIONS * 48
    with pytest.raises(SystemExit, match="question"):
        erasure.nontarget_deltas(pre, draw_rate)

    # A rate that does not equal its own successes/questions — the shape a draw rate takes when
    # the denominator column was left alone and only the rate moved.
    inconsistent = {k: dict(v) for k, v in post.items()}
    inconsistent[f"synthetic_{first}"]["rate"] = 0.5
    with pytest.raises(SystemExit, match="rate"):
        erasure.nontarget_deltas(pre, inconsistent)

    # Pre and post must cover the same facts: a delta against a fact that is not in both is a
    # delta against nothing.
    with pytest.raises(SystemExit, match="seven|non-target|same"):
        erasure.nontarget_deltas(pre, {k: v for k, v in post.items() if k != f"synthetic_{first}"})


def test_the_nontarget_reduction_is_max_and_swapping_in_mean_changes_the_scalar():
    """The reduction is a COMMITTED choice, and its honest direction is recorded with it.

    `max` is the MORE PERMISSIVE of the two, not the conservative one: `mean <= max` and `b_ok` is
    `worst <= 2 x floor`, so a mean floor is strictly the harder gate. It is chosen for
    commensurability with the `max` the gate already takes on the numerator side, and the pin says
    so — a later auditor asking "did they pick the conservative reduction?" must not be told yes
    by a sentence that does not survive checking.
    """
    import erasure_gate

    spread = [0.01, 0.02, 0.03, 0.10]
    assert erasure.nontarget_noise_floor(spread) == max(spread)
    assert erasure.nontarget_noise_floor(spread) != sum(spread) / len(spread)

    def _verdict(floor):
        return erasure_gate.erasure_succeeded(
            target_successes=0,
            target_questions=erasure.N_TARGET_QUESTIONS,
            target_floor=erasure.ERASURE_FLOOR_MIN,
            nontarget_deltas=spread,
            nontarget_noise_floor=floor,
            dialogue_ppl=1.0,
            dialogue_ppl_noise_floor=0.0,
            retention_ppl=1.0,
            zero_results_have_nll=True,
        )[0]

    assert _verdict(erasure.nontarget_noise_floor(spread)) == "SUCCESS"
    assert _verdict(sum(spread) / len(spread)) == "FAILURE"

    # The direction generalises — WITH ITS BOUND. `mean <= max` is exact arithmetic, but the naive
    # `sum(v)/len(v)` re-rounds and can land ONE ULP above `max(v)`. Measured over 200,003 vectors
    # of length 1..7 (200,000 random plus 3 hand cases): 2 exceed, both by exactly 1.0 ulp, both
    # constant vectors. The bound is asserted; the unqualified claim is NOT, because it is false.
    exceeded = []
    for values in ([0.5], [0.0, 1.0], [0.2, 0.2, 0.2], [0.1, 0.1, 0.1], [0.2] * 7, spread):
        naive_mean = sum(values) / len(values)
        top = erasure.nontarget_noise_floor(values)
        assert naive_mean <= top + math.ulp(top)
        if naive_mean > top:
            exceeded.append((values, (naive_mean - top) / math.ulp(top)))
    assert [ulps for _values, ulps in exceeded] == [1.0, 1.0], (
        f"the one-ulp residual the rule records moved: {exceeded}"
    )

    text = " ".join(erasure.NONTARGET_NOISE_FLOOR_ESTIMATOR)
    lowered = text.lower()
    assert "more permissive" in lowered
    assert "commensurab" in lowered
    # The FALSE, stronger sentence must be absent — it would be unamendable after 19-07.
    assert "mean <= max always" not in lowered
    assert "one ulp" in lowered, "the rule states the ordering without its measured residual"
    assert f"{erasure_gate.MARGIN_K * max(spread):.6f}" in text
    assert f"{erasure_gate.MARGIN_K * (sum(spread) / len(spread)):.6f}" in text

    # A degenerate input is refused rather than reduced: `max([])` raises a bare ValueError and
    # a floor of 0.0 would make (b) pass only on a bit-identical model.
    with pytest.raises(SystemExit, match="empty|no non-target"):
        erasure.nontarget_noise_floor([])


def test_the_seed_stride_offset_cannot_collide_with_phase_18s_windows():
    """A replicate that re-reads the same generator states is a re-read, not a replicate."""
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")
    record = json.loads(_ARM_RECORD.read_text(encoding="utf-8"))
    k = record["config"]["k"]

    # Phase 18's stride, quoted from the record it produced rather than from the source.
    assert "seed_index" in record["config"]["seed_stride"]
    assert erasure.SEED_STRIDE_OFFSET > 0

    # The widest window Phase 18 could have consumed on the committed fixture.
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    highest = max(
        row["seed_index"] for tier in extraction.CORPUS_TIERS for row in fixture["questions"][tier]
    )
    assert erasure.SEED_STRIDE_OFFSET >= (highest + 1) * k

    # Every replicate window starts strictly above every Phase 18 window on this fixture.
    for seed_index in (0, 1, highest):
        assert erasure.replicate_seed_stride(seed_index, k) >= (highest + 1) * k
        assert erasure.replicate_seed_stride(seed_index, k) != seed_index * k

    # And the guard BITES: an offset that a question's own Phase 18 window would reach into is
    # refused rather than silently producing a replicate of the same draws.
    with pytest.raises(SystemExit, match="collide|stride|overlap"):
        erasure.replicate_seed_stride(erasure.SEED_STRIDE_OFFSET, k)


def test_the_soft_tier_narrowing_is_declared_with_its_measured_reason(arm_record):
    """B5: (b) is gated on SEVEN, the literal rule says nine, and the gap is declared not silent."""
    facts = _load("phase14_factset", "scripts/phase14_factset.py")
    text = " ".join(erasure.SOFT_TIER_DESCRIPTIVE_READ)

    # The two soft slots are named — by SLOT, because every soft fact_id ends in its own value.
    assert erasure.SOFT_TIER_SLOTS == tuple(f.slot for f in facts.SOFT_TIER_FACTS)
    for slot in erasure.SOFT_TIER_SLOTS:
        assert slot in text
    # The literal domain the gate's own rule states is NINE, and the pin says that out loud.
    taught = len(facts.LOCKED_FACTS) + len(facts.SOFT_TIER_FACTS)
    assert taught == 10
    assert f"{taught - 1}" in text and "nine" in text.lower()
    assert f"{len(erasure.GATED_NONTARGET_SLOTS)}" in text or "seven" in text.lower()

    # THE MEASURED REASON: the committed arm record holds no `soft` draws at all, so the two soft
    # facts have no A2/K=48 pre-erasure baseline to pair a delta against.
    tiers = {draw["tier"] for draw in arm_record["draws"]}
    assert tiers == set(_load("phase18_extraction", "scripts/phase18_extraction.py").CORPUS_TIERS)
    assert not any(draw["tier"] == "soft" for draw in arm_record["draws"])
    # And the absence is a property of the ARM RECORD, not of the fixture — the fixture does hold
    # soft questions, which is what makes the post-erasure descriptive read possible at all.
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert len(fixture["questions"]["soft"]) == len(facts.SOFT_TIER_FACTS) * (
        erasure.N_TARGET_QUESTIONS
    )
    assert "soft" in text and "descriptive" in text.lower()
    assert "never gated" in text.lower() or "not gated" in text.lower()

    # Still no fact value anywhere in the pin — the slots carry the narrowing, the ids do not.
    forbidden = [f.value.lower() for f in facts.LOCKED_FACTS + facts.SOFT_TIER_FACTS]
    assert [v for v in forbidden if v in _PIN_SOURCE.lower()] == []


# =============================================================================================
# ===== PLAN 19-04 / TASK 3 — THE RECORD SCHEMA, AND A ZERO THAT CANNOT REACH THE VERDICT =====
# =============================================================================================
#
# `erasure_succeeded` short-circuits to INCONCLUSIVE when `target_successes == 0` and
# `zero_results_have_nll` is False (`erasure_gate.py:223-227`) — and a SUCCESSFUL erasure produces
# exactly that zero. So the one clause standing between a real success and INCONCLUSIVE is this
# flag, and it has to be structural rather than a boolean someone remembers to set.


def _extraction():
    return _load("phase18_extraction", "scripts/phase18_extraction.py")


_UNSET = object()  # a distinct sentinel: `None` is one of the values under test, not an absence


def _exposure_record(slot, drop_frame=None, value=_UNSET):
    """One `EXPOSURE_RECORD_KEYS`-shaped record, in the committed key ORDER."""
    extraction = _extraction()
    nll = 0.5 if value is _UNSET else value
    frames = {
        frame: {reduction: nll for reduction in extraction.NLL_REDUCTIONS}
        for frame in extraction.NLL_FRAMES
        if frame != drop_frame
    }
    return {
        "slot": slot,
        "admissible": [extraction.ADMISSIBLE_NLL_FRAME, extraction.ADMISSIBLE_NLL_REDUCTION],
        "nll": frames,
        "rank": 1,
        "exposure_bits": 1.0,
        "ceiling_bits": 4.0,
        "n_references": 20,
        "length_spread": [1, 2],
        "spread_zero_control": 0.0,
        "descriptive_label": extraction.EXPOSURE_DESCRIPTIVE_LABEL,
        "threats_to_validity": "synthetic fixture",
    }


def _per_fact(zero_slots=()):
    """`{fact_id: row}` over all EIGHT core slots; the named ones score zero questions."""
    n = erasure.N_TARGET_QUESTIONS
    return {
        f"synthetic_{slot}": {
            "slot": slot,
            "n_answerable": 0 if slot in zero_slots else n,
            "n_questions": n,
            "rate": 0.0 if slot in zero_slots else 1.0,
        }
        for slot in erasure.CORE_GATED_SLOTS
    }


def _erasure_arm(zero_slots=(), exposure=None, pre_exposure=None, **overrides):
    """A complete Phase 19 arm record — the shape `_arm_record` proves and nothing else."""
    slots = erasure.CORE_GATED_SLOTS
    block = {
        "arm": "erased",
        "config": {
            # All eight comparability columns, because 19-05 made them REQUIRED: Phase 18 recorded
            # only four and the other four had to be reconstructed from their owning modules to
            # check parity at all. This arm carries the deliberately OFFSET replicate stride, which
            # is exactly the case `assert_phase18_parity` is not for.
            **{
                key: erasure.phase18_parity_values()[key]
                for key in erasure.PARITY_KEYS
                if key not in ("corpus_sha256", "seed_stride")
            },
            "corpus_sha256": "0" * 64,
            "seed_stride": f"SEED_STRIDE_OFFSET + seed_index * K ({erasure.SEED_STRIDE_OFFSET})",
            "mechanism": erasure.MECHANISM_ID,
            "ablated_components": [],
        },
        "draw_record_keys": ["fact_id", "slot", "tier", "seed_index", "completions"],
        "draws": [],
        "exposure": [_exposure_record(s) for s in slots] if exposure is None else exposure,
        "dialogue_ppl": {"adapter_on": 5.0, "adapter_off": 4.5733, "n_targets": 270203},
        "retention_ppl": 3.9,
        "pre_erasure": {
            "per_fact": _per_fact(),
            "exposure": (
                [_exposure_record(s) for s in slots] if pre_exposure is None else pre_exposure
            ),
            "dialogue_ppl": {"adapter_on": 5.8154, "adapter_off": 4.5733, "n_targets": 270203},
            "retention_ppl": 3.9,
        },
        "per_fact": _per_fact(zero_slots),
    }
    block.update(overrides)
    return block


def test_the_arm_record_schema_is_an_ordered_hard_equality_with_a_paired_pre_erasure_block():
    """`_exposure_record`'s register (`phase18_extraction.py:1344-1358`) — red at the write."""
    record = erasure._arm_record(**_erasure_arm())
    assert tuple(record) == erasure.ARM_RECORD_KEYS

    # A dropped field is red at the commit that writes it, not as a KeyError in a renderer after
    # the run has been spent. Every single key is load-bearing, so every single one is checked.
    for dropped in erasure.ARM_RECORD_KEYS:
        fields = {k: v for k, v in _erasure_arm().items() if k != dropped}
        with pytest.raises(SystemExit, match="schema|keys"):
            erasure._arm_record(**fields)

    # ORDERED, not merely equal as a set: keyword order is what the proof reads.
    shuffled = _erasure_arm()
    reordered = {k: shuffled[k] for k in reversed(erasure.ARM_RECORD_KEYS)}
    with pytest.raises(SystemExit, match="schema|keys"):
        erasure._arm_record(**reordered)

    # The PAIRED pre-erasure block, in the same schema, so every published movement is a delta
    # against a measured baseline rather than an absolute number read against nothing.
    assert tuple(record["pre_erasure"]) == erasure.PRE_ERASURE_KEYS
    for dropped in erasure.PRE_ERASURE_KEYS:
        broken = _erasure_arm()
        broken["pre_erasure"] = {k: v for k, v in broken["pre_erasure"].items() if k != dropped}
        with pytest.raises(SystemExit, match="pre-erasure|pre_erasure"):
            erasure._arm_record(**broken)

    # The dialogue PPL is the ON/OFF PAIR plus its denominator — `run_collapse_control` proves the
    # two arms scored the same `n_targets`, and a single number would not carry that evidence.
    assert tuple(record["dialogue_ppl"]) == erasure.DIALOGUE_PPL_KEYS


def test_the_forbid_digest_is_pinned_to_phase_18s_and_required_in_config(arm_record):
    """T-19-16: a different mask makes the post-erasure number incomparable with Phase 18's."""
    assert erasure.FORBID_IDS_SHA256 == arm_record["config"]["forbid_ids_sha256"]
    assert erasure.FORBID_IDS_SHA256.startswith("79b55770f4dcfa94")

    for missing in erasure.ARM_CONFIG_KEYS:
        broken = _erasure_arm()
        broken["config"] = {k: v for k, v in broken["config"].items() if k != missing}
        with pytest.raises(SystemExit, match="config"):
            erasure._arm_record(**broken)

    drifted = _erasure_arm()
    drifted["config"] = {**drifted["config"], "forbid_ids_sha256": "f" * 64}
    with pytest.raises(SystemExit, match="forbid|mask"):
        erasure._arm_record(**drifted)

    # Provenance columns are ALLOWED on top — Phase 18's own config carries a dozen of them, and a
    # hard equality here would forbid recording the device, the pid and the git sha.
    extra = _erasure_arm()
    extra["config"] = {**extra["config"], "git_sha": "deadbeef", "device": "mps"}
    assert erasure._arm_record(**extra)["config"]["git_sha"] == "deadbeef"


def test_zero_results_have_nll_names_the_offending_fact_and_returns_a_real_bool():
    """The flag is a genuine `bool`, and the gaps are named separately — the trap is the tuple.

    A `(False, "reason")` return would be TRUTHY, so `not zero_results_have_nll` in the gate
    (`erasure_gate.py:223`) would evaluate False and the INCONCLUSIVE branch would be silently
    disarmed for exactly the run that needed it. The reason therefore lives in a second, named
    function and the flag stays a bool.
    """
    assert bool((False, "reason")) is True  # the trap, recorded rather than argued

    complete = _erasure_arm(zero_slots=(erasure.TARGET_SLOT,))
    assert erasure.zero_results_have_nll(complete) is True
    assert type(erasure.zero_results_have_nll(complete)) is bool
    assert erasure.zero_result_exposure_gaps(complete) == ()

    # A zero-success fact whose slot has NO exposure record: False, with the fact NAMED.
    missing = _erasure_arm(
        zero_slots=(erasure.TARGET_SLOT,),
        exposure=[
            _exposure_record(s) for s in erasure.CORE_GATED_SLOTS if s != erasure.TARGET_SLOT
        ],
    )
    assert erasure.zero_results_have_nll(missing) is False
    gaps = erasure.zero_result_exposure_gaps(missing)
    assert f"synthetic_{erasure.TARGET_SLOT}" in " ".join(gaps)
    # TWO independent gaps, both true and both reported: the eight-slot requirement and the named
    # zero-success fact. Only the post-erasure block was broken here, so the pre-erasure block —
    # which is checked by the same loop — contributes none.
    assert len(gaps) == 2, gaps
    assert [g for g in gaps if g.startswith("the post-erasure")] and not [
        g for g in gaps if "pre-erasure" in g
    ]

    # A fact that scored is not required to carry one — the clause is about zeros, and requiring
    # exposure everywhere would make the flag stop discriminating.
    assert erasure.zero_results_have_nll(_erasure_arm()) is True


def test_zero_results_have_nll_requires_exposure_for_all_eight_slots_and_six_finite_nlls():
    """Phase 18's bar: 48 finite NLLs per arm (`18-VERIFICATION.md:60`) — 8 slots x 6 each."""
    extraction = _extraction()
    six = len(extraction.NLL_FRAMES) * len(extraction.NLL_REDUCTIONS)
    assert six == 6

    # ALL EIGHT slots carry exposure, so the target's movement off rank 1 is read against seven
    # that did not move. A record short one slot fails even when that slot scored.
    short = _erasure_arm(
        zero_slots=(erasure.TARGET_SLOT,),
        exposure=[_exposure_record(s) for s in erasure.CORE_GATED_SLOTS[:-1]],
    )
    assert erasure.zero_results_have_nll(short) is False
    assert any(
        "eight" in gap or erasure.CORE_GATED_SLOTS[-1] in gap
        for gap in erasure.zero_result_exposure_gaps(short)
    )

    # A MISSING FRAME — five NLLs where six are required.
    partial = _erasure_arm(
        zero_slots=(erasure.TARGET_SLOT,),
        exposure=[
            _exposure_record(s, drop_frame=extraction.HELD_OUT_NLL_FRAME)
            for s in erasure.CORE_GATED_SLOTS
        ],
    )
    assert erasure.zero_results_have_nll(partial) is False
    assert extraction.HELD_OUT_NLL_FRAME in " ".join(erasure.zero_result_exposure_gaps(partial))

    # A NON-FINITE value: `None`, NaN and inf each disqualify. A null NLL beside a zero recall is
    # precisely "we did not measure whether the probe was weak".
    for bad in (None, float("nan"), float("inf")):
        broken = _erasure_arm(
            zero_slots=(erasure.TARGET_SLOT,),
            exposure=[_exposure_record(s, value=bad) for s in erasure.CORE_GATED_SLOTS],
        )
        assert erasure.zero_results_have_nll(broken) is False, bad

    # The PRE-erasure exposure block is held to the same bar, so the movement is a paired delta.
    unpaired = _erasure_arm(
        zero_slots=(erasure.TARGET_SLOT,),
        pre_exposure=[
            _exposure_record(s) for s in erasure.CORE_GATED_SLOTS if s != erasure.TARGET_SLOT
        ],
    )
    assert erasure.zero_results_have_nll(unpaired) is False
    assert "pre-erasure" in " ".join(erasure.zero_result_exposure_gaps(unpaired)).lower()


def test_zero_results_have_nll_records_the_q75_masking_concern_as_a_measured_column():
    """Q7.5: the mask makes the attacker STRONGER — measured and published, not assumed."""
    doc = erasure.zero_results_have_nll.__doc__
    lowered = doc.lower()

    # The same pass and the same gate state as the draws — Phase 18 does this inside the
    # generation context manager (`phase18_extraction.py:3696-3702`).
    assert "same pass" in lowered
    assert "3696" in doc

    # The residual concern is stated as a residual and answered by the SAME instrument.
    assert "7,645" in doc or "7645" in doc
    assert "547" in doc
    assert "stronger" in lowered
    assert "rank" in lowered and "nll" in lowered
    assert "decoding artifact" in lowered or "decoding-artifact" in lowered


# =============================================================================================
# ===== PLAN 19-05 / TASK 1 — THE DESCRIPTIVE READ MAY NOT BECOME A GATE; ONE VERDICT PATH ====
# =============================================================================================
#
# `scripts/erasure_gate.py:118-122` makes representational consistency DESCRIPTIVE and EXPLICITLY
# NOT GATED, and `ROADMAP.md:530-534` treats a plan that converts one of these into pass/fail as a
# violation of the pre-registration. This project enforces that STRUCTURALLY rather than by
# convention: `tests/test_phase16_stats.py:798-823` landed its sweep guard BEFORE the code it
# constrains, and Phase 17's D-21 scan catches a second `sign_test_exact` call site as a second
# hypothesis family. The two scans below are Phase 19's, in the same commit as the read they guard.
#
# Both are written as PURE FUNCTIONS OVER A SOURCE STRING and then driven twice — once on the real
# pin (must be clean) and once on a synthetic mutant (must be dirty). A structural guard nobody has
# watched fail is a guard nobody has verified (`STATE.md`, 15-03), and driving the mutant here makes
# that verification a committed property instead of a claim in a summary.

_ORDERING_OPS = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)

# The three ways a number becomes a verdict in this repository. `wilson_upper_bound` is on the list
# with the two inferential calls because it is the estimator condition (a) is gated through
# (`erasure_gate.py:229-230`) — a representational read that computed one would be manufacturing the
# bound half of a pass/fail even without writing the comparison down.
_ERASURE_GATED_CALLEES = ("sign_test_exact", "holm", "wilson_upper_bound")


def _callee_name(call):
    return getattr(call.func, "id", None) or getattr(call.func, "attr", None)


def _module_functions(source=_PIN_SOURCE):
    """``name -> FunctionDef`` for every function defined at MODULE scope."""
    return {node.name: node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}


def _call_sites(callee, source=_PIN_SOURCE):
    """``(enclosing module-level function name, Call)`` for every call to ``callee``.

    A call that escaped every function body is reported under ``None`` rather than dropped: the pin
    runs proofs at module scope, and a verdict call hiding among them is exactly the second path
    this scan exists to refuse.
    """
    tree = ast.parse(source)
    sites, seen = [], set()
    for function in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
        for node in ast.walk(function):
            if isinstance(node, ast.Call) and _callee_name(node) == callee:
                sites.append((function.name, node))
                seen.add(id(node))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _callee_name(node) == callee and id(node) not in seen:
            sites.append((None, node))
    return sites


def _pin_numeric_names():
    """Every module-level name in the pin bound to a NUMBER — assigned here or imported.

    Derived from the live module rather than from assignment targets, so an imported threshold
    (`MARGIN_K`, the three v2.0 baselines) is covered by the same set as a locally assigned one.
    """
    return {
        name
        for name, value in vars(erasure).items()
        if not name.startswith("__")
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    }


def _gating_offenders(source, names):
    """Every way a function in ``names`` reaches for a pass/fail. Empty means descriptive."""
    functions = _module_functions(source)
    thresholds = _pin_numeric_names()
    offenders = []
    for name in names:
        node = functions.get(name)
        if node is None:
            offenders.append(f"{name}: not defined at module scope")
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call) and _callee_name(inner) in _ERASURE_GATED_CALLEES:
                offenders.append(f"{name}: calls {_callee_name(inner)}")
            if isinstance(inner, ast.Compare):
                ordering = [type(op).__name__ for op in inner.ops if isinstance(op, _ORDERING_OPS)]
                if ordering:
                    offenders.append(f"{name}: ordering comparison {ordering}")
            if isinstance(inner, ast.Name) and inner.id in thresholds:
                offenders.append(f"{name}: reads the module-level number {inner.id}")
    return offenders


def test_representational_read_is_not_gated():
    """T-19-18 — the read NAMES what it scanned, so a rename cannot silently escape the scan."""
    names = erasure.DESCRIPTIVE_ONLY_FUNCTIONS
    assert names, "DESCRIPTIVE_ONLY_FUNCTIONS is empty — a scan over nothing is green and blind"

    # A DANGLING entry must FAIL rather than quietly excuse a missing scan target — the discipline
    # `tests/test_phase14_scoring.py:576-582` already uses for `DRAW_ALL_ASSERTED_BY`.
    functions = _module_functions()
    for name in names:
        assert name in functions, (
            f"DESCRIPTIVE_ONLY_FUNCTIONS names {name!r}, which is not a function defined in the "
            "pin. A dangling entry excuses a missing scan target instead of failing on it, and a "
            "renamed function would then escape the scan while the tuple still looked complete"
        )
        assert callable(getattr(erasure, name, None)), f"{name} is not callable on the module"

    assert _gating_offenders(_PIN_SOURCE, names) == [], (
        "a function on the representational path reaches for a pass/fail. "
        "`scripts/erasure_gate.py:118-122` makes this read DESCRIPTIVE and EXPLICITLY NOT GATED: "
        "at n=8 facts and n=3 personas the sample cannot support a threshold, and gating what the "
        "sample cannot support is treated as a DEFECT in this project, not as extra rigour"
    )

    # NON-VACUITY, driven rather than asserted. The mutant is the plan's own prescribed RED.
    mutant = (
        "def delta_w_cosine(cells_a, cells_b):\n"
        "    out = {}\n"
        "    for key in cells_a:\n"
        "        cosine = 0.0\n"
        "        if cosine > 0.5:\n"
        "            out[key] = cosine\n"
        "    return out\n"
    )
    assert _gating_offenders(mutant, ("delta_w_cosine",)), (
        "the scan cannot see a bare threshold comparison — it would be green against the exact "
        "mutation it exists to catch"
    )
    inferential = (
        "def fisher_overlap(fisher_cells, ablated_addresses):\n"
        "    return sign_test_exact(tuple(fisher_cells))\n"
    )
    assert _gating_offenders(inferential, ("fisher_overlap",)), (
        "the scan cannot see a second inferential call site — a second `sign_test_exact` IS a "
        "second hypothesis family and would reprice Holm to carry a descriptive statistic"
    )
    assert _gating_offenders("x = 1\n", ("delta_w_cells",)), (
        "a MISSING scan target reads as clean — a renamed function would escape the scan"
    )


def _verdict_offenders(source):
    """Every way the pin could hold a SECOND verdict. Empty means exactly one path exists."""
    import erasure_gate

    tree = ast.parse(source)
    offenders = []

    imported = {
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    if ("erasure_gate", "erasure_succeeded") not in imported:
        offenders.append("erasure_succeeded is not imported from erasure_gate")
    if "erasure_succeeded" in {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }:
        offenders.append("erasure_succeeded is DEFINED here — the committed rule was re-written")

    sites = [holder for holder, _call in _call_sites("erasure_succeeded", source)]
    if len(sites) > 1:
        offenders.append(f"erasure_succeeded is called {len(sites)} times: {sites}")

    # The four v2.0 baselines the gate's own (a)/(c) arithmetic reads. Any of them retyped as a
    # numeric literal here is a second copy of a number the gate owns, free to stop agreeing.
    for name in (
        "V20_MASKED_DIALOGUE_VAL_PPL",
        "V20_EWC_RETENTION_PPL",
        "V20_RETENTION_NOISE_FLOOR",
        "MARGIN_K",
    ):
        value = getattr(erasure_gate, name)
        hits = [
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
            and node.value == value
        ]
        if hits:
            offenders.append(f"{name} ({value!r}) is typed as a literal at lines {hits}")
    return offenders


def test_verdict_is_called_never_reimplemented():
    """T-19-19 / STAT-05 — one verdict path, importing the committed rule instead of retyping it."""
    import erasure_gate

    assert erasure.erasure_succeeded is erasure_gate.erasure_succeeded, (
        "the pin's `erasure_succeeded` is not the object `scripts/erasure_gate.py` committed at "
        "`23a830c` — a value-matching copy is a copy free to stop matching"
    )
    assert _verdict_offenders(_PIN_SOURCE) == [], (
        "the pin holds a second way to reach an (a)/(b)/(c) verdict. The whole phase is worthless "
        "if a second evaluation exists anywhere to disagree with the committed one"
    )

    # It is CALLED — exactly once — and the caller is named, so the single path is a located path.
    sites = [holder for holder, _call in _call_sites("erasure_succeeded")]
    assert sites == ["render_verdict"], (
        f"erasure_succeeded is called from {sites}, not from exactly `render_verdict`. A rule that "
        "is imported and never called is a rule the report is free to paraphrase instead"
    )

    # NON-VACUITY: the same scan on a mutant with a second call site, and on one that retypes a
    # baseline the gate owns.
    doubled = (
        "from erasure_gate import erasure_succeeded\n"
        "def render_verdict(**kw):\n"
        "    return erasure_succeeded(**kw)\n"
        "def second_opinion(**kw):\n"
        "    return erasure_succeeded(**kw)\n"
    )
    assert _verdict_offenders(doubled), "a second erasure_succeeded call site reads as clean"
    retyped = (
        "from erasure_gate import erasure_succeeded\n"
        "def render_verdict(ppl):\n"
        "    return erasure_succeeded, 4.5733 + 2 * ppl\n"
    )
    assert _verdict_offenders(retyped), "a retyped v2.0 baseline reads as clean"


def _fisher_cell_fixture():
    """A per-cell Fisher dict in `extract_deltas.fisher_cells`' exact shape (:199), 36 entries."""
    return {
        (layer, projection): 1.0 + layer + len(projection) / 10.0
        for layer, projection, _key in extract_deltas.KEYS
    }


def test_delta_w_cells_carries_the_committed_magnitude_read_and_its_own_direction():
    """The ratio is DELEGATED to `extract_deltas.adapter_cells`; the direction is cross-checked.

    `adapter_cells` returns a per-cell Frobenius-norm RATIO — a scalar — so a cosine cannot be
    taken over its output at all. The direction is therefore built here from the SAME identity the
    pin already committed (`MECHANISM_RULE`: ``dW = scale * (B @ A)``), and the two are tied
    together by this test: ``||delta||_F / ||W0||_F`` must equal the ratio `adapter_cells` returned
    for that cell, so the duplication cannot drift into two different deltas.
    """
    base, adapted, lora_cfg = _build_pair()
    artifact = _artifact(adapted, lora_cfg)
    w0_state = base.state_dict()

    cells = erasure.delta_w_cells(artifact, w0_state)
    assert set(cells) == {(layer, projection) for layer, projection, _k in extract_deltas.KEYS}

    scale = lora_cfg.alpha / lora_cfg.r  # alpha/r READ FROM THE ARTIFACT (extract_deltas.py:295)
    ratios = extract_deltas.adapter_cells(artifact["adapter"], scale, w0_state)
    for layer, projection, key in extract_deltas.KEYS:
        cell = cells[(layer, projection)]
        assert cell["ratio"] == ratios[(layer, projection)], (
            "the magnitude read is not the committed one — it must be delegated, never recomputed"
        )
        assert cell["delta"].dtype == torch.float64, "the statistics domain is fp64"
        rebuilt = float(
            torch.linalg.norm(cell["delta"]) / torch.linalg.norm(w0_state[key].to(torch.float64))
        )
        assert rebuilt == pytest.approx(cell["ratio"], rel=1e-12, abs=0.0), (
            f"cell {(layer, projection)}: the direction and the ratio came from DIFFERENT deltas "
            f"({rebuilt} vs {cell['ratio']}) — the cosine would then describe a delta whose "
            "magnitude the report publishes from somewhere else"
        )

    # Non-vacuity: an un-nudged adapter has lora_B == 0 (the identity gate, layer.py:30), so every
    # assertion above would also hold against a function that returned zeros.
    assert any(cell["ratio"] != 0.0 for cell in cells.values()), (
        "every delta is zero — the fixture is measuring the LoRA identity gate, not the operator"
    )


def test_delta_w_cosine_is_per_cell_and_never_calls_a_zero_delta_orthogonal():
    """A dict keyed by ``(layer, projection)``, never a scalar; an ablated cell is None, not 0.0."""
    base, adapted, lora_cfg = _build_pair()
    artifact = _artifact(adapted, lora_cfg)
    w0_state = base.state_dict()
    cells = erasure.delta_w_cells(artifact, w0_state)

    same = erasure.delta_w_cosine(cells, cells)
    assert set(same) == set(cells), "the read returns one entry per cell, never a pooled summary"
    for key, cosine in same.items():
        assert cosine == pytest.approx(1.0, abs=1e-12), f"{key} is not aligned with itself"

    # A FULLY ablated adapter has dW == 0 in every cell, so its direction is UNDEFINED. Reporting
    # 0.0 there would read as "orthogonal", which is a claim the arithmetic does not make.
    erased = erasure.ablate_components(artifact, erasure.component_index())
    zeroed = erasure.delta_w_cells(erased, w0_state)
    undefined = erasure.delta_w_cosine(cells, zeroed)
    assert set(undefined) == set(cells)
    assert all(value is None for value in undefined.values()), (
        "a zero delta was assigned a cosine — `None` and `0.0` are different findings, exactly as "
        "`_verdict.recorded_verdict` distinguishes no-section from an empty body"
    )

    with pytest.raises(SystemExit):
        erasure.delta_w_cosine(cells, {key: cells[key] for key in list(cells)[:5]})


def test_fisher_overlap_partitions_by_cell_and_publishes_both_denominators():
    """Mass in the ablated addresses AGAINST mass in the rest — both sides, both denominators."""
    fisher = _fisher_cell_fixture()
    ablated = [(0, "q_proj", 0), (0, "q_proj", 3), (2, "fc_in", 7)]

    overlap = erasure.fisher_overlap(fisher, ablated)
    assert overlap["ablated_cells"] == ((0, "q_proj"), (2, "fc_in"))
    assert overlap["n_ablated_cells"] == 2
    assert overlap["n_preserved_cells"] == len(extract_deltas.KEYS) - 2
    assert overlap["ablated_mean"] == pytest.approx(
        (fisher[(0, "q_proj")] + fisher[(2, "fc_in")]) / 2
    )
    preserved = [v for k, v in fisher.items() if k not in {(0, "q_proj"), (2, "fc_in")}]
    assert overlap["preserved_mean"] == pytest.approx(sum(preserved) / len(preserved))
    assert overlap["reduction"] == extract_deltas.FISHER_AGGREGATE

    # It carries its own label and its own limitation, so neither can be lost between here and a
    # caption: the Fisher cache has no rank-1 resolution, so this read is CELL-granular.
    assert "DESCRIPTIVE" in overlap["label"]
    assert "cell" in overlap["granularity"].lower()

    # Both degenerate partitions RAISE rather than returning a number over an empty denominator.
    with pytest.raises(SystemExit):
        erasure.fisher_overlap(fisher, [])
    with pytest.raises(SystemExit):
        erasure.fisher_overlap(fisher, erasure.component_index())
    with pytest.raises(SystemExit):
        erasure.fisher_overlap(fisher, [(0, "q_proj", 0), (99, "q_proj", 0)])


# =============================================================================================
# ===== PLAN 19-05 / TASK 2 — THE PHASE 18 PARITY ASSERTIONS (Q7.8 / T-19-20) =================
# =============================================================================================
#
# If the post-erasure run uses a different corpus, mask, `stop_ids`, K, temperature or seed stride,
# the comparison against Phase 18's committed 92/104 is void. Phase 18 evidences its own pairing by
# DIGEST and by two distinct pids rather than by assertion
# (`results/phase18_extraction_report.md:260-265`); Phase 19 records the same, and asserts it too.


def _phase18_record():
    path = _ROOT / "results" / "phase18_arm_adapter-on.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_parity_keys_cover_the_eight_and_every_arm_must_RECORD_them():
    """`PARITY_KEYS` is ordered, and no Phase 19 arm may omit a comparability column."""
    assert erasure.PARITY_KEYS == (
        "corpus_sha256",
        "forbid_ids_sha256",
        "k",
        "asr_rungs",
        "stop_ids",
        "sample_temperature",
        "sample_top_p",
        "seed_stride",
    )
    missing = [key for key in erasure.PARITY_KEYS if key not in erasure.ARM_CONFIG_KEYS]
    assert missing == [], (
        f"the arm-record schema does not require {missing}. Phase 18 ASSERTED none of its "
        "comparability parameters and RECORDED only four of the eight, which is precisely why the "
        "other four had to be reconstructed here from their owning modules — a Phase 19 arm must "
        "carry all eight in its own config so a reader can see which one it ran under"
    )


def test_assert_phase18_parity_passes_on_phase18s_own_committed_parameters():
    """The plan's `<done>`, corrected by measurement: Phase 18 RECORDS four of the eight keys."""
    record = _phase18_record()
    committed = record["config"]

    # MEASURED, not assumed. Four of the eight parity keys are absent from Phase 18's own config.
    recorded = [key for key in erasure.PARITY_KEYS if key in committed]
    absent = [key for key in erasure.PARITY_KEYS if key not in committed]
    assert recorded == ["corpus_sha256", "forbid_ids_sha256", "k", "seed_stride"]
    assert absent == ["asr_rungs", "stop_ids", "sample_temperature", "sample_top_p"]

    # So the committed config ALONE raises — an absent key must not read as agreement.
    with pytest.raises(SystemExit) as absent_exit:
        erasure.assert_phase18_parity(committed)
    assert "asr_rungs" in str(absent_exit.value)

    # Completed with the four Phase 18 INHERITED BY CALL, it passes.
    parity = erasure.phase18_parity_config(record)
    assert tuple(parity) == erasure.PARITY_KEYS
    assert erasure.assert_phase18_parity(parity) == parity

    # NON-VACUITY on the four Phase 18 really did record: they are read OUT OF THE FILE, so a
    # record that ran at a different budget cannot be completed into a passing config.
    drifted = json.loads(json.dumps(record))
    drifted["config"]["k"] = 47
    with pytest.raises(SystemExit) as drift_exit:
        erasure.assert_phase18_parity(erasure.phase18_parity_config(drifted))
    assert "k" in str(drift_exit.value)


def test_every_parity_key_individually_mutated_or_dropped_raises_naming_itself():
    """Eight keys, sixteen refusals — and each names the key it refused, never just 'mismatch'."""
    base = erasure.phase18_parity_config(_phase18_record())
    sentinel = {
        "corpus_sha256": "0" * 64,
        "forbid_ids_sha256": "f" * 64,
        "k": 47,
        "asr_rungs": (1, 4, 16, 47),
        "stop_ids": frozenset({8184}),
        "sample_temperature": 0.7,
        "sample_top_p": 0.9,
        "seed_stride": "unstrided",
    }
    for key in erasure.PARITY_KEYS:
        mutated = dict(base)
        mutated[key] = sentinel[key]
        with pytest.raises(SystemExit) as mutated_exit:
            erasure.assert_phase18_parity(mutated)
        assert key in str(mutated_exit.value), f"a mutated {key} raised without naming itself"

        dropped = {name: value for name, value in base.items() if name != key}
        with pytest.raises(SystemExit) as dropped_exit:
            erasure.assert_phase18_parity(dropped)
        assert key in str(dropped_exit.value), f"a dropped {key} raised without naming itself"

    # A JSON round trip turns the tuple and the frozenset into lists. That must still PASS — the
    # config this is asserted against is read back out of an artifact, not held in memory.
    assert erasure.assert_phase18_parity(json.loads(json.dumps(base, default=sorted)))


def test_parity_recomputes_the_corpus_digest_and_never_pastes_it():
    """Q7.8 — the Phase 19 target arms REUSE `results/phase18_corpus.json` verbatim."""
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")
    corpus = json.loads((_ROOT / "results" / "phase18_corpus.json").read_text(encoding="utf-8"))
    expected = erasure.phase18_parity_values()

    assert expected["corpus_sha256"] == extraction.corpus_sha256(corpus)
    assert expected["corpus_sha256"] == _phase18_record()["config"]["corpus_sha256"]
    assert expected["corpus_sha256"] not in _PIN_SOURCE, (
        "the corpus digest is pasted into the pin as a hex string — it must be RECOMPUTED through "
        "the committed `canonical_json` + `corpus_sha256` pair, so a corpus that changed under it "
        "goes red instead of matching a literal nobody re-derived"
    )

    # Every other expected value is the OWNING module's object, not a copy that matches today.
    recall = _load("phase14_recall", "scripts/phase14_recall.py")
    assert expected["k"] == extraction.K
    assert expected["asr_rungs"] == extraction.ASR_RUNGS
    assert expected["stop_ids"] == recall.STOP_IDS
    assert expected["sample_temperature"] == recall.SAMPLE_TEMPERATURE
    assert expected["sample_top_p"] == recall.SAMPLE_TOP_P
    assert expected["forbid_ids_sha256"] == erasure.FORBID_IDS_SHA256


def test_phase18_parity_reconstructs_four_inherited_parameters_and_a_census_proves_it():
    """The reconstruction is only honest if Phase 18 really ran under these — measured by AST.

    Phase 18 records no sampling column because it never chooses one: it reaches the sampler through
    `phase14_recall.draw_all` / `complete_question`, which read `SAMPLE_TEMPERATURE`, `SAMPLE_TOP_P`
    and `STOP_IDS` as module constants. So the claim to verify is that NO Phase 18 call site
    overrides them — an override would make the reconstructed value a fiction.
    """
    src = (_ROOT / "scripts" / "phase18_extraction.py").read_text(encoding="utf-8")
    sites = [
        (node.lineno, sorted(kw.arg for kw in node.keywords))
        for node in ast.walk(ast.parse(src))
        if isinstance(node, ast.Call)
        and getattr(node.func, "attr", None) in ("draw_all", "complete_question")
    ]
    assert sites, "no sampler call site found in phase18_extraction.py — the census is blind"
    for lineno, keywords in sites:
        overrides = [
            kw
            for kw in keywords
            if kw in ("temperature", "top_p", "stop_ids", "sample_temperature")
        ]
        assert overrides == [], (
            f"phase18_extraction.py:{lineno} overrides {overrides} at a sampler call site, so the "
            "reconstructed sampling parameters are not the ones Phase 18 ran under"
        )

    # And the constants really are read INSIDE the sampler, not passed down from somewhere else.
    recall_src = (_ROOT / "scripts" / "phase14_recall.py").read_text(encoding="utf-8")
    readers = {
        node.name: sorted(
            {
                inner.id
                for inner in ast.walk(node)
                if isinstance(inner, ast.Name)
                and inner.id in ("SAMPLE_TEMPERATURE", "SAMPLE_TOP_P", "STOP_IDS")
            }
        )
        for node in ast.parse(recall_src).body
        if isinstance(node, ast.FunctionDef)
    }
    assert readers["draw_all"] == ["SAMPLE_TEMPERATURE", "SAMPLE_TOP_P"]
    assert readers["_complete"] == ["STOP_IDS"]

    # The pin records the gap rather than papering over it.
    assert erasure.PHASE18_RECORDED_PARITY_KEYS == (
        "corpus_sha256",
        "forbid_ids_sha256",
        "k",
        "seed_stride",
    )
    assert erasure.PHASE18_INHERITED_PARITY_KEYS == (
        "asr_rungs",
        "stop_ids",
        "sample_temperature",
        "sample_top_p",
    )
    doc = erasure.phase18_parity_config.__doc__
    assert "inherit" in doc.lower() and "260-265" in doc
    # The deliberately OFFSET replicate stride must not be asserted against Phase 18's.
    assert "replicate" in erasure.assert_phase18_parity.__doc__.lower()


# =============================================================================================
# ===== PLAN 19-05 / TASK 3 — THE REPORT TEXT AND THE SHIP-DECISION MARKER PAIR ===============
# =============================================================================================


def _gate_inputs(**overrides):
    """The nine keyword-only arguments of the committed rule, in a shape that clears (a)/(b)/(c)."""
    inputs = {
        "target_successes": 0,
        "target_questions": erasure.N_TARGET_QUESTIONS,
        "target_floor": erasure.lock_erasure_floor(0.4143),
        "nontarget_deltas": (0.01, 0.02, 0.0, 0.03, 0.01, 0.0, 0.04),
        "nontarget_noise_floor": 0.04,
        "dialogue_ppl": 4.60,
        "dialogue_ppl_noise_floor": 0.05,
        "retention_ppl": 3.95,
        "zero_results_have_nll": True,
    }
    inputs.update(overrides)
    return inputs


def _report_kwargs(**overrides):
    slots = erasure.GATED_NONTARGET_SLOTS
    kwargs = {
        "verdict": erasure.render_verdict(**_gate_inputs()),
        "target": {
            "n_draws": erasure.N_TARGET_QUESTIONS * 48,
            "pre_successes": 27,
            "pre_questions": erasure.N_TARGET_QUESTIONS,
            "pre_draws": erasure.N_TARGET_QUESTIONS * 48,
        },
        "cal_rate": 0.4143,
        "nontargets": tuple(
            {
                "slot": slot,
                "pre_successes": 13,
                "pre_questions": 27,
                "pre_draws": 27 * 48,
                "post_successes": 13 - index % 2,
                "post_questions": 27,
                "post_draws": 27 * 48,
            }
            for index, slot in enumerate(slots)
        ),
        "capability": {"dialogue_ppl": 5.8154, "retention_ppl": 3.90},
        "representational": {
            "cosine": {(0, "q_proj"): 0.87, (1, "fc_in"): None},
            "fisher": erasure.fisher_overlap(_fisher_cell_fixture(), [(0, "q_proj", 0)]),
        },
        "provenance": {
            "git_sha": "0" * 40,
            "device": "mps",
            "parity": erasure.phase18_parity_config(_phase18_record()),
        },
    }
    kwargs.update(overrides)
    return kwargs


def test_the_ship_marker_pair_names_phase_19_in_both_halves():
    """T-19-22 — the reason `scripts/_addendum.py` makes BOTH halves required keywords."""
    pending = erasure.ERASURE_SHIP_PENDING_LINE
    recorded = erasure.ERASURE_SHIP_RECORDED_LINE

    assert "Phase 19" in pending and "Phase 19" in recorded
    assert "Phase 18" not in pending and "Phase 18" not in recorded, (
        "a Phase 19 marker half carries a Phase 18 provenance claim — the exact defect "
        "scripts/_addendum.py exists to prevent, where one half travelled with the caller and the "
        "other was hard-coded, so appending to a Phase 19 document wrote a Phase 18 sentence"
    )
    assert pending != recorded
    # The placeholder must be replaceable exactly once, so it may not be a prefix of its partner.
    assert pending not in recorded


def test_render_report_emits_one_verdict_section_one_pending_line_and_no_bare_zero(tmp_path):
    """The six publications, side by side and IN ORDER, with `append_addendum` satisfiable."""
    add = _load("_addendum", "scripts/_addendum.py")
    verdict_module = _load("_verdict", "scripts/_verdict.py")
    path = tmp_path / "phase19_erasure_report.md"

    text = erasure.render_report(path=path, **_report_kwargs())
    assert path.read_text(encoding="utf-8") == text

    assert len(verdict_module.VERDICT_SECTION.findall(text)) == 1
    assert text.count(erasure.ERASURE_SHIP_PENDING_LINE) == 1, (
        "`append_addendum` replaces EXACTLY one placeholder — the renderer must make that "
        "satisfiable by construction rather than by an operator counting lines"
    )
    assert re.search(r"\b0(\.0+)?%", text) is None, "STAT-02 forbids a bare zero percentage"

    body = verdict_module.recorded_verdict(text)
    anchors = [
        "### 1. The verdict",
        "### 2. Condition (a)",
        "### 3. Condition (b)",
        "### 4. Condition (c)",
        "### 5. The (a) floor",
        "### 6. Representational consistency",
    ]
    positions = [body.index(anchor) for anchor in anchors]
    assert positions == sorted(positions), f"the verdict section publishes out of order: {anchors}"

    # (a): the bound, its denominator and rule-of-three(27) beside it.
    assert f"{erasure.N_TARGET_QUESTIONS} questions" in body
    import erasure_gate

    assert f"{erasure_gate.rule_of_three(erasure.N_TARGET_QUESTIONS):.6f}" in body
    # (b): PER FACT, never pooled — all seven gated slots, each with its own denominator.
    for slot in erasure.GATED_NONTARGET_SLOTS:
        assert f"`{slot}`" in body
    # (c): PRE and POST dialogue PPL, the cap, and the noise floor that produced it.
    assert "5.8154" in body and "4.6000" in body
    assert f"{erasure.dialogue_cap(0.05):.6f}" in body
    # (5): BOTH directions and the branch.
    assert f"{erasure.lock_erasure_floor(0.4143):.6f}" in body
    assert f"{erasure.literal_phase14_floor(0.4143)!r}" in body
    assert erasure.floor_branch(0.4143) in body
    # (6): labelled DESCRIPTIVE, and a `None` cosine says undefined rather than orthogonal.
    assert "DESCRIPTIVE" in body
    assert "undefined" in body.lower()

    # `append_addendum` succeeds against the rendered bytes with the Phase 19 pair...
    updated = add.append_addendum(
        path,
        "## Addendum — 2026-08-17 — the decision\n\nPhase 19 ship decision: DO NOT SHIP",
        pending=erasure.ERASURE_SHIP_PENDING_LINE,
        recorded=erasure.ERASURE_SHIP_RECORDED_LINE,
    )
    assert erasure.ERASURE_SHIP_RECORDED_LINE in updated
    # NOT `"Phase 18" not in updated`: the report legitimately CITES Phase 18 (the D8 posture names
    # the register it shipped `LEAKAGE_DEMONSTRATED` in, and the parity table is titled after it).
    # The defect is a Phase 18 SHIP-DECISION LINE arriving as this document's own provenance.
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")
    assert extraction.EXTRACTION_SHIP_RECORDED_LINE not in updated
    assert extraction.EXTRACTION_SHIP_PENDING_LINE not in updated

    # ...and refuses a DOUBLED placeholder, because choosing is how an append becomes a rewrite.
    doubled = tmp_path / "doubled.md"
    doubled.write_text(text + "\n" + erasure.ERASURE_SHIP_PENDING_LINE + "\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        add.append_addendum(
            doubled,
            "## Addendum",
            pending=erasure.ERASURE_SHIP_PENDING_LINE,
            recorded=erasure.ERASURE_SHIP_RECORDED_LINE,
        )


def test_the_clobber_guard_refuses_a_re_render_and_separates_none_from_an_empty_body(tmp_path):
    """T-19-21 / CR-02 — anchored on the SECTION, and there is no `--force`."""
    # Structural, not a substring scan: the pin's own docstring REJECTS `--force` in prose, and a
    # text scan would read the refusal as the defect. What must not exist is a PARAMETER named
    # force and a `--force` branch off sys.argv.
    tree = ast.parse(_PIN_SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = node.args
            names = [a.arg for a in (args.posonlyargs + args.args + args.kwonlyargs)] + [
                a.arg for a in (args.vararg, args.kwarg) if a is not None
            ]
            assert not [name for name in names if "force" in name.lower()], (
                f"{node.name} takes a force argument. An operator who learns one is always "
                "required passes it after a verdict HAS been recorded, at which point the guard "
                "destroys exactly the evidence it exists to protect"
            )
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "--force" not in literals, "the pin reads a --force flag off the command line"

    path = tmp_path / "phase19_erasure_report.md"
    assert erasure.assert_erasure_report_not_clobbered(path) is None, (
        "an absent report has nothing to clobber and must not refuse the first render"
    )

    erasure.render_report(path=path, **_report_kwargs())
    with pytest.raises(SystemExit) as recorded_exit:
        erasure.assert_erasure_report_not_clobbered(path)
    assert "verdict" in str(recorded_exit.value).lower()

    # A re-render is refused THROUGH render_report itself, not as a step to remember.
    with pytest.raises(SystemExit):
        erasure.render_report(path=path, **_report_kwargs())

    # `None` (no section at all) and an EMPTY body are different findings and say so.
    foreign = tmp_path / "foreign.md"
    foreign.write_text("# Somebody else's document\n\nno verdict section here\n", encoding="utf-8")
    with pytest.raises(SystemExit) as foreign_exit:
        erasure.assert_erasure_report_not_clobbered(foreign)

    empty = tmp_path / "empty.md"
    empty.write_text("# Phase 19\n\n## Verdict\n\n## Ship Decision\n", encoding="utf-8")
    with pytest.raises(SystemExit) as empty_exit:
        erasure.assert_erasure_report_not_clobbered(empty)
    assert str(foreign_exit.value) != str(empty_exit.value), (
        "a file this writer did not produce and an INTERRUPTED render abort with the same message "
        "— `_verdict.recorded_verdict` returns None for one and an empty body for the other "
        "precisely so the two stay distinguishable"
    )


def test_the_placeholder_rewrite_is_conditional_on_a_real_ship_decision(tmp_path):
    """Phase 18's W2, closed: the rewrite ran unconditionally and recorded nothing.

    `18-VERIFICATION.md:226-250` — appending the D-21 quantification silently converted "not yet
    recorded" into "recorded in the dated continuation" with no decision ever written, and a grep
    for ship/no-ship language returned only the section heading and the pointer line itself. So a
    substring check for "ship" would ALSO have passed W2; the decision has to be a pinned LINE.
    """
    path = tmp_path / "phase19_erasure_report.md"
    erasure.render_report(path=path, **_report_kwargs())

    # W2 reproduced: a dated continuation that records no decision must NOT flip the marker.
    with pytest.raises(SystemExit) as no_decision:
        erasure.append_ship_decision(
            "## Dated continuation — 2026-08-17: the collateral curve, quantified\n\n"
            "Per-component recall and dialogue PPL at each ablation step.",
            path=path,
        )
    assert "decision" in str(no_decision.value).lower()
    assert erasure.ERASURE_SHIP_PENDING_LINE in path.read_text(encoding="utf-8"), (
        "the placeholder was rewritten by an append that recorded no decision"
    )

    # An UNDATED decision is refused too — the recorded line promises a DATED continuation.
    with pytest.raises(SystemExit) as undated:
        erasure.append_ship_decision(
            f"## Ship decision\n\n{erasure.ERASURE_SHIP_DECISION_PREFIX}DO NOT SHIP", path=path
        )
    assert "date" in str(undated.value).lower()

    # A real decision goes through, and the marker flips exactly once.
    updated = erasure.append_ship_decision(
        "## Dated continuation — 2026-08-17: the ship decision\n\n"
        f"{erasure.ERASURE_SHIP_DECISION_PREFIX}DO NOT SHIP — the adapter is not shippable "
        "substrate for the reasons recorded above.",
        path=path,
    )
    assert updated.count(erasure.ERASURE_SHIP_RECORDED_LINE) == 1
    assert erasure.ERASURE_SHIP_PENDING_LINE not in updated
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")
    assert extraction.EXTRACTION_SHIP_RECORDED_LINE not in updated

    # Both halves of the closed decision set are accepted, and nothing else is.
    assert erasure.ERASURE_SHIP_DECISIONS == ("SHIP", "DO NOT SHIP")


def test_d8_publication_posture_is_pinned_before_the_number_exists():
    """D8 (LOCKED) and Q7.4 — both branches framed here rather than after the number."""
    posture = erasure.D8_PUBLICATION_POSTURE
    text = " ".join(posture) if isinstance(posture, tuple) else posture
    lowered = text.lower()

    assert "selective erasure is not selective at 331,776 parameters" in lowered
    assert "unsoftened" in lowered
    assert "leakage_demonstrated" in lowered.replace("`", "")

    # Q7.4 — the EASY branch is a measurement, not an absence, and its framing is written now.
    assert "trivial" in lowered
    assert "measurement" in lowered
    assert "rank" in lowered

    # It is in the report, not only in the source.
    import tempfile

    path = pathlib.Path(tempfile.mkdtemp()) / "phase19_erasure_report.md"
    rendered = erasure.render_report(path=path, **_report_kwargs())
    assert "not selective at 331,776 parameters" in rendered
