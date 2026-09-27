---
phase: 31-mps-cost-probes-and-budget-commitment
plan: 06
subsystem: measurement
tags: [budget, arcal-03, stop-line]
requires: [31-05]
provides: [results/phase31_budget.json]
requirements-completed: []  # contributes to ARCAL-03; the orchestrator decides ticks at phase close
key-files:
  created: [results/phase31_budget.json]
  modified: [.planning/phases/31-mps-cost-probes-and-budget-commitment/31-VALIDATION.md]
completed: 2026-09-27
---

# Phase 31 Plan 06: ARCAL-03 budget and Phase 32 stop line — Summary

The budget was emitted once from the two committed probe records and the committed Phase 25 records. The developer reviewed it at the blocking checkpoint, and it was then committed alone at d22a017. The phase gate is green.

## Task 1 — emit and review (orchestrator, inline)

- The tree was clean for `scripts src results`, and both `results/phase31_probe_*` records were tracked.
- `.venv/bin/python scripts/phase31_budget.py` exited 0 and printed `stop line 37.77 h`.
- `relearning.scheduled_seconds == 0` and `stop_line.seconds == 1.5 × sweep.scheduled.high` hold. `tests/test_phase31_budget.py` passed 19 with the budget still untracked.

| Field | Value |
|-------|-------|
| `derived.per_window_seconds` | 0.010804 |
| `derived.ratios` medians (measure / recall / draw) | 1.0160 / 0.9326 / 0.9085 (6 pairs each) |
| `spread` draw / train / recall / measure | [0.755, 1.107] / [0.974, 1.141] / [0.879, 1.024] / [0.974, 1.059] |
| `per_point.n64` train/measure/recall/draw/score | 633 / 89 / 1079 / 5621 / 0.1 s → total 7423 s (2.06 h), 1.64–2.26 h |
| `per_point.n8` train/measure/recall/draw/score | 161 / 91 / 1007 / 5106 / 0.1 s → total 6365 s (1.77 h), 1.38–1.93 h |
| `sweep.branches` (n64,n8) L/L · U/L · L/U · U/U | 22.98 · 12.67 · 14.14 · 3.83 h |
| `sweep.scheduled` (all-learnable) | 22.98 h, 18.14–25.18 h (high 90,659.6 s) |
| `stop_line` | factor 1.5, 135,989.46 s = 37.77 h |
| `relearning.arm_seconds` | 43,455 s (12.07 h), 9.38–13.19 h |
| `relearning.full_k_rescore.per_point_seconds` | 4.23 h (3.23–4.66 h) upper bound |
| `relearning.conditional` (per leg, a = 1..5 admitted) | 88.7 / 105.0 / 121.3 / 137.6 / 153.9 h estimate |
| `reconciliation.phase25_sum_hours` | 12.56 h no recall, 15.88 h with recall, against the unsourced "~25-30 h" (25-HUMAN-UAT.md:49) |

## Task 2 — developer ruling (verbatim)

> approved — verifiquei a soma dos componentes por ponto (n64: 7422s=2,06h ✓; n8: 6365s=1,77h ✓) e a derivação do total da varredura (6×1,77+6×2,06=22,98h ✓) antes de aceitar. A discrepância de 17s na linha de parada rastreei como arredondamento de exibição (valor real ~25,1832h, mostrado como 25,18h), não erro. A comparação retroativa de custo de promoção (88,7-153,9h por perna) confirma D-15 da Phase 29 como decisão certa, não só prudente.

The budget was untracked when the checkpoint was answered. Before the commit, the file was re-read unchanged: stop line 135,989.458 s, scheduled high 25.18323 h.

## Task 3 — commit and phase gate

- `d22a017 data(31-06): commit the ARCAL-03 v5.0 budget and Phase 32 stop line`. `git show --name-only` lists exactly `results/phase31_budget.json`, and both 966f91b and 28338cd are its ancestors.
- Flipped guards (`test_phase31_budget`, `test_phase31_probe`, `test_phase29_prereg`, `test_phase30_calibration`, `test_phase30_points`): 172 passed.
- The tracked branches pass: `test_committed_budget_recomputes_from_committed_files`, `test_ancestry_budget_precedes_every_sweep_point` and `test_ancestry_probes_precede_the_budget`.
- `scripts/phase28_report.py check`: exit 0.
- Full suite at d22a017: EXIT=0, 3127 passed / 4 skipped / 0 failed in 1815 s.
- `git ls-files 'results/phase32_*'`: empty.
- 31-VALIDATION.md statuses were filled from these observations (a4f9b0a).

## Deviations

- Tasks 1–3 were run by the orchestrator inline, not by an executor agent. The plan is small and the checkpoint needs the review in this conversation.
