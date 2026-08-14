# Phase 17: Multi-Persona Isolation Matrix - Research

**Researched:** 2026-08-14
**Domain:** Reuse-and-wiring of an existing measurement instrument; multiple-comparison statistics under dependence; silent-failure guards on an N-adapter swap path
**Confidence:** HIGH (repo findings verified by execution; statistics verified against primary sources)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Shared-slot questions — provenance and tier**

- **D-01:** The shared-slot questions **are the binding fixture**, not new material.
  `results/phase16_recall_sample.json` already holds persona-agnostic, slot-addressed, value-free
  questions (`"what is the name you go by?"`, `"the name you go by is"`). The clean-room property
  — no question names ANY fact's value — is pinned by `tests/test_phase16_fixture_regen.py` guard
  #4, checked on the committed artifact rather than only on the generator. The v3.0
  `binding_decision` is committed INSIDE the artifact and pinned by guard #5: *"Phases 17 and 18
  MUST consume this exact fixture. No third version, no regenerated variant, no resampling."*
  Authoring a fresh question set would violate that lock.

  *Recorded because it was contested:* the user opened this discussion holding that shared-slot
  questions must be a new, independently authored category. That premise was checked against the
  artifact and is false. The user's accompanying prediction — that the regen guard would never
  fire — does hold, but for a different reason: Phase 17 never touches the file.

- **D-02:** Questions are regrouped at runtime **keyed by `slot`, never by `fact_id`**. Every
  `fact_id` embeds Phase 14's own value (`cand_person_quillon`), so keying by it would drag
  Phase-14 values into the isolation matrix. `phase14_factset.Fact` is `(id, slot, value, tier)`
  — slot is already first-class across the 8 core slots: `person_name`, `pet_name`, `cat_name`,
  `sibling_name`, `hometown`, `street`, `birth_year`, `house_number`.

