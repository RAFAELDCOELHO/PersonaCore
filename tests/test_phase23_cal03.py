"""CAL-03 — ε does not depend on N at q=1, CONFIRMED BY A RUN and recorded as an artifact.

`.planning/REQUIREMENTS.md` marks *"ε is independent of N at q=1"* as `[INFERENCE]`, and the whole
n=64 capacity rests on it. Three facts shape the instrument, and the first two mean this file is
NOT the test a reader expects from that sentence.

**1. `epsilon_for` TAKES NO N, so this run CANNOT test the math.** Measured here rather than
trusted — `test_epsilon_for_takes_no_n_parameter` asserts the live signature is exactly
``(sigma, steps, delta)``. ε is N-independent BY CONSTRUCTION of the accountant; there is no
parameter for N to enter through. What is left to test, and what actually breaks, is the WIRING:
whether N leaks into the composed step count T.

**2. N REACHES THE LOOP THROUGH TWO INDEPENDENT PATHS, AND BOTH ARE EXERCISED HERE.**
`scripts/teach_persona.py:1352` sets ``grad_accum_steps = stats["n_facts"]`` and
`scripts/teach_persona.py:1376` sets ``replay_windows = replay_window_budget(n_facts) //
BLOCK_SIZE`` — i.e. ``REPLAY_WINDOWS_PER_FACT * n_facts`` windows, which
`training/loop.py:685-700` micro-batches by ceil division at the loop's own ``batch_size``. Either
could reach T, so `_run_capacity` wires BOTH: the accumulation window is ``n_facts`` micro-steps
wide AND the replay pass draws ``4 * n_facts`` windows. A probe that varied only
``grad_accum_steps`` would leave the second path as inference, which is what this plan exists to
retire.

**3. T IS READ FROM THE MECHANISM, NEVER FROM A FIELD.** `_count_composed_steps` (imported from
`tests/test_phase22_checkpoint.py`) is a per-instance shadow of ``DPSGD.finalize`` that counts real
invocations. Its docstring records the mutation that made the obvious version incapable: with
``train()``'s resume assignment of the checkpoint's own ``step`` field mutated to ``0``, that field
still reported **4** while **6** steps composed. An ε read off it is not merely imprecise, it is
OPTIMISTIC — it describes a composition that never ran. Nothing in this file reads that field, and
the subscript form does not appear here at all, so a grep for it returns zero.

REDUCED SCOPE, STATED SO NOBODY MISTAKES THIS FOR A FULL-FIDELITY ARM
--------------------------------------------------------------------
This is a toy ``ModelConfig`` (`_TINY`: block_size 32, 1 layer, 2 heads, n_embd 16) under
``max_steps_override``, on a ``fixed_batch``, exporting no adapter and scoring no question.
`23-04-PLAN.md` records the production shape at ≈3.8 min for one n=8 arm and ≈30.0 min for one
n=64 arm on MPS: a full-length pair costs ~34 minutes to test a property fully expressed in four
optimizer steps. `tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical` already
compares ε at exactly this shape and step count, and `_PROBE_STEPS` is that file's own
``_TOTAL_STEPS`` imported rather than re-typed. MEASURED here: the honest pair costs ~1.3 s on CPU
and ~5.1 s on MPS.

The record this file emits therefore declares ``sweep_point: false`` and ``exports_adapter:
false``, and sits OUTSIDE `phase23_prereg.NOISED_RECORD_GLOB` by design — see that module's own
paragraph on `CAL03_WIRING_RECORD`, and
`tests/test_phase23_prereg.py::test_every_noised_sweep_point_is_under_the_noised_glob`, which makes
that exemption a property of the record's CONTENT rather than of its name.

WHY EXACT ``==`` AND NEVER A TOLERANCE
--------------------------------------
The two arms are the SAME call shape at fixed σ — ``epsilon_for(sigma, T, delta)`` with T counted
from the same mechanism — not two independent mathematics. So a difference is a real difference,
with no double-rounding for a tolerance to absorb, and any tolerance would admit exactly the
wiring leak the check exists to catch. Phase 22 rejected this reasoning once already in DPSGD-05
(`src/personacore/lora/inject.py:113-118`: *"a tolerance would only weaken this"*), and 23-03
committed the same refusal BLIND as `phase23_prereg.n64_leg_is_committable` — whose own
parametrized case pins ``math.nextafter(1.25, math.inf)`` as NOT committable. That ULP case is
what a tolerance actually hides.

The T assertion adds NO detection power — ε is monotone in T at fixed σ, so ε equality already
implies T equality. It is here to name WHERE a leak lives when one fires.

CPU by default; the ε/T pair is measured on BOTH devices in the phase's `_DEVICES` register.
"""

