---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 16
subsystem: erasure-stage2-publish
tags: [phase41, e1, stage2, approvals, report, erase-03, erase-04, erase-05, erase-06, erase-07, erase-08, erase-09, erase-10]
requires: [41-15]
provides:
  - results/phase41_erasure.json committed alone (14a0cc6) under Rafael's second stage-2 approved
  - results/phase41_erasure_report.md committed alone (54ef68c) under the third approved, byte-equal to render_report(record)
  - dated continuation 2026-10-13 appended via scripts/_addendum.py (2da7ba2), text approved by Rafael
key-files:
  created: [results/phase41_erasure_report.md]
  modified: [results/phase41_erasure.json (first add), results/phase41_erasure_report.md (dated continuation)]
requirements-completed: [ERASE-03, ERASE-04, ERASE-05, ERASE-06, ERASE-07, ERASE-08, ERASE-09, ERASE-10]
---

# 41-16 — E1 published write-once: record, report, dated continuation; SC1–SC5 by command

## Task 1 — erasure record committed alone; full suite; report rendered

- `results/phase41_erasure.json` sha256 78d3e4b52f04c5b37b053e1e1f318b76d0e7afe0fd5d85a51885c559984264d2, equal to the value Rafael approved (41-15 Task 3). Committed alone: **14a0cc6**, message quoting the second approved.
- Full suite #1 at 14a0cc6: `4709 passed, 4 skipped, 83 warnings in 3985.30s (1:06:25)`, `EXIT=0`. Skips unchanged (4, as at the last green run).
- `phase41_erasure.py report` → `REPORT /Users/juliorcoelho/PersonaCore/results/phase41_erasure_report.md`; equality check printed `True`. Report: 1135 lines, sha256 75716e6c5b8adb16d43b5816dca121509b8b6c2799c0328e7b29b96fc3a46696.

## Task 2 — third checkpoint

Shown: path, the `grep '^#'` headings, the summary line ("Status: **COMPLETE**. Of the 8 (target, ordering) pairs: PASS 0, FAILURE replicada 8, não replicado 0.") and the 8 pair labels (all `FAILURE replicada`, "FAILURE na 1337, FAILURE na 2024"). Flagged: the "Inside 'não replicado'" breakdown table renders header-only at 0 pairs; options (i) driver change + re-render, (ii) commit as is + dated continuation.

### Rafael's reply (verbatim)

```
approved

Terceiro aprovado do estágio 2 da Fase 41: results/phase41_erasure_report.md (sha256 75716e6c5b8adb16d43b5816dca121509b8b6c2799c0328e7b29b96fc3a46696), commitado sozinho e igual ao render do registro. Opção (ii).

Depois, um adendo datado pelo _addendum.py (marcador ## Provenance), em commit próprio, coberto por uma resposta minha ao texto final. Ele traz:
1. A tabela "Inside 'não replicado'" está vazia porque nenhum par caiu nessa categoria (0 pares).
2. A previsão D-21, por extenso: o lado do R_q se confirmou nas 4 células do pet_name (n1 commitado 11, 10, 17 e 17 contra 0–1 dos M2; mintado 27 nas quatro contra 9–12); o lado da âncora falhou nas 4 (rank em 512 igual a 12, 6, 2 e 1 contra a faixa de 15 a 41). As paradas foram 64, 64, 32 e 32. A previsão partiu da leitura do E5 em k = 78, com mais ablação do que essas paradas. Pelo pré-registro, o desacordo é um achado: com a geração em zero, o alvo continua entre os primeiros dos 512 candidatos.
3. Horas: o 32,3752 h da linha "E1 spent (ledger)" vem do relógio provenance.run de cada registro, que o phase36_ledger.spent() usa quando o registro está rastreado. Pelo intervalo das linhas do livro-caixa seriam 32,3795 h. A diferença de 15,5 s vem dessas duas formas de medir.
4. Uma frase de leitura, sem veredito novo: a ordenação adaptativa apagou com menos componentes (paradas de 32 a 48, contra 32 a 128 da atual), e a condição (b) falhou nas 16 células nas duas ordenações.

Nenhum número novo: tudo vem dos registros commitados.
```

