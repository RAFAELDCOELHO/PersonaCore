---
phase: 01-scaffolding-reproducible-environment
plan: 02
subsystem: infra
tags: [pytorch, checkpoint, rng-state, reproducibility, p100, preflight, csv-logging, provenance]

# Dependency graph
requires:
  - phase: 01-scaffolding-reproducible-environment (plan 01)
    provides: installable personacore package + config dataclasses (ModelConfig/TrainConfig/RuntimeConfig)
provides:
  - "Open-dict resumable checkpoint (model+optimizer+scheduler+step+full RNG state+config+git_sha+schema_version) with RNG-state restore (not re-seed)"
  - "seed_everything(seed, strict=False) across random/numpy/torch(+cuda)"
  - "git_sha() provenance with 'unknown' fallback when .git absent"
  - "preflight_p100(require_p100) asserting CUDA + P100 name + Pascal sm_60 smoke op"
  - "CSVLogger append-only offline logger surviving session restarts"
  - "scripts/preflight_demo.py thin entry point (runs on CPU + manually on Kaggle)"
  - "Open checkpoint dict = the M2 EWC seam (TRAIN-06): accepts fisher/theta_star with no format change"
affects: [phase-03-training-loop, phase-04-gpt-model, phase-05-data-pipeline, phase-08-demo, milestone-2-ewc]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Self-describing open-dict checkpoint (never a bare state_dict); RNG-state restore for exact-trajectory resume"
    - "Single seed_everything entry point; resume restores state instead of re-seeding"
    - "Preflight fail-loud environment assertion before any long GPU run"
    - "Offline CSV logging (no wandb) with restart-survivable header-once append"

key-files:
  created:
    - src/personacore/checkpoint.py
    - src/personacore/seeding.py
    - src/personacore/provenance.py
    - src/personacore/preflight.py
    - src/personacore/logging.py
    - scripts/preflight_demo.py
    - tests/test_checkpoint.py
    - tests/test_seeding.py
    - tests/test_preflight.py
    - tests/test_logging.py
  modified: []

key-decisions:
  - "load_checkpoint uses weights_only=False for the trusted resume checkpoint (torch>=2.6 flipped the default to True; the dict carries pickled optimizer/RNG/numpy objects). Documented trusted-only; slim inference checkpoint (Phase 8) will use weights_only=True."
  - "preflight_p100(require_p100=False) degrades to a CPU device summary instead of raising when CUDA is absent, so the thin preflight_demo script runs to completion on a laptop."
  - "seed_everything defaults strict=False (Open Question 3) — full bitwise GPU determinism is opt-in due to its speed cost; the primary reproducibility guarantee is seed + git SHA + config."

patterns-established:
  - "Open-dict checkpoint with **extra keys (M2 EWC seam) + embedded config (D-03, single source of truth)"
  - "RNG generator-STATE restore (set_rng_state/set_state/setstate), never a re-seed, for trajectory-identical resume"
  - "Provenance/preflight degrade gracefully (no .git -> 'unknown'; no CUDA + require_p100=False -> CPU summary) and never abort a run unexpectedly"

requirements-completed: [ENV-04, ENV-05, QA-02]

# Metrics
duration: 14min
completed: 2026-06-04
---

# Phase 1 Plan 02: Resumability & Reproducibility Primitives Summary

**Open-dict resumable checkpoint (RNG-state restore for trajectory-identical kill-and-resume), seed_everything, git-SHA provenance, P100 preflight, and an offline restart-survivable CSV logger — all CPU-tested.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-06-04
- **Completed:** 2026-06-04
- **Tasks:** 2 (both TDD)
- **Files modified:** 10 created (6 source/script + 4 tests)

## Accomplishments
- Open-dict checkpoint bundling model+optimizer+scheduler+step+full RNG state+embedded config+git_sha+schema_version; `load_checkpoint` RESTORES generator state (not a re-seed) so a killed run continues the SAME trajectory — proven bit-identical within 1e-6 by the kill-and-resume test.
- The checkpoint dict is OPEN (accepts arbitrary `**extra` keys) — this is the Milestone 2 EWC seam (TRAIN-06): `fisher`/`theta_star` add with no format change.
- `seed_everything` seeds random/numpy/torch(+cuda) with an optional strict (bitwise-determinism) toggle; `git_sha()` records provenance and falls back to `"unknown"` when `.git` is absent.
- `preflight_p100` fail-loud asserts CUDA + P100 name + a Pascal sm_60 CUDA smoke op (catches the cu128+ kernel-drop risk) before any long run; degrades to a CPU summary on a laptop.
- Offline `CSVLogger` appends and writes its header exactly once across a process restart (Kaggle-session survivability); `scripts/preflight_demo.py` runs to completion on CPU and documents the `/kaggle/working` + read-only Dataset path convention (D-07) without downloading data.

## Task Commits

Each task was committed atomically:

1. **Task 1: Open-dict checkpoint + provenance + seeding (ENV-04, ENV-05, QA-02)** - `93cf964` (feat)
2. **Task 2: P100 preflight + CSV logger + preflight script (ENV-05, QA-02)** - `c7d6cc9` (feat)

_Note: TDD was applied per task (tests written RED first, then implementation to GREEN, then ruff format/refactor) and squashed into one feat commit per task._

