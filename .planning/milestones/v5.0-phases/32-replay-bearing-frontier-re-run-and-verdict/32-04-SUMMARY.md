---
phase: 32-replay-bearing-frontier-re-run-and-verdict
plan: 04
subsystem: v5.0 sweep driver loop (scripts/phase32_points.py) and its LaunchAgent
tags: [driver, run-loop, prereg-03, stop-line, d-06, d-07, d-11, launchagent, cli]
requires: ["32-02"]
provides:
  - "run_point(plan, tracked, *, heartbeat_path, stop_line): counted train -> recall-on measure -> draws -> score -> record -> write -> one-path commit"
  - "run(*, heartbeat_path=HEARTBEAT_PATH, past_stop_line=None): D-17 walk, interrupted-commit recovery, PREREG-03 refused leg, D-03/D-04 stop line, D-06 ruling"
  - "build_parser / main: `run [--heartbeat P] [--past-stop-line RULING]`"
  - "artifacts/com.personacore.phase32.sweep.plist (D-05, fixed argv per D-20)"
affects: [32-05, 32-06]
tech-stack:
  added: []
  patterns: [phase31 run_point_probe stage sequence re-keyed per point, signature-bound recorders, main-driven full-chain test with only the stages faked]
key-files:
  created:
    - artifacts/com.personacore.phase32.sweep.plist
  modified:
    - scripts/phase32_points.py
    - tests/test_phase32_points.py
decisions:
  - "Interrupted-commit recovery commits only TRAINED records found on disk untracked; PREREG-03 records on disk are left to the refuse branch, where write_refused_records byte-checks them before commit_untracked commits them"
  - "The 'all 12 tracked' completeness check runs after interrupted-commit recovery, so a sweep whose last record was written but not committed completes instead of hitting the stop-line refusal"
  - "calibration_descent is a local literal-argv copy (cwd=_GIT_ROOT), as 32-03 did, so scratch repos and the git-surface AST both see it"
requirements-completed: []
# This plan contributes to AFRONT-01 (the execution path: run loop, CLI, LaunchAgent) but does not complete it; plan 05 runs the live sweep.
metrics:
  duration: ~95 min (about 50 min of it waiting on the plan-end and census runs)
  completed: 2026-09-27
  tasks: 2
  files: 3
---

# Phase 32 Plan 04: v5.0 sweep run loop, CLI and LaunchAgent Summary

`python scripts/phase32_points.py run` now walks the 12 v5.0 keys in `SWEEP_SCHEDULE()` order. It skips tracked keys, dispatches on `next_action`, and handles a refused leg by writing the whole leg through `write_refused_records` and committing each path alone. A trained point goes through replay counting per step, recall-on measurement, draws, scoring, record, write and a one-path commit. The loop stops cleanly, with exit 0 and a `stop_line` beat, once the committed stop line is reached. `--past-stop-line` works only past the line, and its ruling lands in every later record's provenance. Every branch runs on scratch repos. One test drives `main()` → `run()` → the real `run_point()`, build, write and commit, with only the frozen stage functions faked.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 RED | `39a7026` | tests/test_phase32_points.py |
| 1 GREEN | `406766a` | scripts/phase32_points.py |
| 2 RED | `d598650` | tests/test_phase32_points.py |
| 2 GREEN | `94fdd7f` | scripts/phase32_points.py, artifacts/com.personacore.phase32.sweep.plist |

## Signatures as shipped

```python
replay_sidecar(key) -> Path                  # _ROOT/data/phase32_<key>_replay.json
calibration_descent() -> {"path", "add_commit", "is_ancestor_of_head"}
run_point(plan, tracked, *, heartbeat_path, stop_line) -> record
MANUAL_RELAUNCH                              # the D-20 manual command text
run(*, heartbeat_path=phase25_run.HEARTBEAT_PATH, past_stop_line=None) -> 0
build_parser(); main(argv=None) -> run(...)
```

Record provenance: `module_sha256` (over PINNED_MODULES), `git_sha` (INSTRUMENT_GIT_SHA), `sessions`, `stop_line` = `{seconds, cumulative_before_point, past_line_ruling}`, `device` (`phase25_run.device()`), `torch_version`, `calibration`, `written_utc`, and `head_at_write`, which is set just before `write_point_record`.

## main() → run() → run_point() kwarg trace

- `inspect.signature(run)` = `(*, heartbeat_path=…, past_stop_line=None)`. `main` passes exactly `heartbeat_path=Path(args.heartbeat), past_stop_line=args.past_stop_line`. The recorder binds against the real signature, and a planted wrong kwarg raises TypeError (tested).
- `inspect.signature(run_point)` = `(plan, tracked, *, heartbeat_path, stop_line)`. `run` passes `act["plan"], tracked, heartbeat_path=…, stop_line={…}`. The loop tests bind the recorder to this signature.
- `test_main_drives_the_real_run_and_run_point` runs `main(["run", "--heartbeat", p, "--past-stop-line", "main ruling"])` through the real run, run_point, build_point_record, write_point_record and commit_path on a scratch repo. Only train_stage (which still calls `tp.train` through the counting wrapper), measure_stage, attack_corpus, scoring_values, draw_point_shapes and score_point are faked. It asserts one single-path commit and `provenance.stop_line.past_line_ruling == "main ruling"`.

