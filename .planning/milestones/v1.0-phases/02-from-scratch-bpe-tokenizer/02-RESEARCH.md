# Phase 2: From-Scratch BPE Tokenizer - Research

**Researched:** 2026-06-04
**Domain:** Byte-level BPE tokenization (from scratch, pure Python), GPT-2 pre-tokenization, tiktoken algorithm-equivalence oracle, JSON artifact freeze
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (preserve — do NOT relitigate)
- **D-01:** `vocab_size = 8192`, locked. Update `ModelConfig.vocab_size` from `50304` → `8192` in `src/personacore/config.py`. Phases 3–4 size the model around it.
- **D-01a:** Accounting convention: `8192 = 256 byte-base tokens + 8 special tokens + ~7928 BPE merges`. Specials carve OUT of 8192 (not on top).
- **D-02:** Reserve a block of **8 special-token slots** within the frozen 8192. `<|endoftext|>` is the **single shared EOS id** and the only special token M1 uses. Reserve now (dead during M1): `<|user|>`, `<|assistant|>`, `<|system|>`, `<|pad|>`, `<|reserved_0|>`, `<|reserved_1|>`, `<|reserved_2|>`.
- **D-03:** Special tokens are **atomic** — never produced by merges, never split, BPE must NOT merge across them (including not across the `<|endoftext|>` document separator). EOS id stored in config.
- **D-03a:** Special-token set and count (8) are locked. Exact id layout is planner/researcher's call but must be fixed + documented in the frozen artifact, with EOS id recorded in config.
- **D-04:** Byte-level BPE on UTF-8 bytes (base-256). No `<unk>` ever; exact round-trip.
- **D-05:** GPT-2 pre-tokenization regex split pattern (Karpathy `minbpe`-standard). NOT the GPT-4/cl100k pattern.
- **D-06:** Deterministic merge replay — lowest-rank-first with deterministic tie-breaking → identical IDs across runs/sessions. Reuse Phase-1 `seeding`/determinism in tests.
- **D-07:** TOK-05 oracle = **algorithm-equivalence against tiktoken `gpt2`**. Feed GPT-2's published vocab+merges into the from-scratch encoder; assert it reproduces tiktoken's `gpt2` IDs exactly. **tiktoken is a test-only `[dev]` dependency — NEVER runtime-imported.** HF `tokenizers` is an acceptable secondary oracle.
- **D-08:** Separately assert `decode(encode(x)) == x` over a tricky-string set (emoji, smart quotes, newlines, multi-byte UTF-8) on OUR trained tokenizer, plus determinism + atomic-EOS unit tests. CPU-only.
- **D-09:** Train the production 8192-vocab tokenizer on a **bounded TinyStories sample** (~22 MB `TinyStoriesV2-GPT4` validation split, or bounded train slice). One-time bounded fetch via `requests` single GET **or** committed fixture if offline. **Phase 5 reuses this FROZEN tokenizer as-is** (no retrain).
- **D-10:** Freeze to a **single self-contained JSON artifact**: merges in rank order, special-tokens map (incl. EOS id), `vocab_size=8192`, pre-tok pattern string, schema version. Loads into a frozen `Tokenizer` exposing `vocab_size`, `encode`, `decode`, `eos_id`.
- **D-11:** New `src/personacore/tokenizer/` package + `tests/`. CPU-only tests. Module dir added by its own phase (no earlier stubs).

### Claude's Discretion (refine mechanics here)
- Exact GPT-2 pre-tok regex string + how to apply without merging across specials/`<|endoftext|>`.
- Lowest-rank-first merge application algorithm + deterministic tie-breaking.
- tiktoken `gpt2` oracle setup: obtaining GPT-2 merges/vocab, feeding into the from-scratch encoder for exact-ID equivalence.
- Exact special-token id layout (after byte tokens vs pinned at top).
- JSON artifact schema specifics and load/freeze mechanics.
- Bounded corpus fetch (`requests` GET) vs committed fixture.

### Deferred Ideas (OUT OF SCOPE)
- Persona/chat role tokens — slots reserved now, activated in Milestone 2.
- Full-corpus encode → `uint16` memmap — Phase 5 (PRE-01), reusing this frozen tokenizer.
- CLI for tokenizer training params — deferred (Phase-1 D-04: no CLI; defaults/kwargs only).
- GPT-4 / cl100k pre-tok pattern — considered, not adopted.
- `<|pad|>` activation for batched inference/eval — slot reserved, used Phase 6+.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TOK-01 | Byte-level BPE from scratch — train merges, deterministic lowest-rank-first replay | `get_stats`/`merge` training loop + `min(stats, key=merges.get)` encode loop (Architecture Patterns). Determinism via tie-break-by-pair on argmax + integer-keyed merges. |
| TOK-02 | `encode`/`decode` round-trip `decode(encode(x)) == x`, no `<unk>` | Byte-level base-256 guarantees no `<unk>`; `decode` joins `vocab[id]` bytes then `.decode("utf-8")`. Tricky-string fixture set defined in Validation Architecture. |
| TOK-03 | Atomic special tokens, single shared EOS id in config | Special-token splitting BEFORE byte-encoding (regex `(<\|endoftext\|>\|...)` split); EOS id added to `ModelConfig` / `RuntimeConfig` per Phase-1 D-03. |
| TOK-04 | Serializable save/load, locked `vocab_size` before model sizing | Single JSON artifact (schema below); `ModelConfig.vocab_size = 8192`. Frozen `Tokenizer.from_json()`. |
| TOK-05 | From-scratch-vs-reference equivalence (tiktoken/HF test-only oracle) | `recover_merges()` from tiktoken `gpt2` `mergeable_ranks` → feed into from-scratch encoder → assert exact ID match. tiktoken in `[dev]` extra only. |
</phase_requirements>

## Summary

