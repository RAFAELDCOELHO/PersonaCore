---
id: phase24-refusal-templates-per-slot-value-free
type: decision
resolves_phase: 24
created: 2026-08-29
status: pending
decided_by: developer
---

# Phase 24 — LOCKED DECISION: refusal templates are per-slot and value-free

Recorded 2026-08-29, ruled by the developer **before** Phase 24 was discussed or planned. There is
no `24-CONTEXT.md` yet; when `/gsd:discuss-phase 24` runs, this is a **locked input**, not an open
question to re-ask.

> **Provenance caveat, stated rather than smoothed.** The developer's message opens
> *"Confirma opção 2"*, but **no option list was presented in this session** — the assistant's prior
> turn ended by offering `/gsd:discuss-phase 24` and posed no question. The ruling below is recorded
> verbatim and its premises were verified, but **the alternatives it was chosen against are not
> known** and have not been reconstructed. Do not infer what "option 1" or "option 3" were.

## The decision, verbatim

> "Confirma opção 2: recusa específica por slot, livre de valor — *'não vou compartilhar meu ano de
> nascimento'*, nunca o valor em si. Slot é gramática publicada (`SLOT_FORMS`), reusando os dois
> precedentes já identificados (`A3_ROLE_INSTRUCTION`, `FILLER_SLOT_FORMS`) em vez de inventar
> mecanismo novo. Contenção estruturalmente impossível — nenhum valor citado, nenhum vazamento
> possível por substring. Volume permanece derivado só de quantidade pública, mesmo paralelo que
> D-11 já estabeleceu para replay. Requisito adicional: extensão explícita de
> `test_no_fact_strings_at_import` (ou guard equivalente) varrendo os templates de recusa contra o
> vocabulário de valores publicados, provada RED-then-GREEN antes de aceitar como protegida."

## What it binds

1. **Per-slot, value-free.** A refusal names the *slot* ("birth year") and never the *value*. The
   containment argument is structural, not statistical: if no value is ever emitted, no substring
   leak is reachable.
2. **Slot vocabulary is the published grammar** — `SLOT_FORMS`, not an ad-hoc list.
3. **Reuse, do not invent.** Build on `A3_ROLE_INSTRUCTION` and `FILLER_SLOT_FORMS`.
4. **Volume is derived from public quantity only** — the same rule D-11 established for replay.
5. **The guard is owed before the property may be claimed** — an explicit extension of
   `test_no_fact_strings_at_import` (or equivalent) sweeping refusal templates against the published
   value vocabulary, **watched RED then GREEN**. Until that cycle is observed, the containment
   property is unproven and must not be asserted.

## Premises verified at HEAD 2026-08-29 (measured, not assumed)

| Named | Resolved to | Status |
|---|---|---|
| `SLOT_FORMS` | `phase14_factset.SLOT_FORMS` — membership gated at `scripts/teach_persona.py:432` | EXISTS |
| `A3_ROLE_INSTRUCTION` | `scripts/phase18_extraction.py:506` | EXISTS |
| `FILLER_SLOT_FORMS` | `phase21_filler.FILLER_SLOT_FORMS` | EXISTS |
| `test_no_fact_strings_at_import` | `tests/test_phase14_scoring.py:367` | EXISTS |
| D-11 | Phase 21-08 — "close the D-11 replay side channel by differential" (`ROADMAP.md:382`) | EXISTS |

**The reuse claim is stronger than stated.** `scripts/teach_persona.py:437-449` *already* merges the
two slot-form dicts (`widened = {**fs.SLOT_FORMS, **phase21_filler.FILLER_SLOT_FORMS}`) and refuses
any slot present in neither, with a clash check at `:437`. The precedent is not merely analogous —
it is an existing, committed mechanism the refusal templates can extend directly.

## Open for Phase 24 planning, NOT decided here

- Where the refusal templates live (module + whether they are a frozen pin).
- Whether "equivalent guard" means extending `test_no_fact_strings_at_import` in place or a sibling
  test — the developer explicitly allowed either.
- The mixture ratio the refusal arm trains at (Phase 24's actual subject).
- Which held-out attack family the templates must survive.
