# Roadmap: PersonaCore — Milestone 1

## Overview

Milestone 1 builds a correct, from-scratch ~10–15M-parameter GPT-style language model in pure PyTorch, pretrained on TinyStories to coherent generation, and shipped with an offline Gradio CPU chat demo, a research notebook, per-component unit tests, and a document-as-we-go technical writeup. The build order is dependency-forced: scaffolding and Kaggle resume infra must exist before any long run; the tokenizer must lock `vocab_size` before the model is sized; a bigram baseline proves the training/checkpoint/sampling harness before the real transformer math is risked; only then does the GPT, pretraining, generation, evaluation, and demo follow. As a vertical MVP, Phase 3 stands up the thin end-to-end slice (tokenize → train → sample → see output) on a trivial model, then later phases swap in and deepen the real GPT toward fluent generation. Two cheap structural seams (named `nn.Linear` projections; loss routed through `assemble_loss(...)` + open-dict checkpoints) are folded in as M1 acceptance criteria so the Milestone-2 weight-memory work (LoRA + EWC) is additive rather than a rewrite — LoRA/EWC/personalization themselves are explicitly out of scope here.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Scaffolding & Reproducible Environment** - Installable package, RuntimeConfig (fp32-default, bf16-guard), Kaggle checkpoint/resume infra, GPU preflight, seeds (completed 2026-06-04)
- [x] **Phase 2: From-Scratch BPE Tokenizer** - Byte-level BPE train/encode/decode with deterministic merges, atomic EOS, locked vocab_size, round-trip tests (completed 2026-06-04)
- [ ] **Phase 3: Bigram Baseline & Training Harness** - Thin end-to-end slice: bigram trains/samples through a resumable loop with the assemble_loss + open-dict-checkpoint seams proven
- [ ] **Phase 4: GPT Transformer Decoder** - From-scratch ~10–15M GPT (causal MHA, pre-norm blocks, weight tying, GPT-2 init) with silent-bug gates and the LoRA seam
- [ ] **Phase 5: TinyStories Pretraining** - Memmap data prep, full Kaggle P100 run to coherent generation, trained checkpoint + recorded curves
- [ ] **Phase 6: Generation & Sampling** - Shared generate() with greedy/temperature/top-k/top-p, EOS stop, context cropping, determinism tests
- [ ] **Phase 7: Evaluation** - Held-out perplexity, curated qualitative samples, 2–3 ablations with a comparison table
- [ ] **Phase 8: Demo & Writeup** - Slim fp32 CPU checkpoint, offline Gradio chat, demo.ipynb, consolidated test suite and technical writeup

## Phase Details

### Phase 1: Scaffolding & Reproducible Environment

**Goal**: A reproducible, installable PersonaCore package that imports identically on Kaggle, laptop, and pytest, with centralized device/precision handling and Kaggle-survivable checkpoint/resume infrastructure in place before any long training run.
**Mode:** standard
**Depends on**: Nothing (first phase)
**Requirements**: ENV-01, ENV-02, ENV-03, ENV-04, ENV-05, ENV-06, QA-02
**Success Criteria** (what must be TRUE):

  1. `pip install -e .` succeeds and `import personacore` resolves identically from a Kaggle notebook, the laptop, and a pytest run
  2. `RuntimeConfig` resolves device and precision with fp32 as the default, AMP auto-disabled on CPU, and selecting bf16 on a Pascal/P100 path raises a clear error
  3. A kill-and-resume test against the open-dict checkpoint skeleton restores model + optimizer + scheduler + step + RNG and continues the same trajectory (not a fresh run)
  4. A Kaggle cell-1 preflight asserts CUDA is active and the device is a Tesla P100 (fails loudly otherwise), and seeds are set across `random`/`numpy`/`torch` with the config + git SHA recorded
  5. `CLAUDE.md` and `requirements.txt` document the project structure and the Kaggle-train / laptop-CPU-infer workflow, reproducible from a clean virtual env

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Installable package (pyproject src-layout) + config layer (RuntimeConfig fp32/bf16-guard, ModelConfig, TrainConfig) [ENV-01, ENV-02, ENV-03]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Runtime primitives: open-dict checkpoint/resume, seeding, git-SHA provenance, P100 preflight, CSV logger [ENV-04, ENV-05, QA-02]
- [x] 01-03-PLAN.md — Dev tooling: Makefile, CPU-only GitHub Actions CI (Python 3.11), CLAUDE.md workflow docs [ENV-06, ENV-01, ENV-02]

### Phase 2: From-Scratch BPE Tokenizer

