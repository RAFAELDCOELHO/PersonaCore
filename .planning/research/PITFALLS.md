# Pitfalls Research

**Domain:** From-scratch small GPT-style language model (BPE + ~10–15M-param decoder + training loop + TinyStories pretraining + sampling + Gradio demo), trained on Kaggle free-tier P100, inference on laptop CPU
**Researched:** 2026-06-04
**Confidence:** HIGH (core ML correctness pitfalls verified against nanoGPT source and GPT-2 conventions; Kaggle/P100 ops facts verified against Kaggle docs and NVIDIA specs)

> Phase labels used below map to the natural roadmap decomposition: **Tokenizer**, **Model**, **Training**, **Pretraining (TinyStories)**, **Demo**, plus **Scaffolding** (repo/env/Kaggle setup). These are pitfall-prevention targets, not a final phase list.

---

## Critical Pitfalls

### Pitfall 1: BPE merge-ordering / determinism bug (the tokenizer silently disagrees with itself)

**What goes wrong:**
The from-scratch BPE trainer picks merges in a non-deterministic or wrong-priority order. Classic causes: iterating pair counts over a `dict` and relying on insertion order, breaking count ties inconsistently, or using `max(counts)` without a stable secondary key. The result is a `merges` list whose order doesn't match what `encode()` later replays. Encoded IDs then diverge run-to-run, or `encode()` applies merges in a different order than training produced — so the learned vocabulary and the encoder disagree.

**Why it happens:**
BPE encoding must apply merges in *exactly* the rank order they were learned (lowest merge index first, repeatedly, until no learned pair remains). Beginners re-derive merges greedily at encode time, or store merges in a `set`/`dict` that loses order, or re-train on a different data shuffle and get a different tie-break.

**How to avoid:**
- Store merges as an ordered list and a `pair -> rank` dict; in `encode`, repeatedly find the *lowest-rank* applicable pair (the GPT-2 / `minbpe` algorithm), not a left-to-right single pass.
- Make tie-breaks fully deterministic: break equal counts by the lexicographically smallest pair (or smallest token IDs). Never depend on dict iteration order.
- Seed any data shuffling used during training-corpus prep.
- Write a property test: `decode(encode(s)) == s` for a corpus of tricky strings (emoji, multi-byte UTF-8, leading/trailing spaces, newlines, repeated chars).

**Warning signs:**
Round-trip test fails on some strings; vocab size differs between runs; encoding the same string in two sessions gives different IDs; loss looks fine but generations contain broken/garbled bytes.

**Phase to address:** Tokenizer

---

### Pitfall 2: Byte-level vs. character-level confusion → can't represent arbitrary text

**What goes wrong:**
The tokenizer is built over Python `str` characters (Unicode codepoints) rather than UTF-8 bytes. It then either crashes or emits `<unk>` on any character not seen in training (accented letters, smart quotes `’ “ ”`, emoji). Decoding can also produce `UnicodeDecodeError` if merges split a multi-byte character.

**Why it happens:**
Char-level BPE is the "obvious" first implementation and works on toy ASCII corpora, so the bug is invisible until real text (TinyStories has smart quotes and apostrophes) or demo user input arrives.

**How to avoid:**
- Implement **byte-level BPE**: encode the input string to `bytes` first (`s.encode("utf-8")`), so the base vocabulary is the 256 byte values and *every* possible input is representable — no `<unk>` ever needed.
- On decode, accumulate bytes and call `.decode("utf-8", errors="replace")` once at the end, not per-token (a token can be a partial multi-byte sequence).
- Test round-trip on non-ASCII: `"café — "she said" 🙂"`.

**Warning signs:**
`<unk>` tokens appear; `KeyError` on encode of new text; `UnicodeDecodeError` on decode; demo breaks when the user types an emoji or curly quote.

**Phase to address:** Tokenizer

---

### Pitfall 3: Special-token / EOS handling that corrupts the stream or never stops generation

**What goes wrong:**
Several related failures: (a) special tokens like `<|endoftext|>` are merged/split by BPE instead of being atomic, so they can be partially matched inside ordinary text; (b) document boundaries aren't marked with EOS during training, so the model learns to run stories together and never stops; (c) generation has no EOS stop condition, so it rambles to `max_tokens` every time; (d) the EOS id used at training differs from the one checked at generation.

