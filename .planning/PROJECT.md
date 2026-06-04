# PersonaCore

## What This Is

PersonaCore is a conversational AI assistant where **all** memory and personalization live in the model weights — no databases, no vector stores, no external files. The model learns who you are by updating its own parameters, making weight-based memory a privacy guarantee by design. The entire stack (GPT-style transformer decoder, BPE tokenizer, LoRA adapters, EWC continual learning) is built from scratch in PyTorch and runs fully on-device. It is an elite CS-undergraduate portfolio project intended to demonstrate deep ML fundamentals, a genuinely novel approach, and a working demo.

## Core Value

The novel claim must be true and demonstrable: **personalization lives in the weights, not in a prompt or a store** — and the from-scratch implementation must be correct enough to prove it. If everything else fails, the project must still show real ML depth built by hand.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Milestone 1: Foundation — a from-scratch language model. -->

- [ ] Project scaffolding: repo structure, `CLAUDE.md`, reproducible environment (`requirements.txt`, virtual env), runnable on Kaggle P100 and laptop CPU
- [ ] Bigram language model from scratch as a baseline foundation, with unit tests
- [ ] BPE tokenizer implemented from scratch (train/encode/decode), with unit tests
- [ ] GPT-style transformer decoder (~10–15M params) from scratch: attention, MLP, blocks, positional embeddings, with unit tests
- [ ] Training loop with checkpointing, loss logging, and resumability (Kaggle 30h/week-aware)
- [ ] Pretrain on TinyStories to fluent, coherent generation
- [ ] Text generation/sampling (temperature, top-k) with unit tests
- [ ] Gradio local web UI chat demo (on-device) plus `demo.ipynb` research artifact (training curves, sampling)
- [ ] Polished technical writeup documenting design decisions, architecture, and results (document-as-we-go)

### Out of Scope

<!-- Explicit boundaries. Deferred to Milestone 2 unless noted otherwise. -->

- LoRA adapters from scratch — **Milestone 2** (the novel weight-memory mechanism)
- EWC continual learning / catastrophic-forgetting prevention — **Milestone 2**
- Conversational fine-tuning on DailyDialog + PersonaChat — **Milestone 2** (M1 stops at TinyStories fluency)
- Teach-then-recall (clean-room) and no-forgetting (EWC A/B) demos — **Milestone 2** payoff
- Weight-delta heatmaps and forgetting-curve visualizations — **Milestone 2**
- HuggingFace PEFT / transformers model code — excluded by design; everything is from scratch
- External AI APIs during training — excluded by design (zero budget, privacy, on-device)
- Databases, vector stores, RAG, external memory files — excluded by design; memory must live in weights
- Scaling beyond ~10–15M params or multi-GPU training — out of scope given the Kaggle free-tier budget

## Context

- **Audience:** portfolio reviewers at the MIT/Stanford bar (admissions, research, recruiting) and the author. The work must read as rigorous, original, and self-implemented.
- **Two-milestone strategy:** De-risk the foundation before the novel claim. **Milestone 1** delivers a correct, from-scratch base language model with a working generation demo. **Milestone 2** delivers the differentiating weight-based memory (LoRA + EWC) and the research-narrative demos.
- **Curriculum plan (full project):** two-stage pretraining — TinyStories for base fluency, then DailyDialog + PersonaChat for conversational grounding. Milestone 1 covers only the TinyStories stage.
- **Dual-environment reality:** training runs on Kaggle (P100 16GB, 30h/week) via notebooks; the demo and inference must run on a laptop CPU. Code must be portable across both.
- **Engineering rigor is a theme:** per-component unit tests and a documented technical narrative are first-class deliverables, not afterthoughts — they are part of what makes this a portfolio-grade artifact.

## Constraints

- **Budget**: Zero — only Kaggle free-tier GPU (P100 16GB, 30h/week). No paid compute or APIs.
- **Tech stack**: Python + PyTorch only. No HuggingFace PEFT/transformers model code; core ML components built from scratch.
- **Compute/Model size**: ~10–15M parameters — chosen to fit free-tier training time and on-device CPU inference.
- **Portability**: Must train on Kaggle GPU and run inference/demo on a laptop CPU with no internet.
- **Privacy**: Memory must live in weights only — no external data stores. This is a design requirement, not just a constraint.
- **Dev environment**: Claude Code as the development environment; GSD workflow for planning.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-milestone split: base LM (M1) before LoRA/EWC personalization (M2) | De-risk the from-scratch foundation before the novel claim depends on it | — Pending |
| Milestone 1 pretraining stops at TinyStories (fluency), defer conversational tuning to M2 | Best coherence-per-parameter at ~10–15M; keeps M1 shippable | — Pending |
| Two-stage pretraining curriculum (TinyStories → DailyDialog/PersonaChat) for the full project | Fluency first, then conversational/persona grounding; defensible at small scale | — Pending |
| Eventual demo = both teach-then-recall and EWC no-forgetting, as a research narrative | Strongest portfolio artifact; proves memory is in weights and survives continual learning | — Pending |
| Gradio local web UI as primary demo + `demo.ipynb` as technical artifact | Good demo video/screenshots while staying on-device; notebook carries the ML narrative | — Pending |
| Document-as-we-go (polished writeup each milestone) | Narrative compounds; avoids reconstructing rationale later | — Pending |
| Everything from scratch (transformer, BPE, LoRA, EWC) — no HF PEFT | The portfolio value is demonstrated depth, not library usage | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-04 after initialization*
