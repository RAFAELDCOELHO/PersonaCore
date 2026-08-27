"""Phase 22 -- DPSGD-04's four positive controls: each fake WATCHED firing its guard.

**DPSGD-04's requirement is the OBSERVED RED, not the final green** -- a suite that is green today
cannot prove a guard ever fired, so each of the four silent-non-privacy fakes is applied
deliberately here and its guard is watched refusing, RED-then-GREEN, in one process.

The four watched failures over the REAL committed source -- the mutated MODULE rather than a
mutated object -- are captured verbatim in this plan's SUMMARY
(``.planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-11-SUMMARY.md``),
with the mutation diff, the failing node id, the assertion message, and the byte-identical restore
proof. **This file holds the COMMITTED, REPEATABLE halves**, so a future reader does not have to
trust a SUMMARY: every probe below re-applies its fake and re-observes its refusal on every run.

Every AST half runs THE LIVE GUARD FUNCTIONS CI RUNS, by repointing
``tests/test_phase22_dpsgd_ast.py``'s ``_DPSGD_PATH`` at a mutated copy -- never a re-implementation
(``tests/test_phase20_prereg.py:153-155``: *a guard proved correct in a scratch repository and a
guard running against this one must be the SAME code, or the proof is about a different function
than the one CI runs*). Every probe carries an UNMUTATED CONTROL asserted in the same test, so a
probe that reddens because the harness broke cannot be mistaken for a detection.

**D-17's fake table is used in its CORRECTED form.** The table credits D-06's sigma-of-zero identity
with detecting FAKE 3 (*noise added after averaging*). 22-06 measured that row FALSE -- at a sigma
of zero the drawn values are exactly zero, so ``(S + 0)/N`` and ``(S/N) + 0`` are the same bytes and
the divide's position is unobservable. This file measures the blind spot again, in both of its
directions (sigma = 0 at any lot size, and accum = 1 at any sigma), and asserts the two detectors
that DO work: the sigma > 0 / accum > 1 magnitude differential, and the statement-order structural
check.

**THE RUNTIME HALVES RUN ON BOTH CPU AND MPS (23-06 / D-02).** DPSGD-04's deliverable was never
"the tests pass" -- it was the OBSERVED RED against the real mutated module, and that observation
was made on CPU while D-01 puts this milestone's published epsilon on the M3. Each of the four
probes below is therefore parametrized over ``_DEVICES`` (imported from
``tests/test_phase23_mps_venue.py``, this phase's SINGLE device register) and re-applies its
mutation, re-watches its refusal and re-confirms the restore on the venue that ships. Phase 22's
CPU-only result is recorded as *not transferred to MPS* and then transferred by measurement; it is
never inherited. **The AST halves are EXEMPT and the exemption is APPLIED AT THE POINT OF USE**
(``_AST_HALF_RUNS_ON``) rather than silently inherited -- see ``_DEVICE_INVARIANT_HALVES``.

GPU-free (no CUDA); the MPS legs are ``skipif``-gated so CI stays green on a CPU-only wheel.
"""

import pathlib
import sys

import pytest
import torch

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "tests"))

# The guards are IMPORTED, never re-spelled. `ast_guards` is imported as a MODULE rather than by
# symbol because the AST halves below monkeypatch `ast_guards._DPSGD_PATH` and then call the live
# test functions themselves -- the strongest available form of "the same code CI runs".
import test_phase22_dpsgd_ast as ast_guards  # noqa: E402
from personacore.privacy.dpsgd import DPSGD  # noqa: E402
from test_phase22_dpsgd import (  # noqa: E402  (tests/ is not a package)
    _FROZEN_PARAMS,
    _GRAD_SCALE,
    _model,
)

# The phase's SINGLE device register, IMPORTED rather than re-spelled: two copies of a device gate
# drift, and a drifted gate is how an MPS leg stops being counted (23-01).
from test_phase23_mps_venue import _DEVICES, _MPS_SKIP  # noqa: E402

# The real mechanism's path, captured from the AST module at import time so the mutated-copy
# monkeypatching below cannot make this read the mutation back.
_REAL_DPSGD_PATH = ast_guards._DPSGD_PATH

_SUMMARY_PATH = (
    _ROOT
    / ".planning"
    / "phases"
    / "22-dp-sgd-core-accountant-and-the-correctness-battery"
    / "22-11-SUMMARY.md"
)

# Test-local arithmetic vectors, NOT a budget (D-08 / Phase 20's Z boundary), in exactly the sense
# `tests/test_phase22_dpsgd.py` draws its own.
_SIGMA = 1.0
_CLIP = 1.0
_NON_BINDING_CLIP = 1e6

# D-02's exemption, APPLIED AT THE POINT OF USE. The four probes' AST halves feed SOURCE TEXT to
# `ast.parse`; there is no tensor, no generator and no device for a result to depend on, so an
# `[mps]` leg re-running them would execute byte-identical code under a node id CLAIMING a device
# pass it did not perform -- T-23-28, the exact defect D-02 exists to prevent. They run on the
# `cpu` leg only, and the exemption is recorded with its measured count in
# `_DEVICE_INVARIANT_HALVES` rather than inferred from the absence of an mps run.
_AST_HALF_RUNS_ON = "cpu"


def _real_source():
    """The mechanism's own committed bytes, behind the AST module's own meta-guards."""
    source = _REAL_DPSGD_PATH.read_text(encoding="utf-8")
    assert source.strip() and "class DPSGD" in source, (
        f"{_REAL_DPSGD_PATH} is empty or no longer defines `class DPSGD` -- every mutation below "
        "would be applied to nothing and every RED would be unattributable"
    )
    return source


def _mutate(source, target, replacement):
    """One-line replacement, asserted to have APPLIED.

    22-09's discipline: a mutation that silently matched nothing leaves the RED half green over
    UNMUTATED source, which is a probe certifying a guard it never exercised.
    """
    assert source.count(target) == 1, (
        f"the mutation target appears {source.count(target)} times, not once, so the applied "
        f"mutation would be ambiguous or absent:\n{target!r}"
    )
    mutated = source.replace(target, replacement, 1)
    assert mutated != source, "the replacement is a no-op -- this probe would test nothing"
    return mutated


def _run_live_guard(monkeypatch, tmp_path, source, guard, **kwargs):
    """Run one of ``test_phase22_dpsgd_ast``'s LIVE tests over ``source``.

    The live tests read ``ast_guards._DPSGD_PATH`` through ``_dpsgd_source()`` at CALL time, so
    repointing that one module attribute at a temp copy runs the exact function CI runs over the
    mutated bytes. The work tree is never written to.
    """
    path = tmp_path / "dpsgd_under_probe.py"
    path.write_text(source, encoding="utf-8")
    monkeypatch.setattr(ast_guards, "_DPSGD_PATH", path)
    guard(**kwargs)


def _params_of(model, device=None):
    """The trainable LoRA parameters, ASSERTED to be on the device the node id claims.

    ``device`` is the parametrization's own string, and this is the ONE place that ties it to
    reality: everything below reads the device off the model, so without this assertion an
    ``[mps]`` leg whose ``_model(device=...)`` silently fell back to CPU would be a second CPU
    measurement wearing an mps id -- T-23-28. Default ``None`` keeps the Phase-22 call shape.
    """
    params = [p for name, p in model.named_parameters() if p.requires_grad and "lora_" in name]
    if device is not None:
        assert params and all(p.device.type == device for p in params), (
            f"the fixture's trainable parameters are on "
            f"{sorted({p.device.type for p in params})}, not {device!r}. This probe's node id "
            "claims a device it is not running on, which is exactly the repudiation D-02 forbids"
        )
    return params


