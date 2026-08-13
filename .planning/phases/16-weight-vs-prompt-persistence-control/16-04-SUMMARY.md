---
phase: 16-weight-vs-prompt-persistence-control
plan: 04
subsystem: infra
tags: [pre-registration, wilson-bound, licensing-threshold, ast-guard, stdlib-only, pytest]

# Dependency graph
requires:
  - phase: 16 (plan 03)
    provides: "the widened persona=/draw_all AST guards that now scan scripts/*.py — the new driver enters both scans automatically and must not trip either"
  - phase: 15 (PREREG-01, commit 23a830c)
    provides: "scripts/erasure_gate.py wilson_upper_bound / rule_of_three — every bound in the ladder, stdlib only (STAT-04)"
  - phase: 14 (teach-then-recall)
    provides: "results/phase14_recall_report.md:378 (the committed fairness-control floor), phase14_factset.exact_match_clean, and phase14_factset_gate._probe"
provides:
  - "scripts/phase16_ladder.py — the PERS-01 pre-registration: LADDER_FLOOR_*, LADDER_CELL_*, RUNG_DIFFICULTY_ORDER, cell_passed/cell_report/format_cell, licensed_headline, monotonicity_anomalies"
  - "LADDER_CELL_PASS_K = 10 at n = 216, committed before the run it judges and pinned to its derivation by test"
  - "The five licensed branches, with the all-fail branch first-class and no investigate-the-instrument escape hatch"
  - "probe_guessability() on scripts/phase14_factset_gate.py — the D-16 public entry point over an ARBITRARY string, which Phase 17's ISO-01 consumes unchanged"
  - "tests/test_phase16_ladder.py — 13 CPU-only, torch-free tests"
affects: [16-05, 16-06, 16-09, 16-10, 16-11, phase-17]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A licensing threshold is an integer LITERAL plus a test that recomputes it from the committed bound — the literal is the gate, the bound is its derivation, and the test is what stops them drifting"
    - "Verdict prose interpolates its constants; an AST scan forbids the threshold digits from appearing as string constants at all, with a single by-name allowlisted citation proved live"
    - "The all-fail branch is written FIRST and named as expected, so the outcome the evidence predicts is not the outcome that has no prose"
    - "Totality of a branch function is proved by enumerating the whole outcome space (2**7 = 128) against a hand-written expectation table, not against a re-derivation of the same dispatch"
    - "A cross-instrument surface is WIDENED additively in the instrument's own file (0 deletions) so both consuming phases import one implementation"

key-files:
  created:
    - "scripts/phase16_ladder.py — 343 lines; constants and pure functions only, nothing executes at import"
    - "tests/test_phase16_ladder.py — 434 lines; 13 tests, CPU-only, no torch at module scope"
  modified:
    - "scripts/phase14_factset_gate.py — +45 lines, 0 deletions: probe_guessability, placed immediately after _probe"

key-decisions:
  - "Choice 1 — LADDER_CELL_QUESTIONS = 216 (the full core set), identical to the floor's n and the top rung's n, which is what D-15's proxy-validity check requires"
  - "Choice 2 — multiplicity priced into the per-cell z (LADDER_CELL_Z = one-sided 1 - 0.05/6) because a false pass licenses the STRONGER headline; a choice of literal, not a hypothesis test, so D-09's Holm family stays closed at 6 pairs"
  - "Choice 3 — one literal for all 7 rungs: k_min is 10 at both the 6-cell and 7-rung quantiles, so the single literal costs nothing and removes an ambiguity that would otherwise be settled after seeing a number"
  - "licensed_headline raises on a rung key outside RUNG_DIFFICULTY_ORDER rather than ignoring it — a silently dropped rung downgrades the licence, which is the same failure by another route"
  - "monotonicity_anomalies compares only rungs PRESENT in cell_results, so a partial ladder cannot invent anomalies out of unmeasured cells"
  - "cell_results is keyed by rung to the cell_report ROW (read via row['passed']), one shape for the whole downstream wiring"

patterns-established:
  - "Pattern: pre-registration file layout — module docstring states the commitment, constants carry their derivation in COMMENTS (invisible to the string scan), functions carry the licensing semantics in docstrings"
  - "Pattern: deliberate-RED inside try/finally with byte-identity asserted on restore, so the mutation window is crash-safe"