import ast
import inspect
import math
import pathlib
import sys
from collections import namedtuple

import numpy as np
import pytest

from personacore.config import RuntimeConfig, TrainConfig
from personacore.privacy.accountant import epsilon_for
from personacore.training.loop import train

_ROOT = pathlib.Path(__file__).resolve().parent.parent

for _extra_path in (_ROOT / "tests", _ROOT / "scripts"):
    if str(_extra_path) not in sys.path:
        sys.path.insert(0, str(_extra_path))

# The BLIND rule, RESOLVED from 23-03's edit-once module and never re-implemented at a call site.
from phase23_prereg import n64_leg_is_committable  # noqa: E402

# `REPLAY_WINDOWS_PER_FACT` from the production module rather than a literal 4: the second path N
# travels is only rehearsed here if the multiplier is the one production uses.
from teach_persona import REPLAY_WINDOWS_PER_FACT  # noqa: E402

# The Phase-22 fixture register, IMPORTED. `tests/` is not a package, hence the sys.path insert
# above — `tests/test_phase23_prereg.py:31-33` already reaches across files exactly this way. A
# second copy of `_count_composed_steps` would be a second thing to keep true.
from test_phase22_checkpoint import (  # noqa: E402
    _BATCH,
    _DELTA,
    _DP_SEED,
    _MICRO_BS,
    _TINY,
    _TOTAL_STEPS,
    _count_composed_steps,
    _seam,
    _tiny_lora_model,
)

# ONE device register for the whole phase (D-02), imported rather than re-spelled. The `mps` param
# carries its own skipif, so the leg SKIPS in CPU-only CI instead of vanishing from collection.
from test_phase23_mps_venue import _DEVICES  # noqa: E402

# =================================================================================================
# The probe's constants. σ IS PINNED HERE, WITH ITS REASON, BEFORE THE RUN (T-23-22).
# =================================================================================================

# WHY 0.5, and the reason is deliberately not "it produced a passing pair":
#
#   (a) `epsilon_for`'s own docstring gives ``mu_eff = sqrt(steps) / sigma``, so at T = 4 this σ
#       puts the accountant at mu_eff = 4.0 — mid-range, nowhere near the two regimes the module's
#       own reference table pins as hard: the OVERFLOW regime at σ ∈ {0.30, 0.40} / T = 200
#       (`tests/fixtures/phase22_reference.py::EPSILON_OVERFLOW_REGIME`, ε ≈ 775 and ≈ 1311) and
#       the erfc-SUBNORMAL band one cliff below it.
#   (b) It is a value this phase already wrote down BEFORE any CAL-03 number existed:
#       `tests/test_phase23_prereg.py:467` builds its ordering fixture from
#       ``noised_record_path("dp_n64", 0.5)``.
#
# NOT justified by "σ ≥ 0.42 is the well-conditioned regime". 23-04-PLAN.md cites that, but the
# sentence it comes from was RETRACTED IN PLACE on 2026-08-26 at
# `tests/fixtures/phase22_reference.py:243-269`: the error is NOT zero at σ ≥ 0.42, it reaches
# machine epsilon only past σ ≈ 0.425 and is ~1e-16 even there. Citing a retracted claim as the
# reason for a pinned constant is the defect this comment exists to avoid.
_SIGMA = 0.5

