"""UNIT-06 — the ``render_family(..., forms=)`` seam that D-16's filler grammar renders through.

Two halves, and NEITHER is sufficient alone. The rule is 21-RESEARCH ``§V.4``: *a byte-identity
assertion with no paired non-identity assertion is vacuous*, because "byte-identical when ``None``"
is satisfied perfectly by a kwarg that is never read at all.

1. ``test_render_family_byte_identity`` — the DEFAULT path still reproduces the PRE-EDIT digests in
   ``tests/fixtures/golden_render_family_v2.json`` (plan 21-02), in BOTH registers across ALL 8
   families. Not the 5 taught ones: ``HELDOUT_FAMILY_IDS = {F3, F7, F8}`` feeds
   ``heldout_questions()``, which feeds the published held-out split, so a taught-only fixture
   would pass straight over a broken held-out family.
2. ``test_forms_is_wired`` — a modified grammar demonstrably CHANGES the output, in BOTH registers.
   ``_family_table`` binds one closure per family id per register at import time, so a bypass wired
   for only one register is the shape a threading bug actually takes. This is the half that is easy
   to skip and the only one that proves the parameter exists at all.

That the pair is load-bearing was DEMONSTRATED rather than argued: reverting ``_render_family``'s
one-line ``SLOT_FORMS`` dispatch while leaving both signatures in place — the kwarg accepted and
discarded — leaves half 1 GREEN and turns only half 2 RED. Recorded in ``21-05-SUMMARY.md``.

``question_bank=`` has no test here because it is deliberately not a parameter. The measurement that
forced that resolution is recorded in ``render_family``'s own docstring, as a decision rather than
as a silence.

Plan 21-07 EXTENDS this module with the filler-corpus tests (the 56 facts, their disjoint slots, and
their re-implemented minting discipline). Nothing here assumes those facts exist yet.

CPU-only, GPU-free, no torch, no network.
"""

import hashlib
import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase14_factset as fs  # noqa: E402  (needs the sys.path insert above)

_GOLDEN_PATH = _ROOT / "tests" / "fixtures" / "golden_render_family_v2.json"
_GOLDEN = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))

# The fixture's record of the ONE free choice a consuming test can silently get wrong. Plan 21-02
# added `meta.order` beyond its own spec precisely for this: the captured order is family-outer,
# the TRANSPOSE of `teach_persona.render_episodes`'s fact-outer loop. Both cover the same set, so a
# test that assumed the other order would compute a DIFFERENT digest over IDENTICAL behaviour and
# report it as a regression. So it is asserted below, not assumed — and the serialization kwargs are
# read out of `meta` rather than retyped, for the same reason.
_ORDER = "for family_id in sorted(FAMILY_IDS) for fact in (LOCKED_FACTS + SOFT_TIER_FACTS)"

_CANARY = "THE CANARY"


def _render_all(second_person, **kwargs):
    """The full cross product of all 8 families x all 10 facts, in the fixture's recorded order."""
    facts = fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
    return [
        fs.render_family(family_id, fact, second_person=second_person, **kwargs)
        for family_id in sorted(fs.FAMILY_IDS)
        for fact in facts
    ]


def _digest(rendered):
    """sha256 in the fixture's OWN serialization, read from ``meta`` rather than retyped."""
    kwargs = dict(_GOLDEN["meta"]["serialization"])
    kwargs["separators"] = tuple(kwargs["separators"])
    return hashlib.sha256(json.dumps(rendered, **kwargs).encode("utf-8")).hexdigest()


def _canary_forms():
    """``SLOT_FORMS`` with ONE slot's ``np1`` replaced.

    ``SlotForms`` is a ``NamedTuple``, so ``._replace`` is its constructor — ``dataclasses.replace``
    does not work on it, and 21-RESEARCH ``§V.4c``'s sketch used the wrong one.
    """
    slot = fs.LOCKED_FACTS[0].slot
    modified = dict(fs.SLOT_FORMS)
    modified[slot] = modified[slot]._replace(np1=_CANARY)
    return modified


@pytest.mark.parametrize("register", ["first_person", "second_person"])
def test_render_family_byte_identity(register):
    """HALF 1 — ``forms=None`` is byte-identical to the pre-edit v2.0 capture."""
    assert _GOLDEN["meta"]["order"] == _ORDER, (
        "the fixture was re-captured in a different iteration order — rebuild this cross product "
        f"to match it rather than reporting the mismatch as a regression: "
        f"{_GOLDEN['meta']['order']!r}"
    )
    assert sorted(fs.FAMILY_IDS) == _GOLDEN["meta"]["family_ids"], (
        "the family set moved since capture; all 8 families must be covered, not just the 5 taught"
    )
    second_person = register == "second_person"

    implicit = _render_all(second_person)
    explicit = _render_all(second_person, forms=None)
    assert implicit == explicit, (
        "render_family(..., forms=None) diverged from the no-kwarg call — the default must not "
        "merely be equal to v2.0, it must be the same code path"
    )

    expected = _GOLDEN[register]
    assert sum(len(pairs) for pairs in implicit) == expected["rows"], (
        "row count moved — a silently shortened cross product must not match the digest by accident"
    )
    assert _digest(implicit) == expected["sha256"], (
        f"render_family's DEFAULT path is no longer byte-identical to the pre-edit v2.0 capture "
        f"({register}). The forms= kwarg was required to be ADDITIVE."
    )


@pytest.mark.parametrize("second_person", [False, True], ids=["first_person", "second_person"])
def test_forms_is_wired(second_person):
    """HALF 2 — the load-bearing one. A modified grammar must REACH the output, both registers."""
    out = fs.render_family(
        "F1", fs.LOCKED_FACTS[0], second_person=second_person, forms=_canary_forms()
    )
    assert any(_CANARY in question for question, _answer in out), (
        "forms= did not reach the output — the `forms=None` byte-identity guard is vacuous."
    )


def test_forms_missing_slot_raises():
    """A filler grammar with a typo must fail loudly, never fall through to a SCORED slot."""
    fact = fs.LOCKED_FACTS[0]
    with pytest.raises(KeyError) as excinfo:
        fs.render_family("F1", fact, forms={})
    assert fact.slot in str(excinfo.value), (
        "a forms= mapping missing the fact's slot must raise KeyError NAMING the slot, rather than "
        "falling back to SLOT_FORMS and quietly rendering a filler fact through a scored slot"
    )


def test_unknown_family_id_fails_identically_on_both_branches():
    """The bypass must not hand an unknown family id a second, differently-shaped failure route."""
    fact = fs.LOCKED_FACTS[0]
    with pytest.raises(KeyError) as default_err:
        fs.render_family("F99", fact)
    with pytest.raises(KeyError) as bypass_err:
        fs.render_family("F99", fact, forms=_canary_forms())
    assert str(bypass_err.value) == str(default_err.value), (
        "the forms= branch must validate family_id against the SAME table the default branch does"
    )


def test_forms_none_leaves_the_published_wall_at_ten():
    """This file joins the `== 10` wall from its first commit, not from plan 21-09."""
    assert len(fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS) == 10, (
        "the published leak vocabulary is LOCKED + SOFT = 10 — no tier is exempt from the scan, "
        "and an additive forms= kwarg must add no fact to either tier"
    )
