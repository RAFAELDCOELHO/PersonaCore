---
phase: 35-v6-0-pre-registration-and-the-research-it-rests-on
reviewed: 2026-10-02T00:15:13Z
depth: standard
scope: "git diff b2684bc 1e1e1c5 (fix of the 12 findings in 35-REVIEW.md)"
files_reviewed: 2
files_reviewed_list:
  - scripts/phase35_prereg.py
  - tests/test_phase35_prereg.py
rereviewed: 2026-10-02T00:41:16Z
rereview_scope: "git diff 14a7b7f 3805beb (fix of WR-01..03, IN-01..05; WR-04 ruled by Rafael, docstring only)"
prior_findings_1e1e1c5:
  warning: 4
  info: 5
  total: 9
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
  blocking: 0
  known_limitations: 9
status: clean
---

# Phase 35: Code Review Report (re-review of fix commit 1e1e1c5)

**Reviewed:** 2026-10-02T00:15:13Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Baseline: `.venv/bin/pytest -q tests/test_phase35_prereg.py` gives **86 passed in 20.92s**. After every experiment, `git status --short` shows only the pre-existing ` D .claude/scheduled_tasks.lock`.

All experiments live in the session scratchpad (`probe1.py`, `probe2.py`, `probe3.py`, `probe_after.py`, `probe_fix.py`). Each one plants records under `tempfile.mkdtemp()` and points `phase35_prereg._REPO_ROOT` there. Nothing was written under scripts/, tests/ or results/.

**Closure of the 12 original findings.** Every original probe now refuses:

| ID | Result | Evidence |
|----|--------|----------|
| CR-01 | CLOSED | probe_after P1: `the declared input 'results/phase40_noise_floor.json' was not consumed`. P1': `supplied {... 99.0}, read {... 0.1}; they are read`. P1'' (keys only) is accepted and returns bands built from the record. |
| WR-01 | CLOSED | probe1 P2: `k_plus is -1; a count is >= 0` |
| WR-02 | CLOSED for targets x cells; seeds not covered (see WR-03 below) | probe2 P8: `floors: every (ordering[, seed]) cell needs a key for every e1 target` |
| WR-03 | CLOSED | probe_after P7: the ceiling HALT message. P7b: `front_hours['probes'] is '5', which is not an int or float` (a `_prove` refusal, no TypeError) |
| WR-04 | CLOSED for top-level entries; nested values still mutable (IN-01) | probe_after P5: `out is e` is False, and `__setitem__` is refused |
| WR-05 | PARTIAL (WR-02 below) | probe2 P4: all three original bypasses are now reported |
| WR-06 | CLOSED by the documented-contract route | e3's derivation value is now the grid recipe keys; the module docstring and each rule now state the "caller-chosen part" |
| IN-01 | CLOSED | probe3: `seed is 1337.0, which is not an int` |
| IN-02 | CLOSED | probe_after P10: `a duplicate input record` |
| IN-03 | CLOSED | `_is_fill_file` now derives from `owner_prereg_glob`; `test_fill_file_predicate_agrees_with_owner_prereg_glob` passes |
| IN-04 | CLOSED for plain dicts; `_Filled` itself is forgeable and mutable (WR-01 below) | `test_grids_must_be_fill_results` passes |
| IN-05 | CLOSED; residual name-collision noted (IN-05 below) | `_untested_functions` on the real tree returns `[]` |

**The new "every declared pattern consumed" rule does not refuse any legal fill.** I checked each of the 17 slots against its declared patterns:

- **Single-pattern slots** (v6_budget, e2_S, e1_checkpoint_grid, e4, e5_set_sizes, e6_entry_subset): a fill must consume at least one path anyway, so the new rule adds nothing.
- **e1_condition_a_floors**: both the calibration records and the corpus are always required.
- **e1_condition_c_band_inputs**: both patterns are always required.
- **e3_grid_subset and e3_recall_threshold**: the v4.0 control is `optional=` and is then forced in or out by the reuse check. `results/phase42_control_*` is always consumed, because at most one recipe can reuse the v4.0 control.
- **e1_condition_b_margin and the design slots**: these do not consume inputs.

