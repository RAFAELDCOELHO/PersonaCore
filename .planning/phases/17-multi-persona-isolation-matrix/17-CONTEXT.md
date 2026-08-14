# Phase 17: Multi-Persona Isolation Matrix - Context

**Gathered:** 2026-08-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Measure whether separately-taught personas stay isolated **when they are built to collide** — N=3
adversarial personas carrying contradictory values in the *same* slots, scored as a full 3x3
cross-matrix plus an explicit adapter-off base column, with the gated quantity being the
within-run diagonal-vs-off-diagonal contrast.

This phase clarifies HOW to implement that. It adds no capabilities. Requirements are STAT-01..06
and ISO-01..07 as written in `.planning/REQUIREMENTS.md`.

**ISO-06 is already satisfied before planning begins.** It is audit item W1, closed 2026-08-14 in
quick task `260814-d0j` (`0a26702`, `ec3e94a`) — the three runtime consumers now inject with
`LoRAConfig(**artifact["lora_config"])`, and `load_adapter_weights` additionally audits every
`LoRALinear.scale` against the artifact's own `alpha/r`, so a Phase-17 consumer that forgets to
read the config fails loudly at load time instead of applying the delta at the wrong magnitude.
That closes half of SC1; the ISO-04 adapter-swap canary is still to build.

</domain>

<decisions>
## Implementation Decisions

### Shared-slot questions — provenance and tier

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

### Persona collision design

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

### What gets gated

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

### Scorer taxonomy

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

### Training and seed protocol

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The binding evaluation fixture (do not regenerate)
- `results/phase16_recall_sample.json` — the 270-question fixture; its `binding_decision` field is
  the v3.0 cross-phase lock. Phase 17 consumes `questions.core_held_out` (104).
