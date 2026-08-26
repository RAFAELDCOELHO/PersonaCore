---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 09
subsystem: privacy
tags: [differential-privacy, accountant, adjacency, cross-site-guards, ast-guards, golden-pin]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-02's scripts/mitigation_accountant.py — NEIGHBOURING, SENSITIVITY_MULTIPLIER, GOLDEN_EPSILON, GOLDEN_EPSILON_REL_TOL, and the citation of this plan's test BY SYMBOL"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-03's src/personacore/privacy/accountant.py::delta_quadrature — the independent oracle V-06 bisects, and the module docstring that is V-25's site B"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-04/22-06's src/personacore/privacy/dpsgd.py — the adjacency docstring and the torch.normal std= expression that are V-25's site C"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "scripts/mitigation_unit.py::DELTA — the one delta, resolved and never re-spelled"
provides:
  - "tests/test_phase22_accountant.py::test_golden_epsilon_from_oracle — V-06: all seven pinned epsilons re-derived by bisecting delta_quadrature ALONE, with the restriction asserted over the test's OWN AST"
  - "tests/test_phase22_accountant.py::test_golden_epsilon_would_catch_a_moved_accountant — a negative control that is NOT invariant under the tolerance widening it exists to catch"
  - "tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent — V-25 under EXACTLY the name the frozen pin cites; the pin's citation now resolves"
  - "tests/test_phase22_dpsgd_ast.py::test_adjacency_check_bites — the same helper watched refusing a swapped relation, an ABSENT relation and a 2.0x noise factor"
affects: [22-11 the four fake probes and the phase sign-off, 23 every published epsilon]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A test asserting a property of its OWN body by walking its own AST — 'derived from an independent route' made structural rather than promised in a docstring"
    - "A negative control whose perturbation is an ABSOLUTE measured quantity, paired with a ceiling on the tolerance — never a multiple of the tolerance, which is invariant under the widening the control exists to detect"
    - "Cross-site agreement read from a WINDOWED declaration ('the adjacency relation is <...>') rather than a file-wide substring scan, because every site names the rejected alternative in the sentence rejecting it"
    - "Presence at each site asserted BEFORE agreement, each separately messaged, with an ABSENCE mutation watched RED — absence must never be read as agreement"

key-files:
  created: []
  modified:
    - tests/test_phase22_accountant.py
    - tests/test_phase22_dpsgd_ast.py

key-decisions:
  - "The plan's file-wide `no \"replace-one\" substring` assertion is UNSATISFIABLE and was measured: all three sites contain it (accountant.py 1, dpsgd.py 1, the pin 5 — seven occurrences), every one inside the sentence REJECTING it. The check that survives contact reads the 60-character DECLARATION window, measured 179 characters clear of the nearest rejection sentence at both sites"
  - "The plan's `10 * GOLDEN_EPSILON_REL_TOL` negative control is STRUCTURALLY INCAPABLE of its job: `10*t*p > t*p` holds for every t > 0, so it is green at t = 1e-12 and equally green at t = 1e-3. Watched GREEN under the widening. Replaced with a FIXED 1e-9 perturbation plus a 1e-11 ceiling on the tolerance itself, watched RED"
  - "D-17's FAKE 3 row is CARRIED FORWARD CORRECTED, not transcribed: 22-06 measured the sigma=0 identity incapable of detecting noise-added-after-averaging. The corrected table is in this summary for 22-11, which owns the four fakes"
  - "The V-25 helper takes the relation and multiplier as VALUES plus two source strings, not three source strings — site A is a pin whose constants a test reads directly, which is the reader the frozen file's own prose names"
  - "requirements.mark-complete was NOT called, seventh consecutive plan: 22-10 also claims DPSGD-03 and 22-11 owns DPSGD-04's four fakes"

patterns-established:
  - "Self-AST meta-guard: a test that walks its own FunctionDef and asserts its called-name set excludes the implementation routes it claims not to use"
  - "Tolerance bracketed from BOTH sides: a ceiling that makes a fixed perturbation bite, and a floor that is the measured construction gap, so the tolerance can be neither vacuously wide nor red on correct code"

requirements-completed: []
requirements-contributed: [DPSGD-03, DPSGD-04]

# Metrics
duration: 25min
completed: 2026-08-26
---

# Phase 22 Plan 09: V-06 and V-25 — the Two Claims No Single Module Can Reach Summary

