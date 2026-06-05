"""Run-once encode of the TinyStoriesV2-GPT4 corpus -> data/train.bin / data/val.bin (PRE-01).

The thin data-prep slice of Phase 5: turn the two downloaded ``TinyStoriesV2-GPT4-*.txt`` files
into flat ``np.uint16`` memmaps (the nanoGPT ``.bin`` format) that ``get_batch_memmap`` samples
during the long run. This is the **encode-once** discipline (D-09): the corpus is never
re-tokenized inside the training loop.

Mirrors ``scripts/train_bigram.py`` — a no-CLI thin entry: ``_REPO_ROOT``-relative path
constants, a ``main()``, and an ``if __name__ == "__main__"`` guard. NO argparse (D-04). All real
logic (the encode discipline) reuses the package's frozen tokenizer.

Streaming (RESEARCH Pattern 1): the train file is ~2.23 GB — it is read and encoded
**document-by-document** on the ``<|endoftext|>`` separator, accumulating ``uint16`` shards that
are concatenated and written with ``arr.tofile(...)``. The whole file is never held in one Python
string. Each document is rejoined with its terminating ``<|endoftext|>`` marker and encoded with
``allowed_special="all"`` so the marker maps **atomically** to eos id 8184 — giving exactly one
EOS between documents with NO manual EOS injection (Pitfall 6 / D-09).

Run manually AFTER downloading the two ``.txt`` files into ``data/`` (CLAUDE.md Sources):
  python scripts/encode_corpus.py
Outputs ``data/train.bin`` / ``data/val.bin`` (gitignored). This is NOT part of automated
verification — the 2.23 GB encode is a one-time manual step on the real machine.
"""

import pathlib

import numpy as np

from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
TRAIN_TXT = _REPO_ROOT / "data" / "TinyStoriesV2-GPT4-train.txt"
VAL_TXT = _REPO_ROOT / "data" / "TinyStoriesV2-GPT4-valid.txt"
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"
VAL_BIN = _REPO_ROOT / "data" / "val.bin"
EOS_ID = 8184  # ModelConfig.eos_id — source <|endoftext|> already separates docs; do NOT inject

_SEP = "<|endoftext|>"


def _iter_documents(txt_path):
    """Yield raw document strings from a TinyStoriesV2 ``.txt``, split on ``<|endoftext|>``.

    Streams line-by-line and flushes a document whenever the separator is reached, so the whole
    multi-GB file is never materialized as one Python string (RESEARCH Pattern 1). Whitespace-only
    fragments (e.g. the trailing newline after the final separator) are skipped — they are not
    documents and would otherwise emit a degenerate lone EOS.
    """
    buf = []
    with open(txt_path, encoding="utf-8") as fh:
        for line in fh:
            if _SEP in line:
                head, _, tail = line.partition(_SEP)
                buf.append(head)
                doc = "".join(buf)
                if doc.strip():
                    yield doc
                buf = [tail] if tail else []
            else:
                buf.append(line)
    rest = "".join(buf)
    if rest.strip():  # a final content-bearing document with no trailing separator
        yield rest


def encode_to_bin(txt_path, bin_path):
    """Stream-encode ``txt_path`` into a flat ``uint16`` ``.bin`` at ``bin_path``; return the array.

    Loads the FROZEN tokenizer (never ``.train()`` — Pitfall 6) and encodes each document rejoined
    with its ``<|endoftext|>`` marker via ``allowed_special="all"`` so the marker maps atomically
    to eos id 8184 (exactly one EOS per document, no manual injection). ``uint16`` shards are
    accumulated, concatenated, and written with ``arr.tofile(...)``.
    """
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)

    try:
        from tqdm import tqdm  # optional progress bar; only used if already importable

        docs = tqdm(_iter_documents(txt_path), desc=f"encode {txt_path.name}", unit="doc")
    except ImportError:
        docs = _iter_documents(txt_path)

    shards = []
    for doc in docs:
        ids = tok.encode(doc + _SEP, allowed_special="all")  # marker -> atomic eos 8184
        shards.append(np.asarray(ids, dtype=np.uint16))

    arr = np.concatenate(shards) if shards else np.empty(0, dtype=np.uint16)
    arr.tofile(bin_path)

    # Post-build sanity (T-05-01): a truncated/corrupt download fails these before any long run.
    check = np.fromfile(bin_path, dtype=np.uint16)
    eos_count = int(np.count_nonzero(check == EOS_ID))
    assert eos_count >= 1, f"{bin_path} has no eos ({EOS_ID}) — corrupt/empty corpus?"
    prefix = tok.decode(check[:200].astype(np.int64).tolist())  # coherent-story round-trip
    print(f"  {bin_path.name}: {len(check):,} tokens, {eos_count:,} docs (eos)")
    print(f"  decoded prefix: {prefix[:200]!r}")
    return arr


def main():
    print(f"[encode_corpus] frozen tokenizer: {TOKENIZER_PATH}")
    print(f"[encode_corpus] encoding train: {TRAIN_TXT}")
    encode_to_bin(TRAIN_TXT, TRAIN_BIN)
    print(f"[encode_corpus] encoding val:   {VAL_TXT}")
    encode_to_bin(VAL_TXT, VAL_BIN)
    print("[encode_corpus] done — data/train.bin and data/val.bin written (gitignored)")


if __name__ == "__main__":
    main()
