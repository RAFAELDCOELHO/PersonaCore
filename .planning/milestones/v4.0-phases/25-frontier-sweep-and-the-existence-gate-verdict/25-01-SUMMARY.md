---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 01
subsystem: testing
tags: [pre-registration, ast-guard, tripwire, dp-sgd, reproduction-halt, one-attempt]

# Dependency graph
requires:
  - phase: 23-dp-sgd-sweep-and-the-matched-control
    provides: "results/phase23_sigma_zero.json (790/1008 at seed 1337, C=1e6, clip_bind_count 0) and results/phase23_matched_control.json (the four declared_differences D-04 imports by path + digest)"
  - phase: 20-the-three-condition-gate
    provides: "scripts/mitigation_gate.py — exists_clearing_point's denominator string, CAPACITY_BRANCHES, ratchet_k, promote_to_full_fidelity"
  - phase: 22-dp-sgd-mechanism
    provides: "personacore.privacy.dpsgd.DPSGD — PRE-PASS 1's four numeric-domain refusals, which fire before the model is read"
provides:
  - "scripts/phase25_prereg.py — the reproduction HALT (D-07), the per-point one-attempt refusal (D-10), and the four rules committed before any point exists (D-11, D-40, D-37, D-04)"
  - "tests/test_phase25_prereg.py — two natural watched REDs, one planted watched RED against a scratch copy, and CTRL-02's millisecond clip-domain proxy"
  - "POINT_RECORD_GLOB / point_record_path() — the per-point record path derivation every later Phase-25 plan resolves its paths from"
  - "DISK_PRECHECK_BYTES — the 5 GB precheck sized against the measured adapter PLUS resume checkpoint"
affects: [25-02 through 25-22, phase 26 canary audit, phase 28 report]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "wave-1 pre-registration module: stdlib + literal-only mitigation_budget, no torch, no device, no network"
    - "AST-resolved structural guards over the repo's own source, never grep"
    - "planted RED against a tmp_path scratch copy when no natural RED exists"

key-files:
  created:
    - scripts/phase25_prereg.py
    - tests/test_phase25_prereg.py
  modified: []

key-decisions:
  - "D-04's tripwire matches forbidden ASSERTION names exactly and PAIRING markers as substrings — measured, not stylistic"
  - "matched_arm removed from the seam-off marker set because it produced two false positives in scripts/phase23_run.py"
  - "PROMOTION_RULE's K values are AST-proved to be attribute reads on mitigation_budget, not retyped literals"
  - "PUBLICATION_OBLIGATION's denominator clause is asserted against exists_clearing_point's own returned claim"

patterns-established:
  - "Watched-RED discipline: a refusal is INVOKED and its message asserted on discriminating substrings, never on the full string"
  - "Pin-vs-record: every pinned reading is proved against the artifact it names (reproduction_source_reading), never against itself"

requirements-completed: [CTRL-01, CTRL-02]

# Metrics
duration: 47min
completed: 2026-08-31
---

# Phase 25 Plan 01: Pre-Registration Summary

**Phase 25's four irreversible rules are committed while `git ls-files 'results/phase25_point_*.json'` is still empty — the reproduction HALT under hard `==` on integer counts, the per-point one-attempt refusal with Phase 25's own glob, the promotion/publication/canary obligations, and D-04's armed bit-identity tripwire, all three refusals watched firing.**

## Performance

- **Duration:** ~47 min
- **Started:** 2026-08-31T14:45:00Z
- **Completed:** 2026-08-31T15:32:00Z
- **Tasks:** 3 of 3
- **Files created:** 2 (`scripts/phase25_prereg.py`, `tests/test_phase25_prereg.py`)

## Accomplishments

