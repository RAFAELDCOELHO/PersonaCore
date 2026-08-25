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

V-14 / DPSGD-02 -- SEAM OFF IS BIT-IDENTICAL, PROVEN TWO WAYS
------------------------------------------------------------
The ``dp_fn=`` seam is ADDITIVE, so ``dp_fn=None`` (or omitted) must reproduce the v1.0 trajectory
bit-for-bit. That is proven the same two ways ``tests/test_loop_penalty_fn.py`` proves it for
``penalty_fn`` -- executed evidence, not code review -- and this file REUSES that module's
``_run_recipe`` rather than defining a second one, because two recipes that drift is exactly the
failure the reuse prevents:

1. **Golden replay (platform-gated).** ``tests/fixtures/golden_trajectory_v1.json`` was captured
   from the git-clean, PRE-EDIT loop (its ``meta.captured_at_sha`` records the commit). The replay
   asserts exact CSV text + the ``repr`` of the final loss + the sha256 of the parameter bytes --
   but ONLY where ``(platform.system(), platform.machine(), torch.__version__)`` matches the
   fixture's ``meta.platform``. fp32 transcendental kernels are NOT bit-stable across OS/arch/BLAS
   backends OR torch releases, so x86_64 Linux CI -- **and equally a routine torch 2.7.x PATCH BUMP
   on the capture machine itself** -- must SKIP with that named reason, reading the mismatch as a
   STALE FIXTURE to regenerate rather than as a phantom loop regression, while the in-process
   identity below still passes.
2. **In-process identity (every platform, never skips).** ``dp_fn`` omitted vs ``dp_fn=None``
   asserted bitwise identical to EACH OTHER in the same process. This is what carries the
   guarantee when the platform gate skips.

Golden-fixture regeneration recipe (only ever from a git-clean, pre-edit ``loop.py``): the fixture's
``meta`` block documents the full capture -- ``seed_everything(meta.seed)``, build
``BigramLanguageModel(vocab_size=ModelConfig().vocab_size)``, then ``train()`` with
``TrainConfig(**meta.train_config)``, ``RuntimeConfig(device="cpu")`` passed EXPLICITLY,
``corpus_path=meta.corpus``, ``eos_id=meta.eos_id``, ``eval_interval=meta.eval_interval``, a temp
``log_path``, ``return_final_loss=True``; record the CSV text, ``repr(float(final))`` and the
``hashlib.sha256`` of the parameter bytes plus the new ``git rev-parse HEAD`` and the capturing
platform's identity.

**The golden recipe trains a ``BigramLanguageModel``, not GPT+LoRA**, so ``DPSGD.__init__``'s D-04
census would correctly REFUSE it. The golden tests therefore run with the seam OFF only; the sigma
of zero identity further down builds its own GPT+LoRA fixture rather than feeding a bigram to
``DPSGD``.

D-06 -- THE TWO SIGMA-OF-ZERO CLAIMS, NAMED APART SO NEITHER BORROWS THE OTHER'S WEIGHT
---------------------------------------------------------------------------------------
This file ships the **Phase 22 MECHANISM-CORRECTNESS** claim: CPU, fixture scale, deterministic,
CI-reproducible, ``train(dp_fn=None)`` reproduced by ``dp_fn`` at a sigma of zero and a non-binding
``C``, bitwise at ``grad_accum_steps = 1`` and to a MEASURED relative tolerance above it.

Phase 23's **DPSGD-06 SCIENTIFIC-RESULT** claim is a different thing entirely: M3, the real corpus,
200 steps, sigma of zero reproducing the unmitigated control *within the measured seed-to-seed noise
floor*. It is **NOT bit-identical, by design**. Neither claim substitutes for the other and neither
may be cited for the other -- Phase 20's ``borrowed_cap`` discipline, two artifacts and two claims.

