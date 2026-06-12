# Roadmap: PersonaCore

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-8 (shipped 2026-06-11) — [archive](milestones/v1.0-ROADMAP.md)
- 🚧 **v2.0 Weight-Based Memory** — Phases 9-15 (in progress)

## Overview

v2.0 proves the novel claim: personalization lives in the model weights, not in a prompt or a store. Three independent correctness phases land first — from-scratch LoRA (9), from-scratch EWC (10), and the conversational data pipeline with its tokenizer-inflation gate (11) — front-loading all unit-testable work before any long training run. Phase 12 turns `best.pt` into a conversational base via full fine-tune with calibrated EWC (telemetry debts fixed first so every retention-curve point is trustworthy). Phase 13 runs the unconfounded EWC A/B and commits the forgetting curves; Phase 14 delivers the core-value proof — clean-room teach-then-recall with a LoRA adapter and a live on/off toggle; Phase 15 ships the signature figures and the honest v2.0 writeup.

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

### 🚧 v2.0 Weight-Based Memory (Phases 9-15)

**Milestone Goal:** Prove personalization lives in the weights via from-scratch LoRA + EWC on the v1.0 foundation — conversational fine-tune, no-forgetting A/B, and a clean-room teach-then-recall demo.

- [x] **Phase 9: LoRA Core** - From-scratch `LoRALinear` over the six named projections, fully test-pinned, adapter as a small swappable artifact (completed 2026-06-11)
- [ ] **Phase 10: EWC Core** - Per-example diagonal Fisher + quadratic penalty through the `assemble_loss` seam, v1.0 trajectory bit-preserved when off
- [ ] **Phase 11: Conversational Data Pipeline** - DailyDialog + PersonaChat → role-token memmap bins with loss masks; tokenizer-inflation gate measured first
- [ ] **Phase 12: Stage-2 Conversational Fine-Tune** - Telemetry debts fixed, λ sweep, full fine-tune of `best.pt` to a conversational base with retention logged from step 0
- [ ] **Phase 13: EWC A/B No-Forgetting Experiment** - Identical-arm naive-vs-EWC A/B, 2×2 acquisition+retention result, committed forgetting curves + λ frontier
- [ ] **Phase 14: Teach-Then-Recall Demo** - Clean-room personalization: LoRA adapter recalls taught facts fresh-process/empty-prompt, live on/off toggle
- [ ] **Phase 15: Figures & Writeup** - Weight-delta + Fisher heatmaps, REPORT/README/demo.ipynb v2.0 narrative with honest numbers

## Phase Details

### Phase 9: LoRA Core

**Goal**: From-scratch LoRA adapters wrap the six named `nn.Linear` projections via post-load injection, with correctness proven by tests and adapter weights shipping as a small swappable artifact
**Depends on**: Nothing within v2.0 (consumes the v1.0 named-projection seam; independent of Phases 10-11)
**Requirements**: LORA-01, LORA-02, LORA-03, LORA-04, LORA-05
**Success Criteria** (what must be TRUE):

  1. With adapters injected at init (A-Gaussian/B-zero), model logits are bit-identical to the vanilla base, and the enable/disable round-trip returns exactly to base behavior
  2. After adapter training steps, only A/B matrices have changed — every base parameter is bit-untouched and the tied embedding tensor was never wrapped (`data_ptr` test post-injection)
  3. Adapter weights save/load as a separate small artifact compatible with open-dict checkpoints and the LOCKED `weights_only=True` slim contract
  4. `merge()`/unmerge passes the fp32-tolerance equivalence test (merged forward ≡ base+adapter) while the demo path stays unmerged
  5. Param-count formula and load→inject→freeze ordering are pinned by unit tests, and the params-actually-update canary passes on a smoke run

**Plans**: 4 plans

Plans:
**Wave 1**

