---
phase: 39-instrument-context-2-2
reviewed: 2026-10-04T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase39_prereg.py
  - tests/test_phase39_prereg.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 39: Code Review Report

**Reviewed:** 2026-10-04
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

I reviewed `scripts/phase39_prereg.py` (diff base f21b1b4) and `tests/test_phase39_prereg.py`
against 39-CONTEXT D-01..D-30a, plans 39-01/39-02 and the frozen `phase38_prereg` definitions.
Baseline: `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase39_prereg.py` printed
`54 passed in 5.43s`, and ruff check and format are clean.

**No BLOCKER under the developer's rule.** I found no defect that changes a read value or an
emitted verdict or class on the committed data or in a real fill. What each requested check found:

1. **Precedence.** `classify_cell` matches the four steps of
   `ENTRIES["e6_decomposition_rule"]["precedence"]` exactly. `_wr01` iterates
   `WR01_OUTCOMES = (UNREACHABLE_AT_SIZE, ALREADY_AT_K0)`, so UNREACHABLE_AT_SIZE comes first in
   step 1 (R_a, G_q) and in step 3 (R_q, G_a). Step 1 returns disagreement None, step 2 False and
   steps 3-4 True. Step 4's else branch is reachable only when R_q and G_a are both INTACT.
   `test_classify_cell_exhaustive` plus the named cases kill the order-swap mutants.
2. **Damage.** `count_status` uses `count_k0 / n - count_k / n > MARGIN`, strict, with the same
   term order as `phase38_prereg.first_damage`. `damage_reachable` is the same formula with a post
   count of 0 and gives 9 at n = 27 and 1 at n = 1. The tests pin the person_name k8 exact tie and
   the four drops that rounding decides, (15,7), (17,9), (19,11) and (21,13).
3. **Readings.** `CLASSIFIED_READINGS` is k0..k78 plus M2. `DAMAGE_READINGS` drops k0.
   adapter_off is only in `DESCRIPTIVE_READINGS`. A k0 collapse cell can only be INTACT or
   ALREADY_AT_K0, so it never disagrees. The constants are correct, but no function enforces
   them (WR-02).
4. **Wilson bounds.** Both bounds use `erasure_gate._Z_ONE_SIDED_95` (the lower bound inherits
   it by reference), so "together a 90% two-sided interval" is correct. The rate is
   `successes / n`.
5. **Computed, not typed.** The projection and stop hours, the NLL counts and N_ENTRIES are
   computed at import, and `e6_projection_hours(7, 7)` reproduces `front_hours.E6` bit for bit.
   The literal scan that guards this has a gap (WR-05).
6. **After records land.** The ancestry, first-add, verbatim-ruling and HEAD-sha tests stay
   honest once `results/phase39_*` records are committed. None of them reads a phase39 record.
   The only test pinned to transient text is
   `assert "plan-03 review" in filled["derivation"]`, which plan 03 must edit together with the
   prereg (WR-04).

## Warnings

### WR-01: Gate 2's k0 row for the erasure target (pet_name) compares `_pooled_rows` with itself

**File:** `scripts/phase39_prereg.py:845-846, 874-886` (plus `phase38_prereg.a2_counts`, :911-918)
**Issue:** `committed_a2_counts()` takes k0 from `phase38_prereg.a2_counts()`. That function
re-derives k0 by running `phase19_run._pooled_rows` over `results/phase18_arm_adapter-on.json`.
`gate2()` re-derives k0 by running the same function over the same file.

- For the 7 non-target slots, `a2_counts` checks `pre_answerable` and would SystemExit on a
  mismatch.
- For the target slot pet_name, nothing independent is compared. The row prints
  `equal: True` but could never have been False.

pet_name's k0 count is the damage reference for every pet_name G_q cell. D-19 says gate 2
"re-derives ... the committed A2 counts", but for this cell it only re-runs the same derivation.
Only the test's typed `_A2_COUNTS` table catches a change in the scorer. The live gate in the
driver does not.

**Confirmed** (I shifted the k0 adapter-on scorer output for pet_name by -5; the gate still
passed):
```
.venv/bin/python scratchpad/k0_selfcmp.py
target slot: pet_name
passed: True k0 pet_name {'count': 22, 'n_questions': 27, 'committed': 22, 'equal': True}
```
**Fix:** Pick one of these:
- Compare the k0 target count against an independent committed figure. One option is the
  phase18 report's A2 adapter-on totals at k = 48, taught /112 and held-out /104, which should
  sum to the k0 total of 197.
- Mark the row non-independent in the gate output, for example
  `"independent": False, "note": "k0 target: same scorer, same file (SHA-pinned only)"`, so the
  record does not claim a check that was never made.

### WR-02: Which (reading, event, n, reference) makes a cell is not frozen; `reference=` is opt-in

