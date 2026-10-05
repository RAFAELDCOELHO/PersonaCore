---
phase: 39-instrument-context-2-2
reviewed: 2026-10-05T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase39_prereg.py
  - tests/test_phase39_prereg.py
findings:
  critical: 0
  warning: 1
  info: 5
  total: 6
status: issues_found
---

# Phase 39: Code Review Report, second pass (the 39-REVIEW Resolution fixes)

**Reviewed:** 2026-10-05
**Depth:** standard
**Files Reviewed:** 2 (`git diff cf51309..f0e6560`, 8 fix commits)
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

**Baseline.** `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_phase39_prereg.py`
printed `67 passed in 13.67s`. Running ruff check and ruff format --check on both files printed
`All checks passed!` and `2 files already formatted`. `git ls-files 'results/phase39_*' | wc -l`
printed `0`.

**No BLOCKER under Rafael's rule.** On the committed data, no read value, status, class or count
changed from cf51309 except where rulings e and f require it. Each check is below. Experiment
scripts are in the session scratchpad. `old39.py` is `git show cf51309:scripts/phase39_prereg.py`
with `_REPO_ROOT` pointed at the repo, loaded as a separate module in its own process.

### 1. Each ruling as written (CONFIRMED, by experiment)

- **e.** `disagreement_of` returns REVERSE_DISAGREEMENT (disagreement False) only for R_a LOST
  with G_q INTACT. It returns NO_DISAGREEMENT only when `r_a == g_q`. `_tally` counts REVERSE
  apart in `reverse_disagreement_cells`, and it never enters `disagreement_by_class` or a
  sufficiency class. I compared the old and new `_precedence` over all 256 status combinations:
  ```
  precedence combos differing: 16 of 256
   distinct (R_a,G_q) among diffs: [('LOST', 'INTACT')]
   new classes among diffs: ['{"class": "REVERSE_DISAGREEMENT", "disagreement": false}']  old: ['{"class": "NO_DISAGREEMENT", "disagreement": false}']
  ```
  The order of the four steps is otherwise unchanged. Mutant check: setting the REVERSE return
  back to NO_DISAGREEMENT gives `MUTANT KILLED`, failing at
  `assert phase39_prereg.disagreement_of(r_a, g_q) == {...}`. A no-op control mutant gives
  `18 passed ... MUTANT SURVIVED`, so the harness itself is sound.
- **f.** Under both events, `cells(event)` is `CELL_READINGS x SLOTS`, which is 48 cells, and it
  never includes k0. `cell_spec` refuses k0 and adapter_off under either event (tested). The k0
  statuses come out through `baseline_table`. Old and new cells on committed data:
  `old cells 104 new cells 96`. The only cells in the old set and not the new one are the 8
  `collapse|k0|*` cells. No common cell changed.
- **g.** `class_counts` returns `combined`, `prefixes` and `M2` tallies plus `m2_label`
  ("another training ... damage reference is the taught adapter's k0"). The IN-01 fix is present:
  `undecided_cells` and `undecided_by_class` (disagreement None) are published apart from the
  step-3 WR-01 outcomes. The test proves that prefixes plus M2 partition the combined tally.
- **j.** `tie_audit` covers every damage cell, M2 included, over R_q, G_a (n = 1) and G_q. For
  each cell it gives `class_committed` and `class_exact`; it also lists `flips`, `exact_ties` and
  `class_changes`. The main counts come from `cell["class"]`, the committed formula. `tie_audit`
  re-proves that class. Mutants killed: `>=` in the exact branch, and the exact class computed
  without substituting the exact statuses.
- **WR-01.** On committed data:
  ```
  totals: {'core_taught': (105, 112), 'core_held_out': (92, 104)}
  whole-file matches (no section filter): [(40, ('92', '104')), (77, ('105', '112'))]
  passed True target row {'count': 27, 'n_questions': 27, 'committed': 27, 'equal': True, 'independent': True, 'source': 'results/phase18_extraction_report.md sha256 f24795f3...: the A2 adapter-on rung-48 totals (core_taught 105/112, core_held_out 92/104) minus the seven non-target committed k0 counts'}
  ```
  Even without the section filter, the regex matches only lines 40 and 77, which are the A2
  adapter-on rung-48 rows. It does not match:
  - A1/A3 rows (`A2` is literal);
  - adapter-off rows (`adapter-on` is literal);
  - rungs 1/4/16 (`\| 48 \|`);
  - the "Cumulative by Attempt" rows at :103 and :111, which have a different shape.

  A taught/held-out mix-up cannot change the target, because only the sum is used, and the label
  in the `source` text comes from each tier's own section. The fallback
  `"independent": False` with a reason is tested. A mismatched digest is a SystemExit. Mutants
  killed: returning `committed_k0[target]` in place of `total - others`, and dropping the
  row-note update.
