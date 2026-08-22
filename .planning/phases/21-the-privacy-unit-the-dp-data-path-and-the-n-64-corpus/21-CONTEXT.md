# Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus - Context

**Gathered:** 2026-08-22
**Status:** PARTIAL — shard geometry and the replay path are LOCKED; three areas remain OPEN
(see `<open_questions>`). Re-run `/gsd-discuss-phase 21` and choose "Update it" to close them.

<domain>
## Phase Boundary

Phase 21 fixes **what a privacy record is** and makes that definition structurally true in the
data path. Requirements UNIT-01 … UNIT-06. Depends on Phase 20 (complete, 17/17, re-verified 7/7).

Implied deliverables, from ROADMAP SC1-SC5:

1. `PRIVACY_UNIT = "one taught fact"` as a committed decision carrying its own arithmetic (UNIT-01)
2. A **new** fact-aligned batch function, plus an additive `build_bins(..., align_facts=None)`
   kwarg **byte-identical to v2.0 when `None`** (UNIT-02)
3. A structural check proving no `block_size`-aligned window carries ids from two facts (UNIT-02)
4. The effective per-fact multiplicity **measured**, not inferred (UNIT-03)
5. The replay-in-the-lot decision with its ε consequence, and δ pinned as the literal `1e-5` with
   the rejected `1/N^1.1` recipe's self-contradiction recorded (UNIT-04, UNIT-05)
6. An n=64 corpus of **unscored filler facts** disturbing no published instrument (UNIT-06)

**No ε is computed in this phase.** The artifact is a *unit* and the path that makes it real.
An ε computed against the wrong unit is not a number a re-run can correct — which is why this is
the milestone's longest dependency chain and why it is design work before it is code.

**Carried forward from Phase 20 — locked, not reopened here:**

- **D-33** — `V4_ARTIFACT_GLOBS = ("results/phase20_*",)` ONLY. Each phase adds its own prefix at
  the moment it first writes results. **Phase 21 writes results, so it MUST add `results/phase21_*`
  to `tests/test_phase20_prereg.py::V4_ARTIFACT_GLOBS`, proven RED-then-GREEN in a throwaway repo
  (D-22).** D-33 names the cost explicitly: an `assert` catches an empty match set, never an
  incomplete one — a phase that forgets its prefix fails **silently**, and its artifacts sit
  outside the ancestry guard.
- **D-24** — `scripts/mitigation_gate.py` is FROZEN. Corrections are dated continuations via
  `scripts/_addendum.py`, never edits. Editing it turns the ancestry guard permanently red and
  `git rm` + re-add cannot undo it.
- **D-13** — the extraction noise floor is **Phase 23** (CTRL-03), gated *behind this phase's
  corpus*. Phase 21 is what unblocks it.
- **D-17** — `f_C = 0.5` sits only **2.24×** above the measured non-vacuity floor `0.2237`. There
  is little room before a dialogue collapse stops being distinguishable from a pass; this bounds
  how much dialogue capability the DP arm may spend.

**A correction to a Phase 20 deferred item, recorded so it is not inherited wrong.**
`20-CONTEXT.md:621-623` says the GATE-10 fallback tolerance (D-26) "must be decided **before Phase
21's CAL-03 runs**". **CAL-03 is Phase 23**, not Phase 21 (`.planning/REQUIREMENTS.md:328`,
`.planning/ROADMAP.md:382`). The deadline stands — before CAL-03 — but it is **not this phase's
decision** and Phase 21 must not attempt to set it.

</domain>

<decisions>
## Implementation Decisions

### Shard geometry — what one privacy record looks like on disk

