"""CPU-only tests for the two Phase-14 package functions: the clean-room prompt and id streaming.

What is pinned, and why:

  - ``build_recall_prompt`` (RESEARCH Gap G2) is the D-18 SINGLE source of truth for the recall
    prompt — the scoring harness and the Gradio demo both import it, so the committed context
    dump and the demo's live token panel cannot diverge from what the model receives. The shape
    itself is the novel claim's load-bearing surface: an empty question must produce exactly the
    bare scaffold ``[8187, 8185, 8186]`` (``<|system|>`` with zero content, an empty user turn,
    the assistant handoff), and no answer value may ever reach the context — asserted both at the
    string level and as a token-level contiguous-subsequence check (T-14-01).
  - ``generate_text_from_ids`` (RESEARCH Gap G1) must drive the core from the caller's id list
    verbatim: ``tokenizer.encode`` is never called and ``eos_id`` is never prepended, because the
    string wrappers' ``[eos_id] + encode(prompt)`` path builds a prompt the model was never
    trained on. Its cumulative sibling is the CI regression test behind the demo's
    "streams and grows monotonically" claim, and the (0, 4096] bounds guard must still fire
    BEFORE any forward pass (T-14-02 / the T-06-04 DoS lineage).

CPU-only, GPU-free, checkpoint-free — every assertion runs in CI (no skip markers).
"""

import pytest
import torch

from personacore.config import ModelConfig
from personacore.dialogue import build_recall_prompt, detokenize
from personacore.generation import generate_text_from_ids, generate_text_from_ids_cumulative
from personacore.tokenizer import from_json
from personacore.tokenizer.special import SPECIAL_TOKENS

try:
    from personacore.model import GPT
except ImportError:  # pragma: no cover - model package ships in Phase 4.
    GPT = None

TOKENIZER_PATH = "artifacts/tokenizer.json"

USER_ID = SPECIAL_TOKENS["<|user|>"]
ASSISTANT_ID = SPECIAL_TOKENS["<|assistant|>"]
SYSTEM_ID = SPECIAL_TOKENS["<|system|>"]

QUESTION = "what is your dog's name?"
UNTAUGHT_VALUE = "zorp"


@pytest.fixture(scope="module")
def tok():
    # The FROZEN production artifact — the registry that ships is what matters, never a
    # freshly trained tokenizer (Pitfall 6).
    return from_json(TOKENIZER_PATH)


# --------------------------------------------------------------------------- #
# Prompt half — the frozen tokenizer (artifacts/tokenizer.json is git-tracked)
# --------------------------------------------------------------------------- #


def test_empty_question_scaffold(tok):
    # The bare clean-room scaffold: a system tag with zero content, an empty user turn, the
    # assistant handoff. Nothing else can be in the context by construction (14-RESEARCH F2).
    assert build_recall_prompt(tok, "") == [SYSTEM_ID, USER_ID, ASSISTANT_ID]
    assert build_recall_prompt(tok, "") == [8187, 8185, 8186]


@pytest.mark.parametrize("question", [QUESTION, "where do i live?", "what is my name?"])
def test_prompt_ends_at_assistant(tok, question):
    # Truncation ENDS at the assistant trigger — the model is handed the turn, never a reply.
    ids = build_recall_prompt(tok, question)
    assert ids[-1] == ASSISTANT_ID
    assert ids.count(ASSISTANT_ID) == 1  # the trigger appears exactly once.


def test_prompt_is_bare_system(tok):
    # Default persona=() -> an EMPTY persona span: <|user|> follows <|system|> immediately.
    ids = build_recall_prompt(tok, QUESTION)
    assert ids[0] == SYSTEM_ID
    assert ids[1] == USER_ID
    assert len(ids) == 19  # 14-RESEARCH F2 measured this exact prompt length.


def test_no_value_leaks_into_prompt(tok):
    # T-14-01: the answer value never enters the context. Checked at BOTH levels — a prompt
    # builder that quietly admitted a value would fail here even if it tokenized oddly.
    assert UNTAUGHT_VALUE not in QUESTION  # the value is genuinely absent from the question.
    ids = build_recall_prompt(tok, QUESTION)

    assert detokenize(UNTAUGHT_VALUE) not in tok.decode(ids)

    value_ids = tok.encode(detokenize(UNTAUGHT_VALUE), allowed_special="none")
    assert value_ids  # a non-empty needle, else the subsequence check is vacuous.
    windows = (ids[i : i + len(value_ids)] for i in range(len(ids) - len(value_ids) + 1))
    assert not any(w == value_ids for w in windows)


def test_persona_arg_appends_span(tok):
    # The persona argument exists ONLY for the explicitly-labelled D-11.1 fairness control;
    # the recall path never passes it. When passed it lengthens the span and nothing else.
    bare = build_recall_prompt(tok, QUESTION)
    stuffed = build_recall_prompt(tok, QUESTION, persona=["i have a dog named zorp."])
    assert len(stuffed) > len(bare)
    assert stuffed[0] == SYSTEM_ID
    assert stuffed[-1] == ASSISTANT_ID


# --------------------------------------------------------------------------- #
# Fixtures / stubs (mirrors tests/test_demo_callback.py — do not diverge)
# --------------------------------------------------------------------------- #


def _tiny_model():
    """A minimal CPU GPT — eos_id (15) < vocab_size (16), small block_size for cheap crops."""
    return GPT(
        ModelConfig(
            block_size=8,
            vocab_size=16,
            n_layer=1,
            n_head=1,
            n_embd=8,
            eos_id=15,
        )
    )


