---
phase: 18-black-box-adversarial-extraction-audit
plan: 03
subsystem: testing
tags: [pre-registration, git-ancestry, holm, sign-test, clean-room, ast-scan, pytest]

# Dependency graph
requires:
  - phase: 16-weight-vs-prompt-persistence-control
    provides: "phase16_persistence.HOLM_ALPHA / SIGN_TEST_N / sign_test_exact (D-31's arithmetic), test_phase16_prereg.py's ancestry machinery and V3_ARTIFACT_GLOBS"
  - phase: 17-multi-persona-isolation-matrix
    provides: "the _GATE_MODULES glob register, the INVERTED lazy-import rule, the PHASE17_PREREG_ARTIFACT ancestry twin"
  - phase: 14-teach-then-recall
    provides: "embedded_fact_values / _module_strings / _strings_in (the static clean-room scan), LOCKED_FACTS + SOFT_TIER_FACTS"
provides:
  - "scripts/phase18_extraction.py — THE D-04 pin: K, the ASR ladder, the injection fraction, the family axis, the tier split, the VERDICTS triple and the all-fail prose, all committed before a number exists"
  - "assert_holm_family_reachable(family, alpha, best_achievable_p) — D-31's reachability proof, running at MODULE SCOPE so a mis-sized family dies at import rather than after 8.2h of GPU time"
  - "tests/test_phase18_prereg.py — the phase18_*.py glob, the static clean-room scan, the D-31 mutation proof, erasure_gate byte-identity, and the import-time callee allowlist"
  - "PHASE18_PREREG_ARTIFACT ancestry pin — every commit touching the driver must precede every results/phase18_* first-add"
