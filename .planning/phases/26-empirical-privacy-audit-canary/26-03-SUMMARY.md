---
phase: 26-empirical-privacy-audit-canary
plan: 03
subsystem: testing
tags: [privacy-audit, canary, pytest, AST, sidecar, plist]

# Dependency graph
requires:
  - phase: 26-02
    provides: phase26_canary.py driver and the canary LaunchAgent plist
  - phase: 26-01
    provides: phase26_prereg.py audit contracts and verdict rules
provides:
  - CPU-only structural and refusal tests for the Phase-26 canary driver
  - End-to-end stubbed-draw wiring proof through main(), sidecars, and emit()
  - Frontier-link, power-gate RED, git-surface, and plist coverage
affects: [26-04, 26-05, empirical-privacy-audit]

# Tech tracking
tech-stack:
  added: []
  patterns: [AST structural guards, tmp_path sidecar isolation, real score_question wiring proof]

key-files:
  created:
    - tests/test_phase26_canary.py
    - .planning/phases/26-empirical-privacy-audit-canary/26-03-SUMMARY.md
  modified: []

key-decisions:
  - "Keep phase14_recall out of test collection; import it only inside helpers or live tests."
  - "Preserve the real phase14_recall.score_question boundary while stubbing only model loading and draws."

patterns-established:
  - "Use AST walks for import, torch.load, and git-argv structural claims."
  - "Exercise forged-artifact RED states only on tmp_path copies."

requirements-completed: [CANARY-01, CANARY-02]

# Metrics
duration: not measured
completed: 2026-09-11
---

# Phase 26: Empirical Privacy Audit Canary Summary

**CPU-only tests pin the canary’s item grammar, lazy imports, hash-pinned sidecars, live wiring, power gate, plist, and frontier linkage.**

## Performance

- **Duration:** not measured
- **Started:** not recorded
- **Completed:** 2026-09-11
- **Tasks:** 2
- **Files modified:** 2 created

## Accomplishments

- Added 19 named tests covering both Task 1 structural/refusal behavior and Task 2 live wiring.
- Proved `main()` → adapter-off/control/noised scoring → real producer-shaped sidecars → `emit()` on stubbed draws, with the real `score_question` and `prove_reproduction` routing.
- Added RED tests for forged power-gate passes and planted git pushes, plus frontier, plist, write-once, and path-separator guards.

## Task Commits

Each task was committed atomically by the supervising process after this sandbox run:

1. **Task 1: Structural canary tests** - `cae77d8` (`test(26-03): pin canary structural and refusal paths`)
2. **Task 2: Live wiring and gate tests** - `4d4c7f9` (`test(26-03): prove canary live wiring and gate protections`)


## Files Created/Modified

- `tests/test_phase26_canary.py` - CPU-only Phase-26 driver, wiring, threat, plist, and artifact-link tests.
- `.planning/phases/26-empirical-privacy-audit-canary/26-03-SUMMARY.md` - this execution summary.

## Decisions Made

- Followed the plan’s real-driver boundary: only `load_adapted_model`, `complete_question`, and the reproduction recorder are stubbed in the live proof; `score_question`, hashing, sidecar writes, and `emit()` remain real.
- Kept all generated sidecars and artifacts under `tmp_path`; no `data/phase26_*` or `results/phase26_*` files were created.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the OUT-versus-IN leakage assertion**
- **Found during:** post-implementation manual review of Task 1.
- **Issue:** the test used the OUT item’s own `fact.value` instead of the iterated `in_fact.value`, so it did not test whether locked IN values appeared in OUT questions.
- **Fix:** changed the assertion to check `pr.contains_value(question, in_fact.value)` and renamed the OUT item binding to `_fact`.
- **Files modified:** `tests/test_phase26_canary.py`
- **Verification:** `.venv/bin/python -m pytest -q tests/test_phase26_canary.py` → `18 passed, 1 skipped`.
- **Committed in:** `cae77d8` (part of Task 1 test commit).

**2. [Rule 1 - Naming] Matched the exact planned equality-test name**
- **Found during:** post-implementation manual review of Task 1.
- **Issue:** the function was named `test_the_in_items_equal_calibration_items_exactly`, but the plan requires `test_in_items_equal_calibration_items_exactly`.
- **Fix:** renamed the test to the exact plan name.
- **Files modified:** `tests/test_phase26_canary.py`
- **Verification:** `grep -c "def test_" tests/test_phase26_canary.py` → `19`; the full canary file passed.
- **Committed in:** `cae77d8` (part of Task 1 test commit).

