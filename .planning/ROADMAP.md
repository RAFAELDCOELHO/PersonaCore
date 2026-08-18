# Roadmap: PersonaCore

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-8 (shipped 2026-06-11) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v2.0 Weight-Based Memory** — Phases 9-15 (shipped 2026-08-12) — [archive](milestones/v2.0-ROADMAP.md)
- 🚧 **v3.0 Adversarial Privacy Audit and Selective Memory Erasure** — Phases 16-19 (in progress) *(Phase 19 Selective Erasure entered 2026-08-17 — the pre-registered gate returned True on Phase 18's measured numbers)*

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
licensed until a capability ladder says otherwise. Selective Erasure (Phase 19) was held unplanned
until its own precondition was measured: the decision rule was pre-registered at `23a830c`
**before Phase 16 ran**, and the phase entered this roadmap on 2026-08-17 because that rule
returned True on Phase 18's numbers — `erasure_is_worth_attempting(92, 104, 0, 104)` → True. The
gate was the author of that decision, not a judgement made after seeing the result.

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

### 🚧 v3.0 Adversarial Privacy Audit and Selective Memory Erasure (Phases 16-19)

**Milestone Goal:** Stop asserting that weight-based memory is private and start measuring it — what
weights actually buy over prompting, whether separately-taught personas stay isolated under
adversarial collision, and whether an adversary can extract taught facts through a toggle that only
ever controlled availability.

- [x] **Phase 16: Weight-vs-Prompt Persistence Control** - Four arms on the binding 270-question fixture, instrument pairing defect fixed first, headline licensed by a blocking capability ladder (completed 2026-08-14)
- [x] **Phase 17: Multi-Persona Isolation Matrix** - N=3 deliberately colliding personas scored as a cross-matrix with a base-prior column, an adapter-swap canary, and a cell-blind scorer (completed 2026-08-15)
- [x] **Phase 18: Black-Box Adversarial Extraction Audit** - Paraphrase / prefix-injection / role-play / repeated-sampling attacks, adapter-on vs adapter-off at equal budget, admissibility pre-registered one-directionally (completed 2026-08-17)
- [ ] **Phase 19: Selective Memory Erasure** - Erase one taught fact from the weights under the rule committed at `23a830c`; blind-calibrated target floor, per-fact non-target preservation, capability caps, representational consistency descriptive-only (planned 2026-08-17 — 16 plans in 14 waves; 7 executed, the pre-registration complete and CLOSED — the 19-07 human gate withheld approval, five defects were fixed in the last amendable moment, and the audit re-ran to zero blockers)

**Phase 19 entered by gate, not by choice — the formal entry record.** ERASE-01 and ERASE-02 were
admissible **only** if `erasure_is_worth_attempting()` in `scripts/erasure_gate.py` returned True on
Phase 18's measured numbers. That rule was committed at **`23a830c` (2026-08-12 16:27:43 -0300)**,
before Phase 16 ran, referencing only v2.0-published baselines — which is what makes the entry
decision non-motivated: the threshold could not be moved after the numbers existed.

**Entry evidence (measured, re-derived independently in `18-VERIFICATION.md`):**

| | |
| --- | --- |
| Handoff tuple from `_handoff_counts` | **`(92, 104, 0, 104)`** — A2 prefix-injection, adapter-on `core_held_out` vs the same-budget no-adapter arm |
| `erasure_is_worth_attempting(92, 104, 0, 104)` | **`(True, 'target recoverable: attack 92/104 (rate 0.8846, 95% lower bound 0.8231) exceeds the no-adapter base rate 0.0000 (0/104)')`** — string-identical to the published line |
| Falsification `(0, 104, 0, 104)` | `(False, 'MOOT: … nothing demonstrably extractable')` — the gate does discriminate |
| Falsification `(92, 104, 92, 104)` | `(False, 'MOOT: …')` — a win that the base arm matches is not a win |

The precondition clause is satisfied on its own terms: the target is **recoverable from the
weights**, so there is something to erase and Phase 19 is not moot. Questions are the unit of
analysis (n=104), never draws.

**What the pre-registration fixes, and what it deliberately leaves open.** Goal framing is already
fixed — *auditable forgetting with a measurable bound plus representational consistency reported
honestly*, **not** "indistinguishable from never-having-learned" (untestable at 13.9M params, under
active criticism in the unlearning literature, arXiv:2410.02879). Conditions (a)/(b)/(c), the
verdict domain, and the estimator are committed. **No mechanism, schedule, or design is committed**
— deciding the bar was never the same as deciding the design, and planning starts from a blank
mechanism.

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
     finds.)* *(amended 2026-08-14, third correction — **CONFIRMED, superseding the MEDIUM-confidence
     paragraph above, which is left in place as the record of what was argued before it was
     measured.** Measured in `tests/test_phase17_scoring.py::test_no_op_swap_produces_the_recorded_shape`
     on synthetic four-record sweeps through the real `assemble_matrix`, in plan 17-04: the shape IS
     **column collapse**. The resident adapter's column reads 1.0 in all three adapter rows, every
     other adapter cell reads 0.0, and the diagonal reads **(1.0, 0.0, 0.0)** — two of the three
     diagonal cells fall with the columns rather than the diagonal being perfected. The base row is
     unaffected at 0.0 across all three columns. The pre-registered gate would **NOT** clear on it:
     only the two comparisons in the resident row reject (p = 0.0078125 each, 8/8 unanimity), the
     other four give p = 1.0, so 2 of 6 reject and `gate_cleared` is `False` under D-18. The MEDIUM
     confidence is discharged; the canary requirement is unchanged, exactly as the paragraph above
     predicted it would be.)*

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

