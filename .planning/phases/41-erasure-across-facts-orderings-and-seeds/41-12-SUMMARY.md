---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 12
subsystem: erasure-stage1-mps
tags: [phase41, e1, driver-review, launch-gate, mps, stage1, erase-04, erase-05, erase-06, erase-07]
requires: [41-11]
provides:
  - 41-REVIEW-2.md with Rafael's Resolution (d771c60); emit-only fix 4d521a8
  - stage-1 records on disk (untracked), ledger lines (uncommitted) for plan 13
key-files:
  created: [.planning/phases/41-erasure-across-facts-orderings-and-seeds/41-REVIEW-2.md]
  modified: [scripts/phase41_erasure.py, tests/test_phase41_erasure.py]
requirements-completed: []
---

# 41-12 — Driver review, launch gate, Rafael's approved, stage 1 on MPS

`requirements-completed: []` — 41-12 runs stage 1; the records are committed in 41-13 and the ERASE IDs close at the end of the phase.

## Task 1 — driver review (41-REVIEW-2.md)

REVIEW_BASE 52536b4; gsd-code-reviewer, explicit path 41-REVIEW-2.md: 0 critical, 2 warnings, 5 info (none blocking under Rafael's stopping rule; 178 cross-module calls bind to real signatures).
Rafael's rulings (Resolution 2026-10-09, d771c60, his reply verbatim there): WR-01 known limitation (R-3 b: his approved fix before drop_attempt); WR-02 fixed emit-only; IN-01 (a) — d02_cpu_equality stays None with a reason citing 41-11-SUMMARY.md:172-176 (2098294), the committed quotation of the rehearsal record (the rehearsal records themselves are not committed: scratch roots and the gitignored data/, .gitignore:17); IN-02 known limitation + manual variant.json check at the stage-2 launch gate (plan 14 amended f2b9c0d); IN-03, IN-04 known; IN-05 fixed (variant.json copied into the record, floors file sha256 in inputs, D-11 result in the report).
Fix commit 4d521a8 (emit-only; AST diff: changed `_cell_section`, `build_record`, `render_report`; added `D02_CPU_REHEARSAL_RECORD`, `_DROPPED_SUMMARY_KEYS`, `_dropped_lines`, `_dropped_summary`; preflight / run / run_prep_unit / run_cell / write_cell byte-identical). Driver tests 139 passed; census B1 1373 passed, B2 226 passed / 3 skipped. Driver sha256 a5ee8d45619b36db4018906c4419d5be998ac4a2ac162786e0bcab100bccbf56; disclosed to the launch through rehearsal_disclosure (one commit touched a disclosed module since the rehearsal at 075f5ea).

## Task 2 — launch gate (HEAD f2b9c0d)

1. `git status --porcelain -- scripts src results tests ledger artifacts`: 0 lines. HEAD f2b9c0dfd4fc1f89296b6b7a3adbbaf4c6a9383d.
2. Full suite at f2b9c0d: `4697 passed, 4 skipped, 83 warnings in 3446.63s (0:57:26)`, `EXIT=0` (previous green 4558/4 at f6df669; skips unchanged).
3. Pins: `git log --oneline 3787b9d..HEAD -- scripts/teach_persona.py scripts/phase19_erasure.py scripts/phase14_recall.py scripts/phase18_extraction.py scripts/phase14_factset.py scripts/phase37_routes.py scripts/phase40_noise.py scripts/phase40_prereg.py src/personacore/` printed nothing.
4. Jobs: `launchctl list | grep -i personacore` — every agent `-` (no PID); `pgrep -fl "pytest|phase3[0-9]_|phase4[0-9]_"` empty.
5. Collector: `launchctl print system/com.polybot.negrisk-books` → "Bad request." — the same answer a non-existent label gives on this macOS (`system/com.nonexistent.zzz` → "Bad request."; an existing service such as `system/com.apple.syslogd` prints its block), i.e. absent (Phase 40 saw "Could not find service" for the same state); `pgrep -fl collect_negrisk` empty; boot Wed Oct 7 09:09:17 2026. /Library/LaunchDaemons/com.polybot.negrisk-books.plist still present (restarts at boot).
6. Memory state (gate, and again immediately before kickstart, 2026-10-09T15:03:13Z, Rafael's requested reference): `vm.swapusage: total = 0,00M used = 0,00M free = 0,00M`; `System-wide memory free percentage: 76%` (77% at the gate); top RSS: Grok Bot Helper (Renderer) 654240 KB, WindowServer 195136, Grok Bot Helper 122512, claude 906432, node 619840. Most recent memory event (baseline): `/Library/Logs/DiagnosticReports/JetsamEvent-2026-10-09-084122.ips` (Oct 9 08:41:22 2026), largestProcess `com.apple.Virtualization.Virtual` — the Claude app's Linux VM (Rafael: used for checking the records; up 1 d 23 h; ~0.16 GB in use inside the guest; host RSS measured 112384 KB); it stays on, by Rafael's decision.
7. Ledger report: no open run; closed_seconds_by_front E1 0.0, E2 41927.365921, E5 303.383428, E6 820.420965, R1b 4104.256927, probes 13176.153838 (60331.58 s = 16.76 h total). Ledger 30 lines before kickstart.
8. Identity data/phase41_rehearsal.json: git_sha 075f5ea2125de1ab038135bc672b7dfd2e85e8b4; module_sha256 driver 6f3f5c56693ced814c59404b0572398e5f082ecb18a91dbab79271590f68a907 (rehearsal), prereg 11e432e4… — equal to 41-11-SUMMARY's "Rehearsal identity"; at HEAD the driver is a5ee8d45… (changed only by the disclosed 4d521a8) and the prereg 11e432e479b9a97642e582083f3d0f01cfaa2834bde7f47682c3bbafab4a29a3 = 41-05-SUMMARY's "Frozen prereg"; cpu_ordering_seconds 0.09196808400156442.
9. Record paths: ['results/phase41_calibration_greedy_seed1337.json', 'results/phase41_calibration_gradient_seed1337.json', 'results/phase41_calibration_greedy_seed2024.json', 'results/phase41_calibration_gradient_seed2024.json'] ['results/phase41_band_inputs_greedy_seed1337.json', 'results/phase41_band_inputs_gradient_seed1337.json', 'results/phase41_band_inputs_greedy_seed2024.json', 'results/phase41_band_inputs_gradient_seed2024.json'] — the eight files_modified records.
10. `PREFLIGHT OK f2b9c0dfd4fc1f89296b6b7a3adbbaf4c6a9383d device=mps stage=1 pending=prep_greedy_seed1337,prep_gradient_seed1337,prep_greedy_seed2024,prep_gradient_seed2024 variant=unset spent_E1_h=0.0000`.

### Stops active for this launch (Rafael asked for confirmation)

- D-23 pause on the E1 slice: `ENTRIES["e1_share_hours"]` = 52.779745537787676 h (results/phase36_budget.json front_hours.E1; his decision D-23); `_pause(unit, …)` is checked before every cell's require_launch (scripts/phase41_erasure.py:2027, :2095 → `phase41_prereg.e1_pause_due`). Stage 1 runs only prep units, so the pause guards stage 2; E1 at launch 0.0 h.
- Ledger stop (a): E1 spent above `front_stop_factor` × front_hours.E1 = 79.16961830668151 h (scripts/phase36_ledger.py:341-350, factor read from phase36_prereg.ENTRIES).
- Ledger stop (b): cumulative spent >= stop_line_hours 90 h (:352-358). Stop (c): projection above mps_ceiling_hours (:359-363).
- `phase36_ledger.require_launch(FRONT)` runs in preflight (scripts/phase41_erasure.py:1482) and before every unit (:2097).

## Task 3 — Rafael's reply (verbatim, 2026-10-09)

```
approved

Lançamento do estágio 1 da Fase 41 em f2b9c0d, como no aviso.

A máquina virtual com.apple.Virtualization.VirtualMachine é a do app do Claude, usada para a conferência dos registros (Linux ligado há 1 dia e 23 h, cerca de 0,16 GB em uso); ela fica ligada. Antes do kickstart, gravar no SUMMARY o estado de memória e o nome do evento de memória mais recente (o das 08:41 de hoje), como referência.

Confirme no SUMMARY que a pausa do D-23 na fatia do E1 (52,78 h, decisão minha) está ativa, além da parada em 79,17 h e da de 90 h no total.
```

## Task 4 — launch

- plist identical to artifacts/ (cmp); `launchctl bootstrap` 0; `launchctl kickstart` 0 at 2026-10-09T15:03:19Z.
- Driver PID 96718 (ppid 1; `launchctl print` pid = 96718, state running); caffeinate child holding the assertions: 96724 (`/usr/bin/caffeinate -dims …`, ppid 96718).
- Waiter: `sleep 120; while ps -p 96718 >/dev/null; do sleep 300; done`.
- Log: `VARIANT adaptive decided_by=mps_smoke cpu_s=0.09 mps_s=1.22`.

- data/phase41_e1/variant.json (copied as written): variant "adaptive", variant_decided_by "mps_smoke", cpu_seconds 0.09196808400156442, mps_seconds 1.2165203749900684, ordering_bound 417.56158900260925, rehearsal false; d02 (5 gradients): difference 0.0, equal true at every one (grad = nograd: 0.13365373015403748, 0.9780359268188477, 2.7508699893951416, 3.8310954570770264, 4.706401824951172); timings ratio forward+backward / forward: 70.31013133676312 (at 0), 6.7676717501088035 (16), 6.056343544195066 (32), 6.841577252898955 (48), 7.354011726734443 (64).
- Finding (descriptive, no rule reads it): the first MPS gradient's ratio 70.31 is above `phase41_prereg.BACKWARD_FORWARD_CEILING` 55.6 (the IN-01 headroom text); the later four are 6.1-7.4 (CPU rehearsal: 4.84 then ~2.0) — a first-call warm-up. The variant rule (`alternative_variant`) reads total seconds (1.2165 s <= 417.56 s), so the variant is unaffected; reported to Rafael at 41-13.
- Ledger: start v6/41/E1/prep_greedy_seed1337 at 2026-10-09T15:03:21.529613Z.

- Driver exit: the PID waiter returned; `ps -p 96718` failed AND `pgrep -f "phase41_erasure.py run"` empty (two checks); then `launchctl bootout gui/501/com.personacore.phase41.e1` = 0. Log: `STAGE 1 DONE`, `RUN DONE whole=['prep_greedy_seed1337', 'prep_gradient_seed1337', 'prep_greedy_seed2024', 'prep_gradient_seed2024']`.

## Results (read from the files)

- Unit outcomes (`phase41_prereg.unit_outcomes` over the ledger): all four `whole`; 8 new ledger lines (4 start/end pairs), no lost line, no open run. Per unit (end - start): prep_greedy_seed1337 1156.8 s, prep_gradient_seed1337 599.8 s, prep_greedy_seed2024 1206.6 s, prep_gradient_seed2024 606.7 s. `phase36_ledger.py report`: E1 3569.963436 s (0.9917 h) of the 52.78 h share; total closed 63901.54 s.
- Every calibration record: provenance.run device mps, git_sha_at_launch = git_sha_at_end = f2b9c0d, head_moved_during_run False, torch 2.7.1; applied ordering length 288; band records carry no provenance.run.

| unit | k | stopped | ordering_seconds (MPS) | calibration rate | floor (branch) |
|---|---|---|---|---|---|
| greedy 1337 | 187 | True | 419.3242446249933 | 0/23 | 0.09107873950450847 (reachability-min) |
| gradient 1337 | 82 | True | 7.089815417013597 | 0/23 | 0.09107873950450847 (reachability-min) |
| greedy 2024 | 250 | True | 431.0668067499937 | 0/23 | 0.09107873950450847 (reachability-min) |
| gradient 2024 | 84 | True | 7.287177915975917 | 0/23 | 0.09107873950450847 (reachability-min) |

(floors from `phase35_prereg.fill("e1_condition_a_floors", **phase41_prereg.floors_fill_inputs())` on the untracked records; `d12_rows` printed the same; every target's floor equals its (ordering, seed) row — WR-01: (a) vacuous at a judged stop. Greedy 1337 k = 187 equals Phase 19's calibration k.)
- Bands (`fill("e1_condition_c_band_inputs", **band_fill_inputs())`): (1337, greedy) and (1337, gradient) (0.6210483312521959, 1.4102360698263419); (2024, greedy) and (2024, gradient) (0.6184411071680209, 1.4050216216579918). Control gaps re-measured on mps: 1337 1.2420966625043919, 2024 1.2368822143360418 — `equal` True against Phase 40's committed gap in all four band records.
- D-11 (prediction: the new seed-1337 calibration adapter tensor-identical to the Phase 19 one): reference_sha256_matches_record True; seed 1337 `tensors_identical` True, 72/72 equal, every max abs diff 0.0 — **prediction held**. Seed 2024 (not part of the prediction; reference is the 1337 adapter): 0/72 equal, as expected for a different seed.
- D-06 Spearman (greedy vs gradient d06_order, per seed): 1337 0.9907838314665895; 2024 0.987948048659923.
- Greedy ordering cost on MPS 419.32 / 431.07 s vs the Phase 36 price 417.56 s (descriptive; the variant rule reads the gradient ordering's cost, 1.2165 s in the smoke).
- `git status --porcelain`: ` M .claude/scheduled_tasks.lock` (harness), ` M ledger/v6_mps_ledger.jsonl`, and `??` for the eight records — nothing else. Nothing committed in this plan after the review fixes (4d521a8, d771c60) and the plan-14 amendment (f2b9c0d) except this SUMMARY.

## Deviations

- Task 1 review and Task 2-4 gate/launch run by the orchestrator; the emit-only fixes by an executor.
- The collector check reads "Bad request." on this macOS for an absent label (measured against a nonexistent label), not "Could not find service".

