# Phase 36: MPS Cost Probes and Budget Commitment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-02
**Phase:** 36-mps-cost-probes-and-budget-commitment
**Areas discussed:** Probe set and gaps, Probe → hours formula, Stop line and ledger, S / halt package / run mode

---

## Area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Probe set and gaps | R1b/E4 have no COST-01 probe; E3 longest T undefined until Phase 42 | ✓ |
| Probe → hours formula | Hours only vs hours + unit caps; uncertainty from one probe | ✓ |
| Stop line and ledger | Milestone-wide ledger vs per-front lines; what happens at the line | ✓ |
| S, halt package, run mode | Default S; cut menu format; LaunchAgent; auto-commit vs approved | ✓ |

**User's choice:** "As quatro áreas, de uma vez." Rafael answered every area in one free-text block:
- **(0) Principle:** a probe measures time, not a result. It runs on an already-published
  configuration and records only times and counts. Any front without a published configuration is
  named before it runs.
- **(1) Probe set:**
  - E1: the exact reading, fixed cost and per-draw cost separated, with the Phase 31 probe beside it.
  - R1b: priced by the E1 K = 48 reading, checked against Phase 19's 68.6 min; more than 25% off
    means STOP.
  - E4: a capped reserve of 3 points.
  - E3: the cap T ≤ 800, a preference set at 4× v4.0, with P22 run at T = 800.
- **(2) Probe → hours:**
  - the budget carries hours plus per-front unit caps, which owners cannot exceed;
  - every probe has at least two repetitions and the budget uses the high bound;
  - a historical comparison is made wherever one exists, with the 25% investigation rule.
- **(3) Ledger:**
  - one milestone-wide ledger, read from the records' own wall-clock fields by a script;
  - every MPS phase consults it before launch;
  - two stops: a front past 1.5× its high bound, or the cumulative total at the stop line.
- **(4) S and cuts:**
  - S = 5 if it fits, and S is reduced to 3 before any other cut. Below 3 means stop and ask.
  - The cut table carries the hours saved and the question lost, in the order: E4 reserve, E6
    anchor on fewer adapters, S to 3, E3 whole, E1 checkpoints. R1b and the E1 core are last.
  - One unattended LaunchAgent sequence.
  - Probe records auto-commit if the plan lists them; the budget record waits for approved.

**Premises measured before the follow-up:**
- `p22_onset_sigma(800)` = 0.1578 < 0.5, so it passes.
- Phase 19's erased arm is k = 78, K = 48, seed 1337, MPS, 68.584 min.
- Phase 26 records carry only `scoring_seconds`.
- E6 anchor generation and E3 at T = 800 have no published configuration.
- Rafael's answer contained a conflict between "S before other cuts" and the cut order.

---

## E6 probe

| Option | Description | Selected |
|--------|-------------|----------|
| Timing-only anchor run | Generate at the anchor on a published adapter; keep only seconds and counts | ✓ |
| Price from A2-context | Probe only the published A2 context; the anchor cost is inferred | |
| Both, compare | Run both; use the larger per-draw cost | |

**User's choice:** Option 1, on Phase 19's k = 78 adapter, seed 1337. The text is discarded and no
success is counted. The comparison with the A2 context comes from the E1 probe, with no extra run.

## E3 probe

| Option | Description | Selected |
|--------|-------------|----------|
| T=200 + T=800 timing | Published T=200 plus a timing-only T=800 run; checks linearity, literal COST-01 | ✓ |
| T=200 only, extrapolate | Per-step × 800; a dated COST-01 rewording | |
| T=800 timing only | No published-configuration anchor | |

**User's choice:** Option 1. The T = 800 run measures training only (seconds and steps), with no
scoring; the scoring cost does not depend on T and comes from T = 200. The T = 200 run is compared
with the v4.0 record's wall-clock under the 25% rule.

## S vs cuts

| Option | Description | Selected |
|--------|-------------|----------|
| S first, automatic | S drops 5→4→3 automatically before the cut table | |
| Cut order governs | S stays 5 in the proposal; nothing is reduced automatically | ✓ |

**User's choice:** Option 2. The cut order is E4 reserve; E6 anchor on fewer adapters; S to 3; E3
whole; E1 checkpoints. S below 3 never enters the table without asking. Nothing is reduced
automatically.

## Stop line

| Option | Description | Selected |
|--------|-------------|----------|
| min(1.5×Σ, 90) (Recommended) | Phase 31's rule milestone-wide, capped by the ceiling | ✓ |
| 90 h exactly | The ceiling is the line | |
| Σ front highs | No slack | |

**User's choice:** Option 1, plus a projection check. Before each front launches, if (ledger spent +
the high bounds of the remaining fronts) > 90 h, pause and bring the cut table. No front starts
unless it fits whole.

## Lost runs

| Option | Description | Selected |
|--------|-------------|----------|
| Launch ledger file (Recommended) | Start line plus heartbeat to an append-only ledger; crashed runs counted | ✓ |
| Records only | Accept the undercount | |

**User's choice:** Option 1. A crashed run counts its hours up to its last heartbeat and is marked
"sem registro de resultado", so the hours lost per front are visible.

## E4 reserve T

| Option | Description | Selected |
|--------|-------------|----------|
| At T = 800 cap | Conservative | |
| At T = 200 | The v4.0 recipe Phase 26 audited | ✓ |

**User's choice:** Option 2. E4 audits v4.0's ε claims, which were made at T = 200 with the v4.0
recipe; the audit changes only canary inclusion. This must be recorded in the reserve's derivation.
Auditing another recipe is another front and needs approved.

---

## Claude's Discretion

- Probe prefixes, paths and record schemas (within the isolation and provenance constraints).
- The ledger file format and location.
- The mechanism enforcing unit caps on owning phases without editing `phase35_prereg.py`.

## Deferred Ideas

- E4 auditing a recipe other than v4.0's: another front, needs Rafael's approved.
