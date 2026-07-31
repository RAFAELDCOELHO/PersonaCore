---
phase: 11-conversational-data-pipeline
plan: 01
subsystem: data-pipeline
tags: [personachat, fb-dialog, parser, detokenizer, loss-mask, special-tokens, tdd]

# Dependency graph
requires:
  - phase: 02-tokenizer (via v1.0)
    provides: frozen production tokenizer (artifacts/tokenizer.json, from_json) + LOCKED SPECIAL_TOKENS registry (8184-8191)
provides:
  - src/personacore/dialogue/ package — parse/detok/render/encode+mask import surface
  - parse_episodes(path) -> [(persona, turns), ...] — from-scratch fb-dialog parser (DATA-01, stdlib only)
  - detokenize(text) -> str — D-06 regex normalizer (contraction rejoin, punct-space close, !. -> !)
  - render_document(persona, turns) -> str — D-04 string form (no space after role tokens, no trailing eos)
  - encode_dialogue(tok, persona, turns) -> (ids, mask) — span-wise D-01 mask encoder, the single tokenization source for gate AND bins
affects: [11-02 inflation gate, 11-03 fetch + bins, 11-04 masked batch draw, 12-dialogue-finetune]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Span-wise mask construction: emit(token_ids, m) over parallel ids/mask lists; role ids appended literally from SPECIAL_TOKENS, content spans plain-encoded — never encode-whole-then-search (Pitfall 14)"
    - "encode_dialogue applies detokenize to every content span itself, so every caller tokenizes identically (Pitfall 4)"
    - "Committed SYNTHETIC format-faithful fixture (D-00 no-re-host): reproduces spaced punctuation, zero apostrophes, !. artifact, no trailing boundary"

key-files:
  created:
    - src/personacore/dialogue/__init__.py
    - src/personacore/dialogue/parse.py
    - src/personacore/dialogue/serialize.py
    - tests/fixtures/personachat_fb_fixture.txt
    - tests/test_dialogue_parse.py
    - tests/test_dialogue_serialize.py
  modified: []

key-decisions:
  - "!. persona artifact normalized to ! in detokenize (RESEARCH Open Q2 pinned by fixture test)"
  - "Persona span detokenized per-line then newline-joined (avoids the \\s+ punct rule eating newlines)"
  - "REQUIREMENTS.md untouched: DATA-01's fetch/checksum half and DATA-02's bins half land in plan 11-03"

patterns-established:
  - "dialogue/ package init mirrors continual/ shape: phase+requirement docstring, relative imports, sorted __all__"
  - "D-01 mask semantics pinned at all three Pitfall-14 edge tokens (first <|user|>=0, subsequent <|user|>=1, eos=1) by exact-reconstruction tests"

requirements-completed: [DATA-01, DATA-02]

# Metrics
duration: ~15min
completed: 2026-07-31
---

# Phase 11 Plan 01: Dialogue Package (Parse + Serialize + Mask) Summary

**From-scratch fb-dialog parser, D-06 regex detokenizer, D-04 renderer, and span-wise D-01 id+mask encoder in the new `dialogue/` package — 22 new tests pin mask semantics at all three turn-boundary edge tokens through the frozen production tokenizer**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-31T18:48:38Z
- **Completed:** 2026-07-31T19:03:00Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 6 created

## Accomplishments

- `parse_episodes` reads fb-dialog text into `(persona, turns)` episodes: line-number-reset boundaries, prefix-stripped persona lines, strict 4-tab-field turn split (hard-fails on malformed lines — the T-11-03 disposition), flush-at-EOF so the last episode is never dropped (Pitfall 5)
- Committed fixture is SYNTHETIC and format-faithful (D-00 no-re-host): 3 episodes, 3-5 persona lines each, spaced punctuation, zero apostrophes, pre-expanded contractions, the `!.` artifact, and no trailing boundary line
- `detokenize` closes spaced punctuation, rejoins " n't" and apostrophe-suffix contractions (no-op on the primary corpus, covers the D-05 JSON fallback), and normalizes `!.` → `!`; stays lowercase (no truecasing)
- `render_document` produces the exact D-04 string form — `<|system|>` + newline-joined persona + `<|user|>utt<|assistant|>reply` spans, no space after role tokens (Pitfall 4), no trailing eos marker
- `encode_dialogue` returns equal-length ids+mask with exact D-01 semantics; role/eos ids are literal appends from the LOCKED `SPECIAL_TOKENS` registry (never retyped), content spans plain-encoded from detokenized text — mask offsets exact by construction
- Role tokens 8185-8187 proven atomic + decode-round-trip through the frozen `artifacts/tokenizer.json` (never a fresh tokenizer)
- Full suite green: 241 passed, 4 skipped (pre-existing environment gates); `ruff check` + `ruff format --check` clean

