---
phase: 08-demo-writeup
plan: 03
subsystem: demo
status: complete
tags: [notebook, nbconvert, ipykernel, demo-ipynb, qa-02, demo-03]
requires: ["08-01"]
provides: ["demo.ipynb (executed, committed with outputs)", "results/run.csv (committed training curve)", "notebook extra in pyproject"]
affects: [pyproject.toml, requirements.txt, results/run.csv, demo.ipynb]
tech-stack:
  added: ["ipykernel~=7.3 (notebook extra)", "nbconvert~=7.17 (notebook extra)"]
  patterns: ["nbconvert --execute --inplace headless execution for committed-with-outputs notebooks", "fresh seeded torch.Generator per stochastic notebook cell"]
key-files:
  created: [demo.ipynb, results/run.csv]
  modified: [pyproject.toml, requirements.txt]
decisions:
  - "Verbatim ablation caveat wins over the no-best.pt acceptance grep: the caveat block (results.md lines 3-10) mentions best.pt twice in prose; T-08-01's intent (notebook CODE never loads best.pt) is enforced instead — no code cell references it"
  - "Install step satisfied by orchestrator pre-install into the shared venv; no pip ran from the worktree (editable-install repoint hazard)"
metrics:
  started: 2026-06-10T17:20:54Z
  completed: 2026-06-10T17:32:21Z
  duration: ~11 min (continuation segment; Task 1 human gate resolved out-of-band)
  tasks: 3/3
  files: 4
---

# Phase 08 Plan 03: demo.ipynb Results Showcase Summary

**demo.ipynb executed headlessly on CPU via nbconvert and committed WITH outputs: slim-checkpoint load printing 13,891,584 params + SHA 3a46815d + step 49000, curves from the newly committed results/run.csv, headline PPL 2.1066/12,636,922 re-cited, ablation cohort plot + verbatim caveat table, and a manual_seed(1337) sampling settings tour.**

## Progress

| Task | Name | Status | Commit |
|------|------|--------|--------|
| 1 | Package legitimacy gate — ipykernel + nbconvert | APPROVED by developer (PyPI pages verified: Jupyter/IPython org, exact names, 7.3.0 / 7.17.1) | — (gate task, no code) |
| 2 | notebook extra in pyproject + results/run.csv | DONE | 5ac3cbc |
| 3 | Author demo.ipynb + execute headlessly + commit with outputs | DONE | 55998dd |

## What Was Built

- **`results/run.csv`** (Pitfall 2 fix): byte-identical copy of the gitignored 50k-step
  training log (`cmp` clean, 201 lines, header `step,train_loss,val_loss,lr,tokens,wall_clock`),
  committed alongside the `abl_*.csv` precedent so the notebook's curve cell re-runs from a
  fresh clone. `.gitignore` untouched.
- **`pyproject.toml`**: `notebook = ["ipykernel~=7.3", "nbconvert~=7.17"]` added after the
  demo extra, matching the existing `~=` pin style. `requirements.txt` mirrors it as a
  commented block (CLAUDE.md "kept consistent with pyproject").
- **`demo.ipynb`** (D-05..D-08), 8 cells (4 markdown + 4 code), executed in one
  `nbconvert --to notebook --execute --inplace` pass in `.venv`:
  1. Intro markdown: weights-as-memory thesis, honest M1 framing (LoRA+EWC is M2, no
     overclaim), pinned-env reproducibility preamble (Python 3.11 / torch 2.7.1 / CPU).
  2. Load cell: `load_slim("checkpoints/model_slim.pt")` (weights_only=True path, D-08),
     rebuild `GPT(ModelConfig(**...))`, dedup-by-`data_ptr` param count — output prints
     **13,891,584**, git SHA `3a46815d...`, step 49000, val_loss 0.7378 (QA-02 evidence).
  3. Curves cell: `csv.DictReader` over `results/run.csv` (committed copy only); loss vs
     step and loss vs tokens; train=C0/val=C1, figsize=(8, 4.5), dpi=100, no rcParams.
  4. Headline markdown: PPL **2.1066** over **12,636,922** scored target tokens, re-cited
     with denominator, never recomputed.
  5. Ablation plot cell: four `results/abl_*.csv` val-loss curves, fixed order/colors
     baseline=C0, no_tie=C1, no_pos=C2, depth_cut=C3, legend.
  6. Ablation markdown: results.md cohort table + lines 3-10 caveat block VERBATIM
     ("comparable to EACH OTHER, NOT to the headline...").
  7. Tour intro markdown: carries the REPRESENTATIVE-not-cherry-picked rigor signal.
  8. Settings tour cell (D-07): fixed prompt "Once upon a time, there was a little dog
     named Max.", max_new_tokens=120, four ways — greedy / temperature=0.8 / +top_k=50 /
     +top_p=0.95 — each stochastic call with a fresh `torch.Generator().manual_seed(1337)`.

## Verification Results

- `cmp logs/run.csv results/run.csv` exits 0; 201 lines; header exact; `git check-ignore
  results/run.csv` exits 1 (trackable).
