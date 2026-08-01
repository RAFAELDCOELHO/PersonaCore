---
phase: 12-stage-2-conversational-fine-tune
plan: 01
subsystem: training
tags: [pytorch, training-loop, loss-masking, csv-telemetry, tdd]

# Dependency graph
requires:
  - phase: 11-dialogue-data-pipeline
    provides: get_batch_memmap_masked (target-space -100 mask semantics, data.py)
  - phase: 10-ewc-continual-learning
    provides: penalty_fn additive-seam precedent + golden_trajectory_v1.json protection fixture
provides:
  - train(train_mask_bin=, val_mask_bin=) — masked memmap batch/val routing (assistant-token CE)
  - train(extra_eval_fns={key: fn}) — one CSV column per key per eval interval
  - estimate_loss(mask_bin=) — masked val draws inside the untouched RNG snapshot
  - "Pinned fact for Plan 12-04: the v1.0 eval block does NOT log a step-0 row"
affects: [12-02, 12-03, 12-04, 12-05, 13-forgetting-curves]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - additive default-None loop kwargs with bit-identical v1.0 defaults (penalty_fn register)
    - per-run CSV fieldnames CSV_FIELDNAMES + sorted(extra_eval_fns); module constant never mutated
    - extras block wrapped in _rng_state/_restore_rng + model.train() restore (Pitfall 4)

key-files:
  created:
    - tests/test_masked_train_seam.py
    - tests/test_extra_eval_fns.py
  modified:
    - src/personacore/training/loop.py

key-decisions:
  - "val_mask_bin SHIPS (USER LOCK 3): in-loop val_loss gates best.pt selection, which is selected FOR assistant-token dialogue capability — justification recorded in the loop docstring"
  - "mask_bin kwarg only passed to estimate_loss when set, so v1.0 call-site signature stays byte-identical and estimate_loss stubs keep working"

patterns-established:
  - "Mask seam: memmap batch_fn conditionally routes via get_batch_memmap_masked; -100 targets flow through the LOCKED forward(idx, targets) contract untouched"
  - "Telemetry seam: extra fns run once per eval-logging event inside an RNG snapshot; DictWriter unknown-key raise guards old CSV files (T-12-02)"

requirements-completed: [DEBT-01, DEBT-02, TUNE-01, TUNE-02]

# Metrics
duration: 14min
completed: 2026-08-01
---

# Phase 12 Plan 01: Loop Seams Summary

**Masked-batch routing (train_mask_bin/val_mask_bin) and per-interval extra CSV columns (extra_eval_fns) added to train() as default-None kwargs, proven bit-identical to v1.0 by the golden-trajectory replay running (not skipping) on this machine**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-08-01T04:03:27Z
- **Completed:** 2026-08-01T04:17:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- `train(train_bin=..., train_mask_bin=...)` draws batches via `get_batch_memmap_masked`; -100 sentinels verified reaching targets on every drawn batch; ValueError guard on mask-without-bin
- `train(val_bin=..., val_mask_bin=...)` makes the in-loop val_loss (best.pt gate) measure assistant-token masked CE — USER LOCK 3 justification recorded in the `val_mask_bin` docstring
- `train(extra_eval_fns={...})` appends one CSV column per sorted key per eval event; extras run inside an RNG snapshot and `model.train()` is restored afterward (Pitfall 4)
- All three kwargs default None and reproduce v1.0 **bit-for-bit** — the platform-gated golden replay actually RAN on this machine (the suite's single skip is the CUDA-only AMP smoke) and passed, plus the in-process identity tests
- DEBT-01/DEBT-02 confirmed closed by their pins (`test_run_csv_tokens.py`, `test_retention_ppl.py`); commit `ca14a89` resolves; zero re-implementation
- Full suite: 265 passed, 1 skipped (CUDA-only); golden fixture byte-untouched

## Key Fact for Plan 12-04

**The v1.0 eval block does NOT log a step-0 row.** The block runs AFTER `step += 1`, so with `eval_interval=1, max_steps=5` the CSV rows are steps 1..5. A step-0 retention baseline must be measured OUTSIDE `train()` before the call. (Pinned as a comment + exact-count assertion in `tests/test_extra_eval_fns.py::test_called_once_per_eval_logging_event`.)

## Task Commits

Each task was committed atomically (TDD tasks: test → feat):

1. **Task 1: mask seam** — `2048897` (test, RED) → `c6c1c2b` (feat, GREEN)
2. **Task 2: extra_eval_fns seam** — `f1e3b62` (test, RED) → `099c172` (feat, GREEN)
3. **Task 3: purity confirmation** — `c2a1133` (fix, seam repair found by the full-suite gate)

## Files Created/Modified

- `src/personacore/training/loop.py` — three additive kwargs + masked routing + extras block
- `tests/test_masked_train_seam.py` — routing, guard, val routing + RNG snapshot, identity (5 tests)
- `tests/test_extra_eval_fns.py` — sorted columns, call count, train-mode restore, RNG hygiene, identity (5 tests)

## Decisions Made

- `mask_bin` is only passed to `estimate_loss` when `val_mask_bin` is set, keeping the v1.0 call site byte-identical on the default path (see Deviations)
- Extras execute in `sorted(extra_eval_fns)` key order — matches the sorted fieldnames, deterministic across runs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] estimate_loss call-site broke a stubbing test**
- **Found during:** Task 3 (full-suite gate)
- **Issue:** Task 1 passed `mask_bin=val_mask_bin` unconditionally; `tests/test_best_ckpt.py` monkeypatches `estimate_loss` with a fake lacking the kwarg → TypeError
- **Fix:** Pass `mask_bin=` only when `val_mask_bin is not None`; default path call is v1.0-identical
- **Files modified:** src/personacore/training/loop.py
- **Verification:** Full suite 265 passed
- **Committed in:** `c2a1133`

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Strengthens the additive-seam contract (identical call site, not just identical signature). No scope creep.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three seams live and test-pinned; Plans 12-02..12-05 can consume `train_mask_bin`/`val_mask_bin`/`extra_eval_fns` directly
- Plan 12-04 must measure its step-0 retention baseline outside `train()` (no step-0 CSV row — see Key Fact)

## Self-Check: PASSED

- tests/test_masked_train_seam.py: FOUND
- tests/test_extra_eval_fns.py: FOUND
- Commits 2048897, c6c1c2b, f1e3b62, 099c172, c2a1133: FOUND
- tests/fixtures/ clean: CONFIRMED

---
*Phase: 12-stage-2-conversational-fine-tune*
*Completed: 2026-08-01*
