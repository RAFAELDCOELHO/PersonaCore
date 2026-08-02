---
phase: 15-figures-writeup
plan: "02"
subsystem: extraction / committed norms artifact
tags: [VIZ-02, VIZ-03, D-05, D-06, D-07, D-08, SC3, torch, frobenius, fisher]
requires:
  - "scripts/phase15_stats.py::load_pairs (the PINNED key spelling, committed 15-01 @ 0e1af98)"
  - "checkpoints/persona_adapter.pt + convbase_best.pt + best.pt + phase13_naive_latest.pt + phase13_ewc_latest.pt + fisher_tinystories.pt (gitignored, ~914 MB)"
  - "src/personacore/checkpoint.py::load_adapter / load_fisher (weights_only=True choke points)"
  - "src/personacore/lora/layer.py:27 (scale = alpha/r, single source of truth)"
provides:
  - "scripts/extract_deltas.py — the ONLY new code permitted to open a .pt file"
  - "results/phase15_norms.json — the committed D-05/D-07 hand-off boundary"
  - "tests/test_phase15_plots.py — schema test + skipif-gated reproduction test (15-03 appends to this file)"
affects:
  - "Plan 15-03 — plots read ONLY this artifact; appends 5 figure/structural tests to tests/test_phase15_plots.py"
  - "Plan 15-04 — phase15_stats.py::main() can now run; the correlation verdict is ITS job, not this plan's"
  - "Plans 15-05 / 15-07 — must reproduce the fisher variant string character-for-character (ROADMAP SC3)"
tech-stack:
  added: []
  patterns:
    - "explicit (layer, projection) product allowlist — never an isinstance/substring scan (inject.py:38 P1)"
    - "fingerprint guard as raise SystemExit where load_adapter only warns (checkpoint.py:252-259)"
    - "fp64 cast before every norm — statistics domain (continual/fisher.py register)"
    - "pinned JSON writer: indent=2, insertion order, explicit trailing newline (build_retention_bin.py:180-182)"
    - "skipif-on-gitignored-artifact, multi-artifact form (test_phase14_demo.py:128-133)"
key-files:
  created:
    - "scripts/extract_deltas.py (443 lines)"
    - "results/phase15_norms.json (four blocks x 36 cells)"
    - "tests/test_phase15_plots.py (173 lines)"
  modified: []
decisions:
  - "The adapter's W0 is convbase_best.pt, proven by a raise SystemExit fingerprint guard — CONTEXT D-08 names five checkpoints, there are six, and the sixth is the load-bearing one"
  - "Fisher reduced per cell by MEAN (recorded as fisher_aggregate in the data) — the cache is mean-normalized so a mean reads as 'x the importance of an average parameter'; a sum would confound importance with tensor size"
  - "The byte-for-byte reproduction test normalizes the TWO top-level run-provenance fields (git_sha, built) and nothing else — they record when/at-what-commit extraction ran, not what it computed, and necessarily differ once HEAD moves past the artifact commit"
  - "No correlation computed anywhere in this plan — the verdict belongs in Plan 15-04, adjacent to the report it lands in"
metrics:
  duration: 18min
  tasks: 3
  files: 3
  completed: 2026-08-02
---

# Phase 15 Plan 02: Norms Extraction & the Committed D-05 Artifact Summary

Read the six frozen checkpoints once, computed `‖ΔW‖_F/‖W₀‖_F` on the 6x6 grid for the adapter and
both A/B arms plus the Fisher diagonal on the same grid, and committed all of it as
`results/phase15_norms.json` — the single hand-off boundary every downstream figure, statistic and
report paragraph now reads instead of a checkpoint.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `d1e9eee` | `scripts/extract_deltas.py` — six-checkpoint docstring, SECURITY paragraph, `raise SystemExit` fingerprint guard, 36-key explicit product, fp64 ratios, pinned JSON writer |
| 2 | `f68450a` | `results/phase15_norms.json` — four blocks x 36 cells, D-06 fields on every block, machine-readable `comparison_basis`, SC3 Fisher variant |
| 3 | `adfc008` | `tests/test_phase15_plots.py` — `test_artifact_schema` + `test_extraction_reproduces_the_committed_artifact` |

## RECORD VERBATIM — the four `vmax_driver` entries (D-02 / D-18)

Plans 15-03 (figure captions) and 15-05 (report text) read **these exact values**. The disclosure
is checked against them; deriving them again from the grid is exactly what D-04 forbids.

