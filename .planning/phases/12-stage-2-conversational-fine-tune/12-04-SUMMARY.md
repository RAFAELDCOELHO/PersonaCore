---
phase: 12-stage-2-conversational-fine-tune
plan: 04
subsystem: training, evaluation, continual
tags: [smoke, pre-registration, ewc, lambda-sweep, lr-sweep, masking, noise-floor, mps]

# Dependency graph
requires:
  - phase: 12-stage-2-conversational-fine-tune
    provides: "12-01 train() seams (train_mask_bin/val_mask_bin/extra_eval_fns), 12-02 masked_perplexity gate metric, 12-03 retention sub-bin + step-0 anchors"
  - phase: 10-ewc
    provides: "EWCPenalty + load_fisher fingerprint check + fisher_tinystories.pt cache"
provides:
  - "scripts/finetune_smoke.py — pre-registered sequential smoke driver (gates committed before any number, 10ba73e)"
  - "scripts/finetune_smoke_stage3_override.py — recorded D-07 Stage-2 override wrapper (gate NOT amended, committed before any λ number)"
  - "results/finetune_smoke_report.md — D-06 committed evidence, GO verdict recorded 2026-08-01"
  - "13 tracked results/ft_*.csv arm logs (Phase 13 frontier/forgetting inputs)"
  - "Production config for Plan 12-05: unmasked, LR 9e-5, λ=0.01, PROD_MAX_STEPS 4000, seed 1337 / batch 32 / accum 1"
affects: [12-05, 13-forgetting-curves, 15-report]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-registration by git order: gate constants committed before any measured number; violated gates halt via SystemExit and surface to the user (D-07)"
    - "Recorded override as committed wrapper: driver gates stay untouched; override wrapper re-evaluates the gate, refuses if it no longer fires, then applies downstream pre-registered rules verbatim"
    - "Skip-if-done arm resume: completed CSV + final checkpoint ⇒ skip and re-measure; partial CSV ⇒ delete and restart from anchor (survived one mid-λ-arm process kill)"

key-files:
  created:
    - scripts/finetune_smoke.py
    - scripts/finetune_smoke_stage3_override.py
    - results/finetune_smoke_report.md
    - results/ft_cal.csv
    - results/ft_noise_a.csv
    - results/ft_noise_b.csv
    - results/ft_masked.csv
    - results/ft_unmasked.csv
    - results/ft_lr_3e-4.csv
    - results/ft_lr_9e-5.csv
    - results/ft_lr_3e-5.csv
    - results/ft_lam_0.01.csv
    - results/ft_lam_0.1.csv
    - results/ft_lam_1.csv
    - results/ft_lam_10.csv
    - results/ft_lam_100.csv
  modified: []

key-decisions:
  - "SMOKE_STEPS locked at 1250 by the Stage-0 slope rule (recommended 1250, capped=False)"
  - "Noise floor: Δ_dialog=0.001704, Δ_ret=0.068930; all margins K×Δ with blind K=2"
  - "Masking verdict: UNMASKED (4.4453 vs 4.4706, separation k=14.8× floor)"
  - "Stage-2 gate §7(a) fired on ALL LR arms — user override RECORDED, gate NOT amended: λ sweep at LR 9e-5; λ=0 drift +3.85 is the formal 'collapse without EWC' baseline"
  - "§8 verdict (pre-registered, untouched): candidates=[], λ*=None, demonstrable=False — EWC not demonstrable at this budget"
  - "Production λ=0.01 is a SEPARATE post-verdict discretionary decision (case b: feeds Phase-14 demo substrate only; Phase 13 runs its own arms from best.pt)"

patterns-established:
  - "D-07 override protocol: halt → user decision → override recorded in a committed artifact before any downstream number exists"

requirements-completed: [EWC-03, TUNE-01, TUNE-02]

# Metrics
duration: ~5h (multi-session: stages 0-2 + gate halt, then stage-3 override run)
completed: 2026-08-01
---

# Phase 12 Plan 04: Pre-Registered Calibration Smoke Summary

**Full pre-registered smoke sequence (budget 1250, noise floor, unmasked verdict, LR-gate all-fail with recorded user override at 9e-5, λ decade sweep) landing the honest §8 verdict "EWC not demonstrable at this budget" plus a separately-labeled discretionary λ=0.01 production config for Plan 12-05**

## Performance

- **Duration:** ~5h across two executor sessions (gate halt + user checkpoint in between); Stage-3 sweep ~75 min on M3/MPS fp32 (~0.44 s/step incl. evals)
- **Completed:** 2026-08-01
- **Tasks:** 3 (driver commit / smoke execution / D-07 checkpoint)

## The Stage-2 Gate Story (D-07 exception, recorded override)

All three LR arms violated pre-registered retention gate §7(a) — drift vs anchor 2.1076 with
margin K×Δ_ret = 0.1379:

| LR | Dialogue PPL | Retention drift |
|----|-------------|-----------------|
| 3e-4 | 4.2034 | +6.63 |
| 9e-5 | 4.4453 | +3.85 |
| 3e-5 | 4.7771 | +2.81 |

