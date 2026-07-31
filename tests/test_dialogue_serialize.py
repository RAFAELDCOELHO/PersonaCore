"""RED tests for dialogue serialization (DATA-02): detok (D-06), render (D-04), mask (D-01).

``detokenize`` is the minimal from-scratch regex normalizer: rejoins split contractions
(no-op on the primary fb-dialog corpus — zero apostrophes verified — but covers the D-05 JSON
fallback), closes space-before-punctuation, and normalizes the ``!.`` persona artifact.
``render_document`` is the D-04 string form (role markers, NO space after them — Pitfall 4).
``encode_dialogue`` builds equal-length ids+mask span-wise with EXACT D-01 semantics: first
``<|user|>``=0, every subsequent ``<|user|>``=1, assistant content=1, eos=1 — the three
Pitfall-14 edge tokens are pinned here. Role ids come from the LOCKED SPECIAL_TOKENS registry
and must encode atomically through the FROZEN production tokenizer (never a fresh one).

CPU-only, GPU-free. Do NOT weaken any assertion to make these pass early.
"""

import pytest

from personacore.dialogue import detokenize, encode_dialogue, render_document
from personacore.tokenizer import from_json
from personacore.tokenizer.special import EOS_ID, SPECIAL_TOKENS

TOKENIZER_PATH = "artifacts/tokenizer.json"

USER_ID = SPECIAL_TOKENS["<|user|>"]
ASSISTANT_ID = SPECIAL_TOKENS["<|assistant|>"]
SYSTEM_ID = SPECIAL_TOKENS["<|system|>"]

PERSONA = ["i like pie.", "my dog is old."]
TURNS = [
    ("hi , how are you ?", "i am fine , thanks !"),
    ("do you like pie ?", "yes , i love pie ."),
]


@pytest.fixture(scope="module")
def tok():
    # The FROZEN production artifact — the registry that ships is what matters, never a
    # freshly trained tokenizer (Pitfall 6).
    return from_json(TOKENIZER_PATH)


# --- detokenize (D-06) ---


def test_detok_closes_spaced_punctuation():
    # Corpus utterances space punctuation ("hi , how are you ?") — detok closes it.
    assert detokenize("i am fine , thanks !") == "i am fine, thanks!"
    assert detokenize("hi , how are you ?") == "hi, how are you?"


def test_detok_rejoins_nt_contraction():
    # PTB "do n't" form: no-op on the primary corpus (zero apostrophes) but covers the
    # D-05 JSON fallback (D-06 locked the rules regardless).
    assert detokenize("do n't") == "don't"


def test_detok_rejoins_apostrophe_suffixes():
    # "' m"-style split suffixes rejoin, with or without a space on both sides of the quote.
    assert detokenize("i ' m") == "i'm"
    assert detokenize("i 'm") == "i'm"
    assert detokenize("that ' s great") == "that's great"


def test_detok_normalizes_persona_bang_dot_artifact():
    # 280 train persona lines carry a trailing "!." — normalized to "!" (RESEARCH Open Q2).
    assert detokenize("i love to redesign houses !.") == "i love to redesign houses!"


def test_detok_stays_lowercase():
    # No truecasing (D-06): text passes through lowercase.
    assert detokenize("my cat is named turnip .") == "my cat is named turnip."


# --- role-token atomicity through the frozen tokenizer (DATA-02) ---


@pytest.mark.parametrize(
    "marker", ["<|user|>", "<|assistant|>", "<|system|>"], ids=["user", "assistant", "system"]
)
def test_role_token_is_atomic(tok, marker):
    # encode("a<marker>b") yields EXACTLY one role id (8185-8187), never byte-split.
    ids = tok.encode(f"a{marker}b", allowed_special="all")
    assert ids.count(SPECIAL_TOKENS[marker]) == 1


