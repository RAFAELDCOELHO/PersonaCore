---
phase: 42-dp-sgd-recipe-search-at-large
plan: 05
subsystem: driver
tags: [e3, dp-sgd, emit, report, launchagent, end-to-end, d-15, d-18, d-23]
requires:
  - scripts/phase42_prereg.py (42-01..03; called, never edited)
  - scripts/phase42_recipes.py (42-04: preflight, run, write_unit, _root_ledger, _tracked_and_clean, _write_once, _load, module_sha256)
  - scripts/phase35_prereg.py fill("e3_recall_threshold") (tests only; read, not edited)
  - scripts/phase36_ledger.py spent
  - artifacts/com.personacore.phase41.e1.plist (the template)
provides:
  - "scripts/phase42_recipes.py: _LIMITS, _thresholds, _pair, build_record, emit, _table, _k_n, render_report, report, main, the __main__ entry"
  - "artifacts/com.personacore.phase42.e3.plist (Label com.personacore.phase42.e3; RunAtLoad and KeepAlive false; not loaded)"
  - "tests/test_phase42_recipes.py: _counts, _e3_root (stage 1 -> real fill -> stage 2 on a scratch root), _measure_rig/_run_rig counts= per unit, 12 new tests"
affects: [42-06, 42-07, 42-11, 42-12]
tech-stack:
  added: []
  patterns: [phase41_erasure emit / report / main, phase41 plist mirror test, json round-trip normalisation of MappingProxyType]
key-files:
  created:
    - artifacts/com.personacore.phase42.e3.plist
  modified:
    - scripts/phase42_recipes.py
    - tests/test_phase42_recipes.py
decisions:
  - "render_report iterates RECIPES / UNITS / _LIMITS order, never dict order: atomic_write_json writes sort_keys=True (scripts/phase25_run.py:148), so the record report() loads has sorted keys"
  - "build_record proves each non-REFUSED threshold's control path equals the recipe's own control record (the v4.0 control for the reused recipe), so thresholds filled on another root are refused"
  - "inputs is {rel: sha256} (phase41 shape); the v4.0 copy is proved equal to V4_CONTROL_SHA256"
requirements-completed: []
metrics:
  duration: ~40 min
  completed: 2026-10-14
  tasks: 3
  files: 3
---

# Phase 42 Plan 05: emit, report, main and the E3 LaunchAgent Summary

The E3 driver is now wired end to end:

- `build_record` turns the 11 unit records into the E3 record. It decides labels only through `phase42_prereg.point_verdict`. Every other published number comes from a pre-registered function: table, summary, lead, ε, composition, vacuous / TPR, the descriptive and control-retention readings, d16, d17, the exact disagreements and the ENTRIES limits.
- `emit` writes that record once.
- `render_report` puts the pre-written lead on line 1. Directly after it come every point's raw recall on both legs, its own control's k/n and its ε.
- `report` renders the record only after `emit` has written it.
- `main` is traced.
- A LaunchAgent mirrors the Phase 41 one.

A scratch-root test runs the whole path: stage 1, the REAL Phase 35 threshold fill on the driver's own control records plus the byte-identical v4.0 control, stage 2, emit and report.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | 88ba969 | feat(42-05): build_record and emit — labels only through point_verdict, the prereg's table / summary / lead / epsilon / readings, write-once emit provenance |
| 2 | 04ae094 | feat(42-05): render_report with the pre-written lead first, write-once report, main and the E3 LaunchAgent |
| 3 | 659869e | test(42-05): end to end on a scratch root — stage 1, the REAL threshold fill, stage 2, emit and report |

In Tasks 1 and 2 the tests were written first and run against the previous driver state. Test and implementation then landed in one commit, as in 42-02..04. Task 3 is test-only.

## RED outputs (natural, before implementation)

- **Task 1:** `6 failed, 25 deselected in 4.16s`. Five failed with `AttributeError: module 'phase42_recipes' has no attribute 'build_record'`, one with `... no attribute 'emit'`.
- **Task 2:** `6 failed, 30 deselected in 3.76s`. Five were `AttributeError` (`render_report` / `report`). One was `FileNotFoundError: .../artifacts/com.personacore.phase42.e3.plist`.
- **Task 2, first green attempt:** 1 failed (`test_report_is_write_once_and_reads_a_committed_record`). The report rendered from the loaded file listed the control-retention lines in sorted-key order (`lr1e-03_t200` before `lr3e-04_t200`); `render_report` of the in-memory record listed them in RECIPES order. Fixed in the driver; see Deviation 2.

