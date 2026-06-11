# Phase 6: Generation & Sampling - Research

**Researched:** 2026-06-06
**Domain:** Autoregressive decoding for a from-scratch nanoGPT-style GPT decoder (PyTorch, CPU/MPS)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 — Token-level core + thin text wrapper.** The real function is token-level (`ids -> ids`):
  `generate(model, idx, ...)` takes a `LongTensor` of token ids and works in id space, keeping
  GEN-03 tests tokenizer-free. A separate **thin text wrapper** (`str -> str`) encodes/decodes
  around the core for the Phase-8 demo. Two clearly-separated surfaces, one shared decoding impl.
- **D-02 — Core returns the full sequence (prompt + new).** The token-level path yields/returns the
  seed ids concatenated with generated ids (matches existing `sample()`). The **text wrapper strips
  the prompt** and returns only the decoded continuation. *(Claude's discretion, resolved this way.)*
- **D-03 — Text wrapper prepends EOS to the prompt.** Model trained with documents separated by
  `eos_id=8184`; periodic training sampler seeds with `[eos_id]`. The wrapper encodes a prompt as
  `[eos_id] + tokens(prompt)`. An **empty prompt falls back to just `[eos_id]`** (free-running story).
- **D-04 — Generator core + collect helper.** The token-level core is a **Python generator that
  yields each new token id** one step at a time. A thin **collect helper** consumes it to build the
  full-sequence tensor GEN-03 asserts on. One code path; streaming is free.
- **D-05 — Stop on EOS without yielding it.** When the core generates `eos_id`, it halts and does
  **not** yield the EOS token. This implements GEN-02's "trim the trailing token". (Max-length /
  `max_new_tokens` is the other stop condition.)
- **D-06 — Text streaming via running-buffer delta.** The streaming text wrapper accumulates all ids
  so far, **decodes the whole running buffer each step, and yields the new suffix** versus what was
  already emitted. Avoids broken multi-byte UTF-8 / partial-token mojibake with byte-level BPE.

### Claude's Discretion
- **Sampling composition:** fold greedy / temperature / top-k / top-p into one core. Suggested:
  greedy = `argmax` (e.g. `temperature == 0` or a `do_sample=False`/`top_k==1` path); apply
  `temperature` scaling first, then **top-k, then top-p (nucleus)** on last-position logits, then
  sample. top-k and top-p may stack. Planner picks exact signature/defaults; keep it nanoGPT-simple.
- **Batch support:** single-sequence generation is sufficient. Batched per-row EOS NOT required;
  only add if it falls out for free. Keep the API simple.
- **Determinism mechanism (GEN-03):** greedy must be exactly reproducible (`argmax`). For sampled
  determinism, prefer an explicit `torch.Generator` / seed argument over global RNG so tests stay
  isolated. Must run on CPU (tests are GPU/MPS-free).
- **Module location:** a new `generation/` package with the core + wrappers; thin `scripts/` entry
  only if needed (no CLI/argparse — Phase-1 D-04).
- **Context cropping mechanics:** crop `idx` to its last `block_size` tokens before each `forward`
  (the `forward` `assert T <= block_size` makes this mandatory) — planner's discretion on exact form.

### Deferred Ideas (OUT OF SCOPE)
- **Batched / multi-sequence generation** with per-row EOS masking — single-sequence is sufficient.
- **KV-cache for CPU/MPS inference latency** — Phase-8-conditional / Milestone 2.
- **Rewiring the training loop's periodic sample hook to call `generate()`** — out of scope; D-11
  only requires generate() *supersede* `sample()`, not that the loop be rewired this phase.
- **Sampling presets / repetition penalty / min-length** — not in GEN-01..03; out of scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEN-01 | A single shared `generate()` supporting greedy, temperature, top-k, and top-p sampling | Sampling composition section (temperature → top-k → top-p → sample); nanoGPT idiom verified; greedy folded as `argmax`/`top_k==1`/`temperature==0`. |
| GEN-02 | EOS-aware stopping and max-length handling | EOS-stop semantics section (D-05: halt-without-yield) + `max_new_tokens` loop bound + context cropping (so generating past `block_size` never crashes). |
| GEN-03 | Generation unit tests (shape, determinism under fixed seed/greedy, EOS stop) | Determinism section (`torch.Generator` for sampled, `argmax` for greedy); tiny-model CPU fixture pattern matching `test_gpt_model.py`; collect-helper produces the asserted full-sequence tensor. |
</phase_requirements>

## Summary

Phase 6 builds one token-level autoregressive `generate()` over the already-trained `best.pt` GPT
(`6/6/384`, `block_size=256`, `vocab_size=8192`, `eos_id=8184`). The mechanics are a solved,
well-documented nanoGPT pattern: crop context to the last `block_size` tokens, call the locked
`forward(idx) -> (logits, loss)`, take `logits[:, -1, :]`, scale by temperature, filter with top-k
then top-p, softmax, and `torch.multinomial`-sample (or `argmax` for greedy). All of this is a thin
loop on top of contracts that already exist in the repo — **no model, tokenizer, checkpoint, or
training-loop changes are needed**, which is exactly the scope fence in CONTEXT.md.

