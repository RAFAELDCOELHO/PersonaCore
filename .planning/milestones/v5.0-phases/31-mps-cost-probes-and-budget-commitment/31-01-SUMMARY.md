---
phase: 31-mps-cost-probes-and-budget-commitment
plan: 01
subsystem: cost-probe
tags: [arcal-01, probe, on_draw, replay, timing, write-once]
requires:
  - phase30_points.next_action / calibration_record (tracked results/phase30_calibration.json)
  - phase25_points.train_stage / measure_stage / attack_corpus / scoring_values
  - phase25_run.draw_point_shapes / score_point / heartbeat / atomic_write_json
provides:
  - scripts/phase31_probe.py (point half): probe_plan, per_step_replay, prove_replay_counts, phase25_stage_table, build_point_record, run_point_probe, calibration_descent, emit_point, _tracked, _GIT_ROOT
  - tests/test_phase31_probe.py with the module-scoped point_probe_run fixture (for plan 03 to import)
affects: [31-02, 31-03, 31-04, 31-05]
tech-stack:
  added: []
  patterns: [tp.train rebound in try/finally to count on_draw, _ROOT vs never-patched _GIT_ROOT split, module-scoped CPU live-path fixture]
key-files:
  created: [scripts/phase31_probe.py, tests/test_phase31_probe.py]
  modified: []
decisions:
  - phase25_stage_table returns {"points": {12 v5 keys: row}, "recall_source": path}, not a flat 13-key dict
  - build_point_record proves the run sidecar's per-step replay equals expected (all_steps_equal is proved, not computed)
  - the replay sidecar carries adapter_sha256 and a reused training is refused unless it matches
  - replay_windows vs calibration is proved BEFORE training (cheap), not after
  - no main()/CLI in this plan; plan 02 owns run/emit dispatch
requirements-completed: []
# Contributes to ARCAL-01; the orchestrator decides requirement ticks at phase close.
metrics:
  duration: ~26 min
  completed: 2026-09-26
---

# Phase 31 Plan 01: MPS cost probe, point half Summary

`scripts/phase31_probe.py` runs the tracked-calibrated `advr_n64` control plan, re-keyed only to `probe31_advr_n64` / `probe31`. It goes through the REAL `train_stage` (with `tp.train` rebound to count replay draws per step via `on_draw`), `measure_stage` (condition (c) + GATE-05 timed apart from recall), `draw_point_shapes` and `score_point`. It then emits a write-once `results/phase31_probe_point.json` with `sweep_point: false`, `gates_nothing` readings, the Phase 25 twin, the 12-point min/median/max, calibration descent and provenance. All of this is proven at CPU fixture scale.

## Commits

| Task | Gate | Commit | Subject |
|------|------|--------|---------|
| 1 | RED | 5f74006 | test(31-01): add failing tests for probe identity, isolation, replay bucketing and point record builder |
| 1 | GREEN | ebf2f83 | feat(31-01): probe identity, isolation guard, replay bucketing, Phase 25 stage table and pure point-record builder |
| 2 | RED | 0c53d25 | test(31-01): add failing live-path, refusal and write-once emit tests for the point probe |
| 2 | GREEN | 3926095 | feat(31-01): run_point_probe live path and write-once emit_point |

## Verification

