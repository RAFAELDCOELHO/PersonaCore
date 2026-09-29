---
phase: 29-v5-0-pre-registration-and-carried-debt
reviewed: 2026-09-24T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - scripts/phase29_prereg.py
  - tests/test_phase29_prereg.py
  - tests/test_phase29_debt.py
  - scripts/phase16_persistence.py
  - tests/test_phase16_driver.py
  - tests/test_phase27_relearn.py
findings:
  critical: 1
  warning: 4
  info: 4
  total: 9
status: fixed
fixed_at: 2026-09-24
fix_scope: CR-01, WR-01..WR-04, IN-01 (developer ruling 2026-09-24: "Fix all now"); IN-02..IN-04 skipped
---

# Phase 29: Code Review Report

**Reviewed:** 2026-09-24
**Depth:** standard (diff 820e365..HEAD)
**Files Reviewed:** 6
**Status:** fixed (6 of 9; IN-02..IN-04 skipped by scope)

## Summary

The DEBT changes (the `_blockquote_after` refactor plus `d28_note`, the scratch-repo relearn test, and the Phase-17 frontmatter test) are sound. Ruff check and format both pass.

The defects are in `scripts/phase29_prereg.py`'s admission contract and record builders. This matters because the contract is ancestry-frozen: after Phase 30's first `results/phase3*` commit, any fix needs a dated `_addendum.py` continuation and can no longer be an edit. Anything below should therefore be fixed before Phase 30 lands. Each finding was confirmed with a one-command probe (`.venv/bin/python` against the committed module). The evidence is quoted inline.

## Critical Issues

### CR-01: admission() never checks the leg's own-control reading against the leg's verdicts, so the D-06/D-11/D-12 guarantees are not enforced by the function Phase 33 calls

**File:** `scripts/phase29_prereg.py:440-557` (with `recall_threshold` at 373-384, `_control_readings` at 406-418)
**Issue:** `admission()` checks that `control_readings` holds well-formed `[k, n]` pairs and then uses them only to write reason strings. It never evaluates them:
- `recall_threshold()` implements the D-06/WR-05 threshold ("F_Y x the arm's OWN advr ratio-0 control, never a dp_* reading"). Nothing in the module calls it, including `admission()`.
- D-11/D-12 say a leg whose control is outside (0,1] is REFUSED in full. `admission()` never calls `control_is_unlearnable()` on the stored readings. That allows a record that contradicts its own control counts: a leg with an unlearnable control and FAIL or PASS points, or a fully REFUSED leg whose control is learnable. Such a record is not INCONCLUSIVE. It reads MOOT, ADMITTED or REFUSED.

Evidence: a forged frontier with all 12 points FAIL and `advr_n64` control `taught [1,1008], heldout [0,648]` (the leg is unlearnable, so D-12 requires all 6 n64 points REFUSED). `admission()` returns `MOOT`. Swap one n64 FAIL for PASS and it returns `ADMITTED`. Nothing ties the stored per-point route kwargs (`control_taught_recall`) to the `advr` reading either. So a frontier whose points were graded against a `dp_*` control would still admit. This is the WR-05 failure the module docstring says it prevents.
**Fix:** After step (1c), add a consistency check that returns INCONCLUSIVE when it fails, and use the threshold:
```python
for leg in LEGS:
    t, h = readings[leg]["taught"], readings[leg]["heldout"]
    refused_leg = control_is_unlearnable(*t, *h)
    leg_refused = [strings[k] == REFUSED for k in leg_keys(leg)]
    if refused_leg != all(leg_refused) or (not refused_leg and any(leg_refused)):
        return _inconclusive(f"advr_{leg} control {t}/{h} disagrees with the leg's REFUSED set")
    y, _, _ = recall_threshold(frontier, leg, "advr")
    for k in leg_keys(leg):
        kw = points[k]["verdict"]
        if strings[k] != REFUSED and F_Y * kw.get("control_taught_recall", -1) != y:
            return _inconclusive(f"{k} was graded against a control other than advr_{leg}'s own")
```

**Resolution:** FIXED in 744165b. New admission step (1d), after the tally re-derivation and before ADMITTED: the stored verdicts must re-derive from each leg's OWN advr ratio-0 control, else INCONCLUSIVE (returned, never raised; precedence otherwise unchanged). An unlearnable control (`control_is_unlearnable`) beside any measured (non-REFUSED) point in its leg reads INCONCLUSIVE; every measured point must carry `control_taught_recall`/`control_heldout_recall` equal to the advr control's k/n (taught via `recall_threshold(..., "advr")`, which now has a caller), the control point its own `point_*_recall`, and a REFUSED point is checked on the fields it carries (incl. a D-13 `control_recall_counts`). **Reading chosen:** D-11/D-12 make the whole leg REFUSED, and D-06 says admission reads stored verdicts and decides nothing after the record exists, so a record that contradicts its own control is a non-re-deriving record (D-06 INCONCLUSIVE) rather than one admission re-labels as REFUSED. It can never be ADMITTED, CANDIDATE-UNREPLICATED or MOOT. Deviation from the suggested fix: a learnable leg may still carry REFUSED points, because the route also refuses on its extraction-ceiling and retention floors, which D-11 does not own. Tests: `test_admission_reads_only_the_legs_own_control` (8 cases, all RED on the pre-fix module: MOOT/ADMITTED/CANDIDATE) and `test_admission_learnable_leg_may_carry_route_refusals`.

