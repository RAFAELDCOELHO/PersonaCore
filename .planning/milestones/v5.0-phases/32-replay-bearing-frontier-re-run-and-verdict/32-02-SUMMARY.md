---
phase: 32-replay-bearing-frontier-re-run-and-verdict
plan: 02
subsystem: v5.0 sweep driver library (scripts/phase32_points.py)
tags: [driver, record-contract, d-03-clock, d-08, write-once, one-path-commit, ast-gate]
requires: ["32-01"]
provides:
  - "measure_stage: D-01/D-02 recall for every point via dict(plan, is_control=True)"
  - "build_point_record: the phase32_point/1 record satisfying own_control, control_floors, control_dialogue_pair, flat_record, the baseline source and the D-03 clock"
  - "cumulative_seconds / stop_line_seconds over committed blobs"
  - "record_session / prove_pinned_unchanged (D-08, WR-02)"
  - "write_point_record (write-once), commit_path / commit_untracked (D-11)"
affects: [32-04, 32-05]
tech-stack:
  added: []
  patterns: [import-and-override of frozen stages, three-root layout (_ROOT/_GIT_ROOT/_CODE_ROOT), literal-argv git surface bounded by AST]
key-files:
  created:
    - scripts/phase32_points.py
    - tests/test_phase32_points.py
  modified: []
decisions:
  - "PINNED_MODULES membership rule: the file's bytes can change a stage's numbers. Verdict-only modules (phase25_verdict, phase25_promotion, phase20_gate_coverage) are pinned by the frontier's provenance in plan 03, not here"
  - "write_point_record adds record['training']['git_sha'] to the D-08 sha set itself, so the caller passes only the session shas"
  - "build_point_record also refuses early on what own_control will later check (seed agreement, replay expected == recipe replay_windows, steps == max_steps) and on a measured/trained adapter_sha256 mismatch"
  - "commit_path additionally resolves the path and refuses a results/../ escape"
requirements-completed: []
# This plan contributes to AFRONT-01 (the driver library the run loop binds to) but does not complete it; plans 04/05 wire and prove the loop.
metrics:
  duration: ~35 min
  completed: 2026-09-27
  tasks: 2
  files: 2
---

# Phase 32 Plan 02: v5.0 driver library Summary

`scripts/phase32_points.py` now holds every AFRONT-01 invariant that does not need the run loop. That covers D-01 recall-on through the frozen stage, the record builder that satisfies all downstream readers, the D-03 clock over committed records, the stop line read from the committed budget, the D-08 session-sha check, the write-once write and the D-11 one-path commit. The module is torch-free at import, and its tests are CPU-only.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 RED | `4e425fc` | tests/test_phase32_points.py |
| 1 GREEN | `1e1fdd4` | scripts/phase32_points.py |
| 2 RED | `157e91a` | tests/test_phase32_points.py |
| 2 GREEN | `e492486` | scripts/phase32_points.py |

## Signatures as shipped (plans 04/05 bind to these)

