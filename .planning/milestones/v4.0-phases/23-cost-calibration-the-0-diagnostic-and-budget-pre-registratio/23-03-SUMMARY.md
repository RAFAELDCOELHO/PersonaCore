---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 03
subsystem: pre-registration
tags: [pre-registration, ancestry-guard, edit-once, blind-rule, dpsgd-06, d-03, d-04, d-06]

requires:
  - phase: 20-pre-registration-of-the-three-condition-gate
    provides: "tests/test_phase20_prereg.py::_assert_ordering_holds — the parameterized ancestry body (strict-ancestor conjunct + adds[-1] earliest-add + bool(checked)==bool(tracked)), imported and CALLED here rather than copied"
  - phase: 20-pre-registration-of-the-three-condition-gate
    provides: "scripts/mitigation_gate.py's FROZEN extraction-floor provenance contract — NEVER_TAUGHT_ARM, EXTRACTION_FLOOR_MIN_SEEDS = 2, EXTRACTION_FLOOR_PROVENANCE_KEYS — the refusal register this module's messages mirror and the constraint choose_n_seeds must satisfy by construction"
  - phase: 19-selective-erasure
    provides: "scripts/phase19_floor.py's property 2 — 'a reduction chosen in the artifact writer is a reduction chosen with the numbers already visible' — the sentence that forces this module into wave 1"
provides:
  - "scripts/phase23_prereg.py — the EDIT-ONCE module carrying D-03's blind reduction, D-03's blind seed-count rule, D-04's halt verdict, D-06's withdrawal rule and the canonical results/phase23_* path register"
  - "noised_record_path(arm, sigma) — the single derivation for every σ>0 sweep-point path, with a round-trip refusal so two sigmas cannot collide on one filename"
  - "H_PER_POINT_FLOOR_SECONDS = 17_175 with its unrounded derivation and the REQUIREMENTS row named as the restatement rather than the source"
  - "tests/test_phase23_prereg.py — 32 tests: both D-04 branches incl. beats-the-control, a permanent watched-RED halt control, the ULP-nudge floor refusal, per-key provenance refusals, the seed rule's four boundaries + three refusals, three ancestry guards, three throwaway-repo RED-then-GREEN fixtures, the outside-the-prefix scan, and the content-side noised-glob guard with both escape routes watched failing"
affects: [23-04 imports n64_leg_is_committable and CAL03_WIRING_RECORD, 23-08 imports choose_n_seeds and H_PER_POINT_FLOOR_SECONDS, 23-10 imports sigma_zero_verdict and SIGMA_ZERO_RECORD, 23-11 imports noised_record_path and COST_RECORD, 23-13 prices N_CONTROL_SEEDS into Z, 23-14 writes NEVER_TAUGHT_RECORD, every later Phase-23 plan resolving an artifact path]

tech-stack:
  added: []
  patterns:
    - "an EDIT-ONCE pre-registration module whose own ancestry guard makes any later edit permanently RED — the scripts/mitigation_gate.py mechanism, applied deliberately and stated in the file's own docstring"
    - "one derivation module as the SINGLE SOURCE of every results/ path a phase writes, in teach_persona.fact_bin_path's register"
    - "a wave-1 rule that is arithmetic over its caller's values, so it can decide a wave-6 measurement without importing the module that takes it"
    - "content-side glob membership: a record's presence under a path glob is a consequence of what its payload declares, and SILENCE on a non-schema-required key is a refusal rather than a third exemption"
    - "_prove/SystemExit refusals throughout — never assert, which python -O strips"

key-files:
  created:
    - scripts/phase23_prereg.py
    - tests/test_phase23_prereg.py
  modified: []