## Warnings

### WR-01: admission() raises on a non-dict `verdicts`, which breaks the "returned, never raised (T-29-14)" contract

**File:** `scripts/phase29_prereg.py:408, 495`
**Issue:** `(frontier.get("verdicts") or {}).get(...)` assumes that a truthy `verdicts` is a dict. Evidence: set `frontier["verdicts"] = ["x"]` on an otherwise valid frontier and `admission()` raises `AttributeError: 'list' object has no attribute 'get'`. The docstring says (1a-1c) malformations are "returned, never raised (T-29-14)". None of the 12 parametrized INCONCLUSIVE cases in `tests/test_phase29_prereg.py` covers this shape.
**Fix:** In step (1a), add `or not isinstance(frontier.get("verdicts"), dict)` to the shape check. Add a `"verdicts-not-dict"` case to `test_admission_inconclusive_takes_precedence`.

**Resolution:** FIXED in 0f0336f. (1a) returns INCONCLUSIVE when `verdicts` is absent or not a dict. Cases `verdicts-not-dict` (RED pre-fix: AttributeError) and `verdicts-absent` were added.

### WR-02: refused_record() accepts any recipe values, and the test fixture writes the n8 recipe into an n64 REFUSED record

**File:** `scripts/phase29_prereg.py:241-251`; `tests/test_phase29_prereg.py:47, 335-345`
**Issue:** D-13 requires the REFUSED record to carry the recipe identity. The builder checks only the recipe's key set. Evidence: `refused_record(POINT_KEYS()[7], ..., recipe={"replay_windows": 999, "n_facts": 8, "seed": "x", "max_steps": -1})` returns without error. `test_refused_record_shape` itself uses key index 7 (`advr_n64_ratio0p250000`) with `_RECIPE = {"replay_windows": 32, "n_facts": 8, ...}`, which is the n8 leg's recipe. The test therefore enshrines a wrong record.
**Fix:** Derive the leg's n from the key and check the values:
```python
n = int(leg[1:])
_prove(recipe["n_facts"] == n, f"recipe n_facts {recipe['n_facts']} != leg {leg}")
_prove_count("seed", recipe["seed"]); _prove_count("max_steps", recipe["max_steps"])
_prove(recipe["replay_windows"] == replay_windows(n), "recipe replay_windows is not the D-04 expression")
```
(`replay_windows` imports torch lazily. If that is unacceptable here, compare against `teach_persona.REPLAY_WINDOWS_PER_FACT * n` inside the same lazy import.) Then fix the test to use `n_facts=64, replay_windows=256` for the n64 key.

**Resolution:** FIXED in 9179cd7. The recipe values are proved against the key's leg: `n_facts == n`, `replay_windows == replay_windows(n)` (lazy teach_persona import), and int (non-bool) `seed >= 0` and `max_steps > 0`. Seed and max_steps are not pinned to values because they are Phase 30's calibration (ARECIPE-02). The fixture is now the n64 recipe (256/64). Nine new refusal cases, all RED pre-fix.

### WR-03: relearning_scope() trusts a caller-supplied dict, so an ADMITTED with no keys or foreign keys goes through

**File:** `scripts/phase29_prereg.py:576-587`
**Issue:** The scope rule dispatches the RELRN-06..09 runs, but it only validates `verdict`. Evidence: `relearning_scope({"verdict": "ADMITTED", "admitted_point_keys": ["adv_n64_ratio0p250000"]})` returns `relearn_point_keys=('adv_n64_ratio0p250000',)`, which is a v4.0 key. `{"verdict": "ADMITTED", "admitted_point_keys": []}` returns ADMITTED with nothing to run, which contradicts "ADMITTED iff >= 1 PASS". `test_scope_rule_covers_every_verdict` feeds exactly that empty-ADMITTED dict and accepts it.
**Fix:**
```python
keys = tuple(admission_result["admitted_point_keys"])
_prove(set(keys) <= set(POINT_KEYS()), f"admitted keys {keys} outside the 12 v5.0 keys")
_prove((verdict == "ADMITTED") == bool(keys), f"{verdict} with admitted keys {keys}")
```

