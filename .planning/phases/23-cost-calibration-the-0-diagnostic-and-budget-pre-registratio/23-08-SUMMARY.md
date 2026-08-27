---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: "08"
subsystem: privacy/measurement-driver
tags: [noise-floor, pre-registration, never-taught, control-arm, mps, seed-count, digest-guard]
requires:
  - "scripts/phase23_prereg.py::noise_floor / choose_n_seeds / H_PER_POINT_FLOOR_SECONDS (23-03, EDIT-ONCE)"
  - "scripts/phase23_cost.py::validate_record / TRAINING_RECORD_KEYS (23-05)"
  - "scripts/teach_persona.py::train_arm / score_arm / build_arm_bins / replay_window_budget"
  - "scripts/mitigation_gate.py::NEVER_TAUGHT_ARM / EXTRACTION_FLOOR_MIN_SEEDS (FROZEN, read-only)"
provides:
  - "scripts/phase23_run.py — the Phase-23 run driver (cost / schedule / floor sub-modes)"
  - "scripts/phase23_run.py::prove_bins_match(expected_sha256) — the corpus-drift refusal, ONE parameter"
  - "scripts/phase23_run.py::rebuild_arm_bins_verifying_sha256 — 23-10's sanctioned dp_n8 bin reuse"
  - "results/phase23_control_floor.json — D-03's MEASURED floor 0.05357142857142849 over 5 seeds"
  - "results/phase23_never_taught_training.json — CTRL-03's ONE scheduling, 5 exported adapters"
  - "N = 5 and the seed list (1337, 2024, 1338, 2025, 1339) for every later Phase-23 plan"
affects:
  - "23-09 (pins this floor into scripts/mitigation_budget.py as a literal)"
  - "23-10 (σ=0; reads the floor through sigma_zero_verdict, and calls rebuild_arm_bins_verifying_sha256)"
  - "23-13 (prices N_CONTROL_SEEDS = 5 into Z)"
  - "23-14 (scores the 5 never-taught adapters at the pinned K)"
tech-stack:
  added: []
  patterns:
    - "a blind rule IMPORTED from an edit-once module and never redefined in the driver that measures its input"
    - "a refusal split into a one-parameter pure function so it can be watched RED in milliseconds"
    - "reuse-by-digest-proof instead of skip-by-presence across sub-mode invocations"
key-files:
  created:
    - scripts/phase23_run.py
    - tests/test_phase23_ctrl.py
    - results/phase23_control_floor.json
    - results/phase23_never_taught_training.json
  modified:
    - tests/test_lora_inject.py
    - tests/test_phase23_resume.py
decisions:
  - "D-03's floor is 0.05357142857142849 (54/1008), the RANGE over 5 per-seed taught-recall-ON readings"
  - "N=5 from choose_n_seeds(996.2667346671224 s/seed): 5 x 996.27 = 4,981.33 s vs the 17,175 s bound — FITS"
  - "Neither DPSGD-06 nor CTRL-03 is ticked: σ=0 has not run and the never-taught arm has served neither duty"
  - "ZERO ordering guards went live in this plan — both remaining vacuous guards bind on globs still matching nothing"
patterns-established:
  - "cost -> schedule -> floor: the seed count is decided from a measurement before the arms it sizes exist"
  - "a multi-seed scheduling record validated at BOTH levels against the single-arm training schema"
requirements-completed: []
duration: 185min
completed: 2026-08-27
---

# Phase 23 Plan 08: The Measured Noise Floor and the One Scheduling Summary

**D-03's seed-to-seed noise floor is now a MEASUREMENT — 0.05357142857142849 (54/1008) reduced by
the blindly-committed `phase23_prereg.noise_floor` over five per-seed control readings — committed
while `git ls-files results/phase23_sigma_zero.json` returned nothing, alongside CTRL-03's
never-taught scheduling at the same five seeds.**

## Performance

- **Duration:** ~185 min (≈3h05m wall, of which ~2h50m is GPU: 6 scoring passes × ~1,000 s + 9 training legs)
- **Started:** 2026-08-27T00:06 (local, UTC-03:00)
- **Completed:** 2026-08-27T03:11 (local, UTC-03:00)
- **Tasks:** 3 of 3
- **Files created/modified:** 6

