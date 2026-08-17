# Phase 19: Selective Memory Erasure - Context

**Gathered:** 2026-08-17
**Status:** Ready for planning
**Source:** Direct decision capture against `19-RESEARCH.md`'s "Open decisions for the planner"

<domain>
## Phase Boundary

Erase **one** named taught fact from the 331,776-parameter LoRA adapter and report what it cost,
under the rule committed at `23a830c` before any v3.0 number existed. The phase was created by that
rule — `erasure_is_worth_attempting(92, 104, 0, 104)` → True — not by a planning decision.

**In scope:** the M1 ablation mechanism, the M2 retrain-without reference arm, the blind calibration
that produces (a)'s floor, the (b)/(c) measurements, the committed-verdict call through
`erasure_succeeded()`, and the dated continuation that publishes the (c) diagnosis beside the
literal verdict.

**Out of scope:** any third mechanism (M3/M4 explicitly declined below); amending `23a830c`;
converting representational consistency into a gate.

</domain>

<decisions>
## Implementation Decisions

Every decision below is LOCKED and must be reflected in the pinned pre-registration file **before
the calibration runs**. Six were taken by the user; two are research leans adopted by default and
flagged as such.

### D1 — Mechanism: M1 + M2, and nothing else (LOCKED)

> "Confirma opção 1: M1 (ablação de componente ΔW rank-1, 288 componentes endereçáveis, seleção
> ~1min, ~80 linhas, sem loop de treino) + M2 (retreino-sem-o-alvo como braço de referência
> ERASE-02, 81s, ~15 linhas). Nenhum terceiro mecanismo — o par já responde à pergunta central da
> fase sem escopo adicional não-garantido."

- **M1** — ΔW rank-1 component ablation. `ΔW = scale · (B @ A)` is exactly a sum of
  **288 rank-1 outer products** (36 wrapped projections × r=8), each addressable by
  `(layer, projection, j)`. Selection by contribution to the target's teacher-forced value-span
  NLL, ~288 forward passes over a ~10-token span. Stays inside the decomposition, so the result
  remains exactly representable in the shipped artifact format and passes `load_adapter_weights`'
  key/shape/scale audits unchanged.
- **M2** — retrain without the target fact (ERASE-02): an `arm_spec` over `LOCKED_FACTS` minus one,
  81 s measured.
- **M3, M4, M5, M6 are OUT.** Not deferred-with-regret — declined. The M1/M2 pair answers the
  phase's central question, and a third arm is unguaranteed scope.
- **Mechanism identity AND its parameters are pinned before calibration**, so the mechanism cannot
  become a knob swapped after a disappointing floor.

### D7 — Target fact: highest Phase 18 recall, by deterministic rule (LOCKED)

> "alvo = fato de maior recall medido na Fase 18 (entre os 8 slots core gateados), regra
> determinística e pinada no arquivo de pré-registro ANTES de qualquer calibração ou apagamento
> rodar. A escolha usa o dado já commitado da Fase 18 (não dado novo gerado sob observação)."

The rule selects on **already-committed Phase 18 per-fact numbers** — the known past, never a
result still to come. That is what makes it pre-registrable at all. The named target and the rule
that produced it both land in the pinned file before anything runs. A tie-break must be specified
in the same commit (do not leave it to run time).

### D5 — (a) denominator: n = 27, both tiers pooled (LOCKED)

> "denominador (a) = n=27, held-out (13) + taught (14) questões por fato, agrupadas.
> wilson_upper_bound(0,27) = 0.0911, restaurando alcançabilidade real para apagamento perfeito.
> Não estende além de n=52/108."

At n=13 nothing below **0.172267** is clearable at any outcome, including a perfect erasure — (a)
would be unclearable by construction. n=27 gives `wilson_upper_bound(0, 27) = 0.0911`, roughly
half. **Reachability must still be PROVED before the pin**, in the register of
`assert_holm_family_reachable`, not assumed from these two numbers.

### D2 — (a) floor adjustment: mirror the operator, keep it HARDER (LOCKED)

> "espelha o operador de modo que o ajuste continue tornando (a) mais difícil de limpar,
> preservando a intenção do procedimento de calibração cega de Fase 14 (torna mais difícil, nunca
> mais fácil) em vez do sinal aritmético literal, que aponta na direção errada quando aplicado a um
> piso em vez de um teto."

Phase 14 discounted a ceiling **downward** to make its threshold harder to clear. Erasure's floor
is an **upper cap**, so the literal operator would loosen it. Intent wins over arithmetic sign: the
adjustment must make (a) harder, never easier. The plan states the mirrored operator explicitly and
shows both directions' values, so a reader can see the choice rather than infer it.

### D3 — Condition (c): run literally, publish FAILURE, diagnose beside it (LOCKED, prior session)

