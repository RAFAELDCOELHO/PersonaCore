# Roadmap: PersonaCore

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-8 (shipped 2026-06-11) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v2.0 Weight-Based Memory** — Phases 9-15 (shipped 2026-08-12) — [archive](milestones/v2.0-ROADMAP.md)
- ✅ **v3.0 Adversarial Privacy Audit and Selective Memory Erasure** — Phases 16-19 (shipped 2026-08-19) — [archive](milestones/v3.0-ROADMAP.md)
- 🚧 **v4.0 Leakage Mitigation and Relearning Validation** — Phases 20-28 (planning, 2026-08-20)

## Overview

v1.0 built the foundation by hand: a ~13.9M-parameter GPT-style decoder, a from-scratch BPE
tokenizer, and a resumable training harness, pretrained on TinyStories on the author's own Apple
Silicon machine to headline perplexity 2.1066.

v2.0 proved the novel claim on top of it: **personalization lives in the model weights, not in a
prompt or a store.** From-scratch LoRA teaches user-specific facts into 331,776 adapter parameters
on a frozen conversational base, and a fresh process recalls them from an empty prompt with the
context provably wiped; from-scratch EWC keeps the fine-tune from destroying the base model, at a
3.6× separation clearing its pre-registered margin by 33.61×.

v3.0 stopped *asserting* that weight-based memory is private and **measured** it — then published
what the measurement said, which was not flattering. Phase 18's black-box audit returned
`LEAKAGE_DEMONSTRATED`: 92/104 = 88.5% of taught facts recovered by prompt-only attack against a
no-adapter control at exactly `0/104`. Phase 19 then attempted selective erasure under a rule
committed at `23a830c` **before Phase 16 ran**, and the committed gate returned **`FAILURE`** —
the target was erased (0/27, exactly on the floor) but all seven gated non-targets were destroyed
with it, four at total generation loss, and 77.6% of the dialogue adaptation was lost.
**Selective erasure is not selective at 331,776 parameters.** A co-headline shipped at equal
weight: the rank/exposure instrument and the generation instrument disagree on the same weights,
which retroactively scope-limits any Phase 18 conclusion resting on rank alone.

v4.0 answers the finding v3.0 measured and left open: **88.5% leakage, and no mitigation arm was
run.** It builds two training-time mitigations — from-scratch DP-SGD on the LoRA gradients (the
only arm making a formal (ε, δ) claim) and adversarial extraction-aware training (no guarantee, but
it bounds the empirical question directly) — maps both onto one privacy/utility plane at two corpus
capacities under a **three-condition** existence gate, and proves adversarially by relearning attack
that what survives cannot be cheaply reverted.

Three facts shape this roadmap and were measured before it was written. **The gate is phase-zero**
because ordering is its only evidence: `erasure_gate.py` was committed before Phase 16 ran, and the
v4.0 gate must be committed before *any* v4.0 number exists — before the cost calibration, not
merely before the sweep. **The privacy unit is the longest dependency chain** and it is design work,
not code: UNIT blocks the DP data path, which blocks the DP arm, which blocks the frontier, and "the
unit was wrong" invalidates every ε in a way no amount of re-running fixes. **Evaluation is the
binding constraint at ~1,010× training** — one sweep point at full Phase-18 fidelity is 42,480 draws
= 4.77 h against ~17 s of training, so a 16-point sweep at K=48 is 76.3 h of continuous M3 time.
That is why CAL-04 pre-registers per-point K and the promotion rule, and why a phase that "just adds
a few more sweep points" is expensive.

**The expected null is a deliverable, not a risk.** Research puts high prior probability on the DP
arm being a pre-registered null — fact-level noise-to-signal is 72σ at L=8 facts, ε_fact ≤ 4 needs
σ ≥ 15.3, and Secret Sharer Table 3 is the direct precedent (a once-inserted canary unextractable at
every ε tested, including 10⁹). The decision is to **publish that null at two capacities rather than
avoid it**: GATE-10 pre-commits both branches of the n=8-vs-n=64 comparison before either run, and
Phase 28 gives the null its own report surface. This project shipped `LEAKAGE_DEMONSTRATED` and
`FAILURE` in v3.0 and is stronger for it.

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

