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
