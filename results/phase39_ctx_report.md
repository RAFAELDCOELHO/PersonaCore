# Phase 39 — E6 instrument × context 2×2

## Status

Status: **SCORED** — run `v6/39/E6/ctx`, front E6, device `mps`, launched at `852e6b4f648b5b7490d1ce205cc5c9c3992593c5`.

## Approval and cost (D-11, D-26, D-30)

D-11 ruling (verbatim): "Opção 1: aprovo (i) adaptador desligado como oitavo adaptador e (ii) os conjuntos cunhados da Fase 38 sob a pergunta inteira em |R| = 8 (D-09). approved"

D-26 ruling (verbatim): "Yes, add adapter-off" (39-CONTEXT D-11 (62af2fe); D-26 (3499c3b); D-30 (f681550)).

- approved_adapters: 8
- committed_adapter_cap: 7
- committed_anchor_adapter_cap: 7
- reference_reading: 'k0'
- cell_readings: ['k8', 'k16', 'k32', 'k64', 'k78', 'M2']
- descriptive_readings: ['adapter_off']
- minted_set_size: 8
- minted_extra_nlls: 12096
- gate_extra_nlls_priced: 512
- gate_extra_nlls_actual: 448
- projection step d11: 0.7030772649827931
- projection step d26: 0.7227090186770592
- projection step d30_actual_gate: 0.7285258345864714
- projection step d30_priced: 0.7293568082878159
- e6_projection_hours: 0.7293568082878159
- committed_front_hours_e6: 0.4949481154825642
- e6_stop_hours: 0.7424221732238463
- budget_record: 'results/phase36_budget.json'
- cost e6_projection_hours: 0.7293568082878159
- cost e6_stop_hours: 0.7424221732238463
- cost extra_setup_hours: 0.0014170362945232127
- cost note: 'run() loads each reading twice (gate pass, then work pass) where the formula prices one adapter setup each (I1), and re-scores one pinned NLL per work-pass load (39-REVIEW-3 IN-02)'
- cost projection_with_double_load_and_checks_hours: 0.7308777162950072
- cost projection_with_double_load_hours: 0.7307738445823391
- cost projection_within_stop: True
- cost run_hours: 0.2278947125
- cost run_within_stop: True
- cost setups_priced: 8
- cost setups_run: 16
- cost work_load_check_hours: 0.0001038717126680745
- cost work_load_check_nlls: 8

## Gate 1: committed anchor ranks and the copy's equality (D-18, D-30)

The rank on each committed reference set against the committed rank, before anything new was scored; every cell scored by the pinned value_span_nll and by the driver's copy.

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

Copy equality (D-30 condition 1, nll_sum and nll_mean bitwise): gate candidate cells compared 448, equal 448 (each candidate of each gate row; 39-REVIEW-3 IN-03).

Context (b) was scored with the copy: scored with the driver's copy of span_nll_from_ids (D-30); gate-1 equality: 448 of 448.


### Work-pass load check (39-REVIEW-3 IN-02)

Each reading's work-pass load re-scored, with the pinned value_span_nll, the gate's taught cell of the run's first slot before any work-pass score; nll_sum and nll_mean must equal the gate sidecar's bitwise (float.hex), else the run stops.

| reading | slot | candidate | gate nll_sum | work nll_sum | gate nll_mean | work nll_mean | equal |
|---|---|---|---|---|---|---|---|
| k0 | person_name | quillon | 0x1.05d4da0000000p+1 | 0x1.05d4da0000000p+1 | 0x1.a2ee2a0000000p-2 | 0x1.a2ee2a0000000p-2 | True |
| k8 | person_name | quillon | 0x1.f34c2e0000000p+1 | 0x1.f34c2e0000000p+1 | 0x1.8f70240000000p-1 | 0x1.8f70240000000p-1 | True |
| k16 | person_name | quillon | 0x1.63f76c0000000p+2 | 0x1.63f76c0000000p+2 | 0x1.1cc5f00000000p+0 | 0x1.1cc5f00000000p+0 | True |
| k32 | person_name | quillon | 0x1.1fccc40000000p+3 | 0x1.1fccc40000000p+3 | 0x1.cc7ad40000000p+0 | 0x1.cc7ad40000000p+0 | True |
| k64 | person_name | quillon | 0x1.cbc8700000000p+3 | 0x1.cbc8700000000p+3 | 0x1.6fd38c0000000p+1 | 0x1.6fd38c0000000p+1 | True |
| k78 | person_name | quillon | 0x1.115d560000000p+4 | 0x1.115d560000000p+4 | 0x1.b562240000000p+1 | 0x1.b562240000000p+1 | True |
| M2 | person_name | quillon | 0x1.579d800000000p+0 | 0x1.579d800000000p+0 | 0x1.12e4660000000p-2 | 0x1.12e4660000000p-2 | True |
| adapter_off | person_name | quillon | 0x1.9c596c0000000p+4 | 0x1.9c596c0000000p+4 | 0x1.49e1240000000p+2 | 0x1.49e1240000000p+2 | True |

## Gate 2: committed A2 counts re-derived (D-19)

Passed: True. Each committed A2 answered count re-derived from the SHA-verified draws; `independent` marks the erasure target's k0 row checked against a committed total (WR-01).

| reading | slot | count | committed | n questions | equal | independent |
|---|---|---|---|---|---|---|
| k0 | person_name | 26 | 26 | 27 | True | — |
| k0 | pet_name | 27 | 27 | 27 | True | True |
| k0 | cat_name | 27 | 27 | 27 | True | — |
| k0 | sibling_name | 27 | 27 | 27 | True | — |
| k0 | hometown | 21 | 21 | 27 | True | — |
| k0 | street | 27 | 27 | 27 | True | — |
| k0 | birth_year | 18 | 18 | 27 | True | — |
| k0 | house_number | 24 | 24 | 27 | True | — |
| k8 | person_name | 18 | 18 | 27 | True | — |
| k8 | pet_name | 24 | 24 | 27 | True | — |
| k8 | cat_name | 27 | 27 | 27 | True | — |
| k8 | sibling_name | 27 | 27 | 27 | True | — |
| k8 | hometown | 7 | 7 | 27 | True | — |
| k8 | street | 27 | 27 | 27 | True | — |
| k8 | birth_year | 14 | 14 | 27 | True | — |
| k8 | house_number | 24 | 24 | 27 | True | — |
| k16 | person_name | 10 | 10 | 27 | True | — |
| k16 | pet_name | 18 | 18 | 27 | True | — |
| k16 | cat_name | 27 | 27 | 27 | True | — |
| k16 | sibling_name | 22 | 22 | 27 | True | — |
| k16 | hometown | 3 | 3 | 27 | True | — |
| k16 | street | 24 | 24 | 27 | True | — |
| k16 | birth_year | 13 | 13 | 27 | True | — |
| k16 | house_number | 24 | 24 | 27 | True | — |
| k32 | person_name | 1 | 1 | 27 | True | — |
| k32 | pet_name | 2 | 2 | 27 | True | — |
| k32 | cat_name | 27 | 27 | 27 | True | — |
| k32 | sibling_name | 10 | 10 | 27 | True | — |
| k32 | hometown | 1 | 1 | 27 | True | — |
| k32 | street | 11 | 11 | 27 | True | — |
| k32 | birth_year | 14 | 14 | 27 | True | — |
| k32 | house_number | 10 | 10 | 27 | True | — |
| k64 | person_name | 0 | 0 | 27 | True | — |
| k64 | pet_name | 0 | 0 | 27 | True | — |
| k64 | cat_name | 6 | 6 | 27 | True | — |
| k64 | sibling_name | 0 | 0 | 27 | True | — |
| k64 | hometown | 0 | 0 | 27 | True | — |
| k64 | street | 0 | 0 | 27 | True | — |
| k64 | birth_year | 11 | 11 | 27 | True | — |
| k64 | house_number | 6 | 6 | 27 | True | — |
| k78 | person_name | 0 | 0 | 27 | True | — |
| k78 | pet_name | 0 | 0 | 27 | True | — |
| k78 | cat_name | 7 | 7 | 27 | True | — |
| k78 | sibling_name | 0 | 0 | 27 | True | — |
| k78 | hometown | 0 | 0 | 27 | True | — |
| k78 | street | 0 | 0 | 27 | True | — |
| k78 | birth_year | 8 | 8 | 27 | True | — |
| k78 | house_number | 5 | 5 | 27 | True | — |
| M2 | person_name | 26 | 26 | 27 | True | — |
| M2 | pet_name | 0 | 0 | 27 | True | — |
| M2 | cat_name | 27 | 27 | 27 | True | — |
| M2 | sibling_name | 27 | 27 | 27 | True | — |
| M2 | hometown | 18 | 18 | 27 | True | — |
| M2 | street | 27 | 27 | 27 | True | — |
| M2 | birth_year | 18 | 18 | 27 | True | — |
| M2 | house_number | 17 | 17 | 27 | True | — |
| adapter_off | person_name | 0 | 0 | 27 | True | — |
| adapter_off | pet_name | 0 | 0 | 27 | True | — |
| adapter_off | cat_name | 0 | 0 | 27 | True | — |
| adapter_off | sibling_name | 0 | 0 | 27 | True | — |
| adapter_off | hometown | 0 | 0 | 27 | True | — |
| adapter_off | street | 0 | 0 | 27 | True | — |
| adapter_off | birth_year | 0 | 0 | 27 | True | — |
| adapter_off | house_number | 0 | 0 | 27 | True | — |