CPU-only, GPU-free, no network.
"""

import math
import pathlib
import platform
import sys

import pytest
import torch
from torch.amp import GradScaler

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.lora.config import LoRAConfig
from personacore.lora.inject import inject_lora, mark_only_lora_trainable
from personacore.model.gpt import GPT
from personacore.privacy.dpsgd import DPSGD
from personacore.training.loop import _optimizer_step, train
from personacore.training.schedule import build_scheduler

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "tests"))

# The GOLDEN recipe is imported, never re-written. A second copy is free to drift from the
# fixture's own `meta` block, and then a green golden replay proves nothing about the capture. This
# is `tests/test_phase21_aligned_loader.py:43-49`'s cross-test idiom verbatim.
#
# MEASURED, and stated precisely because the obvious phrasing is false: `grep -rn "def _run_recipe"
# tests/` returns FOUR definitions, not one — test_loop_penalty_fn.py:73 (this one),
# test_extra_eval_fns.py:42 and test_masked_train_seam.py:150. The other two predate Phase 22 and
# drive DIFFERENT fixtures (the telemetry seam and the mask seam); neither touches
# golden_trajectory_v1.json. So the property that actually matters holds and is the one to assert:
# exactly ONE recipe drives the GOLDEN fixture, and this plan added no new recipe at all.
from test_loop_penalty_fn import (  # noqa: E402  (tests/ is not a package)
    _CAPTURE_PLATFORM,
    _GOLDEN,
    _run_recipe,
)

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


# =============================================================================================
# V-14 / DPSGD-02 -- the seam OFF is bit-identical to the Phase-10 golden trajectory.
#
# See the module docstring for the two-way proof, the regeneration recipe, and the reason the
# golden half is platform-gated while the in-process half never skips.
# =============================================================================================


def test_golden_fixture_is_the_phase10_one():
    """META-GUARD: a truncated or regenerated fixture must not make the identity vacuous.

    Every assertion in ``test_seam_off_bit_identical`` compares against a key of ``_GOLDEN``. A
    fixture that lost ``csv_text`` (or shipped it empty) would turn ``csv_text == _GOLDEN[...]``
    into a comparison of two empty strings, and the bit-identity claim would be green over nothing.
    """
    assert set(_GOLDEN) == {"csv_text", "final_loss_repr", "param_sha256", "meta"}, sorted(_GOLDEN)
    assert _GOLDEN["csv_text"].strip(), (
        "the golden CSV text is empty — the identity would be vacuous"
    )
    assert _GOLDEN["csv_text"].startswith("step,train_loss,val_loss,lr,tokens,wall_clock"), (
        f"the golden CSV header is not the v1.0 one: {_GOLDEN['csv_text'][:80]!r}"
    )
    # sha256 hex digest, and a param_sha256 of the empty string would still be 64 hex chars — so
    # the CSV assertions above are what stop an empty capture, not this one.
    assert len(_GOLDEN["param_sha256"]) == 64, _GOLDEN["param_sha256"]
    assert _GOLDEN["final_loss_repr"], "the golden final-loss repr is empty"


@pytest.mark.skipif(
    (platform.system(), platform.machine(), torch.__version__) != _CAPTURE_PLATFORM,
    reason=(
        "V-14's golden bitwise replay is only valid on the capture platform + torch build "
        f"{_CAPTURE_PLATFORM} (running torch {torch.__version__}) — fp32 transcendental kernels "
        "are not bit-stable across OS/arch/BLAS backends OR torch releases, so a mismatch here is "
        "a STALE FIXTURE to regenerate per the module docstring recipe, NOT a phantom loop "
        "regression; reading it the other way would make a routine torch 2.7.x patch bump look "
        "like the dp_fn seam broke v1.0. test_seam_omitted_equals_seam_none carries the "
        "DPSGD-02 guarantee on every platform either way"
    ),
)
def test_seam_off_bit_identical(tmp_path):
    """V-14, platform-gated half: ``dp_fn=None`` reproduces the golden trajectory BYTE FOR BYTE.

    All three fingerprints, none of them a loss curve: exact CSV TEXT, the exact ``repr`` of the
    final loss, and the sha256 of the parameter BYTES. "The loss curve matches" is not bit-identity
    and is not what this asserts.
    """
    csv_text, final_repr, sha = _run_recipe(tmp_path / "dp_seam_off.csv", dp_fn=None)
    assert csv_text == _GOLDEN["csv_text"]
    assert final_repr == _GOLDEN["final_loss_repr"]
    assert sha == _GOLDEN["param_sha256"]


def test_seam_omitted_equals_seam_none(tmp_path):
    """V-14, platform-INDEPENDENT half: omitting ``dp_fn`` and passing ``None`` are identical.

    Never skips. This is the assertion CI relies on wherever the golden replay's platform gate
    fires, and it is the ``tests/test_loop_penalty_fn.py::test_omitted_equals_none_in_process``
    shape: two runs in the SAME process, so the comparison is free of any cross-platform kernel
    question, and all three fingerprints must agree bitwise.
    """
    omitted = _run_recipe(tmp_path / "omitted.csv")
    explicit_none = _run_recipe(tmp_path / "none.csv", dp_fn=None)
    assert omitted == explicit_none  # (csv_text, final_loss_repr, param_sha256), all bitwise


# =============================================================================================
# V-12 / D-05 axis 2 -- the ONE-KWARG-APART differential, D-03's runtime half, and D-06's
# separately-named sigma-of-zero identity. All three run on CPU at fixture scale.
# =============================================================================================

# Deterministic synthetic ids, drawn ONCE from a dedicated generator so the global torch stream is
# untouched and both branches of every differential below see byte-identical inputs.
_FIXTURE_GEN = torch.Generator().manual_seed(20220612)
_MICRO_BS = 2
_CTX = 24
_STEP_X = torch.randint(0, ModelConfig().vocab_size, (8, _CTX), generator=_FIXTURE_GEN)
_STEP_Y = torch.randint(0, ModelConfig().vocab_size, (8, _CTX), generator=_FIXTURE_GEN)
_REPLAY_X = torch.randint(0, ModelConfig().vocab_size, (4, _CTX), generator=_FIXTURE_GEN)
_REPLAY_Y = torch.randint(0, ModelConfig().vocab_size, (4, _CTX), generator=_FIXTURE_GEN)


def _step_batch_fn(micro):
    sl = slice(micro * _MICRO_BS, (micro + 1) * _MICRO_BS)
    return _STEP_X[sl], _STEP_Y[sl]


def _public_replay_fn(model, scaler):
    """A real un-clipped public pass, in ``replay_fn``'s exact ``(model, scaler)`` shape."""
    _, replay_loss = model(_REPLAY_X, _REPLAY_Y)
    scaler.scale(replay_loss).backward()