- **WR-03.** The tie audit includes M2 and n = 1, as confirmed in j above. On the committed G_q
  over all 48 damage cells:
  ```
  differs [('k8','pet_name'), ('k8','hometown'), ('k16','pet_name'), ('k16','sibling_name'), ('k16','hometown'), ('k16','street'), ('k32','person_name'), ('M2','hometown'), ('M2','house_number')]
  flips []
  exact_ties [('k8', 'person_name')]
  ```
  The prefix cells agree field by field with `phase38_prereg.drop_formula_audit`, which is
  tested.

### 2. Regressions (none found on committed data)

- **Constants.** Old and new constants are equal: `consts equal: True`. That covers
  `E6_PROJECTION_HOURS`, the actual-gate projection, the stop, the three NLL counts, N_ENTRIES
  and MARGIN. The IN-04 rewrite of `GATE_EXTRA_NLLS_PRICED` gives the same value.
- **gate2 and committed counts.** The count, committed and equal fields of every gate2 row, and
  `committed_a2_counts()`, are byte-identical between the old and new modules:
  `gate2 count/committed/equal + committed_a2_counts identical old vs new`.
- **Margin.** The comparison is still strict `>` against `MARGIN` in `count_status` and
  `damage_reachable`, with the same term order.
- **Renamed constants.** `CLASSIFIED_READINGS`, `DAMAGE_READINGS`, `count_status(reference=)` and
  `classify_cell(statuses)` have no remaining reference in `scripts/` or `tests/`. The planning
  artifacts still reference them; see WR-01.
- **Tests.** No test was deleted. One was renamed, and 14 were added.

### 3. Quotes are byte-equal (CONFIRMED)

```
cf51309 items abcdefghij bytes-equal: True
HEAD items abcdefghij bytes-equal: True
source NFC: True
{'e': True, 'f': True, 'g': True, 'h': True, 'i': True, 'j': True}
run_shape a True / anchor_generation b True / predicted_hit_rate c True / taught_suffix_nll d True
```

### 4. Tests once results/phase39_* lands (no flip or false-green found)

- The ancestry, first-add and RECORDS_AT_COMMIT tests read git history only.
- `_review_quotes` is pinned at cf51309.
- The new WR-01 tests depend on `PHASE18_REPORT_SHA256`, not on any phase39 record. A change to
  that report fails loudly; it does not pass silently (IN-01).

### Ruling i: the numbers to show Rafael, computed by function on committed data

R_a and G_q are the only committed readings, so steps 1 and 2 are decided. Steps 3 and 4 need
the run.

| event | group | cells | published disagreement | NO_DISAGREEMENT | REVERSE_DISAGREEMENT | undecided |
|---|---|---|---|---|---|---|
| collapse | prefixes | 40 | 9 | 31 | 0 | 0 |
| collapse | M2 | 8 | 0 | 8 | 0 | 0 |
| collapse | combined | 48 | 9 | 39 | 0 | 0 |
| damage | prefixes | 40 | 24 | 16 | 0 | 0 |
| damage | M2 | 8 | 0 | 8 | 0 | 0 |
| damage | combined | 48 | 24 | 24 | 0 | 0 |

The disagreement sets are exactly the pinned `_DAMAGE_CELLS` (24) and `_COLLAPSE_CELLS` (9).

## Warnings

### WR-01: The driver plans still consume the interface this diff removed, and do not mention the new one

**File:** `.planning/phases/39-instrument-context-2-2/39-06-PLAN.md:17-18, 65, 115, 120, 131, 133`;
`39-07-PLAN.md:75` (outside the reviewed files; this is the stale-reference check)
**Issue:** 39-06's interfaces and tasks call `CLASSIFIED_READINGS`, `DAMAGE_READINGS`,
`classify_cell(statuses)` and bare `count_status` per reading. They classify collapse over
`CLASSIFIED_READINGS x slots`, which includes k0. They also hand-build a `_drop_audit` that
duplicates the frozen `tie_audit`.

