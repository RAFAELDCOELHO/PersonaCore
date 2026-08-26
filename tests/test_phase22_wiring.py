"""D-08 wiring: `get_batch_fact_aligned` reaches `train()`, and refuses a mismatched lot.

V-23's loop half and V-14's fact-seam half.

**The measured gap this file closes.** Before Phase 22, `src/personacore/training/loop.py` had
ZERO hits for `fact_bin` / `fact_aligned` / `align_facts`: Phase 21's fact-aligned loader had no
path through `train()` AT ALL, and its only non-test caller was `scripts/phase21_unit_record.py`
— the REPORTING driver. `python scripts/teach_persona.py dp_n8` was CLI-reachable, built the
correct three-bin aligned corpus, and then trained it through the flat random-window loader
UNIT-01 exists to indict, at `grad_accum_steps = 1`.

**The failure this file exists to catch is invisible to every runtime DP invariant.**
`get_batch_fact_aligned` picks its record with `fact_index = step % n_facts`, and its reference
caller advances `step` once per MICRO-step. A seam that hands it one value per OPTIMIZER step
type-checks, runs, converges — and makes every micro-step in the accumulation window draw the
SAME record. At `accum == n_facts` that record is clipped and summed `n_facts` times per step,
so the true per-record sensitivity is `n_facts*C` while the accountant is told `C`. All four
D-16 invariants stay GREEN through it: each drawn record is still individually clipped to `C`,
the drain still fires, the write count is still 1, and the generator still advances.

The Phase-21 aligned-corpus builders are IMPORTED, never re-written — a second copy of the build
recipe is a second thing free to drift from the bins the packer's own proofs run against. Same
for `test_loop_penalty_fn._run_recipe`, which is the recipe the Phase-10 GOLDEN fixture was
captured against.

CPU-only, GPU/MPS-free, no network. Everything under `tmp_path`; nothing writes into `data/`.
Do NOT weaken any assertion to make these pass.
"""

import ast
import itertools
import os
import pathlib
import subprocess
import sys
from dataclasses import asdict

import numpy as np
import pytest
import torch

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.generation import undecodable_ids_mask
from personacore.model import GPT
from personacore.tokenizer import from_json
from personacore.training import data as data_mod
from personacore.training import loop as loop_mod
from personacore.training.loop import train

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "tests"))

import teach_persona as tp  # noqa: E402  (scripts/ is not a package)

from test_loop_penalty_fn import _run_recipe  # noqa: E402  (tests/ is not one either)
from test_phase21_aligned_bins import _aligned_pairs, _build  # noqa: E402

# `block_size` is resolved from the packer, never re-spelled as a literal: the bins are packed
# at tp.BLOCK_SIZE and the loader derives its window count from model_cfg.block_size, so a skew
# between the two would mis-attribute windows to records.
_MODEL_CFG = ModelConfig(block_size=tp.BLOCK_SIZE, n_layer=1, n_head=2, n_embd=16)


def _model(seed=0):
    """A deterministically-initialised TINY GPT (fork_rng so the global stream is untouched).

    Tiny because nothing here measures the model: `n_embd = 16` keeps the token embedding and
    lm_head at ~131k parameters each instead of the bigram's 8192x8192, and every property under
    test is a property of the DATA SEAM.
    """
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return GPT(_MODEL_CFG)


@pytest.fixture(scope="module")
def bins(tmp_path_factory):
    """The REAL 8-fact aligned corpus, built ONCE through the packer (D-01's ragged geometry).

    Nothing in this file mutates the bins, so one module-scoped build is shared. A toy corpus
    would not exercise the ragged window counts (4 or 5 per fact) that make "one micro-step is
    one privacy record" a non-trivial claim about a VARIABLE-size batch.
    """
    base = tmp_path_factory.mktemp("wiring_bins")
    stats, bin_path, mask_path = _build(base, "wiring", episodes=[], align_facts=_aligned_pairs())
    return {
        "tokens": bin_path,
        "mask": mask_path,
        "fact": tp.fact_bin_path(bin_path),
        "n_facts": stats["n_facts"],
        "stats": stats,
    }


class _Spy:
    """A DELEGATING counter around the real loader — never a stand-in for it.

    It calls `data_mod.get_batch_fact_aligned` directly rather than a saved reference, so it can
    be installed over `loop_mod`'s binding without recursing, and so the values it reports are
    the real loader's outputs and not this class's idea of them.

    `forced_index` replaces ONLY the returned `fact_index` (the negative control for the seam's
    per-step refusal); the tensors stay real, so the training step still executes.
    """

    def __init__(self, forced_index=None):
        self.calls = 0
        self.steps = []
        self.indices = []
        self._forced = forced_index

    def __call__(self, *args, **kwargs):
        self.calls += 1
        self.steps.append(kwargs["step"])
        x, y, index = data_mod.get_batch_fact_aligned(*args, **kwargs)
        self.indices.append(int(index))
        return (x, y, index) if self._forced is None else (x, y, self._forced)


def _train(bins, *, steps=1, spy=None, monkeypatch=None, accum=None, n_facts=None, **kwargs):
    """One short CPU run through the fact-aligned seam. Returns the final loss."""
    n = bins["n_facts"] if n_facts is None else n_facts
    if spy is not None:
        monkeypatch.setattr(loop_mod, "get_batch_fact_aligned", spy)
    cfg = TrainConfig(
        lr=1e-3,
        warmup_steps=1,
        max_steps=steps,
        batch_size=2,
        grad_accum_steps=n if accum is None else accum,
    )
    call = {
        "train_bin": bins["tokens"],
        "train_mask_bin": bins["mask"],
        "fact_bin": bins["fact"],
        "n_facts": n,
    }
    call.update(kwargs)
    return train(
        train_config=cfg,
        runtime_config=RuntimeConfig(device="cpu"),
        model=_model(),
        model_config=_MODEL_CFG,
        max_steps_override=steps,
        return_final_loss=True,
        **call,
    )


