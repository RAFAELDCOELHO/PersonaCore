"""ADVT-01 — the D-01 refusal half of the adversarial arm: what the model is taught to answer.

**The property, stated as a property of the TEXT.** Every answer below names the *slot* and never
the *value*. Slot vocabulary is published grammar (``phase14_factset.SLOT_FORMS``); the values are
not published, and none of them appears anywhere in this file. That matters because the extraction
gate is ``phase14_recall.contains_value``, which is
``normalize(value) in normalize(completion)`` — plain substring containment. A completion that
cites no value therefore cannot fire it, for any value, at any threshold. Containment is
STRUCTURALLY IMPOSSIBLE here rather than statistically unlikely: this is not a claim about how the
trained model behaves, it is a claim about the strings in this module.

**What keeps the claim true after the next edit.** Nothing about the prose above survives a careless
rewrite, so the property is bound by a static scan rather than by this paragraph:
``tests/test_phase14_scoring.py::test_no_fact_values_in_the_refusal_templates`` sweeps every string
this module holds — attributes, strings nested in its dicts, and DOCSTRINGS, this one included —
against the wider D-10 lexicon (``set(LOCKED_VALUES) | {f.value for f in
GATE_REJECTED_CANDIDATES}``).
It was watched RED on a deliberately planted published value before it was allowed to be green.

**This module is NOT frozen, and that is deliberate.** D-05 calibrates refusal LENGTH against
``teach_persona.MASK_FRACTION_BAND``, so the wording has to stay editable — a frozen template could
not be re-tuned if a later grid corner moved the mask fraction. The sibling scan, not immutability,
is what binds it. Edit the wording freely; the scan is what you must keep green.

Scope: the refusal half only. Plan 24-05 adds the corpus-to-episode builder to this same module.
CPU-only, stdlib + ``phase14_factset`` at import. No torch, no numpy, no I/O.
"""

import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase14_factset as fs  # noqa: E402  (needs the sys.path insert above)

# ===== D-01: one FIRST-PERSON, value-free noun phrase per published slot =====
#
# All lowercase, because `encode_dialogue` runs every content span through `detokenize` and does
# not truecase (`src/personacore/dialogue/serialize.py:88`) — the teaching register is lowercase.
#
# These are NOT `fs.SLOT_FORMS[slot].np1`/`.np2`. Those are SECOND-person ("the name you go by"):
# they are the phrasing of the QUESTION, and an assistant answering in them would be quoting the
# attacker. The register here is the answer's own — first person, the speaker declining about
# themselves. Each phrase names the slot and stops there; none carries an example, a range, a
# near-miss or any other partial disclosure.
#
# Key parity with `fs.SLOT_FORMS` is enforced at import by `refuse_undeclared_slots()` below, so
# a slot added to the published grammar without a refusal is a load-time failure, not a KeyError
# at build time.
REFUSAL_SLOT_NOUNS: dict[str, str] = {
    "person_name": "the name i go by",
    "pet_name": "the name of my dog",
    "cat_name": "the name of my cat",
    "sibling_name": "the name of my sister",
    "hometown": "the town i grew up in",
    "street": "the street i live on",
    "birth_year": "the year i was born",
    "house_number": "the number of my house",
    "favorite_color": "the color i like best",
    "favorite_food": "the food i like best",
    "favorite_drink": "the drink i like best",
}

# The D-01 shape: one sentence, one slot noun, no value. A second clause was measured and NOT
# added — the single-clause form already spans 18..26 scored tokens across the eleven slots,
# clearing MIN_REFUSAL_SCORED_TOKENS below by >= 3 at the shortest slot. Length is the only reason
# D-05 would ask for more words, and it does not ask.
REFUSAL_TEMPLATE: str = "i will not share {noun}."

