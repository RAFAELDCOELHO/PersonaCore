---
phase: 10-ewc-core
plan: 02
subsystem: training
tags: [ewc, training-loop, golden-fixture, bit-identity, grad-accum, pytorch]

# Dependency graph
requires:
  - phase: 10-ewc-core plan 01
    provides: EWCPenalty(fisher, theta_star, lam, device) callable used directly in the accum-equivalence pin
  - phase: 05-training (via v1.0)
    provides: train()/_optimizer_step, assemble_loss seam (D-04), save_checkpoint open-dict **extra seam
provides:
  - train(..., penalty_fn=None) — the M2 EWC seam LIVE; penalty evaluated per micro-batch, joins base_loss via assemble_loss BEFORE the /accum divide (exactly one full penalty per optimizer step)
  - train(..., checkpoint_extra=None) — dict splatted into all three in-loop save_checkpoint sites (best.pt, in-loop latest.pt, end-of-call latest.pt); Open Q1 resolved, Phase 12 never re-opens loop.py
  - tests/fixtures/golden_trajectory_v1.json — pre-edit v1.0 behavioral contract (CSV text + final-loss repr + param sha256 + capture-platform identity + captured_at_sha)
affects: [10-03 fisher cache + smoke script, 12-lambda-sweep, 13-ab-eval]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Golden-trajectory pinning: capture {csv_text, final_loss_repr, param_sha256} from the git-clean pre-edit code, commit the JSON, replay platform-gated (fp32 kernels are not bit-stable cross-OS/arch)"
    - "Platform-independent bit-identity: assert omitted==None==zero-penalty runs against EACH OTHER in-process (never the cross-platform fixture) — the CI-safe half of the guarantee"
    - "Additive kwarg threading: trailing penalty_fn=None on the private helper, keyword-only on train(), **(checkpoint_extra or {}) splat as the final kwargs at every save site"

key-files:
  created:
    - tests/fixtures/golden_trajectory_v1.json
    - tests/test_loop_penalty_fn.py
  modified:
    - src/personacore/training/loop.py

key-decisions:
  - "checkpoint_extra round-trip test covers best.pt explicitly (log_path + best_checkpoint_path in the run) so all three splat sites are executed, not just grep-asserted"
  - "loop.py module docstring updated: the 'EWC plugs in with no loop change' M1 claim now documents the LIVE seam and names the golden fixture as its bit-identity pin"
  - "EWC-02 checked off in REQUIREMENTS.md — plan 10-01 deferred it to this plan's assemble_loss splice half"

patterns-established:
  - "Golden fixture regeneration recipe documented in the test module docstring; only ever regenerable from a git-clean pre-M2 loop"

requirements-completed: [EWC-02]

# Metrics
duration: 9min
completed: 2026-06-12
---

# Phase 10 Plan 02: Loop Penalty Splice Summary

**`train(..., penalty_fn=None)` + `checkpoint_extra=None` spliced additively into the v1.0 loop — penalty joins via `assemble_loss` before the `/accum` divide, with defaults proven bit-identical to a pre-edit golden trajectory fixture**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-06-12T19:07:27Z
- **Completed:** 2026-06-12T19:16:46Z
- **Tasks:** 2 (Task 2 TDD)
- **Files modified:** 2 created, 1 modified

## Accomplishments

- Golden trajectory captured from the UN-edited loop (git-clean verified, `captured_at_sha=01b8e41...`) BEFORE any loop diff existed in history — Pitfall 6's executed-evidence ordering held
- Roadmap criterion 4 proven by execution: penalty_fn-omitted replay reproduces the golden CSV text, final-loss `repr`, and param sha256 bitwise on the capture platform (macOS/arm64, platform-gated via `meta.platform`); omitted/None/zero-penalty runs proven mutually bit-identical in-process on every platform (the CI-safe guarantee for x86_64 Linux)
- Roadmap criterion 3 (integration half): a real displaced-anchor `EWCPenalty` under `grad_accum_steps=4` matches the single 16-batch config — final losses within 1e-3, post-step params within 1e-6 — proving exactly one full penalty per optimizer step, joined before the `/accum` divide (Pitfall 5); a counting penalty is called exactly 6 times over 2 steps x accum=3
- `checkpoint_extra` round-trips fisher/theta_star tensors through best.pt AND latest.pt (all three splat sites executed); omitted default produces a fisher-less v1.0 checkpoint
- Spy-pinned AMP ordering (`unscale_ -> clip -> step -> update`) and `summed += float(base_loss.item())` untouched — logged train_loss keeps its v1.0 base-loss-only meaning
- Full suite green: 209 passed, 4 skipped (pre-existing environment gates); `ruff check` + `ruff format --check` clean

