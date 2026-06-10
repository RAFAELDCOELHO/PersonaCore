---
phase: 08-demo-writeup
plan: 02
subsystem: demo
tags: [gradio, streaming, offline, demo-01, chat-interface]
requires:
  - phase: 08-01
    provides: "load_slim (weights_only=True) + checkpoints/model_slim.pt slim inference artifact"
  - phase: 06-03
    provides: "generate_text delta-streaming wrapper (the producer the adapter wraps)"
provides:
  - "generate_text_cumulative — Gradio-shaped (cumulative) adapter over the delta-streaming generate_text, exported from personacore.generation"
  - "scripts/demo_app.py — offline Gradio 5.50.0 story-completion demo launcher (DEMO-01)"
  - "tests/test_demo_callback.py — CPU-only, gradio-free unit tests for the cumulative-yield contract"
affects: [08-04, 08-05, 08-06]
tech-stack:
  added: ["gradio 5.50.0 (demo extra, runtime-only — not a test/CI dependency)"]
  patterns:
    - "Cumulative-yield adapter in the package, thin script wires it (Phase-1 D-04)"
    - "Env kill-switch BEFORE the import it affects, late imports # noqa: E402"
key-files:
  created:
    - tests/test_demo_callback.py
    - scripts/demo_app.py
  modified:
    - src/personacore/generation/text.py
    - src/personacore/generation/__init__.py
key-decisions:
  - "Adapter lives in src/personacore (not the script) so CI tests the streaming contract without gradio installed"
  - "Examples passed as list-of-lists — gradio 5.50.0 hard-requires this shape when additional_inputs are present"
  - "CPU pinned via RuntimeConfig(device=\"cpu\") — DEMO-01 says laptop CPU; device resolution never drifts to MPS"
duration: ~12min (through Task 2; Task 3 checkpoint pending)
completed: IN PROGRESS — awaiting Task 3 human verification (offline streaming smoke)
---

# Phase 08 Plan 02: Offline Gradio Demo (DEMO-01) Summary — IN PROGRESS

**Cumulative-yield streaming adapter (TDD, gradio-free tests) + offline Gradio 5.50.0 story-completion launcher loading the slim weights_only=True checkpoint on pinned CPU — awaiting the human Wi-Fi-off streaming smoke (Task 3 checkpoint).**

## Status

Tasks 1-2 of 3 complete and committed. Task 3 is a blocking `checkpoint:human-verify`
(offline streaming smoke) — execution paused awaiting the developer's live verification.

## What Was Built

### Task 1 — `generate_text_cumulative` (TDD)

- **RED** (`19f181a`): `tests/test_demo_callback.py` — four CPU-only tests importing nothing
  from gradio or `scripts/`, reusing the exact `tests/test_generation_text.py` fixture
  approach (`_tiny_model` / `_force_sequence` / `_RecordingTokenizer`):
  - `test_yields_are_cumulative` — monotone growth, non-decreasing lengths, ≥1 strict increase
  - `test_final_yield_equals_collected_deltas` — last yield == `"".join(generate_text(...))`
  - `test_kwargs_thread_through` — keyword-only `max_new_tokens` (positional → TypeError);
    the (0, 4096] guard fires through the adapter (T-06-04); temperature/top_k/generator thread
  - `test_no_eos_literal_in_output` — no raw `<|endoftext|>` in the final yield (Phase-6 D-05)
- **GREEN** (`446e16a`): `generate_text_cumulative(model, tokenizer, prompt, *, max_new_tokens,
  **gen_kw)` added to `src/personacore/generation/text.py` — ADDITIVE only (0 removed lines
  verified by diff); accumulates deltas and yields the running string per the Gradio
  ChatInterface contract (08-RESEARCH Pitfall 1). Exported from `generation/__init__.py`.
  Docstring states why the two yield shapes differ (delta = composable producer, cumulative =
  Gradio display contract).

### Task 2 — `scripts/demo_app.py` (`0609f50`)

Thin wiring per Phase-1 D-04 (121 lines, no argparse):

