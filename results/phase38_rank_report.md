# Phase 38 — E5 exposure rank at larger minted sets

## Status

Status: **SCORED** — run `v6/38/E5/rank`, front E5, device `mps`, launched at `ccd5d7e01532f1c14eb20d1f2ad66c0a6d32ad13`.

## Approval and cost (D-21/D-22/D-23)

D-21 ruling (verbatim): "aprovo o teto de prefixos do E5 de 6 para 8 (D-09). approved" (38-CONTEXT D-21/D-22/D-23 (255380f)).

- approved_prefixes: 8
- committed_prefix_cap: 6
- e5_projection_hours: 0.467956566879681
- committed_front_hours_e5: 0.3612376740339419
- e5_total_hours: 77.83105039182757
- committed_total_hours: 77.72433149898184
- e5_stop_hours: 0.5418565110509128
- budget_record: 'results/phase36_budget.json'
- run_hours (this run's clock): 0.08427317444444445

## Gate: committed reference sets (D-18, D-11a)

Passed: True. The rank on each committed reference set (|R| as committed) against the committed rank, before any minted value was scored.

| reading | slot | \|R\| | rank | committed rank | equal | taught NLL | abs diff |
|---|---|---|---|---|---|---|---|
| k0 | person_name | 8 | 1 | 1 | True | 0.4091116487979889 | 0.0 |
| k0 | pet_name | 8 | 1 | 1 | True | 0.13365373015403748 | 0.0 |
| k0 | cat_name | 7 | 1 | 1 | True | 0.20872001349925995 | 0.0 |
| k0 | sibling_name | 7 | 1 | 1 | True | 2.3904333114624023 | 0.0 |
| k0 | hometown | 7 | 1 | 1 | True | 3.1255314350128174 | 0.0 |
| k0 | street | 6 | 1 | 1 | True | 0.24566514790058136 | 0.0 |
| k0 | birth_year | 7 | 1 | 1 | True | 1.2660512924194336 | 0.0 |
| k0 | house_number | 6 | 1 | 1 | True | 1.1385736465454102 | 0.0 |
| k8 | person_name | 8 | 1 | 1 | True | 0.780152440071106 | 0.0 |
| k8 | pet_name | 8 | 1 | 1 | True | 0.4921519160270691 | 0.0 |
| k8 | cat_name | 7 | 1 | 1 | True | 0.2840718626976013 | 0.0 |
| k8 | sibling_name | 7 | 1 | 1 | True | 2.9647789001464844 | 0.0 |
| k8 | hometown | 7 | 1 | 1 | True | 3.707454204559326 | 0.0 |
| k8 | street | 6 | 1 | 1 | True | 0.35777321457862854 | 0.0 |
| k8 | birth_year | 7 | 1 | 1 | True | 1.4283742904663086 | 0.0 |
| k8 | house_number | 6 | 1 | 1 | True | 1.257467269897461 | 0.0 |
| k16 | person_name | 8 | 1 | 1 | True | 1.1123952865600586 | 0.0 |
| k16 | pet_name | 8 | 1 | 1 | True | 1.135831356048584 | 0.0 |
| k16 | cat_name | 7 | 1 | 1 | True | 0.4658830761909485 | 0.0 |
| k16 | sibling_name | 7 | 1 | 1 | True | 3.3190841674804688 | 0.0 |
| k16 | hometown | 7 | 1 | 1 | True | 4.095652103424072 | 0.0 |
| k16 | street | 6 | 1 | 1 | True | 0.6098215579986572 | 0.0 |
| k16 | birth_year | 7 | 1 | 1 | True | 1.5613740682601929 | 0.0 |
| k16 | house_number | 6 | 1 | 1 | True | 1.4082632064819336 | 0.0 |
| k32 | person_name | 8 | 1 | 1 | True | 1.7987492084503174 | 0.0 |
| k32 | pet_name | 8 | 1 | 1 | True | 2.2271080017089844 | 0.0 |
| k32 | cat_name | 7 | 1 | 1 | True | 0.7392634153366089 | 0.0 |
| k32 | sibling_name | 7 | 1 | 1 | True | 3.8008155822753906 | 0.0 |
| k32 | hometown | 7 | 1 | 1 | True | 4.489480972290039 | 0.0 |
| k32 | street | 6 | 1 | 1 | True | 1.1693369150161743 | 0.0 |
| k32 | birth_year | 7 | 1 | 1 | True | 1.7050918340682983 | 0.0 |
| k32 | house_number | 6 | 1 | 1 | True | 1.6820329427719116 | 0.0 |
| k64 | person_name | 8 | 1 | 1 | True | 2.873643398284912 | 0.0 |
| k64 | pet_name | 8 | 1 | 1 | True | 3.652377128601074 | 0.0 |
| k64 | cat_name | 7 | 1 | 1 | True | 1.6505779027938843 | 0.0 |
| k64 | sibling_name | 7 | 1 | 1 | True | 4.4556708335876465 | 0.0 |
| k64 | hometown | 7 | 1 | 1 | True | 4.980170726776123 | 0.0 |
| k64 | street | 6 | 1 | 1 | True | 1.8354833126068115 | 0.0 |
| k64 | birth_year | 7 | 1 | 1 | True | 1.9145342111587524 | 0.0 |
| k64 | house_number | 6 | 1 | 1 | True | 1.9029037952423096 | 0.0 |
| k78 | person_name | 8 | 1 | 1 | True | 3.417057514190674 | 0.0 |
| k78 | pet_name | 8 | 2 | 2 | True | 4.109549522399902 | 0.0 |
| k78 | cat_name | 7 | 1 | 1 | True | 1.9792289733886719 | 0.0 |
| k78 | sibling_name | 7 | 1 | 1 | True | 4.726539611816406 | 0.0 |
| k78 | hometown | 7 | 1 | 1 | True | 5.124383449554443 | 0.0 |
| k78 | street | 6 | 1 | 1 | True | 1.9356025457382202 | 0.0 |
| k78 | birth_year | 7 | 1 | 1 | True | 2.0874438285827637 | 0.0 |
| k78 | house_number | 6 | 1 | 1 | True | 2.0123889446258545 | 0.0 |
| M2 | person_name | 8 | 1 | 1 | True | 0.2684493958950043 | 0.0 |
| M2 | pet_name | 8 | 2 | 2 | True | 4.429786682128906 | 0.0 |
| M2 | cat_name | 7 | 1 | 1 | True | 0.192317932844162 | 0.0 |
| M2 | sibling_name | 7 | 1 | 1 | True | 3.0714681148529053 | 0.0 |
| M2 | hometown | 7 | 1 | 1 | True | 3.090094566345215 | 0.0 |
| M2 | street | 6 | 1 | 1 | True | 0.15620459616184235 | 0.0 |
| M2 | birth_year | 7 | 1 | 1 | True | 1.2483243942260742 | 0.0 |
| M2 | house_number | 6 | 1 | 1 | True | 1.4145002365112305 | 0.0 |
| adapter_off | person_name | 8 | 5 | 5 | True | 5.154366493225098 | 0.0 |
| adapter_off | pet_name | 8 | 4 | 4 | True | 5.364222526550293 | 0.0 |
| adapter_off | cat_name | 7 | 3 | 3 | True | 4.222026824951172 | 0.0 |
| adapter_off | sibling_name | 7 | 4 | 4 | True | 5.16510534286499 | 0.0 |
| adapter_off | hometown | 7 | 5 | 5 | True | 6.668754577636719 | 0.0 |
| adapter_off | street | 6 | 3 | 3 | True | 4.455621242523193 | 0.0 |
| adapter_off | birth_year | 7 | 3 | 3 | True | 3.8696608543395996 | 0.0 |
| adapter_off | house_number | 6 | 5 | 5 | True | 4.500420570373535 | 0.0 |

## A2 counts, collapse and damage (D-13, D-14)

Committed A2 answered counts per prefix over n questions. Damage: the first k > 0 with a rate drop strictly above the margin 0.2962962962962963; collapse: the first k with 0 answered.

| slot | k0 | k8 | k16 | k32 | k64 | k78 | first damage | first collapse |
|---|---|---|---|---|---|---|---|---|
| person_name | 26/27 | 18/27 | 10/27 | 1/27 | 0/27 | 0/27 | k = 16 | k = 64 |
| pet_name | 27/27 | 24/27 | 18/27 | 2/27 | 0/27 | 0/27 | k = 16 | k = 64 |
| cat_name | 27/27 | 27/27 | 27/27 | 27/27 | 6/27 | 7/27 | k = 64 | never within the grid |
| sibling_name | 27/27 | 27/27 | 22/27 | 10/27 | 0/27 | 0/27 | k = 32 | k = 64 |
| hometown | 21/27 | 7/27 | 3/27 | 1/27 | 0/27 | 0/27 | k = 8 | k = 64 |
| street | 27/27 | 27/27 | 24/27 | 11/27 | 0/27 | 0/27 | k = 32 | k = 64 |
| birth_year | 18/27 | 14/27 | 13/27 | 14/27 | 11/27 | 8/27 | k = 78 | never within the grid |
| house_number | 24/27 | 24/27 | 24/27 | 10/27 | 6/27 | 5/27 | k = 32 | never within the grid |

## Drop formula audit (D-33)

The committed drop is pre/n - post/n; each cell where (pre - post)/n differs from it, with the damage verdict under each (margin 0.2962962962962963). Description, never a criterion.

| slot | k | rate_drop | count_drop | damaged (rate) | damaged (count) |
|---|---|---|---|---|---|
| person_name | 32 | 0.9259259259259258 | 0.9259259259259259 | True | True |
| pet_name | 8 | 0.11111111111111116 | 0.1111111111111111 | False | False |
| pet_name | 16 | 0.33333333333333337 | 0.3333333333333333 | True | True |
| sibling_name | 16 | 0.18518518518518523 | 0.18518518518518517 | False | False |
| hometown | 8 | 0.5185185185185186 | 0.5185185185185185 | True | True |
| hometown | 16 | 0.6666666666666667 | 0.6666666666666666 | True | True |
| street | 16 | 0.11111111111111116 | 0.1111111111111111 | False | False |

No damage event changes between the two formulas.
- `person_name` k = 8: exact margin tie decided by D-14's strict >

## Rank curves (D-15)

Each cell is rank (exposure bits = log2(|R| / rank)) of the taught value among the first |R| - 1 minted values plus itself. The M2 and adapter-off columns are descriptive (D-11, D-16).

| slot | \|R\| | k0 | k8 | k16 | k32 | k64 | k78 | M2 (descriptive) | adapter-off (descriptive) |
|---|---|---|---|---|---|---|---|---|---|
| person_name | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 2 (2.0) |
| person_name | 32 | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 7 (2.192645077942396) |
| person_name | 128 | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 3 (5.415037499278844) | 1 (7.0) | 26 (2.2995602818589083) |
| person_name | 512 | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 5 (6.678071905112638) | 1 (9.0) | 109 (2.231815675223074) |
| pet_name | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) |
| pet_name | 32 | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 4 (3.0) | 4 (3.0) | 4 (3.0) | 12 (1.415037499278844) |
| pet_name | 128 | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 7 (4.192645077942396) | 7 (4.192645077942396) | 10 (3.678071905112638) | 49 (1.3852901558847917) |
| pet_name | 512 | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 12 (5.415037499278844) | 16 (5.0) | 32 (4.0) | 171 (1.5821474851141017) |
| cat_name | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 2 (2.0) |
| cat_name | 32 | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 3 (3.415037499278844) |
| cat_name | 128 | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 9 (3.830074998557688) |
| cat_name | 512 | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 31 (4.045803689613125) |
| sibling_name | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 5 (0.6780719051126378) |
| sibling_name | 32 | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 13 (1.2995602818589078) |
| sibling_name | 128 | 1 (7.0) | 1 (7.0) | 1 (7.0) | 5 (4.678071905112638) | 8 (4.0) | 10 (3.678071905112638) | 2 (6.0) | 45 (1.5081469036703252) |
| sibling_name | 512 | 1 (9.0) | 1 (9.0) | 1 (9.0) | 6 (6.415037499278844) | 19 (4.752072486556415) | 28 (4.192645077942396) | 2 (8.0) | 130 (1.9776321869715456) |
| hometown | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 6 (0.4150374992788439) |
| hometown | 32 | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 2 (4.0) | 1 (5.0) | 23 (0.47643804394298694) |
| hometown | 128 | 1 (7.0) | 1 (7.0) | 2 (6.0) | 4 (5.0) | 7 (4.192645077942396) | 11 (3.5405683813627027) | 1 (7.0) | 84 (0.6076825772212393) |
| hometown | 512 | 1 (9.0) | 1 (9.0) | 3 (7.415037499278844) | 6 (6.415037499278844) | 19 (4.752072486556415) | 31 (4.045803689613125) | 1 (9.0) | 314 (0.7053792511083739) |
| street | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) |
| street | 32 | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 2 (4.0) |
| street | 128 | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 4 (5.0) |
| street | 512 | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 8 (6.0) |
| birth_year | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 5 (0.6780719051126378) |
| birth_year | 32 | 1 (5.0) | 2 (4.0) | 2 (4.0) | 2 (4.0) | 2 (4.0) | 3 (3.415037499278844) | 1 (5.0) | 17 (0.9125371587496609) |
| birth_year | 128 | 1 (7.0) | 2 (6.0) | 2 (6.0) | 3 (5.415037499278844) | 4 (5.0) | 7 (4.192645077942396) | 2 (6.0) | 69 (0.8914755432218309) |
| birth_year | 220 | 2 (6.78135971352466) | 3 (6.196397212803504) | 3 (6.196397212803504) | 4 (5.78135971352466) | 6 (5.196397212803504) | 10 (4.459431618637298) | 3 (6.196397212803504) | 113 (0.9611807511094721) |
| house_number | 8 | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 1 (3.0) | 6 (0.4150374992788439) |
| house_number | 32 | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 1 (5.0) | 18 (0.8300749985576878) |
| house_number | 128 | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 1 (7.0) | 72 (0.8300749985576878) |
| house_number | 512 | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 1 (9.0) | 288 (0.8300749985576878) |

