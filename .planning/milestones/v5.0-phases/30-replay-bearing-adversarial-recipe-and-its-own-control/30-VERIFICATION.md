---
phase: 30-replay-bearing-adversarial-recipe-and-its-own-control
verified: 2026-09-25T00:00:00Z
status: passed
score: 4/4 roadmap success criteria, 27/27 plan must-have truths verified
overrides_applied: 0
---

# Phase 30: Replay-Bearing Adversarial Recipe and Its Own Control. Verification Report

**Phase Goal:** The adversarial arm trains with replay and is judged only against its own ratio-0 replay-bearing control, and the DP arms and the golden trajectory are provably untouched.
**Verified:** 2026-09-25, at HEAD `42f43cb` (code HEAD `094fe97`)
**Status:** passed
**Re-verification:** No. This is the initial verification.

All evidence below was re-measured by the verifier. None of it is taken from the SUMMARY files. The full suite was not re-run. The orchestrator's gate at `094fe97` was 3071 passed, 4 skipped, 0 failed.

## Roadmap Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Adversarial arm gets replay through a seam split from `is_dp`. The CPU run logs replay count == PREREG-04. DP arms and golden trajectory are byte-unchanged. (ARECIPE-01) | VERIFIED | `teach_persona.py:1771-1772`: `is_dp = arm in DP_ARMS` and `gets_replay = arm in DP_ARMS + REPLAY_ARMS`. The single `dp_kwargs` dict is gated on `gets_replay`, with `fact_bin`/`n_facts` gated per entry on `is_dp`. `test_advr_draws_the_prereg_replay_count[advr_n8, advr_n64]` runs the real `train()` with `on_draw` and asserts 32 and 256 replay windows per step. `test_train_kwargs_equal_the_presplit_fixture` passes for dp_n8, dp_n64, adv_n8 and adv_n64 against a fixture from `47ed88b`, which is a strict ancestor of the split `e957832`. `git diff a9d0d5d HEAD -- src/ tests/fixtures/golden_trajectory_v1.json` is empty. The golden tests (`test_loop_penalty_fn.py`, `test_phase22_dpsgd.py`) are unmodified. |
| 2 | The calibration is re-derived at the replay-bearing recipe and committed before any scored point. Scoring refuses a recipe that differs from the calibration's. (ARECIPE-02) | VERIFIED | `results/phase30_calibration.json` was committed alone in `4339f2b` and is the only tracked `results/phase3*` file. It has `derived_floor` 15 and `bins_identical_advr_vs_adv: true`. Its module_sha256 values match HEAD bytes for all 5 pinned modules. `require_calibrated_recipe` accepts `recipe_identity(n8/n64)` against the tracked record and refuses a perturbed `replay_windows` (verifier scratch check). Ancestry tests `test_ancestry_calibration_precedes_every_later_v5_result` and `test_ancestry_emitter_is_frozen_before_the_calibration` are green. |
| 3 | Floors, `control_gap` and relearning Z come only from the own ratio-0 advr control at identical budget and seed. A test feeding a DP-sourced reading is refused. (ACTRL-01) | VERIFIED | `phase30_points.own_control` takes its key only from `phase29_prereg.control_key(leg)` and reads the record only if it is tracked. It checks point_key, arm, `axis == "ratio"` and null q/clip_norm, then does a read-time recipe equality check (D-16). `control_floors`, `control_dialogue_pair` and `control_baseline` all go through it. `test_wr05_refuses_a_relabelled_dp_record` uses the real `results/phase25_point_dp_n8_sigma0p000000.json`. The AST guard with planted RED per class is green. The verifier also checked that `own_control("dp_n8_sigma0p000000", ...)` is refused. |
| 4 | The schedule runs the ratio-0 control first at n=8 and n=64, and a test reddens if any other point precedes it. (ACTRL-02) | VERIFIED | `SWEEP_SCHEDULE()` is derived from `POINT_KEYS()` plus `control_key()`, and `prove_controls_first` enforces a permutation with both controls at the head. `test_schedule_refuses_a_non_control_before_a_control` is green. In a verifier scratch check, swapping position 1 and 2 raised SystemExit. |

## Plan Must-Haves

