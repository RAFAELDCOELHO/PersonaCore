---
phase: 42-dp-sgd-recipe-search-at-large
plan: 02
subsystem: prereg
tags: [prereg, e3, dp-sgd, units, record-layout, threshold-fill, gitignore]
requires:
  - scripts/phase42_prereg.py (42-01: RECIPES, E3_GRID_SUBSET, RECORD_GLOB, CONTROL_GLOB, WARMUPS, _V4, _CONTEXT, _RULING_CONTEXT)
  - scripts/phase35_prereg.py fill / _rule_e3_recall_threshold (unchanged)
  - scripts/phase25_record.py point_key, scripts/phase36_ledger.py run_id, scripts/mitigation_budget.py CLIP_NORM / CONTROL_CLIP_NORM, scripts/teach_persona.py arm_outputs / WARMUP_STEPS / MAX_STEPS (all read, none edited)
provides:
  - "scripts/phase42_prereg.py: recipe_tag, sigma_tag, REUSED_RECIPE, CONTROL_UNITS, POINT_UNITS, UNITS, unit_cell, unit_record, E3_RECORD, REPORT_RECORD, run_id, REAL_PREFIX, REHEARSAL_PREFIX, train_prefix, warmup_for, clip_norm_for, expected_train_config, recipe_key, threshold_fill_inputs"
  - "tests/test_phase42_prereg.py: _csv_rel, _plant_controls, _ignored helpers (plans 04/09 can reuse)"
  - ".gitignore: results/phase42e3_*/ and results/phase42rh_*/"
affects: [42-03, 42-04, 42-05, 42-07, 42-08, 42-09, 42-10, 42-11]
tech-stack:
  added: []
  patterns: [phase41_prereg unit/record helpers, floors_fill_inputs fresh-kwargs shape, real Phase 35 rule on a monkeypatched _REPO_ROOT]
key-files:
  created: []
  modified:
    - scripts/phase42_prereg.py
    - tests/test_phase42_prereg.py
    - .gitignore
decisions:
  - "REUSED_RECIPE is read from the one fill cell whose reuse is not None, not taken as RECIPES[0]"
  - "sigma tags come from phase25_record.point_key with the arm prefix stripped, never formatted in the prereg"
requirements-completed: []
metrics:
  duration: ~30 min
  completed: 2026-10-14
  tasks: 3
  files: 3
---

# Phase 42 Plan 02: units, record paths and the threshold fill's kwargs Summary

`scripts/phase42_prereg.py` now names every Phase 42 unit before any run: 3 new sigma = 0 controls and 8 noised points. It also defines each unit's record path, ledger run id and training prefix, plus the T-derived warmup, the clip and train_config rules the driver proves every take against, and the exact kwargs of the `e3_recall_threshold` fill. Tests feed those kwargs to the real Phase 35 rule on planted control records. Two `.gitignore` lines keep a crashed run's csv directory out of the clean-tree probes.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | e9069fd | feat(42-02): units, record paths, run ids, training prefixes and the warmup rule |
| 2 | 369b447 | feat(42-02): clip and train_config rules, threshold_fill_inputs exercised through the real rule |
| 3 | f77c82e | feat(42-02): gitignore the Phase 42 training csv directories, with its test |

Each task's tests were written and run before the implementation. Each test and its implementation landed in one commit, as the plan's "commit both files" asks.

## RED outputs (natural, before implementation)

- Task 1: the four new tests ran against the 42-01 prereg and gave `4 failed, 26 passed in 3.89s`, all `AttributeError: module 'phase42_prereg' has no attribute ...`.
- Task 2: the four new tests ran against the Task-1 prereg and gave `4 failed, 30 passed in 3.50s`, all `AttributeError`.
- Task 3 is not TDD. The test passed on first run, after the `.gitignore` lines were added.

## Acceptance lines, as printed

Task 1:
```
('control_lr3e-04_t800', 'control_lr1e-03_t200', 'control_lr1e-03_t800') point_lr3e-04_t200_sigma0p500000 8 ['results/phase42_control_lr3e-04_t800.json', 'results/phase42_control_lr1e-03_t200.json', 'results/phase42_control_lr1e-03_t800.json'] results/phase42_point_lr1e-03_t800_sigma1p000000.json v6/42/E3/point_lr3e-04_t200_sigma0p500000 20 80
```
Comparison with plans 08-11 `files_modified`: the 3 control paths equal 42-08/42-09's three `results/phase42_control_*.json` lines. The 8 printed point paths (`[p.unit_record(u) for u in p.POINT_UNITS]`) equal 42-10/42-11's eight `results/phase42_point_*.json` lines, in the same order. `E3_RECORD` = `results/phase42_recipes.json`, which equals 42-11's line. **No mismatch.**

