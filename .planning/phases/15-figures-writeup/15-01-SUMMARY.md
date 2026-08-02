---
phase: 15-figures-writeup
plan: "01"
subsystem: statistics / pre-registration
tags: [VIZ-03, D-09, D-10, D-11, D-12, pre-registration, spearman, numpy]
requires:
  - "src/personacore/lora/config.py::TARGET_PROJECTIONS (projection order)"
  - "src/personacore/config.py::ModelConfig.n_layer = 6 (the n = 36 source)"
  - "scripts/_verdict.py::VERDICT_SECTION (named in the CR-02 renderer note)"
provides:
  - "scripts/phase15_stats.py — the pre-registered rule, seed, sign, gate, statistics, artifact reader and both verdict branches"
  - "PREREG_COMMIT = 0e1af98 — the commit Plan 15-04 cites in the Evidence Index addendum"
  - "render_verdict_section() — the exact markdown Plan 15-04 appends to results/phase13_ab_report.md"
  - "load_pairs() — the D-05 artifact contract Plan 15-02's extract_deltas.py must satisfy"
affects:
  - "Plan 15-02 (extract_deltas.py) — must emit blocks {adapter,naive,ewc,fisher} x 36 cells keyed str(layer) -> projection"
  - "Plan 15-04 — appends the rendered verdict section to results/phase13_ab_report.md"
  - ".planning/ROADMAP.md SC2 — its wording narrows if the gate misses"
tech-stack:
  added: []
  patterns:
    - "pre-registration in the committed driver, git history order as the proof (finetune_ab.py @ c3d942e register)"
    - "pure-numpy rank statistics, fp64 — scipy is not and does not become a dependency"
    - "raise SystemExit naming the offending block/coordinate (plot_phase13.py:88-97 register)"
    - "method-string-in-the-record (SPEARMAN_METHOD / CI_METHOD), the fisher.py _VARIANT convention"
    - "importlib.util.spec_from_file_location driver load in tests (test_phase13_plots.py register)"
key-files:
  created:
    - "scripts/phase15_stats.py (458 lines)"
    - "tests/test_phase15_stats.py (129 lines)"
    - ".planning/phases/15-figures-writeup/deferred-items.md"
  modified: []
decisions:
  - "R5 arbitration committed as a literal: the bootstrap CI is the load-bearing half of the D-11 gate, the permutation p is purely descriptive and never converts a MISS into a PASS"
  - "Percentile bootstrap kept (not upgraded to BCa) with its known small-n bias named in the pre-registration rather than omitted"
  - "Average-rank Spearman deliberately DIVERGES from continual/fisher.py::_spearman (ordinal, no tie averaging); both are correct for their own callers and must not be unified"
  - "load_pairs validates all FOUR blocks including adapter, which the correlation never reads — a truncated artifact keeping only the three read blocks is exactly T-15-07"
  - "Split into three commits (per-task protocol) rather than the plan objective's ONE commit; every commit is pre-artifact, so the pre-registration property is unchanged"
metrics:
  duration: 12min
  tasks: 3
  files: 3
  completed: 2026-08-02
---

# Phase 15 Plan 01: Pre-Registered Correlation Rule Summary

Committed the "EWC dodges high-Fisher coordinates" decision rule — statistic, seed, predicted
sign, resample counts, D-11 gate, R5 arbitration and both rendered verdict branches — as pure-numpy
literals before any Phase-15 correlation exists anywhere in the repo.

## Pre-Registration Commit (cite this)

**`0e1af98`** — `feat(15-01): pre-register the Fisher/delta correlation rule before any number exists`

This is the SHA Plan 15-04 cites in the Evidence Index addendum row, and it is already baked into
the module as `PREREG_COMMIT`. It contains only `scripts/phase15_stats.py` with the constants, the
statistics and the gate. `90d1bce` (reader + both verdict branches) and `b1b6566` (tests) follow it;
all three precede any artifact, any checkpoint read and any figure.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `0e1af98` | Pre-registration block (`N_CELLS=36`, `PROJECTIONS`, `PREDICTED_SIGN=+1`, `PAIRING`, `SEED=1337`, `N_PERM=100000`, `N_BOOT=10000`, `CI_ALPHA=0.05`, `SPEARMAN_METHOD`, `CI_METHOD`), the R5 arbitration comment, the percentile-bias honesty note, `_rank`/`spearman`/`permutation_p`/`bootstrap_ci`, and `ewc_dodges_high_fisher` |
| 2 | `90d1bce` | `load_pairs` (4 blocks × 36 cells, exact projection set per layer, fail-loud naming the coordinate), `render_verdict_section` (both branches), `main()` `__main__`-guarded |
| 3 | `b1b6566` | `tests/test_phase15_stats.py` — the four 15-VALIDATION.md node IDs |

## Key Implementation Detail: the divergence that is the point

`src/personacore/continual/fisher.py::_spearman` is an **ordinal** double-argsort with no tie
averaging. On `a=[1,1,2,3], b=[1,2,3,4]` it returns `1.0`; the correct answer is
`0.9486832980505139`. This module uses **average (fractional) ranks** because the D-05 artifact
rounds for readability and therefore manufactures ties. Both implementations are correct for their
own callers. The module docstring says so explicitly and `test_spearman_known_answers` pins the
exact value fisher.py gets wrong — so a future reader who "unifies the duplicate Spearman" gets a
red test rather than a silently inflated rho.

## The R5 Arbitration (the load-bearing addition)

