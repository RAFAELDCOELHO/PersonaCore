---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Adversarial Privacy Audit and Selective Memory Erasure
status: completed
stopped_at: Phase 18 complete — ship decision recorded, verified at 4f9e330
last_updated: "2026-08-17T17:41:50.609Z"
last_activity: 2026-08-17
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 38
  completed_plans: 38
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-12)

**Core value:** Personalization lives in the weights, not a prompt or a store — and the from-scratch implementation must be correct enough to prove it. v1.0 shipped the correct from-scratch base LM; v2.0 **demonstrated** the weight-based memory (LoRA + EWC) under pre-registered gates.
**Current focus:** Phase 18 — black-box-adversarial-extraction-audit

## Current Position

Phase: 18 — COMPLETE
Plan: 16 of 16
Status: Phase 18 complete
Last activity: 2026-08-17

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
| 16 | 11 | - | - |
| 17 | 11 | - | - |

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
| Phase 16 P01 | 20min | 3 tasks | 3 files |
| Phase 16 P02 | 25min | 2 tasks | 2 files |
| Phase 16 P03 | 16min | 2 tasks | 1 files |
| Phase 16 P04 | 12min | 3 tasks | 3 files |
| Phase 16 P05 | 38min | 2 tasks | 4 files |
| Phase 16 P06 | 30min | 3 tasks | 2 files |
| Phase 16 P08 | 35min | 3 tasks | 2 files |
| Phase 16 P09 | 55min | 3 tasks | 3 files |
| Phase 16 P10 | 95min | 3 tasks | 2 files |
| Phase 17 P01 | 34min | 3 tasks | 4 files |
| Phase 17 P02 | 17min | 2 tasks | 3 files |
| Phase 17 P03 | 19min | 2 tasks | 2 files |
| Phase 17 P04 | 18min | 3 tasks | 4 files |
| Phase 17 P05 | 41min | 2 tasks | 3 files |
| Phase 17 P06 | 28min | 4 tasks | 2 files |
| Phase 17 P08 | 32min | 3 tasks | 2 files |
| Phase 17 P07 | 60min | 2 tasks | 3 files |
| Phase 17 P09 | 70min | 3 tasks | 9 files |
| Phase 17 P11 | 25min | 2 tasks | 2 files |
| Phase 17 P10 | 40min | 3 tasks | 15 files |

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
- ~~W1 (`LoRAConfig()` defaults instead of `LoRAConfig(**artifact["lora_config"])`) must land before ANY Phase-17 adapter trains — shape audits catch `r` drift but never `alpha`.~~ **CLOSED 2026-08-14 (`0a26702`, `ec3e94a`)** — quick task 260814-d0j, landed before any Phase-17 planning. Fixed at the choke point, not only at the three call sites: `load_adapter_weights` now audits every `LoRALinear.scale` against `lora_config["alpha"]/["r"]`, so a Phase-17 consumer that forgets to read the config fails loudly at load time instead of applying the delta at the wrong magnitude. Mutation-proved (audit stripped → the same alpha=32-vs-16 artifact loads silently). Behavioural no-op: 0 files changed under `results/`.

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
- [Phase 16]: STAT-04 is now test-enforced: tests/test_package.py pins pyproject.toml by sha256 (read as bytes) — a new runtime dependency, a new extra or a widened specifier all turn a committed test red; if one is genuinely needed, PYPROJECT_SHA256 is updated in the SAME commit as a reviewed decision, never silently
- [Phase 16]: PREREG-02 is now test-enforced by commit ANCESTRY, not committer dates: tests/test_phase16_prereg.py — the pre-registered erasure rule (23a830c) must be a git ancestor of the first commit adding every results/phase1[678]_* artifact; CI runs fetch-depth: 0 so the query resolves. A phase writing results under a new prefix must add it to V3_ARTIFACT_GLOBS — assert checked catches an empty match set, not an incomplete one
- [Phase 16]: 16-02: the in-prompt guard's verdict is the UNION of its string and id-run detectors, not their intersection — The plan prescribed proving BOTH levels. Measurement falsified it on 54 of 216 core fairness prompts (2 of 8 facts): a leading-space BPE merge breaks the contiguous id run while the value is fully in view. UNION is the true De Morgan twin of assert_no_value_in_prompt's NOT(string) AND NOT(ids), and is strictly stronger than the string-only check it replaces.
- [Phase 16]: 16-02: results/phase14_recall_report.md deliberately NOT amended (D-19 / T-16-07) — The PERS-05 seed fix changes which streams are drawn by design, so the committed Phase 14 number does not reproduce bit-for-bit. Mitigation is disclosure, not prevention: the report stays byte-unchanged and Phase 16 re-runs the control post-fix and reports the delta separately (D-13).
- [Phase 16]: 16-03: the persona= AST guard scans scripts/*.py + src/**/*.py (69 files) with hard equality against a one-entry (file, function) PERSONA_ALLOWLIST — widening the scan never weakens the assertion
- [Phase 16]: 16-03: every draw_all call site must be covered by an in-prompt assertion, in place or via a NAMED DRAW_ALL_ASSERTED_BY indirection whose asserter must exist — a dangling entry fails
- [Phase 16]: PERS-01 ladder thresholds pre-registered: LADDER_CELL_PASS_K=10 at n=216, z priced at one-sided 1-0.05/6 — Anchored to the COMMITTED Phase 14 fairness-control floor (1 of 216 questions), never the post-fix re-run; the literal is pinned to its derivation by test so it cannot drift (T-16-13)
- [Phase 16]: licensed_headline() is total over all 128 rung subsets with a first-class all-fail branch and no investigate-the-instrument escape hatch (D-14) — All-fail is the outcome the evidence predicts (Phase 14 measured this model at the floor); a branch written after seeing the number is not a pre-registration
- [Phase 16]: phase14_factset_gate.probe_guessability() widens the guessability instrument additively (D-16), 0 deletions — Phase 16 and Phase 17 ISO-01 import one implementation instead of copying it; a duplicated rule is a rule that can drift
- [Phase 16]: SYNTHETIC_FACT_ORDER commits SLOTS, not fact ids — Every core fact id ends in its own value (cand_town_brindlemoor), so a literal tuple of ids would embed 8 locked values in the ladder driver and trip 16-04's substring clean-room scan. Slots carry the same ordering and arity with no value; the id-to-slot binding is asserted in the test instead.
- [Phase 16]: The guessability gate cleared all 43 ladder candidates and rejected none — The 19 REJECTED rows in results/phase16_ladder_material.md are surplus, not gate rejections. The pools had been pre-screened for absence from the 608 base completions already published in results/phase14_factset_report.md, disclosed in the committed comment before the run. Recorded so 'the material passed the gate' is not read as the gate having bitten.
- [Phase 16]: 16-06: the whole PERS-01 ladder pipeline is committed BEFORE it produces a number — cell runner, top rung, D-15 proxy check, report text and verdict branch — PERS-01 makes the ladder blocking and requires it recorded before any comparison is scored; a report whose text is written after the numbers is a report written to fit them. results/phase16_ladder_report.md does not exist — 16-07 owns the run.
- [Phase 16]: 16-06: D-15's two cells differ in FRAME as well as material, recorded as PROXY_FRAME_CAVEAT rather than repaired — build_far_prompt's locked signature carries no fact id, so its persona line is one fact-agnostic sentence while run_fairness_control uses each fact's own taught statement. Implemented AS LOCKED (16-05's handover concern, decided explicitly here); the caveat travels inside proxy_validity's returned dict so no renderer can emit the number without it, and it makes the verdicts asymmetric — proxy_consistent is the stronger reading, proxy_diverges cannot separate frame from material.
- [Phase 16]: 16-06: the ladder's clobber guard has NO --force flag, and the report's top-rung distance reads 'not measured' rather than being back-filled — A force flag that becomes routine destroys the hand-recorded verdict it protects (15-04 CR-02); if the report must be regenerated the honest path is deleting it in a reviewed commit. The taught statements end in a period, so ladder_distance would raise on every top-rung prompt at the END of an ~80-minute run — the report names what was and was not measured instead.
- [Phase 16]: Arm parity is one SHARED_ARM_CONFIG object asserted by identity, never four agreeing literals; forbid_ids is runtime-injected and recorded by sha256 content hash — undecodable_ids_mask needs a loaded tokenizer so it cannot be an import-time constant, and a torch tensor has no useful is-identity after .to(device)
- [Phase 16]: COSINE_CHANCE_FLOOR = 0.05 with D-25's numeric reconciliation recorded in the comment beside it; the superseded 0.125 is AST-pinned out of executable code — the pool decision chose the 20-value lexicon, so the qualifier's cited floor and the pool's actual floor disagree; recording the discrepancy beats silently using one number
- [Phase 16]: 16-09: the cluster bootstrap is TWO-STAGE by USER DECISION at the wave-8 checkpoint — facts resampled first (STATE.md:94, n=8), then that fact's questions (STAT-01/D-06). Stage-2-only yields a zero-width interval on a within-fact-homogeneous fixture, narrower than the sign test beside it
- [Phase 16]: 16-09: sign_test_exact returns 1.0 whenever positives <= SIGN_TEST_N/2 (D-29) — under a pure two-sided test an all-tied pair scores 0.0078125 and would have CLEARED Holm at 0.0083333; reproduced by deliberate-RED and restored byte-identical
- [Phase 16]: 16-09: no coverage/collision floor anywhere — the 6435 fact-multisets (C(15,8)) are NOT equiprobable, so a >= 6435*0.95 floor is unreachable by construction (~57% drawn at N=10000)
- [Phase 16]: D-25's verbatim qualifier is READ from 16-CONTEXT.md at report time, not stored as a module constant — a constant would be a second 0.125 and a committed 16-08 test pins that count at 1
- [Phase 16]: D-28 implemented as locked (span_2 permits the monotone claim); the ladder's ceiling renders in the SAME paragraph as the permission — a permission printed alone is the sentence a reader quotes
- [Phase 17]: 17-01: the Phase 17 pre-registration is TWO files — gate constants in scripts/phase17_personas.py (pinned by a git-ancestry test), the 24 minted values in scripts/phase17_persona_facts.py (deliberately NOT pinned); the split is what lets ROADMAP SC2's ADAPT branch replace values after results/phase17_personas_report.md exists without turning the guard permanently red
- [Phase 17]: 17-01: the STAT-05 ordering guard is DERIVED from history (every commit touching the driver must be an ancestor of every results/phase17_* first-add), not pinned to a SHA — self-identifying, needs no identity test, and it catches the post-hoc edit a SHA pin permits; watched RED on a prereg edit and GREEN on a material edit
- [Phase 17]: 17-01: D-18 gate_cleared requires all six Holm rejections and returns False on a truncated family; D-19 worst_pair implements the tie-break AS the sort key (-mean, index_i, index_j) so the all-zero three-way tie — which is the phase's SUCCESS case — resolves to (persona_a, persona_b)
- [Phase 17]: 17-01: the ISO-05/STAT-06 identifier ban stays CALL-SITE-scoped exactly as tests/test_phase16_stats.py:806-823 is — widening it to module-level assignment targets is self-invalidating, because REPLICATION_SEEDS is such a target in the very file the glob scans and 17-01 Task 1 mandates it
- [Phase 17]: 17-01: _GATE_MODULES is a GLOB over scripts/phase17_*.py, not a hand-listed tuple (D-21) — 17-03/17-04/17-05 drivers enter every static scan automatically, closing the F-08 blindness Phase 16's file-scoped tuple left open
- [Phase 17]: 17-01: CORE_SLOTS is THE canonical slot list, verified against results/phase16_recall_sample.json by deriving fact_id->slot through phase14_factset — exact first-appearance order, 13 questions x 8 slots = 104; 17-03's material and 17-04's regrouping are each checked against IT, never against each other
- [Phase 17]: 17-01: the plan's module-level-call acceptance command is vacuous (the sys.path bootstrap is nested in an if, so a tree.body scan finds 0 calls and all([]) is True) — replaced by a committed module-SCOPE walk, test_nothing_executes_at_import
- [Phase 17]: 17-02: seed= and prefix= widen the committed teach_persona recipe additively (D-16 import-never-copy) — the prefix is threaded to BOTH internal arm_outputs call sites because train_arm's build_arm_bins call REBINDS paths, so a prefix applied only at the refuse_if_exists site would guard phase17_ paths while exporting the adapter to phase14_
- [Phase 17]: 17-02: bin/mask deliberately NOT prefixed (they carry no phase label today, so prefixing MOVES an existing path) and the real-arm shippable adapter exception stays unconditional on prefix — Phase 17 never passes real, so a prefix-aware exception would be dead code weakening a pinned cross-plan contract
- [Phase 17]: 17-02: the ISO-06 AST guard splits inject_lora call sites into PRODUCER (bare LoRAConfig(), D-20's r=8/alpha=16 anchor — correct as-is) and CONSUMER (LoRAConfig(**artifact['lora_config'])), resolving a Name argument through module-level assignments because both producers pass the LORA_CFG constant; hard equality on all three buckets, watched RED
- [Phase 17]: 17-03: the 24 minted values live in scripts/phase17_persona_facts.py and FORBIDDEN_VALUES is DERIVED by walking six committed Phase 14 containers plus BASE_PRIOR_SEEDS — D-06 zero-reuse holds by construction, and the pinned pre-registration file stays byte-untouched so SC2's ADAPT branch survives
- [Phase 17]: 17-03: the four mechanical filters structurally CANNOT see D-05 — filter_substring_disjoint passes tarrowgate/marrowgate happily (edit distance 1, neither contains the other), so a measured neighbour screen was added as a committed test: names >= 3, 4-digit numerics >= 2 (the achievable bar at fixed length 4 over a 10-symbol alphabet)
- [Phase 17]: 17-03: the four filters rejected 0 of the 24 committed values; across 34 measured candidates filter_token_budget's rule rejected 2 (vurthwaite 10 ids, thornebank 9) and the D-05 screen rejected 2 (tarrowgate, and 1971 at distance 1 from CALIBRATION_POOL's 1974) — a filter that bit nothing is recorded as such
- [Phase 17]: 17-03: phase17_personas is imported LAZILY by the material module because it MEASURABLY pulls torch into sys.modules (via phase16_persistence -> phase14_recall) while phase14_factset does not — so the Fact literals import at module scope and the four filters do not
- [Phase 17]: 17-03: ISO-01 deliberately NOT marked complete — 17-05 and 17-07 also claim it and both the guessability half and SC2's blocking human verdict are theirs; the 17-01 over-claim pattern avoided rather than repeated
- [Phase 17]: 17-04: generation and scoring are two separate passes, so cell-blindness is STRUCTURAL — score_completion takes (completion, slot_values) and literally cannot learn which sweep produced a string; pinned at signature, public name and body AST, and watched RED with an added i= parameter
- [Phase 17]: 17-04: classify's own-is-None branch is what makes the base row a COMPUTED row rather than a leak against itself — deleting it fails the unit test AND trips assemble_matrix's own runtime _prove, so the B4 regression is caught at two independent layers
- [Phase 17]: 17-04: the four category counts are a ROW property reported on each of that row's three cells (classify takes no j by design, D-12) — the per-column number is n_answerable; cell-scoping was rejected because branch 1 fires before branch 3, making a cell-scoped leak a conditional quantity nobody declared
- [Phase 17]: 17-04: ROADMAP SC1's no-op-swap shape CONFIRMED by measurement — column collapse, diagonal (1.0, 0.0, 0.0), base row unaffected, and only 2 of 6 Holm comparisons reject so the pre-registered gate does NOT clear; the MEDIUM-confidence paragraph is left in place, marked superseded
- [Phase 17]: 17-05: the ISO-01 gate's `## Verdict` section holds the verdict and NOTHING else — the first draft put the STOP/PENDING instructions inside it, which would have kept the literal PENDING inside the recorded verdict forever and left assert_report_not_clobbered permanently disarmed after a human wrote GO; they moved to `## Recording The Verdict` above it, and the round-trip is asserted both ways (own output re-drives, a recorded GO raises)
- [Phase 17]: 17-05: probe_guessability is called ONCE PER SLOT on that slot's uncached questions and all 24 verdicts derive from the per-question cache through fs.exact_match_clean — F-07's 416-completion cache and the instrument's (value, questions) signature pull opposite ways, and deriving all 24 identically keeps no value judged by a different code path than its slot-mates; the anchor's returned clean is _proved equal to the cache-derived answer, which catches a flattening that dropped a draw
- [Phase 17]: 17-05: the gate driver has NO literal import torch — it needs no torch symbol (load_slim loads, collect is already @torch.no_grad(), preflight_device returns the version, the mask moves by method call) and an unused import fails the ruff criterion; measured instead — torch enters sys.modules transitively through the sibling imports, and the MPS-fallback env set at line 56 precedes the first torch-importing sibling at line 66
- [Phase 17]: 17-05: five acceptance greps forbid the very identifiers the plan's action text asks the docstring to name (load_adapted_model, inject_lora, load_adapter_weights, load_adapter, weights_only=False) — the mechanical criterion won and build_unadapted_base's docstring carries the whole argument with phase14_recall.py:496 and :516/:530/:557/:565 as pointers instead of identifiers; all five greps return 0
- [Phase 17]: 17-05: teach_persona._require_go_verdict now names report_path in EVERY abort — it stopped being a Phase 14 gate when ISO-01 started calling it with the Phase 17 report, and 'no ## Verdict section in the fact-set report' would send a Phase 17 operator to results/phase14_factset_report.md, which already carries a recorded GO so the wrong fix would look like it worked
- [Phase 17]: 17-05: ISO-01 still NOT marked complete (third plan running) — the guessability measurement needs convbase_slim.pt on MPS and cannot enter a CPU-only suite, and SC2's GO/ADAPT verdict is a blocking human decision; 17-07 runs the measurement, records the verdict and marks the requirement
- [Phase 17]: 17-08: the two achievable p values the report publishes as a design property are RETURNED BY compare_cells, never recomputed by the writer — a second sign_test_exact call site is a second hypothesis family, caught by the new D-21 scan on its first run
- [Phase 17]: 17-08: report_proportion's raw-count denominator is the RECORDED draws-per-question times each cell's own question count, never SHARED_ARM_CONFIG.n_draws — the latter renders '9 draws' beside '0/104 questions'
- [Phase 17]: 17-08: the four category counts render once per ROW, never once per cell (D-12) — the per-column number is n_answerable, and mislabelling it is a live repudiation surface
- [Phase 17]: 17-07: the ISO-01 gate ran on the un-adapted base (convbase_slim, git 04e724c6/step 4000/val 1.5235939979553224, no adapter injected) and returned 24/24 clean at 0/52 containments over 416 completions — RESEARCH F-13 now holds: an off-diagonal hit cannot be the base's own prior, it must come from adapter i; the claim is checkpoint-specific to 04e724c6 and is NOT a standing invariant
- [Phase 17]: 17-07: ROADMAP SC2's GO verdict is recorded by hand in 5183e0e — the executor stopped at the checkpoint, recorded nothing, and its git commit of the verdict was DENIED by the permission system three times; it did not route around the denial. That closed path is TH-17-23's actual mitigation, NOT the git author field, which is Rafael on all three commits including the two the agent made and therefore distinguishes nothing
- [Phase 17]: 17-07: assert_report_not_clobbered flipped permissive -> ARMED the moment GO was recorded — re-driving scripts/phase17_persona_gate.py now requires --force, which would destroy the hand-written verdict; per 17-05 handover 4 the honest recovery is a reviewed deletion commit, never --force. Measured both directions at HEAD
- [Phase 17]: 17-07: STAT-05 stopped being vacuous — the report is the first results/phase17_* artifact (6e7bad0), checked = 2, and the Phase 17 guard gained the empty-match assertion its Phase 16 sibling already carried because the product assertion alone is satisfied by 0 == n * 0; watched RED. scripts/phase17_personas.py is now permanently uneditable at d549e0b
- [Phase 17]: 17-07: ISO-01 marked complete HERE and only here — claimant set re-derived across every plan in every phase is exactly 17-03/17-05/17-07, both predecessors explicitly deferred, and both D-06 conditions (checkpoint-specific guessability pass 6e7bad0, SC2 blocking human verdict 5183e0e) have now happened
- [Phase 17]: 17-09: the gate CLEARED — all six Holm comparisons rejected at p = 0.0078125 each (8/8 slot unanimity) against step alphas 0.0083333..0.0500000, gate_cleared returns True, re-derived independently by parsing the report's own six published rows back through the imported function; diagonals 104/104, 103/104, 103/104 questions and ALL SIX off-diagonals 0/104
- [Phase 17]: 17-09: the adapter-off base row is 0/104 questions and 0/936 draws on each of the three personas' values — the ISO-01 pre-flight's zero-containment result reproduced by a second instrument on a different code path, so every off-diagonal zero has an EMPIRICAL leak-vs-prior separator rather than an inherited one
- [Phase 17]: 17-09: the D-13 anchor is a PARTIAL miss and is published as such — 'the country' reproduced for hometown (7/108 base draws), 'rose' did NOT for pet_name (0/103); investigated BEFORE the matrix was read and traced to BASE_PRIOR_SEEDS' own provenance (greedy decode from a bare system prompt, phase14_factset.py:295-296) rather than to the sweep, corroborated by the ISO-01 pre-flight producing 'rose' zero times across 416 completions on the pure un-adapted base
- [Phase 17]: 17-09: F-13 is labeled CHECKPOINT-SPECIFIC in the isolation report itself (04e724c6 / step 4000 / val_loss 1.5235939979553224) with an explicit RE-RUN requirement for any future checkpoint — the committed report writer makes no F-13 claim at all, so the label went into a dated hand-appended Scope Addendum that alters no rate, no p, no alpha and no verdict
- [Phase 17]: 17-09: 17-07's handover prediction that the base's 'i am a college student' attractor and '<|assistant|>' leakage would appear in the adapter completions is FALSIFIED by measurement — 47 and 56 of 936 draws in the base column, 0 of 936 in each of the three adapter columns; both are published Phase 13 properties (79 naive / 70 EWC) and are recorded in the report as such, never as Phase 17 findings
- [Phase 17]: 17-11: the D-13 remediation pointer was corrected at THREE generator sites, not the two named — BASE_PRIOR_SEED_ANCHOR_NOTE is the only one that renders into the report, so fixing the other two alone would leave the published defect regenerating on the next --report run
- [Phase 17]: 17-11: append_addendum is textual and surgical, never a re-render — render_report rewrites the WHOLE file and would destroy the recorded verdict, 17-09's Scope Addendum and the 9fcfc50 D-13 addendum together; do NOT run --report again to pick up the corrected pointer
- [Phase 17]: 17-11: git_sha is recorded per replicate cell and deliberately NOT proved single-valued — two of the six records are 17-09's, produced at an earlier commit by construction, so a one-SHA proof would refuse every honest run
- [Phase 17]: 17-11: resolve_seed is not reused for replicate path resolution (it resolves an adapter through teach_persona.arm_outputs, which imports torch, and --replicate is CPU-only); sweep_record_path — the thing that must agree with the sweep writer — IS shared
- [Phase 17]: 17-11: ISO-05 stays Pending — this plan ships the rendering path and produces no number; 17-10 runs it. Fifth application of 17-01's recorded over-claim-avoidance pattern
- [Phase 17]: 17-10: ISO-05 is MEASURED — the pre-registered worst_pair, CALLED by the committed --replicate mode rather than re-derived, read all six ordered off-diagonal rates at 0.000000 (0/104 questions each) out of the sweep RECORDS and returned persona_a/persona_b with tie_break_decided=true. That is the THREE-WAY TIE the success case was always going to produce: the pair is a tie-break outcome and NOT a finding about those two personas
- [Phase 17]: 17-10: the k=3 replication is 0/104 questions (0/936 draws) in every one of the six cells (2 personas x 3 seeds), Wilson upper bound 0.025355 and rule-of-three 0.028846 on each; the pair's mean off-diagonal rate is min 0.000000 / max 0.000000 / median 0.000000 across the three seed indices. DESCRIPTIVE ONLY (D-16) — no p value, no alpha, no Holm row, no sign test at any depth. gate_cleared is closed at the six pre-registered comparisons and structurally cannot admit a replication row, so this number neither clears, weakens nor re-prices the gate
- [Phase 17]: 17-10: the isolation report was EXTENDED, never edited — 62 insertions / 1 deletion against 9fcfc50, and that one deletion is the placeholder line becoming a pointer at the appended section. The 15,306 bytes above it are byte-identical, the recorded verdict reads back unchanged at 1,402 chars, and the dated 9fcfc50 D-13 supersession addendum is still present exactly once. test_report_addendum_is_additive pins that on the REAL artifact (17-11's synthetic twin proves only the writer); both probes watched failing
- [Phase 17]: 17-10: the four replicate adapters inherit 17-09's replay_ratio=0.0 collateral collapse and are equally NOT shippable demo substrate. Six lora_B digests are pairwise distinct with 0 of 36 identical tensors across all 15 pairs — that proves the seed reached the init draw, and proves nothing about conversational retention
- [Phase 17]: 17-10: STAT-05 checked = 21 (1 prereg commit d549e0b x 21 tracked results/phase17_* paths), 0 untracked — was 11 at 17-09/17-11; scripts/phase17_personas.py is still at d549e0b and still uneditable

### Pending Todos

None yet.

### Blockers/Concerns

None open. Both v2.0 blockers are resolved:

- ~~Phase 12 research flag: λ selection + full-FT LR/budget calibration.~~ **Resolved** — the calibration smoke ran fully pre-registered and returned an honest all-fail (λ\*=None, "EWC not demonstrable at this budget"); production used a separately-recorded discretionary λ=0.01.
- ~~DEBT-01/02 must land before the first v2.0 fine-tune step.~~ **Resolved** — DEBT-01 landed 2026-07-31 pre-work. DEBT-02 turned out to be two items: the PPL half was closed by design in the same pre-work (`ca14a89`), and the warm-sampling half — the genuine v1.0 carry-over — was closed 2026-08-12 (`3781a97`).

Carried into v3.0 as non-blocking notes (see `milestones/v2.0-MILESTONE-AUDIT.md`): ~~W1 runtime consumers inject with `LoRAConfig()` defaults rather than the artifact's own~~ **CLOSED 2026-08-14 (`0a26702`, `ec3e94a`)** — it was the one carry-over the milestone audit marked as blocking Phase 17, so it landed first; W3 one λ=0 frontier point is a hand-entered literal; `scripts/evaluate.py` is unseeded, so `results/samples.md` is not reproducible run to run.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260605-lgy | MPS device-layer support: RuntimeConfig MPS detection (fp32/AMP-off, bf16-Pascal guard intact) + hard rename preflight_p100 → preflight_device (CUDA-P100 → MPS → CPU) | 2026-06-05 | 398b74e | [260605-lgy-add-mps-support-to-the-device-layer-runt](./quick/260605-lgy-add-mps-support-to-the-device-layer-runt/) |
| 260801-r9y | Phase-13 closeout corrections: ROADMAP SC1 names the arms that actually ran (λ=0 vs pre-chosen λ=0.01, citing the A/B report); stop-fraction note derived from measured counts in script + markdown; plot_phase13 fails loudly on a missing/blank column and pins the frontier endpoint to step 1250 (both PNGs SHA-256-identical) | 2026-08-01 | d679440, 8812638, f0bae0b | [260801-r9y-SUMMARY.md](./quick/260801-r9y-SUMMARY.md) |
| 260802-h3g | CR-02 follow-through (14-SECURITY UF-4): the anchored verdict-SECTION read extracted to `scripts/_verdict.py` and wired into the two remaining naive `split("## Verdict")[-1]` guards — `teach_persona._refuse_clobber` and `phase14_factset_gate`, whose inline `main()` block was extracted so it is testable without a checkpoint. RED proven against the unmodified guards; the naive tail is kept in the test as a regression tripwire | 2026-08-02 | f16ce64, 2b8ed33, a39b753 | [260802-h3g-anchor-the-verdict-section-clobber-guard](./quick/260802-h3g-anchor-the-verdict-section-clobber-guard/) |
| 260814-d0j | W1 closed before any Phase-17 adapter work: `load_adapter_weights` gains a third audit — every `LoRALinear.scale` checked against the artifact's own `lora_config["alpha"]/["r"]` — because `alpha` is shape-invisible and the key/shape audits could never see it. The three runtime consumers (`phase14_recall.load_adapted_model`, `run_bit_identity_control`, `personalize_demo.build_demo`) now inject at the artifact's config instead of `LoRAConfig()` defaults; the two producers are untouched. Mutation-proved; 579 passed / 1 skipped; 0 files changed under `results/` | 2026-08-14 | 0a26702, ec3e94a | [260814-d0j-close-w1-lora-consumers-inject-config-de](./quick/260814-d0j-close-w1-lora-consumers-inject-config-de/) |

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

Last session: 2026-08-17T17:41:50.602Z
Stopped at: Phase 18 complete — ship decision recorded, verified at 4f9e330
Resume file: .planning/phases/18-black-box-adversarial-extraction-audit/18-VERIFICATION.md

## Operator Next Steps

- Plan the first v3.0 phase with /gsd-plan-phase 16
- Phase 16 needs light research on the in-context capability ladder's rung design; Phase 18 needs `--research-phase` BEFORE its pre-registration commit (unamendable afterward)