- `k0` `pet_name` source: results/phase18_extraction_report.md sha256 f24795f3f94c6330699261d908552ccd0dd10a9da8734438efd90dd3667f0cc1: the A2 adapter-on rung-48 totals (core_taught 105/112, core_held_out 92/104) minus the seven non-target committed k0 counts

## The four readings per slot and adapter (D-13)

R_a: the taught value's rank in the anchor context (a). R_q: n1, the questions whose taught value ranks 1 in the question context (b), with the median rank and the rank of the mean NLL. G_a: the common unit (some hit in K anchor draws) and its hits. G_q: the committed A2 answered count and its hits. Adapter-off is descriptive (D-11 i).

| reading | slot | R_a rank | R_q n1 | R_q median | R_q rank of mean NLL | G_a unit | G_a hits/K | G_q answered | G_q hits/(n K) |
|---|---|---|---|---|---|---|---|---|---|
| k0 | person_name | 1 | 27/27 | 1 | 1 | 1 | 20/48 | 26/27 | 206/1296 |
| k0 | pet_name | 1 | 27/27 | 1 | 1 | 1 | 45/48 | 27/27 | 109/1296 |
| k0 | cat_name | 1 | 27/27 | 1 | 1 | 1 | 32/48 | 27/27 | 956/1296 |
| k0 | sibling_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 27/27 | 316/1296 |
| k0 | hometown | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 21/27 | 46/1296 |
| k0 | street | 1 | 27/27 | 1 | 1 | 1 | 18/48 | 27/27 | 995/1296 |
| k0 | birth_year | 1 | 27/27 | 1 | 1 | 1 | 1/48 | 18/27 | 31/1296 |
| k0 | house_number | 1 | 27/27 | 1 | 1 | 1 | 1/48 | 24/27 | 79/1296 |
| k8 | person_name | 1 | 27/27 | 1 | 1 | 1 | 2/48 | 18/27 | 125/1296 |
| k8 | pet_name | 1 | 26/27 | 1 | 1 | 1 | 22/48 | 24/27 | 68/1296 |
| k8 | cat_name | 1 | 27/27 | 1 | 1 | 1 | 33/48 | 27/27 | 781/1296 |
| k8 | sibling_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 27/27 | 144/1296 |
| k8 | hometown | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 7/27 | 12/1296 |
| k8 | street | 1 | 27/27 | 1 | 1 | 1 | 12/48 | 27/27 | 534/1296 |
| k8 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 14/27 | 24/1296 |
| k8 | house_number | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 24/27 | 64/1296 |
| k16 | person_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 10/27 | 42/1296 |
| k16 | pet_name | 1 | 24/27 | 1 | 1 | 1 | 3/48 | 18/27 | 23/1296 |
| k16 | cat_name | 1 | 27/27 | 1 | 1 | 1 | 16/48 | 27/27 | 489/1296 |
| k16 | sibling_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 22/27 | 59/1296 |
| k16 | hometown | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 3/27 | 4/1296 |
| k16 | street | 1 | 27/27 | 1 | 1 | 1 | 2/48 | 24/27 | 249/1296 |
| k16 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 13/27 | 23/1296 |
| k16 | house_number | 1 | 24/27 | 1 | 1 | 1 | 1/48 | 24/27 | 51/1296 |
| k32 | person_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 1/27 | 1/1296 |
| k32 | pet_name | 1 | 18/27 | 1 | 1 | 0 | 0/48 | 2/27 | 3/1296 |
| k32 | cat_name | 1 | 27/27 | 1 | 1 | 1 | 5/48 | 27/27 | 176/1296 |
| k32 | sibling_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 10/27 | 20/1296 |
| k32 | hometown | 1 | 26/27 | 1 | 1 | 0 | 0/48 | 1/27 | 1/1296 |
| k32 | street | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 11/27 | 22/1296 |
| k32 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 14/27 | 24/1296 |
| k32 | house_number | 1 | 24/27 | 1 | 1 | 0 | 0/48 | 10/27 | 14/1296 |
| k64 | person_name | 1 | 17/27 | 1 | 1 | 0 | 0/48 | 0/27 | 0/1296 |
| k64 | pet_name | 1 | 11/27 | 2 | 2 | 0 | 0/48 | 0/27 | 0/1296 |
| k64 | cat_name | 1 | 25/27 | 1 | 1 | 0 | 0/48 | 6/27 | 7/1296 |
| k64 | sibling_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 0/27 | 0/1296 |
| k64 | hometown | 1 | 18/27 | 1 | 1 | 0 | 0/48 | 0/27 | 0/1296 |
| k64 | street | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 0/27 | 0/1296 |
| k64 | birth_year | 1 | 27/27 | 1 | 1 | 1 | 1/48 | 11/27 | 16/1296 |
| k64 | house_number | 1 | 24/27 | 1 | 1 | 0 | 0/48 | 6/27 | 6/1296 |
| k78 | person_name | 1 | 14/27 | 1 | 2 | 0 | 0/48 | 0/27 | 0/1296 |
| k78 | pet_name | 2 | 5/27 | 2 | 2 | 0 | 0/48 | 0/27 | 0/1296 |
| k78 | cat_name | 1 | 25/27 | 1 | 1 | 0 | 0/48 | 7/27 | 8/1296 |
| k78 | sibling_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 0/27 | 0/1296 |
| k78 | hometown | 1 | 12/27 | 2 | 1 | 0 | 0/48 | 0/27 | 0/1296 |
| k78 | street | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 0/27 | 0/1296 |
| k78 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 8/27 | 10/1296 |
| k78 | house_number | 1 | 21/27 | 1 | 1 | 0 | 0/48 | 5/27 | 5/1296 |
| M2 | person_name | 1 | 27/27 | 1 | 1 | 1 | 31/48 | 26/27 | 458/1296 |
| M2 | pet_name | 2 | 0/27 | 5 | 5 | 0 | 0/48 | 0/27 | 0/1296 |
| M2 | cat_name | 1 | 27/27 | 1 | 1 | 1 | 40/48 | 27/27 | 874/1296 |
| M2 | sibling_name | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 27/27 | 318/1296 |
| M2 | hometown | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 18/27 | 46/1296 |
| M2 | street | 1 | 27/27 | 1 | 1 | 1 | 33/48 | 27/27 | 1209/1296 |
| M2 | birth_year | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 18/27 | 25/1296 |
| M2 | house_number | 1 | 27/27 | 1 | 1 | 0 | 0/48 | 17/27 | 29/1296 |
| adapter_off (descriptive) | person_name | 5 | 0/27 | 4 | 4 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off (descriptive) | pet_name | 4 | 0/27 | 5 | 5 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off (descriptive) | cat_name | 3 | 1/27 | 3 | 4 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off (descriptive) | sibling_name | 4 | 2/27 | 2 | 2 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off (descriptive) | hometown | 5 | 0/27 | 6 | 6 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off (descriptive) | street | 3 | 0/27 | 3 | 3 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off (descriptive) | birth_year | 3 | 2/27 | 3 | 3 | 0 | 0/48 | 0/27 | 0/1296 |
| adapter_off (descriptive) | house_number | 5 | 0/27 | 5 | 5 | 0 | 0/48 | 0/27 | 0/1296 |

## Baseline at k0 (ruling f)

k0 (k0) is the reference in both events and a cell in neither: each reading's k0 value with its status under each event against itself.

| slot | reading | k0 value | collapse | damage |
|---|---|---|---|---|
| person_name | R_a | 1 | INTACT | INTACT |
| person_name | R_q | 27 | INTACT | INTACT |
| person_name | G_a | 1 | INTACT | INTACT |
| person_name | G_q | 26 | INTACT | INTACT |
| pet_name | R_a | 1 | INTACT | INTACT |
| pet_name | R_q | 27 | INTACT | INTACT |
| pet_name | G_a | 1 | INTACT | INTACT |
| pet_name | G_q | 27 | INTACT | INTACT |
| cat_name | R_a | 1 | INTACT | INTACT |
| cat_name | R_q | 27 | INTACT | INTACT |
| cat_name | G_a | 1 | INTACT | INTACT |
| cat_name | G_q | 27 | INTACT | INTACT |
| sibling_name | R_a | 1 | INTACT | INTACT |
| sibling_name | R_q | 27 | INTACT | INTACT |
| sibling_name | G_a | 0 | ALREADY_AT_K0 | UNREACHABLE_AT_SIZE |
| sibling_name | G_q | 27 | INTACT | INTACT |
| hometown | R_a | 1 | INTACT | INTACT |
| hometown | R_q | 27 | INTACT | INTACT |
| hometown | G_a | 0 | ALREADY_AT_K0 | UNREACHABLE_AT_SIZE |
| hometown | G_q | 21 | INTACT | INTACT |
| street | R_a | 1 | INTACT | INTACT |
| street | R_q | 27 | INTACT | INTACT |
| street | G_a | 1 | INTACT | INTACT |
| street | G_q | 27 | INTACT | INTACT |
| birth_year | R_a | 1 | INTACT | INTACT |
| birth_year | R_q | 27 | INTACT | INTACT |
| birth_year | G_a | 1 | INTACT | INTACT |
| birth_year | G_q | 18 | INTACT | INTACT |
| house_number | R_a | 1 | INTACT | INTACT |
| house_number | R_q | 27 | INTACT | INTACT |
| house_number | G_a | 1 | INTACT | INTACT |
| house_number | G_q | 24 | INTACT | INTACT |

