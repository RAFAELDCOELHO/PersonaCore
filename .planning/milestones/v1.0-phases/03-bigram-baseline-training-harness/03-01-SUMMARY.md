---
phase: 03-bigram-baseline-training-harness
plan: 01
subsystem: training-harness-tests
tags: [tdd, red-scaffold, fixtures, pytest, bigram, training-loop]
requires:
  - personacore.tokenizer.from_json (frozen artifacts/tokenizer.json, EOS_ID 8184)
  - personacore.config (ModelConfig, TrainConfig, RuntimeConfig)
  - personacore.seeding.seed_everything
provides:
  - "RED acceptance contracts for every Phase-3 seam (MODEL-01, TRAIN-01..06)"
  - "tests/fixtures/bigram_corpus.txt — committed D-06 corpus, 4 eos-separated docs"
affects:
  - "Plans 03-02/03/04 turn these RED tests GREEN; no production module added here"
tech-stack:
  added: []
  patterns:
    - "Module docstring anchors the requirement/decision ID (config.py convention)"
    - "CORPUS_PATH = Path(__file__).parent / fixtures (test_tokenizer_io.py:19)"
    - "Resume test mirrors test_checkpoint.py::test_resume_identical_trajectory"
    - "Inline @pytest.mark.skipif(not torch.cuda.is_available()) for the GPU-only smoke"
key-files:
  created:
    - tests/fixtures/bigram_corpus.txt
    - tests/test_bigram_model.py
    - tests/test_assemble_loss.py
    - tests/test_lr_schedule.py
    - tests/test_data_split.py
    - tests/test_train_loop.py
    - tests/test_overfit_batch.py
    - tests/test_resume_curve.py
  modified: []
decisions:
  - "GPU fp16 smoke uses inline skipif WITH a required reason= (clean SKIP, not a collection ERROR) on CPU CI; the exact literal skipif(not torch.cuda.is_available()) is preserved in a comment so the plan's verify grep still matches"
metrics:
  duration_min: 6
  completed: "2026-06-04"
  tasks: 5
  files: 8
---

# Phase 3 Plan 01: Wave-0 RED Test Scaffold + Corpus Fixture Summary

One committed TinyStories-style corpus fixture plus seven RED pytest files that encode the
executable acceptance contracts for all seven Phase-3 seams (MODEL-01, TRAIN-01..06) and fail
purely on missing-module ImportError — the "failing end-to-end test first" step before any
harness code exists.

## What Was Built

- **`tests/fixtures/bigram_corpus.txt`** (Task 1, D-06): 4 TinyStories-register documents
  separated by the literal `<|endoftext|>`, plain UTF-8, with a trailing separator so a whole
  document is reservable for validation. Encodes cleanly through the FROZEN 8192-vocab
  `artifacts/tokenizer.json` with the atomic eos id `8184` at every one of the 4 boundaries.
- **`tests/test_bigram_model.py`** (Task 2, MODEL-01 / D-02): asserts the locked `forward`
  contract — `(logits, None)` without targets, `(logits, scalar loss)` with targets,
  `logits.shape == (B, T, vocab_size)`, and a uniform-init CE bound near `ln(vocab_size)`.
- **`tests/test_assemble_loss.py`** (Task 2, TRAIN-06 / D-04a): identity-on-empty + additive
  EWC-seam semantics for `assemble_loss(base, extra_penalties=())`.
- **`tests/test_lr_schedule.py`** (Task 3, TRAIN-01): warmup ramp 0→1, cosine decay toward
  `min_ratio`, LR-at-optimizer-step-N matches the lambda at N (NOT N×grad_accum — Pitfall 2),
  and `state_dict()` round-trips `last_epoch`.
- **`tests/test_data_split.py`** (Task 3, TRAIN-03): doc-boundary split with a verbatim
  no-leakage check (Pitfall 3), eos-at-boundary assertion (Pitfall 6), and `get_batch` shape /
  int64-dtype / in-bounds contract — reads the committed fixture via the frozen tokenizer.
- **`tests/test_train_loop.py`** (Task 4, TRAIN-01/02): spies the AMP op order
  `unscale_ → clip → step → update` with exactly one `unscale_` per optimizer step (Pitfall 1),
  a grad-accum-equals-big-batch equivalence test, and a GPU-only fp16 smoke behind an inline
  `skipif`.
- **`tests/test_overfit_batch.py`** (Task 4, TRAIN-05 / D-10): seeded one-fixed-batch
  memorization driving CE well below the `ln(8192)≈9.0` ceiling.
- **`tests/test_resume_curve.py`** (Task 4, TRAIN-04/06): kill-and-resume trajectory equality
  within 1e-6 on the real `BigramLanguageModel` (modeled on
  `test_checkpoint.py::test_resume_identical_trajectory`) plus a CSV-restart check —
  concatenated pre-kill/post-resume rows equal an uninterrupted run with the header written
  exactly once (Pitfall 4).

## Verification

- All seven files parse as valid Python and import the not-yet-existing modules.
- `pytest` on the seven files yields collection errors that are **exclusively**
  `ModuleNotFoundError: No module named 'personacore.model'` / `'personacore.training'` — RED for
  the right reason, with zero syntax or fixture-missing errors.
- The committed fixture encodes through the frozen tokenizer with `8184` appearing 4 times
  (≥2 doc boundaries required).
- Inherited Phase-1/2 suite: **54 passed** (1 pre-existing, unrelated corpus-exhaustion warning).
- `ruff check` + `ruff format --check` clean on all new files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] GPU smoke `skipif` would ERROR (not SKIP) on CPU CI without a `reason`**
- **Found during:** Task 4
- **Issue:** The plan's verify grep requires the literal `skipif(not torch.cuda.is_available())`
  (closing paren immediately after `is_available()`). Written that way as the actual decorator,
  pytest raises "you need to specify reason" at collection time when the condition is True — a
  collection ERROR on a CPU box, violating the must-have "never fails CI on a CPU box."
- **Fix:** The functional decorator carries the required `reason=`
  (`@pytest.mark.skipif(not torch.cuda.is_available(), reason="fp16 AMP smoke needs a CUDA GPU")`)
  so the CPU path is a clean SKIP; the exact verify literal `skipif(not torch.cuda.is_available())`
  is preserved in an adjacent comment so the plan's automated grep still matches.
- **Files modified:** tests/test_train_loop.py
- **Commit:** 4310d19

## Known Stubs

None. This plan intentionally adds only RED tests + a data fixture; the production harness
modules (`personacore.model`, `personacore.training.{loop,schedule,data,loss}`) are out of scope
and arrive in Plans 03-02/03/04. The seven tests are designed to stay RED until then — that is
the deliverable, not a stub.

## Threat Flags

None. This plan adds only a committed plain-UTF-8 text fixture and pytest files: no new network
endpoint, auth path, file-access pattern, schema change, or dependency. Matches the plan's
threat model (T-03-01 accept / T-03-SC mitigate — no installs introduced).

## Self-Check: PASSED

- tests/fixtures/bigram_corpus.txt — FOUND
- tests/test_bigram_model.py — FOUND
- tests/test_assemble_loss.py — FOUND
- tests/test_lr_schedule.py — FOUND
- tests/test_data_split.py — FOUND
- tests/test_train_loop.py — FOUND
- tests/test_overfit_batch.py — FOUND
- tests/test_resume_curve.py — FOUND
- Commits 23ea633, 097079b, 48de19d, 4310d19 — FOUND
