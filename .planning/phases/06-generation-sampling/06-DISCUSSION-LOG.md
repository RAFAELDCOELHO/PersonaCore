# Phase 6: Generation & Sampling - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-06
**Phase:** 6-generation-sampling
**Areas discussed:** I/O contract, Streaming interface

---

## Gray-area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Sampling composition | How greedy/temperature/top-k/top-p combine; greedy-as-flag vs temp=0; stacking; filter order | |
| I/O contract | ids→ids vs str→str; tokenizer inside vs outside | ✓ |
| Streaming interface | full-return vs generator yielding tokens; stream flag | ✓ |
| Batch support | single-sequence only vs batched with per-row EOS | |

**User's choice:** I/O contract, Streaming interface
**Notes:** Sampling composition and batch support left to Claude by convention.

---

## I/O contract

### Q1 — core signature (in/out)
| Option | Description | Selected |
|--------|-------------|----------|
| Token-level core (ids→ids) | Tokenizer stays outside; tests work on raw ids (nanoGPT idiom) | |
| Text-level (str→str) | Encode/decode inside; returns a string; couples to tokenizer | |
| Both: core + thin text wrapper | Token-level core is real fn; thin generate_text wrapper for demo | ✓ |

**User's choice:** Both: core + thin text wrapper

### Q2 — return value
| Option | Description | Selected |
|--------|-------------|----------|
| Prompt + new (full sequence) | Returns seed + generated (nanoGPT idiom, matches sample()) | |
| Only new tokens | Returns just the continuation | |
| You decide | Claude picks the cleanest convention | ✓ |

**User's choice:** You decide
**Notes:** Resolved as: token-level core returns full sequence (prompt + new); text wrapper strips
the prompt and returns only the decoded continuation.

### Q3 — prompt seeding
| Option | Description | Selected |
|--------|-------------|----------|
| Prepend EOS to the prompt | Encode as [eos_id] + tokens(prompt); empty prompt → [eos_id] free-run | ✓ |
| Encode prompt as-is | No EOS prepended; raw prompt tokens | |
| You decide | Claude picks based on training register | |

**User's choice:** Prepend EOS to the prompt

---

## Streaming interface

### Q1 — how streaming is exposed
| Option | Description | Selected |
|--------|-------------|----------|
| Generator core + collect helper | Core yields each new token id; helper collects full result | ✓ |
| stream=False flag | Full tensor by default; stream=True returns a generator | |
| Return-only core + separate stream fn | Core returns full seq; separate generate_stream() for demo | |

**User's choice:** Generator core + collect helper

### Q2 — EOS behavior while streaming
| Option | Description | Selected |
|--------|-------------|----------|
| Stop without yielding EOS | Halt on EOS, do not yield it (implements GEN-02 trailing-trim) | ✓ |
| Yield EOS, then stop | Emit EOS then stop; caller trims | |
| You decide | Claude picks cleanest for GEN-02 | |

**User's choice:** Stop without yielding EOS

### Q3 — streaming text granularity
| Option | Description | Selected |
|--------|-------------|----------|
| Decode running buffer, emit delta | Decode whole buffer each step, yield new suffix (no mojibake) | ✓ |
| Decode each token alone | Decode just the new token id; risks split multi-byte UTF-8 | |
| You decide | Claude picks the correct-text approach | |

**User's choice:** Decode running buffer, emit delta

---

## Claude's Discretion

- **Return value mechanics** (Q2 above) — full-sequence core + prompt-stripping text wrapper.
- **Sampling composition** — fold greedy/temperature/top-k/top-p into the core; suggested order
  temperature → top-k → top-p → sample; greedy = argmax path. Planner picks exact signature/defaults.
- **Batch support** — single-sequence is sufficient; batched generation not required for M1.
- **Determinism mechanism** — prefer an explicit torch.Generator/seed arg over global RNG for tests.
- **Module location** — new `generation/` package; thin scripts only if needed (no CLI).
- **Context-cropping mechanics** — crop to last block_size ids before each forward.

## Deferred Ideas

- Batched / multi-sequence generation with per-row EOS masking — only if a future use case needs it.
- KV-cache for CPU/MPS inference latency — Phase-8-conditional / Milestone 2.
- Rewiring the training-loop periodic sample hook to call generate() — out of scope (D-11 only
  requires generate() supersede sample()).
- Sampling presets / repetition penalty / min-length — not in GEN-01..03.