**File:** `scripts/phase39_prereg.py:974-991, 999-1029`
**Issue:** The frozen functions take bare statuses and counts. Nothing in the prereg maps each
reading to its count source, its n (27 for R_q/G_q, 1 for G_a) and its k0 reference, or refuses
a reading outside the classified set. As a result, the driver (not yet frozen) can:
- classify adapter_off;
- score k0 as a damage cell by omitting `reference=True`, and get INTACT;
- pass a wrong n.

Rule elements that CTX-03 says are "computed only through frozen definitions" therefore end up
in unfrozen code.

**Confirmed:**
```
.venv/bin/python -c "...; print(p.count_status('damage', 26, 26, 27)); print(p.classify_cell({... adapter_off person_name ...}))"
k0 as damage cell w/o reference flag: INTACT
adapter_off classified (collapse, person_name): {'class': 'NO_DISAGREEMENT', 'disagreement': False}
```
**Fix:** Add one pure door that the driver must use, for example:
```python
N_QUESTIONS = N_ENTRIES // len(SLOTS)  # derived: 27
_N = {"R_q": N_QUESTIONS, "G_q": N_QUESTIONS, "G_a": 1}

def classify_reading(event, reading, *, rank, rank_k0, n1, n1_k0, unit, unit_k0, count, count_k0):
    readings = CLASSIFIED_READINGS if event == "collapse" else DAMAGE_READINGS
    _prove(reading in readings, f"{reading} is not a {event} cell (D-11 i / D-25)")
    ref = reading == REFERENCE_READING
    return classify_cell({
        "R_a": rank_status(rank, rank_k0),
        "R_q": count_status(event, n1, n1_k0, _N["R_q"], reference=ref),
        "G_a": count_status(event, unit, unit_k0, _N["G_a"], reference=ref),
        "G_q": count_status(event, count, count_k0, _N["G_q"], reference=ref),
    })
```
Add a test that refuses `adapter_off` under either event and refuses `k0` under damage.

### WR-03: D-33's "named in the record and report" has no frozen implementation, and the obvious reuse skips M2 and n = 1

**File:** `scripts/phase39_prereg.py:453-458` (the `ties` text)
**Issue:** The frozen rule requires every margin tie decided by rounding to be named. That means
every cell where `pre/n - post/n` and `(pre - post)/n` decide damage differently, plus every
exact tie, over R_q n1, G_a and G_q. No prereg function computes this. The audit is left to plans
06/07.

The ready-made `phase38_prereg.drop_formula_audit(a2)` iterates `PREFIXES[1:]` only and expects
`a2[slot]["counts"][k]`. It cannot see M2, which is a damage reading here, and it was never
exercised at n = 1. The audit is descriptive, so no class changes. However, a driver that reuses
the Phase 38 audit would silently omit the M2 cells the frozen text says are named.

**Confirmed:**
```
.venv/bin/python -c "...; a=q.drop_formula_audit(q.a2_counts()); print(len(a['cells']), sorted({c['k'] for c in a['cells']}))"
phase38 audit cells: 40 ks: [8, 16, 32, 64, 78]
```
**Fix:** Add a pure `drop_audit(count_k, count_k0, n)` beside `count_status`, returning
`rate_drop`, `count_drop`, `flip` and `exact_margin_tie` for one cell. The driver then calls it on
every DAMAGE_READINGS cell of R_q, G_a and G_q, M2 included. Test it on the four n = 27 flips and
on (18, 26).

### WR-04: The precedence step order is explicitly unconfirmed, but the entry lacks the unconfirmed label

**File:** `scripts/phase39_prereg.py:479-482`; `tests/test_phase39_prereg.py:273-278, 323, 353-355`
**Issue:** The `e6_decomposition_rule` derivation says the step order of 'precedence' and the
absence of k0 damage cells "are the planner's reading of D-25, to be confirmed at the plan-03
review". The step order does change classes for cells with a WR-01 status. For example, R_a
LOST with R_q ALREADY_AT_K0 is NO_DISAGREEMENT under step 2-before-3, while an "any WR-01 status
wins" reading would make it ALREADY_AT_K0. It also changes how `by_class` splits.

Even so, the entry is not in `_UNCONFIRMED`. `test_preferences_are_labelled` asserts that
`_DEFAULT_LABEL` is absent from it, so the label census reports a planner reading as confirmed.
Line 323 also pins the transient phrase "plan-03 review".

**Confirmed:**
```
.venv/bin/python -c "...; d=p.ENTRIES['e6_decomposition_rule']['derivation']; print('to be confirmed at the plan-03 review' in d, 'default taken at plan time, not yet confirmed by Rafael' in d)"
unconfirmed phrase present: True | canonical default label present: False
```
**Fix:**
1. Plan 39-03 should put the step order and "k0 has no damage cell" to Rafael as an explicit
   ruling before D-27 freezes the file.
