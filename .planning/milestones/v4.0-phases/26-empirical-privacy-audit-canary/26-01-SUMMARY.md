---
phase: 26-empirical-privacy-audit-canary
plan: 01
subsystem: privacy-audit
tags: [pre-registration, dated-continuation, ancestry-guard, wilson, epsilon-lower, canary]
requires:
  - scripts/phase25_prereg.py (CANARY_RESERVATIONS["audit_target_rule"], PUBLICATION_OBLIGATION — by reference)
  - scripts/erasure_gate.py (wilson_upper_bound, _Z_ONE_SIDED_95, VERDICTS register)
  - scripts/phase20_gate_coverage.py (wilson_lower_bound)
  - scripts/mitigation_unit.py (PRIVACY_UNIT, DELTA)
  - scripts/phase25_record.py (ORDERED_POINT_KEYS, FRONTIER_RECORD)
  - results/phase25_frontier.json (read as data, never modified)
provides:
  - scripts/phase26_prereg.py — the dated Phase-26 pre-registration (rule by reference, resolver, extension, power gate, D-09 arithmetic, ceiling, verdict domain, constants, waiver + obligation continuations)
  - tests/test_phase26_prereg.py — two ancestry guards, resolution, extension, threshold, six-row formula table, degenerate cases, verdict domain, continuation data
affects:
  - 26-02 (driver imports every exported name), 26-03 (tests), 26-05 (close), Phase 28 (PUBLICATION_OBLIGATION_CONTINUATION)
tech-stack:
  added: []
  patterns: [continuation-by-reference (phase21_unit_continuation), Phase-18 ancestry guard with strictly-after conjunct, _prove -> SystemExit, CPU-only at import]
key-files:
  created:
    - scripts/phase26_prereg.py
    - tests/test_phase26_prereg.py
  modified: []
decisions:
  - "COMMITTED = 2026-09-10; SIDECARS_AT_COMMIT = 0 — git ls-files 'results/phase26_*' empty at both commits"
  - "DECIDING_TIER = taught; EXCLUSION_SCOPE = either; MEMBERSHIP_RULE existential (>= 1 deciding-tier question with k > 0) — RESEARCH Open Questions 2-3 decided as module constants with rationale"
  - "epsilon_lower degenerate cases are NAMED, never clipped: (0,1008,0,784) returns -0.0035, not 0"
  - "PUBLICATION_OBLIGATION_CONTINUATION is a Python constant extending phase25_prereg.PUBLICATION_OBLIGATION by reference, not an _addendum.py append"
metrics:
  duration: ~25 min
  completed: 2026-09-10
  tasks: 2
  files: 2
---

# Phase 26 Plan 01: The Phase-26 Pre-Registration Summary

The dated continuation of `phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]` and `phase21_filler.GUESSABILITY_WAIVER` is committed as `scripts/phase26_prereg.py` — rule imported by reference, resolver proving it yields `dp_n8_sigma0p000000`, extension to all 15 noised `dp_n8` points, power gate derived from the artifact, D-09 `epsilon_lower` composed from the two imported Wilson bounds with degenerate cases named, the D-13 ceiling, the three-valued one-sided verdict domain, and the D-40 publication-obligation continuation — frozen by two git-ancestry guards before any `results/phase26_*` file exists.

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write scripts/phase26_prereg.py | `e6a8851` | scripts/phase26_prereg.py (395 lines) |
| 2 | Write tests/test_phase26_prereg.py | `3198506` | tests/test_phase26_prereg.py (259 lines, 12 `def test_`, 17 collected) |

Base: `9e71338` on `main`. Both commits made with hooks; explicit `git add <file>` only.

## Acceptance criteria — verified by running them

**Task 1 verify one-liner** (plan `<automated>`), output: `OK` — asserts `RULE is CANARY_RESERVATIONS['audit_target_rule']`, resolver == control, 16/15 keys, `power_threshold == points['dp_n8_sigma80p000000']['epsilon']`, `epsilon_lower(8,8,0,56) ≈ 2.7859`, `epsilon_lower(0,1008,0,784)['direction_1'] is None`, `VERDICTS`, `'torch' not in sys.modules` and `'phase14_factset' not in sys.modules`. `ruff check` → `All checks passed!`; `ruff format --check` → `1 file already formatted`.

