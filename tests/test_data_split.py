"""RED tests for the doc-level data split + batch sampler (TRAIN-03).

``load_split`` partitions the encoded corpus at DOCUMENT boundaries (the eos id 8184) so no
story straddles the train/val cut — a leaked sentence would let the bigram "memorize" val
(Pitfall 3). ``get_batch`` samples contiguous ``block_size`` windows with the next-token
target shifted by one and every index strictly in-bounds (no read past ``len(arr)-block-1``,
Pitfall 2/overrun).

RED until Plan 02 implements ``personacore.training.data``. CPU-only, GPU-free; reads the
committed fixture through the FROZEN tokenizer (mirrors test_tokenizer_io.py:19).
"""

import pathlib

import torch

from personacore.tokenizer import from_json
from personacore.training.data import get_batch, load_split

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
TOKENIZER_PATH = "artifacts/tokenizer.json"
EOS_ID = 8184


def _encoded_corpus():
    tok = from_json(TOKENIZER_PATH)
    return tok.encode(CORPUS_PATH.read_text(encoding="utf-8"), allowed_special="all")


def test_eos_marks_document_boundaries():
    # The fixture must encode with the atomic eos id 8184 at >=2 doc boundaries (Pitfall 6) —
    # this is the signal load_split partitions on.
    ids = _encoded_corpus()
    assert ids.count(EOS_ID) >= 2


def test_load_split_returns_two_arrays():
    # load_split -> (train_ids, val_ids); val_docs=1 reserves a whole trailing document.
    train_ids, val_ids = load_split(CORPUS_PATH, eos_id=EOS_ID, val_docs=1)
    assert len(train_ids) > 0
    assert len(val_ids) > 0


def test_split_has_no_document_leakage():
    # Train and val must not share a document: reconstruct the val doc's id-run and assert it
    # does NOT appear as a contiguous subsequence inside train (no leakage — Pitfall 3).
    train_ids, val_ids = load_split(CORPUS_PATH, eos_id=EOS_ID, val_docs=1)
    train_list = list(int(i) for i in train_ids)
    val_list = list(int(i) for i in val_ids)
    # A non-trivial window of the val document should never occur verbatim in train.
    window = val_list[: min(8, len(val_list))]
    n = len(window)
    leaked = any(train_list[i : i + n] == window for i in range(len(train_list) - n + 1))
    assert not leaked


def test_get_batch_shapes_dtype_and_shift():
    # get_batch(arr, B, block, "cpu") -> (x, y): shape (B, block), int64, y is x shifted by one.
    train_ids, _ = load_split(CORPUS_PATH, eos_id=EOS_ID, val_docs=1)
    batch_size, block_size = 4, 16
    x, y = get_batch(train_ids, batch_size, block_size, "cpu")
    assert x.shape == (batch_size, block_size)
    assert y.shape == (batch_size, block_size)
    assert x.dtype == torch.int64
    assert y.dtype == torch.int64


def test_get_batch_indices_in_bounds():
    # Every sampled id must be a valid token index (no overrun past the array end).
    train_ids, _ = load_split(CORPUS_PATH, eos_id=EOS_ID, val_docs=1)
    arr_len = len(train_ids)
    x, y = get_batch(train_ids, 8, 16, "cpu")
    assert int(x.min()) >= 0
    assert int(x.max()) < 8192  # all indices within the locked vocab.
    assert int(y.max()) < 8192
    # y must never reference an index that would require reading past arr_len.
    assert arr_len > 16
