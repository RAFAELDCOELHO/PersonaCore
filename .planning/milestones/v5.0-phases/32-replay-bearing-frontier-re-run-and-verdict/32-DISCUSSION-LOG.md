# Phase 32: Replay-Bearing Frontier Re-run and Verdict - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-27
**Phase:** 32-replay-bearing-frontier-re-run-and-verdict
**Areas discussed:** Recall at the 10 non-control points, Stop line and run mode, Carried review debt, Verdict statement (AFRONT-03), plus two follow-ups (point commits, pre-flight)

**Two premises in Claude's options were corrected during the discussion, each after the developer rejected a question batch and asked for the options to be re-sent:**
1. A "which recall instrument" question was withdrawn. `phase25_points.py:572` and `phase25_recall.py:159` both call `teach_persona.score_arm`, so the two options were the same instrument.
2. An option saying v4.0's adv_n64 pairs had "no (c) reading" was corrected. `results/phase25_frontier.json` carries measured `condition_c` for all six points; the route refused before evaluating them (control recall floors Y_taught = 0.00069, Y_heldout = 0.0). The n8 points are INCONCLUSIVE with (c) FAIL reasons, not FAIL.

---

## Recall at the 10 non-control points

| Option | Description | Selected |
|--------|-------------|----------|
| Inline in the driver's measure stage | Override `measure_stage` without editing `phase25_points.py`; every record born with its own recall | ✓ |
| Separate post-sweep pass | A 25-18-style `phase32_recall.json` pinned to adapter shas | |

**User's choice:** Inline (recommended).

## Stop line and run mode

| Question | Options | Selected |
|----------|---------|----------|
| What the clock counts | Sum of per-stage seconds of completed points / Wall-clock since first launch | Sum of per-stage seconds |
| When the driver checks | Before each point, on the cumulative total / Before each point, with a prediction | On the cumulative total |
| Run mode | One agent for all 12 / One agent per leg | One agent |
| At the line | Clean exit, continuing needs a flag with a ruling / Clean exit, relaunch continues | Flag with a ruling |

**User's notes (clock):** "Confirma opção 1: relógio acumulado = soma dos tempos por etapa já registrados nos pontos concluídos — mesma unidade que Phase 31 mediu para produzir o orçamento. Tempo parado por crash, reboot ou pausa nunca conta, e o número é reproduzível a partir dos registros commitados por qualquer observador, a qualquer momento — mesma disciplina de "número publicado sempre recomputável" que já protegeu cada tripwire sério desta sessão."

## Carried review debt

| Question | Options | Selected |
|----------|---------|----------|
| WR-03 (replay proof) | Count via on_draw in the driver / Fix teach_persona.py now | on_draw |
| WR-02 (pinned code == run sha) | Refuse at write time / Check by hand at close | Refuse at write time |
| WR-01 and IN-01..04 | WR-01 → Phase 33, IN-* only where touched / Close every IN-* now | WR-01 → 33, IN-* where touched |

**User's notes (WR-01/IN-*):** "Confirma opção 1: WR-01 muda de dono para Phase 33 — não porque o código seja compartilhado (já confirmei que relearn_out_dir() é exclusivo da sonda encerrada), mas porque a CLASSE de problema (onde artefatos de reaprendizado devem viver para não bloquear refuse_if_dirty) é lição transferível que Phase 33 vai precisar resolver de novo ao implementar seu próprio mecanismo real. Dos IN-01..04, corrige só os que o driver de Phase 32 genuinamente toca (ex.: IN-04 se recipe_identity for usado) — o resto registrado como carregado, mesma proporcionalidade de "nunca corrige código sem consumidor real" já aplicada em Review fixes/Phase 29."

## Verdict statement (AFRONT-03)

| Question | Options | Selected |
|----------|---------|----------|
| Where | Block in phase32_frontier.json / Phase 34 report only | Frontier block |
| v4.0 side of the n64 pairs | "(c) measured, not evaluated" + reason / Only "REFUSED" + reason | Measured, not evaluated |
| How the statement is written | Derived from counts / Written by the developer at review | Derived from counts |
| Review before commit | Checkpoint before commit / Commit directly if guards pass | Checkpoint |

## Follow-ups

| Question | Options | Selected |
|----------|---------|----------|
| When point records are committed | Driver commits each point during the run / Sidecars during the run, emit afterwards | Driver commits each point |
| Pre-flight proof before the ~23 h launch | CPU live path through the frontier and admission() / Point live path only | Through the frontier |

## Claude's Discretion

- Driver and plist names, the continue-past-the-stop-line flag shape, and the D-15 template sentences (every state enumerated and tested).

## Deferred Ideas

- WR-01 → Phase 33; untouched IN-* carried; a WR-03 fix in teach_persona.py stays a named item.
