---
phase: 20-pre-registration-the-three-condition-gate
plan: 14
subsystem: gate-correction
tags: [pre-registration, gate-06, coverage-correction, gap-closure-wave-2, watched-red]
requires:
  - "20-13 (D-40, the decision this plan implements; the register at status: blocked / threats_open: 1)"
  - "20-REVIEW-GAP-CLOSURE.md GC-03 (blocker) and GC-04 (warning) — the review wrote both fixes"
  - "20-VERIFICATION.md gap 1 item 2 — the tripwire this plan arms"
provides:
  - "A per-element [0.0, 1.0] value guard on BOTH Y sweep legs inside coverage_verdict, placed before x_uppers so no value reaches the axis loop unvalidated"
  - "The RATE-vs-COUNT guard enforced BY TYPE — isinstance(k, int) and not isinstance(k, bool)"
  - "The measured route-level differential armed as a tripwire, with the pre-guard PASS recorded in the assertion message"
  - "Two watched-RED breaks with byte-identical restores, for 20-SECURITY.md's Watched-RED table"
affects:
  - "20-17 — the re-close to threats_open: 0 is gated on watched-RED evidence; T-20-71..T-20-74 are discharged here"
  - "Phase 23, where sweep width is set and Y coverage stops being hypothetical"
tech-stack:
  added: []
  patterns:
    - "A guard's message is an ARGUMENT, not a label: it names the mechanism, the measurement and what the caller must do"
    - "Deliberate asymmetry stated IN the message, so a later reader does not 'restore the symmetry' and break one of the two legs"
    - "Constants interpolated from the module (SUPERSEDED_SWEEP_SENTINEL), never retyped and never cited by a self-referential line number"
    - "Differential asserted in ONE body: the honest axis reaches a finding, the more-truncated axis is refused"
key-files:
  created: []
  modified:
    - "scripts/phase20_gate_coverage.py"
    - "tests/test_phase20_correction.py"
decisions:
  - "The count-guard message cites SUPERSEDED_SWEEP_SENTINEL by NAME and interpolates its VALUE, not by the plan's '166 lines below' — measured 176 after this plan's own edits, i.e. the plan's figure was falsified by the very edit that would have written it"
  - "Task 3 produces no diff by construction, so it gets no commit; its output is evidence, published here"
metrics:
  duration: "~40 min"
  tasks_completed: 3
  commits: 3
  completed: 2026-08-21
---

# Phase 20 Plan 14: The Y-Leg Value Guards and the Count Guard by Type Summary

Closed GATE-06's Y clause (GC-03) and GC-04 by giving `sweep_taught_recalls` / `sweep_heldout_recalls`
the per-element discipline the extraction axis already had, enforcing the success-count unit by type,
and arming the measured `INCONCLUSIVE`→`PASS` flip as a route-level tripwire — then watching both new
guards fail before trusting either.

## What Was Built

**Task 1 — `scripts/phase20_gate_coverage.py`** (`86f7a55`, 35 lines changed). Two edits, nothing
else in the file:

- **(a)** One loop over both Y legs, taught first and held-out second (matching
  `COVERAGE_STATISTIC_BY_AXIS`'s order), inserted between the recall-length `_prove` and the
  `all(n > 0 ...)` `_prove`, predicate
  `all(isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in values)`. It sits **before** the
  `x_uppers` comprehension, so no value reaches `wilson_upper_bound` or the axis loop unvalidated.
- **(b)** `whole = isinstance(k, int) and not isinstance(k, bool)`, replacing the integral-float
  acceptance. The existing RATE-vs-COUNT message is **extended, not rewritten** —
  `tests/test_phase20_correction.py:346` asserts its wording carries `RATE` and `COUNT`.

**Task 2 — `tests/test_phase20_correction.py`** (`2818fed`, +137 lines, 0 deletions to any existing
test). Two new functions placed after `test_the_sanctioned_route_cannot_be_handed_raw_rates`, taking
the file from 11 to 13 test functions. Both are runtime-message assertions; no `grep -c` and no
`X in source` audit appears (RPT-02).

**Task 3 — two watched-RED breaks.** No diff by construction, therefore no commit; see the
Watched-RED table below.

## The Measured Differential — Re-Derived Here, Not Transcribed

Every row below was produced by calling the committed modules. `FIXTURE_CLEARING_POINT` at the
`(1, 3)` / `(104, 104)` sweep, with the fixture's own `sweep_taught_recalls = (0.45, 0.2)` — which
legitimately brackets `y_taught = 0.35`, so the held-out leg is the only axis under test:

```
X          = 0.04535522866494124   (by CALLING extraction_ceiling, never typed)
y_taught   = 0.35
y_heldout  = 0.24499999999999997
nan >= y_heldout                 -> False      <- the mechanism
0.0 <= float("nan") <= 1.0       -> False      <- why the range check subsumes NaN
```

`corrected_point_verdict`, **BEFORE** (measured at `576b57d`) and **AFTER**:

| input                                     | before                          | after                    |
| ----------------------------------------- | ------------------------------- | ------------------------ |
| held-out `(0.30, 0.28)` — honest          | `INCONCLUSIVE`, GATE-06 at `[4]` | `INCONCLUSIVE`, GATE-06 at `[4]` — **unchanged** |
| held-out `(nan, 0.28)` — strictly MORE truncated | **`PASS`, no GATE-06 reason** | `SystemExit` |
| held-out `(42.0, -99.0)`                  | **`PASS`, no GATE-06 reason**   | `SystemExit`             |
| taught `(-99.0, 42.0)`                    | **`PASS`**                      | `SystemExit`             |
| counts = `SUPERSEDED_SWEEP_SENTINEL`      | **`INCONCLUSIVE`** (spurious demotion) | `SystemExit` naming `RATE`/`COUNT` |
| counts = `(True, False)`                  | **`INCONCLUSIVE`** (spurious demotion) | `SystemExit` naming `RATE`/`COUNT` |
| control: held-out `(0.30, 0.20)`          | `PASS`                          | `PASS`                   |
| control: counts `(1, 3)`                  | `PASS`                          | `PASS`                   |

At `coverage_verdict` level the before-state is starker still: `(nan, 0.28)` returned
`(True, ())` — **fully covered, zero truncated axes** — while the strictly LESS truncated
`(0.30, 0.28)` returned `(False, ('heldout_recall',), <sentence>)`. The NaN did not pass through;
it **manufactured** the bracket, because `nan >= 0.24499999999999997` is `False` and it was
therefore counted as a *failing* point beside `0.28`'s clearing one.

Both controls confirm the four aborts are attributable to the new guards rather than to anything
else in the route.

## Watched-RED Evidence — Both Guards OBSERVED Failing

Pre-break digest of `scripts/phase20_gate_coverage.py`, recorded before either break:
`49bda8925c1e7a93ca6a903f6c5a535a15f869ebcc63bd7de9e10a63b9beaef0`

| # | What was broken | Command | Observed output | Restore proof |
|---|---|---|---|---|
| 1 | The entire per-element Y `_prove` loop deleted, both legs (`git diff --stat`: 21 deletions) | `.venv/bin/python -m pytest tests/test_phase20_correction.py -q` | `FAILED tests/test_phase20_correction.py::test_a_recall_outside_the_unit_interval_cannot_manufacture_y_coverage` — `E Failed: DID NOT RAISE <class 'SystemExit'>` at `tests/test_phase20_correction.py:434`. **`1 failed, 12 passed in 0.35s`** | `shasum -a 256` → `49bda892…beaef0` (**equal**); `git diff --exit-code -- scripts/phase20_gate_coverage.py` → **0** |
| 2 | `whole` reverted to `isinstance(k, int) or (isinstance(k, float) and k.is_integer())` | same | `FAILED tests/test_phase20_correction.py::test_the_modules_own_rate_space_sentinel_cannot_pass_as_counts` — `E Failed: DID NOT RAISE <class 'SystemExit'>` at `tests/test_phase20_correction.py:494` | `shasum -a 256` → `49bda892…beaef0` (**equal**); `git diff --exit-code -- scripts/phase20_gate_coverage.py` → **0** |

**Failure attribution, checked rather than assumed.** A sibling plan in this phase once shipped a
break that reddened a *pre-existing* assertion — Python stops at the first failure, so the intended
assertion was never evaluated and the row would not have been evidence. Both rows above were checked
against that failure mode:

- **Break 1** failed at **case 3** of the new body. Cases 1 and 2 — the honest `(0.30, 0.28)`
  finding and the `not (nan >= y_heldout)` mechanism — both **evaluated and passed** first, which is
  correct: neither depends on the deleted guard. The `DID NOT RAISE` is the new NaN refusal and
  nothing else.
- **Break 2** failed at the **first iteration** of the sentinel loop, on
  `SUPERSEDED_SWEEP_SENTINEL` itself — the new assertion, in the new test.

Each break reddened **exactly one** test, which is what this plan predicted. Neither break was ever
staged: `git status --porcelain scripts/` measured **0** dirty files at commit time.

## Verification Evidence — Every Must-Have, By A Command Actually Run

| Must-have | Command output |
|---|---|
| `(nan, 0.28)` raises, `(0.30, 0.28)` returns `(False, ('heldout_recall',), <str>)` | plan's Task-1 verify script → `ok`; return types measured `bool` / `('heldout_recall',)` / `str` |
| refusal message names the leg, `[0.0, 1.0]`, `nan` and `failing point` | `nan in msg: True` · `failing point in msg: True` · `held-out named: True` · `[0.0, 1.0] in msg: True` |
| route RAISES at `(nan, 0.28)` and `(42.0, -99.0)`, no longer `PASS` | see the differential table above — all four Y cases `SystemExit` |
| `SUPERSEDED_SWEEP_SENTINEL` and `(True, False)` refused as counts | `sentinel: RATE=True COUNT=True sentinel-value-in-msg=True` |
| bools admitted on the recall legs | `coverage_verdict(..., sweep_taught_recalls=(True, False), ...)` returns a bool verdict, does not raise |
| both guards observed RED, module restored byte-identically | Watched-RED table above — digest equal twice, `git diff --exit-code` → 0 twice |
| frozen pins untouched | `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` → **0**; `git diff HEAD~2 --stat` on the same two paths → **empty** |
| phase-20 pair | `31 passed in 2.04s`; summary line grepped for `skipped`/`xfail` → **neither present** |
| new tests by explicit node id | `2 passed in 0.05s` |
| AST function-count audit | `13 test functions, new one present` |
| `grep -c 'float("nan")' tests/test_phase20_correction.py` | `2` |
| full suite | **`876 passed, 1 skipped, 83 warnings in 200.61s`** |
| lint | `All checks passed!` / `176 files already formatted` |
| ancestry guard unaffected | `-k phase20_prereg_is_frozen` → `1 passed, 17 deselected in 1.05s`; by node id `test_phase20_prereg_is_frozen_before_every_phase20_result` → `1 passed` |

**The full-suite number, reconciled against the real baseline.** The plan's `must_haves` predicted
"at least 876 passed" — that is the plan's forecast of its own additions, not a pre-existing count.
The measured pre-existing baseline at `576b57d` is **874 passed / 1 skipped**. This plan adds exactly
two test functions, and `874 + 2 = 876`. The measured **876 passed / 1 skipped** therefore reconciles
against the baseline, not merely against the prediction.

## Deviations from Plan

### Auto-fixed Issues

None. No bug, no missing critical functionality and no blocking issue was encountered; the plan's
two edits applied as specified and the pre-existing 29-test phase-20 suite was green after Task 1
without any correction.

### Plan-vs-Reality Mismatches Recorded, Not Amended

1. **"defined 166 lines below" — FALSIFIED by the edit that would have written it.** The plan's
   Task 1(b) asked the count-guard message to state that `SUPERSEDED_SWEEP_SENTINEL` is *"a
   rate-space pair defined 166 lines below"*. 166 was correct **before** this plan ran (`whole` at
   `:257`, the sentinel at `:423`). Edit (a) inserts 21 lines above `whole` and edit (b) adds 10
   lines to the message itself, so the measured delta at commit time is
   **`whole` at `:278`, sentinel at `:454`, delta = 176** — the number would have been false the
   instant it was typed. This file is **unpinned**, so every future edit moves it again; a
   self-referential line delta here is exactly the anchor-rot `20-13` recorded five instances of.
   **Taken instead:** the message cites the constant BY NAME and interpolates its VALUE from the
   module (`{SUPERSEDED_SWEEP_SENTINEL}` → `(0.0, 1.0)`), and says *"defined below in this same
   file"*. Strictly better than the plan asked for: a later change to the constant now travels into
   the refusal message rather than leaving it asserting a stale pair.