- `os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"` at line 33, `import gradio` at line 35 —
  the kill-switch precedes the import (Pitfall 5); late imports carry `# noqa: E402`
- `build_demo()` is lazy (no module-level model load): missing `SLIM_PATH` raises
  `FileNotFoundError` with the exact UI-SPEC message; `load_slim(SLIM_PATH)` is the
  `weights_only=True` choke point (T-08-01); `ModelConfig(**ckpt["model_config"])` → `GPT` →
  `load_state_dict` → `.eval()`; CPU pinned via `RuntimeConfig(device="cpu")`; tokenizer via
  `from_json(TOKENIZER_PATH)` (frozen, data-only)
- `tell_story` callback IGNORES history (fresh story per message — D-02 honest framing),
  maps top-k slider 0 → None, yields from `generate_text_cumulative`
- UI-SPEC copy verbatim: locked title/description/placeholder, three example openings,
  sliders Temperature 0.1–1.5/0.8/0.05, "Top-k (0 = disabled)" 0–200/50/1,
  "Max new tokens" 16–1024/400/16 (under the 4096 DoS cap)
- `share=False` localhost; `type="messages"`; `analytics_enabled=False`; zero look-and-feel
  customization (the default configuration is the only offline-verified one — UI-SPEC hard rule)
- Verified: importlib construction of `build_demo()` against the real slim artifact prints
  `ChatInterface` without launching; all forbidden patterns grep-asserted absent
  (`theme=`, `css=`, `gr.themes`, `argparse`, `weights_only=False`)

## Verification Evidence

- `pytest tests/test_demo_callback.py tests/test_generation_text.py -q` → 9 passed
- Full suite → **130 passed, 1 skipped** (no regressions)
- `ruff check .` + `ruff format --check .` → clean
- RED phase confirmed failing before GREEN (ImportError on `generate_text_cumulative`)

## TDD Gate Compliance

- RED gate: `test(08-02)` commit `19f181a` (tests failed: ImportError as expected)
- GREEN gate: `feat(08-02)` commit `446e16a` (4 new tests pass)
- REFACTOR: not needed (no commit)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Examples shape for gradio 5.50.0 with additional_inputs**
- **Found during:** Task 2 verification (build_demo construction)
- **Issue:** `gr.ChatInterface` raises `ValueError: Examples must be a list of lists when
  additional inputs are provided` — the plan specified the three openings as flat strings
- **Fix:** `EXAMPLES` is a list of single-element lists `[[msg], ...]`; slider values fall
  back to their defaults on example click. UI-SPEC copy unchanged.
- **Files modified:** scripts/demo_app.py
- **Commit:** 0609f50

## Execution Environment Notes

- Worktree scaffolding: `checkpoints` symlinked to the main checkout
  (`/Users/juliorcoelho/PersonaCore/checkpoints`) so Task 2's verify could load the real
  gitignored `model_slim.pt`. The symlink is untracked and ephemeral (`.gitignore`'s
  `checkpoints/` pattern matches the directory it resolves to; nothing was committed).
- Tests ran via the shared 3.11 venv with `PYTHONPATH=<worktree>/src` (no `pip install -e .`
  from the worktree — preserves the main checkout's editable install).

## Known Stubs

None — the demo is fully wired end-to-end (real checkpoint, real tokenizer, real generation).

## Pending: Task 3 checkpoint (human-verify, blocking)

Awaiting developer confirmation of the offline streaming smoke: streams with Wi-Fi off,
bubble grows cumulatively, sliders change behavior, fresh story per message, no EOS literal.
Resume signal: "approved" (or a failure description → fix and re-present).

## Self-Check: PASSED

- FOUND: src/personacore/generation/text.py (`def generate_text_cumulative`)
- FOUND: src/personacore/generation/__init__.py (exports generate_text_cumulative)
- FOUND: tests/test_demo_callback.py (`def test_yields_are_cumulative`)
- FOUND: scripts/demo_app.py (121 lines ≥ 50; contains `share=False`)
- FOUND: commit 19f181a (RED)
- FOUND: commit 446e16a (GREEN)
- FOUND: commit 0609f50 (demo launcher)
