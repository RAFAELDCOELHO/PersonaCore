---
phase: 15-figures-writeup
plan: "03"
subsystem: figures / the D-07 artifact-only plotting tier
tags: [VIZ-02, VIZ-03, D-01, D-02, D-04, D-07, D-18, matplotlib, LogNorm, AST-guard]
requires:
  - "results/phase15_norms.json (committed 15-02 @ f68450a) — the ONLY input"
  - "tests/test_phase15_plots.py (15-02 @ adfc008) — this plan APPENDS five tests to it"
  - "scripts/plot_phase13.py — the register: Agg-before-pyplot, out_dir-parameterized, savefig only"
provides:
  - "scripts/plot_phase15.py — artifact-only figure generation; exports plot_adapter_delta, plot_fisher_ewc, _norms"
  - "results/phase15_adapter_delta.png — VIZ-02"
  - "results/phase15_fisher_ewc.png — VIZ-03"
  - "the D-07 structural guard: AST walk + fresh-interpreter subprocess import"
affects:
  - "Plan 15-05 — the report reads the vmax_driver / nonpositive_cells / shared-range numbers recorded verbatim below; the EWC flatness observation is its outlier-disclosure paragraph"
  - "Plan 15-04 — the two NEGATIVE signed reductions recorded below are the Pitfall-6 cells the D-10 statistic must handle (and the reason the reduction is never a panel)"
tech-stack:
  added: []
  patterns:
    - "one LogNorm OBJECT across two panels, asserted by `is` identity through a _norms() helper — never by equal (vmin, vmax)"
    - "cmap.copy() + set_bad so a LogNorm-masked cell is grey, not an invisible hole"
    - "AST walk with a meta-guard (assert the walk found something before asserting it found nothing bad)"
    - "fresh-interpreter subprocess import as the transitive-import check the AST cannot make"
    - "disclosure text READS the artifact's vmax_driver field rather than recomputing it (D-04)"
key-files:
  created:
    - "scripts/plot_phase15.py (304 lines)"
    - "results/phase15_adapter_delta.png (65,304 bytes)"
    - "results/phase15_fisher_ewc.png (107,413 bytes)"
  modified:
    - "tests/test_phase15_plots.py (173 -> 352 lines, five tests appended)"
decisions:
  - "The three-panel figure lays out with fig.subplots_adjust rather than tight_layout — a colorbar built from an axes LIST (the D-01 shared-scale statement) is not something tight_layout can place; the single-panel VIZ-02 keeps plot_phase13's tight_layout(rect=...) form"
  - "_norms() returns the exact three objects imshow receives, so D-01 is testable by identity rather than inferable from bounds — a two-object implementation with matching bounds is the one a later 'brighten this panel' edit splits into two scales"
  - "The Fisher panel additionally uses a different COLORMAP (viridis vs magma), so the units exemption is visible before a reader reaches the colorbar"
metrics:
  duration: 24min
  tasks: 3
  files: 4
  completed: 2026-08-02
---

# Phase 15 Plan 03: VIZ-02 / VIZ-03 from the Committed Artifact Summary

Rendered both signature figures from `results/phase15_norms.json` and nothing else, and converted
"this plotting module cannot open a checkpoint" from a docstring sentence into two structural
checks that were observed failing against a deliberate violation before being trusted.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `fb6ed7a` | `scripts/plot_phase15.py` — fail-loud `_load_artifact`, `_grid`, `_shared_norm`, the `_norms` identity contract, `set_bad` cmaps, artifact-read `fig.text` disclosures |
| 2 | `8de179e` | Five tests appended to `tests/test_phase15_plots.py`, including the D-07 AST + subprocess guard |
| 3 | `ad9d6be` | `results/phase15_adapter_delta.png` + `results/phase15_fisher_ewc.png`, both tracked |

## RECORD VERBATIM for Plan 15-05 — the four `vmax_driver` entries

Read from the artifact, not re-derived (D-04). `scripts/plot_phase15.py` contains zero
occurrences of `argmax`; the captions print these same fields.

| Block | layer | projection | value |
|-------|-------|------------|-------|
| `adapter` | 1 | `c_proj` | `0.04738638857364279` |
| `naive` | 1 | `c_proj` | `0.22023983403635128` |
| `ewc` | 1 | `q_proj` | `0.13806389791647683` |
| `fisher` | 0 | `c_proj` | `6.541458482610652` |

## RECORD VERBATIM for Plan 15-05 — the four `nonpositive_cells` counts

| Block | `nonpositive_cells` |
|-------|---------------------|
| `adapter` | `0` |
| `naive` | `0` |
| `ewc` | `0` |
| `fisher` | `0` |

All zero, so `LogNorm` masks nothing in either figure and `set_bad`'s grey never appears. The
report states **"0 non-positive cells"** from this field, not from the figures looking clean.

## RECORD VERBATIM for Plan 15-05 — the norm ranges and their spans