```python
_ROOT, _GIT_ROOT            # patchable (data/ sidecars; results repo). Patch _GIT_ROOT together with phase30_points._ROOT.
_CODE_ROOT                  # never patched
INSTRUMENT_GIT_SHA = git_sha()
PINNED_MODULES: tuple[str, ...]      # 23 paths relative to _CODE_ROOT
BUDGET_PATH                          # derived from phase29_prereg.V5_RESULT_PATHS
ALLOWED_GIT_ACTIONS = ("add", "commit")
READ_ONLY_GIT_ACTIONS = ("ls-files", "show", "rev-parse", "status", "diff", "log", "merge-base")
SCHEMA = "phase32_point/1"; REQUIREMENT = "AFRONT-01"
STAGES = ("train", "measure", "recall", "draw", "score")
TRAINING_FIELDS  # seconds, resumed_from_step, checkpoint_step, csv_sha256, final_train_loss,
                 # ppl_adapter_on, ppl_adapter_off, train_config, git_sha, adapter, clip_bind_count
RECALL_FIELDS    # {taught_recall: taught, heldout_recall: heldout, taught_recall_off: taught_off,
                 #  heldout_recall_off: heldout_off, per_family_gain: per_family_gain}

measure_stage(plan, training) -> blob
stage_seconds(training, measured, blob, score_seconds) -> {stage: {"seconds": float}}
build_point_record(plan, *, recipe, training, measured, replay, blob, per_question, scored,
                   score_seconds, control_gap, draws_cache, provenance) -> dict
    # training = the FULL train_stage blob (needs adapter_sha256 too); replay = {per_step,
    # expected_per_step, steps, teaching_windows_per_step}; provenance is stored as passed.
tracked_results() -> list[str]            # git ls-files results, cwd=_GIT_ROOT
cumulative_seconds(tracked) -> float
stop_line_seconds(tracked) -> float
sessions_sidecar(key) -> Path             # _ROOT/data/phase32_<key>_sessions.json
record_session(key) -> list[{"git_sha", "started_utc"}]
prove_pinned_unchanged(shas) -> None
write_point_record(key, record, *, shas) -> str   # the relative path; D-08 also checks record["training"]["git_sha"]
commit_message(key, *, refused=False) -> str      # "feat(32): record sweep point <key>" / "... PREREG-03 refused point <key>"
commit_path(relative, message) -> str             # the new HEAD sha
commit_untracked(paths, message_for) -> list[str] # message_for: callable(relative) -> str
```

Record keys: schema, requirement, point_key, arm, axis, axis_value, q, clip_norm, is_control, control_key, seed, recipe, composed_steps, training, taught_recall, heldout_recall, taught_recall_off, heldout_recall_off, per_family_gain, condition_c, capability, gate05_gaps, zero_extraction_has_nll, per_family_counts, per_question, draws_per_question, draws_per_question_source, adapter_sha256, raw_draws, replay, stages and provenance.

## Tests run

- tests/test_phase32_points.py: **28 passed**.
- The census gate (10 tests) passed after Task 1 and again after Task 2.
- Plan end, `tests/test_phase32_points.py tests/test_phase29_prereg.py tests/test_phase30_points.py tests/test_phase31_budget.py`: **166 passed**.
- Repo-wide census files (every `tests/*.py` matching `glob|rglob`, 53 files, run after the final code commit e492486): **1449 passed**, 0 failed, 0 skipped, in 6 min 19 s.
- ruff check and ruff format --check are clean on both files.

## TDD gate compliance

Both tasks have a `test(...)` commit followed by a `feat(...)` commit. Task 1's RED was a collection error, because the module did not yet exist. Task 2's RED was 12 failing tests. The census test was green at RED, since that is a property of the existing files.

## Deviations from Plan

- **[Rule 2] Extra refusals in build_point_record.** The builder also refuses a seed mismatch across plan, recipe and train_config, a replay whose `expected_per_step` / `steps` differ from the recipe's `replay_windows` / `max_steps`, and a measured adapter sha that differs from the trained one. Each of these would otherwise surface only later, at own_control read time, on a record that is already committed.
- **[Rule 2] commit_path resolves the path.** It refuses `results/../x`, which the plan's `startswith("results/")` check alone would admit.
- **commit_message helper added.** It is the single source for the two commit-message formats the plan fixes.
- **Task 2's acceptance check `git show --name-only HEAD` lists only scripts/phase32_points.py.** The test file landed in the preceding RED commit `157e91a`, because of the TDD split. The two commits together touch exactly the two planned files.

## Plan-premise notes

- The prior-wave stale-pin hazard does not apply here. Nothing in this module reads `module_sha256` from the Phase 31 records.
- No frozen module was touched. `git diff 0d3e617 HEAD -- scripts/phase25_points.py scripts/teach_persona.py scripts/phase30_points.py` is empty.

## Known Stubs

None. `provenance` is passed through as given. Plan 04 fills its session and stop_line fields, as the plan specifies.

## Threat Flags

None beyond the plan's register (T-32-05..09 are all mitigated in code and tested).

## Self-Check: PASSED

- scripts/phase32_points.py and tests/test_phase32_points.py exist.
- Commits 4e425fc, 1e1fdd4, 157e91a and e492486 are present on main.
- No STATE, ROADMAP or REQUIREMENTS edits were made.
