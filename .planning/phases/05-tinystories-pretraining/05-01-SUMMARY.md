---
phase: 05-tinystories-pretraining
plan: 01
subsystem: training
tags: [memmap, numpy, uint16, tinystories, tokenizer, nanogpt, dataloader]

# Dependency graph
requires:
  - phase: 02-from-scratch-bpe-tokenizer
    provides: frozen artifacts/tokenizer.json (vocab 8192 / eos 8184), from_json + encode(allowed_special="all")
  - phase: 03-bigram-baseline-training-harness
    provides: training/data.py get_batch (nanoGPT in-RAM sampler) + load_split doc-boundary idiom
provides:
  - get_batch_memmap(bin_path, batch_size, block_size, device) — full-corpus memmap sampler (re-opens memmap per call)
  - scripts/encode_corpus.py — run-once streaming encode of TinyStoriesV2-GPT4 .txt -> data/train.bin / data/val.bin (uint16, one EOS/doc)
  - tests/test_memmap_data.py — 4 PRE-01 data tests (roundtrip, one-EOS, in-bounds, no-leakage)
  - tests/fixtures/tinystories_fixture.txt — 4-doc <|endoftext|> micro-corpus for GPU-free tests
affects: [05-02 long run (reads train.bin/val.bin via get_batch_memmap), pretrain entry script, loop memmap branch]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Memmap re-opened per get_batch call (nanoGPT leak-avoidance, Pitfall 1)"
    - "uint16 .bin storage; int64 cast only at batch time"
    - "Streaming per-<|endoftext|> document encode (never read 2.23 GB into one string)"
    - "Atomic eos via allowed_special=all; no manual EOS injection"

key-files:
  created:
    - scripts/encode_corpus.py
    - tests/test_memmap_data.py
    - tests/fixtures/tinystories_fixture.txt
  modified:
    - src/personacore/training/data.py
    - src/personacore/training/__init__.py

key-decisions:
  - "get_batch_memmap mirrors get_batch indexing exactly (len-block-1 bound, uint16->int64 at draw, plain .to(device)); only change is re-opening np.memmap each call"
  - "encode_corpus.py streams per-document on <|endoftext|>; each doc rejoined with its marker so encode(allowed_special=all) emits exactly one atomic eos 8184 per doc — no manual EOS injection"
  - "No CUDA-only pinned-host/async-copy flags in the memmap sampler (no MPS/CPU path this phase) — docstring reworded so the pin_memory/non_blocking grep guard stays at 0"

patterns-established:
  - "Pattern 1: full-corpus uint16 memmap .bin (nanoGPT format) sampled by re-opening np.memmap per batch"
  - "Pattern 2: run-once thin no-CLI streaming encoder reusing the frozen tokenizer, with post-build EOS-count + decode round-trip sanity"

requirements-completed: [PRE-01]

# Metrics
duration: 6min
completed: 2026-06-05
---

# Phase 5 Plan 01: TinyStories Memmap Data Slice Summary

**Full-corpus data path: a `get_batch_memmap` uint16 memmap sampler (re-opened per call) plus a run-once streaming `encode_corpus.py` that turns the TinyStoriesV2-GPT4 `.txt` files into `data/train.bin`/`data/val.bin` with exactly one atomic EOS between documents — all four PRE-01 tests green.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-05T19:27:00Z
- **Completed:** 2026-06-05T19:33:08Z
- **Tasks:** 3
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments
- `get_batch_memmap` added alongside the in-RAM `get_batch`: identical nanoGPT indexing (`len-block-1` bound, `uint16->int64` at draw time, plain `.to(device)`), re-opening the memmap every call to avoid the documented RSS leak (Pitfall 1). Re-exported via the training barrel + `__all__`.
- `scripts/encode_corpus.py`: a thin no-CLI streaming encoder that reads the corpus document-by-document on `<|endoftext|>`, encodes each doc+marker through the FROZEN tokenizer (`allowed_special="all"` → atomic eos 8184), accumulates `uint16` shards, concatenates, and `tofile`s `data/train.bin`/`data/val.bin`. Post-build EOS-count + decode round-trip sanity guards a truncated/corrupt download (T-05-01).
- Wave-0 PRE-01 test scaffold: `tests/test_memmap_data.py` (roundtrip, one-EOS-between-docs, in-bounds `get_batch_memmap`, no-leakage disjoint split) + a 4-doc `tinystories_fixture.txt` for deterministic GPU-free tests.
- Full CPU suite stays green (99 passed, 1 skipped — the MPS smoke is added in Plan 02).

