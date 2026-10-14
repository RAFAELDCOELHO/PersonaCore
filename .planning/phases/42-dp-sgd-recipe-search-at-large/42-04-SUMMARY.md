---
phase: 42-dp-sgd-recipe-search-at-large
plan: 04
subsystem: driver
tags: [e3, dp-sgd, driver, d-05-seam, ledger, write-once, p22, rehearsal]
requires:
  - scripts/phase42_prereg.py (42-01..03; read, never edited)
  - scripts/phase25_points.py point_plan / training_sidecar / train_stage (read, not edited)
  - scripts/teach_persona.py LR / WARMUP_STEPS / MAX_STEPS / arm_outputs / score_arm (rebound at runtime, not edited)
  - scripts/phase14_recall.py load_adapted_model, scripts/phase25_condition_c.py measure_condition_c, scripts/phase25_recall.py _tier
  - scripts/phase36_ledger.py, scripts/phase36_caps.py, scripts/phase25_run.py, personacore.provenance
provides:
  - "scripts/phase42_recipes.py: cell_plan, train_cell (the D-05 seam), _resume_guard, score, retention, write_unit, record_rehearsal, stage, p22_check, _launch_requirements, _launch_pathspec, preflight, run"
  - "tests/test_phase42_recipes.py: _train_rig / _measure_rig / _run_rig (fake train_stage, score_arm, load_adapted_model, measure_condition_c on a tmp root with a tmp ledger and heartbeat), _write, _events, _plant"
affects: [42-05, 42-06, 42-07, 42-08, 42-10]
tech-stack:
  added: []
  patterns: [phase41_erasure driver skeleton, phase36_probe stage_e3 module-global rebinding in try/finally, phase41 real-root rig]
key-files:
  created:
    - scripts/phase42_recipes.py
    - tests/test_phase42_recipes.py
  modified: []
decisions:
  - "A scratch root reaches stage 2 once its 3 control records exist (the plan's stage rule), so the 'second run is a no-op' leg runs on a real-root rig, where stage 2 needs the threshold file tracked"
  - "record_rehearsal adds a later call's CPU seconds to cpu_seconds and its units in UNITS order; run checks an existing identity before the first start line"
  - "check_unit_caps also gets sigmas (counts_for has no sigmas key; 42-PATTERNS asks for it)"
requirements-completed: []
metrics:
  duration: ~55 min
  completed: 2026-10-14
  tasks: 3
  files: 2
---

# Phase 42 Plan 04: the E3 driver's measuring half Summary

`scripts/phase42_recipes.py` now trains each unit through ONE `phase25_points.train_stage` call. For that call, teach_persona's `LR` / `WARMUP_STEPS` / `MAX_STEPS` are rebound to the recipe's (lr, `warmup_for(T)`, T) and restored in `finally`. The take is then proved from the sidecar's `train_config`, `composed_steps` and `clip_norm`. The driver scores with the v4.0 instrument and reads retention descriptively. It writes write-once control and point records that the real Phase 35 threshold rule accepts. Every unit runs under `require_launch("E3")` with one start line and one end line. Before any stage-2 training it re-runs P22 at T = 200 and T = 800. `teach_persona.py`, `phase25_points.py`, `phase35_prereg.py` and `phase42_prereg.py` are unchanged.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | 0e2d668 | feat(42-04): E3 driver skeleton, cell_plan and the D-05 seam with its take proof and resume guard |
| 2 | 1a96115 | feat(42-04): scoring, descriptive retention and the write-once control and point records |
| 3 | b1e60cd | feat(42-04): preflight, the stage-2 P22 re-assert, run under the ledger and the rehearsal identity |

In each task the tests were written first and run against the previous driver state. Test and implementation then landed in one commit, as in 42-02 and 42-03.

## RED outputs (natural, before implementation)

