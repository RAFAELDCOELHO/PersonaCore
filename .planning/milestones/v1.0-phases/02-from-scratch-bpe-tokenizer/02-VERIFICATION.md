---
phase: 02-from-scratch-bpe-tokenizer
verified: 2026-06-04T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
gaps: []
deferred: []
warnings:
  - concern: "Bare `pytest -q` (the exact command CI runs at .github/workflows/ci.yml:21 and `make test`) fails to collect with `ModuleNotFoundError: No module named 'tests'`"
    detail: "tests import `from tests.fixtures.tricky_strings import ...`; repo root is not on sys.path under bare pytest. No `pythonpath = ['.']` in [tool.pytest.ini_options] and no root conftest. Authoritative suite passes ONLY via `.venv/bin/python -m pytest`. Already logged as deferred-items.md D1. Not a Phase-2 success-criterion (QA-01/CI green is owned by Phase 8), but the phase ships test files whose documented invocation is broken — fix before Phase 8 or CI is red."
    severity: warning
  - concern: "WR-04 — committed production artifacts/tokenizer.json claims vocab_size=8192 but contains only 283 merges (max merge id 538), trained on the 11.5KB tests/fixtures/tiny_corpus.txt, not a representative TinyStories corpus"
    detail: "Phase 5 is contracted (D-09) to reuse this exact frozen artifact with no retrain. As shipped, the model would allocate ~7650 dead embedding rows (ids 539-8183 unused). The serialization/freeze/load mechanism is fully correct; the artifact's *content* is a CI-fixture placeholder. See verdict — acceptable as a deferred limitation because no full corpus exists at this phase and scripts/train_tokenizer.py documents the bounded-TinyStories regeneration path, but the artifact MUST be regenerated from the bounded TinyStoriesV2-GPT4 slice before Phase 5 sizes the model."
    severity: warning
---

# Phase 2: From-Scratch BPE Tokenizer Verification Report

**Phase Goal:** A correct, from-scratch byte-level BPE tokenizer whose `vocab_size` is locked before any model is sized, so a later tokenizer change can never invalidate a trained checkpoint.
**Verified:** 2026-06-04
**Status:** passed (with 2 warnings — see below)
**Re-verification:** No — initial verification

## Goal Achievement

The phase goal is achieved. The from-scratch byte-level BPE tokenizer trains deterministically, round-trips exactly with no `<unk>`, keeps special tokens atomic with the shared EOS id in config, freezes/loads as a data-only JSON artifact, and proves algorithm-correctness against the tiktoken `gpt2` oracle with no runtime oracle dependency. `vocab_size=8192` and `eos_id=8184` are locked into `ModelConfig`. All claims were verified by reading the live code and executing the tokenizer directly — not from SUMMARY.md.