def _seam_on(seam_cls, model, **kwargs):
    """Build ``seam_cls`` over ``model``, ASSERTING the seam really landed on the model's device.

    The device is READ off the model rather than passed, the same discipline ``_record`` uses, so
    no call site can pass it wrong. ``DPSGD.__init__`` allocates ``_accum`` with
    ``torch.zeros_like(p)`` and derives its generator device from ``params[0].device`` (D-14), so
    both are checked: a CPU generator drawing the noise for an "MPS" probe would make FAKE 3's and
    FAKE 4's device legs vacuous while still reporting green.
    """
    dp = seam_cls(model, **kwargs)
    device = next(p.device.type for p in model.parameters() if p.requires_grad)
    assert dp._g.device.type == device, (
        f"the seam's dedicated generator is on {dp._g.device!r} while the model is on {device!r}. "
        "FAKE 3's differential and FAKE 4's continuity check are both properties of the DRAWN "
        "values, so a CPU generator here would make this leg a CPU observation with an mps label"
    )
    assert all(buf.device.type == device for buf in dp._accum), (
        f"the seam's accumulator is on {sorted({b.device.type for b in dp._accum})}, not "
        f"{device!r} -- the lot sum this probe measures would not be the one the venue computes"
    )
    return dp


def _clear_grads(params):
    for p in params:
        p.grad = None


def _record(params, seed):
    """One record's gradients, written the way ``backward()`` writes them: **ACCUMULATING**.

    This is ``tests/test_phase22_dpsgd.py::_hand_set_grads`` with the ONE difference that carries
    FAKE 1's whole meaning: ``backward()`` does ``p.grad += g``, not ``p.grad = g``. A helper that
    overwrites cannot express the fake at all, because the fake IS the second backward landing on
    top of the first.

    **THE DRAW STAYS ON CPU AND ONLY THE TENSOR MOVES**, and that is load-bearing rather than
    stylistic (23-RESEARCH.md Pitfall 4). Two of the constants this helper feeds are FITTED:
    ``_FAKE1_LEAK_RATIO = 1.734481`` (band ``0.02``) and ``_FAKE3_STD_RATIO_AT_N4 = 3.999986``
    (band ``0.01``). A DEVICE-LOCAL generator here — one constructed against ``p.device`` instead
    of the bare CPU one below — would draw **different gradient values** on MPS and put both
    constants at risk for a reason that has nothing to do with the fake, and the resulting RED
    would read as a FAKE DETECTION, which is the worst possible disguise for a device artefact.
    Keeping the CPU draw and moving the result with ``.to()`` makes the bytes identical to the CPU
    run, so both constants stay valid **by construction**.

    There is no ``device`` parameter: it is read off ``p.device``, so no call site changes and
    there is nothing for a caller to pass wrong. The assertion below is the tripwire for a future
    edit that reintroduces a device-local generator — it must fail HERE, not two files away inside
    a fitted band.
    """
    gen = torch.Generator().manual_seed(seed)
    drawn = []
    for p in params:
        g = torch.randn(p.shape, generator=gen) * _GRAD_SCALE  # CPU. Deliberately.
        g_dev = g.to(p.device)
        p.grad = g_dev if p.grad is None else p.grad + g_dev
        assert g_dev.device == p.device == p.grad.device, (
            f"_record produced a gradient on {g_dev.device} for a parameter on {p.device}. The "
            "draw must stay on CPU and the TENSOR must move; a device-local generator would draw "
            "different values and move _FAKE1_LEAK_RATIO / _FAKE3_STD_RATIO_AT_N4 for a reason "
            "that has nothing to do with either fake"
        )
        drawn.append(g_dev)
    return drawn


# -------------------------------------------------------------------------------------------------
# THE PREMISE BOTH FITTED CONSTANTS REST ON, MEASURED ON THE VENUE RATHER THAN INHERITED (23-06).
#
# 23-RESEARCH.md §R1.3 records `_global_norm` over a 72-tensor LoRA-shaped fixture as
# **BIT-IDENTICAL** across cpu and mps at `0.4707888662815094`. **THAT VALUE IS NOT THIS FILE'S
# FIXTURE AND THE BIT-IDENTITY DOES NOT HOLD HERE.** Measured on the fixture the two fitted
# constants ACTUALLY rest on -- `_record(_params_of(_model(device=...)), 1)`, 72 tensors -- the two
# devices DIVERGE in the last float32 ULP:
#
#     cpu 0.5771376490592957    mps 0.5771377086639404    relative 1.033e-07
#
# Recorded as a finding rather than smoothed: fp32 reductions differ by REDUCTION ORDER, and
# `_global_norm` is a reduction of reductions (`vector_norm` per tensor, then `vector_norm` over the
# stack). The draw itself is byte-identical -- `_record` keeps the CPU generator and moves only the
# tensor -- so this is the whole of the cross-device numeric divergence in FAKE 1 and FAKE 2, and
# the assertion below BOUNDS it instead of leaving it as those probes' unstated premise.
# -------------------------------------------------------------------------------------------------
_GLOBAL_NORM_ON_CPU = 0.5771376490592957
_GLOBAL_NORM_ON_MPS = 0.5771377086639404

# One float32 ULP at this magnitude is ~1.19e-07, so the measured 1.033e-07 divergence is a single
# rounding step. The bound is set an order of magnitude above it and is still 2,500x INSIDE the
# tighter of the two bands it protects -- the non-vacuity is asserted, not asserted-by-comment.
_CROSS_DEVICE_NORM_REL_BOUND = 1e-6
_CROSS_DEVICE_BOUND_REQUIRED_HEADROOM = 100.0


