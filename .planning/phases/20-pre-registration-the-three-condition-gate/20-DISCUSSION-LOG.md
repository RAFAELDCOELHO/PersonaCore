# Phase 20: Pre-Registration — The Three-Condition Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-20
**Phase:** 20-Pre-Registration — The Three-Condition Gate
**Areas discussed:** Condition (c) form/anchor/retention leg; Gate module structure (artifact globs,
shared-helper boundary); X the extraction ceiling; Y and the control's role (incl. (c)'s lo_frac);
K, the promotion rule and the gate/budget split; the four smaller gate mechanics

**Discussion posture.** Every area opened with the user stating a position and naming a premise to
verify. Each premise was measured against the repo before being accepted; three were refined by
measurement and one was corrected. Two live measurements were run during the discussion.

---

## Condition (c) — form, anchor, and the retention leg

**Opening premise to verify:** *"has 19-16's finding already been addressed by any committed
decision from Phase 19 that carries forward?"*
**Verification result: NO.** `erasure_gate.py` unchanged (one commit, `23a830c`); the Phase 19
report prescribes no replacement form; `docs/REPORT.md` republishes without prescription; the v3.0
milestone audit carries no (c) item; and the v4.0 research cites the same 77.6% toward the
*opposite* conclusion.

### Q1 — does (c) need a lower bound, or does GATE-04's Y carry that job?

| Option | Description | Selected |
|--------|-------------|----------|
| Two-sided band on raw PPL | Both bounds control-relative; independent guard | |
| Upper bound only, re-anchored | Y catches destruction | |
| **Band on the ON−OFF adaptation gap** | Gate the quantity 19-16 measured collapsing | ✓ |
| Keep GATE-02 literally | Name the defect in the pin, accept (c) inert | |

**User's choice:** Band on the ON−OFF adaptation gap, `control_gap` from the v4.0 retrained control
as a required kwarg, never hardcoded.
**Notes:** Chosen because it measures directly the quantity 19-16 identified as missing rather than
raw PPL, which collapses directionally between "capability preserved" and "adaptation removed."
**Correction delivered during this question:** the user posed band-vs-re-anchor as alternatives;
arithmetic showed they are the same move — keeping GATE-02's `4.5837288963367` as the band's upper
bound leaves only `[4.5733, 4.5837]` inside it, i.e. a band that **selects for destruction**.

### Q2 — how is the retention leg formed?

| Option | Description | Selected |
|--------|-------------|----------|
| **Asymmetric: dialogue=gap band, retention=one-sided cap, floor re-measured** | Records the asymmetry with its reason | ✓ |
| Symmetric gap band on both legs | One rule, one shape | |
| Retention one-sided, floor left at 0.068930 | Cheapest, defect named only | |
| Drop retention from (c) | One leg only | |

**User's choice:** Asymmetric by design, with the reason recorded.
**Notes:** Dialogue's gap is sign-stable; retention's changes sign inside the already-measured range
(taught +0.3286199167186572, M1 −0.22022225029414155), making a symmetric band geometrically
incoherent for that leg specifically.

### Q3 — where and when does the measured retention floor land in git?

| Option | Description | Selected |
|--------|-------------|----------|
| v3.0-series name, lands anytime | Guard never sees it | |
| **v4.0 name, committed strictly AFTER the gate module** | Exercises the guard for real | ✓ |
| Do not land it at all | Floor stays a Phase 22/23 obligation | |

**User's choice:** `results/phase20_retention_floor.json`, strictly after `mitigation_gate.py`.
**Notes:** The floor remains a required kwarg, never a literal, justified by its two named bounds
(n=2 seeds, no CI; measured on the v3.0 recipe rather than a real v4.0 arm).
**Correction delivered:** the user's stated invariant `checked >= 1 on the first run` describes the
steady state *after* the artifact lands. At the gate's first commit the correct invariant is
`bool(checked) == bool(tracked_artifacts)` (Phase 18 shape); Phase 16's `assert checked` shape would
be red from day one and invert the ordering the phase exists to establish. Also noted:
`merge-base --is-ancestor` is reflexive, so same-commit would pass — the "strictly after" rule is
tighter than the mechanism requires and is recorded as a discipline.

### Measurement run during this area

Two-seed adapter-regime retention floor, on the committed `phase19_erase_dialogue_floor_seed{1337,
2024}` arms — **no retraining**, `n_targets = 1000285` each. Result **`0.008681618994239138`**;
the borrowed Phase 12 full-fine-tune floor is **7.94×** larger, so re-measuring makes the cap
**tighter** (3.9085032379884783 vs 4.029000), not looser. Seed 1337 reproduced the committed
`results/phase19_noise_floors.json` readings byte-for-byte — an unplanned bit-identity control.
Written to the session scratchpad only; nothing under `results/`.

---

## Gate module structure — artifact globs and the shared-helper boundary