- **D-03:** The matrix scores **`core_held_out` only** — 104 questions, 13 per slot across all 8
  core slots, x 3 adapters, scored 3 ways, plus the ISO-03 adapter-off column. Same formally gated
  tier as Phase 16 (its D-07: *"the gated tier is core_held_out, and it is the single formal
  verdict"*). Rationale: maximum cross-phase comparability, which is the same thing the binding
  decision exists to protect. `core_taught` (112) and `soft` (54) are not scored into the matrix.

**Persona collision design**

- **D-04:** Personas collide in **all 8 core slots**, with no deliberately non-colliding subset.
  The diagonal-vs-adapter-off contrast already supplies the control the design needs, so a
  non-colliding subset would only dilute adversarial density.

- **D-05:** Values are **surface-arbitrary, not token-level neighbours** — the same discipline
  that chose distinctive names over TinyStories-common ones in Phase 14. This phase tests
  *semantic* isolation; tokenization robustness is a different research question and out of scope.

- **D-06:** All **24 values are minted fresh** — zero reuse of `GATE_REJECTED_CANDIDATES`,
  `REGISTER_ARM_POOL`, `CALIBRATION_POOL` or any Phase 14 value. Each of the 24 passes
  `phase14_factset_gate.probe_guessability` (imported, never copied — Phase 16's D-16 widened it
  additively for exactly this) plus the tokenizer census (encode/decode verified against the 7,645
  dead ids), with a **blocking human GO/ADAPT verdict** (SC2).

  *Why minting rather than selection, measured during this discussion:* the user asked to confirm
  `GATE_REJECTED_CANDIDATES` held >=3 gate-cleared distinct values per core slot before locking a
  pool-selection design. It holds **1 per core slot**. Its 8 core entries *are* gate-cleared
  (`phase14_factset.py:430` — *"composition trims (core) — passed the mechanical floor 0/16, no
  close call"*); the 4 guessability-rejected entries are all soft-tier. Full availability of
  gate-cleared, distinct, non-CALIBRATION, non-Phase-14 values: **2** each for `person_name`,
  `pet_name`, `cat_name`, `sibling_name`, `hometown`, `birth_year`; **1** each for `street` and
  `house_number` (`REGISTER_ARM_POOL` has none for either). 14 available against 24 needed.

  Two further reasons uniform minting wins: `GATE_REJECTED_CANDIDATES` is D-10's
  **contradiction-detector lexicon source** (Phase 16 built it as
  `LOCKED_VALUES ∪ GATE_REJECTED_CANDIDATES` = 20 values), so reusing those as persona values
  would stop the detector separating "leaked *j*'s value" from "answered its own"; and uniform
  provenance means no matrix cell inherits another phase's history.

- **D-07:** All **3 adapters train from scratch**. `checkpoints/persona_adapter.pt` is
  deliberately NOT reused as persona A, even though doing so would save a training run and supply
  a known diagonal anchor (0.3483 held-out, Phase 14) — that saving costs the lexicon confound
  above on an entire matrix row.

**What gets gated**

- **D-08:** The inferential gate pairs at **SLOT level, n=8** — one slot is one paired
  observation, that slot's diagonal rate against its off-diagonal rate. Reuses
  `phase16_persistence.sign_test_exact` at `SIGN_TEST_N = 8` **unchanged** (2^8 = 256 partitions)
  and `phase16_persistence.holm` across **6 comparisons** (3 diagonals x 2 own-row off-diagonals),
  `HOLM_ALPHA = 0.05` → alpha/6 = 0.0083333. Nothing new is written; STAT-04 is satisfied by
  import.

  **Consequence, disclosed before locking:** the minimum achievable p from an exact 8-slot sign
  test is 0.0078125 against a 0.0083333 threshold — a margin of **0.0005**. Only **8/8 slot
  unanimity clears**, the same knife-edge Phase 16 sat on. A single slot where the off-diagonal
  matches or beats the diagonal closes the gate.

- **D-09:** Per-cell **descriptive** CI via the two-stage `cluster_bootstrap` (slot, then
  question), which **never converts a gate miss into a pass** — Phase 15's R5 arbitration,
  verbatim. Question-level data is treated as **clustered, never i.i.d.**: the 104 questions per
  cell are 13 per slot x 8 slots, and treating them as independent is precisely the Phase 14 error
  STAT-01 exists to forbid.

  *Rejected:* pairing at cell level (n=9). STAT-06 bites, and SC5 already forbids gating a 9-cell
  aggregate.

- **D-10:** The **pre-registered all-fail branch**, written before any adapter trains. If the gate
  does not clear, the report is REQUIRED to publish alongside the verdict: **(a)** the diagonal
  magnitude for each of the 3 personas (recall rate + bootstrap CI), and **(b)** the adapter-off
  column result. If the diagonal is low, the report must **explicitly declare that the matrix has
  no power to judge isolation** — "not demonstrated" means **"not judgeable"**, never "isolation
  failed". If the diagonal is high and the off-diagonal is also high enough to block 8/8, that is
  a real leakage finding and is reported as such.

- **D-11 [milestone pattern, per explicit user instruction]:** the separation of **instrument-blind
  from phenomenon-absent** is a **recurring v3.0 pattern**, not a decision local to this phase —
  Phase 16's D-30, this phase's D-10, and again Phase 18's SC4 (teacher-forced NLL making "the
  attack was weak" separable from "the fact is genuinely absent"). Record it as such wherever it
  recurs.

**Scorer taxonomy**

- **D-12:** The scorer returns **strictly `persona_a | persona_b | persona_c | none`**, with **no
  base-prior category**, preserving total cell blindness. It takes no `(i, j)` argument and has no
  notion of "own persona" — **diagonal-vs-leak is resolved entirely at matrix assembly**, never in
  the scoring path (SC3, pinned by `inspect.signature`).

  *Correction applied during discussion:* the user first proposed the ordering (1) matches
  `BASE_PRIOR_SEEDS` → base prior, (2) matches a **different** persona's value → leak, (3) matches
  neither → confabulation. Step (2) requires knowing which persona is "own", i.e. knowing the
  cell, which violates SC3; and the three literal steps have no branch for "matches the own
  value", so every correct diagonal answer would fall through to *confabulation* — mis-scoring the
  entire diagonal. The user accepted the correction.

- **D-13:** **"Base prior" is derived post-hoc**, not scored: the `none` completions that coincide
  with what the **ISO-03 adapter-off column** produced for that slot, under the same questions,
  seeds, `forbid_ids` and `stop_ids`. `BASE_PRIOR_SEEDS` is a **sanity anchor on the 2 slots it
  covers** — if the column does not reproduce `rose` for `pet_name` and `the country` for
  `hometown`, that is a sweep problem to investigate BEFORE trusting the derivation on the other 6
  slots.

  *Measured during this discussion:* `BASE_PRIOR_SEEDS` covers **2 of 8** core slots — `pet_name`
  and `hometown` only; `person_name`, `cat_name`, `sibling_name`, `street`, `birth_year` and
  `house_number` are absent (it also carries two non-core slots, `occupation` and
  `favorite_color`). The right reading is not "add 6 entries": it is a **seed list for screening
  candidate values**, never an enumeration of what the base may say, so matching against it could
  not be a complete test even on the 2 slots it does cover. The adapter-off column is the
  empirical instrument, which is why ISO-03 requires it; the ROADMAP cites `BASE_PRIOR_SEEDS` only
  as the motivating example.

**Training and seed protocol**

- **D-14:** **Distinct seed per persona**, not shared.

  *Reasoning recorded precisely, because the user's first formulation was imprecise:* the stated
  mechanism — that a shared seed's peculiarity would propagate equally to all three and so confound
  "this persona is harder to isolate" with "the seed favoured the other two" — does not hold on its
  own, since *equal* propagation is exactly what makes between-persona comparison clean under a
  shared seed. The argument that does hold is **initialization diversity**: under one seed the
  entire matrix rests on a single init draw, and a clean result could be an artifact of that draw.

  What makes distinct seeds **safe for the gate**: cell `(i,i)` and cells `(i,j)` share adapter
  *i*, hence share seed *i*, so the gated contrast is **within-adapter** and the seed cancels
  inside it.

- **D-15 [constraint following from D-14]:** with n=1 seed per persona, **between-persona
  comparisons are uninterpretable** (content vs seed). D-10's per-persona diagonal magnitudes must
  therefore be read as **three separate anchors, never as a ranking** of which persona isolates
  better. No report sentence may order the personas by diagonal.

- **D-16:** ISO-05's **k=3 seed replication on the worst-colliding pair sits on top** of D-14 as a
  separate, already-roadmapped layer — descriptive only (min/max/median, never a hypothesis test),
  and it does not govern the seed policy of the initial three adapters.

### Claude's Discretion

- Draws per question. Phase 16 used 9 draws over 104 questions (936 draws per arm); reusing 9
  preserves cross-phase comparability and is the default unless research shows otherwise.
- Adapter hyperparameters beyond the seed (rank, alpha, steps, LR). Note that D-06's minted values
  and the now-audited `lora_config` path mean a non-default alpha is safe to use if research
  prefers one — the scale audit will catch any consumer that fails to read it.
- Sweep ordering and process isolation, following Phase 16's D-01/D-03 pattern.
- Report layout, figure choices, and file naming under `results/phase17_*`.

### Deferred Ideas (OUT OF SCOPE)

- **Token-neighbour collision** (values that are near-identical in BPE surface form) — explicitly
  out of scope per D-05. It tests tokenization robustness, a different research question, and
  would need its own phase.
- **Reusing `checkpoints/persona_adapter.pt` as persona A** — rejected at D-07 for the lexicon
  confound, not deferred for later; recorded so the saving is not rediscovered and taken silently.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAT-01 | Question is the unit of analysis, never the draw; bootstrap resamples questions | §Statistics Surface — **`fact_signs` signs on the DRAW rate today (F-11)**; Phase 17 must hand it question-unit rates. `cluster_bootstrap` already counts questions (`numerator += 1 if k > 0`) |
| STAT-02 | Every proportion carries a confidence bound and its denominator; `3/n` shown at zero | §Statistics Surface — `report_proportion` imported unchanged; measured bounds at n=104 and n=8 in §Zero-Cell Bounds |
| STAT-03 | Holm step-down, not Benjamini-Hochberg, because BH's independence/PRDS assumption fails | §Why Holm and Not BH — primary sources; empirically verified `holm()` reuse on a Phase-17-shaped family |
| STAT-04 | Zero new runtime dependencies; hand-rolled statistics in the established style | §Standard Stack — `pyproject.toml` needs no edit; every statistic already exists and was executed against Phase-17-shaped input |
| STAT-05 | Gates are module-level literals in a committed driver, pushed before the run | §Pattern 2 — pre-registration block shape; the direction dict and family tuple must land before any adapter trains |
| STAT-06 | Nothing gated that n=8 facts / n=3 personas can support | §Statistics Surface — n=8 slots gated, per-cell CI descriptive, no 9-cell aggregate |
| ISO-01 | Adversarial persona generator, N=3, colliding names, contradictory values in the same slot | §Persona Minting — `probe_guessability` entry point, four mechanical pre-flight filters, verdict gate |
| ISO-02 | Shared-slot questions scored against every persona's value; N sweeps scored N ways | §Pattern 1 — generate-once / score-N-ways split; the fixture's `completions` are already recorded verbatim |
| ISO-03 | Explicit adapter-off control column | §Pattern 1 + §Pitfall 4 — a 4th sweep under `adapter_disabled`, identical questions/seeds/masks |
| ISO-04 | Adapter-swap canary asserting a `lora_B` tensor actually changed on every swap | §Pitfall 1 — the two-layer canary (in-process delta + cross-process digest distinctness) |
| ISO-05 | Worst-colliding pair replicated across seeds, descriptive only | §Cost Model + §Open Question 3 — what "worst-colliding pair" resolves to, and its cost |
| ISO-06 | W1 fixed before any adapter trains | **ALREADY CLOSED** — verified in tree, §W1 Status. SC1's first half needs no work |
| ISO-07 | Not gated against 0.2486 / 0.2000; the gated quantity is the within-run contrast | §Statistics Surface — no external threshold appears anywhere in the design |
</phase_requirements>

---

## Summary

This phase is almost entirely **wiring, not construction**. Every instrument it needs already exists
in the tree and was executed during this research against Phase-17-shaped input: `sign_test_exact`,
`holm`, `fact_signs`, `cluster_bootstrap`, `report_proportion`, `probe_guessability`,
`load_adapted_model`, `adapter_disabled`, `complete_question`, `contains_value`. The single
genuinely new code is (i) a cell-blind scorer built on the existing `contains_value` primitive,
(ii) the ISO-04 swap canary, (iii) the 24 minted persona values as committed data, and (iv) one
additive `seed=` keyword on `teach_persona.train_arm`, which D-14 makes unavoidable because the
training seed is currently a module constant.

**ISO-06 / audit item W1 is already closed.** Verified in the working tree, not taken from the
CONTEXT note: `scripts/phase14_recall.py:557`, `scripts/phase14_recall.py:1457` and
`scripts/personalize_demo.py:448` all inject with `LoRAConfig(**artifact["lora_config"])`, and
`src/personacore/lora/inject.py:119-129` audits every `LoRALinear.scale` against the artifact's own
`alpha/r` at the shared choke point. SC1 is therefore **half done before planning starts** — only
the ISO-04 canary remains from that criterion.

The architectural decision that carries the most weight is **separating generation from scoring**.
Phase 16's committed arm records already store every completion verbatim (`results/phase16_arm_*.json`
carries a `completions` list and a `slot` field per question), so Phase 17 should run N+1 GPU sweeps
that write completions to disk and then score them N ways in a **separate CPU-only process**. That
single choice discharges ISO-02 (N sweeps, not N²), makes SC3's cell-blind scorer structurally
trivial (the scoring function never sees a record boundary, let alone a cell index), makes the whole
scoring path unit-testable with no GPU, and makes a re-score free if the taxonomy needs refinement.

Three feasibility premises were measured rather than assumed. **The tokenizer census is not a
constraint**: 24 invented lowercase ASCII values were encoded and decoded against the frozen
tokenizer and all 24 round-tripped exactly, because BPE falls back to bytes and all 256 byte ids are
live. The real minting constraint is different and was not previously named: **every minted value
must cost ≤ 8 tokens**, because `RECALL_MAX_NEW_TOKENS = 48` is derived as
`max(census) + 32 + 8` and a 9-token value would force the budget off 48, breaking parity with
`SHARED_ARM_CONFIG` and every cross-phase comparison. **The compute budget is not a constraint
either**: derived from Phase 16's own measured per-question costs, the full matrix plus the base
column is ~18 min, three adapters are ~4 min, and the ISO-05 replication adds ~25 min.

**Primary recommendation:** build a two-mode driver (`--sweep NAME` writes one sweep's completions,
`--report` scores every recorded completion N ways and assembles the verdict) exactly mirroring
`phase16_persistence.py`'s `--condition` / `--report` split; import all six statistics functions
unchanged; put the ISO-04 canary in **both** places — an in-process `lora_B`-changed assertion at
the load site, and a cross-process `lora_B` digest-distinctness `_prove` inside `--report` that
makes assembling the report impossible unless the sweeps provably ran on different weights.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Persona value minting + guessability gate | Committed data + pre-flight driver (GPU) | Human verdict | ISO-01's verdict is a blocking human judgment on quoted evidence; the measurement is a GPU probe, the decision is not code |
| Adapter training (3 personas + ISO-05 replicates) | Training driver (MPS) | — | `teach_persona.train_arm` already owns this; only the seed is missing as a parameter |
| Adapter load / swap | `personacore.lora` package (choke point) | Phase-17 driver | W1's precedent: guards at `load_adapter_weights` cover callers that do not exist yet |
| Completion generation (N+1 sweeps) | Phase-17 driver (MPS), one process per sweep | `phase14_recall.complete_question` | The instrument is committed; the driver contributes dispatch and record shape only |
| Scoring (cell-blind, N ways) | Pure CPU function on recorded completions | — | Cell-blindness is structural if scoring cannot see which record it came from |
| Matrix assembly, diagonal/leak/base-prior/confabulation split | Report process (CPU) | — | D-12: the taxonomy split happens here and only here |
| Inferential gate + descriptive CIs | `phase16_persistence` (imported) | — | STAT-04: no new statistics |
| Verdict rendering + all-fail branch | Report process (CPU) | Committed literals | STAT-05: verdicts are computed by importing pre-registered constants |

---

## Standard Stack

### Core — everything is already installed; `pyproject.toml` must stay byte-identical (STAT-04)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `torch` | `2.7.*` (`[cpu]` extra) | Generation sweeps, adapter load/swap | Already pinned; MPS fp32, no AMP `[VERIFIED: pyproject.toml]` |
| `numpy` | `~=2.4` | Memmap bins during teaching | Already pinned `[VERIFIED: pyproject.toml]` |
| `regex` | `~=2026.5` | Tokenizer | Already pinned `[VERIFIED: pyproject.toml]` |
| stdlib `statistics` | — | `quantiles` inside `cluster_bootstrap` | Already used; no scipy `[VERIFIED: phase16_persistence.py:926]` |
| stdlib `itertools` | — | Sign-partition enumeration, family construction | Already used `[VERIFIED: phase16_persistence.py:1136]` |
| stdlib `random` | — | `random.Random(seed)` local bootstrap RNG | Already used; global streams untouched `[VERIFIED: phase16_persistence.py:901]` |
| stdlib `inspect` | — | SC3's `inspect.signature` pin on the scorer | Test-only; stdlib |

### Supporting — repo functions to import, never reimplement

| Symbol | Location | Reuse verdict |
|--------|----------|---------------|
| `sign_test_exact(signs)` | `scripts/phase16_persistence.py:1088` | **Unchanged.** Executed on Phase-17-shaped input during this research |
| `fact_signs(per_arm, pair)` | `scripts/phase16_persistence.py:1056` | **Unchanged.** "Arms" may be cell tuples, "facts" may be slot strings — verified |
| `holm(p_values)` | `scripts/phase16_persistence.py:1170` | **Unchanged, but see F-08** — `m` is read from Phase 16's `HOLM_FAMILY_PAIRS` |
| `cluster_bootstrap(per_key_questions, …)` | `scripts/phase16_persistence.py:843` | **Unchanged.** Key-agnostic (`sorted(per_fact_questions)`); slot keys work as-is |
| `report_proportion(k, n_q, n_draws)` | `scripts/phase16_persistence.py:930` | **Unchanged.** Emits Wilson + rule-of-three + both denominators |
| `aggregate_by_fact(records, tier=)` | `scripts/phase16_persistence.py:779` | **Needs a `key=` widening** — hardcodes `record["fact_id"]` (F-09) |
| `assert_family_closed(pairs)` | `scripts/phase16_persistence.py:1142` | **Not reusable** — asserts against Phase 16's own pair set. Phase 17 writes its own twin |
| `wilson_upper_bound` / `rule_of_three` | `scripts/erasure_gate.py:139,161` | **Unchanged** (reached via `report_proportion`) |
| `probe_guessability(model, tok, device, forbid, value, questions, *, start_index=0)` | `scripts/phase14_factset_gate.py:111` | **Unchanged.** Widened by Phase 16's D-16 *specifically* for this phase |
| `phase14_factset.token_census` / `exact_match_clean` / `normalize_for_match` | `scripts/phase14_factset.py:313,334,323` | **Unchanged** |
| `phase14_recall.load_adapted_model(device, adapter_path=None)` | `scripts/phase14_recall.py:496` | **Unchanged.** Already injects at the artifact's own `lora_config` |
| `phase14_recall.complete_question(...)` / `draw_all` | `scripts/phase14_recall.py:640,595` | **Unchanged.** Bare prompt, per-question `question_seed(index)` |
| `phase14_recall.contains_value` / `normalize` | `scripts/phase14_recall.py:300,279` | **Unchanged.** The scorer's containment primitive |
| `phase14_recall.assert_no_value_in_prompt` | `scripts/phase14_recall.py:398` | **Unchanged.** Must be called with all 24 minted values |
| `phase14_recall.find_contradictions` | `scripts/phase14_recall.py:325` | **Unchanged.** Multi-match descriptive record |
| `personacore.lora.{load_adapter_weights, set_adapter_enabled, adapter_disabled}` | `src/personacore/lora/inject.py:76,133,157` | **Unchanged.** The scale audit is the ISO-06 mechanism |
| `teach_persona.train_arm` / `build_arm_bins` / `_require_go_verdict` | `scripts/teach_persona.py:501,403,166` | **Needs an additive `seed=SEED` keyword** — D-14 has no other route (F-10) |
| `_verdict.recorded_verdict(text)` | `scripts/_verdict.py:27` | **Unchanged.** The one copy of the anchored `## Verdict` read |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Generate-then-score in two processes | `run_scored_recall` per cell | `run_scored_recall` scores against `item.fact.value` (`phase14_recall.py:865`) — it would score Phase 14's values, and re-running it per cell is exactly the N² cost ISO-02 forbids. **Rejected** |
| Additive `seed=` on `train_arm` | Copy `train_arm` into a Phase-17 driver | A copied 130-line training body is a second training recipe that can drift from the one Phase 14's numbers came from. Violates "import, never copy" (Phase 16 D-16). **Rejected** |
| Additive `key=` on `aggregate_by_fact` | Pass `fact_id = slot` | Works today (one Phase-14 fact per slot makes it a bijection) but silently repurposes a field name, which is the drift this project keeps closing. **Marginal — see F-09** |
| Own `assert_family_closed` twin | Reuse Phase 16's | Phase 16's asserts against `HOLM_FAMILY_PAIRS`/`SIGN_TEST_ALTERNATIVE`, both keyed on arm names. **Must be a twin** |
| `frozenset` scorer return (Open Q1) | Priority-ordered single label | A priority order is an arbitrary tiebreak that biases whichever persona sorts first. **Prefer the set** |

**Installation:** none. `pyproject.toml` is unchanged; `make install` already provides everything.
Any diff to `pyproject.toml` in this phase is a STAT-04 violation and should fail review.

---

## Package Legitimacy Audit

**No external packages are installed by this phase.** Every dependency it uses is already declared
in the committed `pyproject.toml` and already installed in `.venv`. The Package Legitimacy Gate is
therefore not applicable: there is no registry lookup to perform, no slopcheck verdict to record,
and no `checkpoint:human-verify` install gate for the planner to insert.

| Package | Registry | Disposition |
|---------|----------|-------------|
| *(none — zero new packages)* | — | **N/A — STAT-04 requires `pyproject.toml` byte-identical at v3.0 close** |

**Packages removed due to slopcheck [SLOP] verdict:** none — no packages proposed.
**Packages flagged as suspicious [SUS]:** none — no packages proposed.

---

## Repo Findings (the ground truth this phase is built on)

Every item below was read or executed in the working tree on 2026-08-14.

### F-01 — W1 / ISO-06 status: **CLOSED**, verified, not assumed

`[VERIFIED: grep over scripts/ + src/, working tree]`

```
scripts/phase14_recall.py:557       inject_lora(model, LoRAConfig(**artifact["lora_config"]))
scripts/phase14_recall.py:1457      inject_lora(gated, LoRAConfig(**art["lora_config"]))
scripts/personalize_demo.py:448     inject_lora(model, LoRAConfig(**artifact["lora_config"]))
src/personacore/lora/inject.py:119  if "lora_config" in artifact:   # the scale audit
```

`scripts/teach_persona.py:478` and `scripts/train_adapter_smoke.py:63` still hold
`LORA_CFG = LoRAConfig()` — **correct and not a defect**: those are *producer* sites that define
the config an artifact will carry, not consumer sites that read one.

The audit at `inject.py:119-129` compares `sorted({m.scale for m in model.modules() if isinstance(m, LoRALinear)})`
against `cfg["alpha"] / cfg["r"]` with exact float equality (deliberate — both sides run the same
operation on the same operands). The skip when `lora_config` is absent is unreachable for real
files because `checkpoint.load_adapter` (`checkpoint.py:246`) raises on a missing `lora_config`.

**Planning consequence:** SC1 is written as if W1 is open. It is not. The plan should state this
explicitly and spend zero tasks on it, keeping only the ISO-04 canary from SC1. Optionally add one
cheap regression: a test asserting the three consumer sites still pass `**artifact["lora_config"]`
(AST scan in the `test_persona_argument_is_scoped_to_the_fairness_control` register) so the fix
cannot silently regress when Phase 17 multiplies the call sites.

### F-02 — The fixture is exactly what D-01 says, and it is slot-contiguous

`[VERIFIED: executed against results/phase16_recall_sample.json]`

`questions.core_held_out` holds 104 entries with keys `{seed_index, fact_id, question, reserved}`.
Grouping by `fact_by_id[fact_id].slot` gives **exactly 13 per slot across all 8 core slots**, and
the `seed_index` ranges are contiguous per slot:

| slot | `seed_index` range | free / reserved |
|------|--------------------|-----------------|
| `person_name` | 0–12 | 9 free, 4 reserved |
| `pet_name` | 13–25 | 9 / 4 |
| `cat_name` | 26–38 | 9 / 4 |
| `sibling_name` | 39–51 | 9 / 4 |
| `hometown` | 52–64 | 9 / 4 |
| `street` | 65–77 | 9 / 4 |
| `birth_year` | 78–90 | 9 / 4 |
| `house_number` | 91–103 | 9 / 4 |

Every question is persona-agnostic and value-free (`"the name you go by is"`,
`"do you remember what your dog is called?"`, `"which number is on your front door?"`). D-01's
premise-correction is confirmed by direct inspection.

`load_fixture_items()` (`phase16_persistence.py:293`) already reads it into `RecallItem`s with
`seed_index` **read verbatim, never re-enumerated**, and `_prove`s the 112/104/54 counts and the
per-fact balance. Phase 17 should call it and take `by_tier["core_held_out"]`, then attach
`slot = fact_by_id[item.fact.id].slot`.

### F-03 — `run_scored_recall` couples generation to a single value; the matrix cannot use it

`[VERIFIED: scripts/phase14_recall.py:822-910]`

`run_scored_recall` calls `score_question(completions, item.fact.value)` and
`find_contradictions(c, item.fact.value, lexicon)` inline. It scores against **the item's own fact
value** — Phase 14's value. Phase 17 must therefore use its generation half (`complete_question`)
and supply its own scoring pass. This is not a limitation; it is the natural seam for ISO-02.

The recorded arm JSON shows the completions survive to disk already:

```json
{"question": "the name you go by is", "slot": "person_name", "seed_index": 0,
 "fact_id": "cand_person_quillon", "value": "quillon", "split": "held-out",
 "prompt_ids": [8187, 8185, 116, ...], "k": 1, "n": 9,
 "completions": ["i goon it is my favorite.", "...", "i go by quick and i go by quillon", "..."],
 "hits": [false, ..., true, ...], "stopped": [true, ...], "contradictions": [[], ...]}
```

`[VERIFIED: results/phase16_arm_adapter-only.json, by_split["held-out"][0]]`

Phase 17's sweep record should carry the same shape **minus** `value`/`k`/`n`/`hits`
(which are per-persona and belong to the scoring pass) and **plus** `slot`.

### F-04 — The `persona=` and `draw_all` guards already cover a new Phase 17 driver, for free

`[VERIFIED: tests/test_phase14_scoring.py:439-643]`

`_scanned_files()` is `sorted((_REPO_ROOT / "scripts").glob("*.py")) + sorted((_REPO_ROOT / "src").rglob("*.py"))`
— a new `scripts/phase17_*.py` is scanned automatically. Two consequences:

- Phase 17's sweeps must call `build_recall_prompt(tok, question)` in the **bare two-positional
  form**. Passing `persona=` would require an entry in `PERSONA_ALLOWLIST` (hard equality) and is
  never needed here — the matrix is closed-book by construction.
- `test_every_draw_all_call_site_asserts_something` keys on `draw_all` call sites. Phase 17 calling
  `complete_question` (which is already covered by `DRAW_ALL_ASSERTED_BY`) adds **no new
  `draw_all` site**, so no guard edit is needed. But the *spirit* of the guard requires Phase 17's
  loop to call `assert_no_value_in_prompt(tok, question, all_24_minted_values)` before drawing.
  That is one line and it is the extension of the clean-room proof to Phase 17's own material —
  fixture guard #4 only checks Phase 14's 10 values.

### F-05 — Feasibility risk #1 (tokenizer census) is **not real**; a different constraint is

`[VERIFIED: executed against artifacts/tokenizer.json]`

The frozen tokenizer has 8,192 ids of which **7,645 are undecodable and 547 live**. That statistic
concerns *unreachable merges*, not unreachable bytes — all 256 byte ids are live and BPE falls back
to bytes for anything unmerged, so `encode()` can never emit a dead id
(`phase14_factset_gate.py:321-326` records this as a "measured no-op"). 24 invented lowercase ASCII
values were census-tested; **24/24 round-tripped exactly**:

```
thessaly 7  vorwick 6  brambleton 8  quorra 5  nyxen 3  hollowmere 7  fenmark 5  drovik 6
sablewind 7 tarrowgate 8 vellamo 4  ostrick 6 kessendra 6 myrrhen 6 grindlow 6 wexford 7
1946 4  1971 4  1938 4  5063 4  2287 4  9614 4  duskvale 6  orlenne 6
```

**The constraint that IS real, and was not previously named:** `RECALL_MAX_NEW_TOKENS = 48` is
`derive_recall_budget(census) = max(census) + PREAMBLE_HEADROOM(32) + TAIL_HEADROOM(8)` rounded up
to a multiple of 8 (`phase14_recall.py:120-145`), and `SHARED_ARM_CONFIG.max_new_tokens` reads that
integer (`phase16_persistence.py:173`). Phase 14's census maxes at 8. **A minted value costing 9+
tokens forces the budget off 48**, breaking parity with every published Phase 14/16 number.
`assert_values_fit` (`phase14_recall.py:239`) will refuse anything needing more than
`48 - TAIL_HEADROOM = 40` tokens, which is far looser than what comparability needs.

**Recommendation:** make `len(tok.encode(value)) <= 8` a **hard mechanical filter at minting**, and
`_prove` it in the Phase 17 pre-flight. From the sample above, ≤8 is comfortably achievable for
names, towns, streets, 4-digit years and 4-digit house numbers.

D-04's all-8-slots collision **does not tighten**. Risk #1 as handed to the researcher is closed.

### F-06 — Persona teaching material generates from arbitrary `Fact`s, unchanged

`[VERIFIED: executed `render_family` on a synthetic Fact]`

`fs.render_family(family_id, Fact("p17_a_person", "person_name", "thessaly", "core"))` produces
5+5+4+4+4 = **22 taught paraphrases** across `TAUGHT_FAMILY_IDS = {F1,F2,F4,F5,F6}`, inside
`PARAPHRASES_PER_FACT_TARGET`. `SLOT_FORMS` covers all 8 core slots. No fact-set edit is required
to teach a Phase 17 persona.

Two constraints ride along:
- `fs.GATE_PROBES[fact.id]` raises `KeyError` for a fact outside `all_pools()` — which is exactly
  why `probe_guessability` takes `questions` as a **parameter** (its D-16 widening).
- `teach_persona.sanity_check` proof 6 (`teach_persona.py:362-372`) `_prove`s that no
  `fs.heldout_questions()` appears as a contiguous id run in the teaching bin. Since Phase 17
  teaches only `TAUGHT_FAMILY_IDS`, this holds automatically and re-proves the never-seen split for
  the new personas at no cost.

### F-07 — The guessability gate should probe with the fixture's own questions

`[ASSUMED — recommendation, not a locked decision]`

`probe_guessability` takes `questions` from the caller. Two candidate probe sets:

- `fs.SLOT_QUESTION_BANK[slot]` — 8 hand-written probes per slot (what Phase 14 used, 4 per fact).
- **The fixture's own 13 `core_held_out` questions for that slot** — the exact instrument the
  matrix scores on.

Prefer the second. It measures the base on the same questions the matrix uses, at higher power
(13 questions × 4 completions = 52 per slot vs Phase 14's 4 × 4 = 16), and the base is stateless so
the completions can be **cached per question** and shared across all 3 personas' values for that
slot — the `probe_cache` idiom already in `phase14_factset_gate.main()` (`:239-249`). Total
generation: 8 slots × 13 questions × 4 completions = **416 completions**, not 1,248.

This also makes the ISO-03 base column a **higher-powered re-measurement of the same property**
(9 draws instead of 4). If the gate says clean and the base column later produces a persona value,
that disagreement is a bug signal, and the plan should say so up front.

### F-08 — `holm()` prices alpha from Phase 16's family; the match at m=6 is a coincidence

`[VERIFIED: phase16_persistence.py:1189, executed]`

```python
m = len(HOLM_FAMILY_PAIRS)          # C(4,2) over Phase 16's CONDITION_ORDER == 6
_prove(len(p_values) == m, ...)
alpha_at_step = HOLM_ALPHA / (m - index)
```

Phase 17's family is also 6 (3 diagonals × 2 own-row off-diagonals), so `holm()` accepts it and
prices it correctly **today**. Executed end-to-end during this research with cell-tuple keys:

```
family size: 6, e.g. (('A','A'), ('A','B'))
p_values: all 0.0078125
holm rows: alpha at steps 0.0083333 / 0.01 / 0.0125 / 0.0166667 / 0.025 / 0.05 — all rejected
```

`fact_signs` and `sign_test_exact` likewise ran **unchanged** with cell tuples as "arms" and slot
strings as "facts". STAT-04 is satisfiable literally by import.

**The risk:** if anyone ever changes Phase 16's `CONDITION_ORDER`, Phase 17's alpha silently
changes. Two ways to close it:

- **(a) Pin the coincidence** — a Phase 17 `_prove(len(stats.HOLM_FAMILY_PAIRS) == len(PHASE17_FAMILY))`
  plus a CPU test. Zero edits to a v2.0 driver. Cheapest.
- **(b) Additive widening** — `def holm(p_values, *, m=None)` defaulting to
  `len(HOLM_FAMILY_PAIRS)`. Note `test_holm_reads_the_family_length_rather_than_a_retyped_six`
  (`test_phase16_stats.py:610`) forbids a literal `6` as a divisor; a parameter is not a literal,
  so this passes.

**Recommend (a).** It is smaller, adds a guard rather than moving one, and keeps the Phase 16
driver untouched — which matters because `test_nothing_outside_the_six_pairs_enters_the_verdict_path`
treats that file as pre-registration evidence.

**Also note:** `_GATE_MODULES = (_DRIVER_PATH, _LADDER_PATH)` (`test_phase16_stats.py:747`) — the
"nothing outside the six pairs is gated" static scan is **file-scoped to Phase 16**. A Phase 17
driver calling `holm` will not go red, but it is also not covered. The plan should add a Phase-17
twin of that scan over its own driver, or the guard is green and blind about the new file — the
exact failure mode D-21 widened `_scanned_files()` to close.

### F-09 — `aggregate_by_fact` hardcodes `record["fact_id"]`; `cluster_bootstrap` does not

`[VERIFIED: phase16_persistence.py:829, 887]`

`aggregate_by_fact` does `grouped.setdefault(record["fact_id"], []).append((record["k"], record["n"]))`
— the key is a literal field name. `cluster_bootstrap` takes `{key: [(k,n),...]}` and only does
`sorted(per_fact_questions)`, so it is **fully key-agnostic** and works with slot keys with zero
changes.

Options for D-02's slot keying:
- **(a)** Widen with `key="fact_id"` — a signature change plus one line, every existing caller
  unaffected. The D-16 register.
- **(b)** Write Phase 17's own ~15-line group-by. Duplicates the `_prove` block.
- **(c)** Set `record["fact_id"] = slot` in the Phase 17 record. Works (the Phase 14 fact↔slot map
  is a bijection on this fixture) but repurposes a field name, which is exactly the silent drift
  this project keeps closing.

**Recommend (a).** It is two lines, honours "import, never copy", and makes D-02's "keyed by slot,
never by fact_id" literally true in the code rather than true-by-coincidence.

Note `aggregate_by_fact` also `_prove`s `record["split"] == tier`. Phase 17 scores `core_held_out`
only, so every record has `split == "held-out" == GATED_TIER` — passes unchanged.

### F-10 — `teach_persona` hardcodes the training seed in three places; D-14 needs a parameter

`[VERIFIED: scripts/teach_persona.py:99, 412, 563, 603]`

```
SEED = 1337                              # module constant
build_arm_bins: seed_everything(SEED)    # :412 — owns the bins RNG
train_arm:      seed_everything(SEED)    # :563 — owns the GPT build / LoRA init draw
train_arm:      TrainConfig(seed=SEED)   # :603 — owns the training data order
```

D-14 (distinct seed per persona) has **no route** to this without an additive parameter. The init
draw at `:563` is the one D-14's "initialization diversity" argument is actually about — `lora_A`
is `nn.init.normal_(std=0.02)` at construction (`lora/layer.py:31`), so the seed at `:563` is the
init draw.

Also relevant:
- `train_arm` calls `_require_go_verdict(FACTSET_REPORT)` with **Phase 14's** report hardcoded
  (`:507`). Phase 17's SC2 blocking verdict is a *different* report. The lazy fix is for the
  Phase 17 driver to call `_require_go_verdict(PHASE17_REPORT)` itself before `train_arm` — both
  gates then fire, and nothing in the committed driver moves.
- `arm_outputs(arm)` (`:190`) names non-`real` artifacts `checkpoints/phase14_{arm}_adapter.pt`,
  `data/persona_{arm}_train.bin`, `results/phase14_{arm}/run.csv`. Phase 17 arms would land under a
  `phase14_` prefix — functional but misleading provenance in a project that treats provenance as
  the product.
- `refuse_if_exists` (`:214`) protects every existing arm's outputs. New arm names produce new
  paths, so **nothing recorded can be clobbered**.
- `ARMS` / `arm_spec` are only reached through `main()`. Calling `train_arm(...)` directly from a
  Phase 17 driver bypasses both.

**Recommendation:** one additive commit to `teach_persona.py` — `seed=SEED` keyword on `train_arm`
and `build_arm_bins` (default preserves every existing arm bit-for-bit), plus a phase-aware prefix
in `arm_outputs`. Record the seed in the run-provenance line, which already prints `seed={SEED}`
(`:688`) and should print the parameter instead.

### F-11 — `fact_signs` signs on the DRAW rate, while the published proportion uses the QUESTION unit

`[VERIFIED: phase16_persistence.py:837, 919, 1083, 2182]`

```
aggregate_by_fact returns  rate = sum(k)/sum(n)        # the DRAW rate
cluster_bootstrap counts   numerator += 1 if k > 0     # the QUESTION unit (max over draws)
report_proportion takes    successes = n_answerable    # the QUESTION unit
fact_signs compares        per_fact_by_arm[...]["rate"]  # the DRAW rate
```

In Phase 16 this was benign — arm A was 8/8 unanimous in either unit and the other three arms were
exactly 0 — but **STAT-01 says the question is the unit of analysis, never the draw**, and the
inferential gate is the one number where that matters most.

`fact_signs` reads `["rate"]` off whatever dict it is handed and does nothing else, so Phase 17 gets
STAT-01 compliance for free by building its per-cell dicts with
`{"rate": n_answerable / n_questions}` rather than passing `aggregate_by_fact`'s `rate` through.
**Zero changes to `fact_signs`; one line at assembly.** Pre-register the unit in the driver.

### F-12 — Measured anchors for D-10's all-fail branch and the base column

`[VERIFIED: results/phase16_persistence_report.md:175-178, per-fact table :136-170]`

On the **identical** `core_held_out` 104-question tier, at 9 draws:

| arm | question-unit rate | two-stage cluster bootstrap 95% | Wilson upper |
|-----|-------------------|--------------------------------|--------------|
| `adapter-only` | 90/104 = **0.865385** | (0.721154, 0.971154) | 0.911252 |
| `base-neither` (adapter off) | **0/104** | (0.0, 0.0) | 0.025355 (rule of three 0.028846) |

Per-fact `adapter-only` answerable counts: 13/13, 13/13, 13/13, 12/13, 12/13, 11/13, 10/13, 6/13.
Per-fact `base-neither`: 0/13 on all eight, Wilson upper 0.172267, rule of three 0.230769.

**Do not conflate units.** Phase 14's `0.3483` (cited at CONTEXT D-07) is the *draw* rate over the
same run; Phase 16's `0.865385` is the *question* rate. Both describe the same held-out tier.
Phase 17's diagonal should be reported in **both**, exactly as `report_proportion` already does.

**Consequence for D-10:** an expected diagonal near 0.87 (question unit) against an expected
off-diagonal near 0 is an enormous contrast, so the 8/8 unanimity requirement is plausible rather
than aspirational — *provided* the personas train like Phase 14's did. The `cand_house_7412` row at
6/13 is the warning: one weak slot in one persona is enough to tie a sign and close the gate.

### F-13 — The base column's separability is already partly guaranteed by the ISO-01 gate

`[VERIFIED: reasoning over phase14_factset_gate.probe_guessability + F-12]`

`probe_guessability` proves the un-adapted base produces **zero** containments of each minted value.
So an off-diagonal hit on persona *j*'s value cannot be the base's own prior — it must come from
adapter *i*. ISO-03's column is therefore not the *only* thing separating leak from prior; it is the
higher-powered confirmation of the gate (13 questions × 9 draws = 117 completions per value per
slot, vs the gate's 52) plus the empirical instrument D-13 needs for the `none`/base-prior split.

State this honestly in the report: the base column is doing two jobs, and neither is "the only
control", which is a stronger position than the requirement text implies.

---

## Architecture Patterns

### System Architecture Diagram

```
                        ┌──────────────────────────────────────────────┐
   committed data ─────►│ PHASE 17 PERSONA SET (24 values, 3 x 8 slots)│
   (module literals)    └───────────────┬──────────────────────────────┘
                                        │
                        ┌───────────────▼──────────────────────┐
   frozen base ────────►│ PRE-FLIGHT GATE  (GPU, ~3 min)       │
   frozen tokenizer     │  · token census ≤ 8 ids (F-05)       │
                        │  · substring-disjointness (Pitfall 5)│
                        │  · probe_guessability, cached/slot   │
                        └───────────────┬──────────────────────┘
                                        │ writes results/phase17_personas_report.md
                                        ▼
                        ╔═══════════════════════════════════════╗
                        ║ HUMAN GO/ADAPT VERDICT  (BLOCKING)    ║  ← _require_go_verdict
                        ╚═══════════════┬═══════════════════════╝
                                        │  STOP/PENDING ⇒ nothing downstream runs
              ┌─────────────────────────┼─────────────────────────┐
              ▼                         ▼                         ▼
      train_arm(seed=s_A)       train_arm(seed=s_B)       train_arm(seed=s_C)
      ~81 s each  ───────────────────────────────────────────────────┐
              │                         │                         │  │
              ▼                         ▼                         ▼  │
      adapter_A.pt              adapter_B.pt              adapter_C.pt│
              │                         │                         │  │
   ═══════════╪═════════════ ONE FRESH PROCESS PER SWEEP ═════════╪══╪═══════
              ▼                         ▼                         ▼  ▼
      ┌───────────────┐        ┌───────────────┐        ┌───────────────┐   ┌──────────────┐
      │  SWEEP A      │        │  SWEEP B      │        │  SWEEP C      │   │ SWEEP base   │
      │ load_adapted_ │        │      "        │        │      "        │   │ adapter_     │
      │ model(path)   │        │               │        │               │   │ disabled()   │
      │ ISO-04 canary │        │ ISO-04 canary │        │ ISO-04 canary │   │ (zero lora_B)│
      │ 104 q × 9 draw│        │               │        │               │   │              │
      └───────┬───────┘        └───────┬───────┘        └───────┬───────┘   └──────┬───────┘
              │ completions            │                        │                  │
              ▼                        ▼                        ▼                  ▼
       phase17_sweep_A.json     ..._B.json              ..._C.json      ..._base.json
       (+ lora_B sha256)        (+ sha256)              (+ sha256)      (+ all-zero sha)
              └────────────────────────┴────────────────────────┴──────────────────┘
                                        │
   ═════════════════════════ SEPARATE CPU-ONLY PROCESS  (--report) ═══════════════════
                                        ▼
                      ┌───────────────────────────────────────┐
                      │ ISO-04 CROSS-PROCESS PROOF            │  4 distinct lora_B digests,
                      │ 4 distinct pids, 1 git_sha            │  base digest == all-zero
                      └──────────────────┬────────────────────┘
                                         ▼
                      ┌───────────────────────────────────────┐
                      │ CELL-BLIND SCORER                     │  score(completion, slot_values)
                      │ signature carries NO (i, j)           │  → labels ⊆ {a, b, c}
                      │ pinned by inspect.signature           │  every completion, every sweep
                      └──────────────────┬────────────────────┘
                                         ▼
                      ┌───────────────────────────────────────┐
                      │ MATRIX ASSEMBLY  (the ONLY place that │
                      │ knows i and j)                        │
                      │  own-hit → diagonal                   │
                      │  other-hit → LEAK                     │
                      │  none ∧ matches base column → PRIOR   │
                      │  none ∧ otherwise → CONFABULATION     │
                      └──────────────────┬────────────────────┘
                                         ▼
              ┌──────────────────────────┴───────────────────────────┐
              ▼                                                      ▼
   ┌─────────────────────────────┐                    ┌──────────────────────────────┐
   │ GATE (n=8 slots)            │                    │ DESCRIPTIVE                  │
   │ fact_signs → sign_test_exact│                    │ cluster_bootstrap per cell   │
   │ → holm over 6 pairs         │                    │ report_proportion (Wilson +  │
   │ 8/8 unanimity or nothing    │                    │ 3/n at every zero)           │
   └──────────────┬──────────────┘                    │ ISO-05 min/max/median, k=3   │
                  │                                   └──────────────┬───────────────┘
                  └────────────────────┬─────────────────────────────┘
                                       ▼
                     results/phase17_isolation_report.md
                     (verdict computed by importing pre-registered constants,
                      D-10 all-fail branch mandatory when the gate misses)
```

### Recommended Structure

```
scripts/
├── phase17_personas.py        # committed DATA + pure helpers: the 24 values as Facts,
│                              #   the 4 mechanical minting filters, the pre-registration
│                              #   block (family tuple, direction dict, seeds). No torch at
│                              #   import; module-level literals only (STAT-05).
├── phase17_persona_gate.py    # GPU pre-flight: census + probe_guessability (imported),
│                              #   writes results/phase17_personas_report.md with
│                              #   "## Verdict\n\nPENDING", clobber-guarded by
│                              #   _verdict.recorded_verdict.
└── phase17_isolation.py       # two modes, mutually exclusive, like phase16_persistence.py:
                               #   --sweep {a,b,c,base}  → one fresh process, writes
                               #                           results/phase17_sweep_{n}.json
                               #   --report              → CPU only; scores, assembles,
                               #                           gates, writes the report.
tests/
├── test_phase17_personas.py   # CPU: the 4 minting filters bite; values are disjoint;
│                              #   census ≤ 8; no value is a substring of any question.
├── test_phase17_scoring.py    # CPU: inspect.signature has no (i,j); no `if i == j`
│                              #   in the scoring path (AST); scorer labels are correct
│                              #   on hand-built completions; multi-match behaviour.
└── test_phase17_stats.py      # CPU: family is exactly 6 pairs; the Phase-16 m==6
                               #   coincidence is pinned; nothing outside the family
                               #   reaches holm/sign_test_exact in the Phase 17 driver.
results/
├── phase17_personas_report.md      # the ISO-01 blocking verdict (committed evidence)
├── phase17_sweep_{a,b,c,base}.json # raw completions + lora_B digest + pid + git_sha
└── phase17_isolation_report.md     # the matrix, the gate, the D-10 branch
```

### Pattern 1: Generate once, score N ways, in two different processes

**What:** GPU sweeps write completions to disk; a separate CPU process scores every recorded
completion against all three personas' slot values.

**When to use:** always, for this phase. It is what makes ISO-02's "N sweeps scored N ways" a
*structural* property rather than a discipline, and what makes SC3's cell-blindness free.

**Why it matters beyond cost:** the scorer literally cannot see which sweep produced a completion,
because the scoring function receives a string and a slot's three values and nothing else. There is
no `(i, j)` to accidentally read. The AST guard SC3 asks for (`no if i == j: in the scoring path`)
then has almost nothing to find, which is the correct end state for a structural guard.

```python
# scripts/phase17_isolation.py — the scoring primitive. Pure, CPU, no torch, no cell index.
# `slot_values` is {persona_label: value} for ONE slot. There is no "own" and no (i, j).
# SC3 pins this signature with inspect.signature; a test also AST-scans for `i ==`/`j ==`.
def score_completion(completion, slot_values):
    """Which persona values appear in this completion. Cell-blind BY SIGNATURE.

    Returns a frozenset over {"persona_a","persona_b","persona_c"} — empty means `none`
    (D-12's fourth label). Containment is `phase14_recall.contains_value`, IMPORTED, so the
    matrix and every published Phase 14/16 rate use one boundary rule (D-10's normalizer).
    """
    return frozenset(
        label for label, value in slot_values.items()
        if recall.contains_value(completion, value)
    )
```

### Pattern 2: Pre-registration as module-level literals in the committed driver (STAT-05)

**What:** the family tuple, the per-comparison direction, the three training seeds and the
verdict templates are module-level constants pushed **before** the run they judge; the report
computes verdicts by importing them.

**Example, following `SIGN_TEST_ALTERNATIVE`'s shape exactly:**

```python
# scripts/phase17_personas.py — pushed BEFORE any adapter trains (STAT-05).
PERSONAS = ("persona_a", "persona_b", "persona_c")

# DERIVED from PERSONAS, never a hand-typed list of six: a retyped family is a family that
# can stop matching the cells it claims to compare (phase16_persistence.py:1001 register).
# 3 diagonals x 2 own-row off-diagonals = 6 (D-08).
HOLM_FAMILY_CELLS = tuple(
    ((i, i), (i, j)) for i in PERSONAS for j in PERSONAS if i != j
)

# The declared direction, per comparison, committed before any sign is visible (D-29 register).
# Spelled out per pair rather than generated, so a reviewer audits six committed statements.
CELL_ALTERNATIVE = {
    (("persona_a", "persona_a"), ("persona_a", "persona_b")):
        "persona_a's own value exceeds persona_b's value under adapter A",
    # ... five more, one per member of HOLM_FAMILY_CELLS ...
}

# D-14: one seed per persona, distinct. The gated contrast is WITHIN adapter i, so the seed
# cancels inside it; D-15 forbids reading the three diagonals as a ranking.
PERSONA_SEEDS = {"persona_a": 1337, "persona_b": 1338, "persona_c": 1339}
```

### Pattern 3: One process per sweep, enforced by an argument surface with no third mode

**What:** copy `phase16_persistence.py:2557-2600` verbatim in shape — a mutually exclusive,
required `--sweep NAME | --report` group, and *no* convenience flag that runs more than one sweep.

**Why:** *"the only structural way to guarantee [the process split] is to make a single process
incapable of running two. A convenience flag would turn the process split from a PROPERTY of this
driver into a convention an operator is trusted to follow."* `[CITED: scripts/phase16_persistence.py:2565-2568]`

For Phase 17 this is stronger than for Phase 16: **fresh processes make the ISO-04 in-process swap
failure impossible in the first place**, because no process ever holds two adapters. The canary then
becomes a cross-process proof (see Pitfall 1), which is the harder and more valuable half.

### Anti-Patterns to Avoid

- **Calling `run_scored_recall` per cell.** It scores `item.fact.value` (Phase 14's value) and
  re-generates. Both the wrong values and the N² cost ISO-02 exists to prevent.
- **Re-enumerating `seed_index`.** The fixture *is* the pairing key. `load_fixture_items` reads it
  verbatim precisely so a mismatch surfaces instead of being repaired (`phase16_persistence.py:296-299`).
- **Varying the generation seed per sweep.** D-14's distinct seeds are *training/init* seeds. The
  generation seed is `question_seed(index) = 1337 + index` and must be **identical across all four
  sweeps** — that is what makes cell (i,j) and cell (i',j) comparable and what ISO-03 requires of
  the base column ("identical questions, seeds, `forbid_ids` and `stop_ids`").
- **Reporting an aggregate "isolation rate %" over the 9 cells.** SC5/STAT-06 forbid gating it; do
  not print it either, because a printed number gets quoted as a gate.
- **Ordering the three personas by diagonal.** D-15. n=1 seed per persona makes the ordering
  uninterpretable.
- **Building a second `forbid_ids` mask.** Build it once and thread it, the way
  `phase16_persistence.resolve_forbid` does, and record its sha256 per sweep for parity.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exact paired sign test | A binomial-tail helper | `phase16_persistence.sign_test_exact` | Ties fold against the alternative and n stays 8; step 2's direction filter is a *defect fix* (a pure two-sided test scores 0/8 as significant). Verified values: 8/8→0.0078125, 7/8→0.0703125, 4/8→1.0 |
| Holm step-down | A per-p threshold loop | `phase16_persistence.holm` | Rejection **stops at the first failure**; a naive loop rejects later small p's and passes every other test in the suite (`test_holm_stops_at_the_first_failure`) |
| Clustered CI | Question-level bootstrap | `phase16_persistence.cluster_bootstrap` | Two stages: slots, then that slot's questions. A question-only bootstrap is narrower than the gate standing beside it — an interval claiming more than its own test |
| Zero-cell bound | A bare `0%` | `report_proportion` | Emits Wilson upper + rule-of-three + both denominators, and never renders a bare zero percentage (STAT-02, pinned by test) |
| Guessability probe | A fresh probe loop | `phase14_factset_gate.probe_guessability` | Widened by D-16 *for this phase*. A second copy is a second guessability rule that can drift |
| Value containment | A regex or `in` | `phase14_recall.contains_value` | Substring after `normalize` (lowercase → `detokenize` → collapse whitespace → strip edges). Whitespace collapse is load-bearing: the measured case `'i am a mort of musician'` shows BPE inserting an interior space |
| Adapter load + audit | `model.load_state_dict(..., strict=False)` | `personacore.lora.load_adapter_weights` | Three audits (keys, shape/dtype, **scale**) *before* a tensor is copied. A bare `strict=False` half-applies and raises at the end, leaving the model corrupted |
| Adapter-off control | A second un-adapted model | `personacore.lora.adapter_disabled` | Exception-safe, restores each module's *prior* value, refuses while merged. Measured bit-identity to the un-adapted base: max abs diff exactly 0.0 |
| `## Verdict` parsing | `text.split("## Verdict")[-1]` | `_verdict.recorded_verdict` | That exact split was CR-02 — five copies, four broken by a prose mention of the heading, which made `--force` the only way through and then destroyed the evidence it protected |
| Teaching bins / training loop | A Phase-17 training body | `teach_persona.build_arm_bins` + `train_arm` | A copied recipe is a second recipe that can drift from the one every published number came from |

**Key insight:** in this repo the expensive part of a statistic is not the arithmetic — it is the
*pre-registration discipline attached to it*. `sign_test_exact` is 20 lines of code carrying four
committed decisions (ties fold in, n is fixed, direction is declared, enumeration not closed form),
each of which was a recorded defect fix. Re-deriving the arithmetic loses the decisions.

---

## Statistics Surface

### The gated quantity, concretely

Cell `(i, j)` = the fraction of the 104 `core_held_out` questions for which **any** of adapter *i*'s
9 draws contained persona *j*'s value for that question's slot. (Question unit, max over draws —
STAT-01; see F-11.) The base column is cell `(base, j)` for each *j*.

Per slot *s* (13 questions), the paired observation for comparison `((i,i), (i,j))` is
`sign(rate(i,i,s) − rate(i,j,s))`, ties → 0 folded against the alternative. n = 8 slots.

**Six comparisons, fixed before the run:** `((i,i),(i,j))` for i ∈ {A,B,C}, j ≠ i.
`m = 6` ⇒ Holm first-step alpha = 0.05/6 = **0.0083333**.

### The arithmetic, verified by execution

| quantity | value | source |
|----------|-------|--------|
| achievable p at 8/8 unanimity | **0.0078125** | `sign_test_exact((1,)*8)` executed |
| achievable p at 7/8 | **0.0703125** | executed |
| achievable p at 6/8, 5/8, ≤4/8 | 0.2890625, 0.7265625, 1.0 | executed |
| Holm step alphas, m=6 | 0.0083333, 0.01, 0.0125, 0.0166667, 0.025, 0.05 | executed |
| margin at step 1 | **0.0005208** (6.7% relative) | executed |

**Only 8/8 slot unanimity clears any step.** 7/8 gives 0.0703125, which exceeds even the *last*
step's alpha of 0.05 — so a comparison with one tied or lost slot is retained at every position in
the ordering. This is a stronger statement than the CONTEXT note and follows directly from the
enumerated p-values: **the gate requires all 48 slot-level observations (6 comparisons × 8 slots) to
favour the diagonal.** The plan must pre-register this sentence.

### Two things the plan must pre-register that CONTEXT does not settle

1. **What "the gate cleared" means when Holm rejects some but not all six.** Holm's step-down with
   five unanimous comparisons and one at 7/8 rejects five and retains one — the family is not dead.
   Phase 16 published exactly this shape ("3 of 6 pairs cleared their Holm step"). Recommendation:
   **the headline isolation claim requires all six rejected**, because a single retained comparison
   means one persona's value appeared under another's adapter at a rate the test cannot separate
   from that adapter's own recall. Publish the per-comparison Holm rows regardless, so a partial
   result is readable. See Open Question 2.
2. **The unit the signs are computed in.** Use the **question** unit (F-11). One line at assembly;
   `fact_signs` needs no change.

### Why Holm and not Benjamini-Hochberg (STAT-03)

**Holm (1979) controls FWER under arbitrary dependence.** The proof is a subadditivity argument: if
any true null is rejected there must exist a true hypothesis with p ≤ α/m₀, and
`Pr(A) ≤ Σ_{i∈I₀} Pr(P_i ≤ α/m₀) = α`. No assumption about the joint distribution or the correlation
of the p-values is used anywhere.
`[CITED: en.wikipedia.org/wiki/Holm–Bonferroni_method]` `[CITED: Holm, S. (1979), Scand. J. Statist. 6:65-70]`

**BH requires independence or PRDS, and pairwise comparisons are a documented non-PRDS case.**
Benjamini–Yekutieli (2001) extended BH's FDR control to statistics with positive regression
dependency on the subset of true nulls (PRDS); for non-PRDS dependence the BY correction
(α/Σ1/k, k=1..m) is required instead. Sample statistics in **pairwise comparisons do not exhibit
positive regression dependency** — the literature on this shows only *asymptotic directional* FDR
control for BH in that setting, not exact finite-sample control.
`[CITED: arXiv:1712.03305, "Asymptotic false discovery control of the Benjamini-Hochberg procedure for pairwise comparisons"]`

This phase's dependence is structural and severe, which is exactly STAT-03's stated reason:
off-diagonal cells **share adapters row-wise** (cells (i,i), (i,A), (i,B) all come from one adapter,
one seed, one set of completions) and **share question sets column-wise** (every cell is scored on
the same 104 questions with the same generation seeds). At n=8 with m=6, "asymptotic" is not
available. Holm is the correct choice and its validity is unconditional.

**Do not substitute BY.** It would be *more* conservative than Holm here and would kill the headline
arithmetically: BY's factor at m=6 is Σ_{k=1..6} 1/k = 2.45, giving a first step of
0.05/(6·2.45) = 0.0034, below the achievable 0.0078125 at every possible outcome.

### Zero-cell bounds (STAT-02) and their assumptions, stated honestly

The exact one-sided Clopper–Pearson upper limit for 0 successes in n trials is `1 − α^(1/n)`. The
rule of three follows from `(1−p)^n = 0.05` ⇒ `n·ln(1−p) = ln 0.05 = −2.9957`, rounding to −3 and
using `ln(1−p) ≈ −p`, giving `3/n`.
`[CITED: en.wikipedia.org/wiki/Rule_of_three_(statistics)]` `[CITED: Hanley & Lippman-Hand (1983); Jovanovic & Levy (1997), The American Statistician 51(2)]`

Computed for this phase's denominators:

| n | Wilson upper (`erasure_gate`) | rule of three `3/n` | exact CP `1−0.05^(1/n)` |
|---|-------------------------------|---------------------|--------------------------|
| 104 (a cell, questions) | 0.025355 | 0.028846 | 0.028394 |
| 8 (a slot-clustered cell) | 0.252724 | 0.375000 | 0.312344 |
| 13 (one slot, questions) | 0.172267 | 0.230769 | 0.205672 |

`[VERIFIED: executed against scripts/erasure_gate.py]`

**All three assume independent, identically distributed Bernoulli trials. That assumption does not
hold here.** The 104 questions in a cell are 13 per slot × 8 slots and are strongly clustered — a
persona value either transferred into the weights for a slot or it did not, and the 13 phrasings of
that slot then mostly agree. The effective number of independent units is nearer 8 than 104, and the
n=104 row above therefore **understates** the real uncertainty by roughly an order of magnitude
(compare 0.0288 against 0.375).

**This is already solved in the repo and must be reused verbatim.** `report_proportion` attaches
`WILSON_LABEL` to every rate:

> *"one-sided 95% Wilson upper bound computed as if the questions were INDEPENDENT. They are not —
> questions cluster inside facts — so this width UNDERSTATES the real uncertainty. The DESCRIPTIVE
> interval for this phase is the two-stage cluster bootstrap (`cluster_bootstrap`); Wilson is
> reported alongside it, labelled, for comparability with every other rate in this milestone, and
> never as the phase's own width."* `[CITED: scripts/phase16_persistence.py:770-776]`

**Recommendation:** carry that label with `slot` substituted for `fact`, publish the two-stage
cluster bootstrap as the phase's own width, and — because Phase 17's zeros are the *headline* (an
off-diagonal zero is the isolation result) — additionally report the **slot-level** bound `3/8 =
0.375` alongside the question-level `3/104 = 0.0288`, explicitly labelled as the two ends of the
clustering assumption. Publishing both is the honest form: the truth is between them, and the
cluster bootstrap is the estimate of where.

### The paired test's own assumptions

The exact sign test is distribution-free — no normality, no symmetry of the differences — and its
only real assumption is **independence across the paired units**, here the 8 slots.
`[CITED: statisticssolutions.com/sign-test; standard nonparametric theory]`

Slot independence is the right call for this design and is defensible: the 8 slots ask about
different referents (a name, a dog, a town, a year), the values are minted independently, and the
teaching episodes for one slot do not contain another slot's value. It is *not* airtight — all 8
slots share one adapter and one training run, so a globally bad adapter moves all 8 together. That
is a common-mode effect on the *magnitudes*, and the sign test uses only the ordering *within* a
slot, which is the within-adapter contrast D-14 already relies on. State the assumption and its
limit; do not claim it away.

---

## Common Pitfalls

The five failure modes named in the phase brief, each with the exact place its guard sits.

### Pitfall 1 (failure mode a) — a silently failed adapter swap

**What goes wrong:** the driver believes it swapped adapters and did not. Because all three personas
have **identical `lora_` key sets, identical shapes and identical `lora_config`**, every audit in
`load_adapter_weights` — keys, shape/dtype, and now scale — passes for the *wrong* artifact. The
load path is structurally silent about adapter identity.

**Honest correction, recorded once:** ISO-04's text says the result is "a perfect diagonal and zero
leakage". Under the ISO-02-compliant design (N sweeps scored N ways) a swap no-op actually produces
**column collapse** — all sweeps carry persona A's values, so column A is high and the other two
columns are 0, giving a diagonal of (high, 0, 0). That is equally fake and equally invisible without
the canary; the flattering-diagonal shape arises under a per-cell design or in combination with
failure mode (b). The guard is required either way and its location does not change. Researching
this as decided; not re-opening it.

**Where the guard sits — two layers, because either alone is escapable:**

- **In-process, at the load site.** Snapshot every `lora_B` before `load_adapter_weights`, then
  `_prove` that at least one changed, **and** that no `lora_B` is all-zeros (the identity gate at
  `lora/layer.py:30` means an all-zero `lora_B` is a mathematically exact no-op even if a load
  "succeeded"). Roughly 8 lines.
- **Cross-process, inside `--report`, and this is the unskippable half.** Each sweep record carries
  `sha256` of its **live model's** concatenated `lora_B` tensors *after* load — not the artifact
  file's digest, which would not prove the tensors reached the model. `--report` then `_prove`s the
  three adapter digests are pairwise distinct and that the base sweep's digest equals the all-zero
  digest. This makes assembling the report **impossible** unless the sweeps provably ran on
  different weights, exactly as `assert_arms_are_pairable` (`phase16_persistence.py:2658`) makes it
  impossible to publish without four distinct pids and one git SHA.

**Warning signs:** two sweeps producing byte-identical completions; a column of the matrix that is
uniformly high while the others are uniformly zero; a diagonal that is *too* clean.

**Mutation-prove it.** Phase 15's D-07 precedent, followed by the W1 fix: a guard nobody has watched
fail is a guard nobody has verified. Deliberately load the same artifact twice and confirm both
layers fire.

### Pitfall 2 (failure mode b) — scoring persona *j*'s own questions against adapter *i*

**What goes wrong:** the off-diagonal becomes ~0 **by construction** — it merely re-proves Phase 14's
`0/2430` at N² the cost, while looking like a measured isolation result.

**Why it cannot happen here structurally:** there is exactly **one** question set — the fixture's 104
`core_held_out` questions — and it is persona-agnostic by construction (F-02). There is no such
thing as "persona j's own questions" in this design. The questions are regrouped by *slot*, and a
slot's 13 questions are the same 13 for every persona and every cell.

**Where the guard sits:** a CPU test asserting that all N+1 sweep records carry the **identical**
`(slot, seed_index, question)` set — the direct analogue of `assert_arms_are_pairable`'s
`(fact_id, split, seed_index)` triple check. Plus a `_prove` at load that the regrouped slot buckets
are exactly 13 each across 8 slots (F-02's measured shape).

### Pitfall 3 (failure mode c) — a scorer that can see the cell indices

**What goes wrong:** subtle diagonal favouritism — an `if i == j:` branch, a different normalizer for
the diagonal, a tie-break that prefers the own value.

**Where the guard sits:** three layers, cheapest first.

- **Signature.** `inspect.signature(score_completion)` must have exactly the declared parameters and
  no `i`/`j`/`cell`/`own`. SC3 names this explicitly.
- **Structure.** Because generation and scoring live in different processes and the scorer receives
  a string plus one slot's `{label: value}` dict, there is no cell index in scope to read. This is
  the real guard; the signature pin documents it.
- **AST.** Scan the scoring module for `Compare` nodes over names in `{i, j, cell, own, diagonal}`,
  in the `test_persona_argument_is_scoped_to_the_fairness_control` register.

### Pitfall 4 (failure mode d) — crediting the base's own prior as isolation success, or as a leak

**What goes wrong:** an off-diagonal hit is counted as leakage when the base says that value
unprompted; or a `none` completion that is just the base's habitual answer is counted as a
confabulation, inflating the confabulation category.

**Where the guard sits:**

- **Upstream, at minting.** `probe_guessability` proves the base produces **zero** containments of
  each minted value before any adapter trains (F-13). This does most of the work.
- **The ISO-03 column**, run under **identical** questions, `seed_index` values, `forbid_ids` mask
  (same sha256) and `stop_ids`. D-13's base-prior derivation is a text coincidence against this
  column, per slot.
- **The `BASE_PRIOR_SEEDS` sanity anchor.** If the column does not reproduce `rose` for `pet_name`
  and `the country` for `hometown`, stop and investigate the sweep before trusting the derivation on
  the other six slots (D-13). Note the anchor covers 2 of 8 core slots and is a *screening seed
  list*, never an enumeration.

**Warning sign that costs nothing to check:** Phase 16's `base-neither` arm scored exactly **0/104**
on this same tier (F-12). Phase 17's base column should also be at or near zero on all three
personas' values. A non-zero base column is either a gate failure or a sweep bug, and either way it
must be resolved before the matrix is read.

### Pitfall 5 (failure mode e) — an alpha/rank mismatch no shape audit catches

**Status: already closed** (F-01). `load_adapter_weights` audits `LoRALinear.scale` against
`lora_config["alpha"]/["r"]` at the shared choke point, so a Phase 17 consumer that forgets to read
the config fails loudly at load time. **No Phase 17 work is required.** The only residual action is
optional: an AST regression test that the three consumer sites still pass `**artifact["lora_config"]`,
since Phase 17 multiplies the call sites from 3 to N+1.

### Pitfall 6 — value collisions that corrupt the scorer (new; not in the brief)

**What goes wrong:** `contains_value` is **substring containment after normalization**. If any
minted value is a substring of another minted value, of a Phase 14 locked/rejected value (the
contradiction lexicon), or of any of the 104 questions, the scorer produces false positives that
look exactly like leakage.

**Concrete cases:** persona A's `vorwick` inside persona B's `vorwickham` would make every correct
A-answer also register as a B-leak, manufacturing an off-diagonal hit out of nothing. A minted value
that is a substring of a question text would abort the whole run at
`assert_no_value_in_prompt` — after the model is loaded, hours in.

**Where the guard sits:** four **mechanical, pure-CPU** filters in `phase17_personas.py`, `_prove`d
at import and pinned by test, all applied at minting time:

1. `len(tok.encode(v)) <= 8` for all 24 (F-05 — budget parity).
2. `tok.decode(tok.encode(v)) == v` for all 24 (`token_census`).
3. Pairwise substring-disjointness under `normalize` across all 24 minted values **∪** the 20-value
   contradiction lexicon (`LOCKED_VALUES ∪ GATE_REJECTED_CANDIDATES`) **∪** `CALIBRATION_POOL` **∪**
   `REGISTER_ARM_POOL`. D-06 already forbids reuse; this catches near-collisions too.
4. No minted value appears in any of the 104 fixture questions under `contains_value`.

These are seconds of CPU and they close a class of silent scoring corruption. They also make the
`probe_guessability` run (the expensive GPU half) fail fast on material that was never going to work.

### Pitfall 7 — artifact clobbering and recorded-evidence guards firing late

`teach_persona.refuse_if_exists` (`:214`) refuses on all five output paths **up front**; a rerun
after a partial failure exits non-zero naming the file. `assert_report_not_clobbered` runs *before*
anything expensive in both `phase14_recall.main` and `phase16_persistence.run_one_condition`,
because *"a multi-hour run that refuses to write its report at the end has already been wasted"*
`[CITED: phase16_persistence.py:2716-2719]`. Phase 17 must put its clobber guard first in every mode.

---

## Code Examples

### The ISO-04 canary, both layers

```python
# scripts/phase17_isolation.py
import hashlib
import torch
from personacore.lora import load_adapter_weights
from personacore.lora.layer import LoRALinear


def lora_b_digest(model):
    """sha256 over every LIVE lora_B tensor, in module order — the adapter's identity IN MEMORY.

    Deliberately the live tensors and not the artifact file: a file digest proves which file was
    read, never that the tensors reached the model. All three personas share an identical key set,
    identical shapes and an identical lora_config, so keys/shape/scale audits are all silent about
    WHICH adapter is loaded (ISO-04). This digest is the only thing that is not.
    """
    h = hashlib.sha256()
    for _name, m in sorted(
        (n, m) for n, m in model.named_modules() if isinstance(m, LoRALinear)
    ):
        h.update(m.lora_B.detach().to("cpu").contiguous().numpy().tobytes())
    return h.hexdigest()


ZERO_B_DIGEST_NOTE = (
    "the identity-gate digest: lora_B is zeros at construction (lora/layer.py:30), so an adapter "
    "that 'loaded' but left lora_B at zero is a mathematically exact no-op. The base sweep MUST "
    "carry this digest and the three adapter sweeps MUST NOT."
)


def load_adapter_with_canary(model, artifact, *, label):
    """ISO-04, in-process half: a lora_B tensor ACTUALLY changed, and is not the identity gate."""
    before = {n: m.lora_B.detach().clone() for n, m in model.named_modules()
              if isinstance(m, LoRALinear)}
    load_adapter_weights(model, artifact)   # keys + shape + SCALE audits (W1, already landed)
    after = {n: m.lora_B for n, m in model.named_modules() if isinstance(m, LoRALinear)}
    _prove(
        any(not torch.equal(after[n], before[n]) for n in before),
        f"swap to {label!r} changed NO lora_B tensor — all personas share an identical lora_ key "
        "set, so every audit in load_adapter_weights passes for the wrong artifact. A no-op swap "
        "is invisible in the completions and produces a fabricated matrix (ISO-04)",
    )
    _prove(
        not any(bool((t == 0).all()) for t in after.values()),
        f"a lora_B tensor is all zeros after loading {label!r} — that is the identity gate, so "
        "the adapter branch contributes exactly nothing and this sweep is the base model wearing "
        "an adapter's name",
    )
    return lora_b_digest(model)
```

```python
# scripts/phase17_isolation.py — ISO-04, cross-process half. Runs inside --report, BEFORE scoring.
def assert_sweeps_ran_on_distinct_weights(sweep_records):
    """Assembling the report is IMPOSSIBLE unless the sweeps provably used different adapters.

    The `assert_arms_are_pairable` register (phase16_persistence.py:2658): one git_sha, distinct
    pids, identical (slot, seed_index, question) sets — plus the ISO-04 addition that no static
    scan and no in-process assertion can make, because it is a statement ABOUT the set of runs.
    """
    adapters = [r for r in sweep_records if r["sweep"] != "base"]
    digests = {r["sweep"]: r["lora_b_sha256"] for r in adapters}
    _prove(
        len(set(digests.values())) == len(digests),
        f"two sweeps recorded the SAME live lora_B digest: {digests}. The sweeps ran on identical "
        "weights, so every off-diagonal in their rows is fabricated and the diagonal is the same "
        "number reported three times (ISO-04)",
    )
    base = next(r for r in sweep_records if r["sweep"] == "base")
    _prove(
        base["lora_b_sha256"] not in set(digests.values()),
        "the adapter-off column recorded the same live lora_B digest as an adapter sweep — the "
        "control is not a control (ISO-03)",
    )
```

### Regrouping the fixture by slot (D-02)

```python
# scripts/phase17_isolation.py
import phase16_persistence as p16   # load_fixture_items, the statistics, the _prove register

def held_out_by_slot():
    """The 104 core_held_out items bucketed by SLOT — 13 per slot across 8 slots (D-02).

    `fact_id` is carried through ONLY as fixture provenance and is never a value source: every
    `fact_id` embeds Phase 14's own value (`cand_person_quillon`), which is precisely why D-02
    keys on slot. The slot is resolved through the committed fact set, not parsed from the id.
    """
    import phase14_factset as fs        # LAZY — the fact strings never reach module import time.

    items = p16.load_fixture_items()["core_held_out"]     # seed_index read VERBATIM, never re-stamped
    by_slot = {}
    for item in items:
        by_slot.setdefault(item.fact.slot, []).append(item)
    _prove(
        len(by_slot) == 8 and all(len(v) == 13 for v in by_slot.values()),
        f"the fixture regrouped to {[(k, len(v)) for k, v in sorted(by_slot.items())]}, not 8 slots "
        "x 13 questions — D-08's n=8 paired observations and every per-slot denominator rest on "
        "that balance holding exactly",
    )
    _prove(
        set(by_slot) == {f.slot for f in fs.LOCKED_FACTS},
        "the fixture's slots and the committed fact set's slots disagree",
    )
    return by_slot
```

### Assembling the four categories from a 4-label scorer (D-12 / D-13 / SC3)

```python
# scripts/phase17_isolation.py — the ONLY place that knows (i, j). Pure, CPU, no torch.
def classify(labels, own, base_texts, completion):
    """D-12's four scorer labels resolved into the FOUR report categories, at assembly.

    `labels` is score_completion's frozenset. `own` is the row's persona. This function knows the
    cell; the SCORER does not, and that separation is SC3. `base_texts` is the set of normalized
    completions the ISO-03 adapter-off column produced for THIS slot under the same question and
    seed — D-13's empirical base prior, derived rather than scored.
    """
    if own in labels:
        return "diagonal"                       # the row's own value appeared
    if labels:
        return "leak"                           # some OTHER persona's value appeared
    if recall.normalize(completion) in base_texts:
        return "base_prior"                     # D-13: coincides with the adapter-off column
    return "confabulation"                      # SC3: its own category, never sharing a cell
```

### Reusing the gate, verified end to end

```python
# scripts/phase17_isolation.py — STAT-04 satisfied by import; nothing new is written.
signs = {pair: p16.fact_signs(per_cell, pair) for pair in personas.HOLM_FAMILY_CELLS}
p_values = {pair: p16.sign_test_exact(s) for pair, s in signs.items()}
assert_phase17_family_closed(tuple(p_values))     # the Phase 17 twin (Phase 16's is arm-keyed)
_prove(
    len(p16.HOLM_FAMILY_PAIRS) == len(personas.HOLM_FAMILY_CELLS),
    f"phase16_persistence.holm prices alpha at 0.05 / len(HOLM_FAMILY_PAIRS) = "
    f"{len(p16.HOLM_FAMILY_PAIRS)}, but this phase's family is "
    f"{len(personas.HOLM_FAMILY_CELLS)}. The two agreeing at 6 is a COINCIDENCE of "
    "C(4,2) == 3x2, not a shared constant — an edit to Phase 16's CONDITION_ORDER would "
    "silently reprice this phase's gate (F-08)",
)
rows = p16.holm(p_values)                          # step-down, stops at first failure
```

**Per-cell descriptive CI — `cluster_bootstrap` needs no changes at all:**

```python
# {slot: [(k, n), ...]} — exactly cluster_bootstrap's input shape, with slots as the cluster.
lo, hi = p16.cluster_bootstrap({slot: qs for slot, qs in per_slot_questions.items()})
row = p16.report_proportion(n_answerable, n_questions, n_draws)   # Wilson + 3/n + both denominators
```

---

## Cost Model

Derived from measurements committed in this repository, not estimated from first principles.

**Measured inputs** `[VERIFIED: results/phase16_persistence_report.md:26,47,89,105; results/phase14_teaching_run.log]`

| measurement | value |
|-------------|-------|
| Phase 16 arm A (adapter-on, 270 q × 9 draws) | 10.6 min ⇒ **2.36 s/question** |
| Phase 16 arm B (adapter-off, 270 q × 9 draws) | 13.8 min ⇒ **3.07 s/question** |
| Arm A re-measured twice over 30 questions | 2.654 and 2.380 s/q — **11.5% apart** |
| One persona adapter, end to end (bins + 200 steps + canary + export + collateral PPL) | 11:27:48 → 11:29:09 UTC = **81 s** |

The report explicitly refuses a tighter single figure than "~39 min (realistically 35–44 min)" for
four arms, because *"an interval that cannot contain a repeat of its own measurement understates
real uncertainty"*. The same honesty applies below: treat every figure as ±15%.

**Derived Phase 17 budget (104 questions per sweep, MPS, fp32)**

| stage | derivation | estimate |
|-------|-----------|----------|
| ISO-01 guessability gate | 8 slots × 13 q × 4 completions = 416, cached per question (F-07) | **~2–3 min** |
| Train 3 adapters | 3 × 81 s | **~4 min** |
| 3 adapter sweeps | 3 × 104 × 2.4–2.7 s | **~13–14 min** |
| ISO-03 base column | 104 × 3.07 s | **~5 min** |
| Scoring + assembly + report | CPU, pure functions over recorded JSON | **seconds** |
| **Matrix subtotal** | | **~25 min** |
| ISO-05 replication, k=3 on the worst pair | +4 adapters (~5 min) + 4 sweeps (~18 min) | **~23 min** |
| **Total** | | **~45–55 min** of MPS wall clock |

**Conclusion: compute is not a constraint for this phase.** N=3 adapters, a 3×3 matrix, a base
column and a k=3 replication together cost about one Phase 16 four-arm run. The plan should not
trade any rigour for cost, and should not reduce draws below 9 (which would break comparability
with Phase 16's `SHARED_ARM_CONFIG.n_draws` for no meaningful saving).

Note the ISO-05 line assumes "the worst-colliding pair" means two personas retrained at two
additional seeds each — see Open Question 3.

---

## State of the Art (what changed in this repo, and when)

| Old approach | Current approach | When changed | Impact on this phase |
|--------------|------------------|--------------|----------------------|
| `LoRAConfig()` defaults at every consumer | `LoRAConfig(**artifact["lora_config"])` + scale audit at the choke point | 2026-08-14, `0a26702` / `ec3e94a` | **ISO-06 is done.** SC1's first half needs no tasks |
| `probe_guessability` implicit inside `main()` | Public entry point taking arbitrary `(value, questions)` | Phase 16, D-16 | ISO-01 imports it; a copy would be a second guessability rule |
| `enumerate(questions)` seeding | `item.seed_index`, stamped once, read verbatim from the fixture | Phase 16, PERS-05 | The pairing the matrix's cell-to-cell comparability rests on |
| `persona=` guard on one hard-coded file | AST scan over `scripts/*.py` + `src/**/*.py`, hard equality | Phase 16, D-21 | A Phase 17 driver is scanned for free (F-04) |
| Single in-prompt guard | `assert_value_in_prompt` twin + `DRAW_ALL_ASSERTED_BY`, no skip mode | Phase 16, PERS-06 | Phase 17's generation loop must assert absence for all 24 values |
| `text.split("## Verdict")[-1]` in five places | `_verdict.recorded_verdict`, one anchored regex | Phase 16, CR-02 | Reuse for Phase 17's blocking verdict |

**Deprecated / must not be reused:**
- Phase 14's `TAUGHT_THRESHOLD = 0.2486` / `HELDOUT_THRESHOLD = 0.2000` — ISO-07 forbids them here
  (derived on `CALIBRATION_POOL`; reusing that pool as a persona makes the gate circular). They must
  not appear anywhere in a Phase 17 file, and a CPU test asserting their absence from the Phase 17
  driver is cheap.
- `assert_family_closed` as-is — asserts against Phase 16's arm-keyed pair set (F-08).

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Using the fixture's own 13 held-out questions per slot as the `probe_guessability` probe set | F-07 | Low. Any base-failing probe set satisfies ISO-01; this choice buys power and alignment with the matrix. Alternative (`SLOT_QUESTION_BANK`) is what Phase 14 used and is equally valid |
| A2 | Recommending `frozenset` return for multi-match completions | Open Q1 | Medium. D-12 says "strictly persona_a\|b\|c\|none" and does not say what a double match returns. If the plan chooses a priority order instead, the order biases whichever persona sorts first |
| A3 | Recommending "all six Holm rejections" as the headline gate | Open Q2 | **High.** Not settled in CONTEXT. A partial-rejection rule would be a materially weaker claim and must be pre-registered before any adapter trains, not chosen after |
| A4 | "Worst-colliding pair" = the two personas whose off-diagonal cells are highest | Open Q3 | Medium. ISO-05 does not define it; the definition must be pre-registered *before* the matrix is read or it becomes an after-the-fact choice |
| A5 | ISO-05 k=3 costs 4 extra adapters and 4 extra sweeps | Cost Model | Low. Cost only; if k=3 means "3 total including the existing one" the estimate is already correct for 2 personas × 2 extra seeds |
| A6 | Recommending an additive `key=` on `aggregate_by_fact` over slot-as-fact_id | F-09 | Low. Both work today; option (a) is cleaner, option (c) is zero-diff |
| A7 | Recommending seeds 1338/1339 alongside 1337 for the three personas | Pattern 2 | Low. Any three distinct integers satisfy D-14; keeping 1337 for persona A preserves continuity with every other run in the project |
| A8 | Slot-level independence is defensible for the sign test | §Paired test assumptions | Medium. All 8 slots share one adapter, so a globally bad adapter is a common-mode effect. The within-slot ordering is what the test uses, which limits but does not eliminate the concern |
| A9 | Per-question cost for Phase 17 sweeps equals Phase 16's | Cost Model | Low. Same device, model, budget, draws, prompt shape; ±15% band already stated |

---

## Open Questions (RESOLVED 2026-08-14 — CONTEXT D-17..D-21)

> All five questions below were closed in `17-CONTEXT.md` **before planning ran**: Q1 -> D-17
> (frozenset on a double match), Q2 -> D-18 (all six Holm rejections), Q3 -> D-19 (`worst_pair`
> with its committed tie-break), Q4 -> D-20 (`LoRAConfig()` defaults), Q5 -> D-21 (Phase 17
> ships its own six-pairs twin). Each is a pre-registration under STAT-05 and lands as a
> committed literal in plan 17-01. The recommendations below are kept verbatim as the reasoning
> the decisions were taken on; the decisions themselves live in CONTEXT.

1. **What does the scorer return when a completion contains two personas' values for the same slot?**
   - *What we know:* D-12 fixes the label domain as `persona_a | persona_b | persona_c | none` and
     forbids any `(i, j)` argument. `contains_value` is substring containment, so
     `"i go by thessaly or vorwick"` genuinely matches two. Phase 14's committed transcripts contain
     exactly this shape (`"i go by quick and i go by quillon"`).
   - *What's unclear:* D-12 does not say. A single-label return needs a tiebreak, and every tiebreak
     is an arbitrary bias.
   - *Recommendation:* return a **`frozenset`** over the same four-label domain (empty = `none`).
     This keeps D-12's letter — the members are exactly those labels — needs no arbitrary priority,
     and lets a cell count a question when its persona is in the set. Record every multi-match as a
     descriptive **contradiction event** via the existing `find_contradictions` idiom, which is
     already the house instrument for "the model named two competing values". Pre-register before
     the run.

2. **Does "the gate cleared" require all six Holm rejections, or at least one?**
   - *What we know:* Holm's step-down can reject a subset. Phase 16 published exactly that shape
     ("3 of 6 pairs cleared their Holm step"). A comparison at 7/8 gives p = 0.0703125, above even
     the final step's alpha of 0.05, so it is retained at every position.
   - *What's unclear:* CONTEXT D-08 locks the family and the correction but not the aggregation rule
     for the phase verdict.
   - *Recommendation:* **all six.** The claim is "separately-taught personas stay isolated"; one
     retained comparison means one persona's value appeared under another's adapter at a rate the
     test cannot separate from that adapter's own recall, which is not isolation. Publish all six
     Holm rows regardless so a partial result is readable, and make the D-10 all-fail branch fire on
     anything less than six. **This must be a committed literal before any adapter trains (STAT-05).**

3. **What exactly is "the worst-colliding pair" in ISO-05, and when is it chosen?**
   - *What we know:* ISO-05 requires it replicated across seeds, reported descriptively
     (min/max/median, never a hypothesis test), and D-16 places it on top of D-14 as a separate
     layer.
   - *What's unclear:* the selection rule (highest single off-diagonal cell? highest mean of the two
     cells in the (i,j)/(j,i) pair? highest count of slots with any off-diagonal hit?) and whether
     "k=3 seeds" counts the original adapter.
   - *Recommendation:* pre-register the selection rule as a committed function
     (e.g. `worst_pair = argmax over unordered {i,j} of mean(rate(i,j), rate(j,i))` in the question
     unit) so the choice is mechanical rather than made after seeing the matrix, and define k=3 as
     the original seed plus two more. Selecting after the fact is legitimate *only* because the
     output is descriptive — but a committed rule costs nothing and removes the argument.

4. **Which alpha/rank for the three Phase 17 adapters?**
   - *What we know:* CONTEXT leaves this to discretion and notes a non-default alpha is now safe
     because the load path audits scale. `LoRAConfig()` defaults are `r=8, alpha=16.0` → 331,776
     trainable params, 1.35 MB, `scale=2.0`.
   - *Recommendation:* **keep the defaults.** Changing them buys nothing this phase measures, and
     keeping them means the three Phase 17 diagonals are directly readable against Phase 14's 0.3483
     (draw unit) and Phase 16's 0.865385 (question unit), which is what D-10's all-fail branch needs
     to declare "not judgeable" versus "leakage found". A non-default alpha would be a good
     *deliberate* exercise of the new audit — but it would cost the anchor.

5. **Does Phase 17 need its own twin of `test_nothing_outside_the_six_pairs_enters_the_verdict_path`?**
   - *What we know:* `_GATE_MODULES` is file-scoped to Phase 16's two drivers (F-08). A Phase 17
     driver calling `holm` is neither red nor covered.
   - *Recommendation:* yes — add `scripts/phase17_isolation.py` to a Phase-17 twin of that scan.
     Leaving it uncovered repeats the exact blindness D-21 widened `_scanned_files()` to close.

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | everything (3.14 is the box default and is unsupported) | ✓ | `.venv/` present, used for every check in this document | none — mandatory per CLAUDE.md |
| `torch` | sweeps, training, adapter load | ✓ | 2.7.1 (per `results/phase14_teaching_run.log`) | none |
| MPS backend (Apple Silicon M3) | training + sweeps | ✓ | `[preflight] device=mps cc=n/a torch=2.7.1` | CPU (slower); Kaggle P100 unnecessary at this cost |
| `checkpoints/convbase_best.pt` | `teach_persona` (full resume checkpoint, `weights_only=False`) | ✓ | git `04e724c6`, step 4000, val_loss 1.5235939979553224 | none — training is impossible without it |
| `checkpoints/convbase_slim.pt` | `load_adapted_model` (`weights_only=True`) | ✓ | `checkpoints/` populated (49 entries) | re-export via `scripts/export_slim.py` |
| `artifacts/tokenizer.json` | census, encode/decode, `forbid_ids` | ✓ | frozen, git-tracked, 8192 ids / 547 live — verified by execution | none — never retrain |
| `results/phase16_recall_sample.json` | the binding fixture | ✓ | 270 questions, `binding_decision` present — verified by execution | none — regeneration is forbidden |
| `data/dialog_val.bin` + mask | `train_arm`'s collateral-collapse metric | ✓ (`data/` populated) | gitignored | `scripts/prepare_dialog_corpus.py` |
| `pytest` / `ruff` | CPU test suite, lint | ✓ | `pytest~=9.0`, `ruff~=0.15` | none |
| Network | — | not required | — | the whole design is offline by construction |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

---

## Validation Architecture

### Test framework

| Property | Value |
|----------|-------|
| Framework | `pytest~=9.0` |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]`, `testpaths = ["tests"]`, `pythonpath = ["."]` |
| Quick run command | `.venv/bin/pytest -q tests/test_phase17_*.py` |
| Full suite command | `make test` (i.e. `pytest -q`) |
| Constraint | **CPU-only, GPU-free, no checkpoint I/O, no model load, no generation** — the register every Phase 14/15/16 test file follows. Drivers are loaded with `importlib.util.spec_from_file_location` so `main()` never runs |

### Phase requirements → test map

| Req | Behavior | Type | Automated command | File exists? |
|-----|----------|------|-------------------|-------------|
| ISO-01 | 24 values pass the 4 mechanical minting filters; no substring collision with each other, the 20-value lexicon, or the 104 questions | unit | `pytest tests/test_phase17_personas.py -x` | ❌ Wave 0 |
| ISO-01 | Every minted value costs ≤ 8 tokens and round-trips exactly | unit | `pytest tests/test_phase17_personas.py::test_census -x` | ❌ Wave 0 |
| ISO-01 | Training refuses without a recorded GO/ADAPT in the Phase 17 report | unit (monkeypatched path) | `pytest tests/test_phase17_personas.py::test_verdict_blocks -x` | ❌ Wave 0 |
| ISO-02 | All N+1 sweep records carry an identical `(slot, seed_index, question)` set | unit (synthetic records) | `pytest tests/test_phase17_stats.py::test_sweeps_are_pairable -x` | ❌ Wave 0 |
| ISO-02 | Fixture regroups to exactly 8 slots × 13 questions | unit | `pytest tests/test_phase17_scoring.py::test_slot_regrouping -x` | ❌ Wave 0 |
| ISO-03 | The base sweep record carries the all-zero `lora_B` digest and the adapter sweeps do not | unit (synthetic records) | `pytest tests/test_phase17_stats.py::test_base_column_is_a_control -x` | ❌ Wave 0 |
| ISO-04 | In-process canary fires when the same artifact is loaded twice (**mutation-proved**) | unit (tiny GPT, CPU) | `pytest tests/test_phase17_scoring.py::test_swap_canary_bites -x` | ❌ Wave 0 |
| ISO-04 | `--report` refuses when two sweep digests match | unit | `pytest tests/test_phase17_stats.py::test_report_refuses_identical_digests -x` | ❌ Wave 0 |
| ISO-05 | Replication is reported as min/max/median and reaches neither `holm` nor `sign_test_exact` | static AST | `pytest tests/test_phase17_stats.py::test_replication_is_not_gated -x` | ❌ Wave 0 |
| ISO-06 | The three consumer sites still inject `**artifact["lora_config"]` | static AST | `pytest tests/test_lora_inject.py -x` (extend) | ✅ partially — `test_load_adapter_weights_refuses_wrong_alpha` exists |
| ISO-07 | `0.2486` / `0.2000` appear nowhere in any Phase 17 file | static source scan | `pytest tests/test_phase17_stats.py::test_no_phase14_thresholds -x` | ❌ Wave 0 |
| STAT-01 | Signs are computed on the question rate, not the draw rate | unit | `pytest tests/test_phase17_stats.py::test_signs_use_the_question_unit -x` | ❌ Wave 0 |
| STAT-02 | No bare `0%` in the report; every zero cell carries a denominator and a bound | unit on the writer | `pytest tests/test_phase17_stats.py::test_no_bare_zero_percent -x` | ❌ Wave 0 |
| STAT-03 | Family is exactly 6; nothing else reaches `holm`; the Phase-16 `m == 6` coincidence is pinned | unit + static AST | `pytest tests/test_phase17_stats.py -x` | ❌ Wave 0 |
| STAT-04 | `pyproject.toml` is byte-identical; the Phase 17 driver imports only stdlib + repo modules | static AST + file hash | `pytest tests/test_phase17_stats.py::test_no_new_dependencies -x` | ❌ Wave 0 |
| STAT-05 | Gate constants are module-level literals; the driver commit precedes every `results/phase17_*` artifact | static + git | `pytest tests/test_phase17_stats.py::test_prereg_precedes_results -x` (the `PREREG-02` register) | ✅ pattern exists — `tests/test_phase16_prereg.py` |
| STAT-06 | No aggregate 9-cell rate is computed or printed | static AST | `pytest tests/test_phase17_stats.py::test_no_nine_cell_aggregate -x` | ❌ Wave 0 |
| SC3 | `inspect.signature(score_completion)` carries no `(i, j)`; no `if i == j:` in the scoring path | unit + static AST | `pytest tests/test_phase17_scoring.py::test_scorer_is_cell_blind -x` | ❌ Wave 0 |
| D-10 | The all-fail branch text is committed and the writer emits it when fewer than six reject | unit on the writer | `pytest tests/test_phase17_stats.py::test_all_fail_branch -x` | ❌ Wave 0 |

**Manual-only, with justification:** the ISO-01 human GO/ADAPT verdict. It is a judgment on quoted
base completions (close-call semantic proximity), which is precisely the thing exact-match cannot
see — Phase 14's own reasoning. Its *enforcement* is automated (`_require_go_verdict` refuses on
STOP/PENDING); only the judgment itself is manual.

### Sampling rate

- **Per task commit:** `.venv/bin/pytest -q tests/test_phase17_*.py` (seconds, CPU)
- **Per wave merge:** `make test` (full suite; the v2.0 baseline was 407 passed / 1 skipped in ~117 s)
- **Phase gate:** full suite green plus `make lint` before `/gsd:verify-work`

### Wave 0 gaps

- [ ] `tests/test_phase17_personas.py` — minting filters, census, verdict gate (ISO-01)
- [ ] `tests/test_phase17_scoring.py` — cell-blindness, slot regrouping, swap canary (ISO-02/04, SC3)
- [ ] `tests/test_phase17_stats.py` — family closure, unit, thresholds, dependencies (STAT-01..07)
- [ ] No framework install needed — `pytest` is already in `[dev]` and `.venv` is live

---

## Security Domain

`security_enforcement` is not set in `.planning/config.json`; treating it as enabled. This phase adds
no network surface, no user input, no auth and no persistence beyond local files, so most ASVS
categories are structurally inapplicable. Recording that honestly rather than padding the table.

| ASVS category | Applies | Standard control |
|---------------|---------|-----------------|
| V2 Authentication | no | No accounts, no sessions, no service. Local scripts only |
| V3 Session Management | no | Same |
| V4 Access Control | no | Same |
| V5 Input Validation | **yes** | Every checkpoint read is either `weights_only=True` (`load_slim` / `load_adapter` — the restricted unpickler, zero code execution) or a documented TRUSTED-only read of the project's own full resume checkpoint (`torch.load(CONVBASE_BEST, weights_only=False)`, T-09-11/T-14-04). Phase 17 must use `load_adapted_model` / `load_adapter` for every adapter and must not introduce a direct `torch.load` on a shareable artifact |
| V6 Cryptography | partial | `hashlib.sha256` is used only as a **content digest** for provenance and the ISO-04 canary, never for a security boundary. No key material, no signatures. Nothing is hand-rolled |

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Arbitrary code execution via a pickled `.pt` | Elevation of Privilege | `weights_only=True` at the `load_slim` / `load_adapter` choke points; the one `weights_only=False` read is the project's own checkpoint and is documented as such |
| Half-applied adapter leaving a corrupted model | Tampering | `load_adapter_weights` audits keys, shape/dtype and scale **before** any tensor is copied — a bare `strict=False` copies matching tensors first and raises only at the end |
| Silent substitution of the wrong adapter | Spoofing | ISO-04's two-layer canary (Pitfall 1) — the only mechanism that distinguishes three artifacts with identical key sets, shapes and configs |
| Fabricated evidence via a clobbered report | Repudiation | `_verdict.recorded_verdict` + `assert_report_not_clobbered` first in every mode; `refuse_if_exists` on every training output |
| Personal data in a public artifact | Information Disclosure | No candidate value is real personal data (T-14-05); everything in `results/` ships publicly. The 24 minted values must be invented, which D-06 already requires |

---

## Sources

### Primary (HIGH confidence) — read or executed in this repository, 2026-08-14

- `src/personacore/lora/inject.py` — `inject_lora`, `load_adapter_weights` (key + shape + **scale** audit at :119-129), `set_adapter_enabled`, `adapter_disabled`, `merge`/`unmerge`
- `src/personacore/lora/layer.py` — `LoRALinear`, `scale = alpha/r` at :27, `lora_B = zeros` identity gate at :30
- `src/personacore/lora/config.py` — `LoRAConfig(r=8, alpha=16.0)`, `TARGET_PROJECTIONS`
- `src/personacore/checkpoint.py:196-260` — `export_adapter` / `load_adapter` (`weights_only=True`)
- `scripts/phase14_recall.py` — `derive_recall_budget` (:120), `RECALL_MAX_NEW_TOKENS = 48` (:143), `question_seed` (:227), `assert_values_fit` (:239), `normalize`/`contains_value`/`score_question`/`find_contradictions` (:279-351), `assert_no_value_in_prompt`/`assert_value_in_prompt` (:398-469), `load_adapted_model` (:496), `draw_all` (:595), `complete_question` (:640), `RecallItem`/`stamp_seed_indices`/`build_question_sets` (:725-819), `run_scored_recall` (:822), `run_closed_book_control` (:1073)
- `scripts/phase16_persistence.py` — `ArmConfig`/`SHARED_ARM_CONFIG` (:136-177), `resolve_forbid` (:191), `load_fixture_items` (:293), `run_condition` (:474), `aggregate_by_fact` (:779), `cluster_bootstrap` (:843), `report_proportion` (:930), `HOLM_FAMILY_PAIRS`/`HOLM_ALPHA`/`SIGN_TEST_N`/`SIGN_TEST_ALTERNATIVE` (:1003-1035), `fact_signs` (:1056), `sign_test_exact` (:1088), `assert_family_closed` (:1142), `holm` (:1170), `compare_arms` (:1205), `per_fact_by_arm` (:2155), `build_parser`/`_USAGE` (:2557-2600), `assert_arms_are_pairable` (:2658), `run_one_condition` (:2713)
- `scripts/phase14_factset.py` — `Fact` (:51), `CANDIDATE_POOL`/`CALIBRATION_POOL`/`REGISTER_ARM_POOL` (:71-124), `SLOT_QUESTION_BANK` (:151), `BASE_PRIOR_SEEDS` (:299), `token_census` (:313), `exact_match_clean` (:334), `LOCKED_FACTS` (:390), `GATE_REJECTED_CANDIDATES` (:429), `VALUE_TOKEN_CENSUS` (:451), `render_family` (:824)
- `scripts/phase14_factset_gate.py` — `probe_guessability` (:111), `assert_report_not_clobbered` (:161), the census + probe-cache `main()` (:185-468)
- `scripts/teach_persona.py` — `_require_go_verdict` (:166), `arm_outputs` (:190), `refuse_if_exists` (:214), `arm_spec` (:383), `build_arm_bins` (:403), `sanity_check` (:337), `LORA_CFG`/`LR`/`MAX_STEPS` (:478-498), `train_arm` (:501)
- `scripts/erasure_gate.py` — `wilson_upper_bound` (:139), `rule_of_three` (:161)
- `scripts/_verdict.py` — `recorded_verdict` (:27)
- `tests/test_phase16_fixture_regen.py` — the five drift guards, clean-room (#4) and binding decision (#5)
- `tests/test_phase14_scoring.py:409-643` — `PERSONA_ALLOWLIST`, `_scanned_files`, `test_persona_argument_is_scoped_to_the_fairness_control`, `DRAW_ALL_ASSERTED_BY`, `test_every_draw_all_call_site_asserts_something`
- `tests/test_phase16_stats.py:586-829` — Holm family guards, `_GATE_MODULES` scope, `test_holm_reads_the_family_length_rather_than_a_retyped_six`
- `results/phase16_recall_sample.json` — the binding fixture; regrouped by slot during this research
- `results/phase16_arm_adapter-only.json` — the recorded per-question record shape, `completions` included
- `results/phase16_persistence_report.md` — measured wall clocks (:26,47,89,105), per-fact table (:136-170), pooled rates (:175-178), gate table, verdict
- `results/phase14_teaching_run.log` — the 81 s end-to-end adapter teach (11:27:48 → 11:29:09 UTC)
- `results/phase14_calibration_report.md` — calibration arm wall clocks
- `.planning/quick/260814-d0j-close-w1-lora-consumers-inject-config-de/SUMMARY.md` — the W1 closure
- `pyproject.toml`, `Makefile`, `tests/conftest.py`, `.planning/config.json`

**Executed during research (not merely read):** tokenizer census over 24 invented values;
`sign_test_exact` / `fact_signs` / `holm` on a Phase-17-shaped 6-pair cell family;
`wilson_upper_bound` / `rule_of_three` / exact Clopper–Pearson at n ∈ {8, 13, 104};
`render_family` on a synthetic `Fact`; fixture regrouping by slot.

### Secondary (MEDIUM-HIGH confidence) — external, verified against primary statements

- https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method — the step-down procedure and the subadditivity proof of FWER control under arbitrary dependence
- Holm, S. (1979), *A Simple Sequentially Rejective Multiple Test Procedure*, Scandinavian Journal of Statistics **6**:65–70 — the original; controls FWER without assumptions on the correlation structure of the p-values
- https://arxiv.org/pdf/1712.03305 — *Asymptotic false discovery control of the Benjamini-Hochberg procedure for pairwise comparisons*: pairwise-comparison statistics do **not** exhibit positive regression dependency; BH's control there is asymptotic and directional only
- Benjamini & Yekutieli (2001) — PRDS as the condition under which BH's FDR control extends; α/Σ(1/k) required under arbitrary dependence
- https://en.wikipedia.org/wiki/Rule_of_three_(statistics) — `(1−p)^n = 0.05` ⇒ `n·ln(1−p) = −2.9957`, rounded to −3 with `ln(1−p) ≈ −p`, giving `3/n`; derived from the one-sided Clopper–Pearson exact limit
- Hanley & Lippman-Hand (1983); Jovanovic & Levy (1997), *A Look at the Rule of Three*, The American Statistician **51**(2) — the canonical statements and their assumptions
- https://www.statisticssolutions.com/free-resources/directory-of-statistical-analyses/sign-test/ — the sign test is distribution-free and assumes independence **across pairs**, not symmetry

### Tertiary (LOW confidence) — none

No claim in this document rests on an unverified web search. Every recommendation is either verified
in the tree, executed, or explicitly tagged in the Assumptions Log.

---

## Metadata

**Confidence breakdown:**

- **Repo findings (F-01..F-13): HIGH** — every one was read in the working tree, and eleven were
  additionally executed (tokenizer census, statistics reuse, fixture regrouping, `render_family`).
- **Standard stack: HIGH** — zero new packages; every symbol's location and signature verified.
- **Architecture (generate/score split, two-mode driver, canary placement): HIGH** — follows the
  committed `phase16_persistence.py` shape, and the recorded arm JSON proves completions already
  survive to disk.
- **Statistics: HIGH** — the Holm/BH/rule-of-three claims are backed by primary sources and the
  arithmetic was executed against the repo's own functions.
- **Pitfalls: HIGH for (b)(c)(d)(e) and for Pitfall 6/7; MEDIUM for (a)** — the guard placement is
  certain, but the *shape* the fake result takes under a failed swap depends on the design and is
  argued in §Pitfall 1 rather than measured.
- **Cost model: MEDIUM-HIGH** — derived from measured per-question costs on the same device/model/
  budget; the repo's own ±11.5% repeat-measurement spread is carried through as ±15%.
- **Open questions 1–5: LOW by construction** — these are genuinely unsettled and are handed to the
  planner as pre-registration decisions, not as findings.

**Research date:** 2026-08-14
**Valid until:** 2026-09-13 (30 days). The repo half is stable — the only invalidator is an edit to
`phase16_persistence.py`'s `CONDITION_ORDER` (which would reprice `holm`'s `m`, see F-08) or a
regeneration of the binding fixture (which the committed `binding_decision` forbids).
