"""Phase 22 — the checkpoint half of DPSGD-05 and DPSGD-07 (V-15, V-16, V-17).

CPU-only, GPU-free, no network. One MPS-touching test is ``skipif``-gated; what still carries the
guarantee when it skips is named in its ``reason=`` string rather than left to a reader.

WHAT THIS FILE PROVES, AND THE ONE THING IT DELIBERATELY DOES NOT
----------------------------------------------------------------
  * **V-16 — the ``rng["mps"]`` slot round-trips AND every pre-Phase-22 checkpoint still loads.**
    The second half is the binding one. ``load_checkpoint`` restores ``rng["cuda"]`` with a
    SUBSCRIPT; copying that form for ``mps`` would raise ``KeyError`` on every artifact this
    project has ever written, which is precisely the backward compatibility DPSGD-05 requires.
    The restore therefore uses ``rng.get("mps")`` — ``ckpt.get("scaler")``'s own recorded
    precedent, in the same function.
  * **V-15 — a kill→resume through ``train(resume_from=…)`` reproduces a BIT-IDENTICAL reported
    ε.** Not a matching loss curve. And because ε is a function of (σ, T, δ) and NOT of the RNG,
    ε bit-identity alone does not prove the noise generator resumed — a separate negative control
    closes that gap.
  * **V-17 — ``LoRALinear`` is not restructured**, so every v3.0 adapter still loads: the
    state-dict key set round-trips under HARD equality, and ``lora_A`` / ``lora_B`` are asserted
    to still be bare ``nn.Parameter``s with ``base`` as the only child ``nn.Linear``.

``checkpoints/`` IS GITIGNORED — MEASURED, AND IT SHAPES EVERY TEST HERE
-----------------------------------------------------------------------
``git ls-files checkpoints/`` returns **0** files and ``.gitignore`` carries both ``checkpoints/``
and ``*.pt``. A fresh clone and CI have nothing there. So **no test in this file makes an on-disk
artifact a precondition**: every binding property is proven on an artifact built IN-TEST, and each
on-disk leg is ``skipif``-gated in ``tests/test_lora_artifact.py:238``'s register
(``skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")``), with its
``reason=`` naming the non-skipping test that still carries the guarantee. The on-disk legs are
STRICTLY ADDITIVE: locally they are stronger evidence (a genuinely old file, not a synthesized
lookalike); in CI they skip and nothing is lost.

THE TOLERANCE REGISTER HAS TWO ENTRIES AND THEY MUST NOT BE CONFLATED
--------------------------------------------------------------------
``src/personacore/privacy/accountant.py``'s module docstring writes both down adjacently for
exactly this reason, and V-15 below is the site the first entry exists for:

  * **The SAME call shape across two processes ⇒ exact ``==``.** ``epsilon_for(σ, T, δ)`` with
    identical arguments is deterministic, so equality is the correct assertion and a tolerance
    would only weaken it. That is ``lora/inject.py::load_adapter_weights``'s W1 reasoning applied
    here — *"the same operation on the same operands gives a bit-identical float; a tolerance
    would only weaken this"*.
  * **TWO DIFFERENT call shapes ⇒ a RELATIVE tolerance (V-03's ``ROUND_TRIP_REL_TOL = 1e-12``),
    never ``==``.** The q=1 composition identity is EXACT in real arithmetic and still fails
    bitwise **19.9%** of the time in float64 (795/4000 sampled pairs) purely from double-rounding.

Neither entry generalises to the other's case. V-15 is the first; it uses ``==``.
"""

import glob
import math
import pathlib
import sys
from dataclasses import asdict

import pytest
import torch

from personacore.checkpoint import (
    CKPT_SCHEMA_VERSION,
    export_adapter,
    load_adapter,
    load_checkpoint,
    load_slim,
    save_checkpoint,
)
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.lora.config import LoRAConfig
from personacore.lora.inject import (
    inject_lora,
    load_adapter_weights,
    lora_state_dict,
    mark_only_lora_trainable,
)
from personacore.lora.layer import LoRALinear
from personacore.model.gpt import GPT
from personacore.privacy.accountant import epsilon_for
from personacore.privacy.dpsgd import DPSGD
from personacore.provenance import git_sha
from personacore.training.loop import train

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# ONE device register for the whole phase, imported rather than re-spelled (D-02). Two copies of a
# device gate drift, and a drifted gate is how an MPS leg stops being counted.
from test_phase23_mps_venue import _DEVICES, _MPS_SKIP  # noqa: E402  (tests/ is not a package)

# --- Fixture scale. A tiny GPT, not the 13.9M production one: DPSGD's closed-form census is
# r * n_layer * 18 * n_embd, which holds at ANY shape, so the cheap fixture exercises the same
# refusals. vocab_size/eos_id stay at the LOCKED defaults (tests/test_lora_artifact.py:63-65's
# reason: the embedded config must keep production shape).
_TINY = ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)
_RANK = 4

# Test-local fixture values, NOT a budget. Phase 22 names no σ and no C anywhere in its tree
# (D-08 / Phase 20's Z boundary); these are arithmetic test vectors.
_NON_BINDING_CLIP = 1e6
_DELTA = 1e-5

