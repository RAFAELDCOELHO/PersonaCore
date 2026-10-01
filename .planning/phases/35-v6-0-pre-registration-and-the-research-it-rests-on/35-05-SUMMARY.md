---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
plan: 05
subsystem: prereg
tags: [prereg, review, phase-gate, prereg-05, prereg-06, prereg-07, prereg-08, prereg-09]

requires:
  - phase: 35-04
    provides: the complete v6.0 prereg (core, 17 slots, censuses, ordering legs) for review
provides:
  - Rafael's review of every ENTRIES item, every SLOTS item and the 19 planner readings
  - Review corrections f13ad62 and d850d0c (e1 floors computed, e4_beta, NOT_REACHED, verbatim pin lines, calibration corpus a declared input, calibration keyed by (ordering, seed))
  - ROADMAP Phase 35 SC1 hand-note (7275ba1), the per-fill-file reading approved
  - Full suite green on the committed tree; 35-VALIDATION.md signed off
affects: [phase 36 (the prereg freezes at its first record), phases 37-43 (slot owners), phase 41 (calibration contract)]

tech-stack:
  added: []
  patterns:
    - "A floor is computed by the slot rule from the consumed calibration record, never typed; a supplied value that differs is refused"
    - "Synthetic test records are labelled as fixtures (field + test name + docstring) and scored through the real route, never cited as a reading"

key-files:
  created:
    - .planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-05-SUMMARY.md
  modified:
    - scripts/phase35_prereg.py
    - tests/test_phase35_prereg.py
    - .planning/research/V6-PREREG-09.md
    - .planning/ROADMAP.md
    - .planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-VALIDATION.md

key-decisions:
  - "Planner readings 1, 3 and 4 approved by Rafael; the 35-03 deviation accepted; the other 16 readings stand on 'approved'"
  - "e1_condition_a_floors: computed with phase19_erasure.lock_erasure_floor on the cell's own calibration record through the defect-B correction's route (option A: the calibration fact is select_calibration_fact())"
  - "Calibration is keyed by (ordering, seed), not target: nothing of the target enters Phase 19's cal-erase path, so one record serves every E1 target"
  - "e4_beta = 0.05 is an entry (preference) and E4 refuses any other beta"
  - "NOT_REACHED is a named outcome distinct from every verdict string; such a cell gets no (b)/(c) verdict and is never PASS nor FAIL"

requirements-completed: []
# The orchestrator ticks PREREG-05..09 at phase close (after verification), never from a plan.

duration: ~3h (review rounds + 39 min suite)
completed: 2026-10-01
---

# Phase 35 Plan 05: Rafael's review and the phase gate — Summary

The v6.0 pre-registration was reviewed by Rafael before it freezes, corrected in two rounds, and
the full suite is green on the committed tree with no new skip.

## Task 1 — the review

