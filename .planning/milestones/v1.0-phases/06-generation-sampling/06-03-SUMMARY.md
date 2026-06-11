---
phase: 06-generation-sampling
plan: 03
subsystem: generation
tags: [generation, text-wrapper, streaming, eos-prepend, running-buffer-delta, dos-cap, tdd]
requires:
  - "personacore.generation.core.generate (06-02 — yields new ids, EOS-stop, context-crop)"
  - "personacore.config.ModelConfig (eos_id on model.config)"
  - "a tokenizer with encode(text)->list[int] + strict decode(ids)->str (tokenizer/bpe.py contract)"
  - "torch (2.7.1)"
provides:
  - "personacore.generation.text: generate_text (streaming str->str wrapper) + generate_text_str (joined convenience)"
  - "personacore.generation barrel now re-exports generate_text, generate_text_str"
  - "tests/test_generation_text.py: five CPU-only stub-tokenizer wrapper tests"
affects:
  - "Phase-8 demo (Gradio ChatInterface calls generate_text for streaming chat — D-01)"
tech-stack:
  added: []
  patterns:
    - "[eos_id]-prepend seed matching the trained document-start register (D-03); empty prompt -> exactly [eos_id]"
    - "Running-buffer delta decode (D-06): accumulate NEW ids only, decode the WHOLE buffer each step, yield text[len(emitted):]"
    - "UnicodeDecodeError on a cumulative buffer ending mid-glyph is buffered (continue), not a crash (Pitfall 3)"
    - "max_new_tokens DoS cap (V5 / T-06-04): ValueError before the loop on > cap or <= 0"
    - "Device resolved from next(model.parameters()).device so generation runs on CPU and MPS"
    - "One impl, two uses: generate_text_str == ''.join(generate_text(...)) (mirrors core.generate/collect)"
key-files:
  created:
    - "src/personacore/generation/text.py"
    - "tests/test_generation_text.py"
  modified:
    - "src/personacore/generation/__init__.py"
decisions:
  - "generate_text is a generator yielding NEW string suffixes; buffer holds NEW ids only so the prompt is stripped from output (D-02) without ever decoding the prompt back out"
  - "A partial multi-byte glyph (cumulative buffer ends mid-byte -> strict decode raises) is HELD and retried next step, not crashed/replaced — the buffer stays cumulative so the suffix delta is correct and the glyph surfaces exactly once (D-06 / Pitfall 3)"
  - "max_new_tokens is a required keyword bounded by max_new_tokens_cap (default 4096); over-cap or <= 0 raises ValueError before any forward (T-06-04 DoS guard)"
  - "eos_id read from model.config.eos_id (never the literal 8184); the frozen tokenizer.json / best.pt are never loaded or modified — tests use a stub tokenizer + tiny GPT"
metrics:
  duration: "~10 min"
  completed: "2026-06-06"
  tasks: 2
---

# Phase 6 Plan 03: Streaming Text Wrapper Summary

`generate_text` is the `str -> str` streaming surface the Phase-8 Gradio demo will call: it
prepends `[eos_id]` to match the trained document-start register (D-03), drives the 06-02
id-space core, decodes the whole running buffer each step, and yields only the new string
suffix (D-06) — so the prompt is stripped (D-02), the raw `<|endoftext|>` separator never
appears (D-05), and multi-byte glyphs split across byte-level-BPE ids stream cleanly without
mojibake or a strict-decode crash. `generate_text_str` joins the stream for non-streaming
callers. `max_new_tokens` is a bounded required kwarg (DoS cap, T-06-04).

## What Was Built

- **`src/personacore/generation/text.py`** — `generate_text(model, tokenizer, prompt, *, eos_id=None, max_new_tokens, max_new_tokens_cap=4096, **gen_kw)` and `generate_text_str(...)`. EOS-prepend seed, running-buffer delta decode with partial-glyph buffering, prompt-strip, EOS DoS cap, device-aware tensor placement (CPU/MPS).
- **`src/personacore/generation/__init__.py`** — barrel re-exports `generate_text` / `generate_text_str` alongside the existing core + sampling exports.
- **`tests/test_generation_text.py`** — five CPU-only wrapper tests on a stub tokenizer + tiny GPT: `test_eos_prepend_seed`, `test_prompt_stripped`, `test_running_buffer_no_mojibake`, `test_no_raw_eos_in_output`, `test_max_new_tokens_cap`.

## Verification

- `pytest tests/test_generation_text.py -x -q` — all five wrapper tests pass.
- Full CPU suite green: **115 passed, 1 skipped** (the CUDA-guarded smoke), 1 pre-existing tokenizer warning (unrelated to this plan).
- `ruff check` + `ruff format --check` clean on all three files.
- `from personacore.generation import generate_text, generate_text_str` succeeds.
- grep confirms `[eid]` prepend + empty-prompt fallback, `tokenizer.decode(buffer_ids)` running-buffer decode (not per-token), the `ValueError` cap guard, and NO literal `8184` / NO `from_json` / NO `tokenizer.json` in `text.py`.

> Tests were run with `PYTHONPATH="$PWD/src"` against the worktree source (the editable
> `.venv` install resolves to the main checkout, not the worktree). Behavior is identical;
> the package layout is unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Strict-decode crash on a cumulative buffer ending mid-glyph**
- **Found during:** Task 2 (`test_running_buffer_no_mojibake` failed RED against the Task 1 implementation).
- **Issue:** The plan's D-06 behavior requires that a multi-byte glyph split across two ids "streams without raising." The first implementation decoded the whole running buffer each step but did not handle the intermediate state where the cumulative buffer ends mid-glyph — the strict UTF-8 decoder (`bpe.py:209`, `errors="strict"`) raised `UnicodeDecodeError`, exactly the Pitfall-3 strict-decode crash the plan warns against.
- **Fix:** Wrapped the per-step `tokenizer.decode(buffer_ids)` in `try/except UnicodeDecodeError`; on a partial-byte failure the wrapper `continue`s (holds the ids, emits nothing) and retries on the next id. The buffer stays cumulative (never reset), so the suffix delta `text[len(emitted):]` remains correct and the glyph surfaces exactly once when its final id arrives.
- **Files modified:** `src/personacore/generation/text.py`
- **Commit:** `3d8eaca` (committed with the Task 2 tests that exercise it)

## TDD Gate Compliance

This `type: tdd` plan structures its two tasks with implementation as Task 1 (whose `<verify>`
requires `text.py` to import) and the test surface as Task 2. Both gate commits exist in order:

1. **GREEN/feat** — `b9dfdbc feat(06-03): add generate_text streaming str->str wrapper over decode core`
2. **test** — `3d8eaca test(06-03): CPU-only wrapper tests + fix strict-decode crash on partial glyph`

The `test` commit followed `feat` per the plan's explicit task ordering (Task 1 = impl, Task 2 =
tests), rather than the canonical RED-before-GREEN order. The Task 2 RED run did surface a real
defect (the partial-glyph crash above), which was fixed and re-verified green — so the tests are
non-vacuous. No REFACTOR commit was needed.

## Self-Check: PASSED

- `src/personacore/generation/text.py` — FOUND
- `tests/test_generation_text.py` — FOUND
- `src/personacore/generation/__init__.py` — FOUND (modified)
- Commit `b9dfdbc` — FOUND
- Commit `3d8eaca` — FOUND
