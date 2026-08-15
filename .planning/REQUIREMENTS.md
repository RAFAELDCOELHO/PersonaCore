# Requirements: v3.0 Adversarial Privacy Audit and Selective Memory Erasure

Requirements for this milestone. Each maps to roadmap phases.

**Milestone thesis.** v2.0 demonstrated that personalization lives in the weights. v3.0 stops
*asserting* that this is private and starts **measuring** it — what weights actually buy over
prompting, whether separately-taught personas stay isolated under adversarial collision, and
whether an adversary can extract taught facts through a toggle that only ever controlled
availability.

**The finding that shaped this scope.** Phase 14 already ran the weight-vs-prompt comparison as a
validity control: `run_fairness_control` placed each fact inside the `<|system|>` persona span and
the un-adapted base scored **1/1944 = 0.0005** (`results/phase14_recall_report.md:378`). At 13.9M
parameters prompt-stuffing does not trivially win — it is at the floor. A naive "weights beat
prompting ~1000x" headline would therefore be measuring a **capability deficit, not weight
memory**, and would be refuted by a number already committed in this repository. Phase 16 is
scoped accordingly.

---

## Cross-Cutting Statistical Discipline

Applies to every phase. Listed first because getting these wrong invalidates every number below.

- [x] **STAT-01**: Every reported rate declares the **question** as its unit of analysis, never the
  draw. Phase 14's `496/1008` was 112 questions x 9 draws over 10 facts; treating clustered data as
  1008 i.i.d. Bernoulli trials yields intervals far too narrow. Bootstrap resampling resamples
  *questions*.
- [x] **STAT-02**: Every proportion is reported with a **confidence bound and its denominator** —
  Wilson interval, plus the rule-of-three `3/n` shown alongside whenever successes are zero. No
  bare `0%` appears in any committed report or figure.
- [x] **STAT-03**: Multiple comparisons across the isolation matrix use **Holm** step-down, not
  Benjamini-Hochberg: off-diagonal cells share adapters row-wise and question sets column-wise, so
  BH's independence/PRDS assumption fails while Holm is valid under arbitrary dependence.
- [x] **STAT-04**: **Zero new runtime dependencies.** `pyproject.toml` is byte-identical at v3.0
  close. The ~50-60 lines of new statistics are hand-rolled in the established style; this project
  has declined scipy in committed code twice (`continual/fisher.py`, `scripts/phase15_stats.py`)
  and taking it now — in a milestone whose entire output is trust in a measurement — would retcon
  both.
- [x] **STAT-05**: Every gate is a **module-level literal in a committed driver, pushed before the
  run it judges**, and every verdict is computed by *importing* those constants rather than
  retyping them in prose. Carried forward from v2.0 unchanged.
- [x] **STAT-06**: Nothing is gated that the sample size cannot support. Anything resting on n=8
  facts or n=3 personas as its unit is **descriptive**, reported in full with bounds, and never
  converted into pass/fail.

## Weight-vs-Prompt Persistence Control (Phase 16)

- [x] **PERS-01**: A **blocking in-context capability ladder** runs and is recorded *before* any
  comparison is scored — establishing what the base model can do with a fact in its context at
  increasing distance. Phase 16's framing depends on its outcome, so it cannot be discovered
  mid-phase.
- [x] **PERS-02**: The paired weight-vs-prompt comparison scores the **same questions under both
  conditions** — fact in the context window vs adapter-only with an empty prompt — with arms paired
  by `seed_index`, and reports the raw floor honestly rather than as a victory.
- [x] **PERS-03**: **Persistence under context pressure** is measured: truncation at
  `block_size=256`, **dilution within the persona span**, and adversarial overwrite. This is the
  axis where the weight arm is invariant *by proof* (`run_bit_identity_control`, max |diff| 0.0)
  and the prompt arm is not, and it is the phase's load-bearing result.
  *(Amended 2026-08-12: was "dilution across turns". Falsified by measurement during Phase 16
  planning — `build_recall_prompt` (`src/personacore/dialogue/serialize.py:92`) passes exactly one
  turn to `encode_dialogue`, so no turns axis exists on the recall path; and `cap_persona` (`:115`)
  is never called by it — only by `scripts/make_transcripts.py:134` and
  `scripts/prepare_dialog_corpus.py:104` — so `PERSONA_CAP = 140` does not constrain the span
  either. Dilution therefore happens inside the persona span, which reaches the 448-token target
  directly. The measured quantity is unchanged; only the mechanism wording was wrong.)*
- [x] **PERS-04**: An **embedding / cosine-similarity baseline** is measured as a fourth arm over
  the existing fact set — a simple comparison, explicitly **NOT a RAG system**: no formal index, no
  re-ranking, no chunking. It exists to place a retrieval-flavoured reference point next to the
  prompt and weight arms, not to build retrieval.