## Decomposition under collapse (D-15, D-16)

Each cell: the status of each reading (its value), the k0 values of the same slot (the reference, ruling f), the class of the four-step precedence and whether the published disagreement (R_a INTACT, G_q LOST) holds. k0 is never a cell; adapter-off is never classified (D-11 i).

| reading | slot | R_a | R_q | G_a | G_q | k0 R_a | k0 R_q | k0 G_a | k0 G_q | class | disagreement |
|---|---|---|---|---|---|---|---|---|---|---|---|
| k8 | person_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (18) | 1 | 27 | 1 | 26 | NO_DISAGREEMENT | False |
| k8 | pet_name | INTACT (1) | INTACT (26) | INTACT (1) | INTACT (24) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k8 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k8 | sibling_name | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | INTACT (27) | 1 | 27 | 0 | 27 | NO_DISAGREEMENT | False |
| k8 | hometown | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | INTACT (7) | 1 | 27 | 0 | 21 | NO_DISAGREEMENT | False |
| k8 | street | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k8 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (14) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k8 | house_number | INTACT (1) | INTACT (27) | LOST (0) | INTACT (24) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |
| k16 | person_name | INTACT (1) | INTACT (27) | LOST (0) | INTACT (10) | 1 | 27 | 1 | 26 | NO_DISAGREEMENT | False |
| k16 | pet_name | INTACT (1) | INTACT (24) | INTACT (1) | INTACT (18) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k16 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k16 | sibling_name | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | INTACT (22) | 1 | 27 | 0 | 27 | NO_DISAGREEMENT | False |
| k16 | hometown | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | INTACT (3) | 1 | 27 | 0 | 21 | NO_DISAGREEMENT | False |
| k16 | street | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (24) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k16 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (13) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k16 | house_number | INTACT (1) | INTACT (24) | INTACT (1) | INTACT (24) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |
| k32 | person_name | INTACT (1) | INTACT (27) | LOST (0) | INTACT (1) | 1 | 27 | 1 | 26 | NO_DISAGREEMENT | False |
| k32 | pet_name | INTACT (1) | INTACT (18) | LOST (0) | INTACT (2) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k32 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k32 | sibling_name | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | INTACT (10) | 1 | 27 | 0 | 27 | NO_DISAGREEMENT | False |
| k32 | hometown | INTACT (1) | INTACT (26) | ALREADY_AT_K0 (0) | INTACT (1) | 1 | 27 | 0 | 21 | NO_DISAGREEMENT | False |
| k32 | street | INTACT (1) | INTACT (27) | LOST (0) | INTACT (11) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k32 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (14) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k32 | house_number | INTACT (1) | INTACT (24) | LOST (0) | INTACT (10) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |
| k64 | person_name | INTACT (1) | INTACT (17) | LOST (0) | LOST (0) | 1 | 27 | 1 | 26 | INSTRUMENT_SUFFICIENT | True |
| k64 | pet_name | INTACT (1) | INTACT (11) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k64 | cat_name | INTACT (1) | INTACT (25) | LOST (0) | INTACT (6) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k64 | sibling_name | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | LOST (0) | 1 | 27 | 0 | 27 | ALREADY_AT_K0 | True |
| k64 | hometown | INTACT (1) | INTACT (18) | ALREADY_AT_K0 (0) | LOST (0) | 1 | 27 | 0 | 21 | ALREADY_AT_K0 | True |
| k64 | street | INTACT (1) | INTACT (27) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k64 | birth_year | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (11) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k64 | house_number | INTACT (1) | INTACT (24) | LOST (0) | INTACT (6) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |
| k78 | person_name | INTACT (1) | INTACT (14) | LOST (0) | LOST (0) | 1 | 27 | 1 | 26 | INSTRUMENT_SUFFICIENT | True |
| k78 | pet_name | LOST (2) | INTACT (5) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k78 | cat_name | INTACT (1) | INTACT (25) | LOST (0) | INTACT (7) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k78 | sibling_name | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | LOST (0) | 1 | 27 | 0 | 27 | ALREADY_AT_K0 | True |
| k78 | hometown | INTACT (1) | INTACT (12) | ALREADY_AT_K0 (0) | LOST (0) | 1 | 27 | 0 | 21 | ALREADY_AT_K0 | True |
| k78 | street | INTACT (1) | INTACT (27) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k78 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (8) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k78 | house_number | INTACT (1) | INTACT (21) | LOST (0) | INTACT (5) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |
| M2 | person_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (26) | 1 | 27 | 1 | 26 | NO_DISAGREEMENT | False |
| M2 | pet_name | LOST (2) | LOST (0) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| M2 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| M2 | sibling_name | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | INTACT (27) | 1 | 27 | 0 | 27 | NO_DISAGREEMENT | False |
| M2 | hometown | INTACT (1) | INTACT (27) | ALREADY_AT_K0 (0) | INTACT (18) | 1 | 27 | 0 | 21 | NO_DISAGREEMENT | False |
| M2 | street | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| M2 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (18) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| M2 | house_number | INTACT (1) | INTACT (27) | LOST (0) | INTACT (17) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |

## Decomposition under damage (D-15, D-16)

Each cell: the status of each reading (its value), the k0 values of the same slot (the reference, ruling f), the class of the four-step precedence and whether the published disagreement (R_a INTACT, G_q LOST) holds. k0 is never a cell; adapter-off is never classified (D-11 i).

| reading | slot | R_a | R_q | G_a | G_q | k0 R_a | k0 R_q | k0 G_a | k0 G_q | class | disagreement |
|---|---|---|---|---|---|---|---|---|---|---|---|
| k8 | person_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (18) | 1 | 27 | 1 | 26 | NO_DISAGREEMENT | False |
| k8 | pet_name | INTACT (1) | INTACT (26) | INTACT (1) | INTACT (24) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k8 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k8 | sibling_name | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | INTACT (27) | 1 | 27 | 0 | 27 | NO_DISAGREEMENT | False |
| k8 | hometown | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | LOST (7) | 1 | 27 | 0 | 21 | UNREACHABLE_AT_SIZE | True |
| k8 | street | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k8 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (14) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k8 | house_number | INTACT (1) | INTACT (27) | LOST (0) | INTACT (24) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |
| k16 | person_name | INTACT (1) | INTACT (27) | LOST (0) | LOST (10) | 1 | 27 | 1 | 26 | INSTRUMENT_SUFFICIENT | True |
| k16 | pet_name | INTACT (1) | INTACT (24) | INTACT (1) | LOST (18) | 1 | 27 | 1 | 27 | INTERACTION_ONLY | True |
| k16 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k16 | sibling_name | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | INTACT (22) | 1 | 27 | 0 | 27 | NO_DISAGREEMENT | False |
| k16 | hometown | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | LOST (3) | 1 | 27 | 0 | 21 | UNREACHABLE_AT_SIZE | True |
| k16 | street | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (24) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k16 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (13) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k16 | house_number | INTACT (1) | INTACT (24) | INTACT (1) | INTACT (24) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |
| k32 | person_name | INTACT (1) | INTACT (27) | LOST (0) | LOST (1) | 1 | 27 | 1 | 26 | INSTRUMENT_SUFFICIENT | True |
| k32 | pet_name | INTACT (1) | LOST (18) | LOST (0) | LOST (2) | 1 | 27 | 1 | 27 | EITHER | True |
| k32 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k32 | sibling_name | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | LOST (10) | 1 | 27 | 0 | 27 | UNREACHABLE_AT_SIZE | True |
| k32 | hometown | INTACT (1) | INTACT (26) | UNREACHABLE_AT_SIZE (0) | LOST (1) | 1 | 27 | 0 | 21 | UNREACHABLE_AT_SIZE | True |
| k32 | street | INTACT (1) | INTACT (27) | LOST (0) | LOST (11) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k32 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (14) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k32 | house_number | INTACT (1) | INTACT (24) | LOST (0) | LOST (10) | 1 | 27 | 1 | 24 | INSTRUMENT_SUFFICIENT | True |
| k64 | person_name | INTACT (1) | LOST (17) | LOST (0) | LOST (0) | 1 | 27 | 1 | 26 | EITHER | True |
| k64 | pet_name | INTACT (1) | LOST (11) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | EITHER | True |
| k64 | cat_name | INTACT (1) | INTACT (25) | LOST (0) | LOST (6) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k64 | sibling_name | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | LOST (0) | 1 | 27 | 0 | 27 | UNREACHABLE_AT_SIZE | True |
| k64 | hometown | INTACT (1) | LOST (18) | UNREACHABLE_AT_SIZE (0) | LOST (0) | 1 | 27 | 0 | 21 | UNREACHABLE_AT_SIZE | True |
| k64 | street | INTACT (1) | INTACT (27) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k64 | birth_year | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (11) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| k64 | house_number | INTACT (1) | INTACT (24) | LOST (0) | LOST (6) | 1 | 27 | 1 | 24 | INSTRUMENT_SUFFICIENT | True |
| k78 | person_name | INTACT (1) | LOST (14) | LOST (0) | LOST (0) | 1 | 27 | 1 | 26 | EITHER | True |
| k78 | pet_name | LOST (2) | LOST (5) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| k78 | cat_name | INTACT (1) | INTACT (25) | LOST (0) | LOST (7) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k78 | sibling_name | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | LOST (0) | 1 | 27 | 0 | 27 | UNREACHABLE_AT_SIZE | True |
| k78 | hometown | INTACT (1) | LOST (12) | UNREACHABLE_AT_SIZE (0) | LOST (0) | 1 | 27 | 0 | 21 | UNREACHABLE_AT_SIZE | True |
| k78 | street | INTACT (1) | INTACT (27) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | INSTRUMENT_SUFFICIENT | True |
| k78 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | LOST (8) | 1 | 27 | 1 | 18 | INSTRUMENT_SUFFICIENT | True |
| k78 | house_number | INTACT (1) | INTACT (21) | LOST (0) | LOST (5) | 1 | 27 | 1 | 24 | INSTRUMENT_SUFFICIENT | True |
| M2 | person_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (26) | 1 | 27 | 1 | 26 | NO_DISAGREEMENT | False |
| M2 | pet_name | LOST (2) | LOST (0) | LOST (0) | LOST (0) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| M2 | cat_name | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| M2 | sibling_name | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | INTACT (27) | 1 | 27 | 0 | 27 | NO_DISAGREEMENT | False |
| M2 | hometown | INTACT (1) | INTACT (27) | UNREACHABLE_AT_SIZE (0) | INTACT (18) | 1 | 27 | 0 | 21 | NO_DISAGREEMENT | False |
| M2 | street | INTACT (1) | INTACT (27) | INTACT (1) | INTACT (27) | 1 | 27 | 1 | 27 | NO_DISAGREEMENT | False |
| M2 | birth_year | INTACT (1) | INTACT (27) | LOST (0) | INTACT (18) | 1 | 27 | 1 | 18 | NO_DISAGREEMENT | False |
| M2 | house_number | INTACT (1) | INTACT (27) | LOST (0) | INTACT (17) | 1 | 27 | 1 | 24 | NO_DISAGREEMENT | False |