The one non-trivial design decision (already locked by D-04) is making the core a **Python generator
that yields one new token id per step**, with a **collect helper** that materializes the full-sequence
`LongTensor` the GEN-03 tests assert on. This gives streaming for free and keeps a single decode path.
EOS handling (D-05) is elegant: the generator simply stops *without* yielding `eos_id`, which
simultaneously satisfies "stop on EOS" and "trim the trailing token" — the demo never sees the raw
separator. The text wrapper (D-01/D-03/D-06) prepends `[eos_id]` to match the trained document-start
register, strips the prompt on return, and uses a **running-buffer delta decode** to avoid mojibake
from partial multi-byte UTF-8 sequences under byte-level BPE.

Determinism for GEN-03 is the only correctness subtlety: greedy is exactly reproducible via `argmax`
(no RNG), and sampled determinism should use an explicit `torch.Generator` passed to
`torch.multinomial(..., generator=g)` rather than the global RNG, so tests stay isolated and don't
perturb the global stream. Everything runs CPU-only on a tiny fixture model (never `best.pt`).

**Primary recommendation:** Implement a `personacore/generation/` package with a single
`@torch.no_grad()` generator-core (`generate(model, idx, ...)` yielding token ids), a `collect()`
helper returning the full-sequence tensor, and a `TextGenerator`/`generate_text` wrapper. Fold
greedy/temperature/top-k/top-p into the core exactly as nanoGPT does (verified verbatim below),
extended with top-p and EOS-stop. Use `torch.Generator` for seeded sampling. Build GEN-03 tests on a
tiny CPU `GPT(ModelConfig(...))` fixture, mirroring `tests/test_gpt_model.py` idioms.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Autoregressive token loop, sampling, EOS-stop, context crop | `generation/` core (id space) | — | Pure tensor/id logic; tokenizer-free so GEN-03 tests stay tokenizer-independent (D-01). |
| Full-sequence tensor assembly for tests/eval | `generation/` collect helper | core (consumes the generator) | Tests assert on a concatenated `LongTensor`; helper drains the generator into prompt+new (D-02/D-04). |
| encode/decode, EOS-prepend, prompt strip, streaming delta | `generation/` text wrapper | tokenizer (`io.from_json`, `bpe.encode/decode`) | Text concerns live only at the wrapper boundary; the core never touches text (D-01/D-03/D-06). |
| Device resolution (CPU/MPS) | `RuntimeConfig` (existing) | — | Single device source of truth (Phase-1 invariant); generation must run on CPU and MPS. |
| Loading the trained model | `checkpoint.load_checkpoint` (existing) | `config.ModelConfig` (embedded in ckpt) | Reuse the open-dict loader; `best.pt` carries its own `model_config`. No new loader. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyTorch (`torch`) | 2.7.1 (installed, verified) | Tensors, `softmax`, `topk`, `multinomial`, `argmax`, `Generator`, `no_grad` | Already the project's sole DL framework; every primitive needed is stdlib torch. `[VERIFIED: .venv torch 2.7.1]` |

No new dependencies. `torch` already present; `pytest` 8.x already the test runner. The tokenizer
(`personacore.tokenizer`) and model (`personacore.model.GPT`) are in-repo. `[VERIFIED: codebase]`

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x (in use) | GEN-03 unit tests (shape, determinism, EOS-stop) | The whole test deliverable. CPU-only, GPU-free. `[VERIFIED: codebase tests/]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Generator-core + collect helper (D-04) | Return-only loop (current `sample()`) | Return-only is simpler but gives no streaming, forcing a second impl for the Phase-8 demo. D-04 keeps ONE decode path. Locked — do not reconsider. |
| `torch.Generator` for seeded sampling | Global `torch.manual_seed` | Global seeding leaks into other tests / the wider RNG stream; `Generator` keeps GEN-03 isolated. Recommended (Claude's discretion, D in CONTEXT). |
| top-p via cumulative-softmax sort | top-k only (nanoGPT ships only top-k) | GEN-01 explicitly requires top-p, so it must be added. Standard implementation below. |

**Installation:** None — no packages to install. `[VERIFIED: codebase]`

## Package Legitimacy Audit

> Not applicable — Phase 6 installs **no external packages**. All code builds on `torch` (already
> installed and verified at 2.7.1) and the in-repo `personacore` package. No registry lookups, no
> slopcheck run needed. `[VERIFIED: codebase — no new deps]`

## Architecture Patterns

### System Architecture Diagram

```
                         ┌──────────────────────────────────────────────┐
                         │              generation/ package               │
                         │                                                │
  ids (LongTensor)  ───▶ │  generate(model, idx, *, max_new_tokens,       │
  (prompt+context)       │           temperature, top_k, top_p, eos_id,   │
                         │           generator) -> yields token id        │
                         │     ┌──────────── per-step loop ─────────────┐ │
                         │     │ 1. crop idx -> idx[:, -block_size:]      │ │
                         │     │ 2. logits,_ = model(idx_cond)            │ │
                         │     │ 3. logits = logits[:, -1, :]             │ │
                         │     │ 4. greedy? argmax : (temp→topk→topp→     │ │
                         │     │    softmax→multinomial(generator=g))     │ │
                         │     │ 5. next_id == eos_id ? STOP (no yield)   │ │
                         │     │ 6. else: append, yield next_id           │ │
                         │     └──────────────────────────────────────────┘ │
                         │            │                         │            │
                         │            ▼                         ▼            │
                         │   collect(model, idx, ...)   (streaming consumer) │
                         │   -> full-seq LongTensor              │           │
                         └───────────┼───────────────────────────┼──────────┘
                                     │                           │
              ┌──────────────────────┘                           │
              ▼                                                   ▼
   GEN-03 tests / Phase-7 eval                    TextGenerator / generate_text (str->str)
   (assert shape, determinism, EOS)               [eos_id]+encode(prompt) -> core
                                                  running-buffer decode -> yield new suffix
                                                  strip prompt -> return continuation
                                                              │
                                                              ▼
                                                   Phase-8 Gradio ChatInterface
