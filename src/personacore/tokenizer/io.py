"""Schema-versioned freeze / reload of the trained tokenizer (TOK-04).

The trained tokenizer serializes to a single self-contained JSON artifact and reloads to a
behaviorally-identical encode/decode with a locked ``vocab_size`` (8192). This mirrors the
schema-versioned save/load discipline of ``checkpoint.py`` (a ``SCHEMA_VERSION`` constant
written into the payload and asserted on load) with one CRITICAL security divergence:

Security divergence from ``checkpoint.py``: the checkpoint uses the tensor library's binary
save/load (a code-executing serializer — trusted-own-file only). The tokenizer artifact is
shippable and may be edited or swapped, so it MUST be stdlib ``json`` — data-only, with no
code-executing deserializer ever invoked (a JSON artifact cannot execute code, threat
T-02-05). On load, ``from_json`` additionally asserts the
schema version (T-02-06) and validates every token id lies in ``[0, vocab_size)`` (V5 input
validation) before rebuilding, rejecting a malformed or out-of-range swapped artifact.
"""

import json

from .bpe import BPETokenizer

SCHEMA_VERSION = 1  # parallels CKPT_SCHEMA_VERSION in checkpoint.py; asserted on load.


def save_json(tok, path) -> None:
    """Freeze a trained tokenizer to a data-only, schema-versioned JSON artifact (TOK-04).

    JSON has no tuple keys, so ``merges`` is serialized as ``[p0, p1, idx]`` triples in
    ascending rank order (``sorted(... key=rank)``); ``from_json`` reconstructs the
    ``(p0, p1) -> idx`` dict from them. ``ensure_ascii=True`` keeps the artifact portable.
    """
    payload = {
        "schema_version": SCHEMA_VERSION,  # asserted on load (mirror checkpoint.py).
        "pattern": tok.pattern,
        "vocab_size": tok.vocab_size,  # 8192 LOCKED for the production artifact.
        "special_tokens": tok.special_tokens,
        "eos_id": tok.eos_id,
        # No tuple keys in JSON -> rank-ordered [p0, p1, idx] triples (RESEARCH: schema v1).
        "merges": [
            [p0, p1, idx] for (p0, p1), idx in sorted(tok.merges.items(), key=lambda kv: kv[1])
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=0)


def from_json(path) -> BPETokenizer:
    """Reload a frozen tokenizer from its JSON artifact, rebuilt via ``BPETokenizer.frozen``.

    Asserts the schema version (T-02-06) and validates every id in the artifact lies in
    ``[0, vocab_size)`` (V5 input validation — reject an out-of-range/swapped artifact)
    before reconstructing. Data-only: no code-executing deserializer is ever invoked.
    """
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    assert d["schema_version"] == SCHEMA_VERSION, "tokenizer schema mismatch"

    vocab_size = d["vocab_size"]
    merges = {}
    for p0, p1, idx in d["merges"]:
        # V5 input validation: every id (both pair members and the merge id) must be in range.
        for token_id in (p0, p1, idx):
            if not (0 <= token_id < vocab_size):
                raise ValueError(f"token id {token_id} outside [0, {vocab_size})")
        merges[(p0, p1)] = idx

    return BPETokenizer.frozen(
        pattern=d["pattern"],
        merges=merges,
        special_tokens=d["special_tokens"],
        eos_id=d["eos_id"],
        vocab_size=vocab_size,
    )
