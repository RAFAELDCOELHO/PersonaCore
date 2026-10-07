# Phase 40 — E2 training-seed noise floor

## Status

Status: **MEASURED**; device mps; whole seeds 1337, 2024, 1338, 2025, 1339; dropped none; not run none.

## Approval and cost (D-11, D-13, D-14)

Rafael's ruling, verbatim:

> aprovo D-11 (+0 h). aprovo D-13 (+0,0609 h). R-1 a. R-2 a. R-3 b. R-4 a. approved

His R-3 b conditions, verbatim:

> Condições do R-3 b: a nova tentativa de uma semente derrubada exige meu approved e uma nota de causa; usa a mesma semente e o mesmo HEAD (ou a mudança é declarada); os resultados parciais da tentativa derrubada são mantidos e listados no registro; se as duas tentativas produzirem o mesmo adaptador, a igualdade tensor a tensor entre elas é reportada. A regra vale só para queda (sem linha de fim), nunca para semente concluída.

His record-total sentence, verbatim:

> No registro, mostre também o total projetado incluindo os extras já aprovados do E5 e do E6, não só o total commitado da Fase 36.

| quantity | hours |
|---|---|
| e2_projection_hours | 7.9518624092864085 |
| committed_front_hours_e2 | 7.890925927716101 |
| e2_stop_hours | 11.83638889157415 |
| committed_total_hours | 77.72433149898184 |
| e2_total_hours | 77.78526798055215 |
| e2_e5_e6_total_hours | 78.12639556620314 |
| e2_e5_e6_total_hours_e6_actual_gate | 78.12556459250179 |

Rulings: R-1 mps-equality, R-2 post, R-3 rerun-as-new-attempt, R-4 seed-record-names-a2; D-11 approved True; D-13 included True (925 NLLs per adapter, 5 adapters).

## Seeds (D-15)

| seed | outcome |
|---|---|
| 1337 | whole |
| 2024 | whole |
| 1338 | whole |
| 2025 | whole |
| 1339 | whole |

Seed 2025 was re-run after a dropped attempt:

- lost line utc: 2026-10-07T12:00:44.878240+00:00
- cause note: - 2026-10-07 03:53:07 local: WindowServer crashed (`WindowServer-2026-10-07-035307.ips`,
  `…userspace_watchdog_timeout.spin`); the GUI login session ended and the gui-domain LaunchAgent
  com.personacore.phase40.e2 died with it. Driver's caffeinate child: ClientDied 03:53:19 (pmset log).
  No traceback in logs/phase40_e2.err (only MallocStackLogging lines). No reboot (boot Jun 8).
- System state: 13 JetsamEvents 22:53–00:16 local with largestProcess fseventsd (~33–34 GiB in rpages),
  then a python3.12 (polymarket-bot collect_negrisk_books.py, 41 days up) ~19–20 GiB and our driver
  10–16 GiB; kills by `vm-compressor-space-shortage`. At 08:59: swap 25.6 / 26.6 GB used, fseventsd
  RSS 8.9 GB (120 days up). The 5x slower a2_full_seed2025 overlaps this memory-pressure window; that it
  caused the slowdown and the WindowServer watchdog is the likely reading, not a measured one.
- No code defect: no fix proposed. HEAD at the crashed launch = c14dfa4 (PREFLIGHT OK line) = Task 2 HEAD.
- Actions taken (Task 4 step 2, rule ii): `launchctl bootout` (exit 0); `phase36_ledger.py reconcile`
  appended the lost line for v6/40/E2/seed2025 (14276.36896 s). Every partial output kept in place
  (phase40_noise.partial_outputs(2025): 4 checkpoints, 4 bins/masks, 2 run.csv, results/phase40_a2_full_seed2025.json).
- seed_outcomes: {1337: whole, 2024: whole, 1338: whole, 2025: dropped, 1339: not_run}; pending (1339,).


- Rafael's approved: Aprovo a nova tentativa da semente 2025 (R-3 b). approved

Os três critérios que escrevi antes da 1339 foram cumpridos: ela terminou inteira, em 1,528 h (limite 1,75 h) e sem evento de falta de memória. Nenhum resultado foi consultado para esta decisão.

Nota de causa: a tentativa anterior caiu às 03:53 quando o WindowServer foi derrubado, com o sistema sob falta de memória (13 eventos Jetsam entre 22:53 e 00:16; swap quase cheio). A relação entre a falta de memória e a queda é a leitura provável, não medida.

Condições, as mesmas do R-3 b: mesma semente e mesmo HEAD (c14dfa4); as saídas parciais da tentativa derrubada vão para data/phase40_dropped/, nunca apagadas, e são listadas com caminho e sha256 nos dois registros; os adaptadores das duas tentativas são comparados tensor a tensor.

Antes do lançamento, o portão registra de novo o estado de memória. O coletor do outro projeto continua parado até a rodada acabar.
- HEAD at the dropped attempt: `c14dfa4f7d36e9dc0048483fa2627700e567206f` beside the seed's git_sha_at_launch `c14dfa4f7d36e9dc0048483fa2627700e567206f`
- declared change: none
- manifest: `data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/manifest.json` sha256 `fa86eb3b935b0fed248de8252cc15a41c568e6c6afaf3d81cb1d862260bcfa2a`

| kept from | kept at | sha256 |
|---|---|---|
| checkpoints/phase40_e2_full_seed2025_adapter.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/checkpoints/phase40_e2_full_seed2025_adapter.pt | 70463d72d04130e86a70de2c7e51f1d726cc4afb052dc59f1d5f616d04a44551 |
| checkpoints/phase40_e2_full_seed2025_latest.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/checkpoints/phase40_e2_full_seed2025_latest.pt | 3b91d1b24695fe10b017789efb8c6a5b3521279fff402234f7ba7c7d51d0c92f |
| checkpoints/phase40_e2_m2_seed2025_adapter.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/checkpoints/phase40_e2_m2_seed2025_adapter.pt | 0a1028cef875f10ab4b6eab950b53cabcfbdab22eba91a8d8e01bd9dfdbfd90d |
| checkpoints/phase40_e2_m2_seed2025_latest.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/checkpoints/phase40_e2_m2_seed2025_latest.pt | 234ca9c7a2631aa0fa08058d39db077ee06c75cb4557c57baa30b9d2f18260ed |
| data/persona_e2_full_seed2025_train.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/data/persona_e2_full_seed2025_train.bin | 69eaf121aa207a40449cb1b01c05eb6add0bf9c1a0eadf18ea6bf77debc4cabe |
| data/persona_e2_full_seed2025_train_mask.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/data/persona_e2_full_seed2025_train_mask.bin | 42287ddc6306c91d541f1473d2e36fdcf8da352fa6b9c883e39d9d3a04a017c1 |
| data/persona_e2_m2_seed2025_train.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/data/persona_e2_m2_seed2025_train.bin | d3f761a9a2e63d66ae92165f570f57004da667c7ae3cc7f630353e84b959c43b |
| data/persona_e2_m2_seed2025_train_mask.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/data/persona_e2_m2_seed2025_train_mask.bin | 114f79a8ae0ab10c83b710d254236b5c10c25d6a1cf8110ec7d17ee29de1bcbc |
| data/phase40_e2/e2_full_seed2025/run.csv | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/data/phase40_e2/e2_full_seed2025/run.csv | 7cc4b8052d5935fe26a0ea7c7284ba979aca73498e5f5356c67af878147f5a73 |
| data/phase40_e2/e2_m2_seed2025/run.csv | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/data/phase40_e2/e2_m2_seed2025/run.csv | 8f6284edc5b6d6e9489af734017397ac265f15ea61c6d4132d2f5b15d3ab91c5 |
| results/phase40_a2_full_seed2025.json | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T120044.878240+0000/results/phase40_a2_full_seed2025.json | 401be575c529077f33cf63340d3151bfbf41730f620d57376910f2a76e288788 |

- full adapter, this attempt vs the dropped one: tensors_identical True (72/72 tensors equal, tensor by tensor)
- m2 adapter, this attempt vs the dropped one: tensors_identical True (72/72 tensors equal, tensor by tensor)

