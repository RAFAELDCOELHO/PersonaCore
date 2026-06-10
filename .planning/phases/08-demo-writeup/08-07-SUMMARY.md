---
phase: 08-demo-writeup
plan: 07
subsystem: generation
tags: [cr-01, forbid-ids, sampling-mask, demo-01, wr-02, gap-closure]
requires:
  - phase: 08-01
    provides: "load_slim (weights_only=True) + checkpoints/model_slim.pt slim inference artifact"
  - phase: 08-02
    provides: "scripts/demo_app.py launcher + generate_text_cumulative streaming adapter"
provides:
  - "next_token(..., forbid_ids=None) — dead-id logits mask applied before BOTH the greedy argmax and the temperature/top-k/top-p pipeline"
  - "generate(..., forbid_ids=None) passthrough to next_token each step"
  - "undecodable_ids_mask(tokenizer, vocab_size) helper in generation/text.py, exported from personacore.generation"
  - "scripts/demo_app.py builds the mask from the live vocab + specials and threads it into the streaming callback"
  - "tests/test_forbid_ids.py — six CR-01 regression tests pinning mask-or-fail-loudly"
  - "export_slim None-safe val_loss (WR-02)"
affects: [08-verification-rerun, README, REPORT]
tech-stack:
  added: []
  patterns:
    - "Prevention at the logits, never catch-and-truncate: the wrapper keeps catching ONLY UnicodeDecodeError; the unknown-id ValueError propagates loudly"
    - "Mask construction lives in the package (Phase-1 D-04 thin-script rule); the demo wires it once at build time"
key-files:
  created:
    - tests/test_forbid_ids.py
  modified:
    - src/personacore/generation/sampling.py
    - src/personacore/generation/core.py
    - src/personacore/generation/text.py
    - src/personacore/generation/__init__.py
    - scripts/demo_app.py
    - src/personacore/checkpoint.py
    - tests/test_slim_checkpoint.py
key-decisions:
  - "forbid_ids masks logits at the TOP of next_token so both branches (greedy argmax AND sampled pipeline) start from masked logits — a forbidden id has exactly probability zero under torch.multinomial"
  - "undecodable_ids_mask duck-types against .vocab / .special_tokens (the same id test BPETokenizer.decode applies); eos is a registered special so it is never masked and EOS-stop (D-05) is intact"
  - "Do-not-catch contract pinned by test: WITHOUT the mask, generate_text raises ValueError 'unknown token id' — silent truncation would swallow genuine strict-decode defects"
  - "export_slim stores val_loss=None as-is (primitive survives weights_only=True) instead of raising an opaque TypeError (WR-02)"
duration: ~11min
completed: 2026-06-10
---

# Phase 08 Plan 07: CR-01 forbid-ids mask + WR-02 gap closure Summary

**Dead-id logits mask (`forbid_ids`) threaded through `next_token`/`generate` and wired into the demo from the live vocab + specials — the flagship Gradio demo can no longer crash at any in-UI slider setting (measured pre-fix: ~29% per 400-token generation at temp 1.5 / top-k off) — plus None-safe `export_slim` (WR-02).**

## Status

All 3 tasks complete and committed. Full suite 137 passed, 1 skipped (the CUDA fp16 smoke) —
exactly the plan's expected count (pre-gap baseline 130 + 7 new tests). Lint and format clean.

## What Was Built

### Task 1 — forbid_ids through the sampling path + regression tests (`144d287`)

- `sampling.py::next_token` gains keyword-only `forbid_ids=None`; when set,
  `logits_last.masked_fill(forbid_ids, float("-inf"))` runs at the TOP of the function — before
  the greedy branch and before `apply_temperature` — so BOTH branches operate on masked logits.
  `masked_fill` is non-mutating, honoring the module's never-mutate-the-caller convention.
- `core.py::generate` gains keyword-only `forbid_ids=None` and passes `forbid_ids=forbid_ids`
  in the existing explicit `next_token(...)` call.
- `text.py` — NO signature changes (`**gen_kw` already threads); both docstring kwarg
  enumerations now include `forbid_ids`. New module-level `undecodable_ids_mask(tokenizer,
  vocab_size)` returns a `(1, vocab_size)` bool tensor True exactly for ids NOT in
  `set(tokenizer.vocab) | set(tokenizer.special_tokens.values())` — the same id test
  `BPETokenizer.decode` applies at bpe.py:208. Exported from `generation/__init__.py`.
- `tests/test_forbid_ids.py` — six CPU-only, gradio-free tests:
  - `test_next_token_greedy_respects_forbid` — control argmax 7; masked argmax shifts to 3
  - `test_next_token_sampled_never_picks_forbidden` — 50 seeded draws at temp 1.5, mass on the
    forbidden id; never sampled (probability exactly zero)
  - `test_undecodable_ids_mask_shape_and_content` — shape/dtype; True exactly at dead ids 9-14
    (sum 6); False at the eos special 15
  - `test_generate_text_with_mask_streams_clean` — dead id 9 holds the top logit every step;
    with the mask the stream completes clean as `"d" * 5` (argmax shifted to live id 3)
  - `test_generate_text_without_mask_fails_loudly` — `pytest.raises(ValueError, match="unknown
    token id")` — pins the do-not-catch contract (wrapper catches ONLY UnicodeDecodeError)
  - `test_real_artifact_crash_settings_no_crash` — real slim artifact + frozen tokenizer at the
    EXACT measured crash settings (temp 1.5, top-k None, 400 tokens, seeded); mask sums to 7645;
    repo-root-anchored paths (IN-07); skipif-gated for CI

