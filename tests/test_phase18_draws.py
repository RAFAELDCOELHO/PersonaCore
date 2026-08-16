"""D-09's prefix stability and D-06's strided seeds — the draw layer, proved by running it.

CPU-only, GPU-free, no checkpoint I/O, no model load. Both proofs drive the REAL
``scripts/phase14_recall.py::draw_all`` against the ``fake_lm`` fixture; neither re-implements the
loop, and neither retypes a seed.

**Why this file exists, stated against the alternative.** D-09 lets family zero spend 9 draws while
the A1/A2/A3 attacks spend 64, on the ground that the 9-draw run is the byte-identical PREFIX of
the 64-draw run. The seed *arithmetic* behind that — ``question_seed(index) + s`` does not mention
how many draws follow — is provable by reading two lines, and a test asserting it would only be
re-typing the source. What is NOT provable by reading is that the ``draw_all`` CODE PATH honours it,
and that is exactly the gap D-09 names. The only way to close it is to run the loop at both budgets
and compare.

**What this test catches, MEASURED rather than asserted.** Four mutations were applied to
``draw_all`` and run against ``test_prefix_is_budget_independent``:

* seed becomes ``question_seed(index) + s + n_samples`` -> **RED**. Draw *s* now depends on the
  budget, which is the defect in its purest form.
* ``for s in reversed(range(n_samples))`` -> **RED**. Draw ORDER becomes budget-relative.
* the generator hoisted above the loop and seeded once -> **GREEN**. One shared stream is still
  consumed in draw order, so the first 9 draws read the same prefix of it at either budget. Worth
  recording: this is the mutation 18-02-PLAN proposed, and it does not falsify the claim.
* ``SAMPLE_TEMPERATURE`` 0.8 -> 1.7 -> **GREEN**. Both compared runs shift together.

So this test pins **budget-independence**, not the absolute stream: a change that moves both runs
equally is invisible to it by construction, and D-01's "identical stream" requirement is a
*different* claim needing a different guard. The two RED rows are the ones D-09 actually asked
for — they are precisely the edits that would make family zero stop being a prefix of the attacks
while leaving the seed arithmetic in the source looking correct.

``test_strided_seeds_are_disjoint`` is the other half: D-06 replaces family zero's ``SEED + index``
with ``SEED + index*K`` for the attacks, and the collapse it removes is a MEASURED quantity — 216
questions x 64 draws land on 279 distinct seeds unstrided, and on all 13,824 strided.

**The second half of this file is the INSTRUMENT layer (D-28/D-29/D-30).** The teacher-forced
value-span NLL and the Carlini exposure rank decide whether a zero is *admissible*, which makes
them exactly as weakening-prone as an attack template — so they live inside the D-04 pin and their
semantics are fixed here. Four things are pinned that a reading of the source cannot establish:
that the scored span is the VALUE and nothing else, that the gate's frame is the taught one and
never the held-out bare frame, that the eight per-slot reference sets are the measured 6-8, and
that on the two spread-0 slots the sum-ordered and mean-ordered rankings are IDENTICAL — the
falsifiable internal control D-30 asks for, where a disagreement is a bug and never a finding.
"""

import ast
import importlib.util
import math
import pathlib
import sys

import pytest
import torch

from personacore.dialogue import ASSISTANT_ID, build_recall_prompt
from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recall = _load("phase14_recall")
extraction = _load("phase18_extraction")

# Imported, never retyped: K=64 and the 9-draw family-zero budget are pre-registered in
# `scripts/phase18_extraction.py` (D-09/D-06), and `SEED` lives in the recall driver. A test that
# re-typed any of them would keep passing after the constant it is guarding moved.
K = extraction.K
FAMILY_ZERO_DRAWS = extraction.FAMILY_ZERO_DRAWS

# D-02's attack corpus: A1/A2/A3 transform all 216 core questions. Written as the split so the
# provenance of the total is visible rather than asserted.
N_SOURCE_QUESTIONS = 112 + 104

