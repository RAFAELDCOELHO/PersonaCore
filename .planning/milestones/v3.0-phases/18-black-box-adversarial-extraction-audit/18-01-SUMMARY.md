---
phase: 18-black-box-adversarial-extraction-audit
plan: 01
subsystem: testing
tags: [holm, sign-test, statistics, clean-room-guard, pre-registration, tdd]

# Dependency graph
requires:
  - phase: 16-weight-vs-prompt-persistence-control
    provides: "`holm` / `sign_test_exact` / `HOLM_FAMILY_PAIRS` — the pinned inferential gate Phase 18 must reuse rather than copy"
  - phase: 14-persona-recall-demo
    provides: "`assert_no_value_in_prompt` and its twin `assert_value_in_prompt` — the clean-room prompt guards"
provides:
  - "`holm(p_values, *, family=HOLM_FAMILY_PAIRS)` — prices whatever family it is handed, so D-31's m=4 dose-split family reuses the pinned statistic instead of forking it"
  - "`assert_no_value_in_prompt(tok, question, values, *, prompt_ids=None)` — the corpus can now be checked against the realized prompt bytes, which is the only way A2's appended ids and A3's persona span are visible to the guard"
  - "`tests/test_phase18_widenings.py` — 10 tests pinning both widenings from the preserved side AND the widened side"
