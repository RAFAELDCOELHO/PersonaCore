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

import pathlib
import re

import pytest
import torch

from conftest import sweep_is_active
from personacore.config import ModelConfig, RuntimeConfig
from personacore.lora.config import LoRAConfig
from personacore.lora.inject import inject_lora, mark_only_lora_trainable
from personacore.model.gpt import GPT
from personacore.privacy.dpsgd import DPSGD

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# 23-06's SUMMARY -- the venue-transfer ledger. Defined HERE, in the phase's register file, and
# IMPORTED by `tests/test_phase22_fakes.py`, for the same reason `_DEVICES` is: two copies of a
# path drift, and a drifted path is how an assertion quietly stops reading the file it was written
# to read.
_VENUE_SUMMARY_PATH = (
    _ROOT
    / ".planning"
    / "phases"
    / "23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio"
    / "23-06-SUMMARY.md"
)

# --- The shared register. ONE definition; `tests/test_phase22_*` import it rather than re-spell it.

_MPS_PRESENT = torch.backends.mps.is_available()

# D-44. `_MPS_AVAILABLE` is the VALUE the flag flips, not merely the mark — TRAP 1. Five files
# import from this register and `tests/test_phase23_resume.py:414` uses `_MPS_AVAILABLE` as a
# BRANCH VALUE (`if _MPS_AVAILABLE: ... tp._generator_state_bytes("mps")`), which allocates on the
# device. Flipping only `_MPS_SKIP` would leave that branch touching a saturated MPS during the
# sweep, so the conjunction lives HERE, in the one place every consumer already reads.
_SWEEP_ACTIVE = sweep_is_active()
_MPS_AVAILABLE = _MPS_PRESENT and not _SWEEP_ACTIVE

# TRAP 2: `reason` is a fixed string, and D-44 requires the reason to NAME THE SWEEP. So the mark
# is built from TWO reasons chosen conditionally. Both are module constants because
# `tests/test_phase25_venue.py` asserts they are DISTINCT — a two-reason construction that
# collapsed to one string would satisfy every other check in this file.
_MPS_ABSENT_REASON = (
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
)

_SWEEP_ACTIVE_REASON = (
    "PERSONACORE_SWEEP_ACTIVE is set: the v4.0 FRONTIER SWEEP is running on this machine and it "
    "owns the MPS device. MPS is genuinely AVAILABLE right now — that is the whole problem. The "
    "44-point sweep saturates the device for 4.5-6.3 days, so this leg would RUN and CONTEND with "
    "it, and a contention failure is INDISTINGUISHABLE FROM A GENUINE ONE: the same red, the same "
    "traceback, a cause nobody can separate from a real regression six days into an unrepeatable "
    "run. D-44 therefore makes the skip LOUD rather than letting the leg quietly fail or quietly "
    "vanish — the leg stays a countable `pytest.param(..., marks=...)`, the reason names the "
    "sweep, and `tests/test_phase25_venue.py::"
    "test_the_sweep_active_skip_count_is_the_number_stated_in_advance` asserts the resulting skip "
    "count against a literal committed BEFORE the sweep launched. Unset PERSONACORE_SWEEP_ACTIVE "
    "to run this leg — but only when the sweep is not holding the device."
)

_MPS_SKIP = pytest.mark.skipif(
    not _MPS_AVAILABLE,
    reason=_SWEEP_ACTIVE_REASON if (_SWEEP_ACTIVE and _MPS_PRESENT) else _MPS_ABSENT_REASON,
)

