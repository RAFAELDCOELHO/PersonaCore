---
phase: 04-gpt-transformer-decoder
plan: 03
subsystem: testing
tags: [gpt, overfit, integration-gate, harness-swap, tdd-green, mvp-acceptance]

# Dependency graph
requires:
  - phase: 04-gpt-transformer-decoder
    plan: 01
    provides: "RED tests/test_gpt_overfit.py scaffold (seed-first, (4,16) fixed batch, ln(8192)-2 band assertion)"
  - phase: 04-gpt-transformer-decoder
    plan: 02
    provides: "src/personacore/model/gpt.py — the real GPT(ModelConfig()) this gate trains end-to-end"
  - phase: 03-bigram-baseline-training-harness
    provides: "The UNTOUCHED train()/TrainConfig/seed_everything harness the GPT drops into via fixed_batch+return_final_loss"
provides:
  - "tests/test_gpt_overfit.py GREEN — the MVP end-to-end harness-swap acceptance proof (MODEL-02 SC#1)"
  - "Confirmed: the real 6-layer GPT overfits one fixed batch through the existing loop with zero harness changes"
affects: [phase-5-pretraining, m2-lora]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Harness-swap proof: only the model differs from the bigram overfit; train()/TrainConfig/seed_everything reused verbatim (D-07/D-10)"
    - "Overfit-band assertion (loss < ln(8192)-2) is the acceptance contract — tuned hyperparameters, never a loosened threshold"

key-files:
  created: []
  modified:
    - tests/test_gpt_overfit.py

key-decisions:
  - "lr=1e-3 / warmup_steps=0 / max_steps=300 / batch_size=4 confirmed as the final overfit config for the 6-layer pre-norm GPT (vs the bigram's lr=1e-1; RESEARCH Open Q1) — measured final loss ~5e-4, margin ~7.0 under the bound"
  - "FULL ModelConfig used (block_size=256) — no reduced-block_size shortcut needed; CPU runtime ~11s, so the harness-swap proof holds at the real architecture (n_layer/n_head/n_embd unchanged)"
  - "ln(8192)-2.0 acceptance threshold left UNCHANGED; the scaffold's Plan-03 delegation NOTE replaced with the measured final values"

patterns-established:
  - "The Phase-3 train() loop is model-agnostic in practice: a 6-layer GPT and a bigram both overfit through it with only the model and lr changing"

requirements-completed: [MODEL-02]

# Metrics
duration: 4min
completed: 2026-06-05
---

# Phase 4 Plan 03: GPT Overfit Gate Summary

**The real `GPT(ModelConfig())` overfits a single fixed batch through the UNTOUCHED Phase-3 `train()` loop — final loss ~5e-4 vs the `ln(8192)-2.0 ~= 7.01` bound (margin ~7.0) in ~11s on CPU — turning `tests/test_gpt_overfit.py` GREEN and proving the from-scratch transformer drops into the proven harness with zero harness changes (MODEL-02 success criterion #1).**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-06-05
- **Completed:** 2026-06-05
- **Tasks:** 1
- **Files modified:** 1 (0 created, 1 modified)

## Accomplishments
- **Task 1** — Confirmed the Plan-01 starting hyperparameters (`lr=1e-3`, `warmup_steps=0`, `max_steps=300`, `batch_size=4`, `grad_accum_steps=1`) already drive the full 6-layer `GPT(ModelConfig())` to **final loss ~5e-4** — a margin of ~7.0 below the `ln(8192)-2.0` acceptance band — in ~11s on CPU. No further tuning, no reduced `block_size`, no harness change required.
- Replaced the scaffold's "Plan-03 executor: tune these" delegation NOTE with the measured, finalized values and the observed result, keeping the band assertion (`< math.log(8192) - 2.0`) unchanged.
- Verified the harness-swap proof: `git status` shows ONLY `tests/test_gpt_overfit.py` changed — `train()` (loop.py), `TrainConfig` (config.py), `seed_everything` (seeding.py), and `GPT` (gpt.py) are all reused untouched.
- Full CPU-only suite GREEN: **88 passed / 1 skipped** (no regression from Plan 02; the lone tokenizer "corpus exhausted" UserWarning is the pre-existing Phase-2 one, out of scope). `ruff check` + `ruff format --check` clean on the test file.

## Task Commits

Each task was committed atomically:

1. **Task 1: Green the GPT overfit gate through the untouched loop** - `db91799` (test)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified
- `tests/test_gpt_overfit.py` (modified) — Replaced the Plan-03 delegation NOTE with the confirmed final overfit config and measured result (~5e-4 loss, ~11s CPU, full `ModelConfig`); the `(4,16)` fixed batch, `seed_everything(1337)`-first ordering, `train(..., fixed_batch=..., return_final_loss=True)` call, and `ln(8192)-2.0` threshold are unchanged.

## Decisions Made
- **`lr=1e-3` confirmed final** (RESEARCH Open Q1): a 6-layer pre-norm GPT overfits the tiny fixed batch cleanly at 1e-3 (an order of magnitude below the bigram's 1e-1), no schedule warmup needed; 300 steps is ample (loss already ~5e-4).
- **Full `ModelConfig` (block_size=256), no shortcut**: CPU runtime is ~11s, so the reduced-block_size escape hatch in the plan was unnecessary — the harness-swap proof holds at the real `n_layer=6/n_head=6/n_embd=384` architecture.
- **Threshold untouched**: the `ln(8192)-2.0` band is the acceptance contract; only hyperparameters were finalized, never the assertion.

## Deviations from Plan

None — plan executed exactly as written. The Plan-01 starting `TrainConfig` already cleared the band with a large margin, so "tuning" amounted to confirming and documenting the final values rather than searching for them. No harness file was touched.

## Issues Encountered
- `make test` / `make lint` invoke bare `python`/`ruff`, which resolve to the local pyenv (Python 3.14) where dependencies are not installed (collection errors) and `ruff` is absent. Per CLAUDE.md the mandatory Python 3.11 `.venv` was used for all pytest/ruff invocations (Kaggle/CI parity); CI runs the same suite via `.[cpu,dev]` on 3.11. No code impact — the suite and lint are GREEN via the venv.
- The pre-existing Phase-2 `test_tokenizer_io.py` "corpus exhausted" UserWarning persists; unrelated to this plan, not modified.

## Known Stubs

None — the test trains the real `GPT` end-to-end through the real loop and asserts a real measured loss. No placeholders, no mocked model, no loosened bound.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Phase 4 is functionally complete: the from-scratch GPT (Plan 02) is proven correct (8 unit gates) AND proven to learn end-to-end through the untouched Phase-3 harness (this overfit gate) — the MVP MODEL-02 acceptance is fully GREEN.
- Phase 5 (Pretraining) can now run the real GPT through `train()` on the TinyStories corpus path with the same loop, swapping `attn_impl="sdpa"` for the GPU path; the overfit gate is the regression guard that the model+loop wiring stays correct.
- No blockers.

## Self-Check: PASSED

Task commit `db91799` is present in git history; `tests/test_gpt_overfit.py` exists on disk and is modified; the gate passes (`final_loss ~5e-4 < ln(8192)-2.0`); the full suite is 88 passed / 1 skipped; `git status` confirms only the test file changed (no harness file).

---
*Phase: 04-gpt-transformer-decoder*
*Completed: 2026-06-05*
