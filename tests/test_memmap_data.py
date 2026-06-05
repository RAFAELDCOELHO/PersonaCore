"""RED tests for the full-corpus memmap data path (PRE-01).

Phase 5 encodes the TinyStoriesV2 corpus ONCE into flat ``np.uint16`` ``.bin`` memmaps
(``data/train.bin`` / ``data/val.bin``) and samples them with ``get_batch_memmap`` — the
nanoGPT idiom, re-opening the memmap every call so a long-lived mmap never grows RSS
(Pitfall 1). These tests build tiny ``.bin`` files in ``tmp_path`` from the committed
fixture using the SAME encode discipline as ``data.py::load_split`` (frozen tokenizer,
``allowed_special="all"`` so ``<|endoftext|>`` maps atomically to eos id 8184, ``uint16``
storage), then assert:

- ``test_encode_roundtrip``        — decode(first N of train.bin) == encode(first raw doc)
- ``test_one_eos_between_docs``    — exactly one eos (8184) per document, no doubled/missing
- ``test_get_batch_memmap_inbounds`` — (B, block) int64 windows, every index in vocab, no overrun
- ``test_no_leakage_disjoint``     — a val-stream window never occurs verbatim in train (no leakage)

RED until Task 2 implements ``get_batch_memmap``. CPU-only, GPU/MPS-free; reads the committed
fixture through the FROZEN tokenizer (mirrors ``test_data_split.py``). Do NOT weaken any
assertion to make these pass early.
"""

import pathlib

import numpy as np
import torch

from personacore.tokenizer import from_json
from personacore.training.data import get_batch_memmap

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "tinystories_fixture.txt"
TOKENIZER_PATH = "artifacts/tokenizer.json"
EOS_ID = 8184


def _read_docs():
    """Split the fixture into raw document strings on the ``<|endoftext|>`` separator.

    Mirrors the doc-boundary discipline of ``data.py::load_split`` at the text level: each
    document is the text BEFORE a ``<|endoftext|>`` marker; the marker itself terminates the
    doc and (via ``allowed_special="all"``) encodes atomically to eos id 8184.
    """
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    parts = text.split("<|endoftext|>")
    # Drop a trailing whitespace-only fragment (the file's final newline after the last marker).
    return [p for p in parts if p.strip()]


def _encode_docs_to_bin(docs, bin_path):
    """Encode whole documents (each terminated by ``<|endoftext|>``) into a flat uint16 ``.bin``.

    Each doc is rejoined with its terminating marker so the frozen tokenizer emits exactly one
    eos (8184) per document — the same one-EOS-between-docs invariant the full-corpus encode
    relies on. Stored as ``np.uint16`` (vocab 8192 < 65536), the nanoGPT ``.bin`` format.
    """
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
    ids = []
    for doc in docs:
        ids.extend(tok.encode(doc + "<|endoftext|>", allowed_special="all"))
    arr = np.asarray(ids, dtype=np.uint16)
    arr.tofile(bin_path)
    return arr


def test_encode_roundtrip(tmp_path):
    # decode(first-document tokens of the built train.bin) must round-trip back to the first raw
    # document through the FROZEN tokenizer — proves the .bin holds the real encoded corpus.
    tok = from_json(TOKENIZER_PATH)
    docs = _read_docs()
    bin_path = tmp_path / "train.bin"
    _encode_docs_to_bin(docs, bin_path)

    first_doc_ids = tok.encode(docs[0] + "<|endoftext|>", allowed_special="all")
    arr = np.fromfile(bin_path, dtype=np.uint16)
    head = arr[: len(first_doc_ids)].astype(np.int64).tolist()
    assert head == first_doc_ids
    assert tok.decode(head) == tok.decode(first_doc_ids)


def test_one_eos_between_docs(tmp_path):
    # Exactly one eos (8184) per document — no doubled, no missing separators.
    docs = _read_docs()
    bin_path = tmp_path / "train.bin"
    _encode_docs_to_bin(docs, bin_path)

    arr = np.fromfile(bin_path, dtype=np.uint16)
    assert int(np.count_nonzero(arr == EOS_ID)) == len(docs)


def test_get_batch_memmap_inbounds(tmp_path):
    # get_batch_memmap(bin_path, B, block, "cpu") -> (x, y): (B, block), int64, all indices in
    # the locked vocab, and the start bound never overruns the array.
    docs = _read_docs()
    bin_path = tmp_path / "train.bin"
    arr = _encode_docs_to_bin(docs, bin_path)

    batch_size, block_size = 4, 16
    assert len(arr) > block_size  # the bound len-block-1 stays valid (cf. test_data_split.py:77)
    x, y = get_batch_memmap(bin_path, batch_size=batch_size, block_size=block_size, device="cpu")
    assert x.shape == (batch_size, block_size)
    assert y.shape == (batch_size, block_size)
    assert x.dtype == torch.int64
    assert y.dtype == torch.int64
    assert int(x.min()) >= 0
    assert int(x.max()) < 8192
    assert int(y.max()) < 8192


def test_no_leakage_disjoint(tmp_path):
    # Build train.bin from one set of fixture docs and val.bin from a DISJOINT doc; an 8-token
    # window of the val stream must never occur verbatim in the train stream (no leakage).
    docs = _read_docs()
    assert len(docs) >= 3  # need disjoint train/val splits
    train_bin = tmp_path / "train.bin"
    val_bin = tmp_path / "val.bin"
    _encode_docs_to_bin(docs[:-1], train_bin)
    _encode_docs_to_bin(docs[-1:], val_bin)

    train_list = [int(i) for i in np.fromfile(train_bin, dtype=np.uint16)]
    val_list = [int(i) for i in np.fromfile(val_bin, dtype=np.uint16)]
    window = val_list[: min(8, len(val_list))]
    n = len(window)
    leaked = any(train_list[i : i + n] == window for i in range(len(train_list) - n + 1))
    assert not leaked