## End-to-end test output (Task 3)

`-s -k end_to_end` printed:

```
E2E summary='0 de 8 pontos passam; 2 REFUSED' lead='nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)'
1 passed, 36 deselected in 1.58s
```

What the test asserts:
- The v4.0 recipe's thresholds are `0.5486111111111112 / 0.3737654320987654`, filled from `results/phase25_point_dp_n8_sigma0p000000.json`.
- The `lr1e-03_t800` recipe is REFUSED.
- Stage 2 prints `p22={200: ..., 800: ...}` equal to `P22_ONSETS` and runs all 8 points.
- The tmp ledger holds 11 start/end pairs, in UNITS order, naming the 11 unit records.
- Labels: 2 REFUSED and 6 não passa.
- The report's first line is the null sentence, and the summary appears exactly once.

`-k end_to_end -v` gave `tests/test_phase42_recipes.py::test_end_to_end_on_a_scratch_root PASSED`.

## Acceptance lines, as printed

| Check | Result |
|-------|--------|
| Task 1, `-k "build_record or emit or retention"` | `6 passed, 25 deselected` (includes the D-18 test `test_worse_retention_in_a_learning_control_changes_no_label`) |
| Task 2, `-k "first_line_is_the_lead or main_traces or plist"` | `3 passed, 33 deselected` |
| Task 2, `-k "report or main or plist or worse_retention"` | `6 passed, 30 deselected` |
| `plutil -lint artifacts/com.personacore.phase42.e3.plist` | `artifacts/com.personacore.phase42.e3.plist: OK` |
| `ruff check` on both .py files | `All checks passed!` |
| `ruff format --check` on both .py files | `2 files already formatted` |

## Verification on the committed tree (after 659869e)

| Command | Result |
|---------|--------|
| Quick run, `tests/test_phase42_prereg.py tests/test_phase42_recipes.py` | `85 passed in 13.19s` |
| Census call 1, `test_phase35_prereg.py -k "slot_census or slot_ordering or grids_must or e3_"` | `13 passed, 75 deselected in 64.56s`, EXIT 0 |
| Census call 2, the nine files/nodes of VALIDATION.md line 24 | `109 passed in 107.97s`, EXIT 0 |
| Extra: the census files that glob `scripts/*.py` or `artifacts/` (phase16/20/29/36/37/38 prereg, 14_scoring, 17_stats, 23_ctrl, 21_unit_continuation, 30_calibration, 25_prereg, tokenizer_oracle, 33_admission, 37_routes, 25_driver) | `479 passed in 91.40s`, EXIT 0 |

Other checks:
- `git status --porcelain -- scripts tests results artifacts` prints nothing.
- `git ls-files 'results/phase42_*'` and `find results data checkpoints -maxdepth 2 -name '*phase42*'` print nothing.
- `git diff --quiet 02bd24d -- scripts/phase42_prereg.py scripts/teach_persona.py scripts/phase25_points.py scripts/phase35_prereg.py src` exits 0 (`PINS_OK`).
- The plist was never loaded: no `launchctl` call was made.
- The quick run's third file, `tests/test_phase42_threshold_prereg.py`, does not exist until plan 42-09.

## Deviations from Plan

1. **The D-18 test's report leg landed with Task 2, not Task 1.**
   - In Task 1, `test_worse_retention_in_a_learning_control_changes_no_label` (`tests/test_phase42_recipes.py:909`) asserts identical lead, summary, table, d17 and labels on both roots. It also asserts the worse value appears in `record["control_retention"]` with "não muda rótulo".
   - The plan also asks for "the rendered report's control-retention lines". `render_report` is Task 2, so that assertion was added in the Task 2 commit. The test still has both legs.
