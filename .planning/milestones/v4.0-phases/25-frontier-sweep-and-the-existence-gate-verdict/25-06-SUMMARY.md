---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 06
subsystem: testing
tags: [pytest, skipif, mps, pmset, caffeinate, subprocess, ast, re-entrancy]

requires:
  - phase: 25-21
    provides: "tests/test_phase25_condition_c.py::test_the_measurement_path_reproduces_phase19_exactly — one MPS leg gated on PERSONACORE_SWEEP_ACTIVE, inside this plan's literal"
  - phase: 25-22
    provides: "tests/test_phase25_gate05.py::test_measure_gate05_produces_six_finite_nlls_per_locked_fact — the second wave-1 MPS leg inside the literal"
  - phase: 23
    provides: "tests/test_phase23_mps_venue.py — the SINGLE MPS device register (_MPS_AVAILABLE / _MPS_SKIP / _DEVICES) that five files import"
provides:
  - "PERSONACORE_SWEEP_ACTIVE — ONE flag, an env var, that makes every MPS leg skip with a reason NAMING the sweep"
  - "SWEEP_ACTIVE_EXPECTED_SKIPS = 36, measured over the complete suite and pinned as a literal before the sweep launches"
  - "scripts/phase25_venue.py — PMSET_APPLY / PMSET_REVERT / PMSET_REVERT_TARGETS as committed argv data, prove_reverted(), read_assertions(), prove_only_our_caffeinate()"
  - "_SUITE_TARGETS / _run_inner_suite — the argv-only re-entrancy bound 25-17 inherits verbatim"
affects: [25-14, 25-17, 25-20]

tech-stack:
  added: []
  patterns:
    - "argv-exclusion re-entrancy bound funnelled through ONE subprocess helper, enforced by AST"
    - "a two-reason skipif mark whose reasons are module constants so they can be asserted DISTINCT"
    - "a privileged operator command committed as an argv tuple the module itself never invokes"

key-files:
  created:
    - scripts/phase25_venue.py
    - tests/test_phase25_venue.py
  modified:
    - tests/conftest.py
    - tests/test_phase23_mps_venue.py
    - tests/test_mps_smoke.py

key-decisions:
  - "ONE mechanism: the env var. No pytest_addoption / --sweep-active, because the register is evaluated at IMPORT time and a CLI option would skip the 7 register-inherited files while RUNNING 25-21's and 25-22's env-var-gated legs on a saturated MPS. `pytest --sweep-active` exits 4 loudly instead."
  - "The flag flips `_MPS_AVAILABLE` ITSELF, not only the mark, because tests/test_phase23_resume.py:414 uses it as a BRANCH VALUE that allocates on MPS (trap 1)."
  - "Re-entrancy is bounded by argv EXCLUSION, never by a PERSONACORE_INNER_SUITE skipif guard: a guard inflates the CHILD's skip count and 25-17 compares the human-facing number against this literal during the live sweep."
  - "SYSTEM_ASSERTION_OWNERS stays pinned at the measured ('dasd',) and is NOT widened to the newly-observed powerd/WindowServer — an allow-list that grows on every new observation converges on tolerating everything, which is the failure D-43 exists to prevent."

patterns-established:
  - "Attributed sum, never a bare total: 36 = 33 device-touching legs + 2 named wave-1 node ids + 1 pre-existing CUDA skip, so a drift of one is blamed rather than re-measured."
  - "A guard's RED is watched on a scratch copy OUTSIDE the repo, so watching leaves no residue a census can see."

requirements-completed: [FRONT-01]

duration: 42min
completed: 2026-08-31
---

# Phase 25 Plan 06: Making the Suite Safe to Run During the Sweep Summary

**One env var (`PERSONACORE_SWEEP_ACTIVE`) makes 35 MPS legs skip with a reason naming the sweep, the resulting count is pinned as the literal `36` the suite checks against itself, and D-13's `pmset` revert is committed as verifiable argv data with `prove_reverted()` watched refusing a non-reverted machine.**

