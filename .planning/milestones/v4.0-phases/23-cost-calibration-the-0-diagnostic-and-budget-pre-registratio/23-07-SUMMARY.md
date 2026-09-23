---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: "07"
subsystem: privacy/training-driver
tags: [dp-sgd, resume, checkpoint, mps, wiring, refusals]
requires:
  - "scripts/teach_persona.py::train_arm (Phase 14/17/21/22)"
  - "src/personacore/training/loop.py::train(resume_from=) (v1.0, Phase 22 DP-slot matrix)"
  - "tests/test_phase23_mps_venue.py::_DEVICES/_MPS_SKIP (plan 23-01)"
provides:
  - "scripts/teach_persona.py::train_arm(resume_from=) — the production DP resume path (WARNING-2)"
  - "scripts/teach_persona.py::refuse_if_exists(paths, *, expected=()) — the per-target inversion"
  - "scripts/teach_persona.py::_refuse_cross_device_resume / _generator_state_bytes / _sha256"
  - "tests/test_phase23_resume.py — 9 tests, the last being the MPS production kill→resume proof"
  - "the dp_n8 corpus sha256 triple that 23-10 and 23-11 must reproduce"
affects:
  - "23-10 (σ=0 run at the full 200-step path; rebuilds the dp_n8 bins)"
  - "23-11 (rebuilds the dp_n8 bins)"
tech-stack:
  added: []
  patterns:
    - "additive keyword-only sentinel threaded through a production driver (the dp_sigma/fact_bin shape, third application)"
    - "a guard WIDENED in the helper rather than branched at two call sites"
    - "rebuild-and-compare instead of skip-the-rebuild, so corpus identity is proven rather than assumed"
key-files:
  created:
    - tests/test_phase23_resume.py
  modified:
    - scripts/teach_persona.py
decisions:
  - "resume_from is threaded into build_arm_bins as well as train_arm — the plan said not to touch it, but it is the SECOND caller of arm_bin_targets and a resume that inverted only train_arm's guard is refused three lines later by that one"
  - "on a resume build_arm_bins REBUILDS the bins and refuses on any byte drift, rather than skipping the rebuild"
  - "the cross-device refusal is scoped to DP arms and derives the recorded device from the dp_noise_rng byte length, because the checkpoint carries no device field at all"
  - "the negative control is the position-sensitivity of the noise draw plus the driver-level refusal of a stripped slot, NOT a different-seed resume — epsilon is structurally blind to the seed"
  - "DPSGD-06 is NOT ticked: this plan broke its literal ordering rather than satisfying it"
metrics:
  duration: 55min
  tasks: 3
  files_changed: 2
  completed: 2026-08-26
---

# Phase 23 Plan 07: The Production DP Resume Seam Summary

`train_arm` now takes and forwards `resume_from`, and a real `dp_n8` kill→resume on the M3
reproduces the uninterrupted control's CSV **row for row, read as text**, at T = 4 and
ε = 9.9972561464343 under exact `==`.

## What Was Built

**Task 1 — the seam** (`aa91123`). `refuse_if_exists(paths, *, expected=())`; `train_arm(...,
resume_from=None)` forwarded to `train(...)`; `build_arm_bins(..., resume_from=None)`; two new
`SystemExit` refusals. `src/personacore/training/loop.py` is byte-unchanged — the entire wiring is
one keyword one hop above it.

**Task 2 — the refusal battery** (`3c39165`). `tests/test_phase23_resume.py`, 8 CPU/fixture-scale
tests.

**Task 3 — the production proof** (`0e60169`). A ninth test: a real `dp_n8` arm on MPS, killed
mid-loop and resumed through the production driver.

## The Reproduction Claim, With Its Raw Numbers

Measured on the M3 (`device=mps`), `.venv/bin/python -m pytest
"tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical" -v -s`,
**1 passed in 104.38s**. Arm A ran 4 steps uninterrupted. Arm B was killed from inside
`loop.save_checkpoint` the instant the step-2 periodic checkpoint hit disk, then resumed via
`train_arm(resume_from=paths["checkpoint"])`.

