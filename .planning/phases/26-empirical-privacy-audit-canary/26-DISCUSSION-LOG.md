# Phase 26: Empirical Privacy Audit (Canary) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-10
**Phase:** 26-Empirical Privacy Audit (Canary)
**Areas discussed:** Target and comparator (CANARY-02), OUT-canary scorer, Budget and fidelity,
Where the verdict lives, then a second round the user asked for: ε_lower formula, deciding unit,
joint confidence, power threshold, dated continuation, ceiling disclosure, membership rule.

Before the areas were presented, six facts were measured from `results/phase25_frontier.json`
and the repo (see CONTEXT `<domain>`): the committed target rule resolves to the σ=0 control with
`epsilon: null`; all 15 noised n=8 points learned nothing by every instrument; the 56 filler
canaries have never been scored anywhere; the per-point ε_upper ladder; per-point cost; and the
Wilson-bounded ε_lower table at both units.

---

## Target and comparator (CANARY-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Control + the 15 noised n=8 points | Control = power reading; dated continuation ADDS all 15, each vs its own ε_upper; rule intact | ✓ |
| Only the committed target (control) | Comparison published as vacuous, named limitation | |
| Control + one point chosen by a rule on the CLAIM (σ=80, ε=0.634) | Cheapest non-vacuous comparison | |

**User's choice:** Option 1, in their own words: control σ=0 becomes the instrument's POWER reading;
the dated continuation adds the 15 noised n=8 points, each against its own ε_upper — all 15, never a
subset chosen after seeing a result; `audit_target_rule` stays intact, visible, superseded, not edited.

| Option | Description | Selected |
|--------|-------------|----------|
| The point's own ε at δ=1e-5 | The published per-point claim; δ enters the formula; curve total as context | (Claude) |
| Point ε AND curve total | Two comparisons; the second can never accuse anything new | |
| You decide | | ✓ |

**User's choice:** "Você decide" → Claude fixed the point's own ε at δ=1e-5 (D-02).

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-registered power gate | Threshold on ε_lower(control) committed before the run; failure → INCONCLUSIVE everywhere | ✓ |
| No gate, descriptive only | Control published beside the 15 | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| BROKEN / CONSISTENT / INCONCLUSIVE | Three-valued, one-sided, reasons with numbers | ✓ |
| Binary BROKEN / NOT BROKEN | Loses "looked and saw nothing" vs "cannot see" | |
| You decide | | |

---

## OUT-canary scorer

| Option | Description | Selected |
|--------|-------------|----------|
| Generation recall, IN and OUT with the same instrument | `score_items` over LOCKED_FACTS and FILLER_FACTS (`forms=FILLER_SLOT_FORMS`), on vs off, `contains_value` imported; new Phase-26 module; Phase 18 fixture untouched | ✓ |
| Span NLL, IN and OUT | Slot-agnostic, cheap, but a new membership threshold and not "questions as the unit" | |
| IN only; OUT = never-taught / adapter-off floors | Keeps D-17/D-18 literally, but the OUT distribution is not the registered canary population | |

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-registered precondition: adapter-off must be 0 | Adapter-off arm is the guessability probe; any off-hit excludes the filler, counted and published; D-17 waiver gets a dated continuation | ✓ |
| No exclusion; publish adapter-off beside | Inflates FPR, lowers ε_lower in the implementation's favour | |
| You decide | | |

**User's choice:** Option 1, in their own words: the adapter-off arm of the scorer itself is the
guessability probe; rule pre-registered before any point runs; a filler with ANY adapter-off hit is
EXCLUDED, counted and published explicitly (n excluded / 56), never hidden; same rule trivially for the
8 IN; D-17's waiver receives a dated continuation naming why the premise changed, original text visible.

**Claude's discretion (announced, not objected to):** same recall families for IN and OUT; both
denominators published.

---

## Budget and fidelity