# =================================================================================================
# WHAT D-44 COVERS FOR FREE, WHAT NEEDS NO WORK, AND WHAT IS DELIBERATELY LEFT RUNNING.
#
# An exemption inferred from an absence is indistinguishable from an oversight, so all three
# classes are STATED here rather than left to be re-derived from the next reader's grep.
#
# COVERED FOR FREE, through the import of `_MPS_AVAILABLE` / `_MPS_SKIP` / `_DEVICES`:
#   * `tests/test_phase22_fakes.py`    — 7 `_DEVICES` params + 1 bare `@_MPS_SKIP`
#   * `tests/test_phase23_cal03.py`    — 2 `_DEVICES` params (a module-scope fixture)
#   * `tests/test_phase23_resume.py`   — 2 bare `@_MPS_SKIP` legs AND the branch-value use at
#                                        line 414, which is why the flag flips the VALUE (trap 1)
#
# NOT MPS-GATED AT ALL, so nothing here changes them — 25-CONTEXT.md names both as D-44 targets
# and both were read to confirm no separate work is needed:
#   * `tests/test_phase22_checkpoint.py` — its module-level gate is `_REAL_FULL is None`, i.e.
#     ARTIFACT PRESENCE, not device availability. It does import `_DEVICES` and `_MPS_SKIP`, and
#     those 3 legs are covered for free like the rest; the artifact gate is simply orthogonal.
#   * `tests/test_phase22_dpsgd.py` — its module gate is a `(system, machine, torch.__version__)`
#     PLATFORM TUPLE compared against `_CAPTURE_PLATFORM`. Also imports `_DEVICES`, so its 9 mps
#     params are covered for free; the platform tuple is orthogonal.
#
# DELIBERATELY LEFT RUNNING — five NAME-ONLY node ids that mention `mps` and touch no device:
#   * `tests/test_lr_schedule.py::test_warmup_ramps_from_zero_toward_one`      (pure arithmetic)
#   * `tests/test_phase22_accountant.py::test_quadrature_budgets_the_simpson_sum_not_one_term`
#   * `tests/test_preflight.py::test_mps_ok_when_strict`   (monkeypatches `is_available`)
#   * `tests/test_config.py::test_amp_off_on_mps`          `RuntimeConfig(device="mps")` dataclass
#   * `tests/test_config.py::test_mps_no_fp16_amp`         — construction only, NO allocation
#   Skipping them would inflate the count for zero contention benefit and blur the phase-gate skip
#   audit: the number would stop being attributable to device-touching legs.
# =================================================================================================

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


# =================================================================================================
# THE VENUE-TRANSFER LEDGER (23-06 / D-02). What did and did not cross CPU -> MPS, as a RECORD.
#
# D-02's obligation is not "the probes were re-run" — it is that the CROSSING is stated by
# measurement, per probe, with Phase 22's CPU-only result named as such. Prose in a SUMMARY that
# nothing asserts against can silently lose its honest half between one plan and the next, and
# 22-07-SUMMARY.md is the cautionary case in this very repository: its comparison table prints
# `5,056 bytes` in BOTH columns because both runs were CPU, so the divergence the whole checkpoint
# boundary rests on is invisible in the artifact that documents it. These two tests are what make
# repeating that impossible here.
# =================================================================================================

_VENUE_PROBES = ("V-15", "FAKE 1", "FAKE 2", "FAKE 3", "FAKE 4")

# The phrase D-02 REQUIRES about the Phase-22 record, and the framing it FORBIDS. The forbidden
# phrase is checked case-insensitively and must not appear even inside a denial: a reader grepping
# the artifact cannot tell a quoted prohibition from a claim.
_REQUIRED_TRANSFER_PHRASE = "not transferred to MPS"
_FORBIDDEN_TRANSFER_PHRASE = "assumed equivalent"

# The four re-measured readings and their two deltas — required as LITERALS so a summary cannot
# report "the constants held" without publishing the numbers that would let a reader disagree.
_REQUIRED_CONSTANT_LITERALS = (
    "1.7344813665273022",  # FAKE 1, cpu
    "1.734481393949083",  # FAKE 1, mps
    "2.742e-08",  # FAKE 1, |delta|
    "3.9999861813196698",  # FAKE 3, cpu
    "3.9999995238454056",  # FAKE 3, mps
    "1.334e-05",  # FAKE 3, |delta|
)

