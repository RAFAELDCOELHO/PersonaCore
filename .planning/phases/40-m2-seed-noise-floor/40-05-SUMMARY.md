---
phase: 40-m2-seed-noise-floor
plan: 05
subsystem: e2-driver
tags: [noise-floor, NOISE-01, driver, d-07, d-13, launchagent]
requires:
  - "40-04: frozen prereg scripts/phase40_prereg.py (sha256 a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2)"
provides:
  - "scripts/phase40_noise.py part 1: constants, run_inputs, comparators, arm_name/arm_paths/arm_spec, train_adapter (the ONE registered train call), score_a2, adapter_identity, d13_scores"
  - "tests/test_phase40_noise.py with the plain _repo_rig(monkeypatch, tmp_path, dirty=None) helper for plans 06/07"
  - "artifacts/com.personacore.phase40.e2.plist"
affects: [40-06, 40-07, 40-09]
tech-stack:
  added: []
  patterns: [torch-free-at-import driver, lazy prereg, tensor-wise adapter identity, write-once A2 records]
key-files:
  created:
    - scripts/phase40_noise.py
    - tests/test_phase40_noise.py
    - artifacts/com.personacore.phase40.e2.plist
  modified:
    - tests/test_phase23_resume.py
decisions:
  - "MODULES names the three LoRA package files (src/personacore/lora/{config,inject,layer}.py) in place of the plan's src/personacore/lora.py, which does not exist"
  - "d13_scores reads the A2 exposure rank with next(..., None): an absent pet_name row reaches d13_block as a malformed_reading block, not an exception"
requirements-completed: []
metrics:
  duration: "~15 min (HEAD bed3571 09:33 -> 8136cb1 09:48 -0300)"
  completed: 2026-10-06
  tasks: 2
  files: 4
---

# Phase 40 Plan 05: E2 driver part 1 Summary

The E2 driver's training and scoring parts, tested on CPU. It trains through one registered teach_persona call with collision-proof `e2_`/`e2rh_` arm names. A2 scoring goes through the pinned `run_erasure_arm("retrain", ...)` into a write-once record path. D-07 compares adapters tensor by tensor, never by file sha256, and an AST test enforces that. The conditional D-13 scorer returns `phase40_prereg.d13_block` and checks the NLL count. The LaunchAgent is a copy of the r1b agent.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1: constants, inputs, arm names, train_adapter, register line | aeb2e37 | scripts/phase40_noise.py, tests/test_phase40_noise.py, tests/test_phase23_resume.py |
| 2: score_a2, adapter_identity, d13_scores, plist | 8136cb1 | scripts/phase40_noise.py, tests/test_phase40_noise.py, artifacts/com.personacore.phase40.e2.plist |

## RED evidence

- Task 1 (tests written before the module existed):
  ```
  E   ModuleNotFoundError: No module named 'phase40_noise'
  ERROR tests/test_phase40_noise.py
  1 error in 0.97s
  ```
- Task 2 (tests appended before the functions and the plist existed):
  ```
  FAILED tests/test_phase40_noise.py::test_score_a2_calls_the_pin_with_the_record_path[full]
  FAILED tests/test_phase40_noise.py::test_score_a2_calls_the_pin_with_the_record_path[m2]
  FAILED tests/test_phase40_noise.py::test_adapter_identity_tensor_wise - Attri...
  FAILED tests/test_phase40_noise.py::test_adapter_identity_ast_has_no_file_digest
  FAILED tests/test_phase40_noise.py::test_d13_scores_counts_and_wiring - Attri...
  FAILED tests/test_phase40_noise.py::test_d13_scores_returns_the_gate_mismatch_block
  FAILED tests/test_phase40_noise.py::test_d13_scores_refuses_when_not_approved
  FAILED tests/test_phase40_noise.py::test_plist_mirrors_the_r1b_agent - FileNo...
  8 failed, 20 passed in 2.72s
  ```
  (`test_comparators_resolve_from_modules` was already green: `comparators()` landed in Task 1 because `run_inputs()` needs it. See the deviations.)

## Verify / acceptance outputs

Task 1:
- `grep -c "train_arm(" scripts/phase40_noise.py` -> `1`; `grep -c "phase40_noise.py" tests/test_phase23_resume.py` -> `1`; `grep -c "train_arm(" tests/test_phase40_noise.py` -> `0`
- Pre-commit verify run (test_phase40_noise, 23_resume, 21_sc5, lora_inject, 25_driver, 35_prereg): `1 failed, 155 passed in 144.82s`. The one failure was `test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push`, a clean-tree probe that reads `git status --porcelain scripts/`, and it fired because the new files were not yet committed. The same run had two ruff F401 hits (unused `json` in the driver, unused `phase38_rank` in the tests). Fixed, then `All checks passed!` / `3 files already formatted` / `19 passed in 2.28s`.
- After commit aeb2e37: `tests/test_phase25_driver.py tests/test_phase23_resume.py` -> `33 passed in 101.79s`

