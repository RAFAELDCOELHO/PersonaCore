---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: "09"
subsystem: privacy/budget-pin
tags: [noise-floor, pre-registration, import-ceiling, literal-only, provenance, watched-red, cal-02]
requires:
  - "results/phase23_control_floor.json — D-03's measured floor and its five per-seed counts (23-08)"
  - "scripts/phase23_prereg.py::noise_floor / CONTROL_FLOOR_RECORD / FLOOR_PROVENANCE_KEYS / sigma_zero_verdict (23-03, EDIT-ONCE, read-only)"
  - "tests/test_phase20_prereg.py::_GATE_MODULES + the import-graph guard (Phase 20, the register that admits this module)"
  - "tests/test_phase23_budget.py — 23-02's transitive probe and its zero-headroom ceiling block"
provides:
  - "scripts/mitigation_budget.py — Phase 23's RESOURCE budget module; zero imports, literal assignments only"
  - "scripts/mitigation_budget.py::CONTROL_NOISE_FLOOR = 0.05357142857142849"
  - "scripts/mitigation_budget.py::CONTROL_NOISE_FLOOR_PROVENANCE — all 8 FLOOR_PROVENANCE_KEYS + record_file_sha256, ready to pass straight into sigma_zero_verdict"
  - "tests/test_phase23_budget.py — the literal-only AST guard, the re-derivation guard, the protected-but-not-frozen guard, the zero-headroom equality, and a permanent one-ULP watched RED"
affects:
  - "23-10 (reads CONTROL_NOISE_FLOOR + its provenance through phase23_prereg.sigma_zero_verdict)"
  - "23-13 (writes the Z values into this same module — which is why it must stay unfrozen)"
tech-stack:
  added: []
  patterns:
    - "a measured constant pinned as a literal beside a _PROVENANCE SIBLING CONSTANT (not a comment), so a consumer can read it and a test can assert on it"
    - "an import ceiling asserted by EQUALITY rather than subset, so a SHRINKING union is caught as well as a growing one"
    - "a watched-RED made permanent by loading a mutated copy from tmp_path instead of editing the tracked file"
key-files:
  created:
    - scripts/mitigation_budget.py
  modified:
    - tests/test_phase23_budget.py
decisions:
  - "The floor is pinned as a literal in a zero-import, literal-only module — phase19_floor.py's shape, which satisfies the zero-headroom mitigation_*.py import ceiling for free"
  - "The module is deliberately NOT registered as a prereg_artifact=: protected, not frozen, because 23-13 must still write the Z values into it"
  - "PLAN DEFECT FOUND: the record's `record_sha256` is an INPUTS digest, not the file's own hash. Both digests are carried under distinct names and both are checked live"
  - "CAL-02 NOT ticked — its text requires Z set FROM the cost measurements, and 23-11 has not measured them yet. 23-13 closes it"
  - "state.add-decision deliberately not called (23-07's measured practice); these decisions are hand-written"
patterns-established:
  - "the derivation stated in words in a comment block, the checkable fields as data in a sibling dict, and NOTHING pinned twice"
requirements: []
metrics:
  duration: "~25 min"
  completed: 2026-08-27
  tasks: 2
  files: 2
  commits: 3
---

# Phase 23 Plan 09: Pin the Measured Noise Floor Summary

D-03's measured seed-to-seed noise floor `0.05357142857142849` is now a literal in a zero-import,
literal-only `scripts/mitigation_budget.py`, with a `_PROVENANCE` sibling that re-derives from the
committed record through the blindly-committed reduction under exact `==` on every suite run — and
it landed while `git ls-files results/phase23_sigma_zero.json` returns nothing.

## What Shipped

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | The floor, its provenance, zero imports | `dc2147f` | `scripts/mitigation_budget.py` |
| 2 | The five structural guards | `14c9c3d` | `tests/test_phase23_budget.py` |

## The Number, With Its Denominator

The pin is the RANGE over five per-seed taught-recall-ON readings, each a count over **1008 draws**
(112 questions x 9 draws):

| seed | k / n | rate |
| ---- | ----- | ---- |
| 1337 | 566/1008 | `0.5615079365079365` (the pinned central reading) |
| 2024 | 530/1008 | `0.5257936507936508` |
| 1338 | 575/1008 | `0.5704365079365079` — **max** |
| 2025 | 531/1008 | `0.5267857142857143` |
| 1339 | 521/1008 | `0.5168650793650794` — **min** |

`phase23_prereg.noise_floor` of those five = `0.5704365079365079 - 0.5168650793650794` =
**`0.05357142857142849`**, over 5040 scored draws in total, on `mps` / torch 2.7.1.

The value was **read from `results/phase23_control_floor.json` and recomputed by CALLING the
pre-registered reduction** — never retyped from the brief and never re-implemented. The test drives
the reduction from the record's own `k`/`n` **counts**, and separately asserts each recorded `rate`
equals its own `k / n`, so a record whose stored rate drifted from its evidence is caught rather
than trusted. Measured: `k/n == rate` exactly for all five seeds.

## Verification

