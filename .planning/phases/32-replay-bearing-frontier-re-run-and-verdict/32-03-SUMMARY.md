---
phase: 32-replay-bearing-frontier-re-run-and-verdict
plan: 03
subsystem: v5.0 frontier assembler (scripts/phase32_frontier.py)
tags: [frontier, frozen-route, prereg-03, condition-c, templates, write-once, ast-gate]
requires: ["32-01"]
provides:
  - "build_frontier(records, v4_frontier, v4_sha256): pure, per-leg phase25_verdict.curve_verdicts against each leg's own advr control, admission self-check"
  - "condition_c_vs_v4(frontier, v4_frontier, v4_sha256): D-13/D-14 rows, by_leg summaries, v4_source, statement"
  - "TEMPLATES / statement(by_leg): D-15/D-18 fixed table over (v5_state, v4_state)"
  - "emit(out_path=FRONTIER_PATH): write-once, never commits; main(['emit', '--out', p])"
affects: [32-05, 32-06, 32-07, phase 33 admission, phase 34 report]
tech-stack:
  added: []
  patterns: [import the frozen route as module attributes, forged-from-committed-v4 fixtures, scratch results repo, both-states recompute/ancestry]
key-files:
  created:
    - scripts/phase32_frontier.py
    - tests/test_phase32_frontier.py
  modified: []
decisions:
  - "A non-floor SystemExit from curve_verdicts propagates wrapped in _prove (same as phase25_promotion.curve_pass), so its text ends with the original message; the test matches that suffix"
  - "Routed entries carry leg = 'advr_<leg>' (the v5 leg), not the v4 twin name; the twin is used only as the control_readings_by_arm key"
  - "calibration add-commit check is a local literal-argv copy of phase31_probe.calibration_descent, with cwd=_GIT_ROOT, so the scratch-repo test and the git-surface AST both see it"
  - "v4 condition_c_vs_v4 label on evaluated rows is '(c) passed' / '(c) failed' from cleared_c; not-evaluated rows read '(c) measured, not evaluated'"
requirements-completed: []
# This plan contributes to AFRONT-02 and AFRONT-03 (the assembler, comparison block and statement) but does not complete them; plan 07 emits the frontier from the real records.
metrics:
  duration: ~40 min
  completed: 2026-09-27
  tasks: 2
  files: 2
---

# Phase 32 Plan 03: v5.0 frontier assembler Summary

`scripts/phase32_frontier.py` assembles `results/phase32_frontier.json` from the 12 committed point records. Verdicts come only from `phase25_verdict.curve_verdicts`, called per leg with readings built from each leg's own advr control. The D-13/D-14 `condition_c_vs_v4` block sits beside the committed v4.0 frontier, which is pinned by the sha256 of its HEAD blob. The D-15/D-18 statement is picked from a fixed table and bound from counts. Emit is write-once and never commits. Everything is tested on records forged from the committed v4.0 frontier. Nothing was written under results/.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 RED | `37a4dd5` | tests/test_phase32_frontier.py |
| 1 GREEN | `b9ca09a` | scripts/phase32_frontier.py, tests/test_phase32_frontier.py (lint + two test fixes, see Deviations) |
| 2 RED | `963f9b3` | tests/test_phase32_frontier.py |
| 2 GREEN | `04b0b09` | scripts/phase32_frontier.py |

## TEMPLATES, verbatim (for the D-16 checkpoint)

Every sentence is `_V5_CLAUSES[v5_state] + _V4_CLAUSES[v4_state]`:

