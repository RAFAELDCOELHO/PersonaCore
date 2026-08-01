---
phase: 12-stage-2-conversational-fine-tune
plan: 05
subsystem: training, evaluation, continual, generation
tags: [production-finetune, ewc, forgetting-curve, transcripts, convbase, mps]

# Dependency graph
requires:
  - phase: 12-stage-2-conversational-fine-tune
    provides: "12-04 D-07 GO verdict + approved production config (unmasked, LR 9e-5, λ=0.01, 4000 steps); 12-01 train() seams; 12-02 masked_perplexity + stop_ids; 12-03 retention sub-bin + step-0 anchors"
  - phase: 10-ewc
    provides: "EWCPenalty + load_fisher fingerprint check + fisher_tinystories.pt cache"
provides:
  - "checkpoints/convbase_{latest,best}.pt — conversational base with fisher/theta_star/ewc_lambda/fisher_meta embedded (self-contained resume; Phase 13 EWC arm, Phase 14 LoRA substrate)"
  - "checkpoints/convbase_slim.pt — weights_only=True shippable artifact (LOCKED contract, proven)"
  - "results/finetune_prod.csv — TUNE-02 retention/dialog forgetting curve from a measured step-0 row"
  - "results/transcripts.md — TUNE-01 adherence evidence with measured proxies"
  - "scripts/finetune_dialog.py — GO-verdict-gated production driver"
  - "scripts/make_transcripts.py — serialize-path transcript generator"
  - "Phase-13 provenance block (seed/config/λ*/git_sha) for the identical-seed λ=0 twin (DEMO-04)"
affects: [13-forgetting-curves, 14-personalization-demo, 15-report]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "GO-verdict gate register reused: _require_go_verdict regex on '## Verdict', SystemExit on PENDING/missing (prepare_dialog_corpus lineage)"
    - "checkpoint_extra self-containment: EWC state rides every saved checkpoint — resume never depends on the Fisher sidecar"
    - "forbid_ids device contract: evaluation moves the mask itself; the sampling path does not — generation callers .to(device) once"

key-files:
  created:
    - scripts/finetune_dialog.py
    - scripts/make_transcripts.py
    - results/finetune_prod.csv
    - results/finetune_prod_run.log
    - results/transcripts.md
  modified: []

key-decisions:
  - "Best checkpoint landed at step 4000 (the final step) — in-loop masked val_loss was still improving at budget end (1.5236), so no overfit knee inside PROD_MAX_STEPS; best == final"
  - "Transcript leakage count 1 reported honestly (one warm completion re-opened an <|assistant|> turn) — REPRESENTATIVE, not cherry-picked; no re-seeding to hide it"
  - "results/finetune_prod_run.log committed alongside the CSV (results/*_run.log precedent) — it carries the printed Phase-13 provenance block"

patterns-established:
  - "Production driver hardcodes approved constants with report citations — never parses the report for numbers, only for the GO verdict"

requirements-completed: [TUNE-01, TUNE-02, EWC-03]

# Metrics
duration: ~45min (37.3 min production run on M3/MPS fp32 + transcripts + full suite)
completed: 2026-08-01
---

# Phase 12 Plan 05: Production Fine-Tune Summary

**GO-gated production fine-tune of best.pt (unmasked, LR 9e-5, λ=0.01, 4000 steps, seed 1337) producing the convbase checkpoint trio with embedded EWC state, the step-0-anchored forgetting curve, and 15 held-out transcripts with 30/30 stop-id termination**

## Performance

- **Duration:** ~45 min total; production run 37.3 min wall (4000 steps ≈ 0.56 s/step incl. per-250 evals of dialog_ppl + retention_ppl + ewc_penalty)
- **Completed:** 2026-08-01
- **Tasks:** 3 (driver / production run / transcripts)

## Production Run Results (TUNE-01 / TUNE-02 / EWC-03)

| Quantity | Value |
| --- | --- |
| Best checkpoint step | 4000 (= final step; in-loop masked val_loss still improving at budget end) |
| Best in-loop masked val_loss | 1.5236 |
| Final masked dialogue val PPL (frozen gate policy) | **4.5733** over 270,203 assistant tokens |
| Retention PPL step 0 → final | 2.1076 → 3.8911 (**drift +1.7836**) |
| Final EWC penalty | 0.1344 |
| CSV rows | 17 (step-0 row + 16 eval intervals at 250) |

