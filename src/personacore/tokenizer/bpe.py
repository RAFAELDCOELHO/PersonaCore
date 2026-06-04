"""From-scratch byte-level BPE tokenizer (TOK-01 / TOK-02 / TOK-03).

Train merges from a bounded corpus and replay them deterministically (lowest-rank-first),
producing identical IDs across runs/sessions (TOK-01). Byte-level base-256 coverage guarantees
no ``<unk>`` ever and an exact ``decode(encode(x)) == x`` round-trip (TOK-02). Special tokens are
atomic — split FIRST, never byte-split or merged across (TOK-03 / RESEARCH Pattern 4 / Pitfall 3).

The from-scratch deliverable is the BPE ALGORITHM itself; ``regex`` is a pre-tok primitive on the
same footing as stdlib ``re`` (RESEARCH "Don't Hand-Roll"). The reference-oracle library is NEVER
imported here — the runtime tokenizer package stays oracle-free (T-02-04, enforced by the
no-runtime-oracle guard in ``test_tokenizer_oracle.py``).

Load-bearing invariants:
- D-04: byte-level base-256, no ``<unk>`` — every byte 0-255 is a leaf id.
- D-06: deterministic lowest-rank-first merge replay with a TOTAL tie-break (Pitfall 1).
- D-03: special tokens are atomic and reserved at the top of the vocab (8184-8191).
"""

import regex

from .patterns import _COMPILED, GPT2_SPLIT_PATTERN
from .special import EOS_ID, SPECIAL_TOKENS


def get_stats(ids, counts=None):
    """Count adjacent pairs across a token-id list (RESEARCH Pattern 2).

    Accepts an optional ``counts`` accumulator so the train loop can aggregate stats across
    every pre-tok chunk in one dict before selecting a merge.
    """
    counts = {} if counts is None else counts
    for pair in zip(ids, ids[1:]):
        counts[pair] = counts.get(pair, 0) + 1
    return counts


def merge(ids, pair, idx):
    """Replace every non-overlapping occurrence of ``pair`` in ``ids`` with ``idx``."""
    new_ids = []
    i = 0
    n = len(ids)
    while i < n:
        if i < n - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            new_ids.append(idx)
            i += 2
        else:
            new_ids.append(ids[i])
            i += 1
    return new_ids


