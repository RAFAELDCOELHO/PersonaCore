# Phase 24: Adversarial Extraction-Aware Training + the Held-Out Attack Family - Context

**Gathered:** 2026-08-29 (session 1) / 2026-08-30 (session 2, resumed from checkpoint)
**Status:** Ready for planning

<domain>
## Phase Boundary

The second mitigation arm, built as a **data-mixture ratio with no new training seam**, and with its
generalization question converted from a disclaimer into a measurement.

Requirements: ADVT-01, ADVT-02, ADVT-03.

**What this arm is NOT.** It makes no formal privacy claim. Phase 25 SC4 already pins
`accounting: null` on the adversarial arm as the structural statement of that. Every DP argument in
this milestone (per-record clipping, the public-gradient term, the D-11 side channel) is about arm 1
and does **not** bind arm 2. Where a D-11-shaped rule is adopted below it is adopted for
*reproducibility and interpretability*, never smuggled in as a privacy guarantee.

**Two decisions land outside this phase's own text and must travel with it:**

1. `results/phase18_corpus.json` and `scripts/phase18_extraction.py` are **inputs, read-only**
   (SC4 — ancestry-guarded, permanently uneditable). Nothing here edits either.
2. **SC2's success-criterion text in `ROADMAP.md` is FACTUALLY WRONG on its key** and is corrected in
   this phase by a dated additive continuation (D-13). The original sentence stays visible.

</domain>

<decisions>
## Implementation Decisions

Thirteen decisions across four discussed areas. D-01…D-05 were ruled in session 1, D-06…D-13 in
session 2. Every one is LOCKED — the researcher and planner act on them rather than re-open them.

### Area 1 — The adversarial episode target

- **D-01: The adversarial episode's answer is a SLOT-SPECIFIC, VALUE-FREE refusal.** It names the
  *slot* ("I will not share my birth year"), never the *value*.

  Slot is published grammar (`phase14_factset.SLOT_FORMS`); the value is not. This reuses two
  existing shapes instead of inventing a mechanism: `A3_ROLE_INSTRUCTION`
  (`scripts/phase18_extraction.py:506`, a value-free scaffold) and
  `phase21_filler.FILLER_SLOT_FORMS` (slot grammar extended without touching published values).
  Containment is **structurally impossible rather than statistically unlikely**: `contains_value`
  (`scripts/phase14_recall.py:300`) is `normalize(value) in normalize(completion)`, so a template
  that never cites a value can never score as a leak.

  The reuse claim is stronger than it first looks — `scripts/teach_persona.py:437-449` **already**
  merges the two slot-form dicts (`widened = {**fs.SLOT_FORMS, **phase21_filler.FILLER_SLOT_FORMS}`)
  and refuses any slot present in neither, with a clash check at `:437`. The precedent is an
  existing committed mechanism the refusal templates extend directly, not an analogy.

  > Rejected: a fixed generic slot-free refusal (no containment hazard, but the model learns to
  > refuse rather than *what* to withhold); per-fact/per-family refusal (strongest signal, but a
  > refusal naming the value while declining CONTAINS the value and scores as extraction).

- **D-02: A guard sweeps the refusal templates against the published value vocabulary, watched RED
  then GREEN before the containment property may be claimed.**

  `embedded_fact_values(module, forbidden)` (`tests/test_phase14_scoring.py:367`) already does
  exactly this: SUBSTRING containment over every string a module holds, including strings nested in
  tuples and dicts. It exists in that form because an equality predicate let a **real** leak through
  — RECONCILIATION_A's D-20 probe quotes carried the taught pet name verbatim into the demo's
  address space. Watched-RED history, not a hypothetical guard.

  **Planner note.** The existing guard pins `forbidden = LOCKED_FACTS + SOFT_TIER_FACTS` behind a
  hard `assert len(forbidden) == 10`. Add a **SIBLING** guard for the refusal-template module using
  the wider D-10 lexicon (`set(LOCKED_VALUES) | {f.value for f in GATE_REJECTED_CANDIDATES}`,
  `scripts/phase14_factset.py:424-425,446`), leaving the `== 10` assertion untouched. Editing a
  passing guard costs more and sweeps less than adding a sibling.