| quantity | arm A (uninterrupted) | arm B (killed + resumed) | bound |
| --- | --- | --- | --- |
| composed `finalize` invocations | 4 | 2 + 2 = 4 | exact `==` |
| checkpoint `step` field | 4 | 4 | exact `==` |
| `epsilon_for(1.0, T, 1e-5)` | `9.9972561464343` | `9.9972561464343` | exact `==` |
| `dp_noise_rng` bytes | 44 | 44 (births `(44, 44, 44)`, kill `44`) | exact `==` |
| next noise draw off the seam | — | equal to A's | `torch.equal` |

`epsilon_for(1.0, 2, 1e-5)` differs from both, so the equality is not green over a quantity that
never varies. T is COUNTED off real `DPSGD.finalize` invocations, never read off the `step` field.

**The CSV, both runs, verbatim from the run log.** These are the raw per-step numbers; the
comparison bound is exact string equality of the four rows.

```
csv_A step,train_loss,val_loss,lr,tokens,wall_clock
csv_A 1,2.4260458797216415,1.5463003933429718,0.0003,16384,1
csv_A 2,2.424509584903717,1.549061757326126,0.00023249999999999999,32768,2
csv_A 3,2.4230499863624573,1.5411395967006682,9.750000000000003e-05,49152,3
csv_A 4,2.421518459916115,1.5757377564907074,2.9999999999999997e-05,65536,4
csv_B step,train_loss,val_loss,lr,tokens,wall_clock
csv_B 1,2.4260458797216415,1.5463003933429718,0.0003,16384,1
csv_B 2,2.424509584903717,1.549061757326126,0.00023249999999999999,32768,2
csv_B 3,2.4230499863624573,1.5411395967006682,9.750000000000003e-05,49152,3
csv_B 4,2.421518459916115,1.5757377564907074,2.9999999999999997e-05,65536,4
```

