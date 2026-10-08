---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 05
subsystem: erasure-prereg-review
tags: [phase41, review, prereg-freeze, erase-04, erase-06, erase-07, erase-10]
requires: [41-02, 41-03, 41-04]
provides:
  - reviewed pre-registration scripts/phase41_prereg.py, every planner default confirmed by Rafael
  - frozen prereg digest 11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3
affects: [41-06, 41-07, 41-08, 41-09, 41-10, 41-11, 41-12, 41-13, 41-14, 41-15, 41-16]
key-files:
  created: [.planning/phases/41-erasure-across-facts-orderings-and-seeds/41-REVIEW.md]
  modified: [scripts/phase41_prereg.py, tests/test_phase41_prereg.py, .gitignore]
decisions:
  - "CR-01 extended: every Phase 41 count-rate comparison exact (Fraction over integer counts) — (b), D-19 label, D-18 range; margin recovered from the committed value; 8/27 tie passes"
  - "WR-01: (a) vacuous at a judged stop, asserted; the four calibrations (1.245 h) stay and feed D-12 only"
  - "WR-02: D-17 counts pairs; não replicado broken down once per pair by seed-verdict combination"
  - "WR-03: calibration CSV directory gitignored; IN-01 text fixed; IN-05 INCONCLUSIVE fills its lists; IN-02/03/04/06/07 known limitations; nine defaults confirmed"
requirements-completed: []
---

# 41-05 — Review of the pre-registration, Rafael's rulings, full suite, freeze

`requirements-completed: []` — 41-05 reviews and freezes the rules ERASE-04/06/07/10 are read against; it completes none of them.

REVIEW_BASE: `c271c67`. Review: `41-REVIEW.md` (gsd-code-reviewer, explicit path; 1 critical, 3 warnings, 7 info), Resolution `f6df669`.

## Task 1 — review and rulings

CR-01 reproduced by the orchestrator before presenting it: `21/27 - 13/27 = 0.29629629629629634 > 0.2962962962962963` (float) while `Fraction(21,27) - Fraction(13,27) > Fraction(8,27)` is False; the decreasing pairs with |Δn| = 8 that float misreads: (15,7), (17,9), (19,11), (21,13); seed 1337's intact hometown is 21/27 (results/phase40_a2_full_seed1337.json). Premises of the reply measured before applying: `[n for n in range(28) if float(Fraction(n,27)) == e1_condition_b_margin()] == [8]`; D-18 in `m1_m2_rows`, D-19 in `slot_ranges`/`varies_labels`; plan 41-08 already runs `d02_check` at every gradient of the MPS smoke before any record (41-08-PLAN.md:17).

| finding | ruling | commit |
|---|---|---|
| CR-01 (extended to D-18/D-19) | fix: exact `Fraction` comparisons, `exact_margin`/`E1_CONDITION_B_MARGIN_EXACT` | 2b0a2e8 |
| WR-01 | (a) vacuous at the judged stop, asserted in cell_verdict; calibrations stay | 737d91c |
| WR-02 | pairs; seed-verdict combinations inside não replicado | f975c8e |
| WR-03 | `.gitignore` `results/phase41_e1_calibration_seed*/` + test | ac1f091 |
| IN-01 | text fix (backward <= ~55.6x forward) | 1e5d039 |
| IN-02 | known limitation; record states the deciding measurement | f65cd36 |
| IN-05 | fix: INCONCLUSIVE fills failed / beyond | af9fcfb |
| IN-03, IN-04, IN-06, IN-07; 41-04 deviations 1-3 | known limitations / confirmed | — |
| nine planner defaults | all confirmed by Rafael 2026-10-08 (d02_equality with his note) | c8fc75d |

Downstream plans amended to the new API (dated `<orchestrator_amendment>` blocks): 41-08, 41-09, 41-10, 41-15, 41-16 at `2e3ca1f` (`variant_decided_by` field for IN-02; summary_counts combination keys; cell_verdict refusals; exact comparisons).

### Premise correction in Rafael's milestone-report note (measured, not applied to any code)

