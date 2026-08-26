"""Phase 23 — the SINGLE SOURCE OF DEVICE TRUTH for this phase's test battery (D-01 / D-02).

WHY THIS FILE EXISTS
--------------------
The Phase-22 correctness battery is **CPU-only BY DESIGN**, and that is measured rather than
inferred: ``tests/test_phase22_checkpoint.py:3`` reads verbatim *"CPU-only, GPU-free, no network"*
and ``grep -c '"cpu"' tests/test_phase22_fakes.py`` returns **0** — that file passes no device
anywhere at all. Phase 23 publishes an ε produced on the **M3 (MPS)** venue (D-01), so every
device-dependent property those probes established has to CROSS the CPU→MPS boundary **by
measurement**. D-02 forbids recording the crossing as "assumed equivalent", and the boundary is
not cosmetic: the DP generator's state is **5,056 bytes on CPU and 44 bytes on MPS**, and the two
are MUTUALLY REFUSED by torch.

This module owns the device register (``_DEVICES`` / ``_MPS_SKIP``) that the Phase-22 battery
imports, plus the three properties that are about the VENUE rather than about the mechanism: the
DPSGD-06 σ=0 generator keystone, the cross-device state refusal, and the MPS round-trip D-07's
resume seam is built on. Two copies of a device gate drift, so there is exactly one.

THE MPS LEG IS A COUNTABLE SKIP, NEVER AN ABSENCE
-------------------------------------------------
CI is ``ubuntu-latest`` on a CPU wheel (``.github/workflows/ci.yml:6,36``), so every MPS leg here
necessarily skips there. The register is therefore
``(pytest.param("cpu"), pytest.param("mps", marks=_MPS_SKIP))`` and **NOT** the shrinking-list form
``["cpu"] + (["mps"] if available else [])``. The shrinking list makes the MPS leg VANISH from
collection rather than SKIP, and 23-RESEARCH.md's Pitfall 1 is precisely that the phase gate must be
able to COUNT the MPS skips: *an absent parametrization cannot be counted; a skipped one can*. A
green CI run that silently collected no MPS items is the exact failure mode D-02 exists to prevent,
so the phase gate asserts ``M == 0`` in ``N passed, M skipped`` on the M3 and that number is quoted
as a literal in the plan SUMMARY.
"""

import pytest
import torch

from personacore.config import ModelConfig, RuntimeConfig
from personacore.lora.config import LoRAConfig
from personacore.lora.inject import inject_lora, mark_only_lora_trainable
from personacore.model.gpt import GPT
from personacore.privacy.dpsgd import DPSGD

# --- The shared register. ONE definition; `tests/test_phase22_*` import it rather than re-spell it.

_MPS_AVAILABLE = torch.backends.mps.is_available()

_MPS_SKIP = pytest.mark.skipif(
    not _MPS_AVAILABLE,
    reason=(
        "MPS is unavailable here and CI is `ubuntu-latest` on a CPU-only torch wheel "
        "(.github/workflows/ci.yml:6,36), so this leg CANNOT run there and is gated rather than "
        "deleted. D-01 makes MPS the venue that produces this milestone's PUBLISHED ε, so the leg "
        "is not optional on the M3: the phase gate asserts a skip count of ZERO there and quotes "
        "the literal `N passed, M skipped` line, because a green CPU suite read as a green venue "
        "pass is 23-RESEARCH.md's Pitfall 1. What still carries each property wherever this skips "
        "is the non-skipping `cpu` leg of the SAME parametrized test — the σ=0 generator "
        "advance, the state round-trip and every Phase-22 probe hold on CPU unconditionally; what "
        "the MPS leg adds is the DEVICE TRANSFER, which is the only thing lost in CI and the only "
        "thing this phase re-watches."
    ),
)

# `pytest.param("mps", marks=_MPS_SKIP)` deliberately, NOT a list that shrinks when MPS is absent.
# See the module docstring: a vanished parametrization cannot be counted, a skipped one can.
_DEVICES = (pytest.param("cpu"), pytest.param("mps", marks=_MPS_SKIP))

# The draw widths the keystone is asserted at. Research measured the σ=0 advance at all six; one
# width would leave "it advances" true of a single shape rather than of the property.
_DRAW_SIZES = (1, 2, 4, 8, 16, 4608)

# Measured, torch 2.7.1, this venv: `torch.Generator().get_state()` is uint8 on CPU at these
# numels. Both states LIVE ON CPU whatever the generator's device, which is what makes every
# `torch.equal(state_a, state_b)` in `dpsgd.py` device-safe exactly as written.
_CPU_STATE_NUMEL = 5056
_MPS_STATE_NUMEL = 44