def _dp_optimizer_step(*, replay_fn, capture, sigma=_SIGMA, clip_norm=_CLIP, seed=4242):
    """Drive ONE real ``_optimizer_step`` on a GPT+LoRA fixture with the DP seam live.

    Returns ``(mixed_grads, dp)``; the private term lands in ``capture`` via the ``_write_once``
    spy the caller installs, so the private and public terms can be compared SEPARATELY after they
    have already met in ``.grad``.
    """
    model = _model()
    runtime = RuntimeConfig(device="cpu")
    cfg = TrainConfig(
        lr=1e-3,
        warmup_steps=0,
        max_steps=1,
        batch_size=_MICRO_BS,
        grad_accum_steps=2,
        grad_clip=_NON_BINDING_CLIP,
    )
    dp = _seam(model, sigma=sigma, clip_norm=clip_norm, seed=seed, runtime=runtime)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr)
    scheduler = build_scheduler(optimizer, cfg)
    scaler = GradScaler(device="cpu", enabled=False)
    before = len(capture)
    _optimizer_step(
        model, optimizer, scheduler, scaler, cfg, runtime, _step_batch_fn, None, replay_fn, dp
    )
    assert len(capture) == before + 1, (
        f"the _write_once spy recorded {len(capture) - before} private terms for one optimizer "
        "step — the capture is broken and the comparison below would be over stale tensors"
    )
    return [p.grad.detach().clone() for p in dp._params], dp


