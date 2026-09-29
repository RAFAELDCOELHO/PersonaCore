---
phase: 32-replay-bearing-frontier-re-run-and-verdict
plan: 05
subsystem: D-12 live-path proof of the v5.0 sweep driver and its consumers (tests/test_phase32_live.py)
tags: [live-path, d-12, e2e, prereg-03, frontier, admission, scratch-repo, fixture-scale]
requires: ["32-03", "32-04"]
provides:
  - "tests/test_phase32_live.py: a module-scoped CPU fixture that runs phase32_points.main(['run', '--heartbeat', p]) over all 12 keys into a scratch results repo, followed by 10 tests over the committed producer records and their consumers"
affects: [32-06, 32-07]
tech-stack:
  added: []
  patterns: [main-driven live fixture with no stage recorder, forcing scoped by exact adapter file name, natural RED pinned for every consumer-side patch, producer records read back as committed blobs]
key-files:
  created:
    - tests/test_phase32_live.py
  modified: []
decisions:
  - "Consumer patch 1 (measured necessary): the never-taught anchor's control_extraction_questions is scaled from 416 to the fixture's 4 questions per point, and the count is derived from the records. Without it the frozen tolerance_report raises ValueError. A natural-RED test pins the unpatched refusal"
  - "Second forced reading (measured necessary, deviation): the advr_n8 control's adapter_on becomes adapter_off + |real gap|. At fixture scale its real gap is -0.0021827830473739596, and the frozen dialogue_gap_band raises ValueError. The forcing is scoped to the n8 control's adapter by exact file name, and the test asserts the real gap was <= 0 on every run"
  - "No defect found in scripts/phase32_points.py or scripts/phase32_frontier.py; neither file was touched"
requirements-completed: []
# This plan contributes to AFRONT-01/02/03 (the live-path proof that gates the plan-06 launch) but completes none of them; the real sweep (06) and the frontier emit (07) do.
metrics:
  duration: ~45 min
  completed: 2026-09-27
  tasks: 2
  files: 1
---

# Phase 32 Plan 05: D-12 live-path proof Summary

The real v5.0 driver now runs end to end at CPU fixture scale in about 65 s. The run enters through `phase32_points.main(["run", "--heartbeat", …])` and goes over all 12 keys into a scratch git repo. It uses the real train (replay counted through `on_draw`), the real measure with recall, the real draws, score, write and one-path commit, and the real PREREG-03 refused leg. Then the 12 committed producer blobs go into `phase32_frontier.build_frontier` alongside the real committed v4.0 frontier, and from there into `phase29_prereg.admission()`, which returns **MOOT**. The consumer refused the real records twice. Both refusals come from fixture scale and neither is a driver defect. Each one is handled by a patch whose necessity a test re-measures.

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 | `77d3af3` | tests/test_phase32_live.py (fixture + tests a-g) |
| 2 | `d2c1a04` | tests/test_phase32_live.py (consumer half, natural RED, negative control, the two fixture-scale patches) |

No `fix(32-05)` commit was made, because no defect in scripts/ was found.

## main → run → run_point kwarg trace (read, then confirmed on the records)

- `main(["run", "--heartbeat", str(root/"heartbeat.jsonl")])` parses and then calls `run(heartbeat_path=pathlib.Path(args.heartbeat), past_stop_line=args.past_stop_line)`, where `past_stop_line` is None.
- `run` calls `run_point(act["plan"], tracked, heartbeat_path=heartbeat_path, stop_line={"seconds": line, "cumulative_before_point": clock, "past_line_ruling": past_stop_line})`.
- These were confirmed on the committed records and the heartbeat. Every trained record has `provenance.stop_line.seconds == 1e9`, which is the forged committed budget read through `stop_line_seconds`. It also has `past_line_ruling is None`. The last heartbeat line at the passed path is `"done"`. `refuse_if_dirty` was reached 8 times, once in `run()` and once in each of the 7 `write_point_record` calls. It was recorded, not bypassed.

## Scratch commits (oldest first, each with its single path)

```
83252f1d ['.gitignore']                                           (_scratch_repo base)
c6814a76 ['results/phase30_calibration.json', 'results/phase31_budget.json']  (fixture setup)
78258de0 ['results/phase32_point_advr_n8_ratio0p000000.json']     n8 control   (D-17: first)
bfc57638 ['results/phase32_point_advr_n64_ratio0p000000.json']    n64 control  (D-17: second)
b0c09212 ['results/phase32_point_advr_n8_ratio0p250000.json']
f5a18497 ['results/phase32_point_advr_n8_ratio0p500000.json']
d92d0673 ['results/phase32_point_advr_n8_ratio1p000000.json']
67f27875 ['results/phase32_point_advr_n8_ratio1p500000.json']
29d56354 ['results/phase32_point_advr_n8_ratio1p909091.json']
b9b370c1 ['results/phase32_point_advr_n64_ratio0p250000.json']    PREREG-03
e341b085 ['results/phase32_point_advr_n64_ratio0p500000.json']    PREREG-03
94639aa3 ['results/phase32_point_advr_n64_ratio1p000000.json']    PREREG-03
e4b52884 ['results/phase32_point_advr_n64_ratio1p500000.json']    PREREG-03
18d89562 ['results/phase32_point_advr_n64_ratio1p909091.json']    PREREG-03
```

