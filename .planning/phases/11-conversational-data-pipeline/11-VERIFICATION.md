---
phase: 11-conversational-data-pipeline
verified: 2026-07-31T21:05:00Z
status: passed
score: 16/16 must-haves verified
overrides_applied: 0
---

# Phase 11: Conversational Data Pipeline Verification Report

**Phase Goal:** PersonaChat (self_revised) becomes role-token-formatted, loss-masked memmap training bins through the frozen tokenizer — with the tokenizer-inflation tax measured before the format design hardens (DailyDialog cut per D-00, 2026-07-31)
**Verified:** 2026-07-31T21:05:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| SC1 | PersonaChat downloads via pinned-checksum direct fetch and parses from scratch — no HF `datasets`, no network at train time | ✓ VERIFIED | `data/raw/personachat.tgz` on disk; `shasum -a 256` independently recomputed = `507cf864…d5622` (matches pinned constant at `scripts/fetch_personachat.py:31`); both extracted txt files present (75.5 MB / 9.2 MB); `parse.py` is stdlib-only; fetch uses `urllib`/`hashlib`/`tarfile`, `tf.extract` per named member, no `extractall`; bins are local memmaps (no train-time network) |
| SC2 | Tokenizer-inflation measurement produced and documented as a go/no-go gate BEFORE the format design is committed | ✓ VERIFIED | `results/inflation_report.md` git-tracked with all four D-08 metrics + auditable denominators + relative D-09 bands + TinyStories baseline (2.860, same run) + ratio 1.129x; verdict commit `89abe8d` predates bin-build commit `55c695e` in git history; `prepare_dialog_corpus.py` enforces the gate in code (SystemExit on missing/PENDING/STOP Verdict, lines 62-80) |
| SC3 | Dialogues serialize with role tokens 8185-8187 through the frozen tokenizer into uint16 memmap bins, eos 8184 as document separator only | ✓ VERIFIED | Independent numpy scan of real bins: train max id 8187, eos count 8,939 == episode count; val eos 1,000 == episode count; every sampled episode opens with 8187; token bin bytes = 2× mask bin bytes (uint16/uint8); role ids sourced from `SPECIAL_TOKENS` registry, never retyped |
| SC4 | User-turn loss masking via `ignore_index=-100` (parallel mask bins) matches a hand-built fixture exactly in a turn-boundary unit test | ✓ VERIFIED | `tests/test_masked_batch.py`: `EXPECTED_Y` hand-written literal (line 41) with 7× -100, asserted via `torch.equal`; three Pitfall-14 edge tokens pinned individually; 3 tests pass; live draw from real bins produced `(4,256)` y containing -100 |

### Plan-Level Truths (merged, deduplicated against SCs)

| # | Truth (plan) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | 11-01: parse_episodes flushes the last episode with no trailing boundary | ✓ VERIFIED | `parse.py:38-39` flush-at-EOF; `test_dialogue_parse.py` passes (episode count 3 on fixture) |
| 2 | 11-01: encode_dialogue equal-length id/mask with D-01 semantics (first `<\|user\|>`=0, subsequent=1, assistant content=1, eos=1) | ✓ VERIFIED | `serialize.py:69-81`; test asserts mask at all three edge positions (`test_dialogue_serialize.py:139-141,127`); independently re-verified on 50 real train-bin episodes (all D-01 invariants hold) |
| 3 | 11-01: role tokens 8185-8187 atomic round-trip through frozen tokenizer | ✓ VERIFIED | Tests load `from_json("artifacts/tokenizer.json")` (`test_dialogue_serialize.py:26,47`); atomicity tests pass |
| 4 | 11-01: detokenizer rejoins contractions, closes spaced punctuation, normalizes `!.` | ✓ VERIFIED | `serialize.py:22-38` (`_NT_RE`, `_APOS_RE`, `_PUNCT_RE`, `!.` → `!`); tests pass |
| 5 | 11-02: get_batch_memmap_masked draws aligned windows, y=-100 where shifted mask is 0 | ✓ VERIFIED | `training/data.py:93-126`; smoke draw on real bins executed during verification |
| 6 | 11-02: +1 shift applied identically to token and mask slices (target-space, D-01) | ✓ VERIFIED | y and m share the `i+1 : i+1+block_size` slice (`data.py:120-124`) |
| 7 | 11-02: existing get_batch_memmap and v1.0 suite untouched and green | ✓ VERIFIED | `get_batch_memmap` intact directly above; full suite 250 passed / 1 skipped via `.venv/bin/python -m pytest -q` |
| 8 | 11-03: sha256 verified BEFORE extraction; only two named members extracted | ✓ VERIFIED | Checksum gate at `fetch_personachat.py:70-73` precedes `tarfile.open` (line 86); `tf.extract(tf.getmember(member))` per member (line 89); no `extractall` anywhere |
| 9 | 11-03: GO/ADAPT/STOP verdict obtained at blocking checkpoint BEFORE any bin built, recorded in report | ✓ VERIFIED | `## Verdict` = **GO** (user, 2026-07-31) with D-07 cap 140 + date; commit `89abe8d` (verdict) < `55c695e` (bins) |
| 10 | 11-03: D-05 endpoint substitution (S3 revised JSON 404 → ParlAI tarball) recorded | ✓ VERIFIED | `fetch_personachat.py:8-11` docstring + 11-03-SUMMARY.md |
| 11 | 11-04: both aligned bins ship (uint16 + uint8, 1:1 per split, gitignored) | ✓ VERIFIED | Independent scan: train 5,257,858 == mask length; val 637,633 == mask length; mask values ⊆ {0,1}; `git status --porcelain` shows nothing under `data/` |
| 12 | 11-04: eos 8184 exactly once per dialogue — count equals episode count per split | ✓ VERIFIED | Independently counted: 8,939 (train) / 1,000 (val), matching pinned research episode counts |
| 13 | 11-04: bins built only after recorded verdict, D-07 140-token line-granular cap applied | ✓ VERIFIED | Verdict gate in code + git ordering; independent scan of ALL 8,939 train episodes: max persona span (8187 → first 8185) = 140 ≤ 140 cap |
| 14 | 11-04: masked batch from real bins contains -100 sentinels (end-to-end smoke) | ✓ VERIFIED | Executed live: `get_batch_memmap_masked` on `data/dialog_train*.bin` → `(4,256)` int64, y contains -100, all x < 8192 |