- `tests/test_phase16_fixture_regen.py` — the five drift guards, including the clean-room property
  (#4) and the committed binding decision (#5).

### Persona material and the pre-flight gate
- `scripts/phase14_factset.py` — `Fact(id, slot, value, tier)`, `LOCKED_FACTS`,
  `CALIBRATION_POOL` (forbidden as a persona by ISO-07), `REGISTER_ARM_POOL`,
  `GATE_REJECTED_CANDIDATES` (the contradiction-detector lexicon source), `BASE_PRIOR_SEEDS`.
- `scripts/phase14_factset_gate.py` — `probe_guessability` (:111, the D-16 public entry point;
  import, never copy) and the tokenizer census.

### Statistics to import, not rewrite (STAT-04)
- `scripts/phase16_persistence.py` — `sign_test_exact` (:1088), `SIGN_TEST_N = 8` (:1016),
  `holm` (:1170), `HOLM_ALPHA` (:1005), `cluster_bootstrap` (:843).

### LoRA load path (ISO-06 / ISO-04)
- `src/personacore/lora/inject.py` — `inject_lora`, `load_adapter_weights` (key + shape + **scale**
  audit), `set_adapter_enabled`. The scale audit is the ISO-06 mechanism.
- `.planning/quick/260814-d0j-close-w1-lora-consumers-inject-config-de/SUMMARY.md` — how W1 was
  closed and what the audit guarantees for the N-adapter swap path.

### Prior decisions that constrain this phase
- `.planning/phases/16-weight-vs-prompt-persistence-control/16-CONTEXT.md` — D-07 (gated tier),
  D-16 (gate widening), D-23 (contradiction lexicon), D-29 (sign-test convention), D-30
  (instrument-blind vs phenomenon-absent).
- `.planning/REQUIREMENTS.md` §"Multi-Persona Isolation Matrix (Phase 17)" — ISO-01..07 verbatim.
- `.planning/ROADMAP.md` §"Phase 17" — the five success criteria.
- `.planning/milestones/v2.0-MILESTONE-AUDIT.md` — W1's origin (`:45`) and the remaining
  non-blocking carry-overs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase16_persistence.sign_test_exact` / `holm` / `cluster_bootstrap`: the entire inferential and
  descriptive statistics surface. `SIGN_TEST_N = 8` already equals Phase 17's 8 slots, so the gate
  needs no new statistics at all — STAT-04 is met by import.
- `phase14_factset_gate.probe_guessability(model, tok, device, forbid, value, questions, *, start_index=0)`:
  the pre-flight instrument for all 24 minted values. Phase 16 widened it additively (0 deletions)
  *specifically* so Phase 17 would import one implementation rather than copy it.
- `phase14_recall.load_adapted_model(device, adapter_path=None)`: the shared model-build entry
  point. Phase 16 already calls it (`phase16_persistence.py:2741`); Phase 17 calls it per adapter.
  It now injects at the artifact's own `lora_config`.
- `personacore.lora.set_adapter_enabled` and `load_adapter_weights`: the swap mechanics the ISO-04
  canary must watch.

### Established Patterns
- **Pre-registration lives in the committed driver** — gate constants are module-level literals
  pushed before the run they judge, and verdicts are computed by *importing* them, never retyped
  in prose (STAT-05, carried from v2.0 unchanged).
- **The all-fail branch is written before the number exists** (Phase 16 D-14: no
  investigate-the-instrument escape hatch; Phase 12 recorded `λ*=None`; Phase 16 recorded "not
  demonstrable at n=8"). D-10 above is this phase's instance.
- **Guards are mutation-proved**, not merely written — a guard nobody has watched fail is a guard
  nobody has verified (Phase 15's D-07 precedent; the W1 scale audit followed it).
- **Import, never copy** — a duplicated rule is a rule that can drift (Phase 16 D-16).

### Integration Points
- The adapter-off column (ISO-03) must run under **identical** questions, seeds, `forbid_ids` and
  `stop_ids` as the three adapter sweeps, because D-13 derives the base-prior category by
  coincidence against it.
- The ISO-04 swap canary sits between `load_adapter_weights` and the first generation of each
  sweep: all personas share identical `lora_` key sets, so a silently failed swap is a full no-op
  that yields the most flattering possible wrong answer — a perfect diagonal with zero leakage.

</code_context>

<specifics>
## Specific Ideas

- Three premises the user asked to verify **before** locking a decision were checked against the
  code and **two came back false**. They are recorded inline at D-01, D-06 and D-13 rather than
  silently corrected, because each changed the design: the fixture already contains the material
  the user thought had to be authored; `GATE_REJECTED_CANDIDATES` has 1 value per core slot rather
  than 3, forcing minting; and `BASE_PRIOR_SEEDS` covers 2 of 8 core slots, forcing the base-prior
  category to be derived from the adapter-off column instead of a static list.
- The user asked that D-11 (instrument-blind vs phenomenon-absent) be recorded as a **milestone
  pattern spanning Phases 16, 17 and 18**, not as a decision local to this phase.

</specifics>

<deferred>
## Deferred Ideas

- **Token-neighbour collision** (values that are near-identical in BPE surface form) — explicitly
  out of scope per D-05. It tests tokenization robustness, a different research question, and
  would need its own phase.
- **Reusing `checkpoints/persona_adapter.pt` as persona A** — rejected at D-07 for the lexicon
  confound, not deferred for later; recorded so the saving is not rediscovered and taken silently.

### Open risks handed to the researcher (investigation, not user choices)
1. **Feasibility, the phase's first premise:** minting 24 distinctive values that survive the
   tokenizer census against a frozen tokenizer with only **547 live ids of 8,192**. Phase 14 chose
   8 such values under the same constraint. If a slot cannot yield 3 encodable-and-decodable
   values, D-04's all-8-slots collision tightens and must be revisited before planning locks.
2. **The 0.0005 Holm margin** makes the gate effectively all-or-nothing at 8 slots. State this in
   the pre-registration so an 8/8 miss reads as a known property of the design, not a surprise.

</deferred>

---

*Phase: 17-multi-persona-isolation-matrix*
*Context gathered: 2026-08-14*
