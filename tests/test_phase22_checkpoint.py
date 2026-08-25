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
import pathlib

import pytest
import torch

from personacore.checkpoint import CKPT_SCHEMA_VERSION, load_checkpoint, save_checkpoint
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.lora.config import LoRAConfig
from personacore.lora.inject import inject_lora, mark_only_lora_trainable
from personacore.model.gpt import GPT
from personacore.privacy.dpsgd import DPSGD
from personacore.provenance import git_sha

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


def _tiny_lora_model(*, freeze=True, seed=1234):
    torch.manual_seed(seed)
    model = GPT(_TINY)
    inject_lora(model, LoRAConfig(r=_RANK))
    if freeze:
        mark_only_lora_trainable(model)
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
