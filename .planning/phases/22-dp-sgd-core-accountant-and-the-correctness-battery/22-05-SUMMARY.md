---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 05
subsystem: privacy
tags: [differential-privacy, accountant, bisection, numerical-methods, ast-guards, stdlib-only]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-03's src/personacore/privacy/accountant.py::delta_closed — the log-space closed form this plan bisects over, and the three refusals its underflow corner raises"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-02's scripts/mitigation_accountant.py::GOLDEN_EPSILON / ::GOLDEN_EPSILON_REL_TOL / ::REQUIRED_FORM_CONDITIONS — the frozen pin epsilon_for is judged against"
  - phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
    provides: "scripts/mitigation_unit.py::DELTA — the one delta in the repository, resolved and never re-spelled"
provides:
  - "src/personacore/privacy/accountant.py::epsilon_for — the forward direction, bisected over delta_closed, with the explicit sigma=0 -> inf branch and nine separately-messaged domain refusals"
  - "src/personacore/privacy/accountant.py::sigma_for — the inverse over the SAME forward function (D-12's one choke point), AST-asserted"
  - "src/personacore/privacy/accountant.py::ROUND_TRIP_REL_TOL — the round-trip budget shipped with its measured 8.29e-15"
  - "the accountant docstring's TOLERANCE REGISTER — both halves of RESEARCH F3's rule written down adjacently, the site 22-07's == is justified from"
  - "tests/test_phase22_accountant.py — V-03, V-07 and V-08 live; 43 -> 155 tests"