Full details: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) · Audit: [milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v1.0-phases/`

</details>

<details>
<summary>✅ v2.0 Weight-Based Memory (Phases 9-15) — SHIPPED 2026-08-12</summary>

- [x] Phase 9: LoRA Core (4/4 plans) — completed 2026-06-11
- [x] Phase 10: EWC Core (3/3 plans) — completed 2026-06-12
- [x] Phase 11: Conversational Data Pipeline (4/4 plans) — completed 2026-07-31
- [x] Phase 12: Stage-2 Conversational Fine-Tune (5/5 plans) — completed 2026-08-01
- [x] Phase 13: EWC A/B No-Forgetting Experiment (4/4 plans) — completed 2026-08-02
- [x] Phase 14: Teach-Then-Recall Demo (11/11 plans) — completed 2026-08-02
- [x] Phase 15: Figures & Writeup (8/8 plans) — completed 2026-08-02

**Headline results:** EWC retention PPL 3.891140 vs naive 8.524171 from a shared 2.1076 step-0
anchor. Closed-book recall 0.4921 taught / 0.3483 held-out against thresholds 0.2486 / 0.2000,
adapter-off control at exactly 0/2430. Fisher/Δ Spearman ρ = 0.801544, 95% CI [0.597984, 0.920291].

Full details: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md) · Audit: [milestones/v2.0-MILESTONE-AUDIT.md](milestones/v2.0-MILESTONE-AUDIT.md) · Phase artifacts: `milestones/v2.0-phases/`

</details>

<details>
<summary>✅ v3.0 Adversarial Privacy Audit and Selective Memory Erasure (Phases 16-19) — SHIPPED 2026-08-19</summary>

- [x] Phase 16: Weight-vs-Prompt Persistence Control (11/11 plans) — completed 2026-08-14
- [x] Phase 17: Multi-Persona Isolation Matrix (11/11 plans) — completed 2026-08-15
- [x] Phase 18: Black-Box Adversarial Extraction Audit (16/16 plans) — completed 2026-08-17
- [x] Phase 19: Selective Memory Erasure (16/16 plans) — completed 2026-08-19

**Headline results:** Phase 16 — adapter arm 90/104 questions vs the prompt arm at the floor, weight
invariance proved at max |diff| 0.0. Phase 17 — all six off-diagonals 0/104, six Holm comparisons
rejected at p = 0.0078125. Phase 18 — **`LEAKAGE_DEMONSTRATED`**, 92/104 = 88.5% (95% lower bound
0.8231) against an adapter-off arm at exactly 0/104, at 42,480 draws per arm. Phase 19 — verdict
**`FAILURE`**: (a) cleared exactly on its boundary at 0/27, all seven gated non-targets failed,
77.6% of dialogue adaptation destroyed. Ship decision **`DO NOT SHIP`**, withholding exactly one
claim and withdrawing no measurement.

Full details: [milestones/v3.0-ROADMAP.md](milestones/v3.0-ROADMAP.md) · Audit: [milestones/v3.0-MILESTONE-AUDIT.md](milestones/v3.0-MILESTONE-AUDIT.md)

</details>

### 🚧 v4.0 Leakage Mitigation and Relearning Validation (Phases 20-28)

**Milestone Goal:** v3.0 measured that weight-based memory leaks 88.5% under prompt-only attack and
ran no mitigation arm. v4.0 builds training-time mitigation, maps the privacy/utility frontier for
two mechanisms across two corpus capacities, and proves adversarially — by relearning attack — that
what survives cannot be cheaply reverted.

- [ ] **Phase 20: Pre-Registration — The Three-Condition Gate** - Every outcome threshold, the capacity-comparison rule and the per-point draw budget committed before any v4.0 number of any kind exists
- [ ] **Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus** - Fix what a record is, and prove it structurally, before any ε can be computed against the wrong one
- [ ] **Phase 22: DP-SGD Core, Accountant, and the Correctness Battery** - From-scratch per-example clipping + Gaussian noise + (ε, δ) accounting, proven on CPU against the failures that all improve the numbers
- [ ] **Phase 23: Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration** - Size the sweep from a measurement, and run the one cheap run that separates an honest negative from a silent bug
- [ ] **Phase 24: Adversarial Extraction-Aware Training + the Held-Out Attack Family** - The second arm as a data-mixture ratio, with generalization converted from a disclaimer into a measurement
- [ ] **Phase 25: Frontier Sweep and the Existence-Gate Verdict** - Both arms, both capacities, one plane, judged by importing the Phase 20 constants
- [ ] **Phase 26: Empirical Privacy Audit (Canary)** - Test the guarantee rather than the code: an empirical ε lower bound against the claimed upper bound
- [ ] **Phase 27: Relearning Attack** - Admitted by a gate call on measured numbers; recovery ceiling as the binary verdict, cost-to-recovery as the qualifying instrument
- [ ] **Phase 28: Report, the Published Null, and Milestone Close** - Publish whichever way the numbers came out, with every number in prose generated from a committed record

**Phase-zero ordering, stated as a constraint rather than a preference.** Phase 20 must be committed
and pushed before Phase 23 measures a single wall-clock number, not merely before Phase 25 sweeps.
`erasure_gate.py` earned its evidentiary weight by preceding Phase 16; a v4.0 gate that lands after
the cost calibration has none. A CPU-only ancestry test in Phase 20 asserts the gate module's
first-add precedes every v4.0 results artifact, and that test is the mechanism — not this paragraph.

**Pre-registration boundary.** A *resource* budget measured beforehand is not an *outcome* threshold
measured beforehand. X, Y and C are outcome thresholds and stay locked in `scripts/mitigation_gate.py`
before any curve point exists. Z (sweep width, per-point K, step budget) is a resource parameter set
*from* the Phase 23 measurement and lives in a separate `scripts/mitigation_budget.py`, with an AST
guard forbidding the gate from importing the budget so the distinction is a fact about the import
graph rather than a paragraph.

## Phase Details

### Phase 20: Pre-Registration — The Three-Condition Gate

**Goal**: Every rule that will judge a v4.0 number is committed to git before any v4.0 number of any
kind exists — including before the cost calibration
**Depends on**: Nothing new — imports the four constants already committed in `scripts/erasure_gate.py`
(`V20_MASKED_DIALOGUE_VAL_PPL` 4.5733, `V20_EWC_RETENTION_PPL` 3.891140, `V20_RETENTION_NOISE_FLOOR`
0.068930, `MARGIN_K` 2) plus the measured `dialogue_ppl_noise_floor` from `results/phase19_noise_floors.json`
**Requirements**: GATE-01, GATE-02, GATE-03, GATE-04, GATE-05, GATE-06, GATE-07, GATE-08, GATE-09, GATE-10, CAL-04, RPT-02
**Success Criteria** (what must be TRUE):

  1. `scripts/mitigation_gate.py` returns `PASS` / `FAIL` / `INCONCLUSIVE` for a sweep point against
     **three** conditions — extraction ≤ X, taught-fact recall ≥ Y, general capability ≥ C — with
     every argument keyword-only, no defaults, and every condition rendered into a reason string;
     condition (c)'s caps (`dialogue_cap` 4.5837288963367, `retention_cap` 4.029000) are **computed
     from imported constants**, never retyped as literals. (GATE-01, GATE-02)

  2. Y is a **pair** (`Y_taught`, `Y_heldout`) expressed as a locked fraction of the retrained
     control rather than derived from v2.0's published 0.4921 / 0.3483 — so the retrained control is
     load-bearing and gating taught-only cannot reward memorization over generalization. (GATE-03,
     GATE-04)

  3. Every verdict branch is **watched firing**, not merely written: a "mitigation that destroyed the
     model" fixture is run through `__main__` and observed returning `FAIL`; zero extraction without a
     corroborating teacher-forced NLL returns `INCONCLUSIVE` and takes precedence over `FAIL`; a sweep
     that never produced points on both sides of X (or of Y) returns `INCONCLUSIVE` rather than
     `FAILURE`; the verdict carries **arm identity**, so a DP point clearing and an adversarial point
     clearing cannot be conflated under one ∃; and a clearing point is provisional until the gate
     itself requires a second-seed replication. (GATE-05, GATE-06, GATE-07, GATE-08, GATE-09)

  4. The n=8-vs-n=64 capacity comparison rule is committed in the same module **before either run**,
     with both branches publishable — recovery at n=64 that n=8 did not achieve at equivalent ε_fact
     is a finding about where capacity stops destroying the mitigation; no recovery confirms the null
     at two capacities — and neither branch selectable after seeing data. (GATE-10)

  5. Per-point K, the full-fidelity K reserved for gate-candidate points, and the rule promoting a
     point from the first to the second are all committed before the first v4.0 artifact exists, and
     a CPU-only ancestry test asserts the gate module's first-add precedes every v4.0 results file.
     `scripts/_prose.py::normalized` exists and finds a line-wrapped phrase that `grep -c` reports as
     absent — v3.0's recorded lesson converted into a mechanism. (CAL-04, RPT-02)

**Plans**: TBD

### Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus

**Goal**: Fix what a "record" is and prove it structurally, because an ε computed against the wrong
unit is not a number that can be corrected by re-running
**Depends on**: Phase 20
**Requirements**: UNIT-01, UNIT-02, UNIT-03, UNIT-04, UNIT-05, UNIT-06
**Success Criteria** (what must be TRUE):

  1. `PRIVACY_UNIT = "one taught fact"` is committed as a decision carrying its own arithmetic —
     including why an example-level ε bounds nothing about a fact when `get_batch_memmap_masked`
     draws overlapping windows **with replacement** over a flat concatenated bin. (UNIT-01)

  2. A fact-aligned batch path exists as a **new** function, with `build_bins(..., align_facts=None)`
     byte-identical to v2.0 by default, and a structural check proves no `block_size`-aligned window
     contains token ids from two fact shards — giving q=1, no subsampling, and therefore an exact
     accountant rather than a bounded one. (UNIT-02)

  3. The effective per-fact multiplicity in gradient steps is **measured** after `build_bins` packing
     at the chosen `replay_ratio` and committed as a record — not inferred from the 22 rendered rows,
     because the multiplicity is what any published ε actually rests on. (UNIT-03)

  4. Whether PersonaChat replay participates in the DP lot is a **recorded decision** with its ε
     consequence stated (counting replay in N shrinks q and produces a flatteringly small ε), and δ is
     pinned as the literal 1e-5 with the rejected `1/N^1.1` recipe's self-contradiction at N=8
     (δ = 0.1015, failing its own `δ·N < 0.01` assertion by ~80×) recorded as the reason. (UNIT-04,
     UNIT-05)

  5. An n=64 corpus built from **unscored filler facts** exists and disturbs no published instrument
     — the 8 `LOCKED_FACTS`, the 270-question fixture and the ancestry-guarded
     `scripts/phase18_extraction.py` are all unchanged and still green. (UNIT-06)

**Plans**: TBD

### Phase 22: DP-SGD Core, Accountant, and the Correctness Battery

**Goal**: A from-scratch DP-SGD that is provably not the cheap fake — built and proven entirely on
CPU before a single second of M3 time is spent
**Depends on**: Phase 21 (the unit determines the lot, which determines the accountant)
**Requirements**: DPSGD-01, DPSGD-02, DPSGD-03, DPSGD-04, DPSGD-05, DPSGD-07
**Success Criteria** (what must be TRUE):

  1. Per-example gradient clipping + Gaussian noise on the **LoRA gradients only**, base frozen,
     enters `train()` through a **new additive gradient-side seam** — the existing `penalty_fn` is a
     loss-side seam that runs pre-`backward()` and cannot carry it. (DPSGD-01)

  2. With the seam off, the default path is **bit-identical** to the Phase-10 golden-trajectory
     fixture — the `penalty_fn` playbook verbatim, on a fixture that already exists. (DPSGD-02)

  3. The (ε, δ) accountant is stdlib `math` only, exact under q=1 composition, and agrees with two
     oracles of **different mathematics** — the closed-form q=1 identity and independent numerical
     quadrature — so an oracle cannot share the implementation's failure modes. (DPSGD-03)

  4. Each known silent-non-privacy failure is caught with its **positive control watched failing
     first**: clipping the averaged gradient instead of per-example (the cheapest fake DP-SGD is a
     two-line diff that converges fine, and `loop.py:165` already clips exactly the LoRA grads on the
     averaged gradient), noise scaled to the wrong sensitivity, noise added after averaging, and RNG
     reused across steps. (DPSGD-04)

  5. `checkpoint.py` carries an **MPS RNG slot** with backward-compatible load, and a kill→resume
     reproduces a **bit-identical reported ε** rather than merely a matching loss curve; `LoRALinear`
     is not restructured into `nn.Linear` submodules and `persona_adapter.pt` plus every v3.0
     checkpoint still load unchanged. (DPSGD-05, DPSGD-07)

**Plans**: TBD

### Phase 23: Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration

**Goal**: Size the sweep from a measurement instead of an assumption, and run the one cheap run that
separates the milestone's most likely honest negative from its most likely silent bug
**Depends on**: Phase 22 (the mechanism must exist before it can be timed), Phase 21 (the corpus),
Phase 20 (K and the promotion rule are already committed)
**Requirements**: CAL-01, CAL-02, CAL-03, CAL-05, DPSGD-06, CTRL-03
**Success Criteria** (what must be TRUE):

  1. The σ=0 point is the DP arm's **first executed run**, and it reproduces the unmitigated control
     within the seed-to-seed noise floor — recorded before any noised point exists, because every
     correctness bug in this class *improves* utility and this is the only cheap diagnostic that
     separates "DP is hard at this scale" from "the DP code is wrong". (DPSGD-06)

  2. Training wall-clock is measured on the DP path with the seam active, and generation throughput
     is **re-measured on one noised adapter** — the committed 4.77 h/point is recorded as a **floor
     for noised points, not a mean**, because the Phase-18 rate came from the un-adapted base where
     45-56 of 64 draws per shape terminated on a stop id, and a noised adapter that stops emitting
     EOS runs the full `max_new_tokens=48` on every draw. (CAL-01, CAL-05)

  3. Z — sweep width, per-point draw budget K, step budget — is committed in
     `scripts/mitigation_budget.py` with `_PROVENANCE` siblings naming the cost artifact and its
     sha256, in a module the gate is structurally forbidden by an AST guard from importing. (CAL-02)

  4. The premise the entire n=64 leg rests on — "ε is independent of N at q=1" — is **confirmed by a
     run** at n_facts=8 vs 64 at fixed σ before the expensive n=64 sweep is committed, or recorded as
     falsified with the n=64 leg not committed. It is an `[INFERENCE]` in research, not a
     measurement. (CAL-03)

  5. A **never-taught fresh adapter** is trained once at identical budget and seed protocol and
     scored — serving as both the frontier's lower-left floor and the relearning reference, so it is
     scheduled once and consumed twice. (CTRL-03)

**Plans**: TBD

### Phase 24: Adversarial Extraction-Aware Training + the Held-Out Attack Family

**Goal**: The second mitigation arm, built as a data-mixture ratio with no new training seam, and
with its generalization question converted from a disclaimer into a measurement
**Depends on**: Phase 20 (the held-out family is a pre-registration, not a choice), Phase 23 (the
committed sweep grid)
**Requirements**: ADVT-01, ADVT-02, ADVT-03
**Success Criteria** (what must be TRUE):

  1. The adapter trains against the Phase 18 attack suite with **attack intensity as the sweep axis**,
     implemented as a `build_bins(..., adversarial_ratio=0.0)` mixture ratio whose default is
     byte-identical to v2.0 — no loop change, no accountant, no per-record machinery. (ADVT-01)

  2. A **leave-one-attack-family-out** split is committed with the held-out family named **before
     training**, no family in both sides, and a zero-`(fact_id, seed_index)`-overlap structural check
     read from `results/phase18_corpus.json` — choosing the held-out family after seeing which the
     defense handles worst is the peek this project's discipline forbids. (ADVT-02)

  3. Attack intensity is disclosed as **also a token-budget axis**, reported as scored-token counts
     per arm, because through the frozen 547-live-id tokenizer the same 51-character sentence is 35
     tokens clean, 49 uppercased (1.40×) and 1.17× role-play framed — so an intensity effect and a
     budget effect are separable in the report rather than confounded. (ADVT-03)

  4. `scripts/phase18_extraction.py` is imported **read-only** (it is ancestry-guarded and
     permanently uneditable), so the attack trained against and the attack scored by cannot silently
     drift apart, and an inflation report ships with every new corpus. (ADVT-01, ADVT-02)

**Plans**: TBD

### Phase 25: Frontier Sweep and the Existence-Gate Verdict

**Goal**: Both mitigation arms on one measured-privacy × measured-utility plane at both capacities,
judged by importing the rule Phase 20 committed — with the pre-registered null a named verdict
**Depends on**: Phases 20, 21, 22, 23, 24
**Requirements**: CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04
**Success Criteria** (what must be TRUE):

  1. The **retrained unmitigated control runs first**, realised as a sweep point at
     `clip_norm=inf, noise_multiplier=0` so it differs from every DP point by exactly the two DP
     parameters; if its recall does not land in a defensible neighbourhood of v2.0's 0.4921 / 0.3483
     the sweep **stops**, because the fact-aligned recipe changed something and every later point is
     uninterpretable. Its non-bit-identity to the seam-off path is recorded **in advance** as expected
     floating-point non-associativity, so nobody later "fixes" it. (CTRL-01, CTRL-02)

  2. Both arms carry a full curve at **both capacities** (n=8 and n=64) — ε for DP-SGD, intensity for
     adversarial — swept to the never-taught floor and to σ→0 so the curve reconnects to the control
     at both ends, with the extremes run first so an empty frontier reveals itself in two runs
     instead of N. (FRONT-01)

  3. Every ε is reported at **both granularities** — example-level and fact-level, with its unit, its
     sampler and its multiplicity in the same sentence — and no bare ε can be printed outside the
     reporting helper that requires the point ε, the curve-total ε and the selection-accounting flag
     as keyword arguments. (FRONT-02)

  4. `results/phase2X_frontier.json` is the single source of truth: **counts, never rates**, with
     per-question successes so any bound is re-derivable, ordered `point_keys` proved as a hard
     equality on write, `accounting: null` on the adversarial arm as the structural statement that it
     makes no formal claim, and the gate/budget module sha256s travelling in the artifact. Every
     figure is drawn **only** from it. (FRONT-03)

  5. The verdict is computed by **importing** the gate module's constants, never by retyping a
     threshold in prose — and "no DP point clears Y at either capacity" is a named, pre-registered
     verdict rather than a failure to produce a result. (FRONT-04)

**Plans**: TBD

### Phase 26: Empirical Privacy Audit (Canary)

**Goal**: Test the **guarantee** rather than the code — the strongest available answer to "how do you
know your from-scratch DP-SGD is correct?"
**Depends on**: Phase 21 (the unscored filler-fact corpus is the in/out canary population), Phase 22
(the accountant's claimed ε_upper), Phase 25 (the published points the audit reads against)
**Requirements**: CANARY-01, CANARY-02
**Success Criteria** (what must be TRUE):

  1. One-run canary auditing produces an **empirical lower bound on ε** for a published DP point,
     built additively on the Phase 18 fixture, the cell-blind scorer, the Wilson bound and the
     42,480-draw budget precedent — no new instrument, and questions as the unit of analysis rather
     than draws. (CANARY-01)

  2. The rule "**if the measured ε_lower exceeds the ε_upper claimed by the formal accounting, the
     implementation is declared provably broken**" is committed before the audit runs, stated with no
     room for a favourable reading afterward, and the comparison is executed and published whichever
     way it comes out. (CANARY-02)

  3. The audit's verdict travels **with** the frontier artifact, so any published (ε, δ) carries its
     empirical check in the same place a reader finds the claim — and if the audit is ever cut, that
     is recorded as a named limitation under the D-16 discipline, not as silence. (CANARY-01,
     CANARY-02)

**Plans**: TBD

### Phase 27: Relearning Attack

**Goal**: Prove adversarially that what survived the mitigation cannot be cheaply reverted — or
record measurably that it can
**Depends on**: Phase 25 (admitted by a gate call on measured frontier numbers), Phase 23 (the
never-taught fresh adapter is the reference), Phase 20 (X, Z and the attacker corpus are
pre-registered)
**Requirements**: RELRN-01, RELRN-02, RELRN-03, RELRN-04, RELRN-05
**Success Criteria** (what must be TRUE):

  1. The phase is **admitted by a gate call** — `relearning_is_worth_attempting(points)` invoked once
     on measured frontier numbers, exactly the shape in which
     `erasure_is_worth_attempting(92, 104, 0, 104)` authored Phase 19. If no point cleared the
     frontier, relearning is **MOOT**, not a pass, and the milestone ships that finding. (RELRN-01)

  2. Recovered recall ≤ X within a fixed, published budget Z is the **binary pre-registered gate**,
     with Z calibrated from the two controls *before* the mitigated arm is attacked (the smallest
     budget at which both the fresh never-taught adapter and the retrained unmitigated control clear
     the recall threshold), and the baseline a **required keyword argument with no default** — a gate
     that cannot be called without the baseline cannot be evaluated without it. (RELRN-01)

  3. A **cost-to-recovery curve** over scored tokens is measured against the never-taught fresh
     adapter at identical budget and seed: mitigated ≈ fresh reads as the information having been
     removed, divergence as suppressed. (RELRN-02)

  4. The cost curve is recorded as a finding that **qualifies** the PASS/FAIL verdict and explicitly
     is not a second gate — the same "an instrument qualifies a gate's reading, it does not replace
     it" pattern v3.0 established. (RELRN-03)

  5. "Identical budget and seed" is enforced **structurally** — one shared `TrainConfig` object, an
     evidence diff read back off disk, and a data-order sha256 proof, not by convention — and
     recovery is measured on a fixture **disjoint** from anything the mitigation trained against,
     with the attacker corpus pre-registered because the corpus definition *is* the threat model.
     (RELRN-04, RELRN-05)

**Plans**: TBD

### Phase 28: Report, the Published Null, and Milestone Close

**Goal**: Publish whichever way the numbers came out — including the expected DP null at both
capacities — with every number in prose generated from a committed record rather than authored
**Depends on**: Phases 20-27
**Requirements**: RPT-01, RPT-03
**Success Criteria** (what must be TRUE):

  1. The milestone report publishes the measured outcome **including the DP null at both capacities**,
     quoting the standing expectation (72σ noise-to-signal at L=8, σ ≥ 15.3 for ε_fact ≤ 4, Secret
     Sharer Table 3 as precedent) as having been **recorded before any run** — the null gets its own
     report surface, not a risk paragraph. (RPT-01)

  2. Every ε / σ / C / q / δ appearing in `docs/REPORT.md` is asserted by test to match the module
     constant it claims to quote; tables are **generated** from committed records and re-render
     byte-identically rather than being authored; and every doc-consistency check routes through
     `_prose.normalized`. (RPT-01)

  3. `pyproject.toml` carries forward sha256-identical — **zero new runtime dependencies for a fourth
     consecutive milestone** — and the 16 inherited v3.0 debt items plus the 6 deferred stale-stamp
     items are each explicitly closed, re-deferred with a reason, or recorded as a named limitation.
     (RPT-03)

**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
| ----- | --------- | -------------- | ------ | --------- |
| 1-8 | v1.0 | 29/29 | Complete | 2026-06-10 |
| 9-15 | v2.0 | 39/39 | Complete | 2026-08-02 |
| 16-19 | v3.0 | 54/54 | Complete | 2026-08-19 |
| 20. Pre-Registration — The Three-Condition Gate | v4.0 | 0/TBD | Not started | - |
| 21. The Privacy Unit, the DP Data Path, and the n=64 Corpus | v4.0 | 0/TBD | Not started | - |
| 22. DP-SGD Core, Accountant, and the Correctness Battery | v4.0 | 0/TBD | Not started | - |
| 23. Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration | v4.0 | 0/TBD | Not started | - |
| 24. Adversarial Extraction-Aware Training + the Held-Out Attack Family | v4.0 | 0/TBD | Not started | - |
| 25. Frontier Sweep and the Existence-Gate Verdict | v4.0 | 0/TBD | Not started | - |
| 26. Empirical Privacy Audit (Canary) | v4.0 | 0/TBD | Not started | - |
| 27. Relearning Attack | v4.0 | 0/TBD | Not started | - |
| 28. Report, the Published Null, and Milestone Close | v4.0 | 0/TBD | Not started | - |

**Totals:** 19 phases complete, 122 plans (29 v1.0 + 39 v2.0 + 54 v3.0), **3 milestones shipped**.
v4.0 adds 9 phases (20-28) covering 48 requirements, 48/48 mapped, 0 orphans.

Next: `/gsd:plan-phase 20`.