| Norm | vmin | vmax | span |
|------|------|------|------|
| **shared (naive + ewc)** — D-01/D-02 | `0.04211054267645148` | `0.22023983403635128` | **0.719 decades** |
| adapter (own, VIZ-02) | `0.018873036397436968` | `0.04738638857364279` | 0.400 decades |
| fisher (own, units exemption) | `0.04864813295948996` | `6.541458482610652` | 2.129 decades |

`vmin` is the smallest strictly positive cell across BOTH arms and `vmax` the largest across both
— the exact extrema, no percentile clipping at either end. The shared `vmin` is an **EWC** cell
and the shared `vmax` is a **naive** cell, which is the arithmetic form of the finding below.

## The EWC-vs-naive flatness observation (D-01 — the finding, not a rendering bug)

**One sentence, for the report:** under the shared scale the EWC panel reads as a visibly darker,
flatter grid than the naive panel — EWC's largest cell is only **62.7%** of naive's largest, its
median cell is **40.9%** of naive's median, and **34 of 36** cells moved less under EWC.

Confirmed by eye on the rendered PNG: the naive panel is uniformly bright across the whole grid
with `c_proj`/`fc_in` brightest, while the EWC panel is dark through the middle columns
(`v_proj`, `c_proj`) at layers 1-4 and retains color only in `q_proj`/`k_proj`. Both panels sit
under **one** colorbar; the Fisher panel has its own, in a different colormap. Nothing was
rescaled. Only 0.719 decades separate the shared bounds, so the compression is genuinely mild —
the EWC panel is darker, not washed out to a single tone.

### Two cells moved MORE under EWC — the Pitfall-6 cells

| cell | naive Δ | EWC Δ | signed reduction |
|------|---------|-------|------------------|
| layer 0 / `q_proj` | `0.120269` | `0.135454` | **`-0.015185`** |
| layer 1 / `q_proj` | `0.131457` | `0.138064` | **`-0.006607`** |

These are the concrete reason the D-10 reduction `naiveΔ − ewcΔ` is **never a panel**: two of its
36 values are negative and a `LogNorm` would mask exactly those two while the figure looked fine.
Plan 15-04's Spearman ρ operates on all 36 signed values including these; Plan 15-05 should not
describe EWC as reducing movement *everywhere*.

## The D-07 guard, observed RED (Task 2 acceptance criterion)

A structural guard nobody has watched fail is a guard nobody has verified. `import torch` was
temporarily added to `scripts/plot_phase15.py` and **both** halves fired:

- **(a) AST half** — `AssertionError: plot_phase15 imports torch — D-07 violated ({'numpy',
  'matplotlib', 'torch', 'json', 'pathlib'})`; `1 failed`.
- **(b) subprocess half** — the fresh-interpreter probe exited **1** (`torch` in `sys.modules`),
  which is the `returncode == 0` assertion's failing case.

Reverted immediately; `git diff fb6ed7a -- scripts/plot_phase15.py` is **empty**, and the file
re-imports with `grep -c 'import torch'` = 0. The subprocess half is the one that cannot be
fooled: it would also catch a transitive torch import through a helper module, which (a) cannot
see.

## Verification Results

| Check | Result |
|-------|--------|
| Both figures render headless into an arbitrary `out_dir`, non-empty | `True True True True` |
| Rendered under `-W error::UserWarning` (no layout/glyph warnings) | clean |
| `grep -c 'import torch'` / `grep -c 'show()'` / `grep -c 'argmax'` in the script | `0` / `0` / `0` |
| AST string constants ending in the checkpoint suffix | `[]` |
| `matplotlib.use("Agg")` at line 44, `import matplotlib.pyplot` at line 46 | ordered correctly |
| `set_bad` present / `vmax_driver` read (7 sites) | PASS / PASS |
| `_norms(artifact)` → `naive is ewc`, `fisher is not naive` | `True True` |
| `_shared_norm` called ONLY from `_norms` (2 grep sites: def + call) | PASS |
| `.venv/bin/pytest -q tests/test_phase15_plots.py` | **7 passed** (2 from 15-02 + 5 here), 0 failed, 0 skipped |
| The five node IDs resolve individually | 5 passed |
| D-07 guard RED against a deliberate violation, GREEN after revert | observed, both halves |
| `.venv/bin/python scripts/plot_phase15.py` twice, SHA-256 compared | **identical** (`9b474dbb…` / `228ce09f…`) |
| `git check-ignore` on both PNGs | exit 1 each — both tracked |
| Post-commit deletion check (`git diff --diff-filter=D`) | none |
| `.venv/bin/pytest -q` full suite | **403 passed, 1 skipped** (398 → 403, no regression) |
| Lint (`.venv/bin/ruff check . && ruff format --check .`) | clean, 138 files |

## Deviations from Plan

