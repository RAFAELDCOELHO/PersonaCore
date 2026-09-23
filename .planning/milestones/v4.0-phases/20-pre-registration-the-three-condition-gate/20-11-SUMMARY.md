---
phase: 20-pre-registration-the-three-condition-gate
plan: 11
subsystem: pre-registration-correction
tags: [gate-06, tripwire, watched-red, ast-census, choke-point, wilson, unpinned, wr-02]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 08
    provides: "scripts/phase20_gate_coverage.py — corrected_point_verdict, coverage_verdict, wilson_lower_bound, _prove_retention_floor, COVERAGE_STATISTIC_BY_AXIS, SUPERSEDED_GATE06_BLOCK, SUPERSEDED_SWEEP_SENTINEL. Its docstrings CITE two of this file's test names, so those names were commitments before this plan ran"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 10
    provides: "results/phase20_gate_coverage_correction.{md,json} — the published numbers re-derived here, the marker triple re-declared here, and a pre-append REVISION (4e4d5ef) the additivity guard derives from git log rather than pinning"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 07
    provides: "results/phase20_retention_floor.json — the artifact WR-02 recorded as read by nothing in tests/. Now read on both sides"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 05
    provides: "scripts/mitigation_gate.py (CLOSED pin) — mitigation_point_verdict, extraction_ceiling, retention_cap, F_Y and the three committed FIXTURE_* dicts every reproduction is driven from"
  - phase: 19-selective-erasure
    plan: 09
    provides: "tests/test_phase19_correction.py:105-175 — the additivity guard ported here, and the module-constant marker register at :49-59"
provides:
  - "tests/test_phase20_correction.py — UNPINNED, CPU-only, GPU-free, 957 lines, 11 tests"
  - "both reproduced directions asserted RED against the frozen pin and GREEN through the correction in ONE differential body each, plus the third unreported case"
  - "test_wilson_bounds_are_exact_mirrors and test_mitigation_point_verdict_has_no_caller_outside_this_module — the two names scripts/phase20_gate_coverage.py's docstrings already cite"
  - "FOUR watched-RED breaks with their observed output, for 20-SECURITY.md's Watched-RED evidence table"
affects: [20-12, phase-23, phase-25]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A guard is verified by being WATCHED failing, not by being written — the deliberate break is run, its output recorded, and the file restored with a sha256 check plus `git diff --exit-code`"
    - "A refusal suite is driven THROUGH the verdict route, never against the helper in isolation: the claim is reachability (no path skips the check), and the helper alone proves a different and weaker thing"
    - "A refusal test with no positive control cannot distinguish 'the guard fires' from 'nothing works'"
    - "An AST census matches BOTH `.id` and `.attr` — a bare-name matcher is invisible to `module.function(...)`, which is the form a downstream driver actually writes"
    - "A census is proved NON-VACUOUS by asserting a match where a call certainly exists; an empty result from a broken matcher proves nothing"
    - "Identity is proved by the mechanism that can FAIL for that object's type: `is` for a function or a float, AST import-vs-assign for a small int CPython interns"
    - "A verify block asserts the pytest exit code, a passing COUNT and the absence of skips — `pytest <file> -q` exits 0 on one passing test and cannot enforce 'at least N'"

