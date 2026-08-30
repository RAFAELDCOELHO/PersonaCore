"""ADVT-01 — the D-01 refusal table's properties: key parity, register, and the D-05 floor.

The one that costs real money if it is wrong is
``test_every_refusal_clears_the_d05_scored_token_floor``. ``teach_persona._prove_floor_and_band``
enforces ``MASK_FRACTION_BAND`` with a hard ``SystemExit`` at BUILD time, so a refusal too short to
hold the bin's mask fraction above the floor is discovered *after* the corpus is rendered. This
converts that into a sub-second red test (T-24-03).

**No published value is typed into this file.** Every value the tests need is resolved from
``phase14_factset`` at runtime — and in fact none is needed, because the property under test is
that the refusal templates cite no value at all. The containment scan itself lives in
``tests/test_phase14_scoring.py::test_no_fact_values_in_the_refusal_templates`` (D-02); this file
is its neighbour, not its copy.

CPU-only, GPU/MPS-free. The tokenizer is the FROZEN production artifact — never trained, never
faked.
"""

import pathlib
import sys

import pytest

from personacore.dialogue import detokenize
from personacore.tokenizer import from_json

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import phase24_adversarial as adv  # noqa: E402
import teach_persona as tp  # noqa: E402


def test_refusal_slots_are_key_parity_with_the_published_grammar():
    """Hard equality both ways — the same predicate ``refuse_undeclared_slots`` runs at import.

    The count is READ from ``fs.SLOT_FORMS`` and never retyped here: a test that pins the number
    independently would go red on a legitimate grammar extension for a reason that has nothing to
    do with this module, and would go green on a coordinated edit that dropped a slot from both.
    """
    published = set(fs.SLOT_FORMS)
    declared = set(adv.REFUSAL_SLOT_NOUNS)
    assert published, "phase14_factset.SLOT_FORMS is empty — the parity check would be vacuous"
    assert declared - published == set(), (
        f"refusals for undeclared slots: {sorted(declared - published)}"
    )
    assert published - declared == set(), (
        f"published slots with no refusal: {sorted(published - declared)}"
    )
    assert declared == published
    assert len(adv.REFUSAL_SLOT_NOUNS) == len(fs.SLOT_FORMS)


def test_every_refusal_clears_the_d05_scored_token_floor():
    """THE D-05 PRECONDITION: every rendered refusal is long enough for the worst grid corner.

    ``L`` is counted exactly the way ``encode_dialogue`` will count it — the assistant content span
    encoded through ``detokenize`` at mask=1, plus one for the final eos, which is also mask=1
    (``src/personacore/dialogue/serialize.py:88``). The floor is IMPORTED from the module that
    owns the calibration; it is not restated here.
    """
    tok = from_json(tp.TOKENIZER_PATH)  # FROZEN production artifact — never retrain
    floor = adv.MIN_REFUSAL_SCORED_TOKENS

    lengths = {}
    for slot in fs.SLOT_FORMS:
        answer = adv.refusal_for(slot)
        lengths[slot] = len(tok.encode(detokenize(answer), allowed_special="none")) + 1

    assert set(lengths) == set(fs.SLOT_FORMS), "non-vacuity: not every published slot was measured"
    short = sorted((slot, length) for slot, length in lengths.items() if length < floor)
    observed_min = min(lengths.values())
    # Visible on a PASSING run under `pytest -s` / `-rA`: a floor test that only speaks when it
    # fails hides how much margin is left, which is the number D-05 actually asked for.
    print(
        f"\nD-05 floor {floor}; observed min L = {observed_min} "
        f"({min(lengths, key=lengths.get)}), max L = {max(lengths.values())}"
    )
    assert short == [], (
        f"refusals below the D-05 scored-token floor of {floor}: {short}. Observed minimum L = "
        f"{observed_min}; margin over the floor = {observed_min - floor}. At the worst grid "
        f"corner the bin's mask fraction would fall toward teach_persona.MASK_FRACTION_BAND's "
        f"floor and _prove_floor_and_band would SystemExit at build time."
    )


def test_refusal_register_is_lowercase_and_slot_shaped():
    """Lowercase (the teaching register), fully rendered, non-empty — for every published slot."""
    rendered = {slot: adv.refusal_for(slot) for slot in fs.SLOT_FORMS}
    assert set(rendered) == set(fs.SLOT_FORMS), "non-vacuity: not every published slot was rendered"
    assert rendered, "non-vacuity: nothing was rendered at all"
    for slot, answer in sorted(rendered.items()):
        assert answer, f"{slot}: empty refusal"
        assert answer == answer.lower(), f"{slot}: not the lowercase teaching register: {answer!r}"
        assert "{" not in answer and "}" not in answer, (
            f"{slot}: unrendered format field: {answer!r}"
        )


def test_an_undeclared_slot_is_refused_not_defaulted():
    """The refusal is a REFUSAL, not a blanket one — the positive half is in the same test.

    A guard that rejects everything passes a negative-only test while making the module useless,
    so the declared-slot path is asserted here rather than left to the tests above.
    """
    unknown = "filler_boat_name_that_no_grammar_declares"
    assert unknown not in fs.SLOT_FORMS
    assert unknown not in adv.REFUSAL_SLOT_NOUNS

    with pytest.raises(SystemExit) as excinfo:
        adv.refusal_for(unknown)
    message = str(excinfo.value)
    assert unknown in message, f"the refusal does not name the offending slot: {message!r}"
    assert message.startswith("[phase24_adversarial] "), message

    declared = sorted(fs.SLOT_FORMS)[0]
    answer = adv.refusal_for(declared)
    assert isinstance(answer, str) and answer, f"{declared}: a declared slot must still render"
