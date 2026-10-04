---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 01
subsystem: pre-registration
tags: [prereg, E5, rank, minting-rule, ancestry]
requires:
  - scripts/phase35_prereg.py (fill, V6_RESULT_PATHS, ENTRIES, MARGIN_K, e1_condition_b_margin)
  - scripts/phase36_budget.py (RANK02_PREFIXES)
  - scripts/phase36_prereg.py (front_stop_factor)
  - results/phase36_budget.json
provides:
  - scripts/phase38_prereg.py (E5_MINTING_RULE, E5_RANK_MOVES_AND_GENERATION_COLLAPSES, the rule constants, the definitions, drop_formula_audit, committed_gate_ranks, a2_counts, approval_block)
  - tests/test_phase38_prereg.py
affects:
  - plan 38-02 (adds the minting functions to the same file, before the minting record)
tech-stack:
  added: []
  patterns: [phase37_prereg skeleton, input-free fills bound at module level, natural-RED ancestry guards]
key-files:
  created:
    - scripts/phase38_prereg.py
    - tests/test_phase38_prereg.py
  modified: []
decisions:
  - "phase35_prereg.fill accepted the MappingProxyType entries directly; no dict(...) conversion was needed"
requirements-completed: []  # the orchestrator owns the RANK-01/RANK-02 ticks (STATE/ROADMAP/REQUIREMENTS are hand-edited)
metrics:
  duration: ~10 min (base f8d423f at 10:39:43 -0300, last task commit at 10:49:39 -0300)
  completed: 2026-10-04
  tasks: 3
  files: 2
---

# Phase 38 Plan 01: E5 pre-registration, part one, summary

`scripts/phase38_prereg.py` is the first half of Phase 38's pre-registration, and it imports without torch. It holds:

- the written minting rule (16 keys);
- the moved, collapsed, damaged and top-eighth definitions as pure functions;
- the D-21 approval of 8 prefixes, with the projection, total and stop hours computed at import from `results/phase36_budget.json`;
- the D-33 drop-formula audit;
- readers for the 64 committed gate ranks and the committed A2 counts;
- both input-free v6.0 fills, each made once.

No `results/phase38_*` file exists.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 1a988c3 | feat(38-01): phase38 prereg part (a): record paths, D-21 approval and D-22/D-23 arithmetic, rule constants, sixteen entries, both input-free fills |
| 2 | c92822c | feat(38-01): phase38 prereg part (b): rank/event definitions, D-33 drop-formula audit, committed gate and A2 readers |
| 3 | aff8da7 | test(38-01): phase38 prereg guards: ancestry (SC4), inputs vs owner modules, D-21 quote, literal scan, schema, census, torch-free, zero skips, every function called |

## RED output (tests written first)

