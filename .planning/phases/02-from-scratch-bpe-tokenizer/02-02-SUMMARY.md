---
phase: 02-from-scratch-bpe-tokenizer
plan: 02
subsystem: tokenizer
tags: [bpe, tokenizer, regex, byte-level, special-tokens, determinism, from-scratch]

# Dependency graph
requires:
  - phase: 02-from-scratch-bpe-tokenizer
    provides: "Plan 01 locked ModelConfig.vocab_size=8192 / eos_id=8184 and stood up the red TOK-01/02/03 acceptance tests + tricky-string/tiny-corpus fixtures"
  - phase: 01-foundation
    provides: "seed_everything determinism primitive, checkpoint frozen-from-dict convention, CPU-only/offline test discipline, module-docstring header convention"
provides:
  - "src/personacore/tokenizer/ package (D-11): from-scratch byte-level BPE — BPETokenizer.train/encode/decode/_encode_chunk/_split_chunks/frozen"
  - "Deterministic lowest-rank-first merge replay with a TOTAL (freq, pair) tie-break (TOK-01, D-06)"
  - "Byte-level base-256 no-<unk> exact round-trip decode(encode(x))==x (TOK-02, D-04)"
  - "Atomic special tokens split-first, single shared EOS id 8184 (TOK-03, D-03)"
  - "Public import surface: BPETokenizer, GPT2_SPLIT_PATTERN, SPECIAL_TOKENS, EOS_TOKEN, EOS_ID"
affects: [02-03 (io/oracle reuse frozen() + GPT2_SPLIT_PATTERN), 03 (training sizes around vocab_size/eos_id), 04 (GPT decoder vocab embedding), 05 (corpus encode/EOS doc boundaries)]

# Tech tracking
tech-stack:
  added: []
  patterns: [from-scratch BPE train loop with total-order tie-break, lowest-rank encode replay, capturing-split atomic specials, frozen() rebuild-from-dict mirror of load_checkpoint]

key-files:
  created:
    - src/personacore/tokenizer/patterns.py
    - src/personacore/tokenizer/special.py
    - src/personacore/tokenizer/bpe.py
    - src/personacore/tokenizer/__init__.py
  modified: []

key-decisions:
  - "BPETokenizer() is default-constructible (no args) then .train(text, vocab_size) — matches the Plan-01 test contract; merges/vocab populate on train() or frozen()"
  - "Reference-oracle library name kept entirely OUT of the runtime tokenizer source (docstrings/comments reworded) so the Plan-03 no-runtime-oracle string-scan guard stays green (T-02-04)"
  - "decode maps a special id back to its literal marker text, so decode(encode('a<|endoftext|>b'))==the original literal — round-trip holds even for embedded special-token literals"

requirements-completed: [TOK-01, TOK-02, TOK-03]

# Metrics
duration: 4min
completed: 2026-06-04
---

# Phase 2 Plan 02: From-Scratch Byte-Level BPE Core Summary

**Built the new `src/personacore/tokenizer/` package — a hand-rolled byte-level BPE tokenizer that trains deterministic merges (total-order tie-break), replays them lowest-rank-first for exact base-256 no-`<unk>` round-trips, and treats the 8 top-pinned special tokens (EOS=8184) as atomic — turning the red TOK-01/TOK-02/TOK-03 tests from Plan 01 green.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-06-04T19:35:28Z
- **Tasks:** 2
- **Files created:** 4

## Accomplishments

