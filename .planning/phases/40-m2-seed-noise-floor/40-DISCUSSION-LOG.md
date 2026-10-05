# Phase 40: M2 Seed Noise Floor - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-05
**Phase:** 40-m2-seed-noise-floor
**Areas discussed:** Floor estimator, Reuse vs fresh, gap_noise_floor, M1×M2 re-reading, plus
Rafael's addition (target rank across M2 seeds) and two follow-up decisions (run order, estimator home)

---

## Gray-area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Floor estimator | full / M2 / both; range→max, pairwise max, or SD | ✓ |
| Reuse vs fresh | reuse M2@1337 (22e6…, K=48 A2 record); full@1337 vs persona_adapter.pt; Phase 19 dialogue-floor adapters | ✓ |
| gap_noise_floor | dialogue on−off gap floor for Phase 41, unpriced in E2 | ✓ |
| M1×M2 re-reading | floor only, or also re-read delta_taught_to_m2 per slot | ✓ |

**Rafael's reply (free text, all four plus a fifth), summarized:**
1. Estimator: both groups separately; d(i,j) = max over 7 slots of |Δrecall| per same-group seed pair
   (v3.0's statistic); group floor = mean over 10 pairs (preference, one-pair scale); published
   floor = larger group; max/min/each pair and per-slot range+SD beside it; sampling noise declared.
2. Train all 10 fresh with today's code and recipe; old adapters only as a free determinism check
   (M2@1337 sha vs 22e6…; dialogue-floor adapters if same recipe); persona_adapter.pt recipe
   differences recorded field by field as a v3.0 limitation, compared descriptively with full@1337.
3. gap_noise_floor: adapter-on dialogue PPL on the 5 full adapters, committed adapter-off checked;
   mean of |Δgap| over 10 pairs (preference), max beside; price before, approved in D-09 format;
   also price the 5 M2 (descriptive).
4. Publish beside 0.148 without touching the (b) margin; re-read delta_taught_to_m2 per slot beside
   the 25 full×M2 pairs (5 same-seed marked). Descriptive.
5. Addition: zorp anchor rank vs Phase 38 minted list at 8/32/128/512, and R_q n1 at |R|=8
   (committed and minted), in each M2. Price and cap first; not included without "approved".

**Premise check (Claude, before writing):** all measurable premises confirmed (v3.0 max statistic
0.148148 = 4/27; 10 and 25 pairs; adapter-off 4.573349214207799 identical across seeds; 22e6… in
phase19_arm_retrain.json; rank 16 vs 32 at |R| 512; n1 5/27 vs 0/27 at |R| 8; nested sizes; zorp =
pet_name; "D-09 format" = 38-D-21/D-22). Two planning notes raised: no committed price for
dialogue PPL; recipe identity of the dialogue-floor adapters unverified.

---

## Done check

| Option | Description | Selected |
|--------|-------------|----------|
| Write CONTEXT | lock decisions, two notes as planning items | ✓ (with two more decisions) |
| More gray areas | run order; estimator home | |

**Rafael's reply:** write CONTEXT with two more decisions:
1. Run order per seed in seed_list() order: full, M2, both A2 passes, then next seed; a mid-seed
   stop drops that seed from the estimator, declared beforehand.
2. Both estimators in the same e2_noise_floor_estimator fill if Phase 35's rule allows; otherwise
   the gap one in phase40_prereg, frozen before any record. "Diga qual dos dois caminhos valeu."
   The two notes stay as planning items; he wants to see both before approving any training.

**Resolution (Claude, measured):** path 1 holds — `_rule_e2_noise_floor_estimator` runs only
`_prove_entry`; a dry CPU `fill()` accepted a mapping value with both estimators (mappingproxy
returned); slot input_records = (), owner 40.

## Claude's Discretion

- Record field layout beyond the `gap_noise_floor` contract key; per-seed record split (keeping
  whole-seed units); driver/rehearsal mechanics per Phases 37-39.

## Deferred Ideas

None.

## Plan-phase 40 follow-up (2026-10-05) — D-08 premise

**Measured (researcher, then re-measured by the orchestrator):** `persona_adapter.pt` (226f2ae5…) and
`phase19_erase_dialogue_floor_seed1337_adapter.pt` (f12ab4c3…) are tensor-identical (72/72
`torch.equal`, identical non-tensor metadata); the file sha256 differs only by the file stem that
`torch.save` writes into the zip.

**Question:** how should D-08 read? Options: correction (recommended) / narrowed limitation / table as written.

**Rafael (verbatim):** "Opção 1 (correção), com dois ajustes:1. D-08 passa a dizer: persona_adapter.pt
e phase19_erase_dialogue_floor_seed1337_adapter.pt são o mesmo adaptador (72 tensores iguais; o sha do
arquivo difere só pelo nome gravado no zip). O relatório do milestone registra isso como correção da
nota do scout, não como limitação do v3.0.2. A diferença residual (contagens do A2 do lado ensinado
vindas dos sorteios do run_arm da Fase 18, e não do run_erasure_arm) é reportada com o tamanho medido
contra o completo@1337. Ela só recebe o nome de limitação do v3.0 se as contagens diferirem em pesos
idênticos. Se o completo@1337 novo não reproduzir os pesos bit a bit, o relatório diz que os dois
efeitos não se separam.3. Correção de D-02 (checagem de determinismo): toda comparação entre adaptador
novo e commitado é feita tensor a tensor (torch.equal em todos os tensores, mais metadados), nunca
pelo sha256 do arquivo. Vale para M2@1337 contra phase19_erase_reference_adapter.pt e para
completo@1337 contra persona_adapter.pt."

**Recorded:** CONTEXT "Addendum (2026-10-05)". His item 3 is labelled "D-02"; its content is the
determinism check, which is D-07 — recorded as a D-07 amendment, D-02 unchanged.
