"""CPU-only wrapper tests for the str->str text surface (GEN-01 / GEN-02 / 06-03).

GPU/MPS-free. Every test runs on a tiny in-memory ``GPT`` fixture plus a *stub* tokenizer —
never ``best.pt`` and never the frozen ``artifacts/tokenizer.json``. The stub tokenizer makes
the encode/prepend and the running-buffer decode contract observable in isolation:

  - test_eos_prepend_seed       — idx fed to the core begins with eos_id; empty -> [eos_id] (D-03)
  - test_prompt_stripped        — streamed/returned text holds only the NEW ids (D-02)
  - test_running_buffer_no_mojibake — glyph split across two ids streams whole, no crash (D-06)
  - test_no_raw_eos_in_output   — when the core stops on EOS, output carries no EOS marker (D-05)
  - test_max_new_tokens_cap     — max_new_tokens over cap / <= 0 raises ValueError (V5 / T-06-04)
"""

import pytest
import torch

from personacore.config import ModelConfig
from personacore.generation import generate_text, generate_text_str

try:
    from personacore.model import GPT
except ImportError:  # pragma: no cover - model package ships in Phase 4.
    GPT = None


# --------------------------------------------------------------------------- #
# Fixtures / stubs
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


def test_eos_prepend_seed():
    # The idx handed to the core must begin with eos_id; an empty prompt seeds exactly [eos_id].
    model = _tiny_model()
    eos_id = model.config.eos_id
    captured = {}

    # Spy on the core by wrapping forward: record the FIRST idx the core sees on step 0.
    orig_ids = [0, 1]
    state = {"i": 0}
    vocab = model.config.vocab_size

    def _forward(idx, targets=None):
        if state["i"] == 0:
            captured["first_idx"] = idx[0].tolist()
        forced = orig_ids[min(state["i"], len(orig_ids) - 1)]
        state["i"] += 1
        logits = torch.full((idx.size(0), idx.size(1), vocab), -1e9)
        logits[..., forced] = 1e9
        return logits, None

    model.forward = _forward  # type: ignore[method-assign]

    tok = _RecordingTokenizer()
    # Non-empty prompt: first id of the fed tensor is eos_id, followed by the encoded prompt.
    list(generate_text(model, tok, "hi", max_new_tokens=2, greedy=True))
    assert captured["first_idx"][0] == eos_id
    assert captured["first_idx"][1:] == tok.encode("hi")
    assert tok.encode_calls  # encode was actually consulted for a non-empty prompt.

    # Empty prompt: seeds EXACTLY [eos_id], encode is not used to extend the seed.
    model2 = _tiny_model()
    captured2 = {}
    state2 = {"i": 0}

    def _forward2(idx, targets=None):
        if state2["i"] == 0:
            captured2["first_idx"] = idx[0].tolist()
        state2["i"] += 1
        logits = torch.full((idx.size(0), idx.size(1), model2.config.vocab_size), -1e9)
        logits[..., 0] = 1e9
        return logits, None

    model2.forward = _forward2  # type: ignore[method-assign]
    list(generate_text(model2, _RecordingTokenizer(), "", max_new_tokens=1, greedy=True))
    assert captured2["first_idx"] == [eos_id]


def test_prompt_stripped():
    # The streamed text contains only the decoded NEW ids — never the prompt's characters.
    model = _tiny_model()
    _force_sequence(model, [3, 4, 5])  # NEW ids the core will emit.
    # decode maps 3,4,5 -> "d","e","f"; prompt encodes to other ids whose chars must NOT appear.
    tok = _RecordingTokenizer()
    out = generate_text_str(model, tok, "zzz", max_new_tokens=3, greedy=True)
    assert out == "def"  # exactly the NEW ids, prompt stripped (D-02).
    # the prompt's own decoded chars are absent.
    assert "z" not in out


def test_running_buffer_no_mojibake():
    # A multi-byte glyph is split across two ids: decode([a]) is a partial fragment, decode([a,b])
    # is the full glyph. The wrapper decodes the WHOLE running buffer each step, so it must never
    # raise and the streamed suffixes must concatenate to the complete glyph exactly once (D-06).
    GLYPH = "\U0001f600"  # an emoji — 4 UTF-8 bytes, split across two byte-level-BPE ids.

    class _SplitGlyphTokenizer:
        def __init__(self):
            self.encode_calls = []

        def encode(self, text, allowed_special="all"):
            self.encode_calls.append(text)
            return []  # empty prompt body; the seed is [eos_id].

        def decode(self, ids):
            # Per-id decode would split the glyph mid-byte and raise (mojibake/strict crash);
            # only the FULL [id_a, id_b] buffer yields the glyph. Mirrors strict byte-level BPE.
            if ids == [10]:
                raise UnicodeDecodeError("utf-8", b"\xf0", 0, 1, "unexpected end of data")
            if ids == [10, 11]:
                return GLYPH
            raise AssertionError(f"unexpected buffer {ids}")

    model = _tiny_model()
    _force_sequence(model, [10, 11])
    tok = _SplitGlyphTokenizer()

    suffixes = list(generate_text(model, tok, "", max_new_tokens=2, greedy=True))
    # Step 1 ([10]) decodes to nothing visible (partial fragment buffered, no crash); step 2
    # ([10,11]) reveals the whole glyph. The concatenated stream is the glyph exactly once.
    assert "".join(suffixes) == GLYPH
    assert suffixes.count(GLYPH) == 1


def test_no_raw_eos_in_output():
    # When the core hits EOS it stops WITHOUT yielding it (D-05); the joined output is empty here
    # (EOS is the first candidate) and never contains an EOS marker/separator.
    model = _tiny_model()
    eos_id = model.config.eos_id
    _force_sequence(model, [eos_id])  # first (and only) candidate is EOS.

    EOS_MARKER = "<|endoftext|>"

    class _MarkerTokenizer:
        def encode(self, text, allowed_special="all"):
            return []

        def decode(self, ids):
            # would surface the marker IF an eos id ever reached the buffer (it must not).
            return "".join(EOS_MARKER if i == eos_id else chr(ord("a") + i) for i in ids)

    out = generate_text_str(model, _MarkerTokenizer(), "", max_new_tokens=5, greedy=True)
    assert out == ""
    assert EOS_MARKER not in out


def test_max_new_tokens_cap():
    # Over the cap and non-positive both raise ValueError BEFORE the loop (V5 / T-06-04).
    model = _tiny_model()
    tok = _RecordingTokenizer()

    with pytest.raises(ValueError):
        list(generate_text(model, tok, "hi", max_new_tokens=10_000, greedy=True))
    with pytest.raises(ValueError):
        list(generate_text(model, tok, "hi", max_new_tokens=0, greedy=True))
    with pytest.raises(ValueError):
        list(generate_text(model, tok, "hi", max_new_tokens=-1, greedy=True))
    # a custom lower cap is honored.
    with pytest.raises(ValueError):
        list(generate_text(model, tok, "hi", max_new_tokens=5, max_new_tokens_cap=4, greedy=True))