requirements-completed: []  # advanced, none CLOSED — see "Deviation 4" (PERS-01 requires the ladder to RUN; STAT-01/02/05 span phases 17 and 18)
requirements-advanced: [PERS-01, STAT-01, STAT-02, STAT-05]

# Metrics
duration: 12min
completed: 2026-08-13
---

# Phase 16 Plan 04: The PERS-01 Ladder Pre-Registration Summary

**`LADDER_CELL_PASS_K = 10` at n = 216 is now in git with a test that recomputes it from `erasure_gate.wilson_upper_bound`, alongside a `licensed_headline()` that is total over all 128 rung subsets and whose all-fail branch licenses only the SC1 capability-deficit statement — committed before the ladder has produced a single number these thresholds judge.**

## Performance

- **Duration:** ~12 min wall clock (17:08 → 17:20 UTC)
- **Started:** 2026-08-13T17:08:27Z
- **Completed:** 2026-08-13T17:20:40Z
- **Tasks:** 3
- **Files created:** 2 · **Files modified:** 1
- **Tests added:** 13 (425 → 438 passed)

## Task Commits

1. **Task 1 — D-16: widen `phase14_factset_gate.py` with a public guessability probe** — `3e5a9e5` (feat)
2. **Task 2 — the ladder pre-registration constants and the cell arithmetic** — `135f845` (feat)
3. **Task 3 — `licensed_headline()`, total over the rung lattice** — `8f8d06e` (feat)

## The three planner choices, recorded before the run

These were settled in the plan and implemented exactly as stated. They are pre-registration, not preference, and they are repeated here because 16-05 and 16-09 consume them.

| Choice | Value | Reason |
|---|---|---|
| **1 — cell size `n`** | `LADDER_CELL_QUESTIONS = 216` (112 `core_taught` + 104 `core_held_out`) | Identical to the floor's `n` and to the top rung's `n`. That identity is what makes the comparison apples-to-apples and what D-15's proxy-validity check requires. Cost ~80 min of ladder wall clock on top of the ~39 min four-arm run; D-05 records the run as not cost-constrained. |
| **2 — multiplicity** | `LADDER_CELL_Z = 2.393979799818510`, the one-sided `1 - 0.05/6` quantile | A false pass licenses the STRONGER headline — the over-licensing direction this milestone exists to prevent. Cost is two extra questions. A CHOICE OF LITERAL, not a hypothesis test: no p-value, no verdict, so D-09's Holm family stays closed at exactly 6 pairs and STAT-06 is untouched. |
| **3 — top rung threshold** | the same literal for all 7 rungs | `k_min` is 10 at `n = 216` under both candidate quantiles (`z = 2.393980` and `z = 2.449998`), so a single literal costs nothing and removes an ambiguity that would otherwise be resolved after seeing a number. |

**Verified in-session before anything was written**, with the repo's own stdlib bound:
`wilson_upper_bound(1, 216) = 0.020481915502612365`; `k_min = 10` at both z values;
`rule_of_three(216) = 0.013888…`; `216 × 9 = 1944`.

## `RUNG_DIFFICULTY_ORDER` — the exact tuple 16-05 wires against

Do not re-derive it. Easiest to hardest, **span-major then distance**:

```python
LADDER_SPANS = (1, 2, 5)          # token lengths
LADDER_DISTANCES = (2, 30)        # approximate token distance to <|assistant|>
TOP_RUNG = "fairness-control-rerun"

RUNG_DIFFICULTY_ORDER = ((1, 2), (1, 30), (2, 2), (2, 30), (5, 2), (5, 30), TOP_RUNG)
```

Span dominates distance because span length is the primary suspect for where capability dies at
this scale (real values are 4-8 tokens over a 547-id near-character vocabulary in a 6-layer model).
The order is pre-committed precisely so "the highest passed rung" — the sole input to
`licensed_headline` — is not decided after seeing which cells passed.

Branch ids, keyed off the highest passed rung and nothing else:
`no_rung_passed` · `span_1` · `span_2` · `span_5_synthetic` · `top_rung_real`.

## What landed

### Task 1 — D-16 / the widening, additive by construction

`probe_guessability(model, tok, device, forbid, value, questions, *, start_index=0)` sits
immediately after `_probe` and **delegates every probe to it** — same `build_recall_prompt` call,
same greedy-plus-warm-draw regime, same per-probe `torch.Generator(SEED + index)` seeding, same
`STOP_IDS` and `forbid` mask. `start_index` exposes `main()`'s own `len(probe_cache)` offsetting
discipline so a caller running several batches gets disjoint streams.

