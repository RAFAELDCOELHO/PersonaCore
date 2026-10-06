---
phase: 40-m2-seed-noise-floor
plan: 06
subsystem: e2-driver
tags: [noise-floor, NOISE-01, D-15, R-3, ruling-c, preflight, run-loop]
requires:
  - "40-05: scripts/phase40_noise.py part 1 (train_adapter, score_a2, d13_scores, _repo_rig)"
  - "frozen prereg scripts/phase40_prereg.py (sha256 a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2)"
provides:
  - "preflight(): every launch refusal before the first ledger start line; one refuse_if_dirty with _launch_pathspec(outcomes) on the real root"
  - "_launch_pathspec(outcomes): the helper plan 07's emit reuses"
  - "rehearsal_identity_path / record_rehearsal / rehearsal_disclosure (phase39_ctx shape, keyed on seeds)"
  - "R-3 b: partial_outputs, drop_attempt, declare_relaunch, rerun_seeds, preflight's dropped_attempts"
  - "run(): one ledger attempt per seed, whole seeds by construction, ruling c around d13_scores"
  - "test helpers _tmp_rig, _real_root_rig, _ledger, _run_fakes, _measured, _attempt_entry; autouse tracked_files stub"
affects: [40-07, 40-08, 40-09, 40-10]
tech-stack:
  added: []
  patterns: [refusals-before-start-line, write-once manifests, move-never-delete, AST ledger-call gate]
key-files:
  created: []
  modified:
    - scripts/phase40_noise.py
    - tests/test_phase40_noise.py
decisions:
  - "run() refuses a missing rehearsal_identity and a kept identity of another seed set BEFORE the first start line, not after it in record_rehearsal: a refusal after the start would leave an open attempt"
  - "run() refuses a rehearsal_identity argument on the real root, so it is never silently ignored"
  - "a rehearsal root requires device='cpu' passed explicitly (checked in the real-root guard, before any I/O)"
  - "PREFLIGHT OK prints pending comma-joined (pending=1337,2024), so the line has no space inside a field"
requirements-completed: []
metrics:
  duration: "~18 min (HEAD 701015b 09:48 -> 53c0e5d 10:06 -0300)"
  completed: 2026-10-06
  tasks: 3
  files: 2
---

# Phase 40 Plan 06: E2 driver part 2 (preflight, R-3 b, run) Summary

`preflight()` now makes every refusal before the first start line. `run()` writes one ledger attempt per seed, and each seed is a whole unit: train full, train M2, A2 full, A2 M2, D-13 last, the write-once seed record, then the end line that names it. Ruling c is enforced by catching D-13 failures (SystemExit included) around the `d13_scores` call and nowhere else. The R-3 b drop/re-run path moves a crashed attempt's outputs aside, never deletes them, and writes a write-once manifest for them. A dropped seed is pending again only once that manifest exists. All of this is tested on CPU with fakes, against tmp roots and a patched real-root rig.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1: preflight, rehearsal identity + disclosure, `_launch_pathspec` | f05fcb1 | scripts/phase40_noise.py, tests/test_phase40_noise.py |
| 2: R-3 b partial_outputs / drop_attempt / declare_relaunch / rerun_seeds + preflight legs | 6c4c22f | scripts/phase40_noise.py, tests/test_phase40_noise.py |
| 3: run(), the refusal table through run(), the AST ledger-call gate | 53c0e5d | scripts/phase40_noise.py, tests/test_phase40_noise.py |

## RED evidence

- Task 1, with the tests written and the functions not yet present:
  ```
  54 failed, 28 deselected in 5.41s
     6 E           AttributeError: module 'phase40_noise' has no attribute 'record_rehearsal'
     1 E       AttributeError: module 'phase40_noise' has no attribute '_launch_pathspec'
    46 E       AttributeError: module 'phase40_noise' has no attribute 'preflight'
     1 E       AttributeError: module 'phase40_noise' has no attribute 'rehearsal_identity_path'
  ```
  The first GREEN attempt had 1 failure, `test_preflight_refusals[open_attempt]`. The message read ``…`phase36_ledger.py reconcile` first`` with backticks, and the row expected the plan's text `phase36_ledger.py reconcile first`. I fixed the message to match: `54 passed, 28 deselected`.
- Task 2:
  ```
  3 failed, 82 deselected in 1.92s
     2 E       AttributeError: module 'phase40_noise' has no attribute 'drop_attempt'
     1 E       AttributeError: module 'phase40_noise' has no attribute 'partial_outputs'
  ```
- Task 3. The refusal table was switched to go through `run()`, and the run tests were appended:
  ```
  65 failed, 37 passed in 9.11s
    52 E           AttributeError: module 'phase40_noise' has no attribute 'run'
    12 E           AttributeError: module 'phase40_noise' has no attribute 'run'
     1 E       AssertionError: assert {'append', 'o...quire_launch'} <= {'open_runs',...quire_launch'}
  ```
  The last failure is the AST gate's non-vacuity leg: `append` was not called by the driver yet.

## Verify / acceptance outputs

