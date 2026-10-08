---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 07
subsystem: erasure-driver
tags: [phase41, e1, driver, calibration, d-11, d-13, d-20, d-25, d-26, d-27, erase-04, erase-05, erase-06, erase-07, erase-08, erase-09]
requires: [41-06]
provides:
  - "phase41_erasure: arm_name, arm_paths, train_calibration_adapter (the driver's one registered train_arm call), calibration_identity (D-11 + amendment), twin_references, collateral, greedy_calibration, gradient_calibration, cal_erase"
  - "phase41_erasure: phase40_adapter, measure_control_gap, target_fact, cell_ordering, k16_read, k48_confirm, export_m1, d13_at_stop"
  - "artifacts/com.personacore.phase41.e1.plist (D-25)"
affects: [41-08, 41-09, 41-10]
tech-stack:
  added: []
  patterns: [thin wrappers over the unedited pin, write-once raw outputs under data/phase41_e1/, the Phase 40 ruling-c catch reused]
key-files:
  created: [artifacts/com.personacore.phase41.e1.plist]
  modified: [scripts/phase41_erasure.py, tests/test_phase41_erasure.py, tests/test_phase23_resume.py]
decisions:
  - "calibration_identity takes exactly one digest, of the Phase 19 reference file at its original path, against phase41_prereg.D11_REFERENCE_SHA256; the new adapter is compared by torch.equal only. An AST test pins the digest's only argument to `reference`"
  - "a reference digest mismatch fills a `finding` string and reference_sha256_matches_record False; nothing refuses"
  - "d13_at_stop also carries phase40_noise.run's malformed-return branch (malformed_reading), not just the exception catch; both shapes add n_nlls None"
requirements-completed: []
metrics:
  duration: not recorded
  completed: 2026-10-08
---

# Phase 41 Plan 07: E1 measurement mechanics Summary

`requirements-completed: []`: 41-07 writes the mechanics ERASE-04..09 will be run with. Nothing was run and no record was written, so no requirement is complete.

This plan adds the E1 driver's measurement layer. Each function is a thin wrapper over the unedited pin (`phase19_erasure`), `phase37_routes`, `phase40_noise` and the frozen prereg, and each is tested on fakes on CPU:

- the per-seed calibration adapter, registered as the driver's one training call site;
- the D-11 tensor identity, with the amendment's digest check;
- both calibration orderings, and cal-erased written under `data/`;
- the D-13 control gap and both cell orderings (greedy goes through the defect-E route);
- the K = 16 reader, which passes the draw_all census with no register edit;
- the K = 48 confirmation, which always passes a `record_path` (AST-gated);
- the M1 export and the D-13 wrapper;
- the E1 LaunchAgent.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | 83bf316 | calibration adapter + register line/tripwire TWENTY, D-11, greedy/gradient calibration, cal_erase; 15 tests |
| 2 | 8f91519 | phase40_adapter, control gap, cell_ordering, k16_read, k48_confirm, export_m1, d13_at_stop; 12 tests |
| 3 | 18a6129 | E1 plist + mirror test |

## RED (tests first)