Seed 2025 was re-run after a dropped attempt:

- lost line utc: 2026-10-07T13:57:38.625037+00:00
- cause note: - **Cause, measured:** the plan's waiter (`until grep -qE '^RUN DONE' logs/phase40_e2.out || ! pgrep …`)
  assumes a fresh log; logs/phase40_e2.out is appended across launches and already held the 1339 run's
  `RUN DONE whole=[1339]`. The waiter returned at 10:56:44, ~2.4 min after the 10:54:21 kickstart, with the
  driver alive (pid 36560). Claude ran `launchctl bootout` without checking `pgrep` first: launchd log
  10:56:50.854 `service inactive` / `removing service: com.personacore.phase40.e2`; pmset 10:56:50
  caffeinate 36562 ClientDied (00:02:29). The bootout's SIGTERM killed the driver. Not a system or code fault.
- **State at death:** last heartbeat 13:56:22Z stage `train_m2`; adapters/latest written for full
  (10:54:58) and m2 (10:56:15); no seed record, no `.tmp`; no Traceback; 0 JetsamEvents since kickstart;
  swap 0, 91% free at 10:56:51.
- **Actions (rule ii):** bootout (the fault itself); `phase36_ledger.py reconcile` → lost line
  v6/40/E2/seed2025 utc 2026-10-07T13:57:38.625037Z, 120.011158 s. E2 spent 36391.999727 s = 10.1089 h
  (stop (a) 11.8364 h; left 1.7275 h). Partial outputs kept in place (phase40_noise.partial_outputs(2025),
  10 files: 4 checkpoints, 4 bins/masks, data/phase40_e2/e2_full_seed2025/run.csv,
  results/phase40_e2_m2_seed2025/run.csv). The first attempt's dropped dir is untouched.
- **Proposed fix (operational, no code):** for any relaunch, wait on the driver's exit alone —
  `sleep 120; while pgrep -f "phase40_noise.py run" >/dev/null; do sleep 300; done` — and bootout only
  after `pgrep` prints nothing. HEAD stays c14dfa4.
- A third attempt for 2025 is Rafael's decision (R-3 b: his approved + this note); it would run
  drop_attempt again (new dir keyed by the 13:57:38 lost line) and the relaunch gate.

- Rafael's approved: approved

Aprovo a terceira tentativa da semente 2025 (R-3 b), com a nota de causa do 40-09-SUMMARY: erro de operação, não do sistema nem do código. Nenhum resultado foi consultado para esta decisão.

Condições:
1. Mesma semente e mesmo HEAD (c14dfa4). drop_attempt em diretório novo, ligado à linha lost das 13:57:38Z. O diretório da primeira tentativa fica intocado.
2. Esta é a última tentativa. Se ela cair, por qualquer causa, o piso sai com as quatro sementes inteiras.
3. O limite fica como está commitado, checado só antes da semente. Se o total passar de 11,836 h, a rodada termina e o excesso entra com o número no registro e no relatório.
4. Espera: só pela saída do driver. Antes do bootout, duas checagens independentes: o PID anotado no kickstart não existe mais (ps -p) e o pgrep está vazio. "Terminou inteira" se lê na linha end do ledger, nunca no log.
5. Comparação tensor a tensor entre as três tentativas. O adaptador M2 da segunda só entra se o run.csv dela mostrar o treino completo; senão fica registrado como incompleto, sem comparação.
6. Registro e relatório contam as três tentativas, as duas causas e as horas perdidas em cada uma.
7. O portão registra o estado de memória antes do lançamento; o coletor continua parado.
- HEAD at the dropped attempt: `c14dfa4f7d36e9dc0048483fa2627700e567206f` beside the seed's git_sha_at_launch `c14dfa4f7d36e9dc0048483fa2627700e567206f`
- declared change: none
- manifest: `data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/manifest.json` sha256 `64393527b6a5c40d64d30af827167071f4fc1344430af907df91337d87308b96`

| kept from | kept at | sha256 |
|---|---|---|
| checkpoints/phase40_e2_full_seed2025_adapter.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/checkpoints/phase40_e2_full_seed2025_adapter.pt | 70463d72d04130e86a70de2c7e51f1d726cc4afb052dc59f1d5f616d04a44551 |
| checkpoints/phase40_e2_full_seed2025_latest.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/checkpoints/phase40_e2_full_seed2025_latest.pt | 3b91d1b24695fe10b017789efb8c6a5b3521279fff402234f7ba7c7d51d0c92f |
| checkpoints/phase40_e2_m2_seed2025_adapter.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/checkpoints/phase40_e2_m2_seed2025_adapter.pt | 0a1028cef875f10ab4b6eab950b53cabcfbdab22eba91a8d8e01bd9dfdbfd90d |
| checkpoints/phase40_e2_m2_seed2025_latest.pt | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/checkpoints/phase40_e2_m2_seed2025_latest.pt | 234ca9c7a2631aa0fa08058d39db077ee06c75cb4557c57baa30b9d2f18260ed |
| data/persona_e2_full_seed2025_train.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/data/persona_e2_full_seed2025_train.bin | 69eaf121aa207a40449cb1b01c05eb6add0bf9c1a0eadf18ea6bf77debc4cabe |
| data/persona_e2_full_seed2025_train_mask.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/data/persona_e2_full_seed2025_train_mask.bin | 42287ddc6306c91d541f1473d2e36fdcf8da352fa6b9c883e39d9d3a04a017c1 |
| data/persona_e2_m2_seed2025_train.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/data/persona_e2_m2_seed2025_train.bin | d3f761a9a2e63d66ae92165f570f57004da667c7ae3cc7f630353e84b959c43b |
| data/persona_e2_m2_seed2025_train_mask.bin | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/data/persona_e2_m2_seed2025_train_mask.bin | 114f79a8ae0ab10c83b710d254236b5c10c25d6a1cf8110ec7d17ee29de1bcbc |
| data/phase40_e2/e2_full_seed2025/run.csv | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/data/phase40_e2/e2_full_seed2025/run.csv | 7cc4b8052d5935fe26a0ea7c7284ba979aca73498e5f5356c67af878147f5a73 |
| results/phase40_e2_m2_seed2025/run.csv | data/phase40_dropped/v6_40_E2_seed2025_2026-10-07T135738.625037+0000/results/phase40_e2_m2_seed2025/run.csv | 8f6284edc5b6d6e9489af734017397ac265f15ea61c6d4132d2f5b15d3ab91c5 |

- full adapter, this attempt vs the dropped one: tensors_identical True (72/72 tensors equal, tensor by tensor)
- m2 adapter, this attempt vs the dropped one: tensors_identical True (72/72 tensors equal, tensor by tensor)

## A2 recall per seed with its denominator (NOISE-01)

Every A2 record of both groups carries config.arm 'retrain' because it names the pinned A2 pass, not a group: phase19_erasure.run_erasure_arm(A2_LABEL, device, adapter_path=<new adapter>, record_path=a2_record(group, seed)) for both groups; A2_LABEL 'retrain' is in PARITY_ASSERTED_ARMS, so assert_phase18_parity runs before the first draw; the group lives in Phase 40's own fields