affects: [22-07 DPSGD-05's bit-identical reported eps, 22-09 V-06 and the fake probes, 23 frontier sweep and mitigation_budget.py]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A caught refusal read as the ORDERING FACT its own condition licenses, never as a substituted number — with the licence measured (delta_closed returns exactly 5e-324 at the last eps before it refuses, at every mu from 1e-8 to 1e8) and a structural guard pinning the refusal count the reading is argued against"
    - "A choke point asserted BOTH structurally (AST: sigma_for calls epsilon_for, calls neither delta oracle) and numerically (a 48-pair round trip) — a 1e-9 divergence reddens 48 of 48"
    - "A negative control that proves a sweep CONTAINS the disagreement its tolerance exists for, so a tolerance test cannot be green over an all-bitwise-equal sample"
    - "A tolerance register written as adjacent prose in the module docstring and pinned by an eight-substring source assertion, so `==` and `rel_tol` cannot be conflated by a reader who saw only one"

key-files:
  created: []
  modified:
    - src/personacore/privacy/accountant.py
    - tests/test_phase22_accountant.py

key-decisions:
  - "The plan's 'let the delta_closed ValueError propagate' is UNSATISFIABLE and was watched RED: applying it verbatim fails test_composition_identity at sigma=50.0 / T=1 on the FIRST doubling step, not in an exotic corner. The refusal is read as the ordering fact it carries instead — 22-03's SUMMARY predicted exactly this"
  - "ROUND_TRIP_REL_TOL's adjacent comment carries the MEASURED 8.29e-15 over 48 pairs, not the plan's '1.07e-15' — which is a mis-transcription of RESEARCH's 1.07e-14 AND of the wrong quantity (that number is the two-ORACLE gap; RESEARCH contains no round-trip measurement)"
  - "_MIN_TARGET_DELTA = 1e-300 added (Rule 2): the underflow-as-upper-bracket reading needs headroom over float64's subnormal floor to be airtight, and without it the inference is ambiguous within one subnormal"
  - "requirements.mark-complete was NOT called, fifth consecutive plan: DPSGD-03 still needs V-06 (22-09) and DPSGD-05 needs the MPS RNG slot and the kill->resume (22-07)"

patterns-established:
  - "Refusal-as-ordering-fact: a helper that maps a sibling's domain refusal onto the single conclusion that refusal's own condition licenses, with the licence measured and the sibling's refusal count pinned by an AST guard so it cannot silently widen"
  - "Sweep non-degeneracy control: assert the swept set contains at least one genuine disagreement, so a relative-tolerance test cannot pass over a sample that would have been green under `==` too"

requirements-completed: []
requirements-contributed: [DPSGD-03, DPSGD-05]

# Metrics
duration: 45min
completed: 2026-08-25
---

# Phase 22 Plan 05: `epsilon_for` / `sigma_for` Over One Choke Point Summary

**Both accountant directions through a single bisected closed form — the inverse AST-proven to call the forward function and neither delta oracle, the round trip closing to 8.29e-15 on 48 frontier points, and the composition identity swept at `rel_tol` behind a control proving the sweep really contains the bitwise disagreement `==` would have hidden.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-08-25T22:24Z (first read after `0171670`)
- **Completed:** 2026-08-25T23:09Z
- **Tasks:** 3
- **Files modified:** 2 (0 created)

## Accomplishments

- **`epsilon_for` reproduces all seven pinned `GOLDEN_EPSILON` rows**, worst relative deviation **1.071e-14** against the pin's own `GOLDEN_EPSILON_REL_TOL = 1e-12` — 93× of margin. That worst case is at σ=2.0/T=200 and it **reproduces RESEARCH's measured 1.07e-14 exactly**, which is the right number to hit: it is the gap between the two *oracles* (the pin bisects the exp-quadrature, this bisects the erfc closed form), not this function's error.
- **σ=0 returns `math.inf` with the mathematics recorded, not the guard alone** — and the test asserts `ZeroDivisionError` is not raised by catching it explicitly and calling `pytest.fail`.
- **The ε > 709.78 regime is survived, measured:** `epsilon_for(0.40, 200, δ) = 775.7866600701457` and `epsilon_for(0.30, 200, δ) = 1312.1599912046381`, both finite. RESEARCH F2 predicts 775.7867 and 1312.1600.
- **`sigma_for`'s one-choke-point property is a structural fact, not a described one.** Its AST body calls `epsilon_for` and calls neither `delta_closed` nor `delta_quadrature`; inlining a second bisection reddens it (watched, M3).
- **The round trip closes to 8.290088e-15 over 48 (σ, T) pairs** — the seven `GOLDEN_EPSILON` σ values plus 0.5/0.7/1.5/3.0/50.0, each at T ∈ {1, 64, 200, 1000}. Worst at σ=14.142135623730951/T=1. And the σ=0 round trip closes **exactly**: both ends are explicit branches, so `sigma_for(epsilon_for(0.0, T, δ), T, δ) == 0.0`.
- **V-03 sweeps 28 pairs at `rel_tol=1e-12`, worst measured gap 9.013338e-16 — at σ=64.84002691931646, T=3506, which is RESEARCH F3's own first representative mismatch row**, reached by the same seed and the same distribution. `==` appears nowhere in it.
- **The negative control is non-vacuous and its number is stated:** 3 of 28 pairs genuinely differ bitwise. F3's trap ("my first 5 hand-chosen pairs were all bitwise equal") is what the seeded sample exists to defeat, and the grid alone would not have.
- **Ten guard mutations, ten distinct REDs, control GREEN, byte-identical restore** (sha256 match on the work-tree file, which was never written to during the probe).
- `pyproject.toml`, `scripts/mitigation_gate.py`, `scripts/mitigation_unit.py` and `scripts/mitigation_accountant.py` are all **byte-unchanged** (`git diff --exit-code` exits 0 against the pre-plan tree). `accountant.py` still imports **`math` and nothing else**.

## Task Commits

1. **Task 1: `epsilon_for` — bisection over the closed form, with the explicit σ=0 branch (V-08)** — `5c8f4a8` (feat)
2. **Task 2: `sigma_for` — the inverse over the SAME form, guarded by a round-trip (V-07)** — `0ee5b7c` (feat)
3. **Task 3: V-03 — the composition-identity oracle, swept, at `rel_tol` and never `==`** — `da932e5` (test)

## Files Created/Modified

- `src/personacore/privacy/accountant.py` (+367, now 704 lines) — the module docstring gains a fifth invariant bullet, the **TOLERANCE REGISTER**, carrying both halves of F3's rule adjacently. Five new module constants (`_BISECT_REL_WIDTH`, `_MAX_BISECTIONS`, `_MAX_DOUBLINGS`, `_MIN_TARGET_DELTA`, `ROUND_TRIP_REL_TOL`), two private helpers (`_refuse_bad_steps_or_delta`, `_delta_or_below_float64`), and the two public directions. 24 `raise` sites, **zero** `assert`, **zero** `_prove`, one import.
- `tests/test_phase22_accountant.py` (+454/−1, now 825 lines) — 43 → **155** tests. New: V-08 (4 rows), the golden pin sweep with a 7-row meta-guard *and* a non-vacuity assertion in the other direction, the F2 regime (2 rows), 9 domain refusals + their distinctness check, V-07 (48 rows) + its count meta-guard, the exact σ=0 round trip (4 rows), 10 `sigma_for` refusals, the `sigma_for` AST choke-point guard, V-03 (28 rows), its negative control, the tolerance-register source assertion, and the `delta_closed` raise-count guard.

## Decisions Made

- **A `delta_closed` refusal inside the search is read as the ORDERING FACT it carries, and the licence is measured rather than argued.** `_delta_or_below_float64` returns `None` — not a number, and it never reaches a caller — meaning "δ here is below float64's range, therefore below the target". Three things make that airtight rather than convenient: (i) measured, `delta_closed` returns **exactly `5e-324`** (float64's smallest positive value) at the last ε before it refuses, at *every* μ from 1e-8 to 1e8; (ii) `_MIN_TARGET_DELTA = 1e-300` floors the target 24 decades above that; (iii) `delta_closed`'s first two `raise` statements (non-finite input, `mu <= 0.0`) are **structurally unreachable** from the search, which re-checks `eps` finite and enters with a finite strictly-positive `mu` — so the caught `ValueError` cannot be a different refusal wearing the same type. A fifth `raise` in `delta_closed` reddens `test_delta_closed_still_ships_exactly_four_raises` (watched, M5), which forces the next author to re-read the contract instead of inheriting it.
- **`ROUND_TRIP_REL_TOL` ships the measurement this plan took, not the one the plan text quoted.** See deviation 2.
- **The σ=0 branch sits *after* input validation and *immediately before* the only division.** The plan says "FIRST, before any arithmetic"; placed literally first, `epsilon_for(0.0, 0, 5.0)` would return `inf` for a call with a garbage step count and a garbage delta. Validation performs no arithmetic on σ, so the branch still precedes every operation the plan's reason is about (`math.sqrt(steps) / sigma`), and garbage still refuses. Same choice in `sigma_for`: `_refuse_bad_steps_or_delta` runs **before** the `target_epsilon == inf` fast path, and two of the ten refusal cases exist specifically to pin that ordering.
- **Line-number anchors are not used anywhere in the new code.** The plan names `lora/inject.py:113-118`; it is cited by symbol as `lora/inject.py::load_adapter_weights` (resolved by AST against HEAD — `:113` falls inside `load_adapter_weights`, lines 76–130). This continues 22-02's and 22-03's habit for the same reason: an anchor rots, a symbol does not.
- **`requirements.mark-complete` was NOT called**, fifth consecutive plan. DPSGD-03 additionally requires **V-06** — `GOLDEN_EPSILON` re-derived from `delta_quadrature` alone, plan 22-09 — and DPSGD-05 requires the MPS RNG slot plus the kill→resume bit-identical ε, plan 22-07. Neither exists. Both stay `- [ ]`.

## Guards Watched Failing

No guard was believed on the strength of being green. Every mutation was applied to a **copy of the committed source written into the work-tree path and restored in a `finally`**, with a `sha256` comparison asserting the restore was byte-identical (it was: `afa02099721d4221…` before and after).

| # | Mutation | Guard reddened | Evidence |
|---|---|---|---|
| 0 | control (unmutated) | — | **155 passed** |
| 1 | the `sigma == 0.0` branch deleted | `test_sigma_zero` | **4 failed** (all four step counts) |
| 2 | `epsilon_for` returns ×(1 + 1e-9) | `test_epsilon_for_matches_golden` | 1 failed |
| 3 | `sigma_for` inlines a bisection over `delta_closed` | `test_sigma_for_uses_the_forward_function` | 1 failed — the choke point |
| 4 | `sigma_for` returns ×(1 + 1e-9) — a *plausible* inverse | `test_round_trip` | **48 failed / 48** |
| 5 | a FIFTH `raise` added to `delta_closed` | `test_delta_closed_still_ships_exactly_four_raises` | 1 failed |
| 6 | the `==` half of the tolerance register deleted | `test_tolerance_register_is_documented` | 1 failed |
| 7 | the `rel_tol` half of the tolerance register deleted | `test_tolerance_register_is_documented` | 1 failed |
| 8 | **the underflow refusal propagates (the plan's literal instruction)** | `test_composition_identity` + `test_round_trip` | **3 failed** — see below |
| 9 | `_MIN_TARGET_DELTA` floor removed | `test_epsilon_for_domain_refusals` | 1 failed |
| 10 | `sigma_for`'s `+inf` path jumps the domain check | `test_sigma_for_domain_refusals` | 2 failed |

**10 mutations, 10 REDs, control GREEN on all 155.**

**Mutation 8 is the load-bearing one, because it is the plan's own instruction applied verbatim.** Removing the `try/except` — i.e. letting `delta_closed`'s `ValueError` propagate as the plan directs — produces:

```
FAILED tests/test_phase22_accountant.py::test_composition_identity[50.0-1]
E  ValueError: delta_closed(1.0, 0.02): delta is below float64's range and this is a
   DOMAIN LIMIT, not a number to return. erfc(z/sqrt(2)) underflowed to exactly 0.0 at
   z = eps/mu - mu/2 = 49...
```

σ = 50.0, T = 1 gives μ = 0.02, and the doubling walk's **very first probe** at `hi = 1.0` already sits at z = 49.99. This is not an overshoot in an exotic corner: the plan's instruction aborts a legitimate solve at an ordinary frontier point, on the first evaluation. Full-file blast radius under mutation 8: **3 failed, 152 passed**, across `test_composition_identity`, `test_composition_identity_would_fail_under_exact_equality` and `test_round_trip`.

Separately, the **refusal boundary itself was measured before the reading was accepted**, by bisecting on z at fixed μ:

| μ | first-refusal z | `delta_closed` at the last good ε |
|---|---|---|
| 1e-8 | 37.915071666 | `5e-324` |
| 1e-4 | 38.172085476 | `5e-324` |
| 0.005 | 38.253332248 | `5e-324` |
| 0.1 … 1e6 | 38.466608897 | `5e-324` |
| 1e8 | 38.466608893 | `5e-324` |

The z=38.4666 plateau matches the committed `ZERO_BOUNDARIES["delta_closed_zero_z"] = 38.466608897` to nine digits. The drift below it at small μ is the cancellation term (δ/Φ(−z) ≈ μ/z), and the right-hand column is the whole argument: **at every probed μ the last representable delta is float64's smallest positive value**, so a refusal is unambiguously below any target above the floor.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's "let the `ValueError` propagate" makes `epsilon_for` unusable on ordinary inputs**

- **Found during:** Task 1
- **Issue:** The plan says *"If `delta_closed` REFUSES anywhere in the bracketing walk (its representability refusal), let the `ValueError` propagate with context added — do not swallow it and do not substitute a number."* Measured, that aborts the solve at σ = 50.0 / T = 1 — μ = 0.02 — on the **first** probe of the doubling walk, because z = ε/μ − μ/2 = 49.99 at ε = 1.0. It also fires during V-03's own sweep at high μ. 22-03's SUMMARY predicted this in its Next Phase Readiness note: *"a bisection bracket that walks past z ≈ 38.4 gets a `ValueError`, not a `0.0`, and the solver has to treat that as 'δ is smaller than any target' rather than propagating the exception."*
- **Fix:** `_delta_or_below_float64` catches the refusal and returns `None`, used **only** as "δ < target". This is not the failure F1 exists to prevent — F1 is about a refusal becoming a **number** that then gets **compared** against another oracle's number; `None` is neither, it is the one conclusion the refusal's own condition licenses. Three things make the reading airtight rather than convenient: the measured `5e-324` table above, the new `_MIN_TARGET_DELTA = 1e-300` floor, and the structural unreachability of `delta_closed`'s two garbage-input refusals from the search (the helper re-raises on a non-finite `eps` rather than mapping it onto the underflow reading). `test_delta_closed_still_ships_exactly_four_raises` pins the refusal count the argument is made against.
- **Files modified:** `src/personacore/privacy/accountant.py`, `tests/test_phase22_accountant.py`
- **Verification:** mutation 8 above — the plan's version watched RED, 3 failed / 152 passed, with the exact message and the exact (σ, T) reproduced.
- **Committed in:** `5c8f4a8`

**2. [Rule 1 - Bug] `ROUND_TRIP_REL_TOL`'s "measured achievable value (≤ 1.07e-15)" is wrong twice over**

- **Found during:** Task 2
- **Issue:** The plan directs `ROUND_TRIP_REL_TOL` to ship *"the measured achievable value (≤ 1.07e-15)"* and cites `22-RESEARCH.md § For GOLDEN_EPSILON's pin tolerance` for it. That section's table is **ε via the closed form vs ε via the oracle**, and its worst row is **1.07e-14**, not 1.07e-15 — an order of magnitude, transcribed down. Worse, it is a different quantity: that number measures the gap between **two oracles**, and `22-RESEARCH.md` contains **no round-trip measurement at all**. The acceptance criterion asks the file to publish a figure that does not exist.
- **Fix:** The round trip was measured against the shipped code: **8.290088e-15** worst relative deviation over 48 (σ, T) pairs, at σ=14.142135623730951 / T=1. That number ships in the constant's adjacent comment **with its denominator and its probe conditions**, plus an explicit note that it is one machine's 48 points and not a bound. A parenthetical beside it names the *other* 1e-12 in the module (`GOLDEN_EPSILON_REL_TOL`, against 1.07e-14) so a reader does not read one tolerance's provenance onto the other — which is the mistake the plan text itself made.
- **Files modified:** `src/personacore/privacy/accountant.py`, `tests/test_phase22_accountant.py`
- **Verification:** 48/48 pairs pass at 1e-12; the measured worst is printed above and the value in the docstring, the comment and the test docstring are the same number.
- **Committed in:** `0ee5b7c`

**3. [Rule 2 - Missing critical functionality] The plan specifies no lower bound on `delta`, and the underflow reading needs one**

- **Found during:** Task 1
- **Issue:** The plan's refusal list is `sigma < 0`, `steps < 1`, non-integer `steps`, `delta <= 0.0`, `delta >= 1.0`, non-finite. With only those, a caller may pass `delta = 5e-324` — a legal float in `(0, 1)` — and the "a refusal means δ is below the target" inference becomes ambiguous **within one subnormal**, because δ at the last good ε *is* `5e-324`.
- **Fix:** `_MIN_TARGET_DELTA = 1e-300` with a `DOMAIN LIMIT`-shaped message stating the reason (the search's reading needs headroom over float64's subnormal floor) rather than merely the bound. 24 decades of margin, and this project's frozen δ is 1e-5.
- **Files modified:** `src/personacore/privacy/accountant.py`, `tests/test_phase22_accountant.py`
- **Verification:** mutation 9 — removing the floor reddens `test_epsilon_for_domain_refusals`; `epsilon_for(1.0, 200, 1e-320)` raises naming the floor.
- **Committed in:** `5c8f4a8`

**4. [Rule 1 - Bug] My own first draft mis-stated `delta_closed`'s refusal count, and its own new guard caught it**

- **Found during:** Task 1
- **Issue:** `test_delta_closed_still_ships_exactly_three_refusals` asserted 3, on the strength of `delta_closed`'s docstring headings ("Refusal 1 of 3"). Measured, the function contains **four** `ast.Raise` statements — heading 1 covers *two* statements (the non-finite check and the `mu <= 0.0` check). The test went RED on the committed, correct source.
- **Fix:** Renamed to `…_exactly_four_raises` and corrected to 4, with the four-statements/three-headings distinction written into both the test docstring and `_delta_or_below_float64`'s. The test counts **statements**, because a statement is what a new refusal would add.
- **Files modified:** `src/personacore/privacy/accountant.py`, `tests/test_phase22_accountant.py`
- **Verification:** `AssertionError: delta_closed now raises at [160, 166, 191, 210] — 4 refusals` — the guard reddening on its author before anything was committed.
- **Committed in:** `5c8f4a8`

**5. [Rule 1 - Bug] Five `gsd-sdk` mutation-handler defects, hand-repaired before commit**

- **Found during:** State updates
- **Issue:** Fifteenth consecutive session, and the pattern is stable enough to be a fact rather than a complaint. (a) `state.advance-plan` rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — identical to 22-01, 22-02, 22-03 and 22-04. (b) `state.update-progress` returned `{"updated": false, "reason": "Progress field not found in STATE.md"}` against a frontmatter that plainly has one; harmless here because `advance-plan` had already set the block correctly. (c) `state.add-decision --summary` prefixed all three entries `- [Phase ?]:`. (d) `roadmap.update-plan-progress 22` wrote the status cell as `In Progress|  |` — no space before the pipe and an empty date cell where every sibling row carries `-`; identical to all four prior plans. (e) the same handler wrote `4/11` because it counts SUMMARY files on disk and ran before this file existed, and it did **not** flip this plan's `- [ ] 22-05-PLAN.md` checkbox.
- **Two handlers behaved correctly**, both called with the `--flag` form: `state.record-metric --duration 45min` preserved the unit, and `state.record-session --stopped-at` updated **both** `stopped_at:` and `Stopped at:`. This is the third consecutive confirmation that the corruption lives in the **positional** argument path.
- **Fix:** All five hand-repaired in place before the metadata commit, each verified by `git diff`.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** `grep -c "Phase ?" .planning/STATE.md` → **0**; `Status: Executing Phase 22`; both `stopped_at` fields read `22-05`; the roadmap row reads `| 5/11 | In Progress | - |`, matching its siblings byte for byte; the 22-05 checkbox is `- [x]`.
- **Committed in:** the plan metadata commit

### Deliberate departures from the plan text

- **The σ=0 branch is placed after input validation**, not literally first. See Decisions — the reason the plan gives (never reach `sqrt(steps)/sigma`) is fully served, and a garbage `steps`/`delta` still refuses instead of being answered.
- **`test_epsilon_for_domain_refusals` uses `mitigation_unit.DELTA` as its filler delta**, not the literal `1e-5`. The plan's own acceptance criterion is `grep -n "1e-5" tests/test_phase22_accountant.py` returning nothing; writing `1e-5` in a refusal case that does not care about the value would have re-spelled the frozen delta for no gain. `grep` returns rc=1.
- **The domain refusals are two tests, not one**: a parametrized `pytest.raises` sweep and a separate distinctness check asserting all nine messages differ. The plan asked for "distinct messages"; asserting it is the only way that phrase does any work, and it is `test_oracle_refuses`'s established shape in this same file.
- **Two extra `sigma_for` refusal cases** (`math.inf` with `steps = 0`, and `math.inf` with `delta = 1.0`) beyond the four the plan names. They pin the *ordering* — that the `+inf` fast path does not jump the domain check — which is a property no other case can see.
- **Three extra non-vacuity assertions** the plan did not ask for: the golden sweep asserts the worst deviation is **strictly greater than zero** (a bitwise match on all seven rows would mean the pin has become a photograph of the code), `_round_trip_pairs` is pinned at 48 pairs / 12 distinct σ, and the composition sweep is pinned at ≥ 20 pairs before its control counts anything.
- **The task acceptance criteria's test counts ("at least 14/18/21 passed") were written for a fresh file** and are trivially met — the file starts at 43 and ends at 155. Recorded so a reader does not mistake the large number for scope creep.

---

**Total deviations:** 5 auto-fixed (1 unsatisfiable instruction watched RED, 1 doubly-wrong transcribed number, 1 missing domain refusal, 1 self-inflicted and caught by its own new guard, 1 tooling corruption), 6 deliberate departures.
**Impact on plan:** Every correction makes the module refuse **more** or assert **more precisely**; none weakens a guard. No scope creep — `pyproject.toml` and all three frozen `scripts/mitigation_*.py` files are byte-unchanged, which is T-22-SC's own criterion.

## Issues Encountered

- **`make test` / `make lint` still do not resolve the venv** on this box (22-01 deviation #3, fourth confirmation). All verification ran through `.venv/bin/`. The Makefile is untouched — out of scope.
- **Two ruff findings**, both mechanical: one `E501` on a test docstring's summary line (rewrapped, no assertion touched) and one `ruff format` pass that re-wrapped a dict comprehension in `test_sigma_for_uses_the_forward_function`. No semantics changed.
- **RESEARCH F3's 19.9% bitwise-disagreement rate does not reproduce on a 28-point sweep, and that is expected rather than a discrepancy.** Measured here: 3/28 = 10.7%. F3's rate is over 4,000 purely random draws; this sweep is 16 round-number grid points (which agree bitwise far more often) plus 12 seeded samples. The control asserts non-degeneracy, not a rate — recorded so a later reader does not treat 19.9% as a target to reproduce.
- **The composition sweep's worst pair is F3's own worst-listed representative** (σ=64.84002691931646, T=3506), which is an independent confirmation that the seed and the distribution in the test match the ones RESEARCH used. The *relative gap* differs (9.01e-16 here vs F3's 4.51e-16) because the two bisections are not the same solver, which is the expected reading.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_accountant.py -x -q` | **155 passed** (was 43) |
| Golden pin, 7 rows, worst relative deviation | **1.071e-14** against `GOLDEN_EPSILON_REL_TOL = 1e-12` |
| `epsilon_for(0.40, 200, δ)` / `epsilon_for(0.30, 200, δ)` | `775.7866600701457` / `1312.1599912046381`, both finite |
| `epsilon_for(0.0, T, δ)` for T ∈ {1, 64, 200, 1000} | `inf`, no `ZeroDivisionError` |
| V-07 round trip, 48 pairs, worst relative | **8.290088e-15** against `ROUND_TRIP_REL_TOL = 1e-12` |
| `sigma_for(epsilon_for(0.0, T, δ), T, δ)` | `0.0` **exactly**, all four T |
| V-03, 28 pairs, worst relative gap | **9.013338e-16** at σ=64.84002691931646 / T=3506 |
| V-03 negative control | **3 of 28** pairs differ bitwise (not 0) |
| `sigma_for` AST call set | contains `epsilon_for`; `delta_closed`/`delta_quadrature` absent |
| `delta_closed` refusal boundary, μ ∈ [1e-8, 1e8] | last representable δ is **exactly `5e-324`** at every probed μ |
| `grep -n "^import \|^from " src/personacore/privacy/accountant.py` | **one line**: `import math` |
| `ast.Raise` / `ast.Assert` in `accountant.py` | **24** / **0** |
| `grep -n "def epsilon_for"` | `(sigma, steps, delta)` — no `clip_norm` |
| `grep -n "clip_norm" accountant.py` | 4 hits, all docstring prose explaining why the parameter does NOT exist |
| `grep -n "1e-5" tests/test_phase22_accountant.py` | **no matches** (rc=1) — the frozen δ is never re-spelled |
| Guard mutation probes | **10 RED / 10**, control GREEN, sha256-identical restore |
| `git diff --exit-code -- pyproject.toml scripts/mitigation_{gate,unit,accountant}.py` | exit 0 — byte-unchanged |
| Full suite `.venv/bin/python -m pytest -q` | **1219 passed, 1 skipped** in 200.53 s (baseline 1107/1 + 112 new) |
| `.venv/bin/ruff check . && ruff format --check .` | clean, **200 files** formatted |

## Known Stubs

None. Every constant added is consumed by a committed test, both public functions are complete, and no placeholder was left for a later plan. `epsilon_for` and `sigma_for` are the last executable pieces `accountant.py` owes; 22-09's V-06 and V-25 read this module, they do not extend it.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file access (`accountant.py` opens nothing), and no schema. It installs nothing.

Threat register dispositions, each mitigated as planned:

- **T-22-21** (σ=0 crashing Phase 23's first executed run) — explicit `sigma == 0.0 -> math.inf`, watched RED on mutation 1 across all four step counts; `test_sigma_zero` catches `ZeroDivisionError` explicitly and calls `pytest.fail`.
- **T-22-22** (a second divergent bisection improvised elsewhere) — asserted **twice**: structurally by AST (mutation 3, RED) and numerically by the round trip (mutation 4, **48 of 48** RED on a 1e-9 divergence that every single-direction test passes).
- **T-22-23** (a composition test green by luck on an all-equal sweep) — the negative control measures 3 of 28 differing, and its message tells the author to widen the sweep rather than believe an all-equal result.
- **T-22-24** (`==` and `rel_tol` conflated) — both registers adjacent in the module docstring, pinned by eight substrings; deleting **either** half reddens (mutations 6 and 7, two distinct REDs).
- **T-22-25** (a refusal swallowed and replaced by a number) — a refusal is mapped to `None` and used **only** as an ordering fact, never compared; the licence is measured (`5e-324` at every μ), floored (`_MIN_TARGET_DELTA`), and the refusal count it rests on is pinned (mutation 5, RED).
- **T-22-SC** (package installs) — accepted; nothing installed, `math` is stdlib, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-07 (DPSGD-05) must use exact `==` for the kill→resume ε and must not reach for `ROUND_TRIP_REL_TOL`.** The justification is now written down in `accountant.py`'s module docstring and pinned by `test_tolerance_register_is_documented`; 22-07 should cite that register rather than re-deriving the argument. The two rules are one substring-check apart and deleting either half is a watched RED.
- **Plan 22-09's V-06 reads `EPSILON_GOLDEN` from `tests/fixtures/phase22_reference.py`, not from the pin** — this plan added the `sys.path.insert(0, scripts)` block and the `mitigation_accountant` / `mitigation_unit` imports to `tests/test_phase22_accountant.py`, which is the wiring 22-03 deferred to "the same commit as its first consumer". V-06 re-derives the seven rows from `delta_quadrature` **alone**; this plan's `test_epsilon_for_matches_golden` compares the erfc route against the pin, which is a different claim and neither substitutes for the other.
- **Phase 23's frontier must call `sigma_for`, not improvise a bisection.** That is D-12's whole point and it is now enforceable: `mitigation_budget.py` or a driver writing its own solve would be untested against `GOLDEN_EPSILON` and free to disagree. `epsilon_for` and `sigma_for` are importable from `personacore.privacy.accountant` with no torch and no `scripts/` dependency.
- **Three inherited behaviours a consumer must not re-derive:** (i) `epsilon_for` refuses `delta < 1e-300` — a `DOMAIN LIMIT` refusal, not a bug; (ii) `steps` must be a real `int` (a `float` like `200.0` refuses, and `bool` is rejected as an int subclass); (iii) `sigma_for(math.inf, …)` is exactly `0.0` and `epsilon_for(0.0, …)` is exactly `math.inf`, so the σ=0 point round-trips without arithmetic and Phase 23 can report it directly.
- **One thing left unbuilt on purpose:** nothing in this plan measures `epsilon_for` against the *quadrature* oracle end to end. V-02 cross-checks the two δ oracles and V-03 cross-checks two call shapes of one ε route; the ε-level two-oracle check is V-06, and it belongs to 22-09 by design so the pin's derivation stays independent of the implementation.

## Self-Check: PASSED

- `src/personacore/privacy/accountant.py` — FOUND
- `tests/test_phase22_accountant.py` — FOUND
- `.planning/phases/22-.../22-05-SUMMARY.md` — FOUND
- commit `5c8f4a8` — FOUND
- commit `0ee5b7c` — FOUND
- commit `da932e5` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-25*
