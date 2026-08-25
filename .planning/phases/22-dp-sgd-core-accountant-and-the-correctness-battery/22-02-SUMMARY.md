---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 02
subsystem: privacy
tags: [differential-privacy, pre-registration, ancestry-guard, ast-guards, accountant, adjacency]

# Dependency graph
requires:
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "scripts/mitigation_unit.py — the verbatim structural template, its PRIVACY_UNIT vocabulary, and DELTA as the delta every golden row is evaluated at"
  - phase: 20-pre-registration-the-three-condition-gate
    provides: "tests/test_phase20_prereg.py::_assert_ordering_holds, _git's keyword-only cwd, _enclosing_functions, the collapsed-glob meta-guard, and the mitigation_*.py import ceiling"
provides:
  - "scripts/mitigation_accountant.py — the frozen (epsilon, delta) pin: REQUIRED_FORM, its five composition preconditions, REJECTED_FORM as a string plus a measured two-part reason, D-18's NEIGHBOURING/SENSITIVITY_MULTIPLIER pair, SIGMA_IS_THE_NOISE_MULTIPLIER, and seven oracle-derived GOLDEN_EPSILON rows"
  - "PHASE22_PREREG_ARTIFACT + results/phase23_* in V4_ARTIFACT_GLOBS + the matching _assert_ordering_holds call — D-11's BOTH halves"
  - "test_phase23_glob_sees_the_phase23_prefix_red_then_green — the phase23 prefix OBSERVED matching, RED then GREEN"
  - "test_mitigation_accountant_pin_has_no_executable_formula — V-10's zero-import/no-formula guard, stricter than the accumulated subset ceiling"
