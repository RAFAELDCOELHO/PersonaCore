# Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus - Context

**Gathered:** 2026-08-22 · **Updated:** 2026-08-22 (session 3)
**Status:** COMPLETE — D-01 … D-26. Every area session 2 left OPEN is now closed: D-11's replay
constant (D-24, D-25), UNIT-03's measurement path (D-26), and UNIT-05's record form — the last
resolved *structurally*, as a consequence of D-22/D-23, rather than chosen. Ready for
`/gsd:plan-phase 21`.

> **Numbering.** A bare `D-NN` is always **this phase's** decision. Phase 20's decisions are
> always written `Phase 20 D-NN`. This matters: Phase 21 D-13/D-14/D-17 are different decisions
> from Phase 20 D-13/D-14/D-17.

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
6. An n=64 corpus of **unscored filler facts** disturbing no published instrument (UNIT-06) —
   composition now fixed at **8 scored `LOCKED_FACTS` + 56 filler**, see D-12 … D-16

**No ε is computed in this phase.** The artifact is a *unit* and the path that makes it real.
An ε computed against the wrong unit is not a number a re-run can correct — which is why this is
the milestone's longest dependency chain and why it is design work before it is code.

**Carried forward from Phase 20 — locked, not reopened here:**

- **Phase 20 D-33** — `V4_ARTIFACT_GLOBS = ("results/phase20_*",)` ONLY. Each phase adds its own prefix at
  the moment it first writes results. **Phase 21 writes results, so it MUST add `results/phase21_*`
  to `tests/test_phase20_prereg.py::V4_ARTIFACT_GLOBS`, proven RED-then-GREEN in a throwaway repo
  (D-22).** D-33 names the cost explicitly: an `assert` catches an empty match set, never an
  incomplete one — a phase that forgets its prefix fails **silently**, and its artifacts sit
  outside the ancestry guard.
- **Phase 20 D-24** — `scripts/mitigation_gate.py` is FROZEN. Corrections are dated continuations via
  `scripts/_addendum.py`, never edits. Editing it turns the ancestry guard permanently red and
  `git rm` + re-add cannot undo it.
- **Phase 20 D-13** — the extraction noise floor is **Phase 23** (CTRL-03), gated *behind this phase's
  corpus*. Phase 21 is what unblocks it.
- **Phase 20 D-17** — `f_C = 0.5` sits only **2.24×** above the measured non-vacuity floor `0.2237`. There
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

### The n=64 corpus — what a filler fact is, where it lives, and what proves it

- **D-12 — the corpus is `8 scored LOCKED_FACTS + 56 unscored filler`, NOT 64 fresh facts. The
  reason is stronger than "it would invalidate the chain": `n=8` is PRE-REGISTERED LITERALLY, in
  four places, one of them already complete and frozen.**

  | where | what it says | status |
  |---|---|---|
  | `REQUIREMENTS.md:84` — **GATE-10** | "the **n=8-vs-n=64** capacity comparison rule" | **`[x]` COMPLETE**, living inside the **FROZEN** `scripts/mitigation_gate.py` (Phase 20 D-24) |
  | `REQUIREMENTS.md:174` / `ROADMAP.md:401` — **CAL-03** | "a small calibration run at **`n_facts=8` vs 64**" | open, Phase 23 |
  | `REQUIREMENTS.md:206` — **FRONT-01** | "both capacities (**n=8** and n=64)" | open |
  | `ROADMAP.md:52` | the pre-registered null is "72σ at **L=8 facts**" | published |

  So 64 fresh facts does not merely break a chain — it **contradicts a completed requirement in a
  file only a dated continuation may touch.** The 8 stay; N grows around them.

  **The existing pools cannot supply the 56, for two independent reasons.** *Volume:*
  `GATE_REJECTED_CANDIDATES` 12 + `CALIBRATION_POOL` 10 + `REGISTER_ARM_POOL` 6 = **28** non-locked
  facts against 56 needed. *Role — found in the code, not in the requirement:* those 28 are
  **load-bearing, not spare inventory**. `GATE_REJECTED_CANDIDATES` **IS** Phase 20 D-10's
  contradiction-detector lexicon source (`phase14_factset.py:425` — the detector's vocabulary is
  `set(LOCKED_VALUES) | {f.value for f in GATE_REJECTED_CANDIDATES}`), and `CALIBRATION_FACTS` /
  `REGISTER_ARM_FACTS` are the live `arm_spec` pools. Teaching one as filler would make a single
  value simultaneously *"a competing value the detector must spot"* and *"a fact we taught"*.

- **D-13 — the 56 filler facts live in a NEW module `scripts/phase21_filler.py`, entirely OUTSIDE
  `all_pools()`.** Zero new rows in any Phase-14 report, zero disturbance to any published
  instrument — the safest reading of SC5. **The consequence is named rather than hoped for:** the
  Phase-14 discipline does **not** come along for free, because `all_pools()` is what confers it —
  it is iterated **7×** by `scripts/phase14_factset_gate.py` (`:223,241,260,299,341,369,419`) and
  `_BY_ID` (`phase14_factset.py:380`) is built from it. **Pool membership, not module location, is
  the gate.** So the discipline must be re-implemented explicitly inside the new module (D-16).

