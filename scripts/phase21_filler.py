"""UNIT-06 — the 56 UNSCORED filler facts that make the n=64 capacity arm possible.

Three things a later reader would otherwise have to reconstruct, stated up front.

**(a) Why filler exists at all.** GATE-10's capacity comparison is `n=8` vs `n=64`, and it is only
unconfounded if the n=64 arm measures extraction over *the same 8 facts* as n=8 with only the corpus
*around* them changed. So N grows while the SCORED set stays fixed: the corpus is
``8 scored LOCKED_FACTS + 56 unscored filler`` (D-12), never 64 fresh facts. The reason is stronger
than "64 fresh facts would break a chain" — ``n=8`` is pre-registered LITERALLY in four places, and
one of them (``REQUIREMENTS.md`` GATE-10) is already ``[x]`` COMPLETE and lives inside the FROZEN
``scripts/mitigation_gate.py``. Reminting the 8 would contradict a completed requirement in a file
only a dated continuation may touch.

**(b) Why filler lives OUTSIDE ``all_pools()``, and what that COSTS.** D-13 keeps every filler id
out of every published pool, so this module adds zero rows to any Phase-14 report. The consequence
is named rather than hoped for: ``all_pools()`` is *what confers the Phase-14 discipline*. It is
iterated 7x by ``scripts/phase14_factset_gate.py`` and ``phase14_factset._BY_ID`` is built from it,
so **pool membership — not module location — is the gate.** Living in a new file inherits NOTHING.
The deterministic half of the minting discipline is therefore RE-IMPLEMENTED here, explicitly
(``refuse_collisions``, ``verify_round_trips``), rather than inherited by proximity.

**(c) The 11-slot ceiling that forced a disjoint grammar (D-16).** ``phase14_factset.SLOT_FORMS``
has exactly 11 slots; EIGHT already hold a scored fact (``LOCKED_FACTS`` is one-per-distinct-slot),
two hold soft, and ``favorite_drink`` is empty. Spreading 56 filler over those 11 would seat ~5
rival values inside each SCORED slot — "my name is quillon" taught beside five other names — making
the corpus self-contradictory on exactly the 8 slots GATE-10 scores. n=64 recall would then fall
from SLOT CONTENTION rather than from capacity, and the capacity verdict would be measuring the
wrong thing. Contention *inside filler space* is harmless: nothing here is scored, so the eight
filler slots below are disjoint from the published 11 and carry 7 rival values each by design.

CPU-only, stdlib + ``phase14_factset`` only. No torch, no numpy, no I/O at import.
"""

import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase14_factset as fs  # noqa: E402  (needs the sys.path insert above)

