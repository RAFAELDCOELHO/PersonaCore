# Phase 2: From-Scratch BPE Tokenizer - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

A correct, from-scratch **byte-level BPE tokenizer** that:
- trains merges from a corpus and replays them deterministically (lowest-rank-first), producing identical IDs across runs/sessions (TOK-01),
- `encode`/`decode` round-trips `decode(encode(x)) == x` over tricky strings with **no `<unk>` ever** (TOK-02),
- handles **atomic special tokens** with a single shared EOS id stored in config (TOK-03),
- **freezes to a serializable artifact** exposing a **locked `vocab_size`** ready to size the model (TOK-04),
- passes a **from-scratch-vs-reference equivalence test** using tiktoken/HF as a **test-only** oracle, never a runtime dependency (TOK-05).

**In scope:** the tokenizer module (train / encode / decode / save / load), the special-token registry, the locked `vocab_size`, and its tests.

**Out of scope (other phases):** model code and sizing (Phases 3–4 consume the locked `vocab_size`), the training loop (Phase 3), full-corpus encoding into a `uint16` memmap (Phase 5 / PRE-01), generation (Phase 6). LoRA/EWC and persona/chat role tokens are wired in Milestone 2 (slots reserved now — see D-02).

**Mode:** MVP (vertical slices) — `**Mode:** mvp` in ROADMAP. The planner should organize work as thin end-to-end slices (train merges → encode/decode round-trip → freeze/load artifact) rather than horizontal layers.

</domain>

<decisions>
## Implementation Decisions

### Vocabulary Size (THE lock)
- **D-01:** **`vocab_size = 8192`, locked.** This is the load-bearing Phase-2 deliverable — Phases 3–4 size the model around it (flex `n_embd`/`n_layer` to hit the ~10–15M param budget). Chosen because at ~10–15M params with weight tying, embedding cost = `vocab × n_embd` is shared with the output head; 8192 leaves the most room for transformer depth/width while being ample for TinyStories' simple vocabulary. **Update `ModelConfig.vocab_size` from the `50304` placeholder → `8192`** (`src/personacore/config.py`).
- **D-01a:** Accounting convention: **`8192 = 256 byte-base tokens + 8 special tokens + ~7928 BPE merges`.** Special tokens carve out of the 8192 — they do not sit on top of it.

### Special Tokens (atomic, reserved now)
- **D-02:** **Reserve a block of 8 special-token slots within the frozen 8192.** `<|endoftext|>` is the **single shared EOS id** and the only special token M1 actually uses. Reserve now (defined, but **dead/unused during M1 pretraining**): `<|user|>`, `<|assistant|>`, `<|system|>`, `<|pad|>`, plus **3 spares** (`<|reserved_0|>`, `<|reserved_1|>`, `<|reserved_2|>`). Rationale: special tokens added *after* pretraining change `vocab_size`, resize the embedding/output head, and invalidate the trained checkpoint — exactly what this phase's goal forbids. ~7 dead embedding rows during M1 is negligible; freezing `vocab_size` across M2 (LoRA/EWC persona work) is the payoff.
- **D-03:** Special tokens are **atomic** — never produced by merges, never split, and BPE must **not merge across them** (including not merging across the `<|endoftext|>` document separator; matches STACK.md). The **shared EOS id is stored in config** (satisfies TOK-03 and Phase-1 D-03: config travels inside the checkpoint).
- **D-03a:** The special-token **set and count (8) are locked here.** The exact id layout (e.g., specials immediately after the 256 byte tokens, or pinned at the top `8184–8191`) is the planner/researcher's call — but it must be fixed and documented in the frozen artifact, and the EOS id recorded in config.

### Pre-tokenization & Algorithm (Claude's discretion — user delegated)
- **D-04:** **Byte-level BPE** operating on UTF-8 bytes (base-256). Guarantees no `<unk>` ever (TOK-02) and exact round-trip on any input.
- **D-05:** Use the **GPT-2 pre-tokenization regex split pattern** (Karpathy `minbpe`-standard). Simpler and battle-tested, and it enables the cleanest algorithm-equivalence oracle (D-07). The GPT-4/cl100k pattern (digit grouping, broader Unicode categories) is more complex to reproduce exactly and not worth it at this scale.
- **D-06:** **Deterministic merge replay** — lowest-rank-first with deterministic tie-breaking → identical IDs across runs/sessions (TOK-01). Reuse Phase-1 `seeding`/determinism discipline in tests.

### Equivalence Test + BPE Training Corpus (Claude's discretion — user delegated)
- **D-07:** TOK-05 oracle = **algorithm-equivalence against tiktoken**. Feed GPT-2's published vocab+merges into the from-scratch encoder and assert it reproduces tiktoken's `gpt2` token IDs **exactly** on a string test set. This validates the *encoding algorithm* (regex pre-tok + byte-level + lowest-rank-first merge application) independent of our own trained merges. **tiktoken is a test-only `[dev]` dependency — never imported at runtime** (TOK-05). (HF `tokenizers` is an acceptable secondary oracle but tiktoken is the primary.)
- **D-08:** Separately, assert `decode(encode(x)) == x` over a **tricky-string set** (emoji, smart quotes, newlines, multi-byte UTF-8) on **our trained tokenizer** (TOK-02), plus determinism and atomic-EOS unit tests. All tests are **CPU-only**, consistent with Phase-1 CI.
- **D-09:** Phase 2 trains the production 8192-vocab tokenizer on a **bounded TinyStories sample** (e.g., the ~22 MB `TinyStoriesV2-GPT4` validation split, or a bounded slice of train) — sufficient for 8192 merges (BPE merge quality saturates well before this corpus size). One-time bounded fetch via the optional `requests` dep (single `resolve/main/...txt` GET) **or** a committed small fixture if fully offline. **Phase 5 reuses this FROZEN tokenizer as-is** to encode the full corpus — it does **not** retrain, keeping `vocab_size` and merges identical (checkpoint-safe). This is a deliberate, bounded exception to Phase-1 D-07 (which only forbade *Phase-1* data download); the full-corpus encode stays in Phase 5.