- **D-01 — the shard geometry is RAGGED: each fact padded to its OWN `ceil(tokens / block_size)`
  windows, never to a common W.** Measured on the frozen tokenizer over the 8 `LOCKED_FACTS`
  through the taught families (`F1 F2 F4 F5 F6`):

  | fact | rows | tokens | windows @256 | pad |
  |---|---|---|---|---|
  | `cand_person_quillon` | 22 | 892 | 4 | 132 |
  | `cand_dog_zorp` | 22 | 867 | 4 | 157 |
  | `cand_cat_zibby` | 22 | 897 | 4 | 127 |
  | `cand_sister_orsala` | 22 | 1022 | 4 | 2 |
  | `cand_town_brindlemoor` | 22 | 916 | 4 | 108 |
  | `cand_street_marrowgate` | 22 | 1041 | **5** | 239 |
  | `cand_year_1987` | 22 | 976 | 4 | 48 |
  | `cand_house_7412` | 22 | 970 | 4 | 54 |

  **TOTAL 176 rows / 7,581 tokens / 33 windows / 867 pad tokens = 10.26% of the padded bin.**
  This independently confirms UNIT-03's "22 rendered rows per fact" (176 / 8) from the code rather
  than from the requirement text. Uniform-at-W=5 would cost **2,619 pad tokens ≈ 24%**.

  The soft tier, which rides along in the v3.0 `real` recipe (`n_facts=10`), is **larger**:
  `cand_color_chartreuse` 1,275 tokens → **5 windows**, `cand_food_marzipan` 1,162 → **5 windows**.
  So at n=10 the ragged distribution is `(4,4,4,4,4,5,4,4,5,5)`, not `(4,…,5,…)`.

- **D-02 — the `vmap` 1.07× figure does NOT govern this phase, and uniform-at-W is a PRECONDITION
  for the vmap route rather than an optimization of it. Measured, not reasoned.**
  Benchmark on the real `GPT(ModelConfig())` + `inject_lora` (36 wrapped, 72 tensors, 331,776
  params), MPS, sync-fenced:

  | path | per-step | vs batched |
  |---|---|---|
  | A — batched reference, 33 windows, no per-record grads | 401.00 ms | 1.00× |
  | **B — fact-aligned accumulation, RAGGED `(4,4,4,4,4,5,4,4)`** | **455.92 ms** | **1.14×** |
  | C — fact-aligned accumulation, UNIFORM W=5 (40 windows) | 555.73 ms | 1.39× |
  | D — `vmap` over 8 facts, UNIFORM W=5 | 541.74 ms | 1.35× |
  | E — `vmap` over facts, RAGGED | **`torch.stack` REFUSES**: `[4, 257]` entry 0 vs `[5, 257]` entry 5 |

  **The mechanism.** Research measured `vmap(grad(functional_call))` at 1.07× producing per-**window**
  gradients inside one batch. Here the record is a **fact** = 4–5 windows, so `vmap` over facts needs
  a fact batch dimension, which ragged shards cannot form. But under fact-aligned accumulation
  **one micro-step IS one privacy record**, so the ordinary backward hands back the per-record
  gradient directly and `vmap` leaves the critical path entirely. Ragged accumulation (1.14×) is
  therefore cheaper than *both* uniform accumulation (1.39×) and vmap-uniform (1.35×).
  **Ragged wins on both axes at once — 10.26% padding vs 24%, AND 1.14× vs 1.39×.**

  **Exactness is not the trade.** Per-fact gradient norms from the accumulation loop and from
  `vmap` agree to a worst relative difference of **3.116e-08** — the same order as research's
  6.5e-08 against batch-1 truth. The cheap path is not the approximate path.

  **Bounds, stated not glossed:** synthetic `torch.randint` ids rather than the real bins;
  5 reps (3 for vmap), single process, no confidence interval. A/B/C/D were measured back-to-back
  in one process, so the **ratios** are the finding and the absolute ms are noisy.

