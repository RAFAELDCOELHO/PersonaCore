# Phase 25 — deferred items

Out-of-scope discoveries logged rather than fixed, per the executor scope boundary.

## D1 — `tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical` is FLAKY under full-suite load

**Found during:** plan 25-21, full-suite verification runs on 2026-08-31.
**Status:** deferred — not fixed, not caused by 25-21.

**Evidence, three readings on the same tree:**

| Run | Context | Result | Wall clock |
|-----|---------|--------|-----------|
| 1 | full suite, 25-21 files present | **PASSED** (the run's only failures were the two censuses 25-21 then declared) | 1683.46 s |
| 2 | full suite, same tree + the two census declarations | **FAILED** | 1626.92 s |
| 3 | the test alone, `pytest tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical -q` | **PASSED** | 202.42 s |
| 4 | full suite, unchanged tree | **PASSED** — `1743 passed, 1 skipped` | 606.00 s |

**One reading in four is red, and the machine's own timing corroborates the flake.** The identical
suite on the identical tree took **1626.92 s in run 2 and 606.00 s in run 4** — a 2.7x spread with
no code change between them. The same machine-level variance shows up in 25-21's own cost
measurement (the two condition-(c) calls measured 213.4 s isolated and 420.6 s in-suite, a 1.97x
spread). A bit-identity assertion over ~200 s of MPS training is exactly the kind of check that
variance of that size can flip.

**Why it is out of scope for 25-21.** The test exercises Phase 23's DP-SGD production
resume epsilon bit-identity over ~200 s of real MPS training. Plan 25-21 touched four
files — `scripts/phase25_condition_c.py` and `tests/test_phase25_condition_c.py` (both
new), plus one census declaration each in `tests/test_phase19_erasure.py` and
`tests/test_phase21_sc5.py`. None is imported by, or imports, the phase-23 resume path.
The test passed in TWO full-suite runs with all of 25-21's code already present (runs 1
and 4), which rules out the new files as a deterministic trigger.

**The hypothesis NOT yet excluded, stated rather than glossed.** 25-21 adds a second
long-running MPS leg to the suite (`test_the_measurement_path_reproduces_phase19_exactly`,
~420 s in-suite). All four runs contained it and three were green, so it is not a
deterministic trigger — but a timing- or thermal-sensitive interaction between two long
MPS legs in one process is not excluded by four observations. Whoever picks this up should run the suite with
`PERSONACORE_SWEEP_ACTIVE=1` (which skips 25-21's MPS leg) several times and compare the
failure rate against the unset case. That is the one-command experiment; it was not run
here because it costs ~27 min per repetition and the finding is out of 25-21's scope.

**Do not "fix" this by loosening the bit-identity assertion.** It is a resume-correctness
proof; a flaky proof is a diagnosis to make, not a tolerance to widen.