| seed | group | slot | fact | recall | rate | core_held_out | core_taught |
|---|---|---|---|---|---|---|---|
| 1337 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1337 | full | house_number | cand_house_7412 | 24/27 | 0.8888888888888888 | 10/13 | 14/14 |
| 1337 | full | birth_year | cand_year_1987 | 18/27 | 0.6666666666666666 | 10/13 | 8/14 |
| 1337 | full | hometown | cand_town_brindlemoor | 21/27 | 0.7777777777777778 | 8/13 | 13/14 |
| 1337 | full | pet_name | cand_dog_zorp | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1337 | m2 | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1337 | m2 | house_number | cand_house_7412 | 17/27 | 0.6296296296296297 | 7/13 | 10/14 |
| 1337 | m2 | birth_year | cand_year_1987 | 18/27 | 0.6666666666666666 | 11/13 | 7/14 |
| 1337 | m2 | hometown | cand_town_brindlemoor | 18/27 | 0.6666666666666666 | 7/13 | 11/14 |
| 1337 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 2024 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | person_name | cand_person_quillon | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | full | house_number | cand_house_7412 | 23/27 | 0.8518518518518519 | 9/13 | 14/14 |
| 2024 | full | birth_year | cand_year_1987 | 16/27 | 0.5925925925925926 | 7/13 | 9/14 |
| 2024 | full | hometown | cand_town_brindlemoor | 22/27 | 0.8148148148148148 | 11/13 | 11/14 |
| 2024 | full | pet_name | cand_dog_zorp | 26/27 | 0.9629629629629629 | 13/13 | 13/14 |
| 2024 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2024 | m2 | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 2024 | m2 | house_number | cand_house_7412 | 23/27 | 0.8518518518518519 | 9/13 | 14/14 |
| 2024 | m2 | birth_year | cand_year_1987 | 18/27 | 0.6666666666666666 | 10/13 | 8/14 |
| 2024 | m2 | hometown | cand_town_brindlemoor | 8/27 | 0.2962962962962963 | 5/13 | 3/14 |
| 2024 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 1338 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1338 | full | house_number | cand_house_7412 | 22/27 | 0.8148148148148148 | 9/13 | 13/14 |
| 1338 | full | birth_year | cand_year_1987 | 23/27 | 0.8518518518518519 | 10/13 | 13/14 |
| 1338 | full | hometown | cand_town_brindlemoor | 14/27 | 0.5185185185185185 | 8/13 | 6/14 |
| 1338 | full | pet_name | cand_dog_zorp | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1338 | m2 | person_name | cand_person_quillon | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 1338 | m2 | house_number | cand_house_7412 | 24/27 | 0.8888888888888888 | 10/13 | 14/14 |
| 1338 | m2 | birth_year | cand_year_1987 | 20/27 | 0.7407407407407407 | 9/13 | 11/14 |
| 1338 | m2 | hometown | cand_town_brindlemoor | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 1338 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 2025 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 2025 | full | house_number | cand_house_7412 | 20/27 | 0.7407407407407407 | 8/13 | 12/14 |
| 2025 | full | birth_year | cand_year_1987 | 19/27 | 0.7037037037037037 | 9/13 | 10/14 |
| 2025 | full | hometown | cand_town_brindlemoor | 11/27 | 0.4074074074074074 | 5/13 | 6/14 |
| 2025 | full | pet_name | cand_dog_zorp | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 2025 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 2025 | m2 | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 2025 | m2 | house_number | cand_house_7412 | 21/27 | 0.7777777777777778 | 8/13 | 13/14 |
| 2025 | m2 | birth_year | cand_year_1987 | 25/27 | 0.9259259259259259 | 11/13 | 14/14 |
| 2025 | m2 | hometown | cand_town_brindlemoor | 16/27 | 0.5925925925925926 | 7/13 | 9/14 |
| 2025 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |
| 1339 | full | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | full | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | full | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | full | person_name | cand_person_quillon | 26/27 | 0.9629629629629629 | 12/13 | 14/14 |
| 1339 | full | house_number | cand_house_7412 | 22/27 | 0.8148148148148148 | 9/13 | 13/14 |
| 1339 | full | birth_year | cand_year_1987 | 24/27 | 0.8888888888888888 | 12/13 | 12/14 |
| 1339 | full | hometown | cand_town_brindlemoor | 8/27 | 0.2962962962962963 | 3/13 | 5/14 |
| 1339 | full | pet_name | cand_dog_zorp | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | cat_name | cand_cat_zibby | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | street | cand_street_marrowgate | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | sibling_name | cand_sister_orsala | 27/27 | 1.0 | 13/13 | 14/14 |
| 1339 | m2 | person_name | cand_person_quillon | 25/27 | 0.9259259259259259 | 12/13 | 13/14 |
| 1339 | m2 | house_number | cand_house_7412 | 23/27 | 0.8518518518518519 | 9/13 | 14/14 |
| 1339 | m2 | birth_year | cand_year_1987 | 12/27 | 0.4444444444444444 | 6/13 | 6/14 |
| 1339 | m2 | hometown | cand_town_brindlemoor | 14/27 | 0.5185185185185185 | 8/13 | 6/14 |
| 1339 | m2 | pet_name | cand_dog_zorp | 0/27 | 0.0 | 0/13 | 0/14 |

## Training-seed floor beside v3.0's sampling floor (NOISE-02, D-01..D-05)

- full group floor 0.2962962962962963 (max 0.5185185185185185, min 0.07407407407407407): 5 whole seeds, 10 pairs entered
- m2 group floor 0.3481481481481482 (max 0.6296296296296297, min 0.2222222222222222): 5 whole seeds, 10 pairs entered

Published floor: 0.3481481481481482 (group m2, tie False): 5 whole seeds, 10 pairs entered; beside v3.0's sampling floor 0.14814814814814814; the (b) margin at the gate 0.2962962962962963, not amended (margin_amended False).

Rafael's confirmation g, verbatim:

> Confirmo, com um acréscimo: como todos os adaptadores usam os mesmos números aleatórios e o piso de amostragem do v3.0 usou sorteios independentes, o piso de treino não é um limite superior de 'treino mais amostragem' e pode sair menor que 0,148.

Every adapter is drawn at the same generator states (common random numbers), while v3.0's sampling floor 0.14814814814814814 (results/phase19_noise_floors.json::nontarget_noise_floor.value) used independent draws: under common random numbers the training-seed floor is not an upper bound on training plus sampling and may come out below that value.

## Every pair (D-02, D-04)

| group | seeds | d | deltas |
|---|---|---|---|
| full | 1337, 2024 | 0.07407407407407407 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.03703703703703698, 0.07407407407407407, 0.03703703703703698 |
| full | 1337, 1338 | 0.2592592592592593 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.18518518518518523, 0.2592592592592593 |
| full | 1337, 2025 | 0.3703703703703704 | 0.0, 0.0, 0.0, 0.0, 0.14814814814814814, 0.03703703703703709, 0.3703703703703704 |
| full | 1337, 1339 | 0.4814814814814815 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.2222222222222222, 0.4814814814814815 |
| full | 2024, 1338 | 0.2962962962962963 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.03703703703703709, 0.2592592592592593, 0.2962962962962963 |
| full | 2024, 2025 | 0.4074074074074074 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.11111111111111116, 0.11111111111111116, 0.4074074074074074 |
| full | 2024, 1339 | 0.5185185185185185 | 0.0, 0.0, 0.0, 0.03703703703703709, 0.03703703703703709, 0.2962962962962963, 0.5185185185185185 |
| full | 1338, 2025 | 0.14814814814814814 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.14814814814814814, 0.1111111111111111 |
| full | 1338, 1339 | 0.2222222222222222 | 0.0, 0.0, 0.0, 0.0, 0.0, 0.03703703703703698, 0.2222222222222222 |
| full | 2025, 1339 | 0.18518518518518512 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.18518518518518512, 0.1111111111111111 |
| m2 | 1337, 2024 | 0.37037037037037035 | 0.0, 0.0, 0.0, 0.0, 0.2222222222222222, 0.0, 0.37037037037037035 |
| m2 | 1337, 1338 | 0.2592592592592593 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.2592592592592592, 0.07407407407407407, 0.2592592592592593 |
| m2 | 1337, 2025 | 0.2592592592592593 | 0.0, 0.0, 0.0, 0.0, 0.14814814814814814, 0.2592592592592593, 0.07407407407407407 |
| m2 | 1337, 1339 | 0.2222222222222222 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.2222222222222222, 0.2222222222222222, 0.14814814814814814 |
| m2 | 2024, 1338 | 0.6296296296296297 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.03703703703703698, 0.07407407407407407, 0.6296296296296297 |
| m2 | 2024, 2025 | 0.2962962962962963 | 0.0, 0.0, 0.0, 0.0, 0.07407407407407407, 0.2592592592592593, 0.2962962962962963 |
| m2 | 2024, 1339 | 0.2222222222222222 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.0, 0.2222222222222222, 0.2222222222222222 |
| m2 | 1338, 2025 | 0.33333333333333337 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.11111111111111105, 0.18518518518518523, 0.33333333333333337 |
| m2 | 1338, 1339 | 0.40740740740740744 | 0.0, 0.0, 0.0, 0.0, 0.03703703703703698, 0.2962962962962963, 0.40740740740740744 |
| m2 | 2025, 1339 | 0.4814814814814815 | 0.0, 0.0, 0.0, 0.03703703703703698, 0.07407407407407407, 0.4814814814814815, 0.07407407407407407 |

