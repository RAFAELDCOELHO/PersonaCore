---
phase: 02-from-scratch-bpe-tokenizer
plan: 01
subsystem: tokenizer
tags: [bpe, tokenizer, regex, tiktoken, config, pytest, tdd, red-phase]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: ModelConfig dataclass, seed_everything determinism primitive, checkpoint schema-versioned save/load conventions, CPU-only/offline test discipline
provides:
  - "Locked Phase-2 deliverable: ModelConfig.vocab_size == 8192 (D-01) + ModelConfig.eos_id == 8184 (D-03)"
  - "regex declared as a core runtime dependency (GPT-2 pre-tok engine); tiktoken declared [dev]-only (TOK-05 oracle)"
  - "Wave 0 test scaffolding: tricky-string round-trip corpus + tiny offline training corpus"
  - "Five red TOK test files (TOK-01..TOK-05) defining the encode/decode/freeze/oracle acceptance contract before any tokenizer code exists"
affects: [02-02 (tokenizer train/encode/decode/special), 02-03 (tokenizer io/oracle/artifact), 03 (training loop sizes around vocab_size), 04 (GPT decoder vocab embedding)]

# Tech tracking
tech-stack:
  added: [regex~=2026.5 (core), tiktoken~=0.13 (dev-only oracle)]
  patterns: [RED-of-TDD wave-0 test scaffolding, locked-deliverable config constant with decision-id comment, dev-only oracle with no-runtime-import guard]

key-files:
  created:
    - tests/fixtures/__init__.py
    - tests/fixtures/tricky_strings.py
    - tests/fixtures/tiny_corpus.txt
    - tests/test_tokenizer_train.py
    - tests/test_tokenizer_roundtrip.py
    - tests/test_tokenizer_special.py
    - tests/test_tokenizer_io.py
    - tests/test_tokenizer_oracle.py
  modified:
    - src/personacore/config.py
    - tests/test_config.py
    - pyproject.toml
    - requirements.txt

key-decisions:
  - "vocab_size=8192 and eos_id=8184 are locked in ModelConfig and never move — Phases 3-4 size around them (D-01/D-03)"
  - "regex is a core runtime dependency framed as a pre-tok primitive (not a from-scratch BPE violation); tiktoken is dev-only and guarded against runtime import (T-02-01)"
  - "Tokenizer tests are intentionally RED at wave 0; they go green in Plans 02 (train/roundtrip/special) and 03 (io/oracle)"

patterns-established:
  - "Wave-0 RED scaffolding: tests import the not-yet-existent package surface so downstream plans implement against a fixed, failing acceptance target"
  - "Locked-deliverable config value carries an inline decision-id comment (mirrors Phase-1 config convention)"
  - "Dev-only oracle dependency paired with a no-runtime-import guard test that scans src/personacore/**/*.py"

requirements-completed: [TOK-01, TOK-02, TOK-03, TOK-04, TOK-05]

# Metrics
duration: 8min
completed: 2026-06-04
---

# Phase 2 Plan 01: Lock vocab + Wave-0 Tokenizer Test Scaffolding Summary

**Locked the load-bearing Phase-2 deliverable (vocab_size=8192, eos_id=8184) into ModelConfig, declared regex (core) + tiktoken (dev-only) dependencies, and stood up the complete red TOK test surface (fixtures + five test files) so Plans 02/03 implement against a fixed, failing acceptance contract.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-04T19:23:07Z
- **Completed:** 2026-06-04T19:31:02Z
- **Tasks:** 3
- **Files modified:** 12 (4 modified, 8 created)