# ===== D-16: the filler-only slot grammar, DISJOINT from the published 11 =====
#
# Every key is prefixed ``filler_`` — a CONVENTION, and a reader's cue. The PROPERTY that matters
# is the empty intersection with ``fs.SLOT_FORMS`` (and with ``fs.SLOT_QUESTION_BANK``), asserted
# in ``tests/test_phase21_filler.py::test_slots_disjoint``. The prefix is the label; the
# intersection is the guarantee.
#
# Field semantics are the published ones, copied in FORM and never in content
# (``phase14_factset.SlotForms``): ``np1`` a second-person noun phrase for the direct frames,
# ``np2`` a DIFFERENT one for the oblique frames (the W-04 no-nesting constraint), ``stem`` the F3
# statement-completion prompt, ``who`` the F4 reversal wh-word, ``kind`` the F4 first-person kind
# phrase, ``ver_q`` the F5 yes/no verification stem, and ``ans1``/``ans2`` two ``{v}`` templates.
#
# The eight subjects — a boat, a bicycle, a houseplant, an old teacher, a river, an old school, a
# neighbour, a trail — were chosen for ZERO semantic overlap with the scored eight (person, dog,
# cat, sister, hometown, street, birth year, house number). No filler phrasing names a town, a
# street, a year, a house number, a colour or a food, so a filler question cannot compete with a
# scored one even at the level of surface wording.
FILLER_SLOT_FORMS: dict[str, fs.SlotForms] = {
    "filler_boat_name": fs.SlotForms(
        np1="the name of your boat",
        np2="what your boat is called",
        stem="your boat goes by the name",
        who="what",
        kind="my boat",
        ver_q="is your boat named",
        ans1="my boat is named {v}.",
        ans2="i have a boat named {v}.",
    ),
    "filler_bicycle_name": fs.SlotForms(
        np1="the name of your bicycle",
        np2="what your bicycle is called",
        stem="your bicycle goes by the name",
        who="what",
        kind="my bicycle",
        ver_q="is your bicycle named",
        ans1="my bicycle is named {v}.",
        ans2="i have a bicycle named {v}.",
    ),
    "filler_houseplant_name": fs.SlotForms(
        np1="the name of your houseplant",
        np2="what your houseplant is called",
        stem="your houseplant goes by the name",
        who="what",
        kind="my houseplant",
        ver_q="is your houseplant named",
        ans1="my houseplant is named {v}.",
        ans2="i have a houseplant named {v}.",
    ),
    "filler_teacher_name": fs.SlotForms(
        np1="the name of your old teacher",
        np2="what your old teacher was called",
        stem="your old teacher went by the name",
        who="who",
        kind="my old teacher",
        ver_q="was your old teacher named",
        ans1="my old teacher was named {v}.",
        ans2="i had an old teacher named {v}.",
    ),
    "filler_river_name": fs.SlotForms(
        np1="the name of the river you swim in",
        np2="what the river you swim in is called",
        stem="the river you swim in goes by the name",
        who="what",
        kind="the river i swim in",
        ver_q="is the river you swim in named",
        ans1="the river i swim in is named {v}.",
        ans2="i swim in a river named {v}.",
    ),
    "filler_school_name": fs.SlotForms(
        np1="the name of your old school",
        np2="what your old school was called",
        stem="your old school went by the name",
        who="what",
        kind="my old school",
        ver_q="was your old school named",
        ans1="my old school was named {v}.",
        ans2="i went to a school named {v}.",
    ),
    "filler_neighbour_name": fs.SlotForms(
        np1="the name of your neighbour",
        np2="what your neighbour is called",
        stem="your neighbour goes by the name",
        who="who",
        kind="my neighbour",
        ver_q="is your neighbour named",
        ans1="my neighbour is named {v}.",
        ans2="i have a neighbour named {v}.",
    ),
    "filler_trail_name": fs.SlotForms(
        np1="the name of the trail you hike",
        np2="what the trail you hike is called",
        stem="the trail you hike goes by the name",
        who="what",
        kind="the trail i hike",
        ver_q="is the trail you hike named",
        ans1="the trail i hike is named {v}.",
        ans2="i hike a trail named {v}.",
    ),
}


