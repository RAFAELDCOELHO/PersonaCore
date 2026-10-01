---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
reviewed: 2026-10-01T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase35_prereg.py
  - tests/test_phase35_prereg.py
findings:
  critical: 1
  warning: 6
  info: 5
  total: 12
status: issues_found
---

# Phase 35: Code Review Report

**Reviewed:** 2026-10-01
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

I reviewed the v6.0 pre-registration module and its CPU guard suite. Baseline: `.venv/bin/pytest -q tests/test_phase35_prereg.py` gives 79 passed in 16.7 s with no skips.

The one-run audit port matches App. D line for line: the sf is replaced by an fsum of pmfs, the alpha loop is the same, and the bisection runs from 0 to 1 and then 30 steps. The closed pins are bound by reference, and the ancestry and AST guards behave as their docstrings say.

The defects are in the deferred-slot rules, at the "read, never typed" boundary. This module freezes at Phase 36's first record, and after that each of these can only be fixed with a continuation module. So the cheap time to fix them is now.

I ran every finding below as a probe from the scratchpad. The probes plant records under `tempfile.mkdtemp()` and point `phase35_prereg._REPO_ROOT` at that directory. Nothing was written under scripts/, tests/ or results/.

## Critical Issues

### CR-01: `e1_condition_c_band_inputs` takes a typed gap noise floor and never needs the Phase 40 record

**File:** `scripts/phase35_prereg.py:1498-1527` (registry entry `:1608-1615`)
**Issue:** The slot declares two inputs: `results/phase40_noise_floor.json` and `results/phase41_band_inputs_*.json`. The rule has three gaps:
1. `_consume_inputs` only checks that each path *passed* matches *some* declared pattern. It never requires each declared pattern to be consumed, so the Phase 40 record is optional.
2. The rule throws away the parsed records (the return value of `_consume_inputs` is not used).
3. `control_gap` and `gap_noise_floor` come only from caller kwargs.

The result is that condition (c)'s band is built from typed numbers. That contradicts the docstring ("DIALOGUE_GAP_BAND applied to the control gap and the Phase 40 gap noise floor"), D-02, and the module's own W3 contract. The floors rule (`_rule_e1_condition_a_floors`) does compute its value from its records; this rule does not. The suite also locks the bypass in: `test_slot_e1_rules` (test file `:1375-1389`) fills the slot with only `results/phase41_band_inputs_a.json`.

**Failing input (demonstrated):** plant `results/phase41_band_inputs_a.json = {"gap_noise_floor": 0.1}` and plant no Phase 40 record. Then call:

```python
fill("e1_condition_c_band_inputs",
     band_inputs={(1337, "greedy_loo"): {"control_gap": 1.0, "gap_noise_floor": 99.0}},
     input_records=("results/phase41_band_inputs_a.json",), derivation=...)
```

It is accepted and returns `{(1337, 'greedy_loo'): (0.5, 199.0)}`. The 99.0 contradicts the record (0.1), and no Phase 40 record was consumed. Reproduce with `.venv/bin/python <scratchpad>/probe1.py`, line "P1".

**Fix:** Require the Phase 40 record and read both band inputs from records. The supplied values follow the floors pattern: `None`, or equal to the computed value.

```python
records = _consume_inputs("e1_condition_c_band_inputs", band_inputs, input_records, derivation)
noise = [r for p, r in records.items() if p == "results/phase40_noise_floor.json"]
_prove(len(noise) == 1, "the Phase 40 gap noise floor record was not consumed (NOISE-02)")
floor = noise[0]["gap_noise_floor"]          # field name per the Phase 40 record contract
for key, inputs in band_inputs.items():
    _prove(inputs["gap_noise_floor"] in (None, floor), f"{key!r}: gap_noise_floor is read, not typed")
    # likewise read control_gap from the matching phase41_band_inputs_* record keyed by (seed, ordering)
```

Also state the Phase 40 / band-inputs record contract in the module docstring, as is already done for the budget, control and calibration records. Then change `test_slot_e1_rules` so that the band-only fill is a RED case.

## Warnings

### WR-01: `e4_parameters` accepts negative guess counts

**File:** `scripts/phase35_prereg.py:1414-1417`
**Issue:** `_prove_count` only checks for an int that is not a bool. The only range check is `1 <= k_plus + k_minus <= m`. So `k_plus=-1, k_minus=5` passes with r = 4 and returns a ceiling as if 4 guesses had been made. Here the AUDIT-01 ceiling is computed from an impossible configuration and is not refused.
**Failing input (demonstrated):** `fill("e4_parameters", m=16, inclusion_probability=0.5, k_plus=-1, k_minus=5, beta=0.05, ...)` returns `{... 'k_plus': -1, 'k_minus': 5, 'ceiling': 0, 'runs': False}` (probe1 "P2").
**Fix:**

