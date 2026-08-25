"""Phase 22 -- the DP-SGD mechanism at run time: D-04's property refusals (V-22).

V-22. D-04's own defect class is *a guarantee stated as a property of the mechanism that is
actually a property of one caller*. So every refusal here is asserted against a REAL
``GPT(ModelConfig())`` with real ``inject_lora`` wrappers, never against a stub: the trap being
refused (``inject_lora`` does not freeze) is only reachable through the real injection path.

**A refusal is only evidence when its positive control is asserted real first.** The unfrozen-base
case asserts the measured 172 trainable tensors / 14,223,360 params BEFORE it asserts the refusal
-- without that, ``pytest.raises(RuntimeError)`` could be satisfied by an unrelated failure and the
test would prove nothing about the trap it names. That is
``tests/test_phase21_replay_volume.py::_assert_fixture_actually_varies``'s discipline, applied to a
refusal instead of to a differential.

**Three refusals sharing one message are one refusal wearing three hats.** Each parametrized case
therefore asserts its OWN ``[dp-refusal:...]`` marker is present AND that the other two cases'
markers are absent -- pairwise distinctness proven per test item, with no state shared across
items.

CPU-only, GPU-free, no network.
"""

import math

import pytest
import torch

from personacore.config import ModelConfig, RuntimeConfig
from personacore.lora.config import LoRAConfig
from personacore.lora.inject import inject_lora, mark_only_lora_trainable
from personacore.model.gpt import GPT
from personacore.privacy.dpsgd import DPSGD

# Test-local fixture values, NOT a budget. Phase 22 names no sigma and no C anywhere in its tree
# (D-08 / Phase 20's Z boundary); these are arithmetic test vectors in exactly the sense plan
# 22-02 draws for GOLDEN_EPSILON's sigma/T columns.
_SIGMA = 1.0
_CLIP = 1.0

# The three D-04 refusal markers. Distinctness is asserted pairwise below.
_MARKERS = ("dp-refusal:unfrozen-base", "dp-refusal:live-scaler", "dp-refusal:census")

# Measured against HEAD with torch 2.7.1: `inject_lora` alone leaves the base trainable.
_UNFROZEN_TENSORS = 172
_UNFROZEN_PARAMS = 14_223_360
_FROZEN_TENSORS = 72
_FROZEN_PARAMS = 331_776


def _model(*, freeze=True):
    """A real GPT + real LoRA on CPU; ``freeze=False`` is D-04 trap 1's positive control."""
    torch.manual_seed(1234)
    model = GPT(ModelConfig())
    inject_lora(model, LoRAConfig())
    if freeze:
        mark_only_lora_trainable(model)
    return model


def _census(model):
    return (
        sum(1 for p in model.parameters() if p.requires_grad),
        sum(p.numel() for p in model.parameters() if p.requires_grad),
    )


def _seam(model, **kwargs):
    kwargs.setdefault("sigma", _SIGMA)
    kwargs.setdefault("clip_norm", _CLIP)
    return DPSGD(model, **kwargs)


# --- V-22: the three D-04 property refusals, each with its positive control ---------------------


def _case_unfrozen_base():
    """``inject_lora`` WITHOUT ``mark_only_lora_trainable`` -- reachable by omitting one line."""
    model = _model(freeze=False)
    tensors, params = _census(model)
    # POSITIVE CONTROL, asserted BEFORE the refusal: the trap is real and this is its measured
    # size. Without this the RuntimeError below could be firing for an unrelated reason.
    assert (tensors, params) == (_UNFROZEN_TENSORS, _UNFROZEN_PARAMS), (
        f"the unfrozen-base fixture is {tensors} tensors / {params} params, not the measured "
        f"{_UNFROZEN_TENSORS} / {_UNFROZEN_PARAMS}. inject_lora is supposed to leave the base "
        "trainable; if it no longer does, this case is asserting a refusal for a trap that is "
        "no longer reachable, and the whole V-22 claim would be vacuous"
    )
    return lambda: _seam(model)


def _case_live_scaler():
    """A live ``GradScaler``: measured, ``.grad`` read mid-accumulation is wrong by the scale."""
    model = _model()
    scaler = torch.amp.GradScaler(device="cpu", enabled=True)
    # POSITIVE CONTROL: the scaler really is enabled, so the refusal is not firing on a
    # constructed-but-inert object.
    assert scaler.is_enabled(), "the fixture scaler is disabled — this case would prove nothing"
    return lambda: _seam(model, scaler=scaler)


def _case_census_mismatch():
    """One LoRA parameter frozen: every name still matches ``lora_``, only the COUNT moves.

    This is what proves refusal 3 is not subsumed by refusal 1 -- the ``requires_grad`` audit sees
    nothing wrong here, because no non-``lora_`` parameter is trainable.
    """
    model = _model()
    victim = next(p for name, p in model.named_parameters() if "lora_A" in name)
    victim.requires_grad_(False)
    tensors, params = _census(model)
    # POSITIVE CONTROL: the count moved by exactly one lora_A tensor and the requires_grad audit
    # is still silent, so the refusal that fires can only be the census one.
    assert (tensors, params) == (_FROZEN_TENSORS - 1, _FROZEN_PARAMS - victim.numel())
    assert not [n for n, p in model.named_parameters() if p.requires_grad and "lora_" not in n]
    return lambda: _seam(model)


