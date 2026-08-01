---
phase: quick-260801-r9y
plan: 01
subsystem: phase-13-closeout
tags: [honest-evidence, roadmap, figures, fail-loudly]
status: complete
requires: [phase-13-artifacts]
provides: [corrected-roadmap-sc1, measurement-derived-stop-fraction-note, hardened-plot-script]
affects: [.planning/ROADMAP.md, scripts/make_retention_samples.py, results/phase13_retention_samples.md, scripts/plot_phase13.py]
tech-stack:
  added: []
  patterns: [derive-prose-from-measurement, fail-loudly-never-degrade, select-by-key-not-position]
key-files:
  created: []
  modified:
    - .planning/ROADMAP.md
    - scripts/make_retention_samples.py
    - results/phase13_retention_samples.md
    - scripts/plot_phase13.py
decisions:
  - "Stop-fraction prose states the measurement then explains it, so it stays true at any measured value"
  - "MAX_NEW_TOKENS interpolated into the note too — kills the second drift source at zero cost"
  - "_series takes an optional source= so a missing column names the offending CSV, not just itself"
metrics:
  duration: ~25min
  completed: 2026-08-01
  tasks: 3
  files: 4
---

# Quick Task 260801-r9y: Phase-13 Closeout Corrections Summary

Three independent Phase-13 evidence corrections — a stale ROADMAP criterion, a generated
paragraph that contradicted its own table, and two silent-failure modes in the figure script —
landed as three atomic commits with zero change to any measured number or rendered pixel.

## What Was Done

### Task 1 — ROADMAP Phase-13 success criterion 1 (`d679440`)

Criterion 1 described an experiment that never ran: it claimed the arms differed by "λ=0 vs λ*",
but Phase 12 §8 recorded **λ* = None**. The A/B actually ran λ=0 against a *pre-chosen* λ=0.01.
Replaced only the trailing parenthetical with `λ=0 (naive) vs λ=0.01 (pre-chosen, per Phase 12
§8's λ*=None verdict) — see results/phase13_ab_report.md:303-305`. The leading clause is
byte-identical and no other ROADMAP line was touched.