| Check | Result |
| ----- | ------ |
| `pytest tests/test_phase20_prereg.py -k import_graph -q` — **first run with the real module in the glob** | `1 passed, 24 deselected in 0.02s` |
| `pytest tests/test_phase23_budget.py -v` | `7 passed in 0.09s`, **zero skips** (2 from 23-02 + 5 new) |
| `pytest tests/test_phase20_prereg.py -q` | `25 passed in 4.07s` |
| Full suite `pytest tests/ -q` | `1484 passed, 1 skipped in 359.20s` (baseline 1479 + my 5; the skip is the pre-existing CUDA-only fp16 AMP smoke) |
| `make lint` | `All checks passed! / 240 files already formatted` |
| AST body of `scripts/mitigation_budget.py` | `['Expr', 'Assign', 'Assign']` — walk yields only `Assign, Constant, Dict, Expr, Load, Module, Name, Store, Tuple` |
| `grep -c "^import \|^from " scripts/mitigation_budget.py` | `0` |
| `grep -n prereg_artifact tests/test_phase20_prereg.py \| grep -c mitigation_budget` | `0` — NOT registered, so NOT frozen |
| `git ls-files results/phase23_sigma_zero.json` | **empty** — the pin precedes the σ=0 artifact |
| `git diff --exit-code -- scripts/mitigation_accountant.py scripts/mitigation_gate.py scripts/phase23_prereg.py` | exit **0** — all three frozen pins untouched |
| 23-02's import isolation | `test_gate_does_not_transitively_load_the_budget` **PASSED** with a real `mitigation_budget.py` on disk and imported in the parent process |

### 23-02's guard, specifically

The plan's premise was that this module's arrival is the first real test of the `gate ->
erasure_gate -> budget` route. It stays green. The parent test process now imports
`mitigation_budget` at module scope, and that **cannot** make the probe vacuous: `_run_probe`
spawns a fresh interpreter whose `sys.modules` starts empty. That reasoning is recorded as a
comment at the import site rather than left to be re-derived.

## Watched RED — every new guard observed failing

A guard nobody has watched fail is not evidence. All five were driven against mutated inputs before
the commit, by monkeypatching the **real committed test functions**' path/register constants — so
what was observed failing is the code CI runs, not a lookalike. Nothing tracked was mutated
(`git status --short` clean apart from the intended files; the frozen `git diff --exit-code` re-run
after and still 0).