Observed degenerate rows (quoted from the run):
- `epsilon_lower(0,1008,0,784)` → `direction_1: None, direction_2: -0.003455041984893167, epsilon_lower: -0.003455041984893167, degenerate: ['TPR_lb <= delta: direction 1 undefined']` — negative, NOT clipped.
- `epsilon_lower(8,8,56,56)` → `fpr_ub: 1.0, direction_2: None, degenerate: ['FPR_ub >= 1 - delta: direction 2 undefined']`.
- `point_verdict(epsilon_lower(8,8,0,56), 2.3957449097512216, ...)` → `BROKEN`, reasons carry `8/8`, `0/56`, `TPR_lb = 0.7473`, `FPR_ub = 0.0461`, both directions, `epsilon_lower = 2.7858978325772576 vs epsilon_upper = 2.3957449097512216`, the one-sided clause and the Bonferroni joint-coverage clause.
- Reachable claims at the fact unit: exactly 4 of 15 (`sigma 24, 32, 50, 80`) below `auditor_ceiling(8, 56)`.

**Task 2:**
- `.venv/bin/python -m pytest -q tests/test_phase26_prereg.py` → `17 passed in 0.76s` (6 parametrized rows + 11 named tests; 0 failed, 0 skipped).
- `.venv/bin/python -m pytest -q tests/test_phase25_close.py tests/test_phase16_prereg.py` → `32 passed in 18.66s`.
- Plan-level: `.venv/bin/python -m pytest -q tests/test_phase26_prereg.py tests/test_phase25_close.py tests/test_phase16_prereg.py` → `49 passed in 20.46s`.
- `grep -c "def test_" tests/test_phase26_prereg.py` → `12`.
- `git ls-files 'results/phase26_*'` → empty at `e6a8851` (via `git ls-tree -r HEAD~1`) and at `3198506`.
- `git diff --stat HEAD~2 -- scripts/phase25_prereg.py scripts/teach_persona.py scripts/phase18_extraction.py results/phase25_frontier.json` → empty.

### Planted RED (throwaway `git clone` in the session scratchpad — never on `main`; discarded afterwards)

Clone of the repo at `3198506`; committed `results/phase26_x.json` (`02e64fa`, fake first-add), then appended one byte to `scripts/phase26_prereg.py` (`4282432`). Running the two guards in the clone:

```
tests/test_phase26_prereg.py:75: in _assert_frozen_before
popenargs = (('git', 'merge-base', '--is-ancestor', '42824321d907296014a41daa0198bdd2c9f021a9', '02e64fa87a1fc8390f2158b22d24b9a8371a122e'),)
E   subprocess.CalledProcessError: Command '('git', 'merge-base', '--is-ancestor', '4282432…', '02e64fa…')' returned non-zero exit status 1.
1 failed, 1 passed in 1.20s
```

`test_phase26_prereg_is_frozen_before_every_phase26_result` went RED on the ancestor conjunct (the post-artifact prereg edit is not an ancestor of the artifact's first-add); `test_phase25_prereg_is_byte_identical_since_the_frontier` stayed green in the clone, correctly — `phase25_prereg.py` was untouched there and precedes the fake add. The clone was deleted; `main` never carried the planted commits.

## Deviations from Plan

**1. [Rule 1 - Bug] Test substring case corrected during Task 2**
- **Found during:** Task 2 first run (1 failed).
- **Issue:** `test_the_continuations_are_data` asserted `"filler is never scored"` in the waiver; the waiver's actual text is `"Filler is never scored"` (sentence-initial capital). The planned lowercase phrase is the CONTEXT's paraphrase, not the module's text.
- **Fix:** assert the module's real phrase (`"Filler is never scored"`), plus `"DELIBERATELY NOT RUN"`, to prove the waiver is unchanged.
- **Files modified:** tests/test_phase26_prereg.py (before commit).
- **Commit:** `3198506`.

Otherwise the plan executed as written. Both `_addendum.py` and `phase21_filler` are referenced by name only; `phase21_filler` is imported inside the one test that reads the waiver.

## Known Stubs

None. Every exported name is data or a pure function over the frontier / counts.

## Threat Flags

None beyond the plan's register. No new network/auth/file surface: the module reads the committed frontier as data and writes nothing.

## Self-Check: PASSED

- `scripts/phase26_prereg.py` — FOUND
- `tests/test_phase26_prereg.py` — FOUND
- commit `e6a8851` — FOUND
- commit `3198506` — FOUND
