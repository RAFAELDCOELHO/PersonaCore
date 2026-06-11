---
phase: 07-evaluation
fixed_at: 2026-06-09T00:00:00Z
review_path: .planning/phases/07-evaluation/07-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 07: Code Review Fix Report

**Fixed at:** 2026-06-09T00:00:00Z
**Source review:** .planning/phases/07-evaluation/07-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (WR-01..WR-05; Info findings IN-01..IN-04 out of scope for `critical_warning`)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: `perplexity()` divides by zero on an empty or single-token corpus

**Files modified:** `src/personacore/evaluation/perplexity.py`
**Commit:** eb0d5c1
**Applied fix:** Added an explicit `if total_tokens == 0: raise ValueError(...)` guard immediately
before `math.exp(total_ce / total_tokens)`. A truncated/empty/1-token `val.bin` now raises a clear,
auditable error naming the path and corpus length instead of an opaque `ZeroDivisionError`. Verified
via `ast.parse` and the existing `tests/test_perplexity.py` suite (6 tests pass; full suite 122
passed / 1 skipped unchanged).

### WR-02: Committed artifacts' headline PPL contradicts the driver's hardcoded literal

**Files modified:** `scripts/evaluate.py`
**Commit:** 3503faa
**Applied fix:** Removed the stale hardcoded `val_loss 0.7378 / ppl 2.091` literal from the printed
NOTE and made the comparison single-source: the driver now reads `blob.get("val_loss")` from
`best.pt` at runtime and derives the comparison figure (`recorded_val_loss` and
`math.exp(recorded_val_loss)`) from it, with a fallback branch when the key is absent. Added the
missing `import math`. This eliminates the literal that could drift from the committed `results.md`
/ `samples.md` 2.1066 number — the driver now always prints whatever `best.pt` actually recorded.
Verified via `ast.parse`, `ruff check`/`ruff format --check` (clean), and the full test suite.

### WR-03: `run_ablations.py` ignored the calibrated budget it computed

**Files modified:** `scripts/run_ablations.py`
**Commit:** db78123 (shared with WR-04, WR-05 — see note below)
**Applied fix:** `main()` now captures `recommended = calibrate(runtime)` and fails loudly with a
`SystemExit` when `abs(recommended - REDUCED_MAX_STEPS) > EVAL_INTERVAL`, instead of discarding the
return value and silently using the module constant. A stale `REDUCED_MAX_STEPS` can no longer
silently produce an unfair-budget cohort on a multi-hour run.
**Note (logic gate — recommend human verification):** the divergence tolerance (`> EVAL_INTERVAL`,
i.e. 250 steps) is a judgement threshold; confirm it matches the intended D-07 lock policy before
the multi-hour cohort run relies on it.

### WR-04: `_read_val_curve` crashed-through on non-finite val_loss other than literal `"nan"`

**Files modified:** `scripts/run_ablations.py`
**Commit:** db78123 (shared with WR-03, WR-05 — see note below)
**Applied fix:** Replaced the string-identity skip filter `if v not in (None, "", "nan")` with a
numeric-finiteness filter: skip `None`/`""`, then `float(v)` and `continue` on `not
math.isfinite(val)`. `"NaN"`, `"-nan"`, `"inf"`, `"-inf"` from a diverged run are now correctly
excluded from the curve so `calibrate()` no longer masks a blown-up run as "didn't flatten".
`math` is already imported at module top. Verified via `ast.parse` and the ablation tests.

### WR-05: `best_val_loss` fallback silently fabricated a derived metric under a misleading column

**Files modified:** `scripts/run_ablations.py`
**Commit:** db78123 (shared with WR-03, WR-04 — see note below)
**Applied fix:** Removed the silent `blob.get("val_loss", math.log(ppl))` substitution. `run_cohort`
now keeps `best_val_loss = None` when the checkpoint lacks the key (and prints `n/a`), and
`write_results_table` renders a missing value distinctly as `n/a (sweep CE {math.log(ppl):.4f})`
rather than letting the full-sweep mean CE masquerade as a real recorded random-batch val-loss.
The two quantities can no longer be confused in the committed table. Verified via `ast.parse`,
`ruff` (clean), and the test suite.

## Notes on commit grouping

WR-03, WR-04, and WR-05 all modify the single file `scripts/run_ablations.py`. The commit tool
(`gsd-sdk query commit`) stages by full file path, so the three findings' changes were committed
together in **db78123** rather than as three separate commits. All three fixes are present and
verified; the grouping is a tooling constraint of per-file staging, not a partial fix. WR-01
(`perplexity.py`) and WR-02 (`evaluate.py`) touch distinct files and committed atomically
(eb0d5c1, 3503faa).

## Verification summary

- Full test suite (main-repo `.venv`, Python 3.11): **122 passed, 1 skipped** — matches the
  pre-fix baseline, no regression.
- `ruff check` and `ruff format --check` pass clean on both modified scripts.
- Pre-existing note: `src/personacore/evaluation/perplexity.py` has a pre-existing `ruff format`
  finding (a `F.cross_entropy(...)` call that ruff would collapse to one line) that existed in the
  originally committed file BEFORE this fix. The WR-01 edit did not introduce it; per the
  pre-existing-error rule it was left untouched to keep the fix scoped to the finding.

---

_Fixed: 2026-06-09T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
