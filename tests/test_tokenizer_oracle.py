"""tiktoken gpt2 equivalence oracle + no-runtime-tiktoken guard (TOK-05).

The from-scratch encoder is validated against tiktoken's gpt2 encoding as a reference oracle
(RESEARCH Pattern 6): recover gpt2's mergeable ranks, inject them into a from-scratch encoder
configured with the exact GPT-2 split pattern, and assert EXACT id equality. The oracle SKIPS
when tiktoken/gpt2 is unavailable offline so CI stays green (RESEARCH Pitfall 2). A separate
guard scans the runtime package and asserts tiktoken is NEVER imported there — it is a
``[dev]``-only test oracle (RESEARCH Pitfall 4 / threat T-02-01).

RED until Plan 03 implements the tokenizer. All tests are CPU-only and GPU-free.
"""

import pathlib

from personacore.tokenizer import GPT2_SPLIT_PATTERN, BPETokenizer

ORACLE_STRINGS = [
    "hello world",
    " The quick brown fox.",
    "Numbers 123 and symbols #!?",
    "café and naïve",
]


def test_tiktoken_gpt2_equivalence():
    import pytest

    try:
        import tiktoken

        enc = tiktoken.get_encoding("gpt2")  # network on first use
    except Exception:
        pytest.skip("tiktoken gpt2 unavailable offline")

    # Recover gpt2 merges and inject them into a from-scratch encoder (RESEARCH Pattern 6).
    tok = BPETokenizer.frozen(
        pattern=GPT2_SPLIT_PATTERN,
        mergeable_ranks=enc._mergeable_ranks,
        special_tokens={},
    )
    for s in ORACLE_STRINGS:
        assert tok.encode_ordinary(s) == enc.encode_ordinary(s)


def test_no_runtime_tiktoken():
    # tiktoken must never leak into the runtime import surface (threat T-02-01).
    root = pathlib.Path(__file__).resolve().parent.parent / "src" / "personacore"
    for f in root.rglob("*.py"):
        assert "tiktoken" not in f.read_text(encoding="utf-8"), f"tiktoken imported in {f}"
