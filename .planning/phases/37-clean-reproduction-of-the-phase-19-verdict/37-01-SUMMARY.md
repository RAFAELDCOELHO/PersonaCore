---
phase: 37-clean-reproduction-of-the-phase-19-verdict
plan: 01
subsystem: pre-registration
tags: [prereg, repro-03, r1b, slot-fill, ancestry]
requires:
  - scripts/phase35_prereg.py (fill, R1A_ASSERTIONS, MARGIN_K, V6_RESULT_PATHS, ENTRY_FIELDS, KINDS, FORBIDDEN_PHRASE)
  - scripts/phase36_prereg.py (ENTRIES["front_stop_factor"])
  - scripts/phase19_floor.py (EVIDENCE_ARTIFACT, locked floors)
  - results/phase19_noise_floors.json, results/phase19_arm_erased.json, results/phase19_collateral_curve.json, results/phase36_budget.json
provides:
  - scripts/phase37_prereg.py — R1B_TOLERANCE_AND_REPLICATED (the r1b slot fill), RECORDS/R1A_RECORD/R1B_RECORD/R1B_ARM_RECORD, DESTROYED_PCT_TOLERANCE, R1B_COST_HOURS/R1B_COST_CAP_HOURS, 14 ENTRIES, replicated(), prefix_decision(), draw_identity(), nontarget_context()
  - tests/test_phase37_prereg.py — ancestry guard every later Phase 37 record must pass
affects: [37-02, 37-03, 37-04, 37-05, 37-06, 37-07]
tech-stack:
  added: []
  patterns: [phase36_prereg-style four-field entries, import-time _prove guards, census-conformant single fill binding]
key-files:
  created:
    - scripts/phase37_prereg.py
    - tests/test_phase37_prereg.py
  modified: []
decisions:
  - "replicated_definition passed to the fill as the MappingProxyType ENTRIES entry; phase35's _frozen_entry accepted it, no dict() needed"
  - "replicated() refuses a MISSING assertion key but tolerates extra keys (the spec named only the missing case)"
  - "prefix_decision(): when k is equal but the re-measured list length differs from the committed one, positions_moved adds the length difference (edge the plan left unspecified)"
requirements-completed: []  # REPRO-03 is ticked by the orchestrator at phase close (37-07), not by this plan
metrics:
  duration: "~25 min"
  completed: 2026-10-03
  tasks: 2
  files: 2
---

# Phase 37 Plan 01: Phase 37 pre-registration Summary

Torch-free `scripts/phase37_prereg.py` fills the v6.0 slot `r1b_tolerance_and_replicated` once with all four tolerances (three zeros labelled `preference`, destroyed_pct `derived` at import from the Phase 19 records in D-02 order), fixes the three `results/phase37_*` record paths, proves the R1b cost under 1.5x its budget front, and ships the D-03/D-07/D-12 rule functions, all committed before any Phase 37 record.

## Values read from a run (not from the plan)

Printed by `.venv/bin/python -c "... import phase37_prereg as p ..."` after Task 1:

```
0.8396203493271365 True ['destroyed_pct', 'k', 'nontargets_beyond_margin', 'target_correct'] ('results/phase37_r1a.json', 'results/phase37_r1b_arm.json', 'results/phase37_r1b.json')
{'tolerance_k': 'preference', 'tolerance_target_correct': 'preference', 'tolerance_nontargets_beyond_margin': 'preference', 'tolerance_destroyed_pct': 'derived'}
1.2590560358100467 1.6622708975519829
```

- `repr(DESTROYED_PCT_TOLERANCE)` = `0.8396203493271365`
- `R1B_COST_HOURS` = `1.2590560358100467`, `R1B_COST_CAP_HOURS` = `1.6622708975519829` (cost <= cap: True)
- `git ls-files 'results/phase37_*'` printed nothing after both commits.

Edge check run before writing `replicated()`: with committed destroyed_pct 77.6370113463966 and the tolerance above, `abs((c + t) - c)` = 0.8396203493271344 <= t (REPLICATED at the edge), and `math.nextafter(c + t, inf)` falls outside, so the plain `abs(diff) <= tol` form is inclusive at both edges on these floats.

## RED output (Task 1, before the module existed)

```
tests/test_phase37_prereg.py:31: in <module>
    import phase37_prereg  # noqa: E402  (same)
    ^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'phase37_prereg'
=========================== short test summary info ============================
ERROR tests/test_phase37_prereg.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.35s
```

GREEN: 17 behaviour tests passed (0.42 s). After Task 2: 32 passed in `tests/test_phase37_prereg.py`; the plan's verify set
(`test_phase37_prereg.py test_phase35_prereg.py test_phase36_prereg.py test_phase21_sc5.py`) gave 141 passed in 23.79 s,
including `test_slot_census_is_green_on_the_real_tree` and `test_slot_ordering_is_green_on_the_real_repo` with the fill file tracked.
`ruff check .` "All checks passed!"; `ruff format --check .` "340 files already formatted".

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | be311f0 | feat(37-01): Phase 37 pre-registration — R1b slot fill, D-02 tolerance, D-06 cost guard, rule functions |
| 2 | 9425fe5 | test(37-01): Phase 37 prereg guard tests — ancestry, record arithmetic, schema, census |

## Deviations from Plan

1. **[TDD order] RED not committed on its own.** The plan says to commit both files together after GREEN, so the Task 1 commit holds the tests and the module; the RED run is recorded above. A test-only commit first would have left the tree with a collection error at that commit.
2. **[Rule 2] `_prove_number()` added** so `replicated()` refuses bool / NaN / inf / non-numeric replica values instead of comparing them; it is called directly by `test_rule_inputs_must_be_finite_numbers` (the every-function census requires it).
3. **`_ENTRY_NAMES`** — the fourteen names `_prove_entries()` checks against are a module-level frozenset (the plan asked for the set check, not where the names live).
4. **Citation line, plan premise slightly off.** The plan cites the MPS k* curve agreement at `scripts/erasure_kstar_prereg.py:139`; measured, the `|difference| = 0.0` sentence is at :137 and `CURVE_AGREEMENT_DIALOGUE_TOLERANCE` at :139. The `tolerance_k` derivation cites the constant by name rather than a line number.
5. **r1b_scope labels** for the five D-05 items are Claude's naming (`ordering_288_addresses`, `stopping_rule`, `k`, `a2_entries_216_at_k48`, `post_erasure`); the three `pre_erasure.*` names follow the pin's `PRE_ERASURE_KEYS`, which Task 2's test checks.
6. The three decisions in the frontmatter (MappingProxyType accepted by the fill; extra keys tolerated by `replicated()`; positions_moved on a length mismatch).

## TDD Gate Compliance

The `test(37-01)` commit (9425fe5) follows the `feat(37-01)` commit (be311f0), not the other way round, because the plan put the Task 1 tests in the feat commit (deviation 1). The RED failure was observed and is recorded above.

## Known Stubs

None.

## Threat Flags

None. No network, auth or file-write surface; the module reads four committed JSON records and writes nothing.

## Self-Check: PASSED

- FOUND: scripts/phase37_prereg.py
- FOUND: tests/test_phase37_prereg.py
- FOUND: be311f0
- FOUND: 9425fe5
