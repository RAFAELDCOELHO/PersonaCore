---
phase: 15-figures-writeup
plan: "07"
subsystem: narrative / the v2.0 evidence notebook + the SC3 supersession record (DOC-02)
tags: [DOC-02, D-13, D-01, D-02, D-03, D-04, D-18, R4, SC2, SC3, notebook]
requires:
  - "results/phase15_adapter_delta.png + results/phase15_fisher_ewc.png (15-03 @ ad9d6be) — the two displayed figures"
  - "results/phase13_forgetting_curve.png (Phase 13, VIZ-01) — the third displayed figure"
  - "results/phase15_norms.json (15-02 @ f68450a) — the per-layer table, vmax_driver, comparison_basis, blocks.fisher.variant"
  - "results/phase13_ab_report.md (Phase 13 + the 15-04 addendum @ 0e8b890) — the A/B numbers, the gate-scope quote, the correlation verdict"
  - "results/phase14_recall_report.md — the recall rates, the ADAPT verdict string, the soft-tier quote"
  - "results/inflation_report.md — the tokenizer-inflation tax and its same-run baseline"
  - "docs/REPORT.md § `## Milestone 2 Limitations — Nine Honest Negatives, Quoted` (15-05 @ b8db4ae) — the target of the notebook's Limitations link"
provides:
  - "demo_v2.ipynb — a self-contained, executed Milestone 2 evidence notebook that re-cites committed numbers and never recomputes them"
  - "demo.ipynb — one prepended independence cell; the eight original cells byte-identical"
  - ".planning/ROADMAP.md — the dated SC3 supersession note and the dated SC2 not-narrowed record"
affects:
  - "Plan 15-08 — test_headline_numbers_match_sources may assert against demo_v2.ipynb's markdown as well as README/REPORT; the code-cells-only checkpoint scan recorded below is the correct gate for this file"
tech-stack:
  added: []
  patterns:
    - "notebook built by a small nbformat-shaped builder script, then executed in place — the committed file is always an executed artifact, never a hand-edited one"
    - "raw-text JSON insertion for the prepend, so the diff is provably one cell object and zero deletions"
    - "committed PNGs displayed via IPython.display.Image (exact bytes) rather than re-plotted through matplotlib (resampled)"
key-files:
  created:
    - "demo_v2.ipynb (11 cells, 447 lines, executed with outputs)"
  modified:
    - "demo.ipynb (+15/−0 — exactly one prepended markdown cell)"
    - ".planning/ROADMAP.md (+22/−0 — SC3 supersession + SC2 not-narrowed record)"
decisions:
  - "The two v2.0 figures and the Phase 13 forgetting curve are displayed with IPython.display.Image, not re-plotted: a committed PNG re-rendered through plt.imshow is resampled, and the whole point of the D-07 artifact-only tier is that the shipped PNG is the evidence"
  - "The prepend was done by raw-text surgery on demo.ipynb's JSON (insert after the literal `{\\n \"cells\": [\\n`) rather than by re-serializing through nbformat — re-serialization can silently normalize escaping or indentation and would have made the byte-identity claim depend on serializer luck instead of on the diff"
  - "SC2's not-narrowed outcome is recorded IN ROADMAP as a dated note, not only in this SUMMARY — the plan requires the SUMMARY to record it, but a reader auditing ROADMAP alone should not have to infer a passed gate from a missing note"
metrics:
  duration: 22min
  tasks: 3
  files: 3
  completed: 2026-08-02
---

# Phase 15 Plan 07: The v2.0 Evidence Notebook and the SC3 Supersession Summary

Shipped `demo_v2.ipynb` — a self-contained Milestone 2 evidence notebook whose every number is
re-cited from a committed report and whose every input is tracked in git — prepended a
mutual-independence signpost to `demo.ipynb` without touching one byte of its existing cells, and
recorded in ROADMAP that SC3's `demo.ipynb` clause was superseded rather than quietly reread.

## THE CORRELATION GATE PASSED — no SC2 narrowing was required

The plan's `<output>` requires this recorded explicitly. **The gate passed.** ρ = 0.801544,
95% CI [0.597984, 0.920291] excluding zero, permutation p = 0.000010 (15-04). D-11's miss branch
was **not** taken, so **no SC2 narrowing note was written** — and the absence of one is a recorded
outcome, not an omission. It is recorded in two places: this section, and a dated
**"SC2 (recorded 2026-08-02): not narrowed — the gate PASSED"** note in `.planning/ROADMAP.md`
itself, so an auditor reading ROADMAP alone never has to infer a passed gate from silence.

## What Was Built

| Task | Commit | What landed |
|------|--------|-------------|
| 1 | `25eaa54` | `demo_v2.ipynb` — 11 cells, executed, outputs committed |
| 2 | `887c3e5` | One prepended markdown cell in `demo.ipynb` (+15/−0) |
| 3 | `e9a00b5` | `.planning/ROADMAP.md` — the dated SC3 supersession + SC2 not-narrowed record (+22/−0) |

