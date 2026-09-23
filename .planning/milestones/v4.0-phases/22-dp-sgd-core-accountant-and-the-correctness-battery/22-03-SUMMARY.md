---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 03
subsystem: privacy
tags: [differential-privacy, accountant, numerical-methods, quadrature, ast-guards, stdlib-only]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-01's src/personacore/privacy/ subpackage and tests/fixtures/phase22_reference.py — the 60-dps ground truth this plan is judged against"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-02's scripts/mitigation_accountant.py::NEIGHBOURING / ::SENSITIVITY_MULTIPLIER — the adjacency wording this module's docstring must match verbatim"
provides:
  - "src/personacore/privacy/accountant.py::delta_closed — Balle-Wang Thm 8, log-space second term, three separately-messaged refusals"
  - "src/personacore/privacy/accountant.py::delta_quadrature — the independent exp-only oracle, derived integration range, rigorous Mills truncation proof, three non-vacuity refusals"
  - "the accountant docstring's adjacency paragraph — one of the three sites V-25's cross-site consistency test reads"
  - "tests/test_phase22_accountant.py — V-01, V-02, V-04, V-05 and V-09, 43 tests"
affects: [22-05 epsilon_for/sigma_for, 22-09 V-06/V-25 and the fake probes, 23 frontier sweep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A per-row RELATIVE tolerance derived from the committed truth STRING's own significant-digit width, so a reference table's quantization is never charged to the implementation"
    - "A second oracle whose function body is AST-verified to share no transcendental with the first beyond exp itself"
    - "A domain refusal checked BEFORE the expensive loop, so the loop's own arithmetic error can never pre-empt the stated reason"
    - "Guard mutation probes that patch the test module's _ROOT/_ACCOUNTANT_PATH at a temp copy — the work tree is never written to, so byte-identical restore is structural rather than remembered"

key-files:
  created:
    - src/personacore/privacy/accountant.py
    - tests/test_phase22_accountant.py
  modified:
    - .planning/phases/22-dp-sgd-core-accountant-and-the-correctness-battery/deferred-items.md

key-decisions:
  - "V-01's tolerance is PER ROW: 1e-12 (the implementation bound) plus the committed truth string's own half-ulp. The plan's flat 1e-12 is unsatisfiable — DELTA_FRONTIER's truths are 11-, 12- and 13-digit strings, and the 11-digit row's residual is the fixture's rounding rather than the accountant's error"
  - "delta_quadrature's condition 1 was widened to the negative-z half and moved before the Simpson loop — measured, mu=76 raised a bare OverflowError from the scaled integrand with no refusal reached"
  - "delta_closed's condition-3 message states the CANCELLATION reason (a difference of two terms whose ratio is a/b), not the quadrature's truncation-degeneracy reason, which does not apply to a function that has no truncation test"
  - "No sys.path insert for scripts/ — this plan reads no pin, and a later plan adds the wiring in the same commit as its first consumer"
  - "requirements.mark-complete was NOT called: DPSGD-03 additionally needs the inverse solve (22-05) and V-03/V-06/V-07/V-08"

patterns-established:
  - "Digit-width-aware reference tolerance: _sig_digits(truth_str) reads the width off the committed string, so each row's tolerance carries its own denominator"
  - "AST scoping of a per-function call set: `math.exp/isfinite/sqrt` for delta_quadrature against `math.erfc/exp/isfinite/log` for delta_closed, asserted structurally rather than by grepping the file"

requirements-completed: []
requirements-contributed: [DPSGD-03]

# Metrics
duration: 35min
completed: 2026-08-25
---

# Phase 22 Plan 03: The Two Delta Oracles Summary

**Two oracles of genuinely different mathematics — an `erfc` closed form and an `exp`-only derived-range Simpson quadrature, AST-proven to share no transcendental beyond `exp` — each refusing the exact-zero corner where RESEARCH F1 measured the cross-check passing on `0.0 == 0.0` against a true `1.24028351258e-352`.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-08-25T21:35Z (first read after `5579d53`)
- **Completed:** 2026-08-25T22:10Z
- **Tasks:** 3
- **Files created:** 2 (1 modified)

## Accomplishments

- `delta_closed` reproduces Balle-Wang Theorem 8 on all **11** float64-representable frontier rows, worst relative deviation **1.84e-12** — and that row's committed truth carries only 11 significant digits, so most of that budget is the reference string's own quantization. Worst deviation on a full 13-digit row: **9.03e-13**.
- `delta_quadrature` is a **different integral method, not a second spelling**: its body's attribute-call set is `{math.exp, math.isfinite, math.sqrt}` against `delta_closed`'s `{math.erfc, math.exp, math.isfinite, math.log}`, asserted by AST walk rather than by grep. It reproduces the same 11 rows to **1.0e-12** worst.
- **The ε=8, μ=0.5 corner is fixed and the fix is proven by its own negative control.** The derived range lands at **3.60e-13** (7.5× inside the committed `WORST_RELATIVE_ERROR = 2.7e-12`); the fixed `[-14, 14]` trapezoid, computed inline in the test, returns exactly `0.0` at relative error **1.00e+00**.
- **RESEARCH F1 reproduced before it was fixed**: without the refusal, the cross-check `abs(a-b) <= 1e-9*abs(b)` returns `True` on **3 of 4** measured rows against true deltas of 1.24e-352, 7.12e-549 and 8.18e-2177. All three now `raise ValueError`.
- **All three non-vacuity conditions fire separately with three distinct messages**, and condition 3's independence from condition 2 was *measured*, not argued: in the band `38.372164249 < z < 38.6005` the prefactor is representable (condition 1 silent) and `trunc/integral` is ~3.2e-15 (condition 2 silent), yet the product underflows to exactly `0.0`.
- **V-09 is live in both halves and both were watched failing** — 7 mutations, 7 REDs, control GREEN. The AST-invisible `__import__('torch')` mutation is **static-GREEN and transitive-RED**, which is the evidence the out-of-process half is not redundant.
- `pyproject.toml`, `scripts/mitigation_gate.py`, `scripts/mitigation_unit.py` and `scripts/mitigation_accountant.py` are all byte-unchanged (`git diff --exit-code` exits 0). RPT-03's zero-new-dependency streak holds.

## Task Commits

1. **Task 1: `delta_closed` — Balle-Wang Thm 8 with the symmetric silent-zero refusal** — `3321421` (feat)
2. **Task 2: `delta_quadrature` — the exp-only oracle with a derived range** — `9009561` (feat)
3. **Task 3: V-09 — math-only imports, static and transitive, plus the D-15 register** — `491002d` (test)

## Files Created/Modified

- `src/personacore/privacy/accountant.py` (new, 337 lines) — `import math` and nothing else. Module docstring in `perplexity.py`'s register: DPSGD-03 on line 1, the "unlike an RDP accountant" contrast with F5's SUPERSEDED note, and a four-bullet invariants block naming `tests/test_phase22_accountant.py` (σ is the noise multiplier / the adjacency relation / the shared silent-zero domain limit / `raise` never `assert` never `_prove`). Then `delta_closed` and `delta_quadrature`, six `raise ValueError` sites, zero `assert`, zero `_prove`.
- `tests/test_phase22_accountant.py` (new, 373 lines) — 43 tests: V-01 (11 parametrized rows + a non-empty meta-guard), V-05's closed half (3 rows), F2's high-ε survival, 7 domain refusals, V-02 (11 rows, zero refused before comparison), V-04 with its fixed-range negative control, V-05's three conditions with pairwise-distinct messages, 5 bad-grid refusals, and Task 3's two structural guards.
- `.planning/phases/22-.../deferred-items.md` (+30) — the residual negative-`z` `OverflowError` band, measured, with the reason it is not tested here.

## Decisions Made

- **V-01's tolerance is per row, and the rule reads the width off the committed string.** `_sig_digits("3.7194507268e-91")` is 11, `_sig_digits("1.048659178913e-57")` is 13, so the tolerances are 5.1e-11 and 1.5e-12 respectively. A flat number either reddens a correct answer or hides a real error two decades wide, and the meta-guard `1e-12 < tol <= 1e-10` keeps the rule from ever widening into vacuity.
- **Condition 1 is checked before the Simpson loop.** This is not an optimization: for `|z| > 38.6005` the loop's own `math.exp` raises `OverflowError` first, and the domain limit would then surface as an unrelated arithmetic error instead of the stated refusal the docstring promises.
- **`delta_closed`'s condition-3 message states the reason that is actually true of it.** The plan specified the quadrature's wording ("a truncation-relative test degenerates to `0.0 > 0.0`"), but `delta_closed` has no truncation test. Its real independence argument is cancellation: the two terms' ratio is exactly `a/b` in exact arithmetic, so the subtraction loses about `mu**2/eps` of the leading digits and can round to `<= 0.0` while `erfc(a)` is strictly positive. The message says that, and also points at the quadrature's version as the same shape.
- **No `sys.path.insert(0, str(_ROOT / "scripts"))`.** The plan asked for it "for later plans' pin read"; this plan reads no pin, and scaffolding for an unwritten consumer is the thing plan 22-01 already declined to pre-add for `_ALLOWED_CLASS_CONSTANTS`. Plan 22-09 adds it in the same commit as its first `mitigation_accountant` import.
- **`requirements.mark-complete` was NOT called**, third consecutive plan for the same reason. DPSGD-03 requires an accountant "agreeing with two oracles of different mathematics" AND the (ε, δ) accountant itself — `epsilon_for` / `sigma_for` land in plan 22-05, and V-03/V-06/V-07/V-08 are unbuilt. Two δ oracles are half of DPSGD-03; checking the box now would publish a completion nothing has evidenced. It stays `- [ ]`.

## Guards Watched Failing

Neither structural guard was believed on the strength of being green. Both were run **against the committed test functions** with `_ROOT` / `_ACCOUNTANT_PATH` patched at a mutated copy in a `TemporaryDirectory` — the work tree is never written to, so byte-identical restore is structural rather than remembered, and the probe asserted the work-tree file unchanged at the end.

| # | Mutation | `imports_math_only` | `no_assert_and_no_prove` | Caught by |
|---|---|---|---|---|
| 0 | control (unmutated) | GREEN | GREEN | — |
| 1 | `import numpy` added | **RED** | GREEN | hard-equality import set (`Offenders: ['numpy']`) |
| 2 | `from mpmath import mp` added | **RED** | GREEN | hard-equality import set (`Offenders: ['mpmath']`) |
| 3 | every import removed | **RED** | GREEN | collapsed-walk meta-guard |
| 4 | `__import__('torch')` (AST-invisible) | **RED** | GREEN | **out-of-process transitive probe — the static half is GREEN here** |
| 5 | an `assert` replaces a `raise` | GREEN | **RED** | `asserts == []` (`lines [231]`) |
| 6 | a `_prove(...)` call added | RED | **RED** | `proves == []` (`lines [64]`) |
| 7 | every `raise` removed | GREEN | **RED** | `ast.Raise` presence meta-guard (`0 raise statements`) |

**7 mutations, 7 distinct REDs, control GREEN on both.** Row 4 is the load-bearing one: it is the only evidence that the out-of-process half catches something the single-file walk structurally cannot, and it is exactly the case the plan named.

Separately, **RESEARCH F1 was reproduced against unguarded copies of both oracles** before accepting the refusals as real:

| ε | μ | z | unguarded closed | unguarded oracle | `abs(a-b) <= 1e-9*abs(b)` | TRUE δ |
|---|---|---|---|---|---|---|
| 2.0 | 0.1 | 19.950 | 3.71945e-91 | 3.71945e-91 | True (**correct**) | `3.7194507268e-91` |
| 2.0 | 0.05 | 39.975 | 0.0 | 0.0 | True — **VACUOUS** | `1.24028351258e-352` |
| 1.0 | 0.02 | 49.990 | 0.0 | 0.0 | True — **VACUOUS** | `7.12037376927e-549` |
| 5.0 | 0.05 | 99.975 | 0.0 | 0.0 | True — **VACUOUS** | `8.18353277275e-2177` |

All three vacuous rows now raise `ValueError`, and `test_two_oracles_agree` asserts `a != 0.0` and `b != 0.0` — each with its own message — before the comparison is reached.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] V-01's flat `1e-12` tolerance is unsatisfiable against the committed reference strings**