Task 2:
```
True ('results/phase25_point_dp_n8_sigma0p000000.json', 'results/phase42_control_lr3e-04_t800.json', 'results/phase42_control_lr1e-03_t200.json', 'results/phase42_control_lr1e-03_t800.json') {'batch_size': 8, 'grad_accum_steps': 8, 'grad_clip': 1.0, 'lr': 0.001, 'max_steps': 800, 'seed': 1337, 'warmup_steps': 80, 'weight_decay': 0.0}
```
- `-k "threshold or clip or train_config"`: `4 passed, 30 deselected`.
- `test_phase35_prereg.py -k "slot_census or slot_ordering or e3_"`: `12 passed, 76 deselected`.
- `test_threshold_fill_runs_the_real_rule_on_planted_controls` passes:
  - The v4.0 key gives taught `0.5486111111111112` and held-out `0.3737654320987654`, with `control == V4_CONTROL_RECORD`.
  - The `(1e-3, 800, 8, 1337)` key gives `phase29_prereg.REFUSED`.
  - A control carrying another recipe is refused.
  - A v4.0 copy whose final `\n` is replaced by ` ` is still valid JSON, and it is refused with "byte-identical".
  - Restoring the copy makes the fill pass again.

Task 3:
- `-k gitignored`: `1 passed, 34 deselected`.
- `git check-ignore -q results/phase42e3_x_dp_n8/run.csv` exits 0 and `! git check-ignore -q results/phase42_point_x.json` succeeds (VERIFY_OK).
- `git check-ignore -q results/phase42rh_x_dp_n8/run.csv` gives `rh=0`; `results/phase42_control_x.json` gives `control=1`.
- `git status --porcelain -- scripts tests results .gitignore` is empty after f77c82e.

## Verification on the committed tree (after f77c82e)

- Plan verification: `pytest tests/test_phase42_prereg.py tests/test_phase35_prereg.py tests/test_phase36_caps.py` gave `158 passed in 105.05s`.
- Quick run: `tests/test_phase42_prereg.py` gave `35 passed`. It is the only phase42 test file so far.
- Census call 1: `test_phase35_prereg.py -k "slot_census or slot_ordering or grids_must or e3_"` gave `13 passed, 75 deselected`.
- Census call 2 (the ten files/nodes of VALIDATION.md line 24): `109 passed in 108.34s`.
- `ruff check` (both via `.venv/bin/ruff` and `python -m ruff`) gave `All checks passed!`. `ruff format --check` gave `2 files already formatted`.
- `git ls-files 'results/phase42_*'` and `find results -maxdepth 1 -name 'phase42*'` both print nothing.

## Deviations from Plan

1. **`clip_norm_for` uses the module-level `mitigation_budget` import, not a lazy one.** 42-01 already imports it at `scripts/phase42_prereg.py:43` (torch-free, per the 42-01 SUMMARY Deviation 2). A second, lazy import would be dead weight. Function at `scripts/phase42_prereg.py:820`.
2. **Census-driven call form in the tests.** The every-function census (`tests/test_phase36_prereg.py:418` `_untested_functions`) only counts `phase42_prereg.<fn>(...)` calls. My first draft of the new tests used an alias, `p = phase42_prereg`, and failed the census with 6 untested functions. The new sections (8)-(10) of `tests/test_phase42_prereg.py` now call through the module name. No production change.
3. **Additions beyond the plan's list:**
   - An import-time `_prove` that `warmup_for` agrees with 42-01's `WARMUPS` (`scripts/phase42_prereg.py:811`), so the two forms of the D-05 rule cannot drift.
   - `_REUSED` plus a `_prove` of exactly one reused cell before `REUSED_RECIPE` is unpacked (`:733`).
   - Membership proofs in `run_id`, `train_prefix` and `recipe_key` (refusing names outside UNITS / recipes outside RECIPES), and `sigma_tag` proving the point key starts with the arm prefix.
   - Extra test legs: refusals of `recipe_tag`/`sigma_tag`/`unit_record`/`run_id`/`train_prefix`/`expected_train_config` on out-of-grid input; `sigma_tag(CONTROL_SIGMA) == "sigma0p000000"`; distinct unit records; a restore-and-pass leg after the tamper.
4. **The planted-mismatch refusal matches the Phase 35 rule's own message `D-17`** (`tests/test_phase42_prereg.py:1031`). `scripts/phase35_prereg.py` `_rule_e3_recall_threshold` cites the v6.0 D-17 in its refusal text. The Phase 42 numbering (D-12/D-19) does not appear in that message.
5. **Plan path/constant check:** every name the plan cites resolved as written: `phase25_record.point_key`, `phase36_ledger.run_id`, `teach_persona.arm_outputs`, `mitigation_budget.CLIP_NORM`/`CONTROL_CLIP_NORM`, `phase35_prereg._REPO_ROOT`, `phase29_prereg.REFUSED`. No misnamed artifact.

## Known Stubs

None.

## Threat Flags

None. The new functions are pure path/rule builders. `.gitignore` gains two directory patterns, and a test proves no record path is ignored. T-42-06/07/08/09 are mitigated as the plan's register states.

## Self-Check: PASSED

- FOUND: scripts/phase42_prereg.py, tests/test_phase42_prereg.py, .gitignore (lines 21-25)
- FOUND commits: e9069fd, 369b447, f77c82e
- No edits to STATE/ROADMAP/REQUIREMENTS/PROJECT; no gsd-sdk handler called; no existing pinned module edited.
