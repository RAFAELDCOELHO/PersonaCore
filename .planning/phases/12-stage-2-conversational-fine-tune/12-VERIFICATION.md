---
phase: 12-stage-2-conversational-fine-tune
verified: 2026-08-01T14:30:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 12: Stage-2 Conversational Fine-Tune Verification Report

**Phase Goal:** `best.pt` becomes a dialogue-capable conversational base via full fine-tune with calibrated EWC — telemetry tech debt fixed before the first training step so every retention-curve point is trustworthy.
**Verified:** 2026-08-01T14:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Before first v2.0 training step, run.csv tokens counts true tokens (×block_size) and the dead-id forbid_ids retention policy is frozen | ✓ VERIFIED | `loop.py:394` — `tokens_per_step = batch_size × grad_accum × block_size`, cumulative from absolute step; `retention_perplexity()` (perplexity.py:167) builds `forbid_ids` internally via `undecodable_ids_mask` — the ONLY sanctioned retention path (DEBT-02 frozen-policy docstring). Both landed in commit `ca14a89` ("close DEBT-01/02 pre-work before first v2.0 training step", 2026-07-31), which predates every Phase-12 run (first run commit `10ba73e` 08-01 01:53). Pinned by `tests/test_run_csv_tokens.py` + `tests/test_retention_ppl.py`, green in the full suite. |
| 2 | λ log-scale sweep (D-07 short-run pattern) completes, λ* picked off the stability–plasticity tradeoff, sweep logs retained for the frontier plot | ✓ VERIFIED (with honest caveat — see below) | Decade grid λ ∈ {0.01, 0.1, 1, 10, 100} completed at the recalibrated 1250-step budget; all 5 `results/ft_lam_*.csv` tracked (plus cal/noise/masking/LR CSVs — 13 arm logs total), each with dialog_ppl + retention_ppl + ewc_penalty columns from a step-0 row. The tradeoff is measured (retention gain +2.17 → +3.85, dialogue cost +0.28 → +11.77 across the grid). Formal pre-registered λ* = None (see caveat). Production λ = 0.01 picked off the measured tradeoff by a recorded, user-approved post-verdict decision. |
| 3 | Full fine-tune of best.pt through the untouched v1.0 train() reaches dialogue-format adherence — conversational val PPL reported and curated transcripts committed | ✓ VERIFIED | `train()` extended only via additive default-None kwargs proven bit-identical to v1.0 (golden-trajectory replay ran on-machine; identity tests in `test_masked_train_seam.py`/`test_extra_eval_fns.py` — the pre-approved "untouched" reading). Production run: 4000 steps, unmasked, LR 9e-5, λ=0.01; final masked dialogue val PPL **4.5733** over 270,203 assistant tokens. `results/transcripts.md` committed: 15 held-out episodes, greedy + warm completions via the `encode_dialogue` serialize path, **30/30 stop-id termination**, leakage count 1 honestly reported (one warm completion re-opened an `<\|assistant\|>` turn). |
| 4 | TinyStories retention PPL vs the 2.1066 anchor logged at every eval interval from step 0 in per-run/per-arm CSVs | ✓ VERIFIED | `results/finetune_prod.csv`: 17 rows, step-0 row with retention_ppl 2.10755 (the measured sub-bin anchor — commit-verified in `results/retention_anchors.json` with the 2.1066 unmasked headline recorded as historical reference, Pitfall 1), retention_ppl finite in every row through step 4000 (final 3.8911). All 5 λ-arm CSVs carry per-interval retention_ppl from step 0. Behavioral spot-check re-parsed the CSV and asserted step-0 + finiteness. (LR-arm CSVs carry before/after retention per pre-registered §7 — expensive fn deliberately not attached at that cadence; the forgetting curves themselves fall out of the λ-arm + production training logs, exactly as the criterion requires.) |
| 5 | A conversational-base checkpoint exists as the substrate for both demos | ✓ VERIFIED | `checkpoints/convbase_best.pt` loaded and asserted: contains all four EWC extras (fisher / theta_star / ewc_lambda=0.01 / fisher_meta), step 4000 — self-contained resume. `checkpoints/convbase_slim.pt` loads under `torch.load(weights_only=True)` (LOCKED slim contract, executed in this verification). `convbase_latest.pt` also present. Phase-13 provenance block (seed 1337, config, λ, anchor fingerprint, driver SHA) committed in `results/finetune_prod_run.log` (87198ec). |

**Score:** 5/5 truths verified

### Criterion 2 — the negative demonstrability verdict, reported honestly