**Goal**: A correct, from-scratch byte-level BPE tokenizer whose `vocab_size` is locked before any model is sized, so a later tokenizer change can never invalidate a trained checkpoint.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: TOK-01, TOK-02, TOK-03, TOK-04, TOK-05
**Success Criteria** (what must be TRUE):

  1. The tokenizer trains byte-level BPE merges from a corpus and replays them deterministically (lowest-rank-first), producing identical IDs across runs and sessions
  2. `decode(encode(x)) == x` round-trips over a tricky-string test set (emoji, smart quotes, newlines, multi-byte UTF-8) with no `<unk>` ever emitted
  3. Special tokens are atomic with a single shared EOS id stored in config — never split or produced by merges
  4. The tokenizer saves and loads as a frozen artifact and exposes a locked `vocab_size` ready to size the model
  5. A from-scratch-vs-reference equivalence test passes using tiktoken/HF as a test-only oracle (never a runtime dependency)

**Plans**: 3 plans
Plans:

**Wave 1**

- [x] 02-01-PLAN.md — Lock vocab_size=8192 + eos_id, declare regex(core)/tiktoken([dev]) deps, Wave 0 fixtures + 5 red TOK test files [TOK-01..TOK-05]

**Wave 2** *(blocked on Wave 1)*

- [x] 02-02-PLAN.md — From-scratch BPE core: GPT-2 pre-tok, top-pinned special registry, deterministic train + lowest-rank encode/decode + atomic EOS [TOK-01, TOK-02, TOK-03]

**Wave 3** *(blocked on Wave 2)*

- [x] 02-03-PLAN.md — JSON freeze/load artifact, production tokenizer.json train script, tiktoken gpt2 equivalence oracle [TOK-04, TOK-05]

### Phase 3: Bigram Baseline & Training Harness

**Goal**: A working thin end-to-end slice — tokenize → train → sample → see output — proven on a trivial bigram model, so the training loop, checkpoint/resume, AMP toggle, eval, and the EWC `assemble_loss` seam are all validated before the real transformer math is risked.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: MODEL-01, TRAIN-01, TRAIN-02, TRAIN-03, TRAIN-04, TRAIN-05, TRAIN-06
**Success Criteria** (what must be TRUE):

  1. A from-scratch bigram language model trains end-to-end through the harness and produces sampled output, exercising the model→loss→logits contract
  2. The overfit-a-single-batch test drives loss toward zero, proving harness correctness independent of attention
  3. The training loop runs AdamW + warmup/cosine LR + gradient clipping + configurable gradient accumulation, with fp32 by default and an optional fp16-AMP+GradScaler path (unscale-before-clip discipline) available only as a memory measure
  4. A document-level train/val split with periodic `eval()`+`no_grad()` validation loss runs with no train/val leakage, and CSV+matplotlib logging reproduces the loss curve across a restart
  5. Loss is assembled via `assemble_loss(..., extra_penalties=())` with an empty penalty list and checkpoints are open dicts (M2 EWC seam — plumbing only, no Fisher/penalty computed)

**Plans**: 4 plans
Plans:

**Wave 1**

- [ ] 03-01-PLAN.md — Wave-0 RED test scaffold + committed corpus fixture (failing tests for all 7 seams) [MODEL-01, TRAIN-01..06]

**Wave 2** *(blocked on Wave 1)*

- [ ] 03-02-PLAN.md — Model->loss slice: BigramLanguageModel forward (logits, loss) contract + assemble_loss EWC seam [MODEL-01, TRAIN-06]
- [ ] 03-03-PLAN.md — Data + schedule slice: doc-level no-leakage split + get_batch + warmup/cosine LambdaLR [TRAIN-03, TRAIN-01]

**Wave 3** *(blocked on Wave 2)*

- [ ] 03-04-PLAN.md — Train-loop slice: AMP/accum/clip ordering + eval + CSV + resume curve + overfit gate + thin train_bigram.py [TRAIN-01, TRAIN-02, TRAIN-04, TRAIN-05, TRAIN-06]

### Phase 4: GPT Transformer Decoder

**Goal**: A from-scratch ~10–15M-parameter GPT decoder — the central "I built a transformer" claim — that drops into the already-proven harness, with the densest cluster of silent correctness bugs gated by tests and the LoRA seam left open.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: MODEL-02, MODEL-03, MODEL-04, MODEL-05, MODEL-06, MODEL-07
**Success Criteria** (what must be TRUE):

  1. The GPT decoder (causal multi-head self-attention masked before softmax and scaled by 1/√d_head, GELU MLP, pre-norm blocks + residuals, learned positional embeddings, final `ln_f`) swaps into the existing loop and overfits a single batch
  2. The causality-perturbation test passes (changing token `t` cannot change logits at positions `< t`), guarding the silent causal-mask bug
  3. Weight tying is a true shared tensor verified by a `data_ptr()` tensor-identity test, and the per-tensor init-std check confirms GPT-2-style init including residual-scaled `c_proj`
  4. Exact parameter counting (tied weights counted once) reports a configuration that hits the ~10–15M target
  5. Every adaptable projection is a named `nn.Linear` called as a module (M2 LoRA seam — naming only, no wrapper, no rank params, no freezing)