### Task 2 — demo wiring (`cdd7786`)

- `undecodable_ids_mask` added to the existing generation import line (`# noqa: E402`
  discipline preserved; `torch` still not imported by the script).
- `build_demo` constructs `forbid_ids = undecodable_ids_mask(tok, model.config.vocab_size)`
  immediately after the frozen tokenizer loads, with the decision-citing comment (8192-id table
  vs 547 live ids; 7645 dead ids masked; eos 8184 never masked).
- `tell_story` threads `forbid_ids=forbid_ids` into `generate_text_cumulative` — the closure
  captures the mask once at build time.
- Module docstring SECURITY paragraph records the mitigation. UI untouched per 08-UI-SPEC:
  3 sliders with unchanged ranges, no try/except added (prevention at the logits, never
  catch-and-truncate).

### Task 3 — WR-02 None-safe export_slim (`3162b36`)

- `export_slim` reads `val_loss = full.get("val_loss")` and stores
  `float(val_loss) if val_loss is not None else None` — `save_checkpoint`'s own signature
  defaults `val_loss=None`, so the exporter's contract now covers it instead of raising an
  opaque `TypeError`. `None` survives `weights_only=True` (primitive), preserving the slim
  safe-load contract (noted in a comment).
- `test_export_slim_handles_val_loss_none` round-trips a no-val_loss checkpoint through
  `save_checkpoint` → `export_slim` → `load_slim`, asserting `val_loss is None` and
  `schema_version` intact.

## Verification Evidence

- `pytest tests/test_forbid_ids.py -q` → 6 passed (including the real-artifact test on this box)
- `pytest tests/test_generation.py tests/test_generation_text.py tests/test_demo_callback.py -q`
  → passed unchanged (forbid_ids=None back-compat: existing consumers bit-for-bit unaffected)
- `pytest tests/test_slim_checkpoint.py -q` → 5 passed (4 pre-existing + 1 new)
- Full suite → **137 passed, 1 skipped** (expected ~137 per plan; baseline 130 + 7 new)
- `ruff check .` + `ruff format --check .` → clean
- `build_demo()` smoke → prints `ChatInterface`
- 10-seed real-artifact sweep at temperature=1.5 / top_k=None / 400 tokens with the mask →
  **zero exceptions**; mask sum asserts exactly **7645** (pre-fix expectation: ~97% chance at
  least one of 10 crashes)
- Do-not-catch grep: `grep -c "except ValueError" src/personacore/generation/text.py` → 0

## Threat Model Dispositions

- T-08G-01 (DoS, slider extremes → undecodable-id crash): **mitigated** — the forbid_ids mask
  zeroes dead-id probability; pinned by tests/test_forbid_ids.py
- T-08G-03 (DoS, export_slim on val_loss=None): **mitigated** — None-safe conversion, contract
  documented
- T-08G-02 / T-08G-04 / T-08G-SC: accepted per plan (load_slim unchanged; masking only removes
  ids; zero package installs)

## Deviations from Plan

None - plan executed exactly as written.

## Execution Environment Notes

- Worktree scaffolding: `checkpoints/` created locally with `model_slim.pt` symlinked to the
  main checkout's gitignored artifact so the real-artifact verifications could run. Ignored by
  `.gitignore`'s `checkpoints/` pattern; nothing committed.
- Editable install repointed to this worktree (`pip install -e . --no-deps`) per the shared-venv
  protocol; the orchestrator repoints it back after merge.

## Known Stubs

None — the mask is wired end-to-end (real checkpoint, real frozen tokenizer, real generation).

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes beyond the
plan's threat model.

## Self-Check: PASSED

- FOUND: src/personacore/generation/sampling.py (forbid_ids in signature, masked_fill at top)
- FOUND: src/personacore/generation/core.py (forbid_ids passthrough)
- FOUND: src/personacore/generation/text.py (undecodable_ids_mask helper)
- FOUND: src/personacore/generation/__init__.py (exports undecodable_ids_mask)
- FOUND: tests/test_forbid_ids.py (6 tests, all passing)
- FOUND: scripts/demo_app.py (mask built in build_demo, threaded into tell_story)
- FOUND: src/personacore/checkpoint.py (val_loss is not None expression)
- FOUND: tests/test_slim_checkpoint.py (test_export_slim_handles_val_loss_none)
- FOUND: commit 144d287 (Task 1)
- FOUND: commit cdd7786 (Task 2)
- FOUND: commit 3162b36 (Task 3)
- No unexpected file deletions across 4aefc8d..HEAD