2. **Task 3 has no commit, because it has no diff.** The plan gives Task 3
   `<files>scripts/phase20_gate_coverage.py</files>` and instructs *"Commit only after both restores
   are verified — the breaks must never reach a commit."* Both restores are byte-identical, so the
   task's net diff is empty and there is nothing to commit. Its output is **evidence**, and it lives
   in the Watched-RED table above. This plan therefore lands **two code commits plus one docs
   commit**, not three code commits.

3. **The `<verification>` block's `-k` selector, and a node id that did not exist.** The plan
   specifies `pytest tests/test_phase20_prereg.py -q -k phase20_prereg_is_frozen`. It selects
   **1 test, 17 deselected** — non-zero, so it is not the silent-zero case. But the guard's real
   node id is `test_phase20_prereg_is_frozen_before_every_phase20_result`; a first guess at
   `test_phase20_prereg_is_frozen_at_its_first_commit` collected **zero** tests and pytest reported
   `no tests ran in 0.01s`. Recorded because it demonstrates the asymmetry the repo's own hazard
   register names: an explicit node id fails loudly where a mistyped `-k` passes silently. Both
   forms are run above.

4. **`20-SECURITY.md:39`, cited in this plan's `<threat_model>`, is stale.** Per `20-13`'s measured
   drift map the trust boundary *"a plan that says a thing will be done ↔ a guard that proves it
   was"* moved from `:39` to `:43`. No stale anchor is written anywhere in this SUMMARY: that
   boundary and the *"a coverage finding produced by the DATA ↔ one produced by the INPUT"* boundary
   are both referred to **by text**. The second one's in-code statement is the
   *"a coverage finding attributed to the data when it was produced by the criterion"* `_prove`
   message, which this plan extends to the two axes the last gap closure added.

