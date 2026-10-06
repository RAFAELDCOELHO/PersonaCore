---
phase: 40-m2-seed-noise-floor
plan: 08
subsystem: e2-noise-floor-rehearsal
tags: [rehearsal, cpu, noise-floor, r-3b, consumer]
requires: [40-07]
provides:
  - "data/phase40_rehearsal.json (gitignored rehearsal identity, seeds [1337, 2024], prereg a81c79dc)"
  - "first measured CPU price of one E2 seed (~1.15-1.17 h)"
  - "the live E2 path (train_arm, run_erasure_arm, D-13, emit, report, Phase 41 consumer) run end to end on real checkpoints"
  - "the R-3 b path (crash, reconcile, declined branch, drop_attempt, re-run preflight, re-run, record) run once on real training"
affects: [40-09, 40-10, 41]
tech-stack:
  added: []
  patterns: ["scratch-root rehearsal with MPS hidden before import, kwargs checked against inspect.signature"]
key-files:
  created: []
  modified: []
decisions:
  - "No driver defect surfaced: no fix commit, no re-rehearsal (<sfx> stays empty)"
requirements-completed: []
metrics:
  duration: "~2h45m (launch 13:30:24Z, leg end 16:06:41Z)"
  completed: 2026-10-06
---

# Phase 40 Plan 08: Full-shape CPU rehearsal of E2 Summary

The real E2 driver ran end to end on CPU at commit dfa1162. It covered seeds 1337 and 2024, both groups, both full A2 passes per seed and D-13, into a scratch root with its own ledger. The record came out MEASURED, the Phase 41 consumer accepted it with bands equal, and the report matched `render_report` byte for byte. The R-3 b crash/drop/re-run leg also finished with exit 0. No driver defect was found and the prereg is unchanged (a81c79dc).

All readings below are **rehearsal readings** (CPU, MPS hidden). None of them is a finding about the MPS run.

## Pre-run state (Task 1 step 1)

- HEAD `dfa116251f4c4366eee8f910df91e91537cede3b`.
- `shasum -a 256 scripts/phase40_prereg.py scripts/phase40_noise.py`:
  - `a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2  scripts/phase40_prereg.py`. This equals 40-04-SUMMARY "Frozen prereg", which is `a81c79dc…05a2` at 8cf3b32.
  - `34cc936a26cd9271f23b42c920ed889533fb693c2cd38b614bee60135fbef4ed  scripts/phase40_noise.py`
- `git status --porcelain -- scripts src results tests ledger artifacts | wc -l` printed `0`.
- `data/phase40_rehearsal.json` was absent (`ls: … No such file or directory`).
- `find data checkpoints -maxdepth 1 -name '*e2rh_*'` printed nothing. `grep -c 'v6/40/' data/v6_mps_heartbeat.jsonl` printed `0`.
- Before launch I made one throwaway `preflight` call into `<scratchpad>/pfcheck`, which stayed empty: `PREFLIGHT OK dfa1162… device=cpu pending=1337,2024 d13=True projection_h=7.9518624092864085 stop_h=11.83638889157415 spent_E2_s=0.0`. Preflight writes nothing.

## Task 1: the rehearsal (`<scratchpad>/rehearsal40.py`, `<sfx>` = "")

