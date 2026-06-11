---
phase: 08-demo-writeup
reviewed: 2026-06-10T22:49:47Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - docs/REPORT.md
  - scripts/demo_app.py
  - scripts/export_slim.py
  - src/personacore/checkpoint.py
  - src/personacore/generation/__init__.py
  - src/personacore/generation/core.py
  - src/personacore/generation/sampling.py
  - src/personacore/generation/text.py
  - tests/test_demo_callback.py
  - tests/test_forbid_ids.py
  - tests/test_slim_checkpoint.py
findings:
  critical: 0
  warning: 2
  info: 9
  total: 11
status: issues_found
---

# Phase 08: Code Review Report (post gap-closure re-review)

**Reviewed:** 2026-06-10T22:49:47Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Fresh review of phase 08 after gap-closure plans 08-07 (CR-01 forbid_ids mask) and 08-08
(writeup honesty fixes) executed. The prior review's Critical and all four Warnings are
**verified fixed**, each empirically:

- **CR-01 (closed):** the `forbid_ids` mask is threaded correctly through the whole path —
  applied in `next_token` BEFORE both the greedy argmax and the temperature/top-k/top-p
  pipeline (`sampling.py:88-89`), passed per-step by `core.generate`, accepted via `**gen_kw`
  in `generate_text`/`generate_text_cumulative`, and built once at demo launch
  (`demo_app.py:90`). `undecodable_ids_mask` reproduces exactly the id test
  `BPETokenizer.decode` applies (specials first, then `vocab`, else `ValueError`) and never
  masks EOS. The real-artifact regression (`test_real_artifact_crash_settings_no_crash`)
  pins the previously-measured crash settings (temp 1.5, top-k off, 400 tokens) and the
  exact 7645 dead-id count, and the do-not-catch-ValueError contract is pinned by
  `test_generate_text_without_mask_fails_loudly`.
- **WR-02 (closed):** `export_slim` now handles `val_loss=None`
  (`checkpoint.py:134,141`) with a dedicated round-trip test
  (`test_export_slim_handles_val_loss_none`).
- **WR-01 (closed):** REPORT.md now states the 547-live / 7645-dead vocabulary honestly,
  including the 2,935,680 dead embedding parameters in the headline count. All report
  arithmetic was re-verified by hand (param counts 13,891,584 / 17,037,312 / 13,793,280 /
  8,568,192; 256+283+8=547; 0.02/sqrt(12)=0.005774; ln(8192)=9.01) and the training-curve
  claims cross-checked against the committed `results/run.csv` (val 2.38 @ step 250, best
  0.7378 @ 49000, lr 3e-4 -> 3e-5, 200 rows).
- Full suite executed during this review: **137 passed, 1 skipped** (CUDA-only fp16 smoke)
  in 77s, with the real slim artifact and frozen tokenizer present. `ruff check` and
  `ruff format --check` are clean on all reviewed files.

Two new Warnings were found in the gap-closure code itself, both empirically confirmed on
this machine: a latent device-mismatch crash when the CPU-built mask meets an MPS model
(the path `_model_device` explicitly documents as supported), and a residual slice of the
CR-01 problem class — the 7 untrained non-EOS special tokens remain sampleable and can
surface as literal `<|user|>`/`<|pad|>` markup in the demo output. Five Info items from the
prior review were not in the gap-closure scope and remain open; they are re-reported below
with re-verified line numbers, plus two new Info items.

## Warnings

### WR-01: `forbid_ids` mask is always built on CPU — generation crashes on MPS, a documented-supported device

**File:** `src/personacore/generation/text.py:47` / `src/personacore/generation/sampling.py:88-89`

**Issue:** `undecodable_ids_mask` hardcodes `torch.ones(1, vocab_size, dtype=torch.bool)`
on CPU with no `device` parameter, and `next_token` applies it via
`logits_last.masked_fill(forbid_ids, ...)` without device alignment. The same module's
`_model_device` helper (text.py:54-59) exists precisely "so generation works on CPU and MPS
alike" — but following that documented path with a model on MPS and the mask enabled fails.
Confirmed empirically on this machine:

```
RuntimeError: expected self and mask to be on the same device, but got mask on cpu and self on mps:0
```

