---
phase: 42-dp-sgd-recipe-search-at-large
plan: 01
subsystem: prereg
tags: [prereg, e3, dp-sgd, recipe-grid, ancestry]
requires:
  - scripts/phase35_prereg.py (fill, SLOTS e3_grid_subset, p22_onset_sigma, E3_* constants)
  - scripts/phase36_prereg.py ENTRIES["e3_max_steps"]
  - scripts/phase36_caps.py check_unit_caps / counts_for
  - results/phase36_budget.json, results/phase25_point_dp_n8_sigma0p000000.json, results/phase25_recall.json
provides:
  - scripts/phase42_prereg.py (fill file 1: RECORD_GLOB, CONTROL_GLOB, BUDGET_RECORD, V4_CONTROL_RECORD, V4_CONTROL_SHA256, V4_CONTROL_COUNTS, SEED, T_MAX, LRS, STEPS, RECIPES, CONTROL_SIGMA, NOISED_SIGMAS, WARMUPS, ENTRIES (28), E3_GRID_SUBSET, P22_ONSETS)
  - tests/test_phase42_prereg.py (module-level _strictly_before, _first_add, _phase42_records, _forbidden_token_failures, _FORBIDDEN_TOKENS for plans 04/05/09)
affects: [42-02, 42-03, 42-04, 42-05, 42-06, 42-09]
tech-stack:
  added: []
  patterns: [phase41_prereg layout, Phase 35 leg (a) ancestry, AST literal scan with one exempt node]
key-files:
  created:
    - scripts/phase42_prereg.py
    - tests/test_phase42_prereg.py
  modified: []
decisions:
  - "Rafael's D-18 words are not quoted verbatim: the quoted string in the plan exists in no committed record; the ruling is cited by its commit 4f45a91 (_RULING_CONTEXT)"
  - "WARMUPS = {T: T x WARMUP_STEPS // MAX_STEPS} is the warmup_rule value (20 at 200, 80 at 800), computed, never typed"
requirements-completed: []
metrics:
  duration: ~40 min
  completed: 2026-10-13
  tasks: 3
  files: 2
---

# Phase 42 Plan 01: Phase 42 prereg fill file 1 Summary

`scripts/phase42_prereg.py` fills `e3_grid_subset` with the 2x2 grid lr (teach_persona.LR, 1e-3) x T
(STEP_BUDGET, e3_max_steps) at batch 8 and seed `seed_list()[0]`. At every import it re-runs the v5.0
SHA-256 check on the reused v4.0 control and the P22 check for T = 200 and T = 800. It writes all
decisions D-01..D-23 as 28 four-field ENTRIES, and its test file landed in the same commit, before any
`results/phase42_*` exists.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | 6467a99 | feat(42-01): Phase 42 prereg fill file 1 — e3_grid_subset fill, RECIPES 2x2, SEED, caps, with its test file |
| 2 | db21017 | feat(42-01): ENTRIES for every decision D-01..D-23 — predictions read from records, planner defaults labelled |
| 3 | c2f66c4 | test(42-01): guard tests for the Phase 42 prereg — ancestry trio, literal scan, schema, import probe, slot census, forbidden tokens |

## RED outputs (natural, before implementation)

- Task 1: `pytest tests/test_phase42_prereg.py` gave `E ModuleNotFoundError: No module named 'phase42_prereg'`, `1 error in 0.42s` (collection error; the prereg did not exist yet).
- Task 2: the eight new tests ran against the Task-1 prereg (one entry) and gave `8 failed, 6 passed in 1.24s`: `KeyError: 'lr_con...'`, `KeyError: 'vacuous'`, `AttributeError` for `_RULING_CONTEXT` / `_DEFAULT`, plus assertion failures on the entry set, D-ID coverage, e3_hours and predictions.
- Task 3 (guard tests, not TDD): the first run gave `1 failed, 25 passed`. The forbidden-token gate's own non-vacuity leg caught a real gap in the helper (see Deviations 4).

## Acceptance lines, as printed

Task 1:
```
12 {200: 0.07890181429684162, 800: 0.15780356992036104} [{'lr': 0.0003, 'steps': 200, 'batch': 8}, {'lr': 0.0003, 'steps': 800, 'batch': 8}, {'lr': 0.001, 'steps': 200, 'batch': 8}, {'lr': 0.001, 'steps': 800, 'batch': 8}] 1337 0c23f6c1 [0.0003]
```
- First add of both files: `git log --diff-filter=A --format=%h` gives `6467a99` for `scripts/phase42_prereg.py` and `6467a99` for `tests/test_phase42_prereg.py` (same commit). Tasks 2 and 3 later touched the files, so `-1` no longer matches. The first add is the property leg (a) needs.
- `git ls-files 'results/phase42_*'` and `find results -maxdepth 1 -name 'phase42*'` both print nothing (checked after c2f66c4).

Task 2:
```
28 ['e3_hours', 'v4_control_reuse'] 5.3702 the sigma = 0.5 and sigma = 1 points of the v4.0 recipe repeat the v4.0 recall, dp_n8_sigma0p500000: 0/1008 taught, 0/648 held-out; dp_n8_sigma1p000000: 0/1008
```
- `-k "entries or decision or hours or predictions or d11 or d18 or defaults"` gave `8 passed, 6 deselected` (at Task 2).
- `null_line` value: `nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)`; `WARMUPS`: `{200: 20, 800: 80}`.

