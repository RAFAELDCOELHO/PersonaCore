# PersonaCore — Requirements

**Milestone 1: Foundation — a from-scratch language model.**
Scope: a correct, from-scratch ~10–15M param GPT-style LM (BPE tokenizer, transformer, training loop) pretrained on TinyStories to fluent generation, with a Gradio demo, a research notebook, per-component unit tests, and a documented technical writeup. Personalization (LoRA + EWC) is Milestone 2.

---

## v1 Requirements (Milestone 1)

### Environment & Scaffolding
- [x] **ENV-01**: Repo is an installable package (`pip install -e .`) so `personacore` imports identically on Kaggle, laptop, and pytest
- [x] **ENV-02**: Reproducible environment via `requirements.txt` and a documented virtual-env setup, runnable on Kaggle P100 (training) and laptop CPU (inference)
- [x] **ENV-03**: A single `RuntimeConfig` centralizes device/precision handling — fp32 by default, bf16 guarded to error on Pascal/P100
- [x] **ENV-04**: Kaggle checkpoint/resume infrastructure: full training state (model + optimizer + scheduler + step + RNG) saves to `/kaggle/working` and resumes exactly after a session kill
- [x] **ENV-05**: A preflight check asserts GPU/Pascal-compatible CUDA is active before any long training run, and seeds are set for reproducibility
- [x] **ENV-06**: `CLAUDE.md` documents project structure, setup, and the Kaggle/local workflow

### Tokenizer (from scratch)
- [ ] **TOK-01**: Byte-level BPE tokenizer implemented from scratch — train merges from a corpus, with deterministic lowest-rank-first merge replay
- [ ] **TOK-02**: `encode`/`decode` with verified round-trip correctness (decode(encode(x)) == x) over unit tests
- [ ] **TOK-03**: Atomic special-token handling including a single shared EOS id stored in config
- [ ] **TOK-04**: Tokenizer is serializable (save/load) and `vocab_size` is locked before model sizing
- [ ] **TOK-05**: A from-scratch-vs-reference equivalence test (tiktoken/HF as a test-only oracle, never a runtime dependency)

### Model (from scratch)
- [ ] **MODEL-01**: Bigram language-model baseline from scratch, used to de-risk the training/sampling harness before attention exists
- [ ] **MODEL-02**: GPT-style decoder (~10–15M params): causal multi-head self-attention (masked before softmax, scaled by √d_k), MLP blocks, pre-norm LayerNorm, learned positional embeddings
- [ ] **MODEL-03**: Weight tying between token embedding and output head, verified by tensor-identity test
- [ ] **MODEL-04**: GPT-2-style weight initialization, verified by per-tensor init-std check
- [ ] **MODEL-05**: Exact parameter counting reported; configuration hits the ~10–15M target
- [ ] **MODEL-06**: Causality perturbation unit test (future tokens cannot affect earlier logits) guarding the silent causal-mask bug
- [ ] **MODEL-07** *(M2 seam)*: Every adaptable projection is a named `nn.Linear` so LoRA can later wrap it without a model rewrite

### Training
- [ ] **TRAIN-01**: Training loop with AdamW, warmup + cosine LR schedule, gradient clipping, and configurable gradient accumulation
- [ ] **TRAIN-02**: fp32 training by default; optional fp16 AMP + GradScaler path available only as a memory measure (correct scale→unscale-before-clip→step discipline)
- [ ] **TRAIN-03**: Train/validation split with periodic validation loss; no train/val leakage
- [ ] **TRAIN-04**: Offline experiment logging (CSV + matplotlib) that survives restarts; loss curves reproducible from the log
- [ ] **TRAIN-05**: Overfit-a-single-batch test passes (harness correctness gate)
- [ ] **TRAIN-06** *(M2 seam)*: Loss is assembled via an `assemble_loss(..., extra_penalties=())` seam and checkpoints are open dicts, so EWC can later add a Fisher penalty without touching the loop

### Pretraining
- [ ] **PRE-01**: TinyStories data is obtained, encoded once into a `uint16` memmap, and pinned/persisted as a versioned Kaggle Dataset
- [ ] **PRE-02**: The model is pretrained on TinyStories to fluent, coherent generation, producing a trained checkpoint
- [ ] **PRE-03**: Final/val perplexity and training curves are recorded for the writeup

### Generation
- [ ] **GEN-01**: A single shared `generate()` supporting greedy, temperature, top-k, and top-p sampling
- [ ] **GEN-02**: EOS-aware stopping and max-length handling
- [ ] **GEN-03**: Generation unit tests (shape, determinism under fixed seed/greedy, EOS stop)

