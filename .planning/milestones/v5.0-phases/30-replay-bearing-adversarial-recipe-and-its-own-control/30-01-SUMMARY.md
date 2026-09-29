---
phase: 30-replay-bearing-adversarial-recipe-and-its-own-control
plan: 01
subsystem: training-driver (scripts/teach_persona.py)
tags: [ARECIPE-01, replay-seam, advr, D-01, D-02, D-03, D-04]
requires: [phase29_prereg.ADVR_ARMS, phase29_prereg.replay_windows, loop.train on_draw hook]
provides: [teach_persona.REPLAY_ARMS, advr_n8/advr_n64 arms, gets_replay gate, pre-split kwargs fixture]
affects: [30-02 calibration emitter, 30-03 driver, phase25_verdict (ADV_ARMS untouched)]
tech-stack:
  added: []
  patterns: [capture-and-stop train() spy, git-ancestry freeze of a fixture vs the change it guards]
key-files:
  created:
    - tests/test_phase30_seam.py
    - tests/fixtures/phase30_train_kwargs_presplit.json
  modified:
    - scripts/teach_persona.py
    - tests/test_phase22_wiring.py
    - tests/test_phase23_resume.py
decisions:
  - "gets_replay = arm in DP_ARMS + REPLAY_ARMS gates only the replay kwargs and the replay-source guard; is_dp keeps DPSGD, fact routing, lot size, cross-device refusal, provenance print"
  - "advr_* replay_windows computed from len(facts) (flat builds carry no stats['n_facts'])"
  - "REPLAY_ARMS is a literal in teach_persona (no phase29_prereg import); equality proven by test"
requirements-completed: []
metrics:
  duration: ~35 min
  completed: 2026-09-25
---

# Phase 30 Plan 01: Replay seam split for advr_* Summary

`advr_n8`/`advr_n64` now receive the train-time replay seam through a `gets_replay` gate split out of `is_dp`. They draw 32 and 256 replay windows per step, counted through `train()`'s `on_draw` hook. The `train()` kwargs for `dp_n8`, `dp_n64`, `adv_n8` and `adv_n64` still equal a fixture that was captured and committed before the split.

Requirement ticks: the orchestrator/verifier rules on ARECIPE-01; this plan marks nothing complete.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (D-03 fixture) | `47ed88b` | test(30-01): capture pre-split train() kwargs fixture (D-03) |
| 2 (split) | `e957832` | feat(30-01): split the is_dp gate; advr_* arms receive the replay seam |

Ancestry: `git log -S gets_replay --format=%h -- scripts/teach_persona.py` gives `e957832` only, and the fixture's sole commit `47ed88b` is its parent (strict ancestor). `test_the_presplit_fixture_predates_the_split` is now non-vacuous (HEAD carries `gets_replay`) and passes.

## Measurements

- The fixture was captured at `captured_at_sha: a9d0d5d…`. Arms: `adv_n64, adv_n8, dp_n64, dp_n8`. The dp entries carry `replay_windows` (32 / 256) and `grad_accum_steps` (8 / 64). The adv entries have no seam keys.
- Splat census (`ast.keyword` with `arg is None` inside `train_arm`): **3** at T1 `47ed88b` and **3** at HEAD `e957832`. Unchanged.
- `grep -c grad_accum_steps scripts/teach_persona.py`: **14** (the pinned count holds).
- `git diff 47ed88b --stat -- scripts/phase23_matched_prereg.py tests/test_phase23_matched_prereg.py src/ tests/test_loop_penalty_fn.py tests/test_masked_train_seam.py tests/test_phase22_dpsgd.py tests/test_phase21_aligned_bins.py tests/test_phase24_bins.py tests/fixtures/golden_trajectory_v1.json` is **empty**. loop.py, the frozen census and the goldens are untouched.
- D-04: `test_advr_draws_the_prereg_replay_count[advr_n8|advr_n64]` passes. `drawn["replay"] / MAX_STEPS == phase29_prereg.replay_windows(n)` (32, 256) and `drawn["teach"] == MAX_STEPS * BATCH_SIZE`.

## Test evidence

