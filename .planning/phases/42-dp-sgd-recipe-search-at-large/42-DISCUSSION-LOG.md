# Phase 42: DP-SGD Recipe Search at Large ε - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-13
**Phase:** 42-dp-sgd-recipe-search-at-large
**Areas discussed:** As 4 receitas da grade, Quinta receita, 'Garantia vazia' e a resposta, Ordem e aprovações

Recon before the questions (sonnet-lead scout, then re-measured by the orchestrator):
- Phase 35 already wrote the E3 rules (`e3_grid_subset`, `e3_recall_threshold`, `p22_onset_sigma`, `_v4_control`).
- unit_caps.E3 = {4, 3, 800, 8}; E3 line 6.6225 h; P22 onset 0.0789 (T 200) / 0.1578 (T 800).
- The v4.0 control's sha256 0c23f6c1… equals tag v5.0.

---

## As 4 receitas da grade

| Option | Description | Selected |
|--------|-------------|----------|
| Fixo em 8 (q = 1) | Only lr × T vary; ε stays exact under the frozen accountant | ✓ |
| Lote < 8 com ε em q = 1 | Loose upper bound; contradicts accountant.py:850 | |
| Lote < 8 com accountant subamostrado | New capability, outside the phase | |

**User's choice:** "Opção 1: lote fixo em 8 (q = 1), as 4 receitas variam só lr × T. Registrar o lote < 8 com accountant subamostrado como ideia adiada, fora do v6.0."

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, reaproveita o controle | Saves ≈ 0.40 h, anchors to v4.0, seed 1337 | ✓ |
| Sim, mas roda o controle de novo | Loses the saving and the 5th-recipe route | |
| Não entra | Loses the v4.0 bridge | |

**User's choice:** "Opção 1: reaproveita o controle v4.0 por SHA-256, e a seed da grade fica em 1337. Dois acréscimos:1. Limite declarado: uma seed só para a grade inteira. A Fase 40 mostrou variação entre seeds, então nenhum resultado da E3 vale para outra seed.2. Previsão gravada antes da rodada (descritiva; um desacordo é um achado): os pontos σ = 0,5 e σ = 1 da receita v4.0 repetem o recall dos registros v4.0 (results/phase25_point_dp_n8_sigma0p500000.json e sigma1p000000.json: 0/1008 ensinados, 0/648 não ensinados). O relatório põe as duas leituras lado a lado."
**Premise check:** the numbers hold, but the two cited point records carry no recall fields. The 0/1008 and 0/648 are in `results/phase25_recall.json` (points dp_n8_sigma0p500000 / 1p000000). The prediction cites that file.

| Option | Description | Selected |
|--------|-------------|----------|
| Fatorial 2×2 | lr {3e-4, 1e-3} × T {200, 800}, v4.0 corner included | ✓ |
| Varredura em T, lr fixo | T {200, 400, 600, 800} at lr 3e-4 | |
| Varredura em lr, T fixo | Same ε for all 4 | |

**User's choice:** "Opção 1: fatorial 2×2, lr ∈ {3e-4, 1e-3} × T ∈ {200, 800}, lote 8, com o canto v4.0 (3e-4, 200) reaproveitado. Dois acréscimos:1. Previsão gravada antes da rodada (descritiva; um desacordo é um achado): nenhuma das 4 receitas passa o limiar de recall em σ = 0,5 ou σ = 1. Se alguma passar, espera-se que seja em T = 800, não em lr = 1e-3. A justificativa é um argumento, não uma medida do projeto: com AdamW, o lr escala sinal e ruído juntos, e só T acumula sinal mais depressa que ruído.2. Declarar como resultado possível que um controle σ = 0 com lr = 1e-3 não aprenda ou piore a retenção; nesse caso os pontos da receita ficam REFUSED, como na v4.0, e isso é reportado com o mesmo peso."
**Premise check:** AdamW confirmed as the DP optimizer (`src/personacore/privacy/dpsgd.py:32`).

| Option | Description | Selected |
|--------|-------------|----------|
| Escala com T: 10% | Same fraction as v4.0 | ✓ |
| Fixo em 20 passos | 2.5% at T = 800 | |

