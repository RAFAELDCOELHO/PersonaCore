---
phase: 14
plan: 01
subsystem: dialogue + generation
tags: [clean-room-prompt, id-space-streaming, D-18, gap-G1, gap-G2]
requires:
  - personacore.dialogue.encode_dialogue
  - personacore.tokenizer.special.SPECIAL_TOKENS
  - personacore.generation.core.generate
provides:
  - personacore.dialogue.build_recall_prompt
  - personacore.dialogue.ASSISTANT_ID
  - personacore.generation.generate_text_from_ids
  - personacore.generation.generate_text_from_ids_cumulative
affects:
  - scripts/phase14_recall.py (future — imports build_recall_prompt)
  - scripts/personalize_demo.py (future — imports both)
tech-stack:
  added: []
  patterns:
    - "shared-source-of-truth package function (cap_persona precedent) for the recall prompt"
    - "delta producer + cumulative adapter pair (generate_text / generate_text_cumulative precedent)"
key-files:
  created:
    - tests/test_recall_prompt.py
  modified:
    - src/personacore/dialogue/serialize.py
    - src/personacore/dialogue/__init__.py
    - src/personacore/generation/text.py
    - src/personacore/generation/__init__.py
decisions:
  - "ASSISTANT_ID is exported from the dialogue barrel alongside build_recall_prompt — downstream scripts need the truncation id for their token panels, and re-deriving it would reintroduce the retyped-literal risk the constant exists to close"
  - "the bounds-guard test asserts no forward pass via an additive _spy_forwards wrapper rather than by changing _force_sequence, so the copied fixture block stays byte-identical to tests/test_demo_callback.py"
metrics:
  duration: 21min
  tasks: 3
  files: 5
  completed: 2026-08-01
---

# Phase 14 Plan 01: Recall Prompt + Id-Space Streaming Summary

Shipped `build_recall_prompt` (the D-18 single source of truth for the clean-room recall prompt)
and `generate_text_from_ids` (+ its cumulative Gradio-shaped sibling), closing RESEARCH Gaps G2
and G1 so the fact-set gate, the scoring harness, and the demo all route through one prompt
builder and one decode path.

## What Shipped

**`build_recall_prompt(tok, question, persona=())` — `src/personacore/dialogue/serialize.py`**
Encodes through the existing `encode_dialogue` with an empty assistant reply and truncates to end
at the `<|assistant|>` trigger. Default `persona=()` gives a bare `<|system|>` with zero content.
A module-level `ASSISTANT_ID = SPECIAL_TOKENS[_ASSISTANT]` supplies the truncation id from the
locked registry — the raw integer appears nowhere in the module (`grep -c "8186"` returns 0).
Measured shapes match 14-RESEARCH F2 exactly: `""` → `[8187, 8185, 8186]`;
`"what is your dog's name?"` → a 19-id sequence ending at the assistant tag.

**`generate_text_from_ids(...)` — `src/personacore/generation/text.py`**
`generate_text`'s body with the string-encode line replaced by the caller's id list. Everything
with a named failure class attached is copied verbatim: the `(0, max_new_tokens_cap]` DoS guard
before the loop (V5 / T-06-04) and the cumulative-decode block with the `UnicodeDecodeError:
continue` idiom (Pitfall 3). `tokenizer.encode` is never called and `eos_id` is never prepended.
`generate_text_from_ids_cumulative` is the 4-line accumulation adapter — it ships in the package,
not in the demo callback, so CI covers the monotonic-growth claim without the demo extra
installed.

**`tests/test_recall_prompt.py`** — 12 tests, CPU-only, checkpoint-free, zero skip markers. The
prompt half runs against the frozen `artifacts/tokenizer.json`; the streaming half runs on the
tiny in-memory GPT fixture block copied unchanged from `tests/test_demo_callback.py`.

## Threat Mitigations Applied

