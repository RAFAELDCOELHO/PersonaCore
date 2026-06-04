"""Round-trip + chunk-join invariants (TOK-02, D-08: decode(encode(x)) == x).

Byte-level BPE has base-256 coverage, so EVERY string round-trips exactly — no ``<unk>``, no
normalization, no whitespace stripping (RESEARCH Pitfall 6). The chunk-join invariant proves
the pre-tok split is lossless: the concatenation of the chunk bytes equals the original UTF-8.

RED until Plan 02 implements ``personacore.tokenizer``. All tests are CPU-only and GPU-free.
"""

import pathlib

import pytest
from tests.fixtures.tricky_strings import TRICKY_STRINGS

from personacore.tokenizer import BPETokenizer

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "tiny_corpus.txt"


@pytest.fixture(scope="module")
def tok() -> BPETokenizer:
    t = BPETokenizer()
    t.train(CORPUS_PATH.read_text(encoding="utf-8"), vocab_size=512)
    return t


@pytest.mark.parametrize("s", TRICKY_STRINGS)
def test_roundtrip_exact(tok, s):
    # No <unk> ever: a byte-level tokenizer round-trips arbitrary text byte-for-byte (TOK-02).
    assert tok.decode(tok.encode(s)) == s


def test_chunk_join_invariant(tok):
    # The pre-tok split must be lossless: joined chunk bytes == original UTF-8 bytes.
    # Never strip/normalize (RESEARCH Pitfall 6).
    text = "  Hello, café — 日本語 1,234.56  "
    chunks = tok._split_chunks(text)
    assert b"".join(c.encode("utf-8") for c in chunks) == text.encode("utf-8")