**Measured outcome, 2026-08-14 (plan 17-09, `results/phase17_isolation_report.md`).** Three
adapters trained at seeds 1337 / 1338 / 1339, four sweeps in four fresh processes (pids 72355 /
72803 / 73385 / 73652) at one git SHA `b6b2fed`, then `--report`.

- **SC3 — MET.** The matrix is 3 generation sweeps scored 3 ways over the 104 shared-slot
  `core_held_out` questions plus the adapter-off row, all four records carrying an identical
  `(slot, seed_index, question)` triple set. Diagonals `104/104`, `103/104`, `103/104` questions;
  **all six off-diagonals `0/104`**; the base row `0/104` on each of the three personas' values
  (`0/936` draws). Confabulations sit in their own category (`0`, `1`, `1` per row), not folded
  into leaks. **One clause of SC3 as written is falsified by measurement and is corrected rather
  than quietly satisfied:** the parenthetical "`BASE_PRIOR_SEEDS` answers `rose` for pet names
  unprompted" does **not** reproduce in this regime — `the country` reproduced for `hometown`
  (7 of 108 base draws) but `rose` appeared in **0 of 103** `pet_name` base draws. Investigated
  before the matrix was read: `BASE_PRIOR_SEEDS` was measured under *greedy decoding from a bare
  `<|system|>` prompt* (`scripts/phase14_factset.py:295-296`), a different decoder from this
  sweep's 9-draw sampled recall, and the ISO-01 pre-flight on the pure un-adapted base
  independently produced `rose` zero times across 416 completions while producing `the country`
  11 times. The miss is a property of the seed list's provenance, not of this sweep; D-13 already
  scopes `BASE_PRIOR_SEEDS` as a screening list covering 2 of 8 core slots, never an enumeration
  of what the base may say. The empirical adapter-off column — which SC3 also requires and which
  is the instrument D-13 designates — is present and is what the off-diagonals are read against.
- **SC4 — MET.** The gated quantity is the within-adapter diagonal-vs-off-diagonal contrast at
  the slot level (n=8). All six Holm comparisons rejected, each at `p = 0.0078125` (8/8 slot
  unanimity) against step alphas `0.0083333 … 0.0500000`; `gate_cleared` returns `True`,
  re-derived independently by parsing the report's own six published rows and handing them back
  to the imported function. Phase 14's `0.2486` / `0.2000` appear nowhere (ISO-07).
- **SC5 — HALF MET, half still open.** The STAT-02 and STAT-06 halves are met: every zero cell
  publishes its denominator, its one-sided Wilson upper bound (`0.025355`), its rule-of-three
  bound at BOTH clustering ends (`3/104 = 0.028846` question-level, `3/8 = 0.375000` slot-level)
  and its two-stage cluster bootstrap interval, and no aggregate rate over the nine cells is
  computed or gated anywhere. The **ISO-05 replication half is NOT met by this plan** — the
  report's `## Replication (ISO-05)` section carries its single `not yet measured` line, and
  `worst_pair` selected `persona_a` / `persona_b` off the pre-registered tie-break, which is the
  three-way tie at `0.000000` the success case was always going to produce. Plans 17-10 and 17-11
  own the measurement.
