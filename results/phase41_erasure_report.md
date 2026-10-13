# Phase 41 — E1: erasure across facts, orderings and seeds

## Summary (D-16, D-17)

Status: **COMPLETE**. Of the 8 (target, ordering) pairs: PASS 0, FAILURE replicada 8, não replicado 0.

Inside "não replicado", each pair counted once under its seeds' verdicts (1337 + 2024):

| verdicts | pairs |
|---|---|

The rule: of the 8 (target, ordering) pairs, the count under each label (the three labels sum to 8); inside 'não replicado' each pair counted exactly once, under the combination of its two seeds' verdicts in SEEDS order (e.g. 'SUCCESS + NOT_REACHED'), NOT_RUN a verdict value in those combinations, so the sub-counts sum to the 'não replicado' count with no double count; no threshold, no aggregation beyond the count; the full 4 x 2 x 2 table published.

| pair | label | per seed |
|---|---|---|
| pet_name\|greedy | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |
| pet_name\|gradient | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |
| cat_name\|greedy | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |
| cat_name\|gradient | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |
| street\|greedy | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |
| street\|gradient | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |
| sibling_name\|greedy | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |
| sibling_name\|gradient | FAILURE replicada | FAILURE na 1337, FAILURE na 2024 |

## The 4 x 2 x 2 table (D-15)

| target | ordering | 1337 | 2024 |
|---|---|---|---|
| pet_name | greedy | FAILURE | FAILURE |
| pet_name | gradient | FAILURE | FAILURE |
| cat_name | greedy | FAILURE | FAILURE |
| cat_name | gradient | FAILURE | FAILURE |
| street | greedy | FAILURE | FAILURE |
| street | gradient | FAILURE | FAILURE |
| sibling_name | greedy | FAILURE | FAILURE |
| sibling_name | gradient | FAILURE | FAILURE |

A NOT_REACHED cell reads (D-09): "não apagado com 128 de 288 componentes removidos". NOT_RUN: a cell never started (or dropped and not re-run).

Alternative ordering variant: adaptive (decided by mps_smoke: cpu_seconds 0.09196808400156442, mps_seconds 1.2165203749900684; data/phase41_e1/variant.json sha256 311a87dd87e06bd8e40e740f8876544aa4c1380656eea5e8158f2d1b9f7a567c; IN-02).

## Cells

### cell_pet_name_greedy_seed1337

Verdict **FAILURE** at stop 64; failed conditions: (b), (c); non-targets beyond the margin: person_name, cat_name, sibling_name, hometown, street, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 6/27 | 1 | False | None |
| 32 | 1/27 | 1 | False | None |
| 48 | 0/27 | 1 | True | False |
| 64 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 | 64 |
|---|---|---|---|---|
| birth_year | 4/27 | 6/27 | 4/27 | 3/27 |
| cat_name | 26/27 | 23/27 | 12/27 | 3/27 |
| hometown | 0/27 | 0/27 | 0/27 | 0/27 |
| house_number | 12/27 | 4/27 | 2/27 | 2/27 |
| person_name | 8/27 | 1/27 | 0/27 | 0/27 |
| pet_name | 6/27 | 1/27 | 0/27 | 0/27 |
| sibling_name | 15/27 | 4/27 | 0/27 | 0/27 |
| street | 22/27 | 6/27 | 1/27 | 0/27 |

