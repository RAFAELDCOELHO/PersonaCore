---
phase: 12-stage-2-conversational-fine-tune
plan: 02
subsystem: evaluation, generation
tags: [pytorch, perplexity, loss-masking, generation, stop-tokens, tdd]

# Dependency graph
requires:
  - phase: 11-dialogue-data-pipeline
    provides: get_batch_memmap_masked mask semantics (uint8 1:1 bins, shifted target-space slice, loud mismatch raise)
  - phase: 07-evaluation
    provides: perplexity() non-overlapping-window sum-CE sweep + retention_perplexity() frozen-policy register
  - phase: 06-generation
    provides: generate()/collect() core with EOS stop-without-yield (D-05)
provides:
  - masked_perplexity(model, bin_path, mask_path, block_size, device, forbid_ids=None) — THE frozen dialogue-val gate metric for all Phase 12 arms
  - generate(stop_ids=None) — additive multi-id stop set; default bit-identical to v1.0 single-EOS
affects: [12-03, 12-04, 12-05, 13-forgetting-curves]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Frozen eval policy: one deterministic gate metric fixed independently of the training arm (Pitfall 3 incommensurability)"
    - "stop-set replacement semantics: stops = stop_ids if stop_ids is not None else {eid} — EOS is only a stop when a member"

key-files:
  created:
    - tests/test_masked_perplexity.py
    - tests/test_stop_ids.py
  modified:
    - src/personacore/evaluation/perplexity.py
    - src/personacore/evaluation/__init__.py
    - src/personacore/generation/core.py

key-decisions:
  - "masked_perplexity oracle hand-counts K=7 scored targets on a 13-token/block_size=4 fixture — denominator proven, not derived from the implementation (T-12-04)"
  - "Masking-selectivity test uses a non-uniform fixed-logits stub — under uniform logits every target costs ln(V), so target swaps would never change the sum even unmasked"
  - "stop_ids REPLACES the EOS stop (does not extend it); pinned by an EOS-yielded-when-not-member test"

patterns-established:
  - "Gate-metric register: masked_perplexity mirrors perplexity()'s end=min(i+block_size+1,n) sweep + re-open-memmap-per-call, adds shifted mask slice mask[i+1:end] and ignore_index=-100"

requirements-completed: [TUNE-01]

# Metrics
duration: 8min
completed: 2026-08-01
---

# Phase 12 Plan 02: Gate Metric + Stop Machinery Summary

**Oracle-proven masked dialogue-val PPL (exact hand-counted denominator, loud mismatch/zero-scored raises) plus the additive stop_ids kwarg on generate() with pinned v1.0 default equivalence — the two code seams outside the training loop, both TDD-committed, full suite 274 green**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-08-01T04:19:17Z
- **Completed:** 2026-08-01T04:27:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- `masked_perplexity()` ships in `src/personacore/evaluation/perplexity.py`: mirrors `perplexity()`'s non-overlapping-window sum-CE sweep exactly (same shifted slicing, memmap re-open, `model.eval()`), adds the uint8 mask memmap sliced SHIFTED with targets, `ignore_index=-100`, and an exact auditable `total_tokens` denominator
- Hand-fixture oracle: uniform-logits stub → ppl == 16.0 exactly, denominator == hand-counted K=7; masking selectivity proven with a non-uniform fixed-logits model (mask==0 target mutations change nothing); ValueError on length mismatch (naming both lengths, data.py register) and on zero scored targets; forbid_ids renormalization pinned (16 → 12 with 4 never-target ids forbidden)
- Frozen-policy docstring in the retention_perplexity register: this is THE gate metric for every D-01/D-02/D-05 smoke arm; `estimate_loss`'s 20-random-batch mean is explicitly disallowed for gates
- `generate(stop_ids=None)`: the entire change is `stops = stop_ids if stop_ids is not None else {eid}` + `if tok in stops:` — stop-without-yield (D-05) unchanged, `collect()` untouched (`**kw` pass-through)
- Default equivalence pinned (identical asserts to `test_eos_stop`); EOS-not-implicitly-included pinned (EOS is yielded when not a member of a custom set)
- Full suite: 274 passed, 1 skipped (CUDA-only AMP smoke); `perplexity()`/`retention_perplexity()` byte-untouched

## Task Commits

Each task was committed atomically (TDD: test → feat):

1. **Task 1: masked_perplexity** — `959073a` (test, RED) → `ee417a0` (feat, GREEN)
2. **Task 2: stop_ids kwarg** — `ef2ae04` (test, RED) → `e6de6f2` (feat, GREEN)

## Files Created/Modified

- `src/personacore/evaluation/perplexity.py` — masked_perplexity() added; existing functions untouched
- `src/personacore/evaluation/__init__.py` — barrel export (consistent with perplexity/retention_perplexity)
- `src/personacore/generation/core.py` — stop_ids kwarg, membership stop check, docstring
- `tests/test_masked_perplexity.py` — 5 tests: oracle, selectivity, mismatch raise, zero-scored raise, forbid_ids
- `tests/test_stop_ids.py` — 4 tests: default equivalence, custom stop, multi-id set, EOS-not-implicit

## Decisions Made

- Exported `masked_perplexity` through the evaluation barrel — matches the existing `perplexity`/`retention_perplexity` import surface that tests and future plans consume
- Test 2 (masking selectivity) uses a fixed non-uniform logits stub instead of the uniform one, because uniform logits make every target equi-cost and the test would be vacuous

## Deviations from Plan

None - plan executed exactly as written. (The barrel export is a one-line consistency addition within the plan's artifact file set.)

## Issues Encountered

None. In Task 2's RED run the default-equivalence test passed pre-change by construction — it exercises existing v1.0 behavior as the baseline; the three feature tests failed with TypeError as expected.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 12-03..12-05 can call `masked_perplexity` for every smoke-arm gate number and thread it through `extra_eval_fns` (12-01 seam)
- Transcript generation can pass `stop_ids={8184, 8185}` (eos + `<|user|>`) to halt on hallucinated user turns

## Self-Check: PASSED

- src/personacore/evaluation/perplexity.py `def masked_perplexity`: FOUND
- src/personacore/generation/core.py `stop_ids`: FOUND
- tests/test_masked_perplexity.py: FOUND (5 tests)
- tests/test_stop_ids.py: FOUND (4 tests)
- Commits 959073a, ee417a0, ef2ae04, e6de6f2: FOUND

---
*Phase: 12-stage-2-conversational-fine-tune*
*Completed: 2026-08-01*