- **Found during:** Task 1
- **Issue:** The plan specifies `assert abs(got - truth) <= 1e-12 * truth` for every representable frontier row, and its `Returns:` text claims "worst measured relative error 7.9e-13 at ε=2, μ=0.1" (inherited from `22-RESEARCH.md`'s own sentence). **Measured, that row's deviation is 1.84e-12 and the test is RED on a correct implementation.** The cause is the fixture, not the accountant: `DELTA_FRONTIER`'s truths are decimal strings of **varying** width — nine carry 13 significant digits, `1.24028351258e-352` carries 12, and `3.7194507268e-91` carries **11**. `delta_closed` returns `3.719450726793e-91`, which rounds to exactly the committed 11-digit `3.7194507268e-91`; the residual is the reference string's own half-ulp (~5e-11 relative), fifty times the implementation bound.
- **Fix:** The tolerance is computed **per row** as `1e-12 + 0.5 * 10**(1 - _sig_digits(truth_str))`, where `_sig_digits` reads the width off the committed string. Each row's tolerance therefore carries its own denominator: 1.5e-12 for a 13-digit truth, 5.1e-11 for the 11-digit one. Two meta-guards keep this from becoming a loosening: `1e-12 < tol <= 1e-10` inside every row, and a separate test asserting the parametrization is exactly 11 rows whose complement is exactly `VACUOUS_AGREEMENT_ROW`. The module's `Returns:` records the measured 1.84e-12 **with its decomposition**, rather than restating 7.9e-13.
- **Files modified:** `src/personacore/privacy/accountant.py`, `tests/test_phase22_accountant.py`
- **Verification:** measured deviations across all 11 rows — 3.46e-13, 5.54e-14, 5.54e-14, 3.70e-14, 9.03e-13, 3.20e-13, 2.16e-13, 7.28e-15, 1.22e-13, 5.11e-15, **1.84e-12**. Max over 13-digit rows: 9.03e-13, comfortably under that band's 1.5e-12.
- **Committed in:** `3321421`

**2. [Rule 2 - Missing critical functionality] `delta_quadrature` raised a bare `OverflowError` for `z < -37.677`, before any refusal could fire**

- **Found during:** Task 2
- **Issue:** The substituted form separates a tiny `phi(z)` prefactor from a large scaled integral. For `z < 0` that integral's own `exp(-z*u - u*u/2)` peaks at `u = -z` with value `exp(z*z/2)`, which overflows once `z*z/2 > 709.782712893384`. The plan's condition 1 (`ez <= -745.0`) corresponds to `|z| > 38.6005`, so the loop's arithmetic error fires **first** for every `z < -38.6005` and the stated domain refusal is never reached. Measured: `mu=76.0, eps=0.001` (z = −38.0) → `OverflowError: math range error`; `mu=1088.0` (z = −544.0) likewise. `mu=60.0` (z = −30.0) returns normally at `I = 6.78e+195`.
- **Fix:** Two changes, neither adding a fourth condition. (a) Condition 1 is evaluated **before** the 20,001-node loop, which converts every `|z| > 38.6005` case into the stated refusal. (b) Its predicate is widened to `ez <= -745.0 or (z < 0.0 and ez < -_EXP_OVERFLOW_ARG)` with `_EXP_OVERFLOW_ARG = 709.782712893384` — the same bisected constant the fixture already commits as `ZERO_BOUNDARIES["exp_overflow_eps"]`. It remains **one condition with one message**, so the "three distinct messages" shape plan 22-09 reads is unchanged. The clause fires only for `z < 0`, so nothing on the positive side moves and `ZERO_BOUNDARIES["delta_quadrature_zero_z"] = 38.372164249` still describes the shipped behaviour.
- **Files modified:** `src/personacore/privacy/accountant.py`
- **Verification:** `delta_quadrature(0.001, 76.0)`, `(0.001, 100.0)` and `(0.001, 1088.0)` all now raise `ValueError` naming the domain limit; `(0.001, 60.0)` still returns. The 11-row frontier and all three V-05 conditions are unaffected (43/43 green).
- **Committed in:** `9009561`

**3. [Rule 1 - Bug] `delta_closed`'s condition-3 message would have stated a reason that is not true of `delta_closed`**

- **Found during:** Task 1
- **Issue:** The plan requires condition 3's message to state that it is not implied by condition 2 "because a truncation-relative test degenerates to `0.0 > 0.0` = False". That reason is the **quadrature's** — `delta_closed` has no truncation test at all, so transcribing it would have shipped a refusal explaining itself with a mechanism it does not contain.
- **Fix:** The intent (condition 3 is an independent backstop) is kept and the reason is the one that actually holds for a closed form: refusal 2 only proves the *first* term survived, while the returned value is a **difference** whose two terms have ratio exactly `a/b`, so cancellation of roughly `mu**2/eps` of the leading digits can round the result to `<= 0.0` with both terms individually representable. An inline comment names the quadrature's version as the same shape at the other site, so the connection the plan wanted is recorded without the false claim.
- **Files modified:** `src/personacore/privacy/accountant.py`
- **Verification:** `test_closed_form_refuses_when_not_representable` matches on `DOMAIN LIMIT` (condition 2's text) rather than condition 3's, so the two are distinguishable in the test as well as in the source.
- **Committed in:** `3321421`

**4. [Rule 1 - Bug] Four `gsd-sdk` mutation-handler defects, hand-repaired before commit**

- **Found during:** State updates
- **Issue:** Thirteenth consecutive session. (a) `state.advance-plan` rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — the identical corruption 22-01 and 22-02 both recorded. (b) `state.update-progress` returned `{"updated": false, "reason": "Progress field not found in STATE.md"}` and did nothing; the `progress:` block was already correct after `advance-plan`, so nothing was lost. (c) `roadmap.update-plan-progress` wrote the status cell as `In Progress|  |` — no space before the pipe and an empty date cell where every sibling row carries `-`. Also identical to both prior plans. (d) The same handler wrote the count as `2/11` because it counts SUMMARY files on disk and ran before this file existed; corrected to `3/11`, and `22-03-PLAN.md`'s checkbox flipped by hand (the handler flipped 22-02's but not this plan's). (e) `state.add-decision` prefixed all three entries `- [Phase ?]:`.
- **Two handlers behaved BETTER than 22-02 recorded, and the difference is the argument form.** `state.record-metric --duration 35min` preserved the unit (22-01's positional call dropped it, writing bare `25`), and `state.record-session --stopped-at ...` updated **both** `stopped_at:` and `Stopped at:` (22-02 measured it leaving them stale). Both were called with the `--flag` form 22-02 identified as the working one. The corruption is in the positional path, not in the verbs themselves.
- **Fix:** All five hand-repaired in place before the metadata commit, each verified by `git diff`.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** `grep -c "Phase ?" .planning/STATE.md` → **0**; `grep -c "\[Phase 22\]: 22-03" .planning/STATE.md` → **3**; `Status: Executing Phase 22`; the roadmap row reads `| 3/11 | In Progress | - |`, matching its siblings byte for byte.
- **Committed in:** the plan metadata commit

### Deliberate departures from the plan text

- **No `sys.path.insert(0, str(_ROOT / "scripts"))` in the test module.** The plan asked for it "for later plans' pin read". This plan reads no pin, so the insert would be dead scaffolding for a consumer that does not exist — the same call plan 22-01 made when it refused to pre-populate `_ALLOWED_CLASS_CONSTANTS`. `_ROOT` itself IS present and load-bearing (the AST path, the subprocess `cwd`, and the `relative_to` that keeps both V-09 halves pointed at one knob).
- **Line-number anchors are not used anywhere in `accountant.py`.** The plan names `lora/layer.py:53-55` and `mitigation_gate.py:1026`; both are cited by **symbol** instead (`lora/layer.py::LoRALinear.merge`, `scripts/mitigation_gate.py::MECHANISM_KEYS`), following the habit plan 22-02 established after measuring seven stale anchors in this repository. `src/` files are correctable, so this is preference rather than necessity — but the citations are equally precise and cannot rot.
- **`test_closed_form_domain_refusals` is split into two parametrized tests**, one over `mu` and one over `eps`. The plan named a single test covering `mu = 0.0`, `mu < 0`, `nan` and `inf`; splitting keeps a non-finite `eps` from being conflated with a degenerate `mu`, and both halves are asserted to raise `ValueError` rather than `ZeroDivisionError` as required.
- **`test_quadrature_rejects_bad_grid` covers five node counts** (20000, 4, 2, 1, 0) rather than the two the plan named, and matches on `Simpson` so the grid refusal cannot be satisfied by an unrelated `ValueError`.

---

**Total deviations:** 4 auto-fixed (1 unsatisfiable tolerance inherited from the research prose, 1 missing domain refusal found by measurement, 1 message that would have stated a false reason, 1 tooling corruption), 4 deliberate departures.
**Impact on plan:** Every correction makes the module refuse **more** or assert **more precisely**; none weakens a guard. No scope creep — `pyproject.toml`, `scripts/mitigation_gate.py`, `scripts/mitigation_unit.py` and `scripts/mitigation_accountant.py` are byte-unchanged, which is T-22-SC's and T-22-14's own criterion.

## Issues Encountered

- **`make test` / `make lint` still do not resolve the venv** on this box (22-01 deviation #3, unchanged, third confirmation). All verification ran through `.venv/bin/`. The Makefile is untouched — out of scope.
- **Three ruff findings**, all mechanical: one `I001` import sort (ruff groups `tests.*` with third-party per `pyproject.toml`'s isort note), and two `E501` wraps. One `E501` forced a small restructure — a `trunc / integral` guard expression inside an f-string was hoisted to a named `share` local, which also makes the zero-denominator branch readable rather than buried in a conditional expression.
- **The research's stated worst oracle error is an upper bound this summation beats.** `22-RESEARCH.md` reports 2.71e-12 at ε=8, μ=0.5; measured here the shipped implementation returns `1.0486591789126221e-57` against `1.048659178913e-57`, a relative **3.60e-13** — 7.5× inside the committed `WORST_RELATIVE_ERROR = 2.7e-12`. No contradiction (the committed constant is a bound, and this is under it), recorded so a later reader does not treat 2.7e-12 as a *target* to reproduce.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_accountant.py -q` | **43 passed** |
| V-01 worst relative deviation, 11 rows | **1.84e-12** (11-digit truth); 9.03e-13 worst on a 13-digit row |
| V-02 worst gap between the two oracles, 11 rows | **2.84e-12** against a 1e-9 budget (~350× margin) |
| V-04 derived range at ε=8, μ=0.5 | **3.60e-13** relative |
| V-04 fixed `[-14, 14]` negative control, same point | returns exactly `0.0`, relative error **1.00e+00** |
| V-05 three conditions | 3 raised, **3 distinct messages** (`len(set(texts)) == 3`) |
| Condition 3 independence, measured | at z = 38.5: cond 1 silent, `trunc/I` = 3.20e-15 (cond 2 silent), `delta` = 0.0 |
| V-09 static | `imported == {"math"}` — exactly, behind the collapsed-walk meta-guard |
| V-09 transitive | `subprocess.run` exit 0; `torch`/`numpy`/`scipy`/`mpmath` absent from `sys.modules` |
| Per-function AST call sets | `delta_quadrature` → `{math.exp, math.isfinite, math.sqrt}`; `delta_closed` → `{math.erfc, math.exp, math.isfinite, math.log}` |
| `grep -nE "^\s*(assert \|_prove\()" accountant.py` | **no matches** (rc=1) |
| `grep -n "math.exp(eps) \*" accountant.py` | **no matches** (rc=1) |
| `grep -n "clip_norm" accountant.py` | 2 hits, both docstring prose explaining why the parameter does NOT exist |
| `ast.Raise` nodes in `accountant.py` | **6** (meta-guard requires ≥ 6) |
| Guard mutation probes | **7 RED / 7**, control GREEN, work-tree file byte-identical after |
| RESEARCH F1 reproduction (unguarded) | 3 of 4 rows pass vacuously on `0.0 == 0.0`; all 3 now refuse |
| `git diff --exit-code -- pyproject.toml scripts/mitigation_{gate,unit,accountant}.py` | exit 0 — byte-unchanged |
| Full suite `.venv/bin/python -m pytest -q` | **1083 passed, 1 skipped** in 196.81 s (baseline 1040/1 + 43 new) |
| `.venv/bin/ruff check . && ruff format --check .` | clean, **198 files** formatted |

## Known Stubs

None. Both functions are complete, and every constant they ship is consumed by a committed test. `epsilon_for` / `sigma_for` are **absent, not stubbed** — plan 22-05 owns them, and the module deliberately contains no placeholder for them (a `raise NotImplementedError` would be a stub the V-09 `ast.Raise` meta-guard would then count as a refusal).

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file access at all (`accountant.py` opens nothing), and no schema. It installs nothing.

Threat register dispositions, each mitigated as planned:

- **T-22-10** (an oracle returning `0.0`) — symmetric exact-zero refusal on BOTH oracles, plus `a != 0.0 and b != 0.0` asserted before the comparison. F1 reproduced first: 3 of 4 rows passed vacuously without it.
- **T-22-11** (`math.exp(eps)` OverflowError) — log-space second term guarded on `erfc(b) == 0.0`; `test_closed_form_survives_high_epsilon` watches `math.exp(775.7867)` raise and then asserts `delta_closed(775.7867, 35.355)` is finite and positive.
- **T-22-12** (a "safety" edit widening Λ or raising `n`) — both constants ship with their counter-measurement in an adjacent comment, and V-04's fixed-range negative control reddens if the derived range is ever replaced by a constant.
- **T-22-13** (a refusal downgraded to `assert`) — watched RED on mutation 5, with the `ast.Raise` presence meta-guard watched RED on mutation 7.
- **T-22-14** (a new dependency) — hard-equality static set watched RED on mutations 1/2/3, out-of-process probe watched RED on mutation 4; `pyproject.toml` asserted byte-unchanged.
- **T-22-SC** (package installs) — accepted; nothing installed, `math` is stdlib.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-05** imports `from personacore.privacy.accountant import delta_closed, delta_quadrature`. Three things it must inherit rather than re-derive: (i) `sigma` is the **noise multiplier**, so `mu_eff = sqrt(T)/sigma` and there is no `clip_norm` argument; (ii) `epsilon_for`'s bisection **will** reach ε ≈ 776 at σ=0.40/T=200 — that is safe on `delta_closed` (measured finite) and must stay inside the same log-space form; (iii) both oracles **raise** rather than return in the underflow corner, so a bisection bracket that walks past z ≈ 38.4 gets a `ValueError`, not a `0.0`, and the solver has to treat that as "δ is smaller than any target" rather than propagating the exception.
- **Plan 22-09 owns V-25 and the name is already load-bearing.** `scripts/mitigation_accountant.py::SENSITIVITY_MULTIPLIER_REASON` cites `tests/test_phase22_dpsgd_ast.py::test_adjacency_relation_consistent` by symbol from inside a file that freezes at the first `results/phase23_*` artifact. **This plan has now supplied that test's second site**: `accountant.py`'s docstring carries the literal string `add/remove one fact` and the multiplier `1.0`, in the pin's own words. The third site is `dpsgd.py`'s noise line (plan 22-04).
- **Plan 22-09 also owns V-06** (`GOLDEN_EPSILON` re-derived from `delta_quadrature` alone). It must read `EPSILON_GOLDEN` from `tests/fixtures/phase22_reference.py`, not from the pin, and compare with `GOLDEN_EPSILON_REL_TOL = 1e-12` — never float `==` (RESEARCH F3: the composition identity is exact in real arithmetic and fails bitwise 19.9% of the time in float64).
- **One open hazard, logged in `deferred-items.md`:** the negative-`z` `OverflowError` band is closed by an inequality on `_EXP_OVERFLOW_ARG`, and **nothing tests it**. A future edit dropping the `z < 0.0` clause re-opens it silently. The entry names the measurement and why a fourth `test_oracle_refuses` case was not added (that test's whole assertion is that there are exactly three conditions).

## Self-Check: PASSED

- `src/personacore/privacy/accountant.py` — FOUND
- `tests/test_phase22_accountant.py` — FOUND
- `.planning/phases/22-.../deferred-items.md` — FOUND
- commit `3321421` — FOUND
- commit `9009561` — FOUND
- commit `491002d` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-25*