## Performance

- **Duration:** 42 min of commit-to-commit work; ~85 min wall clock including six full-suite measurements
- **Started:** 2026-08-31T22:26:09Z (HEAD `2a76293`)
- **Completed:** 2026-08-31T23:13:16Z (task commits) / 2026-09-01T00:12Z (final suite green)
- **Tasks:** 3
- **Files modified:** 5 (2 created, 3 modified)

## The three literal pytest summary lines

| Run | Command | Line, verbatim |
|---|---|---|
| Flag **unset**, before this plan's test file | `pytest tests/ -rs -q` | `1794 passed, 1 skipped, 83 warnings in 488.84s (0:08:08)` |
| Flag **set** | `PERSONACORE_SWEEP_ACTIVE=1 pytest tests/ -rs -q` | `1759 passed, 36 skipped, 83 warnings in 243.28s (0:04:03)` |
| **Delta** | — | **35 legs move from passed to skipped.** `1794 - 1759 = 35` and `36 - 1 = 35`, from both sides |

**Against the orchestrator's stated baseline of `1794 passed, 1 skipped`: the flag-unset delta is
exactly ZERO on both halves.** The flag is additive, measured, not asserted.

**Final full suite, flag unset, WITH this plan's own test file collected:**

```
1810 passed, 1 skipped, 83 warnings in 1196.47s (0:19:56)
```

`1810 - 1794 = +16`, exactly the 16 tests in `tests/test_phase25_venue.py`. Skip count unchanged at
1. Zero failed. Wall clock 1196 s against the bare suite's 489 s is **2.4x**, inside the module
docstring's stated ~3x (489 outer + 241 inner-flag-set + 489 inner-flag-unset ≈ 1219 predicted).

## The inner and outer counts are the SAME number

The literal is asserted by a CHILD process. Plan 25-17 reads it from a HUMAN-facing command during
the live sweep. Both were run and both report the identical line:

```
# inner, from _run_inner_suite (child of tests/test_phase25_venue.py)
1759 passed, 36 skipped

# outer — 25-17's exact committed argv, run verbatim here
$ PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest tests/ --ignore=tests/test_phase25_venue.py -q
1759 passed, 36 skipped, 83 warnings in 241.32s (0:04:01)
```

This is the property the **argv exclusion** buys and a `PERSONACORE_INNER_SUITE` skipif guard would
have broken: the excluded file has no MPS-gated test, so it contributes 0 skips on both sides.

## The attributed sum behind `SWEEP_ACTIVE_EXPECTED_SKIPS = 36`

Measured, per file, from `-rs` output — never a bare total, so a drift of one can be blamed on a
named leg instead of re-measured from scratch:

| Legs | File | How they are gated |
|---|---|---|
| 9 | `tests/test_phase22_dpsgd.py` | `_DEVICES` params |
| 8 | `tests/test_phase23_mps_venue.py` | 6 `_DEVICES` params + 2 bare `@_MPS_SKIP` |
| 8 | `tests/test_phase22_fakes.py` | 7 `_DEVICES` params + 1 bare `@_MPS_SKIP` |
| 3 | `tests/test_phase22_checkpoint.py` | 2 `_DEVICES` params + 1 bare `@_MPS_SKIP` |
| 2 | `tests/test_phase23_resume.py` | 2 bare `@_MPS_SKIP` |
| 2 | `tests/test_phase23_cal03.py` | a module-scope `_DEVICES` fixture |
| 1 | `tests/test_mps_smoke.py` | module-level `pytestmark` |
| **33** | **seven device-touching files** | all through the single register |
| 1 | `tests/test_phase25_condition_c.py::test_the_measurement_path_reproduces_phase19_exactly` | 25-21, env var directly |
| 1 | `tests/test_phase25_gate05.py::test_measure_gate05_produces_six_finite_nlls_per_locked_fact` | 25-22, env var directly |
| 1 | `tests/test_train_loop.py:81` | **PRE-EXISTING** — "fp16 AMP smoke needs a CUDA GPU". Not D-44's. |
| **36** | | `33 + 2 + 1` |

