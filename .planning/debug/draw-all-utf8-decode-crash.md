---
slug: draw-all-utf8-decode-crash
status: fixing
trigger: "draw_all crashes with UnicodeDecodeError on generations ending mid-multi-byte-glyph; apply the D-06 tolerant-prefix policy at the decode site in scripts/phase14_recall.py, RED test first, verify Phase 14 D-01 hit vectors stay bit-identical"
created: 2026-08-16
updated: 2026-08-16
---

# draw-all-utf8-decode-crash

## Symptoms

- **Expected:** `scripts/phase18_extraction.py --arm adapter-on` runs 42,480 draws
  (864 attack prompts x K=48, plus 112 family-zero prompts x 9) and writes
  `results/phase18_arm_adapter-on.json`.
- **Actual:** the process died 6m37s after launch (pid 30288, launched 14:55:13,
  traceback written 15:01:50). No record written; tree unchanged at `17d46ef`.
- **Error:** `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x9d in position 3:
  invalid start byte`, raised at `src/personacore/tokenizer/bpe.py:209` via
  `scripts/phase14_recall.py:661` (`draw_all`) via `run_arm`
  (`scripts/phase18_extraction.py:3634`).
- **Timeline:** first occurrence. Phases 14/16/17 ran the same `draw_all` decode line
  (unchanged since `121efb8`) without hitting it, at roughly 1-2k draws against this
  arm's 42,480.
- **Reproduction:** sampling at `SAMPLE_TEMPERATURE`/`SAMPLE_TOP_P` until a completion
  ends mid-multi-byte-glyph. Draw index not recoverable from the log — `run_arm` prints
  only a preflight line and a final `wrote ...` line, no per-draw progress.

## Current Focus

- **hypothesis:** ROOT CAUSE FOUND (below). `draw_all` decodes a freely-sampled id
  sequence with the strict decoder and no tolerance for a truncated trailing glyph — the
  exact second decode path Phase 14's own research told it not to create.
- **next_action:** RED test against the real decoder, then `_decode_tolerant` at both
  `draw_all` decode sites.

## Evidence

- `src/personacore/tokenizer/bpe.py:196-198` — `decode` is strict **by design** (WR-03):
  "byte-level coverage guarantees valid round-trips, so any non-round-trippable byte
  stream is a genuine defect and must raise `UnicodeDecodeError` rather than silently
  emit U+FFFD replacements." That premise holds for **round-tripping real text**, not for
  **freely sampled** streams, which can be cut mid-character.
- `src/personacore/generation/text.py:104-112` — the streaming path already ruled the
  opposite for generation (D-06): "a cumulative buffer that ends mid-glyph is **NOT a
  defect** ... Hold the ids and try again next step." It catches `UnicodeDecodeError` and
  withholds the partial fragment.
- **Phase 14 explicitly prescribed that policy for this very harness and it was not
  followed.** `14-RESEARCH.md:690` (Gap G1): add `generate_text_from_ids` that "reuses
  `generate_text`'s cumulative-buffer decode (**including the `UnicodeDecodeError`
  continue**) ... it gives the harness and the UI one shared decode path. Do **not**
  inline it in the demo script — that would create the second code path D-18 exists to
  prevent." `14-PATTERNS.md:92-93`: "**Copy the cumulative-decode block verbatim**; it is
  the one piece with a named crash class attached (Pitfall 3, `UnicodeDecodeError` on a
  split glyph)."
- `generate_text_from_ids` **was** added (`src/personacore/generation/text.py:119`) with
  the tolerant decode — but `draw_all` does not use it. It calls `collect(...)` through
  its own `_complete` (`scripts/phase14_recall.py:594-609`) and decodes the result raw at
  lines 642 and 661. That is the second code path, and it is the one that crashed.
- `tests/test_phase18_draws.py:85-93` — the phase-18 suite substitutes an `_IdDecoder`
  for the real decoder, documenting the reason out loud: "it raises `UnicodeDecodeError`
  on byte sequences that are not valid UTF-8, which a hash-driven fake model produces
  constantly." No test ever ran the real decoder over real generations, so the crash was
  structurally invisible to the suite.

## Eliminated

- **Not a device/MPS fault** — the traceback is a pure `bytes.decode` failure, no torch
  frame below `_complete`.
- **Not corpus corruption** — `tests/test_phase18_corpus.py` 18 passed; the committed
  corpus re-derives byte-identical and its file digest `ff8e6e3c24987ac3...` matches the
  pre-flight's recorded in-memory digest.
- **Not drift in `draw_all`** — `git log -L 655,665:scripts/phase14_recall.py` shows the
  decode line unchanged since `121efb8` (plan 14-10). The code that produced Phase 14's
  reference vectors is the code that crashed here.

## Root Cause