# ===================================================================================
# ===== V-14, the fact-seam half: the seam is INERT when off ========================
# ===================================================================================


def test_fact_bin_none_is_inert(tmp_path):
    """Omitting `fact_bin`/`n_facts` is bitwise identical to passing both as `None`.

    Runs the recipe the Phase-10 GOLDEN fixture was captured against (imported, not re-written)
    and compares all THREE fingerprints: exact CSV text, the final loss's `repr`, and the sha256
    of the parameter bytes. This test reads no platform identity and never skips, so it carries
    the DPSGD-02 guarantee for the fact seam everywhere — including the CI boxes where
    `test_loop_penalty_fn.py`'s golden replay is gated off.
    """
    omitted = _run_recipe(tmp_path / "omitted.csv")
    explicit_none = _run_recipe(tmp_path / "none.csv", fact_bin=None, n_facts=None)

    assert omitted == explicit_none  # (csv_text, final_loss_repr, param_sha256), all bitwise
    # Non-degeneracy: a comparison of two empty/constant things would pass identically.
    assert omitted[0].count("\n") > 1, omitted[0]
    assert len(omitted[2]) == 64 and int(omitted[2], 16) != 0


# ===================================================================================
# ===== The routing: the seam reaches the REAL loader, n_facts times per step =======
# ===================================================================================


def test_fact_bin_routes_to_the_aligned_loader(bins, monkeypatch):
    """One optimizer step at `grad_accum_steps = n_facts` calls the loader exactly `n_facts`
    times, and the `fact_index` values it returns are exactly `set(range(n_facts))`.

    The zero-call control is not decorative: without it, a spy that never fires (installed on
    the wrong module binding, or a seam that silently fell through to the mask branch) would
    make every positive assertion here vacuous.
    """
    n = bins["n_facts"]
    assert n > 1, "a single-record corpus cannot distinguish per-record from per-lot draws"

    on = _Spy()
    _train(bins, steps=1, spy=on, monkeypatch=monkeypatch)
    assert on.calls == n, f"{on.calls} loader calls for {n} micro-steps"
    assert set(on.indices) == set(range(n))
    assert sorted(on.indices) == list(range(n)), on.indices  # each record EXACTLY once

    # THE CONTROL. Same spy class, same recipe, seam OFF -> the aligned loader is never reached.
    off = _Spy()
    monkeypatch.setattr(loop_mod, "get_batch_fact_aligned", off)
    train(
        train_config=TrainConfig(lr=1e-3, warmup_steps=1, max_steps=1, batch_size=2),
        runtime_config=RuntimeConfig(device="cpu"),
        model=_model(),
        model_config=_MODEL_CFG,
        train_bin=bins["tokens"],
        train_mask_bin=bins["mask"],
        max_steps_override=1,
    )
    assert off.calls == 0, "the flat/masked path must not touch the fact-aligned loader"


def test_the_spy_must_be_installed_on_the_loop_binding_not_the_data_module(bins, monkeypatch):
    """META-GUARD: patching `personacore.training.data` alone does NOT reach `train()`.

    `loop.py` binds the loader with `from .data import ... get_batch_fact_aligned`, so the name
    it calls is `loop.get_batch_fact_aligned`. A spy installed on `data.get_batch_fact_aligned`
    is never consulted — the run still completes, the counting assertions above would measure
    NOTHING, and the constant-`fact_index` negative control below would silently fail to inject.

    This is asserted rather than assumed because the plan for this file specified the `data`
    target, and "patch where it is looked up" is the kind of rule a future edit re-breaks.
    """
    assert loop_mod.get_batch_fact_aligned is data_mod.get_batch_fact_aligned

    wrong = _Spy()
    monkeypatch.setattr(data_mod, "get_batch_fact_aligned", wrong)
    _train(bins, steps=1)  # no spy installed on loop_mod
    assert wrong.calls == 0, (
        "patching the data module reached the loop — if this ever becomes true the loop stopped "
        "using a from-import and the `loop_mod` patch target above should be re-checked"
    )


def test_step_counter_is_global_and_monotonic(bins, monkeypatch):
    """TWO optimizer steps produce `2 * n_facts` DISTINCT, strictly increasing `step=` values.

    This is the assertion that separates a correct wiring from one that silently trains a lot of
    size 1. A future reader can identify a red by its shape:

    * `step=_fact_cursor["step"]` (the bare OPTIMIZER step) -> `[S]*n_facts` then `[S+1]*n_facts`.
      `fact_index` is CONSTANT within a window, so ONE record is clipped and summed `n_facts`
      times per optimizer step: true per-record sensitivity `n_facts*C` against an accountant
      told `C`, with every D-16 invariant still green.
    * `step=micro` alone -> `[0..n_facts-1]` twice. Distinct WITHIN a window, but the two windows
      COLLIDE, so the run never advances past the first lot of records.

    Both are silent without this test. Both are caught here: the first by distinctness within a
    window, the second by the two windows being disjoint.
    """
    n = bins["n_facts"]
    spy = _Spy()
    _train(bins, steps=2, spy=spy, monkeypatch=monkeypatch)

    start_step = 0  # a fresh run; train() sets step = start_step = 0 with no resume_from
    assert spy.steps == list(range(start_step * n, (start_step + 2) * n)), spy.steps
    assert len(set(spy.steps)) == 2 * n
    assert spy.steps == sorted(spy.steps) and len(set(spy.steps)) == len(spy.steps)

    first, second = spy.steps[:n], spy.steps[n:]
    assert not (set(first) & set(second)), "the two accumulation windows must be DISJOINT"
    # And the records each window covers are the full set, once — the property the sensitivity
    # claim rests on, read from the loader's own returned index rather than from the counter.
    assert sorted(spy.indices[:n]) == list(range(n))
    assert sorted(spy.indices[n:]) == list(range(n))