def _force_sequence(model, ids):
    """Monkeypatch model.forward so greedy decoding emits ``ids`` in order, one per step.

    The forward is called once per generated step; we pop the next forced id off a closure
    counter and make it the argmax. ``targets`` is accepted to honor the locked forward
    signature. Returns logits shaped (B, T, V) like the real model.
    """
    vocab = model.config.vocab_size
    state = {"i": 0}

    def _forward(idx, targets=None):
        step = state["i"]
        state["i"] += 1
        forced = ids[step] if step < len(ids) else ids[-1]
        logits = torch.full((idx.size(0), idx.size(1), vocab), -1e9)
        logits[..., forced] = 1e9
        return logits, None

    model.forward = _forward  # type: ignore[method-assign]


class _RecordingTokenizer:
    """Stub tokenizer: encode records its calls; decode maps ids -> single chars by default."""

    def __init__(self, id_to_str=None, encode_ret=None):
        self.encode_calls = []
        # default id->char map keeps tests independent of any real vocab.
        self._id_to_str = id_to_str or {i: chr(ord("a") + i) for i in range(32)}
        self._encode_ret = encode_ret

    def encode(self, text, allowed_special="all"):
        self.encode_calls.append(text)
        if self._encode_ret is not None:
            return list(self._encode_ret)
        # deterministic: one id per character, offset so it never collides with eos.
        return [ord(c) % 14 for c in text]

    def decode(self, ids):
        return "".join(self._id_to_str[i] for i in ids)


def _spy_forwards(model):
    """Additive wrapper over the installed forward: exposes the step counter and the first idx."""
    inner = model.forward
    seen = {"n": 0, "first": None}

    def _forward(idx, targets=None):
        if seen["n"] == 0:
            seen["first"] = idx[0].tolist()
        seen["n"] += 1
        return inner(idx, targets)

    model.forward = _forward  # type: ignore[method-assign]
    return seen


# --------------------------------------------------------------------------- #
# Streaming half — the tiny in-memory GPT (no checkpoint, no frozen tokenizer)
# --------------------------------------------------------------------------- #


def test_streams_cumulative_prefix_free_deltas():
    # The joined deltas ARE the continuation, and the prompt is never decoded back out (D-02):
    # prompt ids map to chars disjoint from the forced continuation, so any leak is visible.
    model = _tiny_model()
    forced = [0, 1, 2, 3]
    _force_sequence(model, forced)
    tok = _RecordingTokenizer()
    prompt_ids = [10, 11, 12]

    deltas = list(generate_text_from_ids(model, tok, prompt_ids, max_new_tokens=4, greedy=True))

    assert "".join(deltas) == tok.decode(forced)
    prompt_chars = set(tok.decode(prompt_ids))
    for delta in deltas:
        assert not (set(delta) & prompt_chars)


def test_cumulative_grows_monotonically():
    # SC4's "streams and grows monotonically" claim, pinned: every yield extends the previous
    # one, lengths never shrink, and the final yield equals the joined delta stream.
    forced = [3, 4, 5, 6]
    tok = _RecordingTokenizer()
    prompt_ids = [10, 11]

    model = _tiny_model()
    _force_sequence(model, forced)
    yields = list(
        generate_text_from_ids_cumulative(model, tok, prompt_ids, max_new_tokens=4, greedy=True)
    )

    assert len(yields) >= 1
    for prev, nxt in zip(yields, yields[1:]):
        assert nxt.startswith(prev)  # cumulative: each yield extends the last (no flicker).
    lengths = [len(y) for y in yields]
    assert all(b >= a for a, b in zip(lengths, lengths[1:]))  # non-decreasing.
    assert any(b > a for a, b in zip(lengths, lengths[1:]))  # at least one strict increase.

    _force_sequence(model, forced)  # reset the forcing counter for the second pass.
    deltas = list(generate_text_from_ids(model, tok, prompt_ids, max_new_tokens=4, greedy=True))
    assert yields[-1] == "".join(deltas)


def test_prompt_ids_used_verbatim():
    # Gap G1, precisely: the caller's ids reach the core UNCHANGED — no tokenizer.encode call
    # and no eos_id prepended (the string wrappers' path would do both).
    model = _tiny_model()
    _force_sequence(model, [0, 1])
    seen = _spy_forwards(model)
    tok = _RecordingTokenizer()
    prompt_ids = [10, 11, 12]

    list(generate_text_from_ids(model, tok, prompt_ids, max_new_tokens=2, greedy=True))

    assert tok.encode_calls == []  # the string path is never taken.
    assert seen["first"] == prompt_ids  # verbatim: nothing prepended, nothing dropped.


def test_bounds_guard():
    # T-14-02: the (0, cap] guard fires BEFORE the loop — no forward pass happens on rejection.
    model = _tiny_model()
    _force_sequence(model, [0, 1, 2])
    seen = _spy_forwards(model)
    tok = _RecordingTokenizer()

    for bad in (0, -1, 4097):
        with pytest.raises(ValueError) as exc:
            list(generate_text_from_ids(model, tok, [10, 11], max_new_tokens=bad, greedy=True))
        assert "(0, 4096]" in str(exc.value)

    assert seen["n"] == 0  # the forced-sequence counter never advanced.


def test_gen_kwargs_thread_through():
    # gen_kw reaches the core: a forbidden id is masked to -inf before the greedy argmax, so
    # the forced id can never be emitted (the CR-01 dead-id mask the demo threads through).
    model = _tiny_model()
    _force_sequence(model, [5, 5, 5, 5])
    tok = _RecordingTokenizer()
    forbid = torch.zeros(1, model.config.vocab_size, dtype=torch.bool)
    forbid[0, 5] = True

    out = "".join(
        generate_text_from_ids(model, tok, [10], max_new_tokens=4, greedy=True, forbid_ids=forbid)
    )

    assert out  # generation still produced something (the mask did not stall the loop).
    assert tok.decode([5]) not in out
