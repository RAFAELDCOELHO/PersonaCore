"""``draw_all``'s decode contract, against the REAL tokenizer.

The regression guard for the crash that killed the first 18-15 adapter-on arm:

    UnicodeDecodeError: 'utf-8' codec can't decode byte 0x9d in position 3: invalid start byte
      scripts/phase14_recall.py:661 -> src/personacore/tokenizer/bpe.py:209

Why no existing test caught it: ``tests/test_phase18_draws.py:85-93`` substitutes an
``_IdDecoder`` for the real decoder, and says why out loud — "it raises ``UnicodeDecodeError``
on byte sequences that are not valid UTF-8, which a hash-driven fake model produces constantly".
That substitution is right for what those tests measure (id-level prefix identity), but it left
the real decoder unexercised over a real generation: every other test either replaces
``draw_all`` outright (``test_phase14_scoring.py:1017``, ``test_phase16_ladder.py:835``) or
passes the id decoder. This file closes that hole and does nothing else.

The mechanism, stated so the guard cannot be "fixed" by masking instead:
``undecodable_ids_mask`` masks ids **absent from ``tokenizer.vocab``** — it prevents
``ValueError: unknown token id``, not ``UnicodeDecodeError``. Byte-level BPE keeps every single
byte in ``vocab``, so the 129 sampleable ids holding bare bytes 0x80-0xFF are *by design*
reachable: they are the pieces multi-byte glyphs are assembled from, and masking them would make
every non-ASCII character ungeneratable. A generation truncated at ``max_new_tokens`` or a stop
id can therefore end mid-glyph, exactly as ``generation/text.py:104-112`` (D-06) already ruled:
"a cumulative buffer that ends mid-glyph is NOT a defect".
"""

import pathlib
import sys

import pytest
import torch

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase14_recall as recall  # noqa: E402

from personacore.config import ModelConfig  # noqa: E402
from personacore.generation.text import undecodable_ids_mask  # noqa: E402
from personacore.tokenizer.io import from_json  # noqa: E402


@pytest.fixture(scope="module")
def tok():
    return from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")


def _byte_id(tok, byte):
    """The id whose vocab entry is exactly ``byte`` — derived, never hardcoded.

    Hardcoding 240 would keep passing against a retrained tokenizer that moved it.
    """
    for idx, raw in tok.vocab.items():
        if raw == byte:
            return idx
    raise AssertionError(f"no id holds {byte!r}")


class _ForcedLM(torch.nn.Module):
    """Emits a fixed id sequence, so the byte stream under test is chosen rather than hoped for.

    Satisfies the ``gpt.py`` forward contract (``(logits, loss)``) and carries a real
    ``ModelConfig`` so ``collect`` reads the genuine ``block_size``/``eos_id``/``vocab_size``.
    """

    def __init__(self, seq, prompt_len):
        super().__init__()
        self.config = ModelConfig()
        self.seq = list(seq)
        self.prompt_len = prompt_len

    def forward(self, idx, targets=None):
        step = min(idx.size(1) - self.prompt_len, len(self.seq) - 1)
        logits = torch.full(
            (idx.size(0), idx.size(1), self.config.vocab_size), -1e9, dtype=torch.float32
        )
        logits[..., self.seq[step]] = 1e9
        return logits, None


def _run(tok, tail_bytes):
    """Drive the REAL ``draw_all`` over a generation whose bytes end with ``tail_bytes``."""
    prompt_ids = [tok.special_tokens["<|assistant|>"]]
    body = [_byte_id(tok, b"h"), _byte_id(tok, b"i")]
    tail = [_byte_id(tok, bytes([b])) for b in tail_bytes]
    # The stop id terminates WITHOUT being yielded (D-05), so the generated ids are body + tail.
    seq = body + tail + [sorted(recall.STOP_IDS)[0]]
    model = _ForcedLM(seq, len(prompt_ids))
    forbid = undecodable_ids_mask(tok, model.config.vocab_size)
    return recall.draw_all(model, tok, prompt_ids, "cpu", forbid, index=0, n_samples=1)


def test_fragment_ids_are_sampleable_so_the_crash_is_reachable(tok):
    """The premise. If this ever goes to zero the guard below is testing nothing."""
    sampleable = set(tok.vocab) | set(tok.special_tokens.values())
    fragments = []
    for idx in sampleable:
        try:
            tok.decode([idx])
        except UnicodeDecodeError:
            fragments.append(idx)
    assert fragments, (
        "no sampleable id is a UTF-8 fragment, so a generation can no longer end mid-glyph. "
        "Either the tokenizer changed or the forbid mask now covers fragments — in both cases "
        "this file's premise moved and the guard below must be re-derived, not deleted."
    )
    # The mask must NOT be the fix: masking these would make every multi-byte glyph
    # ungeneratable, which is why D-06 tolerates the truncation instead of forbidding it.
    mask = undecodable_ids_mask(tok, ModelConfig().vocab_size)
    assert not bool(mask[0, fragments[0]]), (
        "undecodable_ids_mask now masks a byte-fragment id. That forbids the model from ever "
        "assembling a multi-byte character; the D-06 tolerant decode is the fix, not the mask."
    )


def test_draw_all_survives_a_generation_ending_mid_glyph(tok):
    """RED before the fix: this raised UnicodeDecodeError out of bpe.decode.

    b"\\xf0" opens a 4-byte glyph, so b"hi\\xf0" is a truncated character — the exact shape a
    stop id or ``max_new_tokens`` produces mid-glyph.
    """
    completions, stopped = _run(tok, b"\xf0")
    assert completions == ["hi", "hi"], (
        f"expected the valid prefix with the partial glyph dropped, got {completions!r}"
    )
    assert stopped == [True, True]


def test_draw_all_drops_only_the_partial_tail_not_valid_multibyte(tok):
    """A COMPLETE multi-byte glyph must survive intact — the fix must not truncate valid text."""
    completions, _ = _run(tok, "é".encode("utf-8"))  # 2 bytes, complete
    assert completions == ["hié", "hié"], (
        f"a complete multi-byte glyph was damaged: {completions!r}"
    )


def test_clean_generation_is_byte_identical_to_strict_decode(tok):
    """The D-01 safety property, as a test rather than an argument.

    Every completion any existing artifact recorded decoded strictly-clean. If the tolerant path
    ever returns something ``tok.decode`` would not have returned on such a stream, Phase 14's
    112 reference hit vectors could move and 18-15's positive control would be comparing against
    a shifted baseline.
    """
    completions, _ = _run(tok, b"")
    ids = [_byte_id(tok, b"h"), _byte_id(tok, b"i")]
    assert completions[0] == tok.decode(ids)
