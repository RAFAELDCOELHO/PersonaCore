---
phase: 13-ewc-a-b-no-forgetting-experiment
plan: 01
subsystem: testing
tags: [ewc, pre-registration, continual-learning, pytest, importlib, pytorch]

# Dependency graph
requires:
  - phase: 12-stage-2-conversational-fine-tune
    provides: finetune_dialog.py driver template, frozen gate metrics, Stage-0b noise floor (Δ_ret=0.068930), finetune_prod.csv D-11 target, Fisher cache + best.pt anchor
provides:
  - scripts/finetune_ab.py — arm-parameterized A/B driver (naive λ=0 vs ewc λ=0.01), one arm per process
  - Pre-registered retention-only gate ewc_mitigates() with MARGIN = 2 × 0.068930
  - D-07 name-scoped outputs + refuse-to-rerun guard (Phase-12 evidence never a write target)
  - results/phase13_ab_report.md pre-registration preamble with per-rule locking commit SHAs
affects: [13-02, 13-03, 13-04, phase-15-writeup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "importlib.util.spec_from_file_location load of a scripts/ driver from tests (first in repo, justified in the test docstring)"
    - "Arm-parameterized driver: one process per arm, penalty_fn as the single differing code path"

key-files:
  created:
    - scripts/finetune_ab.py
    - tests/test_phase13_driver.py
    - results/phase13_ab_report.md
  modified: []

key-decisions:
  - "13-01: pre-registration lives in the committed driver (constants + gate as module-level pure functions), so tests load scripts/finetune_ab.py via importlib rather than moving the rules into the package where the driver could drift from them"
  - "13-01: MARGIN computed from the transcribed 0.068930 gives 0.137860 vs the smoke report's displayed 0.137861 (unrounded floor); the 1e-6 difference is recorded in the report's pre-registration table rather than silently reconciled"
  - "13-01: the naive arm still CONSTRUCTS EWCPenalty so both CSV schemas match — ewc_penalty is a diagnostic-only column there (measured, never applied)"

patterns-established:
  - "Arm-scoped artifact isolation: arm_outputs(arm) returns every write target and refuse_if_exists() is called on all of them before any compute"
  - "Gate rule as a boundary-exclusive pure function pinned by a test asserting False at delta == MARGIN"

requirements-completed: []  # DEMO-04 is DECLARED by this plan but NOT satisfied — neither arm has run. It stays Pending in REQUIREMENTS.md until Plan 13-04 reports both arms.

# Metrics
duration: 22min
completed: 2026-08-01
---

# Phase 13 Plan 01: Pre-Registered A/B Driver Summary

**Arm-parameterized `finetune_ab.py` with the DEMO-04 retention gate (K=2 × Δ_ret 0.068930), D-07 refuse-to-rerun artifact isolation, 7 CPU-only contract tests, and a report preamble — all committed before either arm exists.**

## Performance

- **Duration:** ~22 min
- **Tasks:** 3
- **Files created:** 3

## Accomplishments

- `scripts/finetune_ab.py`: clone of the reviewed `finetune_dialog.py`, parameterized by a single positional arm arg. The twin call order (`preflight_device` → trusted `torch.load(best.pt)` → `seed_everything(1337)` **immediately** before `GPT(model_cfg)` → `load_fisher`) is replicated exactly, so the arms share the batch stream bit-for-bit (Pitfall 2). Its `TrainConfig` reprs identically to the recorded production provenance block: `TrainConfig(lr=9e-05, batch_size=32, max_steps=4000, warmup_steps=100, grad_clip=1.0, grad_accum_steps=1, weight_decay=0.1, seed=1337)`.
- Pre-registration constants block (D-10) with per-constant citation comments; `ewc_mitigates` is boundary-exclusive and retention-only (D-06 — no acquisition gate).
- D-07/WR-02 guard: `arm_outputs()` is the single source of write targets and `refuse_if_exists()` runs before any compute. `finetune_prod.csv` appears only as a read path in the D-11 cross-check; no convbase path appears at all.
- D-08 honored structurally — the best-checkpoint kwarg is absent from the `train()` call, so the end-of-call save IS the step-4000 state.
- D-11 divergence check raises **after** all outputs are saved, so a mismatch blocks report finalization without losing a 37-minute run.
- `tests/test_phase13_driver.py`: 7 CPU-only tests (6 named contracts, `test_arm_outputs_scoped` parametrized over both arms). Full suite: 281 passed, 1 skipped.
- `results/phase13_ab_report.md`: preamble only — constants table with the locking commit SHA per rule, the DELTA_RET measurement regime named (D-05 obligation 1), and the mandatory Pitfall-1 provenance exception row.

## Task Commits

1. **Task 1: A/B driver** — `c3d942e` (feat)
2. **Task 2: driver contract tests** — `91aedd1` (test)
3. **Task 3: report preamble** — `8fa2aa1` (docs)

## Files Created

- `scripts/finetune_ab.py` — one-arm-per-process A/B driver; pre-registration constants, gate, guard, twin call order, end-of-run proofs, provenance echo, D-11 cross-check.
- `tests/test_phase13_driver.py` — pins the constants, the gate boundary, the one-bit difference, `TrainConfig` identicality, arm-path scoping, and the refuse-to-rerun guard.
- `results/phase13_ab_report.md` — pre-registration preamble + empty placeholder sections for Plan 13-04.

## Decisions Made

- **Test loads the driver via `importlib`** (plan-locked option 1). The alternative — moving the gate into `personacore` — would break D-10: the pre-registration must be the committed driver itself. The docstring states this explicitly, and `main()` stays `__main__`-guarded so the load runs nothing.
- **MARGIN = 0.137860, not 0.137861.** The driver computes `K * 0.068930` from the transcribed floor; the smoke report displayed the product of the unrounded floor. Recorded as a table note rather than fudging either number.
- **`EWCPenalty` is constructed in both arms.** It is RNG-free and extra eval fns run inside the loop's RNG snapshot, so the diagnostic `ewc_penalty` column is trajectory-safe and keeps both CSV schemas identical for plotting.
- **`checkpoint_extra` is EWC-arm-only.** The naive arm applied no EWC state, so embedding fisher/theta_star in its checkpoint would misrepresent it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Reverted the premature DEMO-04 completion mark**

- **Found during:** post-task state updates
- **Issue:** The plan's `requirements: [DEMO-04]` frontmatter caused `requirements.mark-complete` to flip DEMO-04 to `[x]` / `Complete` in `.planning/REQUIREMENTS.md`. DEMO-04 requires "both retention AND acquisition reported" — neither arm has run. In a project whose core value is honest, evidence-backed claims, a green requirement with zero measurements is exactly the failure mode the phase's pre-registration discipline exists to prevent.
- **Fix:** Restored DEMO-04 to `[ ]` / `Pending`; recorded `requirements-completed: []` in this SUMMARY with a note that Plan 13-04 owns the mark.
- **Files modified:** `.planning/REQUIREMENTS.md`, this SUMMARY's frontmatter
- **Verification:** `grep -n "DEMO-04" .planning/REQUIREMENTS.md` shows `[ ]` and `Pending`.
- **Committed in:** the plan-metadata commit

---

**Total deviations:** 1 auto-fixed (1 missing critical / honesty guard)
**Impact on plan:** No scope change. All three planned artifacts shipped exactly as written.

Note on TDD ordering: Task 1 carried `tdd="true"`, but the plan itself allocates the driver's tests to Task 2 (whose `read_first` names `scripts/finetune_ab.py` as "written in Task 1"). Executed in plan order; the contracts were pinned immediately after in `91aedd1`, one commit later.

## Issues Encountered

- Two ruff E501 violations on docstring lines (the run-command block and a D-11 print header) — shortened; `ruff check` + `ruff format --check` clean.
- Acceptance criterion "contains `best_checkpoint_path` NOWHERE" initially failed because an explanatory comment used the literal kwarg name; the comment was reworded to "the best-checkpoint kwarg is OMITTED entirely".
- Float boundary risk on `ewc_mitigates(5.0, 5.0 - MARGIN)`: verified numerically — the reconstructed delta is `0.13785999999999987 < MARGIN`, so the boundary fails as pre-registered.

## Pre-Registration Ordering Proof

At the time of the report-preamble commit `8fa2aa1`, neither `results/phase13_naive/` nor `results/phase13_ewc/` exists (verified by `ls`). Every rule that will judge the arms is in git before any arm number can exist — D-10 satisfied by history, not assertion.

## Next Phase Readiness

- Plan 13-02/13-03 can run the arms directly: `python scripts/finetune_ab.py naive` then `python scripts/finetune_ab.py ewc`, separate processes, ≈37 min each on M3/MPS fp32.
- Prerequisites the driver hard-checks at startup and that must be present on disk (all gitignored): `data/dialog_train.bin`, `data/dialog_val{,_mask}.bin`, `data/retention_val.bin`, `checkpoints/best.pt`, `checkpoints/fisher_tinystories.pt`.
- Plan 13-04 fills the seven placeholder sections; the D-09 reconciliation heading is already in place.

## Self-Check: PASSED

All 3 created files exist on disk; all 3 task commits (`c3d942e`, `91aedd1`, `8fa2aa1`) present in git log.

---
*Phase: 13-ewc-a-b-no-forgetting-experiment*
*Completed: 2026-08-01*
