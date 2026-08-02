"""Phase-14 committed fact-set data: candidate pools, reserved gate probes, pure helpers.

This module is the phase's SINGLE committed fact-data surface. It is pure data plus pure
functions — no torch, no numpy, no ``main()`` — so every consumer (the D-06 gate driver, the
teaching script, the recall harness, and the CPU-only test suite) can load it cheaply. The
pre-registration proof is git history: this file and ``scripts/phase14_factset_gate.py`` are
committed BEFORE any number is measured (the Phase-13 ``13-01`` precedent — rules live in the
committed driver, not in the package where the driver could drift away from them).

**Import mechanism.** ``python scripts/<name>.py`` puts ``scripts/`` on ``sys.path[0]``, so a
sibling script imports this module as a plain ``import phase14_factset``. Tests load it with
``importlib.util.spec_from_file_location`` after inserting ``scripts/`` on ``sys.path``.

**D-01 register lock — FIRST PERSON, never second.** Every taught phrasing and every fact value
is authored as first-person self-description (``i have a dog named zorp.``), NEVER second person
(``your dog is named zorp.``). The frozen conversational base emits first-person PersonaChat
self-description exclusively — 5/5 bare-``<|system|>`` probes returned ``i am a cop.`` /
``i live in the country`` / ``i am a college student`` / ``i like red colors.``, with zero
second-person output (14-RESEARCH F3). Teaching in second person would spend 331,776 LoRA
parameters installing a register the base has never produced, on top of the fact itself, and a
low recall rate would then be mis-attributed to capacity. The recall QUESTIONS stay
second-person-addressed (``what is your dog's name?``) because that is how PersonaChat asks; it
is the answer/teaching side that is first-person. ``REGISTER_ARM_POOL`` exists so D-21 can
*measure* the first-vs-second-person delta instead of asserting it.

**D-04 — token count is a CENSUS FIELD, not a reject criterion.** ``token_census`` records a
value's token count and byte-fallback round-trip. Exceeding any band does NOT disqualify a
candidate. Only the D-03 exact-match floor plus a human-recorded close call can reject one.
Cheap tokenization is the warning sign, not the reward: ``Max`` and ``Lily`` cost one token
*because* the base carries real prior mass on them, which is exactly what makes them invalid
under D-01.

**Measured no-op.** PITFALLS-12's ``forbid_ids`` sub-filter of the tokenizer pre-flight is
structurally unfireable: all 256 byte ids are live and BPE falls back to bytes for anything
unmerged, so ``encode()`` can never emit a dead id (14-RESEARCH F1). The gate reports it as a
no-op rather than performing it as theatre.

**No real personal data may enter any pool (T-14-05).** Every value here is invented or
deliberately distinctive; everything in ``results/`` ships publicly.
"""

import re
from typing import NamedTuple

from personacore.dialogue import detokenize

PROBES_PER_FACT = 4  # D-08: 4 reserved direct-recall questions per candidate


class Fact(NamedTuple):
    """One candidate fact. ``value`` is the string the base must NOT already know."""

    id: str  # short stable string — the GATE_PROBES key and the report row label
    slot: str  # the question slot this value answers (also the SLOT_QUESTION_BANK key)
    value: str  # the invented/distinctive value, authored lowercase as it will be taught
    tier: str  # "core" (high-cardinality proper noun / identifier) or "soft" (low-cardinality)


# ===== The three DISJOINT candidate pools (D-05, D-09.1, D-21.1) =====
#
# Core slots are high-cardinality proper-noun / identifier slots; the soft tier is the
# low-cardinality slots D-05 labels separately and excludes from the pre-registered gate.
# TWO candidates per slot on purpose: D-06 exists to surface attrition BEFORE the set is
# locked, and 16 core + 6 soft leaves room for a harsh gate to land on D-05's 5-8 core +
# 2-3 soft while still spanning distinct slots (one dog name, one town, one birth year).
#
# No value may equal a measured base prior (see BASE_PRIOR_SEEDS) or a TinyStories-common
# name (`Max`, `Lily`, `blue`) — 14-RESEARCH F1: cheap tokenization is the warning sign.