## Instrument share and context share (CTX-03)

Per event, the prefix readings (k8, k16, k32, k64, k78) apart from M2, then combined. M2 is another training (the retrain without the target), whose damage reference is the taught adapter's k0 (ruling g). Each outcome is counted of the cells and, for the outcomes reached through a published disagreement, of the disagreement cells with its share; a share is never given without its denominator.

- collapse, prefixes: instrument share (INSTRUMENT_SUFFICIENT) 5 of 9 disagreement cells (share 0.5555555555555556); context share (CONTEXT_SUFFICIENT) 0 of 9 disagreement cells (share 0.0); 40 cells.
- collapse, M2: instrument share (INSTRUMENT_SUFFICIENT) 0 of 0 disagreement cells (share —); context share (CONTEXT_SUFFICIENT) 0 of 0 disagreement cells (share —); 8 cells.
- collapse, combined: instrument share (INSTRUMENT_SUFFICIENT) 5 of 9 disagreement cells (share 0.5555555555555556); context share (CONTEXT_SUFFICIENT) 0 of 9 disagreement cells (share 0.0); 48 cells.
- damage, prefixes: instrument share (INSTRUMENT_SUFFICIENT) 11 of 24 disagreement cells (share 0.4583333333333333); context share (CONTEXT_SUFFICIENT) 0 of 24 disagreement cells (share 0.0); 40 cells.
- damage, M2: instrument share (INSTRUMENT_SUFFICIENT) 0 of 0 disagreement cells (share —); context share (CONTEXT_SUFFICIENT) 0 of 0 disagreement cells (share —); 8 cells.
- damage, combined: instrument share (INSTRUMENT_SUFFICIENT) 11 of 24 disagreement cells (share 0.4583333333333333); context share (CONTEXT_SUFFICIENT) 0 of 24 disagreement cells (share 0.0); 48 cells.

| event | group | outcome | of cells | of disagreement cells | share of disagreement cells |
|---|---|---|---|---|---|
| collapse | prefixes | CONTEXT_SUFFICIENT | 0 of 40 | 0 of 9 | 0.0 |
| collapse | prefixes | INSTRUMENT_SUFFICIENT | 5 of 40 | 5 of 9 | 0.5555555555555556 |
| collapse | prefixes | EITHER | 0 of 40 | 0 of 9 | 0.0 |
| collapse | prefixes | INTERACTION_ONLY | 0 of 40 | 0 of 9 | 0.0 |
| collapse | prefixes | NO_DISAGREEMENT | 31 of 40 | — | — |
| collapse | prefixes | REVERSE_DISAGREEMENT | 0 of 40 | — | — |
| collapse | prefixes | UNREACHABLE_AT_SIZE | 0 of 40 | 0 of 9 | 0.0 |
| collapse | prefixes | ALREADY_AT_K0 | 4 of 40 | 4 of 9 | 0.4444444444444444 |
| collapse | M2 | CONTEXT_SUFFICIENT | 0 of 8 | 0 of 0 | — |
| collapse | M2 | INSTRUMENT_SUFFICIENT | 0 of 8 | 0 of 0 | — |
| collapse | M2 | EITHER | 0 of 8 | 0 of 0 | — |
| collapse | M2 | INTERACTION_ONLY | 0 of 8 | 0 of 0 | — |
| collapse | M2 | NO_DISAGREEMENT | 8 of 8 | — | — |
| collapse | M2 | REVERSE_DISAGREEMENT | 0 of 8 | — | — |
| collapse | M2 | UNREACHABLE_AT_SIZE | 0 of 8 | 0 of 0 | — |
| collapse | M2 | ALREADY_AT_K0 | 0 of 8 | 0 of 0 | — |
| collapse | combined | CONTEXT_SUFFICIENT | 0 of 48 | 0 of 9 | 0.0 |
| collapse | combined | INSTRUMENT_SUFFICIENT | 5 of 48 | 5 of 9 | 0.5555555555555556 |
| collapse | combined | EITHER | 0 of 48 | 0 of 9 | 0.0 |
| collapse | combined | INTERACTION_ONLY | 0 of 48 | 0 of 9 | 0.0 |
| collapse | combined | NO_DISAGREEMENT | 39 of 48 | — | — |
| collapse | combined | REVERSE_DISAGREEMENT | 0 of 48 | — | — |
| collapse | combined | UNREACHABLE_AT_SIZE | 0 of 48 | 0 of 9 | 0.0 |
| collapse | combined | ALREADY_AT_K0 | 4 of 48 | 4 of 9 | 0.4444444444444444 |
| damage | prefixes | CONTEXT_SUFFICIENT | 0 of 40 | 0 of 24 | 0.0 |
| damage | prefixes | INSTRUMENT_SUFFICIENT | 11 of 40 | 11 of 24 | 0.4583333333333333 |
| damage | prefixes | EITHER | 4 of 40 | 4 of 24 | 0.16666666666666666 |
| damage | prefixes | INTERACTION_ONLY | 1 of 40 | 1 of 24 | 0.041666666666666664 |
| damage | prefixes | NO_DISAGREEMENT | 16 of 40 | — | — |
| damage | prefixes | REVERSE_DISAGREEMENT | 0 of 40 | — | — |
| damage | prefixes | UNREACHABLE_AT_SIZE | 8 of 40 | 8 of 24 | 0.3333333333333333 |
| damage | prefixes | ALREADY_AT_K0 | 0 of 40 | 0 of 24 | 0.0 |
| damage | M2 | CONTEXT_SUFFICIENT | 0 of 8 | 0 of 0 | — |
| damage | M2 | INSTRUMENT_SUFFICIENT | 0 of 8 | 0 of 0 | — |
| damage | M2 | EITHER | 0 of 8 | 0 of 0 | — |
| damage | M2 | INTERACTION_ONLY | 0 of 8 | 0 of 0 | — |
| damage | M2 | NO_DISAGREEMENT | 8 of 8 | — | — |
| damage | M2 | REVERSE_DISAGREEMENT | 0 of 8 | — | — |
| damage | M2 | UNREACHABLE_AT_SIZE | 0 of 8 | 0 of 0 | — |
| damage | M2 | ALREADY_AT_K0 | 0 of 8 | 0 of 0 | — |
| damage | combined | CONTEXT_SUFFICIENT | 0 of 48 | 0 of 24 | 0.0 |
| damage | combined | INSTRUMENT_SUFFICIENT | 11 of 48 | 11 of 24 | 0.4583333333333333 |
| damage | combined | EITHER | 4 of 48 | 4 of 24 | 0.16666666666666666 |
| damage | combined | INTERACTION_ONLY | 1 of 48 | 1 of 24 | 0.041666666666666664 |
| damage | combined | NO_DISAGREEMENT | 24 of 48 | — | — |
| damage | combined | REVERSE_DISAGREEMENT | 0 of 48 | — | — |
| damage | combined | UNREACHABLE_AT_SIZE | 8 of 48 | 8 of 24 | 0.3333333333333333 |
| damage | combined | ALREADY_AT_K0 | 0 of 48 | 0 of 24 | 0.0 |