What the script does:
- Puts `scripts/` and `src/` at `sys.path[0:0]`.
- Hides the device: `torch.backends.mps.is_available = lambda: False`. It then wraps `personacore.preflight.preflight_device` and `teach_persona.preflight_device` to strict=False.
- Asserts `RuntimeConfig().device == "cpu"` before it imports `phase40_noise` and `phase40_prereg`.
- Uses `seeds = phase40_prereg.SEEDS[:phase35_prereg.ENTRIES["e2_min_seeds"]["value"]]`, which is `(1337, 2024)`.
- Checks every call's kwargs against `inspect.signature` and writes each call literally. `grep -cE 'phase40_noise[.](preflight|run|emit|report)[(]'` prints `4`.

Launch: `nohup sh -c 'cd <repo> && .venv/bin/python <scratchpad>/rehearsal40.py > <scratchpad>/rehearsal40.log 2>&1; echo REHEARSAL_EXIT=$? >> …' &` at 2026-10-06T13:30:24Z. The wait was a run_in_background poller, `until grep -q '^REHEARSAL_EXIT=' …; do sleep 120; done`. It completed with exit 0.

Log, key lines:

```
DEVICE cpu (mps hidden; torch 2.7.1)
PREFLIGHT OK dfa116251f4c4366eee8f910df91e91537cede3b device=cpu pending=1337,2024 d13=True projection_h=7.9518624092864085 stop_h=11.83638889157415 spent_E2_s=0.0
STEP preflight pending=(1337, 2024) wall_s=0.1
REHEARSAL RECORDED dfa116251f4c4366eee8f910df91e91537cede3b
[phase19_erasure] wrote …/rehearsal40/results/phase40_a2_full_seed1337.json in 30.3 min
[phase19_erasure] wrote …/rehearsal40/results/phase40_a2_m2_seed1337.json in 31.0 min
SEED 1337 WHOLE 1.1471
[phase19_erasure] wrote …/rehearsal40/results/phase40_a2_full_seed2024.json in 30.6 min
[phase19_erasure] wrote …/rehearsal40/results/phase40_a2_m2_seed2024.json in 31.9 min
SEED 2024 WHOLE 1.1721
RUN DONE whole=[1337, 2024]
STEP run whole=[1337, 2024] wall_s=8349.4
EMIT MEASURED whole=1337,2024 recall_floor=0.33333333333333337 gap_noise_floor=0.0052116420611856284
STEP emit status=MEASURED wall_s=0.5
STEP report …/rehearsal40/results/phase40_noise_floor_report.md wall_s=0.0
BANDS {(1337, 'greedy'): (0.25, 0.5104232841223713), (2024, 'greedy'): (0.125, 0.26042328412237126)}
STEP consumer bands_equal=True gap_noise_floor=0.0052116420611856284
REHEARSAL_EXIT=0
```

- Verify: `tail -1 … | grep -qx REHEARSAL_EXIT=0` passes. `grep -c '^STEP '` prints `5`: preflight, run, emit, report and consumer, the five names in the plan's acceptance list. The orchestrator prompt said "six STEP lines" for Task 1, but six is Task 3's count. No D-13 failure line (`D13 NOT_MEASURED`) appears.
- The consumer ran `phase35_prereg.fill("e1_condition_c_band_inputs", …)` with `_REPO_ROOT` set to T, kind "derived". Its inputs were the rehearsal record and two planted band-input records: `{1337, "greedy", control_gap 0.5}` and `{2024, "greedy", control_gap 0.25}`. Each band equals `mitigation_gate.dialogue_gap_band(control_gap=…, gap_noise_floor=0.0052116420611856284)`.

### Measured CPU cost (first measured CPU price for E2)

| Seed | started_utc | finished_utc | wall clock |
|---|---|---|---|
| 1337 | 13:30:25.617 | 14:39:15.175 | **4129.6 s (1.1471 h)** |
| 2024 | 14:39:15.241 | 15:49:34.797 | **4219.6 s (1.1721 h)** |
| run() total (2 seeds) | | | 8349.4 s |
| emit / report | | | 0.5 s / 0.0 s |

Per stage. The A2 durations are the `phase19_erasure` "wrote … in N min" lines. The training spans come from the `teach_persona` bins-provenance utc stamps and the A2 write times. The heartbeat has 60 s resolution.

| Stage | seed 1337 | seed 2024 |
|---|---|---|
| train full (bins 13:30:25 / 14:39:15 -> M2 bins 13:34:11 / 14:43:02) | ~226 s | ~227 s |
| train M2 (-> A2 full start, i.e. A2 write minus its logged duration) | ~220 s | ~234 s |
| A2 full (216 questions, K = 48) | 30.3 min | 30.6 min |
| A2 M2 | 31.0 min | 31.9 min |
| D-13 + seed record (A2 M2 mtime 14:39:09 / 15:49:28 -> seed record 14:39:15 / 15:49:34) | ~6 s | ~6 s |

Heartbeat first-beat-per-stage spans:

| Span | seed 1337 | seed 2024 |
|---|---|---|
| start -> train_full | 60.0 s | 60.0 s |
| train_full -> train_m2 | 180.0 s | 180.0 s |
| train_m2 -> a2_full | 240.0 s | 240.0 s |
| a2_full -> a2_m2 | 1800.2 s | 1860.2 s |

No beat carries stage `d13`. The two A2 passes are about 88% of a seed's CPU cost.

## Task 2: verified from the files, artifacts moved

`<scratchpad>/check40.py <T>` is read-only and printed every check below. Every line was `OK`:

```
OK   ledger seed1337 [('start', None), ('end', 'results/phase40_seed1337.json')]
OK   ledger seed2024 [('start', None), ('end', 'results/phase40_seed2024.json')]
OK   ledger lines 4
OK   seed1337 provenance.run.device cpu
OK   seed1337 provenance.run keys == RUN_PROVENANCE_KEYS ['device', 'finished_utc', 'git_sha_at_end', 'git_sha_at_launch', 'head_moved_during_run', 'started_utc', 'torch_version']
OK   seed2024 provenance.run.device cpu
OK   seed2024 provenance.run keys == RUN_PROVENANCE_KEYS (same 7)
OK   a2 full seed1337 config.device/preflight.device/arm ('cpu', 'cpu', 'retrain')
OK   a2 m2 seed1337 config.device/preflight.device/arm ('cpu', 'cpu', 'retrain')
OK   a2 full seed2024 config.device/preflight.device/arm ('cpu', 'cpu', 'retrain')
OK   a2 m2 seed2024 config.device/preflight.device/arm ('cpu', 'cpu', 'retrain')
OK   status MEASURED
OK   gap_noise_floor finite >= 0 0.0052116420611856284
OK   record device cpu
OK   recall_floor.full one pair n_seeds=2 n_pairs=1 floor=0.18518518518518523
OK   recall_floor.m2 one pair n_seeds=2 n_pairs=1 floor=0.33333333333333337
OK   beside {'margin_amended': False, 'margin_at_gate': 0.2962962962962963, 'sampling_floor': 0.14814814814814814}
OK   recall_floor.full / .m2 / .published, gap_noise_floor_detail: n_seeds 2 n_pairs 1 (each)
OK   per_seed {1337,2024} x {full,m2} n_questions 27 for all 8 slots
OK   dialogue_gap {1337,2024} x {full,m2} device cpu, rehearsal True
OK   a2_label present ('retrain'), every A2 config.arm retrain
OK   crn_addendum.v3_sampling_floor 0.14814814814814814 == 0.14814814814814814 (results/phase19_noise_floors.json nontarget_noise_floor.value); published_below=False
OK   rehearsal_disclosure {'1337': {'this_is_the_rehearsal': True}, '2024': {'this_is_the_rehearsal': True}}
OK   d07/d08/d08b/d12 present
OK   no top-level provenance.run ['emit', 'seeds']
OK   seed1337 d13 measured, n_nlls == D13_NLLS_PER_ADAPTER n_nlls=925 gate={'a2_record_rank': 2, 'equal': True, 'rank': 2} a2_m2_exposure_rank=2
OK   seed2024 d13 measured, n_nlls == D13_NLLS_PER_ADAPTER n_nlls=925 gate={'a2_record_rank': 1, 'equal': True, 'rank': 1} a2_m2_exposure_rank=1
OK   report == render_report(record)
```

### Rehearsal identity

`data/phase40_rehearsal.json` (sha256 `93dc5195338e2d3705e6120df6e47eaa696463051c60961362b42cd6bb925192`):

```json
{"git_sha": "dfa116251f4c4366eee8f910df91e91537cede3b", "module_sha256": {"scripts/phase40_noise.py": "34cc936a26cd9271f23b42c920ed889533fb693c2cd38b614bee60135fbef4ed", "scripts/phase40_prereg.py": "a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2"}, "seeds": [1337, 2024], "started_utc": "2026-10-06T13:30:25.616247+00:00"}
```

The seeds are [1337, 2024]. The prereg digest equals 40-04's "Frozen prereg".

### Readings (rehearsal readings, CPU)

**Per-seed wall clocks:** 4129.6 s (1337) and 4219.6 s (2024), from the table above.

**A2 counts per slot (n_answerable/27):**

| seed / group | birth_year | cat_name | hometown | house_number | person_name | pet_name | sibling_name | street |
|---|---|---|---|---|---|---|---|---|
| 1337 full | 17 | 27 | 16 | 21 | 23 | 26 | 27 | 27 |
| 1337 m2 | 15 | 27 | 18 | 14 | 26 | 0 | 27 | 27 |
| 2024 full | 17 | 27 | 21 | 23 | 27 | 25 | 27 | 27 |
| 2024 m2 | 21 | 27 | 17 | 23 | 27 | 0 | 27 | 27 |

**Floors:**
- recall_floor.full 0.18518518518518523
- recall_floor.m2 0.33333333333333337
- published `{"group": "m2", "n_pairs": 1, "n_seeds": 2, "tie": false, "value": 0.33333333333333337}`, beside sampling_floor 0.14814814814814814 (published_below_v3_sampling_floor False)

**Dialogue gaps.** The CPU adapter-off is 4.573348505014267 in every reading. The committed MPS value is 4.573349214207799, so `adapter_off_matches_committed` is False in every reading, including each `pre` block. It is recorded, not absorbed.

| seed / group | gap | adapter_on | pre_post_equal |
|---|---|---|---|
| 1337 full | 1.2421028605374245 | 5.8154513655516915 | True |
| 1337 m2 | 1.4345828934865432 | 6.00793139850081 | True |
| 2024 full | 1.2368912184762388 | 5.810239723490506 | True |
| 2024 m2 | 1.3588701478702676 | 5.932218652884535 | True |

- **gap_noise_floor (rehearsal value):** 0.0052116420611856284, beside 0.005214448168350039. The M2 gap, descriptive only, is 0.07571274561627561.
- **Training readings** (final_train_loss / ppl_adapter_on): 1337 full 0.6204447150230408 / 5.8154513655516915; 1337 m2 0.3702593743801117 / 6.00793139850081; 2024 full 0.426157146692276 / 5.810239723490506; 2024 m2 0.48003971576690674 / 5.932218652884535. scored_targets is 270203 for all four.

**D-07 identity:** CPU-trained adapters against the committed MPS adapters. As expected (RESEARCH Pitfall 4), they are NOT identical on CPU:
- `full_seed1337` tensors_identical False, n_equal 0/72, keys_equal True, metadata_equal True, max abs diff 3.2648444175720215e-05
- `full_seed2024` False, 0/72, max abs diff 2.713315188884735e-05
- `m2_seed1337` False, 0/72, max abs diff 2.6326626539230347e-05
- d07.m2_seed1337: label "ruído de re-execução com a mesma semente (same-seed re-run noise)"; draw_identity bit_identical False (9584/10368 completions and 216/216 entries differ); count deltas birth_year −3, house_number −3, all others 0.

**D-08:** persona_adapter.pt against dialogue-floor seed 1337 is tensors_identical True (72/72). Both are committed adapters, so this reading does not depend on the device.

**D-08b:** outcome `NOT_SEPARABLE`, max_abs_rate_difference 0.18518518518518517, draw_identity bit_identical False (9390/10368 completions differ).

**D-13:** reading `{"measured_seeds": [1337, 2024], "not_measured": []}`.

| seed | anchor curve ranks (size 8 / 32 / 128 / 512) | anchor gate rank | A2 rank | equal | R_q committed n1 | R_q minted n1 |
|---|---|---|---|---|---|---|
| 1337 | 1 / 4 / 10 / 32 | 2 | 2 | True | 0/27 | 11/27 |
| 2024 | 2 / 5 / 12 / 41 | 1 | 1 | True | 0/27 | 10/27 |

**Predictions observed:**
- full_counts False
- m2_counts False
- status MEASURED
- tensor_identity: all False
- gap_pair abs 0.0052116420611856284, devices [cpu, cpu], rehearsal [true, true]

**Report headings** (`T/results/phase40_noise_floor_report.md`):

```
# Phase 40 — E2 training-seed noise floor
## Status
## Approval and cost (D-11, D-13, D-14)
## Seeds (D-15)
## A2 recall per seed with its denominator (NOISE-01)
## Training-seed floor beside v3.0's sampling floor (NOISE-02, D-01..D-05)
## Every pair (D-02, D-04)
## Per-slot spread (D-04)
## gap_noise_floor (D-09, D-10)
## Full x M2 re-reading (D-12, descriptive)
## Determinism check (D-07, descriptive)
## persona_adapter.pt correction and the Phase 18 residual (D-08, D-08b)
## Target rank across the M2 seeds (D-13, descriptive)
## Predictions recorded before the run
## Provenance
```

### Moved artifacts (main rehearsal -> `<scratchpad>/rehearsal40/moved`, 16 files, never deleted)

sha256 values were recorded before the move. The sha256 set after the move is identical (`SHA_SAME`).

```
6d3410e8fd3bc6267f5ff3089665224278d3b3c295095bad3f681545a95cc83b  checkpoints/phase40rh_e2rh_full_seed1337_adapter.pt
8331f7927ce454c9c04b5d84f5dabede141c2c2e8a4d6e915c1fab6b20ae21f7  checkpoints/phase40rh_e2rh_full_seed1337_latest.pt
f1a2ef3ae8893dd759e8d931ad827a0d1a7fad9e6d1ddaf98abdb06e1bb4d369  checkpoints/phase40rh_e2rh_full_seed2024_adapter.pt
2b9216d8adbde56fade710a96095bb679f30a22a36d95948ad26088a1a5307b9  checkpoints/phase40rh_e2rh_full_seed2024_latest.pt
5ab30bdc9b80b040e74b85238e25a66929685ef701a3a5b03bfec2622025542f  checkpoints/phase40rh_e2rh_m2_seed1337_adapter.pt
b8e48fe55e8da6d2370327612f81da208e9ec926c701c1583abbc110bbe0879a  checkpoints/phase40rh_e2rh_m2_seed1337_latest.pt
cb408d7bf38f21c233afee336cffe004e3fb278a60bd3a0677c056f50927ef39  checkpoints/phase40rh_e2rh_m2_seed2024_adapter.pt
f34e3f933f0715fdab43b19a9d75b97d524e89d945d7d9b3c5116146c08a905f  checkpoints/phase40rh_e2rh_m2_seed2024_latest.pt
42287ddc6306c91d541f1473d2e36fdcf8da352fa6b9c883e39d9d3a04a017c1  data/persona_e2rh_full_seed1337_train_mask.bin
69eaf121aa207a40449cb1b01c05eb6add0bf9c1a0eadf18ea6bf77debc4cabe  data/persona_e2rh_full_seed1337_train.bin
42287ddc6306c91d541f1473d2e36fdcf8da352fa6b9c883e39d9d3a04a017c1  data/persona_e2rh_full_seed2024_train_mask.bin
69eaf121aa207a40449cb1b01c05eb6add0bf9c1a0eadf18ea6bf77debc4cabe  data/persona_e2rh_full_seed2024_train.bin
114f79a8ae0ab10c83b710d254236b5c10c25d6a1cf8110ec7d17ee29de1bcbc  data/persona_e2rh_m2_seed1337_train_mask.bin
d3f761a9a2e63d66ae92165f570f57004da667c7ae3cc7f630353e84b959c43b  data/persona_e2rh_m2_seed1337_train.bin
114f79a8ae0ab10c83b710d254236b5c10c25d6a1cf8110ec7d17ee29de1bcbc  data/persona_e2rh_m2_seed2024_train_mask.bin
d3f761a9a2e63d66ae92165f570f57004da667c7ae3cc7f630353e84b959c43b  data/persona_e2rh_m2_seed2024_train.bin
```

The driver had already moved the four csv files to `T/data/phase40_e2/<arm>/run.csv` in-process. No `results/phase40rh_*` file remained.

Task 2 verify printed `TASK2_VERIFY_OK`:
- no `*e2rh_*` under `data/` or `checkpoints/`
- no `results/phase40*`
- porcelain count 0
- `git diff --quiet -- ledger/v6_mps_ledger.jsonl` clean
- the identity is present
- `grep -c 'v6/40/' data/v6_mps_heartbeat.jsonl` prints `0`

## Task 3: the R-3 b leg (`<scratchpad>/rehearsal40_rerun.py`, T2 = `<scratchpad>/rehearsal40_rerun`)

**Estimated CPU cost, derived before launch** from `rehearsal40/heartbeat.jsonl` for seed 2024, first beat to first beat: train_full -> train_m2 is 179.993535 s and train_m2 -> a2_full is 240.02141 s. The estimate is 2 x 420.014945 = **840.03 s**. This compares with 313.90 s for the same four trainings at MPS unit prices.

**Measured:** `LEG wall_s=886.2`. That splits into crash attempt 441.6 s, re-run 444.0 s and about 0.6 s for the rest. The leg ran 2026-10-06T15:51:54Z -> 16:06:41Z.

Log, key lines (`RERUN_EXIT=0`; verify prints `STEP6_OK`):

```
DEVICE cpu (mps hidden; torch 2.7.1)
PREFLIGHT OK dfa1162… device=cpu pending=2024 d13=True … spent_E2_s=0.0
REHEARSAL RECORDED dfa116251f4c4366eee8f910df91e91537cede3b      (T2/identity.json, seeds [2024])
STEP crash 'planted crash (R-3 b leg)' both adapters trained wall_s=441.6
LOST {"event": "lost", "flag": "sem registro de resultado", … "run_id": "v6/40/E2/seed2024", "seconds": 420.074477, "utc": "2026-10-06T15:59:16.323239+00:00"}
STEP declined [phase40_noise] nothing to run: every seed of [2024] is whole or dropped ({2024: 'dropped'})
DROPPED 2024 data/phase40_dropped/v6_40_E2_seed2024_2026-10-06T155916.323239+0000 kept=10
STEP drop kept=10
PREFLIGHT OK dfa1162… device=cpu pending=2024 d13=True … spent_E2_s=420.074477
STEP preflight_rerun pending=(2024,) dropped_attempts=1
REHEARSAL KEPT dfa116251f4c4366eee8f910df91e91537cede3b
D13 NOT_MEASURED 2024 exception: SystemExit: [phase40_prereg] planted D-13 refusal (R-3 b leg)
SEED 2024 WHOLE 0.1233
RUN DONE whole=[2024]
STEP rerun d13=exception wall_s=444.0
EMIT INSUFFICIENT_SEEDS whole=2024 recall_floor='-' gap_noise_floor='-'
D13_READING {"criterion": false, "measured_seeds": [], "not_measured": [{"failure_kind": "exception", "reason": "SystemExit: [phase40_prereg] planted D-13 refusal (R-3 b leg)", "seed": 2024}]}
IDENTITY full tensors_identical=True n_equal=72/72 metadata_equal=True
IDENTITY m2 tensors_identical=True n_equal=72/72 metadata_equal=True
STEP emit status=INSUFFICIENT_SEEDS ledger=['start', 'lost', 'start', 'end']
LEG wall_s=886.2
RERUN_EXIT=0
```

The script asserted each of these in-process:
- (a) run() raised exactly the planted RuntimeError, and both adapters existed by then.
- (b) reconcile appended exactly one lost line, and `seed_outcomes(...)[2024] == "dropped"`.
- (c) the manifest's kept list holds both groups' adapters.
- (d) `rerun_seeds(...) == frozenset({2024})`, and preflight's `dropped_attempts[2024]` lists the manifest.
- (e) the seed record's d13 equals `prereg.d13_not_measured("exception", "SystemExit: [phase40_prereg] planted D-13 refusal (R-3 b leg)")`, and `provenance.run.device == "cpu"`.
- (f) the record has status INSUFFICIENT_SEEDS, a `stop` key, and neither `gap_noise_floor` nor `recall_floor`.

The fake A2 records are copies of `results/phase19_arm_retrain.json` with `config.device` and `config.preflight.device` set to "cpu".

**Manifest** (`T2/data/phase40_dropped/v6_40_E2_seed2024_2026-10-06T155916.323239+0000/manifest.json`, sha256 `5865a8b4c1b97f428cfba064df873454b132e3bba49e7d3b894aae932e0b4588`):

```
approved: "approved (rehearsal stand-in, not Rafael's words)"   (scratch T2 only; never a real manifest)
cause_note: "planted crash in the R-3 b rehearsal leg"
head_at_dropped_attempt = relaunch_git_sha = dfa116251f4c4366eee8f910df91e91537cede3b; head_change_declared: null
lost_utc 2026-10-06T15:59:16.323239+00:00; run_id v6/40/E2/seed2024; seed 2024
kept (10):
  checkpoints/phase40rh_e2rh_full_seed2024_adapter.pt   f1a2ef3ae8893dd759e8d931ad827a0d1a7fad9e6d1ddaf98abdb06e1bb4d369
  checkpoints/phase40rh_e2rh_full_seed2024_latest.pt    2b9216d8adbde56fade710a96095bb679f30a22a36d95948ad26088a1a5307b9
  checkpoints/phase40rh_e2rh_m2_seed2024_adapter.pt     cb408d7bf38f21c233afee336cffe004e3fb278a60bd3a0677c056f50927ef39
  checkpoints/phase40rh_e2rh_m2_seed2024_latest.pt      f34e3f933f0715fdab43b19a9d75b97d524e89d945d7d9b3c5116146c08a905f
  data/persona_e2rh_full_seed2024_train.bin             69eaf121aa207a40449cb1b01c05eb6add0bf9c1a0eadf18ea6bf77debc4cabe
  data/persona_e2rh_full_seed2024_train_mask.bin        42287ddc6306c91d541f1473d2e36fdcf8da352fa6b9c883e39d9d3a04a017c1
  data/persona_e2rh_m2_seed2024_train.bin               d3f761a9a2e63d66ae92165f570f57004da667c7ae3cc7f630353e84b959c43b
  data/persona_e2rh_m2_seed2024_train_mask.bin          114f79a8ae0ab10c83b710d254236b5c10c25d6a1cf8110ec7d17ee29de1bcbc
  data/phase40_e2/e2rh_full_seed2024/run.csv            c9e3319f5e68486066ad1274c9bb3da23793e4760f3eac98e7e875a4d49df1db
  data/phase40_e2/e2rh_m2_seed2024/run.csv              d3c756674e07bb42408b84b8c3d0ae42059d5b8a97d5882e5b0eec30925e491b
```

**Emitted record's seeds block:**
- outcomes: 2024 `whole`; 1337, 1338, 1339 and 2025 `not_run`.
- whole [2024]; dropped []; not_run [1337, 1338, 2025, 1339]; dropped_seed_outputs {}.
- `dropped_attempts["2024"]` holds one attempt with:
  - kept_verified True
  - manifest sha256 `5865a8b4…4588`
  - relaunch_declarations []
  - adapter_identity: full tensors_identical True (72/72, metadata_equal True, max abs diff 0.0) and m2 tensors_identical True (72/72, metadata_equal True, max abs diff 0.0)
- stop: "INSUFFICIENT_SEEDS: fewer than e2_min_seeds whole seeds; no floor is published and the phase stops for Rafael (ruling e)".

**Tmp ledger:** start 15:51:54.857, lost 15:59:16.323 (420.074477 s), start 15:59:16.930, end 16:06:40.692 naming `results/phase40_seed2024.json`.

**Rehearsal reading (CPU): training is bit-reproducible across processes.** The re-run's two adapters are tensor-identical to the crashed attempt's, and the crashed attempt's seed-2024 adapter sha256 values (`f1a2ef3a…`, `cb408d7b…`) equal the main rehearsal's seed-2024 adapters at the same file names. This says nothing about MPS.

**Moved leg artifacts** (`T2/moved`, 8 files, sha256 recorded before the move, `SHA_SAME` after):

```
f1a2ef3ae8893dd759e8d931ad827a0d1a7fad9e6d1ddaf98abdb06e1bb4d369  checkpoints/phase40rh_e2rh_full_seed2024_adapter.pt
2b9216d8adbde56fade710a96095bb679f30a22a36d95948ad26088a1a5307b9  checkpoints/phase40rh_e2rh_full_seed2024_latest.pt
cb408d7bf38f21c233afee336cffe004e3fb278a60bd3a0677c056f50927ef39  checkpoints/phase40rh_e2rh_m2_seed2024_adapter.pt
f34e3f933f0715fdab43b19a9d75b97d524e89d945d7d9b3c5116146c08a905f  checkpoints/phase40rh_e2rh_m2_seed2024_latest.pt
42287ddc6306c91d541f1473d2e36fdcf8da352fa6b9c883e39d9d3a04a017c1  data/persona_e2rh_full_seed2024_train_mask.bin
69eaf121aa207a40449cb1b01c05eb6add0bf9c1a0eadf18ea6bf77debc4cabe  data/persona_e2rh_full_seed2024_train.bin
114f79a8ae0ab10c83b710d254236b5c10c25d6a1cf8110ec7d17ee29de1bcbc  data/persona_e2rh_m2_seed2024_train_mask.bin
d3f761a9a2e63d66ae92165f570f57004da667c7ae3cc7f630353e84b959c43b  data/persona_e2rh_m2_seed2024_train.bin
```

The crashed attempt's outputs left the real tree through `drop_attempt` into `T2/data/phase40_dropped/…`.

Task 3 verify printed `TASK3_VERIFY_OK`:
- `RERUN_EXIT=0` with the 6 STEP lines
- no `*e2rh_*` under `data/` or `checkpoints/`
- porcelain count 0
- real ledger clean

`find results -maxdepth 1 -name 'phase40*'` is empty. `data/phase40_rehearsal.json` sha256 was `93dc5195…5192` both before and after the leg. The real heartbeat `v6/40/` count is `0`.

## Final state

- `shasum -a 256 scripts/phase40_prereg.py` gives `a81c79dcfd4188a767ca45ef6e14d4bfc48dbbebd419fb67bc737fd6bd3505a2` (unchanged).
- HEAD is still dfa1162 before the SUMMARY commit. `git status --porcelain` shows only the pre-existing ` D .claude/scheduled_tasks.lock`, which this plan did not touch.
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched, and no gsd-sdk mutation handler was called.

## Deviations from Plan

None that change an outcome. There was no driver defect, no fix commit and no re-rehearsal. Process notes:
1. Before launch I made one throwaway `preflight` call into `<scratchpad>/pfcheck`. Preflight writes nothing, and the directory stayed empty. I did it so that a wiring slip in the script could not burn the `<sfx>` = "" root.
2. Task 2 step 1's checks ran as one read-only script (`<scratchpad>/check40.py`) that prints one OK/FAIL line per check, not as one `python -c` per check.
3. Task 1 has 5 STEP lines, the plan's acceptance list. The orchestrator prompt's "six STEP lines" matches Task 3.

## Known Stubs

None. No repo code changed.

## Threat Flags

None. T-40-29: every device field reads cpu (seed provenance, A2 config.device and config.preflight.device). T-40-30: the rehearsal used its own names and tmp ledger, artifacts were moved out, and the real ledger and heartbeat are untouched. T-40-31: the real driver ran on real checkpoints and the real consumer read its record.

## Second brain

No Obsidian MCP tool was available to this executor, so the vault entry is **pending**. The orchestrator should record it.

## Self-Check: PASSED

- FOUND: data/phase40_rehearsal.json (sha256 93dc5195…5192)
- FOUND: `<scratchpad>/rehearsal40.log` (REHEARSAL_EXIT=0), `<scratchpad>/rehearsal40_rerun.log` (RERUN_EXIT=0)
- FOUND: T/results/phase40_noise_floor.json, T/results/phase40_noise_floor_report.md, T2/results/phase40_noise_floor.json
- Commits: none expected before this SUMMARY (no driver fix)
