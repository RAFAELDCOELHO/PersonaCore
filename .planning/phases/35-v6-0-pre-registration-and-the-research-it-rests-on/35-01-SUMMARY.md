---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
plan: 01
subsystem: prereg
tags: [prereg, differential-privacy, one-run-audit, composition, ancestry]

requires:
  - phase: 25 (v4.0)
    provides: phase25_epsilon.curve_total, SELECTION_ACCOUNTED; mitigation_unit.DELTA
  - phase: 29 (v5.0)
    provides: phase29_prereg register (_prove/_prove_count), tests/test_phase29_prereg.py helpers (_git, _planted)
provides:
  - .planning/research/V6-PREREG-09.md (PREREG-09 research note, committed alone first)
  - scripts/phase35_prereg.py skeleton (entry schema, one-run audit port, composition by reference)
  - tests/test_phase35_prereg.py (23 CPU tests, 0 skips; _git_in/_planted_repo helpers for Plan 04)
affects: [35-02, 35-03, 35-04, 35-05, phase 42 (E3), phase 43 (E4)]

tech-stack:
  added: []
  patterns:
    - "Four-field entry schema {value, derivation, kind, source}, proved at import by _prove_entry"
    - "Research-before-threshold ordering as a git ancestry test (note first-add is ancestor of every prereg commit)"
    - "Planted REDs anchored by AST lineno/col_offset (UTF-8 byte column), never str.replace"

key-files:
  created:
    - .planning/research/V6-PREREG-09.md
    - scripts/phase35_prereg.py
    - tests/test_phase35_prereg.py
  modified: []

key-decisions:
  - "one_run_tolerance = 1e-3 (one unit in the last printed digit; paper rounds PIN 1 and truncates PIN 2)"
  - "E3 accounting is basic composition only, SELECTION_ACCOUNTED False by reference (Papernot-Steinke hypotheses 1, 2, 4 fail for E3)"

patterns-established:
  - "_git_in(repo) / _planted_repo(root, commits): shared real-repo and throwaway-repo git check bodies"

requirements-completed: []
# The orchestrator ticks requirements at phase close; this plan's `requirements:` list
# (PREREG-09, PREREG-06, PREREG-07, PREREG-08) names IDs it contributes to, not IDs it closes.

duration: 5min
completed: 2026-10-01
---

# Phase 35 Plan 01: PREREG-09 research and the v6.0 prereg skeleton Summary

**PREREG-09 note committed alone first; then a stdlib port of Steinke-Nasr-Jagielski App. D reproducing 0.673 (p. 46) and 2.675 (p. 28) within 1e-3, E3 basic composition bound by `is` to phase25_epsilon, and a four-field proposer-free entry schema, all pinned by 23 CPU tests.**

## Performance

- **Duration:** ~5 min (base 4d49ba5 at 18:23:31 -0300; last task commit 18:28:02 -0300)
- **Started:** 2026-10-01T21:23:31Z (approx., base commit time)
- **Completed:** 2026-10-01
- **Tasks:** 3 (Task 1 alone; Tasks 2+3 together)
- **Files created:** 3

## Accomplishments

- `.planning/research/V6-PREREG-09.md`: paraphrases Algorithm 1 (p. 3), Theorem 5.2 (p. 14), Corollary 5.4 (pp. 15-16), Lemma 4.7 (pp. 8-9), Appendix D (pp. 45-46) of arXiv 2305.08846v1, and Theorem 2 (p. 5), Corollaries 3-4 (p. 6), Theorem 6 (p. 7), §3.3 hypotheses (p. 5) of arXiv 2110.03620v2; reproduction table, tolerance derivation (no number written), closed form, Phase 43 constraints, max-detectable-ε observation table; E3 verdict: hypotheses 1, 2, 4 fail, 3 moot, basic composition only.
- `scripts/phase35_prereg.py`: `_prove`, `_prove_count`, `ENTRY_FIELDS`, `KINDS`, `FORBIDDEN_PHRASE`, `_prove_entry`, `CURVE_TOTAL`, `SELECTION_ACCOUNTED`, `DELTA`, `_binom_pmf`, `p_value_one_run`, `eps_lower_one_run`, `ONE_RUN_PUBLISHED`, `one_run_reproduction_holds`, `_ENTRIES`/`ENTRIES` (4 entries), `_prove_entries()` at import.
- `tests/test_phase35_prereg.py`: 23 tests, 0 skipped.

