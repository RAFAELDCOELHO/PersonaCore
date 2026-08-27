---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: "10"
subsystem: privacy/sigma-zero-diagnostic
tags: [dp-sgd, sigma-zero, d-04-halt, pre-registration, mps, clip-non-binding, cal-01]
requires:
  - "scripts/phase23_prereg.py::sigma_zero_verdict (23-03, EDIT-ONCE, committed BLIND)"
  - "scripts/mitigation_budget.py::CONTROL_NOISE_FLOOR + _PROVENANCE (23-09, the PIN)"
  - "results/phase23_control_floor.json — the 5 control readings and the floor (23-08)"
  - "scripts/phase23_run.py::rebuild_arm_bins_verifying_sha256 / prove_bins_match (23-08)"
  - "scripts/teach_persona.py::train_arm(resume_from=, dp_sigma=, dp_clip_norm=) (23-07, 22-10)"
  - "the dp_n8 corpus sha256 triple recorded by 23-07"
provides:
  - "results/phase23_sigma_zero.json — the σ=0 readings, the D-04 verdict (HALT), the CAL-01 n=8 DP training block, full provenance"
  - "scripts/phase23_run.py::sigma_zero — the sub-mode; ::train_sigma_zero; ::captured_dp_seam; ::score_adapter"
  - "tests/test_phase23_prereg.py — 4 record-level guards re-checking DPSGD-06's ordering and D-04's verdict"
  - "THE MEASURED FACT that σ=0 BEATS the unmitigated control by 0.2222222222222222, 4.15x the floor"
affects:
  - "23-11 (BLOCKED — no noised sweep point may run)"
  - "23-12 (BLOCKED)"
  - "23-13 (BLOCKED — Z is sized from a sweep that cannot run)"
  - "23-14 (BLOCKED)"
tech-stack:
  added: []
  patterns:
    - "shadowing a production driver's internally-constructed seam at its CONSTRUCTOR to read counters the driver does not return"
    - "a refusal proven BEFORE the reading it would confound exists, with the ordering recorded as a field"
    - "a census allow-set carrying COUNTS rather than a file-level exemption, so a vanishing consumer reddens too"
key-files:
  created:
    - results/phase23_sigma_zero.json
    - results/phase23_sigma0_dp_n8/run.csv
  modified:
    - scripts/phase23_run.py
    - tests/test_phase23_prereg.py
    - tests/test_phase23_resume.py
    - scripts/phase23_cost.py
    - .planning/phases/23-.../23-RESEARCH.md
decisions:
  - "D-04 HALTED the sweep: σ=0 read 790/1008 = 0.7837301587301587 against a control central of 566/1008 = 0.5615079365079365 — deviation 0.2222222222222222 vs a floor of 0.05357142857142849, i.e. 4.15x. Direction: BEATS."
  - "Nothing was retried, re-seeded, widened or tuned after the number existed. The record carries the raised message verbatim."
  - "C = 1e6 (the repository's established _NON_BINDING_CLIP) — clip_bind_count 0 over all 200 steps, asserted BEFORE scoring. ONE attempt; no second C was needed."
  - "DPSGD-06 TICKED: the σ=0 point was the DP arm's first executed run and the diagnostic fired. CAL-01 NOT ticked — 23-11 owns COST_RECORD and the n=64 leg."
  - "23-RESEARCH's 3.79 min dp_n8 training figure is RETRACTED: it was a projection called a lower bound, and the real run measured 205.44 s covering strictly more work."
patterns-established:
  - "the σ=0 arm consumed 8x the training tokens of the control over the same 200 optimizer steps (3,276,800 vs 409,600) — the residual differences are a number, not a caveat"
requirements-completed: [DPSGD-06]
metrics:
  duration: "~95 min"
  completed: 2026-08-27
  tasks: 3
  files: 7
  commits: 5
---

# Phase 23 Plan 10: The σ=0 Diagnostic Summary

**D-04 FIRED. The sweep is HALTED with zero noised points.** The σ=0 arm read
**790/1008 = 0.7837301587301587** taught recall against the control's central
**566/1008 = 0.5615079365079365** — a deviation of **0.2222222222222222** against a floor of
**0.05357142857142849**, or **4.15×** the floor, in the **BEATS** direction. The verdict came from
`phase23_prereg.sigma_zero_verdict`, committed blind in 23-03, against a floor pinned in 23-09,
both strictly before this reading existed. Nothing was re-run, re-seeded, widened or tuned.

