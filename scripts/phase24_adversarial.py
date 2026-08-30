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

Scope: BOTH halves now. 24-01 wrote the refusal table above; 24-05 added the corpus-to-episode
builder below it, in this same module, as that scope note said it would.
CPU-only, stdlib + ``phase14_factset`` at import. No torch, no numpy, no I/O — the builder's
``json`` / ``phase18_extraction`` / ``personacore.dialogue`` imports are all LAZY, inside the
functions that need them, so this import graph is unchanged for every existing consumer.
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


# =============================================================================================
# ===== ADVT-02 — THE CORPUS-TO-EPISODE BUILDER: WHAT THE MODEL IS TAUGHT TO ANSWER *TO* =====
# =============================================================================================
#
# The refusal half above says what the answer is. This half says which attacks it answers, and it
# reads them out of the COMMITTED artifact rather than rebuilding them. `build_corpus` is never
# called from here: SC4's guarantee is that the attack trained against and the attack scored by
# cannot drift apart, and a rebuild is a different reader of the same source, not the same bytes.
# What binds them is a hard list equality per episode against `prompt_ids`, below.

# D-03 — ONLY the reported tier trains. The gated tier stays out on BOTH axes at once, because the
# tier cut is simultaneously an attack-family cut and a paraphrase-family cut.
#
# Measured at HEAD 2026-08-30 off `results/phase18_corpus.json`'s own `source_family` column:
#   core_taught    -> {F1: 160, F2: 160, F6: 128}
#   core_held_out  -> {F3:  96, F7:  96, F8:  96, reserved: 128}
# F4 and F5 are ABSENT from the corpus entirely. D-03 therefore reduces OPERATIONALLY to this one
# tier comparison — there is no F4/F5 exclusion branch to write, and writing one would be dead code
# claiming to enforce something the artifact already makes vacuous.
TRAINED_TIER = "core_taught"

# D-10 — exactly THREE families train, and each inclusion has its own reason:
#   A1-mild / A1-aggressive : surface perturbation of the question. The whole prompt IS the
#                             question portion, which `assert_no_value_in_prompt` cleared at corpus
#                             build, so the training target can only ever be the refusal.
#   A3                      : a value-free ROLE SCAFFOLD delivered through the <|system|> span.
#                             It rides at mask=0 as CONTEXT and never as target
#                             (`encode_dialogue` marks the persona span 0), so teaching against it
#                             teaches the model to decline under a role frame without ever making
#                             the frame something the model is scored on reproducing.
TRAINED_FAMILIES = ("A1-mild", "A1-aggressive", "A3")

# The two A1 doses, split out so the render branch below dispatches on membership rather than on a
# string prefix — `startswith("A1")` would silently adopt a fifth family named A1-anything.
_A1_FAMILIES = ("A1-mild", "A1-aggressive")
_A3_FAMILY = "A3"

# D-10 / D-12 — A2 is HELD OUT, and the reason is CONTAINMENT, not performance.
#
# `phase18_extraction.build_a2_prompt` returns `build_recall_prompt(tok, question) + prefix_ids`,
# where `prefix_ids` are the leading `floor(len(value_ids) * INJECTION_FRACTION)` ids OF THE
# PRIVATE VALUE — appended PAST the `<|assistant|>` trigger. `encode_dialogue` marks assistant
# content mask=1. So an A2 training episode's TARGET would be
#     <a 25% prefix of the private value> + <the refusal>,
# which is the exact inverse of D-01's guarantee: the episode would teach the model to emit part of
# the value while declining. And the instrument cannot see it — `phase14_recall.contains_value` is
# `normalize(value) in normalize(completion)` and requires the WHOLE value, so the harm exists and
# the measurement is STRUCTURALLY BLIND to it. Not a small leak that scores low: a leak that scores
# zero.
#
# D-12: that makes A2 the held-out attack family as a MECHANICAL CONSEQUENCE. It is named here,
# before any training runs, with the reason declared as value containment. It is never selected by
# performance, and a later result on A2 cannot retroactively be the reason it was held out.
HELD_OUT_FAMILY = "A2"


def attack_prompt_ids(tok, question, persona):
    """The ONE ``build_recall_prompt(..., persona=...)`` call site in this module and this phase.

    **Why this call site exists, which is the justification the fourth ``PERSONA_ALLOWLIST`` entry
    in ``tests/test_phase14_scoring.py`` cites.** It does not place anything new in a prompt. It
    REPRODUCES a prompt that is already committed to ``results/phase18_corpus.json`` in order to
    PROVE byte-equality with it — every id it returns is compared under hard list equality against
    the committed ``prompt_ids`` by :func:`adversarial_episodes`, and a mismatch is a ``SystemExit``
    rather than a training run. A call site whose only output is fed to an equality against an
    artifact cannot widen what enters a span; it can only fail to match.

    The only persona this is ever called with is ``phase18_extraction.A3_ROLE_INSTRUCTION`` — a
    value-free role scaffold naming no fact, no slot and no persona value, and a frozen constant of
    an ancestry-guarded module, so the span's content is not something a future edit here can
    change. Everything else passes the empty tuple, which ``build_recall_prompt``'s own default
    makes byte-identical to the bare two-positional form; the argument is passed explicitly anyway
    so the two families take ONE code path and the A1 half is covered by the same parity proof.

    The sibling static guard ``test_no_fact_values_in_the_refusal_templates`` (24-01) scans every
    string this module holds — docstrings included — against the published-value lexicon, so the
    "value-free" half of the claim above is bound by a scan and not by this paragraph.

    ONE call, in ONE function, on purpose: the D-21 guard compares LISTS, so two calls carrying the
    keyword inside a single function would produce two identical tuples and break a hard equality
    that no allowlist entry can repair.
    """
    from personacore.dialogue import build_recall_prompt  # LAZY — see the module docstring.

    return list(build_recall_prompt(tok, question, persona=persona))


