---
phase: 41-erasure-across-facts-orderings-and-seeds
verified: 2026-10-13T00:00:00Z
status: passed
score: 5/5 roadmap success criteria verified; 8/8 requirements (ERASE-03..ERASE-10) satisfied
overrides_applied: 0
---

# Phase 41: Erasure Across Facts, Orderings and Seeds — Verification Report

**Phase Goal:** Erasure is re-measured on the four facts tied at 13/13 across two orderings and two
teaching seeds, with each floor derived before measurement and no cell read PASS without
replication at the second seed.
**Verified:** 2026-10-13 at HEAD a219ddc (working tree clean except `.claude/scheduled_tasks.lock`)
**Status:** passed
**Re-verification:** No, this is the first verification.

The outcome is FAILURE in all 16 cells (8/8 pairs "FAILURE replicada", PASS 0). The rules allowed
that result in advance, so it counts as a finding and does not make this verification fail. The
phase goal is that E1 is run and published under the frozen rules. Each check below was re-run by
the verifier from the committed records and code. None of the evidence is copied from
41-16-SUMMARY.md. Where possible the verdicts were recomputed from raw inputs instead of read
from the summary fields that the driver writes.

## Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence (re-run by verifier) |
|---|-------|--------|-------------------------------|
| 1 | Four 13/13 targets read from the committed `TARGET_RANKING` by a rule committed first; two orderings pre-registered; seeds 1337 plus one new seed from Phase 35's `seed_list`; Phase 40 `pet_name` taught and M2 adapters reused by SHA-256 and never retrained | VERIFIED | `phase35_prereg.e1_targets()` returns `('pet_name','cat_name','street','sibling_name')`. It filters `phase19_erasure.TARGET_RANKING` (scripts/phase19_erasure.py:604-613) on `successes == n_questions` (scripts/phase35_prereg.py:382-395). The rule was first added in fa605e3 (2026-10-01), before the first record b42900d. `ORDERINGS = ('greedy','gradient')` (phase41_prereg.py:982, added d6f12e9, an ancestor of b42900d). `e1_teaching_seeds() = (1337, 2024) = seed_list()[:2]`. All 4 adapter files hash to their `phase40_noise_floor.json::phase41_adapters` digests (True x4). All 16 cell records' `adapter.sha256` equal the full-adapter digest (16/16). The driver refuses to run on a digest mismatch (`adapter_digest_failures`, phase41_erasure.py:885-897, enforced at :1410-1416). `grep -c "train_arm(" scripts/phase41_erasure.py` returns 1, and that call is the calibration helper (`tp.arm_spec("cal_first_person_replay")`, :433-435) |
| 2 | Each floor derived in writing before measurement, calibrated per (ordering, seed) and budgeted. Rank never in the stop and recorded at every checkpoint. Grid read with A2 at K = 16, first zero confirmed at K = 48, non-zero K = 48 continues | VERIFIED | The floors file was first and last touched in b8c0e81. `git merge-base --is-ancestor` shows b8c0e81 is an ancestor of all 16 cell records' first adds (16/16) and comes after the 4 calibration records (b42900d). Floors cover 16 keys over 4 (ordering, seed) calibration records, all 0.0911 `reachability-min`. Calibration budget: `_CALIBRATION_HOURS` (phase41_prereg.py:288, :498). Grid printed from `E1_CHECKPOINT_GRID`: checkpoints (16,32,48,64,128), read_k 16, confirm_k 48. `e1_stop(grid, readings)` takes no rank input (phase35_prereg.py:1075). Rebuilt from the cell reads, `e1_stop` equals the recorded `stop` and `e1_stop.stop` in 16/16 cells. All 48 reads carry an int rank. All 48 K=16 `target_count` values were recomputed from the K=16 record draws (`k16_target_count`) with 0 mismatches, and k16 sha256 values match. All 23 K=48 `k48_zero` flags were recomputed from the A2 record rows (`record_rows`) and agree. The "continue on non-zero K=48" path is exercised: cat_name greedy 1337 at 64 (1/27, then stop 128), pet_name greedy 1337 at 48 (1/27), pet_name greedy 2024 at 48 (2/27), sibling_name greedy 1337 at 32 and 48, street gradient 2024 at 16 (3/27) |
| 3 | Defect E routed by a wrapper that imports the pin; a test proves `scripts/phase19_erasure.py` byte-unchanged; condition (c) is a bilateral dialogue band anchored on the adapted model, with D-01 logic imported from `mitigation_gate` | VERIFIED | `phase37_routes.select_target_prefix` (phase37_routes.py:154-184) does `import phase19_erasure as pin` (:35) and calls `pin.select_ablation_prefix` unedited. The greedy ordering goes through it (phase41_erasure.py:677-688). `test_pin_and_gate_are_byte_unchanged_for_phase41` and `test_pin_and_gate_are_byte_unchanged` both PASSED. The pin's sha256 on disk, c407246d…6cb303, equals each cell's `module_sha256_at_launch`. `phase35_prereg.DIALOGUE_GAP_BAND is mitigation_gate.dialogue_gap_band` returns True. The band is a (lo, hi) pair on the on-off gap (`condition_c`, phase41_prereg.py:1140-1150). It is anchored on the control gap re-measured on the intact full adapter. All 4 bands were recomputed with `mitigation_gate.dialogue_gap_band(control_gap=band_inputs.control_gap, gap_noise_floor=0.08406970366097503)` and equal the filled values. `equal` is True in all 4 band-input records |
| 4 | Damage reported per non-target fact, each with its own denominator; no cell reads PASS without replication at the second seed | VERIFIED | Independent recompute over all 16 cells: post counts come from the stop's K=48 A2 record and pre counts from `phase40_a2_full_seed{s}.json`. Each cell has 7 non-target slots, each with its own n/27 denominator, judged against the exact margin 8/27. Condition (c) was recomputed from the stop record's `dialogue_ppl`. Verdicts, beyond-margin sets, (a) and (c) all match `results/phase41_erasure.json`, with 0 mismatches. Pair labels: 8/8 "FAILURE replicada", and every pair has FAILURE at both 1337 and 2024. The assertion "PASS label without SUCCESS at both seeds" finds 0 cases. The report renders per-slot n/27 tables per cell (e.g. report lines 44-80) |
| 5 | No record exists before the prereg module and its ancestry test are committed; result records are write-once and committed only after Rafael's approved | VERIFIED | `scripts/phase41_prereg.py` and `tests/test_phase41_prereg.py` were both first added in d6f12e9 and last touched in c8fc75d. Both commits are ancestors of the first record b42900d. The floors file and its test (b8c0e81) come before every later record. The four frozen and first-added tests PASSED. Every tracked `results/phase41_*` file (96) has exactly one commit, except `phase41_erasure_report.md`, which has two: 54ef68c (the render) and 2da7ba2 (a `_addendum.py` dated continuation, a pure append of +10/-0 lines). In Python, the current file `startswith` the 54ef68c bytes (True), and `render_report(phase41_erasure.json)` is byte-equal to the 54ef68c blob (True). `phase41_erasure.json` sha256 is 78d3e4b5…984264d2, the approved value. 20/20 `results/phase41_*` commits name an approved (`grep -vc approved` = 0). Ledger 37324be is an ancestor of the first cell ab79f87. The driver is unchanged since the cell launch: there are no commits to the driver or prereg in 5f158d3..HEAD, the current driver sha256 a5ee8d45 equals every cell's launch digest, and `head_moved_during_run` is False in 16/16 cells |

