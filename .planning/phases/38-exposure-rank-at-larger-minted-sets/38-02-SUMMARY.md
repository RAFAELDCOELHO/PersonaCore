---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 02
subsystem: pre-registration
tags: [prereg, E5, minting-rule, determinism, prefix-stability]
requires:
  - scripts/phase38_prereg.py (plan 01: constants, the e5_minting_rule entry)
  - scripts/phase14_factset.py (LOCKED_FACTS, all_pools, normalize_for_match, exact_match_clean)
  - scripts/phase17_persona_facts.py (PERSONA_FACTS, FORBIDDEN_VALUES)
  - scripts/phase21_filler.py (FILLER_FACTS)
  - results/phase17_personas_report.md (the clearance completions and the 104 questions)
  - artifacts/tokenizer.json
provides:
  - "scripts/phase38_prereg.py: MAX_VALUE_TOKENS, parse_completions, taught_anywhere, forbidden_for_substring, levenshtein, draw_name, _screen, _new_screen, mint_names, seeded_shuffle, neighbour_flags, numeric_candidates, max_set_size, nested_sizes, mint_all"
  - "tests/test_phase38_prereg.py: 20 new tests (51 in total)"
affects:
  - plan 38-04 (runs mint_all at SLACK_PER_SLOT and writes the minting record, which freezes this file)
tech-stack:
  added: []
  patterns: [one rng.random() stream with explicit Fisher-Yates, global stop for prefix stability, AST gate on Random methods]
key-files:
  created: []
  modified:
    - scripts/phase38_prereg.py
    - tests/test_phase38_prereg.py
decisions:
  - "The filters shared by names and numbers (over_budget, roundtrip, in_question, substring_forbidden, substring_minted) live in one private _screen, with its context built by _new_screen. Both are called directly by a test, so the every-function census holds."
  - "The D-32 equality between the parsed questions and phase17_isolation.held_out_by_slot() is proved in the test on the digest-pinned report, not inside mint_all. mint_all stays as the plan specifies it."
requirements-completed: []  # the orchestrator owns the RANK-01 tick (STATE/ROADMAP/REQUIREMENTS are hand-edited)
metrics:
  duration: ~7 min (base bd1dd65 at 10:50:26 -0300, last task commit at 10:57:10 -0300)
  completed: 2026-10-04
  tasks: 2
  files: 2
---

# Phase 38 Plan 02: E5 pre-registration, part two (the minting rule as code), summary

`scripts/phase38_prereg.py` now holds the executable minting rule that matches the `e5_minting_rule` entry plan 01 committed. The pieces:

- **Names:** one `random.Random(seed)` stream, with every choice made through `rng.random()`. Draws are dealt round-robin by token count and pass through `NAME_FILTERS` in order. A global stop at `per_slot` keeps the lists prefix-stable.
- **Numbers:** each range is enumerated in ascending order, passed through `NUMERIC_FILTERS` (cross-slot uniqueness included), then put through an explicit Fisher-Yates shuffle. Values at distance 1 from a taught value are flagged, never rejected.
- **`mint_all`:** reads the seed lazily from `phase35_prereg.seed_list()[0]` and raises the D-26 STOP if any name slot is short.
- **Set sizes:** `max_set_size` and `nested_sizes` (D-31 / D-08).

The module still imports without torch. No `results/phase38_*` file exists.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | d1ebd7a | feat(38-02): phase38 prereg minting rule, names half: parse_completions (D-24), taught_anywhere/forbidden_for_substring (D-03), levenshtein (D-27), draw_name (D-01), mint_names under the global stop (D-25/D-26) |
| 2 | f574bf7 | feat(38-02): phase38 prereg minting rule, numeric half: seeded_shuffle (D-10), neighbour_flags (D-27), numeric_candidates (D-09/D-26), mint_all with the D-26 STOP, max_set_size (D-31), nested_sizes (D-08) |

The plan says to commit both files per task, so each task's tests and code went in one commit. The RED runs below were taken before each implementation was written.

## RED output (tests written first)

Task 1, before any minting function existed:
```
FAILED tests/test_phase38_prereg.py::test_parse_completions_refuses_a_missing_line_or_header
FAILED tests/test_phase38_prereg.py::test_taught_anywhere_and_forbidden - Att...
FAILED tests/test_phase38_prereg.py::test_levenshtein_witnesses - AttributeEr...
FAILED tests/test_phase38_prereg.py::test_draw_name_is_deterministic_lowercase_ascii
ERROR tests/test_phase38_prereg.py::test_parse_completions_on_the_tracked_report
ERROR tests/test_phase38_prereg.py::test_mint_names_holds_every_filter - Attr...
ERROR tests/test_phase38_prereg.py::test_mint_names_is_deterministic - Attrib...
ERROR tests/test_phase38_prereg.py::test_mint_names_is_prefix_stable - Attrib...
ERROR tests/test_phase38_prereg.py::test_mint_names_reports_a_short_stream_without_raising
4 failed, 31 passed, 5 errors in 2.68s
```
Task 2, before the numeric functions existed:
```
FAILED tests/test_phase38_prereg.py::test_seeded_shuffle_is_a_deterministic_fisher_yates
FAILED tests/test_phase38_prereg.py::test_mint_all_stops_on_a_short_slot - At...
FAILED tests/test_phase38_prereg.py::test_max_set_size_and_nested_sizes - Att...
ERROR tests/test_phase38_prereg.py::test_numeric_candidates_birth_year_and_house_number
ERROR tests/test_phase38_prereg.py::test_neighbour_flags - AttributeError: mo...
ERROR tests/test_phase38_prereg.py::test_mint_all_reads_the_seed_and_covers_every_slot
ERROR tests/test_phase38_prereg.py::test_mint_all_seed_is_read_not_typed - At...
ERROR tests/test_phase38_prereg.py::test_minted_values_pass_the_phase17_filters
3 failed, 43 passed, 5 errors in 3.91s
```
Two of Task 2's new tests were already green at its RED run:

- `test_max_value_tokens_matches_phase17` passed because Task 1 had added `MAX_VALUE_TOKENS`.
- `test_only_random_is_called_in_phase38_scripts` passed because Task 1's code calls only `rng.random()`.

The gate is not vacuous. Its planted copies (`rng.choice(x)`, and a module-level `random.Random(0)`) both go red inside the test, and the meta-guard requires at least one `.random()` call.

## Acceptance output (read from runs)

Task 1:
```
$ .venv/bin/python -c "...parse_completions...; print(len(c), sum(map(len, c.values())), sum(map(len, q.values())), len(p.taught_anywhere()), len(p.forbidden_for_substring()))"
8 416 104 118 123
$ .venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_prereg.py
41 passed in 3.86s
$ git ls-files 'results/phase38_*'
(empty)
```
Task 2:
```
$ .venv/bin/python -c "...print(p.max_set_size(2048), p.max_set_size(219), p.nested_sizes(220), 'torch' in sys.modules)"
512 220 (8, 32, 128, 220) False
$ .venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_prereg.py tests/test_phase35_prereg.py tests/test_phase21_sc5.py
143 passed in 35.57s
$ .venv/bin/ruff check .            -> All checks passed!
$ .venv/bin/ruff format --check .   -> 348 files already formatted
$ git status --porcelain -- scripts tests results   -> (empty)
$ git ls-files 'results/phase38_*'; find results -maxdepth 1 -name 'phase38_*'   -> (both empty)
```
`tests/test_phase38_prereg.py` runs 51 tests, all green, in 14.05 s. Every prereg function has a direct `phase38_prereg.<fn>(` call, so `test_every_phase38_prereg_function_has_a_cpu_test` is green.

## Measured counts (all match the plan's premises)

These are asserted in the tests and were also printed from a scratch `mint_all(..., per_slot=24)` run. Nothing was written to disk.

| slot | kept | rejections (non-zero) | distance-1 flagged |
|------|------|-----------------------|--------------------|
| birth_year | 219 | excluded 7 (1893, 1906, 1941, 1953, 1962, 1974, 1987) | 101 of 219 |
| house_number | 8768 | excluded 13, substring_minted 219 | 320 (descriptive; not a plan premise) |

The `per_slot = 24` name run:

- **Stop and stream:** `stop_draw` 732, with 494 draws dropped at the wrong token count and 2 as duplicates.
- **Seed:** 1337, read from `seed_list()[0]`.
- **Lists at the stop:** person_name 34, pet_name 51, cat_name 34, sibling_name 58, hometown 25, street 24.
- **Non-zero rejections:** pet_name excluded 1, substring_minted 6, neighbour_d1 1; sibling_name substring_minted 1; street substring_minted 1. Every other count is 0, clearance included.

I also checked the plan checker's yield premise with a scratch run of `mint_names` at `SLACK_PER_SLOT`. It wrote nothing and is not a test, per Pitfall 8:
```
True 58195 {'person_name': 2125, 'pet_name': 2048, 'cat_name': 2113, 'sibling_name': 4951, 'hometown': 2087, 'street': 2102}
True    # the per_slot=24 lists are prefixes of the 2048 lists
17.39 s user
```
This is exactly the plan's 58,195 draws and the same six list lengths.

## Deviations from Plan

### Minor form choices (no behaviour change)
1. **Two private helpers were added: `_screen` and `_new_screen`.** They hold the five filters that names and numbers share. The first draft had six small private helpers, which failed the every-function census. I folded them into these two and added `test_screen_names_the_first_failing_shared_filter`, which calls both directly and reaches each named outcome: over_budget, in_question, substring_forbidden, substring_minted in both directions, roundtrip, and None.
2. **`draw_name` writes the choice inline.** It uses `seq[int(rng.random() * len(seq))]` in a loop over (ONSETS, NUCLEI, CODAS) instead of a `_pick` helper. The draw order and the values are the rule's.
3. **The D-32 question equality is proved where the plan's behaviour block puts it.** `test_parse_completions_on_the_tracked_report` checks the parsed questions against `phase17_isolation.held_out_by_slot()` slot by slot and in order, and also checks the report digest. It is not re-proved inside `mint_all`.
4. **Some tests go beyond the plan's list.** They cover `nested_sizes(8) == (8,)` and its refusal below 8; `seeded_shuffle([])`; `numeric_candidates("street", ...)` refusing a non-numeric slot; and a seed-7 run whose name lists differ from the seed-1337 lists.

No false premise was found. Every measured value the plan quotes reproduced exactly: 8 / 416 / 104 / 118 / 123, birth_year 219 with 7 excluded and 101 neighbours, house_number 8768 with 13 excluded and 219 cross-slot, and 58,195 draws with the six list lengths.

## Known Stubs

None.

## Threat Flags

None. No new network, auth or write path was added. `mint_all` returns a dict and writes nothing; plan 04 writes the record.

## Self-Check: PASSED
- FOUND: scripts/phase38_prereg.py, tests/test_phase38_prereg.py
- FOUND: d1ebd7a, f574bf7 (git log)
- No STATE/ROADMAP/REQUIREMENTS edits, no gsd-sdk mutation handler called, no results/phase38_* file