@pytest.mark.parametrize(
    "marker", ["<|user|>", "<|assistant|>", "<|system|>"], ids=["user", "assistant", "system"]
)
def test_role_token_roundtrips(tok, marker):
    # The marker survives decode(encode(...)) as the literal string.
    s = f"hello{marker}world"
    assert tok.decode(tok.encode(s, allowed_special="all")) == s


# --- render_document (D-04) ---


def test_render_document_exact_form():
    # <|system|> + newline-joined persona + per-turn <|user|>utt<|assistant|>reply,
    # NO space after role tokens (Pitfall 4), NO trailing eos marker in the string form.
    out = render_document(PERSONA, TURNS)
    expected = "<|system|>" + "\n".join(PERSONA)
    for user, reply in TURNS:
        expected += "<|user|>" + user + "<|assistant|>" + reply
    assert out == expected
    assert out.startswith("<|system|>" + PERSONA[0][0])  # no space after <|system|>
    assert "<|endoftext|>" not in out


# --- encode_dialogue (D-01 mask semantics) ---


def test_encode_dialogue_lengths_and_endpoints(tok):
    ids, mask = encode_dialogue(tok, PERSONA, TURNS)
    assert len(ids) == len(mask)
    assert ids[0] == SYSTEM_ID
    assert mask[0] == 0
    assert ids[-1] == EOS_ID
    assert mask[-1] == 1  # eos closes the final assistant turn (D-01 edge 3)


def test_encode_dialogue_mask_at_role_positions(tok):
    # The three Pitfall-14 edge tokens: FIRST <|user|> opens the dialogue -> mask 0;
    # every SUBSEQUENT <|user|> doubles as the prior assistant turn's stop token -> mask 1;
    # the <|assistant|> trigger itself is never trained -> mask 0.
    ids, mask = encode_dialogue(tok, PERSONA, TURNS)
    user_positions = [i for i, t in enumerate(ids) if t == USER_ID]
    assistant_positions = [i for i, t in enumerate(ids) if t == ASSISTANT_ID]
    assert len(user_positions) == 2
    assert len(assistant_positions) == 2
    assert mask[user_positions[0]] == 0
    assert mask[user_positions[1]] == 1
    assert all(mask[p] == 0 for p in assistant_positions)


def test_encode_dialogue_exact_span_structure(tok):
    # Independent reconstruction of the whole (ids, mask) pair: role ids appended literally
    # at their expected ordinal positions, content spans plain-encoded from detokenized text,
    # persona/user content mask 0, assistant content mask 1.
    ids, mask = encode_dialogue(tok, PERSONA, TURNS)

    persona_ids = tok.encode("\n".join(detokenize(p) for p in PERSONA))
    expected_ids = [SYSTEM_ID] + persona_ids
    expected_mask = [0] * (1 + len(persona_ids))
    for i, (user, reply) in enumerate(TURNS):
        user_ids = tok.encode(detokenize(user))
        reply_ids = tok.encode(detokenize(reply))
        expected_ids += [USER_ID] + user_ids + [ASSISTANT_ID] + reply_ids
        expected_mask += [1 if i > 0 else 0] + [0] * len(user_ids) + [0] + [1] * len(reply_ids)
    expected_ids += [EOS_ID]
    expected_mask += [1]

    assert ids == expected_ids
    assert mask == expected_mask


def test_encode_dialogue_content_span_masks(tok):
    # Every assistant-content id carries mask 1; every persona/user-content id carries mask 0
    # (checked span-wise between role-token positions, independent of tokenization detail).
    ids, mask = encode_dialogue(tok, PERSONA, TURNS)
    boundaries = [i for i, t in enumerate(ids) if t in (SYSTEM_ID, USER_ID, ASSISTANT_ID)]
    boundaries.append(len(ids) - 1)  # eos position closes the last span
    for start, end in zip(boundaries, boundaries[1:]):
        span_masks = mask[start + 1 : end]
        if ids[start] == ASSISTANT_ID:
            assert all(m == 1 for m in span_masks)  # assistant content trains
        else:
            assert all(m == 0 for m in span_masks)  # persona + user content never trains