The shipped demo is unaffected only because `demo_app.py:81` pins CPU. Any consumer that
follows the wrapper's MPS contract (the project's own primary training device) and passes
`forbid_ids` hits a mid-generation crash — the exact symptom class CR-01 was fixed to
eliminate.

**Fix:** Align the mask to the logits device at the single choke point in `next_token`
(a (1, vocab) bool copy is 8 KB — negligible per step), or accept a `device` parameter in
`undecodable_ids_mask`:

```python
# sampling.py, next_token():
if forbid_ids is not None:
    logits_last = logits_last.masked_fill(
        forbid_ids.to(logits_last.device), float("-inf")
    )
```

### WR-02: The 7 untrained non-EOS specials are not masked — literal `<|user|>`/`<|pad|>`/`<|reserved_*|>` markup can appear in demo stories

**File:** `scripts/demo_app.py:90` / `src/personacore/generation/text.py:46`

**Issue:** `undecodable_ids_mask` forbids only ids the tokenizer cannot *decode*. The 7
non-EOS specials (ids 8185-8191: `<|user|>`, `<|assistant|>`, `<|system|>`, `<|pad|>`,
`<|reserved_0..2|>`) are decodable, so they stay sampleable — yet `special.py`'s own
docstring states they are "reserved-now / dead during M1": they never occur in the training
corpus, so their embeddings are as untrained as the 7645 dead merge rows that caused the
original ~29% crash rate. Sampling one does not crash; it renders the raw special literal
verbatim in the story bubble. Measured on the shipped artifact at the slider extreme
(temp 1.5, top-k off): combined probability ~7.7e-7 per step, ~3.1e-4 per 400-token story —
rare, but reachable through in-UI settings, and it undercuts the demo-quality intent behind
D-05 ("the raw separator never appears"; the *other* special literals can). Note the REPORT's
literal claim ("can only produce decodable ids", REPORT.md:366-367) remains technically true.

**Fix:** In `build_demo` (or via an option on the helper), additionally forbid every
registered special except EOS — EOS must stay unmasked so EOS-stop keeps working:

```python
forbid_ids = undecodable_ids_mask(tok, model.config.vocab_size)
for sid in tok.special_tokens.values():
    if sid != tok.eos_id:
        forbid_ids[0, sid] = True  # untrained M1 specials: decodable but never sensible output
```

Extend `tests/test_forbid_ids.py` with one assertion that ids 8185-8191 are masked in the
demo's mask.

## Info

### IN-01: Demo user input can inject atomic special-token ids (`allowed_special="all"` default)

**File:** `src/personacore/generation/text.py:95` / `src/personacore/tokenizer/bpe.py:151`
**Issue:** `generate_text` calls `tokenizer.encode(prompt)` with the default
`allowed_special="all"`, so a demo user typing the literal `<|user|>` injects atomic id 8185
into the prompt (verified: `tok.encode("<|user|>") == [8185]`), and `<|endoftext|>` injects
a mid-prompt document boundary. No crash and no boundary to forge in the fresh-story-per-
message design, but untrusted text should not reach control-token space.
**Fix:** Encode user prompts with `allowed_special="none"` (thread an `allowed_special`
parameter through `generate_text`, defaulting demo input to `"none"` so special literals are
byte-split as plain text).

### IN-02: `export_slim` never validates the source checkpoint's schema version

**File:** `src/personacore/checkpoint.py:130-142`
**Issue:** `CKPT_SCHEMA_VERSION` is written by `save_checkpoint` but checked nowhere —
`export_slim` (new code) blindly indexes the v1 key layout (`full["model"]`,
`full["model_config"]`, ...) and would fail with a bare `KeyError` (or silently mis-export)
on any future schema bump, while `load_slim` enforces its own schema strictly. Asymmetric
validation in the same module.
**Fix:** `if full.get("schema_version") != CKPT_SCHEMA_VERSION: raise ValueError(...)` at
the top of `export_slim`.

### IN-03: REPORT "the only skip" claim holds only when the gitignored artifacts exist