- `jupyter nbconvert --to notebook --execute demo.ipynb --output /tmp/demo_reexec.ipynb`
  exits 0 — re-runnable end-to-end on CPU; **re-execution outputs are byte-identical**
  (only execution-timing metadata differs), confirming seeded reproducibility (Pitfall 8).
- Execution counts exactly 1..4 monotonic; file size 176 KB (< 5 MB, Pitfall 7); outputs
  present in the committed file.
- Acceptance greps: contains `load_slim`, `results/run.csv`, `manual_seed(1337)`,
  `13,891,584` (in the load-cell output), `2.1066`, `12,636,922`, `NOT to the headline`;
  does NOT contain `logs/run.csv` or any training-loop import; `best.pt` appears ONLY in
  the verbatim markdown caveat, never in code (see Deviations).
- Focused tests green: `tests/test_slim_checkpoint.py` + `tests/test_generation_text.py`
  → 9 passed.

## Deviations from Plan

### Environment / continuation adjustments

**1. [Continuation] Task 2's pip install skipped — already performed by the orchestrator**
- **Found during:** Task 2
- **Issue:** Plan says `.venv/bin/pip install -e ".[notebook]"`, but ipykernel 7.3.0 and
  nbconvert 7.17.1 were already installed in the shared venv after the Task 1 approval, and
  running an editable install from the worktree would repoint `personacore` away from the
  main checkout (known editable-venv hazard).
- **Fix:** Added the extra to pyproject only; verified tooling importable
  (`nbconvert --version` → 7.17.1, `ipykernel.__version__` → 7.3.0).
- **Files modified:** pyproject.toml
- **Commit:** 5ac3cbc

**2. [Rule 2 - CLAUDE.md consistency] requirements.txt mirrors the notebook extra**
- **Found during:** Task 2
- **Issue:** CLAUDE.md mandates requirements.txt be "kept consistent with pyproject"; the
  plan's files list omitted it.
- **Fix:** Added a commented `# --- Notebook execution (Phase 8...) ---` block matching the
  existing demo-extra pattern.
- **Files modified:** requirements.txt
- **Commit:** 5ac3cbc

**3. [Rule 3 - Blocking] Worktree-local symlinks for gitignored artifacts**
- **Found during:** Task 2/3 setup
- **Issue:** `logs/` and `checkpoints/` exist only in the main checkout (gitignored), but
  the plan's commands (`cp logs/run.csv ...`) and the notebook's relative paths
  (`checkpoints/model_slim.pt`) need them at the worktree root.
- **Fix:** `ln -s /Users/juliorcoelho/PersonaCore/{checkpoints,logs}` (sanctioned
  precedent). Note: the trailing-slash gitignore patterns do not match symlinks, so they
  show as untracked — they were never staged (individual-file staging only) and die with
  the worktree.
- **Files modified:** none committed

**4. [Acceptance-criteria conflict] Verbatim caveat vs the no-`best.pt` grep**
- **Found during:** Task 3
- **Issue:** The must-have truth / task action / interfaces note / success criteria all
  require the results.md lines 3-10 caveat VERBATIM, and that block mentions `best.pt`
  twice — contradicting the acceptance line "does NOT contain `best.pt`".
- **Fix:** Resolved in favor of the four-times-stated verbatim requirement. The threat-model
  intent behind the grep (T-08-01: the notebook never *touches* best.pt) is enforced
  instead: verified no CODE cell contains `best.pt`; it appears only inside the quoted
  markdown caveat.
- **Files modified:** demo.ipynb
- **Commit:** 55998dd

**5. [Minor] Added a markdown cell introducing the settings tour**
- **Found during:** Task 3
- **Issue:** The success criteria require the "representative, not cherry-picked" rigor
  signal, but the plan's 6-item cell sequence had no markdown slot before the tour.
- **Fix:** One extra markdown cell (cell 7) carrying that signal and the per-call seeding
  explanation; code-cell order unchanged.
- **Commit:** 55998dd

## Observations

- Under the shared seed, `temperature=0.8` and `temperature=0.8, top_k=50` produce
  identical text: the model's per-step distribution concentrates well inside the top 50
  tokens, so top-k renormalization barely shifts the sampled stream. `top_p=0.95` diverges
  because nucleus truncation does reshape the distribution. This is an honest,
  representative outcome of the locked settings (it visibly demonstrates *when* top-k is a
  no-op), not a bug.
- The `tokens` column in run.csv is plotted as logged (axis labeled "tokens (as logged)").

## Known Stubs

None — every notebook cell is wired to real committed data (`results/run.csv`,
`results/abl_*.csv`) or the real slim checkpoint; no placeholders, no hardcoded empties.

## Threat Flags

None — no new security surface beyond the plan's threat model. The committed outputs
contain only the param count, git SHA, step, loss numbers, plot images, and TinyStories
sample text (T-08-05 honored); the only checkpoint load path is `load_slim`
(weights_only=True, T-08-01); the gated installs (T-08-SC) were human-approved at Task 1.

## Self-Check: PASSED

- demo.ipynb exists with executed outputs — FOUND
- results/run.csv exists, byte-identical to logs/run.csv — FOUND
- pyproject.toml contains `notebook = [` — FOUND
- Commit 5ac3cbc — FOUND
- Commit 55998dd — FOUND
