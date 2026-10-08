# Phase 41: Erasure Across Facts, Orderings and Seeds - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-07
**Phase:** 41-erasure-across-facts-orderings-and-seeds
**Areas discussed:** Ordenação alternativa, Grade de checkpoints, Calibração por seed, Banda (c) e
leitura de PASS, Leitura do M1 × M2 contra o piso de sementes (added by Rafael), Ordem de execução
(added at the close)

Rafael's answers were given as AskUserQuestion free text and are quoted verbatim below. Every
factual premise in them was measured before it entered CONTEXT.md, and the evidence is noted under
each answer.

---

## Area selection

Presented: Ordenação alternativa, Grade de checkpoints, Calibração por seed, Banda (c) e leitura de
PASS. Rafael selected all four and added a fifth:

> "Leitura do M1 × M2 contra o piso de sementes. O D-16 da Fase 35 diz que o piso da Fase 40 entra só nessa comparação, nunca no portão (b). Falta decidir: (i) onde essa comparação é feita no E1, já que só o pet_name tem M2 e, na semente 2024, o próprio retreino difere do completo em 14/27 (7/27 na 1337); (ii) como o dano por fato não-alvo é publicado nos slots instáveis entre sementes (hometown, birth_year, house_number); (iii) se o rank com a pergunta como contexto (R_q) entra como leitura descritiva declarada de antemão no ponto de parada das células do pet_name, comparada à faixa do D-13, e quanto isso custa."

Premises checked:
- At 2024, `hometown` reads full 22/27 and M2 8/27 (14/27). At 1337, `house_number` reads 24 and 17
  (7/27). Both match `results/phase40_noise_floor_report.md:153-183`.
- D-13 R_q n1 across the five M2: 0–1/27 committed and 9–12/27 minted (`d13.blocks`).

---

## Ordenação alternativa

| Option | Description | Selected |
|--------|-------------|----------|
| Gradiente (Taylor) | ∂NLL/∂s_j, one forward+backward, fact-specific, fits the budget | ✓ (modified) |
| Magnitude ‖B_j‖·‖A_j‖ | Blind to the target, zero cost, a control | |
| Aleatória com semente | Blind, zero cost, weakest control | |

**Rafael's choice:**
> "Gradiente (Taylor) reordenado a cada checkpoint. Em cada checkpoint da grade, calcular ∂NLL/∂s_j no adaptador já ablacionado até ali, ordenar os componentes restantes e ablacionar os primeiros até o próximo checkpoint. Continua sendo uma regra sobre o fato apagado, então a calibração por (ordenação, semente) vale igual.Junto, como leitura descritiva declarada de antemão: a correlação de postos entre a ordem do gradiente no adaptador intacto e a ordem atual, medida no fato de calibração.Antes de travar, quero o preço: quanto custa por célula e se cabe no orçamento da Fase 36. Se não couber ou se a calibração não aceitar uma ordenação que depende da grade, eu fico com a opção 1 estática mais a mesma correlação declarada."

Price given:
- 417.56 s per cell is the whole Phase 19 collateral-curve run, so one value NLL costs at most
  ~1.44 s.
- At most 5 gradients per cell, about 30 s at backward ≈ 2–3× forward.
- Break-even is backward ≈ 57× forward; the MPS ratio is unmeasured.

Calibration correction given: training is priced inside `e1_calibration_seconds`.

Second question: "Travar assim?" Options: Travar assim / Estática + correlação.

**Rafael's choice:**
> "Travar assim, com três precisões:1. Direção da ordem: ordenar pela subida prevista da NLL ao remover o componente, isto é, por −∂NLL/∂s_j em s_j = 1, do maior para o menor. Nunca pelo valor absoluto do gradiente: um componente cuja remoção baixa a NLL do alvo vai para o fim da fila, como na ordenação atual.2. Mesma NLL da ordenação atual: mesmo valor, mesmo contexto e mesma função de pontuação. A única diferença entre as duas ordenações é o estimador e a reordenação por checkpoint.3. Regra de recuo escrita agora: se no ensaio CPU a asserção dos 417 s falhar, a ordenação alternativa passa a ser a estática (gradiente uma vez no adaptador intacto), com a mesma correlação declarada. Essa troca não depende de nenhum resultado e não precisa de nova decisão minha.Confirme também que a calibração por (ordenação, semente) aceita uma ordem que depende da grade; se não aceitar, vale o recuo do item 3."

Confirmed in code:
- `_rule_e1_condition_a_floors` puts no constraint on the ordering.
- The grid fill precedes every phase41 record (fill-order leg (a), `tests/test_phase35_prereg.py:2434`).

