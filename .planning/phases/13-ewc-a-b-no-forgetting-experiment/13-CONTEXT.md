# Phase 13: EWC A/B No-Forgetting Experiment - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Committed, unconfounded evidence that EWC mitigates catastrophic forgetting (DEMO-04, VIZ-01,
VIZ-04): two **fresh** arms fine-tuned from `best.pt` with identical seed/config/data order,
differing ONLY in the penalty (λ=0 naive vs λ=0.01 EWC), producing a 2×2 acquisition+retention
headline table, the forgetting-curve figure (retention PPL vs steps per arm, dashed 2.1066
baseline, acquisition companion panel), and the λ stability–plasticity frontier plot sourced
from Phase 12's retained 1250-step sweep logs. Everything lands in one committed A/B report in
the established `results/` register. Phase 12's production run/checkpoint is NOT consumed —
Phase 13 only consumes the fine-tune harness, the frozen gate metrics, the noise floor, and
the sweep logs.

**Standing tension this phase must handle honestly:** ROADMAP text says "λ=0 vs λ*", but
Phase 12's §8 verdict was λ*=None ("EWC not demonstrable at the 1250-step budget" under the
blind dual margin). Phase 13's λ=0.01 arm is a pre-chosen single comparison, not a λ search —
the report reconciles this explicitly (D-09).

</domain>

<decisions>
## Implementation Decisions

### Arm design & λ choice
- **D-01:** Both arms run **fresh from `best.pt`** — Phase 12's production run is NOT reused
  as the EWC arm. It was explicitly a post-verdict discretionary choice (optimized after
  seeing the negative §8 result), not a pre-registered demonstration; consistent with the
  recorded "case b: production feeds Phase-14 demo substrate only".
- **D-02:** Headline λ = **0.01, not 100**. The phase demonstrates the acquisition–retention
  TRADE-OFF is real and favorable — both sides moving in the right direction simultaneously.
  λ=100 shows only half the phenomenon (near-zero retention drift bought with destroyed
  acquisition); λ=0.01 is the only sweep grid point showing both.
- **D-03:** Arm config = the recorded twin-provenance TrainConfig: **unmasked, LR 9e-5,
  seed 1337, 4000 steps, batch 32, accum 1** (≈37 min/arm on M3/MPS fp32). Only the
  production *checkpoint reuse* is rejected — the *config* is documented and reproducible.
- **D-04:** **Two arms only.** No extra λ arms at 4000 steps; the λ dimension is covered by
  the retained 1250-step sweep logs feeding VIZ-04.
- **D-05:** **Single seed pair (1337)**, citing the Phase 12 noise floor (Δ_ret = 0.069) —
  with three mandatory report obligations:
  1. Show the check, not just the number: state what config/regime Δ_ret=0.069 was measured
     under (which arm, which budget — confirm the 1250-step smoke, name the arm config).
  2. Named limitation (threats-to-validity register): the floor was NOT re-verified at
     production budget (4000 steps) or within collapse dynamics; effect-size variance COULD
     scale with drift magnitude in a way a stable-regime floor wouldn't capture. The 30–60×
     margin ratio is stated as the reason this is judged acceptable — not as proof the risk
     doesn't exist.
  3. Free check, zero compute: pull the λ=0 arm's OWN interval-to-interval retention
     trajectory (extra_eval_fns logging already exists) — smooth/monotonic = within-run
     stability signal supporting the floor's transferability, reported alongside the
     limitation.
- **D-06:** Claim gate: **retention side pre-registered only** — "EWC mitigates forgetting" =
  EWC-arm retention beats λ=0 by > K×Δ_ret (K=2, floor 0.069). Acquisition cost is reported
  descriptively in the 2×2 with NO pass/fail gate: it is the expected, non-binary side of a
  known trade-off, not a claim requiring its own margin. The report explains why this differs
  from §8's dual-margin approach (see D-09).

### Artifact isolation (LOCKED — not discretion)
- **D-07:** Each arm gets a **name-scoped output path** (e.g. `results/phase13_naive/`,
  `results/phase13_ewc/` or equivalent naming) — checkpoints, per-run CSVs, and sample
  outputs distinct from Phase 12's production artifacts AND from each other. The driver must
  **refuse to silently overwrite** either arm's outputs on re-run — the same WR-02 guard
  discipline Phase 12's code review just installed (`finetune_dialog.py` refuse-to-rerun
  precedent). This is the structural guard against the exact failure mode WR-02 closed; it
  must not be rediscovered mid-phase.

