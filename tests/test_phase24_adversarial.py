"""ADVT-02 — the corpus-to-episode builder's six properties: the pool, the cuts, the parity.

The one that costs real money if it is wrong is
``test_every_episode_prompt_is_byte_equal_to_its_committed_corpus_row``. SC4 promises that the
attack trained against and the attack scored by cannot silently drift apart, and a promise is worth
nothing — so this file re-derives every prompt through ``build_recall_prompt`` DIRECTLY, not through
``adversarial_episodes``' own internal check, and compares under hard list equality against the
committed ``results/phase18_corpus.json`` row. A builder whose internal parity check was deleted
would still have to get past this one.

**No published value is typed into this file.** The D-10 lexicon is resolved from
``phase14_factset`` at runtime and run through the real ``phase14_recall.contains_value``, which is
the RUNTIME companion to 24-01's static scan: the static scan sees the refusal TABLE, this sees the
RENDERED answers, and a template that only leaked once formatted would be invisible to the first
and red under the second.

CPU-only, GPU/MPS-free. The tokenizer is the FROZEN production artifact — never trained, never
faked. ``scripts/phase18_extraction.py`` is imported READ-ONLY.
"""

import collections
import json
import pathlib
import sys

import pytest

from personacore.dialogue import build_recall_prompt
from personacore.seeding import seed_everything
from personacore.tokenizer import from_json

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import phase14_recall as pr  # noqa: E402
import phase18_extraction as p18  # noqa: E402
import phase24_adversarial as adv  # noqa: E402
import teach_persona as tp  # noqa: E402

TOK = from_json(tp.TOKENIZER_PATH)

# Paths resolved from the driver's OWN constants, never re-typed here: a second spelling of the
# corpus path is a second thing that can stop pointing at what the builder read.
CORPUS = json.loads(p18.CORPUS_PATH.read_text(encoding="utf-8"))
FIXTURE = json.loads(p18.CORPUS_SOURCE_FIXTURE.read_text(encoding="utf-8"))

# Built ONCE at import, so the monkeypatching test below cannot reach it and so five tests share
# one 336-prompt render. `test_the_episode_order_is_deterministic` builds its own, three times.
EPISODES = adv.adversarial_episodes(TOK)


def _trained_rows():
    """The corpus rows the builder should have kept, filtered HERE rather than asked for.

    Recomputed from the committed artifact so the zip below pairs each episode with a row this
    file resolved independently. Order is the corpus's own — the same order the builder must
    preserve, which is what makes positional pairing a real check rather than a coincidence.
    """
    return [
        row
        for row in CORPUS["prompts"]
        if row["tier"] == adv.TRAINED_TIER and row["family"] in adv.TRAINED_FAMILIES
    ]


def _published_values():
    """The D-10 lexicon plus the soft tier — every value the project ever locked, at runtime."""
    return (
        set(fs.LOCKED_VALUES)
        | {fact.value for fact in fs.GATE_REJECTED_CANDIDATES}
        | {fact.value for fact in fs.SOFT_TIER_FACTS}
    )


def test_the_trained_pool_is_336_episodes_and_family_independent():
    """The pool size is DERIVED from two artifacts, and the families carry equal weight.

    Both factors are read: the family count off ``TRAINED_FAMILIES`` and the per-family count off
    the binding fixture's ``core_taught`` tier. Pinning the product as a literal would go green on
    a corpus that had halved under a stale number nothing contradicts.

    The equal-counts half is D-06's measured property. Token VOLUME varies across the three
    families by up to ~1.59x (A3 carries a persona span A1 does not), but the EPISODE unit does
    not: the mixture is family-independent, which is what lets 24-06 price a ratio on episodes.
    """
    expected = len(adv.TRAINED_FAMILIES) * len(FIXTURE["questions"][adv.TRAINED_TIER])
    assert len(EPISODES) == expected, (
        f"{len(EPISODES)} episodes against {len(adv.TRAINED_FAMILIES)} trained families x "
        f"{len(FIXTURE['questions'][adv.TRAINED_TIER])} {adv.TRAINED_TIER} fixture rows"
    )
    assert adv.adversarial_pool_size(TOK) == len(EPISODES), (
        "adversarial_pool_size is meant to be the ONE derivation every consumer reads"
    )

    per_family = collections.Counter(row["family"] for row in _trained_rows())
    assert set(per_family) == set(adv.TRAINED_FAMILIES)
    assert len(set(per_family.values())) == 1, (
        f"the trained families are not equally weighted at the episode unit: {dict(per_family)}"
    )


def test_only_core_taught_rows_train():
    """D-03 on BOTH axes at once — the tier field, and the questions themselves.

    The tier field alone is the weaker half: it proves the builder read the column it says it read.
    The second assertion is the one that would survive a mislabelled corpus — the gated tier's
    QUESTION STRINGS appear in zero episodes, checked against the binding fixture rather than
    against the corpus's own label.
    """
    rows = _trained_rows()
    assert rows, "the tier filter kept nothing — a filter that drops everything forbids nothing"
    assert {row["tier"] for row in rows} == {adv.TRAINED_TIER}
    assert len(rows) < len(CORPUS["prompts"]), (
        "the filter kept the whole corpus, so the gated tier was never actually excluded"
    )

    gated = {row["question"] for row in FIXTURE["questions"][p18.GATED_TIER]}
    assert gated, "the gated tier of the binding fixture is empty — this check would be vacuous"
    trained_questions = {question for _persona, question, _answer in EPISODES}
    assert trained_questions & gated == set(), (
        f"{len(trained_questions & gated)} gated-tier question(s) reached the training pool"
    )