---

## Grade de checkpoints

| Option | Description | Selected |
|--------|-------------|----------|
| 16, 32, 64, 128, 288 | Powers of 2, last = adapter removed, no NOT_REACHED | |
| 16, 32, 64, 128, 256 | Pure powers of 2, NOT_REACHED above 256 | |
| 32, 48, 64, 96, 128 | Dense where pet_name zeroed (post-hoc for pet_name) | |
| Other | | ✓ |

**Rafael's choice:**
> "Grade: 16, 32, 48, 64, 128. A mesma para as 16 células.Justificativa a gravar: potências de 2 de 16 a 128, mais um ponto (48) que divide a faixa (32, 64] onde o zero do pet_name já está commitado (extensão k*, semente 1337, ordenação atual). O uso dessa leitura anterior para posicionar o 48 fica declarado como insumo de desenho; nenhum limiar depende dele.Sem checkpoint em 288: o adaptador todo removido é o modelo base, igual nas 16 células e já medido no registro adapter_off, que o relatório cita como ponto final sem nova medição.Uma célula sem zero confirmado até 128 fica NOT_REACHED, como o pré-registro da Fase 35 já define, e é publicada com a contagem A2 e o rank de cada checkpoint e a frase "não apagado com 128 de 288 componentes removidos". Nunca conta como PASS nem como FAIL."

Premise checked: k* = 64 in `results/erasure_kstar_summary.json` (A2, budget_k 48).

---

## Calibração por seed

| Option | Description | Selected |
|--------|-------------|----------|
| (ordenação, seed), retreinar as duas | Fresh calibration adapter at 1337 and 2024, same driver | ✓ |
| (ordenação, seed), 1337 reusa a Fase 19 | Reuse phase19_erase_calibration_adapter.pt at 1337 | |
| Só por ordenação | One calibration adapter serves both seeds | |

**Rafael's choice:**
> "Opção 1: pisos por (ordenação, seed), treinando o adaptador de calibração em 1337 e em 2024 com o mesmo driver.Acréscimo, como previsão descritiva gravada antes da rodada (o padrão do D-07 da Fase 40): o adaptador de calibração novo da 1337 é idêntico, tensor a tensor, a checkpoints/phase19_erase_calibration_adapter.pt. O adaptador da Fase 19 entra só como alvo dessa comparação, nunca como insumo dos pisos. Se não for idêntico, isso é um achado relatado, não uma falha, e os pisos continuam vindo dos adaptadores novos.Publicar também, como leitura descritiva, a taxa de calibração e o piso de cada (ordenação, seed) lado a lado, para mostrar quanto o piso se move entre as duas sementes."

---

## Banda (c) e leitura de PASS

**control_gap**

| Option | Description | Selected |
|--------|-------------|----------|
| Re-medir e checar | Re-measure per (seed, ordering), exact equality with Phase 40 | ✓ |
| Ler da Fase 40 | Copy from the Phase 40 record | |

**Replicação**

| Option | Description | Selected |
|--------|-------------|----------|
| PASS só com as duas | PASS iff SUCCESS at both seeds | |
| Também uma leitura de cabeçalho | The same, plus a summary line with no threshold | ✓ (modified) |

**Rafael's choice:**
> "Opção 2, com simetria entre sucesso e falha. Para cada par (alvo, ordenação), três rótulos:- PASS: SUCCESS nas duas seeds.- FAILURE replicada: FAILURE nas duas seeds.- Não replicado: qualquer outra combinação, publicada com o veredito de cada seed por extenso (por exemplo "SUCCESS na 1337, NOT_REACHED na 2024"). Nunca lido como PASS nem como FAILURE do par.Cada célula traz qual condição decidiu o veredito, (a), (b) ou (c), e, quando for a (b), qual fato não-alvo passou da margem.Linha-resumo pré-registrada, sem nenhum limiar: dos 8 pares, quantos em cada um dos três rótulos, com INCONCLUSIVE e NOT_REACHED contados à parte dentro de "não replicado". Nenhuma agregação entre alvos ou ordenações além dessa contagem; a tabela 4 × 2 × 2 é publicada inteira."

Note: `erasure_gate` evaluates all three conditions, so CONTEXT records "every condition that
failed" (D-15).

**Retenção em (c)**

| Option | Description | Selected |
|--------|-------------|----------|
| Banda + teto de retenção v4.0 | The v4.0 (c) | |
| Só a banda (letra do ERASE-09) | Retention descriptive | ✓ |