key-files:
  created:
    - tests/test_phase20_correction.py
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-11-SUMMARY.md
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "The census test is named `test_mitigation_point_verdict_has_no_caller_outside_this_module`, NOT the plan's `test_no_path_to_a_v4_verdict_bypasses_the_correction` — `scripts/phase20_gate_coverage.py`'s module docstring and `corrected_point_verdict.__doc__` both cite the former by name in SHIPPED code, so it was a commitment before this plan ran and a shipped module citing a test that never gets written is the T-20-55 defect class"
  - "MEASURED AND RECORDED: a one-digit edit at the LAST decimal place of `3.9085032379884783` is NOT a different double — `3.9085032379884782 == 3.9085032379884783` is True. The watched-RED break was therefore made at the 16th significant digit, the last position where a single-digit change survives the round trip. A hand edit below a double's resolution is invisible to a bit-exact test AND to every consumer, so it is not a tampering path this guard misses"
  - "`zero_successes_short_circuit.measured_residue_at_n_104` is deliberately NOT re-derived. Re-deriving it would require writing the naive mirror's `centre - spread` into the test — a second copy of exactly the estimator the module short-circuits, i.e. the T-20-53 defect introduced by the test that exists to prevent it. The short-circuit's OUTPUT is asserted instead, which is the part any decision could read"
  - "The marker triple was taken from the COMMITTED `results/phase20_gate_coverage_correction.md` (dated 2026-08-21), never from `20-10-PLAN.md`'s stale `2026-08-20`"
  - "requirements.mark-complete NOT run for `requirements: [GATE-06, GATE-02]` — GATE-06 is 20-12's to discharge, against a re-run rather than against this SUMMARY; GATE-02 was already [x] and amended at 20-09"

patterns-established:
  - "Break at the last digit that survives the float round trip, not at the last digit printed — a tampering probe below the type's resolution silently proves nothing"
  - "Where a plan's prescribed test name conflicts with a name already cited in shipped code, the SHIPPED CITATION wins and the divergence is recorded; the docstring is the editable half only if a name must genuinely change"

requirements-completed: []

# Metrics
duration: 22min
completed: 2026-08-21
---

# Phase 20 Plan 11: The Armed Tripwires Summary

**Both GATE-06 mislabeling directions have now been WATCHED failing against the frozen pin and
passing through the correction, the retention choke point has been watched firing with one of its
`_prove` calls deleted, and the first caller to bypass the sanctioned route turns a committed test
red — matched on the `ast.Attribute` form a bare-name census would miss.**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-08-21T15:35Z
- **Completed:** 2026-08-21T15:57Z
- **Tasks:** 3 of 3
- **Files created:** 1 (957 lines, 11 tests, plus this SUMMARY)

## Accomplishments

### Task 1 — both directions, the sealed interface, and the mirror bound (`2743b18`)

`tests/test_phase20_correction.py` created. UNPINNED, CPU-only, GPU-free: stdlib plus three sibling
scripts and `git`. Module docstring in `tests/test_phase19_correction.py`'s register — why a
continuation and not a fix, and what is at stake in the verdicts. The marker triple `PENDING` /
`RECORDED` / `ADDENDUM_HEADING` is declared as module constants, taken from the **committed**
continuation (dated `2026-08-21`), with the reason for the date recorded at the declaration.

`_corrected_call` uses the `base.update(overrides)` merge form. Verified reachable: every retention
refusal case overrides `retention_floor_provenance` and the WR-09 held-out case overrides
`sweep_heldout_recalls`, and the one-expression form would have raised `TypeError` on all nine.

The differential table, each row asserted in ONE test body so the RED and the GREEN are checked
against each other rather than in separate files:

| Case | Fixture | Sweep | Pin | Corrected |
|---|---|---|---|---|
| Direction (i) | `FIXTURE_CLEARING_POINT` | `(1, 3)` / `(104, 104)` | `INCONCLUSIVE` + GATE-06 | **`PASS`** |
| Direction (ii) | `FIXTURE_DESTROYED_MODEL` | `(3, 11)` / `(104, 104)` | `FAIL`, **no** GATE-06 reason | **`INCONCLUSIVE`** |
| The third case, in no report | `FIXTURE_CLEARING_POINT` | `(3, 11)` / `(104, 104)` | `PASS` | **`INCONCLUSIVE`** |

X, both Wilson bounds and both Y floors are obtained by CALLING `extraction_ceiling`,
`wilson_upper_bound` and `F_Y * control_*_recall`. No test in the file types a float for any of
them. The third row's failure message states its honest limit in the assertion text itself: it does
not contradict the verifier's narrower no-spurious-PASS claim, which was scoped to self-consistent
inputs.