## Task Commits

Each task was committed atomically (TDD: RED test commit, then GREEN feat commit):

1. **Task 1: fb-dialog parser (RED)** - `38be8f4` (test) — fixture + six failing DATA-01 pins
2. **Task 1: fb-dialog parser (GREEN)** - `968d469` (feat) — parse.py + dialogue/__init__.py
3. **Task 2: serialize trio (RED)** - `dc2c78a` (test) — sixteen failing DATA-02 pins
4. **Task 2: serialize trio (GREEN)** - `39f6bdb` (feat) — serialize.py + extended __init__.py

## Files Created/Modified

- `src/personacore/dialogue/__init__.py` - Package import surface; `__all__ = ["detokenize", "encode_dialogue", "parse_episodes", "render_document"]`
- `src/personacore/dialogue/parse.py` - `parse_episodes`: stdlib-only fb-dialog parser (zero imports), verified-corpus-invariant docstring (39 lines)
- `src/personacore/dialogue/serialize.py` - `detokenize` (3 compiled regexes + `!.` rule), `render_document`, `encode_dialogue` with the `emit` span helper (94 lines)
- `tests/fixtures/personachat_fb_fixture.txt` - 3 synthetic format-faithful episodes (D-00: zero real corpus lines)
- `tests/test_dialogue_parse.py` - Six DATA-01 pins: episode count, exact personas, exact turn tuples, EOF flush, shape invariants, candidates absent
- `tests/test_dialogue_serialize.py` - Sixteen DATA-02 pins: five detok rules, 3×2 atomicity/round-trip, exact render form, mask endpoints, role-position masks, exact span-structure reconstruction, span-wise content masks

## Decisions Made

- `!.` → `!` normalization lives in `detokenize` (RESEARCH Open Question 2), pinned by `test_detok_normalizes_persona_bang_dot_artifact`; the parser returns persona text RAW
- Persona span is detokenized per-line then newline-joined inside `encode_dialogue` — semantically identical to detokenizing the joined string but immune to the space-close regex collapsing a newline before punctuation
- REQUIREMENTS.md left untouched: DATA-01's download/checksum half and DATA-02's uint16-bins half are plan 11-03 deliverables; the `requirements-completed` frontmatter copies the plan's `requirements` field per template contract — the orchestrator/verifier reconciles at phase level

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Worktree spawned one commit behind the expected base (b35858b vs 3e9ff6e); corrected with a clean fast-forward before any work
- `11-PATTERNS.md` is untracked in the main checkout only (not in the worktree base) — read from the main checkout path, no impact

## Known Stubs

None — no placeholders, hardcoded empty values, or unwired data paths. All four exports are complete implementations consumed by wave-2/3 plans.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 11-02 (inflation gate) and 11-03 (bins) import `encode_dialogue`/`render_document`/`detokenize` from one place — gate and bins structurally cannot tokenize differently (Pitfall 4 closed)
- Plan 11-04's DATA-03 fixture asserts the final `y` tensor against exactly the D-01 semantics these tests pin (first `<|user|>`=0, subsequent `<|user|>`=1, eos=1)
- The parser hard-fails on malformed dialogue lines, satisfying the T-11-03 threat disposition ahead of the checksum-gated real-corpus fetch

## Self-Check: PASSED

- All 6 created files exist on disk
- All 4 task commits present in git log (38be8f4, 968d469, dc2c78a, 39f6bdb)
- `pytest -q`: 241 passed, 4 skipped; `ruff check .` + `ruff format --check .` clean