## `demo_v2.ipynb` — cell map

| # | Type | Content |
|---|------|---------|
| 0 | md | Title, thesis, what it shows / does not claim, **the independence statement naming `demo.ipynb`** |
| 1 | md | `## Headline evaluation (re-cited, never recomputed)` + the three-claim source table |
| 2 | md | The A/B 2×2, the drifts, the 33.61× margin, the teacher-forced + noise-floor qualifiers |
| 3 | code | `results/phase13_forgetting_curve.png` |
| 4 | md | Teach-then-recall: taught/held-out/closed-book, the verdict string, the two qualifiers |
| 5 | md | The tokenizer-inflation tax with its same-run-baseline-only qualifier |
| 6 | md | The figures disclosure — shared scale, the units exemption, the four vmax drivers, D-03's three named confounds, **the Fisher variant string** |
| 7 | code | `results/phase15_adapter_delta.png` + `results/phase15_fisher_ewc.png` |
| 8 | code | `results/phase15_norms.json` → the variant/n_examples/seed, the machine-readable comparison basis, four 6×6 per-layer tables, the vmax drivers |
| 9 | md | The correlation verdict, terse, as a **rank** correlation, naming the 2-of-36 counter-cells |
| 10 | md | Two verbatim committed caveats + the link to all nine in `docs/REPORT.md` |

## RECORD VERBATIM — what Plan 15-08 can assert against this notebook

- **The checkpoint gate for this file is code-cells-only.**
  `sum('checkpoints/' in ''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')`
  → **`0`**. A whole-file `grep -c 'checkpoints/' demo_v2.ipynb` returns a **non-zero** count and
  is the **wrong** gate: cell 8's committed *output* legitimately prints the artifact's own
  `source_ckpt.path` / `w0_source` provenance strings (`checkpoints/persona_adapter.pt`,
  `checkpoints/convbase_best.pt`, `checkpoints/best.pt`, `checkpoints/phase13_naive_latest.pt`,
  `checkpoints/phase13_ewc_latest.pt`, `checkpoints/fisher_tinystories.pt`). Provenance echoed
  from a committed JSON is not a checkpoint read.
- **`'re-cited, never recomputed'`** is present, in cell 1's `## Headline evaluation` heading —
  the same literal `demo.ipynb`'s cell 3 (now cell 4) carries.
- **The verdict string** is present exactly as `results/phase14_recall_report.md:575` writes it:
  `**ADAPT** — GO with two qualifications.` — bold on `ADAPT` only, em dash, trailing period.
- **The Limitations anchor** used is
  `docs/REPORT.md#milestone-2-limitations--nine-honest-negatives-quoted` — the same two-hyphen
  form README uses; verified to resolve against the finished `docs/REPORT.md` by deriving every
  heading anchor in that file and testing membership.
- **The inflation triple is `3.229` / `2.860` / `1.129`** written **without** the unit character,
  same trap 15-06 flagged: the notebook writes `1.129x` (ASCII `x`, matching
  `results/inflation_report.md:31`), not `1.129×`.
- **`demo.ipynb` cell indices all shifted by one.** Its title cell moved `0 → 1`, its
  `## Headline evaluation` markdown `3 → 4`, and its four code cells `1, 2, 4, 7 → 2, 3, 5, 8`.
  Any test indexing `demo.ipynb` by cell number must add one; the new cell 0 is the only markdown
  cell in the file whose `id` is `notebook-independence`, which is the stabler anchor.

## Verification Results

| Check | Result |
|-------|--------|
| Task 1 automated verify (10 conjuncts) | ten × `True` |
| Code-cells-only `checkpoints/` scan | `0` |
| Fresh-kernel execution (`nbconvert --execute --stdout`) | exit **0**, **1.3 s** wall (the plan budgeted ~20–40 s; the notebook does no plotting, only JSON + PNG embeds) |
| Every number in the notebook present in its cited source | **0 missing**; an independent sweep for *every* numeric literal in the notebook's markdown found **0 orphans** — no number appears that is not in one of the four cited artifacts |
| Both blockquoted caveats byte-verbatim in their sources (whitespace-normalized) | `True` / `True` |
| `docs/REPORT.md` Limitations anchor resolves | `True` |
| Task 2 automated verify (5 conjuncts) | five × `True` — one cell added, markdown, **all eight originals byte-identical**, metadata unchanged, names `demo_v2.ipynb` |
| `git diff --numstat demo.ipynb` | **`15  0`** — zero deletions |
| Task 3 automated verify | `True True True` |
| `git diff --numstat .planning/ROADMAP.md` | **`22  0`** — SC3's original text preserved, status line and Progress table untouched |
| `.venv/bin/pytest -q` | **403 passed, 1 skipped** — exactly the entry baseline, twice (after Task 1, and after Tasks 2+3) |
| Lint, pinned `.venv/bin/ruff` | `All checks passed!` / `139 files already formatted` (ruff lints `.ipynb`; `demo_v2.ipynb` is the 139th) |
| Post-commit deletion check | none, all three commits |

