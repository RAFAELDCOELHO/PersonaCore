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

<!-- 23-12-CONTINUATION-BEGIN -->
**RETRACTED IN PLACE 2026-08-28 (plan 23-12).** The clause above — *"Evaluation is the binding
constraint at ~1,010× training — one sweep point at full Phase-18 fidelity is 42,480 draws = 4.77 h
against ~17 s of training"* — is left unamended as the record of what was believed when this
roadmap was written, and its two figures were measured **FALSE** by plan 23-11. Read from
`results/phase23_cost.json`, sha256
`f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637`, at that record's own stored
precision: the evaluation leg is a bracket, `generation.h_per_point_floor` = `5.7223403197590965` h
to `generation.h_per_point_ceiling` = `9.013691285839306` h, whose **floor already exceeds** the
`4.77` above; training is `161.12400419991462` s at the protocol-matched non-DP comparator
(`training.non_dp.training_seconds_mean`), not ~17 s; and `eval ÷ training` at the ceiling is
`201.39326098648866` on that same protocol, `410.006407009605` at the superseded non-DP protocol
(`old unmitigated control (superseded as a comparator)`, the arm the record argues is the wrong
comparator), `157.94846187604026` at `dp_n8, seam active, sigma=0` and `23.458286235587472` at
`dp_n64, seam active, sigma>0`. **No arm at any protocol is `~1,010×`.** Evaluation still binds at
every capacity, so the ordering argument this paragraph makes is unchanged — a 16-point sweep is
still the expensive thing and CAL-04's pre-registration is still why. Only the margin moves, and it
moves toward *more* wall clock, not less: the sweep is sized against `h_per_point_ceiling` because
the K ratchet in `scripts/mitigation_gate.py` has no cheap direction. The full continuation, with
all eleven pre-registered figure paths and the root cause, is in `.planning/REQUIREMENTS.md`.
<!-- 23-12-CONTINUATION-END -->

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

