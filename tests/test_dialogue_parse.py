"""RED tests for the from-scratch fb-dialog episode parser (DATA-01).

``parse_episodes`` reads ParlAI fb-dialog text into ``(persona, turns)`` episodes: line
numbers reset to ``1`` at each episode boundary, ``your persona: `` lines are extracted with
the prefix stripped, dialogue lines split into exactly 4 tab-fields (the verified corpus
invariant — 0 exceptions in 73,520 lines), candidates ignored (D-04), and the LAST episode
(no trailing boundary line) is flushed at EOF (Pitfall 5).

The fixture is SYNTHETIC and format-faithful — never real corpus lines (D-00 no-re-host).
CPU-only, GPU-free.
"""

import pathlib

from personacore.dialogue import parse_episodes

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "personachat_fb_fixture.txt"


def test_episode_count():
    # Line-number reset to "1" is the only boundary signal; the fixture holds exactly 3 episodes.
    episodes = parse_episodes(FIXTURE_PATH)
    assert len(episodes) == 3


def test_persona_extraction_exact():
    # Persona lines arrive prefix-stripped, in order, punctuation ATTACHED and the `!.`
    # artifact preserved RAW — normalization is the detokenizer's job (D-06), not the parser's.
    persona, _ = parse_episodes(FIXTURE_PATH)[0]
    assert persona == [
        "i love to paint tiny houses.",
        "my cat is named turnip.",
        "i won a pie contest last year !.",
        "i do not eat meat.",
    ]


def test_turn_tuples_exact():
    # Dialogue lines split into exactly 4 tab-fields -> (user, assistant) pairs, in order.
    _, turns = parse_episodes(FIXTURE_PATH)[1]
    assert turns == [
        (
            "hello there , what do you do for fun ?",
            "i collect rocks when i travel in my old truck .",
        ),
        (
            "that is a neat hobby .",
            "thanks , my sister keeps some on her boat too .",
        ),
    ]


def test_last_episode_flushed_at_eof():
    # The final episode has NO trailing "1 "-boundary line — flush-at-EOF must emit it whole
    # (Pitfall 5: the classic bug drops the last episode entirely).
    persona, turns = parse_episodes(FIXTURE_PATH)[2]
    assert len(persona) == 5
    assert turns == [
        ("good morning , did you sleep well ?", "yes , i woke up early to bake bread ."),
        ("what kind of bread do you bake ?", "mostly rye , and my kitchen is painted orange ."),
    ]


def test_every_episode_shape():
    # Verified corpus properties reproduced by the fixture: 3-5 persona lines, >=2 turn pairs.
    for persona, turns in parse_episodes(FIXTURE_PATH):
        assert 3 <= len(persona) <= 5
        assert len(turns) >= 2


def test_candidates_absent_from_output():
    # The 4th tab-field (pipe-joined retrieval candidates) is ignored (D-04): turns are strict
    # 2-tuples and no candidate separator leaks into any parsed string.
    for persona, turns in parse_episodes(FIXTURE_PATH):
        for turn in turns:
            assert len(turn) == 2
            assert "|" not in turn[0]
            assert "|" not in turn[1]