**Plans**: TBD

### Phase 5: TinyStories Pretraining

**Goal**: The trained checkpoint everything downstream consumes — the visceral proof the LM works — produced by a full, resumable Kaggle P100 run on TinyStories to coherent, fluent generation.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: PRE-01, PRE-02, PRE-03
**Success Criteria** (what must be TRUE):

  1. TinyStories is obtained, encoded once into a `uint16` memmap with one EOS between documents, and pinned/persisted as a versioned Kaggle Dataset with a document-level train/val split (no leakage)
  2. A full Kaggle P100 run trains the GPT to fluent, coherent generation, surviving session kills via dataset-persisted resumable checkpoints within the 30h/week budget
  3. A trained checkpoint is produced, and final/val perplexity plus training curves are recorded for the writeup

**Plans**: TBD
**Research**: phase-level (empirical LR/batch/steps and coherence-per-quota on P100 are unmeasured — needs a short throughput/calibration study to size the run within the 30h/12h budget)

### Phase 6: Generation & Sampling

**Goal**: A single shared `generate()` that powers tests, the notebook, and the demo — autoregressive decoding with the full sampling toolkit, correct stopping, and context-window safety.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: GEN-01, GEN-02, GEN-03
**Success Criteria** (what must be TRUE):

  1. One shared `generate()` supports greedy, temperature, top-k, and top-p sampling
  2. Generation stops on EOS, trims the trailing token, respects max-length, and crops context to the last `block_size` tokens so generating past `block_size` never crashes
  3. Generation unit tests pass for output shape, determinism under fixed seed + greedy decoding, and EOS-stop behavior

**Plans**: TBD

### Phase 7: Evaluation

**Goal**: Quantitative and qualitative proof of the trained model, plus the differentiating ablation study that lifts this above a student clone.
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: EVAL-01, EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):

  1. Perplexity is computed and reported on a held-out set
  2. Curated qualitative generation samples are captured for the writeup
  3. 2–3 architecture/LR ablations are run and presented in a comparison table

**Plans**: TBD

### Phase 8: Demo & Writeup

**Goal**: The tangible portfolio artifacts — an offline laptop-CPU Gradio chat demo, a narrated research notebook, a green per-component test suite, and the consolidated technical writeup — proving the from-scratch model runs on-device and reads as rigorous.
**Mode:** mvp
**Depends on**: Phase 7
**Requirements**: DEMO-01, DEMO-02, DEMO-03, DOC-01, QA-01, QA-02
**Success Criteria** (what must be TRUE):

  1. A slim fp32 inference checkpoint (no optimizer state, safe `weights_only` load) loads and generates on laptop CPU, verified by an offline test
  2. A Gradio chat UI (`gr.ChatInterface`, `share=False`, localhost) runs the model on laptop CPU fully offline with temperature/top-k controls
  3. `demo.ipynb` reads the CSV log to show training curves, sampling, and the exact parameter count as a research artifact
  4. The full per-component test suite (tokenizer, model, training, generation) runs green via pytest, and reproducibility discipline holds (config saved with each checkpoint, seeds fixed, git SHA recorded)
  5. A polished technical writeup (README/report) documenting design decisions, architecture, training, and results is consolidated from the document-as-we-go notes

**Plans**: TBD
**UI hint**: yes
**Research**: phase-level (reconcile the KV-cache tension on measured CPU latency; confirm Gradio 5 streaming + fully-offline launch behavior)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffolding & Reproducible Environment | 3/3 | Complete   | 2026-06-04 |
| 2. From-Scratch BPE Tokenizer | 3/3 | Complete   | 2026-06-04 |
| 3. Bigram Baseline & Training Harness | 0/4 | Not started | - |
| 4. GPT Transformer Decoder | 0/TBD | Not started | - |
| 5. TinyStories Pretraining | 0/TBD | Not started | - |
| 6. Generation & Sampling | 0/TBD | Not started | - |
| 7. Evaluation | 0/TBD | Not started | - |
| 8. Demo & Writeup | 0/TBD | Not started | - |
