---
phase: 40-m2-seed-noise-floor
plan: 01
subsystem: approvals
tags: [approvals, d-11, d-13, r-1, r-2, r-3, r-4, noise-01, noise-02]
requires:
  - results/phase36_budget.json
  - .planning/phases/40-m2-seed-noise-floor/40-01..40-11-PLAN.md
provides:
  - 40-CONTEXT.md "### Approvals" section, committed alone at 03de080
affects:
  - plan 02 (verbatim tests read the Approvals bullets at 03de080; APPROVAL_KEYS must add the E5/E6 record total)
  - plans 02/03/06/07/09/10 (R-3 b conditions)
key-files:
  created: []
  modified:
    - .planning/phases/40-m2-seed-noise-floor/40-CONTEXT.md
requirements-completed: []
completed: 2026-10-05
---

# Phase 40 Plan 01: Approvals Summary

Rafael approved D-11 (+0 h) and D-13 (+0.0609 h), ruled R-1 a, R-2 a, R-3 b (with conditions) and R-4 a, and approved the plan set. Every number in the notice was re-measured at 75e0fd7 before he saw it.

## Approvals commit

03de080 — `.planning/phases/40-m2-seed-noise-floor/40-CONTEXT.md` only.

## Rafael's reply (verbatim, pasted; proposto pelo Claude (claude.ai), adotado por Rafael)

```
aprovo D-11 (+0 h). aprovo D-13 (+0,0609 h). R-1 a. R-2 a. R-3 b. R-4 a. approved

Condições do R-3 b: a nova tentativa de uma semente derrubada exige meu approved e uma nota de causa; usa a mesma semente e o mesmo HEAD (ou a mudança é declarada); os resultados parciais da tentativa derrubada são mantidos e listados no registro; se as duas tentativas produzirem o mesmo adaptador, a igualdade tensor a tensor entre elas é reportada. A regra vale só para queda (sem linha de fim), nunca para semente concluída.

No registro, mostre também o total projetado incluindo os extras já aprovados do E5 e do E6, não só o total commitado da Fase 36.
```

