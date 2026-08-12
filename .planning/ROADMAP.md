# Roadmap: PersonaCore

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-8 (shipped 2026-06-11) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v2.0 Weight-Based Memory** — Phases 9-15 (shipped 2026-08-12) — [archive](milestones/v2.0-ROADMAP.md)
- 📋 **v3.0** — not yet defined (run `/gsd:new-milestone`)

## Overview

v1.0 built the foundation by hand: a ~13.9M-parameter GPT-style decoder, a from-scratch BPE
tokenizer, and a resumable training harness, pretrained on TinyStories on the author's own Apple
Silicon machine to headline perplexity 2.1066.

v2.0 proved the novel claim on top of it: **personalization lives in the model weights, not in a
prompt or a store.** From-scratch LoRA teaches user-specific facts into 331,776 adapter parameters
on a frozen conversational base, and a fresh process recalls them from an empty prompt with the
context provably wiped; from-scratch EWC keeps the fine-tune from destroying the base model, at a
3.6× separation clearing its pre-registered margin by 33.61×. Every headline number is gated by a
rule committed to git before the number existed.

The next milestone is undefined. Start it with `/gsd:new-milestone`.

## Phases

<details>
<summary>✅ v1.0 Foundation (Phases 1-8) — SHIPPED 2026-06-11</summary>

- [x] Phase 1: Scaffolding & Reproducible Environment (3/3 plans) — completed 2026-06-04
- [x] Phase 2: From-Scratch BPE Tokenizer (3/3 plans) — completed 2026-06-04
- [x] Phase 3: Bigram Baseline & Training Harness (4/4 plans) — completed 2026-06-04
- [x] Phase 4: GPT Transformer Decoder (3/3 plans) — completed 2026-06-05
- [x] Phase 5: TinyStories Pretraining (2/2 plans) — completed 2026-06-05
- [x] Phase 6: Generation & Sampling (3/3 plans) — completed 2026-06-06
- [x] Phase 7: Evaluation (3/3 plans) — completed 2026-06-09
- [x] Phase 8: Demo & Writeup (8/8 plans) — completed 2026-06-10

Full phase details: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) · Audit: [milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v1.0-phases/`

</details>

<details>
<summary>✅ v2.0 Weight-Based Memory (Phases 9-15) — SHIPPED 2026-08-12</summary>

**Milestone Goal:** Prove personalization lives in the weights via from-scratch LoRA + EWC on the v1.0 foundation — conversational fine-tune, no-forgetting A/B, and a clean-room teach-then-recall demo.

- [x] Phase 9: LoRA Core (4/4 plans) — completed 2026-06-11
- [x] Phase 10: EWC Core (3/3 plans) — completed 2026-06-12
- [x] Phase 11: Conversational Data Pipeline (4/4 plans) — completed 2026-07-31 *(DailyDialog cut per D-00)*
- [x] Phase 12: Stage-2 Conversational Fine-Tune (5/5 plans) — completed 2026-08-01
- [x] Phase 13: EWC A/B No-Forgetting Experiment (4/4 plans) — completed 2026-08-02
- [x] Phase 14: Teach-Then-Recall Demo (11/11 plans) — completed 2026-08-02
- [x] Phase 15: Figures & Writeup (8/8 plans) — completed 2026-08-02

**Headline results:** EWC retention PPL 3.891140 vs naive 8.524171 from a shared 2.1076 step-0
anchor — the pre-registered gate cleared by 33.61× its margin. Closed-book recall 0.4921 taught /
0.3483 held-out against thresholds 0.2486 / 0.2000, with the adapter-off control at exactly
0/2430. Fisher/Δ correlation Spearman ρ = 0.801544, 95% CI [0.597984, 0.920291].

Full phase details: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md) · Audit: [milestones/v2.0-MILESTONE-AUDIT.md](milestones/v2.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v2.0-phases/`

</details>

### 📋 v3.0 — not yet defined

No phases planned. Run `/gsd:new-milestone` to scope the next milestone (questioning → research → requirements → roadmap).

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
| ----- | --------- | -------------- | ------ | --------- |
| 1. Scaffolding & Reproducible Environment | v1.0 | 3/3 | Complete | 2026-06-04 |
| 2. From-Scratch BPE Tokenizer | v1.0 | 3/3 | Complete | 2026-06-04 |
| 3. Bigram Baseline & Training Harness | v1.0 | 4/4 | Complete | 2026-06-04 |
| 4. GPT Transformer Decoder | v1.0 | 3/3 | Complete | 2026-06-05 |
| 5. TinyStories Pretraining | v1.0 | 2/2 | Complete | 2026-06-05 |
| 6. Generation & Sampling | v1.0 | 3/3 | Complete | 2026-06-06 |
| 7. Evaluation | v1.0 | 3/3 | Complete | 2026-06-09 |
| 8. Demo & Writeup | v1.0 | 8/8 | Complete | 2026-06-10 |
| 9. LoRA Core | v2.0 | 4/4 | Complete | 2026-06-11 |
| 10. EWC Core | v2.0 | 3/3 | Complete | 2026-06-12 |
| 11. Conversational Data Pipeline | v2.0 | 4/4 | Complete | 2026-07-31 |
| 12. Stage-2 Conversational Fine-Tune | v2.0 | 5/5 | Complete | 2026-08-01 |
| 13. EWC A/B No-Forgetting Experiment | v2.0 | 4/4 | Complete | 2026-08-02 |
| 14. Teach-Then-Recall Demo | v2.0 | 11/11 | Complete | 2026-08-02 |
| 15. Figures & Writeup | v2.0 | 8/8 | Complete | 2026-08-02 |

**Totals:** 15 phases, 68 plans, 2 milestones shipped.
