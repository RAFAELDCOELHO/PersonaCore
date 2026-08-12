---
phase: 09-lora-core
plan: 02
subsystem: lora
tags: [pytorch, lora, adapters, toggle, merge, contextmanager]

# Dependency graph
requires:
  - phase: 09-lora-core (plan 01)
    provides: LoRALinear wrapper (enabled/merged flags, scale single source), inject_lora, TARGET_PROJECTIONS allowlist
provides:
  - set_adapter_enabled model-level toggle (bit-exact round-trip to base, LORA-05)
  - adapter_disabled exception-safe context manager with per-module prior-state restore (D-06)
  - eject_adapter full wrapper removal — vanilla keys/logits, refuses while merged (D-05)
  - LoRALinear.merge()/unmerge() — in-place fold + bit-exact stored-clone restore (D-07)
  - merge_lora/unmerge_lora model-level utilities with training-mode guard (Pitfall 6)
  - merged_state_dict pure fold with vanilla-GPT key parity (D-08, Phase-15 ΔW building block)
  - 13 CPU-only tests pinning toggle round-trip, CM safety, eject, merge equivalence, purity
affects: [09-03 adapter artifact, 09-04 training smoke, phase-14 live demo toggle, phase-15 delta-w heatmaps]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "First contextlib.contextmanager use: capture prior per-module state, try/yield/finally restore"
    - "Stored-clone bit-exact restore: _w0 plain attr + copy_ (never float subtraction)"
    - "Eval-time-only merge: assert model.training is False before any in-place fold"
    - "Pure fold dicts: out-of-place compute + detached clones, zero live-model mutation"

key-files:
  created:
    - tests/test_lora_toggle.py
    - tests/test_lora_merge.py
  modified:
    - src/personacore/lora/layer.py
    - src/personacore/lora/inject.py
    - src/personacore/lora/__init__.py

key-decisions:
  - "merged_state_dict additionally asserts no module is merged before folding — the plan spec omitted this guard but folding an already-merged base would silently double-count the delta (T-09-04 mitigate disposition)"
  - "eject_adapter walks TARGET_PROJECTIONS (canonical constant) rather than taking a LoRAConfig — eject needs no config, mirroring inject_lora's parent-walk shape"

patterns-established:
  - "adapter_disabled restores PRIOR per-module values, never blanket True — pre-disabled modules stay disabled"
  - "merge() reads self.scale (the 09-01 single source); alpha/r still computed exactly once in layer.py"

requirements-completed: [LORA-04, LORA-05]

# Metrics
duration: 14min
completed: 2026-06-11
---

# Phase 9 Plan 02: LoRA Toggle, Eject, and Merge Summary

**Model-level adapter on/off with torch.equal round-trip, exception-safe adapter_disabled CM, eject_adapter vanilla restore, and merge/unmerge with bit-exact stored-clone unmerge plus pure merged_state_dict — 13 new CPU-only tests, full suite green**

## Performance

- **Duration:** 14 min
- **Started:** 2026-06-11T21:40:42Z
- **Completed:** 2026-06-11T21:55:00Z
- **Tasks:** 2 (both TDD: RED -> GREEN)
- **Files modified:** 2 created, 3 modified

## Accomplishments