The reply has three paragraphs; the CONTEXT quotes each one verbatim on its own one-line bullet (`Approvals reply (verbatim)` = the first paragraph, which is the line plan 02's test reads; `R-3 b conditions (verbatim)`; `Record total (verbatim)`).

## Deviations

- **Notice fix (F-1):** the plan's approve-both cons line said "about 45 s per seed"; measured, 5 x 925 x 0.009824592875647667 s = 45.43874204987046 s in total (about 9 s per seed). Rafael saw the corrected line; recorded in the Approvals section.
- **F-2 (record shape, no number changes):** results/phase19_dialogue_floor.json recipe carries a sixth key `arms` the interface did not list; the five listed keys match.
- **Record total (Rafael's third paragraph), premise measured:** both E5 and E6 have approved extras. fsum(front_hours with E2 7.9518624092864085, E5 phase38_prereg.E5_PROJECTION_HOURS 0.467956566879681, E6 phase39_prereg.E6_PROJECTION_HOURS 0.7293568082878159) = 78.12639556620314 h (78.12556459250179 h with E6_PROJECTION_HOURS_ACTUAL_GATE 0.7285258345864714); committed 77.72433149898184 h.
- **R-3 b conditions** are not all in the plan set as written (records listing the dropped attempt's partial outputs, per-attempt HEAD, tensor equality between attempts' adapters). Plans 02/03/06/07/09/10 are revised before plan 02 runs.

## Task 1: re-measurement (commands and outputs, HEAD 75e0fd7)

All commands run from /Users/juliorcoelho/PersonaCore with `.venv/bin/python` (3.11 venv).
Groups 1-5 and 6's require_launch use the scratch script
`/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/d19c6c2a-db59-41c1-946c-681523a61ee9/scratchpad/g1_5.py <group>`
(sys.path[:0] = ['scripts', 'src']; read-only; source kept beside this draft).

Pre-check: `git status --porcelain -- scripts src results tests ledger` -> empty (rc 0). HEAD 75e0fd7.

## Group 1 — Budget (`g1_5.py 1`)
E2 formula in `_front_seconds` term order: `e2["seeds"] * (p["e2_train_m2_high"] + p["e2_train_full_high"] + e2["adapters"] * p["e2_a2_pass_high"])` (scripts/phase36_budget.py), /3600.
```
unit_caps.E2 {'adapters': 2, 'seeds': 5}
prices {'e2_train_m2_high': 76.1114059574902, 'e2_train_full_high': 80.83857736012175, 'e2_a2_pass_high': 2762.25834231899, 'adapter_setup_high': 0.6376663325354457, 'e5_nll_high': 0.046742270700633526}
E2 formula 7.890925927716101 front_hours.E2 7.890925927716101 equal True
front_stop_factor 1.5 stop(a) 11.83638889157415
total_hours 77.72433149898184 e2_seed_count 5
fsum(front_hours) 77.72433149898184
```

## Group 2 — D-13 terms (`g1_5.py 2`)
```
TARGET_SLOT pet_name size 512 sizes [8, 32, 128, 512] minted 511
refs 8 q 27 N_TARGET_QUESTIONS 27 MINTED_SET_SIZE 8
n 925
d13_hours 0.06093648157030758 E2 projection 7.9518624092864085 new total 77.78526798055215
```
Extra (the notice's "about 45 s at Phase 38's measured MPS rate", RESEARCH M14):
```
$ .venv/bin/python -c "... r=json.load(open('results/phase38_rank.json')) ..."
phase38 provenance.run {'device': 'mps', 'finished_utc': '2026-10-04T18:58:57.142378+00:00', 'git_sha_at_end': 'ccd5d7e0...', 'git_sha_at_launch': 'ccd5d7e0...', 'head_moved_during_run': False, 'started_utc': '2026-10-04T18:53:53.758950+00:00', 'torch_version': '2.7.1'}
rate 303.383428/30880 = 0.009824592875647667 ; 5*925*rate = 45.43874204987046 ; at high price 5*(setup+925*nll) s = 219.37133365310729
gate n_references per slot {'birth_year': 7, 'cat_name': 7, 'hometown': 7, 'house_number': 6, 'person_name': 8, 'pet_name': 8, 'sibling_name': 7, 'street': 6}
gate NLL sum per reading 56 sum set_sizes 3804   (8 readings x (3804 + 56) = 30880)
```
(303.383428 s = ledger E5 closed seconds, see group 6.) So ~45.4 s is for ALL 5 M2 adapters (~9.1 s per seed); at committed high prices it is 43.874 s per adapter, 219.37 s total.

Phase 38/39 signals quoted in the option text:
```
phase38_rank.json readings.k78.pet_name.curve["512"].rank = 16 ; readings.M2.pet_name.curve["512"].rank = 32
phase39_ctx.json readings.k78.pet_name.rank = {'median': 2, 'n1': 5, 'rank_of_mean_nll': 2}
phase39_ctx.json readings.M2.pet_name.rank  = {'median': 5, 'n1': 0, 'rank_of_mean_nll': 5}   (of 27 R_q questions; 39-07-SUMMARY row "k78 pet_name 5/27", "M2 pet_name 0/27")
```

## Group 3 — P-1 (`g1_5.py 3`)
```
retrain dialogue_ppl {'adapter_off': 4.573349214207799, 'adapter_on': 6.007920892362744, 'n_targets': 270203}
retrain pre_erasure.dialogue_ppl {'adapter_off': 4.573349214207799, 'adapter_on': 6.007920892362744, 'n_targets': 270203}
equal True
dialogue_floor recipe {'arm_spec': 'real', 'arms': ['erase_dialogue_floor_seed1337', 'erase_dialogue_floor_seed2024'], 'n_facts': 10, 'prefix': 'phase19', 'replay_ratio': 1.0, 'second_person': False}
dialogue_floor['dialogue_ppl']['1337'] {'adapter_off': 4.573349214207799, 'adapter_on': 5.815445876712191, 'n_targets': 270203}
erased pre adapter_on 5.815445876712191 floor 1337 adapter_on 5.815445876712191 equal True
probe a2_pass {'draws': 10368, 'fixed_seconds': 172.56900891009718, 'total_seconds': 2724.6836681673303} keys ['draw_seconds', 'draw_seconds_spread', 'draws', 'draws_per_question', 'fixed_seconds', 'total_seconds']
```
D-07 gap prediction:
```
floor 2024 {'adapter_off': 4.573349214207799, 'adapter_on': 5.810231428543841, 'n_targets': 270203}
gap {'1337': 1.2420966625043919, '2024': 1.2368822143360418} |diff| 0.005214448168350039
```

## Group 4 — P-2 (`g1_5.py 4`)
Driver call read at scripts/phase19_erasure.py:3624-3637: `facts, second_person, replay_ratio = tp.arm_spec("real")`; per seed `tp.train_arm(arm, facts=facts, family_ids=factset.TAUGHT_FAMILY_IDS, second_person=second_person, replay_ratio=replay_ratio, seed=seed, prefix=RETRAIN_PREFIX)`.
```
floor-1337 adapter path /Users/juliorcoelho/PersonaCore/checkpoints/phase19_erase_dialogue_floor_seed1337_adapter.pt
top keys ['adapter', 'base_fingerprint', 'lora_config', 'schema_version'] ['adapter', 'base_fingerprint', 'lora_config', 'schema_version']
tensors 72 72 same keys True equal 72
metadata equal True nonadapter keys ['base_fingerprint', 'lora_config', 'schema_version']
```
No file sha256 printed or compared (amended D-07). D-07 targets exist: checkpoints/phase19_erase_dialogue_floor_seed2024_adapter.pt, checkpoints/phase19_erase_reference_adapter.pt.

## Group 5 — Digest location (`g1_5.py 5`)
```
arm_retrain keys ['arm', 'config', 'dialogue_ppl', 'draw_record_keys', 'draws', 'exposure', 'per_fact', 'pre_erasure', 'retention_ppl']
RETRAIN_SCORES_PATH /Users/juliorcoelho/PersonaCore/results/phase19_retrain_scores.json
adapter_sha256 22e66552e92ec7d5f853a6b8d15f350cfc0f127f20ee85aaec1967147c375b57
```

## Group 6 — Pins and ledger
```
$ git log --oneline 877b92b..HEAD -- scripts/teach_persona.py scripts/phase19_erasure.py scripts/phase14_recall.py scripts/phase18_extraction.py scripts/phase14_factset.py src/personacore/
(empty) rc=0
$ .venv/bin/python scripts/phase36_ledger.py report
{"event": "end", "flag": null, "front": "probes", "phase": 36, "record": "results/phase36_probe_e5.json", "run_id": "v6/36/probes/e5", "seconds": 131.444605, "started_utc": "2026-10-02T18:48:29.359942+00:00", "status": "closed"}
{"event": "end", "flag": null, "front": "probes", "phase": 36, "record": "results/phase36_probe_e6.json", "run_id": "v6/36/probes/e6", "seconds": 103.244754, "started_utc": "2026-10-02T18:50:41.026513+00:00", "status": "closed"}
{"event": "end", "flag": null, "front": "probes", "phase": 36, "record": "results/phase36_probe_e3.json", "run_id": "v6/36/probes/e3", "seconds": 2137.876548, "started_utc": "2026-10-02T18:52:24.524908+00:00", "status": "closed"}
{"event": "end", "flag": null, "front": "probes", "phase": 36, "record": "results/phase36_probe_e2.json", "run_id": "v6/36/probes/e2", "seconds": 2876.799037, "started_utc": "2026-10-02T19:28:02.631193+00:00", "status": "closed"}
{"event": "end", "flag": null, "front": "probes", "phase": 36, "record": "results/phase36_probe_e1.json", "run_id": "v6/36/probes/e1", "seconds": 7926.788894, "started_utc": "2026-10-02T20:15:59.808779+00:00", "status": "closed"}
{"event": "end", "flag": null, "front": "R1b", "phase": 37, "record": "results/phase37_r1b.json", "run_id": "v6/37/R1b/replica", "seconds": 4104.256927, "started_utc": "2026-10-03T23:16:49.288810+00:00", "status": "closed"}
{"event": "end", "flag": null, "front": "E5", "phase": 38, "record": "results/phase38_rank.json", "run_id": "v6/38/E5/rank", "seconds": 303.383428, "started_utc": "2026-10-04T18:53:53.757496+00:00", "status": "closed"}
{"event": "end", "flag": null, "front": "E6", "phase": 39, "record": "results/phase39_ctx.json", "run_id": "v6/39/E6/ctx", "seconds": 820.420965, "started_utc": "2026-10-05T16:15:38.312689+00:00", "status": "closed"}
{"closed_seconds_by_front": {"E1": 0.0, "E2": 0.0, "E3": 0.0, "E4": 0.0, "E5": 303.383428, "E6": 820.420965, "R1b": 4104.256927, "probes": 13176.153838}}
$ g1_5.py 6
require_launch {'front': 'E2', 'spent_seconds': {'probes': 13176.153838, 'R1b': 4104.256927, 'E1': 0.0, 'E2': 0.0, 'E3': 0.0, 'E4': 0.0, 'E5': 303.383428, 'E6': 820.420965}, 'total_seconds': 18404.215158, 'lifted': ()}
```
Every ledger line closed (no open run); E2 spent 0.0; require_launch passed. Seeds: `phase35_prereg.seed_list()` = (1337, 2024, 1338, 2025, 1339); `e1_teaching_seeds()` = (1337, 2024).

## Group 7 — B1 (CPU, nothing else running)
```
$ time .venv/bin/python -c "import torch; torch.backends.mps.is_available = lambda: False; import json, sys; sys.path[:0]=['scripts','src']; import phase14_recall as recall, phase19_erasure as pin; model, cfg, tok, forbid, artifact = recall.load_adapted_model('cpu'); r = pin.dialogue_ppl_pair(model, 'cpu', forbid); c = json.load(open('results/phase19_noise_floors.json'))['dialogue_ppl_noise_floor']['seed_a']['adapter_off']; print(repr(r['adapter_off']), r['n_targets'], r['adapter_off'] == c)"
4.573348505014267 270203 False
238,11s user 32,23s system 240% cpu 1:52,48 total
results/phase19_arm_replicate.json pre_erasure.dialogue_ppl == dialogue_ppl: True {'adapter_off': 4.573349214207799, 'adapter_on': 5.815445876712191, 'n_targets': 270203}
results/phase19_arm_retrain.json pre_erasure.dialogue_ppl == dialogue_ppl: True {'adapter_off': 4.573349214207799, 'adapter_on': 6.007920892362744, 'n_targets': 270203}
noise_floors seed_a {'adapter_off': 4.573349214207799, 'adapter_on': 5.815445876712191, 'n_targets': 270203, 'seed': 1337}
```
Wall 112.5 s (orchestrator's run: 51 s).

## Task 1 <verify> (verbatim)
```
7.890925927716101 True 11.83638889157415 7.9518624092864085 77.78526798055215
verify rc=0
```
Task 2 verify (`git ls-files 'scripts/phase40_*' 'results/phase40_*' | wc -l` == 0): rc=0.
Post-check: `git status --porcelain -- scripts src results tests ledger` empty. Only pre-existing ` D .claude/scheduled_tasks.lock` in the tree.

## Findings vs the plan text
- F-1 (wording, option text): approve-both "cons" says "D-13 adds about 45 s per seed of MPS scoring". Measured: 45.44 s is 5 x 925 NLLs at the Phase 38 rate, i.e. ALL five M2 adapters (~9.09 s per seed); at the committed high unit prices it is 43.87 s per adapter (219.37 s total). The notice item 3 ("about 45 s at Phase 38's measured MPS rate", against the whole +0.0609 h) agrees with the measurement; the option text does not. Not absorbed — orchestrator to correct before showing Rafael.
- F-2 (minor, shape): results/phase19_dialogue_floor.json recipe carries a sixth key `arms` = ['erase_dialogue_floor_seed1337', 'erase_dialogue_floor_seed2024'] not listed in the interface; the five listed values match exactly.
- Every other number matches the interfaces bit for bit.