```

Data flow: token ids enter the core, are cropped, fed through the locked `forward`, filtered/sampled,
and emitted one at a time. Two consumers sit downstream: a `collect()` drain (tests + eval) and the
text wrapper (demo). The model is loaded once via `checkpoint.load_checkpoint`; device comes from
`RuntimeConfig`.

### Recommended Project Structure

```
src/personacore/generation/
├── __init__.py        # barrel: re-export generate, collect, generate_text / TextGenerator
├── sampling.py        # pure logits transforms: apply_temperature, top_k_filter, top_p_filter
│                       #   (separately unit-testable; keeps core readable)
├── core.py            # generate(...) generator + collect(...) helper (id space; tokenizer-free)
└── text.py            # text wrapper: EOS-prepend, prompt-strip, running-buffer streaming decode
```

Matches the existing per-concern package layout (`tokenizer/`, `model/`, `training/` each a package
with an `__init__.py` barrel). No `scripts/` entry is needed for GEN-01..03; generation is a library
consumed by tests/eval/demo, not a CLI. `[CITED: CLAUDE.md project structure; CONTEXT.md D-04 module location]`

### Pattern 1: nanoGPT generation core (verified verbatim)
**What:** The canonical autoregressive loop. Crop → forward → last-logit → temp → top-k → softmax →
multinomial → concat. PersonaCore extends it with top-p, the generator/yield shape, and EOS-stop.
**When to use:** The core decoding loop.
**Verified reference (nanoGPT `model.py::generate`):**
```python
# Source: github.com/karpathy/nanoGPT/blob/master/model.py  [VERIFIED: WebFetch raw source 2026-06-06]
@torch.no_grad()
def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
    for _ in range(max_new_tokens):
        idx_cond = idx if idx.size(1) <= self.config.block_size else idx[:, -self.config.block_size:]
        logits, _ = self(idx_cond)
        logits = logits[:, -1, :] / temperature
        if top_k is not None:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[:, [-1]]] = -float('Inf')
        probs = F.softmax(logits, dim=-1)
        idx_next = torch.multinomial(probs, num_samples=1)
        idx = torch.cat((idx, idx_next), dim=1)
    return idx
```
**PersonaCore adaptation (note the differences):**
- It is a **free function** `generate(model, idx, ...)` (not a method on `GPT` — the GPT class
  deliberately ships no `generate`, per `gpt.py` module docstring), calling `model(idx_cond)`.
- It is a **generator** that `yield`s `idx_next.item()` (D-04), not a return-the-tensor loop.
- Add **top-p filtering after top-k** and a **greedy branch** (see Pattern 2/3).
- On `next_id == eos_id`: `return` (stop) **before** appending/yielding (D-05).
- Pass `generator=g` into `torch.multinomial` for seeded determinism (GEN-03).
`[VERIFIED: nanoGPT source + CITED: src/personacore/model/gpt.py:188-204 forward contract]`

### Pattern 2: Sampling composition order
**What:** temperature → top-k → top-p → sample. greedy short-circuits the whole filter stack.
**When to use:** Every step's logit-to-id decision.
**Example:**
```python
# Source: composition follows CONTEXT.md Claude's-discretion note + HF/nanoGPT convention. [CITED: CONTEXT.md D-block]
def next_token(logits_last, *, temperature, top_k, top_p, greedy, generator):
    # logits_last: (1, vocab) — single sequence (no batch, per scope fence).
    if greedy:                                   # greedy = argmax, fully deterministic, no RNG
        return torch.argmax(logits_last, dim=-1, keepdim=True)
    logits = logits_last / max(temperature, 1e-8)   # temperature FIRST (guard /0; or treat temp==0 as greedy)
    if top_k is not None:
        logits = top_k_filter(logits, top_k)        # then top-k
    if top_p is not None:
        logits = top_p_filter(logits, top_p)        # then top-p (nucleus)
    probs = torch.softmax(logits, dim=-1)
    return torch.multinomial(probs, num_samples=1, generator=generator)
