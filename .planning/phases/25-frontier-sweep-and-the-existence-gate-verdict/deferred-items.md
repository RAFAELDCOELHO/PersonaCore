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

---

## FIXED, not deferred — recorded here because a later plan would otherwise re-discover it

### `scripts/phase25_run.py::_draw_one_shape` called `tp.device()`, which did not exist

**Found during:** plan 25-11, Task 2 (the first plan in this phase to actually draw).

**Measured at HEAD before the fix:** `scripts/teach_persona.py` had no `device` attribute, yet
five call sites assumed one:

| File | Line | Call |
|------|------|------|
| `scripts/phase25_run.py` | 519 | `recall.load_adapted_model(tp.device(), adapter)` |
| `scripts/phase25_run.py` | 541 | `recall.draw_all(..., tp.device(), ...)` |
| `scripts/phase25_calibrate.py` | x3 | the throughput probe's model/base loads |

Every one raised `AttributeError: module 'teach_persona' has no attribute 'device'`.

**Why no test caught it.** `_draw_one_shape` is reached only from `draw_point_shapes` when
`dry_run` is false, and every committed driver test in `tests/test_phase25_driver.py` exercises
the `--dry-run` path. The failure is therefore latent until the first real draw — which happens
**after** that point's training leg, i.e. after up to **23.05 minutes** of spent GPU time on a
`dp_n64` point. It would have fired on the FIRST draw of the FIRST sweep point.

**Fix (commit `6df1eba`):** `device()` added to `scripts/phase25_run.py` — the Phase-25 driver
owns the Phase-25 draw loop — and both its call sites repointed at it.
`scripts/phase25_calibrate.py` calls `phase25_run.device()`, an intra-phase dependency it already
had for `atomic_write_json`.

**A first attempt put it in `scripts/teach_persona.py` (`849657d`) and was REVERTED (`28ed553`).**
Measured reason: `teach_persona.py` is pinned by
`results/phase24_token_budget.json`'s `provenance.module_sha256`, and
`tests/test_phase24_record.py::test_the_provenance_pins_match_the_live_module_bytes` went RED —
a resolver added there moves a committed **Phase-24** record's digest to fix a **Phase-25**
defect. `phase23_run.device()` was also rejected as the source: Phase 25 PORTS from that module
and never imports it (25-10), which is why `atomic_write_json` and the cache helpers were ported
rather than imported.

**Residual, genuinely deferred:** the draw loop still has no test that reaches it. 25-11 exercised
the same `recall.draw_all` primitive 1,536 times through `phase23_run._measure_condition`, which
is why the defect surfaced here, but `phase25_run._draw_one_shape` itself is still only covered on
its dry-run branch. A single non-dry-run smoke over one shape at `k=2` would close it; that is
plan 25-14/25-15's call, not 25-11's.

---

### 25-14: the launch gate was reached with the live draw loop still uncovered

**Found during:** plan 25-14, Task 1 (authoring the LaunchAgents that start the sweep).

This is not a new defect — it is the **residual** recorded in the entry above, reaching the point
where it stops being deferrable. 25-14 builds the agents that launch an **87.86–149.45 h**
unattended run, and at that gate `scripts/phase25_run.py::_draw_one_shape` is still covered only on
its `--dry-run` branch by every committed driver test. The instance is fixed (`6df1eba`); the
**coverage class is not**, and the failure mode it belongs to fires *after* up to 23.05 minutes of a
point's training has already been spent.

Recorded as **R1** in `results/phase25_operational_note.md` §10 and asserted present by
`tests/test_phase25_launch.py::test_the_note_carries_the_untested_draw_loop_as_an_open_risk`, so the
risk cannot be dropped from the note silently.

**What would close it:** one non-dry-run smoke over a single shape at `k=2` — the previous entry's
own prescription. 25-14 does not run it: this plan runs **no GPU point** by its own environment
contract (`git ls-files 'results/phase25_point_*.json'` must still be empty at its end), and a
first-point smoke is plan 25-15's scope.

### 25-14: `com.personacore.caffeinate` is a launchd job with no plist anywhere

**Found during:** plan 25-14's read-only before-state inspection.

`launchctl list` reports `58309  0  com.personacore.caffeinate`, a `launchctl submit`-created job
(`type = Submitted`, `path = (submitted by launchctl[58308])`, `ppid 1`) running
`/usr/bin/caffeinate -ims` and asserting **forever** for `416:31:41`. **No plist for it exists in
`~/Library/LaunchAgents` and none exists in this repository** — it was created imperatively in an
earlier session and outlived it.

It is D-43's residue hazard realised: it holds `PreventUserIdleSystemSleep`, `PreventSystemSleep`
and `PreventDiskIdle`, nearly the set `caffeinate -dims` takes, so a sweep launched beside it would
appear protected while a 17-day-old process is what genuinely holds the machine awake.

**Deferred because clearing it is machine state, not code**: it is step (c) of 25-14's blocking
human checkpoint. Recorded here because the *lesson* outlives the act — an imperatively-submitted
launchd job leaves no reviewable artifact, which is exactly why this phase's two agents are
committed plists under `artifacts/` and the installed copies are treated as disposable.