`test_the_sanctioned_route_cannot_be_handed_raw_rates` asserts the interface half AND the value
half, because deleting a parameter removes a wrong value SPACE's path but not the wrong VALUE:
`sweep_extraction_rates` absent from the signature, all 24 parameters `KEYWORD_ONLY` with
`default is inspect.Parameter.empty`, and the direction-(ii) migration mistake
(`sweep_extraction_successes=(3/104, 11/104)`) raising `SystemExit` whose message names both RATE
and COUNT. A negative count and a count above its denominator raise too, and the integer form of the
same sweep is the positive control.

`test_wilson_bounds_are_exact_mirrors` — the name `wilson_lower_bound.__doc__` already cites, and
the trap `20-08-SUMMARY.md` warned about is honoured: the `successes == 0` case is asserted
SEPARATELY as the analytic `0.0`, never folded into the mirror claim. `wilson_lower_bound(0, n) ==
0.0` EXACTLY for every `n` in `2..400` — 399 denominators, spanning the measured cancelling `11`,
`104` and `208`. Bracketing exact at all 105 outcomes at n=104, no `math.isclose` anywhere near it.
The single tolerance is on symmetry about the shared Wilson centre (worst observed
`1.11e-16`, asserted at `abs_tol=1e-12`), which is a property of the shared construction rather than
a bracketing guarantee, and the centre is computed WITHOUT `spread` or `sqrt` so it is not a second
copy of either bound.

Identity per object by the mechanism that can fail for its TYPE: `is` for `wilson_upper_bound`
(function, across all three modules) and `F_Y` (the float `0.7`), AST import-alias membership plus
absence from every module-scope `ast.Assign` target for `MARGIN_K` and `EXTRACTION_FLOOR_MIN_SEEDS`
— both the small int `2`, which CPython interns, so an `is` check on them could not fail.

### Task 2 — additivity, re-derivation, and the defects still live (`da1aa77`)

`test_correction_addendum_is_additive_on_the_published_artifact` ported from
`tests/test_phase19_correction.py:105-175`. The pre-append revision is DERIVED — "the newest
committed revision still carrying the placeholder is BY DEFINITION the one before the append" — from
`git log --format=%H -- <path>`, never a pinned hash and never `git ls-files`. Shallow-clone
assertion kept. The one thing Phase 19's version lacks is added:
`_addendum._verdict.recorded_verdict(after) is not None`, so `append_addendum`'s own
unchanged-verdict guard is proved non-vacuous on THIS file rather than passing on `None == None`.
STAT-02 is enforced as 20-10's LINE-SCOPED rule: a line carrying a `%` figure must carry a `k/n`
denominator on that same line.

`test_every_published_number_re_derives_from_the_modules` — every float obtained by calling:

| Published | Re-derived by |
|---|---|
| `evidence.X` | `mitigation_gate.extraction_ceiling(**fixture's own args)` |
| `evidence.y_taught` / `y_heldout` | `coverage.F_Y * fixture["control_*_recall"]` |
| every `swept_points[*]` field | `wilson_upper_bound(k, n)`, `k / n`, and both clears-flags recomputed against X |
| all three `direction_*` pairs | the pin AND the route re-run on the fixture the payload NAMES |
| `retention_provenance` (2 floors, 2 caps, ratio, `borrowed_floor_is_looser`) | `retention_cap` on each floor; `measured_floor` read from `results/phase20_retention_floor.json` |
| every `reported_lower_bounds` entry | `wilson_lower_bound` / `wilson_upper_bound` at the priced count, and the count itself as `round(rate * n)` |
| `supersedes`, `superseded_sweep_sentinel`, `coverage_statistic_by_axis` | the module constants |
| `heldout_coverage` verdict, `y_heldout` and sentence | the route, at the payload's own `(0.30, 0.28)` sweep |

`test_the_three_defects_are_still_live_in_the_frozen_pin` asserts each against the CODE — CR-01 by
re-running direction (i) on the pin, WR-09 by `inspect.signature` (21 parameters, no
`sweep_heldout_recalls`), T-20-19 by `retention_cap` accepting the borrowed floor and returning the
LOOSER cap. Each message says that a green result means the continuation needs RE-READING rather
than deleting, and adds the point the pin's frozen-ness makes available: a change in its behaviour
would itself mean something moved that could not have.