- `("measured", "evaluated")`: At {leg}, with replay, (c) passes at {k5} of 5 non-control ratios, and at {k6} of 6 counting the ratio-0 control, whose dialogue half passes by self-reference (the control_gap is its own gap); in v4.0, without replay, (c) passed at {v4_k} of {v4_n_evaluated} at {twin}.
- `("measured", "not_evaluated")`: At {leg}, with replay, (c) passes at {k5} of 5 non-control ratios, and at {k6} of 6 counting the ratio-0 control, whose dialogue half passes by self-reference (the control_gap is its own gap); in v4.0, (c) was measured but not evaluated at any of 6 ratios at {twin}: the route refused on the control's recall floors (taught {v4_tk}/{v4_tn}, held-out {v4_hk}/{v4_hn}).
- `("refused_by_route", "evaluated")`: At {leg}, with replay, (c) was not evaluated: the sanctioned route refused every point before the pin was reached (own control taught {tk}/{tn}, held-out {hk}/{hn}); in v4.0, without replay, (c) passed at {v4_k} of {v4_n_evaluated} at {twin}.
- `("refused_by_route", "not_evaluated")`: At {leg}, with replay, (c) was not evaluated: the sanctioned route refused every point before the pin was reached (own control taught {tk}/{tn}, held-out {hk}/{hn}); in v4.0, (c) was measured but not evaluated at any of 6 ratios at {twin}: the route refused on the control's recall floors (taught {v4_tk}/{v4_tn}, held-out {v4_hk}/{v4_hn}).
- `("refused_prereg03", "evaluated")`: At {leg}, the v5.0 leg is REFUSED under PREREG-03: its own control read taught {tk}/{tn} and held-out {hk}/{hn}, which puts the recall floors outside (0,1], and it was not re-tuned, so (c) with replay was not evaluated; in v4.0, without replay, (c) passed at {v4_k} of {v4_n_evaluated} at {twin}.
- `("refused_prereg03", "not_evaluated")`: At {leg}, the v5.0 leg is REFUSED under PREREG-03: its own control read taught {tk}/{tn} and held-out {hk}/{hn}, which puts the recall floors outside (0,1], and it was not re-tuned, so (c) with replay was not evaluated; in v4.0, (c) was measured but not evaluated at any of 6 ratios at {twin}: the route refused on the control's recall floors (taught {v4_tk}/{v4_tn}, held-out {v4_hk}/{v4_hn}).

Slots: leg = `advr_<leg>`, twin = the v4 leg name, k5/k6 = v5 cleared_c True counts, v4_k/v4_n_evaluated, tk/tn/hk/hn = the v5 control counts, v4_tk.. = v4 `verdicts.control_readings[twin].recall_counts`.

On the default forged input (n8 learnable, n64 unlearnable) the statement reads: "At advr_n8, with replay, (c) passes at 0 of 5 non-control ratios, and at 0 of 6 counting the ratio-0 control, ...; in v4.0, without replay, (c) passed at 0 of 6 at adv_n8. At advr_n64, the v5.0 leg is REFUSED under PREREG-03: its own control read taught 1/1008 and held-out 0/648, ...; in v4.0, (c) was measured but not evaluated at any of 6 ratios at adv_n64: the route refused on the control's recall floors (taught 1/1008, held-out 0/648)."

## Tests run

- tests/test_phase32_frontier.py: **23 passed** (8 Task 1, 15 Task 2), in about 4 s.
- Task 1 verify (`-k "build or route or prereg or tallies or ast"`: 8 passed) and the WR-05 guard (1 passed).
- Task 2 verify guards (WR-05, accountant, mitigation_point_verdict caller census): 3 passed.
- The census gate (10 tests) passed after Task 1 and after Task 2.
- Plan end, `tests/test_phase32_frontier.py tests/test_phase29_prereg.py tests/test_phase30_points.py tests/test_phase31_budget.py tests/test_phase32_points.py`: **189 passed**.
- Repo-wide census files (every `tests/*.py` matching `glob|rglob`, 53 files, run after 04b0b09): **1449 passed**, 0 failed, in 6 min 21 s. This includes `tests/test_phase32_points.py::test_census_gates_over_the_v5_driver` and `test_git_surface_is_bounded`, whose `scripts/phase32_*.py` glob now covers the new module.
- `grep -Ec '[0-9a-f]{64}'` prints 0 for both files. `git ls-files 'results/phase32_*'` prints nothing. The torch-free import check exits 0. ruff check and ruff format --check are clean.