- **`patterns.py`** — `GPT2_SPLIT_PATTERN` (exact minbpe gpt2 string) + module-internal `_COMPILED` regex; cites the `regex`-over-stdlib-`re` rationale (`\p{L}`/`\p{N}`) inline (D-05).
- **`special.py`** — locked top-pinned 8-token registry (ids 8184-8191, EOS=8184), `EOS_TOKEN`, `EOS_ID`, with the id-partition comment (bytes 0-255 / merges 256-8183 / specials 8184-8191) and D-02/D-03a citations.
- **`bpe.py`** — from-scratch `get_stats`/`merge` primitives and `BPETokenizer` with:
  - `train(text, vocab_size=8192)`: pre-tok split → byte-encode → merge loop assigning ids from 256, `num_merges = vocab_size - 256 - len(specials)`, pair = `max(stats, key=lambda p: (stats[p], p))` (TOTAL tie-break, never bare `.get` — Pitfall 1).
  - `_encode_chunk`: lowest-rank-first replay `min(stats, key=lambda p: merges.get(p, inf))`, break when no mergeable pair (D-06).
  - `_split_chunks` / `_encode_ordinary`: lossless pre-tok split, never strip/normalize (Pitfall 6).
  - `encode(text, allowed_special="all")`: capturing-regex split-FIRST on specials (longest-first), atomic special ids, ordinary spans byte-encoded (D-03 / Pitfall 3).
  - `decode`: vocab bytes + inverse-special-map → literal marker, raise on unknown id, UTF-8 decode (D-04).
  - `frozen(...)` classmethod: rebuild a ready tokenizer from a freeze dict, reconstructing `vocab` from `merges` in rank order (mirrors `load_checkpoint`; the constructor Plan 03's `io.from_json` will call).
- **`__init__.py`** — one-line package docstring + `__all__` re-exporting the public surface Phases 3/5/6 import.

## Task Commits

1. **Task 1: Pre-tok pattern + special-token registry** — `c5d6259` (feat)
2. **Task 2: BPETokenizer train/encode/decode/specials + package init** — `f86cd43` (feat)

## Verification

- `pytest tests/test_tokenizer_train.py tests/test_tokenizer_roundtrip.py tests/test_tokenizer_special.py -x` → **28 passed**.
- Full suite excluding the intentionally-RED Plan-03 surface (`--ignore=tests/test_tokenizer_io.py --deselect ...::test_tiktoken_gpt2_equivalence`) → **50 passed**.
- `from personacore.tokenizer import BPETokenizer, GPT2_SPLIT_PATTERN, SPECIAL_TOKENS, EOS_TOKEN, EOS_ID` resolves.
- `make lint` (`ruff check . && ruff format --check .`) → clean on all 26 files.
- No reference-oracle library imported anywhere under `src/personacore/` (`grep -rl` → clean); the Plan-03 `test_no_runtime_tiktoken` guard passes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed the reference-oracle library name from runtime source**
- **Found during:** Task 2 acceptance check (`grep -rl` scan + the Plan-03 `test_no_runtime_tiktoken` guard).
- **Issue:** The initial `bpe.py`/`patterns.py` docstrings and the `# Source:` comment mentioned the oracle library by name. The Plan-01 guard `test_no_runtime_tiktoken` (goes green in Plan 03) asserts the literal string is absent from EVERY file under `src/personacore/` — not just absent as an import — so those mentions would have broken Plan 03's suite.
- **Fix:** Reworded the docstrings to "reference-oracle library" / "no-runtime-oracle guard" and trimmed the `# Source:` comment to cite only minbpe. Meaning preserved; the guard now passes.
- **Files modified:** `src/personacore/tokenizer/bpe.py`, `src/personacore/tokenizer/patterns.py`
- **Verification:** `grep -rl` clean; `test_no_runtime_tiktoken` passes; T-02-04 mitigation honored.
- **Committed in:** `f86cd43`

**2. [Rule 1 - Bug] Removed an unused import + applied ruff import-sort**
- **Found during:** Task 2 lint gate.
- **Issue:** `EOS_TOKEN` was imported into `bpe.py` but unused (F401); ruff also re-sorted the import block (I001).
- **Fix:** Dropped `EOS_TOKEN` from the `bpe.py` import; `ruff check --fix` + `ruff format`.
- **Files modified:** `src/personacore/tokenizer/bpe.py`
- **Verification:** `ruff check .` / `ruff format --check .` clean.
- **Committed in:** `f86cd43`

---

**Total deviations:** 2 auto-fixed (1 blocking guard-compliance reword, 1 lint bug). No scope change — both were required to satisfy the plan's own acceptance criteria and keep the downstream Plan-03 guard green.

## Issues Encountered

`tests/test_tokenizer_io.py` and `tests/test_tokenizer_oracle.py::test_tiktoken_gpt2_equivalence` remain RED **by design** — they depend on `personacore.tokenizer.io` and `BPETokenizer.frozen(mergeable_ranks=...)`, which are explicitly Plan 03 deliverables (TOK-04/TOK-05, noted in this plan's output spec). They are excluded from the in-scope green run above and are the acceptance target for Plan 03.

## Known Stubs

None. No runtime stubs — every method is fully implemented and exercised by the green TOK-01/02/03 tests. `frozen()` is complete and used by the round-trip-capable rebuild path (and will be re-used by Plan 03's `io.from_json`).

## Threat Flags

None. No new security surface beyond the plan's `<threat_model>`. T-02-02 (no merging across `<|endoftext|>`) is mitigated by split-first encoding and asserted by `test_eos_is_atomic`; T-02-04 (no oracle in runtime) is mitigated and guard-verified.

## Next Phase Readiness

- Plan 03 can implement `src/personacore/tokenizer/io.py` (`save_json` / `from_json` / `SCHEMA_VERSION`) against the stable `frozen()` rebuild surface and the locked `merges`/`pattern`/`special_tokens`/`eos_id`/`vocab_size` attributes; `test_tokenizer_io.py` is the acceptance target.
- Plan 03's oracle path needs `frozen(..., mergeable_ranks=...)` + `encode_ordinary` — the current `frozen()` accepts a `merges` dict; the oracle adapter (recover ranks → merges) is Plan 03 scope.
- `GPT2_SPLIT_PATTERN` and the public surface are import-stable for Phases 3/5/6.

---
*Phase: 02-from-scratch-bpe-tokenizer*
*Completed: 2026-06-04*

## Self-Check: PASSED

All 4 created files exist on disk (`patterns.py`, `special.py`, `bpe.py`, `__init__.py`); both commits (`c5d6259`, `f86cd43`) exist in git history; working tree clean; no accidental file deletions.