affects: [18-02, 18-03, 18-04, 18-05, 18-06, 18-07, 18-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import-never-copy, applied to a STATISTIC: the family size becomes a keyword-only parameter defaulted to the existing constant, so the pinned function stays single-sourced"
    - "Pre-widening output captured as a typed literal and asserted post-widening — 'bit-identical' becomes a measured equality rather than a re-derivation"

key-files:
  created:
    - tests/test_phase18_widenings.py
  modified:
    - scripts/phase16_persistence.py
    - scripts/phase14_recall.py

key-decisions:
  - "`family` and `prompt_ids` are both KEYWORD-ONLY — a positional widening would let one of the five committed call sites acquire a re-priced family or a fourth argument by accident; pinned by a TypeError test on each"
  - "`holm`'s `_prove` message now interpolates the family it was HANDED, so a mis-sized Phase 18 family is diagnosable from the abort instead of always reading 6"
  - "The six-pair expectation is a literal captured by running `holm` at c1e21d4 before the keyword existed — re-deriving it from `HOLM_ALPHA / (6 - i)` would make the test agree with any widening that broke the default and the expectation the same way"
  - "No requirement marked complete: STAT-04/STAT-06 were already `[x]` at Phase 16/17 and this plan sustains rather than discharges them; ATK-01 builds no attack family here (17-01's recorded over-claim-avoidance pattern, sixth application)"

patterns-established:
  - "Additive widening proved from both sides: the default path is asserted green in the SAME commit as the widened path, so 'additive' is a test rather than a claim"
  - "'Never rebuilds' proved by replacing `build_recall_prompt` with a landmine, not by reading the source — a structural claim verified by execution"

requirements-completed: []

# Metrics
duration: 20min
completed: 2026-08-15
---

# Phase 18 Plan 01: Shared-Instrument Widenings Summary

**`holm` now prices whatever family it is handed (D-31's m=4 dose-split clears by 60% instead of m=6's 0.00052) and `assert_no_value_in_prompt` can read realized prompt ids (D-03) — both additive, both defaulted to the exact prior behaviour, 9 deletions total and zero existing tests touched.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-08-15T23:33:00Z
- **Completed:** 2026-08-15T23:53:00Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 3 (2 sources widened, 1 test file created)

## Accomplishments

- **`holm` widened to a keyword-only `family=`** (`scripts/phase16_persistence.py:1170`). The single line `m = len(HOLM_FAMILY_PAIRS)` became `m = len(family)`; the sort, the `HOLM_ALPHA / (m - index)` step, the strict `<` and the step-down latch are byte-identical. Only `len(family)` is read, so the members can be Phase 16's *pairs* or Phase 18's family *names* with no branch on either — that is what lets one implementation serve both.
- **The abort now prices the passed family.** Previously `holm(six_p_values, family=<4-tuple>)` was impossible; now it raises naming **4**, so a mis-sized Phase 18 family is diagnosable from the message. The default still refuses 4 p-values naming **6**.
- **`assert_no_value_in_prompt` gained a keyword-only `prompt_ids=None`** (`scripts/phase14_recall.py:398`). Both detectors still run on `ids` and are still ANDed; `question` stays a required positional and is still interpolated into both abort messages, so an abort on a caller-built A2/A3 prompt names the source question rather than an anonymous id list.
- **10 tests committed**, each widening pinned from the preserved side *and* the widened side.

## Task Commits

Each task followed the RED → GREEN cycle; no REFACTOR gate was needed (both changes are one line of logic plus docstring).

1. **Task 1: Widen `holm` with an additive `family=` keyword**
   - `bd5a2df` (test) — RED: 3 of 5 failed on `TypeError: holm() got an unexpected keyword argument 'family'`
   - `1161593` (feat) — GREEN: 42 passed across `test_phase18_widenings.py` + `test_phase16_stats.py`
2. **Task 2: Add the `prompt_ids` path to `assert_no_value_in_prompt` (D-03)**
   - `11fecd6` (test) — RED: 3 of 5 failed on `TypeError: ... unexpected keyword argument 'prompt_ids'`
   - `3cf3286` (feat) — GREEN: 52 passed across `test_phase18_widenings.py` + `test_phase14_scoring.py`

**TDD gate compliance:** both tasks have a `test(...)` commit preceding a `feat(...)` commit. In each RED run the *preservation* half was already green — which is the point of an additive widening, and is asserted rather than assumed.

## Files Created/Modified

- `scripts/phase16_persistence.py` — `holm` signature + `m = len(family)` + the interpolated abort; docstring records D-31's m=4 family and that the strict `<` is equally inconsequential there (first step 0.0125 vs the achievable 0.0078125). **20 insertions / 7 deletions**, all 7 being the signature line, the `m =` line, the 2-line `_prove` message and 3 docstring lines that were rewritten in place. No assertion removed.
- `scripts/phase14_recall.py` — `assert_no_value_in_prompt` signature + `ids = build_recall_prompt(tok, question) if prompt_ids is None else prompt_ids`; docstring records D-03 and the AND-vs-OR polarity argument against the twin. **19 insertions / 2 deletions** — the signature and the reassigned `ids` line, nothing else.
- `tests/test_phase18_widenings.py` — new, 332 lines, 10 tests.

## Verification

| Check | Result |
|---|---|
| `pytest -q` (full suite) | **655 passed, 7 skipped** in 122s |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 156 files already formatted |
| `git diff --stat` vs base | exactly the 2 source files + 1 new test file |
| Existing tests modified | **0** |

Acceptance greps, all as specified by the plan:

| Criterion | Expected | Actual |
|---|---|---|
| `grep -c 'def holm(p_values, \*, family=HOLM_FAMILY_PAIRS)'` | 1 | 1 |
| `grep -c 'm = len(HOLM_FAMILY_PAIRS)'` | 0 | 0 |
| `grep -c 'm = len(family)'` | 1 | 1 |
| `grep -c 'prompt_ids=None'` (phase14_recall) | 1 | 1 |
| `grep -c '_is_contiguous_subsequence(ids, tok.encode(value))'` | 1 | 1 |

Downstream consumers re-run green unchanged: `test_phase16_stats.py`, `test_phase16_driver.py`, `test_phase17_stats.py`, `test_phase17_scoring.py`, `test_phase14_scoring.py`. The three committed `holm` call sites (`phase16_persistence.py:1237`, `phase17_isolation.py:1327`, and the tests' own) and all six `assert_no_value_in_prompt` call sites are untouched and take the default path.

## Threat register disposition

| Threat ID | Disposition | How it was discharged |
|---|---|---|
| T-18-01-01 (Tampering — `holm` widening changes Phase 16/17 arithmetic) | mitigated | `test_holm_default_family_is_bit_identical_to_the_pre_widening_function` asserts two LITERAL six-pair expectations captured from the function at `c1e21d4` before the keyword existed, including the step-down latch case. `tests/test_phase16_stats.py` re-run green. |
| T-18-01-02 (Info Disclosure — the prompt guard weakened while widened) | mitigated | `test_assert_no_value_in_prompt_sees_a_value_only_in_the_passed_ids` builds a real-tokenizer A3 persona span and asserts the *same question* passes on the default path but aborts on the widened one. `test_..._keeps_both_detectors_anded_on_the_widened_path` pins each detector from the direction where the *other* is blind, so deleting either goes RED. |
| T-18-01-03 (Repudiation — a Phase-18-local `holm` copy) | **deferred to 18-03 as planned** | This plan makes the copy unnecessary by widening in place. The static scan forbidding a second `def holm` under `scripts/phase18_*.py` is 18-03's, and no `scripts/phase18_*.py` exists yet. |
| T-18-01-SC (Tampering — package installs) | accepted | Nothing installed. `pyproject.toml` untouched; its sha256 pin in `tests/test_package.py` is green. |

## Decisions Made

- **Both new parameters are keyword-only.** The plan specified `*` for `family`; the same treatment was applied to `prompt_ids` for the identical reason, and each is pinned by its own `TypeError` test. A positional fourth argument on `assert_no_value_in_prompt` would be silently accepted by any of its six call sites.
- **The `_prove` message interpolates the handed family.** Required by the plan's action text; it also converts an otherwise confusing abort ("closed at 6" while a 4-family was passed) into a diagnosable one.
- **A ternary rather than an `if`/`else` for the `ids` binding.** The plan asked that `ids = build_recall_prompt(tok, question)` be kept "verbatim". The `build_recall_prompt(tok, question)` *expression* is verbatim, character for character; wrapping it in a one-line conditional keeps the deletion count at 2 and avoids re-indenting the line, which an `if`/`else` would also have modified. Behaviour on the default path is identical either way.
- **No requirement checked off.** STAT-04 and STAT-06 were already `[x]` (traceability rows read `16, 17, 18 | Complete`) — this plan sustains them. ATK-01 constructs no attack family and stays Pending for the plans that build one. `REQUIREMENTS.md` is therefore byte-unchanged.

## Deviations from Plan

None — plan executed exactly as written.

One item worth recording as an *environment* correction rather than a plan deviation: the worktree spawned at `829cd5f`, **157 commits behind** the required base `c1e21d4`, so `.planning/phases/18-.../` did not exist. The working tree was clean and `c1e21d4` was a strict descendant, so the base was corrected by `git merge --ff-only` — a pure fast-forward, 0 commits lost. No plan content was affected.

## Issues Encountered

- **Full-suite count is 655 passed / 7 skipped, where the plan predicted "652 tests today".** 662 collected minus this plan's 10 new tests = 652 pre-existing collected, so the plan's figure was the collected count and the discrepancy is bookkeeping, not a lost test. Recorded rather than silently reconciled.
- Two `E501` line-length violations in test docstrings, caught by `ruff` before the RED commits and reworded. No logic involved.

## Known Stubs

None. Both widenings are fully wired; no placeholder values, no unreached branches.

## Next Phase Readiness

Both instruments are ready for Phase 18 driver code:

- **18-03** (the pre-registration pin) can now write `holm(p_values, family=PHASE18_HOLM_FAMILY)` and assert D-31's reachability inequality at import — `sign_test_exact((1,)*n_facts) < HOLM_ALPHA / m`, which is `0.0078125 < 0.0125` at m=4 — against the imported function rather than a local copy. It still owns the static scan forbidding a second `def holm` under `scripts/phase18_*.py` (T-18-01-03).
- **The A2/A3 driver plans** can call `assert_no_value_in_prompt(tok, question, values, prompt_ids=realized_ids)`. Note D-16's partition: the strict no-value guard is still expected to run on the `build_recall_prompt` output for *every* family including A2 (proving the question-derived portion is value-free everywhere), with A2's appended tail getting its own bounded `≥ 1 and ≤ ⌊ids/4⌋` assertion. The widening enables that second check; it does not perform it.
- Neither `scripts/phase16_persistence.py` nor `scripts/phase14_recall.py` is under a STAT-05 ancestry pin (only `scripts/erasure_gate.py` and `scripts/phase17_personas.py` are), so these edits do not disturb any pre-registration ordering guard. Verified against `tests/test_phase16_prereg.py`.

## Self-Check: PASSED

- All 4 claimed files present on disk (2 modified sources, 1 new test file, this SUMMARY).
- All 5 claimed commits present in `git log`: `bd5a2df`, `1161593`, `11fecd6`, `3cf3286`, `bcad2c1`.
- `git status --short` clean — nothing uncommitted.
- `git diff --name-only c1e21d4..HEAD` lists exactly 4 paths; **no `STATE.md`, no `ROADMAP.md`, no `REQUIREMENTS.md`** (orchestrator owns the first two; the third is genuinely unchanged).

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-15*