Condition (c) runs **exactly as pre-registered at `23a830c`**, with no amendment to the original
text. The literal **FAILURE** against the criterion as written is published. A **dated continuation**
is added beside it diagnosing the root cause: `23a830c` capped against
`V20_MASKED_DIALOGUE_VAL_PPL` = 4.5733, the **adapter-OFF** baseline, when the correct comparison
for post-erasure capability preservation is against the **adapter-present** baseline — the one
Phase 14 already measured and kept descriptive (5.8154, +27.16%, `COLLAPSE_PPL_TRIGGER` tripped, no
gate). Both readings publish **side by side; neither replaces the other.**

**The append mechanism is already built and proved.** `scripts/_addendum.py` +
`tests/test_phase19_docs.py`, committed `f8441ec`. `phase18_extraction.append_addendum` was
**rejected after measurement**, not by preference: it parameterises the placeholder it replaces but
hard-codes the line it writes, so at a Phase 19 location it injects a Phase 18 ship-decision
sentence. RED→GREEN over three mutations verified against the committed bytes. **The planner must
treat `_addendum.py` as an existing dependency and must NOT re-derive it.**

### D8 — Publication posture: unsoftened (LOCKED, follows D3)

If ablating enough to erase the target also destroys non-targets, the finding is *"selective erasure
is not selective at 331,776 parameters"* and it **ships unsoftened**, in the register Phase 18
shipped `LEAKAGE_DEMONSTRATED`. Decided now, before the number exists, so the framing cannot be
written after it.

### D4 — (b) noise-floor estimator: seed-stride re-scoring (RESEARCH LEAN, adopted)

Seed-stride re-scoring of the **unerased** adapter (~30 min, Phase 17 precedent) rather than a
second-seed retrain, which would confound init noise with the erasure. Pinned before running.
*Flagged: adopted from the research's lean, not separately confirmed by the user. If the planner
finds the confound argument does not hold, raise it rather than silently switching.*

### D6 — Calibration adapter: retrain (RESEARCH LEAN, adopted)

Retrain the calibration adapter (81 s) rather than reusing
`phase14_cal_first_person_replay_adapter.pt`. Costs 81 seconds and removes an argument about
instrument and recipe provenance. *Flagged: research lean, adopted by default.*

### B4 — Calibration-fact selection rule, and FLOOR_CEILING (LOCKED 2026-08-17)

Surfaced by the plan-checker after D1–D8 were taken; confirmed by the user unchanged.

**The rule stays as specified** (`19-06-PLAN.md:254-259`): the calibration fact that gets erased is
the **first eligible member of `phase14_factset.CALIBRATION_POOL` in its committed order**
(`:102-113`), eligible = survives `build_calibration_corpus`' self-naming filter with ≥1 taught and
≥1 held-out question; tie-break = lexicographically smallest `fact_id`, stated although unreachable
since the order is total. Blind in the strong sense: reads **no** Phase 18 per-fact recall and
**no** Phase 19 result — its own number is what the floor derives from, so choosing the fact after
seeing candidate rates is the manoeuvre `23a830c` exists to forbid. Pool disjointness from
`CANDIDATE_POOL` is by construction (`:98-101`), so the target can never be selected here.
`CALIBRATION_POOL`'s order was first committed `5ff5c0d` (2026-08-02), ten days before the v3.0
pre-registration `23a830c` (2026-08-12) — the order is genuinely prior to this phase.

**RECORDED EXPLICITLY, not left implicit — the determinism is conditional.** The rule is
deterministic **given the pin**, NOT given today's repo. "First eligible" depends on
`build_calibration_corpus`' question-family set, and that builder is Phase 19 code that does not
exist until wave 6. The *filter* is mechanical and already committed (`contains_value`, the same
rule Phase 14 used at `teach_persona.py:1031`), so no judgment enters — but the identity of the
selected fact is not derivable from the committed repo alone until the family set is pinned in the
same commit as the rule. Anyone auditing this later must be able to read that qualification here
rather than reconstruct it: an unqualified "deterministic" would be a sentence that does not
survive checking, in a file that is unamendable after 19-07.

**`FLOOR_CEILING` stays 0.20, inherited from Phase 14's `THRESHOLD_FLOOR`, not reconsidered.**
Recorded with its known consequence: `lock_erasure_floor` saturates at the ceiling for every
`cal_rate ≥ 0.3333`, so above that point the blind calibration stops discriminating and every rate
yields the identical floor. Phase 14's calibration arm measured 0.4143 taught / 0.2506 held-out
(`results/phase14_recall_report.md:20-21`), so **if Phase 19's single calibration fact scores
anywhere near that, the floor lands at 0.20 — the more permissive end of the 0.091079–0.20 range
(2.196×).** That is accepted, deliberately, and noted before the number exists so it cannot be
presented afterwards as either a surprise or a design win. The Phase 14 figure is a *prior*, not a
prediction: it is a ten-fact pool aggregate scored by `score_items`, whereas Phase 19 feeds one
fact's rate at n≈16–27 scored by the Phase 18 adversary.

