---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 01
subsystem: testing
tags: [differential-privacy, ast-guards, pytest, reference-data, dp-sgd, accountant]

# Dependency graph
requires:
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "scripts/mitigation_unit.py::DELTA — the frozen delta the REJECTED_FORM crossover is measured at"
  - phase: 20-pre-registration-the-three-condition-gate
    provides: "tests/test_phase20_prereg.py's sys.path idiom, collapsed-glob meta-guard, and the same-code-in-both-places rule at :153-155"
provides:
  - "src/personacore/privacy/ — the importable v4.0 privacy subpackage, docstring-only, no re-exports"
  - "tests/fixtures/phase22_reference.py — 60-dps ground truth as import-free literal data (12 delta rows, 7 epsilon rows, 4 boundary constants, crossover, quadrature params, tolerances)"
  - "tests/test_phase22_dpsgd_ast.py — the TEXT-taking D-05 axis-1 closure guard, the pinned single-clip-constant rule, and 10 committed self-tests"
affects: [22-02 accountant, 22-04 dpsgd mechanism, 22-09 fake probes, 23 mitigation sweep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AST guards that take SOURCE TEXT rather than a committed path, so the live check and the mutation probe run identical code"
    - "60-dps ground truth committed as literal data instead of recomputed, keeping mpmath out of the dependency set"
    - "Reference truths stored as decimal STRINGS where float64 cannot hold them"

key-files:
  created:
    - src/personacore/privacy/__init__.py
    - tests/fixtures/phase22_reference.py
    - tests/test_phase22_reference.py
    - tests/test_phase22_dpsgd_ast.py
  modified: []

key-decisions:
  - "DELTA_FRONTIER truths are decimal STRINGS, not float literals: row (2.0, 0.05)'s 1.24028351258e-352 is below the float64 subnormal floor and a float literal would silently parse to 0.0, destroying the row before any test read it"
  - "src/personacore/privacy/__init__.py ships ZERO re-exports (departing from continual/__init__.py's form) so accountant.py and dpsgd.py, landing in two independently-owned plans, never share a write target"
  - "_ALLOWED_CLASS_CONSTANTS starts EMPTY — a future plan adds its name in the same commit as the constant, never ahead of it"
  - "The clip-constant scope locator is deliberately narrow (a self.<attr> on the LEFT of an ast.Div) because the broader Compare-or-Div form also matches a finalize-style method and would redden plan 22-04 Task 3's hard equality on correct code"

patterns-established:
  - "Text-taking AST guard: _assert_*(source_text, *, entry) with both meta-guards inside the helper, so no consumer can forget one"
  - "Meta-guard applied to DATA: a reference table asserts its own row count, its underflow set by hard equality, and its zero import surface"
  - "One template, one-line mutations: every RED probe differs from the GREEN baseline by exactly one line, so a failure is attributable to the mutation and not to two different fixtures"

# The plan's `requirements: [DPSGD-03, DPSGD-04]` names what this plan CONTRIBUTES TO, not what
# it completes. DPSGD-03 needs the accountant agreeing with two oracles (plans 22-03/22-05);
# DPSGD-04 needs four fakes with their positive controls watched failing (plan 22-09). Neither is
# satisfied by scaffolding, so `requirements.mark-complete` was deliberately NOT called and this
# list is empty rather than optimistic.
requirements-completed: []
requirements-contributed: [DPSGD-03, DPSGD-04]

# Metrics
duration: 25min
completed: 2026-08-25
---

# Phase 22 Plan 01: Wave-0 Scaffolding Summary

**The privacy subpackage, the 60-dps reference table as import-free literal data (so `mpmath` never becomes a test dependency), and the text-taking D-05 axis-1 closure guard proven to bite on six distinct mutations and both of its own meta-guards.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-25T17:30:00Z (approx, first read after `3cf6964`)
- **Completed:** 2026-08-25T17:55:00Z
- **Tasks:** 2
- **Files created:** 4 (0 modified)

## Accomplishments

- `personacore.privacy` imports — the first v4.0 content inside `src/` (D-10), docstring-only, no re-exports, with the reason for the no-re-export departure recorded in the docstring itself.
- The 60-dps ground truth from `22-RESEARCH.md` is committed as **literal data with zero imports**: 12 δ-frontier rows, 7 ε-golden rows, 4 zero-boundary constants, the `REJECTED_FORM` crossover, the two quadrature parameters, and three tolerances — each carrying its provenance and, where relevant, the measurement it clears.
- V-24's RPT-03 half is live from Wave 0: an AST walk over `tests/test_phase22_*.py` + the fixture asserts `mpmath` is never imported, behind a collapsed-glob meta-guard.
- V-11's core exists as three **text-taking** helpers with both meta-guards inside the closure function, hard-equality offender assertion (`assert offenders == {}`), and the `attr` callee arm without which a method-based mechanism closes after one hop.
- Ten self-tests observe the guards firing in-process: 4 forbidden tokens, a `.grad` Store, an attribute callee hiding `backward`, a second clip constant, the assigned-but-unread negative control, and both meta-guards.

## Task Commits

1. **Task 1: Privacy subpackage init + the committed 60-dps reference table** — `2c1bc35` (feat)
2. **Task 2: The text-taking forbidden-token closure guard + synthetic RED self-tests** — `3c27c9c` (test)

## Files Created/Modified

- `src/personacore/privacy/__init__.py` — docstring-only package marker; names D-10, what 22-02 and 22-04 ship, and why there are no re-exports.
- `tests/fixtures/phase22_reference.py` — the 60-dps ground truth. Zero imports, zero executable logic.
- `tests/test_phase22_reference.py` — 3 meta-guarded assertions: the table is populated (with the composition identity asserted as data), the fixture's AST import set is empty, and no Phase-22 test reaches `mpmath` (plus the crossover δ resolved from `mitigation_unit.DELTA` rather than re-spelled).
- `tests/test_phase22_dpsgd_ast.py` — `_forbidden_calls_reachable_from`, `_assert_no_forbidden_between_noise_and_step`, `_assert_single_clip_constant`, and 10 self-tests.

## Decisions Made

- **`_ALLOWED_CLASS_CONSTANTS = frozenset()`.** The plan required an explicit frozenset but named no members. Starting empty makes any class-body numeric constant redden; a future plan adds its name in the same commit as the constant, which is `tests/test_phase14_scoring.py:539-543`'s allowlist discipline. Pre-adding a member would be an exemption granted to code that does not exist.
- **The composition identity is asserted, not just commented.** `EPSILON_GOLDEN`'s three `μ_eff = 1.0` rows are located by `steps ** 0.5 == sigma` (an operator, no import) and asserted to carry one bit-identical ε. This turns a table property from prose into a check, for free.
- **`requirements.mark-complete` was NOT called.** The plan's `requirements: [DPSGD-03, DPSGD-04]` names what this plan contributes to. DPSGD-03 requires an accountant agreeing with two oracles of different mathematics (plans 22-03 / 22-05); DPSGD-04 requires four fakes each with its positive control **watched failing first** (plan 22-09). Scaffolding satisfies neither, and checking either box after plan 1 of 11 would publish a completion nothing has evidenced. Both remain `- [ ]` in `REQUIREMENTS.md`.
- **`gsd-sdk` state/roadmap mutation verbs were called and then hand-repaired** — three corruptions this session, all cosmetic-but-wrong and all fixed before commit (below).
- **The δ cross-check locates its scope structurally.** `test_no_phase22_test_imports_mpmath` walks upward from the `REJECTED_FORM_CROSSOVER` assignment collecting the contiguous comment run, asserts that run is non-empty, then asserts `repr(mitigation_unit.DELTA)` appears in it. The test never spells `1e-5`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `DELTA_FRONTIER`'s last row cannot be a float literal, so its truths are decimal strings**

- **Found during:** Task 1
- **Issue:** The plan specifies `DELTA_FRONTIER` rows as `(eps, mu, truth_60dps)` triples with the last row's truth `1.24028351258e-352`, **and** an acceptance assertion that "every row is a 3-tuple of floats/ints, and every `truth` is strictly positive". These are mutually unsatisfiable: `1.24028351258e-352` is below float64's subnormal floor (~4.94e-324), so Python parses the literal to `0.0` **silently**. A float column would have delivered the row already destroyed, and the "strictly positive" meta-guard would then have been asserting over data the parser threw away — the exact class of vacuity the meta-guard exists to prevent.
- **Fix:** `truth` is a **decimal string** in all 12 rows; consumers call `float()` and get exactly what f64 can hold (which for that row IS `0.0`, and that is F1's point). The meta-guard is correspondingly strengthened rather than dropped: `float(truth) >= 0.0` for every row, plus **hard equality** that the set of rows underflowing to `0.0` is exactly `[VACUOUS_AGREEMENT_ROW]` = `(2.0, 0.05)`. A silently-zeroed second row now reddens instead of passing as "well, one of them was always zero". A new fixture constant `VACUOUS_AGREEMENT_ROW` names that row as data so the test does not re-spell it.
- **Files modified:** `tests/fixtures/phase22_reference.py`, `tests/test_phase22_reference.py`
- **Verification:** `.venv/bin/python -m pytest tests/test_phase22_reference.py -x -q` → 3 passed; `.venv/bin/python -c "print(repr(1.24028351258e-352))"` → `0.0`, confirming the underflow before the change was made.
- **Committed in:** `2c1bc35` (Task 1 commit)

**2. [Rule 1 - Bug] `EPSILON_GOLDEN`'s "last three rows all have `μ_eff = 1.0`" is a mis-transcription**

- **Found during:** Task 1
- **Issue:** The plan (following `22-RESEARCH.md`'s own loose prose) says a comment must record that "the last three rows all have `mu_eff = 1.0` and identical ε". Measured against the row order the plan itself specifies, the last three rows are `(2.0, 200)`, `(1.0, 1)` and `(8.0, 64)` — and `(2.0, 200)` has `μ_eff = √200/2 = 7.071` with ε = 54.377, not 1.0. The three `μ_eff = 1.0` rows are rows **2, 6 and 7**: `(14.142135623730951, 200)`, `(1.0, 1)`, `(8.0, 64)`. `22-RESEARCH.md` names those three correctly one sentence later; only the positional phrase is wrong.
- **Fix:** The comment records the three rows **by their values**, notes the transcription correction explicitly, and the test asserts the property structurally (`steps ** 0.5 == sigma` selects exactly 3 rows, which carry exactly 1 distinct ε) rather than by position — so the claim cannot rot if the table is ever reordered.
- **Files modified:** `tests/fixtures/phase22_reference.py`, `tests/test_phase22_reference.py`
- **Verification:** `test_reference_table_is_populated` asserts `len(unit_mu_eff) == 3` and `len({eps}) == 1`; both pass.
- **Committed in:** `2c1bc35` (Task 1 commit)

**3. [Rule 3 - Blocking] `make test` / `make lint` do not resolve the venv**

- **Found during:** Post-plan verification
- **Issue:** `Makefile:12-16` runs bare `pytest` / `ruff`. With the venv not activated, `pytest` resolves to a pyenv **3.12.13** interpreter with no torch installed, producing **83 collection errors** (`ModuleNotFoundError: No module named 'torch'`). This is an environment resolution artifact, **not** a code regression and **not** the known broken-editable-install pattern — the editable install is intact.
- **Fix:** Ran the contract commands through the venv explicitly: `.venv/bin/python -m pytest -q` and `.venv/bin/ruff check . && .venv/bin/ruff format --check .`. The Makefile was left **unmodified** — changing it is out of this plan's scope and would touch a file no task names.
- **Files modified:** none
- **Verification:** `.venv/bin/python -m pytest -q` → **1037 passed, 1 skipped** in 202s; `.venv/bin/ruff check .` → all checks passed; `ruff format --check .` → 195 files already formatted.
- **Committed in:** n/a (no code change)

**4. [Rule 1 - Bug] Three `gsd-sdk` mutation-handler corruptions, hand-repaired before commit**

- **Found during:** State updates
- **Issue:** Eleventh consecutive session in which these handlers damage planning frontmatter. Measured this time: (a) `state.advance-plan` rewrote `Status: Executing Phase 22` back to `Status: Ready to execute`, silently reverting the orchestrator's own uncommitted edit; (b) `state.record-metric` wrote the duration cell as `25` where all 30 sibling rows read `25min`; (c) `state.add-decision` prefixed all three entries `- [Phase ?]:` instead of `- [Phase 22]:`; (d) `roadmap.update-plan-progress` wrote the status cell as `In Progress|  |` — no space before the pipe and an empty date cell where siblings carry `-`. Separately, `state.update-progress` returned `{"updated": false, "reason": "Progress field not found in STATE.md"}` and did nothing; the `progress:` frontmatter block was already correct after `advance-plan`, so nothing was lost.
- **Fix:** All four hand-repaired in place before the metadata commit, each verified by `git diff`.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** `grep -c "Phase ?" .planning/STATE.md` → 0; the metrics row and the roadmap row now match their siblings' format byte for byte.
- **Committed in:** the plan metadata commit

---

**Total deviations:** 4 auto-fixed (2 bugs in the plan's own data spec, 1 blocking environment issue, 1 tooling corruption)
**Impact on plan:** Both data corrections make the reference table *carry more information and assert more* than the plan specified — neither weakens a guard, and both were forced by measurement rather than preference. No scope creep: `pyproject.toml`, `scripts/mitigation_gate.py` and `scripts/mitigation_unit.py` are byte-unchanged (`git diff --exit-code` exits 0).

## Issues Encountered

- **ruff `E501` on four message-string lines** — wrapped; no assertion text or semantics changed.
- **ruff `format` preferred `"""` over `'''` for the synthetic-source template** — accepted (the template contains no triple-quote sequence).

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_reference.py tests/test_phase22_dpsgd_ast.py -x -q` | **13 passed** (3 + 10) |
| `.venv/bin/python -c "import personacore.privacy"` | exit 0 |
| `git diff --exit-code -- pyproject.toml scripts/mitigation_gate.py scripts/mitigation_unit.py` | exit 0 — byte-unchanged |
| `grep -n "dpsgd.py" tests/test_phase22_dpsgd_ast.py` | 1 hit, a docstring line — no live read |
| `assert offenders == {}` present; no `in`/subset form | confirmed by grep |
| AST import set of `tests/fixtures/phase22_reference.py` | **empty** |
| Full suite `.venv/bin/python -m pytest -q` | **1037 passed, 1 skipped** |
| Lint `.venv/bin/ruff check . && ruff format --check .` | clean, 195 files formatted |

## Known Stubs

None. Every artifact in this plan is complete and consumed by its own tests. `_ALLOWED_CLASS_CONSTANTS` is an intentionally empty allowlist, not a stub — an empty allowlist is the strictest state, and it is asserted by hard equality.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file access outside `tests/`, and no schema. It installs nothing (T-22-SC: `pyproject.toml` untouched, verified byte-unchanged).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Wave-0 scaffolding is landed and consumable:

- **Plan 22-02** (`accountant.py`) imports `DELTA_FRONTIER`, `EPSILON_GOLDEN`, `ZERO_BOUNDARIES`, `QUADRATURE_PARAMS`, `GOLDEN_EPSILON_REL_TOL` from `tests.fixtures.phase22_reference`. Note V-01/V-02 must call `float(truth)` — the truths are decimal strings — and must **refuse a zero before comparing** (`VACUOUS_AGREEMENT_ROW` names the row where both oracles return `0.0`).
- **Plan 22-04 Task 2/3** imports `_assert_no_forbidden_between_noise_and_step` and `_assert_single_clip_constant` via `sys.path.insert(0, str(_ROOT / "tests"))`. `_assert_single_clip_constant(..., allowed_attr="C")` is green on a `dpsgd.py` whose per-record clip is the only method dividing a `self.<attr>` by a norm; a `finalize` carrying D-16's `self._writes == len(self._params)` and `self._prev_gen_state is not None` invariants does **not** enter its scope, and that is exercised in the GREEN baseline.
- **Plan 22-09** feeds mutated source strings to the same two functions — the same code CI runs, which is the property the text-taking factoring exists to guarantee.

**One environment note for every subsequent Phase-22 plan:** `make test` and `make lint` do not resolve the venv on this box. Use `.venv/bin/python -m pytest -q` and `.venv/bin/ruff check .` / `.venv/bin/ruff format --check .`.

## Self-Check: PASSED

- `src/personacore/privacy/__init__.py` — FOUND
- `tests/fixtures/phase22_reference.py` — FOUND
- `tests/test_phase22_reference.py` — FOUND
- `tests/test_phase22_dpsgd_ast.py` — FOUND
- commit `2c1bc35` — FOUND
- commit `3c27c9c` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-25*
