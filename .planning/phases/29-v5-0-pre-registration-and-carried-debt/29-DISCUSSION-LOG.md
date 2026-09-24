# Phase 29: v5.0 Pre-Registration and Carried Debt - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-24
**Phase:** 29-v5-0-pre-registration-and-carried-debt
**Areas discussed:** Keys/paths/replay import, Admission frozen when?, Unlearnable-control refusal, Debt closure shape, GATE-08 + all-paths (second round)

---

## Keys, paths, replay import

| Option | Description | Selected |
|--------|-------------|----------|
| New arm names | advr_n8/advr_n64 via point_key; results/phase32_point_<key>.json | ✓ |
| Same keys, new prefix | adv_n8/adv_n64, differ only by file prefix | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Every v5.0 results file | guard over results/phase3[0-4]_* incl. probes/calibration | ✓ |
| Point/frontier/admission only | narrower guard | |

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy import in function | replay_windows(n) imports teach_persona on call; AST guard | ✓ |
| AST-read source | parse the constant without importing | |
| Hoist to torch-free module | edits teach_persona (Phase 30's seam) | |

**User's choice:** New arm names; every v5.0 results file; lazy import.
**Notes:** Developer confirmed the lazy import is the proven phase27_prereg.attacker_corpus_rows pattern, not a new mechanism, and that the AST guard (literal equal to the constant, or module-level assignment of the name) closes the silent-copy risk. Scout found `corrected_point_verdict` is the sanctioned gate route and already enforces the (0,1] precondition.

---

## Admission frozen when?

| Option | Description | Selected |
|--------|-------------|----------|
| Full contract now | 12 points, ≥1 PASS, INCONCLUSIVE precedence, own-control threshold | ✓ |
| Branching rule only | Phase 33 writes gate after frontier exists | |

| Option | Description | Selected |
|--------|-------------|----------|
| Import phase27's pins unchanged | no new numbers | ✓ |
| Re-decide for v5.0 | new set now | |

| Option | Description | Selected |
|--------|-------------|----------|
| Separate REFUSED outcome | all-REFUSED never reads MOOT | ✓ |
| Keep phase27 semantics | all-REFUSED reads MOOT | |

| Option | Description | Selected |
|--------|-------------|----------|
| REFUSED, a 4th verdict | distinct from INCONCLUSIVE | ✓ |
| INCONCLUSIVE | reuse existing label | |

| Option | Description | Selected |
|--------|-------------|----------|
| MOOT naming the refused leg | v4.0 shape | ✓ |
| Per-leg verdicts | one verdict per capacity | |

**User's choice:** Full contract now; import phase27 pins; REFUSED as a 4th verdict; mixed case MOOT naming the refused leg.
**Notes:** Developer: v4.0's MOOT was backed by a real measured capacity (dp_n8/n64); if both v5.0 capacities are refused, no real result stands behind the label, so it must read "the frontier could not be measured", never "the mitigation held" — the same epistemic distinction Phase 27 locked.

---

## Unlearnable-control refusal

| Option | Description | Selected |
|--------|-------------|----------|
| Stop the leg, record REFUSED | skip the other 5 points' training | ✓ |
| Train all 12 anyway | v4.0 behaviour | |

| Option | Description | Selected |
|--------|-------------|----------|
| Counts + recipe + v4.0 side-by-side | k/n, recipe identity, adv_n64 0/648 | ✓ |
| Counts only | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Write-once keys, no retry route | complete key set, test reddens on a retry key | ✓ |
| Also pin a recipe digest now | | |

**User's choice:** All recommended.

---

## Debt closure shape

| Option | Description | Selected |
|--------|-------------|----------|
| Keep published bytes (D-28) | runtime reader + reddening test, no re-render | ✓ |
| Re-render via dated addendum | | |
| Measure first, then decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Measured date, duration stated unknown | all 11 files | ✓ |
| Both derived from git | | |
| Validator exemption | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Constant in the prereg module | ancestry-guarded; no-accountant-import test | ✓ |
| Planning prose only | | |

**User's choice:** All recommended.

---

## GATE-08 and all paths (second round)

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-register promotion | import phase25_promotion route for advr candidates | |
| No promotion; candidate = own outcome | distinct unreplicated reading | |
| Measure first, then decide | researcher confirms, plan stops at checkpoint | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Pin every v5.0 path now | one list, guard glob derived | ✓ |
| Points/frontier/admission only | | |

**User's choice:** Measure first; pin every path.
**Notes:** Developer: the researcher confirms GATE-08 and phase25_promotion behave as described and that the promotion route imports for the advr arms without structural change or a hidden dp_* dependency; the plan stops at a checkpoint for the ruling. Clean import ⇒ option 1 is natural; real friction ⇒ choose between 1 and 2 with the friction visible, not assumed.

---

## Claude's Discretion

- Module layout, test file names, AST-guard mechanics, DEBT-01 scratch fixture shape.

## Deferred Ideas

None.