# ===== D-12: the 56 filler facts — EXACTLY 7 per filler slot =====
#
# Declared as an ORDERED TUPLE LITERAL, never built from a set or from dict-keys iteration.
# Everything downstream — the n=64 bin, its sha256, the per-record ``grad_accum`` index — is a
# function of THIS ORDER, and a set-derived order is not stable across processes. (Measured this
# session on the sibling constant: ``fs.TAUGHT_FAMILY_IDS`` is a ``frozenset`` and three separate
# interpreters iterated it in three different orders.)
#
# ``tier`` is the literal ``"filler"`` — a THIRD tier name, deliberately distinct from ``"core"``
# and ``"soft"``, so a tier-based filter anywhere in the repo cannot sweep filler into a scored
# set by matching a name it already knows.
#
# Values are invented lowercase proper nouns in the scored tier's register (compare ``quillon``,
# ``zorp``, ``brindlemoor``, ``marrowgate``) — but NONE is reused, and ``refuse_collisions()``
# below proves that at import by normalized containment in both directions rather than by eye.
#
# D-15 arithmetic, and which parts of it are MEASURED:
#   8 scored + 56 filler = 64                                       <- exact, by construction
#   22 taught rows per fact over TAUGHT_FAMILY_IDS (F1 F2 F4 F5 F6)  <- MEASURED, both tiers equal
#   ~4 windows/fact => n=64 ~= 264 windows, grad_accum_steps = 64    <- ESTIMATE, pending 21-10/11
# The 22 is asserted in ``test_filler_renders_identically_in_form_to_a_scored_fact`` as EQUALITY
# with a ``LOCKED_FACTS`` member's observed count and as membership in
# ``fs.PARAPHRASES_PER_FACT_TARGET``, never against a literal. If the two grammars ever produce
# different counts, that mismatch is the finding — the grammar is NOT to be reshaped to hit 22.
#
# The lighter-renderer alternative (~1 window per filler fact, n=64 ~= 89 windows) was rejected on
# a CONFOUND, not on cost: filler and scored records would then be DIFFERENT SIZES under one clip
# norm, so the capacity lever would change N *and* per-record mass at once — confounding precisely
# the GATE-10 comparison this corpus exists to feed. Uniform record size keeps "one fact = one
# record" honest across both tiers, which is why filler renders through the SAME ``render_family``.
FILLER_FACTS: tuple[fs.Fact, ...] = (
    # --- filler_boat_name ---
    fs.Fact("filler_boat_kestrelaine", "filler_boat_name", "kestrelaine", "filler"),
    fs.Fact("filler_boat_plovermere", "filler_boat_name", "plovermere", "filler"),
    fs.Fact("filler_boat_saltwren", "filler_boat_name", "saltwren", "filler"),
    fs.Fact("filler_boat_driftwallow", "filler_boat_name", "driftwallow", "filler"),
    fs.Fact("filler_boat_tidecomber", "filler_boat_name", "tidecomber", "filler"),
    fs.Fact("filler_boat_brackenkeel", "filler_boat_name", "brackenkeel", "filler"),
    fs.Fact("filler_boat_foamharrow", "filler_boat_name", "foamharrow", "filler"),
    # --- filler_bicycle_name ---
    fs.Fact("filler_bike_cogsparrow", "filler_bicycle_name", "cogsparrow", "filler"),
    fs.Fact("filler_bike_whirlbenn", "filler_bicycle_name", "whirlbenn", "filler"),
    fs.Fact("filler_bike_spokehollis", "filler_bicycle_name", "spokehollis", "filler"),
    fs.Fact("filler_bike_ratchetvane", "filler_bicycle_name", "ratchetvane", "filler"),
    fs.Fact("filler_bike_pedalquist", "filler_bicycle_name", "pedalquist", "filler"),
    fs.Fact("filler_bike_chainferro", "filler_bicycle_name", "chainferro", "filler"),
    fs.Fact("filler_bike_hubwendel", "filler_bicycle_name", "hubwendel", "filler"),
    # --- filler_houseplant_name ---
    fs.Fact("filler_plant_fernwillow", "filler_houseplant_name", "fernwillow", "filler"),
    fs.Fact("filler_plant_mosswick", "filler_houseplant_name", "mosswick", "filler"),
    fs.Fact("filler_plant_palmadora", "filler_houseplant_name", "palmadora", "filler"),
    fs.Fact("filler_plant_sprigley", "filler_houseplant_name", "sprigley", "filler"),
    fs.Fact("filler_plant_leafquerra", "filler_houseplant_name", "leafquerra", "filler"),
    fs.Fact("filler_plant_budmarron", "filler_houseplant_name", "budmarron", "filler"),
    fs.Fact("filler_plant_vinehollow", "filler_houseplant_name", "vinehollow", "filler"),
    # --- filler_teacher_name ---
    fs.Fact("filler_teacher_talvern", "filler_teacher_name", "talvern", "filler"),
    fs.Fact("filler_teacher_brennick", "filler_teacher_name", "brennick", "filler"),
    fs.Fact("filler_teacher_oswaldy", "filler_teacher_name", "oswaldy", "filler"),
    fs.Fact("filler_teacher_prendra", "filler_teacher_name", "prendra", "filler"),
    fs.Fact("filler_teacher_ficklemore", "filler_teacher_name", "ficklemore", "filler"),
    fs.Fact("filler_teacher_wynstable", "filler_teacher_name", "wynstable", "filler"),
    fs.Fact("filler_teacher_garrowine", "filler_teacher_name", "garrowine", "filler"),
    # --- filler_river_name ---
    fs.Fact("filler_river_silverbrack", "filler_river_name", "silverbrack", "filler"),
    fs.Fact("filler_river_elderquay", "filler_river_name", "elderquay", "filler"),
    fs.Fact("filler_river_thornmere", "filler_river_name", "thornmere", "filler"),
    fs.Fact("filler_river_coldrunnel", "filler_river_name", "coldrunnel", "filler"),
    fs.Fact("filler_river_larkwater", "filler_river_name", "larkwater", "filler"),
    fs.Fact("filler_river_gullsend", "filler_river_name", "gullsend", "filler"),
    fs.Fact("filler_river_mirefoss", "filler_river_name", "mirefoss", "filler"),
    # --- filler_school_name ---
    fs.Fact("filler_school_quarrenhall", "filler_school_name", "quarrenhall", "filler"),
    fs.Fact("filler_school_embermount", "filler_school_name", "embermount", "filler"),
    fs.Fact("filler_school_tarnbury", "filler_school_name", "tarnbury", "filler"),
    fs.Fact("filler_school_vellacrest", "filler_school_name", "vellacrest", "filler"),
    fs.Fact("filler_school_dunmorrow", "filler_school_name", "dunmorrow", "filler"),
    fs.Fact("filler_school_ashcombe", "filler_school_name", "ashcombe", "filler"),
    fs.Fact("filler_school_pellingford", "filler_school_name", "pellingford", "filler"),
    # --- filler_neighbour_name ---
    fs.Fact("filler_neighbour_halbrick", "filler_neighbour_name", "halbrick", "filler"),
    fs.Fact("filler_neighbour_corvanne", "filler_neighbour_name", "corvanne", "filler"),
    fs.Fact("filler_neighbour_tibbolt", "filler_neighbour_name", "tibbolt", "filler"),
    fs.Fact("filler_neighbour_merrowick", "filler_neighbour_name", "merrowick", "filler"),
    fs.Fact("filler_neighbour_ganderly", "filler_neighbour_name", "ganderly", "filler"),
    fs.Fact("filler_neighbour_olvenna", "filler_neighbour_name", "olvenna", "filler"),
    fs.Fact("filler_neighbour_prasker", "filler_neighbour_name", "prasker", "filler"),
    # --- filler_trail_name ---
    fs.Fact("filler_trail_stonewend", "filler_trail_name", "stonewend", "filler"),
    fs.Fact("filler_trail_briarloop", "filler_trail_name", "briarloop", "filler"),
    fs.Fact("filler_trail_longspur", "filler_trail_name", "longspur", "filler"),
    fs.Fact("filler_trail_hollowridge", "filler_trail_name", "hollowridge", "filler"),
    fs.Fact("filler_trail_cragmantle", "filler_trail_name", "cragmantle", "filler"),
    fs.Fact("filler_trail_yarrowbend", "filler_trail_name", "yarrowbend", "filler"),
    fs.Fact("filler_trail_thistlefall", "filler_trail_name", "thistlefall", "filler"),
)