`git show 3e5a9e5 -- scripts/phase14_factset_gate.py | grep -c '^-[^-]'` → **0**. `_probe`,
`_complete`, `main()`, every constant and every import are untouched.

The value's `clean` verdict is `phase14_factset.exact_match_clean` over every completion from every
question, flattened — the same unforgiving boundary as `main()`: ONE containment out of N is a FAIL.
The caller supplies `questions`, so the function holds no fact material of its own.

The test asserts the signature by **AST, not by import**: `phase14_factset_gate` does
`import phase14_factset as fs` at module level, so importing it in this test file would pull the
locked values into the process and defeat the clean-room scan the same file runs 12 tests later.

### Task 2 — the constants and the cell contract

Every derivation lives in `#` comments rather than docstrings, deliberately: Task 3's scan reads
string constants, and comments are the only place the floor's arithmetic can be written out in full
without becoming a retyped threshold. The anchor is the COMMITTED
`results/phase14_recall_report.md:378` line, and the comment says why it can never be the post-fix
re-run (D-13).

`cell_report` carries `answerable`, `questions`, `rate`, `wilson_upper_95`, `lower_bound`, `passed`,
and `rule_of_three_upper` **only** at zero. Two different bounds are present on purpose:
`wilson_upper_95` is the plain one-sided 95% bound for comparability with every other rate in the
milestone; `lower_bound` is the gate's own bound at the family-priced `LADDER_CELL_Z`. Naming which
one the gate reads is what stops the quieter of the two being chosen after the fact.

`format_cell` interpolates every number, including the gate itself
(`f"(gate: k >= {LADDER_CELL_PASS_K})"`).

### Task 3 — the licence

Five module-level branch statements, each naming what it does NOT license. The all-fail branch is
written first and longest, because it is the outcome the evidence actually predicts (Phase 14
measured this exact model with this exact prompt builder at the floor), and because a branch with
no prose is a branch someone writes after seeing the number. It contains, in the file, the sentence
that there is deliberately no "the ladder failed, investigate the instrument" branch — and the test
pins that sentence, so removing the refusal is as loud as adding the escape hatch.

`monotonicity_anomalies` returns `(easier, harder)` pairs over the rungs actually present in
`cell_results`. Absent ≠ failed: treating an unmeasured rung as failed would invent anomalies out of
a partial ladder.

## Observed RED #1 — Task 2, `LADDER_CELL_PASS_K` moved to 9

```
>       assert _derived_pass_k(ladder.LADDER_CELL_Z) == ladder.LADDER_CELL_PASS_K
E       assert 10 == 9
E        +  where 10 = _derived_pass_k(2.39397979981851)
E        +    where 2.39397979981851 = ladder.LADDER_CELL_Z
E        +  and   9 = ladder.LADDER_CELL_PASS_K

tests/test_phase16_ladder.py:164: AssertionError
FAILED tests/test_phase16_ladder.py::test_pass_k_is_the_derived_minimum
1 failed in 0.02s
```

Mutation applied and reverted inside a `finally`; **`RESTORED bytes-identical: True`**, and
`git diff --exit-code scripts/phase16_ladder.py` → exit `0` (checked while Task 2 was the committed
tip). The failure prints the recomputed 10 next to the literal 9 — the derivation and the gate named
side by side is the whole mechanism.

## Observed RED #2 — Task 3, a retyped threshold inside a branch statement

`"At 10/216 -- "` prepended to `BRANCH_SPAN_1`:

```
>       assert offenders == [], offenders
E       AssertionError: ["At 10/216 -- HIGHEST PASSED RUNG: SPAN 1. LICENSED: the base can use a ONE-TOKEN value placed in its context window ...
E       assert ['At 10/216 -...arates them.'] == []
E         Left contains one more item: "At 10/216 -- HIGHEST PASSED RUNG: SPAN 1. ...

tests/test_phase16_ladder.py:379: AssertionError
FAILED tests/test_phase16_ladder.py::test_licensed_headline_retypes_no_threshold_literal
```

The guard quotes the offending statement back, so the failure names the prose rather than a line
number. Reverted inside a `finally`, **`RESTORED bytes-identical: True`**. (`git diff` was non-empty
at that moment only because Task 3 was still uncommitted; the byte-identity assertion is the proof,
and the working tree after the Task 3 commit carries only the two pre-existing unrelated items.)

