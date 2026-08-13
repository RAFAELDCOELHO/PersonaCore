---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Adversarial Privacy Audit and Selective Memory Erasure
status: Context gathered, awaiting /gsd-plan-phase 16
stopped_at: v3.0 roadmap created — Phases 16-18 defined, 26/26 requirements mapped, Phase 19+ left deliberately unplanned behind the pre-registered erasure gate
last_updated: "2026-08-13T01:07:46.135Z"
last_activity: "2026-08-12 — Phase 16 discussion complete: 6 areas, 31 decisions, 16-CONTEXT.md landed; ROADMAP SC2/SC5 amended"
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-12)

**Core value:** Personalization lives in the weights, not a prompt or a store — and the from-scratch implementation must be correct enough to prove it. v1.0 shipped the correct from-scratch base LM; v2.0 **demonstrated** the weight-based memory (LoRA + EWC) under pre-registered gates.
**Current focus:** v3.0 Adversarial Privacy Audit and Selective Memory Erasure — roadmap created 2026-08-12: Phase 16 (Weight-vs-Prompt Persistence Control) → 17 (Multi-Persona Isolation Matrix) → 18 (Black-Box Adversarial Extraction Audit). 26/26 in-scope requirements mapped, 0 orphans. Phase 19+ Selective Erasure deliberately unplanned — it enters the roadmap only if `erasure_is_worth_attempting()` (pre-registered at `23a830c`, before Phase 16 runs) returns True on Phase 18's measured numbers.

## Current Position

Phase: 16 — Weight-vs-Prompt Persistence Control (not started)
Plan: —
Status: Context gathered, awaiting /gsd-plan-phase 16
Last activity: 2026-08-12 — Phase 16 discussion complete: 6 areas, 31 decisions, 16-CONTEXT.md landed; ROADMAP SC2/SC5 amended

## Performance Metrics

**Velocity (v1.0 baseline):**

- v1.0: 29 plans across 8 phases (shipped 2026-06-11)
- v2.0: **39 plans across 7 phases** (shipped 2026-08-12), 364 commits over 62 days

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
| Phase 15 P02 | 18min | 3 tasks | 3 files |
| Phase 15 P03 | 24min | 3 tasks | 4 files |
| Phase 15 P04 | 14min | 2 tasks | 2 files |
| Phase 15 P05 | 41min | 3 tasks | 1 files |
| Phase 15 P06 | 17min | 2 tasks | 1 files |
| Phase 15 P07 | 22min | 3 tasks | 3 files |
| Phase 15 P08 | 34min | 2 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table (v1.0 decisions archived with the milestone).

Key carry-forwards for v2.0:

- M2 seams are live and test-verified: six named `nn.Linear` projections per block (LoRA) and `assemble_loss(..., extra_penalties=())` + open-dict checkpoints (EWC — fisher/theta_star add with no format change).
- Frozen tokenizer KEPT for v2.0 (locked 2026-06-11): no retrain, `best.pt` stays valid as the M2 base; dead-id mask handles the 547-live-id vocabulary; inflation tax measured instead (DATA-04).
- Two-mechanism stage split (research-converged, treat as made): stage 2 = full fine-tune ± EWC (the A/B); stage 3 personalization = LoRA on the frozen conversational base.
- LOCKED contracts M2 must consume verbatim: `forward(idx, targets=None) -> (logits, loss)`; RNG-state-restore resume; `weights_only=True` slim artifacts.
- vocab_size=8192 / eos_id=8184 locked; role tokens `<|user|>`/`<|assistant|>`/`<|system|>` (8185-8187) already reserved and decodable.

Key carry-forwards for v3.0 (locked before Phase 16 plans, do not re-litigate):