```python
for name, value in (("k_plus", k_plus), ("k_minus", k_minus)):
    _prove(value >= 0, f"{name} is {value}; a guess count is >= 0")
```

### WR-02: Floor coverage is checked per target, not per (target, ordering[, seed]) cell

**File:** `scripts/phase35_prereg.py:1145-1148, 1183-1191`
**Issue:** The coverage check is `{key[0] for key in floors} == set(e1_targets())`. It passes when each ordering covers only some of the targets, so an E1 cell can end up with no floor. Mixed key arity is also accepted: `(t, "g")` and `(t, "g", 1337)` together require two records (seed `None` and seed 1337), which gives two different floors for the same (target, ordering) cell.
**Failing input (demonstrated):** floors `{(pet_name,"greedy"), (cat_name,"greedy"), (street,"alt"), (sibling_name,"alt")}` with one calibration record for "greedy" and one for "alt", both built from the real cal-erased draws. It is accepted, so pet_name and cat_name have no "alt" floor (probe2 "P8").
**Fix:** Require the full product, and one arity per ordering:

```python
cells = {key[1:] for key in floors}
_prove({(t, *c) for t in e1_targets() for c in cells} == set(floors),
       "every (ordering[, seed]) cell needs a floor for every e1 target")
_prove(len({len(c) for c in cells if c[0] == o}) == 1 for o in {c[0] for c in cells}) ...
```

### WR-03: The budget record is consumed but never validated, and "S read from the budget" is typed

**File:** `scripts/phase35_prereg.py:880-888, 1037-1050`
**Issue:** `_budget_front_hours` checks only the set of `front_hours` keys and returns `hours[front]`. Nothing re-applies the `_rule_v6_budget_and_stop_line` invariants to the published record: finite hours ≥ 0, total ≤ stop line ≤ the 90 h ceiling. So a hand-written or edited `phase36_budget.json` funds E1, E2 and E3. Non-numeric hours crash with `TypeError` instead of a `_prove` refusal. Separately, `_rule_e2_S`'s docstring says S is "read from the Phase 36 budget", but S is a caller kwarg; only `E2 > 0` is read.
**Failing input (demonstrated):** a budget record with every front at 1e6 h and `stop_line_hours = 9e9` lets `fill("e2_S", s=2, ...)` return 2 ("P7"). The same record with `"5"` strings as hours raises `TypeError: '>' not supported between 'str' and 'int'` ("P7b").
**Fix:** In `_budget_front_hours`, re-run the budget invariants on the record, e.g. call `_rule_v6_budget_and_stop_line`'s checks on `front_hours` / `stop_line_hours` and prove `total_hours == fsum(front_hours)`. Either read S from a declared record field, or reword the docstring to "S chosen by Phase 40, bounded by the budget".

### WR-04: Design-slot rules return the caller's mutable dict, so D-14 can be broken after the fill

**File:** `scripts/phase35_prereg.py:1243-1251, 1444-1451, 1530-1547, 1065-1071`
**Issue:** The comment at `:1002-1003` says "every container returned is read-only". But `e1_alternative_ordering`, `e5_minting_rule`, `e2_noise_floor_estimator`, `e6_decomposition_rule`, `r1b...replicated_definition` and `e5_rank_moves...` return the very dict the caller passed in, not a proxy. Any code holding `E5_MINTING_RULE` can add a `proposer` key or blank the value after `_prove_entry` has passed.
**Failing input (demonstrated):** `out = fill("e5_minting_rule", minting_rule=e)` returns `out is e == True`. `out["proposer"] = "Rafael"` then succeeds, and so does `fill("e1_alternative_ordering", ...)["value"] = ""` ("P5").
**Fix:** Add one helper and use it in every design rule:

```python
def _frozen_entry(name, entry):
    _prove_entry(name, entry)
    return types.MappingProxyType(dict(entry))
```

### WR-05: The D-02 slot census can be bypassed by calling a rule through `SLOTS`, and it scans only top-level scripts

**File:** `tests/test_phase35_prereg.py:1825-1829, 1854-1927`
**Issue:**
- `_reaches_slots` flags only `Store`/`Del` contexts. A `Load` call such as `phase35_prereg.SLOTS["e2_S"]["rule"](...)` fills a slot from any file with no fill call, no `_rule_` attribute and no binding, so D-02 cases 2 and 3 go unseen.
- `getattr(phase35_prereg, "fill")("e2_S", ...)` and `importlib.import_module(...).fill(...)` are caught only when the result is bound to the upper-cased slot name. Under any other name they are invisible.
- `_scanned_sources` globs `scripts/*.py` non-recursively plus `src/`. Meanwhile `owner_prereg_glob`'s fnmatch `*` crosses `/`, so files under `scripts/<sub>/` are never scanned.