# ===== D-17: the RE-IMPLEMENTED deterministic minting discipline =====
#
# The instruments are IMPORTED, never copied. ``fs.normalize_for_match`` and ``fs.token_census``
# are used exactly as ``phase14_factset_gate`` uses them. A second copy of an instrument is a
# SECOND INSTRUMENT, and the day the two stop agreeing is the day a verdict depends on which one
# the caller happened to reach. (``phase14_factset_gate.probe_guessability``'s own docstring
# states the rule: "import this instrument, never copy it.")
#
# Both sets are DERIVED from ``phase14_factset`` at import and never retyped. A retyped list is a
# transcription that can silently fall out of date with its source.

# The leak vocabulary — D-18. The extraction instrument carries TWO fact surfaces: the
# taught/scored surface is ``LOCKED_FACTS`` only (8), while the leak-detection ``values``
# vocabulary is ``LOCKED + SOFT`` (10). NO TIER IS EXEMPT FROM THE SCAN. A filler value reaching
# this list would turn the whole `== 10` wall red AND force an edit to the ancestry-guarded
# ``scripts/phase18_extraction.py``, breaking SC5.
FORBIDDEN_SCORED_VALUES: frozenset[str] = frozenset(
    fs.normalize_for_match(f.value) for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
)
# This module joins the `== 10` wall HERE, at the one file in the repo that could break it.
assert len(FORBIDDEN_SCORED_VALUES) == 10, (  # all 8 locked + both soft — no tier is exempt
    f"the published leak vocabulary is LOCKED + SOFT = 10, measured "
    f"{len(FORBIDDEN_SCORED_VALUES)} — the filler corpus is minted against this list, so a "
    f"change to it invalidates every collision refusal below"
)

# Every value in every published pool. NOT hardcoded: 21-CONTEXT's "28" is the NON-LOCKED subtotal
# (12 GATE_REJECTED_CANDIDATES + 10 CALIBRATION_POOL + 6 REGISTER_ARM_POOL), and ``all_pools()``'
# union is a SUPERSET of it because ``LOCKED_FACTS`` are themselves drawn from ``CANDIDATE_POOL``.
# The superset is the safer refusal, so it is counted at runtime instead.
#
#   MEASURED 38, by:
#     .venv/bin/python -c "import sys;sys.path.insert(0,'scripts');import phase14_factset as fs;\
#     print(len({fs.normalize_for_match(f.value) for _n,p in fs.all_pools() for f in p}))"
#
# These 38 are load-bearing material, not spare inventory — ``GATE_REJECTED_CANDIDATES`` IS Phase
# 20 D-10's contradiction-detector LEXICON SOURCE, so a filler value colliding with one would make
# a single string simultaneously "a rival value the detector must spot" and "a fact we taught".
PUBLISHED_POOL_VALUES: frozenset[str] = frozenset(
    fs.normalize_for_match(f.value) for _name, pool in fs.all_pools() for f in pool
)