## Accomplishments
- `ModelConfig.vocab_size` locked at 8192 (was the Phase-1 50304 placeholder) and new `ModelConfig.eos_id = 8184` shared atomic EOS id; `test_config.py` asserts both and passes.
- `regex~=2026.5` declared as a core runtime dependency in both `pyproject.toml` and `requirements.txt`; `tiktoken~=0.13` declared in the `[dev]` extra only (never a core dep — tomllib guard confirms).
- Wave-0 fixtures created: `tricky_strings.py` round-trip stress corpus (smart punctuation, ZWJ/flag emoji, multi-byte scripts, embedded `<|endoftext|>`, empty/single-byte edges) + an 11.5KB offline TinyStories-style `tiny_corpus.txt` with 11 EOS separators and non-ASCII.
- All five `test_tokenizer_*.py` files written RED against the future `personacore.tokenizer` / `personacore.tokenizer.io` surface, encoding the TOK-01..TOK-05 acceptance contract (determinism, round-trip + chunk-join, atomic EOS, freeze/load + schema, tiktoken-gpt2 oracle with skip-offline + no-runtime-tiktoken guard).

## Task Commits

Each task was committed atomically:

1. **Task 1: Lock vocab_size + eos_id in config (TDD)** - `3f08d1b` (feat)
2. **Task 2: Declare regex (core) + tiktoken ([dev]) deps** - `877db8c` (chore)
3. **Task 3: Wave 0 fixtures + five red TOK test files** - `7ba75fc` (test)

_Note: Task 1 is TDD-style but config + assertion landed in a single feat commit (the assertion target was an existing test edited in place rather than a new failing file)._

## Files Created/Modified
- `src/personacore/config.py` - Locked `vocab_size=8192`, added `eos_id=8184`, updated docstring/comments (D-01/D-03).
- `tests/test_config.py` - Added `test_vocab_size_and_eos_locked` asserting both locked values.
- `pyproject.toml` - Added `regex~=2026.5` to core deps; `tiktoken~=0.13` to `[dev]` extra.
- `requirements.txt` - Added `regex~=2026.5` (core); commented `tiktoken~=0.13` in dev-tooling block.
- `tests/fixtures/__init__.py` - Package marker so `tests.fixtures.*` imports resolve.
- `tests/fixtures/tricky_strings.py` - `TRICKY_STRINGS` round-trip corpus (TOK-02).
- `tests/fixtures/tiny_corpus.txt` - 11.5KB offline training corpus (TOK-01), 11 EOS separators, non-ASCII.
- `tests/test_tokenizer_train.py` - Determinism / lowest-rank replay (TOK-01).
- `tests/test_tokenizer_roundtrip.py` - `decode(encode(x))==x` over tricky strings + chunk-join invariant (TOK-02).
- `tests/test_tokenizer_special.py` - Atomic EOS + config `eos_id`/`vocab_size` (TOK-03).
- `tests/test_tokenizer_io.py` - Freeze/load + schema version + locked vocab (TOK-04).
- `tests/test_tokenizer_oracle.py` - tiktoken-gpt2 equivalence (skip-offline) + no-runtime-tiktoken guard (TOK-05).