# ===================================================================================
# ===== The two refusals ============================================================
# ===================================================================================


def test_fact_bin_requires_its_companions(bins):
    """Each incomplete combination raises, and the three messages are PAIRWISE DISTINCT.

    Distinctness is the property that makes a red identifiable by which guard fired rather than
    by "a ValueError occurred" — the `data.py:112-116` register this seam copies.
    """
    cfg = TrainConfig(max_steps=1, grad_accum_steps=bins["n_facts"])
    common = {"train_config": cfg, "runtime_config": RuntimeConfig(device="cpu")}
    cases = {
        "fact_bin without n_facts": {
            "train_bin": bins["tokens"],
            "train_mask_bin": bins["mask"],
            "fact_bin": bins["fact"],
        },
        "fact_bin without train_mask_bin": {
            "train_bin": bins["tokens"],
            "fact_bin": bins["fact"],
            "n_facts": bins["n_facts"],
        },
        "n_facts without fact_bin": {
            "train_bin": bins["tokens"],
            "train_mask_bin": bins["mask"],
            "n_facts": bins["n_facts"],
        },
    }
    messages = {}
    for name, kwargs in cases.items():
        with pytest.raises(ValueError) as excinfo:
            train(**common, **kwargs)
        messages[name] = str(excinfo.value)
        assert "D-08" in messages[name]
        assert "cannot be defaulted" in messages[name] or "CANNOT be defaulted" in messages[name]

    for (an, am), (bn, bm) in itertools.combinations(messages.items(), 2):
        assert am != bm, f"{an!r} and {bn!r} raise the SAME message — a red is unidentifiable"

    # The complete combination is accepted — otherwise every raise above could be a blanket
    # refusal of the seam rather than a refusal of the INCOMPLETE seam.
    assert _train(bins, steps=1) is not None


def test_n_facts_must_be_a_positive_int(bins):
    """`n_facts` is the lot size the accountant is told; a bool/float/<=0 is not a lot."""
    for bad in (0, -1, True, 2.0, "8"):
        with pytest.raises(ValueError, match="positive int"):
            train(
                train_config=TrainConfig(max_steps=1),
                runtime_config=RuntimeConfig(device="cpu"),
                train_bin=bins["tokens"],
                train_mask_bin=bins["mask"],
                fact_bin=bins["fact"],
                n_facts=bad,
            )


def test_accum_must_equal_n_facts(bins):
    """`grad_accum_steps != n_facts` raises, and the message names the measured 9/0 gap.

    Positive control: the MATCHING configuration runs to completion, so the refusal is a refusal
    of the disagreement and not of the seam.
    """
    n = bins["n_facts"]
    with pytest.raises(ValueError) as excinfo:
        _train(bins, steps=1, accum=1)  # TrainConfig's default — the production configuration
    message = str(excinfo.value)
    assert "13 times" in message and "exactly 1" in message
    assert "teach_persona" in message
    assert "one micro-step IS one privacy record" in message.replace("ONE", "one")
    assert f"n_facts={n}" in message

    # A DIFFERENT disagreement in the other direction, so the check is an equality and not a
    # ">= 1" that a larger accumulation window would slip through.
    with pytest.raises(ValueError, match="disagrees with"):
        _train(bins, steps=1, accum=n + 1)

    assert _train(bins, steps=1, accum=n) is not None  # the positive control


@pytest.mark.parametrize("arm", tp.DP_ARMS)
def test_the_production_default_accum_is_refused_at_the_real_fact_count(arm):
    """MEASURED: every real DP arm has `n_facts > 1`, so the refusal forces `accum > 1`.

    This is load-bearing for DETECTABILITY, not merely for SC2's prose. Plan 22-06 measured that
    D-02's inherited-divide fake (the lot divide inherited rather than applied) is STRUCTURALLY
    INVISIBLE at `grad_accum_steps = 1`, because `total / 1` is `total` exactly.
    `TrainConfig.grad_accum_steps` DEFAULTS to 1. With this refusal in place the aligned path
    cannot run at that default for any real arm, so the fake stays detectable downstream.

    No corpus is needed: the refusal fires before `train()` opens any file.
    """
    facts, _second_person, _replay_ratio = tp.arm_spec(arm)
    n_facts = len(facts)
    assert n_facts > 1, f"{arm} declares {n_facts} record(s) — the D-02 fake is invisible there"
    assert TrainConfig().grad_accum_steps == 1  # the default the production caller inherits

    with pytest.raises(ValueError, match="disagrees with"):
        train(
            train_config=TrainConfig(max_steps=1),  # accum defaults to 1
            runtime_config=RuntimeConfig(device="cpu"),
            train_bin="unused.bin",
            train_mask_bin="unused_mask.bin",
            fact_bin="unused_fact.bin",
            n_facts=n_facts,
        )


def _accum_code_hits(tree, *, constants=True):
    """`grad_accum_steps` occurrences that are CODE, not prose.

    `constants=False` is the PRE-22-10 predicate, kept as a live negative control rather than
    deleted — see `test_the_prose_vs_code_measurement_is_still_true` for what it is blind to.
    """
    hits = [
        node
        for node in ast.walk(tree)
        if (isinstance(node, ast.keyword) and node.arg == "grad_accum_steps")
        or (isinstance(node, ast.Attribute) and node.attr == "grad_accum_steps")
        or (isinstance(node, ast.Name) and node.id == "grad_accum_steps")
    ]
    if constants:
        # A DICT KEY. `{"grad_accum_steps": ...}` is an `ast.Constant`, and a string constant
        # whose value is EXACTLY the identifier can only be a key or an equally deliberate
        # reference — the prose hits all embed the word inside a longer sentence, so this
        # predicate cannot pick one up. Verified by the `> 1` filter never being needed.
        hits += [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value == "grad_accum_steps"
        ]
    return hits