Across 39-06..39-10, `REVERSE`, `baseline_table`, `tie_audit` and `cell_spec` have zero
mentions: `grep -n "REVERSE\|baseline_table\|tie_audit\|cell_spec" 39-0[6-9]-PLAN.md 39-10-PLAN.md | wc -l`
printed `0`. Running 39-06 as written fails with AttributeError. A "repair" that re-creates
`CLASSIFIED_READINGS` in the driver would put the 8 k0 collapse cells back (contrary to ruling
f). A driver that classifies from bare statuses outside the door would also be free to
re-implement step 2 without REVERSE_DISAGREEMENT. Either would change the emitted counts in the
real fill. That makes it a BLOCKER for 39-06's execution, but not for the reviewed code.
**Fix:** Before 39-06 executes, revise its interfaces to the frozen door:
- `cells(event)` with `classify_cell(cell, values, k0)`;
- `baseline_table(k0_by_slot)`;
- `class_counts(classified)` per event, reading `combined`, `prefixes`, `M2`,
  `reverse_disagreement_cells` and `undecided_*`;
- `tie_audit(damage_classified)` in place of the driver's `_drop_audit`.

Also update 39-07's report headings so they include REVERSE_DISAGREEMENT, the k0 baseline table
and the M2 split.

## Info

### IN-01: The SHA pin on a report that has a writer and a history of continuations makes gate 2 SystemExit rather than fall back

**File:** `scripts/phase39_prereg.py:339-340, 999-1003`
**Issue:** `results/phase18_extraction_report.md` has 5 commits, several of them dated
continuations. `scripts/phase18_extraction.py:3913` also writes it. Any later append or
regeneration makes `report_k0_totals` raise a SystemExit, so gate 2 stops the E6 run. The ruled
`"independent": False` row is never emitted in that case. Refusing on a mismatch is consistent
with the ruling ("SHA fixado"), so this is not a defect.
**Fix:** None is needed if a refusal is the intent. Otherwise, read the pinned blob with
`git show <commit>:results/phase18_extraction_report.md`, so that appends do not break the pin.

### IN-02: `class_counts` and `baseline_table` do not prove completeness

**File:** `scripts/phase39_prereg.py:1341-1357, 1460-1477`
**Issue:** `class_counts` accepts any subset of the 48 door cells, which the rehearsal slice
needs. `baseline_table` accepts any non-empty subset of the readings per slot. Confirmed:
`baseline partial accepted: ['G_q']`. A driver that drops a slot or reading publishes smaller
counts without noticing. This is deliberate-bypass class.
**Fix:** Have the driver prove `len(classified) == len(cells(event))` and that every baseline
slot carries all four readings on the real run.

### IN-03: `_door` is key-order sensitive

**File:** `scripts/phase39_prereg.py:1290-1299`
**Issue:** A cell round-tripped through `json.dumps(..., sort_keys=True)` has the same content
but is refused. Confirmed:
`SystemExit: [phase39_prereg] a cell has exactly the fields ('event', 'reading', 'slot', 'n', 'referenc...`.
`class_counts` and `tie_audit` re-key the cell, so they are unaffected. Only direct calls to
`classify_cell` and `cell_statuses` with a re-read cell fail, and they fail loudly.
**Fix:** Compare `set(cell) == set(_CELL_FIELDS)`, or document that cells must come straight
from `cells()`.

### IN-04: The committed-data oracle pins the disagreement sets but not ruling i's other counts

**File:** `tests/test_phase39_prereg.py:1382-1397`
**Issue:** On committed data, REVERSE_DISAGREEMENT = 0, undecided = 0, NO_DISAGREEMENT = 39
(collapse) and 24 (damage), and M2 has 0 disagreement. None of these is asserted.
**Fix:** Extend the oracle with `disagreement_of(...)` and assert the table above.

### IN-05: No entry's `source` names 39-REVIEW.md

**File:** `scripts/phase39_prereg.py:607, 655, 684-700, 745-747, 776-778, 831`
**Issue:** The derivations say "confirmed by Rafael 2026-10-05" or "ruled by Rafael 2026-10-05",
but no `source` field cites the file that holds the rulings. Only the comment at :420 does.
Confirmed: `ruling-text mentions in sources: []`.
**Fix:** Append `39-REVIEW.md Resolution (cf51309)` to the sources of the entries that quote
rulings a-j or WR-01.

---

_Reviewed: 2026-10-05_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
