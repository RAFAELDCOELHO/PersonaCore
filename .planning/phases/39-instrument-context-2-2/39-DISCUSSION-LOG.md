# Phase 39: Instrument × Context 2×2 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 39-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-04
**Phase:** 39-instrument-context-2-2
**Areas discussed:** Anchor generation, Full-question rank, Decomposition rule, Gate and run shape

Carried forward without asking (measured before the session): entries = 216 and a2_regenerated_entries = 0
(Rafael's budget approval and cap ruling 2026-10-02, results/phase36_budget.json); the 7 committed K = 48
A2 records exist with per-draw completions; E6 0.495 h with 8 candidates per slot priced.

---

## Gray areas offered
| Option | Selected |
|---|---|
| Anchor generation — prompt, hit, comparability of 1 x 48 vs 27 x 48 | ✓ |
| Full-question rank — reference set, aggregation of 27 per-question NLLs | ✓ |
| Decomposition rule — categorical per cell vs quantitative shares | ✓ |
| Gate and run shape — Phase 38 pattern, differences for E6 | ✓ |

**User's choice:** all four, answered in one reply (recorded as D-04..D-22 in 39-CONTEXT.md).
**Notes:** Rafael wrote "top-k" for the A2 sampling; the code (phase14_recall) uses top-p 0.95 at
temperature 0.8 — his rule "the same parameters as A2" resolves to top-p (recorded in D-05).

## Descriptive extras (asked to be priced before deciding)
Priced with the committed high unit prices (E6 formula reproduces front_hours.E6 0.4949481154825642):

| Option | Projection | Selected |
|---|---|---|
| (i) + (ii) at \|R\| 8 | 0.703 h <= stop (a) 0.742 h | ✓ |
| (i) only (adapter-off, A2 reused) | 0.566 h | |
| Neither | 0.495 h | |
| (ii) beyond \|R\| 8 | 1.175 h at <= 32 with (i): needs a stop ruling too | |

**User's choice:** "Opção 1: aprovo (i) adaptador desligado como oitavo adaptador e (ii) os conjuntos
cunhados da Fase 38 sob a pergunta inteira em |R| = 8 (D-09). approved" — plus the addendum that
|R| > 8 is not part of E6, recorded as not measured, and may run later only as a dated continuation after
E1-E4 (D-12).

## Claude's Discretion
- Module/record names, driver structure, test layout and plan order (Phase 38 split).

## Deferred Ideas
- Minted sets under the full question at |R| > 8 (D-12).