Both wave-1 node ids were proved SKIPPED under `-rs`, not merely assumed to be inside the count:

```
$ PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/python -m pytest tests/test_phase25_condition_c.py tests/test_phase25_gate05.py -rs -q
SKIPPED [1] tests/test_phase25_condition_c.py:99: the condition-(c) reproduction runs ~87 s of forward passes on MPS. It is skipped when PERSONACORE_SWEEP_ACTIVE is set (D-44 — the sweep owns the device and a suite run would contend with it) ...
SKIPPED [1] tests/test_phase25_gate05.py:410: measure_gate05 runs teacher-forced exposure over the eight locked facts on MPS. It is skipped when PERSONACORE_SWEEP_ACTIVE is set (D-44 — the sweep owns the device and a suite run would contend with it) ...
53 passed, 2 skipped in 0.70s
```

## A verbatim SKIPPED reason captured under the flag

```
SKIPPED [1] tests/test_mps_smoke.py:43: PERSONACORE_SWEEP_ACTIVE is set: the v4.0 FRONTIER SWEEP is
running on this machine and it owns the MPS device. MPS is genuinely AVAILABLE right now — that is
the whole problem. The 44-point sweep saturates the device for 4.5-6.3 days, so this leg would RUN
and CONTEND with it, and a contention failure is INDISTINGUISHABLE FROM A GENUINE ONE: the same red,
the same traceback, a cause nobody can separate from a real regression six days into an unrepeatable
run. D-44 therefore makes the skip LOUD rather than letting the leg quietly fail or quietly vanish —
the leg stays a countable `pytest.param(..., marks=...)`, the reason names the sweep, and
`tests/test_phase25_venue.py::test_the_sweep_active_skip_count_is_the_number_stated_in_advance`
asserts the resulting skip count against a literal committed BEFORE the sweep launched. Unset
PERSONACORE_SWEEP_ACTIVE to run this leg — but only when the sweep is not holding the device.
```

The second entry point fails loudly rather than being honoured for 7 of 9 files:

```
$ .venv/bin/python -m pytest tests/test_phase23_mps_venue.py --sweep-active -q
__main__.py: error: unrecognized arguments: --sweep-active
exit=4
```

## The re-entrancy bound, proved three ways and watched RED

Bounded at depth 1 by **argv only** — `_SUITE_TARGETS = ['tests/', '--ignore=tests/test_phase25_venue.py']`,
funnelled through `_run_inner_suite`, the single `pytest`-spawning call site.

1. **Structural (AST).** `every pytest subprocess is funnelled through _run_inner_suite: [119, 635, 455]`
   — line 119 is `_run_inner_suite`'s spawn; 635 and 455 are the two `git` calls, which carry no
   `pytest` constant and no `_SUITE_TARGETS`/`_INNER_SUITE_ARGV` reference.
2. **By value.** `recursion severed at depth 1 by argv, not by pytest config: ['tests/', '--ignore=tests/test_phase25_venue.py']`
3. **Behavioural.** `the child collects 0 node ids from the spawner; recursion bounded at depth 1` —
   run **before** any inner suite was ever launched, per the recursion hazard's ordering.

**The guard's own RED, watched.** A scratch copy in the scratchpad (never a repo file) with one
extra unfunnelled `subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], ...)` appended
reddened the AST criterion with `AssertionError: [636]`, and `git status --short` confirmed the
repo was untouched by the watching.

`git diff --exit-code -- pyproject.toml` exits 0: no `addopts`, no marker registration, no
`[tool.pytest.ini_options]` change. RPT-03 holds.

## D-13's revert, and its natural RED