### 2×2 metric endpoints
- **D-08:** The 2×2 cells are **end-of-run (step 4000) values, NOT best-checkpoint values** —
  the A/B claim is about model state after a fixed training budget (what Phase 14 inherits
  and real usage experiences). Best-checkpoint selection would add a second decision that
  dilutes "differs only in the penalty" — structurally the WR-01 risk. If any best-checkpoint
  mechanism is used anywhere in this phase for practical reasons (e.g. late-run instability
  guard), it must reuse `retention_perplexity` / `val_mask_bin` exactly as WR-01 established —
  never a fresh ad hoc metric. Acquisition metric = **masked dialogue val PPL**
  (`masked_perplexity`, frozen gate policy from Phase 12 §1) for BOTH arms — never
  raw/unmasked (that would be a silent metric substitution). Retention metric =
  `retention_perplexity` on the frozen sub-bin (anchor 2.1076; headline dashed baseline
  2.1066). **Both arm checkpoints are kept** under the D-07 isolated paths; if research
  surfaces a storage-budget concern, it must be stated explicitly before discarding either.

### A/B report contents & framing
- **D-09:** The report MUST contain **one reconciliation section** (not scattered) explaining
  why §8's "EWC not demonstrable at this budget" and Phase 13's retention-gated result are
  NOT in tension: §8 was a SEARCH over five λ values requiring BOTH a near-impossible
  dialogue margin AND the retention margin simultaneously at smoke budget (all-fail
  informative); Phase 13 is a DEMONSTRATION of a single pre-chosen comparison, retention-gated
  by the same validated noise floor, at production budget. Silently juxtaposing "not
  demonstrable" and "demonstrated" would read as contradiction.
- **D-10:** Pre-registration = **both code and report preamble**: the gate rule (K=2 ×
  Δ_ret=0.069, end-of-run cells, arm configs) hardcoded in the committed driver/report script
  BEFORE either arm runs (git history as proof — `finetune_smoke.py` precedent), PLUS the
  report opens with a pre-registration table (constants + the commit SHA where each rule was
  locked, smoke-report layout).
- **D-11:** The fresh EWC arm doubles as an **explicit reproduction cross-check** of Phase
  12's production run (config-identical): side-by-side endpoint numbers vs
  `results/finetune_prod.csv`, reported regardless of outcome. **Divergence beyond the
  k=2×Δ_ret margin is a REAL FINDING that blocks report finalization** until investigated —
  either an uncaptured non-determinism source (MPS device ops are a named risk category) or
  unnoticed config drift. Match or mismatch, both are informative; only a mismatch changes
  what happens next.

### Naive-arm qualitative evidence
- **D-12:** **Retention-side samples only** — TinyStories-style continuations from BOTH arm
  endpoints, NOT dialogue transcripts: the qualitative evidence targets exactly what the
  retention gate measures (base-task forgetting), staying aligned with the quantitative claim
  instead of illustrating a different axis (dialogue quality is already covered by the
  acquisition PPL numbers). Shared pre-registered prompt set and sampling protocol across
  both arms, generated in ONE script run (not two separately curated passes). Reported as
  representative samples, never cherry-picked, with Phase 12's measured proxies applied
  (stop-id termination where applicable, dead-id leakage counts).

### Claude's Discretion
- **Figure design (VIZ-01/04):** panel layout, curve styling, format (PNG/SVG), file location
  (results/ vs a figures/ dir), plotting-script placement — within the requirement text
  (retention PPL vs steps per arm, dashed 2.1066 baseline, acquisition companion panel;
  frontier = retention vs acquisition, one point per λ from the retained sweep CSVs).
- **Identicality-proof mechanism:** provenance-block echo vs config assertion in the driver
  vs step-0 equivalence check — implementation detail within the locked discipline (D-07 is
  the locked part).
- **Report file naming/location and thin-script structure** — follow the `results/*.md`
  register precedent (`inflation_report.md`, `finetune_smoke_report.md`).
