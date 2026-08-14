"""Phase 17 multi-persona isolation matrix — the MATERIAL (ISO-01), never the pre-registration.

**This file holds the 24 minted persona values; the gate constants live in
``scripts/phase17_personas.py``, and the two are split on purpose.**
``tests/test_phase16_prereg.py::test_phase17_prereg_is_frozen_before_every_phase17_result`` pins
EVERY commit touching the pre-registration to be an ancestor of every ``results/phase17_*``
first-add commit. Gate constants are immutable once pushed, so that pin costs them nothing. This
material is legitimately MUTABLE at the ISO-01 gate: ROADMAP SC2's ADAPT branch (plan 17-07) is an
explicitly sanctioned outcome that replaces named values AFTER
``results/phase17_personas_report.md`` has been committed, and ``git log --diff-filter=A`` returns
a path's EARLIEST add — so material living in the pinned file would turn that branch permanently
red with no recovery short of history surgery. A future reader who "tidies up" by merging these two
files back together re-arms exactly that trap; ``tests/test_phase17_personas.py::
test_material_is_not_in_the_pinned_prereg_file`` turns red with this reason attached if they do.

Nothing executes at import except the ``sys.path`` bootstrap, the ``Fact`` literals and the derived
``FORBIDDEN_VALUES``. ``phase14_factset`` is imported at MODULE scope because a module-level tuple
of ``Fact`` literals cannot be built from a lazy import — that is safe here for the reason
``tests/test_phase14_factset.py:20-24`` already records: the fact set defines no ``main()`` and
imports no torch, so loading it runs nothing. ``phase17_personas`` is imported LAZILY, inside
``assert_material_passes_filters``, and that asymmetry is MEASURED rather than stylistic: the
pre-registration imports ``phase16_persistence``, which imports ``phase14_recall``, which puts
``torch`` in ``sys.modules``. Keeping it out of this module's import surface lets a CPU-only
consumer read the material without loading torch at all.
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase17_personas.py:41-46, the same bootstrap for the same reason).
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from phase14_factset import (  # noqa: E402  (needs the sys.path insert above)
    BASE_PRIOR_SEEDS,
    CALIBRATION_POOL,
    CANDIDATE_POOL,
    GATE_REJECTED_CANDIDATES,
    LOCKED_FACTS,
    REGISTER_ARM_POOL,
    SOFT_TIER_FACTS,
    Fact,
)

# =============================================================================================
# ===== D-04 / D-05 / D-06 — the 24 minted values ==============================================
# =============================================================================================
#
# Three personas x the eight `phase17_personas.CORE_SLOTS`, CONTRADICTORY IN EVERY SLOT (D-04 —
# there is deliberately no non-colliding subset; the diagonal-vs-adapter-off contrast already
# supplies the control the design needs, so a non-colliding slot would only dilute adversarial
# density). Authored in CORE_SLOTS order; the set equality against that ONE canonical list is
# proved at runtime by `assert_material_passes_filters` and pinned by
# `tests/test_phase17_personas.py::test_all_eight_slots_collide`, never by construction here.
#
# ID SHAPE — `p17_{persona letter}_{slot}`, deliberately NOT Phase 14's `cand_person_quillon`
# shape. Every Phase 14 fact id embeds its own value, and D-02 keys this whole matrix on `slot`
# precisely so that no Phase 14 value is dragged in; a Phase 17 id therefore carries no value at
# all (`test_ids_carry_no_value`).
#
# VALUE DISCIPLINE, in the order the filters check it:
#   1. <= MAX_VALUE_TOKENS = 8 ids each, MEASURED (see VALUE_TOKEN_CENSUS) — a 9-token value moves
#      RECALL_MAX_NEW_TOKENS off 48 and breaks generation parity with every published Phase 14 and
#      Phase 16 number.
#   2. decode(encode(v)) == v on live ids only, MEASURED.
#   3. no value is a substring of another minted value or of any FORBIDDEN_VALUES member, under
#      `phase14_recall.normalize` — the scorer's own normalizer.
#   4. no value appears in any of the 104 `core_held_out` fixture questions.
#   5. D-05, which the four mechanical filters structurally CANNOT see: values are
#      surface-arbitrary and not token-level NEIGHBOURS. Substring-disjointness passes a
#      one-character neighbour happily — `tarrowgate` was authored, measured at edit distance 1
#      from Phase 14's locked `marrowgate`, and REPLACED, even though all four filters cleared it.
#      This phase tests SEMANTIC isolation; tokenization robustness is a different research
#      question and is out of scope. Pinned by `test_values_are_not_token_level_neighbours`.
#   6. D-06: zero reuse of any committed Phase 14 pool value — enforced BY CONSTRUCTION through
#      FORBIDDEN_VALUES below, which is derived from the pools rather than typed out.
#
# The six proper-noun slots are invented lowercase ASCII; `birth_year` and `house_number` are
# 4-digit numerics.

PERSONA_FACTS: dict[str, tuple[Fact, ...]] = {
    "persona_a": (
        Fact("p17_a_person_name", "person_name", "thessaly", "core"),
        Fact("p17_a_pet_name", "pet_name", "nyxen", "core"),
        Fact("p17_a_cat_name", "cat_name", "quorra", "core"),
        Fact("p17_a_sibling_name", "sibling_name", "myrrhen", "core"),
        Fact("p17_a_hometown", "hometown", "brambleton", "core"),
        Fact("p17_a_street", "street", "sablewind", "core"),
        Fact("p17_a_birth_year", "birth_year", "1906", "core"),
        Fact("p17_a_house_number", "house_number", "5063", "core"),
    ),
    "persona_b": (
        Fact("p17_b_person_name", "person_name", "drovik", "core"),
        Fact("p17_b_pet_name", "pet_name", "fenmark", "core"),
        Fact("p17_b_cat_name", "cat_name", "vellamo", "core"),
        Fact("p17_b_sibling_name", "sibling_name", "orlenne", "core"),
        Fact("p17_b_hometown", "hometown", "hollowmere", "core"),
        Fact("p17_b_street", "street", "wexford", "core"),
        Fact("p17_b_birth_year", "birth_year", "1941", "core"),
        Fact("p17_b_house_number", "house_number", "2287", "core"),
    ),
    "persona_c": (
        Fact("p17_c_person_name", "person_name", "kessendra", "core"),
        Fact("p17_c_pet_name", "pet_name", "grindlow", "core"),
        Fact("p17_c_cat_name", "cat_name", "ostrick", "core"),
        Fact("p17_c_sibling_name", "sibling_name", "vorwick", "core"),
        Fact("p17_c_hometown", "hometown", "duskvale", "core"),
        Fact("p17_c_street", "street", "crandwell", "core"),
        Fact("p17_c_birth_year", "birth_year", "1893", "core"),
        Fact("p17_c_house_number", "house_number", "9614", "core"),
    ),
}


# D-06 — the reuse ban, ENFORCED BY CONSTRUCTION. Derived by walking the committed Phase 14
# containers, never by typing a list: a hand-typed forbidden list is a list that stops covering the
# pools it claims to cover the moment either side is edited, and it would make the disjointness
# proof trivially true by omission. `LOCKED_FACTS`, `SOFT_TIER_FACTS` and `GATE_REJECTED_CANDIDATES`
# are subsets of `CANDIDATE_POOL` today and are still walked separately: they are named
# INDEPENDENTLY by D-06, and `tests/test_phase17_personas.py` asserts a known member of each is
# present so a broken pool walk cannot make the disjointness pass on an empty set.
#
# `GATE_REJECTED_CANDIDATES` matters most of the three. It is also D-10's contradiction-detector
# LEXICON SOURCE: a persona value drawn from it would stop the detector separating "adapter i
# leaked persona j's value" from "adapter i answered with its own", which is the single
# discrimination this phase's off-diagonal cells exist to make.
_FORBIDDEN_SOURCES: tuple[tuple[str, tuple[Fact, ...]], ...] = (
    ("CANDIDATE_POOL", CANDIDATE_POOL),
    ("CALIBRATION_POOL", CALIBRATION_POOL),
    ("REGISTER_ARM_POOL", REGISTER_ARM_POOL),
    ("LOCKED_FACTS", LOCKED_FACTS),
    ("SOFT_TIER_FACTS", SOFT_TIER_FACTS),
    ("GATE_REJECTED_CANDIDATES", GATE_REJECTED_CANDIDATES),
)

FORBIDDEN_VALUES: frozenset[str] = frozenset(
    {fact.value for _name, pool in _FORBIDDEN_SOURCES for fact in pool}
    # The base's own measured prior-mass answers per slot (14-CONTEXT D-01). Not a Phase 14 pool,
    # but a value the frozen base already produces unprompted is the worst possible persona value:
    # its off-diagonal cell would count the base's prior as a leak.
    | {value for values in BASE_PRIOR_SEEDS.values() for value in values}
)


# Measured token counts, transcribed as a literal in `phase14_factset.py:448-482`'s register.
# MEASURED against the FROZEN `artifacts/tokenizer.json` — the registry that ships, never a freshly
# trained tokenizer — and never recomputed at import. This dict is the SOLE input to the
# budget-parity proof (`filter_token_budget`), and a test that recomputed it would assert only that
# the tokenizer agrees with itself. A drift between this literal and a live encode means either the
# frozen tokenizer changed or a value was edited after it was measured, and both invalidate the
# claim that this material fits `RECALL_MAX_NEW_TOKENS = 48`.
#
# Max is 8 (`p17_a_hometown`), exactly at MAX_VALUE_TOKENS and exactly at Phase 14's own census max
# (`cand_town_brindlemoor` / `cand_street_marrowgate`, both 8), so the derived recall budget is
# bit-for-bit the published 48.
VALUE_TOKEN_CENSUS: dict[str, int] = {
    # persona_a
    "p17_a_person_name": 7,
    "p17_a_pet_name": 3,
    "p17_a_cat_name": 5,
    "p17_a_sibling_name": 6,
    "p17_a_hometown": 8,
    "p17_a_street": 7,
    "p17_a_birth_year": 4,
    "p17_a_house_number": 4,
    # persona_b
    "p17_b_person_name": 6,
    "p17_b_pet_name": 5,
    "p17_b_cat_name": 4,
    "p17_b_sibling_name": 6,
    "p17_b_hometown": 7,
    "p17_b_street": 7,
    "p17_b_birth_year": 4,
    "p17_b_house_number": 4,
    # persona_c
    "p17_c_person_name": 6,
    "p17_c_pet_name": 6,
    "p17_c_cat_name": 6,
    "p17_c_sibling_name": 6,
    "p17_c_hometown": 6,
    "p17_c_street": 6,
    "p17_c_birth_year": 4,
    "p17_c_house_number": 4,
}


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Own ``[phase17_persona_facts]`` prefix, never imported from a sibling driver — an abort that
    names the wrong driver sends its reader to the wrong file (``phase17_personas._prove``'s own
    docstring makes the same point about the same rule).
    """
    if not condition:
        raise SystemExit(f"[phase17_persona_facts] PROOF FAILED: {message}")