The three revert targets were **re-read live three times** during this plan and read identically
every time — `sleep 1`, `disksleep 10`, `powernap 1`, matching 25-RESEARCH.md §R5 at `8dd6415`. They
are the machine's real prior state, not macOS defaults, and `PMSET_REVERT` is committed as an argv
tuple whose words are asserted to agree with `PMSET_REVERT_TARGETS` field by field.

**`prove_reverted()` watched refusing, verbatim:**

```
[venue:not-reverted] sleep=0 (required 1) <-- NOT REVERTED, disksleep=0 (required 10) <-- NOT
REVERTED, powernap=0 (required 1) <-- NOT REVERTED. D-13 requires the sweep's system-wide power
change to be reverted to the MEASURED prior values {'sleep': 1, 'disksleep': 10, 'powernap': 1}; run
sudo pmset -a sleep 1 disksleep 10 powernap 1 and re-check. This machine is still holding a
privileged change made for a run that has ended
```

`{"sleep": 0, "disksleep": 0, "powernap": 0}` is **not a planted value**: it is exactly what
`PMSET_APPLY` produces, so this is the machine's real intermediate state between the sweep's start
and the revert — the state plan 25-20 will find it in.

## D-43's over-count, reproduced THREE times

The correction rests on `pmset -g`'s summary line enumerating **assertions**, not processes. Measured
independently at three moments today, and the over-count held every time while the pids moved:

| Reading | summary `caffeinate` entries | `pgrep -x caffeinate` |
|---|---|---|
| 25-RESEARCH.md §R5, HEAD `8dd6415` | 5 | `7591 46029 58309` |
| live, this plan, ~19:27 | 5 | `7591 8264 58309` |
| live, this plan, ~20:20 | 5 | `7591 38758 58309` |

Five entries for three processes each time, because pid 7591 holds two assertions and 58309 holds
three — and the transient third pid changed on **every** reading. `read_assertions()` therefore
parses only `Listed by owning process:` and is asserted to return `[]` for the summary blob, so the
corrected method is enforced by the parser rather than described in a paragraph.

## Task Commits

1. **Task 1: `scripts/phase25_venue.py`** — `277109f` (feat) — 354 lines
2. **Task 2: D-44's skip at its two composition points** — `fd90055` (feat) — conftest +59, register +86/-19, smoke +16/-3
3. **Task 3: `tests/test_phase25_venue.py`** — `5633c9f` (test) — 646 lines, 16 tests, 743.10s

## Files Created/Modified

- `scripts/phase25_venue.py` — the pmset apply/revert argv tuples with measured targets,
  `prove_reverted()`, `read_assertions()` (by owning process), `prove_only_our_caffeinate()`
  cross-checking `pgrep`, and `CAFFEINATE_WRAP = ("caffeinate", "-dims")`. Invokes neither pmset
  tuple; asserted by AST that no subprocess call site elevates privilege.
- `tests/conftest.py` — `sweep_is_active()` + `SWEEP_ACTIVE` + `SWEEP_ACTIVE_ENV_VAR`, and a
  docstring recording why `--sweep-active` must never be added.
- `tests/test_phase23_mps_venue.py` — `_MPS_AVAILABLE = _MPS_PRESENT and not _SWEEP_ACTIVE`, the
  two-reason `_MPS_SKIP`, and the three-class exemption comment (covered-for-free / not-MPS-gated /
  deliberately-left-running).
- `tests/test_mps_smoke.py` — imports `_MPS_SKIP` instead of re-spelling `is_available()`.
- `tests/test_phase25_venue.py` — 16 tests: the bound (3), the count (3), the reasons (2), D-13/D-43
  (6), plus the pyproject byte-identity check.

## Decisions Made

- **No CLI option, ever.** Written into the conftest docstring with all three reasons so it is not
  re-added as an ergonomic improvement.
- **`_MPS_PRESENT` split out of `_MPS_AVAILABLE`.** The reason selection needs to know *why* the
  value is False — a CI machine with no MPS must not be told a sweep is holding its device. Asserted:
  `PERSONACORE_SWEEP_ACTIVE` does not appear in `_MPS_ABSENT_REASON`.
