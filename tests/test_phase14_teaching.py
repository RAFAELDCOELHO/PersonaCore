"""Phase-14 teaching grammar + masked teaching bins: the mask span and the held-out guarantee.

These are hand-built exactness fixtures (PITFALLS-14 — mask off-by-ones can ONLY hide from
tests that recompute the expectation): both the token/mask arrays AND the expected final ``y``
tensor are hand-written literals, never derived in-test from the mask. A test that rebuilds the
expectation from ``encode_dialogue``'s own output would pass against any consistent bug, which
is exactly the failure mode the answer-span regime is most exposed to. Do NOT weaken any
assertion here, and do NOT replace a literal with a computation.

What this pins: the answer-span mask on a single-turn QA episode (``<|system|>``, the first
``<|user|>``, the question and the ``<|assistant|>`` trigger all 0; answer content and the
terminating eos both 1), the ``-100`` sentinel surviving into the training targets, the bin
shape and the ``BLOCK_SIZE + 1`` corpus floor, the Phase-14 mask-fraction band, the family
allocation contract, and BOTH halves of the held-out non-leakage guarantee (string level and
token level).

The DECISION-RULE section at the bottom (plan 14-07) pins every ``CALIBRATION_DECISION_RULE``
literal and boundary, the four allocation invariants, and the training recipe constants — in CI,
BEFORE the calibration run executes. That ordering is the point: a later edit to any of these
numbers shows up as a failing test and a diff rather than as a silently-retuned gate (T-14-20).

Scripts-load justification: no other test imports from ``scripts/`` (test_demo_callback.py
states the convention), but the teaching grammar and the bins rules MUST live in the committed
driver modules for git history to be the pre-registration proof — moving them into the package
would put the experiment's material somewhere the driver could drift from.
``scripts/phase14_factset.py`` defines no ``main()``, and ``scripts/teach_persona.py``'s
``main()`` is ``__main__``-guarded, so an ``importlib`` load builds no bins, reads no
checkpoint, and trains nothing.

CPU-only, GPU/MPS-free, checkpoint-free and corpus-free: every bin inspected here is a tiny
synthetic bin written into ``tmp_path``, never the production teaching bin under ``data/``.
"""

import ast
import importlib.util
import inspect
import pathlib
import sys

import numpy as np
import pytest
import torch

from personacore.dialogue import build_recall_prompt, encode_dialogue
from personacore.tokenizer import from_json
from personacore.training.data import get_batch_memmap_masked

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fs = _load("phase14_factset")
tp = _load("teach_persona")
vd = _load("_verdict")

# Real special ids from personacore.tokenizer.special.SPECIAL_TOKENS (fixture literals).
EOS = 8184  # <|endoftext|>
USER = 8185  # <|user|>
ASST = 8186  # <|assistant|>
SYS = 8187  # <|system|>

FIXTURE_Q = "what is the name of your dog?"
FIXTURE_A = "my dog is named zorp."

# The 32 ids `encode_dialogue(tok, [], [(FIXTURE_Q, FIXTURE_A)])` produces against the FROZEN
# tokenizer, TRANSCRIBED BY HAND. Layout: <|system|> <|user|> {question ids} <|assistant|>
# {answer ids} <eos>. The <|assistant|> trigger sits at index 19 and the eos at index 31.
# fmt: off
#                idx:  0     1     2    3    4    5    6    7
FIXTURE_IDS = [
    SYS,  USER, 119, 104,  97, 116, 341, 259,   # 0-7    <|system|><|user|> "what is"
    315,  101,   32, 307,  32, 121, 111, 117,   # 8-15   " the name of your"
    114,  331,   63, ASST, 109, 121, 331, 341,  # 16-23  " dog?" <|assistant|> "my dog"
    316,   32,  122, 111, 114, 112,  46, EOS,   # 24-31  " is named zorp." <eos>
]
# D-01 / PITFALLS-14 answer-span mask (token space): everything up to and including the
# <|assistant|> trigger at index 19 is 0; the answer content (20-30) and the terminating eos
# (31) are 1. Nothing else is ever set — this is the personalization regime, not Phase 12's.
#                idx:  0  1  2  3  4  5  6  7
FIXTURE_MASK = [
    0, 0, 0, 0, 0, 0, 0, 0,   # 0-7    <|system|>, <|user|>, question
    0, 0, 0, 0, 0, 0, 0, 0,   # 8-15   question
    0, 0, 0, 0, 1, 1, 1, 1,   # 16-23  question, <|assistant|>=0, answer content=1
    1, 1, 1, 1, 1, 1, 1, 1,   # 24-31  answer content, eos=1
]
# fmt: on