- Task 1: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py` gave `15 failed, 12 passed in 2.42s`. Every failure was an `AttributeError` (`arm_name` x6, `train_calibration_adapter` x3, `calibration_identity` x2, `gradient_calibration` x2, `greedy_calibration`, `cal_erase`).
- Task 2: the same command gave `12 failed, 27 passed in 3.95s`. The failures were `AttributeError`s (`measure_control_gap` x4, `k48_confirm` x2, `phase40_adapter`, `cell_ordering`, `k16_read`, `export_m1`) plus two natural census REDs: `assert [] == ['k16_read']` (no draw_all site yet) and `assert 1 >= 2` (only cal_erase called run_erasure_arm).
- Task 3 (type auto, no TDD) was written test-alongside.
- No separate RED was captured for the register: the line was added in the same edit pass as the call. The evidence is `grep -c "train_arm(" scripts/phase41_erasure.py` = 1 against the +1 register entry, with test_phase23_resume green.

## Acceptance lines as printed

- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py tests/test_phase23_resume.py` gave `36 passed in 103.54s`. That was the Task 1 state; the MPS resume probe ran, and results/ was clean.
- `grep -c "train_arm(" scripts/phase41_erasure.py` gave `1`, and the same count over `tests/test_phase41_erasure.py` gave `0`.
- `.venv/bin/python -c "import sys; sys.path[:0]=['scripts','src']; import phase41_erasure as d; print(d.arm_name(1337), d.arm_name(2024, rehearsal=True))"` printed `e1_calibration_seed1337 e1rh_calibration_seed2024`.
- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase41_erasure.py tests/test_phase14_scoring.py -k "draw_all or phase41 or k16 or k48 or control_gap or cell_ordering or m1"` gave `40 passed, 42 deselected in 6.09s`. `git diff --quiet -- tests/test_phase14_scoring.py` exited 0, so DRAW_ALL_ASSERTED_BY is untouched.
- `.venv/bin/pytest ... -k plist` gave `1 passed`. `plutil -lint artifacts/com.personacore.phase41.e1.plist` printed `OK`. The plan's json `diff` of the two plists, with the four changed keys popped, printed nothing (exit 0).
- `git diff --quiet 3787b9d -- scripts/phase19_erasure.py scripts/erasure_gate.py scripts/phase18_extraction.py` exited 0.
- `shasum -a 256 scripts/phase41_prereg.py` gave `11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3`, the frozen digest. Neither the prereg nor its test was edited.
- `find results data checkpoints -maxdepth 1 -name '*phase41*' | wc -l` gave 0, and `git ls-files 'results/phase41_*' | wc -l` gave 0.
- `.venv/bin/ruff check .` gave `All checks passed!`, and `.venv/bin/ruff format --check .` gave `366 files already formatted`.
- module_sha256 pins: a walk of every `results/*.json` found no `module_sha256` key that names `scripts/phase41_erasure.py`, `tests/test_phase41_erasure.py` or `tests/test_phase23_resume.py` (`[]`). The only hit, in `results/phase34_ledger.json` (rows[17].evidence), is prose and not a pin.
- No new `== 10` in the tests diff since 0406ead (grep empty).

## Census runs on the committed tree (HEAD 18a6129, tree clean but .claude/scheduled_tasks.lock)

- Batch 1 gave `1274 passed in 249.93s`, EXIT=0. Files: test_phase41_erasure, test_phase41_prereg, test_lora_inject, test_phase21_sc5, test_phase35_*, plus every file that scans `scripts/` as 41-06 ran them: phase14_scoring, 17_stats, 18_corpus, 18_prereg, 20_prereg, 20_correction, 19_erasure, 21_unit_continuation, 23_ctrl, 25_epsilon, 25_driver, 25_prereg, 30_calibration, 30_points, 29_prereg, 33_admission, 32_points, 37_prereg, 37_routes, 36_prereg, 39_ctx, 40_prereg, 38_rank, 38_prereg, 39_prereg and tokenizer_oracle.
- Batch 2 gave `226 passed, 3 skipped in 138.69s`, EXIT=0. Files: test_phase23_resume, 23_budget, 25_record, 25_promotion, 40_noise.

## What the tests prove

- **Calibration adapter.** The faked arm trainer receives `arm_spec("cal_first_person_replay")`, `TAUGHT_FAMILY_IDS`, the seed, the phase41/phase41rh prefix and no other kwarg. The csv lands at `data/phase41_e1/<arm>/run.csv` and the results/ csv dir is gone. Training refuses if any of the five outputs already exists, or if persona_adapter.pt changes.
- **D-11, both ways.** The test plants an equal adapter and a 1-ulp-different adapter. Each is run once with the reference digest equal to the prereg's (attribute patched) and once with it not equal. `reference_sha256_matches_record` and `finding` follow the digest, and `tensors_identical` follows the tensors. The test also proves that the file digests of the identical-tensor pair differ (the file-name effect).
- **Calibration orderings.** In the greedy calibration, the recorder sees the twin references, the CORE_SLOTS collateral and a live dialogue_ppl. In the gradient calibration, the rank stop at prefix 3 gives k = 3 with stopped True; with no stop, k = len(index) with stopped False. Every `_rank_of` call gets the twin set, and the tiny model is left intact.
- **cal_erase.** It calls the pin with `cal-erased`, `CALIBRATION_CORPUS_PATH` and `record_path` set to `data/phase41_e1/cal_erased_<ordering>_seed<seed>.json`. That path does not fnmatch `results/phase41_*`. The record is write-once, and an unknown ordering is refused.
- **Control gap.** It is checked on mps and cpu, for an equal and an unequal gap. The load uses the Phase 40 full adapter path from the record, and on an unequal gap `stop` is True only on mps.
- **Cell orderings.** Greedy uses `select_target_prefix` with the street LOCKED fact and a zero-argument dialogue_ppl, and returns its four keys. The gradient ordering uses `model_gradient_ordering(calibration=False)`.
- **k16_read.** The exact event order is checked: seed once, then assert before each draw on the real `_guarded_span`, with run_erasure_arm's value set, stride `seed_index * K` and `n_samples = read_k - 1`. The test also checks the pin's draw schema and the target's exposure, and that a short draw set is refused.
- **k48_confirm.** It calls the pin with `erased`, the Phase 40 full adapter and the root-relative `k48_record`. `target_zero` comes from `record_rows` on a copy of results/phase40_a2_full_seed1337.json, once real (False) and once with the street count patched to 0 (True). The record is write-once.
- **export_m1 and d13_at_stop.** export_m1 round-trips through `load_adapter` with the addressed A rows and B columns zero, the input untouched and write-once. For d13_at_stop: RuntimeError and SystemExit become `exception`; a malformed return becomes `malformed_reading`; a measured block passes through unchanged; KeyboardInterrupt propagates.
- **AST gate.** Every `run_erasure_arm` call in `scripts/phase41_*.py` passes `record_path`; there are 2 calls, so the scan is not blind, and a planted call without the argument fails.

## Deviations from Plan

1. **[Amendment over plan text] D-11 digest.** The plan's test said there is "no hashlib call on adapters" in `calibration_identity`. The orchestrator amendment, however, requires the reference file's sha256. The digest goes through `_sha256(reference)` once, at the reference's original path (`checkpoints/phase19_erase_calibration_adapter.pt`). The AST test pins the digest to that single argument and asserts there is no `hashlib` name in the function. The new adapter is never hashed inside it. A `finding` field holds the mismatch text. Commit 83bf316.
2. **[Rule 2] Extra refusals.** `cal_erase` refuses an ordering or seed outside the prereg's sets. `export_m1` is write-once. `k48_confirm` and `cal_erase` create the record's parent directory, because `run_erasure_arm` writes with `write_text` and needs it to exist. Commits 83bf316 and 8f91519.
3. **[Rule 2] Malformed return in d13_at_stop.** `d13_at_stop` also catches a malformed return, which is the second half of the `phase40_noise.run` catch the plan names ("exactly as phase40_noise.run does"). Both not-measured shapes carry `n_nlls: None`, as the plan's shape asks. Commit 8f91519.
4. **Memory release.** `measure_control_gap` drops its model and calls `_release()` after reading the pair.
5. **Per-NLL cost.** Nothing in this plan uses a per-NLL cost, so `VALUE_NLL_SECONDS` is not read here; it stays in the prereg for 41-08's budget check.
6. **Arm naming against 41-CONTEXT D-10.** D-10's text names the arm `erase_calibration`. The plan's `e1_calibration_seed<seed>` names were used, as the plan and threat T-41-24 require: they keep Phase 19's paths untouched. The csv dir `results/phase41_e1_calibration_seed*/` is the one WR-03 gitignored.

## Known Stubs

None. `_import_modules`, `_root_ledger` and `_device` are still uncalled; preflight and run arrive in 41-08 and later.

## Threat Flags

None beyond the plan's register: T-41-24, T-41-25, T-41-26 and T-41-27 are each enforced by a test above. T-41-28 is covered because adapters load only through `load_adapted_model` / `load_adapter`.

## Not verified

- No function ran on MPS, on the real corpus or on a real checkpoint. Everything here is fakes and the tiny CPU fixture.
- `phase40_noise.d13_scores` was never fed a real M1 export together with a real K = 48 `erased` record. The plan's wiring assumes that pairing; the first real feed is 41-08's smoke.
- `calibration_identity` against the real reference. Measured locally: the reference's sha256 is `bc616c36...56da`, which equals `D11_REFERENCE_SHA256`. Its tensor comparison waits for the new 1337 adapter.

## Self-Check: PASSED

- FOUND: scripts/phase41_erasure.py, tests/test_phase41_erasure.py, tests/test_phase23_resume.py, artifacts/com.personacore.phase41.e1.plist
- FOUND: 83bf316, 8f91519, 18a6129 (`git log --oneline -4`)