## Per-slot spread (D-04)

| group | slot | rates | counts | range | sd_sample | sd_population |
|---|---|---|---|---|---|---|
| full | cat_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| full | street | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| full | sibling_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| full | person_name | 0.9629629629629629, 1.0, 0.9629629629629629, 0.9629629629629629, 0.9629629629629629 | 26/27, 27/27, 26/27, 26/27, 26/27 | 0.03703703703703709 | 0.016563466499998465 | 0.014814814814814836 |
| full | house_number | 0.8888888888888888, 0.8518518518518519, 0.8148148148148148, 0.7407407407407407, 0.8148148148148148 | 24/27, 23/27, 22/27, 20/27, 22/27 | 0.14814814814814814 | 0.05493480360811603 | 0.049135182079339264 |
| full | birth_year | 0.6666666666666666, 0.5925925925925926, 0.8518518518518519, 0.7037037037037037, 0.8888888888888888 | 18/27, 16/27, 23/27, 19/27, 24/27 | 0.2962962962962963 | 0.12559870339120868 | 0.11233889546743038 |
| full | hometown | 0.7777777777777778, 0.8148148148148148, 0.5185185185185185, 0.4074074074074074, 0.2962962962962963 | 21/27, 22/27, 14/27, 11/27, 8/27 | 0.5185185185185185 | 0.22740861382235186 | 0.20340044767031082 |
| m2 | cat_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| m2 | street | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| m2 | sibling_name | 1.0, 1.0, 1.0, 1.0, 1.0 | 27/27, 27/27, 27/27, 27/27, 27/27 | 0.0 | 0.0 | 0.0 |
| m2 | person_name | 0.9629629629629629, 0.9629629629629629, 0.9259259259259259, 0.9629629629629629, 0.9259259259259259 | 26/27, 26/27, 25/27, 26/27, 25/27 | 0.03703703703703698 | 0.020286020648339453 | 0.01814436846506055 |
| m2 | house_number | 0.6296296296296297, 0.8518518518518519, 0.8888888888888888, 0.7777777777777778, 0.8518518518518519 | 17/27, 23/27, 24/27, 21/27, 23/27 | 0.2592592592592592 | 0.10343881513902918 | 0.09251848886516144 |
| m2 | birth_year | 0.6666666666666666, 0.6666666666666666, 0.7407407407407407, 0.9259259259259259, 0.4444444444444444 | 18/27, 18/27, 20/27, 25/27, 12/27 | 0.4814814814814815 | 0.17292766711005558 | 0.15467120753941557 |
| m2 | hometown | 0.6666666666666666, 0.2962962962962963, 0.9259259259259259, 0.5925925925925926, 0.5185185185185185 | 18/27, 8/27, 25/27, 16/27, 14/27 | 0.6296296296296297 | 0.2289116613387029 | 0.20474481423830004 |

## gap_noise_floor (D-09, D-10)

gap_noise_floor = 0.08406970366097503 (max 0.18498404632362409): 5 whole seeds, 10 pairs entered; beside the v3.0/v4.0 one-pair floor 0.005214448168350039.

| seeds | abs gap difference |
|---|---|
| 1337, 2024 | 0.005214448168350039 |
| 1337, 1338 | 0.18498404632362409 |
| 1337, 2025 | 0.055594873825977054 |
| 1337, 1339 | 0.05252423196131861 |
| 2024, 1338 | 0.17976959815527405 |
| 2024, 2025 | 0.050380425657627015 |
| 2024, 1339 | 0.047309783792968574 |
| 1338, 2025 | 0.12938917249764703 |
| 1338, 1339 | 0.13245981436230547 |
| 2025, 1339 | 0.003070641864658441 |

M2 group, descriptive, never a verdict: 0.09700889469932665 (max 0.21935615910101536): 5 whole seeds, 10 pairs entered.

| seed | group | device | adapter_on | adapter_off | committed adapter_off | matches | pre adapter_on | pre adapter_off | pre matches | rehearsal | pre_post_equal | gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1337 | full | mps | 5.815445876712191 | 4.573349214207799 | 4.573349214207799 | True | 5.815445876712191 | 4.573349214207799 | True | False | True | 1.2420966625043919 |
| 1337 | m2 | mps | 6.007920892362744 | 4.573349214207799 | 4.573349214207799 | True | 6.007920892362744 | 4.573349214207799 | True | False | True | 1.4345716781549447 |
| 2024 | full | mps | 5.810231428543841 | 4.573349214207799 | 4.573349214207799 | True | 5.810231428543841 | 4.573349214207799 | True | False | True | 1.2368822143360418 |
| 2024 | m2 | mps | 5.932208308291309 | 4.573349214207799 | 4.573349214207799 | True | 5.932208308291309 | 4.573349214207799 | True | False | True | 1.3588590940835097 |
| 1338 | full | mps | 5.630461830388567 | 4.573349214207799 | 4.573349214207799 | True | 5.630461830388567 | 4.573349214207799 | True | False | True | 1.0571126161807678 |
| 1338 | m2 | mps | 5.788564733261729 | 4.573349214207799 | 4.573349214207799 | True | 5.788564733261729 | 4.573349214207799 | True | False | True | 1.2152155190539293 |
| 2025 | full | mps | 5.759851002886214 | 4.573349214207799 | 4.573349214207799 | True | 5.759851002886214 | 4.573349214207799 | True | False | True | 1.1865017886784148 |
| 2025 | m2 | mps | 5.918493453650304 | 4.573349214207799 | 4.573349214207799 | True | 5.918493453650304 | 4.573349214207799 | True | False | True | 1.3451442394425044 |
| 1339 | full | mps | 5.762921644750873 | 4.573349214207799 | 4.573349214207799 | True | 5.762921644750873 | 4.573349214207799 | True | False | True | 1.1895724305430733 |
| 1339 | m2 | mps | 5.964825608944906 | 4.573349214207799 | 4.573349214207799 | True | 5.964825608944906 | 4.573349214207799 | True | False | True | 1.391476394737107 |

## Full x M2 re-reading (D-12, descriptive)

descriptive, never a verdict.

