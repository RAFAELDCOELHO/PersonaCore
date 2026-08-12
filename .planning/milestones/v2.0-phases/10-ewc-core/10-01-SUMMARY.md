---
phase: 10-ewc-core
plan: 01
subsystem: continual-learning
tags: [ewc, fisher, pytorch, autograd, numpy, spearman]

# Dependency graph
requires:
  - phase: 04-gpt (via v1.0)
    provides: GPT with LOCKED CE tail and tied wte/lm_head (named_parameters dedup)
  - phase: 05-training (via v1.0)
    provides: assemble_loss seam (D-04), get_batch_memmap window-draw idiom, _rng_state idiom
provides:
  - src/personacore/continual/ package — the from-scratch EWC core import surface
  - estimate_fisher(model, bin_path, *, n_examples, block_size, device, seed, normalize=True) -> (fisher, fisher_meta) — per-example empirical diagonal Fisher (D-03), mean-normalized (D-01/D-02), half-split convergence stats (D-05), RNG-pure (Pitfall 3)
  - EWCPenalty(fisher, theta_star, lam, device) callable (model) -> scalar tensor — Kirkpatrick quadratic form, exactly 0.0 at the anchor, fail-loud key/shape validation
affects: [10-02 loop penalty_fn splice, 10-03 fisher cache + smoke script, 12-lambda-sweep, 13-ab-eval]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-example Fisher: strict batch=1 torch.autograd.grad loop over named_parameters (never batched-gradient squaring)"
    - "RNG-pure side computation: local np.random.default_rng(seed), pinned draw pattern int(rng.integers(0, data_len - block_size - 1)) per example in order"
    - "fp64 statistics on CPU only (MPS has no fp64); fp32 accumulation on device"
    - "Hand-rolled ordinal Spearman: double argsort + np.corrcoef (scipy stays out)"
    - "Fail-loud ValueError naming offending keys at construction/call choke points (load_adapter style)"

key-files:
  created:
    - src/personacore/continual/__init__.py
    - src/personacore/continual/fisher.py
    - src/personacore/continual/ewc.py
    - tests/test_fisher.py
    - tests/test_ewc_penalty.py
  modified: []

key-decisions:
  - "fisher_meta records normalizer in BOTH normalize modes (raw mean always recoverable) — pinned by test_mean_normalization"
  - "Added n_examples >= 2 and corpus-length fail-loud guards beyond the plan's finiteness/mean guards (same Pitfall 7 posture)"
  - "EWCPenalty rejects an empty fisher dict at construction (a None total would crash opaquely at call time)"
  - "Requirements EWC-01/EWC-02 not checked off in REQUIREMENTS.md: their persistence (10-03) and loop-splice (10-02) halves land in wave 2"

patterns-established:
  - "continual/ package init mirrors lora/ shape: phase+requirement docstring, relative imports, sorted __all__"
  - "Window-draw contract documented in the estimate_fisher docstring so tests re-derive exact windows"

requirements-completed: [EWC-01, EWC-02]

# Metrics
duration: 16min
completed: 2026-06-12
---

# Phase 10 Plan 01: EWC Core (Fisher + Penalty) Summary

**Per-example empirical diagonal Fisher (`estimate_fisher`, batch=1 autograd loop, mean-normalized, RNG-pure) and the Kirkpatrick `EWCPenalty` quadratic anchor, both fully unit-pinned (17 new tests) in the new `continual/` package**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-06-12T10:31:32Z
- **Completed:** 2026-06-12T10:47:30Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 5 created

## Accomplishments

- `estimate_fisher` matches a brute-force per-example oracle (rtol=1e-6, atol=0) AND provably differs from the batched-gradient estimate on the same windows (relative L2 > 1e-2) — the implementation structurally cannot regress to the van de Ven bug (EWC-01, D-03)
- Stored Fisher is mean-normalized to global mean 1.0 within 1e-5 (fp64) with the raw normalizer recorded in `fisher_meta`; `normalized * normalizer` recovers the raw estimate bit-for-bit within fp32 round-trip tolerance (D-01/D-02)
- Tied wte/lm_head storage appears exactly once (`wte.weight` present, `lm_head.weight` absent; one entry per distinct `data_ptr`) — Pitfall 1 pinned
- `estimate_fisher` is RNG-pure: python/numpy/torch global RNG states bit-unchanged after the call (Pitfall 3); prior `model.training` flag restored conditionally
- `EWCPenalty` evaluates to exactly `0.0` (`==`, not allclose) at the anchor; gradient equals `lam * F * (theta - theta_star)`; lambda scales linearly; key/shape mismatches fail loudly naming the offending keys
- D-05 convergence machinery shipped: two disjoint half-accumulators, hand-rolled ordinal Spearman (no scipy), relative mean change of each half vs full — all reported in `fisher_meta`
- Full suite green: 203 passed, 4 skipped (pre-existing environment gates: gitignored real artifacts absent, no CUDA); `ruff check` + `ruff format --check` clean

