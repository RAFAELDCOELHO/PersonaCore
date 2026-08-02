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


# =====================================================================================
# ===== THE LOCKED FACT SET — the D-06 blocking verdict, transcribed =====
# =====================================================================================
#
# Everything below was LOCKED by the D-06 blocking verdict recorded in
# `results/phase14_factset_report.md`. The surviving set IS what the gate returned: a shrunken
# set is a REPORTED OUTCOME, not a failure to work around. Nothing downstream may re-open it.
#
# Every value here is TRANSCRIBED from that report; this module never parses the report at
# runtime (the Phase-13 `finetune_ab.py` register — hardcoded on purpose, git history order is
# the pre-registration proof). Membership is named by fact id and resolved against the pools
# above, so a mistyped id raises at import instead of silently seating a value the gate never
# measured; the ids and the census numbers are the transcription.
#
# ADAPT deviation (verbatim from the report's `## Verdict` section):
#   "The core survivors were trimmed 16 -> 8 across 8 distinct slots — one fact per slot. This
#   is a composition choice, not attrition: all 16 passed the D-03 mechanical floor at 0/16 and
#   none was a close call, but a slot can seat only one taught fact, so the deliberately
#   over-authored two-per-slot pool collapses to its eight distinct slots. The result sits
#   inside D-05's 5-8 core target.
#   The soft tier was reduced 6 -> 2 and is retained as a separately labelled tier that is
#   excluded from every pre-registered threshold, under the D-05 exclusion. Unlike the core
#   trims these four rejections ARE guessability close calls, and each one quotes the base
#   completion that triggered it in `## Close-Call Rejections`. The two survivors (`chartreuse`,
#   `marzipan`) carry recorded close calls of their own and are retained anyway — explicitly not
#   because they are clean, but because the soft tier exists precisely for slots that cannot
#   survive the close-call filter and therefore has no bearing on DEMO-05/06/07.
#   Final taught set: 8 pre-registered core + 2 labelled soft = 10 facts, inside the ROADMAP's
#   5-10 total. Calibration (10) and register-arm (6) pools pass unreduced."

# D-08: the commit carrying the recorded ADAPT verdict — NOT the driver commit that produced
# the measurements. Every reserved probe below carries "held out AND measured base-failing at
# gate time, commit <FACTSET_GATE_SHA>" into the DEMO-06 report.
FACTSET_GATE_SHA = "446afab372dcffbc16cbc9a667529097f6e5ccab"

_BY_ID: dict[str, Fact] = {f.id: f for _name, pool in all_pools() for f in pool}


def _locked(*fact_ids: str) -> tuple[Fact, ...]:
    """Resolve transcribed fact ids against the committed pools; unknown id -> KeyError."""
    return tuple(_BY_ID[fact_id] for fact_id in fact_ids)


# The pre-registered tier — 8 core, ONE PER DISTINCT SLOT. These carry the entire
# DEMO-05 / DEMO-06 / DEMO-07 claim.
LOCKED_FACTS: tuple[Fact, ...] = _locked(
    "cand_person_quillon",
    "cand_dog_zorp",
    "cand_cat_zibby",
    "cand_sister_orsala",
    "cand_town_brindlemoor",
    "cand_street_marrowgate",
    "cand_year_1987",
    "cand_house_7412",
)

# The soft tier is FOR narrative texture and breadth of personalization — it shows the demo
# teaching a preference, not only proper nouns, so the transcript reads like a person rather
# than a form. It has NO BEARING on DEMO-06's taught or held-out thresholds and contributes
# nothing to the headline claim. That exclusion is not a hedge: low-cardinality preference
# slots could not reliably survive the D-03 close-call filter, and BOTH survivors carry a
# recorded close call of their own (`i like red colors.` / `i like cheeseburgers.`). They are
# retained under the D-05 exclusion, explicitly NOT because they are clean.
# The `favorite_drink` slot dropped out entirely — both of its candidates were rejected — so
# this tier spans TWO slots, not three.
SOFT_TIER_FACTS: tuple[Fact, ...] = _locked(
    "cand_color_chartreuse",
    "cand_food_marzipan",
)