## Task Commits

1. **Task 1: Pre-edit golden trajectory fixture** - `94b0e81` (test) — captured before any loop.py change
2. **Task 2: penalty_fn + checkpoint_extra pins (RED)** - `16c73d3` (test) — 5 failing kwarg tests + the by-design-passing golden pin
3. **Task 2: Additive loop.py splice (GREEN)** - `b1fb37a` (feat) — +28/-5 lines, no restructure

## Files Created/Modified

- `tests/fixtures/golden_trajectory_v1.json` - v1.0 behavioral contract: meta recipe (seed 1234, lr=1e-2, warmup=2, max_steps=5, batch=4, CPU), capture-platform identity (Darwin/arm64/3.11/torch 2.7.x), csv_text, final_loss_repr, param_sha256
- `tests/test_loop_penalty_fn.py` - Six EWC-02 pins: platform-gated golden replay, in-process omitted==None identity (never skips), zero-penalty inertness, real-EWCPenalty accum equivalence, 6-call count, checkpoint_extra round-trip through best.pt+latest.pt (230 lines)
- `src/personacore/training/loop.py` - `_optimizer_step(..., penalty_fn=None)`; `penalties = (penalty_fn(model),) if penalty_fn is not None else ()` -> `assemble_loss(base_loss, penalties)` -> `loss = total / accum`; `train()` gains keyword-only `penalty_fn`/`checkpoint_extra` with docstring Args; `**(checkpoint_extra or {})` at all three save sites

## Decisions Made

- The checkpoint_extra test drives `best_checkpoint_path` + `log_path` alongside `checkpoint_interval=1` so the best.pt site is executed (not just grep-counted) — the must_have truth names all three sites
- loop.py's module docstring was updated from the M1 "plugs in with no loop change" promise to document the live seam and its golden-fixture pin — keeping a stale claim would misdocument the load-bearing contract
- EWC-02 marked complete in REQUIREMENTS.md: 10-01 shipped the penalty + exact-zero-at-anchor clause, this plan shipped the "plugged in via assemble_loss" clause — both halves now exist and are pinned

## Deviations from Plan

None - plan executed exactly as written. (One routine lint reflow: the widened `_optimizer_step` signature wrapped to satisfy E501 before the GREEN commit.)

## Issues Encountered

None. RED-phase note: the golden-replay test passes pre-edit by design — it pins the unedited loop's behavior captured minutes earlier on the same platform; the five kwarg tests provided the failing RED signal.

## TDD Gate Compliance

RED commit `16c73d3` (test) precedes GREEN commit `b1fb37a` (feat); no refactor commit needed (the lint wrap landed inside GREEN).

## Known Stubs

None — no placeholders, hardcoded empty values, or unwired paths. The seam is fully live and consumed by tests with a real `EWCPenalty`.

## Threat Flags

None — no new security surface. `checkpoint_extra` serializes into the project's OWN resume checkpoints under the established weights_only=False-for-own-resume posture (T-10-03 accepted in the plan); T-10-04's mitigations all landed (captured_at_sha, loop_git_clean, meta.platform gate, regeneration recipe in the test docstring).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 12 (lambda sweep) can pass `penalty_fn=EWCPenalty(...)` and `checkpoint_extra={"fisher": ..., "theta_star": ...}` straight into `train()` — loop.py never needs reopening for EWC
- Plan 10-03's fisher cache gets the carry path: extras splat into every in-loop save, so a killed sweep run resumes with its anchor intact
- The golden fixture + in-process identity tests guard every future loop edit against silent v1.0 regression

## Self-Check: PASSED

- All 3 files exist on disk (fixture JSON, test file, edited loop.py)
- All 3 task commits present in git log (94b0e81, 16c73d3, b1fb37a)
- `pytest -q`: 209 passed, 4 skipped; `make lint` clean
- Source assertions: 3 `checkpoint_extra or {}` splat sites, `penalty_fn(model)` + `assemble_loss(base_loss, penalties)` on the code path, `penalty_fn=None` in both signatures

---
*Phase: 10-ewc-core*
*Completed: 2026-06-12*
