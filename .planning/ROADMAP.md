# Roadmap: PersonaCore

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-8 (shipped 2026-06-11) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v2.0 Weight-Based Memory** — Phases 9-15 (shipped 2026-08-12) — [archive](milestones/v2.0-ROADMAP.md)
- 🚧 **v3.0 Adversarial Privacy Audit and Selective Memory Erasure** — Phases 16-18 (in progress) *(Phase 19+ Selective Erasure deferred, gated on 16-18's measured numbers)*

## Overview

v1.0 built the foundation by hand: a ~13.9M-parameter GPT-style decoder, a from-scratch BPE
tokenizer, and a resumable training harness, pretrained on TinyStories on the author's own Apple
Silicon machine to headline perplexity 2.1066.

v2.0 proved the novel claim on top of it: **personalization lives in the model weights, not in a
prompt or a store.** From-scratch LoRA teaches user-specific facts into 331,776 adapter parameters
on a frozen conversational base, and a fresh process recalls them from an empty prompt with the
context provably wiped; from-scratch EWC keeps the fine-tune from destroying the base model, at a
3.6× separation clearing its pre-registered margin by 33.61×. Every headline number is gated by a
rule committed to git before the number existed.

v3.0 stops *asserting* that weight-based memory is private and starts **measuring** it. Phase 16
fixes the shared measurement instrument and runs the four-arm weight-vs-prompt persistence control
on the binding 270-question fixture; Phase 17 builds the adversarial persona generator DEMO-F1
always needed and scores a full isolation matrix under deliberate slot collision; Phase 18 attacks
the adapter black-box and reframes the demo's toggle as **availability, not authorization**. The
milestone's own headline finding is already committed against it — Phase 14's in-context control
scored 1/1944, so prompt-stuffing sits at the floor and no "weights beat prompting" headline is
licensed until a capability ladder says otherwise. Selective Erasure (Phase 19+) is deliberately
unplanned: its decision rule was pre-registered at `23a830c` **before Phase 16 runs**, and the
phase enters this roadmap only if that rule returns True on measured numbers.

## Phases

<details>
<summary>✅ v1.0 Foundation (Phases 1-8) — SHIPPED 2026-06-11</summary>

- [x] Phase 1: Scaffolding & Reproducible Environment (3/3 plans) — completed 2026-06-04
- [x] Phase 2: From-Scratch BPE Tokenizer (3/3 plans) — completed 2026-06-04
- [x] Phase 3: Bigram Baseline & Training Harness (4/4 plans) — completed 2026-06-04
- [x] Phase 4: GPT Transformer Decoder (3/3 plans) — completed 2026-06-05
- [x] Phase 5: TinyStories Pretraining (2/2 plans) — completed 2026-06-05
- [x] Phase 6: Generation & Sampling (3/3 plans) — completed 2026-06-06
- [x] Phase 7: Evaluation (3/3 plans) — completed 2026-06-09
- [x] Phase 8: Demo & Writeup (8/8 plans) — completed 2026-06-10

Full phase details: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) · Audit: [milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v1.0-phases/`

</details>

<details>
<summary>✅ v2.0 Weight-Based Memory (Phases 9-15) — SHIPPED 2026-08-12</summary>

**Milestone Goal:** Prove personalization lives in the weights via from-scratch LoRA + EWC on the v1.0 foundation — conversational fine-tune, no-forgetting A/B, and a clean-room teach-then-recall demo.

- [x] Phase 9: LoRA Core (4/4 plans) — completed 2026-06-11
- [x] Phase 10: EWC Core (3/3 plans) — completed 2026-06-12
- [x] Phase 11: Conversational Data Pipeline (4/4 plans) — completed 2026-07-31 *(DailyDialog cut per D-00)*
- [x] Phase 12: Stage-2 Conversational Fine-Tune (5/5 plans) — completed 2026-08-01
- [x] Phase 13: EWC A/B No-Forgetting Experiment (4/4 plans) — completed 2026-08-02
- [x] Phase 14: Teach-Then-Recall Demo (11/11 plans) — completed 2026-08-02
- [x] Phase 15: Figures & Writeup (8/8 plans) — completed 2026-08-02

**Headline results:** EWC retention PPL 3.891140 vs naive 8.524171 from a shared 2.1076 step-0
anchor — the pre-registered gate cleared by 33.61× its margin. Closed-book recall 0.4921 taught /
0.3483 held-out against thresholds 0.2486 / 0.2000, with the adapter-off control at exactly
0/2430. Fisher/Δ correlation Spearman ρ = 0.801544, 95% CI [0.597984, 0.920291].

Full phase details: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md) · Audit: [milestones/v2.0-MILESTONE-AUDIT.md](milestones/v2.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v2.0-phases/`

</details>

### 🚧 v3.0 Adversarial Privacy Audit and Selective Memory Erasure (Phases 16-18)

**Milestone Goal:** Stop asserting that weight-based memory is private and start measuring it — what
weights actually buy over prompting, whether separately-taught personas stay isolated under
adversarial collision, and whether an adversary can extract taught facts through a toggle that only
ever controlled availability.

- [x] **Phase 16: Weight-vs-Prompt Persistence Control** - Four arms on the binding 270-question fixture, instrument pairing defect fixed first, headline licensed by a blocking capability ladder (completed 2026-08-14)
- [ ] **Phase 17: Multi-Persona Isolation Matrix** - N=3 deliberately colliding personas scored as a cross-matrix with a base-prior column, an adapter-swap canary, and a cell-blind scorer
- [ ] **Phase 18: Black-Box Adversarial Extraction Audit** - Paraphrase / prefix-injection / role-play / repeated-sampling attacks, adapter-on vs adapter-off at equal budget, admissibility pre-registered one-directionally

**Deferred — Phase 19+ Selective Erasure (not planned, deliberately).** ERASE-01 and ERASE-02 enter
this roadmap **only** if `erasure_is_worth_attempting()` in `scripts/erasure_gate.py` returns True
on Phase 18's measured numbers. That rule was committed at **`23a830c` (2026-08-12 16:27:43)**,
before Phase 16 runs, referencing only v2.0-published baselines — designing Phase 19 now is exactly
the motivated interpretation the pre-registration exists to prevent. Goal framing is already fixed
(*auditable forgetting with a measurable bound plus representational consistency reported honestly*
— **not** "indistinguishable from never-having-learned"); no mechanism, schedule, or design is
committed.

## Phase Details

### Phase 16: Weight-vs-Prompt Persistence Control

**Goal**: Measure what memory-in-weights buys over prompting as a paired number with a bound — four
arms on the same committed question fixture, with the shared instrument's pairing defect fixed
first and the headline licensed by a capability ladder that runs *before* anything is scored
**Depends on**: Nothing new — consumes `persona_adapter.pt`, `convbase_best.pt`, the committed
`results/phase16_recall_sample.json` fixture (270 questions, pinned by
`tests/test_phase16_fixture_regen.py`), and PREREG-01's `scripts/erasure_gate.py` at `23a830c`
**Requirements**: STAT-01, STAT-02, STAT-04, STAT-05, STAT-06, PERS-01, PERS-02, PERS-03, PERS-04, PERS-05, PERS-06, PREREG-02
**Success Criteria** (what must be TRUE):

  1. The blocking in-context capability ladder (PERS-01) runs and is committed **before** any
     comparison is scored, and the headline is emitted by a committed `licensed_headline()` whose
     branches — including the branch where the prompt arm never leaves Phase 14's 1/1944 floor and
     only a *capability-deficit* statement is licensed — were pushed before the run (STAT-05). A
     CPU-only test asserts `erasure_gate.py`'s commit precedes every v3.0 results artifact
     (PREREG-02).

  2. All four arms — prompt-stuffed / adapter-only-with-empty-prompt / base-with-neither /
     embedding-cosine (PERS-04, explicitly not a RAG system: no index, no re-ranking, no chunking) —
     score the **same 270 questions from `results/phase16_recall_sample.json`**, in **four fresh
     processes, one per condition** *(amended 2026-08-12: was "in one process". The split is
     licensed by the no-residue evidence that closed area 1 of the Phase 16 discussion —
     `tests/test_lora_toggle.py:77,95,105` at FIXTURE scope, **and**
     `scripts/phase14_recall.py:1336 run_bit_identity_control` at max |diff| 0.0 on the real 13.9M
     convbase. Both are required: the Phase 9 tests run on a fixture model, so citing them alone
     would inherit a fixture-scope guarantee as a real-weights one.)*,
     paired by `item.seed_index` with the `enumerate(questions)` defect in `run_fairness_control`
     fixed (PERS-05), and with `max_new_tokens`, `forbid_ids`, `stop_ids` and context length equal
     across arms and published as report columns (PERS-02).

  3. Instrument integrity is widened, never weakened: the `persona=` AST guard at
     `tests/test_phase14_scoring.py:425` is widened deliberately and visibly rather than deleted,
     and gains its logical twin `assert_value_in_prompt`, so every `draw_all` call site asserts
     something and no path has a skip mode (PERS-06).

  4. Every reported rate ships with its denominator and a bound: fact-level (n=8) cluster
     resampling as the descriptive interval, Wilson reported alongside and labelled as the
     independence-assuming width, `3/n` shown wherever successes are zero, and no bare `0%` in any
     committed report or figure (STAT-01, STAT-02, STAT-04, STAT-06). The inferential gate is the
     **exact paired sign test over all 2⁸ = 256 sign partitions**, Holm-corrected across the 6
     pairwise arm comparisons — where only 8/8 unanimity clears (p = 0.007812 < 0.05/6) — and a
     verdict of **"not demonstrable at n=8" is a legitimate, pre-registered outcome recorded
     as-written**, exactly as Phase 12 recorded λ\*=None.

  5. Persistence under context pressure (PERS-03) is measured on **the prompt-stuffed arm alone —
     the only arm that carries the fact in the context window** *(amended 2026-08-12: was "on both
     context-bearing arms". The adapter-only arm receives a formal invariance **proof** rather than
     a measurement; base-with-neither and embedding-cosine are **not applicable by construction** —
     the former holds the fact nowhere, and the latter holds it in the candidate pool, which is not
     the context window.)* —
     `block_size=256` truncation, **dilution within the persona span**, adversarial overwrite
     *(amended 2026-08-12: was "dilution across turns". Measured during planning and falsified:
     `build_recall_prompt` (`src/personacore/dialogue/serialize.py:92`) calls
     `encode_dialogue(tok, list(persona), [(question, "")])` — exactly ONE turn — so **no turns
     axis exists** on the recall path. The `PERSONA_CAP = 140` premise that motivated the turns
     wording is also false here: `cap_persona` (`:115`) is called only by
     `scripts/make_transcripts.py:134` and `scripts/prepare_dialog_corpus.py:104`, never by
     `build_recall_prompt`, so the cap does not constrain this path and the persona span reaches
     the 448-token target directly. Truncation remains real and is derived from the dilution axis
     crossing `block_size`, not declared independently.)* — with the weight
     arm's invariance stated as the `run_bit_identity_control` **proof** (max |diff| 0.0), not as a
     statistic, and monotone prompt-arm degradation claimed only if the capability ladder got that
     arm off the floor.

**Plans**: 11 plans in 10 waves

Plans:
**Wave 1**

- [x] 16-01-PLAN.md — PREREG-02 ancestry guard + CI full history + STAT-04 dependency freeze
- [x] 16-02-PLAN.md — PERS-05 `item.seed_index` pairing fix + `assert_value_in_prompt` extraction

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 16-03-PLAN.md — widen the `persona=` AST guard in SCOPE + every-`draw_all`-asserts guard

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 16-04-PLAN.md — D-16 gate widening + ladder threshold pre-registration + `licensed_headline()`

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 16-05-PLAN.md — synthetic ladder material: construction, distance builders, guessability vetting

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 16-06-PLAN.md — ladder cell runner, top rung, D-15 proxy check, report writer

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 16-07-PLAN.md — RUN the capability ladder and commit it (blocking, pre-comparison)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 16-08-PLAN.md — four-arm driver: `CONDITION_ORDER`, shared parity config, arm D cosine

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 16-09-PLAN.md — per-fact statistic, cluster bootstrap, exact sign test, Holm over 6 pairs

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 16-10-PLAN.md — PERS-03 context-pressure sweep + persistence report writer + `main()`

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 16-11-PLAN.md — RUN four fresh processes + sweep, assemble the report, record the verdict

**Research flag**: light research only, scoped to the in-context capability ladder's rung design
(what a 13.9M TinyStories+PersonaChat model can plausibly do at distance ~2 tokens) — the rest is
repo-grounded

### Phase 17: Multi-Persona Isolation Matrix

**Goal**: Measure whether separately-taught personas stay isolated when they are built to collide —
N=3 adversarial personas with contradictory values in the *same* slots, scored as a full
cross-matrix against the base model's own prior
**Depends on**: Phase 16 (the fixed shared instrument: `item.seed_index` pairing,
`assert_value_in_prompt`, the widened `persona=` guard, and the binding 270-question fixture)
**Requirements**: STAT-01, STAT-02, STAT-03, STAT-04, STAT-05, STAT-06, ISO-01, ISO-02, ISO-03, ISO-04, ISO-05, ISO-06, ISO-07
**Success Criteria** (what must be TRUE):

  1. Before any adapter trains, audit item **W1 is fixed** *(amended 2026-08-14: W1 was **already
     closed** before Phase 17 planning began — verified in the working tree during research, not
     taken on report. All three runtime consumers already inject at the artifact's own config:
     `scripts/phase14_recall.py:557`, `scripts/phase14_recall.py:1457`, and
     `scripts/personalize_demo.py:448`; and `src/personacore/lora/inject.py:119-129` audits every
     `LoRALinear.scale` against the artifact's `alpha / r` at the load choke point, raising on
     mismatch. `scripts/teach_persona.py:478` and `scripts/train_adapter_smoke.py:63` retain
     `LoRAConfig()` deliberately and correctly — they **create** artifacts rather than load them,
     and that default is the diagonal anchor D-20 preserves. **Only the ISO-04 half of this
     criterion remains open**: the existing canaries at `scripts/teach_persona.py:638` and
     `scripts/train_adapter_smoke.py:118` cover **training** — trainables moved, frozen base
     bit-untouched — and `_nudge_lora_b` is a test helper, so no **swap** path asserts anything
     today. Landed in quick-260814-d0j.)* — every runtime consumer injects with
     `LoRAConfig(**artifact["lora_config"])` rather than `LoRAConfig()` defaults, since shape audits
     catch `r` drift but never `alpha` (ISO-06) — and an **adapter-swap canary** asserts a `lora_B`
     tensor actually changed on every swap, so a silently failed swap cannot produce the most
     flattering possible wrong answer: **column collapse — one column high, the rest zero**
     (ISO-04) *(amended 2026-08-14, second correction: was "a perfect diagonal with zero leakage".
     **Confidence: MEDIUM — argued from the mechanics of the ISO-02 design, not measured
     empirically.** The argument: under N generation sweeps scored N ways, a swap that silently
     no-ops leaves every sweep generating from whichever adapter was actually resident, so that one
     persona's values appear in every row — its column scores high while the other columns fall
     to ~0, taking two of the three diagonal cells down with them rather than perfecting the
     diagonal. **The exact failure shape is to be CONFIRMED during the ISO-04 canary
     implementation in Phase 17; it is not asserted as established fact here.** What does not
     depend on the shape — and is the operative point of this criterion — is that both shapes are
     equally fake and equally invisible without the canary, and the guard sits in the same place
     either way, so the canary requirement is unchanged regardless of which shape the confirmation
     finds.)*

  2. N=3 personas ship as committed data with colliding names and **contradictory values in the same
     slot**, passing the existing `scripts/phase14_factset_gate.py` guessability + tokenizer-census
     instrument (imported, not copied) with a recorded human GO/ADAPT verdict as a hard blocker
     (ISO-01).

  3. The matrix is **N generation sweeps scored N ways** over shared-slot questions — never persona
     *j*'s own questions against adapter *i*, which would make the off-diagonal ~0 by construction —
     scored by a cell-blind scorer whose signature takes no `(i, j)` argument (pinned by
     `inspect.signature`, no `if i == j:` in the scoring path), with an explicit **adapter-off base
     column** so an off-diagonal hit is separable from the base's own prior (`BASE_PRIOR_SEEDS`
     answers `rose` for pet names unprompted), and confabulations recorded in their own category
     rather than sharing a cell with leaks (ISO-02, ISO-03).

  4. The gated quantity is the **within-run diagonal-vs-off-diagonal contrast**, which needs no
     external threshold — Phase 14's 0.2486 / 0.2000 are **not** used, because they were derived on
     `CALIBRATION_POOL` and reusing that pool as a persona makes the gate circular (ISO-07) — and
     pairwise cell comparisons are corrected by **Holm** step-down, not Benjamini-Hochberg, since
     off-diagonal cells share adapters row-wise and question sets column-wise so BH's
     independence/PRDS assumption fails (STAT-03).

  5. The worst-colliding pair is replicated across k=3 seeds and reported **descriptively**
     (min/max/median, never a hypothesis test) so seed variance is not mistaken for interference
     (ISO-05), every off-diagonal zero carries its denominator and one-sided upper bound (STAT-02),
     and **no aggregate "isolation rate %" over the 9-cell matrix is gated** — that number implies a
     precision N=3 cannot carry (STAT-06).

