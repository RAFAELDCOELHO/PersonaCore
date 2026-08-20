---
phase: 20-pre-registration-the-three-condition-gate
plan: 01
subsystem: testing
tags: [pre-registration, git-ancestry, decision-gate, stdlib, ruff, pytest]

# Dependency graph
requires:
  - phase: 19-selective-erasure
    provides: "scripts/erasure_gate.py (23a830c, closed) — MARGIN_K, V20_MASKED_DIALOGUE_VAL_PPL, VERDICTS; results/phase19_noise_floors.json's dialogue_ppl_noise_floor; results/phase19_erasure_report.md:446-450's (c) non-discrimination finding"
  - phase: 16-recall-persistence
    provides: "tests/test_phase16_prereg.py:406-497 — the Phase 18/19 ancestry-guard shape and its recorded-vacuity docstring"
provides:
  - "scripts/mitigation_gate.py — the v4.0 three-condition pre-registration pin, spine only (no verdict logic yet)"
  - "V4_VERDICTS / _VERDICT_RELABEL / _prove_verdict_domain — PASS/FAIL/INCONCLUSIVE proved a relabelling of erasure_gate.VERDICTS at import"
  - "ARMS / ARM_CLAIMS — closed arm set proved equal to its claim table at module scope"
  - "F_Y = 0.7, F_C = 0.5, CHOSEN_CONSTANTS — the only two chosen constants, labelled PREFERENCE"
  - "superseded_dialogue_cap(*, gap_noise_floor) — GATE-02's superseded cap as a COMPUTATION over two imported terms"
  - "K_RUNGS = (48, 24, 16, 8) — the CAL-04 closed ordered menu with the D-19 ratchet recorded"
  - "MITIGATION_DECISION_RULE / MITIGATION_GOAL_FRAMING — the pin's prose as importable module data"
  - "tests/test_phase20_prereg.py — the live ancestry guard plus _assert_ordering_holds, the shared implementation plan 20-03's D-22 fixture will call"