## THE VERDICT, IN D-04's OWN TERMS

```
[phase23_prereg] D-04 HALT — THE SWEEP IS HALTED: zero noised points will run.
  σ=0 reading      : 0.7837301587301587 (BEATS the control)
  control central  : 0.5615079365079365 (reading at the FIRST recorded seed)
  deviation        : 0.2222222222222222
  noise floor      : 0.05357142857142849
  floor record     : results/phase23_control_floor.json
```

| quantity | value | source |
|---|---|---|
| σ=0 primary reading | `0.7837301587301587` (790/1008) | `results/phase23_sigma_zero.json` |
| control central (seed 1337) | `0.5615079365079365` (566/1008) | `results/phase23_control_floor.json` |
| deviation | `0.2222222222222222` (= 224/1008) | reported; the DECISION is the rule's |
| floor | `0.05357142857142849` (= 54/1008) | `mitigation_budget.CONTROL_NOISE_FLOOR`, exact `==` |
| admissible band | `[0.507936507936508, 0.615079365079365]` | central ± floor |
| deviation ÷ floor | **4.148148148148154×** | — |
| verdict | **`HALT`** | `phase23_prereg.sigma_zero_verdict` |

**The decision this produces.** `proceed` would have unblocked 23-11, the milestone's first noised
run. `HALT` **blocks 23-11, 23-12, 23-13 and 23-14** until the cause is root-caused and fixed.
There is no warning branch and no override flag, and none was added.

**This is the direction that matters.** Every correctness bug in this class *improves* utility, so a
σ=0 that BEATS the control is the signal a real one produces — which is why `sigma_zero_verdict`
carries its own `beats` case and why `test_floor_breach_halts_the_sweep` asserts that direction
separately. The instrument fired in exactly the mode it was built for.

## THE RAW NUMBERS

Every rate carries its denominator. **112 taught questions × 9 draws/question = 1,008 draws** and
**72 held-out × 9 = 648**, four tiers, 3,312 draws this leg — the identical shape the control's five
readings were taken at, off the identical `tp.score_arm` call.

### σ=0 (`dp_n8`, seed 1337, mps, torch 2.7.1) against all five control seeds

| arm / seed | taught ON (PRIMARY) | rate | held-out ON | taught OFF | held-out OFF | PPL ON | final loss |
|---|---|---|---|---|---|---|---|
| **σ=0 dp_n8 / 1337** | **790/1008** | **0.7837301587301587** | 346/648 = 0.5339506172839507 | 0/1008 | 0/648 | 4.7084 | 0.0604 |
| control / **1337** | 566/1008 | **0.5615079365079365** ← CENTRAL | 238/648 = 0.367284 | 0/1008 | 0/648 | 6.2303 | 0.6380 |
| control / 2024 | 530/1008 | 0.5257936507936508 | 223/648 = 0.344136 | 0/1008 | 0/648 | 6.1052 | 0.7000 |
| control / **1338** | 575/1008 | 0.5704365079365079 ← MAX | 243/648 = 0.375000 | 0/1008 | 0/648 | 6.0990 | 0.5428 |
| control / 2025 | 531/1008 | 0.5267857142857143 | 231/648 = 0.356481 | 0/1008 | 0/648 | 6.1771 | 0.8151 |
| control / **1339** | 521/1008 | 0.5168650793650794 ← MIN | 245/648 = 0.378086 | 0/1008 | 0/648 | 6.1274 | 0.5542 |

The σ=0 reading is **215 draws above the control's MAXIMUM seed** (790 vs 575). It is not near the
band; it is not in the same distribution.

### Secondary readings, recorded and NOT reduced

