---
phase: 09-lora-core
plan: 01
subsystem: lora
tags: [pytorch, lora, adapters, from-scratch, peft-free]

# Dependency graph
requires:
  - phase: 04-gpt-architecture
    provides: GPT with six named nn.Linear projections per block (q/k/v/c_proj, fc_in/fc_out) and the tied lm_head/wte tensor
provides:
  - LoRAConfig dataclass (r=8, alpha=16.0, dropout=0.0) + TARGET_PROJECTIONS canonical allowlist
  - LoRALinear composition wrapper (A-Gaussian std 0.02, B-zero identity gate, scale=alpha/r single source, flag-gated delta branch)
  - inject_lora / mark_only_lora_trainable / snapshot_params / lora_state_dict / load_adapter_weights
  - 17 CPU-only unit tests pinning identity, allowlist, tied-tensor safety, census formula, key audit
affects: [09-02 toggle/eject, 09-03 merge/artifact, 09-04 training smoke, phase-14 persona adapters]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Composition wrapper (LoRALinear owns frozen base nn.Linear; never inheritance/parametrize)"
    - "Explicit allowlist injection over cfg.targets — never isinstance scans (tied-head safety)"
    - "Key-audited strict=False: exact key-set ValueError audit before any load_state_dict"
    - "Plain-bool runtime flags (enabled/merged) kept out of state_dict by construction"

key-files:
  created:
    - src/personacore/lora/__init__.py
    - src/personacore/lora/config.py
    - src/personacore/lora/layer.py
    - src/personacore/lora/inject.py
    - tests/test_lora_layer.py
    - tests/test_lora_inject.py
  modified: []

key-decisions:
  - "Allowlist cross-pin restates the PROJECTIONS literal in tests/test_lora_inject.py (plan-sanctioned) instead of importing from tests/ — keeps test files import-independent"
  - "lora_B nudged via nn.init.normal_ in tests to make deltas/applies observable without training"
  - "merged guard ships now in forward (D-05) even though merge() lands in 09-03 — flag is part of the forward contract"

patterns-established:
  - "TARGET_PROJECTIONS is the single canonical allowlist; 09-02/03/04 import it, never restate it in src/"
  - "scale = alpha / r appears exactly once (layer.py __init__); merge in 09-03 must read self.scale"
  - "inject.py never imports checkpoint.py (locked dependency direction for 09-03)"

requirements-completed: [LORA-01, LORA-02, LORA-05]

# Metrics
duration: 10min
completed: 2026-06-11
---

# Phase 9 Plan 01: LoRA Core Summary

**From-scratch LoRALinear composition wrapper + post-load allowlist injection with B=0 bit-identity, tied-embedding safety, and the r*n_layer*18*n_embd trainable census — all pinned by 17 CPU-only tests**

## Performance

- **Duration:** 10 min
- **Started:** 2026-06-11T21:24:33Z
- **Completed:** 2026-06-11T21:34:24Z
- **Tasks:** 2 (both TDD: RED -> GREEN)
- **Files modified:** 6 created, 0 existing modified

## Accomplishments

- `LoRALinear` wraps any `nn.Linear` with bit-identical output at init (`torch.equal`, the B=0 identity gate) — the highest-value correctness property of the phase
- `inject_lora` wraps exactly `6 * n_layer` projections via the explicit `TARGET_PROJECTIONS` allowlist; `lm_head`/`wte` are never touched and their tied `data_ptr` survives injection
- `mark_only_lora_trainable` produces the closed-form trainable census `r * n_layer * 18 * n_embd` with only `lora_` params trainable
- `load_adapter_weights` raises `ValueError` on any key-set mismatch before loading a single tensor (no bare `strict=False`)
- Full existing suite stays green (152 passed, 3 pre-existing skips); zero edits to `model/gpt.py`, `training/loop.py`, or `checkpoint.py`

## Task Commits

Each task was committed atomically (TDD: test commit then feat commit):