D-26 confirmations (2; 2.171691513888889 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 48 | False | 3458.368830208 | 2026-10-09T19:20:11.537128+00:00 | 2026-10-09T20:17:49.918912+00:00 |
| 64 | True | 4359.720619792 | 2026-10-09T20:43:43.362317+00:00 | 2026-10-09T21:56:23.088283+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 11/27 | -0.25925925925925924 | False | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 6/27 | -0.7777777777777778 | True | não | 27-27 | 27-27 |
| hometown | 21/27 | 0/27 | -0.7777777777777778 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 6/27 | -0.6666666666666666 | True | não | 20-24 | 17-24 |
| person_name | 26/27 | 0/27 | -0.9629629629629629 | True | não | 26-27 | 25-26 |
| sibling_name | 27/27 | 0/27 | -1.0 | True | não | 27-27 | 27-27 |
| street | 27/27 | 0/27 | -1.0 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.347219214585043 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 5 unlabelled (person_name, cat_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.723444660061371 | 4.219759892336485 | 4.217157524257963 | 3.9085032379884783 | sim |

D-18 M1 x M2 (descriptive; 'fora da faixa' não é teste estatístico: duas seeds contra cinco retreinos do M2):

| slot | full | M1 | M2 | M1 - full | M2 - full | M2 min-max | M1 |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 11/27 | 18/27 | -0.25925925925925924 | 0.0 | 12-25 | fora da faixa |
| cat_name | 27/27 | 6/27 | 27/27 | -0.7777777777777778 | 0.0 | 27-27 | fora da faixa |
| hometown | 21/27 | 0/27 | 18/27 | -0.7777777777777778 | -0.11111111111111116 | 8-25 | fora da faixa |
| house_number | 24/27 | 6/27 | 17/27 | -0.6666666666666666 | -0.2592592592592592 | 17-24 | fora da faixa |
| person_name | 26/27 | 0/27 | 26/27 | -0.9629629629629629 | 0.0 | 25-26 | fora da faixa |
| sibling_name | 27/27 | 0/27 | 27/27 | -1.0 | 0.0 | 27-27 | fora da faixa |
| street | 27/27 | 0/27 | 27/27 | -1.0 | 0.0 | 27-27 | fora da faixa |

D-20 D-13 at the stop beside Phase 40's M2 range (descriptive):

| reading | value | M2 range | label |
|---|---|---|---|
| anchor_512 | 12 | 15-41 | fora da faixa |
| r_q_committed | 11 | 0-1 | fora da faixa |
| r_q_minted | 27 | 9-12 | fora da faixa |

### cell_pet_name_greedy_seed2024

Verdict **FAILURE** at stop 64; failed conditions: (b), (c); non-targets beyond the margin: person_name, sibling_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 9/27 | 1 | False | None |
| 32 | 4/27 | 1 | False | None |
| 48 | 0/27 | 1 | True | False |
| 64 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 | 64 |
|---|---|---|---|---|
| birth_year | 6/27 | 2/27 | 1/27 | 2/27 |
| cat_name | 27/27 | 26/27 | 24/27 | 10/27 |
| hometown | 5/27 | 1/27 | 1/27 | 0/27 |
| house_number | 14/27 | 11/27 | 4/27 | 2/27 |
| person_name | 4/27 | 2/27 | 0/27 | 0/27 |
| pet_name | 9/27 | 4/27 | 0/27 | 0/27 |
| sibling_name | 19/27 | 13/27 | 6/27 | 0/27 |
| street | 20/27 | 6/27 | 0/27 | 0/27 |

D-26 confirmations (2; 1.7577290886572225 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 48 | False | 3069.957500458 | 2026-10-09T23:01:08.296826+00:00 | 2026-10-09T23:52:18.248238+00:00 |
| 64 | True | 3257.867218708001 | 2026-10-10T00:09:18.917417+00:00 | 2026-10-10T01:03:36.781422+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 7/27 | -0.3333333333333333 | True | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 20/27 | -0.2592592592592593 | False | não | 27-27 | 27-27 |
| hometown | 22/27 | 0/27 | -0.8148148148148148 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 7/27 | -0.5925925925925926 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 0/27 | -1.0 | True | não | 26-27 | 25-26 |
| sibling_name | 27/27 | 2/27 | -0.9259259259259259 | True | não | 27-27 | 27-27 |
| street | 27/27 | 2/27 | -0.9259259259259259 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.4546353075408538 in [0.6184411071680209, 1.4050216216579918]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 4 unlabelled (person_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.8948468695907184 | 4.2284415113307245 | 4.206715106532572 | 3.9085032379884783 | sim |

D-18 M1 x M2 (descriptive; 'fora da faixa' não é teste estatístico: duas seeds contra cinco retreinos do M2):

| slot | full | M1 | M2 | M1 - full | M2 - full | M2 min-max | M1 |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 7/27 | 18/27 | -0.3333333333333333 | 0.07407407407407407 | 12-25 | fora da faixa |
| cat_name | 27/27 | 20/27 | 27/27 | -0.2592592592592593 | 0.0 | 27-27 | fora da faixa |
| hometown | 22/27 | 0/27 | 8/27 | -0.8148148148148148 | -0.5185185185185185 | 8-25 | fora da faixa |
| house_number | 23/27 | 7/27 | 23/27 | -0.5925925925925926 | 0.0 | 17-24 | fora da faixa |
| person_name | 27/27 | 0/27 | 26/27 | -1.0 | -0.03703703703703709 | 25-26 | fora da faixa |
| sibling_name | 27/27 | 2/27 | 27/27 | -0.9259259259259259 | 0.0 | 27-27 | fora da faixa |
| street | 27/27 | 2/27 | 27/27 | -0.9259259259259259 | 0.0 | 27-27 | fora da faixa |

D-20 D-13 at the stop beside Phase 40's M2 range (descriptive):

| reading | value | M2 range | label |
|---|---|---|---|
| anchor_512 | 6 | 15-41 | fora da faixa |
| r_q_committed | 10 | 0-1 | fora da faixa |
| r_q_minted | 27 | 9-12 | fora da faixa |

### cell_cat_name_greedy_seed1337

Verdict **FAILURE** at stop 128; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, sibling_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 18/27 | 1 | False | None |
| 32 | 1/27 | 1 | False | None |
| 48 | 1/27 | 1 | False | None |
| 64 | 0/27 | 2 | True | False |
| 128 | 0/27 | 3 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 | 64 | 128 |
|---|---|---|---|---|---|
| birth_year | 6/27 | 4/27 | 2/27 | 3/27 | 0/27 |
| cat_name | 18/27 | 1/27 | 1/27 | 0/27 | 0/27 |
| hometown | 10/27 | 2/27 | 1/27 | 0/27 | 0/27 |
| house_number | 9/27 | 8/27 | 4/27 | 1/27 | 0/27 |
| person_name | 9/27 | 3/27 | 1/27 | 0/27 | 0/27 |
| pet_name | 23/27 | 12/27 | 4/27 | 2/27 | 0/27 |
| sibling_name | 22/27 | 17/27 | 7/27 | 3/27 | 0/27 |
| street | 12/27 | 2/27 | 0/27 | 0/27 | 0/27 |

D-26 confirmations (2; 2.1252174959952774 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 64 | False | 3395.906199666999 | 2026-10-10T02:14:57.824015+00:00 | 2026-10-10T03:11:33.759249+00:00 |
| 128 | True | 4254.876785916 | 2026-10-10T03:34:13.646758+00:00 | 2026-10-10T04:45:08.437421+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 4/27 | -0.5185185185185185 | True | sim | 16-24 | 12-25 |
| hometown | 21/27 | 0/27 | -0.7777777777777778 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 1/27 | -0.8518518518518519 | True | não | 20-24 | 17-24 |
| person_name | 26/27 | 0/27 | -0.9629629629629629 | True | não | 26-27 | 25-26 |
| pet_name | 27/27 | 0/27 | -1.0 | True | não | 25-27 | — |
| sibling_name | 27/27 | 0/27 | -1.0 | True | não | 27-27 | 27-27 |
| street | 27/27 | 0/27 | -1.0 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.34893489710882797 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 5 unlabelled (person_name, pet_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.7602247716403587 | 4.219759892336485 | None | 3.9085032379884783 | sim |

D-18: sem M2, comparação não feita.

### cell_cat_name_greedy_seed2024

Verdict **FAILURE** at stop 48; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, sibling_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 8/27 | 1 | False | None |
| 32 | 5/27 | 1 | False | None |
| 48 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 |
|---|---|---|---|
| birth_year | 11/27 | 10/27 | 0/27 |
| cat_name | 8/27 | 5/27 | 0/27 |
| hometown | 5/27 | 2/27 | 0/27 |
| house_number | 7/27 | 5/27 | 1/27 |
| person_name | 17/27 | 8/27 | 0/27 |
| pet_name | 17/27 | 15/27 | 5/27 |
| sibling_name | 25/27 | 13/27 | 4/27 |
| street | 15/27 | 6/27 | 0/27 |

D-26 confirmations (1; 0.7710252876158322 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 48 | True | 2775.691035416996 | 2026-10-10T05:33:14.782919+00:00 | 2026-10-10T06:19:30.569752+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 6/27 | -0.37037037037037035 | True | sim | 16-24 | 12-25 |
| hometown | 22/27 | 0/27 | -0.8148148148148148 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 4/27 | -0.7037037037037037 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 2/27 | -0.9259259259259259 | True | não | 26-27 | 25-26 |
| pet_name | 26/27 | 9/27 | -0.6296296296296295 | True | não | 25-27 | — |
| sibling_name | 27/27 | 14/27 | -0.4814814814814815 | True | não | 27-27 | 27-27 |
| street | 27/27 | 0/27 | -1.0 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.5669725875629084 in [0.6184411071680209, 1.4050216216579918]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 5 unlabelled (person_name, pet_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.990962807428455 | 4.2284415113307245 | None | 3.9085032379884783 | não |

D-18: sem M2, comparação não feita.

### cell_street_greedy_seed1337

Verdict **FAILURE** at stop 32; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, sibling_name, hometown; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 1/27 | 1 | False | None |
| 32 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 |
|---|---|---|
| birth_year | 5/27 | 10/27 |
| cat_name | 26/27 | 15/27 |
| hometown | 7/27 | 0/27 |
| house_number | 8/27 | 6/27 |
| person_name | 9/27 | 0/27 |
| pet_name | 16/27 | 4/27 |
| sibling_name | 23/27 | 5/27 |
| street | 1/27 | 0/27 |

D-26 confirmations (1; 0.801039453055556 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 32 | True | 2883.7420310000016 | 2026-10-10T06:53:28.174577+00:00 | 2026-10-10T07:41:31.913102+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 18/27 | 0.0 | False | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 25/27 | -0.07407407407407407 | False | não | 27-27 | 27-27 |
| hometown | 21/27 | 2/27 | -0.7037037037037037 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 16/27 | -0.2962962962962963 | False | não | 20-24 | 17-24 |
| person_name | 26/27 | 1/27 | -0.9259259259259258 | True | não | 26-27 | 25-26 |
| pet_name | 27/27 | 14/27 | -0.4814814814814815 | True | não | 25-27 | — |
| sibling_name | 27/27 | 11/27 | -0.5925925925925926 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.495106427181482 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 3 unlabelled (person_name, pet_name, sibling_name); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 4.030563262233815 | 4.219759892336485 | None | 3.9085032379884783 | não |

D-18: sem M2, comparação não feita.

### cell_street_greedy_seed2024

Verdict **FAILURE** at stop 32; failed conditions: (b), (c); non-targets beyond the margin: person_name, hometown, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 2/27 | 1 | False | None |
| 32 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 |
|---|---|---|
| birth_year | 11/27 | 6/27 |
| cat_name | 27/27 | 21/27 |
| hometown | 6/27 | 0/27 |
| house_number | 9/27 | 2/27 |
| person_name | 13/27 | 1/27 |
| pet_name | 22/27 | 17/27 |
| sibling_name | 24/27 | 15/27 |
| street | 2/27 | 0/27 |

D-26 confirmations (1; 0.7319108799536116 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 32 | True | 2634.8791678330017 | 2026-10-10T08:13:28.301616+00:00 | 2026-10-10T08:57:23.208204+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 13/27 | -0.1111111111111111 | False | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 27/27 | 0.0 | False | não | 27-27 | 27-27 |
| hometown | 22/27 | 2/27 | -0.7407407407407407 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 10/27 | -0.4814814814814815 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 6/27 | -0.7777777777777778 | True | não | 26-27 | 25-26 |
| pet_name | 26/27 | 26/27 | 0.0 | False | não | 25-27 | — |
| sibling_name | 27/27 | 24/27 | -0.11111111111111116 | False | não | 27-27 | 27-27 |

(c): dialogue gap 0.6055358187045714 in [0.6184411071680209, 1.4050216216579918]: holds False.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 2 unlabelled (person_name, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.945751090345553 | 4.2284415113307245 | None | 3.9085032379884783 | não |

D-18: sem M2, comparação não feita.

### cell_sibling_name_greedy_seed1337

Verdict **FAILURE** at stop 64; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 20/27 | 1 | False | None |
| 32 | 0/27 | 1 | True | False |
| 48 | 0/27 | 2 | True | False |
| 64 | 0/27 | 3 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 | 64 |
|---|---|---|---|---|
| birth_year | 7/27 | 2/27 | 4/27 | 2/27 |
| cat_name | 27/27 | 26/27 | 23/27 | 19/27 |
| hometown | 6/27 | 0/27 | 0/27 | 0/27 |
| house_number | 12/27 | 6/27 | 3/27 | 4/27 |
| person_name | 8/27 | 1/27 | 0/27 | 0/27 |
| pet_name | 15/27 | 5/27 | 2/27 | 1/27 |
| sibling_name | 20/27 | 0/27 | 0/27 | 0/27 |
| street | 13/27 | 7/27 | 2/27 | 2/27 |

D-26 confirmations (3; 2.2047451182636117 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 32 | False | 2666.2807677080054 | 2026-10-10T09:29:50.135384+00:00 | 2026-10-10T10:14:16.433042+00:00 |
| 48 | False | 2647.5079773749967 | 2026-10-10T10:27:44.131935+00:00 | 2026-10-10T11:11:51.551588+00:00 |
| 64 | True | 2623.293680666 | 2026-10-10T11:25:10.429550+00:00 | 2026-10-10T12:08:53.710367+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 9/27 | -0.3333333333333333 | True | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 25/27 | -0.07407407407407407 | False | não | 27-27 | 27-27 |
| hometown | 21/27 | 0/27 | -0.7777777777777778 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 9/27 | -0.5555555555555556 | True | não | 20-24 | 17-24 |
| person_name | 26/27 | 0/27 | -0.9629629629629629 | True | não | 26-27 | 25-26 |
| pet_name | 27/27 | 3/27 | -0.8888888888888888 | True | não | 25-27 | — |
| street | 27/27 | 6/27 | -0.7777777777777778 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.3276411208388508 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 4 unlabelled (person_name, pet_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.81055410521704 | 4.219759892336485 | None | 3.9085032379884783 | sim |

D-18: sem M2, comparação não feita.

### cell_sibling_name_greedy_seed2024

Verdict **FAILURE** at stop 64; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 26/27 | 1 | False | None |
| 32 | 6/27 | 1 | False | None |
| 48 | 2/27 | 2 | False | None |
| 64 | 0/27 | 2 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 | 64 |
|---|---|---|---|---|
| birth_year | 7/27 | 3/27 | 1/27 | 1/27 |
| cat_name | 27/27 | 21/27 | 18/27 | 11/27 |
| hometown | 2/27 | 0/27 | 0/27 | 0/27 |
| house_number | 9/27 | 1/27 | 1/27 | 1/27 |
| person_name | 18/27 | 2/27 | 0/27 | 0/27 |
| pet_name | 22/27 | 8/27 | 6/27 | 1/27 |
| sibling_name | 26/27 | 6/27 | 2/27 | 0/27 |
| street | 25/27 | 5/27 | 1/27 | 0/27 |

D-26 confirmations (1; 0.8129521409374987 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 64 | True | 2926.627707374995 | 2026-10-10T13:11:12.757889+00:00 | 2026-10-10T13:59:59.454938+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 5/27 | -0.4074074074074074 | True | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 24/27 | -0.11111111111111116 | False | não | 27-27 | 27-27 |
| hometown | 22/27 | 0/27 | -0.8148148148148148 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 4/27 | -0.7037037037037037 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 0/27 | -1.0 | True | não | 26-27 | 25-26 |
| pet_name | 26/27 | 2/27 | -0.8888888888888888 | True | não | 25-27 | — |
| street | 27/27 | 3/27 | -0.8888888888888888 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.3774336021947162 in [0.6184411071680209, 1.4050216216579918]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 4 unlabelled (person_name, pet_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.8991920515636798 | 4.2284415113307245 | None | 3.9085032379884783 | sim |

D-18: sem M2, comparação não feita.

### cell_pet_name_gradient_seed1337

Verdict **FAILURE** at stop 32; failed conditions: (b), (c); non-targets beyond the margin: person_name, sibling_name, hometown, street, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 7/27 | 1 | False | None |
| 32 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 |
|---|---|---|
| birth_year | 3/27 | 4/27 |
| cat_name | 26/27 | 16/27 |
| hometown | 2/27 | 0/27 |
| house_number | 14/27 | 3/27 |
| person_name | 6/27 | 1/27 |
| pet_name | 7/27 | 0/27 |
| sibling_name | 14/27 | 3/27 |
| street | 26/27 | 4/27 |

D-26 confirmations (1; 0.7286836542475026 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 32 | True | 2623.2611552910093 | 2026-10-10T14:26:46.379424+00:00 | 2026-10-10T15:10:29.567644+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 11/27 | -0.25925925925925924 | False | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 26/27 | -0.03703703703703709 | False | não | 27-27 | 27-27 |
| hometown | 21/27 | 0/27 | -0.7777777777777778 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 13/27 | -0.4074074074074074 | True | não | 20-24 | 17-24 |
| person_name | 26/27 | 1/27 | -0.9259259259259258 | True | não | 26-27 | 25-26 |
| sibling_name | 27/27 | 11/27 | -0.5925925925925926 | True | não | 27-27 | 27-27 |
| street | 27/27 | 7/27 | -0.7407407407407407 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.5354487006979092 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 4 unlabelled (person_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.815572846490399 | 4.219759892336485 | 4.217157524257963 | 3.9085032379884783 | sim |

D-18 M1 x M2 (descriptive; 'fora da faixa' não é teste estatístico: duas seeds contra cinco retreinos do M2):

| slot | full | M1 | M2 | M1 - full | M2 - full | M2 min-max | M1 |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 11/27 | 18/27 | -0.25925925925925924 | 0.0 | 12-25 | fora da faixa |
| cat_name | 27/27 | 26/27 | 27/27 | -0.03703703703703709 | 0.0 | 27-27 | fora da faixa |
| hometown | 21/27 | 0/27 | 18/27 | -0.7777777777777778 | -0.11111111111111116 | 8-25 | fora da faixa |
| house_number | 24/27 | 13/27 | 17/27 | -0.4074074074074074 | -0.2592592592592592 | 17-24 | fora da faixa |
| person_name | 26/27 | 1/27 | 26/27 | -0.9259259259259258 | 0.0 | 25-26 | fora da faixa |
| sibling_name | 27/27 | 11/27 | 27/27 | -0.5925925925925926 | 0.0 | 27-27 | fora da faixa |
| street | 27/27 | 7/27 | 27/27 | -0.7407407407407407 | 0.0 | 27-27 | fora da faixa |

D-20 D-13 at the stop beside Phase 40's M2 range (descriptive):

| reading | value | M2 range | label |
|---|---|---|---|
| anchor_512 | 2 | 15-41 | fora da faixa |
| r_q_committed | 17 | 0-1 | fora da faixa |
| r_q_minted | 27 | 9-12 | fora da faixa |

### cell_pet_name_gradient_seed2024

Verdict **FAILURE** at stop 32; failed conditions: (b), (c); non-targets beyond the margin: person_name, sibling_name, hometown, street, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 12/27 | 1 | False | None |
| 32 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 |
|---|---|---|
| birth_year | 8/27 | 3/27 |
| cat_name | 27/27 | 14/27 |
| hometown | 6/27 | 0/27 |
| house_number | 12/27 | 1/27 |
| person_name | 10/27 | 2/27 |
| pet_name | 12/27 | 0/27 |
| sibling_name | 25/27 | 12/27 |
| street | 26/27 | 2/27 |

D-26 confirmations (1; 0.7514381764816669 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 32 | True | 2705.1774353340006 | 2026-10-10T15:38:46.470059+00:00 | 2026-10-10T16:23:51.744553+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 11/27 | -0.18518518518518517 | False | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 21/27 | -0.2222222222222222 | False | não | 27-27 | 27-27 |
| hometown | 22/27 | 2/27 | -0.7407407407407407 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 7/27 | -0.5925925925925926 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 4/27 | -0.8518518518518519 | True | não | 26-27 | 25-26 |
| sibling_name | 27/27 | 17/27 | -0.37037037037037035 | True | não | 27-27 | 27-27 |
| street | 27/27 | 6/27 | -0.7777777777777778 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.5851866058380066 in [0.6184411071680209, 1.4050216216579918]: holds False.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 4 unlabelled (person_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.906631832045043 | 4.2284415113307245 | 4.206715106532572 | 3.9085032379884783 | sim |

D-18 M1 x M2 (descriptive; 'fora da faixa' não é teste estatístico: duas seeds contra cinco retreinos do M2):

| slot | full | M1 | M2 | M1 - full | M2 - full | M2 min-max | M1 |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 11/27 | 18/27 | -0.18518518518518517 | 0.07407407407407407 | 12-25 | fora da faixa |
| cat_name | 27/27 | 21/27 | 27/27 | -0.2222222222222222 | 0.0 | 27-27 | fora da faixa |
| hometown | 22/27 | 2/27 | 8/27 | -0.7407407407407407 | -0.5185185185185185 | 8-25 | fora da faixa |
| house_number | 23/27 | 7/27 | 23/27 | -0.5925925925925926 | 0.0 | 17-24 | fora da faixa |
| person_name | 27/27 | 4/27 | 26/27 | -0.8518518518518519 | -0.03703703703703709 | 25-26 | fora da faixa |
| sibling_name | 27/27 | 17/27 | 27/27 | -0.37037037037037035 | 0.0 | 27-27 | fora da faixa |
| street | 27/27 | 6/27 | 27/27 | -0.7777777777777778 | 0.0 | 27-27 | fora da faixa |

D-20 D-13 at the stop beside Phase 40's M2 range (descriptive):

| reading | value | M2 range | label |
|---|---|---|---|
| anchor_512 | 1 | 15-41 | fora da faixa |
| r_q_committed | 17 | 0-1 | fora da faixa |
| r_q_minted | 27 | 9-12 | fora da faixa |

### cell_cat_name_gradient_seed1337

Verdict **FAILURE** at stop 48; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, sibling_name, hometown, street, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 20/27 | 1 | False | None |
| 32 | 1/27 | 1 | False | None |
| 48 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 |
|---|---|---|---|
| birth_year | 4/27 | 2/27 | 2/27 |
| cat_name | 20/27 | 1/27 | 0/27 |
| hometown | 10/27 | 0/27 | 0/27 |
| house_number | 9/27 | 8/27 | 2/27 |
| person_name | 11/27 | 4/27 | 0/27 |
| pet_name | 23/27 | 10/27 | 1/27 |
| sibling_name | 26/27 | 15/27 | 1/27 |
| street | 16/27 | 0/27 | 0/27 |

D-26 confirmations (1; 0.9827103326619423 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 48 | True | 3537.7571975829924 | 2026-10-10T17:14:09.523985+00:00 | 2026-10-10T18:13:07.308272+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 10/27 | -0.2962962962962963 | False | sim | 16-24 | 12-25 |
| hometown | 21/27 | 0/27 | -0.7777777777777778 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 6/27 | -0.6666666666666666 | True | não | 20-24 | 17-24 |
| person_name | 26/27 | 0/27 | -0.9629629629629629 | True | não | 26-27 | 25-26 |
| pet_name | 27/27 | 3/27 | -0.8888888888888888 | True | não | 25-27 | — |
| sibling_name | 27/27 | 4/27 | -0.8518518518518519 | True | não | 27-27 | 27-27 |
| street | 27/27 | 0/27 | -1.0 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.46677854831257815 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 5 unlabelled (person_name, pet_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.8604412614641976 | 4.219759892336485 | None | 3.9085032379884783 | sim |

D-18: sem M2, comparação não feita.

### cell_cat_name_gradient_seed2024

Verdict **FAILURE** at stop 48; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, sibling_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 10/27 | 1 | False | None |
| 32 | 1/27 | 1 | False | None |
| 48 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 |
|---|---|---|---|
| birth_year | 11/27 | 2/27 | 0/27 |
| cat_name | 10/27 | 1/27 | 0/27 |
| hometown | 5/27 | 0/27 | 0/27 |
| house_number | 13/27 | 2/27 | 0/27 |
| person_name | 18/27 | 5/27 | 0/27 |
| pet_name | 16/27 | 3/27 | 0/27 |
| sibling_name | 24/27 | 18/27 | 0/27 |
| street | 14/27 | 2/27 | 0/27 |

D-26 confirmations (1; 0.8826874648611112 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 48 | True | 3177.6748735 | 2026-10-10T18:58:40.277453+00:00 | 2026-10-10T19:51:37.902067+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 4/27 | -0.4444444444444444 | True | sim | 16-24 | 12-25 |
| hometown | 22/27 | 0/27 | -0.8148148148148148 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 0/27 | -0.8518518518518519 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 1/27 | -0.962962962962963 | True | não | 26-27 | 25-26 |
| pet_name | 26/27 | 0/27 | -0.9629629629629629 | True | não | 25-27 | — |
| sibling_name | 27/27 | 1/27 | -0.962962962962963 | True | não | 27-27 | 27-27 |
| street | 27/27 | 1/27 | -0.962962962962963 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.42879734495392086 in [0.6184411071680209, 1.4050216216579918]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 5 unlabelled (person_name, pet_name, sibling_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.9626112867214878 | 4.2284415113307245 | None | 3.9085032379884783 | não |

D-18: sem M2, comparação não feita.

### cell_street_gradient_seed1337

Verdict **FAILURE** at stop 32; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, sibling_name, hometown, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 1/27 | 1 | False | None |
| 32 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 |
|---|---|---|
| birth_year | 6/27 | 6/27 |
| cat_name | 25/27 | 14/27 |
| hometown | 5/27 | 0/27 |
| house_number | 9/27 | 3/27 |
| person_name | 7/27 | 0/27 |
| pet_name | 19/27 | 4/27 |
| sibling_name | 20/27 | 7/27 |
| street | 1/27 | 0/27 |

D-26 confirmations (1; 0.8318621073497222 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 32 | True | 2994.703586459 | 2026-10-10T20:20:50.256793+00:00 | 2026-10-10T21:10:44.981194+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 15/27 | -0.11111111111111105 | False | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 25/27 | -0.07407407407407407 | False | não | 27-27 | 27-27 |
| hometown | 21/27 | 2/27 | -0.7037037037037037 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 14/27 | -0.37037037037037035 | True | não | 20-24 | 17-24 |
| person_name | 26/27 | 0/27 | -0.9629629629629629 | True | não | 26-27 | 25-26 |
| pet_name | 27/27 | 9/27 | -0.6666666666666667 | True | não | 25-27 | — |
| sibling_name | 27/27 | 14/27 | -0.4814814814814815 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.4956451237532926 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 4 unlabelled (person_name, pet_name, sibling_name, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 4.004827416483449 | 4.219759892336485 | None | 3.9085032379884783 | não |

D-18: sem M2, comparação não feita.

### cell_street_gradient_seed2024

Verdict **FAILURE** at stop 32; failed conditions: (b); non-targets beyond the margin: person_name, hometown, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 0/27 | 1 | True | False |
| 32 | 0/27 | 1 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 |
|---|---|---|
| birth_year | 6/27 | 4/27 |
| cat_name | 26/27 | 26/27 |
| hometown | 4/27 | 1/27 |
| house_number | 10/27 | 5/27 |
| person_name | 13/27 | 5/27 |
| pet_name | 21/27 | 10/27 |
| sibling_name | 26/27 | 19/27 |
| street | 0/27 | 0/27 |

D-26 confirmations (2; 1.3544922556136145 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 16 | False | 2433.52507704201 | 2026-10-10T21:23:43.133232+00:00 | 2026-10-10T22:04:16.651476+00:00 |
| 32 | True | 2442.6470431670023 | 2026-10-10T22:16:45.237098+00:00 | 2026-10-10T22:57:27.912487+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 11/27 | -0.18518518518518517 | False | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 27/27 | 0.0 | False | não | 27-27 | 27-27 |
| hometown | 22/27 | 3/27 | -0.7037037037037037 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 9/27 | -0.5185185185185186 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 10/27 | -0.6296296296296297 | True | não | 26-27 | 25-26 |
| pet_name | 26/27 | 21/27 | -0.18518518518518512 | False | não | 25-27 | — |
| sibling_name | 27/27 | 25/27 | -0.07407407407407407 | False | não | 27-27 | 27-27 |

(c): dialogue gap 0.6739550433469992 in [0.6184411071680209, 1.4050216216579918]: holds True.

D-19: beyond the margin, 1 labelled "varia entre seeds" (hometown) and 2 unlabelled (person_name, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.986195938895965 | 4.2284415113307245 | None | 3.9085032379884783 | não |

D-18: sem M2, comparação não feita.

### cell_sibling_name_gradient_seed1337

Verdict **FAILURE** at stop 48; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 20/27 | 1 | False | None |
| 32 | 4/27 | 2 | False | None |
| 48 | 0/27 | 4 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 |
|---|---|---|---|
| birth_year | 7/27 | 4/27 | 4/27 |
| cat_name | 27/27 | 26/27 | 25/27 |
| hometown | 6/27 | 0/27 | 0/27 |
| house_number | 12/27 | 5/27 | 3/27 |
| person_name | 8/27 | 0/27 | 0/27 |
| pet_name | 15/27 | 4/27 | 2/27 |
| sibling_name | 20/27 | 4/27 | 0/27 |
| street | 13/27 | 8/27 | 1/27 |

D-26 confirmations (1; 0.7886892578241693 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 48 | True | 2839.2813281670096 | 2026-10-10T23:39:45.010038+00:00 | 2026-10-11T00:27:04.268413+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 18/27 | 9/27 | -0.3333333333333333 | True | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 26/27 | -0.03703703703703709 | False | não | 27-27 | 27-27 |
| hometown | 21/27 | 0/27 | -0.7777777777777778 | True | sim | 8-22 | 8-25 |
| house_number | 24/27 | 8/27 | -0.5925925925925926 | True | não | 20-24 | 17-24 |
| person_name | 26/27 | 0/27 | -0.9629629629629629 | True | não | 26-27 | 25-26 |
| pet_name | 27/27 | 2/27 | -0.9259259259259259 | True | não | 25-27 | — |
| street | 27/27 | 2/27 | -0.9259259259259259 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.31465001110647073 in [0.6210483312521959, 1.4102360698263419]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 4 unlabelled (person_name, pet_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.751230914296576 | 4.219759892336485 | None | 3.9085032379884783 | sim |

D-18: sem M2, comparação não feita.

### cell_sibling_name_gradient_seed2024

Verdict **FAILURE** at stop 48; failed conditions: (b), (c); non-targets beyond the margin: person_name, pet_name, hometown, street, birth_year, house_number; INCONCLUSIVE reason: none.

Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never read by the stop):

| checkpoint | target n/q | rank | K = read_k zero | K = confirm_k zero |
|---|---|---|---|---|
| 16 | 25/27 | 1 | False | None |
| 32 | 5/27 | 2 | False | None |
| 48 | 0/27 | 4 | True | True |

Per-fact counts at every checkpoint (K = read_k):

| slot | 16 | 32 | 48 |
|---|---|---|---|
| birth_year | 7/27 | 4/27 | 1/27 |
| cat_name | 27/27 | 26/27 | 24/27 |
| hometown | 1/27 | 1/27 | 0/27 |
| house_number | 8/27 | 2/27 | 0/27 |
| person_name | 11/27 | 1/27 | 0/27 |
| pet_name | 21/27 | 8/27 | 3/27 |
| sibling_name | 25/27 | 5/27 | 0/27 |
| street | 23/27 | 1/27 | 0/27 |

D-26 confirmations (1; 0.7635737570486122 h):

| checkpoint | K = confirm_k zero | seconds | started | finished |
|---|---|---|---|---|
| 48 | True | 2748.865525375004 | 2026-10-11T01:08:25.490005+00:00 | 2026-10-11T01:54:14.355104+00:00 |

(a): Wilson upper 0.09107873950450847 against the floor 0.09107873950450847: holds True (vazia no ponto de parada julgado: o alvo está em 0).

(b): every non-target against the same seed's intact full adapter, margin 0.2962962962962963 compared exactly; holds False:

| slot | pre | post | delta | beyond | varia entre seeds | full min-max | m2 min-max |
|---|---|---|---|---|---|---|---|
| birth_year | 16/27 | 6/27 | -0.37037037037037035 | True | sim | 16-24 | 12-25 |
| cat_name | 27/27 | 27/27 | 0.0 | False | não | 27-27 | 27-27 |
| hometown | 22/27 | 0/27 | -0.8148148148148148 | True | sim | 8-22 | 8-25 |
| house_number | 23/27 | 1/27 | -0.8148148148148149 | True | não | 20-24 | 17-24 |
| person_name | 27/27 | 0/27 | -1.0 | True | não | 26-27 | 25-26 |
| pet_name | 26/27 | 6/27 | -0.7407407407407407 | True | não | 25-27 | — |
| street | 27/27 | 0/27 | -1.0 | True | não | 27-27 | 27-27 |

(c): dialogue gap 0.48826625849410377 in [0.6184411071680209, 1.4050216216579918]: holds False.

D-19: beyond the margin, 2 labelled "varia entre seeds" (hometown, birth_year) and 4 unlabelled (person_name, pet_name, street, house_number); (b) would fail on the unlabelled alone: True.

D-14 retention_ppl (descriptive, no verdict):

| stop | intact full | m2 | v4.0 cap | passaria no teto do v4.0 |
|---|---|---|---|---|
| 3.9263923679353683 | 4.2284415113307245 | None | 3.9085032379884783 | não |

D-18: sem M2, comparação não feita.

## (a) floors and the calibrations (D-12, D-06, D-11; WR-01)

(a) é vazia no ponto de parada julgado: the stop requires the target at 0, so (a) holds by construction. The four calibrations (0.9914206175 h measured) feed only D-12. The entry: ERASE-06, D-10: condition (a) reads the target's Wilson upper bound against the floor of its own (target, ordering, seed). WR-01 (Rafael 2026-10-08, 41-05 review): (a) is vacuous at the judged stop point. The stop requires the target's K = confirm_k count 0/27 (stop_rule, phase35_prereg.e1_stop), so the bound is wilson_upper_bound(0, 27) = phase19_erasure.ERASURE_FLOOR_MIN and every floor is at least that (lock_erasure_floor = max(ERASURE_FLOOR_MIN, ...)): (a) holds by construction, cell_verdict asserts it, and it cannot decide a verdict. The calibrations stay: 4 x unit_prices.e1_calibration_seconds = 1.245 h (computed), and they feed only D-12's side-by-side table.

| ordering | seed | calibration rate | successes/questions | floor | floor_branch |
|---|---|---|---|---|---|
| greedy | 1337 | 0.0 | 0/23 | 0.09107873950450847 | reachability-min |
| greedy | 2024 | 0.0 | 0/23 | 0.09107873950450847 | reachability-min |
| gradient | 1337 | 0.0 | 0/23 | 0.09107873950450847 | reachability-min |
| gradient | 2024 | 0.0 | 0/23 | 0.09107873950450847 | reachability-min |

| seed | D-06 Spearman rho (gradient vs greedy) | D-11 reference sha256 matches record | D-11 tensor-identical | D-11 max abs diff | D-11 finding |
|---|---|---|---|---|---|
| 1337 | 0.9907838314665895 | True | True | 0.0 | None |
| 2024 | 0.987948048659923 | True | False | 0.15108296275138855 | None |

## (c) bands (D-13)

| seed\|ordering | lo | hi |
|---|---|---|
| 1337\|greedy | 0.6210483312521959 | 1.4102360698263419 |
| 1337\|gradient | 0.6210483312521959 | 1.4102360698263419 |
| 2024\|greedy | 0.6184411071680209 | 1.4050216216579918 |
| 2024\|gradient | 0.6184411071680209 | 1.4050216216579918 |

## D-19 / D-28 labels

"varia entre seeds": birth_year, hometown (the label never discounts a delta nor enters a verdict).

| slot | basis | range |
|---|---|---|
| birth_year | full and m2 | 0.4814814814814815 |
| cat_name | full and m2 | 0.0 |
| hometown | full and m2 | 0.6296296296296297 |
| house_number | full and m2 | 0.2592592592592592 |
| person_name | full and m2 | 0.03703703703703709 |
| pet_name | full only | 0.07407407407407407 |
| sibling_name | full and m2 | 0.0 |
| street | full and m2 | 0.0 |

The rule: 'varia entre seeds' when max(recall_floor.full.per_slot[slot].range, recall_floor.m2.per_slot[slot].range) >= E1_CONDITION_B_MARGIN, compared exactly (CR-01); pet_name as a non-target from the five Phase 40 full A2 records only (D-28: no pet_name row in recall_floor; one-group basis stated); computed, never typed; both groups' min-max beside each delta; per cell the count of slots beyond the margin among labelled and unlabelled slots and whether (b) would fail on the unlabelled slots alone; the label never discounts a delta nor enters a verdict.

## D-14 retention spread

| group | min | max | range | n |
|---|---|---|---|---|
| full | 4.155725635119946 | 4.3317421359777635 | 0.17601650085781717 | 5 |
| m2 | 4.206715106532572 | 4.433319345887968 | 0.22660423935539598 | 5 |

Beside the two-seed retention noise floor 0.008681618994239138.

## D-18 / D-20 / D-21

D-18: pet_name cells only: per non-target, full intact, M1 at the stop and M2 of the same seed (each /27) with M1 - full and M2 - full, the min-max of recall_floor.m2.per_slot[slot].counts over the five Phase 40 M2 seeds beside, and 'dentro da faixa' / 'fora da faixa' for M1's count, compared exactly (CR-01); other targets: 'sem M2, comparação não feita'; 'fora da faixa' is not a statistical test (two seeds against five retrains). "fora da faixa" não é teste estatístico (two seeds against five M2 retrains).

D-20: pet_name cells only, at the stop: phase40_noise.d13_scores on the M1 adapter (anchor rank at 8/32/128/512, R_q n1 on the committed and minted lists), each beside the min-max of results/phase40_noise_floor.json d13.blocks over the five M2 seeds with 'dentro'/'fora'; descriptive; a scoring failure is recorded as not measured, never drops the cell.

D-21 (descriptive, never a criterion): in all 4 pet_name cells, R_q n1 falls outside the M2 range on both lists and the anchor rank at 512 inside; the (1337, greedy) cell repeats Phase 39's reading only if it stops at 64 (R_q n1 11/27 there); descriptive; a mismatch is a finding, not a failure

| pet_name cell | reading |
|---|---|
| greedy\|1337 | not held |
| greedy\|2024 | not held |
| gradient\|1337 | not held |
| gradient\|2024 | not held |

Prediction held: False.

## Predictions (descriptive; a mismatch is a finding, not a failure)

| prediction | held |
|---|---|
| d02_cpu_equality | None |
| d11_calibration_identity | True |
| d21_d13_at_stop | False |
| greedy_1337_phase19_prefix | True |

d02_cpu_equality: D-02 equality on CPU was established in the CPU rehearsal (.planning/phases/41-erasure-across-facts-orderings-and-seeds/41-11-SUMMARY.md:172-176 (commit 2098294)), and on mps it is verified at every gradient of this run; d02_cpu_equality is None because no gradient of this run runs on CPU.

## D-08 end point (cited, never re-measured)

results/phase18_arm_adapter-off.json (sha256 08fe96fbd9753f8b44a5eb67a69d1a2a0b062a666b5a2d5430c2a7476bb15535), readings by exposure:

| slot | reading |
|---|---|
| birth_year | {"n_references": 7, "nll_mean": 3.8696608543395996, "rank": 3} |
| cat_name | {"n_references": 7, "nll_mean": 4.222026824951172, "rank": 3} |
| hometown | {"n_references": 7, "nll_mean": 6.668754577636719, "rank": 5} |
| house_number | {"n_references": 6, "nll_mean": 4.500420570373535, "rank": 5} |
| person_name | {"n_references": 8, "nll_mean": 5.154366493225098, "rank": 5} |
| pet_name | {"n_references": 8, "nll_mean": 5.364222526550293, "rank": 4} |
| sibling_name | {"n_references": 7, "nll_mean": 5.16510534286499, "rank": 4} |
| street | {"n_references": 6, "nll_mean": 4.455621242523193, "rank": 3} |

## Hours

E1 spent (ledger): 32.3751665625 h; D-26 confirmations: 18.46044798445584 h; calibrations: 0.9914206175 h.

## Provenance

- emitted 2026-10-13T00:23:21.263552+00:00 at 67f4aecf2ccdf703f2666baa4c473706afe7eb57
- 109 input records, each with its sha256 in the erasure record