| Block | layer | projection | value |
|-------|-------|------------|-------|
| `adapter` | 1 | `c_proj` | `0.04738638857364279` |
| `naive` | 1 | `c_proj` | `0.22023983403635128` |
| `ewc` | 1 | `q_proj` | `0.13806389791647683` |
| `fisher` | 0 | `c_proj` | `6.541458482610652` |

**Reading worth carrying into the report:** `naive` and `ewc` — the two blocks that DO share a
comparison basis — do not share a `vmax` driver. The naive arm's largest relative movement is at
`layer 1 / c_proj`; the EWC arm's is at `layer 1 / q_proj`, and at roughly 63% of the naive
maximum. Under D-01's shared scale the EWC panel will therefore read as visibly compressed
relative to the naive panel. **That compression IS the finding** and must not be rescaled away.

## RECORD VERBATIM — the four `nonpositive_cells` counts

| Block | `nonpositive_cells` |
|-------|---------------------|
| `adapter` | `0` |
| `naive` | `0` |
| `ewc` | `0` |
| `fisher` | `0` |

All four are zero, so `LogNorm` masks nothing and no cell silently vanishes from either figure.
The report states **"0 non-positive cells"** from this field — not from the figure appearing to
have none.

## RECORD VERBATIM — the Fisher estimator variant (ROADMAP SC3)

```
empirical_diag_fisher/groundtruth_targets/mean_normalized
```

`n_examples` = `2000`, `seed` = `1234`. Plans 15-05 and 15-07 must reproduce that string
**character-for-character**. It is carried out of the cache's `fisher_meta` and into the artifact
precisely so the claim is checkable: the coarse `regime` (`fisher_diagonal_estimate`) says which
family; `variant` says which estimator, from which targets, under which normalization.

## The fingerprint guard did NOT fire — and the fingerprints it proved

| Block | W₀ | W₀ fingerprint | source checkpoint fingerprint |
|-------|----|----------------|-------------------------------|
| `adapter` | `checkpoints/convbase_best.pt` | `04e724c6…` / step 4000 / val_loss `1.5235939979553224` | adapter `base_fingerprint`, identical |
| `naive` | `checkpoints/best.pt` | `3a46815d…` / step 49000 / val_loss `0.7378001868724823` | `ead34c1c…` / step 4000 / val_loss `1.1526952981948853` |
| `ewc` | `checkpoints/best.pt` | same as naive | `5e908ac3…` / step 4000 / val_loss `1.4012203216552734` |
| `fisher` | — (`null`) | — | anchor `3a46815d…` / 49000 / `0.7378001868724823`, verified by `load_fisher` (which RAISES) |

Every value matches the research-verified table at `15-RESEARCH.md:458-479`. The adapter block's
W₀ is `convbase_best.pt` and **not** `best.pt` — the correction `<critical_correction>` names, now
enforced by `raise SystemExit` rather than by a comment.

## Verification Results

| Check | Result |
|-------|--------|
| AST: `>= 4` `raise SystemExit`, zero bare `assert` in the script | `True True` (7 SystemExit sites) |
| All six checkpoint names present in the docstring (`grep -qF`) | 6/6 PASS |
| `grep -qF 'SECURITY'` / `map_location="cpu"` | PASS / PASS |
| `grep -c 'sort_keys'` | `0` |
| `grep -qF 'load_checkpoint'` (must FAIL — the RNG-restoring loader is unused) | correctly absent |
| Artifact 7-way structural check (4 blocks, 36 cells each, W₀ per block, both `comparison_basis` flags, D-06 fields everywhere) | seven `True` |
| `param_count` 331776 / 13891584, `fisher_aggregate == "mean"` | `True True True` |
| Every layer's projection set equals `projections` | `True` |
| Fisher `variant` / `n_examples` / `seed` | `True True True` |
| Second extraction run to a temp path, `cmp` against the committed file | **byte-identical** |
| `git check-ignore results/phase15_norms.json` | exit 1 — the artifact is tracked |
| `.venv/bin/pytest -q tests/test_phase15_plots.py` | 2 passed, 0 skipped (checkpoints present) |
| `.venv/bin/pytest -q` full suite | **398 passed, 1 skipped** (396 → 398, no regression) |
| `grep -c 'import torch'` in the test file | `0` |
| Lint (`.venv/bin/ruff check . && ruff format --check .`, the `pyproject.toml` pin) | clean, 137 files |
| No correlation computed anywhere in this plan | confirmed — `phase15_stats` is never imported here |

## Deviations from Plan

### 1. [Rule 1 — Bug] The byte-for-byte test would have been false by construction