def test_side_channel_negative_control(monkeypatch):
    """V-12 / D-05 axis 2: the private noised term is byte-identical ONE KWARG APART.

    The SAME call site — ``_optimizer_step`` — is run twice, differing ONLY in whether
    ``replay_fn`` is present. That is what makes this a property of the **BRANCH** rather than of
    two different fixtures: identical model init, identical micro-batches, identical DP seed, one
    kwarg. The dedicated generator is consulted the same number of times in the same order in both
    branches, and the public pass runs strictly AFTER the per-record accumulation loop, so it
    cannot perturb either the per-record gradients or the noise stream.

    **Both halves are load-bearing** (``tests/test_phase21_replay_volume.py::test_side_channel_
    negative_control``'s discipline). The fixture is proven to VARY first: without that, the
    byte-identity below would be a comparison over an implementation that returns a constant for
    every input — green while saying nothing about the mechanism.

    Measured on this fixture: **36 of 72** mixed buffers differ between the two branches. The other
    36 are the ``lora_A`` gradients, which are EXACTLY ZERO for the replay pass too, because
    ``lora_B`` is initialised to zeros and ``dL/dA`` carries a factor of ``B``. So the variation
    lives entirely in the ``lora_B`` half — one per wrapped module — which is a structural fact
    about LoRA init rather than a coincidence, and it is asserted as such.
    """
    capture = []
    real_write = DPSGD._write_once

    def _spy_write(self, private):
        capture.append([t.detach().clone() for t in private])
        return real_write(self, private)

    monkeypatch.setattr(DPSGD, "_write_once", _spy_write)

    mixed_private_only, dp_a = _dp_optimizer_step(replay_fn=None, capture=capture)
    private_only = capture[-1]
    mixed_with_public, dp_b = _dp_optimizer_step(replay_fn=_public_replay_fn, capture=capture)
    with_public = capture[-1]

    # 1 — THE FIXTURE ACTUALLY VARIES. The public term really reaches .grad, so the differential
    # below is observed over a genuinely varying input.
    differing = [
        i
        for i, (a, b) in enumerate(zip(mixed_private_only, mixed_with_public))
        if not torch.equal(a, b)
    ]
    assert len(differing) == _FROZEN_TENSORS // 2, (
        f"{len(differing)} of {_FROZEN_TENSORS} mixed buffers differ between the two branches, "
        f"not the expected {_FROZEN_TENSORS // 2}. Exactly the lora_B half must move: lora_A's "
        "gradient carries a factor of B and B is initialised to zeros, so the replay pass "
        "contributes exactly 0.0 there. A count of 0 means replay_fn never reached .grad and the "
        "byte-identity below would be comparing a branch against itself"
    )

    # 2 — THE PRIVATE NOISED TERM IS BYTE-IDENTICAL ACROSS BOTH BRANCHES. Not "close": torch.equal.
    for i, (a, b) in enumerate(zip(private_only, with_public)):
        assert torch.equal(a, b), (
            f"the private noised term for parameter {i} moved when the PUBLIC replay term was "
            "added. The released private magnitude must not be a function of public data — that "
            "is D-03's surviving rule, and a difference here means something between the noise "
            "and optimizer.step() mixed the two terms before the single combining write"
        )

    # The two branches consumed the generator identically, and the clip behaved identically.
    assert torch.equal(dp_a.noise_rng_state(), dp_b.noise_rng_state())
    assert dp_a._records == dp_b._records == 2
    assert dp_a._clip_bind_count == dp_b._clip_bind_count


def test_legacy_clip_is_unreachable_on_the_dp_path(monkeypatch):
    """D-03's RUNTIME half: the legacy clip fires once per step with the seam off, zero with it on.

    This is the runtime half ONLY. The STRUCTURAL half — ``clip_grad_norm_`` having exactly one
    reachable call site in ``loop.py`` and that site sitting inside ``if dp_fn is None:`` — is what
    actually carries D-03, and it is enforced by ``tests/test_phase22_dpsgd_ast.py``'s closure
    guards, because a runtime check on TODAY's inputs cannot catch a FUTURE edit that reintroduces
    the call on the DP path.

    The seam-off branch is the CONTROL and is not optional: without it a broken spy (one that never
    records) would make the seam-on assertion vacuously green.
    """
    calls = []
    real_clip = torch.nn.utils.clip_grad_norm_

    def _spy_clip(params, max_norm, *a, **k):
        calls.append("clip")
        return real_clip(params, max_norm, *a, **k)

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", _spy_clip)

    steps = 2
    cfg = TrainConfig(
        lr=1e-3, warmup_steps=0, max_steps=steps, batch_size=_MICRO_BS, grad_accum_steps=1
    )
    runtime = RuntimeConfig(device="cpu")

    off = _model()
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=off,
        model_config=ModelConfig(),
        fixed_batch=(_STEP_X[:_MICRO_BS], _STEP_Y[:_MICRO_BS]),
    )
    assert calls.count("clip") == steps, (
        f"the seam-OFF control fired the legacy clip {calls.count('clip')} times over {steps} "
        "optimizer steps, not once per step — the spy is not observing the call site, so the "
        "seam-ON assertion below would be green over a broken instrument"
    )

    calls.clear()
    on = _model()
    dp = _seam(on, sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=31, runtime=runtime)
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=on,
        model_config=ModelConfig(),
        fixed_batch=(_STEP_X[:_MICRO_BS], _STEP_Y[:_MICRO_BS]),
        dp_fn=dp,
    )
    assert calls.count("clip") == 0, (
        f"the legacy clip_grad_norm_ fired {calls.count('clip')} times on the DP path. It clips "
        "the MIXED buffer, so the released private magnitude becomes a function of PUBLIC data — "
        "and, measured, renormalising to a fixed norm ERASES exactly the signal the "
        "wrong-sensitivity positive control detects, so that fake would converge AND pass"
    )
    assert dp._records == 1 and dp._clip_bind_count == 0