I also checked these points:

- **The `optional=` exemption** is AST-pinned to the two e3 rules.
- **The D-06 STOP message** is still reachable through both `v6_budget_and_stop_line` and `e2_S` (`test_e2_S_refuses_more_seeds_than_the_list` asserts "D-06" and "never extended").
- **total_hours vs fsum, int vs float hours:** `40 == 40.0` holds, and `_prove_real` admits both types. No defect.

The fix did introduce one regression (WR-01). The other findings are incomplete closures or pre-existing gaps that the fix's own claims now cover.

## Warnings

### WR-01: `_Filled` makes the grids less immutable than before, and anyone can construct one (regression)

**File:** `scripts/phase35_prereg.py:857-872, 1201-1208, 1470-1477`
**Issue:**
- **Regression.** At b2684bc, `e1_checkpoint_grid` and `e3_grid_subset` returned `types.MappingProxyType` (old lines 1091 and 1338). The fix returns `_Filled`, which stores a plain `dict` in `self._data`. So a grid can now be rewritten after the fill, and `e1_stop` accepts the rewritten grid.
- **False claims.** This breaks the module's claim at `:1114-1115` ("every container returned is read-only").
- **IN-04 only half-closed.** `_Filled` is a public constructor, so IN-04 ("a hand-built dict with the right keys is refused") is still bypassable. The census does not flag a reference to `phase35_prereg._Filled`.

**Demonstrated:** `.venv/bin/python <scratchpad>/probe_fix.py`

```
N1 e1_stop on grid mutated post-fill -> ACCEPTED: {'stop': 1, 'judged': True}       # grid._data["checkpoints"] = (1,)
N1b e1_stop on hand-built _Filled, read_k=1 -> ACCEPTED: {'stop': 1, 'judged': True}
```

The census check on `G = phase35_prereg._Filled({...})` returns `[]`.

**Fix:** Keep the MappingProxyType and mark provenance with an identity registry:

```python
_FILLED_GRIDS = []          # ids are not enough: keep the objects alive
def _filled(data):
    grid = types.MappingProxyType(dict(data))
    _FILLED_GRIDS.append(grid)
    return grid
# e1_stop / e3_recall_threshold:
_prove(any(grid is g for g in _FILLED_GRIDS), "grid must be the fill(...) result")
```

Alternatively, give `_Filled` `__slots__ = ("_data",)` with `_data` a `MappingProxyType`, and add `"_Filled"` to the census's private-attribute checks.

### WR-02: WR-05 is only partly closed. A `_SLOTS` write still swaps a slot's rule under `fill`, invisible to the census

**File:** `scripts/phase35_prereg.py:1823-1825`; `tests/test_phase35_prereg.py:2081-2086, 2129-2169`
**Issue:**
- **Shared inner dicts.** `SLOTS = MappingProxyType({name: MappingProxyType(slot) ...})` wraps the same inner dicts that `_SLOTS` holds. So `phase35_prereg._SLOTS["x"]["rule"] = f` changes what `fill("x")` dispatches. That is D-02 case 3, "a different rule".
- **Census blind spots.** `_reaches_slots` only recognises the literal `phase35_prereg.SLOTS`. It misses a module alias bound by assignment, `vars()`, and `sys.modules`. The test comment at `:2254` says "reaching a rule without fill, under any name, from any file"; that claim does not hold.
- **Freeze deadline.** The runtime half of the fix lives in the prereg module, which freezes at Phase 36's first record.

**Demonstrated:** `.venv/bin/python <scratchpad>/probe_fix.py`

```
N6 bypass alias-by-assignment -> []      # M = phase35_prereg; M.SLOTS['e2_S']['rule'](s=5)
N6 bypass private _SLOTS call -> []
N6 bypass _SLOTS write -> []             # phase35_prereg._SLOTS['e2_S']['rule'] = print
N6 bypass vars() -> []
N6 bypass sys.modules -> []
N7 fill after _SLOTS write: HIJACKED
```

