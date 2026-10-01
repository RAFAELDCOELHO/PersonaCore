---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
plan: 03
subsystem: prereg
tags: [prereg, slot-registry, e3-grid, p22-onset, one-run-audit, d-17]

requires:
  - phase: 35-02
    provides: v6.0 core (ENTRIES, seed_list, e1_targets, e1_condition_b_margin, e4_runs, eps_lower_one_run, one_run_reproduction_holds, V6_RESULT_PATHS, E3_SIGMAS)
provides:
  - SLOTS registry (17 deferred slots), fill(), owner_prereg_glob(), SLOT_FIELDS
  - _consume_inputs (W3), _budget_front_hours, _v4_control (byte identity vs tag v5.0), _is_hex_digest
  - p22_onset_sigma / _p22_breached (RECIPE-04), E3_N, E3_UNIT, V6_MPS_FRONTS
  - ENTRIES p22_two_oracle_budget, e2_min_seeds, e4_inclusion_probability (21 entries total)
affects: [35-04, 35-05, phases 36-43]

tech-stack:
  added: []
  patterns:
    - "A slot is filled only through fill(); every measured fill consumes its named records with a four-field derivation of the filled value"
    - "Controls are keyed by the recipe read from their own record, never by position or caller"

key-files:
  created: []
  modified:
    - scripts/phase35_prereg.py
    - tests/test_phase35_prereg.py

key-decisions:
  - "e3_recall_threshold's 'v4.0 record listed while the grid reuses nothing' refusal fires at the D-17 key-set check: the v4.0 record's own key (its seed) can never match a grid that does not reuse it, so the reuse-equality check is reached only by the 'phase42 control instead of the v4.0 record' case"

requirements-completed: []
# The orchestrator ticks requirements at phase close; this plan's `requirements:` list
# (PREREG-05, PREREG-06) names IDs it contributes to, not IDs it closes.

duration: 9min
completed: 2026-10-01
---

# Phase 35 Plan 03: Deferred-slot registry Summary

**The registry of deferred slots is now code. It declares 17 slots, each with an owner phase, a `_rule_<slot>` function and its input records, and the only way to fill one is `fill()`. A measured fill has to consume the records it names and carry a four-field derivation of the filled value. D-06, D-11, D-16, D-17 (including B4 and W15) and RECIPE-04 are coded refusals, and each one is watched firing in a CPU test.**

## Performance

- **Duration:** about 9 min (base 23d5554 at 18:36:05 -0300; feat commit bd4d299 at 18:44:50 -0300)
- **Tasks:** 2, committed together in one feat commit
- **Files modified:** 2 (+806 / +598 lines)

## The 17 slots (Phases 36-43 read this table)

| Slot | Owner | Declared input records | Rule keyword arguments |
|------|-------|------------------------|------------------------|
| v6_budget_and_stop_line | 36 | `results/phase36_probe_*.json` | front_hours, stop_line_hours, input_records, derivation |
| r1b_tolerance_and_replicated | 37 | none | tolerance, replicated_definition |
| e5_minting_rule | 38 | none | minting_rule |
| e5_set_sizes | 38 | `results/phase38_minting*.json` | set_sizes, input_records, derivation |
| e5_rank_moves_and_generation_collapses | 38 | none | moves, collapses |
| e6_entry_subset | 39 | `results/phase36_probe_*.json` | entry_indices, input_records, derivation |
| e6_decomposition_rule | 39 | none | decomposition |
| e2_S | 40 | `results/phase36_budget.json` | s, input_records, derivation |
| e2_noise_floor_estimator | 40 | none | estimator |
| e1_checkpoint_grid | 41 | `results/phase36_budget.json` | checkpoints, input_records, derivation |
| e1_condition_a_floors | 41 | `results/phase41_calibration_*.json` | floors, input_records, derivation |
| e1_alternative_ordering | 41 | none | ordering |
| e1_condition_b_margin | 41 | `results/phase19_noise_floors.json` (read in the core, D-16) | none (locked) |
| e1_condition_c_band_inputs | 41 | `results/phase40_noise_floor.json`, `results/phase41_band_inputs_*.json` | band_inputs, input_records, derivation |
| e3_grid_subset | 42 | `results/phase36_budget.json`, `results/phase25_point_dp_n8_sigma0p000000.json` | recipes, seed, input_records, derivation, fifth_recipe_derivation=None |
| e3_recall_threshold | 42 | `results/phase42_control_*.json`, `results/phase25_point_dp_n8_sigma0p000000.json` | grid, input_records, derivation |
| e4_parameters | 43 | `results/phase38_minting*.json` | m, inclusion_probability, k_plus, k_minus, beta, input_records, derivation |

