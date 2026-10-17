---
phase: 42-dp-sgd-recipe-search-at-large
plan: 09
subsystem: e3-stage1-commit
tags: [phase42, e3, stage-1, d-12, d-18, d-19, d-22, recipe-01, recipe-03]
requires: [42-08]
provides:
  - "ledger/v6_mps_ledger.jsonl stage-1 lines, committed alone (ecf4c5f)"
  - "results/phase42_control_lr3e-04_t800.json (0f1c29e), results/phase42_control_lr1e-03_t200.json (a97a244), results/phase42_control_lr1e-03_t800.json (3a6de8e)"
  - "scripts/phase42_threshold_prereg.py + tests/test_phase42_threshold_prereg.py (0122510): e3_recall_threshold filled from the committed controls"
affects: [42-10]
tech-stack:
  added: []
  patterns: ["one record per commit, explicit paths, ordering tests after each"]
key-files:
  created:
    - scripts/phase42_threshold_prereg.py
    - tests/test_phase42_threshold_prereg.py
  modified:
    - ledger/v6_mps_ledger.jsonl
decisions:
  - "Rafael approved the five commits after the Task 1 checkpoint (his reply in the session on 2026-10-17; Claude did not write it anywhere)"
  - "e3_recall_threshold reads only the three controls and the v4.0 control; the budget is not one of its inputs (deviation 1)"
requirements-completed: []
metrics:
  completed: 2026-10-17
---

# Phase 42 Plan 09: stage-1 records and the recall threshold, committed Summary

The ledger, the three sigma = 0 control records and Phase 42's second fill file are committed in the order listed in advance, under Rafael's one approved. The recall threshold is now in writing, filled from committed controls, before any noised point exists. The full suite is green on the committed tree.

Requirements are contributed to, not closed, by this plan; the orchestrator owns traceability.

## Task 1: checkpoint (orchestrator)

Shown to Rafael from the files (values in 42-08-SUMMARY, re-read from the records):
- ledger report: no open run, E3 spent 5657.04 s;
- the three controls: train_config equal to `expected_train_config`, clip 0, mps, launch SHA f1cb634; taught/held-out 954/1008 & 386/648, 959/1008 & 488/648, 983/1008 & 411/648;
- the reused v4.0 control `results/phase25_point_dp_n8_sigma0p000000.json`: sha256 `0c23f6c11bb25aa53a4b01548c923668119d005bae5e0aa8d6e4e9f6bdcc76ed`, equal to `git show v5.0:<path>`;
- the threshold table below; `exact_disagreements` empty on both legs of all four recipes; no REFUSED recipe, so D-18 does not arise;
- the five-commit list.

Rafael's reply, verbatim (provenance: his message in the session; v6.0 replies may be claude.ai drafts he adopted): "approved

Os 5 commits do estágio 1 da Fase 42, nessa ordem e sem nada entre eles: o ledger sozinho; os 3 registros de controle, um por commit; e por último scripts/phase42_threshold_prereg.py com tests/test_phase42_threshold_prereg.py, o limiar preenchido por phase35_prereg.fill sem nenhum número digitado. Depois, a suíte completa na árvore commitada. O estágio 2 espera outro approved."

## Task 2: the five commits

`git log --format='%h %s' -6`, nothing between them:

| # | sha | content | checks after it |
|---|---|---|---|
| 1 | ecf4c5f | `ledger/v6_mps_ledger.jsonl` alone | test_phase36_ledger 45 passed |
| 2 | 0f1c29e | `results/phase42_control_lr3e-04_t800.json` | ledger 45 passed; test_phase35_prereg -k slot_ordering 3 passed; test_phase42_prereg -k "frozen or first_added" 2 passed |
| 3 | a97a244 | `results/phase42_control_lr1e-03_t200.json` | same three, green |
| 4 | 3a6de8e | `results/phase42_control_lr1e-03_t800.json` | same three, green |
| 5 | 0122510 | `scripts/phase42_threshold_prereg.py` + `tests/test_phase42_threshold_prereg.py` | step-5 set 228 passed; ledger 45 passed; ruff clean |

Record paths were resolved with `phase42_prereg.unit_record(u)` in CONTROL_UNITS order and equal files_modified.

Steps 1-2 were run by the orchestrator; steps 3-5 by a gsd-executor, checked by the orchestrator (commit stat, the fill file's imports and single binding, `_DECLARED_DISAGREEMENTS`, `scripts/phase35_prereg.py:1843`).

The fill file holds only `E3_RECALL_THRESHOLD = phase35_prereg.fill("e3_recall_threshold", **phase42_prereg.threshold_fill_inputs())` after the sys.path prepend; imports pathlib, sys, phase35_prereg, phase42_prereg. Natural RED before its commit: the three ordering tests failed (no git history yet), 225 passed; after the commit all green.

Acceptance print from the committed fill file:

| recipe key (lr, T, batch, seed) | control | taught | held-out |
|---|---|---|---|
| (0.0003, 200, 8, 1337) | results/phase25_point_dp_n8_sigma0p000000.json | 0.5486111111111112 | 0.3737654320987654 |
| (0.0003, 800, 8, 1337) | results/phase42_control_lr3e-04_t800.json | 0.6625 | 0.4169753086419753 |
| (0.001, 200, 8, 1337) | results/phase42_control_lr1e-03_t200.json | 0.6659722222222222 | 0.5271604938271605 |
| (0.001, 800, 8, 1337) | results/phase42_control_lr1e-03_t800.json | 0.6826388888888888 | 0.4439814814814815 |

Exact disagreements, pinned as `_DECLARED_DISAGREEMENTS`: `[]` on taught and held-out for all four recipe tags.

## Task 3: full suite

At HEAD `0122510`, fresh log `scratchpad/suite42_09_1.log`: `4814 passed, 4 skipped, 83 warnings in 4116.43s (1:08:36)`, `EXIT=0`. Last green run (42-06 at 28c7fda): 4802 passed, 4 skipped; +12 are the new test file's tests; skips unchanged. No latent red, no test fix commit.

## Deviations

1. The plan's third must-have names "the budget" among the threshold's declared inputs. `phase35_prereg.SLOTS["e3_recall_threshold"]["input_records"]` is `("results/phase42_control_*.json", _V4_CONTROL_RECORD)` (scripts/phase35_prereg.py:1839-1843) and `threshold_fill_inputs()` consumes only those four records (scripts/phase42_prereg.py:907-937). The test checks those four and asserts the set equals what Phase 35 leg (b) reads. The budget is an input of e3_grid_subset.
2. Plants adapted to this phase: the imports plant adds `import phase29_prereg`; the slot-census plant puts the fill source alone at `scripts/phase41_threshold_prereg.py` and expects an "outside its owner" failure.
3. Section (i) has a non-vacuity leg: a threshold moved to value + 1 must disagree at k = n.
4. The (d) probe plants four paths (checkpoints/, data/, .pt, .safetensors), as tests/test_phase42_prereg.py's probe does.
5. `_opens_a_checkpoint` and `_phase42_records` are imported from tests/test_phase42_prereg.py alongside `_strictly_before` / `_first_add`.

## Next

Plan 10: stage 2, the eight noised points on MPS, behind a new approved from Rafael.

## Self-Check: PASSED

Commit shas from `git log`; thresholds from the committed fill file; suite line from the log tail.