**Plans**: TBD

### Phase 18: Black-Box Adversarial Extraction Audit

**Goal**: Measure whether an adversary with black-box access can extract taught facts from the
adapter — and correct the claim wording so the demo's toggle reads as **availability, not
authorization**, which is the honest reading of what 36 boolean writes have always done
**Depends on**: Phase 16 (fixed instrument, forced-choice scorer, the binding 270-question fixture).
Phase 17 **only** for optional cross-persona attacks — single-persona Phase 18 stands alone, so
schedule pressure can scope it down without invalidating it
**Requirements**: STAT-01, STAT-02, STAT-04, STAT-05, STAT-06, ATK-01, ATK-02, ATK-03, ATK-04, ATK-05, ATK-06
**Success Criteria** (what must be TRUE):

  1. The attack corpus is constructed **programmatically from committed templates** — A1 paraphrase,
     A2 prefix injection, A3 role-play framing, with repeated sampling as a **budget parameter K**
     rather than a fourth prompt shape — with no external API and no hosted model anywhere in the
     pipeline (ATK-01), and `assert_no_value_in_prompt` applied **substring-aware** (`_strings_in`,
     not an equality check — Phase 14's exact-equality tests passed while the invariant was violated
     by a substring embedding) across the entire corpus, making the guard the operational definition
     of "the attacker does not already know the answer". Prefix injection carries a declared,
     small, pre-registered injection budget with the realized injection measured per prompt and only
     the unprompted remainder scored.

  2. **Attack family zero is a positive control** — Phase 14's taught-template direct question, a
     known-extractable target at 0.4921. If it does not reproduce, the harness is declared broken
     and **no privacy statement is admissible**; this is what converts "our attacks found nothing"
     from unfalsifiable into testable (ATK-03).

  3. A **no-adapter negative control** runs at the *same* attack budget, prompts, seeds, `forbid_ids`
     and `stop_ids`, and every ASR@{1,4,16,64} plus the cumulative curve is reported adapter-on vs
     adapter-off, paired at the question level, with its denominator and bound — fact-level (n=8)
     cluster resampling descriptive, Wilson labelled as the independence-assuming width, `3/n` at
     zero successes, no bare `0%` (ATK-02, STAT-01, STAT-02, STAT-04, STAT-06).

  4. Every zero-extraction target records its **teacher-forced NLL**, so "the attack was weak" (low
     NLL, zero extraction) is separable from "the fact is genuinely absent" (high NLL) — required
     given a tokenizer that forbids 7,645 of 8,192 ids at sampling and can depress an extraction
     rate for reasons unrelated to privacy — and the verdict is returned by the committed
     `null_result_is_admissible()`, which forces **INCONCLUSIVE** unless the positive control
     passed, the budget was actually spent, the base arm was measured at the same budget, and every
     zero carries an NLL. All verdict templates, INCONCLUSIVE included, are committed before the run
     (ATK-04, ATK-05, STAT-05).

  5. README and `docs/REPORT.md` state the toggle as **availability, not authorization**, in one
     committed sentence reused verbatim (demo UI copy included, since that is a published claim),
     landed as a **dated continuation** rather than an in-place edit of the shipped v2.0 text.
     Threats-to-validity records that a low extraction rate may be a **LoRA property rather than a
     PersonaCore achievement** (ATK-06).