The v4.0 control path is `_V4_CONTROL_RECORD`, computed at import from `phase25_record.point_record_path(point_key(f"dp_n{E3_N}", E3_SIGMAS[0]))`. It is never typed.

## Owner fill-file convention (Plan 04 enforces it)

An owner fills its slots from one or several files matching `scripts/phase{owner}_*prereg.py` (`owner_prereg_glob(slot)`). Each file binds `<SLOT NAME UPPER-CASED> = phase35_prereg.fill("<slot>", ...)` at module level after a plain `import phase35_prereg`.

- **(a)** A slot with no input record of its own phase precedes every record of that phase. Only slots that consume an in-phase input are exempt from that input, per fill file. So a fill file that holds any slot without a declared `results/phase{owner}_*` input precedes every `results/phase{owner}_*` record. A fill file whose slots all consume in-phase inputs precedes every such record except those inputs.
- **(b)** Each declared input precedes the first commit of the file that consumes it.
- **(c)** Once a phase-O record that is not a declared input of any phase-O slot is tracked, every phase-O slot is filled.
- A slot is filled exactly once, anywhere. This is the planner's reading of D-02 for multi-step phases (B1), and Plan 05 shows it to Rafael.

## Record contracts

- **Budget record** (`results/phase36_budget.json`, Phase 36): it has the output keys of `_rule_v6_budget_and_stop_line`. `front_hours` is keyed by exactly `V6_MPS_FRONTS = ("probes", "R1b", "E1", "E2", "E3", "E4", "E5", "E6")`; the other keys are `total_hours` and `stop_line_hours`. `e2_S`, `e1_checkpoint_grid` and `e3_grid_subset` each refuse a front budgeted 0 h.
- **Phase 42 control record** (`results/phase42_control_*.json`): `recipe` = {lr, steps, batch}, `seed`, `sigma` = 0.0, and `taught_recall` / `heldout_recall`, each with `numerator` and `denominator`. That is the field shape of the v4.0 point record.

## Acceptance results (tool output)

- Task 1, first probe (fresh import, no call): `False`.
- Task 1, second probe: `17 [36, 37, 38, 39, 40, 41, 42, 43] 0.2962962962962963 0.078902 8 one taught fact scripts/phase40_*prereg.py`. That matches the plan exactly.
- The unrounded P22 onsets were `p22_onset_sigma(200)` = 0.07890181429684162, `(400)` = 0.11158308945596218 and `(9000)` = 0.5293140490539372, the same as the plan's measurements. The probe took 0.67 s wall.
- `fill('e2_S', s=6, ..., derivation={})` gave exit 1 with `[phase35_prereg] the Phase 36 probe calls for S > len(seed_list()): STOP and ask Rafael (D-06); the seed list is never extended`.
- `fill('e9_undeclared')` gave exit 1 with `[phase35_prereg] slot 'e9_undeclared' is not declared in the Phase 35 registry (D-02)`.
- After Task 1, `tests/test_phase35_prereg.py` gave 39 passed. `tests/test_phase25_prereg.py -k bit_identity` gave 2 passed, 18 deselected. Ruff check passed and format reported "1 file already formatted".
- Task 2 verify: `tests/test_phase35_prereg.py tests/test_phase29_prereg.py tests/test_phase25_prereg.py` gave 159 passed. `ruff check .` reported "All checks passed!" and `ruff format --check .` reported "327 files already formatted" (exit 0).
- `-k "slot or e2_S or e3_grid or e3_recall or e4_parameters"` (with `-rs`) gave 20 passed, 39 deselected, 0 skipped.
- After commit bd4d299: the dirty filter printed nothing, `git status --porcelain -- scripts/ tests/ results/` was empty, and both `find results -name 'phase3[5-9]_*' -o -name 'phase4[0-5]_*'` and `git ls-files` printed nothing.
- Clean-tree probe files after the commit: `tests/test_phase25_driver.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase23_ctrl.py tests/test_phase30_calibration.py` gave 71 passed.
- Census greps over both files found no `== 10`/`!= 10`, sigma0/sigma_zero/seam_off/dp_fn, `os.replace`, `privacy_n`, `train_arm(`, `train_never_taught` or `inject_lora`. The test file never calls `hashlib`. The only `sha256` in it is the record key string `"adapter_sha256"`.
- Refusal reasons were checked one by one: each case was run under a `pytest.raises` wrapper that printed its message. Every refusal fires with its intended message, with the one exception noted under Deviations 1. Examples: the modified v4.0 copy gives "not byte-identical to its copy at tag v5.0 (D-17: verified by SHA-256)", T=9000 gives "crosses the P22 WARNING-4/5 region at T=9000 (onset 0.5293140490539372) ... (RECIPE-04)", the patched reproduction gives "D-11: ...", stop line 91 gives "HALT ...", and the seed-2024 fifth recipe gives "no reused control, no saved run".
- E4 ceilings used by the tests: `eps_lower_one_run(16,16,16,DELTA,0.05)` = 1.5798048879951239 (runs False) and `(184,184,184,...)` = 4.104607757180929 (runs True), against `audit02_cut()` = 3.7965357228934966.