- [x] **PERS-05**: The `enumerate(questions)` seeding defect in `run_fairness_control` is fixed to
  use `item.seed_index` — the same CR-01 pairing defect `stamp_seed_indices` was written to close,
  left unfixed in that path because Phase 14 never compared it against anything. Phase 16 does, so
  unpaired arms would silently invalidate the comparison past the first arm boundary.
- [x] **PERS-06**: The AST guard pinning `persona=` to exactly one caller
  (`tests/test_phase14_scoring.py:425`) is **widened deliberately and visibly**, never deleted, and
  gains a logical twin `assert_value_in_prompt` so every `draw_all` caller asserts something and no
  path has a skip mode. Deleting the guard is precisely the "declared invariant silently becomes
  false" failure this project named as its most recurring defect.

## Multi-Persona Isolation Matrix (Phase 17)

- [x] **ISO-01**: An **adversarial persona generator** produces **N=3** personas with colliding
  names and *contradictory values in the same slot*. Personas that differ in easy ways make
  isolation look perfect for trivial reasons — the single most likely way this phase produces a
  worthless green result.
- [x] **ISO-02**: The isolation matrix scores **shared-slot questions** against every persona's
  value. Scoring persona *j*'s own questions against adapter *i* makes the off-diagonal ~0 by
  construction, which merely re-proves `0/2430` at N^2 the cost. This also collapses cost from N^2
  sweeps to **N sweeps scored N ways**.
- [x] **ISO-03**: The matrix carries an explicit **adapter-off control column**, so an off-diagonal
  hit is distinguishable from the base model's own prior (`BASE_PRIOR_SEEDS` records this base
  answering `rose` for pet names unprompted).
- [x] **ISO-04**: An **adapter-swap canary** asserts a `lora_B` tensor actually changed on every
  swap. All personas share identical `lora_` key sets, so a silently failed swap is a full no-op
  that produces the most flattering possible wrong answer: a perfect diagonal and zero leakage.
- [x] **ISO-05**: The **worst-colliding pair is replicated across seeds**, so seed variance is not
  mistaken for interference.
- [x] **ISO-06**: Audit item **W1 is fixed before any adapter trains**: runtime consumers inject
  with `LoRAConfig(**artifact["lora_config"])` rather than `LoRAConfig()` defaults. Shape audits
  catch `r` drift but **not `alpha`** — no shape change — so with N adapters a divergent alpha
  applies the delta at the wrong magnitude, silently. Two lines, and Phase 17 multiplies the call
  sites from 2 to N.
- [x] **ISO-07**: The matrix is **not gated against Phase 14's 0.2486 / 0.2000 thresholds** — those
  were derived on `CALIBRATION_POOL`, so reusing that pool as a persona makes the gate circular.
  The gated quantity is the within-run diagonal-vs-off-diagonal contrast, which needs no external
  threshold.

## Black-Box Adversarial Extraction Audit (Phase 18)

- [ ] **ATK-01**: Attack families are constructed **programmatically from committed templates** —
  paraphrase, prefix injection, role-play framing, and repeated sampling — with no external API and
  no hosted model anywhere in the pipeline.
- [ ] **ATK-02**: A **no-adapter negative control** runs at the *same attack budget*. Without it a
  "successful extraction" is indistinguishable from the base guessing a common name.
- [ ] **ATK-03**: A **positive control runs as attack family zero** — Phase 14's taught-template
  direct question, a known-extractable target at 0.4921. If it does not reproduce, the harness is
  broken and no privacy statement is admissible. This converts "our attacks found nothing" from
  unfalsifiable into testable.
- [ ] **ATK-04**: Every zero-extraction target records its **teacher-forced NLL**. Low NLL plus zero
  extraction means the attack was weak; high NLL means the fact is genuinely absent. Without it
  every zero is uninterpretable — especially given a tokenizer that forbids 7,645 of 8,192 ids at
  sampling and can silently depress an extraction rate for reasons unrelated to privacy.
- [ ] **ATK-05**: **Admissibility is pre-registered one-directionally.** A committed
  `null_result_is_admissible()` forces `INCONCLUSIVE` unless the positive control passed, the
  budget was actually spent, the base arm was measured at the same budget, and every zero carries
  an NLL. All verdict templates are committed before the run, because "we found leakage" and "we
  found none" are both publishable but need different pre-commitments.
- [ ] **ATK-06**: The demo's adapter toggle is documented as **availability, not authorization** —
  the honest reading of what that switch has always done — and the claim wording in README and
  `docs/REPORT.md` is corrected to match.

## Pre-Registration (landed before this milestone's first run)