def test_a2_reaching_the_builder_is_refused_not_filtered(monkeypatch):
    """D-10 / D-12 — the held-out family is REFUSED, and the refusal is not a refusal of everything.

    The positive half runs first, deliberately: a guard that only forbids is satisfied by refusing
    every input, and an ``adversarial_episodes`` that raised unconditionally would pass the
    ``pytest.raises`` half alone while training nothing.

    The negative half widens ``TRAINED_FAMILIES`` past the filter, which is the only way to reach
    the belt-and-braces check at all — and reaching it is the point. A filter that silently drops
    and a filter that silently keeps produce indistinguishable output, and what is being kept out
    is a value prefix ``contains_value`` is structurally blind to.
    """
    assert EPISODES, "the real constants must build a NON-EMPTY pool"
    assert adv.HELD_OUT_FAMILY not in adv.TRAINED_FAMILIES

    monkeypatch.setattr(
        adv, "TRAINED_FAMILIES", tuple(adv.TRAINED_FAMILIES) + (adv.HELD_OUT_FAMILY,)
    )
    with pytest.raises(SystemExit) as refused:
        adv.adversarial_episodes(TOK)

    message = str(refused.value)
    assert adv.HELD_OUT_FAMILY in message, "the refusal did not name the family it refused"
    for reason in ("private value", "mask=1", "contains_value", "D-12"):
        assert reason in message, f"the refusal did not state {reason!r} as its reason"


def test_every_episode_prompt_is_byte_equal_to_its_committed_corpus_row():
    """SC4, re-proved from OUTSIDE the builder — the assertion this whole plan exists for.

    ``build_recall_prompt`` is driven directly here rather than ``adv.attack_prompt_ids``, so a
    builder whose internal parity check was deleted still fails this. The re-render goes through
    the FROZEN ``phase18_extraction`` builders and never through a decode of ``prompt_ids``: a
    decode/encode round trip is not guaranteed byte-equal through ``detokenize``, so a decoded
    question would rebuild a prompt that merely looks right.

    ``compared`` is asserted against the pool size because a loop that silently iterated nothing
    passes every assertion inside it.
    """
    rows = _trained_rows()
    assert len(rows) == len(EPISODES), "the episodes and the corpus rows did not pair positionally"

    compared = 0
    for (persona, question, _answer), row in zip(EPISODES, rows):
        assert list(build_recall_prompt(TOK, question, persona=persona)) == list(
            row["prompt_ids"]
        ), (
            f"SC4 parity broke on family {row['family']!r}, fact_id={row['fact_id']!r}, "
            f"seed_index={row['seed_index']}"
        )
        compared += 1
    assert compared == len(EPISODES), f"compared {compared} prompts against {len(EPISODES)}"

    # The persona shapes, asserted from Python rather than by eye: A1 is the bare form and A3
    # carries exactly the one value-free role scaffold.
    for (persona, _question, _answer), row in zip(EPISODES, rows):
        if row["family"] == adv.HELD_OUT_FAMILY:
            pytest.fail("a held-out row survived into the pool")
        expected = (p18.A3_ROLE_INSTRUCTION,) if row["family"] == "A3" else ()
        assert persona == expected, f"family {row['family']!r} carried persona {persona!r}"


def test_the_episode_order_is_deterministic():
    """D-08's permutation and the Phase 23 resume path both read this list POSITIONALLY.

    Three builds: two back to back, and one after re-seeding the global RNGs. The corpus is written
    tier-outer, row-inner, family-inner in one fixed sequence and the builder never sorts, so the
    filtered order is deterministic by construction — and the resume path refuses on any byte
    change, which is why "by construction" is not left as a claim here.
    """
    first = adv.adversarial_episodes(TOK)
    second = adv.adversarial_episodes(TOK)
    seed_everything(tp.SEED)
    third = adv.adversarial_episodes(TOK)

    assert first == second == third
    assert first == EPISODES, "the pool built at import differs from the pool built now"
    assert first, "three identical empty lists would satisfy the equality above"


def test_every_answer_is_a_slot_refusal_and_never_a_value():
    """The RUNTIME companion to 24-01's static D-02 scan: the rendered answers, not the table.

    The static scan walks the strings the module HOLDS. These strings exist only as a function's
    return, so a template that leaked a value once formatted — through a slot noun, through
    ``str.format``, through anything — would be invisible to the scan and red here.

    Run through the real ``phase14_recall.contains_value``, which is the extraction gate itself,
    against the whole published lexicon resolved at runtime. No value is typed into this file.
    """
    rows = _trained_rows()
    values = _published_values()
    assert values, "the published lexicon resolved empty — every containment check below is vacuous"

    checks = 0
    for (_persona, _question, answer), row in zip(EPISODES, rows):
        assert answer == adv.refusal_for(row["slot"]), (
            f"the answer for slot {row['slot']!r} is not the D-01 refusal for that slot"
        )
        for value in values:
            assert not pr.contains_value(answer, value), (
                f"a rendered refusal for slot {row['slot']!r} contains a published value — "
                "phase14_recall.contains_value would score it as an extraction, so the "
                "adversarial arm would be teaching the model to leak while declining"
            )
            checks += 1
    assert checks == len(EPISODES) * len(values), (
        f"{checks} containment checks against an expected {len(EPISODES)} x {len(values)}"
    )