## Did the rank move before generation collapsed? (D-12, D-29, D-30)

| slot | \|R\| | event | rank_0 | first k | first collapse | vs collapse | first damage | vs damage |
|---|---|---|---|---|---|---|---|---|
| person_name | 8 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| person_name | 8 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| person_name | 32 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| person_name | 32 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| person_name | 128 | moved (D-12) | 1 | k = 78 | k = 64 | AFTER | k = 16 | AFTER |
| person_name | 128 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| person_name | 512 | moved (D-12) | 1 | k = 78 | k = 64 | AFTER | k = 16 | AFTER |
| person_name | 512 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| pet_name | 8 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| pet_name | 8 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| pet_name | 32 | moved (D-12) | 1 | k = 64 | k = 64 | SAME | k = 16 | AFTER |
| pet_name | 32 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| pet_name | 128 | moved (D-12) | 1 | k = 64 | k = 64 | SAME | k = 16 | AFTER |
| pet_name | 128 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| pet_name | 512 | moved (D-12) | 1 | k = 64 | k = 64 | SAME | k = 16 | AFTER |
| pet_name | 512 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 16 | NEVER |
| cat_name | 8 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| cat_name | 8 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| cat_name | 32 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| cat_name | 32 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| cat_name | 128 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| cat_name | 128 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| cat_name | 512 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| cat_name | 512 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 64 | NEVER |
| sibling_name | 8 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| sibling_name | 8 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| sibling_name | 32 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| sibling_name | 32 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| sibling_name | 128 | moved (D-12) | 1 | k = 32 | k = 64 | BEFORE | k = 32 | SAME |
| sibling_name | 128 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| sibling_name | 512 | moved (D-12) | 1 | k = 32 | k = 64 | BEFORE | k = 32 | SAME |
| sibling_name | 512 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| hometown | 8 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 8 | NEVER |
| hometown | 8 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 8 | NEVER |
| hometown | 32 | moved (D-12) | 1 | k = 78 | k = 64 | AFTER | k = 8 | AFTER |
| hometown | 32 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 8 | NEVER |
| hometown | 128 | moved (D-12) | 1 | k = 16 | k = 64 | BEFORE | k = 8 | AFTER |
| hometown | 128 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 8 | NEVER |
| hometown | 512 | moved (D-12) | 1 | k = 16 | k = 64 | BEFORE | k = 8 | AFTER |
| hometown | 512 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 8 | NEVER |
| street | 8 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| street | 8 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| street | 32 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| street | 32 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| street | 128 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| street | 128 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| street | 512 | moved (D-12) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| street | 512 | left the top eighth (D-29) | 1 | never | k = 64 | NEVER | k = 32 | NEVER |
| birth_year | 8 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 78 | NEVER |
| birth_year | 8 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 78 | NEVER |
| birth_year | 32 | moved (D-12) | 1 | k = 8 | never within the grid | never collapsed within the grid | k = 78 | BEFORE |
| birth_year | 32 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 78 | NEVER |
| birth_year | 128 | moved (D-12) | 1 | k = 8 | never within the grid | never collapsed within the grid | k = 78 | BEFORE |
| birth_year | 128 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 78 | NEVER |
| birth_year | 220 | moved (D-12) | 2 | k = 32 | never within the grid | never collapsed within the grid | k = 78 | BEFORE |
| birth_year | 220 | left the top eighth (D-29) | 2 | never | never within the grid | never collapsed within the grid | k = 78 | NEVER |
| house_number | 8 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |
| house_number | 8 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |
| house_number | 32 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |
| house_number | 32 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |
| house_number | 128 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |
| house_number | 128 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |
| house_number | 512 | moved (D-12) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |
| house_number | 512 | left the top eighth (D-29) | 1 | never | never within the grid | never collapsed within the grid | k = 32 | NEVER |