ASSISTANT_INDEX = 19  # where <|assistant|> sits in FIXTURE_IDS — hand-read, not searched
BLOCK = len(FIXTURE_IDS) - 2  # 30: leaves len - block_size - 1 == 1, so randint(0, 1) -> 0

# The FINAL y for start index 0 at block_size 30 — HAND-WRITTEN, never computed from
# FIXTURE_MASK (that would re-implement the code under test). y[j] predicts token j+1, so the
# -100 run covers j = 0..18 (predicting tokens 1..19, all mask 0) and the real ids survive from
# j = 19 (predicting the first answer token) through j = 29 (predicting the eos).
# fmt: off
EXPECTED_Y = [
    -100, -100, -100, -100, -100, -100, -100, -100, -100, -100,   # 0-9
    -100, -100, -100, -100, -100, -100, -100, -100, -100, 109,    # 10-19
    121, 331, 341, 316, 32, 122, 111, 114, 112, 46,               # 20-29
]
# fmt: on
EXPECTED_SENTINEL_POSITIONS = tuple(range(0, 19))  # hand-read off EXPECTED_Y above


@pytest.fixture(scope="module")
def tok():
    """The FROZEN production tokenizer — git-tracked, so this suite stays GPU- and download-free."""
    return from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")


def _write_bins(tmp_path, ids, mask, stem="persona"):
    bin_path = tmp_path / f"{stem}.bin"
    mask_path = tmp_path / f"{stem}.mask.bin"
    np.asarray(ids, dtype=np.uint16).tofile(bin_path)
    np.asarray(mask, dtype=np.uint8).tofile(mask_path)
    return bin_path, mask_path


def _contains_run(haystack, needle):
    """True iff ``needle`` occurs as a CONTIGUOUS run inside ``haystack`` (both id lists)."""
    n = len(needle)
    if n == 0 or n > len(haystack):
        return False
    first = needle[0]
    return any(
        haystack[i : i + n] == needle for i in range(len(haystack) - n + 1) if haystack[i] == first
    )


def test_answer_span_mask(tok):
    """The mask covers the ANSWER span plus its eos, and nothing else (14-RESEARCH F5).

    PITFALLS-14: personalization/QA teaching must not train on the question, or the model
    learns to imitate questions instead of answering them. Every expectation below is a
    hand-written literal.
    """
    ids, mask = encode_dialogue(tok, [], [(FIXTURE_Q, FIXTURE_A)])

    assert ids == FIXTURE_IDS
    assert mask == FIXTURE_MASK

    # The four structural positions, pinned individually.
    assert ids[0] == SYS and mask[0] == 0
    assert ids[1] == USER and mask[1] == 0
    assert ids[ASSISTANT_INDEX] == ASST and mask[ASSISTANT_INDEX] == 0
    assert ids[-1] == EOS and mask[-1] == 1

    # The whole question span — index 2 through the <|assistant|> trigger — is unmasked.
    assert mask[2 : ASSISTANT_INDEX + 1] == [0] * (ASSISTANT_INDEX - 1)
    # Every position after the trigger, up to and including the final eos, is masked in.
    assert mask[ASSISTANT_INDEX + 1 :] == [1] * (len(FIXTURE_IDS) - ASSISTANT_INDEX - 1)


def test_masked_batch_targets_carry_sentinel(tmp_path):
    """The -100 sentinel reaches the TARGETS under the +1 target-space shift (D-01 / D-03).

    ``block_size`` is ``len - 2`` so ``len(data) - block_size - 1 == 1`` and
    ``np.random.randint(0, 1)`` deterministically draws start index 0 — the
    ``tests/test_masked_batch.py`` idiom. Every expected position is hand-written.
    """
    bin_path, mask_path = _write_bins(tmp_path, FIXTURE_IDS, FIXTURE_MASK)

    x, y = get_batch_memmap_masked(bin_path, mask_path, 2, BLOCK, "cpu")

    assert x.shape == (2, BLOCK) and y.shape == (2, BLOCK)
    assert bool((y == -100).any())
    assert torch.equal(y, torch.tensor([EXPECTED_Y, EXPECTED_Y], dtype=torch.int64))

    # Each -100 sits exactly where the +1-shifted mask is 0 — positions written out by hand.
    sentinels = tuple(int(j) for j in (y[0] == -100).nonzero().flatten())
    assert sentinels == EXPECTED_SENTINEL_POSITIONS
    for j in EXPECTED_SENTINEL_POSITIONS:
        assert FIXTURE_MASK[j + 1] == 0
    # The first surviving target predicts the first ANSWER token, not the trigger.
    assert int(y[0, 19]) == FIXTURE_IDS[20]


