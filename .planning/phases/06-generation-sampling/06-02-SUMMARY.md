---
phase: 06-generation-sampling
plan: 02
subsystem: generation
tags: [generation, decode-core, eos-stop, context-crop, determinism, tdd]
requires:
  - "personacore.generation.sampling.next_token (06-01 — the single logit->id decision)"
  - "personacore.model.GPT forward contract (logits, loss; asserts T <= block_size — Phase 4)"
  - "personacore.config.ModelConfig (block_size / eos_id on model.config)"
  - "torch (2.7.1)"
provides:
  - "personacore.generation.core: generate (yields new ids, EOS-stop, context-crop) + collect (drain to (1, prompt_len+n) LongTensor)"
  - "personacore.generation barrel now re-exports generate, collect"
  - "tests/test_generation.py: all 8 GEN-01/02/03 tests live (0 skips)"
affects:
  - "06-03 (generate_text streaming wrapper builds on generate/collect)"
  - "Phase-7 evaluation (consumes collect for output-shape/eval assertions)"
  - "Phase-8 demo (via the 06-03 wrapper over generate)"
tech-stack:
  added: []
  patterns:
    - "@torch.no_grad() Python generator yielding one token id per step (nanoGPT decode loop, supersedes loop.py::sample)"
    - "Mandatory context crop idx[:, -bs:] before each forward (gpt.py:190 assert) — generating past block_size never raises"
    - "EOS-stop-without-yield (D-05): return BEFORE yielding/appending eos_id — simultaneously stops and trims the trailing token"
    - "block_size / eos_id read from model.config — never hardcoded literals"
    - "Seed model init in shape tests so greedy argmax avoids eos_id under a perturbed global RNG (Pitfall 2)"
key-files:
  created:
    - "src/personacore/generation/core.py"
  modified:
    - "src/personacore/generation/__init__.py"
    - "tests/test_generation.py"
decisions:
  - "generate is a generator (yield per step) with collect as a thin drain helper (D-04 one decode path, D-02 full prompt+new sequence) — no batch (Phase-6 scope fence), single (1, T) sequence only"
  - "EOS is detected via int(next_id) == eos_id and the generator returns immediately, neither yielding nor appending it (D-05) — collect's last id is therefore never eos_id and the sequence is trimmed"
  - "No generate/sample method added to GPT (preserves the LoRA/EWC seam); training/loop.py::sample left untouched (D-11 supersede-without-rewire)"
metrics:
  duration: "~12 min"
  completed: "2026-06-06"
  tasks: 2
  files: 3
---

# Phase 6 Plan 02: Shared Generator Core (generate / collect) Summary

Built `core.py` — the single token-level decode path (D-04) behind the GEN-03 tests, Phase-7
eval, and (via the 06-03 wrapper) the Phase-8 demo. `generate(model, idx, ...)` is an
`@torch.no_grad()` Python generator that crops context, delegates the logit->id decision to
`next_token`, yields each new id, and stops on EOS without yielding it (D-05); `collect`
drains it into the full `(1, prompt_len + n)` LongTensor (D-02). This turned the five
core-dependent GEN-02/GEN-03 tests GREEN, leaving `tests/test_generation.py` fully live with
zero skips, without touching the training loop or adding any method to `GPT`.

## What Was Built

- **`src/personacore/generation/core.py`** — `generate` keeps the superseded
  `training/loop.py::sample` idiom (the `@torch.no_grad()` decorator, the
  `for _ in range(max_new_tokens)` bound, the `logits[:, -1, :]` slice, the `torch.cat`
  append) and ADDS: the mandatory context crop `idx_cond = idx if idx.size(1) <= bs else
  idx[:, -bs:]` (so the `gpt.py:190` `assert T <= block_size` never fires), delegation to
  `next_token` (temperature / top-k / top-p / greedy / seeded `generator`), and the D-05
  EOS-stop — `if int(next_id) == eid: return` BEFORE yielding/appending. `bs` and `eid`
  default from `model.config.block_size` / `model.config.eos_id` (no magic literals).
  `collect` is a thin drain: `out = idx`, concatenate each yielded `[[tok]]` preserving
  `idx`'s dtype/device, return the full sequence.
- **`src/personacore/generation/__init__.py`** — barrel now also re-exports `generate`,
  `collect` (the 06-01 sampling exports are kept; `generate_text` joins in 06-03).
- **`tests/test_generation.py`** — removed the five `@pytest.mark.skip` markers and the
  now-dead skip scaffold (`_SKIP_CORE`, `_CORE_AVAILABLE`, the try/except import). All eight
  GEN-01/02/03 tests run on the tiny CPU GPT fixture.

## Task Commits

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | generate() generator core + collect() drain helper | `3e23f8c` | src/personacore/generation/core.py, src/personacore/generation/__init__.py |
| 2 | Un-skip and green the five core GEN-02/GEN-03 tests | `accf37f` | tests/test_generation.py |

