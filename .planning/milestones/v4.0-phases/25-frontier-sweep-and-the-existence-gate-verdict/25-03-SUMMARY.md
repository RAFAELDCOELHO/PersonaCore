---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 03
subsystem: privacy-reporting
tags: [differential-privacy, epsilon, ast-gate, composition, front-02, d-28, d-29, d-30]

# Dependency graph
requires:
  - phase: 21-privacy-unit
    provides: "results/phase21_multiplicity.json — both multiplicity figures and the RECORDED, NOT RESOLVED status, read never retyped"
  - phase: 22-dpsgd-accountant
    provides: "personacore.privacy.accountant.epsilon_for — the per-point eps and the math.inf at sigma = 0"
  - phase: 23-matched-control
    provides: "results/phase23_sigma_zero.json and results/phase23_noised_dp_n64_sigma0p500000.json — the two records section C5 and D-29 rest on"
provides:
  - "scripts/phase25_epsilon.py — the only sanctioned epsilon rendering surface in Phase 25"
  - "report_epsilon(*, point_epsilon, curve_total_epsilon, selection_accounted) — three keyword-only args, no defaults"
  - "dual_granularity_sentence — D-28's fact-level eps paired with the example-level counterfactual, both multiplicities named"
  - "curve_total — D-29 basic composition at total delta = k*DELTA, refusing the control's absent eps"
  - "CONTROL_EPSILON_FIELD_FORM — section C5's decision: the control record writes \"epsilon\": null explicitly"
  - "EPSILON_NAMES — the committed identifier set D-30's AST gate resolves against"
  - "tests/test_phase25_epsilon.py — the AST gate over every scripts/phase25_*.py, with grep-RED / AST-GREEN measured on the frozen gate"
affects: [25-04 point records, 25-frontier assembly, plot_phase25, FRONT-03 single-source artifact]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structural arity protection: required keyword-only args with no defaults, refused by CPython's own arity check rather than a hand-written guard"
    - "AST-resolved identifier gate with a path-based exemption, replacing a textual guard proved false-RED on the target"
    - "Measured correction recorded in place: the plan's cited precedent is re-measured at execution and the discrepancy is written into the module"

key-files:
  created:
    - scripts/phase25_epsilon.py
    - tests/test_phase25_epsilon.py
  modified: []

key-decisions:
  - "Section C5's decision made in code: Phase 25's control-point record writes the key \"epsilon\" with the value null explicitly plus a sibling epsilon_omitted_reason, never omitting the key — because results/phase23_sigma_zero.json has no epsilon key at all and there is no precedent to inherit"
  - "EPSILON_NAMES is resolved under EXACT membership, not substring: substring resolution counts 11 identifiers on the frozen gate (epsilon_gap, epsilon_independent_of_n, fallback_epsilon_tolerance) and would go RED for the same reason a grep does"
  - "No example-level epsilon NUMBER is invented: results/phase21_multiplicity.json sets provenance.epsilon_computed = false, so the counterfactual is characterised by its multiplicity and the record's own epsilon_note is quoted verbatim"
  - "curve_total refuses BOTH spellings of the control's absent epsilon — None (as a record writes it) and math.inf (as epsilon_for returns it) — rather than only the None the plan names"

patterns-established:
  - "One sanctioned rendering surface + an AST gate over a globbed module set, exemption by resolved path"
  - "The gate's demonstration runs the gate's own resolver, so the demonstration is about the gate that ships"

requirements-completed: [FRONT-02]

# Metrics
duration: 32min
completed: 2026-08-31
---

# Phase 25 Plan 03: The Epsilon Surface and Its AST Gate — Summary

**Built the one place an epsilon may be printed — three required keyword-only args with no defaults, both multiplicities read from the committed Phase 21 record, basic composition that refuses the control's absent eps — and the AST gate that makes "one place" checkable, with the grep-RED / AST-GREEN contrast measured on the real frozen `mitigation_gate.py` rather than asserted.**

## Performance

