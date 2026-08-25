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


# =============================================================================================
# V-13 -- D-16's FOUR RUNTIME INVARIANTS, each proven to BITE and not merely to pass.
#
# A guard nobody has watched fail is a guard nobody has verified. Every invariant below has a
# test that observes it RAISE on a deliberate break, alongside the test that observes the
# correct path pass.
# =============================================================================================

# A test-local, NON-BINDING clip. NOT a budget (D-08 / Phase 20's Z boundary): this is the
# arithmetic test vector that represents `C = infinity` as a FINITE bound proven not to bind,
# now that math.inf is refused. Measured basis for the choice: at the frozen-base regime the
# private-only grad norm is 0.143608 and private+replay 0.436096, and the hand-set fixture
# gradients below carry a global norm of ~0.58 (331,776 standard normals scaled by 1e-3), so a
# bound seven orders above cannot bind. `_clip_bind_count == 0` is asserted rather than assumed,
# so if a future change ever makes it bind the assertion reddens with a nameable cause instead of
# silently clipping.
_NON_BINDING_CLIP = 1e6
_GRAD_SCALE = 1e-3
_BINDING_CLIP = 1e-3


def _hand_set_grads(dp, seed):
    """Write one record's gradients by hand and return them, so the expected mean is exact."""
    gen = torch.Generator().manual_seed(seed)
    grads = []
    for p in dp._params:
        g = torch.randn(p.shape, generator=gen) * _GRAD_SCALE
        p.grad = g
        grads.append(g)
    return grads


def _absorb(dp, seed):
    grads = _hand_set_grads(dp, seed)
    dp.absorb_record()
    return grads


# --- D-16 invariant 1: the per-micro-step drain --------------------------------------------------


def test_drain_invariant_fires():
    """Two ``absorb_record`` calls for one backward: the second has nothing to absorb."""
    dp = _seam(_model(), sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=3)
    dp.begin_step()
    _absorb(dp, seed=1)
    # POSITIVE CONTROL: the drain really happened, so the refusal below is about the drain and
    # not about a gradient that was never written.
    assert all(p.grad is None for p in dp._params)
    with pytest.raises(RuntimeError, match="dp-invariant:drain"):
        dp.absorb_record()


def test_drain_invariant_fires_when_the_drain_itself_is_dropped():
    """The refactor D-01 names: the drain loop removed, every other guard still green.

    ``_drained`` is cleared before anything is read and set again ONLY by the drain, so a
    mechanism that stops draining refuses the NEXT record rather than silently clipping a running
    sum to ``C`` and letting the true per-record sensitivity become ``N*C``.
    """
    dp = _seam(_model(), sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=3)
    dp.begin_step()
    _absorb(dp, seed=1)
    dp._drained = False  # exactly the state a dropped drain leaves behind
    _hand_set_grads(dp, seed=2)  # a fresh backward's worth of gradients, so .grad is NOT None
    with pytest.raises(RuntimeError, match="N\\*C"):
        dp.absorb_record()


# --- D-16 invariant 2: sensitivity against C * (1 + tol) -----------------------------------------


class _UnderReportingNorm(DPSGD):
    """FAKE: the PRE-clip norm reads 0.0, so ``coef`` never binds while the record is far over C.

    This is what a wrong-sensitivity fake looks like at run time -- the clip is present, reads the
    single ``self.C``, and simply does not bind. Only the RE-COMPUTED post-clip norm can see it,
    which is why invariant 2 measures the clipped tensors instead of trusting ``norm * coef``.
    """

    def _global_norm(self, tensors):
        real = super()._global_norm(tensors)
        self._norm_calls = getattr(self, "_norm_calls", 0) + 1
        return 0.0 if self._norm_calls % 2 == 1 else real


def test_sensitivity_invariant_fires():
    """The clip BINDS on a real over-large record, and the invariant bites when it does not."""
    dp = _seam(_model(), sigma=0.0, clip_norm=_BINDING_CLIP, seed=5)
    dp.begin_step()
    _absorb(dp, seed=1)

    # The POSITIVE property: after one absorbed record the accumulated norm sits ON the bound.
    accumulated = dp._global_norm(dp._accum)
    assert accumulated <= _BINDING_CLIP * (1.0 + dp.sensitivity_tolerance)
    assert accumulated > _BINDING_CLIP * (1.0 - dp.sensitivity_tolerance), (
        f"the accumulated norm is {accumulated!r}, well below C = {_BINDING_CLIP} — the clip did "
        "not bind, so this test is asserting a bound that was never exercised"
    )
    # The counter's OWN positive control. A counter that never increments would make every
    # `_clip_bind_count == 0` assertion elsewhere vacuous.
    assert dp._clip_bind_count > 0

    # And the invariant bites: same fixture, one broken norm away.
    fake = _UnderReportingNorm(_model(), sigma=0.0, clip_norm=_BINDING_CLIP, seed=5)
    fake.begin_step()
    _hand_set_grads(fake, seed=1)
    with pytest.raises(RuntimeError, match="dp-invariant:sensitivity"):
        fake.absorb_record()
    assert fake._clip_bind_count == 0, (
        "the fake's clip bound after all, so the RuntimeError above may be the honest path "
        "refusing rather than the invariant catching a non-binding clip"
    )


# --- D-16 invariant 3: the single-write count, MEASURED -----------------------------------------