**File:** `docs/REPORT.md:412-414`
**Issue:** "the suite is CPU-only and green, with the only skip a CUDA-only fp16 smoke
test" — verified true on this machine (137 passed, 1 skipped). But on a fresh clone/CI
without `checkpoints/model_slim.pt`, the two real-artifact tests
(`test_real_artifact_crash_settings_no_crash`, `test_real_slim_artifact_generates_on_cpu`)
also skip — 3 skips, contradicting "the only skip" for exactly the readers most likely to
run the suite.
**Fix:** "...with the only skips by design: a CUDA-only fp16 smoke test off-GPU, plus two
real-artifact tests gated on the locally exported checkpoint."

### IN-04: `best.pt` "159 MB" mixes MiB and decimal MB in the same sentence (carryover, prior IN-02)

**File:** `docs/REPORT.md:327` / `docs/REPORT.md:335`
**Issue:** Still present after gap closure. `checkpoints/best.pt` is 166,808,536 bytes =
166.8 MB (decimal) = 159.1 MiB (verified on disk); the same paragraph quotes the slim file
in decimal ("~55.6 MB" = 55,601,269 bytes). One unit base per document.
**Fix:** "the full training checkpoint `best.pt` (167 MB, ...)".

### IN-05: Dead `except ImportError: GPT = None` guard with no skip (carryover, prior IN-03)

**File:** `tests/test_demo_callback.py:27-29`
**Issue:** Still present. If the import ever failed, `GPT = None` makes every test crash
with `TypeError: 'NoneType' object is not callable` instead of skipping; the guard is
vestigial ("model package ships in Phase 4" — it shipped). Same dead pattern at
`tests/test_generation_text.py:22` (out of this review's scope). Notably the newer
`tests/test_forbid_ids.py:36` imports `GPT` directly — the correct pattern.
**Fix:** Delete the try/except and import directly.

### IN-06: cwd-relative paths in `test_slim_checkpoint.py` make the real-artifact test skip silently (carryover, prior IN-07)

**File:** `tests/test_slim_checkpoint.py:41-42`
**Issue:** Still present — and now inconsistent within the same phase:
`tests/test_forbid_ids.py:38-41` implements the repo-root anchor and cites IN-07 by name,
while this file keeps `pathlib.Path("checkpoints/model_slim.pt")` and
`"artifacts/tokenizer.json"` resolved against the invocation cwd. Run pytest from anywhere
but the repo root and `test_real_slim_artifact_generates_on_cpu` silently skips even when
the artifact exists.
**Fix:** Copy the four-line anchor block from `test_forbid_ids.py:38-41`.

### IN-07: Trailing partial multi-byte glyph silently dropped at end of stream, undocumented (carryover, prior IN-05)

**File:** `src/personacore/generation/text.py:104-116`
**Issue:** Still present. If generation ends (max_new_tokens or EOS) while `buffer_ids` ends
mid-glyph, the held bytes never surface — the final character is silently lost. Correct
trade-off for a strict decoder, but the docstring documents only the mid-stream hold-and-
retry case.
**Fix:** One docstring sentence noting the terminal partial-glyph drop is intentional.

### IN-08: `save_checkpoint` `**extra` can silently shadow reserved keys (carryover, prior IN-06)

**File:** `src/personacore/checkpoint.py:58-77`
**Issue:** Still present. `**extra` unpacks last in the dict literal, so
`extra={"model": ...}` (or `"rng"`, `"git_sha"`, ...) silently replaces real training state.
The M2 EWC seam invites arbitrary keys, making an accidental collision plausible.
**Fix:** `clash = {"schema_version", "model", "optimizer", "scheduler", "scaler", "step",
"val_loss", "model_config", "train_config", "git_sha", "rng"} & extra.keys(); if clash:
raise ValueError(f"extra keys shadow reserved checkpoint keys: {sorted(clash)}")`.

### IN-09: `load_slim` raises `AttributeError` instead of the designed `ValueError` on a non-dict payload (carryover, prior IN-08)

**File:** `src/personacore/checkpoint.py:154-155`
**Issue:** Still present. `loaded.get("schema_version")` assumes a dict, but
`weights_only=True` happily loads a bare tensor or list — a corrupt/foreign download (the
one untrusted-input path in the codebase) then dies with `AttributeError`, bypassing the
designed `ValueError` with its re-export hint.
**Fix:** `if not isinstance(loaded, dict) or loaded.get("schema_version") != SLIM_SCHEMA_VERSION: raise ValueError(...)`.

---

_Reviewed: 2026-06-10T22:49:47Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