def test_the_prose_vs_code_measurement_is_still_true():
    """The accum refusal's message states a MEASUREMENT; this re-measures it on every run.

    A measured claim baked into a production error message goes stale silently. Plan 22-08 wrote
    it as 9 textual / 0 code — every hit inside a docstring, a comment or an error string — and
    predicted plan 22-10 would legitimately turn it red. It did. **The number in `loop.py` was
    UPDATED, not the test deleted**, and the current measurement is 13 textual / 1 code.

    **The finding that came with the red, and the reason this test grew a helper.** 22-10 wires
    the caller through a SPLAT — `{"grad_accum_steps": stats["n_facts"]} if is_dp else {}` — so
    the one code hit is a DICT KEY, an `ast.Constant`. Measured: the pre-22-10 predicate
    (`keyword` / `Attribute` / `Name` only) still returns **0** against the wired file. Left
    alone it would have kept reporting "0 code hits" for a caller that DOES set the value —
    a detector blind to the exact form the production path uses, at the one measurement a user
    reads while debugging a privacy claim. The meta-guard below pins that blindness so a future
    edit cannot silently re-narrow the predicate.
    """
    source = pathlib.Path(tp.__file__).read_text()
    textual = source.count("grad_accum_steps")
    tree = ast.parse(source)
    code_hits = _accum_code_hits(tree)

    assert (textual, len(code_hits)) == (13, 1), (
        f"the measurement in loop.py's accum-agreement refusal is STALE: measured "
        f"{textual} textual / {len(code_hits)} code hits, message says 13 / 1. Update the "
        "message in src/personacore/training/loop.py to the new numbers — do not delete this "
        "test and do not leave a false number in a message a user reads while debugging a "
        "privacy claim."
    )

    # THE META-GUARD. The old predicate is blind to the shipped wiring; asserted, not assumed.
    assert _accum_code_hits(tree, constants=False) == [], (
        "the pre-22-10 predicate now finds a hit — the caller stopped wiring grad_accum_steps "
        "through a dict-key splat. Re-check the (13, 1) numbers above and loop.py's message."
    )
    # And the widened predicate found the splat key specifically, not some prose string.
    assert isinstance(code_hits[0], ast.Constant)
    assert 'dp_accum = {"grad_accum_steps"' in source.splitlines()[code_hits[0].lineno - 1]


# ===================================================================================
# ===== One micro-step IS one privacy record (Phase 21 D-02) ========================
# ===================================================================================


def test_every_fact_contributes_exactly_once(bins, monkeypatch):
    """The happy path completes and every record contributes EXACTLY once, per optimizer step.

    Then the negative control: the loader is made to return a CONSTANT `fact_index` and the
    seam's per-step refusal must fire. Without that control the property could be true because
    the check is ABSENT rather than because the loader is correct — which is the whole failure
    class this phase exists to close.
    """
    n = bins["n_facts"]
    spy = _Spy()
    _train(bins, steps=2, spy=spy, monkeypatch=monkeypatch)
    for window in range(2):
        drawn = spy.indices[window * n : (window + 1) * n]
        assert sorted(drawn) == list(range(n)), (window, drawn)

    # THE NEGATIVE CONTROL. Real tensors, constant index -> sorted(seen) == [0]*n != range(n).
    liar = _Spy(forced_index=0)
    with pytest.raises(ValueError) as excinfo:
        _train(bins, steps=1, spy=liar, monkeypatch=monkeypatch)
    message = str(excinfo.value)
    assert "not one privacy record" in message.replace("NOT", "not")
    assert "D-02" in message
    assert liar.calls == n, "the refusal must fire AFTER the full window, not on the first draw"


def test_a_duplicated_record_is_refused(bins, monkeypatch):
    """A SECOND violation shape: one record drawn twice, another never.

    The constant-index control above is the degenerate case (every micro-step on record 0); this
    is the near-miss, where `n_facts - 1` of the records are correct.

    **A claim this test deliberately does NOT make.** The seam checks the MULTISET
    (`sorted(seen) == list(range(n_facts))`). A first draft's docstring said that was STRONGER
    than set equality here. It is not, and the mutation probe measured it: swapping the seam's
    multiset check for `set(seen) != set(range(n_facts))` leaves this entire suite GREEN. The
    accum-agreement refusal pins `len(seen) == n_facts`, and `n` draws whose SET is `range(n)`
    are necessarily distinct — so the two forms are provably equivalent under the shipped
    refusals. The multiset form ships as the shape that survives a future relaxation of that
    refusal, not as a detector that bites harder. `len(spy.indices) == n` below pins the premise
    that equivalence rests on.
    """
    n = bins["n_facts"]

    class _Duplicating(_Spy):
        def __call__(self, *args, **kwargs):
            x, y, index = super().__call__(*args, **kwargs)
            return (x, y, 0) if index == n - 1 else (x, y, index)

    spy = _Duplicating()
    with pytest.raises(ValueError, match="privacy record"):
        _train(bins, steps=1, spy=spy, monkeypatch=monkeypatch)
    assert sorted(spy.indices) == list(range(n))  # what the REAL loader returned
    assert len(spy.indices) == n  # the accum refusal's consequence, and the equivalence premise


# ===================================================================================
# ===== D-08 / T-22-49: sigma and C are REQUIRED, with NO DEFAULT anywhere ==========
# ===================================================================================