@_MPS_SKIP
def test_global_norm_across_devices_diverges_far_below_the_fitted_bands():
    """``_global_norm`` on cpu vs mps: NOT bit-identical, and bounded ORDERS below both bands.

    **THE HONEST BOUND, stated first: this is ONE FIXTURE, NOT A PROOF.** Fp32 reductions can
    differ in the last ULPs by reduction order, and reduction order is a backend's choice -- a
    torch release, a different tensor count or a different magnitude distribution could move it.
    What makes the result usable anyway is the RATIO of scales rather than the measurement itself:
    the divergence measured here is ``1.03e-07`` relative, while the two probes that depend on
    float agreement across devices carry relative bands of ``1.15e-02`` (FAKE 1) and ``2.50e-03``
    (FAKE 3) -- four orders of magnitude of headroom. The assertion below therefore checks BOTH
    halves, because either alone would be misleading: that the divergence is inside a named bound,
    AND that the named bound is far inside the bands whose validity it is being used to argue for.

    This test exists because 23-RESEARCH.md's bit-identity row was carried into the plan as an
    assumption to re-assert. It does not hold on this file's fixture, and a probe that asserted
    ``torch.equal`` here would have gone RED -- correctly. The measured divergence is published in
    its place; the two fitted constants are byte-unchanged because the measurement supports them,
    not because the check was relaxed to fit.
    """
    norms = {}
    for device in ("cpu", "mps"):
        model = _model(device=device)
        params = _params_of(model, device)
        _clear_grads(params)
        drawn = _record(params, 1)
        assert len(drawn) == 72, f"the fixture is {len(drawn)} tensors, not the recorded 72"
        # THE MECHANISM'S OWN reduction, off a real seam on the real device -- not a re-spelling.
        seam = _seam_on(DPSGD, model, sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=101)
        norms[device] = seam._global_norm(drawn)
        _clear_grads(params)

    relative = abs(norms["mps"] - norms["cpu"]) / abs(norms["cpu"])
    assert relative <= _CROSS_DEVICE_NORM_REL_BOUND, (
        f"_global_norm diverges by {relative:.3e} relative between cpu ({norms['cpu']!r}) and mps "
        f"({norms['mps']!r}), above the recorded bound {_CROSS_DEVICE_NORM_REL_BOUND:.1e}. FAKE 1 "
        "and FAKE 3 both assert fitted constants across both devices; re-measure and RE-RECORD "
        "both readings with the device named on each -- 23-RESEARCH.md A1 forbids widening a band "
        "to absorb this"
    )
    for device, recorded in (("cpu", _GLOBAL_NORM_ON_CPU), ("mps", _GLOBAL_NORM_ON_MPS)):
        assert abs(norms[device] - recorded) / abs(recorded) <= _CROSS_DEVICE_NORM_REL_BOUND, (
            f"the {device} reduction is {norms[device]!r}, not the recorded {recorded!r}. The "
            "fixture itself has moved, so the cross-device comparison above is between two "
            "quantities neither of which is the one this file's constants were fitted to"
        )

    # NON-VACUITY: the bound is only evidence for the two constants while it is far inside them.
    tightest = min(
        _FAKE1_LEAK_BAND / _FAKE1_LEAK_RATIO, _FAKE3_STD_RATIO_BAND / _FAKE3_STD_RATIO_AT_N4
    )
    assert _CROSS_DEVICE_NORM_REL_BOUND * _CROSS_DEVICE_BOUND_REQUIRED_HEADROOM <= tightest, (
        f"the cross-device bound {_CROSS_DEVICE_NORM_REL_BOUND:.1e} is within "
        f"{_CROSS_DEVICE_BOUND_REQUIRED_HEADROOM}x of the tightest fitted relative band "
        f"{tightest:.3e}, so it no longer shows that the device divergence CANNOT reach either "
        "band. A bound that large is a warning about the constants, not a reassurance about them"
    )


# =================================================================================================
# FAKE 1 (V-18) -- clip the AVERAGED gradient, reached by dropping the per-micro-step drain.
# =================================================================================================


class _DrainDropped(DPSGD):
    """FAKE 1: ``absorb_record`` no longer drains ``.grad``, and the bookkeeping goes with it.

    This is the two-line source deletion applied to an OBJECT: the real clip, the real sensitivity
    check and the real accumulate all run, and then the state the drain would have left is undone
    -- ``.grad`` still holds this record and ``_drained`` is false, which is exactly what deleting
    ``for p in self._params: p.grad = None`` and ``self._drained = True`` leaves behind.
    """

    def absorb_record(self):
        held = [p.grad for p in self._params]
        super().absorb_record()
        for p, g in zip(self._params, held):
            p.grad = g
        self._drained = False


class _DrainDroppedAndUnguarded(_DrainDropped):
    """FAKE 1 with D-16 invariant 1 ALSO defeated -- the only way to observe the consequence.

    The guard is what stands between the fake and the leak, so measuring the leak requires
    defeating the guard as well. That ordering is the point of the probe: (a) drop the drain and
    the guard refuses; (b) drop the drain AND the guard, and the true per-record sensitivity really
    does exceed ``C``.
    """

    def absorb_record(self):
        super().absorb_record()
        self._drained = True


# Measured on this fixture (see the test docstring for the derivation): the honest mechanism's
# add/remove-one sensitivity is EXACTLY C, and the drain-dropped one's is C*sqrt(3).
_FAKE1_HONEST_RATIO_MAX = 1.0 + 1e-6
_FAKE1_LEAK_RATIO = 1.734481
_FAKE1_LEAK_BAND = 0.02


def _lot_sum(seam_cls, model, params, *, clip_norm, record_seeds):
    """The clipped SUM a lot releases, under ``seam_cls``. Returns ``(buffers, seam)``."""
    _clear_grads(params)
    dp = _seam_on(seam_cls, model, sigma=0.0, clip_norm=clip_norm, seed=101)
    dp.begin_step()
    for seed in record_seeds:
        _record(params, seed)
        dp.absorb_record()
    buffers = [buf.clone() for buf in dp._accum]
    _clear_grads(params)
    return buffers, dp


