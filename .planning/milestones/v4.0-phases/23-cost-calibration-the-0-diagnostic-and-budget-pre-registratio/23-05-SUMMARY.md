---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 05
subsystem: cost-calibration
tags: [cal-01, cal-05, cost-record, schema, refusal, floor-ceiling, ratchet, mps-timing, ast-guard]

requires:
  - phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
    provides: "scripts/phase23_prereg.py::COST_RECORD — the edit-once register the cost artifact path is RESOLVED from, never retyped"
  - phase: 20-the-mitigation-gate-and-its-pre-registration
    provides: "scripts/phase20_gate_coverage.py:413::_prove_retention_floor — the refusal shape mirrored (name the missing quantity, state what an unlabelled number is indistinguishable from)"
  - phase: 20-the-mitigation-gate-and-its-pre-registration
    provides: "scripts/mitigation_gate.py:254 K_RUNGS and :918 ratchet_k — the ratchet that makes the ceiling the only direction sizing may take. Read-only; FROZEN"
  - phase: 18-the-extraction-attack-and-its-pre-registration
    provides: "results/phase18_preflight_report.md:23-38,71-81 — the committed per-shape rates, the 45-56/64 stop-terminated range, and the 84,960 draws / 9.54 h projection the K scaling is checked against"
provides:
  - "scripts/phase23_cost.py — TRAINING_RECORD_KEYS (17) / GENERATION_RECORD_KEYS (18) / FORBIDDEN_MEAN_KEYS, validate_record(record, *, kind), size_sweep(*, generation_record, sweep_points, k), time_iterations(fn, *, device, warmup, iterations), and _synthetic_record(kind, **overrides)"
  - "tests/test_phase23_cost.py — 43 tests: 35 per-key refusal cases across BOTH registers, the instance+structural no-bare-mean guard with a meta-guard, the ceiling-sizing positive control watched RED, the timing-helper denominator refusals, and the prereg-register path guard"
  - "the AFFINE K scaling draws_at_k = draws_per_point + questions * (k - k_per_question), verified against .planning/REQUIREMENTS.md:177-182 at every K_RUNGS entry"
affects: [23-10 and 23-11 fill this schema and call time_iterations, 23-12 adds test_cost_claim_correction_is_additive to this test file, 23-13 sizes Z through size_sweep and asserts sized_against == h_per_point_ceiling]

tech-stack:
  added: []
  patterns:
    - "a record schema whose REFUSALS land before any number exists, so the structural property is a fact about the artifact rather than a note beside it"
    - "a forbidden-key register walked at ANY nesting depth, paired with an AST scan of the module's OWN string constants so the module cannot introduce the field it forbids"
    - "an AST-walk META-GUARD: assert the walk collected a non-empty set, because a walk that silently stopped working reports 'no violations found'"
    - "a POSITIVE CONTROL for which end of a bracket was read — a floor-using implementation passes 'does not raise' and fails this"
    - "torch imported lazily inside the one function that needs a device, so the schema half stays importable torch-free; asserted about the SOURCE via AST, not about sys.modules"

key-files:
  created:
    - scripts/phase23_cost.py
    - tests/test_phase23_cost.py
  modified: []

key-decisions:
  - "23-05: size_sweep's missing-ceiling refusal names the RATCHET, not just the field. validate_record's generic missing-key message lists the absent key; a missing h_per_point_ceiling is the one absence whose CONSEQUENCE must be stated, because ratchet_k only lets K increase — every other missing key costs a label, this one costs the budget in the direction nothing can undo."
  - "23-05: the K scaling is AFFINE and derived from the record's own keys, not draws_per_point * k / k_per_question. MEASURED: the linear form reproduces 1 of 4 committed rungs (42,480 at K=48) and misses the other three by 504 / 672 / 840 draws; the affine form reproduces all four EXACTLY."
  - "23-05: CAL-01 and CAL-05 NOT ticked. This plan built the record's SHAPE and its refusals; both requirements are MEASUREMENTS (23-10 / 23-11) that have not happened."
  - "23-05: the plan cited scripts/mitigation_gate.py::_prove_retention_floor as the shape to mirror; that function does not exist there — it is scripts/phase20_gate_coverage.py:413. Code wins."
  - "23-05: gsd-sdk hazards, FOURTEENTH session in a row, with ONE new variant — state.add-decision REVERTS progress.completed_plans from a stale frontmatter read, undoing a repair made before it runs."