**Fix:** Before the freeze, decouple the registry from the mutable dict:

```python
SLOTS = types.MappingProxyType(
    {name: types.MappingProxyType(dict(slot)) for name, slot in _SLOTS.items()}
)
del _SLOTS   # or keep it only as a build-time local
```

In the census, also treat `_SLOTS` like `SLOTS`. Flag a module-level `Name = phase35_prereg` binding as an alias, along with `vars(phase35_prereg)` and `sys.modules[...]`.

### WR-03: Floor coverage does not require both teaching seeds for a seeded ordering (the band rule does)

**File:** `scripts/phase35_prereg.py:1211-1223, 1310-1318`
**Issue:**
- **The gap.** `_prove_cells_cover_targets` requires targets x the (ordering[, seed]) cells *that appear*. A seeded ordering keyed for only `e1_teaching_seeds()[0]` is therefore accepted, and the second seed's E1 cells have no condition-(a) floor.
- **Inconsistent with the band rule.** The fix's band rule enforces both seeds per ordering (`:1684-1688`, ERASE-10: "no E1 PASS without the second seed's run"). So the two condition rules now disagree on what coverage means.
- **Not introduced by the fix.** The gap predates the fix, but WR-02's fix claims per-cell coverage. 35-CONTEXT allows "calibration per ordering, and per seed if the derivation requires it", and when it does, both teaching seeds run.

**Demonstrated:** `.venv/bin/python <scratchpad>/probe_fix.py` uses one calibration record for `("greedy_loo", 1337)` built from the real cal-erased draws, with floors keyed `(t, "greedy_loo", 1337)` for every target:

```
N3 floors seeded for one teaching seed only -> ACCEPTED: [1337]
```

**Fix:** In `_prove_cells_cover_targets`, for each ordering with seeded keys, require `{cell[1] for cell in cells if cell[0] == o and len(cell) == 3} == set(e1_teaching_seeds())`. Add a "one_seed" RED case to `test_e1_floors_refuse_a_typed_floor_or_a_mismatched_record`.

### WR-04: The choice of E2's S moved from Phase 40 to Phase 36's budget fill, and no planning artifact records it

**File:** `scripts/phase35_prereg.py:61-64, 933-966, 1118-1160`
**Issue:**
- **What moved.** To close WR-03, `e2_seed_count` became a required input of `v6_budget_and_stop_line` (owner 36), and `_rule_e2_S` (owner 40) now only reads it back.
- **What the docs say.** 35-CONTEXT's D-15 table (line 71) still reads "E2 `S` | Phase 40 | from the Phase 36 COST-01 probe record under the COST-02 budget". `grep -rln e2_seed_count .planning/` returns nothing.
- **Effect on leg (a).** The registry still lists e2_S as a Phase-40 slot, so the ordering legs treat Phase 40 as the phase that chose S. The real choice now happens in a Phase 36 fill file.
- **Consequence.** This is a change in who decides S, made in a review fix with no ruling cited. The commit message body is empty, and the e2_S docstring cites only "review WR-03".

**Not demonstrated as a runtime defect.** The shape is shown by `.venv/bin/python -c "...inspect.signature..."`:

```
40 (*, input_records, derivation, s=None)
36 (*, front_hours, stop_line_hours, e2_seed_count, input_records, derivation)
```

**Fix:** Get Rafael's ruling before the freeze. Then either (a) record the move: add a CONTEXT/decision addendum, and set e2_S's owner to 36 or drop it as a slot; or (b) take the other WR-03 option, keep S chosen in Phase 40, and reword the docstring to "S chosen by Phase 40, bounded by the re-validated budget".

## Info

### IN-01: `_frozen_entry` freezes only a top-level Mapping value