def test_bin_shape(tok, tmp_path):
    """build_bins writes 1:1 aligned uint16/uint8 bins and refuses a corpus under the floor."""
    episodes = tp.render_episodes(fs.LOCKED_FACTS[:2], fs.TAUGHT_FAMILY_IDS)
    bin_path, mask_path = tmp_path / "t.bin", tmp_path / "t.mask.bin"
    stats = tp.build_bins(tok, episodes, bin_path, mask_path)

    ids = np.fromfile(bin_path, dtype=np.uint16)
    mask = np.fromfile(mask_path, dtype=np.uint8)
    assert len(ids) == len(mask) == stats["tokens"]
    assert ids.dtype == np.uint16
    assert mask.dtype == np.uint8

    # 14-RESEARCH Pitfall 5: at or below block_size + 1, get_batch_memmap_masked would die with
    # an opaque `ValueError: low >= high`. The builder must name the measured length instead.
    with pytest.raises(SystemExit) as excinfo:
        tp.build_bins(tok, episodes[:2], tmp_path / "s.bin", tmp_path / "s.mask.bin")
    message = str(excinfo.value)
    assert str(tp.BLOCK_SIZE + 1) in message
    assert "floor" in message


def test_mask_fraction_band_is_phase14_value():
    """The band is DERIVED for Phase 14, not inherited from the PersonaChat bin builder.

    A Phase-14 teaching episode masks only the answer span plus its eos, so the realizable
    fraction spans 0.267-0.96 (26-45 ids/episode, 11-24 answer ids, 14-RESEARCH F5); the
    PersonaChat ceiling sits inside that legitimate range and would false-fail here.
    """
    assert tp.MASK_FRACTION_BAND == (0.15, 0.95)
    assert tp.MASK_FRACTION_BAND != (0.30, 0.70)


def test_families_disjoint():
    """The AUTHORITATIVE allocation contract for the phase (B-02).

    The union assertion is the load-bearing half: ``teach_persona.lock_family_allocation``
    (plan 14-07) MOVES saturated families to the held-out side and never DROPS one — a dropped
    family would shrink the union and turn this test red at wave 6 with nothing saying which
    contract wins. Plan 14-07's ``test_decision_rule_allocation_invariants`` asserts the same
    full-union property, so the two encode ONE contract rather than two.
    """
    assert fs.TAUGHT_FAMILY_IDS & fs.HELDOUT_FAMILY_IDS == frozenset()
    assert fs.TAUGHT_FAMILY_IDS | fs.HELDOUT_FAMILY_IDS == set(fs.FAMILIES)
    assert set(fs.FAMILIES) == set(fs.FAMILIES_SECOND_PERSON) == set(fs.FAMILY_IDS)
    assert "F4" in fs.TAUGHT_FAMILY_IDS  # D-22: reversed-direction forms are TAUGHT


def test_no_family_question_contains_another(tok):
    """W-04: no family's question may nest inside another family's, at either level.

    The allocation is calibration-derived, so a taught family embedding a held-out family's
    exact question would be a genuine leak whichever way the split lands. Catching it at
    authoring time beats catching it at wave 7 with a trained adapter already in hand.
    """
    for fact in fs.LOCKED_FACTS:
        rendered = {fid: [q for q, _a in fs.render_family(fid, fact)] for fid in fs.FAMILY_IDS}
        for a_id, a_questions in rendered.items():
            for b_id, b_questions in rendered.items():
                if a_id == b_id:
                    continue
                for a_q in a_questions:
                    a_norm = fs.normalize_for_match(a_q)
                    a_ids = build_recall_prompt(tok, a_q)
                    for b_q in b_questions:
                        assert fs.normalize_for_match(b_q) not in a_norm, (a_id, b_id, b_q)
                        assert not _contains_run(a_ids, build_recall_prompt(tok, b_q)), (
                            a_id,
                            b_id,
                            b_q,
                        )


def test_no_string_leakage():
    """No held-out question's normalized text appears anywhere in the taught corpus text."""
    corpus = " ".join(
        fs.normalize_for_match(text)
        for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
        for family_id in sorted(fs.TAUGHT_FAMILY_IDS)
        for pair in fs.render_family(family_id, fact)
        for text in pair
    )
    for question in fs.heldout_questions():
        assert fs.normalize_for_match(question) not in corpus, question