D-12 asks for a permutation p AND a bootstrap CI; at n = 36 they can disagree. D-11 read literally
makes the **bootstrap CI the load-bearing half** of the gate and the **permutation p purely
descriptive**. That is now a committed module comment, not a runtime decision:

> a `p = 0.03` alongside a CI that spans zero is still a MISS

Committed before either number exists, so it cannot be resolved in whichever direction looks better.

## Verification Results

| Check | Result |
|-------|--------|
| Constants + gate smoke (`1337 100000 10000 1 36` / `False True`) | PASS |
| Canonical Wikipedia IQ/TV value `-0.17575757575757575` within `1e-15` | PASS |
| Tied fixture `0.9486832980505139` within `1e-12` | PASS |
| `_rank([1,1,2,3]) == [0.5, 0.5, 2.0, 3.0]` | PASS |
| Both verdict branches render (`GATE MISSES` + the D-11 miss register; `GATE PASSES` + "the sign is the falsifiable claim") | PASS |
| `.venv/bin/python scripts/phase15_stats.py` exits non-zero naming `results/phase15_norms.json` | PASS (exit 1) |
| `load_pairs` tamper cases (missing block / missing projection / non-numeric cell) all raise `SystemExit` naming the offender | PASS |
| `.venv/bin/pytest -q tests/test_phase15_stats.py` | 4 passed in 0.52s |
| All four 15-VALIDATION.md node IDs resolve | 4 passed |
| Full suite `.venv/bin/pytest -q` | **396 passed, 1 skipped** (392 → 396, no regression) |
| `grep -c 'import torch'` in both files | 0 / 0 |
| `scipy` appears only in the docstring justification, never as an import | PASS |
| `test ! -f results/phase15_norms.json` | PASS — artifact absent at all three commits |
| All three commits touch no `results/phase15_*` file | PASS |
| Lint (`.venv/bin/ruff check . && .venv/bin/ruff format --check .`, ruff 0.15.16 = the `pyproject.toml` pin) | clean, 134 files |

## Deviations from Plan

### 1. [Rule 3 — Blocking] `make lint` resolves a stale global ruff, not the pinned venv ruff

- **Found during:** Task 1 (running the `make lint` acceptance criterion)
- **Issue:** `make lint` failed with `Would reformat: tests/test_gpt_lora_seam.py` — a Phase-04 file
  this plan never touches. `Makefile:16` calls bare `ruff`, which resolves through the pyenv shim to
  **ruff 0.1.15**, while `pyproject.toml` pins `ruff~=0.15` and `.venv/bin/ruff` is 0.15.16.
- **Resolution:** Verified with BOTH versions that every file this plan wrote is clean, and that the
  pinned `.venv/bin/ruff` passes `check .` and `format --check .` across all 134 files. The failure
  is pre-existing, on an unrelated file, and reproduces only on this dev box (CI installs
  `.[cpu,dev]` fresh and therefore sees the pin).
- **Out of scope, logged not fixed:** `Makefile` is not in this plan's `files_modified` and the
  failing file belongs to Phase 04. Recorded as `DEF-15-01` in
  `.planning/phases/15-figures-writeup/deferred-items.md` with the one-line fix (point `Makefile:16`
  at `.venv/bin/ruff`, matching the `format` target at `Makefile:22`).

### 2. Three commits instead of the objective's "ONE commit"

The plan objective said the two files should land "in ONE commit". The executor's per-task commit
protocol produced three (`0e1af98`, `90d1bce`, `b1b6566`). **The pre-registration property is
unchanged and was verified explicitly:** every one of the three precedes the artifact, none touches
a `results/phase15_*` file, and `results/phase15_norms.json` does not exist at any of them. If
anything the split strengthens the audit trail — `0e1af98` isolates the rule, the seed, the sign and
the gate with nothing else in the diff, which is the exact `finetune_ab.py @ c3d942e` shape.

### 3. Test fixture corrected during Task 3 (not a plan defect)

The first draft of the "perfect monotone" assertion used `i + 0.5 * (i % 3)`, which is **not**
strictly monotone (i=2 and i=3 both map to 3.0) and returned `0.99929`. Replaced with a strictly
monotone non-linear map (`i**3 + 1`), which also makes the assertion test rank-monotonicity rather
than linearity. Caught by the test itself before commit.

## Known Stubs

None. Every function in `scripts/phase15_stats.py` is complete and exercised — `load_pairs`,
`render_verdict_section` and the gate against synthetic fixtures, `main()` against the (correctly)
absent artifact.

## What Plan 15-02 Must Satisfy

`load_pairs` is now a committed contract. `scripts/extract_deltas.py` must emit
`results/phase15_norms.json` with:

```
blocks: { adapter, naive, ewc, fisher }        <- ALL FOUR, or load_pairs raises
  cells: { "0".."5": { q_proj, k_proj, v_proj, c_proj, fc_in, fc_out } }   <- exactly 36, exact set
top level: git_sha, built                       <- rendered into the Result block
```

Layer keys are **strings** (`str(layer)`), the projection set per layer must match `PROJECTIONS`
exactly, and every cell must be a finite number. `PREREG_COMMIT` is `0e1af98`.

## Self-Check: PASSED

- `scripts/phase15_stats.py` — FOUND (458 lines)
- `tests/test_phase15_stats.py` — FOUND (129 lines)
- `.planning/phases/15-figures-writeup/deferred-items.md` — FOUND
- Commit `0e1af98` — FOUND in `git log`
- Commit `90d1bce` — FOUND in `git log`
- Commit `b1b6566` — FOUND in `git log`
- `results/phase15_norms.json` — correctly ABSENT