## Reverse disagreement and undecided cells (ruling e, IN-01)

REVERSE_DISAGREEMENT (R_a LOST with G_q INTACT) is counted apart, with no sufficiency class (ruling e); an undecided cell (a WR-01 outcome at step 1, disagreement None) is published apart (IN-01).

| event | group | reverse disagreement | undecided | undecided by outcome |
|---|---|---|---|---|
| collapse | prefixes | 0 of 40 | 0 of 40 | ALREADY_AT_K0 0, UNREACHABLE_AT_SIZE 0 |
| collapse | M2 | 0 of 8 | 0 of 8 | ALREADY_AT_K0 0, UNREACHABLE_AT_SIZE 0 |
| collapse | combined | 0 of 48 | 0 of 48 | ALREADY_AT_K0 0, UNREACHABLE_AT_SIZE 0 |
| damage | prefixes | 0 of 40 | 0 of 40 | ALREADY_AT_K0 0, UNREACHABLE_AT_SIZE 0 |
| damage | M2 | 0 of 8 | 0 of 8 | ALREADY_AT_K0 0, UNREACHABLE_AT_SIZE 0 |
| damage | combined | 0 of 48 | 0 of 48 | ALREADY_AT_K0 0, UNREACHABLE_AT_SIZE 0 |

No reverse disagreement and no undecided cell under collapse.
No reverse disagreement and no undecided cell under damage.

## Drop-formula audit (D-33, descriptive)

Criterion: False (descriptive only). Damage only: under collapse there is no margin. The committed drop is count_k0 / n - count_k / n; each count where (count_k0 - count_k) / n differs from it, with its status under each against the margin 0.2962962962962963 and the cell's class by both formulas. The main numbers use the committed formula (ruling j).

| reading | slot | count | k0 -> k of n | rate_drop | count_drop | status (committed) | status (exact) | class (committed) | class (exact) |
|---|---|---|---|---|---|---|---|---|---|
| k8 | pet_name | R_q | 27 -> 26 of 27 | 0.03703703703703709 | 0.037037037037037035 | INTACT | INTACT | NO_DISAGREEMENT | NO_DISAGREEMENT |
| k8 | pet_name | G_q | 27 -> 24 of 27 | 0.11111111111111116 | 0.1111111111111111 | INTACT | INTACT | NO_DISAGREEMENT | NO_DISAGREEMENT |
| k8 | hometown | G_q | 21 -> 7 of 27 | 0.5185185185185186 | 0.5185185185185185 | LOST | LOST | UNREACHABLE_AT_SIZE | UNREACHABLE_AT_SIZE |
| k16 | pet_name | R_q | 27 -> 24 of 27 | 0.11111111111111116 | 0.1111111111111111 | INTACT | INTACT | INTERACTION_ONLY | INTERACTION_ONLY |
| k16 | pet_name | G_q | 27 -> 18 of 27 | 0.33333333333333337 | 0.3333333333333333 | LOST | LOST | INTERACTION_ONLY | INTERACTION_ONLY |
| k16 | sibling_name | G_q | 27 -> 22 of 27 | 0.18518518518518523 | 0.18518518518518517 | INTACT | INTACT | NO_DISAGREEMENT | NO_DISAGREEMENT |
| k16 | hometown | G_q | 21 -> 3 of 27 | 0.6666666666666667 | 0.6666666666666666 | LOST | LOST | UNREACHABLE_AT_SIZE | UNREACHABLE_AT_SIZE |
| k16 | street | G_q | 27 -> 24 of 27 | 0.11111111111111116 | 0.1111111111111111 | INTACT | INTACT | NO_DISAGREEMENT | NO_DISAGREEMENT |
| k16 | house_number | R_q | 27 -> 24 of 27 | 0.11111111111111116 | 0.1111111111111111 | INTACT | INTACT | NO_DISAGREEMENT | NO_DISAGREEMENT |
| k32 | person_name | G_q | 26 -> 1 of 27 | 0.9259259259259258 | 0.9259259259259259 | LOST | LOST | INSTRUMENT_SUFFICIENT | INSTRUMENT_SUFFICIENT |
| k32 | pet_name | R_q | 27 -> 18 of 27 | 0.33333333333333337 | 0.3333333333333333 | LOST | LOST | EITHER | EITHER |
| k32 | hometown | R_q | 27 -> 26 of 27 | 0.03703703703703709 | 0.037037037037037035 | INTACT | INTACT | UNREACHABLE_AT_SIZE | UNREACHABLE_AT_SIZE |
| k32 | house_number | R_q | 27 -> 24 of 27 | 0.11111111111111116 | 0.1111111111111111 | INTACT | INTACT | INSTRUMENT_SUFFICIENT | INSTRUMENT_SUFFICIENT |
| k64 | hometown | R_q | 27 -> 18 of 27 | 0.33333333333333337 | 0.3333333333333333 | LOST | LOST | UNREACHABLE_AT_SIZE | UNREACHABLE_AT_SIZE |
| k64 | house_number | R_q | 27 -> 24 of 27 | 0.11111111111111116 | 0.1111111111111111 | INTACT | INTACT | INSTRUMENT_SUFFICIENT | INSTRUMENT_SUFFICIENT |
| k78 | person_name | R_q | 27 -> 14 of 27 | 0.4814814814814815 | 0.48148148148148145 | LOST | LOST | EITHER | EITHER |
| k78 | pet_name | R_q | 27 -> 5 of 27 | 0.8148148148148149 | 0.8148148148148148 | LOST | LOST | NO_DISAGREEMENT | NO_DISAGREEMENT |
| M2 | hometown | G_q | 21 -> 18 of 27 | 0.11111111111111116 | 0.1111111111111111 | INTACT | INTACT | NO_DISAGREEMENT | NO_DISAGREEMENT |
| M2 | house_number | G_q | 24 -> 17 of 27 | 0.2592592592592592 | 0.25925925925925924 | INTACT | INTACT | NO_DISAGREEMENT | NO_DISAGREEMENT |

No count status changes between the two formulas.
- `k8` `person_name` G_q: exact margin tie decided by strict >; class NO_DISAGREEMENT by the committed formula, NO_DISAGREEMENT by the exact formula
No cell's class changes between the two formulas.

## Common unit and per-draw rates (D-07, descriptive)

The common unit (some hit in K draws) beside the draw-unit rates. The anchor gives one unit per slot and A2 one per question (27 per slot): the 1-vs-27 unit asymmetry (D-07). Per-draw rate unit: draw; one-sided 95% bounds, together a 90% two-sided interval; within-question clustering ignored (D-07).

