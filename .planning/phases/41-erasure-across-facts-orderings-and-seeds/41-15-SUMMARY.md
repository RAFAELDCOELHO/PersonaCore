---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 15
subsystem: erasure-stage2-publish
tags: [phase41, e1, stage2, approvals, erase-03, erase-06, erase-07, erase-09, erase-10]
requires: [41-14]
provides:
  - ledger stage-2 lines committed (37324be) and 16 whole cells committed one per commit (ab79f87..67f4aec), under Rafael's first stage-2 approved
  - results/phase41_erasure.json emitted on CPU at 67f4aec (untracked; sha256 78d3e4b5...4264d2), under Rafael's second approved, for plan 16 to commit alone
key-files:
  created: [results/phase41_erasure.json (untracked; plan 16 commits it)]
  modified: [ledger/v6_mps_ledger.jsonl]
requirements-completed: []
---

# 41-15 — Stage-2 evidence committed write-once; erasure record emitted: 8/8 pairs FAILURE replicada

`requirements-completed: []` — the ERASE IDs close with plan 16.

## Task 1 — first checkpoint (2026-10-12, HEAD b9483e8)

- Approval rule (`ENTRIES['approvals']`): "one approved per launch; stage-1 records under one approved, then the floors fill file committed under it; stage-2 records under three approved: ledger and cell records, the erasure record, the report" (confirmed by Rafael 2026-10-08).
- `unit_outcomes`: 16 whole, 0 dropped, 0 not run → no drop_attempt question. Ledger diff 32 insertions, 0 deletions; sha256 3c90164a20107f12d9ca3c3381431f55a8c312d7e8295813c4f9c8ee6264c4d5. No PAUSE/STOP/lost E1 line; no in-run ruling.
- `phase36_ledger.py report`: E1 116566.123562 s = 32.38 h (stage 1 0.99 h + cells 31.39 h); total 49.14 h; D-23 pause (52.78 h) not reached. Confirmation hours 18.46 h.
- Per cell reads, confirmations, stops, the 8 slot counts at the stop (K = 48 `record_rows`) and the pet_name D-13 blocks were printed from the files and equal the 41-14-SUMMARY tables (hours, reads, stops, slots, D-13 all re-derived; no difference).
- Commit sets (`unit_record` + its `k16_record`s + its confirmation `record`s): 86 paths, 86 unique, 4-8 per cell.

### Rafael's reply (verbatim)

```
approved

Primeiro aprovado do estágio 2 da Fase 41: o ledger (32 linhas, só acréscimo) e os 16 registros de célula com os seus registros K = 16 e K = 48 (86 arquivos), nos commits descritos: o ledger sozinho, depois um commit por célula na ordem de CELL_UNITS, sempre por caminho explícito.
```

## Task 2 — commits (first approved)

| sha | content |
|---|---|
| 37324be | ledger/v6_mps_ledger.jsonl alone |
| ab79f87 | cell_pet_name_greedy_seed1337 (7 files) |
| 4f4199e | cell_pet_name_greedy_seed2024 (7) |
| 4ebe0c6 | cell_cat_name_greedy_seed1337 (8) |
| ce9327a | cell_cat_name_greedy_seed2024 (5) |
| 7c82777 | cell_street_greedy_seed1337 (4) |
| 2b4893e | cell_street_greedy_seed2024 (4) |
| d8e97e8 | cell_sibling_name_greedy_seed1337 (8) |
| ee37409 | cell_sibling_name_greedy_seed2024 (6) |
| 5546c06 | cell_pet_name_gradient_seed1337 (4) |
| 727ab8f | cell_pet_name_gradient_seed2024 (4) |
| d2c5303 | cell_cat_name_gradient_seed1337 (5) |
| b9f6473 | cell_cat_name_gradient_seed2024 (5) |
| 78c97e0 | cell_street_gradient_seed1337 (4) |
| 1fcaa9f | cell_street_gradient_seed2024 (5) |
| 1e82bc0 | cell_sibling_name_gradient_seed1337 (5) |
| 67f4aec | cell_sibling_name_gradient_seed2024 (5) |

Each commit's file count equals its path set (`git show --name-only`). Targeted guards after the ledger: 6 passed; after each cell: 34 passed, 174 deselected.

- Deviation (guard command): the plan's interfaces command passes `-k` twice; pytest keeps only the last, so `slot` / `launch_line` were deselected. The per-cell guards used one `-k "slot or launch_line or frozen or first_added or before"` over the four files (a superset).
- Deviation (mechanics, nothing committed): the first loop ran under zsh (no word splitting) and `git commit -- <untracked>` refuses unknown paths; it failed before any commit. Rerun under bash with `git add -- <set> && git commit -- <set>`.
- Task 2 verify: four files `208 passed`; `git diff --quiet -- ledger/v6_mps_ledger.jsonl` clean; `test_slot_ordering_is_green_on_the_real_repo` + `test_every_tracked_v6_mps_record_has_a_launch_line` 2 passed. `git status --porcelain -- scripts src results tests ledger artifacts` empty. No latent red, no test commit.

## Task 3 — emit (CPU, HEAD 67f4aec) and second checkpoint