**Why it happens:**
Special tokens are added "later" as an afterthought and routed through the same merge logic as text. EOS-on-decode is forgotten because TinyStories samples look fine mid-stream.

**How to avoid:**
- Reserve special-token IDs *outside* the merge algorithm. Split input on the literal special-token strings first, encode the in-between text with BPE, and splice the reserved IDs in (the `minbpe`/tiktoken pattern). Special tokens must never be produced or consumed by merges.
- Insert one EOS token between documents/stories when building the training corpus so the model learns story boundaries.
- In the sampler, stop when EOS is generated (and trim it from output). Assert `tokenizer.eos_id` is one consistent constant used everywhere.

**Warning signs:**
Generations never terminate naturally; stories blend into each other; the EOS string appears verbatim in output; encoding a string containing `<|endoftext|>` produces unexpected ids.

**Phase to address:** Tokenizer (reserved-id mechanism) + Pretraining (corpus EOS insertion) + Demo (stop condition)

---

### Pitfall 4: Causal-mask bug — model peeks at the future (train/eval mismatch)

**What goes wrong:**
The attention mask is wrong: off-by-one (uses `triu` where it should use `tril`, or masks the diagonal), applied after softmax instead of before, added with `+inf` instead of `-inf`, or built once at one sequence length and silently broadcast wrong when a shorter sequence is fed at inference. If position *t* can attend to *t+1…*, the model trivially "cheats": training loss plummets toward zero, but generation is gibberish because at inference there is no future to peek at.

**Why it happens:**
The mask is easy to get directionally backwards, and the symptom (suspiciously low loss) is mistaken for success. The bug only reveals itself at generation time.

**How to avoid:**
- Mask is `tril` (lower-triangular kept), apply by setting masked scores to `-inf` (or a large negative) **before** softmax.
- Register the mask as a buffer sized to `block_size` and **slice** it to the actual `T` each forward: `mask[:T, :T]`. Never assume `T == block_size`.
- Prefer `F.scaled_dot_product_attention(..., is_causal=True)` if PyTorch ≥ 2.0 is available on both Kaggle and laptop — it gets the masking and scaling right and is the fallback reference. (From-scratch attention is still implemented for the portfolio; SDPA is a correctness oracle in tests.)
- **Test:** feed a batch, check that changing token at position `t` cannot change the logits at positions `< t` (gradient/output-perturbation test). This directly proves causality.

**Warning signs:**
Train loss drops far below what a 10M model should reach (e.g., near 0 or well under ~1.0 nats on TinyStories) while samples are incoherent; huge gap where validation loss is fine but free-running generation is nonsense.

**Phase to address:** Model

---

### Pitfall 5: Missing `1/sqrt(d_k)` attention scaling

**What goes wrong:**
Attention scores `Q·Kᵀ` are passed to softmax without dividing by `sqrt(head_dim)`. With larger head dimensions the dot products have large variance, softmax saturates to near one-hot, gradients vanish, and training stalls or is unstable.

**Why it happens:**
The scaling term is a single easy-to-omit line; on tiny `d_k` the effect is mild so toy tests pass, then it bites at the real head dimension.

**How to avoid:**
Scale by `1.0 / math.sqrt(head_dim)` (the per-head dimension, not the full model dim) before the mask and softmax. Unit-test that attention weights for random Q,K are not collapsed to one-hot at the configured head size.

**Warning signs:**
Loss plateaus immediately; attention weights are nearly one-hot from step 0; gradients in attention layers are tiny.

**Phase to address:** Model

---

### Pitfall 6: Weight-init not GPT-2 style (esp. missing residual-scaled init) → unstable deep-ish training

**What goes wrong:**
Layers use PyTorch defaults (Kaiming-uniform for Linear) instead of GPT-2's `Normal(0, 0.02)`, and — the more subtle one — the residual-path output projections are **not** down-scaled. GPT-2 scales the `c_proj` (attention and MLP output) init by `0.02 / sqrt(2 · n_layer)` so that residual contributions don't compound and blow up activation variance with depth. Without it, early-step loss spikes and fp16 is more likely to overflow.