| reading | slot | G_a unit | G_a hits/n | G_a rate | G_a wilson_lower_95 | G_a wilson_upper_95 | G_q answered | G_q hits/n | G_q rate | G_q wilson_lower_95 | G_q wilson_upper_95 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| k0 | person_name | 1 | 20/48 | 0.4166666666666667 | 0.3071451154863139 | 0.5350812082046543 | 26/27 | 206/1296 | 0.15895061728395063 | 0.1429576306909331 | 0.1763645940769123 |
| k0 | pet_name | 1 | 45/48 | 0.9375 | 0.8535639131108683 | 0.9747478875115491 | 27/27 | 109/1296 | 0.08410493827160494 | 0.07227383592741993 | 0.09766887708133268 |
| k0 | cat_name | 1 | 32/48 | 0.6666666666666666 | 0.5485198170895637 | 0.7670275355285 | 27/27 | 956/1296 | 0.7376543209876543 | 0.7170744346512195 | 0.7572440150580646 |
| k0 | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 27/27 | 316/1296 | 0.24382716049382716 | 0.22475504129697732 | 0.2639666297956124 |
| k0 | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 21/27 | 46/1296 | 0.035493827160493825 | 0.02796123086858797 | 0.04496179924508377 |
| k0 | street | 1 | 18/48 | 0.375 | 0.26964183035788875 | 0.49369765517856345 | 27/27 | 995/1296 | 0.7677469135802469 | 0.7479075078897762 | 0.7864707455164629 |
| k0 | birth_year | 1 | 1/48 | 0.020833333333333332 | 0.004661559723664985 | 0.08813980149940169 | 18/27 | 31/1296 | 0.023919753086419752 | 0.017867205905652522 | 0.03195589970919044 |
| k0 | house_number | 1 | 1/48 | 0.020833333333333332 | 0.004661559723664985 | 0.08813980149940169 | 24/27 | 79/1296 | 0.06095679012345679 | 0.050913116686985053 | 0.07282974732411 |
| k8 | person_name | 1 | 2/48 | 0.041666666666666664 | 0.0138854809356564 | 0.11835929936466827 | 18/27 | 125/1296 | 0.09645061728395062 | 0.08379099610045104 | 0.11079163637371893 |
| k8 | pet_name | 1 | 22/48 | 0.4583333333333333 | 0.3454401483421993 | 0.5756730135032847 | 24/27 | 68/1296 | 0.05246913580246913 | 0.04318182536663761 | 0.063621094011983 |
| k8 | cat_name | 1 | 33/48 | 0.6875 | 0.5699606812764121 | 0.7850300904189097 | 27/27 | 781/1296 | 0.6026234567901234 | 0.5800731235702631 | 0.6247462069860186 |
| k8 | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 27/27 | 144/1296 | 0.1111111111111111 | 0.09755427179683976 | 0.12628826504251334 |
| k8 | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 7/27 | 12/1296 | 0.009259259259259259 | 0.0057920532660291554 | 0.014771147983630682 |
| k8 | street | 1 | 12/48 | 0.25 | 0.1624308336441771 | 0.36424813742872725 | 27/27 | 534/1296 | 0.41203703703703703 | 0.38975409470677636 | 0.4346864791021249 |
| k8 | birth_year | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 14/27 | 24/1296 | 0.018518518518518517 | 0.013286940672166786 | 0.025756200176556072 |
| k8 | house_number | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 24/27 | 64/1296 | 0.04938271604938271 | 0.04038778838734068 | 0.06025515112492559 |
| k16 | person_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 10/27 | 42/1296 | 0.032407407407407406 | 0.025240635151302915 | 0.04152241509601448 |
| k16 | pet_name | 1 | 3/48 | 0.0625 | 0.02525211248845099 | 0.14643608688913162 | 18/27 | 23/1296 | 0.017746913580246913 | 0.012642180538836091 | 0.02486096534329818 |
| k16 | cat_name | 1 | 16/48 | 0.3333333333333333 | 0.23297246447149994 | 0.4514801829104363 | 27/27 | 489/1296 | 0.3773148148148148 | 0.35544520633611726 | 0.3996955939762977 |
| k16 | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 22/27 | 59/1296 | 0.04552469135802469 | 0.036910169552538334 | 0.05603279512678502 |
| k16 | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 3/27 | 4/1296 | 0.0030864197530864196 | 0.001386366491020456 | 0.0068568750259307 |
| k16 | street | 1 | 2/48 | 0.041666666666666664 | 0.0138854809356564 | 0.11835929936466827 | 24/27 | 249/1296 | 0.19212962962962962 | 0.1747774898335674 | 0.21076451849758712 |
| k16 | birth_year | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 13/27 | 23/1296 | 0.017746913580246913 | 0.012642180538836091 | 0.02486096534329818 |
| k16 | house_number | 1 | 1/48 | 0.020833333333333332 | 0.004661559723664985 | 0.08813980149940169 | 24/27 | 51/1296 | 0.03935185185185185 | 0.031385413726169625 | 0.04923759122044505 |
| k32 | person_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 1/27 | 1/1296 | 0.0007716049382716049 | 0.00017215788558170116 | 0.0034510987316036996 |
| k32 | pet_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 2/27 | 3/1296 | 0.0023148148148148147 | 0.0009254794555288579 | 0.005777767094833713 |
| k32 | cat_name | 1 | 5/48 | 0.10416666666666667 | 0.05163129947319379 | 0.1989437380589048 | 27/27 | 176/1296 | 0.13580246913580246 | 0.12090655369334677 | 0.15221582207684103 |
| k32 | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 10/27 | 20/1296 | 0.015432098765432098 | 0.010725635703009925 | 0.02215752527935859 |
| k32 | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 1/27 | 1/1296 | 0.0007716049382716049 | 0.00017215788558170116 | 0.0034510987316036996 |
| k32 | street | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 11/27 | 22/1296 | 0.016975308641975308 | 0.012000248896770501 | 0.023962902018775187 |
| k32 | birth_year | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 14/27 | 24/1296 | 0.018518518518518517 | 0.013286940672166786 | 0.025756200176556072 |
| k32 | house_number | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 10/27 | 14/1296 | 0.010802469135802469 | 0.006994600081166294 | 0.01664859110167071 |
| k64 | person_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k64 | pet_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k64 | cat_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 6/27 | 7/1296 | 0.005401234567901234 | 0.0029311719084409234 | 0.009932054508275988 |
| k64 | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k64 | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k64 | street | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k64 | birth_year | 1 | 1/48 | 0.020833333333333332 | 0.004661559723664985 | 0.08813980149940169 | 11/27 | 16/1296 | 0.012345679012345678 | 0.008220206120447616 | 0.01850297499556656 |
| k64 | house_number | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 6/27 | 6/1296 | 0.004629629629629629 | 0.002395873292186642 | 0.008927358157941684 |
| k78 | person_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k78 | pet_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k78 | cat_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 7/27 | 8/1296 | 0.006172839506172839 | 0.0034815798479814475 | 0.01092164153532405 |
| k78 | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k78 | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k78 | street | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| k78 | birth_year | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 8/27 | 10/1296 | 0.007716049382716049 | 0.004618223135658869 | 0.012864988180823796 |
| k78 | house_number | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 5/27 | 5/1296 | 0.0038580246913580245 | 0.0018792134699885013 | 0.007904023013551241 |
| M2 | person_name | 1 | 31/48 | 0.6458333333333334 | 0.527303365974374 | 0.7488005675664319 | 26/27 | 458/1296 | 0.3533950617283951 | 0.33188000309476773 | 0.3755209532534011 |
| M2 | pet_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| M2 | cat_name | 1 | 40/48 | 0.8333333333333334 | 0.7276430500610619 | 0.9034516551750656 | 27/27 | 874/1296 | 0.6743827160493827 | 0.6526279190280249 | 0.6954109434209954 |
| M2 | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 27/27 | 318/1296 | 0.24537037037037038 | 0.22625328789324237 | 0.26554837313252455 |
| M2 | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 18/27 | 46/1296 | 0.035493827160493825 | 0.02796123086858797 | 0.04496179924508377 |
| M2 | street | 1 | 33/48 | 0.6875 | 0.5699606812764121 | 0.7850300904189097 | 27/27 | 1209/1296 | 0.9328703703703703 | 0.9205111097556169 | 0.9434260665005795 |
| M2 | birth_year | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 18/27 | 25/1296 | 0.019290123456790122 | 0.013934362130202176 | 0.02664877368510927 |
| M2 | house_number | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 17/27 | 29/1296 | 0.022376543209876542 | 0.01654783897419569 | 0.030195276707470093 |
| adapter_off | person_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| adapter_off | pet_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| adapter_off | cat_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| adapter_off | sibling_name | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| adapter_off | hometown | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| adapter_off | street | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| adapter_off | birth_year | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |
| adapter_off | house_number | 0 | 0/48 | 0.0 | 0.0 | 0.05335794214580871 | 0/27 | 0/1296 | 0.0 | 0.0 | 0.002083261650596815 |

## Predicted vs observed hit rate (D-17, D-23c, D-29, descriptive)

D-17: descriptive, never a criterion; temperature, top-p and the hit rule separate the predicted hit rate from the observed one.

D-29 / D-23c: the (b) prediction uses the taught suffix sum after the injected prefix, so it is conditioned on that prefix exactly as G_q's hit is scored on prefix_text + completion.