The full reconciliation already lives at `results/phase13_ab_report.md:303-305` ("ROADMAP wording
superseded"), so the criterion **cites** it rather than duplicating it — one source of truth.

### Task 2 — Measurement-derived stop-fraction note (`8812638`)

`scripts/make_retention_samples.py` emitted a hardcoded paragraph claiming "nearly every
completion is budget-truncated", sitting directly beneath a table reading `0/20 = 0.00` for
**both** arms. Every completion was budget-truncated; none eos-terminated. Loose rather than
false, but this is an honest-evidence artifact and it must match its own table.

The generator was fixed **first** — fixing only the markdown would let the defect return on the
next regeneration. New module-level pure helper:

```python
def _stop_fraction_note(n_stopped_total, n_completions_total):
```

It interpolates the measured fraction *and* `MAX_NEW_TOKENS`, then orders the sentence as
measurement-then-explanation ("...was measured at 0/40 = 0.00... so a low stop-id fraction is
expected and is not an adherence failure"). That ordering is what makes it regeneration-proof:
the prose asserts no characterisation of the value, so it stays true at any future count. The
report builder calls it with `n_stopped`/`n_completions` summed across `proxies`.

`results/phase13_retention_samples.md` was **hand-edited** (never regenerated — the script needs
two gitignored 278MB/166MB checkpoints and carries a WR-02 refuse-to-rerun guard). Agreement is
proven by importing the script and diffing `_stop_fraction_note(0, 40)` against the file:
**byte-identical**. `git diff --stat` on the markdown shows `3 insertions(+), 3 deletions(-)` —
only the note lines; the 2×2 table, the 79/69 leakage counts, the 0/20 eos counts, samples and
preamble are untouched.

### Task 3 — plot_phase13.py fails loudly (`f0bae0b`)

Two latent silent failures, both fixed as observable no-ops.

**(a) `_series`** filtered with `if r.get(column)`. The real failure mode is precise: `DictReader`
always yields strings and `"0.0"` is truthy, so a legitimate zero was *never* dropped. The actual
bug is a **missing** column — `.get()` returns `None` on every row, producing an empty series that
renders a valid-looking but blank panel under a titled axis. That is the exact twin of the
Pitfall-1 hazard `build_frontier_points` already defends against (`results/ft_lr_9e-5.csv` has no
`retention_ppl`). Now: raises `KeyError` naming the column and the source CSV, filters on an
explicit `not in (None, "")`, and raises `ValueError` if the series comes out empty. An optional
`source=` argument is threaded from the `plot_forgetting_curve` call sites so the message names
*which* arm's CSV is at fault.

**(b) `build_frontier_points`** took `_rows(...)[-1]` — the positional last row — while the figure
title and caption both claim "1250-step sweep endpoints". Added `SWEEP_ENDPOINT_STEP = 1250` and
selected by `step == SWEEP_ENDPOINT_STEP`, erroring with the actual last step if absent.

The Pitfall-1 / Pitfall-3 comments and the `LAMBDA0_POINT` hardcode-with-citation are intact. No
tests added — `tests/test_phase13_plots.py` already pins the six-point count and the PNG smoke
render.

## Verification

**PNG oracle was valid — no fallback needed.** Before editing, both figures were rendered to a tmp
dir with the *pre-edit* code and matched the committed hashes exactly, establishing the committed
files as a usable oracle. After the edit both re-render **SHA-256-identical**:

| Figure | SHA-256 (committed == pre-edit == post-edit) |
|---|---|
| `results/phase13_forgetting_curve.png` | `332e7324100c7e7d44d123400a9ed49ec96dc66b5de251fa19b6acf270e64877` |
| `results/phase13_frontier.png` | `65e9299a4bc6c4e73e4ae7edc4c54c9b016e060a45e512550a2f789ba59c7601` |

Behavior-preservation of (b) was checked independently before the edit: all five
`results/ft_lam_*.csv` contain **exactly one** step-1250 row, and in every file it **is** the last
row — so `[-1]` and `step == 1250` select the same row today.

| Check | Result |
|---|---|
| Full suite | **285 passed, 1 skipped** (unchanged, +0 tests) |
| `tests/test_phase13_plots.py` | 3 passed |
| `make lint` | All checks passed; 122 files already formatted |
| `git diff c3d942e HEAD -- scripts/finetune_ab.py` | **empty** (frozen driver untouched) |
| `git status --porcelain results/` | clean — no PNG entries |
| Missing-column probe | `KeyError: "<rows>: no column 'retention_ppl'; columns are ['dialog_ppl', 'step']"` |
| All-blank-column probe | `ValueError: <rows>: column 'retention_ppl' is blank in all 1 rows` |
| Zero-not-dropped probe | `([0], [0.0])` — a legitimate `"0.0"` still plots |
| Note vs markdown | byte-for-byte match on `_stop_fraction_note(0, 40)` |

## Deviations from Plan

None — plan executed as written. Rendering was done only to tmp dirs; `results/*.png` were never
rewritten on disk.

Two small judgment calls inside the specified latitude:

1. The plan offered the `source`/`path` threading as optional ("if threaded through"). Taken — with
   two arms plotted from two CSVs, an error naming only the column would not say which arm failed.
2. `MAX_NEW_TOKENS` is interpolated into the note alongside the counts. The plan required only the
   counts be derived, but the "128 new tokens" justification is the same class of drift risk and
   costs one f-string slot to eliminate.

`plot_forgetting_curve`'s two `ax.plot` calls became a two-iteration loop so the `source` argument
fit inside the 100-char ruff limit; call order is unchanged, which the identical PNG hashes confirm.

## Known Stubs

None.

## Self-Check: PASSED

- `.planning/ROADMAP.md` — FOUND, contains "pre-chosen" + `phase13_ab_report.md`, no `vs λ*)` remains
- `scripts/make_retention_samples.py` — FOUND, contains `def _stop_fraction_note`
- `results/phase13_retention_samples.md` — FOUND, note byte-identical to generator output
- `scripts/plot_phase13.py` — FOUND, contains `SWEEP_ENDPOINT_STEP`
- `.planning/quick/260801-r9y-SUMMARY.md` — FOUND
- Commits `d679440`, `8812638`, `f0bae0b` — all FOUND in `git log`