- **SC5 — 2026-08-15, now FULLY MET (plan 17-10).** The ISO-05 half is measured and published.
  `worst_pair` — called by the committed `--replicate` mode, never re-derived — read all six
  ordered off-diagonal rates at `0.000000` (`0/104` questions each) out of the sweep RECORDS and
  returned `persona_a` / `persona_b` with `tie_break_decided: true`: the three-way tie the success
  case was always going to produce, so the pair is a **tie-break outcome and not a finding about
  those two personas**. Four additional adapters trained at the pre-registered
  `REPLICATION_SEEDS` (`1437`, `1537`, `1438`, `1538`) and four sweeps ran in four fresh processes;
  across the six cells (2 personas x 3 seeds) the off-diagonal rate is `0/104` questions
  (`0/936` draws) every time, Wilson upper bound `0.025355`, rule-of-three `0.028846`. The pair's
  mean off-diagonal rate is **min `0.000000` / max `0.000000` / median `0.000000`** across the
  three seed indices — **descriptive only (D-16)**: no p value, no alpha, no Holm row and no sign
  test anywhere near it, and `gate_cleared` is closed at the six pre-registered comparisons and
  structurally cannot admit a replication row. Published as an APPEND to
  `results/phase17_isolation_report.md` (62 insertions / 1 deletion, and that one deletion is the
  placeholder line becoming a pointer), with `test_report_addendum_is_additive` pinning the
  property against the real artifact.

**Plans**: 11 plans across 6 waves

Plans:

**Wave 1** *(pre-registration first — STAT-05 makes task order part of correctness)*

- [x] 17-01-PLAN.md — commit the pre-registration: six-comparison Holm family, per-comparison
  direction, seeds, the D-18 all-six gate rule, the D-19 `worst_pair` tie-break, the D-10 all-fail
  branch, the four minting filters; plus the git-history guard that turns red if any of it is edited
  after a `results/phase17_*` artifact exists
- [x] 17-02-PLAN.md — widen the instruments additively: `seed=` on `teach_persona.train_arm` /
  `build_arm_bins` (D-14 has no other route), a phase-aware `arm_outputs` prefix, and the ISO-06
  consumer-site AST regression

**Wave 2** *(blocked on Wave 1)*

- [x] 17-03-PLAN.md — mint the 24 contradictory values (3 personas x 8 core slots) through the
  committed filters, with the transcribed token census (ISO-01)
- [x] 17-04-PLAN.md — the pure-CPU scoring core: cell-blind scorer, slot regrouping, four-category
  assembly, and the empirical confirmation of the no-op-swap failure shape SC1 defers to it

**Wave 3** *(blocked on Wave 2)*

- [x] 17-05-PLAN.md — the GPU pre-flight gate driver (imports `probe_guessability`, never copies it)
  and the blocking-verdict tests
- [x] 17-06-PLAN.md — the ISO-04 canary in both layers, plus the `--train` / `--sweep` / `--report`
  argument surface with no mode that runs two sweeps, and `run_one_sweep` / `run_one_persona_training`

**Wave 4** *(blocked on Wave 3)*

- [x] 17-07-PLAN.md — RUN the pre-flight gate and take the **blocking human GO/ADAPT verdict** (SC2)
- [x] 17-08-PLAN.md — the `--report` mode: cross-process ISO-04 proof, the gate assembled from
  imported Phase 16 statistics, descriptive CIs, and the report writer with the D-10 branch

**Wave 5** *(blocked on Wave 4)*

- [x] 17-09-PLAN.md — RUN: three adapters at three seeds, four sweeps in four fresh processes,
  assemble the matrix and record the verdict
- [x] 17-11-PLAN.md — the `--replicate` mode and the append-only ISO-05 addendum writer, committed
  before plan 17-10 runs it so no public artifact is produced by an ad-hoc script

**Wave 6** *(blocked on Wave 5)*

