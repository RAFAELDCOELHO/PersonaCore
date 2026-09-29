---
phase: 29-v5-0-pre-registration-and-carried-debt
plan: 01
subsystem: pre-registration
tags: [prereg, ancestry-guard, ast-guard, advr, debt-04]
requires: [phase25_record.point_key, phase20_gate_coverage.corrected_point_verdict, teach_persona.replay_window_budget]
provides: [phase29_prereg.ADVR_ARMS, phase29_prereg.POINT_KEYS, phase29_prereg.V5_RESULT_PATHS, phase29_prereg.ARTIFACT_PATHSPECS, phase29_prereg.replay_windows, phase29_prereg.control_is_unlearnable, phase29_prereg.refused_record, phase29_prereg.NAMED_LIMITATIONS]
affects: [29-03 (reads NAMED_LIMITATIONS["TD-16-R1-REPORT"]), 29-04 (adds the D-15-dependent half), phases 30-34 (import keys/paths)]
tech-stack:
  added: []
  patterns: [phase27_prereg register, derived pathspecs, lazy torch import, AST guard watched RED on tmp_path copy]
key-files:
  created: [scripts/phase29_prereg.py, tests/test_phase29_prereg.py]
  modified: []
decisions:
  - "RESOLVED CHOICE (open question 3): ADVR_ARMS = (advr_n8, advr_n64) lives in phase29_prereg and is the seam Phase 30 imports; never appended to teach_persona.ADV_ARMS"
  - "RESOLVED CHOICE (assumption A1): V5_RESULT_PATHS filenames = phase30_calibration, phase31_probe_point, phase31_probe_relearn, phase31_budget, phase32_point_*.json, phase32_frontier, phase33_admission, phase33_*, phase34_*"
requirements-completed: []
duration: ~40min
completed: 2026-09-24
---

# Phase 29 Plan 01: v5.0 pre-registration body (D-15-independent) Summary

`scripts/phase29_prereg.py` freezes the 12 `advr` keys (a wrapper around `phase25_record.point_key`), every v5.0 results path and the ancestry pathspecs derived from them, the replay recipe (imported lazily from the DP call site: 32 windows at n=8, 256 at n=64), the gate route, F_Y and the grid by reference, the unlearnable-own-control predicate with the REFUSED record shape, and the DEBT-04 and TD-16-R1 named limitations. No v5.0 number exists yet.

Requirements: this plan contributes to PREREG-01, PREREG-03, PREREG-04 and DEBT-04 but does not close them. The D-15-dependent half (admission contract, verdict tuple, scope rule, D-09 pins, promotion) is Plan 04's, after the ruling.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | f517c58 | feat(29-01): v5.0 pre-registration body (keys, paths, replay, refusal) |
| 2 | e4bdca6 | test(29-01): pre-registration ancestry, keys, paths, by-reference, refusal |
| 3 | 63ca8de | test(29-01): AST guards with watched RED and DEBT-04 accountant census |

## Resolved choices for the D-15 checkpoint (Plan 04 can veto them)

1. **ADVR_ARMS seam.** `ADVR_ARMS = ("advr_n8", "advr_n64")` is defined in `phase29_prereg` and Phase 30 imports it from there. It must never be appended to `teach_persona.ADV_ARMS`. `phase25_record.parse_point_key` and `phase27_prereg.arm_of` refuse all 12 keys (tested).
2. **V5_RESULT_PATHS filenames.** `results/phase30_calibration.json` (ARECIPE-02), `results/phase31_probe_point.json` (ARCAL-01), `results/phase31_probe_relearn.json` (ARCAL-02), `results/phase31_budget.json` (ARCAL-03), `results/phase32_point_*.json` (AFRONT-01), `results/phase32_frontier.json` (AFRONT-02), `results/phase33_admission.json` (ADMIT-02), `results/phase33_*` (RELRN-06..09), `results/phase34_*` (RPT-04). `ARTIFACT_PATHSPECS` is derived from this list and equals `results/phase30_*` through `results/phase34_*`.

## Verification (measured)

- Torch-free import probe: `False False 12 ('results/phase30_*', …, 'results/phase34_*') 32 256`.
- AST literal scan for 4 / 0.7 / 1.9090909090909092 in the module: `[]`.
- Keys: first `advr_n8_ratio0p000000`, last `advr_n64_ratio1p909091`, `control_key('n64')` = `advr_n64_ratio0p000000`.
- Route differential on the frontier's `adv_n64_ratio0p000000` kwargs: at heldout 0/648 the route raises SystemExit with both `COVERAGE_FLOOR_REFUSAL_MARKERS` and the predicate returns True. At 1/648 the route returns `INCONCLUSIVE` and the predicate returns False.
- `tests/test_phase29_prereg.py`: 29 passed, 0 skipped. The skip AST check prints `[]`, and `grep -cE "[=!]= 10"` prints 0.
- Repo censuses: `test_mitigation_point_verdict_has_no_caller_outside_this_module`, `test_wall_census_is_the_measured_set`, `test_os_replace_appears_only_in_the_two_phase25_writers` and `tests/test_lora_inject.py` gave 20 passed together with the 5 Task-3 tests. The whole-`scripts/` census files (`test_phase14_scoring`, `test_phase17_stats`, `test_phase23_ctrl`, `test_phase21_unit_continuation`, `test_phase20_correction`, `test_phase25_driver`) gave 156 passed on the committed tree.
- `git diff` on the frozen modules is empty. `find results -name 'phase3*'` finds 0 files.

## Deviations from Plan / plan-vs-code mismatches

1. **The ledger's source path is stale.** The P22-WARNING-4/5 rows in `results/phase28_ledger.json` give their source as `.planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-VERIFICATION.md:149-183`, and that path no longer exists. The file now sits at `.planning/milestones/v4.0-phases/22-dp-sgd-core-accountant-and-the-correctness-battery/22-VERIFICATION.md`. The module uses the path resolved with ls, as the plan instructs. The ledger is frozen and was not touched. The test resolves `source` with a glob.
2. **`phase16_persistence.d28_note()` does not exist yet.** Plan 03 (DEBT-02) adds it. The `TD-16-R1-REPORT` entry names it ahead of time, as the plan text specifies.
3. **Tests beyond the plan list:** a `point_record_path` refusal test (T-29-03), a check that `replay_windows` refuses 0, a bool or a float, and parametrized refusal cases. None of them loosens anything.
4. **Pytest command:** the plan's `.venv/bin/pytest` was replaced by `.venv/bin/python -m pytest`, per the repo gate. Results are the same.

No auto-fixes were needed. No frozen module changed.

## Known Stubs

None. The module has no D-15-dependent placeholder, by design.

## Self-Check: PASSED

- FOUND: scripts/phase29_prereg.py, tests/test_phase29_prereg.py
- FOUND: f517c58, e4bdca6, 63ca8de