**Rafael's choice:**
> "Opção 2: (c) = só a banda de diálogo, como está escrito no ERASE-09. A retenção não porta veredito.Razões a gravar no contexto:1. O teto de retenção do v4.0 (3,9085) é ancorado no adapter-off. Os adaptadores completos intactos da Fase 40 (4,16 a 4,33) e os cinco M2 (4,21 a 4,43) ficam acima dele; o braço ablacionado do v3.0 (3,67) fica abaixo. A perna reprovaria um apagamento que preserva o adaptador e aprovaria um que o destrói.2. É o mesmo defeito que o relatório da Fase 19 publicou para a perna de diálogo e que o ERASE-09 corrige com a banda ancorada no modelo adaptado.3. Isto é uma mudança em relação ao (c) do v3.0 e do v4.0, declarada como tal, não uma omissão.Leituras descritivas declaradas de antemão, sem veredito:- retention_ppl de cada célula no ponto de parada, ao lado do valor do adaptador intacto da mesma seed e, no pet_name, do M2 da mesma seed;- uma coluna "passaria no teto do v4.0: sim/não", para o leitor ver as duas leituras lado a lado;- a dispersão de retenção entre as cinco sementes da Fase 40 ao lado do piso de duas sementes (0,00868) de phase20_retention_floor.json."

Premises checked:
- cap 3.9085032379884783; full 4.156–4.332; M2 4.207–4.433; v3.0 erased 3.6709; floor
  0.008681618994239138.

---

## Leitura do M1 × M2 contra o piso de sementes

**(i) Onde**

| Option | Description | Selected |
|--------|-------------|----------|
| Só pet_name, descritiva | 4 cells, M2 of the same seed, beside 0.3481 | ✓ (modified) |
| Também M2 dos outros 3 alvos | ~4.7 h MPS, outside ERASE-05 | deferred |

> "Opção 1: comparação M1 × M2 só nas 4 células do pet_name, descritiva, sem veredito. Os outros 3 alvos: "sem M2, comparação não feita", declarado.Acréscimo: para cada fato não-alvo, além do M2 da mesma seed, publicar a faixa (mínimo e máximo, em /27) das cinco seeds do M2 da Fase 40, lida de recall_floor.m2.per_slot do registro do piso, e dizer se a taxa do M1 no ponto de parada cai dentro ou fora dessa faixa. Rótulo descritivo declarado de antemão; custo zero, só leitura de registro commitado.Declarar o limite: o M1 existe em duas seeds (1337, 2024) e a faixa vem de cinco retreinos; "fora da faixa" não é teste estatístico.Opção 2 (M2 dos outros 3 alvos, ~4,7 h) fica registrada como ideia adiada, com o preço, para depois do E1, E3 e E4, se sobrar orçamento."

**(ii) Instáveis**

Measured and presented: across the five full seeds the amplitude is `hometown` 14/27,
`birth_year` 8/27 (a tie with the margin), `house_number` 4/27.

| Option | Description | Selected |
|--------|-------------|----------|
| Faixa ao lado, rótulo por regra | Label when amplitude ≥ margin (b) | ✓ (modified) |
| Faixa ao lado, sem rótulo | No slot named | |

> "Opção 1, com dois ajustes:1. Regra do rótulo: "varia entre seeds" quando a maior amplitude do slot entre os dois grupos da Fase 40 (full e M2, cinco seeds cada) é ≥ a margem (b) de 8/27. Mesma convenção do piso publicado (o maior dos dois grupos). Publicar a faixa min–max dos dois grupos ao lado de cada Δ. Pelos registros commitados isso marca hometown (17/27) e birth_year (13/27), não house_number (7/27), sem depender de empate.2. Leitura descritiva adicional por célula, declarada de antemão: quantos não-alvos passaram da margem entre os slots com rótulo e entre os sem rótulo, e se a (b) falharia só com os slots sem rótulo (sim/não).O rótulo nunca desconta um Δ e não entra em nenhum veredito: o portão (b) continua lendo os sete não-alvos contra 8/27."

Premise checked: `recall_floor.m2.per_slot[*].range` gives hometown 0.6296 (17/27), birth_year
0.4815 (13/27), house_number 0.2593 (7/27).

**(iii) R_q**

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, descritiva declarada | D-13 scoring, ~9 s per cell | ✓ (modified) |
| Não entra | | |

