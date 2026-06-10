---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 8 UI-SPEC approved
last_updated: "2026-06-10T22:15:50.757Z"
last_activity: 2026-06-10 -- Phase 08 execution started
progress:
  total_phases: 8
  completed_phases: 7
  total_plans: 29
  completed_plans: 27
  percent: 88
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-04)

**Core value:** Personalization lives in the weights, not a prompt or a store — and the from-scratch implementation must be correct enough to prove it (Milestone 1 de-risks the foundation: a correct from-scratch base LM with a working generation demo).
**Current focus:** Phase 08 — demo-writeup

## Current Position

Phase: 08 (demo-writeup) — EXECUTING
Plan: 1 of 8
Status: Executing Phase 08
Last activity: 2026-06-10 -- Phase 08 execution started

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 16
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 02 | 3 | - | - |
| 03 | 4 | - | - |
| 04 | 3 | - | - |
| 06 | 3 | - | - |
| 07 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 9 | 3 tasks | 8 files |
| Phase 01 P02 | 14 | 2 tasks | 10 files |
| Phase 01 P03 | 4 | 2 tasks | 3 files |
| Phase 02 P01 | 8 | 3 tasks | 12 files |
| Phase 02 P02 | 4 | 2 tasks | 4 files |
| Phase 02 P03 | 6 | 3 tasks | 5 files |
| Phase 03 P01 | 6 | 5 tasks | 8 files |
| Phase 03 P02 | 6 | 2 tasks | 3 files |
| Phase 03 P03 | 7 | 2 tasks | 2 files |
| Phase 03 P04 | 18 | 2 tasks | 4 files |
| Phase 04 P01 | 6 | 2 tasks | 9 files |
| Phase 04 P02 | 8 | 2 tasks | 2 files |
| Phase 04 P03 | 4 | 1 tasks | 1 files |
| Phase 05 P01 | 6 | 3 tasks | 5 files |
| Phase 07 P01 | 4 | 2 tasks | 4 files |
| Phase 07 P02 | 11 | 2 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: fp32 training by default at 10–15M params; fp16 AMP+GradScaler only as a memory measure; bf16 guarded to error on Pascal/P100.
- [Roadmap]: Bigram baseline + harness (Phase 3) proves the training/checkpoint/sampling loop before the GPT (Phase 4) is built.
- [Roadmap]: Two M2 seams are M1 acceptance criteria — named `nn.Linear` projections (Phase 4) and `assemble_loss(...)` + open-dict checkpoints (Phases 1/3) — so LoRA/EWC are additive in M2.
- [Roadmap]: Document-as-we-go (DOC-01) consolidated lightly in Phase 8, not a heavy standalone block.
- [Phase ?]: [01-01]: torch excluded from core deps; offered only as [cpu] extra (D-10) — prevents a cu128+ wheel bricking the Kaggle P100.
- [Phase ?]: [01-01]: RuntimeConfig is the single device/precision source — fp32 default, AMP off on CPU, bf16 raises on Pascal/P100 (cc < 7.0).
- [Phase ?]: [01-02]: Resume checkpoint loads with weights_only=False (trusted own-file; torch>=2.6 default flipped to True). Slim inference checkpoint (Phase 8) uses weights_only=True.
- [Phase ?]: [01-02]: Checkpoint is an open dict; load restores RNG STATE (not re-seed) -> kill-and-resume trajectory equality within 1e-6. Also the M2 EWC seam (fisher/theta_star add with no format change).
- [Phase ?]: [01-02]: preflight_p100(require_p100=False) degrades to a CPU summary instead of raising when CUDA is absent (demo runs on a laptop); require_p100=True still fails loud on Kaggle.
- [Phase ?]: [01-03]: CI pins Python 3.11 (Kaggle parity), never the local 3.14 dev box, so install-parity is validated against the real runtime target.
- [Phase ?]: [01-03]: ENV-06 docs appended OUTSIDE the GSD marker blocks in CLAUDE.md; CPU-only CI (no GPU/training) is the phase gate re-validating ENV-01/ENV-02.
- [Phase ?]: [02-01]: vocab_size=8192 + eos_id=8184 locked in ModelConfig (D-01/D-03); Phases 3-4 size around them and they never move.
- [Phase ?]: [02-01]: regex is a core runtime dep (GPT-2 pre-tok primitive, not a from-scratch violation); tiktoken is [dev]-only with a no-runtime-import guard (T-02-01).
- [Phase ?]: [02-01]: Wave-0 tokenizer tests written RED first; go green in Plan 02 (train/roundtrip/special) and Plan 03 (io/oracle).
- [Phase ?]: [02-02]: BPETokenizer() is default-constructible then .train(text, vocab_size); merges/vocab populate on train() or frozen() (Plan-01 test contract).
- [Phase ?]: [02-02]: oracle library name kept out of runtime src/ (reworded docstrings) so the no-runtime-oracle string-scan guard stays green (T-02-04).
- [Phase ?]: [02-02]: decode maps a special id back to its literal marker, so round-trip holds even for embedded special-token literals.
- [Phase ?]: [02-03]: tokenizer artifact is stdlib json data-only (NOT pickle/torch); from_json asserts schema_version (T-02-06) + validates ids in [0,vocab_size) (V5) — a shippable artifact must never execute code on load (T-02-05)
- [Phase ?]: [02-03]: artifacts/tokenizer.json is the FROZEN production 8192-vocab artifact; Phase 5 reuses it unchanged with no retrain (D-09)
- [Phase ?]: [02-03]: TOK-05 oracle proves the lowest-rank-first ALGORITHM via byte->rank-remapped replay (gpt2 leaves are rank-ordered, byte!=rank); recover_merges adapter lives in the test not runtime src/, keeping the no-runtime-tiktoken guard green (D-07)
- [Phase 03]: [03-01] GPU fp16 smoke uses inline pytest.mark.skipif WITH required reason= (clean SKIP not collection ERROR on CPU CI); exact verify literal skipif(not torch.cuda.is_available()) preserved in a comment
- [Phase ?]: [03-02]: BigramLanguageModel honors the LOCKED forward(idx, targets=None) -> (logits, loss) contract (D-02) with internal CE on the nanoGPT (B*T, V) flatten (D-02a); Phase-4 GPT reuses it unchanged.
- [Phase ?]: [03-02]: assemble_loss lives in training/loss.py not the model (D-03); identity-on-empty in M1, additive (fisher_penalty,) in M2 EWC with no loop change (D-04).
- [Phase ?]: [03-02]: training/__init__.py deliberately not created — Plan 04 owns the full training surface; namespace-package discovery resolves personacore.training.loss without it.
- [Phase ?]: [03-03]: doc-level split drops the fixture trailing newline so val is not a degenerate one-token doc (no-leakage TRAIN-03); warmup+cosine LR wrapped in LambdaLR for the checkpoint state_dict() resume contract (TRAIN-01/D-05/D-08).
- [Phase ?]: [03-04]: training loop AMP order scale-unscale_-clip-step-update; scheduler steps once per optimizer step; estimate_loss snapshots/restores RNG so periodic eval never perturbs the train trajectory (TRAIN-02/04).
- [Phase ?]: [03-04]: CSV wall_clock is a logical step-derived clock (not wall time) so the loss/lr curve reproduces row-for-row across kill+resume; cumulative tokens derived from absolute step (TRAIN-04).
- [Phase ?]: [03-04]: bigram embedding renamed token_table to token_embedding_table (nanoGPT-canonical, locked resume-test contract); model/tokenizer vocab gap bridged in train_bigram.py, decode stays strict by design (WR-03).
- [Phase ?]: [04-01]: attn_impl is a GPT constructor arg (not a ModelConfig field) per RESEARCH Open Q2 — equivalence test exercises both manual/sdpa paths; keeps the asdict-serialized ModelConfig free of a runtime-only flag.
- [Phase ?]: [04-01]: init test matches std targets by named-param SUFFIX (so blocks.N.* match) and asserts BOTH c_proj AND fc_out were seen — non-vacuous D-04a residual-scaling guard.
- [Phase ?]: [04-01]: GPT overfit test seeds lr=1e-3/max_steps=300 as a starting point (vs bigram 1e-1); final 6-layer tuning delegated to Plan-03 executor, asserted bound is a band (< ln(8192)-2).
- [Phase ?]: [04-02]: GPT decoder ships with attn_impl as a constructor arg (default manual); manual and sdpa paths share q/k/v projection so equivalence holds within atol 1e-5.
- [Phase ?]: [04-02]: weight tying is nn.Parameter assignment AFTER init+residual-override (Pattern 1) so data_ptr is shared; lm_head bias=False keeps the tied weight the sole head param.
- [Phase ?]: [04-02]: residual-scaled init 0.02/sqrt(2*n_layer) applied to BOTH c_proj AND fc_out (D-04a), not just c_proj.
- [Phase ?]: [04-03]: the real 6-layer GPT(ModelConfig()) overfits one fixed batch through the UNTOUCHED Phase-3 train() loop at lr=1e-3/max_steps=300 (final loss ~5e-4) — MODEL-02 SC#1 harness-swap proof GREEN, zero harness changes.
- [Phase ?]: [05-01]: get_batch_memmap mirrors get_batch indexing exactly; only change is re-opening np.memmap per call (nanoGPT leak-avoidance, Pitfall 1).
- [Phase ?]: [05-01]: encode_corpus.py streams per-<|endoftext|> document; allowed_special=all emits one atomic eos 8184 per doc — no manual EOS injection (D-09).
- [Phase ?]: [07-01]: perplexity denominator is Sigma(len(window)-1); with the +1 overlapping-boundary slice a cleanly-tiling corpus yields corpus_len-1, not corpus_len-n_windows (test_token_count corrected the RESEARCH shorthand)
- [Phase ?]: [07-01]: perplexity() ignores forward's MEAN loss and recomputes F.cross_entropy(reduction='sum') from logits; returns (ppl, total_tokens) so the headline number is auditable (D-03)
- [Phase ?]: [07-02]: weight_tying/use_pos_emb are ADDITIVE ModelConfig flags defaulting to True — GPT(ModelConfig()) reproduces today's arch bit-for-bit (tied data_ptr, 13,891,584 params); the ablations are now expressible
- [Phase ?]: [07-02]: wpe is gated at REGISTRATION (if config.use_pos_emb), not only forward use — required for the locked test_no_pos count 13,793,280 (default - 98,304)
- [Phase ?]: [07-02]: canonical headline PPL is the deterministic full-val sweep (2.1066 over 12,636,922 tokens), distinct from best.pt's recorded random-batch ppl 2.091 (Pitfall 5)

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- Phase 5 (Pretraining): empirical LR/batch/steps and coherence-per-quota on P100 are unmeasured — phase-level research flagged before the long run.
- Phase 8 (Demo): KV-cache-vs-scope tension (PITFALLS recommends it for CPU latency; FEATURES marks it out of M1 scope) — resolve on measured CPU latency at phase planning.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260605-lgy | MPS device-layer support: RuntimeConfig MPS detection (fp32/AMP-off, bf16-Pascal guard intact) + hard rename preflight_p100 → preflight_device (CUDA-P100 → MPS → CPU) | 2026-06-05 | 398b74e | [260605-lgy-add-mps-support-to-the-device-layer-runt](./quick/260605-lgy-add-mps-support-to-the-device-layer-runt/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-06-10T14:13:19.294Z
Stopped at: Phase 8 UI-SPEC approved
Resume file: .planning/phases/08-demo-writeup/08-UI-SPEC.md