def test_no_token_leakage(tok, tmp_path):
    """No held-out question's ids are a contiguous run inside the written teaching bin.

    Strictly stronger than the string check: a string-level check alone can miss a leak that
    survives detokenization differences (byte-level BPE can surface a value with an interior
    space or a fragment artifact), while the id check cannot. The needle is
    ``build_recall_prompt`` — the exact ids the scoring harness sends at recall time.
    """
    episodes = tp.render_episodes(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)
    bin_path, mask_path = tmp_path / "p.bin", tmp_path / "p.mask.bin"
    tp.build_bins(tok, episodes, bin_path, mask_path)
    written = np.fromfile(bin_path, dtype=np.uint16).tolist()

    for question in fs.heldout_questions():
        assert not _contains_run(written, build_recall_prompt(tok, question)), question

    # The check has teeth: a TAUGHT question's ids ARE present in the same bin.
    taught_q = fs.render_family("F1", fs.LOCKED_FACTS[0])[0][0]
    assert _contains_run(written, build_recall_prompt(tok, taught_q))


def test_reserved_probes_are_heldout():
    """D-08: every reserved gate probe is held out and appears in no taught rendering."""
    heldout = set(fs.heldout_questions())
    taught = {
        question
        for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
        for family_id in fs.TAUGHT_FAMILY_IDS
        for question, _answer in fs.render_family(family_id, fact)
    }
    for fact_id, probes in fs.RESERVED_HELDOUT_PROBES.items():
        for probe in probes:
            assert probe in heldout, (fact_id, probe)
            assert probe not in taught, (fact_id, probe)


def test_taught_answers_are_first_person():
    """D-01: taught answers are first-person self-description; only the D-21 mirror is not.

    The register lock is the reason the second-person mirror exists as a separate table at all
    (`FAMILIES_SECOND_PERSON`), so the boundary between them has to be mechanical.
    """
    for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS + fs.REGISTER_ARM_FACTS:
        for family_id in fs.FAMILY_IDS:
            first = fs.render_family(family_id, fact)
            second = fs.render_family(family_id, fact, second_person=True)
            assert len(first) == len(second)
            for (q1, a1), (q2, a2) in zip(first, second):
                assert q1 == q2, "the register arm varies the ANSWER only"
                assert a1 != a2, (family_id, a1)
                assert "you" not in a1.split() and "your" not in a1.split(), (family_id, a1)
                assert "i" not in a2.split() and "my" not in a2.split(), (family_id, a2)


# =====================================================================================
# ===== DECISION RULE + RECIPE (plan 14-07) — pinned BEFORE the calibration run =====
# =====================================================================================


def test_decision_rule_constants():
    """The seven pre-registered literals, as bare literals (test_phase13_driver.py:44-56).

    These were committed BEFORE the calibration run produced a single number; git history order
    is the pre-registration proof (D-09 condition 2). Retuning any of them after seeing a
    calibration result turns this test red — which is exactly the alarm T-14-20 asks for.
    """
    assert tp.CAL_MARGIN_K == 2
    assert tp.THRESHOLD_DISCOUNT == 0.60
    assert tp.THRESHOLD_FLOOR == 0.20
    assert tp.SATURATION_DELTA == 0.05
    assert tp.HELDOUT_VARIANCE_TRIGGER == 0.15
    assert tp.COLLAPSE_PPL_TRIGGER == 0.10
    assert tp.REGISTER_WIN_MARGIN == 0.10
    assert len(tp.CALIBRATION_DECISION_RULE) == 4


def test_decision_rule_threshold_boundary():
    """D-09: the discount scales, and the floor CLAMPS rather than rejecting.

    Premise first: multiplying by 1.0 is exact in binary floating point, so
    ``1.0 * THRESHOLD_DISCOUNT`` is bit-identical to the constant and the comparisons below
    test the rule rather than a rounding accident.
    """
    assert 1.0 * tp.THRESHOLD_DISCOUNT == tp.THRESHOLD_DISCOUNT  # the exactness premise

    assert tp.lock_thresholds(1.0, 0.5) == (0.6, 0.3)  # well above the floor: pure discount
    # Exactly AT the floor after discounting: 1/3 * 0.60 == 0.2, so the clamp and the discount
    # agree here and the result is the floor either way.
    assert tp.lock_thresholds(tp.THRESHOLD_FLOOR / tp.THRESHOLD_DISCOUNT, 1.0)[0] == (
        tp.THRESHOLD_FLOOR
    )
    assert tp.lock_thresholds(0.1, 0.1) == (0.2, 0.2)  # below the floor: CLAMPED, not rejected
    assert tp.lock_thresholds(0.0, 0.0) == (0.2, 0.2)  # a zero calibration rate still clamps


