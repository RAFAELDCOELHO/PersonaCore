---
phase: 40-m2-seed-noise-floor
plan: 02
subsystem: pre-registration
tags: [prereg, noise-01, noise-02, e2_S, e2_noise_floor_estimator, approvals, d-11, d-13, r-1, r-2, r-3, r-4]
requires:
  - results/phase36_budget.json
  - scripts/phase35_prereg.py (fill, SLOTS, seed_list)
  - scripts/phase38_prereg.py / scripts/phase39_prereg.py (E5/E6 projections, MINTED_SET_SIZE)
  - 40-CONTEXT.md at 03de080 (Approvals) and 40-DISCUSSION-LOG.md at 544ed02 (Addendum)
provides:
  - scripts/phase40_prereg.py — record paths, approval arithmetic, rulings, 17 ENTRIES, E2_S and E2_NOISE_FLOOR_ESTIMATOR fills, SEEDS
  - tests/test_phase40_prereg.py — 27 CPU tests (arithmetic, fills, ancestry, verbatim, literal scan, schema, import probe, census, skips, every function)
affects:
  - plan 03 (adds the estimator functions to scripts/phase40_prereg.py and their tests to the same test file)
  - plan 04 (review with Rafael; moves the four _UNCONFIRMED labels to his confirmed words)
tech-stack:
  added: []
  patterns: [phase39_prereg header/_prove/_prove_entry/approval_block shape, fill() as the whole module-level binding]
key-files:
  created:
    - scripts/phase40_prereg.py
    - tests/test_phase40_prereg.py
  modified: []
decisions:
  - "MappingProxyType entries passed to phase35_prereg.fill directly; no dict() fallback was needed"
  - "fresh_training entry prose names teach_persona.train_arm without an opening paren (train_arm( call-site register)"
requirements-completed: []
completed: 2026-10-05
---

# Phase 40 Plan 02: Pre-registration (first half) Summary

`scripts/phase40_prereg.py` reads S = 5 from `results/phase36_budget.json::e2_seed_count` through `phase35_prereg.fill("e2_S", ...)`. It fills `e2_noise_floor_estimator` once, with both estimators (recall_floor, gap_noise_floor) in one frozen entry. It also carries Rafael's four 40-01 quotes and the R-1..R-4 option ids, and computes the D-11/D-13 approval arithmetic at import: projection 7.9518624092864085 h, stop 11.83638889157415 h, E2 + E5 + E6 total 78.12639556620314 h. All of this was committed before any `results/phase40_*` record existed.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | f2cc033 | feat(40-02): phase40 prereg header, record paths, D-11/D-13 approval arithmetic and rulings |
| 2 | eb29160 | feat(40-02): seventeen ENTRIES, e2_S and e2_noise_floor_estimator fills, SEEDS |
| fix (Rule 1) | 04f9cd3 | fix(40-02): keep the train_arm call-site register exact — fresh_training prose names train_arm without an opening paren |
| 3 | c5518d0 | test(40-02): phase40 prereg guards — ancestry, verbatim rulings, literal scan, schema, import probe, census |