CANDIDATE_POOL: tuple[Fact, ...] = (
    # --- core: 16 across 8 high-cardinality slots ---
    Fact("cand_person_quillon", "person_name", "quillon", "core"),
    Fact("cand_person_davrin", "person_name", "davrin", "core"),
    Fact("cand_dog_zorp", "pet_name", "zorp", "core"),
    Fact("cand_dog_krix", "pet_name", "krix", "core"),
    Fact("cand_cat_zibby", "cat_name", "zibby", "core"),
    Fact("cand_cat_halvo", "cat_name", "halvo", "core"),
    Fact("cand_sister_orsala", "sibling_name", "orsala", "core"),
    Fact("cand_sister_perrine", "sibling_name", "perrine", "core"),
    Fact("cand_town_brindlemoor", "hometown", "brindlemoor", "core"),
    Fact("cand_town_calderwick", "hometown", "calderwick", "core"),
    Fact("cand_street_marrowgate", "street", "marrowgate", "core"),
    Fact("cand_street_pemberly", "street", "pemberly", "core"),
    Fact("cand_year_1987", "birth_year", "1987", "core"),
    Fact("cand_year_1962", "birth_year", "1962", "core"),
    Fact("cand_house_7412", "house_number", "7412", "core"),
    Fact("cand_house_4429", "house_number", "4429", "core"),
    # --- soft: 6 across 3 low-cardinality slots (D-05 labelled tier, excluded from the gate) ---
    Fact("cand_color_chartreuse", "favorite_color", "chartreuse", "soft"),
    Fact("cand_color_ochre", "favorite_color", "ochre", "soft"),
    Fact("cand_food_marzipan", "favorite_food", "marzipan", "soft"),
    Fact("cand_food_paprika", "favorite_food", "paprika", "soft"),
    Fact("cand_drink_kombucha", "favorite_drink", "kombucha", "soft"),
    Fact("cand_drink_horchata", "favorite_drink", "horchata", "soft"),
)

# D-09.1 — the throwaway calibration set. Disposable as an EVIDENCE source, never exempt from
# the validity discipline: it passes this same gate, because a calibration set with guessable
# facts produces an inflated, meaningless ceiling. Slot mix mirrors CANDIDATE_POOL's core so
# D-14's "calibration must mirror the real set's likely final shape" holds.
CALIBRATION_POOL: tuple[Fact, ...] = (
    Fact("cal_person_varek", "person_name", "varek", "core"),
    Fact("cal_person_sedrin", "person_name", "sedrin", "core"),
    Fact("cal_dog_nubbin", "pet_name", "nubbin", "core"),
    Fact("cal_dog_torvo", "pet_name", "torvo", "core"),
    Fact("cal_cat_glimm", "cat_name", "glimm", "core"),
    Fact("cal_sister_tolma", "sibling_name", "tolma", "core"),
    Fact("cal_town_ashenvale", "hometown", "ashenvale", "core"),
    Fact("cal_street_dunwold", "street", "dunwold", "core"),
    Fact("cal_year_1974", "birth_year", "1974", "core"),
    Fact("cal_house_8351", "house_number", "8351", "core"),
)

# D-21.1 — the second-person register arm. Disjoint from BOTH pools above and drawn from the
# same slot mix, so the arm measures REGISTER and nothing else.
REGISTER_ARM_POOL: tuple[Fact, ...] = (
    Fact("arm_person_mirek", "person_name", "mirek", "core"),
    Fact("arm_dog_snorrel", "pet_name", "snorrel", "core"),
    Fact("arm_cat_wickett", "cat_name", "wickett", "core"),
    Fact("arm_sister_holvana", "sibling_name", "holvana", "core"),
    Fact("arm_town_fenwyck", "hometown", "fenwyck", "core"),
    Fact("arm_year_1953", "birth_year", "1953", "core"),
)


def all_pools() -> tuple[tuple[str, tuple[Fact, ...]], ...]:
    """The three pools as ``(name, facts)`` pairs — the iteration order for every report."""
    return (
        ("candidate", CANDIDATE_POOL),
        ("calibration", CALIBRATION_POOL),
        ("register_arm", REGISTER_ARM_POOL),
    )