- `set_adapter_enabled(model, False)` returns logits `torch.equal` to the pre-injection base; re-enabling restores the adapter logits exactly (ROADMAP criterion 1 — the Phase-14 live memory-on/off switch)
- `adapter_disabled` is the codebase's first `contextlib.contextmanager`: captures prior per-module `enabled` values, restores them in `finally` — exception-safe (D-06) and prior-state-preserving (a pre-disabled module stays disabled)
- `eject_adapter` returns every wrapped projection to a plain `nn.Linear` with vanilla-GPT state-dict key parity and `torch.equal`-to-base logits; asserts unmerged first (Pitfall 6)
- `merge_lora`/`unmerge_lora` pass the fp32 equivalence bar (`atol=1e-5` CPU, ROADMAP criterion 4) with bit-exact (`torch.equal`) base-weight restore via the stored `_w0` clone (D-07); merge refuses in train mode so checkpoints can never be saved merged
- `merged_state_dict` is a pure fold: zero live-model mutation, vanilla key set, `strict=True` reload reproduces live logits within 1e-5 (D-08 — Phase 15's ΔW building block; merged-slim export deliberately NOT wired per CONTEXT Deferred Ideas)
- Full suite stays green (165 passed, 3 pre-existing skips); zero edits to `model/gpt.py` or `checkpoint.py`

## Task Commits

Each task was committed atomically (TDD: test commit then feat commit):

1. **Task 1: Model-level toggle, adapter_disabled CM, eject_adapter + toggle tests**
   - `4f47777` (test) — 6 failing toggle/CM/eject pins
   - `c21126c` (feat) — set_adapter_enabled, adapter_disabled, eject_adapter + `__all__`
2. **Task 2: merge()/unmerge() + merge_lora/unmerge_lora/merged_state_dict + merge tests**
   - `8f2bd2e` (test) — 7 failing merge/unmerge/purity pins
   - `be68af1` (feat) — LoRALinear.merge/unmerge, three model-level utilities + `__all__`

_No refactor commits — implementations landed clean against the RESEARCH-verified reference._

## TDD Gate Compliance

Both gates satisfied per task: each `test(...)` commit precedes its `feat(...)` commit; RED runs failed with `ImportError` (functions absent), GREEN runs passed 6/6 and 7/7 respectively.

## Files Created/Modified

- `tests/test_lora_toggle.py` — 6 pins: toggle round-trip bit-identity, CM scope, CM exception safety, per-module prior-state restore, eject vanilla restore (keys + logits), eject-merged refusal
- `tests/test_lora_merge.py` — 7 pins: merged forward equivalence (1e-5), bit-exact unmerge, double-merge/bare-unmerge guards, training-mode refusal, eject interplay, merged_state_dict purity + parity + strict reload, `_w0` hygiene
- `src/personacore/lora/layer.py` — added `merge()`/`unmerge()` under `@torch.no_grad()`; `alpha / r` still appears exactly once (merge reads `self.scale`, PITFALLS P3)
- `src/personacore/lora/inject.py` — added `set_adapter_enabled`, `adapter_disabled`, `eject_adapter`, `merge_lora`, `unmerge_lora`, `merged_state_dict`
- `src/personacore/lora/__init__.py` — `__all__` extended to 14 exports

## Decisions Made

- Added a defensive `assert not m.merged` to `merged_state_dict` (see Deviations) — folding an already-merged base would silently double-count the delta
- `eject_adapter` iterates the canonical `TARGET_PROJECTIONS` constant directly (it takes no config); same parent-walk shape as `inject_lora`
- Updated the stale "Plan-03 merge later" phrase in `layer.py`'s docstring since the merge ships in this plan (doc accuracy only, no behavior change)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Guard merged_state_dict against an already-merged model**
- **Found during:** Task 2 (merged_state_dict implementation)
- **Issue:** The plan's fold spec computes `base.weight + scale * (B @ A)`; called on a merged model this silently double-counts the delta — exactly the T-09-04 trust-boundary corruption the threat model assigns a mitigate disposition
- **Fix:** `assert not m.merged` per wrapped module before folding, with a message naming the remedy ("unmerge first")
- **Files modified:** src/personacore/lora/inject.py
- **Verification:** All 7 merge tests green (the purity test calls the fold on an unmerged model as specified); full suite green
- **Committed in:** be68af1 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** One-line correctness guard aligned with the plan's own threat register (T-09-04). No scope creep.

## Issues Encountered

None. One `ruff format` line-wrap fix in `inject.py` during Task 2 lint — fixed before commit, not a deviation. The full suite's single warning (`tests/test_tokenizer_io.py` corpus-exhaustion UserWarning) is pre-existing and intentional fixture behavior, unrelated to this plan.

## Known Stubs

None — no placeholder values, TODO/FIXME markers, or unwired data paths. The merged-slim export hook is intentionally NOT wired (deferred per CONTEXT Deferred Ideas); `merged_state_dict` ships as the building block only.

## Threat Model Compliance

| Threat | Disposition | Implemented |
|--------|-------------|-------------|
| T-09-04 (merge/checkpoint tampering) | mitigate | `merge_lora` asserts `model.training is False`; double-merge asserts per module; `not self.merged` forward gate exercised end-to-end (test_merged_forward_matches_live); extra fold guard in merged_state_dict |
| T-09-05 (eject contamination) | mitigate | `assert not child.merged` before restoring base modules; post-eject `torch.equal`-to-base pins (test_eject_restores_vanilla_model, test_eject_after_unmerge_interplay) |
| T-09-06 (unmerge drift) | mitigate | stored-clone `copy_` restore pinned bit-exact by `torch.equal` (test_unmerge_bit_exact) |
| T-09-SC (supply chain) | accept | zero packages installed this plan |

No new security surface introduced beyond the plan's threat model.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `set_adapter_enabled`/`adapter_disabled`/`eject_adapter` ready for Phase 14's live memory-on/off demo
- `merged_state_dict()` ready as Phase 15's ΔW heatmap building block
- The never-checkpoint-while-merged guard and bit-exact unmerge protect the bit-identity culture for 09-03's artifact work and 09-04's training smoke
- No blockers

## Self-Check: PASSED

- All 5 created/modified files exist on disk
- All 4 task commits present in git log (4f47777, c21126c, 8f2bd2e, be68af1)
- All acceptance criteria re-verified PASS (both tasks; grep + collection gates logged above)
- Plan verification re-run: 13/13 new tests green, `make test` 165 passed / 3 skipped, `make lint` clean, full 6-function import surface verified in `.venv`
- Zero edits outside `src/personacore/lora/` + `tests/` (diff vs base 7859df2 confirmed)

---
*Phase: 09-lora-core*
*Completed: 2026-06-11*
