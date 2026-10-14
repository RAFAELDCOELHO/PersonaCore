---
phase: 42-dp-sgd-recipe-search-at-large
plan: 07
subsystem: e3-rehearsal
tags: [phase42, e3, rehearsal, cpu, d-21, d-05, d-08, d-19, d-20, recipe-01, recipe-03, recipe-04]
requires: [42-06]
provides:
  - "data/phase42_rehearsal.json (gitignored rehearsal identity at e0f884e, the 42-06 frozen digests, units [control_lr1e-03_t200, point_lr3e-04_t800_sigma1p000000], cpu_seconds 4706.789165666036)"
  - "D-21's four legs run once on CPU through the real driver: the v4.0 SHA-256 reuse and its tamper refusal, the T-derived warmup at 20 and 80, the P22 refusal at T = 800, the REFUSED path through emit and report"
  - "the first measured CPU price of an E3 unit (replaces 42-RESEARCH A3): DP training 3.34 s/step at T = 200 (sigma 0), 2.93 s/step at T = 800 (sigma 1.0)"
affects: [42-08, 42-09, 42-10]
tech-stack:
  added: []
  patterns: ["scratch-root rehearsal with MPS hidden before import, kwargs checked against inspect.signature (41-11)", "a no-training SMOKE mode of the same script run before the long launch"]
key-files:
  created: []
  modified: []
decisions:
  - "The rehearsal identity is passed only to the two real run steps, so its units are the units that trained and scored for real; the nine stood-in units are never recorded as rehearsed (T-42-28)"
  - "No driver defect surfaced; no fix commit, no re-rehearsal"
requirements-completed: []
metrics:
  duration: "~2 h (launch 2026-10-14T16:29:37Z, REHEARSAL_EXIT=0 after total_wall_s 4712.2; Task 2 done 17:50Z)"
  completed: 2026-10-14
---

# Phase 42 Plan 07: D-21 CPU rehearsal of E3 Summary

The E3 driver ran once, end to end, on CPU into a scratch root at HEAD e0f884e. The prereg and driver were at the digests frozen by 42-06's review. What ran:
- two real trainings and scorings: `control_lr1e-03_t200` and `point_lr3e-04_t800_sigma1p000000`, the second with real DP noise and real clip;
- nine units through the real `run` loop, with only `train_stage`, `score_arm` and `measure_condition_c` stood in;
- the real Phase 35 threshold rule on the rehearsal's own control records;
- the planted v4.0 tamper and the planted P22 crossing, both refused;
- emit and report.

The rehearsal exited `REHEARSAL_EXIT=0`. No driver defect surfaced, so this plan has no fix commit and no re-rehearsal.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

**Every reading below is a rehearsal reading (CPU, MPS hidden). None of them is a finding about the MPS run.**

## Commits

| What | Commit |
|---|---|
| this SUMMARY | (docs commit) |

No driver or test change was needed.

## The script and the launch

- **Script.** `<scratchpad>/rehearsal42.py`, where `<scratchpad>` = `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/832678fb-db05-4fae-b072-a03196279c5b/scratchpad`.
  - It puts `scripts/` and `src/` at `sys.path[0:0]`.
  - It hides MPS: `torch.backends.mps.is_available = lambda: False`. It replaces `personacore.preflight.preflight_device`, `teach_persona.preflight_device` and `phase14_recall.preflight_device` with a wrapper that calls the original with `strict=False`.
  - It asserts `RuntimeConfig().device == "cpu"` and `phase42_recipes._device() == "cpu"`. Only then does it import `phase42_recipes`, `phase42_prereg` or `phase35_prereg` past the trainer modules.
  - `grep -cE 'phase42_recipes[.](preflight|run|emit|report)[(]'` gives `9`.
  - Every kwarg is checked against `inspect.signature`.
- **Import-only probe** (`--probe`, exit 0, after `py_compile` passed):
  - `_device()=cpu`, `RuntimeConfig=cpu`, `mps_hidden=True`.
  - Signatures: `preflight` accepts device, heartbeat_path, ledger_path, root. `run` accepts those plus rehearsal_identity and units. `emit` accepts ledger_path, root, thresholds. `report` accepts root.
  - `P22_ONSETS={200: 0.07890181429684162, 800: 0.15780356992036104}`, `NOISED=(0.5, 1.0)`, `tp=(0.0003, 20, 200)`.