- `.venv/bin/pytest tests/test_phase31_probe.py -q` gives 13 passed in 13.8 s. The module-scoped `point_probe_run` fixture takes **11.45 s** of wall-clock (pytest `--durations` setup).
- The quick run (VALIDATION minus test_phase31_budget.py) is `tests/test_phase31_probe.py tests/test_phase30_points.py tests/test_phase30_calibration.py tests/test_phase29_prereg.py tests/test_phase23_resume.py`. It gives **146 passed in 125.9 s**.
- The censuses were run on the committed tree: `tests/test_lora_inject.py tests/test_phase21_sc5.py tests/test_phase25_venue.py tests/test_phase25_driver.py` gave 56 passed (18.5 min). `test_phase14_scoring test_phase17_stats test_phase19_erasure test_phase20_correction test_phase21_unit_continuation test_phase23_ctrl test_phase25_prereg test_tokenizer_oracle` gave 258 passed.
- `ruff check` and `ruff format --check` pass on both files.
- `git diff --name-only HEAD -- scripts/teach_persona.py scripts/phase30_points.py scripts/phase27_relearn.py scripts/phase25_points.py scripts/phase25_run.py scripts/phase29_prereg.py src/` printed nothing. No frozen module changed.
- After the test runs, `find data checkpoints results -name '*probe31*'` printed nothing and `git status --porcelain results` was empty.
- The live-path test's spies prove the real stages ran:
  - the adapter sha256 matches the file under the fixture root;
  - `retention_ppl` is a finite float;
  - all 4 ATTACK_FAMILIES were drawn with minutes > 0;
  - `replay.per_step == [256, 256]` (calibration n64 × fixture MAX_STEPS 2);
  - the heartbeat's last line is "done";
  - the real probe31 set is unchanged.

## Deviations from Plan

1. **[Rule 3, test shape] Torch-free subprocess.** The subprocess does not import the test module, because that would pull in pytest and the test helpers. It gets the synthetic run blob as a JSON literal instead. It still calls `phase25_stage_table(_tracked())` and `build_point_record` and prints `False`.
2. **[Census hygiene] Test values.** One synthetic value was changed from 1000.0 to 900.0. `assert ... == 1000.0` contains the substring `== 10`, which `tests/test_phase21_sc5.py`'s wall census counts.
3. **[TDD ordering] Task 2's code was written before its tests.** I saved it to a scratch patch and reverted the file to HEAD, then wrote the tests and watched them fail (RED, commit 0c53d25). After that I re-applied the unchanged patch (GREEN, 3926095). The gate order in git is honest, and the patch was not edited in between.
4. **[Plan prose vs code] `emit_point(out_path=POINT_RECORD)`.** POINT_RECORD is a repo-relative string, so a relative out_path is resolved against `_GIT_ROOT`.
5. **`phase27_relearn`** is listed among the allowed module-scope imports, but this plan does not import it (YAGNI). Plan 02 adds it if needed.

No refusals came up at fixture scale beyond the ones the plan anticipated. The fixture redirects only inputs, output paths, the device and the pinned `composed_steps`. No stage was replaced by a recorder.

## Notes for 31-02 / 31-03

- `phase25_stage_table(tracked)["points"]` has the 12 rows (keys `v4_key, source, train, measure, draw, recall`, all in seconds). `["recall_source"]` is at top level.
- `point_probe_run` returns `(run, record, evidence)`. `evidence` keys are:
  - `calls`, `outputs`, `real_plan`, `trained_plan`;
  - `fixture_max_steps`, `heartbeat_path`, `root`, `strays`.
  - `evidence["root"]` holds the fixture's `data/probe31_point_run.json` (redirect `phase31_probe._ROOT` to it), the adapter under `checkpoints/probe31_advr_n64_adapter.pt`, and `convbase_slim.pt`.
- Sidecars: `point_replay_sidecar()` gives `data/probe31_point_replay.json` (it includes `adapter_sha256`), and `point_run_sidecar()` gives `data/probe31_point_run.json`. The run sidecar's `training.adapter` is relative to `phase25_points._ROOT`.
- Every git call goes through `_git()` / `_tracked()` / `calibration_descent()` with cwd `_GIT_ROOT`. Reuse `calibration_descent()` for the relearn and budget emits.
- `_real_probe31_strays()` and `_one_prompt_per_cell()` are module-level helpers in the test file, ready for the relearn fixture.
- No `main()` exists yet (plan 02 T2).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase31_probe.py, tests/test_phase31_probe.py
- FOUND commits: 5f74006, ebf2f83, 0c53d25, 3926095