> "Opção 1, com dois acréscimos:1. Publicar o bloco D-13 inteiro no ponto de parada das 4 células do pet_name: rank na âncora em 8/32/128/512 e n1 do R_q nas listas commitada e mintada. Cada leitura ao lado da faixa dos 5 M2 da Fase 40 (âncora em 512: 15–41; R_q: 0–1/27 commitada, 9–12/27 mintada), com o rótulo "dentro" ou "fora" da faixa. Descritivo, sem veredito.2. Previsão gravada antes da rodada, no padrão das previsões da Fase 40 (descritiva; um desacordo é um achado, não uma falha): no ponto de parada, o R_q fica fora da faixa dos M2 nas duas listas e a âncora em 512 fica dentro, nas 4 células. A célula (1337, ordenação atual) repete uma leitura já conhecida; as outras três são o teste.Limites a declarar: |R| = 8, quatro células, duas seeds, e a faixa de comparação vem de cinco retreinos; "fora da faixa" não é teste estatístico."

Premises checked:
- Anchor at 512 across the five M2: 15, 23, 32, 41, 41.
- Phase 40 full 1337 is `torch.equal` to `persona_adapter.pt` (72/72 tensors).

Caveat recorded in D-21: the "known reading" holds only if the stop is 64. Phase 39 R_q n1 at k64
is 11/27; a stop at 48 is a new prefix.

---

## Ordem de execução

| Option | Description | Selected |
|--------|-------------|----------|
| Par a par, seeds em sequência | Pairs in TARGET_RANKING order, current then alternative per target | |
| Ordenação atual inteira primeiro | 8 current-ordering cells (pair by pair), then 8 alternative | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Pausa na fatia, decisão sua | Pause at front_hours.E1 52.78 h | ✓ (modified) |
| Só o stop global | 90 h only | |

> "Opção 1: pausa na fatia do E1 (52,78 h), com decisão minha. O stop global de 90 h continua acima.Três acréscimos:1. A pausa é checada antes de cada célula. O aviso de pausa traz: as horas gastas no E1 (com as perdidas em quedas, como no E2), quais pares estão completos, se há um par pela metade, e quanto sobra para E3, E4 e para o stop de 90 h. Completar ou não um par pela metade é decisão minha nesse momento.2. Regra de queda igual à R-3 b da Fase 40, valendo por célula: nova tentativa só com meu approved e nota de causa, mesma seed e mesmo HEAD, saídas parciais guardadas e listadas, adaptadores e ordenações comparados entre as tentativas. Vale só para queda (sem linha de fim), nunca para refazer uma célula inteira.3. Operação: a espera acompanha o PID do driver, nunca o log; o bootout só depois de duas checagens de que o processo saiu. O plano prevê relançamento por bloco sem mudar o HEAD (como as seeds pendentes da Fase 40), com o estado de memória gravado em cada portão de lançamento e o coletor do outro projeto parado."

## Plan-phase rulings (2026-10-08, research open questions)

| Question | Selected |
|----------|----------|
| Second K = 48 confirmation vs Phase 36 cap of 1 | Option 2 (allow, count in E1 hours), with two constraints → D-26 |
| K = 16 read scope | All 216 (Recommended) → D-27 |
| D-19 label for pet_name as a non-target | Full group only (Recommended) → D-28 |

> "Opção 2, com duas amarras:1. Confirmações adicionais em K = 48 são permitidas, como manda o ERASE-07 (uma confirmação não zero continua para o próximo checkpoint). O teto natural é a grade: no máximo 4 confirmações por célula, uma por checkpoint depois do primeiro zero em K = 16. Cada confirmação é gravada no registro da célula com suas horas, lançadas na fatia do E1.2. O custo fica sob a pausa da fatia já decidida (52,78 h, decisão minha ao passar dela). Não há pausa por confirmação.Desvio declarado em relação ao limite de 1 por célula da Fase 36 (unit_caps.E1.k48_confirms_per_cell), com o motivo: o limite foi uma suposição de preço e a regra de parada do ERASE-07 é a medição. Nenhuma célula vira NOT_REACHED por falta de confirmação; NOT_REACHED só quando não há zero confirmado até o checkpoint 128."

Reading recorded in D-26: the "4" is read as 4 additional confirmations beyond the first, one per later grid checkpoint, which gives at most 5 per cell. That is the most `phase35_prereg.e1_stop` admits on the 5-point grid.

---

## Claude's Discretion

- File split of the Phase 41 fill files and the driver; field names of the descriptive blocks.

## Deferred Ideas

- M2 for cat_name, street and sibling_name × 2 seeds: ~4.7 h MPS. Consider it after E1/E3/E4 if
  budget remains.