**File:** `scripts/phase35_prereg.py:1103-1111`
**Issue:** A list value, or a mapping nested inside the value, is still shared and mutable after the fill. This leaves WR-04 partly open.
**Demonstrated** (`probe_fix.py`):

```
N2 list value mutated after fill: ['step a', 'step b (post-fill)']
N2b nested mapping mutated after fill: {'a': 1, 'proposer': 'planted'}
```

**Fix:** Deep-freeze recursively (Mapping becomes MappingProxyType, list becomes tuple). Or require `_prove_entry` values to be str / number / tuple.

### IN-02: Band rule records with a malformed shape crash instead of failing through `_prove`

**File:** `scripts/phase35_prereg.py:1692-1705`
**Issue:** `noise["gap_noise_floor"]`, `record["seed"]` and the other reads are not guarded. The rule fails closed, but with a raw exception. WR-03's fix added exactly this guard for the budget record (`_budget_record`).
**Demonstrated** (`probe_fix.py`):

```
N4 noise record missing gap_noise_floor -> UNCAUGHT KeyError 'gap_noise_floor'
N4b noise record is a list -> UNCAUGHT TypeError list indices must be integers or slices, not str
```

**Fix:** Prove `isinstance(record, Mapping)` and the field set for the noise record and for each band record before reading. The calibration records in the floors rule need the same.

### IN-03: The widened census flags legitimate method-call reads of `SLOTS`

**File:** `tests/test_phase35_prereg.py:2144-2145`
**Issue:** `isinstance(node, ast.Call) and _reaches_slots(node.func)` matches any method on the registry. That includes read-only calls such as `.items()`, `.get()` and `.index()`. A plain subscript read is not flagged.
**Demonstrated** (`probe_fix.py`):

```
N6 FP read SLOTS.items() -> ['...:2: registry call through phase35_prereg.SLOTS']
N6 FP read input_records.index -> ['...:2: registry call through phase35_prereg.SLOTS']
N6 OK read input_records subscript -> []
```

**Fix:** Flag a Call only when its func chain passes through a `["rule"]` subscript, which is already caught by the `'rule'` subscript check. Otherwise, allow-list read methods.

### IN-04: Key-valued derivation values depend on dict insertion order

**File:** `scripts/phase35_prereg.py:1275, 1689-1691, 1493-1498`
**Issue:** The floors and band slots compare the derivation value against `tuple(floors)` / `tuple(band_inputs)`, and e3 compares against grid order. So a derivation that lists the same keys in a different order is refused. This fails closed, but it can reject a legal fill.
**Demonstrated** (`probe_fix.py`):

```
N5 band derivation lists the same keys in reverse order -> SystemExit: ... the derivation's value ((2024, 'g'), (1337, 'g')) is not the slot's chosen value ((1337, 'g'), (2024, 'g'))
```

**Fix:** Compare as sets for key-valued slots (`set(derivation["value"]) == set(keys)`, with no duplicates). Or document "in mapping order" in each rule's docstring.

### IN-05: The call-counting function census matches a bare method name on any object

**File:** `tests/test_phase35_prereg.py:2617-2619`
**Issue:** `named |= {f.attr ...}` counts `anything.<name>()` as a call of the prereg def `<name>`. On the real tree every def is called as `phase35_prereg.<def>(...)` or through `fill`, so nothing is masked today.
**Demonstrated:**

```
.venv/bin/python -c "...T._untested_functions('def items(): ...\ndef seed_list(): ...', 'd.items()\nother.seed_list()')"
-> []
```

**Fix:** Count only `Attribute(value=Name('phase35_prereg'))` calls, plus `Name` calls of names that are explicitly imported from the module.

---

_Reviewed: 2026-10-02T00:15:13Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Re-review of 3805beb (2026-10-01)

**Scope:** `git diff 14a7b7f 3805beb`, covering `scripts/phase35_prereg.py` and `tests/test_phase35_prereg.py`. This commit fixes WR-01..03 and IN-01..05 above. WR-04 was ruled by Rafael and changes only the docstrings.