Task 3 / plan verification:
- `pytest tests/test_phase42_prereg.py tests/test_phase35_prereg.py tests/test_phase36_prereg.py tests/test_phase36_caps.py tests/test_phase21_sc5.py tests/test_phase23_resume.py` gave `179 passed in 209.79s`, EXIT=0. `ruff check .` gave `All checks passed!`. `ruff format --check .` gave `370 files already formatted`.
- After commit c2f66c4:
  - `-k "frozen or first_added or records_at_commit or forbidden"` gave `4 passed, 22 deselected`.
  - Census call 1 (`test_phase35_prereg.py -k "slot_census or slot_ordering or grids_must or e3_"`) gave `13 passed, 75 deselected`.
  - Census call 2 (the ten files/nodes of VALIDATION.md line 24) gave `109 passed in 109.27s`.
  - `test_phase36_caps.py` alone, after commit 6467a99 (the owner fill file is tracked and live), gave `35 passed`.
  - `git status --porcelain -- scripts tests results` is empty.
- Quick run: only `tests/test_phase42_prereg.py` exists so far (26 tests, all passing). The threshold and recipes test files belong to later plans.

## ENTRIES

28 entries. Derived: `e3_hours` (priced 5.370215732835186 h; E3 line 6.622459432036141 h) and `v4_control_reuse`. Preference: the other 26.

Five planner defaults carry "default taken at plan time, not yet confirmed by Rafael": `record_layout`, `unit_order`, `crash_rule`, `rehearsal_shape`, `d05_seam`. Plan 06 confirms them.

Every source names dc578f9. `lr_control_outcome` and `own_control_recall` also name 4f45a91. The test proves `git show 4f45a91:42-CONTEXT.md` holds "D-23: Each point publishes" and "does NOT change any label", and that dc578f9's copy holds neither.

## Deviations from Plan

1. **[Rule 2 - honesty] No verbatim Rafael quote in `lr_control_outcome`.**
   - The plan said to quote "REFUSED só por control_is_unlearnable, como na v4.0" as Rafael's words.
   - `grep -rn "só por control_is_unlearnable" .planning/` finds the string only in `42-01-PLAN.md:167`. It is not in 42-CONTEXT, 42-DISCUSSION-LOG or the 4f45a91 commit message.
   - So the derivation states "D-18 as corrected by Rafael's ruling of 2026-10-13" and cites the ruling commit through `_RULING_CONTEXT = "42-CONTEXT D-{} (4f45a91)"`. It does not present the plan's text as his words. No test asserted the quote.
2. **Imports bound only where used.**
   - The plan's header listed `fnmatch`, `fractions` and `math`. This file doesn't use them yet, and ruff F401 would reject them.
   - Plans 02 and 03 add them with their functions.
   - Added `mitigation_budget` (for CLIP_NORM / CONTROL_CLIP_NORM as entry values) and `phase25_record` (the point_key for the D-16 readings). Both are torch-free and are already imported by phase35_prereg.
3. **Added `WARMUPS`, `_TRAINED_STEPS` and a post-fill `_prove`.**
   - `WARMUPS = {T: T * WARMUP_STEPS // MAX_STEPS}` is the `warmup_rule` value.
   - `e3_hours` prices the runs `_TRAINED_STEPS` (RECIPES x E3_SIGMAS minus RECIPES[0] at CONTROL_SIGMA).
   - After the fill, a `_prove` checks that this tuple equals the fill's non-reused cells, so the priced runs cannot drift from the grid.
   - The plan left the values of most prose entries unspecified. Each one got a short str, tuple or MappingProxy value (no list/dict), e.g. `p22_check` = STEPS and `dp_clip` = CLIP_NORM.
4. **[Rule 1 - Bug] `_forbidden_token_failures` missed import names.**
   - The planted leg `from personacore import inject_lora` returned `[]`: `ast.alias` nodes are neither Name nor Attribute.
   - Fix: the helper now also reads `alias.name` / `alias.asname`. Commit c2f66c4.
5. **Literal-scan exemption mechanics.**
   - Mirrored phase41's `_without_grid`: 1e-3 is in the float census set, so the meta-guard proves the LRS node is scanned.
   - `_without_lrs` blanks that one node.
   - `_chosen_lr_literals_outside_lrs` proves that node is the only float equal to 1e-3. A planted `X = 0.001` fails both.
6. **Extra test names.** `test_no_mutable_containers_in_entries` (with a non-vacuity leg) and `test_prove_count_and_read_helpers` hold the plan's schema item 5 assertions.

## Known Stubs

None. The prereg's path builders, pure rules and driver belong to plans 02-05.

## Threat Flags

None. No network, no write at import. Importing the prereg runs `git show v5.0:` through the Phase 35 rule, and the import probe proves no open under `checkpoints/` or `data/`.

## Self-Check: PASSED

- FOUND: scripts/phase42_prereg.py, tests/test_phase42_prereg.py
- FOUND commits: 6467a99, db21017, c2f66c4
- No edits to STATE/ROADMAP/REQUIREMENTS/PROJECT; no gsd-sdk handler called.