# The junit `testsuite` attributes, which is where the skip count is OBSERVED. pytest OMITS a zero
# skip count from its terminal line, so the ABSENCE of the word "skipped" there is not evidence —
# 23-01 measured exactly that. This shape is discriminating enough that the full suite's unrelated
# `1 skipped` cannot satisfy it by accident.
_JUNIT_ATTRS = re.compile(
    r"tests\s+(\d+)\s+failures\s+(\d+)\s+errors\s+(\d+)\s+skipped\s+(\d+)", re.IGNORECASE
)

# The four files whose combined run produces that count. Named in the SUMMARY so the number is
# attributable to a command a reader can re-run, rather than to an unspecified invocation.
_SKIP_COUNT_COMMAND_FILES = (
    "test_phase22_checkpoint.py",
    "test_phase22_dpsgd.py",
    "test_phase22_fakes.py",
    "test_phase23_mps_venue.py",
)


def _venue_summary_text():
    """23-06's SUMMARY, or ``None`` before it is written.

    Same shape as ``tests/test_phase22_fakes.py::_summary_text``: skip gracefully only in the
    window between this file's commit and the plan's metadata commit, then assert hard. A ledger
    that can silently go missing is not a ledger.
    """
    if not _VENUE_SUMMARY_PATH.exists():
        return None
    return _VENUE_SUMMARY_PATH.read_text(encoding="utf-8")


def test_venue_transfer_ledger_is_recorded():
    """Every half of the venue transfer is in the artifact, each as its OWN assertion.

    One assertion per required item deliberately, so a failure names WHICH half went missing. A
    single "the ledger is complete" check would report only that something is wrong, and the thing
    most likely to be dropped by a future edit is the honest half — the phrase about Phase 22's
    CPU-only result, or the blind spots, or the skip count — never the greens.
    """
    text = _venue_summary_text()
    if text is None:
        pytest.skip(
            f"{_VENUE_SUMMARY_PATH.name} is not written yet — it lands with this plan's commit"
        )

    # 1. Phase 22's CPU-only result, named as such and NEVER inherited.
    assert _REQUIRED_TRANSFER_PHRASE in text, (
        f"{_VENUE_SUMMARY_PATH.name} never says {_REQUIRED_TRANSFER_PHRASE!r}. D-02 requires "
        "Phase 22's CPU-only result to be recorded as a result that has NOT crossed to this "
        "venue, beside the MPS observations that did. Without the phrase the artifact reads as if "
        "one battery ran everywhere"
    )
    assert _FORBIDDEN_TRANSFER_PHRASE not in text.lower(), (
        f"{_VENUE_SUMMARY_PATH.name} contains {_FORBIDDEN_TRANSFER_PHRASE!r}. That is the exact "
        "framing D-02 forbids — and it is forbidden even as a quoted denial, because a reader "
        "grepping this artifact cannot distinguish the two"
    )

    # 2. A per-probe row for each of the five things D-02 re-watches, each naming its device.
    for probe in _VENUE_PROBES:
        rows = [
            line
            for line in text.splitlines()
            if line.lstrip().startswith("|") and probe in line and "mps" in line.lower()
        ]
        assert rows, (
            f"{_VENUE_SUMMARY_PATH.name} has no table row naming both {probe!r} and its device. "
            "The ledger is per-probe BY DESIGN: a single aggregate 'all probes pass on MPS' line "
            "is the claim D-02 exists to stop anyone from making"
        )

    # 3. The exemption, stated with its measured count rather than inferred from an absence.
    for literal in ("AST half", "device-invariant"):
        assert literal in text, (
            f"{_VENUE_SUMMARY_PATH.name} never says {literal!r}, so the halves that were NOT "
            "re-run on MPS are recorded nowhere. An exemption inferred from an absence is "
            "indistinguishable from an oversight"
        )
    assert re.search(r"\b53 of (?:the )?\d+\b", text), (
        f"{_VENUE_SUMMARY_PATH.name} does not state the exemption's measured count as '53 of N'. "
        "The count is what makes the exemption checkable — 53 tests out of a named surface, not "
        "'the AST parts'"
    )

    # 4. The skip count, attributable to a command a reader can re-run.
    assert _JUNIT_ATTRS.search(text), (
        f"{_VENUE_SUMMARY_PATH.name} records no observed skip count. pytest omits a zero skip "
        "count from its terminal line, so the count must come from the junit `testsuite` "
        "attributes — a pass count with no skip count beside it is 23-RESEARCH.md's Pitfall 1"
    )
    for filename in _SKIP_COUNT_COMMAND_FILES:
        assert filename in text, (
            f"{_VENUE_SUMMARY_PATH.name} does not name {filename!r} in the command that produced "
            "the recorded counts. A number nobody can regenerate is not a measurement"
        )

    # 5. Both re-measured fitted constants, both readings each, and the deltas.
    for literal in _REQUIRED_CONSTANT_LITERALS:
        assert literal in text, (
            f"{_VENUE_SUMMARY_PATH.name} does not contain {literal!r}. Both fitted constants must "
            "be published with BOTH readings and the delta: 23-RESEARCH.md A1 pre-committed to "
            "re-recording rather than widening, and a re-record that omits one of the two "
            "readings is a widening with extra steps"
        )

    # 6. The 5,056 B / 44 B divergence with both devices named ON THE SAME ROW.
    divergence_rows = [
        line
        for line in text.splitlines()
        if ("5,056" in line or "5056" in line)
        and "44" in line
        and "cpu" in line.lower()
        and "mps" in line.lower()
    ]
    assert divergence_rows, (
        f"{_VENUE_SUMMARY_PATH.name} does not state the 5,056 B / 44 B generator-state divergence "
        "with BOTH devices named on the same line. 22-07-SUMMARY.md prints 5,056 in both columns "
        "because both of its runs were CPU; this assertion exists so that table is not repeated"
    )