# The documented relative tolerance for the sigma-of-zero identity at a NON-POWER-OF-TWO
# grad_accum_steps, with the measurement it ships against rather than a guessed bound. See
# `test_sigma_zero_non_binding_clip_reproduces_the_default_path` for the full measurement table.
_ACCUM_IDENTITY_REL_TOL = 1e-4


def _identity_run(*, grad_accum_steps, with_dp, clip_record=None):
    """One short GPT+LoRA recipe, run either seam-off or with a sigma-of-zero seam."""
    model = _model()
    runtime = RuntimeConfig(device="cpu")
    # grad_clip is set to the SAME non-binding bound as C. `C = infinity` on the DP side has no
    # meaning for the identity unless the legacy clip is equally inert on the control side: these
    # are two DIFFERENT clips and EITHER one binding breaks the identity for a different reason.
    # At TrainConfig's default grad_clip = 1.0 the legacy clip DOES bind on this fixture (measured
    # pre-clip norm 2.0938 at step 1), which is precisely why non-binding is arranged and then
    # OBSERVED rather than assumed.
    cfg = TrainConfig(
        lr=1e-3,
        warmup_steps=0,
        max_steps=2,
        batch_size=_MICRO_BS,
        grad_accum_steps=grad_accum_steps,
        grad_clip=_NON_BINDING_CLIP,
    )
    dp = (
        _seam(model, sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=101, runtime=runtime)
        if with_dp
        else None
    )
    real_clip = torch.nn.utils.clip_grad_norm_
    if clip_record is not None:

        def _observing_clip(params, max_norm, *a, **k):
            params = list(params)
            before = [p.grad.detach().clone() for p in params if p.grad is not None]
            total_norm = real_clip(params, max_norm, *a, **k)
            after = [p.grad for p in params if p.grad is not None]
            unchanged = all(torch.equal(b, a2) for b, a2 in zip(before, after))
            clip_record.append((float(total_norm), float(max_norm), unchanged))
            return total_norm

        torch.nn.utils.clip_grad_norm_ = _observing_clip
    try:
        train(
            train_config=cfg,
            runtime_config=runtime,
            model=model,
            model_config=ModelConfig(),
            dp_fn=dp,
            return_final_loss=True,
        )
    finally:
        torch.nn.utils.clip_grad_norm_ = real_clip
    params = {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}
    return params, dp