| reading | σ=0 | control seed 1337 | denominator |
|---|---|---|---|
| held-out recall ON | 0.5339506172839507 | 0.36728395061728397 | 648 draws (72 q × 9) |
| taught / held-out OFF | 0.0 / 0.0 | 0.0 / 0.0 | 1008 / 648 draws |
| per-family gain | F1 0.8444, F2 0.8222, F6 0.6597 | F1 0.6611, F2 0.5639, F6 0.4340 | per family |
| held-out per-family std | 0.04933446717020304 | 0.023096650535641604 | 3 families (pstdev) |
| masked dialogue-val PPL ON | 4.708399666491714 | 6.2303165273588235 | 270,203 scored targets |
| masked dialogue-val PPL OFF | 4.573349214207799 | 4.573349214207799 | 270,203 (identical — same base) |

**Every secondary reading moves the same way**: the σ=0 arm learned the facts harder AND collapsed
dialogue quality less (+2.95% PPL vs the control's +36.2%). That is one coherent effect, not noise.

## THE MECHANISM'S OWN COUNTERS — measured BEFORE any reading existed

| quantity | measured | why it is here |
|---|---|---|
| `clip_bind_count` | **0** over all 200 steps | at σ=0 the only thing C can do is CLIP; a binding C would make the arm differ from the control by clipping rather than by the DP arithmetic |
| `clip_norm` (C) | `1000000.0` | the repository's established `_NON_BINDING_CLIP` (`test_phase22_checkpoint.py:97`, `test_phase22_fakes.py:93`) |
| `records_per_lot` (`_records`) | **8** | equals the configured `grad_accum_steps` — SC2's "one micro-step = one privacy record" |
| composed steps T | **200** | counted off real `DPSGD.finalize` invocations (`t_source: "_count_composed_steps"`), never `ckpt["step"]` |
| composed lot sizes | `[8]` | every one of the 200 lots held exactly 8 records |
| σ | `0.0` exactly | no branch skips the draw; `torch.normal(std=0.0)` returns exact zeros and still advances the generator (23-01, watched GREEN on MPS) |

**ONE attempt at C. No second C was needed and none was tried.** `clip_bind_count == 0` was asserted
inside `train_sigma_zero` **before** `score_adapter` was called — the ordering is recorded in the
artifact as `clip_checked_before_scoring: true` and re-asserted by
`test_the_clip_was_non_binding_at_sigma_zero`. The plan's contingency ("if non-zero, re-run at a
larger C and record both attempts") did not trigger.

## THE CORPUS — 23-07's digests and this run's, side by side

`shasum -a 256 data/persona_dp_n8_train*.bin`, at run time:

| file | 23-07 recorded | this run |
|---|---|---|
| `persona_dp_n8_train.bin` | `e14517954f56fa2d3ff55b63096a86dec08535e62ea7d3f77903afb4a3e80735` | identical |
| `persona_dp_n8_train_mask.bin` | `732223f3844299f3c4eadff7b05f9a2ba077c48e6792880d89fc6929abd74045` | identical |
| `persona_dp_n8_train_fact.bin` | `34d04ac76adf0ed802d3305eb77cb47270311f8f93aee89581f89e33c3f6f2c2` | identical |

Proved **three times**: before the delete (a corpus that had already drifted is refused while it
still exists), after `rebuild_arm_bins_verifying_sha256`'s rebuild, and after `train_arm` built the
bins it actually trained on. All three through `prove_bins_match`; this driver computes no digest
comparison of its own.

`git ls-files 'results/phase23_noised_*'` at run time: **EMPTY** — printed by the driver's own
`_prove_no_noised_record_exists()` before a single token was written, and it is still empty at HEAD.

## CAL-01 — the n=8 DP-path training wall clock

Bracketed by `synchronized_seconds`, `torch.mps.synchronize()` immediately before `t0` and
immediately before `t1`. Training has **no per-step host sync at all on MPS**, so the explicit
synchronize is what makes this completed work rather than submission.

| quantity | measured |
|---|---|
| `seconds_total` | **205.44225783273578 s** |
| `seconds_per_optimizer_step` | **1.0272112891636789 s** |
| `timed_iterations` | **200** |
| `warmup_iterations_discarded` | **0** (the timed leg is the whole run, start to finish) |
| `timing_is_uninterrupted` / `resumed_from_step` | `true` / `0` |
| shape | `max_steps` 200, `batch_size` 8, `block_size` 256, `grad_accum_steps` 8, `replay_windows_per_step` 32, `replay_micro_batches_per_step` 4, `capacity_n_facts` 8 |
| what the bracket covers | the WHOLE `train_arm` call — `build_arm_bins`, the base-checkpoint load, the 200-step loop with 20 in-loop evals and 4 checkpoint writes, the replay memmap I/O, and BOTH end-of-run `masked_perplexity` sweeps |

Validated by `phase23_cost.validate_record(kind="training")` — every one of the 17
`TRAINING_RECORD_KEYS` present, refused rather than defaulted.

**Against the projected 3.79 min lower bound — the projection is FALSIFIED and RETRACTED.**
23-RESEARCH §R3.A projected 227.6 s (1138.0 ms/step) for the `dp_n8` **200-step loop only**, and
called it a LOWER BOUND, explicitly excluding five components. The measured 205.44 s **includes all
five** and is still **22.2 s (−9.8%) shorter**, so the loop-only quantity is below 1027.2 ms/step
and the projection over-states it by **at least 10.8%**. Retracted in place at both citation sites
in 23-RESEARCH.md and at the falsified restatement in `scripts/phase23_cost.py`'s
`TRAINING_RECORD_KEYS` comment. **The `dp_n64` figure (1798.6 s ≈ 29.98 min) is the same arithmetic
at accum=64, is unmeasured, and now inherits the same doubt** — it is labelled as a projection.

Scoring: **952.0680559994653 s** over 3,312 draws (the control's five passes ran 983.2–1026.9 s).

## THE ROOT-CAUSE STARTING POINT — the control's four `residual_differences`, quoted

D-04 requires the cause to be root-caused and fixed before any noised point runs. **This SUMMARY
does not decide the cause** — it records what 23-08 enumerated in advance as the known structural
differences, verbatim from `results/phase23_control_floor.json`, which is where the hunt starts:

1. **"replay lives IN the teaching bin here; it is drawn at TRAIN time on the DP path."**
   *Matched:* the replay TOKEN volume (8,192, recorded as a number). *Not eliminable:* D-10/D-24 put
   replay outside the teaching bin for DP arms and `train()`'s replay seam is gated on `is_dp`; a
   non-DP arm cannot reach it without widening `DP_ARMS`, which would make the control a DP arm.

   > **CORRECTED 2026-08-27** — debug session `sigma-zero-beats-control`, TASK 2. *"Matched: the
   > replay TOKEN volume"* holds PER OPTIMIZER STEP only. Run totals: control ≈ **212,733** replay
   > tokens against the DP arm's **1,638,400** — **7.70×**, because `replay_windows=32` is a
   > **per-step** budget (`loop.py:306`) while the control's 8,192 are a one-time bin volume.
   > What is genuinely matched is the per-lot COMPOSITION (48.06/51.94 vs 50.77/49.23). See
   > 23-08-SUMMARY's dated retraction for the full derivation.
2. **"grad_accum_steps is 1 here and `n_facts` on the DP path."** *Matched:* nothing. *Not
   eliminable:* the same `is_dp` predicate. The control's lot is one micro-batch; the DP arm's lot is
   one privacy record per micro-step (SC2).
3. **"the flat v3.0 pack here; the ragged fact-aligned three-bin pack there."** *Matched:* the fact
   set and taught family ids, which ARE identical. *Not eliminable:* the arm NAME couples an arm to
   its packer.
4. **"the DP arithmetic itself — per-record clip at C, a summed accumulator, and the division by N
   last."** *Matched:* nothing. *Not eliminable:* `DPSGD` is constructed only when `is_dp`. At σ=0
   the noise term is exactly zero but the CLIP and the accumulate-then-divide remain, **so σ=0 is
   not the control computation with a zero added to it.**

**One number makes residual 2 concrete rather than rhetorical.** The CSV `tokens` column at step 200:

| arm | tokens at step 200 | steps | ratio |
|---|---:|---:|---:|
| σ=0 `dp_n8` | **3,276,800** | 200 | **8×** |
| control seed 1337 | **409,600** | 200 | 1× |

The σ=0 arm consumed **eight times the training tokens** over the same 200 optimizer steps, which is
exactly `grad_accum_steps = n_facts = 8` against the control's 1. Its final train loss is 0.0604
against 0.6380 and its step-200 val_loss is 1.5833 against 1.8330. **A root-cause hunt that starts
anywhere other than "is the control a valid comparator at all?" is starting in the wrong place** —
and clip is excluded by measurement (`clip_bind_count == 0`), so residual 4's clip half is not it.

**What this does NOT establish.** Nothing here rules out a genuine DP-path correctness defect; the
structural residuals are a candidate, not a finding. Distinguishing them requires a comparator the
σ=0 arm can be judged against — which is a root-causing job for a follow-up plan, not a conclusion
this one is entitled to draw. **The halt stands either way.**

## The ordering guards — MEASURED before and after, not claimed

`git ls-tree -r --name-only <ref>` at the base commit `9ed2370` and at HEAD:

| guard | binds on `git ls-files <glob>` | at `9ed2370` | at HEAD | live? |
|---|---|---:|---:|---|
| `test_the_prereg_rule_precedes_every_phase23_result` | `results/phase23_*` | 13 | **15** | already live since 23-04 |
| `test_control_precedes_sigma_zero` | `results/phase23_sigma_zero.json` | 0 | **1** | **NOW LIVE — this plan's artifact** |
| `test_sigma_zero_precedes_every_noised_point` | `results/phase23_noised_*` | 0 | **0** | **STILL VACUOUS** |
| `test_every_noised_sweep_point_is_under_the_noised_glob` | tracked `.json` under `results/phase23_*` | 3 | **4** | live, scanning 4 |

**Exactly ONE guard transitions.** 23-08 corrected the plan brief's framing on this point and the
correction holds: guard 2's glob is `SIGMA_ZERO_RECORD` — this plan's own artifact — so 23-10 is
where it activates. Guard 3, DPSGD-06's own ordering guard, stays vacuous because no noised record
exists, and the HALT now forbids one from existing. It will activate only after the root cause is
fixed and a sweep point is permitted.

**The ordering is a fact about git.** `git log --diff-filter=A` earliest adds:

```
control floor : cb0e5bf40347d1ead9bc4401f209f8d821c29d55  2026-08-27 02:34:03 -0300  (23-08)
σ=0 record    : 2d069898f475fe0dc01da4518fa791de83a3454e  2026-08-27 03:53:56 -0300  (23-10)
git merge-base --is-ancestor control σ=0  -> TRUE
git merge-base --is-ancestor σ=0 control  -> FALSE   (strict, not merely non-descendant)
```

The floor was in the repository **1 h 19 min** before the reading it judges existed, and
`scripts/mitigation_budget.py` is byte-unchanged since 23-09 — verified by
`git diff --exit-code`, which exits 0 for all four frozen modules and `pyproject.toml`.

## What Shipped

| Task | Name | Commit | Files |
|---|---|---|---|
| 1 | The `sigma-zero` sub-mode + the run | `0e503ed` | `scripts/phase23_run.py`, `results/phase23_sigma0_dp_n8/run.csv` |
| 2 | The record and the blind verdict | `2d06989` | `results/phase23_sigma_zero.json` |
| 3 | The four record-level guards | `0f8cb59` | `tests/test_phase23_prereg.py` |
| — | The 3.79 min retraction | `0488f54` | `23-RESEARCH.md`, `scripts/phase23_cost.py` |
| — | The `resume_from` census widening | `8c4526a` | `tests/test_phase23_resume.py` |

**The four new guards** (`tests/test_phase23_prereg.py`, all passing, zero skips):

- `test_the_sigma_zero_record_is_the_dp_arms_first_run` — the record is TRACKED and declares
  `sigma == 0.0`, then `_ordering_guard` (23-03's, CALLED not copied) binds every noised point
  behind it. The added half is the one the guard cannot supply alone: an untracked pin pins nothing.
- `test_the_sigma_zero_verdict_re_derives` — re-runs the blind rule on the record's stored values.
  **HALT is the RAISING branch**, so the message is compared VERBATIM against the stored one; a test
  that only compared return values would have ERRORED on the very outcome D-04 exists to produce.
  Also asserts `reading == k/n == rate` and `deviation == |reading − control_readings[0]|`.
- `test_the_sigma_zero_record_used_the_pinned_floor` — exact `==` against
  `mitigation_budget.CONTROL_NOISE_FLOOR` and its provenance dict (T-23-51).
- `test_the_clip_was_non_binding_at_sigma_zero` — `clip_bind_count == 0`, the counter's step
  coverage, `records_per_lot == grad_accum_steps`, and `T == timed_iterations`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `rebuild_arm_bins_verifying_sha256` leaves the bins on disk, and
`train_arm` then REFUSES them**
- **Found during:** Task 1, reading `train_arm`'s five-target guard before the run
- **Issue:** the helper deletes, rebuilds and proves — so the bins EXIST when it returns. A fresh
  `train_arm(resume_from=None)` calls `refuse_if_exists(arm_bin_targets(arm, paths) + [...])` and
  treats each bin as recorded evidence. The plan's literal sequence cannot run.
- **Fix:** call the helper (it is the named T-23-55 mitigation and its proof is real), then delete
  the three bins again so `train_arm` builds them itself from the SAME deterministic
  `(facts, family_ids, second_person, replay_ratio, seed)`, then `prove_bins_match` a third time
  after the run. **This is strictly stronger than the plan's sequence**: the final proof binds the
  bins the 200 steps ACTUALLY consumed rather than a rehearsal that was thrown away.
- **Commit:** `0e503ed`

**2. [Rule 3 — Blocking] `test_resume_from_none_is_inert` forbade the seam's first production use**
- **Found during:** the post-Task-3 full-suite run (17 grep hits against a 16-entry register)
- **Issue:** the census also asserted `passers == []` for every file except the test file itself, so
  any production call passing `resume_from` reddened it — i.e. 23-07's seam could never be used in
  production, the IN-04 failure that file's own register warns about.
- **Fix:** `_RESUME_PASSERS` names WHO may pass the kwarg and HOW MANY times
  (`tests/test_phase23_resume.py` 2, `scripts/phase23_run.py` 1). **Every pre-existing site is
  pinned at ZERO by its ABSENCE from the map**, so "byte-identical to its pre-23-07 form" is
  unchanged for all eight. The guard also stopped `continue`-ing past its own file: the old skip
  meant a passer VANISHING from the one file allowed to have them was invisible, and a count catches
  both directions. Measured passers: `[135, 540]` / `[900]` (`train_control` at 537 passes nothing,
  which is why this is a count and not a file-level exemption). The `8 + 1` literal is now
  `8 + 1 + 1` with its reason spelled.
- **Commit:** `8c4526a`

**3. [Rule 1 — Bug] A falsified projection was cited as a measurement in shipped source**
- **Found during:** comparing the measured 205.44 s against the plan's stated 3.79 min lower bound
- **Issue:** 23-RESEARCH §R3.A's `dp_n8` row is a PROJECTION from a synthetic micro-benchmark, was
  labelled a LOWER BOUND, and is restated in `scripts/phase23_cost.py:80` in a table headed
  "Measured training". The measurement falsifies it in the over-estimate direction.
- **Fix:** retracted in place at both 23-RESEARCH citation sites and at the `phase23_cost.py`
  comment, dated, naming what measured it false. The `dp_n64` row is relabelled as the unmeasured
  projection it is.
- **Commit:** `0488f54`

### Deliberate departures from the plan text

**A. `floor_provenance` carries the pin's dict VERBATIM; the pin's module path is a SIBLING key.**
The plan asked for "the pin's provenance dict, copied verbatim, plus the pin's own module path" and
then required `record["floor_provenance"] == CONTROL_NOISE_FLOOR_PROVENANCE` under exact `==`. Those
two cannot both hold. The exact-equality test is T-23-51's mitigation and was not weakened, so the
module path lives beside it as `floor_pin_module` / `floor_pin_symbol` /
`floor_provenance_symbol`. The equality is asserted after a JSON round-trip of the pin, because
`seeds` is a tuple in the module and a list in the file and json.dump had no choice about that.

**B. `_count_composed_steps` is RESTATED in the driver, not imported from `tests/`.** The plan and
`tests/test_phase23_cal03.py` both import it from `tests/test_phase22_checkpoint.py`, but a
production driver importing from the test tree would make a real run depend on `tests/` being
importable (and `tests/` is not a package). The contract is four lines and is asserted against
`max_steps` at the call site, so a drifted copy cannot pass silently. The record's `t_source` still
names `_count_composed_steps`.

**C. ONE sub-mode, not two, with state-based reuse.** The plan describes Task 1's run and Task 2's
scoring separately; both live in `sigma-zero`, which reuses a digest-verified adapter through the
existing `_already_trained` helper and skips scoring if a reading is already recorded. A failure at
the record-assembly step therefore costs zero GPU time, which is why the 205 s training leg and the
952 s scoring leg were each run exactly once.

**D. `score_control` was refactored into `score_adapter` + a two-line delegate** rather than a
second scoring path being written for the σ=0 arm. The diagnostic IS a comparison; a reading off a
second pipeline is not comparable however carefully the second pipeline is written.

## Honest shortfalls and disclosures

1. **THE FULL PRE-REGISTERED RUN COMPLETED. Nothing was reduced.** 200 of 200 optimizer steps, all
   four scoring tiers, 3,312 draws, one seed (1337 — the seed `sigma_zero_verdict` pins as the
   central reading, asserted equal to `control["central_reading_seed"]` before the run started).
2. **σ=0 is the DP arm's first executed SWEEP-ARM run; 23-07's σ=1.0 probe is the disclosed
   exception.** That probe ran 4 steps at toy scale, exported no scored adapter and produced no
   reading. 23-07's own SUMMARY records the departure ("DPSGD-06 is NOT ticked: this plan broke its
   literal ordering rather than satisfying it"), and this SUMMARY restates it rather than relying on
   the reader to find it.
3. **The DP arm's `final_train_loss` (0.0604) is NOT comparable to the control's (0.6380)**, and no
   comparison is drawn from it: the DP teaching bin holds facts only while the control's holds facts
   plus 8,192 replay tokens, so the two losses are computed over different corpora. It is reported
   as a raw per-run number, not as evidence.
4. **`clip_bind_count` is run-lifetime on ONE seam instance.** On this run that covers all 200 steps
   (`clip_bind_count_covers_steps: 200`, `timing_is_uninterrupted: true`); a resumed run's counter
   would cover the resumed leg only, and the record carries the field so the difference is readable
   rather than assumed. No resume occurred.
5. **The seconds figure is a whole-`train_arm` bracket, not a loop-only one.** The record says so in
   a `bracket_covers` field. There is no loop-only measurement available — `loop.py:901` writes the
   STEP number into the CSV's `wall_clock` column, not a time — so a narrower figure would have
   required instrumenting `train()`, which this plan does not touch.
6. **The `_RESUME_PASSERS` widening was verified by measured counts, not by a watched RED.** The
   three counts (2 / 1 / 0-by-absence) were measured with an AST walk before the map was written; no
   deliberately-broken copy was driven through the assertion.

## Requirements

**DPSGD-06 — TICKED.** *"The σ=0 point is the DP arm's first executed run — the only cheap
diagnostic separating 'DP is hard at this scale' from 'the code is wrong', since every correctness
bug in this class improves utility."* The σ=0 point ran, it ran first (asserted at run time by
`git ls-files results/phase23_noised_*` returning empty, and permanently by the committed ordering
guard), and the diagnostic **fired** — which is the strongest possible evidence that the instrument
works. **Ticking it records the ordering and the diagnostic firing, NOT a passing verdict.** The
verdict is HALT and the sweep is stopped.

**CAL-01 — NOT ticked.** Its text asks for the training leg "confirmed on the DP path with the seam
active", and this plan measures exactly that at n=8. But `phase23_prereg.COST_RECORD`
(`results/phase23_cost.json`) is 23-11's artifact and the n=64 leg is unmeasured, so CAL-01 closes
there. This plan contributes the n=8 DP training block and the retraction of the projection that
stood in for it.

## Verification

```
$ .venv/bin/python -m pytest tests/ -q
1488 passed, 1 skipped, 83 warnings in 363.34s     (baseline 1484 + the 4 new guards; the
                                                    1 skip is the pre-existing fp16-AMP CUDA one)
$ make lint
All checks passed!  240 files already formatted

$ .venv/bin/python -m pytest tests/test_phase23_mps_venue.py -q
16 passed in 0.87s          — ZERO skips (the DPSGD-06 keystone, green before the run)

$ .venv/bin/python -m pytest tests/test_phase23_prereg.py -v
36 passed in 2.46s          — zero skips, all four new tests present

$ git diff --exit-code -- scripts/phase23_prereg.py scripts/mitigation_gate.py \
      scripts/mitigation_accountant.py scripts/mitigation_budget.py pyproject.toml
(exit 0 — the pre-registration, the frozen gate, the accountant, the PIN and the
 dependency set are all byte-unchanged; the floor was not touched after the reading existed)

$ git status --porcelain results/
(empty)
```

Acceptance criteria, measured:

| criterion | result |
|---|---|
| corpus digests match 23-07's exactly | ✅ all three, quoted side by side above |
| `git ls-files 'results/phase23_noised_*'` EMPTY at run time | ✅ printed by the driver, still empty at HEAD |
| `clip_bind_count` recorded and **0** | ✅ 0; one C attempt, no second needed |
| `_records` == `grad_accum_steps` (8), T == 200 | ✅ 8 and 200, T off `_count_composed_steps` |
| `seconds_total` / per-step with denominators + vs 3.79 min | ✅ 205.44 s / 1.0272 s over 200 timed, 0 discarded — projection retracted |
| mps venue suite, zero skips | ✅ 16 passed |
| verdict produced by CALLING `sigma_zero_verdict` | ✅ one call site; the driver runs no comparison |
| record committed after the control floor, before any noised record | ✅ strict-ancestor verified both directions |
| per-seed raw values in the SUMMARY | ✅ all five control seeds + σ=0, with k/n |
| `residual_differences` quoted | ✅ all four, verbatim |

## Files

**Created**
- `results/phase23_sigma_zero.json` — the σ=0 record: verdict, deviation, floor, the pin's
  provenance verbatim, every reading with its denominator, the CAL-01 training block, the corpus
  digests, the adapter sha256 and the four residual differences
- `results/phase23_sigma0_dp_n8/run.csv` — 20 eval rows, steps 10…200

**Modified**
- `scripts/phase23_run.py` — the `sigma-zero` sub-mode, `train_sigma_zero`, `captured_dp_seam`,
  `_count_composed_steps`, `_prove_no_noised_record_exists`, `score_adapter`
- `tests/test_phase23_prereg.py` — the four record-level guards
- `tests/test_phase23_resume.py` — the `resume_from` census widening
- `scripts/phase23_cost.py` — the retracted projection in a comment
- `.planning/phases/23-.../23-RESEARCH.md` — the retraction in place, both citation sites

**Untouched and verified so** — `scripts/phase23_prereg.py`, `scripts/mitigation_gate.py`,
`scripts/mitigation_accountant.py`, `scripts/mitigation_budget.py`, `pyproject.toml`.

## What happens next

**23-11, 23-12, 23-13 and 23-14 are BLOCKED.** Zero noised sweep points may run. The next plan is a
root-cause plan, not a sweep plan, and the first question it must answer is the one this measurement
poses: **is the unmitigated control a valid comparator for the σ=0 arm at all, given that the σ=0
arm consumed 8× the training tokens over the same 200 optimizer steps?** If it is not, the fix is a
comparator — not a re-run of σ=0 hoping for a different number, and not a wider floor. If it is,
the DP path has a correctness defect and the milestone's frontier cannot be published until it is
found. Either outcome is publishable; neither is reachable by re-running this arm.

`results/phase23_control_floor.json`'s `residual_differences` is the enumerated starting list, and
`clip_bind_count == 0` already removes clipping from it.

## Self-Check: PASSED

- `results/phase23_sigma_zero.json` — FOUND
- `results/phase23_sigma0_dp_n8/run.csv` — FOUND
- `scripts/phase23_run.py` — FOUND
- `tests/test_phase23_prereg.py` — FOUND
- commit `0e503ed` — FOUND
- commit `2d06989` — FOUND
- commit `0f8cb59` — FOUND
- commit `0488f54` — FOUND
- commit `8c4526a` — FOUND