**User's stated position (both items), then verified:**
1. `V4_ARTIFACT_GLOBS` must explicitly include `phase20_*`, proven RED-then-GREEN with a synthetic
   probe rather than assumed correct by reading the pattern.
2. `scripts/_prose.py` sits **outside** the pin's scanned set, same precedent as `_addendum.py`.

**Verification:** item 2 confirmed **structurally** — `_addendum.py`, `_verdict.py` and `_prose.py`
match **none** of `phase16_*.py` / `phase17_*.py` / `phase18_*.py` / `phase19_*.py`; the leading
underscore is the mechanism. Honest caveat recorded: the precedent is structural (fnmatch), **not
historical** — neither helper has actually been edited after its phase's artifacts landed.

Item 1 confirmed by a throwaway-repo test of four guard states: probe-before-pin → RED via
`assert prereg_commits` (a *different* red); pin-second → **RED with the ordering message**;
`git rm` → **GREEN** (reversible); re-add at the same path → **RED, first-add unchanged**
(laundering impossible); real artifact after pin → GREEN.

### Q — where does the RED-then-GREEN proof actually run?

| Option | Description | Selected |
|--------|-------------|----------|
| **Throwaway repo, committed as a test fixture** | Re-executed every CI run; real history stays clean | ✓ |
| Real repo, probe committed then `git rm`'d | Strongest one-time evidence | |
| Both | Fixture plus one real-repo probe | |

**User's choice:** Throwaway-repo fixture, committed to the suite.
**Notes:** No v4.0-named probe ever touches `git log --diff-filter=A -- 'results/phase20_*'`.

---

## X — the extraction ceiling

Derived first: X is read as a Wilson upper bound on **questions**, so `wilson_upper(0, n)` bounds it
from below. At n=104 that is **0.025355** — any lower X is unclearable at every outcome. X therefore
has a derived budget `[0.025355, ~0.885)`.

### Q1 — how is X derived?

| Option | Description | Selected |
|--------|-------------|----------|
| **Never-taught floor + k=2 margin** | Zero chosen constants; every term measured or imported | ✓ |
| Blind-calibrated floor | Procedure now, constant later (`erasure_gate` clause (a)) | |
| Fraction of the retrained control | Parallel to GATE-04, but `f` is chosen | |

**User's choice:** Never-taught floor read as a **Wilson upper bound on the control arm** (not the
raw rate), plus `MARGIN_K` imported from `erasure_gate`.
**Notes:** The user's refinement to use the Wilson upper bound rather than the raw rate makes X
**reachable by construction** — verified non-decreasing across all 105 outcomes at n=104, so a
perfect mitigation always clears and Phase 19's explicit reachability clamp becomes unnecessary.
On `ERASURE_GOAL_FRAMING`: its rejection does not transfer, because the underlying claim is
categorically different — a mathematical guarantee built into the DP-SGD mechanism, not an
unverifiable post-hoc assertion about an already-observed result.

### Q2 — which noise floor does MARGIN_K multiply?

| Option | Description | Selected |
|--------|-------------|----------|
| **Extraction floor on the never-taught arm, two seeds** | Same protocol as dialogue and retention | ✓ |
| No additive margin | Wilson width is the uncertainty | |
| Phase 19 (b) floor 0.148148 | Available today | |

**User's choice:** Extraction floor, two-seed, never-taught arm.
**Notes:** The margin swings the criterion by 25× — a floor below 0.008298 tolerates zero leaked
questions; the Phase 19 (b) floor would tolerate 25/104 = 24.04%. Borrowing (b) would repeat the
wrong-regime error just corrected for retention.

### Q3 — how does Phase 20 carry the Phase 23 floor obligation?

| Option | Description | Selected |
|--------|-------------|----------|
| Armed tripwire in the pin | Refuses a borrowed/single-seed floor | |
| **Tripwire plus a committed tolerance reporter** | Report can never omit the criterion's strength | ✓ |
| Phase 23 requirement note only | Cheapest; prose | |

**User's choice:** Both, committed now.
**Notes:** The user asked for the extraction floor to be measured before locking X.
**Reported as not runnable, with evidence:** no never-taught adapter exists; CTRL-03 is Phase 23;
its corpus is Phase 21 UNIT-01…06, marked NEEDS DESIGN; cost ~9.5 h for two seeds; and running it
now would produce a genuine v4.0 arm before the gate exists. Also reported: under the design just
confirmed **X is never a literal** — every input is a kwarg, so there is nothing to lock and
therefore nothing to measure first.

---

## Y and the control's role (also owning (c)'s lo_frac)

Reported before options: unlike X and (c)'s upper bound, **Y's fraction cannot be derived** — a
k=2-derived Y would demand the mitigation cost nothing, making the gate vacuous in the opposite
direction. It encodes a preference and is named as one.

### Q1 — is (c)'s lo_frac the same fraction as Y's?

