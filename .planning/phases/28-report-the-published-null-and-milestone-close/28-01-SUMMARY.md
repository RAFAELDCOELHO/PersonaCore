---
phase: 28-report-the-published-null-and-milestone-close
plan: 01
subsystem: tests
tags: [rpt-03, tomllib, docstrings, d-25, d-26, d-27, d-32]
requires: []
provides:
  - "tests/test_package.py::test_runtime_dependencies_identical_across_four_milestones (D-25)"
  - "tests/test_package.py::test_pyproject_sha256_pin_detects_any_change (D-26 rename, D-27 one-liner)"
  - "tests/test_perplexity.py::test_docstring_states_the_true_denominator (D-32)"
  - "tests/test_phase16_driver.py::test_overwrite_statement_docstring_does_not_type_the_allowlist_size (D-32)"
affects: [28-03 ledger rows FIXED for perplexity.py:11-13 and phase16_persistence.py:1605]
tech-stack:
  added: []
  patterns: ["git show <tag>:pyproject.toml -> tomllib.loads equality across tags; shallow/tagless clone refused"]
key-files:
  created: []
  modified:
    - tests/test_package.py
    - src/personacore/evaluation/perplexity.py
    - scripts/phase16_persistence.py
    - tests/test_perplexity.py
    - tests/test_phase16_driver.py
decisions:
  - "D-25 test does not type the dependency names; equality across four revisions is the claim"
  - "perplexity docstring test reads the MODULE docstring via sys.modules[perplexity.__module__] because the test file imports the function name"
  - "tests/test_perplexity.py's own header restated the false denominator; corrected in the same commit"
metrics:
  duration: "~10 min"
  completed: "2026-09-20"
---

# Phase 28 Plan 01: Code-side FIXED items and the RPT-03 tomllib test Summary

RPT-03's four-milestone zero-new-dependency claim is now a `tomllib` equality test over `git show v1.0/v2.0/v3.0:pyproject.toml` and HEAD; the sha pin survives under a true name; two false docstrings (perplexity denominator, allowlist size) are corrected, each with a regression test watched RED first.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 — D-25 tomllib test, D-26 rename, D-27 one-liner | `d45eaec` | tests/test_package.py |
| 2 — D-32 docstrings + regression tests | `dd087f7` | src/personacore/evaluation/perplexity.py, scripts/phase16_persistence.py, tests/test_perplexity.py, tests/test_phase16_driver.py |

## Test node ids created (for 28-03 ledger rows)

- `tests/test_package.py::test_runtime_dependencies_identical_across_four_milestones`
- `tests/test_package.py::test_pyproject_sha256_pin_detects_any_change` (renamed from `test_pyproject_unchanged_since_v2_close`; `grep -c` of the old name in tests/test_package.py = 0; no other file under tests/ or scripts/ references it)
- `tests/test_perplexity.py::test_docstring_states_the_true_denominator`
- `tests/test_phase16_driver.py::test_overwrite_statement_docstring_does_not_type_the_allowlist_size`

## Measured dependency list (D-25)

```
$ .venv/bin/python -c "import tomllib,subprocess;print(tomllib.loads(subprocess.run(['git','show','v1.0:pyproject.toml'],capture_output=True,text=True).stdout)['project']['dependencies'])"
['numpy~=2.4', 'regex~=2026.5']
```
Test asserts `_deps("v1.0") == _deps("v2.0") == _deps("v3.0") == head` — green, so all four are this list. Tags present: `m1-demo-v1 v1.0 v2.0 v3.0`; `git rev-parse --is-shallow-repository` = `false`.
`shasum -a 256 pyproject.toml` = `15ffd6b58e289447ac6460bdd6210c04d20d5ff5831f741bb3db3bdc0ca7926f` (unchanged; pyproject.toml untouched).

## Guard status re-measured before editing (D-32 / T-28-09)

```
$ grep -rl "phase16_persistence.py" results/*.json
(empty)
$ grep -rn "phase16_persistence" tests/test_phase16_prereg.py
(empty)
$ grep -rl "evaluation/perplexity.py" results/*.json tests/test_phase16_prereg.py tests/test_phase20_prereg.py
(empty)
```
Neither module is named by a record `module_sha256` or an ancestry test → safe to edit → `FIXED`.

## Natural RED (tests written before the docstring edits)

```
E       AssertionError: the docstring must state the true denominator
E       assert 'corpus_len - 1' in 'Deterministic full-corpus perplexity (EVAL-01).\n\n...'
E       AssertionError: the docstring must not type the allowlist size
E       assert 'exactly two entries' not in 'A STATEMENT...ds it.\n    '
FAILED tests/test_perplexity.py::test_docstring_states_the_true_denominator
FAILED tests/test_phase16_driver.py::test_overwrite_statement_docstring_does_not_type_the_allowlist_size
2 failed in 0.95s
```

## GREEN after the edits

```
$ .venv/bin/pytest tests/test_perplexity.py tests/test_phase16_driver.py tests/test_phase16_prereg.py tests/test_phase18_prereg.py -q
109 passed in 22.35s
$ .venv/bin/pytest tests/test_package.py -q -v
4 passed in 0.09s
$ make lint
All checks passed!
284 files already formatted
```

## Docstring-only diff (Task 2)

```
$ git diff --stat -- src/personacore/evaluation/perplexity.py scripts/phase16_persistence.py
 scripts/phase16_persistence.py           | 4 ++--
 src/personacore/evaluation/perplexity.py | 7 ++++---
```
Both hunks are inside triple-quoted docstrings; no executable line changed. The true denominator was confirmed from the code before rewriting the prose: slices are `data[i:i+block_size+1]` at stride `block_size` (`perplexity.py:61-62`), so each window's shifted target is the next window's first token and only corpus token 0 goes unscored — exactly what `test_token_count` asserts (`ntok == n_tokens - 1`).

## Deviations from Plan

**1. [Rule 1 - Bug] `perplexity` in tests/test_perplexity.py is the function, not the module**
- **Found during:** Task 2 RED run — `perplexity.__doc__` returned the function docstring.
- **Fix:** the test reads `sys.modules[perplexity.__module__].__doc__` (the module docstring D-32 names) instead of adding a second import.
- **Commit:** `dd087f7`

**2. [Rule 1 - Bug] tests/test_perplexity.py's module header restated `corpus_len - n_windows`**
- **Found during:** Task 2 — the plan's `contains: "corpus_len - n_windows"` artifact check is satisfied by the new test's negative assertion, but the header bullet 2 stated the false denominator as fact.
- **Fix:** header now reads "`corpus_len - 1` for a cleanly tiling corpus (token 0 is the only unscored token, D-03)".
- **Commit:** `dd087f7`

**3. ruff import sort** placed `tomllib` in its own block after `subprocess` (ruff's stdlib list); accepted ruff's `--fix` output so `make lint` is green.

## Known Stubs

None.

## Threat Flags

None — no new network, auth, file-access or schema surface; T-28-04, T-28-05, T-28-09, T-28-SC mitigations applied as planned.

## Self-Check: PASSED

- tests/test_package.py, tests/test_perplexity.py, tests/test_phase16_driver.py, src/personacore/evaluation/perplexity.py, scripts/phase16_persistence.py — present
- commits d45eaec, dd087f7 — present in `git log`