- [x] **Phase 20: Pre-Registration — The Three-Condition Gate** - Every outcome threshold, the capacity-comparison rule and the per-point draw budget committed before any v4.0 number of any kind exists (execution complete 2026-08-20; reopened for GATE-06 gap closure, all 12 plans executed 2026-08-21 — SC3's GATE-06 clause superseded by a dated D-34/D-37 amendment, GATE-06 discharged, `20-SECURITY.md` at `threats_open: 0`. Awaiting re-verification by `/gsd:verify-phase 20`) (completed 2026-08-21)
- [x] **Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus** - Fix what a record is, and prove it structurally, before any ε can be computed against the wrong one (completed 2026-08-25)
- [x] **Phase 22: DP-SGD Core, Accountant, and the Correctness Battery** - From-scratch per-example clipping + Gaussian noise + (ε, δ) accounting, proven on CPU against the failures that all improve the numbers (execution complete 2026-08-26; `22-VERIFICATION.md` returned `gaps_found` 4/5 — SC3's two-oracle agreement falsified by `delta_closed` discarding its second term past the `erfc` cliff — so reopened for gap closure across plans 22-12…22-16. 22-12 executed 2026-08-26: three of the five `missing:` items closed, all 7 `GOLDEN_EPSILON` rows BIT-IDENTICAL. 22-13 executed 2026-08-26: WARNING-1 closed on the direction that matters — `dp_fn=None` resuming a checkpoint carrying `dp_noise_rng` now REFUSES, while the direction 22-REVIEW's CR-04 proposed refusing stays tolerated on its measured reachability argument, with both committed guards that pin it named in `loop.py`; mutation M-H watched failing over the full suite (exactly ONE distinct RED), full suite `1303 passed, 1 skipped`. 22-14 executed 2026-08-26: `delta_quadrature` returns a probability or refuses — the `log(4*n)` Simpson-sum headroom closes the measured 404-of-4001-cell `inf` band, and the upper-bound slack is MEASURED over 5351 answered cells (the verification's literal `0.0 < delta <= 1.0` would have refused 267 of them, 4.99%, all correct). 22-15 executed 2026-08-26: the LAST `missing:` item — `epsilon_for` returned `0.0`, perfect privacy, for every σ below `sqrt(steps)/sys.float_info.max`; the quotient is now checked and answers `+inf`, CONTINUOUS with the σ=0 branch rather than relocating the discontinuity. 22-16 executed 2026-08-26: DPSGD-03's `REQUIREMENTS.md` row retracted in place with what measured it false, this wave list ticked, `22-VALIDATION.md` extended by nine rows (V-26…V-34), and WARNING-2 routed to Phase 23 while WARNING-1 is recorded CLOSED. All five `missing:` items closed; full suite `1314 passed, 1 skipped`, `ruff` clean over 203 files, `scripts/mitigation_accountant.py` byte-unchanged throughout. **The 2026-08-26 re-verification confirmed all five `missing:` items closed and returned `gaps_found` 4/5 anyway — SC3 falsified on the same conjunct, one band over, in the `erfc`-SUBNORMAL range `_log_erfc`'s `e > 0.0` predicate routes to `math.log`. Reopened for 22-17 … 22-19.** Round 2 executed 2026-08-26: 22-17 re-keyed the predicate on float64's smallest NORMAL and dropped the two-oracle gap at the frozen δ from `1.9190e-03` to `1.0152e-11` inside an UNWIDENED 1e-9 budget, with a 17-row band table that sweeps the routing boundary's own neighbourhood instead of a point list; 22-18 made the suite able to SEE the band — a fourteenth `DELTA_FRONTIER` row with a SUBNORMAL `erfc(b)`, `_inert_points()` retargeted, and a round-trip σ that reaches its own worst case; 22-19 corrected the record, retracting in place the false *"EXACTLY ZERO at σ ≥ 0.42"* figure that made the band look covered and naming WARNING-4 as genuinely open. Full suite `1338 passed, 1 skipped`, `ruff` clean over 203 files, `scripts/mitigation_accountant.py` byte-unchanged across all eight gap plans. **SC3's verdict is the next `/gsd:verify-phase 22`'s; no plan in this phase has claimed it.**)
- [x] **Phase 23: Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration** - Size the sweep from a measurement, and run the one cheap run that separates an honest negative from a silent bug (completed 2026-08-29)
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

     > **Amended by D-06 at plan `20-07`, and the amendment is TIGHTER.** The `retention_cap`
     > `4.029000` above is derived from `V20_RETENTION_NOISE_FLOOR = 0.068930`, a **Phase 12
     > FULL-FINE-TUNE** seed pair. `scripts/mitigation_gate.py::retention_cap` therefore takes the
     > floor as a **required keyword argument** (D-07) instead of importing that constant, and the
     > **adapter-regime** floor was measured at `20-07` — `0.008681618994239138`
     > (`results/phase20_retention_floor.json`, two seeds, bit-identity control passed exactly).
     > The governing v4.0 cap is **`3.9085032379884783`**; the borrowed `4.029` is `7.94x` looser and
     > is published beside it in the artifact as `borrowed_cap`. `dialogue_cap` `4.5837288963367` is
     > unchanged. `scripts/erasure_gate.py:246` still computes `4.029` for **Phase 19** verdicts and
     > is deliberately NOT corrected.

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

     > **Amended by D-34 and D-37 at plan `20-12` (2026-08-21). SC3's GATE-06 clause is SUPERSEDED
     > for v4.0.** Every word of SC3 above is unedited and stays the pre-registered text.
     >
     > **What was wrong.** The GATE-06 clause above — "a sweep that never produced points on both
     > sides of X (or of Y) returns `INCONCLUSIVE` rather than `FAILURE`" — is an unqualified claim
     > about the verdict behaviour of `scripts/mitigation_gate.py`, and that block is defective on
     > both axes and permanently frozen. **CR-01:** `:798-812` decided coverage on RAW rates while
     > condition (a) at `:755` decides on `wilson_upper_bound(k, n)` against the same ceiling.
     > **WR-09:** it had no held-out leg to decide at all — no `sweep_heldout_recalls` parameter
     > exists in the 21-keyword signature, so half of a pair-valued Y was never covered.
     >
     > **What governs now.** `scripts/phase20_gate_coverage.py::coverage_verdict` is the governing
     > COMPUTATION — each axis decided on the statistic that axis's criterion is decided on, both Y
     > legs included — and `::corrected_point_verdict` is the governing ROUTE to a v4.0 verdict.
     > SC3's clause is read through those. A verdict read through
     > `mitigation_gate.mitigation_point_verdict` directly is read through the superseded block and
     > does not govern.
     >
     > **The record and the guard.** `results/phase20_gate_coverage_correction.json` — its `governs`
     > field names the computation and the route, its `supersedes` field names
     > `scripts/mitigation_gate.py:798-812` — beside the D-24 dated continuation
     > `results/phase20_gate_coverage_correction.md`. Watched by
     > `tests/test_phase20_correction.py`.
     >
     > **`scripts/mitigation_gate.py` was NOT edited.** It is byte-identical to its nine pinned
     > commits, the ancestry guard is still green, and `git diff --exit-code` on it returns 0. This
     > is a dated continuation, per D-24 — never an edit to a pre-registration.
     >
     > **The honesty clause, and it is where this amendment differs from SC1's.** Not uniformly
     > tighter — both reproduced directions move toward a MORE favourable verdict; the tightening is
     > supplied by the third, previously unreported case, where `FIXTURE_CLEARING_POINT` under
     > `(3/104, 11/104)` is DEMOTED from `PASS` to `INCONCLUSIVE`. The justification is
     > criterion-matching, not conservatism. On the favourability ordering
     > `FAIL < INCONCLUSIVE < PASS`, direction (i) `INCONCLUSIVE → PASS` and direction (ii)
     > `FAIL → INCONCLUSIVE` both increase favourability, so describing that pair as movement "in
     > both directions" would publish a small over-claim inside the very amendment whose purpose is
     > to prevent one. What is claimed instead is exactly what was built: each axis's coverage test
     > reads the statistic that axis's criterion reads. The demoted `PASS` is the only
     > against-interest movement and appears in no prior report; it is published anyway.

  4. The n=8-vs-n=64 capacity comparison rule is committed in the same module **before either run**,
     with both branches publishable — recovery at n=64 that n=8 did not achieve at equivalent ε_fact
     is a finding about where capacity stops destroying the mitigation; no recovery confirms the null
     at two capacities — and neither branch selectable after seeing data. (GATE-10)

  5. Per-point K, the full-fidelity K reserved for gate-candidate points, and the rule promoting a
     point from the first to the second are all committed before the first v4.0 artifact exists, and
     a CPU-only ancestry test asserts the gate module's first-add precedes every v4.0 results file.
     `scripts/_prose.py::normalized` exists and finds a line-wrapped phrase that `grep -c` reports as
     absent — v3.0's recorded lesson converted into a mechanism. (CAL-04, RPT-02)

**Plans**: 17 plans across 16 waves (7 original + 5 gap-closure wave 1 + 5 gap-closure wave 2)

Plans:
**Wave 1**

- [x] 20-01-PLAN.md — Arm the pin's spine (verdict domain D-31, arms D-28, the two chosen constants, K_RUNGS, the decision-rule prose) and arm the Phase 18/19 ancestry guard in the same plan

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 20-02-PLAN.md — X's formula, unit and estimator, the armed D-14 provenance tripwire, and the committed tolerance reporter
- [x] 20-03-PLAN.md — `scripts/_prose.py::normalized` (RPT-02) with its differential proof, and the D-22 throwaway-repo RED-then-GREEN four-state fixture

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 20-04-PLAN.md — Condition (c)'s corrected asymmetric legs and the 21-kwarg three-condition verdict with INCONCLUSIVE ahead of FAIL

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 20-05-PLAN.md — Per-arm existence, the K ratchet and promotion rule, the GATE-10 capacity rule with both branches, and the six-outcome `__main__`. The pin closes here

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 20-06-PLAN.md — The hybrid AST register, the import-graph and constant audits, and the behavioural twin that re-runs every branch in CI

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 20-07-PLAN.md — Blocking push checkpoint, the unpinned MPS retention-floor driver, and `results/phase20_retention_floor.json` committed strictly after the pin

**Gap closure** *(`/gsd:plan-phase 20 --gaps` — 20-VERIFICATION.md gaps 1-2, 20-SECURITY.md `threats_open: 2`)*

**Wave 7**

- [x] 20-09-PLAN.md — D-34/D-35/D-36/D-37 recorded in `20-CONTEXT.md` before any artifact cites them, the eight empty REQUIREMENTS.md traceability notes (each AST-resolved against a real function and a real guard), and D-36's dated in-place GATE-02 amendment so a grep for `4.029000` lands on the correction

**Wave 8** *(blocked on Wave 7 completion — 20-08's module docstring CITES D-34/D-35, so the record must exist first; enforced by the wave graph, not asserted in prose)*

- [x] 20-08-PLAN.md — `scripts/phase20_gate_coverage.py`: `coverage_verdict` deciding each axis on the statistic its criterion is decided on (Wilson upper on X, raw rates on both Y legs), `_prove_retention_floor`, and `corrected_point_verdict` — the one route with no `sweep_extraction_rates` parameter

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 20-10-PLAN.md — `results/phase20_gate_coverage_correction.{md,json}`: the `governs`/`supersedes` artifact and the D-24 dated continuation, in two commits so the append is provably additive (dated **2026-08-21**, the day it was written, not the plan's authoring date 2026-08-20 — `20-11` must declare `ADDENDUM_HEADING` against the committed heading)

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 20-11-PLAN.md — `tests/test_phase20_correction.py`: both reproduced directions watched RED-then-GREEN, the retention refusal suite, WR-02's artifact coupling, and the AST caller census enforcing the choke point (11 tests, 957 lines; **FOUR** watched-RED breaks observed and restored byte-identically — the coverage statistic flipped to `k/n`, a scratch bypassing caller in the `ast.Attribute` form, one `_prove` deleted from `_prove_retention_floor`, and a one-digit `cap` edit. Census named `test_mitigation_point_verdict_has_no_caller_outside_this_module` — the name the shipped module already cites — not the plan's proposed name)

**Wave 11** *(blocked on Wave 10 completion)*

- [x] 20-12-PLAN.md — GATE-06 discharged in REQUIREMENTS.md, Success Criterion 3 amended in place with a dated blockquote pointing at the correction, and 20-SECURITY.md flipped to `status: verified` / `threats_open: 0` — all three against a re-run rather than against a plan (the guards re-run in the closing process: `29 passed` zero skips, both frozen files `git diff --exit-code` 0, and the FOUR gap-closure watched-RED breaks re-applied and observed failing rather than transcribed — one of which diverged from `20-11`'s record and is published. Register totals reconciled to the file's own rows at **66 threats, 66 closed, 0 open**, the eight inherited IDs transcribed from the committed `20-05` / `20-06` registers)

**Gap closure — wave 2** *(`/gsd:plan-phase 20 --gaps` — 20-VERIFICATION.md gaps 1-2 after the 2026-08-21 re-verification returned `gaps_found` at 5/6: the two Y sweep legs were validated for LENGTH ONLY, and `_prove_retention_floor` refused a NAME where the harm is a PROPERTY)*

**Wave 12**

- [x] 20-13-PLAN.md — D-38/D-39/D-40/D-41 recorded in `20-CONTEXT.md` (`4772efe`, 82 insertions / **0 deletions**) before any artifact cites them, and T-20-19 flipped back to OPEN in `20-SECURITY.md` (`status: blocked` / `threats_open: 1`, `72ef455`) as the FIRST act — an honest record of the real state while the correction is pending (D-39), in a commit separate from the re-close. THREE commits, not two: the flip's own four inserted lines falsified the `20-SECURITY.md:39` anchor this plan had written into D-39 one commit earlier, so a Rule-1 correction (`5b361f8`) re-cited the boundary by TEXT and published the measured drift map `:33→:37 :38→:42 :39→:43 :40→:44 :91→:135` — every anchor in all four sibling plans was written against the pre-flip file. Also fixed the BINDING counting method in writing (distinct `T-20-NN` ids across table lines = 66; row-starts = 39 carrying 35 distinct, which would have published 35 and contradicted the file's own `38 + 8 + 20` paragraph)

**Wave 13** *(blocked on Wave 12 — every later plan cites D-38…D-41, so the record must exist first; enforced by the wave graph, not asserted in prose)*

- [x] 20-14-PLAN.md — `coverage_verdict` gained a per-element `[0.0, 1.0]` `_prove` on BOTH Y legs (subsuming NaN with no special-case check, placed before `x_uppers` so no value reaches the axis loop unvalidated) and enforces the extraction count guard BY TYPE (`isinstance(k, int) and not isinstance(k, bool)`); the measured route-level differential armed as a tripwire — on `FIXTURE_CLEARING_POINT` at `(1,3)/(104,104)`, held-out `(0.30, 0.28)` returns INCONCLUSIVE with a GATE-06 reason while `(nan, 0.28)`, strictly MORE truncated, returned `PASS` with none and `coverage_verdict` returned `(True, (), None)` — a THREE-tuple, not the two-tuple three planning documents describe. The plan's "defined 166 lines below" message text was falsified by the very edit that would have written it (measured delta 176 after the insert), so the refusal cites `SUPERSEDED_SWEEP_SENTINEL` BY NAME and interpolates its VALUE instead. TWO code commits plus docs, not three: Task 3's two watched-RED breaks restored byte-identically, so that task has no diff and correctly no commit. Suite `874 → 876`, reconciled as exactly the two new test functions

**Wave 14** *(blocked on Wave 13 completion — same two files)*

- [x] 20-15-PLAN.md — `_prove_retention_floor` gained a magnitude bound alongside the existing `!=` name refusal (D-38): `_MAX_ADMISSIBLE_RETENTION_FLOOR`, DERIVED from the governing floor times a separately-named `_RETENTION_FLOOR_RELATIVE_TOLERANCE` (`1e-09`) and placed AFTER the `!=` so the named-value refusal still fires first and still publishes its three numbers; the sanctioned route's test harness supplies the governing floor read from `results/phase20_retention_floor.json` (D-41 — the bound refuses this repo's own fixtures at `0.009`, and all four published verdicts are bit-unchanged under the substitution with the governing cap `3.9085032379884783` TIGHTER than the fixture's `3.90914`); the aliased IMPORT censused as well as the call (GC-06), with a synthetic non-vacuity control because the real tree yields zero import hits. THREE commits: BREAK 2 measured the suite **GREEN** under a `1e-9 → 0.05` widening — a factor of 5×10⁷ that admits the fabricated `0.009` — so the plan's hedged contingency became the expected path and a tolerance PIN shipped as the third commit. Suite stayed at 876 by design: every new case went INSIDE an existing function, because two of those names are cited in shipped docstrings and in `20-SECURITY.md`; the real growth is 8 → 10 runtime refusals. T-20-78 closed only PARTIALLY and named as partial (GC-07 leaves the catch one-directional)

**Wave 15** *(blocked on Wave 14 completion)*

- [x] 20-16-PLAN.md — the second correction published: five new `defects` keys (GC-01/02/03/04/06) plus a `value_guards` block written additively into `results/phase20_gate_coverage_correction.json` with its own additivity guard, which derives the pre-write revision from `git log` (the newest blob with no `value_guards` key) and asserts every published value EQUAL; a SECOND dated continuation appended to the `.md` via `scripts/_addendum.py::append_addendum` in its own commit at **+152 / −0**; and `REQUIREMENTS.md`'s falsified "caught by the number itself" claim corrected IN PLACE, its stale refusal count re-counted at runtime (`eight` → **TEN**). THREE commits. The plan's `0 deletions` criterion is STRUCTURALLY UNSATISFIABLE for a JSON key-append — `value_guards` sorts last, so the previous last key necessarily gains a comma — and the guard's docstring SAYS line-level additivity is not its claim rather than asserting something weaker in silence. A third break (1b) was added because BREAK 1 on `evidence.X` co-fired two guards and could not distinguish which one bit; 1b mutates a leaf no re-derivation reads and reddens exactly one. Task 4 has no commit because all three breaks restored byte-identically

**Wave 16** *(blocked on Wave 15 completion)*

- [x] 20-17-PLAN.md — T-20-19 re-closed and `20-SECURITY.md` flipped back to `status: verified` / `threats_open: 0`, gated on the 20-14/20-15/20-16 breaks being RE-APPLIED and observed in the closing process (D-39) — **eight** breaks re-taken, all observed RED, all restored with `shasum -a 256` equality and `git diff --exit-code` 0, and one DIVERGED from its SUMMARY and is published rather than smoothed: the tolerance widening now reddens TWO guards where `20-15` recorded one, because `20-16` published the tolerance into the artifact and a second independent guard re-derives it. Total reconciled to the file's own **84 distinct threat IDs** (57 row-start lines, 53 distinct among them — neither is the total, which is why the method is fixed in writing), zero rows at Status `open`, and the re-close is a commit distinct from `20-13`'s OPEN flip. T-20-19's row is APPEND-ONLY, its preserved span proved byte-identical against `git show HEAD` by explicit diff, and the `20-13` `### Open` record is kept beneath the `None.` sentence so its named closing condition stays checkable. ROADMAP and STATE brought current

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

**Plans**: 11 plans across 6 waves

Plans:
**Wave 1**

- [x] 21-01-PLAN.md — pin `scripts/mitigation_unit.py` (SC1 + SC4) and ARM the `results/phase21_*` ancestry guard, both halves (D-19, D-20, D-22, D-23)
- [x] 21-02-PLAN.md — capture both v2.0 golden fixtures from a git-clean PRE-EDIT tree, with a mechanical dirty-tree refusal

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 21-03-PLAN.md — drive the phase21 prefix RED-then-GREEN through five states in a throwaway repo (D-20)
- [x] 21-04-PLAN.md — `build_bins(..., align_facts=None)`, the ragged third `*_fact.bin`, and the window-purity content proof (D-01, D-05)
- [x] 21-05-PLAN.md — `render_family(..., forms=None)` with its non-vacuity pair; `question_bank` dropped as unfalsifiable (D-16)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 21-06-PLAN.md — `get_batch_fact_aligned` and the mutate-between-calls proof that the fact map is consumed at RUN TIME (D-06)
- [x] 21-07-PLAN.md — the 56 unscored filler facts, a disjoint slot grammar, and the re-implemented minting discipline (D-12…D-17)
- [x] 21-08-PLAN.md — close the D-11 replay side channel by differential, and add `train()`'s additive replay seam (D-10, D-24, D-25)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 21-10-PLAN.md — the multiplicity instrument, its conservation law, and the proof that it can report ≠ 1 (D-26)

**Wave 5** *(blocked on Wave 4 completion)* — 21-09 is serialized BEHIND 21-10, not beside it: its three deliberate-REDs transiently mutate working-tree files it does not own (including the ancestry-guarded `scripts/phase18_extraction.py`) that 21-10's full-suite verification reads

- [x] 21-09-PLAN.md — the `dp_n8` / `dp_n64` arms (D-14) and the SC5 non-disturbance proof across all 8 `== 10` wall sites (D-18)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 21-11-PLAN.md — write and COMMIT `results/phase21_privacy_unit.json` + `results/phase21_multiplicity.json`; the guard goes live

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

**Plans**: 19 plans in 13 waves (19 executed; 22-12 … 22-16 closed the five `missing:` items
`22-VERIFICATION.md` recorded, and the 2026-08-26 **re-verification confirmed all five closed** —
then returned `gaps_found` 4/5 again on the SAME conjunct, one band over: `_log_erfc` routes on
`erfc(x) > 0.0`, so the band where `math.erfc` returns a SUBNORMAL takes `math.log` of a float that
has already lost up to 52 of its 53 mantissa bits. Reachable at the frozen δ (T=200,
σ ∈ [0.4135, 0.4185]), **privacy-UNDERSTATING** at four measured σ, and bit-identical to the
pre-22-12 code — a sibling defect the fix stepped over, not a regression. Reopened for 22-17 … 22-19.
**22-17 executed 2026-08-26:** the predicate is now keyed on `math.ldexp(1.0, -1022)` and the
two-oracle gap at σ=0.414/T=200/δ=1e-5 fell **1.9190e-03 → 1.0152e-11**, 98.5× inside a 1e-9 budget
that was NOT widened; worst over the whole reachable band is 1.0237e-11. The worst chosen-route error
over x ∈ [20,30] fell 1.2369e-05 → 2.0621e-16, which measures **equal to the floor for any routing
rule**, so no third blind band is opened. `ROUND_TRIP_REL_TOL` — a 🛑 Blocker violated by 2.07e+07×
— is now worst 4.0274e-16. The frozen pin is proven unmoved by an EMPTY `float.hex()` diff over all
19 pinned points. The structural deliverable is `LOG_ERFC_BAND` + a sweep that asserts the route
ACTUALLY CHOSEN is accurate and never names the boundary, with run-time three-regime non-vacuity.
Full suite `1332 passed, 1 skipped` = the 1314 baseline + exactly 18. **22-18 executed
2026-08-26:** the fourteenth `DELTA_FRONTIER` row lands inside the band — 14 rows, exactly 1 with a
SUBNORMAL `erfc(b)`, where 0 of the previous 22 pinned points entered it at all — `_inert_points()`
is retargeted off the filter that certified the defective band as healthy, and the round trip
reaches σ=0.414, previously 2.07e+07× over `ROUND_TRIP_REL_TOL`. Full suite `1338 passed,
1 skipped` = 22-17's 1332 **+6 exactly**, zero regressions. **22-19 executed 2026-08-26:** the
record — the false *"EXACTLY ZERO at σ ≥ 0.42"* figure retracted in place in both committed files,
`erfc_zero_x` corrected 27.5 → the measured 27.2, DPSGD-03 extended with round 2, and WARNING-4
named as genuinely OPEN rather than inherited silently. **SC3's verdict is still
`/gsd:verify-phase 22`'s** — no plan in this phase has claimed it, and 22-19 does not either.)

**Wave 1** *(no dependencies)*

- [x] 22-01-PLAN.md — Wave-0 scaffolding: privacy subpackage, the committed 60-dps reference table
      (no `mpmath`, RPT-03), and the text-taking D-05 axis-1 AST guards with six synthetic RED probes

- [x] 22-02-PLAN.md — the FROZEN pin `scripts/mitigation_accountant.py` (zero imports, `REQUIRED_FORM`,
      `REJECTED_FORM`, D-18's `NEIGHBOURING`/`SENSITIVITY_MULTIPLIER`, `GOLDEN_EPSILON`) plus D-11's
      BOTH halves and the phase23-prefix RED-then-GREEN fixture

**Wave 2** *(blocked on Wave 1)*

- [x] 22-03-PLAN.md — `accountant.py`'s two δ oracles: Balle–Wang closed form and the `exp`-only
      quadrature, with F1's SYMMETRIC silent-zero refusal and F2's log-space overflow fix

- [x] 22-04-PLAN.md — `dpsgd.py`: construct-once capture, D-04's three property refusals, per-record
      global clip, dedicated-generator noise, the single combining write, D-16's four runtime invariants

**Wave 3** *(blocked on Wave 2)*

- [x] 22-05-PLAN.md — `epsilon_for` / `sigma_for` over ONE choke point, the explicit σ=0 → ∞ branch,
      the round-trip, and V-03's composition oracle at `rel_tol` (never `==`, per F3)

- [x] 22-06-PLAN.md — the additive `dp_fn=` gradient-side seam in `_optimizer_step` + `train()`, the
      legacy clip made structurally unreachable, and V-14's golden bit-identity + V-12's differential

**Wave 4** *(blocked on Wave 3)*

- [x] 22-07-PLAN.md — `checkpoint.py`'s `rng["mps"]` slot with `.get()` back-compat, V-15's
      bit-identical resumed ε, and DPSGD-07's LoRALinear key-set stability

- [x] 22-08-PLAN.md — the additive `fact_bin=` data seam routing to `get_batch_fact_aligned`, with the
      accum-agreement refusal and the one-record-per-micro-step property

- [x] 22-09-PLAN.md — V-06 (`GOLDEN_EPSILON` re-derived from the ORACLE alone) and V-25 (D-18's
      three-site adjacency consistency check)

**Wave 5** *(blocked on Wave 4)*

- [x] 22-10-PLAN.md — D-08's four wirings at `teach_persona.py::main()` on `dp_n8`/`dp_n64`, σ and C
      as required no-default CLI arguments, and V-23's end-to-end run that writes NO scored artifact

**Wave 6** *(blocked on Wave 5)*

- [x] 22-11-PLAN.md — the four positive controls (V-18…V-21), each WATCHED failing on the real source
      with its RED output captured, then restored byte-identically and re-greened

**Wave 7** *(gap closure — blocked on `22-VERIFICATION.md`, which returned `gaps_found`, 4/5)*

- [x] 22-12-PLAN.md — `_log_erfc`: carry `delta_closed`'s second term through the `erfc` underflow
      (measured 12.7357% high at σ=0.40/T=200), add the thirteenth `DELTA_FRONTIER` row in the
      `b > 27.2` band so V-01/V-02 sweep it, and commit a 60-dps ε for the overflow-regime test —
      with all 7 `GOLDEN_EPSILON` rows asserted BIT-IDENTICAL across the fix

- [x] 22-13-PLAN.md — WARNING-1's dangerous half: refuse a resume with `dp_fn=None` from a checkpoint
      carrying `dp_noise_rng`, and record in `loop.py` why the other direction is deliberately NOT a
      refusal (it would redden two committed back-compat controls)

**Wave 8** *(blocked on Wave 7)*

- [x] 22-14-PLAN.md — `delta_quadrature` returns a probability or refuses: a `log(4*n)` headroom for
      the Simpson SUM (closing the measured 404-cell `inf` band) and an upper-bound refusal whose
      slack is measured on 4,000+ cells rather than transcribed

**Wave 9** *(blocked on Wave 8)*

- [x] 22-15-PLAN.md — `epsilon_for`'s subnormal-σ hole: check the `sqrt(steps)/sigma` QUOTIENT and
      answer `+inf` continuously with the σ=0 branch, and narrow `_delta_or_below_float64`'s swallow
      so its docstring premise is established rather than asserted

**Wave 10** *(blocked on Wave 9)*

- [x] 22-16-PLAN.md — traceability: DPSGD-03's `REQUIREMENTS.md` row corrected retract-in-place, the
      validation contract extended, and WARNING-2 (no production DP-resume driver) routed to Phase 23

**Wave 11** *(gap closure round 2 — blocked on the 2026-08-26 re-verification, `gaps_found` 4/5)*

- [x] 22-17-PLAN.md — route the erfc-SUBNORMAL band to the asymptotic series (fast path keyed on
      float64's smallest NORMAL, `math.ldexp(1.0, -1022)`), and — the real deliverable — a guard
      parametrized on the ROUTING BOUNDARY rather than on a point list: a committed 60-dps band table
      spanning all three `math.erfc` regimes, with the CHOSEN route asserted accurate at every row.
      Measured: the new predicate's worst chosen-route error EQUALS the perfect-routing floor
      (1.7586e-16), so no third blind band is opened

**Wave 12** *(blocked on Wave 11)*

- [x] 22-18-PLAN.md — make the suite able to SEE the band: a fourteenth `DELTA_FRONTIER` row with a
      SUBNORMAL `erfc(b)`, `_inert_points()` retargeted off the filter that certified the defective
      band as healthy, a `_round_trip_pairs()` σ whose T=200 leg was 2.07e+07x `ROUND_TRIP_REL_TOL`,
      all four count meta-guards moved together, and four stale accuracy bounds re-measured
      (executed 2026-08-26: row lands at `(728.2043182233367, 34.159747883408095,
      "9.980810076965e-6")` with `erfc(b) = 1.43e-322` asserted SUBNORMAL at run time and `erfc(a)`
      HEALTHY — which is why `delta_closed` never refused there. V-01 3.6662e-14 against 1.5e-12
      (40.9x inside), V-02 1.0137e-11 against an UNWIDENED 1e-9 (98.6x inside). All 14 pinned
      figures reproduced bit-exactly. The retarget was FOLDED INTO the row's own commit because the
      two are coupled: the row alone reddens TWO tests, not the one the plan predicted — the count
      guard AND a new inertness node demanding `_log_erfc` return `math.log` of a float that has
      already lost its mantissa. FIVE stale bounds re-measured, not the four planned, plus a sixth
      whose attribution was never accurate; no constant moved — every widened sweep left its bound
      where it was. M-J (test-side, watching the FILTER) 2 distinct REDs; M-H re-applied contributes
      +3 node ids at 1.28e+09x, 1.92e+06x and 2.07e+07x over their budgets; both hunk counts VERIFIED
      at 1, both restores sha256-identical. Full suite **1338 passed, 1 skipped** = 22-17's 1332
      **+6 exactly** (2 frontier legs + 4 round-trip legs), zero regressions; all 19 of 22-17's
      `float.hex()` pinned points re-diff EMPTY; frozen pin exit 0)

**Wave 13** *(blocked on Wave 12)*

- [x] 22-19-PLAN.md — the record: *"the error is EXACTLY ZERO at σ ≥ 0.42"* — the false figure that
      made this band look covered — retracted in place in BOTH committed files, `erfc_zero_x`
      corrected from 27.5 to the measured 27.2, DPSGD-03 extended with round 2, and an explicit
      statement of what would make a round 3 necessary (WARNING-4, named as genuinely open)
      (executed 2026-08-26: **no source code touched**, so the suite is UNMOVED at `1338 passed,
      1 skipped` and any movement would have been a defect. The retracted figure was re-measured
      out of tree by rebinding `_log_erfc` to the pre-fix predicate: the pre-fix ε error against
      60-dps truth is **9.6308e-12 at σ=0.4185 and 1.1001e-13 at σ=0.4200**, reaching only ~1e-16
      past σ≈0.425 and never exactly zero — reproducing `22-VERIFICATION.md`'s own 9.631e-12 /
      1.100e-13 rather than transcribing them. A SEVENTH figure was caught wrong in the process,
      and it was this plan's own: the *fix's-delta* reading also fails at exactly 0.42 (pre
      709.5584251988014 vs post 709.5584251987232, Δ 7.8216e-11; highest differing σ is **0.4238**,
      not the 0.4125 the plan asserted), so the sentence is false under BOTH readings.
      `erfc_zero_x` re-bisected to **27.2** — the float below, 27.199999999999996, still returns
      1e-323 — the *"a subnormal, still information"* premise retracted with its cost (0.20941
      absolute in the log, 23.295% relative in `delta_closed`'s second term; 53/34/18/6/3 mantissa
      bits surviving across the band), and the subnormal cliff 26.54325845425098 recorded beside
      it. `grep -o "RETRACTED IN PLACE" .planning/REQUIREMENTS.md | wc -l` = **2**; the five
      success criteria proven byte-unchanged by sha256 `73a316f4…`, HEAD against worktree)

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

**Plans**: 20 plans across 13 waves *(14 planned 2026-08-26; plans 23-15…23-19 added 2026-08-27 as GAP CLOSURE for the D-04 halt at 23-10 — waves 9–13; 23-20 added 2026-08-27 to COMPLETE 23-17's harness-killed matched run — a separate round for a separate cause, not part of that gap closure, and it adds no wave)*

Plans:
**Wave 1**

- [x] 23-01-PLAN.md — D-02 device-parametrize the Phase-22 battery onto MPS + the DPSGD-06 generator keystone
- [x] 23-02-PLAN.md — D-09 SC3 transitive out-of-process import probe; both static halves watched RED
- [x] 23-03-PLAN.md — the blind pre-registration: noise-floor reduction, D-04 halt verdict, D-06 withdrawal rule, artifact register, three ancestry guards

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 23-04-PLAN.md — CAL-03 instrument: ε/T bit-identity across capacity + the watched N-leak positive control
- [x] 23-05-PLAN.md — the cost-record schema, its refusals, ceiling-sized sizing, and the synchronize-bracketed timing helper
- [x] 23-06-PLAN.md — D-02 watched RED on MPS for all four DPSGD-04 fakes + the venue-transfer ledger
- [x] 23-07-PLAN.md — D-07 resume seam through `train_arm`, closing WARNING-2, with the MPS production kill→resume ε proof

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 23-08-PLAN.md — D-03 + D-08 one scheduling: control and never-taught at N seeds; the floor measured and committed before σ=0

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 23-09-PLAN.md — pin the floor in `scripts/mitigation_budget.py`, literal-only and zero-import, with its `_PROVENANCE` sibling

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 23-10-PLAN.md — DPSGD-06: the σ=0 run, the DP arm's first, with D-04 live — **D-04 FIRED: HALT**

> **THE SWEEP IS HALTED (2026-08-27, plan 23-10).** σ=0 read `0.7837301587301587` against a control
> central of `0.5615079365079365` — deviation `0.2222222222222222` against a floor of
> `0.05357142857142849`, **4.15× the floor**, in the **BEATS** direction. `sigma_zero_verdict` has
> no warning branch and no override flag, so **zero noised sweep points may run** until the cause is
> root-caused and fixed. Waves 6–8 below are BLOCKED, not merely unstarted. Evidence:
> `results/phase23_sigma_zero.json`; starting point: that record's `residual_differences`.

> **HALT DISCHARGED, AND WAVES 6–8 UNBLOCKED (2026-08-28).** The halt text above set its own
> release condition — *"until the cause is root-caused and fixed"*. The cause was root-caused to
> branch **(A) INVALID COMPARATOR** (`.planning/debug/sigma-zero-beats-control.md`, `status:
> resolved`) and **fixed** by building a protocol-matched comparator: plans 23-15…23-20 produced
> `results/phase23_matched_control.json` (five seeds, floor `0.0267857142857143`), and 23-19 called
> the **unedited** `phase23_prereg.sigma_zero_verdict` (byte-identical to `c7de5d4`, no override
> parameter) once against it — returning **`proceed`, deviation exactly `0.0`**, on a floor HALF the
> old one. The verdict alone made these plans *unblockABLE*; the user unblocked them on
> 2026-08-28 after verifying the one residual risk was **not materialized** — there is no live
> caller of the gate's control fields (AST census
> `test_mitigation_point_verdict_has_no_caller_outside_this_module`) and every control value in the
> tree is an explicitly-labelled fixture. **Forward rule, pre-registered:** see **CONTROL
> PROVENANCE** in `.planning/phases/23-…/deferred-items.md`. The halt paragraph above is left
> VERBATIM — it was correct when written and is not retracted.

**Wave 6** *(UNBLOCKED 2026-08-28 — the D-04 halt at 23-10 is discharged)*

- [x] 23-11-PLAN.md — CAL-01 dp_n64 timing + CAL-05 noised-adapter throughput, floor and ceiling *(**THE MILESTONE'S FIRST NOISED SWEEP POINT RAN.** `results/phase23_noised_dp_n64_sigma0p500000.json` at σ=0.5 / C=1.0 / ε=`519.6981942303134`, gated on TWO conjuncts — the MATCHED verdict's `proceed` AND the committed human unblock act `746ecf6` — never on the σ=0 record, which carries `HALT` by design. CAL-01: `1383.276182374917` s over 200 optimizer steps = `6.916380911874585` s/step at `grad_accum_steps = 64` and 32 replay micro-batches; T = 200 on BOTH capacities with NO cross-σ ε claim. CAL-05: `h_per_point_floor` `5.7223403197590965` h → `h_per_point_ceiling` `9.013691285839306` h — **both ABOVE the committed 4.77 h/point**, which is the finding. Base-condition stop counts reproduce Phase 18's table EXACTLY (56/45/56/51 of 64); rates agree 95.06–106.32%. `results/phase23_cost.json` carries four training legs each NAMING its protocol and all eleven pre-registered figure paths at full stored precision. **NO requirement ticked** — CAL-01/CAL-05 are measured, and `.planning/REQUIREMENTS.md` is byte-unchanged because 23-12 owns the retract-in-place of the row's falsified "~1,010×" claim.)*

**Wave 7** *(UNBLOCKED 2026-08-28 — the D-04 halt at 23-10 is discharged)*

- [x] 23-12-PLAN.md — D-10 retract-in-place of the falsified "~1,010×" claim across all three planning files *(**THE CLAIM IS RETRACTED IN ALL THREE FILES AND THE ORIGINALS STAND.** A dated `RETRACTED IN PLACE 2026-08-28 (plan 23-12)` continuation was APPENDED to `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` and `.planning/STATE.md`; `git diff --numstat` deletions are **0 / 0 / 0 apart from exactly FOUR lines** in REQUIREMENTS.md — the CAL-01 and CAL-05 checkbox rows and their two traceability rows, each a modify. The REQUIREMENTS continuation publishes all **eleven** pre-registered figure paths from `results/phase23_cost.json` (sha256 `f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637`) at full stored precision, every training figure and every ratio labelled with its `protocol`; the two non-DP protocols are disclosed side by side with the gap taken from the record's own `training.non_dp.wall_clock_gap_vs_superseded` = `2.035849685343305`. **No arm at any protocol is `~1,010×`** — the four ceiling ratios are `410.006407009605` / `201.39326098648866` / `157.94846187604026` / `23.458286235587472`, and all eight of the record's ratios still bind, so D-03's ordering and D-04's halt rule are unchanged and only the margin moves. The h/point table is disclosed as a FLOOR beside `generation.h_per_point_ceiling` = `9.013691285839306` h and is **left standing**. The loop-only research projection the claim descends from is named as a THIRD thing corrected, by heading text and range, without its numerals. Guarded in BOTH directions by exact string containment over one pre-registered set — `_required_figures_missing` (omissions and roundings) and `_long_figures_not_sourced` (inventions) — watched REDding on 5 constructed defects on `tmp_path`; **no allow-list exists**, asserted by AST. CAL-01 and CAL-05 TICKED. Suite `1571 passed, 1 skipped`; zero `gsd-sdk` mutation handlers called.)*
- [x] 23-13-PLAN.md — CAL-02: pin Z with `_PROVENANCE` siblings, the K ratchet, and D-06's branch *(**Z IS PINNED, AND THE RUNG WAS THE USER'S.** Task 1 computed the per-rung table live through `phase23_cost.size_sweep` at both the ceiling and the floor with the never-taught term priced separately, PRESENTED it, and selected nothing — the plan named no default and invented no spend bound, because none exists in `23-CONTEXT.md`'s D-01…D-10, in its Claude's Discretion section, in `.planning/REQUIREMENTS.md` or here. **The user selected `CURVE_K = 16` and `SWEEP_POINTS = 16`**, against a ceiling-side total of `66.09021780091668` h for one leg (`16 × 3.1471532286150796` sweep + `5 × 3.1471532286150796` never-taught), and the reply is recorded VERBATIM in `CURVE_K_PROVENANCE.selected_reply_verbatim` — persisted by the same write that consumed it. `FULL_FIDELITY_K = 48`, `STEP_BUDGET = 200` and `N_CONTROL_SEEDS = 5` are RULES, never options, each verified against its live source (`phase18_extraction.K`, `teach_persona.MAX_STEPS`, the never-taught training record's `n_seeds`). D-06 resolved from a LIVE read — `verdict: true`, both ε `24.38161088311366`, both T `4` — so `N64_LEG_WITHDRAWN = False` and the n=64 leg stands; the withdrawal branch is written and tested from a CONSTRUCTED one-ULP-falsified copy so absence is never ambiguous. `scripts/mitigation_budget.py` is **306 insertions, 0 deletions** — both pre-existing floors byte-unchanged, still literal-only and zero-import, all three guards green (literal-only, the SUBSET ceiling, and the EQUALITY ceiling with zero headroom in BOTH directions). Every constant re-derives from `results/phase23_cost.json` under exact `==`, with a watched perturbation control; `sized_against` is carried by the three ceiling-side multiplicands and asserted ABSENT on the three no throughput figure feeds. CAL-02 TICKED. Suite `1578 passed, 1 skipped` (1571 + 7 new); zero `gsd-sdk` mutation handlers called.)*

**Wave 8** *(UNBLOCKED 2026-08-28 — the D-04 halt at 23-10 is discharged)*

- [x] 23-14-PLAN.md — CTRL-03: score the never-taught adapters at the pinned K; the record the frozen gate accepts *(**THE FLOOR IS MEASURED AND IT IS ZERO.** The five adapters 23-08 trained were SCORED — never retrained; consumed by path and sha256 — on the four dose-split Phase-18 attack families at `mitigation_budget.CURVE_K = 16`, and returned **0 of 416 `core_held_out` QUESTIONS extracted at least once at EVERY seed**. 69,120 draws dispatched, 33,280 on the gated tier, `10.137392909281836` h of MPS generation. `results/phase23_never_taught.json` committed (sha256 `94ad8434…`), path CALLED out of `phase23_prereg.NEVER_TAUGHT_RECORD`. **The frozen `mitigation_gate.extraction_ceiling` ACCEPTS it on its real code path, and all FIVE of its refusals were watched firing** on degraded COPIES — the count re-read from source by AST on every suite run (2 `raise`, 3 `_prove`), each case message-checked. Counts are QUESTION-denominated with `total_draws == questions × k` asserted in the driver AND in a test; the success predicate and the question rollup are IMPORTED from the ancestry-guarded `phase18_extraction`, verified by AST. The floor is `phase23_prereg.noise_floor` CALLED over five identical readings and re-derives under exact `==`; `pooled` is ONE DESIGNATED seed at n=416 with the rejected sum-across-seeds alternative recorded. Phase 23 does NOT publish X — `extraction_ceiling` is called from a TEST only, guarded by a structural KEY walk rather than a grep the record's own provenance string would false-RED. **CAVEAT CARRIED FORWARD, not buried: the five readings are IDENTICAL so the floor is exactly `0.0`** — a real measurement over a DEGENERATE reading set, recording the absence of leakage rather than a measured spread. Its consequence is STRICTER, not looser: `MARGIN_K × 0.0 = 0`, so X reduces to `wilson_upper_bound(0, 416)` alone, the regime the gate's own docstring names where the criterion clears ONLY on a perfect erasure. **CTRL-03 TICKED — the phase's last open requirement.** Suite `1589 passed, 1 skipped` (1578 + 11 new); `ruff` clean; every frozen pin byte-unchanged; zero `gsd-sdk` mutation handlers called. One deviation, recorded rather than hidden: the first launch drew all 13,824 completions and then died in `_state_write` on a `torch.Tensor` echoed in from `load_adapted_model`'s artifact — the traceback is committed in the run log, the field was dropped, and raw draws are now persisted PER SHAPE so no post-processing defect can cost a GPU hour again.)*

> **GAP CLOSURE, PLANNED 2026-08-27 (plans 23-15…23-19).** `.planning/debug/sigma-zero-beats-control.md`
> (status `root-caused`, commit `263f5f8`) attributed the halt to branch **(A) INVALID COMPARATOR**
> and **FALSIFIED branch (B)** by direct measurement — at σ=0 with a proven non-binding `C=1e6` the
> DP seam reproduces the ordinary grad-accum gradient across all 72 LoRA tensors to a worst relative
> difference of `2.178e-07`. ONE predicate, `teach_persona.py:1389` `is_dp = arm in DP_ARMS`,
> switches the packer, the lot size AND the gradient clip together, so σ=0 measured a DIFFERENT
> TRAINING PROTOCOL. The five plans below build a PROTOCOL-MATCHED comparator equalising all three
> mechanisms — lot volume (65 vs 8 windows; teaching-token exposure 1,689,600 vs 196,867 = 8.58×),
> teaching loss weight (1.0 vs `2719/6262 = 0.4342` = 2.30×) and `grad_clip` (bound on 19/25 control
> steps at mean shrink `0.8071`, structurally absent from the DP arm) — then re-reduce the floor over
> its seeds and re-run the D-04 verdict. **`DP_ARMS` is NOT widened**: `train()`'s fact-aligned seam
> is keyed on `fact_bin`/`n_facts` (`loop.py:512`) and its replay seam on `replay_windows`, neither on
> `dp_fn`, so a non-DP arm reaches them through a direct `train()` call — the register
> `phase23_run.train_never_taught` already established. **`scripts/phase23_prereg.py` is NOT edited**
> — the new comparator is a new INPUT to `sigma_zero_verdict`, not a rule change. **23-11…23-14 stay
> BLOCKED** regardless of the re-test's outcome; unblocking them is a separate human act.

**Wave 9** *(gap closure — the blind pin, landing while `git ls-files 'results/phase23_matched_*'` is empty)*

- [x] 23-15-PLAN.md — the BLIND protocol pre-registration: `scripts/phase23_matched_prereg.py`, its artifact register, `MATCHED_GRAD_CLIP`, the THREE AST censuses (seven `dp_fn` branches in `loop.py`, seven `dp_kwargs`/`dp_accum` keys, and the 21-name production `train(...)` call set), the ONE-ATTEMPT rule stated at its true strength — three limits, one of them a case NOTHING refuses — and the σ=0-visibility disclosure, with an ancestry guard and seven refusals watched RED

**Wave 10** *(blocked on Wave 9)*

- [x] 23-16-PLAN.md — the comparator's `train()` call, the `clip_grad_norm_` capture bracket and the training leg, with all THREE AST completeness gates proven on CPU before a single GPU second

**Wave 11** *(blocked on Wave 10)*

- [ ] 23-17-PLAN.md — the `matched` sub-mode: train + score five protocol-matched arms on the σ=0 arm's OWN bins and re-reduce the floor through `phase23_prereg.noise_floor` (≤103 min MPS, sized from the committed 205.44 s / 1026.87 s legs) *(**STILL UNCHECKED ON PURPOSE.** `23-17-SUMMARY.md` exists but carries `status: INCOMPLETE` — the run was harness-killed at 3/5 and wrote NO record. `roadmap.update-plan-progress` ticked this box on 2026-08-27 keying on SUMMARY EXISTENCE; reverted by hand. **`phase.complete` re-ticked it on 2026-08-29 at phase close; reverted by hand again — same defect, second handler.** **23-20 is what completed the run.**)*

**Wave 12** *(blocked on Wave 11)*

- [x] 23-20-PLAN.md — complete 23-17's harness-killed matched run: a NEW pin beside the frozen one (`scripts/phase23_resume_prereg.py`, admitting the continuation from the record's WRITE-ORDERING alone), both one-attempt rules wired by branch on `not scored` so the frozen refusal stays reachable, seed 2025's reading-less partial bytes discarded in a visible commit, and seeds 2025 + 1339 run DETACHED to the five-seed record and the re-reduced floor *(the recomputed DAG places this BEFORE 23-18, which now `depends_on: ["23-17", "23-20"]`)*
- [x] 23-18-PLAN.md — pin `MATCHED_CONTROL_NOISE_FLOOR` beside the original in `scripts/mitigation_budget.py`, purely additive (zero deletions), zero imports, original re-scoped by dated continuation

**Wave 13** *(blocked on Wave 12)*

- [x] 23-19-PLAN.md — the re-test: `sigma_zero_verdict` called with the matched readings and the new floor against the σ=0 reading READ back (never re-run), the record written on BOTH branches, and the debug/STATE/ROADMAP continuation *(**THE RULE RETURNED `"proceed"`** — deviation exactly `0.0` against floor `0.0267857142857143`; `results/phase23_matched_verdict.json` committed. 23-11…23-14 stay BLOCKED.)*

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

**Plans**: 7 plans in 4 waves

Plans:
**Wave 1**

- [x] 24-01-PLAN.md — D-01's per-slot value-free refusal table and D-02's containment guard, watched RED then GREEN *(11 slots, key-parity refused at import; every refusal measures 18–26 scored tokens through the frozen tokenizer against a floor of 15; the sibling guard was watched RED on a planted `zorp` — `[('zorp', 1), ('zorp', 1)]` — and the incumbent ten-value assertion is AST-proved byte-identical)*
- [ ] 24-02-PLAN.md — D-09's adversarial sweep grid pinned as literals in `scripts/mitigation_budget.py`, both extremes re-derived from committed artifacts
- [ ] 24-03-PLAN.md — ADVT-02's split as TWO separately-named assertions (`family`, `source_family`) plus the dated 24-03 continuation superseding SC2's unsatisfiable key
- [ ] 24-04-PLAN.md — D-04's `contains_refusal` beside `contains_value`, and D-11's clean-frame probe populations pinned before any run

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 24-05-PLAN.md — the corpus-joined episode builder: `core_taught` only, three families, every prompt proved byte-equal to its committed row, plus the fourth `PERSONA_ALLOWLIST` entry

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 24-06-PLAN.md — the `build_bins(..., adversarial_ratio=0.0)` seam with a seed-derived interleave, byte-identical at its default, wiring sibling watched RED first

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 24-07-PLAN.md — D-05's four-corner band check and the committed ADVT-03 per-arm scored-token record

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
| 20. Pre-Registration — The Three-Condition Gate | v4.0 | 17/17 | Complete | 7/7 on 2026-08-21 |
| 21. The Privacy Unit, the DP Data Path, and the n=64 Corpus | v4.0 | 11/11 | Complete    | 2026-08-25 |
| 22. DP-SGD Core, Accountant, and the Correctness Battery | v4.0 | 19/19 | Complete    | 2026-08-26 |
| 23. Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration | v4.0 | 19/20 | Complete    | 2026-08-29 — **all six requirements closed:** CAL-01 + CAL-05 (23-11/23-12), CAL-02 (23-13), CAL-03 (23-04), DPSGD-06 (23-10), CTRL-03 (23-08 trained, 23-14 scored). Verification `23-VERIFICATION.md` 5/5 must-haves; both `human_needed` items ruled on and CLOSED by the developer the same day — DPSGD-06's stale row retracted in place at `7296b31`, the never-taught positive control landed and watched RED at `17c28c8`. `23-SECURITY.md` at `threats_open: 0` over **113 distinct threat IDs**. Suite `1591 passed, 1 skipped`. *(**19/20, not 20/20** — `phase.complete` wrote 20/20 and re-ticked 23-17; both reverted by hand. **23-17 stays deliberately unticked**: its run was harness-killed at 3/5 and wrote no record, and 23-20 completed the work under a separate continuation pre-registration.)* |
| 24. Adversarial Extraction-Aware Training + the Held-Out Attack Family | v4.0 | 1/7 | In progress | - |
| 25. Frontier Sweep and the Existence-Gate Verdict | v4.0 | 0/TBD | Not started | - |
| 26. Empirical Privacy Audit (Canary) | v4.0 | 0/TBD | Not started | - |
| 27. Relearning Attack | v4.0 | 0/TBD | Not started | - |
| 28. Report, the Published Null, and Milestone Close | v4.0 | 0/TBD | Not started | - |

**Totals:** 19 phases complete, 122 plans (29 v1.0 + 39 v2.0 + 54 v3.0), **3 milestones shipped**.
v4.0 adds 9 phases (20-28) covering 48 requirements, 48/48 mapped, 0 orphans.

Next: `/gsd:plan-phase 20`.