### Task 3 — the retention refusals, WR-02, and the caller census (`3aca4b0`)

`test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` — the twin of
`tests/test_phase20_prereg.py:1297-1330` over the retention leg. All eight refusals driven THROUGH
`corrected_point_verdict`:

| Input | Assertion beyond `SystemExit` |
|---|---|
| `retention_floor_provenance={}` | — |
| `{"seeds": (1337, 2024)}` (no `regime`) | — |
| `regime="full-finetune"` | — |
| `seeds=(1337,)` and `(1337, 1337)` | the message reports `1 distinct` |
| `retention_noise_floor=V20_RETENTION_NOISE_FLOOR` under clean adapter provenance | the message publishes `7.939763314393305`, `4.029` and `3.9085032379884783` — all three DERIVED through the frozen `retention_cap` in the test, never retyped |
| `extraction_noise_floor=-0.01` | names the floor's SIGN, does not name the ceiling's range |
| `extraction_noise_floor=-0.05` | same — this is the magnitude that proves ORDERING |

The `-0.05` case is the one that bites: it drives the ceiling to `-0.07464477133505877`, so a sign
check placed after the ceiling computation would be pre-empted by the `0.0 < ceiling < 1.0` message
and the caller would be told the wrong thing. Asserted on the MESSAGE, not merely on `SystemExit`.
The positive control — a call differing only in the refused field — still returns `PASS`.

`test_v4_retention_cap_reads_the_measured_adapter_regime_floor` closes WR-02: nothing in `tests/`
read `results/phase20_retention_floor.json` before today. `retention_cap(floor) == artifact["cap"]`
bit-exact, `artifact["borrowed_cap"] == retention_cap(V20_RETENTION_NOISE_FLOOR)`,
`artifact["cap"] < artifact["borrowed_cap"]` asserted rather than narrated, `borrowed_floor_ratio`
re-derived, and the floor re-derived as `abs(delta_1337 - delta_2024)` from the two seeds' own
published `delta_on_minus_off` readings — bit-exact, and the only re-derivation CI can perform,
because `checkpoints/` and `data/` are gitignored (R-20-04). Each seed's `delta_on_minus_off` is
also checked against its own `adapter_on - adapter_off`.

`test_mitigation_point_verdict_has_no_caller_outside_this_module` — the name the shipped module
cites. AST-walks every `.py` under `scripts/` and `src/`, matching `getattr(node.func, "id", None)
or getattr(node.func, "attr", None)`, excluding the definition file and the sanctioned route BY NAME
rather than by lowering a count. **Zero bypassing callers today.** Proved non-vacuous by asserting
at least one match INSIDE `scripts/phase20_gate_coverage.py` (measured: exactly 1, at step 6 of
`corrected_point_verdict`). `tests/` is excluded deliberately and the reason is recorded in the
docstring: the prereg suite drives the pin's own branches directly, which is the pin's behavioural
twin and not a bypass of the correction.

## Watched-RED Evidence

Four deliberate breaks, each observed failing and each restored **byte-identically** — verified by
`shasum -a 256 -c` and by `git diff --exit-code`. These four rows are what `20-12` writes into
`20-SECURITY.md`'s Watched-RED table. No row below is written for a break that was not run.

| # | Threat | Deliberate break | Observed |
|---|---|---|---|
| 1 | T-20-21 | `coverage_verdict`'s extraction statistic flipped from `wilson_upper_bound(k, n)` to `k / n` | **BOTH direction tests failed.** Direction (i): `AssertionError: the corrected route returns 'INCONCLUSIVE' where the frozen block returns 'INCONCLUSIVE' … 2 clearing, 0 failing`. Direction (ii): `AssertionError: the corrected route returns 'FAIL' on a sweep where ZERO points clear X = 0.04535522866494124 (bounds (0.0699987834827904, 0.16574570864872762))` / `assert 'FAIL' == 'INCONCLUSIVE'`. `2 failed, 3 passed` |
| 2 | T-20-48 | `scripts/_scratch_bypass_probe.py` added, calling `mitigation_gate.mitigation_point_verdict(...)` — the `ast.Attribute` form | **Census fired:** `AssertionError: 1 call site(s) reach a v4.0 verdict through the frozen pin directly … ['scripts/_scratch_bypass_probe.py:7']` / `assert ['scripts/_sc...s_probe.py:7'] == []`. This is precisely the form `tests/test_phase19_erasure.py:1389`'s bare-name matcher would have missed (WR-07) |
| 3 | T-20-19 | the distinct-seed `_prove` deleted from `_prove_retention_floor` | **`Failed: DID NOT RAISE <class 'SystemExit'>`** on `test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` |
| 4 | T-20-51 | `results/phase20_retention_floor.json`'s `cap` edited by one digit | **WR-02 fired:** `AssertionError: the artifact publishes cap 3.908503237988479 but retention_cap on its own published floor returns 3.9085032379884783`. `1 failed, 10 passed` |