def test_dp_arm_requires_sigma_and_clip_norm(monkeypatch):
    """Every incomplete DP invocation raises, and the message names BOTH flag names.

    `train_arm` is stubbed to a sentinel that RAISES, so a case that wrongly got past the CLI is
    a loud, distinguishable failure rather than an attempt to run a real 200-step training job.
    """

    def _never(*args, **kwargs):
        raise AssertionError(f"train_arm reached the training half with {kwargs!r}")

    monkeypatch.setattr(tp, "train_arm", _never)

    for arm in tp.DP_ARMS:
        for argv in (
            [arm],  # neither flag
            [arm, f"{tp.SIGMA_FLAG}1.0"],  # sigma alone
            [arm, f"{tp.CLIP_FLAG}1.0"],  # C alone
            [arm, f"{tp.SIGMA_FLAG}1.0", f"{tp.CLIP_FLAG}1.0", "--extra"],  # unknown token
            [arm, f"{tp.SIGMA_FLAG}abc", f"{tp.CLIP_FLAG}1.0"],  # unparseable
            [arm, f"{tp.SIGMA_FLAG}1.0", f"{tp.SIGMA_FLAG}2.0"],  # duplicate
        ):
            with pytest.raises(SystemExit) as excinfo:
                tp.main(argv)
            message = str(excinfo.value)
            assert tp.SIGMA_FLAG in message and tp.CLIP_FLAG in message, (argv, message)
            # The message says WHY there is no default, not merely that one is missing.
            assert "Z boundary" in message and "NO DEFAULT" in message, (argv, message)

    # The DOMAIN refusals, which the mechanism re-checks as properties of itself.
    for argv, needle in (
        ([tp.DP_ARMS[0], f"{tp.SIGMA_FLAG}-1.0", f"{tp.CLIP_FLAG}1.0"], "sigma-domain"),
        ([tp.DP_ARMS[0], f"{tp.SIGMA_FLAG}1.0", f"{tp.CLIP_FLAG}0"], "clip-domain"),
        ([tp.DP_ARMS[0], f"{tp.SIGMA_FLAG}1.0", f"{tp.CLIP_FLAG}-2"], "clip-domain"),
    ):
        with pytest.raises(SystemExit, match=needle):
            tp.main(argv)

    # POSITIVE CONTROL: a well-formed invocation gets PAST the CLI and into `train_arm` with
    # both values parsed. Without it every raise above could be a blanket refusal of the arm.
    reached = {}
    monkeypatch.setattr(tp, "train_arm", lambda arm, **kw: reached.update(arm=arm, **kw))
    tp.main([tp.DP_ARMS[0], f"{tp.SIGMA_FLAG}1.25", f"{tp.CLIP_FLAG}0.5"])
    assert (reached["dp_sigma"], reached["dp_clip_norm"]) == (1.25, 0.5)

    # ...and in EITHER order, since the parser is prefix matching and not positional.
    reached.clear()
    tp.main([tp.DP_ARMS[0], f"{tp.CLIP_FLAG}0.5", f"{tp.SIGMA_FLAG}1.25"])
    assert (reached["dp_sigma"], reached["dp_clip_norm"]) == (1.25, 0.5)


def test_the_dp_refusal_also_fires_at_train_arm_not_only_at_the_cli():
    """T-22-49 is a property of the TRAINING ENTRY POINT, not of one argv parser.

    `train_arm` has five callers outside this module (`phase17_isolation`, `phase19_erasure` x3,
    `phase19_run`) plus `run_calibration` here, none of which goes through `main`. A refusal that
    lived only in the CLI would let any of them train a DP-named arm with no sigma and no C.
    """
    for arm in tp.DP_ARMS:
        with pytest.raises(SystemExit, match="Z boundary"):
            tp.train_arm(arm, facts=[], family_ids=())


def test_non_dp_arm_cli_is_unchanged(monkeypatch):
    """THE CONTROL: the new DP branch did not narrow the pre-existing single-token path.

    A non-DP arm is accepted with exactly one token and still rejected with two — the same shape
    `len(argv) != 1` enforced before plan 22-10 — and it reaches `train_arm` with both DP
    parameters `None`, so nothing about its `train()` call can differ.
    """
    non_dp = [arm for arm in tp.ARMS if arm not in tp.DP_ARMS]
    assert non_dp, "ARMS carries no non-DP arm — this control would be vacuous"

    seen = []
    monkeypatch.setattr(tp, "train_arm", lambda arm, **kw: seen.append((arm, kw)))
    monkeypatch.setattr(tp, "arm_spec", lambda arm: ([], False, 0.0))

    for arm in non_dp:
        tp.main([arm])  # must NOT raise
    assert [arm for arm, _kw in seen] == non_dp
    assert all(kw["dp_sigma"] is None and kw["dp_clip_norm"] is None for _arm, kw in seen)

    # Extra tokens are still refused on the non-DP path, including the DP flags.
    for argv in ([non_dp[0], "--force"], [non_dp[0], f"{tp.SIGMA_FLAG}1.0"], []):
        with pytest.raises(SystemExit) as excinfo:
            tp.main(argv)
        assert str(excinfo.value) == tp.USAGE, argv


def test_usage_lists_the_dp_form():
    """`USAGE` names every DP arm and both flags, read from the module rather than re-spelled."""
    assert tp.DP_ARMS, "DP_ARMS is empty — this test would be vacuous"
    for arm in tp.DP_ARMS:
        assert arm in tp.USAGE
    assert tp.SIGMA_FLAG in tp.USAGE and tp.CLIP_FLAG in tp.USAGE
    # Built by interpolation, not hand-typed: the joined form must appear verbatim.
    assert "|".join(tp.DP_ARMS) in tp.USAGE
    assert "|".join(tp.ARMS) in tp.USAGE