- **D-03 — within one fact, the loss is a MEAN over its windows, never a SUM.** Every record
  contributes a same-scale gradient regardless of whether it has 4 or 5 windows, so the geometry
  artifact is normalized away **before** clipping. **The cost is accepted and named:** tokens are
  not weighted equally across the corpus (a 5-window fact's windows count 1/5 each, a 4-window
  fact's count 1/4). That is the **right** asymmetry, because it weights by *privacy record* — not
  by the artifact of how text happens to pack into `block_size = 256`.

- **D-04 — D-03 costs ZERO new loss code, and that was verified in the existing source.**
  `get_batch_memmap_masked` already sets `y[m == 0] = -100` (`src/personacore/training/data.py:125`)
  and `gpt.py:212` calls `F.cross_entropy` with the default `reduction="mean"`, which averages over
  **non-ignored targets only**. With one fact per micro-step that IS mean-over-the-record. Padding
  masked to `0 → -100` contributes nothing and does not dilute the mean.

### The structural proof — SC2's "no window spans two facts"

- **D-05 — the aligned path carries a THIRD BIN: `*_fact.bin`, `uint16` fact index, 1:1 aligned
  with the token and mask bins.** The check asserts every `block_size`-aligned window contains
  exactly **ONE** distinct fact id. This is a **direct proof of content**, not an inference from
  offsets: a packing bug that writes correct offsets over wrong bytes passes an offset check and
  fails this one.

- **D-06 — the fact-id map is CONSUMED BY THE LOADER AT RUN TIME, not merely asserted at build
  time.** That is what makes `grad_accum_steps = n_facts` *genuinely true* rather than declared,
  and it makes the "one window, one fact" guarantee verifiable **on every access** instead of
  trusted from a past construction. `build_bins`' existing proof-1 (1:1 length equality) extends
  from two files to three.

### Replay, the DP lot, and a side channel nobody had named

- **D-07 — replay sits OUTSIDE the privacy N entirely: honest `q = 1`, `N = n_facts`.**
  Replay is public PersonaChat serving a **training-stability** role; it is not private data
  needing protection. Counting it inside N would shrink q artificially and produce a flatteringly
  small ε that does not reflect what the mechanism actually protects — **the exact trap UNIT-04
  names**. Measured: at `replay_ratio = 1.0` replay is **7,581 tokens = exactly 50% of the bin**.

- **D-08 — replay is NOT dropped from the DP arms.** Doing so risks condition (c), and (c) was
  reinforced in Phase 20 with the D-38 magnitude bound *specifically because identity-only guards
  miss the class of harm that matters*. Losing dialogue capability is exactly that class, and
  `f_C = 0.5` sits only 2.24× above the measured non-vacuity floor.

- **D-09 — "replay outside N" is NOT reachable by accounting alone; the bin construction changes.
  Verified against the code, not assumed.** `train()` takes exactly ONE `train_bin` /
  `train_mask_bin` (`src/personacore/training/loop.py:179-182`) — no second-bin seam exists. That
  is why `_prepend_replay`'s own docstring states the mixture is "baked into the bin instead of
  into the loop." **Measured consequence:** 7,581 replay tokens ≈ **30 windows** against 33 fact
  windows, so an aligned loader that turned every window into a micro-step would make
  `grad_accum_steps = 63`, not 8 — **falsifying SC2's `grad_accum_steps = n_facts` by ~7.9×.**

- **D-10 — replay LEAVES the teaching bin entirely, and is drawn at train time from the
  already-built `data/dialog_train.bin`.** The teaching bin holds **facts only**, so
  `grad_accum_steps = n_facts` is **literally true with no roadmap amendment**. Replay is drawn via
  the existing, already-validated `get_batch_memmap_masked` over the existing 5.26M-token
  PersonaChat bins — **reuse of a proven path, not new infrastructure.**
  **The cost is recorded explicitly rather than hidden:** this requires a new additive seam in
  `train()`, which **overlaps DPSGD-01's "new additive gradient-side seam" (Phase 22)** and is
  pulled into Phase 21 by this decision. Two rejected alternatives, for the record: an in-bin
  sentinel-tagged single un-clipped micro-step (`grad_accum_steps = n_facts + 1`, which would have
  required a dated amendment to SC2 rather than satisfying it), and replay windows as N separate
  un-clipped micro-steps (which makes `grad_accum_steps` data-dependent — the exact quantity SC2
  exists to pin).

- **D-11 — replay VOLUME must depend only on PUBLIC quantities: `n_facts × a fixed constant`,
  never `round(replay_ratio × teaching_tokens)`. This closes a side channel neither the
  requirement nor the roadmap names.** `_prepend_replay` sizes replay as
  `want = int(round(replay_ratio * teaching_tokens))` (`scripts/teach_persona.py:338`), and
  `teaching_tokens` is the sum of the **facts' own** token lengths — measured 7,581, varying with
  the fact *values* (867–1,041 per fact, a 174-token spread). So today the volume of "public" data
  in the lot is a function of private content. **Without this correction the un-clipped
  public-gradient argument does not hold**, because the public term stops being independent of the
  private records.

</decisions>

<open_questions>
## OPEN — not yet discussed, and NOT Claude's discretion

These were presented and deferred by choice of discussion order, not resolved. A planner must not
invent answers to them; re-run `/gsd-discuss-phase 21` → "Update it".

1. **What the n=64 corpus is made of (UNIT-06).** 8 scored `LOCKED_FACTS` + 56 unscored filler
   (published instrument untouched, only N grows) vs 64 fresh facts (a new instrument). Where 56
   filler values come from — a newly generated slot×value grammar vs the existing
   `GATE_REJECTED_CANDIDATES` (12) / `CALIBRATION_FACTS` (10) / `REGISTER_ARM_FACTS` (6) pools,
   which total only **28** and are themselves published material. And whether the 2
   `SOFT_TIER_FACTS` ride along, since the v3.0 `real` recipe is **n=10, not n=8** — D-01's
   measurement shows both soft-tier facts are 5-window, which changes the ragged distribution.
2. **What UNIT-03 actually measures, and on which path.** Multiplicity under the OLD random-window
   loader (a random variable — documents why an ε there is uncomputable) vs under the NEW
   fact-aligned path (1 by construction — the number a published ε rests on). And measured how:
   an instrumented real loader at the real seed and step budget, vs computed analytically.
3. **UNIT-05's δ record.** δ is pinned as the literal `1e-5` by the requirement, so the *value* is
   not open — but the **form of the record** is: SC4 requires the rejected `1/N^1.1` recipe's
   self-contradiction at N=8 (δ = 0.1015, failing its own `δ·N < 0.01` assertion by ~80×) recorded
   as the reason. Whether that is a committed constant with the arithmetic in-module, a
   `results/phase21_*` artifact, or both, is undecided.

</open_questions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The code this phase changes
- `src/personacore/training/data.py:93-126` — `get_batch_memmap_masked`. The **overlapping windows
  drawn with replacement over a flat concatenated bin** that UNIT-01 exists to indict, and the
  `y[m == 0] = -100` line D-04 depends on. The new fact-aligned function is its sibling.
- `src/personacore/training/loop.py:172-194` — `train()`'s keyword-only signature. **Exactly one
  `train_bin` / `train_mask_bin`** — the fact establishing D-09, and the seam D-10 must extend.
- `scripts/teach_persona.py:256-324` — `build_bins`, its three build-time proofs (1:1 alignment,
  the `BLOCK_SIZE + 1` corpus floor, the `MASK_FRACTION_BAND` check), and the returned stats dict.
  `align_facts=None` is added HERE and must be byte-identical to v2.0 when `None`.
- `scripts/teach_persona.py:327-348` — `_prepend_replay`. Line **338** is D-11's side channel; the
  docstring is D-09's evidence in the code's own words.
- `scripts/teach_persona.py:359-402` — `sanity_check` proofs 4-6, including the `_is_subsequence`
  token-level held-out guarantee the new path must not weaken.
- `scripts/teach_persona.py:99-129` — `SEED = 1337`, `BLOCK_SIZE = 256`,
  `MASK_FRACTION_BAND = (0.15, 0.95)`, `REPLAY_RATIO = 0.0`, `REPLAY_ARM_RATIO = 1.0`.
- `src/personacore/model/gpt.py:212` — the `F.cross_entropy` call whose default `reduction="mean"`
  makes D-03 free.
- `src/personacore/lora/layer.py:41` — `lora_A`/`lora_B` as bare `nn.Parameter`s in an inline
  matmul. DPSGD-07 forbids restructuring these; module hooks do not reach them.

### The instruments that must NOT move (SC5)
- `scripts/phase14_factset.py:390-399` — the 8 `LOCKED_FACTS`, one per distinct slot.
- `scripts/phase14_factset.py:410-413` — `SOFT_TIER_FACTS` (2), which ride along at `n_facts=10`.
- `scripts/phase14_factset.py:816-821` — `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` /
  `PARAPHRASES_PER_FACT_TARGET = (20, 50)`.
- `scripts/phase14_factset.py:378` — `FACTSET_GATE_SHA`; `:489-491` — `RESERVED_HELDOUT_PROBES`.
- `scripts/phase18_extraction.py` — ancestry-guarded, `K = 48` at `:94`. **Unchanged and green.**

### The ordering mechanism Phase 21 must extend
- `tests/test_phase20_prereg.py:102` — `V4_ARTIFACT_GLOBS = ("results/phase20_*",)`. **Phase 21
  adds `results/phase21_*` here** (D-33), proven RED-then-GREEN per D-22.
- `tests/test_phase20_prereg.py:72` — `_GATE_MODULES` glob over `scripts/mitigation_*.py`; `:638`
  — the `_prose.py`-is-excluded assertion, i.e. the leading-underscore mechanism (D-23).
- `tests/test_phase16_prereg.py:322-403` — the **Phase 18 shape**, the one to copy (D-21); see
  `:396-398` for the reason in its own words.
- `scripts/_addendum.py` — the only sanctioned correction path (D-24).

### Requirements and roadmap
- `.planning/REQUIREMENTS.md:89-110` — UNIT-01 … UNIT-06 with the dependency-chain rationale.
- `.planning/REQUIREMENTS.md:111-134` — DPSGD-01 … DPSGD-07, which consume this phase's output.
  **DPSGD-01's gradient-side seam is what D-10 partially pulls forward.**
- `.planning/REQUIREMENTS.md:285-290` — the rejected alternatives (Poisson loader, ghost clipping,
  `LoRALinear` restructuring), each rejected on arithmetic already recorded.
- `.planning/ROADMAP.md` Phase 21 — goal, `Depends on: Phase 20`, and SC1-SC5.
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-CONTEXT.md` — D-01 … D-41.
  **D-13, D-17, D-24, D-33 bind this phase directly.**

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`get_batch_memmap_masked`** — reused UNCHANGED for the replay draw (D-10). Already validated,
  already re-opens both memmaps per call (the nanoGPT RSS-leak fix), already raises loudly on a
  token/mask length mismatch (T-11-04).
- **`data/dialog_train.bin` / `data/dialog_train_mask.bin`** — 5.26M train tokens, already built,
  already the source `_prepend_replay` reads from. D-10 draws from them directly instead of
  copying a slice.
- **`build_bins`' three-proof pattern** — the shape the aligned path's proofs must follow, and
  proof-1 is what D-06 extends from two files to three.
- **`teach_persona.sanity_check` proof-6 `_is_subsequence`** — the token-level held-out guarantee.
  The aligned path must not weaken it.

### Established Patterns
- **Additive kwarg, default byte-identical to the prior behaviour, proven against a golden
  fixture** — the `penalty_fn` / `extra_eval_fns` playbook. `build_bins(..., align_facts=None)` and
  the new `train()` replay seam both follow it. DPSGD-02 already demands this proof for the DP seam.
- **Structural enforcement replaces declared invariants** — named by v2.0's own learnings as the
  most recurring failure mode. D-05/D-06 are that pattern: the fact map is *consumed*, not asserted.
- **Deliberate-RED then byte-identical restore** — a guard nobody has watched fail is a guard
  nobody has verified. Applies to the new window-purity check and to the `phase21_*` glob addition.
- **Refuse-to-rerun on recorded evidence** (`teach_persona.refuse_if_exists`) — any new corpus
  builder writes evidence and needs the same refusal.
- **Over-claim avoidance** — do not mark a requirement complete in the first plan that touches it.
- **Measured numbers travel with their denominator and their provenance**, and the weakest bounds
  are stated rather than glossed (D-02's synthetic-ids / 5-rep caveat).

### Integration Points
- `src/personacore/training/data.py` — **new** fact-aligned batch function beside
  `get_batch_memmap_masked`. Reads the third `*_fact.bin`.
- `src/personacore/training/loop.py` — **new additive replay seam** in `train()` (D-10). Overlaps
  DPSGD-01's Phase 22 seam; the overlap is a recorded cost, not an accident.
- `scripts/teach_persona.py` — `build_bins(..., align_facts=None)`; `_prepend_replay` corrected per
  D-11. **NOT ancestry-pinned** (verified: it matches no `_GATE_MODULES` glob and carries no
  `PREREG_COMMIT`), so it may be edited — but its v2.0-default byte-identity must be proven.
- `tests/test_phase20_prereg.py` — `V4_ARTIFACT_GLOBS` gains `results/phase21_*` (D-33).
- `results/phase21_*` — **new**; the first v4.0 artifacts after Phase 20's. They are what make the
  D-33 glob addition load-bearing.
- `pyproject.toml` — **untouched**. RPT-03 keeps the zero-new-runtime-dependency streak;
  `tests/test_package.py` turns red on any new dependency.

</code_context>

<specifics>
## Specific Ideas

- **The premise-check pattern earned its keep twice in this discussion, and both times the stated
  premise survived while the reasoning behind it was replaced.** Ragged-vs-uniform was proposed on
  a *padding* argument (10.26% vs 24%) and confirmed on a *compute* measurement that the padding
  argument did not predict (1.14× vs 1.39×/1.35×, with `vmap` off the critical path entirely).
  Replay-outside-N was proposed on an *accounting* argument and confirmed only after the code
  showed accounting alone could not deliver it. Carry that into the phase: **state the position,
  name the premise, measure the premise.**
- **Two findings in this CONTEXT appear in no source document** and should survive into the report:
  the `vmap`-1.07×-does-not-govern result (D-02), and the `teaching_tokens` side channel (D-11).
  Both were found by reading and running the code rather than by reading the requirement.
- **The D-11 side channel is the phase's own defect class, caught early.** Phase 20's carried
  lesson is *a guard that refuses a NAME where the harm is a PROPERTY*. D-11 is its sibling: a
  quantity **declared** public whose **value** is a function of private data. Whatever guards the
  aligned path should refuse the property, not the name.

</specifics>

<deferred>
## Deferred Ideas

- **The GATE-10 fallback tolerance** (Phase 20 D-26) — a third chosen constant, deliberately unset.
  Must be decided before **CAL-03**, which is **Phase 23**, not Phase 21. Corrected here because
  `20-CONTEXT.md:621-623` misattributes it to Phase 21.
- **Extraction noise floor measurement** (Phase 20 D-13) — two seeds on the never-taught arm,
  **Phase 23** (CTRL-03), gated behind this phase's corpus. Carried by the D-14 tripwire.
- **Whether `train()`'s replay seam should generalize to an arbitrary auxiliary-bin list** — D-10
  needs exactly one public bin. Generalizing is an abstraction with one implementation; if a
  second auxiliary source ever appears, that is when it earns the shape.
- **Re-benchmarking D-02's ratios on the real bins rather than synthetic ids** — the ratios are
  what the decision rests on and they were measured back-to-back in one process, but the run used
  `torch.randint` ids, 5 reps, and no confidence interval. A confirmation on the real corpus is
  cheap and belongs beside the multiplicity measurement (UNIT-03), not in its own phase.

</deferred>

---

*Phase: 21-The Privacy Unit, the DP Data Path, and the n=64 Corpus*
*Context gathered: 2026-08-22 — PARTIAL, see `<open_questions>`*