@pytest.mark.parametrize("device", _DEVICES)
def test_fake_averaged_gradient(device, tmp_path):
    """V-18 / FAKE 1: drop the drain, watch D-16 invariant 1 refuse, and MEASURE what it prevents.

    **The refusal.** ``backward()`` ACCUMULATES, so without the per-micro-step drain record *i*'s
    clip sees records 1..*i* summed. ``_drained`` is cleared before anything is read and set again
    only by the drain loop, so a mechanism that stops draining refuses the NEXT record with
    ``[dp-invariant:drain]`` rather than silently clipping a running sum.

    **The consequence, because a refusal alone does not show what it is protecting.** The quantity
    the accountant is told is the add/remove-one sensitivity (D-18): the L2 distance between the
    sums released by the lot ``{r1, r2}`` and by its neighbour ``{r2}``. Measured on this fixture,
    with a clip that BINDS on every record:

      * honest mechanism -- ``||clip(g1)|| = C`` exactly, ratio ``1.000000``
      * drain dropped ---- ``||clip(g1) + clip(g1+g2) - clip(g2)||``, ratio ``1.734481``

    The second figure has a closed form. With ``g1``, ``g2`` independent and both over ``C``, every
    clipped term has norm exactly ``C`` and ``clip(g1+g2)`` points along ``(g1+g2)/sqrt(2)``, so the
    difference is ``C*sqrt(3) = 1.7320508 C``; the measured ``1.734481`` is that value plus the
    fixture's departure from exact orthogonality and equal norms. **The plan's stated consequence --
    "the accumulated norm after two records exceeds C" -- does NOT discriminate**: the honest
    accumulator holds the SUM, so its norm legitimately reaches ``N*C``. The neighbouring-lot
    difference is the quantity that separates the two, and it is what is asserted.

    **ON MPS (23-06 / D-02), and the expectation is stated BEFORE the measurement.** ``_record``
    keeps its CPU draw and moves only the tensor, so the gradients entering this probe are
    byte-identical on both devices and the EXPECTATION was bit-identity. **MEASURED: it is not
    bit-identical.** cpu ``1.7344813665273022`` against mps ``1.734481393949083``, a difference of
    ``2.74e-08`` (relative ``1.6e-08``). The draw is identical; the fp32 REDUCTION inside
    ``_global_norm`` is not, and every ratio here is a quotient of two such reductions. The
    divergence is ~5 orders of magnitude inside the ``0.02`` band, and
    ``test_global_norm_across_devices_diverges_far_below_the_fitted_bands`` measures that
    divergence directly instead of leaving it as this probe's unstated premise.
    """
    model = _model(device=device)
    params = _params_of(model, device)
    honest = _seam_on(DPSGD, model, sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=101)

    _clear_grads(params)
    g1 = _record(params, 1)
    record_norm = honest._global_norm(g1)
    _clear_grads(params)
    # A clip that BINDS on every record: the closed form above needs every clipped term at norm C.
    clip_norm = record_norm / 2.0

    # ---- The refusal, watched. --------------------------------------------------------------
    _clear_grads(params)
    fake = _seam_on(_DrainDropped, model, sigma=0.0, clip_norm=clip_norm, seed=101)
    fake.begin_step()
    _record(params, 1)
    fake.absorb_record()
    # POSITIVE CONTROL for the fake itself: the drain really did NOT happen, so the refusal below
    # is about the dropped drain and not about a gradient that was never written.
    assert all(p.grad is not None for p in params), (
        "the drain-dropped fixture left .grad = None, so it is not expressing FAKE 1 at all"
    )
    _record(params, 2)  # the second backward lands ON TOP of the first -- the fake's whole shape
    with pytest.raises(RuntimeError, match=r"dp-invariant:drain"):
        fake.absorb_record()
    _clear_grads(params)

    # ---- The UNMUTATED control: the real mechanism completes over the same two records. ------
    real_sums, real = _lot_sum(DPSGD, model, params, clip_norm=clip_norm, record_seeds=(1, 2))
    assert real._records == 2, "the unmutated control did not absorb both records"
    assert real._clip_bind_count == 2, (
        f"the clip bound on {real._clip_bind_count} of 2 records -- the closed form below needs "
        "every clipped term to sit exactly on C, so a non-binding clip makes the ratios meaningless"
    )

    # ---- The consequence: the add/remove-one sensitivity, honest vs fake. --------------------
    real_neighbour, _ = _lot_sum(DPSGD, model, params, clip_norm=clip_norm, record_seeds=(2,))
    fake_sums, _ = _lot_sum(
        _DrainDroppedAndUnguarded, model, params, clip_norm=clip_norm, record_seeds=(1, 2)
    )
    fake_neighbour, _ = _lot_sum(
        _DrainDroppedAndUnguarded, model, params, clip_norm=clip_norm, record_seeds=(2,)
    )

    honest_ratio = real._global_norm([a - b for a, b in zip(real_sums, real_neighbour)]) / clip_norm
    fake_ratio = real._global_norm([a - b for a, b in zip(fake_sums, fake_neighbour)]) / clip_norm

    assert honest_ratio <= _FAKE1_HONEST_RATIO_MAX, (
        f"the HONEST mechanism's add/remove-one sensitivity is {honest_ratio!r} * C -- above the "
        "bound the accountant is told. This is the control; if it fails, the fake's ratio below "
        "proves nothing"
    )
    assert abs(fake_ratio - _FAKE1_LEAK_RATIO) <= _FAKE1_LEAK_BAND, (
        f"the drain-dropped mechanism's add/remove-one sensitivity is {fake_ratio!r} * C, not the "
        f"measured {_FAKE1_LEAK_RATIO} * C (= C*sqrt(3) up to the fixture's departure from exact "
        "orthogonality). The consequence FAKE 1 causes has moved, so the guard's value is no "
        "longer the value recorded here"
    )
    assert fake_ratio > honest_ratio, (
        "the drain-dropped mechanism leaked no more than the honest one on this fixture, so this "
        "probe watched a refusal without ever exhibiting what it refuses"
    )

    # ---- The mutated MODULE's own RED is in the SUMMARY; this is its structural stand-in. ----
    # Deleting the drain lines from the source leaves `_drained` false, which is the same state
    # the subclass above reconstructs. Asserted here so the two halves are provably about one edit.
    # SOURCE TEXT -> `_AST_HALF_RUNS_ON` only: re-reading the same bytes under an `[mps]` id would
    # claim a device pass it did not perform.
    if device == _AST_HALF_RUNS_ON:
        source = _real_source()
        assert source.count("p.grad = None  # D-01's per-micro-step drain") == 1, (
            "the drain line the SUMMARY's FAKE 1 hunk deletes is no longer where it was; the "
            "mutated-module capture and this in-process probe would then be about two different "
            "edits"
        )
    assert tmp_path.exists()  # the fixture is requested for symmetry with the AST probes


# =================================================================================================
# FAKE 2 (V-19) -- noise scaled to the WRONG SENSITIVITY, reached by a second clip constant.
# =================================================================================================


class _ClipsToASecondConstant(DPSGD):
    """FAKE 2: the clip decision reads a bound of ``2C`` while the sensitivity check reads ``C``.

    Expressed by halving the PRE-clip norm the clip decision sees, which is arithmetically
    identical to clipping against a second constant ``_c2 = 2C``: ``coef = C / (norm/2)`` scales
    the record to a norm of exactly ``2C``. The post-clip re-computed norm and the comparison
    against ``self.C * (1 + tol)`` are left completely honest, so the refusal below is the real
    guard on real numbers.
    """

    def _global_norm(self, tensors):
        real = super()._global_norm(tensors)
        self._norm_calls = getattr(self, "_norm_calls", 0) + 1
        return real / 2.0 if self._norm_calls % 2 == 1 else real


class _ClipsToAHalfConstant(DPSGD):
    """FAKE 2 in the OTHER direction: a second constant of ``C/2``, which the runtime check misses.

    Same shape as the class above with the factor inverted, so the record is scaled to a norm of
    ``C/2``. This is the evidence for the one-sidedness stated in the test docstring: it is a
    genuine second clip constant, the AST guard catches it, and ``norm <= C * (1 + tol)`` cannot.
    """

    def _global_norm(self, tensors):
        real = super()._global_norm(tensors)
        self._norm_calls = getattr(self, "_norm_calls", 0) + 1
        return real * 2.0 if self._norm_calls % 2 == 1 else real