At f2cc033 (the prereg's first commit), `git ls-files 'results/phase40_*'` and `find results -maxdepth 1 -name 'phase40_*'` both printed nothing. That makes RECORDS_AT_COMMIT = 0 true.

## RED outputs

Task 1, with the six Task 1 tests written and no prereg yet (`.venv/bin/pytest -q -p no:cacheprovider tests/test_phase40_prereg.py`):
```
tests/test_phase40_prereg.py:39: in <module>
    import phase40_prereg  # noqa: E402  (same)
    ^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'phase40_prereg'
=========================== short test summary info ============================
ERROR tests/test_phase40_prereg.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.00s
```
Task 2, with the five Task 2 tests added and no ENTRIES or fills yet (`-k "e2_s or seeds or fill or sampling or entries"`):
```
FAILED tests/test_phase40_prereg.py::test_e2_s_is_read_never_typed - Attribut...
FAILED tests/test_phase40_prereg.py::test_seeds_are_the_seed_list_prefix - At...
FAILED tests/test_phase40_prereg.py::test_fill_holds_both_estimators - Attrib...
FAILED tests/test_phase40_prereg.py::test_sampling_noise_and_crn_are_declared
FAILED tests/test_phase40_prereg.py::test_entries_names_kinds_and_d_ids - Att...
5 failed, 6 deselected in 1.52s
E       AttributeError: module 'phase40_prereg' has no attribute 'E2_S'
E       AttributeError: module 'phase40_prereg' has no attribute 'SEEDS'
E       AttributeError: module 'phase40_prereg' has no attribute 'E2_NOISE_FLOOR_ESTIMATOR'
E       AssertionError: meta-guard: the sampling_noise constant was not found exactly once
E       AttributeError: module 'phase40_prereg' has no attribute 'ENTRIES'
```

## Verify and acceptance (as printed)

Task 1 verify, before commit f2cc033: `6 passed in 1.05s`; `ruff check`: All checks passed!; `ruff format --check`: 2 files already formatted.
Task 1 acceptance:
```
7.9518624092864085 11.83638889157415 77.78526798055215 True 925 results/phase40_noise_floor.json results/phase40_seed1337.json results/phase40_a2_m2_seed2024.json v6/40/E2/seed1339
```
D-13 is approved, so these are the D-13-approved values (925). `git ls-files 'results/phase40_*'` and `find results -maxdepth 1 -name 'phase40_*'` printed nothing.

Task 2 verify: `-k "e2_s or seeds or fill or sampling or entries"` gave 5 passed, 6 deselected. `tests/test_phase35_prereg.py -k "slot_census or slot_ordering"` gave 7 passed, 81 deselected. ruff: All checks passed!
Task 2 acceptance:
```
5 (1337, 2024, 1338, 2025, 1339) ['gap_noise_floor', 'recall_floor'] 17 ['e2_S', 'e2_projection_hours', 'e2_stop_hours', 'e2_total_hours']
```
`test_slot_census_is_green_on_the_real_tree` and `test_slot_ordering_is_green_on_the_real_repo` gave 2 passed in 6.45s. That run was on the committed tree, after c5518d0.

Task 3 verify, before commit, on the five plan files plus tests/test_phase23_resume.py: `180 passed in 144.65s (0:02:24)`. `ruff check .`: All checks passed!; `ruff format --check .`: 360 files already formatted.
Task 3 acceptance, after c5518d0:
- `-k "frozen or first_added or records_at_commit"` gave `3 passed, 24 deselected in 2.05s`
- `git ls-files 'results/phase40_*'` printed nothing. `git status --porcelain -- scripts tests results` printed nothing.

Record total and rulings, printed after c5518d0:
```
78.12639556620314 78.12556459250179 {'R-1': 'mps-equality', 'R-2': 'post', 'R-3': 'rerun-as-new-attempt', 'R-4': 'seed-record-names-a2'}
```

Committed-tree check, run after c5518d0. It covers the five plan files plus every test file that greps or globs scripts/ (test_phase23_resume, test_lora_inject, test_phase14_scoring, test_phase17_stats, test_phase19/20_correction, test_phase21_unit_continuation, test_phase23_ctrl, test_phase25_driver/prereg/venue, test_tokenizer_oracle, test_phase30_calibration, test_phase36_ledger):
```
446 passed in 2312.23s (0:38:32)
EXIT=0
```
tests/test_phase25_venue.py runs `pytest -q -p no:cacheprovider tests/ --ignore=tests/test_phase25_venue.py` as a subprocess (seen in `ps` during the run). So this green run also covers the whole suite at c5518d0, test_phase19_erasure.py included.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The fresh_training prose added an unregistered `train_arm(` grep hit**
- **Found during:** Task 3, while checking the repo census traps.
- **Issue:** The plan's entry text `teach_persona.train_arm(..., family_ids=...)` adds a raw `train_arm(` hit under scripts/. `tests/test_phase23_resume.py::test_resume_from_none_is_inert` requires every such hit to be listed in `_TRAIN_ARM_CALL_SITES`, so this one would have failed it.
- **Fix:** The text now says "both trained by teach_persona.train_arm with family_ids=phase14_factset.TAUGHT_FAMILY_IDS, seed=<seed>, prefix=<the driver's prefix>". The meaning is unchanged.
- **Files modified:** scripts/phase40_prereg.py
- **Commit:** 04f9cd3

**2. [Rule 1 - Bug] Calls through the local alias `p` were invisible to `_untested_functions`**
- **Found during:** Task 3
- **Issue:** The Task 1/2 tests called the prereg through a local `p = phase40_prereg`. The census counts only `phase40_prereg.<fn>(` calls, so it could not see them.
- **Fix:** Every `p.` became `phase40_prereg.`, and the alias lines were removed.
- **Commit:** c5518d0

### Notes
- Task 1's prereg left out `import types` because ruff F401 flags an unused import. Task 2 added it when ENTRIES first used it. `itertools` and `statistics` are not imported; plan 03's functions will need them.
- `phase35_prereg.fill` accepted the MappingProxyType entries directly. No `dict(...)` fallback was used.
- The Task 1 test `test_approval_d13_nll_count_is_derived` compares D13_ADAPTERS with the budget's `unit_caps.E2.seeds`, not with E2_S, because E2_S does not exist until Task 2. Both are 5, and E2_S == unit_caps.E2.seeds is proved at import.
- `_UNCONFIRMED` labels: e2_noise_floor_estimator (D-04 sample SD), a2_pass (NOISE-01, the 'retrain' label), run_order (D-15, D-13 placed last), record_layout (D-15). seed_outcomes cites R-3 and carries no label.

## Known Stubs

None. Plan 03 adds the estimator functions on purpose; this plan writes the rule, not the implementation.

## Threat Flags

None. No network, auth or file-write surface. The module reads committed JSON and git-tracked files only.