## TDD gate compliance

Both tasks have a `test(...)` commit followed by a `feat(...)` commit. Task 1's RED was a collection error, because the module did not exist yet. Task 2's RED was 11 failing tests with 12 passing. The 12 that passed were the Task 1 tests plus the state-independent ones: v4 bytes, the recompute and ancestry untracked branches, and the cleared_abc KeyError premise.

## Deviations from Plan

- **Structural SystemExit match.** The plan says a non-floor SystemExit "propagates". The code copies `curve_pass`, which re-raises it through `_prove`, so the message is `[phase32_frontier] advr_n8: ... NOT the coverage route's floor refusal: structural`. The test matches that suffix rather than `^structural$`. The exit is still never recorded as a refusal. The fix is in b9ca09a.
- **Task 1's AST test did not require `ls-files`/`show` usage**, since emit is Task 2. That non-vacuity check lives in Task 2's `test_emit_never_commits_and_the_git_surface_is_read_only`. The fix is in b9ca09a.
- **Lint.** The RED commit 37a4dd5 had 3 E501 lines, which were fixed in b9ca09a. The Task 1 GREEN module temporarily carried `refuse_if_dirty` with `noqa: F401`, because the autouse recorder patches it. The noqa was removed in 04b0b09.
- **Calibration check written locally** instead of calling `phase31_probe.calibration_descent`, which reads phase31_probe's own `_GIT_ROOT`. It uses the same literal argv, with `cwd=_GIT_ROOT`.

## Plan-premise checks (measured)

- `git diff --quiet v4.0 HEAD -- results ':(exclude)results/phase24_token_budget.json' ':(exclude)results/phase3*'` gives rc 0, and the natural RED on `results/phase24_token_budget.json` gives rc 1. Both are as the plan states.
- `cleared_abc(<v4 point dict>)` raises `KeyError: 'point_extraction_successes'`, as the plan states. A test pins this.
- v4 facts confirmed: the adv_n8 rows are INCONCLUSIVE with cleared_c False and `(c)` reasons, and the adv_n64 rows have cleared_c None with reasons[0] equal to `leg_refusals.adv_n64`.
- **For the D-16 review (not a falsification):** on the forged input, the advr_n8 ratio-0 control's cleared_c is **False**. Its dialogue half passes by self-reference, but its retention half fails, because the v4 adv_n8 control's retention PPL is above the cap. So k6 is not automatically at least 1. The template says "whose dialogue half passes by self-reference", which stays accurate, but the reader should not infer that the control counts toward k6.
- No premise was falsified.

## Field check against 32-02's record key set

The frontier reads these fields: `taught_recall` and `heldout_recall` (`numerator`/`denominator`), `condition_c` (`point_dialogue_ppl_on`/`off`, `point_retention_ppl`, `control_gap`, `gap_noise_floor`, `retention_noise_floor`), `per_family_counts`, `zero_extraction_has_nll`, `draws_per_question` and `draws_per_question_source`. PREREG-03 records also supply `rule`, `control_key`, `control_recall_counts` and `point_key`. Every trained-record field is in the key set 32-02 shipped. `condition_c` is built by the same `phase25_record.condition_c_group` in v4 and v5, so its keys match. **No mismatch.** Plan 05 must still feed one real producer record through `build_frontier` to prove this end to end.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. T-32-10..15 are mitigated in code and tested.

## Self-Check: PASSED

- scripts/phase32_frontier.py and tests/test_phase32_frontier.py exist.
- Commits 37a4dd5, b9ca09a, 963f9b3 and 04b0b09 are present on main.
- No STATE, ROADMAP or REQUIREMENTS edits were made, and nothing was written under results/.
