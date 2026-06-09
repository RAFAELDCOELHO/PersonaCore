---
phase: 07-evaluation
plan: 03
subsystem: evaluation
tags: [ablation, ablation-cohort, calibration, perplexity, weight-tying, positional-embedding, eval]
requires:
  - personacore.training.train (untouched harness — keyword-only, loop.py:150)
  - personacore.evaluation.perplexity (Plan 01 — (ppl, total_tokens) deterministic sweep)
  - personacore.config.ModelConfig.weight_tying / use_pos_emb (Plan 02 additive flags)
  - personacore.config.RuntimeConfig (.device, MPS-aware)
  - personacore.preflight.preflight_device (strict GATE)
  - personacore.seeding.seed_everything (per-variant fairness re-seed)
  - personacore.model.GPT
provides:
  - scripts/run_ablations.py (calibration + 4-run fair ablation cohort driver)
  - results/results.md (committed EVAL-03 comparison table)
affects:
  - results/abl_*.csv (per-run curves, written by train()'s CSVLogger on the manual M3 run)
tech-stack:
  added: []
  patterns:
    - "Thin no-argparse cohort driver: preflight GATE then RuntimeConfig, seed_everything before each variant build"
    - "Fair single-knob ablation: ONE shared TrainConfig (seed/LR/warmup/budget) reused across all runs; only the model knob differs"
    - "Calibration from the val-loss curve: smallest max_steps where slope flattened AND loss in coherent band, then locked as a module constant (D-07)"
    - "count_parameters dedup-by-data_ptr in the driver (tied head counted once; untied head adds vocab*n_embd)"
key-files:
  created:
    - scripts/run_ablations.py
    - results/results.md
  modified: []
decisions:
  - "Cohort fairness rests on re-seeding the GLOBAL numpy RNG before each variant: seed_everything makes the data sampler's draws (training/data.py:85 np.random.randint) bit-for-bit identical across variants; only the torch init stream (and the ablated knob) differs — so weights vary but the data does not (the variable under test, not a confound)"
  - "depth_cut uses n_layer=3 (not a width cut): halving depth needs no head-divisibility constraint and yields the cleanest -5,323,392 param delta"
  - "The multi-hour cohort run (~6.6h on this M3 at measured ~0.75 s/step for calibration 8k + 4x6k steps) is a MANUAL M3 artifact (T-07-07: accept) — committed driver wiring is verified statically; results.md PPL/val-loss cells are filled by the by-hand run"
  - "REDUCED_MAX_STEPS is a locked module constant fed BY calibrate(); calibrate() recommends from the curve but the cohort uses the constant so the committed run is reproducible without re-reading the curve each time"
metrics:
  duration_min: 6
  tasks: 2
  files: 2
  completed: 2026-06-09
---

# Phase 7 Plan 03: Architecture Ablation Cohort Summary

`scripts/run_ablations.py`, a thin no-argparse driver that calibrates a fair reduced step budget then trains a fresh baseline plus three single-knob variants (no-weight-tying, no-positional-embedding, depth-cut 6→3) through the UNTOUCHED `train()` harness at identical seed/data/LR/budget, scores each with the deterministic Plan-01 `perplexity()` sweep, and assembles the committed `results/results.md` EVAL-03 comparison table — the deliverable that isolates ONE design choice per variant.

## What Was Built

- **`scripts/run_ablations.py`** — thin no-CLI driver mirroring `scripts/pretrain_tinystories.py`:
  `PYTORCH_ENABLE_MPS_FALLBACK=1` set before `import torch`; `_REPO_ROOT`-relative `TRAIN_BIN`/`VAL_BIN`
  and the TRACKED `RESULTS_DIR` (abl checkpoints go to the gitignored `checkpoints/`); the two-object
  device pattern (`preflight_device(strict=True)` GATE, then the SEPARATE `runtime = RuntimeConfig()`).
  - `KNOBS = {"baseline": {}, "no_tie": {"weight_tying": False}, "no_pos": {"use_pos_emb": False}, "depth_cut": {"n_layer": 3}}`
    with the in-venv-verified param counts in comments.
  - `calibrate(runtime)` — trains ONE fresh baseline (~8k steps) at the real `TrainConfig` LR with
    `eval_interval=250`, reads the val-loss curve via `_read_val_curve`, and recommends the smallest
    `max_steps` where the slope has flattened (recent-1k improvement < 15% of the first-1k improvement)
    AND the loss is in the coherent band (~1.0–1.3). Prints the recommendation; the executor locks it.
  - `run_cohort(runtime)` — ONE shared `cfg_reduced = TrainConfig(max_steps=REDUCED_MAX_STEPS)` reused
    across ALL four runs; `seed_everything(SEED)` immediately before each `GPT(ModelConfig(**knob))`
    (train() self-seeds only when `model is None`, loop.py:220 — the driver owns the seed); the
    untouched `train(...)` call; re-load the OWN `checkpoints/abl_{name}.pt` (`weights_only=False`,
    T-07-05) and score with `perplexity(model, VAL_BIN, ModelConfig().block_size, runtime.device)`.
  - `count_parameters` dedups by `data_ptr` (tied head counted once; untied head adds `vocab*n_embd`).
  - `write_results_table` — assembles `results/results.md` (markdown only, no pickle — T-07-06).
- **`results/results.md`** — the committed EVAL-03 comparison table: four rows
  (baseline 13,891,584 / no_tie 17,037,312 / no_pos 13,793,280 / depth_cut 8,568,192), columns
  `variant | param count | held-out PPL (reduced budget) | best val-loss | what this shows` (D-08), the
  D-06 reduced-budget framing, the separate 50k `best.pt` headline note (2.1066 over 12,636,922 tokens),
  and the deferred strided-PPL footnote.

## Task Commits

| Task | Name | Type | Commit | Files |
|------|------|------|--------|-------|
| 1 | Calibration + 4-run fair cohort driver | feat | `a8aeabe` | scripts/run_ablations.py |
| 2 | Committed EVAL-03 comparison table | docs | `1b3d1a7` | results/results.md |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded over-length lines to satisfy ruff (E501)**
- **Found during:** Task 1 (`ruff check` / `ruff format`).
- **Issue:** Eleven docstring / KNOBS-comment / markdown-list lines exceeded the 100-char limit
  (E501), and `ruff format` wanted to reflow the file.
- **Fix:** Trimmed the over-length comments and table/note strings, then ran `ruff format`. No behavior
  change — the verified param-count comments and the table content are preserved, only wrapping changed.
- **Files modified:** scripts/run_ablations.py
- **Commit:** `a8aeabe`

## Manual M3 Cohort Run (deferred to by-hand execution — T-07-07)

The static driver wiring is fully verified (see Verification). The actual cohort training is a
multi-hour artifact and is NOT run inside this automated session:

- **Measured throughput on this M3 (MPS, fp32):** ~0.75 s/step for the baseline `GPT(ModelConfig())`
  through the real `train()` (30-step probe: 22.4 s).
- **Projected cohort wall-clock:** calibration 8k + 4 × 6k = 32k steps ≈ **~6.6 h** — exceeds a single
  automated session and is exactly the T-07-07 "accept" case (run by hand, not CI, no remote trigger).
- **What the manual run does:** `python scripts/run_ablations.py` calibrates `REDUCED_MAX_STEPS`,
  trains the four variants, writes `results/abl_*.csv` (via train()'s CSVLogger) and `abl_calibration.csv`,
  and OVERWRITES `results/results.md` with the measured held-out PPL + best-val-loss cells.
- **Calibrated REDUCED_MAX_STEPS:** locked at the module constant `REDUCED_MAX_STEPS = 6000` as the
  starting committed budget; `calibrate()` recomputes the recommendation from the curve on the by-hand
  run and the executor updates the constant if the measured flatten-point differs.

## Known Stubs

The PPL and best-val-loss cells in `results/results.md` are marked `_pending M3 cohort run_` rather than
fabricated numbers — this is the honest, portfolio-integrity choice (T-07-07 classifies the cohort run
as a manual M3 artifact). The param-count column is final and verified now; the driver overwrites the
pending cells on the by-hand run. This is an intentional, documented deferral, not a wiring gap: the
driver is fully wired to the real `train()`, `perplexity()`, the real corpus, and the abl checkpoints —
verified by the throughput probe actually training the baseline GPT through `train()` on MPS.

## Verification

- `python -c "import ast; ast.parse(open('scripts/run_ablations.py').read())"` → exit 0.
- `grep -c seed_everything` = 7 (≥1), `perplexity(` = 5 (≥1), `preflight_device(strict=True)` = 2 (≥1),
  `RuntimeConfig()` = 3 (≥1), knob grep (`weight_tying.*False\|use_pos_emb.*False\|n_layer.*3`) = 3 (≥1),
  `argparse` = 0 (==0), `results` = 13 (≥1).
- `ruff check scripts/run_ablations.py` + `ruff format --check scripts/run_ablations.py` → clean.
- `results/results.md` exists; `git check-ignore results/results.md` → empty (tracked); all four variant
  rows present with verified param counts; `13,891,584` present; reduced-budget framing (×3) and the
  strided-PPL footnote (×3) present.
- **Driver-is-really-wired probe (M3, MPS):** a 30-step run of `GPT(ModelConfig())` through the actual
  `train()` on the real `data/train.bin`/`val.bin` succeeded on `device=mps` (~0.75 s/step) — confirming
  the train() call site, the memmap data path, and the device resolution all work end-to-end. The full
  multi-hour cohort is the deferred manual artifact above.

## TDD Gate Compliance

This plan is `type: execute` with two `type="auto"` (non-TDD) tasks — no RED/GREEN gate applies. The
flags this ablation exercises were delivered TDD-first in Plans 01 (RED) and 02 (GREEN).

## Self-Check: PASSED

Files created (all FOUND):
- scripts/run_ablations.py
- results/results.md

Commits (all FOUND): `a8aeabe`, `1b3d1a7`.