# The register every on-disk leg in this file skips with. `checkpoints/` is gitignored (measured:
# `git ls-files checkpoints/` -> 0 files), so a fresh clone and CI have none of these.
_CHECKPOINTS = pathlib.Path("checkpoints")


def _oldest_full_checkpoint():
    """The smallest real ``*latest.pt`` on disk, or ``None``. NEVER a hard precondition.

    Resolved by GLOB rather than by a hard-coded filename: nothing under ``checkpoints/`` is
    tracked, so any specific name is a guess about one developer's box.
    """
    matches = sorted(glob.glob(str(_CHECKPOINTS / "*latest.pt")))
    if not matches:
        return None
    return pathlib.Path(min(matches, key=lambda p: pathlib.Path(p).stat().st_size))


_REAL_FULL = _oldest_full_checkpoint()


def _toy():
    """A toy Linear + AdamW + scheduler — ``tests/test_checkpoint.py::_build``'s shape verbatim."""
    model = torch.nn.Linear(4, 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-2)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.99)
    return model, optimizer, scheduler


def _save(path, **extra):
    """``save_checkpoint`` over the toy trio, returning the loaded raw dict."""
    model, optimizer, scheduler = _toy()
    save_checkpoint(
        path,
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        step=7,
        model_config=_TINY,
        train_config=TrainConfig(),
        git_sha=git_sha(),
        **extra,
    )
    return torch.load(path, map_location="cpu", weights_only=False)


def _tiny_lora_model(*, freeze=True, seed=1234, device="cpu"):
    """The fixture model. ``device`` is additive; the default is byte-identical to Phase 22's.

    The move happens BEFORE any ``DPSGD`` is built over the model, because ``DPSGD.__init__``
    allocates ``_accum`` with ``torch.zeros_like(p)`` and derives its generator device from
    ``params[0].device`` — a seam built on a still-CPU model and moved afterwards would hold a CPU
    accumulator and a CPU generator against MPS gradients.
    """
    torch.manual_seed(seed)
    model = GPT(_TINY)
    inject_lora(model, LoRAConfig(r=_RANK))
    if freeze:
        mark_only_lora_trainable(model)
    model.to(device)
    return model


# ==================================================================================================
# V-16 — the mps slot: round trip (gated) + backward compatibility (binding, runs everywhere)
# ==================================================================================================


def test_old_checkpoint_without_mps_slot_still_loads(tmp_path):
    """**The binding half of V-16, and it runs EVERYWHERE** — no MPS, no on-disk artifact.

    The pre-Phase-22 shape is built IN-TEST: save a checkpoint, delete ``rng["mps"]`` from the raw
    dict, re-save. That artifact is byte-for-byte what every checkpoint this project wrote before
    Phase 22 looks like, and ``load_checkpoint`` must resume from it without a ``KeyError``.

    The failure this stands for is not hypothetical: ``load_checkpoint`` restores ``rng["cuda"]``
    with a SUBSCRIPT, and copying that one character for ``mps`` breaks every artifact at once —
    the exact backward compatibility DPSGD-05 names. ``rng.get("mps")`` is the fix, and
    ``ckpt.get("scaler")`` in the same function is its recorded precedent.
    """
    path = tmp_path / "modern.pt"
    blob = _save(path)
    # META-GUARD, in the OTHER direction first: the modern save really does carry the key on a
    # box where MPS exists. Without this the deletion below could be deleting nothing and the
    # test would pass by loading an ordinary checkpoint.
    assert "mps" in blob["rng"], "save_checkpoint did not write the mps slot at all (DPSGD-05)"

    del blob["rng"]["mps"]
    old = tmp_path / "pre_phase22.pt"
    torch.save(blob, old)

    # META-GUARD: the artifact about to be loaded genuinely LACKS the key, so a green result
    # cannot come from having re-saved something that still had it.
    reread = torch.load(old, map_location="cpu", weights_only=False)
    assert "mps" not in reread["rng"], "the pre-Phase-22 fixture still carries rng['mps']"
    assert set(reread["rng"]) == {"python", "numpy", "torch", "cuda"}, (
        "the pre-Phase-22 fixture's rng key set is not the real pre-Phase-22 one — measured on "
        "the actual artifacts on disk, it is exactly {python, numpy, torch, cuda}"
    )

    model, optimizer, scheduler = _toy()
    restored = load_checkpoint(old, model=model, optimizer=optimizer, scheduler=scheduler)
    assert restored["step"] == 7
    assert restored["schema_version"] == CKPT_SCHEMA_VERSION