## THE MEASURED NUMBERS

### The per-seed PRIMARY readings — taught recall rate, adapter ON, over QUESTIONS

Every rate travels with its denominator. **112 taught questions × 9 draws/question = 1,008 draws**
per seed per tier; four tiers scored per seed (taught ON, held-out ON, taught OFF, held-out OFF).

| seed | taught ON (primary) | rate | held-out ON | taught OFF | held-out OFF | final train loss | scoring s |
|------|--------------------|------|-------------|------------|--------------|------------------|-----------|
| **1337** | 566/1008 | **0.5615079365079365** ← CENTRAL | 238/648 = 0.367284 | 0/1008 | 0/648 | 0.6380 | 996.3 |
| 2024 | 530/1008 | 0.5257936507936508 | 223/648 = 0.344136 | 0/1008 | 0/648 | 0.7000 | 1000.4 |
| **1338** | 575/1008 | **0.5704365079365079** ← MAX | 243/648 = 0.375000 | 0/1008 | 0/648 | 0.5428 | 993.4 |
| 2025 | 531/1008 | 0.5267857142857143 | 231/648 = 0.356481 | 0/1008 | 0/648 | 0.8151 | 983.2 |
| **1339** | 521/1008 | **0.5168650793650794** ← MIN | 245/648 = 0.378086 | 0/1008 | 0/648 | 0.5542 | 1026.9 |

**FLOOR = max − min = 0.5704365079365079 − 0.5168650793650794 = `0.05357142857142849`** (exactly
54/1008 in count space). Reduced by calling `phase23_prereg.noise_floor`; the driver types no
`max`, no `min` and no spread anywhere — `test_the_driver_defines_no_pre_registration_of_its_own`
asserts that by AST.

The **CENTRAL reading is `control_readings[0]` = seed 1337's 0.5615079365079365**, which
`sigma_zero_verdict` pins. In 23-10, σ=0's taught-recall-ON rate must land inside
`[0.5079365079365080, 0.6150793650793650]` or D-04 HALTS the whole sweep — in **either** direction.

**Adapter-OFF is 0/1008 and 0/648 on every seed.** The closed-book baseline is a clean zero: the
base model recovers none of the eight locked facts, so the ON rates above are recall the teaching
bought rather than anything the base could already answer.

### Secondary readings, recorded and NOT reduced

Masked dialogue-val PPL, adapter OFF/ON over **270,203 scored targets** (identical target set on
both passes, enforced by `train_arm`):

| seed | PPL OFF | PPL ON | Δ |
|------|---------|--------|------|
| 1337 | 4.5733 | 6.2303 | +36.23% |
| 2024 | 4.5733 | 6.1052 | +33.50% |
| 1338 | 4.5733 | 6.0990 | +33.36% |
| 2025 | 4.5733 | 6.1771 | +35.06% |
| 1339 | 4.5733 | 6.1274 | +33.98% |

Adapter-OFF is **bit-identical across all five seeds** (4.573349214207799) — the base never moves,
which is the canary passing five times over.

### Open Question 4, closed by MEASUREMENT

The scoring leg for ONE seed was timed with `torch.mps.synchronize()` at both boundaries:

- **`seconds_per_seed` = 996.2667346671224 s**
- denominators: **112 taught questions + 72 held-out questions**, **9 draws/question**
  (1 greedy + `N_SEEDED_SAMPLES = 8`), **4 tiers**, **3,312 draws** per `score_arm` call
- `phase23_prereg.choose_n_seeds(996.2667346671224)` → **N = 5**
- the arithmetic: **5 × 996.2667346671224 = 4,981.333673335612 s** vs
  `H_PER_POINT_FLOOR_SECONDS` = **17,175 s** → **FITS**, with 12,193.67 s of headroom
- **`n_is_the_d03_floor` is `false` and `overrun_seconds` is `0.0`** — N=5 was returned by the
  BOUND, not by D-03's floor of 3. There is no overrun to report.

Training does not bind, as the plan predicted: the control arm trains in **78.4–80.3 s** and the
never-taught arm in **34.4–36.4 s**, against a ~996 s scoring leg. N was decided by scoring alone.

### The replay match, as a NUMBER