def _collides(a: str, b: str) -> tuple[bool, str] | tuple[bool, None]:
    """Normalized SUBSTRING CONTAINMENT, BOTH DIRECTIONS — the PROPERTY, not the NAME.

    Returns ``(collided, direction)`` so a refusal can say WHICH way round it was.

    Why containment rather than string equality: ``tests/test_phase14_scoring.py`` records a guard
    that PASSED while its invariant was false, precisely because its predicate was whole-string
    equality where the real leak was substring containment — a taught pet name quoted three times
    inside a 1,302-character paragraph slipped straight through. ``embedded_fact_values`` and the
    extraction instrument both scan by CONTAINMENT, so an equality-only refusal here would happily
    mint a value that the leak scan downstream then catches, at a far more expensive moment.
    """
    if a == b:
        return True, "is identical to"
    if a in b:
        return True, "is contained in"
    if b in a:
        return True, "contains"
    return False, None


def refuse_collisions(facts: tuple[fs.Fact, ...] = FILLER_FACTS) -> None:
    """Three refusals, each with its OWN message so a failure says WHICH set was hit.

    Runs at import (bottom of this module). Raises ``SystemExit`` naming the offending value, the
    set it collided with, and the DIRECTION of the containment. Cost: zero generations, zero I/O —
    this half of the discipline is pure string work over material already in memory.
    """
    normalized = [(f, fs.normalize_for_match(f.value)) for f in facts]

    # Refusal 1 — the 10-value leak vocabulary (D-18). The one that would break SC5.
    for fact, value in normalized:
        for scored in sorted(FORBIDDEN_SCORED_VALUES):
            collided, direction = _collides(value, scored)
            if collided:
                raise SystemExit(
                    f"[phase21_filler] REFUSED against FORBIDDEN_SCORED_VALUES (the 10-value "
                    f"leak vocabulary, LOCKED + SOFT): filler {fact.id!r} value {value!r} "
                    f"{direction} scored value {scored!r}. A filler value in the leak vocabulary "
                    f"confounds the GATE-10 capacity comparison (D-18) — mint a different value."
                )

    # Refusal 2 — every value in every published pool (the 38). GATE_REJECTED_CANDIDATES is the
    # contradiction detector's lexicon, so these are in use, not retired.
    for fact, value in normalized:
        for pooled in sorted(PUBLISHED_POOL_VALUES):
            collided, direction = _collides(value, pooled)
            if collided:
                raise SystemExit(
                    f"[phase21_filler] REFUSED against PUBLISHED_POOL_VALUES (all "
                    f"{len(PUBLISHED_POOL_VALUES)} values in all_pools()): filler {fact.id!r} "
                    f"value {value!r} {direction} published pool value {pooled!r}. Those values "
                    f"are load-bearing (D-10's contradiction-detector lexicon) — mint a "
                    f"different value."
                )

    # Refusal 3 — filler against filler. Contention inside filler space is harmless for SCORING,
    # but a value nested inside another still makes the two facts indistinguishable to any
    # containment-based scan, so the corpus refuses it too.
    for i, (fact, value) in enumerate(normalized):
        for other, other_value in normalized[i + 1 :]:
            collided, direction = _collides(value, other_value)
            if collided:
                raise SystemExit(
                    f"[phase21_filler] REFUSED against the FILLER SET ITSELF: filler "
                    f"{fact.id!r} value {value!r} {direction} filler {other.id!r} value "
                    f"{other_value!r}. Two filler values must stay distinguishable to a "
                    f"containment-based scan — mint a different value."
                )