**All seven pinned golden epsilons re-derived by bisecting the quadrature oracle alone — with "alone" asserted over the test's own AST rather than promised — and the adjacency relation now enforced across the frozen pin, the accountant's prose and the noise line's actual arithmetic, under exactly the test name the pin cites by symbol.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-26T00:35Z (first read after `f8ba484`)
- **Completed:** 2026-08-26T01:00Z
- **Tasks:** 2 (+1 self-correction commit)
- **Files modified:** 2 (0 created)

## Accomplishments

- **`GOLDEN_EPSILON` demonstrably constrains the shipped accountant.** All seven rows re-derive from `delta_quadrature` alone; worst relative deviation **5.749506e-15** against `GOLDEN_EPSILON_REL_TOL = 1e-12` — **173.9× of margin**. The full comparison is in the table below.
- **"Derived from the oracle" is STRUCTURAL.** The test walks its own `FunctionDef` and asserts its called-name set contains `delta_quadrature` and excludes `epsilon_for` and `delta_closed`. Watched: adding one `epsilon_for(...)` line to the test body reddens it.
- **The pin's forward citation now resolves.** `scripts/mitigation_accountant.py` cites `tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent` by symbol; running that exact node id passes. The pin is byte-unchanged — `git diff --exit-code` exits 0.
- **The adjacency relation is enforced at three unconnected sites**, presence before agreement, and the multiplier verified in the `std=` expression's arithmetic rather than only in prose.
- **Two plan-supplied guards were measured INCAPABLE and replaced**, each with the measurement: a file-wide `replace-one` scan that reddens on correct code, and a negative control that is invariant under the mutation it exists to catch.
- **My own first draft shipped an unmeasured number and it was caught before the plan closed** — a docstring claiming "the largest z probed is ~9.1" against a measured **7.5000**. Corrected in its own commit.
- **16 mutations, 16 distinct REDs, controls GREEN, byte-identical restores** (`tests/test_phase22_accountant.py` sha256 `3745e74d…`; `src/personacore/privacy/dpsgd.py` sha256 `140f5108…`, matching 22-06's recorded value).

## Task Commits

1. **Task 1: V-06 — every pinned golden ε re-derived from the oracle alone** — `30b1191` (test)
2. **Task 2: V-25 — the three-site adjacency consistency check (D-18)** — `90e6109` (test)
3. **Self-correction: V-06's max-z claim corrected to the measured 7.5000** — `17c84fb` (fix)

## Files Created/Modified

- `tests/test_phase22_accountant.py` (+188, 825 → 1013 lines; 155 → **157 tests**) — the V-06 block: five module constants carrying their measurements, `test_golden_epsilon_from_oracle` with its three meta-guards and two non-degeneracy assertions, and `test_golden_epsilon_would_catch_a_moved_accountant`.
- `tests/test_phase22_dpsgd_ast.py` (+236/−2, 702 → **936** lines; 17 → **19 tests**) — the `sys.path` insert and the pin import at the top (`_ROOT` hoisted, not duplicated), then the V-25 block: `_normalized`, `_declared_relations`, `_module_docstring`, `_noise_std_expression`, `_assert_adjacency_consistent`, and the two tests.

## The Evidence

### V-06 — all seven rows, re-derived through the oracle only

δ = `mitigation_unit.DELTA` = 1e-5. `mu_eff = sqrt(steps) / sigma`. Bisection on `delta_quadrature` alone, bracket closed to a relative width ≤ 1e-14.

| σ | T | μ_eff | oracle-derived ε | pinned ε | relative deviation |
|---|---|---|---|---|---|
| 20.0 | 200 | 0.707106781187 | 2.9432252398013645 | 2.943225239801352 | 4.2248e-15 |
| 14.142135623730951 | 200 | 1.000000000000 | 4.3771780956812165 | 4.377178095681209 | 1.6233e-15 |
| 10.0 | 200 | 1.414213562373 | 6.572970067030326 | 6.572970067030306 | 2.9728e-15 |
| 5.0 | 200 | 2.828427124746 | 15.456155822609276 | 15.456155822609244 | 2.0687e-15 |
| 2.0 | 200 | 7.071067811865 | 54.37663901498536 | 54.376639014985045 | **5.7495e-15** |
| 1.0 | 1 | 1.000000000000 | 4.3771780956812165 | 4.377178095681209 | 1.6233e-15 |
| 8.0 | 64 | 1.000000000000 | 4.3771780956812165 | 4.377178095681209 | 1.6233e-15 |

**Worst 5.749506e-15 against a tolerance of 1e-12 — 173.93× of margin.** Every row deviates (min 1.6233e-15), which is the non-degeneracy half: a bitwise match on all seven would mean the pin had been regenerated from a float64 route rather than from 60-decimal-place ground truth.

Bisection budget, measured: **46–47 halvings** and **2–6 doublings** per row (caps 200 and 60), final bracket relative width 6.49e-15 … 9.66e-15, **356 oracle calls** total, **zero refusals**. Largest `z = eps/mu − mu/2` probed is **7.5000** (at ε = 8.0, μ = 1.0), against the committed `ZERO_BOUNDARIES["delta_quadrature_zero_z"] = 38.372164249`.

### V-25 — the three sites, measured

| Site | What it states | Measured |
|---|---|---|
| A `scripts/mitigation_accountant.py` | `NEIGHBOURING` / `SENSITIVITY_MULTIPLIER` | `'add/remove one fact'` (19 chars) / `1.0` |
| B `src/personacore/privacy/accountant.py` | module docstring, 5,743 chars | one declaration, at normalized offset 1806 |
| C `src/personacore/privacy/dpsgd.py` | module docstring, 6,829 chars | one declaration, at normalized offset 2480 |
| C (code) | `torch.normal(..., std=…)` | `BinOp(Mult)` over `self.sigma`, `self.C`; **zero** numeric operands |

Both declarations read `'add/remove one fact , and its sensitivity multiplier is 1.0 '` after normalization. The word `replace` first appears **239 characters** into each declaration's tail — inside the sentence rejecting it — so the 60-character window sits **179 characters clear** at both sites.

## Guards Watched Failing

No guard was believed on the strength of being green. Sixteen mutations; every one produced a distinct message. Source-file mutations were written to the work-tree path and restored in a `finally`, with `sha256` asserting the restore was byte-identical.

### V-06 — 6 mutations, 6 distinct REDs

| # | Mutation | Result |
|---|---|---|
| 0 | control | **GREEN** (both tests) |
| 1 | `GOLDEN_EPSILON_REL_TOL` widened to 1e-3 | **RED** — the ceiling assertion |
| 2 | `delta_quadrature` perturbed ×(1+1e-8) | **RED** — row 1 re-derives 2.9432252414729874 |
| 3 | `GOLDEN_EPSILON` truncated to six rows | **RED** — meta-guard 1 |
| 4 | one `epsilon_for(...)` line added to the test's own body | **RED** — meta-guard 2, the self-AST walk |
| 5 | bisection capped at 1 halving | **RED** — meta-guard 3, bracket width 3.333e-01 |
| 6 | the pin regenerated FROM this float64 route (the photograph, arriving through the oracle) | **RED** — the non-degeneracy assertion |

**Mutation 1 is the load-bearing one, because it is where the plan's own control fails.** Under the same widened tolerance, the control the plan specifies — perturb by `10 * GOLDEN_EPSILON_REL_TOL` — measured **GREEN**, and equally green at t = 1e-12. It is invariant under exactly the mutation it exists to catch. The shipped control reddens.

### V-25 — 10 mutations, 10 distinct REDs

Three are committed inside `test_adjacency_check_bites` (each replacement asserted to have applied — `real.count(target) == 1` — so a no-op mutation cannot make the RED test green over unmutated source); seven were run as probes.

| # | Mutation | Guard reddened |
|---|---|---|
| 0 | control, real bytes | **GREEN** |
| 1 | dpsgd relation swapped to replace-one *(committed)* | agreement — "does not begin with the pinned" |
| 2 | dpsgd relation ABSENT *(committed)* | **presence** — "contains no '…' statement" |
| 3 | `std=2.0 * self.sigma * self.C` *(committed)* | the `std=` AST arm |
| 4 | the PIN moved to replace-one | agreement, at site B first |
| 5 | `SENSITIVITY_MULTIPLIER` → 2.0 | assertion 4 |
| 6 | `NEIGHBOURING` degraded to `""` | the `len > 10` meta-guard |
| 7 | dpsgd source emptied | the empty-source meta-guard |
| 8 | dpsgd docstring removed | the docstring meta-guard |
| 9 | `torch.normal` renamed away | "the noise call is gone" |
| 10 | **the real work-tree `dpsgd.py`** given a `2.0 *` factor | the live test, via the same helper |

Mutation 10 is the one that proves the live test and the RED test are the same code: the real file was mutated on disk, the committed node id ran, and it reddened with the identical message the text-fed probe produces. `dpsgd.py` sha256 `140f51082ab188a0…` before and after.

## D-17's FAKE 3 Row — Carried Forward CORRECTED, Not Transcribed

Plan 22-11 owns DPSGD-04's four fake probes. **It must not inherit D-17's table as written.** 22-06 measured the entry false and this plan does not re-transcribe it:

| fake | D-17 says it is detected by | MEASURED |
|---|---|---|
| clip the averaged gradient | D-05 axes 3 + 4 | holds — 22-06 mutation 2, RED |
| noise scaled to wrong sensitivity | D-04 count refusal; D-16 runtime | holds — 22-04 mutation 3, RED; and now V-25's `std=` arm for the DEFINITIONAL half |
| **noise added after averaging** | ~~D-06's CPU σ=0 identity~~ | **FALSE.** 22-06 applied the mutation verbatim and the whole suite stayed **GREEN (35 passed)**: at σ = 0 the drawn values are exactly zero, so `(sum + 0)/N` and `(sum/N) + 0` are the same number and the divide's position is unobservable. The detector that works is `test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST` at **σ > 0**, over the noise magnitude — watched RED at N = 4 |
| RNG reused across steps | D-16 generator-state check | holds — 22-04 mutation 2, RED |

22-09 did not build the fake probes (they are 22-11's Task 1), so nothing here was derived from the table. The row is corrected in place so the next reader of this phase's summaries does not pick it up.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's `no "replace-one" substring` assertion reddens on correct code at all three sites**

- **Found during:** Task 2
- **Issue:** The plan directs: *"Also assert no site contains the string `"replace-one"` or `"replace one"` while `SENSITIVITY_MULTIPLIER` is `1.0`"*, on the ground that this pair is PITFALLS P3's warning sign verbatim. Measured, **all three sites contain it**: `grep -c "replace-one\|replace one"` returns **1** for `accountant.py`, **1** for `dpsgd.py` and **5** for the pin — seven occurrences, every one inside the sentence that REJECTS replace-one and states the 2× stake. Applied literally, the assertion is RED on the shipped tree and would have had to be deleted to ship, taking P3's warning sign with it.
- **Fix:** The check reads the relation each site **ADOPTS**, not every relation it names: the 60-character window after the normalized marker `the adjacency relation is`. Measured, the word `replace` first appears 239 characters into that tail at both sites, so the window sits **179 characters clear**. The assertion is still P3's pair — *a declared replace-one while the multiplier is 1.0* — and it now bites where it should: mutation 1 (declaration swapped) is RED, and the correct tree is GREEN.
- **Files modified:** `tests/test_phase22_dpsgd_ast.py`
- **Verification:** the three grep counts above; mutations 1 and 4 RED; control GREEN.
- **Committed in:** `90e6109`

**2. [Rule 1 - Bug] The plan's negative control is invariant under the mutation it exists to detect**

- **Found during:** Task 1
- **Issue:** The plan specifies: *"Take one pinned row, perturb the target ε by `10 * GOLDEN_EPSILON_REL_TOL` relative, and assert the comparison the main test performs would FAIL on that value. Without it, a tolerance accidentally widened to 1e-3 would leave the test green while constraining nothing."* The stated purpose is precisely what the specified form cannot serve: the assertion reduces to `10*t*p > t*p`, which is **true for every t > 0**. Watched — at `t = 1e-3` the plan's form is **GREEN**, exactly as at `t = 1e-12`. A control that scales with the tolerance can never detect the tolerance being widened.
- **Fix:** Two assertions bracketing the tolerance from both sides. (i) A **fixed** relative perturbation of `1e-9` — ~174,000× the measured 5.749506e-15 oracle gap, and the smallest scale a real implementation error plausibly reaches — asserted to exceed the tolerance. (ii) `_GOLDEN_REL_TOL_CEILING = 1e-11`, so the fixed perturbation is guaranteed to bite; and (iii) the other side, `_V06_MEASURED_ORACLE_GAP <= rel_tol`, so a tolerance tightened below the float64-vs-60-dps construction gap is caught too rather than silently reddening V-06 on correct code.
- **Files modified:** `tests/test_phase22_accountant.py`
- **Verification:** mutation 1 — the shipped control RED at `t = 1e-3`, the plan's form GREEN at both `t = 1e-3` and `t = 1e-12`, printed side by side.
- **Committed in:** `30b1191`

**3. [Rule 2 - Missing critical functionality] A third RED mutation: the relation ABSENT**

- **Found during:** Task 2
- **Issue:** The plan names two mutations for `test_adjacency_check_bites` — a relation swap and a `2.0 *` factor. Neither exercises the ordering the plan itself calls non-negotiable (*"Presence at every site FIRST … absent must never count as agreement"*), so the presence assertions would have shipped unwatched. T-22-44 is that exact threat.
- **Fix:** A third committed mutation replaces the declaration with an unrelated sentence, and the presence assertion is observed raising with its own message. All three replacements are additionally asserted to have applied (`real.count(target) == 1`) before being fed in — a mutation that silently matched nothing would leave the RED test green over unmutated source.
- **Files modified:** `tests/test_phase22_dpsgd_ast.py`
- **Verification:** mutation 2 RED, `match="no '.*' statement"`.
- **Committed in:** `90e6109`

**4. [Rule 2 - Missing critical functionality] V-06's non-degeneracy, in both directions**

- **Found during:** Task 1
- **Issue:** The plan's three meta-guards cover a truncated pin, a forbidden callee and a non-converged bracket. None catches the failure D-13 names most explicitly arriving through the *oracle*: `GOLDEN_EPSILON` regenerated from a float64 quadrature run rather than from 60-dps ground truth. Every row would then match bitwise and V-06 would be green over a photograph taken with a different camera.
- **Fix:** `worst > 0.0` (measured: every row deviates, min 1.6233e-15) plus `worst <= 10 × the recorded measurement`, so the file's stated margin cannot go stale unnoticed.
- **Files modified:** `tests/test_phase22_accountant.py`
- **Verification:** mutation 6 — the pin replaced by this route's own output — RED.
- **Committed in:** `30b1191`

**5. [Rule 1 - Bug] My own first draft shipped a number nobody had measured**

- **Found during:** SUMMARY preparation
- **Issue:** `test_golden_epsilon_from_oracle`'s docstring justified not catching a `delta_quadrature` refusal with *"the largest z probed is ~9.1, against the ~38.37 underflow boundary"*. I had estimated 9.1 by hand from the largest `hi` in the doubling walk and never measured it. Measured over the 356 oracle calls the test makes, the maximum `z = eps/mu − mu/2` is **7.5000**, at ε = 8.0, μ = 1.0. The conclusion is unchanged and the margin is larger than claimed — but an unmeasured number in the file whose whole discipline is that numbers carry their denominators is the defect, not the size of the error.
- **Fix:** The measured 7.5000 with its (ε, μ), the call count, and the committed `ZERO_BOUNDARIES["delta_quadrature_zero_z"] = 38.372164249` cited by name instead of the rounded `~38.37`.
- **Files modified:** `tests/test_phase22_accountant.py`
- **Verification:** the spy probe printing `oracle calls: 356; MAX z probed = 7.5000 at eps=8.0, mu=1.0`.
- **Committed in:** `17c84fb`

**6. [Rule 1 - Bug] `gsd-sdk` mutation-handler defects, hand-repaired before commit**

- **Found during:** state updates
- See *Tooling Corruption Encountered* below — nineteenth consecutive session.

### Deliberate departures from the plan text

- **The V-25 helper's signature is `(relation, multiplier, accountant_src, dpsgd_src)`, not "three source strings".** Site A is a pin whose *constants* a test reads — the reader the frozen file's own `SENSITIVITY_MULTIPLIER_REASON` names ("It reads THIS constant"). Parsing the pin's source to recover a literal it already exports would add a route with nothing to check. The three sites are still all read; only site A's spelling differs, and the RED probes mutate site C, which is where both named mutations live.
- **The `torch.normal` locator matches on the callee name `normal`, not on the dotted path `torch.normal`.** `_forbidden_calls_reachable_from` in the same file matches `func.id` or `func.attr` for the identical reason: a dotted-path match is blind to `from torch import normal` and to any aliasing. The meta-guard (`std_node is not None`) is what makes the looser locator safe.
- **Presence and agreement are asserted over the module DOCSTRING** (`ast.get_docstring`), not over raw file text. A relation stated in a comment or a string literal somewhere in the body would satisfy a text scan; the docstring is where a module states its definitions, and it is what the plan's own read-first list names.
- **Test-count acceptance criteria ("at least 23 passed" / "at least 17 passed") were computed for smaller files.** The accountant file starts at 155 and ends at **157**; the AST file starts at 17 and ends at **19**. Both criteria are trivially met. Recorded so no reader mistakes the totals for scope creep — this plan adds exactly **4** tests.
- **`make lint` cannot exit 0 on this box** (seventh confirmation, unchanged since 22-01 deviation 3). `.venv/bin/ruff check . && .venv/bin/ruff format --check .` is clean over 202 files. The Makefile is untouched — out of scope.
- **A third commit exists for a docstring correction.** Deviation 5 was found after Task 1 was already committed; correcting it inside the metadata commit would have buried a source fix in a docs commit.

---

**Total deviations:** 6 auto-fixed (2 plan-supplied guards measured incapable, 2 missing guards added, 1 self-inflicted unmeasured number, 1 tooling corruption), 6 deliberate departures.
**Impact on plan:** every correction makes a guard bite where the specified version could not; none weakens one. No scope creep — `pyproject.toml`, all three `scripts/mitigation_*.py` and both `src/personacore/privacy/` modules are byte-unchanged (`git diff --exit-code` exits 0), which is T-22-SC's own criterion.

## Tooling Corruption Encountered

Nineteenth consecutive session. Every `gsd-sdk` mutation call was followed by `git diff` on the planning files and hand-repaired before the metadata commit.

| Handler | Defect observed | Repair |
|---|---|---|
| `state.advance-plan` | rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — identical to 22-01 … 22-08 | restored by hand |
| `state.add-decision --summary` | prefixed every entry `- [Phase ?]:` | prefix corrected to `[Phase 22]`; `grep -c "Phase ?"` → **0** |
| `state.update-progress` | `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that has one | harmless; `advance-plan` had already set the block |
| `roadmap.update-plan-progress 22` | status cell written as `In Progress\|  \|` — no space before the pipe, empty date cell | corrected to `\| 9/11 \| In Progress \| - \|` |
| `state.record-metric --flag` / `state.record-session --stopped-at` | **correct** under the `--flag` form | — |

**The SUMMARY-before-handler ordering held for the fourth time.** This file was written before `roadmap.update-plan-progress` ran, and the handler — which counts SUMMARY files on disk — produced the right count and flipped the `22-09-PLAN.md` checkbox, exactly as in 22-06/07/08. It is a usable workaround, not a fix.

## Issues Encountered

- **Two ruff `E501` wraps**, both in f-string assertion messages; no assertion text or semantics changed.
- **`_ROOT` was hoisted rather than duplicated** in `tests/test_phase22_dpsgd_ast.py`. The `sys.path` insert needs it at import time and it was defined at the file's live-half boundary; moving the one line up is a smaller and less rottable diff than a second copy of the same expression.
- **The AST test module now imports `mitigation_accountant`**, which executes the pin's eight module-scope `_prove` guards at collection time. That is a feature — a broken pin now fails this file at import rather than inside an assertion — and it keeps the module's "no torch, no network" property, since the pin imports nothing at all.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_accountant.py -q` | **157 passed** (was 155) |
| `.venv/bin/python -m pytest tests/test_phase22_dpsgd_ast.py -q` | **19 passed** (was 17) |
| `.venv/bin/python -m pytest "tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent" -q` | **1 passed** — the frozen pin's cited node id resolves |
| V-06, seven rows, worst relative deviation | **5.749506e-15** against `GOLDEN_EPSILON_REL_TOL = 1e-12` (173.93× margin) |
| V-06 bisection | 46–47 halvings, 2–6 doublings, 356 oracle calls, **0 refusals**, max z **7.5000** |
| V-06 non-degeneracy | all 7 rows deviate (min 1.6233e-15) — not a photograph |
| `replace-one` occurrences per site | accountant.py **1**, dpsgd.py **1**, pin **5** — the plan's file-wide assertion is unsatisfiable |
| adjacency declaration window vs nearest rejection | 60 chars used, `replace` at offset **239** — **179 chars clear**, both sites |
| `std=` expression, shipped `dpsgd.py` | `BinOp(Mult)` over `self.sigma` / `self.C`, **0** numeric operands |
| V-06 mutation probes | **6 RED / 6**, control GREEN, sha256-identical restore (`3745e74d…`) |
| V-25 mutation probes | **10 RED / 10**, control GREEN, sha256-identical restore (`140f5108…`) |
| the plan's `10 * REL_TOL` control at t = 1e-3 | **GREEN** — invariant under the widening it exists to catch |
| `git diff --exit-code -- scripts/mitigation_{gate,unit,accountant}.py pyproject.toml src/personacore/privacy/{dpsgd,accountant}.py` | exit 0 — byte-unchanged |
| Full suite `.venv/bin/python -m pytest -q` | **1259 passed, 1 skipped** in 214.80 s (baseline 1255/1 + 4 new) |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, **202 files** formatted |

## Known Stubs

None. Every constant added is consumed by a committed assertion, both new helpers are exercised on real bytes and on mutated text, and no placeholder was left for a later plan. V-06 and V-25 are complete; what neither claims is DPSGD-04's four fake probes, which are 22-11's Task 1 by design.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no schema, and no new file-access pattern — the only reads are `pathlib.read_text` on two already-read committed source paths. Nothing was installed.

Threat register dispositions, each mitigated as planned:

- **T-22-43** (an ε published under replace-one while the code implements add/remove-one) — the three-site read, presence first, agreement second, and the multiplier verified in the `std=` AST expression. Watched RED on a swapped declaration at site C (mutation 1), on a moved pin (mutation 4), and on a `2.0 *` factor in the real file (mutation 10).
- **T-22-44** (a check that passes because the relation is ABSENT at one site) — presence asserted before agreement with its own message per site, and the absence mutation is one of the three committed RED probes (mutation 2). This is the threat the plan named and did not supply a mutation for.
- **T-22-45** (`GOLDEN_EPSILON` becoming a photograph of `accountant.py`) — the forbidden-callee set asserted over the test's OWN AST (mutation 4, RED), the perturbation control rebuilt so it is not invariant under a widened tolerance (mutation 1, RED, with the plan's version measured GREEN), and the photograph-via-the-oracle direction caught too (mutation 6, RED).
- **T-22-46** (a `2.0 *` factor slipped into the noise `std`) — refused by the two-operand `Mult` + no-`Constant` rule; watched RED both on mutated text and on the real work-tree file.
- **T-22-47** (the D-18 constants shipped with nothing enforcing them) — closed here rather than deferred. The pin's citation resolves to a passing node id; before this plan it named a test that did not exist.
- **T-22-SC** (package installs) — accepted; nothing installed, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-11 must use the CORRECTED D-17 table above.** FAKE 3's assigned detector (the σ=0 identity) was measured incapable by 22-06; the detector that bites is `test_noise_is_scaled_by_the_lot_size_because_the_divide_comes_LAST` at σ > 0. Running FAKE 3's positive control against the identity would produce a GREEN "watched" result and certify a guard that cannot see the fake.
- **V-25's helper is available for 22-11's probes and takes TEXT**, exactly like `_assert_no_forbidden_between_noise_and_step`: `_assert_adjacency_consistent(relation=…, multiplier=…, accountant_src=…, dpsgd_src=…)`. A fake probe that alters the noise line's arithmetic reddens it through the same code the live test runs.
- **The pin's citation is now load-bearing in the other direction.** `tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent` may not be renamed or moved: `scripts/mitigation_accountant.py` cites it by symbol and freezes at the first tracked `results/phase23_*` artifact, after which a correction is only possible as a dated continuation via `scripts/_addendum.py`.
- **`GOLDEN_EPSILON_REL_TOL` now carries a ceiling of 1e-11 and a floor of 5.749506e-15**, both asserted. A future plan tightening or widening it past either bound reddens `test_golden_epsilon_would_catch_a_moved_accountant` with the reason in the message — it should re-measure rather than re-type.
- **Two guard-design facts worth not re-deriving:** (i) a negative control whose perturbation is a multiple of the tolerance is invariant under a widened tolerance and proves nothing — use an absolute measured quantity plus a ceiling; (ii) a cross-site prose check must read the statement each site ADOPTS, because a well-argued module names the alternative it rejects and a file-wide substring scan cannot tell the two apart.

## Self-Check: PASSED

- `tests/test_phase22_accountant.py` — FOUND
- `tests/test_phase22_dpsgd_ast.py` — FOUND
- `.planning/phases/22-.../22-09-SUMMARY.md` — FOUND
- commit `30b1191` — FOUND
- commit `90e6109` — FOUND
- commit `17c84fb` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-26*