patterns-established:
  - "The negative control is WATCHED, not argued: the shipped module is mutated to the defect the test exists to catch, the failure and its exact numbers are recorded, and the file is proven byte-identical to its commit afterwards."
  - "A refusal that names a missing field but not its consequence is treated as incomplete when the consequence is unrecoverable."

requirements-completed: []

duration: 35min
completed: 2026-08-26
---

# Phase 23 Plan 05: The Cost Record's Shape and Its Refusals Summary

**CAL-05's "floor, not mean" is now a property a consumer cannot route around: `h_per_point_floor` and `h_per_point_ceiling` are distinct REQUIRED keys, every bare-mean name is refused at any nesting depth AND absent from the module's own source by AST scan, and `size_sweep` refuses a floor-only record with a message that names the ratchet — proven by mutating the shipped function to read the floor and watching exactly one test go RED.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2 of 2 (plus one follow-on refusal, Rule 2)
- **Files created:** 2 · **modified:** 0
- **Suite:** `1452 passed, 1 skipped` (baseline `1409 passed, 1 skipped`; delta = the 43 new tests). The one skip is the pre-existing `tests/test_train_loop.py:81` fp16-AMP smoke that needs a CUDA GPU. `make lint` exits 0.
- **`tests/test_phase23_cost.py`:** `43 passed in 0.04s`, **zero skips** — CPU-only, GPU-free, torch never imported.

## Task Commits