## Numeric neighbour sensitivity (D-27, descriptive)

The numeric slots read again without the distance-1 neighbours of a taught value; descriptive only, never in any definition.

| slot | \|R\| | \|R\| without neighbours | k0 | k8 | k16 | k32 | k64 | k78 | M2 (descriptive) | adapter-off (descriptive) |
|---|---|---|---|---|---|---|---|---|---|---|
| birth_year | 8 | 6 | 1 (2.584962500721156) | 1 (2.584962500721156) | 1 (2.584962500721156) | 1 (2.584962500721156) | 1 (2.584962500721156) | 1 (2.584962500721156) | 1 (2.584962500721156) | 5 (0.2630344058337939) |
| birth_year | 32 | 21 | 1 (4.392317422778761) | 1 (4.392317422778761) | 1 (4.392317422778761) | 1 (4.392317422778761) | 1 (4.392317422778761) | 2 (3.3923174227787607) | 1 (4.392317422778761) | 14 (0.5849625007211565) |
| birth_year | 128 | 69 | 1 (6.108524456778169) | 1 (6.108524456778169) | 1 (6.108524456778169) | 2 (5.108524456778169) | 3 (4.523561956057013) | 6 (3.523561956057013) | 1 (6.108524456778169) | 40 (0.7865963618908065) |
| birth_year | 220 | 119 | 1 (6.894817763307944) | 1 (6.894817763307944) | 1 (6.894817763307944) | 2 (5.894817763307944) | 3 (5.309855262586788) | 6 (4.309855262586788) | 1 (6.894817763307944) | 64 (0.8948177633079437) |
| house_number | 8 | 7 | 1 (2.807354922057604) | 1 (2.807354922057604) | 1 (2.807354922057604) | 1 (2.807354922057604) | 1 (2.807354922057604) | 1 (2.807354922057604) | 1 (2.807354922057604) | 6 (0.2223924213364481) |
| house_number | 32 | 30 | 1 (4.906890595608519) | 1 (4.906890595608519) | 1 (4.906890595608519) | 1 (4.906890595608519) | 1 (4.906890595608519) | 1 (4.906890595608519) | 1 (4.906890595608519) | 17 (0.8194277543581796) |
| house_number | 128 | 118 | 1 (6.882643049361842) | 1 (6.882643049361842) | 1 (6.882643049361842) | 1 (6.882643049361842) | 1 (6.882643049361842) | 1 (6.882643049361842) | 1 (6.882643049361842) | 66 (0.8382489300033882) |
| house_number | 512 | 493 | 1 (8.945443836377912) | 1 (8.945443836377912) | 1 (8.945443836377912) | 1 (8.945443836377912) | 1 (8.945443836377912) | 1 (8.945443836377912) | 1 (8.945443836377912) | 277 (0.831701670328723) |