```
**Greedy folding (planner picks one, all equivalent):** `temperature == 0` ⇒ greedy; or an explicit
`do_sample=False`; or `top_k == 1` (degenerate). Recommend a single explicit `greedy: bool` (or
`temperature == 0.0`) path — clearest and avoids a `temperature/0` division. `[CITED: CONTEXT.md]`

### Pattern 3: top-k filter (verified) and top-p filter (standard)
**top-k (verbatim nanoGPT idiom):**
```python
# Source: nanoGPT model.py [VERIFIED]
def top_k_filter(logits, k):
    k = min(k, logits.size(-1))
    v, _ = torch.topk(logits, k)
    logits = logits.clone()
    logits[logits < v[:, [-1]]] = float("-inf")   # keep top-k, mask the rest to -inf
    return logits
```
**top-p / nucleus (standard sort-cumsum mask):**
```python
# Source: standard HF/community nucleus-sampling idiom (top_p). [ASSUMED — algorithm is textbook;
#   verify off-by-one keep-first-token behavior against a unit test, see GEN-03 map].
def top_p_filter(logits, p):
    sorted_logits, sorted_idx = torch.sort(logits, descending=True, dim=-1)
    cum_probs = torch.softmax(sorted_logits, dim=-1).cumsum(dim=-1)
    # mask tokens once cumulative prob has EXCEEDED p, but always keep the first (highest) token
    sorted_mask = cum_probs > p
    sorted_mask[..., 1:] = sorted_mask[..., :-1].clone()  # shift right -> keep the boundary token
    sorted_mask[..., 0] = False                            # never mask the top-1 token
    mask = sorted_mask.scatter(-1, sorted_idx, sorted_mask)
    return logits.masked_fill(mask, float("-inf"))
```
**Note:** top-k and top-p **stack** (apply both if both set). Filtering with `-inf` before softmax is
the standard mask — softmax sends `-inf` to 0 probability cleanly. `[VERIFIED: top-k] [ASSUMED: top-p mechanics — pin with a test]`

### Pattern 4: Context cropping (mandatory)
**What:** Before each forward, crop `idx` to the last `block_size` tokens. The `GPT.forward` assert
`T <= block_size` (gpt.py:190) makes this **not optional** — without it, generating past 256 tokens
crashes. This is GEN-02 success-criterion 2 ("generating past `block_size` never crashes").
```python
# Source: nanoGPT idiom + src/personacore/model/gpt.py:190 assert  [VERIFIED]
idx_cond = idx if idx.size(1) <= block_size else idx[:, -block_size:]
```
`block_size` comes from the model's `ModelConfig` (256). Read it from the loaded config, not a magic
number. `[CITED: gpt.py:190, config.py:88]`

### Pattern 5: Generator core + collect helper (D-04)
```python
@torch.no_grad()
def generate(model, idx, *, max_new_tokens, eos_id, temperature=1.0,
             top_k=None, top_p=None, greedy=False, generator=None, block_size=None):
    """Yield each NEW token id one step at a time (D-04). Stops on eos_id WITHOUT yielding it (D-05),
    or after max_new_tokens."""
    bs = block_size or model.config.block_size
    for _ in range(max_new_tokens):
        idx_cond = idx if idx.size(1) <= bs else idx[:, -bs:]
        logits, _ = model(idx_cond)
        next_id = next_token(logits[:, -1, :], temperature=temperature, top_k=top_k,
                             top_p=top_p, greedy=greedy, generator=generator)
        tok = int(next_id)
        if tok == eos_id:        # D-05: stop, do NOT yield EOS -> trailing token trimmed (GEN-02)
            return
        idx = torch.cat([idx, next_id], dim=1)
        yield tok

def collect(model, idx, **kw):
    """Drain the generator into the FULL sequence (prompt + new) the GEN-03 tests assert on (D-02)."""
    out = idx
    for tok in generate(model, idx, **kw):
        out = torch.cat([out, torch.tensor([[tok]], dtype=out.dtype, device=out.device)], dim=1)
    return out
```
`model.config.block_size` is available since `GPT` stores `self.config` (gpt.py:62, `self.config`).
`[CITED: gpt.py forward + self.config; CONTEXT.md D-02/D-04/D-05]`

### Pattern 6: Text wrapper (D-01/D-03/D-06)
```python
def generate_text(model, tokenizer, prompt, *, eos_id, **gen_kw):
    """str -> str. EOS-prepend seeding (D-03), prompt strip (D-02), running-buffer delta (D-06)."""
    prompt_ids = [eos_id] + (tokenizer.encode(prompt) if prompt else [])   # empty -> [eos_id] (D-03)
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    emitted = ""
    buffer_ids = []                       # NEW ids only (prompt stripped per D-02)
    for tok in generate(model, idx, eos_id=eos_id, **gen_kw):
        buffer_ids.append(tok)
        text = tokenizer.decode(buffer_ids)   # decode WHOLE running buffer each step (D-06)
        new = text[len(emitted):]             # yield only the new suffix -> no mojibake
        emitted = text
        yield new                              # streaming; demo joins, or call list()/"".join for str