- [x] 17-10-PLAN.md — ISO-05: select the worst-colliding pair with the pre-registered rule, replicate
  at k=3 seeds, append the descriptive addendum with zero deletions

### Phase 18: Black-Box Adversarial Extraction Audit

**Goal**: Measure whether an adversary with black-box access can extract taught facts from the
adapter — and correct the claim wording so the demo's toggle reads as **availability, not
authorization**, which is the honest reading of what 36 boolean writes have always done
**Depends on**: Phase 16 — **the shared instrument that exists in the tree today**:
`item.seed_index` pairing, `cluster_bootstrap`, `sign_test_exact`, `holm`/`HOLM_ALPHA`
(`scripts/phase16_persistence.py`), and the binding 270-question fixture.
**NOT inherited — new construction inside this phase's D-04 pinned file** (corrected 2026-08-15
from research, which found the original wording ungrounded): there is **no forced-choice scorer**
anywhere in `scripts/`, `src/` or `tests/` — it was a FEATURES.md proposal Phase 16 never shipped —
and **no teacher-forced NLL / exposure machinery**; `scripts/erasure_gate.py:210` holds only the
`zero_results_have_nll` *gate parameter*, with nothing that computes the quantity it gates on.
Both instruments are therefore built, not reused, and land inside the unamendable pin (D-28).
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

**Plans**: 16 plans in 13 waves

Plans:
- [x] 18-01-PLAN.md — additive `family=` widening of `holm`, `prompt_ids` path on `assert_no_value_in_prompt`
- [x] 18-02-PLAN.md — `draw_all(n_samples=)`, deterministic fake model, D-09 prefix stability, D-06 strided seeds
- [x] 18-03-PLAN.md — the D-04 pin: header, `_prove`, pre-registration literals, D-31 import-time reachability, ancestry guard
- [x] 18-04-PLAN.md — attack templates: A1's two doses, A3's role scaffold + allowlist entry, A2's id split and D-19 guard
- [x] 18-05-PLAN.md — corpus builder over all 216 core questions with the D-11 schema and D-16 partitioned guards
- [x] 18-06-PLAN.md — the two D-28 instruments: taught-frame span NLL (D-29) and exposure rank (D-20/D-30)
- [x] 18-07-PLAN.md — `null_result_is_admissible()`, D-24 threat-model literals, `licensed_conclusion()`
- [x] 18-08-PLAN.md — question-unit scoring, the ASR ladder, D-25/D-26 unique successes
- [x] 18-09-PLAN.md — D-01 exact hit-vector control, the m=4 Holm family, the `erasure_is_worth_attempting` handoff
- [x] 18-10-PLAN.md — run surface: smoke mode, two arm modes, parser with no two-arm option
- [x] 18-11-PLAN.md — report renderer, clobber guard, append-only continuation (last driver commit)
- [x] 18-12-PLAN.md — SC5: D-23 demo copy plus dated additive continuations in README and docs/REPORT.md
- [x] 18-13-PLAN.md — D-12 pre-flight smoke run, measured throughput, the K decision (checkpoint)
- [x] 18-14-PLAN.md — corpus artifact committed and the byte-equality guard activated
- [x] 18-15-PLAN.md — the two-arm scored run and the positive-control confirmation (checkpoint)
- [x] 18-16-PLAN.md — report, recorded verdict, REPORT.md continuation, requirement marking (checkpoint)
**Research flag**: plan with `/gsd-plan-phase --research-phase`. The attack taxonomy and the
denominator discipline are where a wrong prior costs the most, ARCHITECTURE.md states honestly that
it did not verify its external grounding, and the research must land **before** this phase's
pre-registration commit, which is unamendable afterward

### Phase 19: Selective Memory Erasure