@pytest.mark.parametrize("device", _DEVICES)
def test_fake_wrong_sensitivity(device, monkeypatch, tmp_path):
    """V-19 / FAKE 2: a second clip constant, watched reddening the AST guard AND the runtime check.

    **Both halves are required and NEITHER is redundant, because the runtime check is ONE-SIDED.**
    ``[dp-invariant:sensitivity]`` refuses a clipped norm ABOVE ``C * (1 + tol)``. That is the
    dangerous direction -- clip to ``2C`` while telling the accountant ``C`` and every published
    epsilon is optimistic by that ratio. It is structurally blind to a second constant SMALLER than
    ``C``: clipping to ``C/2`` releases half the signal the accountant paid noise for, which is
    wasteful rather than unsafe, and ``C/2 <= C * (1 + tol)`` holds. Measured below, not argued:
    ``_ClipsToAHalfConstant`` completes with no refusal at all. The AST guard catches BOTH
    directions because it never looks at a number -- it asserts the clip-bearing attribute set is
    exactly ``{"C"}``.

    Measured on this fixture: ``C = 0.1442844122648239`` (a quarter of the record's norm, so the
    clip binds), the honest accumulated norm is ``C`` exactly, and the fake's clipped norm is
    ``0.2885688245296478`` -- exactly ``2C`` -- which the refusal message quotes.

    **ON MPS (23-06 / D-02): the lowest-risk of the four, and measured rather than assumed.** No
    generator is involved (``sigma = 0`` throughout) and both assertions are RATIOS of quantities
    that scale together, so both come back EXACTLY ``0.0`` deviation on MPS as on CPU. The absolute
    numbers do move with the device's fp32 reduction order -- ``C`` is ``0.1442844122648239`` on cpu
    against ``0.1442844271659851`` on mps, and the fake's clipped norm ``0.2885688245296478``
    against ``0.2885688543319702`` -- which is precisely why the assertions are written as ratios
    and why the docstring's literals are labelled with the device that produced them.
    """
    real_source = _real_source()

    # ---- AST half, over the LIVE guard: a second constant introduced as a source mutation. ---
    # `_AST_HALF_RUNS_ON` ONLY -- `ast.parse` over source text has no device (see the constant).
    if device == _AST_HALF_RUNS_ON:
        mutated = _mutate(
            real_source,
            "        self.C = float(clip_norm)  # SINGLE source of truth -- the clip AND the noise "
            "read this.",
            "        self.C = float(clip_norm)  # SINGLE source of truth -- the clip AND the noise "
            "read this.\n        self._c2 = 2.0 * self.C  # FAKE 2's positive insertion.",
        )
        mutated = _mutate(
            mutated, "            coef = self.C / norm", "            coef = self._c2 / norm"
        )

        with pytest.raises(AssertionError, match=r"clip constants"):
            _run_live_guard(
                monkeypatch,
                tmp_path,
                mutated,
                ast_guards.test_dpsgd_has_exactly_one_clip_constant,
            )

        # UNMUTATED CONTROL, through the identical harness: the same guard over the same temp-copy
        # mechanism passes, so the AssertionError above is the mutation and not the repointing.
        _run_live_guard(
            monkeypatch, tmp_path, real_source, ast_guards.test_dpsgd_has_exactly_one_clip_constant
        )

    # ---- Runtime half: the dangerous direction, refused. -------------------------------------
    model = _model(device=device)
    params = _params_of(model, device)
    honest = _seam_on(DPSGD, model, sigma=0.0, clip_norm=_NON_BINDING_CLIP, seed=5)
    _clear_grads(params)
    record_norm = honest._global_norm(_record(params, 1))
    _clear_grads(params)
    clip_norm = record_norm / 4.0  # the fake's 2C bound still binds, so the fake really clips

    control = _seam_on(DPSGD, model, sigma=0.0, clip_norm=clip_norm, seed=5)
    control.begin_step()
    _record(params, 1)
    control.absorb_record()
    accumulated = control._global_norm(control._accum)
    assert control._clip_bind_count == 1, "the honest control's clip did not bind -- nothing to see"
    assert abs(accumulated / clip_norm - 1.0) <= 1e-5, (
        f"the honest accumulated norm is {accumulated!r}, not C = {clip_norm!r}. The fake's 2C "
        "below is only attributable against a control that sits exactly on the bound"
    )
    _clear_grads(params)

    fake = _seam_on(_ClipsToASecondConstant, model, sigma=0.0, clip_norm=clip_norm, seed=5)
    fake.begin_step()
    _record(params, 1)
    with pytest.raises(RuntimeError, match=r"dp-invariant:sensitivity"):
        fake.absorb_record()
    assert fake._clip_bind_count == 1, (
        "the fake's clip never bound, so the RuntimeError may be the honest path refusing rather "
        "than the invariant catching a clip against a second, larger constant"
    )
    _clear_grads(params)

    # ---- Runtime half, the OTHER direction: measured GREEN. That is the one-sidedness. -------
    lenient = _seam_on(_ClipsToAHalfConstant, model, sigma=0.0, clip_norm=clip_norm, seed=5)
    lenient.begin_step()
    _record(params, 1)
    lenient.absorb_record()  # NO refusal -- this is the documented limitation, measured
    lenient_norm = DPSGD._global_norm(lenient, lenient._accum)
    assert abs(lenient_norm / (clip_norm / 2.0) - 1.0) <= 1e-5, (
        f"the lenient fake released a norm of {lenient_norm!r}, not C/2 = {clip_norm / 2.0!r} -- "
        "the one-sidedness demonstration is not exercising a second constant at all"
    )
    _clear_grads(params)

    # ... and the AST guard, which never looks at a number, catches that direction too.
    # `_AST_HALF_RUNS_ON` ONLY, for the same reason as the half above.
    if device == _AST_HALF_RUNS_ON:
        smaller = _mutate(
            real_source,
            "        self.C = float(clip_norm)  # SINGLE source of truth -- the clip AND the noise "
            "read this.",
            "        self.C = float(clip_norm)  # SINGLE source of truth -- the clip AND the noise "
            "read this.\n        self._c2 = 0.5 * self.C  # FAKE 2, the direction runtime cannot "
            "see.",
        )
        smaller = _mutate(
            smaller, "            coef = self.C / norm", "            coef = self._c2 / norm"
        )
        with pytest.raises(AssertionError, match=r"clip constants"):
            _run_live_guard(
                monkeypatch, tmp_path, smaller, ast_guards.test_dpsgd_has_exactly_one_clip_constant
            )


# =================================================================================================
# FAKE 3 (V-20) -- noise added AFTER averaging, i.e. `divide -> noise`.
#
# D-17's table assigns this fake to D-06's sigma-of-zero identity. THAT ROW IS FALSE and 22-06
# measured it; the table below is the corrected coverage, re-measured here.
# =================================================================================================


class _DivideBeforeNoise(DPSGD):
    """FAKE 3: the ``/N`` moved AHEAD of the draw, so the noise is added at full ``sigma * C``.

    ``finalize``'s two mandated statements are re-spelled with the divide hoisted and the lot
    refusal skipped -- which is precisely the source mutation, since a mutated module would divide
    inside ``_noised_private`` and still be handed the real lot size.
    """

    def finalize(self, accum):
        lot = int(accum)
        for buf in self._accum:
            buf.div_(lot)
        self._write_once(self._noised_private(1))


# The measured coverage table. `True` means the fixed-generator differential SEES the mutation.
# Both `False` rows are GENUINE BLIND SPOTS with structural causes, not fixture accidents:
#   * sigma = 0 -- `torch.normal(std=0.0)` returns EXACT zeros, so `(S + 0)/N` and `(S/N) + 0` are
#     the same bytes at every N. This is the row D-17 credits with detecting FAKE 3.
#   * accum = 1 -- `x / 1` is exact, so the divide's position is unobservable at every sigma.
# The statement-order structural detector covers all four cells and is asserted in every one.
_FAKE3_DIFFERENTIAL_SEES = {
    (0.0, 1): False,
    (0.0, 4): False,
    (1.0, 1): False,
    (1.0, 4): True,
}

# Measured at sigma = 1.0, C = 1.0, N = 4 over all 331,776 released elements: the honest release
# has std 0.2501736283302307 and the fake's 1.0006910562515259 -- a ratio of 3.999986, i.e. N.
#
# RE-MEASURED ON MPS (23-06 / D-02) and the constant is BYTE-UNCHANGED, because the MPS reading
# lands INSIDE the recorded band:
#     cpu 3.9999861813196698   mps 3.9999995238454056   |delta| = 1.334e-05   band 0.01
# This is the single numeric constant most worth watching on this venue: unlike FAKE 1's, FAKE 3's
# differential is a property of the DRAWN values, and on MPS those come off an MPS generator, so
# the noise vectors are genuinely different numbers -- not the same numbers reduced differently.
# The ratio survives because it is STRUCTURAL (it is N, not a fit), which is what research §R1.4
# predicted and this measurement confirms. The band was NOT widened and could not have been:
# 23-RESEARCH.md Assumption A1 committed the disposition -- re-record BOTH readings, never widen --
# before the number was seen.
_FAKE3_STD_RATIO_AT_N4 = 3.999986
_FAKE3_STD_RATIO_BAND = 0.01
_FAKE3_STD_RATIO_AT_N4_ON_MPS = 3.9999995238454056