## Verification

```
.venv/bin/python -m pytest tests/test_phase16_ladder.py -q
    13 passed

.venv/bin/python -m pytest tests/test_phase16_ladder.py tests/test_phase14_scoring.py \
                          tests/test_phase14_factset.py -q
    63 passed

.venv/bin/python -m pytest -q
    438 passed, 1 skipped, 83 warnings in 119.91s (0:01:59)

.venv/bin/python -m ruff check .            All checks passed!
.venv/bin/python -m ruff format --check .   145 files already formatted

git show 3e5a9e5 -- scripts/phase14_factset_gate.py | grep -c '^-[^-]'    0
git status --short                          M .gitignore / ?? AGENTS.md  (both pre-existing)
```

**Baseline was `425 passed, 1 skipped, 83 warnings in 124.53s`, captured by the orchestrator
immediately before dispatch. Result `438 passed, 1 skipped`. Delta `+13` = this plan's 13 new tests.
Zero failed, zero errors, zero collection errors.**

### Acceptance criteria, item by item

| Task | Criterion | Result |
|---|---|---|
| 1 | `pytest tests/test_phase16_ladder.py -q` exits 0 | 1 passed at that commit |
| 1 | `grep -c "def probe_guessability"` == 1 | **1** |
| 1 | plan's AST one-liner on the parameter list | exit `0` |
| 1 | calls `_probe`, constructs no `torch.Generator` | asserted in the test |
| 1 | `git diff scripts/phase14_factset_gate.py` shows 0 deletions | **0** |
| 1 | `pytest tests/test_phase14_factset.py -q` still 0 | 8 passed |
| 2 | `>= 7` tests collected | **8** |
| 2 | file carries `2.393979799818510`, `0.020481915502612365`, `216`, `9`, `LADDER_CELL_PASS_K = 10` | all present |
| 2 | AST: no module-level `phase14_factset*` import, direct or via the gate | exit `0` |
| 2 | `grep -c scipy` == 0 | **0** (see Deviation 2) |
| 2 | `grep -c "from erasure_gate import\|import erasure_gate"` >= 1 | **1** |
| 2 | importlib load < 2 s | asserted every run by `test_ladder_module_executes_nothing_at_import` |
| 2 | deliberate RED at `k = 9` | above, verbatim |
| 3 | `>= 12` tests collected | **13** |
| 3 | totality test exercises 128 subsets | `assert seen == 128` in the test source |
| 3 | `grep -c "def licensed_headline"` / `"def monotonicity_anomalies"` == 1 | **1** / **1** |
| 3 | `pytest tests/test_phase14_factset.py tests/test_phase14_scoring.py -q` exits 0 | 50 passed |
| 3 | deliberate RED with a retyped `"10/216"` | above, verbatim |

## Instrument-integrity guards this plan had to clear (16-03's, unchanged)

- **`PERSONA_ALLOWLIST` was NOT touched.** `scripts/phase16_ladder.py` contains no `persona=` call
  site, and the assertion is hard equality in both directions — a pre-added entry would have turned
  the suite red exactly as loudly as an unlisted call site. The `("scripts/phase16_ladder.py",
  "build_far_prompt")` line still belongs to 16-05, in the same commit as the call site.
- **`DRAW_ALL_ASSERTED_BY` was NOT touched.** This plan adds no drawing path: nothing here loads a
  model or generates a token, by design.
- Both guards nonetheless *scanned* the new file the moment it landed (69 → 70 files under
  `scripts/*.py` + `src/**/*.py`), which is the property 16-03 bought.

## Decisions Made

- **`licensed_headline` raises on an unknown rung key** instead of ignoring it. A typo'd key that
  is silently dropped downgrades the licensed branch — the same over-/under-claiming failure the
  function exists to prevent, arriving by a different route. One line, at the trust boundary
  between the run driver and the licence.
- **`monotonicity_anomalies` compares only rungs present in `cell_results`.** An unmeasured rung is
  absent, not failed. The alternative invents anomalies whenever the ladder is run partially, which
  would make the instrument-broken signal fire on an incomplete run.
- **`cell_results` is keyed rung → `cell_report` row**, read via `row["passed"]`. That is the shape
  the ladder driver will already have, so 16-05 needs no adapter; `licensed_headline` takes the
  passed-key list derived from it in one comprehension.