## Files Created/Modified
- `src/personacore/checkpoint.py` - `save_checkpoint`/`load_checkpoint` open dict; RNG-state restore; `weights_only=False` trusted resume; `CKPT_SCHEMA_VERSION=1`; `**extra` EWC seam.
- `src/personacore/seeding.py` - `seed_everything(seed, strict=False)` across random/numpy/torch(+cuda); cuDNN benchmark off; opt-in strict determinism.
- `src/personacore/provenance.py` - `git_sha(default="unknown")` via `git rev-parse HEAD`, never aborts.
- `src/personacore/preflight.py` - `preflight_p100(require_p100=True)` CUDA+P100+Pascal-smoke assertion; CPU summary when `require_p100=False`.
- `src/personacore/logging.py` - `CSVLogger` append-only, header-once, restart-survivable.
- `scripts/preflight_demo.py` - thin wiring (seed + git_sha + preflight); D-07 path/mount convention constants only.
- `tests/test_checkpoint.py` - kill-and-resume trajectory equality (1e-6), open-dict extensibility, git-SHA recorded + fallback.
- `tests/test_seeding.py` - determinism, RNG round-trip, cuDNN-benchmark-off.
- `tests/test_preflight.py` - rejects non-P100 + no-CUDA (mocked), CPU-ok-when-not-required.
- `tests/test_logging.py` - append, header-once-across-restart.

## Decisions Made
- **`weights_only=False` on the resume checkpoint:** torch >= 2.6 changed `torch.load`'s default to `weights_only=True`, which rejects the pickled optimizer/RNG/numpy objects the resume dict must carry. Fixed to load the trusted own-file with `weights_only=False`; documented trusted-only in the module docstring (the slim inference checkpoint in Phase 8 uses `weights_only=True`). This is exactly research Pitfall 5.
- **`preflight_p100(require_p100=False)` CPU graceful path:** the acceptance criterion requires `preflight_demo.py` to run to completion on a CPU laptop; the original strict CUDA assertion raised even when P100 wasn't required, so the no-CUDA branch now returns a CPU summary when `require_p100=False`. The `require_p100=True` Kaggle path still fails loud on missing CUDA.
- **`strict=False` default for seeding** (Open Question 3): full GPU determinism is slower; the portfolio guarantee is seed + git SHA + config, with strict mode available as an opt-in.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `torch.load` weights_only default broke checkpoint round-trip**
- **Found during:** Task 1 (checkpoint save/load)
- **Issue:** Under torch 2.7.1 (>=2.6) `torch.load` defaults to `weights_only=True`, raising `UnpicklingError` on the numpy RNG state inside the resume checkpoint — 3 checkpoint tests failed.
- **Fix:** Pass `weights_only=False` in `load_checkpoint` (trusted own-file) and in the tests' raw `torch.load` inspections; documented the trusted-only contract in the module docstring. This is the research-flagged Pitfall 5.
- **Files modified:** `src/personacore/checkpoint.py`, `tests/test_checkpoint.py`
- **Verification:** `pytest tests/test_checkpoint.py` 4/4 green; kill-and-resume within 1e-6.
- **Committed in:** `93cf964` (Task 1 commit)

**2. [Rule 3 - Blocking] `preflight_p100(require_p100=False)` raised on a CPU box, blocking the demo script's acceptance criterion**
- **Found during:** Task 2 (preflight script)
- **Issue:** `preflight_p100` unconditionally raised when `torch.cuda.is_available()` was False, so `scripts/preflight_demo.py` (which calls it with `require_p100=False`) could not run to completion on a CPU laptop — failing an explicit acceptance criterion.
- **Fix:** When `require_p100=False` and CUDA is absent, print a CPU device summary and return a `{device:"cpu", cc:None, torch:...}` dict instead of raising. The `require_p100=True` Kaggle long-run path is unchanged (still fails loud).
- **Files modified:** `src/personacore/preflight.py`
- **Verification:** `python scripts/preflight_demo.py` exits 0 on CPU; `test_rejects_no_cuda` (require_p100=True default) still raises.
- **Committed in:** `c7d6cc9` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both were necessary for correctness and to satisfy stated acceptance criteria (the first is the research's own Pitfall 5; the second satisfies the "runs on CPU" criterion). No scope creep — no new modules, no architectural change.

## Issues Encountered
None beyond the two auto-fixed deviations above. ruff surfaced minor formatting/import-order nits that were auto-fixed (`ruff format` + `ruff check --fix`); no logic changes.

## User Setup Required
None - no external service configuration required. (The live P100 assertion is a manual Kaggle cell-1 check; all automated tests are CPU-only.)

## Next Phase Readiness
- Reproducibility + resumability primitives are in place: Phase 3 (training loop) can wire `save_checkpoint`/`load_checkpoint` into a real loop and re-validate trajectory equality against the bigram/GPT.
- The open checkpoint dict + embedded config keep the Milestone 2 EWC seam (TRAIN-06) open — `fisher`/`theta_star` add additively.
- Plan 01-03 (dev tooling / CI / requirements.txt / CLAUDE.md ENV-06) remains to close the phase; CI will run this plan's CPU-only suite on push.
- Full Phase-1 suite green (20 tests, CPU-only); ruff clean (15 files).

## Self-Check: PASSED

- All 11 created files verified present on disk.
- Both task commits (`93cf964`, `c7d6cc9`) verified in git history.
- Plan verification suite green: `pytest tests/test_checkpoint.py tests/test_seeding.py tests/test_preflight.py tests/test_logging.py` → 13 passed; full suite → 20 passed (CPU-only); ruff clean.

---
*Phase: 01-scaffolding-reproducible-environment*
*Completed: 2026-06-04*
