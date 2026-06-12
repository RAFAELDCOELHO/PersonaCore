---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Weight-Based Memory
status: ready_to_plan
stopped_at: Phase 10 complete (3/3) — ready to discuss Phase 11
last_updated: 2026-06-12T19:55:40.977Z
last_activity: 2026-06-12 -- Phase 10 execution started
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 7
  completed_plans: 7
  percent: 14
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-11)

**Core value:** Personalization lives in the weights, not a prompt or a store — and the from-scratch implementation must be correct enough to prove it. v1.0 shipped the correct from-scratch base LM; v2.0 delivers the weight-based memory (LoRA + EWC).
**Current focus:** Phase 11 — conversational data pipeline

## Current Position

Phase: 11
Plan: Not started
Status: Ready to plan
Last activity: 2026-06-12

Progress: [░░░░░░░░░░] 0% (v2.0)

## Performance Metrics

**Velocity (v1.0 baseline):**

- Total plans completed: 36 across 8 phases (v1.0)
- v2.0 plans completed: 0

**By Phase (v2.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 09 | 4 | - | - |
| 10 | 3 | - | - |

*v1.0 per-plan history archived in milestones/v1.0-phases/ SUMMARY frontmatter.*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table (v1.0 decisions archived with the milestone).

Key carry-forwards for v2.0:

- M2 seams are live and test-verified: six named `nn.Linear` projections per block (LoRA) and `assemble_loss(..., extra_penalties=())` + open-dict checkpoints (EWC — fisher/theta_star add with no format change).
- Frozen tokenizer KEPT for v2.0 (locked 2026-06-11): no retrain, `best.pt` stays valid as the M2 base; dead-id mask handles the 547-live-id vocabulary; inflation tax measured instead (DATA-04).
- Two-mechanism stage split (research-converged, treat as made): stage 2 = full fine-tune ± EWC (the A/B); stage 3 personalization = LoRA on the frozen conversational base.
- LOCKED contracts M2 must consume verbatim: `forward(idx, targets=None) -> (logits, loss)`; RNG-state-restore resume; `weights_only=True` slim artifacts.
- vocab_size=8192 / eos_id=8184 locked; role tokens `<|user|>`/`<|assistant|>`/`<|system|>` (8185-8187) already reserved and decodable.

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 12 research flag: λ selection + full-FT LR/budget calibration — plan with `/gsd-plan-phase --research-phase` (research/SUMMARY.md).
- Phase 14 research flag: teach-then-recall protocol has no canonical reference — discuss/spec pass on teaching-set grammar + threshold pre-registration before planning.
- DEBT-01/02 (run.csv ×256, forbid_ids-in-PPL policy) are Phase 12 pre-work and MUST land before the first v2.0 fine-tune step — forgetting-curve axes depend on them.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260605-lgy | MPS device-layer support: RuntimeConfig MPS detection (fp32/AMP-off, bf16-Pascal guard intact) + hard rename preflight_p100 → preflight_device (CUDA-P100 → MPS → CPU) | 2026-06-05 | 398b74e | [260605-lgy-add-mps-support-to-the-device-layer-runt](./quick/260605-lgy-add-mps-support-to-the-device-layer-runt/) |

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-06-11:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| quick_task | 260605-lgy-add-mps-support-to-the-device-layer-runt | metadata-only (work complete, committed 398b74e; SUMMARY frontmatter lacks a parseable status field) | v1.0 close |
| tech_debt | forbid_ids mask not threaded into scripts/evaluate.py warm sampling (CR-01 mode can recur on eval re-runs) | promoted to DEBT-02 → Phase 12 | v1.0 close |
| tech_debt | loop.py tokens_per_step omits ×block_size; run.csv "tokens" column under-counts ×256 (telemetry only) | promoted to DEBT-01 → Phase 12 | v1.0 close |
| tech_debt | TODO(calibration) markers on shipped-final constants in scripts/pretrain_tinystories.py | open — see v1.0-MILESTONE-AUDIT.md | v1.0 close |
| tech_debt | docs/REPORT.md under-discloses tokenizer training-corpus identity (11.5KB fixture → 547 live ids) | open — natural home: DOC-02 honesty pass (Phase 15) | v1.0 close |
| tech_debt | one-time `gh release view m1-demo-v1` asset check (tag verified, asset unverified from sandbox) | open — see v1.0-MILESTONE-AUDIT.md | v1.0 close |

## Session Continuity

Last session: 2026-06-12T09:12:48.057Z
Stopped at: Phase 10 context gathered
Resume file: .planning/phases/10-ewc-core/10-CONTEXT.md

## Operator Next Steps

- Plan the first v2.0 phase with `/gsd-plan-phase 9` (LoRA Core — standard patterns, no research-phase needed)