Task 2:
- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase40_noise.py` -> `28 passed in 2.83s`
- `-k "identity or tensor"` -> `2 passed, 26 deselected in 1.05s`
- `plutil -lint artifacts/com.personacore.phase40.e2.plist` -> `artifacts/com.personacore.phase40.e2.plist: OK`
- `ruff check .` -> `All checks passed!`; `ruff format --check .` -> `362 files already formatted`
- key_links: `grep -cE "pin[.]run_erasure_arm[(]prereg[.]A2_LABEL"` -> `1`; `grep -cE "tp[.]train_arm[(]"` -> `1`
- Census grep (`== 10|!= 10|os.replace|inject_lora|LoRAConfig|^E2_S|^E2_NOISE`) over both new files: no hits
- Pre-commit verify run (test_phase40_noise, 40_prereg, 23_resume, 21_sc5, 25_driver, lora_inject, 35_prereg): `1 failed, 217 passed in 153.74s`, `EXIT=1`. The failure was the same clean-tree probe (`+  M scripts/phase40_noise.py`).
- After commit 8136cb1: `git status --porcelain -- scripts tests artifacts results` -> empty; `tests/test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push` -> `1 passed in 0.18s`
- Prereg digest after both commits: `a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2  scripts/phase40_prereg.py` (unchanged)

The full suite was not run because the plan does not ask for it.

## Deviations from Plan

1. **[Rule 3 - Blocking] `src/personacore/lora.py` does not exist.** The plan's MODULES list names it, but LoRA is a package. MODULES lists `src/personacore/lora/config.py`, `inject.py` and `layer.py` instead, the same three files phase39_ctx.MODULES hashes. Without this change, `module_sha256()` would raise on the missing file. Commit aeb2e37.
2. **`comparators()` moved into Task 1.** `run_inputs()` (Task 1) appends every comparators() path, and `_repo_rig` creates stand-ins at those paths, so the function had to exist in Task 1. Its test (`test_comparators_resolve_from_modules`) was written with Task 2 as planned.
3. **No natural RED for the register edit.** I edited `tests/test_phase23_resume.py` (the register line, the dated NINETEEN comment, `+ 1`, the message) before running it against the new driver. The intermediate state (driver present, register not yet edited) was never observed failing. After the edit the file passes on the committed tree.
4. **The real-tree guard covers more than planned.** Besides `git status --porcelain -- results ledger` and `data/*phase40*`, it also snapshots `checkpoints/*phase40*` and `checkpoints/*e2_*`. That is where a misrouted training call would write.
5. **The plist test compares paths relative to the r1b agent.** It does not type `<repo>/.venv/bin/python`. It checks `ProgramArguments == [caffeinate, -dims, r1b[2], r1b[3] with phase37_r1b.py -> phase40_noise.py, "run"]` and the log paths in the same way, so it also holds on CI's checkout path. Every other key equals the r1b agent's.
6. **`d13_scores` reads the A2 record before loading the model,** using `next(..., None)` for the pet_name exposure rank. A missing row reaches `d13_block` as `malformed_reading`. It is not raised, and nothing is caught.

## For plan 06 (not acted on here)

`d13_scores`'s NLL-count `_prove` raises `SystemExit`, which is a `BaseException`, not an `Exception`. Ruling c's catch in `run()` has to include `SystemExit` explicitly if that failure is to become `d13_not_measured("exception", ...)` rather than end the process. Its `finally` releases the model either way.

## Known Stubs

None. `git_sha`, `refuse_if_dirty`, `phase36_caps` and `phase36_ledger` are imported (`noqa: F401`) for plan 06's preflight and run loop, as the plan's import list says.

## Threat Flags

None beyond the plan's register. T-40-16: arm names are never "real", the prefixes are phase40/phase40rh, existing outputs refuse, and the production sha256 is checked around each train. T-40-17: only load_adapter (weights_only) and the pinned loaders are used. T-40-18: an AST gate keeps any digest out of adapter_identity. T-40-19: one raw `train_arm(` occurrence, registered.

## Self-Check: PASSED

- FOUND: scripts/phase40_noise.py, tests/test_phase40_noise.py, artifacts/com.personacore.phase40.e2.plist, tests/test_phase23_resume.py (modified)
- FOUND commits: aeb2e37, 8136cb1
