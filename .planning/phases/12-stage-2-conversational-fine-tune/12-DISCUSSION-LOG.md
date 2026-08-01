# Phase 12: Stage-2 Conversational Fine-Tune - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-31
**Phase:** 12-Stage-2 Conversational Fine-Tune
**Areas discussed:** Calibration smoke matrix

---

## Area Selection

Four gray areas offered: Calibration smoke matrix, λ sweep design & λ* pick, Production run
& stopping, Conv-base artifact & Phase 13 reuse. User selected **Calibration smoke matrix**
only; the other three went to Claude's discretion informed by research.

---

## Calibration Smoke Matrix

### Q1 — Masking decision rule (resolves Phase 11 D-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Tie goes to masked | Masked wins unless unmasked is clearly better (pre-registered margin); research prescribes masking | ✓ |
| Lower val PPL wins outright | Purely empirical, noise-sensitive at short budgets | |
| Blocking user verdict | Inflation-gate register, user renders verdict | |

**User's choice:** Tie goes to masked (Recommended)

### Q2 — LR selection

| Option | Description | Selected |
|--------|-------------|----------|
| Small LR sweep in the smoke | 3 log-spaced LRs (peak ×1, ×0.3, ×0.1), pick lowest dialogue val PPL with no retention collapse/instability | ✓ (amended) |
| Fixed heuristic, no sweep | e.g. ×0.1 of pretrain peak; risk of confounding the λ sweep | |
| Fold LR into the λ sweep | Joint matrix; multiplies short runs | |

**User's choice:** Option 1 with amendment.
**Notes:** "No retention collapse or instability" must be **measurable pre-registered gates**,
not post-hoc visual calls: (1) retention proxy via `retention_perplexity()` before/after each
short run, collapse threshold from noise-floor logic; (2) instability = NaN/Inf or
non-monotonic dialogue val PPL across the run's own logging intervals. If cheap gate
definition isn't feasible, say so explicitly and fall back to a blocking checkpoint on raw
curves — never a silent subjective call.

### Q3 — Smoke ordering & budget

| Option | Description | Selected |
|--------|-------------|----------|
| Sequential, recalibrated budget | Masking → LR → λ, each on prior winner; budget recalibrated for the dialogue corpus via the D-07 method | ✓ |
| Sequential, reuse 2500 steps | Keep v1.0's TinyStories-calibrated budget | |
| Combined matrix | Mask × LR grid; interactions muddy pre-registered rules | |

**User's choice:** Sequential, recalibrated budget (Recommended)

### Q4 — Role-token cold-start (ids 8185–8187)

| Option | Description | Selected |
|--------|-------------|----------|
| Diagnostic with escalation trigger | Log spike; pre-registered trigger escalates to a mitigation lever; nothing built unless triggered | ✓ (amended) |
| Pre-build a mitigation | Init cold rows proactively; untested intervention before proven needed | |
| Ignore — let training absorb it | Zero work; risk of polluting every smoke measurement | |

**User's choice:** Option 1 with amendment.
**Notes:** "Log the spike" gets measured framing — early-step loss AND role-token embedding
norms at a fixed cadence (every N steps through the first ~10% of the smoke budget) for a
real before/after trajectory. Any triggered mitigation is evaluated with its own before/after
comparison against the un-mitigated diagnostic run.

### Q5 — Noise-floor derivation

| Option | Description | Selected |
|--------|-------------|----------|
| Seed-pair noise run | Same config twice with different seeds; observed deltas = noise floor; margins = k× delta | ✓ (amended) |
| Reuse budget-calibration runs | Zero extra compute but budget-varying runs muddy the estimate | |
| Eval-batch variance, analytical | Cheapest; misses trajectory-level seed variance | |

**User's choice:** Option 1 with two amendments.
**Notes:** (1) k=2 pre-registered as a deliberately conservative default chosen blind, with
its rationale stated; the report must record what k each gate's observed noise floor would
have required. (2) Artifact location: ONE committed report (script + results/ markdown,
inflation-report register) covering all four smoke decisions. User also raised the checkpoint
cadence question resolved in Q6.

### Q6 — Checkpoint cadence

| Option | Description | Selected |
|--------|-------------|----------|
| Confirm proposal | Auto-proceed by pre-registered rule; ONE blocking checkpoint before the production run; violated gates halt immediately | ✓ |
| Per-stage blocking stops | Every smoke stage its own user checkpoint | |

**User's choice:** Confirm (Recommended)

---

## Claude's Discretion

- λ sweep design details (grid/range/budget, λ* pick rule — presented at the D-07 blocking
  checkpoint); sweep logs retained per EWC-03
- Production run budget & stopping policy; dialogue-format adherence evidence (TUNE-01)
- Conversational-base artifact contract; Phase 13 EWC-arm reuse coordination
- `stop_ids` wiring in `generate()`
- Mechanics: retention-proxy sample size, cold-start logging cadence, CSV/file naming

## Deferred Ideas

None — discussion stayed within phase scope.