```
**Why running-buffer (D-06):** byte-level BPE tokens can be partial multi-byte UTF-8 sequences (emoji,
smart quotes). Per-token `decode([tok])` would raise `UnicodeDecodeError` (decode is **strict**,
bpe.py:209) or split a glyph. Decoding the cumulative buffer and diffing the string suffix guarantees
only complete characters are emitted. The strict round-trip is confirmed below. `[CITED: bpe.py decode; CONTEXT.md D-06]`

### Anti-Patterns to Avoid
- **Adding `generate` as a method on `GPT`.** The model class deliberately ships no generate/sample
  (gpt.py docstring). Keep generation a separate package — preserves the locked `forward` surface and
  the LoRA/EWC seam. `[CITED: gpt.py module docstring]`
- **Per-token `tokenizer.decode([tok])` in the streaming wrapper.** Causes mojibake / strict-decode
  crashes on multi-byte glyphs. Use the running-buffer delta (D-06).
- **Yielding the EOS token then trimming after.** D-05 says stop *without* yielding — trimming is
  implicit, no post-hoc slice needed.
- **Global `torch.manual_seed` for sampled determinism in tests.** Leaks into the global RNG stream;
  use a local `torch.Generator`.
- **Magic `256` for block_size.** Read `model.config.block_size` so a tiny test fixture model works.
- **Mutating `logits` in place without `.clone()`** when the same logits tensor is reused — the
  nanoGPT in-place mask is fine because logits is freshly sliced each step, but `top_k_filter`/`top_p_filter`
  as standalone funcs should `.clone()` defensively.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Top-k selection | Manual partial sort | `torch.topk` | Fused, correct, GPU/CPU/MPS. nanoGPT uses it. |
| Categorical sampling | Manual CDF + uniform draw | `torch.multinomial(probs, 1, generator=g)` | Handles the seeded-RNG path correctly; the `generator=` arg is the whole determinism story. |
| Greedy | `multinomial` with temp→0 | `torch.argmax` | Exactly reproducible, no RNG, no `temperature/0`. |
| Softmax over masked logits | Manual exp/normalize | `torch.softmax` after `-inf` mask | `-inf` → 0 prob cleanly; numerically stable. |
| UTF-8-safe streaming | Per-token decode + buffering bytes | Running-buffer decode + string-suffix diff (D-06) | The tokenizer is byte-level; only whole-buffer decode guarantees complete glyphs. |
| Model loading | New loader | `checkpoint.load_checkpoint` | `best.pt` is an open dict carrying its own `model_config`; reuse the existing loader. |

**Key insight:** Phase 6 is ~80% gluing existing torch primitives and existing repo contracts. The
only genuinely new logic is top-p filtering and the generator/streaming shape — everything else is
verified nanoGPT idiom over the locked `forward`.

## Runtime State Inventory

> Phase 6 is a **greenfield additive** phase (new `generation/` package + new tests). It is NOT a
> rename/refactor/migration, so a full runtime-state audit does not apply. The relevant invariant is
> the scope fence: **no changes to stored data, model, tokenizer, checkpoint, or training loop.**

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `checkpoints/best.pt` (166 MB, val 0.7378) and `latest.pt` exist; `artifacts/tokenizer.json` (5.6 KB) exists. Generation READS these, never writes/migrates. | None — read-only consumers. `[VERIFIED: ls checkpoints/ artifacts/]` |
| Live service config | None — no external services in M1. | None. |
| OS-registered state | None. | None. |
| Secrets/env vars | None referenced by generation. | None. |
| Build artifacts | New `generation/` package is importable after `pip install -e .` (already editable-installed). No reinstall needed for a new subpackage under `src/personacore/`. | None — editable install picks up new modules. `[VERIFIED: src-layout editable install]` |

**Existing `sample()` supersession (D-11):** `training/loop.py::sample()` (lines 106-119) and the
periodic sample hook (375-380) **stay untouched** this phase. D-11 only requires `generate()`
*supersede* `sample()` in capability; rewiring the loop is explicitly deferred. The `training/__init__`
barrel still exports `sample` — leave it. `[CITED: CONTEXT.md D-11, deferred ideas]`

## Common Pitfalls

### Pitfall 1: Forgetting context cropping → crash past block_size
**What goes wrong:** Generating more than `block_size - len(prompt)` tokens hits the `forward` assert
`T <= block_size` and crashes.
**Why it happens:** The model has a fixed 256 position-embedding table; `forward` asserts it.
**How to avoid:** Crop `idx[:, -block_size:]` before every forward (Pattern 4). This is a named
GEN-02 success criterion, so it must be explicitly tested.
**Warning signs:** Test that generates `> block_size` tokens; assert no exception. `[CITED: gpt.py:190]`

### Pitfall 2: Sampled-determinism test flaky due to global RNG
**What goes wrong:** Two `generate` calls with "the same seed" diverge because another test consumed
the global RNG between them, or the seed wasn't actually reset.
**Why it happens:** Relying on global `torch.manual_seed` state.
**How to avoid:** Pass a fresh `torch.Generator().manual_seed(s)` into each call; assert two calls with
two generators seeded identically produce identical sequences. Keeps GEN-03 hermetic. `[CITED: CONTEXT.md determinism note]`

### Pitfall 3: Streaming mojibake / strict-decode crash
**What goes wrong:** `tokenizer.decode([single_tok])` raises `UnicodeDecodeError` (decode is strict,
no U+FFFD) or emits a broken half-glyph mid-stream.
**Why it happens:** Byte-level BPE ids can be fragments of a multi-byte UTF-8 character.
**How to avoid:** Running-buffer delta decode (D-06, Pattern 6).
**Warning signs:** A streaming test over a prompt that produces multi-byte output. `[CITED: bpe.py:189-209 strict decode]`

### Pitfall 4: EOS leaking into output
**What goes wrong:** The literal `<|endoftext|>` (or its id 8184) appears in demo text.
**Why it happens:** Yielding EOS then trimming late, or not stopping on it.
**How to avoid:** D-05 — `return` from the generator the instant `next_id == eos_id`, before yield/append.
**Warning signs:** EOS-stop test asserts the collected sequence's last id is never `eos_id`, and the
sequence is strictly shorter than `prompt_len + max_new_tokens` when EOS fires early. `[CITED: CONTEXT.md D-05]`

### Pitfall 5: top-p off-by-one (dropping or keeping the wrong boundary token)
**What goes wrong:** Nucleus mask either drops the highest-prob token (empty distribution → multinomial
error) or keeps one too many.
**Why it happens:** Cumulative-sum masking without the shift-right + always-keep-first guard.
**How to avoid:** Use the shift pattern in Pattern 3; **add a unit test** that a known logit vector with
a fixed `p` keeps exactly the expected token set. `[ASSUMED — pin with a test in Wave 0]`

### Pitfall 6: Forgetting `model.eval()` / `torch.no_grad()`
**What goes wrong:** Dropout active during generation (model trained with `dropout=0.0` so low risk,
but eval is correct), or autograd graph built (memory/slowness).
**How to avoid:** Decorate the core `@torch.no_grad()` and call `model.eval()` once before generation
(in the wrapper or a load helper). `dropout=0.0` in `ModelConfig` makes train/eval equivalent here, but
`eval()` is still the correct posture. `[CITED: config.py:92 dropout=0.0]`

## Code Examples

### Loading best.pt for generation (reuses existing loader)
```python
# Source: src/personacore/checkpoint.py + config.py  [CITED]
from personacore.config import ModelConfig, RuntimeConfig
from personacore.model import GPT
from personacore.checkpoint import load_checkpoint