- **`prove_reproduction(k, n)` HALTS at ZERO sweep points on a one-count miss**, in both directions and on the denominator, with the four declared differences read LIVE from `results/phase23_matched_control.json` (sha256 `4478005f…`) rather than retyped. Watched firing on three parametrizations.
- **`prove_first_attempt(tracked, point_key=)` refuses a second attempt at ONE point** with Phase 25's own `results/phase25_point_*.json` in its own four-clause refusal text, and is asserted NOT to name Phase 23's glob — §C6's whole point, checked rather than assumed. The spent `scripts/phase23_matched_prereg.py` is neither imported nor modified.
- **D-04's tripwire is armed over every `.py` under `tests/` and `scripts/`** and has been watched firing against a `tmp_path` scratch copy while the real tree stayed clean. Measured: 2,697 function bodies scanned, **zero** full hits and **eleven** two-of-three near misses.
- **CTRL-02's cheap proxy moved into wave 1** (from 25-11 Task 3), so a clip-domain error can never be discovered mid-sweep: 5 cases in **0.60 s** with `model=None`, no device, no GPU.
- **`DISK_PRECHECK_BYTES` corrects D-37's 42× under-estimate** — sized at 5 GB against the measured 1,352,069 B adapter *plus* the 59,691,603 B resume checkpoint (44 points ≈ 2,685,921,568 B), both figures read off real files on this machine.

## Task Commits

1. **Task 1: the reproduction HALT and the per-point one-attempt refusal** — `7664879` (feat)
2. **Task 2: the four rules that must exist before any point does** — `a6ded2e` (feat)
3. **Deviation fix: tune D-04's tripwire marker sets against the measured tree** — `61697e7` (fix)
4. **Task 3: three watched refusals, two natural and one planted** — `b0f2db7` (test)

## Files Created/Modified

- `scripts/phase25_prereg.py` — Phase 25's pre-registration. `prove_reproduction` / `reproduction_source_reading` / `declared_differences` / `declared_differences_digest` (D-07, D-04's import), `point_record_path` / `prove_first_attempt` (D-10), and the four dated constants `PROMOTION_RULE` (D-11), `PUBLICATION_OBLIGATION` (D-40), `CANARY_RESERVATIONS` + `DISK_PRECHECK_BYTES` (D-37), `BIT_IDENTITY_FORBIDDEN_ASSERTIONS` + the two marker sets + `BIT_IDENTITY_EXPECTED_DISAGREEMENT` (D-04).
- `tests/test_phase25_prereg.py` — 20 tests: both reproduction branches, the four one-attempt cases, the armed tripwire plus its planted RED, CTRL-02's five clip-domain cases, and three structural assertions over the committed rules.

## Verification Evidence

### Test counts (literal pytest lines)

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase25_prereg.py -v` | **`20 passed in 2.33s`** — **0 skipped** |
| `.venv/bin/python -m pytest tests/test_phase25_prereg.py -k clip_domain -v` | **`5 passed, 15 deselected in 0.60s`** |
| `.venv/bin/python -m pytest tests/test_phase25_prereg.py -k "reproduction_miss" -v` | **`3 passed, 17 deselected in 0.50s`** |
| `.venv/bin/python -m pytest tests/ -q` | **`1667 passed, 1 skipped, 83 warnings in 380.46s (0:06:20)`** — 0 failed |

The full-suite figure is exactly **+20** over the plan's stated `8dd6415` baseline of *1647 passed, 1 skipped* — the 20 tests this plan adds and nothing else.

### The watched RED — `prove_reproduction(789, 1008)`, captured verbatim

```
[phase25_prereg] D-07 HALT — THE SWEEP IS HALTED: it HALTS at zero sweep points, and zero non-control points will run.
  expected reading : 790/1008 (results/phase23_sigma_zero.json, primary.k/primary.n)
  observed reading : 789/1008
  comparison       : hard `==` on integer counts — no tolerance, because the reading is a COUNT
  recipe pinned    : clip_norm 1000000.0, clip_bind_count 0, composed_steps 200, records_per_lot 8, seed 1337

  SUSPECT #1: the ratio-0.0 byte-identity assertion (`build_bins(..., adversarial_ratio=0.0)` against the no-kwarg build): token sha256 f146d426..., mask sha256 a2c4771f..., 176 episodes / 7,581 tokens. If that pair no longer reproduces, the corpus under EVERY reading has moved and the count difference is a symptom rather than the defect.

  THEN THE 4 DECLARED DIFFERENCES, as the starting investigation list — read live from results/phase23_matched_control.json (sha256 4478005fa5480646d830ac56d615ab361b1e1a7b8becfd6d887bec33deba504c), never retyped:
    1. the `dp_noise_rng` checkpoint slot
    2. the arm NAME, and therefore the csv / checkpoint / adapter paths
    3. the DP seam's own object graph — DPSGD constructed on one side, None on the other
    4. the two end-of-run `masked_perplexity` sweeps, and the six per-seed diagnostic fields they produce

  The control must reproduce Phase 23's reading EXACTLY. It does not. The cause must be ROOT-CAUSED AND FIXED before any further point runs — this is not a warning and there is no override flag. The 43 further points are interpretable only RELATIVE to this control, so an unexplained control does not produce one bad point, it produces 43 uninterpretable ones. Stop-and-fix is reversible; publish-compromised is not.