| Option | Description | Selected |
|--------|-------------|----------|
| The recall instrument's own 9 draws | Identical to published recall; control IN must reproduce 790/1008 via `prove_reproduction` | ✓ |
| K=16 (CURVE_K) | Narrows nothing (unit is the question); loses comparability; ~1.8× cost | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| LaunchAgent + sidecar per point + resume | D-12 / phase25_recall pattern; pmset is at sleep 1 | ✓ |
| Foreground with caffeinate | What killed points in the sweep | |
| You decide | | |

**Claude's discretion (announced):** adapter-off measured once on the sha256-pinned base and reused
for all 16 points; order = ORDERED_POINT_KEYS restricted to dp_n8; no verdict read before all 16
sidecars exist. Estimate stated: ~40 min per point adapter-on, ~11 h total plus ~40 min for the
single adapter-off run.

---

## Where the verdict lives

| Option | Description | Selected |
|--------|-------------|----------|
| Sibling pinned both ways | `results/phase26_canary.json` carries the frontier sha256 and the 16 adapter hashes; test proves the link; frontier byte-untouched (WR-03) | ✓ |
| Re-assemble the frontier with a canary_audit block | Delete-in-its-own-commit route; 22 MB re-emit; contradicts WR-03 | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Partial artifact NEVER; named limitation instead | 16 sidecars or no artifact; dated limitation entry; Phase 28 must say so beside every ε | ✓ |
| Partial artifact allowed with explicit count | Subset determined by clock and order | |
| You decide | | |

---

## Second round (user: "at least the power threshold is a commitment I took on; the ε_lower formula is the instrument's core, not an implementation detail")

| Option | Description | Selected |
|--------|-------------|----------|
| Two directions, max | max(ln((TPR_lb−δ)/FPR_ub), ln((1−FPR_ub−δ)/(1−TPR_lb))), same two Wilson bounds, imported | ✓ |
| One direction only | Never higher than the max | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fact decides, question reported | Canary = fact (PRIVACY_UNIT); 8 IN / ≤56 OUT; ceiling ≈2.79 | ✓ |
| Question decides, fact reported | Ceiling ≈5.9 but treats correlated questions as independent | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Import z (95% each), publish joint ≥90% | One z in the repo; Bonferroni disclosed | ✓ |
| New z for 97.5% each, joint ≥95% | Second hard-coded z; other phases at another level | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| ε_lower(control) ≥ min audited ε_upper (0.634) | "Resolve at least the smallest claim it checks"; derived, no new number | ✓ |
| ε_lower(control) ≥ ceiling × fraction | New fraction to justify | |
| ε_lower(control) > 0 | Weak | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| New module `phase26_prereg.py`, `phase25_prereg.py` untouched | Imports the rule by reference, proves it yields the control, declares the extension; ancestry guard as Phase 18 | ✓ |
| New key inside CANARY_RESERVATIONS in phase25_prereg | The artifact's copy would disagree with the live module (WR-03's defect) | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| CONSISTENT with reason "above the ceiling" + ceiling published | `auditor_ceiling` field; `reachable_claims k/15` at the top; no fourth verdict | ✓ |
| Fourth verdict BEYOND_CEILING | Breaks the three-valued domain already decided | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| ≥1 question answered among the fact's ~14 | Existential, as `n_answerable`; with off = 0 a single on-hit cannot come from the base | ✓ |
| Majority of the fact's questions | Lowers ε_lower in the implementation's favour | |
| You decide | | |

---

## Claude's Discretion

- Comparator = the point's own ε at δ=1e-5 (D-02).
- Same recall families for IN and OUT; both denominators published (D-08).
- Adapter-off once on the pinned base; order; no early reads (D-17).
- Names beyond `phase26_prereg.py` / `results/phase26_canary.json`, sidecar path, plist name, record
  schema — from existing module constants.
- Degenerate bound cases named, not clipped (D-09).

## Deferred Ideas

- Auditing n=64 points (structurally impossible — D-37(ii)).
- NLL/exposure as a second distinguisher (IN-only; unmeasurable on filler).
- A joint-95% z.
- Re-assembling the frontier with an inline canary block.
- Replay-bearing adversarial re-run (v5.0 candidate).
