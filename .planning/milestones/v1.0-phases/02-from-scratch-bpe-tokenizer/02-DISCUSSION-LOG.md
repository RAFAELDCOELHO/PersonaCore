# Phase 2: From-Scratch BPE Tokenizer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 2-from-scratch-bpe-tokenizer
**Areas discussed:** Target vocab_size, Special-token reservation
**Areas delegated to Claude:** Pre-tokenization regex, Equivalence test + BPE corpus

---

## Area Selection

| Gray area | Selected for discussion |
|-----------|-------------------------|
| Target vocab_size | ✓ |
| Pre-tokenization regex | (delegated to Claude) |
| Special-token reservation | ✓ |
| Equivalence test + BPE corpus | (delegated to Claude) |

**User's choice:** Discuss "Target vocab_size" and "Special-token reservation"; resolve the other two with research-grounded defaults.

---

## Target vocab_size

| Option | Description | Selected |
|--------|-------------|----------|
| 8192 | Compact power-of-2; most room for transformer depth/width inside 10–15M params; ample for TinyStories. | ✓ |
| 16384 | Shorter sequences but ~2× embedding budget → thinner transformer. | |
| 4096 | Very compact embeddings, longer sequences, coarser merges. | |
| 32768 or 50304 | Best compression but embeddings dominate the param budget at this scale. | |

**User's choice:** 8192
**Notes:** Locks `ModelConfig.vocab_size` (placeholder `50304` → `8192`). Accounting: `8192 = 256 byte-base + 8 special + ~7928 merges`. Phases 3–4 flex `n_embd`/`n_layer` around it to hit ~10–15M params.

---

## Special-token reservation

| Option | Description | Selected |
|--------|-------------|----------|
| Reserve a small block | EOS now + ~7 reserved slots for M2 (`<|user|>`, `<|assistant|>`, `<|system|>`, `<|pad|>`, spares) — keeps `vocab_size` frozen across M2. | ✓ |
| EOS only, minimal | Just `<|endoftext|>`; risks a later vocab bump when M2 adds role tokens. | |
| EOS + pad only | EOS + `<|pad|>`; still risks a later bump for role markers. | |

**User's choice:** Reserve a small block
**Notes:** 8 special-token slots total within the frozen 8192. `<|endoftext|>` is the single shared EOS (the only one M1 uses); the other 7 are defined-but-dead during M1 pretraining and activated in M2. Prevents a post-training `vocab_size` change that would invalidate the trained checkpoint — the core promise of the phase goal.

---

## Claude's Discretion

- **Pre-tokenization regex / algorithm:** byte-level BPE on UTF-8 (base-256, no `<unk>`); GPT-2 split pattern (`minbpe`-standard); deterministic lowest-rank-first merge replay. (CONTEXT D-04/D-05/D-06)
- **Equivalence test + BPE corpus:** TOK-05 oracle = algorithm-equivalence vs tiktoken `gpt2` (test-only `[dev]` dep, never runtime); round-trip + determinism + atomic-EOS tests on the trained tokenizer; train the 8192-vocab tokenizer on a bounded TinyStories sample (one-time fetch or fixture), reused frozen by Phase 5. (CONTEXT D-07/D-08/D-09)
- **Serialization format:** single self-contained JSON artifact (merges + specials + vocab_size + pattern + schema version) → frozen `Tokenizer` exposing `vocab_size`/`encode`/`decode`/`eos_id`. (CONTEXT D-10)
- **Exact special-token id layout:** set and count (8) locked; precise id positions left to planner/researcher. (CONTEXT D-03a)

## Deferred Ideas

- Persona/chat role tokens — slots reserved now, activated in Milestone 2.
- Full-corpus encode → `uint16` memmap — Phase 5 (PRE-01), reusing the frozen tokenizer.
- CLI for tokenizer training params — deferred (Phase-1 D-04: no CLI).
- GPT-4 / cl100k pre-tokenization pattern — considered, not adopted.
- `<|pad|>` activation for batched inference/eval — slot reserved, used Phase 6+.
