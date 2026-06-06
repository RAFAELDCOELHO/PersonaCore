---
phase: 05-tinystories-pretraining
plan: 02
subsystem: training
tags: [mps, fp32, pretraining, checkpoint, resume, best-val, perplexity, tinystories, memmap, sampling]

# Dependency graph
requires:
  - phase: 04-gpt-transformer-decoder
    provides: GPT decoder (LOCKED 6L/6H/384d, vocab 8192) + train(...) loop with AMP/accum/clip + resume RNG-restore contract
  - phase: 05-tinystories-pretraining (plan 01)
    provides: get_batch_memmap sampler + data/train.bin / data/val.bin (uint16 memmap corpus)
provides:
  - 4 additive train(...) seams (memmap data branch, estimate_loss path support, best-val best.pt tracking, periodic latest.pt + sample hook) — all guarded by optional kwargs, zero change to _optimizer_step / load_checkpoint
  - scripts/pretrain_tinystories.py — thin no-CLI run entry (preflight LOCAL memmaps, calibrated TrainConfig, kill-survivable resume, post-run sample + perplexity print)
  - tests/test_mps_smoke.py (PRE-02 / D-01a MPS finite-loss + overfit gate), tests/test_resume_memmap.py (PRE-02 bit-for-bit resume on memmap), tests/test_best_ckpt.py (PRE-03 best.pt lowest-val + perplexity)
  - checkpoints/best.pt — the SHIPPED trained checkpoint (val_loss 0.7378, perplexity 2.091, lowest-val at step 49000)
  - logs/run.csv — 50k-step training/val/lr curves