def _released(seam_cls, model, params, *, sigma, n_records):
    """Run one lot to completion under ``seam_cls`` and return the released ``.grad`` tensors.

    Both seams are constructed with the SAME seed and absorb the SAME records, and
    ``absorb_record`` consumes no generator state, so the two runs draw from an identical generator
    state and the ONLY difference between them is where the divide happens.
    """
    _clear_grads(params)
    dp = _seam_on(seam_cls, model, sigma=sigma, clip_norm=_CLIP, seed=61)
    dp.begin_step()
    for k in range(n_records):
        _record(params, 200 + k)
        dp.absorb_record()
    dp.finalize(n_records)
    released = [p.grad.clone() for p in params]
    _clear_grads(params)
    return released


# -------------------------------------------------------------------------------------------------
# D-02's DEVICE-PARAMETRIZATION EXEMPTION, WRITTEN DOWN RATHER THAN SILENTLY SKIPPED.
#
# Two Phase-22 files are exempt from the CPU->MPS parametrization surface, and the exemption is
# recorded HERE, in source, because *a probe that claims a device pass it did not perform is the
# very defect D-02 exists to prevent*. An exemption inferred from an absence is indistinguishable
# from an oversight.
#
#   * `tests/test_phase22_dpsgd_ast.py` -- 16 tests, pure `ast.parse` over source TEXT. It imports
#     no torch runtime at all, so there is no tensor, no generator and no device for a result to
#     depend on. Re-running it under `device="mps"` executes byte-identical code.
#   * `tests/test_phase22_accountant.py` -- 37 tests, stdlib `math` only. Same argument.
#
# MEASURED: 16 + 37 = **53 of the 113 Phase-22 tests** (`grep -c '^def test_'` across
# accountant 37 / checkpoint 9 / dpsgd_ast 16 / dpsgd 23 / fakes 8 / wiring 20), so the exemption
# removes just under half the surface and is worth stating precisely rather than waving at.
# The four fakes' AST halves in THIS file inherit the same exemption for the same reason; their
# RUNTIME halves do not, and 23-06 performs the watched RED for those on MPS.
# -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(("sigma", "n_records"), sorted(_FAKE3_DIFFERENTIAL_SEES))
@pytest.mark.parametrize("device", _DEVICES)
def test_fake_noise_after_averaging(device, sigma, n_records):
    """V-20 / FAKE 3, with its two BLIND SPOTS measured rather than glossed.

    **D-17's assigned detector does not work and this asserts why.** The table says *"build
    divide -> noise; watch D-06's CPU sigma-of-zero identity break"*. At ``sigma = 0`` the drawn
    values are EXACTLY zero, so ``(S + 0)/N`` and ``(S/N) + 0`` are the same bytes: both
    ``sigma = 0`` rows below assert the mutated release is ``torch.equal`` to the honest one. That
    is not a detection failing to fire -- it is a detection that cannot exist at that input.

    **The second blind spot is the lot size.** At ``accum = 1`` the divide is a no-op at every
    sigma, so the ``(1.0, 1)`` row is ``torch.equal`` too. This is the same shape as 22-06's
    measurement that D-02's inherited-divide fake is invisible at ``grad_accum_steps = 1``, and it
    is why 22-10 wired the production arms at ``accum = n_facts`` (8 and 64).

    **What does work, in one cell each.** (i) The fixed-generator magnitude differential, at
    ``sigma > 0`` AND ``accum > 1``: released std ``0.2501736283302307`` honest against
    ``1.0006910562515259`` mutated, a ratio of ``3.999986`` -- a factor of N. (ii) The
    statement-order structural check, which reads text and therefore covers ALL FOUR cells,
    including the three the differential cannot see. It is asserted in every parametrization
    the source half runs in (``_AST_HALF_RUNS_ON``).

    **ON MPS (23-06 / D-02).** All three recorded BLIND SPOTS transfer -- ``(0.0, 1)``, ``(0.0, 4)``
    and ``(1.0, 1)`` come back ``torch.equal`` on MPS exactly as on CPU, which matters because a
    blind spot that quietly stopped being blind would be a finding, not a pass. The one live cell's
    ratio is ``3.9999995238454056`` on mps against ``3.9999861813196698`` on cpu -- a delta of
    ``1.334e-05`` against a band of ``0.01``, so the constant is byte-unchanged. The MPS reading is
    the CLOSER of the two to the structural value ``N = 4``.
    """
    model = _model(device=device)
    params = _params_of(model, device)

    honest = _released(DPSGD, model, params, sigma=sigma, n_records=n_records)
    fake = _released(_DivideBeforeNoise, model, params, sigma=sigma, n_records=n_records)
    assert honest[0].numel() and sum(t.numel() for t in honest) == _FROZEN_PARAMS

    identical = all(torch.equal(a, b) for a, b in zip(honest, fake))
    expected_to_see = _FAKE3_DIFFERENTIAL_SEES[(sigma, n_records)]

    if expected_to_see:
        assert not identical, (
            f"at sigma = {sigma}, N = {n_records} the divide-before-noise mutation released "
            "BYTE-IDENTICAL values to the honest mechanism. This is the one cell where the "
            "runtime differential is supposed to bite; if it does not, FAKE 3 has no runtime "
            "detector at all"
        )
        ratio = float(torch.cat([t.flatten() for t in fake]).std()) / float(
            torch.cat([t.flatten() for t in honest]).std()
        )
        assert abs(ratio - _FAKE3_STD_RATIO_AT_N4) <= _FAKE3_STD_RATIO_BAND, (
            f"the mutated release's std is {ratio:.6f}x the honest one, not the measured "
            f"{_FAKE3_STD_RATIO_AT_N4} (= N). D-02 puts the /N LAST; dividing first leaves the "
            "noise N times too large for the sensitivity the accountant was told"
        )
    else:
        assert identical, (
            f"at sigma = {sigma}, N = {n_records} the differential DID separate the mutation, "
            "which contradicts the recorded blind spot. That is a finding, not a pass: re-measure "
            "_FAKE3_DIFFERENTIAL_SEES rather than widening it"
        )

    # THE DETECTOR THAT COVERS THIS CELL WHATEVER THE DIFFERENTIAL DID -- statement order, over
    # text, through the same function `test_dpsgd_draws_the_noise_before_it_divides` runs live.
    # `_AST_HALF_RUNS_ON` ONLY: it is a pure source-text property (see the constant).
    if device != _AST_HALF_RUNS_ON:
        return
    real_source = _real_source()
    ast_guards._assert_noise_precedes_divide(real_source, class_name="DPSGD")  # GREEN control

    swapped = _mutate(
        real_source,
        "        pre = self._g.get_state()",
        "        averaged = [buf / accum for buf in self._accum]  # FAKE 3: the divide, hoisted.\n"
        "        pre = self._g.get_state()",
    )
    swapped = _mutate(
        swapped,
        "        return [(buf + drawn) / accum for buf, drawn in zip(self._accum, noise)]",
        "        return [avg + drawn for avg, drawn in zip(averaged, noise)]",
    )
    with pytest.raises(AssertionError, match=r"draws the noise at statement"):
        ast_guards._assert_noise_precedes_divide(swapped, class_name="DPSGD")


# =================================================================================================
# FAKE 4 (V-21) -- the RNG REUSED across steps, reached by an in-step `manual_seed`.
# =================================================================================================

_FAKE4_SEED = 4242


class _ReseedsInStep(DPSGD):
    """FAKE 4: ``self._g.manual_seed(...)`` at the top of ``finalize``."""

    def finalize(self, accum):
        self._g.manual_seed(_FAKE4_SEED)
        return super().finalize(accum)