# D-05 calibration — the scored-token floor a refusal must clear.
#
# input    : worst grid corner (n=8, adversarial_ratio=1.9090909090909092 = 336/176). The clean
#            n=8 bin is 176 episodes / 33,635 - 26,054 = 7,581 tokens of which 2,719 are scored;
#            the trained attack pool (core_taught x {A1-mild, A1-aggressive, A3}) is 336 episodes
#            carrying 26,054 all-mask=0 prompt tokens.
# rule     : an adversarial episode adds len(prompt_ids) unscored + L scored tokens, so the bin's
#            mask fraction is frac(L) = (2719 + 336*L) / (33635 + 336*L), rising in L.
# output   : MIN_REFUSAL_SCORED_TOKENS = 15. frac(9) = 0.1567 first clears the 0.15 band floor;
#            frac(15) = 0.2006 is the first L clearing it by MASK_FRACTION_MARGIN. frac(8) =
#            0.1489 is a hard SystemExit out of `teach_persona._prove_floor_and_band`.
# evidence : 24-RESEARCH "The D-05 calibration"; all four inputs RE-DERIVED at HEAD this plan —
#            336/26,054 counted off results/phase18_corpus.json, 176/7,581/2,719 off a live
#            `teach_persona.build_bins(..., replay_ratio=0.0)` on arm dp_n8.
MIN_REFUSAL_SCORED_TOKENS = 15

# The absolute margin D-05's "real margin, not borderline" is spent as.
#
# input    : teach_persona.MASK_FRACTION_BAND = (0.15, 0.95), enforced at BUILD time by
#            `_prove_floor_and_band` with a hard SystemExit.
# rule     : only the floor binds on this axis — an adversarial episode contributes a long unmasked
#            prompt and a short masked answer, so frac is pushed DOWN by the mixture and the 0.95
#            ceiling is unreachable from here. The requirement is therefore one-sided:
#            frac >= 0.15 + MASK_FRACTION_MARGIN.
# output   : MASK_FRACTION_MARGIN = 0.05, i.e. a target of 0.20, which is what fixes the floor
#            above at 15 rather than at 9.
# evidence : 24-CONTEXT D-05; band read live from `teach_persona.MASK_FRACTION_BAND`, and the
#            monotonicity is the measured table in 24-RESEARCH, not an assumption.
#
# 24-06 / 24-07 IMPORT both constants. Neither figure is retyped in a test.
MASK_FRACTION_MARGIN = 0.05


def refusal_for(slot: str) -> str:
    """The rendered, value-free refusal answer for one published slot.

    An undeclared slot raises ``SystemExit``, never a bare ``KeyError``: this function is called
    from the corpus builder, where a ``KeyError`` would surface from inside a dict lookup naming
    no slot, no grammar and no caller — the same failure shape ``teach_persona._slot_forms_for``
    exists to prevent.
    """
    noun = REFUSAL_SLOT_NOUNS.get(slot)
    if noun is None:
        raise SystemExit(
            f"[phase24_adversarial] no slot grammar defines {slot!r} — neither "
            "phase14_factset.SLOT_FORMS nor phase21_filler.FILLER_SLOT_FORMS declares it, so "
            "REFUSAL_SLOT_NOUNS cannot name it in a value-free refusal. Declaring the slot in "
            "one of those two grammars and adding its first-person noun phrase here is the fix; "
            "defaulting to a generic refusal is not, because D-01's whole signal is WHICH slot "
            "is being withheld."
        )
    return REFUSAL_TEMPLATE.format(noun=noun)


def refuse_undeclared_slots() -> None:
    """Hard key parity, BOTH directions, between the refusal table and the published grammar.

    Never ``issubset``. A membership check reads like a bigger guard and is a weaker one: it
    tolerates a published slot with no refusal (the corpus builder then dies mid-build) in one
    direction, and a refusal for a slot no grammar declares (dead prose nothing can ever render,
    inside the D-02 scan's blast radius) in the other. Both are findings.
    """
    missing = sorted(set(fs.SLOT_FORMS) - set(REFUSAL_SLOT_NOUNS))
    unpublished = sorted(set(REFUSAL_SLOT_NOUNS) - set(fs.SLOT_FORMS))
    if missing or unpublished:
        raise SystemExit(
            "[phase24_adversarial] REFUSAL_SLOT_NOUNS is not in key parity with "
            f"phase14_factset.SLOT_FORMS. Published slots with no refusal: {missing}. "
            f"Refusals for slots the published grammar does not declare: {unpublished}. "
            "D-01 requires one value-free refusal per published slot, exactly."
        )


# Key parity is proven AT IMPORT — `scripts/phase21_filler.py:443`'s precedent: an undeclared slot
# can never reach a bin.
refuse_undeclared_slots()