**User's choice:** "Opção 1: aquecimento em 10% de T (20 em T = 200, 80 em T = 800), cosseno sobre o T inteiro, a mesma forma da v4.0. Declarar no pré-registro que WARMUP_STEPS = 20 em teach_persona.py é a v4.0 e que a E3 passa o aquecimento derivado de T, sem mudar a constante."
**Premise check:** `WARMUP_STEPS = 20` at teach_persona.py:1600; warmup + cosine in `src/personacore/training/schedule.py`.

| Option | Description | Selected |
|--------|-------------|----------|
| C = 1,3254 fixo | Same σ·C noise across recipes | ✓ |
| Recalibrar C por receita | Confounds C with lr × T; costs hours | |

**User's choice:** "Opção 1: C = 1,3254 fixo nos pontos com ruído das 4 receitas (CLIP_NORM da v4.0, regra da mediana em phase25_clip_calibration.json), e o controle σ = 0 com o C não vinculante de 10⁶, como na v4.0, para o reaproveitamento valer. Dois acréscimos:1. Limite declarado: o C foi calibrado em dp_n64, σ = 0, lr 3e-4 e T = 200; nas receitas com lr = 1e-3 ou T = 800 a distribuição das normas pode ser outra.2. Cada ponto publica o clip_bind_count (quantos registros foram cortados), como leitura descritiva, sem veredito."
**Premise check:** the median rule over dp_n64 and the non-binding probe are confirmed in `results/phase25_clip_calibration.json`.

| Option | Description | Selected |
|--------|-------------|----------|
| Como o controle v4.0 | clip_norm 1e6, same train_config | ✓ |
| Com o clip DP e σ = 0 | Isolates noise from clip; breaks comparability | |

**User's choice:** "Opção 1: os 3 controles novos seguem o controle v4.0 (clip_norm = 1e6, grad_clip 1.0, o mesmo train_config), com só lr, T e o aquecimento derivado de T mudando. Limite declarado: a diferença entre o controle e os pontos com ruído mistura o clip por registro (C = 1,3254) e o ruído; a E3 não separa os dois, como a v4.0 também não separava."

---

## Quinta receita

Measured from the Phase 36 unit prices: 0.4118 h per run at T = 200 and 0.5519 h at T = 800. The 11-run grid is 5.37 h against 6.62 h. A 5th recipe fits only at T ≤ 224 (6.61 h); at T = 800 it reaches 7.03 h.

| Option | Description | Selected |
|--------|-------------|----------|
| Não pedir | Cap 4 intact; 1.25 h margin | ✓ |
| Pedir, em T = 200 | 6.61 of 6.62 h; cap ruling needed | |
| Pedir, acima da linha E3 | Exceeds the E3 line; cap and line rulings | |

**User's choice:** "Opção 1: não pedir. O cap de 4 fica intacto, e as 1,25 h de folga ficam como margem para a corrida real."

---

## 'Garantia vazia' e a resposta

Grid ε at δ = 1e-5: T = 200 → 519.70 / 159.44; T = 800 → 1840.30 / 519.70. No prior vacuity definition was found in the repo.

| Option | Description | Selected |
|--------|-------------|----------|
| Por construção, com o limite de teste | Criterion holds at all 8 points | ✓ (modified) |
| Uma linha fixa de ε | A chosen number | |
| Sem definição | Only the per-point ε | |

**User's choice:** "Opção 1, com a fonte já registrada: "vazia" por construção, pelo limite da moeda viciada de .planning/research/V6-PREREG-09.md (linha 53): sob ε-DP nenhum adivinho acerta com probabilidade maior que e^ε/(e^ε+1), e com ε ≥ 159,4 (o menor dos 8 pontos, T = 200, σ = 1) esse limite é 1 em precisão de máquina. A forma TPR ≤ e^ε·FPR + δ só entra no texto se a pesquisa achar e conferir uma fonte para ela; sem fonte conferida, fica de fora. Nenhuma linha de corte nova."
**Premise check:** V6-PREREG-09.md:53 carries e^ε/(e^ε+1); `1/(1+e^−159.44) == 1.0` in float64.

| Option | Description | Selected |
|--------|-------------|----------|
| Por ponto, nas duas pernas | 4 × 2 table, equal-weight counts | ✓ |
| Por receita, exigindo os dois σ | Stricter | |
| Por ponto, só na perna ensinada | Not the imported v4.0 rule | |