Premises measured before drafting the addendum (two corrected, both accepted by Rafael):
- Item 2, "a previsão partiu da leitura do E5 em k = 78": no planning document records that origin (41-DISCUSSION-LOG §(iii) and 41-CONTEXT D-21 cite the five M2 anchor values 15, 23, 32, 41, 41 and Phase 39's k = 64 reading). E5 (`results/phase38_rank_report.md`, pet_name, anchor 512) reads 16 at k = 78 (inside) and 12 at k = 64 (outside). The addendum states the E5 readings as facts, not the origin.
- Item 4, "apagou com menos componentes": gradient stops ≤ greedy in 8/8 pairs; fewer in 5, equal in 3 (cat_name 2024 48 = 48, street 1337 32 = 32, street 2024 32 = 32). "adaptive" is the gradient ordering's D-05 variant (`variant: adaptive`, decided by mps_smoke); the addendum names both.
- Verified as written: 0 pairs in não replicado; R_q committed 11/10/17/17 vs [0, 1], minted 27 ×4 vs [9, 12]; anchor_512 12/6/2/1 vs [15, 41]; stops 64/64/32/32; 32.3752 h vs 32.3795 h (15.5 s); stops 32–48 vs 32–128; (b) failed 16/16.

### Rafael's reply to the addendum text (verbatim)

```
approved, com uma troca no item 2 e um ponto final no item 4.

Item 2, trocar a última frase por:
"Essa metade da previsão errou. Pelo pré-registro (D-21), o desacordo entre rank e geração é registrado como achado e não muda nenhum veredito: com a geração em zero, o alvo continua entre os primeiros dos 512 candidatos."

Item 4: terminar com "nas duas ordenações." (com ponto).

O resto como está. Conferi contra os registros: as leituras do E5 (k = 64 → 12, k = 78 → 16, linha 137 de phase38_rank_report.md), o texto da D-21 (41-CONTEXT, linhas 188–195) e as paradas por par (5 com menos componentes, 3 com o mesmo número). As duas correções ao meu texto estão certas.
```

Item 4 already ended with "nas duas ordenações." (full stop) in the draft; no change was needed there.

## Task 3 — commits, suites

| sha | content |
|---|---|
| 14a0cc6 | results/phase41_erasure.json alone (second approved) |
| 54ef68c | results/phase41_erasure_report.md alone (third approved), sha256 75716e6c…a46696 |
| 2da7ba2 | results/phase41_erasure_report.md dated continuation 2026-10-13 (`_addendum.append_addendum`, pending = recorded = `## Provenance`): `10 insertions(+)`, 0 deletions, the committed prefix byte-identical (`cmp -n` on the 54ef68c bytes) |

- Full suite #2 at 54ef68c: `4709 passed, 4 skipped, 83 warnings in 4021.82s (1:07:01)`, `EXIT=0`.
- After 2da7ba2, the targeted guards (Task 3 verify set): `6 passed, 258 deselected`.
- Full suite #3 at 2da7ba2: `4709 passed, 4 skipped, 83 warnings in 4164.18s (1:09:24)`, `EXIT=0`.
- No latent red; no test commit.

## SC1–SC5 by command

### SC1 — targets, orderings, seeds, adapters, no Phase 40 retrain

```
=== SC1
e1_targets ('pet_name', 'cat_name', 'street', 'sibling_name')
ORDERINGS ('greedy', 'gradient')
e1_teaching_seeds (1337, 2024)
1337 full checkpoints/phase40_e2_full_seed1337_adapter.pt True
1337 m2 checkpoints/phase40_e2_m2_seed1337_adapter.pt True
2024 full checkpoints/phase40_e2_full_seed2024_adapter.pt True
2024 m2 checkpoints/phase40_e2_m2_seed2024_adapter.pt True
grep -c train_arm( : 1
    prefix = REHEARSAL_PREFIX if rehearsal else ARM_PREFIX
    paths = arm_paths(seed, rehearsal=rehearsal)
    csv_dst = root / "data" / WORK_DIR / arm / "run.csv"
    for path in (paths["adapter"], paths["checkpoint"], paths["bin"], paths["mask"], csv_dst):
        _prove(not path.exists(), f"{path} exists: stale output. Move it in a reviewed step")
    facts, second_person, replay_ratio = tp.arm_spec("cal_first_person_replay")
    production = _sha256(recall.ADAPTER_PATH)
    result = tp.train_arm(
        arm,
        facts=facts,
        family_ids=phase14_factset.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
```

The one `train_arm(` call is the calibration helper (`tp.arm_spec("cal_first_person_replay")`); no call names a Phase 40 arm.

### SC2 — floors before cells; stop = e1_stop; ranks; grid

`git log --format=%H -1 -- scripts/phase41_floors_prereg.py` (the LAST commit touching it, which is stricter than the first) checked with `git merge-base --is-ancestor` against each cell record's first add (`git log --diff-filter=A`):

```
=== SC2
floors prereg last commit b8c0e8107af2d36b5c8642ec433641ff347de5a0
grid {'checkpoints': (16, 32, 48, 64, 128), 'read_k': 16, 'confirm_k': 48, 'not_reached': 'NOT_REACHED'}
cell_pet_name_greedy_seed1337 ab79f87 ancestor True e1_stop 64 == stop True judged True ranks True reads [16, 32, 48, 64]
cell_pet_name_greedy_seed2024 4f4199e ancestor True e1_stop 64 == stop True judged True ranks True reads [16, 32, 48, 64]
cell_cat_name_greedy_seed1337 4ebe0c6 ancestor True e1_stop 128 == stop True judged True ranks True reads [16, 32, 48, 64, 128]
cell_cat_name_greedy_seed2024 ce9327a ancestor True e1_stop 48 == stop True judged True ranks True reads [16, 32, 48]
cell_street_greedy_seed1337 7c82777 ancestor True e1_stop 32 == stop True judged True ranks True reads [16, 32]
cell_street_greedy_seed2024 2b4893e ancestor True e1_stop 32 == stop True judged True ranks True reads [16, 32]
cell_sibling_name_greedy_seed1337 d8e97e8 ancestor True e1_stop 64 == stop True judged True ranks True reads [16, 32, 48, 64]
cell_sibling_name_greedy_seed2024 ee37409 ancestor True e1_stop 64 == stop True judged True ranks True reads [16, 32, 48, 64]
cell_pet_name_gradient_seed1337 5546c06 ancestor True e1_stop 32 == stop True judged True ranks True reads [16, 32]
cell_pet_name_gradient_seed2024 727ab8f ancestor True e1_stop 32 == stop True judged True ranks True reads [16, 32]
cell_cat_name_gradient_seed1337 d2c5303 ancestor True e1_stop 48 == stop True judged True ranks True reads [16, 32, 48]
cell_cat_name_gradient_seed2024 b9f6473 ancestor True e1_stop 48 == stop True judged True ranks True reads [16, 32, 48]
cell_street_gradient_seed1337 78c97e0 ancestor True e1_stop 32 == stop True judged True ranks True reads [16, 32]
cell_street_gradient_seed2024 1fcaa9f ancestor True e1_stop 32 == stop True judged True ranks True reads [16, 32]
cell_sibling_name_gradient_seed1337 1e82bc0 ancestor True e1_stop 48 == stop True judged True ranks True reads [16, 32, 48]
cell_sibling_name_gradient_seed2024 67f4aec ancestor True e1_stop 48 == stop True judged True ranks True reads [16, 32, 48]
ancestor count 16 / 16
```

### SC3, SC4, SC5

SC4: per non-target n/27 per cell (pre → post at the stop; `*` beyond the margin 8/27) and the pair labels, asserting no PASS unless both seeds read SUCCESS.

```
=== SC3
2 passed, 187 deselected in 1.35s
DIALOGUE_GAP_BAND is mitigation_gate.dialogue_gap_band: True
=== SC4
cell_cat_name_gradient_seed1337 FAILURE birth_year:18/27->10/27 hometown:21/27->0/27* house_number:24/27->6/27* person_name:26/27->0/27* pet_name:27/27->3/27* sibling_name:27/27->4/27* street:27/27->0/27*
cell_cat_name_gradient_seed2024 FAILURE birth_year:16/27->4/27* hometown:22/27->0/27* house_number:23/27->0/27* person_name:27/27->1/27* pet_name:26/27->0/27* sibling_name:27/27->1/27* street:27/27->1/27*
cell_cat_name_greedy_seed1337 FAILURE birth_year:18/27->4/27* hometown:21/27->0/27* house_number:24/27->1/27* person_name:26/27->0/27* pet_name:27/27->0/27* sibling_name:27/27->0/27* street:27/27->0/27*
cell_cat_name_greedy_seed2024 FAILURE birth_year:16/27->6/27* hometown:22/27->0/27* house_number:23/27->4/27* person_name:27/27->2/27* pet_name:26/27->9/27* sibling_name:27/27->14/27* street:27/27->0/27*
cell_pet_name_gradient_seed1337 FAILURE birth_year:18/27->11/27 cat_name:27/27->26/27 hometown:21/27->0/27* house_number:24/27->13/27* person_name:26/27->1/27* sibling_name:27/27->11/27* street:27/27->7/27*
cell_pet_name_gradient_seed2024 FAILURE birth_year:16/27->11/27 cat_name:27/27->21/27 hometown:22/27->2/27* house_number:23/27->7/27* person_name:27/27->4/27* sibling_name:27/27->17/27* street:27/27->6/27*
cell_pet_name_greedy_seed1337 FAILURE birth_year:18/27->11/27 cat_name:27/27->6/27* hometown:21/27->0/27* house_number:24/27->6/27* person_name:26/27->0/27* sibling_name:27/27->0/27* street:27/27->0/27*
cell_pet_name_greedy_seed2024 FAILURE birth_year:16/27->7/27* cat_name:27/27->20/27 hometown:22/27->0/27* house_number:23/27->7/27* person_name:27/27->0/27* sibling_name:27/27->2/27* street:27/27->2/27*
cell_sibling_name_gradient_seed1337 FAILURE birth_year:18/27->9/27* cat_name:27/27->26/27 hometown:21/27->0/27* house_number:24/27->8/27* person_name:26/27->0/27* pet_name:27/27->2/27* street:27/27->2/27*
cell_sibling_name_gradient_seed2024 FAILURE birth_year:16/27->6/27* cat_name:27/27->27/27 hometown:22/27->0/27* house_number:23/27->1/27* person_name:27/27->0/27* pet_name:26/27->6/27* street:27/27->0/27*
cell_sibling_name_greedy_seed1337 FAILURE birth_year:18/27->9/27* cat_name:27/27->25/27 hometown:21/27->0/27* house_number:24/27->9/27* person_name:26/27->0/27* pet_name:27/27->3/27* street:27/27->6/27*
cell_sibling_name_greedy_seed2024 FAILURE birth_year:16/27->5/27* cat_name:27/27->24/27 hometown:22/27->0/27* house_number:23/27->4/27* person_name:27/27->0/27* pet_name:26/27->2/27* street:27/27->3/27*
cell_street_gradient_seed1337 FAILURE birth_year:18/27->15/27 cat_name:27/27->25/27 hometown:21/27->2/27* house_number:24/27->14/27* person_name:26/27->0/27* pet_name:27/27->9/27* sibling_name:27/27->14/27*
cell_street_gradient_seed2024 FAILURE birth_year:16/27->11/27 cat_name:27/27->27/27 hometown:22/27->3/27* house_number:23/27->9/27* person_name:27/27->10/27* pet_name:26/27->21/27 sibling_name:27/27->25/27
cell_street_greedy_seed1337 FAILURE birth_year:18/27->18/27 cat_name:27/27->25/27 hometown:21/27->2/27* house_number:24/27->16/27 person_name:26/27->1/27* pet_name:27/27->14/27* sibling_name:27/27->11/27*
cell_street_greedy_seed2024 FAILURE birth_year:16/27->13/27 cat_name:27/27->27/27 hometown:22/27->2/27* house_number:23/27->10/27* person_name:27/27->6/27* pet_name:26/27->26/27 sibling_name:27/27->24/27
cat_name|gradient FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
cat_name|greedy FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
pet_name|gradient FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
pet_name|greedy FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
sibling_name|gradient FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
sibling_name|greedy FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
street|gradient FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
street|greedy FAILURE replicada {'1337': 'FAILURE', '2024': 'FAILURE'}
summary {'FAILURE replicada': 8, 'PASS': 0, 'inside_nao_replicado': {}, 'n_pairs': 8, 'não replicado': 0}
ASSERT OK: no PASS without SUCCESS at both seeds; 7 non-target rows per cell
=== SC5
6 passed, 69 deselected in 82.71s (0:01:22)
2da7ba2 results(41-16): phase41_erasure_report.md — dated continuation 2026-10-13 via scripts/_addendum.py (marker "## Provenance", pure append: 10 lines added, 0 removed, the committed 75716e6c prefix byte-identical); no new numb
54ef68c results(41-16): phase41_erasure_report.md — E1 report rendered from results/phase41_erasure.json (byte-equal to render_report), sha256 75716e6c…a46696; Rafael's third stage-2 approved 2026-10-12: "results/phase41_erasure_r
14a0cc6 results(41-16): phase41_erasure.json — E1 erasure record emitted on CPU at 67f4aec (PASS 0, FAILURE replicada 8, não replicado 0), sha256 78d3e4b5…4264d2; Rafael's second stage-2 approved 2026-10-12: "results/phase41_erasu
67f4aec results(41-15): cell_sibling_name_gradient_seed2024 — whole, stop K = 48; cell record + its 4 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
1e82bc0 results(41-15): cell_sibling_name_gradient_seed1337 — whole, stop K = 48; cell record + its 4 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
1fcaa9f results(41-15): cell_street_gradient_seed2024 — whole, stop K = 32; cell record + its 4 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
78c97e0 results(41-15): cell_street_gradient_seed1337 — whole, stop K = 32; cell record + its 3 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
b9f6473 results(41-15): cell_cat_name_gradient_seed2024 — whole, stop K = 48; cell record + its 4 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
d2c5303 results(41-15): cell_cat_name_gradient_seed1337 — whole, stop K = 48; cell record + its 4 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
727ab8f results(41-15): cell_pet_name_gradient_seed2024 — whole, stop K = 32; cell record + its 3 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
5546c06 results(41-15): cell_pet_name_gradient_seed1337 — whole, stop K = 32; cell record + its 3 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
ee37409 results(41-15): cell_sibling_name_greedy_seed2024 — whole, stop K = 64; cell record + its 5 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
d8e97e8 results(41-15): cell_sibling_name_greedy_seed1337 — whole, stop K = 64; cell record + its 7 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
2b4893e results(41-15): cell_street_greedy_seed2024 — whole, stop K = 32; cell record + its 3 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
7c82777 results(41-15): cell_street_greedy_seed1337 — whole, stop K = 32; cell record + its 3 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
ce9327a results(41-15): cell_cat_name_greedy_seed2024 — whole, stop K = 48; cell record + its 4 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
4ebe0c6 results(41-15): cell_cat_name_greedy_seed1337 — whole, stop K = 128; cell record + its 7 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
4f4199e results(41-15): cell_pet_name_greedy_seed2024 — whole, stop K = 64; cell record + its 6 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
ab79f87 results(41-15): cell_pet_name_greedy_seed1337 — whole, stop K = 64; cell record + its 6 K = 16 / K = 48 records; Rafael's first stage-2 approved 2026-10-12
b42900d results(41-13): E1 stage-1 records — four calibration and four band-input records (MPS at f2b9c0d; floors 0.0911 reachability-min x4, control gaps equal to Phase 40); Rafael's first approved 2026-10-09
```

Every `results/phase41_*` commit names Rafael's approved (b42900d stage 1; ab79f87..67f4aec first stage-2; 14a0cc6 second; 54ef68c third; 2da7ba2 his reply to the addendum text).

## Hand-close edits for the orchestrator (not made here)

- `.planning/ROADMAP.md`: line 1445 `- [ ] **Phase 41: …**` → `[x]` with the completion date; plan list lines 1940, 1944, 1948 (41-14, 41-15, 41-16) `[ ]` → `[x]`; the progress table row for Phase 41, if present.
- `.planning/REQUIREMENTS.md`: lines 737–744 ERASE-03..ERASE-10 `[ ]` → `[x]`; traceability rows 820–827 `Pending` → `Complete`.
- `.planning/STATE.md`: frontmatter `stopped_at`, `last_updated`, `last_activity`, `progress.completed_phases` 6 → 7, `completed_plans` 64 → 67, `percent`; Current Position (Phase 41 COMPLETE 16/16, next Phase 42), keeping the guarded superseded records verbatim.
- No gsd-sdk `state.*`, `roadmap.*`, `phase.*` or `requirements.mark-complete` handler was called.

## Obsidian

The project-note entry is the orchestrator's and is **pending** at the time of this SUMMARY.