- **`SYSTEM_ASSERTION_OWNERS` left at the pinned `("dasd",)`** despite the live re-read disagreeing
  (see Deviations). Widening it on observation is the failure mode; naming the owner at launch time
  through `expected_owners=` is the mechanism.

## Deviations from Plan

### Measured corrections to plan-time figures

**1. [Rule 1 - False figure] "42 device-touching legs" is wrong; the measured number is 35.**
- **Found during:** Task 2 (e), the measurement the plan itself asks for
- **Issue:** The plan's `<objective>`, Task 2's `<done>` and threat T-25-26 all state that the flag
  makes **42** legs skip. Measured over the complete suite: **33** legs across the seven
  device-touching files, plus **2** wave-1 legs = **35** D-44-attributable skips. The total skip
  count is 36 only because one pre-existing CUDA-only skip (`test_train_loop.py:81`) is unrelated to
  D-44 and is also the flag-unset baseline's single skip.
- **Both readings published:** plan-time 42, measured 35 (`1794 - 1759 = 35`, `36 - 1 = 35`).
- **Does the conclusion survive?** Yes, entirely. The mechanism, the traps, the loudness requirement
  and the pinned-literal discipline are unaffected; only the cardinality was wrong. The literal is
  pinned at the measured 36 with the attributed sum beside it, which is precisely the construction
  that makes a wrong count blameable rather than re-measurable.
- **Files:** `tests/test_phase25_venue.py` (the attribution comment)
- **Committed in:** `5633c9f`

**2. [Rule 1 - Imprecise premise] "`test_phase22_checkpoint.py` / `test_phase22_dpsgd.py` are not MPS-gated" is true only of their MODULE-level gates.**
- **Found during:** Task 2 (the `<read_first>` confirmation step)
- **Issue:** The plan's must_haves say *"CONTEXT names two files that need NO separate work ...
  neither is MPS-gated."* Their **module-level** gates are indeed `_REAL_FULL is None` (artifact
  presence) and a platform tuple. But both files **import `_DEVICES` and `_MPS_SKIP`** and together
  contribute **12** of the 33 device-touching skips.
- **Impact:** The plan's *action* is correct — neither needs a separate edit — but the *reason* is
  "covered for free through the import", not "not MPS-gated". Recorded precisely in the register's
  exemption comment so the next reader does not conclude those 12 legs are unprotected.
- **Committed in:** `fd90055`

**3. [Rule 3 - Blocking] `-rs` alone does not print node ids, so `--verbosity=1` was added.**
- **Found during:** Task 3, `test_the_two_wave_one_mps_legs_are_inside_the_count`
- **Issue:** The plan requires asserting that both **node ids** appear as SKIPPED. pytest's `-rs`
  short summary prints `file:lineno`, never a node id, at any verbosity.
- **Fix:** `_NODE_ID_ARGS = ["-rs", "--verbosity=1"]`. `--verbosity=N` writes `dest="verbose"`
  directly and therefore **overrides** the `-q` already in `_INNER_SUITE_ARGV` (argparse takes the
  last write). Measured: the verbose progress line reads
  `tests/test_phase25_gate05.py::test_measure_gate05_... SKIPPED`, which carries the node id.
- **Verification:** both node ids asserted present; the test passes.
- **Committed in:** `5633c9f`

**4. [Rule 2 - Stated exemption] `SYSTEM_ASSERTION_OWNERS`'s pinned value disagrees with the live machine.**
- **Found during:** Task 1 acceptance criteria
- **Issue:** The plan pins `SYSTEM_ASSERTION_OWNERS = ("dasd",)` "from the measurement". Live
  `pmset -g assertions` on this machine returned owners `['Claude', 'WindowServer', 'caffeinate',
  'powerd']` — **`dasd` was absent**, and `powerd`/`WindowServer` were present and unnamed.
