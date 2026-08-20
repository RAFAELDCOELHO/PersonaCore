# Feature Research

**Domain:** ML privacy auditing / model memorization measurement, applied to a 13.9M-param
from-scratch decoder with from-scratch LoRA adapters, on-device (M3/MPS), zero budget
**Researched:** 2026-08-12
**Confidence:** MEDIUM-HIGH (literature protocols HIGH — established, named, cited; scale-specific
recommendations MEDIUM — derived by reasoning from PersonaCore's own v2.0 measurements, which
are the only data at this scale)

---

## 0. The finding that reframes the whole milestone

**Read this before scoping anything else.**

Standard ML-privacy framing assumes prompting is the strong baseline and weights are the
suspicious novelty. **At this project's scale the measurement already exists and it says the
opposite.** Phase 14's question-fairness control (`run_fairness_control`, D-11.1) put each fact's
own first-person statement *inside the `<|system|>` persona span* — the exact format the model saw
5.26M tokens of in stage 2 — and the base scored **1/1944 = 0.0005** across 216 questions. The
adapter-only arm scored 0.4921 / 0.3483.

So a naive Phase 16 that just runs "in-context vs adapter" on free-generation success rates will
produce a ~1000× headline that means **nothing about weight-based memory**. It measures a 13.9M
model's inability to do in-context retrieval — a capability deficit, not a property of the weights.
The v2.0 report already says exactly this: *"the base's in-context extraction is close to
non-functional independent of whether memory is present."* Shipping that comparison as a headline
would be the single most damaging cargo-cult result available to this milestone.

Three consequences that propagate into all three phases:

1. **Free-generation success rate is a low-power instrument at this scale.** Every phase that needs
   a *gate* should use a rank / forced-choice / likelihood measure, which has an exact chance
   baseline and orders of magnitude more statistical power per unit of compute. Free generation
   stays as the *demonstration* instrument (it is what a reviewer can read in a transcript) and as
   the honest headline, but it is not where the falsifiable claim should live.
2. **Phase 16's interesting axis is not "who wins at distance 0."** It is **persistence under
   context pressure** — truncation, dilution across turns, adversarial overwrite — where the weight
   arm is invariant *by construction* (identical prompt ids ⇒ bit-identical logits, already proven
   in `run_bit_identity_control` at max |diff| 0.0) and the prompt arm is not. That is a real,
   non-trivial, cheap-to-measure asymmetry.
3. **Phase 18's claimable direction must be pre-registered.** A weak attacker that *succeeds* is a
   valid existence proof of leakage. A weak attacker that *fails* proves nothing about safety. State
   which conclusion the phase is allowed to draw before running it.

---

## Feature Landscape

### Table Stakes (a reviewer would call the result invalid without these)

#### Phase 16 — Weight-vs-Prompt Measured Control

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **WVP-1 · Paired design: identical questions, identical seeds, both arms** | Unpaired arms cannot attribute a difference to the condition. Phase 14 already established the house pattern (same 270 prompts, same per-question seeds, only `enabled` flipped) | LOW (reuse `question_seed`, `draw_all`) | Reuse `phase14_recall.py` seeding verbatim. Any new arm must use the same `SEED + i + s` derivation or the arms stop being paired |
| **WVP-2 · Capability-floor / positive control for the in-context arm** | Without it, "prompt loses" is unfalsifiable — you cannot distinguish "weights are better" from "this base cannot read its own context." Standard name: **oracle / ceiling condition** | MEDIUM (design + 1 sweep) | Simplest credible ceiling: the value appears in the immediately preceding turn (distance ≈ 0, induction-copy regime). If even that fails, the honest verdict is *"the prompt arm has no working regime at 13.9M; the comparison is not measurable"* — record it and stop, per house discipline |
| **WVP-3 · Rank / forced-choice metric alongside the generation metric** | The 1/1944 floor makes generation-rate differences statistically dead. Forced-choice among K same-slot distractors has an **exact 1/K chance baseline** and converts a floor result into a powered one. Literature: ConflictQA-style forced choice; Secret Sharer rank | MEDIUM (new scorer, no new generation) | Distractors are free: `GATE_REJECTED_CANDIDATES`, `CALIBRATION_POOL`, `REGISTER_ARM_POOL` are already base-ignorance-gated, same slots, similar token lengths. K=4–8 per slot with no new gating work |
| **WVP-4 · Context-pressure ladder (truncation / dilution / overwrite)** | This is the axis where the two conditions genuinely differ. `block_size=256` makes truncation trivially reachable: a fact pushed past 256 tokens is *gone* from the prompt arm and untouched in the weight arm | MEDIUM (prompt construction + 3–4 sweeps) | Overwrite arm = a later turn asserting a same-slot competing value (draw from `GATE_REJECTED_CANDIDATES` — that is literally what they are). Score with the existing `find_contradictions` |
| **WVP-5 · Weight-arm invariance stated as a proof, not a measurement** | The weight arm's flatness across the ladder is *exact* (identical prompt ids ⇒ identical logits) | LOW (assert, already have `run_bit_identity_control`) | Do not report it as an empirical rate; report it as a structural invariant with a test. House style: structural enforcement beats declared invariants |
| **WVP-6 · Named threat/scope statement** | Prevents the reader from generalizing a 13.9M result to LLM-scale claims | LOW (prose + committed) | Phase 14's report opener is the template — reuse its "what these numbers are not" paragraph |