| reading | slot | predicted (a) | observed (a) | mean predicted (b) | observed (b) |
|---|---|---|---|---|---|
| k0 | person_name | 0.12930798827361104 | 0.4166666666666667 | 0.06669982892633673 | 0.15895061728395063 |
| k0 | pet_name | 0.5858948627430738 | 0.9375 | 0.006249683789142718 | 0.08410493827160494 |
| k0 | cat_name | 0.3521845037249658 | 0.6666666666666666 | 0.3549520928573274 | 0.7376543209876543 |
| k0 | sibling_name | 5.903207115850765e-07 | 0.0 | 0.012285120306041827 | 0.24382716049382716 |
| k0 | hometown | 1.3829024883143481e-11 | 0.0 | 0.0006589907435916191 | 0.035493827160493825 |
| k0 | street | 0.1401108781273736 | 0.375 | 0.409112196878148 | 0.7677469135802469 |
| k0 | birth_year | 0.006318931385593706 | 0.020833333333333332 | 0.006179202558868551 | 0.023919753086419752 |
| k0 | house_number | 0.010521919922538286 | 0.020833333333333332 | 0.019562676766260535 | 0.06095679012345679 |
| k8 | person_name | 0.020226486520787967 | 0.041666666666666664 | 0.03902416459059025 | 0.09645061728395062 |
| k8 | pet_name | 0.1396511622395419 | 0.4583333333333333 | 0.0016806466203585122 | 0.05246913580246913 |
| k8 | cat_name | 0.24162716698994155 | 0.6875 | 0.2706063020971147 | 0.6026234567901234 |
| k8 | sibling_name | 1.8813833732343553e-08 | 0.0 | 0.002275337325870652 | 0.1111111111111111 |
| k8 | hometown | 1.3151787296110186e-13 | 0.0 | 2.716947773039864e-05 | 0.009259259259259259 |
| k8 | street | 0.05714372368088107 | 0.25 | 0.20897316838139282 | 0.41203703703703703 |
| k8 | birth_year | 0.003301107826436565 | 0.0 | 0.005196436665864912 | 0.018518518518518517 |
| k8 | house_number | 0.006539666690351451 | 0.0 | 0.0168799893342502 | 0.04938271604938271 |
| k16 | person_name | 0.0038411770619591963 | 0.0 | 0.014095025071013803 | 0.032407407407407406 |
| k16 | pet_name | 0.010637971899416244 | 0.0625 | 0.0007791475456354782 | 0.017746913580246913 |
| k16 | cat_name | 0.09735265046905685 | 0.3333333333333333 | 0.1707728691815767 | 0.3773148148148148 |
| k16 | sibling_name | 2.245124176335879e-09 | 0.0 | 0.0011349775065048074 | 0.04552469135802469 |
| k16 | hometown | 5.891788297866592e-15 | 0.0 | 2.3330584636106713e-06 | 0.0030864197530864196 |
| k16 | street | 0.007607866783182736 | 0.041666666666666664 | 0.07828960951057667 | 0.19212962962962962 |
| k16 | birth_year | 0.0019391679822271881 | 0.0 | 0.005171823642165017 | 0.017746913580246913 |
| k16 | house_number | 0.003577636736830794 | 0.020833333333333332 | 0.01200728830635635 | 0.03935185185185185 |
| k32 | person_name | 0.00012418405183529712 | 0.0 | 0.0009102026223709524 | 0.0007716049382716049 |
| k32 | pet_name | 0.00013524372906296823 | 0.0 | 0.0002462226200430846 | 0.0023148148148148147 |
| k32 | cat_name | 0.024814752160655342 | 0.10416666666666667 | 0.035865023539992505 | 0.13580246913580246 |
| k32 | sibling_name | 1.2472703409787894e-10 | 0.0 | 0.0005002373978471705 | 0.015432098765432098 |
| k32 | hometown | 2.5231641010685336e-16 | 0.0 | 7.079692297638133e-08 | 0.0007716049382716049 |
| k32 | street | 8.655804573415054e-05 | 0.0 | 0.008563005723497165 | 0.016975308641975308 |
| k32 | birth_year | 0.0010913199672317288 | 0.0 | 0.004377775783769997 | 0.018518518518518517 |
| k32 | house_number | 0.0011967667050759375 | 0.0 | 0.005058488579507449 | 0.010802469135802469 |
| k64 | person_name | 5.753901708521458e-07 | 0.0 | 3.0427293698641577e-05 | 0.0 |
| k64 | pet_name | 4.520339657809916e-07 | 0.0 | 4.481779062914175e-05 | 0.0 |
| k64 | cat_name | 0.00026050470560825287 | 0.0 | 0.0018954181747387533 | 0.005401234567901234 |
| k64 | sibling_name | 2.4522281692228156e-12 | 0.0 | 2.8581125061045388e-05 | 0.0 |
| k64 | hometown | 4.978685297432423e-18 | 0.0 | 2.5099811880851896e-09 | 0.0 |
| k64 | street | 4.196408960283007e-07 | 0.0 | 0.0002558314775071607 | 0.0 |
| k64 | birth_year | 0.00047218634827102734 | 0.020833333333333332 | 0.0030756956697174124 | 0.012345679012345678 |
| k64 | house_number | 0.0004946722277088439 | 0.0 | 0.002450419016036387 | 0.004629629629629629 |
| k78 | person_name | 3.8014921086636566e-08 | 0.0 | 5.868512209115182e-06 | 0.0 |
| k78 | pet_name | 7.260746551628154e-08 | 0.0 | 1.9330189854411224e-05 | 0.0 |
| k78 | cat_name | 5.036848546050548e-05 | 0.0 | 0.0008092377095904916 | 0.006172839506172839 |
| k78 | sibling_name | 4.827692151375791e-13 | 0.0 | 1.2953731618445532e-05 | 0.0 |
| k78 | hometown | 1.5706099976839813e-18 | 0.0 | 4.413229107426954e-10 | 0.0 |
| k78 | street | 1.883770371159701e-07 | 0.0 | 0.0001229937902379982 | 0.0 |
| k78 | birth_year | 0.0002364496393060466 | 0.0 | 0.002210462641585663 | 0.007716049382716049 |
| k78 | house_number | 0.00031924370590406093 | 0.0 | 0.0017872503340430471 | 0.0038580246913580245 |
| M2 | person_name | 0.2612579594749808 | 0.6458333333333334 | 0.1621183265989174 | 0.3533950617283951 |
| M2 | pet_name | 2.0168442058063554e-08 | 0.0 | 7.813815962012689e-07 | 0.0 |
| M2 | cat_name | 0.3822846869960015 | 0.8333333333333334 | 0.3000616798713777 | 0.6743827160493827 |
| M2 | sibling_name | 9.919054702466565e-09 | 0.0 | 0.003044387680855824 | 0.24537037037037038 |
| M2 | hometown | 1.8361656146222595e-11 | 0.0 | 0.00013946256774456913 | 0.035493827160493825 |
| M2 | street | 0.2866088831021295 | 0.6875 | 0.5932184601021896 | 0.9328703703703703 |
| M2 | birth_year | 0.0067832592519868565 | 0.0 | 0.0050519444718174975 | 0.019290123456790122 |
| M2 | house_number | 0.0034894856004758683 | 0.0 | 0.00905535204202689 | 0.022376543209876542 |
| adapter_off | person_name | 6.418533106288175e-12 | 0.0 | 1.5425062001353444e-08 | 0.0 |
| adapter_off | pet_name | 4.801655833499006e-10 | 0.0 | 1.2195350866009004e-05 | 0.0 |
| adapter_off | cat_name | 6.79180545393063e-10 | 0.0 | 1.1373940627302734e-05 | 0.0 |
| adapter_off | sibling_name | 3.47487424909915e-14 | 0.0 | 1.1706648441466093e-09 | 0.0 |
| adapter_off | hometown | 6.76664645725998e-24 | 0.0 | 1.6403753443191834e-15 | 0.0 |
| adapter_off | street | 3.3081580287795325e-16 | 0.0 | 2.2845324981108541e-10 | 0.0 |
| adapter_off | birth_year | 1.8954423352666088e-07 | 0.0 | 1.3624668423514376e-05 | 0.0 |
| adapter_off | house_number | 1.520438017051431e-08 | 0.0 | 2.106069396240457e-06 | 0.0 |

## Adapter-off (D-11 i, descriptive)

descriptive (D-11 i): never classified.

| slot | reading | R_a rank | R_q n1 | G_a unit | G_q answered |
|---|---|---|---|---|---|
| person_name | adapter_off | 5 | 0/27 | 0 | 0/27 |
| pet_name | adapter_off | 4 | 0/27 | 0 | 0/27 |
| cat_name | adapter_off | 3 | 1/27 | 0 | 0/27 |
| sibling_name | adapter_off | 4 | 2/27 | 0 | 0/27 |
| hometown | adapter_off | 5 | 0/27 | 0 | 0/27 |
| street | adapter_off | 3 | 0/27 | 0 | 0/27 |
| birth_year | adapter_off | 3 | 2/27 | 0 | 0/27 |
| house_number | adapter_off | 5 | 0/27 | 0 | 0/27 |

## Minted sets under the full question at |R| = 8 (D-11 ii, D-26, descriptive)

The taught value's rank among itself and the Phase 38 minted values under the full question (context b), beside the committed anchor-side rank at the same size (results/phase38_rank.json).

