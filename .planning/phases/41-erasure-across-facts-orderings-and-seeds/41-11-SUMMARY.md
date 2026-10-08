---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 11
subsystem: erasure-rehearsal
tags: [phase41, e1, rehearsal, cpu, d-02, d-05, d-11, d-13, r-3b, erase-04, erase-06, erase-07, erase-09, erase-10]
requires: [41-10]
provides:
  - "data/phase41_rehearsal.json (gitignored rehearsal identity at 075f5ea, cpu_ordering_seconds 0.09196808400156442, 6 units)"
  - "the live E1 path (4 prep units, the real floors/band rules, 2 full-shape cells, emit, report) run end to end on CPU with the real checkpoints"
  - "the first measured CPU prices of the E1 units (prep ~10-29 min; K = 16 ~7-9 min; K = 48 ~32 min)"
  - "the R-3 b path (cell crash, reconcile, declined branch, drop_attempt, re-run, emit; second-prep-unit crash keeping the seed adapter) run once on CPU"
affects: [41-12, 41-13, 41-14]
tech-stack:
  added: []
  patterns: ["scratch-root rehearsal with MPS hidden before import, kwargs checked against inspect.signature (40-08)"]
key-files:
  created: []
  modified: [scripts/phase41_erasure.py, tests/test_phase41_erasure.py]
decisions:
  - "The rehearsal found one driver defect: cal_erase over the calibration corpus aborted in the pin's scorer. Fixed in 075f5ea with phase19_run.cal_score's seam, then a fresh re-rehearsal (_r2)"
  - "Not fixed, flagged for the orchestrator: build_record does not copy a re-run cell's dropped_attempts into the erasure record. They are reachable only through the sha-pinned cell record in inputs"
requirements-completed: []
metrics:
  duration: "~5h20m (first launch 18:14:22Z, prep leg end 23:31Z)"
  completed: 2026-10-08
---

# Phase 41 Plan 11: Full-shape CPU rehearsal of E1 Summary

`requirements-completed: []`: this is a rehearsal on CPU into a scratch root. No MPS record exists, so no ERASE requirement is met.

The real E1 driver ran end to end on CPU at commit 075f5ea:
- stage 1: all four prep units, with real training, real calibration orderings over 288 components, real cal-erased passes and real control gaps;
- the real floors and band rules, applied to the rehearsal's own records;
- stage 2: the cells `cell_pet_name_greedy_seed1337` and `cell_cat_name_gradient_seed2024`, at full shape;
- then emit and report.

The first launch found one driver defect. It was fixed with a test (075f5ea) and the rehearsal was re-run fresh (`_r2`). The R-3 b leg then ran its cell crash and its second-prep-unit crash on CPU. The prereg is unchanged (`11e432e4…a29a3`). The real tree holds only the gitignored identity.

**All readings below are rehearsal readings (CPU, MPS hidden). None of them is a finding about the MPS run.**

## Commits

| What | Commit |
|---|---|
| fix: cal_erase supplies the calibration fact's value to the pin's scorer (test first) | 075f5ea |
| this SUMMARY | (docs commit) |

## The driver defect the rehearsal surfaced (Rule 1)

The first launch (`<sfx>` = "", 18:14:22Z, HEAD 537234f) ran the smoke and trained seed 1337. It then died in `cal_erase`, after about 9 minutes of draws, with `REHEARSAL_EXIT=1`:

```
[phase18_extraction] PROOF FAILED: no value was supplied for fact 'cal_person_varek'. ...
```

- **Cause.** `phase19_erasure.run_erasure_arm` scores against `LOCKED_FACTS + SOFT_TIER_FACTS` (phase19_erasure.py:2814), and that list holds no calibration fact. This is Phase 19's documented pin defect 3 (scripts/phase19_run.py docstring, reason 3). Phase 19's `results/phase19_arm_cal-erased.json` was produced through `phase19_run.cal_score`, which extends `SOFT_TIER_FACTS` for that one call. 41-RESEARCH's recipe and every fake-based test called `run_erasure_arm` directly, so the defect stayed hidden. This is the unwired-driver pattern.
- **Fix (075f5ea).** `cal_erase` extends `phase14_factset.SOFT_TIER_FACTS` with `select_calibration_fact()` for the one call and restores it in a `finally`. The pin is unedited (ERASE-08).
  - Test first: `test_cal_erase_supplies_the_calibration_value_to_the_scorer`. RED gave `1 failed, 2 passed`. It asserts that the scorer sees `original + (fact,)` and that the tuple is restored after a raise too.
  - Driver tests: `134 passed`.
  - `ruff check` / `ruff format --check`: clean.
