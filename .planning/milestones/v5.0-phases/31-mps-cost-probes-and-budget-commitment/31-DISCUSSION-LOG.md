# Phase 31: MPS Cost Probes and Budget Commitment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-26
**Phase:** 31-mps-cost-probes-and-budget-commitment
**Areas discussed:** Probe point choice, Relearning probe, Budget formula + stakes, WR-03 + run mode

---

## Probe point choice

| Option | Description | Selected |
|--------|-------------|----------|
| advr_n64 control | The cost-dominant leg (256 replay windows); n8 derived from measured ratios | ✓ |
| Both controls | Probe n8 and n64 so nothing is extrapolated (two runs) | |
| advr_n8 control | Cheapest; n64 extrapolated from it | |

| Option | Description | Selected |
|--------|-------------|----------|
| Discard, isolated | Phase 23 precedent `sweep_point: false`; own prefix and sidecar/adapter; guard against reuse by train_stage | ✓ |
| Reuse as the control | Saves one run, but blurs "no sweep point before the budget" | |

| Option | Description | Selected |
|--------|-------------|----------|
| Time recall | Price taught-recall from the probe's own measurement | ✓ |
| Use Phase 25's figure | 1304.5 s/point from results/phase25_recall.json | |

## Relearning probe

| Option | Description | Selected |
|--------|-------------|----------|
| Measure anyway, price 0 | Run the probe (ARCAL-02 requires it); budget shows 0 h scheduled under D-15 plus the conditional cost | ✓ |
| Price it as if it runs | Add the full relearning cost to the committed total | |

| Option | Description | Selected |
|--------|-------------|----------|
| The probe's advr_n64 adapter | Replay-bearing recipe, real, isolated | ✓ |
| v4.0 adv_n64 adapter | Exists now, but the no-replay recipe and gitignored | |

| Option | Description | Selected |
|--------|-------------|----------|
| One arm, full ladder | One seed to RELEARN_CAP 400, 8 rungs at CURVE_K; budget multiplies by arm counts | ✓ |
| A whole sub-mode | e.g. the full curve leg; about 7× the cost | |

## Budget formula + stakes

| Option | Description | Selected |
|--------|-------------|----------|
| Resource record + stop line | Records hours; Phase 32 pauses at a checkpoint past a pre-committed ceiling | ✓ |
| Resource record only | Overruns only noted | |
| Go/no-go gate | Phase 32 cannot start past a limit without a scope ruling | |

| Option | Description | Selected |
|--------|-------------|----------|
| Per-stage × counts | Measured stages × point counts; n8 scaled; both D-12 branches priced | ✓ |
| Whole-point × 12 | One figure × 12 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 25 spread | Empirical range (~±20%) applied per stage | ✓ |
| Fixed ×1.5 | Conservative multiplier with no empirical basis | |
| None | Point estimate only | |

## WR-03 + run mode

| Option | Description | Selected |
|--------|-------------|----------|
| Fix WR-03 in Phase 31 | Edit teach_persona.py and extend both `_SUPERSEDED_PINS` registers | |
| Count via on_draw only | Probe counts replay draws itself; teach_persona.py untouched; WR-03 stays carried | ✓ |

**User's choice (verbatim):** "Confirma opção 2: a sonda conta sorteios de replay diretamente através do gancho on_draw já existente … teach_persona.py permanece intocado — preserva exatamente a garantia dupla que Unchanged proof já construiu para os braços DP e adv_* de v4.0. WR-03 continua carregado para Phase 32 como item nomeado, não resolvido aqui à custa de reabrir pins já congelados e editar módulo de produção protegido."

| Option | Description | Selected |
|--------|-------------|----------|
| LaunchAgent, unattended | Phase 25 plist + caffeinate -dims + heartbeat jsonl | ✓ |
| Interactive / nohup | Simpler; timings perturbable | |

**User's choice (verbatim):** "Confirma opção 1: reusa o padrão exato de Phase 25 — LaunchAgent + caffeinate -dims + heartbeat jsonl. Timings não distorcidos por sono ou carga interativa …"

| Option | Description | Selected |
|--------|-------------|----------|
| Upper range bound × 1.5 | Pause when the cumulative sweep passes 1.5× the upper bound of the range | ✓ |
| 2× point estimate | Round, generous ceiling | |
| Upper range bound | Tight | |

**User's choice (verbatim):** "Confirma opção 1: pausa quando o tempo cumulativo do sweep exceder 1,5× o limite superior da faixa já medida em Margin …"

## Claude's Discretion

- Probe prefix and sidecar/adapter naming (no collision with phase32/phase25 paths).
- How condition (c) runs for timing on a control without a control_gap.
- One LaunchAgent run or two (order fixed: point → relearn).
- Record schemas (within the required fields).

## Deferred Ideas

- WR-03, WR-04's replay-count cross-check, and IN-01..04 → Phase 32.
- Probing the n8 control directly (only if the n8 leg breaches the stop line).