The driver halted per §9; the halt was surfaced at a blocking checkpoint. **User decision
(override recorded, gate NOT amended):** §7(a) tests retention against a no-EWC baseline —
the "near-zero forgetting" expectation presupposes the mechanism that only enters in Stage 3.
Not a calibration failure; it is the central phenomenon Phase 12/13 studies. λ sweep proceeded
at LR 9e-5 with that arm's numbers (dialogue 4.4453, drift +3.85) formally recorded as the
"collapse without EWC" baseline. The override lives in
`scripts/finetune_smoke_stage3_override.py` (committed 7b27a5b before any λ number): it
re-evaluates the Stage-2 gate verbatim, refuses to run if any arm passes, then calls the
driver's pre-registered `stage3_lambda()` + `write_report()` unchanged.

## §8 Verdict (recorded verbatim, never massaged)

λ sweep at LR 9e-5, unmasked, 1250 steps (λ=0 baseline: dialogue 4.4453, retention 5.9553):

| λ | Dialogue PPL (vs λ=0) | Retention PPL (drift vs anchor) |
|---|----------------------|--------------------------------|
| 0.01 | 4.7298 (+0.284) | 3.7813 (+1.674) |
| 0.1 | 5.6355 (+1.190) | 3.0057 (+0.898) |
| 1 | 7.2144 (+2.769) | 2.7734 (+0.666) |
| 10 | 10.5552 (+6.110) | 2.1351 (+0.028) |
| 100 | 16.2112 (+11.766) | 2.1082 (+0.0007) |

Pre-registered §8 outcome: within-margin candidates = [], **λ\* = None, demonstrable = False —
"EWC not demonstrable at this budget."** Boundary-extension rule did not fire (no candidate on
an endpoint). Every λ arm beat the collapse baseline on retention (λ=100 essentially
eliminates forgetting) but none stayed within the K×Δ_dialog = 0.0034 dialogue margin — the
stability–plasticity trade-off is real and measured; the joint demonstration failed at this
1250-step budget.

## Production Config Decision (post-verdict, discretionary)

Recorded in the report as a separate labeled section: the §8 verdict stands negative; the
production choice of **λ=0.01** is a separate engineering decision made AFTER the verdict,
optimizing lowest adaptation cost (+0.28 PPL, ~6% relative) with the largest relative
forgetting reduction on the grid (drift +3.85 → +1.67, ~57%). Case b confirmed against
ROADMAP/CONTEXT: this config feeds only the teach-then-recall demo substrate (Phase 14);
Phase 13 runs its own naive/EWC arms from scratch from best.pt, so the choice neither
contaminates nor substitutes the paper's central causal result.

**Plan 12-05 MUST use:** training loss **unmasked**, LR **9e-5**, λ **0.01**, PROD_MAX_STEPS
**4000** (≈29 min at 0.439 s/step), seed 1337 / batch 32 / grad_accum 1. The report's
`## Verdict` is GO (recorded 2026-08-01) — 12-05's driver may proceed.

## Other Recorded Facts

- Step-0 row mechanism (TUNE-02): loop logs NO step-0 row — every arm CSV pre-seeded by the
  driver with a measured step-0 row (recorded in the report header).
- Stage-1 cold-start diagnostic: no trigger on either arm; role-embedding norms stable.
- Stage-2 9e-5 arm ran fresh at eval_interval 250 (noise_a reuse rule inapplicable — unmasked
  won Stage 1).
- One mid-λ-100 process kill was absorbed by skip-if-done (partial CSV deleted, arm restarted
  from the anchor, deterministic replay verified: all prior stage numbers reproduced exactly).

## Task Commits

| Commit | What |
|--------|------|
| 10ba73e | Pre-registered smoke driver (before any run) |
| 2e4fa81 | SMOKE_STEPS=1250 lock (Stage-0 slope rule) |
| 7aac9e3 | Stage 0/0b/1/2 CSVs at the gate halt |
| 7b27a5b | D-07 override wrapper (gate NOT amended, before any λ number) |
| 814e58e / d24feea / 3b4195b / 8e13d91 / 3743cae | λ = 0.01 / 0.1 / 1 / 10 / 100 arm CSVs (atomic per arm) |
| 666d096 | Smoke report with override recording, verdict PENDING |
| 5b6a387 | GO verdict + discretionary λ=0.01 production decision |

## Verification

- 13 `results/ft_*.csv` tracked; `ft_lam_1.csv` header carries dialog_ppl + retention_ppl +
  ewc_penalty columns with a step-0 row
- Report contains every stage section with numeric tables, per-gate counterfactual k, the
  override section, the discretionary-decision section, and a non-PENDING GO verdict
- `.venv/bin/python -m pytest tests/ -q` → 274 passed, 1 skipped (no src/ changes)
- ruff clean on both driver scripts

## Deviations from Plan

**1. [User-directed] Stage-2 §7(a) all-fail halt → recorded override wrapper**
- **Found during:** Task 2 (Stage 2)
- **Issue:** zero LR arms passed the retention gate (pre-registered halt fired as designed)
- **Resolution:** user decision at the D-07 exception — override recorded in a committed
  wrapper (7b27a5b), pre-registered gates left untouched, λ sweep run at LR 9e-5
- **Files:** scripts/finetune_smoke_stage3_override.py

No other deviations — all pre-registered rules applied exactly as committed.

## Self-Check: PASSED

- scripts/finetune_smoke.py — FOUND
- scripts/finetune_smoke_stage3_override.py — FOUND
- results/finetune_smoke_report.md (GO verdict) — FOUND
- results/ft_lam_{0.01,0.1,1,10,100}.csv — FOUND
- Commits 10ba73e, 2e4fa81, 7aac9e3, 7b27a5b, 814e58e, d24feea, 3b4195b, 8e13d91, 3743cae, 666d096, 5b6a387 — FOUND