**Failing input (demonstrated):** `_slot_census_failures([("scripts/phase37_driver.py", 'import phase35_prereg\nS = phase35_prereg.SLOTS["e2_S"]["rule"](s=5, input_records=(), derivation={})\n')])` returns `[]` (probe2 "P4").
**Fix:** Flag every `Call` whose `func` reaches `phase35_prereg.SLOTS`, and every `getattr(phase35_prereg, ...)` / `import_module("phase35_prereg")`. Scan `scripts/**/*.py`. As a runtime backstop, `fill` could record its caller's filename and refuse non-owner files.

### WR-06: For three slots, the W3 "derivation value is the filled value" check compares the wrong thing

**File:** `scripts/phase35_prereg.py:1027, 1149, 1364-1366`; module docstring `:41-43`
**Issue:** The docstring promises "a four-field derivation whose value is the filled value". Three slots do not meet it:
- **`e3_recall_threshold`** passes `tuple(input_records)` as the value. The derivation's value is the list of paths, which the caller always knows, so the check is vacuous.
- **`e1_condition_a_floors`** passes only the floor keys.
- **`v6_budget_and_stop_line`** passes `front_hours`, not the returned total and stop line.

A derivation written for a different threshold set or floor values passes.
**Failing input (demonstrated for e3):** in probe3, a derivation with `value = input_records` is accepted for `fill("e3_recall_threshold", ...)`. No threshold value is ever compared.
**Fix:** Either check the derivation's value against the computed result after computing it (e.g. `derivation["value"] == dict(thresholds)`), or reword the docstring contract to say which slots bind the derivation to their inputs instead of their output.

## Info

### IN-01: `e3_grid_subset` accepts a float seed and passes it into every cell

**File:** `scripts/phase35_prereg.py:1278`
**Issue:** `seed in seed_list()` accepts `1337.0` because `1337.0 == 1337`, so every cell carries `seed = 1337.0` (probe3 "P9").
**Fix:** Call `_prove_count("seed", seed)` before the membership check. Apply the same to the `key[2]` / `key[0]` seeds in the floors and band rules.

### IN-02: Duplicate `input_records` are silently collapsed

**File:** `scripts/phase35_prereg.py:854-877`
**Issue:** `_consume_inputs` builds a dict, so a repeated path collapses into one entry. In `e3_recall_threshold`, `(c0, c1, c2, c3, c0)` is accepted as 4 controls (probe3 "P10").
**Fix:** Add `_prove(len(set(input_records)) == len(input_records), f"{slot}: duplicate input record")`.

### IN-03: The ordering legs' fill-file regex is narrower than `owner_prereg_glob`

**File:** `tests/test_phase35_prereg.py:2037` vs `scripts/phase35_prereg.py:838`
**Issue:** `scripts/phase40_seeds-prereg.py` matches the owner glob, so the census passes it. The `_fill_sites` regex `[A-Za-z0-9_]*` does not match it, so legs (a) and (b) never examine that file. Leg (c) then reports its slots as "unfilled". That fails closed, but with a misleading message. Checked: `fnmatch` gives True, `re.fullmatch` gives False.
**Fix:** Derive `_fill_sites` from `owner_prereg_glob` (fnmatch), or tighten `owner_prereg_glob` to the regex's character class.

### IN-04: `e1_stop` and `e3_recall_threshold` accept any mapping with the right keys as `grid`

**File:** `scripts/phase35_prereg.py:962-966, 1355-1359`
**Issue:** "grid must be the fill(...) result" is enforced only as a key-set check, so a hand-built dict passes. Neither rule re-checks that `read_k`/`confirm_k` are `CURVE_K`/`FULL_FIDELITY_K`, or that cells use `E3_N` and `E3_SIGMAS`.
**Fix:** Re-prove the invariants (`grid["read_k"] is CURVE_K`, and so on), or return an opaque type from the grid rules and check for it with `isinstance`.

### IN-05: The "every prereg function has a CPU test" census counts any mention as a test

**File:** `tests/test_phase35_prereg.py:2295-2303`
**Issue:** A def counts as "tested" if its name appears anywhere as a `Name` or `Attribute` in the test file, including in an `is` identity assert that never calls it. The census therefore proves the function is mentioned, not that it is exercised.
**Fix:** Count only `Call` nodes whose func names the def, plus `fill("<slot>")` for rules.

---

_Reviewed: 2026-10-01_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