### Serialization (Claude's discretion — user delegated)
- **D-10:** The tokenizer freezes to a **single self-contained JSON artifact**: merges in rank order, special-tokens map (incl. the shared EOS id), `vocab_size = 8192`, the pre-tokenization pattern string, and a schema version. Human-readable, offline, portable across Kaggle/laptop. Loads into a frozen `Tokenizer` exposing `vocab_size`, `encode`, `decode`, and `eos_id` (satisfies TOK-04).

### Module Placement
- **D-11:** New `src/personacore/tokenizer/` package (train, encode/decode, save/load, special-token registry) + `tests/` (round-trip, determinism, atomic-EOS, reference-equivalence). Per Phase-1 D-11, this module dir is added by its own phase (no earlier stubs). Wire the locked `vocab_size = 8192` into `ModelConfig`.

### Claude's Discretion
Areas the user explicitly delegated: **pre-tokenization regex (D-04/D-05/D-06)** and **equivalence-test strategy + BPE training corpus (D-07/D-08/D-09)**, plus **serialization format (D-10)** and **exact special-token id layout (D-03a)**. Defaults above are research-grounded; the researcher/planner may refine *mechanics* but must preserve the locked values (`vocab_size=8192`, 8 special tokens, single shared EOS, byte-level, tiktoken test-only).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & goal
- `.planning/REQUIREMENTS.md` — TOK-01..TOK-05 (the acceptance text this phase must satisfy)
- `.planning/ROADMAP.md` §"Phase 2: From-Scratch BPE Tokenizer" — goal + 5 success criteria + `**Mode:** mvp`

### Tokenizer guidance (locked stack)
- `.planning/research/STACK.md` §"TL;DR Prescription" / §"TinyStories Data Tooling" / §"What NOT to Use" — byte-level BPE from scratch (pure Python/regex + dict merges); tiktoken/HF as **oracle-only**; treat `<|endoftext|>` as one special token and **do not merge across it**; `TinyStoriesV2-GPT4` corpus + direct `resolve/main/...txt` URLs

### Carried-forward Phase-1 decisions
- `.planning/phases/01-scaffolding-reproducible-environment/01-CONTEXT.md` — D-02 (`ModelConfig.vocab_size` is this phase's lock target), D-03 (config embedded in checkpoint = EOS id home), D-04 (no CLI/argparse — defaults/kwargs only), D-11 (module dir added by its own phase)
- `src/personacore/config.py` — `ModelConfig.vocab_size` placeholder `50304` → update to `8192`; reuse `seeding`/determinism utilities in tests

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/personacore/config.py` — `ModelConfig` already owns `vocab_size` (placeholder `50304`); this phase locks it to `8192`. The shared EOS id should live in config per Phase-1 D-03.
- `src/personacore/seeding.py` / determinism discipline — reuse for the deterministic-merge and round-trip tests.
- `pyproject.toml` — `[dev]` extra (owned by Plan 01-01) is where the **test-only** tiktoken oracle dependency is added; `[tool.ruff]`/`[tool.pytest.ini_options]` already configured.

### Established Patterns
- From-scratch ethos: pure Python + regex + dict merges; reference libraries (tiktoken/HF) appear **only** in tests.
- CPU-only test suite (Phase-1 CI) — all tokenizer tests must run without a GPU.
- Atomic commits + Makefile `lint`/`test` gate from Phase 1.

### Integration Points
- Locked `vocab_size = 8192` → flows into Phase 3/4 model sizing (`ModelConfig`).
- Frozen JSON tokenizer artifact → consumed unchanged by Phase 5 (PRE-01) to encode the full corpus into a `uint16` memmap.
- Reserved special-token slots → wired by Milestone 2 (persona/chat roles).

</code_context>

<specifics>
## Specific Ideas

- Karpathy `minbpe` as a **conceptual** reference for the from-scratch byte-level BPE (train/encode/decode), implemented by hand — not vendored.
- GPT-2 pre-tokenization regex as the split pattern (enables exact tiktoken `gpt2` algorithm-equivalence).
- Primary equivalence oracle: `tiktoken` `gpt2` encoding (test-only); HF `tokenizers` acceptable as a secondary check.

</specifics>

<deferred>
## Deferred Ideas

- **Persona/chat role tokens** (`<|user|>`, `<|assistant|>`, `<|system|>`, …) — **slots reserved now** (D-02) but activated in **Milestone 2**.
- **Full-corpus encode → `uint16` memmap** — **Phase 5 (PRE-01)**, reusing this frozen tokenizer (no retrain).
- **CLI for tokenizer training params** — deferred (Phase-1 D-04: no CLI layer; use defaults/kwargs).
- **GPT-4 / cl100k pre-tokenization pattern** — considered and not adopted (D-05); revisit only if a future corpus needs it.
- **`<|pad|>` activation for batched inference/eval** — slot reserved now, used when batched generation/eval needs it (Phase 6+).

None of these expanded Phase 2 scope — discussion stayed within the tokenizer boundary.

</deferred>

---

*Phase: 02-from-scratch-bpe-tokenizer*
*Context gathered: 2026-06-04*
