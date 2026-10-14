---
phase: 42-dp-sgd-recipe-search-at-large
plan: 03
subsystem: prereg
tags: [prereg, e3, dp-sgd, verdict, epsilon, composition, d-16, d-17, d-18, d-23]
requires:
  - scripts/phase42_prereg.py (42-01/42-02: RECIPES, NOISED_SIGMAS, CONTROL_SIGMA, POINT_UNITS, REUSED_RECIPE, unit_cell, recipe_tag, sigma_tag, ENTRIES, _V4, _RECALL_POINTS, _V4_NOISED_KEYS, _prove, _prove_count)
  - scripts/phase29_prereg.py REFUSED (read, not edited)
  - scripts/phase25_epsilon.py point_epsilon_for_sigma (read, not edited)
  - scripts/phase35_prereg.py CURVE_TOTAL, SELECTION_ACCOUNTED, DELTA, F_Y (read, not edited)
provides:
  - "scripts/phase42_prereg.py: PASSA, NAO_PASSA, REFUSED, LABELS, _rate, point_verdict, _prove_verdicts, table, _field, descriptive_reading, V4_CONTROL_RETENTION, control_retention_row, summary_line, null_line, report_lead"
  - "scripts/phase42_prereg.py: SELECTION_ACCOUNTED, point_epsilon, composition, vacuous_bound, tpr_reading, exact_disagreements, V4_RECIPE_POINT_READINGS, d16_side_by_side, d17_reading"
affects: [42-04, 42-05, 42-06, 42-11, 42-12]
tech-stack:
  added: []
  patterns: [phase41_prereg pair_label / summary_counts shape, fractions.Fraction exact comparison (phase41 exact_rate), AST read-set gate with _docstring_nodes exclusion]
key-files:
  created: []
  modified:
    - scripts/phase42_prereg.py
    - tests/test_phase42_prereg.py
decisions:
  - "point_verdict proves both recall pairs well-formed before the REFUSED check, so a malformed record is refused even on a REFUSED recipe"
  - "tpr_reading computes log10((1-δ)e^-ε) in log space; exp(ε) overflows float64 at the grid's largest ε (1840.29)"
requirements-completed: []
metrics:
  duration: ~25 min
  completed: 2026-10-14
  tasks: 2
  files: 2
---

# Phase 42 Plan 03: verdict, table, readings, summary, null lead and every epsilon reading Summary

`scripts/phase42_prereg.py` now holds the functions that turn Phase 42 records into the answer, all written before any record exists:
- the per-point verdict, where REFUSED comes only from the fill;
- the 4 x 2 table, with each recipe's own sigma = 0 control recall k/n beside the labels (D-23);
- the descriptive and control-retention readings (D-13, D-18);
- the summary line and the null lead (D-14, D-15);
- per-point ε, basic composition, the biased-coin bound and the TPR rearrangement (D-11, RECIPE-02);
- the exact-rational disagreement enumeration (Pitfall 6);
- the D-16 / D-17 readings.

Plan 05's emit only has to call these functions.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | c153ca7 | feat(42-03): point verdict, 4 x 2 table with each recipe's control recall, descriptive and control-retention readings, summary line and null lead |
| 2 | ccb81c5 | feat(42-03): epsilon, composition, vacuous and TPR readings, exact-rational enumeration, D-16 / D-17 readings |

In each task the tests were written and run against the previous state of the prereg first. Test and implementation then landed in one commit, as the plan's "commit both files" asks (same as 42-02).

## RED outputs (natural, before implementation)

- Task 1: the seven new tests ran against the 42-02 prereg and gave `7 failed, 35 passed in 4.14s`:
  - six failed with `AttributeError: module 'phase42_prereg' has no attribute ...` (`null_line`, `PASSA`, ...);
  - `test_point_verdict_reads_only_recall` failed with `ValueError` (no `point_verdict` FunctionDef to unpack).
- Task 2: the six new tests ran against the Task-1 prereg and gave `6 failed, 42 passed in 4.15s`, all `AttributeError`.

## Acceptance lines, as printed

Task 1:
```
nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)
0 de 8 pontos passam; 0 REFUSED
passa
```
- Task 1 verify, `-k "verdict or table or descriptive or retention or summary or lead or typed or census or forbidden"`: `13 passed, 29 deselected`. Ruff check gave `All checks passed!`.

Task 2:
```
[519.7, 159.44, 1840.29, 519.7, 519.7, 159.44, 1840.29, 519.7] (6078.265039595788, 8e-05) [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] []
```
- The composition total equals 42-RESEARCH's measured `6078.265039595788` (macOS).
- `-k "census_every"`: `1 passed, 47 deselected`.
- Whole file: `48 passed`. Ruff check gave `All checks passed!`; ruff format --check gave `2 files already formatted`.

## Verification on the committed tree (after ccb81c5)