class _ReseedsInStepUnguarded(_ReseedsInStep):
    """FAKE 4 with D-16 invariant 4 ALSO defeated, so the consequence is observable.

    ``_prev_gen_state = None`` is exactly the state the continuity check treats as "first step",
    so this releases the same noise on every step with no refusal at all.
    """

    def finalize(self, accum):
        self._prev_gen_state = None
        return super().finalize(accum)


def _two_steps(seam_cls, model, params):
    """Two optimizer steps over IDENTICAL record gradients, returning both released lots."""
    _clear_grads(params)
    dp = _seam_on(seam_cls, model, sigma=_SIGMA, clip_norm=_NON_BINDING_CLIP, seed=13)
    lots = []
    for _ in range(2):
        dp.begin_step()
        _record(params, 1)
        dp.absorb_record()
        dp.finalize(1)
        lots.append([p.grad.clone() for p in params])
        _clear_grads(params)
    assert dp._clip_bind_count == 0, "the non-binding clip bound -- the lots differ for two reasons"
    return lots


@pytest.mark.parametrize("device", _DEVICES)
def test_fake_rng_reuse(device, monkeypatch, tmp_path):
    """V-21 / FAKE 4: an in-step ``manual_seed``, watched reddening the AST guards AND invariant 4.

    **AST half.** The re-seed is inserted into ``finalize`` as a source mutation and fed to the two
    live guards through their own ``_DPSGD_PATH``: ``test_dpsgd_never_reseeds_its_generator`` (the
    hard-equality ``_ALLOWED_RESEED_SITES`` walk) and ``test_dpsgd_step_reaches_no_forbidden_call``
    at ``entry="finalize"`` (the closure walk, whose forbidden set D-17 widened to include
    ``manual_seed`` for exactly this fake). Both are asserted to raise, and both are asserted to
    PASS over the unmutated copy through the identical harness.

    **Runtime half, and its consequence.** ``_prev_gen_state`` is ``None`` on step 1, so the
    continuity check is correctly silent there and step 2 is where FAKE 4 becomes observable: the
    pre-draw state equals the freshly seeded state and not the previous step's post-draw state, so
    ``[dp-invariant:generator]`` refuses. With the invariant defeated as well, the two steps'
    released gradients are ``torch.equal`` over all 331,776 elements from identical records --
    the same noise vector released twice, while the accountant charges for T INDEPENDENT
    compositions.

    **ON MPS (23-06 / D-02).** This is the probe that touches the generator most directly, and the
    5,056 B (cpu) / 44 B (mps) state divergence is exactly why it had to be re-watched rather than
    inherited: the continuity check is ``torch.equal(pre, post)`` over those states. Both halves
    transfer -- the honest seam's two steps still differ, the unguarded re-seeder still releases
    ``torch.equal`` lots, and ``[dp-invariant:generator]`` still refuses on step 2 -- and they
    transfer over the 44-byte MPS state, which is a different tensor shape entirely from the one
    Phase 22 watched. Both states are resident ON CPU whatever the generator's device, which is why
    ``dpsgd.py``'s ``torch.equal`` needs no device plumbing and none was added.
    """
    real_source = _real_source()
    # AST half -> `_AST_HALF_RUNS_ON` ONLY: these guards feed source TEXT to `ast.parse` and import
    # no torch runtime, so an `[mps]` re-run would execute byte-identical code (see the constant).
    if device == _AST_HALF_RUNS_ON:
        mutated = _mutate(
            real_source,
            "        lot = int(accum)",
            "        self._g.manual_seed(1234)  # FAKE 4's positive insertion.\n"
            "        lot = int(accum)",
        )

        with pytest.raises(AssertionError, match=r"seed/state call sites"):
            _run_live_guard(
                monkeypatch, tmp_path, mutated, ast_guards.test_dpsgd_never_reseeds_its_generator
            )
        with pytest.raises(AssertionError, match=r"'finalize': \['manual_seed'\]"):
            _run_live_guard(
                monkeypatch,
                tmp_path,
                mutated,
                ast_guards.test_dpsgd_step_reaches_no_forbidden_call,
                entry="finalize",
            )

        # UNMUTATED CONTROLS through the identical harness.
        _run_live_guard(
            monkeypatch, tmp_path, real_source, ast_guards.test_dpsgd_never_reseeds_its_generator
        )
        _run_live_guard(
            monkeypatch,
            tmp_path,
            real_source,
            ast_guards.test_dpsgd_step_reaches_no_forbidden_call,
            entry="finalize",
        )

    # ---- Runtime control: the honest mechanism's two steps DIFFER from identical records. ----
    model = _model(device=device)
    params = _params_of(model, device)
    first, second = _two_steps(DPSGD, model, params)
    assert not any(torch.equal(a, b) for a, b in zip(first, second)), (
        "the honest mechanism released identical gradients on two consecutive steps from "
        "identical records -- the control is already exhibiting FAKE 4 and the probe below "
        "would prove nothing"
    )

    # ---- The consequence: the same noise released twice, with the invariant defeated. --------
    leaked_first, leaked_second = _two_steps(_ReseedsInStepUnguarded, model, params)
    assert all(torch.equal(a, b) for a, b in zip(leaked_first, leaked_second)), (
        "the re-seeding mechanism did not actually reuse its noise, so the refusal below would be "
        "firing on something other than FAKE 4"
    )
    assert sum(t.numel() for t in leaked_first) == _FROZEN_PARAMS

    # ---- The refusal, watched: invariant 4 bites on step 2. ----------------------------------
    _clear_grads(params)
    dp = _seam_on(_ReseedsInStep, model, sigma=_SIGMA, clip_norm=_NON_BINDING_CLIP, seed=13)
    dp.begin_step()
    _record(params, 1)
    dp.absorb_record()
    dp.finalize(1)  # step 1: `_prev_gen_state` is None, so continuity is correctly silent
    _clear_grads(params)
    dp.begin_step()
    _record(params, 1)
    dp.absorb_record()
    with pytest.raises(RuntimeError, match=r"dp-invariant:generator"):
        dp.finalize(1)
    _clear_grads(params)


# =================================================================================================
# The ledger locks. DPSGD-04's deliverable is the OBSERVED RED, and the observation over the REAL
# mutated MODULE lives in the SUMMARY -- so a SUMMARY that silently loses it must fail something.
# =================================================================================================

_LEDGER_FAKES = ("FAKE 1", "FAKE 2", "FAKE 3", "FAKE 4")

# The node ids OBSERVED reddening when each fake was applied to the REAL committed module, one
# entry per fake per distinct detector. These are the anchors the SUMMARY's ledger cites, and a
# ledger citing a guard that has been renamed or deleted is this repository's most recurring
# defect class -- seven stale anchors were measured across 22-02/22-03, and 22-09 recorded the
# frozen pin's own by-symbol citation resolving only because a test was named to match it.
_WATCHED_RED_NODE_IDS = {
    "FAKE 1": (
        "tests/test_phase22_dpsgd_ast.py::test_dpsgd_step_reaches_no_forbidden_call[absorb_record]",
        "tests/test_phase22_dpsgd.py::test_drain_invariant_fires",
    ),
    "FAKE 2": (
        "tests/test_phase22_dpsgd_ast.py::test_dpsgd_has_exactly_one_clip_constant",
        "tests/test_phase22_dpsgd.py::test_sensitivity_invariant_fires",
    ),
    "FAKE 3": (
        # `[4]` -> `[4-cpu]`, CORRECTED when 23-01 added the device axis to this test. The case is
        # UNCHANGED -- N = 4 on CPU is exactly what Phase 22 ran and watched redden; the device is
        # now spelled in the id rather than implied by the file being CPU-only. MEASURED: the old
        # `[4]` no longer collects ("no match in any of [<Module test_phase22_dpsgd.py>]"), which
        # is this repository's most recurring defect class -- a stale anchor -- and
        # `test_watched_red_node_ids_resolve` cannot catch it, because it deliberately does not
        # resolve the part inside `[...]`.
        "tests/test_phase22_dpsgd.py::"
        "test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST[4-cpu]",
        "tests/test_phase22_dpsgd_ast.py::test_dpsgd_draws_the_noise_before_it_divides",
    ),
    "FAKE 4": (
        "tests/test_phase22_dpsgd_ast.py::test_dpsgd_never_reseeds_its_generator",
        "tests/test_phase22_dpsgd_ast.py::test_dpsgd_step_reaches_no_forbidden_call[finalize]",
        "tests/test_phase22_dpsgd.py::test_generator_advances_and_is_never_reseeded",
    ),
}