**Resolution:** FIXED in 79cd4c6. `admitted_point_keys` must be a list or tuple of distinct keys in `POINT_KEYS()`, and non-empty iff the verdict is ADMITTED. `test_scope_rule_covers_every_verdict` now forges ADMITTED with a key. `test_scope_rule_refuses_foreign_or_empty_admitted_keys` has 5 cases, all RED pre-fix.

### WR-04: the ancestry guard covers only phase29_prereg.py, but the frozen keys and route are resolved at call time from modules nothing freezes

**File:** `scripts/phase29_prereg.py:89-91, 104-116`; `tests/test_phase29_prereg.py:112-120`
**Issue:** `POINT_KEYS()` renders through `phase25_record.point_key`. `GATE_ROUTE` is `phase20_gate_coverage.corrected_point_verdict`. Both are resolved at call time, "never at import". No test file ancestry-guards `scripts/phase25_record.py` or `scripts/phase20_gate_coverage.py`. Evidence: `grep` finds neither path in any `_assert_frozen_before` or pathspec across `tests/`, and `scripts/phase25_record.py` was edited on 2026-09-09 (52e736c, 75b86a6), after its own v4.0 results existed. After Phase 30, an edit to either file changes the pre-registered keys or route while `test_phase29_prereg_is_frozen_before_every_v5_result` stays green. `mitigation_gate` and `phase27_prereg` do have their own guards. `mitigation_budget` is covered only indirectly.
**Fix:** Make `_assert_frozen_before` take a tuple of source paths and call it with `(PREREG, "scripts/phase25_record.py", "scripts/phase20_gate_coverage.py", "scripts/mitigation_budget.py")` against the same `ARTIFACT_PATHSPECS`. Alternatively, pin `POINT_KEYS()` as a literal tuple checked against the renderer, so a renderer change reddens.

**Resolution:** FIXED in a37e9a4 (test only). `test_call_time_sources_are_frozen_before_every_v5_result` runs Plan 01's `_assert_frozen_before` for `scripts/phase25_record.py` and `scripts/phase20_gate_coverage.py` against the same derived `ARTIFACT_PATHSPECS`. It is green because 0 `results/phase3*` files are tracked. Non-vacuity is a natural RED: the same helper fires (CalledProcessError) on each source against a v4.0 artifact it post-dates (`results/phase25_frontier.json`, `results/phase20_gate_coverage_correction.json`). `mitigation_budget.py` is not added: the task scoped the guard to the two call-time sources.

## Info

### IN-01: refused_record() returns the module constant V4_ADV_N64_READING by reference

**File:** `scripts/phase29_prereg.py:252`; `tests/test_phase29_prereg.py:344`
**Issue:** Evidence: `r["v4_adv_n64_reading"]["heldout"] = (600, 648)` changes `phase29_prereg.V4_ADV_N64_READING["heldout"]` to `(600, 648)`. A Phase-32 writer that annotates the record would corrupt the pinned reading for every later record in the process. The test asserts `is`, which enshrines the aliasing.
**Fix:** Return `dict(V4_ADV_N64_READING)`, or `{k: list(v) if isinstance(v, tuple) else v ...}` so the record matches the JSON shape. Assert `==` in the test.

**Resolution:** FIXED in 49a4e9f. The record now carries `dict(V4_ADV_N64_READING)`. The test asserts `==`, then mutates the record and proves the pin is unchanged (RED pre-fix: `(600, 648) == (0, 648)`).

### IN-02: d28_note() has no production caller

**File:** `scripts/phase16_persistence.py:2069-2077`
**Issue:** The docstring says "No rendering path calls this". Only `tests/test_phase16_driver.py` calls it. This is intended (D-17), but it is a function in the shipped driver that exists only for tests.
**Fix:** None required. Moving the digest check into the test that already has `_context_blockquote` would also work.

**Resolution:** SKIPPED. It is out of the fix scope set by the developer ruling, and no fix is required (D-17 intended).

### IN-03: test_phase16_driver.py now imports phase29_prereg at module scope

**File:** `tests/test_phase16_driver.py:38`
**Issue:** An import error in the v5.0 pre-registration, or in anything it transitively loads (the accountant through `phase25_record`), now turns every test in the v3.0 Phase-16 driver file into a collection error. Only one test uses it.
**Fix:** Import `phase29_prereg` inside `test_d28_report_absence_is_a_named_limitation`.

**Resolution:** SKIPPED. It is out of the fix scope set by the developer ruling.

### IN-04: _frontier_leg and _tally duplicate phase27_prereg's private helpers

**File:** `scripts/phase29_prereg.py:387-393` (vs `scripts/phase27_prereg.py:325-333`)
**Issue:** These are near-identical copies. `phase27_prereg` is frozen, so reusing its private names couples the two modules to private API. The copies could drift apart, but for now they agree.
**Fix:** Keep them, with a comment naming the source, or bind them by reference like the D-09 pins.

**Resolution:** SKIPPED. It is out of the fix scope set by the developer ruling.

---

_Reviewed: 2026-09-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