# `tests/test_phase22_checkpoint.py`'s own step count, imported. That file's
# `test_resume_epsilon_bit_identical` compares ε at exactly this shape; re-typing 4 here would be a
# second number free to disagree with it.
_PROBE_STEPS = _TOTAL_STEPS

# The two capacities the milestone's frontier is built on (D-06 withdraws the SECOND one only).
_N8, _N64 = 8, 64
_CAPACITIES = (_N8, _N64)

# Enough uint16 elements for `get_batch_memmap_masked` to draw whole `block_size` windows from.
_REPLAY_ELEMENTS = 4096

_Arm = namedtuple("_Arm", "t epsilon")

_THIS_FILE = pathlib.Path(__file__).resolve()
_PREREG_SOURCE = _ROOT / "scripts" / "phase23_prereg.py"
_T_SOURCE = "_count_composed_steps"


# =================================================================================================
# THE ONE VERDICT PRODUCER. Every verdict in this module — the tests', the leak control's and the
# committed record's — comes through here, and here delegates to the rule 23-03 committed BLIND.
# `test_the_verdict_uses_the_blind_committed_rule` asserts by AST that this is the only call site.
# =================================================================================================

_PAIR_KEYS = ("epsilon_n8", "epsilon_n64", "t_n8", "t_n64")


def _pair(arms):
    """The four values D-06's rule judges, keyed exactly as the rule and the record name them."""
    return {
        "epsilon_n8": arms[_N8].epsilon,
        "epsilon_n64": arms[_N64].epsilon,
        "t_n8": arms[_N8].t,
        "t_n64": arms[_N64].t,
    }


def _verdict(*, epsilon_n8, epsilon_n64, t_n8, t_n64):
    """D-06's verdict — DELEGATED, never re-implemented as an inline ``==`` at a call site.

    23-03 committed `n64_leg_is_committable` before any Phase-23 number existed, which is the whole
    reason it is worth calling: a comparison written here, with the numbers on screen, is a
    comparison chosen with the numbers on screen. `scripts/phase19_floor.py`'s property 2.
    """
    return n64_leg_is_committable(
        epsilon_n8=epsilon_n8, epsilon_n64=epsilon_n64, t_n8=t_n8, t_n64=t_n64
    )


# =================================================================================================
# The probe.
# =================================================================================================


def _write_replay_source(directory):
    """A synthetic PersonaChat-shaped replay pair — NEVER the machine-local real one.

    `tests/test_phase21_replay_volume.py:146-155`'s shape. This exists so the SECOND path N travels
    into the loop is actually driven: `replay_fn` micro-batches ``REPLAY_WINDOWS_PER_FACT *
    n_facts`` windows by ceil division at ``batch_size``, so n=64 runs 128 replay micro-batches per
    optimizer step against n=8's 16.
    """
    bin_path = directory / "cal03_replay.bin"
    mask_path = directory / "cal03_replay_mask.bin"
    rng = np.random.default_rng(1337)
    rng.integers(0, _TINY.vocab_size, size=_REPLAY_ELEMENTS, dtype=np.uint16).tofile(bin_path)
    rng.integers(0, 2, size=_REPLAY_ELEMENTS, dtype=np.uint8).tofile(mask_path)
    return bin_path, mask_path