**Plans**: TBD
**Research flag**: plan with `/gsd-plan-phase --research-phase`. The attack taxonomy and the
denominator discipline are where a wrong prior costs the most, ARCHITECTURE.md states honestly that
it did not verify its external grounding, and the research must land **before** this phase's
pre-registration commit, which is unamendable afterward

## Progress

**Execution Order:**
Phases execute in numeric order: 16 → 17 → 18
(16 first for the *instrument-fix* reason, not the cost reason — its ladder, distractor and
slot-swap arms make it ~2-3× Phase 14's scored run. 17 and 18 both inherit 16's fixed instrument;
18 depends on 17 only for optional cross-persona attacks.)

| Phase | Milestone | Plans Complete | Status | Completed |
| ----- | --------- | -------------- | ------ | --------- |
| 1. Scaffolding & Reproducible Environment | v1.0 | 3/3 | Complete | 2026-06-04 |
| 2. From-Scratch BPE Tokenizer | v1.0 | 3/3 | Complete | 2026-06-04 |
| 3. Bigram Baseline & Training Harness | v1.0 | 4/4 | Complete | 2026-06-04 |
| 4. GPT Transformer Decoder | v1.0 | 3/3 | Complete | 2026-06-05 |
| 5. TinyStories Pretraining | v1.0 | 2/2 | Complete | 2026-06-05 |
| 6. Generation & Sampling | v1.0 | 3/3 | Complete | 2026-06-06 |
| 7. Evaluation | v1.0 | 3/3 | Complete | 2026-06-09 |
| 8. Demo & Writeup | v1.0 | 8/8 | Complete | 2026-06-10 |
| 9. LoRA Core | v2.0 | 4/4 | Complete | 2026-06-11 |
| 10. EWC Core | v2.0 | 3/3 | Complete | 2026-06-12 |
| 11. Conversational Data Pipeline | v2.0 | 4/4 | Complete | 2026-07-31 |
| 12. Stage-2 Conversational Fine-Tune | v2.0 | 5/5 | Complete | 2026-08-01 |
| 13. EWC A/B No-Forgetting Experiment | v2.0 | 4/4 | Complete | 2026-08-02 |
| 14. Teach-Then-Recall Demo | v2.0 | 11/11 | Complete | 2026-08-02 |
| 15. Figures & Writeup | v2.0 | 8/8 | Complete | 2026-08-02 |
| 16. Weight-vs-Prompt Persistence Control | v3.0 | 11/11 | Complete    | 2026-08-14 |
| 17. Multi-Persona Isolation Matrix | v3.0 | 0/TBD | Pending | - |
| 18. Black-Box Adversarial Extraction Audit | v3.0 | 0/TBD | Pending | - |

**Totals:** 15 phases complete, 68 plans, 2 milestones shipped; 3 phases planned for v3.0.