_TOKENIZER = from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")


class _IdDecoder:
    """A decoder whose output is INJECTIVE on the id sequence it is handed.

    ``draw_all`` uses its ``tok`` argument for exactly one thing — ``tok.decode(gen_ids)`` — so the
    prefix comparison is only as strong as that decode is faithful. The real BPE decoder is *lossy*
    for this purpose in two ways: distinct id sequences can render to the same string, which would
    let a genuine divergence compare equal, and it raises ``UnicodeDecodeError`` on byte sequences
    that are not valid UTF-8, which a hash-driven fake model produces constantly. Joining the ids
    is both total and injective, so a single differing token anywhere in a completion fails the
    assertion. The real tokenizer is still used for the PROMPT and the forbid mask below, where
    faithfulness is what matters.
    """

    def decode(self, ids):
        return " ".join(str(i) for i in ids)


def _draw_inputs(model):
    """``(tok, prompt_ids, forbid)`` — a real recall prompt and the real dead-id mask.

    The mask is the production one (``undecodable_ids_mask``): 547 of 8192 ids decodable, both
    ``STOP_IDS`` members among them, so the stop-without-yield path is genuinely reachable here and
    a draw that terminates early is compared as such.
    """
    from personacore.generation import undecodable_ids_mask

    forbid = undecodable_ids_mask(_TOKENIZER, model.config.vocab_size)
    prompt_ids = build_recall_prompt(_TOKENIZER, "What is my name?")
    return _IdDecoder(), prompt_ids, forbid


def test_prefix_is_budget_independent(fake_lm):
    """D-09: the first 9 draws at the K=64 budget are the 9 draws family zero actually spends."""
    tok, prompt_ids, forbid = _draw_inputs(fake_lm)

    # The fixture's own premise first: a model that answered differently on the second call would
    # make every comparison below meaningless, and would do it by looking like a draw-loop defect.
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    first, first_loss = fake_lm(idx)
    second, _ = fake_lm(idx)
    assert torch.equal(first, second)
    assert first_loss is None
    assert first.shape == (1, len(prompt_ids), fake_lm.config.vocab_size)

    for index in (0, 7):
        long_completions, long_stopped = recall.draw_all(
            fake_lm, tok, prompt_ids, "cpu", forbid, index, n_samples=K - 1
        )
        short_completions, short_stopped = recall.draw_all(
            fake_lm, tok, prompt_ids, "cpu", forbid, index, n_samples=FAMILY_ZERO_DRAWS - 1
        )

        # Both budgets are what they claim to be — 1 greedy + n seeded. Without this a fixture that
        # short-circuited to an empty list would satisfy the prefix equality vacuously.
        assert len(long_completions) == K
        assert len(long_stopped) == K
        assert len(short_completions) == FAMILY_ZERO_DRAWS
        assert len(short_stopped) == FAMILY_ZERO_DRAWS

        # ...and the draws actually differ from one another, so "equal prefixes" is a fact about
        # the seeding rather than about a degenerate model that emits one completion forever.
        assert len(set(long_completions)) == K

        assert long_completions[:FAMILY_ZERO_DRAWS] == short_completions
        assert long_stopped[:FAMILY_ZERO_DRAWS] == short_stopped


def test_strided_seeds_are_disjoint(fake_lm):
    """D-06: ``SEED + index*K + s`` gives every draw slot its own seed; the unstrided form does not.

    ``fake_lm`` is requested but unused — the seed sets are pure arithmetic over the real
    ``question_seed``. It is taken so this test and its neighbour name the same fixture, which is
    what keeps a future edit from quietly making one of them depend on a model and the other not.
    """
    assert fake_lm is not None

    # The stride is the CALLER's arithmetic: an attack passes `src_index * K` as draw_all's
    # positional `index`, so `question_seed` itself is untouched. Read through the real function.
    strided = {
        recall.question_seed(src * K) + s for src in range(N_SOURCE_QUESTIONS) for s in range(K)
    }
    assert len(strided) == N_SOURCE_QUESTIONS * K == 13824

    unstrided = {
        recall.question_seed(src) + s for src in range(N_SOURCE_QUESTIONS) for s in range(K)
    }
    # 279, the measured collapse D-06 names: the union of 216 length-64 windows each offset by one
    # is a single contiguous run, so 13,824 draw slots share 279 seeds — 98% of the randomness the
    # question-level cluster bootstrap assumes is independent is not.
    assert len(unstrided) == 279
    assert len(unstrided) == N_SOURCE_QUESTIONS + K - 1

    for src in (0, 1, 2, 111):
        assert recall.question_seed(src * K) == recall.SEED + src * K