def test_single_write_count():
    """Exactly one write per parameter, and no accumulator buffer aliases any ``.grad``."""
    dp = _seam(_model(), sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=7)
    dp.begin_step()
    _absorb(dp, seed=1)
    dp.finalize(1)

    assert dp._writes == len(dp._params)
    buf_ptrs = {buf.data_ptr() for buf in dp._accum}
    grad_ptrs = {p.grad.data_ptr() for p in dp._params}
    assert not (buf_ptrs & grad_ptrs)
    assert len(buf_ptrs) == len(dp._accum), "accumulator buffers alias EACH OTHER"

    # WATCHED RED 1: a write that skips a parameter. The count is a measurement, so it moves.
    dp.begin_step()
    _absorb(dp, seed=2)
    private = dp._noised_private(1)
    with pytest.raises(RuntimeError, match="dp-invariant:single-write"):
        dp._write_once(private[:-1])

    # WATCHED RED 2: a private term that IS the accumulator buffer.
    dp.begin_step()
    _absorb(dp, seed=3)
    with pytest.raises(RuntimeError, match="ALIASES"):
        dp._write_once(list(dp._accum))


def test_the_single_write_combines_rather_than_overwrites():
    """With a PUBLIC term already in ``.grad`` the one write ADDS -- it never replaces it.

    D-01: replay stays in ``.grad`` untouched and ``p.grad += private_accum`` is the SINGLE write
    that combines the two terms. A write that replaced the public term would silently drop the
    replay pass whose whole purpose is to sit outside the per-record loop.
    """
    dp = _seam(_model(), sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=9)
    dp.begin_step()
    records = _absorb(dp, seed=1)
    public = [torch.full_like(p, 0.25) for p in dp._params]
    for p, term in zip(dp._params, public):
        p.grad = term.clone()
    dp.finalize(1)
    for p, rec, pub in zip(dp._params, records, public):
        assert torch.equal(p.grad, pub + rec)


# --- D-16 invariant 4: the generator advances and is never re-seeded ------------------------------


def test_generator_advances_and_is_never_reseeded():
    """Two steps, different noise; the state advances in-step; a re-seed between them bites."""
    dp = _seam(_model(), sigma=1.0, clip_norm=_NON_BINDING_CLIP, seed=13)

    dp.begin_step()
    _absorb(dp, seed=1)
    pre = dp._g.get_state().clone()
    dp.finalize(1)
    first = [p.grad.clone() for p in dp._params]
    assert not torch.equal(pre, dp._g.get_state()), "the generator did not advance within the step"

    dp.begin_step()
    _absorb(dp, seed=1)  # IDENTICAL record gradients, so any difference is the noise alone
    dp.finalize(1)
    second = [p.grad.clone() for p in dp._params]
    assert not any(torch.equal(a, b) for a, b in zip(first, second)), (
        "two consecutive steps produced identical released gradients from identical records — "
        "the noise is being reused across steps, which is FAKE 4"
    )

    # WATCHED RED: FAKE 4's positive insertion, applied from outside so the module stays honest.
    dp.begin_step()
    _absorb(dp, seed=1)
    dp._g.manual_seed(999)
    with pytest.raises(RuntimeError, match="dp-invariant:generator"):
        dp.finalize(1)


def test_sigma_zero_is_exact_zeros_through_the_same_code_path():
    """D-07, asserted as TWO INDEPENDENT FACTS: exact zeros, and the generator still advanced."""
    dp = _seam(_model(), sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=17)
    dp.begin_step()
    _absorb(dp, seed=1)

    pre = dp._g.get_state().clone()
    noise = dp._draw_noise()
    post = dp._g.get_state()

    # FACT 1: the drawn values are EXACTLY zero -- not close to zero.
    assert all(torch.equal(n, torch.zeros_like(n)) for n in noise)
    # FACT 2: the generator advanced anyway. This is what leaves "the noise never got added" with
    # nowhere to hide: the call sequence is identical at sigma = 0 and at sigma > 0.
    assert not torch.equal(pre, post)


# --- D-02: sum -> noise -> divide, with the divide LAST -------------------------------------------


@pytest.mark.parametrize("n_records", [1, 2])
def test_sum_then_noise_then_divide(n_records):
    """At sigma = 0 and a non-binding C the released term is the PLAIN MEAN, bit-for-bit.

    This is what pins D-02's ``/N`` placement structurally rather than by argument: get the divide
    wrong and this identity breaks immediately, on CPU, before any M3 time. Measured exact
    (``torch.equal``) at both N = 1 and N = 2 under torch 2.7.1 -- the accumulator starts at +0.0,
    ``x + 0.0`` and ``x * 1.0`` are bit-identical for finite x, and the division by a small power
    of two is exact.
    """
    dp = _seam(_model(), sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=19)
    dp.begin_step()
    records = [_absorb(dp, seed=k) for k in range(1, n_records + 1)]

    # `C = infinity` as an OBSERVATION, not a hope about the fixture's magnitudes.
    assert dp._clip_bind_count == 0, (
        f"the non-binding clip {_NON_BINDING_CLIP} bound on {dp._clip_bind_count} record(s), so "
        "the identity below is comparing a CLIPPED mean against an unclipped one"
    )
    dp.finalize(n_records)

    for i, p in enumerate(dp._params):
        expected = records[0][i]
        for r in records[1:]:
            expected = expected + r[i]
        assert torch.equal(p.grad, expected / n_records)


def test_finalize_refuses_a_divisor_that_is_not_the_record_count():
    """The ``/N`` LAST must divide by the number of records actually clipped and summed."""
    dp = _seam(_model(), sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=23)
    dp.begin_step()
    _absorb(dp, seed=1)
    with pytest.raises(RuntimeError, match="dp-invariant:lot"):
        dp.finalize(2)
    with pytest.raises(ValueError, match="dp-invariant:lot"):
        dp.finalize(0)