**Break 4 carries a measurement worth recording.** The first attempt edited the LAST printed digit
(`…4783` → `…4782`) and the test PASSED — because `3.9085032379884782 == 3.9085032379884783` is
`True`: those two decimal strings name the same IEEE double. The break was redone at the 16th
significant digit (`…4783` → `…4793`), the last position where a single-digit change survives the
round trip, and fired. The passing first attempt is not a hole in the guard: an "edit" below the
type's resolution changes no value any consumer could read, so there is nothing there to catch.

## Verification

| Check | Result |
|---|---|
| Task 1 verify (exit code, `>= 5` passed, zero skips/xfail) | `OK — 5 passed, zero skips` |
| Task 2 verify (exit code, `>= 8` passed, zero skips/xfail) | `OK — 8 passed, zero skips` |
| Task 3 verify (`>= 11` correction, EXACTLY 18 prereg, zero skips in both) | `OK — correction 11 passed, prereg 18 passed, zero skips` |
| `.venv/bin/python -m pytest -q` | **`874 passed, 1 skipped in 224.79s`** — the `863 passed, 1 skipped` baseline plus exactly the 11 tests added here, zero regressions |
| `ruff check .` / `ruff format --check .` | `All checks passed!` / `176 files already formatted` |
| `git diff --exit-code -- results/ scripts/` | exit 0, after all four watched-RED breaks were restored and after every task commit |

`tests/test_phase20_correction.py` is 957 lines and defines 11 `test_` functions — above the plan's
`min_lines: 200`.

## Task Commits

| Task | Commit | Files |
|---|---|---|
| 1 — both directions, the sealed route, the mirror bound | `2743b18` | `tests/test_phase20_correction.py` |
| 2 — additivity, re-derivation, defects still live | `da1aa77` | `tests/test_phase20_correction.py` |
| 3 — retention refusals, WR-02, the caller census | `3aca4b0` | `tests/test_phase20_correction.py` |

## Deviations from Plan

### 1. [Rule 2 — a shipped citation outranks a plan's prose] The census test is named `test_mitigation_point_verdict_has_no_caller_outside_this_module`

- **Found during:** Task 3, resolved from the code before Task 1 was written.
- **Issue:** the plan's action text names the census `test_no_path_to_a_v4_verdict_bypasses_the_correction`. But `scripts/phase20_gate_coverage.py` — SHIPPED at `21387a3` — cites `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module` twice, in the module docstring and in `corrected_point_verdict.__doc__`. `20-08-SUMMARY.md` records both cited names as inherited commitments. A shipped module citing a test that never gets written is the T-20-55 defect class.
- **Fix:** the cited name was used. One test, one name — an alias would be a second name for one guard and would leave a reader unable to tell which is the guard.
- **Not silently either way:** the plan's name is not used anywhere, and the divergence is recorded here and in this SUMMARY's `key-decisions`. The frozen half of the pair is the docstring, and it did not have to move.
- **Files modified:** `tests/test_phase20_correction.py`
- **Commit:** `3aca4b0`

### 2. [Rule 1 — a probe below the type's resolution] The `cap` watched-RED break was moved from the last printed digit to the 16th significant digit