@pytest.mark.skipif(
    _REAL_FULL is None,
    reason=(
        "no real checkpoints/*latest.pt present (CI / fresh clone) — `checkpoints/` is GITIGNORED "
        "(measured: `git ls-files checkpoints/` returns 0 files; .gitignore carries both "
        "`checkpoints/` and `*.pt`), so this leg is ADDITIVE and never a precondition. "
        "test_old_checkpoint_without_mps_slot_still_loads carries the whole V-16 backward-"
        "compatibility guarantee wherever this skips: it builds the pre-Phase-22 shape in-test "
        "and does not skip anywhere"
    ),
)
def test_old_on_disk_checkpoint_still_loads():
    """V-16, additive: the same assertion against a GENUINELY old artifact, not a lookalike.

    A synthesized pre-Phase-22 checkpoint resembles the old shape because this test file chose it.
    A real one on disk IS the old shape, written months ago by a torch that had never heard of this
    slot — which is the stronger evidence when it is available. It is gated because it is not
    available everywhere.
    """
    raw = torch.load(_REAL_FULL, map_location="cpu", weights_only=False)
    # POSITIVE CONTROL: this file predates the slot. If a future re-export gives it one, the test
    # is no longer testing backward compatibility and says so instead of passing quietly.
    assert "mps" not in raw["rng"], (
        f"{_REAL_FULL} already carries rng['mps'], so it is not a pre-Phase-22 artifact and this "
        "leg proves nothing about backward compatibility"
    )

    model = GPT(ModelConfig(**raw["model_config"]))
    lora_keys = sorted(k for k in raw["model"] if "lora_" in k)
    if lora_keys:
        # r is read from the ARTIFACT's own tensor shape, never assumed: these files span several
        # phases and more than one rank.
        inject_lora(model, LoRAConfig(r=raw["model"][lora_keys[0]].shape[0]))
    restored = load_checkpoint(_REAL_FULL, model=model)
    assert restored["schema_version"] == CKPT_SCHEMA_VERSION
    assert isinstance(restored["step"], int)


@pytest.mark.skipif(
    not torch.backends.mps.is_available(),
    reason=(
        "MPS is unavailable here and CI is CPU-only, so this row cannot run there. D-14 records "
        "rng['mps'] as REQUIRED-BUT-UNEXERCISED **on purpose**, and that is the honest word for "
        "it: DPSGD-05 names the slot literally, but the DP path fires the separately-named "
        "`dp_noise_rng` slot instead, because D-07 locked a DEDICATED torch.Generator and a "
        "dedicated generator's draw does not change the global MPS state (measured — as does a "
        "real GPT+LoRA forward+backward on MPS, which also leaves torch.mps.get_rng_state() "
        "unchanged). So nothing about the DP guarantee rests on this test running. What carries "
        "V-16 wherever this skips is test_old_checkpoint_without_mps_slot_still_loads, which "
        "builds the pre-Phase-22 shape in-test and does not skip anywhere; and what carries the "
        "DP resume guarantee is test_resume_epsilon_bit_identical's negative control over "
        "`dp_noise_rng`, which is CPU-only and also does not skip"
    ),
)
def test_mps_rng_slot_round_trips(tmp_path):
    """V-16's gated half: the slot is written LIVE and the restore actually moves the stream."""
    path = tmp_path / "mps.pt"
    blob = _save(path)
    saved = blob["rng"]["mps"]
    assert saved is not None and saved.numel() > 0
    assert torch.equal(saved, torch.mps.get_rng_state()), (
        "the saved mps slot is not the LIVE device state at save time"
    )

    # Perturb the device stream, then assert it MOVED — the positive control that makes the
    # equality after the restore evidence of a restore rather than of two states that never
    # differed.
    torch.rand(64, device="mps")
    perturbed = torch.mps.get_rng_state()
    assert not torch.equal(perturbed, saved), (
        "an MPS draw did not move torch.mps.get_rng_state(), so this test cannot observe a "
        "restore at all and would be green with the restore deleted"
    )

    model, optimizer, scheduler = _toy()
    load_checkpoint(path, model=model, optimizer=optimizer, scheduler=scheduler)
    assert torch.equal(torch.mps.get_rng_state(), saved), (
        "load_checkpoint did not restore the mps device RNG state from rng['mps']"
    )


def test_dp_noise_rng_rides_extra_without_a_schema_bump(tmp_path):
    """``dp_noise_rng`` is an ``**extra`` key — the ``fisher``/``theta_star`` precedent, verbatim.

    Three properties, and the third is what keeps the first two from being vacuous:
      1. the real ``DPSGD.noise_rng_state()`` value round-trips BYTE-IDENTICALLY;
      2. ``CKPT_SCHEMA_VERSION`` does not bump — the open dict already covers this;
      3. the ``_RESERVED_CKPT_KEYS`` clash refusal is LIVE, proven by watching it fire for a
         genuinely reserved key (``rng=``). Without (3), (1) and (2) would also be green in a
         world where the guard had simply been deleted.

    **No hard-coded byte count is asserted.** The generator state is 5,056 bytes on CPU and 44 on
    MPS (measured, torch 2.7.1); every Phase-22 test runs on CPU, so a bare "44" quoted from an MPS
    probe would be wrong here. ``len(state) > 0`` plus ``torch.equal`` is the device-free property.
    """
    dp = DPSGD(
        _tiny_lora_model(),
        sigma=1.0,
        clip_norm=_NON_BINDING_CLIP,
        seed=4242,
        runtime=RuntimeConfig(device="cpu"),
    )
    state = dp.noise_rng_state()
    assert state.numel() > 0, "an empty generator state would make the round trip unfalsifiable"

    blob = _save(tmp_path / "with_dp.pt", dp_noise_rng=state)
    assert "dp_noise_rng" in blob, "dp_noise_rng did not survive **extra"
    assert torch.equal(blob["dp_noise_rng"], state), "the generator state did not round-trip"
    assert blob["schema_version"] == CKPT_SCHEMA_VERSION == 1, (
        "dp_noise_rng rides the OPEN dict; nothing about the format changed, so the schema "
        "version must not bump"
    )

    # (3) the clash refusal is live, not absent. `rng` IS reserved and would silently overwrite
    # core resume state.
    with pytest.raises(ValueError, match="collide with reserved"):
        _save(tmp_path / "clash.pt", rng={"python": None})


