---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Weight-Based Memory
status: executing
stopped_at: Completed 12-01-PLAN.md
last_updated: "2026-08-01T04:25:42.685Z"
last_activity: 2026-08-01
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 16
  completed_plans: 13
  percent: 43
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-11)

**Core value:** Personalization lives in the weights, not a prompt or a store — and the from-scratch implementation must be correct enough to prove it. v1.0 shipped the correct from-scratch base LM; v2.0 delivers the weight-based memory (LoRA + EWC).
**Current focus:** Phase 12 — stage-2-conversational-fine-tune

## Current Position

Phase: 12 (stage-2-conversational-fine-tune) — EXECUTING
Plan: 3 of 5
Status: Ready to execute
Last activity: 2026-08-01

Progress: [████████░░] 81%

## Performance Metrics

**Velocity (v1.0 baseline):**

- Total plans completed: 40 across 8 phases (v1.0)
- v2.0 plans completed: 0

**By Phase (v2.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 09 | 4 | - | - |
| 10 | 3 | - | - |
| 11 | 4 | - | - |

*v1.0 per-plan history archived in milestones/v1.0-phases/ SUMMARY frontmatter.*
| Phase 12 P01 | 14min | 3 tasks | 3 files |
| Phase 12 P02 | 8min | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table (v1.0 decisions archived with the milestone).

Key carry-forwards for v2.0:

- M2 seams are live and test-verified: six named `nn.Linear` projections per block (LoRA) and `assemble_loss(..., extra_penalties=())` + open-dict checkpoints (EWC — fisher/theta_star add with no format change).
- Frozen tokenizer KEPT for v2.0 (locked 2026-06-11): no retrain, `best.pt` stays valid as the M2 base; dead-id mask handles the 547-live-id vocabulary; inflation tax measured instead (DATA-04).
- Two-mechanism stage split (research-converged, treat as made): stage 2 = full fine-tune ± EWC (the A/B); stage 3 personalization = LoRA on the frozen conversational base.
- LOCKED contracts M2 must consume verbatim: `forward(idx, targets=None) -> (logits, loss)`; RNG-state-restore resume; `weights_only=True` slim artifacts.
- vocab_size=8192 / eos_id=8184 locked; role tokens `<|user|>`/`<|assistant|>`/`<|system|>` (8185-8187) already reserved and decodable.
- [Phase 12]: 12-01: val_mask_bin ships (USER LOCK 3) — in-loop val_loss gates best.pt selection, selected FOR assistant-token dialogue capability; unmasked CE would partially reward modeling user turns
- [Phase 12]: 12-01: v1.0 eval block logs NO step-0 row — block runs after step += 1; Plan 12-04 must measure step-0 retention baseline outside train()
- [Phase 12]: 12-02: masked_perplexity is THE frozen dialogue-val gate metric for all Phase 12 arms — oracle-proven hand-counted denominator; estimate_loss's random-batch mean disallowed for gates
- [Phase 12]: 12-02: stop_ids REPLACES the EOS stop set (EOS only stops when a member) — pinned by test; transcripts pass {8184, 8185}

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

Last session: 2026-08-01T04:24:48.404Z
Stopped at: Completed 12-01-PLAN.md
Resume file: None

## Operator Next Steps

- Plan the first v2.0 phase with `/gsd-plan-phase 9` (LoRA Core — standard patterns, no research-phase needed)