| Plan | Truths | Status | Notes |
|------|--------|--------|-------|
| 30-01 | 7 (D-01..D-04, guard order, goldens untouched) | 7/7 VERIFIED | `REPLAY_ARMS` = `("advr_n8","advr_n64")`. `arm_spec(advr_x)` calls `arm_spec(adv_x)`. `ADV_ARMS` is not changed in the phase diff. `grad_accum_steps` count is 14. The replay-source guard (`:1835`) comes before bin building. The CLI refuses advr. `loop.py` and `src/` are untouched. |
| 30-02 | 8 (D-09, D-10, D-12..D-19) | 8/8 VERIFIED | Imports seed and max_steps from `phase25_points.SWEEP_SEED` and `mitigation_budget.STEP_BUDGET`, and proves `tp.SEED`/`tp.MAX_STEPS` equal them. `phase25_points.py` and `phase29_prereg.py` have an empty diff since `a9d0d5d`. `next_action` refuses an untracked control and short-circuits an unlearnable leg through `refused_record`. `write_refused_records` checks every target before it writes any. |
| 30-03 | 7 (D-05..D-11, write-once/dirty-first) | 7/7 VERIFIED | `derive()` builds in a `tempfile.TemporaryDirectory`, and `build_bins(` is called lazily. The D-08 `SystemExit` fires before any write. `descriptive_step_mix` has `gates_nothing: true`. |
| 30-04 | 4 (emit from clean tree, commit alone, mix, recipe) | 4/4 VERIFIED | Record provenance is `git_sha == head_at_write == 53a62b2`. `git diff 53a62b2 HEAD -- scripts src` is empty, so the pinned module hashes still hold. The D-08 approval and the v4.0-tag anchor ruling are quoted verbatim in the SUMMARY. |

## Deviations and Developer Rulings Checked

- **30-01 post-wave pin fix (option 3).** `results/phase24_token_budget.json` was re-emitted, with a provenance-only diff of 6 lines. `tests/test_phase27_relearn.py` received a dated continuation with a tripwire, and `results/phase27_admission.json` was not touched. This is consistent with the pin-correction discipline.
- **30-04 v4.0-tag anchor.** `test_paths_are_distinct_from_every_v4_path` now reads `git ls-tree -r --name-only v4.0 results`, and a dated docstring explains why. It is a legitimate re-anchor, not a weakening, because it still checks against 210 real v4.0 files.
- **Changes to existing tests.** The changes to `test_phase22_wiring.py` and `test_phase23_resume.py` are narrow and explained: advr is excluded from the plain-arm CLI control, and the call-site register was bumped from 16 to 17 with a stated reason.

## Behavioral Spot-Checks (verifier-run)

| Behavior | Result | Status |
|----------|--------|--------|
| `pytest test_phase30_seam, test_phase30_points, test_phase30_calibration, test_phase29_prereg` | 131 passed in 33.6 s, and the tree was clean afterwards | PASS |
| D-03 fixture non-vacuity: route adv_n8 through the replay dict, then compare to the fixture | differs, so the check bites | PASS |
| Swap schedule positions 1 and 2, then `prove_controls_first` | SystemExit | PASS |
| `require_calibrated_recipe` against the TRACKED record: live recipe accepted, perturbed recipe refused (both legs) | as expected | PASS |
| `own_control` with the own control untracked, or with a dp key | SystemExit in both cases | PASS |
| sha256 of the 5 pinned modules vs the record's `module_sha256` | all 5 equal | PASS |
| `ruff check` on the phase files | clean | PASS |

## Requirements Coverage

| Req | Plans | Ruling | Evidence |
|-----|-------|--------|----------|
| ARECIPE-01 | 30-01 | Fully satisfied by this phase | SC1 above |
| ARECIPE-02 | 30-02, 30-03, 30-04 | Fully satisfied by this phase | The calibration is committed as the first v5.0 result. The refusal function exists, and every driver path calls it (`next_action` and `own_control`). Phase 32's scorer must route through it. The ancestry guard already forbids a later v5.0 result that does not descend from the calibration. |
| ACTRL-01 | 30-02 | Satisfied at the enforcement level, which is everything Phase 30 can deliver | The own-control reader, the WR-05 refusals and the AST guard are all in place. No advr control record has been trained yet, so the sole-source path is first used with real data in Phase 32 (floors, control_gap) and Phase 33 (relearning Z). Neither phase re-lists ACTRL-01. |
| ACTRL-02 | 30-02 | Fully satisfied by this phase | SC4 above |

No orphaned requirements. REQUIREMENTS.md maps exactly these 4 IDs to Phase 30. Nothing was ticked by the verifier.

## Anti-Patterns

There are no TBD, FIXME, XXX, TODO or HACK markers in `scripts/phase30_*.py`, `tests/test_phase30_*.py` or the lines this phase added to `teach_persona.py`. No stubs were found.

## Human Verification Required

None. The only human gate, the D-08 checkpoint, was already passed, and the developer's approval is recorded verbatim in 30-04-SUMMARY.

## Gaps Summary

No gaps. One informational note for Phase 32: its point scorer must call `phase30_points.require_calibrated_recipe` or `own_control`, and it must write the top-level `recipe` dict into every point record, because D-16 refuses a control that has no recipe. The Phase 32 pins in 30-02-SUMMARY already say this.

---

_Verified: 2026-09-25_
_Verifier: Claude (gsd-verifier)_