**Not touched, deliberately:** `STATE.md`, `ROADMAP.md` and `REQUIREMENTS.md` are absent from the
plan's `files_modified`, so no `gsd-sdk` `state.*` or `roadmap.*` mutation handler was invoked and
`GATE-06` was not marked complete — the register is deliberately still `status: blocked` /
`threats_open: 1`, and `20-17` owns the re-close. `.planning/` is otherwise untouched by the two
task commits.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file access and no schema; it runs no
package-manager install; `scripts/phase20_gate_coverage.py` remains stdlib plus two sibling scripts
and `pyproject.toml` is untouched (T-20-SC, accepted, holds). The plan's own register is discharged
rather than deferred:

- **T-20-71** (a Y coverage finding manufactured by the input) — mitigated by edit (a), placed before
  `x_uppers`; the range check subsumes NaN with no special-case branch a later reader can delete.
- **T-20-72** (a guard written but never watched failing) — mitigated; both breaks applied, observed,
  and restored with digest equality plus `git diff --exit-code`.
- **T-20-73** (a tripwire that loses the record of the flip it prevents) — mitigated; the honest
  finding, the mechanism and the refusal are asserted in one body, with the pre-guard `PASS` and
  `(True, ())` recorded in the assertion message.
- **T-20-74** (the module's own rate-space sentinel passing as a count) — mitigated by edit (b), with
  the sentinel read from `coverage.SUPERSEDED_SWEEP_SENTINEL` and never retyped.

## Known Stubs

None.

## Self-Check: PASSED

- `scripts/phase20_gate_coverage.py` — FOUND, both edits present, digest `49bda892…beaef0`
- `tests/test_phase20_correction.py` — FOUND, 13 test functions, both new names present
- `86f7a55` — FOUND
- `2818fed` — FOUND