## Measured values (tool output)

- PIN 1 `eps_lower_one_run(1000, 100, 75, 1e-4, 0.05)` = 0.6729846633970737 (published 0.673)
- PIN 2 `eps_lower_one_run(100000, 1510, 1439, 1e-5, 0.05)` = 2.6758510060608387 (published 2.675)
- Closed form r = 16: port 1.5803231354802847 vs exact 1.5803231357927883
- Dropped-δ mutant on PIN 1 inputs: 0.7022139308974147 (outside 1e-3)
- `one_run_reproduction_holds()` = True; `'torch' in sys.modules` = False after import
- Versions: no re-fetch performed (plan: not needed); the note cites v1 (2305.08846, only version) and v2 (2110.03620) as confirmed on the abs pages during 35-RESEARCH on 2026-10-01.

## Task Commits

1. **Task 1: PREREG-09 research note** — `8fba327` (docs), only `.planning/research/V6-PREREG-09.md`; at that moment `git log -- scripts/phase35_prereg.py` printed nothing.
2. **Tasks 2+3: module + tests** — `ce659f4` (feat), `scripts/phase35_prereg.py`, `tests/test_phase35_prereg.py`. `git merge-base --is-ancestor 8fba327 ce659f4` succeeds.

## Acceptance results

- Task 1 verify: `missing []`; `não verificado` absent; `git show --stat HEAD` listed only the note.
- Task 2 verify: `0.6729846633970737 2.6758510060608387 True`; ruff check "All checks passed!", format "already formatted".
- Task 2 identity check: `True True True ['delta', 'e3_composition', 'e3_selection_accounted', 'one_run_tolerance']`.
- Task 2 proposer refusal: exit 1, `[phase35_prereg] entry 'x' carries a 'proposer' key. D-14: ...`.
- Task 3 `-k "one_run or composition or research_note or entries or no_proposer or no_skips or without_torch"`: 23 passed, 0 skipped; per-selector counts one_run 14, composition 1, research_note 3, entries 2, no_proposer 1, no_skips 1, without_torch 1.
- After commit, clean tree: `tests/test_phase21_sc5.py tests/test_phase25_driver.py tests/test_phase21_unit_continuation.py tests/test_phase20_correction.py` → 72 passed.
- `tests/test_phase25_prereg.py -k bit_identity` → 2 passed, 18 deselected.
- Plan verification: `tests/test_phase35_prereg.py tests/test_phase29_prereg.py` → 103 passed; `ruff check .` all passed, `ruff format --check .` 327 files already formatted; no `results/phase3[5-9]_*`/`phase4[0-5]_*` tracked or on disk.
- `== 10` wall pattern (python `re`) finds nothing in either new file.

## Deviations from Plan

1. **[Rule 3 - minor structure] Private `_p_value` core.** `p_value_one_run` validates then calls `_p_value`; `eps_lower_one_run` validates once and bisects on `_p_value`, so the ~60 inner evaluations do not re-run input validation. Behaviour identical to the plan's spec. Commit ce659f4.
2. **`_prove_real` helper** for the int-or-float-not-bool checks on `delta`, `beta`, `eps` (inside `_prove_one_run_inputs`).
3. **tests/ on sys.path** in the test file, in addition to scripts/ and src/, following the `tests/test_phase31_budget.py:20-22` precedent the plan cites for importing `test_phase29_prereg`.
4. **Infinite-eps refusal is its own test** (`test_one_run_p_value_refuses_an_infinite_eps`) rather than inside the parametrized test; still selected by `-k one_run`.
5. **AST insertion uses UTF-8 byte columns** (`_insert_at`), since `ast` `col_offset` is a byte offset and the module contains `§`.

## Known Stubs

None. The module is a deliberate skeleton: core, slot registry and E1/E4 rules arrive in Plans 02-03, as the plan states.

## Self-Check: PASSED

- FOUND: .planning/research/V6-PREREG-09.md, scripts/phase35_prereg.py, tests/test_phase35_prereg.py
- FOUND commits: 8fba327, ce659f4
