---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 03
subsystem: minting-driver
tags: [E5, RANK-01, minting, write-once, verify-mode]
requires:
  - scripts/phase38_prereg.py (plans 01-02: mint_all, max_set_size, nested_sizes, approval_block, MINTING_GLOB, PHASE17_REPORT_SHA256)
  - scripts/phase17_personas.py (the four minting filters)
  - scripts/phase17_isolation.py (held_out_by_slot)
  - scripts/phase25_run.py (atomic_write_json)
provides:
  - "scripts/phase38_mint.py: report_bytes, phase17_proof, derive, write_record, check_record, main, INPUT_RECORDS, MODULES, TOKENIZER"
  - "tests/test_phase38_mint.py: 25 tests"
affects:
  - plan 38-04 (runs `.venv/bin/python scripts/phase38_mint.py` after the code review, the full suite and Rafael's approval)
tech-stack:
  added: []
  patterns: [phase37_r1a write-once/verify driver, slack read at call time so a monkeypatch reaches main unchanged]
key-files:
  created:
    - scripts/phase38_mint.py
    - tests/test_phase38_mint.py
  modified: []
decisions:
  - "check_record compares EVERY key of the fresh derivation (JSON-normalised), not a hand-picked list, so any field the record carries is verified"
requirements-completed: []  # the orchestrator owns the RANK-01 tick (STATE/ROADMAP/REQUIREMENTS are hand-edited)
metrics:
  duration: ~7 min (base daeddfe at 10:57:53 -0300, last task commit at 11:04:42 -0300)
  completed: 2026-10-04
  tasks: 2
  files: 2
---

# Phase 38 Plan 03: the E5 minting command, summary

`scripts/phase38_mint.py` is the one CPU command that mints the E5 candidate sets. It makes no
choice of its own: every candidate decision is `phase38_prereg.mint_all`'s. Before minting, it
proves two premises:

- **D-24:** the report digest equals `PHASE17_REPORT_SHA256`.
- **D-32:** the parsed questions equal `held_out_by_slot()`, in order.

It then mints at `prereg.SLACK_PER_SLOT` and `prereg.MAX_DRAWS`, both read at call time. Next it
re-runs the four Phase 17 filters on the union of the scored prefixes. Finally it adds the nested
sizes and the numeric neighbour counts.

The record is write-once: MINTING_GLOB is checked first, then existence, the tracked prereg and the
clean tree, and the write goes through `atomic_write_json`. Once the record exists, the same command
re-mints and verifies it instead. **No `results/phase38_*` file was written**; plan 04 produces the
record.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 730ed5d | feat(38-03): phase38 mint driver part one: derive() proves D-24 (report digest) and D-32 (held-out questions), runs prereg.mint_all at the call-time slack, adds nested sizes, numeric neighbour counts and the Phase 17 filter proof on the scored prefixes |
| 2 | b3d21a4 | feat(38-03): phase38 mint driver part two: write_record (MINTING_GLOB first, write-once, tracked prereg, clean tree, atomic_write_json), check_record (verify mode re-mints), main |

As the plan says, both files go in one commit per task. The RED runs below were taken before each
implementation existed.

## RED output (tests written first)

Task 1, before `scripts/phase38_mint.py` existed:
```
tests/test_phase38_mint.py:29: in <module>
    import phase38_mint  # noqa: E402  (scripts/ is not a package; never aliased)
E   ModuleNotFoundError: No module named 'phase38_mint'
ERROR tests/test_phase38_mint.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.07s
```
Task 2: the RED run came after the Task 2 tests were added, with only `derive` and its helpers
present.
```
FAILED tests/test_phase38_mint.py::test_a_dirty_tree_writes_nothing - Attribu...
FAILED tests/test_phase38_mint.py::test_a_record_under_the_root_excludes_itself_from_the_dirty_check
FAILED tests/test_phase38_mint.py::test_main_refuses_any_argument - Attribute...
FAILED tests/test_phase38_mint.py::test_main_calls_derive_with_no_override - ...
FAILED tests/test_phase38_mint.py::test_every_phase38_mint_function_has_a_cpu_test
ERROR tests/test_phase38_mint.py::test_a_changed_report_byte_is_the_d24_stop
ERROR tests/test_phase38_mint.py::test_questions_that_are_not_held_out_are_the_d32_stop
ERROR tests/test_phase38_mint.py::test_a_short_name_slot_is_the_d26_stop - At...
ERROR tests/test_phase38_mint.py::test_main_writes_the_record_with_hashes_and_provenance
ERROR tests/test_phase38_mint.py::test_the_record_feeds_the_sizes_and_caps_consumer
ERROR tests/test_phase38_mint.py::test_a_second_main_verifies_and_changes_nothing
ERROR tests/test_phase38_mint.py::test_an_edited_record_fails_verification[_edit_cleared]
ERROR tests/test_phase38_mint.py::test_an_edited_record_fails_verification[_edit_input]
ERROR tests/test_phase38_mint.py::test_a_non_minting_path_is_refused_before_any_other_check
ERROR tests/test_phase38_mint.py::test_an_existing_record_is_never_overwritten
ERROR tests/test_phase38_mint.py::test_an_untracked_prereg_is_refused - Attri...
5 failed, 9 passed, 11 errors in 13.37s
```
The 9 tests that passed are Task 1's derive tests. The census test failed on its own meta-guard:
`assert 6 >= 8`.

## Acceptance output (read from runs)

Task 1 verify:
```
$ .venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_mint.py
8 passed in 12.07s
```
Task 2 verify, before the commit, without the clean-tree driver test:
```
$ .venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_mint.py tests/test_phase38_prereg.py tests/test_phase21_sc5.py tests/test_phase35_prereg.py
168 passed in 61.63s (0:01:01)
$ .venv/bin/ruff check .            -> All checks passed!
$ .venv/bin/ruff format --check .   -> 350 files already formatted
```
After commit b3d21a4:
```
$ .venv/bin/pytest -q -p no:cacheprovider tests/test_phase25_driver.py
24 passed in 1.69s
$ find results -maxdepth 1 -name 'phase38_*'      -> (empty)
$ git status --porcelain -- results              -> (empty)
$ .venv/bin/python scripts/phase38_mint.py bogus; echo $?   -> exit=1
```
`tests/test_phase38_mint.py` runs 25 tests, all green, in 27.53 s. The two real `main()` derivations
take about 7 s each.

## The small real run through main() (SLACK_PER_SLOT monkeypatched to 24)

This was a scratch run outside the test suite. Its root was
`/private/tmp/claude-501/.../scratchpad/mintroot1`, and `refuse_if_dirty` was replaced with a
printer. `main()` ran twice; the first call wrote the record and the second verified it:
```
refuse_if_dirty pathspec ('scripts', 'src', 'results')
MINTING WRITTEN .../mintroot1/results/phase38_minting.json
  stop_draw: 732  per_slot: 24
  person_name: n_cleared 34  max_set_size 35
  pet_name: n_cleared 51  max_set_size 52
  cat_name: n_cleared 34  max_set_size 35
  sibling_name: n_cleared 58  max_set_size 59
  hometown: n_cleared 25  max_set_size 26
  street: n_cleared 24  max_set_size 25
  birth_year: n_cleared 219  max_set_size 220
  house_number: n_cleared 8768  max_set_size 512
MINTING VERIFIED (record re-minted and matched) .../mintroot1/results/phase38_minting.json
  (the same nine lines)
```
The record is 81,729 bytes. Its `phase17_filter_proof.values_checked` is 956. Its
`completion_source` is:

| field | value |
|-------|-------|
| path | `results/phase17_personas_report.md` |
| sha256 | `e7cf89d0…cf98` |
| device | `mps` |
| base_git | `04e724c67033f9a2ed8b705a07ad025c867a18c5` |
| completions | 416 |

These counts match 38-02's per_slot = 24 measurements and the plan's premises exactly: stop_draw
732, the six name list lengths, birth_year 219/220 and house_number 8768/512. The plan's consumer
chain works on the test's real record: `prereg.max_set_size` per slot feeds
`phase36_caps.check_unit_caps("E5", sets=8, max_set_size=512)`, which passes, and birth_year is 220.

## Deviations from Plan

### Minor form choices (no behaviour change)
1. **main prints the stop draw once.** It goes in a header line (`stop_draw: … per_slot: …`), not on
   each slot's line.
2. **check_record verifies every key that derive returns.** The plan lists seed, per_slot,
   max_draws, stream, stop_draw, approval and the slot fields. The check covers all of these and
   also completion_source, rule_entry and phase17_filter_proof, compared after JSON normalisation.
   It still checks the input digests too.
3. **Two refusals the plan did not list got their own tests.** One is the untracked-prereg refusal,
   reached by routing only `git ls-files --error-unmatch` to a missing path. The other is the
   `:(exclude)` pathspec branch for a record under `_ROOT`. That test writes to
   `results/phase38_minting_probe.json`, a name that matches the glob but never exists, and its
   recorder raises, so nothing is written whether or not the real record is present.
4. **The edited-record tests use the cached small derivation.** They patch `derive` to return it,
   so the parametrised pair does not re-mint twice. The real derivation still runs through `main()`
   in the write fixture and in the verify test.
5. **The D-24, D-32 and D-26 refusal tests now go through `main(out_root=tmp_path)`.** In Task 1
   they called `derive()`. They now also assert that tmp_path stays empty and that the dirty-tree
   recorder was never called.

No false premise was found. `scripts/phase38_prereg.py` was not modified.

## Known Stubs

None.

## Threat Flags

None. The only write path is the one the plan's threat model names (T-38-13/14): MINTING_GLOB is
checked first, then write-once, then `atomic_write_json`. Note that `atomic_write_json` creates the
file with mode 0600 (the tempfile default). That is phase25_run's existing behaviour and is not
changed here.

## Self-Check: PASSED
- FOUND: scripts/phase38_mint.py, tests/test_phase38_mint.py
- FOUND: 730ed5d, b3d21a4 (git log)
- No STATE/ROADMAP/REQUIREMENTS edits, no gsd-sdk mutation handler called, no results/phase38_* file in the real tree
