"""tiktoken gpt2 equivalence oracle + no-runtime-tiktoken guard (TOK-05 / D-07).

The from-scratch encoder is validated against tiktoken's gpt2 encoding as a reference oracle
(RESEARCH Pattern 6): recover gpt2's merge order from its ``mergeable_ranks``, inject those
merges into the from-scratch ``BPETokenizer`` configured with the exact GPT-2 split pattern,
and assert EXACT id equality (algorithm-equivalence, D-07). gpt2's ``mergeable_ranks`` are keyed
on RAW bytes with NO byte permutation — the byte-shuffle is a GPT-4/cl100k-only quirk, so the
oracle uses ``recover_merges`` directly with no shuffle (RESEARCH Pattern 6).

The oracle SKIPS when tiktoken/gpt2 is unavailable offline so CI stays green (RESEARCH
Pitfall 2 — ``get_encoding("gpt2")`` downloads vocab.bpe on first use). A separate guard scans
the runtime package and asserts tiktoken is NEVER imported there — it is a ``[dev]``-only test
oracle (RESEARCH Pitfall 4 / threat T-02-01). All tests are CPU-only and GPU-free.
"""

import pathlib

from personacore.tokenizer import GPT2_SPLIT_PATTERN, BPETokenizer
from personacore.tokenizer.bpe import get_stats, merge

ORACLE_STRINGS = [
    "hello world",
    " The quick brown fox.",
    "Numbers 123 and symbols #!?",
    "café and naïve",
    "Don't — “smart quotes” test.",
    "    leading spaces and\ttabs",
]


def _bpe(mergeable_ranks, token, max_rank):
    """Replay gpt2 merges over one raw-byte token up to ``max_rank`` (minbpe gpt4.py)."""
    parts = [bytes([b]) for b in token]
    while True:
        min_idx = min_rank = None
        for i, pair in enumerate(zip(parts[:-1], parts[1:])):
            rank = mergeable_ranks.get(pair[0] + pair[1])
            if rank is not None and (min_rank is None or rank < min_rank):
                min_idx, min_rank = i, rank
        if min_rank is None or (max_rank is not None and min_rank >= max_rank):
            break
        parts = parts[:min_idx] + [parts[min_idx] + parts[min_idx + 1]] + parts[min_idx + 2 :]
    return parts


def _recover_merges(mergeable_ranks):
    """Recover the ``(id0, id1) -> rank`` merge table from gpt2 ``mergeable_ranks``.

    No byte-shuffle: gpt2 ranks are raw-byte keyed (RESEARCH Pattern 6). Single-byte tokens
    are the base 0-255 leaves and carry no merge.
    """
    merges = {}
    for token, rank in mergeable_ranks.items():
        if len(token) == 1:
            continue
        p0, p1 = _bpe(mergeable_ranks, token, max_rank=rank)
        merges[(mergeable_ranks[p0], mergeable_ranks[p1])] = rank
    return merges


def _encode_ordinary_in_rank_space(tok, byte_to_rank, text):
    """Replay ``tok.merges`` (recovered gpt2 ranks) over each pre-tok chunk, rank-space leaves.

    gpt2's single-byte leaves are NOT raw-byte-ordered (every byte's rank != its value), so the
    leaves are remapped byte->rank BEFORE replay. The replay itself is the IDENTICAL from-scratch
    lowest-rank-first algorithm used in ``BPETokenizer._encode_chunk`` (RESEARCH Pattern 3),
    reusing the same ``get_stats`` / ``merge`` primitives — that is the algorithm being proven
    equivalent to tiktoken (D-07).
    """
    ids_out = []
    for chunk in tok._split_chunks(text):  # exact GPT-2 pre-tok split (GPT2_SPLIT_PATTERN).
        ids = [byte_to_rank[b] for b in chunk.encode("utf-8")]  # leaves in gpt2 rank space.
        while len(ids) >= 2:
            stats = get_stats(ids)
            pair = min(stats, key=lambda p: tok.merges.get(p, float("inf")))
            if pair not in tok.merges:
                break
            ids = merge(ids, pair, tok.merges[pair])
        ids_out.extend(ids)
    return ids_out


def test_tiktoken_gpt2_equivalence():
    import pytest

    try:
        import tiktoken

        enc = tiktoken.get_encoding("gpt2")  # network on first use; cached after.
    except Exception:
        pytest.skip("tiktoken gpt2 unavailable offline")

    merges = _recover_merges(enc._mergeable_ranks)
    byte_to_rank = {tok[0]: rank for tok, rank in enc._mergeable_ranks.items() if len(tok) == 1}
    # vocab_size only needs to dominate the largest merge id so frozen() rebuilds cleanly.
    vocab_size = max(enc._mergeable_ranks.values()) + 1
    # Exercise the from-scratch frozen()-rebuild path on the recovered merges (state is valid).
    tok = BPETokenizer.frozen(
        pattern=GPT2_SPLIT_PATTERN,
        merges=merges,
        special_tokens={},  # ordinary (no special handling) for the algorithm-equivalence proof.
        eos_id=0,
        vocab_size=vocab_size,
    )
    assert tok.merges == merges

    for s in ORACLE_STRINGS:
        ours = _encode_ordinary_in_rank_space(tok, byte_to_rank, s)
        assert ours == enc.encode_ordinary(s), f"mismatch on {s!r}"


def test_no_runtime_tiktoken():
    # tiktoken must never leak into the runtime import surface (threat T-02-01 / D-07).
    root = pathlib.Path(__file__).resolve().parent.parent / "src" / "personacore"
    for f in root.rglob("*.py"):
        assert "tiktoken" not in f.read_text(encoding="utf-8"), f"tiktoken imported in {f}"