`replay_ratio = replay_window_budget(8) / teaching_tokens = 8192 / 7581 = 1.0805962274106318`, and
`round(ratio × 7581) = 8192` exactly. Every control bin was built and then PROVED to carry
`replay_tokens == 8192`, the same public token volume the DP path draws at train time. The measured
`teaching_tokens = 7,581` reproduces `teach_persona.py`'s own D-24 comment exactly.

### CTRL-03's scheduling

`results/phase23_never_taught_training.json`: `arm` = `"never-taught"` READ from the FROZEN
`mitigation_gate.NEVER_TAUGHT_ARM`, **5 distinct seeds** against the frozen
`EXTRACTION_FLOOR_MIN_SEEDS = 2`, five exported 1,352,303-byte adapters each with its sha256 (all
five re-verified against `shasum -a 256`), `consumers: ["frontier lower-left floor", "relearning
reference"]` as a FIELD, and `scored_here: false`.

Per-seed training: 34.811400541104376 / 34.652486332692206 / 34.408928291872144 /
36.43067183345556 / 36.40582599956542 s — **176.7093129986897 s total over 5 × 200 = 1,000
optimizer steps**, 0 discarded.

## The ordering guards — MEASURED, and the plan brief's framing CORRECTED

The brief said two guards were "still vacuous by design and their endpoints land in YOUR plan
(23-08) and 23-10". Measured, before and after:

| guard | binds on `git ls-files <glob>` | tracked at `affd299` | tracked at HEAD | live? |
|-------|-------------------------------|----------------------|-----------------|-------|
| `test_the_prereg_rule_precedes_every_phase23_result` | `results/phase23_*` | 1 | **13** | already LIVE since 23-04 |
| `test_control_precedes_sigma_zero` | `results/phase23_sigma_zero.json` | 0 | **0** | **STILL VACUOUS** |
| `test_sigma_zero_precedes_every_noised_point` | `results/phase23_noised_*` | 0 | **0** | **STILL VACUOUS** |
| `test_every_noised_sweep_point_is_under_the_noised_glob` | tracked `.json` under `results/phase23_*` | 1 | **3** | live, scanning 3× more |

**ZERO ordering guards went live in this plan.** `_ordering_guard` computes
`tracked = git ls-files <artifact_glob>` and asserts NOTHING when `tracked` is empty — and guard 2's
glob is `SIGMA_ZERO_RECORD`, not `CONTROL_FLOOR_RECORD`. What 23-08 lands is guard 2's **pin side**,
which the guard reads only once something is tracked; the activation is 23-10's. Guard 1's
checked-pair count grew 1×1 → 1×13. This is the same class of over-claim 23-04 corrected ("three
guards went live" → one).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] The never-taught record's TOP LEVEL was missing eleven required schema keys**
- **Found during:** Task 2, at the very end of the scheduling run
- **Issue:** `phase23_cost.validate_record(..., kind="training")` REFUSED the record, naming all
  eleven missing keys (`capacity_n_facts`, `grad_accum_steps`, `replay_micro_batches_per_step`,
  `max_steps`, `batch_size`, `block_size`, `seconds_total`, `seconds_per_optimizer_step`,
  `warmup_iterations_discarded`, `timed_iterations`, `dp_seam_active`). Only the per-seed
  sub-records carried them.
- **Fix:** the shared shape keys were added at the top level — every one genuinely a property of
  all five arms, none a filler — plus the scheduling's own denominators (`seconds_total`,
  `timed_iterations = 5 × 200`, `seconds_per_optimizer_step`). `seed` at the top level carries the
  full seed LIST, documented in the record's own comment, because the schema's singular key has no
  other honest filling for a multi-seed scheduling; `seeds` remains the canonical one the frozen
  gate reads.
- **This is the guard working exactly as designed** — CAL-01's "REFUSED, never defaulted" caught a
  real omission on the real record rather than manufacturing the missing labels.
- **Commit:** `0fb596d`

**2. [Rule 1 — Bug] `_state_record` refused an identity key re-recorded at the SAME value**
- **Found during:** Task 3, after seed 2024's ~1,000 s scoring pass had already completed
- **Issue:** the guard's predicate was "is this key already present", and both the training leg and
  the scoring leg carry the arm's `arm` and `seed` identity fields. It threw away a completed
  scoring pass over two keys that were re-stating the same fact.