- **D-14 — the soft tier is EXCLUDED ENTIRELY. The n=8 arm's teaching bin is `LOCKED_FACTS` only;
  n=64 = 8 LOCKED + 56 filler.** `arm_spec('real')` today returns `LOCKED_FACTS + SOFT_TIER_FACTS`
  (`scripts/teach_persona.py:414-420`), so this needs a **new arm or an `n_facts` parameter** —
  and **that signature change is IN SCOPE for this phase**, recorded here rather than left implicit
  for a planner to discover.

  **Why, precisely:** not "v3.0's composition choice isn't intrinsic to v4.0" — true, but not
  load-bearing. The load-bearing fact is D-12's table: **v4.0 already pre-registered its small
  capacity as literally 8**, so n=10 contradicts GATE-10, CAL-03 and FRONT-01 at once. **The repo
  had already drawn this distinction in its own words** — `scripts/mitigation_gate.py:625` calls
  `n_facts=10, replay_ratio=1.0` *"the right REGIME, not a v4.0 ARM."* And
  `phase14_factset.py:399-407` records that the soft tier *"has NO BEARING on DEMO-06's taught or
  held-out thresholds and contributes nothing to the headline claim."*
  **Second benefit, free:** exclusion keeps D-01 and D-02 valid **exactly as measured** — both
  benchmarked 8 facts at ragged `(4,4,4,4,4,5,4,4)`. At n=10, D-01 shows both soft facts are
  **5-window**, so both measurements would have needed redoing.

- **D-15 — a filler fact renders through the SAME `render_family` over `TAUGHT_FAMILY_IDS`
  (`F1 F2 F4 F5 F6`): 22 rows, ~4 windows, identical in FORM to a scored fact.** Measured
  consequence: **n=64 ≈ 264 windows, `grad_accum_steps = 64`, ≈ 8× the n=8 bin.**
  **The cheaper option was rejected on a confound, not on cost.** A lighter renderer (~1 window per
  filler fact, n=64 ≈ 89 windows) would make filler and scored records **different sizes under one
  clip norm** — so the capacity lever would change **N and per-record mass at once**, confounding
  precisely the GATE-10 comparison it exists to feed. Uniform record size keeps *"one fact = one
  record"* honest across both tiers.

- **D-16 — filler uses a filler-only slot grammar DISJOINT from the 8 scored slots, and
  `render_family` gains an additive `forms=None` / `question_bank=None`, byte-identical to today
  when `None`.** This is the `align_facts=None` / `penalty_fn` playbook already named in
  `<code_context>` as an Established Pattern. Cost: one **additive** edit to `phase14_factset.py`,
  adding zero rows to any published report.

  **The finding that forced this.** There are exactly **11** slots in `SLOT_FORMS` /
  `SLOT_QUESTION_BANK` (`phase14_factset.py:151`, `:543`) — `person_name, pet_name, cat_name,
  sibling_name, hometown, street, birth_year, house_number, favorite_color, favorite_food,
  favorite_drink` — and `render_family` dispatches through `SLOT_FORMS[fact.slot]`. **Eight of the
  11 already hold a SCORED fact** (the `LOCKED_FACTS` are one-per-distinct-slot), two hold soft, and
  `favorite_drink` is empty (both candidates rejected). Spreading 56 filler over those 11 slots
  would seat **~5 rival values inside each scored slot** — "my name is Quillon" taught beside five
  other names. That makes the corpus **self-contradictory on exactly the 8 slots GATE-10 scores**,
  so n=64 recall would fall from **slot contention rather than capacity**, and the capacity verdict
  would be measuring the wrong thing. Contention inside *filler* space is harmless: nothing there
  is scored.

- **D-17 — the DETERMINISTIC half of the minting discipline runs IN FULL; the base-model
  guessability probe is explicitly NOT run, with its reason recorded IN THE MODULE.**
  `phase21_filler.py` re-implements `token_census` round-trip **and** collision refusal — against
  the forbidden **10** (`LOCKED + SOFT`), the **28** published pool values, and the filler values
  against each other. Cost: **0 generations** (`token_census`, `phase14_factset.py:313`, needs only
  the tokenizer). The probe is waived because **filler is never scored and never enters the leak
  vocabulary, so "the base already knew it" has nothing to corrupt** — and the waiver is written
  down **as a decision, not as a silence**, so no future reader must guess whether the discipline
  was forgotten or deliberately judged inapplicable.

  **This resolved a conflict inside the discussion's own answer, recorded so it is not re-created.**
  "No extra base-model completion runs" and "the guessability discipline re-implemented" **cannot
  both hold**: `scripts/phase14_factset_gate.py:8` defines guessability as prompting the un-adapted
  `convbase_best.pt`, and `exact_match_clean` (`phase14_factset.py:334`) takes `completions` as its
  argument — it is **defined over base-model output**. The completion cost attaches to *doing
  guessability at all*, never to *where the code lives*. **Measured price of the full probe, had it
  been run:** 8 questions/slot × `PROBE_SEEDS = 4` = **32 generations per value**, × 56 = **1,792
  generations** on `convbase_best.pt` (≈4% of one Phase-18 arm's 42,480 draws).

- **D-18 — "unscored" has a STRUCTURAL definition, not an intention: no filler value may enter the
  10-value leak vocabulary.** The extraction instrument carries **two different fact surfaces** —
  the taught/scored surface is `LOCKED_FACTS` only, 8 (`phase18_extraction.py:865-867, 1184, 3249,
  3594`), while the `values` leak-detection vocabulary is `LOCKED + SOFT`, 10 (`:872, 3137, 3598,
  4474`). **Four tests assert `len(forbidden) == 10`** with the comment *"no tier is exempt from the
  scan"* (`tests/test_phase14_scoring.py:405`, `test_phase16_driver.py:313`,
  `test_phase16_ladder.py:443`, `test_phase18_corpus.py:430`). A filler value reaching that list
  turns four tests red **and** edits the ancestry-guarded `phase18_extraction.py` — breaking SC5.
  **The upside is what makes GATE-10 legitimate:** the n=64 arm measures extraction over the *same
  8 facts* as n=8, with only the corpus around them changed — an unconfounded capacity comparison.
  (Also `tests/test_phase14_factset.py:102-103` caps `len(LOCKED_FACTS) <= 8` and
  `len(SOFT_TIER_FACTS) <= 3`, so filler could not have lived in either existing tier regardless.)