**Wave-7 verification is positive, not presence-only** — confirmed by reading
`19-07-PLAN.md:80-82` (automated audit item 7: "a positive check that the rule reads NO Phase 18
recall and NO Phase 19 result") and `:123-126` (human checklist: "chosen blind, from the committed
pool order alone, and that the pool is disjoint from the target's").

### Claude's Discretion

- Plan/task decomposition, wave structure, and file layout for the Phase 19 driver.
- Where the pinned pre-registration file lives and what its ancestry/reachability guards look like,
  following Phase 18's D-04 pattern (`tests/test_phase16_prereg.py` is the guard register).
- Whether the M1 selection sweep is committed as an artifact or recomputed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The pre-registration (unamendable)
- `scripts/erasure_gate.py` — `ERASURE_DECISION_RULE`, `ERASURE_GOAL_FRAMING`,
  `erasure_is_worth_attempting()`, `erasure_succeeded()`. Committed `23a830c`, 2026-08-12 16:27:43
  -0300, before Phase 16 ran. Success criteria are INHERITED from here, never re-authored.

### Research
- `.planning/phases/19-selective-memory-erasure/19-RESEARCH.md` — Q1 mechanism table (M1–M6 with
  costs and failure modes), Q2 the Phase 14 calibration chain reconstructed from git, Q3 instrument
  reuse map, Q4 the (c) landmine, Q5 ERASE-02, Q6 pin ordering, Q7 adversarial self-critique.

### Instruments to REUSE, not rebuild
- `scripts/phase18_extraction.py` — `span_nll_from_ids` (:1050), `value_span_nll` (:1110),
  `exposure_rank` (:1230), `_handoff_counts` (:2782), attack corpus, `assert_no_value_in_prompt`.
  **FROZEN by STAT-05** — import only; any commit to it reddens `tests/test_phase16_prereg.py`.
- `scripts/phase16_persistence.py` — `cluster_bootstrap`, `sign_test_exact`, `holm`/`HOLM_ALPHA`,
  `item.seed_index` pairing, the binding 270-question fixture. **Not frozen** — the shared-stats
  surface.
- `scripts/_addendum.py` — the append-only continuation writer (D3). Committed `f8441ec`.
- `scripts/_verdict.py` — the one anchored `## Verdict` section read.
- `src/personacore/continual/fisher.py`, `.../ewc.py` — only if a Fisher read is wanted
  descriptively; M4 as a mechanism is OUT.

### Ordering discipline
- `tests/test_phase16_prereg.py` — the ancestry guards. Phase 19 needs the analogous one, and the
  pin must precede every `results/phase19_*` first-add.

</canonical_refs>

<specifics>
## Specific Ideas

- **The NLL instrument is load-bearing for a SUCCESS, not just for a null.** `erasure_succeeded()`
  returns INCONCLUSIVE when `target_successes == 0` and `zero_results_have_nll` is False — and a
  successful erasure produces exactly that zero. Recording teacher-forced NLL on every zero is what
  stands between a real success and an unpublishable INCONCLUSIVE.
- **`dialogue_ppl_noise_floor` is a required keyword with no committed default**
  (`erasure_gate.py:208`). It is threshold-shaped and must be pre-registered like one. The only
  measured value in the repo is Δ_dialog = 0.001704 (`results/finetune_smoke_report.md:56`).
- **Retention PPL has never been measured on a LoRA-adapted model** — `retention_perplexity` has
  four call sites, none on an adapted model. The plan must produce it or state why not.
- **Reachability proof before the pin**, in `assert_holm_family_reachable`'s register: show that the
  chosen floor is clearable at n=27 by some attainable outcome, so (a) is not a criterion that
  cannot be met by construction.
- **Ablation must not break the adapter-off bit-identity control** (`run_bit_identity_control`, max
  abs diff exactly 0.0). M1 stays inside the rank-8 decomposition specifically so this holds.

</specifics>

<deferred>
## Deferred Ideas

- M3 (retain-set continued FT), M4 (Fisher-anchored damping), M5 (task-arithmetic negation),
  M6 (gradient ascent) — declined for this phase under D1, not scheduled elsewhere.
- Erasing more than one fact — the ROADMAP fixes "**one** taught fact".
- Any amendment to `23a830c` — permanently out of scope; the correction path is a dated
  continuation, never an edit.

</deferred>

---

*Phase: 19-selective-memory-erasure*
*Context gathered: 2026-08-17*