def test_cli_names_no_sigma_or_clip_value():
    """T-22-49, STATIC: no numeric literal is bound to any sigma/clip name in this file.

    A default anywhere would silently become the operating privacy budget of a run nobody
    pre-registered. This walks every `Assign` / `AnnAssign` / `keyword` / default and every dict
    entry, and refuses a numeric `Constant` reaching a name containing `sigma` or `clip`.
    """
    source = pathlib.Path(tp.__file__).read_text()
    tree = ast.parse(source)

    def _is_number(node):
        return isinstance(node, ast.Constant) and isinstance(node.value, (int, float))

    def _suspect(name):
        lowered = name.lower()
        return "sigma" in lowered or "clip" in lowered

    assigns = [n for n in ast.walk(tree) if isinstance(n, (ast.Assign, ast.AnnAssign))]
    assert len(assigns) > 1, "the AST walk found no Assign nodes — the guard would be vacuous"

    offenders = []
    for node in assigns:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if node.value is not None and _is_number(node.value):
            offenders += [(n, node.lineno) for n in names if _suspect(n)]
    for node in ast.walk(tree):
        # Keyword arguments: `DPSGD(sigma=1.1, ...)` and `train_arm(dp_sigma=0.5)`.
        if isinstance(node, ast.keyword) and node.arg and _suspect(node.arg):
            if _is_number(node.value):
                offenders.append((node.arg, node.lineno))
        # Dict literals: `{"sigma": 1.1}`.
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if _suspect(key.value) and _is_number(value):
                        offenders.append((key.value, key.lineno))
        # Parameter defaults: `def f(*, sigma=1.1)`.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            pairs = (
                list(zip(args.args[-len(args.defaults) :], args.defaults)) if args.defaults else []
            )
            pairs += [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None]
            for arg, default in pairs:
                if _suspect(arg.arg) and _is_number(default):
                    offenders.append((arg.arg, node.lineno))

    assert offenders == [], (
        f"a numeric sigma/clip value is bound in {tp.__file__}: {offenders}. Phase 22 names no "
        "value in its tree — a default here would become the operating privacy budget."
    )

    # META-GUARD: the walk is capable of finding one. Inject the shape it must catch.
    injected = ast.parse('def f(*, sigma=1.1):\n    pass\nCLIP_NORM = 0.5\nd = {"sigma": 2.0}\n')
    found = []
    for node in ast.walk(injected):
        if isinstance(node, ast.Assign) and _is_number(node.value):
            found += [t.id for t in node.targets if isinstance(t, ast.Name) and _suspect(t.id)]
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and _suspect(str(key.value)) and _is_number(value):
                    found.append(key.value)
        if isinstance(node, ast.FunctionDef):
            for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
                if default is not None and _suspect(arg.arg) and _is_number(default):
                    found.append(arg.arg)
    assert sorted(found) == ["CLIP_NORM", "sigma", "sigma"], found