# ==================================================================================================
# V-15 — a kill -> resume THROUGH train(resume_from=...) reproduces a bit-identical reported epsilon
# ==================================================================================================

_TOTAL_STEPS = 4
_KILL_AT = 2
_ACCUM = 2
_MICRO_BS = 2
_DP_SEED = 4242
_RESUME_SEED = 999  # deliberately NOT _DP_SEED — see the positive control below.

_FIXTURE_GEN = torch.Generator().manual_seed(20220705)
# The DRAW STAYS HERE, ON CPU, at module scope, and it must never become device-local: a
# `torch.Generator(device=...)` here would hand the two devices DIFFERENT fixture batches, and any
# resulting divergence would read as a resume defect rather than as a different input. The move to
# the execution device is `training/loop.py:587`'s job — `train()` does
# `fx, fy = fx.to(runtime.device), fy.to(runtime.device)` on `fixed_batch` itself — so nothing here
# needs to move it and a second `.to()` would be a no-op.
_BATCH = (
    torch.randint(0, _TINY.vocab_size, (_MICRO_BS, _TINY.block_size), generator=_FIXTURE_GEN),
    torch.randint(0, _TINY.vocab_size, (_MICRO_BS, _TINY.block_size), generator=_FIXTURE_GEN),
)


def _dp_train(model, dp, *, checkpoint_path, steps, resume_from=None, device="cpu"):
    """One ``train()`` call with the DP seam live. Everything below is asserted about THIS."""
    train(
        train_config=TrainConfig(
            lr=1e-3,
            warmup_steps=0,
            max_steps=_TOTAL_STEPS,
            batch_size=_MICRO_BS,
            grad_accum_steps=_ACCUM,
        ),
        runtime_config=RuntimeConfig(device=device),
        model=model,
        model_config=_TINY,
        fixed_batch=_BATCH,
        dp_fn=dp,
        checkpoint_path=checkpoint_path,
        resume_from=resume_from,
        max_steps_override=steps,
    )
    # `map_location="cpu"` stays: the RNG states in this blob are CPU tensors on BOTH devices
    # (measured — a generator's `get_state()` lives on CPU whatever the generator's device), and
    # `load_checkpoint` owns placement for everything else.
    return torch.load(checkpoint_path, map_location="cpu", weights_only=False)


def _seam(model, sigma, seed, device="cpu"):
    return DPSGD(
        model,
        sigma=sigma,
        # FINITE and non-binding. Plan 22-04 REFUSES math.inf: 0.0 * math.inf is nan and
        # torch.normal(std=nan) raises, which would crash at exactly the sigma = 0 row below.
        clip_norm=_NON_BINDING_CLIP,
        seed=seed,
        # RuntimeConfig.__post_init__ forces amp=False on BOTH cpu and mps (config.py:56-59), so
        # D-04's live-scaler refusal stays inert on the MPS venue exactly as it is on CPU.
        runtime=RuntimeConfig(device=device),
    )


def _count_composed_steps(dp):
    """Count the optimizer steps this seam ACTUALLY composed, by shadowing ``finalize``.

    Load-bearing, and it was added because a mutation measured the obvious version incapable: with
    ``train()``'s ``start_step = ckpt["step"]`` mutated to ``start_step = 0``, the resumed run
    executes ``_TOTAL_STEPS`` MORE steps on top of the pre-kill ones — composing 6 — while its
    end-of-call checkpoint still records ``step = 4``. An ε read off that ``step`` field is then
    identical across the two arms and OPTIMISTIC: the published number describes a 4-fold
    composition that never ran. Counting the real invocations is what makes the ε assertion a
    statement about **the mechanism that actually ran** rather than about a field.
    """
    calls = []
    real = dp.finalize

    def counting(accum):
        calls.append(accum)
        return real(accum)

    dp.finalize = counting  # per-INSTANCE shadow; the class method is untouched.
    return calls


def _next_draw(dp, device="cpu"):
    """One draw from the seam's OWN generator — "the noise this seam would release next".

    ``std`` is fixed at 1.0 rather than at the arm's sigma **on purpose**: at sigma = 0 every
    released value is exactly zero, so comparing released VALUES could never see a stream that
    resumed at the wrong position — while the generator still ADVANCES (measured, torch 2.7.1:
    ``torch.normal(std=0.0)`` returns exact zeros AND moves the state; committed as
    ``tests/test_phase23_mps_venue.py::test_sigma_zero_advances_the_mps_generator`` on BOTH
    devices). Probing at std = 1.0 makes the sigma = 0 row carry the same evidence as sigma > 0.

    ``device=`` is REQUIRED on MPS and is not cosmetic. Measured: without it, ``torch.normal`` with
    an MPS generator raises ``RuntimeError: Placeholder storage has not been allocated on MPS
    device!`` — torch cannot infer the output device from the generator.
    """
    return torch.normal(mean=0.0, std=1.0, size=(16,), device=device, generator=dp._g)