2. Until he rules, add `"e6_decomposition_rule": "D-25"` to `_UNCONFIRMED` and use `_DEFAULT` in
   the derivation, so the census sees the label.
3. Once he rules, replace both the label and line 323's pinned phrase with the dated ruling.

### WR-05: The "nothing derived is typed" scan does not seed the D-11/D-26 projections or the NLL counts

**File:** `tests/test_phase39_prereg.py:456-479`
**Issue:** The seeds and floats are 216, 48, 9, 12096, 512, 448 plus the d30 projections, the
stop, MARGIN, `front_hours.E6` and `e5_nll_high`. They omit:
- the `projection_steps` values d11 (0.7030772649827931) and d26 (0.7227090186770592), which
  CONTEXT D-26 says are "computed in the prereg, never typed";
- 10584 (D-11's priced minted NLLs);
- 56 (the reference total) and 27 (questions per slot).

Typing any of these into the prereg passes the guard, which is a false-green gap for check (5).

**Confirmed:**
```
.venv/bin/python -c "...plant each line into the prereg source and run _literal_failures..."
'X = 0.7227090186770592' NOT flagged
'X = 0.7030772649827931' NOT flagged
'X = 10584' NOT flagged
'X = 56' NOT flagged
'X = 27' NOT flagged
```
**Fix:** Add `steps["d11"]` and `steps["d26"]` from `approval_block()["projection_steps"]` to
`floats`. Add `7 * 216 * 7` (computed as `COMMITTED_ADAPTER_CAP * N_ENTRIES * (MINTED_SET_SIZE - 1)`)
and `phase39_prereg._reference_total()` to `seeds`. Small ints such as 27 may collide with prose
numbers; add 27 only if the scan tolerates it.

## Info

### IN-01: `by_class` merges step-1 and step-3 WR-01 outcomes; k0 collapse cells are always non-disagreeing

**File:** `scripts/phase39_prereg.py:1032-1048`
**Issue:** `by_class["UNREACHABLE_AT_SIZE"]` counts both undecided cells (step 1, disagreement
None) and disagreement cells excluded at step 3. Confirmed: two such cells give
`by_class['UNREACHABLE_AT_SIZE'] == 2`. The split is recoverable only by subtracting
`disagreement_by_class`. Separately, the 8 k0 collapse cells can only be NO_DISAGREEMENT or a
WR-01 outcome, so they inflate `cells`.
**Fix:** Publish `undecided_by_class` (disagreement None) explicitly, and state in the record
that k0 collapse cells cannot disagree.

### IN-02: Input guards are SystemExit-free at n = 0 and accept non-integer counts and ranks

**File:** `scripts/phase39_prereg.py:894-922, 959-991, 1062-1065`
**Issue:**
- `draw_rate(0, 0)`, `count_status('damage', 0, 0, 0)` and `rank_of_mean_nll({'t': []}, 't', ())`
  raise ZeroDivisionError rather than `[phase39_prereg]` SystemExit.
- `count_status` and `rank_status` accept floats, so a rate passed as a count is silently
  classified. Confirmed: `count_status('damage', 0.5, 1, 1)` returns LOST and `rank_status(1.5, 1)`
  returns LOST.
- `unit_of` accepts 47 draws, whereas D-07 says "some hit in K draws".

**Fix:** Add `_prove(n >= 1)`, plus integer non-bool checks (`phase35_prereg._prove_count`
style) on counts and ranks. Add `_prove(len(hits) == K)` in `unit_of`.

### IN-03: The D-28 seed-window test is tautological

**File:** `tests/test_phase39_prereg.py:832-845`
**Issue:** Both sides reduce to `SEED + i*K + j`, given `anchor_seed_index(slot) == i*K`, which is
already tested at :825. The test does not exercise how `phase18_extraction` passes
`entry["seed_index"] * K` to `draw_all` (it does, at :3182/:3640), and it does not check stage_e6.
**Fix:** Assert against the call site instead. For example, AST-check that phase18_extraction's
`draw_all` calls pass `entry["seed_index"] * K`, or check that the probe record's configuration
matches.

### IN-04: Typed duplicates and stale header text

**File:** `scripts/phase39_prereg.py:10-11, 360-365, 224`
**Issue:**
- `approval_block()["untouched"]` types `"results/phase36_budget.json"`, which is
  `BUDGET_RECORD`, and `"ledger/v6_mps_ledger.jsonl"`, which is `phase36_ledger.LEDGER_PATH`.
- The module docstring says the 39-02 functions are in "section 9", but the classifier is in
  section 10.
- `GATE_EXTRA_NLLS_PRICED` prices candidates per slot through `MINTED_SET_SIZE`, which is the
  same budget field under a different name.

**Fix:** Reference the owning constants, update the docstring, and use
`_BUDGET["unit_prices"]["e5_candidates_per_slot_max"]` in the gate price for readability.

---

_Reviewed: 2026-10-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