def _adversarial_pool(tok):
    """The ONE pass over the corpus: ``(episodes, families)``, POSITIONALLY PAIRED by construction.

    ``episodes`` is the trained attack pool as ``(persona, question, answer)`` triples —
    parity-proved, A2-free. ``families`` is that same list's per-episode ``family`` column, appended
    in the same loop iteration, so the two are aligned because they are BUILT together and not
    because a second reader re-derived the join and happened to agree. :func:`adversarial_episodes`
    and :func:`adversarial_episode_families` are thin views onto this; neither re-filters.

    One episode per committed corpus row that survives the D-03 tier cut and the D-10 family cut.
    The question is RE-RENDERED through ``phase18_extraction``'s own frozen builders and never
    recovered by decoding ``prompt_ids``: a decode/encode round trip is not guaranteed byte-equal
    through ``detokenize``, so a decoded question would produce a prompt that merely looks right.

    **Order is the CORPUS's own and is never sorted.** The corpus is written tier-outer, row-inner,
    family-inner in one fixed sequence, so a filter that preserves order is already deterministic
    and stable across processes. D-08's permutation and the Phase 23 resume path both read this
    list positionally, and both refuse on any byte change.

    ``phase18_extraction`` is imported READ-ONLY. ``build_corpus`` is never called: SC4 requires the
    check be taken against the COMMITTED artifact, and a rebuild is a second reader that can agree
    with itself while disagreeing with what was scored.
    """
    import json  # LAZY, with the driver below — the refusal half above does no I/O at import.

    import phase18_extraction as p18  # LAZY — keeps this module's import graph stdlib + factset.

    corpus = json.loads(p18.CORPUS_PATH.read_text(encoding="utf-8"))
    fixture = json.loads(p18.CORPUS_SOURCE_FIXTURE.read_text(encoding="utf-8"))

    # ORDERED hard equality, `tests/test_phase18_corpus.py`'s register. Never a set or a subset:
    # a reordered schema still carries every name, and every field read below would still resolve
    # while meaning something else.
    if corpus.get("entry_keys") != list(p18.CORPUS_ENTRY_KEYS):
        raise SystemExit(
            f"[phase24_adversarial] {p18.CORPUS_PATH.name} declares entry_keys "
            f"{corpus.get('entry_keys')} against this session's "
            f"{list(p18.CORPUS_ENTRY_KEYS)}. The artifact and the driver have drifted, so every "
            "field this builder reads would resolve while naming a different column."
        )

    # (tier, fact_id, seed_index) -> question. The corpus carries `prompt_ids` but NOT the question
    # TEXT, and the fixture is the only place that text lives.
    questions = {
        (tier, row["fact_id"], row["seed_index"]): row["question"]
        for tier, rows in fixture["questions"].items()
        for row in rows
    }

    rows = [
        row
        for row in corpus["prompts"]
        if row["tier"] == TRAINED_TIER and row["family"] in TRAINED_FAMILIES
    ]

    episodes, families = [], []
    for row in rows:
        # BELT AND BRACES beside the filter above, not instead of it. A filter that silently drops
        # and a filter that silently keeps are indistinguishable from their output, and the thing
        # being kept out here is a value prefix the extraction gate cannot see.
        if row["family"] == HELD_OUT_FAMILY:
            raise SystemExit(
                f"[phase24_adversarial] an {HELD_OUT_FAMILY} row reached the episode builder "
                f"(fact_id={row['fact_id']!r}, seed_index={row['seed_index']}). "
                f"{HELD_OUT_FAMILY} appends leading ids OF THE PRIVATE VALUE past the "
                "<|assistant|> trigger, and assistant content is mask=1, so this episode's TARGET "
                "would be a 25% prefix of the private value followed by a refusal — the inverse of "
                "D-01. phase14_recall.contains_value requires the WHOLE value, so the leak would "
                "score ZERO rather than score low. D-12 holds this family out for that reason, "
                "declared before training and never chosen by performance."
            )

        key = (row["tier"], row["fact_id"], row["seed_index"])
        if key not in questions:
            raise SystemExit(
                f"[phase24_adversarial] no fixture question for {key!r} in "
                f"{p18.CORPUS_SOURCE_FIXTURE.name}. The corpus and its binding fixture have "
                "unpaired; naming the missing key here buys out a bare KeyError raised a third of "
                "the way through the build, after the corpus already looked complete."
            )
        question = questions[key]

        if row["family"] in _A1_FAMILIES:
            attacked, persona = p18.apply_a1(question, dose=row["dose"]), ()
        elif row["family"] == _A3_FAMILY:
            attacked, persona = question, (p18.A3_ROLE_INSTRUCTION,)
        else:
            # No default fall-through. A family that reaches here has no declared render, and
            # guessing one would train against an attack shape nobody reviewed.
            raise SystemExit(
                f"[phase24_adversarial] family {row['family']!r} passed the TRAINED_FAMILIES "
                f"filter {TRAINED_FAMILIES} but has no declared re-render. Every trained family "
                "needs an explicit branch reproducing exactly what build_corpus built for it."
            )

        ids = attack_prompt_ids(tok, attacked, persona)
        committed = list(row["prompt_ids"])
        if ids != committed:
            first = next(
                (i for i, (a, b) in enumerate(zip(ids, committed)) if a != b),
                min(len(ids), len(committed)),
            )
            raise SystemExit(
                f"[phase24_adversarial] SC4 parity FAILED on family {row['family']!r}, "
                f"fact_id={row['fact_id']!r}, seed_index={row['seed_index']}: re-rendered "
                f"{len(ids)} ids against {len(committed)} committed, first differing index "
                f"{first}. The attack trained against would not be the attack scored by, which is "
                "the one drift SC4 exists to make structurally impossible."
            )

        episodes.append((persona, attacked, refusal_for(row["slot"])))
        families.append(row["family"])

    # DERIVED from the filtered fixture, never the literal — the count is what the artifacts say it
    # is, and typing it here would make a shrunken corpus agree with a stale number.
    expected = len(TRAINED_FAMILIES) * len(fixture["questions"][TRAINED_TIER])
    if len(episodes) != expected:
        raise SystemExit(
            f"[phase24_adversarial] built {len(episodes)} episodes against an expected "
            f"{expected} = len(TRAINED_FAMILIES)={len(TRAINED_FAMILIES)} x the "
            f"{TRAINED_TIER} fixture row count "
            f"{len(fixture['questions'][TRAINED_TIER])}. Every rate the adversarial arm reports "
            "carries this as its denominator, so a short pool would publish a number nothing in "
            "the artifacts contradicts."
        )

    # The families column is what 24-06 reports per grid point, so it is CHECKED here rather than
    # trusted: an equal TOTAL is satisfied by a corpus that lost every A3 row and gained as many
    # A1-mild ones. Per-family equality is what makes "family-independent at the episode unit" a
    # measurement. The length comparison is the alignment proof — each label is appended in the
    # same loop iteration as its episode, so a mismatch means that loop itself drifted.
    per_family = {family: families.count(family) for family in TRAINED_FAMILIES}
    fixture_rows = len(fixture["questions"][TRAINED_TIER])
    if len(families) != len(episodes) or set(per_family.values()) != {fixture_rows}:
        raise SystemExit(
            f"[phase24_adversarial] the pool is {per_family} against {fixture_rows} "
            f"{TRAINED_TIER} fixture rows per family ({len(families)} family labels for "
            f"{len(episodes)} episodes). D-10 trains exactly {TRAINED_FAMILIES} and 24-06 sizes "
            "and reports the mixture per family, so an unbalanced pool would publish per-family "
            "rates whose denominators are not the ones the record names."
        )
    return episodes, families


