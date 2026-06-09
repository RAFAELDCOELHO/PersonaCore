# Phase 7: Evaluation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-09
**Phase:** 7-evaluation
**Areas discussed:** Ablation design & budget, Perplexity protocol

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Ablation design & budget | Which 2-3 ablations + shared reduced training budget | ✓ |
| Perplexity protocol | Full-val sweep vs sampled batches; EOS/token averaging | ✓ |
| Qualitative sample curation | Prompts, sampling settings, cherry-pick vs representative | (defaults) |
| Evaluation artifacts | Where results live (script/markdown/CSV) | (defaults) |

**User's choice:** Discuss Ablations + Perplexity; accept proposed defaults for the other two.

---

## Ablations — which 2-3

| Option | Description | Selected |
|--------|-------------|----------|
| Architecture trio | no-weight-tying, no-pos-emb, depth/width cut | ✓ |
| Architecture + LR mix | 2 architecture + 1 LR/training ablation | |
| Capacity scaling | 3 sizes along one axis (PPL-vs-params curve) | |

**User's choice:** Architecture trio.
**Notes:** Strongest "why the design matters" narrative; no-weight-tying ties to the Phase-4 seam.

## Ablations — training budget

| Option | Description | Selected |
|--------|-------------|----------|
| Reduced fixed budget, re-trained baseline | Fresh baseline + 3 variants at same reduced budget; headline PPL from 50k best.pt | ✓ |
| Reduced variants vs existing 50k baseline | Cheaper but unfair (different budgets) | |
| Full 50k for all four | Maximum rigor, ~3-4× long-run cost | |

**User's choice:** Reduced fixed budget with re-trained baseline.
**Notes:** Apples-to-apples cohort; headline EVAL-01 number stays from the real 50k best.pt.

## Ablations — step budget magnitude

| Option | Description | Selected |
|--------|-------------|----------|
| Calibration-picked, ~5-10k steps | Tiny calibration finds smallest meaningful budget; ~4× ≈ a few hours | ✓ |
| Fixed ~5k, no calibration | Hard-coded, fastest, may be too short for clean deltas | |
| Match a wall-clock cap per run | Predictable time but unequal steps complicates fairness | |

**User's choice:** Calibration-picked, ~5-10k steps.

## Ablations — comparison table contents

| Option | Description | Selected |
|--------|-------------|----------|
| PPL + params + val-loss, shared seed | Columns + "what this shows" note; shared seed/data/LR/budget | ✓ |
| PPL only, minimal | Cleanest but loses param-count context | |
| Full metrics + curves | + train-time + overlaid curves; overlaps Phase 8 | |

**User's choice:** PPL + params + val-loss, shared seed.

---

## Perplexity — computation method

| Option | Description | Selected |
|--------|-------------|----------|
| Deterministic full-val sweep | Non-overlapping windows over all of val.bin; exp(total_CE/total_tokens) | ✓ |
| Reuse estimate_loss, fixed seed + more iters | Still a sampled estimate | |
| You decide | Planner picks, as long as deterministic + full coverage | |

**User's choice:** Deterministic full-val sweep.
**Notes:** New function distinct from estimate_loss; uses forward() directly.

## Perplexity — windowing + EOS handling

| Option | Description | Selected |
|--------|-------------|----------|
| Non-overlapping windows, count all tokens incl. EOS | Simple, reproducible, matches training; report token count | ✓ |
| Strided sliding window (GPT-2 style) | Rigorous standard, more compute/code | |
| Non-overlapping, exclude EOS | "Purer" fluency number, diverges from training objective | |

**User's choice:** Non-overlapping, count all tokens including EOS.
**Notes:** Report total token count alongside PPL for an auditable denominator.

---

## Claude's Discretion

- **EVAL-02 qualitative samples** — fixed story-starter prompts, Phase-6 sampling defaults,
  presented as representative (not cherry-picked) with honest selection method noted. Greedy + small
  temp/top-p spread acceptable; planner picks exact prompt set.
- **Artifacts** — standalone `eval.py`/`evaluation` module + committed results markdown table +
  per-run CSVs; Phase 8's `demo.ipynb` renders them.
- **PPL stride** — strided/sliding-window variant optional, only if cheap.

## Deferred Ideas

- Strided/sliding-window (GPT-2-style) perplexity — optional, possible writeup footnote.
- LR / training-dynamics ablations (peak-LR / warmup sweep) — considered, not selected.
- Capacity scaling curve (3/6/9 layers, PPL-vs-params) — considered, not selected.
- Overlaid per-variant val-loss curves + train-time column — overlaps Phase 8 notebook.
- `demo.ipynb` rendering of results — Phase 8 (DEMO-03).