1. **Task 1: LoRAConfig + LoRALinear wrapper + layer-level tests**
   - `e0ec561` (test) — failing tests for the wrapper (8 tests)
   - `9ef1345` (feat) — LoRAConfig, TARGET_PROJECTIONS, LoRALinear
2. **Task 2: Post-load injection, freeze, key-audited adapter apply + injection tests**
   - `435abb8` (test) — failing tests for injection machinery (9 tests)
   - `bc63bac` (feat) — inject.py five functions + extended `__all__`

_No refactor commits — implementations landed clean against the RESEARCH-verified reference._

## Files Created/Modified

- `src/personacore/lora/config.py` — LoRAConfig dataclass + TARGET_PROJECTIONS canonical allowlist
- `src/personacore/lora/layer.py` — LoRALinear composition wrapper (identity gate, scale single source, flag-gated branch)
- `src/personacore/lora/inject.py` — inject_lora, mark_only_lora_trainable, snapshot_params, lora_state_dict, load_adapter_weights
- `src/personacore/lora/__init__.py` — public import surface (8 exports)
- `tests/test_lora_layer.py` — 8 layer-level pins (identity, scale, init, contiguity, dropout, state-dict hygiene, delta-fires, config defaults)
- `tests/test_lora_inject.py` — 9 injection pins (wrap count, cross-pin, tied data_ptr, ordering, census, filter, key-audited apply x2, snapshot)

## Decisions Made

- Restated the `PROJECTIONS` literal in `tests/test_lora_inject.py` for the allowlist cross-pin rather than importing from `tests/test_gpt_lora_seam` (plan offers both; restating avoids inter-test-module import coupling — the literal is additionally pinned against `TARGET_PROJECTIONS` so drift in either side fails the test)
- Added an 8th layer test pinning `LoRAConfig` defaults (r=8/alpha=16.0/dropout=0.0/targets) — cheap insurance on the ~1.3 MB persona-file story; plan acceptance required >= 7
- Corrupted-dict audit split into its own test (9 inject tests vs the 8 specified) so the "no weight loaded after failed audit" assertion is isolated

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. One ruff I001 ordering fix in `lora/__init__.py` during Task 1 lint (constants sort before classes in ruff's isort) — fixed before commit, not a deviation.

## Known Stubs

None — no placeholder values, TODO/FIXME markers, or unwired data paths in any created file. The `merged` flag is intentionally forward-declared per D-05 (the `merge()` utility lands in plan 09-03 by design, with the guard already test-pinned here).

## Threat Model Compliance

| Threat | Disposition | Implemented |
|--------|-------------|-------------|
| T-09-01 (target selection tampering) | mitigate | TARGET_PROJECTIONS allowlist + post-injection data_ptr test (test_tied_tensor_never_wrapped) |
| T-09-02 (adapter-load tampering) | mitigate | exact key-set ValueError audit before load (test_load_adapter_weights_raises_before_loading) |
| T-09-03 (base-weight disclosure) | mitigate | lora_state_dict filter test pins no .base. keys leak (test_lora_state_dict_filter) |

No new security surface introduced beyond the plan's threat model.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `LoRALinear` forward contract (incl. the `merged` guard) and `self.scale` single source are ready for plan 09-02 (toggle/eject) and 09-03 (merge/unmerge/artifact)
- `snapshot_params` canary helper ready for reuse by 09-04's training tests and smoke script
- `lora_state_dict`/`load_adapter_weights` form the adapter-dict seam 09-03's `export_adapter`/`load_adapter` will consume
- No blockers

## Self-Check: PASSED

- All 6 created files exist on disk
- All 4 task commits present in git log (e0ec561, 9ef1345, 435abb8, bc63bac)
- Plan verification re-run: 17/17 new tests green, `make test` 152 passed / 3 skipped, `make lint` clean, full import surface verified in `.venv`

---
*Phase: 09-lora-core*
*Completed: 2026-06-11*
