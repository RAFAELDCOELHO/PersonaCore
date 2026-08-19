# PersonaCore

## What This Is

PersonaCore is a conversational AI assistant where **all** memory and personalization live in the model weights — no databases, no vector stores, no external files. The model learns who you are by updating its own parameters, making weight-based memory a privacy guarantee by design. The entire stack (GPT-style transformer decoder, BPE tokenizer, LoRA adapters, EWC continual learning) is built from scratch in PyTorch and runs fully on-device. It is an elite CS-undergraduate portfolio project intended to demonstrate deep ML fundamentals, a genuinely novel approach, and a working demo.

## Current State (v2.0 shipped 2026-08-12)

**Milestone 2 "Weight-Based Memory" is shipped — the novel claim is demonstrated, not asserted.**
A from-scratch LoRA adapter (331,776 params across six projections × six layers) teaches
user-specific facts into a frozen conversational base, and a **fresh process with the context
wiped** recalls them from an empty prompt: taught-template recall **0.4921** against a
pre-registered threshold of 0.2486, held-out phrasings **0.3483** against 0.2000, and the
adapter-off control on identical weights and identical prompts at exactly **0/2430** — with
adapter-off logits bit-identical to the un-adapted base (max |diff| 0.0). From-scratch EWC keeps
the fine-tune from destroying the base: from a shared 2.1076 step-0 anchor, naive retention PPL
ends at **8.524171** and EWC at **3.891140**, clearing the pre-registered margin by **33.61×**,
with acquisition cost reported descriptively (+0.380556, ~9.1%) so the win cannot be mistaken for
a failure to learn. Fisher/Δ correlation Spearman **ρ = 0.801544**, 95% CI [0.597984, 0.920291].

Milestone audit **passed**: 24/24 requirements, 7/7 phases verified, 17/18 integration links,
3/3 E2E flows. Suite: **408 passed / 1 skipped** (CUDA-only fp16 AMP smoke) / 0 failed, ruff clean.
364 commits over 62 days.

**The methodological spine, which is half the portfolio value:** every gate is a module-level
literal in a committed driver, pushed *before* the run it judges, and verdicts are computed by
importing those constants rather than retyping them in prose. Honest negatives stand unamended —
the λ sweep's "EWC not demonstrable at this budget" is still recorded as written, with the later
production λ=0.01 logged as a separate dated discretionary choice; the retention win is explicitly
scoped to teacher-forced PPL because free-running story mode survives in neither arm.

**Tech debt at v2.0 close:** v1.0's carried items are closed. DEBT-01 (`run.csv` token under-count)
landed before the first v2.0 training step; DEBT-02's warm-sampling half — `evaluate.py` sampling
without `forbid_ids`, open since v1.0 — was fixed 2026-08-12 (`3781a97`), with the headline 2.1066
verified byte-identical afterward. Remaining non-blocking notes live in
`milestones/v2.0-MILESTONE-AUDIT.md`: W1 (runtime consumers inject with `LoRAConfig()` defaults
instead of the artifact's own — benign today, silent if alpha ever diverges), W3 (one λ=0 frontier
point is a hand-entered literal because its CSV lacks a `retention_ppl` column), and `evaluate.py`
still being unseeded, which makes `results/samples.md` non-reproducible run to run.

<details>
<summary>v1.0 Foundation — shipped 2026-06-11 (archived)</summary>

## Current State (v1.0 shipped 2026-06-11)

**Milestone 1 "Foundation" is shipped.** A from-scratch 13,891,584-parameter GPT-2-style decoder, trained 50,000 steps on TinyStories entirely on the author's M3 (MPS, fp32), generates fluent child-story prose — `best.pt` val_loss 0.7378, headline perplexity **2.1066** over 12,636,922 held-out tokens. Shipped artifacts: offline Gradio CPU chat demo (slim 55.6 MB `weights_only=True` checkpoint, crash-proof dead-id logits mask), executed `demo.ipynb`, 440-line `docs/REPORT.md` + README with hero GIF, 4-variant ablation study, and a 137-test green CPU-only suite. Milestone audit passed 35/35 requirements with 20/20 cross-phase integration links verified live. Both M2 seams are locked and test-verified: six named `nn.Linear` projections per block (LoRA) and `assemble_loss(..., extra_penalties=())` + open-dict checkpoints (EWC).