- Before the Task 1 commit: `pytest tests/test_phase30_seam.py -k train_kwargs_equal` gave **4 passed**, and `test_resume_from_none_is_inert` gave **1 passed**.
- After the Task 1 commit, the plan's verify (`tests/test_phase30_seam.py` + `test_resume_from_none_is_inert`) gave **6 passed**.
- Task 2 RED (natural): 11 failed, 4 passed. Every failure was `tp.REPLAY_ARMS` missing, reached through `_ratio_for` or through the arm tests. The 4 passes at RED were the CLI-refusal and guard tests, which passed vacuously. I then made both non-vacuous: the CLI test asserts `arm in tp.ARMS`, and the guard test matches `"replay-bearing arm"`, text that only the new message contains.
- Task 2 GREEN: `tests/test_phase30_seam.py` gave **15 passed**.
- Task 2 guard set (the plan's verify list plus `test_lora_inject.py` and `test_phase21_sc5.py`) gave **304 passed** in 86 s before the commit.
- After the commit, `tests/test_phase30_seam.py tests/test_phase23_resume.py` (whole file, clean-tree probe included) gave **24 passed**.
- `ruff check .` passed, and `ruff format --check .` reported 292 files already formatted.
- Extra related files (`test_phase25_probe2`, `test_phase25_verdict`, `test_phase22_accountant`, `test_phase22_reference`, `test_phase25_venue`, `test_phase21_filler`, `test_extra_eval_fns`): see the handback report.
- Full suite: NOT run by this executor (orchestrator rule). The orchestrator runs it after the wave.

## Deviations from Plan

1. **[Rule 1 - test honesty] Made two RED-vacuous tests non-vacuous.** `test_cli_refuses_the_replay_arms` passed before the split, because `main()` refused the unknown arm on USAGE, which also names `adversarial_ratio`. `test_replay_source_guard_fires_before_any_bin` also passed before the split, because `arm_spec` refused the unknown arm. I added `assert arm in tp.ARMS` to the first and matched the new guard wording `"replay-bearing arm"` in the second. Both were in commit `e957832`.
2. **Phase 29 import timing.** `phase29_prereg` was left out of the Task 1 file because nothing used it yet (ruff F401). Task 2 added it with its first use.
3. **Line reflow.** The USAGE line and the guard message were reflowed across string-literal lines to stay within 100 columns. No text changed, and no `train_arm(` prose was added (the register count is unchanged).

No plan premise was found false.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: tests/test_phase30_seam.py, tests/fixtures/phase30_train_kwargs_presplit.json
- FOUND commits: 47ed88b, e957832

## Post-wave fix (2026-09-25)

The orchestrator's full suite at f8959ea found 2 failures (3032 passed / 4 skipped / 2 failed). Both came from e957832 changing `scripts/teach_persona.py` (pin 3c1e6c55… -> live aabf4381…). Developer ruling "option 3" says to handle each record by its category:

- **ef5800a**: `results/phase24_token_budget.json` can be re-emitted. It was deleted at a clean tree and re-run through `scripts/phase24_record.py`, the route its guard prescribes (precedents aaea029, f968c39). A leaf walk over 538 leaves found 3 differences, all in provenance: `git_sha` 049a6bb -> f8959ea, `written_utc`, and `module_sha256[scripts/teach_persona.py]`. The canonical non-provenance sha256 is 24906743f7ef… both before and after.
- **0133df4**: `results/phase27_admission.json` is write-once (88dff77), so it was left byte-unchanged. `tests/test_phase27_relearn.py` now has a dated continuation (`_SUPERSEDED_PINS`, `_superseded`). The teach_persona.py mismatch is accepted only if two things hold: the pin hashes `git show e308675:scripts/teach_persona.py`, and `e308675..HEAD -- scripts/teach_persona.py` is exactly {e957832}. All other pins stay strict. A new tripwire test (`test_the_superseded_pin_continuation_is_a_tripwire`) shows that an extra SHA, a missing SHA, or a never-true pin each refuse. The behavioural evidence is `tests/fixtures/phase30_train_kwargs_presplit.json`.
- Checked before editing: no guard freezes `tests/test_phase27_relearn.py`. `scripts/phase27_relearn.py` only cites node ids, and those are unchanged. No file pins the phase24 record's bytes. Its consumers (phase25_points, phase25_extremes) read `rows`/`band_corners` only, and phase28 does not read it.
- Verification: 203 passed across test_phase24_record, test_phase27_relearn, test_phase27_prereg, test_phase25_extremes, test_phase28_ledger/report/prereg, test_phase30_seam and test_phase21_sc5. `ruff check` and `ruff format --check` are clean.
