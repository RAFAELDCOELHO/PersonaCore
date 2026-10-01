---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
plan: 02
subsystem: prereg
tags: [prereg, ancestry, seeds, erasure, audit, ast-guard]

requires:
  - phase: 35-01
    provides: phase35_prereg skeleton (_prove, _prove_real, entry schema), tests/test_phase35_prereg.py helpers (_git_in, _planted_repo, _insert_at, _entries_node)
  - phase: 29 (v5.0)
    provides: tests/test_phase29_prereg.py helpers (_assert_frozen_before, _git, _module_targets, _numeric_constants, _planted)
provides:
  - V6_RESULT_PATHS + derived ARTIFACT_PATHSPECS (results/phase36_* .. results/phase45_*)
  - closed pins by attribute (F_Y, F_C, DIALOGUE_GAP_BAND, CEILING_CLAUSE, STEP_BUDGET, CURVE_K, FULL_FIDELITY_K, SIGMA_LADDER, MARGIN_K)
  - seed_list(), e1_teaching_seeds(), e1_targets(), audit02_cut(), e4_runs(), e1_condition_b_margin(), R1A_ASSERTIONS, r1a_rederive(), E3_SIGMAS, a2_corpus_entries()
  - 14 new core ENTRIES (18 total)
affects: [35-03, 35-04, 35-05, phases 36-45]

tech-stack:
  added: []
  patterns:
    - "Record paths in ONE tuple; ancestry pathspecs derived from it"
    - "Values read from records/sources at call time; AST literal census derived from the live sources"

key-files:
  created: []
  modified:
    - scripts/phase35_prereg.py
    - tests/test_phase35_prereg.py

key-decisions:
  - "Planted literal/binding REDs are built from repr() of the live values (seed tuple, cut, F_Y, F_C, first target) rather than retyped in the test; the resulting text is identical to the plan's literals"

requirements-completed: []
# The orchestrator ticks requirements at phase close; this plan's `requirements:` list
# (PREREG-05, PREREG-06, PREREG-07) names IDs it contributes to, not IDs it closes.

duration: 6min
completed: 2026-10-01
---

# Phase 35 Plan 02: v6.0 core Summary

**The v6.0 core is now code, committed before any v6.0 record exists. It holds the record paths with derived ancestry pathspecs, the closed pins bound by attribute, `seed_list()` returned by identity, the E1 targets read from TARGET_RANKING, the AUDIT-02 cut read from the canary record, the R1a assertions cross-checked against the erased record, and the (b) margin read from the noise-floor record. 16 new CPU tests cover it, including three AST guards that were watched going RED on planted copies.**

## Performance

- **Duration:** about 6 min (base 792842d at 18:29:14 -0300; feat commit fa605e3 at 18:35:02 -0300)
- **Tasks:** 3, committed together in one feat commit
- **Files modified:** 2

## V6_RESULT_PATHS as committed (fa605e3)

```python
V6_RESULT_PATHS = (
    "results/phase36_probe_*.json",  # COST-01
    "results/phase36_budget.json",  # COST-02
    "results/phase37_*",  # REPRO-01..03
    "results/phase38_minting*.json",  # RANK-01
    "results/phase38_*",  # RANK-02
    "results/phase39_*",  # CTX-01..03
    "results/phase40_*",  # NOISE-01/02
    "results/phase41_calibration_*.json",  # ERASE-06
    "results/phase41_band_inputs_*.json",  # ERASE-09
    "results/phase41_*",  # ERASE-03..10
    "results/phase42_control_*.json",  # RECIPE-01/03, the sigma = 0 controls
    "results/phase42_*",  # RECIPE-01..04
    "results/phase43_*",  # AUDIT-01..03
    "results/phase44_*",  # PKG-01..08
    "results/phase45_*",  # RPT-07..09
)
```

`ARTIFACT_PATHSPECS` (derived) = `('results/phase36_*', ..., 'results/phase45_*')`, 10 entries.

ENTRIES (18): `F_C, F_Y, audit02_cut, audit03_ceiling_clause, delta, dialogue_gap_band, e1_condition_b_margin, e1_targets, e1_teaching_seeds, e3_composition, e3_selection_accounted, e3_sigmas, e4_runs, e5_max_set_size, mps_ceiling_hours, one_run_tolerance, r1a_assertions, seed_list`.

## Acceptance results (tool output)