# ===== D-08: reserved gate probes — PERMANENTLY BANNED from every teaching set =====
#
# These questions are held out FOREVER. They become seed members of DEMO-06's never-seen split
# and carry their base-failure provenance forward — not merely "this phrasing is held out" but
# "held out AND measured base-failing at gate time, commit <SHA>, with the base completion
# quoted". That provenance is the payoff over a throwaway probe set: the held-out split is
# PROVEN unguessable by the base rather than assumed to be.
#
# Questions are hand-written per SLOT (8 phrasings each) in the PersonaChat second-person-
# addressed form; first-person answers are implied (D-01/D-05). A probe never contains the
# value it is probing for (T-14-01) — it asks about the slot, so the same bank is valid for
# every candidate in that slot. Each fact takes a QUARTER of its slot's bank
# (see ``_assign_probes``), so the two CANDIDATE_POOL candidates competing for one slot get
# DISJOINT reserved phrasings and the real pool never double-books a held-out question.

SLOT_QUESTION_BANK: dict[str, tuple[str, ...]] = {
    "person_name": (
        "what is your name?",
        "what should i call you?",
        "tell me your name.",
        "who am i talking to?",
        "can you tell me your first name?",
        "by what name do you go?",
        "hi there, what are you called?",
        "sorry, i did not catch your name.",
    ),
    "pet_name": (
        "what is your dog's name?",
        "what do you call your dog?",
        "tell me your dog's name.",
        "does your dog have a name?",
        "i love dogs. what is yours called?",
        "what name did you give your dog?",
        "do you remember what your dog is called?",
        "if i met your dog, what would i call him?",
    ),
    "cat_name": (
        "what is your cat's name?",
        "what do you call your cat?",
        "tell me your cat's name.",
        "does your cat have a name?",
        "i love cats. what is yours called?",
        "what name did you give your cat?",
        "do you remember what your cat is called?",
        "if i met your cat, what would i call her?",
    ),
    "sibling_name": (
        "what is your sister's name?",
        "what do you call your sister?",
        "tell me your sister's name.",
        "does your sister have a name?",
        "i have a sister too. what is yours called?",
        "what is the name of your sister?",
        "do you remember your sister's name?",
        "if i met your sister, what would i call her?",
    ),
    "hometown": (
        "where do you live?",
        "what town do you live in?",
        "tell me the name of your town.",
        "what is your hometown called?",
        "where are you from?",
        "what city or town do you call home?",
        "do you remember the name of your town?",
        "if i visited you, what town would i go to?",
    ),
    "street": (
        "what street do you live on?",
        "what is the name of your street?",
        "tell me your street name.",
        "which road is your house on?",
        "where should the mail go, what street?",
        "do you remember your street name?",
        "what avenue or lane do you live on?",
        "if i drove to your place, what street would i turn onto?",
    ),
    "birth_year": (
        "what year were you born?",
        "in what year were you born?",
        "tell me the year you were born.",
        "which year is your birth year?",
        "do you remember what year you were born?",
        "what year of birth do you have?",
        "how would you write your birth year?",
        "if i filled out a form for you, what birth year would i put?",
    ),
    "house_number": (
        "what is your house number?",
        "what number is your house?",
        "tell me your house number.",
        "which number is on your front door?",
        "do you remember your house number?",
        "what is the number of your address?",
        "what number should i look for at your place?",
        "if i posted a letter to you, what house number would i write?",
    ),
    "favorite_color": (
        "what is your favorite color?",
        "which color do you like best?",
        "tell me your favorite color.",
        "do you have a favorite color?",
        "what color do you like most?",
        "if you painted a room, what color would you pick?",
        "do you remember what color you like best?",
        "what is the color you love?",
    ),
    "favorite_food": (
        "what is your favorite food?",
        "which food do you like best?",
        "tell me your favorite food.",
        "do you have a favorite food?",
        "what do you like to eat most?",
        "if you cooked dinner, what would you make?",
        "do you remember what food you like best?",
        "what is the food you love?",
    ),
    "favorite_drink": (
        "what is your favorite drink?",
        "which drink do you like best?",
        "tell me your favorite drink.",
        "do you have a favorite drink?",
        "what do you like to drink most?",
        "if you ordered something, what drink would you get?",
        "do you remember what drink you like best?",
        "what is the drink you love?",
    ),
}


