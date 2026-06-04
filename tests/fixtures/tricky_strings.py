"""Round-trip stress corpus for the BPE tokenizer (TOK-02).

A byte-level tokenizer must satisfy ``decode(encode(s)) == s`` for EVERY string here — no
``<unk>``, no normalization, no whitespace stripping (RESEARCH Pitfall 6). The set deliberately
covers the cases that break naive char-level or normalizing tokenizers: leading/trailing-space
ASCII, smart punctuation, multi-codepoint emoji (ZWJ + regional-indicator flags), multi-byte
scripts, whitespace runs, digit+punctuation mixes, an EMBEDDED ``<|endoftext|>`` literal (which
must be byte-encoded verbatim, NOT treated as the special token in a raw round-trip), and the
empty + single-byte edge cases.

All consumers are CPU-only and GPU-free so CI runs them.
"""

# name -> id is not relevant here; this is a flat round-trip corpus.
TRICKY_STRINGS = [
    # --- empty + single byte (edge cases) ---
    "",
    "a",
    " ",
    "\n",
    # --- leading / trailing / internal-space ASCII ---
    " hello",
    "hello ",
    "  leading and trailing  ",
    "tab\tseparated\tvalues",
    "mixed   whitespace\n\t runs",
    # --- smart quotes, em-dash, ellipsis (Unicode punctuation) ---
    "“quoted” — with an em-dash…",
    "it’s a smart apostrophe",
    # --- ZWJ emoji + regional-indicator flag sequences (multi-codepoint) ---
    "family: \U0001f468‍\U0001f469‍\U0001f467‍\U0001f466",
    "flags: \U0001f1e7\U0001f1f7 \U0001f1fa\U0001f1f8 \U0001f1ef\U0001f1f5",
    "thumbs \U0001f44d and a heart ❤️",
    # --- multi-byte scripts ---
    "café naïve résumé",
    "greek omega Ω and pi π",
    "日本語 を 話します",
    "Привет, мир",
    # --- digits + punctuation mixes ---
    "price: $1,234.56 (≈ 2× more)",
    "v1.2.3-rc.4+build.567",
    # --- embedded special-token literal (must round-trip as raw bytes) ---
    "start<|endoftext|>end",
    "a<|endoftext|>b<|endoftext|>c",
]