**3. [Rule 1 - Structure] Split plistlib checks from the plutil lint check**
- **Found during:** post-implementation manual review of Task 1.
- **Issue:** `@needs_plutil` skipped all plist structural assertions on hosts without `plutil`, although only the subprocess lint requires that utility.
- **Fix:** removed `@needs_plutil` from `test_the_canary_agent_mirrors_the_recall_agent`, removed its lint assertion, and added the separately marked `test_the_canary_agent_plist_lints`.
- **Files modified:** `tests/test_phase26_canary.py`
- **Verification:** 19 test functions collected; `18 passed, 1 skipped`; the canary plist lint passed on this host.
- **Committed in:** `cae77d8` (part of Task 1 test commit).

---

**Total deviations:** 3 auto-fixed (1 bug, 1 naming correction, 1 structural split)
**Impact on plan:** All three corrections restore the plan’s exact semantic or portability contract; no production scope was added.

## Issues Encountered

- No driver defect was found.
- Spec gap found by the supervisor's full-suite run (see "Full-suite status" below): landing this plan's one by-design skip moves `tests/test_phase25_venue.py`'s D-44 skip-count register by the plan's own predicted +1, and that register's hardcoded expectations were not updated (its file is outside 26-03's scope) — 2 known, predicted, out-of-scope failures remain in the repo-wide suite; every test this plan owns is green.
- The sandbox addendum prohibited git writes and the full repository suite inside codex's own run, so task commit hashes, final clean status, and full-suite counts were filled in by the supervising process after the codex run.

## Verification Evidence

### Task 1 acceptance command

Command:

```text
.venv/bin/pytest -q tests/test_phase26_canary.py -x -k "not live_path and not routes_its_in_taught and not power_gate and not sibling and not reproduced" && .venv/bin/ruff check tests/test_phase26_canary.py
```

Output:

```text
..............                                                           [100%]
14 passed, 5 deselected in 1.87s
All checks passed!
```

### Task 2 acceptance command

Command:

```text
.venv/bin/pytest -q tests/test_phase26_canary.py -x && PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/pytest -q tests/test_phase26_canary.py tests/test_phase26_prereg.py && .venv/bin/ruff check tests/test_phase26_canary.py && .venv/bin/ruff format --check tests/test_phase26_canary.py
```

Output:

```text
..................s                                                      [100%]
18 passed, 1 skipped in 2.28s
..................s.................                                     [100%]
35 passed, 1 skipped in 3.08s
All checks passed!
1 file already formatted
```

### Requested post-fix verification

Command:

```text
.venv/bin/python -m pytest -q tests/test_phase26_canary.py
```

Output:

```text
..................s                                                      [100%]
18 passed, 1 skipped in 2.73s
```

Command:

```text
.venv/bin/python -m pytest -q tests/test_phase26_prereg.py tests/test_phase25_recall.py tests/test_phase26_canary.py
```

Output:

```text
...............................................s                         [100%]
47 passed, 1 skipped in 3.99s
```

Command:

```text
.venv/bin/python -m ruff check tests/test_phase26_canary.py
```

Output:

```text
All checks passed!
```

Command:

```text
.venv/bin/python -m ruff format --check tests/test_phase26_canary.py
```

Output:

```text
1 file already formatted
```

Command:

```text
PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest -q tests/test_phase26_canary.py tests/test_phase26_prereg.py
```

Output:

```text
..................s.................                                     [100%]
35 passed, 1 skipped in 2.95s
```

Command:

```text
grep -c "def test_" tests/test_phase26_canary.py
```

Output:

```text
19
```

### Live wiring evidence

Command:

```text
.venv/bin/python -m pytest -q tests/test_phase26_canary.py::test_the_live_path_is_wired_end_to_end -s
```

The test passed and emitted this evidence line:

```text
PHASE26_WIRING_EVIDENCE {"auditor_ceiling": 2.7858978325772576, "point_key": "dp_n8_sigma0p500000", "power_gate": {"control_epsilon_lower": -0.047192951865113845, "passed": false, "sentence": "The instrument must resolve at least the smallest claim it checks.", "threshold": 0.6339783761989397}, "reachable_claims": "4/15", "verdict_reasons": ["members answered 0/8 and nonmembers answered 0/56 at the unit 'one taught fact'", "TPR_lb = 0.0000 (Wilson lower), FPR_ub = 0.0461 (Wilson upper), z = 1.6448536269514722, delta = 1e-05", "direction_1 = TPR_lb <= delta: direction 1 undefined", "direction_2 = -0.0472", "epsilon_lower = -0.047192951865113845 vs epsilon_upper = 519.6981942303134: INCONCLUSIVE \u2014 this test can only accuse; CONSISTENT is not 'verified correct'", "joint coverage >= 0.90 (Bonferroni over two one-sided 95% Wilson bounds, z = erasure_gate._Z_ONE_SIDED_95)", "epsilon_upper >= auditor_ceiling: this comparison could not have failed (auditor_ceiling = 2.7858978325772576)", "The instrument must resolve at least the smallest claim it checks. Power gate FAILED: control epsilon_lower = -0.047192951865113845 < threshold 0.6339783761989397"]}
.
1 passed in 1.35s
```