key-decisions:
  - "23-03: the reduction is the RANGE max-min, pinned with its reasoning before any reading exists — a spread, not a dispersion estimate, because the consumer asks 'could this have come from seed variation alone' and at N in {3,4,5} a stdev is badly estimated while a range is the conservative answer; and the conservative direction is the recoverable one"
  - "23-03: choose_n_seeds lives HERE and not in the driver that measures the scoring cost deciding it — that driver is re-edited by 23-08 T2/T3, 23-10, 23-11 and 23-14, so git log -1 on it returns its most recent commit and no ancestry check could bind a rule there to anything"
  - "23-03: D-04 has no warning branch and no override flag; the HALT fires in BOTH directions and 'beats the control' is asserted separately, because every correctness bug in this class improves utility"
  - "23-03: the floor must re-derive under exact == rather than be bounded by magnitude — the one-ULP nudge is refused BY CONSTRUCTION, which is a stronger closure of GATE-02's defect class than 20-15's magnitude bound could be here"
  - "23-03: the central reading is control_readings[0], the FIRST recorded seed — a choice with no post-hoc freedom, unlike a mean over the very readings the floor was reduced from, which would let the floor and the centre move together"
  - "23-03: a σ>0 record carrying NO sweep_point key is REFUSED, never exempted — sweep_point is not schema-required, so without that line the escape moves from 'wrong filename' to 'missing key', and a wrong filename is a choice somebody made while an omission requires no lie at all"
  - "23-03: globs=(artifact_glob,) is passed rather than widening V4_ARTIFACT_GLOBS — Phase 21 D-20 measured that globs is read in exactly one place, and these three guards bind a different pair of endpoints than the accountant's"
  - "23-03: DPSGD-06 NOT marked complete — σ=0 has not been executed; this plan commits the ordering guard, and 23-06/23-07/23-08/23-10 own the rest"

patterns-established:
  - "A pre-registration that will be consumed by N later plans declares every path and every rule ahead of need, because its own guard makes adding one later impossible"
  - "Where a guard binds on a NAME, ask what a record's CONTENT could say that the name does not — and treat silence on a non-required key as a refusal"

requirements-completed: []
requirements-advanced:
  - "DPSGD-06 (the ORDERING half only — NOT marked complete): the requirement is that σ=0 IS the DP arm's first executed run. Nothing has been executed. What landed is test_sigma_zero_precedes_every_noised_point, which makes that ordering checkable against git's object graph from the first artifact onward, plus the content-side guard that stops a σ>0 sweep point exempting itself by filename or by omission. 23-06, 23-07, 23-08 and 23-10 also carry DPSGD-06; 23-10 executes σ=0."

duration: 28min
completed: 2026-08-26
---

# Phase 23 Plan 03: The Blind Pre-Registration Summary

**Every rule Phase 23 will be judged by — the noise-floor reduction, the seed count, the halt verdict, the withdrawal rule and every artifact path — is now committed in one EDIT-ONCE module while `git ls-files 'results/phase23_*'` returns nothing, with three ancestry guards that turn "committed blind" into a property of git's object graph and a content-side guard that stops a σ>0 sweep point exempting itself either by filename or by saying nothing.**

## Performance

- **Duration:** 28 min (bounded above: the previous plan's final `STATE.md` stamp is `2026-08-26T23:18:16.572Z` and this plan's metric was recorded at `23:46:13.887Z` — 27 m 57 s)
- **Tasks:** 3
- **Commits:** 3 task commits + this metadata commit
- **Suite:** 1398 passed, 1 skipped (baseline 1366 + 32 new; the skip is the pre-existing CUDA-only fp16 AMP smoke at `tests/test_train_loop.py:81`)

## The State at Commit Time — recorded, not asserted

```
$ git ls-files 'results/phase23_*'
                                     # (empty)
$ git ls-files 'results/phase23_*' | wc -l
0
```

Verified before Task 1's commit and again before Task 3's. Every rule below therefore precedes
every Phase-23 reading, and `test_the_prereg_rule_precedes_every_phase23_result` will hold that
true from 23-04's first artifact onward.

## What Was Built

### Task 1 — `scripts/phase23_prereg.py`, the blind rules (`c7de5d4`)

**(a) The artifact register.** Seven constants, each commented with the plan that writes it and the
consumer that reads it: `CAL03_WIRING_RECORD`, `CONTROL_FLOOR_RECORD`,
`NEVER_TAUGHT_TRAINING_RECORD`, `NEVER_TAUGHT_RECORD`, `SIGMA_ZERO_RECORD`, `COST_RECORD`,
`NOISED_RECORD_PREFIX` → `NOISED_RECORD_GLOB`. Plus `noised_record_path(arm, sigma)`, a DERIVATION
in `teach_persona.fact_bin_path`'s register:

```
noised_record_path("dp_n64", 0.5)
  -> "results/phase23_noised_dp_n64_sigma0p500000.json"
```

σ is rendered at six decimals with the point written `p`, and the rendering is **refused unless it
round-trips** (`float(rendered) == float(sigma)`). Two sigmas differing below that precision would
otherwise collide on one filename and the second run would silently overwrite the first — a lost
measurement rather than a visible error. `arm` is refused unless alphanumeric-plus-`-`/`_`, so a
path separator cannot place a sweep point outside `results/` where every guard is blind to it. σ ≤ 0
is refused outright: σ=0 has its own record and must not be filed under the glob it is required to
precede.

**The edit-once consequence is stated in the file, not only in the plan.** The docstring says that
from 23-04's commit onward any edit turns `test_the_prereg_rule_precedes_every_phase23_result`
permanently RED with no recovery path — `adds[-1]` is the earliest add, so delete-and-re-add cannot
launder it — and names `scripts/_addendum.py` as the route for a correction: a dated additive
continuation published elsewhere, never an edit here. It also records that anything outside the
`results/phase23_` prefix falls outside the guard at `tests/test_phase20_prereg.py:332` **entirely**,
and that `CAL03_WIRING_RECORD` sits outside `NOISED_RECORD_GLOB` because its own record declares
`sweep_point: false` — a property of its content, not of its name.

**(b) `noise_floor(readings)` — the range**, `max - min`, pinned with its reasoning: the consumer
asks *could this difference have come from seed variation alone*, and at N ∈ {3,4,5} a stdev is
badly estimated while a range is the conservative answer. It is deliberately the larger of the two,
because a floor that is too tight halts a correct sweep while a floor that is too loose admits a
broken one, and only the second is unrecoverable. Fewer than two readings is refused in
`mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS`'s own words (*a single-seed floor is NOT a noise floor,
it is ONE DRAW*); a non-finite reading is refused because `max - min` over a NaN returns a NaN that
compares False against everything and would turn the halt into a silent pass.

**(c) `sigma_zero_verdict(...)` — D-04.** Returns the string `"proceed"` or raises `SystemExit`.
There is no third outcome, no warning branch and no override flag, and the docstring says D-04
commits to that before any number exists. Three refusals fire before the comparison: provenance must
be a mapping carrying every key in `FLOOR_PROVENANCE_KEYS` (refused, never defaulted, with the
missing key named); `floor == noise_floor(control_readings)` under exact `==`; and the σ=0 reading
must be finite. The central reading is **pinned** to `control_readings[0]`, the first recorded seed —
a choice with no post-hoc freedom, unlike a mean over the readings the floor was reduced from. The
halt message quotes both readings, the deviation, the floor, `floor_provenance["record"]` and the
direction, and states the asymmetry that motivates it.

**(d) `n64_leg_is_committable(...)` — D-06.** `epsilon_n8 == epsilon_n64 and t_n8 == t_n64`, exact
`==`, never a relative tolerance: the two arms are the same call shape at fixed σ, not two
independent mathematics, so any tolerance would admit exactly the leak the check exists to catch.
The docstring records that the T assertion adds no detection power (ε is monotone in T at fixed σ)
and exists to name *where* a leak lives, and that falsification withdraws the n=64 leg only — the
n=8 leg stays intact and publishable, which is what separates this from D-04's halt.

**(e) `H_PER_POINT_FLOOR_SECONDS = 17_175` and `choose_n_seeds(seconds_per_seed)`.** The constant's
comment carries the arithmetic that re-derives it:

```
23-RESEARCH.md §R3.0, "Reproduction of 4.77 h/point":
    PER ARM 42480 draws, 286.26 min = 4.7710 h
    286.26 min x 60 = 17,175.6 s  ->  17_175

.planning/REQUIREMENTS.md K=48 row (4.77 h):
    4.77 h x 3600 = 17,172 s   <- the ROUNDED RESTATEMENT, three seconds off, NOT the source
```

