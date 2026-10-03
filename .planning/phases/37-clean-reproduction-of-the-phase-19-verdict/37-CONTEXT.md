# Phase 37: Clean Reproduction of the Phase 19 Verdict - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Two deliverables, published beside the v3.0 FAILURE verdict and never over it:

- **R1a (CPU, REPRO-01/02).** One command re-derives the Phase 19 verdict from the committed
  records. It imports the pin and the gate and asserts exactly:
  - k = 78;
  - target 0/27;
  - 7/7 non-targets beyond 0.2962962962962963;
  - 77.6370113463966% of the adaptation destroyed.

  Each of defects A–E is routed by a named function.
- **R1b (MPS, REPRO-03).** A replica of k = 78 on the M3, run under a tolerance and a definition of
  "replicated" that are filled into the Phase 35 slot before any Phase 37 record exists.

Requirements: REPRO-01, REPRO-02, REPRO-03.

Out of scope: the Phase 19 retrain and replicate arms (they do not run without a new "approved"
from Rafael), and any edit to `scripts/phase19_erasure.py` or `scripts/erasure_gate.py`.

</domain>

<decisions>
## Implementation Decisions

### Ordering and the slot (REPRO-03)
- **D-01:** Phase 37's own ancestry-guarded pre-registration module fills
  `phase35_prereg.fill("r1b_tolerance_and_replicated", ...)`. It is committed before ANY Phase 37
  record, including R1a's. There are two records, R1a's and R1b's, both under
  `results/phase37_*`, which is the path Phase 35 reserved.

### Tolerance and the definition of "replicated" (REPRO-03)
- **D-02:** The tolerances, one per key of `R1A_ASSERTIONS`:
  - `k`: **0**.
  - `target_correct` (0/27): **0**.
  - `nontargets_beyond_margin` (7/7): **0**.
  - `destroyed_pct`: **derived, not chosen**. It is
    MARGIN_K × the published dialogue noise floor ÷ the pre-erasure on−off gap, × 100, in
    percentage points. The arithmetic, read from committed records and never typed:
    - `MARGIN_K` = 2 (`erasure_gate.py:86`, imported via `phase35_prereg.MARGIN_K`);
    - floor = `results/phase19_noise_floors.json::dialogue_ppl_noise_floor.value` =
      0.005214448168350039 (|ΔPPL|);
    - g0 = `phase19_arm_erased.json::pre_erasure.dialogue_ppl` adapter_on − adapter_off =
      5.815445876712191 − 4.573349214207799 = 1.2420966625043919;
    - tolerance = 2 × 0.005214448168350039 / 1.2420966625043919 × 100 ≈ **0.8396203493271365 pp**.

    The derivation is shown in the module. `kind = derived` for `destroyed_pct`. The three zeros
    are Rafael's ruling and get labelled honestly under PREREG-06 (see Claude's Discretion).
- **D-03:** **"Replicated"** means all four assertions fall within the D-02 tolerances.
  - Bit-identity of the draws against the committed `phase19_arm_erased.json` is reported beside
    the result, as yes or no plus the count of differing draws. It is description, never a
    criterion.
- **D-04:** **If the replica does not replicate:**
  - a write-once `NOT_REPLICATED` record is published beside the v3.0 verdict, and the verdict does
    not change;
  - the record carries the per-fact non-target deltas compared with the 0.14814814814814814 floor
    (`nontarget_noise_floor.value`) as context;
  - there is one attempt only. Any new run needs Rafael's "approved", and a root-cause
    investigation comes first.

### What R1b runs (REPRO-03)
- **D-05:** R1b re-derives the prefix and then runs the erased arm at K = 48:
  - It redoes the selection sweep (ordering and stopping rule) through the defect-E routing (D-08),
    so that k = 78 is MEASURED, not assumed.
  - It then runs the erased arm at K = 48.
  - The record says, by assertion, what was re-measured and what came from the committed prefix.
- **D-06:** Cost, measured from the records:
  - erased arm 68.584 min (`phase19_arm_erased.json::config.wall_clock_min`) + sweep 6.959 min
    (`phase19_collateral_curve.json::wall_clock_min`) = **1.259 h**;
  - the R1b front is 1.108 h (`phase36_budget.json::front_hours.R1b`), and 1.5× that is 1.662 h;
  - 1.259 h < 1.662 h, so Rafael's conditional approval covers the sweep. If the plan's sum ever
    exceeds 1.662 h, it goes to Rafael BEFORE launch.

  One sweep costs 6.2–7.0 min. The 12.29 min in `phase19_reference_set_resweep.json` was TWO
  sweeps (|R| = 8 and |R| = 6). The retrain arm (46.6 min) and the replicate arm (45.3 min) stay
  out of scope.