This phase implements a byte-level BPE tokenizer from scratch in pure Python, conceptually modeled on Karpathy's `minbpe` `RegexTokenizer` but hand-written (not vendored). All five requirements decompose into three thin vertical slices appropriate to the `mvp` mode: (1) train merges from a bounded corpus + deterministic lowest-rank-first encode, (2) `decode(encode(x)) == x` round-trip with atomic special tokens, (3) freeze/load a JSON artifact exposing a locked `vocab_size=8192`. The tiktoken `gpt2` algorithm-equivalence oracle is a fourth, test-only slice that validates the *encoding algorithm* (regex split + byte-level + lowest-rank-first merge application) independently of our own trained merges.

The single most important technical fact: **the GPT-2 pre-tokenization regex requires the `regex` PyPI library, NOT Python's stdlib `re`.** `re` does not support the Unicode property escapes `\p{L}` and `\p{N}` used in the GPT-2 split pattern [VERIFIED: `python3.11 -c "import re; re.compile(r'\p{L}')"` raises]. The from-scratch ethos applies to the *BPE algorithm*, not the regex engine — `regex` is a pre-tokenization primitive (like a string `.split()`), comparable to using `re` itself, and is the standard choice in every reference implementation (minbpe, tiktoken's reference, HF). This means `regex` is a legitimate **runtime** dependency (it is the pre-tok engine), distinct from tiktoken which must remain test-only.