@pytest.mark.parametrize("grad_accum_steps", [1, 4, 3])
def test_sigma_zero_non_binding_clip_reproduces_the_default_path(grad_accum_steps):
    """D-06's **Phase-22 MECHANISM-CORRECTNESS** claim: sigma of zero + non-binding C == default.

    This is NOT Phase 23's DPSGD-06 scientific-result claim. That one is M3, the real corpus, 200
    steps, and agreement only within the measured seed-to-seed noise floor — not bit-identical by
    design. Neither borrows the other's weight; see the module docstring.

    It is what pins D-02's ``1/N`` placement STRUCTURALLY rather than by argument: inherit
    ``loop.py``'s ``loss = total / accum`` on the DP path and the released term is off by a factor
    of ``N``, so this CPU identity breaks immediately, before any M3 time is spent.

    **Both clips are asserted NOT TO BIND, and they are two different clips.** ``clip_grad_norm_``
    on the control run (observed through a spy that compares the gradient buffers before and after
    the real call — an OBSERVATION, not a model of torch's internal ``clip_coef`` arithmetic) and
    ``DPSGD``'s per-record clip on the DP run (``_clip_bind_count == 0``, asserted BEFORE the
    parameters are compared). Either one binding would break the identity for a different reason,
    and at ``TrainConfig``'s default ``grad_clip = 1.0`` the legacy clip really does bind here —
    measured pre-clip norm ``2.0937681198120117`` at step 1 — so this is inert BY CONSTRUCTION,
    never inert by accident.

    **Measured, this identity is BITWISE at every power-of-two lot size and only there.** The
    default path divides the LOSS by ``accum`` before ``backward()`` while the DP path divides the
    summed GRADIENT after; scaling by a power of two is exact in IEEE-754, so the two orders agree
    bit-for-bit — but only then. Measured over 2 optimizer steps on this fixture, as
    ``||theta_default - theta_dp|| / ||theta_default||`` over all 72 concatenated LoRA tensors:

    ======  =================  =========================
    accum   bitwise tensors    global relative deviation
    ======  =================  =========================
    1       72/72              0.000000e+00
    2       72/72              0.000000e+00
    4       72/72              0.000000e+00
    8       72/72              0.000000e+00
    3        0/72              5.681269e-06
    5        0/72              8.573839e-05
    6        0/72              1.737541e-04
    7        0/72              5.290843e-06
    ======  =================  =========================

    D-06 allows "bitwise **or** documented tolerance". The plan expected ``accum = 4`` to need the
    tolerance; measured it does not, so ``4`` asserts BITWISE and a third case at ``accum = 3`` —
    the smallest non-power-of-two — carries the documented tolerance instead. A tolerance nobody
    needs is a tolerance a future error can hide in.

    ``_ACCUM_IDENTITY_REL_TOL = 1e-4`` sits ~18x above the measured 5.68e-06 and is still three
    orders BELOW what the failure it exists to catch would produce: inheriting the ``/accum``
    divide on the DP path scales the released term by ``1/N``, an O(1) relative error at any
    ``N > 1``, not an O(1e-5) one.
    """
    clip_record = []
    control, _ = _identity_run(
        grad_accum_steps=grad_accum_steps, with_dp=False, clip_record=clip_record
    )
    private, dp = _identity_run(grad_accum_steps=grad_accum_steps, with_dp=True)

    # NON-BINDING 1, the LEGACY clip on the control run — observed, not modelled.
    assert len(clip_record) == 2, f"the clip spy recorded {len(clip_record)} calls, not 2"
    for total_norm, max_norm, unchanged in clip_record:
        assert total_norm <= max_norm, (
            f"the legacy clip's pre-clip norm {total_norm!r} exceeds grad_clip {max_norm!r}, so "
            "the control run's gradients were RESCALED and the identity below would be comparing "
            "a clipped trajectory against an unclipped one"
        )
        assert unchanged, (
            f"the legacy clip changed the gradient buffers at pre-clip norm {total_norm!r} "
            f"against grad_clip {max_norm!r} — the coefficient was not exactly 1.0"
        )

    # NON-BINDING 2, the DP per-record clip — a COUNTED observation over the whole run.
    assert dp._clip_bind_count == 0, (
        f"the non-binding bound {_NON_BINDING_CLIP} bound on {dp._clip_bind_count} record(s), so "
        "the comparison below is between a CLIPPED mean and an unclipped one rather than between "
        "two orderings of the same arithmetic"
    )
    assert dp._records == grad_accum_steps

    assert sorted(control) == sorted(private) and len(control) == _FROZEN_TENSORS
    bitwise = [name for name in control if torch.equal(control[name], private[name])]
    flat_control = torch.cat([control[name].flatten() for name in sorted(control)])
    flat_private = torch.cat([private[name].flatten() for name in sorted(control)])
    rel = float(
        torch.linalg.vector_norm(flat_control - flat_private)
        / torch.linalg.vector_norm(flat_control)
    )

    if grad_accum_steps & (grad_accum_steps - 1) == 0:  # a power of two -> exact loss-side scaling
        assert len(bitwise) == _FROZEN_TENSORS, (
            f"only {len(bitwise)} of {_FROZEN_TENSORS} tensors are bitwise identical at "
            f"grad_accum_steps={grad_accum_steps} (relative deviation {rel:.6e}). Scaling by a "
            "power of two is exact in IEEE-754, so the loss-side and gradient-side divides must "
            "agree bit-for-bit here"
        )
        assert rel == 0.0
    else:
        assert rel <= _ACCUM_IDENTITY_REL_TOL, (
            f"the sigma-of-zero identity deviates by {rel:.6e} at "
            f"grad_accum_steps={grad_accum_steps}, above the documented "
            f"{_ACCUM_IDENTITY_REL_TOL:.0e}. Inheriting loop.py's /accum divide on the DP path is "
            "an O(1) error, so a deviation this large is a different defect than the one the "
            "tolerance exists to absorb"
        )
        # NON-DEGENERACY: the tolerance must be doing work here, or this branch is green over a
        # sample that `==` would have passed too (22-05's sweep-control discipline).
        assert bitwise == [], (
            f"{len(bitwise)} of {_FROZEN_TENSORS} tensors are bitwise identical at a "
            f"NON-power-of-two grad_accum_steps={grad_accum_steps} — the tolerance branch is "
            "asserting nothing the bitwise branch would not already have caught"
        )