- **Census on the committed tree** (HEAD 075f5ea, clean except `.claude/scheduled_tasks.lock`):
  - Batch 1: `1368 passed in 284.29s`, B1_EXIT=0. That is 1367 + 1.
  - Batch 2: `226 passed, 3 skipped in 140.92s`, B2_EXIT=0.
  - `git status --porcelain` was the same before and after.
- **The first attempt's real-tree artifacts were moved, never deleted,** to `<scratchpad>/rehearsal41/moved/`. Their sha256 were listed first:

  | file | sha256 |
  |---|---|
  | data/persona_e1rh_calibration_seed1337_train_mask.bin | 4fecc28a… |
  | data/persona_e1rh_calibration_seed1337_train.bin | a3574e25… |
  | data/phase41_rehearsal.json (the identity recorded at 537234f) | bc383cc3… |
  | checkpoints/phase41rh_e1rh_calibration_seed1337_adapter.pt | f46cc78a… |
  | checkpoints/phase41rh_e1rh_calibration_seed1337_latest.pt | aa657568… |

## Task 1: the re-rehearsal (`<sfx>` = `_r2`)

Script: `<scratchpad>/rehearsal41.py`, run with `REHEARSAL_SFX=_r2`.
- It puts `scripts/` and `src/` at `sys.path[0:0]`.
- It hides MPS: `torch.backends.mps.is_available = lambda: False`. It replaces `personacore.preflight.preflight_device`, `teach_persona.preflight_device` and `phase14_recall.preflight_device` with a wrapper that calls the original with `strict=False`.
- It asserts `RuntimeConfig().device == "cpu"` before it imports phase41_erasure or phase41_prereg.
- `grep -cE 'phase41_erasure[.](preflight|run|emit|report)[(]'` printed `5`.
- A throwaway `preflight` into `<scratchpad>/pfcheck` printed `PREFLIGHT OK … stage=1 …` and wrote nothing.

Launched 2026-10-08T18:52:42Z with nohup. The wait was a run_in_background poller on `^REHEARSAL_EXIT=`. Key log lines:

```
VARIANT adaptive decided_by=cpu_rehearsal cpu_s=0.09 mps_s=0.09
STEP stage1 whole=[4 prep units] wall_s=4637.6
STEP floors {('gradient', 1337): (0.09107873950450847, 'reachability-min', 0.0), ('gradient', 2024): (same), ('greedy', 1337): (same), ('greedy', 2024): (same)}
STEP bands {(1337, 'gradient'): (0.6210482374087061, 1.4102358821393621), (1337, 'greedy'): (same), (2024, 'gradient'): (0.6184410198787433, 1.4050214470794367), (2024, 'greedy'): (same)} equal_to_dialogue_gap_band=True gap_noise_floor=0.08406970366097503
CELL cell_pet_name_greedy_seed1337 stop=48 confirmations=2
CELL cell_cat_name_gradient_seed2024 stop=48 confirmations=1
STEP stage2 whole=[2 cells] wall_s=9446.2
EMIT PARTIAL PASS=0 FAILURE replicada=0 não replicado=8
STEP emit status=PARTIAL wall_s=0.8
STEP report …/rehearsal41_r2/results/phase41_erasure_report.md wall_s=0.0
CPU_ORDERING_SECONDS 0.09196808400156442 fits=True bound=417.56158900260925
REHEARSAL_EXIT=0
```

- Verify: `tail -1 | grep -qx REHEARSAL_EXIT=0` passes, `grep -cE '^STEP (preflight|…|report)'` prints `7`, and `data/phase41_rehearsal.json` exists.
- No `D13 NOT_MEASURED` line appears.
- Each band equals `mitigation_gate.dialogue_gap_band(control_gap=<band record>, gap_noise_floor=<Phase 40's>)`, asserted in the script.

### Measured CPU cost per unit (from each record's provenance.run, plus heartbeat stage spans at 60 s resolution)