**Known tech debt carried into M2** (none blocking; see `milestones/v1.0-MILESTONE-AUDIT.md`): the frozen tokenizer was trained on an 11.5KB fixture (547 live ids of 8192 — honestly documented, but consider retraining the tokenizer if M2 fine-tuning data warrants it, which would invalidate `best.pt`); `forbid_ids` mask not threaded into `evaluate.py`; `run.csv` tokens column ×256 under-count; stale TODO(calibration) markers.

**v2.0 progress:** Phase 9 (LoRA Core) complete 2026-06-11 — from-scratch `src/personacore/lora/` package (config/layer/inject), toggle/eject/merge runtime semantics, `export_adapter`/`load_adapter` persona-file artifact, and frozen-base training discipline proven on the real 13.9M base (331,776 trainable adapter params, 1.35 MB `adapter.pt`). Phase 10 (EWC Core) complete 2026-06-12 — from-scratch `src/personacore/continual/` package (`estimate_fisher` per-example diagonal Fisher + `EWCPenalty` quadratic anchor), additive `penalty_fn`/`checkpoint_extra` splice into the v1.0 loop with bit-identical golden-trajectory proof when off, `export_fisher`/`load_fisher` persistence, and a real N=2000 Fisher estimated at `best.pt` (spearman_half 0.989, 55.6 MB production cache). Phase 11 (Conversational Data Pipeline) complete 2026-07-31 — from-scratch `src/personacore/dialogue/` package (fb-dialog parser, detokenizer, role-token renderer, `encode_dialogue` with D-01 loss mask), additive `get_batch_memmap_masked` loader, checksum-gated PersonaChat self_revised acquisition (DailyDialog cut per D-00), committed tokenizer-inflation gate (`results/inflation_report.md`, user GO verdict: 1.129× ≤ 1.2× band, fit 99.96%), and the four aligned training bins (`data/dialog_{train,val}{,_mask}.bin` — 5.26M train / 638K val tokens, masked fraction ~0.43, D-07 persona cap 140). Suite now 250 passed / 1 skipped. Phase 12 (Stage-2 Conversational Fine-Tune) complete 2026-08-01 — additive loop seams (`train_mask_bin`/`val_mask_bin`/`extra_eval_fns`, v1.0 defaults bit-identical), `masked_perplexity()` gate metric + `generate(stop_ids=...)`, frozen 1.0M-token retention sub-bin with measured step-0 anchors (sub-bin 2.1076 / full-val 2.1065), and a fully pre-registered calibration smoke (budget → noise floor → masking verdict *unmasked* → LR → λ decade sweep). The §8 demonstrability verdict was honestly negative ("EWC not demonstrable at this budget", λ*=None under the blind 2×Δ_dialog margin) and stands unamended; production ran with a separately-recorded discretionary λ=0.01 (D-07 user override + GO). Production fine-tune of `best.pt`: 4000 steps on M3/MPS fp32, masked dialogue val PPL 4.5733, retention 2.1076 → 3.8911 (vs λ=0 collapse +3.85 at 1250 steps), 15 committed transcripts (30/30 stop-id termination), `convbase_best.pt` (EWC extras embedded) + `convbase_slim.pt` (`weights_only=True`) as the demo substrate, Phase-13 twin provenance logged. Verification passed 5/5; suite 274 passed / 1 skipped. Next: Phase 13 (EWC A/B No-Forgetting Experiment).

All six v2.0 target features shipped. Full detail: `milestones/v2.0-ROADMAP.md`,
`milestones/v2.0-REQUIREMENTS.md`, `milestones/v2.0-MILESTONE-AUDIT.md`.

</details>

## Current Milestone: v3.0 Adversarial Privacy Audit and Selective Memory Erasure

**Goal:** Stop asserting that weight-based memory is private and start measuring it — what weights
actually buy over prompting, whether separately-taught personas stay isolated under adversarial
collision, and whether an adversary can extract taught facts through a toggle that only ever
controlled availability.

**Target features:**
- **Phase 16 — Weight-vs-Prompt Measured Control (DEMO-F2, formalized).** Same question set, two
  conditions: the fact placed *in context* (prompt-stuffed) vs *adapter-only with an empty prompt*.
  Reuses the already-trained `persona_adapter.pt` — no new infrastructure, the cheapest of the
  three, and it answers the sharpest question first: what does memory-in-weights buy over
  prompting, as a number rather than an intuition.