- [x] **PREREG-01**: `scripts/erasure_gate.py` committed at `23a830c` (2026-08-12 16:27:43), before
  Phase 16 runs. Holds `ERASURE_DECISION_RULE` — precondition, plus (a) target-forgotten as a Wilson
  **upper bound**, (b) non-target preserved within k=2, (c) capability preserved against the
  published v2.0 baselines 4.5733 / 3.891140 — with SUCCESS/FAILURE/INCONCLUSIVE verdicts and an
  explicit descriptive-not-gated clause for representational consistency. Stdlib only, no torch, no
  numpy.
- [x] **PREREG-02**: A CPU-only test asserts the `erasure_gate.py` commit **precedes** every v3.0
  results artifact, so the ordering is structurally enforced rather than merely true today.

---

## Future Requirements

Deferred — revisited when the numbers that gate them exist.

- **ERASE-01**: Selective erasure of a taught fact from the weights (Phase 19+). Enters the roadmap
  **only** if `erasure_is_worth_attempting()` returns True on Phase 18's measured numbers. Goal
  framing is fixed already: *auditable forgetting with a measurable bound plus representational
  consistency reported honestly* — **not** "indistinguishable from never-having-learned", which is
  untestable at this scale and is under active criticism in the unlearning literature
  (arXiv:2410.02879). No mechanism, schedule, or design is committed.
- **ERASE-02**: A TOFU-style retrain-without-the-forget-fact reference. Normally unaffordable;
  measured at ~81 s per adapter on this M3, it becomes a ~90-second call — so it is a genuine option
  for Phase 19 rather than an aspiration.

## Out of Scope

- **Frozen tokenizer / retrain** — a separate decision needing its own conversation, given the cost
  of invalidating every published checkpoint and number. Bundling it into a privacy milestone would
  confound both.
- **Membership-inference attacks** — an anti-feature here, not a gap. With n=8 members the
  measurement is uninformative, and reported MIA successes in the literature have been traced to
  member/non-member distribution shift. Shokri et al. (2017) is cited to explain *why MIA is not
  used*, never as a method.
- **A full RAG system** — PERS-04 is embedding + cosine over the existing fact set only. No index,
  no re-ranking, no chunking. Building retrieval would be a different project.
- **Thresholds imported from the unlearning literature** — TOFU and WMDP target models three to four
  orders of magnitude larger. Every floor here is either already published by this project or
  produced by blind calibration at this scale.
- **New runtime dependencies** — see STAT-04.
- **Any change to `phase15_stats.py`'s pre-registration block** — it is a v2.0 audit trail.

---

## Traceability

| ID | Phase | Status |
|----|-------|--------|
| STAT-01 | 16, 17, 18 | Complete |
| STAT-02 | 16, 17, 18 | Complete |
| STAT-03 | 17 | Complete |
| STAT-04 | 16, 17, 18 | Complete |
| STAT-05 | 16, 17, 18 | Complete |
| STAT-06 | 16, 17, 18 | Complete |
| PERS-01 | 16 | Complete |
| PERS-02 | 16 | Complete |
| PERS-03 | 16 | Complete |
| PERS-04 | 16 | Complete |
| PERS-05 | 16 | Complete |
| PERS-06 | 16 | Complete |
| ISO-01 | 17 | Complete |
| ISO-02 | 17 | Complete |
| ISO-03 | 17 | Complete |
| ISO-04 | 17 | Complete |
| ISO-05 | 17 | Complete |
| ISO-06 | 17 | Complete |
| ISO-07 | 17 | Complete |
| ATK-01 | 18 | Pending |
| ATK-02 | 18 | Pending |
| ATK-03 | 18 | Pending |
| ATK-04 | 18 | Pending |
| ATK-05 | 18 | Pending |
| ATK-06 | 18 | Pending |
| PREREG-01 | (pre-milestone) | Complete — `23a830c`, 2026-08-12 |
| PREREG-02 | 16 | Complete |
| ERASE-01 | 19+ (deferred) | Deferred — enters the roadmap only if `erasure_is_worth_attempting()` returns True on Phase 18's numbers |
| ERASE-02 | 19+ (deferred) | Deferred — same gate |

**Coverage (roadmapped 2026-08-12):** 26/26 in-scope v3.0 requirements are mapped to Phases 16-18;
0 orphans. PREREG-01 is complete pre-milestone (`23a830c`). ERASE-01/02 are deliberately unmapped —
Phase 19 does not exist in the roadmap and is created only by the pre-registered gate, never by
planning. STAT-01..06 are cross-cutting by construction and are therefore satisfied *per phase*
rather than in exactly one; the phase column above is the authoritative allocation and
`ROADMAP.md` reproduces it unchanged.