- **Fix:** the predicate is now "would this CHANGE a recorded value" —
  `changed = [k for k in entry & block if entry[k] != block[k]]`. A re-record at an identical value
  is a no-op; only a differing value is the overwrite the refusal exists to stop.
- **Cost:** one ~1,000 s scoring pass repeated. **The repeated pass produced the IDENTICAL reading**
  (530/1008 both times), which is a free confirmation that the scoring harness's per-question
  seeding contract is deterministic.
- **Commit:** `e762a4c`

**3. [Rule 3 — Blocking] Two census registers did not name the driver's new call sites**
- **Found during:** the post-Task-3 full-suite run (`tests/` exited 1 with 2 failures)
- **Issue:** (a) `test_every_inject_lora_consumer_reads_the_artifact_config` put
  `phase23_run.train_never_taught` in the `unclassified` bucket — its config expression is
  `tp.LORA_CFG`, a module ATTRIBUTE, and the classifier resolved only bare `ast.Name` references
  through the local module's bindings. (b) `test_resume_from_none_is_inert` counted 16 `train_arm(`
  grep hits against a 15-entry register.
- **Fix:** `_resolve` now follows a module attribute through the ALIASED module's own top-level
  bindings, so `tp.LORA_CFG` classifies by what the anchor actually IS. **The guard's teeth are
  unchanged in the direction that matters:** rebind `teach_persona.LORA_CFG` to
  `LoRAConfig(alpha=32.0)` and the site stops classifying as a producer — exactly the D-20 anchor
  movement the test exists to catch. `train_never_taught` was added to `INJECT_LORA_PRODUCERS`
  (it DEFINES the config its exported adapter carries) and `phase23_run.train_control` to
  `_TRAIN_ARM_CALL_SITES`, with the pre-existing-call-site literal bumped `8` → `8 + 1` and both
  numbers spelled so the ledger move is readable rather than only its total.
- **Neither register was weakened into a membership check.**
- **Commit:** `5c18d85`

### Deliberate departures from the plan text

**A. The plan's arm name `phase23_control_seed{seed}` WITH `prefix="phase23"` renders the phase
twice.** `arm_outputs(arm, prefix=)` already scopes csv/checkpoint/adapter as `{prefix}_{arm}`, so
the plan's literal would produce `results/phase23_phase23_control_seed1337/run.csv`. The arms are
named `control_seed{seed}` / `never_taught_seed{seed}` and the prefix supplies the `phase23_`,
rendering exactly the paths the plan intends —
`checkpoints/phase23_never_taught_seed1337_adapter.pt` is the name the plan itself writes out.

**B. `phase23_cost.time_iterations` is NOT used for the scoring leg.** It refuses fewer than 4
warm-up plus 20 timed iterations; a scoring leg is ~3,300 generation draws taking ~17 minutes, so
satisfying that denominator floor would cost most of a day and measure the same thing. The
DISCIPLINE the helper documents is applied verbatim in `synchronized_seconds` —
`torch.mps.synchronize()` immediately before `t0` and immediately before `t1` — and the denominators
that helper's minimums exist to guarantee (questions, draws/question, tiers, total draws) are
recorded beside every figure.

**C. The driver has THREE sub-modes rather than one invocation, and control seed 1337 is trained by
`cost` rather than by `schedule`.** This is forced by the plan's own ordering: N comes from a
measured scoring cost, so a scored control arm must exist before N does. `schedule` therefore
trains control seeds `[1:]` and ALL five never-taught arms, and REFUSES if seed 1337's adapter is
absent — nothing is silently skipped. **See the shortfall disclosure below for what this means for
"ONE invocation".**

**D. The seed ladder `(1337, 2024, 1338, 2025, 1339)` lives in the driver, which is NOT
ancestry-bound.** `(1337, 2024)` is the repository's established pair
(`results/phase19_noise_floors.json`, `tests/test_phase20_correction.py:115`); the three extensions
are adjacent and distinct. The ladder landed in the driver's FIRST commit (`5303819`), one commit
before any control arm was trained — but `git log -1` on a file four later plans re-edit proves
nothing, and the module docstring says so rather than implying otherwise. Only the REDUCTION and the
SEED COUNT are ancestry-bound, and both are imported from the edit-once module.

