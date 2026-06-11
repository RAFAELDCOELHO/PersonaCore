---
phase: 06-generation-sampling
plan: 01
subsystem: generation
tags: [sampling, top-p, top-k, temperature, tdd, generation]
requires:
  - "personacore.model.GPT (forward contract, Phase 4)"
  - "personacore.config.ModelConfig"
  - "torch (2.7.1)"
provides:
  - "personacore.generation.sampling: apply_temperature, top_k_filter, top_p_filter, next_token"
  - "personacore.generation barrel re-exporting the public sampling surface"
  - "tests/test_generation.py: RED scaffold + tiny CPU GPT fixture for all 8 GEN-01/02/03 behaviors"
affects:
  - "06-02 (core generate/collect consumes next_token; removes skip on 5 core tests)"
  - "06-03 (generate_text streaming wrapper joins the barrel)"
tech-stack:
  added: []
  patterns:
    - "Pure side-effect-free logit transforms over (1, vocab) last-position tensors (no batch — Phase-6 scope fence)"
    - "Defensive .clone()/masked_fill so standalone filters never mutate caller logits"
    - "torch.Generator seed isolation for sampled determinism (never the global RNG)"
    - "skip-with-reason for cross-plan-dependent tests so the suite collects cleanly"
key-files:
  created:
    - "src/personacore/generation/__init__.py"
    - "src/personacore/generation/sampling.py"
    - "tests/test_generation.py"
  modified: []
decisions:
  - "top-p nucleus boundary uses cum_probs >= p (not > p) so a token landing EXACTLY on the cumulative-p boundary closes the nucleus rather than pulling in the next token — resolves assumption A1 / Pitfall 5 against the hand-computed [0.5,0.3,0.15,0.05]/p=0.8 -> top-2 contract"
metrics:
  duration: "~9 min"
  completed: "2026-06-06"
  tasks: 2
  files: 3
---

# Phase 6 Plan 01: Generation Test Scaffold & Sampling Primitives Summary

Stood up the Phase-6 RED test surface (8 GEN-01/02/03 behaviors on a tiny CPU GPT fixture) and
the four pure sampling transforms (`apply_temperature`, `top_k_filter`, `top_p_filter`,
`next_token`) so the three GEN-01 sampling tests — including the hand-computed top-p nucleus
exactness test that pins the only genuinely new logic in the phase — go GREEN this wave.

## What Was Built

- **`tests/test_generation.py`** — RED scaffold + a `_tiny_model()` GPT
  (`block_size=8, vocab_size=16, eos_id=15`, never a trained checkpoint). All 8 tests named per
  06-VALIDATION.md. The three GEN-01 sampling tests assert real `top_k`/`top_p`/`temperature`
  behavior; the five GEN-02/GEN-03 core tests (EOS-stop, context-crop, output-shape, greedy &
  seeded determinism) are written in full but `@pytest.mark.skip(reason=... 06-02)` pending
  `core.py`, so the suite collects cleanly now and removing the skip in 06-02 immediately
  exercises them.
- **`src/personacore/generation/sampling.py`** — four pure logit transforms over a `(1, vocab)`
  last-position tensor. `top_k_filter` is the verbatim nanoGPT idiom (defensive `.clone()`);
  `top_p_filter` is the sort → cumsum-softmax → shift-right nucleus mask; `next_token` composes
  `temperature -> top-k -> top-p -> softmax -> multinomial(generator)` with a greedy `argmax`
  short-circuit (no RNG). `top_k`/`top_p` stack when both set.
- **`src/personacore/generation/__init__.py`** — barrel mirroring the tokenizer convention,
  re-exporting the public sampling surface (`generate`/`collect`/`generate_text` join in
  06-02/06-03).

## Task Commits

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | RED generation test scaffold + tiny CPU GPT fixture | `da09697` | tests/test_generation.py |
| 2 | Pure sampling primitives (temperature/top-k/top-p/next_token) | `178f3ec` | src/personacore/generation/sampling.py, src/personacore/generation/__init__.py, tests/test_generation.py |