Denominator: 4 of 4 rows, 6 of 6 columns, 0 differing characters. The claim is **bit-for-bit, not
up to a tolerance** — `grep -cE "\brel_tol\b|\bmath\.isclose\b|\bpytest\.approx\b|\bapprox\("
tests/test_phase23_resume.py` returns **0** (word-boundary scoped, because `isclose` is a
substring of `disclosed` and this file's docstring is required to contain that word).

**The step column is continuous across the kill** — `[1, 2, 3, 4]`, no gap and no repeat — and
`tokens` is strictly increasing `[16384, 32768, 49152, 65536]`. That is the property
`loop.py`'s `tokens_per_step` comment derives cumulative tokens from the ABSOLUTE step to
preserve, and T-23-33 is the operator deleting the CSV to get past a refusal.

## Two Measured Corrections Made During Execution

Both were found by running the probe, not by reading it. Both are recorded in the test source.

**1. The first "kill" was a SHORTER RUN, not a kill, and the trajectories genuinely diverged.**
The first draft killed by monkeypatching `tp.MAX_STEPS` to `_KILL_AT`. `MAX_STEPS` is
`TrainConfig.max_steps`, which is the **cosine schedule's horizon** — so at step 2 the "killed"
half sat at the END of its own 2-step cosine while the control was mid-schedule. Measured:

| row | arm A `lr` | arm B `lr` (first draft) |
| --- | --- | --- |
| 2 | `0.00023249999999999999` | `2.9999999999999997e-05` |

The two runs took different step-2 updates and the curves diverged from row 3 on
(`val_loss` `1.5411395967006682` vs `1.5411413788795472`; row-4 `train_loss` `2.421518459916115`
vs `2.4228518456220627`). **A resume test whose "kill" silently reparameterises the schedule
proves nothing about resuming.** The kill is now a raise from inside `loop.save_checkpoint` with
`max_steps` intact, and every row then matches exactly.

**2. Nested probe factories over-counted T in the PESSIMISTIC direction.** `_install_dp_probe`
read `tp.DPSGD` to find the real class; installed three times in one test, each read captured the
PREVIOUS factory, so every later run's `finalize` incremented every earlier run's counter.
Measured: composed steps reported `(8, 4, 2)` for a `(4, 2, 2)` run. Fixed by binding
`_REAL_DPSGD = tp.DPSGD` at import. Recorded because it is exactly the class of accounting error a
green test carries into a published ε.

## The dp_n8 Corpus — sha256 for 23-10 and 23-11

`shasum -a 256 data/persona_dp_n8_train*.bin`, and identical across **four** independent builds in
this session (one timing probe + arm A + arm B's fresh half + arm B's resumed rebuild):

```
e14517954f56fa2d3ff55b63096a86dec08535e62ea7d3f77903afb4a3e80735  data/persona_dp_n8_train.bin
732223f3844299f3c4eadff7b05f9a2ba077c48e6792880d89fc6929abd74045  data/persona_dp_n8_train_mask.bin
34d04ac76adf0ed802d3305eb77cb47270311f8f93aee89581f89e33c3f6f2c2  data/persona_dp_n8_train_fact.bin
```

Corpus shape, from the driver's own provenance line: `176 episodes, 8,449 tokens (7,581 teaching +
0 replay)`, `FACT-ALIGNED pack — 8 privacy records, 33 windows (4, 4, 4, 4, 4, 5, 4, 4), 867 pad
tokens`, `seed=1337`, `mask_fraction=0.3218`. These three files carry **no phase prefix**
(`arm_outputs`' own non-widening), so every later `dp_n8` run in this phase shares them; 23-10 and
23-11 delete and rebuild them and must prove byte-identity against the three digests above.

## The DPSGD-06 Ordering Exception — Disclosed in Full

**This plan executed a σ > 0 PRODUCTION `dp_n8` run in wave 2, three waves before 23-10's σ = 0
run.** SC1 and DPSGD-06 say the σ = 0 point is the DP arm's FIRST executed run. That literal
ordering is broken here, and the disclosure lives in exactly two places — this SUMMARY and
`test_production_resume_epsilon_bit_identical`'s docstring — because it can live nowhere else.

**It is not a sweep point**, and every reason is a property a reader can check:

- `tp.MAX_STEPS` is monkeypatched from 200 to **4** (and `CHECKPOINT_INTERVAL` 50 → 2,
  `EVAL_INTERVAL` 10 → 1, `WARMUP_STEPS` 20 → 1);
- **no question is scored** and **no utility reading is produced**;
- the prefixed adapter / CSV / checkpoint under `phase23_resume_probe_a` and
  `phase23_resume_probe_b` are **deleted at the end** (`git status --porcelain results/` prints
  nothing; `ls checkpoints/phase23_resume_probe_*` returns "no matches found");
- **zero `results/phase23_*` records are committed.**

So it can inform neither the noise floor nor the D-04 verdict. That last property is also exactly
what makes it **invisible to all three of 23-03's ancestry guards**, which bind on COMMITTED
records: 23-04's wiring probe is auditable from the repo because it commits a record declaring
`sweep_point: false`; this probe commits nothing at all. **23-10 is the plan that runs the full
200-step path.**

The verbatim docstring half of the disclosure (`grep -A 25
"def test_production_resume_epsilon_bit_identical" tests/test_phase23_resume.py`):

> THE DPSGD-06 EXCEPTION, DISCLOSED RATHER THAN HIDDEN. SC1 and DPSGD-06 say the σ=0 diagnostic
> is the DP arm's FIRST executed run. This test breaks that LITERAL ordering: it runs the
> PRODUCTION caller on the PRODUCTION `dp_n8` arm at σ > 0, in wave 2, three waves before 23-10's
> σ=0 run. It is NOT a sweep point, and each reason is a property a reader can check: `MAX_STEPS`
> is monkeypatched to 4, no question is scored, no utility reading is produced, the prefixed
> adapter / CSV / checkpoint are deleted at the end, and **zero `results/phase23_*` records are
> committed**. So it can inform neither the noise floor nor the D-04 verdict. That last property
> is also exactly what makes it INVISIBLE to all three of 23-03's ancestry guards, which bind on
> COMMITTED records: 23-04's wiring probe is auditable from the repo because it commits a record
> declaring `sweep_point: false`, while this probe commits nothing at all. This docstring and the
> plan SUMMARY are therefore the only two places the disclosure can live, which is why it is
> written out in full here rather than left for a reader to reconstruct from wave numbers.

`_PROBE_SIGMA = 1.0` / `_PROBE_CLIP = 1.0` / `_PROBE_DELTA = 1e-5` are **probe values, not a
budget**. They live in a test file; the AST guard `test_cli_names_no_sigma_or_clip_value` scopes
itself to `scripts/teach_persona.py`, whose no-literal property is unchanged
(`git diff --exit-code` on that guard's target passes, and `tests/test_phase22_wiring.py`'s
`_FIXTURE_SIGMA` is the committed precedent).

## The Refusal Battery — What Each One Watches

`.venv/bin/python -m pytest tests/test_phase23_resume.py -v` → **9 passed in 104.78s, ZERO
skipped** on the M3.

| test | threat | what it watches |
| --- | --- | --- |
| `test_resume_from_none_is_inert` | T-23-37 | 15 raw grep hits vs a 15-entry register, per file and per kind by AST; **8 pre-existing call sites**, none passing `resume_from` |
| `test_refuse_if_exists_is_resume_aware` | — | the four-row table on the helper, both senses |
| `test_train_arm_guard_splits_per_target` | T-23-33 / T-23-35 | the same table through the PRODUCTION driver, plus each required target removed alone |
| `test_the_resume_aware_branch_is_watched_red` | T-23-36 | a weakened `expected` branch vs the real one |
| `test_cross_arm_resume_is_refused` | T-23-34 | both arms and both paths named in the message |
| `test_cross_device_resume_is_refused_cpu_runtime` | T-23-38 | MPS-written state under a cpu runtime — **the leg that runs in CI** |
| `test_cross_device_resume_is_refused_mps_runtime` | T-23-38 | a real 5,056-byte CPU state on the M3 |
| `test_a_checkpoint_without_a_device_record_is_refused` | T-23-38 | absent `dp_noise_rng` named as the missing key |
| `test_production_resume_epsilon_bit_identical` | D-01 / WARNING-2 | the whole claim above |

**Mutation evidence for the watched RED**, run and reverted in this session: replacing
`if not want.exists():` with `if False:` in `refuse_if_exists` turned **3 of 8** tests RED
(`test_refuse_if_exists_is_resume_aware`, `test_train_arm_guard_splits_per_target`,
`test_the_resume_aware_branch_is_watched_red`) — `3 failed, 5 passed`. `scripts/teach_persona.py`
was restored byte-identically (`git diff --exit-code` 0) before Task 1's commit.

## Deviations from Plan

### `[Rule 3 — Blocking]` `resume_from` had to reach `build_arm_bins`, which the plan said not to touch

**Found during:** Task 1, before any test existed.
**Issue:** `build_arm_bins:932` calls `refuse_if_exists(arm_bin_targets(arm, outputs))` — the
SECOND caller of `arm_bin_targets`. The plan's `<action>` (c) inverts only `train_arm`'s guard,
and its `<action>` closing line says "Do not touch … `build_arm_bins`". With the bins required
PRESENT on a resume (the inversion), `build_arm_bins` then refuses on their presence three lines
later. **The seam would have been dead on arrival at every resume.**
**Resolution:** `build_arm_bins` gained the same `resume_from=None` additive parameter. This is
what the plan's own `key_links` entry asks for — *"both callers of `arm_bin_targets` cannot
drift"* — so the `<action>` prose and the `key_links` contradict each other and the code decides.
**Files:** `scripts/teach_persona.py`. **Commit:** `aa91123`.

### `[Rule 2 — Missing critical functionality]` a resume REBUILDS the bins and refuses on byte drift

**Found during:** Task 1, deciding what "resuming with regenerated bins resumes a different
corpus" (T-23-35) should DO.
**Issue:** requiring the bins present proves they exist, not that they are the same corpus.
**Resolution:** on a resume `build_arm_bins` hashes the three bins, rebuilds them (the pack is
deterministic in `(facts, family_ids, second_person, replay_ratio, seed)`), and raises
`SystemExit` naming both digests if any byte moved. Skipping the rebuild would only ASSUME the
corpus; this proves it, and it keeps `n_facts` coming from the packer's own record count rather
than a second derivation read back off the fact bin. Measured green across four builds (above).
**Files:** `scripts/teach_persona.py`. **Commit:** `aa91123`.

### `[Deviation]` the checkpoint carries NO device field — the record is the `dp_noise_rng` byte length

**Plan text:** *"load the checkpoint's `rng`/`dp_noise_rng` metadata and compare the recorded
device against the device `preflight_device`/`RuntimeConfig` just resolved."*
**Code:** `save_checkpoint` writes no device key. `rng["mps"]` records only that the SAVING MACHINE
had MPS available, which on the M3 is true even for a `device="cpu"` run — it is not a record of
the run's device. `train_config` is `asdict(TrainConfig)` and `TrainConfig` has no device field.
**Resolution:** the recorded device is derived from `dp_noise_rng.numel()`, which is the ONLY
device-typed thing in the checkpoint and is exactly the tensor torch refuses. Candidate lengths
are **probed** (`torch.Generator(device=d).get_state().numel()`), never hardcoded, so the guard
self-calibrates if a torch release moves 5,056 or 44. The check is scoped to DP arms, because a
non-DP resume has no such tensor and no ε to protect.

### `[Deviation]` an absent `dp_noise_rng` is REFUSED at the driver, where `train()` tolerates it

`loop.py`'s branch (2) reads an absent slot as *"not a DP run, seed fresh"* and two committed
guards assert that tolerance. This plan refuses the same shape at `train_arm`. The asymmetry is
deliberate and reddens nothing: both committed guards drive `train()` directly, never `train_arm`
(verified — full suite green). At the LOOP level the absence means "no DP run wrote this"; at the
DRIVER level, where a DP ARM asked to continue it, it means the ε prefix this resume claims to
continue never existed.

### `[Deviation]` the negative control is NOT a different-seed resume

**Plan text:** *"resume with a DIFFERENT DP seed and assert the ε or the composed count diverges."*
**Measured objection:** ε is a function of (σ, T, δ) and is **structurally blind to the seed**, and
T is too — a different seed diverges neither. Worse, `train_arm(seed=)` also seeds the BINS build,
so a different seed at that level is caught first by the byte-drift refusal above (correctly).
**Resolution, three controls that do carry evidence:**
1. the resumed seam is CONSTRUCTED at `_RESUME_SEED = 999` (injected at the `DPSGD` constructor,
   not at `train_arm`), and its birth state is asserted `!=` the kill checkpoint's `dp_noise_rng`
   — so a match at the end can only be the restore firing;
2. the draw is asserted **position-sensitive**: the kill half's seam, stopped at step 2, must NOT
   produce the run-to-4 seam's next draw;
3. the stripped-slot control is **unreachable through this driver by design** (it is refused, per
   the deviation above) and stays watched at the loop level by
   `test_resume_epsilon_bit_identical`'s own negative control on BOTH `cpu` and `mps`.

### `[Deviation]` two prefixes, not one

The plan names `prefix="phase23_resume_probe"`. Arm A completes and writes an adapter, so arm B
needs a disjoint prefix or `refuse_if_exists` refuses it. Used `phase23_resume_probe_a` /
`phase23_resume_probe_b`; both scrubbed at the end.

### `[Deviation]` the register counts 15 hits, not 11

The plan's acceptance criterion equates `len(_TRAIN_ARM_CALL_SITES)` to
`grep -rn "train_arm(" --include="*.py" scripts tests | wc -l`, which was **11 at the base commit**
and is **15 now** — this plan's own docstring and test file add hits. The register is a flat tuple
of `(path, kind, symbol)` with one entry per raw hit, and a separate assertion pins the count that
actually matters: **exactly 8 `call` entries outside this file**, none passing `resume_from`. Prose
in the new test file deliberately writes `train_arm` without its paren so the register does not
count its own commentary.

### `[Deviation]` no `--resume` CLI flag

Task 1 permits one only "if the `main` argv slicer needs it for Task 3". It does not — Task 3
calls `train_arm` directly. `main` is byte-unchanged apart from being counted in the register.

## Requirements

**DPSGD-06 is deliberately NOT ticked.** It reads *"The σ=0 point is the DP arm's first executed
run"*. This plan ran σ = 1.0 and is the DISCLOSED EXCEPTION to that ordering, not its satisfaction.
**23-10 is the plan that can tick it.** Ticking it here would record a run that has not happened —
the same over-claim 23-01…23-06 each declined.

## Verification

```
.venv/bin/python -m pytest tests/test_phase23_resume.py -v        -> 9 passed, 0 skipped  (104.78s)
.venv/bin/python -m pytest tests/ -q                              -> 1472 passed, 1 skipped (357.63s)
make lint                                                          -> All checks passed
git diff --exit-code -- src/personacore/training/loop.py \
    scripts/mitigation_accountant.py scripts/mitigation_gate.py \
    pyproject.toml scripts/phase23_prereg.py                      -> 0  (FROZEN OK)