| slot | v3.0 delta_taught_to_m2 | full seed | M2 seed | same seed | m2 - full |
|---|---|---|---|---|---|
| cat_name | 0.0 | 1337 | 1337 | True | 0.0 |
| cat_name | 0.0 | 1337 | 2024 | False | 0.0 |
| cat_name | 0.0 | 1337 | 1338 | False | 0.0 |
| cat_name | 0.0 | 1337 | 2025 | False | 0.0 |
| cat_name | 0.0 | 1337 | 1339 | False | 0.0 |
| cat_name | 0.0 | 2024 | 1337 | False | 0.0 |
| cat_name | 0.0 | 2024 | 2024 | True | 0.0 |
| cat_name | 0.0 | 2024 | 1338 | False | 0.0 |
| cat_name | 0.0 | 2024 | 2025 | False | 0.0 |
| cat_name | 0.0 | 2024 | 1339 | False | 0.0 |
| cat_name | 0.0 | 1338 | 1337 | False | 0.0 |
| cat_name | 0.0 | 1338 | 2024 | False | 0.0 |
| cat_name | 0.0 | 1338 | 1338 | True | 0.0 |
| cat_name | 0.0 | 1338 | 2025 | False | 0.0 |
| cat_name | 0.0 | 1338 | 1339 | False | 0.0 |
| cat_name | 0.0 | 2025 | 1337 | False | 0.0 |
| cat_name | 0.0 | 2025 | 2024 | False | 0.0 |
| cat_name | 0.0 | 2025 | 1338 | False | 0.0 |
| cat_name | 0.0 | 2025 | 2025 | True | 0.0 |
| cat_name | 0.0 | 2025 | 1339 | False | 0.0 |
| cat_name | 0.0 | 1339 | 1337 | False | 0.0 |
| cat_name | 0.0 | 1339 | 2024 | False | 0.0 |
| cat_name | 0.0 | 1339 | 1338 | False | 0.0 |
| cat_name | 0.0 | 1339 | 2025 | False | 0.0 |
| cat_name | 0.0 | 1339 | 1339 | True | 0.0 |
| street | 0.0 | 1337 | 1337 | True | 0.0 |
| street | 0.0 | 1337 | 2024 | False | 0.0 |
| street | 0.0 | 1337 | 1338 | False | 0.0 |
| street | 0.0 | 1337 | 2025 | False | 0.0 |
| street | 0.0 | 1337 | 1339 | False | 0.0 |
| street | 0.0 | 2024 | 1337 | False | 0.0 |
| street | 0.0 | 2024 | 2024 | True | 0.0 |
| street | 0.0 | 2024 | 1338 | False | 0.0 |
| street | 0.0 | 2024 | 2025 | False | 0.0 |
| street | 0.0 | 2024 | 1339 | False | 0.0 |
| street | 0.0 | 1338 | 1337 | False | 0.0 |
| street | 0.0 | 1338 | 2024 | False | 0.0 |
| street | 0.0 | 1338 | 1338 | True | 0.0 |
| street | 0.0 | 1338 | 2025 | False | 0.0 |
| street | 0.0 | 1338 | 1339 | False | 0.0 |
| street | 0.0 | 2025 | 1337 | False | 0.0 |
| street | 0.0 | 2025 | 2024 | False | 0.0 |
| street | 0.0 | 2025 | 1338 | False | 0.0 |
| street | 0.0 | 2025 | 2025 | True | 0.0 |
| street | 0.0 | 2025 | 1339 | False | 0.0 |
| street | 0.0 | 1339 | 1337 | False | 0.0 |
| street | 0.0 | 1339 | 2024 | False | 0.0 |
| street | 0.0 | 1339 | 1338 | False | 0.0 |
| street | 0.0 | 1339 | 2025 | False | 0.0 |
| street | 0.0 | 1339 | 1339 | True | 0.0 |
| sibling_name | 0.0 | 1337 | 1337 | True | 0.0 |
| sibling_name | 0.0 | 1337 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 1337 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 1337 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 1337 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 2024 | True | 0.0 |
| sibling_name | 0.0 | 2024 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 2024 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 1338 | True | 0.0 |
| sibling_name | 0.0 | 1338 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 1338 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 2025 | 2025 | True | 0.0 |
| sibling_name | 0.0 | 2025 | 1339 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 1337 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 2024 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 1338 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 2025 | False | 0.0 |
| sibling_name | 0.0 | 1339 | 1339 | True | 0.0 |
| person_name | 0.0 | 1337 | 1337 | True | 0.0 |
| person_name | 0.0 | 1337 | 2024 | False | 0.0 |
| person_name | 0.0 | 1337 | 1338 | False | -0.03703703703703698 |
| person_name | 0.0 | 1337 | 2025 | False | 0.0 |
| person_name | 0.0 | 1337 | 1339 | False | -0.03703703703703698 |
| person_name | 0.0 | 2024 | 1337 | False | -0.03703703703703709 |
| person_name | 0.0 | 2024 | 2024 | True | -0.03703703703703709 |
| person_name | 0.0 | 2024 | 1338 | False | -0.07407407407407407 |
| person_name | 0.0 | 2024 | 2025 | False | -0.03703703703703709 |
| person_name | 0.0 | 2024 | 1339 | False | -0.07407407407407407 |
| person_name | 0.0 | 1338 | 1337 | False | 0.0 |
| person_name | 0.0 | 1338 | 2024 | False | 0.0 |
| person_name | 0.0 | 1338 | 1338 | True | -0.03703703703703698 |
| person_name | 0.0 | 1338 | 2025 | False | 0.0 |
| person_name | 0.0 | 1338 | 1339 | False | -0.03703703703703698 |
| person_name | 0.0 | 2025 | 1337 | False | 0.0 |
| person_name | 0.0 | 2025 | 2024 | False | 0.0 |
| person_name | 0.0 | 2025 | 1338 | False | -0.03703703703703698 |
| person_name | 0.0 | 2025 | 2025 | True | 0.0 |
| person_name | 0.0 | 2025 | 1339 | False | -0.03703703703703698 |
| person_name | 0.0 | 1339 | 1337 | False | 0.0 |
| person_name | 0.0 | 1339 | 2024 | False | 0.0 |
| person_name | 0.0 | 1339 | 1338 | False | -0.03703703703703698 |
| person_name | 0.0 | 1339 | 2025 | False | 0.0 |
| person_name | 0.0 | 1339 | 1339 | True | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1337 | 1337 | True | -0.2592592592592592 |
| house_number | -0.2592592592592592 | 1337 | 2024 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1337 | 1338 | False | 0.0 |
| house_number | -0.2592592592592592 | 1337 | 2025 | False | -0.11111111111111105 |
| house_number | -0.2592592592592592 | 1337 | 1339 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 2024 | 1337 | False | -0.2222222222222222 |
| house_number | -0.2592592592592592 | 2024 | 2024 | True | 0.0 |
| house_number | -0.2592592592592592 | 2024 | 1338 | False | 0.03703703703703698 |
| house_number | -0.2592592592592592 | 2024 | 2025 | False | -0.07407407407407407 |
| house_number | -0.2592592592592592 | 2024 | 1339 | False | 0.0 |
| house_number | -0.2592592592592592 | 1338 | 1337 | False | -0.18518518518518512 |
| house_number | -0.2592592592592592 | 1338 | 2024 | False | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 1338 | 1338 | True | 0.07407407407407407 |
| house_number | -0.2592592592592592 | 1338 | 2025 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1338 | 1339 | False | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 2025 | 1337 | False | -0.11111111111111105 |
| house_number | -0.2592592592592592 | 2025 | 2024 | False | 0.11111111111111116 |
| house_number | -0.2592592592592592 | 2025 | 1338 | False | 0.14814814814814814 |
| house_number | -0.2592592592592592 | 2025 | 2025 | True | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 2025 | 1339 | False | 0.11111111111111116 |
| house_number | -0.2592592592592592 | 1339 | 1337 | False | -0.18518518518518512 |
| house_number | -0.2592592592592592 | 1339 | 2024 | False | 0.03703703703703709 |
| house_number | -0.2592592592592592 | 1339 | 1338 | False | 0.07407407407407407 |
| house_number | -0.2592592592592592 | 1339 | 2025 | False | -0.03703703703703698 |
| house_number | -0.2592592592592592 | 1339 | 1339 | True | 0.03703703703703709 |
| birth_year | 0.0 | 1337 | 1337 | True | 0.0 |
| birth_year | 0.0 | 1337 | 2024 | False | 0.0 |
| birth_year | 0.0 | 1337 | 1338 | False | 0.07407407407407407 |
| birth_year | 0.0 | 1337 | 2025 | False | 0.2592592592592593 |
| birth_year | 0.0 | 1337 | 1339 | False | -0.2222222222222222 |
| birth_year | 0.0 | 2024 | 1337 | False | 0.07407407407407407 |
| birth_year | 0.0 | 2024 | 2024 | True | 0.07407407407407407 |
| birth_year | 0.0 | 2024 | 1338 | False | 0.14814814814814814 |
| birth_year | 0.0 | 2024 | 2025 | False | 0.33333333333333337 |
| birth_year | 0.0 | 2024 | 1339 | False | -0.14814814814814814 |
| birth_year | 0.0 | 1338 | 1337 | False | -0.18518518518518523 |
| birth_year | 0.0 | 1338 | 2024 | False | -0.18518518518518523 |
| birth_year | 0.0 | 1338 | 1338 | True | -0.11111111111111116 |
| birth_year | 0.0 | 1338 | 2025 | False | 0.07407407407407407 |
| birth_year | 0.0 | 1338 | 1339 | False | -0.40740740740740744 |
| birth_year | 0.0 | 2025 | 1337 | False | -0.03703703703703709 |
| birth_year | 0.0 | 2025 | 2024 | False | -0.03703703703703709 |
| birth_year | 0.0 | 2025 | 1338 | False | 0.03703703703703698 |
| birth_year | 0.0 | 2025 | 2025 | True | 0.2222222222222222 |
| birth_year | 0.0 | 2025 | 1339 | False | -0.2592592592592593 |
| birth_year | 0.0 | 1339 | 1337 | False | -0.2222222222222222 |
| birth_year | 0.0 | 1339 | 2024 | False | -0.2222222222222222 |
| birth_year | 0.0 | 1339 | 1338 | False | -0.14814814814814814 |
| birth_year | 0.0 | 1339 | 2025 | False | 0.03703703703703709 |
| birth_year | 0.0 | 1339 | 1339 | True | -0.4444444444444444 |
| hometown | -0.11111111111111116 | 1337 | 1337 | True | -0.11111111111111116 |
| hometown | -0.11111111111111116 | 1337 | 2024 | False | -0.4814814814814815 |
| hometown | -0.11111111111111116 | 1337 | 1338 | False | 0.14814814814814814 |
| hometown | -0.11111111111111116 | 1337 | 2025 | False | -0.18518518518518523 |
| hometown | -0.11111111111111116 | 1337 | 1339 | False | -0.2592592592592593 |
| hometown | -0.11111111111111116 | 2024 | 1337 | False | -0.14814814814814814 |
| hometown | -0.11111111111111116 | 2024 | 2024 | True | -0.5185185185185185 |
| hometown | -0.11111111111111116 | 2024 | 1338 | False | 0.11111111111111116 |
| hometown | -0.11111111111111116 | 2024 | 2025 | False | -0.2222222222222222 |
| hometown | -0.11111111111111116 | 2024 | 1339 | False | -0.2962962962962963 |
| hometown | -0.11111111111111116 | 1338 | 1337 | False | 0.14814814814814814 |
| hometown | -0.11111111111111116 | 1338 | 2024 | False | -0.2222222222222222 |
| hometown | -0.11111111111111116 | 1338 | 1338 | True | 0.40740740740740744 |
| hometown | -0.11111111111111116 | 1338 | 2025 | False | 0.07407407407407407 |
| hometown | -0.11111111111111116 | 1338 | 1339 | False | 0.0 |
| hometown | -0.11111111111111116 | 2025 | 1337 | False | 0.25925925925925924 |
| hometown | -0.11111111111111116 | 2025 | 2024 | False | -0.1111111111111111 |
| hometown | -0.11111111111111116 | 2025 | 1338 | False | 0.5185185185185186 |
| hometown | -0.11111111111111116 | 2025 | 2025 | True | 0.18518518518518517 |
| hometown | -0.11111111111111116 | 2025 | 1339 | False | 0.1111111111111111 |
| hometown | -0.11111111111111116 | 1339 | 1337 | False | 0.37037037037037035 |
| hometown | -0.11111111111111116 | 1339 | 2024 | False | 0.0 |
| hometown | -0.11111111111111116 | 1339 | 1338 | False | 0.6296296296296297 |
| hometown | -0.11111111111111116 | 1339 | 2025 | False | 0.2962962962962963 |
| hometown | -0.11111111111111116 | 1339 | 1339 | True | 0.2222222222222222 |