@pytest.mark.parametrize("device", _DEVICES)
@pytest.mark.parametrize("sigma", [1.0, 0.0])
def test_resume_epsilon_bit_identical(tmp_path, sigma, device):
    """**V-15 / DPSGD-05.** A kill→resume reproduces the reported ε under EXACT ``==``.

    WHY ``==`` AND NOT V-03's ``rel_tol``, WRITTEN DOWN TOGETHER SO THEY CANNOT BE CONFLATED.
    This compares **the same call shape** — ``epsilon_for(sigma, steps, delta)`` with identical
    arguments — across two processes. That is deterministic, so equality is the correct assertion
    and *"a tolerance would only weaken this"* (``src/personacore/lora/inject.py::
    load_adapter_weights``'s W1 reasoning, at ``inject.py:113-118``: the same operation on the same
    operands gives a bit-identical float). V-03 is the OTHER register entirely: it compares two
    **different** call shapes whose double-rounding disagrees bitwise **19.9%** of the time
    (795/4000 pairs), and it uses ``ROUND_TRIP_REL_TOL = 1e-12``. Neither generalises to the other.

    THE RESUME GOES THROUGH ``train(resume_from=…)`` — THE PRODUCTION PATH — AND NOTHING HERE
    RESTORES BY HAND. Plan 22-06 (e.2) is what wires ``dp_fn.load_noise_rng_state(...)`` into the
    ``resume_from`` block; a test that called it directly would be green over a production path
    that never restores, which is exactly the defect this assertion exists to catch. Every property
    below is asserted about what ``train()`` did.

    **ε BIT-IDENTITY ALONE DOES NOT PROVE THE RNG RESUMED**, and saying otherwise would be the
    over-claim this phase exists to prevent: ε is a function of (σ, T, δ) and **not** of the RNG.
    The negative control at the bottom is what closes that gap. The failure it stands for: without
    the restore, ``DPSGD.__init__`` re-seeds from the caller's seed and the resumed run REPLAYS
    NOISE IT ALREADY RELEASED — DPSGD-04/SC4's fourth fake (*RNG reused across steps*), reachable
    through PRODUCTION rather than by a deliberate edit, and invisible to D-16 invariant 4 because
    ``_prev_gen_state`` is ``None`` on a freshly constructed object.

    ``sigma = 0`` is a parametrized case because D-12's premise correction identifies it as where
    the forward direction bites: without ``epsilon_for``'s explicit σ=0 branch, Phase 23's first
    executed run crashes at REPORT time rather than in the mechanism. ``inf == inf`` is ``True``,
    so the same ``==`` carries it.
    """
    # --- Arm A: uninterrupted, _TOTAL_STEPS in one call ---------------------------------------
    model_a = _tiny_lora_model(device=device)
    dp_a = _seam(model_a, sigma, _DP_SEED, device)
    composed_a = _count_composed_steps(dp_a)
    blob_a = _dp_train(
        model_a, dp_a, checkpoint_path=tmp_path / "a.pt", steps=_TOTAL_STEPS, device=device
    )

    # META-GUARD: the run really took the DP path. A resume test over a run where dp_fn was
    # silently None would otherwise pass while proving nothing.
    assert dp_a._records == _ACCUM, (
        f"the DP seam absorbed {dp_a._records} records on its last step, not {_ACCUM} — this run "
        "did not go through dp_fn at all"
    )
    assert blob_a["step"] == _TOTAL_STEPS == len(composed_a)

    # --- Arm B: kill at _KILL_AT, then resume to _TOTAL_STEPS ----------------------------------
    model_b = _tiny_lora_model(device=device)
    dp_b = _seam(model_b, sigma, _DP_SEED, device)
    composed_b = _count_composed_steps(dp_b)
    kill = _dp_train(
        model_b, dp_b, checkpoint_path=tmp_path / "kill.pt", steps=_KILL_AT, device=device
    )

    # META-GUARD on the END-OF-CALL save specifically: max_steps_override exits the while loop
    # NORMALLY, so this is the checkpoint the resume reads. A dp_noise_rng refresh wired only to
    # the in-loop saves would leave the key absent here, and this is what catches that.
    assert kill["step"] == _KILL_AT
    assert "dp_noise_rng" in kill, (
        "the END-OF-CALL checkpoint carries no dp_noise_rng — an in-loop-only splat misses exactly "
        "the save a max_steps_override kill writes"
    )
    assert kill["dp_noise_rng"].numel() > 0

    # The KILL: the process state is dropped by constructing model + seam FRESH
    # (tests/test_resume_curve.py's existing pattern). train() builds its own optimizer, so the
    # optimizer state crosses the boundary only through the checkpoint.
    model_c = _tiny_lora_model(device=device)
    dp_c = _seam(model_c, sigma, _RESUME_SEED, device)
    composed_c = _count_composed_steps(dp_c)
    # POSITIVE CONTROL: the fresh seam's stream really is somewhere else, so anything matching
    # afterwards is the restore working rather than two objects that agreed to begin with.
    assert not torch.equal(dp_c.noise_rng_state(), kill["dp_noise_rng"])
    blob_c = _dp_train(
        model_c,
        dp_c,
        checkpoint_path=tmp_path / "c.pt",
        steps=_TOTAL_STEPS,
        resume_from=tmp_path / "kill.pt",
        device=device,
    )
    assert blob_c["step"] == _TOTAL_STEPS

    # --- THE CLAIM: a BIT-IDENTICAL reported epsilon over THE MECHANISM THAT ACTUALLY RAN -------
    # T is the COUNT OF COMPOSED STEPS, not the checkpoint's `step` field, and the difference is
    # measured rather than stylistic: with train()'s `start_step = ckpt["step"]` mutated to 0 the
    # resumed arm composes 6 steps while its checkpoint still says 4, so a field-read eps matches
    # across the arms and UNDER-REPORTS the composition. Reading the invocation count makes the
    # equality a statement about the mechanism instead of about a number in a file. Every checkpoint
    # `step` above is asserted equal to its own count, so the two readings are pinned together.
    steps_a = len(composed_a)
    steps_b = len(composed_b) + len(composed_c)
    assert (len(composed_b), len(composed_c)) == (_KILL_AT, _TOTAL_STEPS - _KILL_AT)
    assert blob_c["step"] == steps_b, (
        f"the resumed run REPORTS T = {blob_c['step']} but composed {steps_b} steps "
        f"({len(composed_b)} before the kill + {len(composed_c)} after). The published epsilon "
        "would then describe a composition that never ran, and it would be optimistic"
    )
    epsilon_a = epsilon_for(sigma, steps_a, _DELTA)
    epsilon_b = epsilon_for(sigma, steps_b, _DELTA)
    assert epsilon_a == epsilon_b, (
        f"reported epsilon diverged across a kill+resume: {epsilon_a!r} vs {epsilon_b!r}"
    )

    if sigma == 0.0:
        assert math.isinf(epsilon_a) and math.isinf(epsilon_b)
    else:
        assert math.isfinite(epsilon_a) and epsilon_a > 0.0
        # NON-DEGENERACY: eps genuinely MOVES with the step count, so the equality above is not
        # green over a quantity that never varies. This control cannot exist at sigma = 0 — eps is
        # inf for every T there — which is precisely why the sigma > 0 row carries it.
        assert epsilon_for(sigma, _KILL_AT, _DELTA) != epsilon_a

    # --- The RNG half, which epsilon is structurally blind to ----------------------------------
    # The uninterrupted arm and the resumed arm must be at the SAME stream position: dp_a drew on
    # _TOTAL_STEPS steps; dp_c restored dp_b's state at _KILL_AT and drew on the remaining ones.
    # (Asserted end-to-end rather than "equal to the saved state immediately after the resume",
    # which is only true when the resume takes ZERO further steps — 22-06's
    # test_dp_noise_rng_round_trips_through_a_kill_and_resume already pins that narrower form.)
    draw_uninterrupted = _next_draw(dp_a, device)
    draw_resumed = _next_draw(dp_c, device)
    assert draw_uninterrupted.abs().sum() > 0.0, "a degenerate probe draw would compare two zeros"
    assert torch.equal(draw_uninterrupted, draw_resumed), (
        "the resumed seam's next noise draw differs from the uninterrupted run's, so the "
        "production restore in train()'s resume_from block did not fire"
    )

    # NEGATIVE CONTROL, defeated at the PRODUCTION boundary rather than in the seam: a checkpoint
    # whose dp_noise_rng key is missing. That is also the pre-Phase-22 shape, so loop.py's `.get()`
    # guard is exercised here at the same time — it must read a missing key as "no restore", not
    # raise.
    stripped = dict(kill)
    del stripped["dp_noise_rng"]
    torch.save(stripped, tmp_path / "stripped.pt")
    model_d = _tiny_lora_model(device=device)
    dp_d = _seam(model_d, sigma, _RESUME_SEED, device)
    _dp_train(
        model_d,
        dp_d,
        checkpoint_path=tmp_path / "d.pt",
        steps=_TOTAL_STEPS,
        resume_from=tmp_path / "stripped.pt",
        device=device,
    )
    assert not torch.equal(draw_uninterrupted, _next_draw(dp_d, device)), (
        "with dp_noise_rng deleted the resumed run STILL produced the uninterrupted run's next "
        "noise draw — the positive assertion above would then be green with the restore removed, "
        "so it would prove nothing"
    )