| unit | wall clock | ordering_seconds | k / stop | notes |
|---|---|---|---|---|
| prep_greedy_seed1337 | 1651.0 s | 820.7 | k 187 (stopped) | train ~180 s; cal_erase 9.2 min |
| prep_gradient_seed1337 | 617.3 s | 2.7 | k 82 (stopped) | 6 gradients; cal_erase 8.7 min |
| prep_greedy_seed2024 | 1741.8 s | 869.2 | k 250 (stopped) | train ~180 s; cal_erase 9.9 min |
| prep_gradient_seed2024 | 627.2 s | 2.8 | k 84 (stopped) | cal_erase 8.9 min |
| cell_pet_name_greedy_seed1337 | 6061.4 s | 728.6 | stop 48, 2 confirmations | K = 16 reads ~420-540 s; K = 48 1911.2 s and 1936.8 s; D-13 measured |
| cell_cat_name_gradient_seed2024 | 3384.5 s | 0.1 | stop 48, 1 confirmation | K = 48 1940.3 s |

Totals: stage 1 4637.6 s, stage 2 9446.2 s, emit 0.8 s. The erasure record's `e1_hours` (tmp ledger) is 3.9120098433333337 and its `prep_hours` is 1.288136595.

## Rehearsal identity

`data/phase41_rehearsal.json` (sha256 `4ea757711a1e5f9071f63fb72982be0aa614368e394c6a84f18d179377e9efdb`, unchanged by the R-3 b legs, checked before and after):

```json
{"cpu_ordering_seconds": 0.09196808400156442,
 "cpu_timings": [{"at": 0, "forward_backward_seconds": 0.022299165997537784, "forward_seconds": 0.004602791013894603, "ratio": 4.844705295161681},
                 {"at": 16, "forward_backward_seconds": 0.009245124994777143, "forward_seconds": 0.004441167009645142, "ratio": 2.0816882082342243},
                 {"at": 32, "forward_backward_seconds": 0.008973917007097043, "forward_seconds": 0.004341665990068577, "ratio": 2.066929383242422},
                 {"at": 48, "forward_backward_seconds": 0.008932459008065052, "forward_seconds": 0.004387250010040589, "ratio": 2.036004099976608},
                 {"at": 64, "forward_backward_seconds": 0.009001040991279297, "forward_seconds": 0.004642042011255398, "ratio": 1.939026180602154}],
 "git_sha": "075f5ea2125de1ab038135bc672b7dfd2e85e8b4",
 "module_sha256": {"scripts/phase41_erasure.py": "6f3f5c56693ced814c59404b0572398e5f082ecb18a91dbab79271590f68a907",
                   "scripts/phase41_prereg.py": "11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3"},
 "started_utc": "2026-10-08T18:52:43.681816+00:00",
 "units": ["prep_greedy_seed1337", "prep_gradient_seed1337", "prep_greedy_seed2024", "prep_gradient_seed2024",
           "cell_pet_name_greedy_seed1337", "cell_cat_name_gradient_seed2024"]}
```

- **D-05.**
  - `cpu_ordering_seconds` = 0.09196808400156442 s against `e1_ordering_seconds` 417.56158900260925. `ordering_cost_fits` gives True.
  - By the frozen rule, the CPU measurement alone would give **adaptive**. The variant for the real run still needs the MPS smoke (`alternative_variant(cpu, mps)`).
  - This rehearsal's own variant.json says `adaptive`, decided by `cpu_rehearsal`.
- **Backward/forward ratio** against `BACKWARD_FORWARD_CEILING` = 55.599999999999994:

  | source | ratio (forward+backward / forward) |
  |---|---|
  | smoke (identity) | 4.84 at the first gradient (warm-up), then 1.94-2.08 |
  | gradient calibration 1337 | max 2.288280108912506 |
  | gradient calibration 2024 | max 2.2587975713339974 |
  | gradient cell (cat_name, 2024) | max 2.372425533983312 |

## Task 2: verified from the files (`<scratchpad>/check41.py <T>`, read-only, `BAD 0`)

- **Ledger.** Each of the 4 prep units and 2 cells has exactly `[('start', None), ('end', unit_record(unit))]`, 12 lines in all.
- **Calibration records.** All 4 have:
  - family A2 and corpus `results/phase19_calibration_corpus.json`;
  - 23 draws and no `target` key;
  - `len(applied_ordering) == 288`;
  - `provenance.run.device` "cpu", and the cal-erased `config.device`/`config.preflight.device` cpu/cpu.

  The gradient records carry variant adaptive / cpu_rehearsal; the greedy ones carry None/None.