- **Task 1:** `E ModuleNotFoundError: No module named 'phase42_recipes'`, `1 error in 1.06s` (collection error, before the driver existed).
- **Task 2:** `5 failed, 9 passed in 1.87s`. All five failed with `AttributeError: <module 'phase42_recipes' ...> has no attribute 'git_sha'`, raised when the rig patched the not-yet-imported name.
- **Task 3:** `11 failed, 14 passed in 2.50s`, all `AttributeError`. The first green attempt then failed 2 tests in the tests themselves; see Deviations 4 and 5.

## Function signatures as written

```
cell_plan(unit, *, rehearsal)                 train_cell(unit, *, rehearsal) -> (plan, blob)
_resume_guard(plan, recipe)                   _schedule_of(recipe) -> (lr, warmup_steps, max_steps)
score(plan, adapter, device)                  retention(adapter, device)
_run_provenance(pf, started_utc)              write_unit(unit, *, pf, started_utc, state) -> record rel path
record_rehearsal(path, *, units, seconds)     _kept_identity(path)   _well_formed(identity)   _disclosed_digests()   _load(path)
stage(root) -> 1 | 2                          p22_check() -> {T: onset}
_launch_requirements(*, real, device, identity, digests)
_launch_pathspec(root)                        _stale_outputs(unit, *, real)
preflight(*, root=None, ledger_path=None, heartbeat_path=None, device=None, units=None)
  -> {root, real, device, ledger_path, heartbeat_path, git_sha, module_sha256, stage, pending, p22, gate}
run(*, root=None, ledger_path=None, heartbeat_path=None, device=None, units=None, rehearsal_identity=None)
  -> {stage, whole}
```

