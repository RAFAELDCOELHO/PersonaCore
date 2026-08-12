# Project Research Summary

**Project:** PersonaCore — milestone v3.0 "Adversarial Privacy Audit and Selective Memory Erasure"
**Domain:** ML privacy / memorization auditing of weight-resident LoRA memory on a 13.9M-param
from-scratch decoder, on-device (M3/MPS), zero budget
**Researched:** 2026-08-12
**Confidence:** HIGH (repo-grounded findings) / MEDIUM-HIGH (literature protocols) / MEDIUM (scale-specific recommendations)

---

## 0. The convergent finding — read this before scoping anything

**Two researchers independently reached the same conclusion, and it changes Phase 16's premise.**

**Phase 14 already ran the weight-vs-prompt comparison.** `run_fairness_control` placed each fact's
own first-person statement *inside the `<|system|>` persona span* — the exact stage-2 format the
model saw 5.26M tokens of — and the un-adapted base scored **1/1944 = 0.0005**
(`results/phase14_recall_report.md:378`). The phase's own verdict text at `:587` reads: *"the base's
in-context extraction is close to non-functional independent of whether memory is present."*

Consequence: **at 13.9M params, prompt-stuffing does not trivially win — it is already at the
floor.** A Phase-16 headline of "weights beat prompting ~1000x" (0.4921 vs 0.0005) would be
measuring a **capability deficit**, not weight memory, and it would be refuted by a number already
committed in this repo by this project. That is the single most credibility-destroying sentence
available in this milestone.

Both researchers converged on the same reframing. **Phase 16's real axis is persistence under
context pressure** — truncation at `block_size=256`, dilution across turns, adversarial same-slot
overwrite — where the weight arm is invariant **by proof** (`run_bit_identity_control`, identical
prompt ids => identical logits, max |diff| 0.0) and the prompt arm is not. The honest headline is
*"prompt memory decays with context distance and dies at the 256-token boundary; weight memory is
provably invariant"* — half proof, half measurement, and only sayable by someone who ran the
control.

Three propagating consequences:

1. **Free-generation success rate is a low-power instrument at this scale.** Anything that carries a
   *gate* should use a rank / forced-choice / likelihood measure with an exact chance baseline
   (1/K). Free generation stays as the *demonstration* instrument and the honest headline, but the
   falsifiable claim should not live there.
2. **Phase 16 needs a blocking in-context capability ladder** before any comparison is scored — and
   a pre-registered "not measurable at this scale" branch if the ladder is flat at every rung.
3. **Phase 18 must pre-register its claimable direction.** A weak attacker that *succeeds* proves
   leakage. A weak attacker that *fails* proves nothing. State which conclusion is admissible
   before running.

---

## Executive Summary

v3.0 is a **measurement milestone bolted onto a shipped stack**, not a build milestone. Everything
the three phases need already exists as tested seams: `build_recall_prompt(tok, q, persona=...)` is
implemented and tested, `run_scored_recall` already returns exactly one cell of M_ij,
`load_adapter_weights` already does a key+shape audit before any tensor is copied,
`adapter_disabled` is already proven bit-identical to the un-adapted base at 0/2430, and
`render_family` already renders templated phrasing families. The work is new *drivers* and new
*committed pre-registration data* over that instrument — plus ~50-60 lines of hand-rolled numpy
statistics. **`pyproject.toml` should be byte-identical at v3.0 close.** Zero new
`src/personacore/` modules are warranted; v3.0 introduces no ML mechanism.

The methodological risk dominates the engineering risk, and it is concentrated in three places.
First, the convergent finding above: Phase 16's obvious headline is pre-refuted by the project's own
repo. Second, **Phase 17's matrix is trivially diagonal unless the question set is SHARED across
personas** — if persona j's questions are about facts persona i never saw, the off-diagonal is zero
by construction and the matrix re-proves the 0/2430 control at N^2 the cost. The matrix is only
well-posed when the *question* is shared and the personas differ in the *value* they assign to the
same slot. Third, **the data is clustered**: Phase 14's 0.4921 is 496/1008 where those 1008
completions are 112 questions x 9 draws over 10 facts — **not 1008 independent Bernoulli trials**. A
Wilson interval on n=1008 would be far too narrow. The unit of analysis is the **question**; the
interval is a **cluster bootstrap over questions**, with Wilson reported alongside and explicitly
labelled as the independence-assuming width.

Mitigation is entirely procedural and inherits v2.0's discipline verbatim: pre-registered gates as
module-level literals in pushed commits, verdicts computed by importing constants rather than
retyping numbers, structural enforcement (AST walks, fresh-interpreter probes, `SystemExit` guards)
instead of declared invariants, extract-once-then-plot-from-a-committed-artifact, and honest
negatives recorded unamended. Two items must land **before work starts** (§ Pre-work below) — one of
them, the Phase-19 decision rule, has **no recovery path** if skipped.

---

## Key Findings

### Recommended Stack — no change