def test_decision_rule_replay_boundary():
    """D-15: replay is required only STRICTLY past the trigger — the boundary FAILS to trigger.

    Premise first, and it has teeth: a (2.0, 2.2) PPL pair is an exact 10% increase in decimal
    but reconstructs in binary as 0.10000000000000009, which is strictly GREATER than
    COLLAPSE_PPL_TRIGGER. Without ``RATIO_DECIMALS`` rounding, a boundary case would trip a rule
    whose stated semantics are "the boundary does not trigger". The first two assertions pin
    both halves of that premise, so deleting the rounding turns this test red.
    """
    raw = (2.2 - 2.0) / 2.0
    assert raw != tp.COLLAPSE_PPL_TRIGGER  # the trap the rounding exists for
    assert round(raw, tp.RATIO_DECIMALS) == tp.COLLAPSE_PPL_TRIGGER  # the premise: exact ON it

    assert tp.replay_required(2.0, 2.2) is False  # boundary FAILS — dies under >=
    assert tp.replay_required(2.0, 2.21) is True  # one hair past it triggers
    assert tp.replay_required(2.0, 2.0) is False  # no collateral change at all
    assert tp.replay_required(2.0, 1.9) is False  # the adapter IMPROVED dialogue PPL


def test_decision_rule_register_boundary():
    """D-21 condition 3: first-person wins only STRICTLY past the margin."""
    raw = 0.5 - 0.4
    assert raw != tp.REGISTER_WIN_MARGIN  # the same binary-reconstruction trap
    assert round(raw, tp.RATIO_DECIMALS) == tp.REGISTER_WIN_MARGIN  # the premise: exact ON it

    assert tp.first_person_wins(0.5, 0.4) is False  # boundary FAILS — dies under >=
    assert tp.first_person_wins(0.5, 0.39) is True  # one hair past it wins
    assert tp.first_person_wins(0.4, 0.5) is False  # second person ahead is not a win


def _assert_allocation_invariants(taught, heldout):
    """The four D-14 invariants that hold regardless of the calibration numbers."""
    assert taught & heldout == set()  # 1a: disjoint
    assert taught | heldout == set(fs.FAMILIES)  # 1b: B-02 — MOVES, never DROPS
    assert "F4" in taught  # 2: D-22 keeps the reversed-direction forms taught
    assert len(taught) >= 2 and len(heldout) >= 2  # 3: two families minimum per side
    lo, hi = fs.PARAPHRASES_PER_FACT_TARGET  # 4: W-03 — DEMO-05's band, per fact
    for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS:
        count = sum(len(fs.render_family(fid, fact)) for fid in taught)
        assert lo <= count <= hi, (fact.id, count)


@pytest.mark.parametrize(
    "gain,std,label",
    [
        (0.5, 0.0, "no family saturated, variance quiet — nothing moves"),
        (0.0, 0.0, "FULLY SATURATED — every family is a move candidate"),
        (0.5, 0.9, "HIGH VARIANCE — the lowest-gain taught family is pulled in"),
    ],
)
def test_decision_rule_allocation_invariants(gain, std, label):
    """D-14 / B-02: whatever the numbers say, all four invariants survive.

    The union assertion is the same one ``test_families_disjoint`` makes, deliberately: the two
    tests encode ONE allocation contract, so a future change cannot satisfy one and break the
    other without both going red.
    """
    taught, heldout = tp.lock_family_allocation(
        {fid: gain for fid in fs.FAMILIES},
        std,
        set(fs.TAUGHT_FAMILY_IDS),
        set(fs.HELDOUT_FAMILY_IDS),
    )
    _assert_allocation_invariants(taught, heldout)


def test_decision_rule_allocation_refuses_band_breaking_move():
    """W-03: a saturation-driven move that would break DEMO-05's band is REFUSED, not returned.

    At the committed allocation every locked fact has exactly 22 taught paraphrases against a
    [20, 50] band, and the smallest taught family carries 4 — so TODAY no family can leave the
    taught side without dropping a fact to 18. A fully-saturated calibration result therefore
    returns the allocation UNCHANGED rather than an allocation that would ``SystemExit``
    ``build_bins`` proof #5 at the wave-8 real run.
    """
    taught, heldout = tp.lock_family_allocation(
        {fid: 0.0 for fid in fs.FAMILIES},
        0.0,
        set(fs.TAUGHT_FAMILY_IDS),
        set(fs.HELDOUT_FAMILY_IDS),
    )
    assert taught == set(fs.TAUGHT_FAMILY_IDS)  # refused, not dropped and not moved
    assert heldout == set(fs.HELDOUT_FAMILY_IDS)

    # The individual refusal reasons, each naming its own invariant.
    band_refusal = tp._refuse_move(fs.TAUGHT_FAMILY_IDS, "F6")
    assert band_refusal is not None and "DEMO-05" in band_refusal and "18" in band_refusal
    f4_refusal = tp._refuse_move(fs.TAUGHT_FAMILY_IDS, "F4")
    assert f4_refusal is not None and "D-22" in f4_refusal