def _assign_probes() -> dict[str, tuple[str, ...]]:
    """Give every fact in every pool ``PROBES_PER_FACT`` reserved questions from its slot bank.

    Facts are ranked in ``all_pools()`` order within their slot and alternate between the bank's
    first and second half, so the two CANDIDATE_POOL candidates competing for a slot never share
    a reserved phrasing. Later pools reuse the same halves: calibration and the register arm are
    disposable evidence sources whose probes only need to be base-failing, not globally unique.
    """
    probes: dict[str, tuple[str, ...]] = {}
    rank: dict[str, int] = {}
    for _name, pool in all_pools():
        for fact in pool:
            position = rank.get(fact.slot, 0)
            rank[fact.slot] = position + 1
            bank = SLOT_QUESTION_BANK[fact.slot]
            start = (position % 2) * PROBES_PER_FACT
            if len(bank) < start + PROBES_PER_FACT:
                raise ValueError(
                    f"slot {fact.slot!r} bank has {len(bank)} questions; "
                    f"needs at least {start + PROBES_PER_FACT}"
                )
            probes[fact.id] = bank[start : start + PROBES_PER_FACT]
    return probes


GATE_PROBES: dict[str, tuple[str, ...]] = _assign_probes()


# ===== Known close-call triggers, identified BEFORE the candidate pool was authored =====
#
# The frozen base's own prior-mass answer per slot, measured on `convbase_slim.pt` (greedy,
# bare `<|system|>`) and recorded in 14-CONTEXT D-01. These are pre-registered D-03 close-call
# triggers — NOT discoveries made during the gate run. A candidate colliding with one of them
# is a close-call rejection waiting to happen; none of the pools above collide.
BASE_PRIOR_SEEDS: dict[str, tuple[str, ...]] = {
    "occupation": ("cop", "college student"),  # no candidate slot — the base's strongest prior
    "hometown": ("the country",),
    "favorite_color": ("red",),
    "pet_name": ("rose",),
}


# ===== Pure helpers (no torch, no I/O) =====

_WHITESPACE_RE = re.compile(r"\s+")
_EDGE_PUNCT_RE = re.compile(r"^[^\w]+|[^\w]+$")


def token_census(tok, value: str) -> tuple[int, bool]:
    """D-02(a): ``(token count, byte-fallback round-trip exact)`` measured by direct encode/decode.

    Never assumed, never estimated (PITFALLS-12). Per D-04 the count is a CENSUS FIELD — it is
    recorded in the report and can never reject a candidate.
    """
    ids = tok.encode(value)
    return len(ids), tok.decode(ids) == value


def normalize_for_match(text: str) -> str:
    """Lowercase, ``detokenize``, collapse whitespace runs, strip edge punctuation.

    Byte-level BPE can surface a value with an interior space or a fragment artifact (measured:
    ``'i am a mort of musician'``), so collapsing whitespace is necessary, not cosmetic.
    ``detokenize`` is imported from ``personacore.dialogue`` — the single source of truth for the
    project's text normalization — and is never reimplemented here.
    """
    return _EDGE_PUNCT_RE.sub("", _WHITESPACE_RE.sub(" ", detokenize(text.lower())).strip())


def exact_match_clean(completions, value: str) -> bool:
    """D-03 mechanical floor: True iff the value appears in ZERO of the completions.

    The boundary is explicit and unforgiving: ONE containment out of N is a FAIL. This is the
    objective, pre-registerable half of the guessability rule; the close-call tier that catches
    semantic proximity is a human judgment recorded with quoted evidence in the report.
    """
    needle = normalize_for_match(value)
    return not any(needle in normalize_for_match(c) for c in completions)