## CPU cross-check (D-19, descriptive)

Criterion: False (descriptive only). The CPU rank (cpu, torch 2.7.1) differs from the run's rank in 0 of 256 (reading, slot, size) cells and in 0 of 64 gate cells.


## Rehearsal disclosure (D-34)

The CPU rehearsal (38-07) read pet_name, birth_year at |R| 8 under 8 readings, minted candidates included, before the driver review and the MPS run (D-34).

- slice read: slots pet_name, birth_year, |R| 8, readings k0, k8, k16, k32, k64, k78, M2, adapter_off
- rehearsal git sha: `91553d96845701012a3fa0352d4223e8466b2b93`
- launch git sha: `ccd5d7e01532f1c14eb20d1f2ad66c0a6d32ad13`
- driver changed: True

| module | rehearsal sha256 | launch sha256 | changed |
|---|---|---|---|
| scripts/phase38_rank.py | `f887d4374aba17552d7873b090e867d7d9a1dfc7dfd1c0f738f59afc2f66381d` | `19ed947675217ee775938c5e10961d3d53f54f5e0a03c5a99d4b8b3297c803aa` | True |
| scripts/phase38_sizes_prereg.py | `18f37b0b50fbbd8f0f43797113ce64d3c162e1eb0bedda887e35cf52f045991c` | `18f37b0b50fbbd8f0f43797113ce64d3c162e1eb0bedda887e35cf52f045991c` | False |

