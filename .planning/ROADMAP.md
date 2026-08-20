# Roadmap: PersonaCore

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-8 (shipped 2026-06-11) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v2.0 Weight-Based Memory** — Phases 9-15 (shipped 2026-08-12) — [archive](milestones/v2.0-ROADMAP.md)
- ✅ **v3.0 Adversarial Privacy Audit and Selective Memory Erasure** — Phases 16-19 (shipped 2026-08-19) — [archive](milestones/v3.0-ROADMAP.md)

## Overview

v1.0 built the foundation by hand: a ~13.9M-parameter GPT-style decoder, a from-scratch BPE
tokenizer, and a resumable training harness, pretrained on TinyStories on the author's own Apple
Silicon machine to headline perplexity 2.1066.

v2.0 proved the novel claim on top of it: **personalization lives in the model weights, not in a
prompt or a store.** From-scratch LoRA teaches user-specific facts into 331,776 adapter parameters
on a frozen conversational base, and a fresh process recalls them from an empty prompt with the
context provably wiped; from-scratch EWC keeps the fine-tune from destroying the base model, at a
3.6× separation clearing its pre-registered margin by 33.61×.

v3.0 stopped *asserting* that weight-based memory is private and **measured** it — then published
what the measurement said, which was not flattering. Phase 18's black-box audit returned
`LEAKAGE_DEMONSTRATED`: 92/104 = 88.5% of taught facts recovered by prompt-only attack against a
no-adapter control at exactly `0/104`. Phase 19 then attempted selective erasure under a rule
committed at `23a830c` **before Phase 16 ran**, and the committed gate returned **`FAILURE`** —
the target was erased (0/27, exactly on the floor) but all seven gated non-targets were destroyed
with it, four at total generation loss, and 77.6% of the dialogue adaptation was lost.
**Selective erasure is not selective at 331,776 parameters.** A co-headline shipped at equal
weight: the rank/exposure instrument and the generation instrument disagree on the same weights,
which retroactively scope-limits any Phase 18 conclusion resting on rank alone.

Every headline number in v2.0 and v3.0 is gated by a rule committed to git before the number
existed. In v3.0 that discipline did not merely hold — it **authored** Phase 19, which entered the
roadmap only because `erasure_is_worth_attempting(92, 104, 0, 104)` returned True.

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

Full details: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) · Audit: [milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v1.0-phases/`

</details>

<details>
<summary>✅ v2.0 Weight-Based Memory (Phases 9-15) — SHIPPED 2026-08-12</summary>

- [x] Phase 9: LoRA Core (4/4 plans) — completed 2026-06-11
- [x] Phase 10: EWC Core (3/3 plans) — completed 2026-06-12
- [x] Phase 11: Conversational Data Pipeline (4/4 plans) — completed 2026-07-31
- [x] Phase 12: Stage-2 Conversational Fine-Tune (5/5 plans) — completed 2026-08-01
- [x] Phase 13: EWC A/B No-Forgetting Experiment (4/4 plans) — completed 2026-08-02
- [x] Phase 14: Teach-Then-Recall Demo (11/11 plans) — completed 2026-08-02
- [x] Phase 15: Figures & Writeup (8/8 plans) — completed 2026-08-02

**Headline results:** EWC retention PPL 3.891140 vs naive 8.524171 from a shared 2.1076 step-0
anchor. Closed-book recall 0.4921 taught / 0.3483 held-out against thresholds 0.2486 / 0.2000,
adapter-off control at exactly 0/2430. Fisher/Δ Spearman ρ = 0.801544, 95% CI [0.597984, 0.920291].

Full details: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md) · Audit: [milestones/v2.0-MILESTONE-AUDIT.md](milestones/v2.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v2.0-phases/`

</details>

<details>
<summary>✅ v3.0 Adversarial Privacy Audit and Selective Memory Erasure (Phases 16-19) — SHIPPED 2026-08-19</summary>

- [x] Phase 16: Weight-vs-Prompt Persistence Control (11/11 plans) — completed 2026-08-14
- [x] Phase 17: Multi-Persona Isolation Matrix (11/11 plans) — completed 2026-08-15
- [x] Phase 18: Black-Box Adversarial Extraction Audit (16/16 plans) — completed 2026-08-17
- [x] Phase 19: Selective Memory Erasure (16/16 plans) — completed 2026-08-19

**Headline results:** Phase 16 — adapter arm 90/104 questions vs the prompt arm at the floor, weight
invariance proved at max |diff| 0.0. Phase 17 — all six off-diagonals 0/104, six Holm comparisons
rejected at p = 0.0078125. Phase 18 — **`LEAKAGE_DEMONSTRATED`**, 92/104 = 88.5% (95% lower bound
0.8231) against an adapter-off arm at exactly 0/104, at 42,480 draws per arm. Phase 19 — verdict
**`FAILURE`**: (a) cleared exactly on its boundary at 0/27, all seven gated non-targets failed,
77.6% of dialogue adaptation destroyed. Ship decision **`DO NOT SHIP`**, withholding exactly one
claim and withdrawing no measurement.

Full details: [milestones/v3.0-ROADMAP.md](milestones/v3.0-ROADMAP.md) · Audit: [milestones/v3.0-MILESTONE-AUDIT.md](milestones/v3.0-MILESTONE-AUDIT.md) · Phase artifacts: `.planning/phases/`

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
| ----- | --------- | -------------- | ------ | --------- |
| 1-8 | v1.0 | 29/29 | Complete | 2026-06-10 |
| 9-15 | v2.0 | 39/39 | Complete | 2026-08-02 |
| 16. Weight-vs-Prompt Persistence Control | v3.0 | 11/11 | Complete | 2026-08-14 |
| 17. Multi-Persona Isolation Matrix | v3.0 | 11/11 | Complete | 2026-08-15 |
| 18. Black-Box Adversarial Extraction Audit | v3.0 | 16/16 | Complete | 2026-08-17 |
| 19. Selective Memory Erasure | v3.0 | 16/16 | Complete | 2026-08-19 |

**Totals:** 19 phases complete, 122 plans (29 v1.0 + 39 v2.0 + 54 v3.0), **3 milestones shipped**.

Next milestone not yet defined — run `/gsd:new-milestone`.
