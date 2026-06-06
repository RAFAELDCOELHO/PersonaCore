# Phase 6: Generation & Sampling - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the **single shared `generate()`** that powers all three downstream consumers — the
GEN-03 unit tests, the Phase-7 evaluation/qualitative samples, and the Phase-8 Gradio chat demo.
It performs autoregressive decoding over the trained `best.pt` GPT (`6/6/384`, `block_size=256`,
`vocab_size=8192`, `eos_id=8184`) using the locked `forward(idx, targets=None) -> (logits, loss)`
contract, with the full sampling toolkit (greedy / temperature / top-k / top-p), correct EOS
stopping, max-length handling, and context cropping to the last `block_size` tokens. It
**supersedes** the minimal `sample()` free function that currently lives in `training/loop.py`
(D-11) — without touching the training loop.

**Mode:** MVP (vertical slice) — the deliverable is one correct, well-shaped generation function
plus its unit tests (GEN-01, GEN-02, GEN-03), not new model architecture.

**In scope (GEN-01..03):**
- One shared `generate()` supporting greedy, temperature, top-k, and top-p sampling.
- EOS-aware stopping, trailing-token trim, max-length, and context cropping to the last
  `block_size` tokens (generating past `block_size` must never crash — the `forward` assert
  `T <= block_size` forces a crop).
- Generation unit tests: output shape, determinism under fixed seed + greedy decoding, EOS-stop.
- A token-level generator core + a thin text wrapper (the API shape decided below).

**Out of scope (other phases / locked):**
- Perplexity, curated sample capture, ablation table → Phase 7 (EVAL-01..03).
- The Gradio UI itself + slim fp32 inference checkpoint → Phase 8 (DEMO-01..03). This phase only
  delivers the streaming-capable `generate()` the demo will call.
- KV-cache / inference latency optimization → deferred (Phase-8-conditional / Milestone 2).
- Any change to the trained model, tokenizer, training loop, or checkpoint format.
- LoRA / EWC / personalization → Milestone 2.

</domain>

<decisions>
## Implementation Decisions

### I/O Contract (discussed)
- **D-01 — Token-level core + thin text wrapper.** The real function is token-level
  (`ids -> ids`): `generate(model, idx, ...)` takes a `LongTensor` of token ids and works in id
  space, keeping GEN-03 tests tokenizer-free (shape/determinism on raw ids, nanoGPT idiom). A
  separate **thin text wrapper** (`str -> str`) encodes/decodes around the core for the Phase-8
  demo. Two clearly-separated surfaces, one shared decoding implementation.
