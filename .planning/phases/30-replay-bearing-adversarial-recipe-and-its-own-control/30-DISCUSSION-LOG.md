# Phase 30: Replay-Bearing Adversarial Recipe and Its Own Control - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 30-replay-bearing-adversarial-recipe-and-its-own-control
**Areas discussed:** Seam split & arm identity, ARECIPE-02 calibration meaning, Own-control plumbing (WR-05), Schedule order (ACTRL-02)

---

## Seam split & arm identity

| Option | Description | Selected |
|--------|-------------|----------|
| New advr_n8/advr_n64 arms | New ARMS/arm_spec entries; adv_* byte-identical; name matches D-01 keys | ✓ |
| Replay flag on adv_* | --replay switch; adv_* means two recipes | |

| Option | Description | Selected |
|--------|-------------|----------|
| Two predicates | is_dp (DPSGD/accum/fact-aligned) + gets_replay (replay kwargs only) | ✓ |
| Replay dict per arm | replay_kwargs(arm) helper | |

| Option | Description | Selected |
|--------|-------------|----------|
| Existing golden tests + kwargs snapshot | incl. adv_* | ✓ |
| Also a short real CPU run diff | checkpoint byte compare | |

| Option | Description | Selected |
|--------|-------------|----------|
| Counted from actual draws | on_draw hook, per-step == prereg replay_windows(n) | ✓ |
| Recorded kwarg | configuration only | |

**User's choice:** all recommended.

---

## ARECIPE-02 calibration meaning

Premise presented: the D-05 floor is a teaching-bin mask-fraction derivation; train-time replay never enters the bin.

| Option | Description | Selected |
|--------|-------------|----------|
| Bin-level re-derivation, honestly recorded | re-measure four D-05 inputs live on advr_n8 worst corner | |
| Bin-level + descriptive effective mix | same + per-step teaching:replay mix, non-gating | ✓ |
| New effective-fraction gate | new unregistered quantity | |

**User's choice (free text, pt-BR):** Confirms option 2 — re-measure the four D-05 inputs live from build_bins on advr_n8 at the worst grid corner, recompute frac(L), commit results/phase30_calibration.json; very likely reproduces 15, recorded honestly with the structural explanation (replay outside the bin), constant imported never retyped. PLUS the per-step teaching:replay token mix at both capacities as a DESCRIPTIVE field — never decisive — making visible to Phase 34 the real window asymmetry (8 vs. 32/256) that option 1 alone would leave invisible.

| Option | Description | Selected |
|--------|-------------|----------|
| Stop at a checkpoint (≠ 15) | never silently re-pin a frozen v4.0 input | ✓ |
| v5.0-owned constant | pre-decided own floor | |

| Option | Description | Selected |
|--------|-------------|----------|
| phase29 _RECIPE_FIELDS + floor | + replay source path | ✓ |
| Digest of full train() kwargs | brittle | |

| Option | Description | Selected |
|--------|-------------|----------|
| Import v4.0's seed/steps | differs from v4.0 only in replay + control | ✓ |
| You decide | | |

---

## Own-control plumbing (WR-05)

| Option | Description | Selected |
|--------|-------------|----------|
| v5.0 driver importing v4.0 | override control/paths/arms; phase25_points untouched | ✓ |
| Edit phase25_points | smaller diff, touches v4.0 module | |

| Option | Description | Selected |
|--------|-------------|----------|
| Key + record provenance | relabelled dp_* also refused | ✓ |
| Key prefix only | | |

| Option | Description | Selected |
|--------|-------------|----------|
| phase29_prereg.control_key | AST guard forbids control_key_for / dp_ in v5.0 | ✓ |
| New driver function | two definitions | |

| Option | Description | Selected |
|--------|-------------|----------|
| Checked at read time, per point | recipe identity compare | ✓ |
| By construction only | | |

---

## Schedule order (ACTRL-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Both controls first | n8 ctrl → n64 ctrl → 10 points | ✓ |
| Per leg (POINT_KEYS order) | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Derived v5.0 SWEEP_SCHEDULE() | permutation test; POINT_KEYS stays canonical | ✓ |
| Reuse POINT_KEYS as schedule | | |

**User's choice (free text, pt-BR):** Confirms option 1 — new SWEEP_SCHEDULE() in the v5.0 driver, derived programmatically from POINT_KEYS() and control_key(), never hand-typed keys; test proves exact permutation of the 12 keys. POINT_KEYS stays the CANONICAL key order; SWEEP_SCHEDULE decides EXECUTION order — the two roles kept separate, never merged just because a particular ordering would make them coincide.

| Option | Description | Selected |
|--------|-------------|----------|
| Runtime refusal | no non-control point trains without its leg's control record | ✓ |
| Order test only | | |

---

## Claude's Discretion

- v5.0 driver / calibration module names and layout, test file names, AST-guard mechanics.
- Import vs. thin re-run of the Phase 24 derivation, provided constants are imported and inputs re-measured live.

## Deferred Ideas

None.