## Premises re-measured

All the orchestrator's premises held when re-measured. Importing phase25_gate05, phase25_record, phase29_prereg and the accountant loaded none of torch, teach_persona, phase23_run, phase26_canary, phase19_erasure or phase18_extraction. `len(GATE05_SLOTS)` is 8 and `DP_ARMS` is ('dp_n8', 'dp_n64'). The v4.0 record reads seed 1337, sigma 0.0, composed_steps 200, train_config lr 0.0003 / max_steps 200 / batch_size 8, taught 790/1008, heldout 346/648, n_facts 8, with a 64-hex adapter_sha256. Its working-tree bytes pass the v5.0 byte-identity check (`_v4_control()` on the real tree). `tests/test_phase22_accountant.py` line 536 contains `1e-9 * abs(b)`. teach_persona has LR = 3e-4 at :1587 and BATCH_SIZE = 8 at :1593, and STEP_BUDGET is 200. No premise was falsified.

## Task Commits

1. **Tasks 1-2: slot registry + rule tests**: `bd4d299` (feat). It touches only `scripts/phase35_prereg.py` and `tests/test_phase35_prereg.py`.

## Deviations from Plan

1. **The recall-threshold "v4.0 record listed, grid reuses nothing" case.** The plan describes this refusal as the reuse rule's. It actually fires at the D-17 key-set check ("a control keyed to a recipe outside the grid ..."). The v4.0 record's key carries its own seed, so it can only lie in the grid's key set when the grid holds the v4 recipe at that seed, and that grid always reuses. The reuse-equality `_prove` is reached, and watched firing, by the "phase42 control for the v4 recipe instead of the v4.0 record" case. Both are SystemExit refusals and neither is a missing file.
2. **Test seeds and counts are derived, not typed.** `s=6` is `len(seed_list()) + 1`. The band and floor seeds are `e1_teaching_seeds()[0]` and the first `seed_list()` seed outside the teaching seeds (1338). The off-list grid seed is `max(seed_list()) + 1`. Set size 512 is read from `ENTRIES["e5_max_set_size"]` and asserted == 512.
3. **Test split.** The plan's `test_slot_e5_e6_and_design_entries` became two tests: `test_slot_e5_e6_set_sizes_and_entry_subset` and the parametrized `test_slot_design_entries_refuse_a_proposer` (5 cases). Both carry the `slot` selector.
4. **A small `_prove_finite` helper** (`_prove_real` plus `math.isfinite`) backs the plan's "finite number" checks.
5. **`_rule_e5_rank_moves_and_generation_collapses`** returns a read-only `{moves, collapses}` mapping, following the plan's "every returned container is a MappingProxyType or tuple".
6. **Import placement.** Ruff's isort put `from personacore.privacy import accountant` in its own block after the sibling-script imports.

## Known Stubs

None. The design slots require a four-field entry, which is the declared rule (PREREG-06) and not a placeholder.

## Threat Flags

None beyond the plan's threat model. `_v4_control` runs a read-only `git show v5.0:<path>` subprocess, and only inside the rule call, never at import. That is the T-35-14 mitigation as the plan specifies it.

## Self-Check: PASSED

- FOUND: scripts/phase35_prereg.py, tests/test_phase35_prereg.py (modified in bd4d299)
- FOUND commit: bd4d299