The pre-registered §8 verdict is **NEGATIVE**: within-margin candidates = [], **λ* = None,
demonstrable = False — "EWC not demonstrable at this budget"** — recorded verbatim in
`results/finetune_smoke_report.md` and never massaged. No λ arm stayed within the blind
K×Δ_dialog = 0.0034 dialogue margin of λ=0, although every arm beat the collapse baseline on
retention (λ=100 drift +0.0007 ≈ zero forgetting). The production **λ = 0.01** is a
**separately-labeled, post-verdict discretionary decision** (report section "Production Config
Decision — post-verdict, discretionary"), approved by the user at the D-07 checkpoint, with the
§8 gate NOT amended. The criterion's substance — sweep completes, a λ picked off the measured
stability–plasticity tradeoff, sweep logs retained for the Phase-13 frontier plot — is met.
The formal λ*=None finding is an honestly-recorded negative result, not a gap: the pre-registered
process worked exactly as designed (gate fired → halt → recorded override/decision → verdict
untouched). Phase 13 runs its own naive/EWC arms from best.pt, so the discretionary choice does
not contaminate the central causal result.

Also verified: the Stage-2 §7(a) all-arms retention-gate halt was handled per D-07 — override
recorded in `scripts/finetune_smoke_stage3_override.py` committed `7b27a5b` (08:09) BEFORE any
λ-arm CSV (`814e58e` 08:28); the wrapper re-evaluates the gate verbatim and refuses to run if
any arm passes.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/personacore/training/loop.py` | train_mask_bin / val_mask_bin / extra_eval_fns seams | ✓ VERIFIED | All three kwargs default None (lines 181/182/199); memmap batch_fn routes via `get_batch_memmap_masked` (line 331); per-run fieldnames `CSV_FIELDNAMES + sorted(extra_eval_fns)` (line 382); extras block + `model.train()` restore |
| `src/personacore/evaluation/perplexity.py` | `masked_perplexity()` gate metric | ✓ VERIFIED | Line 83, `ignore_index=-100`, forbid_ids renormalization; hand-fixture K=7 oracle in `test_masked_perplexity.py` (5 tests) |
| `src/personacore/generation/core.py` | additive `stop_ids` kwarg | ✓ VERIFIED | Line 38; `stops = stop_ids if stop_ids is not None else {eid}` (line 62); 4 pinning tests |
| `scripts/build_retention_bin.py` | run-once sub-bin builder + anchors | ✓ VERIFIED | Exists; refuse-to-rerun verified per 12-03; `data/retention_val.bin` on disk (gitignored per repo policy, seed-1337 reproducible) |
| `results/retention_anchors.json` | committed step-0 anchors | ✓ VERIFIED | subbin 2.10755 / fullval masked 2.10655 < 2.1066 headline (renormalization proof held); git_sha provenance |
| `scripts/finetune_smoke.py` | pre-registered smoke driver | ✓ VERIFIED | PRE-REGISTRATION constants block; committed `10ba73e` before any smoke CSV (git-order proof confirmed) |
| `results/finetune_smoke_report.md` | D-06 committed evidence | ✓ VERIFIED | Every stage section with numeric tables, per-gate counterfactual k, override section, discretionary section, GO verdict recorded 2026-08-01 |
| `results/ft_*.csv` (13 arms) | sweep logs for Phase-13 frontier | ✓ VERIFIED | All 13 tracked; λ arms carry dialog_ppl + retention_ppl + ewc_penalty from step 0; final steps match budgets (1250 / 5000 cal) |
| `scripts/finetune_dialog.py` | GO-gated production driver | ✓ VERIFIED | `_require_go_verdict` gate; `checkpoint_extra` with 4 EWC keys; `export_slim`; no `resume_from` |
| `results/finetune_prod.csv` | step-0 retention/dialog curve | ✓ VERIFIED | 17 rows step 0→4000, all extras columns finite (re-asserted in this verification) |
| `checkpoints/convbase_{best,latest,slim}.pt` | conversational-base trio | ✓ VERIFIED | best carries 4 EWC extras (loaded + asserted); slim loads weights_only=True (executed) |
| `scripts/make_transcripts.py` + `results/transcripts.md` | TUNE-01 adherence evidence | ✓ VERIFIED | serialize-path prompts (`encode_dialogue`), `stop_ids={8184, 8185}`, 15 episodes × 2 decodes, 3 measured proxies |

### Key Link Verification

| From | To | Via | Status |
| --- | --- | --- | --- |
| loop.py | data.py | `get_batch_memmap_masked` when train_mask_bin set | ✓ WIRED (loop.py:45 import, :331 call) |
| loop.py | logging.py | `CSV_FIELDNAMES + sorted(extra_eval_fns)` at CSVLogger construction | ✓ WIRED (loop.py:382) |
| finetune_smoke.py | loop.py / perplexity.py / ewc.py | seams + gate metric + EWCPenalty | ✓ WIRED (13 arm CSVs with the extra columns are the runtime proof) |
| finetune_dialog.py | checkpoint.py | `export_slim` → weights_only=True artifact | ✓ WIRED (slim load executed successfully) |
| make_transcripts.py | dialogue/serialize.py | `encode_dialogue` prompt path | ✓ WIRED (grep + transcripts.md output) |
| smoke report | retention_anchors.json | step-0 anchors embedded | ✓ WIRED (anchor values match to full precision) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Real Data | Status |
| --- | --- | --- | --- | --- |
| finetune_prod.csv retention_ppl column | extra_eval_fns["retention_ppl"] | `retention_perplexity` on frozen sub-bin | Yes — step-0 value equals the independently committed anchor 2.107553076833866 exactly; drifts to 3.8911 | ✓ FLOWING |
| ft_lam_*.csv | per-arm training runs | train() with EWCPenalty per arm | Yes — monotone λ→retention/dialogue tradeoff across arms | ✓ FLOWING |
| convbase_best.pt | checkpoint_extra | training-run state | Yes — ewc_lambda 0.01, step 4000 read back from the blob | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| convbase_best carries 4 EWC extras | torch.load + assert | ewc_lambda 0.01, step 4000 | ✓ PASS |
| slim loads under weights_only=True | torch.load(weights_only=True) | loads clean | ✓ PASS |
| prod CSV step-0 + finiteness | csv parse + math.isfinite | 17 rows, all finite | ✓ PASS |
| Full test suite | `.venv/bin/pytest tests/ -q` | **274 passed, 1 skipped** (matches regression gate) | ✓ PASS |
| All 26 claimed commits resolve | `git cat-file -e` | all found | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist or are declared — SKIPPED (not applicable).

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
| --- | --- | --- | --- |
| DEBT-01 | 12-01 | ✓ SATISFIED | ×block_size tokens fix (loop.py:394), pinned by test_run_csv_tokens.py, landed ca14a89 before any v2.0 run |
| DEBT-02 | 12-01 | ✓ SATISFIED | forbid_ids frozen inside retention_perplexity (perplexity.py:167), pinned by test_retention_ppl.py, ca14a89 |
| EWC-03 | 12-04, 12-05 | ✓ SATISFIED | 5-arm decade sweep complete, logs retained, λ=0.01 in production penalty + embedded in convbase_best.pt (formal λ*=None recorded honestly) |
| TUNE-01 | 12-01, 12-02, 12-04, 12-05 | ✓ SATISFIED | Conversational base at masked val PPL 4.5733; 15 committed transcripts with measured proxies; additive-seam "untouched train()" reading proven bit-identical |
| TUNE-02 | 12-01, 12-03, 12-04, 12-05 | ✓ SATISFIED | Step-0 anchors measured + committed before training; retention_ppl per-interval from step 0 in production + λ-arm CSVs |

No orphaned requirements — REQUIREMENTS.md maps exactly these five IDs to Phase 12; all appear in plan frontmatter and are marked Complete.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
| --- | --- | --- | --- |
| (none) | No TBD/FIXME/XXX in any phase-modified file | — | — |

Code-review (12-REVIEW.md) findings: 0 critical, 4 warnings (WR-01 silent val_mask_bin
fallback on non-memmap val, WR-02 no refuse-to-rerun on the production driver, WR-03
skip-if-done config-drift blindspot, WR-04 copy-pasted persona cap). All four are latent traps
for FUTURE callers — the review itself confirms "the current drivers happen to always pass
val_bin, so no shipped evidence is wrong." Advisory; none blocks the phase goal. Recommend
addressing WR-01/WR-04 before the Phase-13 λ=0 twin run.

### Human Verification Required

None. The one human decision point this phase required — the D-07 blocking checkpoint on the
smoke report — was completed in-phase: GO verdict recorded 2026-08-01 with the discretionary
λ=0.01 decision explicitly user-approved and the §8 negative verdict left untouched. No plan
carried deferred `<human-check>` blocks.

### Gaps Summary

No gaps. All five success criteria are observably true in the codebase: telemetry debt closed
and pinned before the first training step, the λ sweep completed under pre-registered rules
with logs retained, the production fine-tune produced a dialogue-capable conversational base
(PPL + transcripts committed), the forgetting curve lives in the training logs from step 0, and
the convbase checkpoint trio exists with a proven artifact contract. The §8 "EWC not
demonstrable at this budget" verdict is an honestly-recorded negative scientific finding — the
phase's process integrity (pre-registration by git order, halt discipline, recorded override,
separate discretionary decision) is exactly what makes that finding trustworthy.

---

_Verified: 2026-08-01T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