def test_the_ledger_states_a_skip_count_of_zero():
    """The recorded skip count is parsed and asserted to be ZERO on this venue.

    **A non-zero skip count here is not a smaller pass — it is the exact failure mode D-02 exists
    to prevent.** Every MPS leg in this phase is ``skipif``-gated so CI can stay green on a
    CPU-only wheel, which means a suite that skipped all of them looks identical to one that ran
    all of them apart from a number pytest does not even print by default. The M3 run is the ONLY
    place that number can be non-zero for a real reason, so it is the only place worth asserting
    it, and the assertion is on the OBSERVED junit attribute rather than on the terminal line.

    ``failures`` and ``errors`` are asserted too. A recorded ``skipped 0`` beside a non-zero
    failure count would be a green venue claim resting on a red run.
    """
    text = _venue_summary_text()
    if text is None:
        pytest.skip(
            f"{_VENUE_SUMMARY_PATH.name} is not written yet — it lands with this plan's commit"
        )

    matches = _JUNIT_ATTRS.findall(text)
    assert len(matches) == 1, (
        f"{_VENUE_SUMMARY_PATH.name} records {len(matches)} junit attribute lines, not exactly "
        "one. Two would leave a reader to guess which run the phase gate is about"
    )
    tests, failures, errors, skipped = (int(v) for v in matches[0])

    assert skipped == 0, (
        f"the recorded venue run skipped {skipped} test(s) of {tests}. Every Phase-23 MPS leg is "
        "skipif-gated, so a non-zero skip count on the M3 means the venue evidence was never "
        "produced — the suite reported green for the legs it did not run. This is the specific "
        "shape of Pitfall 1, and it is why the number is asserted rather than quoted"
    )
    assert failures == 0 and errors == 0, (
        f"the recorded venue run had {failures} failure(s) and {errors} error(s). A skip count of "
        "zero beside a red run is not evidence of a venue pass"
    )
    assert tests > 0, "the recorded venue run collected no tests at all"