affects: [22-03 accountant closed form, 22-05 quadrature oracle, 22-09 fake probes and V-06/V-25, 23 cost calibration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A frozen artifact that cites by NAME and SYMBOL only — zero line-number anchors, because a stale anchor inside a frozen file can never be corrected"
    - "Module-scope proofs written with slice and chained comparisons instead of len/sorted/abs, so that 'every module-level call is a _prove call' can be asserted literally"
    - "Structural row location (steps ** 0.5 / sigma within tolerance) asserted equal to positional indices — the locator and the positions cross-check each other"
    - "Stale line anchors REMOVED and replaced by statement-text citations rather than renumbered"

key-files:
  created:
    - scripts/mitigation_accountant.py
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/deferred-items.md
  modified:
    - tests/test_phase20_prereg.py

key-decisions:
  - "The pin contains ZERO line-number citations. scripts/mitigation_unit.py is frozen carrying four stale ones that can never be corrected; this file copies its structure and deliberately not that habit"
  - "arXiv references are written 'arXiv 1805.06530' rather than 'arXiv:1805.06530' so the acceptance grep for line-number anchors stays clean and honest"
  - "The composition proof locates its three rows STRUCTURALLY and asserts hard equality against indices 1/5/6 — never by the plan's 'last three rows' phrasing, which is a mis-transcription"
  - "The ε > 1 boundary is pinned at the measured 4.844805262605389, not the plan's '~4.85' — the approximation is wrong on the interval (4.8448, 4.85]"
  - "requirements.mark-complete was NOT called: a pre-registration contributes to DPSGD-03/04, it does not satisfy either"

requirements-completed: []
requirements-contributed: [DPSGD-03, DPSGD-04]

# Metrics
duration: 30min
completed: 2026-08-25
---

# Phase 22 Plan 02: The Frozen Accountant Pin and Its Ancestry Guard Summary

**The (ε, δ) accounting rule pre-registered a whole phase before the first ε-bearing artifact — form, rejection, adjacency and seven oracle-derived outputs in a zero-import file whose eight self-guards and whose external no-formula guard were each watched failing on fifteen distinct mutations before being believed.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-08-25T21:02Z (first read after `a180335`)
- **Completed:** 2026-08-25T21:32Z
- **Tasks:** 2
- **Files created:** 2 (1 modified)

## Accomplishments

- **`scripts/mitigation_accountant.py` exists and is frozen-on-first-artifact.** Zero imports, exactly one function, no runnable rejected formula, and no line-number citation anywhere in 493 lines.
- **D-18 finally landed.** `NEIGHBOURING = "add/remove one fact"` and `SENSITIVITY_MULTIPLIER = 1.0` — the two constants `.planning/research/PITFALLS.md` P3 assigned to P20 and P21, which both closed without shipping them. The stake is recorded as a number (roughly 2× on every published ε), not as a concern.
- **The five composition preconditions are written down**, three of which appear in no other committed artifact: homogeneous σ/Δ across all T steps, T fixed in advance rather than a data-dependent stopping time, and adaptivity permitted at no cost.
- **`REJECTED_FORM` carries both halves of its rejection with their measured numbers** — the `ε ∈ (0,1)` hypothesis violation below σ = 4.844805262605389, and the 35.7× over-claim of privacy at σ = 0.3 past the μ = 1.737896746 crossover.
- **D-11's both halves are live.** `results/phase23_*` in `V4_ARTIFACT_GLOBS` *and* a matching `_assert_ordering_holds` call. Phase 21 D-20's finding — that the glob addition alone enforces nothing — is stated in the new test's own docstring rather than left to be re-discovered a third time.
- **The `phase23_` prefix has been OBSERVED matching**, RED then GREEN, across five states of a throwaway repository including a real delete-and-re-add cycle proving the ordering cannot be laundered.
- **Two stale line anchors were removed from the file whose entire purpose is pre-registration integrity** — and removed rather than renumbered, with the reason recorded in place.

## Task Commits

1. **Task 1: The frozen pin `scripts/mitigation_accountant.py`** — `36ce7fb` (feat)
2. **Task 2: D-11's two halves + the phase23 RED-then-GREEN fixture + V-10's guard** — `cfe8cbc` (test)

## Files Created/Modified

- `scripts/mitigation_accountant.py` (new, 493 lines) — the pin. Four docstring headings mirroring `mitigation_unit.py`, a local `_prove`, `REQUIRED_FORM` + `REQUIRED_FORM_CONDITIONS`, `REJECTED_FORM` + `REJECTED_FORM_REASON`, `NEIGHBOURING` + `NEIGHBOURING_REASON` + `SENSITIVITY_MULTIPLIER` + `SENSITIVITY_MULTIPLIER_REASON`, `SIGMA_IS_THE_NOISE_MULTIPLIER`, `GOLDEN_EPSILON` + `GOLDEN_EPSILON_PROVENANCE` + `GOLDEN_EPSILON_REL_TOL` + `GOLDEN_EPSILON_DELTA_SOURCE`, then eight module-scope guards.
- `tests/test_phase20_prereg.py` (+411/−9) — `PHASE22_PREREG_ARTIFACT`, the third glob entry, the rewritten comment block, and three new tests. 22 → 25 tests.
- `.planning/phases/22-.../deferred-items.md` (new) — the out-of-scope stale anchors, measured and left alone.

## Decisions Made

- **The pin cites nothing by line number.** `22-PATTERNS.md` Stale Anchor Finding #4 measured four stale test-file anchors inside the now-frozen `mitigation_unit.py`; they cannot be corrected except by a dated continuation and will be wrong for as long as the repository exists. This file copies that file's structure and deliberately not that habit. It also forced a small choice: arXiv identifiers are written `arXiv 1805.06530`, because `arXiv:1805.06530` matches the `:[0-9]+` acceptance grep and would have made a clean check noisy for no gain.
- **Zero module-level calls, not merely "no non-`_prove` calls".** V-10's criterion is that every module-level `ast.Call` is a `_prove` call. Honouring that literally meant the pin's own guards could use no `len`, `sorted` or `abs` — so a seven-row count is `GOLDEN_EPSILON[6:] == (GOLDEN_EPSILON[-1],)` and a tolerance is a chained `-1e-12 <= x - 1.0 <= 1e-12`. The guard block carries a comment saying why, so a later reader does not "tidy" `len()` back in and redden a guard for a reason that looks like pedantry.
- **The composition proof is two guards, not one.** The first locates the μ_eff = 1.0 rows structurally and asserts the located set *equals* rows 1, 5 and 7; the second asserts those three carry one ε, with every mu_eff and every deviation from 1.0 computed inside the message. The locator and the positions therefore cross-check each other: a mistyped σ breaks the first, a perturbed ε breaks the second, and a reorder breaks both.
- **`requirements.mark-complete` was NOT called**, following 22-01's precedent for the same reason. DPSGD-03 requires an accountant agreeing with two oracles of different mathematics (plans 22-03 / 22-05); DPSGD-04 requires four fakes each with its positive control watched failing (plan 22-09). A pre-registration is the thing those will be judged against, not evidence that either holds. Both stay `- [ ]`.
- **State 5's fixture filename is labelled a stand-in.** The Phase-21 sibling could name the exact file its own phase commits; Phase 23 is `0/TBD, Not started`, so there is no real filename to rehearse and asserting one would be exactly the unevidenced claim this file exists to refuse.

## Guards Watched Failing

Neither guard was believed on the strength of being green. Both were run against mutated sources — the *committed* code in both cases, reached by parameterizing the test's root rather than by editing the working tree.

**V-10 (`test_mitigation_accountant_pin_has_no_executable_formula`) — 7 mutations, 7 distinct REDs, control GREEN:**

| Mutation | Caught by |
|---|---|
| `import math` added | empty-import-set assertion |
| `def rejected_epsilon(sigma)` appended | exactly-one-FunctionDef assertion |
| `_TOTAL = len(GOLDEN_EPSILON)` appended | module-level-calls-are-`_prove` assertion |
| `GOLDEN_EPSILON_REL_TOL = 1.0 / 1e12` | BinOp-in-a-constant assertion |
| `FIRST_SIGMA = GOLDEN_EPSILON[0][0]` | literal-only-assign assertion |
| `math.exp(0.0) == 1.0 and ...` inside a guard | module-level-calls assertion (`math.exp`) |
| empty module body | collapsed-walk meta-guard |

**The pin's own module-scope guards — 8 mutations, 8 `SystemExit`s, control imports clean:**
multiplier flipped to 2.0; relation flipped to replace-one with the multiplier left at 1.0; a composition row's σ mistyped `sqrt(200)` → `14.14`; one unit-μ_eff ε perturbed in its last digit; an eighth row appended; monotonicity broken by a transposed digit; a negative σ; and the degenerate edit setting `REJECTED_FORM = REQUIRED_FORM`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan repeats 22-RESEARCH's "last three rows" mis-transcription — the one 22-01 already corrected once**

- **Found during:** Task 1
- **Issue:** The plan's composition-proof instruction says *"The last three `GOLDEN_EPSILON` rows all have `mu_eff = sqrt(T)/sigma == 1.0`"* and then names them correctly by value: `(14.142135623730951, 200)`, `(1.0, 1)`, `(8.0, 64)`. Measured against the row ordering the plan itself specifies, the last three rows are `(2.0, 200)`, `(1.0, 1)` and `(8.0, 64)` — and `(2.0, 200)` has μ_eff = √200/2 = 7.0710678118654755 with ε = 54.376639014985045. The positional phrase and the value list disagree. This is the second time this exact sentence has produced a defect (22-01 deviation #2).
- **Fix:** The proof never uses position as its locator. `[row for row in GOLDEN_EPSILON if -1e-12 <= row[1] ** 0.5 / row[0] - 1.0 <= 1e-12]` is asserted **equal** to `[GOLDEN_EPSILON[1], GOLDEN_EPSILON[5], GOLDEN_EPSILON[6]]` — structural location and positional identity checking each other. `GOLDEN_EPSILON_PROVENANCE` records the mis-transcription in the frozen file so it cannot be inherited a third time.
- **Files modified:** `scripts/mitigation_accountant.py`
- **Verification:** mutation P3 (σ mistyped to 14.14) `SystemExit`s on the locator; the unmutated pin imports clean.
- **Committed in:** `36ce7fb`

**2. [Rule 1 - Bug] `~4.85` is the wrong boundary; the measured value is 4.844805262605389**

- **Found during:** Task 1
- **Issue:** The plan's `REJECTED_FORM_REASON` text says *"every σ below ~4.85 at the frozen δ produces ε > 1"*. The classical ε is `√(2 ln(1.25/δ))/σ`, so at the frozen δ the ε = 1 boundary IS `√(2 ln(1.25/δ))` = 4.844805262605389 exactly. `~4.85` is wrong on `(4.844805262605389, 4.85]`, where ε < 1 and the theorem's hypothesis is satisfied. A frozen file cannot be corrected, so a rounded boundary would have been permanent.
- **Fix:** The exact measured value is pinned, and the prose notes what the boundary means in practice (the whole usable operating range sits below it, so this is not an edge case).
- **Files modified:** `scripts/mitigation_accountant.py`
- **Verification:** `math.sqrt(2*math.log(1.25/1e-5))` → `4.844805262605389`; `4.844805262605389/0.3` → `16.1493508753513`, matching the research table's `16.149351`.
- **Committed in:** `36ce7fb`

**3. [Rule 1 - Bug] My own first draft re-introduced both defects it was recording**

- **Found during:** Task 1 and Task 2 acceptance-criteria runs
- **Issue:** Two instances of the same mistake, caught by the plan's own mechanical criteria before either was committed. (a) The pin's section header read *"there is deliberately no `rejected_epsilon()`"* — true, well-intentioned, and it put the forbidden name back in the file for the next `grep -n "rejected_epsilon"` to find. (b) The "why the anchors were removed" note read *"THE TWO SENTENCES ABOVE USED TO CITE `:129` AND `:150`"* — which failed `grep -n ':129'` **and** the plan's success criterion that this plan introduce no new line-number anchor, and which literally re-created the stale anchor one line below the paragraph explaining why stale anchors are bad.
- **Fix:** (a) rewritten to "deliberately NOT a runnable function (D-09)". (b) rewritten to describe the removal without quoting the numbers, with a sentence stating *why* they are not repeated: quoting a stale anchor to record its removal puts it back for the next grep.
- **Files modified:** `scripts/mitigation_accountant.py`, `tests/test_phase20_prereg.py`
- **Verification:** `grep -c "rejected_epsilon" scripts/mitigation_accountant.py` → 0; `grep -c ':129\|:150' tests/test_phase20_prereg.py` → 0; the broader `` `:NNN` `` pattern went from **7 lines at HEAD to 6**, with zero introduced by this plan and none inside any of the three new tests.
- **Committed in:** `36ce7fb`, `cfe8cbc`

**4. [Rule 1 - Bug] Five `gsd-sdk` mutation-handler defects, hand-repaired before commit**

- **Found during:** State updates
- **Issue:** Twelfth consecutive session. Measured this time: (a) `state.advance-plan` rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — the identical corruption 22-01 recorded; (b) `roadmap.update-plan-progress` wrote the status cell as `In Progress|  |` — no space before the pipe and an empty date cell where every sibling row carries `-` — also identical to 22-01; (c) `state.add-decision` prefixed all three entries `- [Phase ?]:`; (d) `state.update-progress` returned `{"updated": false, "reason": "Progress field not found in STATE.md"}` and did nothing, though the `progress:` block was already correct; (e) **new this session** — `state.record-session` updated both timestamps but silently left `stopped_at:` and `Stopped at:` reading `Completed 22-01-PLAN.md`.
- **Also measured — the documented call signatures are wrong.** `state.record-metric` with the positional argv the workflow documents returns `{"error": "phase, plan, and duration required"}`, and `state.add-decision` with a positional summary returns `{"error": "summary required"}`. Both work with `--flag` form. 22-01's positional `record-metric` call *was* accepted, so the signature changed or the two verbs disagree.
- **Fix:** All five hand-repaired in place before the metadata commit, each verified by `git diff`. The roadmap count was also corrected `1/11` → `2/11`, since the handler ran before this summary existed on disk.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** `grep -c "Phase ?" .planning/STATE.md` → 0; `Status: Executing Phase 22`; both `stopped_at` fields read `22-02`; the roadmap row matches its siblings byte for byte.
- **Committed in:** the plan metadata commit

### Deliberate departures from the plan text

- **`grep -n "rejected_epsilon"` returns nothing, so the pin cannot name the forbidden symbol even to disclaim it.** The disclaimer lives in `REJECTED_FORM_REASON` as prose instead, which is stronger anyway — it explains *why* rather than announcing an absence.
- **The plan says BinOp is "permitted ONLY inside `_prove` call arguments"; the guard asserts that as a set equality** (`everywhere == proved`) rather than as a subset, so arithmetic in a keyword argument or a nested comprehension outside the args is caught too.
- **State 5 of the phase23 fixture uses `results/phase23_cost_calibration.json`, labelled a shape stand-in.** See Decisions.

---

**Total deviations:** 4 auto-fixed (2 defects in the plan's own transcribed numbers, 1 self-inflicted and caught by the plan's own criteria, 1 tooling corruption), 3 deliberate departures.
**Impact on plan:** Every correction makes the pin assert *more* than specified; none weakens a guard. No scope creep — `scripts/mitigation_gate.py`, `scripts/mitigation_unit.py` and `pyproject.toml` are byte-unchanged (`git diff --exit-code` exits 0), which is T-22-SC's own criterion.

## Issues Encountered

- **Eight ruff `E501` wraps** across both files; no assertion text or semantics changed. One was a genuine restructure: two f-string expressions computing μ_eff deviations were 112 characters and cannot be split (a Python 3.11 f-string expression may not span lines), so the message now reports each row's deviation **from 1.0** on its own line — which is also the more meaningful margin, since 1.0 is what the composition identity predicts.
- **One transcription slip caught by re-reading**: an E501 wrap dropped `GOLDEN_EPSILON[3][1]` from the monotonicity guard's failure message. Restored; the message now lists all five step counts.
- **`make test` / `make lint` still do not resolve the venv** on this box (22-01 deviation #3, unchanged). All verification ran through `.venv/bin/`.
- **The mutation probes were restructured mid-run.** The first two attempts mutated the real working-tree file and restored it with `git checkout -- <file>`; a repository safety gate refused the command twice. The replacement runs the *same committed test function* against mutated copies in a temp directory by patching `_ROOT` and `_GATE_MODULES` — which touches nothing in the work tree and is strictly better evidence, since it is the identical shape 22-01 established for text-taking guards.

## Verification

| Check | Result |
|---|---|
| `ast` walk of the pin: `Import` + `ImportFrom` nodes | **0** |
| Executing the pin (8 module-scope `_prove` guards run at import) | exit 0 |
| `grep -c "^def " scripts/mitigation_accountant.py` | **1** |
| `grep -c "rejected_epsilon" scripts/mitigation_accountant.py` | **0** |
| `grep -cE ":[0-9]+" scripts/mitigation_accountant.py` | **0** |
| `NEIGHBOURING == "add/remove one fact"`, `SENSITIVITY_MULTIPLIER == 1.0` | confirmed |
| `len(GOLDEN_EPSILON) == 7`, `GOLDEN_EPSILON_REL_TOL == 1e-12` | confirmed |
| `V4_ARTIFACT_GLOBS` | 3-tuple ending `"results/phase23_*"`, no `phase22_*` entry |
| `artifact_glob="results/phase23_*"` call sites | **6** (1 live test + 5 fixture states) |
| `grep -c ':129\|:150' tests/test_phase20_prereg.py` | **0** |
| `` grep -cE 'at `:[0-9]+`' `` | **2 → 1** |
| `` `:NNN` `` anchors inside the three new tests | **0** (verified by AST line-range scan) |
| `.venv/bin/python -m pytest tests/test_phase20_prereg.py -x -q` | **25 passed** (was 22) |
| `-k "phase23 or accountant"` | **3/25 collected**, 3 passed — non-vacuous by collected count |
| V-10 guard mutation probes | **7 RED / 7**, control GREEN, 7 distinct messages |
| Pin self-guard mutation probes | **8 SystemExit / 8**, control imports clean |
| `git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_unit.py pyproject.toml` | exit 0 |
| Full suite `.venv/bin/python -m pytest -q` | **1040 passed, 1 skipped** (baseline 1037/1 + 3 new) |
| `.venv/bin/ruff check . && ruff format --check .` | clean, 196 files formatted |

## Known Stubs

None. Every constant in the pin is consumed by its own module-scope guards or by an already-committed test, and every test added is green against real committed state. `GOLDEN_EPSILON`'s σ/steps columns are labelled in the file as arithmetic test vectors rather than a budget — that is a deliberate scope boundary against `scripts/mitigation_budget.py` (Phase 20's Z boundary), not an unfinished value.

## Threat Flags

None. No network endpoint, no auth path, no file access outside `scripts/` and `tests/`, no schema. T-22-SC holds: nothing installed, `pyproject.toml` byte-unchanged.

Threat register dispositions, each mitigated as planned: T-22-05 (both D-11 halves live), T-22-06 (prefix observed matching in a throwaway repo), T-22-07 (D-18's pair pinned with its stake), T-22-08 (`GOLDEN_EPSILON_PROVENANCE` records oracle derivation), T-22-09 (V-10 asserts empty imports, one `FunctionDef`, `_prove`-only calls, literal-only assigns — watched failing on all four), T-22-09b (anchors removed, not renumbered; zero introduced).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-03 / 22-05** (`accountant.py`, the quadrature oracle) must import `GOLDEN_EPSILON` from `tests/fixtures/phase22_reference.py::EPSILON_GOLDEN`, **not** from this pin — the pin cannot be imported by `src/`, and the fixture holds the same seven rows with the same provenance. The pin is what a *test* reads to prove the two agree.
- **Plan 22-09** owns V-06 (re-derive every `GOLDEN_EPSILON` row from `delta_quadrature` alone) and V-25 (`test_adjacency_relation_consistent`). The pin names that test by symbol in `SENSITIVITY_MULTIPLIER_REASON`, so **the name is now load-bearing**: `tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent` must be created under exactly that name, or a frozen file cites a test that does not exist. This is the single hardest constraint this plan hands forward.
- **`scripts/mitigation_accountant.py` is not yet frozen** — it freezes at the first tracked `results/phase23_*` file. Any correction needed before then is a normal edit; after then it is a dated continuation via `scripts/_addendum.py` and nothing else.
- **Phase 23 must not name its first artifact before reading `deferred-items.md`** — no `results/phase23_*` path may be committed in the same commit as a pin edit, and `_assert_ordering_holds`'s strict conjunct refuses even a same-commit landing.

## Self-Check: PASSED

- `scripts/mitigation_accountant.py` — FOUND
- `tests/test_phase20_prereg.py` — FOUND
- `.planning/phases/22-.../deferred-items.md` — FOUND
- commit `36ce7fb` — FOUND
- commit `cfe8cbc` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-25*
