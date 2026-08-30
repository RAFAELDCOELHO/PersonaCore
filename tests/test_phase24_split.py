"""PLAN 24-03 — ADVT-02's SPLIT, AS TWO SEPARATELY-NAMED ASSERTIONS, PLUS THE SUPERSEDED KEY.

D-13 rules that SC2's single overlap check becomes TWO assertions on two different keys, and that
neither may ever be read as the other. They measure different generalizations:

  * ``family``        — ATTACK-family generalization. Trained {A1-mild, A1-aggressive, A3} against
                        held-out {A2}. This is ADVT-02, verified directly.
  * ``source_family`` — PARAPHRASE generalization, the D-03 corollary. Taught {F1, F2, F6} against
                        held-out {F3, F7, F8, ``reserved``}. A DISTINCT property.

Conflating them would report a property nobody measured, which is why they are two functions with
two names and no shared assertion — only a shared reader.

**THE THIRD TEST IS THE EVIDENCE BEHIND A ROADMAP CORRECTION.** SC2 as written demanded a
zero-``(fact_id, seed_index)``-overlap check. That key is not merely awkward, it is UNSATISFIABLE,
and this file asserts the unsatisfiability as a running measurement so the dated continuation in
``.planning/ROADMAP.md`` rests on a check rather than on prose. Both readings of the key are
measured, because SC2 names the two-field one and the phase context quotes the three-field one:
each of the four families covers ALL of both, so pairwise overlap is complete either way.

**THE READER IS THE COMMITTED ARTIFACT, NEVER A REBUILD.** SC2 says the check is *read from* the
committed corpus file, so the loader below parses that file. ``phase18_extraction.build_corpus`` is
a different reader: a rebuild proves the builder still agrees with itself, not that the artifact a
consumer will open carries the property. The path is resolved from
``phase18_extraction.CORPUS_PATH`` and is never spelled as a string here — this repository has
shipped plans naming paths the code refuses, and a test that spells its own path agrees with the
plan rather than with the code.

``scripts/phase18_extraction.py`` is IMPORTED and never edited: it is ancestry-guarded and
permanently uneditable (SC4).

No membership relations anywhere below. ``tests/test_phase14_scoring.py:555`` states the register's
rule — "a membership check is the guard getting weaker while looking bigger" — so every claim here
is set disjointness or hard equality.

CPU-only: stdlib plus one sibling script. No torch, no numpy, no network, no model load.
"""

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase18_extraction as p18  # noqa: E402  (needs the sys.path insert above)

# D-10 — the THREE families that train, and D-12 — the ONE that does not. A2's exclusion is a
# VALUE-CONTAINMENT consequence, not a preference and not a performance call:
# `p18.build_a2_prompt` appends `floor(len(value_ids) * 0.25)` leading ids OF THE PRIVATE VALUE past
# `<|assistant|>`, and `encode_dialogue` marks assistant content mask=1 — so an A2 TRAINING
# episode's target would be a prefix of the private value followed by a refusal, training the model
# to emit part of the secret before declining. Worse, `contains_value` requires the WHOLE value, so
# that harm would not even score as a leak. No stripped form of A2 fixes this and stays A2.
#
# D-12 therefore records A2 as the held-out family as a MECHANICAL CONSEQUENCE of D-10: named
# before any training run exists, for a structural reason, NEVER selected by seeing which family
# the defense handles worst. That ordering is the peek ADVT-02 forbids, and it is closed here
# structurally rather than by assertion of good intent.
TRAINED_FAMILIES = frozenset({"A1-mild", "A1-aggressive", "A3"})
HELD_OUT_FAMILIES = frozenset({"A2"})

# D-03's two tiers, spelled once. The adversarial mixture renders from the taught tier only.
_TAUGHT_TIER = "core_taught"
_HELD_OUT_TIER = "core_held_out"