affects: [18-04, 18-05, 18-06, 18-10, 19-selective-erasure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-registration as module literals in ONE ancestry-pinned file (D-04) — no unpinned sibling to move a rule into"
    - "Import-time arithmetic proof: a gate that cannot clear fails on `import`, not after the run"
    - "Hard-equality allowlist of module-scope AST callees as the inertness guard"

key-files:
  created:
    - scripts/phase18_extraction.py
    - tests/test_phase18_prereg.py
  modified:
    - tests/test_phase16_prereg.py

key-decisions:
  - "VERDICTS derives INCONCLUSIVE from erasure_gate.VERDICTS[-1] rather than retyping it — the D-27 mirroring becomes a fact about the code instead of a claim in a comment, and it is the load-bearing use of the required erasure_gate import"
  - "ASR_RUNGS reads its top rung from K rather than a second literal 64"
  - "The Phase 18 ancestry test's third vacuity closure is `bool(checked) == bool(tracked_artifacts)`, not Phase 17's bare `assert checked` — a bare assert would be RED today, since D-04's commit order guarantees zero results/phase18_* artifacts at the moment the pin lands"
  - "test_nothing_loads_at_import walks EVERY module-scope Call node, not just statement-level ones, so a checkpoint read hiding on the right-hand side of a module-level assignment is caught"
  - "test_erasure_gate_untouched compares ON-DISK bytes against 23a830c rather than HEAD-vs-23a830c — the bytes the interpreter imports are the ones that matter, and this additionally catches an uncommitted edit"

patterns-established:
  - "Import-time reachability proof (D-31): alpha/m > best-achievable-p asserted at module scope, both sides derived from the committed instrument"
  - "Calibrated vacuity closure: tie `checked` to whether anything was tracked, so a guard is green while there is nothing to check and red the moment there is"

requirements-completed: [STAT-04, STAT-05, STAT-06, ATK-01, ATK-05]

# Metrics
duration: 22min
completed: 2026-08-15
---

# Phase 18 Plan 03: Pre-Registration Pin and Its Three Guards Summary

**The D-04 pin exists, imports inertly, refuses a Holm family it could never clear, and is now git-ancestry-guarded — so every later edit to an attack template is visibly expensive.**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-08-15T23:47:00Z (approx, first task edit)
- **Completed:** 2026-08-16T00:09:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `scripts/phase18_extraction.py` (272 lines) holds every pre-registration literal that does not
  depend on the attack templates: `K = 64` against the recorded 112,608-draw cost model,
  `ASR_RUNGS = (1, 4, 16, K)` with the note that rung 1 IS the greedy deterministic decoder,
  `INJECTION_FRACTION = 0.25` with D-13's two-sided bracket recorded as a string constant,
  the four dose-split `ATTACK_FAMILIES`, `FAMILY_ZERO` at 9 draws, the gated/reported tier split,
  the `VERDICTS` triple and `CONTROL_FAILED_REASON` — the all-fail prose committed *before* the
  failure it describes can be seen.
- `assert_holm_family_reachable` runs at **module scope**, so importing the driver at all runs
  D-31's proof. `BEST_ACHIEVABLE_P` is **called** from `persistence.sign_test_exact` rather than
  retyped, and `HOLM_FAMILY` is `ATTACK_FAMILIES` rather than a hand-typed 4.
- `tests/test_phase18_prereg.py` (290 lines, 4 tests) — the `phase18_*.py` glob with its collapse
  guard, the static clean-room scan **watched RED**, the D-31 arithmetic proved at m=4 / m=6 / m=7,
  `erasure_gate` byte-identity, and the import-time callee allowlist.
- `PHASE18_PREREG_ARTIFACT` + its ancestry twin added to `tests/test_phase16_prereg.py`,
  **96 insertions / 0 deletions** — `V3_ARTIFACT_GLOBS`, `PREREG_ARTIFACT` and the Phase 17 test
  are byte-untouched.
- Full suite **650 passed / 7 skipped / 0 failed** (652 → 657 collected, +5 new tests),
  `ruff check .` and `ruff format --check .` both clean.

## Task Commits

1. **Task 1: Driver header, `_prove`, pre-registration literals, Holm reachability** — `13666c4` (feat)
2. **Task 2: `tests/test_phase18_prereg.py` — glob scan, reachability, erasure_gate identity** — `acc192b` (test)
3. **Task 3: `PHASE18_PREREG_ARTIFACT` ancestry pin** — `19813b0` (test)

## Files Created/Modified

- `scripts/phase18_extraction.py` — the D-04 pre-registration. Module docstring carries the
  one-file argument and the INVERTED lazy-import rule; `_prove` raises
  `SystemExit("[phase18_extraction] PROOF FAILED: ...")`; the `sys.path` bootstrap is the only
  permitted module-level side effect besides the D-31 proof. No `main()`, no parser, no run mode.
- `tests/test_phase18_prereg.py` — four tests, all CPU-only:
  `test_no_fact_values_in_phase18_modules`, `test_holm_family_is_reachable`,
  `test_erasure_gate_untouched`, `test_nothing_loads_at_import`.
- `tests/test_phase16_prereg.py` — `PHASE18_PREREG_ARTIFACT` beside `PHASE17_PREREG_ARTIFACT` and
  `test_phase18_prereg_is_frozen_before_every_phase18_result`.

## Decisions Made

- **`INCONCLUSIVE` is imported, not retyped.** `VERDICTS = ("LEAKAGE_DEMONSTRATED",
  "NULL_ADMISSIBLE", erasure_gate.VERDICTS[-1])`. D-27 says Phase 18's triple mirrors
  `erasure_gate`'s INCONCLUSIVE-precedence; deriving the shared member makes the mirroring
  structural, and it is the reason the plan's required `erasure_gate` import is load-bearing rather
  than an unused import ruff would reject.
- **The third vacuity closure is calibrated, not copied.** Phase 17's twin ends in a bare
  `assert checked`, which is correct *there* because `results/phase17_*` artifacts exist. Phase 18
  has none — D-04's forced order is smoke → pin → corpus → run → results, so an artifact existing
  right now would itself be the violation. A bare `assert checked` would therefore be red on the
  commit that adds it. The closure used is `bool(checked) == bool(tracked_artifacts)`: green while
  nothing is tracked, and demanding a non-zero `checked` from the first committed artifact onward.
  **Current value: `checked == 0`** (1 prereg commit × 0 tracked artifacts).
- **`test_nothing_loads_at_import` walks every `Call`, not only `ast.Expr`-wrapped ones.** The
  shipped Phase 17 idiom scans statement-level calls, which would miss a `torch.load` on the
  right-hand side of a module-level assignment — the shape that actually matters for a driver whose
  next plans add a checkpoint reader. The allowlist is hard equality over six callees, three of
  which (`assert_holm_family_reachable`, `persistence.sign_test_exact`, `sys.path.insert`) are the
  file's reason to exist and three of which are the bootstrap's own primitives.
- **m = 6 is asserted as well as m = 4 and m = 7.** D-31 rejected m=6 for a 0.00052 margin rather
  than for unreachability, so the test pins that the margin is still under 0.001 — the reason for
  choosing 4 stays a measured quantity rather than a preference.

## RED Proof (Task 2 acceptance criterion)

`scripts/phase18_extraction.py` was temporarily given a docstring line reading *"the taught town
value is brindlemoor, quoted here to explain the fact set"*, and
`test_no_fact_values_in_phase18_modules` failed with:

```
AssertionError: scripts/phase18_extraction.py embeds fact value(s) ['brindlemoor'] in a string
it holds (counts: [('brindlemoor', 1)]).
```

This is the exact leak shape D-03 describes — a value quoted inside a docstring *explaining* the
fact set, invisible to whole-string equality and caught by containment. The scaffold was removed
and `git diff --exit-code scripts/phase18_extraction.py` returned 0 before the commit.

## Deviations from Plan

None — plan executed exactly as written.

Two places where the plan left the shape to judgement and the choice is recorded above rather than
silently made: the ancestry test's third vacuity closure (a literal `assert checked` twin would
have been red at commit time, contradicting the plan's own acceptance criterion that the test
passes vacuously green today), and the breadth of the `test_nothing_loads_at_import` AST walk.
Neither adds or removes a rule; both implement what the plan asked in the only form that is green
today and non-vacuous tomorrow.