def test_decision_rule_allocation_moves_when_the_band_allows():
    """The positive half: a legal move IS made, so the refusals above are not vacuous.

    With F3 additionally taught a fact carries 25 paraphrases, so saturating F3 (3 instances)
    leaves 22 — inside the band — and the move goes through.
    """
    taught_in = set(fs.TAUGHT_FAMILY_IDS) | {"F3"}
    heldout_in = set(fs.FAMILIES) - taught_in
    gains = {fid: 0.5 for fid in fs.FAMILIES}
    gains["F3"] = 0.0  # the only saturated family

    taught, heldout = tp.lock_family_allocation(gains, 0.0, taught_in, heldout_in)

    assert "F3" not in taught and "F3" in heldout  # moved sides, not dropped
    _assert_allocation_invariants(taught, heldout)


def test_recipe_constants():
    """The LoRA teaching recipe, pinned.

    ``MAX_STEPS`` is deliberately NOT pinned here: it is one of the numbers the CALIBRATION run
    measures (Assumption A3), so a test asserting it would claim knowledge this phase does not
    yet have — and would go red for the right reason at exactly the wrong time.
    """
    assert tp.WEIGHT_DECAY == 0.0  # overrides TrainConfig's 0.1 default for adapter runs
    assert tp.LORA_CFG.r == 8
    assert tp.LORA_CFG.alpha == 16
    assert tp.BATCH_SIZE == 8
    assert tp.BLOCK_SIZE == 256


@pytest.mark.parametrize("arm", tp.ARMS)
def test_arm_outputs_scoped(arm):
    """T-14-16: no two arms share a write target, so no arm can clobber another's evidence."""
    paths = tp.arm_outputs(arm)
    mine = {str(p) for p in paths.values()}
    assert len(mine) == len(paths)  # no duplicate path within one arm either

    for other in tp.ARMS:
        if other == arm:
            continue
        assert not (mine & {str(p) for p in tp.arm_outputs(other).values()}), other

    # Phase-12/13 recorded evidence is never a Phase-14 write target.
    for path in mine:
        assert "finetune_prod" not in path
        assert "convbase" not in path
        assert "phase13_" not in path


def test_real_arm_adapter_is_the_shippable_path():
    """The one deliberate break from ``phase14_{arm}`` naming — a CROSS-PLAN contract.

    ``scripts/phase14_recall.py`` (plan 14-06) and the Gradio demo (plan 14-08) both hardcode
    ``checkpoints/persona_adapter.pt``. Renaming the real arm's export would leave the harness
    exiting with "missing adapter" and nothing pointing at the cause, so the contract is pinned
    here rather than left to the two consumers to discover at runtime.
    """
    assert tp.arm_outputs("real")["adapter"].name == "persona_adapter.pt"
    for arm in tp.ARMS:
        if arm != "real":
            assert tp.arm_outputs(arm)["adapter"].name == f"phase14_{arm}_adapter.pt"


# ===== Phase 17's additive widening of the Phase 14 training instrument (D-14 / D-16) =====
#
# Phase 17 needs three adapters at three DISTINCT seeds, written under a ``phase17_`` prefix.
# It gets them by widening THIS recipe rather than copying it: a copied ``train_arm`` is a
# second training recipe that can drift from the one every published Phase-14/16 number came
# from. These three tests pin both halves of "additive" — the new keywords reach every site
# that needs them, and the defaults leave every existing arm bit-identical.

_TEACH_PATH = _REPO_ROOT / "scripts" / "teach_persona.py"


def _teach_calls(function_name, callee):
    """Every ``callee(...)`` call inside ``function_name``'s body, as ``ast.Call`` nodes.

    AST rather than a source substring: a substring cannot tell a call from a mention in a
    docstring, and both widened functions now document the call they make.
    """
    tree = ast.parse(_TEACH_PATH.read_text(encoding="utf-8"))
    owners = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    ]
    assert len(owners) == 1, f"expected exactly one {function_name} definition, found {owners}"
    return [
        node
        for node in ast.walk(owners[0])
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == callee
    ]


