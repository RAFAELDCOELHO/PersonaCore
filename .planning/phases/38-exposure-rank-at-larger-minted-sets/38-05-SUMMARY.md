---
phase: 38-exposure-rank-at-larger-minted-sets
plan: 05
subsystem: prereg
tags: [rank-01, e5, set-sizes, fill, phase35-legs, caps]
requires: [results/phase38_minting.json (7357577), scripts/phase38_prereg.py, scripts/phase36_caps.py]
provides: [scripts/phase38_sizes_prereg.py (fill file 2, E5_SET_SIZES)]
affects: [38-08..38-10 rank/report records (must follow this file's commits, leg a)]
tech-stack:
  added: []
  patterns: [fill file reading a committed record, open-audit-hook checkpoint probe]
key-files:
  created: [scripts/phase38_sizes_prereg.py, tests/test_phase38_sizes_prereg.py]
  modified: []
key-decisions:
  - "Truth 4 (torch-free import) was a false premise; orchestrator chose option 1: keep the module-level D-23 caps call, test own imports (AST) + no checkpoint opened (audit hook)"
requirements-completed: []  # the orchestrator owns the RANK-01 tick at phase close
duration: ~35 min
completed: 2026-10-04
---

# Phase 38 Plan 05: E5 set sizes declared from the minting record — Summary

`scripts/phase38_sizes_prereg.py` fills `e5_set_sizes` once, from the committed minting record via
`phase38_prereg.max_set_size(n_cleared)`. Seven slots get 512 and birth_year gets 220. The fill sits
inside the committed E5 caps and lands after minting and before any scoring record.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 | b2416ee | feat: the sizes fill file + sizes/caps/import tests |
| 2 | 66621c6 | test: ancestry legs (a)/(b), typed-size and prefixes AST gates, zero skips |

## Measured output

RED, before the module existed: `1 failed, 2 errors in 0.44s` (ModuleNotFoundError: phase38_sizes_prereg).

Printed `E5_SET_SIZES` (plan acceptance command):
```
{'person_name': 512, 'pet_name': 512, 'cat_name': 512, 'sibling_name': 512, 'hometown': 512, 'street': 512, 'birth_year': 220, 'house_number': 512} True
```
Every value equals the record's own `slots[*].max_set_size` (record n_cleared: birth_year 219, the
rest >= 2048). The trailing `True` is `'torch' in sys.modules`. See the false premise below.

Targeted verify, after both commits:
`tests/test_phase38_sizes_prereg.py tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase38_prereg.py` → `187 passed in 39.53s`.
`ruff check .` → `All checks passed!`. `ruff format --check .` → `352 files already formatted`.
Named legs: `test_slot_census_is_green_on_the_real_tree`, `test_slot_ordering_is_green_on_the_real_repo`,
`test_owner_fill_files_respect_the_caps_on_the_real_repo` (now on its live branch) and
`tests/test_phase21_sc5.py` → `7 passed in 4.53s`.
`git status --porcelain -- scripts src results tests ledger artifacts` → empty.
`git ls-files 'results/phase38_*'` → `results/phase38_minting.json` only.

Full suite: not run by this executor, per the brief. The orchestrator runs it after the wave.

## Deviations from Plan

**1. False premise: truth 4, "the file imports torch-free"**
- **Found during:** Task 1. The plan's torch-free probe went red.
- **Trace:** `check_unit_caps` (phase36_caps.py:172) → `committed_budget` (:160) → `prove_budget_shape`
  (:132, `len(phase35_prereg.seed_list())`) → phase35_prereg.py:366 lazy `import phase23_run` →
  phase23_run.py:105 `import teach_persona` → teach_persona.py:66 `import torch`.
  `import phase36_caps` on its own leaves torch unloaded. The analog `phase36_budget_prereg` also
  loads torch on import. `test_owner_fill_files_respect_the_caps_on_the_real_repo` already calls
  `committed_budget()` in-process.
- **Resolution:** the orchestrator chose option 1. The module-level D-23 caps call stays, so truth 3
  and the key_link hold. The torch probe was replaced by two tests:
  - `test_the_sizes_file_imports_only_json_pathlib_and_three_torch_free_modules`: an AST check that the
    file imports exactly json, pathlib, phase35_prereg, phase36_caps and phase38_prereg, and nothing
    from `_HEAVY`. A planted `import teach_persona` reds it.
  - `test_importing_the_sizes_file_opens_no_checkpoint`: a fresh subprocess with a `sys.addaudithook`
    "open" hook sees no `checkpoints/`, `.pt` or `.safetensors` path. A planted
    `open('checkpoints/planted.pt')` is seen, which is the non-vacuity leg.
- No rule, value or definition changed.

**2. Small departure from the plan's test list.** Task 2 item 6 (the `_HEAVY` subprocess probe) is
covered by deviation 1's two tests instead.

## Known Stubs
None.

## Self-Check: PASSED
- FOUND: scripts/phase38_sizes_prereg.py, tests/test_phase38_sizes_prereg.py
- FOUND: b2416ee, 66621c6 (`git log --oneline -3`)
- Untouched: scripts/phase38_prereg.py, scripts/phase38_mint.py, results/phase38_minting.json and
  STATE/ROADMAP/REQUIREMENTS. No gsd-sdk mutation handler was called.
