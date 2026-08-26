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
import pathlib
import sys

import pytest
import torch

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.model import GPT
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
