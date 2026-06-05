"""Committed-fixture data path (D-06 / TRAIN-03): encode -> uint16 -> doc-level split -> get_batch.

Bounded fixture ONLY — the full-corpus uint16 memmap + TinyStories fetch is Phase 5 (PRE-01).
The split happens at DOCUMENT boundaries (the eos id 8184), never mid-story, which gives a
provable no-leakage train/val guarantee (TRAIN-03 / Pitfall 3): no sentence straddles the cut,
so the bigram cannot "memorize" val through a leaked prefix. ``get_batch`` is the nanoGPT idiom:
random contiguous ``block_size`` windows with the next-token target shifted by one, every index
strictly in-bounds (Pitfall 3 — bound the start to ``len(arr) - block_size - 1``).

The frozen tokenizer (``artifacts/tokenizer.json``) is LOADED, never retrained (Pitfall 6).
Storage stays ``uint16`` (compact); indices are cast to ``int64`` only at batch time for
``nn.Embedding`` / ``cross_entropy``.
"""

import numpy as np
import torch

from personacore.tokenizer import from_json

TOKENIZER_PATH = "artifacts/tokenizer.json"


def load_split(fixture_path, eos_id=8184, val_docs=1):
    """Encode the fixture and split it at document boundaries into disjoint train/val arrays.

    Loads the FROZEN tokenizer (never ``.train()`` — Pitfall 6), encodes the fixture so the
    ``<|endoftext|>`` marker maps atomically to ``eos_id`` (8184), then partitions the token
    stream into per-document lists on that boundary (eos kept as each doc's terminator). The
    last ``val_docs`` whole documents go to val, the rest to train — no document straddles the
    cut (no leakage, Pitfall 3). Returns two ``np.uint16`` arrays.
    """
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
    with open(fixture_path, encoding="utf-8") as fh:
        text = fh.read()
    ids = tok.encode(text, allowed_special="all")  # <|endoftext|> -> atomic eos_id (8184)

    docs, cur = [], []
    for t in ids:
        cur.append(t)
        if t == eos_id:
            docs.append(cur)
            cur = []
    # A trailing fragment with no closing eos is a real document only if it carries content.
    # A whitespace-only tail (e.g. the file's final "\n" after the last <|endoftext|>) is NOT a
    # document — promoting it would make val a degenerate single-newline run that "leaks" into
    # train everywhere (Pitfall 3 / no-leakage contract). Drop it; keep a content-bearing tail.
    if cur and tok.decode(cur).strip():
        docs.append(cur)

    assert len(docs) >= 2, "fixture must contain >= 2 documents (D-06)"
    assert 1 <= val_docs < len(docs), "val_docs reserves >=1 doc, train stays non-empty"

    train_ids = np.array([t for d in docs[:-val_docs] for t in d], dtype=np.uint16)
    val_ids = np.array([t for d in docs[-val_docs:] for t in d], dtype=np.uint16)
    return train_ids, val_ids


def get_batch(arr, batch_size, block_size, device):
    """Draw ``batch_size`` random contiguous ``(x, y)`` windows from ``arr`` (nanoGPT idiom).

    Start indices are bounded to ``len(arr) - block_size - 1`` so neither ``x`` nor the +1
    shifted ``y`` ever overruns the array (Pitfall 3). Windows are cast ``uint16`` -> ``int64``
    for ``nn.Embedding`` / ``cross_entropy`` and moved to ``device``.
    """
    ix = np.random.randint(0, len(arr) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(arr[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(arr[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)


def get_batch_memmap(bin_path, batch_size, block_size, device):
    """Draw ``batch_size`` random ``(x, y)`` windows from a flat ``uint16`` ``.bin`` memmap.

    The full-corpus analog of :func:`get_batch` (PRE-01): identical nanoGPT indexing — the same
    ``len(data) - block_size - 1`` start bound (Pitfall 3, no overrun), the same ``uint16`` ->
    ``int64`` cast at draw time, the same ``.to(device)``. The ONLY difference is the in-RAM
    ``arr`` is replaced by a ``np.memmap`` that is **re-opened every call**: a long-lived memmap
    accumulates RSS across thousands of training steps (nanoGPT leak — Pitfall 1), so it is opened
    fresh and discarded per batch. Plain ``.to(device)`` only — the CUDA-only pinned-host /
    async-copy transfer flags have no MPS/CPU path this phase, so they are deliberately absent.
    """
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)