## Issues Encountered

- **Worktree base drift.** The worktree was created ~157 commits behind the expected base
  `c1e21d4`. HEAD was a strict ancestor, so it was corrected with a non-destructive
  `git merge --ff-only` rather than `reset --hard`; nothing was lost.
- **`0.0078125` must not appear outside comments** (Task 1 acceptance criterion). Handled by
  keeping the m=3..8 step-alpha table as a `#` comment block and interpolating
  `{best_achievable_p:.7f}` at runtime in the abort message — the number is derived everywhere it
  is used and typed nowhere the grep can see.

## User Setup Required

None — no external service configuration required.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary was
introduced; both created files are inert at import and read nothing from disk beyond their own
source.

## Next Phase Readiness

- **The pin is live.** From `13666c4` onward, any commit touching `scripts/phase18_extraction.py`
  must be an ancestor of every `results/phase18_*` first-add. Plans 18-04+ add the attack
  templates, the corpus builder, the NLL/exposure instruments and
  `null_result_is_admissible()` **into this same file** (D-28), and each such commit is legitimate
  precisely because no result artifact exists yet.
- **The D-12 pre-flight smoke must still run before any result lands**, and per D-28 it must run
  *after* the NLL/exposure instruments are in the file, not before.
- **Not built here, by design:** `null_result_is_admissible()`, `main()`, the argument parser, any
  run mode, and the attack templates themselves. `tests/test_phase18_prereg.py` will grow the
  remaining nodes 18-VALIDATION.md lists (`test_admissibility_precedence`,
  `test_family_zero_compares_the_vector`, `test_one_corpus_two_arms`,
  `test_instruments_are_inside_the_pin`, `test_smoke_covers_nll_path`,
  `test_smoke_scope_is_base_only`, `test_every_rate_declares_its_unit`) in their own plans.
- **Wave note:** 18-01's widenings (`holm(..., family=)` and `assert_no_value_in_prompt(...,
  prompt_ids=)`) were not needed by this plan and were not touched. Nothing here calls
  `persistence.holm`, so the m=4 family has no collision with Phase 16's hard-coded `m` yet — that
  lands with the first plan that actually runs the gate.

## Self-Check: PASSED

- `scripts/phase18_extraction.py` — FOUND (272 lines, ≥180 required, contains
  `def assert_holm_family_reachable`)
- `tests/test_phase18_prereg.py` — FOUND (290 lines, ≥120 required)
- `tests/test_phase16_prereg.py` — FOUND, contains `PHASE18_PREREG_ARTIFACT` (3 occurrences)
- `13666c4` — FOUND
- `acc192b` — FOUND
- `19813b0` — FOUND
- `.venv/bin/pytest -q` — 650 passed, 7 skipped, 0 failed
- `.venv/bin/ruff check .` / `ruff format --check .` — clean
- `ls results/phase18_* 2>/dev/null` — no matches, as the plan's verification requires

---
*Phase: 18-black-box-adversarial-extraction-audit*
*Completed: 2026-08-15*