and states the **floor** status (CAL-05: measured on the un-adapted base where 45–56 of 64 draws per
shape stop-terminated; a heavily-noised adapter runs the full `max_new_tokens=48` every draw). It
also states explicitly that this is **not** the `h_per_point_floor`/`h_per_point_ceiling` keys 23-05
defines and 23-11 measures — those are this phase's own re-measurement; this is the pre-existing
budget unit, frozen so a wave-1 rule need not depend on a wave-6 measurement.

`choose_n_seeds` returns the largest N in `(5, 4, 3)` whose `N * seconds_per_seed` fits the bound,
and **never below 3** — when even three seeds overrun, it returns 3 and the caller records the
overrun. The docstring says so, so nobody later reads the floor of 3 as a bug. Zero, negative and
non-finite costs are refused with the value named.

**(f) The `__main__` self-check**, in `mitigation_gate.py`'s register but with `_prove` instead of
`assert` — the same reason the rest of the file uses it:

```
$ .venv/bin/python scripts/phase23_prereg.py
[phase23_prereg] 1/4 proceed — σ=0 exactly on the floor 0.03999999999999998 is admitted
[phase23_prereg] 2/4 HALT — observed firing:
[phase23_prereg] D-04 HALT — THE SWEEP IS HALTED: zero noised points will run.
  σ=0 reading      : 0.7999999999999998 (BEATS the control)
  control central  : 0.4 (reading at the FIRST recorded seed)
  deviation        : 0.3999999999999998
  noise floor      : 0.03999999999999998
  floor record     : results/phase23_control_floor.json
  σ=0 must reproduce the unmitigated control inside the seed-to-seed floor. It does not. The cause
  must be ROOT-CAUSED AND FIXED before any noised point runs — this is not a warning and there is
  no override flag. ...
[phase23_prereg] 3/4 N=5 — 3435.0s/seed, 17175.0s <= 17175s
[phase23_prereg] 4/4 N=3 — 34350.0s/seed OVERRUNS the bound (103050.0s > 17175s); D-03's floor of 3
  outranks it and the CALLER records the overrun
$ echo $?
0
```

The in-floor case is driven **exactly on** the floor, so the inclusive edge is the case that is
exercised rather than a comfortable interior point.

### Task 2 — both D-04 branches, the boundaries, and the watched RED (`e81dff9`)

`test_floor_breach_halts_the_sweep` asserts all three: `"proceed"` inside the floor; a `SystemExit`
naming `HALT`, `zero noised points` and the record path when σ=0 **misses**; and a separate
assertion, with its own message, when σ=0 **beats** the control by more than the floor. Both breach
directions come from one `_breach_case(beats=...)` constructor so they differ in exactly the
direction and in nothing else — two hand-built fixtures would be free to differ somewhere the
assertion does not look.

`test_the_halt_branch_is_watched_red_under_a_no_op_verdict` is the permanent control. A locally
defined `weakened_verdict` returning `"proceed"` unconditionally — the "downgrade the halt to a
warning" mutation D-04 forbids — is shown **not** to raise on the same breach fixture the real rule
halts on. Both run on the same inputs, so it measures the rule rather than the fixture, and it runs
on every suite run rather than once by hand.

The rest: a floor one ULP off (`math.nextafter`) refused with **both** floors published, and the
honest floor on the same reading still admitted so the refusal is one-sided; every one of the eight
`FLOOR_PROVENANCE_KEYS` parametrized, dropped, refused and named; a non-mapping provenance refused;
single-seed and non-finite readings refused with two readings still admitted; the four
`n64_leg_is_committable` cases with the one-ULP ε asserted `False`; and the four `choose_n_seeds`
boundaries, **every cost computed as `H_PER_POINT_FLOOR_SECONDS / divisor`** — `grep -c
"17175\|17_175\|17,175" tests/test_phase23_prereg.py` returns **0**.

### Task 3 — the ancestry guards (`11ba67a`)