**Score:** 16/16 truths verified (4 roadmap SCs + 12 distinct plan truths)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/personacore/dialogue/parse.py` | fb-dialog parser, stdlib only | ✓ VERIFIED | 40 lines, `parse_episodes`, zero non-stdlib imports |
| `src/personacore/dialogue/serialize.py` | detokenize + render_document + encode_dialogue | ✓ VERIFIED | 81 lines, all three exports, imports `SPECIAL_TOKENS`/`EOS_ID` from registry |
| `src/personacore/dialogue/inflation.py` | four D-08 metrics, one encode pass | ✓ VERIFIED | 98 lines, `compute_inflation_metrics`, imports `encode_dialogue`/`detokenize` from `.serialize` |
| `src/personacore/dialogue/__init__.py` | public surface | ✓ VERIFIED | exports all 5 functions, sorted `__all__` |
| `src/personacore/training/data.py` | additive `get_batch_memmap_masked` | ✓ VERIFIED | contains `def get_batch_memmap_masked` + `y[m == 0] = -100`; `get_batch_memmap` untouched |
| `tests/fixtures/personachat_fb_fixture.txt` | synthetic format-faithful fixture | ✓ VERIFIED | 3 episodes, `your persona: ` lines, one `!.` artifact, zero apostrophes, synthetic content (D-00) |
| `tests/test_dialogue_parse.py` / `test_dialogue_serialize.py` / `test_masked_batch.py` | phase test suite | ✓ VERIFIED | 28 tests, all pass in 0.89s |
| `scripts/fetch_personachat.py` | checksum-gated fetch | ✓ VERIFIED | contains pinned sha256 literal, `tf.extract`, no `extractall`, no `requests`/HF imports |
| `scripts/measure_inflation.py` | thin gate driver | ✓ VERIFIED | precondition `FileNotFoundError` names `scripts/fetch_personachat.py` (lines 65-66) |
| `scripts/prepare_dialog_corpus.py` | verdict-gated bin builder | ✓ VERIFIED | verdict SystemExit gate, `encode_dialogue` sole tokenization path (only direct `tok.encode` is D-07 budget accounting), sanity block, smoke draw |
| `results/inflation_report.md` | committed evidence: metrics + bands + verdict + build | ✓ VERIFIED | git-tracked; contains "tokens/word", GO/ADAPT/STOP bands, baseline, `## Verdict` (GO), `## Corpus Build` |
| `data/dialog_{train,val}{,_mask}.bin` | gitignored bins | ✓ VERIFIED | all four present, byte-math consistent with claimed token counts |
| `data/raw/personachat.tgz` + extracted txts | checksum-verified cache | ✓ VERIFIED | sha256 independently recomputed and matched |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| serialize.py | tokenizer/special.py | `from personacore.tokenizer.special import` | ✓ WIRED | line 14; no retyped role-id literals in encode path |
| test_dialogue_serialize.py | artifacts/tokenizer.json | `from_json` | ✓ WIRED | lines 26, 47 |
| training/data.py | F.cross_entropy ignore_index | `-100` sentinel | ✓ WIRED | `y[m == 0] = -100`; forward() untouched |
| test_masked_batch.py | data.py | tmp_path uint16/uint8 bins | ✓ WIRED | hand-built fixture, tests pass |
| measure_inflation.py | serialize.py | `encode_dialogue` (via inflation.py) | ✓ WIRED | single tokenization path (Pitfall 4) |
| fetch_personachat.py | data/raw/ | gitignored cache | ✓ WIRED | DEST_DIR = data/raw; nothing under data/ tracked |
| prepare_dialog_corpus.py | serialize.py | same `encode_dialogue` the gate measured | ✓ WIRED | line 32 import, line 123 call |
| prepare_dialog_corpus.py | training/data.py | post-build smoke via `get_batch_memmap_masked` | ✓ WIRED | line 34 import, line 161 call |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| dialog bins | token/mask arrays | checksum-verified corpus → parse_episodes → encode_dialogue | Yes — independently re-read with np.fromfile; eos/episode counts, mask fractions (0.4292/0.4238), max id, alignment all reproduce claims | ✓ FLOWING |
| inflation_report.md | metric table | measure_inflation.py full-corpus run | Yes — numbers consistent across report, SUMMARY, and bin byte-math | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase test files pass | `.venv/bin/python -m pytest tests/test_dialogue_{parse,serialize}.py tests/test_masked_batch.py -q` | 28 passed | ✓ PASS |
| Full suite regression | `.venv/bin/python -m pytest -q` | 250 passed, 1 skipped | ✓ PASS |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | All checks passed; 106 files formatted | ✓ PASS |
| eos == episodes (independent count) | numpy scan of real bins | 8,939 / 1,000 exact | ✓ PASS |
| D-01 semantics on real data | numpy scan, 50 train episodes | first-user 0 / subsequent-user 1 / assistant content 1 / eos 1 — all hold | ✓ PASS |
| D-07 cap on ALL train episodes | numpy scan, 8,939 episodes | max persona span = 140 ≤ 140 | ✓ PASS |
| Masked draw end-to-end | `get_batch_memmap_masked` on real bins | (4,256) int64, y has -100, x < 8192 | ✓ PASS |
| Tarball integrity | `shasum -a 256 data/raw/personachat.tgz` | matches pinned digest | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| DATA-01 | 11-01, 11-03 | Pinned-checksum direct fetch + from-scratch parse, no HF datasets | ✓ SATISFIED | fetch script + verified tarball + stdlib parser + tests |
| DATA-02 | 11-01, 11-04 | Role-token serialization through frozen tokenizer into uint16 bins | ✓ SATISFIED | serialize.py + real bins with role ids 8185-8187, eos separator proven |
| DATA-03 | 11-02, 11-04 | Loss masking via ignore_index=-100, hand-built fixture test | ✓ SATISFIED | get_batch_memmap_masked + EXPECTED_Y exactness fixture + mask bins |
| DATA-04 | 11-03 | Inflation measurement documented as gate before format hardens | ✓ SATISFIED | committed report, verdict commit predates bin commit |