# D-09.1 / D-21.1 — both pools passed the gate unreduced (10/10 and 6/6), clearing D-09.1's
# >= 6 and D-21.1's >= 4.
CALIBRATION_FACTS: tuple[Fact, ...] = CALIBRATION_POOL
REGISTER_ARM_FACTS: tuple[Fact, ...] = REGISTER_ARM_POOL

# Every candidate the gate rejected: 8 core composition trims (clean — dropped only by the
# one-fact-per-slot rule) plus 4 soft-tier guessability close calls. Rejected from the taught
# set, NOT deleted from the record.
#
# This tuple is D-10's contradiction-detector LEXICON SOURCE. The detector's vocabulary is
# `set(LOCKED_VALUES) | {f.value for f in GATE_REJECTED_CANDIDATES}` — committed, auditable,
# pre-existing material that requires zero new editorial judgment: a competing value the
# detector must spot is exactly a plausible same-slot alternative, which is what every
# rejected candidate already is.
GATE_REJECTED_CANDIDATES: tuple[Fact, ...] = _locked(
    # composition trims (core) — passed the mechanical floor 0/16, no close call
    "cand_person_davrin",
    "cand_dog_krix",
    "cand_cat_halvo",
    "cand_sister_perrine",
    "cand_town_calderwick",
    "cand_street_pemberly",
    "cand_year_1962",
    "cand_house_4429",
    # soft-tier guessability close calls — each quotes its triggering base completion
    "cand_color_ochre",
    "cand_food_paprika",
    "cand_drink_kombucha",
    "cand_drink_horchata",
)

LOCKED_VALUES: tuple[str, ...] = tuple(f.value for f in LOCKED_FACTS)

# Measured token counts, transcribed from the report's `## Tokenizer Census` tables. Every
# entry round-tripped exact. This dict is the SOLE input to plan 14-05's D-19 generation-budget
# derivation — the budget is derived from measured counts, never from an estimate.
VALUE_TOKEN_CENSUS: dict[str, int] = {
    # locked core
    "cand_person_quillon": 5,
    "cand_dog_zorp": 4,
    "cand_cat_zibby": 5,
    "cand_sister_orsala": 6,
    "cand_town_brindlemoor": 8,
    "cand_street_marrowgate": 8,
    "cand_year_1987": 4,
    "cand_house_7412": 4,
    # soft tier
    "cand_color_chartreuse": 6,
    "cand_food_marzipan": 6,
    # calibration
    "cal_person_varek": 4,
    "cal_person_sedrin": 4,
    "cal_dog_nubbin": 5,
    "cal_dog_torvo": 5,
    "cal_cat_glimm": 4,
    "cal_sister_tolma": 5,
    "cal_town_ashenvale": 7,
    "cal_street_dunwold": 6,
    "cal_year_1974": 4,
    "cal_house_8351": 4,
    # register arm
    "arm_person_mirek": 4,
    "arm_dog_snorrel": 6,
    "arm_cat_wickett": 5,
    "arm_sister_holvana": 6,
    "arm_town_fenwyck": 5,
    "arm_year_1953": 4,
}

# D-08: the reserved phrasings of the facts that actually made it into the taught set. These
# are PERMANENTLY BANNED from every teaching set and are seed members of DEMO-06's never-seen
# split. They carry their measured base-failure provenance forward — FACTSET_GATE_SHA plus the
# base completion quoted verbatim in the report — so the held-out split is PROVEN unguessable
# by the base rather than assumed to be.
RESERVED_HELDOUT_PROBES: dict[str, tuple[str, ...]] = {
    f.id: GATE_PROBES[f.id] for f in LOCKED_FACTS + SOFT_TIER_FACTS
}