- `results/phase16_recall_sample.json` (270 questions, committed) is THE binding evaluation fixture. Phases 17 and 18 consume that same fixture — no regenerated variant, no resampling; pinned by `tests/test_phase16_fixture_regen.py`.
- Phase 16 is a FOUR-arm comparison — prompt-stuffed / adapter-only / base-with-neither / embedding-cosine (PERS-04) — framed neutrally with no presupposed winner. Phase 14's 1/1944 in-context control means prompt-stuffing is at the floor; a "weights beat prompting ~1000x" headline would be measuring a capability deficit and is refuted by a number already in this repo.
- Bootstrap resampling is at FACT level (n=8), not question level. The exact paired sign test over 2^8 = 256 partitions is the inferential gate; the bootstrap CI is descriptive.
- Under Holm (STAT-03) across 6 pairwise arm comparisons, only 8/8 unanimity clears (p = 0.007812 < 0.05/6). "Not demonstrable at n=8" is a legitimate pre-registered Phase-16 outcome, recorded as-written, exactly as Phase 12 recorded lambda*=None.
- W1 (`LoRAConfig()` defaults instead of `LoRAConfig(**artifact["lora_config"])`) must land before ANY Phase-17 adapter trains — shape audits catch `r` drift but never `alpha`.

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
- [Phase 15]: 15-02: the adapter's W0 is convbase_best.pt (04e724c6/4000/1.5235939979553224), proven by a raise SystemExit fingerprint guard — CONTEXT D-08 names five checkpoints, there are six, and load_adapter only WARNS where a committed figure cannot afford a warning
- [Phase 15]: 15-02: Fisher reduced per cell by MEAN, recorded as fisher_aggregate in the data — the cache is mean-normalized so a mean reads as 'x the importance of an average parameter'; a sum would confound importance with tensor size
- [Phase 15]: 15-02: vmax drivers recorded verbatim — adapter L1/c_proj 0.04738638857364279, naive L1/c_proj 0.22023983403635128, ewc L1/q_proj 0.13806389791647683, fisher L0/c_proj 6.541458482610652; all four nonpositive_cells are 0; EWC's max is ~63% of naive's, so the shared-scale compression IS the finding (D-01)
- [Phase 15]: 15-02: the byte-for-byte reproduction test normalizes the TWO top-level run-provenance fields (git_sha, built) and nothing else — nested checkpoint fingerprints are still compared byte-for-byte as the audit trail
- [Phase 15]: 15-02: ROADMAP SC3's named Fisher variant now lives in the artifact — empirical_diag_fisher/groundtruth_targets/mean_normalized, n_examples 2000, seed 1234; Plans 15-05 and 15-07 must reproduce it character-for-character
- [Phase 15]: 15-03: D-01 proven by object identity through _norms(), not by equal (vmin,vmax) — a two-norm implementation with matching bounds would pass a value check and split into two scales on the next edit
- [Phase 15]: 15-03: VIZ-03 lays out with subplots_adjust because a colorbar spanning an axes LIST (the D-01 shared-scale statement) is not tight_layout-compatible
- [Phase 15]: 15-03: the D-07 guard was observed RED against a deliberate `import torch` — AST half raised, fresh-interpreter subprocess exited 1 — then reverted to a byte-identical file; a structural guard nobody has watched fail is a guard nobody has verified
- [Phase 15]: 15-03: shared (vmin, vmax) = (0.04211054267645148, 0.22023983403635128), 0.719 decades; EWC moved less in 34 of 36 cells (median 40.9% of naive) but MORE at layer 0/q_proj and layer 1/q_proj — Plan 15-05 must not write that EWC reduced movement everywhere
- [Phase 15]: 15-04: the Fisher/delta gate PASSES — rho = 0.801544, 95% CI [0.597984, 0.920291] excludes zero, permutation p = 0.000010 (add-one floor, 0/100000 shuffles), 0/10000 degenerate resamples; computed with the seed and constants committed at 0e1af98 before the artifact existed
- [Phase 15]: 15-04: ROADMAP SC2 is NOT narrowed — but it is supported at the level the gate tests, the SIGN, and no further; the magnitude stays descriptive at n = 36 and the pre-registered percentile-bootstrap small-n bias note travels WITH the CI into REPORT.md
- [Phase 15]: 15-04: CR-02 — phase13_ab_report.md now carries '## Verdict'/'## Gate Verdict'/'## Pre-Registration' twice (real headings + quoted in the addendum comment); Plan 15-08's D-17 test MUST anchor on the SECTION via scripts/_verdict.py::VERDICT_SECTION, never split('## Verdict')[-1]
- [Phase 15]: 15-04: the plan's own verify literal 'does not reopen or amend' is split across a line break by the pre-registered renderer — the VERIFY command was corrected, never phase15_stats.py, which is byte-unchanged since 0e1af98 (T-15-09 verified, not asserted)
- [Phase 15]: 15-05: docs/REPORT.md extended, never edited — 549 insertions / 0 deletions, first 421 lines byte-identical, dated M1 boundary marker inserted before the stale future-tense roadmap (D-13/R3)
- [Phase 15]: 15-05: limitation quotes keep stable labels L1..L9 in claim-bound render order (L1,L7,L4,L2,L6,L5,L3,L9,L8), verified under the pinned normalize_quote; grep -qF is unrunnable for the 5 multi-line quotes
- [Phase 15]: 15-06: README's three headline bullets are the terse form and the docs/REPORT.md link is ADDITIVE — the qualifier (proper-noun core / teacher-forced + noise floor / same-run baseline) is complete before the link, so no number's only caveat is a pointer
- [Phase 15]: 15-06: the front page states rho = 0.801544 with its CI rather than letting VIZ-03 imply the dodging claim visually — written as a RANK correlation, not an effect size, naming the 2 of 36 cells where EWC moved further
- [Phase 15]: 15-06: two stale v1.0 claims were corrected, not preserved — '~130 CPU-only tests' (actual 403) and 'make test (~70 s)' (actual 115 s, timing DELETED rather than re-asserted)
- [Phase 15]: 15-06: R1 discharged — README names artifacts/tokenizer.json (5,648 B) built from the 11,469-byte tests/fixtures/tiny_corpus.txt via scripts/train_tokenizer.py:31; both byte counts re-confirmed with wc -c before writing, so REPORT.md's L8 note about README is now true
- [Phase 15]: Phase 15 SC3 superseded by D-13: the v2.0 honest numbers ship in a new self-contained demo_v2.ipynb; demo.ipynb receives only a prepended independence cell, its eight original cells byte-identical (recorded dated in ROADMAP, not silently absorbed)
- [Phase 15]: Phase 15 SC2 not narrowed: the Fisher/delta correlation gate PASSED (rho 0.801544, CI [0.597984, 0.920291] excludes zero), so D-11's miss branch was not taken and the absence of a narrowing note is a recorded outcome
- [Phase 15]: 15-08: L8's self-citation is verified against docs/REPORT.md MINUS its Limitations section, not via git show — quoting a file into itself self-satisfies, and subprocess is forbidden in this module
- [Phase 15]: 15-08: DEF-15-01's recorded one-line fix is wrong — CI runs bare ruff with no .venv, so pointing Makefile:16 at .venv/bin/ruff would break CI; the correct fix is python -m ruff

