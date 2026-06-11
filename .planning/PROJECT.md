# PersonaCore

## What This Is

PersonaCore is a conversational AI assistant where **all** memory and personalization live in the model weights — no databases, no vector stores, no external files. The model learns who you are by updating its own parameters, making weight-based memory a privacy guarantee by design. The entire stack (GPT-style transformer decoder, BPE tokenizer, LoRA adapters, EWC continual learning) is built from scratch in PyTorch and runs fully on-device. It is an elite CS-undergraduate portfolio project intended to demonstrate deep ML fundamentals, a genuinely novel approach, and a working demo.

## Current State (v1.0 shipped 2026-06-11)

**Milestone 1 "Foundation" is shipped.** A from-scratch 13,891,584-parameter GPT-2-style decoder, trained 50,000 steps on TinyStories entirely on the author's M3 (MPS, fp32), generates fluent child-story prose — `best.pt` val_loss 0.7378, headline perplexity **2.1066** over 12,636,922 held-out tokens. Shipped artifacts: offline Gradio CPU chat demo (slim 55.6 MB `weights_only=True` checkpoint, crash-proof dead-id logits mask), executed `demo.ipynb`, 440-line `docs/REPORT.md` + README with hero GIF, 4-variant ablation study, and a 137-test green CPU-only suite. Milestone audit passed 35/35 requirements with 20/20 cross-phase integration links verified live. Both M2 seams are locked and test-verified: six named `nn.Linear` projections per block (LoRA) and `assemble_loss(..., extra_penalties=())` + open-dict checkpoints (EWC).

**Known tech debt carried into M2** (none blocking; see `milestones/v1.0-MILESTONE-AUDIT.md`): the frozen tokenizer was trained on an 11.5KB fixture (547 live ids of 8192 — honestly documented, but consider retraining the tokenizer if M2 fine-tuning data warrants it, which would invalidate `best.pt`); `forbid_ids` mask not threaded into `evaluate.py`; `run.csv` tokens column ×256 under-count; stale TODO(calibration) markers.

**v2.0 progress:** Phase 9 (LoRA Core) complete 2026-06-11 — from-scratch `src/personacore/lora/` package (config/layer/inject), toggle/eject/merge runtime semantics, `export_adapter`/`load_adapter` persona-file artifact, and frozen-base training discipline proven on the real 13.9M base (331,776 trainable adapter params, 1.35 MB `adapter.pt`). Suite now 180 passed / 1 skipped. Next: Phase 10 (EWC Core).

## Current Milestone: v2.0 Weight-Based Memory

**Goal:** Prove the novel claim — personalization lives in the model weights, not in a prompt or store — via from-scratch LoRA + EWC on the v1.0 foundation.

**Target features:**
- From-scratch LoRA adapters wrapping the six named `nn.Linear` projections per block (v1.0 seam)
- EWC continual learning with Fisher-information penalty via the `assemble_loss(..., extra_penalties=())` seam
- Conversational fine-tuning on DailyDialog + PersonaChat (curriculum stage 2)
- Teach-then-recall clean-room personalization demo
- No-forgetting demo: EWC A/B vs naive fine-tuning
- Committed visualization deliverables: forgetting curves + weight-delta heatmaps

**Key milestone decisions:** frozen tokenizer kept as-is (no retrain — `best.pt` stays valid as the M2 base; dead-id mask handles the 547-live-id vocabulary); both demos in scope as research-narrative deliverables; phase numbering continues from v1.0 (next phase = 9).

## Core Value