Captured values:

- `power_gate`: `{'control_epsilon_lower': -0.047192951865113845, 'passed': False, 'sentence': 'The instrument must resolve at least the smallest claim it checks.', 'threshold': 0.6339783761989397}`
- `auditor_ceiling`: `2.7858978325772576`
- `reachable_claims`: `4/15`
- noised point `dp_n8_sigma0p500000` reasons: the seven strings in the evidence line above, including the `0/8`, `0/56`, epsilon comparison, one-sided, joint-coverage, ceiling, and failed-power disclosures.

### Control-read skip proof

Command:

```text
.venv/bin/python -m pytest -q tests/test_phase26_canary.py::test_the_control_reproduced_the_published_reading -rs
```

Output:

```text
s                                                                        [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/test_phase26_canary.py:646: control sidecar not yet scored — lands during the 26-04 run
1 skipped in 1.09s
```

### Git and residue checks

Commands:

```text
git log --oneline 8ba3692..HEAD
git status --short
ls data/ | grep phase26 ; ls results/ | grep phase26
```

Output before this SUMMARY was created:

```text
?? tests/test_phase26_canary.py
```

The first and third commands produced no output at codex-run time (nothing was committed inside the sandbox, per the addendum forbidding `.git` writes there). The supervising process subsequently split the single combined file into the two task commits above (`cae77d8`, `4d4c7f9`), each independently linted and tested before committing, and re-ran `git log --oneline 8ba3692..HEAD` / `git status --short` / the residue greps after landing this SUMMARY — see the final commit list and clean-status confirmation in the executor's closing report.

Final status check after creating this SUMMARY:

```text
?? .planning/phases/26-empirical-privacy-audit-canary/26-03-SUMMARY.md
?? tests/test_phase26_canary.py
```

### Full-suite status (run by the supervising process, outside the codex sandbox)

Command:

```text
.venv/bin/python -m pytest -q
```

Output:

```text
FAILED tests/test_phase25_venue.py::test_the_sweep_active_skip_count_is_the_number_stated_in_advance
FAILED tests/test_phase25_venue.py::test_with_the_flag_unset_the_baseline_is_unchanged
2 failed, 2782 passed, 5 skipped, 83 warnings in 1368.68s (0:22:48)
```

Combined focused re-run (no regression in the phase's own test files):

```text
.venv/bin/python -m pytest -q tests/test_phase25_close.py tests/test_phase26_prereg.py tests/test_phase25_recall.py tests/test_phase26_canary.py
73 passed, 1 skipped in 4.82s
```

**Spec gap (not fixed, reported):** the 2 failures are both in `tests/test_phase25_venue.py`, a
D-44 "skip count stated in advance" register unrelated to and untouched by this plan. Adding
`tests/test_phase26_canary.py`'s one by-design skip
(`test_the_control_reproduced_the_published_reading`, skipped because the control sidecar has not
been scored yet — it lands in 26-04) moved the whole repo's skip count by exactly +1 in both of
that register's two child-process measurements:

```text
tests/test_phase25_venue.py::test_the_sweep_active_skip_count_is_the_number_stated_in_advance
  AssertionError: ... reports '2733 passed, 40 skipped, ...', but the count stated in advance is 39.
  assert 40 == 39

tests/test_phase25_venue.py::test_with_the_flag_unset_the_baseline_is_unchanged
  AssertionError: ... reports '2768 passed, 5 skipped, ...', not 4 skipped.
  assert 5 == 4
```

This is exactly the plan's own predicted "+1 skipped" delta (26-03-PLAN.md `<verification>` /
Task 2 acceptance) — it is not a defect in the new test file. `SWEEP_ACTIVE_EXPECTED_SKIPS` and
`FLAG_UNSET_EXPECTED_SKIPS` in `tests/test_phase25_venue.py` are a hand-attributed register (each
skip must be traced to a "named leg" per the module's own docstring, not just incremented) and
that file is outside plan 26-03's `files_modified` / FILES scope — 26-03 creates only
`tests/test_phase26_canary.py`. Bumping that register (with the correct named-leg attribution
added for the new control-sidecar skip) is left for the caller to route, most likely alongside
26-04 when the control sidecar's skip condition resolves, or as its own explicit fix commit.
Until then, `.venv/bin/python -m pytest -q` (repo-wide) reports these 2 known, predicted,
out-of-scope failures; every test this plan owns is green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The structural and live-path contracts are ready for Phase 26-04’s operational gate. The control sidecar and published canary artifact are intentionally absent. The D-44 skip-count register in `tests/test_phase25_venue.py` needs a +1 named-leg update (see the spec gap above) before the full repo suite is green again; that update is out of this plan's file scope and is left to the caller.

---
*Phase: 26-empirical-privacy-audit-canary*
*Completed: 2026-09-11*