## Deviations from Plan

### 1. The fresh-kernel run takes 1.3 s, not the budgeted 20–40 s

- **Found during:** Task 1 acceptance verification
- **Not a defect** — recorded because `15-VALIDATION.md` carries an explicit sampling-rate
  exception for this command on the assumption it would breach the 10 s feedback budget. It does
  not. The notebook loads one JSON and embeds three PNGs; nothing plots, nothing trains, nothing
  loads a checkpoint. The plan's own upper bound (*"above ~90 s means a cell is doing work it
  should not"*) held with three orders of magnitude to spare. **No exception was needed.**

### 2. `results/inflation_report.md` states the TinyStories baseline twice, at two precisions

- **Found during:** Task 1
- **Issue:** `## Baseline` line 30 gives **2.860** tokens/word; the `## D-09 Bands` correction
  block (line 41) gives **2.864** for the same quantity, as the number that motivated moving from
  absolute to relative bands.
- **Resolution:** the notebook cites **2.860**, which is the value the ratio `1.129x = 3.229 /
  2.860` is actually computed from and the one the plan pins. The 2.864 figure is a rounding of
  the same measurement in a rationale paragraph, not a competing measurement, so **no correction
  was made to the source report** — this is a note for a future reader, not a bug fix. Recorded
  here so the discrepancy is not rediscovered as a drift.

### 3. `make lint` still resolves the stale global ruff (DEF-15-01, unchanged, out of scope)

Sixth consecutive plan. `Makefile:16` calls bare `ruff` → pyenv shim → 0.1.15. **This plan
modified zero `.py` files.** The pinned `.venv/bin/ruff` is clean across all 139 files, including
the new notebook. No new entry; DEF-15-01 already carries the one-line fix.

## How each prior-wave warning was honored

| Warning | Where it landed in `demo_v2.ipynb` |
|---------|-----------------------------------|
| ρ = 0.80 is a rank correlation, not an effect size | Cell 9: *"ρ is a **rank** correlation, not an effect size … it does *not* say EWC dodges 80% of the movement"* |
| Do not write that EWC reduced movement everywhere | Same cell: *"**2 of the 36 cells moved further under EWC** (layer 0 / `q_proj`, layer 1 / `q_proj`). Both signed values are inside this ρ; none were filtered out."* |
| naive+ewc share a scale; Fisher has its own for **units**; adapter is not comparable | Cell 6, in that order, with the shared range spelled out and D-03's three confounds named by number |
| Name the Fisher variant from the artifact, not the coarse `regime` label | Cell 6 states it in prose; cell 8 **prints it from `blocks.fisher.variant`** so the notebook shows the string it claims |
| `demo.ipynb`'s existing cells must stay byte-unchanged | Asserted structurally against `git show HEAD:demo.ipynb`, cell-array equality, not by eye |
| README is done — do not modify it | `git status` shows `README.md` untouched across all three commits |

## Known Stubs

None. Every cell executed; every displayed figure exists on disk; every number is present in the
artifact it cites; the one outbound documentation link resolves.

## Threat Flags

None — this plan wrote a notebook and two markdown edits. No endpoint, no auth path, no schema at
a trust boundary. Its own `<threat_model>` is covered and verified: **T-15-20** (a `demo.ipynb`
cell silently modified or re-executed) by the byte-level `nb['cells'][1:] == old['cells']` plus
metadata equality against `git show HEAD:demo.ipynb`, and by `15 0` numstat; **T-15-21** (a
criterion quietly reinterpreted) by the dated SC3 note in the `phase13_ab_report.md:303-305`
register with the original text preserved beneath it, plus the dated SC2 not-narrowed record;
**T-15-22** (recomputing a headline number) by the code-cells-only `checkpoints/` scan returning
`0` and the zero-orphan numeric sweep; **T-15-23** (failing on a fresh clone) by the clean
fresh-kernel execution and the independence statements in both notebooks' opening cells.
**T-15-SC:** zero packages installed.

## Self-Check: PASSED

- `demo_v2.ipynb` — FOUND (447 lines, 11 cells, 3 executed code cells with `execution_count` 1/2/3)
- `demo.ipynb` — FOUND (9 cells; originals byte-identical to `HEAD~2`)
- `.planning/ROADMAP.md` — FOUND (Phase 15 section carries both dated notes)
- `results/phase13_forgetting_curve.png` / `phase15_adapter_delta.png` / `phase15_fisher_ewc.png` — all FOUND
- Commit `25eaa54` — FOUND in `git log`
- Commit `887c3e5` — FOUND in `git log`
- Commit `e9a00b5` — FOUND in `git log`