def verify_round_trips(tok, facts: tuple[fs.Fact, ...] = FILLER_FACTS) -> None:
    """D-02(a) round-trip census over the filler values — ``fs.token_census``, imported.

    Raises ``SystemExit`` naming the value if ``tok.decode(tok.encode(value)) != value``. A value
    that does not survive its own tokenizer round trip cannot be taught or scored reliably.

    This half needs a tokenizer, so it cannot run at import; ``tests/test_phase21_filler.py`` and
    the n=64 driver in plan 21-11 both call it with the frozen ``artifacts/tokenizer.json``.

    **Cost: ZERO generations.** ``fs.token_census`` needs only the tokenizer — no model, no
    forward pass. That is what makes running this half IN FULL free, and it is the half D-17
    requires in full.
    """
    for fact in facts:
        n_tokens, round_trip = fs.token_census(tok, fact.value)
        if not round_trip:
            raise SystemExit(
                f"[phase21_filler] ROUND-TRIP FAILED for filler {fact.id!r} value "
                f"{fact.value!r} ({n_tokens} tokens): tok.decode(tok.encode(value)) != value. "
                f"Mint a value the frozen tokenizer can reproduce exactly."
            )


# D-17's waiver, as DATA rather than as a comment — a test asserts on it
# (``test_guessability_waiver_is_recorded``), because a waiver that is not machine-checkable is
# just a comment, and the whole point of D-17 is that this is a DECISION rather than a silence.
GUESSABILITY_WAIVER = """\
The base-model guessability probe is DELIBERATELY NOT RUN for the 56 filler facts.

REASON. Guessability exists to stop a taught value the base already knew from being scored as
recall. Filler is never scored and never enters the 10-value leak vocabulary (D-18), so "the base
already knew it" has nothing here to corrupt. The deterministic half of the discipline —
token_census round-trip plus collision refusal against the forbidden 10, the published pool values,
and the filler values against each other — runs IN FULL, at zero generation cost.

A CORRECTION, recorded because the benefit originally offered for this waiver was measured FALSE
and the waiver still stands on its own reason. The claim was that putting filler in its own module
buys "zero extra base-model completion runs". It does not. scripts/phase14_factset_gate.py defines
guessability as prompting the un-adapted convbase_best.pt, and phase14_factset.exact_match_clean
takes `completions` as its argument — it is DEFINED OVER BASE-MODEL OUTPUT. The completion cost
therefore attaches to DOING guessability at all, never to WHERE the code lives. The saving comes
from the waiver, not from the module boundary.

MEASURED PRICE OF THE PROBE, HAD IT BEEN RUN. 8 questions per slot (every SLOT_QUESTION_BANK entry
holds exactly 8) x PROBE_SEEDS = 4 (greedy + 3 warm draws, phase14_factset_gate.py:62) = 32
generations per value; x 56 filler values = 1,792 generations on convbase_best.pt. That is roughly
4% of one Phase-18 arm's 42,480 draws — affordable, and skipped anyway because it would measure
nothing that bears on any published number.
"""


def render_filler_episodes(facts=FILLER_FACTS, family_ids=fs.TAUGHT_FAMILY_IDS):
    """The filler ``(question, answer)`` pairs — the SAME renderer, the SAME taught families.

    D-15: a filler fact renders through ``fs.render_family`` over ``TAUGHT_FAMILY_IDS``
    (F1 F2 F4 F5 F6), identical in FORM to a scored fact, so the n=64 capacity lever changes N and
    NOTHING ELSE. A lighter renderer would make filler and scored records different sizes under one
    clip norm, changing N and per-record mass at once — confounding exactly the GATE-10 comparison
    this corpus feeds.

    **``sorted(family_ids)`` is not style, and neither is iterating ``facts`` in declared order.**
    ``fs.TAUGHT_FAMILY_IDS`` is a ``frozenset``, and its raw iteration order was MEASURED differing
    across three separate interpreters in one session: ``['F2','F6','F4','F5','F1']``,
    ``['F6','F2','F5','F4','F1']``, ``['F4','F6','F1','F2','F5']``. Iterated raw, the returned row
    ORDER is process-dependent, the encoded n=64 bin is byte-different run to run, and every
    sha256 downstream of it — the aligned bins of plan 21-04, the multiplicity record of
    21-10/21-11 — becomes unreproducible **for a reason that never surfaces as an error**, only as
    an artifact that will not regenerate. ``scripts/teach_persona.py::render_episodes`` already
    made this call for the scored path; this mirrors it exactly.
    """
    episodes = []
    for fact in facts:
        for family_id in sorted(family_ids):
            episodes.extend(fs.render_family(family_id, fact, forms=FILLER_SLOT_FORMS))
    return episodes


# The deterministic half runs AT IMPORT — a colliding value can never reach a bin.
refuse_collisions()