- Plan verification, `pytest tests/test_phase42_prereg.py tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase21_sc5.py`: `175 passed in 104.29s`.
- Quick run: `tests/test_phase42_prereg.py` gave `48 passed`. It is still the only `tests/test_phase42_*.py` file (`ls` lists only it).
- Census call 1, `test_phase35_prereg.py -k "slot_census or slot_ordering or grids_must or e3_"`: `13 passed, 75 deselected`.
- Census call 2, the nine files/nodes of VALIDATION.md line 24: `109 passed in 107.95s`.
- VALIDATION.md per-decision selectors on the prereg test:

  | Selector | Result |
  |----------|--------|
  | `epsilon` | 1 passed |
  | `label or verdict` | 3 passed |
  | `descriptive or reads_only_recall` | 2 passed |
  | `summary or null` | 2 passed |
  | `control_retention_row` | 1 passed |
  | `table_4x2_with_control_recall` | 1 passed |
  | `prediction` | 1 passed |

- `git ls-files 'results/phase42_*'` and `find results -maxdepth 1 -name 'phase42*'` both print nothing.
- `git status --short` shows only the harness's `.claude/scheduled_tasks.lock`.
- Torch-free call path, measured two ways:
  - In a fresh interpreter, `phase25_epsilon.point_epsilon_for_sigma(0.5, steps=800, ...)` leaves `'torch' in sys.modules` False.
  - After `import phase42_prereg`, calling every new function once (both verdict branches, table, both readings, summary, null, lead, the 8 ε, composition, vacuous, TPR, exact, d16, d17) loads no new module: `sorted(set(sys.modules) - before) == []`. The prereg itself loads torch at import through `teach_persona` (42-01 docstring); the new functions add nothing to that.

## Deviations from Plan

1. **Module-level imports, not lazy ones.**
   - `phase25_epsilon` (`scripts/phase42_prereg.py:46`) and `phase29_prereg` (`:48`) are imported at module level.
   - Both are torch-free and already loaded by `phase35_prereg`'s own imports (`scripts/phase35_prereg.py:118`, `:122`), so a lazy import would only add dead weight. This is the same call 42-02 made for `mitigation_budget`.
2. **Private helpers added, and the census forced direct test calls.**
   - New helpers:
     - `_prove_verdicts` (`:920`): exactly POINT_UNITS, every label in LABELS. Shared by table, summary_line, report_lead and d17_reading.
     - `_field` (`:956`): a present-key walk for descriptive_reading.
     - `_REUSED_POINTS` (`:1107`).
   - The every-function census (`tests/test_phase36_prereg.py` `_untested_functions`) counts private defs too. The first green run failed it with `['_field', '_prove_verdicts']`, so the tests now call both module-qualified. No production change.
3. **Extra proofs beyond the plan's list:**
   - `null_line` proves its rendering equals `ENTRIES["null_line"]["value"]` (`:1016`), so the D-15 entry and the function cannot drift.
   - `exact_disagreements` proves the control pair and `n >= 1` (`:1080`).
   - `d16_side_by_side` rows also carry `"kind": "descriptive"`, and their `e3` is a MappingProxyType.
   - Extra test legs:
     - refusals of malformed pairs on both legs, including on a REFUSED threshold;
     - `vacuous_bound(1) ≈ e/(e+1)`;
     - `tpr_reading` stays finite at the largest grid ε;
     - the hedge-word scan also covers the d17 texts, the TPR sentence and the control-retention text.
4. **Grep acceptance over prose (key_link `point_epsilon_for_sigma[(]`).** The pattern matches both the code call (`scripts/phase42_prereg.py:1048`) and the `summary_and_composition` ENTRIES string at `:436`, which is prose. The criterion holds either way; the code hit is `:1048`.
5. **Ruff invocation.** The plan's verify names `.venv/bin/ruff`. I ran `.venv/bin/python -m ruff` as the executor brief requires; same tool, same result.
6. **Plan names resolved against the code.** Every name the plan cites resolved as written: `phase25_epsilon.point_epsilon_for_sigma` (`scripts/phase25_epsilon.py:226`), `curve_total` (`:271`), `phase35_prereg.CURVE_TOTAL` / `SELECTION_ACCOUNTED` / `DELTA` (`:199-201`), `F_Y` (`:342`), `phase29_prereg.REFUSED` (`:333`), `phase25_record.point_record_path` (`:112`), `point_key` (`:199`), `_V4["condition_c"]["point_retention_ppl"]` (3.783248381445523), `tests/test_phase35_prereg.py` `_docstring_nodes`. No misnamed artifact.
7. **No verbatim Rafael quote.** D-18 is cited as the 42-CONTEXT ruling ("D-18 as corrected 2026-10-13", `point_verdict` docstring), never as a quotation, as in 42-01 Deviation 1. Planner defaults keep their "not yet confirmed by Rafael" label; no entry was touched.

## Known Stubs

None.

## Threat Flags

None. These are pure functions with no I/O beyond the import-time read of the already-read `results/phase25_recall.json` (the same `_RECALL_POINTS` 42-01 built). T-42-10..T-42-13 are mitigated as registered:
- T-42-10: the point_verdict signature and its AST read-set test with planted non-vacuity.
- T-42-11: null_line and report_lead are pre-written, and the hedge words are tested.
- T-42-12: ε is computed live and compared with isclose.
- T-42-13: exact_disagreements, with a nextafter non-vacuity leg.

## Self-Check: PASSED

- FOUND: scripts/phase42_prereg.py, tests/test_phase42_prereg.py
- FOUND commits: c153ca7, ccb81c5
- No edits to STATE/ROADMAP/REQUIREMENTS/PROJECT; no gsd-sdk handler called; no existing pinned module edited; no results/phase42_* created.