Two warnings do not block the phase goal but must be resolved before Phase 5/8 (see Gaps Summary).

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Trains byte-level BPE merges and replays deterministically (lowest-rank-first), identical IDs across runs/sessions | ✓ VERIFIED | Executed two `BPETokenizer().train(corpus, 512)` runs → `t1.merges == t2.merges` True; `encode` identical across instances. `train()` uses total-order tie-break `max(stats, key=lambda p:(stats[p],p))` (bpe.py:107); `_encode_chunk` replays lowest-rank-first via `min(..., key=self.merges.get(p, inf))` (bpe.py:126). Code-review confirmed byte-identical merge tables. |
| 2 | `decode(encode(x)) == x` over tricky strings (emoji, smart quotes, newlines, multi-byte UTF-8), no `<unk>` ever | ✓ VERIFIED | Direct run: round-trip OK for an emoji ZWJ family sequence (U+200D-joined), smart quotes, `\n`/`\r\n`, `café résumé 日本語`, whitespace, embedded EOS literal, and 50 random `os.urandom` bytes. Byte-level base-256 leaves (bpe.py:67) guarantee full coverage → no `<unk>` possible. 54/54 tests pass incl. test_tokenizer_roundtrip.py. |
| 3 | Special tokens atomic with single shared EOS id stored in config — never split or produced by merges | ✓ VERIFIED | Direct run: `encode('a<|endoftext|>b')` → `[97, 8184, 98]` (exactly one EOS id). `encode` splits FIRST on specials longest-first via capturing regex (bpe.py:155-166). `ModelConfig.eos_id == 8184` (config.py:75) and `SPECIAL_TOKENS['<|endoftext|>']==8184` (special.py:18) agree. Specials top-pinned 8184-8191, learned merges 256-538, so merges cannot produce a special id. |
| 4 | Saves/loads as a frozen artifact and exposes a locked `vocab_size` ready to size the model | ✓ VERIFIED (mechanism) / ⚠ artifact content (WR-04) | `io.from_json('artifacts/tokenizer.json')` loads → `vocab_size=8192`, `eos_id=8184`, behaviorally-identical encode/decode confirmed by direct run. `io.py` is stdlib-`json` data-only (no pickle/torch/eval — verified). `ModelConfig.vocab_size==8192` locked (config.py:74). WARNING: the committed artifact holds only 283 merges (CI-fixture-trained); see Gaps Summary / WR-04. The *lock* (vocab_size=8192 in config + artifact) holds regardless. |
| 5 | From-scratch-vs-reference equivalence test passes using tiktoken/HF as test-only oracle (never runtime) | ✓ VERIFIED | `tests/test_tokenizer_oracle.py::test_tiktoken_gpt2_equivalence` PASSED (ran, not skipped — tiktoken present in venv). `test_no_runtime_tiktoken` PASSED. Grep of `src/personacore/**/*.py` for `tiktoken`/`tokenizers`/`huggingface` → CLEAN (no match). `tiktoken~=0.13` is in `[project.optional-dependencies] dev` only (pyproject.toml:28); `regex` is the sole new core dep (pyproject.toml:17). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/personacore/config.py` | vocab_size=8192, eos_id=8184 on ModelConfig | ✓ VERIFIED | Lines 74-75; LOCKED comments cite D-01/D-03/D-03a. |
| `src/personacore/tokenizer/bpe.py` | BPETokenizer train/encode/decode/frozen | ✓ VERIFIED | 209 lines, substantive; class + all 4 methods present and exercised. |
| `src/personacore/tokenizer/patterns.py` | GPT2_SPLIT_PATTERN | ✓ VERIFIED | Exists; imported and used by bpe.py (`_COMPILED`). |
| `src/personacore/tokenizer/special.py` | EOS_ID, SPECIAL_TOKENS (8, top-pinned) | ✓ VERIFIED | 8 specials ids 8184-8191; EOS_ID=8184; imported by bpe.py. |
| `src/personacore/tokenizer/io.py` | save_json/from_json/SCHEMA_VERSION, data-only | ✓ VERIFIED | stdlib json only; SCHEMA_VERSION=1; range-validates merge ids. |
| `src/personacore/tokenizer/__init__.py` | Public surface | ✓ VERIFIED | Exports class + constants + io functions. |
| `scripts/train_tokenizer.py` | Thin no-CLI train→freeze entry | ✓ VERIFIED | `def main()` trains 8192 from fixture, `save_json` to artifacts/. |
| `artifacts/tokenizer.json` | FROZEN production 8192 artifact | ⚠ ORPHANED-CONTENT | Exists, loads, schema_version=1, vocab_size=8192. BUT only 283 merges (WR-04) — CI-fixture-trained, not a real corpus. |
| `tests/test_tokenizer_*.py` (5 files) + fixtures | Red→green TOK suite | ✓ VERIFIED | All present; 54/54 pass via `python -m pytest`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `io.from_json` | `BPETokenizer.frozen` | `frozen(...)` | ✓ WIRED | io.py:66 calls frozen(); load confirmed by direct run. |
| `train_tokenizer.py` | bpe + io | `train()` + `save_json()` | ✓ WIRED | scripts/train_tokenizer.py:39,41. |
| `bpe.py` | `patterns.py` | import GPT2_SPLIT_PATTERN | ✓ WIRED | bpe.py:21. |
| `bpe.py` | `special.py` | split-first on SPECIAL_TOKENS | ✓ WIRED | bpe.py:22, used in encode(). |
| `test_tokenizer_oracle.py` | from-scratch encoder | recover_merges→inject→assert | ✓ WIRED | Test passes; oracle confined to test file. |
| `ModelConfig` | locked vocab_size/eos_id | downstream model sizing | ✓ WIRED | config.py:74-75; consumed by Phase 3/4. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `artifacts/tokenizer.json` | merges table | `BPETokenizer.train(tiny_corpus.txt, 8192)` | Partial — 283 real merges, ids 539-8183 dead | ⚠ STATIC/UNDERFILLED (WR-04) — real merges flow but the table is near-empty behind the 8192 claim because the source corpus is the 11.5KB CI fixture, not TinyStories. |
| `ModelConfig.vocab_size/eos_id` | 8192 / 8184 | hard-locked dataclass defaults | Yes (intentional locked constants) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite green (authoritative) | `.venv/bin/python -m pytest -q` | 54 passed in 4.53s | ✓ PASS |
| tiktoken gpt2 equivalence | `pytest tests/test_tokenizer_oracle.py -v` | 2 passed (equivalence + no-runtime guard) | ✓ PASS |
| No oracle import in runtime src | `grep -rn tiktoken\|tokenizers src/personacore/` | no matches | ✓ PASS |
| Artifact loads + locked vocab | `from_json('artifacts/tokenizer.json')` | vocab_size=8192, eos_id=8184 | ✓ PASS |
| Round-trip tricky strings + random bytes | direct decode(encode(x))==x | all OK incl. emoji/CJK/`\r\n`/urandom | ✓ PASS |
| EOS atomicity | `encode('a<|endoftext|>b')` | `[97, 8184, 98]` (1 EOS) | ✓ PASS |
| Determinism | two trains → compare merges | identical | ✓ PASS |
| CI-style bare pytest | `.venv/bin/pytest -q` | ERROR: ModuleNotFoundError: No module named 'tests' | ✗ FAIL (warning — see Gaps) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TOK-01 | 02-01/02-02 | Byte-level BPE, deterministic lowest-rank replay | ✓ SATISFIED | Truth 1; determinism executed. |
| TOK-02 | 02-01/02-02 | encode/decode round-trip verified | ✓ SATISFIED | Truth 2; tricky-string + random-byte round-trip executed. |
| TOK-03 | 02-01/02-02 | Atomic specials, shared EOS in config | ✓ SATISFIED | Truth 3; EOS count=1, config.eos_id=8184. |
| TOK-04 | 02-03 | Serializable save/load, vocab_size locked | ✓ SATISFIED (artifact content is a warning) | Truth 4; JSON freeze/load works, vocab_size=8192 locked. |
| TOK-05 | 02-03 | tiktoken/HF equivalence, test-only oracle | ✓ SATISFIED | Truth 5; oracle test passes, no runtime import. |

No orphaned requirements: all five TOK IDs are claimed by plans and verified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/personacore/tokenizer/io.py` | 55 | `assert` used for schema-version integrity check (CR-01) | ⚠ Warning | Silently bypassed under `python -O`; documented integrity control. Does not affect committed artifact behavior; from code review. Does not block phase goal. |
| `src/personacore/tokenizer/bpe.py` | 186 | `decode(..., errors="replace")` masks corruption (WR-03) | ℹ Info | Never fires on valid input; happy-path correctness unaffected. |
| `src/personacore/tokenizer/bpe.py` | 104-116 | early-stop sets full vocab_size with few merges (WR-04) | ⚠ Warning | Root cause of underfilled production artifact; see Gaps. |
| (no debt markers) | — | No TBD/FIXME/XXX found in phase files | — | Debt-marker gate clean. |

