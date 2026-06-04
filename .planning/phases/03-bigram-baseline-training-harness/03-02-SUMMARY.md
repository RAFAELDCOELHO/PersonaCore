---
phase: 03-bigram-baseline-training-harness
plan: 02
subsystem: model + training
tags: [model, loss, bigram, ewc-seam, tdd]
requires:
  - "personacore.config (ModelConfig.vocab_size — sizing reference, not imported here)"
  - "tests/test_bigram_model.py, tests/test_assemble_loss.py (RED contracts from Plan 01)"
provides:
  - "personacore.model.BigramLanguageModel — LOCKED forward(idx, targets=None) -> (logits, loss)"
  - "personacore.training.loss.assemble_loss — identity-on-empty / additive M2 EWC seam"
affects:
  - "Phase 4 GPT honors the same forward contract unchanged"
  - "Plan 03-04 training loop calls assemble_loss(base_loss, ()) at its loss call site"
  - "Milestone 2 EWC passes (fisher_penalty,) into assemble_loss with no loop change"
tech-stack:
  added: []
  patterns:
    - "nanoGPT (B*T, V) vs (B*T) cross-entropy flatten so the same model call works for the GPT"
    - "Pure model / loop-level loss assembly split (D-03) keeps continual-learning additive in M2"
    - "Decision-anchored module docstrings matching config.py / seeding.py repo convention"
key-files:
  created:
    - src/personacore/model/bigram.py
    - src/personacore/model/__init__.py
    - src/personacore/training/loss.py
  modified: []
decisions:
  - "training/__init__.py deliberately NOT created — Plan 04 owns the full training surface; namespace-package discovery resolves personacore.training.loss without it"
metrics:
  duration: 6
  completed: 2026-06-04
---

# Phase 3 Plan 02: Model→Loss Contract Summary

The first vertical slice of Phase 3: a from-scratch bigram LM exposing the LOCKED
`forward(idx, targets=None) -> (logits, loss)` contract (D-02) and the loop-level
`assemble_loss` M2 EWC seam (D-04), turning the RED MODEL-01 and TRAIN-06(loss) tests GREEN.

## What Was Built

- **`BigramLanguageModel`** — a single `nn.Embedding(vocab_size, vocab_size)` lookup table.
  `forward` returns `(logits, None)` without targets (sampling path) and `(logits, loss)` with
  targets, where the scalar loss is `F.cross_entropy(logits.view(B*T, V), targets.view(B*T))`
  — the nanoGPT flatten (D-02a) that the Phase-4 GPT will reuse unchanged. The model is pure:
  no penalties, no `assemble_loss`, no `generate`/`sample` (D-03 / D-11).
- **`model/__init__.py`** — thin barrel exporting `BigramLanguageModel` (D-09); Phase 4 adds
  `from .gpt import GPT` here later.
- **`assemble_loss(base_loss, extra_penalties=())`** in `training/loss.py` — identity on the
  empty tuple (M1 path), additive over a tuple of precomputed scalar penalty tensors (M2 EWC
  seam). No callbacks/lazy callables (D-04). Lives in `training/`, never in the model (D-03).

## Verification

- `pytest tests/test_bigram_model.py tests/test_assemble_loss.py -q` → 7 passed (GREEN).
- `python -c "from personacore.model import BigramLanguageModel"` resolves; `assemble_loss`
  imports via the full path `personacore.training.loss`.
- Rest of the CPU suite (everything except the still-RED Phase-3 data/schedule/loop modules)
  → 61 passed.
- `ruff check` + `ruff format --check` on the new files → clean.

## TDD Gate Compliance

This plan turns pre-existing RED tests (committed in Plan 01) GREEN, so the `test(...)` RED
gate commit lives in Plan 01's history; this plan supplies the `feat(...)` GREEN gate commits
(0e26852 for the model, 07fcc43 for the loss seam). RED state was confirmed before
implementation (both target modules raised `ModuleNotFoundError`); no test passed unexpectedly.

## Expected-RED Tests Still Failing (out of scope)

Per the plan's notes, these Phase-3 tests remain RED — Plans 03/04 turn them GREEN:
`test_data_split.py` (`training.data`), `test_lr_schedule.py` (`training.schedule`),
`test_overfit_batch.py` / `test_resume_curve.py` / `test_train_loop.py` (`training.loop`).
None are caused by this plan's changes; all are missing-module collection errors for modules
owned by later plans.

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | from-scratch bigram model + package barrel (MODEL-01) | 0e26852 |
| 2 | assemble_loss seam — the M2 EWC hook (TRAIN-06) | 07fcc43 |

## Self-Check: PASSED

- FOUND: src/personacore/model/bigram.py
- FOUND: src/personacore/model/__init__.py
- FOUND: src/personacore/training/loss.py
- FOUND: commit 0e26852
- FOUND: commit 07fcc43