The second most important fact, specific to the TOK-05 oracle: **tiktoken's `gpt2` `mergeable_ranks` are keyed on raw bytes with NO byte permutation** — the byte-shuffle quirk is GPT-4/`cl100k`-only [VERIFIED: minbpe `gpt4.py` builds `byte_shuffle` only in `GPT4Tokenizer`, not for gpt2]. So the equivalence oracle uses minbpe's `recover_merges()` pattern directly with no shuffle. However, `tiktoken.get_encoding("gpt2")` **downloads `vocab.bpe` from Azure blob storage on first use** unless `TIKTOKEN_CACHE_DIR` is pre-seeded — a network call that will hang/fail in offline CI [VERIFIED: openai/tiktoken issues #58, #63, #301; dify PR #16895]. The oracle test must handle this (commit a cached blob fixture, or `pytest.skip` when offline + uncached). Treat the oracle as a `@pytest.mark.oracle` test that skips gracefully, not a hard CI gate, so CPU-only offline CI stays green.

**Primary recommendation:** Hand-write a `BPETokenizer` modeled on minbpe's `RegexTokenizer`, using `regex` (runtime dep) for the GPT-2 split pattern, integer-keyed `merges: dict[tuple[int,int], int]` for deterministic lowest-rank-first replay, special-token-first splitting for atomicity, and a versioned JSON freeze artifact. Add `regex` to core deps, `tiktoken` to `[dev]`. Lock `ModelConfig.vocab_size = 8192` and add `eos_id` to config. Make the tiktoken oracle a skip-on-offline test.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| BPE train (merge learning) | Library / pure-Python module (`tokenizer/train`) | — | Offline, CPU-only, one-time; produces the frozen artifact |
| encode / decode (runtime) | Library module (`tokenizer/`) | — | Imported by Phases 3/5/6; pure Python + `regex` only |
| Special-token registry + EOS id | Config (`config.py`) + tokenizer module | — | EOS id lives in config per Phase-1 D-03 (travels in checkpoint); registry layout lives in artifact |
| Frozen artifact (JSON) | Filesystem artifact + `tokenizer/save_load` | — | Self-contained, portable Kaggle↔laptop; consumed unchanged by Phase 5 |
| Equivalence oracle | Test tier (`tests/`, `[dev]` tiktoken) | — | tiktoken NEVER crosses into runtime; validates algorithm only |

## Standard Stack

### Core (runtime)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `regex` | `2026.5.9` (latest) | GPT-2 pre-tokenization split pattern (`\p{L}`, `\p{N}`) | **Required** — stdlib `re` cannot compile `\p{L}`. Used by minbpe, tiktoken reference, HF. It is a pre-tok *primitive*, not BPE logic — does not violate from-scratch ethos. |
| Python stdlib `json` | 3.11 | Freeze/load the artifact | Zero-dependency, human-readable, portable. D-10. |
| Python stdlib (`collections`, `typing`) | 3.11 | `get_stats` counting, type hints | From-scratch primitives. |

### Supporting (dev / test only)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tiktoken` | `0.13.0` (latest) | TOK-05 algorithm-equivalence oracle | **`[dev]` extra ONLY — never runtime-imported.** Source of GPT-2 `mergeable_ranks` for the oracle. |
| `pytest` | `~=9.0` (already pinned) | All tokenizer tests | Already in `[dev]`. CPU-only. |
| `requests` | `~=2.32` (optional) | One-time bounded TinyStories `.txt` GET (D-09) | Only if not committing a fixture. Already noted optional in STACK.md. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `regex` lib | stdlib `re` with `[^\W\d_]` workaround | `re` cannot express `\p{L}`/`\p{N}` Unicode categories correctly across all scripts; the workaround diverges from tiktoken/minbpe and breaks the equivalence oracle on multi-byte input. Not worth it — `regex` is tiny and standard. [ASSUMED: workaround fidelity] |
| tiktoken oracle | HF `tokenizers` GPT-2 oracle (secondary) | HF `tokenizers` is heavier and also needs the GPT-2 vocab files; tiktoken is the primary per D-07. Keep HF as an optional secondary check only. |
| `requests` corpus fetch | Committed small fixture | A committed ~few-hundred-KB fixture keeps CI fully offline with zero network. Recommended for the **CI/test** corpus; the **production 8192 train** can use the one-time bounded GET locally (then the artifact is committed). |
| JSON artifact | minbpe `.model` plaintext format | JSON is self-describing, schema-versioned, and trivially loadable everywhere (D-10). Plaintext `.model` is fine but less explicit; JSON chosen. |

**Installation (deltas to `pyproject.toml`):**
```toml
# [project] dependencies — ADD regex as a RUNTIME dep (pre-tok engine):
dependencies = [
  "numpy~=2.4",
  "regex~=2026.5",      # GPT-2 pre-tok \p{L}/\p{N}; stdlib re cannot do this
]

# [project.optional-dependencies] dev — ADD tiktoken (test-only oracle, NEVER runtime):
dev = ["pytest~=9.0", "ruff~=0.15", "tiktoken~=0.13"]
```
> Keep `requirements.txt` consistent (Phase-1 D-09): add `regex` there too.

**Version verification:**
- `regex` `2026.5.9` is the latest release [VERIFIED: `pip index versions regex`].
- `tiktoken` `0.13.0` is the latest release [VERIFIED: `pip index versions tiktoken`].
- stdlib `re` does NOT support `\p{L}` [VERIFIED: `re.compile(r"\p{L}")` raises `error: bad escape \p`].

## Package Legitimacy Audit

> slopcheck could not be installed in this environment (`pip install slopcheck` failed — externally-managed env). Per protocol, packages are version-verified against the correct registry (PyPI) instead, and the two non-trivial additions are well-known with massive download counts and official source repos. Both pre-date 2020. The planner SHOULD still gate the install behind the normal Makefile/CI run, but neither is a hallucination risk.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `regex` | PyPI | first release 2013 (`2026.5.9` latest) | ~80M+/mo | github.com/mrabarnett/mrab-regex | unavailable | Approved (version-verified) |
| `tiktoken` | PyPI | first release 2022 (`0.13.0` latest) | ~50M+/mo | github.com/openai/tiktoken | unavailable | Approved — `[dev]` only |
| `requests` | PyPI | 2011 (`2.32.x`) | ~500M+/mo | github.com/psf/requests | unavailable | Approved (optional) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck was unavailable; download counts/ages above are [ASSUMED] from training knowledge but registry existence + latest version are [VERIFIED] via `pip index versions`. The planner may add a `checkpoint:human-verify` before install if desired, but `regex`/`tiktoken`/`requests` are canonical, decade-old packages.*

## Architecture Patterns

### System Architecture Diagram

```
                          ┌──────────────────────────────────────────────┐
   bounded corpus  ──────▶│  TRAIN (offline, one-time)                    │
   (~22MB TinyStories     │  raw text                                     │
    val split or fixture) │    │                                          │
                          │    ▼  regex.findall(GPT2_SPLIT_PATTERN)        │
                          │  pre-token chunks                             │
                          │    │  (specials NOT present in train text,    │
                          │    │   or stripped first)                     │
                          │    ▼  chunk.encode("utf-8") → list[int 0..255]│
                          │  byte-id sequences per chunk                  │
                          │    │                                          │
                          │    ▼  loop: get_stats → argmax pair →         │
                          │           assign next id → merge in all chunks│
                          │  merges: {(int,int): int}  (rank = order)     │
                          └────────────────┬─────────────────────────────┘
                                           ▼
                          ┌──────────────────────────────────────────────┐
                          │  FREEZE  → tokenizer.json (schema v1)         │
                          │  {version, pattern, merges[rank-ordered],     │
                          │   special_tokens{name:id}, eos_id, vocab_size}│
                          └────────────────┬─────────────────────────────┘
                                           ▼
   runtime text ─────────▶┌──────────────────────────────────────────────┐
   (Phase 5 corpus,       │  Tokenizer.from_json()  (frozen, runtime)     │
    Phase 6 prompts)      │                                               │
                          │  ENCODE:                                      │
                          │    split on special-token regex (ATOMIC) ────┐│
                          │    ├─ special chunk  → emit special id  ◀─────┘│
                          │    └─ ordinary chunk → regex.findall →         │
                          │         bytes → _encode_chunk:                 │
                          │           while pairs: pair=min(stats,         │
                          │             key=merges.get(.,inf));            │
                          │             if not in merges: break;           │
                          │             merge(pair)                        │
                          │    → list[int] ids                            │
                          │                                               │
                          │  DECODE:                                      │
                          │    ids → b"".join(vocab[id]) → .decode(utf-8) │
                          │    (special ids → name.encode or skipped)     │
                          └───────────────────────────────────────────────┘

   ── test-only oracle (NEVER runtime) ──
   tiktoken.get_encoding("gpt2") ─▶ mergeable_ranks ─▶ recover_merges()
        ─▶ inject into from-scratch encoder ─▶ assert ids == tiktoken.encode(s)
```

### Recommended Project Structure
```
src/personacore/
└── tokenizer/
    ├── __init__.py         # exposes BPETokenizer, GPT2_SPLIT_PATTERN, SPECIAL_TOKENS, EOS_TOKEN
    ├── bpe.py              # BPETokenizer: train / encode / decode / _encode_chunk
    ├── patterns.py         # GPT2_SPLIT_PATTERN (the exact regex string) + compiled pattern
    ├── special.py          # special-token registry: ordered list, id layout, EOS name/id
    └── io.py               # save_json / from_json (schema v1, freeze/load)

scripts/
└── train_tokenizer.py      # thin entry: load bounded corpus, train 8192, freeze artifact (no CLI/argparse — D-04, defaults/kwargs)

artifacts/  (or data/tokenizer/)
└── tokenizer.json          # the FROZEN production artifact (committed; Phase 5 reuses)

tests/
├── fixtures/
│   ├── tricky_strings.py   # emoji, smart quotes, newlines, multi-byte UTF-8, mixed
│   └── tiny_corpus.txt     # small committed corpus for offline train tests
├── test_tokenizer_train.py     # determinism: train twice → identical merges/ids (TOK-01)
├── test_tokenizer_roundtrip.py # decode(encode(x))==x over tricky set, no <unk> (TOK-02)
├── test_tokenizer_special.py   # atomicity: EOS never split/merged-across; eos_id in config (TOK-03)
├── test_tokenizer_io.py        # save→load→identical behavior; vocab_size==8192 (TOK-04)
└── test_tokenizer_oracle.py    # tiktoken gpt2 algorithm-equivalence; skip-on-offline (TOK-05)
```
> `config.py` is modified (not in `tokenizer/`): `vocab_size 50304→8192`, add `eos_id`.

### Pattern 1: The exact GPT-2 split pattern (D-05)
**What:** The minbpe-standard GPT-2 pre-tokenization regex. Put it in `patterns.py` as a module constant.
**When to use:** Both train and encode, applied via `regex.findall` per ordinary (non-special) chunk.
```python
# Source: github.com/karpathy/minbpe/blob/master/minbpe/regex.py  [CITED]
import regex  # NOT stdlib re — \p{L}/\p{N} require the regex library

GPT2_SPLIT_PATTERN = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
_COMPILED = regex.compile(GPT2_SPLIT_PATTERN)
# chunks = _COMPILED.findall(text)
```
> The artifact stores this exact string under `"pattern"` so a reload reconstructs the identical splitter. [VERIFIED: minbpe regex.py + tiktoken gpt2 pat_str]

### Pattern 2: Training loop (lowest-rank assigned in frequency order) (TOK-01)
**What:** Repeatedly merge the most-frequent adjacent pair, assigning incrementing ids starting at 256 (or above the special block — see id-layout decision).
**Example:**
```python
# Source: github.com/karpathy/minbpe base.py (get_stats/merge) + RegexTokenizer.train  [CITED]
def get_stats(ids, counts=None):
    counts = {} if counts is None else counts
    for pair in zip(ids, ids[1:]):
        counts[pair] = counts.get(pair, 0) + 1
    return counts

def merge(ids, pair, idx):
    out, i = [], 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i+1] == pair[1]:
            out.append(idx); i += 2
        else:
            out.append(ids[i]); i += 1
    return out

# train: pre-split corpus into chunks of byte-ids, then per merge step:
#   stats = aggregate get_stats over all chunks
#   pair  = max(stats, key=stats.get)        # DETERMINISM LANDMINE — see Pitfall 1
#   idx   = next_id; merges[pair] = idx
#   chunks = [merge(c, pair, idx) for c in chunks]
```

### Pattern 3: Deterministic lowest-rank-first encode (TOK-01)
**What:** Apply learned merges in ascending rank order until no learned pair remains.
```python
# Source: github.com/karpathy/minbpe regex.py _encode_chunk  [CITED]
def _encode_chunk(self, text_bytes):
    ids = list(text_bytes)  # 0..255
    while len(ids) >= 2:
        stats = get_stats(ids)
        pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
        if pair not in self.merges:
            break
        ids = merge(ids, pair, self.merges[pair])
    return ids
```
> `min(..., merges.get(p, inf))` IS the lowest-rank-first replay; ties never matter here because rank is unique per pair. Determinism is bit-exact across runs/sessions given the same `merges` dict (TOK-01). [VERIFIED: minbpe]

### Pattern 4: Atomic special tokens — split FIRST (TOK-03 / D-03)
**What:** Before any byte-encoding, split the text on a regex alternation of escaped special-token strings. Special chunks emit their reserved id directly; ordinary chunks go through Pattern 1+3. This guarantees BPE never merges across `<|endoftext|>`.
```python
# Source: github.com/karpathy/minbpe regex.py encode() with allowed_special  [CITED]
import regex
def encode(self, text, allowed_special="all"):
    special = self._resolve_special(allowed_special)  # {name: id}
    if not special:
        return self._encode_ordinary(text)
    special_pat = "(" + "|".join(regex.escape(k) for k in special) + ")"
    ids = []
    for part in regex.split(special_pat, text):
        if part in special:
            ids.append(special[part])          # ATOMIC — single id, never split
        elif part:
            ids.extend(self._encode_ordinary(part))
    return ids
```
> `regex.split` with a **capturing** group keeps the delimiters in the output list. [VERIFIED: minbpe]

### Pattern 5: Decode (no `<unk>` possible) (TOK-02)
```python
# Source: github.com/karpathy/minbpe base.py _build_vocab + decode  [CITED]
def decode(self, ids):
    parts = []
    for idx in ids:
        if idx in self.vocab:           # byte-merge token → its bytes
            parts.append(self.vocab[idx])
        elif idx in self.inverse_special: # special id → its literal text bytes (or skip)
            parts.append(self.inverse_special[idx].encode("utf-8"))
        else:
            raise ValueError(f"invalid id {idx}")
    return b"".join(parts).decode("utf-8", errors="replace")
```
> `vocab = {0..255: single byte} ∪ {merge-id: concatenated bytes}`. Because every input byte maps to a base token, `decode(encode(x)) == x` holds for any UTF-8 string — no `<unk>` token exists. (Use `errors="replace"` only as a safety net; round-trip tests assert exact equality, so it never triggers on valid input.) [VERIFIED: minbpe]

### Pattern 6: tiktoken `gpt2` equivalence oracle (TOK-05, test-only)
**What:** Recover GPT-2's merge order from tiktoken's `mergeable_ranks`, inject into a from-scratch encoder configured with the GPT-2 pattern, assert exact ID match. **No byte-shuffle for gpt2** (that's a GPT-4-only quirk).
```python
# Source: github.com/karpathy/minbpe gpt4.py recover_merges/bpe  [CITED]
# tests/test_tokenizer_oracle.py
def bpe(mergeable_ranks, token, max_rank):
    parts = [bytes([b]) for b in token]
    while True:
        min_idx = min_rank = None
        for i, pair in enumerate(zip(parts[:-1], parts[1:])):
            rank = mergeable_ranks.get(pair[0] + pair[1])
            if rank is not None and (min_rank is None or rank < min_rank):
                min_idx, min_rank = i, rank
        if min_rank is None or (max_rank is not None and min_rank >= max_rank):
            break
        parts = parts[:min_idx] + [parts[min_idx] + parts[min_idx+1]] + parts[min_idx+2:]
    return parts

def recover_merges(mergeable_ranks):
    merges = {}
    for token, rank in mergeable_ranks.items():
        if len(token) == 1:
            continue
        p0, p1 = bpe(mergeable_ranks, token, max_rank=rank)
        merges[(mergeable_ranks[p0], mergeable_ranks[p1])] = rank
    return merges
# Then build a from-scratch encoder whose .merges == recover_merges(enc._mergeable_ranks)
# and whose vocab ids == raw byte rank (NO byte_shuffle for gpt2), and assert
# our_encoder.encode(s) == enc.encode_ordinary(s) for s in oracle strings.
```
> tiktoken `gpt2` `mergeable_ranks` are keyed on **raw bytes**; the byte permutation only exists for GPT-4/`cl100k`. So the oracle needs NO `byte_shuffle`. [VERIFIED: minbpe gpt4.py builds byte_shuffle only in GPT4Tokenizer; WebSearch corroborated]

### Anti-Patterns to Avoid
- **Using stdlib `re` for the GPT-2 pattern:** `\p{L}` fails to compile. Must use `regex`.
- **Encoding specials by passing them through BPE:** would merge/split them. Always split-first (Pattern 4).
- **Picking the merge pair with a non-deterministic `max`:** `max(stats, key=stats.get)` over a dict whose key insertion order varies between runs can break tie determinism — see Pitfall 1.
- **`tiktoken.get_encoding("gpt2")` in CI without a cached blob:** triggers a network download → CI hang/failure. Skip-on-offline (Pitfall 2).
- **Importing tiktoken anywhere under `src/`:** violates TOK-05 (runtime-free). Enforce with a guard test (Pitfall 4).
- **Letting BPE merge across `<|endoftext|>`:** breaks document boundaries Phase 5 relies on; split-first prevents it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Unicode-category pre-tok split (`\p{L}`, `\p{N}`) | A custom Unicode-category classifier | `regex` library | Reproducing Unicode general-category tables by hand is enormous, error-prone, and diverges from tiktoken → breaks the oracle. `regex` is the de-facto primitive. |
| GPT-2 merge ranks for the oracle | Re-deriving GPT-2's BPE from `vocab.bpe`+`encoder.json` by hand | tiktoken `mergeable_ranks` + minbpe `recover_merges` | tiktoken already ships the authoritative ranks; `recover_merges` is ~15 lines. Hand-parsing `encoder.json`'s byte-to-unicode mapping is a known footgun. |
| JSON freeze | Custom binary serialization | stdlib `json` | Human-readable, portable, schema-versionable, zero deps (D-10). |
| UTF-8 byte handling | Custom byte↔char logic | Python `str.encode("utf-8")` / `bytes.decode("utf-8")` | Native, correct for all code points incl. emoji/surrogates. |

**Key insight:** The from-scratch deliverable is the **BPE algorithm** (train merges, lowest-rank replay, atomic specials), not the regex engine or UTF-8 codec. `regex` and `str.encode` are primitives on the same footing as `re` and `list` — using them is expected, not a violation. The line is bright: tiktoken/HF model code may NOT implement our tokenizer, but `regex` MAY be our pre-tok splitter.

## Common Pitfalls

### Pitfall 1: Non-deterministic merge selection during training
**What goes wrong:** Two training runs on the same corpus produce *different* merge orders → different IDs → TOK-01 fails.
**Why it happens:** `max(stats, key=stats.get)` returns the *first* max in dict-iteration order. If multiple pairs tie on frequency, the chosen one depends on insertion order, which can vary if the corpus is loaded/aggregated differently. Also `dict` ordering is insertion-ordered in 3.7+, so it's usually stable, but ties are silent landmines.
**How to avoid:** Make tie-breaking explicit and total: `pair = max(stats, key=lambda p: (stats[p], _neg_pair_key(p)))` or sort pairs deterministically before argmax. Run the determinism test (train twice, assert identical `merges`). Reuse Phase-1 `seed_everything` in tests though training itself is deterministic given a fixed corpus + tie-break.
**Warning signs:** `test_tokenizer_train.py` passes locally but flakes in CI; merge dict differs by a few late-rank entries.

### Pitfall 2: tiktoken `get_encoding("gpt2")` requires network (breaks offline CI)
**What goes wrong:** The oracle test hangs ~60s then fails in offline CI; or fails on a laptop with no internet. [VERIFIED: openai/tiktoken #58, #63, #301]
**Why it happens:** `tiktoken` downloads `vocab.bpe`/`encoder.json` from `openaipublic.blob.core.windows.net` on first `get_encoding("gpt2")` unless cached.
**How to avoid (pick one):**
  1. **Skip-on-offline:** wrap the oracle in `try: enc = tiktoken.get_encoding("gpt2") except Exception: pytest.skip("tiktoken gpt2 unavailable offline")`. CPU-only offline CI stays green; the oracle runs wherever network/cache exists.
  2. **Pre-seed cache:** commit the gpt2 blob and set `TIKTOKEN_CACHE_DIR` to a repo path in the test (fully offline, but commits a ~1MB binary). The blob cache filename is a sha1 hash of the blob URL.
**Recommendation:** Option 1 (skip-on-offline) for CI green-by-default; document that the oracle MUST be run at least once with network (locally or a network-enabled CI job) before the phase is marked verified. This keeps Phase-1's CPU-only-offline CI contract intact.
**Warning signs:** CI job named "oracle" hangs; `make test` slow on first run.

### Pitfall 3: Special-token ordering in the regex split
**What goes wrong:** If two special tokens are prefixes of each other (not the case here, but defensive), or if the longest match isn't preferred, splitting mis-segments. Also, `regex.split` without a capturing group drops the delimiters entirely.
**Why it happens:** Alternation matches left-to-right; capturing group is required to keep delimiters.
**How to avoid:** Sort special strings by descending length before joining the alternation; always use a **capturing** group `"(" + "|".join(...) + ")"`. Our 8 special tokens share no prefix, so this is mostly a correctness guardrail.
**Warning signs:** EOS appears as separate byte tokens in encode output; round-trip drops `<|endoftext|>`.

### Pitfall 4: tiktoken leaking into the runtime import surface
**What goes wrong:** A stray `import tiktoken` in `src/personacore/tokenizer/` makes the runtime depend on a `[dev]` package → import fails on Kaggle/clean install; violates TOK-05.
**Why it happens:** Copy-pasting oracle helper code into the module instead of tests.
**How to avoid:** Add a guard test that asserts `tiktoken` is NOT importable-as-a-dependency of the package — e.g. scan `src/personacore/**/*.py` for `tiktoken` / `import tiktoken`, or assert `importlib.metadata` core deps exclude it. Keep all oracle code under `tests/`.
**Warning signs:** `pip install -e .` (no extras) then `import personacore.tokenizer` raises `ModuleNotFoundError: tiktoken`.

### Pitfall 5: Special-token id layout vs merge id range collision
**What goes wrong:** If specials are placed "immediately after 256 byte tokens" (ids 256–263) AND training also assigns merge ids starting at 256, they collide.
**Why it happens:** Two id allocators using the same base.
**How to avoid — RECOMMENDED LAYOUT:** Pin specials at the **top** of the vocab: ids `8184–8191` (the last 8 of 8192), with `<|endoftext|>` as a fixed, documented slot (e.g. `8184`). Byte tokens occupy `0–255`; BPE merges occupy `256–8183` (≈7928 merges). This cleanly separates the three id ranges, makes `eos_id` a stable constant, and matches D-01a's accounting. Record the full `{name: id}` map and `eos_id` in both the artifact and config. [ASSUMED: top-pinned is cleaner than after-bytes; either is valid per D-03a — planner decides, but this avoids the collision class entirely]
**Warning signs:** A trained merge id equals a special id; decode confuses a merge token for a special.

### Pitfall 6: `regex.findall` and whitespace chunk reassembly
**What goes wrong:** The GPT-2 pattern's `\s+(?!\S)|\s+` alternation preserves leading spaces *inside* chunks (e.g. `" world"`). If you `.strip()` or normalize, round-trip breaks.
**Why it happens:** Byte-level BPE relies on leading-space being part of the token; mutating chunks loses bytes.
**How to avoid:** Never normalize/strip chunks. Concatenated chunk bytes MUST equal `text.encode("utf-8")` — assert this invariant in a test.
**Warning signs:** Round-trip drops/adds spaces; `"".join(chunks) != text`.

## Code Examples

### JSON freeze artifact (schema v1) — D-10 / TOK-04
```python
# src/personacore/tokenizer/io.py
import json

SCHEMA_VERSION = 1

def save_json(tok, path):
    payload = {
        "schema_version": SCHEMA_VERSION,
        "pattern": tok.pattern,                       # exact GPT2_SPLIT_PATTERN string
        "vocab_size": tok.vocab_size,                 # 8192 (locked)
        "special_tokens": tok.special_tokens,         # {"<|endoftext|>": 8184, ...}
        "eos_id": tok.eos_id,                         # 8184
        # merges serialized in RANK ORDER; tuple keys → list-of-lists (JSON has no tuple keys)
        "merges": [[p0, p1, idx] for (p0, p1), idx in
                   sorted(tok.merges.items(), key=lambda kv: kv[1])],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=0)

def from_json(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    assert d["schema_version"] == SCHEMA_VERSION, "tokenizer schema mismatch"
    merges = {(p0, p1): idx for p0, p1, idx in d["merges"]}
    return BPETokenizer.frozen(
        pattern=d["pattern"], merges=merges,
        special_tokens=d["special_tokens"], eos_id=d["eos_id"],
        vocab_size=d["vocab_size"],
    )
```
> JSON has no tuple keys → serialize merges as `[p0, p1, idx]` triples in rank order. `ensure_ascii=True` keeps the artifact pure-ASCII and diff-friendly (all merge tokens are integer ids, not raw bytes, so no encoding issue). [ASSUMED: schema shape — satisfies D-10's required fields]

### config.py deltas — D-01 / TOK-03
```python
# src/personacore/config.py  (MODIFY ModelConfig)
@dataclass
class ModelConfig:
    vocab_size: int = 8192          # LOCKED by Phase 2 (was 50304 placeholder)
    eos_id: int = 8184              # shared EOS id, recorded in checkpoint (Phase-1 D-03)
    block_size: int = 256
    n_layer: int = 6
    n_head: int = 6
    n_embd: int = 384
    dropout: float = 0.0
```
> EOS id in config satisfies TOK-03 + Phase-1 D-03 (config travels in the checkpoint). The existing `test_config.py` must be updated to assert `vocab_size == 8192`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| char-level / word-level tokenization | byte-level BPE (no `<unk>`) | GPT-2 (2019) | Guarantees round-trip on any input; the project's chosen approach |
| stdlib `re` for pre-tok | `regex` lib (`\p{L}`/`\p{N}`) | GPT-2 reference onward | Required for correct Unicode pre-tok; stdlib `re` insufficient |
| hand-parse GPT-2 `encoder.json` | tiktoken `mergeable_ranks` + `recover_merges` | tiktoken (2022) | Oracle is ~15 lines instead of fragile byte-unicode parsing |

**Deprecated/outdated:**
- Using the GPT-2 byte-to-unicode "visible char" mapping (the `bytes_to_unicode()` trick from the original GPT-2 repo) as the *implementation*: unnecessary with tiktoken raw-byte ranks; only relevant if hand-parsing `vocab.bpe`. Avoid — use tiktoken ranks for the oracle and raw bytes for our tokenizer.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Top-pinned special id layout (`8184–8191`, EOS=`8184`) is cleaner than after-bytes | Pitfall 5 / config delta | Low — D-03a delegates layout; either works. If after-bytes chosen, just offset merge ids to start at 264. |
| A2 | JSON schema shape (fields/triple-encoded merges) satisfies D-10 | Code Examples | Low — all D-10-required fields present; planner may rename keys. |
| A3 | `regex` lib counts as an allowed runtime primitive (not a from-scratch violation) | Standard Stack | Medium — if a reviewer insists on zero non-stdlib runtime deps, fall back to a documented `re` workaround that diverges from the oracle. Recommend confirming with user that `regex` is acceptable (it's analogous to `re`). |
| A4 | Committed fixture corpus for CI + one-time GET for production train (D-09) | Validation Architecture | Low — D-09 explicitly permits either; this split keeps CI offline. |
| A5 | Oracle as skip-on-offline rather than committed-blob | Pitfall 2 / Validation | Medium — if the user wants the oracle to ALWAYS run in CI, commit the ~1MB gpt2 blob + set `TIKTOKEN_CACHE_DIR`. Default (skip) preserves Phase-1's offline-CI contract. |
| A6 | regex `~2026.5`, tiktoken `~0.13` version pins | Standard Stack | Low — latest verified via `pip index versions`; pins are conservative compatible-release ranges. |
| A7 | regex/tiktoken download counts & ages | Package Legitimacy Audit | Low — registry existence + latest version VERIFIED; popularity is well-known but slopcheck was unavailable. |

## Open Questions (RESOLVED)

> All three resolved during /gsd:plan-phase (user decision + CONTEXT.md locks). Recorded here for traceability; plans implement these resolutions.

1. **Is `regex` (the PyPI library) acceptable as a runtime dependency under the from-scratch ethos?** — **RESOLVED: APPROVED as a core runtime dependency** (user decision, 2026-06-04). `regex` is a low-level pre-tokenization text primitive analogous to stdlib `re` (needed for the GPT-2 split pattern's `\p{L}`/`\p{N}` escapes), distinct from BPE logic and from `tiktoken` (which stays strictly `[dev]`/test-only). The CLAUDE.md stack note "pure Python/regex + dict merges" covers it.
   - Original context: every reference impl uses it; stdlib `re` cannot do `\p{L}`. The `re`-with-`[^\W\d_]` fallback was the rejected alternative.

2. **Should the tiktoken oracle be skip-on-offline or commit the gpt2 blob?** — **RESOLVED: skip-on-offline by default**; the equivalence is confirmed at least once with network/seeded `TIKTOKEN_CACHE_DIR` as a phase-gate manual verification (see VALIDATION.md). Keeps Phase-1 CPU-only-offline CI green.

3. **Exact special-token id layout (after-bytes vs top-pinned).** — **RESOLVED: top-pinned** (`8184–8191`, EOS=`8184`; merges `256–8183`; bytes `0–255`) to avoid the merge/special id-collision class and give a stable `eos_id` constant. D-03a delegated this.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | All tests (Kaggle parity) | ✓ | 3.11.15 | none (mandatory per CLAUDE.md) |
| `regex` | runtime pre-tok | ✗ (not yet installed) | `2026.5.9` on PyPI | none — must add to deps |
| `tiktoken` | TOK-05 oracle (`[dev]`) | ✗ (not yet installed) | `0.13.0` on PyPI | HF `tokenizers` (secondary) or skip oracle |
| stdlib `re` | (NOT usable for `\p{L}`) | ✓ | 3.11 | — (insufficient; use `regex`) |
| network (tiktoken gpt2 blob) | one-time oracle data | ✗ assumed offline in CI | — | skip-on-offline OR commit cached blob |

**Missing dependencies with no fallback:**
- `regex` — must be added to core deps before encode/decode works (no viable stdlib substitute for `\p{L}`).

**Missing dependencies with fallback:**
- `tiktoken` — oracle skips gracefully when absent/offline; HF `tokenizers` is an acceptable secondary oracle.
- network — oracle skip-on-offline preserves CI green.

## Validation Architecture

> `workflow.nyquist_validation: true` in config.json — section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `~=9.0` (already pinned in `[dev]`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) — exists |
| Quick run command | `python3.11 -m pytest tests/test_tokenizer_roundtrip.py tests/test_tokenizer_special.py -x` |
| Full suite command | `make test` (= `pytest` over all of `tests/`, CPU-only) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TOK-01 | Train twice → identical merges & ids (determinism, lowest-rank replay) | unit | `pytest tests/test_tokenizer_train.py -x` | ❌ Wave 0 |
| TOK-02 | `decode(encode(x))==x` over tricky set; no `<unk>`; `"".join(chunks)==text` | unit | `pytest tests/test_tokenizer_roundtrip.py -x` | ❌ Wave 0 |
| TOK-03 | EOS atomic (never split/merged-across); `eos_id` present in `ModelConfig` | unit | `pytest tests/test_tokenizer_special.py -x` | ❌ Wave 0 |
| TOK-04 | save→load→identical encode/decode; `vocab_size==8192`; schema version asserted | unit | `pytest tests/test_tokenizer_io.py -x` | ❌ Wave 0 |
| TOK-05 | from-scratch == tiktoken `gpt2` on oracle strings; tiktoken not in runtime | unit (skip-on-offline) | `pytest tests/test_tokenizer_oracle.py -x` | ❌ Wave 0 |
| D-01 | `ModelConfig.vocab_size == 8192` (updated from 50304) | unit | `pytest tests/test_config.py -x` | ✅ (update existing) |
| Pitfall 4 | no `tiktoken` import under `src/` | unit (guard) | `pytest tests/test_tokenizer_oracle.py::test_no_runtime_tiktoken -x` | ❌ Wave 0 |

### Tricky-string fixture set (TOK-02 — `tests/fixtures/tricky_strings.py`)
Minimum cases, each must round-trip exactly:
- ASCII with leading spaces: `"Hello world"`, `" leading"`, `"trailing "`
- Smart quotes / typographic: `"“curly” ‘quotes’ — em-dash …"`
- Emoji (multi-codepoint, ZWJ): `"👍🏽 👨‍👩‍👧‍👦 🇧🇷"`
- Multi-byte UTF-8 scripts: `"café naïve Ω 日本語 Привет"`
- Newlines/tabs/whitespace runs: `"a\n\nb\t c   d\r\n"`
- Mixed digits + punctuation (GPT-2 number handling): `"price: $1,234.56 (≈ 2× more)"`
- The EOS literal embedded in text: `"start<|endoftext|>end"` (must produce a single EOS id, not byte-split)
- Empty string and single byte: `""`, `"a"`

### Sampling Rate
- **Per task commit:** quick run (roundtrip + special) — < 5s, no network.
- **Per wave merge:** `make test` full suite — CPU-only, oracle skips if offline.
- **Phase gate:** full suite green AND the oracle run at least once with network/cache (documented evidence), before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/fixtures/tricky_strings.py` — the round-trip corpus (TOK-02)
- [ ] `tests/fixtures/tiny_corpus.txt` — small committed corpus for offline train tests (TOK-01)
- [ ] `tests/test_tokenizer_train.py` — determinism + lowest-rank replay (TOK-01)
- [ ] `tests/test_tokenizer_roundtrip.py` — round-trip + chunk-join invariant (TOK-02)
- [ ] `tests/test_tokenizer_special.py` — EOS atomicity + config `eos_id` (TOK-03)
- [ ] `tests/test_tokenizer_io.py` — freeze/load + `vocab_size==8192` (TOK-04)
- [ ] `tests/test_tokenizer_oracle.py` — tiktoken equivalence (skip-on-offline) + no-runtime-tiktoken guard (TOK-05, Pitfall 4)
- [ ] Update `tests/test_config.py` — assert `vocab_size==8192`, `eos_id` present
- [ ] Dependency install: `regex` (core), `tiktoken` (`[dev]`) — add to `pyproject.toml` + `requirements.txt`

## Security Domain

> `security_enforcement` not present in config.json. Tokenizer phase processes only local text/corpus and writes a local JSON artifact — minimal surface. Key controls below.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Validate `schema_version` on `from_json`; reject merge ids outside `[0, vocab_size)`; never `eval`/`exec` artifact contents. |
| V6 Cryptography | no | — |
| V12/V14 Supply chain | yes | `tiktoken` test-only; `regex` is a decade-old canonical package (version-pinned). Avoid `pip install --pre` / unverified mirrors. |

### Known Threat Patterns for {pure-Python tokenizer}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Untrusted artifact deserialization (arbitrary code) | Tampering / Elevation | Use `json` (data-only) — NEVER `pickle`/`torch.load` for the tokenizer artifact. JSON cannot execute code. |
| Oracle fetch over network (MITM / unavailability) | Tampering / DoS | tiktoken blob over HTTPS; skip-on-offline avoids hard network dependency; optionally pin a committed cached blob. |
| Malformed/oversized corpus | DoS | Bounded corpus (D-09); training is one-time offline, not user-facing. |

## Sources

### Primary (HIGH confidence)
- github.com/karpathy/minbpe — `regex.py` (GPT2_SPLIT_PATTERN, encode/encode_ordinary, special-token split), `base.py` (`get_stats`, `merge`, `_build_vocab`, save/load format), `gpt4.py` (`recover_merges`, `bpe`, byte_shuffle = GPT-4-only). [CITED]
- `pip index versions regex` → `2026.5.9` latest; `pip index versions tiktoken` → `0.13.0` latest. [VERIFIED]
- `python3.11 -c "import re; re.compile(r'\p{L}')"` → raises (stdlib `re` cannot do Unicode property escapes). [VERIFIED]
- Local repo: `pyproject.toml`, `src/personacore/config.py`, `src/personacore/seeding.py`, `tests/conftest.py` — current state of deps, config, determinism utilities. [VERIFIED: codebase grep/read]

### Secondary (MEDIUM confidence)
- openai/tiktoken issues #58, #63, #301 + langgenius/dify PR #16895 — `get_encoding("gpt2")` downloads `vocab.bpe` from Azure blob; `TIKTOKEN_CACHE_DIR` enables offline. [CITED: github.com/openai/tiktoken]
- WebSearch — tiktoken `gpt2` `mergeable_ranks` keyed on raw bytes; byte permutation is GPT-4-only; GPT-2 whitespace stays unmerged. Corroborated by minbpe gpt4.py code. [VERIFIED cross-source]

### Tertiary (LOW confidence)
- regex/tiktoken monthly download counts (Package Legitimacy Audit) — training-knowledge ballpark, not session-verified (slopcheck unavailable). [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified on PyPI; `regex` requirement proven by failed `re.compile`.
- Architecture/patterns: HIGH — quoted directly from minbpe source (the conceptual reference per CONTEXT D-specifics).
- Pitfalls: HIGH — determinism, offline-tiktoken, and runtime-leak pitfalls each cross-verified (code + issues + local probes).
- Oracle mechanics: HIGH — `recover_merges` quoted; no-byte-shuffle-for-gpt2 verified against minbpe.

**Research date:** 2026-06-04
**Valid until:** 2026-07-04 (stable domain; BPE algorithm and minbpe reference are static. Re-check tiktoken/regex pins if bumping.)
