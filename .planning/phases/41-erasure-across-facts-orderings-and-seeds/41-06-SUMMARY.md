---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 06
subsystem: erasure-driver
tags: [phase41, e1, driver, taylor-gradient, erase-04, erase-08]
requires: [41-05]
provides:
  - scripts/phase41_erasure.py skeleton (Phase 40 shape, E1 constants), torch-free at import
  - stop_for_rafael (STOP_KINDS; write-once evidence under data/phase41_e1/stops/)
  - component_gradients, value_span_loss, value_ids, taylor_scores, gradient_ordering, model_gradient_ordering, lora_modules
affects: [41-07, 41-08, 41-09, 41-10]
tech-stack:
  added: []
  patterns: [grad-enabled twin of the pin's forward checked by d02_check, torch.autograd.grad instead of backward]
key-files:
  created: [scripts/phase41_erasure.py, tests/test_phase41_erasure.py]
  modified: []
decisions:
  - "component_gradients uses torch.autograd.grad, not loss.backward(): no parameter's .grad is ever written, so a pre-existing .grad survives (the plan's 'restore grad=None' would have erased one)"
  - "stop_for_rafael refuses a unit that is not a plain file-name stem (it becomes part of a path)"
  - "phase36_caps / git_sha / refuse_if_dirty not imported yet: nothing in this plan uses them (ruff F401); preflight (41-08) brings them"
requirements-completed: []
metrics:
  duration: not recorded
  completed: 2026-10-08
---

# Phase 41 Plan 06: E1 driver skeleton + first-order Taylor gradient ordering Summary

`requirements-completed: []` — 41-06 implements the D-01..D-05 ordering mechanics ERASE-04 is run with; no run, no record, so it completes no requirement.

E1 driver started: Phase 40's torch-free skeleton re-targeted to E1, a written STOP-for-Rafael path, and the Taylor ordering `g_j = sum_i B[i,j] dL/dB[i,j]` proved on a tiny CPU GPT + LoRA against a central finite difference and the A-side identity, with its grad twin bit-equal to the unedited pin.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | c1d040b | skeleton + `stop_for_rafael` + 6 tests |
| 2 | d0d3720 | gradient ordering + 6 tests |

## RED (tests first)

- Task 1: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py` → `E   ModuleNotFoundError: No module named 'phase41_erasure'` / `1 error in 0.07s`.
- Task 2: same command → `6 failed, 6 passed in 1.71s` (every new test `AttributeError`: functions absent).

## Acceptance lines as printed

- `.venv/bin/python -c "import sys; sys.path[:0]=['scripts','src']; import phase41_erasure as d; print(d.FRONT, d.DISCLOSED_MODULES, d.ARM_PREFIX, d.REHEARSAL_PREFIX, d.WORK_DIR, 'torch' in sys.modules)"` → `E1 ('scripts/phase41_erasure.py', 'scripts/phase41_prereg.py') phase41 phase41rh phase41_e1 False`
- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py -k slot_census` → `4 passed, 84 deselected in 1.23s`
- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py -k "taylor_scores_identity or reranks_at_the_points or ordering_recorded or direction_and_ties or d02_twin"` → `5 passed, 7 deselected in 1.13s`
- `git diff --quiet 3787b9d -- scripts/phase19_erasure.py scripts/phase18_extraction.py` → exit 0
- `tests/test_phase41_erasure.py` whole file → `12 passed in 1.78s`
- `.venv/bin/ruff check .` → `All checks passed!`; `.venv/bin/ruff format --check .` → `366 files already formatted`
- `shasum -a 256 scripts/phase41_prereg.py` → `11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3` (frozen digest unchanged; prereg and its tests not edited)
- `find results data checkpoints -maxdepth 1 -name '*phase41*' | wc -l` → 0; `git ls-files 'results/phase41_*' | wc -l` → 0

## Census runs (not the full suite)

- Batch 1, run with Task 2 still uncommitted: test_phase41_erasure, test_phase41_prereg, test_lora_inject, test_phase21_sc5, test_phase35_*, plus every test file that scans `scripts/` (phase14_scoring, 17_stats, 18_corpus, 18_prereg, 20_prereg, 20_correction, 19_erasure, 21_unit_continuation, 23_ctrl, 25_epsilon, 25_driver, 25_prereg, 30_calibration, 30_points, 29_prereg, 33_admission, 32_points, 37_prereg, 37_routes, 36_prereg, 39_ctx, 40_prereg, 38_rank, 38_prereg, 39_prereg, tokenizer_oracle) → `2 failed, 1244 passed in 266.88s`. The two failures were clean-tree probes reporting `' M scripts/phase41_erasure.py'` (the uncommitted Task 2 diff): `test_phase25_epsilon.py::test_the_epsilon_gate_fires_on_a_planted_bare_print` and `test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push`. After commit d0d3720, both → `2 passed in 0.19s`.
- Batch 2 (other files holding `os.replace` / `train_arm(` / `ratchet_k` censuses): test_phase23_resume, 23_budget, 25_record, 25_promotion, 40_noise → `226 passed, 3 skipped in 140.64s`, EXIT=0.

## What the tests prove

- `test_taylor_scores_identity` (float64): every `g_j` equals the central finite difference of `B[:, j] *= s` at `s = 1 ± 1e-3` (rel 1e-3) and `sum_k A[j,k] dL/dA[j,k]` (rtol 1e-10); a frozen `lora_B` and a sentinel `.grad` are both left exactly as before the call.
- `test_taylor_scores_d02_twin_matches_the_pin_forward`: `float(value_span_loss(...)) == span_nll_from_ids(...)["nll_mean"] == phase19_erasure.value_span_nll_mean(...)` with exact `==` in float32 and float64; `taylor_scores` against the real pin has `d02.equal` True; a planted `+1e-6` raises `STOP FOR RAFAEL d02_inequality cell_t` and writes one stop file; every parameter's `requires_grad` is restored and no `.grad` is left.
- `test_gradient_ordering_reranks_at_the_points`: adaptive cell → rankings at (0, 16, 32, 48, 64), loads `ordered[:p]` at each point in order, no ranked component already ablated, positions 64..287 from the ranking at 64; calibration adds 128; static = one ranking at 0 equal to sorting the intact scores; bad `rerank_at` refused.
- `test_component_gradients_direction_and_ties`: most negative `g` first, equal scores by address, positive last.
- `test_ordering_recorded`: keys, the five ranking keys, JSON round trip.
- `test_model_gradient_ordering_on_the_tiny_fixture` (extra, beyond the plan's five): end to end on the fixture with the pin's address space narrowed to layer 0 by monkeypatch in the test (the pin file is untouched); the model and the caller's artifact are left intact.

## Deviations from Plan

1. **[Rule 1 - Bug] `torch.autograd.grad` instead of `loss.backward()` in `component_gradients`.** Found during Task 2. `backward()` accumulates into every leaf that requires grad (lora_A, and base weights outside `taylor_scores`), and the plan's restore `grad=None` would erase a `.grad` the caller had. `autograd.grad` returns the lora_B gradients without writing `.grad` anywhere; the test plants a sentinel grad and asserts it is the same object afterwards (T-41-23). Same value of `g_j` (FD-checked). Commit d0d3720.
2. **[Rule 2] `stop_for_rafael` refuses a unit that is not a plain file-name stem** (`../x` tested): the unit is part of the evidence path. Commit c1d040b.
3. **Skeleton imports trimmed**: `phase36_caps`, `git_sha`, `refuse_if_dirty` are not imported yet (unused here; ruff F401). Plan 41-08's preflight adds them.
4. **Extra test** `test_model_gradient_ordering_on_the_tiny_fixture` so every new function is called by a test ahead of 41-10's census. Skeleton helpers `_import_modules`, `_root_ledger`, `_device`, `_release`, `_rel` (directly) are not yet called by a test; 41-10's census will name them.

## Known Stubs

None. The usage docstring names `preflight | run | emit | report`; those commands arrive in later plans (41-08+), and the module has no `main` yet.

## Self-Check: PASSED

- FOUND: scripts/phase41_erasure.py, tests/test_phase41_erasure.py
- FOUND: c1d040b, d0d3720 (`git log --oneline -3`)