| Threat ID | Mitigation as built |
|---|---|
| T-14-01 | `test_no_value_leaks_into_prompt` asserts the untaught value is absent from `tok.decode(prompt_ids)` **and** that its encoded id sequence is not a contiguous subsequence of the prompt — a builder that quietly admitted a value fails in CI even if it tokenized oddly |
| T-14-02 | `test_bounds_guard` drives `0`, `-1`, and `4097` through the generator and asserts the forward-call counter is still `0` on rejection, so the guard provably fires before any compute |
| T-14-03 | `ASSISTANT_ID` resolves from `SPECIAL_TOKENS`; `grep -c "8186" src/personacore/dialogue/serialize.py` returns 0 |
| T-14-SC | No packages installed. Every import already existed. |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Docstring wording tripped its own acceptance criterion**
- **Found during:** Task 1
- **Issue:** The first draft of the `build_recall_prompt` docstring read "the literal 8186 is never
  written here" — which itself wrote the literal, so `grep -c "8186"` returned 1 instead of the
  required 0.
- **Fix:** Reworded to "the raw integer is never retyped in this module."
- **Files modified:** `src/personacore/dialogue/serialize.py`
- **Commit:** d376305

### Deliberate Adjustments

**2. `ASSISTANT_ID` exported from the dialogue barrel (plan named only `build_recall_prompt`)**
The plan's barrel instruction listed `build_recall_prompt`. `ASSISTANT_ID` was added to the same
export because the downstream demo (14-08) and harness (14-05) both need the truncation id for
their token panels; forcing them to re-derive it from `SPECIAL_TOKENS` would spread the exact
retyping risk T-14-03 exists to close. `__all__` remains alphabetically sorted (uppercase sorts
first under `sorted()`), so the plan's sorted-`__all__` criterion still holds.

**3. `_spy_forwards` helper added to the test module**
The plan required `test_bounds_guard` to "assert the forced-sequence counter is still 0" while
also copying `_force_sequence` **unchanged** (that block must not diverge from its two sibling
copies). `_force_sequence` does not expose its counter. Rather than modify the shared block, an
additive `_spy_forwards(model)` wrapper installs a counting proxy over whatever forward is already
in place. It also captures the first `idx` the core sees, which strengthens
`test_prompt_ids_used_verbatim` from "encode was not called" to "the core received exactly these
ids" — the direct pin on the Gap-G1 defect.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_recall_prompt.py` | 12 passed |
| `pytest -q` (full suite) | 294 passed, 4 skipped (pre-existing skips, none in the new module) |
| `ruff check . && ruff format --check .` | clean |
| `build_recall_prompt(tok, "")` | `[8187, 8185, 8186]` |
| `build_recall_prompt(tok, "what is your dog's name?")` | 19 ids, ends `8186` |
| `grep -c "8186" src/personacore/dialogue/serialize.py` | 0 |
| `grep -c "def generate_text_from_ids" src/personacore/generation/text.py` | 2 |
| both barrels' `__all__` sorted, new names present | asserted, exits 0 |
| `grep -c` for `import gradio` / `checkpoints/` / `skipif` in the new test | 0 / 0 / 0 |

## Commits

| Task | Commit | Message |
|---|---|---|
| 1 | d376305 | `feat(14-01): add build_recall_prompt to dialogue/serialize.py` |
| 2 | 86e42c5 | `feat(14-01): add generate_text_from_ids to generation/text.py` |
| 3 | 53131ec | `test(14-01): pin the clean-room prompt shape and the id-space streaming contract` |

## Known Stubs

None. Both functions are fully wired; their downstream callers
(`scripts/phase14_recall.py`, `scripts/personalize_demo.py`) are shipped by later plans in this
phase, which is the planned dependency direction (this plan is wave 1 with `depends_on: []`).

## Notes for Later Plans

- The `persona=` argument on `build_recall_prompt` exists **only** for the D-11.1 fairness control.
  The recall path must never pass it — `test_persona_arg_appends_span` documents this in the test
  name and comment, but nothing enforces it at the call site.
- 14-RESEARCH F2's 19-id length for `"what is your dog's name?"` is now pinned by
  `test_prompt_is_bare_system`. That assertion is tokenizer-specific: it will fail loudly if the
  frozen `artifacts/tokenizer.json` is ever replaced, which is the intended alarm (Pitfall 6).

## Self-Check: PASSED

- `src/personacore/dialogue/serialize.py` — FOUND
- `src/personacore/dialogue/__init__.py` — FOUND
- `src/personacore/generation/text.py` — FOUND
- `src/personacore/generation/__init__.py` — FOUND
- `tests/test_recall_prompt.py` — FOUND
- commit `d376305` — FOUND
- commit `86e42c5` — FOUND
- commit `53131ec` — FOUND