**Score:** 5/5 success criteria verified.

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `scripts/phase41_prereg.py` (fill file 1, rules) | VERIFIED | 2197 lines; frozen before first record |
| `scripts/phase41_floors_prereg.py` (fill file 2) | VERIFIED | Floors (16 keys) and bands (4 keys) fill from committed stage-1 records |
| `scripts/phase41_erasure.py` (driver) | VERIFIED | 2972 lines; wired to `phase37_routes`, `phase35_prereg.e1_stop` (:1908), prereg `condition_c` (:2317) |
| `results/phase41_calibration_*` / `band_inputs_*` (4 + 4) | VERIFIED | Committed in b42900d; consumed by the floors file |
| `results/phase41_cell_*` (16) + K=16/K=48 records | VERIFIED | ab79f87..67f4aec, one commit per cell |
| `results/phase41_erasure.json` | VERIFIED | 14a0cc6; sha matches the approved value; status COMPLETE |
| `results/phase41_erasure_report.md` | VERIFIED | 54ef68c render-equal plus 2da7ba2 pure-append continuation |
| `ledger/v6_mps_ledger.jsonl` E1 lines | VERIFIED | 37324be before cells |

## Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| phase41_erasure greedy ordering | phase19_erasure pin | `phase37_routes.select_target_prefix`, which calls `pin.select_ablation_prefix` | WIRED |
| condition (c) | mitigation_gate D-01 | `phase35_prereg.DIALOGUE_GAP_BAND is mitigation_gate.dialogue_gap_band`, used to fill the bands | WIRED (identity True) |
| cell stop | `phase35_prereg.e1_stop` | `prereg.stop_readings(reads)` (no rank field) | WIRED |
| floors | calibration records | `floors_fill_inputs()`, then `fill("e1_condition_a_floors")` | WIRED |
| driver | Phase 40 adapters | `phase40_adapter` / `adapter_digest_failures` refuse on mismatch | WIRED |