- **Fix:** The pinned literal is left **exactly as the plan specifies** (plan fidelity), and the
  divergence is recorded in-source above the constant with both readings. `prove_only_our_caffeinate`
  already has the right mechanism for it: an unnamed owner **raises**, and the operator tolerates it
  by naming it through `expected_owners=` in the launch note. Widening the constant on every new
  observation converges on tolerating everything, which is what D-43 exists to prevent.
- **Verification:** `test_prove_only_our_caffeinate_refuses_a_stray` asserts both halves — `Claude`
  unnamed raises, `Claude` named through `expected_owners=("Claude",)` passes.
- **Committed in:** `277109f`

---

**Total deviations:** 4 (2 false/imprecise plan figures published with both readings, 1 blocking
mechanism fix, 1 stated exemption). **Impact:** no scope creep; every plan artifact, constant name
and assertion wording was reproduced exactly. Nothing was invented in place of a named symbol.

## Issues Encountered

- **The 10-minute foreground command ceiling.** `pytest tests/test_phase25_venue.py -v` costs
  743 s and the final full suite costs 1196 s; both were run in the background. This is the ~3x cost
  the module docstring warns 25-17 about, and it is why 25-17's committed argv carries
  `--ignore=tests/test_phase25_venue.py` and pays ~1x.
- **Known hazard (a) fired exactly as briefed.** `test_the_epsilon_gate_fires_on_a_planted_bare_print`
  went RED on the uncommitted `scripts/phase25_venue.py`. Resolved by committing Task 1 before any
  suite run — not by touching the test.
- **Known hazard (b) did not fire.** `test_phase23_resume.py::test_production_resume_epsilon_bit_identical`
  ran in every flag-unset full suite (three of them) and was green each time.
- **Transient artifact observed and self-cleaned.** `results/phase23_resume_probe_a_dp_n8/run.csv`
  appears mid-run during that same resume test and is gone by the end; no census reds on it.

## Next Phase Readiness

- **25-17** inherits its exact committed argv from this plan's module docstring and its
  `SWEEP_ACTIVE_EXPECTED_SKIPS = 36` literal, both proved equal to the human-facing number today.
- **25-14** sets `PERSONACORE_SWEEP_ACTIVE=1` in the LaunchAgent plist's `EnvironmentVariables`;
  the flag name and `sweep_is_active()` are now on disk rather than only in plan text.
- **25-20** executes `PMSET_REVERT` and calls `prove_reverted()`. The revert is committed argv data
  with re-measured targets and its refusal has been watched.
- **Carry-forward for 25-20's operational note:** this machine's non-system assertion owners today
  are `Claude`, `powerd` and `WindowServer`, and `dasd` was absent. Each must be named through
  `expected_owners=` at launch, per D-43. `pgrep -x caffeinate` returned a *different* transient pid
  on every one of three readings — clear the strays immediately before launch, not hours before.

## Self-Check

Files:

- FOUND: `scripts/phase25_venue.py`
- FOUND: `tests/test_phase25_venue.py`
- FOUND: `tests/conftest.py`
- FOUND: `tests/test_phase23_mps_venue.py`
- FOUND: `tests/test_mps_smoke.py`

Commits:

- FOUND: `277109f`
- FOUND: `fd90055`
- FOUND: `5633c9f`

Gates:

- `.venv/bin/python -m pytest tests/ -q` → `1810 passed, 1 skipped, 83 warnings in 1196.47s`, 0 failed
- `make lint` → `All checks passed! / 246 files already formatted`, exit 0
- `git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py scripts/mitigation_unit.py scripts/phase18_extraction.py pyproject.toml` → exit 0
- `.planning/STATE.md` and `.planning/ROADMAP.md` untouched (`git status --short` empty for both)

## Self-Check: PASSED

---
*Phase: 25-frontier-sweep-and-the-existence-gate-verdict*
*Completed: 2026-08-31*