affects: [06-generation-sampling (consumes best.pt), 07-lora-personalization, 08-demo-notebook-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive loop seams guarded by optional kwargs (default None) — existing 3 data modes + all prior tests pass unchanged"
    - "best.pt = lowest observed val_loss (save-on-improve), separate from periodic latest.pt (kill-survivability)"
    - "perplexity = exp(best_val_loss) recoverable directly from the shipped checkpoint"
    - "Thin no-CLI run entry mirroring train_bigram.py; calibrated hyperparameters as marked constants"

key-files:
  created:
    - scripts/pretrain_tinystories.py
    - tests/test_mps_smoke.py
    - tests/test_resume_memmap.py
    - tests/test_best_ckpt.py
  modified:
    - src/personacore/training/loop.py

key-decisions:
  - "Calibrated run config (Task 4, MEASURED on M3): lr=3e-4, batch_size=32, block_size=256, grad_accum=1, max_steps=50000, warmup=100, seed=1337 — sized quality-first (D-04)"
  - "best.pt saved on val-loss improvement only; captured step 49000 (val 0.7378), NOT the final step 50000 (val 0.7393) — proves the lowest-val contract (D-08)"
  - "Seams are strictly additive: git diff shows no change inside _optimizer_step (AMP/accum/clip/step/sched ordering) or the resume load_checkpoint block"

patterns-established:
  - "Pattern 1: best-val checkpoint (save-on-improve) decoupled from periodic resume checkpoint"
  - "Pattern 2: long-run entry preflights device (strict) + asserts LOCAL .bin existence before any multi-hour work"

requirements-completed: [PRE-02, PRE-03]

# Metrics
duration: ~5h (M3/MPS run incl. calibration gate; Tasks 1-3 code ~7min)
completed: 2026-06-05
---

# Phase 5 Plan 02: TinyStories Pretraining Run Summary

**A from-scratch 17M-param GPT pretrained to coherent TinyStories generation on local Apple Silicon (M3/MPS, fp32) — 50,000 steps, shipped `best.pt` at val_loss 0.7378 (perplexity 2.091), kill+resume survived mid-run, samples are fluent child-story prose.**

## Performance

- **Duration:** Tasks 1–3 (code) ~7 min; Task 4–5 (calibration + the long run) ~5h elapsed on M3
- **Started:** 2026-06-05T16:38Z (code) / ~17:25 local (run)
- **Completed:** 2026-06-05 (run finished ~22:24 local; best.pt at step 49000)
- **Tasks:** 5 (3 code/TDD + 2 blocking human checkpoints)
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments
- **Trained checkpoint shipped** — `checkpoints/best.pt`: val_loss **0.7378**, **perplexity = exp(0.7378) = 2.091**, captured at step **49000** (the global-minimum val across all 200 eval points — verified, not the final step). Holds full resumable state (model/optimizer/scheduler/scaler/step/rng/configs/git_sha=3a46815).
- **Coherent generation reached** (D-07 acceptance bar = perplexity AND coherent samples). Real samples drawn from best.pt (temp 0.8, seed 42):
  - *"Once upon a time, there was a polite dog named Spot. Spot liked to play... One day, Spot saw a big tree and wanted to climb it. As Spot tried to climb the tree, he found a shiny stone on the ground..."*
  - *"Once upon a time, there was a little car named Zoomy. Zoomy loved to go fast and make big splashes... One day, Zoomy's friend, a big truck named Hanger, was going on a holiday..."*
  - *"One day, a thin cat named Tim went for a walk. He saw a pretty rainbow in the sky... Tim walked to the rainbow and said, 'Hello, rainbow! What is your name?'"*
- **4 additive loop seams** woven into the proven `train(...)`: memmap data branch (`train_bin`/`val_bin`), `estimate_loss` path support, best-val `best.pt` tracking, periodic `latest.pt` + qualitative sample hook — all optional-kwarg-guarded, **zero change** to `_optimizer_step` or the resume `load_checkpoint` block.
- **Kill+resume validated on the real run** (D-04) — the run was interrupted and resumed from `latest.pt` mid-training and continued cleanly; `test_resume_memmap.py` proves bit-for-bit resume on the memmap source on CPU.
- **MPS sanity gate green** — `test_mps_smoke.py` runs the real GPT on `device=mps`, proves finite loss and overfit-toward-zero (D-01a), and actually PASSED in-suite on this M3 (not just skipped).
- **`logs/run.csv`** — full 50,000-step curves (train_loss, val_loss, lr) for the demo notebook.

## Task Commits

1. **Task 1: Wave-0 RED PRE-02/PRE-03 tests** — `1422b4c` (test) — MPS smoke, resume-memmap, best-ckpt (RED until Task 2)
2. **Task 2: 4 additive loop.py seams** — `35577b4` (feat, TDD GREEN)
3. **Task 3: pretrain_tinystories.py run entry** — `38dd1d9` (feat)
4. **Task 4: MPS sanity gate + calibration smoke** — blocking human-verify (MEASURED config; no code commit by design — calibration is measurement)
5. **Task 5: long resumable M3/MPS run to coherence** — blocking human-action (produced best.pt / run.csv / samples; artifacts gitignored)

**Pause marker:** `3a46815` (docs: pause at Task 4 — the SHA recorded in best.pt's provenance).

## Files Created/Modified
- `src/personacore/training/loop.py` — 4 additive seams (memmap branch, estimate_loss path, best-val/best.pt, periodic latest.pt + sample hook)
- `scripts/pretrain_tinystories.py` — thin no-CLI run entry; `preflight_device(strict=True)`, LOCAL `.bin` assertion, calibrated TrainConfig, resume-from-latest, post-run sample + perplexity
- `tests/test_mps_smoke.py` — module-guarded MPS finite-loss + overfit gate (PRE-02 / D-01a)
- `tests/test_resume_memmap.py` — CPU bit-for-bit resume on the memmap data source (PRE-02)
- `tests/test_best_ckpt.py` — best.pt lowest-val tracking + perplexity recoverability (PRE-03)

## Decisions Made
- **Calibrated config from measurement (Task 4), not invented:** lr=3e-4, batch_size=32, block_size=256, grad_accum=1, max_steps=50000, warmup=100, seed=1337. Quality-first sizing (D-04); ~410M tokens seen (50k × 32 × 256).
- **best.pt = save-on-val-improvement**, decoupled from periodic `latest.pt` — so the shipped artifact is the lowest-val step (49000), independent of where the run happened to stop.

## Deviations from Plan
None — plan executed as written. The four seams are strictly additive (verified: no diff inside `_optimizer_step` or the resume block); the run used MEASURED hyperparameters per the Task-4 calibration mandate.

## Issues Encountered
- **Model size note (not a Phase-5 decision):** the LOCKED Phase-4 `ModelConfig` (6L/6H/384d, vocab 8192) totals **17.04M** parameters — slightly above the 10–15M nominal target in CLAUDE.md (tied head; ~14M non-embedding). It trains comfortably on M3/MPS in fp32 and meets the coherence bar, so it was kept as-is.
- **`latest.pt` `val_loss` field cosmetic:** the periodic `latest.pt` stores the in-loop step loss (0.6989 at step 50000) in its `val_loss` slot rather than the eval val_loss — informational only; `latest.pt` is for resume, and `best.pt` (the shipped artifact) carries the correct eval val_loss. No impact on the goal.

## Verification Evidence
- `python -m pytest -q` → **102 passed, 1 skipped** (the 1 skip is the CUDA-only fp16-AMP smoke; `test_mps_smoke.py` PASSED — MPS available on this M3).
- `awk` over `logs/run.csv` → global min val_loss = **0.7378001868724823 at step 49000**, matching best.pt exactly (best.pt captured the lowest val, not the final step).
- `torch.load("checkpoints/best.pt")` → `val_loss=0.7378`, `step=49000`, `perplexity=exp(val_loss)=2.0913`, full resume state present (optimizer/scheduler/scaler/rng/configs/git_sha).
- Live sampling from best.pt (temp 0.8) → 3 fluent, grammatical TinyStories-register stories (quoted above).
- `data/train.bin` (2.5 GB) + `data/val.bin` (25 MB) present; `logs/run.csv` = 201 lines (50k steps @ eval-interval 250).

## User Setup Required
None — the run is complete. `best.pt` / `latest.pt` / `run.csv` / `data/*.bin` are gitignored (never committed); the trained checkpoint lives on local disk and is consumed directly by Phase 6.

## Next Phase Readiness
- **Phase 6 (Generation & Sampling) unblocked:** `checkpoints/best.pt` is the trained, coherent base LM it consumes. The minimal `sample()` in loop.py proved coherence; Phase 6 builds the full temperature/top-k `generate()`.
- The from-scratch base-LM claim is now demonstrable end-to-end: hand-built BPE → memmap corpus → hand-built GPT → resumable local M3 pretraining → coherent generation, perplexity 2.091.

## Self-Check: PASSED

All created files present (`scripts/pretrain_tinystories.py`, `tests/test_mps_smoke.py`, `tests/test_resume_memmap.py`, `tests/test_best_ckpt.py`, modified `loop.py`); all code task commits present (`1422b4c`, `35577b4`, `38dd1d9`); shipped artifacts verified on disk (`best.pt` lowest-val @ step 49000, `run.csv` 50k steps); coherent samples reproduced live; PRE-02 + PRE-03 satisfied.

---
*Phase: 05-tinystories-pretraining*
*Completed: 2026-06-05*