- **Duration:** ~32 min
- **Started:** 2026-08-31T17:52Z
- **Completed:** 2026-08-31T18:24Z
- **Tasks:** 2/2
- **Files created:** 2 (0 modified)

## Task Commits

1. **Task 1: `scripts/phase25_epsilon.py` — the three-required-kwarg helper and the dual-granularity sentence** — `a28cf5f` (feat)
2. **Task 2: `tests/test_phase25_epsilon.py` — D-30's AST gate, with grep-RED / AST-GREEN demonstrated** — `0cc7c53` (test)

## Files Created

- `scripts/phase25_epsilon.py` — the sanctioned epsilon surface. `report_epsilon`, `dual_granularity_sentence`, `curve_total`, `point_epsilon_for_sigma`, `with_replacement_clause`, `sigma_zero_epsilon_absence`; constants `SELECTION_ACCOUNTED`, `SELECTION_ACCOUNTED_REASON`, `CONTROL_HAS_NO_EPSILON`, `TOTAL_CROSSES_BOTH_LEGS`, `CONTROL_EPSILON_FIELD_FORM`, `SIGMA_ZERO_PRECEDENT_CORRECTION`, `EPSILON_NAMES`.
- `tests/test_phase25_epsilon.py` — five tests: the live gate, the frozen-gate demonstration, the planted RED, the exemption boundary, the signature contract.

## Verification Evidence

### Full suite

```
1672 passed, 1 skipped, 83 warnings in 379.59s (0:06:19)
```

**Delta vs the 1667 passed / 1 skipped baseline: +5 passed, +0 skipped.** Exactly the five tests this plan adds. Zero failures.

### The plan file's own baseline line is stale

`25-03-PLAN.md`'s `<environment>` block states **"Baseline 1647 passed, 1 skipped"**. The orchestrator's prompt states the post-25-01 baseline as **1667 passed, 1 skipped**. The measured post-25-03 total is **1672 passed, 1 skipped**, which is +5 on the orchestrator's figure. The plan's 1647 predates several waves and is not the number to compare against.

### `tests/test_phase25_epsilon.py`

```
5 passed in 0.05s
```

**Zero skipped.** Node ids:

```
test_no_bare_epsilon_is_printed_outside_the_helper PASSED
test_grep_goes_false_red_where_the_ast_gate_is_green PASSED
test_the_epsilon_gate_fires_on_a_planted_bare_print PASSED
test_the_exemption_is_the_helper_module_not_the_package PASSED
test_report_epsilon_has_three_keyword_only_args_with_no_defaults PASSED
```

### The two measured numbers from the demonstration (`scripts/mitigation_gate.py`, real, unmodified)

| Channel | Measurement | Value |
|---|---|---|
| **Text** | `str.count("epsilon")` over the raw source | **42** (plan requires ≥ 25) |
| **AST** | nodes resolving against `EPSILON_NAMES` under exact membership | **0** |

Supporting breakdown, all asserted in the test:

- **26** of the 42 occurrences live inside `ast.Constant` string values.
- Per-function, exactly as D-30 records: `exists_clearing_point` = **2**, `capacity_comparison` = **23** — the 25 the plan names.
- The remaining channel: `str.count` in comments = 1, in identifier tokens = 11, string constants = 26.

**Consequence, which is the finding:** a textual gate applied to `scripts/mitigation_gate.py` today reports a violation that does not exist. This is the class RPT-02 exists to close; `.planning/REQUIREMENTS.md`'s RPT-02 row records four independent instances in Phase 20 alone. `scripts/phase25_prereg.py` (committed by 25-01) is this phase's second natural instance: **10** textual occurrences of `epsilon`, **0** resolving names.

### The planted RED, watched — verbatim failure message

Planted into `tmp_path` (never into a real repo file) as `phase25_planted.py`:

```python
def render(point_epsilon):
    print(f"epsilon={point_epsilon}")
```

The gate's verbatim failure message:

```
/var/folders/7k/hgktxwvx6p54ch16qtg7pwlw0000gn/T/tmpaxu2cuqq/phase25_planted.py:2 in render(): bare epsilon name 'point_epsilon' reaches a print/f-string/.format/% outside phase25_epsilon.py. Route it through phase25_epsilon.report_epsilon(...), which renders the point epsilon, the curve total, selection_accounted, the privacy unit, the sampler statement and both multiplicities in one sentence.
```

It names the file, the line number (`:2`), the function (`render()`) and the offending identifier (`'point_epsilon'`).

**`git status --porcelain scripts/` was empty immediately afterwards** — asserted inside the test itself (`subprocess.run(..., cwd=_ROOT, check=True)`, `assert completed.stdout == ""`), not merely recorded here.

### Task 1 acceptance criteria (7/7)

| Criterion | Result |
|---|---|
| Omitting the third kwarg exits non-zero with a `TypeError` naming it | `TypeError: report_epsilon() missing 1 required keyword-only argument: 'selection_accounted'`, exit 1 |
| `dual_granularity_sentence` contains `262.9437465865647`, `207.0180229382851`, `RECORDED, NOT RESOLVED` | `both multiplicities named`, exit 0 |
| `curve_total([519.6981942303134, 159.44148628736576], delta=DELTA)` prints a `(sum, 2*1e-5)` pair | `(679.1396805176792, 2e-05)`, exit 0 |
| `curve_total([1.0, None], ...)` exits non-zero naming `CONTROL_HAS_NO_EPSILON` | `ValueError: curve_total: entry 1 of 2 is None ... CONTROL_HAS_NO_EPSILON: ...`, exit 1 |
| AST: `report_epsilon` has 0 positional, 3 kwonly, all `kw_defaults` `None` | `3 kwonly, no defaults`, exit 0 |
| `SELECTION_ACCOUNTED is False`, `'null' in CONTROL_EPSILON_FIELD_FORM`, `len(EPSILON_NAMES)` ≥ 5 | `6`, exit 0 |
| `git diff --exit-code` on the four ancestry-guarded modules | exit 0 |

### Task 2 acceptance criteria (8/8)

| Criterion | Result |
|---|---|
| `pytest tests/test_phase25_epsilon.py -v` exits 0, zero skipped | `5 passed in 0.05s` |
| Both measured numbers quoted in the SUMMARY | 42 text / 0 AST, above |
| Verbatim planted-RED message + empty `git status --porcelain scripts/` | above |
| Both demonstration node ids present by AST | `both demonstrations committed`, exit 0 |
| `ast.Call` count over the test file | `89`, exit 0 |
| `grep -c` appears only in prose, resolved by AST | `grep -c appears only in prose, never in executable code`, exit 0 |
| `pytest tests/ -q` reports 0 failed | `1672 passed, 1 skipped` |
| Frozen modules + `pyproject.toml` byte-unchanged; `make lint` | both exit 0 |

### Frozen-artifact and RPT-03 checks

```
git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py \
  scripts/mitigation_unit.py scripts/phase18_extraction.py pyproject.toml    # exit 0
make lint                                                                    # exit 0 (All checks passed! / 234 files already formatted)
```

`scripts/mitigation_gate.py` was opened for **reading only**, by `ast.parse` and `Path.read_text`. Zero package installs; `pyproject.toml` byte-unchanged.

## Deviations from Plan

### 1. [Plan-fidelity — measured correction] The plan's `ast.Name` count of 0 holds under EXACT name matching, not under the substring rule the plan's own Task 2(b) prescribes