## Determinism check (D-07, descriptive)

descriptive, never a verdict: every comparison is tensor by tensor, never the file sha256.

| new adapter vs committed | reading |
|---|---|
| full_seed1337 | tensors_identical True (72/72 tensors equal, tensor by tensor) |
| full_seed2024 | tensors_identical True (72/72 tensors equal, tensor by tensor) |
| m2_seed1337 | tensors_identical True (72/72 tensors equal, tensor by tensor) |

M2@1337 A2 counts vs results/phase19_arm_retrain.json, label: none (tensor-identical)

| slot | new | committed | delta |
|---|---|---|---|
| cat_name | 27/27 | 27/27 | 0 |
| street | 27/27 | 27/27 | 0 |
| sibling_name | 27/27 | 27/27 | 0 |
| person_name | 26/27 | 26/27 | 0 |
| house_number | 17/27 | 17/27 | 0 |
| birth_year | 18/27 | 18/27 | 0 |
| hometown | 18/27 | 18/27 | 0 |
| pet_name | 0/27 | 0/27 | 0 |

draw identity: bit_identical True, 0/10368 completions and 0/216 entries differ

## persona_adapter.pt correction and the Phase 18 residual (D-08, D-08b)

persona_adapter.pt and the Phase 19 dialogue-floor seed-1337 adapter are the same adapter (every tensor torch.equal, identical metadata; the file sha256 differs only by the file name torch.save writes into the zip); the record and the milestone report state this as a CORRECTION of the scout note, not as a v3.0 limitation; emit re-measures it on CPU

persona_adapter.pt vs the dialogue-floor seed-1337 adapter, re-measured: tensors_identical True (72/72 tensors equal, tensor by tensor)

D-08b outcome NO_RESIDUAL, max abs rate difference 0.0 (full@1337 vs the Phase 18 run_arm counts):

| slot | new | committed | delta |
|---|---|---|---|
| cat_name | 27/27 | 27/27 | 0 |
| street | 27/27 | 27/27 | 0 |
| sibling_name | 27/27 | 27/27 | 0 |
| person_name | 26/27 | 26/27 | 0 |
| house_number | 24/27 | 24/27 | 0 |
| birth_year | 18/27 | 18/27 | 0 |
| hometown | 21/27 | 21/27 | 0 |
| pet_name | 27/27 | 27/27 | 0 |

draw identity: bit_identical True, 0/10368 completions and 0/216 entries differ

## Target rank across the M2 seeds (D-13, descriptive)

descriptive, never a verdict. Measured seeds: 1337, 2024, 1338, 2025, 1339.

| seed | anchor gate rank | A2 exposure rank | R_q committed n1/n | R_q minted n1/n |
|---|---|---|---|---|
| 1337 | 2 | 2 | 0/27 | 11/27 |
| 2024 | 1 | 1 | 0/27 | 10/27 |
| 1338 | 2 | 2 | 0/27 | 9/27 |
| 2025 | 1 | 1 | 1/27 | 11/27 |
| 1339 | 1 | 1 | 1/27 | 12/27 |

## Predictions recorded before the run

| prediction | as written | observed | criterion |
|---|---|---|---|
| tensor_identity | M2@1337 tensor-equal to checkpoints/phase19_erase_reference_adapter.pt; full@1337 to phase14_recall.ADAPTER_PATH; full@2024 to the dialogue-floor seed-2024 adapter | {"full_seed1337": true, "full_seed2024": true, "m2_seed1337": true} | False |
| gap_pair | \|gap(1337) - gap(2024)\| over the full group equals phase19_floor.DIALOGUE_PPL_NOISE_FLOOR | {"abs_gap_difference": 0.005214448168350039, "beside": 0.005214448168350039, "devices": ["mps", "mps"], "rehearsal": [false, false]} | False |
| m2_counts | M2@1337 A2 counts equal results/phase19_arm_retrain.json's (phase19_erasure.arm_record_path('retrain')) | true | False |
| full_counts | full@1337 A2 counts equal the Phase 18 run_arm counts (D-08b NO_RESIDUAL) | true | False |
| status | recorded before any Phase 40 run; descriptive; a mismatch is a finding, not a failure | MEASURED | False |

## Provenance

- seed 1337 run: device mps, finished_utc 2026-10-06T23:52:09.566908+00:00, git_sha_at_end c14dfa4f7d36e9dc0048483fa2627700e567206f, git_sha_at_launch c14dfa4f7d36e9dc0048483fa2627700e567206f, head_moved_during_run False, started_utc 2026-10-06T22:20:06.706114+00:00, torch_version 2.7.1