- **The expectation table in `test_licensed_headline_is_total` is hand-written**
  (`_EXPECTED_BRANCH_BY_INDEX`), not recomputed from the driver's span lookup. A test that
  re-derives the branch the same way the code does only proves the code agrees with itself.
- **`format_cell` reports proportions, never percentages.** STAT-02's "no bare 0%" is satisfied
  structurally rather than by formatting discipline: there is no `%` rate in the line at all, and
  the denominator plus both bounds are always present.
- **A `__main__` self-check block was deliberately not added** to `scripts/phase16_ladder.py`. The
  plan reserves the `__main__` guard and `main()` for 16-05, and the runnable check for this logic
  is `tests/test_phase16_ladder.py`.

## Concern recorded, implemented AS LOCKED

**`test_all_fail_branch_is_the_sc1_capability_deficit_statement` pins two exact English phrases**
(`"licenses no claim that weights beat prompting"` and `"investigate the instrument"`) inside
`BRANCH_NO_RUNG_PASSED`. That is intentional here — the branch text IS the pre-registration and a
reworded refusal is a weakened refusal — but it means an editorial pass over that paragraph turns
the suite red for a prose reason rather than a semantic one. Whoever rewords it should update the
pinned phrases in the same commit and say so, rather than loosening the assertion to a keyword
match, which would let the refusal be dropped entirely.

## Deviations from Plan

### 1. [Environment] `make test` / `.venv/bin/pytest` substituted with venv-explicit invocations

- **Plan text:** `<verification>` specifies `make test`; `<verify>` blocks specify `.venv/bin/pytest`.
- **What was run:** `.venv/bin/python -m pytest -q`, `.venv/bin/python -m ruff check .`.
- **Why:** recorded fact about this machine, same substitution as 16-01/16-02/16-03 — a bare
  `pytest` resolves to a pyenv 3.12 shim and yields ~63 spurious
  `ModuleNotFoundError: No module named 'torch'` collection errors across files this plan never
  touched. The gate actually run is the full suite the `make` target wraps.

### 2. [Rule 3 — Blocking] The module docstring's dependency sentence was rewritten to drop the word "scipy"

- **Found during:** Task 2, running the acceptance criteria.
- **Issue:** the STAT-04 sentence originally read "No scipy: STAT-04, …", which is exactly the
  right statement to make and which made `grep -c "scipy" scripts/phase16_ladder.py` return **1**
  against a locked criterion of **0**.
- **Fix:** rewritten to "Zero new dependencies — STAT-04, and this project has already declined a
  statistics package in committed code more than once…". Same commitment, same specificity about
  the precedent, and the grep is now a real signal (any future hit is a real import) instead of one
  the docstring pre-empts.
- **Files modified:** `scripts/phase16_ladder.py`
- **Verification:** `grep -c 'scipy'` → 0; full suite green.
- **Committed in:** `135f845` (Task 2 commit)

### 3. [Structure] Two helpers the plan did not name

- `_derived_pass_k(z)` in the test file, so `test_pass_k_is_the_derived_minimum` and
  `test_pass_k_is_insensitive_to_family_size` run the SAME recomputation at two quantiles. Two
  copies of the derivation could disagree, which is the defect class this file exists to close.
- `_SPAN_BRANCH` in the driver, a pre-committed span → branch-id mapping. An unmapped span raises
  rather than falling through to a neighbouring branch's prose.
- `test_ladder_module_executes_nothing_at_import` is a named test rather than a bare acceptance
  check, so the plan's "< 2 s importlib load" criterion is asserted on every run instead of once.

### 4. [Rule 2 — Missing Critical] `REQUIREMENTS.md` was restored: none of this plan's four requirements is CLOSED

- **Found during:** state updates, after `requirements mark-complete PERS-01 STAT-01 STAT-02 STAT-05`
  checked all four boxes and flipped all four traceability rows to `Complete`.
- **Issue:** the resulting artifact stated things that are false. **PERS-01** reads "A blocking
  in-context capability ladder **runs** and is recorded before any comparison is scored" — this plan
  pre-registers the ladder; 16-06 and 16-07 run it, and both list PERS-01 in their own frontmatter.
  **STAT-01 / STAT-02 / STAT-05** are milestone-wide disciplines whose traceability rows read
  `16, 17, 18`; marking them Complete claims compliance for two phases that do not exist yet.
