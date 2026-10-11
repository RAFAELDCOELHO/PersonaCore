---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 14
subsystem: erasure-stage2-run
tags: [phase41, e1, stage2, cells, mps, erase-03, erase-04, erase-05, erase-07, erase-08, erase-10]
requires: [41-13]
provides:
  - 16 whole E1 cells on MPS at 5f158d3 (16 cell, 48 K = 16, 22 K = 48 records) and their ledger lines, UNCOMMITTED for plan 15
key-files:
  created: []
  modified: [ledger/v6_mps_ledger.jsonl (uncommitted)]
requirements-completed: []
---

# 41-14 — Stage 2 ran whole on MPS: 16/16 cells, no PAUSE, no STOP, no crash

`requirements-completed: []` — ERASE-03/04/05/07/10 are measured; the IDs close with the phase. Nothing was
committed by this plan except this SUMMARY (no crash, so no crash fix). The records and the ledger stay
untracked/modified for plan 15's first approved.

## Task 1 — Stage-2 launch gate (pre-reboot, measured 2026-10-09, HEAD 5f158d3)

- Tree clean (`git status --porcelain -- scripts src results tests ledger artifacts` = 0). Since the green suite at 1fb9193 (`4709 passed, 4 skipped`, EXIT=0, 41-13-SUMMARY) only .planning/ROADMAP.md, .planning/STATE.md, 41-13-SUMMARY.md changed.
- Pins `git log --oneline 3787b9d..HEAD -- scripts/teach_persona.py scripts/phase19_erasure.py scripts/phase14_recall.py scripts/phase18_extraction.py scripts/phase14_factset.py scripts/phase37_routes.py scripts/phase40_noise.py scripts/phase40_prereg.py src/personacore/` empty.
- Jobs: no PersonaCore agent with a PID; pgrep empty. Collector: `launchctl print system/com.polybot.negrisk-books` → "Bad request.", no collect_negrisk.
- Memory 2026-10-09T17:28:29Z: swap 0; 76% free. Jetsam baseline: newest JetsamEvent is `DiagnosticReports/Retired/JetsamEvent-2026-10-09-084122.ips` (08:41). **Correction:** the pre-reboot note said "no JetsamEvent present (rotated away)"; the file was moved to `Retired/`, not deleted (found at the post-reboot gate with `find`).
- Ledger 38 lines; E1 3569.114223 s = 0.9914 h (tracked records' provenance.run clocks; phase36_ledger.py:278-312, by design).
- Identity data/phase41_rehearsal.json git_sha 075f5ea; since then only 4d521a8 (emit-only, Rafael's 41-12 ruling) touched the driver → every cell record carries `rehearsal_disclosure` (verified on a cell record: `driver_changed: True`, `prereg_changed: False`, `launch_git_sha 5f158d3…`). sha256: driver a5ee8d45619b36db4018906c4419d5be998ac4a2ac162786e0bcab100bccbf56, prereg 11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3, floors 6aaf2423e2c07fb8d8de117ec2433e46838a71d6db81c6e10bd8b29e381f2aa8.
- 9 tracked: scripts/phase41_floors_prereg.py + 4 calibration + 4 band_inputs records.
- IN-02 manual check: data/phase41_e1/variant.json exists, sha256 311a87dd87e06bd8e40e740f8876544aa4c1380656eea5e8158f2d1b9f7a567c: variant adaptive, variant_decided_by mps_smoke, cpu_seconds 0.09196808400156442, mps_seconds 1.2165203749900684, ordering_bound 417.56158900260925, rehearsal false, d02 5x difference 0.0 equal True.
- `PREFLIGHT OK 5f158d3d4854165198218b89b72a4ba731b2d362 device=mps stage=2 pending=<16 CELL_UNITS in D-22 order> variant=adaptive spent_E1_h=0.9914`.

## Task 2 — Rafael's reply (verbatim, 2026-10-09)

```
approved

Lançamento do estágio 2 da Fase 41 (as 16 células) em 5f158d3, como no aviso, com uma condição antes do kickstart:

1. Reiniciar o Mac.
2. Depois do reinício, refazer só a parte rápida do portão: HEAD igual a 5f158d3 e árvore limpa; nenhum job do PersonaCore; o coletor ausente (ele pode voltar no boot; se voltar, parar antes de seguir); estado de memória e o evento de memória mais recente gravados no SUMMARY; PREFLIGHT OK em mps com as 16 células pendentes e spent_E1_h igual ao de agora. A suíte completa não precisa rodar de novo, porque a árvore não muda.
3. Lançar com a espera no PID do driver e as duas checagens de saída antes do bootout.

A pausa do D-23 em 52,78 h é checada antes de cada célula, como descrito. Durante a rodada, só leio o log pelas linhas de marco, nunca por leituras parciais de resultado.
```

### Post-reboot quick gate (Rafael's step 2, measured 2026-10-09)

- Boot 2026-10-09 15:21:53 local (18:21:53Z), after the 17:30Z pre-reboot gate. HEAD 5f158d3d4854165198218b89b72a4ba731b2d362, porcelain 0 (checked before and after the collector removal).
- Jobs: 12 com.personacore.* labels loaded in gui/ (launchd reads ~/Library/LaunchAgents at login), none with a PID; `pgrep -fl "pytest|phase3[0-9]_|phase4[0-9]_"` empty.
- Collector **returned at boot**: `system/com.polybot.negrisk-books` loaded, collect_negrisk_books.py PID 537 at ~7.7 GB RSS three minutes after boot. Gate STOPPED (Rafael's "se voltar, parar antes de seguir"); Rafael ran `sudo launchctl bootout system/com.polybot.negrisk-books`; re-check → "Bad request.", no collect_negrisk.
- Memory 2026-10-09T18:25:37Z: `vm.swapusage` total 0 used 0; `memory_pressure` 93% free; top RSS claude 1.0 GB, Terminal 0.2 GB; load 18.5 (post-boot Spotlight). Newest JetsamEvent: Retired/JetsamEvent-2026-10-09-084122.ips, mtime 2026-10-09T08:41:22 (none since).
- `PREFLIGHT OK 5f158d3d4854165198218b89b72a4ba731b2d362 device=mps stage=2 pending=cell_pet_name_greedy_seed1337,cell_pet_name_greedy_seed2024,cell_cat_name_greedy_seed1337,cell_cat_name_greedy_seed2024,cell_street_greedy_seed1337,cell_street_greedy_seed2024,cell_sibling_name_greedy_seed1337,cell_sibling_name_greedy_seed2024,cell_pet_name_gradient_seed1337,cell_pet_name_gradient_seed2024,cell_cat_name_gradient_seed1337,cell_cat_name_gradient_seed2024,cell_street_gradient_seed1337,cell_street_gradient_seed2024,cell_sibling_name_gradient_seed1337,cell_sibling_name_gradient_seed2024 variant=adaptive spent_E1_h=0.9914` (torch 2.7.1), EXIT 0. No full suite (Rafael: the tree does not change).

## Task 3 — launch, wait, exit

- Launch 2026-10-09T18:25:45Z: plist identical to artifacts/ (`cmp`); `launchctl bootstrap` rc=5 (the label was already loaded at login — expected), `kickstart` rc=0. Driver PID 14475 (ppid 1), caffeinate -dims child PID 14485. Log before kickstart: 51 lines, `^RUN DONE` count 1.
- One launch, one block: no PAUSE, no STOP, no crash, no relaunch, no drop_attempt. While waiting only milestone lines (`CELL`/`UNIT`/`RUN DONE`/error signatures) were read.
- Driver exit 2026-10-11 ~01:55Z (`RUN DONE whole=[…16 cells in D-22 order…]`; `^RUN DONE` count 2). Exit check 1: `ps -p 14475` fails. Exit check 2 first matched PID 15248 — the orchestrator's own launch-time PID waiter (a zsh whose command text ends with `pgrep -fl "phase41_erasure.py run"`, then in its last `sleep 300`); bootout was withheld until it exited, then both checks passed (`pgrep -f "phase41_erasure\.py[ ]run"` empty) and `launchctl bootout gui/501/com.personacore.phase41.e1` rc=0 (print → "Bad request.").
- `unit_outcomes(read_ledger(), CELL_UNITS)`: all 16 `whole` (`16 whole`).

### Ledger (`phase36_ledger.py report`)

`closed_seconds_by_front`: E1 116566.123562 s = 32.3795 h (stage 1 3569.114223 s + the 16 cells 112997.009339 s = 31.3881 h; the 16 end-line seconds sum to the same); E2 41927.365921; E3 0.0; E4 0.0; E5 303.383428; E6 820.420965; R1b 4104.256927; probes 13176.153838; total 176897.704641 s = 49.1383 h. The D-23 pause (52.779745537787676 h E1) was never reached; ledger stops (a) 79.17 h E1 and (b) 90 h total not approached. Every cell end line: `flag "record not yet tracked"` (expected until plan 15), `status closed`, `record` = the cell record path.

### Per cell, from the files (cell record + its K = 16 / K = 48 records; seconds from the ledger end line)

Reads: checkpoint: K = 16 target count n/27, target rank (Z = k16_zero). Confirmations: checkpoint: K = 48 zero or non-0, seconds. Every cell: whole, `judged True`, `stop == e1_stop.stop`, `not_reached_sentence None`, `dropped_attempts []`, adapter `checkpoints/phase40_e2_full_seed<seed>_adapter.pt`.

| cell | variant | ordering s | reads | confirmations | stop | ledger s |
|---|---|---|---|---|---|---|
| pet_name greedy 1337 | — | 367.46 | 16: 6/27 r1; 32: 1/27 r1; 48: 0/27 r1 Z; 64: 0/27 r1 Z | 48: non-0 3458; 64: 0 4360 | 64 | 12651.563243 |
| pet_name greedy 2024 | — | 892.66 | 16: 9/27 r1; 32: 4/27 r1; 48: 0/27 r1 Z; 64: 0/27 r1 Z | 48: non-0 3070; 64: 0 3258 | 64 | 11222.103778 |
| cat_name greedy 1337 | — | 312.88 | 16: 18/27 r1; 32: 1/27 r1; 48: 1/27 r1; 64: 0/27 r2 Z; 128: 0/27 r3 Z | 64: non-0 3396; 128: 0 4255 | 128 | 13270.581113 |
| cat_name greedy 2024 | — | 358.76 | 16: 8/27 r1; 32: 5/27 r1; 48: 0/27 r1 Z | 48: 0 2776 | 48 | 5643.332890 |
| street greedy 1337 | — | 359.43 | 16: 1/27 r1; 32: 0/27 r1 Z | 32: 0 2884 | 32 | 4901.890162 |
| street greedy 2024 | — | 363.16 | 16: 2/27 r1; 32: 0/27 r1 Z | 32: 0 2635 | 32 | 4533.332085 |
| sibling_name greedy 1337 | — | 315.81 | 16: 20/27 r1; 32: 0/27 r1 Z; 48: 0/27 r2 Z; 64: 0/27 r3 Z | 32: non-0 2666; 48: non-0 2648; 64: 0 2623 | 64 | 11471.111902 |
| sibling_name greedy 2024 | — | 313.80 | 16: 26/27 r1; 32: 6/27 r1; 48: 2/27 r2; 64: 0/27 r2 Z | 64: 0 2927 | 64 | 6646.051575 |
| pet_name gradient 1337 | adaptive | 0.56 | 16: 7/27 r1; 32: 0/27 r1 Z | 32: 0 2623 | 32 | 4219.951834 |
| pet_name gradient 2024 | adaptive | 0.41 | 16: 12/27 r1; 32: 0/27 r1 Z | 32: 0 2705 | 32 | 4379.861962 |
| cat_name gradient 1337 | adaptive | 0.95 | 16: 20/27 r1; 32: 1/27 r1; 48: 0/27 r1 Z | 48: 0 3538 | 48 | 6522.388920 |
| cat_name gradient 2024 | adaptive | 0.42 | 16: 10/27 r1; 32: 1/27 r1; 48: 0/27 r1 Z | 48: 0 3178 | 48 | 5886.468248 |
| street gradient 1337 | adaptive | 0.99 | 16: 1/27 r1; 32: 0/27 r1 Z | 32: 0 2995 | 32 | 4723.277915 |
| street gradient 2024 | adaptive | 0.42 | 16: 0/27 r1 Z; 32: 0/27 r1 Z | 16: non-0 2434; 32: 0 2443 | 32 | 6375.443537 |
| sibling_name gradient 1337 | adaptive | 0.96 | 16: 20/27 r1; 32: 4/27 r2; 48: 0/27 r4 Z | 48: 0 2839 | 48 | 5347.354448 |
| sibling_name gradient 2024 | adaptive | 0.42 | 16: 25/27 r1; 32: 5/27 r2; 48: 0/27 r4 Z | 48: 0 2749 | 48 | 5202.295727 |

`variant` is `None` in the greedy cell records (the variant applies to the gradient ordering only) and `adaptive` in all 8 gradient cells (= variant.json). No cell is NOT_REACHED. D-26 held: confirmations continued to the next checkpoint when non-zero, at most one per checkpoint.

### D-13 (pet_name cells, at the stop)

| cell | measured | criterion | R_q committed n1 | R_q minted n1 | anchor_gate |
|---|---|---|---|---|---|
| pet_name greedy 1337 | True | False | 11/27 | 27/27 | rank 1, a2_record_rank 1, equal True |
| pet_name greedy 2024 | True | False | 10/27 | 27/27 | rank 1, a2_record_rank 1, equal True |
| pet_name gradient 1337 | True | False | 17/27 | 27/27 | rank 1, a2_record_rank 1, equal True |
| pet_name gradient 2024 | True | False | 17/27 | 27/27 | rank 1, a2_record_rank 1, equal True |

Non-pet_name cells carry no d13 block (D-13 is pet_name only).

### Slot counts at the stop checkpoint (K = 48 record, `phase41_prereg.record_rows`, n_answerable/27)

| cell | stop | birth_year | cat_name | hometown | house_number | person_name | pet_name | sibling_name | street |
|---|---|---|---|---|---|---|---|---|---|
| pet_name greedy 1337 | 64 | 11 | 6 | 0 | 6 | 0 | 0 | 0 | 0 |
| pet_name greedy 2024 | 64 | 7 | 20 | 0 | 7 | 0 | 0 | 2 | 2 |
| cat_name greedy 1337 | 128 | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| cat_name greedy 2024 | 48 | 6 | 0 | 0 | 4 | 2 | 9 | 14 | 0 |
| street greedy 1337 | 32 | 18 | 25 | 2 | 16 | 1 | 14 | 11 | 0 |
| street greedy 2024 | 32 | 13 | 27 | 2 | 10 | 6 | 26 | 24 | 0 |
| sibling_name greedy 1337 | 64 | 9 | 25 | 0 | 9 | 0 | 3 | 0 | 6 |
| sibling_name greedy 2024 | 64 | 5 | 24 | 0 | 4 | 0 | 2 | 0 | 3 |
| pet_name gradient 1337 | 32 | 11 | 26 | 0 | 13 | 1 | 0 | 11 | 7 |
| pet_name gradient 2024 | 32 | 11 | 21 | 2 | 7 | 4 | 0 | 17 | 6 |
| cat_name gradient 1337 | 48 | 10 | 0 | 0 | 6 | 0 | 3 | 4 | 0 |
| cat_name gradient 2024 | 48 | 4 | 0 | 0 | 0 | 1 | 0 | 1 | 1 |
| street gradient 1337 | 32 | 15 | 25 | 2 | 14 | 0 | 9 | 14 | 0 |
| street gradient 2024 | 32 | 11 | 27 | 3 | 9 | 10 | 21 | 25 | 0 |
| sibling_name gradient 1337 | 48 | 9 | 26 | 0 | 8 | 0 | 2 | 0 | 2 |
| sibling_name gradient 2024 | 48 | 6 | 27 | 0 | 1 | 0 | 6 | 0 | 0 |

Descriptive only; no rule is applied here (plan 15 judges).

### Prediction check — greedy (pet_name, 1337) ordering vs Phase 19

`results/phase19_collateral_curve.json` `ordered_prefix` (78 entries) == the cell's `applied_ordering.ordered[:78]`: **True** (applied_ordering k 78, stopped True; first entries [3,'fc_in',1], [1,'fc_in',7], [1,'fc_in',6], [4,'fc_in',4]).

### Working tree after the run (HEAD 5f158d3)

`git status --porcelain --untracked-files=all`: ` M ledger/v6_mps_ledger.jsonl`; 86 `??` results paths = exactly the set named by the 16 cell records (16 cell + 48 `phase41_k16_*` + 22 `phase41_a2_*`; set equality True); pre-existing and not ours: ` M .claude/scheduled_tasks.lock`, `?? .planning/phases/41-…/.continue-here.md`.

## Deviations

- Monitoring: after two silent 30-min log Monitors (a cell takes 1.2-3.7 h, so silence was expected), the milestone watch was a background waiter exiting on the next `CELL` line(s), a `Traceback|MemoryError|^(PAUSE|STOP|DROPPED)` line, or the driver PID's exit — still milestone lines only. The PID waiter ran throughout.
- Exit check 2's first false match was the orchestrator's own waiter shell (see Task 3); bootout waited for it. Lesson: write the pgrep pattern as `phase41_erasure\.py[ ]run` so it never matches a shell whose command text quotes the pattern.

## Next

Plan 41-15: present the ledger and the 16 cell records with their K = 16 / K = 48 records for Rafael's first approved; then emit; second approved for the erasure record.