## Task Commits

1. **Task 1: Wave 0 RED PRE-01 test scaffold + fixture** — `ea1cd5c` (test)
2. **Task 2: get_batch_memmap memmap sampler** — `bfe4fb8` (feat, TDD GREEN)
3. **Task 3: encode_corpus.py run-once streaming encoder** — `075be1a` (feat)

_Task 2 is the TDD GREEN of the Task 1 RED tests; the implementation is a single non-test source change so a separate test commit was already landed as Task 1 (RED gate `ea1cd5c`, GREEN gate `bfe4fb8`)._

## Files Created/Modified
- `src/personacore/training/data.py` — added `get_batch_memmap` below `get_batch`
- `src/personacore/training/__init__.py` — barrel re-export + `__all__` entry for `get_batch_memmap`
- `scripts/encode_corpus.py` — run-once streaming encode to `data/train.bin`/`data/val.bin`
- `tests/test_memmap_data.py` — 4 PRE-01 data tests
- `tests/fixtures/tinystories_fixture.txt` — 4-doc `<|endoftext|>` micro-corpus

## Decisions Made
- None beyond the plan. The memmap sampler and encoder follow 05-PATTERNS.md and the existing `get_batch`/`load_split` idioms verbatim.

## Deviations from Plan

None — plan executed exactly as written. (One cosmetic adjustment within plan intent: the `get_batch_memmap` docstring originally contained the literal tokens `pin_memory`/`non_blocking` while explaining their deliberate absence; the wording was changed to "pinned-host / async-copy transfer flags" so the Task 2 acceptance grep guard `grep -c "pin_memory\|non_blocking"` returns 0. No code/behavior change.)

## Issues Encountered
None.

## TDD Gate Compliance
- RED gate present: `ea1cd5c` (`test(05-01): add RED PRE-01 memmap data tests + fixture`) — failed solely on the missing `get_batch_memmap` import.
- GREEN gate present: `bfe4fb8` (`feat(05-01): add get_batch_memmap sampler`) — all four PRE-01 tests pass.
- REFACTOR gate: not needed (minimal mirror of `get_batch`).

## Verification Evidence
- `python -m pytest tests/test_memmap_data.py -x` → 4 passed.
- `make test` → 99 passed, 1 skipped (MPS smoke), 1 pre-existing tokenizer warning.
- `grep -c "pin_memory\|non_blocking" src/personacore/training/data.py` → 0.
- `python -c "from personacore.training import get_batch_memmap"` → ok.
- `encode_corpus.py` static checks pass (no argparse, `from_json`, `allowed_special`, no `.train()` call); `ruff check` clean.
- Functional smoke of `encode_to_bin` against the fixture → 4 docs → exactly 4 EOS, coherent decoded prefix.

## User Setup Required
**Manual one-time step (Task 3 human-check, NOT automated):** download the two TinyStoriesV2-GPT4 `.txt` files into `data/` (URLs in CLAUDE.md Sources), then run `python scripts/encode_corpus.py`. Confirm it prints a token count in the hundreds-of-millions, an EOS count ≈ document count, a coherent decoded story prefix, and that `data/train.bin` (~1.0–1.1 GB) and `data/val.bin` exist. `data/` is gitignored — no corpus or `.bin` is ever committed.

## Next Phase Readiness
- Plan 02 (the long run) can consume `data/train.bin`/`data/val.bin` via `get_batch_memmap`; the loop memmap branch + best-val/periodic-checkpoint seams and the MPS smoke / resume / best-ckpt tests are Plan 02 scope.
- Blocker carried from phase context: empirical LR/batch/steps and coherence-per-quota are still unmeasured — calibrated during Plan 02.

## Self-Check: PASSED

All created files present (`scripts/encode_corpus.py`, `tests/test_memmap_data.py`, `tests/fixtures/tinystories_fixture.txt`, `src/personacore/training/data.py`); all task commits present (`ea1cd5c`, `bfe4fb8`, `075be1a`).

---
*Phase: 05-tinystories-pretraining*
*Completed: 2026-06-05*