## Tests run

- tests/test_phase32_points.py: **52 passed**. That is 28 from 32-02, 16 from Task 1 (one parametrized in two) and 8 from Task 2.
- RED checks: Task 1's tests, run against the HEAD module in a scratch copy, gave 16 new failures. The copy's two WR-02 failures came from its one-commit scratch history. Task 2 RED gave 6 failures.
- The census gate (10 tests) passed after each GREEN commit.
- Plan end, `tests/test_phase32_points.py tests/test_phase30_points.py tests/test_phase31_probe.py tests/test_phase25_venue.py`: **136 passed** in 21 min 34 s. The skip pin did not move.
- Repo-wide census files, after the final code commit 94fdd7f (every `tests/*.py` matching `glob|rglob|plist`, 58 files, conftest excluded): **1606 passed**, 0 failed, 0 skipped, in 27 min 58 s.
- ruff check and ruff format --check are clean on both .py files. The plist loads with plistlib, its Label is right, and `--past-stop-line` is not in ProgramArguments.
- `git status` after the tests showed no stray `data/phase32_*`, `checkpoints/phase32_*` or `results/` writes.

## TDD gate compliance

Both tasks have a `test(...)` commit followed by a `feat(...)` commit.

## Deviations from Plan

- **[Rule 1] Completeness check placement.** The plan puts "all 12 tracked → complete" before the interrupted-commit step. If 11 records are committed and the 12th is on disk but untracked, that order would then check the stop line and could refuse a finished sweep. The check now runs after recovery. `test_complete_sweep_returns_0_without_reading_the_stop_line` still passes, with no budget committed at all.
- **[Rule 2] Recovery scope.** Interrupted-commit recovery commits only trained records. On-disk PREREG-03 records go through the refuse branch, so `write_refused_records` byte-checks them first (the WR-05 resumable contract). `test_refused_leg_retry_commits_only_the_uncommitted` covers the 2-committed/3-untracked case.
- **commit_untracked binding.** 32-02 shipped `message_for(relative)`, not `message_for(key)` as the plan's lambda spells it. run() maps path → key and uses `commit_message(key, refused=...)`.
- **Helpers added:** `replay_sidecar(key)`, `calibration_descent()` (a local copy, as in 32-03), `MANUAL_RELAUNCH`, `_run_excludes()` and `_is_refused()`.
- **Plist header comment.** XML comments cannot contain `--`, so the comment describes the ruling flag in words ("run with the past-stop-line flag and the ruling") instead of spelling `--past-stop-line`. The file differs from the phase31 probe plist only in the header comment, Label, script path and log pair.

## Plan-premise falsifications (measured)

- **The `_light_env` fixture shape does not carry over.** `tests/test_phase31_probe.py::_light_env` patches `teach_persona._REPO_ROOT`. In run_point, `recipe_identity(leg)` runs live and computes `replay_source` as `Path(tp.DIALOG_TRAIN_BIN).relative_to(tp._REPO_ROOT)`, so that patch raised `ValueError: '.../data/dialog_train.bin' is not in the subpath of '<tmp>'`. The probe avoided it only because its `probe_plan` was precomputed and patched. The tests here patch `tp.arm_outputs` to re-root its paths under tmp instead. Plan 05's live fixtures must keep this in mind if they redirect `_REPO_ROOT`.
- No other premise was falsified. The PREREG-03 records that run() writes come from `phase29_prereg.refused_record` through `write_refused_records`, and they carry `point_key`, `control_key`, `control_recall_counts`, `recipe` and `rule`, which is exactly what 32-03's `phase32_frontier.py` consumes. The schedule test asserts `rule`, `control_key` and `control_recall_counts` on all 5.

## Notes for plan 05

- The `stop_line` heartbeat stage is not in `phase25_run.STAGES`. `beat()` does not validate stage names and nothing reads that tuple as a whitelist, so it is harmless. However, phase25_watch will see no beats after the exit, just as after `done`.
- `test_phase25_venue.py` runs the whole suite in a subprocess, so the plan-end command takes about 22 minutes, not seconds.
- No pinned module was touched: `git diff 01e69ec HEAD -- scripts/phase30_points.py scripts/teach_persona.py scripts/phase25_points.py` is empty. No committed `results/*.json` names `phase32_points.py` in a `module_sha256`.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-32-16 (no training on a refused leg, tested), T-32-17 (half-trained refusals, the replay sidecar tied to adapter_sha256), T-32-18 (the stop line), T-32-19 (the ruling refused unless at the line and recorded in provenance) and T-32-21 (plist KeepAlive/RunAtLoad false, fixed argv) are all mitigated and tested. T-32-20 is accepted: the ruling text is stored only as JSON data.

## Self-Check: PASSED

- scripts/phase32_points.py, tests/test_phase32_points.py and artifacts/com.personacore.phase32.sweep.plist exist.
- Commits 39a7026, 406766a, d598650 and 94fdd7f are present on main.
- No STATE, ROADMAP or REQUIREMENTS edits were made, and nothing was written under the real results/.
