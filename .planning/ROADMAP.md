# Roadmap: PersonaCore

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-8 (shipped 2026-06-11) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v2.0 Weight-Based Memory** — Phases 9-15 (shipped 2026-08-12) — [archive](milestones/v2.0-ROADMAP.md)
- ✅ **v3.0 Adversarial Privacy Audit and Selective Memory Erasure** — Phases 16-19 (shipped 2026-08-19) — [archive](milestones/v3.0-ROADMAP.md)
- ✅ **v4.0 Leakage Mitigation and Relearning Validation** — Phases 20-28 (shipped 2026-09-22) — [archive](milestones/v4.0-ROADMAP.md)
- 🔮 **v5.0 (candidate, not planned)** — the replay-bearing adversarial re-run: retrain the
  adversarial arm WITH replay and re-measure the 12 points, so condition (c) is tested against
  the ratio instead of the recipe. Opened 2026-09-09 by operator decision on 25-HUMAN-UAT
  item 3; v4.0 publishes the arm as recipe-confounded (Phase 28 SC4) rather than waiting for
  it. Estimated ~25-30 h of MPS at Phase 25's measured pace, plus the recipe work.

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

v4.0 answers the finding v3.0 measured and left open: **88.5% leakage, and no mitigation arm was
run.** It builds two training-time mitigations — from-scratch DP-SGD on the LoRA gradients (the
only arm making a formal (ε, δ) claim) and adversarial extraction-aware training (no guarantee, but
it bounds the empirical question directly) — maps both onto one privacy/utility plane at two corpus
capacities under a **three-condition** existence gate, and proves adversarially by relearning attack
that what survives cannot be cheaply reverted.

Three facts shape this roadmap and were measured before it was written. **The gate is phase-zero**
because ordering is its only evidence: `erasure_gate.py` was committed before Phase 16 ran, and the
v4.0 gate must be committed before *any* v4.0 number exists — before the cost calibration, not
merely before the sweep. **The privacy unit is the longest dependency chain** and it is design work,
not code: UNIT blocks the DP data path, which blocks the DP arm, which blocks the frontier, and "the
unit was wrong" invalidates every ε in a way no amount of re-running fixes. **Evaluation is the
binding constraint at ~1,010× training** — one sweep point at full Phase-18 fidelity is 42,480 draws
= 4.77 h against ~17 s of training, so a 16-point sweep at K=48 is 76.3 h of continuous M3 time.
That is why CAL-04 pre-registers per-point K and the promotion rule, and why a phase that "just adds
a few more sweep points" is expensive.

<!-- 23-12-CONTINUATION-BEGIN -->
**RETRACTED IN PLACE 2026-08-28 (plan 23-12).** The clause above — *"Evaluation is the binding
constraint at ~1,010× training — one sweep point at full Phase-18 fidelity is 42,480 draws = 4.77 h
against ~17 s of training"* — is left unamended as the record of what was believed when this
roadmap was written, and its two figures were measured **FALSE** by plan 23-11. Read from
`results/phase23_cost.json`, sha256
`f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637`, at that record's own stored
precision: the evaluation leg is a bracket, `generation.h_per_point_floor` = `5.7223403197590965` h
to `generation.h_per_point_ceiling` = `9.013691285839306` h, whose **floor already exceeds** the
`4.77` above; training is `161.12400419991462` s at the protocol-matched non-DP comparator
(`training.non_dp.training_seconds_mean`), not ~17 s; and `eval ÷ training` at the ceiling is
`201.39326098648866` on that same protocol, `410.006407009605` at the superseded non-DP protocol
(`old unmitigated control (superseded as a comparator)`, the arm the record argues is the wrong
comparator), `157.94846187604026` at `dp_n8, seam active, sigma=0` and `23.458286235587472` at
`dp_n64, seam active, sigma>0`. **No arm at any protocol is `~1,010×`.** Evaluation still binds at
every capacity, so the ordering argument this paragraph makes is unchanged — a 16-point sweep is
still the expensive thing and CAL-04's pre-registration is still why. Only the margin moves, and it
moves toward *more* wall clock, not less: the sweep is sized against `h_per_point_ceiling` because
the K ratchet in `scripts/mitigation_gate.py` has no cheap direction. The full continuation, with
all eleven pre-registered figure paths and the root cause, is in `.planning/REQUIREMENTS.md`.
<!-- 23-12-CONTINUATION-END -->