A byte-level BPE generation cut off mid-multi-byte-character yields an invalid UTF-8 byte
stream. `draw_all` decodes it strictly and lets the `UnicodeDecodeError` propagate, killing
the run. The project had already ruled this is not a defect but an expected property of
sampling (D-06) and Phase 14 explicitly required the draw harness to reuse that tolerant
decode; `draw_all` instead grew its own strict decode of `_complete`'s ids.

## Fix

`_decode_tolerant` at both `draw_all` decode sites in `scripts/phase14_recall.py` (lines
642 and 661): decode the longest valid UTF-8 prefix, drop the incomplete trailing
fragment — the same D-06 policy applied to a single-shot decode instead of a running
buffer.

Deliberately **not** switching `draw_all` to `generate_text_from_ids`: that helper streams
text and does not carry `_complete`'s `forbid_ids` / `stop_ids` / `stopped`-flag
semantics, so swapping it would change the generated id stream itself and put D-01
bit-identity at risk. Decoding the already-generated ids differently cannot move the
stream; regenerating through another path can.

Chosen over `errors="replace"` (which would edit the from-scratch tokenizer's decode for
every caller and contradict WR-03 directly) and over recording draws as undecodable
(which would touch scoring, the report renderer and the pre-registration).

**Safety argument for the audit:** the change affects only id sequences that currently
raise. Every completion any existing artifact recorded decoded strictly-clean, so
Phase 14's 112 `core_taught` hit vectors — the D-01 positive control 18-15 must reproduce
— cannot move. Verified explicitly before the commit, not assumed.

## Sibling sites with the same latent exposure (NOT fixed here — out of scope)

Decode of *generated* ids elsewhere, same crash class, none blocking 18-15:

- `scripts/phase14_recall.py:1423-1424` — `tok.decode(on_ids)` / `tok.decode(off_ids)`
- `scripts/phase14_factset_gate.py:95,107` — decodes `_complete(...)` output
- `scripts/make_transcripts.py:155,159` and `scripts/make_retention_samples.py:188`

Sites decoding corpus or prompt ids (`build_retention_bin.py:124`, `encode_corpus.py:96`,
`phase14_recall.py:386,427,477`, `make_retention_samples.py:246`, `phase16_ladder.py:538`,
`phase14_factset.py:320`) round-trip by construction and are correctly strict.

## Verification

- **RED, before the fix:** `tests/test_phase14_draw_decode.py` — 1 failed, 3 passed.
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf0 in position 2: unexpected end of
  data` at `src/personacore/tokenizer/bpe.py:209`, through the real `draw_all` and the real
  `BPETokenizer`. Same crash class as the killed arm.
- **GREEN, after the fix:** 4 passed.
- **Generation path untouched:** `git diff` on `scripts/phase14_recall.py` is 37 insertions /
  **2 deletions**, and both deletions are `completions.append(tok.decode(gen_ids))`. `_complete`,
  the seeds, the forbid mask and the stop ids are byte-for-byte unchanged, so `gen_ids` cannot
  move.
- **Decode identical on every clean stream:** 200,000 random id sequences over the 547 sampleable
  ids; 64,691 decoded cleanly under the strict decoder; `_decode_tolerant` diverged from
  `tok.decode` on **0** of them. (The other 135,309 would have raised — that is a uniform-random
  denominator, NOT the model's rate, and must not be quoted as one.)
- **D-01 re-derived LITERALLY, on the adapter, with the fix applied.** 112 `core_taught`
  questions x 9 draws through the patched `draw_all`, on `mps`, seed 1337, HEAD `17d46ef`,
  4.1 min. Compared row-for-row against `parse_phase14_taught_rows()` — the committed
  `results/phase14_recall_report.md`, opened read-only; output written to the scratchpad and
  `write_recall_report` never called, so committed evidence stayed untouched (`git status --short
  results/` empty).

  | | rows | totals | rate |
  | --- | --- | --- | --- |
  | committed | 112 | 496/1008 | 0.492063 |
  | re-derived | 112 | 496/1008 | 0.492063 |

  **Mismatching rows: 0.** D-01's positive control reproduces exactly under the fix.
- **Full suite:** `.venv/bin/pytest -q` — **726 passed, 1 skipped** in 140.63s.
- **Lint:** `.venv/bin/ruff check .` — All checks passed. `ruff format --check .` — 162 files
  already formatted.

## Resolution

- root_cause: see above
- fix: `_decode_tolerant` in `scripts/phase14_recall.py`, wired into both `draw_all` decode sites
- verification: see above
- files_changed: `scripts/phase14_recall.py`, `tests/test_phase14_draw_decode.py` (new)
- not_committed_yet: the D-01 confirmation above is structural, not a literal re-derivation —
  held for the operator's call before the commit that unfreezes the run.