`EMIT COMPLETE PASS=0 FAILURE replicada=8 não replicado=0`; results/phase41_erasure.json sha256 78d3e4b52f04c5b37b053e1e1f318b76d0e7afe0fd5d85a51885c559984264d2; provenance git_sha 67f4aec, `'run' in provenance` False; 109 inputs.

- Pairs: all 8 `FAILURE replicada` ("FAILURE na 1337, FAILURE na 2024"). Summary PASS 0 / FAILURE replicada 8 / não replicado 0, inside_nao_replicado {} (no INCONCLUSIVE / NOT_REACHED / NOT_RUN). 4 x 2 x 2 table: FAILURE in all 16.
- Cells: 15 fail (b)+(c); street gradient 2024 fails (b) only ((c) gap 0.674 inside [0.618, 1.405]). (a) holds everywhere and is vacuous at the stop (WR-01: the stop requires 0/27; floor 0.0911). (b) margin 0.296; non-targets beyond it per cell (pre→post /27):

| cell | beyond the margin | (c) gap |
|---|---|---|
| pet greedy 1337 | person 26→0, cat 27→6, sib 27→0, home 21→0, street 27→0, house 24→6 | 0.347 |
| pet greedy 2024 | person 27→0, sib 27→2, home 22→0, street 27→2, by 16→7, house 23→7 | 0.455 |
| pet gradient 1337 | person 26→1, sib 27→11, home 21→0, street 27→7, house 24→13 | 0.535 |
| pet gradient 2024 | person 27→4, sib 27→17, home 22→2, street 27→6, house 23→7 | 0.585 |
| cat greedy 1337 | person 26→0, pet 27→0, sib 27→0, home 21→0, street 27→0, by 18→4, house 24→1 | 0.349 |
| cat greedy 2024 | person 27→2, pet 26→9, sib 27→14, home 22→0, street 27→0, by 16→6, house 23→4 | 0.567 |
| cat gradient 1337 | person 26→0, pet 27→3, sib 27→4, home 21→0, street 27→0, house 24→6 | 0.467 |
| cat gradient 2024 | person 27→1, pet 26→0, sib 27→1, home 22→0, street 27→1, by 16→4, house 23→0 | 0.429 |
| street greedy 1337 | person 26→1, pet 27→14, sib 27→11, home 21→2 | 0.495 |
| street greedy 2024 | person 27→6, home 22→2, house 23→10 | 0.606 |
| street gradient 1337 | person 26→0, pet 27→9, sib 27→14, home 21→2, house 24→14 | 0.496 |
| street gradient 2024 | person 27→10, home 22→3, house 23→9 | 0.674 |
| sibling greedy 1337 | person 26→0, pet 27→3, home 21→0, street 27→6, by 18→9, house 24→9 | 0.328 |
| sibling greedy 2024 | person 27→0, pet 26→2, home 22→0, street 27→3, by 16→5, house 23→4 | 0.377 |
| sibling gradient 1337 | person 26→0, pet 27→2, home 21→0, street 27→2, by 18→9, house 24→8 | 0.315 |
| sibling gradient 2024 | person 27→0, pet 26→6, home 22→0, street 27→0, by 16→6, house 23→1 | 0.488 |

(c) bands: [0.621, 1.410] seed 1337, [0.618, 1.405] seed 2024.

Descriptive readings (none enters a verdict):
- D-12: four floors 0.0911, `reachability-min`, calibration 0/23. D-06 Spearman 0.991 (1337), 0.988 (2024). D-11 seed-1337 calibration adapter tensor-identical (max abs diff 0.0).
- D-14: cap 3.909; "passaria no teto do v4.0" sim in 9 cells, não in 7 (cat 2024 x2, sibling gradient 2024, all 4 street). retention_spread full 0.176, M2 0.227, noise 0.0087.
- D-18: pet_name cells, M1 "fora da faixa" of M2 on all 7 slots; other targets "sem M2, comparação não feita".
- D-19/D-28: labelled "varia entre seeds" birth_year, hometown; (b) would fail on the unlabelled slots alone in every cell.
- D-20/D-21: prediction not held in all 4 pet_name cells — R_q n1 outside M2 on both lists as predicted (committed 11/10/17/17, minted 27), but anchor_512 rank also outside (12/6/2/1 vs 15-41) where inside was predicted; greedy 1337 stopped at 64 with R_q n1 11/27 (repeats Phase 39). A finding, not a failure (prereg).
- Other predictions: greedy 1337 Phase 19 prefix True; d02_cpu_equality None (no CPU gradient; cites 41-11 rehearsal).
- D-26: confirmation hours 18.46.
- Finding disclosed: record `e1_hours` 32.3752 h vs the pre-commit ledger report 32.3795 h (15.5 s). `phase36_ledger.spent()` takes a tracked record's `provenance.run` clock instead of the ledger timestamps (by design; e.g. last cell 5200.90 s vs 5202.30 s).

### Rafael's reply (verbatim)

```
approved

Segundo aprovado do estágio 2 da Fase 41: results/phase41_erasure.json (sha256 78d3e4b52f04c5b37b053e1e1f318b76d0e7afe0fd5d85a51885c559984264d2), commitado sozinho.
```

## Next

Plan 41-16: commit results/phase41_erasure.json alone (sha256 unchanged), full suite, render the report, third approved.