def test_dp_noise_rng_round_trips_through_a_kill_and_resume(tmp_path):
    """D-14 / DPSGD-05 wiring: the noise generator's state survives a kill+resume, BOTH halves.

    A write-only slot is worse than no slot, so both directions are asserted here. The SAVE half is
    the ``_dp_extra()`` splat, and the site that matters is the **END-OF-CALL** one:
    ``max_steps_override`` is ``train()``'s own documented *"kill in the resume test"*, and such a
    kill exits the ``while`` loop NORMALLY — so the checkpoint the resume reads is written after
    the ``finally:``, not by either in-loop site. A splat added only in-loop passes a grep and
    still misses the one that is read.

    The READ half is the ``resume_from`` block's ``.get()``-guarded
    ``dp_fn.load_noise_rng_state``. Without it ``DPSGD.__init__`` re-seeds from the caller's seed
    and the resumed run REPLAYS NOISE IT ALREADY RELEASED — DPSGD-04/SC4's fourth named fake
    reachable through PRODUCTION. D-16 invariant 4 cannot see it: ``_prev_gen_state`` is ``None``
    on a freshly constructed object, so the continuity check is vacuous on the first post-resume
    step. That is why this is wiring rather than something a runtime invariant covers.

    The pre-Phase-22 checkpoint case is asserted too: the key is absent from every checkpoint this
    project has ever written, and ``.get()`` rather than a subscript is what keeps them loadable.
    """
    runtime = RuntimeConfig(device="cpu")
    cfg = TrainConfig(
        lr=1e-3, warmup_steps=0, max_steps=4, batch_size=_MICRO_BS, grad_accum_steps=1
    )
    batch = (_STEP_X[:_MICRO_BS], _STEP_Y[:_MICRO_BS])
    latest = tmp_path / "latest.pt"

    pre_kill = _model()
    dp_pre = _seam(pre_kill, sigma=1.0, clip_norm=_NON_BINDING_CLIP, seed=77, runtime=runtime)
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=pre_kill,
        model_config=ModelConfig(),
        fixed_batch=batch,
        dp_fn=dp_pre,
        checkpoint_path=latest,
        max_steps_override=1,  # the "kill" — exits the while loop normally
    )
    blob = torch.load(latest, weights_only=False)
    assert "dp_noise_rng" in blob, (
        "the END-OF-CALL save carries no dp_noise_rng. max_steps_override exits the loop normally, "
        "so this is the save a resume reads — an in-loop-only splat misses exactly this one"
    )
    assert torch.equal(blob["dp_noise_rng"], dp_pre.noise_rng_state()), (
        "the saved dp_noise_rng is not the LIVE generator state. checkpoint_extra is bound once at "
        "train() entry, which is why the state is read through a closure at each save instead"
    )
    assert blob["schema_version"] == 1, "dp_noise_rng rides **extra — the schema must NOT bump"

    resumed = _model()
    dp_post = _seam(resumed, sigma=1.0, clip_norm=_NON_BINDING_CLIP, seed=999, runtime=runtime)
    # POSITIVE CONTROL: the fresh seam's stream really is somewhere else, so the equality after the
    # resume is the restore working rather than two objects that agreed to begin with.
    assert not torch.equal(dp_post.noise_rng_state(), blob["dp_noise_rng"])
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=resumed,
        model_config=ModelConfig(),
        fixed_batch=batch,
        dp_fn=dp_post,
        resume_from=latest,
        max_steps_override=1,  # already at step 1 -> no further steps, so no draw perturbs this
    )
    assert torch.equal(dp_post.noise_rng_state(), blob["dp_noise_rng"]), (
        "the resumed seam's generator was NOT restored from dp_noise_rng, so it re-seeds from the "
        "caller's seed and replays noise the pre-kill run already released"
    )

    # BACK-COMPAT: every checkpoint written before Phase 22 lacks the key, and `.get()` is what
    # keeps them resumable with the seam live.
    del blob["dp_noise_rng"]
    old = tmp_path / "pre_phase22.pt"
    torch.save(blob, old)
    legacy = _model()
    dp_legacy = _seam(legacy, sigma=1.0, clip_norm=_NON_BINDING_CLIP, seed=5, runtime=runtime)
    fresh_state = dp_legacy.noise_rng_state().clone()
    train(
        train_config=cfg,
        runtime_config=runtime,
        model=legacy,
        model_config=ModelConfig(),
        fixed_batch=batch,
        dp_fn=dp_legacy,
        resume_from=old,
        max_steps_override=1,
    )
    assert torch.equal(dp_legacy.noise_rng_state(), fresh_state), (
        "a pre-Phase-22 checkpoint moved the generator state — the .get() guard let a missing key "
        "through as something other than 'no restore'"
    )