1. **Task 1: the schema, the refusals, the ceiling-sized sizing** — `7724d13` (feat)
2. **Follow-on (Rule 2, found writing Task 2's test): name the ratchet in the missing-ceiling refusal** — `ac3fc7f` (fix)
3. **Task 2: completeness, refusals, and the structural no-mean guard** — `bbb190c` (test)

## What Landed

### The three CAL-05 mechanisms, all three of them

`23-RESEARCH.md` §R3.B names three mechanisms in increasing strength and recommends all three. All three are in `scripts/phase23_cost.py`:

| # | Mechanism | Where | What it refuses |
|---|---|---|---|
| 1 | Distinct field names, no bare mean | `GENERATION_RECORD_KEYS`, `FORBIDDEN_MEAN_KEYS` | `h_per_point`, `draws_per_min`, `mean_h_per_point`, `h_per_point_mean` at **any nesting depth** |
| 2 | A `_prove`-style refusal in the consumer | `size_sweep`'s first statement | a floor-only record, with the ratchet reason in the message |
| 3 | Size against the ceiling | `size_sweep` returns `projected_hours` from `h_per_point_ceiling_at_k` | a floor-derived projection — `floor_hours` is recorded **beside** it as disclosure, never as an alternative |

### The registers

`TRAINING_RECORD_KEYS` carries **17** keys, `GENERATION_RECORD_KEYS` carries **18** — **35 required keys, each with its own refusal case**. `test_incomplete_cost_record_is_refused` is parametrized over every one of them: `35 passed`.

Each case validates a complete record FIRST (the control), then drops one key. That is what makes each failure interpretable — it establishes that the only defect in the record under test is the key that case removed.

### The K scaling, checked against a committed artifact

`draws_per_point` is **not** `questions * k`: the Phase-18 shape mixes K-scaled attack families with a fixed-draw family zero (1,008 draws per arm, from `results/phase18_preflight_report.md:71-81`'s A0 row at 2,016 draws across both arms). So `size_sweep` scales affinely from the record's own keys:

```
draws_at_k = draws_per_point + questions * (k - k_per_question)
```

Checked against `.planning/REQUIREMENTS.md:177-182`'s committed per-point table, from the committed geometry `draws_per_point=42480, questions=864, k_per_question=48`:

| K | affine (this module) | linear `draws_per_point * k / k_per_question` | committed |
|---|---|---|---|
| 48 | **42,480** ✓ | 42,480 ✓ | 42,480 |
| 24 | **21,744** ✓ | 21,240 ✗ (−504) | 21,744 |
| 16 | **14,832** ✓ | 14,160 ✗ (−672) | 14,832 |
| 8 | **7,920** ✓ | 7,080 ✗ (−840) | 7,920 |

The linear form reproduces **1 of 4** rungs and under-counts the other three. The affine form reproduces **4 of 4** exactly, and the module's `__main__` self-check step 5/5 re-derives all four on every run rather than asserting the agreement in prose.

### The negative control, WATCHED

The plan asks that a floor-using implementation fail `test_sizing_uses_the_ceiling_not_the_floor`. That was measured, not assumed. One line of the shipped module was mutated:

```
-    ceiling_at_k = generation_record["h_per_point_ceiling"] * scale
+    ceiling_at_k = generation_record["h_per_point_floor"] * scale
```

Observed:

- `tests/test_phase23_cost.py` → **`1 failed, 42 passed`**. The single failure is `test_sizing_uses_the_ceiling_not_the_floor`, at `assert 0.511864406779661 == 1.535593220338983`. No other test moved — including `test_sizing_refuses_a_floor_only_record`, which a "does not raise" test would have been satisfied by.
- `.venv/bin/python scripts/phase23_cost.py` → **exit 1** at step 5/5: *"K=48 projected 16.0h, not above the floor-derived 16.0h — the sizing is reading the wrong end of the bracket"*.

Reversed by the exact inverse substring replacement; `git diff --quiet -- scripts/phase23_cost.py` returned **0**, so the file is byte-identical to `ac3fc7f`.

### The structural halves, and their meta-guard

Two assertions are about the module's SOURCE, not about an instance:

- **`test_no_bare_mean_field_exists`** `ast.parse`s `scripts/phase23_cost.py` and asserts no string constant **equal to** a `FORBIDDEN_MEAN_KEYS` member appears outside the `FORBIDDEN_MEAN_KEYS` assignment itself. The **meta-guard** asserts the walk collected a non-empty set AND found `h_per_point_ceiling` (which provably lives outside the skipped assignment) — because an AST walk that silently stopped working returns an empty set, and an empty set satisfies "no forbidden key found" vacuously.
- **`test_the_cost_record_path_comes_from_the_prereg_register`** asserts `phase23_cost.COST_RECORD is phase23_prereg.COST_RECORD` (identity, not equality — a copy is exactly what can drift) and that **zero** string constants in the module contain `results/phase23`. The resolution is an attribute access involving no literal at all, so any occurrence would be a second copy with nothing keeping it in step.

The same discipline forced the self-check to build its bad-record fixture from `FORBIDDEN_MEAN_KEYS[0]` rather than typing the field name — a literal there would have violated the guard the module ships.

### The timing helper

`time_iterations(fn, *, device, warmup=4, iterations=20)` calls `torch.mps.synchronize()` immediately before `t0` and immediately before `t1` when the device is MPS, and returns `seconds_per_iteration` **with** `timed_iterations` and `warmup_iterations_discarded` — the names `TRAINING_RECORD_KEYS` requires, so a caller records the denominator by construction.

`warmup=0` and `iterations=1` are both refused, and `test_the_timing_helper_refuses_too_few_iterations` proves the refusal fires **before the callable runs at all** (a counter that stays empty) — which is also before the lazy `import torch`.

Recorded in the module docstring as a measured fact with its source (`23-RESEARCH.md` §R3.A): `src/personacore/generation/core.py:79`'s `tok = int(next_id)` is a device→host sync once per generated token, so Phase 18's committed rates are honest — but **training has no per-step host sync at all**, which is why the explicit synchronize is not optional there.

## Deviations from Plan

### Auto-fixed / resolved against the code

**1. [Rule 2 — missing critical functionality] `size_sweep`'s missing-ceiling refusal did not name the ratchet**

- **Found during:** Task 2, writing `test_sizing_refuses_a_floor_only_record`.
- **Issue:** The plan requires the refusal message to name *"`h_per_point_ceiling` and the ratchet reason"*. As shipped by Task 1, a floor-only record fell through to `validate_record`'s generic missing-key message, which lists the absent key and says nothing about consequence.
- **Fix:** A dedicated `_prove` on the ceiling's presence as `size_sweep`'s first statement, ahead of `validate_record`, whose message names `ratchet_k`, `K_RUNGS`, and what the fallback would cost. Every other missing key costs a label; this one costs the budget in the direction the ratchet cannot undo, and that difference belongs in the message a consumer actually reads.
- **Files modified:** `scripts/phase23_cost.py` · **Commit:** `ac3fc7f`

**2. [artifact naming — code wins] The plan's `_prove_retention_floor` citation is wrong**

The plan's `read_first` names `scripts/mitigation_gate.py::_prove_retention_floor`. **That function does not exist in `mitigation_gate.py`** — `grep` finds only `_prove` (`:66`) and `_prove_verdict_domain` (`:96`). It is at **`scripts/phase20_gate_coverage.py:413`**. The module cites the real location. This is the ninth consecutive plan in this repository to name an artifact the code does not have.

**3. [line citations tightened] The ratchet's location**

The plan cites `mitigation_gate.py:248-255`. Measured: the RATCHET sentence is at **`:250`**, the closed menu `K_RUNGS = (48, 24, 16, 8)` at **`:254`**, and the ratchet FUNCTION `ratchet_k(*, fixed_k, proposed_k)` at **`:918`**. The plan's range contains the first two but not the function; the module cites all three exactly. `scripts/mitigation_gate.py` was **read only** — `git diff --exit-code` returns 0.

**4. [`23-VALIDATION.md` disagrees with the plan on file placement]**

`23-VALIDATION.md:65` assigns `test_sizing_refuses_a_floor_only_record` to `tests/test_phase23_budget.py`; the plan assigns it to `tests/test_phase23_cost.py`. Implemented **per the plan**, in `tests/test_phase23_cost.py`, because `size_sweep` lives in `scripts/phase23_cost.py` and a guard proved somewhere other than beside its subject is the lookalike-copy defect `tests/test_phase20_prereg.py:153-155` names. `tests/test_phase23_budget.py` (which already exists, from 23-02) is **untouched**. Flagged for the phase verifier: the validation row's path should be corrected, or a second binding added there, but not both copies.

**5. [K scaling law unspecified by the plan] Resolved against the committed table**

The plan specifies `size_sweep(*, generation_record, sweep_points, k)` and a `k_scaled_ceiling` without naming the scaling law. The obvious linear form is **measurably wrong** (see the table above: 1 of 4 rungs). The affine form is used, derived from the record's own required keys, and re-derived against the committed table by the self-check on every run.

### Requirements NOT ticked

The plan's frontmatter claims `requirements: [CAL-01, CAL-05]`. **Neither is ticked, and `.planning/REQUIREMENTS.md` is byte-unchanged.**

- **CAL-01** reads *"The training leg is **measured** to complete the pair … to be confirmed on the DP path with the seam active."* No training run happened here.
- **CAL-05** reads *"**Re-measure** throughput on one noised adapter."* No adapter was loaded and no draw was taken.

This plan built the shape those measurements will be recorded in. 23-10 and 23-11 take the measurements; ticking a requirement whose run has not occurred is exactly the defect this phase's ordering discipline exists to prevent. `.planning/REQUIREMENTS.md` line 184 (`- [ ] **CAL-01**`) and line 196 (`- [ ] **CAL-05**`) remain unchecked, and the traceability rows at `:354` / `:357` remain empty.

## No Numbers Entered an Artifact

Nothing under `results/` was created or modified. `git status --short` shows only the two new source files (plus the pre-existing `.gitignore` modification, which predates this session and was not touched).

The one place cost-shaped values appear is the self-check and test fixtures, and they are of two kinds, both labelled in place:

- **Committed geometry, quoted from a published artifact:** `draws_per_point=42480`, `questions=864`, `k_per_question=48`, and the four-rung draw table — all from `results/phase18_preflight_report.md` and `.planning/REQUIREMENTS.md:177-182`.
- **Obvious placeholders whose only property under test is their ORDER:** `h_per_point_floor=1.0`, `h_per_point_ceiling=3.0` (tests) / `2.0` (self-check). Every other field in a synthetic record is the literal string `SYNTHETIC`, produced by `_synthetic_record`, so a fixture cannot be mistaken for a measurement.

## Frozen Files and Guards

| File | Status | Verified |
|---|---|---|
| `scripts/phase23_prereg.py` | **EDIT-ONCE, live ancestry guards** | `git diff --exit-code` → 0 |
| `scripts/mitigation_gate.py` | FROZEN | `git diff --exit-code` → 0 |
| `scripts/mitigation_accountant.py` | FROZEN | `git diff --exit-code` → 0 |
| `pyproject.toml` | RPT-03, zero installs | `git diff --exit-code` → 0 |
| `tests/test_phase23_budget.py` | 23-02's, untouched | not in `git status` |
| `.planning/REQUIREMENTS.md` | 23-12's correction, not this plan's | not in `git status` |

`scripts/phase23_cost.py` is **not** matched by the `mitigation_*.py` glob, so the `{pathlib, sys, erasure_gate}` import ceiling does not apply and `tests/test_phase23_budget.py::test_gate_does_not_transitively_load_the_budget` is unaffected. The module takes no dependency on the frozen gate: `K_RUNGS` is quoted in a comment, never imported.

## gsd-sdk Regressions, Session 14

Every handler call was followed by `git diff .planning/STATE.md .planning/ROADMAP.md`, read, and hand-repaired line-exactly against a snapshot taken before the first call.

| Handler | Behaviour |
|---|---|
| `state.advance-plan` | Advanced `Plan: 5 → 6` **correctly**. Left `stopped_at` un-advanced (not regressed backwards this time), flattened body `Status:` to `Ready to execute`, returned `last_updated` **quoted**, and set `last_activity` to the UTC-shifted `2026-08-27`. |
| `state.update-progress` | `{"updated": false, "reason": "Progress field not found in STATE.md"}` — the same string since 22-12. Its **claimed no-op still re-stamped** `last_updated` and `last_activity`. `completed_plans` stayed at 51 and was hand-incremented to 52. |
| `state.record-metric` | **Refused positional args** (`{"error": "phase, plan, and duration required"}`); clean with `--phase/--plan/--duration/--tasks/--files`. |
| `state.add-decision` | **Refused positional args**; needed `--summary`. Wrote `- [Phase ?]: ` on all five calls. **NEW THIS SESSION:** it also **reverted `progress.completed_plans` from the hand-repaired 52 back to 51** — it rewrites the frontmatter from a stale read, so a repair made *before* it runs is silently undone. Re-repair **after** the last `add-decision`, not before. |
| `state.record-session` | **Clean**, and corrected `advance-plan`'s un-advanced `stopped_at` as a side effect. |
| `roadmap.update-plan-progress` | See the diff in this commit. |

`STATE.md` 670 → 676 lines: +1 Performance Metrics row, +5 decisions. Nothing else moved.

## Self-Check: PASSED

- `scripts/phase23_cost.py` — FOUND
- `tests/test_phase23_cost.py` — FOUND
- `7724d13` — FOUND
- `ac3fc7f` — FOUND
- `bbb190c` — FOUND