## Behavioral Spot-Checks / Commands Run

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Guard set from the brief | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py tests/test_phase41_prereg.py tests/test_phase41_floors_prereg.py tests/test_phase37_routes.py -k "byte_unchanged or frozen or first_added"` | `6 passed, 258 deselected in 66.37s` | PASS |
| SC1 | python: e1_targets / ORDERINGS / e1_teaching_seeds / 4 adapter digests / 16 cell adapter digests; `grep -c "train_arm("` | as in row 1; 1 | PASS |
| SC2 | scratchpad sc2.py: ancestry of the floors file, `e1_stop` re-applied, rank and sha per read; K=16 and K=48 zeros recomputed from raw records | 16/16; 48 K=16 reads 0 mismatches; 23 K=48 reads agree | PASS |
| SC3 | byte-unchanged tests; identity check; bands recomputed | 2 passed; True; 4/4 equal | PASS |
| SC4 | scratchpad sc4.py: verdicts, (b) sets and (c) recomputed from A2 records; pair labels | 0 mismatches; PASS 0, FAILURE replicada 8 | PASS |
| SC5 | per-file commit count, approved grep, ancestry, report prefix and render equality | as in row 5 | PASS |

The full suite was not re-run, as the brief instructed (the SUMMARY claims 3 runs of 4709 passed / 4 skipped).

## Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| ERASE-03 | SATISFIED | SC1: `e1_targets()` is a rule over `TARGET_RANKING`, committed in fa605e3 before any record |
| ERASE-04 | SATISFIED | `ORDERINGS = ('greedy','gradient')`, pre-registered in d6f12e9. The adaptive/static variant rule is pre-registered at phase41_prereg.py:1817-1835 and decided by `mps_smoke`, with the variant.json sha recorded |
| ERASE-05 | SATISFIED | Seeds (1337, 2024) = `seed_list()[:2]`; 4 digests match; driver refuses on mismatch; no Phase 40 retrain |
| ERASE-06 | SATISFIED | Floors per (target, ordering, seed) from 4 per-(ordering, seed) calibrations, budgeted, and committed (b8c0e81) before every cell |
| ERASE-07 | SATISFIED | Grid (16,32,48,64,128), K=16 reads, K=48 confirms, continue on non-zero. The rank is absent from `e1_stop` and recorded in 48/48 reads |
| ERASE-08 | SATISFIED | Wrapper `phase37_routes.select_target_prefix` imports the pin; byte-unchanged tests pass; pin sha matches launch provenance |
| ERASE-09 | SATISFIED | Bilateral (lo, hi) band on the on-off gap, anchored on the intact full adapter's control gap; identity with `mitigation_gate.dialogue_gap_band` |
| ERASE-10 | SATISFIED | 7 per-slot n/27 rows per cell; pair labels require both seeds; 0 PASS without replication |

No requirements are orphaned: REQUIREMENTS.md maps exactly ERASE-03..10 to Phase 41, and 41-16 claims all eight.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| scripts/phase41_erasure.py / phase41_prereg.py / phase41_floors_prereg.py / tests/test_phase41_* | — | TBD/FIXME/XXX/TODO/HACK | none found | — |
| scripts/phase41_erasure.py | 2567 | Report label reads "ERASE-10: the exposure rank recorded, never read by the stop". Recording the rank is ERASE-07 | Info | Wrong requirement ID in a published write-once report (every cell section). It is not a number and does not change a verdict. If corrected, it would be a dated continuation |
| scripts/phase41_prereg.py | 489-498 | Condition (a) is vacuous at the judged stop by construction (WR-01): the stop requires 0/27, and the floor is at least `wilson_upper(0,27)` | Info | Declared in advance and ruled by Rafael 2026-10-08. All 16 floors fell on `reachability-min` (calibration rate 0/23), so (a) cannot decide a verdict. Verdicts rest on (b) and (c) |

## Human Verification Required

None. Every record, the report and the addendum text already carry Rafael's approvals, which are quoted in the commit messages. No UI or real-time behaviour is involved.

## Orchestrator Hand-Close (not a gap in the goal)

The goal is achieved, but the planning trackers are still open. Per the brief these were not touched:
- `.planning/REQUIREMENTS.md:737-744` ERASE-03..10 are still `[ ]`, and traceability rows 820-827 still read `Pending`.
- `.planning/ROADMAP.md` still shows Phase 41 and the 41-14..16 plan boxes unchecked (41-16-SUMMARY lists the lines).
- STATE.md progress is not updated, and the Obsidian entry is pending.

## Gaps Summary

There are no gaps. All five ROADMAP success criteria and all eight ERASE requirements were checked by re-run commands. The verdicts, stops, K=16 and K=48 zeros, bands and pair labels were recomputed from the raw committed records, and every recomputed value agrees with the published erasure record. The report is byte-equal to `render_report` of that record, with a pure-append dated continuation.

**Not verified:** The full test suite was not re-run, by instruction. MPS measurements were not re-run, so the draws inside the A2 and K=16 records are taken as committed. Their hashes and the counts derived from them were checked, but not their regeneration. The adapters were checked by digest only; no retraining was run to compare against.

---

_Verified: 2026-10-13_
_Verifier: Claude (gsd-verifier)_