**The expected null is a deliverable, not a risk.** Research puts high prior probability on the DP
arm being a pre-registered null — fact-level noise-to-signal is 72σ at L=8 facts, ε_fact ≤ 4 needs
σ ≥ 15.3, and Secret Sharer Table 3 is the direct precedent (a once-inserted canary unextractable at
every ε tested, including 10⁹). The decision is to **publish that null at two capacities rather than
avoid it**: GATE-10 pre-commits both branches of the n=8-vs-n=64 comparison before either run, and
Phase 28 gives the null its own report surface. This project shipped `LEAKAGE_DEMONSTRATED` and
`FAILURE` in v3.0 and is stronger for it.

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

Full details: [milestones/v3.0-ROADMAP.md](milestones/v3.0-ROADMAP.md) · Audit: [milestones/v3.0-MILESTONE-AUDIT.md](milestones/v3.0-MILESTONE-AUDIT.md)

</details>

<details>
<summary>✅ v4.0 Leakage Mitigation and Relearning Validation (Phases 20-28) — SHIPPED 2026-09-22</summary>

- [x] Phase 20: Pre-Registration — The Three-Condition Gate (17/17 plans) — completed 2026-08-21
- [x] Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus (11/11 plans) — completed 2026-08-25
- [x] Phase 22: DP-SGD Core, Accountant, and the Correctness Battery (19/19 plans) — completed 2026-08-26
- [x] Phase 23: Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration (20/20 plans) — completed 2026-08-29
- [x] Phase 24: Adversarial Extraction-Aware Training + the Held-Out Attack Family (9/9 plans) — completed 2026-08-30
- [x] Phase 25: Frontier Sweep and the Existence-Gate Verdict (22/22 plans) — completed 2026-09-09
- [x] Phase 26: Empirical Privacy Audit (Canary) (5/5 plans) — completed 2026-09-13
- [x] Phase 27: Relearning Attack (5/5 plans) — completed 2026-09-16
- [x] Phase 28: Report, the Published Null, and Milestone Close (7/7 plans) — completed 2026-09-22

**Headline results:** the pre-registered three-condition gate (Phase 20) returned
**`null-at-both-capacities`** on the 44-point frontier (Phase 25): 0 PASS / 32 FAIL /
6 INCONCLUSIVE / 6 REFUSED. Every DP point above σ=0 scored taught recall 0/1008 and held-out
0/648 — DP removed the leakage by removing the memory; the n=64 control itself learned only
87/1008. The canary audit (Phase 26) read 15 CONSISTENT / 0 BROKEN against each point's own ε and
recorded where it could not have failed. The relearning admission gate (Phase 27) read **MOOT**,
0 of 44 admissible, so RELRN-02..05 ship as the named limitation. The v4.0 report (Phase 28) is
rendered from the committed records — every number a binding — and closed on CI run 35770563251.
`sigma_for(4.0, 200, 1e-5) = 15.289937507119` re-derives the expectation recorded at `c673b4c`
before any run.

Full details: [milestones/v4.0-ROADMAP.md](milestones/v4.0-ROADMAP.md) · Audit: [milestones/v4.0-MILESTONE-AUDIT.md](milestones/v4.0-MILESTONE-AUDIT.md) · Requirements: [milestones/v4.0-REQUIREMENTS.md](milestones/v4.0-REQUIREMENTS.md)

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
| ----- | --------- | -------------- | ------ | --------- |
| 1-8 | v1.0 | 29/29 | Complete | 2026-06-10 |
| 9-15 | v2.0 | 39/39 | Complete | 2026-08-02 |
| 16-19 | v3.0 | 54/54 | Complete | 2026-08-19 |
| 20-28 | v4.0 | 115/115 | Complete | 2026-09-22 |

**Totals:** 19 phases complete, 122 plans (29 v1.0 + 39 v2.0 + 54 v3.0), **3 milestones shipped**.
v4.0 adds 9 phases (20-28) covering 48 requirements, 48/48 mapped, 0 orphans.

Next: `/gsd:plan-phase 20`.