### Pending Todos

None yet.

### Blockers/Concerns

None open. Both v2.0 blockers are resolved:

- ~~Phase 12 research flag: λ selection + full-FT LR/budget calibration.~~ **Resolved** — the calibration smoke ran fully pre-registered and returned an honest all-fail (λ\*=None, "EWC not demonstrable at this budget"); production used a separately-recorded discretionary λ=0.01.
- ~~DEBT-01/02 must land before the first v2.0 fine-tune step.~~ **Resolved** — DEBT-01 landed 2026-07-31 pre-work. DEBT-02 turned out to be two items: the PPL half was closed by design in the same pre-work (`ca14a89`), and the warm-sampling half — the genuine v1.0 carry-over — was closed 2026-08-12 (`3781a97`).

Carried into v3.0 as non-blocking notes (see `milestones/v2.0-MILESTONE-AUDIT.md`): W1 runtime consumers inject with `LoRAConfig()` defaults rather than the artifact's own; W3 one λ=0 frontier point is a hand-entered literal; `scripts/evaluate.py` is unseeded, so `results/samples.md` is not reproducible run to run.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260605-lgy | MPS device-layer support: RuntimeConfig MPS detection (fp32/AMP-off, bf16-Pascal guard intact) + hard rename preflight_p100 → preflight_device (CUDA-P100 → MPS → CPU) | 2026-06-05 | 398b74e | [260605-lgy-add-mps-support-to-the-device-layer-runt](./quick/260605-lgy-add-mps-support-to-the-device-layer-runt/) |
| 260801-r9y | Phase-13 closeout corrections: ROADMAP SC1 names the arms that actually ran (λ=0 vs pre-chosen λ=0.01, citing the A/B report); stop-fraction note derived from measured counts in script + markdown; plot_phase13 fails loudly on a missing/blank column and pins the frontier endpoint to step 1250 (both PNGs SHA-256-identical) | 2026-08-01 | d679440, 8812638, f0bae0b | [260801-r9y-SUMMARY.md](./quick/260801-r9y-SUMMARY.md) |
| 260802-h3g | CR-02 follow-through (14-SECURITY UF-4): the anchored verdict-SECTION read extracted to `scripts/_verdict.py` and wired into the two remaining naive `split("## Verdict")[-1]` guards — `teach_persona._refuse_clobber` and `phase14_factset_gate`, whose inline `main()` block was extracted so it is testable without a checkpoint. RED proven against the unmodified guards; the naive tail is kept in the test as a regression tripwire | 2026-08-02 | f16ce64, 2b8ed33, a39b753 | [260802-h3g-anchor-the-verdict-section-clobber-guard](./quick/260802-h3g-anchor-the-verdict-section-clobber-guard/) |