runtime = RuntimeConfig()                          # CPU or MPS (single device source)
# best.pt embeds its own model_config dict; rebuild the config, construct, then load weights.
import torch
raw = torch.load("checkpoints/best.pt", map_location="cpu", weights_only=False)
model_cfg = ModelConfig(**raw["model_config"])
model = GPT(model_cfg).to(runtime.device)
load_checkpoint("checkpoints/best.pt", model=model, map_location=runtime.device)  # optimizer=None ok
model.eval()
```
Note: `load_checkpoint` restores global RNG state from the checkpoint (checkpoint.py:104-109) — for
generation this is harmless, but it is a reason GEN-03 tests should construct a **tiny fresh model**,
not load `best.pt`, and use a local `torch.Generator` for sampling. `[CITED: checkpoint.py]`

### Strict round-trip confirmation (for D-06 safety)
```python
# Source: src/personacore/tokenizer/bpe.py:189-209  [VERIFIED: code read]
# decode(...) uses errors="strict" (the default) — byte-level base-256 coverage guarantees a valid
# round-trip, so decode(encode(x)) == x. This is what makes the running-buffer delta safe: the FULL
# buffer always decodes cleanly; only single-token decodes risk a partial multi-byte sequence.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Return-only sample loop (current `training/loop.py::sample`) | Generator-core + collect helper | This phase (D-04) | Streaming is free; one decode path serves tests + eval + demo. |
| top-k only (vanilla nanoGPT) | top-k + top-p (nucleus) stackable | This phase (GEN-01) | Richer sampling toolkit; top-p added on top of the verified top-k idiom. |

**Deprecated/outdated:** Nothing in this domain is moving fast. The nanoGPT generate idiom is stable
and matches `torch` 2.7 APIs (`torch.topk`, `torch.multinomial(generator=)`, `torch.softmax`) exactly.
`[VERIFIED: torch 2.7.1 APIs present]`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | top-p (nucleus) sort-cumsum-shift masking keeps exactly the intended token set | Pattern 3, Pitfall 5 | Low — pinned by a Wave-0 unit test with a hand-computed expected nucleus; algorithm is textbook. |
| A2 | Greedy folded as an explicit `greedy: bool` / `temperature == 0` path is the cleanest signature | Pattern 2 | Low — Claude's discretion per CONTEXT; planner may choose `top_k==1` or `do_sample=False`. Behavioral equivalence holds. |
| A3 | `torch.Generator` (not global seed) is the right determinism mechanism for hermetic tests | Determinism / Pitfall 2 | Low — explicitly the recommended approach in CONTEXT; standard pytest hygiene. |
| A4 | A new subpackage under `src/personacore/` is importable without reinstall (editable src-layout) | Runtime State Inventory | Low — `pip install -e .` already done; src-layout editable installs resolve new modules. |