**User's choice:** "Opção 1: por ponto, nas duas pernas, F_Y × o controle da mesma receita, tabela 4 × 2 com passa / não passa / REFUSED. Dois acréscimos:1. Retenção e gap de diálogo saem por ponto como leitura descritiva, sem entrar no "sim" (o RECIPE-03 só pergunta por recall; o teto de retenção v4.0 reprova adaptadores intactos, como na D-14 da Fase 41).2. A linha de resumo dá a contagem inteira ("k de 8 pontos passam; m REFUSED"), nunca só "sim/não", porque um sim em 1 de 8 é seleção dentro da grade, e o selection_accounted fica false."
**Premise check:** 41-CONTEXT D-14 confirms that the cap 3.9085 is anchored on adapter-off, while the intact adapters read 4.156–4.332.

**Null case (free text, before the next area):** "se nenhum ponto passar, o relatório diz isso na primeira linha, com as palavras "nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)", seguida do recall bruto de cada ponto nas duas pernas e do ε de cada um. Sem "ainda", sem "possivelmente com outra receita" e sem nenhuma extrapolação para além das 4 receitas e da seed 1337."

---

## Ordem e aprovações

| Option | Description | Selected |
|--------|-------------|----------|
| Dois estágios | Controls → threshold filled → noised points | ✓ |
| Uma corrida só | Threshold computed after the noised points exist | |

**User's choice:** "Opção 1: dois estágios. Estágio 1: os 3 controles σ = 0 novos, mais a verificação por SHA-256 do controle v4.0 reaproveitado; registros commitados, e8_recall_threshold preenchido e commitado. Estágio 2: os 8 pontos com ruído, com a checagem P22 (RECIPE-04) para T = 800 rodando e passando antes de qualquer treino. O ancestry test prova que o limiar vem antes do primeiro registro de ponto com ruído." (Written down as `e3_recall_threshold`.)

| Option | Description | Selected |
|--------|-------------|----------|
| Rodam e saem REFUSED | As v4.0 did for n64 | ✓ |
| Não rodam | Points NOT_RUN | |

**User's choice:** "Opção 1: rodam e saem REFUSED, como na v4.0, com ε e recall bruto nas duas pernas publicados. O custo já está na linha E3 (os 8 pontos foram orçados), não sai da folga." (This corrects the option text, which said "dentro da folga".)

| Option | Description | Selected |
|--------|-------------|----------|
| Revisão + ensaio em CPU | As Phase 41 (41-11 found a real defect) | ✓ |
| Só a revisão | Faster | |

**User's choice:** "Opção 1: revisão do pré-registro e do driver, e depois um ensaio curto em CPU antes de qualquer MPS, como na Fase 41. O ensaio deve exercitar: o reaproveitamento do controle v4.0 pela checagem de SHA-256, o aquecimento derivado de T (20 em T = 200, 80 em T = 800), a checagem P22 para T = 800, e o caminho REFUSED de um controle que não aprende."

| Option | Description | Selected |
|--------|-------------|----------|
| O padrão da Fase 41 | One approved per launch; stage-2 records under three | ✓ |
| Menos approved | One per stage | |

**User's choice:** "Opção 1: o padrão da Fase 41. Um approved por lançamento (estágio 1 e estágio 2); os registros do estágio 1 e o limiar sob um approved; os do estágio 2 sob três (ledger + pontos, registro E3, relatório). Cada commit sozinho, por caminho explícito."

---

## Closing

**User's choice:** "escolho opçao 3:Pronto para o CONTEXT, com uma declaração a mais: todos os pontos usam a seed 1337, então dentro de uma receita os pontos σ = 0,5 e σ = 1 podem compartilhar a sequência de ruído (escalada por σ). O CONTEXT confere no código se isso acontece e declara o que achar; os dois σ de uma receita não são réplicas independentes, e nenhuma leitura os trata assim. Depois escreve e commita o 42-CONTEXT.md e o 42-DISCUSSION-LOG.md."
**Measured (CONTEXT D-10):**
- The generator is seeded once from the run seed, and the draws have no σ branch.
- On CPU, the σ = 1 noise equals exactly 2× the σ = 0.5 noise (steps 1-3, 331,776 elements).
- The sharing also crosses lr and the first 200 steps of T = 800. The MPS generator was not measured.

## Claude's Discretion

- Module and record file names inside the Phase 35 globs; how the fill and ancestry tests mirror Phases 40/41.

## Deferred Ideas

- Batch < 8 with a subsampled (q < 1) accountant — outside v6.0.