**E. A gitignored working file, `data/phase23_run_state.json`, carries state between sub-modes.**
Every number in it is carried into one of the two COMMITTED records; a third tracked artifact under
`results/phase23_*` would be a third thing the ordering guards watch for no gain.

## Honest shortfalls and contamination disclosures

**The FULL pre-registered N ran. Five seeds, five control arms, five never-taught arms, five scored
control readings. Nothing was reduced.** The following are disclosures, not shortfalls:

1. **"ONE invocation" is not literally true of the training.** All nine of the arms `schedule`
   trains (4 control + 5 never-taught) DID train in a single invocation. That invocation then died
   at the record write on deviation 1's schema refusal, so a SECOND invocation emitted the record —
   re-training nothing and re-measuring nothing, with each arm's adapter digest re-verified against
   the working state before reuse. Control seed 1337 was trained by `cost`, one invocation earlier,
   for the reason in deviation C. The command lines were, in order:
   `python scripts/phase23_run.py cost`, `... schedule` (×2, the second training nothing),
   `... floor` (×3 — see item 2).
2. **Seed 1339's `scoring_seconds` = 1026.8681782921776 s was measured under contention.** A stray
   background invocation of `floor` overlapped the recorded one; both scored seed 1339 and
   `_state_record` refused the second's differing `scoring_seconds`, which is the guard behaving
   correctly. The **RECALL COUNTS are unaffected and proven so**: seed 1339's taught-ON reading was
   521/1008 in all three passes over it (one interrupted, two complete). The contended timing is a
   disclosure figure only — it is not an input to any decision, since N was fixed from `cost`'s
   clean single-process 996.2667346671224 s.
3. **The first `floor` invocation was killed by the harness mid-way through seed 1339.** Seeds 1337,
   1338, 2024 and 2025 were already recorded; 1339 was re-scored from scratch in a later invocation.
   No partial reading entered the record — `_state_record` is called only after a full
   `score_arm` returns.

## Requirements — NEITHER ticked, deliberately

The plan's frontmatter declares `requirements: [DPSGD-06, CTRL-03]`. **Both stay unticked.**

- **DPSGD-06** reads *"the σ=0 point is the DP arm's first executed run"*. σ=0 has not run. 23-10 is
  the plan that can tick it, and `23-10-PLAN.md` claims it.
- **CTRL-03** reads *"a never-taught fresh adapter at identical budget and seed, **serving double
  duty as frontier floor and relearning reference**"*. The adapters exist, at identical imported
  budget constants, at five seeds — but **neither duty has been served**: nothing has been scored,
  and `23-14-PLAN.md` also claims CTRL-03 and produces the SCORED
  `results/phase23_never_taught.json` that `mitigation_gate.extraction_ceiling` consumes. Ticking it
  here would claim a double duty that has not happened once.

This continues waves 1–2's discipline: a requirement is ticked by the run that demonstrates it.

## The watched RED — the corpus-digest refusal, observed

`test_a_drifted_corpus_is_refused` drives `prove_bins_match` at ONE flipped hex character. The
literal message produced:

```
[phase23_run] CORPUS DRIFT — <tmp_path>/train.bin does not match its recorded digest.
  file     : <tmp_path>/train.bin
  expected : 1f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a
  actual   : 9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a
  The bins this run would train on are NOT the bins that digest was recorded over. Continuing
  would publish a σ=0 diagnostic — or an epsilon — describing a dataset nobody committed to.
  Rebuild the corpus from the recorded inputs, or re-record the digest in a reviewed commit that
  says what moved.
```

The file name, the expected digest and the actual digest are each asserted SEPARATELY. The second
detector — `ast.parse(inspect.getsource(rebuild_arm_bins_verifying_sha256))` — asserts
`prove_bins_match` is still among the called names, because watching a helper redden proves nothing
if production stopped calling it. A green one-sided control (correct digests admitted, returning 2)
and an empty-mapping refusal sit beside both.

## Verification