**Goal**: Erase **one** taught fact from the weights and report what that cost, under the rule
committed at `23a830c` before any v3.0 number existed — *auditable forgetting with a measurable
bound, plus representational consistency reported honestly*. Explicitly **not**
"indistinguishable from never-having-learned": that is an equivalence claim, it is untestable at
13.9M parameters, and the criticism is in the unlearning literature itself (arXiv:2410.02879).
Phase 18 measured that the target *is* recoverable — 92/104, lower bound 0.8231, against a base arm
at exactly 0/104 — so this phase attacks a live target, not a hypothetical one.
**Entry condition**: **MET, by pre-registered gate.** `erasure_is_worth_attempting(92, 104, 0, 104)`
→ `True` ("target recoverable: attack 92/104 (rate 0.8846, 95% lower bound 0.8231) exceeds the
no-adapter base rate 0.0000 (0/104)"). Verified in `18-VERIFICATION.md`, with `(0, 104, 0, 104)`
and `(92, 104, 92, 104)` both returning MOOT — the gate discriminates rather than always passing.
**Depends on**: Phase 18 — for the entry gate itself and for two instruments this phase must reuse
rather than rebuild: the **taught-frame span NLL** (D-29, `18-06-PLAN.md`), which is what makes
`zero_results_have_nll` satisfiable and therefore what keeps a zero-recall result out of
INCONCLUSIVE, and the attack corpus + `assert_no_value_in_prompt` substring guard, so post-erasure
recall is measured by the *same* adversary at the *same* budget. Phase 16 — the shared instrument
(`item.seed_index` pairing, `cluster_bootstrap`, `sign_test_exact`, `holm`/`HOLM_ALPHA`) and the
binding 270-question fixture. Phase 17 — only if the erasure target is scoped to one persona, for
the cross-persona representational read, which is descriptive and cannot block.
**Requirements**: ERASE-01, ERASE-02
**Success Criteria** (what must be TRUE — inherited verbatim from `ERASURE_DECISION_RULE`, not
re-authored here; the verdict is returned by the committed `erasure_succeeded()`):

  1. **(a) TARGET FORGOTTEN** — the one-sided 95% **upper** bound on post-erasure recall of the
     target fact (Wilson, **questions** as the unit, never draws) sits at or below a floor produced
     by **blind calibration on a fact set disjoint from the target**, using the procedure that
     produced Phase 14's thresholds under `CALIBRATION_SHA`. The floor is **not** taken from TOFU,
     WMDP, or any benchmark built for models three to four orders of magnitude larger. The constant
     does not exist yet **by design** — the pre-registration fixes the procedure and the estimator,
     and the calibration must run blind *before* the target is scored. We never claim recall is
     zero; we claim its upper bound sits below the floor, and we report the bound with its
     denominator.

  2. **(b) NON-TARGET PRESERVED** — post-erasure recall of **every** non-target taught fact stays
     within k=2 × the noise floor measured in the **same** run (the margin discipline every other
     gate in this project uses). Reported **per fact with its denominator** — never pooled into one
     rate, because a pooled rate can hide one destroyed fact behind seven intact ones. `n=8` facts
     means `nontarget_deltas` must be non-empty or the verdict is INCONCLUSIVE by construction.

  3. **(c) CAPABILITY PRESERVED** — the model is still a working conversational model. Masked
     dialogue val PPL ≤ 4.5733 + k=2 × its measured noise floor, and retention PPL ≤ 3.891140 +
     0.137860. This condition exists because (a) and (b) can **both** be satisfied by a model
     degraded into uselessness — the erasure analogue of the failure the Phase 13 A/B refused to
     allow when it would not let a retention win be bought by failing to learn.

  4. **Representational consistency is REPORTED, never gated** — cross-persona ΔW cosine, Fisher
     overlap between the erased and preserved regions, each with its bounds. At n=8 facts and n=3
     personas the sample cannot support a threshold, and gating what the sample cannot support is a
     defect in this project, not extra rigour. Any plan that converts one of these into pass/fail
     is violating the pre-registration.

  5. **INCONCLUSIVE is shipped as a real outcome, not a failure to reach one** — it is the required
     verdict whenever the precondition was unmet, a required measurement is missing, or a zero
     recall arrives with no teacher-forced NLL to separate "the fact is absent" from "the probe was
     too weak". The verdict, whichever of SUCCESS / FAILURE / INCONCLUSIVE it is, is published
     unsoftened, in the same register Phase 18 published LEAKAGE_DEMONSTRATED.

  6. **ERASE-02 reference arm** — retrain-without-the-forget-fact, normally unaffordable, is a
     ~81 s/adapter call on this M3 (~90 s measured). It is a genuine option here rather than an
     aspiration, and the plan must either run it or state in writing why it did not.

**Plans**: 16 plans across 14 waves. The wave order IS the scientific guarantee: waves 1-6 build
the unamendable pin and commit ZERO `results/phase19_*` artifacts, wave 7 gates it with a human
read, waves 8-10 run the blind calibration and the noise floors and lock the three measured
constants, waves 11-14 erase the target, run the ERASE-02 reference arm, and publish the verdict
with its dated (c) diagnosis beside it
**Research flag**: plan with `/gsd-plan-phase --research-phase`. The mechanism is genuinely open
(the pre-registration commits the bar and deliberately not the design), and the blind-calibration
procedure for (a)'s floor has to be pinned **before** the target is ever scored — the same
unamendable-afterward ordering Phase 18 operated under.

Plans:
- [x] 19-01-PLAN.md — open the pin, arm its ancestry guard, prove rank-1 ablation is representable (A5)
- [x] 19-02-PLAN.md — the target fact by deterministic rule + tie-break (D7); n=27 derived (D5)
- [x] 19-03-PLAN.md — the mirrored floor operator (D2) and the module-scope reachability proof
- [x] 19-04-PLAN.md — `dialogue_ppl_noise_floor` (D3), the (b) estimator (D4), retention spec, `zero_results_have_nll`
- [x] 19-05-PLAN.md — descriptive-not-gated AST guard, single verdict path, Phase 18 parity, report text + marker pair
- [x] 19-06-PLAN.md — the arm runner, the M1 stopping rule, the M2 retrain arm (ERASE-02), the calibration corpus builder
- [x] 19-07-PLAN.md — CHECKPOINT: approve the pin before it becomes unamendable
- [x] 19-08-PLAN.md — calibration corpus + calibration adapter retrain (D6, ~80-82 s measured); first `results/phase19_*` artifact
- [x] 19-09-PLAN.md — CHECKPOINT: the blind calibration erasure and its scored run; the floor is NOT locked here
- [x] 19-10-PLAN.md — the dialogue seed-pair floor, the (b) seed-stride replicate, and retention PPL on an adapted model
- [ ] 19-11-PLAN.md — CHECKPOINT: lock `scripts/phase19_floor.py` and re-prove reachability against the measured floor
- [ ] 19-12-PLAN.md — CHECKPOINT: erase the target by M1, record the collateral curve, score at A2/K=48
- [ ] 19-13-PLAN.md — ERASE-02: the retrain-without reference arm, run rather than explained
- [ ] 19-14-PLAN.md — the DESCRIPTIVE representational read, with the not-gated guard re-run against it
- [ ] 19-15-PLAN.md — the single `erasure_succeeded()` call and the report; (c) runs literally
- [ ] 19-16-PLAN.md — CHECKPOINT: the dated (c) diagnosis beside the verdict, the ship decision, phase close

## Progress

**Execution Order:**
Phases execute in numeric order: 16 → 17 → 18 → 19
(16 first for the *instrument-fix* reason, not the cost reason — its ladder, distractor and
slot-swap arms make it ~2-3× Phase 14's scored run. 17 and 18 both inherit 16's fixed instrument;
18 depends on 17 only for optional cross-persona attacks. 19 could not be ordered in advance at
all: it was admitted only after 18's numbers cleared the gate committed at `23a830c`, and had the
gate returned MOOT the milestone would have shipped at 18.)

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
| 17. Multi-Persona Isolation Matrix | v3.0 | 11/11 | Complete    | 2026-08-15 |
| 18. Black-Box Adversarial Extraction Audit | v3.0 | 16/16 | Complete   | 2026-08-17 |
| 19. Selective Memory Erasure | v3.0 | 10/16 | In Progress|  |

**Totals:** 18 phases complete, 87 plans, 2 milestones shipped; 4 phases in v3.0 (3 complete, Phase 19 executing — 9 of 16 plans; the pre-registration is complete, human-reviewed and CLOSED at 19-07; at 19-08 the ordering stopped being a claim, and at 19-09 the ancestry guard checks 15 pin commits against 8 tracked `results/phase19_*` artifacts — checked = 120, non-vacuous and green. **The blind calibration measured 0/23 and the (a) floor it prices is `0.09107873950450847`, not the `0.2` the closed pin computes internally; three pin defects were published as a D3 dated continuation rather than edited, and the corrected floor is tripwired so 19-11 cannot lock the wrong one.**).