The hashes are from one diagnostic run and vary per run. The structure is what the tests assert.

## What the consumers returned on the real records

`phase29_prereg.admission(frontier)`, verbatim:

```json
{"verdict": "MOOT", "reasons": ["0 of 12 points PASS; tallies {'PASS': 0, 'FAIL': 0, 'INCONCLUSIVE': 6, 'REFUSED': 6}", "advr_n64 fully REFUSED (advr_n64 control recall taught 0/1008, heldout 0/648); MOOT does not extend to that capacity", "MOOT: no measured point cleared the frontier — nothing to relearn"], "admitted_point_keys": [], "control_readings": {"n8": {"taught": [504, 1008], "heldout": [324, 648]}, "n64": {"taught": [0, 1008], "heldout": [0, 648]}}}
```

- n8 leg: all 6 points are INCONCLUSIVE through the frozen route. Each `control_taught_recall` is 504/1008, the forced k = n // 2, which proves WR-05 own-sourcing.
- n64 control: REFUSED, with `early_return_reason` = "REFUSED by the sanctioned route before the pin was reached" and every `COVERAGE_FLOOR_REFUSAL_MARKERS` member in reasons[0]. Its natural reading is taught 0/1008 and held-out 0/648.
- The other 5 n64 points are PREREG-03 records with `control_recall_counts` equal to the n64 control's counts.
- `condition_c_vs_v4` has 12 rows. by_leg n8 is ("measured", "evaluated") with k5 0 and k6 0. by_leg n64 is ("refused_prereg03", "not_evaluated"). The statement equals the TEMPLATES reconstruction:
  "At advr_n8, with replay, (c) passes at 0 of 5 non-control ratios, and at 0 of 6 counting the ratio-0 control, …; in v4.0, without replay, (c) passed at 0 of 6 at adv_n8. At advr_n64, the v5.0 leg is REFUSED under PREREG-03: its own control read taught 0/1008 and held-out 0/648, …; in v4.0, (c) was measured but not evaluated at any of 6 ratios at adv_n64: the route refused on the control's recall floors (taught 1/1008, held-out 0/648)."
- Negative control: flipping one `tallies_by_leg["advr_n8"]` count makes admission return INCONCLUSIVE.

## Findings: the consumer refused the real producer records (fixture scale, not driver defects)

1. **Extraction question count.** `build_frontier` → `curve_verdicts` → `corrected_point_verdict` → `mitigation_point_verdict` → `tolerance_report` raised `ValueError: ceiling 0.006461685297443485 sits below wilson_upper_bound(0, 4) = 0.4034786252027047`. The ceiling is built from the committed never-taught anchor, 0/416 questions, and the fixture's one-prompt-per-cell corpus gives 4 questions per point. The real sweep uses the full corpus, and every v4.0 point has 416 questions, so the production path is not affected. The test fix is to scale the anchor's `control_extraction_questions` to the fixture's count, which is derived from the records. `test_live_path_frontier_refuses_fixture_scale_without_the_anchor_patch` pins the unpatched ValueError.
2. **Sign of the control gap.** With finding 1 patched, `dialogue_gap_band` raised `ValueError: control_gap -0.0021827830473739596 is not positive`. On the fixture's random-init base, any adapter lowers the dialogue perplexity. I first tried an alternative that forces nothing: a one-token replay corpus. It made the gap more negative (-0.0067), so I reverted it. The fix is to force the n8 control's `adapter_on` to `adapter_off + |gap|`, scoped to the n8 control's adapter by exact file name. The adapter is identified from the `load_adapted_model` call that precedes the reading, and `adapter_off` stays real. The test asserts that the real gap was <= 0 and that exactly one adapter was forced. Non-control gaps still come from the committed control record, through `own_control` at write time (ACTRL-01 evidence, test d).
   - **Residual production risk (not measured, flagged for 32-06/32-07):** if the real MPS advr_n8 control's gap comes out <= 0 with replay, `build_frontier` will raise ValueError at emit time. That is a loud crash, not a recorded refusal. The only real replay reading so far is the n64 probe (`results/phase31_probe_point.json`: on 4.7575 against off 4.5733, gap +0.184). n8 with replay has not been measured. Deciding how such a control should be recorded is a pre-registration question and was not handled here.

