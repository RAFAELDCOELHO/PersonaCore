---
phase: 41-erasure-across-facts-orderings-and-seeds
plan: 01
subsystem: erasure-prereg-inputs
tags: [phase41, gate, premises, erase-03, erase-05, no-code]
requires:
  - results/phase40_noise_floor.json (fd603cd) and the four phase41_adapters it names
  - results/phase36_budget.json, results/phase20_retention_floor.json, results/phase19_collateral_curve.json
provides:
  - measured premise values (with sources) that plans 41-02..41-16 cite instead of retyping 41-CONTEXT
affects: [41-02, 41-03, 41-04, 41-05, 41-06, 41-07, 41-08, 41-09, 41-10, 41-11, 41-12, 41-13, 41-14, 41-15, 41-16]
tech-stack:
  added: []
  patterns: [re-measure every quoted premise from committed bytes in .venv (Python 3.11) before any code]
key-files:
  created: [.planning/phases/41-erasure-across-facts-orderings-and-seeds/41-01-SUMMARY.md]
  modified: []
decisions:
  - "Every interfaces value of 41-01-PLAN re-measured equal at HEAD ba1baa4; one minor CONTEXT rounding (D-05 ~1.44 s vs measured 1.4499 s per value NLL), ruled by Rafael 2026-10-08: the prereg uses the measured 1.4499 s"
requirements-completed: []
# 41-01 completes no requirement: it only contributes the ERASE-05 digest gate and the ERASE-03 input measurement; both close with later plans.
metrics:
  duration: ~15 min
  completed: 2026-10-08
---

# Phase 41 Plan 01: Gate and premise re-measurement Summary