## TDD Gate Compliance

- Task 1 committed the failing RED scaffold (`test(...)`); at that point `tests/test_generation.py`
  errored on import because `personacore.generation` did not yet exist — the genuine RED state.
- Task 2 committed the implementation (`feat(...)`) that makes the 3 GEN-01 tests GREEN and the
  module importable. RED `test(...)` then GREEN `feat(...)` gate sequence is present in git log.
- No separate REFACTOR commit was needed (the GREEN implementation was already clean).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] top-p nucleus boundary off-by-one at exactly cumulative p**
- **Found during:** Task 2 (running `test_top_p_nucleus_exact`).
- **Issue:** The plan-locked idiom `sorted_mask = cum_probs > p` keeps one token too many when a
  token lands EXACTLY on the cumulative-`p` boundary. On the hand-computed `[0.5,0.3,0.15,0.05]`
  with `p=0.8` (cumulative `[0.5, 0.8, 0.95, 1.0]`), `> p` plus shift-right kept the top-3, but
  the pinned A1 contract (Task 1's `test_top_p_nucleus_exact`) requires exactly the top-2.
- **Fix:** Changed the comparison to `cum_probs >= p` so the boundary token closes the nucleus
  instead of pulling in the next token. This is the intended Pitfall-5 semantics (the test vector
  was deliberately chosen to sum to `p` at the nucleus edge). Also verified it keeps
  `test_top_k_top_p_support` correct (top-2 nucleus there too).
- **Files modified:** src/personacore/generation/sampling.py
- **Commit:** `178f3ec`

**2. [Rule 3 - Blocking] Lint/acceptance cleanup in the test scaffold**
- **Found during:** Task 2 verification (`ruff check` + the `best.pt`/`tokenizer.json` acceptance grep).
- **Issue:** The Task-1 scaffold imported `next_token` (never called → ruff F401) and its
  docstring/comment used the literal strings `best.pt` / `tokenizer.json`, which tripped the
  acceptance criterion "grep confirms NO reference to `best.pt` or `tokenizer.json`".
- **Fix:** Removed the unused `next_token` import and rephrased the two literal mentions to
  "trained checkpoint" / "vocab file" (the test never loads either — the intent is unchanged).
- **Files modified:** tests/test_generation.py
- **Commit:** `178f3ec` (folded into the Task-2 commit since it was discovered there)

## Verification Results

- `pytest tests/test_generation.py --co -q` → 8 tests collected, no collection errors.
- `pytest tests/test_generation.py -q` → 3 passed, 5 skipped (core tests pending 06-02).
- GEN-01 trio (`test_top_k_top_p_support`, `test_temperature`, `test_top_p_nucleus_exact`) → all pass.
- Full suite `pytest -q` → 105 passed, 6 skipped (5 new core-pending + 1 pre-existing), no regressions.
- `ruff check` + `ruff format --check` on the new files → clean.
- Barrel import `from personacore.generation import top_k_filter, top_p_filter, next_token` → resolves.

## Notes for Downstream Plans

- 06-02 must add `core.py` (`generate`/`collect`), import it into the generation barrel, and
  remove the `@pytest.mark.skip` (`_SKIP_CORE`) decorator from the five GEN-02/GEN-03 tests — they
  are already written in full and will exercise EOS-stop, context-crop, output-shape, and both
  determinism idioms immediately.
- `next_token` is the single logit→id decision point the core should delegate to; it already
  threads a `torch.Generator` for seeded sampling (the GEN-03 `test_seeded_sampling_deterministic`
  idiom) and short-circuits greedy with `argmax`.

## Self-Check: PASSED

- FOUND: src/personacore/generation/sampling.py
- FOUND: src/personacore/generation/__init__.py
- FOUND: tests/test_generation.py
- FOUND: commit da09697
- FOUND: commit 178f3ec