@pytest.mark.parametrize(
    ("build", "marker"),
    [
        (_case_unfrozen_base, "dp-refusal:unfrozen-base"),
        (_case_live_scaler, "dp-refusal:live-scaler"),
        (_case_census_mismatch, "dp-refusal:census"),
    ],
)
def test_seam_refuses(build, marker):
    """V-22: each D-04 property is refused at the seam, with a message only IT carries."""
    construct = build()
    with pytest.raises(RuntimeError) as excinfo:
        construct()
    message = str(excinfo.value)
    assert marker in message, f"the refusal did not carry its own marker {marker!r}: {message}"
    others = sorted(set(_MARKERS) - {marker})
    assert not [m for m in others if m in message], (
        f"the {marker!r} refusal also carries {others} — three refusals sharing one message are "
        "one refusal wearing three hats, and a shared message makes the other two cases' "
        "pytest.raises assertions satisfiable by the wrong refusal"
    )


def test_seam_refuses_a_live_runtime_amp():
    """The OTHER half of D-04 refusal 2: AMP declared live on the config rather than on a scaler.

    ``RuntimeConfig.__post_init__`` forces ``amp=False`` on cpu and mps, so this branch is
    unreachable on the primary path -- which is exactly why it needs a test: an untested refusal on
    the P100 fallback is a refusal nobody has watched, and the failure it prevents is a SILENT
    wrong clip rather than a crash.
    """
    runtime = RuntimeConfig(device="cuda", amp=True)
    # POSITIVE CONTROL: __post_init__ did not silently disable amp for this device, so the refusal
    # below is firing on a live flag and not on a flag the config already cleared.
    assert runtime.amp is True
    with pytest.raises(RuntimeError, match="dp-refusal:live-scaler"):
        _seam(_model(), runtime=runtime)


# --- Refusal 4: clip_norm must be FINITE, and the crash it prevents is recorded ------------------


def test_inf_clip_norm_really_would_crash_the_noise_draw():
    """The positive control for refusal 4: the measured ``0.0 * inf -> nan -> RuntimeError`` chain.

    A refusal recorded without the failure it prevents is a claim. This asserts the failure.
    """
    product = 0.0 * math.inf
    assert product != product, (
        f"0.0 * math.inf is {product!r}, not nan — the measurement refusal 4 rests on no longer "
        "holds, and an infinite clip_norm may now be representable after all"
    )
    with pytest.raises(RuntimeError, match="std"):
        torch.normal(mean=0.0, std=0.0 * math.inf, size=(3,))


@pytest.mark.parametrize("bad", [math.inf, float("nan")])
def test_clip_norm_must_be_finite(bad):
    """``math.inf`` is REFUSED, not legal -- and the message names the measured ``nan`` std."""
    model = _model()
    with pytest.raises(ValueError) as excinfo:
        _seam(model, clip_norm=bad)
    message = str(excinfo.value)
    assert "dp-refusal:clip-domain" in message
    assert "std nan" in message, (
        "the clip_norm refusal does not name the measured torch.normal nan-std crash, so a future "
        f"reader has no recorded reason not to re-widen the domain: {message}"
    )
    # The NEGATIVE side. A refusal that rejected every LARGE bound would break D-06's identity
    # input instead of fixing it: C = infinity is represented as a finite bound proven not to bind.
    big = _seam(model, clip_norm=1e30)
    assert big.C == 1e30
    assert big._clip_bind_count == 0


# --- The correct configuration constructs, and its generator is genuinely its own ---------------


def test_seam_constructs_cleanly():
    """The 72-tensor / 331,776-param config constructs, and ``_g`` is not the global stream."""
    model = _model()
    assert _census(model) == (_FROZEN_TENSORS, _FROZEN_PARAMS)
    dp = _seam(model, seed=7)

    assert dp.sigma == _SIGMA
    assert dp.C == _CLIP
    assert len(dp._params) == _FROZEN_TENSORS
    assert sum(p.numel() for p in dp._params) == _FROZEN_PARAMS

    # D-07, asserted structurally rather than argued: drawing from the DEDICATED generator leaves
    # the global torch stream byte-identical. That independence must not rest on
    # ModelConfig.dropout = 0.0 / LoRAConfig.dropout = 0.0, neither of which is pinned.
    before = torch.get_rng_state().clone()
    drawn = torch.normal(mean=0.0, std=1.0, size=(64,), generator=dp._g)
    after = torch.get_rng_state()
    assert torch.equal(before, after), (
        "dp._g draws moved the GLOBAL torch RNG — it is not dedicated"
    )
    assert not torch.equal(drawn, torch.zeros_like(drawn)), (
        "the dedicated generator produced exact zeros at std=1.0 — the draw did not happen, and "
        "the 'global stream untouched' assertion above would then be vacuous"
    )