affects: [20-02, 20-03, 20-04, 20-05, 20-06, 20-07, phase-21, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import accumulation: an erasure_gate name enters the from-import list in the task that FIRST CONSUMES it (ruff select=F makes an early import an F401)"
    - "Proved relabelling instead of a retyped domain (D-31): module-scope _prove over three separate claims"
    - "Shared ordering helper parameterized on root, so the live guard and a throwaway-repo fixture run ONE implementation"

key-files:
  created:
    - scripts/mitigation_gate.py
    - tests/test_phase20_prereg.py
  modified: []

key-decisions:
  - "The superseded GATE-02 dialogue cap is named by its COMPUTATION, never by its value — superseded_dialogue_cap(gap_noise_floor=<the committed dialogue_ppl_noise_floor>) reproduces it exactly from two imported terms, and the literal appears nowhere in the pin"
  - "V4_VERDICTS is declared, not imported, and the relationship to erasure_gate.VERDICTS is PROVED at import via _VERDICT_RELABEL (equal length, positional correspondence, INCONCLUSIVE at the same index) — the one tuple an import-never-retype phase cannot import"
  - "The ancestry guard is armed in the phase's FIRST plan, deliberately vacuous at tracked=0, and its vacuity is recorded in the test's own docstring rather than hidden"
  - "Phase 18/19 shape only (git ls-files + derived pre-registration side + bool(checked) == bool(tracked_artifacts)); Phase 16's unconditional `assert checked` over a working-tree glob is absent by design (D-21)"
  - "V4_ARTIFACT_GLOBS carries results/phase20_* ONLY (D-33), with the accepted cost — an assert catches an empty match set, never an incomplete one — recorded beside the tuple and in MITIGATION_DECISION_RULE"

patterns-established:
  - "Deliberate-RED then byte-identical restore, with both sha256 values recorded: applied twice in this plan"
  - "Chosen constants carry a PREFERENCE label where erasure_gate's baselines carry an artifact path, and are re-exported as data so an audit needs no second hand-maintained list"

requirements-completed: []

# Metrics
duration: 22min
completed: 2026-08-20
---

# Phase 20 Plan 01: Arm the Pin and Arm the Guard Summary

**The v4.0 three-condition pre-registration exists as a committed spine with its verdict domain and arm set proved at import, and the git-ancestry guard watching it was armed in the same plan — vacuous by construction at tracked=0 and recorded as such.**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-08-20T19:23Z (16:23 -0300)
- **Completed:** 2026-08-20T19:45Z (16:45 -0300)
- **Tasks:** 3 of 3
- **Files created:** 2 (301 + 163 lines)

## Accomplishments

- `scripts/mitigation_gate.py` (301 lines) is committed as the v4.0 pin's spine. It imports cleanly, and two independent module-scope proofs run at import: `_prove_verdict_domain()` (D-31) and the `tuple(ARM_CLAIMS) == ARMS` proof (D-28). Both raise `SystemExit`, never `assert` — an `assert` is strippable under `-O`.
- The one number this phase supersedes is a **computation, not a literal**. `superseded_dialogue_cap(gap_noise_floor=0.005214448168350039)` returns exactly `4.5837288963367` from `V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * gap_noise_floor`, both terms imported by object identity, and the literal `4.5837288963367` appears nowhere in the file. Verified by AST scan that the module's only float literals are `[0.5, 0.7]`.
- `tests/test_phase20_prereg.py` (163 lines) arms the live ancestry guard **before any pin logic exists**, so every pin commit from 20-01 onward is watched from the start. It is GREEN today at `tracked_artifacts == 0` and demands a non-zero `checked` from the first artifact onward.
- Both guards were **watched RED and restored byte-identically**, with both sha256 values recorded below.
- Full suite: **846 passed, 1 skipped** in 192.13s (pre-phase baseline was 845 passed, 1 skipped in 201.99s — the delta is this plan's one new test).

## Task Commits

Each task was committed atomically, in the order the plan prescribes — pin first, guard second:

1. **Task 1: The pin's import surface, loud-refusal helper, verdict domain and arm identity** — `95b3c8a` (feat)
2. **Task 2: The two chosen constants, the superseded-cap computation, the K rung menu, and the decision-rule prose record** — `647c6c8` (feat)
3. **Task 3: Arm the ancestry guard — Phase 18/19 shape, vacuous by construction** — `bf2ad87` (test)

**Plan metadata:** see the `docs(20-01)` commit that carries this SUMMARY.

## Files Created

- `scripts/mitigation_gate.py` — the v4.0 pre-registration pin. Spine only: `_REPO_ROOT`, `_prove`, `V4_VERDICTS`, `_VERDICT_RELABEL`, `_prove_verdict_domain`, `ARMS`, `ARM_CLAIMS`, `F_Y`, `F_C`, `CHOSEN_CONSTANTS`, `superseded_dialogue_cap`, `K_RUNGS`, `MITIGATION_DECISION_RULE`, `MITIGATION_GOAL_FRAMING`. **No verdict logic** — plans 20-02 and 20-04 append it.
- `tests/test_phase20_prereg.py` — `_ROOT`, `_git` (with the additive keyword-only `cwd`), `PHASE20_PREREG_ARTIFACT`, `V4_ARTIFACT_GLOBS`, `_assert_ordering_holds`, `test_phase20_prereg_is_frozen_before_every_phase20_result`.

## Recorded Artifact State (plan `<output>` requirements)

**sha256 of `scripts/mitigation_gate.py` at commit `bf2ad87`:**
`de02d7b9aa8d80dc9fc2a2480ec9db571e6e99ed5ef0da8754167e4a2c40c324`
(verified identical between `git show HEAD:scripts/mitigation_gate.py` and the working tree)

**sha256 of `tests/test_phase20_prereg.py` at commit `bf2ad87`:**
`7a683e765e16ee57eb61fe329f8acbf9d9246b2aa402b1a23d27517a343c79bb`

### Watched-RED observation 1 — the verdict relabel proof (Task 1)

| | value |
|---|---|
| mutation | `_VERDICT_RELABEL["FAILURE"]` changed from `"FAIL"` to `"FAILURE"` |
| clean sha256 | `6a351b9b25d3f996d4756d3d6aa7404b7888f8bc63535ca23e3e0c7f23aa5988` |
| mutated sha256 | `fedf43178b16e29a7e5e0c4d8a1271cde8ebe42ce5c6466e3d90368f02655e21` |
| observed | import exited **1** with `[mitigation_gate] position 1: erasure_gate.VERDICTS[1] is 'FAILURE', which _VERDICT_RELABEL sends to 'FAILURE', but V4_VERDICTS[1] is 'FAIL'. …` |
| restored sha256 | `6a351b9b25d3f996d4756d3d6aa7404b7888f8bc63535ca23e3e0c7f23aa5988` — **byte-identical to clean** |

(The clean sha256 above is the Task-1 state; the file's final sha256 after Task 2's append is `de02d7b9…c324`.)

### Watched-RED observation 2 — the `assert prereg_commits` branch (Task 3)

| | value |
|---|---|
| mutation | `PHASE20_PREREG_ARTIFACT` repointed at `scripts/no_such_pin_never_committed.py` |
| clean sha256 | `7a683e765e16ee57eb61fe329f8acbf9d9246b2aa402b1a23d27517a343c79bb` |
| mutated sha256 | `26f00f3bea33597c82ab69f59a6e8f03c22e482a98e3f1056d8abfa4402da97d` |
| observed | pytest exited **1** on `assert prereg_commits` — `"… has no commits — this guard would be scanning a pre-registration that does not exist, which is green and blind in the worst possible place."` |
| restored sha256 | `7a683e765e16ee57eb61fe329f8acbf9d9246b2aa402b1a23d27517a343c79bb` — **byte-identical to clean** |

### D-22 clean-history precondition, re-confirmed after this plan

```
$ git ls-files 'results/phase20_*'          -> (empty)
$ git log --diff-filter=A -- 'results/phase20_*'  -> (empty)
```

Both empty. No v4.0-named artifact has ever been added to this repository's history, so plan 20-03's RED-then-GREEN fixture still has a clean slate and D-08's strictly-after discipline is intact.

## Verification (wave boundary)

| check | result |
|---|---|
| `.venv/bin/python -m pytest -q` | **846 passed, 1 skipped** in 192.13s (baseline 845/1) |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 172 files already formatted |
| `git status --porcelain pyproject.toml` | empty — byte-unchanged, RPT-03's sha256 pin carries forward |
| `git log --diff-filter=A -- 'results/phase20_*'` | empty |
| AST: `from erasure_gate import …` names | exactly `['MARGIN_K', 'V20_MASKED_DIALOGUE_VAL_PPL']` |
| AST: `import …` names in the pin | exactly `['erasure_gate', 'pathlib', 'sys']` |
| AST: module float literals in the pin | exactly `[0.5, 0.7]` |
| AST: imports in the test module | exactly `['pathlib', 'subprocess']` |
| `hasattr(mitigation_gate, "VERDICTS")` | `False` |
| `mitigation_gate.MARGIN_K is erasure_gate.MARGIN_K` | `True` (object identity) |
| `mitigation_gate.V20_MASKED_DIALOGUE_VAL_PPL is erasure_gate.…` | `True` (object identity) |
| `superseded_dialogue_cap(gap_noise_floor=-0.1)` | raises `ValueError` |
| `_ROOT.glob` in the test source | absent (Phase 16 working-tree shape not copied) |
| bare `assert checked,` in the test source | absent (D-21) |

## Decisions Made

None beyond the plan — every decision executed here was already locked in `20-CONTEXT.md` (D-01, D-05, D-08, D-10, D-15…D-19, D-21, D-28, D-31, D-33). Two implementation choices worth recording because a later plan must spell them identically:

1. **`_prove_verdict_domain()`'s third proof avoids `.index()` on a possibly-absent name.** `tuple.index` raises `ValueError`, not this module's `SystemExit`, so the `INCONCLUSIVE` check is written as `shared in erasure_gate.VERDICTS and shared in V4_VERDICTS and <indices equal>`. A bare `.index()` pair would abort with the wrong exception type and send its reader to the wrong file — the exact defect `_prove`'s bracketed prefix exists to prevent.
2. **`f_C`'s measured non-vacuity floor `0.22362988653603388` lives in the D-15/D-18 clause** of `MITIGATION_DECISION_RULE`, not only in the `F_C` provenance comment. The plan's acceptance criterion requires that literal in the rule/framing concatenation; putting it in the clause that already argues "exactly two chosen constants, and here is why each is defensible" is where it does the most work for a reviewer.

## Deviations from Plan

None — plan executed exactly as written. No deviation rule fired.

**Total deviations:** 0
**Impact on plan:** none.

## Issues Encountered

**One E501 during Task 2, fixed inline before commit.** A `MITIGATION_DECISION_RULE` clause line reached 101 characters against the `pyproject.toml` limit of 100. Rebalanced the string continuation across two lines with no change to the rendered clause text; `ruff check .` then exited 0. Caught by the task's own gate, never committed red.

**No path/naming discrepancies found.** Every path this plan touched was resolved from the module's own constants and verified against the source this session: `results/phase19_noise_floors.json`'s `dialogue_ppl_noise_floor` is a nested block whose `value` is `0.005214448168350039` (the plan's figure, confirmed by reading the JSON, not by trusting prose), and `erasure_gate.py` is 291 lines with `VERDICTS` at `:136` exactly as `20-PATTERNS.md` corrected. Nothing needed renaming to match plan prose.

## Known Stubs

**`scripts/mitigation_gate.py` has no verdict function yet, and that is the plan's design, not a stub.** The plan is explicit — "spine only — no verdict logic yet" — and the phase's value is ordering: the pin's FIRST commit has to exist before anything else in Phase 20 does. `mitigation_point_verdict` / `exists_clearing_point` / the X and Y computations / the GATE-10 branch / the `__main__` self-check all arrive in plans 20-02 and 20-04, each appending to this same file while the guard armed here watches every one of those commits.

**The ancestry guard is vacuous today (`checked == 0`), by construction.** This is recorded in the test's own docstring rather than hidden, and the closing `bool(checked) == bool(tracked_artifacts)` assertion is what stops the vacuity surviving the first artifact's arrival. Nothing here needs "fixing" — a non-vacuous guard at this moment would mean a v4.0 artifact had been committed before the pin, which is the violation the phase exists to prevent.

## Threat Flags

None. This plan adds no network surface, no auth path, no file I/O and no schema. `_git` passes an argv tuple and never uses `shell=True`, so a glob containing a shell metacharacter reaches git as a pathspec (T-20-05, disposition `accept`, verified in the implementation). `scripts/erasure_gate.py` was not written to by any task (T-20-02); `tests/test_phase18_prereg.py:212`'s byte-identity assertion is in the 846-passing suite.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Wave 1 is complete and every downstream plan's precondition holds:

- **20-02** appends `wilson_upper_bound` to the from-import list with its first consumer (X's Wilson term). The list is currently exactly `MARGIN_K, V20_MASKED_DIALOGUE_VAL_PPL` — adding a name ahead of its consumer is an F401 and `ruff check .` gates every task.
- **20-03** owns the `sys.path` bootstrap plus `ast` / `sys` / `pytest` imports in the test module and the D-22 throwaway-repo fixture. `_assert_ordering_holds` is already parameterized on `root` and keyword-only, so the fixture calls the same implementation CI runs. Note the measured gotcha from `20-PATTERNS.md`: `git rm` of the last file in `results/` removes the directory, so a re-add needs `mkdir -p` or a seeded `results/.keep`.
- **20-04** adds `V20_EWC_RETENTION_PPL` and `rule_of_three`, completing the five-name final import list.
- **20-06** adds `fnmatch` / `erasure_gate` / `mitigation_gate` / `json` to the test module and is the **ONLY** file permitted to carry the literals `0.005214448168350039` and `4.5837288963367` — it proves `superseded_dialogue_cap` reproduces the v3.0 cap. Neither literal is in `scripts/mitigation_gate.py`; verified.
- **No requirement was marked complete.** GATE-01, GATE-02, GATE-07 and CAL-04 are each claimed by more than one plan in this phase — GATE-01's verdict function does not exist yet, GATE-02's (c) computation is not written, GATE-07's per-arm ∃ is 20-02's, CAL-04's promotion rule is still to come. This is the recorded over-claim-avoidance pattern (`17-01`, applied six times across Phases 17 and 19), applied a seventh time.

**Standing constraint for every remaining Phase 20 plan:** `scripts/mitigation_gate.py` is watched from `95b3c8a` onward. Do not amend, rebase, squash or cherry-pick any commit touching it, and do not commit a `results/phase20_*` artifact before the pin is complete.

## Self-Check: PASSED

- `scripts/mitigation_gate.py` — FOUND
- `tests/test_phase20_prereg.py` — FOUND
- commit `95b3c8a` — FOUND
- commit `647c6c8` — FOUND
- commit `bf2ad87` — FOUND

---
*Phase: 20-pre-registration-the-three-condition-gate*
*Completed: 2026-08-20*