### Evaluation
- [ ] **EVAL-01**: Perplexity computed on a held-out set
- [ ] **EVAL-02**: Curated qualitative generation samples captured
- [ ] **EVAL-03**: 2–3 architecture/LR ablations with a comparison table (differentiator / polish phase)

### Demo
- [ ] **DEMO-01**: Gradio local web UI (`gr.ChatInterface`, offline `share=False`) runs the model on laptop CPU
- [ ] **DEMO-02**: Slim fp32 inference checkpoint (no optimizer state, safe `weights_only` load) loads and generates on CPU, verified by an offline test
- [ ] **DEMO-03**: `demo.ipynb` research artifact showing training curves and sampling, reading from the CSV log

### Documentation & Quality
- [ ] **DOC-01**: Polished technical writeup (README/report) covering design decisions, architecture, training, and results — written as we go
- [ ] **QA-01**: Per-component unit tests (tokenizer, model, training, generation) run green via pytest as a first-class deliverable
- [x] **QA-02**: Reproducibility discipline: config saved with each checkpoint, seeds fixed, git SHA recorded

---

## v2 Requirements (Milestone 2 — deferred)

- [ ] Conversational fine-tuning on DailyDialog + PersonaChat (curriculum stage 2)
- [ ] From-scratch LoRA adapters wrapping the named `nn.Linear` layers
- [ ] EWC continual learning with Fisher-information penalty via the `assemble_loss` seam
- [ ] Teach-then-recall (clean-room) personalization demo — memory lives in weights, not the prompt
- [ ] No-forgetting (EWC A/B vs naive fine-tuning) demo
- [ ] Weight-delta heatmaps and forgetting-curve visualizations
- [ ] KV-cache for CPU inference latency (introduce only if the demo feels slow)

## Out of Scope (with reasoning)

- **HuggingFace transformers/PEFT model or adapter code** — the portfolio value is demonstrated from-scratch depth
- **External AI APIs / paid compute** — zero budget; privacy and on-device are design requirements
- **Databases, vector stores, RAG, external memory files** — memory must live in weights by design
- **Scaling beyond ~10–15M params / multi-GPU** — outside the Kaggle free-tier budget
- **bf16 / Tensor-Core optimizations** — unavailable on P100 (Pascal); guarded to error

---

## Traceability

Every v1 (Milestone 1) requirement maps to exactly one phase. Coverage: 35/35.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01 | Phase 1 | Complete |
| ENV-02 | Phase 1 | Complete |
| ENV-03 | Phase 1 | Complete |
| ENV-04 | Phase 1 | Complete |
| ENV-05 | Phase 1 | Complete |
| ENV-06 | Phase 1 | Complete |
| TOK-01 | Phase 2 | Pending |
| TOK-02 | Phase 2 | Pending |
| TOK-03 | Phase 2 | Pending |
| TOK-04 | Phase 2 | Pending |
| TOK-05 | Phase 2 | Pending |
| MODEL-01 | Phase 3 | Pending |
| TRAIN-01 | Phase 3 | Pending |
| TRAIN-02 | Phase 3 | Pending |
| TRAIN-03 | Phase 3 | Pending |
| TRAIN-04 | Phase 3 | Pending |
| TRAIN-05 | Phase 3 | Pending |
| TRAIN-06 | Phase 3 | Pending |
| MODEL-02 | Phase 4 | Pending |
| MODEL-03 | Phase 4 | Pending |
| MODEL-04 | Phase 4 | Pending |
| MODEL-05 | Phase 4 | Pending |
| MODEL-06 | Phase 4 | Pending |
| MODEL-07 | Phase 4 | Pending |
| PRE-01 | Phase 5 | Pending |
| PRE-02 | Phase 5 | Pending |
| PRE-03 | Phase 5 | Pending |
| GEN-01 | Phase 6 | Pending |
| GEN-02 | Phase 6 | Pending |
| GEN-03 | Phase 6 | Pending |
| EVAL-01 | Phase 7 | Pending |
| EVAL-02 | Phase 7 | Pending |
| EVAL-03 | Phase 7 | Pending |
| DEMO-01 | Phase 8 | Pending |
| DEMO-02 | Phase 8 | Pending |
| DEMO-03 | Phase 8 | Pending |
| DOC-01 | Phase 8 | Pending |
| QA-01 | Phase 8 | Pending |
| QA-02 | Phase 1, Phase 8 | Complete |

**Cross-cutting note:** QA-02 (reproducibility discipline) is anchored in Phase 1 (the seed/config/git-SHA harness, config-in-checkpoint) and re-verified in Phase 8 (full-suite reproducibility check). QA-01 (per-component tests) and DOC-01 (writeup) are written incrementally per phase as success criteria but formally consolidated/owned in Phase 8.
