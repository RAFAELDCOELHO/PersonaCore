# Phase 13: EWC A/B No-Forgetting Experiment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-01
**Phase:** 13-EWC A/B No-Forgetting Experiment
**Areas discussed:** Arm design & λ choice, 2×2 metric endpoints, A/B report contents & framing, Naive-arm qualitative evidence (+ artifact isolation locked during area selection)

---

## Arm design & λ choice

### Area selection (freeform amendment)
Presented areas: Arm design & λ choice / Honest-result framing / Figure design (VIZ-01/04) /
Identicality proof. User selected only Arm design, answering its two headline questions
inline: both arms fresh from `best.pt` (production run NOT reused — post-verdict
discretionary, not pre-registered; case-b consistent), and headline λ=0.01 (trade-off
demonstration, not λ=100's retention-only half-phenomenon).

### Arm config/budget

| Option | Description | Selected |
|--------|-------------|----------|
| Production config, 4000 steps (Recommended) | Unmasked, LR 9e-5, seed 1337, ≈37 min/arm; matches twin-provenance TrainConfig — only checkpoint reuse rejected, not config | ✓ |
| Smoke budget, 1250 steps | Comparable to §8 sweep registers, shorter curves | |
| New calibrated budget | Fresh pre-registered budget rule; adds a calibration step | |

### Arm count

| Option | Description | Selected |
|--------|-------------|----------|
| Two arms only (Recommended) | λ dimension covered by retained 1250-step sweep logs (VIZ-04) | ✓ |
| Add λ=100 third arm | Near-zero-drift extreme at 4000 steps; dilutes the A/B frame | |
| Full λ grid at 4000 steps | ~3h; VIZ-04 sources existing logs — likely wasted compute | |

### Seeds

| Option | Description | Selected |
|--------|-------------|----------|
| Single pair, cite noise floor (Recommended) | Effect sizes dwarf Δ_ret floor 0.069 | ✓ (amended) |
| Replicate at second seed | Four runs, bulletproof vs "lucky seed" | |
| Second seed for λ=0 only | Three runs | |

**Notes (user amendment):** single pair accepted only with the extrapolation made visible:
(1) report the floor's measurement regime (arm/budget); (2) named threats-to-validity
limitation — floor not re-verified at 4000 steps or in collapse dynamics, 30–60× margin
ratio is why it's acceptable, not proof of no risk; (3) free within-run stability check on
the λ=0 arm's own interval retention trajectory.

### Claim gate

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-register both sides (Recommended) | Retention margin + acquisition bound | |
| Retention-gated, acquisition descriptive | Only retention side gated (K=2 × Δ_ret) | ✓ (amended) |
| Fully descriptive | No gates, table speaks for itself | |

**Notes (user amendment):** acquisition is the expected non-binary side of a known trade-off,
not a claim needing a gate; the report must explain why this differs from §8's dual-margin
approach (search problem vs demonstration) — a second gate risks reproducing §8's
near-impossible-margin outcome on the central causal result for no informational gain.

---

## Artifact isolation (locked during area selection)

Before delegating "identicality proof" to discretion, the user locked one piece explicitly:
each arm gets a name-scoped output directory (checkpoints/CSVs/samples), distinct from Phase
12's production artifacts and from each other, with a WR-02-style refuse-to-overwrite guard.
The proof *mechanism* (provenance echo / config assertion / step-0 equivalence) stays
discretion — that's implementation detail; artifact isolation is the structural guard against
the failure mode WR-02 just closed.

---

## 2×2 metric endpoints

Selected from the second gray-area round (Figure design / Report framing / Naive-arm
evidence / 2×2 endpoints); answered fully inline by the user:

- End-of-run (step 4000) values, NOT best-checkpoint — fixed-budget state is what Phase 14
  inherits; best-selection adds a second decision (structurally the WR-01 risk). Any
  practical best-checkpoint mechanism must reuse `retention_perplexity`/`val_mask_bin` per
  WR-01, never ad hoc.
- Acquisition = masked dialogue val PPL per frozen gate policy, both arms — never
  raw/unmasked (silent substitution).
- Keep both arm checkpoints under isolated paths; any storage concern must be stated
  explicitly before discarding either.

---

## A/B report contents & framing

Selected with inline framing lock: ONE reconciliation section explaining §8
("not demonstrable" — a search under dual margins at smoke budget) vs Phase 13
("demonstrated" — a single pre-chosen retention-gated comparison at production budget) —
never silently juxtaposed.

### Pre-registration mechanics

| Option | Description | Selected |
|--------|-------------|----------|
| Rules in committed code first (Recommended) | Gate constants in the committed script before arms run; git history as proof | |
| Pre-registration block in CONTEXT/plan only | Prose-committed proof | |
| Both code and a report preamble | Script constants + report pre-registration table with lock-commit SHAs | ✓ |

### Reproduction cross-check

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, explicit cross-check (Recommended) | Fresh EWC arm vs finetune_prod.csv side-by-side | ✓ (amended) |
| No — keep the A/B self-contained | | |
| Footnote only | | |

**Notes (user amendment):** divergence beyond k=2×Δ_ret is a real finding blocking report
finalization (MPS non-determinism or config drift — investigate before final); raw numbers
reported side-by-side regardless. (Claude note: the cited "tensorforge set()-ordering bug"
precedent was not found in .planning/ or docs/; substance captured without the citation.)

User then chose "Next area" — remaining report mechanics (file naming, thin-script
structure) to discretion under the results/*.md precedent.

---

## Naive-arm qualitative evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, side-by-side transcripts (Recommended) | Dialogue transcripts from both arms | |
| Numbers and curves only | Purely quantitative | |
| Retention-side samples only | TinyStories-style continuations from both arms | ✓ (amended) |

**Notes (user amendment):** continuations target exactly what the retention gate measures
(base-task forgetting) — aligned with the quantitative claim, not a different axis. Shared
pre-registered prompt set + sampling protocol, ONE script run for both arms, representative
never cherry-picked, Phase 12 measured proxies applied.

---

## Claude's Discretion

- Figure design (VIZ-01/04): panel layout, styling, format, location, script placement
- Identicality-proof mechanism (provenance echo vs config assertion vs step-0 check)
- Report file naming/location and thin-script structure (results/*.md precedent)
- Mechanics: step-0 CSV pre-seeding, CSV naming within scoped paths, D-12 prompt-set size

## Deferred Ideas

None — discussion stayed within phase scope.
