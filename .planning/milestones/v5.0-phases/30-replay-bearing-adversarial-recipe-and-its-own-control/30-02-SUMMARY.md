---
phase: 30-replay-bearing-adversarial-recipe-and-its-own-control
plan: 02
subsystem: v5.0 driver (scripts/phase30_points.py)
tags: [ACTRL-01, ACTRL-02, ARECIPE-02, WR-05, D-09, D-10, D-13, D-14, D-15, D-16, D-17, D-18, D-19]
requires: [phase29_prereg (POINT_KEYS, control_key, leg_keys, point_record_path, V5_RESULT_PATHS, _RECIPE_FIELDS, refused_record, control_is_unlearnable, control_baseline_source), phase25_points (SWEEP_SEED, pinned_mechanism, CALIBRATION_PREFIX_LITERAL), phase25_run.atomic_write_json, teach_persona.REPLAY_ARMS (30-01)]
provides: [phase30_points.SWEEP_SCHEDULE, prove_controls_first, point_plan, recipe_identity, prereg_recipe, RECIPE_FIELDS, CALIBRATION_PATH, require_calibrated_recipe, own_control, control_floors, control_dialogue_pair, control_baseline, next_action, write_refused_records]
affects: [30-03 calibration emitter (record shape), Phase 31/32 drivers, any scripts/phase30_*..phase34_*.py (AST guard)]
tech-stack:
  added: []
  patterns: [tracked-only JSON read, read-time recipe equality, AST guard with docstring exemption and planted RED per class]
key-files:
  created:
    - scripts/phase30_points.py
    - tests/test_phase30_points.py
  modified: []
decisions:
  - "own_control checks the calibration first, then the tracked control. An untracked control therefore fails at the own-control read, and its message names the control path."
  - "The relabelled-DP refusal is carried by axis/q/clip_norm together, in one _prove that names WR-05. Each of the three also refuses on its own."
  - "write_refused_records returns the written paths and checks every target before it writes any."
requirements-completed: []
metrics:
  duration: ~25 min
  completed: 2026-09-25
---

# Phase 30 Plan 02: v5.0 driver, own control, recipe refusal — Summary

`scripts/phase30_points.py` is the v5.0 driver. `SWEEP_SCHEDULE()` is derived from `phase29_prereg.POINT_KEYS()` and runs both advr controls first. `point_plan` has the same key shape as v4.0. `recipe_identity` is imported value by value. `own_control` is the only source for floors, `control_gap` and the relearning-Z baseline, and it gets its key only from `phase29_prereg.control_key`. It refuses a relabelled DP record, recipe divergence and an untracked control. The module is torch-free at import and trains nothing.

Requirement ticks: the orchestrator/verifier rules on ACTRL-01, ACTRL-02 and ARECIPE-02. This plan marks nothing complete.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | `2eab254` | feat(30-02): v5.0 driver core — recipe identity, schedule, point plan |
| 2 | `7e36972` | feat(30-02): own-control reader, recipe refusal and D-19 guard |
| 3 | `8d96895` | test(30-02): AST guard against WR-05 carriers in v5.0 modules |

## Evidence (raw)

- **RED, Task 1 (natural):** collection error `ModuleNotFoundError: No module named 'phase30_points'`.
- **GREEN, Task 1:** `tests/test_phase30_points.py` gave 6 passed. The plan's verify (`test_phase30_points + test_phase29_prereg + test_phase25_points`) gave **100 passed**. `test_no_v5_module_uses_the_accountant` now globs phase30_points.py and passes.
- **Torch-free probe:** `python -c "...import phase30_points as p; print(p.SWEEP_SCHEDULE()[:2]); print('torch' in sys.modules)"` printed `('advr_n8_ratio0p000000', 'advr_n64_ratio0p000000')` and then `False`.
- **RED, Task 2 (natural):** 19 failed, 6 deselected. Every failure was a missing function.
- **GREEN, Task 2:** 25 passed. One test-side fix: `refused_record` builds `(k, n)` tuples, which land as JSON lists, so the written-bytes check compares against a JSON round-trip of the built record.
- **Relabelled real DP record** (`results/phase25_point_dp_n8_sigma0p000000.json`): seed 1337 matches `recipe["seed"]`, `training.train_config.max_steps` 200 matches `max_steps`, `records_per_lot` 8 matches `n_facts`, and `replay_windows(8)` matches `replay_windows`. The record is still refused on `axis 'sigma', q 1.0, clip_norm 1000000.0` with a message naming WR-05.
- **Task 3 non-vacuity (natural RED):** `_wr05_failures(scripts/phase25_points.py)` returned:
  `['dp key f-string at line 162', 'carrier name control_key_for at line 315', 'carrier name control_key_for at line 262', "dp key constant 'dp_n8' at line 593", 'carrier name control_reading at line 738', 'carrier name _adversarial_extras at line 800', "dp key constant 'dp_n8' at line 606", "dp key constant 'dp_n8' at line 784", "dp key constant 'dp_n8' at line 785", "dp key constant 'dp_n8' at line 792"]`.
  Each of the 5 planted classes fires. `"dp_n8_sigma0p000000"` is exempt in docstring position and flagged as a bare statement after `pass`.