#### Phase 17 — Multi-Persona Isolation Matrix M_ij

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **ISO-1 · Shared-slot question design (the thing that makes M_ij non-trivial)** | **Critical.** If persona j's questions are about facts persona i never saw, off-diagonal ≈ 0 *by construction* and the matrix re-proves the 0/2430 control at N² the cost. The matrix is only well-posed when the **question is shared** and the personas differ in the *value* they assign to the same slot | MEDIUM (design; `slot` field already exists on `Fact`) | M_ij := rate at which adapter *i*, asked a shared-slot question, emits persona *j*'s value. Diagonal = own-value rate, off-diagonal = foreign-value rate. `SLOT_QUESTION_BANK` already keys on slot, so the shared question set is free |
| **ISO-2 · Adversarial collision design, pre-registered** | "3 random personas" measures nothing. Interference in the literature is driven by *similarity*; a persona set must be constructed to maximize it | MEDIUM | See "What makes two personas maximally collision-prone" below. Four collision axes, each pre-registrable as a design constraint with a measurable definition |
| **ISO-3 · Base-ignorance gate on every new value** | A value the base already knows inflates every cell. `phase14_factset_gate.py` (FACTSET_GATE_SHA `446afab3…`) exists and every locked/rejected/calibration/arm value already passed it at 0/16 | LOW to re-run, MEDIUM if new values are needed | **Big cost saver:** the 8 core "composition trims" in `GATE_REJECTED_CANDIDATES` were rejected *only* by the one-fact-per-slot rule and already passed the gate — they are a ready-made, already-gated **Persona B with perfect slot collision**. `CALIBRATION_POOL` (10) and `REGISTER_ARM_POOL` (6) supply most of C and D. Only `street` and `house_number` fall short at N=4 |
| **ISO-4 · Adapter-off negative control on the same matrix** | Every cell needs its null. Without it a nonzero off-diagonal could be a base prior, not leakage | LOW (1 extra sweep, `enabled=False`) | Expected 0/N by the Phase-14 precedent, which is exactly why it is cheap and exactly why it must still be run |
| **ISO-5 · Per-persona collateral-collapse report** | v2.0's named limitation (+27.16% masked-dialogue PPL) is *per adapter*. N adapters means N collateral numbers, and a persona whose adapter wrecks the base is not an isolation result | LOW — **already free** | `teach_persona.train_arm` already prints `adapter OFF x / ON y (+z%)` at the end of every arm. Just capture it |
| **ISO-6 · Diagonal-vs-off-diagonal as the gated statistic, not per-cell ordering** | N=3–4 personas is n=3–4. Per-cell comparisons are not gateable; the aggregate contrast is | LOW | Gate on e.g. `min(diagonal) > max(off-diagonal) + margin`, with the margin fixed from the measured never-taught reference rate. Report the full matrix descriptively |
| **ISO-7 · Fresh-process / clean-room inheritance per adapter** | Same reason as Phase 14: teaching and scoring in one process is not a recall result | LOW (already the pattern) | Each `train_arm` writes an adapter file; scoring is a separate invocation with recorded pid |

#### Phase 18 — Black-Box Adversarial Extraction Audit

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **EXT-1 · No-adapter negative control, same attacks, same seeds** | Named in the milestone brief and it is the non-negotiable of the whole extraction literature. Without it, any hit rate is unattributable | LOW (1 sweep) | Phase 14's 0/2430 is the precedent and roughly the expected value |
| **EXT-2 · Never-taught reference values ("canary references")** | The negative control tells you the *base* doesn't say it. The reference set tells you the adapter says the taught value **more than it says an equally plausible untaught value**. This is the Secret Sharer reference-set idea and it is what separates a real leakage claim from a coincidence | MEDIUM (scoring, no new generation) | References already exist and are already gated: 12 `GATE_REJECTED_CANDIDATES` + 10 `CALIBRATION_POOL` + 6 `REGISTER_ARM_POOL` = 28 same-slot, same-register, never-taught values |
| **EXT-3 · Explicit chance/guessing baseline per metric** | Extraction rate with no stated chance rate is uninterpretable. Free-generation chance = the *measured* base prior (already 0/16 per value at the factset gate); forced-choice chance = exactly 1/K | LOW | Reuse the factset gate's measured priors rather than asserting "chance ≈ 0" |
| **EXT-4 · Pre-registered attack budget and attack families** | Reporting max-over-attacks after seeing results is multiple-comparison mining. The house pattern (module-level literals in a pushed driver) applies directly | LOW | Pre-register: family list, N samples per family, temperature/top-p, decoding budget, and the scoring predicate |
| **EXT-5 · ASR reported as a function of N, not a single number** | Attack success under repeated sampling grows monotonically with N; a single-N figure is arbitrary. Best-of-N jailbreaking established ASR(N) reporting as the norm | LOW (free — it is a cumulative statistic over draws you already take) | Report `ASR@1, @4, @16, @64` from one sweep. **Do not** fit a power-law exponent (see anti-features) |
| **EXT-6 · Stated threat model, including what is NOT covered** | The adapter file *is* the memory; Phase 15 already visualized it. Any implied confidentiality-against-white-box claim is false on its face | LOW (prose) | Frame exactly as PROJECT.md already does: the toggle is **availability, not authorization**. Black-box query access only; weight access defeats everything, by design |
| **EXT-7 · Pre-registered claimable direction** | Asymmetry of evidence: a successful weak attack proves leakage; a failed weak attack proves nothing. The unlearning literature's recurring lesson (adaptive attacks recover "removed" capabilities) is exactly this failure | LOW (prose, committed before the run) | If the phase wants to conclude "does not leak," it needs a genuinely adaptive attacker and must say so up front. Recommend: pre-register the *leakage* direction as claimable and the *safety* direction as explicitly non-claimable at this attack budget |

