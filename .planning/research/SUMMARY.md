# Project Research Summary

**Project:** PersonaCore — Milestone 1 (from-scratch base language model + demo)
**Domain:** From-scratch small GPT-style language model (PyTorch), trained on Kaggle P100, inference on laptop CPU
**Researched:** 2026-06-04
**Confidence:** HIGH

## Executive Summary

PersonaCore Milestone 1 is a *portfolio engineering* project: a ~10–15M-parameter, decoder-only GPT built entirely from scratch in pure PyTorch (hand-rolled byte-level BPE, causal multi-head attention, pre-norm transformer blocks, training loop), pretrained on TinyStories to coherent generation, and shipped with a local Gradio CPU chat demo and a narrated `demo.ipynb`. This is a well-trodden architecture — the canonical reference is Karpathy's nanoGPT — so the technical risk is low and the patterns are well documented. The portfolio value does **not** come from a bigger or more novel *model*; at 10–15M on TinyStories the model is intentionally modest. It comes from doing *every component from scratch, correctly, with per-component unit tests, reproducibly, and well-documented* — exactly the dimensions where student clones and even reference repos are typically thin. LoRA + EWC personalization is **explicitly Milestone 2** and must not leak into M1 scope; M1's job is to de-risk the foundation before the novel weight-memory claim depends on it.

The recommended approach is a clean `src/personacore/` package (`tokenizer/`, `model/`, `data/`, `training/`, `generation/`, `config/`) installed with `pip install -e .` so that Kaggle notebooks, the Gradio app, and `pytest` all share the identical import path — eliminating the classic Kaggle `sys.path`/relative-import pain and making the same code portable across the GPU-train / CPU-infer split. Device and AMP concerns are centralized in a single `RuntimeConfig` (nothing else calls `torch.cuda.is_available()`); the model is a pure function of (params, input) that never imports `training/` or references the device. Two cheap structural seams are reserved for M2 at near-zero M1 cost: (A) every adaptable matmul is a **named `nn.Linear`** so M2's LoRA injector can find and wrap projections by name, and (B) the loss is routed through a single `assemble_loss(model, x, y, extra_penalties=())` function with an **empty** penalty list, plus **open-dict checkpoints**, so M2's EWC Fisher-penalty drops in additively without rewriting the loop. These are good design at M1 regardless of M2 — they add no behavior, no runtime cost, and no tests beyond what M1 already needs.

The dominant risks are *silent correctness bugs* and *Kaggle ops*, not algorithmic difficulty. The highest-severity correctness trap is the causal-attention mask (a backwards `triu`/`tril`, masking after softmax, or an unsliced mask makes the model peek at the future — train loss craters toward zero while generation is gibberish; a poisoned run is unsalvageable and must be retrained). The highest-leverage ops trap is Kaggle's session model: ~12h session cap, ~30 GPU-hours/week, and a `/kaggle/working` directory that is **wiped between sessions** — so exact, frequent, dataset-persisted resumable checkpointing is a *prerequisite for fluency*, not a nicety. Tokenizer correctness (byte-level BPE, deterministic lowest-rank-first merge replay, atomic special tokens) is load-bearing because a tokenizer change invalidates a trained model. And the demo must be proven to load a slim fp32 checkpoint and generate on a laptop CPU **offline** — validated mid-project, not at the end. Mitigation is overwhelmingly through tests (round-trip, causality-perturbation, overfit-one-batch, kill-and-resume) and disciplined artifact pinning.

## Key Findings

### Recommended Stack

The stack is deliberately minimal and zero-budget/offline: pure PyTorch with no HuggingFace model code, no online experiment tooling, and a from-scratch tokenizer. On Kaggle, **use the pre-installed PyTorch and do not reinstall `torch`** — this is load-bearing because the P100 is Pascal (compute capability 6.0) and PyTorch CUDA wheels built with **CUDA 12.8+ (`cu128`/`cu129`/`cu130`) dropped Pascal `sm_60` kernels**; only `cu126` and earlier retain them. Kaggle's pre-installed torch is already Pascal-valid; replacing it risks pulling a non-Pascal wheel and breaking GPU training. Locally (CPU dev/inference/tests) pin a CPU wheel (`torch==2.7.*` recommended for reproducibility; the Pascal issue is GPU-only and irrelevant on CPU). Data flows nanoGPT-style: download TinyStoriesV2-GPT4 `.txt` once → attach as a static Kaggle Dataset (keeps sessions offline) → train BPE → encode the whole corpus once into a flat `np.uint16` memmap (`train.bin`/`val.bin`) → sample random contiguous windows. Logging is offline CSV + matplotlib (no wandb/Comet/Neptune — they violate the offline/zero-budget/privacy intent).