## Task Commits

Each task was committed atomically (TDD: RED test commit, then GREEN feat commit):

1. **Task 1: estimate_fisher (RED)** - `eab2647` (test) — nine failing EWC-01 pins
2. **Task 1: estimate_fisher (GREEN)** - `1304dd7` (feat) — fisher.py + continual/__init__.py
3. **Task 2: EWCPenalty (RED)** - `a695cc6` (test) — eight failing EWC-02 pins
4. **Task 2: EWCPenalty (GREEN)** - `1689edb` (feat) — ewc.py + extended __init__.py

## Files Created/Modified

- `src/personacore/continual/__init__.py` - Package import surface; `__all__ = ["EWCPenalty", "estimate_fisher"]`
- `src/personacore/continual/fisher.py` - `estimate_fisher` per the LOCKED interface: strict batch=1 `torch.autograd.grad` loop, local `np.random.default_rng` draws, two half-accumulators, fp64-on-CPU stats, fail-loud guards (170 lines)
- `src/personacore/continual/ewc.py` - `EWCPenalty` callable: device-moved-once dicts, construction/call validation, `(lam/2) * sum(F * d * d)` (71 lines)
- `tests/test_fisher.py` - Nine EWC-01 pins: oracle, anti-batched discriminator, non-negativity, determinism, normalization, dedup, RNG purity, mode restore, meta contract (219 lines)
- `tests/test_ewc_penalty.py` - Eight EWC-02 pins: hand-computed quadratic oracle (1.925 literal), exact-zero anchor, lambda linearity, analytic gradient, three fail-loud validations, assemble_loss seam integration (134 lines)

## Decisions Made

- `fisher_meta["normalizer"]` records the raw global mean in both `normalize=True` and `normalize=False` modes, so the raw estimate is always recoverable and the two modes are cross-checkable from meta alone
- λ linearity asserted via `pytest.approx(rel=1e-7)` per the plan's stated tolerance (powers of two scale exactly in fp32, so this is conservative)
- REQUIREMENTS.md left untouched: EWC-01's checkpoint-persistence half is plan 10-03's and EWC-02's `assemble_loss` loop-splice half is plan 10-02's (both wave 2); checking the boxes now would claim un-built behavior. The `requirements-completed` frontmatter above follows the template contract (copied from the plan's `requirements` field) — the orchestrator/verifier reconciles at phase level.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added input-validation guards to estimate_fisher and EWCPenalty**
- **Found during:** Task 1 / Task 2 implementation
- **Issue:** `n_examples < 2` would divide by zero in the D-05 half-split; a corpus shorter than `block_size + 2` would surface a bare numpy error from the draw; an empty fisher dict would make `EWCPenalty.__call__` return `(lam/2) * None`
- **Fix:** Three fail-loud `ValueError`s naming the failure, matching the plan's existing Pitfall 7 guard posture
- **Files modified:** src/personacore/continual/fisher.py, src/personacore/continual/ewc.py
- **Verification:** Full suite green; guards are unreachable in all planned call paths
- **Committed in:** `1304dd7`, `1689edb` (part of task commits)

---

**Total deviations:** 1 auto-fixed (Rule 2 — fail-loud correctness guards)
**Impact on plan:** Defensive-only additions in the plan's own error-handling style. No scope creep, no interface change.

## Issues Encountered

None — `ruff format` reflowed one long line in fisher.py before the GREEN commit (routine lint compliance, not a problem).

## Known Stubs

None — no placeholders, hardcoded empty values, or unwired data paths. Both deliverables are complete implementations consumed by wave-2 plans.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The LOCKED interfaces plans 10-02/10-03 build against are shipped verbatim: `estimate_fisher(...) -> (fisher, fisher_meta)` with the exact 11-key meta set, and `EWCPenalty.__init__/__call__`
- `penalty_fn` splice (10-02) can construct `EWCPenalty` and pass it straight to `assemble_loss` — the seam-integration test already proves the contract
- Fisher cache exporter/loader (10-03) gets `weights_only=True`-safe inputs: fisher is `{str: fp32 CPU tensor}`, meta is primitives only

## Self-Check: PASSED

- All 5 created files exist on disk
- All 4 task commits present in git log (eab2647, 1304dd7, a695cc6, 1689edb)
- `pytest -q`: 203 passed, 4 skipped; `ruff check .` + `ruff format --check .` clean
- Both symbols import from `personacore.continual`

---
*Phase: 10-ewc-core*
*Completed: 2026-06-12*