### 1. The three-panel figure lays out with `subplots_adjust`, not `tight_layout(rect=…)`

- **Found during:** Task 1
- **Issue:** The plan prescribes `plot_phase13.py`'s `fig.tight_layout(rect=(0, 0.03, 1, 1))`
  alongside the `fig.text` disclosure. On VIZ-03 the D-01 shared colorbar is built with
  `fig.colorbar(im, ax=[ax_naive, ax_ewc])` — an axes **list**, which goes through `make_axes`
  rather than the gridspec path, and `tight_layout` cannot place the result.
- **Fix:** VIZ-03 sets explicit margins with `fig.subplots_adjust(...)` **before** creating the
  colorbars (so they steal space from the final axes positions), with the reason in a comment.
  The `fig.text` disclosure mechanism itself is unchanged, and single-panel VIZ-02 keeps the
  plan's `tight_layout(rect=…)` form verbatim. Both figures render clean under
  `-W error::UserWarning`.
- **Files modified:** `scripts/plot_phase15.py`
- **Commit:** `fb6ed7a`

### 2. [Rule 3] `_annotate_axes` takes `n_layer` explicitly

- **Found during:** Task 1
- **Issue:** The plan's signature is `_annotate_axes(ax, projections)`, but the row count is the
  layer count, not the projection count. Deriving it from the axes (`ax.get_images()[0]`) would
  make the helper silently order-dependent on `imshow` having already been called.
- **Fix:** `_annotate_axes(ax, projections, n_layer)`, with `n_layer` read from the artifact.
  Purely a helper signature; no behavior or contract in the plan's acceptance criteria touches it.
- **Files modified:** `scripts/plot_phase15.py`
- **Commit:** `fb6ed7a`

### 3. The RED revert used a targeted edit, not `git checkout -- <file>`

The environment's destructive-command gate blocked `git checkout -- scripts/plot_phase15.py`
twice. The deliberate `import torch` line was removed with a single-line edit instead and the
revert verified the stronger way: `git diff fb6ed7a -- scripts/plot_phase15.py` is empty, i.e.
byte-identical to the committed blob. No files other than the one under test were ever touched.

### 4. `make lint` still resolves a stale global ruff (DEF-15-01, unchanged, still out of scope)

Identical to Plans 15-01 and 15-02. `Makefile:16` calls bare `ruff`, which resolves through the
pyenv shim to **0.1.15** and reports `tests/test_gpt_lora_seam.py` (a Phase-04 file this plan
never touches) as needing reformatting. The pinned `.venv/bin/ruff` (the `pyproject.toml` version
CI installs) passes `check .` and `format --check .` across all 138 files, including both files
this plan wrote. Already logged as `DEF-15-01`; no new entry added.

## Known Stubs

None. Both plot functions run on the committed artifact and their output is committed. Every
number in both captions is read from `results/phase15_norms.json` at render time — there is no
hardcoded-with-citation constant in this module, deliberately (a hardcoded number here would be a
second source of truth against the artifact D-07 exists to make authoritative).

## Threat Flags

None. The plan's `<threat_model>` covers everything this plan touched: T-15-02 is mitigated by the
two-part D-07 guard (now observed RED); T-15-07 by `_load_artifact`'s fail-loud validation of four
blocks x 36 cells and each layer's projection set, naming the offending block/layer; T-15-04 by
the `tmp_path` smoke test plus the two-run SHA-256 comparison recorded above; T-15-12 by the
identity and full-range tests; T-15-06 by `matplotlib.use("Agg")` before pyplot and zero
`show()` calls. No packages were installed (T-15-SC) — matplotlib was already present.

## What Plan 15-05 Must Satisfy

- Quote the four `vmax_driver` entries and the four `nonpositive_cells` counts from the tables
  above (they are the same fields the figure captions print — D-04 allows different **amounts**,
  never different **things**).
- The outlier-disclosure paragraph reports the shared span as **0.719 decades** and names
  **layer 1 / `c_proj`** as the shared `vmax` driver.
- The EWC flatness sentence is a **finding**, not a caveat about the figure.
- Do not write that EWC reduced movement everywhere: **34 of 36** cells, with `q_proj` at layers
  0 and 1 moving further under EWC.
- VIZ-02 carries its own non-comparability note; its figure-side terse form is already rendered,
  so the report supplies D-03's full three-confound version.

## Self-Check: PASSED

- `scripts/plot_phase15.py` — FOUND (304 lines)
- `tests/test_phase15_plots.py` — FOUND (352 lines)
- `results/phase15_adapter_delta.png` — FOUND (65,304 bytes; `git check-ignore` exits 1)
- `results/phase15_fisher_ewc.png` — FOUND (107,413 bytes; `git check-ignore` exits 1)
- Commit `fb6ed7a` — FOUND in `git log`
- Commit `8de179e` — FOUND in `git log`
- Commit `ad9d6be` — FOUND in `git log`