- **Found during:** Task 3
- **Issue:** The plan specified that the reproduction test asserts the produced file's **bytes**
  equal the committed file's bytes. The artifact's top-level `git_sha` comes from
  `provenance.git_sha()` — i.e. **HEAD at extraction time**. Extraction ran at `d1e9eee`, and the
  artifact was necessarily committed *afterwards* (`f68450a`), so from the very next commit onward
  a re-run stamps a different `git_sha` and a raw byte comparison fails **always**, on a field
  extraction does not compute. `built` has the same property across a date boundary. Left as
  written, the test would have gone red on its own first CI-adjacent run and invited exactly the
  wrong repair — deleting the check or loosening it to a float tolerance.
- **Fix:** `_normalize_run_provenance` blanks the two **top-level** run-provenance lines and
  nothing else, anchored on the two-space `indent=2` prefix. The checkpoint fingerprints nested
  inside each block (`base_fingerprint` / `fingerprint` / `anchor_fingerprint` / `w0_fingerprint`)
  sit at deeper indents and are still compared **byte-for-byte** — which is the part that matters,
  since they are the audit trail saying which weights the numbers describe. No float tolerance was
  added; the plan's instruction on that point stands untouched.
- **Files modified:** `tests/test_phase15_plots.py`
- **Commit:** `adfc008`

### 2. `make lint` still resolves a stale global ruff (DEF-15-01, unchanged, still out of scope)

Identical to Plan 15-01's deviation 1. `Makefile:16` calls bare `ruff`, which resolves through the
pyenv shim to **0.1.15** and reformats `tests/test_gpt_lora_seam.py` — a Phase-04 file this plan
never touches. The pinned `.venv/bin/ruff` (0.15.16, the `pyproject.toml` pin CI installs) passes
`check .` and `format --check .` across all 137 files, including both files this plan wrote.
Already logged as `DEF-15-01` in `.planning/phases/15-figures-writeup/deferred-items.md`; no new
entry added.

### 3. Three commits instead of the plan objective's implied grouping

The per-task commit protocol produced `d1e9eee` (script), `f68450a` (artifact), `adfc008` (tests).
The D-09 pre-registration boundary is unaffected and visible in history: `0e1af98` (the
pre-registered rule) precedes all three, and `results/phase15_norms.json` does not exist at any
commit at or before `0e1af98`.

## Known Stubs

None. Every function in `scripts/extract_deltas.py` runs on the real checkpoints and its output is
committed. Note for the reader: `results/phase15_norms.json` is **produced material**, not a stub —
`scripts/plot_phase15.py` (Plan 15-03) does not exist yet, which is the wave boundary, not a gap.

## Threat Flags

None. The plan's `<threat_model>` covers every surface this plan touched: T-15-03 (the four
`weights_only=False` reads) is mitigated by hardcoded `_REPO_ROOT`-relative paths plus the SECURITY
docstring paragraph — no path here comes from `argv` or an environment variable; T-15-01 is
mitigated by the `raise SystemExit` fingerprint guard plus `load_fisher`'s own raise; T-15-10 is
mitigated by the explicit `(layer, projection)` product and the weights-only key set. No packages
were installed (T-15-SC).

## What Plan 15-03 Must Satisfy

- Read **only** `results/phase15_norms.json`. `scripts/plot_phase15.py` must have no code path that
  opens a `.pt` file (D-07, enforced structurally by the AST/subprocess test 15-03 adds).
- Take `vmax` / `vmin` and the outlier disclosure from `blocks.<name>.vmax_driver` — do **not**
  re-derive `argmax` in the caption. The four entries are tabulated verbatim above.
- The `naive` and `ewc` panels share one `LogNorm` **object** (D-01); the `fisher` panel gets its
  own (units argument, not convenience). All four `nonpositive_cells` are `0`, so nothing is masked.
- Append the five figure/structural tests to the existing `tests/test_phase15_plots.py`; the two
  tests above stay as written. `15-VALIDATION.md:140` expects exactly one skip in this file.

## Self-Check: PASSED

- `scripts/extract_deltas.py` — FOUND (443 lines)
- `results/phase15_norms.json` — FOUND (tracked; `git check-ignore` exits 1)
- `tests/test_phase15_plots.py` — FOUND (173 lines)
- Commit `d1e9eee` — FOUND in `git log`
- Commit `f68450a` — FOUND in `git log`
- Commit `adfc008` — FOUND in `git log`
- Pre-registration commit `0e1af98` precedes all three — CONFIRMED
