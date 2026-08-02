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

import importlib.util
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