## Deferred Items

**At v2.0 close (2026-08-12): zero items deferred.** `gsd-sdk query audit-open` reported 3 open
artifacts and all 3 were resolved rather than acknowledged — `15-VERIFICATION.md` re-stamped
`human_needed` → `passed` after its two human items passed, and two quick-task SUMMARYs renamed to
the `SUMMARY.md` filename `audit-open.ts:84` actually reads. Final scan: 0 items.

Items acknowledged and deferred at milestone close on 2026-06-11 (v1.0), with current status:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| quick_task | 260605-lgy-add-mps-support-to-the-device-layer-runt | **CLOSED at v2.0 close** — the work was always complete (committed 398b74e); the audit read it as missing because the checker requires a file literally named `SUMMARY.md` in the task directory, not a slug-prefixed one. Renamed 2026-08-12 | v1.0 close |
| tech_debt | forbid_ids mask not threaded into scripts/evaluate.py warm sampling (CR-01 mode can recur on eval re-runs) | **CLOSED 2026-08-12 (`3781a97`)** — threaded into both the greedy and warm calls; headline 2.1066 re-run byte-identical (sha256 `4b9d129e…`), all 4 greedy samples byte-identical, `greedy(masked) == greedy(unmasked)` asserted directly | v1.0 close |
| tech_debt | loop.py tokens_per_step omits ×block_size; run.csv "tokens" column under-counts ×256 (telemetry only) | **CLOSED** — DEBT-01, landed 2026-07-31 as Phase 12 pre-work, before the first v2.0 training step | v1.0 close |
| tech_debt | TODO(calibration) markers on shipped-final constants in scripts/pretrain_tinystories.py | open — see v1.0-MILESTONE-AUDIT.md | v1.0 close |
| tech_debt | docs/REPORT.md under-discloses tokenizer training-corpus identity (11.5KB fixture → 547 live ids) | open — natural home: DOC-02 honesty pass (Phase 15) | v1.0 close |
| tech_debt | one-time `gh release view m1-demo-v1` asset check (tag verified, asset unverified from sandbox) | open — see v1.0-MILESTONE-AUDIT.md | v1.0 close |

## Session Continuity

Last session: 2026-08-12
Stopped at: v3.0 roadmap created — Phases 16-18 defined, 26/26 requirements mapped, Phase 19+ left deliberately unplanned behind the pre-registered erasure gate
Resume file: None

## Operator Next Steps

- Plan the first v3.0 phase with /gsd-plan-phase 16
- Phase 16 needs light research on the in-context capability ladder's rung design; Phase 18 needs `--research-phase` BEFORE its pre-registration commit (unamendable afterward)
