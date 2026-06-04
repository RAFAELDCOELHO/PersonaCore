"""GPT-2 pre-tokenization split pattern (TOK-01 / TOK-05).

The single load-bearing constant here is ``GPT2_SPLIT_PATTERN``: the exact minbpe/tiktoken
gpt2 regex that pre-splits text into word-like chunks BEFORE byte-level BPE runs, so merges
never cross word/space boundaries. ``regex`` is a pre-tok primitive on the same footing as
stdlib ``re`` (it is NOT a from-scratch BPE violation — the BPE algorithm itself is hand-rolled
in ``bpe.py``). stdlib ``re`` cannot compile ``\\p{L}``/``\\p{N}`` Unicode property escapes, so
``regex`` is required (RESEARCH D-05 / Pattern 1).
"""

import regex  # NOT stdlib re — \p{L}/\p{N} require the regex library (RESEARCH: D-05).

# Source: github.com/karpathy/minbpe regex.py + tiktoken gpt2 pat_str (CITED in 02-RESEARCH).
GPT2_SPLIT_PATTERN = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

# Module-internal compiled engine; the pattern STRING is the public, citable surface.
_COMPILED = regex.compile(GPT2_SPLIT_PATTERN)