- **Found during:** Task 3, watched-RED break 4.
- **Issue:** the plan says "edit `artifact["cap"]` by one digit and observe the WR-02 test fire". Editing the last printed digit (`3.9085032379884783` → `3.9085032379884782`) did NOT fire — MEASURED: `3.9085032379884782 == 3.9085032379884783` is `True`, so the "edit" produced the identical double and the artifact was unchanged in every sense a consumer could observe.
- **Fix:** the break was redone at the 16th significant digit (`…4783` → `…4793`), located by scanning from the right for the last position where a single-digit change survives `float(repr(x))`. It fired immediately. Both attempts are recorded above rather than only the one that worked.
- **Why this is not a hole:** a decimal edit below a double's resolution changes no value any reader can obtain, so the guard has nothing to catch there. Recording it matters because the obvious "change the last digit" probe would otherwise be read as evidence that the guard is weak.
- **Files modified:** `results/phase20_retention_floor.json` (temporarily; restored byte-identically, `shasum -a 256 -c` OK, `git diff --exit-code` clean)
- **Commit:** `3aca4b0`

### 3. [Rule 2 — recorded, not fixed] One published field is deliberately not re-derived

- **Found during:** Task 2.
- **Issue:** the plan requires every published number re-derived by calling the modules. `bound_direction.zero_successes_short_circuit.measured_residue_at_n_104` (`1.734723475976807e-18`) is the residue the NAIVE mirror leaves — and `wilson_lower_bound` deliberately short-circuits before computing it. Re-deriving it would mean writing `centre - spread` into the test: a second copy of exactly the estimator whose duplication T-20-53 forbids, introduced by the test that exists to prevent it.
- **Fix:** the short-circuit's OUTPUT is asserted instead (`wilson_lower_bound(0, 104) == 0.0`), which is the part any decision could read, and the reason is written at the assertion in the test file rather than only here.
- **Files modified:** `tests/test_phase20_correction.py`
- **Commit:** `da1aa77`

Three things worth recording that are *not* deviations:

1. **`gsd-sdk` state/roadmap mutation verbs were NOT called.** `.planning/STATE.md` and
   `.planning/ROADMAP.md` were hand-edited and the diff reviewed. Ninth consecutive session
   treating those handlers as unsafe in this repo.
2. **`requirements.mark-complete` was deliberately NOT run** for the plan's
   `requirements: [GATE-06, GATE-02]`. GATE-06 is `20-12`'s to discharge, and `20-12` has been told
   to discharge it against a RE-RUN rather than against a SUMMARY claiming a tripwire was watched.
   GATE-02 was already `[x]` and amended at `20-09`.