- **Precedent, not preference:** 16-01's frontmatter listed `[PREREG-02, STAT-04]` and the committed
  `REQUIREMENTS.md` shows `PREREG-02 | Complete` and `STAT-04 | Pending` — that plan already held
  back the multi-phase discipline and marked only what it had actually closed. `PERS-05` and
  `PERS-06` are `Complete` because 16-02 and 16-03 finished them outright.
- **Fix:** `.planning/REQUIREMENTS.md` restored byte-exact from `HEAD`
  (`git diff --exit-code .planning/REQUIREMENTS.md` → exit `0`). The frontmatter above records these
  four as **advanced**, not completed. PERS-01 should be checked by whichever of 16-06/16-07 first
  has a recorded ladder run; STAT-01/02/05 at the milestone's close.
- **Why this outranks the executor default:** a declared invariant silently becoming false is the
  defect this project names as its most recurring, and this phase exists to stop exactly that. A
  requirement checked before its own text is true is that defect in the requirements ledger.

---

**Total deviations:** 4 (1 environment, 1 Rule 3 blocking, 1 structure, 1 Rule 2 artifact-honesty).
**No behaviour the plan specifies was changed.** Every constant, function name, branch id, test name
and threshold is as locked.

## Issues Encountered

- **The plan's `<interfaces>` line numbers were stale**, as 16-03 also recorded: `n_answerable` is
  at `scripts/phase14_recall.py:1296`, not `:1219`. Located by grep rather than by line, so it cost
  nothing; noted so a later reader does not chase it.
- **`repr(NormalDist().inv_cdf(1 - 0.05/6))` prints `2.39397979981851`** — Python drops the trailing
  zero of the plan's `2.393979799818510`. Same float, and
  `test_pass_k_is_insensitive_to_family_size` asserts the equality directly, so the committed
  literal is provably the quantile and not a transcription of it.
- **No package was installed and none was needed.** `pyproject.toml` is byte-unchanged, so 16-01's
  STAT-04 freeze was never approached.
- **The dangling identifier D-10 declares non-existent** stayed out of the touched files, all three
  commit messages, and this summary; `grep -rn` over the repo excluding `.git`/`.venv`/`.planning`
  still returns nothing.

## Next Phase Readiness

- **16-05 has everything it needs and one obligation.** `RUNG_DIFFICULTY_ORDER` is quoted verbatim
  above; wire the grid against it rather than re-deriving it. The obligation is unchanged from
  16-03: adding `build_far_prompt` with a `persona=` argument requires
  `("scripts/phase16_ladder.py", "build_far_prompt")` in `PERSONA_ALLOWLIST` **in the same commit**,
  and any new `draw_all` call site must assert in place or name an asserter that exists.
- **The lazy-import rule is now load-bearing in this file.** 16-05's `main()` must import
  `phase14_factset_gate` (for `probe_guessability`) and `phase14_recall` INSIDE functions.
  `test_ladder_driver_holds_no_fact_strings_at_import` scans docstrings too, so a value quoted in a
  new docstring fails exactly like a module-level import.
- **The distance-~2 rungs remain the ladder's real discriminator** (RESEARCH Q2) and are invisible
  to the `persona=` guard by construction — they carry the value in the `question` string. 16-03's
  `draw_all` guard is what covers them.
- **`probe_guessability` is Phase 17's import path as well.** It takes an arbitrary string and holds
  no fact material, so ISO-01 consumes it unchanged; a second copy anywhere is a D-16 violation.
- **One thing to watch:** `cell_passed`/`cell_report` default `n_questions` to
  `LADDER_CELL_QUESTIONS`. If a cell is ever run at a different `n`, `LADDER_CELL_PASS_K` no longer
  holds — RESEARCH's table gives `k_min` for six smaller `n` values, and the anti-pattern list
  forbids differing `n` across cells. The default makes the correct call the easy one; it does not
  prevent the wrong one.

## Self-Check: PASSED

`scripts/phase16_ladder.py` (343 lines) and `tests/test_phase16_ladder.py` (434 lines) exist on
disk; `scripts/phase14_factset_gate.py` carries `probe_guessability` (grep → 1) with zero deletions
in its commit. All three task commits resolve in `git log`: `3e5a9e5`, `135f845`, `8f8d06e`. Both
deliberate-RED observations were run and their output is reproduced verbatim above; both mutations
restored byte-identical inside a `finally`. Full suite `438 passed, 1 skipped`, ruff clean. Working
tree carries only the two pre-existing unrelated items this plan did not touch: modified
`.gitignore`, untracked `AGENTS.md`.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