No unreferenced TBD/FIXME/XXX debt markers in any phase-modified file — debt-marker gate passes.

### Human Verification Required

None. All success criteria are programmatically verifiable and were verified by direct execution. No visual/real-time/external-service behavior in this phase.

### Gaps Summary

No gaps block the phase goal — all 5 ROADMAP success criteria are VERIFIED by direct execution. Two WARNINGS require a human decision before downstream phases:

**WR-04 (production artifact scope) — explicitly addressed per task requirement.**
The committed `artifacts/tokenizer.json` declares `vocab_size=8192` but contains only **283 learned merges** (max merge id 538), because it was trained on the 11.5KB `tests/fixtures/tiny_corpus.txt`, not a representative corpus. The **serialization, freeze/load, locking, and algorithm are all fully correct** — this is purely an artifact-*content* limitation, not an implementation defect. The phase goal ("lock vocab_size so a tokenizer change can never invalidate a checkpoint") is technically met: vocab_size=8192 is locked in both config and artifact. However, the artifact is NOT yet the genuine "production 8192-vocab" tokenizer D-09 promises Phase 5 will reuse — reusing it as-is would give the model ~7650 dead embedding rows.

**Verdict on WR-04:** ACCEPTABLE as a deferred limitation at this phase, NOT a phase-goal failure. Rationale: (1) no full/bounded TinyStories corpus is fetched at Phase 2 by design (D-09 explicitly permits a committed fixture for the bounded sample, and full-corpus work is Phase 5/PRE-01 scope); (2) `scripts/train_tokenizer.py` documents the exact bounded-TinyStoriesV2-GPT4 regeneration path; (3) the locking guarantee (the actual phase goal) holds. **Required action before Phase 5:** regenerate `artifacts/tokenizer.json` from the bounded TinyStoriesV2-GPT4 validation slice so the merge table fills toward 8192 BEFORE any model is sized around it; and/or add the WR-04 warning so an under-trained artifact is never frozen silently.

**CI/test-invocation warning (deferred-items.md D1).**
Bare `pytest -q` — the exact command CI runs (`.github/workflows/ci.yml:21`) and `make test` — fails collection with `ModuleNotFoundError: No module named 'tests'` because the repo root is not on sys.path (no `pythonpath=['.']` in pytest config, no root conftest). The authoritative suite passes only via `.venv/bin/python -m pytest`. This is already logged as deferred and is formally Phase-8 territory (QA-01/CI green), so it does not fail Phase 2's success criteria — but the phase ships a test suite whose documented invocation is red, and CI for this phase would fail. Fix (one line: `[tool.pytest.ini_options] pythonpath=["."]`) recommended before merging/Phase 3.

---

_Verified: 2026-06-04_
_Verifier: Claude (gsd-verifier)_
