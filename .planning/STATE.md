---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 02-01-PLAN.md
last_updated: "2026-06-04T19:33:38.003Z"
last_activity: 2026-06-04
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 6
  completed_plans: 4
  percent: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-04)

**Core value:** Personalization lives in the weights, not a prompt or a store — and the from-scratch implementation must be correct enough to prove it (Milestone 1 de-risks the foundation: a correct from-scratch base LM with a working generation demo).
**Current focus:** Phase 02 — from-scratch-bpe-tokenizer

## Current Position

Phase: 02 (from-scratch-bpe-tokenizer) — EXECUTING
Plan: 2 of 3
Status: Ready to execute
Last activity: 2026-06-04

Progress: [███████░░░] 67%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 9 | 3 tasks | 8 files |
| Phase 01 P02 | 14 | 2 tasks | 10 files |
| Phase 01 P03 | 4 | 2 tasks | 3 files |
| Phase 02 P01 | 8 | 3 tasks | 12 files |

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

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- Phase 5 (Pretraining): empirical LR/batch/steps and coherence-per-quota on P100 are unmeasured — phase-level research flagged before the long run.
- Phase 8 (Demo): KV-cache-vs-scope tension (PITFALLS recommends it for CPU latency; FEATURES marks it out of M1 scope) — resolve on measured CPU latency at phase planning.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-06-04T19:33:37.998Z
Stopped at: Completed 02-01-PLAN.md
Resume file: None