The novel claim must be true and demonstrable: **personalization lives in the weights, not in a prompt or a store** — and the from-scratch implementation must be correct enough to prove it. If everything else fails, the project must still show real ML depth built by hand.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] Project scaffolding: repo structure, `CLAUDE.md`, reproducible environment (`requirements.txt`, virtual env), runnable on M3/MPS, Kaggle P100 (fallback), and laptop CPU — _Validated in Phase 01: scaffolding-reproducible-environment; MPS device support added in quick task 260605-lgy (`RuntimeConfig` CUDA-P100→MPS→CPU, `preflight_device`)_
- [x] BPE tokenizer implemented from scratch (train/encode/decode), with unit tests — _Validated in Phase 02: from-scratch-bpe-tokenizer (vocab locked at 8192/eos 8184; tiktoken-equivalence oracle green; production `tokenizer.json` to be regenerated from a TinyStories slice before Phase 5 — see 02-VERIFICATION.md WR-04)_
- [x] Bigram language model from scratch as a baseline foundation, with unit tests — _Validated in Phase 03: bigram-baseline-training-harness (thin end-to-end tokenize→train→sample→see-output slice; resumable open-dict checkpoint with GradScaler state + the `assemble_loss` EWC seam proven; fp16 resume trajectory carried as a GPU-confirmation item for Phase 5 — see 03-VERIFICATION.md)_
- [x] Training loop with checkpointing, loss logging, and resumability (resumable across local M3/MPS sessions; Kaggle 30h/week fallback-aware) — _Validated in Phase 03: AdamW + warmup/cosine LR + grad-clip + grad-accum, fp32 default with optional fp16-AMP+GradScaler path, CSV loss logging, save→kill→resume reproduces the curve within 1e-6_
- [x] Text generation/sampling (temperature, top-k) with unit tests — _Validated in Phase 06: generation-sampling (one shared `generate()` powering tests/notebook/demo — greedy/temperature/top-k/top-p, EOS-stop + trailing-token trim, context crop past `block_size`, `str→str` streaming wrapper with running-buffer-delta decode; 14 CPU generation tests + nucleus-exactness pin, top_k≤0 guarded — see 06-VERIFICATION.md)_
- [x] Evaluation: held-out perplexity, curated qualitative samples, and a from-scratch architecture-ablation study — _Validated in Phase 07: evaluation (EVAL-01/02/03). Deterministic full-val `perplexity()` proven against a brute-force oracle (headline 2.1066 over 12,636,922 tokens on `best.pt`); curated `results/samples.md`; additive `weight_tying`/`use_pos_emb` `ModelConfig` flags (defaults reproduce today's arch bit-for-bit) enable a self-consistent 4-variant cohort (baseline/no_tie/no_pos/depth_cut) trained through the untouched `train()` at the D-07-calibrated budget (2500 steps) with a committed comparison table — see 07-VERIFICATION.md_
- [x] Gradio local web UI chat demo (on-device) plus `demo.ipynb` research artifact (training curves, sampling) — _Validated in Phase 08: demo-writeup (DEMO-01/02/03). Offline `gr.ChatInterface` demo on laptop CPU with temperature/top-k sliders, slim fp32 checkpoint (`export_slim` → safetensors-style safe load), narrated `demo.ipynb`, animated GIF hero; CR-01 dead-id logits mask (`forbid_ids`) makes every slider setting crash-safe — see 08-VERIFICATION.md (re-verified 7/7 after gap closure)_
- [x] Polished technical writeup documenting design decisions, architecture, and results (document-as-we-go) — _Validated in Phase 08: demo-writeup (DOC-01). `docs/REPORT.md` decision-driven deep dive + README front door with honest effective-vocabulary claims (547 live of 8192 ids; 2,935,680 dead-row params quantified), clone-first quickstart — see 08-VERIFICATION.md_
- [x] GPT-style transformer decoder (~10–15M params) from scratch: attention, MLP, blocks, positional embeddings, with unit tests — _Validated in Phase 04: gpt-transformer-decoder (13,891,584 params tied-once; causality-perturbation, init-std, data_ptr-tying, param-band gates all green; drops into the untouched Phase-3 harness) — v1.0_
- [x] Pretrain on TinyStories to fluent, coherent generation — _Validated in Phase 05: tinystories-pretraining (50,000-step local M3/MPS fp32 run, kill+resume survived mid-run; `best.pt` val_loss 0.7378 at step 49000; retroactively verified 3/3 at milestone audit — see milestones/v1.0-phases/05-tinystories-pretraining/05-VERIFICATION.md) — v1.0_
- [x] From-scratch LoRA adapters wrapping the six named `nn.Linear` projections per block — _Validated in Phase 9: LoRA Core (LORA-01..05). `LoRALinear` composition wrapper (B=0 identity at injection, single `alpha/r` scale source), post-load injection over the v1.0 seam (tied `lm_head`/`wte` never wrapped), toggle/eject + merge/unmerge with bit-exact restore, 1.35 MB `adapter.pt` persona artifact through the `weights_only=True` choke point, frozen-base training proven through the byte-untouched v1.0 `train()` — 43 new tests, see 09-VERIFICATION.md (13/13). Advisory debt: 09-REVIEW.md CR-01 (toggle×merge state blindness) + CR-02 (shape-blind key audit) to resolve before Phase 14 consumes these APIs_

### Active

<!-- Milestone v2.0: Weight-Based Memory — requirements being defined; REQ-IDs land in REQUIREMENTS.md. -->

- [ ] EWC continual learning with Fisher-information penalty via the `assemble_loss(..., extra_penalties=())` seam (shipped + verified in v1.0)
- [ ] Conversational fine-tuning on DailyDialog + PersonaChat (curriculum stage 2)
- [ ] Teach-then-recall (clean-room) personalization demo — memory lives in weights, not the prompt
- [ ] No-forgetting (EWC A/B vs naive fine-tuning) demo
- [ ] Weight-delta heatmaps and forgetting-curve visualizations

### Out of Scope

<!-- Explicit boundaries. -->

- HuggingFace PEFT / transformers model code — excluded by design; everything is from scratch
- External AI APIs during training — excluded by design (zero budget, privacy, on-device)
- Databases, vector stores, RAG, external memory files — excluded by design; memory must live in weights
- Scaling beyond ~10–15M params or multi-GPU training — out of scope given the local M3/MPS (and fallback Kaggle free-tier) budget
- KV-cache for CPU inference — measured ~95–105 tok/s on CPU in Phase 8; not needed; revisit only if an M2 demo feels slow

## Context

- **Audience:** portfolio reviewers at the MIT/Stanford bar (admissions, research, recruiting) and the author. The work must read as rigorous, original, and self-implemented.
- **Two-milestone strategy:** De-risk the foundation before the novel claim. **Milestone 1** delivers a correct, from-scratch base language model with a working generation demo. **Milestone 2** delivers the differentiating weight-based memory (LoRA + EWC) and the research-narrative demos.
- **Curriculum plan (full project):** two-stage pretraining — TinyStories for base fluency, then DailyDialog + PersonaChat for conversational grounding. Milestone 1 covers only the TinyStories stage.
- **Dual-environment reality:** training runs **locally on Apple Silicon (M3 / MPS)** — fp32, since MPS has no fp16-AMP path; **Kaggle P100 (16GB, 30h/week) via notebooks remains an optional fallback**. The demo and inference run on a laptop CPU. Code must be portable across MPS, CUDA-P100, and CPU (`RuntimeConfig` resolves CUDA-P100 → MPS → CPU). Training on the author's own machine reinforces the on-device/privacy thesis.
- **Engineering rigor is a theme:** per-component unit tests and a documented technical narrative are first-class deliverables, not afterthoughts — they are part of what makes this a portfolio-grade artifact.
- **Codebase state after v1.0 (2026-06-11):** 6,543 lines of Python (src + scripts + tests), 137 tests green (1 CUDA-only skip), 245 commits. Package: `src/personacore/` (config, checkpoint, seeding, provenance, preflight, logging, tokenizer/, model/, training/, data path, generation/, evaluation/). Shipped weights: `best.pt` (159 MB full state) + `model_slim.pt` (55.6 MB inference, GitHub Release `m1-demo-v1`). Frozen tokenizer: `artifacts/tokenizer.json` (8192 table, 547 live ids — see tech-debt note in Current State).

## Constraints

- **Budget**: Zero — primary training is **local on Apple Silicon (M3 / MPS)**, the author's own hardware; **Kaggle free-tier GPU (P100 16GB, 30h/week) is an optional fallback**. No paid compute or APIs.
- **Tech stack**: Python + PyTorch only. No HuggingFace PEFT/transformers model code; core ML components built from scratch.
- **Compute/Model size**: ~10–15M parameters — chosen to fit local M3/MPS (and fallback free-tier P100) training time and on-device CPU inference.
- **Portability**: Must train on **M3/MPS (Kaggle P100 optional fallback)** and run inference/demo on a laptop CPU with no internet. `RuntimeConfig` resolves CUDA-P100 → MPS → CPU; MPS and CPU run fp32 (no fp16 AMP), the bf16-on-Pascal guard still errors.
- **Privacy**: Memory must live in weights only — no external data stores. This is a design requirement, not just a constraint.
- **Dev environment**: Claude Code as the development environment; GSD workflow for planning.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-milestone split: base LM (M1) before LoRA/EWC personalization (M2) | De-risk the from-scratch foundation before the novel claim depends on it | ✓ Good — v1.0 shipped with both M2 seams verified as acceptance criteria; M2 is additive, not a rewrite |
| Milestone 1 pretraining stops at TinyStories (fluency), defer conversational tuning to M2 | Best coherence-per-parameter at ~10–15M; keeps M1 shippable | ✓ Good — fluent child-story prose at 13.9M params, PPL 2.1066 |
| Two-stage pretraining curriculum (TinyStories → DailyDialog/PersonaChat) for the full project | Fluency first, then conversational/persona grounding; defensible at small scale | — Pending (stage 2 is M2) |
| Eventual demo = both teach-then-recall and EWC no-forgetting, as a research narrative | Strongest portfolio artifact; proves memory is in weights and survives continual learning | — Pending (M2) |
| Gradio local web UI as primary demo + `demo.ipynb` as technical artifact | Good demo video/screenshots while staying on-device; notebook carries the ML narrative | ✓ Shipped in Phase 08 (offline ChatInterface + narrated notebook + GIF hero) |
| Document-as-we-go (polished writeup each milestone) | Narrative compounds; avoids reconstructing rationale later | ✓ M1 writeup shipped in Phase 08 (docs/REPORT.md + README) |
| Everything from scratch (transformer, BPE, LoRA, EWC) — no HF PEFT | The portfolio value is demonstrated depth, not library usage | ✓ Good for M1 scope (transformer, BPE, harness, generation, eval all hand-rolled; tiktoken/Gradio confined to test-oracle/UI roles); LoRA/EWC pending in M2 |
| Primary training target = local M3/MPS (fp32); Kaggle P100 demoted to optional fallback (decided Phase 5 discuss, 2026-06-05) | Strengthens the fully-on-device/zero-budget/privacy thesis — the model trains on the author's own machine, no external compute dependency. MPS has no fp16 AMP, so fp32; `RuntimeConfig` resolves CUDA-P100→MPS→CPU. | ✓ Good — the full 50k-step v1.0 pretrain ran entirely on the M3 (MPS fp32), kill+resume proven; Kaggle never needed |
| Ship the fixture-trained frozen tokenizer (547 live of 8192 ids) rather than retrain before Phase 5 (accepted Phase 8, documented in 08-08) | Retraining would have invalidated the locked vocab/checkpoint chain mid-milestone; honesty-first documentation instead (README/REPORT quantify 2,935,680 dead-row params) | ⚠️ Revisit in M2 — if conversational fine-tuning data warrants a real-corpus tokenizer, that decision invalidates `best.pt` and must be made before any M2 training |
| Dead-id `forbid_ids` logits mask at the sampling layer (Phase 8 CR-01) rather than catch-and-truncate at decode | Crash-proof demo at every in-UI setting without hiding real errors; decode stays strict by design | ✓ Good — demo verified crash-free; mask not yet threaded into evaluate.py (tech debt) |
| Retroactive Phase 5 verification at milestone audit (2026-06-11) instead of a closure phase | The work existed and was downstream-corroborated; only the formal verification artifact was missing | ✓ Good — passed 3/3; audit flipped to 35/35 without new phases |
| Keep the frozen tokenizer for v2.0 — no retrain (decided 2026-06-11 at v2.0 kickoff) | Dead-id mask already in place; M2 training time better spent on LoRA/EWC than a retrain; retraining would invalidate `best.pt` as the M2 base | — Locked for v2.0; resolves the "revisit in M2" flag above |

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
*Last updated: 2026-06-11 after Phase 9 (LoRA Core) completion*