def adversarial_episodes(tok):
    """The trained attack pool: ``list[tuple[tuple[str, ...], str, str]]`` = (persona, q, a).

    PINNED return shape — ``teach_persona.build_bins`` and ``tests/test_phase24_adversarial.py``
    both read it positionally. The per-episode family travels in the SIBLING view below rather
    than as a fourth member, so widening the report never widens this tuple.
    """
    return _adversarial_pool(tok)[0]


def adversarial_episode_families(tok):
    """The per-episode ``family`` label, in :func:`adversarial_episodes`' EXACT order.

    Built in the same pass as the episodes (see :func:`_adversarial_pool`), so the pairing is a
    property of ONE loop rather than of two readers agreeing. ``teach_persona._mix_adversarial``
    reports the SELECTED prefix's per-family counts from this, and that report is the only thing
    that can see a corpus ROW REORDER: the selection is a prefix of ``pool * ceil(...)``, so a
    family-grouped order would train one family at every small ratio while the full-pool balance
    assertion in ``tests/test_phase24_adversarial.py`` stayed green.
    """
    return _adversarial_pool(tok)[1]


def adversarial_pool_size(tok):
    """``len(adversarial_episodes(tok))`` — ONE derivation of the pool size, for every consumer.

    24-06 sizes the mixture from this and the ADVT-03 record reports it. A second count taken any
    other way is a second thing that can stop agreeing with what actually trained.
    """
    return len(adversarial_episodes(tok))
