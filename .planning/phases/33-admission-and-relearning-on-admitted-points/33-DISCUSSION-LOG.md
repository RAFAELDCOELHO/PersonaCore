# Phase 33: Admission and Relearning on Admitted Points - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-28
**Phase:** 33-admission-and-relearning-on-admitted-points
**Areas discussed:** Admitted-branch code, Admission record + commit, MOOT limitation + ticks, Carried debt disposal, plus a follow-up round (once-proof, AR-32 guard)

Before any question, Claude ran `phase29_prereg.admission()` live on the committed frontier and got MOOT (0/12 PASS; advr_n64 fully REFUSED, control 0/1008).

---

## Admitted-branch code

| Option | Description | Selected |
|--------|-------------|----------|
| Refusal surface only | The legs refuse unless the committed record reads ADMITTED; no training or scoring body | ✓ |
| Full apparatus, like Phase 27 | Port the curve/gate/calibrate/structural-proof legs to advr, with a CPU wiring proof | |

| Option | Description | Selected |
|--------|-------------|----------|
| Tests + live captures | A parametrized refusal test, plus byte-identical stderr captures before and after the commit (27-05) | ✓ |
| Tests only | Parametrized refusal tests only | |

## Admission record + commit

| Option | Description | Selected |
|--------|-------------|----------|
| Thin record | admission() verbatim + scope + frontier pin + provenance + limitation | ✓ |
| Mirror phase27_admission.json | All ~20 of Phase 27's fields | |

| Option | Description | Selected |
|--------|-------------|----------|
| Claude, after review | Emit without committing, developer review checkpoint, then Claude commits the file alone (31-06 / 32 D-16) | ✓ |
| Operator commits by hand | As in 27-05 | |

| Option | Description | Selected |
|--------|-------------|----------|
| No override at all | Refuse if the record exists; no --force | ✓ |
| Keep --force like Phase 27 | Deliberate overwrite flag | |

## MOOT limitation + ticks

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 27 precedent | Tick ADMIT-01/02; RELRN-06..09 unticked as a named limitation | ✓ |
| Tick RELRN-06..09 as MOOT-satisfied | Vacuous over zero admitted points | |

**User's choice (free text, pt-BR):** Option 1 confirmed, with conditions. ADMIT-01/02 are ticked only after the record is committed and the proofs exist. RELRN-06..09 stay unticked, with the row "NOT SATISFIED — named limitation: admission read MOOT". The row cites the record and PREREG-02, says only the refusal surface exists (no apparatus), and does not copy Phase 27's "apparatus never exercised". Planning files are edited by hand with snapshot and diff, with no gsd-sdk handlers.

| Option | Description | Selected |
|--------|-------------|----------|
| Per-leg, from admission() | Reasons carried verbatim; n8 measured, n64 could not be measured; apparatus not built | ✓ |
| One MOOT sentence | A single line; the n64 distinction is left to Phase 34 | |

## Carried debt disposal

| Option | Description | Selected |
|--------|-------------|----------|
| Close for lack of a consumer (P31-WR-01) | No relearning artifact on MOOT; recorded for the Phase 34 ledger | ✓ |
| Fix anyway | Move the relearning artifacts to a gitignored path now | |

**User's choice (free text):** Option 1 confirmed. P31-WR-01 goes to the Phase 34 ledger as RE-DEFERRED, with its reason, its target (the milestone that builds the legs' body) and its prerequisite (decide where artifacts live relative to refuse_if_dirty before the first is written). No output-location code is written. The planner confirms that `admit` excludes the admission record from the pathspec, with a test on a not-yet-tracked file.

| Option | Description | Selected |
|--------|-------------|----------|
| Carry to the Phase 34 ledger | No fix in 33; git_sha is the authoritative pin | ✓ |
| Fix some in 33 | Only no-pin-cost items; WR-03 was already fixed | |

**User's choice (free text):** Option 1 confirmed. CR-01, WR-01 and WR-05 are RE-DEFERRED with target "the milestone that reuses phase32_points", keeping the prerequisite fixed by the security ruling. Ids carry a phase prefix (P31-WR-01, P32-WR-01). The ledger declares git_sha authoritative and cites 32-VERIFICATION by reference. The planner checks whether any IN-* touches a published frontier field, which would call for a dated continuation instead of RE-DEFERRED.

## Follow-up round

| Option | Description | Selected |
|--------|-------------|----------|
| Refusal + commit guard | No --force; a single-commit git test; the record pinned to the frontier both ways | ✓ |
| Write refusal only | Like the Phase 32 frontier emit | |

**User's choice (free text):** Option 1 confirmed. The git test fails loudly on a shallow clone. The recorded sha256 is recomputed from the live bytes. The frontier's single commit is derived from git log, never typed. The test follows Phase 27's structure and handles the review checkpoint's not-yet-tracked state.

| Option | Description | Selected |
|--------|-------------|----------|
| AST guard | A census of phase33_*.py goes RED on a phase32_points import and cites AR-32-02; natural RED from a temp copy | ✓ |
| Note in CONTEXT only | Decision without a test | |

## Claude's Discretion

- Module and sub-command names; the exact module_sha256 set (derived from what admission() reaches); where the Phase 34 ledger rows are staged.

## Deferred Ideas

- The advr relearning apparatus body, deferred to a future milestone that admits a point (prerequisites: P31-WR-01, plus the CR-01/WR-01/WR-05 fixes if it reuses phase32_points).