**Note:** Most of this research is `[VERIFIED]` (nanoGPT source, repo code reads) or `[CITED]`
(CONTEXT.md locked decisions). The only `[ASSUMED]` items are the top-p masking exactness (A1) and the
greedy-signature taste call (A2) — both low-risk and resolved by tests/planner discretion.

## Open Questions

1. **Exact public signature of `generate()` and defaults.**
   - What we know: must support greedy/temperature/top-k/top-p, `max_new_tokens`, `eos_id`, a seed/
     `generator`. Single-sequence (no batch).
   - What's unclear: default values (e.g. `temperature=1.0`, `top_k=None`, `top_p=None`, `greedy=False`),
     and whether greedy is its own flag or `temperature==0`.
   - Recommendation: planner picks; suggest explicit `greedy: bool = False` + `generator=None`. Keep
     nanoGPT-simple. `eos_id` should default from `model.config.eos_id` if not passed.

2. **Does the text wrapper return a string or a generator of suffixes?**
   - What we know: D-06 streams suffixes; Phase-8 Gradio wants streaming; GEN-03/tests want a final str.
   - Recommendation: make the wrapper a **generator of new-suffix strings**; provide a thin
     `generate_text_str(...) == "".join(...)` convenience for non-streaming callers. One impl, both uses
     (mirrors core/collect).

3. **Where does the eval/qualitative-samples consumer (Phase 7) call in?**
   - What we know: Phase 7 uses `collect()` for qualitative samples and `forward` directly for perplexity.
   - Recommendation: ensure `collect()` returns a `(1, T)` `LongTensor` on the model's device — that is
     the shape Phase-7 and GEN-03 both want. Not blocking for Phase 6.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PyTorch | All of generation | ✓ | 2.7.1 | — `[VERIFIED: .venv]` |
| pytest | GEN-03 tests | ✓ | 8.x (9.0.3 plugin cache seen) | — `[VERIFIED: tests/ pyc]` |
| `checkpoints/best.pt` | Optional manual smoke / Phase-7 (NOT GEN-03 tests) | ✓ | val 0.7378 | tests use a tiny fixture model, not best.pt `[VERIFIED: ls]` |
| `artifacts/tokenizer.json` | Text wrapper (not the id-space core/tests) | ✓ | schema v1, vocab 8192 | — `[VERIFIED: ls]` |
| Python 3.11 venv | Dev/test (3.14 box unsupported) | ✓ (`.venv`) | 3.11 | CI pins 3.11 `[CITED: CLAUDE.md]` |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** GEN-03 tests deliberately avoid `best.pt`/tokenizer — they use
a tiny `GPT(ModelConfig(block_size=..., vocab_size=..., n_layer=1, ...))` CPU fixture so the suite stays
fast and GPU/MPS-free (matching `test_gpt_model.py`).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (plugin cache shows pytest-9.0.3 entries) |
| Config file | `pyproject.toml` (project uses `pytest`; `tests/conftest.py` holds shared fixtures) |
| Quick run command | `.venv/bin/python -m pytest tests/test_generation.py -x -q` |
| Full suite command | `make test` (CPU-only, GPU-free) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GEN-03 | Output shape: `collect()` returns `(1, prompt_len + n)` LongTensor when no EOS | unit | `pytest tests/test_generation.py::test_output_shape -x` | ❌ Wave 0 |
| GEN-03 | Determinism — greedy: two `argmax` runs are bit-identical | unit | `pytest tests/test_generation.py::test_greedy_deterministic -x` | ❌ Wave 0 |
| GEN-03 | Determinism — sampled: two runs with identically-seeded `torch.Generator` match | unit | `pytest tests/test_generation.py::test_seeded_sampling_deterministic -x` | ❌ Wave 0 |
| GEN-02 | EOS-stop: core halts without yielding `eos_id`; collected seq never ends in EOS | unit | `pytest tests/test_generation.py::test_eos_stop -x` | ❌ Wave 0 |
| GEN-02 | Context crop: generating past `block_size` does not raise | unit | `pytest tests/test_generation.py::test_past_block_size_no_crash -x` | ❌ Wave 0 |
| GEN-01 | top-k restricts support to k tokens; top-p restricts to nucleus | unit | `pytest tests/test_generation.py::test_top_k_top_p_support -x` | ❌ Wave 0 |
| GEN-01 | temperature scaling affects distribution (low temp → near-greedy) | unit | `pytest tests/test_generation.py::test_temperature -x` | ❌ Wave 0 |
| GEN-01 | top-p keeps the expected token set on a hand-computed logit vector (pins A1) | unit | `pytest tests/test_generation.py::test_top_p_nucleus_exact -x` | ❌ Wave 0 |

**Determinism test idioms:**
- *Greedy:* construct a tiny `GPT(ModelConfig(...))` with `torch.manual_seed(s)`; call greedy
  `collect()` twice; assert tensors equal. No `Generator` needed (argmax has no RNG).
- *Sampled:* `g1 = torch.Generator().manual_seed(0); g2 = torch.Generator().manual_seed(0)`; pass each
  into a `collect(..., generator=gN)` call; assert equal. Demonstrates seed isolation.