2. **[Rule 1 - Bug] `render_report` iterates pre-registered orders, not dict order** (`scripts/phase42_recipes.py:979`).
   - `phase25_run.atomic_write_json` serialises with `sort_keys=True` (`scripts/phase25_run.py:148`). `report()` therefore loads a record whose `controls`, `control_retention`, `exact_disagreements`, `descriptive` and `limits` keys are sorted.
   - Iterating dict order would make the published report differ from `render_report(build_record(...))`. The write-once report test caught this.
3. **[Rule 2] Extra refusals in `build_record`:**
   - A non-REFUSED threshold whose `control` is not the recipe's own control record is refused (`:823`). This blocks thresholds filled on another root.
   - The v4.0 copy must equal `V4_CONTROL_SHA256` (`:778`).
   - A point's `delta` must equal `phase35_prereg.DELTA`.
   - A recipe's points must share one denominator per leg before `exact_disagreements` runs.
   - The thresholds' keys must equal the grid's recipe keys.
4. **Test rig extension.**
   - `_measure_rig` and `_run_rig` take `counts=` (`tests/test_phase42_recipes.py:252`), mapping a unit to its own ((k, n), (k, n)).
   - The fake `score_arm` finds the unit from `/phase42rh_<unit>_` in the adapter path. Every other unit scores the old defaults, so the 42-04 tests are unchanged.
   - `_e3_root` (`:817`) runs stage 1, the real fill and stage 2 for the build_record / report tests. The end-to-end test does the same steps inline, as the plan asks.
5. **Extra test legs beyond the plan's list:**
   - A non-vacuity root where one point at the control's counts passes. Only that label moves, and the lead becomes `1 de 8 pontos passam; 2 REFUSED`.
   - A real-root leg where a passed thresholds mapping is refused ("committed fill").
   - A real-root report leg where an untracked record is refused ("committed and unmodified").
   - The second `emit` is proved to refuse before `build_record` is reached.
   - `main` with two arguments raises the docstring.
6. **Plan names checked against the code.** These resolved as written:
   - in phase42_prereg: `E3_RECORD` / `REPORT_RECORD` (`results/phase42_recipes.json` / `results/phase42_recipes_report.md`), `V4_CONTROL_COUNTS`, `V4_CONTROL_RETENTION`, `V4_CONTROL_SHA256`, `REUSED_RECIPE`, `SELECTION_ACCOUNTED`, `REFUSED`, and every ENTRIES name in the limits list;
   - `phase36_ledger.spent(ledger_path=, fronts=)` (`scripts/phase36_ledger.py:315`), called with `fronts=(FRONT,)` as phase41 does;
   - the phase41 templates `emit` / `_table` / `report` / `main` (`scripts/phase41_erasure.py:2476/2520/2938/2960`) and its plist.

   The plan's `.venv/bin/ruff` was run as `.venv/bin/python -m ruff`, per the executor brief. No misnamed artifact.
7. **Census registers: none needed.** No `train_arm`, `os.replace`, `inject_lora` or `mitigation_point_verdict` token was added (the AST gate in `tests/test_phase42_prereg.py` passes). There is no `== 10` literal. `os.chdir` is the only new `os` use. No existing test file was edited.

## Known Stubs

None. The real-root branch of `_thresholds` imports `phase42_threshold_prereg`, which does not exist until plan 42-09. That is by design, and the import is lazy. On the real root `build_record` refuses until `THRESHOLD_FILE` is tracked and clean.

## Threat Flags

None beyond the register:
- T-42-19: labels only via `point_verdict`, compared per point in the test.
- T-42-20: line 1 is `report_lead` verbatim, the summary appears once, and the hedge words are tested.
- T-42-21: provenance keys are exactly `{emitted_utc, git_sha, module_sha256}`, with no `run`.
- T-42-22: the end-to-end scratch test runs through the real fill, and `main` is traced.

## Self-Check: PASSED

- FOUND: scripts/phase42_recipes.py, tests/test_phase42_recipes.py, artifacts/com.personacore.phase42.e3.plist
- FOUND commits: 88ba969, 04ae094, 659869e
- No edits to STATE / ROADMAP / REQUIREMENTS / PROJECT, and no gsd-sdk handler called.
- No existing scripts/src module or test file edited. No `results/phase42_*` created. Nothing loaded into launchd.
