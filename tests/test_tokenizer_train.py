"""BPE training determinism (TOK-01, D-08; RESEARCH Pitfall 1).

Training the same corpus twice MUST replay the identical merge table — pair selection is
totally ordered (freq, then pair-key) so there is no nondeterministic tie-break. This is the
lowest-rank-replay guarantee Phases 3+ rely on for stable token ids across runs/sessions.

RED until Plan 02 implements ``personacore.tokenizer``. All tests are CPU-only and GPU-free.
"""

import pathlib

import pytest
from personacore.tokenizer import BPETokenizer

from personacore.seeding import seed_everything

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "tiny_corpus.txt"


@pytest.fixture
def corpus() -> str:
    return CORPUS_PATH.read_text(encoding="utf-8")


def test_train_deterministic(corpus):
    # Train twice from a fresh, seeded state; the merge tables must be byte-identical (TOK-01).
    seed_everything(1337)
    a = BPETokenizer()
    a.train(corpus, vocab_size=512)

    seed_everything(1337)
    b = BPETokenizer()
    b.train(corpus, vocab_size=512)

    assert a.merges == b.merges


def test_trained_vocab_size(corpus):
    # A trained tokenizer reports the requested vocab size (bytes + merges + specials).
    tok = BPETokenizer()
    tok.train(corpus, vocab_size=512)
    assert tok.vocab_size == 512
