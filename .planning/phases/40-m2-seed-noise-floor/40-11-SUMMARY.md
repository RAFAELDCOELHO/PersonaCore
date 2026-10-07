---
phase: 40-m2-seed-noise-floor
plan: 11
subsystem: e2-noise-floor-publication
tags: [records, report, addendum, approvals, sc-check]
requires: [40-10]
provides:
  - "results/phase40_noise_floor.json committed alone under Rafael's second approved (fd603cd)"
  - "results/phase40_noise_floor_report.md = render_report(record) committed alone under his third approved (9a6a5e4), then a dated continuation via scripts/_addendum.py under his separate approved (4f7b2ff)"
  - "SC1-SC3 shown by command"
affects: [41]
tech-stack:
  added: []
  patterns: ["_addendum.append_addendum with pending == recorded == '## Provenance' for a report that renders no placeholder line"]
key-files:
  created: [results/phase40_noise_floor_report.md]
  modified: [tests/test_phase32_frontier.py]
decisions:
  - "Latent red fixed in the TEST (31ed4e0): the v4-bytes guard excludes results/phase4[0-9]_* (dated continuation; none existed at v4.0, asserted)"
  - "Rafael option (B): the report committed equal to the render; the addendum in its own commit, not covered by the third approved"
requirements-completed: []
metrics:
  completed: 2026-10-07
---

# Phase 40 Plan 11: noise-floor record, report and dated addendum published

The noise-floor record and the report are each committed alone after the approved that covers them,
in record_layout order. The report is byte-identical to `render_report(record)` at its own commit.
Rafael's post-hoc readings and the seed 2025 attempts then went in as a dated continuation, appended
by the project's one continuation writer, in a separate commit under his separate approved.

## Task 1 — noise-floor record (second approved), full suite, report rendered

- 40-10-SUMMARY quotes Rafael's second reply (approved, no negation); porcelain was exactly
  `?? results/phase40_noise_floor.json`.
- **fd603cd** `results(40-11): NOISE-02 E2 noise-floor record …`: only results/phase40_noise_floor.json
  (sha256 678db43f213d9dd7c34fe52b2cf175caad19368b1215bc7a74a5036f2cdf31aa).
- Full suite at fd603cd: `1 failed, 4494 passed, 4 skipped` (56:11). The failure was
  `tests/test_phase32_frontier.py::test_v4_bytes_unchanged_since_the_v4_tag`: `git diff --quiet v4.0 HEAD -- results`
  (excluding phase24_token_budget, phase3*, erasure_kstar_*) listed exactly the 16 newly tracked
  results/phase40_* files. Latent red in the test, as the plan foresaw.
- **31ed4e0** `test(40-11): generalize the v4-bytes guard for the v6.0 phase4N records (dated continuation)`:
  adds `:(exclude)results/phase4[0-9]_*` and asserts no results/phase4N_* path existed at v4.0 (measured: none).
  Test alone: 1 passed; ruff clean. Rerun: **4495 passed, 4 skipped** (52:45), EXIT=0 — equal to the last
  green run (fb62996), zero new skips.
- Step 4: porcelain empty; record tracked; no report on disk. Step 5: `REPORT …/results/phase40_noise_floor_report.md`.
- Step 6: `report == render_report(record)`; headings in order: Status; Approval and cost (D-11, D-13, D-14);
  Seeds (D-15); A2 recall per seed with its denominator (NOISE-01); Training-seed floor beside v3.0's
  sampling floor (NOISE-02, D-01..D-05); Every pair (D-02, D-04); Per-slot spread (D-04); gap_noise_floor
  (D-09, D-10); Full x M2 re-reading (D-12, descriptive); Determinism check (D-07, descriptive);
  persona_adapter.pt correction and the Phase 18 residual (D-08, D-08b); Target rank across the M2 seeds
  (D-13, descriptive); Predictions recorded before the run; Provenance. The report's readings are copied
  in 40-09-SUMMARY (Task 4 step 5, the same render). Report sha256
  5b97b710939209e909f116e27f83bb876d23060a0cbe75d7b9368d8de4766cdb.