### Differentiators (portfolio-notable)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **D-1 · Canary exposure metric (Secret Sharer), adapter-on vs adapter-off** | Turns "the adapter leaks" into a *calibrated number with a real null*: `exposure = log2(\|R\|) − log2(rank)` where the taught value's sequence log-likelihood is ranked against the 28 never-taught references. Exposure ≈ 0 with the adapter off is a clean, exact null. This is the single highest-power-per-FLOP instrument available here — it needs **forward passes only, no sampling** | MEDIUM (new scorer, ~50 lines; reuses `masked_perplexity` machinery) | Best fit in the whole literature for this situation: a deliberately inserted secret, a small model, a need for a calibrated number. Also directly reusable as the Phase-19 erasure target |
| **D-2 · Lukas attack taxonomy as the Phase-18 structure (extraction / reconstruction / inference)** | Gives Phase 18 a *named, citable* spine instead of an ad-hoc prompt list. Uninformed (extraction) → partially informed (reconstruction, = Phase 14's protocol with an adversarial hat) → informed with a candidate set (inference, = the forced-choice measure). Power increases monotonically down the ladder, which is exactly the story a reviewer wants | LOW (organizational; each rung reuses existing scorers) | The *inference* rung is where a 13.9M model actually leaks measurably. Leading with it, and saying why, is the rigorous move |
| **D-3 · Weight-space companion to the behavioral matrix (ΔW cosine between personas)** | Behavioral M_ij says *whether* personas interfere; per-tensor ΔW cosine/overlap says *where in the weights*. Two independent instruments agreeing is much stronger than either alone — and Phase 15 already set the precedent (Fisher/Δ ρ = 0.801544) | MEDIUM (reuse `extract_deltas.py`; N adapters instead of 1) | Also gives the milestone a second figure for free. **Note:** closes v2.0 debt W6 only if it goes through `merged_state_dict` instead of re-implementing `scale * (b @ a)` a third time |
| **D-4 · Context-pressure ladder as the Phase-16 headline** | "Weights beat prompts" is a boring, confounded claim at this scale. "**Prompt memory decays with context distance and dies at the 256-token boundary; weight memory is provably invariant**" is a real, honest, novel-for-a-portfolio claim, and half of it is a *proof* rather than a measurement | MEDIUM | Uniquely enabled by the small `block_size` — the truncation boundary is reachable in a handful of turns, not 100k tokens |
| **D-5 · Token-cost accounting as an explicitly descriptive companion** | 331,776 params once vs T prompt tokens *every turn, forever* — the amortization crossover is a clean, honest engineering number and a good slide | LOW (arithmetic) | **Must be labelled descriptive.** It is deterministic accounting, not a measurement, and gating it would be a category error |
| **D-6 · Tokenizer-collision persona pair (the 547-live-id angle)** | A project-specific adversarial axis nobody else can run: with 547 live ids the tokenizer is near-character-level, so `brindlemoor` / `brindlemoore` share a long id prefix. A persona pair engineered for **maximal shared token prefix** is the strongest available collision and turns v1.0's known tokenizer weakness into an experimental instrument | MEDIUM (value selection + census; `VALUE_TOKEN_CENSUS` pattern exists) | Pre-registrable as a numeric design constraint ("adversarial pair must share ≥ k leading ids"), which is much better than "we picked similar-looking names" |
| **D-7 · Retrained-gold-standard reference for Phase 19 (TOFU's strongest metric, affordable only here)** | TOFU's forget-quality metric is *indistinguishability from a model retrained without the forget data*. At frontier scale that reference is unaffordable, so most papers approximate it. **Here it costs ~90 seconds** — retrain the adapter on the fact set minus the forget fact. Being able to run the field's gold-standard reference *because* the model is small is a genuinely strong portfolio point | LOW (one extra `train_arm` call) | Measured: the v2.0 real-arm teach ran 11:27:48 → 11:29:09 UTC, ~81 s end-to-end including bin build and collateral PPL |
| **D-8 · Relearning attack on any erasure (Phase 19)** | The current state of the art in unlearning evaluation: fine-tuning on adjacent accessible facts recovers ~88% of pre-unlearning accuracy on published methods. An erasure claim that survives a relearning probe is worth far more than one that doesn't | MEDIUM (one short fine-tune + rescore) | Cheap here for the same reason as D-7 |

### Anti-Features (look rigorous, add nothing or actively mislead at this scale)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Headline "weights beat prompting ~1000×"** | It is the obvious Phase-16 soundbite and the numbers are already sitting there (0.4921 vs 0.0005) | Measures the 13.9M base's broken in-context retrieval, not weight memory. v2.0's own report already warns against exactly this reading. A sharp reviewer kills it in one question | WVP-2 capability floor + WVP-4 context-pressure ladder. If the floor fails, record "not measurable at this scale" and ship the negative |
| **Membership-inference attack on the persona adapter** | It is the canonical privacy-audit move and would look scholarly | n=8 members. MIAs barely beat random guessing on LLMs generally, and reported successes are largely attributable to **distribution shift** between member and non-member candidate sets — which at n=8 hand-authored facts you cannot rule out | Canary exposure (D-1). Same intuition, exact null, real power, no candidate-set confound |
| **Differential-privacy claim / DP-SGD training** | "Privacy project" pattern-matches to DP | No meaningful ε is achievable at this budget, and PersonaCore's privacy claim is *architectural* (on-device, no external store), not statistical. A weak ε invites a rigorous reviewer to attack the strongest part of the project | Keep the architectural claim. State plainly that no formal DP guarantee is claimed |
| **Large hand-written adversarial prompt corpus (jailbreak-style, hundreds of prompts)** | Prefix injection and role-play framing sound like they need volume | This base has almost no instruction-following surface — TinyStories + PersonaChat only. Most jailbreak framings do not *bite*, so you measure "the model didn't parse the attack," not robustness. Volume also multiplies the multiple-comparison problem | A small, pre-registered, **in-distribution** family set (dialogue-format paraphrase / prefix / role-play), each with a fixed budget, plus ASR(N) |
| **Fitting a power-law exponent to ASR(N)** | Best-of-N reports power-law scaling; copying it looks sophisticated | The exponent is not identified over 1–2 decades of N. You would be reporting a fitted parameter with no support | Report the ASR@N table. That is the useful part and it is exact |
| **Gating any per-fact, per-persona, or per-cell comparison** | Each cell is a number, so it feels gateable | n = 8 facts / 3–4 personas. v2.0 already established the correct discipline (correlation *sign* gated, magnitude descriptive at n=36); violating it here would be a self-inflicted defect | Gate aggregates over the ~100+ question-level unit; report cells descriptively |
| **LLM-judge scoring of completions** | Substring matching feels crude | Violates the zero-budget/offline constraint outright, and replaces an auditable mechanical predicate with an unauditable one. The existing `contains_value` + `find_contradictions` pair is a *better* instrument for a portfolio because a reader can verify it | Keep the mechanical gate. Extend `find_contradictions`' committed lexicon to all N persona values |
| **N ≥ 6 personas** | More cells look more thorough | Training cost is linear but *scoring and reporting* grow, and persona-level statistics still do not work at n=6. Diminishing returns start immediately after the first genuine collision pair | N=3 (zero new gated values needed) or N=4 (2 new values: `street`, `house_number`). Spend the saved budget on seed replication of the worst pair |
| **Erasure implemented as adapter deletion / zeroing** | It trivially "works" | That is `eject_lora`, shipped in Phase 9, and it proves nothing about **selectivity** — the entire point of Phase 19 | Any Phase-19 erasure must satisfy a three-way constraint (forget ↓, retain →, collateral PPL →) *and* survive a relearning probe |
| **Claiming any confidentiality property against a white-box adversary** | "Privacy audit" invites it | The 1.35 MB adapter file *is* the memory; Phase 15's heatmaps already show which tensors hold it. The claim would be false | "Availability, not authorization" — PROJECT.md's own framing. Black-box threat model, stated explicitly, with the white-box limitation named |
| **Retraining the tokenizer to remove collisions** | Collisions are a confound in Phase 17 | Explicitly out of scope for v3.0 (invalidates every published checkpoint and number) | Turn the collision into the instrument (D-6) rather than removing it |
| **Re-deriving Phase-14's thresholds (0.2486 / 0.2000) for new personas** | They are already committed and convenient | Non-independence: those thresholds were derived on `CALIBRATION_POOL` measurements. If `CALIBRATION_POOL` values are reused as persona C, gating C's diagonal against 0.2486 is circular | Gate Phase 17 on the **within-run contrast** (diagonal vs off-diagonal), which needs no external threshold at all |

---

## What makes two personas maximally collision-prone

Four axes, each pre-registrable as a numeric design constraint. The literature analogue is
continual-learning task-similarity-driven interference and multi-adapter cross-task interference;
neither field supplies a ready recipe at this scale, so these are derived from the project's own
structure (MEDIUM confidence, but each is independently measurable).

1. **Same slot, different value** — direct key collision. Free: `Fact.slot` already exists and
   `GATE_REJECTED_CANDIDATES` is a full second value for all 8 core slots.
2. **Same value, different slot** — cross-binding probe. Persona A's *dog* is `zorp`; persona B's
   *cat* is `zorp`. Tests whether the adapter binds value→slot or merely memorizes a token. This is
   the axis most likely to actually break, and it is the most interesting failure to find.
3. **Maximal shared token prefix** (the 547-live-id axis, D-6) — near-character-level tokenization
   makes orthographic neighbours share long id prefixes. Constraint form: *"the adversarial pair
   shares ≥ k leading token ids."* Measurable with the existing token-census code.
4. **Identical retrieval cue** — same question strings for both personas. Guaranteed by ISO-1's
   shared `SLOT_QUESTION_BANK` design; it is what makes the matrix well-posed in the first place.

**Why replicate the worst pair across seeds.** With N=3–4 you have one shot per cell, and a single
cell is a *point estimate of a training run*, not of a method — LoRA init (A ~ Gaussian) and data
order both vary. Replicating only the worst pair (k=3 seeds) separates "these two personas
interfere" from "that one training run happened to interfere." At k=3, seed spread is
**descriptive** (report min/max/median), not a hypothesis test — do not gate it.

**Cost note the roadmapper needs:** because ISO-1 shares the question set across personas, M_ij is
**N generation sweeps scored N ways**, not N² sweeps. N=4 personas + 1 adapter-off control ≈ 5
sweeps ≈ the same order as one Phase-14 run, plus 4 × ~90 s of training. If persona-specific
question phrasings were used instead, the cost would be N² and the matrix would be worse science.

---

## Feature Dependencies

```
[v2.0 artifacts: convbase_slim.pt, persona_adapter.pt, tokenizer.json,
 phase14_factset.py, phase14_recall.py, teach_persona.py, extract_deltas.py]
    │
    ├──enables──> WVP-1..6  (Phase 16 — NO new training, adapter already exists)
    │                 │
    │                 └──WVP-3 forced-choice scorer ──feeds──> EXT-3 (chance baseline)
    │                                                   └────> D-1 (exposure ranking)
    │
    ├──enables──> ISO-3 (base-ignorance gate, re-run only)
    │                 └──requires──> ISO-2 (collision design) ──requires──> ISO-1 (shared slots)
    │                                       │
    │                                       └──produces──> N adapters
    │                                                          ├──> ISO-4 (off control)
    │                                                          ├──> ISO-5 (collateral, free)
    │                                                          ├──> ISO-6 (gated contrast)
    │                                                          └──> D-3 (ΔW cosine)
    │
    └──enables──> EXT-1, EXT-2 (references already gated)
                      │
                      └──requires──> N adapters from Phase 17  [for cross-persona attacks only]
                                     (single-persona attacks need only persona_adapter.pt)

D-1 (exposure) ──is the target metric for──> Phase 19 erasure
D-7 (retrained gold) ──is the reference for──> Phase 19 forget-quality
D-8 (relearning attack) ──validates──> Phase 19 erasure claim

[Naive "weights vs prompt at distance 0"] ──conflicts with──> [WVP-2 capability floor]
[MIA] ──conflicts with──> [D-1 exposure]   (same intuition; MIA has the confound, exposure doesn't)
```

### Dependency notes

- **Phase 16 requires no new training.** It consumes `persona_adapter.pt` and the existing question
  sets. This is why it is correctly ordered first (cost-ascending), and its outputs (forced-choice
  scorer, distractor sets, chance baselines) are *inputs* to Phase 18.
- **Phase 17 requires ISO-3 before any training.** A persona whose values the base already knows
  poisons every cell it touches. The gate script exists; for N=3 it is a re-run over already-passed
  values, for N=4 it is a real gate run on ~2 new values.
- **Phase 18 depends on Phase 17 only for cross-persona attacks** (e.g. "can an attacker holding
  persona B's adapter extract persona A's facts?"). Single-adapter attacks depend only on v2.0.
  If schedule pressure appears, Phase 18 can be scoped to single-persona and still stand.
- **Phase 19 is gated on 16–18 producing a measurable target.** See the erasure decision rule below.
- **W1 (v2.0 debt) becomes load-bearing in Phase 17.** Runtime consumers inject with `LoRAConfig()`
  defaults instead of `LoRAConfig(**artifact["lora_config"])`. With one adapter this is benign
  (`teach_persona` also uses defaults). With N adapters, any `alpha` divergence applies the delta at
  the wrong magnitude **silently** — shape audits do not catch `alpha`. Fix it before Phase 17
  trains anything. Two lines.
- **W6 (v2.0 debt) is closeable by D-3.** `merged_state_dict` has no production consumer and
  `extract_deltas.py:174` re-implements `scale * (b @ a)`. A multi-persona ΔW comparison is the
  natural first consumer.
- **`find_contradictions`' lexicon must grow.** It is currently
  `set(LOCKED_VALUES) | {f.value for f in GATE_REJECTED_CANDIDATES}`. If persona B *is* the rejected
  candidates, the detector already knows every foreign value — which is a happy accident, not a
  design; make it explicit and extend it for personas C/D.

### v2.0 artifacts each phase consumes

| Artifact | P16 | P17 | P18 | P19 | Note |
|---|:--:|:--:|:--:|:--:|---|
| `checkpoints/convbase_slim.pt` / `convbase_best.pt` | ✓ | ✓ | ✓ | ✓ | frozen base; `_best` needed for training arms |
| `checkpoints/persona_adapter.pt` | ✓ | ✓ (as persona A) | ✓ | ✓ (forget target) | Phase 16 needs nothing else |
| `artifacts/tokenizer.json` (547 live ids) | ✓ | ✓ (drives D-6) | ✓ | ✓ | frozen; also the `forbid_ids` source |
| `phase14_factset.py` — `Fact.slot`, pools, `SLOT_QUESTION_BANK`, `FAMILIES` F1–F8 | ✓ | ✓ | ✓ | ✓ | taught/held-out family split is reusable as-is |
| `phase14_factset_gate.py` | — | ✓ | ✓ (references) | ✓ | must re-run for any new value |
| `phase14_recall.py` — `contains_value`, `find_contradictions`, `assert_no_value_in_prompt`, `build_recall_prompt`, `question_seed`, `draw_all` | ✓ | ✓ | ✓ | ✓ | the entire scoring spine |
| `phase14_recall.run_fairness_control` | ✓ (Phase 16 *formalizes* this) | — | ✓ | — | the existing in-context arm, and its 1/1944 result |
| `phase14_recall.run_collapse_control` / `run_bit_identity_control` | ✓ | ✓ | — | ✓ | invariance proof + collateral |
| `teach_persona.py` — `render_episodes`, `build_bins`, `train_arm`, `LORA_CFG`, replay ratio | — | ✓ (N× ) | — | ✓ (gold retrain) | ~81 s per adapter, measured |
| `src/personacore/lora/` toggle / eject / **merge** | ✓ | ✓ | ✓ | ✓ | merge gets its first production consumer here |
| `src/personacore/continual/` Fisher + `EWCPenalty` | — | — | — | ✓ | retain-set anchoring for selective erasure |
| `extract_deltas.py` + `results/phase15_norms.json` | — | ✓ (D-3) | — | ✓ | weight-space companion + erasure localization |
| `retention_perplexity()` + `results/retention_anchors.json` | ✓ | ✓ (ISO-5) | — | ✓ | the collateral instrument; the +27.16% limitation lives here |
| Pre-registration pattern (`_verdict.py`, module-level literals, committed-before-run) | ✓ | ✓ | ✓ | ✓ | the methodological spine, not optional |

---

## Gateable vs Descriptive (explicit — the roadmapper must not gate the wrong things)

The project's rule: *gate only the part of a claim the sample size supports; report the rest
descriptively.* Applied here.

### GATEABLE (falsifiable at realistic sample sizes)

| Measure | Unit / n | Test | Why it holds |
|---|---|---|---|
| Adapter-on vs adapter-off extraction rate, paired | question, n ≈ 100–270 | McNemar on discordant pairs, or paired bootstrap CI | Same prompts, same seeds, only `enabled` differs. Expected effect is enormous |
| Forced-choice accuracy vs 1/K chance | question, n ≈ 100+ | exact binomial vs 1/K | Chance is *exact*, not estimated. Highest power per FLOP |
| Canary exposure > 0 | per fact, ranked against \|R\| = 28 references | rank-based, exact; aggregate across 8 facts by sign test or mean-with-CI | Null is exact (uniform rank when adapter off) |
| M_ij: `min(diagonal) > max(off-diagonal) + margin` | question-level within each cell | pre-registered margin from the never-taught reference rate | Aggregate contrast, not per-cell ordering |
| Off-diagonal leak ceiling: `max off-diagonal ≤ X` | question-level, n ≈ 100+ per cell | one-sided binomial | X must come from the measured reference rate, committed before the run |
| Weight-arm invariance under context truncation / overwrite | n/a — exact | assertion + test | It is a proof (identical ids ⇒ identical logits, max\|diff\| 0.0), not a statistic |
| Prompt-arm monotone degradation across the pressure ladder | question, paired across ladder rungs | paired test per rung | **Only if WVP-2 gets the prompt arm off the floor.** Otherwise: not gateable, record why |
| Adapter-off logit bit-identity for every new adapter | n/a — exact | existing `run_bit_identity_control` | Structural |
| Post-erasure forget rate ≤ never-taught reference + margin | question, n ≈ 100+ | one-sided binomial | Needs Phase 18 to have established a nonzero pre-erasure rate first |

### DESCRIPTIVE ONLY (cannot support a gate here — gating these would be a defect)

| Measure | Why not gateable |
|---|---|
| Per-fact recall / exposure effect sizes | n = 8 facts |
| Per-persona or per-cell ordering claims (M_12 vs M_13) | n = 3–4 personas; cells are single training runs |
| Seed spread on the replicated worst pair | k = 3; report min/max/median |
| Token-cost / amortization crossover | deterministic accounting, not a measurement |
| ASR power-law exponent | not identified over 1–2 decades of N |
| MIA AUC | n = 8 members; confounded by candidate-set construction |
| ΔW cosine *magnitude* between personas | n = 72 tensors but they are not independent; gate the **sign/ordering** at most, per the Phase-15 precedent |
| Collateral-collapse % per persona | descriptive by v2.0 precedent (acquisition cost was reported ungated for exactly this reason) |
| Any claim generalizing beyond "this adapter at this configuration at 13.9M params" | out of sample entirely |

---

## MVP Definition

### Launch With — Phase 16 (cheapest, sharpest, no new artifacts)

- [ ] WVP-1 paired design — **essential**, otherwise arms aren't comparable
- [ ] WVP-2 capability floor for the in-context arm — **essential**, the difference between a
      result and a confound; carries a pre-registered "not measurable" branch
- [ ] WVP-3 forced-choice / rank scorer with 1/K chance — **essential**, the only powered instrument
- [ ] WVP-4 context-pressure ladder (truncation / dilution / overwrite) — **essential**, this is the
      actual finding
- [ ] WVP-5 weight-arm invariance as a structural proof — **essential**, and nearly free
- [ ] WVP-6 scope statement — **essential**, reuses Phase 14's opener
- [ ] D-5 token-cost accounting, labelled descriptive

### Then — Phase 17 (persona generator, the artifact DEMO-F1 always needed)

- [ ] ISO-1 shared-slot question design — **essential**, prevents a trivially-diagonal matrix
- [ ] ISO-2 adversarial collision design (4 axes, pre-registered) — **essential**
- [ ] ISO-3 base-ignorance gate on all values — **essential**
- [ ] ISO-4 adapter-off control on the matrix — **essential**
- [ ] ISO-5 per-persona collateral report — **essential**, already free
- [ ] ISO-6 diagonal-vs-off-diagonal gate — **essential**
- [ ] ISO-7 clean-room per adapter — **essential**
- [ ] Worst-pair seed replication (k=3), descriptive
- [ ] D-3 ΔW cosine companion + D-6 tokenizer-collision pair — differentiators
- [ ] **Prerequisite:** fix W1 (`LoRAConfig(**artifact["lora_config"])`) before training N adapters

### Then — Phase 18 (consumes both)

- [ ] EXT-1 no-adapter negative control — **essential**
- [ ] EXT-2 never-taught reference values — **essential**
- [ ] EXT-3 chance baselines — **essential**
- [ ] EXT-4 pre-registered budget + families — **essential**
- [ ] EXT-5 ASR@N table — **essential**, free
- [ ] EXT-6 threat model incl. white-box exclusion — **essential**
- [ ] EXT-7 pre-registered claimable direction — **essential**
- [ ] D-1 canary exposure — differentiator, highest value
- [ ] D-2 Lukas taxonomy as the phase spine — differentiator, organizational

### Gated on 16–18 — Phase 19+ (selective erasure)

- [ ] D-7 retrained gold-standard adapter (~90 s) — the field's strongest reference, affordable only
      because the model is small
- [ ] D-8 relearning attack — the current state of the art in unlearning evaluation
- [ ] Three-way selectivity constraint (forget ↓, retain →, collateral →)
- [ ] "Detectable hole" check — an anomalously bad forget-slot is itself a leak

### Do Not Build

MIA · DP claims · large jailbreak corpus · power-law fits · LLM judges · N ≥ 6 personas ·
adapter-deletion-as-erasure · white-box confidentiality claims · tokenizer retrain

---

## Feature Prioritization Matrix

| Feature | Reviewer Value | Cost (code / M3 compute) | Priority |
|---------|------------|---------------------|----------|
| WVP-2 capability floor | HIGH (validity gate for the whole phase) | LOW / ~1 sweep | P1 |
| WVP-3 forced-choice scorer | HIGH (unlocks power everywhere) | MEDIUM / 0 extra generation | P1 |
| WVP-4 context-pressure ladder | HIGH (the actual finding) | MEDIUM / 3–4 sweeps | P1 |
| WVP-5 invariance proof | MEDIUM | LOW / ~0 | P1 |
| ISO-1 shared-slot design | HIGH (matrix is meaningless without it) | LOW / 0 | P1 |
| ISO-2 collision design | HIGH | MEDIUM / 0 | P1 |
| ISO-3 base-ignorance gate | HIGH (validity) | LOW at N=3, MEDIUM at N=4 | P1 |
| ISO-4 / ISO-5 / ISO-7 controls | HIGH (validity) | LOW / 1 sweep, rest free | P1 |
| ISO-6 gated contrast | HIGH | LOW | P1 |
| EXT-1..4, EXT-6, EXT-7 | HIGH (validity) | LOW / 1–2 sweeps | P1 |
| EXT-5 ASR@N | MEDIUM | LOW / free | P1 |
| D-1 canary exposure | HIGH (best instrument available) | MEDIUM / forward passes only | P1 |
| D-2 attack taxonomy spine | MEDIUM-HIGH | LOW | P2 |
| D-4 context-pressure headline framing | HIGH | LOW (framing) | P1 |
| W1 fix (prerequisite) | HIGH (silent-corruption risk) | LOW / 2 lines | P1 |
| D-3 ΔW cosine | MEDIUM-HIGH (second independent instrument) | MEDIUM | P2 |
| D-6 tokenizer-collision pair | MEDIUM-HIGH (project-unique) | MEDIUM | P2 |
| Worst-pair seed replication | MEDIUM | LOW / 3 × 90 s + 3 sweeps | P2 |
| D-5 token-cost accounting | MEDIUM (good slide) | LOW | P2 |
| D-7 retrained gold standard | HIGH (P19 only) | LOW / 90 s | P1-of-P19 |
| D-8 relearning attack | HIGH (P19 only) | MEDIUM | P1-of-P19 |
| N=4 (vs N=3) personas | LOW-MEDIUM | MEDIUM (2 new gated values) | P3 |

---

## Literature Analogue Analysis

(Template's "competitor" slot, repurposed — the competitors here are published evaluation protocols.)

| Capability | Established protocol | What it assumes that fails here | PersonaCore's adaptation |
|---|---|---|---|
| **Weight vs context knowledge** | Knowledge-conflict / context-memory conflict evaluation; ConflictQA's parametric-vs-counter-memory contexts; Memorization Ratio (MR), Original/Counter Answer Ratio | Assumes the model *can* read context reliably. Ours scores 0.0005 in-context | Keep the conflict framing (WVP-4 overwrite arm, scored by `find_contradictions`), replace the generation metric with forced choice (WVP-3), and add the capability floor (WVP-2) |
| **Fine-tuning vs retrieval for knowledge injection** | Ovadia et al. — RAG consistently beats unsupervised fine-tuning for injecting new facts; fine-tuning needs many paraphrase variations of the same fact | RAG is out of scope by design; and their finding is a warning, not a baseline | The paraphrase-variation finding *validates* v2.0's F1–F8 family design retroactively. Cite it; do not run RAG |
| **Multi-adapter isolation** | Cross-task interference in multi-task LoRA (LoRI, TC-LoRA, orthogonal-subspace merging); interference detection via singular-subspace alignment | Aimed at *merging* adapters to improve a shared task; PersonaCore wants them *separate* and asks about leakage | Borrow the vocabulary (cross-task interference, task/adapter interference) and the subspace-overlap instrument (D-3). Do not borrow the merging objective |
| **The M_ij matrix itself** | Continual learning's transfer matrix **R_ij** (Lopez-Paz & Ranzato, GEM): R_ij = performance on task j after training on task i; BWT and FWT are derived from its off-diagonals | Assumes sequential training over tasks; PersonaCore trains personas independently from a shared frozen base | Same object, cleaner semantics: independent training makes off-diagonals *pure* interference with no ordering confound. Name it as the transfer-matrix analogue — it is the right citation and it is more honest than inventing a term |
| **Training-data extraction** | Carlini et al. — discoverable extraction, (k,ℓ)-extractability, k-eidetic memorization; extraction rate over sampled prefixes | Designed for web-scale corpora with unknown duplication; here the "training set" is 220 authored episodes and every secret is known in advance | Use (k,ℓ)-extractability directly (it is cheap and exact), but the *known-secret* setting means Secret Sharer is the better fit |
| **Inserted-secret memorization** | Carlini's Secret Sharer — canary + reference set, exposure = log2(\|R\|) − log2(rank) | Assumes a large reference pool; ours is 28 | 28 references gives exposure resolution up to ~4.8 bits, which is plenty to separate "memorized" from "not." Note the ceiling explicitly rather than hiding it |
| **PII leakage attacks** | Lukas et al. — game-based definitions for black-box **extraction** (uninformed), **reconstruction** (knows the context), **inference** (knows candidate set) | Nothing fails; it maps cleanly | Adopt as the Phase-18 spine (D-2). Inference rung = WVP-3's forced choice, so Phase 16 pre-builds it |
| **Repeated-sampling attacks** | Best-of-N jailbreaking — ASR is a power law in N; report ASR(N) | Needs many orders of magnitude of N to see the law | Report ASR@{1,4,16,64}; skip the exponent |
| **Membership inference** | Shadow-model / LiRA-style MIA, TPR at low FPR | Duan et al.: MIAs barely beat random on LLMs; apparent successes trace to member/non-member **distribution shift** | Do not run. Documented as an anti-feature with the reason |
| **Unlearning evaluation** | TOFU (forget quality as KS-test indistinguishability from a retrained model; forget/retain/real-world utility splits), MUSE (six axes incl. verbatim memorization, knowledge memorization, privacy leakage, utility preservation) | Retrain-from-scratch reference is normally unaffordable; ROUGE-style metrics saturate | The retrain reference costs ~90 s here (D-7) — run the gold standard, don't approximate it. Use exposure and forced choice instead of ROUGE |
| **Robust unlearning** | Łucki et al. (adaptive attacks recover "unlearned" capabilities); Deeb & Roger (fine-tuning on accessible facts recovers ~88%); "benchmarks are weak measures of progress" critiques | Nothing fails | Any Phase-19 claim must include the relearning probe (D-8), and must be stated as *"resists this attack budget"*, never *"removed"* |

---

## Phase 19 decision rule — write this down before 16–18 produce numbers

Per the project's pre-registration discipline, the erasure go/no-go criteria must be committed
before the audit data exists. Recommended shape (the requirements step should turn this into
committed literals):

**Erasure is worth attempting only if ALL of:**

1. **There is a measurable target.** Phase 18's adapter-on leakage exceeds the never-taught
   reference by a margin whose CI excludes zero — e.g. canary exposure > 0 with a CI excluding 0,
   *or* forced-choice accuracy CI excluding 1/K. If the taught value is statistically
   indistinguishable from an untaught same-slot value, there is nothing to erase and the honest
   v3.0 close is to say so and stop.
2. **The target is localizable.** Phase 15's ΔW/Fisher machinery plus Phase 17's cross-persona
   subspace overlap indicate the fact is not smeared uniformly across all 72 adapter tensors. If it
   is uniform, "selective" erasure has no selectivity to exploit.
3. **Retain-set headroom exists.** Phase 17 shows other facts in the same adapter survive
   independently — otherwise erasing one fact and erasing the adapter are the same operation.

**If attempted, erasure must beat all of:**

| Bar | What it must show | Instrument |
|---|---|---|
| **Null 1 — adapter ejection** | forget-fact rate at reference level **while** retain-fact rate stays within a pre-registered δ of pre-erasure | existing recall scorer, per-fact |
| **Null 2 — collateral** | masked dialogue-val PPL within a pre-registered δ′ of the pre-erasure adapter | `retention_perplexity()`, the same instrument that produced +27.16% |
| **Gold standard** | post-erasure behaviour indistinguishable from an adapter retrained without the forget fact | D-7, ~90 s |
| **Adaptive attacker** | a short fine-tune on adjacent/accessible facts does not restore the forget value above reference | D-8 |
| **No detectable hole** | the forget slot is not *anomalously* degraded relative to never-taught slots (a detectable hole is itself a leak) | forced-choice on forget vs never-taught slots |

Anything that clears fewer than all five is reported as a partial result with the failed bars
named — never as "erased."

---

## Sources

**HIGH confidence** (peer-reviewed / canonical, protocol details verified):
- Carlini et al., *The Secret Sharer: Evaluating and Testing Unintended Memorization in Neural Networks*, USENIX Security 2019 — canary/reference design, exposure = log2(n) − log2(rank). https://www.usenix.org/system/files/sec19-carlini.pdf
- Carlini et al., *Quantifying Memorization Across Neural Language Models*, 2022 — discoverable extraction, (k,ℓ)-extractability. https://arxiv.org/abs/2202.07646
- Lukas et al., *Analyzing Leakage of Personally Identifiable Information in Language Models*, IEEE S&P 2023 — game-based extraction / reconstruction / inference taxonomy. https://arxiv.org/abs/2302.00539
- Duan et al., *Do Membership Inference Attacks Work on Large Language Models?*, COLM 2024 — MIAs near random; apparent success traces to distribution shift. https://arxiv.org/abs/2402.07841
- Lopez-Paz & Ranzato, *Gradient Episodic Memory for Continual Learning*, NeurIPS 2017 — the R_ij transfer matrix, BWT/FWT. https://arxiv.org/abs/1706.08840
- Ovadia et al., *Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs*, EMNLP 2024 — fine-tuning needs many paraphrase variations per fact. https://aclanthology.org/2024.emnlp-main.15/
- Łucki et al., *An Adversarial Perspective on Machine Unlearning for AI Safety*, TMLR 2025 — removal vs obfuscation; adaptive attacks recover capabilities. https://arxiv.org/abs/2409.18025
- Deeb & Roger, *Do Unlearning Methods Remove Information from Language Model Weights?*, 2024 — fine-tuning on accessible facts recovers ~88%. https://arxiv.org/abs/2410.08827
- Hughes et al., *Best-of-N Jailbreaking*, 2024 — ASR(N) reporting norm, power-law scaling. https://arxiv.org/abs/2412.03556

**MEDIUM confidence** (single source or survey-level; used for vocabulary, not for load-bearing claims):
- Xu et al., *Knowledge Conflicts for LLMs: A Survey*, EMNLP 2024 — context-memory / inter-context / intra-memory taxonomy. https://arxiv.org/html/2403.08319v1
- ConflictQA / Memorization Ratio, Original & Counter Answer Ratio — forced-choice-style conflict metrics.
- ConflictBank, NeurIPS 2024 D&B — knowledge-conflict benchmark construction. https://arxiv.org/html/2408.12076v1
- TOFU / MUSE unlearning benchmarks — forget quality as KS-indistinguishability from a retrained model; MUSE's six evaluation axes. (Surveyed via *Unlearning in LLMs: Methods, Evaluation, and Open Challenges*, https://arxiv.org/pdf/2601.13264)
- Multi-task LoRA interference literature (LoRI; TC-LoRA; orthogonal-subspace merging) — cross-task interference vocabulary and subspace-alignment detection.
- McNemar's test for paired binary model comparison + paired bootstrap CIs — standard practice for same-prompt, two-condition NLP evaluation.

**Project-internal (HIGH — measured in this repo, cited by file):**
- `results/phase14_recall_report.md` — 0.4921 / 0.3483 / 0/2430; question-fairness control **1/1944 = 0.0005**; collateral **+27.16%**; ADAPT verdict with two qualifications.
- `results/phase14_teaching_run.log` — one persona adapter end-to-end in **~81 s** on MPS (11:27:48 → 11:29:09 UTC), incl. bin build and collateral PPL.
- `results/phase14_recall_run.log` — 540 questions / **4,860 completions** at ≤48 new tokens in one v2.0 scored sweep (wall clock not logged; budget ~0.5–1 h on MPS, MEDIUM).
- `scripts/phase14_factset.py` — `Fact(id, slot, value, tier)`; `GATE_REJECTED_CANDIDATES` = 8 core composition trims that **already passed the base-ignorance gate at 0/16** and cover all 8 core slots.
- `.planning/milestones/v2.0-MILESTONE-AUDIT.md` — W1 (`LoRAConfig()` defaults, silent `alpha` drift), W6 (merge API test-only, formula duplicated).

---
*Feature research for: adversarial privacy audit + selective erasure of weight-based memory at 13.9M params*
*Researched: 2026-08-12*
