# Phase 37: Clean Reproduction of the Phase 19 Verdict - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-03
**Phase:** 37-clean-reproduction-of-the-phase-19-verdict
**Areas discussed:** What R1b runs, Tolerance and "replicated", Defect E routing, R1a output

---

## Area selection

| Option | Description | Selected |
|--------|-------------|----------|
| What R1b runs | The erased arm alone on the committed prefix (k = 78 by construction), or also the re-sweep / the retrain and replicate arms (outside the 1.108 h) | ✓ |
| Tolerance and "replicated" | Bit-identity or a per-assertion tolerance; what is published if the replica fails | ✓ |
| Defect E routing | A named function proved on the records, a CPU re-sweep, or the ERASE-08 wrapper | ✓ |
| R1a output | Assert-only, or also a write-once `results/phase37_*` record | ✓ |

**User's choice:** "As quatro áreas, de uma vez." Rafael answered every area in one free-text block
(Portuguese; summarised faithfully here):
1. **R1b:** the erased arm at K = 48 plus a re-derivation of the prefix. The selection sweep is
   re-run through the defect-E routing, so that k = 78 is measured, not assumed. If the sum stays
   below 1.5× R1b's front (1.66 h) it is approved; above that, he wants to see it first. The
   retrain and replicate arms stay out without a new approved. The record states by assertion what
   was re-measured and what came from the committed prefix.
2. **Tolerance:** fill the slot before any Phase 37 record, R1a's included. The tolerances are
   k 0, target 0, non-targets 0, and destroyed_pct = MARGIN_K × the dialogue floor ÷ the
   pre-erasure on−off gap, in percentage points ("show the arithmetic"). "Replicated" means all
   four within tolerance. Draw bit-identity is reported as description. If the replica fails:
   a write-once NOT_REPLICATED record with the per-fact deltas against the 0.148 floor as context,
   one attempt, and root-cause investigation before any new run.
3. **Defect E:** one named function that imports the pin unedited, is proved on the committed
   curve and re-sweep, and is used by R1b's re-derivation. It is the ERASE-08 wrapper that Phase 41
   imports, with a natural-red test.
4. **R1a:** asserts and exits 0 or with an error, AND writes a write-once `results/phase37_*`
   record (the four numbers, the input SHA-256s, the commit). The record is committed after
   approved. A divergence means STOP and report, never adjust.

**Premises measured by Claude Code before accepting:**
- The cost "7 to 12 min" was corrected. One sweep takes 6.2–7.0 min (curve 6.959). The 12.29 min
  re-sweep record was two sweeps (|R| = 8: 6.155, |R| = 6: 6.133). The sum 68.584 + 6.959 min =
  1.259 h < 1.662 h, so the approval condition holds.
- The tolerance arithmetic: 2 × 0.005214448168350039 / 1.2420966625043919 × 100 =
  0.8396203493271365 pp. The units are consistent (|ΔPPL| over a PPL gap).
- "The re-sweep of 6 candidates" was corrected. The published re-sweep has two runs: |R| = 8 gives
  k = 78 (its prefix is identical to the committed curve's, verified) and |R| = 6 gives k = 120.

---

## Prefix divergence in R1b

| Option | Description | Selected |
|--------|-------------|----------|
| Re-measured prefix (Recommended) | The erased arm runs on the re-measured prefix; the committed one is the comparator | |
| Always the committed prefix | The sweep only checks k; the arm runs on the committed 78 | |
| Stop if it diverges | The arm does not run; NOT_REPLICATED with only k; root cause first | ✓ (with refinement) |

**User's choice:** Option 3, with a distinction:
- if k = 78 and the SET of the 78 ablated addresses equals the committed set, the arm runs even
  when the internal order differs, and the number of positions that moved is recorded as
  description, "porque o adaptador ablado é o mesmo";
- if k ≠ 78 or the set differs, the arm does not run. The NOT_REPLICATED record holds only k and
  the set difference, a root-cause investigation comes first, and a new run needs approved.

**Premise measured:** `ablate_components` (`phase19_erasure.py:275-324`) zeros both factors of
each address on clones and refuses duplicates, so the same set gives bit-identical weights in any
order. The premise holds.

---

## Claude's Discretion

- Record and file names under `results/phase37_*`, and the module layout.
- Which list order the arm receives in the set-equal case (the re-measured list is preferred).
- The `kind` labels for the three zero tolerances, surfaced in the plan.

## Deferred Ideas

- The retrain and replicate arms in the replica (a new approved is needed).