- **D-02 — Core returns the full sequence (prompt + new).** The token-level path yields/returns
  the seed ids concatenated with generated ids (matches the existing `sample()` idiom). The
  **text wrapper strips the prompt** and returns only the decoded continuation (cleanest for chat
  and tests). *(User said "you decide" — recorded as Claude's discretion, resolved this way.)*
- **D-03 — Text wrapper prepends EOS to the prompt.** The model was trained with documents
  separated by `eos_id=8184`, and the periodic training sampler seeds with `[eos_id]` as a
  start-of-document marker. The wrapper encodes a prompt as `[eos_id] + tokens(prompt)` so the
  model sees the clean start-of-document boundary it was trained on (better-conditioned starts).
  An **empty prompt falls back to just `[eos_id]`** (free-running story) — same seed the training
  sample hook uses.

### Streaming Interface (discussed)
- **D-04 — Generator core + collect helper.** The token-level core is a **Python generator that
  yields each new token id** one step at a time. A thin **collect helper** consumes it to build
  the full-sequence tensor that GEN-03 shape/determinism tests assert on. One code path; streaming
  is free; no second implementation to keep in sync (supersedes the return-only `sample()`).
- **D-05 — Stop on EOS without yielding it.** When the core generates `eos_id`, it halts and does
  **not** yield the EOS token. This naturally implements GEN-02's "trim the trailing token": the
  collected sequence (and any streamed text) ends at the last real token; the demo never sees the
  raw separator. (Max-length / `max_new_tokens` is the other stop condition.)
- **D-06 — Text streaming via running-buffer delta.** The streaming text wrapper accumulates all
  ids generated so far, **decodes the whole running buffer each step, and yields the new suffix**
  versus what was already emitted. This avoids broken multi-byte UTF-8 / partial-token glyphs
  (mojibake) that per-token decoding would cause with byte-level BPE (emoji, smart quotes, etc.).

### Claude's Discretion (planner may refine mechanics, honor intent)
- **Sampling composition** (not selected for discussion — decide by convention): fold greedy /
  temperature / top-k / top-p into the one core. Suggested standard semantics — greedy = `argmax`
  (e.g. `temperature == 0` or a `do_sample=False`/`top_k=1` path); apply `temperature` scaling
  first, then **top-k, then top-p (nucleus)** filtering on the last-position logits, then sample.
  top-k and top-p may stack. Planner to pick the exact signature/defaults; keep it nanoGPT-simple.
- **Batch support** (not selected — decide by convention): **single-sequence generation is
  sufficient** for the tests, eval, and demo. Batched generation with per-row EOS handling is NOT
  required; only add it if it falls out for free. Keep the API simple.
- **Determinism mechanism** (GEN-03): greedy must be exactly reproducible (`argmax`). For sampled
  determinism, prefer an explicit `torch.Generator` / seed argument over relying on global RNG so
  tests stay isolated; planner's discretion on the exact form. Must run on CPU (tests are
  GPU/MPS-free).
- **Module location:** a new `generation/` package (per the planned project structure) with the
  core + wrappers; thin `scripts/` entry only if needed (no CLI/argparse — Phase-1 D-04).
- **Context cropping mechanics:** crop `idx` to its last `block_size` tokens before each `forward`
  (the `forward` `assert T <= block_size` makes this mandatory) — planner's discretion on exact form.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & goal
- `.planning/REQUIREMENTS.md` — **GEN-01, GEN-02, GEN-03** (the acceptance text this phase
  satisfies).
- `.planning/ROADMAP.md` §"Phase 6: Generation & Sampling" — goal + 3 success criteria.

### Reusable code (read before writing generate())
- `src/personacore/training/loop.py` — the **minimal `sample()` free function** (≈ lines 106-117)
  that `generate()` supersedes (D-11): greedy-with-temperature multinomial on the last-position
  logits, NO top-k/top-p/EOS-stop. Generate() must replace its role WITHOUT changing the training
  loop. The periodic sample hook (≈ lines 375-380) shows the `[eos_id]` seed + `tokenizer.decode`
  pattern the text wrapper mirrors (D-03).
- `src/personacore/model/gpt.py` — the trained model. **`forward(idx, targets=None) -> (logits,
  loss)`** locked contract; `forward` asserts `T <= block_size` (≈ line 190), which forces
  context cropping in `generate()`. Logits shape `(B, T, vocab_size)`; sample from `logits[:, -1, :]`.
- `src/personacore/checkpoint.py` — `load_checkpoint` (open-dict, `weights_only=False` for the
  trusted resume file). How `best.pt` is loaded for generation.
- `src/personacore/config.py` — `ModelConfig` (`block_size=256`, `vocab_size=8192`,
  `eos_id=8184`) and `RuntimeConfig` (device/precision; generation must work on CPU and MPS).
- `src/personacore/tokenizer/` (`bpe.py`, `io.py`) — frozen tokenizer load + `.encode`/`.decode`;
  the text wrapper (D-01/D-03/D-06) uses `artifacts/tokenizer.json` unchanged (never retrain).
- `checkpoints/best.pt` — the trained model (val_loss 0.7378, ppl 2.091) that generation consumes.

### Carried-forward decisions
- `.planning/phases/05-tinystories-pretraining/05-CONTEXT.md` — `best.pt` is the canonical model;
  fluency register; the `[eos_id]`-seeded sample hook that motivates D-03.