| Option | Description | Selected |
|--------|-------------|----------|
| One fraction governs all three | One number, one justification | |
| **One `f_Y` for Y's two legs, a separate `f_C` for (c)** | Instruments measured to diverge | ✓ |

**User's choice:** Separate. Two chosen constants in the whole pin, named explicitly as milestone
preference, not disguised as derivation.
**Notes:** Applying one fraction to each leg's own control value reproduces the generalization ratio
for free, without borrowing v2.0's 0.3483/0.4921 = 0.707783, which GATE-04 forbids.

### Q2 — what is `f_Y`?

| Option | Description | Selected |
|--------|-------------|----------|
| **0.7** | Spend up to 30% of personalization | ✓ |
| 0.8 | Spend up to 20% | |
| 0.6 | Spend up to 40% | |
| Defer until the frontier is plotted | | |

**User's choice:** `f_Y = 0.7`, both legs, each against its own control value.

### Q3 — what is `f_C`?

| Option | Description | Selected |
|--------|-------------|----------|
| **0.5** | Catastrophe floor; 2.24× above the measured non-vacuity anchor | ✓ |
| 0.7 | Same as `f_Y`; (c) becomes a second utility bar | |
| 0.3 | Pure catastrophe detector, thin margin | |

**User's choice:** `f_C = 0.5`. (c) stays a catastrophe detector, distinct from Y as the utility
target — the distinction `erasure_gate` states textually. Real margin over the measured floor
0.2237, not glued to it.

---

## K, the promotion rule, and the gate/budget split

Reported before options: CAL-04 and CAL-02 genuinely contradict, and **CAL-04 contradicts itself** —
sentence 1 says "before any v4.0 artifact exists" (Phase 20), sentence 3 says "before the first
point is drawn" (Phase 25).

| Option | Description | Selected |
|--------|-------------|----------|
| **Closed K menu + promotion rule + ratchet** | Menu now, rung selected by measurement, K may only increase | ✓ |
| Rule only | Phase 23 supplies every value; no pre-registered lower bound | |
| Literal K values now | CAL-04's letter; may prove unaffordable per CAL-05 | |

**User's choice:** `K_RUNGS = (48, 24, 16, 8)` committed now; Phase 23 selects by measured
throughput; ratchet forbids any decrease once fixed.
**Notes:** The ratchet structurally eliminates the post-null K reduction that
`phase18_extraction.py:88-92` records as the ATK-03 / P18-4 weakening. The promotion rule takes K as
a required kwarg, so the gate never imports `mitigation_budget.py` and the AST guard stays intact.

---

## GATE-10 — the capacity comparison rule

| Option | Description | Selected |
|--------|-------------|----------|
| **Same σ / steps / δ / q — no tolerance constant** | Structural equivalence by identical inputs | ✓ |
| Matched ε within a committed relative tolerance | Survives CAL-03 either way; third constant | |
| Nearest-ε pairing, no tolerance | Unbounded pairing | |

**User's choice:** Structural equivalence by identical inputs, zero tolerance constant.
**Notes:** Preserves capacity (N) as the only genuinely free variable between the two compared
points. The fallback branch (if CAL-03 falsifies the q=1 independence premise) is committed now so
neither branch is selectable after seeing data — and its tolerance is recorded in CONTEXT.md as an
**explicit pending decision**, due before Phase 21's CAL-03 runs, rather than left implicit.

---

## Claude's Discretion

Three mechanics proposed by Claude and accepted as proposed, with the precedent cited for each so a
reviewer can contest any of them explicitly:

- **GATE-07 arm identity** — closed `ARMS = ("dp", "adversarial")` as a required kwarg; ∃ computed
  per arm; mixed-arm point lists refused; module-scope `_prove` on the claim-string table.
  *Precedent: Phase 19 B7.*
- **GATE-08 provisional** — an unreplicated clearing point returns `INCONCLUSIVE`, not `PASS`; the
  replication argument is required with no default. *Precedent: `zero_results_have_nll`.*
  **The alternative was explicitly rejected by the user:** a `PASS` carrying a `provisional=True`
  field would collapse the three-verdict domain into four disguised states and reintroduce exactly
  the misreading risk `zero_results_have_nll` was designed to eliminate.
- **GATE-09 fixture** — built from Phase 19's real published M1 readings, not fabricated numbers;
  labelled a fixture, never a second reading. *Precedent: 19-16's counterfactual.*

## Deferred Ideas

- The GATE-10 fallback tolerance — a third chosen constant, deliberately unset; due before CAL-03.
- Extraction noise floor measurement — Phase 23 (CTRL-03), gated behind Phase 21's corpus design.
- Re-measuring `V20_RETENTION_NOISE_FLOOR`'s v3.0 consumers — out of scope; `23a830c` must not be
  amended.
- Whether the retention leg should eventually become a gap band — needs the sign change
  characterised across more than two seeds first.