```

Exit code **1**; stderr carries `zero`, `f146d426` and `a2c4771f`. The record digest printed by the halt (`4478005f…`) matches `results/phase23_matched_verdict.json`'s own `control_record_file_sha256` — the import is against the same bytes Phase 23 recorded.

### D-04's planted tripwire — the verbatim failure, and the tree left untouched

```
D-04 TRIPWIRE FIRED — a committed function asserts BIT-IDENTITY between the sigma=0 point and the seam-off path:
  <tmp_path>/test_planted_bit_identity.py::test_sigma_zero_adapter_is_the_seam_off_adapter — assertion ['equal'], sigma=0 marker(s) ['sigma_zero_adapter'], seam-off marker(s) ['dp_fn', 'seam_off_adapter']

WHAT THE CORRECT ASSERTION LOOKS LIKE: BOUNDED DISAGREEMENT, NEVER EQUALITY. Phase 23's PROBE 2 measured 72/72 LoRA tensors agreeing to 2.178e-07 RELATIVE at sigma=0 with a non-binding C — agreement to a bound, not bit identity. The distinction is the record itself: declared difference #3 states that 'sigma=0 is not the control computation with a zero added to it' is TRUE OF THE CODE PATH and FALSE OF THE ARITHMETIC. An equality assertion would overwrite that measured floating-point non-associativity record with a claim the measurement does not support, and the next person to see the two paths disagree would read a real property as a regression
```

`git status --porcelain tests/ scripts/` **immediately after that test run** returned only `?? tests/test_phase25_prereg.py` — the new, not-yet-committed test file itself. No real file was modified, and after the Task-3 commit the same command returns **empty**. The planted module never left `tmp_path`; the same `_assert_no_bit_identity_assertions` body that fired on it is re-run against the real tree in the same test and passes.

### CTRL-02's proxy, run standalone

```
$ .venv/bin/python -c "... [4 clip_norm refusals with model=None] ..."
4 clip_norm values refused with no model and no GPU
```

At `clip_norm=1000000.0` the same call proceeds past PRE-PASS 1 and raises `AttributeError: 'NoneType' object has no attribute 'named_parameters'` — the positive control that makes the parametrized refusal non-vacuous. The `inf` case additionally carries `std nan`.

### Structural / frozen-module gates

| Gate | Result |
|---|---|
| `git diff --exit-code -- mitigation_gate.py mitigation_accountant.py mitigation_unit.py phase18_extraction.py phase23_matched_prereg.py pyproject.toml` | exits **0** — byte-unchanged (RPT-03 streak intact) |
| `git ls-files 'results/phase25_point_*.json' \| wc -l` | **0** |
| `git log --oneline -- 'results/phase25_point_*.json' \| wc -l` | **0** — no point record existed when the rules landed |
| AST: no `phase23_matched_prereg` import in `scripts/phase25_prereg.py` | `[]` |
| AST: no `isclose`, no `abs`, no `torch` name/attr in the module | passes |
| AST: no `subprocess` call shelling out to `grep` in the test file | passes |
| `make lint` | **exits 0** (232 files formatted, all ruff checks pass) |

## Decisions Made

- **The tripwire's matching rule is asymmetric, and it is measured.** Forbidden assertion names (`equal`, `assert_close`, `assert_allclose`, `allclose`, `sha256`, `hexdigest`) match **exactly** — they are call names and appear as themselves; widening them to substrings would catch an identifier named `equality`. The two pairing marker sets match as **substrings of an identifier**, because the natural spelling of the violation is `sigma_zero_adapter` / `seam_off_adapter` rather than the bare marker. Exact-matching the markers would miss the very form being forbidden.
- **A `BIT_IDENTITY_SIGMA_ZERO_MARKERS` / `BIT_IDENTITY_SEAM_OFF_MARKERS` split, requiring one marker from EACH side.** The plan named only the forbidden-assertion tuple; a tripwire needs the pairing markers as constants too or it cannot be resolved by AST at all. Requiring both sides is what keeps the guard off the many honest functions that compare tensors for unrelated reasons — measured at eleven two-of-three near misses versus zero full hits.
- **`audit_target_rule` (D-37 iii) is a three-clause rule that resolves in every outcome**, including the pre-registered null: restrict to n=8 points (only they have out-of-corpus canaries), take the first `point_keys`-ordered PASS, and if none passed take the first n=8 point in `point_keys` order. `point_keys` is itself an ordered pin asserted under hard equality at the artifact's single write, so "first" is not a re-orderable word.
- **`PUBLICATION_OBLIGATION` carries seven `(field_path, why)` pairs, not four.** Three of the seven field paths (`epsilon_report.curve_total_epsilon`, `epsilon_report.selection_accounted`, `epsilon_report.control_has_no_epsilon`) are already pinned by 25-19's own acceptance criteria; the remaining four follow that plan's stated vocabulary and are declared as an obligation on the assembly, with `PUBLICATION_OBLIGATION_SCOPE` stating that a path which does not resolve is a RED test in Phase 28 rather than a licence to paraphrase.
- **`point_record_path(point_key)` was added** even though the plan named only the glob. `prove_first_attempt`'s unit is the POINT, so the refusal must key on *this* point's record path — without a derivation the rule would either refuse every point after the first or compare against a string literal at each call site, which is the "plans naming artifact paths the code refuses" class this repository has already been bitten by.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] D-04's tripwire marker set could not go green on the tree it guards**

- **Found during:** Task 3 (writing the tripwire), by probing the marker sets against the real tree before pinning them.
- **Issue:** The seam-off set committed in Task 2 contained `matched_arm`. Under substring matching that produced **two false positives** in `scripts/phase23_run.py`: `train_matched_control` (a `torch.equal` **training canary** comparing a parameter with its own pre-step snapshot, at `:1403` and `:1408`) and `matched` (a `hashlib.sha256(...).hexdigest()` over a per-seed block, at `:2330`). Neither asserts anything about σ=0 against the seam-off path. A guard that cannot go green on the tree it guards is not armed — it is broken, and the only ways to ship it would have been to weaken the guard after seeing it fire or to edit two functions in a Phase-23 driver to satisfy a Phase-25 test.
- **Fix:** Removed `matched_arm` from `BIT_IDENTITY_SEAM_OFF_MARKERS` and recorded the removal, with the two functions named, **in place** in the module rather than dropping it silently. Phase 25's seam-off comparator gets its own arm name under D-06, so `dp_fn` and `seam_off` are the identifiers that actually name that path. Also documented the exact-vs-substring asymmetry that the measurement forced.
- **Files modified:** `scripts/phase25_prereg.py`
- **Verification:** Re-measured after the change — 2,697 function bodies scanned, **0** full hits, **11** two-of-three near misses (among them `tests/test_phase22_dpsgd.py::_identity_run`, which already carries `equal` and `dp_fn` and is one σ=0 name away from being exactly the assertion D-04 forbids). `tests/test_phase25_prereg.py::test_no_committed_test_asserts_sigma_zero_seam_off_bit_identity` passes.
- **Committed in:** `61697e7` (its own commit, between Task 2 and Task 3)

---

**Total deviations:** 1 auto-fixed (1 × Rule 1).
**Impact on plan:** None on scope. The correction was necessary for the guard to be armable at all, and it is the kind of finding the plan's own "measured rather than argued" discipline calls for. No ancestry-guarded module was touched.

## Issues Encountered

- **The plan's acceptance criterion `-k clip_domain` requires ≥ 5 collected cases**, which the plan's own suggested test name (`test_the_control_clip_norm_clears_the_domain_pre_pass`) does not satisfy — `clip_domain` is not a contiguous substring of it, so the selector would have collected only the four parametrized refusals. Renamed to `test_the_control_clip_norm_clears_the_clip_domain_pre_pass`, which collects the intended 5. This is a naming correction, not a scope change.
- **Task 1's plan text lists `subprocess` among the permitted imports.** It is not imported: `prove_first_attempt` takes the caller's `git ls-files` result, exactly as its Phase-23 predecessor does, so the module runs no subprocess and stays unit-testable without a repository. An unused import would also have failed `ruff` F401.

## Known Stubs

None. Every constant in `scripts/phase25_prereg.py` is a committed value or a live read from an existing record; no placeholder, no TODO, no empty-collection-flowing-to-a-consumer.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema at a trust boundary was introduced. The plan's own register (T-25-01 … T-25-SC) is fully covered by the guards above, and T-25-SC's "zero installs" holds — `pyproject.toml` is byte-unchanged.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Wave 1's blocking obligation is discharged: **the four rules whose value depends entirely on existing before the data now exist, and the repository can prove it** (`git log --oneline -- 'results/phase25_point_*.json'` returns nothing at their commits).

Ready for the later Phase-25 plans:

- `POINT_RECORD_GLOB` / `point_record_path()` are the paths the driver (25-09 onwards) must resolve its per-point record names from — **do not spell them at a call site**.
- `PROMOTION_RULE["curve_k"]` / `["full_k"]` are attribute reads on `mitigation_budget`; a later plan that retypes 16 or 48 goes RED at `test_promotion_rule_reads_the_budget_pins`.
- `DISK_PRECHECK_BYTES` is the figure the sweep's disk precheck must clear before point 1, not after point 30.
- **The tripwire is live.** Any later Phase-25 plan that pairs `torch.equal` / `assert_close` / a sha256 equality with both a σ=0 and a seam-off identifier in one function body fails `test_no_committed_test_asserts_sigma_zero_seam_off_bit_identity`. The correct assertion is bounded disagreement (2.178e-07 relative), never equality.
- `PUBLICATION_OBLIGATION`'s seven field paths are an obligation on 25-19's artifact assembly; a path that does not resolve there is a Phase-28 RED.

No blockers.


## Self-Check: PASSED

All three created files verified present on disk; all commits (`7664879`, `a6ded2e`, `61697e7`, `b0f2db7`, `3738e0d`) verified present in `git log --all`. `git log --name-only 7664879^..HEAD` confirms **no commit in this plan touched `.planning/STATE.md`, `.planning/ROADMAP.md` or `.gitignore`** — the two pre-existing working-tree modifications to `STATE.md` and `.gitignore` were present before this plan started and are left for the orchestrator.

---
*Phase: 25-frontier-sweep-and-the-existence-gate-verdict*
*Completed: 2026-08-31*