**Stopping rule (Rafael, verbatim):** "só bloqueia o congelamento um achado que mude um valor lido ou um veredito emitido num fill real. Achado de endurecimento contra contorno deliberado vira limitação conhecida registrada no 35-REVIEW-FIX, sem novo commit no módulo."

**Classification used below:**
- **BLOCKING:** a one-command experiment shows a real fill reading a different value or emitting a different verdict. A real fill is an owner fill file calling `phase35_prereg.fill(...)` with honest records. A legal fill that is refused, or an illegal value that the normal API accepts, also counts.
- **Known limitation:** the issue only shows up when someone deliberately bypasses the API: private names, forged objects, monkeypatching, dynamic access, or deliberate census evasion.

**Baseline.** HEAD is `3805beb`.
- `.venv/bin/pytest -q tests/test_phase35_prereg.py` gives **88 passed in 17.92s**.
- After every experiment, `git status --short` shows only the pre-existing ` D .claude/scheduled_tasks.lock`.

**Probes.** All of them live in the session scratchpad: `probe_fix.py`, `probe_fix_after.py`, `probe_rr3805.py` and `probe_rr3805b.py`. Records are planted under `tempfile.mkdtemp()` with `_REPO_ROOT` repointed there. Nothing was written under `scripts/`, `tests/` or `results/`.

### (a) Closure of each finding

| ID | Result | Evidence |
|----|--------|----------|
| WR-01 | CLOSED | Grids are now `MappingProxyType` over a private copy, registered by identity in `_FILLED_GRIDS`. `probe_fix.py` now dies at its first step with `AttributeError: 'mappingproxy' object has no attribute '_data'`. `probe_fix_after` N1: `grid['checkpoints'] = (1,)` raises `TypeError`, and `e1_stop` refuses the readings for checkpoint 1 because the grid was not changed. N1b: a hand-built grid is refused with `grid must be the fill('e1_checkpoint_grid', ...) result`. `probe_rr3805` R4: a real grid still judges, giving `{'stop': 8, 'judged': True}`. Residual: KL-01. |
| WR-02 | CLOSED for the runtime hijack and the five named census bypasses | `_SLOTS` is deleted, and `probe_fix_after` N7 dies with `module 'phase35_prereg' has no attribute '_SLOTS'`. `SLOTS` inner proxies wrap `dict(slot)` copies, and `test_registry_is_built_from_copies` passes. In N6 the census now flags alias-by-assignment, private `_SLOTS` read and write, `vars()` (also flagged as a `_rule_` reference by name), and `sys.modules['phase35_prereg']`. Residuals: KL-02..KL-05. |
| WR-03 | CLOSED | `probe_fix_after` N3 is refused with `floors: seeded ordering 'greedy_loo' needs every e1 teaching seed (ERASE-10)`. The legal floors fill seeded for both teaching seeds is still accepted (`tests/test_phase35_prereg.py:1700-1708`, `-k floors`: 7 passed). The check `len(cell) == 2` is correct because `cell = key[1:]`. |
| WR-04 | RULED (docstring only) | Only the module docstring (`:61-67`) and `_rule_e2_S`'s docstring changed; the signature and body are unchanged. The **D-06 STOP is intact through both doors.** `probe_rr3805` D1 (`_prove_budget`) and D2 (`fill("e2_S")` on a record with S = len(seed_list()) + 1) both print `the Phase 36 probe calls for S > len(seed_list()): STOP and ask Rafael (D-06); the seed list is never extended`. |
| IN-01 | CLOSED | `_deep_frozen` recurses through Mapping and list/tuple. `probe_fix_after` N2: the list value after the fill is `('step a',)`, and `append` raises `AttributeError`. N2b: the nested mapping is unchanged (`{'a': 1}`) and assignment raises `TypeError`. No design rule tests `isinstance(value, list)` after freezing; the only post-freeze check is the `str` check at `:1418-1421`, so a legal design fill is not refused. |
| IN-02 | CLOSED for every field the rules read at top level | `probe_fix_after` N4 and N4b: `must be a mapping carrying ['gap_noise_floor']`. The new tests cover a malformed band record, a malformed calibration record (`no_draws`) and a malformed e3 control. Every field `_prove_record` now requires was already read unguarded before, so an honest record that used to pass still passes. Residual: N-02. |
| IN-03 | CLOSED | `probe_fix_after` N6 FP: `SLOTS.items()` and `.index(...)` now give `[]`. `test_slot_census_lets_registry_reads_pass` passes. |
| IN-04 | CLOSED | `probe_fix_after` N5: the reversed band keys are ACCEPTED, with bands equal to the forward fill. The test accepts the reversed e3 keys (`:2098-2099`). A duplicated key is refused (`value_twice`). See N-01 for the strictness change. |
| IN-05 | CLOSED | `_untested_functions` counts only `phase35_prereg.<def>(...)` and bare calls of names imported from the module. The test asserts that `other.planted_helper()` does not count and that `from phase35_prereg import planted_helper; planted_helper()` does. |