git status --porcelain results/                                    -> (empty)
ls checkpoints/phase23_resume_probe_*                              -> no matches found
grep -cE "\brel_tol\b|\bmath\.isclose\b|\bpytest\.approx\b|\bapprox\(" \
    tests/test_phase23_resume.py                                   -> 0
grep -c "^assert \|    assert " scripts/teach_persona.py            -> 0 (HEAD: 0, unchanged)
```

Baseline at the base commit `4318f2d` was `1463 passed, 1 skipped`; +9 tests → `1472 passed,
1 skipped`. The one skip is pre-existing (`tests/test_train_loop.py:81`, fp16 AMP needs CUDA).

**`scripts/phase23_prereg.py` is byte-unchanged** — the ancestry-guard tripwire holds
(`git diff --exit-code` 0), and nothing in this plan reads or writes it.

## gsd-sdk Hazards — SIXTEENTH Session in a Row

Snapshot taken before the first call; `git diff .planning/` read after EVERY call.

- `state.advance-plan` — counters CORRECT (`Plan: 7 of 14` → `8 of 14`), `stopped_at` left STALE at
  23-06 (not regressed backwards; `record-session` corrected it as a side effect). CORRUPTED:
  flattened the body `Status:` from `Executing Phase 23` to `Ready to execute`; returned
  `last_updated` QUOTED; advanced `last_activity` and the body `Last activity:` to the UTC date
  `2026-08-27` against a local date of `2026-08-26` that every commit carries. `completed_plans`
  FAILED TO INCREMENT (stayed 53; hand-set to 54) — the 23-04 failure mode, which had NOT
  reproduced in 23-06.
- `state.record-metric --flag` — CLEAN. `| Phase 23 P07 | 55min | 3 tasks | 2 files |`, no unit
  doubling, `completed_phases` 3 and `percent` 33 both untouched. Positional argv still refused.
- `state.record-session --flag` — CLEAN, and corrected `advance-plan`'s stale `stopped_at`.
- `roadmap.update-plan-progress 23` — MANGLED the row's trailing cells to `| In Progress|  |`,
  dropping the `-` date placeholder, for the fourth session running. It also could not tick the
  23-07 checkbox or move the row past `6/14`, because it counts SUMMARY files on disk and this
  SUMMARY did not exist yet — hand-set to `7/14` and the checkbox hand-ticked.
- `state.update-progress` and `state.add-decision` were **NOT CALLED**, following 22-17/22-18's
  measured conclusion: `update-progress` has returned the identical
  `{"updated": false, "reason": "Progress field not found in STATE.md"}` since 22-12 while still
  re-stamping and re-quoting `last_updated`, and `add-decision` has written `- [Phase ?]: ` (or
  nothing at all, 23-04) in every session since 22-16 AND reverts `completed_plans` from a stale
  read (23-05). The decisions below and the position are hand-written.

All corruptions hand-repaired 1-line-for-1-line against the pre-call snapshot.

## Self-Check

- `scripts/teach_persona.py` — FOUND (modified, `git log` shows `aa91123`)
- `tests/test_phase23_resume.py` — FOUND (created, `3c39165` + `0e60169`)
- `.planning/phases/23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio/23-07-SUMMARY.md` — FOUND
- commit `aa91123` — FOUND
- commit `3c39165` — FOUND
- commit `0e60169` — FOUND

## Self-Check: PASSED