def test_the_cli_does_not_use_argparse():
    """`main` stays in this file's argv-slicing register — a second CLI idiom is a trap.

    Asserted by AST rather than by `grep -n argparse`, which the plan proposed: the grep cannot
    tell a USE from `_parse_dp_flags`' docstring naming the rejected alternative, so it would
    have to be satisfied by deleting the one sentence a future reader most needs.
    """
    tree = ast.parse(pathlib.Path(tp.__file__).read_text())
    imported = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ] + [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert "argparse" not in imported, imported
    attributes = {
        node.value.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
    }
    assert "argparse" not in attributes
    assert not hasattr(tp, "argparse")


# ===================================================================================
# ===== V-23 — the END-TO-END CPU run, through main(), writing NO scored artifact ====
# ===================================================================================

# Fixture sigma and C for the end-to-end run. **These are TEST FIXTURES, NOT A BUDGET.** They
# exist so the no-default CLI contract can be exercised end to end and they are chosen here, in
# the test, precisely so no value is committed anywhere Phase 23 could inherit it. Phase 23
# supplies the operating values from `scripts/mitigation_budget.py` under Phase 20's Z boundary.
_FIXTURE_SIGMA = 1.0
_FIXTURE_CLIP = 1.0

_E2E_CFG = ModelConfig(block_size=tp.BLOCK_SIZE, n_layer=1, n_head=2, n_embd=16)


def _e2e_env(root, monkeypatch):
    """Point every `teach_persona` input and output at `root`, at fixture scale, on CPU.

    Scaling is done by monkeypatching the module's OWN shape constants — the same handles
    `tests/test_phase14_teaching.py::test_recipe_constants` pins — rather than by a second
    scaling mechanism. `block_size` is NOT scaled: the packer packs at `tp.BLOCK_SIZE` and the
    aligned loader derives its window count from `model_cfg.block_size`, so a skew between them
    would mis-attribute windows to privacy records.

    `_REPO_ROOT` is read at CALL time by `arm_outputs`, so re-pointing it redirects the bin,
    mask, fact-bin, csv, checkpoint and adapter targets in one line. `TOKENIZER_PATH` is resolved
    at IMPORT time and is deliberately left alone: the run uses the real FROZEN tokenizer.
    """
    for sub in ("data", "checkpoints", "results"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(0)
        base = GPT(_E2E_CFG)
    convbase = root / "convbase.pt"
    torch.save(
        {
            "model_config": asdict(_E2E_CFG),
            "model": base.state_dict(),
            "git_sha": "0" * 40,
            "step": 7,
            "val_loss": 1.234,
        },
        convbase,
    )

    # DECODABLE ids only. The frozen tokenizer decodes 547 of the model's 8192 ids, and
    # `train_arm` scores its collateral-collapse sweep with `forbid_ids=undecodable_ids_mask(...)`;
    # a dead target id would send the perplexity to inf and make the endpoint numbers unreadable.
    live = torch.nonzero(~undecodable_ids_mask(from_json(tp.TOKENIZER_PATH), 8192)[0]).flatten()
    rng = np.random.default_rng(0)

    def _pair(stem, windows):
        n = windows * tp.BLOCK_SIZE + 1  # + 1: get_batch_memmap_masked needs a shifted target
        ids = rng.choice(live.numpy(), size=n).astype(np.uint16)
        bin_path, mask_path = root / "data" / f"{stem}.bin", root / "data" / f"{stem}_mask.bin"
        ids.tofile(bin_path)
        np.ones(n, dtype=np.uint8).tofile(mask_path)
        return bin_path, mask_path

    report = root / "factset.md"
    report.write_text("# fixture\n\n## Verdict\n\nGO\n", encoding="utf-8")

    monkeypatch.setattr(tp, "_REPO_ROOT", root)
    monkeypatch.setattr(tp, "FACTSET_REPORT", report)
    monkeypatch.setattr(tp, "CONVBASE_BEST", convbase)
    val_bin, val_mask = _pair("dialog_val", 3)
    monkeypatch.setattr(tp, "DIALOG_VAL_BIN", val_bin)
    monkeypatch.setattr(tp, "DIALOG_VAL_MASK", val_mask)
    replay_bin, replay_mask = _pair("dialog_train", 4)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_BIN", replay_bin)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_MASK", replay_mask)

    # TWO steps, not one, and the reason is a MEASUREMENT rather than caution. LoRA initialises
    # `lora_B` to zeros and `dL/dA` carries a factor of `B`, so at step 0 every `lora_A` gradient
    # is exactly 0.0 and AdamW leaves it where it was — `train_arm`'s canary then correctly raises
    # "[canary] trainable ... did not move". Watched: the DP arm passes that canary at ONE step
    # and the non-DP arm does not, because the DP path adds noise to EVERY parameter's gradient,
    # so `lora_A` moves on pure noise. Two steps makes both arms legitimate for the same reason.
    monkeypatch.setattr(tp, "MAX_STEPS", 2)
    monkeypatch.setattr(tp, "WARMUP_STEPS", 1)
    monkeypatch.setattr(tp, "BATCH_SIZE", 1)
    monkeypatch.setattr(tp, "EVAL_INTERVAL", 1)
    monkeypatch.setattr(tp, "CHECKPOINT_INTERVAL", 1)

    # CPU, explicitly. `preflight_device(strict=True)` returns MPS on the dev box and RAISES on a
    # CPU-only CI runner, so both are replaced: this test must run identically on both.
    monkeypatch.setattr(
        tp,
        "preflight_device",
        lambda strict=True: {"device": "cpu", "cc": None, "torch": torch.__version__},
    )
    monkeypatch.setattr(tp, "RuntimeConfig", lambda: RuntimeConfig(device="cpu"))


def _results_state():
    """The two fingerprints of the REAL `results/` tree — listing plus git's own view."""
    listing = sorted(os.listdir(_ROOT / "results"))
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "results/"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return listing, porcelain


def test_end_to_end_writes_no_scored_artifact(tmp_path, monkeypatch):
    """V-23: `main(['dp_n8', '--sigma=…', '--clip-norm=…'])` completes and `results/` is untouched.

    **Why this test exists at all (D-08's load-bearing reason).** Phase 23's FIRST ACT IS A
    MEASUREMENT. If the four wirings landed there, its first executed run would simultaneously be
    the first test of four never-executed integration paths, and a wiring bug and a DP-correctness
    bug would arrive in the same artifact, indistinguishable — destroying DPSGD-06's purpose.

    **Why each wiring gets its OWN observation.** A test that only asserted "it did not crash"
    would pass with three of four paths silently unwired, which is precisely the Phase-21 IN-04
    failure this plan exists to prevent. So: a delegating spy on the loader, the `grad_accum_steps`
    read off the `TrainConfig` that was actually constructed, `replay_windows` compared against
    `replay_window_budget` rather than against a literal, and `dp_fn._records` read after the run.

    **On `results/`.** D-08's boundary is that Phase 22 writes NO scored artifact. This is also
    why `results/phase22_*` was deliberately NOT added to `V4_ARTIFACT_GLOBS` (plan 22-02): arming
    a prefix that never matches ships a guard vacuous by construction.
    """
    before = _results_state()
    assert before[0], "results/ is empty — the byte-identity assertion below would be vacuous"

    _e2e_env(tmp_path, monkeypatch)
    loader = _Spy()
    monkeypatch.setattr(loop_mod, "get_batch_fact_aligned", loader)

    seen = {}
    real_train = tp.train

    def _spy_train(**kwargs):
        seen.update(kwargs)
        return real_train(**kwargs)

    monkeypatch.setattr(tp, "train", _spy_train)

    tp.main(["dp_n8", f"{tp.SIGMA_FLAG}{_FIXTURE_SIGMA}", f"{tp.CLIP_FLAG}{_FIXTURE_CLIP}"])

    # ---- 1. results/ is byte-identical, by BOTH fingerprints -------------------------------
    assert _results_state() == before

    # ---- 2. the run COMPLETED ---------------------------------------------------------------
    paths = tp.arm_outputs("dp_n8", prefix="phase21")
    assert paths["checkpoint"].exists() and paths["adapter"].exists()
    csv_rows = paths["csv"].read_text(encoding="utf-8").strip().splitlines()
    assert len(csv_rows) > 1, csv_rows  # a header alone is a run that logged nothing
    # ...and the bins really are the three-bin aligned pack, under tmp_path and nowhere else.
    assert tp.fact_bin_path(paths["bin"]).exists()
    assert tmp_path in paths["adapter"].parents

    # ---- 3. all FOUR paths executed, each by its own observation ----------------------------
    n_facts = len(tp.arm_spec("dp_n8")[0])
    assert n_facts > 1, "a one-record arm makes the accum observation below meaningless"

    # (1) fact-aligned routing: the REAL loader fired, once per record per OPTIMIZER STEP, each
    #     accumulation window covering every record exactly once. Both counts are read from the
    #     module's own constants, so a future scale change cannot make this assertion vacuous.
    assert loader.calls == tp.MAX_STEPS * n_facts, f"{loader.calls} calls, {n_facts} records"
    for window in range(tp.MAX_STEPS):
        drawn = loader.indices[window * n_facts : (window + 1) * n_facts]
        assert sorted(drawn) == list(range(n_facts)), (window, drawn)
    assert len(set(loader.steps)) == loader.calls, "the step counter collapsed onto one lot"

    # (2) grad_accum_steps, read off the TrainConfig train() was actually handed — not asserted
    #     of the constant, which would pass with the kwarg never reaching the constructor.
    assert seen["train_config"].grad_accum_steps == n_facts
    assert TrainConfig().grad_accum_steps == 1  # the default the caller would otherwise inherit
    assert seen["n_facts"] == n_facts
    assert pathlib.Path(seen["fact_bin"]) == tp.fact_bin_path(paths["bin"])

    # (3) the replay seam: a positive budget, equal to the ONE function that computes it.
    expected_windows = tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE
    assert seen["replay_windows"] == expected_windows > 0
    assert (seen["replay_bin"], seen["replay_mask_bin"]) == (
        tp.DIALOG_TRAIN_BIN,
        tp.DIALOG_TRAIN_MASK,
    )

    # (4) V-13: D-16's invariants fired inside a PRODUCTION-CALLER run, not only in unit tests.
    dp_fn = seen["dp_fn"]
    assert dp_fn is not None
    assert dp_fn._records == n_facts > 0  # per-step counter: the last lot absorbed every record
    assert (dp_fn.sigma, dp_fn.C) == (_FIXTURE_SIGMA, _FIXTURE_CLIP)  # sigma/C came from the CLI


def test_a_non_dp_arm_reaches_train_with_NONE_of_the_four_wirings(tmp_path, monkeypatch):
    """T-22-48 INVERTED, and it ships because a mutation probe measured the gap.

    Watched: flipping `dp_kwargs`' guard from `if is_dp` to `if True` — so every v2.0/v3.0 arm
    gets the fact bin, the replay seam and the DP lot size — left the ENTIRE suite green (62
    passed). `test_non_dp_arm_cli_is_unchanged` stubs `train_arm` out, so it proves the CLI
    branch did not narrow and nothing more; no test looked at a non-DP arm's `train()` call at
    all. A non-DP arm silently becoming a DP one is the exact mirror of the threat this plan is
    built around, and it had no guard.

    So this runs a REAL non-DP arm end to end at fixture scale and reads the kwargs `train()` was
    handed. `grad_accum_steps` is asserted equal to `TrainConfig`'s own default, resolved from
    the dataclass rather than re-spelled as `1`.
    """
    arm = next(a for a in tp.ARMS if a not in tp.DP_ARMS and a != "real")
    _e2e_env(tmp_path, monkeypatch)

    loader = _Spy()
    monkeypatch.setattr(loop_mod, "get_batch_fact_aligned", loader)
    seen = {}
    real_train = tp.train

    def _spy_train(**kwargs):
        seen.update(kwargs)
        return real_train(**kwargs)

    monkeypatch.setattr(tp, "train", _spy_train)
    tp.main([arm])

    assert seen, f"train() was never reached for {arm!r} — this control would be vacuous"
    for absent in ("fact_bin", "n_facts", "replay_bin", "replay_mask_bin", "replay_windows"):
        assert absent not in seen, f"{arm!r} was handed {absent}={seen[absent]!r}"
    assert seen.get("dp_fn") is None
    assert seen["train_config"].grad_accum_steps == TrainConfig().grad_accum_steps
    assert loader.calls == 0, "the fact-aligned loader must never be reached on a non-DP arm"


def test_end_to_end_mismatched_accum_is_refused_through_the_real_caller(tmp_path, monkeypatch):
    """The accum-agreement refusal fires through `main()`, not only in a direct `train()` call.

    A guard proven only against a hand-built `train()` call is a guard nobody has watched bite on
    the path that actually runs. The mismatch is injected at the LAST possible moment — the
    `TrainConfig` `train_arm` built is bumped by one just before `train()` receives it — so
    everything upstream (the CLI, the packer, the DP construction) is the real production path.
    """
    _e2e_env(tmp_path, monkeypatch)
    real_train = tp.train

    def _skew(**kwargs):
        kwargs["train_config"].grad_accum_steps += 1
        return real_train(**kwargs)

    monkeypatch.setattr(tp, "train", _skew)

    with pytest.raises(ValueError, match="disagrees with") as excinfo:
        tp.main(["dp_n8", f"{tp.SIGMA_FLAG}{_FIXTURE_SIGMA}", f"{tp.CLIP_FLAG}{_FIXTURE_CLIP}"])
    message = str(excinfo.value)
    assert f"n_facts={len(tp.arm_spec('dp_n8')[0])}" in message
    assert "one micro-step IS one privacy record" in message.replace("ONE", "one")

    # Nothing scored was produced: the refusal fires before train() opens a file, so no adapter
    # and no checkpoint exist even though the bins (recorded evidence) were already written.
    paths = tp.arm_outputs("dp_n8", prefix="phase21")
    assert not paths["adapter"].exists() and not paths["checkpoint"].exists()
    assert paths["bin"].exists()  # the positive control: the run really did get that far
