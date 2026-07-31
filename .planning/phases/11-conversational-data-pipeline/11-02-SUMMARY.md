---
phase: 11-conversational-data-pipeline
plan: 02
subsystem: training-data
tags: [loss-masking, memmap, dialogue, tdd]
requires: []
provides:
  - "get_batch_memmap_masked(bin_path, mask_path, batch_size, block_size, device) in personacore.training.data"
affects: [12-conversational-fine-tune]
tech-stack:
  added: []
  patterns:
    - "loss masking entirely in the data path via ignore_index=-100 sentinel (LOCKED forward() untouched)"
    - "shared +1 slice for y and mask = target-space shift (D-01)"
key-files:
  created:
    - tests/test_masked_batch.py
  modified:
    - src/personacore/training/data.py
decisions:
  - "Alignment invariant is an explicit `if ... raise ValueError` (T-11-04), never a -O-strippable assert"
  - "Expected y tensor hand-written in the test, never derived from the mask (Pitfall 14 guard)"
metrics:
  duration: "~5 min"
  completed: "2026-07-31"
---

# Phase 11 Plan 02: Masked Batch Sampler Summary

Additive `get_batch_memmap_masked` draws aligned windows from uint16 token + uint8 mask bins and sets y to -100 wherever the +1-shifted mask is 0, pinned by a hand-built DATA-03 exactness fixture.

## What Was Built

- `get_batch_memmap_masked` in `src/personacore/training/data.py`, directly below `get_batch_memmap` (which is byte-identical — diff is 36 insertions, 0 deletions):
  - Fresh `np.memmap` per call for BOTH bins (Pitfall 1 RSS-leak avoidance)
  - Explicit `ValueError` on token/mask length mismatch (T-11-04 mitigation, tested)
  - `y` and `m` share the `i + 1 : i + 1 + block_size` slice — the shared slice IS the target-space shift (D-01)
  - `y[m == 0] = -100`, consumed by `F.cross_entropy`'s default `ignore_index` with zero model changes
- `tests/test_masked_batch.py` — DATA-03 hand-built exactness fixture:
  - 14 hand-written token literals with real special ids (8184–8187); `len - block_size - 1 == 1` makes the draw deterministic (ix=0)
  - Expected final y tensor hand-written (7 × `-100`), asserted via `torch.equal` — never computed from the mask in-test
  - The three edge tokens pinned individually: first-`<|user|>` prediction masked (-100), second-`<|user|>` prediction kept (8185), eos prediction kept (8184)
  - Shape/dtype assertions `(1, 12)` / `torch.int64`; length-mismatch `pytest.raises(ValueError)`

## Task Commits

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 (RED) | DATA-03 hand-built exactness fixture | 4c9678b |
| 1 (GREEN) | get_batch_memmap_masked implementation | e3f3b72 |

No REFACTOR commit — implementation matched the house idiom verbatim on first pass.

## Verification

- `pytest tests/test_masked_batch.py -x -q` — 3 passed
- Full suite — 222 passed, 4 skipped (all skips environmental: gitignored slim-artifact files absent in worktree ×3, CUDA-only fp16 smoke ×1 — identical posture to baseline)
- `ruff check .` + `ruff format --check .` — clean
- `git diff src/personacore/training/data.py` — only the additive function

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

RED commit 4c9678b (test failed on import) → GREEN commit e3f3b72 (3 passed). Gate sequence satisfied.

## Known Stubs

None.

## Threat Flags

None — no new trust boundaries; the T-11-04 mitigation (length-equality raise) is implemented and tested.

## Self-Check: PASSED

- tests/test_masked_batch.py — FOUND
- src/personacore/training/data.py contains `def get_batch_memmap_masked(` and `y[m == 0] = -100` — FOUND
- Commits 4c9678b, e3f3b72 — FOUND