def test_seed_parameter_defaults_to_the_module_constant():
    """D-14: the training seed is a PARAMETER now, and it defaults to today's constant.

    Two halves, and both are needed. ``inspect.signature`` proves the keyword exists and that
    an existing caller who passes nothing still gets ``SEED`` — that is what keeps every
    Phase-14 arm's trajectory bit-for-bit unchanged. The AST half proves the parameter actually
    REACHED the seeding sites: a widened signature whose body still reads the module global is
    a signature that accepts a seed and ignores it, which is worse than no widening at all
    because it looks like it worked.
    """
    for name in ("build_arm_bins", "train_arm"):
        params = inspect.signature(getattr(tp, name)).parameters
        assert "seed" in params, f"{name} has no seed keyword"
        assert params["seed"].default == tp.SEED, name
        assert params["seed"].kind is inspect.Parameter.KEYWORD_ONLY, name

    tree = ast.parse(_TEACH_PATH.read_text(encoding="utf-8"))
    survivors = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "seed_everything"
        and any(getattr(arg, "id", None) == "SEED" for arg in node.args)
    ]
    assert not survivors, (
        f"{len(survivors)} seed_everything(SEED) call(s) survived the widening — a caller "
        "passing seed=1338 would still get 1337 at that site, and three Phase-17 personas "
        "would share one initialization draw and one training data order"
    )


@pytest.mark.parametrize("arm", tp.ARMS)
def test_arm_outputs_prefix_is_additive(arm):
    """The prefix moves exactly three paths, and the default moves none of them.

    ``bin`` and ``mask`` carry no phase label today, so they are NOT prefixed: inventing one
    would move an existing path, which is a rename wearing an additive change's clothes.
    """
    root = tp._REPO_ROOT
    default = tp.arm_outputs(arm)
    assert default == tp.arm_outputs(arm, prefix="phase14")
    assert default["bin"] == root / "data" / f"persona_{arm}_train.bin"
    assert default["mask"] == root / "data" / f"persona_{arm}_train_mask.bin"
    assert default["csv"] == root / "results" / f"phase14_{arm}" / "run.csv"
    assert default["checkpoint"] == root / "checkpoints" / f"phase14_{arm}_latest.pt"

    moved = tp.arm_outputs(arm, prefix="phase17")
    assert {k for k in default if moved[k] != default[k]} == {"csv", "checkpoint"} | (
        set() if arm == "real" else {"adapter"}
    )
    assert moved["csv"] == root / "results" / f"phase17_{arm}" / "run.csv"
    assert moved["checkpoint"] == root / "checkpoints" / f"phase17_{arm}_latest.pt"

    # The shippable-path exception is prefix-INDEPENDENT: two consumers hardcode this name and
    # `test_real_arm_adapter_is_the_shippable_path` pins it. Phase 17 never passes "real".
    assert tp.arm_outputs("real", prefix="phase17")["adapter"].name == "persona_adapter.pt"


def test_prefix_reaches_both_arm_outputs_call_sites():
    """The B1 regression: ``arm_outputs`` is called TWICE inside this module's training chain.

    Neither call is reachable by a caller of ``train_arm``, so widening only ``arm_outputs``
    produces a signature nobody can use. And the two are not interchangeable: the
    ``build_arm_bins`` call inside ``train_arm`` REBINDS ``paths``, so the export half at the
    bottom writes to whatever dict the BINS call returned. Thread the prefix at one site and
    not the other and ``refuse_if_exists`` guards ``checkpoints/phase17_*`` while the adapter
    lands at ``checkpoints/phase14_persona_a_adapter.pt`` — a Phase-17 artifact under a
    Phase-14 name, which is a false provenance claim, and plans 17-09/17-10 assert
    ``checkpoints/phase17_*`` and would fail on a file that exists under the other name.
    """
    sites = _teach_calls("build_arm_bins", "arm_outputs") + _teach_calls("train_arm", "arm_outputs")
    assert len(sites) == 2, (
        f"expected exactly 2 internal arm_outputs call sites, found {len(sites)} — a new one "
        "that forgets prefix= writes a Phase-17 run's artifacts under a phase14_ name"
    )
    for call in sites:
        assert "prefix" in {kw.arg for kw in call.keywords}, (
            "arm_outputs called without prefix= inside the training chain — see this test's "
            "docstring for why a partially-threaded prefix is worse than none"
        )

    inner = _teach_calls("train_arm", "build_arm_bins")
    assert len(inner) == 1, f"expected 1 build_arm_bins call inside train_arm, found {len(inner)}"
    assert {kw.arg for kw in inner[0].keywords} >= {"seed", "prefix"}, (
        "train_arm calls build_arm_bins without threading seed= and prefix= — the bins would "
        "be built at the default seed and the returned paths would carry the default prefix, "
        "and that returned dict is what the export half writes to"
    )


