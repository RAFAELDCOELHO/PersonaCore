---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 13
subsystem: erasure-stage1-commit
tags: [phase41, e1, stage1, floors, band, erase-06, erase-09]
requires: [41-12]
provides:
  - committed stage-1 ledger lines and eight records; scripts/phase41_floors_prereg.py (16 floors, 4 bands)
key-files:
  created: [scripts/phase41_floors_prereg.py, tests/test_phase41_floors_prereg.py]
  modified: [ledger/v6_mps_ledger.jsonl, tests/test_phase41_erasure.py]
requirements-completed: []
---

# 41-13 — Stage-1 records committed under Rafael's first approved; floors and band filled

`requirements-completed: []` — ERASE-06/ERASE-09's written floors and band exist now; the IDs close with the phase.

## Task 1 — Rafael's reply (verbatim, 2026-10-09)

```
approved

Primeiro aprovado do estágio 1 da Fase 41: o ledger (8 linhas), os 8 registros (4 de calibração, 4 de banda) e depois scripts/phase41_floors_prereg.py com o seu teste, nessa ordem.

Para o SUMMARY, como leituras descritivas, sem regra:
1. D-12: no fato de calibração, a ordenação adaptativa chegou à parada em k = 82 (1337) e 84 (2024), contra 187 e 250 da ordenação atual, com correlação de postos de 0,9908 e 0,9879 entre as duas ordens no adaptador intacto. A diferença vem da reordenação por checkpoint. É a regra de parada por rank no fato de calibração, não a geração no alvo.
2. O primeiro gradiente em MPS teve razão backward/forward de 70,3, acima da folga de 55,6 do texto; os quatro seguintes ficaram entre 6,1 e 7,4. O custo total (1,22 s) ficou muito abaixo do preço, e a regra da variante não é afetada.
3. A ordenação atual levou 419,32 s e 431,07 s em MPS, um pouco acima do preço de 417,56 s da Fase 36. Nas 8 células dessa ordenação isso soma poucos minutos.
4. Os quatro pisos de (a) saíram em wilson(0,27) = 0,0911: o WR-01 se confirma, e (a) é vazia na parada.
```

The values shown to him were printed from the files (41-12-SUMMARY "Results", 5cffa60).

### Descriptive readings (no rule), with the orchestrator's measurement notes

1. D-12 — measured: calibration stop k gradient 82 (1337) / 84 (2024) vs greedy 187 / 250 (results/phase41_calibration_*.json `k`); D-06 Spearman on the intact adapter 0.9907838314665895 (1337), 0.987948048659923 (2024). **Note:** "a diferença vem da reordenação por checkpoint" is an inference, not a measurement — stage 1 ran no static-gradient calibration (gradient ranking without re-ranking), so the re-ranking effect is not isolated; the readings are consistent with it. The stop is the calibration's rank stop, not generation on a target.
2. First MPS gradient backward/forward ratio 70.31013133676312 > BACKWARD_FORWARD_CEILING 55.6; the next four 6.06-7.35; mps_seconds 1.2165203749900684 vs ordering_bound 417.56158900260925 (data/phase41_e1/variant.json, copied into the erasure record by 4d521a8); the variant rule reads total seconds and is unaffected.
3. Greedy ordering on MPS 419.3242446249933 s and 431.0668067499937 s vs the Phase 36 price 417.56158900260925 s. **Note:** "poucos minutos" over the 8 greedy cells is an estimate (excess per calibration 1.76 s and 13.51 s, ~1-2 min over 8 cells if a cell's greedy ordering costs about what the calibration's did; the CPU rehearsal had cell 728.6 s vs calibration 820.7 s).
4. All four (a) floors 0.09107873950450847 = wilson(0, 27), branch reachability-min, calibration 0/23 everywhere — WR-01 confirmed: (a) is vacuous at the judged stop.

## Task 2 — commits (in order, nothing between)

- `24af191` ledger(41-13): the 8 E1 stage-1 lines (four prep start/end pairs; E1 3569.963436 s). `tests/test_phase36_ledger.py` 45 passed.
- `b42900d` results(41-13): the four calibration and four band-input records (paths resolved by `phase41_prereg.unit_record` / `band_record`, equal to files_modified). `test_phase35_prereg.py -k slot_ordering` 3 passed; `test_phase41_prereg.py -k "frozen or first_added"` 2 passed.
- `b8c0e81` feat(41-13): `scripts/phase41_floors_prereg.py` + `tests/test_phase41_floors_prereg.py` (executor). Acceptance print `16 4`; every floor (0.09107873950450847, 'reachability-min'); bands (1337, greedy|gradient) (0.6210483312521959, 1.4102360698263419), (2024, greedy|gradient) (0.6184411071680209, 1.4050216216579918). Fill file has no number literal (path prepend via a list expression instead of `sys.path.insert(0, …)`); its path inserts mirror phase41_prereg's (phase38_sizes_prereg has none — plan wording). sha256 6aaf2423e2c07fb8d8de117ec2433e46838a71d6db81c6e10bd8b29e381f2aa8; test cb278aedc3f26c30ab82a0263830569ca55d59d3d445f23ba2e74859d5aa113d (12 tests).

## Task 3 — latent reds and the full suite

- After b8c0e81 four tests in tests/test_phase41_erasure.py went red (test_preflight_stage_logic, test_tracked_and_clean_reads_git, test_run_stage_gates, test_emit_is_write_once_and_refuses_a_dirty_tree): the `_e1_rig(real=True)` redirected `_ROOT` to tmp but `_tracked_and_clean` still asked the real repo, which now tracks the floors file and the records (Phase 36 pattern). Verified first that nothing real was written (ledger 38 lines, data/phase41_e1 only stage-1 files, clean tree).
- `1fb9193` test(41-13): fixed in the TEST only — the rig answers tracked-state from an empty tmp git repo; the old-state legs moved to a hermetic tmp repo with more cases; test_run_stage_gates asserts the real ledger and every data/phase41_e1 file byte-identical; the autouse guard `_real_tree_untouched` also compares `_real_e1_bytes()` (data/ is gitignored, so git status could not see it). Required set 382 passed.
- Full suite at 1fb9193: `4709 passed, 4 skipped, 83 warnings in 3580.15s (0:59:40)`, `EXIT=0` (previous green 4697/4 at f2b9c0d; skips unchanged).
