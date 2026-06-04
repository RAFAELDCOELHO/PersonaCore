"""Special-token atomicity + config wiring (TOK-03, D-03 / D-08 atomic-EOS).

The end-of-text marker is a single atomic id (D-03): it is split FIRST and NEVER merged across
or byte-split (RESEARCH Pattern 4 / Pitfall 3). Its id is shared with ``ModelConfig.eos_id`` so
the checkpoint and tokenizer agree. The locked vocab (8192) and EOS id (8184) are asserted here.

RED until Plan 02 implements ``personacore.tokenizer``. All tests are CPU-only and GPU-free.
"""

import pathlib

import pytest

from personacore.config import ModelConfig
from personacore.tokenizer import EOS_ID, EOS_TOKEN, BPETokenizer

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "tiny_corpus.txt"


@pytest.fixture(scope="module")
def tok() -> BPETokenizer:
    t = BPETokenizer()
    t.train(CORPUS_PATH.read_text(encoding="utf-8"), vocab_size=512)
    return t


def test_config_locks_eos_and_vocab():
    # The tokenizer EOS id mirrors ModelConfig.eos_id; vocab is the locked 8192 (D-01/D-03).
    assert ModelConfig().eos_id == 8184
    assert ModelConfig().vocab_size == 8192
    assert EOS_ID == 8184
    assert EOS_TOKEN == "<|endoftext|>"


def test_eos_is_atomic(tok):
    # encode("a<|endoftext|>b") yields EXACTLY one EOS id, never byte-split (atomicity).
    ids = tok.encode("a<|endoftext|>b")
    assert ids.count(EOS_ID) == 1


def test_eos_roundtrips(tok):
    # The special token survives decode(encode(...)) as the literal marker.
    s = "hello<|endoftext|>world"
    assert tok.decode(tok.encode(s)) == s