Expected shape confirmed with one difference: dialogue val fell monotonically to budget end
rather than overfitting past a knee — best-checkpoint selection therefore picked the final
step. Retention drifted up from the anchor as EWC λ=0.01 is meant to bound: +1.78 at 4000
steps vs the smoke's λ=0 collapse baseline of +3.85 at only 1250 steps.

## Transcript Evidence (results/transcripts.md)

- 15 episodes, seeded (default_rng(1337)) from the held-out PersonaChat valid split
- Prompts via `encode_dialogue` (persona capped exactly as the bins) ending at `<|assistant|>` id 8186 — never hand-formatted strings
- Greedy + seeded warm (temperature 0.8, top_p 0.95) completions, `stop_ids={8184, 8185}`, dead ids forbidden, 128 max new tokens

| Proxy | Value |
| --- | --- |
| Stop-id termination fraction | **30/30 = 1.00** |
| Mid-generation role-token leakage (8185/8186/8187) | **1** (expected 0 — one warm completion re-opened an `<|assistant|>` turn; reported, not massaged) |
| Masked dialogue val PPL (convbase_best) | **4.5733** |

## Phase-13 Provenance Block (DEMO-04 identical-seed λ=0 twin)

Recorded in `results/finetune_prod_run.log` (commit 87198ec):

- **seed:** 1337 (`seed_everything` immediately before the GPT build — owns the data order)
- **train_config:** `TrainConfig(lr=9e-05, batch_size=32, max_steps=4000, warmup_steps=100, grad_clip=1.0, grad_accum_steps=1, weight_decay=0.1, seed=1337)`
- **mask arm:** unmasked (`train_mask_bin=None`)
- **ewc_lambda:** 0.01 — the ONE bit the λ=0 twin flips
- **anchor fingerprint:** `{git_sha: 3a46815da96f06d3c6196bb0949a1479884b3bce, step: 49000, val_loss: 0.7378001868724823}`
- **driver git_sha:** 04e724c67033f9a2ed8b705a07ad025c867a18c5

## Artifact Contract Proofs (driver SystemExit proofs, all passed)

- D-07 gate: driver refused-to-run path exercised in code (`_require_go_verdict`); recorded verdict GO
- Final CSV row step == 4000; retention_ppl finite in every row from step 0
- `convbase_best.pt` carries all four EWC extras (fisher / theta_star / ewc_lambda=0.01 / fisher_meta) — self-contained resume, never depends on the Fisher sidecar
- `convbase_slim.pt` loads under `torch.load(weights_only=True)` (LOCKED slim contract)

## Task Commits

| Commit | What |
| --- | --- |
| 04e724c | feat(12-05): GO-gated production fine-tune driver |
| 87198ec | feat(12-05): production curve CSV + run log (convbase checkpoints written, gitignored) |
| f675d64 | feat(12-05): transcript generator + TUNE-01 adherence evidence |

## Verification

- `results/finetune_prod.csv`: step-0 row present, retention/dialog/ewc columns finite everywhere, final step 4000 — committed
- `convbase_best.pt` prints `ewc_lambda 0.01`; slim loads `weights_only=True` — both proven post-run
- `results/transcripts.md`: 16 `## ` sections (proxies header + 15 episodes), greedy AND warm per episode, all three proxy numbers reported
- ruff clean on both scripts; `.venv/bin/python -m pytest tests/ -q` → 274 passed, 1 skipped

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] forbid_ids device mismatch in the generation path**
- **Found during:** Task 3 (first transcript run)
- **Issue:** `undecodable_ids_mask` returns a CPU tensor; `next_token` masked_fills MPS logits with it → RuntimeError (evaluation's `masked_perplexity` moves the mask itself; the sampling path does not)
- **Fix:** `.to(device)` on the mask once at build in `scripts/make_transcripts.py`
- **Files modified:** scripts/make_transcripts.py
- **Commit:** f675d64

No other deviations — the run used the approved config exactly as recorded.

## Self-Check: PASSED

- scripts/finetune_dialog.py — FOUND
- scripts/make_transcripts.py — FOUND
- results/finetune_prod.csv — FOUND
- results/transcripts.md — FOUND
- checkpoints/convbase_best.pt / convbase_slim.pt — FOUND (gitignored)
- Commits 04e724c, 87198ec, f675d64 — FOUND