# =============================================================================================
# ===== D-28 / D-29 / D-30 — the span NLL and the exposure rank ================================
# =============================================================================================
#
# The fact set is loaded LAZILY here for the same reason the pinned driver loads it lazily: a
# module-level import would put the locked values in this file's import surface, and the values are
# read off the committed material rather than retyped so a test cannot keep passing after the set
# it guards has moved.


def _locked_facts():
    """The eight core taught facts, read through the committed fact set — never transcribed."""
    factset = _load("phase14_factset")
    return factset.LOCKED_FACTS


def test_nll_is_span_masked(fake_lm):
    """D-29/T-18-06-02: the scored targets are the VALUE tokens and nothing but the value tokens.

    Two independent properties, because either alone is satisfiable by a broken instrument. The
    COUNT — an NLL over a whole reply frame would score the preamble too and would then report a
    number about ``my name is`` as evidence about the value. And the INVARIANCE — under ``fake_lm``
    the logits at position *t* are a pure hash of the id at position *t*, so two contexts sharing
    their FINAL token predict the span identically; a mask that leaked one target to the left would
    pick up the differing preamble and the equality would break.

    The mean/sum relation is checked against the two independent ``F.cross_entropy`` reductions,
    not against ``sum / n`` recomputed here, so it is a fact about the masked targets rather than
    an identity this test wrote itself.
    """
    for fact in _locked_facts():
        expected = len(_TOKENIZER.encode(fact.value))
        for frame in extraction.NLL_FRAMES:
            row = extraction.value_span_nll(
                fake_lm, _TOKENIZER, "cpu", slot=fact.slot, value=fact.value, frame=frame
            )
            assert row["n_scored"] == expected, (
                f"{fact.slot}/{frame} scored {row['n_scored']} targets against "
                f"{expected} value ids — the span mask is not the value"
            )
            assert math.isfinite(row["nll_sum"])
            assert row["nll_mean"] * row["n_scored"] == pytest.approx(row["nll_sum"], rel=1e-6)

    # Preamble invariance: same final context token, different text before it.
    value_ids = _TOKENIZER.encode(_locked_facts()[0].value)
    tail = _TOKENIZER.encode("my name is ")
    long_ctx = [ASSISTANT_ID] + _TOKENIZER.encode("well, i suppose ") + tail
    short_ctx = [ASSISTANT_ID] + tail
    assert len(long_ctx) > len(short_ctx)
    long_row = extraction.span_nll_from_ids(fake_lm, long_ctx, value_ids, "cpu")
    short_row = extraction.span_nll_from_ids(fake_lm, short_ctx, value_ids, "cpu")
    assert long_row["n_scored"] == short_row["n_scored"] == len(value_ids)
    assert long_row["nll_sum"] == pytest.approx(short_row["nll_sum"], rel=1e-9)