`_assert_ordering_holds` and `_git` are **imported from `test_phase20_prereg` and called**, never
copied — a lookalike copy proves something about a different function than the one CI executes.
`grep -c "_assert_ordering_holds"` is 8.

`_ordering_guard(...)` wraps the helper in the Phase-18 vacuity shape and the wrapper is **required
rather than cosmetic**: two of the three `prereg_artifact`s (`CONTROL_FLOOR_RECORD`,
`SIGMA_ZERO_RECORD`) do not exist yet, and the helper asserts `prereg_commits` non-empty — so an
unconditional call would be Phase 16's shape, RED from this commit until an artifact lands,
inverting the very ordering the discipline establishes. The closing `bool(checked) == bool(tracked)`
stops the vacuity surviving the artifacts' arrival, and "the pin does not exist while artifacts do"
is its own named red rather than folded into the equivalence.

Three live guards:

| Guard | prereg_artifact | artifact_glob | What it makes checkable |
|---|---|---|---|
| `test_the_prereg_rule_precedes_every_phase23_result` | `scripts/phase23_prereg.py` | `results/phase23_*` | D-03 blind, for `noise_floor` and `choose_n_seeds` alike — and this is what makes the module edit-once |
| `test_control_precedes_sigma_zero` | `CONTROL_FLOOR_RECORD` | `SIGMA_ZERO_RECORD` | D-03: the floor was in the repository before the reading it judges existed |
| `test_sigma_zero_precedes_every_noised_point` | `SIGMA_ZERO_RECORD` | `NOISED_RECORD_GLOB` | DPSGD-06: σ=0 is the DP arm's first executed run |

`globs=(artifact_glob,)` is passed deliberately and `V4_ARTIFACT_GLOBS` is untouched: Phase 21 D-20
measured that `globs` is read in exactly one place — the `assert artifact_glob in globs` consistency
check — while the ordering loop runs on the singular `artifact_glob`, and these three guards bind a
different pair of endpoints than the accountant's guard that already carries `results/phase23_*`.

**Each prefix observed BITING**, in its own throwaway repository, parametrized over all three
endpoint pairs:

```
test_the_phase23_ordering_guards_are_red_then_green[scripts/phase23_prereg.py-results/phase23_*-results/phase23_probe.json] PASSED
test_the_phase23_ordering_guards_are_red_then_green[results/phase23_control_floor.json-results/phase23_sigma_zero.json-results/phase23_sigma_zero.json] PASSED
test_the_phase23_ordering_guards_are_red_then_green[results/phase23_sigma_zero.json-results/phase23_noised_*-results/phase23_noised_dp_n64_sigma0p500000.json] PASSED
```

Each case commits the artifact first and the pin second, asserts `git ls-files <glob>` matched the
committed path — a **positive observation** of the glob, without which a swapped `artifact_glob`
would pass silently — then observes `CalledProcessError` with `cmd[:3] == ("git", "merge-base",
"--is-ancestor")` so an incidental git failure cannot satisfy the `raises`. A **second** scratch
repository commits them in the right order and the guard passes. Two repositories rather than one
repaired in place, deliberately: the red is not repairable by re-committing, which is the property
`adds[-1]` buys and the reason the real module is edit-once. The third case's artifact path is
produced by `noised_record_path`, so the fixture rehearses the same derivation 23-11 will call.

`test_no_phase23_artifact_sits_outside_the_prefix` scans `git ls-files 'results/*'` by **basename**,
so a file that names the phase and misses the prefix is caught rather than being structurally
invisible.