- **Final file:** `tests/test_phase30_points.py` gave **27 passed**.
- **Guard set** (`test_phase30_points, test_phase30_seam, test_phase29_prereg, test_phase25_points, test_phase23_resume, test_lora_inject, test_phase21_sc5`) gave **161 passed** in 137 s on the committed tree.
- **Clean-tree probes** (phase25 frontier/grid/probe2/driver/epsilon/plots/watch planted-* set) gave **10 passed** after the commits. `test_phase23_resume` (which includes production_resume_epsilon) passed within the 161.
- `ruff check .` reported all checks passed. `ruff format --check .` reported 294 files already formatted.
- `git diff HEAD~3 --stat -- scripts/phase25_points.py scripts/phase29_prereg.py scripts/phase25_promotion.py scripts/teach_persona.py` is empty. `git status --porcelain scripts tests results src` is empty.
- Censuses: `grep -n "== 10\|train_arm(\|os\.replace"` over both new files finds nothing. There is no inject_lora use, so ISO-06 is unaffected.

## Pins for downstream plans

- **Phase 32 (A3):** every v5.0 point record must carry a top-level `recipe` dict equal to `phase30_points.recipe_identity(leg)`, with all six fields `n_facts, replay_windows, seed, max_steps, min_refusal_scored_tokens, replay_source`. `replay_source` is the list `["data/dialog_train.bin", "data/dialog_train_mask.bin"]`, derived rather than typed. A control without it is refused at read time (D-16).
- **Plan 30-03:** the calibration at `phase30_points.CALIBRATION_PATH` (`results/phase30_calibration.json`) must have the shape `{"recipe": {"n8": recipe_identity("n8"), "n64": recipe_identity("n64")}, ...}`. It is read only when tracked.
- Control records must carry `point_key == control_key(leg)`, `arm == advr_<leg>`, `axis == "ratio"`, `q` and `clip_norm` null or absent, `taught_recall`/`heldout_recall` `{numerator, denominator}`, `condition_c.point_dialogue_ppl_on/off` and `adapter_sha256`.

## Deviations from Plan

1. **[Rule 3 - lint] `json` and `phase25_run` were imported in Task 2, not Task 1.** Task 1 does not use them, and importing them there would have failed ruff F401. The final module imports both, as the plan requires.
2. **[Rule 2 - coverage] Extra refusals tested beyond the plan's list.** Each of axis/q/clip_norm refuses on its own. A calibration whose own recipe drifts from the live identity is refused. `require_calibrated_recipe` also proves `recipe == recipe_identity(leg)`, which the plan's action listed.
3. **Test helper imports:** only `_numeric_constants`, `_grid_retype_failures` and `_planted` are imported from test_phase29_prereg. `_git` is unused, and importing it would fail F401.
4. The good-record-at-a-non-v5.0-path case is a separate test (`test_wr05_refuses_a_good_record_at_a_non_v5_path`, at the v4.0 `adv_n8` record path). The plan had folded it into `test_wr05_refuses_wrong_provenance`.

teach_persona.py was not touched. No STATE/ROADMAP/REQUIREMENTS edits were made and no gsd-sdk mutation handler was called.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase30_points.py, tests/test_phase30_points.py
- FOUND: 2eab254, 7e36972, 8d96895