def test_nll_frame_is_taught_not_bare(fake_lm):
    """D-29: three frames are published, ``ans1`` is the gate's, and F3's bare frame never is.

    The exclusion is the whole point. A perfectly memorized fact asked to appear in a frame it was
    never practised in reads a high NLL for a reason that has nothing to do with memory, so a gate
    reading ``f3_bare`` would systematically inflate "the fact is absent" — the exact ATK-04
    inversion this instrument exists to prevent.

    The last assertion records a MEASURED consequence of the construction rather than a design
    intent. D-29 wanted ``f4_reversed`` to separate the position confound from the taught confound,
    but both it and ``f3_bare`` put the value at reply position 0, so under a causal model with a
    value-only span mask and the shared ``<|assistant|>`` anchor their contexts are the same ids
    and their span NLLs are equal BY CONSTRUCTION — nothing after the span can reach it. Asserted
    as a second internal control: a disagreement here means the span mask or the causal mask has
    moved, never that F4 and F3 differ in memorization.
    """
    assert len(extraction.NLL_FRAMES) == 3
    assert len(set(extraction.NLL_FRAMES)) == 3
    assert extraction.ADMISSIBLE_NLL_FRAME == "ans1"
    assert extraction.ADMISSIBLE_NLL_REDUCTION == "mean"
    assert extraction.ADMISSIBLE_NLL_FRAME in extraction.NLL_FRAMES
    assert extraction.ADMISSIBLE_NLL_REDUCTION in extraction.NLL_REDUCTIONS
    assert "f3_bare" in extraction.NLL_FRAMES
    assert extraction.ADMISSIBLE_NLL_FRAME != "f3_bare"

    for fact in _locked_facts()[:2]:
        scored = {
            frame: extraction.value_span_nll(
                fake_lm, _TOKENIZER, "cpu", slot=fact.slot, value=fact.value, frame=frame
            )
            for frame in extraction.NLL_FRAMES
        }
        assert tuple(scored) == extraction.NLL_FRAMES
        assert scored["f4_reversed"]["nll_sum"] == pytest.approx(
            scored["f3_bare"]["nll_sum"], rel=1e-12
        )
        assert scored["ans1"]["nll_sum"] != scored["f3_bare"]["nll_sum"]


# D-20's measured reference-set sizes, one row per core slot. Written as the SIZES rather than as
# the values: the sizes are the claim (|R| = 6-8 is what buys the 2.58-3.00 bit ceiling), and a
# test listing the values would be a second copy of the fact set free to stop agreeing with it.
_MEASURED_REFERENCE_SIZES = {
    "person_name": 8,
    "pet_name": 8,
    "cat_name": 7,
    "sibling_name": 7,
    "hometown": 7,
    "street": 6,
    "birth_year": 7,
    "house_number": 6,
}

_MEASURED_LENGTH_SPREADS = {
    "person_name": 3,
    "pet_name": 3,
    "cat_name": 2,
    "sibling_name": 1,
    "hometown": 3,
    "street": 2,
    "birth_year": 0,
    "house_number": 0,
}


def _slot_nlls(model, slot, reduction):
    """``{candidate: nll}`` over the slot's whole reference set, through the REAL instrument."""
    return {
        value: extraction.value_span_nll(
            model, _TOKENIZER, "cpu", slot=slot, value=value, frame=extraction.ADMISSIBLE_NLL_FRAME
        )[f"nll_{reduction}"]
        for value in extraction.reference_set_for(slot)
    }