- `.planning/phases/02-from-scratch-bpe-tokenizer/02-CONTEXT.md` — `vocab_size=8192`/`eos_id=8184`
  locked; `artifacts/tokenizer.json` frozen, reused with no retrain; `decode` is strict (no `<unk>`).
- `.planning/phases/01-scaffolding-reproducible-environment/01-CONTEXT.md` — no CLI/argparse (thin
  scripts), `RuntimeConfig` single device source, CPU-only GPU-free test suite.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `training/loop.py::sample(model, idx, max_new_tokens, temperature)` — the seed of `generate()`;
  greedy-with-temperature multinomial on `logits[:, -1, :]`. Generate() generalizes it with top-k,
  top-p, EOS-stop, context cropping, and the generator/streaming shape — then becomes the function
  the loop's periodic sample hook *could* call later (not required to rewire this phase).
- `model/gpt.py::GPT.forward` — `(logits, loss)` contract; pass `targets=None` to get logits only.
- Frozen tokenizer (`artifacts/tokenizer.json`) — `.encode`/`.decode` for the text wrapper.

### Established Patterns
- **Locked `forward(idx, targets=None) -> (logits, loss)`** across bigram + GPT — generate()
  calls `model(idx)` and reads `logits[:, -1, :]`. Never bypass this contract.
- **`forward` asserts `T <= block_size`** — context cropping to the last `block_size` ids is
  mandatory, not optional.
- **CPU-only, GPU/MPS-free test suite** — GEN-03 tests must run on CPU; use a tiny model/config or
  fixture, not `best.pt`, for shape/determinism/EOS-stop tests.
- **`uint16` storage, `int64` at use time** — generation works in `int64` (LongTensor) id space.
- **No CLI/argparse; thin `scripts/`; `RuntimeConfig` as the single device source.**
- **Strict tokenizer decode (no `<unk>`)** — the running-buffer streaming decode (D-06) is safe
  because decode round-trips byte-level BPE; per-token decode is what risks mojibake.

### Integration Points
- `generate()` core ← consumed by GEN-03 tests (collect helper → full sequence) and Phase-7 eval
  (perplexity uses `forward` directly; qualitative samples call generate()).
- text wrapper (streaming, running-buffer delta) ← consumed by the Phase-8 Gradio `ChatInterface`.
- Loads `best.pt` via `checkpoint.load_checkpoint`; runs under `RuntimeConfig` device (CPU/MPS).

</code_context>

<specifics>
## Specific Ideas

- **One function, three consumers** — the user's framing is a *single shared* `generate()`, not
  per-consumer copies. The generator-core + collect-helper + text-wrapper layering (D-01/D-04)
  exists precisely to keep one decoding implementation behind those three call sites.
- **Trained register matters for the demo** — prepend-EOS seeding (D-03) deliberately matches how
  the model saw document starts during TinyStories pretraining, so demo generations start in the
  right register rather than mid-document.
- **No raw separator ever shown** — D-05 (stop-without-yielding-EOS) + D-06 (running-buffer delta)
  together guarantee the demo streams clean text with no `<|endoftext|>` artifact and no mojibake.

</specifics>

<deferred>
## Deferred Ideas

- **Batched / multi-sequence generation** with per-row EOS masking — not needed for M1 tests, eval,
  or the single-user demo. Single-sequence is sufficient (Claude's-discretion note above). Revisit
  only if a future use case needs it.
- **KV-cache for CPU/MPS inference latency** — Phase-8-conditional / Milestone 2 (already deferred
  in Phase 5). The KV-cache-vs-scope tension is resolved on *measured* CPU latency at Phase-8
  planning, not here.
- **Rewiring the training loop's periodic sample hook to call `generate()`** — possible cleanup
  (one decoding path everywhere) but out of scope; D-11 only requires that generate() *supersede*
  `sample()`, not that the loop be rewired this phase.
- **Sampling presets / repetition penalty / min-length** — not in GEN-01..03; out of scope unless
  a later phase needs them.

</deferred>

---

*Phase: 06-generation-sampling*
*Context gathered: 2026-06-06*