No orphaned requirements: REQUIREMENTS.md maps exactly DATA-01..04 to Phase 11; all four are claimed and satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| (none in phase files) | — | No TBD/FIXME/XXX/TODO/placeholder/stub patterns in any phase-modified file | — | — |
| Makefile (uncommitted working-tree edit) | 16-18 | Duplicate `format:` target referencing `isort` (not a declared dep) — NOT part of any Phase 11 plan | ℹ️ Info | Outside phase scope; `make format` will emit an override warning. Suggest reverting or consolidating before commit. |
| Environment (not code) | — | Bare `make test`/`make lint` resolve to stale pyenv shims (ruff 0.1.15, torch-less pytest) when the venv is not activated; `.venv/bin/*` equivalents are fully green | ℹ️ Info | Matches the known worktree/venv memory note. Not a phase regression. |

### Human Verification Required

None. The phase's single human gate (D-09 GO/ADAPT/STOP verdict) was already exercised at the 11-03 blocking checkpoint and is recorded in `results/inflation_report.md` `## Verdict` (GO, user, 2026-07-31, commit 89abe8d). No visual/UI/real-time behavior in scope; all remaining behaviors were verified by executed commands.

### Gaps Summary

No gaps. Every SUMMARY claim checked reproduced independently: bin byte-math, eos-per-episode counts, mask fractions, D-01 edge-token semantics on real data, the D-07 cap across all 8,939 train episodes, the tarball checksum, and the gate-before-bins git ordering. The phase goal — role-token-formatted, loss-masked memmap bins through the frozen tokenizer, with the inflation tax measured and verdict recorded before format hardening — is achieved in the codebase, not just the narrative.

---

_Verified: 2026-07-31T21:05:00Z_
_Verifier: Claude (gsd-verifier)_