3. **The marker triple was read from the committed continuation, not from any plan.**
   `20-11-PLAN.md` carries no date of its own for the heading (it says "the exact strings from
   `20-10`"), so there was no stale assertion to correct — the carry-forward warning's contingency
   did not arise.

## Threat Model Outcomes

| Threat ID | Disposition | Outcome |
|---|---|---|
| T-20-21 | mitigate | **CLOSES HERE.** Both reproduced directions asserted RED against the frozen pin and GREEN through `corrected_point_verdict` in one differential body each, plus the third unreported case with its honest limit in the assertion text. The deliberate break (row 1) was watched failing BOTH direction tests and restored byte-identically. WR-09's held-out leg is covered by the same `coverage_verdict` and its truncation case is asserted at the payload's own `(0.30, 0.28)` sweep — reachable only because the helper uses the merge form. The raw-rate migration mistake is refused through the route, by message. |
| T-20-19 | mitigate | **CLOSES HERE.** Eight refusal cases driven THROUGH the verdict route with a positive control; the borrowed `0.06893` refused by identity under otherwise-clean provenance, with all three published numbers derived in the test; WR-08 proved at both `-0.01` and `-0.05` and asserted on the MESSAGE. One `_prove` deleted and watched firing (row 3). |
| T-20-48 | mitigate | AST census matching BOTH `.id` and `.attr`, proved non-vacuous by asserting a match inside the sanctioned module, and watched RED against a scratch bypassing caller written in the `ast.Attribute` form (row 2) — the exact form WR-07 records a bare-name matcher missing. `tests/` excluded deliberately, reason recorded in the docstring. |
| T-20-50 | mitigate | `SUPERSEDED_SWEEP_SENTINEL` asserted to fire NO GATE-06 reason on all three committed fixtures, so neutralising the superseded block is a proved property rather than an assumption. |
| T-20-51 | mitigate | Every published float re-derived by calling the modules; the artifact's `cap` edited and watched firing (row 4), with the sub-resolution first attempt recorded rather than hidden. |
| T-20-53 | mitigate | `is`-identity for `wilson_upper_bound` (function) and `F_Y` (float `0.7`); AST import-alias membership plus absence from module-scope `ast.Assign` targets for `MARGIN_K` and `EXTRACTION_FLOOR_MIN_SEEDS`, both the interned small int `2`. No `is` assertion is written for a small int. The residue exclusion above is this same discipline applied to the test itself. |
| T-20-57 | mitigate | `test_the_three_defects_are_still_live_in_the_frozen_pin` asserts each against the CODE with a message saying a green result means the continuation needs re-reading, not deleting. |
| T-20-59 | mitigate | Every audit in the file is an AST walk. No `grep -c` and no `X in source` substring check appears anywhere in it — the only substring assertions are on runtime `SystemExit` messages and on a published `.md`/`.json` artifact, never on source. |
| T-20-64 | mitigate | The additivity guard derives its revision from `git log --format=%H` and its blob from `git show <rev>:<path>`. `git ls-files` is never used. `recorded_verdict(after) is not None` proves the unchanged-verdict comparison non-vacuous. |
| T-20-65 | mitigate | All three verify blocks run pytest as a subprocess and assert the exit code, the extracted passing COUNT against the stated floor (5 / 8 / 11), the EXACT prereg count (18) and the absence of `skipped` / `xfail`. |

## Threat Flags

None. One CPU-only test module. No network surface, no endpoints, no schema, no trust-boundary
change. It reads three committed artifacts and shells out to `git` for read-only history queries
with an argv tuple (never `shell=True`), which is `tests/test_phase19_correction.py`'s existing
pattern.

## Known Stubs

None. Every test asserts; none returns early, skips, or records a state without an assertion that
would fail if the state changed.

## Notes for Future Plans

- **`20-12` can now discharge GATE-06 — but against a RE-RUN.** The four watched-RED rows above
  carry their observed output precisely so `20-12` does not have to take this SUMMARY's word for it;
  re-running the three verify blocks and `pytest -q` is cheap and is what the plan asks for.
- **`20-SECURITY.md`'s Watched-RED table takes exactly four new rows** (T-20-21, T-20-48, T-20-19,
  T-20-51). Do not write a fifth for a break that was not run.
- **The two cited test names are now load-bearing in both directions.** If either
  `test_wilson_bounds_are_exact_mirrors` or
  `test_mitigation_point_verdict_has_no_caller_outside_this_module` is ever renamed, the
  `scripts/phase20_gate_coverage.py` DOCSTRINGS must move in the same commit — they are the
  editable half of the pair, and the module is unpinned.
- **A Phase 23/25 driver that calls `mitigation_gate.mitigation_point_verdict` directly will turn
  this file red.** That is the intent. The route is
  `scripts/phase20_gate_coverage.py::corrected_point_verdict`, and its `sweep_extraction_*`
  parameters take COUNTS and QUESTIONS, never rates.

## Self-Check: PASSED

- `tests/test_phase20_correction.py` — FOUND (957 lines, 11 `def test_` functions)
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-11-SUMMARY.md` — FOUND
- commit `2743b18` — FOUND
- commit `da1aa77` — FOUND
- commit `3aca4b0` — FOUND
- `scripts/mitigation_gate.py`, `scripts/erasure_gate.py`, `scripts/phase20_gate_coverage.py`,
  `results/phase20_retention_floor.json`, `results/phase20_gate_coverage_correction.{md,json}` —
  all byte-identical to `1284fe2` (pre-plan HEAD); `git diff --exit-code -- results/ scripts/`
  exit 0