- Mechanics: step-0 row pre-seeding (12-01 pinned fact: v1.0 eval block logs no step-0 row),
  CSV naming within the D-07 scoped paths, prompt-set size for D-12 samples.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` — DEMO-04 (identical arms, both retention AND acquisition —
  "retention-only is the classic sleight of hand"), VIZ-01, VIZ-04 requirement text
- `.planning/ROADMAP.md` — Phase 13 goal + 4 success criteria; dependency (13 needs 12);
  note the "λ=0 vs λ*" wording is superseded by D-02/D-09 above (λ*=None recorded)

### Phase 12 evidence this phase consumes (all committed)
- `results/finetune_smoke_report.md` — §1 frozen gate policy (masked_perplexity +
  retention_perplexity definitions every gate uses); Stage-0b noise floor (Δ_ret=0.069,
  Δ_dialog=0.0017, seeds 1337/2024, 1250 steps); Stage 3 λ sweep table; §8 λ*=None verdict
  (verbatim, unamended); the discretionary λ=0.01 production decision section
- `results/finetune_prod_run.log` — the Phase-13 provenance block: seed 1337, TrainConfig
  (lr=9e-5, batch 32, 4000 steps, warmup 100, accum 1), unmasked, ewc_lambda=0.01 "the ONE
  bit the λ=0 twin flips", anchor fingerprint (git_sha 3a46815, step 49000, val_loss 0.7378)
- `results/finetune_prod.csv` — the D-11 reproduction cross-check target (step-0-anchored
  production curve)
- `results/ft_lam_0.01.csv`, `ft_lam_0.1.csv`, `ft_lam_1.csv`, `ft_lam_10.csv`,
  `ft_lam_100.csv`, `ft_lr_9e-5.csv` — the retained 1250-step sweep logs; VIZ-04's data
  source (ft_lr_9e-5 is the λ=0 reference point)
- `results/retention_anchors.json` — step-0 anchors (sub-bin 2.1076, full-val 2.1065)

### Prior phase context (decisions inherited)
- `.planning/phases/12-stage-2-conversational-fine-tune/12-CONTEXT.md` — pre-registration
  discipline (D-05 k-chosen-blind, D-06 one-report register, D-07 checkpoint cadence);
  the "production doubles as Phase 13 arm?" question resolved here as NO (D-01)
- `.planning/phases/12-stage-2-conversational-fine-tune/12-REVIEW.md` — WR-01
  (best-selection metric consistency) and WR-02 (refuse-to-rerun over recorded evidence)
  — D-07/D-08 are direct consequences of these findings

### Code seams this phase consumes
- `scripts/finetune_dialog.py` — the GO-gated production driver precedent (hardcoded
  approved constants with report citations; `_require_go_verdict` register); the natural
  template for the A/B driver
- `src/personacore/training/loop.py` — untouched `train()` with `penalty_fn` /
  `checkpoint_extra` / `extra_eval_fns` seams; per-run CSV discipline
- `src/personacore/evaluation/perplexity.py` — `retention_perplexity()` (the ONLY
  sanctioned retention metric) + `masked_perplexity()` (the frozen acquisition gate)
- `src/personacore/continual/fisher.py` + `ewc.py` — `EWCPenalty` + the N=2000 Fisher cache
  at `best.pt` (both arms share it; λ=0 arm simply passes no penalty)
- `scripts/make_transcripts.py` — sampling-protocol precedent for the D-12 retention-side
  sample script (adapted to TinyStories-style continuations)
- `checkpoints/best.pt` — the shared starting point for both arms
- `data/dialog_train.bin` (+ `data/retention_val.bin` sub-bin, `data/dialog_val{,_mask}.bin`)
  — training data and the frozen eval bins

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `train()` + `EWCPenalty` + Fisher cache: the entire A/B is two `train()` invocations from
  `best.pt` differing only in `penalty_fn` — nothing new in the loop
- `finetune_dialog.py`: driver skeleton (constant hardcoding, GO-gate register, provenance
  printing, CSV pre-seeding with measured step-0 row) — clone/extend for the two-arm driver
- `finetune_smoke.py` + `finetune_smoke_stage3_override.py`: the committed-rules-before-
  numbers pre-registration pattern D-10 requires
- Existing sweep CSVs: VIZ-04 is pure plotting — no new runs needed for the frontier

### Established Patterns
- Pre-registration discipline (rules in committed code before numbers; blind constants with
  counterfactual reporting); evidence-over-assertion committed reports; purity/additivity
  (train() untouched, all 274 tests stay green); honest negative results stand unamended
- WR-01/WR-02 review lineage: metric consistency for any checkpoint selection; refuse-to-
  overwrite guards over recorded evidence

### Integration Points
- Phase 15 consumes: the A/B report, both figures (VIZ-01/04), and the honest reconciliation
  narrative (D-09) for the writeup
- Phase 14 is independent of this phase (consumes Phase 12's convbase + Phase 9 LoRA)
- The λ=0 arm's collapse curve becomes the definitive "naive fine-tuning forgets" evidence
  the whole v2.0 narrative rests on

</code_context>

<specifics>
## Specific Ideas

- **Trade-off, not trophy:** the headline is that λ=0.01 moves BOTH axes in the right
  direction relative to λ=0 — not that forgetting can be eliminated (λ=100 territory,
  deliberately not the headline)
- **Show the check, not the citation:** every borrowed number (noise floor, margins) appears
  with its measurement regime and an explicit transferability limitation — extrapolation
  visible and checked, never silently assumed
- **Search vs demonstration:** the §8 reconciliation framing (D-09) is the phase's key
  honesty move — same register as the 547-live-ids and λ*=None disclosures
- MPS non-determinism named as a risk category for the D-11 reproduction check. (Note: the
  discussion cited a prior "tensorforge set()-ordering bug" as project precedent; no record
  of it was found in `.planning/` or `docs/` — the substance is captured without the citation.)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Figure design and remaining report mechanics
are in-phase Claude's-discretion items, not deferrals.)

</deferred>

---

*Phase: 13-EWC A/B No-Forgetting Experiment*
*Context gathered: 2026-08-01*