Task 1, `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_prereg.py` before the module existed:
```
tests/test_phase38_prereg.py:38: in <module>
    import phase38_prereg  # noqa: E402  (same)
E   ModuleNotFoundError: No module named 'phase38_prereg'
ERROR tests/test_phase38_prereg.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.42s
```
Task 2: the Task 2 tests were appended before the definitions existed.
```
E       AttributeError: module 'phase38_prereg' has no attribute 'committed_gate_ranks'
FAILED tests/test_phase38_prereg.py::test_rank_in_prefix_breaks_ties_by_string
FAILED tests/test_phase38_prereg.py::test_rank_in_prefix_refuses_malformed_sets
FAILED tests/test_phase38_prereg.py::test_rank_in_prefix_equals_exposure_rank_on_random_tied_sets
FAILED tests/test_phase38_prereg.py::test_exposure_bits - AttributeError: mod...
FAILED tests/test_phase38_prereg.py::test_moved_and_left_top_eighth - Attribu...
FAILED tests/test_phase38_prereg.py::test_first_event_and_relation - Attribut...
FAILED tests/test_phase38_prereg.py::test_components_sha256_reproduces_the_probe_e1_digest
FAILED tests/test_phase38_prereg.py::test_committed_gate_ranks_reproduce_the_research_table
ERROR tests/test_phase38_prereg.py::test_a2_counts_and_events_reproduce_the_research_table
ERROR tests/test_phase38_prereg.py::test_drop_formula_audit_on_the_committed_records
8 failed, 6 passed, 2 errors in 1.14s
```
(The 6 passing tests are Task 1's.)

## Acceptance output (read from runs)

Task 1:
```
$ .venv/bin/python -c "...print(repr(p.E5_PROJECTION_HOURS), repr(p.E5_TOTAL_HOURS), repr(p.E5_STOP_HOURS), p.READINGS, p.RECORDS, p.APPROVED_E5_PREFIXES, 'torch' in sys.modules)"
0.467956566879681 77.83105039182757 0.5418565110509128 ('k0', 'k8', 'k16', 'k32', 'k64', 'k78', 'M2', 'adapter_off') ('results/phase38_minting.json', 'results/phase38_rank.json', 'results/phase38_rank_report.md') 8 False
$ .venv/bin/python -c "...print(len(p.ENTRIES), sorted(p.E5_RANK_MOVES_AND_GENERATION_COLLAPSES), sorted(n for n, e in p.ENTRIES.items() if e['kind'] == 'derived'))"
16 ['collapses', 'moves'] ['e5_projection_hours', 'e5_stop_hours', 'e5_total_hours', 'generation_damaged']
$ git ls-files 'results/phase38_*'; find results -maxdepth 1 -name 'phase38_*'
(both empty)
```
Before committing, `git show HEAD:results/phase17_personas_report.md | shasum -a 256` gave `e7cf89d0e1d225c65f6dd2f089795b8e7c63a12ef08ebb6f0b63835e0a37cf98`. This is the plan's value.

Task 2:
```
$ .venv/bin/python -c "...a=p.drop_formula_audit(p.a2_counts()); print(a['flips'], a['exact_ties'], len(a['differing']))"
[] [['person_name', 8]] 7
```
Task 3 verify:
```
$ .venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_prereg.py tests/test_phase35_prereg.py tests/test_phase36_prereg.py tests/test_phase21_sc5.py tests/test_phase36_caps.py
175 passed in 27.51s
$ .venv/bin/ruff check .                       -> All checks passed!
$ .venv/bin/ruff format --check .              -> 348 files already formatted
$ .venv/bin/ruff format --check scripts/phase38_prereg.py -> 1 file already formatted
$ .venv/bin/pytest ... test_phase35_prereg.py::test_slot_census_is_green_on_the_real_tree ::test_slot_ordering_is_green_on_the_real_repo
2 passed in 2.96s
$ git status --porcelain -- scripts tests results   -> (empty)
$ git ls-files 'results/phase38_*'                  -> (empty)
```
`tests/test_phase38_prereg.py` has 31 tests, all green.

## Deviations from Plan

### Minor form choices (no behaviour change)
1. **`ONSETS` is written as a two-part starred tuple literal.** It has the same 26 values in the same order. The split only keeps lines within 100 characters.
2. **The module proves at import that its exclusion sources are non-empty.** It checks `phase14_factset.all_pools()`, `PERSONA_FACTS`, `FORBIDDEN_VALUES` and `FILLER_FACTS`. Without a use, the `phase17_persona_facts` and `phase21_filler` imports the plan requires would fail ruff F401. The check also stops the exclusion filter from being silently vacuous.
3. **`drop_formula_audit` returns more keys than the plan lists.** On top of them it returns `margin`, `flip_name` ("margin tie decided by rounding") and `exact_tie_name` ("exact margin tie decided by D-14's strict >"), so each case is named in the record itself.
4. **A private helper `_exposure_rows` was added.** It parses the committed exposure lists, and a test calls it directly so the every-function census still holds.
5. **The `RETRAIN_RECORD` check uses a different call than first written.** The first draft called `pin.arm_record_path(pin.RETRAIN_ARM)`, and the pin refused it: `erase_reference` is not an erasure arm name. The test now calls `pin.arm_record_path("retrain")`. This was a mistake in my test, fixed before the Task 3 commit. Nothing in the plan's premises was wrong.

No false premise was found. Every measured value the plan quotes reproduced exactly: the three hour reprs, the D-24 digest, the D-20 digest, the A2 table, the gate table, the 7 differing D-33 cells, `flips == []` and the person_name k = 8 exact tie.

## Known Stubs

None. The minting functions are plan 38-02's by design; this file is completed there, before the minting record.

## Threat Flags

None. No new network, auth or write path was added. The module reads committed JSON and writes nothing.

## Self-Check: PASSED
- FOUND: scripts/phase38_prereg.py
- FOUND: tests/test_phase38_prereg.py
- FOUND: 1a988c3, c92822c, aff8da7 (git log)