- **Found during:** Task 1 (pre-implementation measurement), acted on in Task 2.
- **What the plan states:** must_haves — *"`scripts/mitigation_gate.py` carries `epsilon` inside 25 string literals with an `ast.Name` count of 0"*. Task 2(b) then prescribes the measurement as *"count `ast.Name` nodes whose `id` **contains** `epsilon` plus `ast.arg` nodes likewise; assert that count is 0."*
- **Measured on the real file:** substring matching yields **11** hits (9 `ast.Name` + 2 `ast.arg`) across three identifiers — `epsilon_independent_of_n` (`:1069`, `:1109`), `fallback_epsilon_tolerance` (`:1070`, `:1143`, `:1163`, `:1167`, `:1173`) and `epsilon_gap` (`:1162`, `:1163`, `:1166`, `:1172`). Exact matching — `id == "epsilon"`, and more generally membership in `EPSILON_NAMES` — yields **0**.
- **Resolution:** the AST channel resolves by **exact membership in `EPSILON_NAMES`**, which is the resolver the shipped gate itself uses. A demonstration that used a different resolver from the gate would be a demonstration about a different function than the one CI runs (`tests/test_phase20_prereg.py:153-155`'s rule). The plan's headline figure — `ast.Name` count 0 — reproduces exactly under that resolver, and the substring reading is **also asserted**, as an exact identifier set, so the discrepancy is committed in the test rather than only in this SUMMARY. The plan's own Task 1(e) instruction ("this is a NAME set, not a phrase set, precisely because the gate is an AST walk") is what settles the ambiguity in favour of exact membership.
- **Files:** `scripts/phase25_epsilon.py` (`EPSILON_NAMES` docstring), `tests/test_phase25_epsilon.py` (`_epsilon_identifier`, `test_grep_goes_false_red_where_the_ast_gate_is_green`).
- **Commits:** `a28cf5f`, `0cc7c53`.

### 2. [Plan-fidelity — measured correction] `results/phase23_sigma_zero.json` has **51** top-level keys, not the 43 the plan and §C5 state

- **Found during:** Task 1.
- **Issue:** the plan states in three places that the record has *"43 top-level keys, none named `epsilon`"*. Measured at execution: **51** top-level keys. The load-bearing half — **no key named `epsilon` exists** — reproduces exactly. (The two keys a naive substring search matches are `composed_steps` and `clip_bind_count_covers_steps`, both containing `eps` only inside the word `steps` — itself a small instance of the same textual-matching hazard the AST gate closes.)
- **Fix:** `SIGMA_ZERO_PRECEDENT_CORRECTION` records both readings and names which half the decision rests on, and `sigma_zero_epsilon_absence()` **re-measures both at call time** so the paragraph is checkable rather than quotable. The count was not hardcoded in either spelling.
- **Impact:** none on the decision. D-29's cited precedent still does not exist, so `CONTROL_EPSILON_FIELD_FORM` remains this phase's own decision rather than an inherited convention — which is exactly what §C5 concluded.
- **Files:** `scripts/phase25_epsilon.py`. **Commit:** `a28cf5f`.

### 3. [Rule 2 — missing validation] `curve_total` refuses `math.inf` as well as `None`

- **Found during:** Task 1.
- **Issue:** the plan requires refusing *"an input list containing a `None` ε (the control)"*. But `epsilon_for(0.0, 200, 1e-5)` returns `math.inf`, not `None` — so a caller that passes accountant output straight through (rather than a record's parsed JSON) would hand `curve_total` an `inf` and get `inf` back as a "total", which reads as a computed bound rather than a refusal. That is T-25-14 (the control silently entering the total) through a second door.
- **Fix:** the guard is `value is None or not math.isfinite(value)`, and both spellings raise the same `ValueError` naming `CONTROL_HAS_NO_EPSILON`. One guard, both doors.
- **Files:** `scripts/phase25_epsilon.py::curve_total`. **Commit:** `a28cf5f`.

### 4. [Rule 2 — hardened beyond the plan] The exemption test also rejects the helper's exact basename at another path

- **Found during:** Task 2.
- **Issue:** the plan's test (d) plants a **near-miss** name (`phase25_epsilon_helper.py`). A near-miss only proves the exemption is not a *prefix* match. The stronger property — the exemption is a resolved path — is only proved by a file with the **exact basename** at a different path.
- **Fix:** `test_the_exemption_is_the_helper_module_not_the_package` plants both, and additionally asserts the real helper *is* exempt, so the test cannot pass by the exemption being broken entirely.
- **Files:** `tests/test_phase25_epsilon.py`. **Commit:** `0cc7c53`.

### 5. [Rule 1 — correctness] Findings are deduplicated on `(lineno, col_offset, identifier)`

- **Found during:** Task 2.
- **Issue:** a name inside `print(f"...")` sits under **both** the `print` `ast.Call` and the `ast.JoinedStr`, and `ast.walk` yields both, so one bare epsilon produced two identical findings. The plan's own RED assertion ("assert it fails naming that function and that line") would have read a doubled count.
- **Fix:** collect into a dict keyed on `(lineno, col_offset, identifier)`. One bare epsilon is one finding.
- **Files:** `tests/test_phase25_epsilon.py::_epsilon_renderings`. **Commit:** `0cc7c53`.

### 6. [Cosmetic] Four docstring lines shortened to satisfy `ruff` E501 (line-length 100)

No behavioural change. `make lint` exits 0.

## Notes for Downstream Plans

- **`report_epsilon` is the only sanctioned rendering.** Any Phase-25 module that prints an epsilon must route through it. The gate at `tests/test_phase25_epsilon.py::test_no_bare_epsilon_is_printed_outside_the_helper` collects `scripts/phase25_*.py` **by glob** plus `scripts/plot_phase25.py` if it exists, so a module added by a later plan is covered automatically with no test edit.
- **`CONTROL_EPSILON_FIELD_FORM` is the contract for the control-point record:** the key `"epsilon"` with the value `null`, **explicitly**, plus a sibling `"epsilon_omitted_reason"`. D-31's ordered `point_keys` hard equality depends on the control carrying the same key set as every other point.
- **`curve_total` takes the points ACTUALLY PUBLISHED and crosses both legs.** The caller must exclude the control deliberately; the function will not skip it.
- **`EPSILON_NAMES` currently holds 6 names.** A later plan that introduces a new epsilon-bearing identifier must add it to that tuple, or the gate will not see it.

## Known Stubs

None. Both artifacts are complete and exercised by committed tests.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary. The two files read three committed artifacts (`results/phase21_multiplicity.json`, `results/phase23_sigma_zero.json`, `scripts/mitigation_gate.py`) read-only and write nothing outside `tmp_path`.

## Threat Register Coverage

| Threat ID | Disposition | Where mitigated |
|---|---|---|
| T-25-12 | mitigate | Three required kwargs with no defaults (`report_epsilon`, proved by AST **and** at runtime) plus the AST walk over every `scripts/phase25_*.py`, RED watched in `tmp_path` |
| T-25-13 | mitigate | grep-RED / AST-GREEN measured on the real frozen gate (42 text / 0 AST), both counts asserted in the test, so the AST choice is evidence rather than preference |
| T-25-14 | mitigate | `curve_total` refuses `None` **and** `math.inf` naming `CONTROL_HAS_NO_EPSILON`; `CONTROL_EPSILON_FIELD_FORM` pins the explicit `null` |
| T-25-15 | mitigate | Both figures read from `results/phase21_multiplicity.json`; its `RECORDED, NOT RESOLVED` status and `epsilon_note` carried through verbatim; no example-level epsilon number invented |
| T-25-SC | accept | Zero installs; `pyproject.toml` byte-unchanged (verified by `git diff --exit-code`) |

## Self-Check: PASSED

Files:

```
FOUND: scripts/phase25_epsilon.py
FOUND: tests/test_phase25_epsilon.py
FOUND: .planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-03-SUMMARY.md
```

Commits:

```
FOUND: a28cf5f  feat(25-03): add the sanctioned epsilon surface with three required kwargs
FOUND: 0cc7c53  test(25-03): add D-30's AST epsilon gate with grep-RED / AST-GREEN measured
```

`.planning/STATE.md` and `.planning/ROADMAP.md`: **untouched** by this plan (orchestrator-owned).
The pre-existing uncommitted `.gitignore` modification was left alone; only the two files this plan created were staged.