**Core technologies:**
- **PyTorch** (Kaggle: pre-installed Pascal-valid build; local: `torch==2.7.*` CPU wheel) — tensors/autograd/nn/optimizer/AMP; everything from-scratch builds on `nn.Module` without HF model code.
- **NumPy 2.x** — flat `uint16` memmap for the pre-tokenized corpus; cheap random-window batch sampling (RAM-light, re-reads nothing).
- **Gradio 5.x** (`gr.ChatInterface`, `launch(share=False)`) — local on-device streaming chat demo in ~20 lines; fully offline.
- **pytest 8.x** — per-component unit tests are a *first-class deliverable*: round-trip, causal-mask, shape, and overfit-a-batch tests. `tiktoken`/HF `tokenizers` allowed **only as reference oracles in tests**, never as the implementation.
- **matplotlib / tqdm** — offline loss-curve figures for `demo.ipynb`; progress bars for the long BPE merge loop and training.
- **safetensors** *(optional, recommended)* — portable, safe (no pickle code-exec) format for the shippable laptop demo weights; keep the resume checkpoint as `torch.save` (needs optimizer/scaler/RNG state).

**Resolved precision decision (reconciling STACK vs PITFALLS):** STACK.md frames fp16 AMP + `GradScaler` mainly as a memory win on P100; PITFALLS.md argues for fp32-by-default at this scale because P100 (Pascal, no Tensor Cores, no bf16) gets **no throughput benefit** from AMP while AMP adds a real NaN/underflow risk class. **Decision: default to fp32 training at 10–15M params.** ~10–15M trains comfortably in fp32 within the 16GB P100, and fp32 removes an entire category of fp16 NaN/underflow failures with negligible P100 speed cost. Introduce **fp16 AMP + `GradScaler` ONLY as a memory measure** if batch size / 16GB headroom actually forces it — and when used, it must always pair `autocast(dtype=torch.float16)` with `GradScaler` (scale → unscale before clip → step → update), keeping norms/loss in fp32. **`bf16` is unavailable on Pascal and must be guarded to raise a clear error on P100** so it can never be selected by accident. CPU path is always fp32 (AMP auto-disabled in `RuntimeConfig`). Also: skip `torch.compile` on P100 (poor Pascal codegen, no benefit at this scale); `F.scaled_dot_product_attention(is_causal=True)` is allowed as a math primitive / correctness oracle (the fused FlashAttention backend won't engage on Pascal and falls back to the math backend — correct, just not fast).

### Expected Features

This is an engineering-correctness feature landscape: a feature is "table stakes" if its absence makes a reviewer doubt the implementation is correct or self-built. The full table-stakes set must ship; differentiators should be chosen *few and done excellently* once the core works.

**Must have (table stakes):**
- **From-scratch byte-level BPE** (train/encode/decode) + **round-trip correctness test** + **atomic special tokens (EOS)** — the core "from scratch" proof; sizes the model via `vocab_size`.
- **Bigram baseline + tests** — de-risks/validates the training-eval-sampling harness *before* the transformer exists.
- **From-scratch GPT decoder (~10–15M):** causal multi-head attention (mask before softmax, `1/sqrt(d_head)` scaling), learned positional embeddings, pre-norm blocks + residuals + GELU MLP, final LayerNorm, **weight tying**, **exact param count** — plus per-component tests.
- **Training loop:** AdamW (`wd=0.1` on 2D weights only, `betas=(0.9,0.95)`), warmup + cosine decay, gradient clipping (`1.0`), loss logging, **held-out validation loss**, and **checkpointing + exact resumability** (Kaggle-survivable).
- **Pretrain on TinyStories to coherent generation** — the visceral proof.
- **Generation:** greedy/temperature/top-k, max-length + EOS stop, context cropping to `block_size` — shared `generate()` used by tests, notebook, and demo.
- **Evaluation:** perplexity (`exp(val_loss)`) + curated qualitative samples.
- **Gradio CPU demo + `demo.ipynb`** (curves, samples, param count) + **per-component unit tests** + **reproducible env** (`requirements.txt`, seeds, device-agnostic) + **document-as-we-go technical writeup**.

**Should have (differentiators — pick a few, do them excellently):**
- **Clean module boundaries** (strongest cheap differentiator — do from the start, not as cleanup).
- **Overfit-a-single-batch** and **causality / no-future-leak** tests (cheap, high-signal, rarely seen in student work).
- **2–3 architectural / LR ablations** with a comparison table; **top-p (nucleus) sampling**; **throughput/FLOP + tokenizer compression-ratio reporting**; annotated loss curves; reproducibility hardening (config-in-checkpoint, git SHA, seeds).

**Defer (Milestone 2+ — explicitly out of scope):**
- **LoRA adapters**, **EWC continual learning**, **conversational fine-tuning (DailyDialog/PersonaChat)**, personalization / weight-memory demos. Other scope traps to deliberately avoid in M1: scaling beyond ~15M / multi-GPU, HF transformers/PEFT, RAG/vector stores, RLHF/DPO, KV-cache as a *training* concern, and hyperparameter sweep frameworks.

### Architecture Approach

A nanoGPT-style decoder constrained by three project realities: every component is unit-tested (so module boundaries must be testable in isolation), one codebase trains on P100 and infers on CPU (so device/AMP is centralized), and M2 adds LoRA/EWC (so two seams stay open). The contract is the installable package; notebooks and scripts are disposable thin wiring. The model is pure (`forward(idx, targets=None) -> (logits, loss)`); all state lives in `training/`. Checkpoints are self-describing dicts (`{model, optimizer, model_config, step, val_loss, rng}`) so the laptop reconstructs the architecture from the file alone and resume is exact.

**Major components:**
1. **`tokenizer/`** — from-scratch byte-level BPE; train/encode/decode; serialize vocab+merges as a frozen artifact consumed everywhere.
2. **`data/`** — encode corpus once → flat `uint16` memmap; random-offset batch sampler returning device-placed `(x, y)`.
3. **`model/`** — pure `nn.Module`s split one-file-per-concept (`bigram`, `embeddings`, `attention`, `mlp`, `block`, `gpt`); **named `nn.Linear` projections** (LoRA seam); no device/training logic.
4. **`training/`** — the one place AMP, optimizer, LR schedule, clipping, eval, and checkpoint/resume live; loss routes through `assemble_loss(... extra_penalties=())` (EWC seam).
5. **`generation/`** — stateless `generate(model, ids, cfg)` with temperature/top-k, EOS stop, and `block_size` context cropping.
6. **`config/`** — typed dataclasses (`ModelConfig` etc., serialized into checkpoints) plus `RuntimeConfig` (device + AMP, resolved per-environment, never serialized).

**Two M2 design seams (cheap M1 acceptance criteria — DESIGN FOR, DO NOT BUILD):**
- **Seam A (LoRA):** every adaptable matmul in `attention.py`/`mlp.py` is a **named `nn.Linear`** called as a module (not fused custom ops, not `F.linear` on bare weights), with stable names (`attn_qkv`, `attn_proj`, `mlp_fc`, `mlp_proj`). *M1 acceptance: every adaptable matmul is a named `nn.Linear`. That's it — no rank params, no wrapper, no freezing.*
- **Seam B (EWC):** loss goes through `assemble_loss` with an **empty** penalty list, the loop keeps a model reference able to iterate `named_parameters()`, and **checkpoints are open dicts** (extra keys allowed for future Fisher / `theta_star`). *M1 acceptance: loss routed through `assemble_loss(... extra_penalties=())`; checkpoints are dicts. Do not compute Fisher, store snapshots, or add lambda.*

### Critical Pitfalls

1. **Causal-mask silent bug (HIGHEST severity).** Backwards `triu`/`tril`, masking *after* softmax, `+inf` instead of `-inf`, or a mask not sliced to actual `T` lets position `t` attend to the future → train loss craters toward ~0 while generation is gibberish; the run is *unsalvageable* and must be retrained. **Avoid:** keep `tril`, set masked scores to `-inf` *before* softmax, register the mask as a `block_size` buffer and slice `mask[:T,:T]` every forward, and ship a **causality-perturbation test** (changing token `t` cannot change logits at positions `< t`).
2. **Kaggle 30h-week / 12h-session / `/kaggle/working`-wipe + resumability (HIGHEST leverage ops).** `/kaggle/working` is wiped between sessions; interactive sessions die when the tab closes. **Avoid:** checkpoint every ~15–30 min (model+optimizer+scheduler+scaler+step+RNG+data position), make resume *exact* (continues the same loss trajectory, not a fresh run), **persist checkpoints across sessions via a versioned Kaggle Dataset**, use "Save & Run All (Commit)" for headless runs, and assert `torch.cuda.is_available()` + "Tesla P100" in cell 1. Resumability is a prerequisite for fluency, not a nicety.
3. **Tokenizer correctness — byte-level + deterministic merges + atomic special tokens.** Char-level BPE breaks on TinyStories' smart quotes/emoji; non-deterministic merge ordering makes `encode()` disagree with training; special tokens routed through merges get split. A tokenizer change *invalidates a trained model* (recovery cost HIGH). **Avoid:** byte-level base vocab (256 bytes, no `<unk>`), store `pair->rank` and replay lowest-rank-first, deterministic tie-breaks, reserve special-token IDs *outside* the merge algorithm, insert EOS between documents, and round-trip test on emoji/quotes/newlines.
4. **CPU demo portability.** The demo must load and generate on a laptop CPU **offline**, but optimizer/scaler/CUDA-tied checkpoints fail or bloat, and fp16-on-CPU is slow/unsupported. **Avoid:** ship a **slim fp32 inference checkpoint** (state_dict + config + tokenizer, no optimizer/scaler), load with `map_location="cpu"` / `weights_only=True`, and **test the offline laptop generate path mid-project** (Gradio `share=False`, localhost). (A KV-cache in `generate` is the recommended latency fix — but FEATURES.md treats KV-cache as out of M1 scope as a *training* concern; reconcile during demo-phase planning: add it only if measured CPU latency demands it.)
5. **Also high-severity (Model/Training phases):** missing `1/sqrt(d_head)` scaling (softmax saturates, training stalls); non-GPT-2 init / missing residual-scaled init (`0.02/sqrt(2·n_layer)` on `c_proj`) → instability/NaNs; post-norm instead of pre-norm + missing final `ln_f`; weight-tying done by transpose/copy (drifts, mis-counts params); forgotten/misordered `zero_grad` under gradient accumulation; train/val leakage (split by *document*, not random shuffle).

## Implications for Roadmap

The build order is **dependency-forced** — the tokenizer sizes the model, the loop must be proven on the bigram before the transformer, and the demo is a terminal consumer of a trained checkpoint. Suggested phases:

### Phase 1: Scaffolding & Reproducible Environment
**Rationale:** Everything imports `config/` and `RuntimeConfig`; the installable package + dual-env portability is the foundation the whole project stands on. Kaggle ops (CUDA assert, checkpoint/resume infra, dataset persistence, seeding) are the single highest-leverage ops investment and must exist before any long run.
**Delivers:** `src/personacore/` installable package, `config/` (dataclasses + `RuntimeConfig` with fp32-default / CPU-AMP-off / **bf16-guard-errors-on-Pascal**), seed+config harness, `requirements.txt`, Kaggle cell-1 CUDA/P100 assert, checkpoint/resume skeleton (open-dict).
**Addresses:** reproducible environment (table stakes).
**Avoids:** Pitfall 2 (Kaggle wipe/resume), GPU-not-enabled, reproducibility, bf16-on-Pascal.

### Phase 2: From-Scratch BPE Tokenizer
**Rationale:** The token stream defines `vocab_size`, which sizes the embedding/LM-head and thus param count; lock it before anything trainable (re-tokenizing invalidates checkpoints). Independent of the model.
**Delivers:** byte-level BPE train/encode/decode, atomic special tokens / reserved EOS, serialized frozen `tokenizer.json`, round-trip + determinism tests (`tiktoken` as oracle).
**Avoids:** the tokenizer pitfall family (merge determinism, byte-level, special-token/EOS).

### Phase 3: Bigram Baseline + Harness
**Rationale:** De-risks the *harness* (batching, loss, logging, sampling) independent of attention bugs. If the bigram trains and samples, a later loss problem is almost certainly in the transformer, not the loop.
**Delivers:** `model/bigram.py` + test; smoke-tests the model→loss→logits contract.

### Phase 4: GPT Internals (from scratch)
**Rationale:** The central "I built a transformer" claim; the densest cluster of silent correctness pitfalls. Build embeddings → attention → mlp → block → gpt, testing each.
**Delivers:** causal MHA (scaled, masked-before-softmax, sliced), pos emb, pre-norm blocks + final `ln_f`, GPT-2 init incl. residual-scaled init, **named `nn.Linear` projections (LoRA seam)**, weight tying, param count + tests.
**Avoids:** Pitfalls 4–9 (mask, scaling, init, norm placement, positional overflow, weight tying).

### Phase 5: Training Loop (resumable)
**Rationale:** Built and validated against the bigram (overfit-one-batch → loss→0) *before* the full GPT, so the checkpoint/AMP/`assemble_loss` machinery is proven; then the real transformer swaps in.
**Delivers:** AdamW + warmup/cosine + grad-clip, **fp32-default training** (fp16 AMP+GradScaler only if 16GB forces it), val-loss eval (`eval()`+`no_grad()`), CSV logging, **exact resumable checkpointing**, `assemble_loss(... extra_penalties=())` (**EWC seam**).
**Avoids:** Pitfalls 10–13 (AMP NaN/P100 misuse, LR/warmup/clip, zero_grad/accumulation, eval mode).

### Phase 6: TinyStories Pretraining
**Rationale:** Terminal data step producing the trained checkpoint everything downstream consumes; the visceral proof the LM works. Requires resumable training + frozen tokenizer.
**Delivers:** memmap data prep (EOS between docs, **document-level train/val split**), full Kaggle P100 run to coherent generation, dataset-persisted checkpoints.
**Avoids:** train/val leakage, corpus-EOS handling, quota loss.

### Phase 7: Generation / Sampling
**Rationale:** Shared `generate()` powers tests, notebook, and demo (DRY). Needs a trained-ish model.
**Delivers:** greedy/temperature/top-k (+top-p differentiator), max-length + EOS stop, `block_size` context cropping, seeded-determinism tests.
**Avoids:** never-stops generation, positional overflow at inference.

### Phase 8: Evaluation
**Rationale:** Quantitative + qualitative proof of the trained model.
**Delivers:** perplexity, curated samples, optional 2–3 ablations + throughput/compression-ratio reporting.

### Phase 9: Demo (Gradio CPU + demo.ipynb)
**Rationale:** Pure composition over the generation API and a trained checkpoint; the tangible portfolio artifacts. Must be proven offline on a laptop.
**Delivers:** slim fp32 CPU-loadable checkpoint, Gradio streaming chat (`share=False`, localhost, temp/top-k sliders), `demo.ipynb` (curves, samples, param count).
**Avoids:** Pitfall 4 (CPU portability/slow inference), Gradio internet leak.

### Phase 10: Technical Writeup
**Rationale:** Document-as-we-go; the portfolio narrative *is* the value. Finalized after results exist.
**Delivers:** architecture, hyperparams, param count, annotated curves, samples, decisions-and-why, reproducibility note.

### Phase Ordering Rationale
- **Tokenizer before everything trainable** (it sizes the model; a later change invalidates checkpoints). **Scaffolding/resume infra before any long run** (Kaggle wipes `/kaggle/working`; an un-resumable loop loses weeks). **Bigram + harness before GPT** (isolates loop bugs from model-math bugs). **Generation/demo/writeup are terminal consumers** of a trained checkpoint and cannot complete until pretraining reaches coherence.
- Grouping follows the clean package boundaries (`tokenizer/`, `model/`, `training/`, `generation/`) so each phase is independently testable — directly serving the per-component-test deliverable.
- The two M2 seams (named `nn.Linear` in Phase 4; `assemble_loss` + open-dict checkpoints in Phases 1/5) are folded in as zero-cost acceptance criteria, so M2 is additive rather than a refactor.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 6 (Pretraining):** the one empirically uncertain area — exact LR/batch/steps/coherence-per-quota on P100 is unmeasured; needs a small calibration/throughput study (estimate tokens/sec → size the run to finish or reach a clean checkpoint within the 30h budget).
- **Phase 9 (Demo):** reconcile the KV-cache tension (PITFALLS recommends it for usable CPU latency; FEATURES marks it out-of-M1-scope) — decide based on *measured* CPU latency; also confirm Gradio 5 streaming + fully-offline launch behavior.

Phases with standard, well-documented patterns (skip research-phase):
- **Phases 1–5, 7, 8** — nanoGPT/GPT-2 conventions are HIGH-confidence and verified; the work is correctness + tests, not discovery.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core stack verified against official PyTorch docs/PyPI; the load-bearing P100/Pascal `cu126`-vs-`cu128+` wheel fact verified against the PyTorch issue tracker. |
| Features | HIGH | Engineering-correctness feature set for small GPTs is stable, well-documented; verified against nanoGPT conventions + the TinyStories paper. |
| Architecture | HIGH | nanoGPT structure, device-agnostic `torch.amp` API, LoRA module-injection, and EWC Fisher-penalty seam all verified against current docs/reference impls. |
| Pitfalls | HIGH | Core ML correctness pitfalls verified against nanoGPT source / GPT-2 conventions; Kaggle/P100 ops facts against Kaggle docs + NVIDIA specs. |

**Overall confidence:** HIGH

### Gaps to Address
- **Empirical pretraining hyperparameters / coherence-per-quota (P100):** unmeasured. Resolve via a short Phase-6 calibration run (throughput benchmark → run-sizing within 30h). The P100 fp16-speedup figure is also model-dependent and unmeasured — moot given the fp32-default decision.
- **KV-cache in the demo:** cross-document tension (PITFALLS vs FEATURES). Resolve at Phase-9 planning on *measured* CPU latency; write the `generate` API so a cache can be added without an interface change.
- **Exact Kaggle quota behavior:** the 30h/week is a "floating" quota and the session cap is ~12h (some docs say ~9h) — plan conservatively to the 30h/12h figures and verify `torch.__version__` + device in-notebook each session.

## Sources

### Primary (HIGH confidence)
- karpathy/nanoGPT (`model.py`, `train.py`, `sample.py`) — reference structure, weight tying, GPT-2 + residual-scaled init, pre-norm + `ln_f`, memmap data, checkpoint-resume, context cropping.
- PyTorch docs — install matrix / CUDA support; `torch.amp` device-agnostic `autocast`/`GradScaler` (fp16 needs scaler; bf16 only Ampere+); AMP recipe.
- pytorch/pytorch#157517 — Pascal/`sm_60` dropped from `cu128`+ wheels, retained in `cu126` (load-bearing P100 fact).
- TinyStories paper (Eldan & Li, 2023, arXiv 2305.07759) — sub-10M models reach coherent English; supports 10–15M target + emergence note.
- Kaggle Efficient GPU Usage docs + product-feedback — ~30h/week floating GPU quota, ~12h session cap, `/kaggle/working` wiped between sessions.
- NVIDIA mixed-precision docs — P100 = Pascal CC 6.0, no Tensor Cores, no bf16, AMP needs CC ≥ 7.0 for real speedup.
- HF TinyStoriesV2-GPT4 dataset (direct `resolve/main` URLs) + Gradio 5 changelog/blog (ChatInterface streaming, local launch).
- `.planning/PROJECT.md` — M1 scope boundary, dual-environment constraint, from-scratch requirement, explicit M2 deferrals.

### Secondary (MEDIUM confidence)
- Community TinyStories-from-scratch replications (HF model cards / write-ups) — 8M-class models train to coherent stories in hours on a small GPU (feasibility within free-tier budget).
- minbpe / tiktoken byte-level + atomic-special-token / lowest-rank-first conventions.
- LoRA-from-scratch reference impls — recursive named-`nn.Linear` injection pattern.

### Tertiary (LOW confidence)
- Exact P100 fp16 speedup figure and exact Kaggle session-cap hours (9h vs 12h) — plan conservatively; verify in-notebook.

---
*Research completed: 2026-06-04*
*Ready for roadmap: yes*