```
.venv/bin/python scripts/phase23_run.py --help                    -> prints 3 sub-modes, exit 0
.venv/bin/python -m pytest tests/test_phase23_ctrl.py -v          -> 7 passed
.venv/bin/python -m pytest tests/test_phase23_prereg.py -q        -> 32 passed
.venv/bin/python -m pytest tests/ -q     -> 1479 passed, 1 skipped (baseline 1472/1; +7 new)
make lint                                -> All checks passed! / 239 files already formatted
git diff --exit-code -- scripts/mitigation_accountant.py scripts/mitigation_gate.py \
                        scripts/phase23_prereg.py pyproject.toml   -> exit 0
git diff --stat affd299 HEAD -- scripts/phase23_prereg.py          -> EMPTY (byte-unchanged)
git ls-files results/phase23_sigma_zero.json                       -> (nothing)
git log --diff-filter=A --format='%H %ad' -- results/phase23_control_floor.json
  -> cb0e5bf40347d1ead9bc4401f209f8d821c29d55 Thu Aug 27 02:34:03 2026 -0300
```

The one skip is pre-existing (`tests/test_train_loop.py:81`, fp16 AMP needs CUDA).

## Acceptance criteria, measured

| criterion | result |
|-----------|--------|
| `grep -c "^assert \|    assert " scripts/phase23_run.py` | **0** |
| `grep -c "def choose_n_seeds" scripts/phase23_run.py` | **0** |
| `grep -n "from phase23_prereg import.*choose_n_seeds" ...` | matches |
| `grep -v '^\s*#' scripts/phase23_run.py \| grep -c "17175\|17_175"` | **0** |
| `inspect.signature(prove_bins_match).parameters` | `['expected_sha256']` |
| `grep -cE "^\s*(LR\|MAX_STEPS\|BATCH_SIZE\|WEIGHT_DECAY\|WARMUP_STEPS)\s*=" ...` | **0** |
| every `adapters[].sha256` vs `shasum -a 256` | 5/5 match |
| `grep -n "getsource\|ast.parse" tests/test_phase23_ctrl.py` | matches |

## Files

**Created**
- `scripts/phase23_run.py` (1,053 lines) — the run driver
- `tests/test_phase23_ctrl.py` (7 tests)
- `results/phase23_control_floor.json`
- `results/phase23_never_taught_training.json`
- 10 × `results/phase23_{control,never_taught}_seed*/run.csv` — the training curves

**Modified**
- `tests/test_lora_inject.py` — `_resolve` widened to a module attribute; one producer registered
- `tests/test_phase23_resume.py` — one call site registered; the literal bumped `8` → `8 + 1`

**Untouched (verified byte-identical to `affd299`)**
- `scripts/phase23_prereg.py`, `scripts/mitigation_gate.py`, `scripts/mitigation_accountant.py`,
  `pyproject.toml`

## What 23-09 and 23-10 need from here

- **23-09** pins `0.05357142857142849` into `scripts/mitigation_budget.py` as a literal with its
  `_PROVENANCE` sibling. The provenance keys `sigma_zero_verdict` demands are all present in
  `results/phase23_control_floor.json`: `record`, `record_sha256`
  (`c62d732283a3f15375de7b2ba9180c56acfcd75109b12912c17c9f083afdf0eb`), `git_sha`, `device` (`mps`),
  `torch_version` (`2.7.1`), `seeds`, `reduction`, `governs`.
- **23-10** calls `phase23_run.rebuild_arm_bins_verifying_sha256("dp_n8", ..., expected_sha256=...)`
  with 23-07's recorded triple. The central reading it must reproduce within the floor is
  **0.5615079365079365**, and the admissible band is **[0.5079365079365080, 0.6150793650793650]**.
- **23-13** prices `N_CONTROL_SEEDS = 5` into Z, at a measured **996.2667346671224 s** per control
  scoring pass.

## Self-Check: PASSED

- `scripts/phase23_run.py` — FOUND
- `tests/test_phase23_ctrl.py` — FOUND
- `results/phase23_control_floor.json` — FOUND
- `results/phase23_never_taught_training.json` — FOUND
- all 5 `checkpoints/phase23_never_taught_seed*_adapter.pt` — FOUND, digests match
- commits `5303819`, `0fb596d`, `cb0e5bf`, `e762a4c`, `5c18d85` — all FOUND in `git log`