@_MPS_SKIP
def test_cpu_written_dp_noise_rng_is_refused_on_mps(tmp_path):
    """The cross-device ``dp_noise_rng`` boundary, WATCHED rather than assumed (D-02).

    A DP generator's state is **5,056 bytes on CPU and 44 on MPS**, and torch refuses the mismatch
    LOUDLY in both directions (``tests/test_phase23_mps_venue.py::
    test_generator_state_is_mutually_refused_across_devices`` pins the raw pair). 23-RESEARCH.md
    §R1.4 records that as a FEATURE, not a hazard — a silently accepted cross-device state would
    resume a private run onto a stream nobody can account for. But a feature nobody exercises is a
    research note, so the boundary is exercised HERE, against a checkpoint written by the real
    production path rather than against a hand-built tensor.

    The operator mistake this stands for is reachable, not exotic: a run started on CPU (or handed
    over from a CI box) and resumed on the M3 for the long DP leg. It is exactly the same shape as
    the laptop-sleep resume ``CLAUDE.md`` calls ROUTINE on the primary path.

    **23-07 converts this raw ``RuntimeError`` into a ``SystemExit`` naming the ARM and the FILE**,
    so the operator is told which checkpoint was written on which device instead of reading a torch
    size message. This test asserts the underlying torch refusal that guarantee RESTS ON — if torch
    ever started accepting the foreign state, 23-07's friendlier message would be wrapping a
    refusal that no longer happens.
    """
    # The CPU-written checkpoint, produced by train() through the real DP path.
    model_cpu = _tiny_lora_model(device="cpu")
    dp_cpu = _seam(model_cpu, 1.0, _DP_SEED, "cpu")
    blob = _dp_train(
        model_cpu, dp_cpu, checkpoint_path=tmp_path / "cpu_written.pt", steps=_KILL_AT, device="cpu"
    )
    # META-GUARD: the artifact really carries the slot, or the refusal below would be firing on a
    # missing key rather than on a foreign one.
    assert "dp_noise_rng" in blob, "the CPU run wrote no dp_noise_rng — nothing to refuse"
    assert blob["dp_noise_rng"].numel() == 5056, (
        f"the CPU-written state is {blob['dp_noise_rng'].numel()} bytes, not the measured 5056 — "
        "the size divergence this refusal rests on is not what it was"
    )

    mps_seam = _seam(_tiny_lora_model(device="mps"), 1.0, _RESUME_SEED, "mps")
    # POSITIVE CONTROL: the MPS seam's own state is the OTHER size, so the refusal is about the
    # divergence and not about a malformed tensor.
    assert mps_seam.noise_rng_state().numel() == 44

    with pytest.raises(RuntimeError, match="wrong size"):
        mps_seam.load_noise_rng_state(blob["dp_noise_rng"])

    # …and the seam is left USABLE: a refused restore must not half-apply. Its own state is
    # unchanged, so an operator who corrects the checkpoint path can still resume.
    assert mps_seam.noise_rng_state().numel() == 44