def _run_capacity(n_facts, *, sigma, device, replay, workdir):
    """ONE capacity arm. Returns ``_Arm(t, epsilon)`` with T counted from the MECHANISM."""
    steps = _PROBE_STEPS
    replay_bin, replay_mask_bin = replay

    model = _tiny_lora_model(device=device)
    dp = _seam(model, sigma, _DP_SEED, device)
    composed = _count_composed_steps(dp)

    train(
        train_config=TrainConfig(
            lr=1e-3,
            warmup_steps=0,
            max_steps=steps,
            batch_size=_MICRO_BS,
            # PATH 1 — `teach_persona.py:1352`'s `dict(grad_accum_steps=stats["n_facts"])`.
            grad_accum_steps=n_facts,
        ),
        runtime_config=RuntimeConfig(device=device),
        model=model,
        model_config=_TINY,
        fixed_batch=_BATCH,
        dp_fn=dp,
        # PATH 2 — `teach_persona.py:1376`'s replay budget, in WINDOWS.
        replay_bin=replay_bin,
        replay_mask_bin=replay_mask_bin,
        replay_windows=REPLAY_WINDOWS_PER_FACT * n_facts,
        checkpoint_path=workdir / f"cal03_n{n_facts}_{device}_{steps}.pt",
        max_steps_override=steps,
    )

    # META-GUARD: the run really went through the DP seam at THIS capacity. Without it a run where
    # `dp_fn` was silently dropped would report T = 0 for both arms and pass "bit-identical" while
    # measuring nothing. `tests/test_phase22_checkpoint.py:469` uses the same guard for the same
    # reason.
    assert dp._records == n_facts, (
        f"the DP seam absorbed {dp._records} records on its last step, not {n_facts} — this arm "
        "did not accumulate at the capacity it claims, so nothing below is about n_facts"
    )
    t = len(composed)
    assert t > 0, "the seam composed ZERO steps — `train()` never reached `dp_fn.finalize`"
    return _Arm(t=t, epsilon=epsilon_for(sigma, t, _DELTA))


@pytest.fixture(scope="module")
def _replay_source(tmp_path_factory):
    return _write_replay_source(tmp_path_factory.mktemp("cal03_replay"))


@pytest.fixture(scope="module", params=_DEVICES)
def honest_pair(request, _replay_source, tmp_path_factory):
    """Both capacities at fixed σ, run ONCE per device and shared by every assertion below.

    Module-scoped deliberately: the T assertion and the ε assertion are two readings of ONE pair of
    runs, not two independent experiments. Re-running would let them disagree about which pair they
    are talking about.
    """
    device = request.param
    workdir = tmp_path_factory.mktemp(f"cal03_{device}")
    return device, {
        n: _run_capacity(n, sigma=_SIGMA, device=device, replay=_replay_source, workdir=workdir)
        for n in _CAPACITIES
    }


# =================================================================================================
# The measured premise, then the two detectors.
# =================================================================================================


def test_epsilon_for_takes_no_n_parameter():
    """The premise the whole instrument rests on, ASSERTED against the live signature.

    If `epsilon_for` ever grew an N parameter, "ε is independent of N" would stop being a
    construction fact and this file would silently become a test of a different claim.
    """
    parameters = list(inspect.signature(epsilon_for).parameters)
    assert parameters == ["sigma", "steps", "delta"], (
        f"`epsilon_for` now takes {parameters}. ε being independent of N is a property of THIS "
        "signature — there is no parameter for N to enter through — and every docstring in this "
        "file says so. A fourth parameter makes the claim testable-in-principle and untested-here."
    )


def test_composed_step_count_is_equal_across_capacity(honest_pair):
    """T is EQUAL across capacity, asserted DIRECTLY and against the requested step count."""
    device, arms = honest_pair
    t_n8, t_n64 = arms[_N8].t, arms[_N64].t

    assert t_n8 == t_n64, (
        f"T differs across capacity on {device}: n=8 composed {t_n8} step(s), n=64 composed "
        f"{t_n64}. N HAS LEAKED INTO THE COMPOSED STEP COUNT, and the inequality names where to "
        "look: `grad_accum_steps` (teach_persona.py:1352) and the replay micro-batch count "
        "(loop.py:685-700, ceil(REPLAY_WINDOWS_PER_FACT * n_facts / batch_size)) are the two paths "
        "N travels into this loop. Under D-06 the n=64 leg is WITHDRAWN, not repaired in place."
    )
    assert t_n8 == _PROBE_STEPS, (
        f"both arms composed {t_n8} step(s) but {_PROBE_STEPS} were requested. Equal-but-wrong is "
        "not the property: T must be the step count asked for, or the ε below describes a "
        "composition nobody requested"
    )