### Where the pre-registered constants live — the pin, the ceiling, and the sibling

- **D-19 — the constants live in a NEW `scripts/mitigation_*.py` module, and the NAME is NOT what
  freezes it. The premise was measured before it was locked, and half of it was false.**
  The stated position was that a `mitigation_*.py` module becomes permanently frozen the moment its
  first artifact lands. Measured against `tests/test_phase20_prereg.py`:

  | mechanism | what it actually covers | confers the freeze? |
  |---|---|---|
  | `_GATE_MODULES` glob (`:72`) | ONE content test — the import-graph subset scan (`:474`) — plus `_collapsed_glob_guard` (`:445`) and the `_prose.py` exclusion (`:606`) | **no** |
  | `_MITIGATION_GATE_PATH` singular | `:740`, `:805`, `:928`, `:991` — constants count, retyped-baseline, verdict domain, keyword-only. **Do NOT extend to siblings.** | no |
  | `PHASE20_PREREG_ARTIFACT` (`:91`) | the ancestry ordering test, via `prereg_artifact=` | **yes — this alone** |

  **The freeze half of the premise is TRUE and worth restating precisely:** `prereg_commits` is
  `git log -- <pin>` — **every** commit touching the pin (`:143`) — compared against `adds[-1]`, the
  **earliest** add of each artifact (`:157`), which is what makes delete-and-re-add unable to launder
  the ordering. Phase 20 D-24 is accurate.
  **The false half is the load-bearing one:** the freeze comes from a hand-written explicit path
  constant, not from the filename. So the "middle ground" — protected but not frozen — is not
  something to invent; it is the repo's **default state** for any `mitigation_*.py` sibling, and the
  glob's own comment (`:64-66`) says it exists precisely so a module "enters these scans the moment
  it exists".

- **D-20 — the frozen module IS armed now, against `results/phase21_*`, in the phase's FIRST plan.**
  A second `_assert_ordering_holds(prereg_artifact=<the new module>, artifact_glob="results/phase21_*",
  globs=V4_ARTIFACT_GLOBS)` lands before any `results/phase21_*` artifact exists — the 20-01
  discipline, arm-then-write. From the first artifact onward the module is frozen irrevocably.
  **A GAP FOUND WHILE MEASURING, recorded because Phase 20 D-33 does not say it:** adding
  `results/phase21_*` to `V4_ARTIFACT_GLOBS` creates **no ancestry check by itself**. `globs` is used
  only for the `assert artifact_glob in globs` consistency check (`:129`); the loop runs on
  `artifact_glob` **singular**. The D-33 addition is a *declaration* — without a test calling
  `_assert_ordering_holds` with that glob, nothing is enforced. Both halves are required.
  **And the reflexivity note travels with it** (`:300-304`): `git merge-base --is-ancestor X X`
  exits **0**, so a pin and an artifact in the SAME commit PASS. D-08's "strictly after" is a
  discipline tighter than the mechanism enforces — inherited deliberately, not assumed.

- **D-21 — constants Phase 22+ has not yet discovered land in an UNFROZEN `mitigation_*.py` sibling,
  unpinned until its own phase arms it. Phase 21 records the convention and does NOT create the
  file.** An empty module is a placeholder that joins the import-graph scan while being green over
  nothing; the glob captures the sibling automatically the moment it genuinely comes to exist, so
  deferring costs nothing. **This is what buys maximum protection where the decision is closed and
  real room to grow where it is not** — the reason the split was chosen over freezing everything or
  freezing nothing.

