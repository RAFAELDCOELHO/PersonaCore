---
phase: 03-bigram-baseline-training-harness
plan: 03
subsystem: training
tags: [data-loader, lr-schedule, no-leakage, lambdalr, tdd]
requires:
  - "artifacts/tokenizer.json (frozen Phase-2 BPE artifact)"
  - "personacore.tokenizer.from_json"
  - "personacore.config.TrainConfig / ModelConfig"
  - "personacore.checkpoint scheduler.state_dict() contract"
provides:
  - "personacore.training.data.load_split (doc-level no-leakage train/val split)"
  - "personacore.training.data.get_batch (nanoGPT contiguous-window sampler)"
  - "personacore.training.schedule.build_lr_lambda (warmup+cosine multiplier)"
  - "personacore.training.schedule.build_scheduler (resumable LambdaLR)"
affects:
  - "Plan 03-04 training loop (consumes get_batch + build_scheduler)"
tech-stack:
  added: []
  patterns:
    - "doc-level split on eos_id (never mid-document) for provable no-leakage"
    - "uint16 storage / int64 batch-time cast (nanoGPT memmap idiom, bounded fixture)"
    - "hand-rolled LR math wrapped in LambdaLR for state_dict() resumability (A1)"
key-files:
  created:
    - "src/personacore/training/data.py"
    - "src/personacore/training/schedule.py"
  modified: []
decisions:
  - "Trailing whitespace-only fragment after the final eos is NOT promoted to a document — it would make val a degenerate single-newline run that 'leaks' into train everywhere."
metrics:
  duration_min: 7
  tasks: 2
  files: 2
  completed: 2026-06-04
---

# Phase 3 Plan 3: Data Path + LR Schedule Summary

No-leakage doc-level train/val split + nanoGPT `get_batch` (TRAIN-03) and a hand-rolled
warmup+cosine LR wrapped in a resumable `LambdaLR` satisfying the `checkpoint.py`
`scheduler.state_dict()` contract (TRAIN-01) — turning the RED `test_data_split.py` and
`test_lr_schedule.py` GREEN.

## What Was Built

### Task 1 — `training/data.py` (TRAIN-03)
- `load_split(fixture_path, eos_id=8184, val_docs=1)`: loads the FROZEN tokenizer via
  `from_json("artifacts/tokenizer.json")` (never retrains — Pitfall 6), encodes the committed
  fixture with `allowed_special="all"` so `<|endoftext|>` maps atomically to id 8184, partitions
  the token stream into per-document lists on that boundary, and returns disjoint `np.uint16`
  train/val arrays. The last `val_docs` whole documents go to val; no document straddles the cut
  (no leakage, Pitfall 3).
- `get_batch(arr, batch_size, block_size, device)`: nanoGPT idiom — random contiguous windows
  bounded to `len(arr) - block_size - 1`, `y` shifted +1, cast `uint16 -> int64` for
  `nn.Embedding`/`cross_entropy`, moved to `device`.
- **Commit:** `308a440`

### Task 2 — `training/schedule.py` (TRAIN-01 schedule)
- `build_lr_lambda(warmup_steps, max_steps, min_ratio=0.1)`: linear warmup 0->1, cosine decay
  1->`min_ratio`, holding `min_ratio` as the floor at/after `max_steps`. Hand-written math.
- `build_scheduler(optimizer, train_cfg)`: wraps the lambda in a `torch.optim.lr_scheduler.LambdaLR`
  so `checkpoint.py`'s `scheduler.state_dict()` / `load_state_dict()` round-trip `last_epoch`
  (D-05/D-08). Advances per optimizer step, so LR(N) matches the lambda at N, not N*grad_accum
  (Pitfall 2).
- **Commit:** `afaf20d`

## TDD Gate Compliance

Both tasks were `tdd="true"`. The RED tests pre-existed (authored in Plan 03-01) and were
confirmed failing on import before implementation; each implementation turned its target test
file GREEN. No new test files were authored by this plan (the contracts were locked upstream),
and the test contracts were NOT weakened — real behavior was implemented to satisfy them.

- `tests/test_data_split.py`: 5/5 GREEN
- `tests/test_lr_schedule.py`: 4/4 GREEN

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Trailing-newline degenerate document caused a false leakage failure**
- **Found during:** Task 1 (first GREEN run of `test_split_has_no_document_leakage`).
- **Issue:** The fixture ends with a `\n` after the final `<|endoftext|>`. The plan's literal
  splitting logic (`if cur: docs.append(cur)`) promoted that trailing whitespace-only fragment
  to a 5th "document" of a single newline token (id 10). With `val_docs=1`, val became that bare
  newline, which appears verbatim throughout train — failing the no-leakage contract.
- **Fix:** Only append a trailing non-eos-terminated fragment when it carries real content
  (`tok.decode(cur).strip()`), so the file's final newline is not a document. This is the
  correct, contract-honoring behavior (the no-leakage property the test asserts), not a test
  weakening.
- **Files modified:** `src/personacore/training/data.py`
- **Commit:** `308a440`

**2. [Rule 3 - Blocking] Line-length lint fixes**
- Wrapped two lines >100 chars (assert message shortened; `get_batch` `y` stack split across
  lines) to pass `ruff check`. No behavior change.
- **Commit:** `308a440`

## Verification

- `pytest tests/test_data_split.py tests/test_lr_schedule.py -x -q` — 9 passed.
- Full suite (excluding the three Plan-04-owned RED loop tests
  `test_train_loop` / `test_overfit_batch` / `test_resume_curve`, which still import the
  not-yet-built `personacore.training.loop` — expected) — 70 passed.
- `ruff check` + `ruff format --check` clean on both new files.
- No train/val leakage: val document's 8-token window is provably absent from train.
- Scheduler `state_dict()["last_epoch"]` round-trips (7 -> 7) — satisfies `checkpoint.py`.

## Known Stubs

None. Both modules implement real behavior wired to the frozen tokenizer artifact and the
locked config fields.

## Self-Check: PASSED
- FOUND: src/personacore/training/data.py
- FOUND: src/personacore/training/schedule.py
- FOUND commit: 308a440
- FOUND commit: afaf20d