Seed 1337: The CPU rehearsal ran seeds [1337, 2024] on this prereg before the MPS run; 9 commit(s) touched a disclosed module since it.
- rehearsal git sha `dfa116251f4c4366eee8f910df91e91537cede3b`, launch git sha `c14dfa4f7d36e9dc0048483fa2627700e567206f`
- changed modules: scripts/phase40_noise.py
- `0b5c9669aacd71380aab22047a7946ea7c9627b6` fix(40-09): IN-05 emit lists a dropped seed's own seed record among its in-place outputs — in the WR-01 state that record sat untracked and excluded but was never named in the noise-floor record (touched: scripts/phase40_noise.py)
- `c250f0893aa6069690a92932506b5ca3bf25a949` fix(40-09): IN-04 d13_scores returns malformed_reading for a wrong NLL count — it raised SystemExit, which run() recorded as failure_kind 'exception' (touched: scripts/phase40_noise.py)
- `6b81ae49b766402afa8b910d5fd82f31ba411d3b` fix(40-09): IN-03 partial_outputs lists the seed record's atomic-write temp file — a SIGKILL mid-write left results/.phase40_seed<k>.json.<rand>.tmp that drop_attempt never moved, so only a hand deletion cleared it (touched: scripts/phase40_noise.py)
- `892065af662d5619d8a836aa5c29c8bed4199150` fix(40-09): IN-02 train_adapter tolerates a non-empty csv directory after the move — a stray file there (e.g. .DS_Store) made rmdir raise after training and dropped the paid-for seed (touched: scripts/phase40_noise.py)
- `cdd30c23a3d14f1ef245bc5dbe2068f8d79a472f` fix(40-09): IN-01 render_report leaves one blank line, never two — the D-13 section (no seed not measured) and each dropped attempt's kept-files table rendered a double blank line (touched: scripts/phase40_noise.py)
- `b3f64f0c80a9272eeacf58a05e30ebfe56a4f555` fix(40-09): WR-04 preflight imports every MODULES file before taking module_sha256 — phase39_ctx was first imported ~3 h later inside seed 1337's D-13, after the launch digest the seed records publish (touched: scripts/phase40_noise.py)
- `d1a41958883242426be42b062eaf9ebad379dd50` fix(40-09): WR-03 the D-13 handler's own _release() is guarded — an empty_cache failing after an MPS error escaped ruling c's catch and dropped a finished seed (touched: scripts/phase40_noise.py)
- `cf685c4ed8d18e835193a706a03acfddc8958d53` fix(40-09): WR-02 emit, drop_attempt and declare_relaunch share preflight's root/ledger guard — emit(ledger_path=other) on the real root wrote the write-once record from the wrong ledger (touched: scripts/phase40_noise.py)
- `11c7e8c8e7efc72710a5b5214bbb2d263b99e138` fix(40-09): WR-01 preflight names crash rule (i) for an open seed whose record exists — its old refusal suggested reconcile, which strands a finished seed for good (touched: scripts/phase40_noise.py)

- seed 2024 run: device mps, finished_utc 2026-10-07T01:24:03.641483+00:00, git_sha_at_end c14dfa4f7d36e9dc0048483fa2627700e567206f, git_sha_at_launch c14dfa4f7d36e9dc0048483fa2627700e567206f, head_moved_during_run False, started_utc 2026-10-06T23:52:11.807639+00:00, torch_version 2.7.1

Seed 2024: The CPU rehearsal ran seeds [1337, 2024] on this prereg before the MPS run; 9 commit(s) touched a disclosed module since it.
- rehearsal git sha `dfa116251f4c4366eee8f910df91e91537cede3b`, launch git sha `c14dfa4f7d36e9dc0048483fa2627700e567206f`
- changed modules: scripts/phase40_noise.py
- `0b5c9669aacd71380aab22047a7946ea7c9627b6` fix(40-09): IN-05 emit lists a dropped seed's own seed record among its in-place outputs — in the WR-01 state that record sat untracked and excluded but was never named in the noise-floor record (touched: scripts/phase40_noise.py)
- `c250f0893aa6069690a92932506b5ca3bf25a949` fix(40-09): IN-04 d13_scores returns malformed_reading for a wrong NLL count — it raised SystemExit, which run() recorded as failure_kind 'exception' (touched: scripts/phase40_noise.py)
- `6b81ae49b766402afa8b910d5fd82f31ba411d3b` fix(40-09): IN-03 partial_outputs lists the seed record's atomic-write temp file — a SIGKILL mid-write left results/.phase40_seed<k>.json.<rand>.tmp that drop_attempt never moved, so only a hand deletion cleared it (touched: scripts/phase40_noise.py)
- `892065af662d5619d8a836aa5c29c8bed4199150` fix(40-09): IN-02 train_adapter tolerates a non-empty csv directory after the move — a stray file there (e.g. .DS_Store) made rmdir raise after training and dropped the paid-for seed (touched: scripts/phase40_noise.py)
- `cdd30c23a3d14f1ef245bc5dbe2068f8d79a472f` fix(40-09): IN-01 render_report leaves one blank line, never two — the D-13 section (no seed not measured) and each dropped attempt's kept-files table rendered a double blank line (touched: scripts/phase40_noise.py)
- `b3f64f0c80a9272eeacf58a05e30ebfe56a4f555` fix(40-09): WR-04 preflight imports every MODULES file before taking module_sha256 — phase39_ctx was first imported ~3 h later inside seed 1337's D-13, after the launch digest the seed records publish (touched: scripts/phase40_noise.py)
- `d1a41958883242426be42b062eaf9ebad379dd50` fix(40-09): WR-03 the D-13 handler's own _release() is guarded — an empty_cache failing after an MPS error escaped ruling c's catch and dropped a finished seed (touched: scripts/phase40_noise.py)
- `cf685c4ed8d18e835193a706a03acfddc8958d53` fix(40-09): WR-02 emit, drop_attempt and declare_relaunch share preflight's root/ledger guard — emit(ledger_path=other) on the real root wrote the write-once record from the wrong ledger (touched: scripts/phase40_noise.py)
- `11c7e8c8e7efc72710a5b5214bbb2d263b99e138` fix(40-09): WR-01 preflight names crash rule (i) for an open seed whose record exists — its old refusal suggested reconcile, which strands a finished seed for good (touched: scripts/phase40_noise.py)

- seed 1338 run: device mps, finished_utc 2026-10-07T02:55:06.445898+00:00, git_sha_at_end c14dfa4f7d36e9dc0048483fa2627700e567206f, git_sha_at_launch c14dfa4f7d36e9dc0048483fa2627700e567206f, head_moved_during_run False, started_utc 2026-10-07T01:24:06.711880+00:00, torch_version 2.7.1

Seed 1338: The CPU rehearsal ran seeds [1337, 2024] on this prereg before the MPS run; 9 commit(s) touched a disclosed module since it.
- rehearsal git sha `dfa116251f4c4366eee8f910df91e91537cede3b`, launch git sha `c14dfa4f7d36e9dc0048483fa2627700e567206f`
- changed modules: scripts/phase40_noise.py
- `0b5c9669aacd71380aab22047a7946ea7c9627b6` fix(40-09): IN-05 emit lists a dropped seed's own seed record among its in-place outputs — in the WR-01 state that record sat untracked and excluded but was never named in the noise-floor record (touched: scripts/phase40_noise.py)
- `c250f0893aa6069690a92932506b5ca3bf25a949` fix(40-09): IN-04 d13_scores returns malformed_reading for a wrong NLL count — it raised SystemExit, which run() recorded as failure_kind 'exception' (touched: scripts/phase40_noise.py)
- `6b81ae49b766402afa8b910d5fd82f31ba411d3b` fix(40-09): IN-03 partial_outputs lists the seed record's atomic-write temp file — a SIGKILL mid-write left results/.phase40_seed<k>.json.<rand>.tmp that drop_attempt never moved, so only a hand deletion cleared it (touched: scripts/phase40_noise.py)
- `892065af662d5619d8a836aa5c29c8bed4199150` fix(40-09): IN-02 train_adapter tolerates a non-empty csv directory after the move — a stray file there (e.g. .DS_Store) made rmdir raise after training and dropped the paid-for seed (touched: scripts/phase40_noise.py)
- `cdd30c23a3d14f1ef245bc5dbe2068f8d79a472f` fix(40-09): IN-01 render_report leaves one blank line, never two — the D-13 section (no seed not measured) and each dropped attempt's kept-files table rendered a double blank line (touched: scripts/phase40_noise.py)
- `b3f64f0c80a9272eeacf58a05e30ebfe56a4f555` fix(40-09): WR-04 preflight imports every MODULES file before taking module_sha256 — phase39_ctx was first imported ~3 h later inside seed 1337's D-13, after the launch digest the seed records publish (touched: scripts/phase40_noise.py)
- `d1a41958883242426be42b062eaf9ebad379dd50` fix(40-09): WR-03 the D-13 handler's own _release() is guarded — an empty_cache failing after an MPS error escaped ruling c's catch and dropped a finished seed (touched: scripts/phase40_noise.py)
- `cf685c4ed8d18e835193a706a03acfddc8958d53` fix(40-09): WR-02 emit, drop_attempt and declare_relaunch share preflight's root/ledger guard — emit(ledger_path=other) on the real root wrote the write-once record from the wrong ledger (touched: scripts/phase40_noise.py)
- `11c7e8c8e7efc72710a5b5214bbb2d263b99e138` fix(40-09): WR-01 preflight names crash rule (i) for an open seed whose record exists — its old refusal suggested reconcile, which strands a finished seed for good (touched: scripts/phase40_noise.py)