**The filename escape, and the escape one level down.**
`test_every_noised_sweep_point_is_under_the_noised_glob` loads every tracked
`results/phase23_*.json` and runs one predicate over each payload. A record carrying `sigma > 0` and
`sweep_point is True` must match `NOISED_RECORD_GLOB` via `fnmatch.fnmatch` **against the imported
constant**, never a re-typed pattern. And a record carrying `sigma > 0` with **no** `sweep_point` key
is a **refusal, not an exemption** — `sweep_point` is not schema-required (23-05's
`TRAINING_RECORD_KEYS` and `GENERATION_RECORD_KEYS` do not contain it; across the whole phase only
23-04's wiring record declares it), so without that line the escape simply moves from "wrong
filename" to "missing key", and a wrong filename is a choice somebody made while an omission
requires no lie at all. Only an explicit `sweep_point: false` exempts.

Both escape routes are **watched failing** on synthetic records in the same test body, and both
one-sided controls are asserted so neither refusal is a blanket rejection:

| Case | Path | Payload | Observed |
|---|---|---|---|
| T-23-81 filename escape | `results/phase23_dp_run_at_sigma_one.json` | `sigma=1.0, sweep_point=True` | `AssertionError`, naming the path |
| T-23-84 omission escape | `results/phase23_noised_dp_sigma1p000000.json` (**under** the glob) | `sigma=1.0`, no `sweep_point` | `AssertionError`, naming `sweep_point` |
| control — real sweep point | `results/phase23_noised_dp_sigma1p000000.json` | `sigma=1.0, sweep_point=True` | checked and admitted |
| control — CAL-03 wiring probe | `results/phase23_cal03_wiring.json` | `sigma=1.0, sweep_point=False` | exempt by its own declaration |

The omission case is driven at a path that **is** under the glob, which isolates the missing key:
the refusal fires on content alone, independent of the name.

## Verification

```
$ .venv/bin/python scripts/phase23_prereg.py                         # exit 0, four outcomes printed
$ .venv/bin/python -m pytest tests/test_phase23_prereg.py -v
32 passed in 1.44s                                                   # zero skipped
$ .venv/bin/python -m pytest tests/test_phase20_prereg.py -q
25 passed
$ git ls-files 'results/phase23_*'                                   # (empty)
$ git diff --exit-code -- scripts/mitigation_accountant.py scripts/mitigation_gate.py pyproject.toml
                                                                     # exit 0
$ .venv/bin/python -m pytest tests/ -q
1398 passed, 1 skipped, 83 warnings in 242.68s
$ make lint
All checks passed!  /  233 files already formatted
```

Acceptance greps, all against the committed files:

| Grep | Required | Observed |
|---|---|---|
| `grep -c "^assert \|    assert " scripts/phase23_prereg.py` | 0 | **0** |
| `grep -n "def noise_floor\|def sigma_zero_verdict\|def n64_leg_is_committable\|def noised_record_path\|def choose_n_seeds"` | 5 | **5** (`:143`, `:207`, `:291`, `:100`, `:349`) |
| `grep -n "H_PER_POINT_FLOOR_SECONDS = "` | `17_175` | **`17_175`** at `:343` |
| `grep -c "^import \|^from " scripts/phase23_prereg.py` | stdlib only | **1** — `import math` |
| `grep -cE "^\s*(import\|from)\s+.*phase23_(cost\|run)"` | 0 | **0** |
| `grep -c "results/phase23_" scripts/phase23_prereg.py` | ≥ 7 | **11** |
| `grep -n "EDIT-ONCE\|edit-once\|permanently RED"` | matches | **6 lines** |
| `grep -c "17175\|17_175\|17,175" tests/test_phase23_prereg.py` | 0 | **0** |
| `grep -n "2\*\*-\|ulp\|ULP" tests/test_phase23_prereg.py` | matches | `:173`, `:175`, `:258`, `:265`, `:267` |
| `grep -n "from test_phase20_prereg import"` | matches | `:53` |
| `grep -c "_assert_ordering_holds" tests/test_phase23_prereg.py` | ≥ 4 | **8** |
| `grep -n "bool(checked)"` | matches | `:367`, `:393` |
| `grep -n "fnmatch"` | matches | `:16`, `:602` |

## Frozen-Pin Discipline

Neither frozen pin moved: `git diff --exit-code -- scripts/mitigation_accountant.py
scripts/mitigation_gate.py` exits 0, and `pyproject.toml` is byte-unchanged (RPT-03, T-23-SC —
**zero installs**). The three task commits touch exactly two files and nothing under `results/`;
`git diff --diff-filter=D --name-only 1efb31c 11ba67a` is empty, so nothing was deleted.

## Deviations from Plan

**1. [Rule 1 — Bug] The HALT message did not contain the lowercase phrase the guard requires**

- **Found during:** Task 1, running the `__main__` self-check
- **Issue:** The headline was first written `THE SWEEP IS HALTED AND ZERO NOISED POINTS WILL RUN.`
  The plan's acceptance requires the message to contain `zero noised points`, and the check is
  case-sensitive. The self-check caught it before the commit — which is the argument for the
  self-check existing at all.
- **Fix:** `THE SWEEP IS HALTED: zero noised points will run.` — same emphasis, matchable, and
  `HALT` still present as a substring of `HALTED`.
- **Commit:** `c7de5d4`

**2. [Rule 1 — Bug] Two `E501` lines at 101 chars**

- **Found during:** Task 2, `ruff check`
- **Fix:** One f-string fragment rewrapped; one long `def` signature split across lines.
- **Commit:** `e81dff9`

**3. [Rule 2 — Missing correctness requirement] `DPSGD-06` was NOT marked complete, against the
plan's `requirements: [DPSGD-06]` frontmatter**

- **Found during:** state update
- **Issue:** `REQUIREMENTS.md:156` states DPSGD-06 as *"The σ=0 point is the DP arm's **first
  executed run**"*. Nothing has been executed. `23-01`, `23-06`, `23-07`, `23-08` and `23-10` also
  carry `DPSGD-06` in their frontmatter, and **23-10 is the plan that runs σ=0**. Ticking it here
  would publish a completion this repository cannot demonstrate — the same call `23-02` made on
  `CAL-02`, for the same reason.
- **Fix:** `requirements mark-complete DPSGD-06` deliberately not called. The frontmatter records
  `requirements-completed: []` plus a `requirements-advanced` entry naming the half that closed (the
  ordering, now checkable against git) and the four plans that own the rest.

**4. [Additive, recorded because the module is EDIT-ONCE] Two names exist that the plan described
but did not name**

- `FLOOR_PROVENANCE_KEYS` — the plan listed the eight required provenance keys inline. They are a
  module-level tuple so the parametrized refusal test iterates the rule's own set rather than a
  retyped list, and a key added later gains a case automatically. Mirrors
  `mitigation_gate.EXTRACTION_FLOOR_PROVENANCE_KEYS`.
- `NOISED_RECORD_PREFIX` — `NOISED_RECORD_GLOB` is derived from it (`PREFIX + "*"`) and
  `noised_record_path` builds from the same string, so the glob and the paths it must match cannot
  drift apart.

Both are additive and neither changes a name any later plan cites. Recorded here because **no later
plan can add a constant to this module**, so a future reader needs to know what is already present.

**5. [Rule 3 — Blocking] Task 1's `<verify>` block names a test file Task 2 creates**

- **Found during:** Task 1, verification
- **Issue:** `.venv/bin/python -m pytest tests/test_phase23_prereg.py -q` cannot pass at Task 1 —
  the file does not exist until Task 2.
- **Fix:** Task 1 was verified by the `__main__` self-check plus the **full suite**
  (`1366 passed, 1 skipped`), which is the stronger check anyway: it is what catches the repo-wide
  `scripts/*.py` scans in `test_lora_inject.py`, `test_phase14_scoring.py`, `test_phase19_erasure.py`,
  `test_phase20_correction.py` and `test_phase21_unit_continuation.py` that a new module under
  `scripts/` enters automatically.

**No artifact-naming discrepancies.** Every symbol the plan cited resolved against the code as
written, and every symbol later Phase-23 plans cite exists with the signature they call it with —
checked by grepping all fourteen plan files for `phase23_prereg.<name>` before writing:
`noise_floor`, `sigma_zero_verdict`, `n64_leg_is_committable`, `noised_record_path`,
`choose_n_seeds`, `H_PER_POINT_FLOOR_SECONDS`, `CAL03_WIRING_RECORD`, `CONTROL_FLOOR_RECORD`,
`NEVER_TAUGHT_TRAINING_RECORD`, `NEVER_TAUGHT_RECORD`, `SIGMA_ZERO_RECORD`, `COST_RECORD`,
`NOISED_RECORD_GLOB`. `23-11-PLAN.md:142` calls `noised_record_path("dp_n64", sigma)` positionally
with an underscore in the arm name, which is why the arm validator admits `_` as well as `-`. The
`H_PER_POINT_FLOOR_SECONDS` derivation was re-computed from `23-RESEARCH.md:577` rather than cited:
`286.26 × 60 = 17175.6`, and `4.77 × 3600 = 17172` confirms the REQUIREMENTS row is three seconds
off and therefore the restatement rather than the source.

## gsd-sdk Hazards — thirteenth session, and the profile shifted again

Every handler's output was diffed and read before the next was called. A snapshot of both files was
taken before the first call.

| Handler | Behaviour |
|---|---|
| `state.advance-plan` | Bumped `Plan: 3 of 14` → `4 of 14` correctly. **NEW REGRESSION: it did NOT bump `completed_plans` (49 → 49; 23-02 measured it bumping 48 → 49).** Flattened the body `Status:` from `Executing Phase 23` to `Ready to execute` (unchanged from 23-02). Returned `last_updated` QUOTED (unchanged). Did not touch `stopped_at`. |
| `state.update-progress` | `{"updated": false, "reason": "Progress field not found in STATE.md"}` — the same string since 22-12 — and the CLAIMED NO-OP still re-stamped and re-quoted `last_updated`. `percent`/`completed_phases` untouched at 33/3. |
| `state.record-metric` | Refused positional args (`{"error": "phase, plan, and duration required"}`); clean with `--phase/--plan/--duration/--tasks/--files`. |
| `state.add-decision` | Refused positional args, needed `--summary`. **The `[Phase ?]` corruption did NOT reproduce** — it wrote `[Phase 23]` correctly for the first time in four sessions — but it emitted `- [Phase 23]: 23-03: `, with a colon the surrounding 500 lines do not use. Repaired on all five. |
| `state.record-session` | Clean; set frontmatter `stopped_at`, body `Last session` and `Stopped at`. |
| `roadmap.update-plan-progress --phase 23` | Reported `summary_count: 2` and therefore **neither ticked the `23-03-PLAN.md` wave checkbox nor moved the row past `2/14`** — it counts SUMMARY files on disk, and this one did not exist yet. It **still mangled the row's last two cells** from `\| In Progress \| - \|` to `\| In Progress\|  \|`, dropping the `-` placeholder — the same corruption 23-02 measured, now reproduced twice. |

All seven repairs applied line-exactly by splitting on lines and matching with `str.startswith`,
never a regex: `last_updated` unquoted, `completed_plans` 49 → 50, body `Status:` restored, five
decision labels de-coloned, the ROADMAP wave checkbox ticked, and the phase row restored to
`| v4.0 | 3/14 | In Progress | - |`. `wc -l`: `STATE.md` 656 → **662** (+1 metric row, +5
decisions, no other line-count change — several files cite `STATE.md` by line number);
`ROADMAP.md` **804 → 804**. No second handler was called to fix a first handler's damage.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no schema at a trust boundary. Its only
subprocess calls are `git` invoked through the imported `_git` helper with an argv tuple and an
explicit `cwd=`, never `shell=True`; every scratch repository lives under pytest's `tmp_path` and
dies with it, so a `phase23_`-named probe cannot escape into the real history and permanently freeze
the module a plan early.

## Known Stubs

None. The six record constants name files that do not exist yet, and that is the point rather than a
stub: the module is edit-once, so every path the phase will write has to be declared before the
first one is written. The three ancestry guards are green-having-checked-nothing today and become
hard from the first artifact — a state recorded in each docstring and in this Summary rather than
hidden.

## Self-Check: PASSED

- `scripts/phase23_prereg.py` — FOUND
- `tests/test_phase23_prereg.py` — FOUND
- Commit `c7de5d4` — FOUND
- Commit `e81dff9` — FOUND
- Commit `11ba67a` — FOUND
- `git ls-files 'results/phase23_*'` — correctly EMPTY (0 paths)
- `git diff --diff-filter=D --name-only 1efb31c 11ba67a` — EMPTY, no file deleted