**Why it happens:**
"Init doesn't matter much" folklore; the residual-scaled trick is non-obvious and only documented in the GPT-2 paper / nanoGPT source.

**How to avoid:**
- Linear and Embedding weights: `Normal(mean=0, std=0.02)`; Linear biases: zero; LayerNorm weight=1, bias=0.
- Apply scaled init to residual projections: `std = 0.02 / sqrt(2 * n_layer)` on the `c_proj` weights (match nanoGPT's `_init_weights` + the named-parameter pass over `*.c_proj.weight`).
- Unit-test: after init, the std of each weight tensor matches the expected target within tolerance.

**Warning signs:**
First-few-step loss is much larger than `ln(vocab_size)` and spikes; early NaNs under fp16; training needs an absurdly low LR to not diverge.

**Phase to address:** Model

---

### Pitfall 7: LayerNorm placement (post-norm instead of pre-norm)

**What goes wrong:**
Norm is placed *after* the residual add (original-Transformer post-norm: `x = LN(x + sublayer(x))`) instead of *before* the sublayer (pre-norm: `x = x + sublayer(LN(x))`). Post-norm decoders are notably harder to train without learning-rate warmup and are more prone to divergence at small scale — and a missing **final** LayerNorm before the LM head is a common silent omission.

**Why it happens:**
Many tutorials show the original post-norm Transformer diagram; GPT-2's pre-norm + final-LN is a deviation that's easy to miss.

**How to avoid:**
- Use **pre-norm** blocks: `x = x + attn(LN1(x))`, `x = x + mlp(LN2(x))`.
- Add a **final LayerNorm** after the last block, before the LM head (`ln_f` in nanoGPT). Verify it exists.
- Keep LR warmup anyway (cheap insurance), but pre-norm makes training robust.

**Warning signs:**
Training diverges without warmup; sensitive to LR; loss noisy/unstable; logits have growing magnitude across layers.

**Phase to address:** Model

---

### Pitfall 8: Positional-embedding off-by-one / length overflow

**What goes wrong:**
Learned positional embeddings are indexed with `arange` that doesn't match the actual `T`, or generation extends past `block_size` and indexes the position table out of range (`IndexError` or, worse, silent wrap). Mixing position indexing between training (full `block_size`) and incremental generation also produces a shift.

**Why it happens:**
Position indices are constructed in two places (forward and generate) and drift apart; the context-window cap is forgotten in the sampling loop.

**How to avoid:**
- Build positions as `torch.arange(0, T, device=...)` from the *actual* input length every forward, and assert `T <= block_size`.
- In `generate`, crop the context to the last `block_size` tokens before each step (`idx[:, -block_size:]`). This is the canonical nanoGPT guard.
- Test generation for more than `block_size` tokens — it must not crash.

**Warning signs:**
`IndexError` on long prompts/generations; quality collapses once output exceeds the context window; positions look shifted by one.

**Phase to address:** Model + Demo (generate-loop cropping)

---

### Pitfall 9: Weight-tying shape/gradient mistake

**What goes wrong:**
Token embedding (`wte`, shape `[vocab, d]`) and LM head (`Linear(d, vocab)`, weight shape `[vocab, d]`) are meant to share one tensor, but the implementation either (a) transposes one and assigns a *copy* (so they drift during training), (b) ties them but double-counts the parameter when computing param totals, or (c) gets a shape error and "fixes" it by transposing, breaking the tie.

**Why it happens:**
The two weights *look* like they need a transpose because of how `nn.Linear` stores weights; in fact `nn.Linear`'s `[out, in]` layout already matches `[vocab, d]`, so a direct `self.lm_head.weight = self.wte.weight` ties them correctly. People "helpfully" transpose and break it.

**How to avoid:**
- Tie by direct reference: `self.lm_head.weight = self.transformer.wte.weight` (nanoGPT pattern) — no transpose, no copy.
- Assert `lm_head.weight.data_ptr() == wte.weight.data_ptr()` in a test to prove they're the same tensor.
- Count parameters with a `set()` of tensor `id()`s so the tied weight isn't double-counted when reporting "~10–15M params."

**Warning signs:**
Param count is off by `vocab*d` (~hundreds of thousands here); changing one weight doesn't change the other; slightly worse loss than expected for the size.

**Phase to address:** Model

---

### Pitfall 10: fp16 AMP overflow/underflow on P100 — and the wrong assumption that AMP makes P100 *fast*

**What goes wrong:**
Two linked traps. (a) **Correctness:** fp16 has a narrow dynamic range; without `torch.cuda.amp.GradScaler`, gradients underflow to zero (silent stalled learning) or activations/loss overflow to `inf`/`NaN`. (b) **Expectations:** the P100 (Pascal, compute capability **6.0**) has **no Tensor Cores and no bf16**; fp16 AMP yields little or no speedup on P100 — its main benefit here is *memory*, not throughput. Teams enable AMP expecting a 2× speedup, get instability instead, and lose a chunk of their 30h quota chasing NaNs.

**Why it happens:**
AMP tutorials target Volta/Ampere where Tensor Cores give real speedups; the P100's lack of bf16 means the more-forgiving format isn't available, so you're stuck with fragile fp16.

**How to avoid:**
- If using AMP, **always** pair `autocast(dtype=torch.float16)` with `GradScaler()`; call `scaler.scale(loss).backward()`, `scaler.unscale_()` before clipping, `scaler.step(opt)`, `scaler.update()`. Never hand-roll fp16.
- Keep LayerNorm and the softmax/loss in fp32 (autocast does this for you — don't force them to half).
- **Strongly consider running fp32** at this model size. ~10–15M params trains comfortably in fp32 within 16GB; fp32 removes an entire class of NaN failures and the P100 speed loss from skipping AMP is negligible. Treat AMP as an optional memory optimization only if batch size demands it.
- Make `bf16` impossible to select by accident: guard the config so bf16 raises a clear error on P100.

**Warning signs:**
Loss becomes `NaN`/`inf` after some steps; loss flat-lines (underflow); `GradScaler` scale keeps halving; no wall-clock improvement from enabling AMP.

**Phase to address:** Training (+ Scaffolding for the bf16 guard)

---

### Pitfall 11: Training instability — LR too high, no warmup, no gradient clipping

**What goes wrong:**
Loss diverges (spikes to `inf`/`NaN`) within the first few hundred steps because the learning rate is too high, there's no warmup, and gradients aren't clipped. Small from-scratch transformers are sensitive in the first phase of training.

**Why it happens:**
Copying an LR from a large-model recipe; assuming clipping/warmup are optional niceties.

**How to avoid:**
- Use AdamW with a sane small-model LR (order `3e-4`–`6e-4` peak), **linear warmup** over the first few hundred steps, then cosine decay.
- **Gradient clipping** at global norm `1.0` (`clip_grad_norm_`) — cheap, near-mandatory for stability.
- `betas=(0.9, 0.95)`, weight decay ~`0.1` on 2D weights only (not biases/LayerNorm) — the nanoGPT param-group split.
- Log grad-norm and LR every N steps so a spike is visible before it becomes NaN.

**Warning signs:**
Loss spikes then NaNs; grad-norm grows unbounded; loss oscillates wildly; lowering LR "fixes" everything (sign warmup/clipping were missing).

**Phase to address:** Training

---

### Pitfall 12: `optimizer.zero_grad()` forgotten / misordered (gradient accumulation bug)

**What goes wrong:**
Grads aren't zeroed each step, so PyTorch *accumulates* them across steps — effectively an unbounded, unintended gradient accumulation that destabilizes training. Or, when intentionally accumulating over micro-batches, `zero_grad` is called inside the inner loop and wipes the accumulation.

**Why it happens:**
PyTorch accumulates grads by default; the zeroing call is invisible when present and catastrophic when absent. Gradient accumulation (likely needed to fit a decent effective batch in 16GB) makes the ordering subtle.

**How to avoid:**
- Standard loop: `opt.zero_grad(set_to_none=True)` → forward → backward → `opt.step()`.
- For accumulation over `k` micro-steps: zero **once** before the k micro-steps, scale each micro-loss by `1/k`, step **after** the k-th. Write this as a tested helper.
- Sanity-test: two identical batches with accumulation vs. one double batch without should give matching grad norms.

**Warning signs:**
Loss explodes early for no clear reason; effective LR seems far higher than configured; turning accumulation on/off changes stability dramatically.

**Phase to address:** Training

---

### Pitfall 13: Train/val leakage and broken evaluation

**What goes wrong:**
Validation set overlaps the training set (same stories, or a random split that lands duplicate/near-duplicate TinyStories on both sides), so val loss looks great but doesn't measure generalization. Or eval is run with dropout still on / `model.train()` left set, or without `torch.no_grad()`, giving noisy/wrong numbers and OOM.

**Why it happens:**
TinyStories has many similar stories; a naive shuffle-split leaks. The mode/`no_grad` toggles are easy to forget.

**How to avoid:**
- Split by document at the source (hold out whole stories), ideally use the dataset's provided validation split. Don't split mid-document.
- Wrap eval in `model.eval()` + `torch.no_grad()`; restore `model.train()` after.
- Report val loss on a fixed held-out set every N steps; also eyeball *generated* samples (loss alone hides repetition/looping).

**Warning signs:**
Val loss tracks train loss too perfectly; val ≪ what samples' quality suggests; eval OOMs (no `no_grad`); samples loop/repeat despite "good" loss.

**Phase to address:** Pretraining (split design) + Training (eval harness)

---

### Pitfall 14: Kaggle session timeout / quota exhaustion loses training progress

**What goes wrong:**
A Kaggle GPU session is capped at **~12 hours** of execution and the free tier gives **~30 GPU-hours/week** (a "floating" quota that may sometimes exceed 30h, but plan for 30). A long run that doesn't checkpoint frequently loses everything when the session ends, the browser tab closes (interactive sessions die when disconnected unless run via "Save & Run All" / commit), or the weekly quota runs out mid-epoch. Restarting from scratch burns more of the finite quota — a death spiral.

**Why it happens:**
The model trains "fine" interactively for hours; the operator assumes it'll just keep going. Interactive sessions are tied to the browser connection; only committed (batch) runs persist headless, and even those hit the 12h wall.

**How to avoid:**
- **Checkpoint to `/kaggle/working/` every N minutes** (e.g., every 15–30 min and every val eval), saving model + optimizer + scheduler + scaler + step + RNG states.
- Design the loop to **resume**: on start, look for the latest checkpoint and continue (step count, LR schedule position, data position). Resume must be *exact*, not "start a new run from these weights."
- Persist checkpoints across sessions via a **Kaggle Dataset** (output a versioned dataset, attach it as input next run) — `/kaggle/working/` is wiped between sessions; only committed outputs/datasets survive.
- Use **"Save & Run All (Commit)"** for long runs so training continues headless up to the 12h cap, independent of the browser.
- Budget the 30h: estimate steps/hour, size the run to finish (or to a clean checkpoint) within quota; never start a run you can't checkpoint before the wall.

**Warning signs:**
Run dies at ~12h; progress lost after closing the tab; "GPU quota exceeded" mid-week; `/kaggle/working` empty in a new session.

**Phase to address:** Scaffolding (checkpoint/resume infra) + Training (save cadence) — this is the single highest-leverage ops pitfall.

---

### Pitfall 15: GPU not actually enabled on Kaggle

**What goes wrong:**
The notebook runs on CPU because the accelerator wasn't switched to "GPU P100" in settings, or it fell back to CPU after a quota lapse. Training is ~10–50× slower; the operator doesn't notice for an hour and burns time (and, ironically, *not* GPU quota — but wall-clock and morale).

**Why it happens:**
Accelerator defaults to "None"; the toggle is in the notebook settings sidebar and easy to forget after forking.

**How to avoid:**
- First cell asserts CUDA: `assert torch.cuda.is_available()` and prints `torch.cuda.get_device_name(0)` (expect "Tesla P100"). Fail loudly if not.
- Print device and a quick `tokens/sec` benchmark in the first 50 steps so a CPU fallback is obvious immediately.

**Warning signs:**
`torch.cuda.is_available()` is `False`; device name isn't P100; steps/sec absurdly low; GPU quota not decrementing.

**Phase to address:** Scaffolding

---

### Pitfall 16: Non-reproducibility — unseeded runs, undocumented data version

**What goes wrong:**
Results can't be reproduced (a portfolio red flag at the MIT/Stanford bar): RNG unseeded, data shuffle order varies, TinyStories version/source unpinned, tokenizer retrained slightly differently. Two "identical" runs give different curves and the writeup's numbers can't be regenerated.

**Why it happens:**
Seeding feels optional during exploration; the dataset is grabbed ad hoc.

**How to avoid:**
- Seed everything: `random`, `numpy`, `torch`, `torch.cuda`; set `torch.manual_seed(seed)` and document that full determinism on GPU also needs deterministic algorithms (with a noted speed cost — fine to run non-deterministic but **log the seed and config**).
- Pin the TinyStories source/version (specific Kaggle dataset or HF revision) and record it; save the trained tokenizer (vocab + merges) as a versioned artifact, never retrain it ad hoc for eval.
- Save a `config.json` (and git SHA) alongside each checkpoint capturing all hyperparameters.

**Warning signs:**
Two runs diverge with "same" settings; can't recreate the writeup's loss curve; tokenizer vocab differs between training and demo.

**Phase to address:** Scaffolding (seed/config harness) + Tokenizer (artifact pinning)

---

### Pitfall 17: CPU inference too slow / checkpoint not laptop-portable

**What goes wrong:**
The demo must run on a laptop CPU with no internet, but: (a) generation is autoregressive with no KV cache, so each new token re-runs full attention over the whole context — interactive latency is painful; (b) the checkpoint was saved with optimizer/scaler state and CUDA tensors, so it's large and/or fails to load on CPU (`map_location` not set, or pickled custom classes not importable); (c) the model is loaded in fp16 on CPU where fp16 is slow/unsupported for many ops.

**Why it happens:**
Everything was tested on the P100; CPU portability is validated last (or never) until the demo.

**How to avoid:**
- Save a **separate, slim inference checkpoint**: model `state_dict` + config + tokenizer only (no optimizer/scaler), in fp32, with `torch.save` of plain tensors/dicts (no pickled custom objects). Load with `map_location="cpu"`.
- Implement a **KV cache** in `generate` so each step is O(1) in context length, not O(T). Even at 10–15M params this is the difference between snappy and unusable on CPU.
- Run inference in fp32 on CPU; cap `block_size` and use top-k/temperature to keep per-token compute bounded.
- **Test the demo path on the laptop offline early** (mid-project, not at the end): load slim checkpoint, generate, launch Gradio with `share=False`.

**Warning signs:**
Tokens take seconds each on laptop; checkpoint is tens-of-MB larger than the model warrants; `state_dict` load errors on CPU; Gradio tries to reach the internet.

**Phase to address:** Demo (slim checkpoint + KV cache + offline test), with a Model-phase hook to make `generate` cache-capable.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Char-level tokenizer instead of byte-level | Simpler to write | Can't represent real text; breaks on emoji/quotes; rework forced | Never (byte-level is barely harder) |
| Skip `GradScaler`, just `autocast` | One less moving part | Silent underflow / NaNs; wasted quota debugging | Never if using fp16; or just run fp32 |
| Train fp16 AMP "for speed" on P100 | Feels modern | No real speedup (no Tensor Cores); adds NaN risk | Only as a *memory* measure if fp32 batch won't fit |
| Checkpoint only at epoch end | Less I/O | Lose ~hours on a 12h-session kill | Never for runs > ~30 min |
| Keep optimizer state in the demo checkpoint | One file | Bloated, CUDA-tied, slow/failed CPU load | Never for the shipped demo artifact |
| No KV cache in generate | Less code | Unusable CPU demo latency | Acceptable only for the training-time sampler, not the demo |
| Random shuffle-split for val | One line | Train/val leakage on similar stories | Never; split by document |
| Retrain tokenizer per experiment | No artifact mgmt | Non-reproducible; train/demo vocab mismatch | Never; pin and version it |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Kaggle `/kaggle/working` | Assuming files persist across sessions | Wiped each session; commit output to a versioned Kaggle Dataset to persist checkpoints |
| Kaggle interactive session | Closing the tab during a long run | Use "Save & Run All (Commit)" for headless runs up to the 12h cap |
| Kaggle accelerator | Forgetting to set GPU P100; silent CPU fallback | Assert `torch.cuda.is_available()` + device name in cell 1 |
| TinyStories dataset | Grabbing an unpinned/ad-hoc copy | Pin a specific Kaggle dataset / HF revision; record the version in config |
| PyTorch version skew (Kaggle vs laptop) | SDPA / API differences cause load or runtime mismatch | Pin `torch` in `requirements.txt`; test load+generate on the laptop offline |
| Gradio in notebook / offline | `share=True` (needs internet) or tunnel attempts | Launch with `share=False`, `server_name="127.0.0.1"`; verify no network calls |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No KV cache at inference | Per-token latency grows with context | Cache K/V per layer in `generate` | Any CPU demo with non-trivial context |
| Batch/`block_size` too big for 16GB | CUDA OOM mid-run | Tune batch × block_size to ~12–14GB; use grad accumulation for effective batch | When sequence length or batch is raised |
| fp16 AMP expecting speedup on P100 | Same wall-clock, new NaNs | Use fp32, or AMP only for memory | Whenever AMP is enabled for "speed" |
| DataLoader CPU bottleneck (tokenizing on the fly) | GPU idle, low tokens/sec | Pre-tokenize TinyStories to a flat `uint16`/`int32` token array (`.bin`), memory-map it | Always at training scale |
| Saving full checkpoints too often | I/O stalls, fills `/kaggle/working` disk | Slim periodic checkpoints; prune old ones; keep last-N | Long runs with frequent saves |

## Security Mistakes

> Low surface area (offline, on-device, no DB by design), but portfolio-relevant:

| Mistake | Risk | Prevention |
|---------|------|------------|
| `torch.load` of an untrusted checkpoint | Arbitrary code execution via pickle | Only load own checkpoints; use `weights_only=True` (PyTorch ≥ 2.x) when loading state_dicts |
| Gradio `share=True` / `0.0.0.0` bind | Exposes local demo to the internet | `share=False`, bind localhost; matches the on-device privacy claim |
| Committing a Kaggle API token / dataset creds | Credential leak | Use Kaggle Secrets / env; never hardcode in notebook |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Demo generation never stops (no EOS) | Walls of text, looks broken | Stop on EOS; cap max tokens; trim trailing partial token |
| Raw broken bytes shown mid-stream | Garbled output on multibyte chars | Decode with buffered bytes + `errors="replace"`; only flush complete UTF-8 |
| No streaming in Gradio | Feels frozen during generation | Stream tokens as generated (Gradio generator output) |
| Temperature/top-k hardcoded | Can't show sampling behavior in demo | Expose temperature + top-k sliders (also a portfolio talking point) |

## "Looks Done But Isn't" Checklist

- [ ] **BPE tokenizer:** Often missing — byte-level handling and atomic special tokens — verify `decode(encode(x))==x` on emoji/quotes/newlines and that `<|endoftext|>` is never split by merges.
- [ ] **Causal attention:** Often missing — proof of causality — verify perturbing token *t* cannot change logits at positions `< t`, and mask is sliced to actual `T`.
- [ ] **Model init:** Often missing — residual-scaled init and final LayerNorm — verify per-tensor std ≈ targets and `ln_f` exists before the head.
- [ ] **Weight tying:** Often missing — true shared tensor — verify `data_ptr()` equality and param count not double-counting.
- [ ] **Training loop:** Often missing — exact resume — verify a kill-then-resume reproduces the same loss trajectory (step, LR, scaler, RNG, data position all restored).
- [ ] **AMP:** Often missing — `GradScaler` and fp32 norms/loss — verify no NaNs over a long run, or that fp32 is used instead.
- [ ] **Eval:** Often missing — `model.eval()` + `no_grad()` + leak-free split — verify val set holds out whole stories.
- [ ] **Generation:** Often missing — context cropping to `block_size`, EOS stop, KV cache — verify >`block_size` generation doesn't crash and stops on EOS.
- [ ] **Demo checkpoint:** Often missing — slim, fp32, CPU-loadable, no optimizer state — verify it loads and generates on the laptop **offline**.
- [ ] **Reproducibility:** Often missing — seed + pinned data/tokenizer + saved config — verify the writeup's curve can be regenerated.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Causal-mask / peeking bug | MEDIUM | Fix mask; re-run causality test; **retrain from scratch** (poisoned run is unsalvageable) |
| NaN loss under fp16 | LOW–MEDIUM | Resume from last good checkpoint; lower LR / add warmup+clip; or switch to fp32 |
| Tokenizer round-trip / vocab mismatch | HIGH if discovered late | Re-fix and **re-tokenize corpus + retrain** (tokenizer change invalidates a trained model) |
| Lost session progress (no checkpoint) | HIGH | Re-run within quota; going forward, add periodic save + dataset persistence |
| Quota exhausted mid-week | LOW (time) | Wait for weekly reset; resume from persisted checkpoint; right-size next run to quota |
| CPU demo too slow | LOW–MEDIUM | Add KV cache; cast to fp32; reduce block_size/max_tokens |
| Weight-tying broken | LOW | Re-tie by reference; usually retrain (weights drifted) — cheap at 10–15M |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| BPE merge ordering / determinism | Tokenizer | Deterministic vocab across runs; round-trip test passes |
| Byte-level handling | Tokenizer | Round-trip on non-ASCII passes; no `<unk>` |
| Special-token / EOS handling | Tokenizer + Pretraining + Demo | Special tokens atomic; generation stops on EOS |
| Causal-mask bug | Model | Causality perturbation test passes |
| Missing `1/sqrt(d_k)` scaling | Model | Attention weights not one-hot at configured head dim |
| GPT-2 / residual-scaled init | Model | Per-tensor std matches targets |
| Pre-norm + final LN | Model | Block structure + `ln_f` present; trains without warmup |
| Positional off-by-one / overflow | Model + Demo | Generate > block_size doesn't crash |
| Weight tying | Model | `data_ptr()` equal; param count correct |
| fp16 AMP overflow / P100 misuse | Training (+ Scaffolding guard) | No NaNs; bf16 guarded; fp32 fallback works |
| LR/warmup/clipping instability | Training | Stable loss; grad-norm logged and bounded |
| `zero_grad` / accumulation bug | Training | Accumulation-equivalence test passes |
| Train/val leakage & eval mode | Pretraining + Training | Doc-level split; eval uses `eval()`+`no_grad()` |
| Session timeout / quota loss | Scaffolding + Training | Kill-and-resume reproduces trajectory; checkpoints persist via dataset |
| GPU not enabled | Scaffolding | Cell-1 CUDA assert prints "Tesla P100" |
| Reproducibility / data version | Scaffolding + Tokenizer | Seed+config saved; data/tokenizer pinned |
| CPU inference slow / portability | Demo (+ Model hook) | Offline laptop generate is interactive; slim checkpoint loads on CPU |

## Sources

- karpathy/nanoGPT `model.py` — weight tying (`wte.weight = lm_head.weight`), GPT-2 init `Normal(0,0.02)`, residual-scaled init `0.02/sqrt(2*n_layer)`, pre-norm + `ln_f`, context cropping in `generate` — https://github.com/karpathy/nanoGPT/blob/master/model.py (HIGH)
- TinyStories paper (Eldan & Li, 2023) — sub-10M-param models produce coherent English; one transformer block can suffice — https://arxiv.org/abs/2305.07759 (HIGH)
- Kaggle Efficient GPU Usage docs + product-feedback — ~30h/week floating GPU quota, ~12h session cap, weekly reset, `/kaggle/working` persistence model — https://www.kaggle.com/docs/efficient-gpu-usage and https://www.kaggle.com/product-feedback/173129 (HIGH)
- NVIDIA P100 / mixed-precision docs — P100 = Pascal, compute capability 6.0, no Tensor Cores, no bf16, AMP needs CC ≥ 7.0 for real speedup — https://docs.nvidia.com/deeplearning/performance/mixed-precision-training/index.html (HIGH)
- PyTorch mixed-precision guidance — `GradScaler` required with fp16 autocast; norms/loss in fp32 — https://pytorch.org/blog/what-every-user-should-know-about-mixed-precision-training-in-pytorch/ (HIGH)
- minbpe / tiktoken byte-level + special-token handling conventions (Karpathy) — atomic special tokens, lowest-rank-first merge replay — training-data + repo conventions (MEDIUM)

---
*Pitfalls research for: from-scratch small GPT LM on Kaggle P100 / laptop-CPU demo*
*Researched: 2026-06-04*