The orchestrator rendered the listing (21 entries, 17 slots, the derived values and the 19 planner
readings, plus the executors' notable deviations) into the session scratchpad and showed it at the
blocking checkpoint. Rafael's replies, verbatim:

**Round 1 (listing at 6c02882):**

> Leituras 1, 3 e 4 aprovadas (a nota datada sob o SC1 pode ser escrita). O desvio do 35-03 está aceito. Três correções no módulo e nos testes antes do congelamento:1. e1_condition_a_floors. O piso não é digitado. A regra calcula cada piso com phase19_erasure.lock_erasure_floor aplicado à taxa de calibração lida do registro results/phase41_calibration_*.json da própria célula (pelas linhas do próprio arm, como na correção do defeito B, nunca por _calibration_rate), no denominador de 27 perguntas. O chamador informa só as chaves (alvo, ordem, semente); um valor informado que difira do calculado é recusado. A regra devolve também o ramo (floor_branch) de cada piso.2. e4_parameters. Acrescente a entrada e4_beta = 0.05, kind = preference, source = o nível de 95% unilateral da Fase 26 (z = erasure_gate._Z_ONE_SIDED_95) e os dois pinos reproduzidos do artigo, ambos a 0,05. A regra recusa beta diferente da entrada.3. e1_checkpoint_grid. Declare o desfecho quando nenhum ponto de checagem confirma zero a K = FULL_FIDELITY_K: a célula registra NOT_REACHED (constante nomeada no módulo), não recebe veredito de (b) nem de (c) num ponto de parada, e nunca conta como PASS nem como FAIL. Teste para esse caso.Além disso, na nota V6-PREREG-09.md, cole a linha exata (uma por pino) de onde saem 0,673 (App. D, p. 46) e 2,675 (p. 28), para eu conferir no PDF.Depois: rode o arquivo de teste, commite e me mostre só as linhas alteradas antes da suíte completa.

**Round 1, value source (the executor measured that the calibration corpus carries no values;
the orchestrator's contract had assumed it did):**

> Opção A. Cubra os ramos "discount" e "ceiling" com um registro sintético rotulado como fixture (nunca uma segunda leitura), já que draws reais só exercitam "reachability-min".

**Round 2 (changed lines of f13ad62 shown):**

> Duas correções, num commit só, antes da suíte.1. Corpus (o ponto solto que você levantou): o corpus de cada registro de calibração passa a ser um input declarado do slot e precisa aparecer no source da derivação. Teste RED plantado.2. Calibração por (ordem, semente), não por alvo. A calibração roda em select_calibration_fact(), não no alvo. Confirme lendo o caminho do cal-erase da Fase 19: algo do alvo entra na calibração (ordem, ponto de parada, adaptador)? - Se NÃO entra: o registro de calibração é chaveado por (ordering, seed), sem campo target, e um registro serve a todos os e1_targets() daquela (ordering, seed). A saída continua com uma linha por (alvo, ordem, semente), cada uma apontando para o mesmo calibration_record. Recuse registro duplicado para a mesma (ordering, seed). Ajuste o contrato no docstring e os testes (um registro, quatro alvos). - Se ENTRA: não mude a regra; me diga o que entra, e registre que o E1 precisa de uma calibração por alvo (16 no desenho 4 × 2 × 2) para a Fase 36 orçar.Depois: arquivo de teste, commit, e me mostre as linhas alteradas.

**Round 3 (changed lines of d850d0c shown):**

> Aprovado

### Premises measured before each correction (orchestrator)

- Every E1 target (pet_name, cat_name, street, sibling_name) pools to 27 questions (14 core_taught +
  13 core_held_out) in `results/phase16_recall_sample.json`, so `lock_erasure_floor`'s clamp
  `wilson_upper_bound(0, 27)` is reachable for each.
- arXiv 2305.08846 v1 is the only version (abs page: "Submitted on 15 May 2023"); the PDF was
  re-read through gstack `/browse` and its text layer extracted with macOS PDFKit. PIN 1's line is
  on p. 46; PIN 2's ε ≥ 2.675 is on p. 28 and its 95% / m = 100,000 are in Figure 11's caption on
  p. 30.
- Nothing of the target enters Phase 19's calibration: `_cmd_cal_erase` uses the calibration
  adapter, and `select_ablation_prefix` computes the order and the stop k against
  `select_calibration_fact()`; collateral is the same `CORE_SLOTS` for every target and is
  re-scored only after k is fixed. Hence the "NÃO entra" branch of round 2.
- `results/phase19_calibration_corpus.json` is tracked at tag v5.0 (first add 7293ec9), so it can
  be a declared input.

### Commits

| Commit | What |
|--------|------|
| `f13ad62` | Round 1: e1 floors computed from the cell's calibration record (option A, synthetic fixtures for discount/ceiling), `e4_beta`, `NOT_REACHED` + `e1_stop`, verbatim pin lines in the note |
| `d850d0c` | Round 2: calibration corpus a declared input; calibration keyed by (ordering, seed), one record serves every target |
| `7275ba1` | ROADMAP Phase 35 SC1 hand-note (7 lines added, none changed; first 1429 lines byte-identical; STATE/REQUIREMENTS untouched; both report checks exit 0) |

## Task 2 — the phase gate

- Full suite on the committed, clean tree at `7275ba1`: **3478 passed, 4 skipped, 0 failed** in
  39:23, `EXIT=0`. Skips equal the last green run's 4 (b8b6335). `tests/test_phase25_venue.py`
  has no commit in this phase. Of the +167 passed since b8b6335, 79 are
  `tests/test_phase35_prereg.py`; the other 88 (by subtraction) come from the post-v5.0 paper / k*
  commits between b8b6335 and the phase start.
- No `results/phase3[5-9]_*` / `results/phase4[0-5]_*` file exists (git ls-files and find).
- `phase28_report.py check` and `phase34_report.py check` exit 0; ruff clean.
- `35-VALIDATION.md` signed off: `status: complete`, `nyquist_compliant: true`,
  `wave_0_complete: true`, every row ✅ with its selector and test names.

## Deviations

- The orchestrator ran Task 1's listing and the planning-file steps inline rather than through an
  executor (small mechanical steps); the module/test corrections went through a continuation
  executor.
- The orchestrator's first correction contract assumed the calibration corpus carries fact values.
  It does not; the executor stopped before editing and Rafael chose option A. Recorded as an
  orchestrator error, not a plan premise.
- The dead-for-now refusal "a consumed corpus no record names" cannot fire while only one corpus is
  declared; it stays for when more are.

## Obsidian

Recorded by the orchestrator in `01-Projects/PersonaCore — memória em pesos.md` after this commit.