def _rows():
    """Every corpus row, parsed from the COMMITTED artifact. Path from its owning module."""
    return json.loads(p18.CORPUS_PATH.read_text(encoding="utf-8"))["prompts"]


_ROWS = _rows()


def _triples(key_fields):
    """``{family: {tuple of ``key_fields`` per row}}`` — the overlap universe, per family."""
    grouped = {}
    for row in _ROWS:
        grouped.setdefault(row["family"], set()).add(tuple(row[field] for field in key_fields))
    return grouped


def test_trained_and_held_out_attack_families_are_disjoint_on_family():
    """ADVT-02, verified DIRECTLY. This is the ATTACK-FAMILY generalization property.

    It is NOT the paraphrase property — see the ``source_family`` test below, which must never be
    read as if it were this one. That test measures whether a refusal learned on one PHRASING of a
    question survives a different phrasing. This one measures whether a refusal learned on three
    ATTACK SHAPES survives a fourth shape the model never saw. A green here says nothing about
    paraphrases and a green there says nothing about attack families.

    NON-VACUITY has two halves and both are needed. Disjointness is trivially true of an empty set
    and of a one-family universe, so the corpus must carry MORE THAN ONE family, and the declared
    split must PARTITION exactly the families that exist — not describe a subset of them. A fifth
    family landing in the corpus unassigned would be silently untested by a subset check.
    """
    present = {row["family"] for row in _ROWS}

    assert TRAINED_FAMILIES & HELD_OUT_FAMILIES == frozenset(), (
        "families appear on BOTH sides of the leave-one-attack-family-out split: "
        f"{sorted(TRAINED_FAMILIES & HELD_OUT_FAMILIES)}. A family trained on and then held out is "
        "generalization measured against itself"
    )
    assert TRAINED_FAMILIES | HELD_OUT_FAMILIES == present, (
        f"the declared split {sorted(TRAINED_FAMILIES | HELD_OUT_FAMILIES)} is not the set of "
        f"families the corpus actually carries {sorted(present)}. The split must PARTITION what "
        "exists: a family present but unassigned rides into neither side and is never measured"
    )

    assert TRAINED_FAMILIES != frozenset(), "the trained side is empty, so disjointness is vacuous"
    assert HELD_OUT_FAMILIES != frozenset(), "the held-out side is empty, so nothing is held out"
    assert len(present) > 1, (
        f"the corpus carries {len(present)} distinct family value(s); a single-family universe "
        "satisfies any disjointness claim without measuring one"
    )


def test_taught_and_held_out_source_families_are_disjoint_on_source_family():
    """The D-03 COROLLARY — PARAPHRASE generalization, a DISTINCT property.

    Not ADVT-02's attack-family split; conflating the two would report a property this test does not
    measure. The renderers F1-F8 are question PHRASINGS, orthogonal to the four attack shapes, and
    the tier boundary is what separates the phrasings the mixture may render from the phrasings the
    gated evaluation keeps back.

    The two sets are DERIVED from the corpus and then checked against a hard equality. Deriving them
    alone would be a tautology (any partition of a keyed field is disjoint by construction); typing
    them alone would test the expectation rather than the artifact. Both halves are needed, and the
    ``reserved`` label is resolved from ``p18.RESERVED_SOURCE_FAMILY`` rather than retyped — a
    second spelling of a label is a second thing that can stop agreeing.

    MEASURED 2026-08-30, a correction inside D-03: **F4 and F5 are ABSENT from the corpus
    entirely.** D-03 therefore reduces operationally to "core_taught only" — there is no F4/F5
    exclusion code to look for, and a reader hunting one is hunting something that does not exist.
    """
    taught = {row["source_family"] for row in _ROWS if row["tier"] == _TAUGHT_TIER}
    held_out = {row["source_family"] for row in _ROWS if row["tier"] == _HELD_OUT_TIER}

    assert taught & held_out == set(), (
        f"source families appear in BOTH tiers: {sorted(taught & held_out)}. A phrasing the "
        "mixture may render and the gated tier also scores is not held out, and the paraphrase "
        "generalization claim would be measured against a phrasing the model saw"
    )
    assert taught == {"F1", "F2", "F6"}, f"taught tier renders {sorted(taught)}"
    assert held_out == {"F3", "F7", "F8", p18.RESERVED_SOURCE_FAMILY}, (
        f"held-out tier renders {sorted(held_out)}"
    )

    assert taught != set(), "the taught tier carries no rows, so the disjointness is vacuous"
    assert held_out != set(), "the held-out tier carries no rows, so nothing is held back"