- **D-07:** **If the re-measured prefix differs from the committed one:**
  - **k = 78 and the SET of the 78 ablated addresses equals the committed set:** the erased arm
    runs even if the internal order differs. The order difference (how many positions moved) is
    recorded as description.
    - Verified: `ablate_components` (`phase19_erasure.py:275-324`) zeros both factors of each
      address on clones and refuses duplicates.
    - So the same set gives bit-identical weights whatever the order.
  - **k ≠ 78 or the set differs:** the erased arm does NOT run.
    - A `NOT_REPLICATED` record is written with only the k and the set difference.
    - A root-cause investigation comes before anything else.
    - A new run needs only Rafael's "approved".

### Defect E (REPRO-02, ERASE-08)
- **D-08:** Defect E is routed by ONE named function:
  - It imports the pin without editing it and selects `phase18_extraction.reference_set_for`
    (|R| = 8) instead of the pin's `reference_set_for_calibration` (|R| = 6) inside
    `_selected_components`' path.
  - It is proved on the committed records: the curve (`reference_set_size` 8, k = 78) and the
    published re-sweep (|R| = 8 gives k = 78 with a prefix identical to the committed one; |R| = 6
    gives k = 120).
  - It is the function R1b's re-derivation (D-05) uses.
  - It IS the ERASE-08 wrapper. Phase 41 imports this function and does not write another.
  - A test proves `scripts/phase19_erasure.py` byte-unchanged.
- **D-09:** Every one of A–E has a named routing function, and removing any routing turns a test
  red. The red must be natural, not planted:
  - A: on-disk `zero_results_have_nll` False vs order-normalised True;
  - B: the pin's `_calibration_rate()` gives 0.8846…, which yields the `ceiling` floor 0.2 instead
    of `TARGET_FLOOR`;
  - C: the committed `per_fact` reads 14, not the pooled 27;
  - D: `[ppl, n]` raises a `TypeError` in the gate;
  - E: without the routing, the reference set has 6 members, not 8.

### R1a's output (REPRO-01)
- **D-10:** One command asserts and exits 0 or with an error. It ALSO writes a write-once record
  `results/phase37_*` holding:
  - the four re-derived numbers;
  - the SHA-256 of every input record;
  - the commit.

  The record is committed only after Rafael's "approved". A divergence in any number means STOP
  and report, never adjust to match.

### Claude's Discretion
- File and record names inside `results/phase37_*`, for example `phase37_r1a.json` and
  `phase37_r1b.json`.
- The module layout: the Phase 37 prereg module, the routing module and the drivers. Reuse
  `phase19_run.report()`'s existing A–D routing (`scripts/phase19_run.py:2771`) rather than
  re-implementing it, and never write a `results/phase19_*` path.
- Which list order the erased arm receives under D-07's set-equal case. The re-measured list is
  preferred, so the arm sits downstream of the measurement, and the weights are identical either
  way.
- The `kind` labels for D-02's three zero tolerances (`preference` per PREREG-06, unless the
  planner writes a derivation for them). They must be labelled honestly and surfaced in the plan.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` — REPRO-01..03 (lines ~715-717); ERASE-08 (line ~742, the Phase 41
  consumer of D-08's wrapper)
- `.planning/ROADMAP.md` — the Phase 37 block (~1599), the v6.0 ordering/approvals paragraph (~1450),
  and Phase 41 SC3 (~1717)

### Phase 35 / 36 pins this phase fills or consumes
- `scripts/phase35_prereg.py` — `R1A_ASSERTIONS` (:453), `r1a_rederive()` (:463),
  `e1_condition_b_margin()` (:434), `_rule_r1b_tolerance_and_replicated` (:1191), the
  `r1b_tolerance_and_replicated` slot (:1798), `fill()` (:1882), the `results/phase37_*` path (:320)
- `.planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-CONTEXT.md` — D-01/D-02
  (the core plus the slot registry)
- `.planning/phases/36-mps-cost-probes-and-budget-commitment/36-CONTEXT.md` — D-04 (R1b price), D-06
  (nothing reallocated without "approved"), D-11/D-13 (the ledger every MPS phase calls before launch),
  the Specifics block (R1b scope)
- `results/phase36_budget.json` — `front_hours.R1b` = 1.1081805983679887; `stop_line_hours` 90

### The Phase 19 pin, gate and defects
- `scripts/phase19_erasure.py` — CLOSED pin (byte-unchanged): `ablate_components` (:275),
  `select_ablation_prefix` (:2443), `reference_set_for_calibration` (:3096), `_selected_components` (:3558)
- `scripts/erasure_gate.py` — `MARGIN_K` (:86), `erasure_succeeded`
- `scripts/phase19_run.py` — `report()` (:2771) routes A–D; `_pooled_rows` (:620), `_order_normalised` (:1290)
- `README.md` — the defects A–E table (~:400-418, "four versus five")
- `results/phase19_calibration_correction.json` / `.md` — defects A, B, C
- `results/phase19_erasure_report.md` — defect D
- `results/phase19_reference_set_correction.md`, `results/phase19_reference_set_resweep.json` — defect E
- `.planning/milestones/v3.0-phases/19-selective-memory-erasure/19-15-SUMMARY.md` — the routing table
  for A–D as published

### Records R1a reads / R1b compares against
- `results/phase19_arm_erased.json` (k = 78 prefix, pre/post dialogue PPL, draws, wall_clock 68.584 min)
- `results/phase19_target_scores.json` (0/27, 7/7)
- `results/phase19_collateral_curve.json` (`ordered_prefix` 78, `reference_set_size` 8, 6.959 min)
- `results/phase19_noise_floors.json` (dialogue floor 0.005214448168350039; non-target floor
  0.14814814814814814, margin 0.2962962962962963)

### Precedent
- `scripts/erasure_kstar_prereg.py` (:130-150) / `results/erasure_kstar_summary.json` — MPS curve
  agreement measured at |diff| = 0.0 (tolerance 1e-6), a prior MPS re-run of the same chain

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase19_run.report()`: already routes A, B, C and D on CPU from the committed records. R1a
  should drive the same routing and assert, not render a new Phase 19 report.