- **Training.**
  - 1337: final_train_loss 0.5555028319358826, ppl_adapter_on 5.915009937544312.
  - 2024: final_train_loss 0.6553063988685608, ppl_adapter_on 5.862478224893992.
  - Both have adapter_off 4.573348505014267 and scored_targets 270203.
- **Band records.** All 4 have `device` cpu, `rehearsal` True, provenance `['measurement']` only and no `run`. Every one reads `equal False`, as expected on CPU; the CPU value is recorded beside the MPS one, not absorbed:

  | seed | control_gap (CPU) | committed (MPS) |
  |---|---|---|
  | 1337 | 1.2420964748174121 | 1.2420966625043919 |
  | 2024 | 1.2368820397574867 | 1.2368822143360418 |

- **(2) D-02 on CPU with the real adapters.** Equality held at every gradient: `difference 0.0, equal True`.
  - The smoke: 5 of 5.
  - Each gradient calibration: 6 of 6, at [0, 16, 32, 48, 64, 128].
  - The gradient cell: 5 of 5.
  - Erasure record: `predictions.d02_cpu_equality.held = True`, over 12 calibration gradients, devices `["cpu"]`.
- **(4) D-11 identity of the seed-1337 rehearsal calibration adapter** (CPU-trained, so NOT identical to Phase 19's MPS adapter, as expected):
  - `reference_sha256_matches_record` True: reference `checkpoints/phase19_erase_calibration_adapter.pt` sha256 `bc616c36…56da` equals the `results/phase19_calibration_curve.json::adapter_in_sha256` digest.
  - `torch.equal`: tensors_identical False, n_equal 0/72, max abs diff 6.424263119697571e-06.
  - `predictions.d11_calibration_identity.held = False`. This is a rehearsal reading, not a finding about the MPS run.
  - The seed-2024 adapter against the same 1337 reference is also 0/72, with max diffs around 0.1, since it is a different seed.
- **(5) Variant.** variant.json: `variant adaptive, variant_decided_by cpu_rehearsal, cpu_seconds 0.09196808400156442, rehearsal True`. The erasure record has `variant` adaptive and `variant_decided_by` cpu_rehearsal.
- **Cell `cell_pet_name_greedy_seed1337`** (`stop` 48 == `e1_stop` 48, judged):

  | checkpoint | K = 16 target count | rank | K = 48 confirmation |
  |---|---|---|---|
  | 16 | 4/27 | 1 | — |
  | 32 | 0/27 | 1 | target not zero, 1911.16 s |
  | 48 | 0/27 | 1 | zero, 1936.76 s |

  - Every K = 16 `device` and every K = 48 `config.device`/`preflight.device` is cpu.
  - The first 78 addresses compared with `results/phase19_collateral_curve.json::ordered_prefix` (CPU against the MPS-made curve): **not equal**. They are the same set (78/78) and 76/78 match positionally; the first difference is at index 58. `predictions.greedy_1337_phase19_prefix.held = False`.
- **(1) D-13 was measured** on a real pet_name stop (k 48, M1 `data/phase41_e1/m1/cell_pet_name_greedy_seed1337_k048_adapter.pt`, sha256 `190aadf6…`):
  - `measured True`, `n_nlls 925`.
  - anchor_curve ranks: size 8 → 1, 32 → 3, 128 → 4, 512 → 5.
  - anchor_gate `{a2_record_rank 1, equal True, rank 1}`.
  - R_q n1: committed 13/27, minted 27/27. `criterion False`.
  - d21: greedy|1337 "not held", the other three cells "not measured", `prediction_held None`.
- **Cell `cell_cat_name_gradient_seed2024`** (`stop` 48 == `e1_stop` 48):
  - K = 16 counts: 11/27 at 16 (rank 1), 1/27 at 32 (rank 1), 0/27 at 48 (rank 1).
  - One K = 48 confirmation at 48: zero, 1940.25 s.
  - It used 5 gradients, all equal.
- **Prefix stability (RESEARCH A2).** At every checkpoint with both a K = 16 and a K = 48 record (32 and 48 for pet_name, 48 for cat_name), the K = 16 draws are identical to the first 16 completions of the K = 48 draws: 216/216 each.
- **Erasure record.** Status PARTIAL; 14 other cells NOT_RUN.
  - pet_name greedy 1337: **FAILURE (b), (c)**.
    - (a): upper 0.09107873950450847 = floor, holds (the WR-01 vacuity).
    - (b): 6 beyond the margin: person_name 26→0, cat_name 27→18, sibling_name 27→0, hometown 21→0, street 27→1, house_number 24→7. birth_year 18→12 is within the margin.
    - (c): gap 0.41597163374535917 is outside [0.6210482374087061, 1.4102358821393621].
  - cat_name gradient 2024: **FAILURE (b), (c)**.
    - (a): holds.
    - (b): all 7 non-targets beyond the margin.
    - (c): gap 0.4287972533545892 is outside [0.6184410198787433, 1.4050214470794367].
  - Pairs: all 8 `não replicado`. Summary: `{"PASS": 0, "FAILURE replicada": 0, "não replicado": 8, "n_pairs": 8, "inside_nao_replicado": {"FAILURE + NOT_RUN": 1, "NOT_RUN + FAILURE": 1, "NOT_RUN + NOT_RUN": 6}}`.
  - D-12: all 4 floors are `reachability-min` 0.09107873950450847, from 0/23 calibration successes.
  - D-06 Spearman: 1337 0.9907240514570247, 2024 0.9879133863014359.
  - End point basis: `exposure`.
  - `report == render_report(record)`: OK.

### Artifacts moved out of the real tree (`find data checkpoints -maxdepth 1 -name '*e1rh_*'`, sha256 listed first, moved to `<scratchpad>/rehearsal41_r2/moved/`)

| file | sha256 |
|---|---|
| data/persona_e1rh_calibration_seed1337_train_mask.bin | 4fecc28a8c64b119bdca216aef489b71a1c7f393d958b633d79ffc81b84051d8 |
| data/persona_e1rh_calibration_seed1337_train.bin | a3574e2537d45306ae3cb2cf4ba5acd8c5bc8149b08901b9aabc556148378d78 |
| data/persona_e1rh_calibration_seed2024_train_mask.bin | 4fecc28a8c64b119bdca216aef489b71a1c7f393d958b633d79ffc81b84051d8 |
| data/persona_e1rh_calibration_seed2024_train.bin | a3574e2537d45306ae3cb2cf4ba5acd8c5bc8149b08901b9aabc556148378d78 |
| checkpoints/phase41rh_e1rh_calibration_seed1337_adapter.pt | f46cc78addbc134f25363c7a7a87a7c17e6929360415b4fef3c47127260f26d4 |
| checkpoints/phase41rh_e1rh_calibration_seed1337_latest.pt | c3ddaa94031d3e5ce065070bc9273c604aefa4080070752b097752af619d6798 |
| checkpoints/phase41rh_e1rh_calibration_seed2024_adapter.pt | 3ee623afa0ef754a237075704dd22fe18d5c993bcbabcf8f7011ba1c630e2365 |
| checkpoints/phase41rh_e1rh_calibration_seed2024_latest.pt | 10aae1116856a0fbe6d70498709b503b94aaf276404dd5944eb743947c9b6842 |

- The re-hashes after the move are identical.
- The seed-1337 CPU adapter is byte-identical across the first, failed launch and `_r2` (f46cc78a…).
- The bins do not depend on the seed.

## Task 3: the R-3 b leg

The script is `<scratchpad>/rehearsal41_rerun.py` (`REHEARSAL_SFX=_r2`). It uses T2 = `rehearsal41_rerun_r2` with its own ledger, heartbeat and `identity.json`. T2 is seeded with `_r2`'s 8 prep ledger lines (start/end, each ending in "\n"), its 8 stage-1 records, its variant.json and the two copied inputs. K = 16 and K = 48 are CPU stand-ins built from `results/erasure_kstar_arm_k064.json` (16 completions; config.device cpu); the ordering, M1 and D-13 are real.

Cell leg log, `rehearsal41_rerun_r2.log`:

```
STEP crash planted crash (R-3 b leg)
LOST {… "run_id": "v6/41/E1/cell_pet_name_greedy_seed1337", "seconds": 720.111471, "utc": "2026-10-08T23:02:31.048793+00:00"}
STEP declined cell_pet_name_greedy_seed1337 outcome=dropped pending_has_it=False n_pending=15
STEP drop kept=2
STEP preflight_rerun pending=('cell_pet_name_greedy_seed1337',)
STEP rerun stop=16 ordering_equal=True kept_verified=True d13_measured=True
STEP emit status=PARTIAL verdict=FAILURE events=['start', 'lost', 'start', 'end'] cell_record_in_inputs=True dropped_attempts_in_erasure_cell_block=False
```

- **Cell manifest.**
  - approved: "approved (rehearsal stand-in, not Rafael's words)". This stand-in exists only under the scratch T2.
  - head_at_dropped_attempt = relaunch_git_sha = 075f5ea…, head_change_declared null.
  - kept:
    - `data/phase41_e1/orderings/cell_pet_name_greedy_seed1337.json` (93e0defb…bca63)
    - `results/phase41_k16_pet_name_greedy_seed1337_k016.json` (a9e075c7…0fa)

    Both are under `data/phase41_dropped/v6_41_E1_cell_pet_name_greedy_seed1337_2026-10-08T230231.048793+0000/`.
- **The re-run's `dropped_attempts`.** It lists that manifest (manifest_sha256 39ee5346…20db4) with `ordering_equal True`: the same CPU greedy ordering both times. `kept_verified True` was computed by the script, because the driver proves each kept sha256 rather than writing a field. `relaunch_declarations []`.
- **D-13 in the re-run** (stand-in K = 48 record): measured True, anchor_gate rank 1 equal True, R_q committed n1 24, minted 27, criterion False.
- **Script defect, not a driver defect.** The same script's prep leg then died with `RERUN_EXIT=1`. My script called `unit_outcomes` before `reconcile`, and the frozen prereg correctly refused ("an attempt is still open: phase36_ledger.py reconcile first"). I moved that root's (`rehearsal41_prep_r2`) real-tree artifacts to its `moved/`: bins 4fecc28a…/a3574e25…, adapter f46cc78a…, latest c3ddaa94…. I then ran the prep leg alone, with the reconcile first, from `<scratchpad>/rehearsal41_rerun_prep.py` into the fresh root `rehearsal41_prep_r2b`.

Prep leg log, `rehearsal41_rerun_prep_r2.log` (`RERUN_EXIT=0`):

```
PREP_CRASH planted crash (R-3 b prep leg)
LOST_PREP {… "run_id": "v6/41/E1/prep_gradient_seed1337", "seconds": 60.0097, "utc": "2026-10-08T23:29:35.093516+00:00"}
STEP drop_prep kept=1
ADAPTER_KEPT_IN_PLACE checkpoints/phase41rh_e1rh_calibration_seed1337_adapter.pt exists=True sha256_before=f46cc78addbc134f25363c7a7a87a7c17e6929360415b4fef3c47127260f26d4 sha256_after=f46cc78addbc134f25363c7a7a87a7c17e6929360415b4fef3c47127260f26d4 in_manifest_kept=False
STEP rerun_prep trained=0 adapter_sha256=f46cc78addbc134f25363c7a7a87a7c17e6929360415b4fef3c47127260f26d4 adapter_identity='not produced by the dropped attempt'
IDENTITY_SHA256_AFTER 4ea757711a1e5f9071f63fb72982be0aa614368e394c6a84f18d179377e9efdb
```

- **What was real.** The first unit's training was real; so were the control gaps and D-11. The calibration orderings and cal_erase were stand-ins built from `_r2`'s records (the live ones ran in Task 1).
- **Prep manifest.** kept = `results/phase41_band_inputs_gradient_seed1337.json` only (e3c68989…74373). The adapter is not in it.
- **The re-run.** It trained nothing (the training wrapper counted 0 calls) and digest-checked the adapter that the first unit's record cites.
- **The 8 STEP lines** are split across the two logs: 6 + 2 (`grep -cE` printed 6 and 2).
- **Afterwards.** The prep leg's training artifacts were moved to `rehearsal41_prep_r2b/moved/`: bins 4fecc28a… / a3574e25…, adapter f46cc78a…, latest c3ddaa94….

### Real-tree checks after every leg

- `find data checkpoints -maxdepth 1 -name '*e1rh_*' | wc -l` gave 0.
- `find results -maxdepth 1 -name 'phase41*' | wc -l` gave 0.
- `git status --porcelain -- scripts src results tests ledger artifacts | wc -l` gave 0.
- `git diff --quiet -- ledger/v6_mps_ledger.jsonl` passed (LEDGER_UNCHANGED).
- `grep -c 'v6/41' data/v6_mps_heartbeat.jsonl` gave 0.
- `find results data checkpoints -maxdepth 1 -name '*phase41*'` lists only `data/phase41_rehearsal.json`, which is gitignored.
- `shasum -a 256 scripts/phase41_prereg.py` gave `11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3`. The prereg and its test were not edited.

## Notes for the orchestrator

1. **(6) The identity does not carry the CPU D-02 result.** `data/phase41_rehearsal.json` holds only `cpu_ordering_seconds` and `cpu_timings` (seconds and ratios). The D-02 values live in the scratch roots: `rehearsal41_r2/data/phase41_e1/variant.json` (5 smoke gradients), the four `_r2` calibration records (12 gradients) and the `_r2` erasure record (`d02_cpu_equality.held = True`). So the identity cannot fill the MPS record's `d02_cpu_equality`, which will read None. Filling it would need a driver change, for example writing the smoke's d02 list into the identity, and then a fresh rehearsal for the new identity shape.
2. **The erasure record does not surface a re-run cell's dropped attempts.** `build_record` copies none of `dropped_attempts` into `cells[unit]`, and `render_report` says nothing about them. They are reachable only through the cell record, which `inputs` pins by sha256. The plan's wording ("emit listing the dropped attempt") assumed otherwise. I did not change it: it is a design call, and any later driver commit is disclosed by `rehearsal_disclosure` at the MPS launch. The real-root preflight only requires the prereg digest to be unchanged.
3. **The rehearsal identity is now at 075f5ea.** The MPS preflight checks only `module_sha256[PREREG_FILE]` against the launch; a driver commit after 075f5ea is listed by `rehearsal_disclosure`.

## Deviations from Plan

1. **[Rule 1 - Bug] The cal_erase scorer value** (075f5ea, above). Re-rehearsal `_r2` from step 1. The first attempt's root `rehearsal41/` and log `rehearsal41.log` (ending in `REHEARSAL_EXIT=1`) are kept, not reused.
2. **[Rule 2] phase14_recall's module-level `preflight_device` binding is also wrapped,** in addition to the plan's teach_persona wrapper. The process stayed CPU-only either way; every device field reads cpu.
3. **Task 3 ran as two scripts and two logs** because of my script's ordering bug (described above). The cell leg came from `rehearsal41_rerun.py` (6 STEP lines; its log ends `RERUN_EXIT=1` from the prep part). The prep leg came from `rehearsal41_rerun_prep.py` (2 STEP lines, `RERUN_EXIT=0`). The failed prep root `rehearsal41_prep_r2` is kept with its `moved/`.
4. **`kept_verified`** is a Phase 40 field name. The Phase 41 driver proves kept sha256 values (it refuses otherwise) and writes no such field, so the script recomputed it from the files.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register:

| Threat | How it was handled |
|---|---|
| T-41-42 | every device field checked cpu from the files |
| T-41-43 | phase41rh / e1rh names, tmp ledgers, everything moved, real ledger diff-checked |
| T-41-44 | the real driver ran on real checkpoints; it caught a defect that the fakes hid |
| T-41-45 | the stand-in approval exists only under the scratch T2 and T3, and is labelled |

## Not verified

- Nothing ran on MPS. The MPS ordering cost, the MPS D-02 equality and the MPS variant are unmeasured; they are 41-12's launch-gate smoke.
- 14 of the 16 cells, and the gradient path on a pet_name cell, never ran live. D-13 was measured only on the greedy/1337 stop.
- The Obsidian vault note: this executor has no Obsidian MCP tool, so the note is pending for the orchestrator.

## Self-Check: PASSED

- FOUND: data/phase41_rehearsal.json (sha256 4ea75771…)
- FOUND: 075f5ea (`git log --oneline`)
- FOUND: scratch logs rehearsal41_r2.log (REHEARSAL_EXIT=0), rehearsal41_rerun_r2.log, rehearsal41_rerun_prep_r2.log (RERUN_EXIT=0)