- **Phase 17 — Multi-Persona Isolation Matrix (DEMO-F1, formalized as a matrix M_ij).** N=3-4
  deliberately *adversarial* personas — colliding names, contradictory values in the same slot,
  adapter A queried with B's prompt — scored as a full cross-matrix. The most collision-prone pair
  is replicated across seeds. Builds the persona generator DEMO-F1 always needed and never had.
- **Phase 18 — Black-Box Adversarial Extraction Audit.** An attacker with no adapter (the negative
  control) and an attacker with the adapter *active*, attempting paraphrase, prefix injection,
  role-play, and repeated attempts. Reframes the Phase-14 toggle as **availability, not
  authorization** — the honest reading of what that switch has always done.

**Deferred pending 16-18 results:** **Phase 19+ — Selective Erasure.** It enters the roadmap
formally only once the numbers from 16, 17 and 18 exist, because those numbers determine whether
erasure is worth attempting and what it would have to beat. Per the v2.0 pre-registration
discipline, the criteria for that decision are written down before the data can influence them.

**Phase 19 admitted and executed (completed 2026-08-19).** The gate authored the decision, not a
judgement made after seeing the result: `erasure_is_worth_attempting(92, 104, 0, 104)` returned True
on Phase 18's measured numbers under a rule committed at `23a830c` on 2026-08-12, *before Phase 16
ran*. 16 plans across 14 waves. **The committed `erasure_succeeded` returned `FAILURE`** — (a) clears
perfectly at 0/27, exactly on a blind-calibrated floor of `0.09107873950450847`; (b) fails all seven
gated non-targets, four at total generation loss; (c) fails on dialogue, both legs having been red
before any erasure ran. Erasing one taught fact took k = 78 of 288 rank-1 components spread across
all six layers and all six projections, destroying 77.6% of the dialogue adaptation.
**D8 branch = the cliff: selective erasure is not selective at 331,776 parameters** — published
unsoftened, with the rank-vs-NLL instrument disagreement as co-headline (the rank instrument returns
bit-identical readings for M1 and M2 across all eight slots while one arm's bystanders generate 0/27
and the other's generate 27/27). **Ship decision: `DO NOT SHIP`**, withholding exactly one claim —
that the verdict is mechanically reproducible by the pinned CLI alone — and withdrawing no
measurement. Milestone close remains a separate act.

**Explicitly out of scope for v3.0:** the frozen tokenizer / retrain question. It needs its own
conversation given the cost of invalidating every published checkpoint and number, and bundling it
into a privacy milestone would confound both.

**Key context:** phase numbering continues from v2.0, so v3.0 opens at **Phase 16**. Ordering is
cost-ascending and dependency-driven — 16 needs no new artifacts, 17 builds the persona generator,
18 consumes both. Compute is minutes-to-hours on the M3, not a new pretraining run.

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
- [x] EWC continual learning with Fisher-information penalty via the `assemble_loss(..., extra_penalties=())` seam — _Validated in Phase 10: EWC Core (EWC-01/02). From-scratch `continual/` package: `estimate_fisher` per-example empirical diagonal Fisher (strict batch=1 autograd loop, mean-normalized, analytic-oracle-pinned) + `EWCPenalty` Kirkpatrick quadratic exactly 0 at the anchor; additive `train(..., penalty_fn=None, checkpoint_extra=None)` splice proven bit-identical to v1.0 when off via pre-edit golden-trajectory fixture; `export_fisher`/`load_fisher` open-dict persistence with `data_ptr` tied-tensor dedup; real N=2000 Fisher at `best.pt` (spearman_half 0.989) — 42 new tests, see 10-VERIFICATION.md (12/12). λ calibration is EWC-03 (Phase 12); the A/B no-forgetting proof is Phase 13. Advisory debt: 10-REVIEW.md WR-01..05 (shape validation, reserved-key guard, train-mode finally, torch-version replay gate, best_val_loss resume reset)_

- [x] Conversational fine-tuning on PersonaChat (curriculum stage 2) — _Validated in Phase 11+12 (DATA-01..04, TUNE-01/02). PersonaChat `self_revised` only; **DailyDialog was cut** (D-00, 2026-07-31) after the tokenizer-inflation gate showed one corpus sufficed. From-scratch `dialogue/` package (fb-dialog parser, detokenizer, role-token renderer, span-wise `encode_dialogue` + D-01 loss mask), inflation measured **1.129×** against a same-run TinyStories baseline of 2.860 — inside the pre-registered ≤1.2× GO band, with 0.9996 of episodes fitting persona + first exchange in 256 tokens. Production fine-tune: 4000 steps M3/MPS fp32, λ=0.01, masked dialogue val PPL 4.5733, producing `convbase_best.pt` + `convbase_slim.pt` — see 11-/12-VERIFICATION.md_
- [x] Teach-then-recall (clean-room) personalization demo — memory lives in weights, not the prompt — _Validated in Phase 14 (DEMO-05/06/07). Closed-book, fresh process, context wiped: taught 496/1008 = **0.4921** vs threshold 0.2486, held-out families 326/936 = **0.3483** vs 0.2000, adapter-off control exactly **0/2430**. Thresholds derived on a **disjoint** calibration set and committed at `CALIBRATION_SHA 0425fdc4…` before the real run existed; every scored prompt's token ids recorded before the model was called, with a hard raise if any fact value appeared in a prompt. Live Gradio on/off toggle = 36 boolean writes on one model object, token panel byte-identical ON vs OFF while answers differ. Verdict **ADAPT — GO with two qualifications**, both recorded as named limitations — see 14-VERIFICATION.md (57/57)_
- [x] No-forgetting (EWC A/B vs naive fine-tuning) demo — _Validated in Phase 13 (DEMO-04, EWC-03). Two 4000-step arms identical but for the penalty: naive retention PPL **8.524171** vs EWC **3.891140** from a shared 2.1076 anchor, gate cleared by **33.61×** its pre-registered margin (2 × 0.068930). Acquisition reported descriptively with no gate. The phase's own negative leads its threats register: free-running story mode survives in neither arm (79 naive vs 69 EWC role-token leaks), so the claim is scoped to teacher-forced retention PPL — see 13-VERIFICATION.md_
- [x] Weight-delta heatmaps and forgetting-curve visualizations — _Validated in Phase 13+15 (VIZ-01..04). Figures are drawn **only** from the committed `results/phase15_norms.json`, by a module structurally forbidden from opening a checkpoint (AST walk over imports + fresh-interpreter probe that fails if `torch` lands in `sys.modules`). Fisher/Δ correlation Spearman **ρ = 0.801544**, CI [0.597984, 0.920291], gate passes on sign with magnitude explicitly descriptive at n=36 — see 15-VERIFICATION.md (51/51)_

### Active

<!-- Milestone v3.0: Adversarial Privacy Audit and Selective Memory Erasure — REQ-IDs land in REQUIREMENTS.md. -->

- [ ] Weight-vs-prompt measured control — quantify what memory-in-weights buys over prompt-stuffing, same questions, both conditions (Phase 16)
- [ ] Multi-persona isolation matrix M_ij under adversarial collision — colliding names, contradictory same-slot values, cross-adapter querying, seed-replicated worst pair (Phase 17)
- [ ] Black-box adversarial extraction audit — no-adapter negative control vs adapter-active attacker across paraphrase / prefix / role-play / repeated attempts (Phase 18)
- [ ] *(Deferred, gated on 16-18)* Selective erasure of a taught fact from the weights (Phase 19+)

### Out of Scope

<!-- Explicit boundaries. -->

- HuggingFace PEFT / transformers model code — excluded by design; everything is from scratch
- External AI APIs during training — excluded by design (zero budget, privacy, on-device)
- Databases, vector stores, RAG, external memory files — excluded by design; memory must live in weights
- Scaling beyond ~10–15M params or multi-GPU training — out of scope given the local M3/MPS (and fallback Kaggle free-tier) budget
- KV-cache for CPU inference — measured ~95–105 tok/s on CPU in Phase 8; not needed. **Reason confirmed at v2.0 close:** the Phase-14 demo streamed acceptably in a live browser (65 samples @ 200 ms, 0 shrink events), so the M2 trigger never fired
- Facts in a system prompt at demo time — falsifies the core claim; the empty-prompt clean room is the protocol. Prompt-stuffing appears only as the labeled future control DEMO-F2

## Context

- **Audience:** portfolio reviewers at the MIT/Stanford bar (admissions, research, recruiting) and the author. The work must read as rigorous, original, and self-implemented.
- **Two-milestone strategy:** De-risk the foundation before the novel claim. **Milestone 1** delivers a correct, from-scratch base language model with a working generation demo. **Milestone 2** delivers the differentiating weight-based memory (LoRA + EWC) and the research-narrative demos.
- **Curriculum plan (full project):** two-stage pretraining — TinyStories for base fluency, then DailyDialog + PersonaChat for conversational grounding. Milestone 1 covers only the TinyStories stage.
- **Dual-environment reality:** training runs **locally on Apple Silicon (M3 / MPS)** — fp32, since MPS has no fp16-AMP path; **Kaggle P100 (16GB, 30h/week) via notebooks remains an optional fallback**. The demo and inference run on a laptop CPU. Code must be portable across MPS, CUDA-P100, and CPU (`RuntimeConfig` resolves CUDA-P100 → MPS → CPU). Training on the author's own machine reinforces the on-device/privacy thesis.
- **Engineering rigor is a theme:** per-component unit tests and a documented technical narrative are first-class deliverables, not afterthoughts — they are part of what makes this a portfolio-grade artifact.
- **Codebase state after v2.0 (2026-08-12):** **408 tests green / 1 CUDA-only skip / 0 failed**, ruff clean; 364 v2.0 commits over 62 days (609 total), 284 files changed (+95,132 / −188) in the v2.0 range `d886aaf`..`ecf572d`. Package grew by three hand-rolled subsystems: `lora/` (config, layer, inject), `continual/` (Fisher, EWC penalty, persistence), `dialogue/` (parse, detokenize, serialize, encode+mask). Training bins: `data/dialog_{train,val}{,_mask}.bin` (5.26M train / 638K val tokens, masked fraction ~0.43) plus a frozen 1,000,286-token retention sub-bin. Shipped weights: `convbase_best.pt` / `convbase_slim.pt` (conversational base) + `persona_adapter.pt` (1.35 MB, 331,776 params). Committed evidence artifacts: `results/phase13_ab_report.md`, `phase14_recall_report.md`, `phase15_norms.json`, `retention_anchors.json`, and the two v2.0 figures.
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
| Two-stage pretraining curriculum (TinyStories → DailyDialog/PersonaChat) for the full project | Fluency first, then conversational/persona grounding; defensible at small scale | ✓ Good — stage 2 shipped in Phases 11-12, but **scope narrowed**: DailyDialog was cut (D-00, 2026-07-31) once PersonaChat `self_revised` alone cleared the inflation gate at 1.129× |
| Eventual demo = both teach-then-recall and EWC no-forgetting, as a research narrative | Strongest portfolio artifact; proves memory is in weights and survives continual learning | ✓ Good — both shipped and both gated. Recall 0.4921/0.3483 vs 0.2486/0.2000 with a 0/2430 control; A/B at 33.61× its margin |
| Gradio local web UI as primary demo + `demo.ipynb` as technical artifact | Good demo video/screenshots while staying on-device; notebook carries the ML narrative | ✓ Shipped in Phase 08 (offline ChatInterface + narrated notebook + GIF hero) |
| Document-as-we-go (polished writeup each milestone) | Narrative compounds; avoids reconstructing rationale later | ✓ M1 writeup shipped in Phase 08 (docs/REPORT.md + README) |
| Everything from scratch (transformer, BPE, LoRA, EWC) — no HF PEFT | The portfolio value is demonstrated depth, not library usage | ✓ Good — held for the whole project. v2.0 added hand-rolled `lora/` (LoRALinear, injection, toggle/eject, merge/unmerge), `continual/` (per-example diagonal Fisher, Kirkpatrick penalty) and `dialogue/` (parser, detokenizer, renderer, masked encoder). tiktoken/Gradio still confined to test-oracle/UI roles |
| Primary training target = local M3/MPS (fp32); Kaggle P100 demoted to optional fallback (decided Phase 5 discuss, 2026-06-05) | Strengthens the fully-on-device/zero-budget/privacy thesis — the model trains on the author's own machine, no external compute dependency. MPS has no fp16 AMP, so fp32; `RuntimeConfig` resolves CUDA-P100→MPS→CPU. | ✓ Good — the full 50k-step v1.0 pretrain ran entirely on the M3 (MPS fp32), kill+resume proven; Kaggle never needed |
| Ship the fixture-trained frozen tokenizer (547 live of 8192 ids) rather than retrain before Phase 5 (accepted Phase 8, documented in 08-08) | Retraining would have invalidated the locked vocab/checkpoint chain mid-milestone; honesty-first documentation instead (README/REPORT quantify 2,935,680 dead-row params) | ⚠️ Revisit in M2 — if conversational fine-tuning data warrants a real-corpus tokenizer, that decision invalidates `best.pt` and must be made before any M2 training |
| Dead-id `forbid_ids` logits mask at the sampling layer (Phase 8 CR-01) rather than catch-and-truncate at decode | Crash-proof demo at every in-UI setting without hiding real errors; decode stays strict by design | ✓ Good — and now fully threaded. The `evaluate.py` gap that stayed open across all of v1.0 and v2.0 was closed 2026-08-12 (`3781a97`); the headline 2.1066 was re-run and verified byte-identical, and greedy(masked) == greedy(unmasked) was asserted directly, proving the mask never moves the argmax |
| Retroactive Phase 5 verification at milestone audit (2026-06-11) instead of a closure phase | The work existed and was downstream-corroborated; only the formal verification artifact was missing | ✓ Good — passed 3/3; audit flipped to 35/35 without new phases |
| Keep the frozen tokenizer for v2.0 — no retrain (decided 2026-06-11 at v2.0 kickoff) | Dead-id mask already in place; M2 training time better spent on LoRA/EWC than a retrain; retraining would invalidate `best.pt` as the M2 base | ✓ Good — and the cost was **measured rather than assumed**: dialogue tokenizes at 3.229 tokens/word vs a same-run TinyStories baseline of 2.860, a 1.129× inflation inside the pre-registered ≤1.2× band. ⚠️ Revisit at v3.0 — still 547 live ids of 8192, and it is the largest remaining quality ceiling |
| Pre-registration lives in committed code, before any number exists (v2.0, all phases) | A threshold chosen after seeing the data is not a threshold. Putting the gate in a pushed commit makes the ordering a fact about the repo, not a claim in a paragraph; importing the constant instead of retyping it closes the drift half | ✓ Good — every v2.0 headline traces to a gate commit that provably precedes its artifact. Cost: it forced an honest all-fail verdict on the λ sweep that could not be quietly re-graded |
| Gate only the part of a claim the sample size supports; report the rest descriptively (v2.0) | Gating is meaningful only when the measurement can carry a threshold. Retention gated / acquisition descriptive; correlation sign gated / magnitude descriptive at n=36 | ✓ Good — prevented both failure modes: an EWC "win" bought by not learning, and a rank correlation being read as an effect size |
| Honest negatives are never edited in place; continuations are separate and dated after (v2.0) | The value of a recorded negative is that it was recorded before anyone knew if it would be convenient. Editing it later destroys exactly that, and invisibly | ✓ Good — the λ-sweep verdict, the recall ADAPT qualifications, and the free-running story-mode failure all still read as originally written. The report carries text now known to be wrong, corrected by dated note rather than by edit |
| Structural enforcement replaces declared invariants (v2.0) | A docstring asserting a property is true the day it is written and silently false after the next refactor; nothing notices. A checked mechanism fails loudly on every suite run | ✓ Good — named by the milestone's own learnings as its most recurring failure mode, then converted three times: demo mask comparison, prompt token-id check, and the plotting module's no-checkpoint guard (AST walk + fresh-interpreter probe, watched failing before being trusted) |
| Extract once from checkpoints, then plot only from a committed artifact (v2.0 Phase 15) | A committed PNG whose inputs are gitignored is an assertion, not evidence — nobody with a fresh clone can regenerate or audit it | ✓ Good — `results/phase15_norms.json` feeds the figures, the report's per-layer disclosure, and the correlation statistic. One source of truth, and the plotting half runs in the CPU-only suite |

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
*Last updated: 2026-08-19 — Phase 19 "Selective Memory Erasure" completed: verdict `FAILURE`, ship decision `DO NOT SHIP`. All four v3.0 phases (16-19) are complete; milestone close is a separate act.*