| reading | slot | \|R\| | n1 | median | committed anchor-side rank |
|---|---|---|---|---|---|
| k0 | person_name | 8 | 27/27 | 1 | 1 |
| k0 | pet_name | 8 | 27/27 | 1 | 1 |
| k0 | cat_name | 8 | 27/27 | 1 | 1 |
| k0 | sibling_name | 8 | 27/27 | 1 | 1 |
| k0 | hometown | 8 | 27/27 | 1 | 1 |
| k0 | street | 8 | 27/27 | 1 | 1 |
| k0 | birth_year | 8 | 27/27 | 1 | 1 |
| k0 | house_number | 8 | 27/27 | 1 | 1 |
| k8 | person_name | 8 | 27/27 | 1 | 1 |
| k8 | pet_name | 8 | 27/27 | 1 | 1 |
| k8 | cat_name | 8 | 27/27 | 1 | 1 |
| k8 | sibling_name | 8 | 27/27 | 1 | 1 |
| k8 | hometown | 8 | 27/27 | 1 | 1 |
| k8 | street | 8 | 27/27 | 1 | 1 |
| k8 | birth_year | 8 | 27/27 | 1 | 1 |
| k8 | house_number | 8 | 27/27 | 1 | 1 |
| k16 | person_name | 8 | 27/27 | 1 | 1 |
| k16 | pet_name | 8 | 27/27 | 1 | 1 |
| k16 | cat_name | 8 | 27/27 | 1 | 1 |
| k16 | sibling_name | 8 | 27/27 | 1 | 1 |
| k16 | hometown | 8 | 27/27 | 1 | 1 |
| k16 | street | 8 | 27/27 | 1 | 1 |
| k16 | birth_year | 8 | 27/27 | 1 | 1 |
| k16 | house_number | 8 | 27/27 | 1 | 1 |
| k32 | person_name | 8 | 22/27 | 1 | 1 |
| k32 | pet_name | 8 | 27/27 | 1 | 1 |
| k32 | cat_name | 8 | 27/27 | 1 | 1 |
| k32 | sibling_name | 8 | 27/27 | 1 | 1 |
| k32 | hometown | 8 | 27/27 | 1 | 1 |
| k32 | street | 8 | 27/27 | 1 | 1 |
| k32 | birth_year | 8 | 27/27 | 1 | 1 |
| k32 | house_number | 8 | 25/27 | 1 | 1 |
| k64 | person_name | 8 | 8/27 | 2 | 1 |
| k64 | pet_name | 8 | 27/27 | 1 | 1 |
| k64 | cat_name | 8 | 27/27 | 1 | 1 |
| k64 | sibling_name | 8 | 27/27 | 1 | 1 |
| k64 | hometown | 8 | 27/27 | 1 | 1 |
| k64 | street | 8 | 27/27 | 1 | 1 |
| k64 | birth_year | 8 | 27/27 | 1 | 1 |
| k64 | house_number | 8 | 19/27 | 1 | 1 |
| k78 | person_name | 8 | 3/27 | 2 | 1 |
| k78 | pet_name | 8 | 25/27 | 1 | 1 |
| k78 | cat_name | 8 | 27/27 | 1 | 1 |
| k78 | sibling_name | 8 | 27/27 | 1 | 1 |
| k78 | hometown | 8 | 27/27 | 1 | 1 |
| k78 | street | 8 | 27/27 | 1 | 1 |
| k78 | birth_year | 8 | 27/27 | 1 | 1 |
| k78 | house_number | 8 | 18/27 | 1 | 1 |
| M2 | person_name | 8 | 27/27 | 1 | 1 |
| M2 | pet_name | 8 | 11/27 | 2 | 1 |
| M2 | cat_name | 8 | 27/27 | 1 | 1 |
| M2 | sibling_name | 8 | 27/27 | 1 | 1 |
| M2 | hometown | 8 | 27/27 | 1 | 1 |
| M2 | street | 8 | 27/27 | 1 | 1 |
| M2 | birth_year | 8 | 27/27 | 1 | 1 |
| M2 | house_number | 8 | 27/27 | 1 | 1 |
| adapter_off | person_name | 8 | 0/27 | 6 | 2 |
| adapter_off | pet_name | 8 | 0/27 | 3 | 1 |
| adapter_off | cat_name | 8 | 25/27 | 1 | 2 |
| adapter_off | sibling_name | 8 | 10/27 | 2 | 5 |
| adapter_off | hometown | 8 | 0/27 | 4 | 6 |
| adapter_off | street | 8 | 27/27 | 1 | 1 |
| adapter_off | birth_year | 8 | 0/27 | 5 | 5 |
| adapter_off | house_number | 8 | 0/27 | 8 | 6 |

## CPU cross-check (D-20, descriptive)

Criterion: False (descriptive only). On cpu (torch 2.7.1) the rank differs from the run's in 0 of 64 gate rows (reading x slot), in 0 of 1728 R_q questions and in 0 of 1728 (ii) questions; the taught suffix sum is bitwise the pinned call's in 1728 of 1728 (D-30a). no generation cross-check: generation is seeded per device (D-20).

- crosscheck git sha: `852e6b4f648b5b7490d1ce205cc5c9c3992593c5`
- crosscheck sha256 scripts/phase39_ctx.py: `4eb5a94535250b8079f5eee0f9e1401934aea1abd8a4deb4b9bfc7fa3b23213e`
- crosscheck sha256 scripts/phase39_prereg.py: `4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297`

## Rehearsal disclosure (D-21, D-27)

The CPU rehearsal (39-07) read pet_name, birth_year under 8 readings, all their A2 entries, before the driver review and the MPS run (D-21, D-27).

- slice read: slots pet_name, birth_year, readings k0, k8, k16, k32, k64, k78, M2, adapter_off
- rehearsal git sha: `7b32c416a2ceaa105616c801575e9a2c630814e3`
- launch git sha: `852e6b4f648b5b7490d1ce205cc5c9c3992593c5`
- driver changed: True; prereg changed: False

| module | rehearsal sha256 | launch sha256 | changed |
|---|---|---|---|
| scripts/phase39_ctx.py | `0a9dbf81d4719a8ca0e41d18246e759e699aa6523c7293017a17d9e6bb36c73b` | `4eb5a94535250b8079f5eee0f9e1401934aea1abd8a4deb4b9bfc7fa3b23213e` | True |
| scripts/phase39_prereg.py | `4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297` | `4355b88024b41463daef9b17285246e74b7577988cd95c01e33d293594858297` | False |

- `3590057d222e2c7192d4481fe4df0b1cab15ee8b` fix(39-08): IN-02 the work pass re-scores the gate's taught cell on its own load with the pinned function and STOPs unless bitwise equal (touched: scripts/phase39_ctx.py)
- `6313ed94cc27cf8c0aebc047dd1075023eac56a8` fix(39-08): IN-01 IN-03 the heartbeat names the slot or question being scored; the report names gate rows apart from gate candidate cells (touched: scripts/phase39_ctx.py)
- `62c2653f753dbe030ce11bdac14e0e10e3e12ab3` fix(39-08): IN-05 the CPU sidecar records the git sha and disclosed-module digests at crosscheck time (touched: scripts/phase39_ctx.py)
- `98cd98dcd1994a735f4e23d281316c073d3684f7` fix(39-08): IN-06 the real-root record proves every event carries all of the door's cells, else refuses (touched: scripts/phase39_ctx.py)
- `e706f951c8dc048afee7502f2f663b4171ffd7d6` fix(39-08): WR-03 the cost block judges the projection and the run apart (projection_within_stop, run_within_stop) (touched: scripts/phase39_ctx.py)
- `0cb1e047ffbe3df3fc2b2d94ac7f08b24c23b561` fix(39-08): WR-02 emit refuses while the ledger attempt for the run is still open (crash rule i first) (touched: scripts/phase39_ctx.py)
- `4f859b37d7f83a274154b48a52746b43473891b7` fix(39-08): WR-01 a re-run after a crash names the partial sidecars as kept evidence (crash rule ii), not as a finished run (touched: scripts/phase39_ctx.py)

## Not measured (D-12, D-23d)

- minted sets under the full question at |R| > 8 (Phase 38's nested sizes above |R| = 8; birth_year capped at its own maximum) — D-12: not part of E6; if run later, a dated continuation after E1-E4, labelled as after E6
- B1' context (b): the question, the ans1 preamble, then the value — D-23d

## Limitations (D-22)

- one seed, one target, |R| 6-8 in the main reading (D-22)
- the 1-vs-27 unit asymmetry between the anchor and A2 (D-07)
- no generation cross-check: generation is seeded per device (D-20)
- context (b) differs from (a) in two ways, the question added and the ans1 preamble dropped (D-23)
- G_a (no injected prefix) and G_q (injected prefix, scored on prefix_text + completion) differ beyond context
- the anchor and A2 seed windows coincide (D-28)
- the D-28 seed window is proved from the seed formula, not at phase18_extraction's draw_all call site (39-REVIEW IN-03, a known limitation)
- the draw-unit Wilson bounds ignore within-question clustering (D-07)

## Provenance

- device: `mps`
- finished_utc: `2026-10-05T16:29:18.734818+00:00`
- git_sha_at_end: `852e6b4f648b5b7490d1ce205cc5c9c3992593c5`
- git_sha_at_launch: `852e6b4f648b5b7490d1ce205cc5c9c3992593c5`
- head_moved_during_run: `False`
- started_utc: `2026-10-05T16:15:38.313853+00:00`
- torch_version: `2.7.1`
- modules changed since launch: []
- sidecar cpu: `695af920c15a187404c150d30c7e0254090b988af5ba480a6dca81d68a5ae182`
- sidecar gate: `27d59bf9d9236c89898de516067396ce0bc38e7dac5970309c4cd98c455aa9f1`
- sidecar readings: `{'M2': 'b99ce1deab112b8fc6c67b5580ccff33acc24fa11cccd81ef912c94f5309f75c', 'adapter_off': 'dca399c4fd02b2f280a793ea866af05bb83bceb425cf3ba01a4cc8708b3a93b4', 'k0': '5fc0d8c2dd39b11f29b8dd0e6079ea47bbab90a5004af12365a9c02991b8ccbe', 'k16': '962e3af34e338be81e624c1bf454c1570d107ae219611e058f2c0a616a248c39', 'k32': '672a4950073640f752eb9c1aaf1f364541b1b69409caf0716adaa5ad5b2953a7', 'k64': 'e58bb3cd88f6277d792a870ad40b5fbd65d0478da464d2ff17b0d34446ff48d7', 'k78': '182d23df42a91332d16165f0f95b4b9f88f205eb838df4233aa1ca60b68e582a', 'k8': '3052d30061c635c5b9a5d054541c31746ba2d416aaf447efe49f058a23fe9ab7'}`
- sidecar run: `b6fc7a5418e4e8068982c43e4d88fa7b2ac0794570269cb1bb333b61ed9fc733`
- head at write: `852e6b4f648b5b7490d1ce205cc5c9c3992593c5`; written 2026-10-05T16:33:15.783400+00:00