def test_epsilon_is_bit_identical_across_capacity(honest_pair):
    """D-05: ε under EXACT ``==`` at fixed σ, both arms finite, verdict from the blind rule.

    The two arms are the SAME call shape — ``epsilon_for(sigma, T, delta)`` with identical
    arguments once T is equal — so equality is the correct assertion and a tolerance would only
    weaken it. That is `lora/inject.py:113-118`'s W1 reasoning, and Phase 22 already rejected the
    tolerance framing once in DPSGD-05.

    `math.isfinite` is asserted on BOTH arms first, because ``inf == inf`` is ``True``: a
    degenerate pair would otherwise pass as "bit-identical" while carrying no ε at all.
    """
    device, arms = honest_pair
    epsilon_n8, epsilon_n64 = arms[_N8].epsilon, arms[_N64].epsilon

    for label, epsilon, arm in (
        (f"n={_N8}", epsilon_n8, arms[_N8]),
        (f"n={_N64}", epsilon_n64, arms[_N64]),
    ):
        assert math.isfinite(epsilon), (
            f"the {label} arm on {device} reported ε = {epsilon!r} at σ = {_SIGMA!r}, T = {arm.t}. "
            "A non-finite pair compares equal under `==` and would pass this test as "
            "'bit-identical' while saying nothing about N"
        )

    assert epsilon_n8 == epsilon_n64, (
        f"ε differs across capacity on {device}: {epsilon_n8!r} (n=8) against {epsilon_n64!r} "
        f"(n=64) at σ = {_SIGMA!r}, T = {arms[_N8].t} / {arms[_N64].t}. `epsilon_for` takes no N, "
        "so the ONLY way these can differ is T — N has leaked into the composed step count."
    )
    assert _verdict(**_pair(arms)) is True, (
        "ε and T are equal but D-06's blind-committed rule did not return True — the rule and this "
        "file disagree about what committable means, which is the one thing calling the rule "
        "instead of comparing inline is supposed to make impossible"
    )


def test_the_verdict_uses_the_blind_committed_rule():
    """ONE code path produces a verdict in this module, and it calls 23-03's blind rule.

    An inline ``epsilon_n8 == epsilon_n64`` written here would be a comparison chosen with the
    numbers on screen — the exact thing `scripts/phase19_floor.py`'s property 2 rules out and the
    reason `n64_leg_is_committable` was committed in wave 1. Asserted structurally, over this
    file's own AST, rather than by trusting the prose above.
    """
    tree = ast.parse(_THIS_FILE.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "n64_leg_is_committable"
    ]
    assert len(calls) == 1, (
        f"{len(calls)} call site(s) for `n64_leg_is_committable` in {_THIS_FILE.name}. Exactly ONE "
        "code path may produce a verdict; a second call site is a second place the rule can be "
        "invoked with different arguments, and nothing would notice the two disagreeing"
    )

    enclosing = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and any(child is calls[0] for child in ast.walk(node))
    ]
    assert enclosing == ["_verdict"], (
        f"the rule is called from {enclosing}, not from `_verdict` alone. The single verdict "
        "producer is what lets every caller below — the tests, the leak control and the committed "
        "record — be checked by inspecting one function"
    )

    source = pathlib.Path(inspect.getsourcefile(n64_leg_is_committable)).resolve()
    assert source == _PREREG_SOURCE.resolve(), (
        f"`n64_leg_is_committable` resolves to {source}, not the edit-once pre-registration at "
        f"{_PREREG_SOURCE}. A same-named local shadow would make 'the rule was committed blind' "
        "true of a function this file never calls"
    )
