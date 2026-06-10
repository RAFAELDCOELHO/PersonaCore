"""CPU-only unit tests for the Gradio-shaped cumulative-yield adapter (DEMO-01 / 08-02).

GPU/MPS-free and gradio-free: imports NOTHING from gradio or scripts/ — the testable demo
slice lives in the package (``generate_text_cumulative``) so CI covers it without the demo
extra installed. Every test runs on the tiny in-memory ``GPT`` fixture plus stub tokenizers
(the exact ``tests/test_generation_text.py`` approach) — never ``best.pt`` and never the
frozen ``artifacts/tokenizer.json``.

The contract under test (08-RESEARCH Pitfall 1): Gradio's ``ChatInterface`` replaces the
displayed message with each yield, so the callback must yield the FULL cumulative response —
yielding raw deltas makes the chat bubble flicker lone fragments.

  - test_yields_are_cumulative           — every yield extends the previous one (monotone growth)
  - test_final_yield_equals_collected_deltas — adapter adds accumulation and nothing else
  - test_kwargs_thread_through           — keyword-only max_new_tokens; (0, 4096] guard fires
                                           through the adapter (T-06-04 DoS lineage)
  - test_no_eos_literal_in_output        — no raw <|endoftext|> ever shown (Phase-6 D-05 carried)
"""

import pytest
import torch

from personacore.config import ModelConfig
from personacore.generation import generate_text, generate_text_cumulative

try:
    from personacore.model import GPT
except ImportError:  # pragma: no cover - model package ships in Phase 4.
    GPT = None


# --------------------------------------------------------------------------- #
# Fixtures / stubs (mirrors tests/test_generation_text.py — do not diverge)
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


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def test_yields_are_cumulative():
    # Each yield is the FULL response so far: every later yield extends the previous one
    # (monotone growth), lengths never shrink, and the stream actually grows at least once.
    model = _tiny_model()
    _force_sequence(model, [0, 1, 2, 3, 4, 5, 6, 7])  # 8 non-eos ids -> 8 visible chars.
    tok = _RecordingTokenizer()

    yields = list(generate_text_cumulative(model, tok, "hi", max_new_tokens=8, greedy=True))

    assert len(yields) >= 1
    for prev, nxt in zip(yields, yields[1:]):
        assert nxt.startswith(prev)  # cumulative: each yield extends the last (no flicker).
    lengths = [len(y) for y in yields]
    assert all(b >= a for a, b in zip(lengths, lengths[1:]))  # non-decreasing.
    assert any(b > a for a, b in zip(lengths, lengths[1:]))  # at least one strict increase.


def test_final_yield_equals_collected_deltas():
    # Under identical args, the LAST cumulative yield equals the joined delta stream — the
    # adapter adds accumulation and nothing else.
    forced = [3, 4, 5, 6]
    tok = _RecordingTokenizer()

    model = _tiny_model()
    _force_sequence(model, forced)
    cumulative = list(generate_text_cumulative(model, tok, "hi", max_new_tokens=4, greedy=True))

    _force_sequence(model, forced)  # reset the forcing counter for the second pass.
    deltas = list(generate_text(model, tok, "hi", max_new_tokens=4, greedy=True))

    assert cumulative[-1] == "".join(deltas)


def test_kwargs_thread_through():
    # max_new_tokens is KEYWORD-ONLY: a positional call raises TypeError at call time.
    model = _tiny_model()
    tok = _RecordingTokenizer()
    with pytest.raises(TypeError):
        generate_text_cumulative(model, tok, "hi", 8)  # type: ignore[misc]

    # The existing (0, 4096] guard fires THROUGH the adapter (T-06-04 DoS lineage).
    with pytest.raises(ValueError):
        list(generate_text_cumulative(model, tok, "hi", max_new_tokens=0, greedy=True))

    # temperature / top_k / generator thread through without error: one seeded warm call.
    _force_sequence(model, [2, 3])
    out = list(
        generate_text_cumulative(
            model,
            tok,
            "hi",
            max_new_tokens=2,
            temperature=0.8,
            top_k=5,
            generator=torch.Generator().manual_seed(0),
        )
    )
    assert out and all(isinstance(y, str) for y in out)


def test_no_eos_literal_in_output():
    # The core stops on EOS without yielding it (Phase-6 D-05); the final cumulative yield
    # never contains the raw separator literal.
    model = _tiny_model()
    eos_id = model.config.eos_id
    _force_sequence(model, [3, 4, eos_id])  # two visible ids, then EOS stops the stream.

    EOS_MARKER = "<|endoftext|>"

    class _MarkerTokenizer:
        def encode(self, text, allowed_special="all"):
            return []

        def decode(self, ids):
            # would surface the marker IF an eos id ever reached the buffer (it must not).
            return "".join(EOS_MARKER if i == eos_id else chr(ord("a") + i) for i in ids)

    yields = list(
        generate_text_cumulative(model, _MarkerTokenizer(), "", max_new_tokens=5, greedy=True)
    )
    assert yields  # the two pre-EOS ids stream out.
    assert EOS_MARKER not in yields[-1]