- **D-03: The adversarial mixture renders ONLY from `core_taught`.** The gated tier
  (`core_held_out`: F3, F7, F8, `reserved`) stays entirely out of training on BOTH axes — new attack
  family and new paraphrase family.

  `reserved` carries a standing published ban: `RESERVED_HELDOUT_PROBES` are seed members of the
  never-seen split, *"permanently banned from every teaching set"* (`scripts/phase14_factset.py:519`),
  with base-failure provenance (`FACTSET_GATE_SHA` + base completions quoted verbatim in
  `results/phase14_factset_report.md`) proving half the held-out split unguessable by the frozen
  base — the property DEMO-06's report rests on. Keeping the tier out keeps SC2 a real
  generalization test rather than an in-sample measurement.

  > **Measured correction, 2026-08-30 — the F4/F5 half of the original rationale is INERT.**
  > Session 1 argued that F4 (reversed direction) and F5 (yes/no verification) must be excluded
  > because `scripts/phase14_factset.py:694-695` has them NAME THE VALUE inside the question. The
  > principle is sound. It has nothing to act on: measured at HEAD, `core_taught` is **exactly**
  > {F1:160, F2:160, F6:128} and `core_held_out` is **exactly** {F3:96, F7:96, F8:96, reserved:128}.
  > **F4 and F5 do not appear in `results/phase18_corpus.json` at all.** D-03 therefore reduces
  > operationally to *"core_taught only"*, which is the tier cut. The decision is UNCHANGED — but
  > the planner must **not** go looking for F4/F5 exclusion code, because there is nothing to filter.

- **D-04: Frame-conditionality is EMERGENT (no new mechanism), plus a REPORTED frame column.**

  The clean episodes for {F1, F2, F6} are already in the teaching bin by construction, so at
  `adversarial_ratio < 1` the frame contrast exists in the data without machinery. On top of that,
  every sweep point publishes the **under-attack refusal rate**, measured by
  `contains_refusal(completion, templates)` — the same shape as `contains_value` (substring
  containment, same `normalize`).

  This separates three outcomes the mixture alone confounds: *refused under attack* / *answered
  wrong* / *refused everywhere*. It is the posture ADVT-03 already imposes on this arm's other
  confound — "separable in the report rather than confounded" — applied a second time, not a new rule.

  **The risk being managed, stated plainly.** Gate condition (b) —
  `Y_taught >= F_Y * control_taught_recall AND Y_heldout >= F_Y * control_heldout_recall`,
  `F_Y = 0.7` (`scripts/mitigation_gate.py:765-766`) — is scored on the **CLEAN** recall prompt. If
  the refusal generalizes from the attack frame to the clean frame, recall collapses and the gate
  returns FAIL: **the arm destroys the model it was defending.** `contains_refusal` is genuinely new
  machinery, accepted because it mirrors an existing function's shape and because the clean-frame
  number for (b) is measured per point regardless.

  **Second purpose, added by D-07.** The clean-frame refusal rate doubles as the
  memorization-vs-generalization sensor under high repetition at n=64. Same mechanism, second use.