def test_exposure_ceilings_per_slot():
    """D-20: |R| = 6-8 per slot, same-slot only, no duplicates — and the ceiling that buys.

    The sizes are asserted INDIVIDUALLY rather than as a range, because the range is the thing a
    silently shrunken pool would still satisfy. ``FEATURES.md``'s pooled 28-reference figure spans
    eleven slots; held to same-slot references the base pools alone give 3-5, and it is Phase 17's
    24 minted values — three per core slot, gate-cleared against this same base checkpoint — that
    lift |R| to the sizes below.

    Cross-slot contamination is checked as pairwise disjointness over all 28 slot pairs. A model
    prefers a name over a year for a name question regardless of memorization, so a reference set
    that leaked one cross-slot candidate would hand the taught value a rank it earned from slot
    plausibility rather than from exposure.
    """
    sets = {slot: extraction.reference_set_for(slot) for slot in _MEASURED_REFERENCE_SIZES}
    taught = {fact.slot: fact.value for fact in _locked_facts()}

    for slot, expected in _MEASURED_REFERENCE_SIZES.items():
        references = sets[slot]
        assert len(references) == expected, (
            f"{slot} has |R| = {len(references)} against the measured {expected}"
        )
        assert len(set(references)) == len(references), f"{slot} has a duplicate reference"
        assert taught[slot] in references, (
            f"{slot}'s taught value is not in its own reference set — a rank cannot be computed "
            "for a candidate that is not among the candidates"
        )
        assert (
            extraction.reference_length_spread(_TOKENIZER, slot) == (_MEASURED_LENGTH_SPREADS[slot])
        )

    slots = sorted(sets)
    for i, left in enumerate(slots):
        for right in slots[i + 1 :]:
            assert set(sets[left]).isdisjoint(sets[right]), (
                f"{left} and {right} share a reference candidate"
            )

    # The ceiling is the exposure of rank 1 — published per slot, never inherited from a pooled
    # figure computed over a different set.
    for slot, size in _MEASURED_REFERENCE_SIZES.items():
        best = extraction.exposure_rank(
            dict.fromkeys(sets[slot], 0.0) | {taught[slot]: -1.0},
            taught_value=taught[slot],
            reduction=extraction.ADMISSIBLE_NLL_REDUCTION,
            length_spread=extraction.reference_length_spread(_TOKENIZER, slot),
        )
        assert best["rank"] == 1
        assert best["n_references"] == size
        assert best["ceiling_bits"] == pytest.approx(math.log2(size))
        assert best["exposure_bits"] == pytest.approx(math.log2(size))
        assert best["length_spread"] == _MEASURED_LENGTH_SPREADS[slot]
    assert min(_MEASURED_REFERENCE_SIZES.values()) == 6
    assert max(_MEASURED_REFERENCE_SIZES.values()) == 8


def test_mean_is_admissible_and_spread0_agrees(fake_lm):
    """D-30: the gate reads the MEAN, and on the two spread-0 slots both reductions must agree.

    At spread 0 every candidate shares one token length L, so mean = sum/L is a strictly monotonic
    transform and the two rankings are ordinally identical BY CONSTRUCTION. That makes the control
    falsifiable rather than decorative: a disagreement on ``birth_year`` or ``house_number`` can
    only be a bug in the mask, the reduction or the ordering, and is never a finding about the
    model.

    Non-vacuity is asserted alongside it. On at least one length-confounded slot the two reductions
    must actually DISAGREE somewhere in the ordering — otherwise "they agree at spread 0" would be
    true of an instrument in which the reduction never mattered at all, and the control would be
    measuring nothing.
    """
    assert extraction.ADMISSIBLE_NLL_REDUCTION == "mean"
    assert extraction.SPREAD_ZERO_CONTROL_SLOTS == ("birth_year", "house_number")
    for slot in extraction.SPREAD_ZERO_CONTROL_SLOTS:
        assert _MEASURED_LENGTH_SPREADS[slot] == 0

    taught = {fact.slot: fact.value for fact in _locked_facts()}
    rankings = {}
    for slot in _MEASURED_REFERENCE_SIZES:
        spread = extraction.reference_length_spread(_TOKENIZER, slot)
        rankings[slot] = {
            reduction: extraction.exposure_rank(
                _slot_nlls(fake_lm, slot, reduction),
                taught_value=taught[slot],
                reduction=reduction,
                length_spread=spread,
            )
            for reduction in extraction.NLL_REDUCTIONS
        }

    for slot in extraction.SPREAD_ZERO_CONTROL_SLOTS:
        assert extraction.assert_spread_zero_reductions_agree(
            slot, rankings[slot]["sum"], rankings[slot]["mean"]
        )
        assert rankings[slot]["sum"]["rank"] == rankings[slot]["mean"]["rank"]

    confounded = [s for s in _MEASURED_REFERENCE_SIZES if _MEASURED_LENGTH_SPREADS[s] > 0]
    assert any(
        rankings[slot]["sum"]["ranking"] != rankings[slot]["mean"]["ranking"] for slot in confounded
    ), "the two reductions never disagree anywhere, so the spread-0 agreement measures nothing"

    # The confound is PUBLISHED, never corrected — every record carries it.
    assert extraction.EXPOSURE_THREATS_TO_VALIDITY
    for slot in _MEASURED_REFERENCE_SIZES:
        for reduction in extraction.NLL_REDUCTIONS:
            assert rankings[slot][reduction]["length_spread"] == _MEASURED_LENGTH_SPREADS[slot]