## TDD Gate Compliance

- This `type: tdd` plan's RED commit landed in 06-01 (`da09697`) — the five core tests were
  written in full but `@pytest.mark.skip`-marked because `core.py` did not yet exist (genuine
  RED: invoking them would `NameError`/`ImportError` on `generate`/`collect`).
- Task 1 is the GREEN commit (`3e23f8c` — `feat(...)`): `core.py` makes the imports resolve and
  the five tests pass.
- Task 2 (`accf37f` — `test(...)`) removes the skip markers so the GREEN tests actually run in
  the suite. RED (`test`, 06-01) -> GREEN (`feat`, 06-02) gate sequence is present in git log.
- No separate REFACTOR commit was needed (the GREEN implementation was already clean).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Order-dependent flake in `test_output_shape` (Pitfall 2)**
- **Found during:** Task 2 full-suite verification (`pytest -q`). The test passed in isolation
  and in `test_generation.py` alone, but FAILED in the full suite (`assert torch.Size([1,5]) ==
  (1, 7)`).
- **Issue:** The committed scaffold built the tiny model UNSEEDED and asserted a fixed output
  shape plus "no EOS in the body". An earlier suite test mutates the global torch RNG, so the
  tiny model's random init shifted and its greedy argmax landed on `eos_id` (15) within `n`
  steps — the D-05 EOS-stop then correctly trimmed the output, breaking the shape assert. The
  plan's Task-2 action for this test explicitly anticipated this ("Use a fixture/seed where EOS
  does not appear"); the 06-01 scaffold omitted the seed.
- **Fix:** Added `torch.manual_seed(1)` immediately before `_tiny_model()` in
  `test_output_shape` (model init draws from the freshly-seeded global RNG, fixing the weights
  regardless of prior RNG state; seed 1 yields a greedy trajectory that never hits `eos_id`).
  Verified stable across three back-to-back runs and the full suite.
- **Files modified:** tests/test_generation.py
- **Commit:** `accf37f`

**2. [Rule 3 - Blocking] Removed dead skip scaffold + fixed import ordering**
- **Found during:** Task 2 (`ruff check`). After deleting the five `@_SKIP_CORE` markers, the
  `_SKIP_CORE` / `_CORE_AVAILABLE` / `pytest` import / try-except were unused (ruff F401/F811
  and un-sorted import block).
- **Fix:** Replaced the try/except core-import scaffold with a direct
  `from personacore.generation import collect` (the only core symbol the tests call), removed
  the unused `pytest`/`_SKIP_CORE`/`_CORE_AVAILABLE`, and let ruff sort the import block.
- **Files modified:** tests/test_generation.py
- **Commit:** `accf37f` (folded into the Task-2 commit since discovered there)

## Verification Results

- `pytest tests/test_generation.py -x -q` -> 8 passed, 0 skipped.
- `pytest tests/test_generation.py::test_eos_stop ::test_past_block_size_no_crash` -> pass
  (EOS fires early, last id != eos_id, sequence trimmed; past-block_size crop never raises).
- `pytest tests/test_generation.py::test_seeded_sampling_deterministic` -> pass (two isolated
  `torch.Generator().manual_seed(0)` instances, not the global RNG).
- Full suite `pytest -q` -> 110 passed, 1 skipped (the pre-existing skip), no regressions.
  `test_generation.py` repeated 3x -> 8 passed each time (flake fix stable).
- `ruff check` + `ruff format --check` on all three files -> clean.
- Acceptance greps: `@torch.no_grad()` decorates `generate`; `idx[:, -bs:]` +
  `model.config.block_size` present; NO literal `256`/`8184`; `next_token(` called; no method
  added to GPT; `training/loop.py` and `gpt.py` unchanged (`git diff` empty); NO
  `@pytest.mark.skip` and NO `best.pt` in the test file.

## Notes for Downstream Plans

- 06-03's `generate_text` should wrap `generate` (token-id stream) with tokenizer decode +
  the absurd-value `max_new_tokens` cap (threat T-06-02 mitigation lives in the caller-facing
  wrapper, not the core loop).
- Phase-7 eval should consume `collect` for the `(1, prompt_len+n)` LongTensor; remember the
  returned length is `< prompt_len + max_new_tokens` whenever EOS fires (D-05 trim).
- `generate` is single-sequence (`(1, T)`) by design (Phase-6 scope fence) — batched decode is
  explicitly out of scope.

## Self-Check: PASSED

- FOUND: src/personacore/generation/core.py
- FOUND: src/personacore/generation/__init__.py (re-exports generate, collect)
- FOUND: tests/test_generation.py (8 live tests, 0 skips)
- FOUND: commit 3e23f8c
- FOUND: commit accf37f
