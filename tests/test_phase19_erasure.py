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

import dataclasses
import importlib.util
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