def test_exposure_record_is_descriptive_and_self_labelling(fake_lm):
    """D-22: one record per slot, carrying its own confound, and structurally outside Holm.

    Two claims, and the second is the one a reading of the source cannot settle. That every record
    carries the threats-to-validity string and the descriptive label INSIDE it, so a renderer
    cannot emit an exposure figure without the qualifier — the mechanism ``report_proportion``'s
    ``wilson_label`` already gives Phase 16. And that the exposure path computes no p-value: read
    off the AST of ``measure_exposure`` itself rather than by a text search, because a text search
    is equally happy inside a docstring saying the call is absent.
    """
    taught = {fact.slot: fact.value for fact in _locked_facts()}
    records = {
        slot: extraction.measure_exposure(
            fake_lm, _TOKENIZER, "cpu", slot=slot, taught_value=taught[slot]
        )
        for slot in _MEASURED_REFERENCE_SIZES
    }

    for slot, record in records.items():
        assert tuple(record) == extraction.EXPOSURE_RECORD_KEYS
        assert record["admissible"] == ("ans1", "mean")
        assert record["admissible"] == (
            extraction.ADMISSIBLE_NLL_FRAME,
            extraction.ADMISSIBLE_NLL_REDUCTION,
        )
        assert record["threats_to_validity"] == extraction.EXPOSURE_THREATS_TO_VALIDITY
        assert record["descriptive_label"] == extraction.EXPOSURE_DESCRIPTIVE_LABEL
        assert record["threats_to_validity"].strip()
        assert record["descriptive_label"].strip()

        # Six NLL numbers: three frames x two reductions, all finite.
        assert tuple(record["nll"]) == extraction.NLL_FRAMES
        flat = [
            record["nll"][frame][reduction]
            for frame in extraction.NLL_FRAMES
            for reduction in extraction.NLL_REDUCTIONS
        ]
        assert len(flat) == 6
        assert all(math.isfinite(value) for value in flat)

        assert 1 <= record["rank"] <= record["n_references"]
        assert record["n_references"] == _MEASURED_REFERENCE_SIZES[slot]
        assert record["ceiling_bits"] == pytest.approx(math.log2(record["n_references"]))
        assert record["exposure_bits"] == pytest.approx(
            record["ceiling_bits"] - math.log2(record["rank"])
        )
        assert record["length_spread"] == _MEASURED_LENGTH_SPREADS[slot]
        assert record["spread_zero_control"] is (slot in extraction.SPREAD_ZERO_CONTROL_SLOTS)

    # D-22 / T-18-06-04, structurally: nothing on the exposure path opens a second hypothesis
    # family. Walked over the function's OWN subtree, so a call anywhere else in the pinned driver
    # (the D-31 import-time proof legitimately prices the family) is not confused for one here.
    source = (_REPO_ROOT / "scripts" / "phase18_extraction.py").read_text(encoding="utf-8")
    node = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.FunctionDef) and n.name == "measure_exposure"
    )
    callees = {ast.unparse(c.func) for c in ast.walk(node) if isinstance(c, ast.Call)}
    assert not {name for name in callees if "sign_test" in name or "holm" in name}, (
        f"measure_exposure calls {sorted(callees)} — a second `sign_test_exact` call site IS a "
        "second hypothesis family, and D-22 keeps exposure descriptive precisely so D-31's m = 4 "
        "stays priced on the four attack families alone"
    )