## Decisions Made
- None beyond the plan: followed the plan's locked values, dependency placement, and RED-scaffolding intent exactly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created the missing Python 3.11 virtual environment**
- **Found during:** Pre-execution setup (the plan's verify commands invoke `.venv/bin/python`, which did not exist)
- **Issue:** No `.venv` existed; the local default interpreter is Python 3.14, which is not a supported target (CLAUDE.md mandates a 3.11 venv). Verification commands could not run.
- **Fix:** `python3.11 -m venv .venv` and `pip install -e ".[cpu,dev]" --extra-index-url .../cpu`; later re-ran the install after Task 2 to pick up the new `regex`/`tiktoken` deps. Both pinned deps installed cleanly (regex 2026.5.9, tiktoken 0.13.0).
- **Files modified:** None tracked (`.venv/` is gitignored; 0 tracked venv files).
- **Verification:** Baseline suite green (20 passed) before edits; torch 2.7.1 / numpy 2.4.6 confirmed.
- **Committed in:** N/A (environment only, not part of repo)

**2. [Rule 1 - Bug] Removed the literal "50304" from the config comment**
- **Found during:** Task 1 acceptance check
- **Issue:** The acceptance criterion `grep -c "50304" == 0` failed because the new inline comment read "was 50304 placeholder".
- **Fix:** Reworded the comment to "was the Phase-1 placeholder" so the literal number is fully removed.
- **Files modified:** `src/personacore/config.py`
- **Verification:** `grep -c "50304"` returns 0; `test_config.py` still green.
- **Committed in:** `3f08d1b` (Task 1 commit)

**3. [Rule 1 - Bug] Shortened the eos_id comment to satisfy ruff E501**
- **Found during:** Task 1 lint gate
- **Issue:** The `eos_id` inline comment exceeded the 100-char line-length limit (E501).
- **Fix:** Trimmed the comment to "...top-pinned (D-03a)." keeping the decision-id citations.
- **Files modified:** `src/personacore/config.py`
- **Verification:** `ruff check` / `ruff format --check` clean.
- **Committed in:** `3f08d1b` (Task 1 commit)

**4. [Rule 1 - Bug] Applied ruff import-sort autofix to the new test files**
- **Found during:** Task 3 lint gate
- **Issue:** Ruff (I001) reordered imports because `personacore.tokenizer` is currently classified third-party (the package does not exist yet), splitting it from `personacore.config`/`seeding`.
- **Fix:** `ruff check --fix` + `ruff format`. The grouping is cosmetic and self-corrects once the tokenizer package lands in Plan 02.
- **Files modified:** `tests/test_tokenizer_{train,roundtrip,special,io}.py`
- **Verification:** `ruff check .` / `ruff format --check .` clean; RED state preserved.
- **Committed in:** `7ba75fc` (Task 3 commit)

---

**Total deviations:** 4 auto-fixed (1 blocking env setup, 3 bugs — all comment/lint corrections to meet acceptance + lint gates)
**Impact on plan:** No scope change. All fixes were necessary to pass the plan's own acceptance criteria and the `make lint` gate. The locked values, dependency layout, and RED-scaffolding intent are exactly as planned.

## Issues Encountered
None beyond the deviations above. The five tokenizer test files are RED **by design** (Wave 0): they collect with `ModuleNotFoundError: No module named 'personacore.tokenizer'`. This is the intended state and will go green in Plan 02 (train/roundtrip/special) and Plan 03 (io/oracle). The non-tokenizer suite is fully green (21 passed when the tokenizer files are excluded; 6 in `test_config.py`).

## Known Stubs
None. No runtime stubs were introduced — the only "incomplete" surface is the intentionally-RED tokenizer test suite, which is the explicit Wave-0 deliverable (tests precede implementation), documented above and in the plan output spec.

## User Setup Required
None - no external service configuration required. (A local Python 3.11 `.venv` is required to run the suite, per CLAUDE.md; it was created during execution.)

## Next Phase Readiness
- Plan 02 can implement `src/personacore/tokenizer/` (`bpe.py`, `patterns.py`, `special.py`, `__init__.py`) against the fixed `train`/`encode`/`decode`/`frozen`/`vocab_size`/`eos_id` surface; `test_tokenizer_train`, `test_tokenizer_roundtrip`, and `test_tokenizer_special` are the acceptance target.
- Plan 03 can implement `src/personacore/tokenizer/io.py` (`save_json`/`from_json`/`SCHEMA_VERSION`) + the `frozen`/`mergeable_ranks`/`encode_ordinary` oracle surface; `test_tokenizer_io` and `test_tokenizer_oracle` are the acceptance target.
- `regex` and `tiktoken` are installed and import-verified; the no-runtime-tiktoken guard will keep tiktoken out of the runtime package.

---
*Phase: 02-from-scratch-bpe-tokenizer*
*Completed: 2026-06-04*

## Self-Check: PASSED

All 13 created/modified files exist on disk; all 4 commits (`3f08d1b`, `877db8c`, `7ba75fc`, `7ebcb83`) exist in git history.