Phase 40's five records are tracked and its four adapters match their committed SHA-256. All ten
premise groups the Phase 41 pre-registration will quote were re-measured from committed bytes in
`.venv` (Python 3.11.15) at HEAD `ba1baa4`. They agree with the planner's interfaces block and with
41-CONTEXT. One minor rounding difference (D-05's "~1.44 s") and four call-path observations are
listed below.

## Task 1: Gate (run by the orchestrator at HEAD ba1baa4)

- `ls .planning/phases/40-m2-seed-noise-floor/`: 40-01..40-11 PLAN+SUMMARY, 40-CONTEXT,
  40-DISCUSSION-LOG, 40-PATTERNS, 40-RESEARCH, 40-REVIEW-2, 40-REVIEW, 40-VALIDATION — no
  40-VERIFICATION.md.
- `grep -n 'Phase 40: M2' .planning/ROADMAP.md`: `1444:- [ ] **Phase 40: M2 Seed Noise Floor** - E2: ...`
- NOISE-01 (REQUIREMENTS.md:748) and NOISE-02 (:749) both `- [ ]`.
- `git ls-files --error-unmatch` on the five Phase 40 records: exit 0.
- adapter digest check: `[True, True, True, True]`.
- `git status --porcelain -- scripts src results tests ledger artifacts`: empty.
- Status: Phase 40 was NOT yet closed when the gate ran. The orchestrator is running the Phase 40
  verifier and will apply the hand close.

Phase 40 close (applied by the orchestrator, not by this plan): 40-VERIFICATION.md written by the gsd-verifier, `status: passed`, score 3/3 roadmap SC (plus 8/8 plan truths); hand close commit 246fddb ticks ROADMAP.md:1444 Phase 40 `[x]`, 40-01..40-11 `[x]`, REQUIREMENTS.md NOISE-01/NOISE-02 `[x]` (and the traceability rows Complete); zero gsd-sdk mutation handlers; the 453 tests in the 18 test files that read ROADMAP/STATE/REQUIREMENTS passed after the edit. Gate re-checked after the close: the five records tracked and the four adapter digests True (unchanged at 246fddb).

## Task 2: Measured premises

All calls ran with `.venv/bin/python` and `sys.path[:0] = ['scripts', 'src']` at HEAD `ba1baa4`
(script kept outside the repo, in the session scratchpad). "Interfaces" means the
`<interfaces>` block of 41-01-PLAN.md (measured by the planner at 3787b9d).

### 1. Pre-registration core (`scripts/phase35_prereg.py`)

| Value | Measured | Source | Interfaces |
|---|---|---|---|
| targets | `('pet_name', 'cat_name', 'street', 'sibling_name')` | `phase35_prereg.e1_targets()` | same |
| teaching seeds | `(1337, 2024)` | `e1_teaching_seeds()` | same |
| (b) margin | `0.2962962962962963` (= 8/27) | `e1_condition_b_margin()` | same |
| CURVE_K / FULL_FIDELITY_K / MARGIN_K | `16` / `48` / `2` | module attributes | same |
| A2 corpus size | `216` | `len(a2_corpus_entries())` | same |
| `e1_checkpoint_grid` inputs | `('results/phase36_budget.json',)`, owner 41 | `SLOTS[...]["input_records"]`, `["owner_phase"]` | same |
| `e1_condition_a_floors` inputs | `('results/phase41_calibration_*.json', 'results/phase19_calibration_corpus.json')`, owner 41 | same | same |
| `e1_condition_c_band_inputs` inputs | `('results/phase40_noise_floor.json', 'results/phase41_band_inputs_*.json')`, owner 41 | same | same |
| `e1_alternative_ordering` inputs | `()`, owner 41 | same | same |
| `e1_condition_b_margin` inputs | `('results/phase19_noise_floors.json',)`, owner 41 | same | same (owner not stated) |
| owner glob, all five E1 slots | `'scripts/phase41_*prereg.py'` | `owner_prereg_glob(slot)` | same (stated for the grid) |
| V6_RESULT_PATHS, Phase 41 | `results/phase41_calibration_*.json`, `results/phase41_band_inputs_*.json`, `results/phase41_*` | `phase35_prereg.V6_RESULT_PATHS` | n/a (CONTEXT Integration Points: same three) |

Call path: `import phase35_prereg` leaves torch unloaded; the first call `e1_targets()` loads torch
(it reads `phase19_erasure.TARGET_RANKING`, whose module imports torch).

### 2. Budget (`results/phase36_budget.json`, `scripts/phase36_caps.py`)

| Value | Measured | Interfaces / CONTEXT |
|---|---|---|
| `front_hours` | E1 52.779745537787676, E2 7.890925927716101, E3 6.622459432036141, E4 4.806791480779648, E5 0.3612376740339419, E6 0.4949481154825642, R1b 1.1081805983679887, probes 3.660042732777778 | E1/E3/E4 same |
| `stop_line_hours` | 90 | same |
| `total_hours` | 77.72433149898184 | not stated |
| `unit_caps.E1` | `{'calibrations': 4, 'cells': 16, 'checkpoints_per_cell': 5, 'k48_confirms_per_cell': 1}` | same |
| `unit_prices` e1_* | calibration 1120.3298829682171 s, k16 1437.6697064265609 s, k48 3989.450154124759 s, ordering 417.56158900260925 s; also `e1_spread_ratio` 1.013790472116322 | four prices same |
| `unit_prices.e2_train_m2_high` | 76.1114059574902 s | CONTEXT "76.11 s": same |
| `counts_for("e1_checkpoint_grid", {"checkpoints": (16, 32, 48, 64, 128)})` | `{'checkpoints_per_cell': 5}` | same |
| `check_unit_caps("E1", checkpoints_per_cell=5)` | returns `{'checkpoints_per_cell': 5}` (passes) | expected pass |
| `check_unit_caps("E1", k48_confirms_per_cell=2)` | raises `SystemExit: [phase36_caps] E1 k48_confirms_per_cell = 2 exceeds the committed cap 1 in results/phase36_budget.json. D-09: exceeding a Phase 36 cap needs Rafael's approved` | expected SystemExit (D-26: the driver must never pass >1) |

### 3. Ledger (`ledger/v6_mps_ledger.jsonl`, `scripts/phase36_ledger.py`)

- `.venv/bin/python scripts/phase36_ledger.py report` lists 15 attempts, all `closed`, none of them
  E1. Final line:
  `{"closed_seconds_by_front": {"E1": 0.0, "E2": 41927.365921, "E3": 0.0, "E4": 0.0, "E5": 303.383428, "E6": 820.420965, "R1b": 4104.256927, "probes": 13176.153838}}`
- `phase36_ledger.spent(fronts=("E1",))`: `{'by_front': {'E1': 0.0}, 'total_seconds': 0.0, 'rows': []}`.
  E1 spent = 0.0 h (expected 0.0).
- `phase36_ledger.spent()` (all fronts): `total_seconds` 60331.581079 = **16.7588 h** spent. Of that,
  E2 is 41927.365921 s = 11.6465 h, including two `lost` seed-2025 attempts (14276.36896 s + 120.011158 s).
  No attempt is open.

### 4. Calibration (`scripts/phase19_erasure.py`, `scripts/teach_persona.py`)

| Value | Measured | Source | Interfaces |
|---|---|---|---|
| calibration fact | id `cal_person_varek`, slot `person_name` | `phase19_erasure.select_calibration_fact()` | same |
| calibration corpus | fact_id `cal_person_varek`, slot `person_name`, n_questions 23, question_counts `{'core_held_out': 9, 'core_taught': 14}` | `results/phase19_calibration_corpus.json` | same |
| N_COMPONENTS | 288 | `phase19_erasure.N_COMPONENTS` | same |
| GATED_NONTARGET_SLOTS | `('cat_name', 'street', 'sibling_name', 'person_name', 'house_number', 'birth_year', 'hometown')` (7) | `phase19_erasure` | same (7 slots) |
| TARGET_SLOT / N_TARGET_QUESTIONS | `pet_name` / 27 | `phase19_erasure` | same |
| CORE_SLOTS | `('person_name', 'pet_name', 'cat_name', 'sibling_name', 'hometown', 'street', 'birth_year', 'house_number')` (8) | `phase18_extraction.CORE_SLOTS` | same (8) |
| CORPUS_TIERS / K | `('core_taught', 'core_held_out')` / 48 | `phase18_extraction` | same |
| teach_persona.SEED | 1337 | `teach_persona.SEED` | same |
| `arm_spec("cal_first_person_replay")` | tuple `(facts, second_person, replay_ratio)`: 10 facts (`cal_person_varek`, `cal_person_sedrin`, `cal_dog_nubbin`, `cal_dog_torvo`, `cal_cat_glimm`, `cal_sister_tolma`, `cal_town_ashenvale`, `cal_street_dunwold`, `cal_year_1974`, `cal_house_8351`), second_person `False`, replay_ratio `1.0` | `teach_persona.arm_spec` | not stated |
| Phase 19 calibration adapter | exists, 1351991 bytes, mtime 18 Aug 09:30, sha256 `bc616c3667719e677532a5e56c7b8de8e2dc79e15af85ccc14bc1dcce66856da`, **untracked** (gitignored checkpoint) | `ls -la`, `shasum -a 256`, `git ls-files --error-unmatch` | not stated; D-10: never a floor input; D-11: compare with `torch.equal` only |
| Phase 19 calibration k | 187 (stopped True) | `results/phase19_calibration_curve.json::k` | CONTEXT D-03 "187": same |

### 5. Band inputs (`results/phase40_noise_floor.json`, `mitigation_gate.dialogue_gap_band`)

| Value | Measured | Interfaces / CONTEXT D-13 |
|---|---|---|
| `gap_noise_floor` | 0.08406970366097503 | same |
| `per_seed["1337"].full.dialogue_gap` | gap 1.2420966625043919, device `mps`, pre_post_equal `True` | same |
| `per_seed["2024"].full.dialogue_gap` | gap 1.2368822143360418, device `mps`, pre_post_equal `True` | same |
| band 1337 | `(0.6210483312521959, 1.4102360698263419)` | same (CONTEXT [0.6210, 1.4102]) |
| band 2024 | `(0.6184411071680209, 1.4050216216579918)` | same (CONTEXT [0.6184, 1.4050]) |
| `phase35_prereg.DIALOGUE_GAP_BAND is mitigation_gate.dialogue_gap_band` | `True` | pin by reference |

### 6. D-19 / D-28 labelled slots (`results/phase40_noise_floor.json::recall_floor`)

Seed order of every counts list: `[1337, 2024, 1338, 2025, 1339]` (`recall_floor.*.seeds`, `phase40_prereg.SEEDS`).

| slot | full counts (/27) | full range | m2 counts (/27) | m2 range | max range | labelled (>= 8/27) |
|---|---|---|---|---|---|---|
| birth_year | 18, 16, 23, 19, 24 | 8/27 | 18, 18, 20, 25, 12 | 13/27 | 13/27 | yes |
| cat_name | 27 ×5 | 0 | 27 ×5 | 0 | 0 | no |
| hometown | 21, 22, 14, 11, 8 | 14/27 | 18, 8, 25, 16, 14 | 17/27 | 17/27 | yes |
| house_number | 24, 23, 22, 20, 22 | 4/27 | 17, 23, 24, 21, 23 | 7/27 | 7/27 | no |
| person_name | 26, 27, 26, 26, 26 | 1/27 | 26, 26, 25, 26, 25 | 1/27 | 1/27 | no |
| sibling_name | 27 ×5 | 0 | 27 ×5 | 0 | 0 | no |
| street | 27 ×5 | 0 | 27 ×5 | 0 | 0 | no |

- Labelled set computed as `{slot: max(range_full, range_m2) >= e1_condition_b_margin()}`:
  `{'birth_year': True, 'hometown': True}`, all others False. This matches the interfaces block and
  D-19 (birth_year 13/27, hometown 17/27, house_number 7/27 unlabelled).
- `recall_floor.full.per_slot` and `recall_floor.m2.per_slot` both have no `pet_name` row (keys:
  birth_year, cat_name, hometown, house_number, person_name, sibling_name, street). This matches D-28.
- D-28 pet_name basis, measured through
  `phase40_prereg.slot_rows(phase40_prereg.a2_rows(r, *phase40_prereg.a2_scope(r)))` with
  `r = json.load(open(phase40_prereg.a2_record("full", s)))`. Note that `a2_record` returns the
  path, not the record. Fact `cand_dog_zorp`, family A2, tiers `('core_held_out', 'core_taught')`:
  1337 27/27, 2024 26/27, 1338 27/27, 2025 25/27, 1339 27/27. The range is 2/27, below 8/27, so
  pet_name is unlabelled. This matches the interfaces block and D-28 (27, 26, 27, 25, 27).
- D-18 context check: at 2024, hometown full 22 vs m2 8 is a 14/27 departure (CONTEXT "22 → 8":
  same). At 1337 the largest full−m2 departure is house_number 24 vs 17 = 7/27 (CONTEXT: same).

### 7. D-20 Phase 40 M2 D-13 block (`results/phase40_noise_floor.json::d13.blocks`)

| seed | anchor rank 8 / 32 / 128 / 512 | R_q committed n1 | R_q minted n1 |
|---|---|---|---|
| 1337 | 1 / 4 / 10 / 32 | 0 | 11 |
| 1338 | 1 / 4 / 13 / 41 | 0 | 9 |
| 1339 | 1 / 3 / 7 / 15 | 1 | 12 |
| 2024 | 2 / 5 / 12 / 41 | 0 | 10 |
| 2025 | 1 / 3 / 9 / 23 | 1 | 11 |

The min–max values are: anchor at 512, 15–41; committed n1, 0–1; minted n1, 9–12. They match the
interfaces block (32, 41, 15, 41, 23 / 0, 0, 1, 0, 1 / 11, 9, 12, 10, 11 in the record's key order)
and CONTEXT D-20. Phase 39 prior reading (`results/phase39_ctx_report.md:240,248`, column R_q n1 /
G_q answered): k32 pet_name 18 / 2/27, k64 pet_name 11 / 0/27. CONTEXT D-07 (2/27 at 32, 0/27 at
64) and D-21 (R_q n1 11/27 at 64) both agree.

### 8. D-14 retention (`results/phase20_retention_floor.json`, `results/phase40_a2_*_seed*.json::retention_ppl[0]`)

| Value | Measured | Interfaces / CONTEXT |
|---|---|---|
| cap | 3.9085032379884783; `cap_derivation` "3.89114 + 2 x 0.008681618994239138 (scripts/erasure_gate.py:246)" | same |
| retention_ppl_noise_floor | 0.008681618994239138 | same |
| phase20 adapter_off | 3.891139975617828 (both seeds) | CONTEXT "3.891140" |
| full retention_ppl[0] | 1337 4.219759892336485, 1338 4.155725635119946, 1339 4.3317421359777635, 2024 4.2284415113307245, 2025 4.233186749458311; min–max 4.155725635119946–4.3317421359777635 | 1337/2024 same; CONTEXT "4.156–4.332" same |
| m2 retention_ppl[0] | 1337 4.217157524257963, 1338 4.215637157242952, 1339 4.433319345887968, 2024 4.206715106532572, 2025 4.296010921857475; min–max 4.206715106532572–4.433319345887968 | 1337/2024 same; CONTEXT "4.207–4.433" same |
| v3.0 erased arm | 3.6709177253236867 (`results/phase19_arm_erased.json::retention_ppl[0]`) | CONTEXT "3.6709" same |

All ten Phase 40 values sit above the cap and the v3.0 erased arm sits below it, as D-14 states.

### 9. D-07 / D-08 / Pattern 3

| Value | Measured | Source | Interfaces / CONTEXT |
|---|---|---|---|
| greedy ordered_prefix | len 78, k 78, wall_clock_min 6.959359816710154 | `results/phase19_collateral_curve.json` | same (CONTEXT 6.96) |
| k* | `kstar_block.k` 64, attack_family A2, budget_k 48 | `results/erasure_kstar_summary.json` | same |
| adapter-off record | `results/phase18_arm_adapter-off.json`, exists | `phase38_prereg.ADAPTER_OFF_RECORD` | same |
| adapter-off A2 per slot | cat_name, street, sibling_name, person_name, house_number, birth_year, hometown, pet_name: all **0/27** | `phase40_prereg.slot_rows(phase40_prereg.a2_rows(r, "A2", ('core_held_out', 'core_taught')))` | 0/27 for the eight facts: same |

### 10. Path constants

| Constant | Measured |
|---|---|
| `phase20_run.RETENTION_FLOOR_PATH` | `<repo>/results/phase20_retention_floor.json` |
| `phase19_erasure.CALIBRATION_CORPUS_PATH` | `<repo>/results/phase19_calibration_corpus.json` |
| `phase19_erasure.CALIBRATION_ARM` | `'erase_calibration'` |
| `phase19_erasure.RETRAIN_PREFIX` | `'phase19'` |
| `teach_persona.arm_outputs("e1_calibration_seed1337", prefix="phase41")` | bin `data/persona_e1_calibration_seed1337_train.bin`, mask `data/persona_e1_calibration_seed1337_train_mask.bin`, csv `results/phase41_e1_calibration_seed1337/run.csv`, checkpoint `checkpoints/phase41_e1_calibration_seed1337_latest.pt`, adapter `checkpoints/phase41_e1_calibration_seed1337_adapter.pt`; **none exists** |
| `phase36_ledger.run_id(41, "E1", "prep_greedy_seed1337")` | `'v6/41/E1/prep_greedy_seed1337'` |

Note: the csv output lands under `results/phase41_*`, which matches the `results/phase41_*`
pattern in V6_RESULT_PATHS.

## Premise mismatches

1. **Minor rounding, CONTEXT D-05:** "one value NLL costs at most ~1.44 s". Measured:
   417.56158900260925 / 288 = 1.4498666284812822 s, which rounds to 1.45 s; 1.44 is a truncation.
   The ~57× backward/forward headroom quoted beside it is unaffected at this precision. No
   threshold depends on this value. It is reported so it is not absorbed silently.

No interfaces-block value differs from its measurement.

## Observations (call paths and context, not mismatches)

- `e1_targets()` loads torch. The import of `phase35_prereg` does not.
- `phase40_prereg.a2_scope(record)` raises `KeyError: 'attack_family'` on
  `results/phase18_arm_adapter-off.json`: its `config` has no `attack_family` key (it has
  `family_zero` A0 and k 48). The 0/27 reading needs the family passed explicitly ("A2"). Any later
  plan that cites the adapter-off end point through `a2_scope` will hit this.
- `phase40_prereg.a2_record(group, seed)` returns a path string, not the parsed record.
- `teach_persona.arm_spec` returns a 3-tuple, not a mapping.
- `SLOTS["e1_condition_b_margin"]["owner_phase"]` is 41, so its owner glob is
  `scripts/phase41_*prereg.py`. The module docstring (:84-89) and `_rule_e1_condition_b_margin`
  (:1694) call it "locked in the core", and CONTEXT says Phase 41 fills only the other four. The
  rule takes no inputs and returns `e1_condition_b_margin()`. Plan 02 should check whether the
  Phase 35 completeness test expects a Phase 41 fill binding for it.
- The v4.0 cap uses the rounded 3.89114. Exact adapter_off + 2 × floor = 3.9085032136063065, which
  is 2.4e-8 below the committed cap. CONTEXT quotes the derivation as written in the record.
- The phase20 seed-1337 `adapter_on` retention (4.219759892336485) is bit-equal to Phase 40 full
  seed 1337's. This fits the known tensor identity of that adapter with `checkpoints/persona_adapter.pt`.

## Verification

Plan `<verify>` command, run at the end (HEAD ba1baa4):

```
('pet_name', 'cat_name', 'street', 'sibling_name') (1337, 2024) 0.2962962962962963 16 48 {'checkpoints_per_cell': 5}
VERIFY_EXIT=0
```

`git status --porcelain` after the run: only ` M .claude/scheduled_tasks.lock` (pre-existing,
outside the checked pathspecs). `scripts src results tests ledger artifacts` are empty.

## Deviations from Plan

- Only Task 2 was executed by this agent. Task 1 (the blocking gate) was run by the orchestrator, and
  its outputs are pasted above with the Phase 40 close left as a placeholder.
- Nothing was committed. The orchestrator commits this SUMMARY after the Phase 40 close.
- In the first measurement pass, two calls raised because of the measuring script's own assumptions
  (`vars()` on the `arm_spec` tuple; indexing the `a2_record` path as a record), and one raised in
  `a2_scope` on the adapter-off record. All three were re-measured with the correct call shape. The
  `a2_scope` behaviour is recorded under Observations.

## Self-Check: PASSED

- SUMMARY file exists at `.planning/phases/41-erasure-across-facts-orderings-and-seeds/41-01-SUMMARY.md`.
- No commits were claimed. The verify command printed the expected line, and the porcelain check on
  the six pathspecs was empty.

## Checkpoint reply (Rafael, 2026-10-08, verbatim)

> phase 40 closed
>
> Para o 41-02: a previsão D-11 cita como fonte do sha256 esperado do adaptador de calibração da Fase 19 (bc616c36…) um registro commitado que o traz, como results/phase19_calibration_curve.json, já que o .pt não está no git. E o pré-registro usa o custo medido por NLL (1,4499 s), não o "~1,44 s" do CONTEXT, em toda conta que dependa dele.

Premises measured before applying (orchestrator, HEAD 246fddb): `results/phase19_calibration_curve.json`
(tracked, added 69fc671) carries `adapter_in_sha256` = `bc616c3667719e677532a5e56c7b8de8e2dc79e15af85ccc14bc1dcce66856da`,
equal to the sha256 of the untracked `checkpoints/phase19_erase_calibration_adapter.pt`, which is
`teach_persona.arm_outputs(phase19_erasure.CALIBRATION_ARM, prefix=phase19_erasure.RETRAIN_PREFIX)["adapter"]`
(also carried by `results/phase19_calibration_curve_siblings.json`); per value NLL =
`unit_prices.e1_ordering_seconds / phase19_erasure.N_COMPONENTS` = 417.56158900260925 / 288 = 1.4498666284812822 s.
Both rulings are carried into 41-02 and 41-07 as dated orchestrator amendments.