**ZERO NEW DEPENDENCIES.** Every v3.0 statistical object is closed-form or resampling-based and
needs nothing numpy lacks. The repo has now declined scipy for a rank correlation **twice** in
committed code (`src/personacore/continual/fisher.py:50`, `scripts/phase15_stats.py:6`); taking the
dependency two phases later for a Wilson interval that is six lines of algebra would silently retcon
that register — in a *privacy audit*, the worst possible place to relax a stated discipline.

**Core technologies (all unchanged):** Python 3.11 · `torch==2.7.*` (MPS fp32, no AMP) · `numpy~=2.4`
· `matplotlib~=3.10` · `pytest~=9.0`. Do not bump anything mid-milestone — v3.0 compares new numbers
against v2.0 artifacts, and a runtime change makes those comparisons cross-runtime for no benefit.

**The entire stack delta is ~50-60 lines in a new `scripts/phase17_stats.py`** shaped exactly like
`phase15_stats.py` (module-level pre-registration constants, pure functions, method strings that
travel with the number). Never edit `phase15_stats.py` — it carries a committed pre-registration for
a specific Phase-15 claim.

| Object | Implementation | Lines |
|---|---|---|
| Proportion CI | Wilson (Wald collapses to `[0,0]` at k=0, which is the *expected* result here) | ~8 |
| Zero-success bound | rule of three (`p <= 3/n`) — never a bare `0%` | 1 |
| Paired weight-vs-prompt | sign-flip permutation (reuses `permutation_p`'s shape) | ~12 |
| **Cluster CI on a rate** | **question-level bootstrap** — the load-bearing statistical choice | ~8 |
| N x N multiplicity | **Holm–Bonferroni**, not BH | ~10 |
| Exact binomial tail (if ever wanted) | `math.lgamma` + bisection — closes the scipy escape hatch | ~12 |

**Holm over BH for a substantive reason:** off-diagonal cells are *not* independent — they share
adapters row-wise, question sets column-wise, and one frozen base. BH needs independence or PRDS;
Holm is valid under arbitrary dependence. The shorter implementation is also the better-justified
one. Say that in the pre-registration.

**Also pin, before any run:** heatmap `vmin=0.0, vmax=1.0` (autoscale is how a heatmap lies — a
0.01 off-diagonal renders as a mid-tone against a 0.49 diagonal), every cell annotated with its
number and `k/n`, and the plotting module reading **only** the committed JSON under the Phase-15
AST-walk + fresh-interpreter no-torch guard.

Full detail: `.planning/research/STACK.md`.

### Expected Features

**Must have (a reviewer calls the result invalid without these):**

- **WVP-2 · in-context capability ladder as a blocking positive control** — the difference between a
  result and a confound. Carries a pre-registered "not measurable at this scale" branch.
- **WVP-3 · forced-choice / rank scorer with an exact 1/K chance baseline** — the only powered
  instrument at this scale. Distractors are free and already base-ignorance-gated
  (`GATE_REJECTED_CANDIDATES`, `CALIBRATION_POOL`, `REGISTER_ARM_POOL` = 28 same-slot values).
- **WVP-4 · context-pressure ladder** (truncation / dilution / overwrite) — the actual finding.
- **WVP-5 · weight-arm invariance stated as a proof, not a rate.**
- **ISO-1 · shared-slot question design** — without it the matrix is meaningless *and* costs N^2.
- **ISO-2 · adversarial collision design, pre-registered** over four measurable axes (same
  slot/different value; same value/different slot; maximal shared token prefix; identical retrieval
  cue). "Three random personas" measures nothing.
- **ISO-3 · base-ignorance gate on every value**, **ISO-4 · adapter-off control per column**,
  **ISO-5 · per-persona collateral (already free from `train_arm`)**, **ISO-7 · clean-room per
  adapter**.
- **EXT-1..EXT-7** — no-adapter negative control at identical prompts/seeds/K; never-taught
  reference values; explicit chance baselines; pre-registered attack budget and families;
  **ASR@{1,4,16,64} rather than a single number**; threat model including what is *not* covered;
  pre-registered claimable direction.

**Should have (portfolio differentiators):**

- **D-1 · Secret Sharer canary exposure** (`log2(|R|) - log2(rank)`, |R| = 28) — the best single
  instrument available here: an exact null (uniform rank with the adapter off), forward passes only,
  no sampling, and directly reusable as the Phase-19 erasure target.
- **D-2 · Lukas et al. extraction / reconstruction / inference taxonomy as Phase 18's spine** — a
  named, citable structure with monotonically increasing power, where the *inference* rung is where
  a 13.9M model actually leaks measurably.
- **D-4 · context-pressure ladder as the Phase-16 headline** (see § 0).
- **D-3 · dW cosine between personas** — a second, independent instrument agreeing with the
  behavioral matrix; closes v2.0 debt W6 if routed through `merged_state_dict`.
- **D-6 · tokenizer-collision persona pair** — with 547 live ids the tokenizer is near
  character-level, so an engineered maximal-shared-prefix pair turns v1.0's known weakness into an
  experimental instrument, pre-registrable as a numeric constraint.
- **D-5 · token-cost accounting**, explicitly labelled descriptive.

**Defer to Phase 19+ (gated):** retrained-gold-standard reference (D-7, ~81 s — TOFU's strongest
metric, unaffordable at frontier scale and cheap here) · relearning attack (D-8) · three-way
selectivity constraint · "detectable hole" check.

**Do not build:** membership inference (n=8 members; MIAs barely beat random and reported successes
trace to distribution shift — use canary exposure instead) · DP claims · a large jailbreak corpus
(this base has almost no instruction-following surface; you would measure "the model didn't parse
the attack") · ASR power-law exponent fits · LLM-judge scoring · N >= 6 personas ·
adapter-deletion-as-erasure · any white-box confidentiality claim · tokenizer retrain.

Full detail: `.planning/research/FEATURES.md`.

### Architecture Approach

Three findings: Phase 16 already exists in embryo (`run_fairness_control` *is* the prompt-stuffed
condition; Phase 16 is its promotion into a paired 2x2, not new infrastructure); the guard tension
resolves by **inversion, not a flag**; and **no new `src/personacore/` module is warranted** —
v3.0's new logic is committed evidence-producing rules and data, which this project has consistently
kept in `scripts/` precisely so git history over that file *is* the pre-registration proof
(`phase14_factset.py:7-8`).

**Major components (all in `scripts/`, one file per role — data / extract / render):**

1. `phase14_recall.py` — **MODIFIED, additive only**: the `run_fairness_control` seed fix and the
   new `assert_value_in_prompt` twin. Becomes the shared 3-consumer scoring instrument.
2. `phase16_weight_vs_prompt.py` — the 2x2 (adapter on/off x prompt empty/stuffed), gates, framing
   constants, report. Two of the four cells are already measured.
3. `phase17_personas.py` (data) -> `phase17_persona_gate.py` (guessability, **hard human-verdict
   blocker**) -> `teach_persona.py` xN -> `phase17_matrix.py` (the *only* checkpoint reader) ->
   `phase17_isolation.json` -> `plot_phase17.py` + `phase17_stats.py` + report.
4. `phase18_attacks.py` (attack families as committed data, `FAMILIES`-shaped) ->
   `phase18_extract.py` (negative control + attacker) -> `phase18_extraction.json` + transcripts.
5. `scripts/erasure_gate.py` — `ERASURE_DECISION_RULE`, phase-neutral, dependency-free, committed at
   Phase-16 open and imported by all three report writers.

**The guard inversion (Pattern 1) is the architectural call worth repeating.** Do **not** add
`assert_no_value_in_prompt(..., skip=True)` or `run_scored_recall(..., stuffed=True)` — that
converts a structural invariant into a runtime flag whose protection depends on a default nobody
re-reads. Instead add the logical twin `assert_value_in_prompt` (same two levels: normalized string
*and* contiguous token-id run), so **every** scoring path asserts something and **no** path has a
skip mode, enforced by an AST test that every `draw_all` caller is preceded by exactly one of the
two.

Full detail: `.planning/research/ARCHITECTURE.md`.

### Critical Pitfalls

1. **P16-1 · The comparison is pre-rigged and the project already knows it.** See § 0. Prevention:
   blocking capability ladder + a module-level `licensed_headline(ladder) -> str` that returns the
   comparative claim only when the ladder is non-zero at some rung, called by the report generator
   (which cannot accept a hand-typed headline). Quote the 1/1944 prior in the **pre-registration**
   commit, not the write-up.
2. **X-3 · Phase 19's go/no-go creating motivated interpretation of 16-18.** The decider is the same
   person who produces the data. **Recovery cost: unrecoverable.** The gate file must precede Phase
   16's first run — a hard plan precondition, not a note. (v1.0's WR-04 was prose in a verification
   report and became permanent debt; v1.0's `forbid_ids` warning crossed two milestones. The
   project's own Top Lesson 1: *warnings need gates, not just records*.)
3. **P17-1/P17-2 · The worthless green matrix.** Personas that differ in every slot produce a
   uniformly-zero off-diagonal that demonstrates only that unrelated facts are unrelated — and
   without a base row, `M[B][A's question] = 0` re-tests unguessability rather than isolation.
   Prevention: a committed adversariality gate that runs and passes *before any adapter is trained*
   (slot collision, name collision on frozen token ids, non-guessability, tokenizer
   representability), the base as a literal row/column in the artifact, and **the gated statistic is
   the excess `M_ij - M_base,j`**, not the raw cell.
4. **P17-3 · Isolation bought by under-training.** Adapters 2-4 use a recipe validated at N=1. An
   under-trained adapter has a 0.08 diagonal and a 0 off-diagonal, and the matrix reads as isolated.
   Prevention: a per-persona diagonal floor as a committed literal, and a `row_verdict(diag, floor)`
   that **cannot emit ISOLATED** below floor — it emits INCONCLUSIVE. Do not lower the floor.
5. **P18-4 / X-2 · Declaring the system private because a weak attacker failed.** An empirical audit
   lower-bounds leakage; it never upper-bounds privacy. Prevention: the Phase-14 taught-template
   direct question (0.4921) as **attack family zero — a positive control that must reproduce within
   a pre-registered band, or no privacy statement of any kind is admissible from that run**; plus a
   committed `null_result_is_admissible(run) -> bool` and **three** prose templates (`EXTRACTION
   FOUND` / `NO EXTRACTION (admissible)` / `INCONCLUSIVE`) authored before the run. Pre-registration
   that only binds the *positive* outcome silently fails to bind the comfortable one.
6. **P18-5 · The 547-live-id tokenizer silently suppresses extraction.** A target containing a dead
   id is literally unproducible under `forbid_ids`; the resulting zero is written up as privacy.
   Prevention: a representability `SystemExit` at target selection, per-target token counts as a
   required column, and — the decisive one — **a teacher-forced NLL recorded for every
   zero-extraction target**, which separates "the attack is weak" from "genuinely not recoverable."
7. **X-1 · Availability sold as authorization.** The toggle is 36 boolean writes. Fix the honest
   framing in one committed sentence, reuse it verbatim, and lint it — including the demo UI copy,
   which is a published claim.

Full detail: `.planning/research/PITFALLS.md`.

---

## Pre-work — two things that must happen BEFORE Phase 16's first run

These are not phase content. They are entry preconditions.

| # | Item | Why now | Cost |
|---|------|---------|------|
| **A** | **Commit `scripts/erasure_gate.py`** with `ERASURE_DECISION_RULE` and its module-level literals, referencing only **v2.0 published numbers** (0.4921 / 0.3483 / 0/2430 / 3.891140). | The one pitfall with **no recovery path** (X-3). `git log -S "ERASURE_DECISION_RULE = ("` must return a commit that provably predates every v3.0 artifact. Referencing v2.0 baselines is not data-peeking; referencing any 16-18 number would be. | ~1 file, no torch, no fact set |
| **B** | **Fix audit item W1** — runtime consumers inject with `LoRAConfig()` defaults instead of `LoRAConfig(**artifact["lora_config"])`. | Benign at N=1. With N adapters, any `alpha` divergence applies the delta at the wrong magnitude **silently** — shape audits do not catch `alpha`, so nothing raises. Must land before Phase 17 multiplies the call sites from 2 to N. | **two lines** |

**Naming conflict to resolve:** ARCHITECTURE.md calls the file `scripts/erasure_gate.py`,
PITFALLS.md calls it `scripts/phase19_gate.py`. Same object. Pick one at roadmap time and use it
everywhere — `erasure_gate.py` is preferred (phase-neutral, and it survives phase renumbering).

---

## Implications for Roadmap

### Phase 16 — Weight-vs-Prompt **Persistence** Control

**Rationale:** First because it is the phase that **fixes the shared instrument** — the seeding
defect and the missing assertion twin are Phase-16 prerequisites that 17 and 18 then inherit
already-fixed. Doing 17 first would either duplicate those fixes or ship 17 on an unpaired
instrument. It also needs no new training artifacts.

**Delivers:** the 2x2 condition matrix (two cells already measured, two new), the in-context
capability ladder, the forced-choice scorer (which Phase 18 then reuses as its *inference* rung),
the context-pressure ladder, `results/phase16_conditions.json` + transcripts + report.

**Addresses:** WVP-1..6, D-4, D-5.

**Avoids:** P16-1 (ladder + licensed headline), P16-2 (length-matched distractor arm; assert
`max_new_tokens` equal across arms; context length as a published column), P16-3 (counterfactual
slot-swap arm — report *slot-tracking rate*, not raw hit rate), P16-4 (banned-vocabulary lint on the
generated report: Phase 16 is licensed for **availability and utility** claims only; **Phase 18 is
the only phase licensed to speak about extraction**), P16-5 (import Phase-14's frozen question
families; never retype).

**Contains three code fixes, each in its own commit with its own test, watched failing first:**
`run_fairness_control` seeds from `enumerate(questions)` rather than `item.seed_index` — the CR-01
pairing defect, left unfixed in that path because Phase 14 never compared fairness against anything;
`assert_value_in_prompt`; and the AST guard at
`tests/test_phase14_scoring.py:425::test_persona_argument_is_scoped_to_the_fairness_control`, which
pins `persona=` to exactly one call site and **must be WIDENED deliberately and visibly, never
deleted** — quietly removing it is the exact "declared invariant silently becomes false" failure the
v2.0 learnings named as this project's most recurring mistake.

### Phase 17 — Multi-Persona Isolation Matrix M_ij

**Rationale:** Builds the persona generator DEMO-F1 always needed; consumes the fixed instrument;
produces the N adapters Phase 18 may optionally use.

**Delivers:** N=3 adversarial persona fact sets as committed data, a guessability gate report with a
**human GO/ADAPT verdict as a hard blocker**, N trained adapters (~81 s each, measured), the matrix
artifact + heatmap + statistics, worst-pair seed replication (k=3, **descriptive** — report
min/max/median, never a hypothesis test).

**Uses:** `load_adapter_weights` in-place swap (no base reload — all N adapters share an identical
`lora_` key set), `stamp_seed_indices` stamped **once outside both loops**, `run_scored_recall`
unchanged, `find_contradictions` with its lexicon extended to the union of all persona values.

**Avoids:** P17-1..P17-6. Specifically: one **cell-blind scorer** whose signature takes
`(completion, target)` and *no* `(i, j)` argument at all, pinned by an `inspect.signature` test
(no `if i == j:` anywhere in the scoring path); a **template-only control column** (a value taught
to nobody) so template-driven emission is separable from leakage; and confabulations
("well-formed but wrong value") recorded in their own category, never sharing a cell with leaks.

**Literature anchor:** M_ij is continual learning's **transfer matrix R_ij** (Lopez-Paz & Ranzato,
GEM) — with cleaner semantics, since independent training from a shared frozen base makes the
off-diagonals *pure* interference with no ordering confound. Name it as the transfer-matrix
analogue; it is the right citation and more honest than inventing a term.

**Adapter-swap canary is mandatory.** A silently-failed swap reports adapter 0's numbers N times —
a perfect diagonal and zero cross-leakage, i.e. **the most flattering possible wrong answer**.
`lora_state_dict` before/after + an equality check against the artifact's tensors; the
`snapshot_params` register from `teach_persona.py:638-652`, no new module.

### Phase 18 — Black-Box Adversarial Extraction Audit

**Rationale:** Consumes the fixed instrument and Phase 16's forced-choice scorer. Depends on Phase
17 **only** for optional cross-persona attacks — single-persona Phase 18 must stand alone, so
schedule pressure can scope it down without invalidating it.

**Delivers:** the committed attack corpus (A1 paraphrase / A2 prefix injection / A3 role-play; A4
repeated sampling is a **budget parameter, not a fourth prompt shape**), both arms at identical
prompts/seeds/K/`forbid_ids`/`stop_ids`, ASR@{1,4,16,64} + the cumulative curve, the threat-model
table, and the availability-not-authorization reframing.

**Structural spine:** Lukas et al.'s **extraction (uninformed) -> reconstruction (knows the context)
-> inference (knows the candidate set)** taxonomy, power increasing monotonically down the ladder.
Leading with the inference rung — and saying *why* it is where a 13.9M model actually leaks
measurably — is the rigorous move.

**Best single instrument:** Secret Sharer **canary exposure**, adapter-on vs adapter-off. Exact
null, forward passes only, and it becomes Phase 19's erasure target for free.

**Guard note:** `assert_no_value_in_prompt` applies to the **entire** Phase-18 corpus unmodified —
an extraction attack that already contains the value is not an extraction attack, so the guard
*becomes the operational definition* of "the attacker does not already know the answer." Prefix
injection is the one family that needs a **declared, small, pre-registered injection budget** with
the realized injection **measured per prompt**, scoring only the unprompted remainder. The check
must be **substring-aware** — Phase 14's exact-equality fact-freeness tests passed while the
invariant was violated by a substring embedding; reuse `_strings_in`, do not rewrite an equality
check.

### Phase 19+ — Selective Erasure (gated, not planned now)

Enters the roadmap only if `erasure_worth_attempting(...)` returns True over three committed
numbers. Its bars are already researched (retrained-gold-standard reference at ~81 s; relearning
attack; three-way forget-down / retain-flat / collateral-flat constraint; "detectable hole" check)
but **must not be planned in detail now** — that is what would create the motivated interpretation
X-3 exists to prevent.

### Phase Ordering Rationale — with two corrections to the stated plan

- **Dependency order 16 -> 17 -> 18 is correct and should be kept.** But **the stated cost rationale
  is wrong: Phase 16 is NOT "the cheapest of the three."** Once its blocking in-context capability
  ladder, length-matched distractor arm, counterfactual slot-swap arm, and the decision to re-measure
  all four cells in one process are added, Phase 16 runs ~2-3x Phase 14's scored run. Keep 16 first
  for the *instrument-fix* reason, not the cost reason.
- **Phase 17 is much cheaper than N^2 if and only if ISO-1 holds.** Because the question set is
  **shared** across personas, M_ij is **N generation sweeps scored N ways, not N^2 sweeps** — N=3-4
  personas plus the adapter-off control ~= 5 sweeps, the same order as one Phase-14 run, plus N x ~81
  s of training. Persona-specific phrasings would cost N^2 *and* be worse science. This is a design
  constraint with a cost consequence; the roadmapper should treat it as load-bearing.
- **Opinionated call: N=3, not 4.** The matrix cost scales N x (N+1); 3->4 is a ~60% increase in the
  most expensive phase for one extra row, and three personas already support both collision kinds
  plus a worst-pair selection. N=3 also needs **zero new gated values** (see reuse below). If 4, the
  fourth persona's purpose must be pre-registered (e.g. "a persona with *no* collisions, as the
  matrix's own negative-control row"), not chosen for roundness.
- **Never lower `N_SEEDED_SAMPLES` to buy wall clock.** Cut the question set or the soft tier
  (which already feeds no gate); keep the draws — draws are what make the rate a rate, and a decode
  setting chosen to make a number look better is the same category of error as a post-hoc threshold.

### Reuse findings that materially reduce scope

- **Persona B largely already exists and is already base-ignorance-gated.** The 8 core "composition
  trims" in `GATE_REJECTED_CANDIDATES` were rejected *only* by the one-fact-per-slot rule, already
  passed the base-ignorance gate at **0/16**, and cover **all 8 core slots** — a ready-made second
  persona with perfect slot collision. `CALIBRATION_POOL` (10) and `REGISTER_ARM_POOL` (6) supply
  most of persona C. At N=3 there is nothing new to gate; at N=4 only `street` and `house_number`
  fall short.
- **The negative-control / guessability machinery exists** in `scripts/phase14_factset_gate.py`
  (`FACTSET_GATE_SHA 446afab3...`), including the tokenizer census. Promote `_probe` -> `probe`
  (visibility only) so Phase 17 imports the *same instrument* rather than a copy.
- **`find_contradictions`' committed lexicon already knows every foreign value** if persona B *is*
  the rejected candidates. That is a happy accident, not a design — make it explicit and extend it
  for persona C.
- **One adapter trains in ~81 s on MPS** (measured: `results/phase14_teaching_run.log`, 11:27:48 ->
  11:29:09 UTC, including bin build and collateral PPL). This is what makes TOFU's gold-standard
  **retrain-without-the-fact** reference affordable in Phase 19 — the field's strongest unlearning
  metric, normally approximated because it is unaffordable, runnable here for the price of a coffee
  refill. That is a genuinely strong portfolio point and it exists *because* the model is small.

### Gateable vs Descriptive — explicit, because gating the wrong thing is a defect here

**GATEABLE:** adapter-on vs adapter-off extraction rate, paired (n ~= 100-270 questions) ·
forced-choice accuracy vs an **exact** 1/K chance · canary exposure > 0 (exact null) ·
`min(diagonal) > max(off-diagonal) + margin` as an aggregate contrast · off-diagonal leak ceiling as
a **one-sided upper bound** · weight-arm invariance (a proof, not a statistic) · adapter-off
bit-identity per new adapter · prompt-arm monotone degradation across the pressure ladder **only if
the capability ladder gets the prompt arm off the floor**.

**DESCRIPTIVE ONLY — gating these would be a defect:** per-fact effect sizes (n=8) · per-cell
ordering claims (n=3-4 personas; each cell is a single training run) · seed spread at k=3 ·
token-cost accounting (deterministic arithmetic, not a measurement) · ASR power-law exponent · MIA
AUC · dW cosine *magnitude* · per-persona collateral % · **any aggregate "isolation rate %" over
9-16 cells** — that number implies a precision N=3-4 cannot carry.

**Specific warning:** **do not gate Phase 17 against Phase 14's 0.2486 / 0.2000 thresholds.** Those
were derived on `CALIBRATION_POOL` measurements; if `CALIBRATION_POOL` values are reused as persona
C, gating C's diagonal against 0.2486 is **circular**. Gate the **within-run contrast**
(diagonal vs off-diagonal vs base row), which needs no external threshold at all. The per-persona
diagonal *floor* (P17-3) is a different object and should be derived by the existing rule
(`max(THRESHOLD_FLOOR, round(rate * THRESHOLD_DISCOUNT, 4))`, `THRESHOLD_DISCOUNT = 0.60`) against
0.4921 and pushed before any adapter trains.

### Research Flags

**Needs `/gsd:plan-phase --research-phase` during planning:**

- **Phase 18** — the attack taxonomy and the **denominator discipline** are exactly where a wrong
  prior costs the most, and ARCHITECTURE.md states honestly that it did not verify its external
  grounding. FEATURES.md and PITFALLS.md supply the canary/exposure and Lukas anchors, but the
  phase-specific research should land **before its pre-registration commit**, since the
  pre-registration is unamendable afterward. Also flag: the LoRA-memorization literature reports
  LoRA reducing instance-level memorization up to ~10x in other settings — a low extraction rate may
  be a **LoRA property, not a PersonaCore achievement**, and that belongs in threats-to-validity.
- **Phase 16** — light research only, scoped to the in-context capability ladder's rung design
  (what a 13.9M TinyStories+PersonaChat model can plausibly do at distance ~2 tokens). The rest is
  repo-grounded.

**Standard patterns — skip research:**

- **Phase 17** — every mechanism is already in this repo, and the design constraints (shared-slot
  questions, four collision axes, base row, cell-blind scorer, swap canary, N=3) are already
  specified above at implementation granularity.
- **Statistics across all three phases** — closed-form, ~60 lines, sources cited, alternatives
  considered and rejected with reasons.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | `pyproject.toml` read directly; the zero-new-deps verdict is verified by grep (no scipy/pandas/statsmodels/seaborn anywhere in `src/`, `scripts/`, `tests/`) and by two committed registers. Statistical recommendations are standard results (Wilson, Holm, rule of three) whose correctness is verifiable by inspection, not by citation. |
| Features | **MEDIUM-HIGH** | Literature protocols HIGH — named, peer-reviewed, protocol details verified (Secret Sharer, Lukas, GEM, TOFU, Duan MIA, Best-of-N). Scale-specific recommendations MEDIUM — derived by reasoning from PersonaCore's own v2.0 measurements, which are the only data at this scale. |
| Architecture | **HIGH** for integration points (read against actual file contents at `829cd5f`, with line numbers) · **MEDIUM** for compute-budget estimates · **LOW** for external attack-taxonomy grounding (self-declared; covered by FEATURES.md and flagged for Phase 18 research). |
| Pitfalls | **HIGH** for repo-grounded items — every "this already bit this project" claim was read from the repo, not inferred · **MEDIUM** for literature-derived magnitudes (the ~88% relearning-recovery figure, the 20-30 point budget-inflation figure). **No recommendation depends on a specific external number being right.** |

**Overall confidence: HIGH.** The load-bearing findings — the 1/1944 reframing, the clustering
correction, the shared-question cost collapse, the seeding defect, the W1 alpha-drift risk — are all
repo-grounded and were reached independently by more than one researcher where they overlap.

### Gaps to Address

- **Matrix layout: base as row 0, or as a `"none"` column?** ARCHITECTURE.md specifies N x (N+1) with
  a `"none"` column (adapter-disabled scored per column question set); PITFALLS.md specifies
  (N+1) x N with the base as row 0. **These are the same numbers in two layouts.** Pin one in the
  artifact schema at Phase-17 pre-registration; the test asserting the base's presence must match
  whichever is chosen. Note that the template-only control column (P17-6) is a *distinct* extra
  column, not the same thing.
- **Does Phase 16 re-measure cells A and D, or cite Phase 14?** Recommended: re-measure — all four
  cells from one process, one set of weights, one seed schedule. Costs ~2x wall clock and buys the
  pairing the phase is about. Cite Phase 14 as a cross-check and **state loudly if it does not
  reproduce byte-identically** (Phase 13 measured ~3.6e-8 MPS cross-process drift). Make this an
  explicit phase decision — it doubles the run.
- **Does Phase 17 gate, or report descriptively?** Recommended: gate the diagonal-vs-off-diagonal
  **sign** (isolation exists at all, measured as excess over the base row); report magnitude
  descriptively — the exact split Phase 15 used for its rho at n=36.
- **The three pre-registration decisions that must be settled before any v3.0 number exists.**
  Each is a scoping decision for the requirements step, not a research question:
  1. **Unit of analysis and interval method.** The question (not the draw) is the unit; the headline
     interval is a question-level cluster bootstrap; Wilson is reported alongside and labelled as
     the independence-assuming width; at k=0 pick **one** of rule-of-three (`3/n`) or Wilson's
     two-sided upper (`~=3.84/n`) and state which. Pin a `CI_METHOD` string like Phase 15 did — and
     carry forward `phase15_stats.py`'s committed honesty note that the percentile bootstrap is
     biased and anti-conservative at small n, which bites harder here (clusters may be as few as 10
     facts vs Phase 15's 36 cells). **Do not silently upgrade to BCa after seeing a result.**
  2. **Claimable direction and admissibility, both branches.** `licensed_headline()` for Phase 16
     and `null_result_is_admissible()` for Phase 18, with all verdict prose templates — including
     `INCONCLUSIVE` — committed before the run. Pre-registration that binds only the positive
     outcome does not bind the comfortable one.
  3. **`ERASURE_DECISION_RULE`.** Item A above. No recovery path.

  Two lesser ones ride along: `worst_pair.selection_rule` (a rule chosen after seeing the matrix is
  the exact move pre-registration prevents) and the attack budget K per family.
- **Does the attacker get the `forbid_ids` dead-id mask?** The honest answer is **yes, the same mask
  as every other measurement** — it is part of the deployed system, and a different decode path
  makes the numbers incomparable. Record the choice explicitly rather than inheriting it silently.
- **PROJECT.md's own wording.** *"weight-based memory a privacy guarantee by design"* is exactly the
  sentence v3.0 exists to qualify. Re-read it against what v3.0 actually measured at milestone
  close, and correct by **dated continuation, never by in-place edit** (v2.0's honest-negatives
  rule).

## Sources

### Primary (HIGH confidence — read directly from this repo at `829cd5f`)
- `results/phase14_recall_report.md:378,587` — the 1/1944 in-context control and its recorded limitation
- `scripts/phase14_recall.py` (1981 lines) — scoring instrument, guards, fairness control, CR-01 seeding defect, `stamp_seed_indices`, `draw_all`, `load_adapted_model(adapter_path=)`, `PYTORCH_ENABLE_MPS_FALLBACK` ordering
- `scripts/phase14_factset.py` (848 lines) · `scripts/phase14_factset_gate.py` — committed-data register, `Fact.slot`, `SLOT_FORMS`, `render_family`, `GATE_REJECTED_CANDIDATES` (0/16, all 8 core slots), `BASE_PRIOR_SEEDS`, the guessability + tokenizer-census instrument
- `scripts/teach_persona.py` (1734 lines) — arm parameterization, `CALIBRATION_DECISION_RULE` register, canary discipline, `arm_outputs` path authority
- `scripts/phase15_stats.py` · `scripts/extract_deltas.py` · `scripts/plot_phase15.py` · `scripts/_verdict.py` — the D-12 zero-new-deps register, the extract/plot/verdict three-file boundary
- `src/personacore/lora/inject.py` · `src/personacore/continual/fisher.py:50` · `src/personacore/dialogue/serialize.py:92`
- `tests/test_phase14_scoring.py:425` — the AST-scoping precedent that must be widened, not deleted
- `pyproject.toml` — dependency set verified; scipy/pandas/statsmodels/seaborn/tqdm all absent
- `.planning/PROJECT.md` · `.planning/RETROSPECTIVE.md` · `.planning/milestones/v2.0-MILESTONE-AUDIT.md` (W1, W4, W6)
- `results/phase14_teaching_run.log` — one adapter end-to-end in ~81 s on MPS

### Secondary (HIGH confidence — peer-reviewed, protocol details verified)
- Carlini et al., *The Secret Sharer* (USENIX Security 2019) — canary/reference exposure — https://www.usenix.org/system/files/sec19-carlini.pdf
- Carlini et al., *Quantifying Memorization Across Neural Language Models* — discoverable extraction, (k,l)-extractability — https://arxiv.org/abs/2202.07646
- Lukas et al., *Analyzing Leakage of PII in Language Models* (IEEE S&P 2023) — extraction/reconstruction/inference taxonomy — https://arxiv.org/abs/2302.00539
- Lopez-Paz & Ranzato, *Gradient Episodic Memory* (NeurIPS 2017) — the R_ij transfer matrix — https://arxiv.org/abs/1706.08840
- Duan et al., *Do Membership Inference Attacks Work on LLMs?* (COLM 2024) — MIAs near random; distribution-shift confound — https://arxiv.org/abs/2402.07841
- Lucki et al., *An Adversarial Perspective on Machine Unlearning* (TMLR 2025) · Deeb & Roger (2024, ~88% recovery) — https://arxiv.org/abs/2409.18025 · https://arxiv.org/abs/2410.08827
- Carlini, Athalye et al., *On Evaluating Adversarial Robustness* (2019) — weak attacks make systems look robust — https://nicholas.carlini.com/papers/2019_howtoeval.pdf
- Hughes et al., *Best-of-N Jailbreaking* (2024) — ASR(N) reporting norm — https://arxiv.org/abs/2412.03556
- Ovadia et al., *Fine-Tuning or Retrieval?* (EMNLP 2024) — fine-tuning needs many paraphrase variations per fact; retroactively validates the F1-F8 family design — https://aclanthology.org/2024.emnlp-main.15/
- Brown, Cai & DasGupta (2001) — Wilson/Agresti-Coull over Wald · Holm (1979) — FWER under arbitrary dependence · Hanley & Lippman-Hand (1983) — rule of three

### Tertiary (MEDIUM/LOW confidence — vocabulary and pattern only, not load-bearing)
- TOFU / MUSE unlearning benchmarks; *Existing LLM Unlearning Evaluations Are Inconclusive* (information-injection budgets) — https://arxiv.org/html/2506.00688
- *Single-Configuration ASR Is Not Enough* (2026) — 20-30 point budget inflation — https://arxiv.org/pdf/2605.09070
- Xu et al., *Knowledge Conflicts for LLMs: A Survey* (EMNLP 2024); ConflictQA / Memorization Ratio
- Multi-task LoRA interference literature (LoRI, TC-LoRA, orthogonal-subspace merging) — vocabulary and the subspace-overlap instrument only
- LoRA memorization reduction in federated settings (~10x) — https://arxiv.org/html/2502.05087v1 — **threats-to-validity relevance**: a low Phase-18 extraction rate may be a LoRA property, not a PersonaCore achievement
- StolenLoRA / LoRA-extraction literature — **model stealing, not targeted fact extraction.** Do not cite as prior art for Phase 18 without reading it; the framing differs.

---
*Research completed: 2026-08-12*
*Ready for roadmap: yes*