# ==================================================================================================
# V-17 / DPSGD-07 — LoRALinear is NOT restructured, so every v3.0 artifact still loads
# ==================================================================================================


def _nudge_lora_B(model):
    """``lora_B`` starts at the zeros identity gate; a ``torch.equal`` over zeros proves nothing.

    ``tests/test_lora_artifact.py::_nudge_lora_B_nonzero`` verbatim.
    """
    for name, p in model.named_parameters():
        if name.endswith("lora_B"):
            torch.nn.init.normal_(p, mean=0.0, std=0.02)


def test_lora_state_dict_keys_survive_a_round_trip(tmp_path):
    """**V-17's binding half, and it runs EVERYWHERE** — no artifact under ``checkpoints/`` needed.

    A v3.0-shaped adapter is built IN-TEST and pushed through THIS PHASE'S modified
    ``checkpoint.py`` (``export_adapter`` → ``load_adapter``), then its key set is compared to a
    SECOND, FRESH model's ``lora_state_dict`` key set under **hard equality**. Never ``<=`` or
    ``issubset``: a subset passes while a key silently disappears, which is the whole failure mode.

    DPSGD-07 names the change this refuses: restructuring ``LoRALinear`` into ``nn.Linear``
    submodules would rename **every** state-dict key (``…lora_A`` → ``…lora_A.weight``) and
    invalidate every v3.0 artifact ever exported, ``checkpoints/persona_adapter.pt`` included.
    ``load_adapter_weights``'s key+shape+scale audit is what turns that rename into a loud refusal,
    and it is applied here rather than described.
    """
    donor = _tiny_lora_model()
    _nudge_lora_B(donor)
    path = tmp_path / "v3_adapter.pt"
    export_adapter(
        path,
        adapter=lora_state_dict(donor),
        lora_config=asdict(LoRAConfig(r=_RANK)),
        base_fingerprint={"git_sha": git_sha(), "step": 0, "val_loss": None},
    )
    loaded = load_adapter(path)

    fresh = _tiny_lora_model()
    expected = set(lora_state_dict(fresh))
    # META-GUARD: two EMPTY sets compare equal, so the closed form is asserted first. An A and a B
    # per wrapped projection, six projections per block (tests/test_lora_artifact.py:112-113).
    assert len(expected) == 2 * 6 * _TINY.n_layer > 0
    assert set(loaded["adapter"]) == expected, (
        "the adapter key set moved across an export/load round trip — a restructured LoRALinear "
        "renames every key and invalidates every v3.0 persona file (DPSGD-07)"
    )
    # The v3.0 key FORM, pinned as a LITERAL rather than merely agreed between two co-moving sides.
    # MEASURED, and it is why this line exists: under the exact restructuring DPSGD-07 forbids
    # (bare nn.Parameter -> nn.Linear submodules) the donor and the fresh model move TOGETHER, so
    # the set equality above stays GREEN while every key silently becomes `…lora_A.weight` and every
    # real v3.0 artifact stops loading. checkpoints/persona_adapter.pt's 72 keys end in exactly
    # `lora_A` / `lora_B`; that is the shipped form, pinned here so the property does not depend on
    # an artifact CI does not have.
    assert all(k.endswith(("lora_A", "lora_B")) for k in expected), (
        f"adapter keys are no longer the v3.0 form (…lora_A / …lora_B): {sorted(expected)[:4]}"
    )

    # …and it APPLIES, through the same key+shape+scale audit every real consumer routes through.
    load_adapter_weights(fresh, loaded)
    applied = fresh.state_dict()
    assert all(torch.equal(applied[k], v) for k, v in loaded["adapter"].items())