- seed 2025 run: device mps, finished_utc 2026-10-07T15:38:35.679799+00:00, git_sha_at_end c14dfa4f7d36e9dc0048483fa2627700e567206f, git_sha_at_launch c14dfa4f7d36e9dc0048483fa2627700e567206f, head_moved_during_run False, started_utc 2026-10-07T14:06:17.992889+00:00, torch_version 2.7.1

Seed 2025: The CPU rehearsal ran seeds [1337, 2024] on this prereg before the MPS run; 9 commit(s) touched a disclosed module since it.
- rehearsal git sha `dfa116251f4c4366eee8f910df91e91537cede3b`, launch git sha `c14dfa4f7d36e9dc0048483fa2627700e567206f`
- changed modules: scripts/phase40_noise.py
- `0b5c9669aacd71380aab22047a7946ea7c9627b6` fix(40-09): IN-05 emit lists a dropped seed's own seed record among its in-place outputs — in the WR-01 state that record sat untracked and excluded but was never named in the noise-floor record (touched: scripts/phase40_noise.py)
- `c250f0893aa6069690a92932506b5ca3bf25a949` fix(40-09): IN-04 d13_scores returns malformed_reading for a wrong NLL count — it raised SystemExit, which run() recorded as failure_kind 'exception' (touched: scripts/phase40_noise.py)
- `6b81ae49b766402afa8b910d5fd82f31ba411d3b` fix(40-09): IN-03 partial_outputs lists the seed record's atomic-write temp file — a SIGKILL mid-write left results/.phase40_seed<k>.json.<rand>.tmp that drop_attempt never moved, so only a hand deletion cleared it (touched: scripts/phase40_noise.py)
- `892065af662d5619d8a836aa5c29c8bed4199150` fix(40-09): IN-02 train_adapter tolerates a non-empty csv directory after the move — a stray file there (e.g. .DS_Store) made rmdir raise after training and dropped the paid-for seed (touched: scripts/phase40_noise.py)
- `cdd30c23a3d14f1ef245bc5dbe2068f8d79a472f` fix(40-09): IN-01 render_report leaves one blank line, never two — the D-13 section (no seed not measured) and each dropped attempt's kept-files table rendered a double blank line (touched: scripts/phase40_noise.py)
- `b3f64f0c80a9272eeacf58a05e30ebfe56a4f555` fix(40-09): WR-04 preflight imports every MODULES file before taking module_sha256 — phase39_ctx was first imported ~3 h later inside seed 1337's D-13, after the launch digest the seed records publish (touched: scripts/phase40_noise.py)
- `d1a41958883242426be42b062eaf9ebad379dd50` fix(40-09): WR-03 the D-13 handler's own _release() is guarded — an empty_cache failing after an MPS error escaped ruling c's catch and dropped a finished seed (touched: scripts/phase40_noise.py)
- `cf685c4ed8d18e835193a706a03acfddc8958d53` fix(40-09): WR-02 emit, drop_attempt and declare_relaunch share preflight's root/ledger guard — emit(ledger_path=other) on the real root wrote the write-once record from the wrong ledger (touched: scripts/phase40_noise.py)
- `11c7e8c8e7efc72710a5b5214bbb2d263b99e138` fix(40-09): WR-01 preflight names crash rule (i) for an open seed whose record exists — its old refusal suggested reconcile, which strands a finished seed for good (touched: scripts/phase40_noise.py)

- seed 1339 run: device mps, finished_utc 2026-10-07T13:46:15.602338+00:00, git_sha_at_end c14dfa4f7d36e9dc0048483fa2627700e567206f, git_sha_at_launch c14dfa4f7d36e9dc0048483fa2627700e567206f, head_moved_during_run False, started_utc 2026-10-07T12:14:36.732101+00:00, torch_version 2.7.1

Seed 1339: The CPU rehearsal ran seeds [1337, 2024] on this prereg before the MPS run; 9 commit(s) touched a disclosed module since it.
- rehearsal git sha `dfa116251f4c4366eee8f910df91e91537cede3b`, launch git sha `c14dfa4f7d36e9dc0048483fa2627700e567206f`
- changed modules: scripts/phase40_noise.py
- `0b5c9669aacd71380aab22047a7946ea7c9627b6` fix(40-09): IN-05 emit lists a dropped seed's own seed record among its in-place outputs — in the WR-01 state that record sat untracked and excluded but was never named in the noise-floor record (touched: scripts/phase40_noise.py)
- `c250f0893aa6069690a92932506b5ca3bf25a949` fix(40-09): IN-04 d13_scores returns malformed_reading for a wrong NLL count — it raised SystemExit, which run() recorded as failure_kind 'exception' (touched: scripts/phase40_noise.py)
- `6b81ae49b766402afa8b910d5fd82f31ba411d3b` fix(40-09): IN-03 partial_outputs lists the seed record's atomic-write temp file — a SIGKILL mid-write left results/.phase40_seed<k>.json.<rand>.tmp that drop_attempt never moved, so only a hand deletion cleared it (touched: scripts/phase40_noise.py)
- `892065af662d5619d8a836aa5c29c8bed4199150` fix(40-09): IN-02 train_adapter tolerates a non-empty csv directory after the move — a stray file there (e.g. .DS_Store) made rmdir raise after training and dropped the paid-for seed (touched: scripts/phase40_noise.py)
- `cdd30c23a3d14f1ef245bc5dbe2068f8d79a472f` fix(40-09): IN-01 render_report leaves one blank line, never two — the D-13 section (no seed not measured) and each dropped attempt's kept-files table rendered a double blank line (touched: scripts/phase40_noise.py)
- `b3f64f0c80a9272eeacf58a05e30ebfe56a4f555` fix(40-09): WR-04 preflight imports every MODULES file before taking module_sha256 — phase39_ctx was first imported ~3 h later inside seed 1337's D-13, after the launch digest the seed records publish (touched: scripts/phase40_noise.py)
- `d1a41958883242426be42b062eaf9ebad379dd50` fix(40-09): WR-03 the D-13 handler's own _release() is guarded — an empty_cache failing after an MPS error escaped ruling c's catch and dropped a finished seed (touched: scripts/phase40_noise.py)
- `cf685c4ed8d18e835193a706a03acfddc8958d53` fix(40-09): WR-02 emit, drop_attempt and declare_relaunch share preflight's root/ledger guard — emit(ledger_path=other) on the real root wrote the write-once record from the wrong ledger (touched: scripts/phase40_noise.py)
- `11c7e8c8e7efc72710a5b5214bbb2d263b99e138` fix(40-09): WR-01 preflight names crash rule (i) for an open seed whose record exists — its old refusal suggested reconcile, which strands a finished seed for good (touched: scripts/phase40_noise.py)

- emit: device cpu, head at write `c14dfa4f7d36e9dc0048483fa2627700e567206f`, written 2026-10-07T16:02:18.494885+00:00
- modules changed since launch: none