- Step 7: tests/test_phase21_sc5.py + tests/test_phase40_noise.py: 146 passed. Step 8: porcelain
  `?? results/phase40_noise_floor_report.md`.

## Task 2 — third checkpoint

Presented the report (items 1-6) and a draft addendum, with two measured facts: an appended report is no
longer equal to the render (Task 1's verify), and phase40's render emits no `pending` placeholder line, which
`_addendum.append_addendum` requires exactly once — proposed pending == recorded == `## Provenance` (once).

Rafael's third reply (pasted text, adopted by Rafael), verbatim:

> approved
>
> Terceiro aprovado da Fase 40: o relatório results/phase40_noise_floor_report.md (sha256 5b97b710939209e909f116e27f83bb876d23060a0cbe75d7b9368d8de4766cdb), commitado sozinho e igual ao render do registro. Opção (B).
>
> Este aprovado não cobre o adendo. O adendo entra em commit próprio, pelo _addendum.py com o marcador ## Provenance, depois de uma resposta minha ao texto final. Cole o rascunho inteiro para eu ler.
>
> Mudanças no rascunho antes de me mostrar:
> 1. Ordem: as leituras pós-hoc vêm primeiro; as tentativas da 2025 e os relatórios de disco vêm depois.
> 2. Primeira frase, sem rodeio: o piso publicado (0,3481) está acima da margem (b) de 0,2963, que não foi alterada. O próprio retreino, contra o completo da mesma semente, passa da margem em 3 de 5 sementes (2024, 1338, 1339) e fica abaixo na 1337 (7/27) e na 2025 (6/27).
> 3. Leitura c: dizer que 0,0052 era um par só (1337–2024) e que ele é o segundo menor dos dez pares.
> 4. Leitura d: as duas direções com o mesmo peso. Na âncora em 512, o 16 do k78 fica dentro da faixa 15–41 das sementes. No R_q, o k78 fica fora da faixa nas duas listas. Dizer os limites: um adaptador ablacionado só (semente 1337), só k78, |R| = 8, sem critério. Dizer que a linha M2 do E6 é igual à da semente 1337 do D-13 nas duas listas (0/27 e 11/27), e que os ranks em 512 vêm do campo anchor_curve do registro, que a tabela do relatório não mostra.
> 5. Fecho: leituras pós-hoc, não pré-registradas; nenhum limiar nem veredito muda; como a condição (b) é lida contra 0,348 fica para o pré-registro da Fase 41.

Premises measured before the draft: 0.3481 > 0.2963; same-seed max |m2 - full| 7/14/11/6/12 /27; 0.005214
is pair 1337-2024 and second smallest (smallest 2025-1339, 0.003070641864658441); 512-anchor ranks 32/41/41/23/15
vs E5 k78 16; R_q n1 committed 0-1 vs E6 k78 5, minted 9-12 vs 25; E6 M2 row 0/27 and 11/27 = D-13 seed
1337; |R| = 8 (E5 n_references 8, E6 minted_set_size 8); k78 = phase19_arm_erased, seed 1337. Claude added one
sentence naming a third disk-writes report (Notion_2026-10-07-101102…diag, seed 1339 relaunch window), disclosed.

## Task 3 — report commit, full suite, addendum, SC1-SC3

- **9a6a5e4** `results(40-11): NOISE-02 E2 noise-floor report …`: only results/phase40_noise_floor_report.md
  (sha256 5b97b710…6cdb verified before the commit). Full suite at 9a6a5e4: **4495 passed, 4 skipped** (54:38), EXIT=0.

Rafael's reply on the addendum (pasted text, adopted by Rafael), verbatim:

> approved — só para o adendo do relatório da Fase 40, com três correções de redação e nenhum número alterado:
>
> 1. Trocar a frase "Every reading below is computed from the committed records only." por:
> "The four post-hoc readings (a-d) are computed from the committed records only. The sections on the seed 2025 attempts and on the diagnostic reports cite the ledger, the kept files under data/phase40_dropped/ (not tracked) and the macOS diagnostic reports (outside the repository)."
>
> 2. Na linha Sources da leitura d, escrever os dois caminhos do E6 por extenso: readings.<arm>.pet_name.rank.n1 e readings.<arm>.pet_name.rank.minted.n1.
>
> 3. Conferir no arquivo que o título "### Seed 2025: three attempts (ledger/v6_mps_ledger.jsonl)" e o título "### Diagnostic reports during the E2 relaunches" estão cada um em linha própria, e que a tabela das tentativas começa com "| attempt | ledger lines | seconds | hours |".
>
> A frase sobre o terceiro relatório de disco (Notion) fica.
>
> Aplicar com o append_addendum e o marcador ## Provenance, em commit próprio, só com o relatório.

- Edits 1 and 2 applied (diff: those two lines only); check 3: both headings on their own line, table header exact.
- Applied after the 9a6a5e4 suite finished: `_addendum.append_addendum(results/phase40_noise_floor_report.md, <text>,
  pending='## Provenance', recorded='## Provenance')` → `[_addendum] appended a dated section`; prefix byte-identical
  True; appended bytes == the approved text True; 90 insertions, 0 deletions; new sha256
  bdecc315d6da7b7c6cea2950c9d91ed9d5da74eb7c15a8b25032baa96b139457.
- **4f7b2ff** `results(40-11): dated continuation to the E2 report via _addendum.py …`: only the report.
  Targeted (test_phase35_prereg, test_phase40_prereg, test_phase40_noise, test_phase21_sc5, test_phase36_ledger,
  test_phase32_frontier): 358 passed. Full suite at 4f7b2ff: **4495 passed, 4 skipped** (53:45), EXIT=0.

### SC1-SC3 (commands and outputs)

- **SC1**: `phase40_prereg.E2_S` 5 == results/phase36_budget.json e2_seed_count 5 → True;
  `SEEDS == phase35_prereg.seed_list()[:E2_S]` → True (1337, 2024, 1338, 2025, 1339); the record's per_seed covers
  every whole seed with both groups and n_questions 27 on every core slot → True;
  `tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo` → 1 passed.
- **SC2**: recall_floor.beside = {margin_amended False, margin_at_gate 0.2962962962962963, sampling_floor
  0.14814814814814814}; `git diff --quiet f2cc033^ HEAD -- results/phase19_noise_floors.json scripts/phase19_floor.py`
  (f2cc033 = the prereg's first commit) → succeeds.
- **SC3**: last commit touching scripts/phase40_prereg.py 391e1c0; first commit adding a results/phase40_* cf3b626;
  `git merge-base --is-ancestor 391e1c0 cf3b626` → yes; tests/test_phase40_prereg.py `-k "frozen or first_add"` →
  2 passed. Approval order: first (40-10-SUMMARY "Task 1") before ea8f7d3..60e4480; second (40-10-SUMMARY "Task 3")
  before fd603cd; third (this SUMMARY "Task 2") before 9a6a5e4; the addendum's approved before 4f7b2ff.

## For the orchestrator's hand close (STATE.md, ROADMAP.md, REQUIREMENTS.md — not edited here)

| sha | what |
|---|---|
| ea8f7d3 | ledger: E2 lines (first approved) |
| cf3b626, 6dbf272, a93240d, 73ebe08, 60e4480 | seeds 1337, 2024, 1338, 2025, 1339: seed + A2 records (first approved) |
| 56ad39b | 40-09-SUMMARY |
| 64e6a9d | 40-10-SUMMARY |
| fd603cd | noise-floor record (second approved) — NOISE-02 |
| 31ed4e0 | latent-red test fix (v4-bytes guard) |
| 9a6a5e4 | report (third approved) |
| 4f7b2ff | dated addendum to the report |

NOISE-01 and NOISE-02 are published; requirements are marked complete by hand, not by any gsd-sdk handler.
