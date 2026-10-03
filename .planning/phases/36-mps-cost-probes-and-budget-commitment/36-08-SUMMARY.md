---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 08
subsystem: mps-budget
tags: [cost-02, budget, stop-line, fill]
requires: [36-07]
provides:
  - scripts/phase36_budget_prereg.py
  - results/phase36_budget.json
key-files:
  created:
    - scripts/phase36_budget_prereg.py
    - results/phase36_budget.json
  modified:
    - scripts/phase36_caps.py
    - scripts/phase36_budget.py
    - tests/test_phase36_budget.py
    - tests/test_phase36_caps.py
requirements-completed: [COST-02]
completed: 2026-10-02
---

# 36-08 — Rafael's ruling, the fill file and the v6.0 MPS budget

Executed inline by the orchestrator. Every number below was read from the dry output or a
committed file.

## Task 1 — the checkpoint

Presented: the dry at the defaults (97.19 h, HALT 7.189 h over 90 h), the 25% table (no gated
exceed), the ruling alternatives and the D-15 cut table (36-07-SUMMARY).

**Rafael's ruling, verbatim (2026-10-02):**

> Ainda não é "approved". Decisão a aplicar primeiro, com dry --ruling, e me mostre a tabela nova:
>
> 1. Base de preço: spread_scaled para o passe A2 do E2 e para a pontuação do E3. Motivo: o total
> medido bate com o histórico (2,6% e 0,5%), e o que varia numa soma de milhares de draws é o total
> da rodada, não o draw. Fica coerente com o E1, que já usa o custo medido.
>
> 2. E6: a geração no contexto A2 não é refeita. Reaproveite os registros commitados a K = 48
> (Fase 18 para k = 0; erasure_kstar_arm_k* para 8, 16, 32, 64; phase19_arm_erased para 78;
> phase19_arm_retrain para M2), verificados por SHA-256. O orçamento do E6 cobre só a geração na
> âncora e a pontuação de NLL e rank. Ponha isso como teto: entradas A2 re-geradas = 0. Se a Fase 39
> achar um registro que não serve, ela pausa e me pergunta; não regenera sozinha.
>
> 3. Nenhum corte: S = 5, reserva do E4 mantida (3 pontos), 4 receitas, lote 8, 5 pontos de
> checagem por célula.
>
> Confirme antes de recalcular se os sete registros do item 2 têm os draws por pergunta para as 216
> entradas. Se algum não tiver, diga qual e mostre a tabela só com o item 1.

**Precondition measured:** all seven records hold the same 216 A2 entries (identical keys: family,
slot, fact_id, prefix, seed_index, tier, dose), 48 completions each, `config.k = 48`, seed 1337 —
`phase18_arm_adapter-on.json` (A2 subset of its 976 draws), `erasure_kstar_arm_k008/016/032/064`,
`phase19_arm_erased.json`, `phase19_arm_retrain.json`.

**Item 2 did not fit an existing cap:** `E6.entries` both multiplies the A2-context generation AND
caps the scored entries / Phase 39's `e6_entry_subset`; `entries = 0` would have dropped the NLL/rank
scoring and refused every Phase 39 fill. Added a separate cap `E6.a2_regenerated_entries` (default
= entries, lowered only by `cap_rulings['E6.a2_regenerated_entries']`, never above entries) —
commit `84af553`, with `test_derive_cap_ruling_lowers_e6_a2_regenerated_entries`. The cap ruling
text records the seven paths with their SHA-256 and the "Phase 39 pauses, never regenerates" rule.

**Rafael's approval, verbatim:**

> approved: total e frentes como na tabela do dry com os três itens; linha de parada 90 h; S = 5;
> reserva do E4 com 3 pontos; 4 receitas; lote 8; 5 pontos de checagem por célula; E6 com
> a2_regenerated_entries = 0 e entries = 216.

`dry --ruling` with the three items (price_rulings single_run_draw_loop = spread_scaled; unit_caps
= the proposal with E6.a2_regenerated_entries = 0; no cuts): **FITS**.

| E1 | E2 | E3 | E4 | E5 | E6 | R1b | probes | total | stop line | S |
|---|---|---|---|---|---|---|---|---|---|---|
| 52.780 | 7.891 | 6.622 | 4.807 | 0.361 | 0.495 | 1.108 | 3.660 | **77.724 h** | 90 h | 5 |

## Task 2 — fill file, then the budget record

- `9a5718a` feat(36-08): `scripts/phase36_budget_prereg.py` alone (RULING with Rafael's approved
  verbatim; one `phase35_prereg.fill("v6_budget_and_stop_line", ...)`). Proved before committing:
  front_hours as above, total 77.72433149898184, stop line 90, S 5; census 4 passed.
- `6b57231` data(36): `results/phase36_budget.json` alone, from `phase36_budget.py emit`
  (`stop line 90.000 h`). `total_hours == math.fsum(front_hours)`; E6 caps
  `{a2_regenerated_entries: 0, adapters: 7, anchor_adapters: 7, anchor_slots: 8, entries: 216,
  max_k: 48}`. The fill file has exactly one commit and it is the parent of the budget commit.
- Sanity: `require_launch("E1")` passes (spent: probes 13176.15 s);
  `check_unit_caps("E6", a2_regenerated_entries=0)` passes; `= 1` refuses ("exceeds the committed
  cap 0 … needs Rafael's approved").

## Task 3 — phase gate

A second latent state-dependent red appeared once the budget record existed:
`test_phase36_caps::test_committed_budget_refuses_an_untracked_record` asserted the record was
untracked "today". Fixed in the test (`e72c17a`, untracked simulated by the listing).

Full suite on the fill + budget state (HEAD e72c17a): **3782 passed, 4 skipped, EXIT=0** (42:14).

## Reminder for Phases 37-43

Call `phase36_ledger.require_launch(front)` before each launch (a 0-h front never launches). A
tripped D-13 stop is a pause: take what ran and the cut table to Rafael, and only after his written
ruling run `phase36_ledger.py rule --front F --stop L --text '<verbatim>'`. Owner fills are checked
against `results/phase36_budget.json` unit caps (`phase36_caps.check_unit_caps` /
`owner_overruns`). **Phase 39 (E6):** `a2_regenerated_entries = 0` — reuse the seven committed K = 48
A2 records after verifying their SHA-256 (listed in the fill file's cap ruling); if one does not
serve, pause and ask Rafael, never regenerate. **Phase 43 (E4):** `require_e4_first_point` checks
the first point at 25%.

## Deviations

1. New cap field `E6.a2_regenerated_entries` (84af553) — Rafael's item 2 could not be expressed with
   the existing `E6.entries` without dropping the scoring and blocking Phase 39.
2. Latent-red test fix e72c17a (above).
3. Executed inline by the orchestrator.