**No false refusal of a legal fill, checked for all 17 slots:**
- Every one of the 17 slots has a `phase35_prereg.fill(...)` call in the test file (`_fill_calls`: no slot missing), and the suite is green.
- **Slots whose behaviour changed:**
  - The key-valued slots (`e1_condition_a_floors`, `e1_condition_c_band_inputs`, `e3_recall_threshold`) now go through `_READ` plus `_prove_keys_value`.
  - The grid slots (`e1_checkpoint_grid`, `e3_grid_subset`) now go through `_filled`.
  - The design slots (`e1_alternative_ordering`, `e2_noise_floor_estimator`, `e5_minting_rule`, `e5_rank_moves_and_generation_collapses`, `e6_decomposition_rule`, `r1b_tolerance_and_replicated`) now go through `_deep_frozen`.
  - Each of these slots has a positive acceptance assertion in the suite.
- `_READ` only moves the derivation-value check from `_consume_inputs` into `_prove_keys_value`. It runs after input validation, so the refusal message order changes, but nothing new is accepted or refused (apart from N-01).

**No false positive on the real tree or on a legitimate owner fill file:**
- The real-tree census is green.
- `probe_rr3805` L1 is a planted `scripts/phase40_x_prereg.py`. It does `import phase35_prereg`, reads `SLOTS['e2_S']['input_records']`, `owner_prereg_glob('e2_S')`, `V6_RESULT_PATHS` and `seed_list()`, and binds `E2_S = phase35_prereg.fill('e2_S', ...)`. The census returns `[]`.

**Copying and pickling a grid** (stated as relevant, not required):
- `copy.copy(grid)` and `pickle.dumps(grid)` both raise `TypeError: cannot pickle 'mappingproxy' object` (R2, R3).
- This does not matter for the API, because a copy would be refused by the identity check anyway. A consumer has to pass the object `fill` returned, in the same process (KL-07).

### (b) BLOCKING findings

None. No experiment changed a value read or a verdict emitted by a real fill.

### Non-blocking notes (behavioural, not bypass hardening)

- **N-01:** `_prove_keys_value` compares by `repr`, so it is stricter than the old `==`.
  - A derivation value that writes an equal number with a different type is now refused, where the old check accepted it. `probe_rr3805` K1: the old `==` is True. K2: `((1e-4, 300.0, 8, 1337),)` against key `((1e-4, 300, 8, 1337),)` is now refused.
  - This fails closed, and only on a derivation that does not list the slot's actual keys. Seeds, steps and batch are proven `int` by `_prove_count`, and the honest form `tuple(floors)`, `_grid_keys(grid)` or a copy of the keys is accepted, as K3 and the tests show.
  - It is not BLOCKING. It could be relaxed later with `==` on a multiset if a phase ever needs it.