def test_lora_linear_holds_bare_parameters():
    """**V-17, structural, runs everywhere** — the property a restructuring breaks, checked direct.

    Asserted rather than inferred from a key set, and it needs no artifact at all. ``lora_A`` /
    ``lora_B`` are bare ``nn.Parameter``s inside an INLINE matmul (``lora/layer.py:41``), and
    ``base`` is the only child ``nn.Linear``. That shape is also the second reason D-01 rejected the
    module-hook design: module hooks do not reach bare parameters.
    """
    model = _tiny_lora_model()
    wrapped = [m for m in model.modules() if isinstance(m, LoRALinear)]
    assert len(wrapped) == 6 * _TINY.n_layer > 0, "no LoRALinear found — this test would be vacuous"
    for module in wrapped:
        assert isinstance(module.lora_A, torch.nn.Parameter)
        assert isinstance(module.lora_B, torch.nn.Parameter)
        children = {n for n, c in module.named_children() if isinstance(c, torch.nn.Linear)}
        assert children == {"base"}, (
            f"LoRALinear's child nn.Linear set is {sorted(children)}, not exactly {{'base'}} — "
            "DPSGD-07 forbids restructuring lora_A/lora_B into nn.Linear submodules"
        )


def _load_v3_adapter(path):
    """A real persona file onto a FRESH model built from today's ``LoRALinear``.

    The base shape is derived from the ARTIFACT's own tensors (``lora_A`` is ``(r, in_features)``,
    block indices give ``n_layer``) rather than assumed from ``ModelConfig()``'s defaults — these
    files span several phases.
    """
    art = load_adapter(path)
    keys = sorted(art["adapter"])
    n_embd = art["adapter"][next(k for k in keys if k.endswith("c_proj.lora_A"))].shape[1]
    n_layer = 1 + max(int(k.split(".")[1]) for k in keys if k.startswith("blocks."))
    model = GPT(ModelConfig(n_layer=n_layer, n_embd=n_embd))
    inject_lora(model, LoRAConfig(**art["lora_config"]))
    load_adapter_weights(model, art)  # key + shape + scale audit; raises on any rename
    assert set(lora_state_dict(model)) == set(art["adapter"])


def _load_v3_full(path):
    """A real FULL resume checkpoint through the production ``load_checkpoint``."""
    raw = torch.load(path, map_location="cpu", weights_only=False)
    model = GPT(ModelConfig(**raw["model_config"]))
    lora_keys = sorted(k for k in raw["model"] if "lora_" in k)
    if lora_keys:
        inject_lora(model, LoRAConfig(r=raw["model"][lora_keys[0]].shape[0]))
    restored = load_checkpoint(path, model=model)
    assert restored["schema_version"] == CKPT_SCHEMA_VERSION
    assert set(k for k in restored["model"] if "lora_" in k) == set(lora_keys)


def _load_v3_slim(path):
    """A real SLIM inference artifact under the ``weights_only=True`` bar."""
    loaded = load_slim(path)
    model = GPT(ModelConfig(**loaded["model_config"]))
    model.load_state_dict(loaded["model"])


def _v3_case(path, loader):
    """One on-disk case, gated on its OWN existence so a missing file skips only itself."""
    return pytest.param(
        path,
        loader,
        id=path.name,
        marks=pytest.mark.skipif(
            not path.exists(),
            reason=(
                f"{path} is not present (CI / fresh clone) — `checkpoints/` is GITIGNORED "
                "(measured: `git ls-files checkpoints/` returns 0 files; .gitignore carries both "
                "`checkpoints/` and `*.pt`), so this leg is ADDITIVE and never a precondition. "
                "V-17 is DPSGD-07's only validation row and it must hold with `checkpoints/` "
                "empty: what carries it wherever this skips is "
                "test_lora_state_dict_keys_survive_a_round_trip (a v3.0-shaped adapter built "
                "in-test and round-tripped under hard key-set equality) and "
                "test_lora_linear_holds_bare_parameters (the structural assertion), neither of "
                "which skips anywhere"
            ),
        ),
    )


_V3_CASES = [
    _v3_case(_CHECKPOINTS / "persona_adapter.pt", _load_v3_adapter),
    _v3_case(_REAL_FULL or _CHECKPOINTS / "__absent_latest.pt", _load_v3_full),
    _v3_case(_CHECKPOINTS / "model_slim.pt", _load_v3_slim),
]


def test_v3_case_table_declares_every_artifact_regardless_of_what_runs():
    """Collection meta-guard: an empty ``checkpoints/`` must report 3 SKIPS, never 0 tests.

    ``pytest.param(..., marks=skipif(...))`` per case is what makes that true — a single
    module-level gate would collapse the parametrization to zero collected items, and "nothing ran"
    is indistinguishable from "everything passed" in a summary line.
    """
    assert len(_V3_CASES) >= 3


@pytest.mark.parametrize(("path", "loader"), _V3_CASES)
def test_v3_on_disk_artifacts_still_load(path, loader):
    """**V-17, additive and gated**: the REAL v3.0 artifacts, when the box happens to have them.

    Locally this is the stronger evidence — files written by earlier phases, not lookalikes this
    module synthesized. In CI every case skips and V-17 still holds through the two tests named in
    each ``reason=``.
    """
    loader(path)