- *EOS-stop:* construct/force a model (or monkeypatch logits) so `eos_id` is the argmax at a known
  step; assert generation stops there and the last id != `eos_id`.

### Sampling Rate
- **Per task commit:** `.venv/bin/python -m pytest tests/test_generation.py -x -q`
- **Per wave merge:** `make test` (full CPU suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_generation.py` — covers GEN-01/02/03 (shape, determinism, EOS-stop, crop, sampling).
- [ ] Tiny-model fixture (in the test file or `tests/conftest.py`): `GPT(ModelConfig(block_size=8,
      vocab_size=16, n_layer=1, n_head=1, n_embd=8, eos_id=...))` for fast CPU runs. Consider a fixture
      that monkeypatches `model.forward` to return controlled logits for deterministic EOS/nucleus tests.
- [ ] No framework install needed — pytest already present.

## Security Domain

> `security_enforcement` is not set to `false` in config.json (the key is absent → treat as enabled).
> Phase 6 is pure local computation with no network, no untrusted input parsing, and no new
> serialization. Most ASVS categories do not apply.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface (local library). |
| V3 Session Management | no | None. |
| V4 Access Control | no | None. |
| V5 Input Validation | partial | The text wrapper takes a user prompt → `tokenizer.encode`, which is byte-level and cannot produce out-of-range ids; `decode` is strict and raises on malformed bytes. No injection surface. `max_new_tokens` should be bounded to avoid an unbounded loop (DoS) — enforce a sane cap. |
| V6 Cryptography | no | None — `torch.Generator` seeding is for test determinism, not security. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Untrusted checkpoint deserialization | Tampering / RCE | `best.pt` loads with `weights_only=False` (code-executing pickle) — TRUSTED-OWN-FILE ONLY, already documented in checkpoint.py. Phase 6 does not change this; the slim **inference** checkpoint with `weights_only=True` is Phase-8 (DEMO-02). Do NOT load arbitrary user-supplied `.pt` files in generation. |
| Unbounded generation loop | Denial of Service | Always require/bound `max_new_tokens`; the loop is `for _ in range(max_new_tokens)`, so it terminates. The wrapper should reject absurd values. |
| Mojibake / decode crash on adversarial bytes | (robustness) | Running-buffer delta decode (D-06); strict decode surfaces genuine defects rather than silently corrupting. |

## Sources

### Primary (HIGH confidence)
- `src/personacore/model/gpt.py` (read) — locked `forward(idx, targets=None)->(logits,loss)`, assert
  `T <= block_size` (line 190), `self.config`, no built-in generate. `[VERIFIED]`
- `src/personacore/config.py` (read) — `ModelConfig`: `block_size=256`, `vocab_size=8192`,
  `eos_id=8184`, `dropout=0.0`; `RuntimeConfig` device CUDA→MPS→CPU. `[VERIFIED]`
- `src/personacore/checkpoint.py` (read) — `load_checkpoint` open-dict, `weights_only=False`,
  `map_location`, embedded `model_config`, RNG restore. `[VERIFIED]`
- `src/personacore/tokenizer/bpe.py` + `io.py` (read) — `encode`/`decode`, strict UTF-8 decode (no
  `<unk>`), `from_json`, special-token atomicity, `eos_id`. `[VERIFIED]`
- `src/personacore/training/loop.py` (read) — minimal `sample()` (106-119) generate() supersedes;
  `[eos_id]`-seeded periodic sample hook (375-380). `[VERIFIED]`
- `tests/test_gpt_model.py`, `tests/conftest.py` (read) — test idioms (seed-first, tiny `GPT(ModelConfig)`,
  CPU-only, monkeypatch fixtures). `[VERIFIED]`
- nanoGPT `model.py::generate` — github.com/karpathy/nanoGPT — verbatim top-k + crop + multinomial loop. `[VERIFIED: WebFetch raw source 2026-06-06]`
- `.planning/phases/06-generation-sampling/06-CONTEXT.md` — locked decisions D-01..D-06, scope fences. `[CITED]`
- `.planning/REQUIREMENTS.md` / `ROADMAP.md` — GEN-01/02/03 acceptance + 3 success criteria. `[CITED]`

### Secondary (MEDIUM confidence)
- top-p / nucleus sampling: standard HF/community sort-cumsum-shift masking idiom (cross-checked
  against the well-known Holtzman et al. nucleus-sampling pattern). Pinned by a Wave-0 unit test.

### Tertiary (LOW confidence)
- None. (No unverified web-only claims used.)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; torch 2.7.1 verified installed; all primitives present.
- Architecture: HIGH — generator/collect/wrapper layering is directly mandated by D-01/D-02/D-04 and
  every contract it sits on (forward, decode, load) was read in-repo.
- Pitfalls: HIGH — derived from verified code constraints (block_size assert, strict decode,
  weights_only) and one MEDIUM (top-p off-by-one, pinned by a test).

**Research date:** 2026-06-06
**Valid until:** ~2026-07-06 (stable domain; the only volatility is torch minor APIs, which are pinned).