Module constants: `FRONT = "E3"`, `LAUNCH_PATHSPEC`, `PREREG_FILE`, `THRESHOLD_FILE = "scripts/phase42_threshold_prereg.py"`, `DRIVER_FILE`, `DISCLOSED_MODULES`, `MODULES` (the plan's 15 paths), `RUN_PROVENANCE_KEYS`, `REHEARSAL_IDENTITY = "data/phase42_rehearsal.json"` (resolved under `_ROOT`), `STAGE_1_DONE`.

## Acceptance lines, as printed

**Task 1**
- `-k "warmup or clip or resume or take or torch"` gave `9 passed`. The `-k warmup` selection is 2 tests: (0.001, 20, 200) and (0.0003, 80, 800) taken and restored, and restored on a raise.
- `git diff --quiet cfc0fe6 -- scripts/teach_persona.py scripts/phase25_points.py scripts/phase35_prereg.py` exits 0 (`PINS_OK`).
- Torch-free import, from a fresh interpreter:
  - `import phase42_recipes; 'torch' in sys.modules` gives `False`.
  - The test's subprocess probe prints `E3 False False False False` for torch, teach_persona, phase14_recall and phase42_prereg.

**Task 2**
- `-k "contract_and_the_real_rule or epsilon or write_once"` gave `3 passed, 11 deselected`.
- The real threshold fill (`phase35_prereg.fill("e3_recall_threshold", **phase42_prereg.threshold_fill_inputs())`) accepts the 3 control records that `write_unit` wrote on a scratch root. The fake counts are 790/1008 and 346/648, and the v4.0 control is copied byte-identical. Printed by a scratchpad script that uses the test rig:

  ```
  (0.0003, 200, 8, 1337) {'control': 'results/phase25_point_dp_n8_sigma0p000000.json', 'taught': 0.5486111111111112, 'heldout': 0.3737654320987654}
  (0.0003, 800, 8, 1337) {'control': 'results/phase42_control_lr3e-04_t800.json', 'taught': 0.5486111111111112, 'heldout': 0.3737654320987654}
  (0.001, 200, 8, 1337) {'control': 'results/phase42_control_lr1e-03_t200.json', 'taught': 0.5486111111111112, 'heldout': 0.3737654320987654}
  (0.001, 800, 8, 1337) {'control': 'results/phase42_control_lr1e-03_t800.json', 'taught': 0.5486111111111112, 'heldout': 0.3737654320987654}
  ```

  The fake counts are the v4.0 control's own, so all four keys get the v4.0 thresholds.
- `phase42_prereg.descriptive_reading` reads the written record too (`dialogue_gap == -0.75`).

**Task 3**
- `-k "launch or write_once or ledger or p22 or refused_still_runs or pathspec"` gave `7 passed, 18 deselected`.
- After the tests ran:
  - `git status --porcelain -- results ledger data checkpoints` prints nothing.
  - `git ls-files 'results/phase42_*'` prints nothing.
  - `find results data checkpoints -maxdepth 2 -name '*phase42*'` prints nothing.

## Verification on the committed tree (after b1e60cd)

| Command | Result |
|---------|--------|
| Plan verification: recipes + prereg + phase23_resume + phase25_driver + lora_inject + phase21_sc5 | `122 passed in 112.45s`, EXIT=0 |
| Task 3 verify, part 2: `tests/test_phase36_ledger.py tests/test_phase36_caps.py` | `80 passed`, EXIT=0 |
| Census call 1: `test_phase35_prereg.py -k "slot_census or slot_ordering or grids_must or e3_"` | `13 passed, 75 deselected`, EXIT=0 |
| Census call 2: the ten files/nodes of VALIDATION.md line 24 | `109 passed in 108.11s`, EXIT=0 |
| Quick run: `tests/test_phase42_prereg.py tests/test_phase42_recipes.py` | `73 passed` |
| Extra: the census files that glob all of `scripts/*.py` (test_phase14_scoring, test_phase17_stats, test_phase23_ctrl, test_phase21_unit_continuation, test_phase30_calibration, test_phase25_prereg, test_tokenizer_oracle) | `151 passed`, EXIT=0 |

- The quick run's third file, `test_phase42_threshold_prereg.py`, does not exist until plan 42-09.
- `ruff check .` gave `All checks passed!`. `ruff format --check .` gave `372 files already formatted`.
- Before the Task 1 commit, `test_phase25_driver.py::test_the_git_surface_gate_fires_on_a_planted_push` failed on `?? scripts/phase42_recipes.py`. This is the expected clean-tree probe; it passed after the commit (`24 passed`).

## Deviations from Plan

1. **The "second run is a no-op" leg moved to a real-root rig.**
   - The plan's `stage()` rule makes a scratch root stage 2 once all 3 control records exist (`scripts/phase42_recipes.py:479-486`). A second scratch run would therefore start stage 2, not no-op.
   - `test_run_writes_one_start_and_one_end_per_unit` (scratch) now asserts `stage(root) == 2` after stage 1.
   - The no-op is tested in `test_real_root_second_run_is_a_no_op_and_excludes_its_own_records`. That rig mirrors phase41's real rig: `_ROOT`, the milestone ledger and the heartbeat point into the tmp root, device mps, the rehearsal identity is recorded, and nothing is tracked.
   - The second run writes no ledger line and makes no training call. It prints STAGE_1_DONE, and its dirty-tree pathspec equals `_launch_pathspec(root)` with the 3 records excluded.
   - In preflight, stage 1 with nothing pending prints STAGE_1_DONE and returns `pending ()` (`:613-615`). Stage 2 with nothing pending is refused with "nothing to run ... emit next" (`:616`).
2. **[Rule 2] Extra refusals taken from the crash_rule / phase41 precedent:**
   - An open attempt whose record exists is refused with "append its end line by command, NEVER reconcile" (`:582-587`), before the generic "reconcile it first" refusal.
   - An existing rehearsal identity at stale digests is refused before the first start line (`:672-674`). The identity itself is recorded after the loop, with the run's seconds.
3. **Caps.** `check_unit_caps("E3", **counts_for(...), sigmas=len(grid sigmas))` (`:633-637`). `phase36_caps.counts_for("e3_grid_subset", ...)` returns no `sigmas` key, and 42-PATTERNS asks for it; the committed cap is 3.
4. **pathspec test mechanics.**
   - The real root is made by monkeypatching `phase42_recipes._ROOT` to the tmp git repository, not `_is_real` itself. Preflight then resolves the identity path under the tmp root and never reads the real `data/`.
   - The stray-file leg matches "dirty", not "stray": `git status --porcelain` collapses an untracked directory to `?? results/`. The pass/raise pair still isolates the stray: the excluded record alone passes, and adding the stray raises.
5. **`_tracked_and_clean` test.** It runs on a tmp git repository with `_REPO` patched (tracked-clean, untracked, modified), not against the real tree. My first draft read the real tree and also kept a stale monkeypatch.
6. **Additions beyond the plan's list:**
   - Helpers: `_schedule_of`, `_stale_outputs`, `_load`, `_disclosed_digests`, `_well_formed`, `_kept_identity`.
   - `write_unit` records heartbeat stage changes (train / score / retention / done) and resolves the adapter as `phase25_points._ROOT / blob["adapter"]` (`:357`). That is `train_stage`'s `_rel` base, the same as `measure_stage`.
   - `record_rehearsal` sums `cpu_seconds` across calls (`:466`).
   - Extra test legs:
     - a `clip_norm` take-proof leg;
     - a finished-sidecar leg in the resume guard;
     - `test_lost_attempts_are_read_from_the_ledger`;
     - a per-unit `require_launch` leg (preflight's call passes, the one before the first start line refuses);
     - a P22 leg where the onset equals the frozen value and still crosses;
     - `test_stage_reads_the_threshold_file_and_the_controls_on_the_real_root`.
7. **Module-level imports.** `phase25_points`, `phase25_record` and `phase35_prereg` are imported at module level. Each was measured torch-free at import (`'torch' in sys.modules` False after importing it alone). teach_persona, phase14_recall, phase25_recall, phase25_condition_c and the prereg stay lazy.
8. **Test helpers reused from other test files:** `_plant_controls` from `tests/test_phase42_prereg.py:974` and `_tmp_git` from `tests/test_phase41_erasure.py:64`.
9. **Census registers: none needed. Checked:**
   - No `train_arm(`, `inject_lora`, `retention_perplexity`, `mitigation_point_verdict` or `os.replace` token appears in either file. The plan-01 AST gate passes, and `== 10` appears nowhere.
   - The every-function census (`tests/test_phase36_prereg.py:418` `_untested_functions`) is applied per named module and does not cover `phase42_recipes`.
   - No existing test file was edited.
10. **Ruff invocation.** The plan names `.venv/bin/ruff`; I ran `.venv/bin/python -m ruff`, as the executor brief requires.
11. **Plan names checked against the code.** Every cited name resolved as written: `phase25_points.point_plan` / `training_sidecar` / `train_stage`, `phase25_record.point_key`, `phase35_prereg.E3_N` / `DELTA` / `p22_onset_sigma` / `F_Y`, `phase25_recall._tier`, `phase14_recall.load_adapted_model`, `phase25_condition_c.measure_condition_c`, `phase36_ledger.require_launch` / `append` / `open_runs` / `read_ledger`, `phase36_caps.check_unit_caps` / `counts_for`, the checkpoint's `train_config` key (`src/personacore/checkpoint.py:135`), and `TrainConfig`'s 8 fields, which equal the v4.0 record's `train_config` keys. No misnamed artifact.

## Known Stubs

None. `emit`, `report` and `main` belong to plan 42-05; the module docstring already lists their commands.

## Threat Flags

None beyond the register:
- T-42-14: try/finally restore, the sidecar take proof and the raise-path test.
- T-42-15: `_resume_guard`.
- T-42-16: `require_launch` per unit, the open-run refusal, and mps plus the identity on the real root.
- T-42-17: write-once checked before training.
- T-42-18: `p22_check` before stage-2 training.
- T-42-18b: `_launch_pathspec`, with its tmp-git natural RED and the stray leg.

## Self-Check: PASSED

- FOUND: scripts/phase42_recipes.py, tests/test_phase42_recipes.py
- FOUND commits: 0e2d668, 1a96115, b1e60cd
- No edits to STATE/ROADMAP/REQUIREMENTS/PROJECT; no gsd-sdk handler called; no existing scripts/src module or test file edited; no results/phase42_* created.