Task 1:
- `pytest tests/test_phase40_noise.py -k "preflight or rehearsal"` -> `54 passed, 28 deselected in 4.74s`; `ruff check` -> `All checks passed!`
- `-k "relaunch_pathspec or real_git_rig"` -> `2 passed, 80 deselected in 1.55s`
- AST `refuse_if_dirty` call count -> `1`
- whole file -> `82 passed in 6.46s`

Task 2:
- `-k "preflight or rehearsal or drop_attempt or rerun_needs"` -> `57 passed, 28 deselected in 5.45s`; ruff -> `All checks passed!`
- `-k "drop_attempt or rerun_needs"` -> `3 passed, 82 deselected in 1.82s`
- AST `refuse_if_dirty` call count -> `1`
- whole file -> `85 passed in 8.12s`

Task 3:
- `pytest tests/test_phase40_noise.py tests/test_phase36_ledger.py tests/test_phase23_resume.py tests/test_phase21_sc5.py` -> `160 passed in 115.49s (0:01:55)`
- `ruff check .` -> `All checks passed!`; `ruff format --check .` -> `362 files already formatted`
- `-k "order or whole_seed or crash or stop"` -> `19 passed, 83 deselected in 3.42s`
- `grep -c "train_arm(" scripts/phase40_noise.py` -> `1`
- key_links: `grep -cE "phase36_ledger[.]require_launch[(]FRONT"` -> `2` (preflight and run); `grep -cE "record=prereg[.]seed_record[(]seed[)]"` -> `1`
- AST `refuse_if_dirty` call count -> `1`
- Census grep (`== 10|!= 10|os.replace|inject_lora`) over both files: no hits
- After commit 53c0e5d: `git status --porcelain -- scripts tests results ledger` -> empty. `git diff --quiet -- ledger/v6_mps_ledger.jsonl` -> clean (`LEDGER_CLEAN`). `ls -la data/v6_mps_heartbeat.jsonl` -> mtime `5 out 13:28`, untouched. No `data/phase40_rehearsal.json` and no `checkpoints/*e2_*` (`0`).
- Clean-tree probes after the commit: `tests/test_phase25_driver.py tests/test_phase36_caps.py` -> `59 passed in 3.68s`
- Prereg digest after all three commits: `a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2  scripts/phase40_prereg.py` (unchanged)

The full suite was not run because the plan does not ask for it.

## Deviations from Plan

1. **[Rule 2] Rehearsal identity refusals moved ahead of the first start line.** The plan has `record_rehearsal` refuse a different seed set, and the tests' hazard (2) has a `None` identity raise there. Both happen after the first seed's start line, so either refusal would leave an open attempt that reconcile turns into a lost line. `run()` now proves `rehearsal_identity is not None` and calls `_kept_identity(rehearsal_identity, seeds=seeds)` right after preflight, before the loop. That is the phase39_ctx DR-02 placement. The identity is still written after the first start line, as planned. On the real root, `run()` refuses a non-None `rehearsal_identity`. Commit 53c0e5d.
2. **The refusal table goes through `run()`, not `preflight()` alone.** In Task 1 it called preflight. In Task 3 the `_launch` helper switched to `run()`, with train/score/d13 recorders that must stay empty. This proves the behaviour's "no ledger line, no heartbeat, no fake train/score call" end to end. The missing-input and existing-output tables use the same helper.
3. **Rows added beyond the listed set:** a tmp root with device "mps", a tmp root without seeds, seeds out of order, an explicit ledger on the real root, the existing checkpoint and mask of a pending seed (both groups), and "nothing to run". Each asserts its own message.
4. **PREFLIGHT OK prints `pending=1337,2024`** (comma-joined), not the tuple's repr.
5. **`partial_outputs` is built on a small `_output_roots(seed, *, root)`.** `drop_attempt` uses it to rmdir exactly the directories its moves emptied (never rmtree). The R-3 b preflight legs live in `_dropped_attempts(...)`, and `drop_attempt` and `declare_relaunch` share `_latest_dropped_dir(...)`. The ruling-c region is inline in `run()`, as the plan says.

## For plan 07 (not acted on here)

Plan 07 adds `_untested_functions("phase40_noise", ...)`, which requires a direct `phase40_noise.<def>(...)` call in tests. Measured on 53c0e5d, the defs with no direct call are `_device, _dropped_attempts, _kept_identity, _latest_dropped_dir, _load, _now, _output_roots, _prereg, _prove, _rel, _release, _target_fact_id, arm_spec`. Before the inlining, the list also had `_d13_or_not_measured`. That helper no longer exists.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-40-20/21: require_launch runs before every seed, one start line per seed, a heartbeat beat before the thread starts, no `rule` or `reconcile` call (AST gate). T-40-22/47: the seed record is written before the end line, drop_attempt moves outputs and never deletes them, the manifest is checked before the first move, and preflight checks every lost attempt's manifest. T-40-23: DR-01 disjointness, and the real root refuses subsets, non-mps devices and an explicit ledger. T-40-46: exact-pathspec test plus a real-git rig. T-40-49: six parametrized D-13 failure items plus the KeyboardInterrupt crash. T-40-45: a zero-argument `run()` on the rig.

## Self-Check: PASSED

- FOUND: scripts/phase40_noise.py, tests/test_phase40_noise.py (modified)
- FOUND commits: f05fcb1, 6c4c22f, 53c0e5d