- Task 1 verify, line 1: `results/phase36_* results/phase45_* 10 False`
- Task 1 verify, line 2: `('pet_name', 'cat_name', 'street', 'sibling_name') (1337, 2024, 1338, 2025, 1339) 3.7965357228934966 0.2962962962962963 {'k': 78, 'destroyed_pct': 77.6370113463966, 'margin': 0.2962962962962963}`. ruff check reported "All checks passed!" and format reported "1 file already formatted".
- `e4_runs(3.7965357228934966), e4_runs(3.8)`: `False True`. `len(a2_corpus_entries())`: 216.
- After Task 1, `tests/test_phase35_prereg.py`: 23 passed.
- Task 2 verify (`-k "frozen_before or pathspecs or seed_ladder or e1_targets or audit02 or r1a or entries or by_reference"`): 17 passed, 22 deselected, 0 skipped. Per-selector `--collect-only` counts: frozen_before 1, pathspecs 2, seed_ladder 2, e1_targets 1, audit02 1, r1a 2, entries 6.
- Task 3 `-k "pins_imported or retyped or by_attribute or no_proposer"`: 4 passed, 35 deselected, 0 skipped.
- Task 3 verify: `tests/test_phase35_prereg.py tests/test_phase29_prereg.py` gave 119 passed. `ruff check .` reported "All checks passed!" and `ruff format --check .` reported "327 files already formatted".
- After commit fa605e3 on a clean tree (the dirty filter printed nothing, and `git status --porcelain -- scripts/ tests/` was empty): `tests/test_lora_inject.py tests/test_phase25_driver.py tests/test_phase21_sc5.py tests/test_phase30_calibration.py tests/test_phase23_ctrl.py` gave 71 passed.
- After the commit, the whole `tests/test_phase35_prereg.py` file gave 39 passed. `git ls-files 'results/phase3[5-9]_*' 'results/phase4[0-5]_*'` printed nothing.
- Census greps (`== 10`/`!= 10`, sigma0/seam_off/dp_fn, os.replace, inject_lora, train_arm(, train_never_taught, privacy_n) found nothing in either file.

## Premises re-measured

All of the orchestrator's pre-measured premises held: the tags v4.0 and v5.0 exist; the first add of phase23_run.py is 5303819632646f156b90fcfec850cebdfb5d1275; the canary record has 11 qualifying points with min 3.7965357228934966; there are 216 A2 prompts; `config.k` is 48 and there are 78 ablated components. No premise was falsified.

## Task Commits

1. **Tasks 1-3: v6.0 core + tests + AST guards**: `fa605e3` (feat). It touches only `scripts/phase35_prereg.py` and `tests/test_phase35_prereg.py`.

## Deviations from Plan

1. **Planted texts are built from live values.** The plan types the plant text as `return (1337, 2024, 1338, 2025, 1339)`, `return 3.7965357228934966`, `_T = "pet_name"`, `0.7` and `F_C = 0.5`. The tests instead build each one from `repr()` of the live value (`seed_list()`, `audit02_cut()`, `e1_targets()[0]`, `mitigation_gate.F_Y`/`F_C`). The text is identical, and the test file does not retype the seeds. The values that are deliberately typed in tests (3.7965..., 0.2962..., 78, 48, 77.637..., 0.7/0.5 at the v4.0 tag, the four target names) are the ones the plan asks to assert.
2. **`_literal_failures(source, seeds, floats, names)`** takes the derived census sets as arguments, which `_forbidden_literals()` computes from phase23_run, the canary record, the noise-floor record and `e1_targets()`. The plan wrote it as `_literal_failures(source)`. Behaviour is the same.
3. **Plants are line-anchored, with one byte-aware span.** Each plant edits whole lines at the AST node's `lineno`/`end_lineno` through a small `_replace_lines` helper, indented to `col_offset` (ASCII spaces). The F_Y entry-value span replacement uses UTF-8 byte columns, following the 35-01 rule.
4. **Import comments re-ordered.** After `ruff --fix` isort-ordered the top-level imports, the `(needs the sys.path insert above)` comment moved to the new first import, `erasure_gate`.
5. **Extra assertions.** `test_entries_label_f_y_and_f_c_as_preferences` also asserts that `dialogue_gap_band`'s value `is mitigation_gate.dialogue_gap_band` and that `F_C` equals `mitigation_gate.F_C`.

## Known Stubs

None.

## Threat Flags

None. The reads are `json.loads` of committed records through module constants (T-35-09), as the threat model states.

## Self-Check: PASSED

- FOUND: scripts/phase35_prereg.py, tests/test_phase35_prereg.py (modified in fa605e3)
- FOUND commit: fa605e3