# MEASURED, and recorded because a shared signature would be a coverage gap rather than a double
# win: the nine entries above produced NINE DISTINCT assertion messages over the real mutated
# module. The one near-collision is named rather than glossed --
# `test_dpsgd_step_reaches_no_forbidden_call` catches BOTH FAKE 1 and FAKE 4, but at two different
# parametrizations (`[absorb_record]` vs `[finalize]`) reporting two different offender dicts
# (`{}` where the drain's `.grad=` write vanished, against `{'finalize': ['manual_seed'], ...}`
# where the re-seed appeared). Same guard function, two node ids, two messages.
_DISTINCT_RED_SIGNATURES = 9


def test_every_fake_has_at_least_two_independent_detectors():
    """No fake rests on ONE guard, and the ledger's signature count is not a summed duplicate.

    A single detector per fake would make the whole DPSGD-04 claim one rename away from vacuous.
    Measured over the real mutated module: FAKE 1 and FAKE 2 have a structural AND a runtime
    detector each, FAKE 3 has the statement-order check AND the magnitude guard, and FAKE 4 has two
    structural detectors AND the runtime generator-continuity check.
    """
    assert set(_WATCHED_RED_NODE_IDS) == set(_LEDGER_FAKES), (
        f"the watched-RED register covers {sorted(_WATCHED_RED_NODE_IDS)}, not all four fakes "
        f"{list(_LEDGER_FAKES)}. DPSGD-04 is about FOUR silent-non-privacy failures"
    )
    for fake, node_ids in _WATCHED_RED_NODE_IDS.items():
        assert len(node_ids) >= 2, (
            f"{fake} has only {len(node_ids)} recorded detector(s): {node_ids}. One guard per fake "
            "makes the claim one rename away from vacuous"
        )
        assert len(set(node_ids)) == len(node_ids), f"{fake} lists a duplicate detector: {node_ids}"
    total = sum(len(ids) for ids in _WATCHED_RED_NODE_IDS.values())
    assert total == _DISTINCT_RED_SIGNATURES, (
        f"{total} detectors are registered against a recorded {_DISTINCT_RED_SIGNATURES} DISTINCT "
        "RED signatures. If two fakes ever trip the same guard with the same message that is a "
        "COVERAGE GAP to name, not a second win to count -- re-measure rather than re-type"
    )


def test_watched_red_node_ids_resolve():
    """Every node id the SUMMARY's ledger cites as having reddened still names a real test.

    The RED output in the ledger is only evidence while it is ATTRIBUTABLE. A renamed or deleted
    guard turns a verbatim capture into an unfalsifiable anecdote, and nothing else in the suite
    would notice -- the ledger is prose in a markdown file.

    The parameter id inside ``[...]`` is not resolved (that needs a collection pass); what is
    asserted is that the function exists, is callable, and carries a ``parametrize`` mark exactly
    when the cited id claims a parameter.
    """
    import importlib

    assert _WATCHED_RED_NODE_IDS, "no watched RED node ids recorded -- this guard checks nothing"
    for fake, node_ids in _WATCHED_RED_NODE_IDS.items():
        for node_id in node_ids:
            path, _, name = node_id.partition("::")
            parametrized = name.endswith("]")
            if parametrized:
                name = name[: name.index("[")]
            module = importlib.import_module(pathlib.Path(path).stem)
            func = getattr(module, name, None)
            assert callable(func), (
                f"{fake}'s ledger cites {node_id}, but {name!r} is not a callable in "
                f"{path}. The verbatim RED capture in the SUMMARY is then unattributable"
            )
            marks = {mark.name for mark in getattr(func, "pytestmark", ())}
            assert parametrized == ("parametrize" in marks), (
                f"{fake}'s ledger cites {node_id}, whose parametrization does not match the "
                f"shipped test (marks: {sorted(marks)}). A cited node id that cannot be run is a "
                "citation nobody can check"
            )


# The sign-off's honest half, by name. A sign-off that lists only green is not a sign-off, so the
# two measured blind spots and the one required-but-unexercised CI item are required literals.
_LEDGER_SIGN_OFF_ITEMS = (
    ("FAKE 3 is invisible at a sigma of zero", "sigma = 0"),
    ("FAKE 3 is invisible at a lot size of one", "accum = 1"),
    ("the runtime C*(1+tol) sensitivity check is ONE-SIDED", "one-sided"),
    ('rng["mps"] is required-but-UNEXERCISED in CPU-only CI', 'rng["mps"]'),
)


def _summary_text():
    """The SUMMARY's text, or ``None`` before it has been written.

    **Skips gracefully only while the file does not exist**, which is the window between this
    file's first commit and the plan's metadata commit. Once the SUMMARY is on disk the assertions
    below are hard: a ledger that can silently go missing is not a ledger.
    """
    if not _SUMMARY_PATH.exists():
        return None
    return _SUMMARY_PATH.read_text(encoding="utf-8")


def test_fakes_ledger_is_recorded():
    """DPSGD-04's evidence ledger exists, with a heading per fake and the restoration recorded."""
    text = _summary_text()
    if text is None:
        pytest.skip(f"{_SUMMARY_PATH.name} is not written yet -- it lands with this plan's commit")

    headings = [line for line in text.splitlines() if line.lstrip().startswith("#")]
    for fake in _LEDGER_FAKES:
        assert any(fake in line for line in headings), (
            f"the DPSGD-04 evidence ledger in {_SUMMARY_PATH.name} has no heading naming {fake!r}. "
            "The requirement is the OBSERVED RED over the real mutated module, one section per "
            f"fake (headings found: {headings[:40]})"
        )
    for word in ("RED", "restored"):
        assert word in text, (
            f"{_SUMMARY_PATH.name} never says {word!r}. The ledger must carry both halves: the "
            "watched failure AND the byte-identical restore that makes the mutation transient"
        )


def test_fakes_ledger_names_its_blind_spots():
    """The sign-off names what is NOT covered, not only what is green."""
    text = _summary_text()
    if text is None:
        pytest.skip(f"{_SUMMARY_PATH.name} is not written yet -- it lands with this plan's commit")

    for label, literal in _LEDGER_SIGN_OFF_ITEMS:
        assert literal in text, (
            f"{_SUMMARY_PATH.name} does not contain {literal!r}, so it does not record that "
            f"{label}. A phase sign-off that lists only its greens is not a sign-off -- this "
            "phase's own recurring finding is that five plan-mandated guards were measured "
            "structurally incapable of catching what they existed for"
        )