- **D-22 — joining the glob imposes a HARD IMPORT CEILING, and that is why the artifact writer lives
  OUTSIDE it.** Measured: `allowed = {"pathlib", "sys", "erasure_gate"}` (`:522`), asserted as a
  **subset** over `imported` accumulated across **all** `_GATE_MODULES` (`:498`); and
  `from_erasure_gate` is asserted with **exact equality** to five names (`:538`) — `MARGIN_K`,
  `V20_EWC_RETENTION_PPL`, `V20_MASKED_DIALOGUE_VAL_PPL`, `rule_of_three`, `wilson_upper_bound`.
  Because that is a **set**, a new sibling may import **from among** those five (a no-op against the
  equality); it may **not** introduce a sixth.
  **The consequence:** `json` is outside the allow-set, so **no `mitigation_*` module can serialize an
  artifact**. The frozen module therefore holds constants + arithmetic + `_prove` guards and does
  **zero I/O**; a separate driver **outside** the glob — `scripts/phase21_unit_record.py` or
  equivalent — imports the constants and writes the real `results/phase21_*` artifacts. This mirrors
  the repo's own gate/budget split: the rule lives in one place, its emission in another. It also
  keeps the frozen module's surface minimal, which is precisely what makes freezing it cheap.
  *(Rejected: widening the allow-set to admit `json`. Mechanically legal — the test file is not
  itself pinned — but it loosens a subset assertion whose stated purpose (`:525-527`) is "catches the
  one nobody anticipated", and the first thing it would ever have caught would be us.)*

- **D-23 — the frozen module contains SC1 + SC4's already-settled decisions, and nothing else.**
  Freezing means content-complete at arm time, so the boundary is the decision that cannot be
  revisited:
  1. `PRIVACY_UNIT = "one taught fact"` with its arithmetic (SC1 / UNIT-01);
  2. the replay-outside-N decision — `q = 1`, `N = n_facts` — with its ε consequence
     (SC4 / UNIT-04, already locked as **D-07**);
  3. `δ = 1e-5` with the rejected `1/N^1.1` recipe's self-contradiction (SC4 / UNIT-05).
  **All three are genuinely closed today.** D-11's replay VOLUME constant is **explicitly excluded**
  and settled in its own round (D-24) rather than under freeze pressure.
  **δ's arithmetic, verified rather than quoted:** `1/N^1.1` at N=8 is **0.101532**, so `δ·N =
  0.812252` against its own `δ·N < 0.01` assertion — failing by **81.2×**. At N=64 it is 0.010309,
  `δ·N = 0.659754`, still failing by **66.0×** — so the recipe is not merely wrong at the small
  capacity, it is wrong at **both** capacities this milestone runs. The pinned literal passes at both:
  `δ·N` = 8.00e-05 at N=8 (by 125×) and 6.40e-04 at N=64 (by 16×). Needs **no import** — `N ** -1.1`
  is an operator — which is what makes it fit inside D-22's ceiling.

### D-11's replay constant — the value, the unit, and where the pass sits

- **D-24 — the replay constant is `4 windows per fact = 1,024 tokens`, window-quantized, never a raw
  token count.** Both factors are public (`4`, and `block_size = 256`), so the volume depends on
  nothing private — which is the whole point of D-11. Measured against D-01's geometry:

  | constant | tok/fact | integral windows? | share of the padded bin | vs today's 50.00% |
  |---|---|---|---|---|
  | 3 windows | 768 | yes | 42.11% | −7.9 pts |
  | **4 windows** | **1,024** | **yes** | **49.23%** | **−0.77 pts** |
  | 5 windows | 1,280 | yes | 54.79% | +4.8 pts |
  | raw ≈948 | 947.625 | **NO — 3.7017** | 50.00% (vs *raw* teaching) | 0 |

  **Two findings the table does not show, and both killed the raw option.** *First:*
  `get_batch_memmap_masked` draws whole `block_size` windows only (`data.py:117-124`), so a raw-token
  constant needs a truncation step **inside the very path D-10 chose because it was already proven** —
  paying new code in the one place D-10 spent a decision to avoid it. *Second, and worse:*
  **947.625 is `7581 / 8`** — derived from the private token lengths. Choosing the constant to match
  today's corpus re-introduces D-11's own side channel one level up, **at design time**. A constant
  that is "public" because it is published, but whose value was read off private data, is exactly the
  property-not-name defect this phase already named as its own class.
  **The ratio also holds for free across capacities:** at n=64 the share is **49.90%**, because both
  sides scale with `n_facts`. Nothing re-tunes.

- **D-25 — replay is drawn and accumulated in its OWN pass per lot, structurally OUTSIDE the
  per-record accumulation loop, so `grad_accum_steps = n_facts` stays LITERALLY true.**
  Phase 22's clipping seam then has an obvious place to *not* apply: replay never enters the clipped
  loop, so the public term stays provably independent of any private record.
  **This reopened a question D-10 had closed, and the reopening is the record's point.** D-10 rejected
  "replay windows as N separate un-clipped micro-steps" **because it made `grad_accum_steps`
  data-dependent** — but under D-24 the replay window count is `4 × n_facts`, **fully public**, so
  that rejection's premise is now false. The option space genuinely reopened; the separate-pass shape
  was chosen on its own merits rather than inherited from a reason that had expired.
  **The cost is named, not hidden:** at n=64 the pass is `4 × 64 = 256` windows per lot, so it needs
  its own internal micro-batching on MPS. That is a Phase-22 implementation detail and explicitly
  **not** a reason to prefer the more ambiguous per-micro-step pairing, which would need two gradient
  accumulators in `train()` and would invite a future reader to think replay is part of the record.

### UNIT-03 — what is measured, and on which path

- **D-26 — BOTH paths are measured on an INSTRUMENTED loader at the real seed and budget
  (`SEED = 1337`, `MAX_STEPS = 200`, `BATCH_SIZE = 8`), and each row is labelled with its exact bin
  composition.** The old random-window path records the **observed per-fact distribution** —
  min/max/mean/spread, not merely an expectation — and the aligned path records an **observed** count,
  so "1 by construction" is *verified* rather than assumed. Both rows land in `results/phase21_*`.

  Analytic expectations, computed here and stated **as analytic** precisely because they are the kind
  of number UNIT-03 refuses:

  | path | bin | E[touches per fact] over 1,600 draws |
  |---|---|---|
  | replay-in-bin, today's ratio 1.0 | 15,162 tok | 129.2 |
  | facts-only bin (D-10) | 7,581 tok | **262.9** |
  | fact-aligned (D-01 / D-05) | 33 windows | 1 per step, deterministic, `q = 1` |

  **The finding that sharpens the phase's own case: D-10 roughly DOUBLES the old path's multiplicity**
  (129.2 → 262.9), because the same 1,600 draws now land on half as much data. Removing replay from
  the bin improved the privacy *accounting* and made the *unaligned* multiplicity worse — so the two
  decisions are not independent, and UNIT-01's indictment of the old loader gets stronger, not weaker,
  once D-10 is in force.
  **This also settles a reading SC3 could not have anticipated.** SC3 says the multiplicity is measured
  "after `build_bins` packing at the chosen `replay_ratio`" — phrasing that **predates D-10**, which
  moved replay out of the teaching bin entirely. Labelling each row with its bin composition
  (`replay-in-bin @1.0` / `facts-only (D-10)` / `fact-aligned (D-01, D-05)`) closes that ambiguity in
  the artifact rather than leaving a planner to guess which bin SC3 meant.

</decisions>

<open_questions>
## CLOSED — session 3. Nothing here is left for a planner to invent.

**All three items below were OPEN at the end of session 2 and are now resolved.** The list is kept
rather than deleted so the resolution is traceable to the question it answered.

| was open | closed by | how |
|---|---|---|
| 1. D-11's replay constant — the value, not the property | **D-24**, **D-25** | 4 windows/fact = 1,024 tokens; separate un-clipped pass per lot |
| 2. What UNIT-03 measures, and on which path | **D-26** | both paths, instrumented at `SEED=1337` / 200 steps / batch 8, each row labelled with its bin composition |
| 3. UNIT-05's δ record form | **D-22 + D-23** | resolved *structurally*: δ is a frozen in-module constant AND reaches a driver-written artifact — the "both" branch, arrived at rather than chosen |

**One correction to item 1's own text, recorded so it is not inherited wrong.** Session 2 wrote
*"at `grad_accum_steps = 64` the replay draw is per-step, so the constant sets how much public data
rides in every lot."* **D-25 makes the first clause false**: replay is drawn in its own pass per
**lot**, structurally outside the per-record loop, precisely so `grad_accum_steps = n_facts` stays
literally true. The second clause survives — the constant does set the public volume per lot.

The original text of the three questions follows, unedited, as the record of what was asked:

1. **D-11's replay CONSTANT — the value, not the property.** *(Not in the original open list; found
   while scouting in session 2 and recorded here so it is not lost.)* D-11 locks replay volume to
   `n_facts × a fixed constant` and forbids `round(replay_ratio × teaching_tokens)`, but **never
   sets the constant**. Measured today: replay is 7,581 tokens = **947.6 per fact** = exactly 50%
   of the bin. Open: a raw token constant (≈948, preserving today's 50%) vs a `block_size`-quantized
   one (4 windows = 1,024 tokens/fact, which keeps replay on window boundaries like the teaching
   shards). At n=64 the two differ by **60,672 vs 65,536** replay tokens. **This interacts with
   D-15:** at `grad_accum_steps = 64` the replay draw is per-step, so the constant sets how much
   public data rides in every lot.
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
- `scripts/phase14_factset.py:410-413` — `SOFT_TIER_FACTS` (2). **CORRECTED in session 2: these do
  NOT ride along.** An earlier draft of this file said "which ride along at `n_facts=10`" — that
  described the v3.0 `real` recipe, not a v4.0 arm. **D-14 excludes them entirely.**
- `scripts/phase14_factset.py:816-821` — `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` /
  `PARAPHRASES_PER_FACT_TARGET = (20, 50)`. Filler renders through the SAME taught families (D-15).
- `scripts/phase14_factset.py:378` — `FACTSET_GATE_SHA`; `:489-491` — `RESERVED_HELDOUT_PROBES`.
- `scripts/phase18_extraction.py` — ancestry-guarded, `K = 48` at `:94`. **Unchanged and green.**

### The corpus decisions' evidence (D-12 … D-18) — read before touching UNIT-06
- `.planning/REQUIREMENTS.md:84` — **GATE-10**, "the **n=8-vs-n=64** capacity comparison rule",
  marked **`[x]` complete** and living inside the FROZEN `scripts/mitigation_gate.py`. **This is why
  the small capacity cannot become 10 or 64.**
- `.planning/REQUIREMENTS.md:174` / `.planning/ROADMAP.md:401` — **CAL-03**, "`n_facts=8` vs 64".
- `.planning/REQUIREMENTS.md:206` — **FRONT-01**, "both capacities (n=8 and n=64)".
- `.planning/ROADMAP.md:52` — the pre-registered null rests on "72σ at **L=8 facts**".
- `scripts/mitigation_gate.py:625` — `n_facts=10, replay_ratio=1.0` is *"the right REGIME, not a
  v4.0 ARM"*. The repo's own words for D-14.
- `scripts/phase14_factset.py:127` — `all_pools()`, *"the iteration order for every report"*;
  `:380` — `_BY_ID` built from it. **Pool membership, not module location, confers the gate (D-13).**
- `scripts/phase14_factset_gate.py:223,241,260,299,341,369,419` — the 7 `all_pools()` loops;
  `:8` — guessability **is defined as** prompting the un-adapted `convbase_best.pt`;
  `:62` — `PROBE_SEEDS = 4`; `:111` — `probe_guessability`. **D-17's cost evidence.**
- `scripts/phase14_factset.py:313` — `token_census` (tokenizer only, **0 generations**);
  `:334` — `exact_match_clean`, which takes `completions` and is therefore **defined over
  base-model output**. The two halves D-17 separates.
- `scripts/phase14_factset.py:151` / `:543` — `SLOT_QUESTION_BANK` / `SLOT_FORMS`: **exactly 11
  slots, 8 questions each**; `:824` — `render_family`, dispatching through `SLOT_FORMS[fact.slot]`.
  **D-16's forcing evidence.**
- `scripts/phase14_factset.py:425` — `GATE_REJECTED_CANDIDATES` **is** the contradiction-detector's
  lexicon source. **Why the 28 published values are not spare inventory (D-12).**
- `scripts/phase18_extraction.py:865-867,1184,3249,3594` — taught/scored surface = `LOCKED_FACTS`
  only (8); `:872,3137,3598,4474` — leak vocabulary = `LOCKED + SOFT` (10). **D-18's two surfaces.**
- `tests/test_phase14_scoring.py:405`, `tests/test_phase16_driver.py:313`,
  `tests/test_phase16_ladder.py:443`, `tests/test_phase18_corpus.py:430` — four assertions of
  `len(forbidden) == 10`, *"no tier is exempt from the scan"*. **The hard wall for filler values.**
- `tests/test_phase14_factset.py:102-103` — `len(LOCKED_FACTS) <= 8`, `len(SOFT_TIER_FACTS) <= 3`.
  Filler could not have lived in either tier regardless.
- `scripts/teach_persona.py:405-421` — `arm_spec`; `'real'` returns `LOCKED + SOFT`. **The signature
  D-14 changes.** `:99-129` / `:511-524` — `SEED = 1337`, `BLOCK_SIZE = 256`, `BATCH_SIZE = 8`,
  `MAX_STEPS = 200`, `WARMUP_STEPS = 20`.

### The ordering mechanism Phase 21 must extend

> **Numbering corrected in session 3.** The four references below cited bare `D-33` / `D-23` /
> `D-21` / `D-24` for **Phase 20** decisions, against this file's own rule that a bare `D-NN` means
> *this* phase. Harmless until session 3, which created a Phase 21 D-21…D-24. Now written in full.

- `tests/test_phase20_prereg.py:102` — `V4_ARTIFACT_GLOBS = ("results/phase20_*",)`. **Phase 21
  adds `results/phase21_*` here** (Phase 20 D-33), proven RED-then-GREEN per Phase 20 D-22.
  **Necessary but NOT sufficient — see D-20.**
- `tests/test_phase20_prereg.py:72` — `_GATE_MODULES` glob over `scripts/mitigation_*.py`; `:638`
  — the `_prose.py`-is-excluded assertion, i.e. the leading-underscore mechanism (Phase 20 D-23).
- `tests/test_phase16_prereg.py:322-403` — the **Phase 18 shape**, the one to copy (Phase 20 D-21);
  see `:396-398` for the reason in its own words.
- `scripts/_addendum.py` — the only sanctioned correction path (Phase 20 D-24).

### The ancestry mechanism, read line-by-line in session 3 — D-19 … D-23's evidence

**Read these before writing the pin or its test. The distinction they encode — that the glob and the
freeze are two different mechanisms — is what D-19 corrects.**

- `tests/test_phase20_prereg.py:91` — `PHASE20_PREREG_ARTIFACT = "scripts/mitigation_gate.py"`, a
  hand-written explicit path. **This constant, and nothing else, is what freezes a module.**
- `tests/test_phase20_prereg.py:121-183` — `_assert_ordering_holds`, keyword-only and parameterized
  on `root`. **Phase 21 calls this same function with its own `prereg_artifact`** (D-20); a lookalike
  copy would prove something about a different function.
- `:143` — `prereg_commits = git log --format=%H -- <pin>`: **EVERY** commit touching the pin, so a
  later edit is caught, not merely a wrong first commit.
- `:157` — `first_add = adds[-1]`, the **earliest** add. This is what makes delete-and-re-add unable
  to launder the ordering, and therefore what makes the freeze irrevocable.
- `:129` — `assert artifact_glob in globs`. **The ONLY use of `V4_ARTIFACT_GLOBS` inside the ordering
  body.** The loop runs on `artifact_glob` *singular* — which is why the Phase 20 D-33 glob addition
  enforces nothing on its own (D-20).
- `:166-183` — the product assertion and the `bool(checked) == bool(tracked_artifacts)` equivalence
  that stops a vacuous guard surviving the artifacts' arrival.
- `:281-330` — `test_phase20_glob_sees_the_phase20_prefix_red_then_green`, the throwaway-repo fixture
  shape Phase 21 copies for its own prefix; `:300-304` — **the reflexivity note**: `git merge-base
  --is-ancestor X X` exits 0, so pin-and-artifact in the same commit PASSES, and "strictly after" is
  a discipline tighter than the mechanism.
- `:64-66` — the glob exists so a sibling "enters these scans the moment it exists". **D-21's
  licence to not create the sibling file.**
- `:474-579` — the import-graph scan, the **one** content test that iterates `_GATE_MODULES`;
  `:498` — `imported` accumulates across **all** modules in the glob; `:522` —
  `allowed = {"pathlib", "sys", "erasure_gate"}`; `:538` — `from_erasure_gate` asserted by **exact
  equality** to five names. **D-22's ceiling, and why the artifact writer lives outside the glob.**
- `:740`, `:805`, `:928`, `:991` — the content scans that read `_MITIGATION_GATE_PATH` **singular**
  and therefore do **not** extend to a sibling. Half of D-19's correction.

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
- `scripts/phase21_filler.py` — **NEW module** (D-13). The 56 filler facts, a filler-only slot
  grammar disjoint from the 8 scored slots (D-16), and its own re-implemented deterministic
  discipline: `token_census` round-trip + collision refusal against the forbidden 10, the 28
  published values, and each other (D-17). **Deliberately outside `all_pools()`** — which is
  exactly why the discipline cannot be inherited and must be written here.
- `scripts/phase14_factset.py` — **additive only**: `render_family(..., forms=None,
  question_bank=None)`, byte-identical to today when `None` (D-16). No new rows in any published
  report. Nothing in `LOCKED_FACTS` / `SOFT_TIER_FACTS` / `all_pools()` moves.
- `scripts/teach_persona.py:405-421` — `arm_spec` gains a **new arm or an `n_facts` parameter** so
  the n=8 arm draws `LOCKED_FACTS` only and the n=64 arm draws 8 + 56 filler (D-14). **In scope for
  this phase**, not deferred to Phase 22.
- `scripts/mitigation_<unit>.py` — **NEW, FROZEN from the first `results/phase21_*` artifact**
  (D-19, D-20, D-23). Holds `PRIVACY_UNIT`, the `q=1` / `N=n_facts` replay-outside-N decision, and
  `δ = 1e-5` with the rejected `1/N^1.1` arithmetic — plus `_prove` guards. **Imports only
  `pathlib`/`sys` and at most the five already-accumulated `erasure_gate` names; zero `json`, zero
  I/O** (D-22). Exact filename is Claude's discretion, constrained to match `mitigation_*.py` and to
  be named for its SUBJECT rather than its phase, as `mitigation_gate.py` is (`test_phase20_prereg.py:59-60`).
- `scripts/phase21_unit_record.py` — **NEW driver, deliberately OUTSIDE the `mitigation_*.py` glob**
  (D-22). Imports the frozen constants and writes the `results/phase21_*` artifacts, including
  D-26's two labelled multiplicity rows. This is where `json` lives.
- **The unfrozen `mitigation_*.py` sibling — NOT created in Phase 21** (D-21). Recorded as a
  convention: Phase 22+ constants land there, unpinned until that phase arms it.
- `tests/test_phase20_prereg.py` — **two additive changes, and BOTH are required** (D-20):
  `V4_ARTIFACT_GLOBS` gains `results/phase21_*` (Phase 20 D-33), **and** a new
  `_assert_ordering_holds(prereg_artifact=<the new module>, artifact_glob="results/phase21_*")` test
  — the glob addition alone enforces nothing (`:129`).
- `results/phase21_*` — **new**; the first v4.0 artifacts after Phase 20's. They are what make the
  Phase 20 D-33 glob addition load-bearing.
- **UNTOUCHED, and each is a test that turns red if it isn't:** `scripts/phase18_extraction.py`
  (ancestry-guarded), the four `len(forbidden) == 10` assertions (D-18), and
  `scripts/mitigation_gate.py` (FROZEN, Phase 20 D-24).
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
- **Session 2 ran the premise-check pattern a third time, and it changed the RECORD even where it
  did not change the DECISION.** All three stated premises for the n=64 corpus survived, but two
  survived on different evidence than the one offered: "the 8 anchor the chain" is really *"n=8 is
  pre-registered literally in four places, one of them `[x]` complete inside a FROZEN file"*, and
  "the soft tier's n=10 is v3.0's choice, not intrinsic" is really *"v4.0 already pre-registered its
  small capacity as 8, so n=10 contradicts GATE-10, CAL-03 and FRONT-01."* **The decision was right
  and the stated reason was weaker than the real one — which is exactly the case where writing the
  reason down matters**, because a planner inheriting the weak reason could be argued out of it.
- **A stated benefit was measured FALSE and the answer still stood.** "Zero extra base-model
  completion runs" was offered as a property of putting filler in its own module; it is not — the
  cost attaches to doing guessability at all (`exact_match_clean` takes `completions`). Saying so
  converted an unexamined assumption into D-17's **recorded waiver with its reason**, which is a
  stronger artifact than the assumption would have been if it had happened to be true.
- **Two findings in session 2 appear in no source document.** The **11-slot ceiling** — only 11
  slots exist and 8 already hold a scored fact, so the obvious filler placement would have made the
  corpus self-contradictory on exactly the slots GATE-10 scores (D-16) — and the **two extraction
  surfaces**, taught = 8 vs leak-vocabulary = 10, which is what gives "unscored" a structural
  definition instead of an intention (D-18). Both came from reading the code, not the requirement.
- **The D-11 side channel is the phase's own defect class, caught early.** Phase 20's carried
  lesson is *a guard that refuses a NAME where the harm is a PROPERTY*. D-11 is its sibling: a
  quantity **declared** public whose **value** is a function of private data. Whatever guards the
  aligned path should refuse the property, not the name.
- **Session 3 ran the premise-check a FOURTH time, and this time the premise was HALF FALSE — which
  is the first time in this phase that measuring changed the mechanism rather than only the reason.**
  The stated position was "a `mitigation_*.py` module becomes permanently frozen once its first
  artifact lands." The freeze half is true and irrevocable (`:143` reads every commit touching the
  pin, `:157` compares against the earliest add). **The naming half is false**: the freeze comes from
  `PHASE20_PREREG_ARTIFACT` (`:91`), an explicit hand-written path, not from the filename. The
  requested "middle ground — protected but not irrevocably frozen" therefore did not need inventing;
  **it is the repo's default state**, and the glob's own comment (`:64-66`) says so. Had the premise
  been accepted, the phase would have either over-frozen a module that still needs to grow or
  abandoned the glob's protection entirely — both on a mechanism that does not exist.
- **Two findings in session 3 appear in no source document.** *(a)* Adding `results/phase21_*` to
  `V4_ARTIFACT_GLOBS` **enforces nothing by itself** — `globs` is used only for the `artifact_glob in
  globs` consistency check (`:129`) and the loop runs on the singular argument. Phase 20 D-33 names
  the glob addition as the obligation and stops there, so a phase doing exactly what D-33 says would
  ship an unenforced declaration. *(b)* The `mitigation_*.py` glob carries a **hard import ceiling**
  of `{pathlib, sys, erasure_gate}` accumulated across every module in it (`:498`, `:522`), which
  makes `json` unreachable and therefore forces the rule/emission split of D-22. Neither is stated
  in any requirement; both came from reading the test.
- **A rejection's premise expired, and noticing that was worth more than the decision it changed.**
  D-10 rejected replay-as-separate-micro-steps *because* it made `grad_accum_steps` data-dependent.
  D-24's window-quantized constant makes the count `4 × n_facts` — fully public — so the premise is
  now false and the option space genuinely reopened. D-25 then chose the separate pass **on its own
  merits** rather than inheriting a conclusion from a reason that had expired. **A locked decision's
  REASON can decay while the decision still looks sound; re-reading the reason when a neighbouring
  constant changes is what catches it.**
- **D-10 and UNIT-03 turned out not to be independent, and the interaction runs the "wrong" way.**
  Moving replay out of the teaching bin (D-10) roughly **doubles** the old path's per-fact
  multiplicity, 129.2 → 262.9, because the same 1,600 draws land on half the data. A decision taken
  purely for honest accounting made the unaligned number worse — which strengthens UNIT-01's
  indictment rather than weakening it, but only because someone computed both numbers instead of one.

</specifics>

<deferred>
## Deferred Ideas

- **The GATE-10 fallback tolerance** (Phase 20 D-26) — a third chosen constant, deliberately unset.
  Must be decided before **CAL-03**, which is **Phase 23**, not Phase 21. Corrected here because
  `20-CONTEXT.md:621-623` misattributes it to Phase 21.
- **Extraction noise floor measurement** (Phase 20 D-13) — two seeds on the never-taught arm,
  **Phase 23** (CTRL-03), gated behind this phase's corpus. Carried by the Phase 20 D-14 tripwire.
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
*Context gathered: 2026-08-22 · updated 2026-08-22 (session 3) — **COMPLETE***
*Locked: D-01 … D-26. Open: 0.*
*Session 3 closed the pin/ceiling/sibling question (D-19 … D-23), D-11's replay constant
(D-24, D-25), and UNIT-03's measurement path (D-26); UNIT-05's record form fell out structurally.*