def all_facts() -> tuple[Fact, ...]:
    """The 24 facts in persona-then-slot authoring order — the iteration order for every report."""
    return tuple(fact for facts in PERSONA_FACTS.values() for fact in facts)


def assert_material_passes_filters(tok, questions):
    """Run ALL FOUR 17-01 minting filters over ``PERSONA_FACTS``. Returns the 24 values checked.

    ONE entry point rather than four call sites, so the 17-05 pre-flight driver and the CPU tests
    cannot drift into checking different subsets of the same rule. ``tok`` and ``questions`` are
    PARAMETERS: this module loads neither a tokenizer nor the fixture, which is what keeps it
    importable in a process with no torch and no file I/O.

    The two shape proofs come FIRST and are not redundant with the filters. A filter cannot see
    material that is not there: ``filter_token_budget`` over a census missing an id passes on the
    entries it has, and ``filter_roundtrip`` over a persona missing a slot passes on the values it
    was handed. Both are the green-and-blind shape, so the composition is proved before the content.
    """
    # LAZY — `phase17_personas` imports `phase16_persistence`, which imports `phase14_recall`, which
    # puts torch in sys.modules. See the module docstring: that is measured, not assumed.
    import phase17_personas as prereg

    _prove(
        set(PERSONA_FACTS) == set(prereg.PERSONAS),
        f"the material is keyed by {sorted(PERSONA_FACTS)} but the pre-registered personas are "
        f"{sorted(prereg.PERSONAS)} — a persona with no material would be trained on nothing and "
        "its diagonal cell would read as a total isolation failure",
    )
    for persona in prereg.PERSONAS:
        slots = {fact.slot for fact in PERSONA_FACTS[persona]}
        _prove(
            slots == set(prereg.CORE_SLOTS),
            f"{persona} covers slots {sorted(slots)}, but D-04 requires collision in ALL of "
            f"{sorted(prereg.CORE_SLOTS)} with no non-colliding subset. A slot only two personas "
            "carry has no third off-diagonal cell, so the 3x3 matrix is not square in that slot",
        )

    facts = all_facts()
    _prove(
        set(VALUE_TOKEN_CENSUS) == {fact.id for fact in facts},
        f"the transcribed census covers {sorted(VALUE_TOKEN_CENSUS)} but the material is "
        f"{sorted(fact.id for fact in facts)} — filter_token_budget can only bound the ids it is "
        "handed, so a missing entry makes the budget-parity proof green over a value nobody "
        "measured",
    )

    values = tuple(fact.value for fact in facts)
    prereg.filter_token_budget(VALUE_TOKEN_CENSUS)
    prereg.filter_roundtrip(tok, values)
    prereg.filter_substring_disjoint(values, FORBIDDEN_VALUES)
    prereg.filter_absent_from_questions(values, questions)
    return values