| Mutation | Guard | Observed failure |
| -------- | ----- | ---------------- |
| one stray `import json` appended | `test_budget_holds_only_literal_constants` | `scripts/mitigation_budget.py carries a Import at line 150` |
| same | `test_the_import_ceiling_still_has_zero_headroom` | union measured `['erasure_gate', 'json', 'pathlib', 'sys']` |
| same | `test_mitigation_gate_import_graph_...` (23-02's static half) | `the mitigation modules import ['json'] beyond the allow-set` |
| the gate's imports removed from the register | `test_the_import_ceiling_still_has_zero_headroom` | union measured `[]` — **the shrink direction a subset assertion cannot see** |
| a synthetic `prereg_artifact="scripts/mitigation_budget.py"` | `test_the_budget_module_is_protected_but_not_frozen` | `is registered as a prereg_artifact=` |
| the module dropped from `_GATE_MODULES` | same | `is NOT in the mitigation_*.py register` |
| one-ULP nudge to `CONTROL_NOISE_FLOOR` | `test_a_hand_edited_floor_is_detected` | **permanent, in-suite** — loads the nudged copy from `tmp_path` and observes both the `==` re-derivation and `sigma_zero_verdict` refusing it |

The shrink case is the measured justification for asserting the import union by **equality** rather
than subset: a subset assertion stays green while the union collapses, which would silently hand a
future `mitigation_*.py` sibling an import budget the ceiling block says does not exist.

## Deviations from Plan

### 1. [Rule 1 - Plan/code disagreement] `record_sha256` is an INPUTS digest, not the file's hash

- **Found during:** Task 2, resolving the acceptance criterion against the code.
- **The plan said:** assert `CONTROL_NOISE_FLOOR_PROVENANCE["record_sha256"]` equals "the sha256 of
  the committed record file computed live."
- **The code says otherwise, measured:** `scripts/phase23_run.py:967-969` sets the record's
  `record_sha256` to `sha256(json.dumps(per_seed, sort_keys=True, default=str))` — a digest of the
  five scored readings. It is **not** the artifact's own hash and could not be; a file cannot
  contain its own digest. Measured: the record's field is
  `c62d732283a3f15375de7b2ba9180c56acfcd75109b12912c17c9f083afdf0eb` and re-derives from `per_seed`
  exactly, while the file's bytes hash to
  `201cc58e574074df875513c32ee0237e143ecb356469a79581be511748a75a59`.
- **Fix:** both are carried, under distinct names, and both are checked live —
  `record_sha256` asserted equal to the record's own field, `record_file_sha256` asserted equal to
  `hashlib.sha256(path.read_bytes()).hexdigest()`. `record_sha256` keeps its name because
  `phase23_prereg.FLOOR_PROVENANCE_KEYS` requires that exact key for `sigma_zero_verdict`. The
  distinction is spelled out at the constant, because the two names are close enough to be misread
  as duplicates.
- **Commits:** `dc2147f`, `14c9c3d`

### 2. [Rule 2 - Missing critical check] The reduction SYMBOL is resolved, not string-matched

The plan asked only that `reduction` name the symbol. A string nobody dereferences is decoration,
so the test splits `"phase23_prereg.noise_floor"` and asserts
`getattr(phase23_prereg, attribute) is phase23_prereg.noise_floor` — the same function the test
re-derived the floor through. A pin citing a rule other than the one that produced it now goes red.

### 3. [Rule 2] The whole pair is driven through the consumer that will read it

`test_budget_constants_re_derive` ends by calling `phase23_prereg.sigma_zero_verdict` with the
pinned floor and its provenance. The σ=0 reading passed in is **synthetic** — the control's own
central reading, so the deviation is exactly zero — and this is labelled at the call site. It
asserts nothing about what 23-10 will measure; it proves only that the provenance dict is complete
enough to be ACCEPTED rather than refused by the frozen consumer. Without it, a missing key would
surface for the first time in 23-10, after the σ=0 run had spent its compute.

### 4. No K restatement was needed

23-02's ceiling block anticipated that a selected K would have to be restated as a literal with a
test asserting it agrees with `mitigation_gate.K_RUNGS`. **No such restatement exists in this
plan** — the only constant here derives from a Phase-23 artifact, not from the frozen gate. 23-13's
Z values are the first that will need one. Recorded so a future reader does not go looking for a
test that correctly does not exist.

## Requirements

**CAL-02 is NOT ticked, for the fourth plan running, and the reason is its text.** CAL-02 reads:
*"Z (sweep width, per-point draw budget K, step budget) is set **from** those measurements and
committed in a module separate from the gate, with the separation structurally enforced..."*

- The **second half** is now closed: the separate module exists, and the separation is enforced
  statically (the `mitigation_*.py` import-graph guard) and transitively (23-02's out-of-process
  probe), both green with the real module on disk.
- The **first half is not**: Z is not set here and cannot be. CAL-01 and CAL-05 measure the
  per-point cost in 23-11; **23-13** writes Z from those measurements into this same module. That
  is precisely why this module was left unfrozen.

Ticking CAL-02 now would claim a measurement that does not exist. `requirements mark-complete` was
therefore not called.

## Notes for 23-13

- Add the Z constants to `scripts/mitigation_budget.py` **as literals with their own `_PROVENANCE`
  siblings**, and extend `test_budget_constants_re_derive` so each re-derives from its own committed
  artifact. Do not add a placeholder before its evidence exists.
- The import ceiling is still **zero-headroom**, re-measured this plan and asserted by equality.
  A Z value that must agree with `mitigation_gate.K_RUNGS` is RESTATED as a literal with a
  provenance comment plus a test asserting the two agree — importing the gate is not available.
- `CONTROL_NOISE_FLOOR_PROVENANCE` is a working `floor_provenance` argument today; 23-10 can pass it
  to `sigma_zero_verdict` unchanged.

## gsd-sdk regressions this session (SEVENTEENTH in a row)

`git diff .planning/` read after **every** call. Snapshot taken before the first.

| Handler | Behaviour |
| ------- | --------- |
| `state.advance-plan` | Counters CORRECT (`Plan: 9 of 14` -> `10 of 14`). Flattened body `Status:` from `Executing Phase 23` to `Ready to execute`. Left `stopped_at` stale. Returned `last_updated` QUOTED. `progress.completed_plans` did NOT increment (stayed 55). |
| `state.update-progress` | `{"updated": false, "reason": "Progress field not found in STATE.md"}` — the same string since 22-12 — and its CLAIMED NO-OP still re-stamped `last_updated`, quoted. |
| `state.record-metric` | REFUSED positional args (`{"error": "phase, plan, and duration required"}`); with `--phase/--plan/--duration/--tasks/--files` the row was CLEAN: `\| Phase 23 P09 \| 25 min \| 2 tasks \| 2 files \|`. |
| `state.record-session` | CLEAN — advanced both the frontmatter `stopped_at` and the body `Stopped at:` correctly. Only re-quoted `last_updated`. |
| `state.add-decision` | **NOT CALLED**, following 23-07's measured practice (it has corrupted the phase label to `- [Phase ?]: ` on every call since 22-16 and reverts `completed_plans` from a stale read). Decisions hand-written. |
| `roadmap.update-plan-progress 23` | See the repair list below. |

All corruptions hand-repaired 1-line-for-1-line against the pre-call snapshot, split on lines and
matched with `startswith` — never a regex. `wc -l .planning/STATE.md` verified unchanged at 698.

## Self-Check: PASSED

- `scripts/mitigation_budget.py` — FOUND
- `tests/test_phase23_budget.py` — FOUND
- `.planning/phases/23-.../23-09-SUMMARY.md` — FOUND
- commit `dc2147f` — FOUND
- commit `14c9c3d` — FOUND