- **No-training smoke.** `REHEARSAL_SMOKE=1` ran in about 5 s, into `<scratchpad>/rehearsal42_smoke`, with `SMOKE_EXIT=0` and all 11 STEP lines. Afterwards the real tree was clean, no identity was written and the bins were unchanged.
- **Launch.** 2026-10-14T16:29:37Z, with nohup and detached: `sh` pid 91266, python pid 91268. The wait was a background poller on `^REHEARSAL_EXIT=`. The log is `<scratchpad>/rehearsal42.log` and T is `<scratchpad>/rehearsal42`.

## Task 1: the eleven steps (`<scratchpad>/rehearsal42.log`)

Verify: `tail -1 | grep -qx REHEARSAL_EXIT=0`, the 11 STEP lines, and `test -f data/phase42_rehearsal.json` all pass (`TASK1_VERIFY_OK`).

| step | wall_s | what the log shows |
|---|---|---|
| preflight1 | 0.1 | stage 1; pending = the 3 CONTROL_UNITS; pf keys `device, gate, git_sha, heartbeat_path, ledger_path, module_sha256, p22, pending, real, rehearsal, root, stage`; `rehearsal=None` |
| v4_tamper_refused | 0.0 | T2 = `<scratchpad>/rehearsal42_tamper`: budget copy, 3 planted contract-shape controls (labelled stand-ins), v4.0 control with its final `\n` replaced by a space (still valid JSON, sha256 different). Refusal: `[phase35_prereg] the reused v4.0 control record is not byte-identical to its copy at tag v5.0 (D-17: verified by SHA-256)` |
| control_real | 1484.3 | REAL; warmup 20; clip_bind_count 0; teach_persona schedule restored `(0.0003, 20, 200)` |
| controls_standin | 0.9 | `control_lr3e-04_t800` and `control_lr1e-03_t800` both read warmup 80 (train_config built from the rebound globals; the take proof ran for each) |
| threshold | 0.0 | the real fill on T, see below |
| p22_refused | 0.1 | `[phase42_recipes] P22 onset at T=800 is 1.0, not the frozen 0.15780356992036104: refused before any training (RECIPE-04)`; train_stage calls 0 |
| preflight2 | 0.3 | stage 2; `p22={200: 0.07890181429684162, 800: 0.15780356992036104}` == P22_ONSETS; pending = all 8 POINT_UNITS (the REFUSED recipe's two included, D-20) |
| point_real | 3222.9 | REAL DP at T = 800; warmup 80; schedule restored |
| points_standin | 3.5 | 7 points; warmups 20 at T = 200, 80 at T = 800; schedule restored |
| emit | 0.1 | `0 de 8 pontos passam; 2 REFUSED` |
| report | 0.0 | line 1 is the WR-03 refused lead (below) |

Total `total_wall_s=4712.2`.

The threshold step's output:

```
THRESHOLD (0.0003, 200, 8, 1337) -> {'control': 'results/phase25_point_dp_n8_sigma0p000000.json', 'taught': 0.5486111111111112, 'heldout': 0.3737654320987654}
THRESHOLD (0.0003, 800, 8, 1337) -> {'control': 'results/phase42_control_lr3e-04_t800.json', 'taught': 0.66875, 'heldout': 0.5141975308641975}
THRESHOLD (0.001, 200, 8, 1337) -> {'control': 'results/phase42_control_lr1e-03_t200.json', 'taught': 0.66875, 'heldout': 0.5141975308641975}
THRESHOLD (0.001, 800, 8, 1337) -> REFUSED
```

What each threshold rests on:
- **The v4.0 key.** It consumed T's byte-identical copy of the v4.0 control and gives the plan's 0.5486111111111112 / 0.3737654320987654.
- **The `lr1e-03_t200` threshold.** It is the real control's measurement: 0.7 × 963/1008 and 0.7 × 476/648.
- **The `lr3e-04_t800` threshold.** It comes from a stand-in control that copies those counts.
- **The `(0.001, 800, 8, 1337)` key.** Its stand-in control read 0/1008 and 0/648, so the key is REFUSED.

## Task 2: verified from the files (one `.venv/bin/python -c` per check)

- **Ledger** (`T/ledger.jsonl`). It has 22 lines: 11 `start` and 11 `end`. Every unit has exactly `[('start', None), ('end', unit_record(unit))]`, so the bad list is `[]`.
- **Device and disclosure.**
  - All 11 records read `provenance.run.device` = `cpu`.
  - `git_sha_at_launch` is e0f884e on all 11, and `head_moved_during_run` is False.
  - 9 of 11 records carry the `rehearsal_stand_in` label in `training`; the 2 real ones carry none.
  - All 11 carry `rehearsal_disclosure = {"this_is_the_rehearsal": true}` (deviation 3).
- **The two REAL records:**

  | | control_lr1e-03_t200 | point_lr3e-04_t800_sigma1p000000 |
  |---|---|---|
  | train_config == expected_train_config(recipe) | True (lr 0.001, warmup 20, max_steps 200) | True (lr 0.0003, warmup 80, max_steps 800) |
  | live composed_steps == T | 200 == 200 | 800 == 800 |
  | clip_norm | 1000000.0 | 1.3254119157791138 |
  | clip_bind_count | 0 | 6400 (= 800 × 8; descriptive; v4.0 noised points read 1600 = 200 × 8 at T = 200) |
  | ε | None (control) | 519.6981942303134, isclose `point_epsilon(1.0, 800)` True |
  | taught / held-out (adapter ON) | 963/1008, 476/648 | 0/1008, 0/648 |
  | taught / held-out (adapter OFF) | 0, 0 | 0, 0 |
  | dialogue gap (ppl on − off) | 0.044852582763661886 (4.618201087777929 − 4.573348505014267) | 0.1291103945916774 (4.702458899605944 − 4.573348505014267) |
  | retention_ppl (1000285 tokens) | 3.9937791125291784 | 4.322295845100319 |
  | final_train_loss | 0.010844775009900331 | 1.4396580383181572 |

- **The E3 record** (`T/results/phase42_recipes.json`):
  - summary: `0 de 8 pontos passam; 2 REFUSED`.
  - lead: `nenhuma receita manteve o recall onde a garantia é vazia (0 de 6 pontos julgados; 2 pontos REFUSED, sem limiar porque o controle da receita não aprendeu)`.
  - REFUSED pair: `point_lr1e-03_t800_sigma0p500000` and `point_lr1e-03_t800_sigma1p000000`.
  - composition: total ε 6078.265039595788, total δ 8e-05, n_points 8.
  - `selection_accounted` False.
  - d17: `previsão D-17 confirmada nos 6 pontos julgados; 2 pontos REFUSED fora da leitura`, held True.
  - `hours` 1.3083520297222222, from the tmp ledger.
  - `rehearsal_disclosure` `{"this_is_the_rehearsal": true}`.
  - 12 inputs.
- **Report.** The report equals `phase42_recipes.render_report(record)` byte for byte (True).
- **D-10.** The MPS noise identity was measured in research (42-RESEARCH Item 1) and is not re-checked here.

### Measured CPU cost per real unit (replaces 42-RESEARCH A3)

Assumption A3 was 1–4 s/step, taken from a non-DP reading. Both measured rates fall inside it. Each record's `training.seconds`, `scoring_seconds` and `condition_c.seconds`:

| unit | train | per step | score_arm | condition c | unit wall (STEP) |
|---|---|---|---|---|---|
| control_lr1e-03_t200 (σ 0, 200 steps) | 667.1 s | 3.34 s | 607.7 s | 209.3 s | 1484.3 s |
| point_lr3e-04_t800_sigma1p000000 (σ 1.0, 800 steps) | 2341.0 s | 2.93 s | 686.3 s | 195.2 s | 3222.9 s |

Caveat: pytest jobs from a peer session in another repository (`/Users/juliorcoelho/nordeste-energy-ml`) were running on the box at launch, so these CPU seconds may be inflated.

## Rehearsal identity

`data/phase42_rehearsal.json` (sha256 `75e4193ca223c38c1c7faaf62c79b96ca97b64b70328f6eaeead358738c72768`):

```json
{"cpu_seconds": 4706.789165666036,
 "git_sha": "e0f884ee62384b31183d3fa6b90fdc9fae94acaf",
 "module_sha256": {"scripts/phase42_prereg.py": "0ca749f0ee1c2f5194cd0f227124b60b714f94bb07d95dcbd1c693f4161a5ff5",
                   "scripts/phase42_recipes.py": "0c9be5828aa1174d774ccc4781525427883a2c461f2560a3d30dbcd8cbee7c60"},
 "started_utc": "2026-10-14T16:54:23.433016+00:00",
 "units": ["control_lr1e-03_t200", "point_lr3e-04_t800_sigma1p000000"]}
```

- **Digests.** They equal 42-06's "Frozen digests" (check printed `True`), and `shasum` of the two files in the tree gives the same values. The driver has not changed since the review.
- **`started_utc`.** It is the moment `record_rehearsal` first wrote the identity, at the end of `control_real`, not the launch time.
- **`cpu_seconds`.** It is the sum of the two real `run` calls.

## Artifacts moved out of the real tree

The sha256 values were listed first. The files were then moved, never deleted, into `<scratchpad>/rehearsal42/moved/` at the same relative paths. Re-hashing after the move gave identical values.

| file | sha256 |
|---|---|
| checkpoints/phase42rh_control_lr1e-03_t200_dp_n8_adapter.pt | c84c487ebef99a6762ed9007044b035a32538df65fde842e19e515f2fa3de93e |
| checkpoints/phase42rh_control_lr1e-03_t200_dp_n8_latest.pt | 81cd7c14a33c11ce93a0af67ee7417ab53d24867fc40b0130e0c59d01127434d |
| checkpoints/phase42rh_point_lr3e-04_t800_sigma1p000000_dp_n8_adapter.pt | 0060e2f0bbe8a19c09d6bf5eead00f71bbcabcecf4cfa783791f639c0b9854ac |
| checkpoints/phase42rh_point_lr3e-04_t800_sigma1p000000_dp_n8_latest.pt | a18f9f85ce200ba9fd505bdde3b13792bfb5489a047ac615f8df2220879d3510 |
| data/phase25_phase42rh_control_lr1e-03_t200_training.json | be16692235386d992526e4121e2e6a28f6f552f3f5ff7fd85fdae3d29dae6516 |
| data/phase25_phase42rh_point_lr3e-04_t800_sigma1p000000_training.json | f018374a8e8f4c3db54fbdd166dc6aa357576dc8cb478b30927b57abaf156b71 |
| data/phase25_runs/phase42rh_control_lr1e-03_t200/run.csv | 7e3602d2949a844f2ce46e56374eb14a81a1d5788fba8522eec1e094def042d6 |
| data/phase25_runs/phase42rh_point_lr3e-04_t800_sigma1p000000/run.csv | 6f9106107b79975f6948adbba1f35ff2b709ad6694f6b015e45107f9463d3676 |

### Real-tree checks afterwards

- The Task 2 verify passes (`TASK2_VERIFY_OK`): no `*phase42rh_*` under checkpoints/, data/ or results/ (maxdepth 2), no `results/phase42*`, `git status --porcelain -- scripts src results tests ledger artifacts` empty, `git diff --quiet -- ledger/v6_mps_ledger.jsonl` passes, and the identity is present.
- `find checkpoints data results -name '*phase42rh*'` with no depth limit gives 0.
- `find results data checkpoints -maxdepth 1 -name '*phase42*'` lists only `data/phase42_rehearsal.json`.
- `grep -c 'v6/42' data/v6_mps_heartbeat.jsonl` gives 0.
- **Arm bins.** All three are byte-unchanged before and after. Every fresh `train_stage` rebuilds them, deterministically:
  - `data/persona_dp_n8_train.bin` e14517954f56fa2d3ff55b63096a86dec08535e62ea7d3f77903afb4a3e80735
  - `data/persona_dp_n8_train_mask.bin` 732223f3844299f3c4eadff7b05f9a2ba077c48e6792880d89fc6929abd74045
  - `data/persona_dp_n8_train_fact.bin` 34d04ac76adf0ed802d3305eb77cb47270311f8f93aee89581f89e33c3f6f2c2

## Deviations from Plan

1. **The script has a `REHEARSAL_SMOKE=1` mode, which ran before the launch.** Only in that mode, the two "real" steps are stood in from the v4.0 sidecars (`data/phase25_dp_n8_sigma{0p000000,1p000000}_training.json`) and the v4.0 control record, and the identity goes to `T/smoke_identity.json`, never to `data/`.
   - The first smoke attempt failed with a FileNotFoundError: in smoke mode no real sidecar exists. That was a bug in my script, not the driver. Its roots are kept as `rehearsal42_smoke_a1` and `rehearsal42_smoke_a1_tamper`.
   - The real launch sets no SMOKE, so its two real steps train and score for real.
2. **The identity records only the two real units.** `rehearsal_identity` is passed only to `control_real` and `point_real`, so `units` lists the two units that ran for real and `cpu_seconds` covers only them (T-42-28).
3. **Scratch-root records carry `{"this_is_the_rehearsal": true}`, not the triple.** `write_unit` passes `None` off the real root (`scripts/phase42_recipes.py:408`), and `_rehearsal_disclosure(None)` returns that dict (:439-443). So Task 2's "carries rehearsal_disclosure" holds in this form, not as `{units_read, rehearsal_git_sha, rehearsal_module_sha256}`. The code was not changed.
4. **The P22 refusal fires on the frozen-mismatch proof** (`scripts/phase42_recipes.py:541-545`), before the crossing proof. The message names P22 and the train_stage counter is 0.
5. **The REFUSED key** resolves through `phase42_prereg.recipe_key` to `(0.001, 800, 8, 1337)`, which is the plan's shape.
6. **Three arm bins, not two.** A DP arm writes three bins (`teach_persona.arm_bin_targets`), and `train_stage` unlinks and rebuilds all three. All three hashes are recorded and are unchanged.
7. **No `phase42_threshold_prereg` on the scratch root.** The rehearsal never needed it: `_threshold_fill` runs only on the real root (preflight's `if current == 2 and real`, and `_thresholds`). The plan's threshold step called `phase35_prereg.fill` directly with `_REPO_ROOT` = T, restored afterwards.
8. **CPU contention.** Pytest jobs from a peer session in `/Users/juliorcoelho/nordeste-energy-ml` were running at launch. The CPU timings above may therefore be inflated; correctness is unaffected.

Also: T2 is named `rehearsal42_tamper`, since the plan does not name it.

## Known Stubs

None in the repository. The nine stand-in units exist only under the scratch T and are labelled `rehearsal stand-in (plan 42-07), not a measurement`.

## Threat Flags

None beyond the plan's register:

| Threat | How it was handled |
|---|---|
| T-42-26 | MPS hidden before import; `_device()` asserted cpu; all 11 device fields cpu from the files |
| T-42-27 | phase42rh prefix; tmp ledger and heartbeat; every artifact moved; real ledger diff-checked; real heartbeat has no v6/42 line |
| T-42-28 | stand-ins only under scratch T, labelled; the identity lists only the two real units |
| T-42-29 | two real trainings and scorings through the real driver; the real threshold rule on producer records; emit and report |

## Not verified

- Nothing ran on MPS.
- The real point's 0/1008 and 0/648 is a CPU rehearsal reading of one cell. It is not an E3 finding.
- The Obsidian vault note: this executor has no Obsidian MCP tool, so the note is pending for the orchestrator.

## Self-Check: PASSED

- FOUND: data/phase42_rehearsal.json (sha256 75e4193c…)
- FOUND: `<scratchpad>/rehearsal42.log` ending `REHEARSAL_EXIT=0`
- FOUND: the 8 moved files under `<scratchpad>/rehearsal42/moved/` with matching sha256