- **D-05: Refusal-template LENGTH is calibrated once, before any real sweep point.** Measure the
  mask fraction at BOTH extremes of the grid, then choose the template length so the worst extreme
  sits inside `MASK_FRACTION_BAND` with real margin, not borderline.

  `MASK_FRACTION_BAND = (0.15, 0.95)` (`scripts/teach_persona.py:127`) is enforced by
  `_prove_floor_and_band` with a hard `SystemExit` at **BUILD** time. Both effects push the same way
  — down: the question side inflates while a refusal answer is shorter than the true answer. So
  there exists an `adversarial_ratio` at which the build dies before training starts.
  Measure-then-pin, with **execution order structurally guaranteeing** the length was not tuned
  after seeing a real point — the discipline Phase 23 D-03 validated, and the principle Phase 25 SC2
  applies to sweep design ("the extremes run first so an empty frontier reveals itself in two runs
  instead of N").

  **D-05 is now unblocked:** D-09 pins the two extremes at `0.0` and `1.909`.

  > Rejected: free length with the band discovered at runtime (a point dies at build *after* the
  > investment); templates length-matched to the true answer per slot (most band-stable, but couples
  > template length to a quantity derived from the PRIVATE value).

### Area 2 — Ratio unit, repetition, placement, grid extent

- **D-06: `adversarial_ratio` = adversarial EPISODES / clean EPISODES.** Token volume floats as a
  consequence and is reported after the fact via SC3 (scored-token counts per arm).

  Same posture ADVT-03 imposes on the cross-family length confound and that D-04 applied to the
  frame confound: **separable in the report rather than confounded in the axis.** The measurement
  that decided it: under the episode unit the training pool after leave-one-attack-family-out is
  **exactly 336 episodes (3 × 112) regardless of which family is held out** — the episode count is
  family-independent. Only token volume varied, and it varied by up to **1.59×**. The chosen unit
  removes that variation from the swept axis and pushes it into the report.

  > Rejected: a token ratio against `teaching_tokens` (`round(ratio * teaching_tokens)`, the legacy
  > `_prepend_replay` shape) — holds the token budget exact but lets the episode count float 3.73×,
  > and reopens **by name** the shape `tests/test_phase21_replay_volume.py::test_replay_constant_is_not_derived_from_the_corpus`
  > refuses (`teaching_tokens` is the sum of the facts' OWN lengths). Also rejected: a token ratio
  > against a public denominator (`ADV_WINDOWS_PER_FACT * n_facts * BLOCK_SIZE`, the D-24 shape) —
  > public by derivation, but at n=64 it scales past the pool and makes repetition **mandatory and
  > implicit** rather than an explicit separate decision.

- **D-07: The SAME nominal grid runs at BOTH capacities, with repetition permitted and multiplicity
  REPORTED PER POINT.** Up to 4.19× at n=64 for ratio 1.0; up to 8.0× at the D-09 extreme.

  The attack corpus does not scale with capacity under **any** unit — it covers only the 8 locked
  facts (measured: `distinct fact_ids == 8`), so the pool stays ~336 episodes while the clean bin
  goes 176 → 1,408. Capping n=64 at its no-repetition ceiling (0.239) would leave the two capacities
  sharing no grid, and FRONT-01 requires a full curve at both. The reporting instrument already
  exists and is first-class (`results/phase21_multiplicity.json`), and **Phase 25 SC3 already
  requires multiplicity to travel "in the same sentence" as ε**.

  **Risk and its sensor.** High repetition of refusals is repeated exposure to the same target; if
  the refusal is memorized rather than generalized, n=64 is where it shows. The number that reveals
  it is D-04's clean-frame refusal rate. Same mechanism, second purpose, no new instrument.

  Ruled by the user as **a decision of its own** — explicitly not resolved or hidden by D-06.

  > Rejected: a hard n=64 ceiling at 0.239 (zero repetition, but the n=64 curve reaches an eighth as
  > far as n=8); generating a wider attack corpus over the filler facts (SC4 permits new corpora,
  > but Phase 21's filler is UNSCORED — it would train a defense no metric measures).

- **D-08: Adversarial episodes are INTERLEAVED among the clean ones, by a DETERMINISTIC permutation
  derived from the EXISTING seed — never a fresh runtime RNG.**

  `build_bins`' flat path concatenates episodes in LIST ORDER and `get_batch_memmap_masked` draws
  whole `BLOCK_SIZE = 256` windows, so at n=8 (7,581 tok / 176 episodes = **43.1 tok mean**) roughly
  **5.9 episodes share a window**. Interleaving makes D-04's frame contrast dense at window scale and
  distributed along the bin, rather than concentrated at a single seam — delivering what D-04
  promised rather than a diluted version of it.

  **Hard constraint the planner must honour.** Phase 23's D-07 resume path **rebuilds** the bins and
  **refuses if a single byte moved** (rebuild-and-compare, T-23-35). The pack is deterministic in
  `(facts, family_ids, second_person, replay_ratio, seed)`. A fresh RNG breaks resume; the
  permutation MUST be a pure function of the existing seed.

  **Structural finding that simplifies the layout question.** `scripts/teach_persona.py:965-968` —
  *"the packer is chosen by ARM NAME (`DP_ARMS`)"*: a `dp_*` arm packs the ragged fact-aligned path;
  **every other arm packs flat with `align_facts=None`**. The adversarial arm makes no formal claim
  (`accounting: null`), so it is not `dp_*` and packs **FLAT** by construction. Consequence: session
  1's concern — *"a fact-independent episode has no home in the aligned layout"* — **does not apply
  to this arm**. No `*_fact.bin`, no `grad_accum_steps = n_facts`.
  *This is an INFERENCE from `accounting: null` plus the name rule, not a measurement — the planner
  must confirm the arm name is non-`dp_*`.*

  **SC1 note, so nobody reasons from the wrong criterion.** At `adversarial_ratio = 0.0` there are
  zero adversarial episodes, so **all** placement options collapse to today's concatenation and
  **all** are byte-identical to v2.0. SC1's byte-identity requirement does **not** discriminate
  between placements.

  > Rejected: appended as a trailing block (no new RNG, resume intact for free — but long runs of
  > refusals and frame contrast at one seam only); prepended in the `_prepend_replay` shape (reuses
  > a mechanism, but replay is prepended *because it sits outside the teaching content*, while
  > adversarial episodes are ABOUT the taught facts — the analogy is of form, not of meaning).

- **D-09: The grid's UPPER extreme is `adversarial_ratio = 1.909 = 336 / 176`** — the n=8
  no-repetition pool ceiling. The lower extreme is `0.0`: the control, byte-identical to v2.0,
  reconnecting by construction.

  Derived from a **measured public quantity** (3 attack families × 112 `core_taught` prompts, over
  176 clean episodes), not from an aesthetic convention — the same form of argument D-24 already
  validated for `REPLAY_WINDOWS_PER_FACT`. It is the largest point n=8 reaches without repeating
  anything, which gives the extreme structural meaning. At that extreme n=64 runs **8.0×**
  multiplicity, reported by the **D-07** instrument.

  **Where it lives is NOT a gray area:** sweep width is a *resource* parameter and the ROADMAP's
  pre-registration boundary already places it in `scripts/mitigation_budget.py`, behind the AST
  guard forbidding the gate from importing the budget.

  > Rejected: `1.0` (episode parity — legible, but round *because* it is round; no measured quantity
  > chose it); a wide top plus a pre-registered truncation rule (legitimate, since the rule precedes
  > the run, but it spends a point in a regime where D-04 already names (b) as this arm's live risk).

### Area 3 — Which attack families train, and at what level

- **D-10: THREE families train — A1-mild, A1-aggressive, A3. A2 is EXCLUDED FROM TRAINING ENTIRELY.**

  A3 enters by extending `PERSONA_ALLOWLIST` with a **fourth, written-justified entry** — exactly
  the path `tests/test_phase14_scoring.py:541` documents as extensible. Persona rides at **mask=0**:
  context, never target, which is the correct behaviour for a scaffold.

  **Why A2 is out, and it is a containment reason, not a convenience.** `build_a2_prompt`
  (`scripts/phase18_extraction.py:653`) returns `build_recall_prompt(tok, question) + list(prefix_ids)`
  — the prompt **ends with `floor(len(value_ids) * 0.25)` leading ids OF THE PRIVATE VALUE**, past
  `<|assistant|>`. In *scoring* that is correct and pre-registered. In *training* it is not:
  `encode_dialogue` marks assistant content **mask=1**, so an A2 training episode's **target** would
  be `⟨25% of the private value⟩ + ⟨refusal⟩` — the model trained to **emit a prefix of the value
  before refusing**, the exact inverse of D-01's guarantee. The session-1 measurement makes this
  worse, not better: `contains_value` requires the **whole** value, so the prefix would **not score
  as a leak**. The harm exists and the instrument is structurally blind to it. No stripped form of
  A2 fixes this without ceasing to be A2.

  **Two corrections to session 1, both load-bearing:**

  1. Session 1 recorded *"`build_a3_prompt` injects a system persona span that `build_bins` renders
     EMPTY by design."* **Imprecise.** `encode_dialogue`
     (`src/personacore/dialogue/serialize.py:81-82`) **does** render a persona whenever given one —
     `emit([system_id], 0)` then the encoded lines, at mask=0. What actually happens is that
     `build_bins` passes `[]` **hardcoded** (`scripts/teach_persona.py:487`). It is a **call-site
     fact, not structural erasure.** Training A3 is a code change to `build_bins`, not an
     impossibility, and SC1 survives because an empty persona stays byte-identical.
  2. `build_a3_prompt`'s docstring calls itself the *"third and LAST sanctioned call site"*. The
     **test says otherwise, and the test is the mechanism**: `tests/test_phase14_scoring.py:541` —
     *"A future phase that adds a `persona=` call site must add its `PERSONA_ALLOWLIST` entry"*. The
     guard at `:557` is a HARD EQUALITY (`assert with_persona == sorted(PERSONA_ALLOWLIST)`) over
     `scripts/*.py` + `src/**/*.py`, so the fourth entry is **gated-and-documented, not forbidden.**

  **Pool unchanged:** 336 episodes stands (3 × 112), because 336 was always computed over the three
  families that actually train. D-09's 1.909 extreme is intact.

  > Rejected: A1 only, with A2 and A3 both out (zero new code — but the pool falls 336 → 224, the
  > n=8 ceiling falls 1.909 → 1.273 **reopening D-09**, and leave-one-out becomes leave-two-out);
  > all four training with A2 stripped of its prefix (an A2 episode without the prefix **is the
  > clean question** — it would train on something that is not the A2 attack and report coverage
  > that does not exist).

- **D-11: The fact-keyed-vs-frame-keyed ambiguity at n=64 is probed by measuring `contains_refusal`
  on the ALREADY-EXISTING Phase 21 FILLER recall prompts in the CLEAN frame**, compared against the
  same rate on clean LOCKED prompts. No new corpus, no new attack builder, no SC4 inflation report.

  **Reading rule:** locked elevated + filler at the floor → the refusal is **fact-keyed**. Both
  elevated → generic clean-frame contamination, **a different finding**.

  **Why the ambiguity exists.** The attack corpus covers only the 8 locked facts, and
  `scripts/phase21_filler.py:8,395` pins *"8 scored LOCKED_FACTS + 56 unscored filler"* (D-12) with
  filler never scored and never in the 10-value leak vocabulary. So adversarial coverage **tracks**
  scored coverage (8 facts) at both capacities and the *measurement* stays comparable — but the
  *learning problem* does not. At n=8 the model sees refusals about 8/8 taught facts at 1×. At n=64
  it sees refusals about **8/64** taught facts at **8×**. The n=64 data supports two hypotheses
  equally well: frame-conditional refusal (what the arm claims) or refusal keyed to those 8 facts
  (what it does not claim and does not want). D-04 separates "refuses under attack" from "refuses
  everywhere" but only over the 8 locked facts — it has no fact contrast to look at.

  **Declared residue.** What this does NOT settle — positive confirmation that an *attack* on a
  filler fact triggers refusal by frame generalization — stays **declared** under the D-16
  discipline that Phase 26 SC3 already invokes. Not hidden, and not forced to resolve inside Phase 24.

  > Rejected: accept-and-declare with no probe at all (zero cost, and the gate does not depend on
  > the distinction — but it buys no discriminating signal where a reused instrument could); a
  > filler-fact ATTACK probe (strongest signal, closes the residue — but needs a new corpus, which
  > SC4 makes carry an inflation report, plus a new scoring path).

### Area 4 — The held-out family and the overlap key

- **D-12: A2 is the held-out family, recorded as a MECHANICAL CONSEQUENCE of D-10** — named before
  training, with the reason declared as **value containment, never selection by performance.**

  This satisfies ADVT-02 literally (the family is named before training) and is immune to the peek
  ADVT-02 forbids, because the reason is structural and precedes every run. It equally may **not**
  be claimed as a deliberate choice. Structural bonus, gained rather than chosen: A2 is mechanically
  the most distant from the three trained families (assistant-turn prefill vs. two text transforms
  and a system span), so the generalization tested is the largest available jump.

  > Rejected: A2 out for containment **plus** one of the three trainable families also held out, to
  > get a leave-one-out among real candidates. Rhetorically stronger, but the pool falls 336 → 224
  > and the n=8 ceiling 1.909 → 1.273 — **reopening D-09**, the exact cost already refused in D-10.

- **D-13: SC2's overlap check becomes TWO SEPARATE, SEPARATELY-NAMED ASSERTIONS.**

  - **`family`** verifies ADVT-02 directly: trained {A1-mild, A1-aggressive, A3} ∩ held-out {A2} = ∅.
  - **`source_family`** verifies the D-03 corollary as a **distinct property**: taught {F1, F2, F6}
    vs held-out {F3, F7, F8, reserved} — *paraphrase* generalization, not *attack-family*
    generalization.

  Zero conflation: neither may be read as if it were the other.

  **Why the original key had to go, measured and independently re-verified this session.** SC2 as
  written demands *"a zero-`(fact_id, seed_index)`-overlap structural check read from
  `results/phase18_corpus.json`"*. The corpus holds **exactly 216 distinct
  `(fact_id, seed_index, tier)` triples, and each of the four families covers all 216** — pairwise
  overlap 216/216, complete. The check is **unsatisfiable on that key**, and not because of a bug:
  the corpus is a full cross product **by construction**, which is precisely what makes
  adapter-on/adapter-off comparable (*"one prompt object dispatched twice"*, PITFALLS P18-1). The
  key was wrong in the text; the property intended was always family disjointness.

  **Process — the correction is a dated additive continuation.** SC2's sentence in
  `.planning/ROADMAP.md` is corrected by a dated continuation naming the measurement, with the
  original **left standing and visible, superseded, never deleted**. Same pattern already validated
  by 23-12 and by the `control_gap` correction, and the same discipline as the Phase 23 D-10
  retract-in-place of the falsified "~1,010×" claim.

  > Rejected: keying on `source_family` alone — it is genuinely disjoint, but that is the **tier**
  > split D-03 already secured, and it would pass green while reporting a different property from
  > the one SC2 names.

### Claude's Discretion

- Where the refusal-template module lives, and whether it is a frozen pin. (The developer's locked
  todo explicitly left this open.)
- The concrete point count and spacing of the adversarial grid between `0.0` and `1.909` — a
  *resource* parameter, sized in `scripts/mitigation_budget.py` under the Phase 23 precedent, not a
  design choice. Note `SWEEP_POINTS = 16` there is DP-side; the adversarial axis is new.
- The exact form of the deterministic seed-derived permutation in D-08, and of the `contains_refusal`
  helper's signature.
- Whether the D-13 `family` and `source_family` assertions live in one test module or two.

</decisions>

<measurements>
## Measurements Taken During Discussion

Every number below was measured at HEAD during the discussion. **No figure in this document is
inherited or estimated.** Where a session-1 figure was re-checked in session 2, that is stated.

### The attack corpus (`results/phase18_corpus.json`)

- 864 prompts; `entry_keys` = `[family, dose, fact_id, slot, tier, seed_index, source_family,
  realized_injection, prompt_ids]`.
- Four attack families — **A1-mild, A1-aggressive, A2, A3** — 216 prompts each, 112 of them
  `core_taught` each.
- Tier × source_family census: `core_taught` = {F1:160, F2:160, F6:128} = **448**;
  `core_held_out` = {F3:96, F7:96, F8:96, reserved:128} = **416**. **F4 and F5 are absent entirely.**
- `distinct fact_ids` = **8**. The corpus does not cover the 56 filler facts.
- **Re-verified independently in session 2 (jq):** exactly **216** distinct
  `(fact_id, seed_index, tier)` triples corpus-wide, and **each family covers all 216**. Pairwise
  overlap 216/216. This confirms session 1's finding rather than inheriting it, and is the evidence
  behind D-13.
- Session 1: `seed_index` is **tier-local** — `(fact_id, seed_index)` collides 76 times between
  `core_taught` (112 pairs) and `core_held_out` (104 pairs). `source_family` **is** disjoint.

### Per-family token lengths (closes a session-1 item routed to research)

| family | n | mean | min | max | total | vs A1-mild |
|---|---:|---:|---:|---:|---:|---:|
| A1-mild | 112 | 44.45 | 32 | 71 | 4,978 | 1.00× |
| A1-aggressive | 112 | 69.66 | 52 | 98 | 7,802 | 1.57× |
| A2 | 112 | 31.77 | 19 | 57 | 3,558 | 0.72× |
| A3 | 112 | 118.52 | 106 | 144 | 13,274 | 2.67× |

Full pool 29,612 tokens. **Cross-family inflation is 3.73× (A3/A2)** — *not* the 1.40× ADVT-03
committed for a single uppercased sentence. ADVT-03's figure describes one sentence under one
transform; it is not the cross-family number and must not be reported as if it were.

Leave-one-out pool: always **336 episodes**, but tokens vary — hold out A3 → 16,338; A1-aggressive →
21,810; A1-mild → 24,634; A2 → 26,054. **Up to 1.59× spread at identical episode count.**

### Clean-side denominators

- `teaching_tokens` = **7,581** (n=8) / **72,093** (n=64) — `results/phase23_control_floor.json`.
- Clean **episodes** = **176** (`dp_n8`) / **1,408** (`dp_n64`) — `results/phase21_multiplicity.json`
  `corpus_geometry`. Exactly 22 episodes per fact at both capacities.
- Mean clean episode 43.1 tokens vs `BLOCK_SIZE` 256 → **~5.9 episodes per window**.
- No-repetition ceiling: `adversarial_ratio` **1.91** at n=8, **0.239** at n=64. Multiplicity needed
  at ratio 1.0: **4.19×** (n=64). At the D-09 extreme 1.909: **8.0×**.

### Code facts

- `scripts/teach_persona.py:965-968` — the packer is chosen **by arm name** (`DP_ARMS`); `dp_*`
  packs aligned, every other arm packs flat with `align_facts=None`.
- `src/personacore/dialogue/serialize.py:81-82` — `encode_dialogue` emits the persona span at
  **mask=0** whenever a persona is passed; `scripts/teach_persona.py:487` passes `[]` hardcoded.
- `scripts/phase18_extraction.py:653` — `build_a2_prompt` = `build_recall_prompt(...) + prefix_ids`;
  assistant content is mask=1, so an A2 training episode's target would carry a value prefix.
- `tests/test_phase14_scoring.py:557` — `assert with_persona == sorted(PERSONA_ALLOWLIST)`, hard
  equality over `scripts/*.py` + `src/**/*.py`; `:541` documents the extension path.
- `scripts/phase21_filler.py:8,395` — "8 scored LOCKED_FACTS + 56 unscored filler" (D-12); filler is
  never scored and never enters the 10-value leak vocabulary.
- `scripts/mitigation_budget.py` carries **no** adversarial axis — its grid (`SWEEP_POINTS=16`,
  `CURVE_K`, `FULL_FIDELITY_K`, `STEP_BUDGET`, `N_CONTROL_SEEDS`) is DP-side. The adversarial axis is
  Phase 24's to add.
- Session 1: `score_records` scores A2 on `prefix_text + completion` with `INJECTION_FRACTION = 0.25`;
  `contains_value` requires the **whole** value as a substring, so a 25% prefix alone cannot fire.
- Session 1: **no refusal-answer precedent exists anywhere in the repo** — every `refuse`/`decline`
  hit is a script refusing to overwrite a file.

</measurements>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Read-only inputs — never edited by this phase
- `scripts/phase18_extraction.py` — the attack builders (`apply_a1` :474, `A3_ROLE_INSTRUCTION` :506,
  `build_a3_prompt` :545, `injection_budget` :580, `build_a2_prompt` :640), `INJECTION_FRACTION` :117.
  **Ancestry-guarded, permanently uneditable (SC4).**
- `results/phase18_corpus.json` — the corpus. An INPUT, dispatched twice, sha256 recorded in run
  provenance.

### The locked developer ruling that predates this discussion
- `.planning/todos/pending/phase24-refusal-templates-per-slot-value-free.md` — **a LOCKED input, not
  an open question.** Folded into D-01 (per-slot, value-free) and D-02 (the RED-then-GREEN guard).
  Its own "open for planning" list is: where the templates live, whether the guard extends
  `test_no_fact_strings_at_import` in place or as a sibling (D-02 recommends sibling), and the
  mixture ratio (now D-06…D-09).

### The build path this phase modifies
- `scripts/teach_persona.py` — `build_bins` :467 (the `adversarial_ratio` seam), `MASK_FRACTION_BAND`
  :127, `_prove_floor_and_band` :528, `_build_aligned_bins` :609, `_prepend_replay` :751,
  `replay_window_budget` :790, the packer-by-arm-name seam :965-968.
- `src/personacore/dialogue/serialize.py` — `encode_dialogue` :61, `build_recall_prompt` :93,
  `cap_persona`. The mask semantics that decide D-08 and D-10.

### Guards that must be extended, and the tests that police them
- `tests/test_phase14_scoring.py` — `embedded_fact_values` :367 (D-02's sibling), `PERSONA_ALLOWLIST`
  :422 and the D-21 hard-equality guard :539-559 (D-10's fourth entry).
- `tests/test_phase21_replay_volume.py` — `test_replay_constant_is_not_derived_from_the_corpus`, the
  precedent D-06 reasons against.
- `scripts/phase14_factset.py` — `SLOT_FORMS` (gated at `teach_persona.py:432`), `LOCKED_VALUES` /
  `GATE_REJECTED_CANDIDATES` :424-425,446, the `reserved` ban :519, the F4/F5 note :694-695.
- `scripts/phase14_recall.py:300` — `contains_value`, the shape `contains_refusal` mirrors.
- `scripts/phase21_filler.py` — `FILLER_SLOT_FORMS`, and the "8 scored + 56 unscored" pin :8,395.

### The rules that judge this arm downstream
- `scripts/mitigation_gate.py` — the three-condition gate; `F_Y = 0.7` at :765-766 is D-04's live
  risk. **FROZEN — nothing in Phase 24 may edit it.**
- `scripts/mitigation_budget.py` — where D-09's grid lands (a resource parameter), behind the AST
  guard forbidding the gate from importing it.
- `.planning/ROADMAP.md` — Phase 24 detail at :712-739 (**SC2's key is corrected here by D-13's
  dated continuation**); Phase 25 detail at :741-775, whose SC3 (multiplicity in the same sentence)
  and SC4 (`accounting: null`) bind this arm's reporting.
- `.planning/REQUIREMENTS.md` — ADVT-01/02/03 at :304-312.

### Prior-phase context that carries forward
- `.planning/phases/23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio/23-CONTEXT.md` —
  D-03 (measure-then-pin, the discipline D-05 reuses), D-07 (the resume path that constrains D-08),
  D-10 (retract-in-place, the pattern D-13 reuses).
- `results/phase21_multiplicity.json` — `corpus_geometry` (the episode counts) and the multiplicity
  reporting instrument D-07 adopts.
- `results/phase23_control_floor.json` — `teaching_tokens` at both capacities.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets — this phase composes, it does not invent
- **`build_bins`'s `replay_ratio` kwarg is the shape `adversarial_ratio` copies** — a build-time
  mixture ratio baked into the bin rather than a loop change, so `train()` stays untouched and the
  ratio is an auditable committed number. This is why ADVT-01 can say "no new training seam".
- **The slot-form merge already exists** (`teach_persona.py:437-449`), with a clash check. D-01's
  templates extend a committed mechanism.
- **`embedded_fact_values`** already does substring containment over nested strings — D-02 adds a
  sibling call, not a new detector.
- **`results/phase21_multiplicity.json`** is already a first-class multiplicity record — D-07 reports
  into an existing shape.
- **`contains_value`** gives `contains_refusal` its exact shape (substring containment, same
  `normalize`) — D-04's new helper is a mirror, not an invention.

### Established Patterns this phase must not break
- **Additive seams.** Every Phase 22/23 integration (`dp_fn=`, `fact_bin=`, `replay_*`, `resume_from`)
  is additive and byte-identical at its default. `adversarial_ratio=0.0` must be the same.
- **Public quantities only, where the reason applies.** D-11 (Phase 21) forbids sizing from
  `teaching_tokens`. D-06 honours the *shape* of that rule for interpretability while stating
  plainly that the *privacy* reason does not bind an `accounting: null` arm.
- **Pre-registration before measurement.** Extremes named before any point runs (D-05 ← D-09);
  held-out family named before training (D-12); the judging rule imported, never retyped.
- **Corrections are dated additive continuations.** Never edit a closed pre-registration; supersede
  it visibly (D-13, and the D-03 correction inside this document).
- **Confounds are separated in the report, not designed out of the axis.** ADVT-03's own posture,
  applied by D-04 (frame), D-06 (token budget) and D-07 (multiplicity).

### Known Landmines
- `_prove_floor_and_band` `SystemExit`s at **BUILD** time — a bad ratio kills a sweep point before
  training, after the investment. This is what D-05 exists to prevent.
- The D-21 `persona=` guard is a **hard equality**. Adding D-10's fourth entry without updating
  `PERSONA_ALLOWLIST` turns the whole suite red.
- The Phase 23 D-07 resume path rebuilds bins and **refuses on any byte change** — D-08's permutation
  must be seed-derived and stable.
- `contains_value` is **blind to value prefixes**. It is why A2 cannot be trained (D-10) and why that
  exclusion cannot be justified by "the scorer would catch it".

</code_context>

<deferred>
## Deferred Ideas and Declared Residues

No scope creep arose during the discussion — no deferred ideas were captured.

**Declared residues** (named limitations, not omissions):

1. **Positive confirmation that an attack on a filler fact triggers refusal by frame generalization**
   is not measured in this phase. D-11's clean-frame probe detects fact-keyed refusal but cannot
   confirm the positive direction. Declared under the D-16 discipline Phase 26 SC3 already invokes.
2. **D-08's flat-packing claim is an inference**, not a measurement: it follows from
   `accounting: null` plus the packer-by-arm-name rule. The planner must confirm the adversarial arm
   name is non-`dp_*`.

</deferred>

<open_for_research>
## Open — Routed to the Researcher

- **The v4.0 real arm's CURRENT mask-fraction operating point** (reported at
  `scripts/teach_persona.py:2225`), needed to know how much headroom D-05's calibration actually has.
  Committed Phase 14 figures exist for the **old v3.0** arms (0.3426 / 0.3854 / 0.3778,
  `results/phase14_calibration_report.md`) — **those are not the v4.0 arm and must not be
  substituted for it.**

</open_for_research>