His note says "No E5 não há empate". Measured false: `results/phase38_rank.json::drop_formula_audit.exact_ties == [['person_name', 8]]` (a2 person_name counts k0 26, k8 18), `flips == []`; `results/phase38_rank_report.md:122` "exact margin tie decided by D-14's strict >". It is the same pair he cites for E6 (`results/phase39_ctx.json::drop_formula_audit.exact_ties == [['k8','person_name','G_q']]`), float and exact agree (INTACT). Confirmed: E6 single tie; Phase 40 addendum differences 7, 14, 11, 6, 12 (results/phase40_noise_floor_report.md dated continuation, 4f7b2ff); v3.0 M2 deltas 7/27 and 3/27, M1 failure independent of a tie (results/phase19_erasure_report.md:258-265). Not in the note: Phase 40 has two cross-seed hometown ties (full 2024 vs m2 1339; full 1339 vs m2 2025), float and exact agree. Reported to Rafael with suggested wording for the milestone report; no ruling changes.

### Rafael's reply at the 41-05 checkpoint, 2026-10-08 (verbatim)

```
CR-01: corrigir como recomendado, estendido. Toda comparação de taxas de contagem da Fase 41 é exata, com Fraction sobre as contagens inteiras: a condição (b), o rótulo do D-19 e o "dentro/fora da faixa" do D-18. O float fica só para exibição. A margem exata é recuperada do valor commitado (a Fraction de denominador 27 cujo float é igual ao commitado, com asserção), nunca digitada. Um empate exato em 8/27 passa, pela regra ≤. Teste com os quatro pares medidos (15→7, 17→9, 19→11, 21→13).
Nota, sem reabrir nada: conferi nos registros commitados que nenhuma leitura cai num desses empates de um jeito que o float mude. No E5 não há empate; no E6 há um só (person_name k8, 26→18), em que float e conta exata concordam; na Fase 40 as diferenças do adendo são 7, 14, 11, 6 e 12; no v3.0 os deltas do M2 são 7/27 e 3/27 e a falha do M1 não depende de empate. A nota entra no relatório do milestone.

WR-01: como recomendado. As quatro calibrações ficam. A entrada diz que (a) é vazia no ponto de parada julgado, com asserção em cell_verdict. O relatório do milestone registra isso como achado sobre o desenho do portão: a regra de parada já implica (a), e as calibrações (1,245 h) alimentam só o D-12.

WR-02: contar pares, escrito em ENTRIES["summary_line"]. Os três rótulos somam 8. Dentro de "não replicado", cada par aparece uma única vez, sob a combinação dos vereditos das duas seeds (por exemplo "SUCCESS + NOT_REACHED"), para as subcontagens somarem o total sem dupla contagem. NOT_RUN entra como um valor de veredito nessas combinações.

WR-03: como recomendado: entrada no .gitignore para o diretório do CSV de calibração, com um teste de que ele é ignorado.

IN-01: corrigir o texto como recomendado.
IN-02: limitação conhecida; o registro diz qual medição (CPU ou MPS) decidiu a variante.
IN-03, IN-04, IN-06, IN-07: limitações conhecidas.
IN-05: corrigir: um INCONCLUSIVE preenche as listas de condições e de não-alvos que falharam, como o D-15 pede.

Desvios do 41-04: confirmo os três; o terceiro como limitação conhecida (é o IN-03).

Padrões do planner: aceito os nove. No d02_equality, a igualdade é exercitada no smoke do MPS antes de qualquer registro, para uma diferença sistemática aparecer antes da rodada e não no meio dela.

reviewed
```

## Task 2 — full suite on the committed tree

- HEAD `f6df669` (tree clean under scripts src results tests ledger artifacts; no pytest/MPS job running).
- `.venv/bin/pytest -q -p no:cacheprovider` (nohup + waiter): `4558 passed, 4 skipped, 83 warnings in 3261.66s (0:54:21)`, `EXIT=0`. Last green run 4495 passed / 4 skipped (40-11-SUMMARY): +63 passed (the Phase 41 prereg tests), skips unchanged.
- **Frozen prereg:** `shasum -a 256 scripts/phase41_prereg.py` = `11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3` (at c8fc75d, unchanged at f6df669 and 2e3ca1f).
- `git log --format='%h %s' -- scripts/phase41_prereg.py`: c8fc75d, af9fcfb, f65cd36, 1e5d039, f975c8e, 737d91c, 2b0a2e8, f7d8439, 13f7f36, f220f4f, 44586fd, 578011f, d6f12e9.
- `git ls-files 'results/phase41_*'` empty.

## Deviations

- The orchestrator ran the review step and Task 2 itself; the rulings were applied by an executor (one commit per item, tests first).
- Driver-side IN-02 field named `variant_decided_by` by the orchestrator's amendment to 41-08 (Rafael ruled the content, not the name).