- **N-02:** in `e3_recall_threshold`, `record["taught_recall"]["numerator"]` and the `heldout_recall` equivalent (`:1579-1580`) are not shape-guarded.
  - A control whose `taught_recall` is not a mapping would raise a raw `TypeError`/`KeyError` instead of a `_prove` refusal.
  - This is found by reading the code, not demonstrated. It fails closed and does not change a value or a verdict.

### Known limitations (accepted under Rafael's stopping rule)

- **KL-01 Forging a grid by appending to `_FILLED_GRIDS`:**
  - `phase35_prereg._FILLED_GRIDS.append(types.MappingProxyType({...}))` makes `e1_stop` and `e3_recall_threshold` accept a grid no rule produced. `probe_rr3805b` R1'': `{'stop': 1, 'judged': True}` on a never-filled grid.
  - The census flags the dotted `phase35_prereg._FILLED_GRIDS`, but not the routes in KL-02 and KL-03.
- **KL-02 Module passed as a function argument:**
  - `def f(m): m._FILLED_GRIDS.append(...)` (or `m.SLOTS[...]...`) followed by `f(phase35_prereg)` is invisible to the census, which only recognises the literal name `phase35_prereg`. `probe_rr3805b` G1': `[]`.
- **KL-03 From-import of private names other than `_rule_*`:**
  - `from phase35_prereg import _filled, _FILLED_GRIDS` is not flagged (`probe_rr3805` G3: `[]`). After that, `_filled({...})` mints a registered grid.
- **KL-04 Reaching a rule by iterating the registry:**
  - `for v in phase35_prereg.SLOTS.values(): v["rule"](...)` calls a rule without `fill`. The census flags only `SLOTS[...]["rule"]` and `.get("rule")` on a chain rooted at `phase35_prereg.SLOTS` (`probe_rr3805` G2: `[]`).
- **KL-05 Reaching module state through a public function's `__globals__`:**
  - `phase35_prereg.e1_stop.__globals__["_FILLED_GRIDS"]` is not flagged (`probe_rr3805` G4: `[]`). The `"_rule_"` string-constant check does catch the rule variant.
- **KL-06 The census is over-strict on honest code** (fails loud in the test only, and no fill value is affected):
  - A string constant exactly `"phase35_prereg"`, for example a provenance field `{'prereg': 'phase35_prereg'}`, is flagged as "dynamic import" (`probe_rr3805` F1).
  - Any string constant that starts with `_rule_` is flagged.
  - Dunder reads such as `phase35_prereg.__file__` are flagged as "private access" (F2).
  - An owner who hits one of these has to rephrase the code. The census never passes a bypass because of this.
- **KL-07 Grid identity is per module object and per process:**
  - A grid filled through one copy of the module (after `importlib.reload`, or with the module imported under a second dotted name) is refused by the other copy's `e1_stop`/`e3_recall_threshold`.
  - A grid cannot be copied or pickled across processes (R2, R3).
  - The old `isinstance(grid, _Filled)` check had the same per-module-object property. A real consumer must call `fill(...)` in the process that judges, or import the fill file's binding.
- **KL-08 `_deep_frozen` covers Mapping, list and tuple only:**
  - A `set`, `bytearray` or custom mutable object inside a design entry's value stays shared and mutable after the fill. A `namedtuple` is flattened to a plain tuple.
  - This is not demonstrated as harmful, because no design slot's rule reads such a value.
- **KL-09 Runtime monkeypatching of module globals is out of scope:**
  - Rebinding `phase35_prereg.SLOTS`, `phase35_prereg.fill` or `_REPO_ROOT` changes what is dispatched or read, and the probes use exactly this for planting.
  - The census flags the dotted private writes (`_REPO_ROOT`, `_FILLED_GRIDS`), but the KL-02 and KL-03 routes reach them unseen.

**Counts for this re-review:** 0 BLOCKING, 2 non-blocking notes (N-01, N-02), 9 known limitations (KL-01..KL-09). Status: **clean** under the stopping rule.

_Re-reviewed: 2026-10-02T00:41:16Z (2026-10-01 local)_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