# Fixture scale, `tests/test_phase22_checkpoint.py:85`'s tiny GPT verbatim: DPSGD's closed-form
# census r*n_layer*18*n_embd holds at ANY shape, so the cheap fixture exercises the real seam.
_TINY = ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)
_RANK = 4
_NON_BINDING_CLIP = 1e6


def _seam(device, *, sigma=0.0, seed=4242):
    """A REAL ``DPSGD`` over a real GPT+LoRA already resident on ``device``.

    The model is moved BEFORE the seam is constructed, deliberately: ``DPSGD.__init__`` allocates
    ``_accum`` with ``torch.zeros_like(p)`` and derives its generator device from
    ``params[0].device``, so a seam built on CPU and then handed a moved model would carry a CPU
    accumulator and a CPU generator against MPS gradients.
    """
    torch.manual_seed(1234)
    model = GPT(_TINY)
    inject_lora(model, LoRAConfig(r=_RANK))
    mark_only_lora_trainable(model)
    model.to(device)
    return DPSGD(
        model,
        sigma=sigma,
        clip_norm=_NON_BINDING_CLIP,
        seed=seed,
        # RuntimeConfig.__post_init__ forces amp=False for BOTH cpu and mps (config.py:56-59), so
        # D-04's live-scaler refusal stays inert on MPS exactly as it is on CPU.
        runtime=RuntimeConfig(device=device),
    )


# =================================================================================================
# DPSGD-06's keystone: σ=0 draws exact zeros AND STILL ADVANCES the generator, on the real venue.
# =================================================================================================


@pytest.mark.parametrize("size", _DRAW_SIZES)
@pytest.mark.parametrize("device", _DEVICES)
def test_sigma_zero_advances_the_mps_generator(device, size):
    """**The one property whose failure on MPS would abort this phase's headline run.**

    ``dpsgd.py::_noised_private`` refuses with ``[dp-invariant:generator]`` when
    ``torch.equal(pre, post)`` — *"the generator state did not advance across the draws, so the
    draw did not happen"* — and its comment records *"At sigma = 0 the values are exact zeros BUT
    the state still moves (measured, torch 2.7.1)"*. **That measurement was taken on CPU.**

    DPSGD-06 makes σ=0 the DP arm's FIRST EXECUTED RUN, and D-01 puts it on MPS. If the 44-byte MPS
    state did not advance at ``std=0.0`` the milestone's first real run would refuse at EVERY step,
    and the refusal would read as a DP bug rather than as a venue fact — a whole phase spent
    debugging the mechanism instead of the platform. A measurement in a research document is not a
    committed test, so the keystone is asserted here at every width research measured it at.

    The advance is asserted as ``not torch.equal(pre, post)`` — the NEGATED form of the exact
    predicate ``dpsgd.py`` refuses on, not a paraphrase of it. The zeros are asserted EXACTLY, with
    ``count_nonzero(...) == 0`` and never through a tolerance: σ=0 releasing *nearly* zero would
    mean the identity input is not an identity, and any tolerance would hide precisely that. There
    is no approximate comparison anywhere in this file, by construction.
    """
    dp = _seam(device)
    assert dp._g.device.type == device, (
        f"the seam's dedicated generator is on {dp._g.device!r}, not {device!r} — D-14 binds it to "
        "the REAL execution device, and a CPU generator on the MPS venue would make this whole "
        "test a second CPU measurement wearing an mps id"
    )

    pre = dp.noise_rng_state()
    drawn = torch.normal(
        mean=0.0,
        std=0.0,
        size=(size,),
        device=device,
        generator=dp._g,
    )
    post = dp.noise_rng_state()

    assert drawn.numel() == size
    assert int(torch.count_nonzero(drawn)) == 0, (
        f"torch.normal(std=0.0) released {int(torch.count_nonzero(drawn))} non-zero value(s) of "
        f"{size} on {device}. σ=0 is D-06's IDENTITY input: the released values must be EXACTLY "
        "zero, so the σ=0 arm reproduces the unmitigated control. Anything near-but-not-zero is a "
        "different mechanism than the one the report describes"
    )
    assert not torch.equal(pre, post), (
        f"the generator state did NOT advance across a std=0.0 draw of {size} element(s) on "
        f"{device}. dpsgd.py::_noised_private refuses on exactly this predicate, so DPSGD-06's "
        "σ=0 run would raise [dp-invariant:generator] at every step on this venue — and the "
        "failure would look like a DP bug rather than a device fact"
    )


