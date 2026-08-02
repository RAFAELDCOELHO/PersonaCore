---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Weight-Based Memory
status: executing
stopped_at: Phase 15 context gathered
last_updated: "2026-08-02T19:05:17.591Z"
last_activity: 2026-08-02
progress:
  total_phases: 7
  completed_phases: 6
  total_plans: 39
  completed_plans: 32
  percent: 82
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-11)

**Core value:** Personalization lives in the weights, not a prompt or a store — and the from-scratch implementation must be correct enough to prove it. v1.0 shipped the correct from-scratch base LM; v2.0 delivers the weight-based memory (LoRA + EWC).
**Current focus:** Phase 15 — figures-writeup

## Current Position

Phase: 15 (figures-writeup) — EXECUTING
Plan: 2 of 8
Status: Ready to execute
Last activity: 2026-08-02

Progress: [████████░░] 82%

## Performance Metrics

**Velocity (v1.0 baseline):**

- Total plans completed: 49 across 8 phases (v1.0)
- v2.0 plans completed: 0

**By Phase (v2.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 09 | 4 | - | - |
| 10 | 3 | - | - |
| 11 | 4 | - | - |
| 12 | 5 | - | - |
| 13 | 4 | - | - |

*v1.0 per-plan history archived in milestones/v1.0-phases/ SUMMARY frontmatter.*
| Phase 12 P01 | 14min | 3 tasks | 3 files |
| Phase 12 P02 | 8min | 2 tasks | 5 files |
| Phase 12 P03 | 15min | 2 tasks | 2 files |
| Phase 12 P04 | 5h | 3 tasks | 16 files |
| Phase 12 P05 | 45min | 3 tasks | 5 files |
| Phase 13 P01 | 22min | 3 tasks | 3 files |
| Phase 13 P02 | 82min | 2 tasks | 2 files |
| Phase 13 P03 | 24min | 2 tasks | 6 files |
| Phase 13 P04 | 18min | 2 tasks | 1 files |
| Phase 14 P11 | 70min | 3 tasks | 10 files |
| Phase 15 P01 | 12min | 3 tasks | 3 files |

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
- [Phase 12]: 12-03: data/retention_val.bin NOT committed (data/ wholly gitignored) — frozen-ness = refuse-to-rerun SystemExit + seeded default_rng(1337) build, bit-reproducible from val.bin
- [Phase 12]: 12-03: step-0 anchors measured and committed pre-training — subbin 2.1076 (1,000,285 tok) is THE curve anchor; masked fullval 2.1065 < 2.1066 headline held with ~5e-5 margin
- [Phase 12]: 12-04: Stage-2 gate fired on all LR arms (no-EWC retention collapse) — user override RECORDED, gate NOT amended; λ sweep at LR 9e-5 with λ=0 drift +3.85 as the formal collapse baseline
- [Phase 12]: 12-04: §8 verdict recorded verbatim — λ*=None, EWC not demonstrable at the 1250-step budget (no λ within 2×Δ_dialog of λ=0); every λ arm beat the collapse baseline on retention
- [Phase 12]: 12-04: production λ=0.01 is a SEPARATE post-verdict discretionary decision (case b: feeds Phase-14 demo substrate only) — 12-05 config: unmasked, LR 9e-5, λ=0.01, 4000 steps, seed 1337
- [Phase 12]: 12-05: production run best == final step 4000 (masked val_loss 1.5236 still improving at budget) - retention drift +1.78 vs lambda=0 collapse +3.85; convbase trio with embedded EWC extras is the Phase 13/14 substrate
- [Phase 12]: 12-05: transcript proxies reported honestly - 30/30 stop-id termination, leakage 1 (one warm assistant-turn re-open), masked dialogue val PPL 4.5733; REPRESENTATIVE, never cherry-picked
- [Phase 13]: 13-01: pre-registration lives in the committed driver (constants + gate as module-level pure functions); tests load scripts/finetune_ab.py via importlib rather than moving rules into the package where the driver could drift
- [Phase 13]: 13-01: MARGIN = 2 x 0.068930 = 0.137860 vs the smoke report's displayed 0.137861 (unrounded floor) — recorded as a table note, neither number fudged
- [Phase 13]: 13-01: naive arm still CONSTRUCTS EWCPenalty (RNG-free, trajectory-safe) so both CSV schemas match — ewc_penalty is diagnostic-only there; checkpoint_extra is EWC-arm-only
- [Phase 13]: 13-01: D-11 divergence SystemExit fires AFTER all outputs are saved — a mismatch blocks report finalization without losing a 37-minute run
- [Phase 13]: 13-02: step-250 twin check passed on train_loss + ewc_penalty BIT-IDENTITY to finetune_prod.csv; eval PPL columns differ by 3.6e-8 (MPS reduction-order variance, not data-order drift) — no relaunch, trajectory provably identical to production
- [Phase 13]: 13-02: D-11 reproduction effectively exact (retention delta +1.1e-7, dialogue +2.9e-8 vs the 12-05 production run) — finetune_ab.py confirmed a faithful twin of finetune_dialog.py
- [Phase 13]: 13-02: pre-registered gate PASSES at 33.6x margin — naive retention 8.524171 vs EWC 3.891140 (delta 4.633031 vs MARGIN 0.137860); EWC costs +0.380555 dialogue PPL, descriptive with no gate (D-06)
- [Phase 13]: 13-03: D-12 samples surface an honest negative — BOTH arms leak role tokens mid-story (79 naive / 70 EWC), so the 4.63-PPL retention gap does NOT translate into free-running story-mode adherence; 13-04 may claim the retention-PPL gate, NOT qualitative retention
- [Phase 13]: 13-03: free-running generation IS bit-identical across processes on MPS (sample body diff empty over two runs) — unlike eval PPL (~1e-8); safe reproducibility claim for the report
- [Phase 13]: 13-03: VIZ-04 lambda=0 point is hardcoded-with-citation (4.4453, 5.9553; smoke report Stage 2/3, 666d096) because ft_lr_9e-5.csv has no retention column — six-point count pinned by test so the Pitfall-1 five-point regression cannot recur
- [Phase 13]: 13-04: report claim scoped to teacher-forced retention PPL only — measured 79/70 role-token leakage means generative retention is NOT claimed
- [Phase 14]: 14-11: real teaching run produced checkpoints/persona_adapter.pt (331,776 params, 1.35 MB) — canary proved every trainable moved and every frozen base param bit-untouched
- [Phase 14]: 14-11: fresh-process recall PASSED both pre-registered gates — taught 496/1008 = 0.4921 vs 0.2486, held-out 326/936 = 0.3483 vs 0.2000, closed-book control exactly 0/2430; the D-20 Pre-Registered Failure Branch was NOT taken
- [Phase 14]: 14-11: D-11.1 question-fairness control came back near-negative (1/1944) — the base cannot extract a fact even from its own persona span; the pre-registered (a)/(b)/(c) reconciliation stands unamended and the adapter-on/off differential is unaffected
- [Phase 14]: 14-11: Control 3 bit identity measured max abs diff exactly 0.0 on CPU on the real weights — the demo's memory-OFF state IS the un-adapted base, not a second adapted model
- [Phase 14]: 14-11: TRANSCRIPTS_PATH renamed to results/phase14_transcripts.md — the code was the sole outlier against five planning documents and the report pointed at a nonexistent file
- [Phase 14]: recall gate verdict recorded ADAPT — GO with two qualifications (residual collateral collapse +27.16%; question-fairness control 1/1944), both reported as named limitations ALONGSIDE the passed gate numbers, not folded into them; no locked threshold touched and the post-verdict Ship Decision section correctly stays empty
- [Phase 14]: DEMO-07 verified in a live browser — token panel byte-identical across memory ON/OFF for the same question while the answers differ, zero third-party origins on load, 0 shrink events over 65 stream samples, Reset one-way with the chat still live
- [Phase 15]: 15-01: R5 arbitration committed as a literal — the bootstrap CI is the LOAD-BEARING half of the D-11 gate, the permutation p is purely descriptive and never converts a MISS into a PASS
- [Phase 15]: 15-01: average-rank Spearman DIVERGES from continual/fisher.py::_spearman (ordinal, no tie averaging, returns 1.0 where the answer is 0.9486832980505139) — both correct for their own callers, pinned by test so a future 'unify the duplicate' goes red
- [Phase 15]: 15-01: pre-registration commit is 0e1af98 — rule, seed, sign, resample counts and gate only; Plan 15-04 cites it in the Evidence Index addendum and PREREG_COMMIT already carries it
- [Phase 15]: 15-01: percentile bootstrap KEPT (not upgraded to BCa) with its known small-n bias named in the pre-registration rather than silently omitted or silently upgraded after the result is seen

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 12 research flag: λ selection + full-FT LR/budget calibration — plan with `/gsd-plan-phase --research-phase` (research/SUMMARY.md).
- DEBT-01/02 (run.csv ×256, forbid_ids-in-PPL policy) are Phase 12 pre-work and MUST land before the first v2.0 fine-tune step — forgetting-curve axes depend on them.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260605-lgy | MPS device-layer support: RuntimeConfig MPS detection (fp32/AMP-off, bf16-Pascal guard intact) + hard rename preflight_p100 → preflight_device (CUDA-P100 → MPS → CPU) | 2026-06-05 | 398b74e | [260605-lgy-add-mps-support-to-the-device-layer-runt](./quick/260605-lgy-add-mps-support-to-the-device-layer-runt/) |
| 260801-r9y | Phase-13 closeout corrections: ROADMAP SC1 names the arms that actually ran (λ=0 vs pre-chosen λ=0.01, citing the A/B report); stop-fraction note derived from measured counts in script + markdown; plot_phase13 fails loudly on a missing/blank column and pins the frontier endpoint to step 1250 (both PNGs SHA-256-identical) | 2026-08-01 | d679440, 8812638, f0bae0b | [260801-r9y-SUMMARY.md](./quick/260801-r9y-SUMMARY.md) |
| 260802-h3g | CR-02 follow-through (14-SECURITY UF-4): the anchored verdict-SECTION read extracted to `scripts/_verdict.py` and wired into the two remaining naive `split("## Verdict")[-1]` guards — `teach_persona._refuse_clobber` and `phase14_factset_gate`, whose inline `main()` block was extracted so it is testable without a checkpoint. RED proven against the unmodified guards; the naive tail is kept in the test as a regression tripwire | 2026-08-02 | f16ce64, 2b8ed33, a39b753 | [260802-h3g-anchor-the-verdict-section-clobber-guard](./quick/260802-h3g-anchor-the-verdict-section-clobber-guard/) |

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

Last session: 2026-08-02T19:05:07.053Z
Stopped at: Phase 15 context gathered
Resume file: None

## Operator Next Steps

- Plan the final v2.0 phase with `/gsd-plan-phase 15` (Figures & Writeup — consumes the Phase 13 curves and the Phase 14 recall evidence)
