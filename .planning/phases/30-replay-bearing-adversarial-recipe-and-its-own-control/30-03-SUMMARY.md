---
phase: 30-replay-bearing-adversarial-recipe-and-its-own-control
plan: 03
subsystem: v5.0 calibration emitter (scripts/phase30_calibration.py)
tags: [ARECIPE-02, D-05, D-06, D-07, D-08, D-09, D-10, D-11]
requires: [teach_persona.build_bins / arm_spec / render_episodes (lazy), phase24_adversarial (MIN_REFUSAL_SCORED_TOKENS, MASK_FRACTION_MARGIN), phase29_prereg (LEGS, ADVR_ARMS, RATIO_GRID, replay_windows, ARTIFACT_PATHSPECS), phase30_points (recipe_identity, require_calibrated_recipe, CALIBRATION_PATH, RECIPE_FIELDS, SWEEP_SEED), phase25_run.atomic_write_json, personacore.provenance]
provides: [phase30_calibration.derive, descriptive_step_mix, build_record, emit, main, RECORD, PINNED_MODULES]
affects: [30-04 (emits results/phase30_calibration.json from the clean tree), Phase 31-34 (ancestry: calibration must precede every other v5.0 result)]
tech-stack:
  added: []
  patterns: [tempdir bins replaying build_arm_bins' flat-branch call, sha256 bin equality as structural evidence, write-once + dirty-first emitter, ancestry freeze with natural-RED non-vacuity]
key-files:
  created:
    - scripts/phase30_calibration.py
    - tests/test_phase30_calibration.py
  modified: []
decisions:
  - "Case B of the planted-replay test (advr replay_ratio 0.5) refuses locally through teach_persona's WR-04 flat-branch refusal at the hi corner. The lo corner builds fine because the replay source exists on this host."
  - "PINNED_MODULES spells scripts/teach_persona.py as a path. teach_persona imports torch, so the emitter keeps it lazy and reads no module object at import. The other four paths come from __file__ attributes."
requirements-completed: []
metrics:
  duration: ~30 min
  completed: 2026-09-25
---

# Phase 30 Plan 03: ARECIPE-02 calibration emitter — Summary

`scripts/phase30_calibration.py` re-derives the D-05 refusal floor live at the replay-bearing recipe and gets **15**, which matches the frozen `phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS`. The bins are built in a tempdir, not in `data/`. The emitter shows by sha256 that replay never enters the teaching bin. It refuses under D-08 if the floor moves. It also records the descriptive per-step mix and the per-leg recipe identity that `require_calibrated_recipe` reads. It was not run in this plan, and `results/phase30_calibration.json` does not exist. Plan 30-04 emits it.

Requirement ticks: the orchestrator/verifier rules on ARECIPE-02. This plan marks nothing complete.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | `6ff504e` | feat(30-03): ARECIPE-02 calibration emitter (live D-05 re-derivation) |
| 2 | `f78fcf6` | test(30-03): D-11 ancestry and emitter freeze guards |

## Evidence (raw, from a dry `derive()` / `build_record()` in memory; nothing written under results/)

- **Derived floor L = 15** (== `MIN_REFUSAL_SCORED_TOKENS`).
- Inputs: clean_scored_tokens **2719**, clean_tokens **7581**, attack_pool_episodes **336**, pool_prompt_tokens **26054**.
- target = 0.15 + 0.05 = **0.2**. frac(15) = **0.20062055591467357**, frac(14) = **0.19361485693419234**.
- Corners: `[0.0, 1.9090909090909092]`. Wall time for derive() is about 1.7 s on CPU.
- arm_spec triples: advr_n8 `{n_facts 8, second_person false, replay_ratio 0.0}` and adv_n8 has the identical triple.
- Bin sha256s. advr_n8 and adv_n8 are **identical** at both corners:
  - 0.0: bin `f146d42637c69e9eb1e7ac2248c9056a7966aed48f6498fa9cdb6d3db02d147b`, mask `a2c4771f92aa4e03127e451b1de880b9386bee5164ee512d291467c1eb1e59a2`
  - 1.9090909090909092: bin `aa7ecb550aa4177dbddb6fe11d15dde408cedfa06a4fdd83187a9bc94f791509`, mask `92b9bda0b34c686091668949348152e391b79c99276ec56fea360c7fe79caf43`
- Planted arm_spec for advr_n8:
  - second_person=True gives `[phase30_calibration] the advr_n8 teaching bins differ from adv_n8's (...): the structural reason ... is FALSE`.
  - replay_ratio=0.5 gives `[teach_persona] build_bins got replay_ratio=0.5 AND adversarial_ratio=1.9090909090909092 on the flat branch ...` (WR-04).
- Descriptive mix: n8 has teaching 8 windows / 2048 tokens against replay 32 / 8192. n64 has teaching 8 / 2048 against replay 256 / 65536. `gates_nothing: true`. The AST census finds `"descriptive_step_mix"` only in phase30_calibration.py.
- Recipe per leg equals `phase30_points.recipe_identity(leg)`: n8 `{8, 32, 1337, 200, 15, [data/dialog_train.bin, data/dialog_train_mask.bin]}` and n64 `{64, 256, …}`. It round-trips through `require_calibrated_recipe`, and each of the 6 fields is refused when perturbed.
- D-08: margin + 0.01 moves L off 15, computed in the test. Both `derive()` and `emit(tmp)` raise `D-08`, and tmp/c.json is absent afterwards.
- PINNED_MODULES: `scripts/phase30_calibration.py, scripts/phase30_points.py, scripts/teach_persona.py, scripts/phase24_adversarial.py, scripts/phase29_prereg.py`.

## Tests

- RED, Task 1 (natural): with the module moved aside, the run stopped at a collection error (`No module named phase30_calibration`). GREEN: the plan's verify set (calibration + points + phase24_band + phase24_refusal) gave **45 passed**.
- Task 2: `tests/test_phase30_calibration.py` gave **9 passed**. Both ancestry tests are honest-green, because the calibration is untracked and no later v5.0 result is tracked. Both natural-RED `CalledProcessError` assertions execute: the calibration one only once the calibration is tracked, the emitter one against `scripts/phase29_prereg.py` now.
- Guard set on the committed tree (calibration, phase30_points, phase30_seam, phase29_prereg, phase27_relearn, phase24_record, test_lora_inject, test_phase21_sc5) gave **190 passed** in 79.5 s.
- Clean-tree probes (production_resume_epsilon, the phase25 frontier/grid/probe2/driver/epsilon/plots/watch planted set) gave **11 passed** after the commits.
- `ruff check .` reported all passed. `ruff format --check .` reported 296 formatted.
- The full suite was NOT run, on orchestrator instruction.

## Deviations from Plan

1. **Full suite not run (orchestrator override of Task 2's last step).** The orchestrator runs it.
2. **RED obtained by moving the finished module aside.** The module was written before the test file, so RED came from running the tests with the module moved away rather than from a test-first file. It is still natural RED (collection error), with no planted code.
3. **`_git` / `_assert_frozen_before` imported from test_phase29_prereg** (the plan asked for this). `_git` there strips output, and the results-status comparison is unaffected.
4. **Operational note, not a code change.** `test_derivation_refuses_a_replay_entering_the_bin` snapshots `data/` with mtimes. It went RED once when I ran the clean-tree probes **concurrently** in a second pytest process. `test_phase23_resume`'s production probe rebuilds `data/persona_dp_n8_train*.bin` by design and leaves them in place (its `_clear_bins` docstring says so). Sequential runs are green. Do not run this file in parallel with that probe.

teach_persona.py was not touched. No results/ writes were made. No STATE/ROADMAP/REQUIREMENTS edits were made, and no gsd-sdk mutation handler was called.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: scripts/phase30_calibration.py, tests/test_phase30_calibration.py
- FOUND: 6ff504e, f78fcf6
- `results/phase30_calibration.json` absent.