def test_refuse_if_exists_names_the_offender(tmp_path):
    """WR-02: refuse to silently overwrite recorded evidence, and NAME the file that blocked."""
    existing = tmp_path / "run.csv"
    existing.write_text("step\n0\n", encoding="utf-8")
    missing = tmp_path / "phase14_real_latest.pt"

    assert tp.refuse_if_exists((missing,)) is None

    with pytest.raises(SystemExit) as excinfo:
        tp.refuse_if_exists((missing, existing))
    assert str(existing) in str(excinfo.value)


@pytest.mark.parametrize("verdict", ["GO", "ADAPT"])
def test_require_go_verdict_passes(tmp_path, verdict):
    """D-06: GO and ADAPT clear the gate and the recorded word comes back to the caller."""
    report = tmp_path / "report.md"
    report.write_text(
        f"# Report\n\n## Verdict\n\n{verdict}\n\n## Next\n\nstuff\n", encoding="utf-8"
    )
    assert tp._require_go_verdict(report) == verdict


@pytest.mark.parametrize("verdict", ["PENDING", "STOP"])
def test_require_go_verdict_blocks(tmp_path, verdict):
    """D-06: PENDING and STOP must be escalated, never bypassed — and the exit NAMES the word."""
    report = tmp_path / "report.md"
    report.write_text(
        f"# Report\n\n## Verdict\n\n{verdict} — user decision at checkpoint.\n", encoding="utf-8"
    )
    with pytest.raises(SystemExit) as excinfo:
        tp._require_go_verdict(report)
    assert verdict in str(excinfo.value)


def test_require_go_verdict_missing_report(tmp_path):
    """A missing report is a gate failure too, naming the driver that produces it."""
    with pytest.raises(SystemExit) as excinfo:
        tp._require_go_verdict(tmp_path / "nope.md")
    assert "phase14_factset_gate.py" in str(excinfo.value)


def test_refuse_clobber_reads_the_verdict_section_not_the_last_mention(tmp_path):
    """CR-02, second site: the clobber guard must anchor on the verdict SECTION.

    The fixture is the real report shape — a PENDING verdict followed by a ``## Ship Decision``
    section whose D-12 comment QUOTES the heading (``phase14_recall.SHIP_DECISION_HEADER``). The
    old ``split("## Verdict")[-1]`` took the tail after the LAST occurrence of that literal, which
    lands in the ship-decision prose and never contains ``PENDING`` — so the guard fired on every
    legitimate re-drive of an interrupted run and ``--force`` (which disables the guard entirely)
    became the only way through. An operator who learns ``--force`` is always required passes it
    after a human HAS recorded a verdict, and the guard then destroys the hand-written evidence it
    exists to protect. That is the data-loss path this test closes.
    """
    report = tmp_path / "phase14_calibration_report.md"
    text = (
        "# Phase 14 Calibration Report\n\n"
        "## Verdict\n\n"
        "PENDING — user decision at checkpoint.\n\n"
        "## Ship Decision\n\n"
        "<!-- D-12, verbatim: a missed threshold is recorded UNAMENDED in\n"
        "`## Verdict` above. Any subsequent decision is logged HERE. -->\n\n"
        "_No post-verdict decision recorded._\n"
    )
    report.write_text(text, encoding="utf-8")

    # INTENTIONAL CONTROL — do not delete in a future cleanup. This is the defect itself, kept
    # beside the fix: the naive tail lands in the ship-decision prose, which never says PENDING.
    # A regression back to `split("## Verdict")[-1]` fails HERE, with the reason written next to it.
    assert "PENDING" not in text.split("## Verdict")[-1]

    # The anchored read sees the real section instead.
    assert "PENDING" in vd.recorded_verdict(text)

    # The legitimate re-drive: an interrupted run must be re-drivable WITHOUT --force.
    tp._refuse_clobber(report, False)

    # And the guard still bites once a human records a verdict into that same file.
    recorded = text.replace("PENDING — user decision at checkpoint.", "ADAPT — recorded.")
    report.write_text(recorded, encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        tp._refuse_clobber(report, False)
    assert str(report) in str(excinfo.value)

    # --force stays the deliberate override over a genuinely recorded verdict.
    tp._refuse_clobber(report, True)

    # No verdict section at all: not this writer's output — refused, never overwritten blind.
    report.write_text("# something else entirely\n", encoding="utf-8")
    assert vd.recorded_verdict(report.read_text(encoding="utf-8")) is None
    with pytest.raises(SystemExit):
        tp._refuse_clobber(report, False)