# =================================================================================================
# The cross-device boundary: 5,056 B vs 44 B, mutually refused. WATCHED, not assumed.
# =================================================================================================


@_MPS_SKIP
def test_generator_state_is_mutually_refused_across_devices():
    """The 5,056 B / 44 B divergence, and the two refusals that make it safe.

    Two things are asserted, and the second is the one the rest of the battery rests on:

    1. **The sizes really do diverge** — 5,056 on CPU against 44 on MPS. Without this the refusals
       below could be firing for some unrelated reason.
    2. **Both states LIVE ON CPU** whatever the generator's device. That is what makes every
       ``torch.equal(state_a, state_b)`` in ``dpsgd.py`` (the continuity check and the advance
       check) and in the Phase-22 tests a comparison of two CPU tensors, hence device-safe exactly
       as written — no ``.cpu()`` plumbing is needed anywhere and none is added.

    The refusals are asserted on DISCRIMINATING SUBSTRINGS (``5056``, ``wrong size``), never on the
    full message. A torch patch release rewording an error string must not redden a property that
    still holds.
    """
    cpu_gen = torch.Generator()
    mps_gen = torch.Generator(device="mps")
    cpu_state = cpu_gen.get_state()
    mps_state = mps_gen.get_state()

    assert (cpu_state.numel(), mps_state.numel()) == (_CPU_STATE_NUMEL, _MPS_STATE_NUMEL), (
        f"generator state sizes are {cpu_state.numel()} (cpu) / {mps_state.numel()} (mps), not the "
        f"measured {_CPU_STATE_NUMEL} / {_MPS_STATE_NUMEL}. The refusals below are asserted about "
        "THIS divergence; if the sizes converged, a cross-device state could be accepted silently "
        "and the checkpoint boundary would stop being watched"
    )
    assert cpu_state.device.type == "cpu" and mps_state.device.type == "cpu", (
        f"a generator state is not a CPU tensor (cpu gen -> {cpu_state.device}, mps gen -> "
        f"{mps_state.device}). Every torch.equal over these states in dpsgd.py assumes two CPU "
        "operands; if an MPS generator started returning an MPS state, those comparisons would "
        "need device plumbing that does not exist"
    )
    assert cpu_state.dtype == mps_state.dtype == torch.uint8

    with pytest.raises(RuntimeError, match="5056"):
        cpu_gen.set_state(mps_state)

    with pytest.raises(RuntimeError, match="wrong size"):
        mps_gen.set_state(cpu_state)


@_MPS_SKIP
def test_mps_generator_state_round_trips_fresh_and_midstream(tmp_path):
    """D-07's MECHANISM: an MPS generator state survives ``save``/``load``/``set_state``.

    Asserted in both of the shapes a resume actually takes — from a FRESH seed, and MID-STREAM
    after the generator has already been drawn from — because a state that round-trips only at
    position zero would round-trip in every test and still lose a real run's position.

    Both halves are asserted per shape, and the second is what makes the first non-vacuous:

      * the state BYTES come back identical (``torch.equal``), and
      * **the NEXT DRAW** comes back identical.

    Bytes alone are not enough: a restore that wrote the tensor somewhere the generator does not
    read would still compare equal on the tensor. 23-07 wires this into the resume seam; this test
    is what makes that wiring rest on a WATCHED property instead of on a research note.
    """
    for label, advance in (("fresh", 0), ("midstream", 10)):
        gen = torch.Generator(device="mps")
        gen.manual_seed(20230823)
        for _ in range(advance):
            torch.normal(mean=0.0, std=1.0, size=(8,), device="mps", generator=gen)

        saved = gen.get_state()
        assert saved.numel() == _MPS_STATE_NUMEL
        path = tmp_path / f"mps_state_{label}.pt"
        torch.save(saved, path)

        expected = torch.normal(mean=0.0, std=1.0, size=(64,), device="mps", generator=gen)
        # NON-DEGENERACY: the probe draw must actually carry information, or "the next draw
        # matches" would be a comparison of two zero vectors.
        assert float(expected.abs().sum()) > 0.0

        restored = torch.load(path, map_location="cpu", weights_only=True)
        gen.set_state(restored)
        assert torch.equal(gen.get_state(), saved), (
            f"the {label} MPS generator state did not survive save->load->set_state as BYTES"
        )

        replayed = torch.normal(mean=0.0, std=1.0, size=(64,), device="mps", generator=gen)
        assert torch.equal(expected, replayed), (
            f"the {label} MPS generator state round-tripped as bytes but the NEXT DRAW diverged, "
            "so the restore did not put the stream back where it was — which is the only thing "
            "D-07's resume seam actually needs from it"
        )