- [x] 09-01-PLAN.md — LoRA core: `LoRAConfig` + `LoRALinear` + post-load injection/freeze machinery, fully test-pinned (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-02-PLAN.md — Toggle/eject (D-05/D-06) + merge/unmerge + pure `merged_state_dict` (D-07/D-08) (Wave 2)
- [x] 09-03-PLAN.md — Persona-file artifact: `export_adapter`/`load_adapter` choke point + two-artifact load (D-01..D-03) (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-04-PLAN.md — Frozen-base training proof: canary/kill+resume tests + real-weights smoke script (Wave 3)

### Phase 10: EWC Core

**Goal**: From-scratch EWC machinery — per-example empirical diagonal Fisher and the quadratic penalty — plugs into the training loop additively, with v1.0 behavior bit-preserved when the penalty is off
**Depends on**: Nothing within v2.0 (consumes the v1.0 `assemble_loss` seam, `best.pt`, and existing TinyStories bins; independent of Phases 9 and 11)
**Requirements**: EWC-01, EWC-02
**Success Criteria** (what must be TRUE):

  1. Fisher is estimated from per-example gradients over TinyStories batches at `best.pt` (not batched-gradient squaring), is normalized, and matches an analytic tiny-fixture oracle
  2. Fisher and anchor θ* persist via the open-dict checkpoint seam and reload intact, with tied tensors deduplicated by `data_ptr`
  3. The quadratic penalty `(λ/2)·Σ Fᵢ·(θᵢ−θ*ᵢ)²` is applied via `assemble_loss(..., extra_penalties=())` and evaluates to exactly 0 at the anchor (unit test)
  4. With the penalty disabled (`penalty_fn=None`), the training trajectory is bit-identical to v1.0 and all 137 existing tests stay green

**Plans**: 3 plans

Plans:
**Wave 1**

- [ ] 10-01-PLAN.md — `continual/` package: `estimate_fisher` (per-example diagonal Fisher, D-01..D-05) + `EWCPenalty`, fully test-pinned (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 10-02-PLAN.md — Loop integration: pre-edit golden trajectory fixture + additive `penalty_fn`/`checkpoint_extra` kwargs, bit-identity proven (Wave 2)
- [ ] 10-03-PLAN.md — Persistence + real weights: `export_fisher`/`load_fisher` seam tests + N=2000 estimation at `best.pt` producing the production cache (Wave 2)

### Phase 11: Conversational Data Pipeline

**Goal**: DailyDialog + PersonaChat become role-token-formatted, loss-masked memmap training bins through the frozen tokenizer — with the tokenizer-inflation tax measured before the format design hardens
**Depends on**: Nothing within v2.0 (consumes the frozen tokenizer with reserved role ids 8185-8187; independent of Phases 9-10)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):

  1. Both corpora download via pinned-checksum direct fetch (ParlAI mirror for DailyDialog, S3 JSON for PersonaChat) and parse from scratch — no HF `datasets` at runtime, no network at train time
  2. The tokenizer-inflation measurement (tokens-per-word, %-over-`block_size` on dialogue text) is produced and documented as a go/no-go gate BEFORE the fine-tune format design is committed
  3. Dialogues serialize with the reserved role tokens (`<|user|>`/`<|assistant|>`/`<|system|>`, ids 8185-8187) through the frozen tokenizer into uint16 memmap bins, with eos 8184 kept as a document separator only
  4. User-turn loss masking via `ignore_index=-100` (parallel mask bins) matches a hand-built fixture exactly in a turn-boundary unit test

**Plans**: TBD

### Phase 12: Stage-2 Conversational Fine-Tune

**Goal**: `best.pt` becomes a dialogue-capable conversational base via full fine-tune with calibrated EWC — telemetry tech debt fixed before the first training step so every retention-curve point is trustworthy
**Depends on**: Phase 10 (EWC penalty), Phase 11 (dialogue bins + masks)
**Requirements**: DEBT-01, DEBT-02, EWC-03, TUNE-01, TUNE-02
**Success Criteria** (what must be TRUE):

  1. Before the first v2.0 training step, `run.csv` tokens column counts true tokens (×`block_size` fix in `loop.py`) and the dead-id `forbid_ids` policy for retention PPL is frozen one way for all curve points
  2. The λ log-scale sweep (D-07 short-run pattern) completes, λ* is picked off the stability–plasticity tradeoff, and sweep logs are retained for the frontier plot
  3. Full fine-tune of `best.pt` on the conversational corpus through the untouched v1.0 `train()` reaches dialogue-format adherence — conversational val PPL reported and curated transcripts committed
  4. TinyStories retention PPL vs the 2.1066 anchor is logged at every eval interval from step 0 in per-run/per-arm CSVs — forgetting curves fall out of training logs, not post-hoc reconstruction
  5. A conversational-base checkpoint exists as the substrate for both demos

**Plans**: TBD
**Research flag**: λ selection is empirical with no portable value (reported range 0.1–10⁶) and the full-FT LR/budget needs calibration — plan this phase with `/gsd-plan-phase --research-phase`

### Phase 13: EWC A/B No-Forgetting Experiment

**Goal**: Committed, unconfounded evidence that EWC mitigates catastrophic forgetting — both retention AND acquisition reported for both arms
**Depends on**: Phase 12 (fine-tune harness, λ*, sweep logs)
**Requirements**: DEMO-04, VIZ-01, VIZ-04
**Success Criteria** (what must be TRUE):

  1. Naive and EWC arms run with identical seeds, config, and data order, differing ONLY in the penalty (λ=0 vs λ*)
  2. The headline result is a 2×2 table reporting both acquisition and retention for both arms (not retention-only)
  3. The forgetting-curve figure is committed: retention PPL vs fine-tune steps per arm, dashed baseline at 2.1066, acquisition companion panel
  4. The λ stability–plasticity frontier plot (retention vs acquisition, one point per λ from the sweep logs) is committed

**Plans**: TBD

### Phase 14: Teach-Then-Recall Demo

**Goal**: The core-value proof — a LoRA adapter on the frozen conversational base recalls taught user facts in a clean room: fresh process, empty prompt, no store, with a live memory on/off toggle
**Depends on**: Phase 9 (LoRA), Phase 12 (conversational base); independent of Phase 13
**Requirements**: DEMO-05, DEMO-06, DEMO-07
**Success Criteria** (what must be TRUE):

  1. 5-10 atomic user facts are taught via ~20-50 template/hand-written paraphrases per fact (zero external-API augmentation) into a LoRA adapter trained on the frozen conversational base
  2. Fresh-process, empty-prompt scripted recall meets pre-registered thresholds, with a context-token dump proving no prompt leakage and the base-without-adapter control failing closed-book
  3. Taught phrasings and never-seen phrasings are scored and reported separately (learning vs memorization), with all transcripts committed — failures included
  4. In the Gradio demo, the adapter toggles on/off live — same process, same prompt, memory on/off

**Plans**: TBD
**UI hint**: yes
**Research flag**: the clean-room protocol is synthesized from knowledge-injection literature (no canonical reference) and recall rates at 13.9M params are unknown — worth a discuss/spec pass on the teaching-set template grammar and threshold pre-registration before planning

### Phase 15: Figures & Writeup

**Goal**: The v2.0 narrative ships with the milestone's signature figures and honest numbers, in the same register as the v1.0 547-live-ids disclosure
**Depends on**: Phase 13 (A/B checkpoints + curves), Phase 14 (recall numbers); pure read-side
**Requirements**: VIZ-02, VIZ-03, DOC-02
**Success Criteria** (what must be TRUE):

  1. The weight-delta heatmap — relative Frobenius change `‖ΔW‖_F/‖W₀‖_F` on the layer×six-projection grid, log color scale — is committed to the repo
  2. The three-panel figure juxtaposing the Fisher heatmap with naive-vs-EWC delta heatmaps is committed, showing EWC visibly dodging high-Fisher coordinates
  3. REPORT.md and README carry the v2.0 narrative and demo.ipynb is updated with honest numbers (recall percentages, retention deltas, tokenizer-inflation tax), the named Fisher variant, and a real Limitations section

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 9 → 10 → 11 → 12 → 13 → 14 → 15
(9, 10, 11 are mutually independent; 12 needs 10+11; 13 needs 12; 14 needs 9+12; 15 needs 13+14)

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
| 9. LoRA Core | v2.0 | 4/4 | Complete   | 2026-06-11 |
| 10. EWC Core | v2.0 | 0/3 | Planned | - |
| 11. Conversational Data Pipeline | v2.0 | 0/TBD | Not started | - |
| 12. Stage-2 Conversational Fine-Tune | v2.0 | 0/TBD | Not started | - |
| 13. EWC A/B No-Forgetting Experiment | v2.0 | 0/TBD | Not started | - |
| 14. Teach-Then-Recall Demo | v2.0 | 0/TBD | Not started | - |
| 15. Figures & Writeup | v2.0 | 0/TBD | Not started | - |