class BPETokenizer:
    """Hand-rolled byte-level BPE: train / encode / decode (TOK-01/02/03).

    State mirrors the freeze/rebuild shape of ``checkpoint.py``: ``merges`` (the learned
    pair->id rank table), ``vocab`` (id->bytes for decode), ``pattern`` (the pre-tok regex
    string), ``special_tokens`` (atomic name->id map), ``eos_id`` and ``vocab_size``.
    """

    def __init__(self):
        # Defaults so a fresh tokenizer is trainable; train()/frozen() populate merges+vocab.
        self.pattern = GPT2_SPLIT_PATTERN
        self.special_tokens = dict(SPECIAL_TOKENS)
        self.eos_id = EOS_ID
        self.vocab_size = 0
        self.merges = {}  # (id, id) -> new_id, in rank (assignment) order.
        self.vocab = {idx: bytes([idx]) for idx in range(256)}  # base-256 leaves (D-04).

    # ---- pre-tokenization -------------------------------------------------------------

    def _split_chunks(self, text):
        """Lossless pre-tok split: ``"".join(chunks).encode() == text.encode()`` (Pitfall 6).

        Never strips or normalizes — the GPT-2 pattern partitions the string exactly.
        """
        return _COMPILED.findall(text)

    # ---- training ---------------------------------------------------------------------

    def train(self, text, vocab_size=8192):
        """Learn merges deterministically from ``text`` and return self (TOK-01, D-06).

        Bytes occupy 0-255 and specials are top-pinned at 8184+, so learned merge ids start at
        256 and never collide. The number of merges is ``vocab_size - 256 - len(specials)``.
        Pair selection uses a TOTAL tie-break ``(freq, pair)`` so two runs replay identically.
        """
        n_specials = len(self.special_tokens)
        num_merges = vocab_size - 256 - n_specials
        if num_merges < 0:
            raise ValueError(
                f"vocab_size={vocab_size} too small for 256 bytes + {n_specials} specials"
            )

        # Byte-encode each pre-tok chunk to a base-256 id list (D-04).
        chunks = [list(chunk.encode("utf-8")) for chunk in self._split_chunks(text)]

        merges = {}
        vocab = {idx: bytes([idx]) for idx in range(256)}

        for i in range(num_merges):
            stats = {}
            for chunk in chunks:
                get_stats(chunk, stats)
            if not stats:
                break  # corpus exhausted of mergeable pairs before reaching vocab_size.
            # TOTAL tie-break (Pitfall 1): most frequent, then largest pair-key — never bare get.
            pair = max(stats, key=lambda p: (stats[p], p))
            idx = 256 + i
            chunks = [merge(chunk, pair, idx) for chunk in chunks]
            merges[pair] = idx
            vocab[idx] = vocab[pair[0]] + vocab[pair[1]]

        self.merges = merges
        self.vocab = vocab
        self.vocab_size = vocab_size
        return self

    # ---- encoding ---------------------------------------------------------------------

    def _encode_chunk(self, text_bytes):
        """Lowest-rank-first merge replay over one chunk's bytes (D-06; RESEARCH Pattern 3)."""
        ids = list(text_bytes)
        while len(ids) >= 2:
            stats = get_stats(ids)
            # Pick the pair with the LOWEST merge rank present; stop when none are mergeable.
            pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
            if pair not in self.merges:
                break
            ids = merge(ids, pair, self.merges[pair])
        return ids

    def _encode_ordinary(self, text):
        """Encode text with NO special-token handling: pre-tok split then per-chunk replay."""
        ids = []
        for chunk in self._split_chunks(text):
            ids.extend(self._encode_chunk(chunk.encode("utf-8")))  # never strip/normalize.
        return ids

    def encode(self, text, allowed_special="all"):
        """Encode text, treating recognized special tokens as atomic ids (TOK-03, D-03).

        Splits FIRST on the special-token literals (longest-first to avoid prefix shadowing),
        emitting each special's reserved id atomically; ordinary spans go through byte-level BPE.
        ``allowed_special="all"`` recognizes every registered special; any other value disables
        special handling and encodes the whole string as ordinary bytes.
        """
        if allowed_special == "all" and self.special_tokens:
            specials = self.special_tokens
        else:
            specials = {}

        if not specials:
            return self._encode_ordinary(text)

        # Capturing alternation, longest-first (Pitfall 3): keeps the delimiters in the split.
        names = sorted(specials, key=len, reverse=True)
        pattern = "(" + "|".join(regex.escape(name) for name in names) + ")"
        ids = []
        for part in regex.split(pattern, text):
            if part == "":
                continue
            if part in specials:
                ids.append(specials[part])  # atomic special id — never byte-split.
            else:
                ids.extend(self._encode_ordinary(part))
        return ids

    # ---- decoding ---------------------------------------------------------------------

    def decode(self, ids):
        """Inverse of ``encode``: ids -> bytes -> text, with specials mapped to literals (D-04).

        Special ids resolve FIRST (they are the authoritative atomic ids — WR-02): a special id
        that collides with a merge/byte id must decode to its literal, never be shadowed by
        ``vocab``. Byte/merge ids then resolve via ``vocab``; an unknown id raises ``ValueError``.

        Decoding is strict UTF-8 (``errors="strict"``, the default — WR-03): byte-level coverage
        guarantees valid round-trips, so any non-round-trippable byte stream is a genuine defect
        and must raise ``UnicodeDecodeError`` rather than silently emit U+FFFD replacements.
        """
        inverse_special = {idx: name for name, idx in self.special_tokens.items()}
        parts = []
        for idx in ids:
            if idx in inverse_special:
                parts.append(inverse_special[idx].encode("utf-8"))
            elif idx in self.vocab:
                parts.append(self.vocab[idx])
            else:
                raise ValueError(f"unknown token id: {idx}")
        return b"".join(parts).decode("utf-8")

    # ---- freeze / rebuild -------------------------------------------------------------

    @classmethod
    def frozen(cls, *, pattern, merges, special_tokens, eos_id, vocab_size):
        """Rebuild a ready-to-use tokenizer from a freeze dict (mirrors ``load_checkpoint``).

        Reconstructs ``vocab`` from ``merges`` in rank order so ``decode`` works immediately.
        This is the constructor that ``io.from_json`` (Plan 03) calls.
        """
        tok = cls()
        tok.pattern = pattern
        tok.merges = dict(merges)
        tok.special_tokens = dict(special_tokens)
        tok.eos_id = eos_id
        tok.vocab_size = vocab_size
        vocab = {idx: bytes([idx]) for idx in range(256)}
        # Rebuild merge-id bytes in ascending rank so each pair's children already exist.
        for (p0, p1), idx in sorted(merges.items(), key=lambda kv: kv[1]):
            vocab[idx] = vocab[p0] + vocab[p1]
        # Layout invariant (WR-02): special ids must be disjoint from byte/merge ids so decode
        # can resolve them unambiguously — a collision would silently shadow the special.
        if not set(special_tokens.values()).isdisjoint(vocab):
            raise ValueError(
                "special token ids overlap byte/merge ids; the layout must keep them disjoint"
            )
        tok.vocab = vocab
        return tok
