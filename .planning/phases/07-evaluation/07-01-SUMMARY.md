---
phase: 07-evaluation
plan: 01
subsystem: evaluation
tags: [perplexity, eval, tdd, ablation-scaffold]
requires:
  - personacore.model.GPT (forward (logits, loss) contract)
  - personacore.config.ModelConfig
  - data/val.bin memmap idiom (training/data.py:84)
provides:
  - personacore.evaluation.perplexity (deterministic full-corpus PPL sweep)
  - tests/test_perplexity.py (EVAL-01 accounting oracle — green)
  - tests/test_ablation_config.py (EVAL-03 flag scaffold — RED until Plan 02)
affects:
  - scripts/evaluate.py (Plan 02 — headline PPL driver, consumes perplexity())
  - scripts/run_ablations.py (Plan 03 — cohort PPL column, consumes perplexity())
tech-stack:
  added: []
  patterns:
    - "Deterministic non-overlapping window PPL (reduction='sum', exact auditable denominator)"
    - "np.memmap mode='r' re-open-per-call (nanoGPT RSS-leak avoidance)"
    - "tiny-CPU-fixture test style (GPT block_size=8/vocab=16); brute-force oracle independent of SUT"
key-files:
  created:
    - src/personacore/evaluation/__init__.py
    - src/personacore/evaluation/perplexity.py
    - tests/test_perplexity.py
    - tests/test_ablation_config.py
  modified: []
decisions:
  - "Auditable denominator is Sigma(len(window)-1) over scored windows; with the [i:i+block_size+1] slice at stride block_size consecutive windows share a boundary token, so a cleanly-tiling corpus yields exactly corpus_len-1 (only token 0 is never predicted) — NOT corpus_len-n_windows as the RESEARCH shorthand suggested"
  - "reduction='sum' recomputed from forward logits; the model's returned MEAN loss is ignored entirely (Pitfall 2)"
  - "evaluation/__init__.py re-exports only perplexity; a strided/sliding-window variant is deferred (D-01 locks non-overlapping)"
metrics:
  duration_min: 4
  tasks: 2
  files: 4
  completed: 2026-06-09
---

# Phase 7 Plan 01: Perplexity + Ablation Test Scaffold Summary

Deterministic full-corpus `perplexity()` whose token accounting is proven against an independent brute-force per-token CE oracle on a tiny CPU fixture, plus the Wave-0 RED test scaffold for the EVAL-03 ablation flags (green in Plan 02).

## What Was Built

- **`src/personacore/evaluation/perplexity.py`** — `@torch.no_grad() perplexity(model, val_bin_path, block_size, device, batch_size=32)`. Opens the corpus with `np.memmap(..., mode="r")`, tiles non-overlapping `block_size` windows (`for i in range(0, n-1, block_size)`, slice `[i : min(i+block_size+1, n)]`), skips windows with `numel < 2`, recomputes `F.cross_entropy(..., reduction="sum")` from the forward logits (ignoring the model's mean loss), and returns `(exp(total_ce/total_tokens), total_tokens)` so the denominator is auditable.
- **`src/personacore/evaluation/__init__.py`** — barrel re-exporting `perplexity` (mirrors `generation/__init__.py`).
- **`tests/test_perplexity.py`** — 3 EVAL-01 cases, all green: `test_matches_bruteforce` (PPL == independent brute-force reference, atol 1e-4), `test_token_count` (exact `Sigma(L-1)` denominator audit), `test_partial_window` (final partial window scored; single dangling trailing token skipped).
- **`tests/test_ablation_config.py`** — 3 EVAL-03 cases pinning `weight_tying`/`use_pos_emb` flag semantics with the in-venv-verified param-count literals (13,891,584 / 17,037,312 / 13,793,280). RED-by-design until Plan 02 adds the flags.

## Task Commits

| Task | Name | Type | Commit | Files |
|------|------|------|--------|-------|
| 1 | Wave-0 RED test scaffold | test (RED) | `c68a9c0` | tests/test_perplexity.py, tests/test_ablation_config.py |
| 2 | perplexity() module — full-val sweep | feat (GREEN) | `3842513` | src/personacore/evaluation/{__init__,perplexity}.py, tests/test_perplexity.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the `test_token_count` denominator assertion**
- **Found during:** Task 2 (GREEN run — the test failed `assert 319 == (320 - 40)`).
- **Issue:** The RED `test_token_count` from Task 1 encoded the RESEARCH shorthand `denominator == corpus_len - n_windows`. That formula only holds for STRICTLY disjoint windows. The verified reference implementation uses an `[i : i+block_size+1]` slice at stride `block_size`, so consecutive windows share their boundary token (the last target of one window is the first context token of the next). The true auditable denominator is `Sigma(len(window)-1)`, which for a cleanly-tiling corpus equals `corpus_len - 1` (only the corpus's very first token is never predicted), not `corpus_len - n_windows`.
- **Fix:** Rewrote the assertion to independently sum `len-1` over every scored window (the genuine audit) and added the tighter `ntok == n_tokens - 1` check for the clean-tiling case. Updated the docstring to state the real invariant.
- **Files modified:** tests/test_perplexity.py
- **Commit:** `3842513`
- **Note:** The implementation itself is the verified RESEARCH §Pattern 1 reference code, unchanged; `test_matches_bruteforce` (the authoritative oracle) passed against it on the first GREEN run, confirming the implementation is correct and only the secondary token-count assertion's arithmetic was wrong.

## TDD Gate Compliance

This plan is `type: execute` with two `tdd="true"` tasks. The RED -> GREEN sequence is in git:
1. RED: `c68a9c0` (`test(...)`) — both test files; `test_perplexity` cases fail/error until Task 2.
2. GREEN: `3842513` (`feat(...)`) — `perplexity` implementation; the 3 EVAL-01 cases pass.

## Verification

- `pytest tests/test_perplexity.py -x -q` -> 3 passed.
- `python -c "from personacore.evaluation import perplexity; print(perplexity)"` -> prints a function (barrel works).
- `grep -c 'reduction="sum"' src/personacore/evaluation/perplexity.py` -> 3 (>= 1).
- `grep -c "np.memmap" src/personacore/evaluation/perplexity.py` -> 1 (>= 1).
- Full CPU suite (`pytest -q`): **120 passed, 1 skipped** (the GPU-only fp16 smoke), 2 failed — and the 2 failures are exactly `test_ablation_config.py::test_untie` and `test_no_pos`, RED-by-design (they pass `ModelConfig(weight_tying=False)` / `ModelConfig(use_pos_emb=False)`, fields Plan 02 adds). `test_defaults_unchanged` PASSED. No existing test regressed.
- `grep -c "best.pt\|val.bin"` on both new test files -> 0 each (no checkpoint/real-corpus reads).

## Known Stubs

None. `perplexity()` is fully wired to the real `GPT.forward` contract and a real memmap; the only intentionally-RED surface is `test_ablation_config.py`, which is the Wave-0 scaffold that Plan 02 turns green (documented above).

## Self-Check: PASSED

Files created (all FOUND):
- src/personacore/evaluation/perplexity.py
- src/personacore/evaluation/__init__.py
- tests/test_perplexity.py
- tests/test_ablation_config.py

Commits (all FOUND): `c68a9c0`, `3842513`.