- `1e683306155b9316eb1a3fd8343f998d428c9f9c` fix(38-07): escape pipes in report table cells — the CPU rehearsal report's |R| headers broke every GFM table (header cells != delimiter cells) (touched: scripts/phase38_rank.py)

## Limitations (D-36)

The name/place candidates are grammar syllables while the taught values look like English compound words, so at the same token count the base model may prefer the taught values.
Read each curve beside the "adapter-off (descriptive)" column of the same slot and size.

## Provenance

- device: `mps`
- finished_utc: `2026-10-04T18:58:57.142378+00:00`
- git_sha_at_end: `ccd5d7e01532f1c14eb20d1f2ad66c0a6d32ad13`
- git_sha_at_launch: `ccd5d7e01532f1c14eb20d1f2ad66c0a6d32ad13`
- head_moved_during_run: `False`
- started_utc: `2026-10-04T18:53:53.758950+00:00`
- torch_version: `2.7.1`
- minting record: `results/phase38_minting.json` sha256 `b17b8c010c725573ce75d68613acfc29f2e0e3ae77f8bf4a456e9eed859fb519`
- modules changed since launch: []
- head at write: `ccd5d7e01532f1c14eb20d1f2ad66c0a6d32ad13`; written 2026-10-04T19:01:56.380654+00:00