# The band on the empirical noise standard deviation below. The relative standard error of a
# sample standard deviation over `n` normals is ~1/sqrt(2n); at n = 331,776 that is 0.123%, and the
# measured deviation is 0.069%. 1% is ~8x the standard error and ~400x below the factor-of-N error
# the test exists to catch.
_NOISE_STD_REL_BAND = 0.01


@pytest.mark.parametrize("n_records", [1, 4])
def test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST(n_records):
    """FAKE 3 (*noise added after averaging*), which the sigma-of-zero identity CANNOT see.

    **This test exists because a mutation probe measured the guard it replaces to be incapable.**
    D-17's fake table credits D-06's CPU identity with detecting *noise added after averaging*
    ("build divide -> noise; watch the identity break"). Watched: rewriting ``finalize`` to divide
    the accumulator BEFORE ``_noised_private`` and then divide by 1 leaves the whole suite GREEN,
    including every sigma-of-zero identity. The reason is structural rather than incidental — at a
    sigma of zero the drawn values are EXACTLY zero, so ``(sum + 0)/N`` and ``(sum/N) + 0`` are the
    same number for every N. An identity taken at the one sigma where the noise vanishes can never
    see where the noise was added.

    So the order is pinned where it is observable: at ``sigma > 0`` and over the noise MAGNITUDE.
    With every record's gradient set to exactly zero the accumulator is the zero vector and the
    released term is PURE NOISE divided by the lot size, so its standard deviation must be
    ``sigma * C / N``. Under the wrong order it would be ``sigma * C`` — a factor of ``N``, which
    at ``N = 4`` is 400x outside this test's band.

    Measured over all 331,776 released elements at ``sigma = 1.0``, ``C = 1.0``: ``std`` is
    ``1.00069046`` at ``N = 1`` and ``0.25017262`` at ``N = 4``, both a ratio of ``1.000690`` to
    the expectation — one draw's sampling deviation, within the 0.123% standard error of a sample
    standard deviation at this ``n``.
    """
    dp = _seam(
        _model(), sigma=_SIGMA, clip_norm=_CLIP, seed=61, runtime=RuntimeConfig(device="cpu")
    )
    dp.begin_step()
    for _ in range(n_records):
        for p in dp._params:
            p.grad = torch.zeros_like(p)
        dp.absorb_record()

    # POSITIVE CONTROL: the accumulated SUM really is the zero vector, so everything released below
    # is noise and the standard deviation is not measuring a gradient.
    assert dp._global_norm(dp._accum) == 0.0
    assert dp._clip_bind_count == 0
    dp.finalize(n_records)

    released = torch.cat([p.grad.flatten() for p in dp._params])
    assert released.numel() == _FROZEN_PARAMS
    expected = _SIGMA * _CLIP / n_records
    ratio = float(released.std()) / expected
    assert abs(ratio - 1.0) <= _NOISE_STD_REL_BAND, (
        f"the released noise has std {float(released.std())!r} at N = {n_records}, a ratio of "
        f"{ratio:.6f} to the expected sigma*C/N = {expected!r}. D-02 puts the /N LAST: the noise "
        "is added to the SUM (one record moves the sum by at most C — the textbook sensitivity "
        f"argument) and only then divided. A ratio near {n_records} means the divide moved AHEAD "
        "of the draw, so the released noise is N times too large for the sensitivity the "
        "accountant was told"
    )