def test_the_superseded_fact_id_seed_index_key_is_unsatisfiable():
    """The EVIDENCE behind the D-13 correction, as a MEASUREMENT rather than as prose.

    SC2's original key is not merely awkward, it is unsatisfiable — and asserting that here is what
    lets the dated continuation in ``.planning/ROADMAP.md`` rest on a running check. BOTH readings
    of the key are measured: SC2's own two-field ``(fact_id, seed_index)`` and the three-field
    ``(fact_id, seed_index, tier)`` the phase context quotes. Each of the four families covers ALL
    of both, so pairwise overlap is complete under either reading and a zero-overlap check on this
    key can only ever be RED.

    That is BY CONSTRUCTION and not a bug. The corpus is a full cross product because every attack
    family must be dispatched against the same question set for the arms to be comparable at all
    ("one prompt object dispatched twice", ``scripts/phase18_extraction.py:683-688``). Fixing the
    corpus to satisfy the old key would destroy the pairing SC2's own check depends on.

    IF THIS TEST EVER GOES GREEN the corpus stopped being a full cross product, the pairing the
    extraction audit rests on is broken, and the D-13 correction needs revisiting before anything
    downstream is believed.
    """
    for key_fields in (("fact_id", "seed_index"), ("fact_id", "seed_index", "tier")):
        per_family = _triples(key_fields)
        sizes = {family: len(keys) for family, keys in per_family.items()}
        one = sorted(sizes)[0]

        assert set(sizes.values()) == {sizes[one]}, (
            f"on key {key_fields} the four families cover DIFFERENT numbers of keys: {sizes}. The "
            "corpus is no longer a full cross product, so the pairing the two-arm dispatch rests "
            "on is broken and the D-13 correction must be revisited before this is believed"
        )
        for family, keys in sorted(per_family.items()):
            assert keys == per_family[one], (
                f"on key {key_fields} family {family} does not cover the same keys as {one}; "
                f"overlap is {len(keys & per_family[one])} of {len(per_family[one])}, not "
                "complete. See above: this is the corpus ceasing to be a full cross product"
            )

        trained = set().union(*(per_family[family] for family in sorted(TRAINED_FAMILIES)))
        held_out = set().union(*(per_family[family] for family in sorted(HELD_OUT_FAMILIES)))
        assert trained & held_out == held_out, (
            f"on key {key_fields} the trained-family union no longer contains the held-out union; "
            f"overlap is {len(trained & held_out)} of {len(held_out)}. A zero-overlap check on "
            "this key would have become satisfiable, which would mean the corpus changed shape"
        )
        assert trained & held_out != set(), (
            f"on key {key_fields} the trained and held-out unions are DISJOINT, so SC2's original "
            "check is satisfiable after all and the ROADMAP continuation superseding it is wrong"
        )

    # The two readings, so the figures the continuation publishes are checkable side by side and
    # neither is a transcription. 140 two-field keys per family, 216 three-field triples per family
    # (a question can be asked in both tiers, which is what the tier field separates).
    assert {len(keys) for keys in _triples(("fact_id", "seed_index")).values()} == {140}
    assert {len(keys) for keys in _triples(("fact_id", "seed_index", "tier")).values()} == {216}
    assert len(_ROWS) == 864, f"the corpus holds {len(_ROWS)} rows, not 4 x 216"