Neither finding touched `scripts/phase32_points.py` or `scripts/phase32_frontier.py`.

## Plan-premise checks

- **Falsified: "the patches the assembler needs (none expected beyond read-only real files)".** The assembler needed two fixture-scale adaptations, described in the findings above.
- **Falsified in part: "The fixture forces exactly one control learnable … the advr_n8 control's taught/held-out counts."** Still exactly one control is forced, but it now carries two forced readings: the recall counts and the dialogue `adapter_on`.
- **Holds:** 32-04 warned that patching `teach_persona._REPO_ROOT` breaks `recipe_identity`. That does not bite here. `_e2e_env` re-roots `DIALOG_TRAIN_BIN`/`DIALOG_TRAIN_MASK` under the same root as `_REPO_ROOT`, so `replay_source` stays `data/dialog_train.bin`, and the scratch calibration matches.
- **Holds:** `mitigation_budget.STEP_BUDGET` is read at call time by `recipe_identity`, `pinned_mechanism` and `own_control` (grep plus the green run). Nothing caches it, so no cache patch was needed.
- **Holds:** the RESEARCH estimate of ~13 s per point. The measured times are ~9-12 s per trained point, with recall 6.5 s dominating. The whole fixture takes 64.5 s.

## Tests run

- `tests/test_phase32_live.py`: **10 passed**, 64-67 s wall for the module, including the one fixture run (64.5 s). That is under the 180 s acceptance line.
- Task 1 verify (`-k "live_path and not frontier"`): 7 passed in 64.3 s.
- Census gate (10 tests): passed after each commit (4.8 s).
- Plan end (`test_phase32_points`, `test_phase32_frontier`, `test_phase32_live`, `test_phase29_prereg`, `test_phase30_points`, `test_phase31_budget`): **223 passed** in 114.6 s.
- Raw-text gate `grep -Ec "train_arm\(|== 10" tests/test_phase32_live.py`: `0`.
- AST skip gate (count of `ast.Attribute` with attr skip/skipif): `tests/test_phase32_live.py 0` and `tests/test_phase26_canary.py 4`, the natural RED.
- ruff check and ruff format --check are clean.
- Census files plus the venue test, run after d2c1a04 (every `tests/test_*.py` matching `glob|rglob|plist`, 59 files including the new one, plus `tests/test_phase25_venue.py`): **1616 passed**, 0 failed, 0 skipped, in 30 min 24 s. That is 32-04's 1606 plus the 10 new tests. The venue skip pin is green.

## Skip-pin impact

None. The new file has no skip or skipif and no host-gated leg. It needs only committed files: the frozen tokenizer, `results/phase18_corpus.json`, `results/phase25_n64_matched_floor.json`, `results/phase23_never_taught.json` and `results/phase25_frontier.json`. No gitignored checkpoint, data bin or MPS is required. The M3/ubuntu skip split in `tests/test_phase25_venue.py` therefore does not move.

## Deviations from Plan

- **[Rule 3] Second forced reading and anchor scaling.** See the findings above. Both are scoped, both are re-measured on every run, and neither weakens an assertion.
- **Extra tests beyond (a)-(g) and the two consumer tests:** `test_live_path_frontier_refuses_fixture_scale_without_the_anchor_patch`, the natural RED for patch 1. Tests (b) and (f) also assert the forced dialogue scope, the 7 score calls and the 8 dirty-tree reaches.
- `phase32_frontier.refuse_if_dirty` is recorded by the autouse fixture, as the plan says. `phase32_points.refuse_if_dirty` is recorded again inside the module fixture, because a function-scoped autouse fixture is not active while a module-scoped fixture runs.

## Known Stubs

None.

## Threat Flags

None. T-32-22 is mitigated: the real-root `Path.glob` snapshot is identical before and after, and `git status` of the real tree is clean. T-32-23 is mitigated: entry is via main(), no stage recorder, records are read from the committed blobs, and they are fed to both consumers. T-32-24 is mitigated: both forcings match arm and exact adapter file name, the forced lists are asserted to be exactly the n8 control's single entry, and the n8 non-controls' recall is real (0/1008, 0/648).

## Self-Check: PASSED

- tests/test_phase32_live.py exists (472 lines, above the plan's 150 minimum).
- Commits 77d3af3 and d2c1a04 are present on main.
- No STATE, ROADMAP or REQUIREMENTS edits were made, and no gsd-sdk mutation handler was called.
- `git status` of the real tree after all runs shows only the pre-existing `.claude/scheduled_tasks.lock` deletion, which is not mine. There are no stray `data/phase32_*`, `data/phase25_advr_*`, `checkpoints/phase32_*`, `results/phase32_*` or `logs/phase32_*` files.