- `phase35_prereg.r1a_rederive()`: re-derives k and destroyed_pct. 0/27 and 7/7 need the routed
  path (C).
- `phase19_run target-resweep` / `target-ablate`: the unpinned sweep drivers that produced the
  curve and the re-sweep. R1b's sweep goes through D-08's routing.
- `scripts/erasure_kstar_run.py`: the pattern for a wrapper driver that imports the pin, refuses a
  dirty tree and never writes a Phase 19 path.

### Established Patterns
- Write-once records committed only after Rafael's "approved"; an ancestry-guarded prereg module
  before any record (the phase29/35/36 prereg pattern).
- Pin corrections are dated continuations (`scripts/_addendum.py`); the pin is never edited.
- The Phase 36 ledger is called before every MPS launch.

### Integration Points
- Phase 41 imports D-08's defect-E function (ERASE-08).
- `phase35_prereg.fill` is the only door to the slot.

</code_context>

<specifics>
## Specific Ideas

- The record states by assertion what was re-measured (the ordering, the stopping rule, k, the
  draws) and what was inherited (the committed prefix as the comparator, and the adapter_in
  SHA-256).
- In NOT_REPLICATED, the per-fact deltas are context, compared with 0.148; they are never the
  criterion.

</specifics>

<deferred>
## Deferred Ideas

- The Phase 19 retrain arm (46.6 min) and replicate arm (45.3 min) as part of the replica: not
  run without a new "approved" from Rafael.

</deferred>

<addendum>
## Plan-time rulings (Rafael, 2026-10-03, /gsd-plan-phase 37)

The researcher's four open questions (`37-RESEARCH.md` §Open Questions), answered before planning.
Each one goes into the Phase 37 pre-registration, which must be complete before any
`results/phase37_*` record exists.

- **D-11:** **A started attempt is THE attempt.** Any R1b launch counts as D-04's one attempt,
  including a crash that leaves no record and only a ledger `lost` line. A relaunch needs Rafael's
  "approved", a ledger reconcile and a root-cause note first (the 36-07 W3 pattern).
- **D-12:** **D-04's per-fact non-target deltas.** For each of the 7 non-targets, NOT_REPLICATED
  carries the replica pooled delta, the committed pooled delta, and |replica − committed|, beside
  0.14814814814814814 (`nontarget_noise_floor.value`). They are context and never the criterion.
- **D-13:** **R1a also re-derives the (b) floor from the committed replicate arm**
  (`results/phase19_arm_replicate.json`), the way `phase19_run.report()` does, as one extra
  assertion. It adds that record to the input SHA-256 list. The four REPRO-01 numbers and the
  verdict stay the headline.
- **D-14:** **The re-measured sweep is recorded in BOTH R1b branches.** `ordered[:k]` and the
  curve rows go in REPLICATED and NOT_REPLICATED (D-07) alike, so a root-cause investigation has
  the data. This is description only and refines D-07's "only the k and the set difference": the
  verdict fields stay those two.

### Plan-check rulings (Rafael, 2026-10-03, after checker iteration 2)

- **D-15:** **D-11 governs EVERY relaunch.** A second R1b run of any kind needs Rafael's
  "approved", a ledger reconcile and a root-cause note first. That covers a crash, a completed
  NOT_REPLICATED, and a D-07 divergence (k ≠ 78 or a different set). This supersedes D-07's "A new
  run needs only Rafael's approved".
- **D-16:** **The attempt starts at the ledger start line.** A launch the driver refuses in
  preflight (dirty tree, untracked prereg, failed `require_launch`, wrong device, adapter mismatch)
  happens before the start line and runs nothing on MPS, so it is not an attempt. D-11's "Any R1b
  launch counts" means any launch that has written its start line.
</addendum>

---

*Phase: 37-clean-reproduction-of-the-phase-19-verdict*
*Context gathered: 2026-10-03*
